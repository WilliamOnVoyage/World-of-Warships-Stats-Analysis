from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine
from datetime import datetime

class Player(SQLModel, table=True):
    __tablename__ = "player"
    
    account_id: int = Field(primary_key=True)
    nickname: str = Field(index=True)
    realm: str = Field(default="na", index=True)
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PlayerSnapshot(SQLModel, table=True):
    __tablename__ = "player_snapshot"
    __table_args__ = (
        {"postgresql_partition_by": "RANGE (timestamp)"}
    )
    
    # Composite PK required for native partitioning in Postgres
    account_id: int = Field(primary_key=True, foreign_key="player.account_id")
    timestamp: datetime = Field(primary_key=True)
    
    battles: int = Field(default=0)
    wins: int = Field(default=0)
    damage_dealt: int = Field(default=0)
    survived: int = Field(default=0)
    frags: int = Field(default=0)
    xp: int = Field(default=0)


def create_partition_if_not_exists(engine: Engine, dt: datetime):
    """
    Creates a monthly partition for the PlayerSnapshot table dynamically if it doesn't exist.
    E.g., for dt = 2026-06-18, creates table "player_snapshot_2026_06"
    """
    partition_name = f"player_snapshot_{dt.strftime('%Y_%m')}"
    
    # Calculate start and end bounds for the month
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
    
    with engine.begin() as conn:
        conn.execute(create_stmt)
