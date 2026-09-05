"""V9 shared family runner for the single selected family SFV9-A4-H2
(cash-net depletion runway conditioning, distress lane A4).

Implements the FROZEN packet literally
(research/control/stocks_free_v9_run/proposals/a4_distress_H2.json,
sha256 3402961b..., per selection_freeze.json) plus the P3 invariants
(p3_invariants_freeze.json):

  - multi-vintage PIT as-of selection (inherited p0a_multivintage
    semantics): newest filed vintage with avail < decision gate and
    age <= the 800-day funded bound at EACH leg's own gate; never the
    latest vintage in the store; never the unbounded clock variant
    (staleness_rule_declared_ex_ante).
  - anchor  SFV9-A4-H2-ANCHOR:    (RE(v_prior) - RE(v_now) - Cash(v_now)) / Assets(v_now),
    low_long, warmup 4 decisions on fold 1 (F1 YoY-delta precedent).
  - neighbour SFV9-A4-H2-NEIGHBOUR: (RE(v_prior) - RE(v_now)) / Assets(v_now),
    depletion velocity alone, low_long, warmup 0.
  - control SFV9-A4-H2-CONTROL:   Cash(v_now) / Assets(v_now), high_long,
    warmup 0.
  - the two RE vintages must be 330-400 effective days apart at their own
    gates (fiscal-type match, F-A7-7 precedent); a name lacking the pair is
    UNPOPULATED - never proxied, never interpolated.
  - P3 eligibility floor at each decision: cohort leg member
    (ALIVE_EVIDENCED + DEAD_PRICE_CONFIRMED) + >= 63 price bars through the
    decision session + ADV63 >= 2,000,000 USD (band C or better) + RAW
    close >= 1.00 + signal populated.  Band D is UNTRADABLE_AT_DECISION.
  - sector-neutral tercile books, one-decile retention hysteresis, sectors
    with < 6 ranked names abstain; UNMAPPED sectors never guessed and
    abstain; equal-weight 0.5 long / 0.5 short per active sector, CASH
    absorbs the net.
  - inherited 21-session decision grid (per-fold local indices 63+21k),
    fills at the NEXT GLOBAL session close, no same-session fill.
  - dead-name book semantics (p3 v9_additions, PREREGISTERED):
      fill_check: a fill references only names with a bar at the fill
        session; a missing bar means the order does not exist (no silent
        substitute pricing) - the leg is not opened and CASH absorbs;
      exit: a held name whose series ends is exited at its LAST recorded
        close on its final session (the delisting return is carried by the
        price series itself; no synthetic continuation, no successor-series
        substitution ever).
  - costs via research/assets/stocks/kernel_band_cost_v9.py ONLY: linear in
    fills, charged exactly once per fill on traded notional, applied to
    booked PnL; band resolution is FAIL-CLOSED (L-I3) - the silent 10bps
    fallback is forbidden; a traded name without a computed band raises
    BandResolutionError.
  - folds forced flat at boundaries WITH cost (F-A7-6 inherited); stress
    rerun = cost multiplier 2.0 (20/30/50 bps per side); folds
    S0_FOLD_1..3 per the frozen fold table.

OUTCOME DISCIPLINE: run_arm(dry_run=True) computes structure only
(books, population, fills, turnover) and NEVER computes or prints PnL or
any metric; the scored path refuses unless BOTH keys are present (two-key,
the driver itself stays inert): the exact owner GO phrase
"GO STOCKS V9 SCORED EXECUTION" AND environment flag V9_LAUNCH_AUTHORIZED=1
(set by A1 at Q/E time).  No wall-clock timestamps are written into arm
records or dry-run ledgers: same inputs -> byte-identical artifacts.

Data root: the raw staging bytes are NEVER copied and NEVER committed.
The panel/prices/benchmarks live only in the integration worktree and are
located via V9_REPO_ROOT (default the V9 integration worktree).  Tests use
synthetic hand-computed fixtures by pointing these module paths at tmp
directories; no production byte is read by the test suite.
"""

import hashlib
import json
import os
import statistics
from datetime import date

from research.assets.stocks import kernel_band_cost_v9 as kernel

# ------------------------------------------------------------------ paths

V9_REPO_ROOT_DEFAULT = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration"
)
ROOT = os.environ.get("V9_REPO_ROOT", V9_REPO_ROOT_DEFAULT)
PANEL = f"{ROOT}/.staging_sec_v9/multivintage_panel.jsonl"
PRICES = f"{ROOT}/.staging_prices_v9/eod"
BENCH = f"{ROOT}/.staging_prices_v9/benchmarks"

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
# Control artifacts (cohort, integrity scan, price manifest, P3 freeze) live
# in the repo; V9_CONTROL_DIR relocates them ONLY for synthetic-fixture runs
# (tests / the /tmp dry-run proof).  It is a data-location knob only and
# touches no score-affecting field.
CONTROL_DIR = os.environ.get(
    "V9_CONTROL_DIR",
    os.path.join(RESEARCH_DIR, "control", "stocks_free_v9_run"))
COHORT_PATH = os.path.join(CONTROL_DIR, "cohort_v9.json")
INTEGRITY_SCAN_PATH = os.path.join(CONTROL_DIR, "p0d_v9_integrity_scan.json")
PRICE_MANIFEST_PATH = os.path.join(CONTROL_DIR, "p0d_v9_price_manifest.json")

# ------------------------------------------------------------------ frozen

FOLDS = [
    {"fold_id": "S0_FOLD_1", "start": "2018-04-04", "end": "2020-09-01"},
    {"fold_id": "S0_FOLD_2", "start": "2020-09-10", "end": "2023-02-09"},
    {"fold_id": "S0_FOLD_3", "start": "2023-02-17", "end": "2025-07-24"},
]
GRID_START = 63
GRID_STEP = 21
MIN_SECTOR_NAMES = 6
TERCILE = 1.0 / 3.0
HYSTERESIS = 0.10

# frozen funded clocks (p2_v9_coverage_first.json dead-leg set, verbatim
# {field, max_age_days} pairs from the packet; 800-day bounded variant only)
CLOCK_DAYS = 800
RE_FIELD = "us-gaap:RetainedEarningsAccumulatedDeficit"
CASH_FIELD = "us-gaap:CashAndCashEquivalentsAtCarryingValue"
ASSETS_FIELD = "us-gaap:Assets"
FISCAL_GAP_MIN_DAYS = 330
FISCAL_GAP_MAX_DAYS = 400
REFERENCE_LAG_SESSIONS = 252  # prior-year RE leg evaluated at t-252 sessions

GO_PHRASE = "GO STOCKS V9 SCORED EXECUTION"
LAUNCH_ENV = "V9_LAUNCH_AUTHORIZED"
SAMPLING_FLOOR = 0.25  # median populated fraction per decision at dry-run

ARM_SPECS = {
    "SFV9-A4-H2-ANCHOR": {
        "family": "SFV9-A4-H2",
        "kind": "depletion_runway",
        "direction": "low_long",
        "warmup_decisions": 4,
        "score": "(RE(v_prior) - RE(v_now) - Cash(v_now)) / Assets(v_now)",
    },
    "SFV9-A4-H2-NEIGHBOUR": {
        "family": "SFV9-A4-H2",
        "kind": "depletion_velocity",
        "direction": "low_long",
        "warmup_decisions": 0,
        "score": "(RE(v_prior) - RE(v_now)) / Assets(v_now)",
    },
    "SFV9-A4-H2-CONTROL": {
        "family": "SFV9-A4-H2",
        "kind": "cash_ratio",
        "direction": "high_long",
        "warmup_decisions": 0,
        "score": "Cash(v_now) / Assets(v_now)",
    },
}
ARM_IDS = ("SFV9-A4-H2-ANCHOR", "SFV9-A4-H2-NEIGHBOUR", "SFV9-A4-H2-CONTROL")

RECORD_SCHEMA = "stocks_free_v9_run/arm_record@1"


def scored_authorized(owner_go):
    """Two-key scored authorization: exact owner GO phrase AND the launch
    environment flag set by A1 at Q/E time.  Either key absent -> refused
    (the driver stays inert; P-8: early or standing phrases do not authorize)."""
    return (
        owner_go == GO_PHRASE
        and os.environ.get(LAUNCH_ENV) == "1"
    )


# ------------------------------------------------------------------- data

def load_universe(cohort_path=None, scan_path=None):
    """The two frozen cohort legs: ALIVE_EVIDENCED (cohort_v9.json members)
    + DEAD_PRICE_CONFIRMED (p0d integrity-scan confirmed verdicts).
    Excluded legs (GAP_COVERAGE, NOT_DEAD_PRICE_SURVIVAL) never enter.
    Paths resolve at CALL time (module constants may be relocated in
    tests/synthetic runs)."""
    cohort_path = cohort_path or COHORT_PATH
    scan_path = scan_path or INTEGRITY_SCAN_PATH
    cohort = json.load(open(cohort_path))
    scan = json.load(open(scan_path))
    uni = {m["cik"] for m in cohort["members"].get("ALIVE_EVIDENCED", [])}
    for _cik, v in scan.get("dead_verdicts", {}).items():
        if v.get("verdict") == "DEAD_PRICE_CONFIRMED":
            uni.add(_cik)
    return uni


def load_panel(fields, unit="USD", panel_path=None):
    """Stream the multi-vintage panel; keep only wanted fields.  unit="USD"
    (the frozen specs form ratios/deltas only from USD-stamped vintages,
    F-A7-3 remediation) drops non-matching rows at load, fail-visible via
    the returned counts.  Non-numeric values never count as coverage."""
    want = set(fields)
    out = {}
    counts = {"rows_read": 0, "rows_kept": 0}
    with open(panel_path or PANEL) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            counts["rows_read"] += 1
            r = json.loads(line)
            fld = r["f"]
            if fld not in want:
                continue
            if unit is not None and r.get("u") != unit:
                continue
            if r["v"] is None or not isinstance(r["v"], (int, float)):
                continue
            counts["rows_kept"] += 1
            e = out.setdefault(r["e"], {"sector": r["s"], "rows": {}})
            e["rows"].setdefault(fld, []).append((r["avail"], r["eff"], r["v"]))
    for e in out.values():
        for fld in e["rows"]:
            e["rows"][fld].sort()
    return out, counts


def load_prices(prices_dir=None):
    """{entity: {"date", "raw", "adj", "dvol", "pos"}} sorted by date.
    pos maps each date to ITS OWN array index (never a global calendar
    index - the F-A7-1 remediation).  Malformed files fail closed."""
    root = prices_dir or PRICES
    out = {}
    for fn in sorted(os.listdir(root)):
        if not fn.endswith(".json"):
            continue
        cik = fn.split("__")[0]
        with open(os.path.join(root, fn)) as f:
            bars = json.load(f)
        dates = [b["date"] for b in bars]
        out[cik] = {
            "date": dates,
            "raw": [float(b["close"]) for b in bars],
            "adj": [float(b["adjusted_close"]) for b in bars],
            "dvol": [float(b["close"]) * float(b["volume"]) for b in bars],
            "pos": {d: i for i, d in enumerate(dates)},
        }
    return out


def asof(rows, decision_date, age_days=None):
    """Newest filed vintage with avail < decision_date (strictly before the
    00:00 UTC gate) and age <= bound.  Scans every row (order-independent;
    load_panel sorts anyway).  Inherited p0a multivintage semantics."""
    best = None
    for avail, eff, v in rows:
        if avail >= decision_date:
            continue
        if age_days is not None:
            if (date.fromisoformat(decision_date) - date.fromisoformat(avail)).days > age_days:
                continue
        if best is None or (avail, eff) > (best[0], best[1]):
            best = (avail, eff, v)
    return best


# --------------------------------------------------------------- schedule

def fold_sessions(prices, folds=None):
    """Market session set = the union of all bars' dates (observed calendar);
    per-fold ordered session lists within [start, end]."""
    days = set()
    for p in prices.values():
        days.update(p["date"])
    all_days = sorted(days)
    out = []
    for f in (folds or FOLDS):
        sess = [d for d in all_days if f["start"] <= d <= f["end"]]
        out.append({"fold_id": f["fold_id"], "sessions": sess})
    return out


def decision_grid(fold_sess):
    """Per-fold local indices 63+21k, strictly inside the fold (inherited
    21-session grid, unchanged)."""
    idx = list(range(GRID_START, len(fold_sess), GRID_STEP))
    return [fold_sess[i] for i in idx], idx


# --------------------------------------------------------------- signals

def _num_ok(vintage):
    """A vintage leg is usable only with a real finite-ish number (None,
    strings and NaN are unpopulated; NaN fails the v != v check)."""
    if vintage is None:
        return False
    v = vintage[2]
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v


def signal_value(spec, panel_entity, decision_date, prev_session_date):
    """Arm signal for one name at one decision; None when UNPOPULATED.

    Every vintage selection cites the 800-day bounded funded clock at its
    OWN gate (staleness_rule_declared_ex_ante: the unbounded variant is
    forbidden).  The prior-year RE leg is evaluated at its own as-of
    reference (prev_session_date = the session 252 global sessions before
    the decision); the pair must be 330-400 effective days apart (fiscal-
    type match) or the name is unpopulated - never proxied, never
    interpolated, no surrogate pairing."""
    rows = panel_entity["rows"]
    kind = spec["kind"]
    if kind in ("depletion_runway", "depletion_velocity"):
        need = (RE_FIELD, ASSETS_FIELD) + ((CASH_FIELD,) if kind == "depletion_runway" else ())
        if any(f not in rows for f in need):
            return None
        re_now = asof(rows[RE_FIELD], decision_date, CLOCK_DAYS)
        if prev_session_date is None:
            return None
        re_prior = asof(rows[RE_FIELD], prev_session_date, CLOCK_DAYS)
        if not _num_ok(re_now) or not _num_ok(re_prior):
            return None
        # fiscal-type match: the pair must be 330-400 eff days apart
        gap = (date.fromisoformat(re_now[1]) - date.fromisoformat(re_prior[1])).days
        if not (FISCAL_GAP_MIN_DAYS <= gap <= FISCAL_GAP_MAX_DAYS):
            return None
        assets = asof(rows[ASSETS_FIELD], decision_date, CLOCK_DAYS)
        if not _num_ok(assets) or not assets[2]:
            return None
        den = float(assets[2])
        depletion = float(re_prior[2]) - float(re_now[2])
        if kind == "depletion_velocity":
            return depletion / den
        cash = asof(rows[CASH_FIELD], decision_date, CLOCK_DAYS)
        if not _num_ok(cash):
            return None
        return (depletion - float(cash[2])) / den
    if kind == "cash_ratio":
        if CASH_FIELD not in rows or ASSETS_FIELD not in rows:
            return None
        cash = asof(rows[CASH_FIELD], decision_date, CLOCK_DAYS)
        assets = asof(rows[ASSETS_FIELD], decision_date, CLOCK_DAYS)
        if not _num_ok(cash) or not _num_ok(assets) or not assets[2]:
            return None
        return float(cash[2]) / float(assets[2])
    raise ValueError(f"unknown arm kind {kind}")


def pct_rank(values):
    """Percentile rank in [0,1]; average ranks for ties.  Inherited."""
    keys = list(values.keys())
    vals = [values[k] for k in keys]
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg / (len(vals) - 1) if len(vals) > 1 else 0.5
        i = j + 1
    return dict(zip(keys, ranks))


# ------------------------------------------------------------------ book

def target_book(ranks, held, direction):
    """Sector-neutral tercile targets with one-decile retention hysteresis.
    ranks: {name: (sector, pct)}; held: {name: side} from previous decision.
    Returns ({name: side}, n_active_sectors); sectors with < 6 ranked names
    abstain.  Inherited verbatim."""
    by_sector = {}
    for n, (sec, pct) in ranks.items():
        by_sector.setdefault(sec, []).append((n, pct))
    book = {}
    active = 0
    for sec, items in sorted(by_sector.items()):
        if len(items) < MIN_SECTOR_NAMES:
            continue
        active += 1
        for n, pct in items:
            prev = held.get(n)
            if direction == "low_long":
                is_long = pct <= TERCILE or (prev == "L" and pct <= TERCILE + HYSTERESIS)
                is_short = pct >= 1 - TERCILE or (prev == "S" and pct >= 1 - TERCILE - HYSTERESIS)
            else:
                is_long = pct >= 1 - TERCILE or (prev == "L" and pct >= 1 - TERCILE - HYSTERESIS)
                is_short = pct <= TERCILE or (prev == "S" and pct <= TERCILE + HYSTERESIS)
            if is_long and not is_short:
                book[n] = "L"
            elif is_short and not is_long:
                book[n] = "S"
    return book, active


def weights_from_book(book, sectors):
    """Equal-weight within legs, 1/n_active allocation per sector, 0.5 long
    / 0.5 short inside each active sector.  CASH absorbs the net.  Inherited."""
    legs = {}
    by_sector = {}
    for n, side in book.items():
        by_sector.setdefault(sectors[n], {"L": [], "S": []})[side].append(n)
    active = [s for s, d in by_sector.items() if d["L"] and d["S"]]
    for s in active:
        d = by_sector[s]
        for n in d["L"]:
            legs[n] = 0.5 / (len(active) * len(d["L"]))
        for n in d["S"]:
            legs[n] = -0.5 / (len(active) * len(d["S"]))
    return legs


# ------------------------------------------------------------ costing

def change_cost(name, dw, bands, cost_mult):
    """Linear cost for one name weight change at the fill session, via the
    kernel only: fail-closed band resolution (L-I3), charged exactly once
    on traded notional.  Missing band at costing = hard error."""
    return kernel.fill_cost_bps(name, dw, bands, cost_mult)


# ----------------------------------------------------------- simulation

def run_arm(arm_id, panel, prices, folds, dry_run, owner_go=None,
            universe=None, price_manifest_sha="", panel_sha="",
            code_freeze_sha="", stress=False):
    """Simulate one arm of SFV9-A4-H2.

    dry_run=True: structure only, no PnL/metrics anywhere in the record.
    Scored path requires BOTH authorization keys (scored_authorized).
    stress=True applies the stress cost multiplier 2.0 (20/30/50 bps per
    side) to booked PnL - the frozen stress rerun.
    """
    spec = ARM_SPECS[arm_id]
    if not dry_run and not scored_authorized(owner_go):
        raise SystemExit(
            "SCORED EXECUTION REFUSED: exact owner GO phrase and "
            f"{LAUNCH_ENV}=1 are both required (two-key)")
    # fail closed on what THIS arm actually reads
    if spec["kind"] == "depletion_runway":
        need = {RE_FIELD, CASH_FIELD, ASSETS_FIELD}
    elif spec["kind"] == "depletion_velocity":
        need = {RE_FIELD, ASSETS_FIELD}
    else:
        need = {CASH_FIELD, ASSETS_FIELD}
    available = set()
    for ent in panel.values():
        available.update(ent["rows"].keys())
        if need <= available:
            break
    missing = sorted(need - available)
    if missing:
        raise ValueError(f"panel missing required fields {missing} - fail closed")
    sect = {e: v["sector"] for e, v in panel.items()}
    cost_mult = 2.0 if stress else 1.0
    uses_reference = spec["kind"] in ("depletion_runway", "depletion_velocity")
    # global union calendar (fold/grid structure and fill clock only)
    global_days = sorted({d for p in prices.values() for d in p["date"]})
    day_pos = {d: i for i, d in enumerate(global_days)}

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
            # bands for EVERY name with 63 bars through d (F-A7-8: a name
            # closes at its own band even when it fails the floor)
            bands = {}
            elig = {}
            for e, p in prices.items():
                if universe is not None and e not in universe:
                    continue
                i = p["pos"].get(d)
                if i is None or i < 62:
                    continue
                adv = statistics.median(p["dvol"][i - 62: i + 1])
                b = kernel.band_of(adv)
                bands[e] = b
                held_band[e] = b
                if b != "UNTRADABLE" and p["raw"][i] >= 1.00:
                    elig[e] = i
            last_bands = bands
            # signals (PIT at the decision gate; prior-year leg at t-252)
            prev_d = (global_days[gi_global - REFERENCE_LAG_SESSIONS]
                      if (uses_reference and gi_global >= REFERENCE_LAG_SESSIONS)
                      else None)
            raw_sig = {}
            for e in elig:
                ent = panel.get(e)
                if ent is None:
                    continue
                if sect.get(e) in (None, "", "UNMAPPED"):
                    continue  # UNMAPPED sectors never guessed and abstain
                sig = signal_value(spec, ent, d, prev_d)
                if sig is not None and sig == sig:  # NaN guard
                    raw_sig[e] = sig
            populated_frac = (len(raw_sig) / len(elig)) if elig else 0.0
            ranks = pct_rank(raw_sig)
            ranks = {k: (sect[k], v) for k, v in ranks.items()}
            book, n_active = target_book(ranks, held, spec["direction"])
            w = weights_from_book(book, sect)
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
                        # a held name survives to the previous window end
                        # (== this fill session) so it HAS a bar here; an
                        # exit for a bar-less held name is unreachable and
                        # must fail closed rather than silently vanish
                        raise RuntimeError(
                            f"exit order for {n!r} without a fill-session bar - "
                            "book-state invariant violated")
                    void_entry_orders += 1  # entry order void; CASH absorbs
                    continue
                dw = tgt - old
                turnover += abs(dw)
                if abs(tgt) < abs(old):
                    # reducing/exiting a held name: its band may have decayed
                    # to UNTRADABLE or gone missing since entry (V9-R1) -
                    # conservative C-ceiling exit path, never the cheap 10bps
                    cost += kernel.exit_cost_bps(n, dw, bands, cost_mult)
                else:
                    cost += change_cost(n, dw, bands, cost_mult)  # entries stay strict
                if tgt != 0.0:
                    exec_w[n] = tgt
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
        # fold boundary: force flat WITH cost (F-A7-6) and reset book state
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
        "hypothesis_id": "SFV9-A4-H2",
        "arm_id": arm_id,
        "family_id": spec["family"],
        "arm_config_digest": hashlib.sha256(
            json.dumps(spec, sort_keys=True).encode()).hexdigest(),
        "data_snapshot_digest": hashlib.sha256(
            (panel_sha + price_manifest_sha).encode()).hexdigest(),
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
