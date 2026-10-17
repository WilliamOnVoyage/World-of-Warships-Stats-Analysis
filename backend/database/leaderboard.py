"""
Write-through helpers for player_leaderboard_stats.

Every snapshot we store is turned into one row per leaderboard mode (pvp, solo,
div, rank) and upserted by primary key (account_id, mode), so leaderboard reads
never need to scan player_snapshot.
"""
from datetime import datetime
from typing import Any, Dict, List, Mapping

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from database.models import PlayerLeaderboardStats

LEADERBOARD_MODES = ("pvp", "solo", "div", "rank")
MIN_MODE_BATTLES = 20

_UPDATE_COLUMNS = (
    "nickname", "realm", "battles", "wins", "win_rate",
    "avg_damage", "frags", "survived", "kd_ratio", "updated_at",
)


def _mode_battles_wins(mode: str, s: Mapping[str, Any]) -> tuple:
    if mode == "solo":
        return s.get("solo_battles") or 0, s.get("solo_wins") or 0
    if mode == "div":
        return (
            (s.get("div2_battles") or 0) + (s.get("div3_battles") or 0),
            (s.get("div2_wins") or 0) + (s.get("div3_wins") or 0),
        )
    if mode == "rank":
        return s.get("rank_battles") or 0, s.get("rank_wins") or 0
    return s.get("battles") or 0, s.get("wins") or 0


def build_leaderboard_rows(
    account_id: int,
    nickname: str,
    realm: str,
    snapshot: Mapping[str, Any],
    updated_at: datetime,
) -> List[Dict[str, Any]]:
    """
    Builds player_leaderboard_stats rows for every mode with >= 20 battles.
    `snapshot` uses player_snapshot column names. Damage, frags and K/D come from
    the overall PvP block (the API does not split them per mode).
    """
    pvp_battles = int(snapshot.get("battles") or 0)
    pvp_wins = int(snapshot.get("wins") or 0)
    damage = int(snapshot.get("damage_dealt") or 0)
    frags = int(snapshot.get("frags") or 0)
    survived = int(snapshot.get("survived") or 0)
    solo_battles = int(snapshot.get("solo_battles") or 0)

    avg_damage = int(round(damage / pvp_battles)) if pvp_battles > 0 else 0
    deaths = pvp_battles - survived
    kd_ratio = round(frags / deaths, 2) if deaths > 0 else float(frags)

    rows = []
    for mode in LEADERBOARD_MODES:
        battles, wins = _mode_battles_wins(mode, snapshot)
        battles, wins = int(battles), int(wins)
        if battles < MIN_MODE_BATTLES:
            continue
        win_rate = round(wins * 100.0 / battles, 2)
        # Distorted legacy PvP payloads (near-zero WR over huge counts, no solo data)
        if mode == "pvp" and win_rate < 5.0 and battles > 20000 and solo_battles == 0:
            continue
        rows.append({
            "account_id": int(account_id),
            "mode": mode,
            "nickname": nickname,
            "realm": realm,
            "battles": battles,
            "wins": wins,
            "win_rate": win_rate,
            "avg_damage": avg_damage,
            "frags": frags,
            "survived": survived,
            "kd_ratio": kd_ratio,
            "updated_at": updated_at,
        })
    return rows


def upsert_leaderboard_rows(session: Any, rows: List[Dict[str, Any]]) -> int:
    """
    Upserts rows by primary key (account_id, mode). An existing row is only
    overwritten by data that is at least as new. Does not commit.
    """
    if not rows:
        return 0
    dialect = getattr(session.get_bind().dialect, "name", "")
    insert_fn = pg_insert if dialect == "postgresql" else sqlite_insert
    table = PlayerLeaderboardStats.__table__
    stmt = insert_fn(table).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[table.c.account_id, table.c.mode],
        set_={col: stmt.excluded[col] for col in _UPDATE_COLUMNS},
        where=table.c.updated_at <= stmt.excluded.updated_at,
    )
    session.execute(stmt)
    return len(rows)
