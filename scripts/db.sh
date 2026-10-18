#!/usr/bin/env bash
# ==============================================================================
# WoWS Stats Tracker — Developer Database Tunnel & Shell Helper
# Connects to private AWS RDS via EC2 SSH Bastion Tunnel
# ==============================================================================

set -euo pipefail

KEY_PATH="${KEY_PATH:-$HOME/.ssh/wows-stats-ec2-key.pem}"
EC2_HOST="${EC2_HOST:-44.253.134.12}"
RDS_HOST="${RDS_HOST:-wows-stats-db.cy2fcthbqjrl.us-west-2.rds.amazonaws.com}"
LOCAL_PORT="${LOCAL_PORT:-5433}"
DB_NAME="${DB_NAME:-wows_stats}"
DB_USER="${DB_USER:-wows_admin}"

usage() {
    echo "Usage: $0 [tunnel|psql|setup-analyst]"
    echo ""
    echo "Commands:"
    echo "  tunnel         Open background SSH tunnel (localhost:${LOCAL_PORT} -> RDS:5432)"
    echo "  psql           Open psql prompt connected to RDS through the tunnel"
    echo "  setup-analyst  Create read-only 'wows_analyst' user on RDS"
    echo ""
    exit 1
}

cmd="${1:-}"

case "$cmd" in
    tunnel)
        echo "Opening SSH tunnel via ${EC2_HOST}..."
        echo "Local port: ${LOCAL_PORT} -> ${RDS_HOST}:5432"
        ssh -i "${KEY_PATH}" -N -L "${LOCAL_PORT}:${RDS_HOST}:5432" "ubuntu@${EC2_HOST}" &
        TUNNEL_PID=$!
        echo "Tunnel running with PID: ${TUNNEL_PID}"
        echo "Connection string: postgresql://${DB_USER}@localhost:${LOCAL_PORT}/${DB_NAME}"
        wait ${TUNNEL_PID}
        ;;
    psql)
        echo "Connecting to RDS via localhost:${LOCAL_PORT}..."
        # Password lives only in the server's backend/.env; fetch it unless PGPASSWORD is already set.
        if [ -z "${PGPASSWORD:-}" ]; then
            PGPASSWORD=$(ssh -i "${KEY_PATH}" "ubuntu@${EC2_HOST}" "grep '^DB_PASSWORD=' /home/ubuntu/app/backend/.env | cut -d= -f2-")
        fi
        PGPASSWORD="${PGPASSWORD}" psql -h localhost -p "${LOCAL_PORT}" -U "${DB_USER}" -d "${DB_NAME}"
        ;;
    setup-analyst)
        echo "Setting up read-only user 'wows_analyst'..."
        # The analyst password is generated on the server and kept in backend/.env (ANALYST_DB_PASSWORD).
        ssh -i "${KEY_PATH}" "ubuntu@${EC2_HOST}" '
            ENV_FILE=/home/ubuntu/app/backend/.env
            if ! grep -q "^ANALYST_DB_PASSWORD=" "$ENV_FILE"; then
                echo "ANALYST_DB_PASSWORD=$(openssl rand -hex 24)" >> "$ENV_FILE"
            fi
            ANALYST_DB_PASSWORD=$(grep "^ANALYST_DB_PASSWORD=" "$ENV_FILE" | cut -d= -f2-)
            docker exec -i -e ANALYST_DB_PASSWORD="$ANALYST_DB_PASSWORD" wows-backend python -
        ' << 'EOF'
import os
from main import engine
from sqlmodel import Session, text

pw = os.environ["ANALYST_DB_PASSWORD"].replace("'", "''")
with Session(engine) as s:
    s.exec(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'wows_analyst') THEN
                CREATE ROLE wows_analyst WITH LOGIN;
            END IF;
        END
        $$;
    """))
    s.exec(text(f"ALTER ROLE wows_analyst WITH LOGIN PASSWORD '{pw}'"))
    s.exec(text("""
        GRANT CONNECT ON DATABASE wows_stats TO wows_analyst;
        GRANT USAGE ON SCHEMA public TO wows_analyst;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO wows_analyst;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO wows_analyst;
    """))
    s.commit()
    print("Role wows_analyst configured. Password: ANALYST_DB_PASSWORD in /home/ubuntu/app/backend/.env")
EOF
        ;;
    *)
        usage
        ;;
esac
