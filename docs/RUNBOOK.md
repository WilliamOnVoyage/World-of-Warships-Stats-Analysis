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
- **Password:** generated on the server; read it with
  `ssh -i ~/.ssh/wows-stats-ec2-key.pem ubuntu@44.253.134.12 "grep ^ANALYST_DB_PASSWORD= ~/app/backend/.env"`
- **Host:** `localhost:5433` (through tunnel)

Re-running `setup-analyst` is idempotent; delete the `ANALYST_DB_PASSWORD` line from the server's `.env` first to rotate it.

---

## 4. Internal Developer REST API (`/internal/*`)

The backend listens on `127.0.0.1:8000` on the EC2 host only (port 8000 is closed in the security group). The public site reaches it through the frontend's `/api/*` proxy. All internal endpoints require the `X-Internal-Key` header, whose value lives only in the server's `backend/.env` as `INTERNAL_API_KEY`.

Open a tunnel and load the key once per shell:
```bash
ssh -i ~/.ssh/wows-stats-ec2-key.pem -N -L 8000:127.0.0.1:8000 ubuntu@44.253.134.12 &
export WOWS_KEY=$(ssh -i ~/.ssh/wows-stats-ec2-key.pem ubuntu@44.253.134.12 "grep ^INTERNAL_API_KEY= ~/app/backend/.env | cut -d= -f2-")
```
Swagger UI is then at http://localhost:8000/docs.

### 4.1 Check Pipeline Status & Heartbeats
```bash
curl -s -H "X-Internal-Key: $WOWS_KEY" "http://localhost:8000/internal/pipeline/status" | jq .
```

### 4.2 Query Recently Active Players
```bash
curl -s -H "X-Internal-Key: $WOWS_KEY" "http://localhost:8000/internal/players/active?days=30&limit=20" | jq .
```

### 4.3 Ad-hoc Read-Only SQL Query Runner
Avoid full-table scans (`count(*)` over `player`); prefer `pg_class.reltuples` and indexed predicates.
```bash
curl -s -X POST -H "X-Internal-Key: $WOWS_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT relname, reltuples::bigint FROM pg_class WHERE relname IN (\u0027player\u0027, \u0027player_leaderboard_stats\u0027);"}' \
  "http://localhost:8000/internal/query" | jq .
```

### 4.4 Trigger Parquet Data Lake Export
```bash
curl -s -X POST -H "X-Internal-Key: $WOWS_KEY" \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-10-05"}' \
  "http://localhost:8000/internal/analytics/export" | jq .
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

---

## 8. Scheduled Jobs on the EC2 Host (`crontab -l` as `ubuntu`)

| Schedule | Command | Log |
| :--- | :--- | :--- |
| `0 * * * *` | `scripts/check_health.sh`: pipeline heartbeat / API probe, SNS alert with 12h cooldown | `~/health_check.log` |
| `0 2 * * *` | `scripts/export_daily.sh`: exports yesterday's `player_snapshot` rows to `s3://wows-stats-analytics/snapshots/year=YYYY/month=MM/date=YYYY-MM-DD/` | `~/export.log` |

Backfill a missed day: `ssh ... "~/app/scripts/export_daily.sh 2026-10-07"`. The exporter exits non-zero when nothing reached S3 and deletes its local copy after a successful upload.

---

## 9. Secrets, Network Access & Infrastructure-as-Code

### 9.1 Secrets
- Every secret lives only in `/home/ubuntu/app/backend/.env` on the EC2 host (mode `600`): `DATABASE_URL`/`DB_PASSWORD` (RDS master), `INTERNAL_API_KEY`, `ANALYST_DB_PASSWORD`, `GF_SECURITY_ADMIN_PASSWORD` (Grafana admin), `WARGAMING_APP_ID`.
- The code has no fallback secrets: the backend rejects every `/internal/*` call if `INTERNAL_API_KEY` is unset, and `scripts/db.sh` fetches passwords from the server over SSH.
- Values that were committed in the past (before Oct 2026) were all rotated and are no longer valid.

To rotate the RDS master password: write the new value to `DATABASE_URL` and `DB_PASSWORD` in the server `.env`, run `aws rds modify-db-instance --db-instance-identifier wows-stats-db --master-user-password <new> --apply-immediately`, wait for `PendingModifiedValues` to clear, then `docker compose up -d --force-recreate backend scraper grafana`. Rotate Grafana admin with `docker exec wows-grafana grafana cli admin reset-admin-password <new>`.

### 9.2 Network access (security group `wows-stats-stack-EC2SecurityGroup-*`)
- Public: `3000` (frontend), `80`/`443` (reserved).
- SSH `22`: restricted to the operator's IP (`/32`). If your IP changes, either update the rule:
  ```bash
  aws ec2 authorize-security-group-ingress --region us-west-2 --group-id sg-01397a3d1827db4ba --protocol tcp --port 22 --cidr $(curl -s https://checkip.amazonaws.com)/32
  ```
  or get a shell without SSH via SSM: `aws ssm start-session --region us-west-2 --target i-06bef9ba2c963cd36`.
- Backend `8000`: not exposed. Compose binds it to `127.0.0.1` and the security group has no rule for it.

### 9.3 CloudFormation (`infrastructure/template.yaml`, stack `wows-stats-stack`)
The template mirrors the live resources (t3.small, Ubuntu 24.04 AMI, SSH CIDR parameter, no port 8000, SNS + S3 inline policies). The deployed stack itself was not updated: applying the template would change the recorded instance type, and EC2 changes may stop or replace the instance. Before any `update-stack`, create a change set and review it, and pass the **current** RDS password as `DBPassword` (the stack's stored parameter is the pre-rotation value).
