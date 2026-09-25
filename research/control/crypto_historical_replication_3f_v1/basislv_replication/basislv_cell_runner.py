"""One BASISLV window-fold replication scored cell in the v14 context.

Args: --fold --window-start --window-end --arm-id --out

Loads the staged replication world (basis parquets from basis_convert.py,
full-coverage catalog_live_crypto_b20 bars through the OPEN->CLOSE remap,
scan_2026 funding AS-IS, b20-report ticks), binds BasislvWindowFoldPlugin to
the fold window, and runs the FROZEN ``run_strategy`` baseline cell end to
end.  Prints one JSON line (last line) with the scored metrics plus the
per-cell refusal census for honest cell rows.

NOT runnable by the implementer lane directly: scored cells are launched
ONLY by replication_scored.py under the machine-wide heavy lock, self-gated
on basislv_replication/A7_PRELAUNCH.json verdict AUTHORIZED.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CD = HERE.parent
V14_ROOT = CD / "recovered/v14_root"
sys.path.insert(0, str(V14_ROOT))
sys.path.insert(0, str(HERE))

from gated_plugin import (  # noqa: E402
    REASON_INSUFFICIENT_ELIGIBLE_REFUSAL,
    BasislvWindowFoldPlugin,
)
from replication_data import (  # noqa: E402
    CATALOG,
    FEED_SYMBOLS,
    load_basis_world,
    load_execution_bars_catalog,
    load_settlements_scan,
    load_tick_sizes,
)
from research.adapter_v10.runner import run_strategy  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--fold", required=True)
ap.add_argument("--window-start", required=True)
ap.add_argument("--window-end", required=True)
ap.add_argument("--arm-id", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

basis, _basis_report = load_basis_world()
bars = load_execution_bars_catalog(FEED_SYMBOLS, catalog=CATALOG)
settlements, _settlements_report = load_settlements_scan()
ticks = load_tick_sizes()

plugin = BasislvWindowFoldPlugin(
    arm_id=a.arm_id,
    basis_by_symbol=dict(basis),
    bars_by_symbol=dict(bars),
    settlements_by_symbol=dict(settlements),
    tick_sizes=dict(ticks),
    window_start_iso=a.window_start,
    window_end_iso=a.window_end,
)
plugin.bind_window((a.window_start, a.window_end))

payload = run_strategy(plugin, out_dir=a.out, write_artifact_file=True)
m = dict(payload.get("portfolio_metrics") or {})
books = list(payload.get("books") or [])
refusal_stamps = [
    int(b["decision_ns"])
    for b in books
    if (b.get("diagnostics") or {}).get("insufficient_eligible_refusal")
]
force_flat_stamps = [
    int(b["decision_ns"])
    for b in books
    if (b.get("diagnostics") or {}).get("fold_terminal_force_flat")
]
eligible = [
    int((b.get("diagnostics") or {}).get("n_eligible", -1))
    for b in books
    if (b.get("diagnostics") or {}).get("n_eligible") is not None
]
print(
    json.dumps(
        {
            "fold": a.fold,
            "arm_id": a.arm_id,
            "window": [a.window_start, a.window_end],
            "net_return_sum": m.get("net_return_sum"),
            "expectancy_per_day": m.get("expectancy_per_day"),
            "position_pf": m.get("position_pf"),
            "max_drawdown": m.get("max_drawdown"),
            "n_positions": m.get("n_positions"),
            "n_days_with_records": m.get("n_days_with_records"),
            "price_pnl_sum": m.get("price_pnl_sum"),
            "funding_sum": m.get("funding_sum"),
            "cost_charged_sum": m.get("cost_charged_sum"),
            "n_books": len(books),
            "n_insufficient_eligible_refusals": len(refusal_stamps),
            "n_fold_terminal_force_flats": len(force_flat_stamps),
            "eligible_min": min(eligible) if eligible else None,
            "eligible_max": max(eligible) if eligible else None,
        }
    )
)
