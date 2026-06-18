import os
from sqlmodel import SQLModel, create_engine
from database.models import Player, PlayerSnapshot, create_partition_if_not_exists
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://wows_admin:DevAdminPass2026@localhost:5432/wows_stats_dev")
engine = create_engine(DATABASE_URL)

def init_db():
    print("Creating tables...")
    SQLModel.metadata.create_all(engine)
    print("Creating initial partition for this month...")
    create_partition_if_not_exists(engine, datetime.utcnow())
    print("Done!")

if __name__ == "__main__":
    init_db()
