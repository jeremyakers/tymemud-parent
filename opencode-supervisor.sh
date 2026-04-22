#!/usr/bin/env bash

LOGFILE="${OPENCODE_LOGFILE:-$HOME/opencode-supervisor.log}"
RESTART_DELAY="${OPENCODE_RESTART_DELAY:-5}"

mkdir -p "$(dirname "$LOGFILE")"

log() {
    printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOGFILE"
}

log "===== supervisor started ====="

while true; do
    log "Running: opencode upgrade"
    opencode upgrade 2>&1 | tee -a "$LOGFILE"
    log "Upgrade exited with status $?"

    log "Starting: opencode --mdns"
    opencode --mdns 2>&1 | tee -a "$LOGFILE"
    rc=$?

    log "opencode exited with status $rc"

    if [ "$rc" -eq 0 ]; then
        log "Normal exit detected; not restarting"
        exit 0
    fi

    log "Non-zero exit detected; restarting in ${RESTART_DELAY}s"
    sleep "$RESTART_DELAY"
done
