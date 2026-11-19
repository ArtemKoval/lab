#!/usr/bin/env bash
# Start the whole demo stack: the floci emulator, the wiring gate, and the crm
# app with every port bound for the web. The library pack is the active pack.
#
# Usage, from anywhere:
#   crm/deploy/demo_up.sh                 # the live route: the real agent
#   crm/deploy/demo_up.sh --emulator      # the runtime route through floci
#   crm/deploy/demo_up.sh --host 1.2.3.4  # an explicit address for the URLs
#
# ADDR is an IP address, not a name: the dev server refuses request hosts it
# doesn't know, and a name would serve every visitor a blocked page.
#
# The live route needs a model key in OPENROUTER_API_KEY in crm/.env, and the
# script refuses to start without one. The agent's own key is made here and
# shared with the backend through the environment.
#
# The script writes crm/.env never. The demo variables live only in the
# processes this script starts. The demo database lives in the compose
# Postgres, so the seed never touches the laptop's crm.db, and the teardown
# leaves nothing to undo. Logs go to crm/target/demo/.
set -euo pipefail

CRM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$CRM_DIR/target/demo"
mkdir -p "$LOG_DIR"

die() {
  echo "FAIL: $1" >&2
  exit 1
}

# The address the URLs carry. The source address of the default route is the
# one the outside world reaches; hostname -I is the fallback.
DEMO_HOST="$(ip -4 route get 1.1.1.1 2>/dev/null | sed -n 's/.* src \([0-9.]*\).*/\1/p')"
[ -n "$DEMO_HOST" ] || DEMO_HOST="$(hostname -I | awk '{print $1}')"
LIVE_AGENT=1
while [ "$#" -gt 0 ]; do
  case "$1" in
    --host) DEMO_HOST="$2"; shift 2 ;;
    --emulator) LIVE_AGENT=0; shift ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -f "$CRM_DIR/.env" ] || die "crm/.env is missing: copy .env.example to .env first"
[ -x "$CRM_DIR/.venv/bin/python" ] || die "crm/.venv is missing: run uv sync first"
AGENT_KEY="$(openssl rand -hex 16 2>/dev/null || echo "")"
if [ -z "$AGENT_KEY" ]; then
  AGENT_KEY="$("$CRM_DIR/.venv/bin/python" -c 'import secrets; print(secrets.token_hex(16))')"
fi
if [ "$LIVE_AGENT" -eq 1 ] && ! grep -q '^OPENROUTER_API_KEY=..*' "$CRM_DIR/.env"; then
  die "the live route needs a model key in OPENROUTER_API_KEY in crm/.env"
fi

# Stop the processes of an earlier run. The group id in dev.pid covers every
# process the last run started. The patterns reach only this clone's
# processes, for a stack a older run left behind without a pid file.
stop_old_processes() {
  if [ -f "$LOG_DIR/dev.pid" ]; then
    local pgid
    pgid="$(cat "$LOG_DIR/dev.pid")"
    kill -- -"$pgid" 2>/dev/null || true
    sleep 1
  fi
  local patterns=(
    "$CRM_DIR.*uvicorn backend.main:app"
    "$CRM_DIR.*uvicorn agent.entrypoint:app"
    "$CRM_DIR.*uvicorn agent.copilot.entrypoint:app"
    "$CRM_DIR.*python -m context"
    "$CRM_DIR.*node_modules/.bin/vite"
  )
  local pattern
  for pattern in "${patterns[@]}"; do
    pkill -f "$pattern" 2>/dev/null || true
  done
  sleep 1
}

wait_for_url() {
  local name="$1" url="$2"
  local try
  for try in $(seq 1 60); do
    if curl -sf --max-time 2 "$url" >/dev/null 2>&1; then
      echo "up:   $name at $url"
      return 0
    fi
    sleep 1
  done
  echo "FAIL: $name did not answer at $url within 60 seconds" >&2
  return 1
}

wait_for_port() {
  local name="$1" port="$2"
  local try
  for try in $(seq 1 60); do
    if timeout 1 bash -c "</dev/tcp/127.0.0.1/$port" 2>/dev/null; then
      echo "up:   $name on port $port"
      return 0
    fi
    sleep 1
  done
  echo "FAIL: $name did not open port $port within 60 seconds" >&2
  return 1
}

echo "== stop the processes of an earlier demo run"
stop_old_processes

echo "== start the emulator and the demo database"
cd "$CRM_DIR"
if docker compose -f deploy/compose.yaml -f deploy/compose.demo.yaml up -d 2>/dev/null; then
  echo "started the containers with compose"
else
  echo "compose is not available, so run the containers directly"
  docker rm -f crm-floci 2>/dev/null || true
  docker run -d --name crm-floci -p 4566:4566 \
    -e FLOCI_HOSTNAME=localhost \
    -e 'FLOCI_SERVICES_BEDROCK_AGENT_CORE_INVOKE_RESPONSE={"accepted": true}' \
    floci/floci:latest
  docker rm -f crm-demo-db 2>/dev/null || true
  docker run -d --name crm-demo-db -p 5433:5432 \
    -e POSTGRES_USER=crm -e POSTGRES_PASSWORD=crm -e POSTGRES_DB=crm \
    postgres:17-alpine
fi
wait_for_url "the emulator" "http://localhost:4566/_floci/health"
for try in $(seq 1 60); do
  if docker exec crm-demo-db pg_isready -U crm -d crm >/dev/null 2>&1; then
    echo "up:   the demo database answers pg_isready"
    break
  fi
  [ "$try" -eq 60 ] && { echo "FAIL: the demo database never got ready" >&2; exit 1; }
  sleep 1
done

echo "== run the wiring gate"
AWS_ENDPOINT_URL=http://localhost:4566 \
AWS_DEFAULT_REGION=us-east-1 \
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
.venv/bin/python deploy/verify_wiring.py >"$LOG_DIR/wiring.log" 2>&1 ||
  { cat "$LOG_DIR/wiring.log" >&2; die "the wiring gate failed"; }
RUNTIME_ARN="$(sed -n 's/^runtime: //p' "$LOG_DIR/wiring.log")"
[ -n "$RUNTIME_ARN" ] || die "the wiring gate printed no runtime ARN"

echo "== seed the library pack into the demo database"
export DATABASE_URL="postgresql://crm:crm@127.0.0.1:5433/crm"
export CRM_AGENT_KEY="$AGENT_KEY"
CRM_DOMAIN=library npm run seed

echo "== start the app with the demo variables"
export CRM_DOMAIN=library
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
if [ "$LIVE_AGENT" -eq 1 ]; then
  # The empty value stays in the environment, so the env file cannot refill
  # it, and the backend's own read treats empty as unset.
  export CRM_AGENT_RUNTIME=""
  echo "the live route: the real agent on 8080 works the cases"
else
  export CRM_AGENT_RUNTIME="$RUNTIME_ARN"
  echo "the emulator route: dispatches go to the emulator (canned answers)"
fi
export CRM_DEV_HOST=0.0.0.0
export CRM_CONTEXT_HOST=0.0.0.0
export HOST=0.0.0.0
# The backend reads its keys from this address, so the demo names the
# loopback one and leaves nothing to the fallback.
export AUTH_URL=http://127.0.0.1:8004
export AUTH_ALLOW_ORIGIN="http://$DEMO_HOST:5173"
export VITE_AUTH_URL="http://$DEMO_HOST:8004"

setsid nohup npm run dev >"$LOG_DIR/dev.log" 2>&1 &
echo $! >"$LOG_DIR/dev.pid"

echo "== wait for the services"
wait_for_url "the backend" "http://127.0.0.1:8000/api/health"

# The ping is served from process start, so this proves the servers answer
# early; the services open their pools and credentials on their first real
# operation, and a failure there shows in the run, not here.
wait_for_ping() {
  local name="$1" url="$2"
  local try
  for try in $(seq 1 120); do
    if curl -sf --max-time 5 "$url" 2>/dev/null | grep -q 'Healthy\|Busy'; then
      echo "up:   $name is ready"
      return 0
    fi
    sleep 1
  done
  echo "FAIL: $name never got ready at $url" >&2
  tail -5 "$LOG_DIR/dev.log" >&2 || true
  return 1
}
wait_for_ping "the agent" "http://127.0.0.1:8080/ping"
wait_for_ping "the copilot" "http://127.0.0.1:8081/ping"

wait_for_port "the context server" 8006
wait_for_url "the auth service" "http://127.0.0.1:8004/api/health"
wait_for_url "the dashboard" "http://127.0.0.1:5173"

echo "== check the external address on this host"
for port in 4566 5433 8000 8004 5173 8080 8081 8006; do
  if timeout 1 bash -c "</dev/tcp/$DEMO_HOST/$port" 2>/dev/null; then
    echo "open: $DEMO_HOST:$port"
  else
    echo "FAIL: $DEMO_HOST:$port refuses connections" >&2
    exit 1
  fi
done
cat <<URLS

The demo stack is up. Visit:

  Dashboard        http://$DEMO_HOST:5173        (sign in: rosa.meridian@northgate.example / crm-dev)
  Backend health   http://$DEMO_HOST:8000/api/health
  Auth service     http://$DEMO_HOST:8004/api/health
  Agent service    http://$DEMO_HOST:8080
  Copilot          http://$DEMO_HOST:8081
  Context server   http://$DEMO_HOST:8006/mcp
  Emulator health  http://$DEMO_HOST:4566/_floci/health

The demo database lives in the compose Postgres.
The laptop's crm.db keeps its data.
The demo script: crm/docs/demo_runbook.md
Tear down with:   crm/deploy/demo_down.sh
URLS
