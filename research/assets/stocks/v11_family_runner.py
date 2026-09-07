"""V11 family runner for the single selected family SFV11-A5-H1
(amendment-cadence latency conditioning, process lane A5).

Implements the FROZEN packet literally
(research/control/stocks_free_v11_run/selection_freeze.json ->
proposals/a5_process_H1.json, verbatim per its implementation_spec) plus
the P3 invariants (p3_v11_invariants_freeze.json):

  - exposure late_share(e,t) = |{g in Q(e,t): inter_arrival_days > 460}| / |Q|,
    defined iff |Q| >= 4.  Q(e,t) = the staged revision-layer chain groups
    (one row per depth>=2 filer-field-period group) with
    last_avail < gate(t)  (gate(t) = 00:00 UTC of the decision session,
    inherited pit_conditioning.session_gate_utc semantics: a stamp ON the
    decision date is not visible) and 0 <= t - last_avail <= 800 days.
    REVISION-LAYER COLUMNS LOADED: entity, field, period, last_avail,
    inter_arrival_days ONLY.  The corrected-value direction/magnitude
    columns of the same staged file are NEVER parsed into any exposure -
    an I-phase recursive leak scan verifies this at record depth and by
    source inspection (no forbidden key is referenced anywhere below).
  - neighbour deep_share(e,t) = |{g in Q(e,t): depth >= 6}| / |Q|; depth is
    JOINED from the timing layer (entity, field, period, depth of depth>=2
    rows) on the group key, with a row-count reconciliation that MUST equal
    1,667,422 joined rows (the P0 census cross-check); a mismatch is
    fail-closed NOT_RUN.
  - control shuffled_chain: within-sector marginal-preserving permutation of
    the anchor values (numpy PCG64 seed 20260907, permutation applied to the
    CIK-sorted index vector, re-drawn per decision date in session-index
    order; sectors of size 1 map identity), mirroring the D2 module's
    implementation semantics (d2_v11_novelty_measure.build_a5_h1).
  - universe: ALIVE_EVIDENCED + DEAD_PRICE_CONFIRMED legs of the inherited
    cohort (cohort_v9.json + p0d integrity scan); per-decision eligibility:
    >= 63 price bars through the decision session, ADV63 >= 2,000,000 USD
    (band C or better; UNTRADABLE excluded), RAW close >= 1.00.
  - books: per-sector long-bottom/short-top terciles on the anchor rank
    (midrank ties at a boundary join the long tercile), sectors with < 6
    ranked names abstain, one-decile retention hysteresis, equal weight
    0.5/0.5 per active sector, CASH absorbs the net, gross cap 2.0
    (fail-closed assert), force-flat at fold boundaries.
  - fills at the NEXT GLOBAL session close (no same-session fill);
    fill_check: a fill references only names with a bar at the fill session,
    missing bar = the order does not exist; dead-name exit at the LAST
    recorded close (delisting return carried by the price series; no
    survivorship re-substitution).
  - costs via research/assets/stocks/kernel_band_cost_v9.py VERBATIM
    (bands A/B/C 10/15/25 bps, linear in fills, charged exactly once per
    fill, applied to booked PnL); band resolution FAIL-CLOSED (L-I3): a
    traded name without a computed band raises BandResolutionError; exits of
    held names use resolve_exit_band_bps (C-rate 25 bps ceiling when the
    band has decayed/missing, never the silent fallback).  Stress rerun =
    cost multiplier 2.0 on booked PnL.
  - drop-one design: symbol (max contributor, driver), fold (min
    expectancy, driver), process-leg depth >= 3 (runner rerun via
    kind_override late_share_depth3: late_share recomputed over only
    depth>=3 groups, |Q'| >= 4 floor re-applied on the filtered Q).

OUTCOME DISCIPLINE: run_arm(dry_run=True) computes structure only (books,
population, fills, turnover) and NEVER computes PnL or any metric; the
scored path refuses unless BOTH keys are present (two-key, P-8: the driver
stays inert without both): the exact owner GO phrase
"GO STOCKS V11 SCORED EXECUTION" AND environment flag V11_LAUNCH_AUTHORIZED=1
(set by the owner at Q/E time - this lane never sets it).  No wall-clock
timestamps enter arm records or dry-run ledgers: same inputs ->
byte-identical artifacts.

Data roots (machine-local, never copied, never committed): prices at the
V9 integration worktree .staging_prices_v9, revision/timing layers at the
V10 integration worktree .staging_sec_v10, cohort/invariants at THIS
worktree's research/control/stocks_free_v9_run (relocatable ONLY for
synthetic-fixture runs via V11_CONTROL_DIR - a data-location knob that
touches no score-affecting field).
"""

from __future__ import annotations

import bisect
import hashlib
import json
import os
import statistics
import sys
from datetime import date, timedelta

from research.assets.stocks import kernel_band_cost_v9 as kernel
from research.assets.stocks.v9_family_runner import (
    FOLDS,
    GRID_START,
    GRID_STEP,
    CLOCK_DAYS,
    decision_grid,
    fold_sessions,
    load_prices,
    load_universe,
    pct_rank,
    target_book,
    weights_from_book,
)

# ------------------------------------------------------------------ paths

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_THIS_DIR)))
_V9_ROOT = os.environ.get(
    "V11_V9_ROOT",
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration")
_V10_ROOT = os.environ.get(
    "V11_V10_ROOT",
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v10/integration")
REVISION_PATH = os.path.join(_V10_ROOT, ".staging_sec_v10",
                             "v10_revision_observables.jsonl")
TIMING_PATH = os.path.join(_V10_ROOT, ".staging_sec_v10",
                           "v10_timing_observables.jsonl")
# Control artifacts (cohort, integrity scan, price manifest) live in THIS
# repo's stocks_free_v9_run control dir; V11_CONTROL_DIR relocates them ONLY
# for synthetic-fixture runs (tests / the /tmp dry-run proof).
COHORT_DIR = os.environ.get(
    "V11_CONTROL_DIR", os.path.join(REPO_ROOT, "research", "control",
                                    "stocks_free_v9_run"))
COHORT_PATH = os.path.join(COHORT_DIR, "cohort_v9.json")
INTEGRITY_SCAN_PATH = os.path.join(COHORT_DIR, "p0d_v9_integrity_scan.json")
PRICE_MANIFEST_PATH = os.path.join(COHORT_DIR, "p0d_v9_price_manifest.json")
RUN_DIR = os.environ.get(
    "V11_RUN_DIR", os.path.join(REPO_ROOT, "research", "control",
                                "stocks_free_v11_run"))

# ------------------------------------------------------------------ frozen

STALE_DAYS = CLOCK_DAYS            # 800-day funded bound, no unbounded variant
LATENCY_CUT_DAYS = 460             # frozen_thresholds.latency_cut_days (P2 pooled p90)
NEIGHBOUR_DEPTH_CUT = 6            # frozen_thresholds.neighbour_depth_cut
MIN_Q = 4                          # frozen_thresholds.min_groups_Q
MIN_SECTOR_NAMES = 6               # frozen_thresholds.min_sector_names
GROSS_CAP = 2.0                    # frozen_thresholds.gross_cap
PCG_SEED = 20260907                # frozen_thresholds.control_permutation_seed
CENSUS_REVISION_GROUPS = 1_667_422  # P0 census chain_groups_total_depth_ge2

# layer pins from the frozen proposal source_to_test_map (fail-closed at load)
REVISION_SHA_EXPECTED = ("7110cbf010ae6d3f414a1a45eec1e504aff5e9446475"
                         "5991e98605e4795657c2")
TIMING_SHA_EXPECTED = ("b1477ea39b8b794b7f32162cb349ff53fdd1a37b9a64d0e"
                       "e20e77412ae802337")

GO_PHRASE = "GO STOCKS V11 SCORED EXECUTION"
LAUNCH_ENV = "V11_LAUNCH_AUTHORIZED"

ARM_SPECS = {
    "SFV11-A5-H1-ANCHOR": {
        "family": "SFV11-A5-H1",
        "kind": "late_share",
        "direction": "low_long",   # long low late_share (punctual), short high
        "warmup_decisions": 0,
        "score": "late_share(e,t) = |{g in Q: inter_arrival_days > 460}| / |Q|",
    },
    "SFV11-A5-H1-NEIGHBOUR": {
        "family": "SFV11-A5-H1",
        "kind": "deep_share",
        "direction": "low_long",   # same machinery; support = same-sign alpha
        "warmup_decisions": 0,
        "score": "deep_share(e,t) = |{g in Q: depth >= 6}| / |Q|",
    },
    "SFV11-A5-H1-CONTROL": {
        "family": "SFV11-A5-H1",
        "kind": "shuffled_chain",
        "direction": "low_long",   # IDENTICAL machinery on permuted exposures
        "warmup_decisions": 0,
        "score": "within-sector marginal-preserving permutation of the anchor",
    },
}
ARM_IDS = ("SFV11-A5-H1-ANCHOR", "SFV11-A5-H1-NEIGHBOUR",
           "SFV11-A5-H1-CONTROL")

RECORD_SCHEMA = "stocks_free_v11_run/arm_record@1"
HYPOTHESIS_ID = "SFV11-A5-H1"


def scored_authorized(owner_go):
    """Two-key scored authorization: exact owner GO phrase AND the launch
    environment flag (set by the owner at Q/E time - never by this lane).
    Either key absent -> refused (P-8: early or standing phrases do not
    authorize; phrases never carry across cycles)."""
    return (owner_go == GO_PHRASE
            and os.environ.get(LAUNCH_ENV) == "1")


# ------------------------------------------------------------------- data

def load_sectors(cohort_path=None):
    """{cik: sector} for the frozen cohort legs (the cohort ships the
    empirical SIC-to-SPDR majority map applied at build; carried unchanged).
    Sector is the neutralizer, never the exposure; UNMAPPED/empty tags
    abstain (inherited guard)."""
    cohort_path = cohort_path or COHORT_PATH
    with open(cohort_path) as f:
        cohort = json.load(f)
    sect = {}
    for cls in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED"):
        for m in cohort["members"].get(cls, []):
            sect[m["cik"]] = m.get("sector", "")
    return sect


def load_revision_layer(path=None):
    """Stream the staged revision layer into per-entity rows
    (last_avail, field, period, inter_arrival_days).

    Columns loaded: entity, field, period, last_avail, inter_arrival_days
    ONLY.  The corrected-value direction/magnitude columns of the same file
    are never read - no forbidden key is referenced anywhere in this module
    (I-phase leak scan verifies at source level and at record depth)."""
    rows = {}
    counts = {"rows_read": 0, "rows_kept": 0}
    with open(path or REVISION_PATH, buffering=1 << 20) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            counts["rows_read"] += 1
            r = json.loads(line)
            counts["rows_kept"] += 1
            rows.setdefault(r["e"], []).append(
                (r["last_avail"], r["f"], r["eff"], r["inter_arrival_days"]))
    return rows, counts


def load_timing_depth(path=None):
    """Stream the staged timing layer; keep depth>=2 rows as
    {entity: {(field, period): depth}}.

    Columns loaded: entity, field, period, depth ONLY (the depth-join
    authority declared by the frozen proposal source_to_test_map)."""
    depth = {}
    counts = {"rows_read": 0, "rows_kept": 0}
    with open(path or TIMING_PATH, buffering=1 << 20) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            counts["rows_read"] += 1
            r = json.loads(line)
            if r["depth"] < 2:
                continue
            counts["rows_kept"] += 1
            depth.setdefault(r["e"], {})[(r["f"], r["eff"])] = r["depth"]
    return depth, counts


def build_stacks(rev_rows, depth_map, expected_join):
    """Join depth onto the revision rows on the group key (entity, field,
    period); the joined row count MUST equal expected_join (the P0 census
    cross-check, 1,667,422 in production) or fail closed NOT_RUN.

    Builds per-entity last_avail-sorted prefix stacks:
      avails/ctot/clate/cdeep   - full depth>=2 Q (anchor + neighbour)
      avails3/ctot3/clate3      - depth>=3-only Q (drop-one-process-leg)
    Window counts are O(log n) bisect lookups (D2 prefix semantics)."""
    joined = 0
    stacks = {}
    for e, rows in rev_rows.items():
        dmap = depth_map.get(e, {})
        enriched = []
        for la, f, eff, iarr in rows:
            d = dmap.get((f, eff))
            if d is None:
                continue  # unreconciled group -> counted, fails the total
            joined += 1
            enriched.append((la, iarr, d))
        if not enriched:
            continue
        enriched.sort(key=lambda x: x[0])  # last_avail order
        avails, ctot, clate, cdeep = [], [], [], []
        avails3, ctot3, clate3 = [], [], []
        a = b = c = a3 = b3 = 0
        for la, iarr, d in enriched:
            a += 1
            b += 1 if (iarr is not None and iarr > LATENCY_CUT_DAYS) else 0
            c += 1 if d >= NEIGHBOUR_DEPTH_CUT else 0
            avails.append(la)
            ctot.append(a)
            clate.append(b)
            cdeep.append(c)
            if d >= 3:
                a3 += 1
                b3 += 1 if (iarr is not None and iarr > LATENCY_CUT_DAYS) else 0
                avails3.append(la)
                ctot3.append(a3)
                clate3.append(b3)
        stacks[e] = {"avails": avails, "ctot": ctot, "clate": clate,
                     "cdeep": cdeep, "avails3": avails3, "ctot3": ctot3,
                     "clate3": clate3}
    if joined != expected_join:
        raise ValueError(
            f"revision/timing group-key join reconciliation FAILED: "
            f"joined {joined} != expected {expected_join} - fail-closed "
            "NOT_RUN (P0 census cross-check)")
    return stacks, {"joined_rows": joined}


def _shift_iso(d_iso, days):
    return (date.fromisoformat(d_iso) + timedelta(days=days)).isoformat()


def _window_count(avails, cum, decision_date):
    """Count of Q-window members for one cumulative prefix array:
    last_avail in [t - 800d, t) (strict gate: a stamp ON the decision date
    is not visible; staleness bound inclusive at exactly 800 days)."""
    lo = bisect.bisect_left(avails, _shift_iso(decision_date, -STALE_DAYS))
    hi = bisect.bisect_left(avails, decision_date)
    if hi == 0:
        return 0
    lo_cnt = cum[lo - 1] if lo > 0 else 0
    return cum[hi - 1] - lo_cnt


def exposure_value(kind, stack, decision_date):
    """Arm exposure for one name at one decision; None when UNPOPULATED
    (|Q| < 4 -> not zero-ranked, per the frozen |Q| floor)."""
    if kind == "late_share_depth3":
        avails, tot, num = stack["avails3"], stack["ctot3"], stack["clate3"]
    elif kind == "late_share":
        avails, tot, num = stack["avails"], stack["ctot"], stack["clate"]
    elif kind == "deep_share":
        avails, tot, num = stack["avails"], stack["ctot"], stack["cdeep"]
    else:
        raise ValueError(f"unknown exposure kind {kind}")
    n = _window_count(avails, tot, decision_date)
    if n < MIN_Q:
        return None
    return _window_count(avails, num, decision_date) / n


def _pcg_rng():
    """numpy PCG64 generator at the frozen seed (local import: only the
    control arm needs numpy)."""
    import numpy as np  # local import: only the control path needs PCG64
    return np.random.Generator(np.random.PCG64(PCG_SEED))


def control_permutation(names, anchor_values, sectors, rng):
    """Within-sector marginal-preserving permutation of the anchor values
    for ONE decision date (D2 build_a5_h1 semantics, mirrored exactly):
    names is the CIK-sorted index vector; sectors are visited in sorted
    order; a sector of size 1 maps identity; otherwise one
    rng.permutation(m) draw assigns to position i the anchor value of
    position perm[i].  Preserves the EXACT per-sector exposure value
    multiset and destroys only the entity-value link."""
    by_sec = {}
    for e in names:  # already CIK-sorted by the caller
        by_sec.setdefault(sectors.get(e, ""), []).append(e)
    out = {}
    for sec in sorted(by_sec):
        block = by_sec[sec]
        m = len(block)
        if m == 1:
            out[block[0]] = anchor_values[block[0]]
            continue
        perm = rng.permutation(m)
        for i, e in enumerate(block):
            out[e] = anchor_values[block[int(perm[i])]]
    return out


# --------------------------------------------------------------- costing

def change_cost(name, dw, bands, cost_mult):
    """Linear cost for one name weight change at the fill session, via the
    kernel only: fail-closed band resolution (L-I3), charged exactly once
    on traded notional.  Missing/UNTRADABLE band at an entry = hard error."""
    return kernel.fill_cost_bps(name, dw, bands, cost_mult)


# ----------------------------------------------------------- simulation

def run_arm(arm_id, stacks, prices, folds, dry_run, owner_go=None,
            universe=None, sectors=None, price_manifest_sha="",
            revision_sha="", timing_sha="", cohort_sha="",
            code_freeze_sha="", stress=False, kind_override=None):
    """Simulate one arm of SFV11-A5-H1.

    dry_run=True: structure only, no PnL/metrics anywhere in the record.
    Scored path requires BOTH authorization keys (scored_authorized).
    stress=True applies the stress cost multiplier 2.0 (20/30/50 bps per
    side) to booked PnL - the frozen stress rerun.
    kind_override="late_share_depth3" reruns the anchor exposure over only
    depth>=3 groups (the drop-one-process-leg cell; never a fourth arm).
    """
    spec = dict(ARM_SPECS[arm_id])
    if kind_override is not None:
        if arm_id != "SFV11-A5-H1-ANCHOR":
            raise ValueError("kind_override is an anchor drop-one rerun only")
        spec["kind"] = kind_override
    if not dry_run and not scored_authorized(owner_go):
        raise SystemExit(
            "SCORED EXECUTION REFUSED: exact owner GO phrase and "
            f"{LAUNCH_ENV}=1 are both required (two-key)")
    sectors = sectors or {}
    cost_mult = 2.0 if stress else 1.0
    # the control permutes the ANCHOR's exposure values: its underlying
    # evaluation kind is late_share, the permutation rides on top
    exposure_kind = "late_share" if spec["kind"] == "shuffled_chain" \
        else spec["kind"]
    global_days = sorted({d for p in prices.values() for d in p["date"]})
    day_pos = {d: i for i, d in enumerate(global_days)}
    rng = _pcg_rng() if spec["kind"] == "shuffled_chain" else None

    held = {}        # {name: side} target book of the previous decision
    prev_exec = {}   # {name: executed weight} after the previous fill
    held_band = {}   # {name: last computed band} PIT record for dead-leg exits
    records = []
    fold_metrics = {}
    name_contrib = {}
    decision_pnls = []
    void_entry_orders = 0   # fill-check refusals (order does not exist)
    terminations = 0        # dead-name exits at last recorded close
    turnover_total = 0.0

    for fold in folds:
        sess = fold["sessions"]
        grid_dates, grid_idx = decision_grid(sess)
        fold_pnls = []
        last_bands = {}
        last_scored_entry = None
        for gi, d in enumerate(grid_dates):
            is_warmup = gi < spec["warmup_decisions"] and fold["fold_id"] == "S0_FOLD_1"
            if d not in day_pos:
                continue
            gi_global = day_pos[d]
            # bands for EVERY name with 63 bars through d (a name closes at
            # its own band even when it fails a floor - inherited F-A7-8)
            bands = {}
            elig = {}
            for e, p in prices.items():
                if universe is not None and e not in universe:
                    continue
                i = p["pos"].get(d)
                if i is None or i < 62:
                    continue  # >= 63 price bars through the decision
                adv = statistics.median(p["dvol"][i - 62: i + 1])
                b = kernel.band_of(adv)
                bands[e] = b
                held_band[e] = b
                if b != "UNTRADABLE" and p["raw"][i] >= 1.00:
                    elig[e] = i
            last_bands = bands
            # exposures (PIT at the decision gate); CIK-sorted iteration so
            # the control's index vector is the CIK-sorted one (frozen)
            raw_sig = {}
            for e in sorted(elig):
                stack = stacks.get(e)
                if stack is None:
                    continue  # no chain groups -> no exposure, by rule
                if sectors.get(e, "") in ("", "UNMAPPED"):
                    continue  # UNMAPPED sectors never guessed and abstain
                sig = exposure_value(exposure_kind, stack, d)
                if sig is not None and sig == sig:  # NaN guard
                    raw_sig[e] = sig
            if rng is not None and raw_sig:
                raw_sig = control_permutation(
                    list(raw_sig.keys()), raw_sig, sectors, rng)
            populated_frac = (len(raw_sig) / len(elig)) if elig else 0.0
            ranks = pct_rank(raw_sig)
            ranks = {k: (sectors.get(k, ""), v) for k, v in ranks.items()}
            book, n_active = target_book(ranks, held, spec["direction"])
            w = weights_from_book(book, sectors)
            gross = sum(abs(x) for x in w.values())
            if gross > GROSS_CAP + 1e-9:
                raise RuntimeError(
                    f"gross {gross} exceeds the frozen cap {GROSS_CAP} at {d}")
            # fill at the NEXT GLOBAL session close (no same-session fill)
            fill_d = global_days[gi_global + 1] if gi_global + 1 < len(global_days) else None
            if fill_d is None or fill_d > sess[-1]:
                # a fill beyond the fold end cannot exist: books are forced
                # flat at fold boundaries, so this decision is not actionable
                records.append({
                    "record_id": f"{arm_id}|{fold['fold_id']}|SKIP|{d}",
                    "decision_date": d, "fill_date": fill_d,
                    "fold": fold["fold_id"], "event": "FILL_BEYOND_FOLD_END",
                    "eligible": len(elig), "populated": len(raw_sig),
                    "populated_frac": round(populated_frac, 6),
                    "active_sectors": n_active, "legs": 0,
                    "turnover": 0.0, "cost_bps_paid": 0.0, "warmup": is_warmup,
                })
                continue
            # ---- fill-check executions at fill_d -----------------------
            turnover = 0.0
            cost = 0.0
            exec_w = {}
            for n in sorted(set(w) | set(prev_exec)):
                tgt = w.get(n, 0.0)
                old = prev_exec.get(n, 0.0)
                if abs(tgt - old) <= 1e-12:
                    if tgt != 0.0:
                        exec_w[n] = tgt
                    continue
                p = prices.get(n)
                if p is None or p["pos"].get(fill_d) is None:
                    # fill_check: missing bar at the fill session = the
                    # order does not exist; no silent substitute pricing.
                    if old != 0.0:
                        raise RuntimeError(
                            f"exit order for {n!r} without a fill-session bar - "
                            "book-state invariant violated")
                    void_entry_orders += 1  # entry order void; CASH absorbs
                    continue
                dw = tgt - old
                turnover += abs(dw)
                if abs(tgt) < abs(old):
                    # reducing/exiting a held name: its band may have decayed
                    # to UNTRADABLE or gone missing since entry - conservative
                    # C-ceiling exit path, never the cheap fallback
                    cost += kernel.exit_cost_bps(n, dw, bands, cost_mult)
                else:
                    cost += change_cost(n, dw, bands, cost_mult)  # entries strict
                if tgt != 0.0:
                    exec_w[n] = tgt
            if not exec_w:
                # every order voided by the fill-check: the decision is
                # UNFILLABLE, recorded as an event (never a scored zero-leg
                # decision); the previous book and executed weights persist.
                records.append({
                    "record_id": f"{arm_id}|{fold['fold_id']}|D|{d}",
                    "decision_date": d, "fill_date": fill_d,
                    "fold": fold["fold_id"],
                    "event": "DECISION_UNFILLABLE_VOID",
                    "eligible": len(elig), "populated": len(raw_sig),
                    "populated_frac": round(populated_frac, 6),
                    "active_sectors": n_active, "legs": 0,
                    "turnover": 0.0, "cost_bps_paid": 0.0,
                    "warmup": is_warmup, "voided_book_names": len(w),
                })
                continue
            turnover_total += turnover
            # window end: the next decision's fill session, or the fold's
            # last session (books forced flat at the boundary)
            end_date = None
            nxt_gi = gi + 1
            if nxt_gi < len(grid_idx) and grid_dates[nxt_gi] in day_pos:
                ng = day_pos[grid_dates[nxt_gi]]
                if ng + 1 < len(global_days):
                    end_date = global_days[ng + 1]
            if end_date is None or end_date > sess[-1]:
                end_date = sess[-1]  # force flat at fold end
            # ---- window accounting ------------------------------------
            # Both modes sweep terminations (book-state invariant); price
            # returns are computed ONLY in scored mode (dry-run stays
            # outcome-blind: no return, no PnL, no metric leaves here).
            pnl = 0.0
            next_exec = {}
            for n in sorted(exec_w):
                wgt = exec_w[n]
                p = prices[n]
                fi = p["pos"][fill_d]
                ei = p["pos"].get(end_date)
                r_ret = None
                if ei is not None and ei > fi:
                    next_exec[n] = wgt
                    if not dry_run:
                        r_ret = p["adj"][ei] / p["adj"][fi] - 1.0
                else:
                    # dead-name exit: last recorded close on its final
                    # session; the delisting return is carried by the
                    # price series itself; never a successor series
                    if not dry_run:
                        li = len(p["adj"]) - 1
                        r_ret = p["adj"][li] / p["adj"][fi] - 1.0
                    xcost = (abs(wgt)
                             * kernel.resolve_exit_band_bps(n, held_band)
                             * cost_mult / 10_000.0)
                    cost += xcost
                    turnover += abs(wgt)
                    turnover_total += abs(wgt)
                    terminations += 1
                if not dry_run:
                    pnl += wgt * r_ret
                    name_contrib[n] = name_contrib.get(n, 0.0) + wgt * r_ret
            pnl -= cost
            decision_pnls.append({
                "d": d, "fill_d": fill_d, "end_d": end_date,
                "fold": fold["fold_id"], "scored": not is_warmup,
            })
            if not dry_run and not is_warmup:
                fold_pnls.append(pnl)
                decision_pnls[-1]["pnl"] = pnl
                last_scored_entry = decision_pnls[-1]
            records.append({
                "record_id": f"{arm_id}|{fold['fold_id']}|D|{d}",
                "decision_date": d, "fill_date": fill_d,
                "fold": fold["fold_id"],
                "eligible": len(elig), "populated": len(raw_sig),
                "populated_frac": round(populated_frac, 6),
                "active_sectors": n_active, "legs": len(exec_w),
                "turnover": round(turnover, 6),
                "cost_bps_paid": round(cost * 1e4, 4),
                "warmup": is_warmup,
            })
            held = book
            prev_exec = next_exec
        # fold boundary: force flat WITH cost (inherited) and reset state
        if prev_exec:
            close_turnover = sum(abs(x) for x in prev_exec.values())
            close_cost = sum(
                abs(x) * kernel.resolve_exit_band_bps(n, last_bands) * cost_mult / 10_000.0
                for n, x in prev_exec.items())
            turnover_total += close_turnover
            if not dry_run and fold_pnls:
                fold_pnls[-1] -= close_cost
                if last_scored_entry is not None:
                    last_scored_entry["pnl"] = last_scored_entry["pnl"] - close_cost
            records.append({
                "record_id": f"{arm_id}|{fold['fold_id']}|FLAT|{sess[-1]}",
                "decision_date": sess[-1], "fill_date": sess[-1],
                "fold": fold["fold_id"],
                "eligible": 0, "populated": 0, "populated_frac": 0.0,
                "active_sectors": 0, "legs": 0,
                "turnover": round(close_turnover, 6),
                "cost_bps_paid": round(close_cost * 1e4, 4),
                "warmup": False, "event": "FOLD_FORCE_FLAT",
            })
            held = {}
            prev_exec = {}
            held_band = {}
        if not dry_run:
            e_sum = sum(fold_pnls)
            wins = sum(x for x in fold_pnls if x > 0)
            losses = -sum(x for x in fold_pnls if x < 0)
            cum, peak_fold, mdd = 0.0, 0.0, 0.0
            for x in fold_pnls:
                cum += x
                peak_fold = max(peak_fold, cum)
                mdd = max(mdd, peak_fold - cum)
            fold_metrics[fold["fold_id"]] = {
                "decisions": len(fold_pnls), "sum_pnl": round(e_sum, 8),
                "pf": round(wins / losses, 6) if losses > 0 else None,
                "mdd": round(mdd, 8),
            }
    decision_records = [x for x in records if x.get("event") is None]
    record = {
        "schema": RECORD_SCHEMA,
        "hypothesis_id": HYPOTHESIS_ID,
        "arm_id": arm_id,
        "family_id": spec["family"],
        "arm_config_digest": hashlib.sha256(
            json.dumps(spec, sort_keys=True).encode()).hexdigest(),
        "data_snapshot_digest": hashlib.sha256(
            (revision_sha + timing_sha + cohort_sha
             + price_manifest_sha).encode()).hexdigest(),
        "code_freeze_sha": code_freeze_sha,
        "dry_run": dry_run,
        "scored": not dry_run,
        "stress": stress,
        "direction": spec["direction"],
        "warmup_decisions": spec["warmup_decisions"],
        "decisions_total": len(decision_records),
        "scored_decisions_total": sum(
            1 for x in decision_records if not x["warmup"]),
        "void_entry_orders": void_entry_orders,
        "terminations": terminations,
        "turnover_two_way_total": round(turnover_total, 6),
        "fold_structure": [
            {k: (len(v) if k == "sessions" else v) for k, v in f.items()}
            for f in folds],
        "schedule": records,
    }
    if not dry_run:
        scored = [x for x in decision_pnls if x["scored"] and "pnl" in x]
        e_sum = sum(x["pnl"] for x in scored)
        wins = sum(x["pnl"] for x in scored if x["pnl"] > 0)
        losses = -sum(x["pnl"] for x in scored if x["pnl"] < 0)
        record["metrics"] = {
            "expectancy": round(e_sum / len(scored), 10) if scored else None,
            "sum_pnl": round(e_sum, 8),
            "pf": round(wins / losses, 6) if losses > 0 else None,
            "folds": fold_metrics,
            "top_name_contribution": (
                max(name_contrib.items(), key=lambda kv: kv[1])
                if name_contrib else None),
            "decision_pnl": [
                {"d": x["d"], "fill_d": x["fill_d"], "end_d": x["end_d"],
                 "fold": x["fold"], "pnl": round(x["pnl"], 10)}
                for x in scored],
        }
    return record
