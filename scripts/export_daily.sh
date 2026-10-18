#!/bin/bash
# Nightly Parquet export: yesterday's player_snapshot rows -> s3://wows-stats-analytics/.
# Runs from cron on the EC2 host:
#   0 2 * * * /home/ubuntu/app/scripts/export_daily.sh >> /home/ubuntu/export.log 2>&1
# Backfill a specific day: scripts/export_daily.sh 2026-10-07

set -euo pipefail

TARGET_DATE="${1:-}"
echo "[$(date -u)] Starting Parquet export ${TARGET_DATE:-(yesterday)}"
if docker exec wows-backend python -m worker.exporter ${TARGET_DATE}; then
  echo "[$(date -u)] Export finished"
else
  echo "[$(date -u)] [EXPORT FAILED] see output above"
  exit 1
fi
