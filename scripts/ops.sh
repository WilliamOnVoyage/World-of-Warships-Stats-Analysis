#!/usr/bin/env bash
# ==============================================================================
# WoWS Stats Tracker — Operations CLI
# Quick diagnosis, container logs, throughput, and worker control
# ==============================================================================

set -euo pipefail

KEY_PATH="${KEY_PATH:-$HOME/.ssh/wows-stats-ec2-key.pem}"
EC2_HOST="${EC2_HOST:-44.253.134.12}"

cmd="${1:-status}"

case "$cmd" in
    status)
        echo "=== WoWS Operations Status ($EC2_HOST) ==="
        ssh -i "${KEY_PATH}" "ubuntu@${EC2_HOST}" '
            echo "--- Containers ---"
            docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            echo ""
            echo "--- System Resources ---"
            free -m | head -2
            df -h / | tail -1
            echo ""
            echo "--- Database Counts & Pipeline Heartbeat ---"
            docker exec -i $(docker ps -qf name=backend) python -c "
from main import engine
from sqlmodel import Session, text
with Session(engine) as s:
    players = s.exec(text(\"SELECT count(*) FROM player\")).one()[0]
    snapshots = s.exec(text(\"SELECT count(*) FROM player_snapshot\")).one()[0]
    print(f\"Total Players in DB:    {players:,}\")
    print(f\"Total Snapshots in DB:  {snapshots:,}\")
    print(\"\nPipeline States:\")
    states = s.exec(text(\"SELECT job_name, cursor_value, heartbeat_at, status, details FROM pipeline_state\")).all()
    for st in states:
        print(f\"  [{st[0]}] status={st[3]} cursor={st[1]:,} heartbeat={st[2]} | {st[4]}\")
"
        '
        ;;
    telemetry)
        echo "=== WoWS Developer Telemetry Dashboard ($EC2_HOST) ==="
        ssh -i "${KEY_PATH}" "ubuntu@${EC2_HOST}" "docker exec -i \$(docker ps -qf name=backend) python - << 'EOF'
from datetime import datetime, timezone
from main import engine
from sqlmodel import Session, text

with Session(engine) as s:
    now = datetime.now(timezone.utc)
    realms = s.execute(text(\"\"\"
        SELECT COALESCE(realm, 'unknown'), count(*) 
        FROM player 
        GROUP BY realm 
        ORDER BY count(*) DESC
    \"\"\")).fetchall()
    total_players = sum(r[1] for r in realms)
    total_snapshots = s.execute(text(\"SELECT count(*) FROM player_snapshot\")).scalar()
    recent_snapshots = s.execute(text(\"SELECT count(*) FROM player_snapshot WHERE timestamp >= NOW() - INTERVAL '24 HOURS'\")).scalar()
    
    print(\"\n[01 // FLEET REGISTRY BY REALM]\")
    for r in realms:
        print(f\"  • {r[0].upper():<6}: {r[1]:>10,} commanders\")
    print(f\"  • TOTAL : {total_players:>10,} commanders\")
    print(f\"  • SNAPSHOTS: {total_snapshots:>10,} total | {recent_snapshots:>8,} past 24h\")

    print(\"\n[02 // INGESTION PIPELINE JOBS & HEARTBEATS]\")
    jobs = s.execute(text(\"SELECT job_name, cursor_value, heartbeat_at, status, details FROM pipeline_state ORDER BY job_name\")).fetchall()
    print(f\"  {'JOB NAME':<24} {'CURSOR':<14} {'FRESHNESS':<12} {'STATUS':<10} {'DETAILS'}\")
    print(\"  \" + \"-\" * 85)
    for j in jobs:
        hb = j[2]
        age_str = f\"{int((now - hb).total_seconds() / 60)}m ago\" if hb else \"never\"
        if hb and (now - hb).total_seconds() < 60:
            age_str = \"just now\"
        details = (j[4] or \"\")[:45]
        print(f\"  {j[0]:<24} {j[1]:>12,}  {age_str:<12} {j[3]:<10} {details}\")

    print(\"\n[03 // HISTORICAL DAILY ROLLUPS]\")
    rollups = s.execute(text(\"SELECT stat_date, realm, total_tracked_players, active_players, battles_fought, mean_win_rate FROM daily_server_stats ORDER BY stat_date DESC LIMIT 5\")).fetchall()
    print(f\"  {'DATE':<12} {'THEATER':<8} {'TRACKED':<12} {'ACTIVE':<10} {'BATTLES':<14} {'SERVER WR'}\")
    print(\"  \" + \"-\" * 70)
    for ro in rollups:
        print(f\"  {ro[0]:<12} {ro[1].upper():<8} {ro[2]:>10,} {ro[3]:>8,} {ro[4]:>12,} {ro[5]:>8.2f}%\")
EOF
            echo \"\"
            echo \"[04 // INFRASTRUCTURE BUFFER]\"
            df -h / | awk 'NR==2 {print \"  • EC2 Host Storage: \" \$4 \" available / \" \$2 \" total (\" \$5 \" used)\"}'
            free -m | awk 'NR==2 {print \"  • EC2 Memory:       \" \$7 \"MB available / \" \$2 \"MB total\"}'
        "
        ;;
    logs)
        service="${2:-scraper}"
        echo "Tailing logs for wows-${service}..."
        ssh -i "${KEY_PATH}" "ubuntu@${EC2_HOST}" "docker logs -f --tail 100 wows-${service}"
        ;;
    restart-scraper)
        echo "Restarting scraper worker on ${EC2_HOST}..."
        ssh -i "${KEY_PATH}" "ubuntu@${EC2_HOST}" "docker restart wows-scraper"
        echo "Done."
        ;;
    deploy)
        echo "Deploying latest commit on ${EC2_HOST}..."
        ssh -i "${KEY_PATH}" "ubuntu@${EC2_HOST}" "
            cd /home/ubuntu/app &&
            git pull origin master &&
            docker compose build &&
            docker compose up -d
        "
        echo "Deployment complete."
        ;;
    *)
        echo "Usage: $0 [status|telemetry|logs <backend|scraper|frontend>|restart-scraper|deploy]"
        exit 1
        ;;
esac
