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
            cd /home/ubuntu/wows-tracker &&
            git pull origin master &&
            docker compose build &&
            docker compose up -d
        "
        echo "Deployment complete."
        ;;
    *)
        echo "Usage: $0 [status|logs <backend|scraper|frontend>|restart-scraper|deploy]"
        exit 1
        ;;
esac
