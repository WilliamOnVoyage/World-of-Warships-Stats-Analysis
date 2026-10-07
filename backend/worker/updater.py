"""
WoWS Data Pipeline Worker v2
- Decoupled Discovery Scout (finds new players above high-water marks)
- Telemetry Refresher (updates known players in DB in 100-ID batches with diff-only snapshotting)
- Multi-Region Support (NA, EU, ASIA)
- PostgreSQL Bulk Upserts (1 round-trip per 100 accounts)
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
from database.models import (
    Player,
    PlayerSnapshot,
    DailyServerStats,
    PipelineState,
    PipelineRun,
    create_partition_if_not_exists,
)
from api.wargaming import WargamingAPIClient

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wows_dev.db")
engine = create_engine(DATABASE_URL)

REGIONS = {
    "na": {"high_water_mark": 1_075_000_000, "upper_limit": 1_100_000_000},
    "eu": {"high_water_mark": 500_000_000, "upper_limit": 760_000_000},
    "asia": {"high_water_mark": 2_000_000_000, "upper_limit": 2_050_000_000},
}

BATCH_SIZE = 100

def update_heartbeat(job_name: str, cursor: int = 0, status: str = "running", details: str = ""):
    """Updates the pipeline_state table with current heartbeat."""
    try:
        with Session(engine) as session:
            stmt = select(PipelineState).where(PipelineState.job_name == job_name)
            state = session.exec(stmt).first()
            now = datetime.now(timezone.utc)
            if not state:
                state = PipelineState(
                    job_name=job_name,
                    cursor_value=cursor,
                    heartbeat_at=now,
                    status=status,
                    details=details
                )
            else:
                state.cursor_value = cursor
                state.heartbeat_at = now
                state.status = status
                if details:
                    state.details = details
            session.add(state)
            session.commit()
    except Exception as e:
        print(f"[{job_name}] Failed to update heartbeat: {e}")

async def refresh_known_players(realm: str = "na", limit: int = 5000):
    """
    Refreshes players that already exist in our DB.
    Batches 100 accounts per Wargaming API call.
    Uses diff-only snapshot insertion (only saves when battles/last_battle_time increased).
    """
    job_name = f"telemetry_{realm}"
    app_id = os.getenv("WARGAMING_APP_ID")
    if not app_id:
        print(f"[{job_name}] WARGAMING_APP_ID not set. Skipping.")
        return 0

    client = WargamingAPIClient(application_id=app_id, realm=realm)
    
    with Session(engine) as session:
        # Select players needing update (oldest updated first)
        query = (
            select(Player.account_id, Player.last_battle_time)
            .where(Player.realm == realm)
            .order_by(Player.last_updated.asc())
            .limit(limit)
        )
        players_to_refresh = session.exec(query).all()

    if not players_to_refresh:
        update_heartbeat(
            job_name=job_name,
            cursor=0,
            status="idle",
            details=f"Queue empty (0 tracked {realm.upper()} commanders pending)"
        )
        await client.close()
        return 0

    known_battle_times = {row[0]: (row[1] or 0) for row in players_to_refresh}
    account_ids = list(known_battle_times.keys())
    
    processed_count = 0
    updated_snapshots = 0
    now = datetime.now(timezone.utc)

    try:
        for i in range(0, len(account_ids), BATCH_SIZE):
            chunk = account_ids[i:i + BATCH_SIZE]
            data = await client.get_player_info(
                chunk,
                extra="statistics.pvp_solo,statistics.pvp_div2,statistics.pvp_div3,statistics.rank_solo,statistics.pve"
            )
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

                    # DIFF-ONLY SNAPSHOTTING: Only write a snapshot if the player had activity
                    if not hidden and curr_battles > 0 and (new_lbt > prev_lbt or prev_lbt == 0):
                        solo = stats_overall.get("pvp_solo") or {}
                        div2 = stats_overall.get("pvp_div2") or {}
                        div3 = stats_overall.get("pvp_div3") or {}
                        rank = stats_overall.get("rank_solo") or {}

                        snapshot = PlayerSnapshot(
                            account_id=acc_id,
                            timestamp=now,
                            battles=curr_battles,
                            wins=stats_pvp.get("wins", 0),
                            damage_dealt=stats_pvp.get("damage_dealt", 0),
                            survived=stats_pvp.get("survived_battles", 0),
                            frags=stats_pvp.get("frags", 0),
                            xp=stats_pvp.get("xp", 0),
                            max_damage=stats_pvp.get("max_damage_dealt", 0),
                            damage_scouting=stats_pvp.get("damage_scouting", 0),
                            ships_spotted=stats_pvp.get("ships_spotted", 0),
                            planes_killed=stats_pvp.get("planes_killed", 0),
                            mb_hits=stats_pvp.get("main_battery", {}).get("hits", 0),
                            mb_shots=stats_pvp.get("main_battery", {}).get("shots", 0),
                            torp_hits=stats_pvp.get("torpedoes", {}).get("hits", 0),
                            torp_shots=stats_pvp.get("torpedoes", {}).get("shots", 0),
                            art_agro=stats_pvp.get("art_agro", 0),
                            torpedo_agro=stats_pvp.get("torpedo_agro", 0),
                            solo_battles=solo.get("battles", 0),
                            solo_wins=solo.get("wins", 0),
                            div2_battles=div2.get("battles", 0),
                            div2_wins=div2.get("wins", 0),
                            div3_battles=div3.get("battles", 0),
                            div3_wins=div3.get("wins", 0),
                            rank_battles=rank.get("battles", 0),
                            rank_wins=rank.get("wins", 0),
                        )
                        session.add(snapshot)
                        updated_snapshots += 1

                session.commit()
            
            update_heartbeat(
                job_name=job_name,
                cursor=i + len(chunk),
                status="running",
                details=f"Processed {processed_count} players, {updated_snapshots} active snapshots saved"
            )

    finally:
        await client.close()

    print(f"[{job_name}] Finished cycle: {processed_count} checked, {updated_snapshots} new snapshots saved.")
    return processed_count

async def discover_new_players(realm: str = "na", chunk_count: int = 100):
    """
    Scouts new account IDs beyond the high water mark for the given realm.
    Advances cursor by BATCH_SIZE (100) per request.
    """
    job_name = f"discovery_{realm}"
    app_id = os.getenv("WARGAMING_APP_ID")
    if not app_id:
        return

    client = WargamingAPIClient(application_id=app_id, realm=realm)
    config = REGIONS.get(realm, REGIONS["na"])
    
    # Retrieve current cursor from DB (enforcing valid window)
    current_id = config["high_water_mark"]
    with Session(engine) as session:
        state = session.exec(select(PipelineState).where(PipelineState.job_name == job_name)).first()
        if state and config["high_water_mark"] <= state.cursor_value < config["upper_limit"]:
            current_id = state.cursor_value

    new_found = 0
    now = datetime.now(timezone.utc)

    try:
        for _ in range(chunk_count):
            batch = list(range(current_id, current_id + BATCH_SIZE))
            # Lightweight call: no extra statistics payloads needed during discovery
            data = await client.get_player_info(batch)
            
            if data:
                with Session(engine) as session:
                    acc_ids = [int(k) for k, v in data.items() if v]
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
                    session.commit()

            current_id += BATCH_SIZE
            # Wrap around if reached upper limit
            if current_id >= config["upper_limit"]:
                current_id = config["high_water_mark"]

            update_heartbeat(job_name, current_id, "running", f"Discovered {new_found} new players so far")

    finally:
        await client.close()

    print(f"[{job_name}] Scout pass finished at ID {current_id}. Found {new_found} new players.")

def generate_daily_rollup():
    """Generates a daily summary row for daily_server_stats table."""
    now = datetime.now(timezone.utc)
    stat_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    with Session(engine) as session:
        # Check if already generated for this date
        existing = session.exec(
            select(DailyServerStats).where(DailyServerStats.stat_date == stat_date)
        ).first()
        if existing:
            return

        # Compute aggregate metrics for yesterday (using weighted server win rate)
        sql = text("""
            SELECT 
                COUNT(DISTINCT account_id) as active_players,
                COALESCE(SUM(battles), 0) as battles_fought,
                COALESCE(SUM(damage_dealt), 0) as damage_dealt,
                COALESCE(SUM(wins)::numeric * 100.0 / NULLIF(SUM(battles), 0), 0) as mean_wr
            FROM player_snapshot
            WHERE timestamp >= :start_time AND timestamp < :end_time
        """)
        start_time = datetime.fromisoformat(f"{stat_date}T00:00:00+00:00")
        end_time = datetime.fromisoformat(f"{stat_date}T23:59:59+00:00")
        
        result = session.execute(sql, {"start_time": start_time, "end_time": end_time}).first()
        total_players = session.exec(select(func.count(Player.account_id))).one()

        rollup = DailyServerStats(
            stat_date=stat_date,
            realm="all",
            active_players=int(result[0] or 0),
            battles_fought=int(result[1] or 0),
            damage_dealt=int(result[2] or 0),
            total_tracked_players=int(total_players or 0),
            mean_win_rate=round(float(result[3] or 0.0), 2),
            mean_damage=0.0
        )
        session.add(rollup)
        session.commit()
        print(f"[Rollup] Saved daily_server_stats for {stat_date}: {rollup.active_players} active players.")

async def main():
    """Continuous orchestrator loop."""
    print("Starting WoWS Data Pipeline Worker v2...")
    update_heartbeat("pipeline_orchestrator", status="running", details="Pipeline started")

    while True:
        try:
            update_heartbeat("pipeline_orchestrator", status="running", details="Initiating telemetry refresh cycle")
            # 1. Telemetry refresh for known players across regions
            for region in ["na", "eu", "asia"]:
                update_heartbeat("pipeline_orchestrator", status="running", details=f"Refreshing telemetry for {region.upper()}")
                await refresh_known_players(realm=region, limit=2000)
                await asyncio.sleep(2)

            # 2. Scout for new player registrations
            for region in ["na", "eu", "asia"]:
                update_heartbeat("pipeline_orchestrator", status="running", details=f"Scouting new registrations for {region.upper()}")
                await discover_new_players(realm=region, chunk_count=20)
                await asyncio.sleep(2)

            # 3. Generate daily rollup if needed
            generate_daily_rollup()

            # Short rest between main cycles
            update_heartbeat("pipeline_orchestrator", status="running", details="Cycle complete. Standing by for next cycle.")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"[Orchestrator Error] {e}")
            traceback.print_exc()
            update_heartbeat("pipeline_orchestrator", status="error", details=str(e)[:250])
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
