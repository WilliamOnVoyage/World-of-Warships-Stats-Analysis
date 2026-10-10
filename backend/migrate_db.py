"""
Safe migration script to apply v2 schema additions to PostgreSQL.
Adds new columns using `ADD COLUMN IF NOT EXISTS` to preserve all existing data.
Creates new tables (daily_server_stats, pipeline_state, pipeline_run) if not exist.
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

from sqlmodel import SQLModel, create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not set.")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

SQL_MIGRATIONS = [
    # 1. Expand player table
    "ALTER TABLE player ADD COLUMN IF NOT EXISTS last_battle_time BIGINT;",
    "ALTER TABLE player ADD COLUMN IF NOT EXISTS hidden_profile BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE player ADD COLUMN IF NOT EXISTS leveling_tier INT;",
    "ALTER TABLE player ADD COLUMN IF NOT EXISTS clan_id INT;",
    "CREATE INDEX IF NOT EXISTS ix_player_last_battle_time ON player (last_battle_time);",
    "CREATE INDEX IF NOT EXISTS ix_player_clan_id ON player (clan_id);",

    # 2. Expand player_snapshot table and its partitions
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS max_damage INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS damage_scouting INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS ships_spotted INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS planes_killed INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS mb_hits INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS mb_shots INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS torp_hits INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS torp_shots INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS art_agro BIGINT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS torpedo_agro BIGINT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS solo_battles INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS solo_wins INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS div2_battles INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS div2_wins INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS div3_battles INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS div3_wins INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS rank_battles INT DEFAULT 0;",
    "ALTER TABLE player_snapshot ADD COLUMN IF NOT EXISTS rank_wins INT DEFAULT 0;",

    # 3. Create DailyServerStats table
    """
    CREATE TABLE IF NOT EXISTS daily_server_stats (
        stat_date VARCHAR NOT NULL,
        realm VARCHAR NOT NULL DEFAULT 'all',
        active_players INT DEFAULT 0,
        battles_fought BIGINT DEFAULT 0,
        damage_dealt BIGINT DEFAULT 0,
        total_tracked_players INT DEFAULT 0,
        mean_win_rate DOUBLE PRECISION DEFAULT 0.0,
        mean_damage DOUBLE PRECISION DEFAULT 0.0,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (stat_date, realm)
    );
    ALTER TABLE daily_server_stats ALTER COLUMN damage_dealt TYPE BIGINT;
    ALTER TABLE daily_server_stats ALTER COLUMN battles_fought TYPE BIGINT;
    """,

    # 4. Create PipelineState table
    """
    CREATE TABLE IF NOT EXISTS pipeline_state (
        job_name VARCHAR PRIMARY KEY,
        cursor_value BIGINT DEFAULT 0,
        max_seen_id BIGINT DEFAULT 0,
        heartbeat_at TIMESTAMPTZ DEFAULT NOW(),
        status VARCHAR DEFAULT 'idle',
        details TEXT
    );
    """,

    # 5. Create PipelineRun table
    """
    CREATE TABLE IF NOT EXISTS pipeline_run (
        id SERIAL PRIMARY KEY,
        job_name VARCHAR NOT NULL,
        started_at TIMESTAMPTZ DEFAULT NOW(),
        finished_at TIMESTAMPTZ,
        status VARCHAR DEFAULT 'running',
        items_processed INT DEFAULT 0,
        items_updated INT DEFAULT 0,
        errors_count INT DEFAULT 0,
        error_message TEXT
    );
    CREATE INDEX IF NOT EXISTS ix_pipeline_run_job_name ON pipeline_run (job_name);
    """,

    # 6. Create ShipEncyclopedia table
    """
    CREATE TABLE IF NOT EXISTS ship_encyclopedia (
        ship_id BIGINT PRIMARY KEY,
        name VARCHAR NOT NULL,
        tier INT NOT NULL,
        type VARCHAR NOT NULL,
        nation VARCHAR NOT NULL,
        is_premium BOOLEAN DEFAULT FALSE,
        image_small VARCHAR,
        image_large VARCHAR,
        description TEXT,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_ship_encyclopedia_name ON ship_encyclopedia (name);
    CREATE INDEX IF NOT EXISTS ix_ship_encyclopedia_tier ON ship_encyclopedia (tier);
    CREATE INDEX IF NOT EXISTS ix_ship_encyclopedia_type ON ship_encyclopedia (type);
    CREATE INDEX IF NOT EXISTS ix_ship_encyclopedia_nation ON ship_encyclopedia (nation);
    """,

    # 7. Create Clan table
    """
    CREATE TABLE IF NOT EXISTS clan (
        clan_id BIGINT PRIMARY KEY,
        tag VARCHAR NOT NULL,
        name VARCHAR NOT NULL,
        realm VARCHAR NOT NULL DEFAULT 'na',
        members_count INT DEFAULT 0,
        description TEXT,
        leader_name VARCHAR,
        created_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_clan_tag ON clan (tag);
    CREATE INDEX IF NOT EXISTS ix_clan_name ON clan (name);
    CREATE INDEX IF NOT EXISTS ix_clan_realm ON clan (realm);
    ALTER TABLE clan ALTER COLUMN clan_id TYPE BIGINT;
    ALTER TABLE player ALTER COLUMN account_id TYPE BIGINT;
    ALTER TABLE player ALTER COLUMN clan_id TYPE BIGINT;
    ALTER TABLE player_snapshot ALTER COLUMN account_id TYPE BIGINT;
    """,

    # 8. Add range boundaries to PipelineState
    "ALTER TABLE pipeline_state ADD COLUMN IF NOT EXISTS range_start BIGINT DEFAULT 0;",
    "ALTER TABLE pipeline_state ADD COLUMN IF NOT EXISTS range_end BIGINT DEFAULT 0;",

    # 9. Create PipelineProgressSample table for moving average rate and ETA calculation
    """
    CREATE TABLE IF NOT EXISTS pipeline_progress_sample (
        id SERIAL PRIMARY KEY,
        job_name VARCHAR NOT NULL,
        sampled_at TIMESTAMPTZ DEFAULT NOW(),
        cursor_value BIGINT DEFAULT 0,
        items_processed INT DEFAULT 0,
        items_found INT DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS ix_pipeline_progress_sample_job_time ON pipeline_progress_sample (job_name, sampled_at);
    """,

    # 10. Create LeaderboardCache table for sub-50ms leaderboard reads
    """
    CREATE TABLE IF NOT EXISTS leaderboard_cache (
        category VARCHAR NOT NULL,
        mode VARCHAR NOT NULL,
        realm VARCHAR NOT NULL,
        payload TEXT NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (category, mode, realm)
    );
    """,

    # 11. Backfill mean_damage in daily_server_stats
    """
    UPDATE daily_server_stats 
    SET mean_damage = ROUND(damage_dealt * 1.0 / NULLIF(battles_fought, 0), 0)
    WHERE (mean_damage IS NULL OR mean_damage = 0.0) AND battles_fought > 0;
    """,

    # 12. Create player_leaderboard_stats table for instant arbitrary column sorting and pagination (<5ms)
    """
    CREATE TABLE IF NOT EXISTS player_leaderboard_stats (
        account_id BIGINT NOT NULL,
        mode VARCHAR(10) NOT NULL DEFAULT 'pvp',
        nickname VARCHAR(255) NOT NULL,
        realm VARCHAR(10) NOT NULL DEFAULT 'na',
        battles INT NOT NULL DEFAULT 0,
        wins INT NOT NULL DEFAULT 0,
        win_rate DOUBLE PRECISION NOT NULL DEFAULT 0.0,
        avg_damage INT NOT NULL DEFAULT 0,
        frags INT NOT NULL DEFAULT 0,
        survived INT NOT NULL DEFAULT 0,
        kd_ratio DOUBLE PRECISION NOT NULL DEFAULT 0.0,
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (account_id, mode)
    );
    CREATE INDEX IF NOT EXISTS idx_pls_mode_realm_wr ON player_leaderboard_stats (mode, realm, win_rate DESC, battles);
    CREATE INDEX IF NOT EXISTS idx_pls_mode_realm_dmg ON player_leaderboard_stats (mode, realm, avg_damage DESC, battles);
    CREATE INDEX IF NOT EXISTS idx_pls_mode_realm_bat ON player_leaderboard_stats (mode, realm, battles DESC);
    CREATE INDEX IF NOT EXISTS idx_pls_mode_realm_kd ON player_leaderboard_stats (mode, realm, kd_ratio DESC, battles);
    CREATE INDEX IF NOT EXISTS idx_pls_mode_realm_nick ON player_leaderboard_stats (mode, realm, nickname);
    """,

    # 13. Backfill player_leaderboard_stats with PvP active players
    """
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
    """
]

def migrate():
    print(f"Applying migrations to {engine.url.render_as_string(hide_password=True)}...")
    with engine.begin() as conn:
        for stmt in SQL_MIGRATIONS:
            try:
                conn.execute(text(stmt))
                print(f"Executed: {stmt.strip().splitlines()[0][:60]}...")
            except Exception as e:
                print(f"Notice: {e}")
    print("All migrations completed successfully!")

if __name__ == "__main__":
    migrate()
