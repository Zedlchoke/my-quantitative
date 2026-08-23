#!/usr/bin/env zsh
# Weekly forward-test ritual (NOTES section 12, Phase 1) - ETH directional MR.
# Params are FROZEN: never edit the YAML based on results.
#
#   ./scripts/weekly_forward_test.sh
#
# Steps: fetch only the disjoint bar tail via scripts/forward_lib.py (fetch
# starts at last-bar close +16min so Binance write-intervals never overlap and
# bars are silently skipped like W1), then run the 60d OOS validation and save
# the artifact. The fetch step FAILS LOUD (exit 1) when 0 new bars land while
# the exchange is >1h ahead of the catalog. An OOS FAIL is a *result*, not a
# pipeline error: the artifact is still saved and reported; record it in
# NOTES.md section 12.

set -euo pipefail
cd "$(dirname "$0")/.."

CONFIG="config/research_mean_reversion_eth_directional.yaml"
OUT_DIR="results/forward_test"
STAMP="$(date -u +%Y%m%d)"
mkdir -p "$OUT_DIR"

PY="${PYTHON_BIN:-.venv/bin/python}"
if [ ! -x "$PY" ] && [ -x "/Users/hoangminhlong/my-quantitative/.venv/bin/python" ]; then
  PY="/Users/hoangminhlong/my-quantitative/.venv/bin/python"
fi

echo "== 1/2 Fetch fresh bars (disjoint tail only) =="
"$PY" -m scripts.forward_lib "$CONFIG"

echo ""
echo "== 2/2 60d OOS validation =="
set +e
"$PY" -m research.oos_validate \
    --config "$CONFIG" \
    --holdout-days 60 \
    --output "$OUT_DIR/${STAMP}.json"
OOS_STATUS=$?
set -e
if [ "$OOS_STATUS" -ne 0 ]; then
  echo "NOTE: OOS validation returned FAIL (exit $OOS_STATUS) - this is a result,"
  echo "not a pipeline error. Artifact saved; log the row in NOTES.md section 12."
fi

echo ""
echo "Artifact: $OUT_DIR/${STAMP}.json"
echo "Next: record the row in NOTES.md section 12 (weekly forward-test log)."
