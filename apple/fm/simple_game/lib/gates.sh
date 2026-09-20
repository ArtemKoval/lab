#!/usr/bin/env bash
# lib/gates.sh - the quality gates of the build harness.
# This file is a library. Source it after lib/log.sh. Do not run it.
#
# Every gate returns 0 when it passes and 1 when it fails.
# Every gate writes one machine readable file under .build/feedback/.
# The repair loop reads only that file. Raw tool output never enters a model prompt.
#
# Measured output shapes that these parsers depend on:
#   node --test (node 24, no terminal) prints the spec reporter:
#       test at test/inc.test.mjs:5:1
#       <cross> wrong on purpose (2.164167ms)
#         AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
#             actual: 2,
#             expected: 99,
#     That printer stops at the depth 2 and breaks a long value over many lines,
#     so the build reads the event stream through tools/reporter.mjs instead.
#     The spec text stays in the log for a human reader only.
#   node --test --experimental-test-coverage prints one row for each loaded file:
#       <info>  turn.js        | 100.00 |   100.00 |  100.00 |
#       <info> all files | 100.00 |   100.00 |  100.00 |
#   eslint prints:
#       1:8   error  Function 'messy' has a complexity of 13. Maximum allowed is 5  complexity
#   stryker prints a diff of one or more lines for each survivor:
#       [Survived] EqualityOperator
#       src/clamp.js:2:7
#       -     if (n < 0) { return 0; }
#       +     if (n <= 0) { return 0; }
#       All files |  88.89 |   88.89 |        8 |         0 |          1 |        0 |        0 |

# gates_strip_ansi removes the colour codes of a tool.
gates_strip_ansi() {
    LC_ALL=C sed "s/$(printf '\033')\[[0-9;]*[A-Za-z]//g"
}

# gates_clip_values holds the GOT field and the EXPECTED field of format D to a length.
# Argument 1 is the maximum length of one value.
gates_clip_values() {
    awk -v maxv="$1" '
        {
            gi = index($0, " | GOT ")
            if (gi == 0) { print; next }
            ei = index($0, " | EXPECTED ")
            head = substr($0, 1, gi - 1)
            if (ei > 0) {
                got = substr($0, gi + 7, ei - gi - 7)
                expval = substr($0, ei + 12)
            } else {
                got = substr($0, gi + 7)
                expval = ""
            }
            if (length(got) > maxv) { got = substr(got, 1, maxv) "..." }
            if (expval != "" && length(expval) > maxv) { expval = substr(expval, 1, maxv) "..." }
            out = head " | GOT " got
            if (expval != "") { out = out " | EXPECTED " expval }
            print out
        }
    '
}

# gates_condense_spec reads the spec text of node --test. It is the fall back reader.
# It joins the continuation lines of a value that node breaks over many lines, and it
# never keeps a bare bracket as a value.
gates_condense_spec() {
    awk -v maxt="$2" -v maxv="$3" '
        function balanced(s,   i, c, d, q) {
            d = 0
            for (i = 1; i <= length(s); i = i + 1) {
                c = substr(s, i, 1)
                if (c == "[" || c == "{" || c == "(") { d = d + 1 }
                if (c == "]" || c == "}" || c == ")") { d = d - 1 }
            }
            return d <= 0
        }
        function clean(s) {
            sub(/^[ ]+/, "", s)
            sub(/,[ ]*$/, "", s)
            return s
        }
        function flush() {
            if (open == 0) { return }
            if (n <= maxt) {
                g = got
                if (g == "" || g == "[" || g == "{") { g = errline }
                if (length(g) > maxv) { g = substr(g, 1, maxv) "..." }
                e = expval
                if (e == "[" || e == "{") { e = "" }
                if (length(e) > maxv) { e = substr(e, 1, maxv) "..." }
                out = "TEST " name " | FILE " loc " | GOT " g
                if (e != "") { out = out " | EXPECTED " e }
                print out
            }
            open = 0; name = ""; loc = ""; got = ""; expval = ""; errline = ""; mode = ""
        }
        BEGIN { infail = 0; n = 0; open = 0; mode = "" }
        /failing tests:/ { infail = 1; next }
        infail == 0 { next }
        /^test at / {
            flush()
            loc = $3
            n = n + 1
            open = 1
            wantname = 1
            mode = ""
            next
        }
        open == 0 { next }
        wantname == 1 {
            wantname = 0
            name = $0
            sub(/^[^ ]+[ ]+/, "", name)
            sub(/[ ]*\([0-9.]+ms\)[ ]*$/, "", name)
            next
        }
        mode == "got" {
            got = got " " clean($0)
            if (balanced(got)) { mode = "" }
            next
        }
        mode == "exp" {
            expval = expval " " clean($0)
            if (balanced(expval)) { mode = "" }
            next
        }
        errline == "" && $0 ~ /^[ ]+[A-Za-z][A-Za-z0-9_]*.*: / && $0 !~ /^[ ]+actual: / && $0 !~ /^[ ]+expected: / {
            errline = $0
            sub(/^[ ]+/, "", errline)
            next
        }
        $0 ~ /^[ ]+actual: / {
            got = $0
            sub(/^[ ]+actual: /, "", got)
            got = clean(got)
            if (!balanced(got)) { mode = "got" }
            next
        }
        $0 ~ /^[ ]+expected: / {
            expval = $0
            sub(/^[ ]+expected: /, "", expval)
            expval = clean(expval)
            if (!balanced(expval)) { mode = "exp" }
            next
        }
        END { flush() }
    ' "$1"
}

# gates_condense_unit prints the failing tests in the format D of the build.
# Argument 1 is the spec report file. Argument 2 is the maximum count of failing tests.
# Argument 3 is the maximum length of one value.
# The reporter file beside the spec file is the first source, because it holds the
# whole value of every failed assertion. The spec text is the fall back.
gates_condense_unit() {
    gc_rep="${1%.out}.feedback"
    if [ -s "$gc_rep" ]; then
        head -"$2" "$gc_rep" | gates_clip_values "$3"
        return 0
    fi
    gates_condense_spec "$1" "$2" "$3"
}

# gates_failing_files prints the test files that hold a failing test, one for each line.
gates_failing_files() {
    gf_rep="${1%.out}.feedback"
    if [ -s "$gf_rep" ]; then
        sed -n 's/.* | FILE \([^ :]*\):.*/\1/p' "$gf_rep" | sort -u
        return 0
    fi
    awk '
        /failing tests:/ { infail = 1; next }
        infail == 1 && /^test at / {
            loc = $3
            sub(/:[0-9]+:[0-9]+$/, "", loc)
            print loc
        }
    ' "$1" | sort -u
}

# gates_tests_parse proves that every file of test/ is valid JavaScript.
# A broken test file makes stryker print no score at all, and the mutation gate then
# reports a number that no run produced. This pass names the file in one second.
gates_tests_parse() {
    gt_bad=''
    for gt_f in "$ROOT"/test/*.mjs; do
        [ -f "$gt_f" ] || continue
        if ! node --check "$gt_f" >"$LOGS_DIR/check.suite.out" 2>&1; then
            gt_bad="$gt_bad test/$(basename "$gt_f")"
            log_err "node --check refuses test/$(basename "$gt_f"):"
            head -5 "$LOGS_DIR/check.suite.out" >&2
        fi
    done
    if [ -n "$gt_bad" ]; then
        printf 'BROKEN_TEST_FILE%s\n' "$gt_bad" >"$FEEDBACK_DIR/suite.txt"
        log_err "the test suite does not parse:$gt_bad"
        return 1
    fi
    : >"$FEEDBACK_DIR/suite.txt"
    return 0
}

# gates_tests_ran prints the count of the tests that a node --test run started.
gates_tests_ran() {
    awk '/^[^0-9]*tests [0-9]+$/ { print $NF }' "$1" | tail -1
}

# gate_unit runs the unit tests. The exit code is the judge, never a grep of the text.
gate_unit() {
    gu_out="$LOGS_DIR/unit.out"
    gu_rep="$LOGS_DIR/unit.feedback"
    gu_rc=0
    : >"$gu_rep"
    ( cd "$ROOT" && node --test \
        --test-reporter=spec --test-reporter-destination=stdout \
        --test-reporter=./tools/reporter.mjs --test-reporter-destination="$gu_rep" \
        "test/**/*.test.mjs" ) >"$gu_out" 2>&1 || gu_rc=$?
    gates_strip_ansi <"$gu_out" >"$gu_out.plain"
    cp "$gu_out.plain" "$gu_out"
    gates_condense_unit "$gu_out" 100 200 >"$FEEDBACK_DIR/unit.txt"
    gu_ran=$(gates_tests_ran "$gu_out")
    case "$gu_ran" in
        '' | *[!0-9]*) gu_ran=0 ;;
    esac
    if [ "$gu_rc" -eq 0 ] && [ "$gu_ran" -eq 0 ]; then
        printf 'NO_TESTS the run started no test at all\n' >"$FEEDBACK_DIR/unit.txt"
        log_err "node --test started no test. An empty suite is never a green gate."
        return 1
    fi
    if [ "$gu_rc" -eq 0 ]; then
        log_ok "the unit gate passes. $gu_ran tests ran."
        return 0
    fi
    log_err "the unit gate fails. The condensed report is at $FEEDBACK_DIR/unit.txt"
    return 1
}

# gate_complexity runs eslint over src.
gate_complexity() {
    gc_out="$LOGS_DIR/complexity.out"
    gc_rc=0
    ( cd "$ROOT" && COMPLEXITY_MAX="$COMPLEXITY_MAX" npx eslint src ) >"$gc_out" 2>&1 || gc_rc=$?
    gates_strip_ansi <"$gc_out" >"$gc_out.plain"
    awk '
        /^\// { file = $0; next }
        / error / {
            msg = $0
            sub(/^[ ]+/, "", msg)
            print "FILE " file " | " msg
        }
    ' "$gc_out.plain" >"$FEEDBACK_DIR/complexity.txt"

    # The second rule of this gate: one export in one source file.
    gc_multi=0
    for gc_f in "$ROOT"/src/*.js; do
        [ -f "$gc_f" ] || continue
        case "$gc_f" in
            */core.js) continue ;;
        esac
        gc_n=$(grep -c '^export ' "$gc_f" || true)
        if [ "$gc_n" -gt 1 ]; then
            printf 'FILE %s | error  the file declares %s exports. One export is the limit  one-export\n' \
                "$gc_f" "$gc_n" >>"$FEEDBACK_DIR/complexity.txt"
            gc_multi=1
        fi
    done

    if [ "$gc_rc" -eq 0 ] && [ "$gc_multi" -eq 0 ]; then
        log_ok "the complexity gate passes. The maximum is $COMPLEXITY_MAX."
        return 0
    fi
    log_err "the complexity gate fails. The report is at $FEEDBACK_DIR/complexity.txt"
    return 1
}

# gates_complexity_line prints the first eslint line of one function name.
gates_complexity_line() {
    grep "'$1'" "$FEEDBACK_DIR/complexity.txt" 2>/dev/null | head -1 || true
}

# gates_core_units prints the base name of every source file that the gate must cover.
# The barrel core.js holds no logic and no test imports it, so it never appears.
gates_core_units() {
    for gu_f in "$ROOT"/src/*.js; do
        [ -f "$gu_f" ] || continue
        case "$gu_f" in
            */core.js) continue ;;
        esac
        basename "$gu_f"
    done
}

# gate_coverage runs the unit tests with the coverage report.
# The report holds a row only for a file that the test process loaded, so an empty
# suite and an untested source file both print 100.00 percent for all files. The gate
# therefore counts the rows against src/ before it reads any number.
gate_coverage() {
    gates_tests_parse || return 1
    gv_out="$LOGS_DIR/coverage.out"
    gv_rc=0
    ( cd "$ROOT" && node --test --experimental-test-coverage "test/**/*.test.mjs" ) >"$gv_out" 2>&1 || gv_rc=$?
    gates_strip_ansi <"$gv_out" >"$gv_out.plain"

    gv_ran=$(gates_tests_ran "$gv_out.plain")
    case "$gv_ran" in
        '' | *[!0-9]*) gv_ran=0 ;;
    esac
    if [ "$gv_ran" -eq 0 ]; then
        printf 'NO_TESTS the coverage run started no test at all\n' >"$FEEDBACK_DIR/coverage.txt"
        log_err "the coverage run started no test. An empty suite always reports 100 percent."
        return 1
    fi

    # A unit with no test file of its own still shows 100.00 percent, because another
    # unit imports it and the coverage counts the loaded lines. The gate therefore
    # asks for the file as well as for the row.
    gv_missing=''
    gv_notest=''
    for gv_u in $(gates_core_units); do
        grep -q "^[^A-Za-z0-9]*$gv_u  *|" "$gv_out.plain" || gv_missing="$gv_missing $gv_u"
        [ -f "$ROOT/test/${gv_u%.js}.test.mjs" ] || gv_notest="$gv_notest $gv_u"
    done
    if [ -n "$gv_missing" ]; then
        printf 'NO_ROW%s\n' "$gv_missing" >"$FEEDBACK_DIR/coverage.txt"
        log_err "the coverage report holds no row for:$gv_missing"
        log_err "no test loads that file, so the all files row cannot see it."
        return 1
    fi
    if [ -n "$gv_notest" ]; then
        printf 'NO_TEST_FILE%s\n' "$gv_notest" >"$FEEDBACK_DIR/coverage.txt"
        log_err "these units hold no test file of their own:$gv_notest"
        log_err "another unit imports them, so the coverage row alone cannot see the gap."
        return 1
    fi

    gv_line=$(grep 'all files' "$gv_out.plain" | head -1 || true)
    if [ -z "$gv_line" ]; then
        printf 'NO_COVERAGE_SUMMARY the coverage report holds no all files row\n' >"$FEEDBACK_DIR/coverage.txt"
        log_err "the coverage report holds no summary row. See $gv_out"
        return 1
    fi
    gv_lines_pct=$(printf '%s\n' "$gv_line" | awk -F'|' '{ gsub(/[^0-9.]/, "", $2); print $2 }')
    gv_branch_pct=$(printf '%s\n' "$gv_line" | awk -F'|' '{ gsub(/[^0-9.]/, "", $3); print $3 }')
    gv_funcs_pct=$(printf '%s\n' "$gv_line" | awk -F'|' '{ gsub(/[^0-9.]/, "", $4); print $4 }')

    {
        printf 'LINE %s\n' "$gv_lines_pct"
        printf 'BRANCH %s\n' "$gv_branch_pct"
        printf 'FUNCS %s\n' "$gv_funcs_pct"
        printf 'FILES %s\n' "$(gates_core_units | wc -l | tr -d ' ')"
        awk -F'|' '
            /start of coverage report/ { on = 1; next }
            /end of coverage report/   { on = 0 }
            on == 1 && NF >= 5 {
                name = $1; gsub(/^[^A-Za-z0-9_.\/-]*/, "", name); gsub(/[ ]+$/, "", name)
                un = $5; gsub(/^[ ]+/, "", un); gsub(/[ ]+$/, "", un)
                if (un != "" && name != "" && name !~ /file/) {
                    print "UNCOVERED " name " " un
                }
            }
        ' "$gv_out.plain"
    } >"$FEEDBACK_DIR/coverage.txt"

    gv_ok=1
    gates_pct_ge "$gv_lines_pct" "$COVERAGE_THRESHOLD" || gv_ok=0
    gates_pct_ge "$gv_branch_pct" "$BRANCH_THRESHOLD" || gv_ok=0
    gates_pct_ge "$gv_funcs_pct" "$FUNCS_THRESHOLD" || gv_ok=0

    if [ "$gv_rc" -ne 0 ]; then
        log_err "the coverage run fails because a unit test fails."
        return 1
    fi
    if [ "$gv_ok" -eq 1 ]; then
        log_ok "the coverage gate passes. Lines $gv_lines_pct percent. Branches $gv_branch_pct percent. Functions $gv_funcs_pct percent."
        return 0
    fi
    log_err "the coverage gate fails. Lines $gv_lines_pct of $COVERAGE_THRESHOLD. Branches $gv_branch_pct of $BRANCH_THRESHOLD. Functions $gv_funcs_pct of $FUNCS_THRESHOLD."
    return 1
}

# gates_pct_ge compares two decimal numbers. It returns 0 when the first is not less than the second.
gates_pct_ge() {
    awk -v a="$1" -v b="$2" 'BEGIN { if (a + 0 >= b + 0) { exit 0 } else { exit 1 } }'
}

# gates_stryker_break prints the break threshold of stryker.config.json.
gates_stryker_break() {
    node -e '
        const fs = require("node:fs");
        const c = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
        const t = c.thresholds || {};
        process.stdout.write(String(t.break === undefined ? "" : t.break));
    ' "$ROOT/stryker.config.json" 2>/dev/null || printf ''
}

# gate_mutation runs stryker and lists every surviving mutant.
# A stryker diff can hold more than one minus line and more than one plus line. The
# whole block goes to .build/feedback/mutants/<n>.diff, because a mutant that is
# rebuilt from the first line alone does not parse, and a mutant that does not parse
# looks like an equivalent mutant to tools/derive.mjs.
gate_mutation() {
    gates_tests_parse || return 1

    gm_break=$(gates_stryker_break)
    if [ -n "$gm_break" ] && [ "$gm_break" != "$MUTATION_THRESHOLD" ]; then
        log_err "MUTATION_THRESHOLD is $MUTATION_THRESHOLD and stryker.config.json breaks at $gm_break."
        log_err "the two numbers must agree. Change thresholds.break of stryker.config.json as well."
        printf 'THRESHOLD_DISAGREE %s %s\n' "$MUTATION_THRESHOLD" "$gm_break" >"$FEEDBACK_DIR/mutation.txt"
        return 1
    fi

    gm_out="$LOGS_DIR/mutation.out"
    gm_rc=0
    ( cd "$ROOT" && npx stryker run ) >"$gm_out" 2>&1 || gm_rc=$?
    gates_strip_ansi <"$gm_out" >"$gm_out.plain"

    rm -rf "$FEEDBACK_DIR/mutants"
    mkdir -p "$FEEDBACK_DIR/mutants"
    awk -v dir="$FEEDBACK_DIR/mutants" '
        function emit() {
            if (n == 0 || loc == "") { return }
            if (nminus == 0 || nplus == 0) { return }
            print "SURVIVOR " n " | MUTATOR " mutator " | LOC " loc " | SPAN " nminus " | MINUS " minus1 " | PLUS " plus1
            out = dir "/" n ".diff"
            for (i = 1; i <= nminus; i = i + 1) { print "-" mlines[i] > out }
            for (i = 1; i <= nplus; i = i + 1) { print "+" plines[i] > out }
            close(out)
            loc = ""; nminus = 0; nplus = 0; minus1 = ""; plus1 = ""; state = 0
        }
        /^\[Survived\]/ {
            emit()
            n = n + 1
            mutator = $2
            state = 1
            loc = ""; nminus = 0; nplus = 0; minus1 = ""; plus1 = ""
            next
        }
        state == 1 { loc = $0; sub(/^[ ]+/, "", loc); state = 2; next }
        state == 2 && /^-/ {
            t = substr($0, 2); sub(/^[ ]+/, "", t)
            nminus = nminus + 1; mlines[nminus] = t
            if (nminus == 1) { minus1 = t }
            next
        }
        state == 2 && /^\+/ { state = 3 }
        state == 3 && /^\+/ {
            t = substr($0, 2); sub(/^[ ]+/, "", t)
            nplus = nplus + 1; plines[nplus] = t
            if (nplus == 1) { plus1 = t }
            next
        }
        state == 3 { emit(); next }
        END { emit() }
    ' "$gm_out.plain" >"$FEEDBACK_DIR/mutation.txt"

    gm_score=$(grep '^All files' "$gm_out.plain" | head -1 | awk -F'|' '{ gsub(/[^0-9.]/, "", $2); print $2 }')
    if [ -z "$gm_score" ]; then
        printf 'NO_SCORE stryker printed no All files row\n' >>"$FEEDBACK_DIR/mutation.txt"
        printf 'THRESHOLD %s\n' "$MUTATION_THRESHOLD" >>"$FEEDBACK_DIR/mutation.txt"
        log_err "stryker printed no score at all. The run did not finish. See $gm_out"
        if [ "$gm_rc" -ne 0 ]; then
            log_err "stryker exited with the code $gm_rc."
        fi
        tail -20 "$gm_out.plain" >&2
        return 1
    fi
    printf 'SCORE %s\n' "$gm_score" >>"$FEEDBACK_DIR/mutation.txt"
    printf 'THRESHOLD %s\n' "$MUTATION_THRESHOLD" >>"$FEEDBACK_DIR/mutation.txt"

    if gates_pct_ge "$gm_score" "$MUTATION_THRESHOLD"; then
        if [ "$gm_rc" -ne 0 ]; then
            log_err "the score $gm_score passes the gate but stryker exited with the code $gm_rc."
            log_err "the two judgements disagree. The build treats the exit code as the truth."
            printf 'RC_DISAGREE %s %s\n' "$gm_score" "$gm_rc" >>"$FEEDBACK_DIR/mutation.txt"
            return 1
        fi
        log_ok "the mutation gate passes with a score of $gm_score percent."
        return 0
    fi
    log_err "the mutation score is $gm_score percent. The threshold is $MUTATION_THRESHOLD percent."
    log_err "the survivor list is at $FEEDBACK_DIR/mutation.txt"
    if [ "$gm_rc" -ne 0 ]; then
        log_info "stryker itself exited with the code $gm_rc."
    fi
    return 1
}

# gates_survivor_count prints the count of the surviving mutants.
# grep -c prints 0 and exits 1 on a no match, so the || branch must never print again.
gates_survivor_count() {
    gs_total=$(grep -c '^SURVIVOR ' "$FEEDBACK_DIR/mutation.txt" 2>/dev/null || true)
    case "$gs_total" in
        '' | *[!0-9]*) gs_total=0 ;;
    esac
    printf '%s\n' "$gs_total"
}

# gates_survivor_locs prints the sorted location of every surviving mutant.
gates_survivor_locs() {
    sed -n 's/^SURVIVOR .* | LOC \([^ ]*\) | .*/\1/p' "$FEEDBACK_DIR/mutation.txt" 2>/dev/null | sort -u
}

# gates_equivalent_locs prints the sorted location of every proven equivalent mutant
# of one derive report.
gates_equivalent_locs() {
    awk '/^EQUIVALENT / { print $2 }' "$1" 2>/dev/null | sort -u
}

# gates_free_port prints a TCP port that is free now.
gates_free_port() {
    python3 -c 'import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()' 2>/dev/null || printf ''
}

# gates_serve_urls prints every path that a browser asks for.
# The list comes from the import lines of the modules, never from a listing of src/.
# A module that src/core.js re-exports but that nobody wrote is absent from the
# directory, so a listing of src/ could never report the 404 that the browser sees.
gates_serve_urls() {
    {
        printf 'web/index.html\n'
        printf 'web/game.js\n'
        ( cd "$ROOT" && ls src/*.js 2>/dev/null ) || true
        ( cd "$ROOT" && sed -n "s|.*from '\.\./\([^']*\)'.*|\1|p" web/game.js 2>/dev/null ) || true
        ( cd "$ROOT" && sed -n "s|.*from '\./\([^']*\)'.*|src/\1|p" src/*.js 2>/dev/null ) || true
    } | sort -u
}

# gate_serve proves that the whole module graph answers over HTTP.
# The browser resolves the import '../src/core.js' of web/game.js against the server ROOT.
# A server rooted at web/ therefore answers 404 for the core, and the page stays black.
# Only a real request proves this. node --check cannot see it.
# The probe asks for every module of the import graph, so a new unit needs no edit.
gate_serve() {
    : >"$FEEDBACK_DIR/serve.txt"
    if ! command -v curl >/dev/null 2>&1; then
        printf 'SERVE_FAIL curl is absent\n' >"$FEEDBACK_DIR/serve.txt"
        log_err "curl is absent. The build cannot prove the served module graph."
        return 1
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        printf 'SERVE_FAIL python3 is absent\n' >"$FEEDBACK_DIR/serve.txt"
        log_err "python3 is absent. The build cannot serve the game for the probe."
        return 1
    fi

    gs_ready=0
    gs_try=0
    gs_max_try=3
    [ -n "${SERVE_CHECK_PORT:-}" ] && gs_max_try=1
    while [ "$gs_try" -lt "$gs_max_try" ] && [ "$gs_ready" -eq 0 ]; do
        gs_try=$((gs_try + 1))
        gs_port="${SERVE_CHECK_PORT:-}"
        [ -n "$gs_port" ] || gs_port=$(gates_free_port)
        if [ -z "$gs_port" ]; then
            printf 'SERVE_FAIL no free port\n' >"$FEEDBACK_DIR/serve.txt"
            log_err "the build found no free TCP port for the serve probe."
            return 1
        fi
        ( cd "$ROOT" && python3 -m http.server "$gs_port" --bind 127.0.0.1 ) >"$LOGS_DIR/serve.out" 2>&1 &
        gs_pid=$!
        gs_i=0
        # The readiness probe asks for the server root, never for a file of the game.
        # A probe on web/index.html cannot tell a dead server from a wrong server root.
        while [ "$gs_i" -lt 40 ]; do
            if curl -fsS -o /dev/null "http://127.0.0.1:$gs_port/" 2>/dev/null; then
                gs_ready=1
                break
            fi
            kill -0 "$gs_pid" 2>/dev/null || break
            sleep 0.25
            gs_i=$((gs_i + 1))
        done
        if [ "$gs_ready" -eq 0 ]; then
            if [ "$gs_try" -lt "$gs_max_try" ]; then
                log_warn "no local server answered on the port $gs_port. The build takes another port."
            else
                log_warn "no local server answered on the port $gs_port."
            fi
            kill "$gs_pid" 2>/dev/null || true
            wait "$gs_pid" 2>/dev/null || true
        fi
    done

    if [ "$gs_ready" -eq 0 ]; then
        printf 'SERVE_FAIL no server answered after 3 ports\n' >"$FEEDBACK_DIR/serve.txt"
        log_err "no local server answered. The build cannot prove the served module graph."
        log_err "the server log is at $LOGS_DIR/serve.out"
        return 1
    fi

    gs_bad=''
    gs_n=0
    for gs_u in $(gates_serve_urls); do
        gs_n=$((gs_n + 1))
        gs_code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$gs_port/$gs_u" || printf '000')
        if [ "$gs_code" != "200" ]; then
            gs_bad="$gs_bad $gs_u($gs_code)"
        fi
    done
    kill "$gs_pid" 2>/dev/null || true
    wait "$gs_pid" 2>/dev/null || true

    if [ -n "$gs_bad" ]; then
        printf 'SERVE_FAIL%s\n' "$gs_bad" >"$FEEDBACK_DIR/serve.txt"
        log_err "the served game misses:$gs_bad"
        log_err "serve the PROJECT ROOT, never the directory web. web/game.js imports ../src/core.js."
        return 1
    fi
    log_ok "$gs_n files of the served game answer 200 over HTTP on the port $gs_port."
    return 0
}
