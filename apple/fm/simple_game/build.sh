#!/usr/bin/env bash
# build.sh - the governing script of the Snake build.
#
# It drives the Apple Foundation Model at /usr/bin/fm through 13 steps.
# The model writes every implementation, every unit test and the browser layer.
# This script writes no game logic. It only assembles prompts, judges answers and runs gates.
#
# Usage:
#   ./build.sh              run every step and resume from the ledger
#   ./build.sh --clean      remove the generated files and start again
#   ./build.sh --from N     start again at the step N
#   ./build.sh --only N     run the step N alone
#   ./build.sh --refreeze   accept the current contracts as the frozen ones
#   ./build.sh --list       list the steps
#   ./build.sh --serve      serve the project root after a good build
#   ./build.sh --help       print this text
#
# This script uses bash 3.2 syntax only, because /bin/bash on macOS is bash 3.2.
# It holds no associative array and no case conversion operator.

set -Eeuo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_SELF="${BASH_SOURCE[0]}"
while [ -h "$SCRIPT_SELF" ]; do
    SCRIPT_LINK=$(readlink "$SCRIPT_SELF")
    case "$SCRIPT_LINK" in
        /*) SCRIPT_SELF="$SCRIPT_LINK" ;;
        *) SCRIPT_SELF="$(dirname "$SCRIPT_SELF")/$SCRIPT_LINK" ;;
    esac
done
ROOT=$(cd "$(dirname "$SCRIPT_SELF")" && pwd)

BUILD_DIR="$ROOT/.build"
STATE_DIR="$BUILD_DIR/state"
FEEDBACK_DIR="$BUILD_DIR/feedback"
FM_CACHE_DIR="$BUILD_DIR/cache"
FM_TRANSCRIPT_DIR="$BUILD_DIR/transcripts"
FM_RAW_DIR="$BUILD_DIR/raw"
FM_WORK_DIR="$BUILD_DIR/work"
LOGS_DIR="$BUILD_DIR/logs"
FM_LOCK_DIR="$BUILD_DIR/fm.lock"
BUILD_LOCK_DIR="$BUILD_DIR/build.lock"

# ---------------------------------------------------------------------------
# Knobs
# ---------------------------------------------------------------------------

FM_BIN="${FM_BIN:-/usr/bin/fm}"
FM_RETRIES="${FM_RETRIES:-3}"
FM_TIMEOUT="${FM_TIMEOUT:-240}"
FM_LOCK_WAIT="${FM_LOCK_WAIT:-1800}"
FM_MIN_BYTES="${FM_MIN_BYTES:-40}"
FM_PROMPT_BUDGET="${FM_PROMPT_BUDGET:-1500}"
REPAIR_BUDGET="${REPAIR_BUDGET:-1200}"
CONTRACT_BUDGET="${CONTRACT_BUDGET:-400}"
CONTRACT_HARD_MAX="${CONTRACT_HARD_MAX:-1200}"
MUTATION_THRESHOLD="${MUTATION_THRESHOLD:-80}"
COVERAGE_THRESHOLD="${COVERAGE_THRESHOLD:-90}"
BRANCH_THRESHOLD="${BRANCH_THRESHOLD:-80}"
FUNCS_THRESHOLD="${FUNCS_THRESHOLD:-90}"
# eslint.config.mjs reads COMPLEXITY_MAX from the environment, so the knob must
# reach the child process of npx eslint. Without the export it changes nothing.
COMPLEXITY_MAX="${COMPLEXITY_MAX:-5}"
export COMPLEXITY_MAX
ALLOW_FALLBACK="${ALLOW_FALLBACK:-0}"
STRENGTHEN_ROUNDS="${STRENGTHEN_ROUNDS:-3}"
STRENGTHEN_FILLS="${STRENGTHEN_FILLS:-20}"
TEST_LITERAL_GATE="${TEST_LITERAL_GATE:-1}"
SERVE_PORT="${SERVE_PORT:-8080}"

OPT_CLEAN=0
# The value -1 means "the flag --from is absent". The value 0 is a real step number,
# so it must clear the ledger like every other number.
OPT_FROM=-1
OPT_ONLY=-1
OPT_REFREEZE=0
OPT_SERVE=0
OPT_LIST=0
CURRENT_STEP_ID='start'
BUILD_LOCK_HELD=0
REPAIR_ATTEMPTS=0
FM_CALLS_SAVED=0
FM_CACHE_HITS_SAVED=0
REPAIR_ATTEMPTS_SAVED=0
FALLBACKS_USED=''

# ---------------------------------------------------------------------------
# The step table and the unit table
# ---------------------------------------------------------------------------

STEP_TABLE='00|preflight|Preflight the host, the model and the tool chain
01|scaffold|Write the static repo files and install the npm tool chain
02|contracts|Freeze the 13 contracts and measure every assembled prompt
03|impl|Generate one implementation for each core unit, in dependency order
04|tests|Generate the blind unit tests for each core unit
05|assemble|Assemble the core barrel
06|unit-gate|Run the unit gate and repair the implementation
07|complexity|Run the complexity gate and repair or decompose
08|coverage|Run the coverage gate
09|mutation|Run the mutation gate and strengthen the frozen suite
10|renderer|Generate the browser layer with five function scoped calls
11|playtest|Drive the assembled game under a fake DOM
12|package|Write the report, the docs and serve the game'

# Fields: index, function name, style, dependency list.
UNIT_TABLE='00|samePos|rules|
01|nextHead|rules|
02|turn|rules|
03|hitsWall|rules|
04|hitsSelf|rules|
05|growOrMove|rules|
06|freeCells|rules|
07|pickCell|rules|
08|placeFood|skeleton|freeCells pickCell
09|createState|rules|
10|isDead|skeleton|hitsWall hitsSelf samePos growOrMove
11|advance|skeleton|samePos growOrMove placeFood
12|step|skeleton|turn nextHead isDead advance'

UNIT_NAMES='samePos nextHead turn hitsWall hitsSelf growOrMove freeCells pickCell placeFood createState isDead advance step'

RENDER_UNITS='drawBoard|ctx, state, cell
keyToInput|key
startLoop|state, tick, render, ms
boot|doc, cols, rows, cell'

# ---------------------------------------------------------------------------
# Libraries
# ---------------------------------------------------------------------------

. "$ROOT/lib/log.sh"
. "$ROOT/lib/fm.sh"
. "$ROOT/lib/gates.sh"

# ---------------------------------------------------------------------------
# Traps
# ---------------------------------------------------------------------------

# on_err runs on every command that errexit would stop the build for.
# It must never call "set +e". A trap body runs in the current shell, so "set +e"
# would disarm errexit for the whole rest of the process. The build would then print
# "the build stopped", go on to the next command, mark the failed step as done and
# exit 0. The handler logs and exits with the code of the command that failed.
on_err() {
    oe_rc=$?
    [ "$oe_rc" -ne 0 ] || oe_rc=1
    log_err "the build stopped in the step '$CURRENT_STEP_ID' at the line $1."
    print_resume
    exit "$oe_rc"
}

# on_exit only cleans up. It runs on the normal end and on an exit of any kind.
on_exit() {
    set +e
    fm_unlock
    if [ "$BUILD_LOCK_HELD" = "1" ]; then
        # Remove the lock only when this process still owns it. A --clean run or a
        # stale lock sweep of another build can hand the directory to somebody else.
        if [ "$(cat "$BUILD_LOCK_DIR/pid" 2>/dev/null || printf '')" = "$$" ]; then
            rm -rf "$BUILD_LOCK_DIR"
        fi
        BUILD_LOCK_HELD=0
    fi
}

# on_signal answers ctrl-c and SIGTERM. A trapped signal does not stop a bash script.
# The handler must exit by itself, or the build goes on with no lock, marks every
# later step as done and exits 0 while the user believes the build stopped.
on_signal() {
    os_sig="$1"
    log_err "the build stopped on the signal $os_sig in the step '$CURRENT_STEP_ID'."
    print_resume
    on_exit
    trap - "$os_sig" EXIT
    kill -s "$os_sig" $$
}

trap 'on_err $LINENO' ERR
trap on_exit EXIT
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM

print_resume() {
    pr_n=$(step_number_of_id "$CURRENT_STEP_ID" 2>/dev/null || printf '')
    if [ -n "$pr_n" ]; then
        printf '\n%sTo start again at this step run:%s\n' "${C_BOLD:-}" "${C_RESET:-}"
        printf '    %s --from %s\n' "$ROOT/build.sh" "$pr_n"
    else
        printf '\n%sThe build stopped before the first step.%s\n' "${C_BOLD:-}" "${C_RESET:-}"
        printf '    %s          to resume\n' "$ROOT/build.sh"
        printf '    %s --clean  to start again from nothing\n' "$ROOT/build.sh"
    fi
    printf '%sThe log is at %s%s\n\n' "${C_DIM:-}" "$BUILD_DIR/build.log" "${C_RESET:-}"
}

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

usage() {
    sed -n '2,19p' "$SCRIPT_SELF" | sed 's/^# \{0,1\}//'
}

# step_number_of_id prints the number of a step id. It prints nothing and returns 1
# when the id is unknown, so a caller never prints a step number that it invented.
step_number_of_id() {
    while IFS='|' read -r sn si st; do
        [ -n "$sn" ] || continue
        if [ "$si" = "$1" ]; then
            printf '%s\n' "$((10#$sn))"
            return 0
        fi
    done <<<"$STEP_TABLE"
    return 1
}

list_steps() {
    printf 'The build holds these steps:\n\n'
    while IFS='|' read -r sn si st; do
        [ -n "$sn" ] || continue
        if [ -f "$STATE_DIR/$sn.done" ]; then
            printf '  %s  %-12s %s   [done]\n' "$sn" "$si" "$st"
        else
            printf '  %s  %-12s %s\n' "$sn" "$si" "$st"
        fi
    done <<<"$STEP_TABLE"
    printf '\n13 steps.\n'
}

need_file() {
    [ -f "$1" ] || die "the file $1 is absent. $2"
}

need_dir() {
    [ -d "$1" ] || die "the directory $1 is absent. $2"
}

ledger_done() {
    [ -f "$STATE_DIR/$1.done" ]
}

ledger_mark() {
    date '+%Y-%m-%dT%H:%M:%S' >"$STATE_DIR/$1.done"
}

# contract_stamp prints the checksum of the contract of one unit.
# The per unit ledger holds this value, so an edited contract forces a new answer
# even on a plain resume that never touches the step ledger.
contract_stamp() {
    shasum -a 256 "$(contract_path "$1")" | awk '{ print $1 }'
}

# ledger_stamp_ok returns 0 when the per unit ledger file holds the current stamp.
ledger_stamp_ok() {
    [ "$(cat "$STATE_DIR/$1.done" 2>/dev/null || printf '')" = "$2" ]
}

# clear_step_state removes the sub ledger of one step. The step ledger alone does not
# describe a step that keeps one file for each unit, so --from N and --only N must
# clear both. The model cache keeps the cost of a full re-issue near zero.
clear_step_state() {
    case "$1" in
        03) rm -f "$STATE_DIR"/impl.*.done ;;
        04) rm -f "$STATE_DIR"/test.*.done "$STATE_DIR/tests.sha256" ;;
    esac
}

# unit_field prints one field of a unit row.
# Argument 1 is the function name. Argument 2 is 1 for the index, 3 for the style, 4 for the deps.
unit_field() {
    while IFS='|' read -r un uf us ud; do
        [ -n "$un" ] || continue
        if [ "$uf" = "$1" ]; then
            case "$2" in
                1) printf '%s\n' "$un" ;;
                3) printf '%s\n' "$us" ;;
                4) printf '%s\n' "$ud" ;;
            esac
            return 0
        fi
    done <<<"$UNIT_TABLE"
    return 1
}

contract_path() {
    printf '%s/contracts/%s-%s.md\n' "$ROOT" "$(unit_field "$1" 1)" "$1"
}

# contract_section prints the body of one section of a contract file.
contract_section() {
    awk -v want="$2" '
        BEGIN { insec = 0 }
        {
            line = $0
            ishdr = 0
            if (line ~ /^#+[ \t]*[A-Z][A-Z_ ]*[ \t]*:?[ \t]*$/) { ishdr = 1 }
            else if (line ~ /^[A-Z][A-Z_]+[ \t]*:?[ \t]*$/) { ishdr = 1 }
            if (ishdr == 1) {
                hdr = line
                sub(/^#+[ \t]*/, "", hdr)
                sub(/[ \t]*:?[ \t]*$/, "", hdr)
                sub(/[ \t]+$/, "", hdr)
                if (hdr == want) { insec = 1 } else { insec = 0 }
                next
            }
            if (insec == 1) { print line }
        }
    ' "$1"
}

# contract_inline prints the value of a one line section such as "STYLE: rules".
contract_inline() {
    ci_body=$(contract_section "$1" "$2" | sed '/^[[:space:]]*$/d' | head -1)
    if [ -n "$ci_body" ]; then
        printf '%s\n' "$ci_body"
        return 0
    fi
    grep -i "^#* *$2:" "$1" 2>/dev/null | head -1 | sed "s/^#* *$2: *//I" || true
}

# render_template splices the files of a value directory into a template.
# Argument 1 is the template. Argument 2 is the directory that holds KEY.txt files.
render_template() {
    awk -v dir="$2" '
        function splice(key,   f, l, v, first) {
            f = dir "/" key ".txt"
            v = ""; first = 1
            while ((getline l < f) > 0) {
                if (first == 1) { v = l; first = 0 } else { v = v "\n" l }
            }
            close(f)
            return v
        }
        {
            line = $0
            out = ""
            while (match(line, /\{\{[A-Z_0-9]+\}\}/)) {
                key = substr(line, RSTART + 2, RLENGTH - 4)
                out = out substr(line, 1, RSTART - 1) splice(key)
                line = substr(line, RSTART + RLENGTH)
            }
            print out line
        }
    ' "$1"
}

# val_set writes one template value.
val_set() {
    mkdir -p "$VALDIR"
    cat >"$VALDIR/$1.txt"
}

val_new() {
    VALDIR="$FM_WORK_DIR/vals.$1"
    rm -rf "$VALDIR"
    mkdir -p "$VALDIR"
}

count_cases() {
    contract_section "$(contract_path "$1")" 'CASES' | grep -c '^[[:space:]]*[0-9][0-9]*\.' || true
}

build_lock() {
    bl_waited=0
    while ! mkdir "$BUILD_LOCK_DIR" 2>/dev/null; do
        bl_owner=$(cat "$BUILD_LOCK_DIR/pid" 2>/dev/null || printf '')
        if [ -n "$bl_owner" ] && ! kill -0 "$bl_owner" 2>/dev/null; then
            log_warn "the build lock of process $bl_owner is stale. The build removes it."
            rm -rf "$BUILD_LOCK_DIR"
            continue
        fi
        sleep 2
        bl_waited=$((bl_waited + 2))
        if [ "$bl_waited" -ge 60 ]; then
            die "another build.sh runs now. Two builds must never share the model. Wait, or remove $BUILD_LOCK_DIR."
        fi
    done
    printf '%s\n' "$$" >"$BUILD_LOCK_DIR/pid"
    BUILD_LOCK_HELD=1
}

# counters_add adds a delta to one persistent counter and prints the new total.
counters_add() {
    ca_file="$STATE_DIR/counter.$1"
    ca_prev=$(cat "$ca_file" 2>/dev/null || printf '0')
    case "$ca_prev" in
        '' | *[!0-9]*) ca_prev=0 ;;
    esac
    ca_new=$((ca_prev + $2))
    printf '%s\n' "$ca_new" >"$ca_file"
    printf '%s\n' "$ca_new"
}

counters_get() {
    cg_v=$(cat "$STATE_DIR/counter.$1" 2>/dev/null || printf '0')
    case "$cg_v" in
        '' | *[!0-9]*) cg_v=0 ;;
    esac
    printf '%s\n' "$cg_v"
}

# counters_persist stores what this process added since the last call.
counters_persist() {
    counters_add calls $((FM_CALLS - FM_CALLS_SAVED)) >/dev/null
    counters_add hits $((FM_CACHE_HITS - FM_CACHE_HITS_SAVED)) >/dev/null
    counters_add repairs $((REPAIR_ATTEMPTS - REPAIR_ATTEMPTS_SAVED)) >/dev/null
    FM_CALLS_SAVED="$FM_CALLS"
    FM_CACHE_HITS_SAVED="$FM_CACHE_HITS"
    REPAIR_ATTEMPTS_SAVED="$REPAIR_ATTEMPTS"
}

frozen_tests_verify() {
    if [ ! -f "$STATE_DIR/tests.sha256" ]; then
        return 0
    fi
    if ( cd "$ROOT" && shasum -a 256 -c "$STATE_DIR/tests.sha256" ) >"$LOGS_DIR/frozen.out" 2>&1; then
        return 0
    fi
    log_err "a frozen test file changed. The build stops now."
    cat "$LOGS_DIR/frozen.out" >&2
    return 1
}

# ---------------------------------------------------------------------------
# Validators. fm_generate calls these on a candidate answer.
# ---------------------------------------------------------------------------

IMPL_FN=''
TEST_FN=''
RENDER_FN=''

deps_header() {
    dh_deps=$(unit_field "$1" 4)
    for dh_d in $dh_deps; do
        printf "import { %s } from './%s.js';\n" "$dh_d" "$dh_d"
    done
}

validate_impl() {
    vi_cand="$1"
    if ! grep -q "function $IMPL_FN(" "$vi_cand"; then
        log_warn "the answer holds no text 'function $IMPL_FN('."
        return 1
    fi
    vi_body="$FM_WORK_DIR/$IMPL_FN.body.js"
    if ! fm_normalise "$vi_cand" "$IMPL_FN" "$vi_body"; then
        log_warn "the answer of $IMPL_FN cannot be cut down to one function."
        return 1
    fi
    case "$(head -1 "$vi_body")" in
        "export function $IMPL_FN("*) : ;;
        *)
            log_warn "the first line of $IMPL_FN is '$(head -1 "$vi_body")'. It must start with export function $IMPL_FN(."
            return 1
            ;;
    esac
    if grep -q '`' "$vi_body"; then
        log_warn "the normalised file of $IMPL_FN holds a backtick."
        return 1
    fi
    mkdir -p "$ROOT/src"
    # A repair attempt overwrites a file that already runs. When the new answer does not
    # parse, the old file must come back. Without this the build leaves no source at all
    # and every later attempt reads an absent file.
    vi_keep="$FM_WORK_DIR/$IMPL_FN.previous.js"
    rm -f "$vi_keep"
    if [ -f "$ROOT/src/$IMPL_FN.js" ]; then
        cp "$ROOT/src/$IMPL_FN.js" "$vi_keep"
    fi
    {
        deps_header "$IMPL_FN"
        cat "$vi_body"
    } >"$ROOT/src/$IMPL_FN.js"
    if ! node --check "$ROOT/src/$IMPL_FN.js" >"$LOGS_DIR/check.$IMPL_FN.out" 2>&1; then
        log_warn "node --check refuses src/$IMPL_FN.js. See $LOGS_DIR/check.$IMPL_FN.out"
        impl_restore "$vi_keep"
        return 1
    fi
    if ! ( cd "$ROOT" && node -e "import('./src/$IMPL_FN.js').then(m => { if (typeof m.$IMPL_FN !== 'function') { process.exit(3); } }).catch(() => process.exit(4));" ) >>"$LOGS_DIR/check.$IMPL_FN.out" 2>&1; then
        log_warn "the module src/$IMPL_FN.js does not export a function named $IMPL_FN."
        impl_restore "$vi_keep"
        return 1
    fi
    return 0
}

# impl_restore puts the file of the last good answer back, or removes a first bad answer.
impl_restore() {
    if [ -f "$1" ]; then
        cp "$1" "$ROOT/src/$IMPL_FN.js"
        log_warn "the build put the last good src/$IMPL_FN.js back."
    else
        rm -f "$ROOT/src/$IMPL_FN.js"
    fi
}

validate_test() {
    vt_cand="$1"
    vt_first=$(head -1 "$vt_cand")
    if [ "$vt_first" != "import { test } from 'node:test';" ]; then
        log_warn "the first line of the test of $TEST_FN is '$vt_first'."
        return 1
    fi
    if grep -q 'require(' "$vt_cand"; then
        log_warn "the test of $TEST_FN uses require."
        return 1
    fi
    mkdir -p "$ROOT/test"
    cp "$vt_cand" "$ROOT/test/$TEST_FN.test.mjs"
    if ! node --check "$ROOT/test/$TEST_FN.test.mjs" >"$LOGS_DIR/check.test.$TEST_FN.out" 2>&1; then
        log_warn "node --check refuses test/$TEST_FN.test.mjs."
        rm -f "$ROOT/test/$TEST_FN.test.mjs"
        return 1
    fi
    vt_want=$(count_cases "$TEST_FN")
    vt_have=$(grep -c "^test(" "$ROOT/test/$TEST_FN.test.mjs" || true)
    if [ "$vt_want" -gt 0 ] && [ "$vt_have" -ne "$vt_want" ]; then
        log_warn "the test of $TEST_FN holds $vt_have test blocks. The contract holds $vt_want cases."
        rm -f "$ROOT/test/$TEST_FN.test.mjs"
        return 1
    fi
    # The test name of a case can hold a word such as "turn applied". A quoted string
    # is never a call, so the gate reads the file with every quoted string removed.
    vt_code="$FM_WORK_DIR/$TEST_FN.code.txt"
    sed -e "s/'[^']*'//g" -e 's/"[^"]*"//g' "$ROOT/test/$TEST_FN.test.mjs" >"$vt_code"
    for vt_other in $UNIT_NAMES; do
        [ "$vt_other" = "$TEST_FN" ] && continue
        if grep -q "[^A-Za-z0-9_]${vt_other}[( ]" "$vt_code"; then
            log_warn "the test of $TEST_FN names the other core function $vt_other."
            rm -f "$ROOT/test/$TEST_FN.test.mjs"
            return 1
        fi
    done
    if ! deep_gate "$TEST_FN"; then
        rm -f "$ROOT/test/$TEST_FN.test.mjs"
        return 1
    fi
    if [ "$TEST_LITERAL_GATE" = "1" ]; then
        if ! literal_gate "$TEST_FN"; then
            rm -f "$ROOT/test/$TEST_FN.test.mjs"
            return 1
        fi
    fi
    return 0
}

# deep_gate proves that a test file compares an object or an array with assert.deepEqual.
# assert.equal of node:assert/strict is strictEqual, so it compares two arrays by identity
# and it always fails. The model writes assert.equal for an array now and then, and the
# unit gate then blames a correct implementation. This gate stops that answer at the source.
deep_gate() {
    dg_want=$(contract_section "$(contract_path "$1")" 'CASES' |
        grep '^[[:space:]]*[0-9][0-9]*\.' |
        sed 's/.*=== *//' |
        grep -c '^[[{]' || true)
    [ -n "$dg_want" ] || dg_want=0
    dg_have=$(grep -c 'deepEqual' "$ROOT/test/$1.test.mjs" || true)
    [ -n "$dg_have" ] || dg_have=0
    if [ "$dg_want" -gt 0 ] && [ "$dg_have" -lt "$dg_want" ]; then
        log_warn "the test of $1 holds $dg_have deepEqual calls. The contract needs $dg_want."
        log_warn "assert.equal of node:assert/strict never matches two arrays or two objects."
        return 1
    fi
    return 0
}

# literal_gate proves that every string literal of a test file is in the contract cases.
literal_gate() {
    lg_cases="$FM_WORK_DIR/$1.cases.txt"
    contract_section "$(contract_path "$1")" 'CASES' >"$lg_cases"
    lg_bad=''
    lg_lits=$(grep "assert" "$ROOT/test/$1.test.mjs" | grep -o "'[A-Za-z][A-Za-z0-9_]*'" | sort -u || true)
    for lg_l in $lg_lits; do
        lg_plain=$(printf '%s\n' "$lg_l" | tr -d "'")
        if ! grep -q "$lg_plain" "$lg_cases"; then
            lg_bad="$lg_bad $lg_plain"
        fi
    done
    if [ -n "$lg_bad" ]; then
        log_warn "the test of $1 invents the literals$lg_bad. They are absent from the contract cases."
        log_warn "set TEST_LITERAL_GATE=0 when the contract states a literal in another form."
        return 1
    fi
    return 0
}

validate_render() {
    vr_cand="$1"
    if ! grep -q "function $RENDER_FN(" "$vr_cand"; then
        log_warn "the answer holds no text 'function $RENDER_FN('."
        return 1
    fi
    vr_tmp="$FM_WORK_DIR/render.$RENDER_FN.js"
    printf 'const __probe = 1;\n' >"$vr_tmp"
    cat "$vr_cand" >>"$vr_tmp"
    if ! node --check "$vr_tmp" >>"$LOGS_DIR/check.render.out" 2>&1; then
        log_warn "node --check refuses the function $RENDER_FN."
        return 1
    fi
    return 0
}

validate_html() {
    vh_cand="$1"
    grep -q '<canvas id="game"' "$vh_cand" || { log_warn "the page holds no canvas with the id game."; return 1; }
    grep -q '<script type="module" src="game.js">' "$vh_cand" || { log_warn "the page holds no module script tag."; return 1; }
    grep -qi '<!DOCTYPE html>' "$vh_cand" || { log_warn "the page holds no doctype."; return 1; }
    html_border_ok "$vh_cand" || { log_warn "the page holds no canvas rule with a border."; return 1; }
    return 0
}

# html_border_ok proves that the CSS gives the canvas a border of its own.
# The board fill and the page background are both near black, so a border on the body
# leaves the player with no visible playfield edge. The walls kill the snake, so the
# player must see them. The selector is canvas, or #game, or both.
html_border_ok() {
    tr -d '\n' <"$1" | grep -qE '(canvas|#game)[^{}]*\{[^{}]*border[^{}]*solid'
}

# ---------------------------------------------------------------------------
# Step 0. Preflight
# ---------------------------------------------------------------------------

step_preflight() {
    mkdir -p "$STATE_DIR" "$FEEDBACK_DIR" "$FM_CACHE_DIR" "$FM_TRANSCRIPT_DIR" \
        "$FM_RAW_DIR" "$FM_WORK_DIR" "$LOGS_DIR"
    : >"$LOGS_DIR/tokens.txt"

    {
        printf 'FM_BIN=%s\n' "$FM_BIN"
        printf 'FM_RETRIES=%s\n' "$FM_RETRIES"
        printf 'FM_TIMEOUT=%s\n' "$FM_TIMEOUT"
        printf 'FM_PROMPT_BUDGET=%s\n' "$FM_PROMPT_BUDGET"
        printf 'REPAIR_BUDGET=%s\n' "$REPAIR_BUDGET"
        printf 'CONTRACT_BUDGET=%s\n' "$CONTRACT_BUDGET"
        printf 'CONTRACT_HARD_MAX=%s\n' "$CONTRACT_HARD_MAX"
        printf 'MUTATION_THRESHOLD=%s\n' "$MUTATION_THRESHOLD"
        printf 'COVERAGE_THRESHOLD=%s\n' "$COVERAGE_THRESHOLD"
        printf 'BRANCH_THRESHOLD=%s\n' "$BRANCH_THRESHOLD"
        printf 'FUNCS_THRESHOLD=%s\n' "$FUNCS_THRESHOLD"
        printf 'STRENGTHEN_ROUNDS=%s\n' "$STRENGTHEN_ROUNDS"
        printf 'STRENGTHEN_FILLS=%s\n' "$STRENGTHEN_FILLS"
        printf 'COMPLEXITY_MAX=%s\n' "$COMPLEXITY_MAX"
        printf 'ALLOW_FALLBACK=%s\n' "$ALLOW_FALLBACK"
        printf 'TEST_LITERAL_GATE=%s\n' "$TEST_LITERAL_GATE"
    } >"$BUILD_DIR/env.txt"
    log_info "the knobs are at $BUILD_DIR/env.txt"

    fm_resolve_timeout
    if [ -n "$TIMEOUT_BIN" ]; then
        log_ok "the timeout program is $TIMEOUT_BIN."
    else
        log_warn "no timeout program exists. The build uses a watchdog of its own."
    fi

    fm_preflight

    node_v=$(node --version 2>/dev/null || printf 'none')
    case "$node_v" in
        v24.*) log_ok "node is $node_v." ;;
        v2[5-9].* | v[3-9][0-9].*) log_warn "node is $node_v. The build measured node v24." ;;
        *) die "node is '$node_v'. The build needs node v24." ;;
    esac
    npm --version >/dev/null 2>&1 || die "npm does not run."
    python3 --version >/dev/null 2>&1 || die "python3 does not run. The flag --serve needs it."
    printf 'write test\n' >"$BUILD_DIR/.writetest" || die "the directory $BUILD_DIR is not writable."
    rm -f "$BUILD_DIR/.writetest"
    log_ok "npm, python3 and the .build tree are ready."
}

# ---------------------------------------------------------------------------
# Step 1. Scaffold
# ---------------------------------------------------------------------------

write_if_absent() {
    wa_path="$1"
    if [ -f "$wa_path" ]; then
        log_info "the file $(basename "$wa_path") exists. The build keeps it."
        cat >/dev/null
        return 0
    fi
    mkdir -p "$(dirname "$wa_path")"
    cat >"$wa_path"
    log_ok "the build wrote $(basename "$wa_path")."
}

step_scaffold() {
    write_if_absent "$ROOT/package.json" <<'PKG'
{
  "name": "fm-snake",
  "private": true,
  "type": "module",
  "version": "1.0.0",
  "description": "A Snake game that the Apple Foundation Model writes, one function at a time.",
  "scripts": {
    "test": "node --test \"test/**/*.test.mjs\"",
    "coverage": "node --test --experimental-test-coverage \"test/**/*.test.mjs\"",
    "lint": "eslint src",
    "lint:web": "eslint -c eslint.web.mjs web/game.js",
    "mutation": "stryker run",
    "serve": "python3 -m http.server 8080"
  },
  "devDependencies": {
    "@stryker-mutator/core": "^10.0.0",
    "eslint": "^10.11.0"
  }
}
PKG

    write_if_absent "$ROOT/eslint.config.mjs" <<'ESL'
// The build exports COMPLEXITY_MAX, so the documented knob reaches this file.
const MAX = Number(process.env.COMPLEXITY_MAX || 5);
export default [
  {
    ignores: ["node_modules/**", ".build/**", ".stryker-tmp/**", "reports/**", "web/**"]
  },
  {
    files: ["src/**/*.js"],
    languageOptions: { ecmaVersion: 2023, sourceType: "module" },
    rules: {
      complexity: ["error", { max: MAX }],
      "max-depth": ["error", 2],
      "max-lines-per-function": ["error", { max: 25, skipBlankLines: true, skipComments: true }],
      "max-params": ["error", 4],
      "no-undef": "error",
      "no-unused-vars": "error"
    }
  }
];
ESL

    write_if_absent "$ROOT/eslint.web.mjs" <<'ESW'
export default [
  {
    files: ["web/*.js"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      globals: {
        document: "readonly",
        window: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        requestAnimationFrame: "readonly",
        Math: "readonly"
      }
    },
    rules: {
      complexity: ["error", { max: 10 }],
      "max-depth": ["error", 2],
      "max-params": ["error", 4],
      "no-undef": "error",
      "no-unused-vars": "error"
    }
  }
];
ESW

    write_if_absent "$ROOT/stryker.config.json" <<'STR'
{
  "$schema": "./node_modules/@stryker-mutator/core/schema/stryker-schema.json",
  "packageManager": "npm",
  "reporters": ["clear-text", "progress"],
  "testRunner": "command",
  "commandRunner": { "command": "node --test \"test/**/*.test.mjs\"" },
  "coverageAnalysis": "off",
  "mutate": ["src/**/*.js", "!src/core.js"],
  "thresholds": { "break": 80 },
  "tempDirName": ".stryker-tmp"
}
STR

    write_if_absent "$ROOT/.gitignore" <<'GIT'
node_modules/
.build/
.stryker-tmp/
reports/
GIT

    if grep -q 'node --test test/' "$ROOT/package.json"; then
        die "package.json holds the broken script 'node --test test/'. Node 24 reads test/ as a module. Use the quoted glob."
    fi
    log_ok "package.json holds no broken 'node --test test/' script."

    log_cmd "npm install"
    ( cd "$ROOT" && npm install ) >"$LOGS_DIR/npm-install.out" 2>&1 ||
        die "npm install failed. See $LOGS_DIR/npm-install.out"
    log_ok "npm install exits 0."

    # The smoke unit proves every gate runs before the model spends any time.
    mkdir -p "$ROOT/src" "$ROOT/test"
    printf 'export function _smoke(n) {\n  return n + 1;\n}\n' >"$ROOT/src/_smoke.js"
    cat >"$ROOT/test/_smoke.test.mjs" <<'SMK'
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { _smoke } from '../src/_smoke.js';
test('the smoke unit adds one', () => {
  assert.equal(_smoke(1), 2);
});
SMK
    ( cd "$ROOT" && node --test "test/**/*.test.mjs" ) >"$LOGS_DIR/smoke-unit.out" 2>&1 ||
        die "the smoke unit test fails. See $LOGS_DIR/smoke-unit.out"
    log_ok "node --test passes on the smoke unit."
    ( cd "$ROOT" && npx eslint src ) >"$LOGS_DIR/smoke-lint.out" 2>&1 ||
        die "eslint fails on the smoke unit. See $LOGS_DIR/smoke-lint.out"
    log_ok "npx eslint src exits 0 on the smoke unit."
    ( cd "$ROOT" && npx stryker --version ) >"$LOGS_DIR/smoke-stryker.out" 2>&1 ||
        die "npx stryker --version fails. See $LOGS_DIR/smoke-stryker.out"
    log_ok "npx stryker --version exits 0 ($(cat "$LOGS_DIR/smoke-stryker.out" | tail -1))."
    rm -f "$ROOT/src/_smoke.js" "$ROOT/test/_smoke.test.mjs"
    log_ok "the smoke unit is removed. The tool chain is ready."
}

# ---------------------------------------------------------------------------
# Step 2. Contracts
# ---------------------------------------------------------------------------

assemble_impl_prompt() {
    ap_fn="$1"
    ap_out="$2"
    ap_c=$(contract_path "$ap_fn")
    ap_style=$(contract_inline "$ap_c" 'STYLE')
    val_new "impl.$ap_fn"
    case "$ap_style" in
        *skeleton*)
            contract_section "$ap_c" 'DEPS' | val_set DEPS
            contract_section "$ap_c" 'SKELETON' | val_set SKELETON
            contract_section "$ap_c" 'HOLES' | val_set HOLES
            if [ ! -s "$VALDIR/SKELETON.txt" ]; then
                die "the contract $ap_c uses the style skeleton but it holds no SKELETON section."
            fi
            render_template "$ROOT/prompts/skeleton.user.md" "$VALDIR" >"$ap_out"
            printf '%s\n' "$ROOT/prompts/skeleton.md"
            ;;
        *)
            contract_section "$ap_c" 'SIGNATURE' | sed 's/^export function //' | val_set SIGNATURE
            contract_section "$ap_c" 'DESCRIPTION' | val_set DESCRIPTION
            contract_section "$ap_c" 'EXAMPLES' | val_set EXAMPLES
            render_template "$ROOT/prompts/impl.user.md" "$VALDIR" >"$ap_out"
            printf '%s\n' "$ROOT/prompts/impl.md"
            ;;
    esac
}

assemble_test_prompt() {
    tp_fn="$1"
    tp_out="$2"
    tp_c=$(contract_path "$tp_fn")
    val_new "test.$tp_fn"
    printf '%s\n' "$tp_fn" | val_set FILE
    contract_section "$tp_c" 'SIGNATURE' | sed 's/^export function //' | val_set SIGNATURE
    contract_section "$tp_c" 'TYPES' | val_set TYPES
    contract_section "$tp_c" 'BEHAVIOUR' | val_set BEHAVIOUR
    contract_section "$tp_c" 'CASES' | val_set CASES
    render_template "$ROOT/prompts/test.user.md" "$VALDIR" >"$tp_out"
}

# measure_prompt counts the tokens of one assembled prompt and holds it to the ceiling.
# Argument 1 is the kind. Argument 2 is the unit. Argument 3 is the system prompt.
# Argument 4 is the user prompt.
measure_prompt() {
    mp_kind="$1"
    mp_fn="$2"
    cat "$3" "$4" >"$FM_WORK_DIR/measure.tmp"
    mp_n=$(fm_count_tokens "$FM_WORK_DIR/measure.tmp" || printf '')
    [ -n "$mp_n" ] || return 0
    printf '%s %s:%s\n' "$mp_n" "$mp_kind" "$mp_fn" >>"$LOGS_DIR/tokens.txt"
    if [ "$mp_n" -gt "$REPAIR_BUDGET" ]; then
        die "the $mp_kind prompt of $mp_fn holds $mp_n tokens. The ceiling is $REPAIR_BUDGET."
    fi
}

step_contracts() {
    need_dir "$ROOT/contracts" "The contract author writes contracts/NN-<unit>.md."
    need_dir "$ROOT/prompts" "The prompt author writes prompts/*.md."
    for sc_p in impl.md impl.user.md skeleton.md skeleton.user.md test.md test.user.md \
        repair.md repair.user.md strengthen.md strengthen.user.md render.md render.user.md \
        html.md html.user.md; do
        need_file "$ROOT/prompts/$sc_p" "The prompt author writes it."
    done

    sc_count=0
    : >"$LOGS_DIR/tokens.txt"
    for sc_fn in $UNIT_NAMES; do
        sc_c=$(contract_path "$sc_fn")
        need_file "$sc_c" "The contract of the unit $sc_fn is missing."
        sc_count=$((sc_count + 1))

        sc_style=$(contract_inline "$sc_c" 'STYLE')
        case "$sc_style" in
            *rules* | *skeleton*) : ;;
            *) die "the contract $sc_c holds the style '$sc_style'. It must be rules or skeleton." ;;
        esac

        for sc_sec in SIGNATURE DESCRIPTION EXAMPLES TYPES BEHAVIOUR CASES DOMAIN; do
            if [ -z "$(contract_section "$sc_c" "$sc_sec" | tr -d '[:space:]')" ]; then
                die "the contract $sc_c holds no section $sc_sec."
            fi
        done

        # The whole contract file never enters one prompt. build.sh sends only the
        # sections that a step needs. Measured cost of a full 11 section contract is
        # 560 to 670 tokens, so a hard limit of 400 on the file is not reachable.
        # The real defence is the assembled prompt gate below, at REPAIR_BUDGET tokens.
        sc_tok=$(fm_count_tokens "$sc_c" || printf '')
        if [ -n "$sc_tok" ]; then
            printf '%s contract:%s\n' "$sc_tok" "$sc_fn" >>"$LOGS_DIR/tokens.txt"
            if [ "$sc_tok" -gt "$CONTRACT_HARD_MAX" ]; then
                die "the contract $sc_c holds $sc_tok tokens. The hard limit is $CONTRACT_HARD_MAX."
            fi
            if [ "$sc_tok" -gt "$CONTRACT_BUDGET" ]; then
                log_warn "the contract $sc_c holds $sc_tok tokens. The design target is $CONTRACT_BUDGET."
            fi
        fi

        sc_ip="$FM_WORK_DIR/prompt.impl.$sc_fn"
        sc_sys=$(assemble_impl_prompt "$sc_fn" "$sc_ip")
        sc_tp="$FM_WORK_DIR/prompt.test.$sc_fn"
        assemble_test_prompt "$sc_fn" "$sc_tp"

        measure_prompt "impl" "$sc_fn" "$sc_sys" "$sc_ip"
        measure_prompt "test" "$sc_fn" "$ROOT/prompts/test.md" "$sc_tp"
        log_ok "the contract of $sc_fn is good. The prompts fit the window."
    done

    [ "$sc_count" -eq 13 ] || die "the build found $sc_count contracts. It needs 13."

    # The freeze must compare the live contracts against the STORED sums. A check of
    # the live files against sums that this step just wrote can never fail, and an
    # edited contract would pass without a word.
    ( cd "$ROOT/contracts" && shasum -a 256 ./*.md ) >"$STATE_DIR/contracts.now"
    if [ ! -f "$ROOT/contracts/SHA256SUMS" ] || [ "$OPT_REFREEZE" -eq 1 ]; then
        cp "$STATE_DIR/contracts.now" "$ROOT/contracts/SHA256SUMS"
        rm -f "$STATE_DIR"/impl.*.done "$STATE_DIR"/test.*.done
        log_warn "the build froze the current contracts and cleared the per unit ledger."
    fi
    if ! ( cd "$ROOT/contracts" && shasum -a 256 -c SHA256SUMS ) >"$LOGS_DIR/contracts-check.out" 2>&1; then
        log_err "a frozen contract changed since the freeze:"
        grep -v ': OK$' "$LOGS_DIR/contracts-check.out" >&2 || true
        die "run ./build.sh --refreeze to accept the new contracts, or put the old text back."
    fi
    cp "$STATE_DIR/contracts.now" "$STATE_DIR/contracts.sha256"
    log_ok "$sc_count contracts match contracts/SHA256SUMS. The token report is at $LOGS_DIR/tokens.txt"
}

# ---------------------------------------------------------------------------
# Step 3. Implementations
# ---------------------------------------------------------------------------

step_impl() {
    mkdir -p "$ROOT/src"
    for si_fn in $UNIT_NAMES; do
        si_stamp=$(contract_stamp "$si_fn")
        if [ -f "$ROOT/src/$si_fn.js" ] && ledger_stamp_ok "impl.$si_fn" "$si_stamp"; then
            log_ok "src/$si_fn.js matches the frozen contract. The build keeps it."
            continue
        fi
        if [ -f "$STATE_DIR/impl.$si_fn.done" ]; then
            log_warn "the contract of $si_fn changed. The build asks the model again."
        fi
        log_info "the unit $si_fn starts."
        si_user="$FM_WORK_DIR/prompt.impl.$si_fn"
        si_sys=$(assemble_impl_prompt "$si_fn" "$si_user")
        IMPL_FN="$si_fn"
        if ! fm_generate "$si_sys" "$si_user" "$FM_WORK_DIR/$si_fn.impl.out" validate_impl; then
            if ! unit_fallback "$si_fn"; then
                die "the model cannot write the unit $si_fn. Read $FEEDBACK_DIR/unit.txt and the contract $(contract_path "$si_fn")."
            fi
        fi
        printf '%s\n' "$si_stamp" >"$STATE_DIR/impl.$si_fn.done"
        log_ok "src/$si_fn.js is ready ($(wc -c <"$ROOT/src/$si_fn.js" | tr -d ' ') bytes)."
    done
}

# unit_fallback copies the FALLBACK block of a contract when ALLOW_FALLBACK is 1.
unit_fallback() {
    uf_fn="$1"
    [ "$ALLOW_FALLBACK" = "1" ] || return 1
    uf_body=$(contract_section "$(contract_path "$uf_fn")" 'FALLBACK')
    if [ -z "$(printf '%s' "$uf_body" | tr -d '[:space:]')" ]; then
        log_err "the contract of $uf_fn holds no FALLBACK block."
        return 1
    fi
    {
        deps_header "$uf_fn"
        printf '%s\n' "$uf_body" | awk '/^[[:space:]]*```/ { next } { print }'
    } >"$ROOT/src/$uf_fn.js"
    node --check "$ROOT/src/$uf_fn.js" || { log_err "the FALLBACK block of $uf_fn does not parse."; return 1; }
    FALLBACKS_USED="$FALLBACKS_USED $uf_fn"
    log_warn "the unit $uf_fn comes from the contract FALLBACK block. The model did not write it."
    return 0
}

# ---------------------------------------------------------------------------
# Step 4. Blind tests
# ---------------------------------------------------------------------------

step_tests() {
    mkdir -p "$ROOT/test"
    for st_fn in $UNIT_NAMES; do
        st_stamp=$(contract_stamp "$st_fn")
        if [ -f "$ROOT/test/$st_fn.test.mjs" ] && ledger_stamp_ok "test.$st_fn" "$st_stamp"; then
            log_ok "test/$st_fn.test.mjs matches the frozen contract. The build keeps it."
            continue
        fi
        if [ -f "$STATE_DIR/test.$st_fn.done" ]; then
            log_warn "the contract of $st_fn changed. The build asks the model for a new test."
        fi
        log_info "the blind test of $st_fn starts. The prompt holds no implementation."
        st_user="$FM_WORK_DIR/prompt.test.$st_fn"
        assemble_test_prompt "$st_fn" "$st_user"
        TEST_FN="$st_fn"
        if ! fm_generate "$ROOT/prompts/test.md" "$st_user" "$FM_WORK_DIR/$st_fn.test.out" validate_test; then
            die "the model cannot write the test of $st_fn. Read the CASES table of $(contract_path "$st_fn")."
        fi
        printf '%s\n' "$st_stamp" >"$STATE_DIR/test.$st_fn.done"
        log_ok "test/$st_fn.test.mjs holds $(grep -c '^test(' "$ROOT/test/$st_fn.test.mjs" || true) test blocks."
    done
    # Every unit needs a test file before the freeze. A missing file must never
    # shrink the frozen list without a word.
    for st_fn in $UNIT_NAMES; do
        [ -f "$ROOT/test/$st_fn.test.mjs" ] ||
            die "test/$st_fn.test.mjs is absent. The build cannot freeze an incomplete suite."
    done
    # The freeze covers the 13 blind test files and nothing else. A glob over test/
    # would also freeze a strengthen file, and a later strengthen round that writes
    # the same round label would then trip the frozen check and stop the build.
    : >"$STATE_DIR/tests.sha256"
    for st_fn in $UNIT_NAMES; do
        ( cd "$ROOT" && shasum -a 256 "test/$st_fn.test.mjs" ) >>"$STATE_DIR/tests.sha256"
    done
    log_ok "the 13 blind test files are frozen. The sums are at $STATE_DIR/tests.sha256"
}

# ---------------------------------------------------------------------------
# Step 5. The barrel
# ---------------------------------------------------------------------------

step_assemble() {
    sa_out="$ROOT/src/core.js"
    {
        printf '// src/core.js - the barrel of the core units.\n'
        printf '// build.sh writes this file. The model never writes an import line.\n'
        for sa_fn in $UNIT_NAMES; do
            printf "export { %s } from './%s.js';\n" "$sa_fn" "$sa_fn"
        done
    } >"$sa_out"
    node --check "$sa_out" || die "node --check refuses src/core.js."
    sa_names=$(printf '%s' "$UNIT_NAMES" | tr ' ' ',')
    ( cd "$ROOT" && node -e "
        import('./src/core.js').then(m => {
          const want = '$sa_names'.split(',');
          const bad = want.filter(n => typeof m[n] !== 'function');
          if (bad.length) { console.error('MISSING ' + bad.join(' ')); process.exit(3); }
        }).catch(e => { console.error(String(e)); process.exit(4); });
    " ) >"$LOGS_DIR/barrel.out" 2>&1 || {
        cat "$LOGS_DIR/barrel.out" >&2
        die "src/core.js does not export every core name. See $LOGS_DIR/barrel.out"
    }
    log_ok "src/core.js exports the $(printf '%s\n' "$UNIT_NAMES" | wc -w | tr -d ' ') core names."
}

# ---------------------------------------------------------------------------
# The repair loop
# ---------------------------------------------------------------------------

# failing_units prints the failing unit names in dependency order.
failing_units() {
    fu_files=$(gates_failing_files "$LOGS_DIR/unit.out")
    for fu_fn in $UNIT_NAMES; do
        case "$fu_files" in
            *"test/$fu_fn.test.mjs"*) printf '%s\n' "$fu_fn" ;;
        esac
    done
}

# test_blocks prints the verbatim test blocks of the failing cases of one unit.
# Argument 1 is the unit. Argument 2 is the maximum count. Argument 3 is the line clip.
test_blocks() {
    tb_file="$ROOT/test/$1.test.mjs"
    [ -f "$tb_file" ] || return 0
    tb_names=$(grep " FILE test/$1.test.mjs" "$FEEDBACK_DIR/unit.txt" 2>/dev/null |
        sed 's/^TEST //; s/ | FILE .*//' | head -"$2" || true)
    tb_i=0
    while IFS= read -r tb_n; do
        [ -n "$tb_n" ] || continue
        tb_i=$((tb_i + 1))
        awk -v want="$tb_n" -v clip="$3" '
            index($0, "test(") == 1 && index($0, want) > 0 { on = 1; k = 0 }
            on == 1 {
                k = k + 1
                if (k <= clip) { print }
                if ($0 ~ /^\}\);[[:space:]]*$/) { on = 0 }
            }
        ' "$tb_file"
    done <<EOF
$tb_names
EOF
}

# build_repair_prompt writes the repair user prompt of one unit at one truncation level.
# Argument 1 is the unit. Argument 2 is the level. Argument 3 is the escalation file.
# Argument 4 is the output file.
build_repair_prompt() {
    br_fn="$1"
    br_level="$2"
    br_esc="$3"
    br_out="$4"
    br_c=$(contract_path "$br_fn")

    br_maxt=100
    br_clip=400
    br_valclip=1000
    br_observed=1
    br_examples=1
    [ "$br_level" -ge 1 ] && br_maxt=3
    [ "$br_level" -ge 2 ] && br_clip=15
    [ "$br_level" -ge 3 ] && br_valclip=200
    [ "$br_level" -ge 4 ] && br_observed=0
    [ "$br_level" -ge 5 ] && br_maxt=1
    [ "$br_level" -ge 6 ] && br_examples=0

    val_new "repair.$br_fn"
    {
        contract_section "$br_c" 'SIGNATURE'
        printf '\n'
        contract_section "$br_c" 'DESCRIPTION'
        if [ "$br_examples" -eq 1 ]; then
            printf '\nEXAMPLES\n'
            contract_section "$br_c" 'EXAMPLES'
        fi
    } | val_set CONTRACT
    grep -v '^import ' "$ROOT/src/$br_fn.js" | val_set CURRENT_CODE
    test_blocks "$br_fn" "$br_maxt" "$br_clip" | val_set FAILING_TEST_SOURCE
    if [ "$br_observed" -eq 1 ]; then
        gates_condense_unit "$LOGS_DIR/unit.out" "$br_maxt" "$br_valclip" |
            grep " FILE test/$br_fn.test.mjs" | val_set OBSERVED
    else
        printf '' | val_set OBSERVED
    fi
    cat "$br_esc" | val_set ESCALATION
    render_template "$ROOT/prompts/repair.user.md" "$VALDIR" >"$br_out"
}

# fit_repair_prompt walks the truncation ladder until the prompt fits.
fit_repair_prompt() {
    fr_fn="$1"
    fr_esc="$2"
    fr_out="$3"
    fr_level=0
    while [ "$fr_level" -le 6 ]; do
        build_repair_prompt "$fr_fn" "$fr_level" "$fr_esc" "$fr_out"
        fr_n=$(fm_count_tokens "$fr_out" || printf '')
        if [ -z "$fr_n" ]; then
            log_warn "count-tokens gave no number. The ladder stops at the level $fr_level."
            return 0
        fi
        if [ "$fr_n" -le "$REPAIR_BUDGET" ]; then
            log_info "the repair prompt of $fr_fn holds $fr_n tokens at the truncation level $fr_level."
            return 0
        fi
        fr_level=$((fr_level + 1))
    done
    log_err "repair prompt cannot fit the context window for $fr_fn"
    return 1
}

# escalation_file writes the escalation slot of one attempt.
escalation_file() {
    ef_fn="$1"
    ef_attempt="$2"
    ef_out="$3"
    ef_hint=$(contract_section "$(contract_path "$ef_fn")" 'HINT' | sed '/^[[:space:]]*$/d' | head -3)
    case "$ef_attempt" in
        1) : >"$ef_out" ;;
        2)
            {
                printf 'Attempt 2. Your previous answer was still wrong.\n'
                if [ -n "$ef_hint" ]; then printf 'Rule: %s\n' "$ef_hint"; fi
            } >"$ef_out"
            ;;
        *)
            {
                printf 'Attempt 3. Write exactly this expression:\n'
                printf '%s\n' "$ef_hint"
            } >"$ef_out"
            ;;
    esac
}

# repair_unit runs one repair attempt of one unit. It returns 0 when the model answered.
repair_unit() {
    ru_fn="$1"
    ru_attempt="$2"
    REPAIR_ATTEMPTS=$((REPAIR_ATTEMPTS + 1))

    case "$ru_fn" in
        step | advance)
            log_warn "the unit $ru_fn never enters the normal repair loop. The build re-issues the skeleton."
            if [ "$ru_attempt" -gt 2 ]; then
                log_err "the unit $ru_fn used the two skeleton re-issues that the design allows."
                return 1
            fi
            reissue_skeleton "$ru_fn" "$ru_attempt"
            return $?
            ;;
    esac

    ru_esc="$FM_WORK_DIR/esc.$ru_fn.$ru_attempt"
    escalation_file "$ru_fn" "$ru_attempt" "$ru_esc"
    ru_user="$FM_WORK_DIR/prompt.repair.$ru_fn.$ru_attempt"
    fit_repair_prompt "$ru_fn" "$ru_esc" "$ru_user" || return 1

    if [ "$ru_attempt" -ge 3 ] && [ "$(contract_inline "$(contract_path "$ru_fn")" 'STYLE')" != 'skeleton' ]; then
        if [ -n "$(contract_section "$(contract_path "$ru_fn")" 'SKELETON' | tr -d '[:space:]')" ]; then
            log_info "the attempt 3 of $ru_fn uses the skeleton prompt."
            reissue_skeleton "$ru_fn" 1
            return $?
        fi
    fi

    IMPL_FN="$ru_fn"
    fm_generate "$ROOT/prompts/repair.md" "$ru_user" "$FM_WORK_DIR/$ru_fn.repair.$ru_attempt.out" validate_impl
}

# reissue_skeleton asks the model for the unit again with the holes made more literal.
reissue_skeleton() {
    rs_fn="$1"
    rs_round="$2"
    rs_c=$(contract_path "$rs_fn")
    if [ -z "$(contract_section "$rs_c" 'SKELETON' | tr -d '[:space:]')" ]; then
        log_err "the contract of $rs_fn holds no SKELETON section. The build cannot re-issue it."
        return 1
    fi
    val_new "skel.$rs_fn.$rs_round"
    contract_section "$rs_c" 'DEPS' | val_set DEPS
    contract_section "$rs_c" 'SKELETON' | val_set SKELETON
    {
        contract_section "$rs_c" 'HOLES'
        if [ "$rs_round" -ge 2 ]; then
            printf '\nCopy every hole text exactly, character for character.\n'
            contract_section "$rs_c" 'HINT'
        fi
    } | val_set HOLES
    rs_user="$FM_WORK_DIR/prompt.skel.$rs_fn.$rs_round"
    render_template "$ROOT/prompts/skeleton.user.md" "$VALDIR" >"$rs_user"
    IMPL_FN="$rs_fn"
    fm_generate "$ROOT/prompts/skeleton.md" "$rs_user" "$FM_WORK_DIR/$rs_fn.skel.$rs_round.out" validate_impl
}

# ---------------------------------------------------------------------------
# Step 6. The unit gate
# ---------------------------------------------------------------------------

step_unit_gate() {
    frozen_tests_verify || exit 1
    # The counters belong to this run of the gate. A counter that survives the run
    # makes every later resume give up with zero repair attempts, and the recovery
    # command that the build prints can then never succeed.
    rm -f "$FM_WORK_DIR"/attempts.unit.*
    su_round=0
    while [ "$su_round" -le 40 ]; do
        if gate_unit; then
            frozen_tests_verify || exit 1
            return 0
        fi
        su_fn=$(failing_units | head -1)
        if [ -z "$su_fn" ]; then
            log_err "the unit gate fails but no core unit owns a failing test."
            log_err "read $LOGS_DIR/unit.out"
            return 1
        fi
        su_key="$FM_WORK_DIR/attempts.unit.$su_fn"
        su_att=$(cat "$su_key" 2>/dev/null || printf '0')
        su_att=$((su_att + 1))
        printf '%s\n' "$su_att" >"$su_key"
        if [ "$su_att" -gt "$FM_RETRIES" ]; then
            if unit_fallback "$su_fn"; then
                su_round=$((su_round + 1))
                continue
            fi
            log_err "the unit $su_fn is still red after $FM_RETRIES repair attempts."
            log_err "the last prompt is at $FM_WORK_DIR/prompt.repair.$su_fn.$FM_RETRIES"
            log_err "reproduce it with: $FM_BIN respond --no-stream -g -i \"\$(cat $ROOT/prompts/repair.md)\" < $FM_WORK_DIR/prompt.repair.$su_fn.$FM_RETRIES"
            log_err "the first triage action is to read the CASES table of $(contract_path "$su_fn")."
            return 1
        fi
        log_info "the unit $su_fn enters the repair loop. Attempt $su_att of $FM_RETRIES."
        frozen_tests_verify || exit 1
        repair_unit "$su_fn" "$su_att" || log_warn "the repair attempt $su_att of $su_fn gave no valid answer."
        frozen_tests_verify || exit 1
        su_round=$((su_round + 1))
    done
    log_err "the unit gate made 40 rounds without a green result."
    return 1
}

# ---------------------------------------------------------------------------
# Step 7. The complexity gate
# ---------------------------------------------------------------------------

step_complexity() {
    rm -f "$FM_WORK_DIR"/attempts.complexity.*
    sx_round=0
    while [ "$sx_round" -le 20 ]; do
        if gate_complexity; then
            return 0
        fi
        sx_file=$(awk -F'|' '{ print $1 }' "$FEEDBACK_DIR/complexity.txt" | sed 's/^FILE //; s/[[:space:]]*$//' | head -1)
        sx_fn=$(basename "$sx_file" .js)
        if ! printf ' %s ' "$UNIT_NAMES" | grep -q " $sx_fn "; then
            log_err "eslint reports a problem in $sx_file. That file is not a core unit."
            cat "$FEEDBACK_DIR/complexity.txt" >&2
            return 1
        fi
        sx_key="$FM_WORK_DIR/attempts.complexity.$sx_fn"
        sx_att=$(cat "$sx_key" 2>/dev/null || printf '0')
        sx_att=$((sx_att + 1))
        printf '%s\n' "$sx_att" >"$sx_key"
        if [ "$sx_att" -gt 2 ]; then
            log_info "two repairs did not fix $sx_fn. The build re-issues the decomposed skeleton."
            if reissue_skeleton "$sx_fn" 2; then
                sx_round=$((sx_round + 1))
                continue
            fi
            log_err "the unit $sx_fn cannot pass the complexity gate."
            log_err "$(gates_complexity_line "$sx_fn")"
            return 1
        fi
        sx_esc="$FM_WORK_DIR/esc.cx.$sx_fn.$sx_att"
        {
            printf 'eslint reports this problem. Fix it and keep every rule of the contract.\n'
            gates_complexity_line "$sx_fn"
        } >"$sx_esc"
        sx_user="$FM_WORK_DIR/prompt.cx.$sx_fn.$sx_att"
        val_new "cx.$sx_fn"
        {
            contract_section "$(contract_path "$sx_fn")" 'SIGNATURE'
            printf '\n'
            contract_section "$(contract_path "$sx_fn")" 'DESCRIPTION'
        } | val_set CONTRACT
        grep -v '^import ' "$ROOT/src/$sx_fn.js" | val_set CURRENT_CODE
        printf '' | val_set FAILING_TEST_SOURCE
        gates_complexity_line "$sx_fn" | val_set OBSERVED
        cat "$sx_esc" | val_set ESCALATION
        render_template "$ROOT/prompts/repair.user.md" "$VALDIR" >"$sx_user"
        IMPL_FN="$sx_fn"
        fm_generate "$ROOT/prompts/repair.md" "$sx_user" "$FM_WORK_DIR/$sx_fn.cx.$sx_att.out" validate_impl ||
            log_warn "the complexity repair of $sx_fn gave no valid answer."
        sx_round=$((sx_round + 1))
    done
    return 1
}

# ---------------------------------------------------------------------------
# Step 8. The coverage gate
# ---------------------------------------------------------------------------

# step_coverage has no repair loop of its own, and that is on purpose.
# tools/derive.mjs reads SURVIVOR rows and nothing else, so a coverage report can
# never give it a killing input. A strengthen call on this report always made zero
# model calls and then printed a message about equivalent mutants during a coverage
# failure, which named the wrong subsystem. The gate now names the uncovered lines
# and the contract to widen.
step_coverage() {
    if gate_coverage; then
        return 0
    fi
    log_err "the coverage gate is short. The blind CASES tables do not reach every line."
    grep '^UNCOVERED' "$FEEDBACK_DIR/coverage.txt" >&2 || true
    grep '^NO_ROW' "$FEEDBACK_DIR/coverage.txt" >&2 || true
    log_err "add a case to the CASES table of the contract of that unit, then run:"
    log_err "  ./build.sh --refreeze"
    return 1
}

# ---------------------------------------------------------------------------
# Step 9. The mutation gate
# ---------------------------------------------------------------------------

step_mutation() {
    sm_round=0
    : >"$FEEDBACK_DIR/equivalent.txt"
    while [ "$sm_round" -lt "$STRENGTHEN_ROUNDS" ]; do
        if gate_mutation; then
            frozen_tests_verify || exit 1
            return 0
        fi
        sm_round=$((sm_round + 1))
        log_info "the strengthen round $sm_round of $STRENGTHEN_ROUNDS starts."
        if ! strengthen_pass "$sm_round"; then
            break
        fi
        frozen_tests_verify || exit 1
    done

    if gate_mutation; then
        return 0
    fi
    mutation_amnesty
}

# mutation_amnesty accepts a red score only when the build can PROVE that no input of
# the domain separates any remaining mutant.
# It compares two sets of locations, never two counts. A count comparison accepted a
# run in which the equivalent list named other files than the survivor list, and the
# equivalent list grew by one entry for the same mutant on every round.
mutation_amnesty() {
    ma_left=$(gates_survivor_count)
    if [ "$ma_left" -eq 0 ]; then
        log_err "the mutation gate stays red and stryker listed no survivor at all."
        log_err "read $LOGS_DIR/mutation.out"
        return 1
    fi
    ma_score=$(awk '/^SCORE / { print $2 }' "$FEEDBACK_DIR/mutation.txt" | tail -1)
    [ -n "$ma_score" ] || ma_score=0
    ma_floor=$((MUTATION_THRESHOLD - 10))
    if ! gates_pct_ge "$ma_score" "$ma_floor"; then
        log_err "the mutation score $ma_score percent is more than 10 points under the threshold."
        log_err "the build never accepts a score that low, whatever the survivors are."
        return 1
    fi

    # Classify the survivors of THIS run. The accumulated file of the rounds describes
    # older survivor sets and it holds one entry for each round of the same mutant.
    ma_der="$FM_WORK_DIR/derive.amnesty.out"
    if ! ( cd "$ROOT" && node tools/derive.mjs <"$FEEDBACK_DIR/mutation.txt" ) >"$ma_der" 2>"$ma_der.err"; then
        log_err "tools/derive.mjs failed. See $ma_der.err"
        return 1
    fi
    gates_survivor_locs >"$FM_WORK_DIR/locs.survivor.txt"
    gates_equivalent_locs "$ma_der" >"$FM_WORK_DIR/locs.equivalent.txt"
    if grep -q '^UNPROVEN ' "$ma_der"; then
        log_err "tools/derive.mjs could not judge every survivor:"
        grep '^UNPROVEN ' "$ma_der" >&2
        log_err "an unproven mutant is a red mutant. The gate stays red."
        return 1
    fi
    if cmp -s "$FM_WORK_DIR/locs.survivor.txt" "$FM_WORK_DIR/locs.equivalent.txt"; then
        log_warn "every remaining mutant is equivalent. No input of the domain separates one."
        grep '^EQUIVALENT ' "$ma_der" | tee "$FEEDBACK_DIR/equivalent.txt"
        return 0
    fi
    log_err "the mutation gate stays red after $STRENGTHEN_ROUNDS rounds."
    log_err "$ma_left survivors and $(wc -l <"$FM_WORK_DIR/locs.equivalent.txt" | tr -d ' ') proven equivalent ones."
    log_err "the survivors are in $FEEDBACK_DIR/mutation.txt"
    return 1
}

# strengthen_pass asks the model for tests that kill the surviving mutants.
# Argument 1 is the round label. tools/derive.mjs finds every input and every expected value.
strengthen_pass() {
    sp_round="$1"
    if [ ! -f "$ROOT/tools/derive.mjs" ]; then
        log_err "tools/derive.mjs is absent. The model can never find a killing input by itself."
        log_err "the tool must read the SURVIVOR lines of $FEEDBACK_DIR/mutation.txt on stdin and print,"
        log_err "for each survivor, the word EQUIVALENT and the location, or a block:"
        log_err "  FILL <location>"
        log_err "  <the ready text of one FILL block>"
        log_err "  ENDFILL"
        return 1
    fi
    sp_in="$FEEDBACK_DIR/mutation.txt"
    sp_der="$FM_WORK_DIR/derive.$sp_round.out"
    ( cd "$ROOT" && node tools/derive.mjs <"$sp_in" ) >"$sp_der" 2>"$sp_der.err" || {
        log_err "tools/derive.mjs failed. See $sp_der.err"
        return 1
    }
    grep '^EQUIVALENT' "$sp_der" >>"$FEEDBACK_DIR/equivalent.txt" || true

    sp_fills="$FM_WORK_DIR/fills.$sp_round.txt"
    sp_user="$FM_WORK_DIR/prompt.strengthen.$sp_round"

    # The strengthen prompt needs the same token ladder that the repair prompt has.
    # Twenty fills of the unit step measure about 2400 tokens against a budget of
    # 1500, so fm_generate would refuse the prompt without one model call, and the
    # round loop would then break and lose every later round.
    sp_n="$STRENGTHEN_FILLS"
    while [ "$sp_n" -ge 1 ]; do
        awk -v maxn="$sp_n" '
            /^FILL / { n = n + 1; if (n <= maxn) { on = 1 }; next }
            /^ENDFILL/ { on = 0; next }
            on == 1 { print }
        ' "$sp_der" >"$sp_fills"
        if [ ! -s "$sp_fills" ]; then
            log_warn "tools/derive.mjs found no killing input. Every survivor is equivalent."
            return 1
        fi
        val_new "strengthen.$sp_round"
        printf '%s\n' "$(printf '%s' "$UNIT_NAMES" | tr ' ' ',' | sed 's/,/, /g')" | val_set EXPORT_LIST
        printf '../src/core.js\n' | val_set MODULE_PATH
        cat "$sp_fills" | val_set FILL_BLOCKS
        render_template "$ROOT/prompts/strengthen.user.md" "$VALDIR" >"$sp_user"
        cat "$ROOT/prompts/strengthen.md" "$sp_user" >"$FM_WORK_DIR/measure.strengthen"
        sp_tok=$(fm_count_tokens "$FM_WORK_DIR/measure.strengthen" || printf '')
        if [ -z "$sp_tok" ]; then
            log_warn "count-tokens gave no number. The strengthen ladder stops at $sp_n fills."
            break
        fi
        if [ "$sp_tok" -le "$FM_PROMPT_BUDGET" ]; then
            log_info "the strengthen prompt of the round $sp_round holds $sp_tok tokens with $sp_n fills."
            break
        fi
        if [ "$sp_n" -eq 1 ]; then
            log_err "one fill alone holds $sp_tok tokens. The budget is $FM_PROMPT_BUDGET."
            return 1
        fi
        sp_n=$((sp_n / 2))
    done

    if ! fm_generate "$ROOT/prompts/strengthen.md" "$sp_user" "$FM_WORK_DIR/strengthen.$sp_round.out"; then
        log_warn "the strengthen call of the round $sp_round gave no valid answer."
        return 1
    fi

    sp_new="$ROOT/test/strengthen-$sp_round.test.mjs"
    cp "$FM_WORK_DIR/strengthen.$sp_round.out" "$sp_new"
    if ! node --check "$sp_new" >"$LOGS_DIR/strengthen.$sp_round.out" 2>&1; then
        log_warn "the strengthen file of the round $sp_round does not parse. The build removes it."
        rm -f "$sp_new"
        return 1
    fi
    if ! ( cd "$ROOT" && node --test "test/strengthen-$sp_round.test.mjs" ) >>"$LOGS_DIR/strengthen.$sp_round.out" 2>&1; then
        log_warn "the strengthen file of the round $sp_round fails against the true source. The build removes it."
        rm -f "$sp_new"
        return 1
    fi
    log_ok "test/strengthen-$sp_round.test.mjs passes against the true source."
    return 0
}

# ---------------------------------------------------------------------------
# Step 10. The browser layer
# ---------------------------------------------------------------------------

render_contract() {
    printf '%s/contracts/render-%s.md\n' "$ROOT" "$1"
}

step_renderer() {
    mkdir -p "$ROOT/web"
    : >"$LOGS_DIR/check.render.out"
    sr_parts="$FM_WORK_DIR/render.parts"
    : >"$sr_parts"

    while IFS='|' read -r sr_name sr_params <&3; do
        [ -n "$sr_name" ] || continue
        sr_c=$(render_contract "$sr_name")
        need_file "$sr_c" "The contract author writes contracts/render-<name>.md with the sections GLOSSARY, STEPS, EXAMPLES, SCOPE and RETURN_CLAUSE."
        val_new "render.$sr_name"
        printf '%s\n' "$sr_name" | val_set NAME
        printf '%s\n' "$sr_params" | val_set PARAMS
        contract_section "$sr_c" 'GLOSSARY' | val_set GLOSSARY
        contract_section "$sr_c" 'STEPS' | val_set STEPS
        contract_section "$sr_c" 'EXAMPLES' | val_set EXAMPLES
        contract_section "$sr_c" 'SCOPE' | val_set SCOPE
        contract_section "$sr_c" 'RETURN_CLAUSE' | val_set RETURN_CLAUSE
        sr_user="$FM_WORK_DIR/prompt.render.$sr_name"
        render_template "$ROOT/prompts/render.user.md" "$VALDIR" >"$sr_user"
        RENDER_FN="$sr_name"
        if ! fm_generate "$ROOT/prompts/render.md" "$sr_user" "$FM_WORK_DIR/render.$sr_name.js" validate_render; then
            die "the model cannot write the browser function $sr_name."
        fi
        printf '%s\n' "$FM_WORK_DIR/render.$sr_name.js" >>"$sr_parts"
        log_ok "the browser function $sr_name is ready."
    done 3<<<"$RENDER_UNITS"

    # The fixed header holds every line that joins the four model written functions.
    # The model never writes an import line and never writes the shared input variable.
    {
        printf "import { createState, step } from '../src/core.js';\n"
        printf "const queued = [];\n"
        printf "const tick = (s) => step(s, queued.length > 0 ? queued.shift() : null, Math.random);\n"
        printf "const press = (e) => {\n"
        printf "  const d = keyToInput(e.key);\n"
        printf "  if (!d) { return; }\n"
        printf "  e.preventDefault();\n"
        printf "  if (queued.length < 3) { queued.push(d); }\n"
        printf "};\n"
        while IFS= read -r sr_p; do
            [ -n "$sr_p" ] || continue
            printf '\n'
            cat "$sr_p"
        done <"$sr_parts"
        printf '\nboot(document, 20, 20, 20);\n'
    } >"$ROOT/web/game.js"

    if grep -q '`' "$ROOT/web/game.js"; then
        die "web/game.js holds a backtick after the fence strip."
    fi
    node --check "$ROOT/web/game.js" || die "node --check refuses web/game.js."
    ( cd "$ROOT" && npx eslint -c eslint.web.mjs web/game.js ) >"$LOGS_DIR/lint-web.out" 2>&1 || {
        cat "$LOGS_DIR/lint-web.out" >&2
        die "eslint refuses web/game.js."
    }
    for sr_k in ArrowUp ArrowDown ArrowLeft ArrowRight; do
        grep -q "$sr_k" "$ROOT/web/game.js" || die "web/game.js holds no key name $sr_k."
    done
    # CapsLock and the shift key give an upper case letter in KeyboardEvent.key.
    # A map of the lower case letters alone leaves the W, A, S and D keys dead.
    for sr_k in W A S D; do
        grep -q "'$sr_k'" "$ROOT/web/game.js" || die "web/game.js does not map the upper case key $sr_k."
    done
    grep -q 'preventDefault' "$ROOT/web/game.js" || die "web/game.js never calls preventDefault. The arrow keys would scroll the page."
    log_ok "web/game.js parses, lints and maps the arrow keys in both letter cases."

    if [ ! -f "$ROOT/web/index.html" ]; then
        if ! fm_generate "$ROOT/prompts/html.md" "$ROOT/prompts/html.user.md" "$FM_WORK_DIR/index.html" validate_html; then
            die "the model cannot write web/index.html."
        fi
        cp "$FM_WORK_DIR/index.html" "$ROOT/web/index.html"
    fi
    grep -q '<canvas id="game"' "$ROOT/web/index.html" || die "web/index.html holds no canvas with the id game."
    grep -q '<script type="module" src="game.js">' "$ROOT/web/index.html" || die "web/index.html holds no module script tag."
    html_border_ok "$ROOT/web/index.html" || die "web/index.html gives the canvas no border. The player cannot see the walls."
    log_ok "web/index.html is ready. The canvas carries a visible border."
}

# ---------------------------------------------------------------------------
# Step 11. The playtest
# ---------------------------------------------------------------------------

step_playtest() {
    need_file "$ROOT/tools/drive.mjs" "The tool author writes the fake DOM driver."
    sp_out="$LOGS_DIR/playtest.out"
    if ! ( cd "$ROOT" && node tools/drive.mjs ) >"$sp_out" 2>&1; then
        cat "$sp_out" >&2
        die "the fake DOM driver refuses web/game.js. node --check cannot prove that a renderer runs."
    fi
    grep -q 'ALL RUNTIME ASSERTIONS PASSED' "$sp_out" ||
        die "tools/drive.mjs exits 0 but it did not print ALL RUNTIME ASSERTIONS PASSED."
    log_ok "the game runs under the fake DOM. Every runtime assertion passes."
}

# ---------------------------------------------------------------------------
# Step 12. The report
# ---------------------------------------------------------------------------

step_package() {
    sk_report="$BUILD_DIR/report.txt"
    {
        printf 'Snake build report\n'
        printf '==================\n\n'
        printf 'Date            %s\n' "$(date '+%Y-%m-%d %H:%M:%S')"
        printf 'Model           %s\n' "$FM_BIN"
        printf 'Model calls     %s\n' "$(counters_get calls)"
        printf 'Cache hits      %s\n' "$(counters_get hits)"
        printf 'Repair attempts %s\n' "$(counters_get repairs)"
        printf '\nGate results\n------------\n'
        printf 'unit        %s\n' "$(test -s "$FEEDBACK_DIR/unit.txt" && printf 'see feedback' || printf 'green')"
        printf 'complexity  %s\n' "$(test -s "$FEEDBACK_DIR/complexity.txt" && printf 'see feedback' || printf 'green')"
        printf 'coverage    %s\n' "$(grep '^LINE' "$FEEDBACK_DIR/coverage.txt" 2>/dev/null || printf 'not run')"
        printf 'branches    %s\n' "$(grep '^BRANCH' "$FEEDBACK_DIR/coverage.txt" 2>/dev/null || printf 'not run')"
        printf 'mutation    %s\n' "$(grep '^SCORE' "$FEEDBACK_DIR/mutation.txt" 2>/dev/null || printf 'not run')"
        printf '\nEquivalent mutants\n------------------\n'
        if [ -s "$FEEDBACK_DIR/equivalent.txt" ]; then
            cat "$FEEDBACK_DIR/equivalent.txt"
        else
            printf 'none\n'
        fi
        printf '\nUnits that came from a contract fallback\n'
        if [ -n "$FALLBACKS_USED" ]; then
            printf '%s\n' "$FALLBACKS_USED"
        else
            printf 'none. The model wrote every unit.\n'
        fi
        printf '\nStep times\n----------\n'
        if [ -s "$STATE_DIR/steptimes.txt" ]; then
            cat "$STATE_DIR/steptimes.txt"
        else
            printf 'no step ran in this build.\n'
        fi
    } >"$sk_report"
    log_ok "the report is at $sk_report"

    sk_missing=''
    for sk_p in build.sh package.json eslint.config.mjs stryker.config.json .gitignore \
        lib/log.sh lib/fm.sh lib/gates.sh src/core.js web/index.html web/game.js; do
        [ -e "$ROOT/$sk_p" ] || sk_missing="$sk_missing $sk_p"
    done
    if [ -n "$sk_missing" ]; then
        die "the repo layout misses:$sk_missing"
    fi
    log_ok "every path of the frozen repo layout exists."

    # The last gate is a real HTTP request. web/game.js imports ../src/core.js, so the
    # server root must be the project root. A server rooted at web/ answers 404 for the
    # core and the page stays black. Only a request proves this.
    gate_serve || die "the served game does not resolve its own module graph."

    printf '\n%sThe game is ready.%s\n' "${C_BOLD:-}${C_GREEN:-}" "${C_RESET:-}"
    printf 'Serve it with:\n'
    printf '    python3 -m http.server %s --directory %s\n' "$SERVE_PORT" "$ROOT"
    printf 'Then open http://localhost:%s/web/index.html\n' "$SERVE_PORT"
    printf 'Serve the project root, never the directory web.\n\n'
}

# ---------------------------------------------------------------------------
# The dispatcher
# ---------------------------------------------------------------------------

run_step() {
    rs_n="$1"
    rs_id="$2"
    rs_title="$3"
    CURRENT_STEP_ID="$rs_id"
    log_step "Step $rs_n  $rs_id  -  $rs_title"
    rs_t0=$(date '+%s')
    case "$rs_id" in
        preflight) step_preflight ;;
        scaffold) step_scaffold ;;
        contracts) step_contracts ;;
        impl) step_impl ;;
        tests) step_tests ;;
        assemble) step_assemble ;;
        unit-gate) step_unit_gate || { print_resume; exit 1; } ;;
        complexity) step_complexity || { print_resume; exit 1; } ;;
        coverage) step_coverage || { print_resume; exit 1; } ;;
        mutation) step_mutation || { print_resume; exit 1; } ;;
        renderer) step_renderer ;;
        playtest) step_playtest ;;
        package) step_package ;;
        *) die "the step id '$rs_id' is unknown." ;;
    esac
    rs_t1=$(date '+%s')
    printf '%s %-12s %s seconds\n' "$rs_n" "$rs_id" "$((rs_t1 - rs_t0))" >>"$STATE_DIR/steptimes.txt"
    counters_persist
    ledger_mark "$rs_n"
    log_ok "the step $rs_n ($rs_id) took $((rs_t1 - rs_t0)) seconds."
}

do_clean() {
    log_warn "the flag --clean removes the generated files."
    # The build lock lives inside $BUILD_DIR. A removal of the whole directory would
    # drop a lock that this process holds and still believes it holds, and the EXIT
    # trap would then remove the lock directory of another build. The clean therefore
    # keeps the lock directory and never drops the lock.
    if [ -d "$BUILD_DIR" ]; then
        find "$BUILD_DIR" -mindepth 1 -maxdepth 1 ! -name 'build.lock' -exec rm -rf {} +
    fi
    rm -rf "$ROOT/src" "$ROOT/test" "$ROOT/web/game.js" "$ROOT/web/index.html" \
        "$ROOT/.stryker-tmp" "$ROOT/contracts/SHA256SUMS" "$ROOT/reports"
    mkdir -p "$BUILD_DIR"
    log_ok "the build state, src, test and web/game.js are gone."
}

do_serve() {
    [ -f "$ROOT/web/index.html" ] || die "web/index.html is absent. Run the build first."
    [ -f "$ROOT/src/core.js" ] || die "src/core.js is absent. Run the build first."
    # The server root is the project root, not web/. The browser resolves the import
    # '../src/core.js' of web/game.js against the server root.
    printf '\nThe game runs at http://localhost:%s/web/index.html\n' "$SERVE_PORT"
    printf 'Stop the server with ctrl-c.\n\n'
    exec python3 -m http.server "$SERVE_PORT" --directory "$ROOT"
}

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --clean) OPT_CLEAN=1 ;;
            --from)
                shift
                [ $# -gt 0 ] || die "the flag --from needs a step number."
                OPT_FROM="$1"
                check_step_number "$OPT_FROM" --from
                ;;
            --from=*)
                OPT_FROM="${1#--from=}"
                check_step_number "$OPT_FROM" --from
                ;;
            --only)
                shift
                [ $# -gt 0 ] || die "the flag --only needs a step number."
                OPT_ONLY="$1"
                ;;
            --only=*) OPT_ONLY="${1#--only=}" ;;
            --serve) OPT_SERVE=1 ;;
            --refreeze) OPT_REFREEZE=1 ;;
            --list) OPT_LIST=1 ;;
            --allow-fallback) ALLOW_FALLBACK=1 ;;
            -h | --help)
                usage
                exit 0
                ;;
            *) die "the flag '$1' is unknown. Run ./build.sh --help" ;;
        esac
        shift
    done
    if [ "$OPT_ONLY" != "-1" ]; then
        check_step_number "$OPT_ONLY" --only
    fi
    if [ "$OPT_ONLY" != "-1" ] && [ "$OPT_FROM" -ge 0 ]; then
        die "the flag --only and the flag --from never run together."
    fi
    # A refreeze has to reach the contract step. The step ledger would skip it.
    if [ "$OPT_REFREEZE" -eq 1 ] && [ "$OPT_ONLY" = "-1" ] && [ "$OPT_FROM" -lt 0 ]; then
        OPT_FROM=2
    fi
}

# check_step_number stops the build when a step number is not a number from 0 to 12.
check_step_number() {
    case "$1" in
        '' | *[!0-9]*) die "the value of $2 must be a number from 0 to 12." ;;
    esac
    [ "$1" -le 12 ] || die "the value of $2 must be a number from 0 to 12."
}

main() {
    parse_args "$@"
    mkdir -p "$BUILD_DIR" "$STATE_DIR" "$LOGS_DIR" "$FEEDBACK_DIR" "$FM_CACHE_DIR" \
        "$FM_TRANSCRIPT_DIR" "$FM_RAW_DIR" "$FM_WORK_DIR"
    log_init "$BUILD_DIR/build.log"

    # The model calls need the timeout program in every step, not only in the step 0.
    # A run with --only or --from skips the step 0, so the resolution happens here.
    fm_resolve_timeout
    if [ -z "$TIMEOUT_BIN" ]; then
        log_warn "no timeout program exists. The build uses a watchdog of its own."
    fi

    if [ "$OPT_LIST" -eq 1 ]; then
        list_steps
        exit 0
    fi

    build_lock

    if [ "$OPT_CLEAN" -eq 1 ]; then
        do_clean
        mkdir -p "$BUILD_DIR" "$STATE_DIR" "$LOGS_DIR" "$FEEDBACK_DIR" "$FM_CACHE_DIR" \
            "$FM_TRANSCRIPT_DIR" "$FM_RAW_DIR" "$FM_WORK_DIR"
        log_init "$BUILD_DIR/build.log"
    fi

    printf '%sThe Snake build starts. The model at %s writes every unit.%s\n' \
        "${C_BOLD:-}" "$FM_BIN" "${C_RESET:-}"

    while IFS='|' read -r mn mi mt <&3; do
        [ -n "$mn" ] || continue
        mnum=$((10#$mn))
        if [ "$OPT_ONLY" != "-1" ]; then
            [ "$mnum" -eq "$OPT_ONLY" ] || continue
            rm -f "$STATE_DIR/$mn.done"
            clear_step_state "$mn"
        else
            if [ "$mnum" -lt "$OPT_FROM" ]; then
                continue
            fi
            if [ "$OPT_FROM" -ge 0 ]; then
                rm -f "$STATE_DIR/$mn.done"
                clear_step_state "$mn"
            fi
            if ledger_done "$mn"; then
                log_ok "the step $mn ($mi) is already done."
                continue
            fi
        fi
        run_step "$mn" "$mi" "$mt"
    done 3<<<"$STEP_TABLE"

    # A step that runs alone changes the input of every later step. The ledger of
    # those steps is now stale, so the build clears it. Without this a plain run
    # after --only 10 declares the build finished and never gates the new code.
    if [ "$OPT_ONLY" != "-1" ]; then
        while IFS='|' read -r xn xi xt <&4; do
            [ -n "$xn" ] || continue
            if [ "$((10#$xn))" -gt "$OPT_ONLY" ]; then
                rm -f "$STATE_DIR/$xn.done"
            fi
        done 4<<<"$STEP_TABLE"
        log_warn "the steps after $OPT_ONLY are stale now. The build cleared their ledger."
    fi

    if [ "$OPT_SERVE" -eq 1 ]; then
        do_serve
    fi
}

main "$@"
