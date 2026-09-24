#!/usr/bin/env python
"""BTC4H-BAND-GROUP S0 characterization for PROSPECTIVE-SHADOW-V1 (owner
directive 2026-09-23) — POSTHOC DISCOVERY numbers + forward-only shadow
mount spec. No claim beyond POSTHOC.

Contents:
  1. BANDRIDGE — the PSV1 Donchian arm (frozen law VERBATIM: Donchian 30/15,
     min-hold 12, max-hold 450) gated by the C3 BAND STATE (close >
     SMA200*1.03 on / < SMA200*0.97 off) with exit_buffer=1 (NO extra
     dilation — the band is already hysteretic; frozen, disclosed).
     Control: block-shuffle(30, seed 20260923) of the band gate on the same
     book (PSV1 G6 law — control out-earning => timing dead on history).
  2. SHARED-EQUITY GROUP: 4 sleeves x 25% of ONE $100k equity (C3, C4, R6,
     BANDRIDGE), joint accounting (fees/funding on the shared account).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "btc_h4_edge_search_v1" / "scripts"))
sys.dont_write_bytecode = True
SCORED_PKG = ("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1/"
              "integration/research/control/phase_strategy_v1/scored")
sys.path.insert(0, SCORED_PKG)
import es1_engine as E          # noqa: E402
from es1_reconcile_comparator import run_book_instrumented  # noqa: E402
from pipeline import config as pc, events as pe  # noqa: E402
import cells                    # noqa: E402

W = E.WARMUP
SLEEVE = 0.25


def band_state(panel, band: float) -> np.ndarray:
    return E.sig_trend_lf(panel, band)  # 0/1 hysteretic band state


def donchian_with_gate(labels_gate, close, fold_ids):
    """PSV1 Donchian machine VERBATIM, gate series supplied (band state)."""
    spec = pe.BookSpec(name="BANDRIDGE", phase="ON", trigger="donchian_breakout",
                       donch_entry=pc.DONCH_ENTRY, donch_stop=pc.DONCH_STOP,
                       exit_buffer=1,  # frozen: no extra dilation (band is hysteretic)
                       min_hold=pc.MIN_HOLD_BARS, max_hold=pc.MAX_HOLD_BARS, direction=1)
    trades, _ = run_book_instrumented(labels_gate, close, spec, fold_ids)
    d = np.zeros(len(close))
    for f, trs in trades.items():
        for tr in trs:
            e, x, r = tr["entry_bar"], tr["exit_bar"], tr["exit_reason"]
            if r == "FOLD_END":
                d[e - 1:x] = 1.0
            else:
                d[e - 1:x - 1] = 1.0
    return d, trades


def joint_simulate(decisions, panel_w, folds, tier, law, funding_df, sleeve=SLEEVE):
    """4 sleeves x `sleeve` fraction of ONE shared equity. Same instrument ->
    same bar legs; fees on |dpos| per sleeve; funding on total held notional."""
    n = len(panel_w)
    open_ = panel_w["open"].to_numpy(float)
    close = panel_w["close"].to_numpy(float)
    fee = E.COST_PER_SIDE_BPS / 1e4 * tier
    hours = pd.to_datetime(panel_w["bucket_ms"], unit="ms", utc=True).dt.hour.to_numpy()
    is_boundary = np.isin(hours, [0, 8, 16])
    fms = funding_df["ms"].to_numpy()
    frt = funding_df["rate"].to_numpy()

    def mrate(ms):
        i = np.searchsorted(fms, ms)
        for j in (i - 1, i):
            if 0 <= j < len(fms) and abs(int(fms[j]) - ms) <= 60_000:
                return float(frt[j])
        return 0.0

    K = len(decisions)
    pos = np.zeros((K, n))
    for k in range(K):
        pos[k, 1:] = decisions[k][:-1]
    for f in np.unique(folds):  # fold starts flat (sleeve-wise)
        first = np.where(folds == f)[0][0]
        if first > 0:
            pos[:, first] = 0.0
        else:
            pos[:, first] = 0.0

    equity = E.CAPITAL
    totals = {"gross": 0.0, "fees": 0.0, "funding": 0.0}
    sleeve_pnl = np.zeros(K)
    eq_path = np.empty(n)
    for t in range(n):
        if t == 0:
            eq_path[0] = equity
            continue
        gap = open_[t] / close[t - 1] - 1.0
        ib = close[t] / open_[t] - 1.0
        leg_sum = 0.0
        fee_t = 0.0
        for k in range(K):
            notional = sleeve * equity
            leg = pos[k, t - 1] * gap * notional + pos[k, t] * ib * notional
            dpos = pos[k, t] - pos[k, t - 1]
            f_t = abs(dpos) * notional * fee
            sleeve_pnl[k] += leg - f_t
            leg_sum += leg
            fee_t += f_t
        equity *= (1.0 + sum(pos[k, t - 1] for k in range(K)) * sleeve * gap)
        equity -= fee_t
        equity *= (1.0 + sum(pos[k, t] for k in range(K)) * sleeve * ib)
        pay = 0.0
        if is_boundary[t]:
            held = sum(pos[k, t] for k in range(K)) * sleeve
            if held > 0:
                rate = E.FUNDING_CONST if law == "constant" else mrate(int(panel_w["bucket_ms"].iloc[t]))
                pay = rate * held * equity
                equity -= pay
        last_of_fold = (t == n - 1) or (folds[t + 1] != folds[t])
        if last_of_fold:
            for k in range(K):
                if pos[k, t] > 0:
                    f_t = pos[k, t] * sleeve * equity * fee
                    sleeve_pnl[k] -= f_t
                    fee_t += f_t
                    pos[k, t] = 0.0
            equity -= fee_t
        totals["gross"] += leg_sum
        totals["fees"] += fee_t
        totals["funding"] += pay
        eq_path[t] = equity
    net = equity - E.CAPITAL
    dd = float(np.max(1.0 - eq_path / np.maximum.accumulate(eq_path)))
    return {"net": round(net, 2), "gross": round(totals["gross"], 2),
            "fees": round(totals["fees"], 2), "funding": round(totals["funding"], 2),
            "max_drawdown": round(dd, 4),
            "sleeve_pnl": {n_: round(float(p), 2) for n_, p in zip(["C3", "C4", "R6", "BANDRIDGE"], sleeve_pnl)}}


def main():
    h4, _ = E.load_panel()
    data = cells.load_btc_h4()
    panel_w = h4.iloc[W:].reset_index(drop=True)
    close_w = panel_w["close"].to_numpy(float)
    folds = E.fold_ids(panel_w["bucket_ms"].to_numpy())
    funding_df = E.load_funding_measured()

    band_on = band_state(panel_w, 0.03)
    gate_labels = np.where(band_on > 0, "ON", "OFF")
    ridge_dec, ridge_trades = donchian_with_gate(gate_labels, close_w, folds)

    # control: block-shuffle the gate series on the same book
    rng = np.random.default_rng(20260923)
    nb = int(np.ceil(len(gate_labels) / 30))
    perm = rng.permutation(nb)
    shuffled = np.concatenate([gate_labels[s * 30:(s + 1) * 30] for s in perm])[:len(gate_labels)]
    ctrl_dec, _ = donchian_with_gate(shuffled, close_w, folds)

    c3 = band_on
    c4 = E.sig_trend_lf(panel_w, 0.005)
    r6 = B_sig_cat = None
    import band_risk as B  # noqa: E402
    r6 = B.sig_band_overlay(panel_w, band=0.03, cat=0.15, folds=folds)

    books = {"C3": c3, "C4": c4, "R6": r6, "BANDRIDGE": ridge_dec}
    out = {"schema": "psv1shadow.bandridge_s0@1",
           "class": "POSTHOC S0 DISCOVERY — outcome-observed window; descriptive characterization for the forward shadow mount; never OOS",
           "capital_law": "WITHDRAWN shared-equity group per owner 2026-09-24; BANDRIDGE shadow sleeve carries its OWN $100,000 virtual capital in PROSPECTIVE-SHADOW-V1 (like the other sleeves)",
           "bandridge": {"law": "PSV1 Donchian 30/15 min-hold 12 max-hold 450 VERBATIM, gate = C3 band state, exit_buffer=1 (no extra dilation, frozen)",
                          "n_trades": sum(len(v) for v in ridge_trades.values())},
           "grid": {}}
    for tier in (1.0, 1.5, 2.0):
        for law in ("constant", "measured"):
            key = f"{tier}|{law}"
            ridge_r = E.simulate(ridge_dec, panel_w, folds, tier=tier, funding_law=law, funding_df=funding_df)
            ctrl_r = E.simulate(ctrl_dec, panel_w, folds, tier=tier, funding_law=law, funding_df=funding_df)
            grp = joint_simulate([books[k] for k in ("C3", "C4", "R6", "BANDRIDGE")],
                                 panel_w, folds, tier, law, funding_df)
            _ = grp  # shared-equity group WITHDRAWN by owner 2026-09-24 (no shared capital); standalone only
            out["grid"][key] = {
                "BANDRIDGE_standalone": ridge_r.as_dict(),
                "GATE_SHUFFLE_control": ctrl_r.as_dict(),
            }
    g10 = out["grid"]["1.0|measured"]
    out["bandridge_control_verdict"] = {
        "bandridge_net_measured": g10["BANDRIDGE_standalone"]["net"],
        "shuffle_control_net_measured": g10["GATE_SHUFFLE_control"]["net"],
        "timing_carries_info": g10["BANDRIDGE_standalone"]["net"] > g10["GATE_SHUFFLE_control"]["net"]}
    digest = hashlib.sha256(json.dumps(out["grid"], sort_keys=True).encode()).hexdigest()[:16]
    out["grid_digest"] = digest
    (HERE.parent / "freezes").mkdir(exist_ok=True, parents=True)
    (HERE.parent / "freezes" / "shadow_group_s0.json").write_text(
        json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out["grid"][k] for k in ("1.0|constant", "1.0|measured")}, indent=1, default=float))
    print("bandridge control:", out["bandridge_control_verdict"])


if __name__ == "__main__":
    main()
