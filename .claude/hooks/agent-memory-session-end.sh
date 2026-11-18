#!/bin/bash
# SessionEnd agent-memory breadcrumb hook (issue #82).
#
# When a session ends (exit, clear, logout, limit, other), and the machine
# has a valid agent-memory config, write ONE mechanical pending marker:
#
#   ~/.config/memory-kit/cache/<owner-name>/PENDING/<epoch>-<session>.txt
#
# carrying flat lines: ts, reason, session, transcript, cwd. The NEXT
# session's start hook lists the newest markers inside its injected slice,
# and that agent distills each transcript into its bound thread (agent-
# memory skill, Mode 3) and deletes the marker. A shell hook runs after the
# agent is gone and cannot write a quality summary, so quit-time is
# deliberately mechanical.
#
# Input: the harness stdin JSON payload; parsed jq-first with a grep
# fallback (the scripts/pre-compact-hook.sh pattern). A payload without a
# transcript_path writes nothing — a marker without a transcript cannot be
# distilled.
#
# Pure local; bounded state (newest 5 markers kept); silent on any missing
# or invalid input; always exits 0; fails open.

set -u

INPUT="$(cat 2>/dev/null)" || INPUT=""

TRANSCRIPT=""
CWD=""
REASON=""
SESSION=""
if command -v jq >/dev/null 2>&1; then
  TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null || echo "")
  CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || echo "")
  REASON=$(printf '%s' "$INPUT" | jq -r '.reason // ""' 2>/dev/null || echo "")
  SESSION=$(printf '%s' "$INPUT" | jq -r '.session_id // ""' 2>/dev/null || echo "")
fi
if [ -z "$TRANSCRIPT" ]; then
  TRANSCRIPT=$(printf '%s' "$INPUT" | grep -o '"transcript_path":"[^"]*"' | head -1 | cut -d'"' -f4 2>/dev/null || echo "")
fi
if [ -z "$CWD" ]; then
  CWD=$(printf '%s' "$INPUT" | grep -o '"cwd":"[^"]*"' | head -1 | cut -d'"' -f4 2>/dev/null || echo "")
fi
if [ -z "$REASON" ]; then
  REASON=$(printf '%s' "$INPUT" | grep -o '"reason":"[^"]*"' | head -1 | cut -d'"' -f4 2>/dev/null || echo "")
fi
if [ -z "$SESSION" ]; then
  SESSION=$(printf '%s' "$INPUT" | grep -o '"session_id":"[^"]*"' | head -1 | cut -d'"' -f4 2>/dev/null || echo "")
fi

[ -n "$TRANSCRIPT" ] || exit 0

CONF="${HOME:-}/.config/memory-kit.conf"
[ -r "$CONF" ] || exit 0

REPO=""
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    MEMORY_REPO=*) REPO="${line#MEMORY_REPO=}" ;;
  esac
done < "$CONF"

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

CACHE="${HOME:-}/.config/memory-kit/cache/${REPO/\//-}"
PENDING="$CACHE/PENDING"
mkdir -p "$PENDING" 2>/dev/null || exit 0

now=$(date +%s 2>/dev/null) || now=""
case "$now" in
  ""|*[!0-9]*) now="0" ;;
esac

sid=$(printf '%s' "$SESSION" | tr -c 'A-Za-z0-9_-' '-' | cut -c1-40)
[ -n "$sid" ] && [ "$sid" != "-" ] || sid="s"

reason=$(printf '%s' "$REASON" | tr -c 'A-Za-z0-9_-' '-' | cut -c1-20)
[ -n "$reason" ] && [ "$reason" != "-" ] || reason="unknown"

THREAD=""
BOUND_FILE="$CACHE/BOUND"
if [ -r "$BOUND_FILE" ]; then
  THREAD="$(<"$BOUND_FILE")"
  case "$THREAD" in
    *[!0-9]*) THREAD="" ;;
  esac
fi

MARKER="$PENDING/${now}-${sid}.txt"
{
  printf 'ts=%s\n' "$now"
  printf 'reason=%s\n' "$reason"
  printf 'session=%s\n' "$sid"
  printf 'transcript=%s\n' "$TRANSCRIPT"
  printf 'cwd=%s\n' "$CWD"
  [ -n "$THREAD" ] && printf 'thread=%s\n' "$THREAD"
  :
} > "$MARKER" 2>/dev/null || exit 0

ls -1t "$PENDING" 2>/dev/null | tail -n +6 | while IFS= read -r old; do
  [ -n "$old" ] || continue
  rm -f "$PENDING/$old" 2>/dev/null
done

exit 0
