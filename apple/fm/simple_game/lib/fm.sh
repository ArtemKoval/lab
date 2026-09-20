#!/usr/bin/env bash
# lib/fm.sh - the interface to the Apple Foundation Model command line tool.
# This file is a library. Source it after lib/log.sh. Do not run it.
#
# Measured facts that control this file:
#   1. fm prints a markdown fence around code in most answers. The strip always runs.
#   2. fm exits 0 on broken output. The exit code is not a signal. The text is the signal.
#   3. The context window holds about 4096 tokens for the prompt and the answer together.
#   4. -g gives the same answer for the same prompt bytes. A retry must change the bytes.
#   5. Two fm processes at one time starve each other. One lock serialises every call.
#   6. node --check needs a .js or a .mjs file name. A .txt file gives ERR_UNKNOWN_FILE_EXTENSION.
#   7. A markdown fence opens a template literal, so pure English can pass node --check.
#      The backtick test always runs before node --check.

FM_CALLS=0
FM_CACHE_HITS=0
FM_LOCK_HELD=0

# fm_resolve_timeout finds a timeout program. It sets TIMEOUT_BIN, or it sets it to an empty value.
fm_resolve_timeout() {
    TIMEOUT_BIN=''
    if command -v timeout >/dev/null 2>&1; then
        TIMEOUT_BIN=$(command -v timeout)
    elif command -v gtimeout >/dev/null 2>&1; then
        TIMEOUT_BIN=$(command -v gtimeout)
    fi
}

# fm_run_timeout runs a command under a time limit.
# Argument 1 is the limit in seconds. The other arguments are the command.
fm_run_timeout() {
    fm_rt_secs="$1"
    shift
    if [ -n "${TIMEOUT_BIN:-}" ]; then
        "$TIMEOUT_BIN" "$fm_rt_secs" "$@"
        return $?
    fi
    # Fall back to a watchdog when no timeout program exists.
    # bash sends the standard input of an asynchronous command to /dev/null.
    # The file descriptor 9 keeps the real standard input of the caller.
    exec 9<&0
    "$@" <&9 &
    fm_rt_pid=$!
    exec 9<&-
    (
        fm_rt_waited=0
        while [ "$fm_rt_waited" -lt "$fm_rt_secs" ]; do
            sleep 1
            kill -0 "$fm_rt_pid" 2>/dev/null || exit 0
            fm_rt_waited=$((fm_rt_waited + 1))
        done
        kill -TERM "$fm_rt_pid" 2>/dev/null || true
    ) &
    fm_rt_watchdog=$!
    fm_rt_rc=0
    wait "$fm_rt_pid" || fm_rt_rc=$?
    kill "$fm_rt_watchdog" 2>/dev/null || true
    wait "$fm_rt_watchdog" 2>/dev/null || true
    return "$fm_rt_rc"
}

# fm_lock takes the exclusive build lock on the model.
# mkdir is atomic on every file system that this build uses. flock is absent on macOS.
fm_lock() {
    fm_lk_waited=0
    while ! mkdir "$FM_LOCK_DIR" 2>/dev/null; do
        if [ -f "$FM_LOCK_DIR/pid" ]; then
            fm_lk_owner=$(cat "$FM_LOCK_DIR/pid" 2>/dev/null || printf '')
            if [ -n "$fm_lk_owner" ] && ! kill -0 "$fm_lk_owner" 2>/dev/null; then
                log_warn "the fm lock of process $fm_lk_owner is stale. The build removes it."
                rm -rf "$FM_LOCK_DIR"
                continue
            fi
        fi
        sleep 1
        fm_lk_waited=$((fm_lk_waited + 1))
        if [ "$fm_lk_waited" -ge "$FM_LOCK_WAIT" ]; then
            die "the fm lock at $FM_LOCK_DIR is busy after $FM_LOCK_WAIT seconds. Another build runs now."
        fi
    done
    printf '%s\n' "$$" >"$FM_LOCK_DIR/pid"
    FM_LOCK_HELD=1
}

fm_unlock() {
    if [ "$FM_LOCK_HELD" = "1" ]; then
        rm -rf "$FM_LOCK_DIR"
        FM_LOCK_HELD=0
    fi
}

# fm_preflight proves that the model answers before the build spends time.
fm_preflight() {
    [ -x "$FM_BIN" ] || die "the model tool $FM_BIN is absent or is not executable. Set FM_BIN."
    fm_pf_out=$("$FM_BIN" available 2>&1 || true)
    case "$fm_pf_out" in
        *"System model available"*) : ;;
        *) die "$FM_BIN available printed '$fm_pf_out'. The build needs 'System model available'." ;;
    esac
    fm_pf_tok=$("$FM_BIN" count-tokens -q 'hello' 2>/dev/null || printf '')
    case "$fm_pf_tok" in
        '' | *[!0-9]*) die "$FM_BIN count-tokens -q hello printed '$fm_pf_tok'. The build needs an integer." ;;
    esac
    log_ok "the model answers. count-tokens of the word hello is $fm_pf_tok."
}

# fm_count_tokens prints the token count of a file.
# Argument 1 is the file. It prints an integer, or it returns 1.
fm_count_tokens() {
    fm_ct_file="$1"
    fm_lock
    fm_ct_out=$(fm_run_timeout "$FM_TIMEOUT" "$FM_BIN" count-tokens -q <"$fm_ct_file" 2>/dev/null || printf '')
    fm_unlock
    case "$fm_ct_out" in
        '' | *[!0-9]*) return 1 ;;
    esac
    printf '%s\n' "$fm_ct_out"
}

# fm_strip_fences removes every markdown fence line.
# Argument 1 is the input file. Argument 2 is the output file.
fm_strip_fences() {
    awk '/^[[:space:]]*```/ { next } { print }' "$1" >"$2"
}

# fm_has_backtick returns 0 when the file holds a backtick.
fm_has_backtick() {
    grep -q '`' "$1"
}

# fm_is_prose returns 0 when the file holds no code character at all.
fm_is_prose() {
    ! grep -q '[{};=()]' "$1"
}

# fm_escalation_text prints the extra strictness line of one attempt.
# Argument 1 is the attempt number.
fm_escalation_text() {
    case "$1" in
        1) printf '' ;;
        2) printf '\nOutput raw source only. Write no markdown fence. Write no backtick. Write no prose.\n' ;;
        *) printf '\nAttempt 3. Your last answer was not valid source.\nThe first characters of your answer must be the word export.\nWrite no markdown fence. Write no backtick. Write no comment. Write no prose.\n' ;;
    esac
}

# fm_raw makes one model call.
# Argument 1 is the system prompt file. Argument 2 is the user prompt file.
# Argument 3 is the raw output file. Argument 4 is the label of the transcript.
fm_raw() {
    fm_rw_sys="$1"
    fm_rw_user="$2"
    fm_rw_out="$3"
    fm_rw_label="$4"
    fm_rw_err="${fm_rw_out}.stderr"
    fm_rw_tr="$FM_TRANSCRIPT_DIR/${fm_rw_label}.json"

    fm_lock
    fm_rw_rc=0
    fm_run_timeout "$FM_TIMEOUT" "$FM_BIN" respond --no-stream -g \
        -i "$(cat "$fm_rw_sys")" \
        --save-transcript "$fm_rw_tr" \
        <"$fm_rw_user" >"$fm_rw_out" 2>"$fm_rw_err" || fm_rw_rc=$?
    fm_unlock
    FM_CALLS=$((FM_CALLS + 1))

    if [ "$fm_rw_rc" -eq 124 ] || [ "$fm_rw_rc" -eq 143 ]; then
        log_warn "the model call $fm_rw_label passed the limit of $FM_TIMEOUT seconds."
        return 1
    fi
    if grep -q 'exceeded the model' "$fm_rw_err" 2>/dev/null; then
        log_err "the model reports a context overflow for $fm_rw_label."
        cat "$fm_rw_err" >&2
        return 2
    fi
    return 0
}

# fm_cache_key prints the key of a prompt pair.
fm_cache_key() {
    cat "$1" "$2" | shasum -a 256 | awk '{ print $1 }'
}

# fm_generate makes one validated model answer.
#   Argument 1 is the system prompt file.
#   Argument 2 is the user prompt file.
#   Argument 3 is the output file.
#   Argument 4 is the name of a validator function. It is optional.
# The validator takes a candidate file and returns 0 when the candidate is good.
# fm_generate returns 0 on success and 1 on failure.
fm_generate() {
    fm_gn_sys="$1"
    fm_gn_user="$2"
    fm_gn_out="$3"
    fm_gn_validator="${4:-}"
    fm_gn_label=$(basename "$fm_gn_out" | tr -c 'A-Za-z0-9._-' '_')

    [ -f "$fm_gn_sys" ] || die "the system prompt file $fm_gn_sys is absent."
    [ -f "$fm_gn_user" ] || die "the user prompt file $fm_gn_user is absent."

    # The cache keeps the accepted answer of a prompt pair. -g makes this safe.
    fm_gn_key=$(fm_cache_key "$fm_gn_sys" "$fm_gn_user")
    fm_gn_cache="$FM_CACHE_DIR/$fm_gn_key.out"
    if [ -s "$fm_gn_cache" ]; then
        # The validator installs the answer in src/ or in test/. A cache hit must run it
        # too, or the destination file stays absent after a --from run or a --only run.
        if [ -z "$fm_gn_validator" ] || "$fm_gn_validator" "$fm_gn_cache"; then
            cp "$fm_gn_cache" "$fm_gn_out"
            FM_CACHE_HITS=$((FM_CACHE_HITS + 1))
            log_ok "cache hit for $fm_gn_label. The build makes no model call."
            return 0
        fi
        log_warn "the cached answer of $fm_gn_label fails the validator now. The build calls the model again."
        rm -f "$fm_gn_cache"
    fi

    # The token gate runs before the call. A prompt over budget can never answer.
    fm_gn_probe="$FM_WORK_DIR/${fm_gn_label}.prompt"
    cat "$fm_gn_sys" "$fm_gn_user" >"$fm_gn_probe"
    fm_gn_tokens=$(fm_count_tokens "$fm_gn_probe" || printf '')
    if [ -z "$fm_gn_tokens" ]; then
        log_warn "count-tokens gave no number for $fm_gn_label. The build goes on without the token gate."
    else
        printf '%s %s\n' "$fm_gn_tokens" "$fm_gn_label" >>"$BUILD_DIR/logs/tokens.txt"
        if [ "$fm_gn_tokens" -gt "$FM_PROMPT_BUDGET" ]; then
            log_err "the prompt of $fm_gn_label holds $fm_gn_tokens tokens. The budget is $FM_PROMPT_BUDGET."
            printf 'PROMPT_TOO_LARGE %s %s\n' "$fm_gn_label" "$fm_gn_tokens" >>"$FEEDBACK_DIR/prompt.txt"
            return 1
        fi
        log_info "the prompt of $fm_gn_label holds $fm_gn_tokens tokens."
    fi

    fm_gn_attempt=1
    fm_gn_empties=0
    while [ "$fm_gn_attempt" -le "$FM_RETRIES" ]; do
        fm_gn_try="$FM_WORK_DIR/${fm_gn_label}.a${fm_gn_attempt}.user"
        cp "$fm_gn_user" "$fm_gn_try"
        fm_escalation_text "$fm_gn_attempt" >>"$fm_gn_try"
        if [ "$fm_gn_empties" -gt 0 ]; then
            printf '\n' >>"$fm_gn_try"
            printf '%s\n' "$(printf '.%.0s' $(seq 1 "$fm_gn_empties"))" >>"$fm_gn_try"
        fi

        fm_gn_raw="$FM_RAW_DIR/${fm_gn_label}.a${fm_gn_attempt}.raw"
        log_info "the model call $fm_gn_label runs. Attempt $fm_gn_attempt of $FM_RETRIES."
        fm_gn_rc=0
        fm_raw "$fm_gn_sys" "$fm_gn_try" "$fm_gn_raw" "${fm_gn_label}.a${fm_gn_attempt}" || fm_gn_rc=$?

        if [ "$fm_gn_rc" -eq 2 ]; then
            log_err "the context overflow of $fm_gn_label cannot improve with a retry."
            return 1
        fi

        # Test a: the size. An answer under FM_MIN_BYTES is empty.
        fm_gn_size=0
        if [ -f "$fm_gn_raw" ]; then
            fm_gn_size=$(wc -c <"$fm_gn_raw" | tr -d ' ')
        fi
        if [ "$fm_gn_size" -le "$FM_MIN_BYTES" ]; then
            fm_gn_empties=$((fm_gn_empties + 1))
            log_warn "the answer of $fm_gn_label holds $fm_gn_size bytes. Empty count is $fm_gn_empties."
            if [ "$fm_gn_empties" -le 2 ]; then
                continue
            fi
            fm_gn_attempt=$((fm_gn_attempt + 1))
            continue
        fi

        # Test b: the fence strip. It always runs.
        fm_gn_cand="$FM_WORK_DIR/${fm_gn_label}.a${fm_gn_attempt}.cand"
        fm_strip_fences "$fm_gn_raw" "$fm_gn_cand"

        # Test c: the backtick test. It runs before any syntax test.
        if fm_has_backtick "$fm_gn_cand"; then
            log_warn "the answer of $fm_gn_label still holds a backtick after the strip."
            fm_gn_attempt=$((fm_gn_attempt + 1))
            continue
        fi

        # Test d: the prose test.
        if fm_is_prose "$fm_gn_cand"; then
            log_warn "the answer of $fm_gn_label holds prose and no code."
            fm_gn_attempt=$((fm_gn_attempt + 1))
            continue
        fi

        # Test e: the validator of the caller.
        if [ -n "$fm_gn_validator" ]; then
            if ! "$fm_gn_validator" "$fm_gn_cand"; then
                log_warn "the answer of $fm_gn_label failed the validator of the step."
                fm_gn_attempt=$((fm_gn_attempt + 1))
                continue
            fi
        fi

        cp "$fm_gn_cand" "$fm_gn_out"
        cp "$fm_gn_cand" "$fm_gn_cache"
        log_ok "the answer of $fm_gn_label is good after attempt $fm_gn_attempt."
        return 0
    done

    log_err "the model gave no valid answer for $fm_gn_label after $FM_RETRIES attempts."
    log_err "the last raw answer is at $FM_RAW_DIR/${fm_gn_label}.a$((fm_gn_attempt - 1)).raw"
    return 1
}

# fm_normalise cuts one function out of a model answer.
#   Argument 1 is the candidate file. Argument 2 is the function name.
#   Argument 3 is the output file.
# It drops every fence line, it cuts the text before the function, it cuts the text
# after the balanced closing brace, and it adds the word export when the word is absent.
fm_normalise() {
    fm_nm_in="$1"
    fm_nm_fn="$2"
    fm_nm_out="$3"
    if [ -x "$ROOT/tools/normalise.sh" ]; then
        "$ROOT/tools/normalise.sh" "$fm_nm_in" "$fm_nm_fn" >"$fm_nm_out"
        return $?
    fi
    awk -v fn="$fm_nm_fn" '
        /^[[:space:]]*```/ { next }
        started == 0 {
            if (index($0, "function " fn "(") > 0) {
                started = 1
                line = $0
                sub(/^.*function[[:space:]]+/, "function ", line)
                if (index($0, "export") > 0) { line = "export " line }
                else { line = "export " line }
                print line
                depth = gsub(/\{/, "{", line) - gsub(/\}/, "}", line)
                if (depth <= 0 && index(line, "{") > 0) { exit }
                next
            }
            next
        }
        started == 1 {
            print $0
            o = gsub(/\{/, "{", $0)
            c = gsub(/\}/, "}", $0)
            depth = depth + o - c
            if (depth <= 0) { exit }
        }
    ' "$fm_nm_in" >"$fm_nm_out"
    [ -s "$fm_nm_out" ]
}
