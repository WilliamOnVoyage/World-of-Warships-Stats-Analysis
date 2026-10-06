from typing import Optional, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import text
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Player(SQLModel, table=True):
    __tablename__ = "player"
    
    account_id: int = Field(primary_key=True)
    nickname: str = Field(index=True)
    realm: str = Field(default="na", index=True)
    last_battle_time: Optional[int] = Field(default=None, index=True)
    hidden_profile: bool = Field(default=False)
    leveling_tier: Optional[int] = Field(default=None)
    clan_id: Optional[int] = Field(default=None, index=True)
    
    last_updated: datetime = Field(default_factory=utc_now)
    created_at: datetime = Field(default_factory=utc_now)


class PlayerSnapshot(SQLModel, table=True):
    __tablename__ = "player_snapshot"
    __table_args__ = (
        {"postgresql_partition_by": "RANGE (timestamp)"}
    )
    
    # Composite PK required for native partitioning in Postgres
    account_id: int = Field(primary_key=True, foreign_key="player.account_id")
    timestamp: datetime = Field(primary_key=True)
    
    # Core PvP
    battles: int = Field(default=0)
    wins: int = Field(default=0)
    damage_dealt: int = Field(default=0)
    survived: int = Field(default=0)
    frags: int = Field(default=0)
    xp: int = Field(default=0)
    
    # Extended Combat Telemetry
    max_damage: int = Field(default=0)
    damage_scouting: int = Field(default=0)
    ships_spotted: int = Field(default=0)
    planes_killed: int = Field(default=0)
    mb_hits: int = Field(default=0)
    mb_shots: int = Field(default=0)
    torp_hits: int = Field(default=0)
    torp_shots: int = Field(default=0)
    art_agro: int = Field(default=0)
    torpedo_agro: int = Field(default=0)
    
    # Game Mode Breakdown
    solo_battles: int = Field(default=0)
    solo_wins: int = Field(default=0)
    div2_battles: int = Field(default=0)
    div2_wins: int = Field(default=0)
    div3_battles: int = Field(default=0)
    div3_wins: int = Field(default=0)
    rank_battles: int = Field(default=0)
    rank_wins: int = Field(default=0)


class DailyServerStats(SQLModel, table=True):
    __tablename__ = "daily_server_stats"
    
    stat_date: str = Field(primary_key=True) # YYYY-MM-DD
    realm: str = Field(primary_key=True, default="all")
    active_players: int = Field(default=0)
    battles_fought: int = Field(default=0)
    damage_dealt: int = Field(default=0)
    total_tracked_players: int = Field(default=0)
    mean_win_rate: float = Field(default=0.0)
    mean_damage: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=utc_now)


class PipelineState(SQLModel, table=True):
    __tablename__ = "pipeline_state"
    
    job_name: str = Field(primary_key=True)
    cursor_value: int = Field(default=0)
    max_seen_id: int = Field(default=0)
    heartbeat_at: datetime = Field(default_factory=utc_now)
    status: str = Field(default="idle")
    details: Optional[str] = Field(default=None)


class PipelineRun(SQLModel, table=True):
    __tablename__ = "pipeline_run"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    job_name: str = Field(index=True)
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: Optional[datetime] = Field(default=None)
    status: str = Field(default="running")
    items_processed: int = Field(default=0)
    items_updated: int = Field(default=0)
    errors_count: int = Field(default=0)
    error_message: Optional[str] = Field(default=None)


def create_partition_if_not_exists(bind: Any, dt: datetime):
    """
    Creates a monthly partition for the PlayerSnapshot table dynamically if it doesn't exist.
    E.g., for dt = 2026-06-18, creates table "player_snapshot_2026_06".
    Safely no-ops for non-PostgreSQL databases (e.g. SQLite in unit tests).
    """
    dialect = getattr(bind, "dialect", None)
    if dialect and dialect.name != "postgresql":
        return

    partition_name = f"player_snapshot_{dt.strftime('%Y_%m')}"
    
    start_date = f"{dt.year}-{dt.month:02d}-01"
    
    if dt.month == 12:
        end_date = f"{dt.year + 1}-01-01"
    else:
        end_date = f"{dt.year}-{dt.month + 1:02d}-01"

    create_stmt = text(f"""
        CREATE TABLE IF NOT EXISTS {partition_name} 
        PARTITION OF player_snapshot 
        FOR VALUES FROM ('{start_date}') TO ('{end_date}');
    """)
    
    if hasattr(bind, "begin"):
        with bind.begin() as conn:
            conn.execute(create_stmt)
    else:
        bind.execute(create_stmt)
