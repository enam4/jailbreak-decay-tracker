#!/usr/bin/env bash
# rerun the tracker: ./run.sh  (writes results/<today>.jsonl, results/<today>-summary.json, appends results/history.csv)
cd "$(dirname "$0")"; [ -f .venv/bin/activate ] && source .venv/bin/activate
export THREADS=${THREADS:-4}
python tracker.py --samples ${SAMPLES:-4} "$@"
