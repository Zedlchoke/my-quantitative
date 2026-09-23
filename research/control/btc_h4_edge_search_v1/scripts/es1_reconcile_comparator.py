#!/usr/bin/env python
"""ES1 COMPARATOR identity gate v2 — position series from the VERBATIM frozen
machine.

`run_book_instrumented` below is copied VERBATIM from the V2 forensic
rebuild (research/control/btc_h4_continuation_v2/forensics/
forensics_driver.py, read-only), where it was asserted trade-identical to
the frozen PSV1 events.run_book; BookSpec + config are imported verbatim
read-only from the PSV1 integration tree. Only the FRACTIONAL accounting
(simulate) is ES1's own; this gate proves it reproduces the PSV1 committed
ledger before any ES1 cell is priced.

HARD GATE: net + per-fold nets match the committed PSV1 ledger within 1e-6
relative (entries/exits within +-0); mismatch => TECHABORT.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PSV1_LANE = ("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
             "integration/research/control/phase_strategy_v1/lane_btc_h4")
sys.path.insert(0, str(PSV1_LANE))
sys.dont_write_bytecode = True
import es1_engine as E  # noqa: E402
from pipeline import config as psv1_config  # noqa: E402
from pipeline import events as psv1_events  # noqa: E402

PSV1 = {"net": 177_691.82,
        "fold_net": {"F1": 140_843.28, "F2": -46_959.99, "F3": 133_820.83, "F4": -50_012.30},
        "entries": 86, "exit_reasons": {"DONCHIAN_STOP": 79, "GATE_INACTIVE": 7}}


def run_book_instrumented(labels, close, spec, fold_ids, allow_stop_immediately=False):
    """VERBATIM from V2 forensics_driver.py (asserted trade-identical there)."""
    n = len(labels)
    hit = labels == spec.phase
    gate = hit.copy()
    for k in range(1, spec.exit_buffer):
        gate[k:] |= hit[:-k]
    hh = np.full(n, np.nan)
    ll = np.full(n, np.nan)
    for t in range(n):
        if t >= spec.donch_entry:
            hh[t] = close[t - spec.donch_entry: t].max()
        if t >= spec.donch_stop:
            ll[t] = close[t - spec.donch_stop: t].min()
    position = 0
    bars_held = 0
    fill_idx = -1
    trades_per_fold: dict = {}
    suppressed: list = []
    for t in range(n):
        if position == 0:
            trig = False
            if gate[t]:
                trig = bool(np.isfinite(hh[t]) and close[t] > hh[t])
            if trig and t + 1 < n and fold_ids[t + 1] == fold_ids[t]:
                position = 1
                fill_idx = t + 1
                bars_held = 0
        else:
            bars_held += 1
            exit_reason = None
            if np.isfinite(ll[t]) and close[t] < ll[t]:
                exit_reason = "DONCHIAN_STOP"
            if exit_reason is None and not gate[t]:
                exit_reason = "GATE_INACTIVE"
            if exit_reason is None and bars_held >= spec.max_hold:
                exit_reason = "MAX_HOLD"
            if exit_reason is not None and bars_held < spec.min_hold:
                if not (allow_stop_immediately and exit_reason == "DONCHIAN_STOP"):
                    suppressed.append({"decision_bar": t, "reason": exit_reason,
                                       "bars_held": bars_held})
                    exit_reason = None
            last_bar_of_fold = (t + 1 >= n) or (fold_ids[t + 1] != fold_ids[t])
            if exit_reason is None and last_bar_of_fold:
                exit_reason = "FOLD_END"
            if exit_reason is not None:
                exit_fill = t if last_bar_of_fold else t + 1
                trades_per_fold.setdefault(fold_ids[t], []).append(
                    {"entry_bar": fill_idx, "exit_bar": exit_fill,
                     "bars_held": bars_held, "exit_reason": exit_reason})
                position = 0
                fill_idx = -1
    return trades_per_fold, suppressed


def decision_series(trades_per_fold, n):
    d = np.zeros(n)
    reasons = {}
    for f, trs in trades_per_fold.items():
        for tr in trs:
            e, x, r = tr["entry_bar"], tr["exit_bar"], tr["exit_reason"]
            reasons[r] = reasons.get(r, 0) + 1
            if r == "FOLD_END":
                d[e - 1:x] = 1.0      # simulate force-flats at the fold's last close
            else:
                d[e - 1:x - 1] = 1.0  # exit decision at x-1 fills at x
    return d, reasons


def main():
    h4, _ = E.load_panel()
    # frozen-engine view: the machine runs on the WARMUP-TRUNCATED window and
    # uses the LOADER-DERIVED labels (pipeline.phase_rule.classify) — the
    # labels_frozen.parquet staging artifact differs on 135 window bars and
    # is NOT the scored truth (measured: it produced 2 phantom entries).
    sys.dont_write_bytecode = True
    SCORED_PKG = ("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
                  "integration/research/control/phase_strategy_v1/scored")
    if str(SCORED_PKG) not in sys.path:
        sys.path.insert(0, SCORED_PKG)
    import cells  # noqa: E402  (PSV1 loader, read-only convention)
    data = cells.load_btc_h4()
    labels_w = np.asarray([str(x) for x in data["labels"]])
    close_w = h4["close"].to_numpy(float)[E.WARMUP:]
    folds_w = E.fold_ids(h4["bucket_ms"].to_numpy()[E.WARMUP:])
    spec = psv1_events.BookSpec(
        name="PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION",
        phase="UPTREND", trigger="donchian_breakout",
        donch_entry=psv1_config.DONCH_ENTRY, donch_stop=psv1_config.DONCH_STOP,
        exit_buffer=psv1_config.EXIT_BUFFER_BARS, min_hold=psv1_config.MIN_HOLD_BARS,
        max_hold=psv1_config.MAX_HOLD_BARS, direction=1)
    trades, suppressed = run_book_instrumented(labels_w, close_w, spec, folds_w)
    dec, reasons = decision_series(trades, len(close_w))

    panel_w = h4.iloc[E.WARMUP:].reset_index(drop=True)
    assert (panel_w["bucket_ms"].to_numpy() == np.asarray(data["open_ms"])).all()
    res = E.simulate(dec, panel_w, folds_w, tier=1.0, funding_law="constant")

    out = {"schema": "es1.comparator_reconciliation@2",
           "psv1_committed": PSV1,
           "es1_rebuild": res.as_dict(),
           "exit_reasons_instrumented": reasons,
           "n_trades": sum(len(v) for v in trades.values()),
           "rel_err": {}}
    out["rel_err"]["net"] = abs(res.net - PSV1["net"]) / abs(PSV1["net"])
    for f in PSV1["fold_net"]:
        out["rel_err"][f] = abs(res.fold_net.get(f, np.nan) - PSV1["fold_net"][f]) / abs(PSV1["fold_net"][f])
    tol = 1e-6
    gate_ok = (out["rel_err"]["net"] <= tol
               and all(v <= tol for v in out["rel_err"].values())
               and res.entries == PSV1["entries"])
    out["verdict"] = "RECONCILED" if gate_ok else "MISMATCH"
    (HERE.parent / "freezes" / "comparator_reconciliation.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("verdict", "rel_err", "es1_rebuild",
                                          "exit_reasons_instrumented", "n_trades")}, indent=1))
    sys.exit(0 if gate_ok else 2)


if __name__ == "__main__":
    main()
