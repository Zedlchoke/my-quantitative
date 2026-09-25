"""Scored-phase engine — ERP1-TRACKA-COHORT-1 (tracka1-scored lane, GO-2).

AUTHORITY: freeze/GO1_freeze_artifact.json (+ erratum E1) and plan 9.1-9.4,
10, 4.2. GO-2 record: GO_RECORDED.json (ECONOMIC-ROBUSTNESS-PROGRAM-V1/
tracka_cohort1/GO2_gate/). This module computes PnL ONLY when a scored run
invokes it after the exact-arm dry-run evidence is committed.

FILL LAW (ported byte-faithful from the ancestry engine via the cycle's
parametrized scripts/engine.py run_strategy, driven here on the H1
SignalPlane):
  - signal on CLOSED H1 bar t; fill at bar t+1 OPEN at the OPPOSITE quote
    with cost = the fill bar's OWN measured spread x k:
      buy  at b_o + k*s_o ;  sell at a_o - k*s_o
    exit crossings likewise at the exit bar's own bar-state spread
    (s_open at an open-price signal exit; s_close at the day-close bar);
    day-close force-flat exits at the day-close bar close spread.
  - no fills on/after the 19:00 bar (SignalPlane.fill_ok); every position
    force-flat at the 19:00-bar close (20:00 UTC); weekend flat; PnL in
    the pair's own pips (pip_mult from the pair config).
  - k in {1.0, 1.5, 2.0}.

ARMS (plan 4.2 + freeze arm registry; digests read FROM THE FREEZE, never
recomputed): R-ANCHOR, R-ORIG, R-NEIGH (0.25/0.75 on anchor semantics),
CAUSAL-PLACEBO (rebuilt recipe ADJUDICATION #2: seed 20260925, frozen
per-pair r, uniform-random hours 7..17, day-parity direction, hold 7
bars), INVERTED (anchor sign-flipped at entry, exits identical -> the
negated target), BASELINE-SET composite (FLAT + day-session SHORT_ALWAYS
+ LONG_ALWAYS through the identical executor).

NO FREEZE INPUT IS MODIFIED. Frozen files (tracka_lib.py, falsifier_run.py,
build_signal_plane.py — sha-pinned in the freeze code_freeze) are imported,
never edited.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

sys_scripts = Path(__file__).resolve().parent
import sys  # noqa: E402

sys.path.insert(0, str(sys_scripts))

import engine as E  # noqa: E402  (cycle parametrized engine — ancestry port)
import tracka_lib as T  # noqa: E402
from falsifier_run import (  # noqa: E402
    DERIVED, FOLD_TABLE, HOLDOUT_END, HOLDOUT_START, LANE, PAIRS,
    WARMUP_TRADED_DAYS, ts_of,
)

FREEZE_PATH = LANE / "freeze" / "GO1_freeze_artifact.json"
K_BOOKS = (1.0, 1.5, 2.0)
K_BASE = 1.0
K_STRESS_REPORT = 1.5
K_STRESS = 2.0
PLACEBO_SEED = 20260925
SEAM_LIMB3_MIN_N = 20
PF_GATE = 1.20
FOLD_GATE = 4  # of 6
TOP_SHARE_GATE = 0.50
RT_GATE = 100
MONTHS_GATE = 6
POWER_GATE_RT = 236

BETA_MATCHED = {"AUDUSD": "SHORT_ALWAYS", "USDCAD": "LONG_ALWAYS"}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canon_sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def load_freeze() -> dict:
    return json.loads(FREEZE_PATH.read_text())


def registry_digests(freeze: dict) -> dict:
    """(pair, arm) -> arm_config_digest from the FROZEN arm registry."""
    out = {}
    for e in freeze["arm_registry"]:
        if e["mechanism"] == "M1" and e.get("arm_config_digest"):
            out[(e["pair"], e["arm"])] = e["arm_config_digest"]
    return out


def load_plane(pair: str, include_holdout: bool):
    from pair_config import load_pair_config

    cfg = load_pair_config(pair)
    df = pd.read_parquet(DERIVED / f"bars1h_ANC_{pair}.parquet")
    if not include_holdout:
        df = df[df["ts"] < pd.Timestamp(f"{HOLDOUT_START}T00:00:00Z")]
    else:
        df = df[df["ts"] < pd.Timestamp(f"{HOLDOUT_END}T00:00:00Z")
                + pd.Timedelta(days=1)]
    return T.SignalPlane(df, pip_mult=1.0 / cfg.pip)


# ------------------------------------------------------------- targets ----

def placebo_target_full_panel(p: T.SignalPlane, r: float, hold_bars: int,
                              seed: int = PLACEBO_SEED) -> dict:
    """CAUSAL-PLACEBO target per the FROZEN rebuild recipe (ADJUDICATION
    #2), one rng stream over the FULL panel's traded days ascending. The
    dev-prefix draws are identical to the falsifier's dev-panel build
    (same day order, same consumption) — verified in the dry-run against
    the frozen counts."""
    days = p.traded_days()
    day_index = {int(d): j for j, d in enumerate(days)}
    bars_by_day = {}
    for i in np.nonzero(~p.skip)[0]:
        bars_by_day.setdefault(int(p.day[i]), []).append(int(i))
    rng = np.random.default_rng(seed)
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    n_selected = n_placed = 0
    for d in days:
        u = float(rng.random())
        if u >= r:
            continue
        n_selected += 1
        h0 = int(rng.integers(7, 18))
        direction = 1 if day_index[int(d)] % 2 == 0 else -1
        bars = bars_by_day.get(int(d), [])
        cand = [i for i in bars if p.hour[i] == h0]
        if not cand:
            continue
        i0 = cand[0]
        i1 = min(i0 + hold_bars, bars[-1])
        tgt[i0:i1 + 1] = direction
        n_placed += 1
    return {"tgt": tgt, "days_selected": n_selected,
            "entries_placed": n_placed, "hold_bars": hold_bars, "r": r}


def build_targets(p: T.SignalPlane) -> dict:
    """All arm target arrays on one panel (full-panel build reproduces the
    dev-panel falsifier arrays on the dev prefix — causal laws)."""
    tgt_anchor = T.f_rangeexp_anchor_shift(p)
    tgt_orig = T.f_rangeexp_orig(p)
    tgt_neigh = T.f_rangeexp_anchor_shift(p, lo_q=0.25, hi_q=0.75)
    sess = ((~p.skip) & (p.hour >= 7) & (p.hour <= 18)).astype(np.int8)
    return {
        "R-ANCHOR": tgt_anchor,
        "R-ORIG": tgt_orig,
        "R-NEIGH": tgt_neigh,
        "INVERTED": (-tgt_anchor).astype(np.int8),
        "SHORT_ALWAYS": (-sess).astype(np.int8),
        "LONG_ALWAYS": sess,
        "FLAT": np.zeros(len(p.ts), dtype=np.int8),
    }


def dev_warmup_end_idx(p: T.SignalPlane) -> int:
    days = p.traded_days()
    return int(np.nonzero(p.day == days[WARMUP_TRADED_DAYS - 1])[0][-1])


# ----------------------------------------------------------- execution ----

def run_cell(p: T.SignalPlane, target, k: float, warmup_end_idx: int):
    """The ancestry fill/PnL path (scripts/engine.run_strategy — the
    cycle's parametrized port) on the H1 SignalPlane. PnL in pips."""
    return E.run_strategy(p, target, k, warmup_end_idx=warmup_end_idx)


def _bar_index_map(p: T.SignalPlane) -> dict:
    return {int(ts): i for i, ts in enumerate(p.ts)}


def cost_pips_of(p: T.SignalPlane, trip: dict, k: float) -> float:
    """trip_cost_pips needs bar indices; the PnL engine's trades carry
    timestamps. H1 bar timestamps are unique, so map ts -> index."""
    if "entry_bar" in trip:
        return T.trip_cost_pips(p, trip, k=k)
    m = getattr(p, "_ts_idx", None)
    if m is None:
        m = _bar_index_map(p)
        p._ts_idx = m
    t2 = dict(trip)
    t2["entry_bar"] = m[int(trip["entry_ts"])]
    t2["exit_bar"] = m[int(trip["exit_ts"])]
    if "exit_kind" not in t2:
        t2["exit_kind"] = "day_close" if p.is_day_close[t2["exit_bar"]] \
            else "signal"
    return T.trip_cost_pips(p, t2, k=k)


def decompose(p: T.SignalPlane, trades: list, k: float) -> dict:
    """net (engine book), gross (= net + round-trip cost: the zero-cost
    fills book), total cost. One spread crossing per side, k x fill-bar
    own spread, exactly as the engine charges it."""
    pnls = np.array([t["pips"] for t in trades], dtype=float) \
        if trades else np.zeros(0)
    costs = np.array([cost_pips_of(p, t, k) for t in trades], dtype=float) \
        if trades else np.zeros(0)
    net = float(pnls.sum())
    cost = float(costs.sum())
    return {
        "net_pips": round(net, 2),
        "gross_pips": round(net + cost, 2),
        "cost_pips": round(cost, 2),
        "n_trades": int(len(pnls)),
    }


def fold_of_ts(ts: int, fold_table=FOLD_TABLE):
    for fid, s, e in fold_table:
        if ts_of(s) <= ts <= ts_of(e, end=True):
            return fid
    return None


def month_of_ts(ts: int) -> str:
    return dt.datetime.fromtimestamp(int(ts), tz=dt.timezone.utc) \
        .strftime("%Y-%m")


def gate_metrics(p: T.SignalPlane, trades: list, k: float,
                 fold_table=FOLD_TABLE) -> dict:
    """Per-fold nets, concentration shares, RT/months counts (k book)."""
    per_fold = {fid: 0.0 for fid, _, _ in fold_table}
    per_fold_trades = {fid: 0 for fid, _, _ in fold_table}
    per_hour_pos = {}
    straddles = 0
    months = set()
    pos_pnls = []
    for t in trades:
        fid = fold_of_ts(t["entry_ts"], fold_table)
        if fid is None:
            continue
        per_fold[fid] += t["pips"]
        per_fold_trades[fid] += 1
        fe = fold_of_ts(t["exit_ts"], fold_table)
        if fe != fid:
            straddles += 1
        months.add(month_of_ts(t["entry_ts"]))
        if t["pips"] > 0:
            pos_pnls.append(t["pips"])
            h = int((t["entry_ts"] // 3600) % 24)
            per_hour_pos[h] = per_hour_pos.get(h, 0.0) + t["pips"]
    total_pos = float(sum(pos_pnls))
    top_fold = max((v for v in per_fold.values()), default=0.0)
    top_fold_share = (top_fold / total_pos) if total_pos > 0 else None
    pos_sorted = sorted(pos_pnls, reverse=True)
    top5 = float(sum(pos_sorted[:5]))
    top5_share = (top5 / total_pos) if total_pos > 0 else None
    top_hour = max(per_hour_pos.values()) if per_hour_pos else 0.0
    top_hour_share = (top_hour / total_pos) if total_pos > 0 else None
    pnls = np.array([t["pips"] for t in trades], dtype=float) \
        if trades else np.zeros(0)
    gw = float(pnls[pnls > 0].sum()) if len(pnls) else 0.0
    gl = float(-pnls[pnls < 0].sum()) if len(pnls) else 0.0
    pf = (gw / gl) if gl > 0 else None
    return {
        "per_fold_net_pips": {f: round(v, 2) for f, v in per_fold.items()},
        "per_fold_trades": per_fold_trades,
        "fold_straddles": straddles,
        "months_with_trades": sorted(months),
        "n_months": len(months),
        "n_trades_fold_assigned": int(sum(per_fold_trades.values())),
        "top_fold_id": max(per_fold, key=per_fold.get) if trades else None,
        "top_fold_share": None if top_fold_share is None
        else round(top_fold_share, 6),
        "top5_trades_share": None if top5_share is None
        else round(top5_share, 6),
        "top_hour": (max(per_hour_pos, key=per_hour_pos.get)
                     if per_hour_pos else None),
        "top_hour_share": None if top_hour_share is None
        else round(top_hour_share, 6),
        "pf": None if pf is None else round(pf, 4),
        "total_positive_net_pips": round(total_pos, 2),
    }


def evaluate_gates(cell: dict) -> dict:
    """G1..G8 with margins-to-fail, at the frozen thresholds, on the
    k=1.0 book (G4 at k=1.5; G6/G7/G8 also logged at k=2.0 as the
    freeze's stress concentration book)."""
    b = cell["books"]["1.0"]
    b15 = cell["books"]["1.5"]
    b20 = cell["books"]["2.0"]
    net0 = b["decompose"]["net_pips"]
    net15 = b15["decompose"]["net_pips"]
    pf = b["gates"]["pf"]
    n_pos_folds = sum(1 for v in b["gates"]["per_fold_net_pips"].values()
                      if v > 0)
    gates = {}

    def g(name, ok, margin, detail):
        gates[name] = {"verdict": "PASS" if ok else "FAIL",
                       "margin_to_fail": margin, "detail": detail}

    g("G1_net_gt0_k1.0", net0 > 0, round(net0, 2),
      {"net_pips": net0, "threshold": 0})
    g("G2_pf_ge_1.20", (pf is not None and pf >= PF_GATE),
      None if pf is None else round(pf - PF_GATE, 4),
      {"pf": pf, "threshold": PF_GATE})
    g("G3_pos_folds_ge_4of6", n_pos_folds >= FOLD_GATE,
      n_pos_folds - FOLD_GATE,
      {"positive_folds": n_pos_folds, "of": 6,
       "per_fold": b["gates"]["per_fold_net_pips"]})
    g("G4_net_gt0_k1.5", net15 > 0, round(net15, 2),
      {"net_pips": net15, "threshold": 0})
    g("G5_rt_ge_100_and_months_ge_6",
      b["decompose"]["n_trades"] >= RT_GATE
      and b["gates"]["n_months"] >= MONTHS_GATE,
      {"rt_margin": b["decompose"]["n_trades"] - RT_GATE,
       "months_margin": b["gates"]["n_months"] - MONTHS_GATE},
      {"rt": b["decompose"]["n_trades"], "months": b["gates"]["n_months"],
       "rt_threshold": RT_GATE, "months_threshold": MONTHS_GATE})
    for gi, key, idkey in (
            ("G6_top_fold_share", "top_fold_share", "top_fold_id"),
            ("G7_top5_trades_share", "top5_trades_share", None),
            ("G8_top_hour_share", "top_hour_share", "top_hour")):
        sh = b["gates"][key]
        ok = sh is not None and sh <= TOP_SHARE_GATE
        g(gi, ok, None if sh is None else round(TOP_SHARE_GATE - sh, 6),
          {"share": sh, "threshold": TOP_SHARE_GATE,
           "k2.0_share": b20["gates"][key],
           "argmax": b["gates"].get(idkey) if idkey else None})
    return gates


def exclusion_zones(cell: dict, arm_id: str, pair: str) -> list:
    """Q-12 exclusion-zone log: the max-share contributor at fold, trade
    and hour level (fields per the freeze f7 declaration)."""
    b = cell["books"]["1.0"]
    zones = []
    if b["decompose"]["n_trades"] == 0:
        return zones
    total_pos = b["gates"]["total_positive_net_pips"]
    if total_pos <= 0:
        return zones
    zones.append({"level": "fold", "id": b["gates"]["top_fold_id"],
                  "share": b["gates"]["top_fold_share"],
                  "threshold": TOP_SHARE_GATE, "cost_tier k": K_BASE,
                  "arm_id": arm_id, "pair": pair,
                  "fold_or_holdout_tag": cell["fold_or_holdout_tag"]})
    pos = sorted(((t["pips"], t["entry_ts"]) for t in b["trades"]
                  if t["pips"] > 0), reverse=True)[:5]
    zones.append({"level": "trade", "id": [ts for _, ts in pos],
                  "share": b["gates"]["top5_trades_share"],
                  "threshold": TOP_SHARE_GATE, "cost_tier k": K_BASE,
                  "arm_id": arm_id, "pair": pair,
                  "fold_or_holdout_tag": cell["fold_or_holdout_tag"]})
    zones.append({"level": "hour", "id": b["gates"]["top_hour"],
                  "share": b["gates"]["top_hour_share"],
                  "threshold": TOP_SHARE_GATE, "cost_tier k": K_BASE,
                  "arm_id": arm_id, "pair": pair,
                  "fold_or_holdout_tag": cell["fold_or_holdout_tag"]})
    return zones


# ------------------------------------------------------------ seam law ----

def seam_law(p: T.SignalPlane, trades_orig: list, trades_anchor: list,
             c_rt_pips: float, frozen: dict) -> dict:
    """Plan 9.4 seam law at the x1.0 book. S = net_dev(R-ORIG) -
    net_dev(R-ANCHOR). c_rt = FROZEN constant (2.0 / 2.4 pips)."""
    net_o = float(sum(t["pips"] for t in trades_orig))
    net_a = float(sum(t["pips"] for t in trades_anchor))
    S = net_o - net_a
    fold_S = {}
    for fid, _, _ in FOLD_TABLE:
        so = sum(t["pips"] for t in trades_orig
                 if fold_of_ts(t["entry_ts"]) == fid)
        sa = sum(t["pips"] for t in trades_anchor
                 if fold_of_ts(t["entry_ts"]) == fid)
        fold_S[fid] = round(so - sa, 2)
    s_pos_folds = sum(1 for v in fold_S.values() if v > 0)

    limb1_fire = bool(S > 10 * c_rt_pips)
    limb2_fire = bool(S > 3 * c_rt_pips and s_pos_folds >= FOLD_GATE)

    m3 = T.limb3_matched_pairs(trades_orig, trades_anchor,
                               min_n=SEAM_LIMB3_MIN_N)
    if m3["evaluable"]:
        ua = [t for t in trades_anchor
              if (t["entry_ts"], t["dir"]) not in
              {(u["entry_ts"], u["dir"]) for u in trades_orig}]
        uo = [t for t in trades_orig
              if (t["entry_ts"], t["dir"]) not in
              {(u["entry_ts"], u["dir"]) for u in trades_anchor}]
        # re-walk the pairing to obtain the matched trip objects
        used = set()
        pairs = []
        for t in uo:
            day_t = t["entry_ts"] // T.SEC_DAY
            cands = [(abs(u["entry_ts"] - t["entry_ts"]), u["entry_ts"], j)
                     for j, u in enumerate(ua)
                     if j not in used and u["entry_ts"] // T.SEC_DAY == day_t]
            if not cands:
                continue
            cands.sort()
            _, _, j = cands[0]
            used.add(j)
            pairs.append((t, ua[j]))
        mean_o = float(np.mean([t["pips"] for t, _ in pairs]))
        mean_a = float(np.mean([a["pips"] for _, a in pairs]))
        limb3_delta = mean_o - mean_a
        limb3 = {
            "status": "EVALUATED",
            "matched_pairs": len(pairs),
            "unmatched_orig_only_excluded": len(uo) - len(pairs),
            "unmatched_anchor_only_excluded": len(ua) - len(pairs),
            "mean_orig_matched_pips": round(mean_o, 4),
            "mean_anchor_matched_pips": round(mean_a, 4),
            "delta_pips": round(limb3_delta, 4),
            "threshold_1c_rt_pips": c_rt_pips,
            "fires": bool(limb3_delta > c_rt_pips),
        }
    else:
        limb3 = {
            "status": "NOT_RUN_FAIL_CLOSED",
            "matched_pairs": m3["matched_pairs"],
            "min_n_floor": SEAM_LIMB3_MIN_N,
            "rule": "matched-pair count < 20 => limb (iii) NOT_RUN "
                    "fail-closed; limbs (i)/(ii) decide",
            "fires": None,
        }
    fired = limb1_fire or limb2_fire or bool(limb3["fires"])
    measured_c_rt = {
        "R-ORIG": round(float(np.median(
            [T.trip_cost_pips(p, t, 1.0) for t in trades_orig])), 4)
        if trades_orig else None,
        "R-ANCHOR": round(float(np.median(
            [T.trip_cost_pips(p, t, 1.0) for t in trades_anchor])), 4)
        if trades_anchor else None,
    }
    return {
        "S_net_pips": round(S, 2),
        "net_R-ORIG_pips": round(net_o, 2),
        "net_R-ANCHOR_pips": round(net_a, 2),
        "c_rt_frozen_pips": c_rt_pips,
        "c_rt_recomputed_pips": measured_c_rt,
        "per_fold_S_pips": fold_S,
        "folds_S_positive": s_pos_folds,
        "limb_i": {"threshold_pips": round(10 * c_rt_pips, 2),
                   "S_pips": round(S, 2), "fires": limb1_fire},
        "limb_ii": {"threshold_pips": round(3 * c_rt_pips, 2),
                    "S_pips": round(S, 2),
                    "folds_S_positive": s_pos_folds,
                    "folds_needed": FOLD_GATE, "fires": limb2_fire},
        "limb_iii": limb3,
        "N_diff_frozen": frozen["N_diff"],
        "fires": fired,
        "verdict": "KILL_PIT_SEAM" if fired else "PASS_PIT_SEAM",
    }


# ------------------------------------------------------------ kill laws ----

def kill_inversion(trades_anchor: list, trades_inv: list,
                   per_fold_anchor: dict, per_fold_inv: dict) -> dict:
    net_a = float(sum(t["pips"] for t in trades_anchor))
    net_i = float(sum(t["pips"] for t in trades_inv))
    shadow_folds = {f: (per_fold_anchor.get(f, 0.0), per_fold_inv.get(f, 0.0))
                    for f in per_fold_anchor}
    viol = {f: (a, i) for f, (a, i) in shadow_folds.items()
            if a <= 0 and i > 0}
    fired = bool(net_i >= net_a) or len(viol) > 0
    return {
        "net_anchor_pips": round(net_a, 2),
        "net_inverted_pips": round(net_i, 2),
        "limb_overall": {"fires": bool(net_i >= net_a),
                         "rule": "inverted >= anchor"},
        "limb_shadow_folds": {"fires": len(viol) > 0,
                              "rule": "inverted net>0 on a fold where "
                                      "anchor net<=0",
                              "violating_folds": {f: {"anchor": round(a, 2),
                                                      "inverted": round(i, 2)}
                                                  for f, (a, i)
                                                  in viol.items()}},
        "fires": fired,
        "verdict": "KILL_INVERSION" if fired else "NO_KILL_INVERSION",
    }


def kill_control(trades_anchor: list, trades_placebo: list,
                 per_fold_anchor: dict, per_fold_placebo: dict) -> dict:
    net_a = float(sum(t["pips"] for t in trades_anchor))
    net_c = float(sum(t["pips"] for t in trades_placebo))
    limb_a = bool(net_c >= 0.5 * net_a)
    pos_folds_c = sum(1 for v in per_fold_placebo.values() if v > 0)
    limb_b = bool(pos_folds_c >= FOLD_GATE and net_a < 2 * net_c)
    fired = limb_a or limb_b
    return {
        "net_anchor_pips": round(net_a, 2),
        "net_placebo_pips": round(net_c, 2),
        "half_anchor_threshold": round(0.5 * net_a, 2),
        "limb_band": {"fires": limb_a,
                      "rule": "placebo net >= 0.5 x anchor net @ k1.0"},
        "limb_fold_residue": {"fires": limb_b,
                              "placebo_positive_folds": pos_folds_c,
                              "needed": FOLD_GATE,
                              "rule": "placebo net>0 on >=4/6 folds AND "
                                      "anchor net < 2 x placebo net"},
        "fires": fired,
        "verdict": ("KILL_CONTROL_REPRODUCED" if fired
                    else "NO_KILL_CONTROL"),
    }


def kill_beta(trades_anchor: list, book_trades: dict, pair: str) -> dict:
    net_a = float(sum(t["pips"] for t in trades_anchor))
    beta = BETA_MATCHED[pair]
    net_b = float(sum(t["pips"] for t in book_trades[beta]))
    diff = net_a - net_b
    limb_a = bool(diff <= 0)
    limb_b = bool(diff < 0.5 * net_a)
    both = {nm: round(float(sum(t["pips"] for t in ts)), 2)
            for nm, ts in book_trades.items() if nm != "FLAT"}
    fired = limb_a or limb_b
    return {
        "beta_matched_book": beta,
        "net_anchor_pips": round(net_a, 2),
        "net_beta_matched_pips": round(net_b, 2),
        "anchor_minus_beta_pips": round(diff, 2),
        "always_on_books_net_pips": both,
        "limb_nonpositive": {"fires": limb_a,
                             "rule": "anchor - beta <= 0"},
        "limb_half_edge": {"fires": limb_b,
                           "rule": "anchor - beta < 0.5 x anchor net"},
        "fires": fired,
        "verdict": "KILL_BETA_EXPLAINED" if fired else "NO_KILL_BETA",
    }


# ----------------------------------------------------------------- DSR ----

def daily_series(trades: list, start_ts: int, end_ts: int) -> pd.Series:
    """Per-period (UTC trading day) net pips series of a book."""
    per_day = {}
    for t in trades:
        per_day[t["entry_ts"] // T.SEC_DAY] = \
            per_day.get(t["entry_ts"] // T.SEC_DAY, 0.0) + t["pips"]
    days = np.arange(start_ts // T.SEC_DAY, end_ts // T.SEC_DAY + 1)
    return pd.Series([per_day.get(int(d), 0.0) for d in days],
                     index=days, dtype=float)


def deflated_sharpe(series_by_cell: dict, target_cell: str) -> dict:
    """Bailey & Lopez de Prado (2014) DSR. N = ALL cohort trials (12
    cells); per-period = UTC trading day, dev window. FLAT (the null
    book) contributes SR = 0 by convention. Returns the deflated value
    and every input so the number is reproducible."""
    srs = {}
    stats = {}
    for cid, s in series_by_cell.items():
        sd = float(s.std(ddof=1))
        sr = float(s.mean()) / sd if sd > 0 else 0.0
        srs[cid] = sr
        x = s.to_numpy(dtype=float)
        mu, sigma = float(x.mean()), float(x.std(ddof=1))
        if sigma > 0:
            z = (x - mu) / sigma
            skew = float(np.mean(z ** 3))
            kurt = float(np.mean(z ** 4))  # non-excess kurtosis
        else:
            skew, kurt = 0.0, 3.0
        stats[cid] = {"sr_daily": sr, "n_periods": int(len(x)),
                      "skew": round(skew, 6), "kurt": round(kurt, 6)}
    N = len(srs)
    v_sr = float(np.var(list(srs.values()), ddof=1))
    gamma_e = 0.5772156649015329
    emc = gamma_e
    if N > 1:
        z1 = _norm_ppf(1.0 - 1.0 / N)
        z2 = _norm_ppf(1.0 - 1.0 / (N * math.e))
        sr0 = math.sqrt(max(v_sr, 0.0)) * ((1 - emc) * z1 + emc * z2)
    else:
        sr0 = float("nan")
    st = stats[target_cell]
    sr_hat = st["sr_daily"]
    Tn = st["n_periods"]
    denom = math.sqrt(max(1e-12,
                          1.0 - st["skew"] * sr_hat
                          + (st["kurt"] - 1.0) / 4.0 * sr_hat ** 2))
    dsr = 0.5 * (1 + math.erf(
        ((sr_hat - sr0) * math.sqrt(Tn - 1) / denom) / math.sqrt(2.0)))
    return {
        "formula": "Bailey & Lopez de Prado 2014; N = ALL cohort scored "
                   "cells (12); per-period = UTC trading-day net pips, "
                   "dev window; SR non-annualized",
        "N_trials": N,
        "var_SR_across_trials": v_sr,
        "SR0_expected_max": sr0,
        "target_cell": target_cell,
        "target_stats": st,
        "per_cell_SR": {k: round(v, 6) for k, v in srs.items()},
        "DSR": round(dsr, 6),
    }


def _norm_ppf(q: float) -> float:
    # Acklam-style inverse normal CDF via statistics.NormalDist (py3.8+)
    from statistics import NormalDist

    return NormalDist().inv_cdf(q)


# --------------------------------------------------------------- holdout ---

def holdout_pass(pair: str, p_full: T.SignalPlane, targets: dict,
                 placebo_tgt: dict, warmup_end_idx: int) -> tuple:
    """ONE-LOOK holdout pass (plan 9.1): anchor + companions, identical
    machinery, k in {1.0, 1.5}. Called AT MOST ONCE per eligible pair."""
    look = {"pair": pair, "arms": {}}
    for arm in ("R-ANCHOR", "CAUSAL-PLACEBO", "INVERTED",
                "SHORT_ALWAYS", "LONG_ALWAYS", "FLAT"):
        tgt = placebo_tgt["tgt"] if arm == "CAUSAL-PLACEBO" \
            else targets[arm]
        for k in (1.0, 1.5):
            trades, _ = run_cell(p_full, tgt, k, warmup_end_idx)
            dec = decompose(p_full, trades, k)
            look["arms"].setdefault(arm, {})[str(k)] = dec
    a1 = look["arms"]["R-ANCHOR"]["1.0"]["net_pips"]
    a15 = look["arms"]["R-ANCHOR"]["1.5"]["net_pips"]
    c1 = look["arms"]["CAUSAL-PLACEBO"]["1.0"]["net_pips"]
    i1 = look["arms"]["INVERTED"]["1.0"]["net_pips"]
    beta = BETA_MATCHED[pair]
    b1 = look["arms"][beta]["1.0"]["net_pips"]
    conditions = {
        "holdout_net_gt0_k1.0": bool(a1 > 0),
        "holdout_net_gt0_k1.5": bool(a15 > 0),
        "placebo_not_reproducing": bool(c1 < 0.5 * a1),
        "inverted_strictly_below_anchor": bool(i1 < a1),
        "beta_matched_beaten": bool(a1 - b1 > 0),
    }
    return look, conditions
