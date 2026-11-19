#!/usr/bin/env bash
# Tear the demo stack down: stop the app's processes, remove the floci
# container, and close every port the demo opened. The script writes crm/.env
# never, because demo_up.sh wrote it never. The demo database and the logs
# stay at crm/target/demo/, and the laptop's crm.db keeps its data.
#
# Usage, from anywhere:
#   crm/deploy/demo_down.sh
#
# Exits 0 when every port is closed, and 2 when a port still answers.
set -euo pipefail

CRM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$CRM_DIR/target/demo"

echo "== stop the processes of the demo stack"
# The group id in dev.pid covers every process demo_up.sh started. The
# patterns reach only this clone's processes, for a stack an older run left
# behind without a pid file.
if [ -f "$LOG_DIR/dev.pid" ]; then
  pgid="$(cat "$LOG_DIR/dev.pid")"
  kill -- -"$pgid" 2>/dev/null || true
  sleep 1
fi
patterns=(
  "$CRM_DIR.*uvicorn backend.main:app"
  "$CRM_DIR.*uvicorn agent.entrypoint:app"
  "$CRM_DIR.*uvicorn agent.copilot.entrypoint:app"
  "$CRM_DIR.*python -m context"
  "$CRM_DIR.*node_modules/.bin/vite"
)
for pattern in "${patterns[@]}"; do
  pkill -f "$pattern" 2>/dev/null || true
done
sleep 1

echo "== remove the floci emulator and the demo database"
docker rm -f crm-floci 2>/dev/null || true
docker rm -f crm-demo-db 2>/dev/null || true

echo "== check the ports"
failed=0
for port in 4566 5433 8000 8004 5173 8080 8081 8006; do
  if timeout 1 bash -c "</dev/tcp/127.0.0.1/$port" 2>/dev/null; then
    echo "FAIL: port $port still answers" >&2
    failed=1
  else
    echo "closed: $port"
  fi
done
if [ "$failed" -ne 0 ]; then
  exit 2
fi

echo "The demo stack is down. The next npm run dev is back on the laptop defaults."
