#!/bin/bash
# WoWS Stats Scraper Health & Alert Monitor
# Strict Anti-Fatigue Policy: Max 1 email per 12 hours on failure, 0 noise when healthy.

set -euo pipefail

LOCK_FILE="/tmp/wows_scraper_alert.lock"
COOLDOWN_SECONDS=43200 # 12 hours
SNS_TOPIC="arn:aws:sns:us-west-2:910534718184:WoWS-Stats-Critical-Alerts"
AWS_REGION="us-west-2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../backend/.env"
INTERNAL_KEY="${INTERNAL_API_KEY:-}"
if [ -z "${INTERNAL_KEY}" ] && [ -f "${ENV_FILE}" ]; then
  INTERNAL_KEY=$(grep -E '^INTERNAL_API_KEY=' "${ENV_FILE}" | cut -d= -f2- | tr -d '"'"'"' || true)
fi

if [ -z "${INTERNAL_KEY}" ]; then
  echo "[$(date -u)] ERROR: INTERNAL_API_KEY is not set in environment or ${ENV_FILE}"
  exit 1
fi

STATUS_JSON=$(curl -s --max-time 10 "${API_URL}" -H "X-Internal-Key: ${INTERNAL_KEY}" || echo "")

if [ -z "${STATUS_JSON}" ]; then
  echo "[$(date -u)] Backend API is not responding."
  NOW=$(date +%s)
  if [ -f "${LOCK_FILE}" ]; then
    LAST_ALERT=$(cat "${LOCK_FILE}")
    if [ $((NOW - LAST_ALERT)) -lt ${COOLDOWN_SECONDS} ]; then
      echo "[$(date -u)] Alert suppressed (12h cooldown active)."
      exit 0
    fi
  fi
  echo "${NOW}" > "${LOCK_FILE}"
  aws sns publish \
    --topic-arn "${SNS_TOPIC}" \
    --subject "ALERT: WoWS Stats API & Backend Unresponsive" \
    --message "The backend API at ${API_URL} did not respond to health check. Further alerts suppressed for 12 hours." \
    --region "${AWS_REGION}" || true
  exit 1
fi

HEARTBEAT_AGE_MIN=$(python3 -c "
import json, sys, datetime
try:
    data = json.loads('''${STATUS_JSON}''')
    states = data.get('pipelineStates', [])
    if not states:
        print(999)
        sys.exit(0)
    now = datetime.datetime.now(datetime.timezone.utc)
    min_age = 99999
    for s in states:
        hb = s.get('heartbeat')
        if hb:
            dt = datetime.datetime.fromisoformat(hb)
            age = (now - dt).total_seconds() / 60.0
            if age < min_age:
                min_age = age
    print(int(min_age))
except Exception:
    print(999)
")

echo "[$(date -u)] Pipeline newest heartbeat age: ${HEARTBEAT_AGE_MIN} minutes"

if [ "${HEARTBEAT_AGE_MIN}" -gt 45 ]; then
  echo "[$(date -u)] Pipeline heartbeat is STALE (>45m)."
  NOW=$(date +%s)
  if [ -f "${LOCK_FILE}" ]; then
    LAST_ALERT=$(cat "${LOCK_FILE}")
    if [ $((NOW - LAST_ALERT)) -lt ${COOLDOWN_SECONDS} ]; then
      echo "[$(date -u)] Alert suppressed by 12h cooldown window."
      exit 0
    fi
  fi
  echo "${NOW}" > "${LOCK_FILE}"
  aws sns publish \
    --topic-arn "${SNS_TOPIC}" \
    --subject "ALERT: WoWS Stats Scraper Pipeline Inactive" \
    --message "WoWS Stats scraper pipeline newest heartbeat is ${HEARTBEAT_AGE_MIN} minutes old (threshold: 45 min). Next alert suppressed for 12 hours to prevent email spam. Inspect on EC2: docker logs --tail 50 wows-scraper" \
    --region "${AWS_REGION}" || true
else
  if [ -f "${LOCK_FILE}" ]; then
    echo "[$(date -u)] Pipeline recovered. Clearing suppression lock."
    rm -f "${LOCK_FILE}"
  fi
fi
