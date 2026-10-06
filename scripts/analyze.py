"""
WoWS Data Lakehouse Analytics Starter Kit (DuckDB).
Queries Parquet files directly from Amazon S3 or local directory.
Runs multi-core columnar analytics across millions of snapshots in seconds.

Usage:
    python scripts/analyze.py
"""
import os
import sys

def run_analysis():
    try:
        import duckdb
    except ImportError:
        print("DuckDB not installed. Run: pip install duckdb")
        sys.exit(1)

    s3_bucket = os.getenv("S3_ANALYTICS_BUCKET", "wows-stats-analytics")
    local_dir = os.getenv("LOCAL_ANALYTICS_DIR", "./analytics_data")

    # Connect to in-memory DuckDB
    con = duckdb.connect()

    # Check for local parquet files first, else configure S3
    parquet_glob = f"{local_dir}/snapshots/*/*/*/*.parquet"
    if not os.path.exists(local_dir):
        print(f"Local analytics dir not found, configuring S3 extension (s3://{s3_bucket}/)...")
        con.execute("INSTALL httpfs; LOAD httpfs;")
        parquet_glob = f"s3://{s3_bucket}/snapshots/*/*/*/*.parquet"

    print(f"\n=== WoWS Lakehouse Analytics (Source: {parquet_glob}) ===\n")

    # Example 1: Skill Tier Cohort Segmentation
    print("1. Win Rate Cohort Distribution & Average Damage:")
    try:
        df_cohorts = con.execute(f"""
            SELECT 
                CASE 
                    WHEN wins * 100.0 / NULLIF(battles, 0) >= 60 THEN 'Unicum (>60%)'
                    WHEN wins * 100.0 / NULLIF(battles, 0) >= 54 THEN 'Good (54-60%)'
                    WHEN wins * 100.0 / NULLIF(battles, 0) >= 48 THEN 'Average (48-54%)'
                    ELSE 'Below Average (<48%)'
                END AS skill_bracket,
                COUNT(DISTINCT account_id) AS player_count,
                ROUND(AVG(damage_dealt * 1.0 / NULLIF(battles, 0)), 0) AS avg_damage,
                ROUND(AVG(frags * 1.0 / NULLIF(battles - survived, 0)), 2) AS avg_kd
            FROM read_parquet('{parquet_glob}')
            WHERE battles >= 100
            GROUP BY 1
            ORDER BY avg_damage DESC
        """).df()
        print(df_cohorts.to_string(index=False))
    except Exception as e:
        print(f"Note: {e}")

    # Example 2: Combat Telemetry Correlation (Spotting vs Winning)
    print("\n2. Spotting Damage & Survival Rate by Division Type:")
    try:
        df_modes = con.execute(f"""
            SELECT 
                ROUND(AVG(solo_wins * 100.0 / NULLIF(solo_battles, 0)), 2) AS solo_win_rate,
                ROUND(AVG((div2_wins + div3_wins) * 100.0 / NULLIF(div2_battles + div3_battles, 0)), 2) AS division_win_rate,
                ROUND(AVG(damage_scouting), 0) AS mean_spotting_damage
            FROM read_parquet('{parquet_glob}')
            WHERE battles >= 500
        """).df()
        print(df_modes.to_string(index=False))
    except Exception as e:
        print(f"Note: {e}")

if __name__ == "__main__":
    run_analysis()
