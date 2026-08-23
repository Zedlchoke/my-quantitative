#!/usr/bin/env zsh
# Weekly forward-test ritual (NOTES section 12, Phase 1) - ETH directional MR.
# Params are FROZEN: never edit the YAML based on results.
#
#   ./scripts/weekly_forward_test.sh
#
# Steps: fetch only the disjoint bar tail (main.py download would be skipped as
# non-disjoint once the catalog overlaps), then run the 60d OOS validation and
# save the artifact. Record the printed row in NOTES.md section 12.

set -euo pipefail
cd "$(dirname "$0")/.."

CONFIG="config/research_mean_reversion_eth_directional.yaml"
OUT_DIR="results/forward_test"
STAMP="$(date -u +%Y%m%d)"
mkdir -p "$OUT_DIR"

echo "== 1/2 Fetch fresh bars (disjoint tail only) =="
.venv/bin/python - "$CONFIG" <<'PY'
import sys
import dataclasses
import pandas as pd
from config.settings import load_research_config
from data.download import download_historical_data
from data.catalog import Catalog

config_path = sys.argv[1]
settings = load_research_config(config_path)
catalog = Catalog(settings.data.catalog_path)
for symbol in settings.market.symbols:
    bars = catalog.bars(settings.market.bar_type(symbol))
    if not bars:
        print(f"{symbol}: empty catalog, run full download first")
        continue
    # Write intervals extend ~9min past the last bar close; stay clear of them.
    last = pd.Timestamp(bars[-1].ts_event, unit="ns", tz="UTC")
    start = (last + pd.Timedelta(minutes=16)).tz_convert("UTC")
    if start >= pd.Timestamp.now("UTC"):
        print(f"{symbol}: catalog already current through {last:%Y-%m-%d %H:%M} UTC")
        continue
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    market = dataclasses.replace(settings.market, symbols=[symbol])
    data = dataclasses.replace(settings.data, start=start_str, end=None)
    print(f"{symbol}: fetching from {start_str}")
    try:
        total = download_historical_data(market, data)["per_symbol"][symbol]["bars_written"]
        print(f"{total} bars total")
    except Exception as exc:  # noqa: BLE001
        if "non-disjoint" in str(exc) or "start was > now" in str(exc):
            print(f"{symbol}: already up to date ({exc.__class__.__name__})")
        else:
            raise
PY

echo ""
echo "== 2/2 60d OOS validation =="
.venv/bin/python -m research.oos_validate \
    --config "$CONFIG" \
    --holdout-days 60 \
    --output "$OUT_DIR/${STAMP}.json"

echo ""
echo "Artifact: $OUT_DIR/${STAMP}.json"
echo "Next: record the row in NOTES.md section 12 (weekly forward-test log)."
