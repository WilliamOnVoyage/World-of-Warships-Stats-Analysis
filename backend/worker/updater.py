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
    PlayerLeaderboardStats,
    create_partition_if_not_exists,
)
from api.wargaming import WargamingAPIClient

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wows_dev.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

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
                        except Exception as sn_err:
                            print(f"[{job_name}] Snapshot warning for player {acc_id}: {sn_err}")

                session.commit()

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

def generate_daily_rollup():
    """Generates daily summary rows for daily_server_stats table using weighted server totals."""
    now = datetime.now(timezone.utc)
    stat_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    with Session(engine) as session:
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

def refresh_leaderboard_cache():
    """Precomputes top 50 leaderboard entries across categories, modes, and realms."""
    print("[Leaderboard Cache] Refreshing precomputed rankings...")
    categories = ["win_rate", "damage", "battles", "frags"]
    modes = ["pvp", "solo", "div", "rank"]
    realms = ["all", "na", "eu", "asia"]

    with Session(engine) as session:
        bind = session.get_bind()
        is_postgres = getattr(bind.dialect, "name", "") == "postgresql"
        if not is_postgres:
            return

        for mode in modes:
            if mode == "solo":
                b_expr = "s.solo_battles"
                w_expr = "s.solo_wins"
            elif mode == "div":
                b_expr = "(s.div2_battles + s.div3_battles)"
                w_expr = "(s.div2_wins + s.div3_wins)"
            elif mode == "rank":
                b_expr = "s.rank_battles"
                w_expr = "s.rank_wins"
            else:
                b_expr = "s.battles"
                w_expr = "s.wins"

            min_battles = 20 if mode in ["solo", "div", "rank"] else 500
            wr_calc = f"ROUND({w_expr} * 100.0 / NULLIF({b_expr}, 0), 2)"

            for realm in realms:
                realm_filter = "WHERE 1=1"
                if realm != "all":
                    realm_filter += f" AND p.realm = '{realm.lower()}'"

                for category in categories:
                    order_clause = "win_rate DESC"
                    if category == "damage":
                        order_clause = "avg_damage DESC"
                    elif category == "battles":
                        order_clause = "battles DESC"
                    elif category == "frags":
                        order_clause = "frags DESC"

                    try:
                        query = text(f"""
                            SELECT 
                                sub.nickname,
                                sub.account_id,
                                sub.realm,
                                sub.battles,
                                sub.wins,
                                sub.win_rate,
                                sub.avg_damage,
                                sub.frags,
                                sub.survived,
                                sub.kd_ratio
                            FROM (
                                SELECT DISTINCT ON (s.account_id)
                                    p.nickname,
                                    p.account_id,
                                    p.realm,
                                    {b_expr} as battles,
                                    {w_expr} as wins,
                                    {wr_calc} as win_rate,
                                    ROUND(s.damage_dealt * 1.0 / NULLIF(s.battles, 0), 0) as avg_damage,
                                    s.frags,
                                    s.survived,
                                    ROUND(s.frags * 1.0 / NULLIF(s.battles - s.survived, 0), 2) as kd_ratio
                                FROM player_snapshot s
                                JOIN player p ON s.account_id = p.account_id
                                {realm_filter} AND {b_expr} >= :min_battles
                                ORDER BY s.account_id, s.timestamp DESC
                            ) sub
                            ORDER BY {order_clause}
                            LIMIT 50
                        """).bindparams(min_battles=min_battles)

                        rows = session.execute(query).fetchall()
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
                            session.add(cache_entry)
                        else:
                            cache_entry.payload = payload_str
                            cache_entry.updated_at = datetime.now(timezone.utc)
                            session.add(cache_entry)
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        print(f"[Leaderboard Cache Error] {category}/{mode}/{realm}: {e}")

def sync_leaderboard_stats():
    """Upserts latest player combat summaries into player_leaderboard_stats for sub-5ms queries."""
    with Session(engine) as session:
        bind = session.get_bind()
        is_postgres = getattr(bind.dialect, "name", "") == "postgresql"
        if not is_postgres:
            return
        try:
            sql = text("""
                INSERT INTO player_leaderboard_stats (account_id, mode, nickname, realm, battles, wins, win_rate, avg_damage, frags, survived, kd_ratio, updated_at)
                SELECT DISTINCT ON (s.account_id)
                    s.account_id,
                    'pvp' as mode,
                    p.nickname,
                    p.realm,
                    s.battles,
                    s.wins,
                    ROUND(s.wins * 100.0 / NULLIF(s.battles, 0), 2) as win_rate,
                    ROUND(s.damage_dealt * 1.0 / NULLIF(s.battles, 0), 0) as avg_damage,
                    s.frags,
                    s.survived,
                    ROUND(s.frags * 1.0 / NULLIF(s.battles - s.survived, 0), 2) as kd_ratio,
                    s.timestamp as updated_at
                FROM player_snapshot s
                JOIN player p ON s.account_id = p.account_id
                WHERE s.battles >= 20
                ORDER BY s.account_id, s.timestamp DESC
                ON CONFLICT (account_id, mode) DO UPDATE SET
                    nickname = EXCLUDED.nickname,
                    realm = EXCLUDED.realm,
                    battles = EXCLUDED.battles,
                    wins = EXCLUDED.wins,
                    win_rate = EXCLUDED.win_rate,
                    avg_damage = EXCLUDED.avg_damage,
                    frags = EXCLUDED.frags,
                    survived = EXCLUDED.survived,
                    kd_ratio = EXCLUDED.kd_ratio,
                    updated_at = EXCLUDED.updated_at;
            """)
            session.execute(sql)
            session.commit()
            print("[Leaderboard Stats] Synchronized player_leaderboard_stats table.")
        except Exception as e:
            session.rollback()
            print(f"[Leaderboard Stats Error] {e}")

def prune_old_progress_samples():
    """Prunes progress samples older than 14 days to prevent unbounded growth."""
    try:
        with Session(engine) as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=14)
            session.execute(
                text("DELETE FROM pipeline_progress_sample WHERE sampled_at < :cutoff"),
                {"cutoff": cutoff}
            )
            session.commit()
    except Exception:
        pass

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
                generate_daily_rollup()
                prune_old_progress_samples()
                sync_leaderboard_stats()
                refresh_leaderboard_cache()

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
    asyncio.run(main())
