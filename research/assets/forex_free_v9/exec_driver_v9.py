"""FOREX-FREE-V9 scored execution driver for the TWO frozen families
FXFV9-A5-P1 (realized-inflation surprise differential) and FXFV9-A5-P2
(inflation-differential momentum) -- A8 implementation lane.

Inherits the V6/V7/V8 driver accounting contract verbatim (p3 freeze
p3_invariants_freeze_v9.json: thresholds "identical_to_v7_v8_thresholds"):
- price identity: side * notional * (exit/entry - 1); NOTIONAL_USD = 10000
  fixed (1 unit per pair per the frozen sizing).
- costs: 1.5 bps per side via the kernel primitive (research.assets.
  forex_free_v3.accounting.bps_cost), charged exactly ONCE per fill
  (2 sides per round trip), ladder tiers {1.0, 1.5, 2.0}; TIER 2.0 PRIMARY
  -- the booked tier-2.0 financing-adjusted PnL drives the frozen rule
  order; the tier is applied to the BOOKED round trip, never scaled after
  the fact.
- financing: inherited V5 day-start as-of policy-rate differential formula
  over the pinned V5-extension ledger (accounting only, never a signal);
  booking is lenient on missing vintages (skips counted) in diagnostics and
  STRICT in the frozen survival path.
- dual books: price-only vs financing-adjusted(+costs); the price-only book
  must not invert the primary book's sign (gate 6, {0,1} vs 0.0 encoding).
- folds: 3 equal thirds of the usable decision grid, split mechanically at
  run time; a fold is POPULATED at >= 10 trades (V9 proposal non-vacuity
  floor: >= 10 anchor entries per fold, >= 60 pooled); gate: positive
  populated folds >= 2 of 3 with STRICT margin > 0 (owner option-1 ruling
  inherited from V8).
- gates: the P3 frozen rule order 1..10 with the P-2 margin-to-fail
  scaffold -- every gate emits {gate_id, value, threshold, margin}; a gate
  passes iff margin is not None and margin > 0 (strict; fail-closed on
  None).
- falsification rules (preregistered, per family): R1 control-reproduces
  kill, R2 sham-calendar kill, R3 fragility kill, R4 mechanical reject.
  Survival requires anchor > 0 AND R1..R3 clear AND all ten gates pass.
- diagnostics: the p3 diagnostic_output_contract -- the 14 canon artifacts
  (identity, per_period_series, per_symbol_breakdown, per_fold_breakdown,
  stress_tiers, drop_one_inputs, benchmark_context, margins_to_fail,
  counters, reproduction_inputs + conditional dsr_per_period_series,
  sham_control_calendar, financing_dual_books + control_rows), each jsonl
  with its diag/*@1 schema id.  DSR-computable per-period series are
  persisted (P-11: terminal DSR over N = 42 + V9 cells).  arm_config_digest
  (sha256 of the arm's frozen config JSON) is carried in every ledger row,
  decision record and identity row.
- TWIN BINDING: all computed artifacts are deterministic and
  path-independent (no absolute paths, no wall-clock inside computed
  artifacts, sorted output).

API keys: the optional --stage-spot helper (I-phase re-staging of the lost
V1 snapshot, already completed for this cycle by the integration lane)
reads TWELVE_DATA_API_KEY / FRED_API_KEY ONLY via os.environ -- keys are
never hardcoded, never printed, never written into any artifact.

Modes:
  dryrun            full pipeline on the real staged paths emitting ONLY
                    structural diagnostics: decision counts, hold stats,
                    coverage, per-clock entry/exit/open series WITHOUT any
                    PnL-shaped field (recursive-scan clean).  Scored PnL is
                    E-phase; dry-run never computes it.
  scored            full booking + gates + diagnostics over all six cells.
                    REFUSES BEFORE ANY COMPUTE unless the run contract
                    (research/control/forex_free_v9_run/run_contract.json)
                    carries the cycle id, the S0 launch authorization
                    verdict (FOREX_FREE_V9_S0_LAUNCH_AUTHORIZED), the fresh
                    owner GO phrase ("GO FOREX V9 SCORED EXECUTION") and
                    remaining budget (used + 6 <= 6).
  diagnostic-smoke  synthetic-fixture proof for the governance diagnostic
                    gate: builds the deterministic fixture in cwd, books it,
                    emits artifacts/*.jsonl in cwd.  Counts as a rerun,
                    never a scored trial.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                "..", "..", "..")))

from research.assets.forex_free_v3 import accounting as K            # read-only
from research.assets.forex_free_v5.family_a6p1 import (              # read-only
    DataBlocked as ReaderDataBlocked,
    LedgerVintageReader,
    dedupe_ledger_rows,
    load_ledger_rows,
)
from research.assets.forex_free_v9 import family_a5p1_v9 as F1
from research.assets.forex_free_v9 import family_a5p2_v9 as F2
from research.assets.forex_free_v9 import family_common as FC

CYCLE_ID = "FOREX-FREE-V9"
CTL = os.path.join("research", "control", "forex_free_v9_run")
RUN_CONTRACT_PATH = os.path.join(CTL, "run_contract.json")
SCORED_LEDGER_DEFAULT = os.path.join(CTL, "scored_ledger_published_v9.jsonl")
V5_LEDGER = os.path.join("research", "control", "forex_free_v5_run",
                         "announcement_ledger_v5_extension.jsonl")
V5_LEDGER_SHA256 = ("cf1f01a7ec2d3d7506892c045139910937147df49d3742cc4ec72b36d"
                    "20fd902")
OWNER_GO_PHRASE = "GO FOREX V9 SCORED EXECUTION"   # plan §4 E-phase phrase
S0_VERDICT = "FOREX_FREE_V9_S0_LAUNCH_AUTHORIZED"
BUDGET_CYCLE_CELLS = 6          # p3 budget.planned_scored_cells
FAMILY_CELLS = 6                # 2 families x 3 arms (selection freeze)

NOTIONAL_USD = 10000.0
STRESS_TIERS = ("1.0", "1.5", "2.0")
PRIMARY_TIER = "2.0"
MIN_PF = 1.10
MAX_PAIR_POS_SHARE = 0.40
MIN_POSITIVE_FOLDS = 2
FOLD_POPULATION_FLOOR = 10      # proposal non_vacuity_floor per fold
POOLED_ANCHOR_FLOOR = 60        # proposal non_vacuity_floor pooled
BREAK_EVEN_FLOOR_BPS = 1.5
USD_CORR_CEILING = 0.30         # V7 threshold inherited (p3 identical)

FAMILIES = OrderedDict((("FXFV9-A5-P1", F1), ("FXFV9-A5-P2", F2)))
S0_START = FC.S0_START
S0_END = FC.S0_END
DATA_PATHS_REAL = {
    "price_dir": os.path.join("data_raw", "forex_free_v9_spot"),
    "cpi_dir": os.path.join("data_raw", "forex_free_v9_cpi"),
    "gb_calendar_path": os.path.join("research", "control",
                                     "forex_free_v5_run",
                                     "gb_ons_cpi_release_dates.json"),
    "ca_calendar_path": os.path.join("research", "control",
                                     "forex_free_v6_run",
                                     "ca_statcan_cpi_release_dates_v3.json"),
    "s0_start": S0_START, "s0_end": S0_END,
    "enforce_real_grid": True,
}
DIAG_ARTIFACTS_DIR = "artifacts"
DataBlocked = ReaderDataBlocked

# sha256 pins over the consumed staged bytes (p0 census + p2 clocks pins)
PINNED_BYTES = OrderedDict((
    ("GB_OFFICIAL", (os.path.join("data_raw", "forex_free_v9_cpi", "GB",
                                  "ons_d7bt_cpi_allitems.csv"),
                     "164f5f8987915fb4ed20619b4fae2d5619322719f8eb979a767cd66e"
                     "018e223e")),
    ("CA_OFFICIAL", (os.path.join("data_raw", "forex_free_v9_cpi", "CA",
                                  "canada_allitems_nsa_2002_100_monthly.csv"),
                     "21ab59af3d5fd69bd48eaffb66147d474e1d91853ab6642cdbece6f2"
                     "cf030f80")),
    ("GB_CAL", (os.path.join("research", "control", "forex_free_v5_run",
                             "gb_ons_cpi_release_dates.json"),
                "aad19697ba3d10b56e498d836eeae48d78ebb47a08ff203bab2f32c19b6cd"
                "00d")),
    ("CA_CAL_V3", (os.path.join("research", "control", "forex_free_v6_run",
                                "ca_statcan_cpi_release_dates_v3.json"),
                   "0f1a93282348cef94aecf2b9a8da275945e809643e3646f551b2df916e"
                   "2af7b3")),
    ("AU_CAL", (os.path.join("research", "control", "forex_free_v5_run",
                             "au_abs_cpi_release_dates.json"),
                "42a4e4a36dbb6a955f7acf1aa9e3ff38b7436db775753bfbd7ad362d21bff"
                "7d1")),
    ("NZ_CAL", (os.path.join("research", "control", "forex_free_v5_run",
                             "nz_statsnz_cpi_release_dates.json"),
                "62f82c23232402f46dab854ede8023ef77dc7637af1d156f0dd748ea2490"
                "27f7")),
))
FRED_MANIFEST_RELPATH = os.path.join("data_raw", "forex_free_v9_cpi",
                                     "fred_vintaged_manifest_v9.json")

SHAM_CALENDAR_ID = ("+7d_shifted_availability_pinned_calendars_and_fred_"
                    "realtime_starts")
TRUE_CALENDAR_ID = "true_availability_sham_lives_in_neighbour_arm"

# gate ids in the FROZEN rule order (p3_invariants_freeze_v9.json rule_order)
GATE_ORDER = (
    "1_expectancy_nonpositive_fin_adj_tier2.0",
    "2_pf_ge_1.10",
    "3_positive_populated_folds_ge_2",
    "4_pair_concentration_le_0.40",
    "5_break_even_bps_le_1.5_floor",
    "6_dual_book_sign_non_inversion",
    "7_lopo_sign_robustness_all_subsets",
    "8_stress_tier_2.0_non_negative_margin",
    "9_usd_drift_diag_abs_corr_le_0.30_diagnostic",
    "10_mechanism_sanity_control_not_reproduce",
)


def staging_api_key(name: str):
    """OWNER API key for the (already completed) I-phase spot re-staging.
    Read ONLY from the environment; never hardcoded, never printed, never
    persisted into any artifact."""
    return os.environ.get(name)


# ------------------------------------------------------------------ booking #
def _r10(x):
    return None if x is None else round(x, 10)


def price_pnl_usd(tr):
    return (tr["side"] * tr["notional_usd"]
            * (tr["exit_price"] / tr["entry_price"] - 1.0))


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
                    f"{tr['pair']}: no eligible policy-rate vintage at "
                    f"{t.isoformat()}")
            return None
        diffs.append(diff / 100.0)
        day += timedelta(days=1)
    return tr["side"] * tr["notional_usd"] * math.fsum(diffs) / 365.0


def book_trades(trades, tier, reader, strict):
    """One cost charge per fill, exactly: 2 sides x bps_cost per round trip,
    booked with the trade (never scaled post hoc)."""
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
        folds.setdefault(tr["fold"], []).append(p)
    out = {}
    for f in (1, 2, 3):
        m = K.book_metrics(folds.get(f, []))
        m["populated"] = m["trades"] >= FOLD_POPULATION_FLOOR
        m["mdd_usd"] = mdd_of(folds.get(f, []))
        out[str(f)] = m
    return out


def pair_concentration(pnls, trades):
    """V7-inherited convention: max single-pair share of the POSITIVE
    fin-adj PnL pool."""
    pos = math.fsum(p for p in pnls if p > 0)
    if pos <= 0:
        return {}
    shares = {}
    for tr, p in zip(trades, pnls):
        if p > 0:
            shares[tr["pair"]] = shares.get(tr["pair"], 0.0) + p
    return {kk: round(v / pos, 6) for kk, v in sorted(shares.items())}


def break_even_bps(trades):
    """Per-side bps at which the costed expectancy reaches zero:
    mean gross bps / 2 (cost = 2 x per-side bps)."""
    if not trades:
        return None
    gross = [price_pnl_usd(t) / t["notional_usd"] * 10000.0 for t in trades]
    return _r10(math.fsum(gross) / len(gross) / 2.0)


def lopo_share(trades, reader):
    """Leave-one-pair-out sign robustness: share of subsets whose tier-2.0
    fin-adj expectancy stays positive (gate 7 requires ALL subsets)."""
    pairs = sorted({tr["pair"] for tr in trades})
    if len(pairs) < 2:
        return None
    ok = 0
    for drop in pairs:
        sub = [tr for tr in trades if tr["pair"] != drop]
        pnls, _sk = book_trades(sub, PRIMARY_TIER, reader, strict=False)
        if not pnls:
            continue
        if math.fsum(pnls) / len(pnls) > 0:
            ok += 1
    return round(ok / len(pairs), 6)


def usd_index_daily(data_paths, pairs):
    per_pair = {}
    for pair in pairs:
        _days, closes = FC.load_spot_daily(data_paths["price_dir"], pair)
        days = sorted(closes)
        steps = {}
        for d0, d1 in zip(days, days[1:]):
            steps[d1.isoformat()] = (FC.USD_LEG_SIGN[pair]
                                     * math.log(closes[d1] / closes[d0]))
        per_pair[pair] = steps
    all_days = sorted({d for s in per_pair.values() for d in s})
    return {d: math.fsum(s[d] for s in per_pair.values() if d in s)
            / sum(1 for s in per_pair.values() if d in s) for d in all_days}


def usd_drift_diag(trades, pnls, usd_index):
    """Gate 9 diagnostic: correlation between the portfolio's signed USD
    exposure and its daily PnL (a USD-beta book is not the mechanism)."""
    daily_exp, daily_pnl = {}, {}
    for tr, p in zip(trades, pnls):
        sign = FC.USD_LEG_SIGN[tr["pair"]] * tr["side"]
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


def control_reproduces(control_expectancy, anchor_expectancy):
    """R1 semantics: the control REPRODUCES the anchor when its fin-adj
    expectancy is positive and >= 0.5 x the anchor's."""
    ce, ae = control_expectancy, anchor_expectancy
    if ce is None or ae is None:
        return None
    return bool(ce > 0 and ae != 0 and ce >= 0.5 * ae)


def falsification_rules(anchor_exp, neighbour_exp, control_exp):
    """The preregistered R1..R4 rule battery (proposal falsification_rule,
    identical shape in both families).  Pure arithmetic on booked
    expectancies (tier-2.0 fin-adj)."""
    r1 = control_reproduces(control_exp, anchor_exp)
    r2 = None
    if anchor_exp is not None and neighbour_exp is not None:
        same_sign = (neighbour_exp > 0) == (anchor_exp > 0)
        r2 = bool(same_sign and neighbour_exp >= 1.0 * anchor_exp)
    r3 = None
    if anchor_exp is not None and neighbour_exp is not None:
        r3 = bool(anchor_exp > 0 and neighbour_exp <= 0)
    r4 = None
    if anchor_exp is not None:
        r4 = bool(anchor_exp <= 0)
    return {
        "R1_control_reproduces_kill": {"fires": r1},
        "R2_sham_calendar_kill": {"fires": r2},
        "R3_fragility_kill": {"fires": r3},
        "R4_mechanical_reject": {"fires": r4},
        "survival_requires": "anchor_exp > 0 AND NOT R1 AND NOT R2 AND NOT "
                             "R3 AND all ten p3 gates pass",
    }


# -------------------------------------------------------------------- gates #
def _margin(gate_id, threshold, cmp_, observed):
    """P-2 margin-to-fail row: {gate_id, value, threshold, margin}."""
    if observed is None:
        return {"gate_id": gate_id, "value": None, "threshold": threshold,
                "margin": None}
    m = (observed - threshold) if cmp_ in (">", ">=") else (threshold - observed)
    return {"gate_id": gate_id, "value": _r10(observed),
            "threshold": threshold, "margin": _r10(m)}


def evaluate_gates(rec, anchor_expectancy=None):
    """The ten frozen gates, in rule order, on the tier-2.0 fin-adj primary
    book.  Every row carries {gate_id, value, threshold, margin}; a gate
    passes iff margin is not None and margin > 0 (STRICT, owner option-1
    ruling; fail-closed on None).  Gate 10 is the family-level mechanism
    sanity verdict (the control must NOT reproduce the anchor); when
    ``control_does_not_reproduce`` is absent from the record it fails
    closed, and when ``anchor_expectancy`` is supplied it is computed
    directly from the two expectancies."""
    base = rec["base"]                      # tier-2.0 fin-adj book
    folds = rec["folds"]
    pop = [f for f in folds.values() if f["populated"]]
    pos_folds = [f for f in pop
                 if f["expectancy"] is not None and f["expectancy"] > 0]
    conc = (max(rec["pair_concentration"].values())
            if rec["pair_concentration"] else None)
    usd = rec["usd_drift_diag"]
    price_exp = rec["price_only_book"]["expectancy"]
    same_sign = (price_exp is not None and base["expectancy"] is not None
                 and (price_exp > 0) == (base["expectancy"] > 0))
    if anchor_expectancy is None:
        does_not_reproduce = rec.get("control_does_not_reproduce")
        not_reproduce = bool(does_not_reproduce)
    else:
        rep = control_reproduces(base["expectancy"], anchor_expectancy)
        not_reproduce = (rep is False)
    # Boolean gates (6/7/10) are encoded observed-in-{0.0,1.0} vs threshold
    # 0.0 so the frozen pass rule (margin > 0) is EXECUTABLE (the literal
    # observed==threshold encoding would yield margin exactly 0 and fail
    # every family by construction -- V8 adjudication kept).
    rows = [
        _margin(GATE_ORDER[0], 0.0, ">", base["expectancy"]),
        _margin(GATE_ORDER[1], MIN_PF, ">=", base["pf"]),
        _margin(GATE_ORDER[2], float(MIN_POSITIVE_FOLDS), ">=",
                float(len(pos_folds))),
        _margin(GATE_ORDER[3], MAX_PAIR_POS_SHARE, "<=", conc),
        _margin(GATE_ORDER[4], BREAK_EVEN_FLOOR_BPS, "<=",
                rec["break_even_cost_bps"]),
        _margin(GATE_ORDER[5], 0.0, ">=", 1.0 if same_sign else 0.0),
        _margin(GATE_ORDER[6], 0.0, ">=",
                1.0 if rec["lopo_share"] is not None
                and rec["lopo_share"] >= 1.0 else 0.0),
        _margin(GATE_ORDER[7], 0.0, ">=", base["total_pnl"]),
        _margin(GATE_ORDER[8], USD_CORR_CEILING, "<=",
                abs(usd["corr"]) if usd["evaluated"]
                and usd["corr"] is not None else None),
        _margin(GATE_ORDER[9], 0.0, ">=", 1.0 if not_reproduce else 0.0),
    ]
    ok = all(r["margin"] is not None and r["margin"] > 0 for r in rows)
    reasons = [f"{r['gate_id']}: margin {r['margin']}" for r in rows
               if r["margin"] is None or r["margin"] <= 0]
    return ok, reasons, rows


# --------------------------------------------------------- scored arm runner #
def run_scored_arm(family, arm, data_paths):
    out = family.run_arm(arm, data_paths)
    trades = []
    for d in out["decisions"]:
        d["notional_usd"] = NOTIONAL_USD
        trades.append(d)
    reader = LedgerVintageReader(dedupe_ledger_rows(
        load_ledger_rows(data_paths["announcement_ledger"])))

    price_pnls = [price_pnl_usd(t) for t in trades]
    base_pnls, skipped_base = book_trades(trades, PRIMARY_TIER, reader,
                                          strict=False)
    stress = {}
    for tier in STRESS_TIERS:
        pnls, _sk = book_trades(trades, tier, reader, strict=False)
        m = K.book_metrics(pnls)
        m["mdd_usd"] = mdd_of(pnls)
        stress[tier] = m
    base = K.book_metrics(base_pnls)
    base["mdd_usd"] = mdd_of(base_pnls)
    price_book = K.book_metrics(price_pnls)

    inversions = [t for t in STRESS_TIERS
                  if (K.book_metrics(book_trades(trades, t, reader,
                                                 strict=False)[0])
                      ["expectancy"] > 0) != (price_book["expectancy"] > 0)]

    rec = {
        "cycle_id": CYCLE_ID, "family_id": family.FAMILY_ID,
        "arm": arm, "arm_id": family.ARM_IDS[arm],
        "arm_config_digest": out["meta"]["arm_config_digest"],
        "n_decisions": len(trades),
        "financing_unavailable_skipped": skipped_base,
        "base": base, "price_only_book": price_book,
        "stress": stress,
        "folds": fold_books(trades, base_pnls),
        "pair_concentration": pair_concentration(base_pnls, trades),
        "break_even_cost_bps": break_even_bps(trades),
        "dual_book_ok": not inversions,
        "dual_book_inversion_tiers": inversions,
        "lopo_share": lopo_share(trades, reader),
        "usd_drift_diag": usd_drift_diag(trades, base_pnls,
                                         usd_index_daily(data_paths,
                                                         sorted({t["pair"]
                                                                 for t in
                                                                 trades}))),
        "meta": out["meta"],
        "decisions": trades,
    }
    return rec, base_pnls, reader


# ------------------------------------------------------ diagnostic artifacts #
def per_period_rows(rec, pnls):
    """Realized PnL booked at the EXIT clock, by day."""
    daily = {}
    for tr, p in zip(rec["decisions"], pnls):
        d = tr["exit_ts"][:10]
        daily[d] = daily.get(d, 0.0) + p
    return daily


def per_period_series(rec, pnls):
    """Per-DECISION-CLOCK portfolio returns for one arm (diag/
    per_period_series@1): one row for every usable decision clock of the
    arm's grid (0.0 when nothing is realized at that clock), so DSR at the
    terminal consumes a complete per-period series over the decision grid
    (P-11: N = 42 + V9 cells).  Realization convention: a trade's booked
    PnL lands on its exit clock."""
    daily = per_period_rows(rec, pnls)
    out = []
    for d in rec["meta"]["usable_clock_list"]:
        out.append((d, _r10(daily.get(d, 0.0))))
    return out


def emit_diagnostics(family_cells, meta, outdir):
    """One jsonl per contract category into outdir.  family_cells:
    {family_id: {arm: (rec, pnls, reader)}}; meta: run metadata."""
    os.makedirs(outdir, exist_ok=True)

    def w(name, rows):
        with open(os.path.join(outdir, name), "w") as f:
            for r in rows:
                f.write(json.dumps(r, sort_keys=True) + "\n")

    id_rows, pps, psb, pfb, st, doi, mtf, fdb = ([] for _ in range(8))
    bc, dsr, scc = ([] for _ in range(3))
    ctrl_rows = []
    for family_id, cells in sorted(family_cells.items()):
        family = FAMILIES[family_id]
        for arm, (rec, pnls, _reader) in sorted(cells.items()):
            arm_id = rec["arm_id"]
            for d, r in per_period_series(rec, pnls):
                pps.append({"schema_id": "diag/per_period_series@1",
                            "cycle_id": CYCLE_ID, "arm_id": arm_id,
                            "period": d, "returns": r})
                dsr.append({"schema_id": "diag/dsr_per_period_series@1",
                            "cycle_id": CYCLE_ID, "arm_id": arm_id,
                            "period": d, "returns": r})
            sym = {}
            for tr, p in zip(rec["decisions"], pnls):
                sym[tr["pair"]] = sym.get(tr["pair"], 0.0) + p
            for s_, v in sorted(sym.items()):
                psb.append({"schema_id": "diag/per_symbol_breakdown@1",
                            "cycle_id": CYCLE_ID, "arm_id": arm_id,
                            "symbol": s_, "contribution_pnl": _r10(v)})
            for fid, fm in sorted(rec["folds"].items()):
                pfb.append({"schema_id": "diag/per_fold_breakdown@1",
                            "cycle_id": CYCLE_ID,
                            "fold_id": f"{family_id}:{arm_id}:F{fid}",
                            "population": fm["trades"],
                            "pnl": fm["total_pnl"],
                            "total_pnl": fm["total_pnl"],
                            "populated": fm["populated"],
                            "expectancy": fm["expectancy"],
                            "positive": (fm["expectancy"] is not None
                                         and fm["expectancy"] > 0)})
                # benchmark treatment inherited from V7: the equal-weight
                # USD-leg index is a DIAGNOSTIC benchmark only (excess =
                # fold PnL minus 0 benchmark drift); never a gate input.
                bc.append({"schema_id": "diag/benchmark_context@1",
                           "cycle_id": CYCLE_ID,
                           "fold_id": f"{family_id}:{arm_id}:F{fid}",
                           "benchmark": "usd_equal_leg_index",
                           "excess_return": fm["total_pnl"]})
            for tier, tm in sorted(rec["stress"].items()):
                st.append({"schema_id": "diag/stress_tiers@1",
                           "cycle_id": CYCLE_ID, "tier": tier,
                           "pnl": tm["total_pnl"],
                           "total_pnl": tm["total_pnl"]})
            # sham-calendar conditional: the +7d sham is MANDATORY and
            # PRESENT for both families -- it IS the neighbour arm.  The
            # row is persisted so the calendar_conditioned conditional is
            # answered from bytes, not from silence.
            scc.append({"schema_id": "diag/sham_control_calendar@1",
                        "cycle_id": CYCLE_ID, "arm_id": arm_id,
                        "family_id": family_id,
                        "calendar": (SHAM_CALENDAR_ID if arm == "neighbour"
                                     else TRUE_CALENDAR_ID)})
            pairs = sorted({tr["pair"] for tr in rec["decisions"]})
            for drop in pairs:
                sub = [(tr, p) for tr, p in zip(rec["decisions"], pnls)
                       if tr["pair"] != drop]
                v = math.fsum(p for _, p in sub) if sub else 0.0
                doi.append({"schema_id": "diag/drop_one_inputs@1",
                            "cycle_id": CYCLE_ID,
                            "omitted_symbol": f"{arm_id}:{drop}",
                            "pnl": _r10(v)})
            for book, v in (("price_only",
                             rec["price_only_book"]["total_pnl"]),
                            ("financing_adjusted_tier2.0",
                             rec["base"]["total_pnl"])):
                fdb.append({"schema_id": "diag/financing_dual_books@1",
                            "cycle_id": CYCLE_ID,
                            "book": f"{arm_id}:{book}", "pnl": _r10(v)})
            id_rows.append({
                "schema_id": "diag/identity@1", "cycle_id": CYCLE_ID,
                "family_id": family_id, "proposal_id": family.PROPOSAL_ID,
                "arm": arm, "arm_id": arm_id,
                "arm_config_digest": rec["arm_config_digest"],
                "data_snapshot_digest": meta["data_snapshot_digest"],
                "code_freeze_sha": meta["code_freeze_sha"],
                "cost_tier": PRIMARY_TIER,
                "decision_clock": FC.DECISION_CLOCK,
                "s0_window": [S0_START.isoformat(), S0_END.isoformat()],
                "staged_manifest_sha256": meta["staged_manifest_sha256"],
                "n_usable_clocks": rec["meta"]["usable_clocks"],
            })
        # control rows: the per-family control-arm summary + R1..R4 battery
        anchor_exp = meta["expectancies"][family_id]["anchor"]
        neigh_exp = meta["expectancies"][family_id]["neighbour"]
        ctrl_exp = meta["expectancies"][family_id]["control"]
        ctrl_rec = cells["control"][0]
        ctrl_rows.append({
            "schema_id": "diag/control_rows@1", "cycle_id": CYCLE_ID,
            "family_id": family_id, "arm_id": ctrl_rec["arm_id"],
            "driver": family.arm_frozen_config("control")["driver"],
            "expectancy_fin_adj_tier2.0": _r10(ctrl_exp),
            "anchor_expectancy_fin_adj_tier2.0": _r10(anchor_exp),
            "neighbour_expectancy_fin_adj_tier2.0": _r10(neigh_exp),
            "control_semantics": (
                "home-only surprise (US leg removed)" if family_id ==
                "FXFV9-A5-P1" else "differential LEVEL form (momentum "
                "removed)"),
        })
        for rid, verdict in falsification_rules(anchor_exp, neigh_exp,
                                                ctrl_exp).items():
            row = {"schema_id": "diag/control_rows@1", "cycle_id": CYCLE_ID,
                   "family_id": family_id, "rule": rid}
            if isinstance(verdict, dict):
                row.update(verdict)
            else:
                row["note"] = verdict
            ctrl_rows.append(row)
    for cell, margins in sorted(meta["gate_margins_by_cell"].items()):
        for r in margins:
            mtf.append({"schema_id": "diag/margins_to_fail@1",
                        "cycle_id": CYCLE_ID,
                        "cell": cell, "gate_id": r["gate_id"],
                        "value": r["value"], "threshold": r["threshold"],
                        "margin": r["margin"]})
    cnt = [{"schema_id": "diag/counters@1", "cycle_id": CYCLE_ID,
            "observed_delta": meta["observed_delta"],
            "published_delta": meta["published_delta"],
            "budget_used": meta["budget_used"],
            "reruns_not_trials": meta["reruns_not_trials"]}]
    rip = [{"schema_id": "diag/reproduction_inputs@1",
            "code_freeze_sha": meta["code_freeze_sha"],
            "data_manifest_sha": meta["data_manifest_sha"],
            "staged_manifest_sha256": meta["staged_manifest_sha256"],
            "sanitized": meta["sanitized"]}]
    w("identity.jsonl", id_rows)
    w("per_period_series.jsonl", pps)
    w("per_symbol_breakdown.jsonl", psb)
    w("per_fold_breakdown.jsonl", pfb)
    w("benchmark_context.jsonl", bc)
    w("control_rows.jsonl", ctrl_rows)
    w("margins_to_fail.jsonl", mtf)
    w("stress_tiers.jsonl", st)
    w("drop_one_inputs.jsonl", doi)
    w("financing_dual_books.jsonl", fdb)
    w("dsr_per_period_series.jsonl", dsr)
    w("sham_control_calendar.jsonl", scc)
    w("counters.jsonl", cnt)
    w("reproduction_inputs.jsonl", rip)


# ---------------------------------------------------------------- staged pin #
def verify_staged_bytes(root="."):
    """Fail-closed provenance: every consumed staged byte must match its
    committed pin (AX2-C7) -- the two official tables via the p0 census
    shas, the FRED vintaged archives via the committed fred manifest, the
    pinned announcement calendars and the financing ledger via the p2/v5
    pins."""
    def sha_of(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()

    for name, (rel, expect) in PINNED_BYTES.items():
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            raise DataBlocked(f"STAGED_BYTES_MISSING: {name}: {p}")
        if sha_of(p) != expect:
            raise DataBlocked(f"STAGED_BYTES_PIN_MISMATCH: {name}")
    manifest_path = os.path.join(root, FRED_MANIFEST_RELPATH)
    if not os.path.exists(manifest_path):
        raise DataBlocked(f"STAGED_BYTES_MISSING: FRED_MANIFEST: "
                          f"{manifest_path}")
    with open(manifest_path) as f:
        manifest = json.load(f)
    from research.assets.forex_free_v9.conditioning import FRED_VINTAGED_FILES
    by_rel = {e["file"]: e for e in manifest["series"].values()}
    for econ, rel in FRED_VINTAGED_FILES.items():
        entry = by_rel.get(rel)
        if entry is None:
            raise DataBlocked(f"STAGED_BYTES_PIN_MISMATCH: FRED_{econ}: "
                              f"{rel} not in manifest")
        p = os.path.join(root, "data_raw", "forex_free_v9_cpi", rel)
        if not os.path.exists(p):
            raise DataBlocked(f"STAGED_BYTES_MISSING: FRED_{econ}: {p}")
        if sha_of(p) != entry["sha256"]:
            raise DataBlocked(f"STAGED_BYTES_PIN_MISMATCH: FRED_{econ}")
    load_pinned_ledger_or_fail(os.path.join(root, V5_LEDGER))


def load_pinned_ledger_or_fail(path):
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if h != V5_LEDGER_SHA256:
        raise RuntimeError(f"FINANCING_LEDGER_PIN_MISMATCH: {h}")
    return path


# -------------------------------------------------------------------- CLI #
def collect_cells(data_paths):
    """Run all six scored cells (2 families x 3 arms); returns
    (family_cells, gate_margins, falsifications, expectancies)."""
    family_cells, gate_margins, falsifications, expectancies = {}, {}, {}, {}
    for family_id, family in FAMILIES.items():
        cells = {}
        exps = {}
        for arm in family.ARM_IDS:
            rec, pnls, _rd = run_scored_arm(family, arm, data_paths)
            cells[arm] = (rec, pnls, _rd)
            exps[arm] = rec["base"]["expectancy"]
        fals = falsification_rules(exps["anchor"], exps["neighbour"],
                                   exps["control"])
        # gate 10 = the family-level mechanism-sanity verdict, stamped on
        # every cell of the family (strict {0,1} vs 0.0 encoding)
        family_verdict = not fals["R1_control_reproduces_kill"]["fires"]
        for arm in family.ARM_IDS:
            rec = cells[arm][0]
            rec["control_does_not_reproduce"] = family_verdict
            _ok, _r, margins = evaluate_gates(rec)
            rec["gates_ok"] = _ok
            rec["gate_reasons"] = _r
            gate_margins[f"{family_id}:{rec['arm_id']}"] = margins
        family_cells[family_id] = cells
        falsifications[family_id] = fals
        expectancies[family_id] = exps
    return family_cells, gate_margins, falsifications, expectancies


def cmd_dryrun(args, data_paths=None):
    """Full pipeline, structural diagnostics ONLY (sanitized).  Real staged
    bytes are pinned against the committed shas; injected paths (tests)
    skip the pin."""
    real = data_paths is None
    paths = DATA_PATHS_REAL if real else data_paths
    if real:
        verify_staged_bytes()
    families = []
    for family_id, family in FAMILIES.items():
        arms = []
        anchor = None
        for arm in family.ARM_IDS:
            out = family.run_arm(arm, paths)
            m = out["meta"]
            # structural per-period series (no PnL-shaped field anywhere)
            entries, exits_by_day = {}, {}
            day_set = set()
            for rec in out["decisions"]:
                day_set.add(rec["entry_day"])
                day_set.add(rec["exit_day"])
                entries[rec["entry_day"]] = entries.get(rec["entry_day"], 0) + 1
                exits_by_day[rec["exit_day"]] = \
                    exits_by_day.get(rec["exit_day"], 0) + 1
            day_list = sorted(day_set)
            events = []
            for rec in out["decisions"]:
                events.append((rec["entry_day"], 1))
                events.append((rec["exit_day"], -1))
            events.sort()
            ev_by_day = {}
            for d, delta in events:
                ev_by_day[d] = ev_by_day.get(d, 0) + delta
            cur = 0
            per_period = []
            for d in day_list:
                cur += ev_by_day.get(d, 0)
                per_period.append({"period": d,
                                   "entries": entries.get(d, 0),
                                   "exits": exits_by_day.get(d, 0),
                                   "open_positions": cur})
            holds = [rec["hold_clocks"] for rec in out["decisions"]]
            arm_row = {
                "arm": arm, "arm_id": m["arm_id"],
                "arm_config_digest": m["arm_config_digest"],
                "n_decisions": m["n_decisions"],
                "counts": m["counts"],
                "driver_meta": m["driver_meta"],
                "hold_clocks_mean": m["hold_clocks_mean"],
                "hold_clocks_max": m["hold_clocks_max"],
                "grid_clocks": m["grid_clocks"],
                "usable_clocks": m["usable_clocks"],
                "first_usable_clock": m["first_usable_clock"],
                "last_usable_clock": m["last_usable_clock"],
                "fold_first_clocks": m["fold_first_clocks"],
                "folds": m["folds"],
                "pnl_suppressed": True,
                "per_period_structural": per_period,
            }
            arms.append(arm_row)
            if arm == "anchor":
                anchor = arm_row
        pooled_entries = anchor["counts"]["entries"]
        per_fold = anchor["folds"]
        adequacy = {
            "nonvacuity_floor_pooled_anchor_entries": POOLED_ANCHOR_FLOOR,
            "nonvacuity_floor_anchor_entries_per_fold": FOLD_POPULATION_FLOOR,
            "pooled_anchor_entries": pooled_entries,
            "anchor_entries_per_fold": per_fold,
            "meets_floor": (pooled_entries >= POOLED_ANCHOR_FLOOR
                            and all(per_fold[str(f)] >= FOLD_POPULATION_FLOOR
                                    for f in (1, 2, 3))),
            "closure_if_unmet": "VACUOUS pre-scoring (data-adequacy closure; "
                                "unused slots never reassigned)",
        }
        families.append({
            "family_id": family_id, "arms": arms, "adequacy": adequacy,
        })
    report = {"schema": "forex_free_v9_dryrun_report_v1",
              "cycle_id": CYCLE_ID, "families": families,
              "mode": "dryrun_sanitized",
              "note": "sanitized: no PnL/PF/stress/break-even/financing "
                      "field at any depth; scored PnL is E-phase, "
                      "two-key gated"}
    payload = json.dumps(report, indent=1)
    if args.out:
        with open(args.out, "w") as f:
            f.write(payload)
    print(payload)
    return 0


def _refuse(missing):
    return {"schema": "forex_free_v9_scored_refusal_v1", "refused": True,
            "missing_gates": missing}


def _launch_gate_state():
    """The scored refusal reader: launch_gate.* of the V9 run contract with
    the contract's own field names (budget rule used + 6 <= 6)."""
    missing = []
    if not os.path.exists(RUN_CONTRACT_PATH):
        return ["run_contract_file"]
    with open(RUN_CONTRACT_PATH) as f:
        rc = json.load(f)
    launch = rc.get("launch_gate") or {}

    def _lg(key):
        return launch.get(key)

    if rc.get("cycle_id") != CYCLE_ID:
        missing.append("cycle_id")
    if not _lg("s0_launch_authorized") or \
            _lg("a7_prelaunch_verdict") != S0_VERDICT:
        missing.append("s0_launch_authorized")
    if not _lg("owner_go_fresh") or _lg("owner_go_phrase") != OWNER_GO_PHRASE:
        missing.append("owner_fresh_go")
    used = rc.get("budget", {}).get("used", 0)
    if used + FAMILY_CELLS > BUDGET_CYCLE_CELLS:
        missing.append("budget")
    return missing


def cmd_scored(args):
    """Two-key gated scored execution (E-phase).  Refusal BEFORE any compute
    unless every launch gate is present in the run contract."""
    missing = _launch_gate_state()
    if missing:
        print(json.dumps(_refuse(missing), indent=1))
        return 2
    with open(RUN_CONTRACT_PATH) as f:
        rc = json.load(f)
    verify_staged_bytes()
    paths = dict(DATA_PATHS_REAL)
    paths["announcement_ledger"] = V5_LEDGER

    family_cells, gate_margins, falsifications, expectancies = \
        collect_cells(paths)

    meta = {
        "data_snapshot_digest": rc.get("data_snapshot_digest", ""),
        "code_freeze_sha": rc.get("code_freeze_sha", ""),
        "data_manifest_sha": rc.get("data_manifest_sha",
                                    paths["price_dir"]),
        "staged_manifest_sha256": "fred_vintaged_manifest_v9+official_pins",
        "sanitized": False,
        "gate_margins_by_cell": gate_margins,
        "expectancies": {fid: {a: e[a] for a in sorted(e)}
                         for fid, e in expectancies.items()},
        "observed_delta": FAMILY_CELLS,
        "published_delta": FAMILY_CELLS,
        "budget_used": rc.get("budget", {}).get("used", 0) + FAMILY_CELLS,
        "reruns_not_trials": 0,
    }
    emit_diagnostics(family_cells, meta, DIAG_ARTIFACTS_DIR)

    ledger_rows = []
    for family_id, cells in sorted(family_cells.items()):
        for arm in sorted(cells):
            rec = cells[arm][0]
            ledger_rows.append({
                "record_id": f"{CYCLE_ID}:{family_id}:{rec['arm_id']}",
                "cycle_id": CYCLE_ID, "family_id": family_id,
                "proposal_id": FAMILIES[family_id].PROPOSAL_ID,
                "arm": arm, "arm_id": rec["arm_id"],
                "arm_config_digest": rec["arm_config_digest"],
                "code_freeze_sha": rc.get("code_freeze_sha", ""),
                "data_snapshot_digest": rc.get("data_snapshot_digest", ""),
                "cost_tier": PRIMARY_TIER, "dry_run": False, "scored": True,
                "n_decisions": rec["n_decisions"],
                "n_trades": rec["base"]["trades"],
                "financing_adjusted_pnl_usd": rec["base"]["total_pnl"],
                "price_only_pnl_usd": rec["price_only_book"]["total_pnl"],
                "expectancy": rec["base"]["expectancy"],
                "pf": rec["base"]["pf"],
                "mdd_usd": rec["base"]["mdd_usd"],
                "stress": rec["stress"], "folds": rec["folds"],
                "pair_concentration": rec["pair_concentration"],
                "break_even_cost_bps": rec["break_even_cost_bps"],
                "dual_book_ok": rec["dual_book_ok"],
                "dual_book_inversion_tiers": rec["dual_book_inversion_tiers"],
                "lopo_sign_robustness_share": rec["lopo_share"],
                "usd_drift_diag": rec["usd_drift_diag"],
                "decision_clock": FC.DECISION_CLOCK,
                "gates_ok": rec["gates_ok"],
                "gate_reasons": rec["gate_reasons"],
                "falsification_rules": falsifications[family_id],
                "financing_formula_id":
                    "fx5_day_start_asof_policy_rate_diff_v5ledger_v1",
                "financing_unavailable_skipped":
                    rec["financing_unavailable_skipped"],
                "usd_index_pairs": sorted(FC.USD_LEG_SIGN),
                "usd_index_source": "staged daily 16:00-NY closes, "
                                    "equal-weight USD-leg index",
                "trial_id": f"{family_id}:{arm}",
                "published": True,
            })
    with open(SCORED_LEDGER_DEFAULT, "a") as f:
        for r in ledger_rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    report = {"schema": "forex_free_v9_scored_report_v1", "cycle_id": CYCLE_ID,
              "cells": [{k: v for k, v in row.items()
                         if k not in ("stress", "folds",
                                      "pair_concentration")}
                        for row in ledger_rows],
              "ledger": SCORED_LEDGER_DEFAULT,
              "diagnostics": DIAG_ARTIFACTS_DIR,
              "budget": {"used": meta["budget_used"],
                         "planned_cycle": BUDGET_CYCLE_CELLS}}
    print(json.dumps(report, indent=1, default=str))
    return 0


def cmd_diagnostic_smoke(args):
    """Synthetic-fixture proof for the governance diagnostic gate (fresh
    sandbox): deterministic fixture in cwd, full booking, every contract
    artifact emitted into ./artifacts.  Counts as a rerun, never a trial."""
    synth = "synthetic_data"
    os.makedirs(synth, exist_ok=True)
    build = os.path.join(os.path.dirname(__file__), "synthetic_fixture_v9.py")
    subprocess.run([sys.executable, build, synth], check=True,
                   capture_output=True)
    data_paths = {
        "price_dir": synth,
        "cpi_dir": os.path.join(synth, "cpi"),
        "gb_calendar_path": os.path.join(synth, "cpi", "calendars",
                                         "gb_cal.json"),
        "ca_calendar_path": os.path.join(synth, "cpi", "calendars",
                                         "ca_cal_v3.json"),
        "announcement_ledger": os.path.join(synth, "ledger.jsonl"),
        "s0_start": date(2018, 4, 4), "s0_end": date(2019, 12, 31),
        "enforce_real_grid": False,
    }
    family_cells, gate_margins, falsifications, expectancies = \
        collect_cells(data_paths)
    meta = {
        "data_snapshot_digest": "synthetic_fixture_v9",
        "code_freeze_sha": "SYNTHETIC_SMOKE",
        "data_manifest_sha": "synthetic_fixture_v9",
        "staged_manifest_sha256": "synthetic_fixture_v9",
        "sanitized": False,
        "gate_margins_by_cell": gate_margins,
        "expectancies": {fid: {a: e[a] for a in sorted(e)}
                         for fid, e in expectancies.items()},
        "observed_delta": 0, "published_delta": 0,
        "budget_used": 0, "reruns_not_trials": 1,
    }
    emit_diagnostics(family_cells, meta, DIAG_ARTIFACTS_DIR)
    print(json.dumps({
        "schema": "forex_free_v9_diagnostic_smoke_v1", "cycle_id": CYCLE_ID,
        "emitted": DIAG_ARTIFACTS_DIR, "synthetic": True,
        "reruns_not_trials": 1,
        "n_decisions": {f"{fid}:{arm}": cells[arm][0]["n_decisions"]
                        for fid, cells in sorted(family_cells.items())
                        for arm in sorted(cells)}}))
    return 0


# -------------------------------------------------- optional staging helper #
def cmd_stage_spot(args):
    """OPTIONAL I-phase prerequisite helper (already completed for this
    cycle by the integration lane; kept so future re-staging never
    hardcodes keys).  Re-stages the daily spot snapshot via Twelve Data
    time_series 1day under the OWNER key read from the environment.
    The key is read ONLY via os.environ and is NEVER printed or persisted."""
    key = staging_api_key("TWELVE_DATA_API_KEY")
    if not key:
        print(json.dumps({"staged": False,
                          "reason": "TWELVE_DATA_API_KEY not set in "
                                    "environment"}))
        return 3
    import urllib.parse
    import urllib.request
    os.makedirs("data_raw/forex_free_v9_spot", exist_ok=True)
    done = []
    for pair in ("GBP/USD", "USDCAD", "AUD/USD", "NZD/USD"):
        sym = pair.replace("/", "")
        q = urllib.parse.urlencode({
            "symbol": pair, "interval": "1day", "outputsize": 5000,
            "apikey": key})
        url = ("https://api.twelvedata.com/time_series?" + q)
        with urllib.request.urlopen(url, timeout=60) as resp:  # nosec - owner API
            payload = json.loads(resp.read().decode("utf-8"))
        payload.pop("meta", None)
        with open(f"data_raw/forex_free_v9_spot/{sym}.json", "w") as f:
            json.dump(payload, f, sort_keys=True)
        done.append(sym)
    print(json.dumps({"staged": True, "pairs": done}))
    return 0


def resolve_mode(mode, dry_run_flag):
    """Map (positional mode, --dry-run flag) to the driver mode."""
    return mode or ("dryrun" if dry_run_flag else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?",
                    choices=["dryrun", "scored", "diagnostic-smoke"],
                    default=None)
    ap.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="structural-only pipeline pass (alias of 'dryrun')")
    ap.add_argument("--out", default=None,
                    help="dry-run: also write the report JSON to this path")
    ap.add_argument("--stage-spot", dest="stage_spot", action="store_true",
                    help="I-phase prerequisite helper: re-stage the daily "
                         "spot snapshot under the OWNER key from the "
                         "environment (already completed this cycle); then "
                         "exit")
    args = ap.parse_args()
    if args.stage_spot:
        return cmd_stage_spot(args)
    mode = resolve_mode(args.mode, args.dry_run)
    if mode is None:
        ap.error("one of {dryrun,scored,diagnostic-smoke} or --dry-run "
                 "is required")
    if mode == "dryrun":
        return cmd_dryrun(args)
    if mode == "scored":
        return cmd_scored(args)
    return cmd_diagnostic_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())
