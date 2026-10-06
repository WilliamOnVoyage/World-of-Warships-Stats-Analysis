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
To create a read-only user (`wows_analyst`) safe against accidental drops or writes:
```bash
./scripts/db.sh setup-analyst
```
Credentials:
- **Username:** `wows_analyst`
- **Password:** `AnalystRead2026!`
- **Host:** `localhost:5433` (through tunnel)

---

## 4. Internal Developer REST API (`/internal/*`)

All internal endpoints require the `X-Internal-Key` HTTP header (set in `.env` as `INTERNAL_API_KEY`):

### 4.1 Check Pipeline Status & Heartbeats
```bash
curl -s -H "X-Internal-Key: wows-secret-internal-key-2026" \
  "http://44.253.134.12:8000/internal/pipeline/status" | jq .
```

### 4.2 Query Recently Active Players
```bash
curl -s -H "X-Internal-Key: wows-secret-internal-key-2026" \
  "http://44.253.134.12:8000/internal/players/active?days=30&limit=20" | jq .
```

### 4.3 Ad-hoc Read-Only SQL Query Runner
```bash
curl -s -X POST -H "X-Internal-Key: wows-secret-internal-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT realm, count(*) FROM player GROUP BY realm;"}' \
  "http://44.253.134.12:8000/internal/query" | jq .
```

### 4.4 Trigger Parquet Data Lake Export
```bash
curl -s -X POST -H "X-Internal-Key: wows-secret-internal-key-2026" \
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

### Tier 1: Catastrophic Alerts (Immediate Response)
- **Condition 1: Scraper Heartbeat Stale (>30 min):**
  - Symptom: `pipeline_state.heartbeat_at` is older than 30 minutes.
  - Action: Run `./scripts/ops.sh logs scraper` to view the traceback. If frozen, run `./scripts/ops.sh restart-scraper`.
- **Condition 2: Wargaming API 407 (IP Whitelist Rejection):**
  - Symptom: Logs show `407 INVALID_IP_ADDRESS` or `REQUEST_LIMIT_EXCEEDED`.
  - Action: Verify Elastic IP `44.253.134.12` is configured in Wargaming Developer Console.
- **Condition 3: RDS Storage >85% Full:**
  - Symptom: RDS free storage alert fires.
  - Action: Modify RDS storage: `aws rds modify-db-instance --db-instance-identifier wows-stats-db --allocated-storage 50 --apply-immediately`.

### Tier 2: Important Alerts (Daily Digest)
- Review daily rollup: `SELECT * FROM daily_server_stats ORDER BY stat_date DESC LIMIT 7;`.
- Check active players count and new account registrations.

### Tier 3: Informational (Weekly)
- Review weekly player growth and region distribution (NA / EU / ASIA).

---

## 7. Zero Data Loss Policy
- **Tenant:** All historical snapshots and player records are immutable.
- Table partitions are generated automatically each month (`player_snapshot_YYYY_MM`).
- Migrations must strictly use `ADD COLUMN IF NOT EXISTS` and never execute destructive `DROP TABLE` or `TRUNCATE`.
