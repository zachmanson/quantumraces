#!/usr/bin/env bash
# Reproduces every v2 configuration (handoff section 4). Each run is resumable; logs go to results_v2/logs/.
set -euo pipefail
cd "$(dirname "$0")/.."
run() {
    local name=$1; shift
    echo "=== $name  $(date '+%F %T')"
    python run.py "$@" --out-dir results_v2 --processes 6 > "results_v2/logs/$name.log" 2>&1
    echo "    done $(date '+%F %T')"
}
for regime in full-header nonce-only; do
    run "c1_$regime" --regime "$regime" -c 1 --n-q 200
    run "c2_$regime" --regime "$regime" -c 2 --n-q 45
    run "c4_$regime" --regime "$regime" -c 4 --n-q 25
done
run c3_full-header --regime full-header -c 3 --n-q 35
run c3_nonce-only  --regime nonce-only  -c 3 --n-q 35 --stop-after 2
