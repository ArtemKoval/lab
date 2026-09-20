#!/usr/bin/env bash
# lib/log.sh - the log functions of the build harness.
# This file is a library. Source it. Do not run it.
# Style: bash 3.2 compatible. No associative array. No case conversion operator.

# The colour names hold an empty value until log_init runs.
# A message before log_init must never stop the build with an unbound variable.
C_RESET=''
C_BOLD=''
C_DIM=''
C_RED=''
C_GREEN=''
C_YELLOW=''
C_BLUE=''
C_CYAN=''
LOG_FILE=''

# log_init makes the log file and turns colour on or off.
# Argument 1 is the path of the log file.
log_init() {
    LOG_FILE="$1"
    LOG_DIR_OF_FILE=$(dirname "$LOG_FILE")
    mkdir -p "$LOG_DIR_OF_FILE"
    : >>"$LOG_FILE"

    if [ -t 1 ] && [ "${NO_COLOR:-}" = "" ] && [ "${TERM:-dumb}" != "dumb" ]; then
        C_RESET=$(printf '\033[0m')
        C_BOLD=$(printf '\033[1m')
        C_DIM=$(printf '\033[2m')
        C_RED=$(printf '\033[31m')
        C_GREEN=$(printf '\033[32m')
        C_YELLOW=$(printf '\033[33m')
        C_BLUE=$(printf '\033[34m')
        C_CYAN=$(printf '\033[36m')
    else
        C_RESET=''
        C_BOLD=''
        C_DIM=''
        C_RED=''
        C_GREEN=''
        C_YELLOW=''
        C_BLUE=''
        C_CYAN=''
    fi
}

# log_stamp prints the time.
log_stamp() {
    date '+%H:%M:%S'
}

# log_write puts one plain line in the log file.
log_write() {
    if [ -n "${LOG_FILE:-}" ]; then
        printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >>"$LOG_FILE" 2>/dev/null || true
    fi
}

# log_step prints the banner of a build step.
log_step() {
    printf '\n%s%s==============================================================%s\n' \
        "$C_BOLD" "$C_BLUE" "$C_RESET"
    printf '%s%s== %s%s\n' "$C_BOLD" "$C_BLUE" "$*" "$C_RESET"
    printf '%s%s==============================================================%s\n' \
        "$C_BOLD" "$C_BLUE" "$C_RESET"
    log_write "STEP $*"
}

log_info() {
    printf '%s[%s]%s %s\n' "$C_DIM" "$(log_stamp)" "$C_RESET" "$*"
    log_write "INFO $*"
}

log_ok() {
    printf '%s[%s]%s %sOK%s   %s\n' "$C_DIM" "$(log_stamp)" "$C_RESET" "$C_GREEN" "$C_RESET" "$*"
    log_write "OK $*"
}

log_warn() {
    printf '%s[%s]%s %sWARN%s %s\n' "$C_DIM" "$(log_stamp)" "$C_RESET" "$C_YELLOW" "$C_RESET" "$*" >&2
    log_write "WARN $*"
}

log_err() {
    printf '%s[%s]%s %sERR%s  %s\n' "$C_DIM" "$(log_stamp)" "$C_RESET" "$C_RED" "$C_RESET" "$*" >&2
    log_write "ERR $*"
}

log_cmd() {
    printf '%s     $ %s%s\n' "$C_CYAN" "$*" "$C_RESET"
    log_write "CMD $*"
}

# die prints an error and stops the build with code 1.
die() {
    log_err "$*"
    exit 1
}
