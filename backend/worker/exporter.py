"""
Nightly S3 Parquet Exporter for WoWS Stats Tracker (Option C Lakehouse).
Exports PostgreSQL daily snapshots to Apache Parquet with Snappy compression.
Uploads to Amazon S3 (s3://{S3_ANALYTICS_BUCKET}/snapshots/year=YYYY/month=MM/date=YYYY-MM-DD/)
or local disk fallback for developer exploration.
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from sqlmodel import create_engine, Session, text

DATABASE_URL = os.getenv("DATABASE_URL")
S3_BUCKET = os.getenv("S3_ANALYTICS_BUCKET", "wows-stats-analytics")
LOCAL_DATA_DIR = os.getenv("LOCAL_ANALYTICS_DIR", "./analytics_data")

engine = create_engine(DATABASE_URL) if DATABASE_URL else None

def export_date_to_parquet(target_date: Optional[str] = None) -> Optional[str]:
    """
    Exports snapshots for target_date (YYYY-MM-DD) into a Parquet file.
    Returns path or S3 key.
    """
    if not engine:
        print("[Exporter] DATABASE_URL not set.")
        return None

    if not target_date:
        now = datetime.now(timezone.utc)
        target_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    start_ts = f"{target_date} 00:00:00+00"
    end_ts = f"{target_date} 23:59:59+00"
    
    print(f"[Exporter] Querying snapshots for date {target_date}...")

    query = text("""
        SELECT 
            s.account_id,
            s.timestamp,
            p.realm,
            s.battles,
            s.wins,
            s.damage_dealt,
            s.survived,
            s.frags,
            s.xp,
            s.max_damage,
            s.damage_scouting,
            s.ships_spotted,
            s.planes_killed,
            s.solo_battles,
            s.solo_wins,
            s.div2_battles,
            s.div2_wins,
            s.div3_battles,
            s.div3_wins,
            s.rank_battles,
            s.rank_wins
        FROM player_snapshot s
        JOIN player p ON s.account_id = p.account_id
        WHERE s.timestamp >= :start_ts AND s.timestamp <= :end_ts
    """)

    with Session(engine) as session:
        result = session.exec(query, {"start_ts": start_ts, "end_ts": end_ts}).all()

    if not result:
        print(f"[Exporter] No snapshots found for date {target_date}.")
        return None

    # Convert to column-oriented dictionary
    columns = [
        "account_id", "timestamp", "realm", "battles", "wins", "damage_dealt",
        "survived", "frags", "xp", "max_damage", "damage_scouting", "ships_spotted",
        "planes_killed", "solo_battles", "solo_wins", "div2_battles", "div2_wins",
        "div3_battles", "div3_wins", "rank_battles", "rank_wins"
    ]
    data_dict = {col: [getattr(row, col, row[i]) for row in result] for i, col in enumerate(columns)}
    import pyarrow as pa
    import pyarrow.parquet as pq

    arrow_table = pa.Table.from_pydict(data_dict)
    
    # Save locally or to S3
    year, month, _ = target_date.split("-")
    partition_relpath = f"snapshots/year={year}/month={month}/date={target_date}"
    os.makedirs(f"{LOCAL_DATA_DIR}/{partition_relpath}", exist_ok=True)
    local_file = f"{LOCAL_DATA_DIR}/{partition_relpath}/snapshots.parquet"

    pq.write_table(arrow_table, local_file, compression="SNAPPY")
    file_size_kb = os.path.getsize(local_file) / 1024
    print(f"[Exporter] Wrote {len(result)} rows to {local_file} ({file_size_kb:.1f} KB).")

    # Upload to S3 if boto3 is available and AWS credentials configured
    try:
        import boto3
        s3 = boto3.client("s3")
        s3_key = f"{partition_relpath}/snapshots.parquet"
        s3.upload_file(local_file, S3_BUCKET, s3_key)
        print(f"[Exporter] Successfully uploaded to s3://{S3_BUCKET}/{s3_key}")
        return f"s3://{S3_BUCKET}/{s3_key}"
    except Exception as e:
        print(f"[Exporter] Note: S3 upload skipped or not configured: {e}")
        return local_file

if __name__ == "__main__":
    t_date = sys.argv[1] if len(sys.argv) > 1 else None
    export_date_to_parquet(t_date)
