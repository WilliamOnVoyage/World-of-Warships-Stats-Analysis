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

from sqlmodel import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
S3_BUCKET = os.getenv("S3_ANALYTICS_BUCKET", "wows-stats-analytics")
LOCAL_DATA_DIR = os.getenv("LOCAL_ANALYTICS_DIR", "./analytics_data")

engine = create_engine(DATABASE_URL) if DATABASE_URL else None

EXPORT_BATCH_SIZE = 50_000
INT_COLUMNS = [
    "battles", "wins", "damage_dealt", "survived", "frags", "xp", "max_damage",
    "damage_scouting", "ships_spotted", "planes_killed", "solo_battles", "solo_wins",
    "div2_battles", "div2_wins", "div3_battles", "div3_wins", "rank_battles", "rank_wins",
]

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

    next_date = (datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    start_ts = f"{target_date} 00:00:00+00"
    end_ts = f"{next_date} 00:00:00+00"
    
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
        WHERE s.timestamp >= :start_ts AND s.timestamp < :end_ts
    """)

    import pyarrow as pa
    import pyarrow.parquet as pq

    # Explicit schema so every streamed batch matches (column order == SELECT order).
    schema = pa.schema(
        [("account_id", pa.int64()), ("timestamp", pa.timestamp("us")), ("realm", pa.string())]
        + [(c, pa.int64()) for c in INT_COLUMNS]
    )

    year, month, _ = target_date.split("-")
    partition_relpath = f"snapshots/year={year}/month={month}/date={target_date}"
    os.makedirs(f"{LOCAL_DATA_DIR}/{partition_relpath}", exist_ok=True)
    local_file = f"{LOCAL_DATA_DIR}/{partition_relpath}/snapshots.parquet"

    # Stream with a server-side cursor and write one row group per batch: a full day
    # (~500K rows) held as Python objects needs ~900 MB and gets OOM-killed on the host.
    total_rows = 0
    writer = None
    try:
        with engine.connect().execution_options(stream_results=True, yield_per=EXPORT_BATCH_SIZE) as conn:
            result = conn.execute(query, {"start_ts": start_ts, "end_ts": end_ts})
            for rows in result.partitions():
                columns = list(zip(*rows))
                batch = pa.Table.from_arrays(
                    [pa.array(col, type=field.type) for col, field in zip(columns, schema)],
                    schema=schema,
                )
                if writer is None:
                    writer = pq.ParquetWriter(local_file, schema, compression="SNAPPY")
                writer.write_table(batch)
                total_rows += batch.num_rows
    finally:
        if writer is not None:
            writer.close()

    if total_rows == 0:
        print(f"[Exporter] No snapshots found for date {target_date}.")
        return None

    file_size_kb = os.path.getsize(local_file) / 1024
    print(f"[Exporter] Wrote {total_rows} rows to {local_file} ({file_size_kb:.1f} KB).")

    # Upload to S3 if boto3 is available and AWS credentials configured
    try:
        import boto3
        s3 = boto3.client("s3")
        s3_key = f"{partition_relpath}/snapshots.parquet"
        s3.upload_file(local_file, S3_BUCKET, s3_key)
        print(f"[Exporter] Successfully uploaded to s3://{S3_BUCKET}/{s3_key}")
        # S3 is the system of record; don't let daily files pile up on the host disk.
        os.remove(local_file)
        return f"s3://{S3_BUCKET}/{s3_key}"
    except Exception as e:
        print(f"[Exporter] Note: S3 upload skipped or not configured: {e}")
        return local_file

if __name__ == "__main__":
    t_date = sys.argv[1] if len(sys.argv) > 1 else None
    dest = export_date_to_parquet(t_date)
    # Non-zero exit when nothing reached S3, so cron logs and callers can tell.
    sys.exit(0 if dest and dest.startswith("s3://") else 1)
