#!/usr/bin/env bash

# Do not enable set -e: failed commands still need a final clock reading.
set -u

clock() {
    local boundary="$1"
    local start="${IMPLEMENTER_STARTED_AT:-}"
    local now elapsed remaining phase

    case "$start" in
        ''|*[!0-9]*)
            printf 'CLOCK_ERROR: missing or invalid IMPLEMENTER_STARTED_AT\n' >&2
            return 2
            ;;
    esac
    # Bound arithmetic input to avoid signed integer overflow.
    if (( ${#start} > 18 )); then
        printf 'CLOCK_ERROR: invalid IMPLEMENTER_STARTED_AT\n' >&2
        return 2
    fi

    if ! now=$(date +%s); then
        printf 'CLOCK_ERROR: unable to read the current time\n' >&2
        return 2
    fi
    elapsed=$((now - 10#$start))
    remaining=$((1200 - elapsed))

    if (( elapsed < 0 )); then
        printf 'CLOCK_ERROR: launch timestamp is in the future\n' >&2
        return 2
    elif (( elapsed >= 1200 )); then
        phase=EXPIRED
    elif (( elapsed >= 1100 )); then
        phase=CHECKPOINT
    elif (( elapsed >= 1000 )); then
        phase=WRAP_UP
    else
        phase=WORK
    fi

    printf '\n[TASK_CLOCK boundary=%s elapsed=%ss remaining=%ss phase=%s]\n' \
        "$boundary" "$elapsed" "$remaining" "$phase" >&2
}

if (( $# == 0 )); then
    clock CHECK
    exit "$?"
fi

clock BEFORE || exit 2

# Execute arguments directly, without eval or changes to the working directory.
"$@"
command_status=$?

clock AFTER
clock_status=$?

if (( command_status != 0 )); then
    exit "$command_status"
fi

exit "$clock_status"
