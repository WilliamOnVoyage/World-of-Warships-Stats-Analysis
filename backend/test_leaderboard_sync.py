import asyncio
import json
from datetime import datetime, timezone, timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

import database.models  # noqa: F401  (registers tables)
from database.leaderboard import build_leaderboard_rows, upsert_leaderboard_rows
from database.models import (
    LeaderboardCache,
    PipelineState,
    Player,
    PlayerLeaderboardStats,
    PlayerSnapshot,
)
from worker import updater


@pytest.fixture
def db(monkeypatch):
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    monkeypatch.setattr(updater, "engine", eng)
    monkeypatch.setattr(updater, "housekeeping_engine", eng)
    yield eng
    SQLModel.metadata.drop_all(eng)


def _snapshot(**overrides):
    base = dict(
        battles=1000, wins=600, damage_dealt=50_000_000, frags=900, survived=400,
        solo_battles=700, solo_wins=420, div2_battles=200, div2_wins=120,
        div3_battles=50, div3_wins=30, rank_battles=10, rank_wins=7,
    )
    base.update(overrides)
    return base


def test_build_rows_per_mode():
    ts = datetime(2026, 10, 17, tzinfo=timezone.utc)
    rows = {r["mode"]: r for r in build_leaderboard_rows(1, "Cmdr", "na", _snapshot(), ts)}

    # rank has only 10 battles (< 20) so it is skipped
    assert set(rows) == {"pvp", "solo", "div"}
    assert rows["pvp"]["win_rate"] == 60.0
    assert rows["solo"]["battles"] == 700 and rows["solo"]["win_rate"] == 60.0
    assert rows["div"]["battles"] == 250 and rows["div"]["wins"] == 150
    assert rows["pvp"]["avg_damage"] == 50_000
    assert rows["pvp"]["kd_ratio"] == 1.5


def test_build_rows_skips_distorted_pvp():
    ts = datetime(2026, 10, 17, tzinfo=timezone.utc)
    rows = build_leaderboard_rows(
        1, "Cmdr", "na", _snapshot(battles=30000, wins=100, solo_battles=0), ts
    )
    assert "pvp" not in {r["mode"] for r in rows}


def test_upsert_ignores_older_data(db):
    new_ts = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
    old_ts = new_ts - timedelta(hours=1)
    with Session(db) as s:
        upsert_leaderboard_rows(s, build_leaderboard_rows(1, "Cmdr", "na", _snapshot(battles=2000, wins=1000), new_ts))
        s.commit()
        upsert_leaderboard_rows(s, build_leaderboard_rows(1, "Cmdr", "na", _snapshot(), old_ts))
        s.commit()
        pvp = s.get(PlayerLeaderboardStats, (1, "pvp"))
        assert pvp.battles == 2000


def test_sync_backfills_all_modes_with_cursor(db):
    t0 = datetime(2026, 10, 1, tzinfo=timezone.utc)
    with Session(db) as s:
        for acc in (10, 20, 30):
            s.add(Player(account_id=acc, nickname=f"P{acc}", realm="eu"))
            s.add(PlayerSnapshot(account_id=acc, timestamp=t0, **_snapshot(solo_battles=100, solo_wins=10)))
            s.add(PlayerSnapshot(account_id=acc, timestamp=t0 + timedelta(days=1), **_snapshot(solo_battles=acc * 10, solo_wins=acc)))
        s.commit()

    # One batch of two accounts then stop on the time budget; cursor persists
    assert updater.sync_leaderboard_stats(time_budget_s=1e-9, batch_size=2) == 2
    with Session(db) as s:
        assert s.get(PipelineState, updater.LEADERBOARD_SYNC_JOB).cursor_value == 20
        assert s.get(PlayerLeaderboardStats, (30, "solo")) is None

    # Next run resumes after the cursor and wraps around once the pass completes
    assert updater.sync_leaderboard_stats(time_budget_s=0, batch_size=2) == 1
    with Session(db) as s:
        assert s.get(PipelineState, updater.LEADERBOARD_SYNC_JOB).cursor_value == 0
        solo = s.get(PlayerLeaderboardStats, (30, "solo"))
        assert solo.battles == 300  # latest snapshot wins
        modes = set(s.exec(select(PlayerLeaderboardStats.mode)).all())
        assert modes == {"pvp", "solo", "div"}


def test_refresh_cache_reads_summary_table(db):
    ts = datetime(2026, 10, 17, tzinfo=timezone.utc)
    with Session(db) as s:
        rows = []
        for acc, solo_wins in ((1, 30), (2, 60), (3, 45)):
            rows += build_leaderboard_rows(acc, f"P{acc}", "asia", _snapshot(solo_battles=100, solo_wins=solo_wins), ts)
        upsert_leaderboard_rows(s, rows)
        s.commit()

    updater.refresh_leaderboard_cache()

    with Session(db) as s:
        solo = json.loads(s.get(LeaderboardCache, ("win_rate", "solo", "asia")).payload)
        assert [e["accountId"] for e in solo] == [2, 3, 1]
        assert json.loads(s.get(LeaderboardCache, ("win_rate", "solo", "na")).payload) == []
        assert len(s.exec(select(LeaderboardCache)).all()) == 64


async def test_housekeeping_step_keeps_heartbeat_fresh(db, monkeypatch):
    monkeypatch.setattr(updater, "HOUSEKEEPING_HEARTBEAT_INTERVAL_S", 0.05)
    beats = []
    real = updater.update_heartbeat

    def spy(job_name, **kw):
        beats.append(kw.get("details", ""))
        real(job_name, **kw)

    monkeypatch.setattr(updater, "update_heartbeat", spy)

    def slow():
        import time
        time.sleep(0.3)

    assert await updater.run_housekeeping_step(7, "slow step", slow) is True
    assert sum("elapsed" in b for b in beats) >= 2

    def boom():
        raise RuntimeError("statement timeout")

    assert await updater.run_housekeeping_step(7, "bad step", boom) is False
