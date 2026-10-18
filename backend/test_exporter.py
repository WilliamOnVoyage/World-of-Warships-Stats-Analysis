import sqlite3
import sys
import types
from datetime import datetime

import pyarrow.parquet as pq
from sqlalchemy import create_engine, text

from worker import exporter


def _seed_engine(tmp_path):
    # PARSE_DECLTYPES makes TIMESTAMP columns come back as datetime, like psycopg2 does.
    engine = create_engine(
        f"sqlite:///{tmp_path / 'export.db'}",
        connect_args={"detect_types": sqlite3.PARSE_DECLTYPES},
    )
    int_cols = ", ".join(f"{c} BIGINT" for c in exporter.INT_COLUMNS)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE player (account_id BIGINT PRIMARY KEY, realm TEXT)"))
        conn.execute(text(f"CREATE TABLE player_snapshot (account_id BIGINT, timestamp TIMESTAMP, {int_cols})"))
        for aid in range(1, 8):
            conn.execute(text("INSERT INTO player VALUES (:a, 'eu')"), {"a": aid})
        rows = [(aid, datetime(2026, 10, 5, aid, 0, 0)) for aid in range(1, 8)]
        rows += [(1, datetime(2026, 10, 4, 23, 59, 59)), (2, datetime(2026, 10, 6, 0, 30, 0))]
        placeholders = ", ".join(f":{c}" for c in exporter.INT_COLUMNS)
        for aid, ts in rows:
            params = {c: 10_000_000_000 + aid for c in exporter.INT_COLUMNS}
            params.update(aid=aid, ts=ts)
            conn.execute(
                text(f"INSERT INTO player_snapshot VALUES (:aid, :ts, {placeholders})"),
                params,
            )
    return engine


def _fake_boto3(uploads):
    class FakeS3:
        def upload_file(self, local_file, bucket, key):
            uploads.append((bucket, key, pq.read_table(local_file)))

    return types.SimpleNamespace(client=lambda name: FakeS3())


def test_export_streams_batches_and_uploads(tmp_path, monkeypatch):
    uploads = []
    monkeypatch.setattr(exporter, "engine", _seed_engine(tmp_path))
    monkeypatch.setattr(exporter, "EXPORT_BATCH_SIZE", 3)  # 7 rows -> 3 row groups
    monkeypatch.setattr(exporter, "LOCAL_DATA_DIR", str(tmp_path / "lake"))
    monkeypatch.setitem(sys.modules, "boto3", _fake_boto3(uploads))

    dest = exporter.export_date_to_parquet("2026-10-05")

    key = "snapshots/year=2026/month=10/date=2026-10-05/snapshots.parquet"
    assert dest == f"s3://{exporter.S3_BUCKET}/{key}"
    (_, uploaded_key, table), = uploads
    assert uploaded_key == key
    # Day window excludes neighbouring days (exact-midnight edge is Postgres-only: SQLite compares text)
    assert table.num_rows == 7
    assert table.column("damage_dealt").to_pylist()[0] > 2**31  # bigint preserved
    assert table.schema.field("realm").type == "string"
    # Local copy removed after a successful upload
    assert not (tmp_path / "lake" / key).exists()


def test_export_empty_day_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "engine", _seed_engine(tmp_path))
    monkeypatch.setattr(exporter, "LOCAL_DATA_DIR", str(tmp_path / "lake"))
    monkeypatch.setitem(sys.modules, "boto3", _fake_boto3([]))

    assert exporter.export_date_to_parquet("2026-09-01") is None
