# WoWS Stats Tracker — Developer & Operations Runbook

> **Service Version:** v2.0.0 (Naval Record Office Edition)  
> **Production Server (EC2):** `44.253.134.12`  
> **Database:** AWS RDS PostgreSQL (`wows-stats-db.cy2fcthbqjrl.us-west-2.rds.amazonaws.com`)  
> **Analytics Lakehouse:** Amazon S3 (`s3://wows-stats-analytics/`)  

---

## 1. System Architecture

```text
[Wargaming.net API] (10 req/s, whitelisted IP: 44.253.134.12)
       │
       ├───► Telemetry Refresher (100 IDs / batch, known accounts from DB)
       └───► Discovery Scout (scans above high-water marks: NA 1.075B+, EU 720M+, Asia 2.060B+)
                   │
                   ▼
       [PostgreSQL RDS (OLTP)] ──(Nightly 02:00 UTC)──► [Amazon S3 (Parquet OLAP)]
         • player (3.27M+ accounts)                        • 10x compressed Snappy/ZSTD
         • player_snapshot (diff-only time series)          • ~$1.05 / month storage
         • daily_server_stats                              • Queryable via DuckDB
                   │
                   ▼
         [FastAPI Backend :8000]
                   │
                   ▼
         [Next.js Frontend :3000] (Naval Record Office Theme)
```

---

## 2. Operational Health & Diagnostics CLI

We provide a developer CLI script [`scripts/ops.sh`](file:///Users/zml/Workspace/World-of-Warships-Stats-Analysis/scripts/ops.sh) to inspect and control production services:

```bash
# Check container status, host RAM/disk, and pipeline heartbeats
./scripts/ops.sh status

# Tail real-time logs for any service
./scripts/ops.sh logs scraper
./scripts/ops.sh logs backend
./scripts/ops.sh logs frontend

# Restart the background scraper worker
./scripts/ops.sh restart-scraper

# Pull latest master branch and rebuild containers on EC2
./scripts/ops.sh deploy
```

---

## 3. Developer Database Access

The PostgreSQL RDS instance is intentionally located inside a private VPC. Developers access the database securely through an SSH bastion tunnel:

### 3.1 One-Command Tunnel
```bash
# Open tunnel on local port 5433
./scripts/db.sh tunnel
```
You can now connect any SQL tool (DataGrip, DBeaver, TablePlus, VS Code SQLTools, pandas) to:
```text
postgresql://wows_admin@localhost:5433/wows_stats
```

### 3.2 Read-Only Analyst Role
To create or rotate a read-only user (`wows_analyst`) safe against accidental drops or writes:
```bash
./scripts/db.sh setup-analyst
```
Credentials:
- **Username:** `wows_analyst`
- **Password:** Printed securely during `setup-analyst` execution
- **Host:** `localhost:5433` (through tunnel)

---

## 4. Internal Developer REST API (`/internal/*`)

All internal endpoints require the `X-Internal-Key` HTTP header (configured via `INTERNAL_API_KEY` in `backend/.env`):

### 4.1 Check Pipeline Status & Heartbeats
```bash
curl -s -H "X-Internal-Key: <YOUR_INTERNAL_API_KEY>" \
  "http://44.253.134.12:8000/internal/pipeline/status" | jq .
```

### 4.2 Query Recently Active Players
```bash
curl -s -H "X-Internal-Key: <YOUR_INTERNAL_API_KEY>" \
  "http://44.253.134.12:8000/internal/players/active?days=30&limit=20" | jq .
```

### 4.3 Trigger Parquet Data Lake Export
```bash
curl -s -X POST -H "X-Internal-Key: <YOUR_INTERNAL_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-10-05"}' \
  "http://44.253.134.12:8000/internal/analytics/export" | jq .
```

---

## 5. Analytical Data Mining with DuckDB

For heavy trend analysis, machine learning, and cohort segmentation across millions of player records, use DuckDB locally on your Mac:

```bash
# Run the starter analysis script
python scripts/analyze.py
```

Or query Parquet files directly in Python:
```python
import duckdb

con = duckdb.connect()

# Query S3 directly without downloading datasets!
df = con.execute("""
    SELECT 
        CASE WHEN wins * 100.0 / NULLIF(battles, 0) >= 60 THEN 'Unicum' ELSE 'Average' END AS cohort,
        avg(damage_dealt / battles) AS avg_damage,
        count(DISTINCT account_id) AS player_count
    FROM read_parquet('s3://wows-stats-analytics/snapshots/*/*/*/*.parquet')
    WHERE battles >= 500
    GROUP BY 1
""").df()

print(df)
```

---

## 6. Tiered Alerting & Incident Playbook

### Active AWS Notification Setup
- **SNS Topic:** `arn:aws:sns:us-west-2:910534718184:WoWS-Stats-Critical-Alerts`
- **Subscribed Email:** `endeavourwilliam.zhou@gmail.com`
- **Anti-Fatigue Policy:** Multi-period thresholds on AWS CloudWatch + 12-hour cooldown deduplication on pipeline stalls. Zero email bombardment.

### Tier 1: Catastrophic Alerts (Immediate Response via CloudWatch)
- **Alarm 1: `wows-ec2-instance-failed`**
  - Metric: `StatusCheckFailed >= 1` for 2 consecutive minutes on EC2 `i-06bef9ba2c963cd36`.
  - Action: Reboot EC2 instance or check AWS Management Console.
- **Alarm 2: `wows-rds-storage-critical`**
  - Metric: `FreeStorageSpace <= 2 GB` for 10 consecutive minutes on RDS `wows-stats-db`.
  - Action: Modify RDS storage: `aws rds modify-db-instance --db-instance-identifier wows-stats-db --allocated-storage 50 --apply-immediately`.

### Tier 2: Pipeline Scraper Stall (Hourly Health Monitor with 12h Cooldown)
- **Monitor:** `/home/ubuntu/app/scripts/check_health.sh` scheduled via cron every hour (`0 * * * *`).
- **Condition:** Latest heartbeat across `pipeline_state` older than 45 minutes.
- **Suppression:** Maximum 1 alert per 12 hours. Suppressed while in degraded state to protect your inbox. Automatically resets upon recovery.
- **Action:** Run `./scripts/ops.sh logs scraper`. If frozen, restart scraper via `./scripts/ops.sh restart-scraper`.

### Tier 3: Informational / Daily Telemetry (Zero Email Policy)
- Routine performance and daily rollups are strictly silent (no emails sent).
- Retained in PostgreSQL (`SELECT * FROM daily_server_stats ORDER BY stat_date DESC LIMIT 7;`) and visible on web dashboard.

---

## 7. Zero Data Loss Policy
- **Tenant:** All historical snapshots and player records are immutable.
- Table partitions are generated automatically each month (`player_snapshot_YYYY_MM`).
- Migrations must strictly use `ADD COLUMN IF NOT EXISTS` and never execute destructive `DROP TABLE` or `TRUNCATE`.
