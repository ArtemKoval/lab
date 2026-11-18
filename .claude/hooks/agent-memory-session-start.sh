#!/bin/bash
# SessionStart agent-memory slice hook (operator-ordered wiring, issue #75).
#
# Injects the cached agent-memory slice (tier 1 + tier 2) as SessionStart
# additionalContext when ~/.config/memory-kit.conf names a valid MEMORY_REPO.
# Pure local on the hot path: shell builtins, one guarded `date`, and a
# dual-form `stat` for the mtime — no gh, no network, so a broken PATH or an
# offline moment cannot slow or break session start.
#
# Silent exits (no output, exit 0): missing or unreadable conf, MEMORY_REPO
# absent or not owner/name shaped, missing cache, empty cache. CLAUDE.md's
# "Agent Memory" section drives the connect conversation when memory
# features are used; this hook never nags about setup.
#
# A cache older than 12 h adds one regeneration nudge line. Pending
# markers from the SessionEnd breadcrumb hook (agent-memory-session-end.sh)
# add one distillation duty block listing the newest three. The agent owns
# regeneration and distillation; this hook only reads, so it cannot race a
# concurrent rewrite into anything worse than a partial projection.
#
# Output envelope is the harness-charter shape: one top-level object,
# hookSpecificOutput.additionalContext. Always exits 0; fails open.

set -u

CONF="${HOME:-}/.config/memory-kit.conf"
[ -r "$CONF" ] || exit 0

REPO=""
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    MEMORY_REPO=*) REPO="${line#MEMORY_REPO=}" ;;
  esac
done < "$CONF"

# Accept exactly owner/name, one slash, both sides over the GitHub name
# charset. Anything else (empty, spaces, quotes, dollar, backtick, no slash,
# a second slash) stays silent.
case "$REPO" in
  */*) : ;;
  *) exit 0 ;;
esac
OWNER="${REPO%%/*}"
NAME="${REPO#*/}"
case "$OWNER" in
  ""|*[!A-Za-z0-9_.-]*) exit 0 ;;
esac
case "$NAME" in
  ""|*[!A-Za-z0-9_.-]*|*/*) exit 0 ;;
esac

CACHE="${HOME:-}/.config/memory-kit/cache/${REPO/\//-}/STATE.md"
[ -r "$CACHE" ] || exit 0

SLICE="$(<"$CACHE")"
[ -n "$SLICE" ] || exit 0

if [ "${#SLICE}" -gt 3500 ]; then
  SLICE="${SLICE:0:3500}
[truncated]"
fi

STALE=""
now=$(date +%s 2>/dev/null) || now=""
if [ -n "$now" ]; then
  case "$now" in
    *[!0-9]*) now="" ;;
  esac
fi
if [ -n "$now" ]; then
  mtime=$(stat -f %m "$CACHE" 2>/dev/null) || mtime=$(stat -c %Y "$CACHE" 2>/dev/null) || mtime=""
  case "$mtime" in
    ""|*[!0-9]*) : ;;
    *) age=$(( now - mtime ))
       if [ "$age" -gt 43200 ]; then
         STALE="

Cache is $(( age / 3600 )) h old. Regenerate it (agent-memory skill, Cache regeneration) before you bind a session."
       fi ;;
  esac
fi

LASTBOUND=""
BOUND_FILE="${CACHE%/*}/BOUND"
if [ -r "$BOUND_FILE" ]; then
  bt="$(<"$BOUND_FILE")"
  case "$bt" in
    ""|*[!0-9]*) : ;;
    *) LASTBOUND="

Last bound thread: #$bt (written at bind time; a hint, not a mandate)." ;;
  esac
fi

PENDING=""
PENDING_DIR="${CACHE%/*}/PENDING"
if [ -d "$PENDING_DIR" ]; then
  n=$(ls -1 "$PENDING_DIR" 2>/dev/null | wc -l | tr -d ' ')
  case "$n" in
    ""|*[!0-9]*) n=0 ;;
  esac
  if [ "$n" -gt 0 ]; then
    PENDING="

$n session(s) ended without a memory summary. Distill each pending transcript into its best-fit thread per the agent-memory skill (Mode 3), then delete that marker. Newest first:"
    for m in $(ls -t "$PENDING_DIR" 2>/dev/null | head -3); do
      PENDING="$PENDING
- $PENDING_DIR/$m"
    done
  fi
fi

CTX="Agent memory (auto-injected from $REPO; read-only slice, the agent-memory skill owns the formats):

$SLICE$STALE$LASTBOUND$PENDING"

esc="${CTX//\\/\\\\}"
esc="${esc//\"/\\\"}"
esc="${esc//$'\n'/\\n}"
esc="${esc//$'\r'/\\r}"
esc="${esc//$'\t'/\\t}"

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$esc"
exit 0
