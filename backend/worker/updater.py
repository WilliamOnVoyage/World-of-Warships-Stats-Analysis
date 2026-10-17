"""
WoWS Data Pipeline Worker v3 (High-Throughput Concurrent Architecture)
- Shared 10 req/s Token Bucket (aiolimiter) across all ingestion tasks
- Fast-Track Clan Roster Crawler (100% active player discovery for EU & ASIA)
- Concurrent Background ID Range Sweepers (EU: 350 IDs/s, ASIA: 150 IDs/s)
- Telemetry Refresher with Diff-Only Snapshotting
- Periodic Time-Series Progress Sampler (for rolling average rates & ETA calculation)
- Pipeline Run Ledger & Heartbeat Monitoring
"""
import asyncio
import os
import json
import traceback
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
load_dotenv()

from sqlmodel import create_engine, Session, select, text, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from aiolimiter import AsyncLimiter
from database.models import (
    Player,
    PlayerSnapshot,
    DailyServerStats,
    PipelineState,
    PipelineRun,
    PipelineProgressSample,
    Clan,
    LeaderboardCache,
    create_partition_if_not_exists,
)
from database.leaderboard import (
    LEADERBOARD_MODES,
    build_leaderboard_rows,
    upsert_leaderboard_rows,
)
from api.wargaming import WargamingAPIClient

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wows_dev.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def is_postgres_engine(db_engine) -> bool:
    return getattr(db_engine.dialect, "name", "") == "postgresql"


# Housekeeping runs on its own small pool with a hard per-statement timeout so a
# bad plan can never stall the orchestrator for long (cycle #1060 hung >53 min).
HOUSEKEEPING_STATEMENT_TIMEOUT_MS = int(os.getenv("HOUSEKEEPING_STATEMENT_TIMEOUT_MS", "120000"))
if is_postgres_engine(engine):
    housekeeping_engine = create_engine(
        DATABASE_URL,
        pool_size=1,
        max_overflow=1,
        connect_args={"options": f"-c statement_timeout={HOUSEKEEPING_STATEMENT_TIMEOUT_MS}"},
    )
else:
    housekeeping_engine = engine

HOUSEKEEPING_HEARTBEAT_INTERVAL_S = 30

# Shared global rate limiter enforcing strictly <= 10 req/s across all concurrent workers
GLOBAL_LIMITER = AsyncLimiter(10, 1.0)

REGIONS = {
    "na": {"high_water_mark": 1_075_000_000, "upper_limit": 1_100_000_000},
    "eu": {"high_water_mark": 500_000_000, "upper_limit": 760_000_000},
    "asia": {"high_water_mark": 2_000_000_000, "upper_limit": 2_050_000_000},
}

BATCH_SIZE = 100

def update_heartbeat(
    job_name: str,
    cursor: int = 0,
    status: str = "running",
    details: str = "",
    range_start: int = 0,
    range_end: int = 0
):
    """Updates the pipeline_state table with current heartbeat and progress bounds."""
    try:
        with Session(engine) as session:
            stmt = select(PipelineState).where(PipelineState.job_name == job_name)
            state = session.exec(stmt).first()
            now = datetime.now(timezone.utc)
            if not state:
                state = PipelineState(
                    job_name=job_name,
                    cursor_value=cursor,
                    range_start=range_start,
                    range_end=range_end,
                    heartbeat_at=now,
                    status=status,
                    details=details
                )
            else:
                state.cursor_value = cursor
                if range_start > 0:
                    state.range_start = range_start
                if range_end > 0:
                    state.range_end = range_end
                state.heartbeat_at = now
                state.status = status
                if details:
                    state.details = details
            session.add(state)
            session.commit()
    except Exception as e:
        print(f"[{job_name}] Failed to update heartbeat: {e}")

def record_progress_sample(job_name: str, cursor: int, processed: int, found: int):
    """Records a time-series checkpoint for moving average rate and ETA calculation."""
    try:
        with Session(engine) as session:
            sample = PipelineProgressSample(
                job_name=job_name,
                sampled_at=datetime.now(timezone.utc),
                cursor_value=cursor,
                items_processed=processed,
                items_found=found
            )
            session.add(sample)
            session.commit()
    except Exception as e:
        pass

async def refresh_known_players(realm: str = "na", limit: int = 2000) -> int:
    """
    Refreshes players that already exist in our DB.
    Batches 100 accounts per Wargaming API call using diff-only snapshotting.
    """
    job_name = f"combat_sync_{realm}"
    app_id = os.getenv("WARGAMING_APP_ID")
    if not app_id:
        return 0

    client = WargamingAPIClient(application_id=app_id, realm=realm, rate_limiter=GLOBAL_LIMITER)
    
    current_cursor = 0
    with Session(engine) as session:
        st = session.exec(select(PipelineState).where(PipelineState.job_name == job_name)).first()
        if not st:
            legacy_st = session.exec(select(PipelineState).where(PipelineState.job_name == f"telemetry_{realm}")).first()
            if legacy_st and legacy_st.cursor_value:
                current_cursor = legacy_st.cursor_value
        elif st.cursor_value:
            current_cursor = st.cursor_value

        query = (
            select(Player.account_id, Player.last_battle_time)
            .where(Player.realm == realm, Player.account_id > current_cursor)
            .order_by(Player.account_id.asc())
            .limit(limit)
        )
        players_to_refresh = session.exec(query).all()

        if not players_to_refresh and current_cursor > 0:
            current_cursor = 0
            query = (
                select(Player.account_id, Player.last_battle_time)
                .where(Player.realm == realm, Player.account_id > 0)
                .order_by(Player.account_id.asc())
                .limit(limit)
            )
            players_to_refresh = session.exec(query).all()

    if not players_to_refresh:
        update_heartbeat(
            job_name=job_name,
            cursor=current_cursor,
            status="idle",
            details=f"Queue empty (0 tracked {realm.upper()} commanders pending)"
        )
        await client.close()
        return 0

    known_battle_times = {row[0]: (row[1] or 0) for row in players_to_refresh}
    account_ids = list(known_battle_times.keys())
    next_cursor = account_ids[-1] if account_ids else current_cursor
    
    processed_count = 0
    updated_snapshots = 0
    now = datetime.now(timezone.utc)

    try:
        for i in range(0, len(account_ids), BATCH_SIZE):
            chunk = account_ids[i:i + BATCH_SIZE]
            try:
                data = await client.get_player_info(
                    chunk,
                    extra="statistics.pvp_solo,statistics.pvp_div2,statistics.pvp_div3,statistics.rank_solo,statistics.pve"
                )
            except Exception as e:
                print(f"[{job_name}] Warning: Chunk error on accounts {chunk[:2]}...: {e}")
                continue

            if not data:
                continue

            leaderboard_rows = []
            with Session(engine) as session:
                create_partition_if_not_exists(session.get_bind(), now)
                
                for acc_id_str, info in data.items():
                    if not info:
                        continue
                    acc_id = int(acc_id_str)
                    processed_count += 1
                    
                    hidden = bool(info.get("hidden_profile", False))
                    new_lbt = info.get("last_battle_time") or 0
                    stats_overall = info.get("statistics") or {}
                    stats_pvp = stats_overall.get("pvp") or {}
                    curr_battles = stats_pvp.get("battles", 0)
                    prev_lbt = known_battle_times.get(acc_id, 0)

                    # Update player record
                    player = session.get(Player, acc_id)
                    if player:
                        player.last_updated = now
                        player.last_battle_time = new_lbt
                        player.hidden_profile = hidden
                        player.leveling_tier = info.get("leveling_tier")
                        session.add(player)

                    # DIFF-ONLY SNAPSHOTTING
                    if not hidden and curr_battles > 0 and (new_lbt > prev_lbt or prev_lbt == 0):
                        solo = stats_overall.get("pvp_solo") or {}
                        div2 = stats_overall.get("pvp_div2") or {}
                        div3 = stats_overall.get("pvp_div3") or {}
                        rank = stats_overall.get("rank_solo") or {}

                        try:
                            snapshot = PlayerSnapshot(
                                account_id=acc_id,
                                timestamp=now,
                                battles=int(curr_battles or 0),
                                wins=int(stats_pvp.get("wins") or 0),
                                damage_dealt=int(stats_pvp.get("damage_dealt") or 0),
                                survived=int(stats_pvp.get("survived_battles") or 0),
                                frags=int(stats_pvp.get("frags") or 0),
                                xp=int(stats_pvp.get("xp") or 0),
                                max_damage=int(stats_pvp.get("max_damage_dealt") or 0),
                                damage_scouting=int(stats_pvp.get("damage_scouting") or 0),
                                ships_spotted=int(stats_pvp.get("ships_spotted") or 0),
                                planes_killed=int(stats_pvp.get("planes_killed") or 0),
                                mb_hits=int(stats_pvp.get("main_battery", {}).get("hits") or 0),
                                mb_shots=int(stats_pvp.get("main_battery", {}).get("shots") or 0),
                                torp_hits=int(stats_pvp.get("torpedoes", {}).get("hits") or 0),
                                torp_shots=int(stats_pvp.get("torpedoes", {}).get("shots") or 0),
                                art_agro=int(stats_pvp.get("art_agro") or 0),
                                torpedo_agro=int(stats_pvp.get("torpedo_agro") or 0),
                                solo_battles=int(solo.get("battles") or 0),
                                solo_wins=int(solo.get("wins") or 0),
                                div2_battles=int(div2.get("battles") or 0),
                                div2_wins=int(div2.get("wins") or 0),
                                div3_battles=int(div3.get("battles") or 0),
                                div3_wins=int(div3.get("wins") or 0),
                                rank_battles=int(rank.get("battles") or 0),
                                rank_wins=int(rank.get("wins") or 0),
                            )
                            session.add(snapshot)
                            updated_snapshots += 1
                            if player:
                                leaderboard_rows.extend(build_leaderboard_rows(
                                    acc_id, player.nickname, player.realm, snapshot.model_dump(), now
                                ))
                        except Exception as sn_err:
                            print(f"[{job_name}] Snapshot warning for player {acc_id}: {sn_err}")

                session.commit()

                # Write-through: keep player_leaderboard_stats current without scanning player_snapshot
                if leaderboard_rows:
                    try:
                        upsert_leaderboard_rows(session, leaderboard_rows)
                        session.commit()
                    except Exception as lb_err:
                        session.rollback()
                        print(f"[{job_name}] Leaderboard upsert warning: {lb_err}")

        update_heartbeat(
            job_name=job_name,
            cursor=next_cursor,
            status="running",
            details=f"Processed {processed_count} players (cursor {next_cursor:,}), {updated_snapshots} active snapshots saved"
        )
        record_progress_sample(job_name, next_cursor, processed_count, updated_snapshots)

    except Exception as e:
        print(f"[{job_name}] Telemetry error: {e}")
        update_heartbeat(job_name, cursor=current_cursor, status="error", details=str(e)[:250])
    finally:
        await client.close()

    return processed_count

async def discover_new_players(realm: str = "na", chunk_count: int = 50) -> int:
    """
    Scouts new account IDs for the given realm.
    - Baseline Phase: Sequential range scan from high_water_mark to upper_limit.
    - Frontier Delta Phase: Once caught up to live edge or upper_limit, probes forward
      directly from MAX(account_id) to detect brand-new registrations with zero waste.
    """
    job_name = f"discovery_{realm}"
    app_id = os.getenv("WARGAMING_APP_ID")
    if not app_id:
        return 0

    client = WargamingAPIClient(application_id=app_id, realm=realm, rate_limiter=GLOBAL_LIMITER)
    config = REGIONS.get(realm, REGIONS["na"])
    
    with Session(engine) as session:
        state = session.exec(select(PipelineState).where(PipelineState.job_name == job_name)).first()
        max_db_id = session.exec(select(func.max(Player.account_id)).where(Player.realm == realm)).one_or_none() or config["high_water_mark"]

    is_frontier_mode = False
    current_id = config["high_water_mark"]

    if state:
        # Check if already in frontier delta mode
        if (
            state.status == "standby"
            or state.cursor_value >= config["upper_limit"]
            or (state.details and "Frontier Delta" in state.details)
        ):
            is_frontier_mode = True
            current_id = max_db_id
        elif config["high_water_mark"] <= state.cursor_value < config["upper_limit"]:
            current_id = state.cursor_value

    new_found = 0
    total_scanned = 0
    consecutive_empty = 0
    now = datetime.now(timezone.utc)
    max_seen_id = max_db_id

    # If in frontier mode, probe a compact leading-edge window (e.g. 10 chunks)
    effective_chunks = min(chunk_count, 10) if is_frontier_mode else chunk_count

    try:
        for _ in range(effective_chunks):
            batch = list(range(current_id, current_id + BATCH_SIZE))
            data = await client.get_player_info(batch)
            total_scanned += len(batch)
            
            batch_found = 0
            if data:
                with Session(engine) as session:
                    acc_ids = [int(k) for k, v in data.items() if v]
                    if acc_ids:
                        existing_ids = set(session.exec(select(Player.account_id).where(Player.account_id.in_(acc_ids))).all())
                        for acc_id_str, info in data.items():
                            if not info:
                                continue
                            acc_id = int(acc_id_str)
                            if acc_id not in existing_ids:
                                new_player = Player(
                                    account_id=acc_id,
                                    nickname=info.get("nickname") or f"Player_{acc_id}",
                                    realm=realm,
                                    last_battle_time=info.get("last_battle_time"),
                                    hidden_profile=bool(info.get("hidden_profile", False)),
                                    leveling_tier=info.get("leveling_tier"),
                                    created_at=datetime.fromtimestamp(info.get("created_at", int(now.timestamp())), tz=timezone.utc),
                                    last_updated=now
                                )
                                session.add(new_player)
                                new_found += 1
                                batch_found += 1
                                if acc_id > max_seen_id:
                                    max_seen_id = acc_id
                        session.commit()

            if batch_found > 0:
                consecutive_empty = 0
            else:
                consecutive_empty += 1

            current_id += BATCH_SIZE

            # Check if we reached the live edge: 5 empty batches past max_db_id or reached upper_limit
            if (current_id >= max_db_id and consecutive_empty >= 5) or current_id >= config["upper_limit"]:
                is_frontier_mode = True
                current_id = max_seen_id
                break

        if is_frontier_mode:
            status = "standby"
            details = f"Frontier Delta: Live edge at ID {max_seen_id:,} • Awaiting new registrations"
            range_start = config["high_water_mark"]
            range_end = max_seen_id
            cursor_to_report = max_seen_id
        else:
            status = "running"
            details = f"Cursor at {current_id:,} • Discovered {new_found} new players in pass"
            range_start = config["high_water_mark"]
            range_end = config["upper_limit"]
            cursor_to_report = current_id

        update_heartbeat(
            job_name,
            cursor_to_report,
            status,
            details,
            range_start=range_start,
            range_end=range_end
        )
        record_progress_sample(job_name, cursor_to_report, total_scanned, new_found)

    finally:
        await client.close()

    return new_found

async def run_clan_crawler(realm: str = "eu", max_pages: int = 10) -> int:
    """
    Fast-track discovery by indexing official clan rosters.
    Each batch of 20 clans returns hundreds of active players in a single API round-trip.
    """
    job_name = f"clan_crawler_{realm}"
    app_id = os.getenv("WARGAMING_APP_ID")
    if not app_id:
        return 0

    client = WargamingAPIClient(application_id=app_id, realm=realm, rate_limiter=GLOBAL_LIMITER)
    current_page = 1
    with Session(engine) as session:
        state = session.exec(select(PipelineState).where(PipelineState.job_name == job_name)).first()
        if state and state.cursor_value > 0:
            current_page = state.cursor_value

    now = datetime.now(timezone.utc)
    clans_ingested = 0
    players_ingested = 0

    try:
        for page in range(current_page, current_page + max_pages):
            try:
                clans_data = await client.get_clans_list(page_no=page, limit=100)
            except Exception as e:
                err_str = str(e)
                if "504" in err_str or "SOURCE_NOT_AVAILABLE" in err_str or "NOT_FOUND" in err_str:
                    print(f"[{job_name}] End of clan directory reached at page {page} ({err_str}). Resetting to page 1.")
                    current_page = 1
                    break
                else:
                    raise

            if not clans_data:
                # End of clan directory -> Reset to page 1 for next sweep
                print(f"[{job_name}] End of clans reached at page {page}. Resetting to page 1.")
                current_page = 1
                break

            clan_ids = [c["clan_id"] for c in clans_data if "clan_id" in c]
            if not clan_ids:
                current_page = page + 1
                continue

            # Batch query clan details and rosters in chunks of 20
            for i in range(0, len(clan_ids), 20):
                chunk = clan_ids[i:i + 20]
                try:
                    details_data = await client.get_clans_batch_info(chunk)
                except Exception as e:
                    print(f"[{job_name}] Warning: Failed to fetch clan batch {chunk[:3]}: {e}")
                    continue

                if not details_data:
                    continue

                with Session(engine) as session:
                    create_partition_if_not_exists(session.get_bind(), now)
                    for cid_str, cinfo in details_data.items():
                        if not cinfo:
                            continue
                        cid = int(cid_str)
                        clans_ingested += 1
                        
                        existing_clan = session.get(Clan, cid)
                        if not existing_clan:
                            c_created = None
                            if cinfo.get("created_at"):
                                c_created = datetime.fromtimestamp(cinfo["created_at"], tz=timezone.utc)
                            new_clan = Clan(
                                clan_id=cid,
                                tag=cinfo.get("tag") or f"[{cid}]",
                                name=cinfo.get("name") or f"Clan_{cid}",
                                realm=realm,
                                members_count=cinfo.get("members_count", 0),
                                description=cinfo.get("description"),
                                leader_name=cinfo.get("leader_name"),
                                created_at=c_created,
                                updated_at=now
                            )
                            session.add(new_clan)

                        members = cinfo.get("members", {})
                        if members:
                            m_ids = [int(mid) for mid in members.keys()]
                            existing_ids = set(session.exec(select(Player.account_id).where(Player.account_id.in_(m_ids))).all())
                            for mid_str, minfo in members.items():
                                mid = int(mid_str)
                                if mid not in existing_ids:
                                    p_created = None
                                    if minfo.get("joined_at"):
                                        p_created = datetime.fromtimestamp(minfo["joined_at"], tz=timezone.utc)
                                    player = Player(
                                        account_id=mid,
                                        nickname=minfo.get("account_name") or f"Player_{mid}",
                                        realm=realm,
                                        clan_id=cid,
                                        last_battle_time=None,
                                        hidden_profile=False,
                                        created_at=p_created or now,
                                        last_updated=now
                                    )
                                    session.add(player)
                                    players_ingested += 1
                    session.commit()

            current_page = page + 1

        # Always update heartbeat and persist the latest cursor/reset
        report_page = current_page if current_page > 1 else 1
        update_heartbeat(
            job_name,
            cursor=current_page,
            status="running",
            details=f"Page {report_page} • {clans_ingested} clans, {players_ingested} players discovered"
        )
        record_progress_sample(job_name, current_page, clans_ingested, players_ingested)

    except Exception as e:
        print(f"[{job_name}] Clan crawler error: {e}")
        update_heartbeat(job_name, cursor=current_page, status="error", details=str(e)[:250])
    finally:
        await client.close()

    return players_ingested

def generate_daily_rollup(db_engine=None):
    """Generates daily summary rows for daily_server_stats table using weighted server totals."""
    now = datetime.now(timezone.utc)
    stat_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    with Session(db_engine or housekeeping_engine) as session:
        existing = session.exec(
            select(DailyServerStats).where(DailyServerStats.stat_date == stat_date)
        ).first()
        if existing:
            return

        bind = session.get_bind()
        is_postgres = getattr(bind.dialect, "name", "") == "postgresql"
        if is_postgres:
            sql = text("""
                SELECT 
                    COUNT(DISTINCT account_id) as active_players,
                    COALESCE(SUM(battles), 0) as battles_fought,
                    COALESCE(SUM(damage_dealt), 0) as damage_dealt,
                    COALESCE(AVG(wins::numeric * 100.0 / NULLIF(battles, 0)), 0) as mean_wr
                FROM (
                    SELECT DISTINCT ON (account_id) account_id, wins, battles, damage_dealt
                    FROM player_snapshot
                    WHERE timestamp >= :start_time AND timestamp < :end_time
                    ORDER BY account_id, timestamp DESC
                ) s
                WHERE battles > 0
            """)
        else:
            sql = text("""
                SELECT 
                    COUNT(DISTINCT account_id) as active_players,
                    COALESCE(SUM(battles), 0) as battles_fought,
                    COALESCE(SUM(damage_dealt), 0) as damage_dealt,
                    COALESCE(AVG(wins * 100.0 / NULLIF(battles, 0)), 0) as mean_wr
                FROM player_snapshot
                WHERE timestamp >= :start_time AND timestamp < :end_time AND battles > 0
            """)
        start_time = datetime.fromisoformat(f"{stat_date}T00:00:00+00:00")
        end_time = datetime.fromisoformat(f"{stat_date}T23:59:59+00:00")
        
        result = session.execute(sql, {"start_time": start_time, "end_time": end_time}).first()
        if is_postgres:
            # Planner estimate instead of count(*) over ~5M players (AGENTS.md rule 2)
            total_players = session.execute(
                text("SELECT reltuples::bigint FROM pg_class WHERE relname = 'player'")
            ).scalar()
        else:
            total_players = session.exec(select(func.count(Player.account_id))).one()

        battles_fought = int(result[1] or 0)
        damage_dealt = int(result[2] or 0)
        calc_mean_damage = round(float(damage_dealt) / float(battles_fought), 0) if battles_fought > 0 else 0.0

        rollup = DailyServerStats(
            stat_date=stat_date,
            realm="all",
            active_players=int(result[0] or 0),
            battles_fought=battles_fought,
            damage_dealt=damage_dealt,
            total_tracked_players=int(total_players or 0),
            mean_win_rate=round(float(result[3] or 0.0), 2),
            mean_damage=calc_mean_damage
        )
        session.add(rollup)
        session.commit()
        print(f"[Rollup] Saved daily_server_stats for {stat_date}: {rollup.active_players} active players, mean damage: {calc_mean_damage}.")

LEADERBOARD_CATEGORIES = {
    "win_rate": "win_rate",
    "damage": "avg_damage",
    "battles": "battles",
    "frags": "kd_ratio",
}
LEADERBOARD_REALMS = ["all", "na", "eu", "asia"]


def refresh_leaderboard_cache(db_engine=None):
    """
    Precomputes top 50 leaderboard entries across categories, modes, and realms.
    Every read is an index range scan on player_leaderboard_stats
    (idx_pls_mode_realm_* / idx_pls_mode_*); player_snapshot is never touched.
    """
    print("[Leaderboard Cache] Refreshing precomputed rankings...")
    with Session(db_engine or housekeeping_engine) as session:
        for mode in LEADERBOARD_MODES:
            min_battles = 500 if mode == "pvp" else 20
            for realm in LEADERBOARD_REALMS:
                realm_clause = "AND realm = :realm" if realm != "all" else ""
                for category, sort_col in LEADERBOARD_CATEGORIES.items():
                    try:
                        query = text(f"""
                            SELECT nickname, account_id, realm, battles, wins, win_rate, avg_damage, frags, survived, kd_ratio
                            FROM player_leaderboard_stats
                            WHERE mode = :mode {realm_clause} AND battles >= :min_battles
                            ORDER BY {sort_col} DESC
                            LIMIT 50
                        """)
                        rows = session.execute(
                            query, {"mode": mode, "realm": realm, "min_battles": min_battles}
                        ).fetchall()
                        leaderboard = []
                        for rank, r in enumerate(rows, start=1):
                            leaderboard.append({
                                "rank": rank,
                                "nickname": r[0],
                                "accountId": r[1],
                                "realm": r[2],
                                "battles": r[3] or 0,
                                "wins": r[4] or 0,
                                "winRate": float(r[5] or 0.0),
                                "avgDamage": int(r[6] or 0),
                                "frags": r[7] or 0,
                                "survived": r[8] or 0,
                                "kd": float(r[9] or 0.0)
                            })

                        payload_str = json.dumps(leaderboard)
                        cache_entry = session.get(LeaderboardCache, (category, mode, realm))
                        if not cache_entry:
                            cache_entry = LeaderboardCache(
                                category=category,
                                mode=mode,
                                realm=realm,
                                payload=payload_str,
                                updated_at=datetime.now(timezone.utc)
                            )
                        else:
                            cache_entry.payload = payload_str
                            cache_entry.updated_at = datetime.now(timezone.utc)
                        session.add(cache_entry)
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        print(f"[Leaderboard Cache Error] {category}/{mode}/{realm}: {e}")


LEADERBOARD_SYNC_JOB = "leaderboard_sync"
LEADERBOARD_SYNC_BATCH = 2000

_SNAPSHOT_COLUMNS = (
    "account_id", "timestamp", "battles", "wins", "damage_dealt", "frags", "survived",
    "solo_battles", "solo_wins", "div2_battles", "div2_wins",
    "div3_battles", "div3_wins", "rank_battles", "rank_wins",
)


def sync_leaderboard_stats(
    time_budget_s: float = 45.0,
    batch_size: int = LEADERBOARD_SYNC_BATCH,
    db_engine=None,
) -> int:
    """
    Incremental, cursor-based reconciliation of player_leaderboard_stats for all
    modes (pvp, solo, div, rank). New snapshots are already written through by
    refresh_known_players; this sweep backfills solo/div/rank for existing
    accounts and repairs drift.

    Each batch walks the next `batch_size` account_ids from the player primary key
    and reads their latest snapshot through player_snapshot_pkey
    (account_id, timestamp) - index range scans only. The cursor persists in
    pipeline_state so the sweep resumes across cycles and restarts.

    Returns the number of accounts processed. time_budget_s <= 0 runs a full pass.
    """
    db_engine = db_engine or housekeeping_engine
    started = datetime.now(timezone.utc)
    cursor = 0
    with Session(db_engine) as session:
        st = session.get(PipelineState, LEADERBOARD_SYNC_JOB)
        if st and st.cursor_value:
            cursor = int(st.cursor_value)

    processed = 0
    pass_complete = False
    while True:
        with Session(db_engine) as session:
            account_rows = session.execute(
                text("""
                    SELECT account_id, nickname, realm FROM player
                    WHERE account_id > :cursor
                    ORDER BY account_id
                    LIMIT :lim
                """),
                {"cursor": cursor, "lim": batch_size},
            ).fetchall()
            if not account_rows:
                cursor = 0
                pass_complete = True
                break

            lo, hi = account_rows[0][0], account_rows[-1][0]
            players = {r[0]: (r[1], r[2]) for r in account_rows}
            cols = ", ".join(f"s.{c}" if c != "timestamp" else 's."timestamp"' for c in _SNAPSHOT_COLUMNS)
            snapshots = session.execute(
                text(f"""
                    SELECT DISTINCT ON (s.account_id) {cols}
                    FROM player_snapshot s
                    WHERE s.account_id BETWEEN :lo AND :hi
                    ORDER BY s.account_id, s."timestamp" DESC
                """)
                if is_postgres_engine(db_engine) else
                text(f"""
                    SELECT {cols}
                    FROM player_snapshot s
                    WHERE s.account_id BETWEEN :lo AND :hi
                      AND s."timestamp" = (
                          SELECT MAX(s2."timestamp") FROM player_snapshot s2
                          WHERE s2.account_id = s.account_id
                      )
                """),
                {"lo": lo, "hi": hi},
            ).fetchall()

            rows = []
            for snap in snapshots:
                snap_map = dict(zip(_SNAPSHOT_COLUMNS, snap))
                acc_id = snap_map["account_id"]
                if acc_id not in players:
                    continue
                ts = snap_map["timestamp"]
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                if ts.tzinfo is None:
                    # player_snapshot.timestamp is stored as naive UTC
                    ts = ts.replace(tzinfo=timezone.utc)
                nickname, realm = players[acc_id]
                rows.extend(build_leaderboard_rows(acc_id, nickname, realm, snap_map, ts))
            try:
                upsert_leaderboard_rows(session, rows)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"[Leaderboard Stats Error] accounts {lo}..{hi}: {e}")

        processed += len(account_rows)
        cursor = int(account_rows[-1][0])
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        if time_budget_s > 0 and elapsed >= time_budget_s:
            break

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    update_heartbeat(
        LEADERBOARD_SYNC_JOB,
        cursor=cursor,
        status="idle" if pass_complete else "running",
        details=(
            f"Reconciled {processed:,} accounts in {elapsed:.1f}s"
            + (" - pass complete, restarting from first account" if pass_complete else f" (cursor {cursor:,})")
        ),
    )
    print(f"[Leaderboard Stats] Reconciled {processed} accounts in {elapsed:.1f}s (cursor {cursor}).")
    return processed

def prune_old_progress_samples(db_engine=None):
    """Prunes progress samples older than 14 days to prevent unbounded growth."""
    try:
        with Session(db_engine or housekeeping_engine) as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=14)
            session.execute(
                text("DELETE FROM pipeline_progress_sample WHERE sampled_at < :cutoff"),
                {"cutoff": cutoff}
            )
            session.commit()
    except Exception:
        pass

async def run_housekeeping_step(loop_count: int, label: str, fn, *args) -> bool:
    """
    Runs a blocking housekeeping step in a worker thread while the event loop keeps
    the orchestrator heartbeat fresh every HOUSEKEEPING_HEARTBEAT_INTERVAL_S.
    Errors are logged and swallowed so ingestion always resumes.
    """
    started = datetime.now(timezone.utc)
    details = f"Cycle #{loop_count}: Housekeeping - {label}"
    update_heartbeat("pipeline_orchestrator", status="running", details=details)
    task = asyncio.create_task(asyncio.to_thread(fn, *args))
    while True:
        done, _ = await asyncio.wait({task}, timeout=HOUSEKEEPING_HEARTBEAT_INTERVAL_S)
        if done:
            break
        elapsed = int((datetime.now(timezone.utc) - started).total_seconds())
        update_heartbeat("pipeline_orchestrator", status="running", details=f"{details} ({elapsed}s elapsed)")
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    try:
        task.result()
        print(f"[Housekeeping] {label} finished in {elapsed:.1f}s")
        return True
    except Exception as e:
        print(f"[Housekeeping] {label} failed after {elapsed:.1f}s: {e}")
        return False


async def main():
    """High-throughput concurrent orchestrator."""
    print("Starting WoWS High-Throughput Pipeline Worker v3...")
    update_heartbeat("pipeline_orchestrator", status="running", details="Pipeline worker v3 started")

    loop_count = 0
    while True:
        try:
            loop_count += 1
            update_heartbeat(
                "pipeline_orchestrator",
                status="running",
                details=f"Cycle #{loop_count}: Executing concurrent throughput tasks"
            )

            # Concurrent Execution of Ingestion Tasks under shared 10 req/s rate limiter
            await asyncio.gather(
                # 1. Fast-track active commanders via clan indexing (EU + ASIA)
                run_clan_crawler(realm="eu", max_pages=5),
                run_clan_crawler(realm="asia", max_pages=5),
                # 2. Continuous historical range sweepers
                discover_new_players(realm="eu", chunk_count=35),
                discover_new_players(realm="asia", chunk_count=15),
                discover_new_players(realm="na", chunk_count=10),
                # 3. Telemetry refresh for existing commanders
                refresh_known_players(realm="na", limit=1500),
                refresh_known_players(realm="eu", limit=1500),
                refresh_known_players(realm="asia", limit=1500),
                return_exceptions=True
            )

            # Daily rollup, leaderboard cache refresh & database housekeeping every 10 cycles (~5-10 minutes)
            if loop_count == 1 or loop_count % 10 == 0:
                for label, step in (
                    ("daily rollup", generate_daily_rollup),
                    ("prune progress samples", prune_old_progress_samples),
                    ("leaderboard stats sync", sync_leaderboard_stats),
                    ("leaderboard cache refresh", refresh_leaderboard_cache),
                ):
                    await run_housekeeping_step(loop_count, label, step)

            update_heartbeat(
                "pipeline_orchestrator",
                status="running",
                details=f"Cycle #{loop_count} complete. Standing by for next burst."
            )
            await asyncio.sleep(5)

        except Exception as e:
            print(f"[Orchestrator Error] {e}")
            traceback.print_exc()
            update_heartbeat("pipeline_orchestrator", status="error", details=str(e)[:250])
            await asyncio.sleep(15)

if __name__ == "__main__":
    import sys
    if "--backfill-leaderboard" in sys.argv:
        # One-off full pass: populates solo/div/rank for every tracked account
        sync_leaderboard_stats(time_budget_s=0)
        if is_postgres_engine(engine):
            # Sampled statistics refresh so the planner picks idx_pls_mode_realm_* for new modes
            with engine.connect() as conn:
                conn.execute(text("ANALYZE player_leaderboard_stats"))
                conn.commit()
        refresh_leaderboard_cache()
    else:
        asyncio.run(main())
