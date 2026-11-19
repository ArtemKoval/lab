#!/usr/bin/env bash
# One command: install and run the whole crm solution locally, in the
# devcontainer, with the AWS targets on the floci emulator.
#
#   crm/local-up.sh [pack]     # pack defaults to library
#
# The script brings up the devcontainer, starts floci, seeds the pack,
# proves the runtime wiring from the host, starts the five services inside
# the container, and prints the addresses. It leaves the stack running;
# stop it with: docker rm -f crm-dev and docker rm -f crm-floci
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACK="${1:-library}"

# Docker access: direct when the shell has it, through the group when it
# does not (a session that predates its own group membership).
if docker info >/dev/null 2>&1; then
  dock() { docker "$@"; }
  dc() { npx --no-install @devcontainers/cli "$@"; }
  dexec() { npx --no-install @devcontainers/cli exec "$@"; }
else
  dock() { sg docker -c "docker $*"; }
  dc() { sg docker -c "npx --no-install @devcontainers/cli $*"; }
  dexec() { sg docker -c "npx --no-install @devcontainers/cli exec $*"; }
fi

echo "== the devcontainer =="
dc up --workspace-folder "$ROOT/crm" --mount-workspace-git-root=false

echo "== floci =="
if curl -sf http://localhost:4566/_floci/health >/dev/null; then
  echo "floci already answers on 4566"
else
  dock rm -f crm-floci >/dev/null 2>&1 || true
  dock run -d --name crm-floci -p 4566:4566 \
    -e FLOCI_HOSTNAME=localhost \
    -e 'FLOCI_SERVICES_BEDROCK_AGENT_CORE_INVOKE_RESPONSE={"accepted": true}' \
    floci/floci:latest
  until curl -sf http://localhost:4566/_floci/health >/dev/null; do sleep 1; done
fi
echo "floci answers on 4566"

echo "== the wiring gate, from the host =="
(
  cd "$ROOT/crm"
  uv sync --quiet --group runtime
  AWS_ENDPOINT_URL=http://localhost:4566 AWS_DEFAULT_REGION=us-east-1 \
  AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
  uv run --no-sync python deploy/verify_wiring.py
)

echo "== seed and validate $PACK =="
cat > "$ROOT/crm/.devcontainer/seed.sh" <<SEED
#!/usr/bin/env bash
cd /workspaces/crm || exit 1
uv sync --quiet
CRM_DOMAIN=$PACK uv run --no-sync python validate.py $PACK
CRM_DOMAIN=$PACK uv run --no-sync python -m backend.seed
SEED
dexec --workspace-folder "$ROOT/crm" -- bash /workspaces/crm/.devcontainer/seed.sh

echo "== start the services =="
cat > "$ROOT/crm/.devcontainer/serve.sh" <<SERVE
#!/usr/bin/env bash
cd /workspaces/crm || exit 1
pkill -f "vite dashboard" 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true
pkill -f spawn_main 2>/dev/null || true
pkill -f concurrently 2>/dev/null || true
pkill -f auth/server.mjs 2>/dev/null || true
pkill -9 -f "npm run dev" 2>/dev/null || true
pkill -9 -f "uv run --env-file" 2>/dev/null || true
pkill -9 -f "python -m context" 2>/dev/null || true
sleep 1
[ -f .env ] || cp .env.example .env 2>/dev/null || touch .env
BASE=\$(hostname -i | awk '{print \$1}')
CRM_DOMAIN=$PACK CRM_API="http:\$BASE:8000" \
  VITE_AUTH_URL="http:\$BASE:8004" AUTH_URL="http://localhost:8004" \
  AUTH_DEV_PASSWORD=crm-dev HOST=0.0.0.0 nohup npm run dev >/tmp/crm-dev.log 2>&1 &
SERVE
dexec --workspace-folder "$ROOT/crm" -- bash /workspaces/crm/.devcontainer/serve.sh

echo "== wait for the services, and find the container address =="
CID=$(dock ps -q -f label=devcontainer.local_folder="$ROOT/crm" | head -1)
BASE=$(dock inspect "$CID" | grep -m1 '"IPAddress"' | sed 's/.*: "\([^"]*\)".*/\1/')
for _ in $(seq 1 60); do
  curl -sf "http://$BASE:8000/api/health" >/dev/null 2>&1 && break
  sleep 2
done
curl -sf "http://$BASE:8000/api/health" >/dev/null && echo "backend healthy"
echo
echo "The $PACK desk is up in the devcontainer, with the AWS targets on floci:"
echo "  dashboard  http://$BASE:5173"
echo "  backend    http://$BASE:8000/api/health"
echo "  emulator   http://localhost:4566/_floci/health"
echo "Sign in with a worker email of the pack and the dev password crm-dev."
