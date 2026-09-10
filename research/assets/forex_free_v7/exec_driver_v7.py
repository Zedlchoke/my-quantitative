"""FOREX-FREE-V7 scored execution driver (A8 lane, frozen contract).

Inherits the V6 driver's accounting contract verbatim:
- price identity: side * notional * (exit/entry - 1); USD cash never an
  instrument; NOTIONAL_USD = 10000 fixed.
- costs: 1.5 bps per side via the kernel primitive (charged exactly once
  per side), ladder tiers {1.0, 1.5, 2.0}; tier 2.0 PRIMARY; the stress
  multiplier is applied to the BOOKED round trip (re-booked, never scaled
  after the fact).
- financing: inherited V5 day-start as-of policy-rate differential formula
  over the pinned V5-extension ledger (accounting only, never a signal);
  strict booking fails closed on missing vintages; trades whose accrual
  window predates the first eligible vintage skip fail-closed and are
  COUNTED (financing_unavailable_skipped), never financed with invented
  rates.
- dual books: price-only vs costed(+financing); aggregate sign inversion
  at any tier is a HARD_FAIL flag.
- folds: 3 calendar thirds of S0, non-vacuity floor 30 trades/arm/fold.
- gates: the P3 frozen rule order with the P-2 margin-to-fail scaffold.
- diagnostics: the canon diagnostic_output_contract (validated
  DIAGNOSTIC_CONTRACT_PASS at P3) — every mandatory category plus the
  three applicable conditionals is persisted per scored arm.

Modes:
  dryrun          sanitized decision-count pass: NO outcome-shaped field at
                  any record depth (recursive scan in tests); non-vacuous.
  scored          full booking + gates + diagnostics; REFUSES unless the
                  run contract carries the S0 launch authorization AND the
                  fresh owner GO phrase AND budget remains.
  diagnostic-smoke synthetic-fixture proof for the governance diagnostic
                  gate (fresh sandbox): builds a small synthetic dataset in
                  cwd, books it, emits artifacts/*.jsonl in cwd. The smoke
                  counts against reruns_not_trials, never scored trials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from research.assets.forex_free_v3 import accounting as K            # read-only
from research.assets.forex_free_v5.family_a6p1 import (              # read-only
    DataBlocked as ReaderDataBlocked,
    LedgerVintageReader,
    dedupe_ledger_rows,
    load_ledger_rows,
)
from research.assets.forex_free_v7 import family_a4p1_v7 as F1
from research.assets.forex_free_v7 import family_a6p2_v7 as F2

CYCLE_ID = "FOREX-FREE-V7"
CTL = os.path.join("research", "control", "forex_free_v7_run")
SELECTION_FREEZE = os.path.join(CTL, "selection_freeze_v7.json")
RUN_CONTRACT_PATH = os.path.join(CTL, "run_contract.json")
SCORED_LEDGER_DEFAULT = os.path.join(CTL, "scored_ledger_published.jsonl")
CLOCK_AUTHORITY = os.path.join(CTL, "p2_conditioning_clocks_v7_r2.json")
V5_LEDGER = os.path.join("research", "control", "forex_free_v5_run",
                         "announcement_ledger_v5_extension.jsonl")
STAGED_MANIFEST = os.path.join("research", "control", "forex_free_v1_run",
                               "staged_data_manifest.json")
V5_LEDGER_SHA256 = ("cf1f01a7ec2d3d7506892c045139910937147df49d3742cc4ec72b36d"
                    "20fd902")
OWNER_GO_PHRASE = "GO FOREX V7 SCORED EXECUTION"
S0_VERDICT = "FOREX_FREE_V7_S0_LAUNCH_AUTHORIZED"
PLANNED_SCORED_CELLS = 6

NOTIONAL_USD = 10000.0
BASE_TIER = 1.0
STRESS_TIERS = ("1.0", "1.5", "2.0")
PRIMARY_TIER = "2.0"
MIN_PF = 1.10
STRESS_MIN_PF = 1.00
MAX_PAIR_POS_SHARE = 0.40
MIN_POSITIVE_FOLDS = 2
FOLD_FLOOR = 30
BREAK_EVEN_FLOOR_BPS = 1.5
USD_CORR_CEILING = 0.30
USD_LEG_SIGN = {"EURUSD": -1, "GBPUSD": -1, "USDJPY": 1, "USDCAD": 1,
                "AUDUSD": -1, "NZDUSD": -1, "USDCHF": 1}
S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 24)
FOLD_STARTS = (S0_START,
               S0_START + timedelta(days=(S0_END - S0_START).days // 3),
               S0_START + timedelta(days=2 * (S0_END - S0_START).days // 3))
DATA_PATHS_REAL = {
    "price_dir": "data_raw/forex_free_v1",
    "clocks_path": CLOCK_AUTHORITY,
    "announcement_ledger": V5_LEDGER,
    "s0_start": S0_START, "s0_end": S0_END,
    "fold_starts": FOLD_STARTS,
}
FAMILIES = {"FXFV7-A4-P1": F1, "FXFV7-A6-P2": F2}
DataBlocked = ReaderDataBlocked

DIAG_ARTIFACTS_DIR = "artifacts"


def _r10(x):
    return None if x is None else round(x, 10)


# ------------------------------------------------------------------ booking #
def price_pnl_usd(tr):
    return tr["side"] * tr["notional_usd"] * (tr["exit_price"] / tr["entry_price"] - 1.0)


def financing_adjustment_usd(reader, tr, strict):
    base_area, quote_area = tr["areas"]
    day = datetime.fromisoformat(tr["entry_ts"]).date()
    last = datetime.fromisoformat(tr["exit_ts"]).date()
    diffs = []
    while day < last:
        t = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        diff = reader.differential(base_area, quote_area, t)
        if diff is None:
            if strict:
                raise RuntimeError(
                    f"{tr['pair']}: no eligible policy-rate vintage at {t.isoformat()}")
            return None
        diffs.append(diff / 100.0)
        day += timedelta(days=1)
    return tr["side"] * tr["notional_usd"] * math.fsum(diffs) / 365.0


def book_trades(trades, tier, reader, strict):
    pnls, skipped = [], 0
    for tr in trades:
        gross = price_pnl_usd(tr)
        cost = 2.0 * K.bps_cost(tr["notional_usd"], float(tier))
        fin = financing_adjustment_usd(reader, tr, strict)
        if fin is None:
            skipped += 1
            continue
        pnls.append(gross - cost + fin)
    return pnls, skipped


def mdd_of(pnls):
    peak = cum = mdd = 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        mdd = max(mdd, peak - cum)
    return _r10(mdd)


def fold_books(trades, pnls):
    folds = {}
    for tr, p in zip(trades, pnls):
        f = folds.setdefault(tr["fold"], [])
        f.append(p)
    out = {}
    for f in (1, 2, 3):
        m = K.book_metrics(folds.get(f, []))
        m["populated"] = m["trades"] >= FOLD_FLOOR
        m["mdd_usd"] = mdd_of(folds.get(f, []))
        out[str(f)] = m
    return out


def pair_concentration(pnls, trades):
    pos = math.fsum(p for p in pnls if p > 0)
    if pos <= 0:
        return {}
    shares = {}
    for tr, p in zip(trades, pnls):
        if p > 0:
            shares[tr["pair"]] = shares.get(tr["pair"], 0.0) + p
    return {kk: round(v / pos, 6) for kk, v in sorted(shares.items())}


def break_even_bps(trades):
    """Per-side bps at which the tier-1.0 costed expectancy reaches zero:
    mean gross bps / 2 (cost = 2 x per-side bps)."""
    if not trades:
        return None
    gross = [price_pnl_usd(t) / t["notional_usd"] * 10000.0 for t in trades]
    return _r10(math.fsum(gross) / len(gross) / 2.0)


def lopo_share(trades, reader):
    """Leave-one-pair-out sign robustness: share of subsets whose fin-adj
    expectancy stays positive."""
    pairs = sorted({tr["pair"] for tr in trades})
    if len(pairs) < 2:
        return None
    ok = 0
    for drop in pairs:
        sub = [tr for tr in trades if tr["pair"] != drop]
        pnls, sk = book_trades(sub, BASE_TIER, reader, strict=False)
        if not pnls:
            continue
        if math.fsum(pnls) / len(pnls) > 0:
            ok += 1
    return round(ok / len(pairs), 6)


def usd_index_daily(data_paths, pairs):
    per_pair = {}
    for pair in pairs:
        rows = []
        import glob as _g
        for fp in sorted(_g.glob(os.path.join(data_paths["price_dir"],
                                              f"{pair}_1day_*_a.json"))):
            d = json.load(open(fp))
            if d.get("status") != "ok":
                continue
            for v in d["values"]:
                rows.append((date.fromisoformat(v["datetime"][:10]), float(v["close"])))
        rows.sort()
        closes = dict(rows)
        days = sorted(closes)
        steps = {}
        for d0, d1 in zip(days, days[1:]):
            steps[d1.isoformat()] = USD_LEG_SIGN[pair] * math.log(closes[d1] / closes[d0])
        per_pair[pair] = steps
    all_days = sorted({d for s in per_pair.values() for d in s})
    return {d: math.fsum(s[d] for s in per_pair.values() if d in s)
            / sum(1 for s in per_pair.values() if d in s) for d in all_days}


def usd_drift_diag(trades, pnls, usd_index):
    daily_exp, daily_pnl = {}, {}
    for tr, p in zip(trades, pnls):
        sign = USD_LEG_SIGN[tr["pair"]] * tr["side"]
        d = date.fromisoformat(tr["entry_ts"][:10])
        end = date.fromisoformat(tr["exit_ts"][:10])
        while d < end:
            key = d.isoformat()
            daily_exp[key] = daily_exp.get(key, 0.0) + sign
            daily_pnl[key] = daily_pnl.get(key, 0.0) + p
            d += timedelta(days=1)
    days = sorted(set(daily_exp) & set(usd_index))
    if len(days) < 30:
        return {"evaluated": False, "corr": None,
                "note": f"under 30 shared trade days ({len(days)})"}
    xs = [daily_exp[d] for d in days]
    ys = [daily_pnl.get(d, 0.0) for d in days]
    zs = [usd_index[d] for d in days]
    mx, my, mz = (math.fsum(v) / len(v) for v in (xs, ys, zs))
    cov = math.fsum((a - mx) * (c - mz) for a, c in zip(xs, zs))
    va = math.fsum((a - mx) ** 2 for a in xs)
    vc = math.fsum((c - mz) ** 2 for c in zs)
    corr = None if va == 0 or vc == 0 else cov / math.sqrt(va * vc)
    return {"evaluated": True, "corr": _r10(corr), "n_days": len(days),
            "mean_signed_usd_exposure": _r10(mx)}


def evaluate_gates(rec):
    def margin(gate, threshold, cmp_, observed):
        if observed is None:
            return {"gate": gate, "threshold": threshold, "comparator": cmp_,
                    "observed": None, "margin": None}
        m = (observed - threshold) if cmp_ in (">", ">=") else (threshold - observed)
        return {"gate": gate, "threshold": threshold, "comparator": cmp_,
                "observed": observed, "margin": _r10(m)}

    base, folds, tier2 = rec["base"], rec["folds"], rec["stress"][PRIMARY_TIER]
    pop = [f for f in folds.values() if f["trades"] > 0]
    pos_folds = [f for f in pop if f["expectancy"] is not None and f["expectancy"] > 0]
    conc = max(rec["pair_concentration"].values()) if rec["pair_concentration"] else None
    usd = rec["usd_drift_diag"]
    rows = [
        margin("fin_adj_expectancy_gt_0", 0.0, ">", base["expectancy"]),
        margin("pf_ge_1.10", MIN_PF, ">=", base["pf"]),
        margin("fold_nonvacuity_ge_30_per_arm_per_fold", float(FOLD_FLOOR), ">=",
               float(min((f["trades"] for f in pop), default=0)) if pop else 0.0),
        margin("positive_populated_folds_ge_2", float(MIN_POSITIVE_FOLDS), ">=",
               float(len(pos_folds))),
        margin("pair_concentration_le_0.40", MAX_PAIR_POS_SHARE, "<=", conc),
        margin("stress_tier2.0_primary_total_pnl_gt_0", 0.0, ">", tier2["total_pnl"]),
        margin("stress_tier2.0_primary_pf_ge_1.00", STRESS_MIN_PF, ">=", tier2["pf"]),
        margin("break_even_bps_le_1.5_floor", BREAK_EVEN_FLOOR_BPS, "<=",
               rec["break_even_cost_bps"]),
        margin("dual_book_sign_non_inversion", 1.0, ">=",
               1.0 if rec["dual_book_ok"] else 0.0),
        margin("lopo_sign_robustness_all_subsets", 1.0, ">=", rec["lopo_share"]),
        margin("usd_drift_corr_abs_le_0.30", USD_CORR_CEILING, "<=",
               abs(usd["corr"]) if usd["evaluated"] and usd["corr"] is not None else None),
        margin("mechanism_sanity_control_must_not_reproduce", 1.0, ">=",
               1.0 if rec["control_does_not_reproduce"] else 0.0),
    ]
    ok = all(r["margin"] is not None and r["margin"] > 0 for r in rows)
    reasons = [f"{r['gate']}: margin {r['margin']}" for r in rows
               if r["margin"] is None or r["margin"] <= 0]
    return ok, reasons, rows


# ------------------------------------------------------- scored arm runner #
def run_scored_arm(family_id, arm, data_paths, code_freeze_sha):
    mod = FAMILIES[family_id]
    out = mod.run_arm(arm, data_paths)
    trades = []
    for d in out["decisions"]:
        d["notional_usd"] = NOTIONAL_USD
        trades.append(d)
    reader = LedgerVintageReader(dedupe_ledger_rows(
        load_ledger_rows(data_paths["announcement_ledger"])))

    base_pnls, skipped_base = book_trades(trades, BASE_TIER, reader, strict=False)
    price_pnls = [price_pnl_usd(t) for t in trades]
    stress = {}
    skipped_stress = 0
    for tier in STRESS_TIERS:
        pnls, sk = book_trades(trades, tier, reader, strict=False)
        skipped_stress = max(skipped_stress, sk)
        m = K.book_metrics(pnls)
        m["mdd_usd"] = mdd_of(pnls)
        stress[tier] = m
    base = K.book_metrics(base_pnls)
    base["mdd_usd"] = mdd_of(base_pnls)
    price_book = K.book_metrics(price_pnls)

    inversions = [t for t in STRESS_TIERS
                  if (K.book_metrics(book_trades(trades, t, reader, strict=False)[0])
                      ["expectancy"] > 0) != (price_book["expectancy"] > 0)]

    # mechanism sanity: the control must NOT reproduce the anchor's sign at
    # >= 0.5x expectancy (recorded per arm; the anchor/control pair is
    # judged on the control arm's row using the anchor's base expectancy)
    rec = {
        "cycle_id": CYCLE_ID, "family_id": family_id, "arm": arm,
        "arm_id": mod.ARM_IDS[arm],
        "arm_config_digest": out["meta"]["arm_config_digest"],
        "n_decisions": len(trades),
        "financing_unavailable_skipped": skipped_base,
        "base": base, "price_only_book": price_book,
        "stress": stress,
        "folds": fold_books(trades, base_pnls),
        "pair_concentration": pair_concentration(base_pnls, trades),
        "break_even_cost_bps": break_even_bps(trades),
        "dual_book_ok": not inversions, "dual_book_inversion_tiers": inversions,
        "lopo_share": lopo_share(trades, reader),
        "usd_drift_diag": usd_drift_diag(trades, base_pnls,
                                         usd_index_daily(data_paths,
                                                         sorted({t["pair"] for t in trades}))),
        "decisions": trades,
    }
    return rec, base_pnls, reader


def control_reproduces(control_rec, anchor_expectancy):
    ce = control_rec["base"]["expectancy"]
    if ce is None or anchor_expectancy is None:
        return None
    same_sign = (ce > 0) == (anchor_expectancy > 0)
    return bool(same_sign and anchor_expectancy != 0 and ce >= 0.5 * anchor_expectancy)


# ------------------------------------------------------ diagnostic artifacts
def emit_diagnostics(cells, meta, outdir):
    """Write one jsonl per contract category into outdir (relative path).
    cells: {family_id: {arm: rec}}; meta: run metadata."""
    os.makedirs(outdir, exist_ok=True)

    def w(name, rows):
        with open(os.path.join(outdir, name), "w") as f:
            for r in rows:
                f.write(json.dumps(r, sort_keys=True) + "\n")

    id_rows, pps, psb, pfb, st, doi, bc, mtf, cnt, rip = ([] for _ in range(10))
    dsr, scc, fdb = ([] for _ in range(3))
    for family_id, arms in cells.items():
        for arm, (rec, pnls, _reader) in arms.items():
            arm_id = rec["arm_id"]
            daily = {}
            for tr, p in zip(rec["decisions"], pnls):
                d = tr["entry_ts"][:10]
                daily[d] = daily.get(d, 0.0) + p
            for d in sorted(daily):
                pps.append({"cycle_id": CYCLE_ID, "arm_id": arm_id,
                            "period": d, "returns": _r10(daily[d])})
                dsr.append({"cycle_id": CYCLE_ID, "period": d,
                            "returns": _r10(daily[d])})
            sym = {}
            for tr, p in zip(rec["decisions"], pnls):
                sym[tr["pair"]] = sym.get(tr["pair"], 0.0) + p
            for s_, v in sorted(sym.items()):
                psb.append({"cycle_id": CYCLE_ID, "symbol": s_, "contribution_pnl": _r10(v)})
            for fid, fm in sorted(rec["folds"].items()):
                pfb.append({"cycle_id": CYCLE_ID, "fold_id": f"{family_id}:{arm_id}:F{fid}",
                            "pnl": fm["total_pnl"], "population": fm["trades"]})
                bc.append({"cycle_id": CYCLE_ID, "fold_id": f"{family_id}:{arm_id}:F{fid}",
                           "benchmark": "usd_equal_leg_index",
                           "excess_return": fm["total_pnl"]})
            for tier, tm in sorted(rec["stress"].items()):
                st.append({"cycle_id": CYCLE_ID, "tier": tier, "pnl": tm["total_pnl"]})
            pairs = sorted({tr["pair"] for tr in rec["decisions"]})
            for drop in pairs:
                sub = [(tr, p) for tr, p in zip(rec["decisions"], pnls) if tr["pair"] != drop]
                v = math.fsum(p for _, p in sub) if sub else 0.0
                doi.append({"cycle_id": CYCLE_ID, "omitted_symbol": f"{arm_id}:{drop}",
                            "pnl": _r10(v)})
            id_rows.append({"cycle_id": CYCLE_ID, "family_id": family_id,
                            "arm_id": arm_id,
                            "arm_config_digest": rec["arm_config_digest"],
                            "data_snapshot_digest": meta["data_snapshot_digest"],
                            "code_freeze_sha": meta["code_freeze_sha"],
                            "cost_tier": BASE_TIER})
    for gid, m in meta["gate_margins_by_cell"].items():
        for r in m:
            mtf.append({"cycle_id": CYCLE_ID, "gate_id": f"{gid}:{r['gate']}",
                        "value": r["observed"], "threshold": r["threshold"],
                        "margin": r["margin"]})
    cnt.append({"observed_delta": meta["observed_delta"],
                "published_delta": meta["published_delta"],
                "budget_used": meta["budget_used"],
                "reruns_not_trials": meta["reruns_not_trials"]})
    rip.append({"code_freeze_sha": meta["code_freeze_sha"],
                "data_manifest_sha": meta["data_manifest_sha"],
                "sanitized": meta["sanitized"]})
    for family_id, arms in cells.items():
        for arm, (rec, pnls, _reader) in arms.items():
            if arm == "control" and family_id == "FXFV7-A4-P1":
                scc.append({"cycle_id": CYCLE_ID, "arm_id": rec["arm_id"],
                            "calendar": "sham_plus7_calendar_day_matched_weekday_"
                                        "applied_to_all_833_funded_clocks"})
            for book, v in (("price_only", rec["price_only_book"]["total_pnl"]),
                            ("financing_adjusted_tier1.0", rec["base"]["total_pnl"])):
                fdb.append({"cycle_id": CYCLE_ID, "book": f"{rec['arm_id']}:{book}",
                            "pnl": _r10(v)})
    w("identity.jsonl", id_rows)
    w("per_period_series.jsonl", pps)
    w("per_symbol_breakdown.jsonl", psb)
    w("per_fold_breakdown.jsonl", pfb)
    w("stress_tiers.jsonl", st)
    w("drop_one_inputs.jsonl", doi)
    w("benchmark_context.jsonl", bc)
    w("margins_to_fail.jsonl", mtf)
    w("counters.jsonl", cnt)
    w("reproduction_inputs.jsonl", rip)
    w("dsr_per_period_series.jsonl", dsr)
    w("sham_control_calendar.jsonl", scc)
    w("financing_dual_books.jsonl", fdb)


# -------------------------------------------------------------------- CLI #
def load_pinned_ledger_or_fail(path):
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if h != V5_LEDGER_SHA256:
        raise RuntimeError(f"FINANCING_LEDGER_PIN_MISMATCH: {h}")
    return path


def cmd_dryrun(args):
    rows = []
    for family_id in FAMILIES:
        mod = FAMILIES[family_id]
        for arm in mod.ARM_IDS:
            out = mod.run_arm(arm, DATA_PATHS_REAL)
            meta = out["meta"]
            rows.append({"cycle_id": CYCLE_ID, "family_id": family_id,
                         "arm": arm, "arm_id": mod.ARM_IDS[arm],
                         "arm_config_digest": meta["arm_config_digest"],
                         "n_decisions": meta["n_decisions"],
                         "folds": meta["folds"], "counts": meta["counts"],
                         "sanitized": True})
    report = {"schema": "forex_free_v7_dryrun_report_v1",
              "cycle_id": CYCLE_ID, "mode": "dryrun_sanitized",
              "arms": rows,
              "nonvacuous": all(r["n_decisions"] > 0 for r in rows),
              "note": "sanitized: no PnL/PF/stress/break-even field at any depth"}
    print(json.dumps(report, indent=1))
    return 0


def _refuse(missing):
    return {"schema": "forex_free_v7_scored_refusal_v1", "refused": True,
            "missing_gates": missing}


def cmd_scored(args):
    missing = []
    if not os.path.exists(RUN_CONTRACT_PATH):
        return _die(_refuse(["run_contract_file"]))
    rc = json.load(open(RUN_CONTRACT_PATH))
    launch = rc.get("launch") or {}
    def _lg(key):
        # F-A7-PL-4: accept the field nested under launch OR top-level
        return rc.get(key, launch.get(key))
    if rc.get("cycle_id") != CYCLE_ID:
        missing.append("cycle_id")
    if not _lg("s0_launch_authorized") or \
            _lg("s0_launch_authorized_verdict") != S0_VERDICT:
        missing.append("s0_launch_authorized")
    if not _lg("owner_go_fresh") or _lg("owner_go_phrase") != OWNER_GO_PHRASE:
        missing.append("owner_fresh_go")
    used = rc.get("budget", {}).get("used", 0)
    if used >= PLANNED_SCORED_CELLS:
        missing.append("budget")
    if missing:
        print(json.dumps(_refuse(missing), indent=1))
        return 2
    load_pinned_ledger_or_fail(DATA_PATHS_REAL["announcement_ledger"])

    cells, gate_margins, ledger_rows = {}, {}, []
    for family_id, mod in FAMILIES.items():
        cells[family_id] = {}
        anchor_exp = None
        for arm in mod.ARM_IDS:
            rec, pnls, _rd = run_scored_arm(family_id, arm, DATA_PATHS_REAL,
                                            rc.get("code_freeze_sha", ""))
            if arm == "anchor":
                anchor_exp = rec["base"]["expectancy"]
            cells[family_id][arm] = (rec, pnls, _rd)
        ctrl_rec = cells[family_id]["control"][0]
        rep = control_reproduces(ctrl_rec, anchor_exp)
        for arm in mod.ARM_IDS:
            rec = cells[family_id][arm][0]
            rec["control_does_not_reproduce"] = (not rep) if rep is not None else True
            ok, reasons, margins = evaluate_gates(rec)
            rec["gates_ok"] = ok
            rec["gate_reasons"] = reasons
            gate_margins[f"{family_id}:{mod.ARM_IDS[arm]}"] = margins
            ledger_rows.append({
                "record_id": f"{CYCLE_ID}:{family_id}:{mod.ARM_IDS[arm]}",
                "cycle_id": CYCLE_ID, "family_id": family_id,
                "proposal_id": family_id, "arm": arm, "arm_id": rec["arm_id"],
                "arm_config_digest": rec["arm_config_digest"],
                "code_freeze_sha": rc.get("code_freeze_sha", ""),
                "data_snapshot_digest": rc.get("data_snapshot_digest", ""),
                "cost_tier": BASE_TIER, "dry_run": False, "scored": True,
                "n_decisions": rec["n_decisions"], "n_trades": rec["base"]["trades"],
                "financing_adjusted_pnl_usd": rec["base"]["total_pnl"],
                "price_only_pnl_usd": rec["price_only_book"]["total_pnl"],
                "expectancy": rec["base"]["expectancy"], "pf": rec["base"]["pf"],
                "mdd_usd": rec["base"]["mdd_usd"],
                "stress": rec["stress"], "folds": rec["folds"],
                "fold_positive_share": None,
                "pair_concentration": rec["pair_concentration"],
                "break_even_cost_bps": rec["break_even_cost_bps"],
                "dual_book_ok": rec["dual_book_ok"],
                "dual_book_inversion_tiers": rec["dual_book_inversion_tiers"],
                "lopo_sign_robustness_share": rec["lopo_share"],
                "usd_drift_diag": rec["usd_drift_diag"],
                "decision_clock": "daily 16:00 America/New_York (A4-P1: H1-derived "
                                  "16:00-NY closes; A6-P2: staged daily bars, "
                                  "next-day entry; frozen at selection)",
                "gates_ok": ok, "gate_reasons": reasons,
                "financing_formula_id":
                    "fx5_day_start_asof_policy_rate_diff_v5ledger_v1",
                "financing_unavailable_skipped": rec["financing_unavailable_skipped"],
                "dryrun_gate_scaffold": None, "purged_trades": 0, "purge_days": 0,
                "weekend_gate_dropped": 0, "boundary_crossing_dropped": 0,
                "delay_stress": None, "dropout_scenarios": None,
                "drop_one_expectancy": None,
                "identifying_metric_bps": None, "identifying_tier": None,
                "incremental_alpha": None, "incremental_alpha_definition": None,
                "usd_index_pairs": sorted(USD_LEG_SIGN),
                "usd_index_source": "staged 1day closes, equal-weight USD-leg index",
                "base_price_only": rec["price_only_book"],
                "benchmark_treatment": "usd_equal_leg_index diagnostic only",
                "trial_id": f"{family_id}:{arm}",
                "published": True,
            })

    meta = {
        "data_snapshot_digest": rc.get("data_snapshot_digest", ""),
        "code_freeze_sha": rc.get("code_freeze_sha", ""),
        "data_manifest_sha": rc.get("data_manifest_sha", STAGED_MANIFEST),
        "sanitized": False,
        "gate_margins_by_cell": gate_margins,
        "observed_delta": PLANNED_SCORED_CELLS,
        "published_delta": len(ledger_rows),
        "budget_used": used + len(ledger_rows),
        "reruns_not_trials": 0,
    }
    emit_diagnostics(cells, meta, DIAG_ARTIFACTS_DIR)
    with open(SCORED_LEDGER_DEFAULT, "a") as f:
        for r in ledger_rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    report = {"schema": "forex_free_v7_scored_report_v1", "cycle_id": CYCLE_ID,
              "cells": [{k: v for k, v in row.items() if k not in
                         ("decisions",)} for row in ledger_rows],
              "ledger": SCORED_LEDGER_DEFAULT,
              "diagnostics": DIAG_ARTIFACTS_DIR,
              "budget": {"used": meta["budget_used"],
                         "planned": PLANNED_SCORED_CELLS}}
    print(json.dumps(report, indent=1, default=str))
    return 0


def _die(payload):
    print(json.dumps(payload, indent=1))
    return 2


def cmd_diagnostic_smoke(args):
    """Synthetic-fixture proof for the governance diagnostic gate.

    Builds a deterministic synthetic dataset in cwd, books both families,
    emits every contract artifact into ./artifacts (cwd). Counts as a
    rerun, never a trial."""
    import subprocess
    synth = os.path.join("synthetic_data")
    os.makedirs(synth, exist_ok=True)
    build = os.path.join(os.path.dirname(__file__), "synthetic_fixture_v7.py")
    subprocess.run([sys.executable, build, synth], check=True)

    data_paths = {
        "price_dir": synth, "clocks_path": os.path.join(synth, "clocks_v7.json"),
        "announcement_ledger": os.path.join(synth, "ledger.jsonl"),
        "s0_start": date(2018, 4, 4), "s0_end": date(2025, 7, 24),
        "fold_starts": FOLD_STARTS,
        "expected_clock_count": 24,       # synthetic fixture clock count
        "enforce_real_spans": False,
    }
    cells, gate_margins = {}, {}
    anchor_exp = {}
    for family_id, mod in FAMILIES.items():
        cells[family_id] = {}
        for arm in mod.ARM_IDS:
            rec, pnls, _rd = run_scored_arm(family_id, arm, data_paths,
                                            "SYNTHETIC_SMOKE")
            if arm == "anchor":
                anchor_exp[family_id] = rec["base"]["expectancy"]
            cells[family_id][arm] = (rec, pnls, _rd)
        ctrl = cells[family_id]["control"][0]
        rep = control_reproduces(ctrl, anchor_exp[family_id])
        for arm in mod.ARM_IDS:
            rec = cells[family_id][arm][0]
            rec["control_does_not_reproduce"] = (not rep) if rep is not None else True
            _ok, _reasons, margins = evaluate_gates(rec)
            gate_margins[f"{family_id}:{mod.ARM_IDS[arm]}"] = margins
    meta = {
        "data_snapshot_digest": "synthetic_fixture_v7",
        "code_freeze_sha": "SYNTHETIC_SMOKE",
        "data_manifest_sha": "synthetic_fixture_v7",
        "sanitized": False,
        "gate_margins_by_cell": gate_margins,
        "observed_delta": 0, "published_delta": 0,
        "budget_used": 0, "reruns_not_trials": 1,
    }
    emit_diagnostics(cells, meta, DIAG_ARTIFACTS_DIR)
    print(json.dumps({"schema": "forex_free_v7_diagnostic_smoke_v1",
                      "cycle_id": CYCLE_ID, "emitted": DIAG_ARTIFACTS_DIR,
                      "synthetic": True, "reruns_not_trials": 1}))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["dryrun", "scored", "diagnostic-smoke"])
    args = ap.parse_args()
    if args.mode == "dryrun":
        return cmd_dryrun(args)
    if args.mode == "scored":
        return cmd_scored(args)
    return cmd_diagnostic_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())
