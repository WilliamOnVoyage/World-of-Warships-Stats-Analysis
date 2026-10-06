# World of Warships Stats Tracker — Naval Record Office

[![Next.js 16](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20Partitioned-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-Parquet%20Lakehouse-FFF000?style=flat-square&logo=duckdb)](https://duckdb.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20RDS%20%7C%20S3-FF9900?style=flat-square&logo=amazon-aws)](https://aws.amazon.com/)

An AI-native, high-performance web platform and automated data pipeline for tracking and visualizing World of Warships player statistics, win rates, and combat performance across all major global servers (NA, EU, ASIA). Designed in authentic **Swiss Minimalist & WWII Admiralty Naval Record Office** editorial style.

---

## 🚀 Quick Reference Links (Production Server)

The application is deployed on a dedicated AWS EC2 instance backed by AWS RDS PostgreSQL in Oregon (`us-west-2`):

| Resource | URL / Access | Description |
| :--- | :--- | :--- |
| **Live Web App** | [http://44.253.134.12:3000](http://44.253.134.12:3000) | Next.js 16 Naval Record Office UI |
| **Fleet Leaderboards** | [http://44.253.134.12:3000/#leaderboard](http://44.253.134.12:3000/#leaderboard) | Global & Regional PvP Rankings |
| **Sample Dossier** | [http://44.253.134.12:3000/player/zmlzeze](http://44.253.134.12:3000/player/zmlzeze) | Verified Combat Telemetry Profile |
| **API Documentation (Swagger)** | [http://44.253.134.12:8000/docs](http://44.253.134.12:8000/docs) | Interactive Swagger UI / OpenAPI 3.0 |
| **API Health Check** | [http://44.253.134.12:8000/health](http://44.253.134.12:8000/health) | Uptime probe (`{"status":"healthy"}`) |
| **Leaderboard API** | [http://44.253.134.12:8000/api/leaderboard](http://44.253.134.12:8000/api/leaderboard) | Top commanders by WR, damage, battles |
| **Developer Runbook** | [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Operations, incident response, & DuckDB guides |

---

## 🏛 System Architecture: Hybrid Lakehouse

```mermaid
flowchart TD
    subgraph WargamingAPI ["Wargaming.net Global APIs (10 req/s)"]
        WG_NA["api.worldofwarships.com (NA)"]
        WG_EU["api.worldofwarships.eu (EU)"]
        WG_ASIA["api.worldofwarships.asia (ASIA)"]
    end

    subgraph EC2 ["AWS EC2 (Ubuntu 24.04 - Elastic IP: 44.253.134.12)"]
        subgraph Pipeline ["Decoupled Data Pipeline v2"]
            Scout["Discovery Scout\n(Probes above high-water marks)"]
            Refresher["Telemetry Refresher\n(Batches 100 known IDs, Diff-Only)"]
            Exporter["Nightly Parquet Exporter\n(Exports daily snapshots to S3)"]
        end

        subgraph BackendService ["Backend Service (:8000)"]
            FastAPIApp["FastAPI REST API\n- SQLModel / SQLAlchemy 2.0\n- Leaderboards & Player Dossiers\n- Secure /internal/* Endpoints"]
        end

        subgraph FrontendService ["Frontend Service (:3000)"]
            NextApp["Next.js 16 App Router\n- Naval Record Office Theme\n- Archivo & IBM Plex Mono Fonts\n- Recharts Monochrome Visualizations"]
        end
    end

    subgraph AWS_RDS ["Operational DB (PostgreSQL 16)"]
        Postgres[("wows_stats DB\n- player table (3.27M+ records)\n- player_snapshot (Monthly partitioned)\n- daily_server_stats & pipeline_state")]
    end

    subgraph AWS_S3 ["Analytical Data Lake (Amazon S3)"]
        ParquetLake[("s3://wows-stats-analytics/\n- Daily 10x Compressed Parquet\n- Direct Columnar DuckDB Queries")]
    end

    WargamingAPI --> Pipeline
    Pipeline --> Postgres
    Pipeline --> ParquetLake
    Postgres --> BackendService
    BackendService --> FrontendService
    ParquetLake --> Developer["Developer DuckDB Analytics"]
```

---

## 📊 Developer Tooling & Operations

### 1. Operations CLI
```bash
# Check container status and pipeline state
./scripts/ops.sh status

# Tail service logs
./scripts/ops.sh logs scraper
```

### 2. Developer Database Access
```bash
# Open secure SSH tunnel to private RDS (localhost:5433 -> RDS:5432)
./scripts/db.sh tunnel

# Connect via psql
./scripts/db.sh psql
```

### 3. DuckDB Lakehouse Analytics
```bash
# Run starter analysis against Parquet data lake
python scripts/analyze.py
```

For full operational procedures, secret rotation, and incident playbooks, refer to [`docs/RUNBOOK.md`](docs/RUNBOOK.md).
