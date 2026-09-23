"""FORENSICS_P1 driver — BTC-H4-CONTINUATION-V2 (plan §1).

Forensic per-trade anatomy of PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION.

Identity law: the rebuild calls the FROZEN PSV1 scored engine functions
VERBATIM (cells.load_btc_h4, books.l2_run_book, books.l2_fills_from_book,
accounting.run_accounting, accounting.btc_8h_boundary_mask) imported from the
PSV1 integration worktree at terminal anchor af52f358. run_scored.run_scored()
itself is NOT called. PSV1 trees are READ-ONLY here (imports only).

Heavy lock: machine-wide via governance.heavy_lock; bounded retry (configurable,
default initial + 3 retries, 100 s apart); release in finally. Resume mode
(A1-authorized): after the bounded attempts fail, `--light-fallback` runs the
rebuild WITHOUT the lock under the plan §8 LIGHT-JOB EXEMPTION (<5 min CPU /
<2 GB) with mandatory resource measurement (wall/CPU/peak RSS via
resource.getrusage) disclosed in data_receipt.json as
lock_mode=LIGHT_EXEMPTION_DISCLOSED; exceeding the ceilings aborts the run
(STOPPED_HEAVY_WITHOUT_LOCK).

All writes are confined to research/control/btc_h4_continuation_v2/forensics/
in the cycle worktree. Determinism: no RNG, sorted iteration, fixed float
repr; a re-run must reproduce byte-identical outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/Users/hoangminhlong/my-quantitative")
V1_INT = REPO / ".worktrees/phase-strategy-v1/integration"
V1_SCORED = V1_INT / "research/control/phase_strategy_v1/scored"
V1_RUNTIME = V1_INT / "research/control/phase_strategy_v1/runtime/scored"
V1_LANE = REPO / ".worktrees/phase-strategy-v1/lane-btc-h4/research/control/phase_strategy_v1/lane_btc_h4"
WT = REPO / ".worktrees/btc-h4-continuation-v2/integration"
OUT = WT / "research/control/btc_h4_continuation_v2/forensics"

sys.path.insert(0, str(REPO / "research"))   # governance.heavy_lock
sys.path.insert(0, str(V1_SCORED))           # frozen PSV1 scored engine

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

TIERS = [1.0, 1.5, 2.0]
TOL_REL = 1e-6
FOLD_NAMES = {0: "F1", 1: "F2", 2: "F3", 3: "F4"}
K_FAILED_BREAKOUT = 6  # a-priori DESCRIPTIVE constant (plan §1.2: min-hold 12 halved)

# Plan §8 LIGHT-JOB EXEMPTION ceilings (binding when running WITHOUT the lock)
LIGHT_MAX_CPU_S = 300.0            # 5 minutes CPU
LIGHT_MAX_PEAK_RSS_BYTES = 2 * 1024 ** 3  # 2 GB


class LightExemptionExceeded(RuntimeError):
    """Resource measurement exceeded the §8 light-job ceilings — the run must
    be treated as heavy and must not stand without the lock."""


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _rel_err(measured: float, target: float) -> float:
    if target == 0.0:
        return 0.0 if measured == 0.0 else float("inf")
    return abs(measured - target) / abs(target)


def _q(measured, target):
    return {"measured": measured, "target": target, "rel_err": _rel_err(measured, target)}


def _iso(ms: float) -> str:
    return pd.Timestamp(int(ms), unit="ms", tz="UTC").isoformat()


def _pct(a, p):
    a = np.asarray(a, dtype=float)
    if a.size == 0:
        return None
    return float(np.percentile(a, p))


# ---------------------------------------------------------------------------
# instrumented copy of the frozen lane machine (events.run_book) — VERBATIM
# logic with a suppression recorder; asserted trade-identical to the frozen
# run before its counts are used anywhere.
# ---------------------------------------------------------------------------
def run_book_instrumented(labels, close, spec, fold_ids, allow_stop_immediately=False):
    from pipeline import config as cfg2  # PSV1 lane config (read-only)
    n = len(labels)
    # gate_active — verbatim
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
    suppressed: list[dict] = []
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
                    exit_reason = None  # churn law: min-dwell suppresses exit triggers
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
    _ = cfg2
    return trades_per_fold, suppressed


def book_trades_sorted(book: dict):
    recs = [(f, tr) for f, trs in book["_trade_records"].items() for tr in trs]
    recs.sort(key=lambda x: x[1]["entry_bar"])
    return recs


def _usage_cpu() -> float:
    ru = resource.getrusage(resource.RUSAGE_SELF)
    return float(ru.ru_utime + ru.ru_stime)


def run_all(lock_mode: str) -> int:
    import cells  # PSV1 scored cells (frozen)
    import books  # PSV1 scored books (frozen)
    import accounting as acc  # PSV1 scored accounting (frozen)

    u0_wall = time.monotonic()
    u0_cpu = _usage_cpu()

    # ---------------- rebuild (identity law: frozen functions, verbatim) ----
    cell = cells.load_btc_h4()
    book = books.l2_run_book(cell)
    fills = books.l2_fills_from_book(book)
    funding_mask = acc.btc_8h_boundary_mask(cell["open_ms"])

    open_, high, low, close = cell["open"], cell["high"], cell["low"], cell["close"]
    n = len(close)
    labels = np.asarray(cell["labels"])
    fold_ids = cell["fold_ids"]
    open_ms = cell["open_ms"]

    # ---------------- tier accounting ---------------------------------------
    tier_res = {}
    tier_trades = {}
    for tier in TIERS:
        res = acc.run_accounting(open_, close, fills, fold_ids, cell["bps"],
                                 tier=tier, funding_mask=funding_mask,
                                 funding_rate=cell["funding_rate"])
        tier_res[tier] = res
        tier_trades[tier] = res["trade_records"]

    # ---------------- reconciliation targets (frozen PSV1 artifacts) --------
    ledger = json.loads((V1_RUNTIME / "scored_ledger.json").read_text())
    tfiles = {f"{t}x": json.loads((V1_RUNTIME / "tiers" / f"tier_{t}x.json").read_text())
              for t in TIERS}
    key = "BTC_H4::PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION"
    arm_t = ledger["arms"][key]

    recon = {"schema": "btc_h4_continuation_v2_forensics_reconciliation@1",
             "cycle_id": "BTC-H4-CONTINUATION-V2",
             "targets_sources": [
                 str(V1_RUNTIME / "scored_ledger.json"),
                 str(V1_RUNTIME / "tiers/tier_1.0x.json"),
                 str(V1_RUNTIME / "tiers/tier_1.5x.json"),
                 str(V1_RUNTIME / "tiers/tier_2.0x.json"),
             ],
             "target_schema": ledger.get("schema"),
             "arm_key": key,
             "tolerance_rel": TOL_REL,
             "tiers": {}, "verdict": "PASS"}
    for tier in TIERS:
        tk = f"{tier}x"
        tgt = arm_t["tiers"][tk]
        meas = tier_res[tier]
        checks: dict = {}
        checks["entries"] = _q(book["n_entries"], arm_t["entries"])
        checks["exits"] = _q(book["n_exits"], arm_t["exits"])
        checks["trades"] = _q(meas["trades"], tgt["trades"])
        for reason, tv in arm_t["exit_reasons"].items():
            checks[f"exit_reasons::{reason}"] = _q(book["exit_reason_counts"].get(reason, 0), tv)
        for extra_reason, tv in book["exit_reason_counts"].items():
            if extra_reason not in arm_t["exit_reasons"]:
                checks[f"exit_reasons::{extra_reason}"] = _q(tv, 0)
        for fv in ("0", "1", "2", "3"):
            checks[f"per_fold_net::{fv}"] = _q(meas["per_fold_net"][int(fv)],
                                               tgt["per_fold_net"][fv])
        for tot in ("net", "gross", "fees", "funding"):
            checks[f"totals::{tot}"] = _q(meas[tot], tgt[tot])
        # cross-check: ledger vs tier file must agree (both are frozen targets)
        tf_arm = tfiles[tk]["arms"][key]["tiers"][tk]
        tier_file_agrees = all(
            tf_arm[f] == tgt[f] for f in ("net", "gross", "fees", "funding", "trades")
        ) and tf_arm["per_fold_net"] == tgt["per_fold_net"]
        tier_ok = all(
            (c["rel_err"] <= TOL_REL) if isinstance(c, dict) else False
            for c in checks.values())
        recon["tiers"][tk] = {"checks": checks,
                              "tier_file_matches_ledger": bool(tier_file_agrees),
                              "verdict": "PASS" if (tier_ok and tier_file_agrees) else "FAIL"}
        if not (tier_ok and tier_file_agrees):
            recon["verdict"] = "FAIL"
    recon["max_rel_err"] = max(
        c["rel_err"] for t in recon["tiers"].values() for c in t["checks"].values())
    (OUT / "reconciliation.json").write_text(json.dumps(recon, indent=1) + "\n")
    if recon["verdict"] != "PASS":
        print(json.dumps({"reconciliation": "FAIL", "max_rel_err": recon["max_rel_err"]}))
        return 2

    # ---------------- per-trade ledger @1.0x --------------------------------
    meas1 = tier_res[1.0]
    acct_trades = meas1["trade_records"]
    bt = book_trades_sorted(book)
    assert len(bt) == len(acct_trades) == 86, (len(bt), len(acct_trades))
    decision_bars = [e["decision_bar"] for e in book["_entry_records"]]
    decision_bars.sort()

    rows = []
    for (f, tr), at in zip(bt, acct_trades):
        assert tr["entry_bar"] == at["entry_bar"] and tr["exit_bar"] == at["exit_bar"], (tr, at)
        ebar, xbar = int(tr["entry_bar"]), int(tr["exit_bar"])
        dbar = ebar - 1
        assert decision_bars and dbar == decision_bars.pop(0)
        at_close = tr["exit_reason"] in ("FOLD_END", "SERIES_END_OPEN")
        entry_price = float(open_[ebar])
        exit_price = float(close[xbar]) if at_close else float(open_[xbar])
        hold_bars = int(at["hold_bars"])
        # MFE/MAE over the holding window (bars whose high/low the position
        # was exposed to): open-class exit -> [entry, exit); close-class exit
        # -> [entry, exit] (position holds through the exit bar's close).
        w_end = xbar + 1 if at_close else xbar
        win = slice(ebar, max(w_end, ebar + 1))
        mfe_ret = float(np.max(high[win] / entry_price - 1.0))
        mae_ret = float(np.min(low[win] / entry_price - 1.0))
        eq0 = float(at["eq_at_entry"])
        # ---------------- PIT covariates AS OF THE ENTRY DECISION BAR -------
        # bars with close time <= decision time only == indices 0..dbar of the
        # truncated scored series the engine itself sees.
        logret20 = np.diff(np.log(close[dbar - 20: dbar + 1]))  # 20 close-to-close log returns
        rv20 = float(np.std(logret20, ddof=1))
        slope20 = float(np.log(close[dbar] / close[dbar - 20]))
        w200 = close[max(0, dbar - 199): dbar + 1]
        dd200 = float(close[dbar] / np.max(w200) - 1.0)
        dwin = close[dbar - 30: dbar]  # exact prior-30-close window hh[dbar] uses
        donch_rank = float(np.sum(dwin < close[dbar]) / len(dwin))
        fwd = {}
        for h in (6, 12, 24):
            j = ebar + h
            fwd[h] = float(close[j] / close[ebar] - 1.0) if j < n else None
        rows.append({
            "trade_id": len(rows),
            "entry_bar": ebar, "exit_bar": xbar, "decision_bar": dbar,
            "entry_bar_ts": _iso(open_ms[ebar]), "exit_bar_ts": _iso(open_ms[xbar]),
            "entry_price": entry_price, "exit_price": exit_price,
            "exit_reason": tr["exit_reason"],
            "hold_bars": hold_bars, "bars_held_decision_space": int(tr["bars_held"]),
            "gross": float(at["gross"]), "fees": float(at["fees"]),
            "funding": float(at["funding"]), "net": float(at["net"]),
            "fold_id": int(f), "fold": FOLD_NAMES[int(f)],
            "mfe_ret": mfe_ret, "mae_ret": mae_ret,
            "mfe_usd": eq0 * mfe_ret, "mae_usd": eq0 * mae_ret,
            "phase_label_at_entry": str(labels[dbar]),
            "realized_vol_20": rv20, "trend_slope_20": slope20,
            "dd_from_high_200": dd200, "donchian_rank": donch_rank,
            "dd200_window_bars": int(len(w200)),
            "btc_fwd_ret_6": fwd[6], "btc_fwd_ret_12": fwd[12], "btc_fwd_ret_24": fwd[24],
        })

    cols = ["trade_id", "fold_id", "fold", "entry_bar", "decision_bar", "exit_bar",
            "entry_bar_ts", "exit_bar_ts", "entry_price", "exit_price", "exit_reason",
            "hold_bars", "bars_held_decision_space", "gross", "fees", "funding", "net",
            "mfe_ret", "mae_ret", "mfe_usd", "mae_usd", "phase_label_at_entry",
            "realized_vol_20", "trend_slope_20", "dd_from_high_200", "donchian_rank",
            "dd200_window_bars", "btc_fwd_ret_6", "btc_fwd_ret_12", "btc_fwd_ret_24"]
    df = pd.DataFrame(rows)[cols]
    df.to_csv(OUT / "trade_ledger_btc_h4.csv", index=False)

    sidecar = {
        "schema": "btc_h4_continuation_v2_trade_ledger_tiers@1",
        "note": ("per-trade rows at 1.5x/2.0x; SAME fills/trades, costs re-charged by "
                 "accounting.run_accounting at each tier (equity path differs, so "
                 "per-trade fees/funding are NOT a constant multiple of the 1.0x rows)"),
        "csv_columns_documented": {
            "mfe_ret/mae_ret": ("max/min over the holding window of high/low vs entry fill price "
                                "(entry=fill bar open; window = entry..exit-1 for open-class exits, "
                                "entry..exit inclusive for close-class FOLD_END/SERIES_END exits)"),
            "mfe_usd/mae_usd": "mfe_ret/mae_ret x equity at entry (fraction 1.0); descriptive",
            "hold_bars": "accounting convention: exit fill bar - entry fill bar",
            "bars_held_decision_space": "lane machine bars_held (decision bars in position)",
            "realized_vol_20": "std(ddof=1) of the 20 log closes-to-close returns ending at the decision bar",
            "trend_slope_20": "log(close[decision]/close[decision-20])",
            "dd_from_high_200": "close[decision]/max(close over up to prior 200 bars incl. decision) - 1",
            "donchian_rank": "share of the prior-30-close Donchian entry window strictly below the decision close (1.0 = fresh 30-bar high)",
            "phase_label_at_entry": "frozen PIT phase label at the decision bar",
            "btc_fwd_ret_6/12/24": "POST-HOC-DESCRIPTIVE ONLY: close[fills+6/12/24]/close[fill]-1",
            "PIT_law": "covariates use bars with close time <= decision time only (indices 0..decision_bar of the engine's truncated series)",
        },
        "tiers": {f"{t}x": [{"trade_id": r["trade_id"],
                             "entry_bar": r["entry_bar"], "exit_bar": r["exit_bar"],
                             "gross": tr["gross"], "fees": tr["fees"],
                             "funding": tr["funding"], "net": tr["net"]}
                            for r, tr in zip(rows, tier_trades[t])] for t in TIERS},
    }
    (OUT / "trade_ledger_tiers_sidecar.json").write_text(json.dumps(sidecar, indent=1) + "\n")

    # ---------------- fold comparison ---------------------------------------
    def fold_metrics(sub: pd.DataFrame) -> dict:
        nets = sub["net"].to_numpy()
        wins = nets[nets > 0]
        losses = nets[nets < 0]
        stops = sub[sub["exit_reason"] == "DONCHIAN_STOP"]
        failed = stops[stops["bars_held_decision_space"] <= K_FAILED_BREAKOUT]
        return {
            "n_trades": int(len(sub)),
            "hit_rate": float((nets > 0).mean()) if len(nets) else None,
            "avg_win": float(wins.mean()) if wins.size else None,
            "avg_loss": float(losses.mean()) if losses.size else None,
            "gross": float(sub["gross"].sum()),
            "fees": float(sub["fees"].sum()),
            "funding": float(sub["funding"].sum()),
            "funding_drag_share": float(abs(sub["funding"].sum()) / abs(sub["gross"].sum()))
            if float(sub["gross"].sum()) != 0 else None,
            "median_hold_bars": float(sub["hold_bars"].median()) if len(sub) else None,
            "mean_hold_bars": float(sub["hold_bars"].mean()) if len(sub) else None,
            "donchian_stop_fraction": float(len(stops) / len(sub)) if len(sub) else None,
            "donchian_stop_n": int(len(stops)),
            "k_failed_breakout_bars": K_FAILED_BREAKOUT,
            "failed_breakout_n": int(len(failed)),
            "failed_breakout_rate_of_trades": float(len(failed) / len(sub)) if len(sub) else None,
            "failed_breakout_rate_of_stops": float(len(failed) / len(stops)) if len(stops) else None,
            "mfe_ret": {"median": _pct(sub["mfe_ret"], 50), "p25": _pct(sub["mfe_ret"], 25),
                        "p75": _pct(sub["mfe_ret"], 75)},
            "mae_ret": {"median": _pct(sub["mae_ret"], 50), "p25": _pct(sub["mae_ret"], 25),
                        "p75": _pct(sub["mae_ret"], 75)},
            "mfe_usd": {"median": _pct(sub["mfe_usd"], 50), "p25": _pct(sub["mfe_usd"], 25),
                        "p75": _pct(sub["mfe_usd"], 75)},
            "mae_usd": {"median": _pct(sub["mae_usd"], 50), "p25": _pct(sub["mae_usd"], 25),
                        "p75": _pct(sub["mae_usd"], 75)},
            "pit_covariates_median_at_entry": {
                "realized_vol_20": float(sub["realized_vol_20"].median()),
                "trend_slope_20": float(sub["trend_slope_20"].median()),
                "dd_from_high_200": float(sub["dd_from_high_200"].median()),
                "donchian_rank": float(sub["donchian_rank"].median()),
            },
            "exit_reason_counts": {k: int(v) for k, v in
                                   sub["exit_reason"].value_counts().sort_index().items()},
        }

    fc = {"schema": "btc_h4_continuation_v2_fold_comparison@1",
          "k_failed_breakout_note": ("a-priori DESCRIPTIVE constant k=6 H4 bars "
                                     "(12-bar min-hold halved; plan §1.2) — NOT tuned"),
          "folds": {FOLD_NAMES[fid]: fold_metrics(df[df["fold_id"] == fid])
                    for fid in (0, 1, 2, 3)},
          "all_folds": fold_metrics(df)}
    fc["folds"]["F2F4_combined"] = fold_metrics(df[df["fold_id"].isin((1, 3))])
    fc["folds"]["F1F3_combined"] = fold_metrics(df[df["fold_id"].isin((0, 2))])

    def _fold_btc_ret(fid: int) -> float:
        idx = np.where(fold_ids == fid)[0]
        return float(close[idx[-1]] / close[idx[0]] - 1.0)

    fc["descriptive_context"] = {
        "label": "POST-HOC-DESCRIPTIVE ONLY — market context for the fold split; "
                 "never a trade input, never a proposal input",
        "btc_close_to_close_return_per_fold": {
            FOLD_NAMES[f]: _fold_btc_ret(f) for f in (0, 1, 2, 3)},
    }
    (OUT / "fold_comparison.json").write_text(json.dumps(fc, indent=1) + "\n")

    # ---------------- min-hold law audit ------------------------------------
    from pipeline import events as ev2, config as cfg2  # PSV1 lane machines (read-only)
    spec = ev2.BookSpec(
        name="PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION",
        phase="UPTREND", trigger="donchian_breakout",
        donch_entry=cfg2.DONCH_ENTRY, donch_stop=cfg2.DONCH_STOP,
        exit_buffer=cfg2.EXIT_BUFFER_BARS, min_hold=cfg2.MIN_HOLD_BARS,
        max_hold=cfg2.MAX_HOLD_BARS, direction=1)

    instr_trades, suppressed = run_book_instrumented(
        labels, close, spec, fold_ids, allow_stop_immediately=False)
    assert instr_trades == book["_trade_records"], \
        "instrumented machine diverged from the frozen book — audit invalid"
    cf_trades, _ = run_book_instrumented(
        labels, close, spec, fold_ids, allow_stop_immediately=True)

    # delay attribution per measured trade
    delays = []
    stop_suppressions = [s for s in suppressed if s["reason"] == "DONCHIAN_STOP"]
    gate_suppressions = [s for s in suppressed if s["reason"] == "GATE_INACTIVE"]
    for f, tr in bt:
        exit_decision = tr["exit_bar"] if tr["exit_reason"] in ("FOLD_END", "SERIES_END_OPEN") \
            else tr["exit_bar"] - 1
        mine = [s for s in stop_suppressions
                if tr["entry_bar"] <= s["decision_bar"] <= exit_decision]
        if mine:
            first = min(s["decision_bar"] for s in mine)
            delays.append({"fold": FOLD_NAMES[int(f)],
                           "entry_bar": tr["entry_bar"], "exit_bar": tr["exit_bar"],
                           "measured_exit_reason": tr["exit_reason"],
                           "n_suppressed_stop_triggers": len(mine),
                           "first_suppressed_stop_decision_bar": first,
                           "bars_held_at_first_suppression":
                               min(s["bars_held"] for s in mine),
                           "delay_bars_to_actual_exit": exit_decision - first})
    delay_vals = [d["delay_bars_to_actual_exit"] for d in delays]
    hist = {str(k): int(sum(1 for v in delay_vals if v == k))
            for k in sorted(set(delay_vals))}

    # descriptive immediate-stop counterfactual (NEVER a proposal input)
    cf_fills = books.l2_fills_from_book({"_trade_records": cf_trades})
    cf_res = acc.run_accounting(open_, close, cf_fills, fold_ids, cell["bps"],
                                tier=1.0, funding_mask=funding_mask,
                                funding_rate=cell["funding_rate"])
    cf_n = sum(len(v) for v in cf_trades.values())
    audit = {
        "schema": "btc_h4_continuation_v2_min_hold_audit@1",
        "min_hold_law_citation": {
            "file": str(V1_LANE / "pipeline/events.py"),
            "lines": "99-100 (inside run_book; suppresses DONCHIAN_STOP/GATE_INACTIVE/"
                     "MAX_HOLD while bars_held < MIN_HOLD_BARS; FOLD_END force-flat is "
                     "checked after and is NOT suppressed)",
            "code": ("if exit_reason is not None and bars_held < spec.min_hold:\n"
                     "    exit_reason = None  # churn law: min-dwell suppresses exit triggers"),
            "constant_source": {"file": str(V1_LANE / "pipeline/config.py"),
                                "line": "MIN_HOLD_BARS = 12"},
        },
        "instrumented_machine_identity_check": "PASSED (trade-identical to books.l2_run_book output)",
        "min_hold_bars": cfg2.MIN_HOLD_BARS,
        "total_suppressed_exit_triggers": len(suppressed),
        "suppressed_DONCHIAN_STOP_triggers": len(stop_suppressions),
        "suppressed_GATE_INACTIVE_triggers": len(gate_suppressions),
        "suppressed_trigger_bars_held_distribution": {
            str(k): int(sum(1 for s in suppressed if s["bars_held"] == k))
            for k in sorted({s["bars_held"] for s in suppressed})},
        "suppressed_triggers_detail": suppressed,
        "measured_trades_with_delayed_stop": len(delays),
        "delay_bars_distribution": hist,
        "delay_detail": delays,
        "counterfactual": {
            "label": "POST-HOC-DESCRIPTIVE-ONLY — reported, never a proposal input, never optimized",
            "definition": ("DONCHIAN_STOP allowed to fire immediately (min-hold not applied to "
                           "the stop trigger); GATE_INACTIVE/MAX_HOLD min-hold kept; everything "
                           "else identical; full-path re-run through the SAME fills adapter and "
                           "accounting.run_accounting at 1.0x"),
            "n_trades_measured": meas1["trades"],
            "n_trades_counterfactual": cf_n,
            "net_measured_1x": meas1["net"],
            "net_counterfactual_1x": cf_res["net"],
            "net_delta_cf_minus_measured_1x": cf_res["net"] - meas1["net"],
            "per_fold_net_measured_1x": {FOLD_NAMES[k]: v for k, v in meas1["per_fold_net"].items()},
            "per_fold_net_counterfactual_1x": {FOLD_NAMES[k]: v for k, v in cf_res["per_fold_net"].items()},
            "per_fold_delta_cf_minus_measured_1x": {
                FOLD_NAMES[k]: cf_res["per_fold_net"][k] - meas1["per_fold_net"][k]
                for k in sorted(meas1["per_fold_net"])},
        },
    }
    (OUT / "min_hold_audit.json").write_text(json.dumps(audit, indent=1) + "\n")

    # ---------------- data receipt ------------------------------------------
    full = pd.read_parquet(cells.L2_STAGE / "scored_h4.parquet")
    manifest_sha = _sha256_file(cells.BASE / "lane_btc_h4" / "data" / "manifest.json")
    pinned = "3f1a668798c82fbfe7311fadf65a300a583043cdbeba226164bd28c81885b66d"
    assert manifest_sha == pinned, manifest_sha
    ingest = json.loads((V1_RUNTIME / "ingest_verification.json").read_text())
    assert ingest["verdict"] == "PASS" and ingest["verified"] == 284, ingest
    fb = {}
    for fid in (0, 1, 2, 3):
        idx = np.where(fold_ids == fid)[0]
        fb[FOLD_NAMES[fid]] = {"start_idx": int(idx[0]), "end_idx": int(idx[-1]),
                               "n_bars": int(idx[-1] - idx[0] + 1),
                               "start_utc": _iso(open_ms[idx[0]]),
                               "end_utc": _iso(open_ms[idx[-1]])}
    # light-job exemption accounting (mandatory measurement + disclosure when
    # running WITHOUT the heavy lock; plan §8). ru_maxrss is bytes on darwin.
    cpu_s = _usage_cpu() - u0_cpu
    wall_s = time.monotonic() - u0_wall
    peak_rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if lock_mode == "LIGHT_EXEMPTION_DISCLOSED" and (
            cpu_s > LIGHT_MAX_CPU_S or peak_rss > LIGHT_MAX_PEAK_RSS_BYTES):
        raise LightExemptionExceeded(
            f"cpu_s={cpu_s:.1f} (limit {LIGHT_MAX_CPU_S}), "
            f"peak_rss_bytes={peak_rss} (limit {LIGHT_MAX_PEAK_RSS_BYTES}) — "
            "treat as HEAVY: stop and wait for the lock")
    receipt = {
        "schema": "btc_h4_continuation_v2_data_receipt@1",
        "lock_mode": lock_mode,
        "resource_measurement": {
            "method": "resource.getrusage(RUSAGE_SELF) around run_all()",
            "wall_s": round(wall_s, 3),
            "cpu_s": round(cpu_s, 3),
            "peak_rss_bytes": peak_rss,
            "peak_rss_note": "ru_maxrss high-water mark; bytes on darwin",
            "light_exemption_limits": {"max_cpu_s": LIGHT_MAX_CPU_S,
                                       "max_peak_rss_bytes": LIGHT_MAX_PEAK_RSS_BYTES},
            "within_light_exemption": lock_mode != "LIGHT_EXEMPTION_DISCLOSED"
            or (cpu_s <= LIGHT_MAX_CPU_S and peak_rss <= LIGHT_MAX_PEAK_RSS_BYTES),
        },
        "manifest_path": str(cells.BASE / "lane_btc_h4" / "data" / "manifest.json"),
        "manifest_sha256": manifest_sha,
        "manifest_sha256_matches_plan_pin": True,
        "staged_parquet": {
            "path": str(cells.L2_STAGE / "scored_h4.parquet"),
            "sha256": _sha256_file(cells.L2_STAGE / "scored_h4.parquet"),
            "rows_full_panel": int(len(full)),
            "rows_scored_post_warmup_truncation": int(n),
            "warmup_bars_truncated": int(len(full) - n),
        },
        "first_bucket_open_utc": _iso(open_ms[0]),
        "last_bucket_open_utc": _iso(open_ms[-1]),
        "fold_edges_utc": ["2021-05-01", "2023-01-01", "2025-01-01"],
        "fold_boundaries_as_applied": fb,
        "ingest_note": ("byte integrity rests on the PRIMARY PSV1 scored run's ingest "
                        "verification of the SAME staged bytes: 284/284 manifest entries "
                        "re-downloaded and re-hashed, verdict PASS "
                        "(phase_strategy_v1/runtime/scored/ingest_verification.json). "
                        "FORENSICS_P1 performed NO re-download (read-only reuse)."),
        "ingest_verification_targets": {"verified": ingest["verified"],
                                        "verdict": ingest["verdict"]},
    }
    (OUT / "data_receipt.json").write_text(json.dumps(receipt, indent=1) + "\n")

    print(json.dumps({
        "reconciliation": recon["verdict"],
        "trades": meas1["trades"],
        "per_fold_net_1x": {FOLD_NAMES[k]: v for k, v in meas1["per_fold_net"].items()},
        "net_1x": meas1["net"],
        "minhold_delayed_trades": len(delays),
        "cf_net_delta_1x": cf_res["net"] - meas1["net"],
    }))
    return 0


def _append_yield_attempt() -> None:
    """Read-only snapshot of the foreign lock holder BEFORE renewed attempts
    (no interaction with it); appended to the existing BLOCKED report."""
    p = OUT / "BLOCKED_lock_report.json"
    try:
        rep = json.loads(p.read_text())
    except FileNotFoundError:
        rep = {"schema": "btc_h4_continuation_v2_forensics_blocked@1",
               "attempts": 0, "detail": "", "lock_inspect": None}
    rep.setdefault("yield_attempts", []).append({
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "note": ("resume (A1): read-only snapshot of the foreign holder's identity "
                 "(pid + cycle) before renewed acquisition attempts; no interaction"),
        "lock_inspect": json.loads(_lock_inspect_json()),
    })
    p.write_text(json.dumps(rep, indent=1) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock-attempts", type=int, default=4)
    ap.add_argument("--lock-retry-sleep", type=float, default=100.0)
    ap.add_argument("--light-fallback", action="store_true",
                    help="if the lock is still busy after the bounded attempts, "
                         "run WITHOUT it under the plan §8 light-job exemption "
                         "(<5 min CPU / <2 GB), with mandatory measurement+disclosure")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    _append_yield_attempt()
    from governance import heavy_lock
    handle = None
    for attempt in range(args.lock_attempts):
        try:
            handle = heavy_lock.acquire(
                cycle_id="BTC-H4-CONTINUATION-V2",
                role="FORENSICS_P1",
                worktree=str(WT),
                command=["research/control/btc_h4_continuation_v2/forensics/forensics_driver.py"],
                expected_artifacts=[
                    str(OUT / "trade_ledger_btc_h4.csv"),
                    str(OUT / "trade_ledger_tiers_sidecar.json"),
                    str(OUT / "reconciliation.json"),
                    str(OUT / "fold_comparison.json"),
                    str(OUT / "min_hold_audit.json"),
                    str(OUT / "data_receipt.json"),
                ],
            )
            break
        except heavy_lock.LockBusyError as exc:
            if attempt == args.lock_attempts - 1:
                if args.light_fallback:
                    print(json.dumps({"lock": "BUSY_AFTER_BOUNDED_ATTEMPTS",
                                      "mode": "LIGHT_EXEMPTION_DISCLOSED",
                                      "detail": str(exc)}))
                    return run_all("LIGHT_EXEMPTION_DISCLOSED")
                blocked = {
                    "schema": "btc_h4_continuation_v2_forensics_blocked@1",
                    "verdict": "BLOCKED_NOT_RUN_RESOURCE_CONFLICT",
                    "attempts": args.lock_attempts,
                    "detail": str(exc),
                    "lock_inspect": json.loads(_lock_inspect_json()),
                }
                (OUT / "BLOCKED_lock_report.json").write_text(json.dumps(blocked, indent=1) + "\n")
                print(json.dumps({"verdict": blocked["verdict"]}))
                return 3
            time.sleep(args.lock_retry_sleep)
    try:
        rc = run_all("HEAVY_LOCK")
        handle.release(status="FINISHED", note="forensics rebuild + reconciliation complete")
        return rc
    except LightExemptionExceeded as exc:
        handle.release(status="TECHABORT", note=f"light-exemption exceeded: {exc}")
        print(json.dumps({"verdict": "STOPPED_HEAVY_WITHOUT_LOCK", "detail": str(exc)}))
        return 4
    except Exception as exc:  # noqa: BLE001 — fail loud, release lock cleanly
        handle.release(status="FAILED", note=f"{type(exc).__name__}: {exc}")
        raise


def _lock_inspect_json() -> str:
    import subprocess
    out = subprocess.run(
        [str(REPO / ".venv/bin/python"), str(REPO / "research/researchctl.py"),
         "locks", "inspect"],
        capture_output=True, text=True, check=True)
    return out.stdout


if __name__ == "__main__":
    raise SystemExit(main())
