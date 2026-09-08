"""STOCKS-FREE-V13 D2 proposal exposure handlers (D2 handler-writing lane).

Registers the SIX blind-proposal anchor exposure builders into the D2
machine's PROPOSAL_EXPOSURE_BUILDERS registry
(research/assets/stocks/d2_v13_novelty_measure.py) via import side-effect,
and exposes the matching CONTROL exposure builders (PROPOSAL_CONTROL_BUILDERS)
for the A1-style execution lane (research/assets/stocks/d2_v13_run.py).

The exposures are implemented EXACTLY as frozen in the D1 proposals
(research/control/stocks_free_v13_run/d1/proposals/proposal_{A4_P1,A4_P2,
A5_P1,A5_P2,A6_P1,A6_P2}.json); the fields features_and_lags /
d2_predeclarations / anchor_arm / control_arms are the authority. Nothing is
reinterpreted. Discipline: feature/rank arithmetic only - zero PnL, zero
returns, zero selection, zero scoring. Deterministic: only proposal-frozen
seeds; no wall clock; all cross-entity iteration in sorted order.

HANDLER CONTRACT (registry): handler(C) -> {(cik_entity, iso_date_str): float}
at the proposal's OWN frozen decision instants (the 30-date frozen quarterly
grid; SFV13-A6-* emit the 27 SCORED dates only, first three grid dates are
declared warmup in their clocks). Abstain = omit the key. NOTE: the runner
converts the iso date strings to datetime.date before feeding the machine's
novelty_block (whose veto builders take date objects); the machine's own
worked example used (entity, date-object) keys - the handlers here use
iso strings per the V13 handler-writing lane contract.

EXPOSURES (registered anchors):
  SFV13-A4-P1  netdir(e,t)      identity-deduplicated net-direction share,
                                non-derivative G-class Form-4 rows, acceptance
                                window (prev(D), D], floor: >= 2 identities
                                AND >= 3 in-window stream rows.
  SFV13-A4-P2  netdir_opp(e,t)  same form restricted to OPPORTUNISTIC rows
                                (CMP month-history rule on acceptance stamps;
                                routine iff the identity has >= 1 same-issuer
                                same-acceptance-month-of-year row in >= 2 of
                                the 3 prior calendar years, candidates strictly
                                before prev(D)); floor: >= 2 in-window opp rows.
  SFV13-A5-P1  w_i * (1-pct)    within-sector percentile of L =
                                LongTermDebtNoncurrent/Assets (panel as-of,
                                avail < D) times the frozen DFII10
                                expanding-percentile regime weight (HIGH 1.0 /
                                MID 0.5 / LOW 0.0, forced MID on dates 0-4).
                                Long-bottom/short-top orientation.
  SFV13-A5-P2  w_i * pct        within-sector percentile of G =
                                Liabilities/Assets times the T10YIE regime
                                weight (same frozen rule). Long-high/short-low.
  SFV13-A6-P1  X in {-1,0,+1}   dividend transition state from staged EODHD
                                dividend records (ex-date evidence; 365/730
                                trailing existence windows; absence-assertable
                                iff earliest staged ex_date <= D-730 or the
                                prior window holds >= 1 record).
  SFV13-A6-P2  X in {-1,0,+1}   split-direction state from staged EODHD split
                                records (most recent split in [D-180, D);
                                ratio>1 +1 / <1 -1 / none 0; unity or
                                unparsable most-recent ratio = defect abstain).

CONTROLS (PROPOSAL_CONTROL_BUILDERS; measured by the runner through
machine.identifiability_anchor_vs_control):
  SFV13-A4-P1  sham_insider_placebo        direction permuted within
                                           (decision-date, sector) cells,
                                           numpy PCG64 seed 20260908.
               filing_arrival_exposure_form  log1p(n4) over ALL Form-4
                                           acceptances (filing level, no
                                           direction) via the machine's
                                           load_form4_acceptances().
  SFV13-A4-P2  sham_insider_placebo        seed 20260909; the frozen
                                           classification is direction-free so
                                           it survives the permutation
                                           UNCHANGED (recomputed anyway).
               filing_arrival_exposure_form  same form as P1.
  SFV13-A5-P1  sham_macro_placebo          duration-preserving block
                                           permutation of the DFII10 weight
                                           vector, numpy default_rng seeded
                                           with int(wave_sha[:8],16) % 2**31.
               exposure_form_control_dgs10 same formula with DGS10 weights.
  SFV13-A5-P2  sham_macro_placebo / exposure_form_control_dgs10 (same forms).
  SFV13-A6-P1  within_sector_permutation   exposure values permuted within
                                           (date, sector) cells by the frozen
                                           deterministic hash order sha256 of
                                           "cycle|{hyp}|{cik}|{decision_index}"
                                           hex-sorted (no RNG library).
  SFV13-A6-P2  within_sector_permutation   same, hypothesis_id SFV13-A6-H2.

PROPOSAL-TEXT AMBIGUITY RESOLVED (documented, frozen text quoted):
  proposal_A5_P1.json / proposal_A5_P2.json control_arms.sham_macro_placebo
  declare: "seed = int(wave_sha[:8], 16) mod 2^31 = int('f1fba3c4', 16) mod
  2^31 = 1911101388". The FORMULA gives int('f1fba3c4',16) % 2**31 =
  1912316868; the inline number 1911101388 is an arithmetic slip in the
  proposal text. The normative definition is the formula ("seed derived from
  the frozen wave sha ... zero free parameters"), so A5_SHAM_SEED here is
  1912316868 = int(WAVE_SHA[:8], 16) % 2**31, computed - not hard-coded.

Other documented resolutions (all narrower than the frozen text, none
reinterpret it):
  - A4 window bounds are compared as the machine's own worked example does
    (d2_v13_novelty_measure.example_insider_buy_pressure): string compare
    prev_iso < stamp <= t_iso on the acceptance timestamp (filingDate
    date-only fallback has 0 measured occurrences per the proposal; any
    occurrence is counted in diagnostics). This implements gate(t) = 00:00 UTC.
  - A5 within-sector percentile: pct(e) = #{sector peers with defined ratio
    <= e's ratio} / n_defined at the decision (self-inclusive). D2 novelty is
    rank-based, so any monotone percentile convention yields identical gate
    arithmetic; the convention is fixed here for byte-stable exposures.
  - Macro as-of: "the row with realtime_start <= D, the latest such row";
    a "."/unparsable value at the selected row is a fail-closed abstention
    (the whole regime vector -> None -> handler returns {}, the machine's
    BLOCKED_EXPOSURE_UNDEFINED path). Measured as-of bindable 30/30 per the
    proposals, so this should never fire on real data.
  - A6 dividends ex-date: staged bytes are raw EODHD vendor arrays; the
    record's ex-date is read from an explicit "ex_date" field if present else
    the vendor "date" field. Absent file = no data -> entity abstains.
  - A6 splits: ratio read from "split" (fallback "ratio"/"split_factor");
    absent file = no records = declared default state 0; a PRESENT but
    unreadable file is a measurement failure -> entity abstains (never 0).
  - Identity rule rows carrying neither rptOwnerCik nor rptOwnerName are
    defect-excluded (counted) rather than collapsed into one degenerate
    identity bucket; the parse contract routes malformed XML to defects, so
    such rows should not exist in the staged stream.

SELFCHECK (mandatory): /Users/hoangminhlong/my-quantitative/.venv/bin/python
  -m research.assets.stocks.d2_v13_proposal_handlers --selfcheck
  from the worktree ROOT (never direct-file run - stdlib calendar shadow,
  INC-V13-1). Builds tiny synthetic fixtures for every data source and
  proves each anchor + control exposure on hand-computed values (expected
  numbers in comments at each assertion). Exits 0 on pass.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

from research.assets.stocks import d2_v13_novelty_measure as machine

# ===========================================================================
# frozen constants (verbatim from the six proposals)
# ===========================================================================
CYCLE = "STOCKS-FREE-V13"
WAVE_SHA = "f1fba3c479d0e46057deb92d0460bf1d3c7d3cab"

# The 30 frozen quarterly decision dates, verbatim from
# p0_census_contract.json s0_decision_grid as restated in every proposal's
# clock.decision_grid. No subset; no added dates.
DECISION_GRID_30 = [
    "2018-04-04", "2018-07-03", "2018-10-02", "2019-01-03", "2019-04-04",
    "2019-07-05", "2019-10-03", "2020-01-03", "2020-04-03", "2020-07-06",
    "2020-09-10", "2020-12-09", "2021-03-12", "2021-06-11", "2021-09-10",
    "2021-12-09", "2022-03-11", "2022-06-10", "2022-09-12", "2022-12-09",
    "2023-02-17", "2023-05-19", "2023-08-21", "2023-11-17", "2024-02-21",
    "2024-05-21", "2024-08-21", "2024-11-19", "2025-02-24", "2025-05-23",
]

FIRST_WINDOW_LOWER_BOUND = "2018-01-01"   # grid-start open (census contract)
A6_WARMUP_DECISIONS = 3                   # A6 clock.warmup: decisions = 3
A6_SCORED_GRID = DECISION_GRID_30[A6_WARMUP_DECISIONS:]   # 27 scored dates

A4_P1_SHAM_SEED = 20260908   # proposal_A4_P1 control_arms.sham_insider_placebo
A4_P2_SHAM_SEED = 20260909   # proposal_A4_P2 control_arms.sham_insider_placebo
A5_SHAM_SEED = int(WAVE_SHA[:8], 16) % (2 ** 31)   # see module docstring

# A5 cited funded clocks (features_and_lags / clock.cited_funded_clocks)
A5_LTD = "us-gaap:LongTermDebtNoncurrent"
A5_ASSETS = "us-gaap:Assets"
A5_LIAB = "us-gaap:Liabilities"

# staged input paths (the same staging the machine's PATHS block declares)
STREAM_PATH = machine.V13_INTEG / ".staging_sec_v13/form4_stream.jsonl"
EODHD_DIV_DIR = machine.V13_INTEG / ".staging_sec_v13/eodhd_div"
EODHD_SPLITS_DIR = machine.V13_INTEG / ".staging_sec_v13/eodhd_splits"
MACRO_VINTAGED_DIR = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v8/integration"
    "/research/control/forex_free_v8_run/staged_vintaged")


def dd(s):
    return date.fromisoformat(s)


def _new_diag():
    return {
        "acceptance_fallback_to_filing_date_rows": 0,
        "direction_defect_rows_excluded": 0,
        "identity_defect_rows_excluded": 0,
        "sham_unmapped_sector_rows_excluded": 0,
        "div_window_formation_abstains": 0,
        "div_entities_without_staged_file": 0,
        "div_undated_records_excluded": 0,
        "div_unreadable_files": 0,
        "split_defect_unity_abstains": 0,
        "split_defect_unparsable_abstains": 0,
        "split_unreadable_files": 0,
        "macro_missing_asof_dates": 0,
    }


# ===========================================================================
# small shared helpers
# ===========================================================================
def _norm_name(s):
    return " ".join(str(s or "").upper().split())


def _owner_identity(row, issuer_cik):
    """Frozen identity rule: rptOwnerCik if present else normalized
    rptOwnerName + issuer CIK."""
    oc = row.get("owner_cik")
    if oc not in (None, ""):
        return "CIK:" + "".join(ch for ch in str(oc) if ch.isdigit())
    nm = _norm_name(row.get("owner_name"))
    if not nm:
        return None        # defect: neither owner field present
    return "NAME:" + nm + "|" + issuer_cik


def _pit_stamp(row, diag):
    """PIT = acceptance timestamp; the filingDate date-only fallback has
    0 measured occurrences per the frozen census - any occurrence counted."""
    a = row.get("acceptance") or ""
    if a:
        return str(a)
    fd = str(row.get("filing_date") or "")
    if fd:
        diag["acceptance_fallback_to_filing_date_rows"] += 1
    return fd


def _is_g_stream_row(r, diag):
    """Frozen stream_rule: nonDerivativeTable ONLY, the census contract's
    open-market primary observable (the non-derivative A/D code G class).
    Direction '.' or missing => FAIL-CLOSED to the defect table."""
    if str(r.get("table", "")).strip().lower() != "nonderivative":
        return False
    if str(r.get("transaction_code", "")).strip() != "G":
        return False
    if r.get("direction") not in ("A", "D"):
        diag["direction_defect_rows_excluded"] += 1
        return False
    return True


def _filter_stream(stream_rows, bookable, diag):
    out = []
    for r in stream_rows:
        cik = r.get("cik")
        if cik not in bookable:
            continue
        if not _is_g_stream_row(r, diag):
            continue
        if _owner_identity(r, cik) is None:
            diag["identity_defect_rows_excluded"] += 1
            continue
        out.append(r)
    out.sort(key=lambda r: (r["cik"], _pit_stamp(r, diag),
                            str(r.get("accession") or "")))
    return out


def _windows(grid):
    """(prev(D), D] pairs; the first decision date's lower bound is the
    2018-01-01 grid-start open (frozen census contract)."""
    out = []
    for i, t in enumerate(grid):
        lo = grid[i - 1] if i > 0 else FIRST_WINDOW_LOWER_BOUND
        out.append((lo, t))
    return out


# ===========================================================================
# A4 (Form-4 stream) exposures
# ===========================================================================
def _netdir(win_rows, min_rows):
    """netdir = (I_buy - I_sell)/(I_buy + I_sell) over distinct reporting-
    owner identities. P1 definition floor: >= 2 identities AND >= 3 in-window
    stream rows. P2 definition floor: >= 2 in-window qualifying rows (the
    identity count is >= 1 whenever rows >= 2, never zero: rows carry
    identities by construction here). None = abstain."""
    buys, sells = set(), set()
    for r in win_rows:
        ident = _owner_identity(r, r["cik"])
        (buys if r["direction"] == "A" else sells).add(ident)
    ib, isell = len(buys), len(sells)
    if len(win_rows) < min_rows or ib + isell < 2:
        return None
    return (ib - isell) / (ib + isell)


def a4_p1_anchor_exposure(stream_rows, bookable, grid, diag=None):
    """SFV13-A4-P1 netdir(e,t) (features_and_lags verbatim)."""
    diag = diag if diag is not None else _new_diag()
    rows = _filter_stream(stream_rows, bookable, diag)
    by_ent = {}
    for r in rows:
        by_ent.setdefault(r["cik"], []).append(r)
    out = {}
    for cik in sorted(by_ent):
        stamped = [(_pit_stamp(r, diag), r) for r in by_ent[cik]]
        stamped.sort(key=lambda sr: (sr[0], str(sr[1].get("accession") or "")))
        for lo, hi in _windows(grid):
            win = [r for s, r in stamped if s and lo < s <= hi]
            v = _netdir(win, min_rows=3)
            if v is not None:
                out[(cik, hi)] = v
    return out


def _routine_class_hist(rows):
    """(cik, identity, acceptance MONTH-OF-YEAR) -> sorted list of acceptance
    stamps, the classification history substrate (direction-free by
    construction). Month-of-year (s[5:7]) is the matching key; the year is
    read per candidate stamp at classification time."""
    hist = {}
    for r in rows:
        ident = _owner_identity(r, r["cik"])
        s = r.get("acceptance") or r.get("filing_date") or ""
        if len(s) < 7:
            continue
        hist.setdefault((r["cik"], ident, s[5:7]), []).append(s)
    for k in hist:
        hist[k].sort()
    return hist


def _is_routine(row, hist, prev_lo, diag):
    """Frozen classification_rule_frozen (proposal_A4_P2): a stream row of
    identity i on issuer e accepted in (prev(D), D] is ROUTINE iff identity i
    has >= 1 accepted stream row on the same issuer with the same ACCEPTANCE
    month-of-year in at least 2 of the 3 prior calendar years, where candidate
    prior rows are those with acceptance < prev(D); otherwise OPPORTUNISTIC.
    Month-of-year matching uses the acceptance month, never transactionDate."""
    s = row.get("acceptance") or row.get("filing_date") or ""
    if len(s) < 7:
        return False
    ident = _owner_identity(row, row["cik"])
    month_of_year = s[5:7]
    year = int(s[:4])
    cand = hist.get((row["cik"], ident, month_of_year), [])
    years = {c[:4] for c in cand if c < prev_lo}
    hits = sum(1 for yy in (year - 1, year - 2, year - 3) if str(yy) in years)
    return hits >= 2


def a4_p2_anchor_exposure(stream_rows, bookable, grid, diag=None):
    """SFV13-A4-P2 netdir_opp(e,t): the P1 direction form over the
    OPPORTUNISTIC subset; DEFINED iff >= 2 in-window opportunistic rows."""
    diag = diag if diag is not None else _new_diag()
    rows = _filter_stream(stream_rows, bookable, diag)
    hist = _routine_class_hist(rows)
    by_ent = {}
    for r in rows:
        by_ent.setdefault(r["cik"], []).append(r)
    out = {}
    for cik in sorted(by_ent):
        stamped = [(_pit_stamp(r, diag), r) for r in by_ent[cik]]
        stamped.sort(key=lambda sr: (sr[0], str(sr[1].get("accession") or "")))
        for lo, hi in _windows(grid):
            win = [r for s, r in stamped if s and lo < s <= hi]
            opp = [r for r in win if not _is_routine(r, hist, lo, diag)]
            v = _netdir(opp, min_rows=2)
            if v is not None:
                out[(cik, hi)] = v
    return out


def a4_sham_exposure(stream_rows, bookable, grid, seed, opportunistic,
                     diag=None, permutor=None):
    """A4 sham_insider_placebo (control_arms verbatim): for each decision
    date and sector tag, permute the direction code (A/D) uniformly across ALL
    in-window stream rows of that sector's entities (CIK-sorted,
    acceptance-ordered), numpy PCG64 (default_rng) frozen seed, one
    permutation drawn per cell in decision-date session order, then recompute
    the full anchor machinery on the permuted stream. For P2 the frozen
    classification is direction-free and survives the permutation UNCHANGED
    (it is recomputed anyway, per the frozen construction). The permutation
    preserves each cell's direction-count marginal EXACTLY.
    `permutor(dirs) -> dirs'` is injectable for known-answer selfchecks;
    default is numpy default_rng(seed)."""
    import numpy as np
    diag = diag if diag is not None else _new_diag()
    rows = _filter_stream(stream_rows, bookable, diag)
    rng = None if permutor is not None else np.random.default_rng(seed)
    new_rows = [None] * len(rows)
    filled = set()
    for lo, hi in _windows(grid):                      # decision-date order
        by_sec = {}
        for i, r in enumerate(rows):
            s = r.get("acceptance") or r.get("filing_date") or ""
            if not (s and lo < s <= hi):
                continue
            sec = bookable[r["cik"]]["sector"]
            if not sec:
                diag["sham_unmapped_sector_rows_excluded"] += 1
                continue
            by_sec.setdefault(sec, []).append((i, r))
        for sec in sorted(by_sec):                     # sector-sorted per cell
            cell = sorted(by_sec[sec],
                          key=lambda ir: (ir[1]["cik"],
                                          ir[1].get("acceptance")
                                          or ir[1].get("filing_date") or "",
                                          str(ir[1].get("accession") or "")))
            dirs = [r["direction"] for _i, r in cell]
            if permutor is not None:
                pd = list(permutor(dirs))
            else:
                pd = [dirs[j] for j in rng.permutation(len(dirs))]
            if len(pd) != len(dirs):
                raise ValueError("permutor length mismatch")
            for (i, r), nd in zip(cell, pd):
                if nd not in ("A", "D"):
                    raise ValueError("permuted direction must remain A/D")
                new_rows[i] = dict(r, direction=nd)
                filled.add(i)
    for i, r in enumerate(rows):
        if i not in filled:
            new_rows[i] = r
    if opportunistic:
        return a4_p2_anchor_exposure(new_rows, bookable, grid, diag)
    return a4_p1_anchor_exposure(new_rows, bookable, grid, diag)


def arrival_exposure(accepts, bookable, grid, diag=None):
    """filing_arrival_exposure_form (both A4 proposals): exposure_arr(e,t) =
    log1p(n4(e,t)), n4 = count of the entity's Form-4 acceptances of ANY kind
    in (prev(D), D] from load_form4_acceptances() (filing level: all tables,
    all codes, no direction, no identity); defined iff n4 >= 1."""
    diag = diag if diag is not None else _new_diag()
    out = {}
    for cik in sorted(bookable):
        accs = accepts.get(cik) or []
        for lo, hi in _windows(grid):
            n4 = 0
            for fd, ad in accs:
                stamp = ad if ad else fd
                if stamp and lo < stamp <= hi:
                    n4 += 1
            if n4 >= 1:
                out[(cik, hi)] = math.log1p(n4)
    return out


# ===========================================================================
# A5 (panel percentile x macro regime weight) exposures
# ===========================================================================
def macro_asof_values(vrows, grid):
    """vintaged as-of reconstruction verbatim: value in effect at decision D
    = the row with realtime_start <= D, the latest such row; no interpolation,
    no revision re-picking. Returns one float or None per grid date ('.' or
    unparsable at the selected row = fail-closed abstention; the proposals
    measure the series as-of bindable 30/30 so this should never fire)."""
    out = []
    for d in grid:
        cands = [r for r in vrows
                 if str(r.get("realtime_start", "")) <= d]
        if not cands:
            out.append(None)
            continue
        latest = max(cands, key=lambda r: (str(r.get("realtime_start", "")),
                                           str(r.get("date") or "")))
        try:
            v = float(latest.get("value"))
        except (TypeError, ValueError):
            out.append(None)
            continue
        out.append(v if v == v else None)   # NaN guard
    return out


def regime_weights(asof_vals, forced_mid=5):
    """Frozen expanding-percentile rule (both A5 proposals):
    p_i = #{j <= i : r_j <= r_i} / i over the as-of values of the frozen
    decision dates themselves (i is 1-based); HIGH w=1.0 iff p_i >= 2/3,
    LOW w=0.0 iff p_i <= 1/3, MID w=0.5 otherwise; ties resolved by the <= in
    the count definition; FORCED MID on the first five decision dates
    (indices 0-4). Band comparisons exact via integer cross-multiplication.
    Returns None if any as-of value is missing (fail-closed)."""
    if any(v is None for v in asof_vals):
        return None
    ws = []
    for i, r in enumerate(asof_vals):
        n = i + 1
        k = sum(1 for j in range(n) if asof_vals[j] <= r)
        if i < forced_mid:
            w = 0.5
        elif 3 * k >= 2 * n:
            w = 1.0
        elif 3 * k <= n:
            w = 0.0
        else:
            w = 0.5
        ws.append(w)
    return ws


def block_permutation(weights, rng):
    """Duration-preserving block permutation (sham_macro_placebo verbatim):
    partition the weight vector into its maximal contiguous blocks of equal w
    (every block's length and label multiset survives; only block ORDER is
    permuted), permuted once by the caller's numpy generator."""
    blocks = []
    for i, w in enumerate(weights):
        if blocks and blocks[-1][0] == w:
            blocks[-1][1].append(i)
        else:
            blocks.append([w, [i]])
    order = list(rng.permutation(len(blocks)))
    out = [0.0] * len(weights)
    pos = 0
    for b in order:
        w, idxs = blocks[b]
        for _i in idxs:                 # lay blocks back-to-back, permuted
            out[pos] = w
            pos += 1
    return out


def _asof_panel_value(lst, t_iso):
    """Selected vintage = max avail among rows with avail < t (strict) - the
    machine's panel gate semantics (never the latest vintage in the store).
    lst: sorted [(avail, eff, v)]."""
    lo, hi = 0, len(lst)
    while lo < hi:
        mid = (lo + hi) // 2
        if lst[mid][0] < t_iso:
            lo = mid + 1
        else:
            hi = mid
    if lo == 0:
        return None
    return lst[lo - 1][2]


def a5_exposures(panel_fields, bookable, grid, weights, num_field, den_field,
                 orientation):
    """SFV13-A5 anchor exposure: within-sector percentile of the as-of ratio
    times the regime weight. orientation 'low' -> w * (1 - pct) (P1 anchor,
    long-bottom/short-top L); orientation 'high' -> w * pct (P2 anchor,
    long-high/short-low G). pct(e) = #{peers with ratio <= e's} / n_defined
    within the sector at the decision. weights None (macro as-of abstention)
    -> {} (fail-closed; the machine's BLOCKED_EXPOSURE_UNDEFINED path)."""
    if weights is None:
        return {}
    out = {}
    for t_idx, t in enumerate(grid):
        w = weights[t_idx]
        ratios = {}
        for e in sorted(bookable):
            num = _asof_panel_value(panel_fields.get((e, num_field), []), t)
            den = _asof_panel_value(panel_fields.get((e, den_field), []), t)
            if num is None or den is None or den <= 0:
                continue
            ratios[e] = num / den
        by_sec = {}
        for e, v in ratios.items():
            by_sec.setdefault(bookable[e]["sector"], []).append((e, v))
        for sec in sorted(by_sec):
            lst = by_sec[sec]
            n = len(lst)
            for e, v in lst:
                k = sum(1 for _e2, v2 in lst if v2 <= v)
                pct = k / n
                base = (1.0 - pct) if orientation == "low" else pct
                out[(e, t)] = w * base
    return out


# ===========================================================================
# A6 (EODHD corporate-action states) exposures
# ===========================================================================
def _div_ex_dates(recs, diag):
    """Vendor-recorded EX-DATE per record (explicit 'ex_date' field if
    present, else the vendor 'date' field); undated records excluded-counted."""
    ex = []
    for r in recs:
        if not isinstance(r, dict):
            diag["div_undated_records_excluded"] += 1
            continue
        s = str(r.get("ex_date") or r.get("date") or "")
        if not s:
            diag["div_undated_records_excluded"] += 1
            continue
        ex.append(s)
    return sorted(ex)


def a6_div_exposures(div_by_ticker, ticker_of, bookable, grid, diag=None):
    """SFV13-A6-P1 dividend transition state X_i(D) on the SCORED grid dates
    (first three grid dates are declared warmup): paid_now = count of records
    with ex_date in [D-365, D); paid_prev = count in [D-730, D-365);
    X = +1 iff paid_prev == 0 and paid_now >= 1 (initiation); -1 iff
    paid_prev >= 1 and paid_now == 0 (omission); 0 otherwise. Absence
    assertability gate verbatim: paid_prev is treated as a ZERO only if the
    entity's earliest staged ex_date <= D - 730 (or the prior window holds
    >= 1 record, i.e. paid_prev >= 1); otherwise the entity ABSTAINS
    (window-formation abstain). Absent staged file = no data -> abstain."""
    diag = diag if diag is not None else _new_diag()
    out = {}
    for cik in sorted(bookable):
        tkr = ticker_of.get(cik)
        recs = div_by_ticker.get(tkr) if tkr else None
        if tkr and tkr in div_by_ticker and recs is None:
            diag["div_unreadable_files"] += 1
        if not recs:
            diag["div_entities_without_staged_file"] += 1
            continue
        ex = _div_ex_dates(recs, diag)
        earliest = ex[0] if ex else None
        for d in grid[A6_WARMUP_DECISIONS:]:
            ddate = dd(d)
            lo_now = (ddate - timedelta(days=365)).isoformat()
            lo_prev = (ddate - timedelta(days=730)).isoformat()
            paid_now = sum(1 for s in ex if lo_now <= s < d)
            paid_prev = sum(1 for s in ex if lo_prev <= s < lo_now)
            if paid_prev == 0 and not (earliest is not None
                                       and earliest <= lo_prev):
                diag["div_window_formation_abstains"] += 1
                continue
            if paid_prev == 0 and paid_now >= 1:
                x = 1.0
            elif paid_prev >= 1 and paid_now == 0:
                x = -1.0
            else:
                x = 0.0
            out[(cik, d)] = x
    return out


def _split_ratio(r):
    raw = r.get("split", r.get("ratio", r.get("split_factor")))
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    return v if v == v else None


def a6_split_exposures(splits_by_ticker, ticker_of, bookable, grid, diag=None):
    """SFV13-A6-P2 split-direction state on the SCORED grid dates: most
    recent staged split with split date in [D-180, D): +1 if ratio > 1,
    -1 if ratio < 1, 0 if none (the declared default - the family has no
    baseline window, absence assertions NOT required). A most-recent in-window
    ratio of exactly 1 or unparsable FAILS CLOSED to the defect table
    (abstain, counted). Absent staged file = no records = state 0; a PRESENT
    but unreadable file is a measurement failure -> abstain (never 0)."""
    diag = diag if diag is not None else _new_diag()
    out = {}
    for cik in sorted(bookable):
        tkr = ticker_of.get(cik)
        recs = splits_by_ticker.get(tkr) if tkr else None
        rows = []
        if tkr and tkr in splits_by_ticker and recs is None:
            diag["split_unreadable_files"] += 1
            recs = None
            unreadable = True
        else:
            unreadable = False
        if recs:
            for r in recs:
                if not isinstance(r, dict):
                    continue
                d0 = str(r.get("date") or r.get("split_date") or "")
                if d0:
                    rows.append((d0, r))
            rows.sort(key=lambda sr: (sr[0], str(sr[1].get("split"))))
        for d in grid[A6_WARMUP_DECISIONS:]:
            if unreadable:
                continue                       # measurement failure: abstain
            lo = (dd(d) - timedelta(days=180)).isoformat()
            win = [sr for sr in rows if lo <= sr[0] < d]
            if not win:
                out[(cik, d)] = 0.0
                continue
            _s0, r0 = win[-1]                  # most recent in window
            ratio = _split_ratio(r0)
            if ratio is None:
                diag["split_defect_unparsable_abstains"] += 1
                continue
            if ratio == 1.0:
                diag["split_defect_unity_abstains"] += 1
                continue
            out[(cik, d)] = 1.0 if ratio > 1.0 else -1.0
    return out


def within_sector_hash_permutation_sham(anchor, bookable, hyp):
    """A6 within-sector permutation control (control_arms verbatim): at each
    scored decision date, the anchor's exposure VALUES are permuted across
    that date's entities INSIDE each mapped sector tag using the frozen
    deterministic hash order - sha256 of the string
    cycle|{hypothesis_id}|{cik}|{decision_index}, hex-sorted, no RNG library.
    Preserves the exact within-date and within-sector multiset of states."""
    out = {}
    for d in sorted({t for _c, t in anchor}):
        idx = DECISION_GRID_30.index(d)
        cells = {}
        for (cik, t), v in anchor.items():
            if t == d:
                cells.setdefault(bookable[cik]["sector"], []).append(cik)
        for sec in sorted(cells):
            names = sorted(cells[sec])
            keyed = sorted(
                names,
                key=lambda c: hashlib.sha256(
                    f"{CYCLE}|{hyp}|{c}|{idx}".encode()).hexdigest())
            vals = sorted(anchor[(c, d)] for c in names)
            for c, v in zip(keyed, vals):
                out[(c, d)] = v
    return out


# ===========================================================================
# context wiring (lazy loaders cached on the machine context)
# ===========================================================================
def _cache(C):
    c = getattr(C, "_d2p_cache", None)
    if c is None:
        c = C._d2p_cache = {}
    return c


def _bookable(C, cache):
    if "bookable" not in cache:
        cohort = json.loads(machine.COHORT.read_text())
        b = {}
        for cls in ("ALIVE_EVIDENCED", "DEAD_EVIDENCED"):
            for m in cohort["members"][cls]:
                b[m["cik"]] = {"sector": m.get("sector", ""),
                               "ticker": m.get("ticker")
                               or m.get("ticker_eodhd") or ""}
        cache["bookable"] = b
    return cache["bookable"]


def _stream_rows(C, cache):
    if "form4_stream_rows" not in cache:
        rows = []
        if STREAM_PATH.exists():
            with open(STREAM_PATH, buffering=1 << 20) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
        cache["form4_stream_rows"] = rows
    return cache["form4_stream_rows"]


def _accepts(C, cache):
    if "form4_accepts" not in cache:
        cache["form4_accepts"] = machine.load_form4_acceptances()
    return cache["form4_accepts"]


def _a5_panel_fields(C, cache):
    if "a5_panel_fields" not in cache:
        want = {A5_LTD, A5_ASSETS, A5_LIAB}
        fields = {}
        with open(machine.PANEL, buffering=1 << 20) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("f") in want and isinstance(r.get("v"), (int, float)):
                    fields.setdefault((r["e"], r["f"]), []).append(
                        (r["avail"], r["eff"], float(r["v"])))
        for k in fields:
            fields[k].sort()
        cache["a5_panel_fields"] = fields
    return cache["a5_panel_fields"]


def _macro_vintages(C, cache, series):
    key = f"macro_vintages_{series}"
    if key not in cache:
        p = MACRO_VINTAGED_DIR / f"{series}.json"
        try:
            cache[key] = json.loads(p.read_text())
        except Exception:
            cache[key] = None
    return cache[key]


def _eodhd_dir(C, cache, ddir, key):
    if key not in cache:
        m = {}
        if ddir.is_dir():
            for p in sorted(ddir.glob("*.json")):
                try:
                    m[p.name[:-len(".json")]] = json.loads(p.read_text())
                except Exception:
                    m[p.name[:-len(".json")]] = None   # unreadable
        cache[key] = m
    return cache[key]


# ===========================================================================
# registered handlers (contract: handler(C) -> {(cik, iso_date_str): float})
# ===========================================================================
def h_a4_p1(C):
    cache = _cache(C)
    return a4_p1_anchor_exposure(_stream_rows(C, cache),
                                 _bookable(C, cache), DECISION_GRID_30,
                                 cache.setdefault("diag:SFV13-A4-P1",
                                                  _new_diag()))


def h_a4_p2(C):
    cache = _cache(C)
    return a4_p2_anchor_exposure(_stream_rows(C, cache),
                                 _bookable(C, cache), DECISION_GRID_30,
                                 cache.setdefault("diag:SFV13-A4-P2",
                                                  _new_diag()))


def h_sham_a4_p1(C):
    cache = _cache(C)
    return a4_sham_exposure(_stream_rows(C, cache), _bookable(C, cache),
                            DECISION_GRID_30, A4_P1_SHAM_SEED, False,
                            cache.setdefault("diag:sham_a4_p1", _new_diag()))


def h_sham_a4_p2(C):
    cache = _cache(C)
    return a4_sham_exposure(_stream_rows(C, cache), _bookable(C, cache),
                            DECISION_GRID_30, A4_P2_SHAM_SEED, True,
                            cache.setdefault("diag:sham_a4_p2", _new_diag()))


def h_arrival(C):
    cache = _cache(C)
    return arrival_exposure(_accepts(C, cache), _bookable(C, cache),
                            DECISION_GRID_30,
                            cache.setdefault("diag:arrival", _new_diag()))


def _a5_weights(C, cache, series):
    key = f"weights_{series}"
    if key not in cache:
        vrows = _macro_vintages(C, cache, series)
        vals = (macro_asof_values(vrows, DECISION_GRID_30)
                if isinstance(vrows, list) else [None] * len(DECISION_GRID_30))
        if any(v is None for v in vals):
            cache[key] = None           # fail-closed: not as-of bindable
            d = cache.setdefault("diag:macro", _new_diag())
            d["macro_missing_asof_dates"] += sum(
                1 for v in vals if v is None)
        else:
            cache[key] = regime_weights(vals, forced_mid=5)
    return cache[key]


def h_a5_p1(C):
    cache = _cache(C)
    return a5_exposures(_a5_panel_fields(C, cache), _bookable(C, cache),
                        DECISION_GRID_30, _a5_weights(C, cache, "DFII10"),
                        A5_LTD, A5_ASSETS, "low")


def h_a5_p2(C):
    cache = _cache(C)
    return a5_exposures(_a5_panel_fields(C, cache), _bookable(C, cache),
                        DECISION_GRID_30, _a5_weights(C, cache, "T10YIE"),
                        A5_LIAB, A5_ASSETS, "high")


def h_sham_a5_p1(C):
    import numpy as np
    cache = _cache(C)
    w = _a5_weights(C, cache, "DFII10")
    if w is None:
        return {}
    key = "sham_weights_DFII10"
    if key not in cache:
        cache[key] = block_permutation(w, np.random.default_rng(A5_SHAM_SEED))
    return a5_exposures(_a5_panel_fields(C, cache), _bookable(C, cache),
                        DECISION_GRID_30, cache[key],
                        A5_LTD, A5_ASSETS, "low")


def h_sham_a5_p2(C):
    import numpy as np
    cache = _cache(C)
    w = _a5_weights(C, cache, "T10YIE")
    if w is None:
        return {}
    key = "sham_weights_T10YIE"
    if key not in cache:
        cache[key] = block_permutation(w, np.random.default_rng(A5_SHAM_SEED))
    return a5_exposures(_a5_panel_fields(C, cache), _bookable(C, cache),
                        DECISION_GRID_30, cache[key],
                        A5_LIAB, A5_ASSETS, "high")


def h_dgs10_a5_p1(C):
    cache = _cache(C)
    return a5_exposures(_a5_panel_fields(C, cache), _bookable(C, cache),
                        DECISION_GRID_30, _a5_weights(C, cache, "DGS10"),
                        A5_LTD, A5_ASSETS, "low")


def h_dgs10_a5_p2(C):
    cache = _cache(C)
    return a5_exposures(_a5_panel_fields(C, cache), _bookable(C, cache),
                        DECISION_GRID_30, _a5_weights(C, cache, "DGS10"),
                        A5_LIAB, A5_ASSETS, "high")


def h_a6_p1(C):
    cache = _cache(C)
    bookable = _bookable(C, cache)
    divs = _eodhd_dir(C, cache, EODHD_DIV_DIR, "eodhd_div")
    ticker_of = {cik: b["ticker"] for cik, b in bookable.items()}
    return a6_div_exposures(divs, ticker_of, bookable, DECISION_GRID_30,
                            cache.setdefault("diag:SFV13-A6-P1", _new_diag()))


def h_a6_p2(C):
    cache = _cache(C)
    bookable = _bookable(C, cache)
    splits = _eodhd_dir(C, cache, EODHD_SPLITS_DIR, "eodhd_splits")
    ticker_of = {cik: b["ticker"] for cik, b in bookable.items()}
    return a6_split_exposures(splits, ticker_of, bookable, DECISION_GRID_30,
                              cache.setdefault("diag:SFV13-A6-P2",
                                               _new_diag()))


def _h_a6_sham(hyp, anchor_key):
    def _handler(C):
        cache = _cache(C)
        anchor = cache.get(anchor_key)
        if anchor is None:
            builder = ANCHOR_BUILDERS[
                "SFV13-A6-P1" if hyp.endswith("H1") else "SFV13-A6-P2"]
            anchor = builder(C)
            cache[anchor_key] = anchor
        return within_sector_hash_permutation_sham(
            anchor, _bookable(C, cache), hyp)
    return _handler


# ---------------------------------------------------------------------------
# REGISTRATION (import side-effect): SIX anchors into the machine's registry
# ---------------------------------------------------------------------------
ANCHOR_BUILDERS = {
    "SFV13-A4-P1": h_a4_p1,
    "SFV13-A4-P2": h_a4_p2,
    "SFV13-A5-P1": h_a5_p1,
    "SFV13-A5-P2": h_a5_p2,
    "SFV13-A6-P1": h_a6_p1,
    "SFV13-A6-P2": h_a6_p2,
}

machine.PROPOSAL_EXPOSURE_BUILDERS.update(ANCHOR_BUILDERS)

# Control builders (NOT in the machine's anchor registry - the machine's
# run_full measures registry entries as anchors; controls are measured by the
# execution lane through identifiability_anchor_vs_control).
# ctrl_gate None = no pooled-rho control gate is declared for that control;
# the runner then applies only the universally declared self-subsumption
# bound (0.98) and marks the operative kill as the book-level expectancy rule
# evaluated at scoring, per each proposal's falsification_rule.
_SELF_SUB_BASIS = (
    "no pooled-rho control gate declared in the proposal; 0.98 is the "
    "universally declared self-subsumption bound (falsification rule 3); the "
    "operative kill is the book-level same-sign >= 0.5x expectancy rule "
    "evaluated at scoring")
_DECLARED_A4_SHAM = {
    "gate_basis": "declared d2_predeclarations.anchor_vs_sham_identifiability",
}

PROPOSAL_CONTROL_BUILDERS = {
    "SFV13-A4-P1": {
        "sham_insider_placebo": {"builder": h_sham_a4_p1, "ctrl_gate": 0.30,
                                 "per_date_gate": 0.30, "date_pass_share": 0.90,
                                 "gate_basis": _DECLARED_A4_SHAM["gate_basis"]},
        "filing_arrival_exposure_form": {"builder": h_arrival,
                                         "ctrl_gate": None,
                                         "gate_basis": _SELF_SUB_BASIS},
    },
    "SFV13-A4-P2": {
        "sham_insider_placebo": {"builder": h_sham_a4_p2, "ctrl_gate": 0.30,
                                 "per_date_gate": 0.30, "date_pass_share": 0.90,
                                 "gate_basis": _DECLARED_A4_SHAM["gate_basis"]},
        "filing_arrival_exposure_form": {"builder": h_arrival,
                                         "ctrl_gate": None,
                                         "gate_basis": _SELF_SUB_BASIS},
    },
    "SFV13-A5-P1": {
        "sham_macro_placebo": {"builder": h_sham_a5_p1, "ctrl_gate": None,
                               "gate_basis": _SELF_SUB_BASIS},
        "exposure_form_control_dgs10": {"builder": h_dgs10_a5_p1,
                                        "ctrl_gate": None,
                                        "gate_basis": _SELF_SUB_BASIS},
    },
    "SFV13-A5-P2": {
        "sham_macro_placebo": {"builder": h_sham_a5_p2, "ctrl_gate": None,
                               "gate_basis": _SELF_SUB_BASIS},
        "exposure_form_control_dgs10": {"builder": h_dgs10_a5_p2,
                                        "ctrl_gate": None,
                                        "gate_basis": _SELF_SUB_BASIS},
    },
    "SFV13-A6-P1": {
        "within_sector_permutation": {
            "builder": _h_a6_sham("SFV13-A6-H1", "anchor:a6_p1"),
            "ctrl_gate": None, "gate_basis": _SELF_SUB_BASIS},
    },
    "SFV13-A6-P2": {
        "within_sector_permutation": {
            "builder": _h_a6_sham("SFV13-A6-H2", "anchor:a6_p2"),
            "ctrl_gate": None, "gate_basis": _SELF_SUB_BASIS},
    },
}


# ===========================================================================
# SELFCHECK - tiny synthetic fixtures, hand-computed expected answers
# ===========================================================================
def _E(n):
    return f"CIK{n:010d}"


E1, E2, E3, E4 = _E(1), _E(2), _E(3), _E(4)
E5, E6, E7, E8, E9, E10 = (_E(5), _E(6), _E(7), _E(8), _E(9), _E(10))
D1, D2 = "2018-04-04", "2018-07-03"
GRID2 = [D1, D2]


def _row(cik, owner_cik, direction, stamp, code="G", table="nonDerivative",
         owner_name=None, shares="100"):
    return {"cik": cik, "accession": f"ACC-{cik}-{stamp}-{owner_cik}",
            "acceptance": stamp, "filing_date": stamp[:10],
            "transaction_date": stamp[:10], "transaction_code": code,
            "direction": direction, "shares": shares,
            "owner_cik": owner_cik, "owner_name": owner_name, "table": table}


def _approx(a, b, eps=1e-12):
    return a is not None and b is not None and abs(a - b) <= eps


def selfcheck() -> int:
    fails = []

    def check(name, cond, msg=""):
        if not cond:
            fails.append(f"{name}: {msg}")

    check("registry_six_anchors",
          set(machine.PROPOSAL_EXPOSURE_BUILDERS) == set(ANCHOR_BUILDERS)
          and len(machine.PROPOSAL_EXPOSURE_BUILDERS) == 6,
          str(sorted(machine.PROPOSAL_EXPOSURE_BUILDERS)))
    check("a5_seed_formula", A5_SHAM_SEED == 1912316868,
          f"{A5_SHAM_SEED} (proposal text asserts 1911101388; the formula "
          f"int('f1fba3c4',16) % 2**31 is normative - see module docstring)")
    check("a6_scored_grid", len(A6_SCORED_GRID) == 27
          and A6_SCORED_GRID[0] == "2019-01-03")

    # ---- A4-P1 netdir: identity dedup, floors, gate boundary ---------------
    diag1 = _new_diag()
    stream1 = [
        # window 1 (2018-01-01, 2018-04-04]
        _row(E1, "9001", "A", "2018-03-01T16:30:00.000Z"),   # O1 buy
        _row(E1, "9001", "D", "2018-03-02T16:30:00.000Z"),   # O1 sell
        _row(E1, "9002", "A", "2018-03-05T16:30:00.000Z"),   # O2 buy
        _row(E2, "9003", "D", "2018-02-01T16:30:00.000Z"),   # 1 identity -> floor
        _row(E3, "9004", "A", "2018-03-01T16:30:00.000Z"),   # O4 buy x2 (dedup)
        _row(E3, "9004", "A", "2018-03-02T16:30:00.000Z"),
        _row(E3, None, "A", "2018-03-03T16:30:00.000Z",
             owner_name="john  smith"),                       # name identity
        # window 2 (2018-04-04, 2018-07-03]
        _row(E1, "9001", "A", "2018-06-01T16:30:00.000Z"),
        _row(E1, "9002", "D", "2018-06-02T16:30:00.000Z"),
        _row(E1, "9002", "D", "2018-06-03T16:30:00.000Z"),
        _row(E1, "9009", "D", "2018-07-03T10:00:00.000Z"),   # AFTER D2 gate: out
        _row(E2, "9003", "A", "2018-05-01T16:30:00.000Z"),   # one identity,
        _row(E2, "9003", "D", "2018-05-02T16:30:00.000Z"),   # 3 rows -> 0.0
        _row(E2, "9003", "A", "2018-05-03T16:30:00.000Z"),
        _row(E3, "9006", "A", "2018-04-04T09:00:00.000Z"),   # IN window 2
        _row(E3, "9007", "A", "2018-04-05T16:30:00.000Z"),
        _row(E3, "9008", "D", "2018-06-15T16:30:00.000Z"),
        # defect rows: must never enter any window
        _row(E2, "9003", "A", "2018-03-01T16:30:00.000Z", code="P"),
        _row(E2, "9003", "A", "2018-03-01T16:30:00.000Z", table="derivative"),
    ]
    stream1.append({"cik": E2, "accession": "ACC-x", "acceptance": "",
                    "filing_date": "2018-03-10", "transaction_date": "2018-03-10",
                    "transaction_code": "G", "direction": "x", "shares": "1",
                    "owner_cik": "9003", "owner_name": None,
                    "table": "nonDerivative"})            # direction defect
    book1 = {E1: {"sector": "XLF", "ticker": "T1"},
             E2: {"sector": "XLF", "ticker": "T2"},
             E3: {"sector": "XLK", "ticker": "T3"}}
    p1 = a4_p1_anchor_exposure(stream1, book1, GRID2, diag1)
    third = 1.0 / 3.0
    # E1 w1: I_buy={O1,O2}=2, I_sell={O1}=1 -> (2-1)/3 = 1/3 (floor 3 id 3 OK)
    check("a4p1_e1_w1", _approx(p1.get((E1, D1)), third), str(p1.get((E1, D1))))
    # E3 w1: buys {O4, JOHN SMITH|E3}=2, sells {} -> 1.0
    check("a4p1_e3_w1", p1.get((E3, D1)) == 1.0, str(p1.get((E3, D1))))
    # E2 w1: single identity (1 buy id) -> sum 1 < 2 -> abstain
    check("a4p1_e2_w1_abstain", (E2, D1) not in p1, str(p1.get((E2, D1))))
    # E1 w2: buys {O1}=1 sells {O2}=1 -> 0.0; the post-gate row must be OUT
    check("a4p1_e1_w2", p1.get((E1, D2)) == 0.0, str(p1.get((E1, D2))))
    # E2 w2: 3 rows 1 identity -> dedup -> 0.0 (rows floor met, identity floor 2)
    check("a4p1_e2_w2", p1.get((E2, D2)) == 0.0, str(p1.get((E2, D2))))
    # E3 w2: buys {O6(04-04 edge), O7}=2 sells {O8}=1 -> 1/3
    check("a4p1_e3_w2", _approx(p1.get((E3, D2)), third), str(p1.get((E3, D2))))
    check("a4p1_size", len(p1) == 5, str(sorted(p1)))
    check("a4p1_defects_counted",
          diag1["direction_defect_rows_excluded"] == 1
          and diag1["acceptance_fallback_to_filing_date_rows"] == 0,
          str(diag1))

    # ---- filing-arrival control --------------------------------------------
    acc1 = {E1: [("2018-03-01", "2018-03-01T16:30:00.000Z"),
                 ("2018-05-01", "2018-05-01T16:30:00.000Z"),
                 ("2018-06-01", "2018-06-01T16:30:00.000Z")],
            E2: [("2018-06-06", "2018-06-06T17:00:00.000Z")]}
    arr = arrival_exposure(acc1, book1, GRID2, _new_diag())
    # E1 w1: n4=1 -> log1p(1)=0.6931471805599453
    check("arr_e1_w1", _approx(arr.get((E1, D1)),
                               math.log1p(1)), str(arr.get((E1, D1))))
    # E1 w2: n4=2 -> log1p(2)=1.0986122886681098
    check("arr_e1_w2", _approx(arr.get((E1, D2)),
                               math.log1p(2)), str(arr.get((E1, D2))))
    check("arr_e2_w2", _approx(arr.get((E2, D2)), math.log1p(1)))
    check("arr_e3_absent", (E3, D1) not in arr and (E3, D2) not in arr)
    check("arr_size", len(arr) == 3, str(sorted(arr)))

    # ---- A4 sham: injected identity permutor -> anchor; reverse permutor ----
    def _identity(dirs):
        return list(dirs)

    sham_id = a4_sham_exposure(stream1, book1, GRID2, A4_P1_SHAM_SEED, False,
                               _new_diag(), permutor=_identity)
    check("a4sham_identity_eq_anchor", sham_id == p1,
          f"{sorted(sham_id.items())} vs {sorted(p1.items())}")

    def _reverse(dirs):
        return list(dirs)[::-1]

    sham_rev = a4_sham_exposure(stream1, book1, GRID2, A4_P1_SHAM_SEED, False,
                                _new_diag(), permutor=_reverse)
    # hand-computed (cells contain ALL in-window XLF rows, CIK-sorted; the
    # 2018-07-03T10:00 row is outside EVERY window - gate boundary):
    # w1 XLF cell rows [E1:03-01 A, 03-02 D, 03-05 A, E2:02-01 D] reversed
    # [D,A,D,A]: E1 buys{O1}=1 sells{O1,O2}=2 -> -1/3; E2 single row -> floor
    # abstain. E3 w1 [A,A,A] palindrome -> 1.0. w2 XLF cell [E1:06-01 A,
    # 06-02 D, 06-03 D, E2:05-01 A, 05-02 D, 05-03 A] reversed
    # [A,D,A,D,A,D]: E1 buys{O1,O2}=2 sells{O2}=1 -> 1/3; E2 buys{O3}=1
    # sells{O3}=1 -> 0.0. E3 w2 [A,A,D] reversed [D,A,A] -> buys 2 sells 1
    # -> 1/3.
    check("a4sham_reverse_e1_w1", _approx(sham_rev.get((E1, D1)), -third),
          str(sham_rev.get((E1, D1))))
    check("a4sham_reverse_e3_w1", sham_rev.get((E3, D1)) == 1.0,
          str(sham_rev.get((E3, D1))))
    check("a4sham_reverse_e1_w2", _approx(sham_rev.get((E1, D2)), third),
          str(sham_rev.get((E1, D2))))
    check("a4sham_reverse_e2_w2", sham_rev.get((E2, D2)) == 0.0,
          str(sham_rev.get((E2, D2))))
    check("a4sham_reverse_e3_w2", _approx(sham_rev.get((E3, D2)), third),
          str(sham_rev.get((E3, D2))))
    check("a4sham_reverse_size", len(sham_rev) == 5, str(sorted(sham_rev)))
    # real seed path: deterministic x2 and direction marginal preserved
    s_a = a4_sham_exposure(stream1, book1, GRID2, A4_P1_SHAM_SEED, False,
                           _new_diag())
    s_b = a4_sham_exposure(stream1, book1, GRID2, A4_P1_SHAM_SEED, False,
                           _new_diag())
    check("a4sham_determinism_x2", s_a == s_b, "two seed-path builds differ")
    # (direction marginals per cell preserved by construction of permutation;
    #  the values remain a permutation of per-cell direction multisets)
    all_rows = [_is_g_stream_row(r, _new_diag()) and r.get("cik") in book1
                for r in stream1]
    check("a4sham_stream_sane", sum(all_rows) >= 15)

    # ---- A4-P2 opportunistic classification --------------------------------
    diag2 = _new_diag()
    stream2 = [
        # E1/O1: 3 prior-year March rows -> ROUTINE for its w1 March row
        _row(E1, "9001", "A", "2017-03-01T16:30:00.000Z"),
        _row(E1, "9001", "A", "2016-03-01T16:30:00.000Z"),
        _row(E1, "9001", "D", "2015-03-01T16:30:00.000Z"),
        _row(E1, "9001", "A", "2018-03-01T16:30:00.000Z"),   # routine
        # E1/O2, O10: no history -> opportunistic (2 rows -> defined 0.0)
        _row(E1, "9002", "A", "2018-03-05T16:30:00.000Z"),
        _row(E1, "9010", "D", "2018-03-06T16:30:00.000Z"),
        # E1/O2 w2 June row: priors 2017-06 + 2016-06 -> routine -> E1 w2 abstain
        _row(E1, "9002", "A", "2017-06-01T16:30:00.000Z"),
        _row(E1, "9002", "A", "2016-06-01T16:30:00.000Z"),
        _row(E1, "9002", "A", "2018-06-01T16:30:00.000Z"),
        # E2/O12: exactly ONE prior-year March row -> OPPORTUNISTIC
        _row(E2, "9012", "A", "2017-03-25T16:30:00.000Z"),
        _row(E2, "9012", "A", "2018-03-25T16:30:00.000Z"),
        _row(E2, "9013", "D", "2018-03-26T16:30:00.000Z"),   # opp
        # E2/O4: month-05 priors in 2017+2016 AND a month-06 decoy -> routine
        _row(E2, "9004", "A", "2017-05-01T16:30:00.000Z"),
        _row(E2, "9004", "A", "2016-05-01T16:30:00.000Z"),
        _row(E2, "9004", "A", "2017-06-01T16:30:00.000Z"),   # wrong month
        _row(E2, "9004", "A", "2018-05-01T16:30:00.000Z"),   # routine
        _row(E2, "9004", "D", "2018-05-02T16:30:00.000Z"),   # routine
        # E3/O5: one prior-year March row -> opp; O6 opp; O7 opp; O8 x2 opp dedup
        _row(E3, "9005", "A", "2017-03-15T16:30:00.000Z"),
        _row(E3, "9005", "A", "2018-03-01T16:30:00.000Z"),   # opp (1 year < 2)
        _row(E3, "9006", "D", "2018-03-02T16:30:00.000Z"),   # opp
        _row(E3, "9007", "A", "2018-03-03T16:30:00.000Z"),   # opp
        _row(E3, "9008", "A", "2018-03-10T16:30:00.000Z"),   # opp (dedup x2)
        _row(E3, "9008", "A", "2018-03-11T16:30:00.000Z"),
        # E3 w2: two no-history opp rows
        _row(E3, "9014", "A", "2018-05-01T16:30:00.000Z"),
        _row(E3, "9015", "D", "2018-05-02T16:30:00.000Z"),
        # E4: two-identity opp pair -> 0.0
        _row(E4, "9020", "A", "2018-03-01T16:30:00.000Z"),
        _row(E4, "9021", "D", "2018-03-02T16:30:00.000Z"),
    ]
    book2 = {E1: {"sector": "XLF", "ticker": "T1"},
             E2: {"sector": "XLF", "ticker": "T2"},
             E3: {"sector": "XLK", "ticker": "T3"},
             E4: {"sector": "XLK", "ticker": "T4"}}
    p2 = a4_p2_anchor_exposure(stream2, book2, GRID2, diag2)
    # E1 w1: opp rows {O2 A, O10 D} -> (1-1)/2 = 0.0
    check("a4p2_e1_w1", p2.get((E1, D1)) == 0.0, str(p2.get((E1, D1))))
    # E1 w2: June row routine -> 0 opp rows -> abstain
    check("a4p2_e1_w2_abstain", (E1, D2) not in p2, str(p2.get((E1, D2))))
    # E2 w1: opp {O12 A, O13 D} -> 0.0
    check("a4p2_e2_w1", p2.get((E2, D1)) == 0.0, str(p2.get((E2, D1))))
    # E2 w2: O4 rows routine (2017+2016 May; June decoy wrong month) -> abstain
    check("a4p2_e2_w2_abstain", (E2, D2) not in p2, str(p2.get((E2, D2))))
    # E3 w1: opp buys {O5,O7,O8}=3 sells {O6}=1 -> 0.5 (O8 deduped)
    check("a4p2_e3_w1", p2.get((E3, D1)) == 0.5, str(p2.get((E3, D1))))
    # E3 w2: {O14 A, O15 D} -> 0.0
    check("a4p2_e3_w2", p2.get((E3, D2)) == 0.0, str(p2.get((E3, D2))))
    # E4 w1: {O20 A, O21 D} -> 0.0
    check("a4p2_e4_w1", p2.get((E4, D1)) == 0.0, str(p2.get((E4, D1))))
    check("a4p2_size", len(p2) == 5, str(sorted(p2)))
    # P2 sham: identity permutor reproduces anchor; direction-free
    # classification means the opp subsets are unchanged under permutation
    p2_id = a4_sham_exposure(stream2, book2, GRID2, A4_P2_SHAM_SEED, True,
                             _new_diag(), permutor=_identity)
    check("a4p2sham_identity_eq_anchor", p2_id == p2, str(sorted(p2_id.items())))
    p2_a = a4_sham_exposure(stream2, book2, GRID2, A4_P2_SHAM_SEED, True,
                            _new_diag())
    p2_b = a4_sham_exposure(stream2, book2, GRID2, A4_P2_SHAM_SEED, True,
                            _new_diag())
    check("a4p2sham_determinism_x2", p2_a == p2_b, "differ")

    # ---- A5: macro as-of, regime weights, percentile exposures -------------
    grid5 = ["2018-01-04", "2018-07-03"]
    dfii = [{"realtime_start": "2017-12-31", "date": "2017-12-31", "value": "2.0"},
            {"realtime_start": "2018-02-01", "date": "2018-02-01", "value": "3.0"}]
    vals = macro_asof_values(dfii, grid5)
    # as-of 2018-01-04 -> 2.0; as-of 2018-07-03 -> 3.0 (latest realtime_start)
    check("macro_asof_vals", vals == [2.0, 3.0], str(vals))
    # tiny 2-date grid: only index 0 is inside the forced-MID warmup, so
    # forced_mid=1 here isolates the data-driven band at index 1
    w = regime_weights(vals, forced_mid=1)
    # idx0 forced MID 0.5; idx1: k=2, n=2, 3*2>=2*2 -> HIGH 1.0
    check("regime_weights_dfii", w == [0.5, 1.0], str(w))
    dgs = [{"realtime_start": "2017-12-31", "date": "2017-12-31", "value": "3.0"},
           {"realtime_start": "2018-02-01", "date": "2018-02-01", "value": "1.0"}]
    w_dgs = regime_weights(macro_asof_values(dgs, grid5), forced_mid=1)
    # idx1 r=1.0: k=1, n=2 -> p=1/2 -> MID 0.5 (3*1=3 > 2, 3*1=3 > 2)
    check("regime_weights_dgs", w_dgs == [0.5, 0.5], str(w_dgs))
    # forced-mid boundary: idx0-4 forced even when data says HIGH/LOW
    w6 = regime_weights([1.0, 2.0, 3.0, 4.0, 5.0, 0.5], forced_mid=5)
    check("regime_forced_mid", w6[:5] == [0.5] * 5 and w6[5] == 0.0,
          str(w6))   # idx5 r=0.5: k=1,n=6 -> 3<=6 -> LOW 0.0
    # missing as-of row / "." value -> fail-closed None
    check("macro_missing", macro_asof_values(dfii, ["2017-06-01"]) == [None])
    check("macro_dot_value",
          macro_asof_values([{"realtime_start": "2018-01-01", "value": "."}],
                            ["2018-02-01"]) == [None]
          and regime_weights([None], 5) is None)
    # same realtime_start tie -> deterministic pick (max by (rs, date))
    tie = [{"realtime_start": "2018-01-01", "date": "2018-01-01", "value": "5.0"},
           {"realtime_start": "2018-01-01", "date": "2018-01-02", "value": "6.0"}]
    check("macro_tie_deterministic",
          macro_asof_values(tie, ["2018-03-01"]) == [6.0],
          str(macro_asof_values(tie, ["2018-03-01"])))

    panel = {
        (E1, A5_LTD): [("2017-01-05", "2016-12-31", 100.0)],
        (E1, A5_ASSETS): [("2017-01-05", "2016-12-31", 1000.0)],
        (E1, A5_LIAB): [("2017-01-05", "2016-12-31", 700.0)],
        (E2, A5_LTD): [("2017-06-01", "2016-12-31", 250.0),
                       ("2018-06-01", "2017-12-31", 300.0)],
        (E2, A5_ASSETS): [("2017-06-01", "2016-12-31", 1000.0)],
        (E2, A5_LIAB): [("2017-06-01", "2016-12-31", 600.0)],
        (E3, A5_LTD): [("2017-01-05", "2016-12-31", 100.0)],
        (E3, A5_ASSETS): [("2017-01-05", "2016-12-31", 1000.0)],
        (E3, A5_LIAB): [("2017-01-05", "2016-12-31", 200.0)],
        (E4, A5_LTD): [("2017-01-05", "2016-12-31", 400.0)],
        (E4, A5_ASSETS): [("2017-01-05", "2016-12-31", 1000.0)],
        (E4, A5_LIAB): [("2017-01-05", "2016-12-31", 300.0)],
    }
    book5 = {E1: {"sector": "XLF", "ticker": "T1"},
             E2: {"sector": "XLF", "ticker": "T2"},
             E3: {"sector": "XLK", "ticker": "T3"},
             E4: {"sector": "XLK", "ticker": "T4"}}
    # L: E1 0.1, E2 0.25 (d1) / 0.3 (d2, second vintage avail< t strict),
    #    E3 0.1, E4 0.4. G: E1 0.7, E2 0.6, E3 0.2, E4 0.3.
    a5p1 = a5_exposures(panel, book5, grid5, [0.5, 1.0], A5_LTD, A5_ASSETS,
                        "low")
    # d1 XLF {0.1,0.25}: pct(E1)=1/2 -> 0.5*(1-0.5)=0.25; pct(E2)=1 -> 0.0
    # d2 XLF {0.1,0.3}: pct(E1)=1/2 -> 1.0*0.5=0.5; E2 -> 0.0
    # XLK {0.1,0.4}: E3 pct 1/2 -> 0.25 (d1) / 0.5 (d2); E4 -> 0.0 both
    for k, v in (((E1, grid5[0]), 0.25), ((E2, grid5[0]), 0.0),
                 ((E3, grid5[0]), 0.25), ((E4, grid5[0]), 0.0),
                 ((E1, grid5[1]), 0.5), ((E2, grid5[1]), 0.0),
                 ((E3, grid5[1]), 0.5), ((E4, grid5[1]), 0.0)):
        check(f"a5p1_{k[0][-1]}_{k[1]}", _approx(a5p1.get(k), v),
              f"{a5p1.get(k)} != {v}")
    # vintage as-of: E2 at d1 must read 250 (not the 2018-06 vintage)
    check("a5_vintage_asof",
          _asof_panel_value(panel[(E2, A5_LTD)], grid5[0]) == 250.0
          and _asof_panel_value(panel[(E2, A5_LTD)], grid5[1]) == 300.0)
    a5p2 = a5_exposures(panel, book5, grid5, [0.5, 1.0], A5_LIAB, A5_ASSETS,
                        "high")
    # d1: XLF {0.7,0.6}: E1 pct 1 -> 0.5, E2 0.5 -> 0.25;
    #     XLK {0.2,0.3}: E3 0.25, E4 0.5. d2 (w=1.0): E1 1.0, E2 0.5,
    #     E3 0.5, E4 1.0
    for k, v in (((E1, grid5[0]), 0.5), ((E2, grid5[0]), 0.25),
                 ((E3, grid5[0]), 0.25), ((E4, grid5[0]), 0.5),
                 ((E1, grid5[1]), 1.0), ((E2, grid5[1]), 0.5),
                 ((E3, grid5[1]), 0.5), ((E4, grid5[1]), 1.0)):
        check(f"a5p2_{k[0][-1]}_{k[1]}", _approx(a5p2.get(k), v),
              f"{a5p2.get(k)} != {v}")
    # DGS10 control: weights [0.5, 0.5] -> P1 shape
    a5p1_dgs = a5_exposures(panel, book5, grid5, [0.5, 0.5], A5_LTD,
                            A5_ASSETS, "low")
    check("a5p1_dgs10_d2", _approx(a5p1_dgs.get((E1, grid5[1])), 0.25),
          str(a5p1_dgs.get((E1, grid5[1]))))
    # sham-macro: real seed -> determinism x2 + block multiset preserved
    import numpy as np
    ws_real1 = block_permutation([0.5, 1.0], np.random.default_rng(A5_SHAM_SEED))
    ws_real2 = block_permutation([0.5, 1.0], np.random.default_rng(A5_SHAM_SEED))
    check("a5_blockperm_determinism", ws_real1 == ws_real2, str(ws_real1))
    check("a5_blockperm_multiset", sorted(ws_real1) == sorted([0.5, 1.0]),
          str(ws_real1))

    class _FakeRng3:
        def permutation(self, n):
            return [n - 1 - i for i in range(n)]

    # blocks of [0.5, 1.0, 0.5, 0.5]: b0=[0.5@0], b1=[1.0@1], b2=[0.5@2,3];
    # reversed block order [2,1,0] -> [0.5, 0.5, 1.0, 0.5]
    ws_rev = block_permutation([0.5, 1.0, 0.5, 0.5], _FakeRng3())
    # blocks: b0=[0.5@0], b1=[1.0@1], b2=[0.5@2,3]; reversed order [2,1,0]
    # -> [0.5, 0.5, 1.0, 0.5]
    check("a5_blockperm_fake_reverse", ws_rev == [0.5, 0.5, 1.0, 0.5],
          str(ws_rev))

    # ---- A6-P1 dividend transitions ----------------------------------------
    grid6 = ["2018-04-04", "2018-07-03", "2018-10-02", "2019-01-03"]
    d6 = "2019-01-03"                     # the only SCORED date in grid6
    lo_now = "2018-01-03"                 # d6 - 365
    lo_prev = "2017-01-03"                # d6 - 730
    check("a6_window_bounds", (dd(d6) - timedelta(days=365)).isoformat()
          == lo_now and (dd(d6) - timedelta(days=730)).isoformat() == lo_prev)
    divs = {
        # E1: paid_now {2018-06-15, 2019-01-02}=2, paid_prev {2017-06-01}=1 -> 0
        "T1": [{"ex_date": "2015-01-10"}, {"ex_date": "2017-06-01"},
               {"ex_date": "2018-06-15"}, {"ex_date": "2019-01-02"}],
        # E2: only record inside now-window, earliest > D-730 -> ABSTAIN
        "T2": [{"date": "2018-06-01"}],
        # E3: paid_now 0, paid_prev 1 -> omission -1
        "T3": [{"ex_date": "2015-03-01"}, {"ex_date": "2017-06-01"}],
        # E4: never-payer, earliest <= D-730 -> assertable 0
        "T4": [{"ex_date": "2015-03-01"}],
        # E5: boundary record exactly at D-365 counts in NOW window -> +1
        "T5": [{"ex_date": "2015-01-01"}, {"ex_date": "2018-01-03"}],
        # E6: only in-window record is dated exactly D -> excluded -> 0
        "T6": [{"ex_date": "2015-01-01"}, {"ex_date": "2019-01-03"}],
        # E7: record before even the prev window; earliest assertable -> 0
        "T7": [{"ex_date": "2014-01-01"}],
    }
    tick = {E1: "T1", E2: "T2", E3: "T3", E4: "T4", E5: "T5", E6: "T6",
            E7: "T7"}
    book6 = {c: {"sector": "XLF", "ticker": t} for c, t in tick.items()}
    diag6 = _new_diag()
    a6p1 = a6_div_exposures(divs, tick, book6, grid6, diag6)
    check("a6p1_e1_zero", a6p1.get((E1, d6)) == 0.0, str(a6p1.get((E1, d6))))
    check("a6p1_e2_abstain", (E2, d6) not in a6p1, str(a6p1.get((E2, d6))))
    check("a6p1_e3_omission", a6p1.get((E3, d6)) == -1.0,
          str(a6p1.get((E3, d6))))
    check("a6p1_e4_neverpayer", a6p1.get((E4, d6)) == 0.0,
          str(a6p1.get((E4, d6))))
    check("a6p1_e5_initiation_boundary", a6p1.get((E5, d6)) == 1.0,
          str(a6p1.get((E5, d6))))
    check("a6p1_e6_exdate_at_D_excluded", a6p1.get((E6, d6)) == 0.0,
          str(a6p1.get((E6, d6))))
    check("a6p1_e7_zero", a6p1.get((E7, d6)) == 0.0, str(a6p1.get((E7, d6))))
    check("a6p1_warmup_dates_absent",
          all((c, g) not in a6p1 for c in book6 for g in grid6[:3]))
    check("a6p1_size", len(a6p1) == 6, str(sorted(a6p1)))
    check("a6p1_abstain_counted", diag6["div_window_formation_abstains"] == 1,
          str(diag6))
    # E2 alternative: prior window holds a record -> assertable (no absence
    # claim needed): payer with unchanged existence -> 0
    divs2 = dict(divs)
    divs2["T2"] = [{"date": "2017-06-01"}, {"date": "2018-06-01"}]
    a6p1b = a6_div_exposures(divs2, tick, book6, grid6, _new_diag())
    check("a6p1_e2_assertable_prev", a6p1b.get((E2, d6)) == 0.0,
          str(a6p1b.get((E2, d6))))
    # absent file -> abstain
    a6p1c = a6_div_exposures({"T1": divs["T1"]}, tick, book6, grid6,
                             _new_diag())
    check("a6p1_absent_file_abstains",
          set(a6p1c) == {(E1, d6)} and a6p1c[(E1, d6)] == 0.0,
          str(sorted(a6p1c)))

    # ---- A6-P2 split states -------------------------------------------------
    splits = {
        "T1": [{"date": "2018-10-01", "split": "2.0"}],        # +1
        "T2": [{"date": "2018-09-01", "split": "0.1"}],        # -1
        "T3": [{"date": "2018-05-01", "split": "2.0"}],        # outside 180d
        "T5": [{"date": "2018-08-01", "split": "1"}],          # unity -> defect
        "T6": [{"date": "2018-08-01", "split": "abc"}],        # unparsable
        "T7": [{"date": "2018-08-01", "split": "1.5"},
               {"date": "2018-09-01", "split": "3.0"}],        # most recent +1
        "T8": [{"date": "2018-09-01", "split": "1.0"},
               {"date": "2018-08-01", "split": "2.0"}],        # unity recent
        "T9": [{"date": "2018-07-07", "split": "2.0"}],        # boundary [D-180
        "T10": [{"date": "2019-01-03", "split": "2.0"}],       # at D -> excluded
    }
    # T4 has NO file -> declared default state 0 (no baseline window)
    tick8 = {E1: "T1", E2: "T2", E3: "T3", E4: "T4", E5: "T5", E6: "T6",
             E7: "T7", E8: "T8", E9: "T9", E10: "T10"}
    book8 = {c: {"sector": "XLF", "ticker": t} for c, t in tick8.items()}
    diag8 = _new_diag()
    a6p2 = a6_split_exposures(splits, tick8, book8, grid6, diag8)
    # window at d6: [2018-07-07, 2019-01-03)
    check("a6p2_e1_forward", a6p2.get((E1, d6)) == 1.0, str(a6p2.get((E1, d6))))
    check("a6p2_e2_reverse", a6p2.get((E2, d6)) == -1.0,
          str(a6p2.get((E2, d6))))
    check("a6p2_e3_outside_window", a6p2.get((E3, d6)) == 0.0,
          str(a6p2.get((E3, d6))))
    check("a6p2_e4_absent_file_zero", a6p2.get((E4, d6)) == 0.0,
          str(a6p2.get((E4, d6))))
    check("a6p2_e5_unity_defect", (E5, d6) not in a6p2,
          str(a6p2.get((E5, d6))))
    check("a6p2_e6_unparsable_defect", (E6, d6) not in a6p2,
          str(a6p2.get((E6, d6))))
    check("a6p2_e7_most_recent", a6p2.get((E7, d6)) == 1.0,
          str(a6p2.get((E7, d6))))
    check("a6p2_e8_unity_recent_wins", (E8, d6) not in a6p2,
          str(a6p2.get((E8, d6))))
    check("a6p2_e9_boundary_inclusive", a6p2.get((E9, d6)) == 1.0,
          str(a6p2.get((E9, d6))))
    check("a6p2_e10_at_D_excluded", a6p2.get((E10, d6)) == 0.0,
          str(a6p2.get((E10, d6))))
    check("a6p2_warmup_absent",
          all((c, g) not in a6p2 for c in book8 for g in grid6[:3]))
    check("a6p2_defects_counted", diag8["split_defect_unity_abstains"] == 2
          and diag8["split_defect_unparsable_abstains"] == 1, str(diag8))

    # ---- A6 within-sector hash permutation sham ----------------------------
    anchor6 = {(E1, d6): 0.0, (E3, d6): -1.0, (E4, d6): 0.0,
               (E5, d6): 1.0, (E6, d6): 0.0, (E7, d6): 0.0}
    sham6 = within_sector_hash_permutation_sham(anchor6, book6,
                                                "SFV13-A6-H1")
    # multiset preserved per (date, sector) cell
    check("a6sham_multiset",
          sorted(sham6.values()) == sorted(anchor6.values()),
          f"{sorted(sham6.values())} vs {sorted(anchor6.values())}")
    # independent re-derivation of the frozen hash-order assignment
    names = sorted(anchor6)                       # same cell: all XLF, one date
    idx = DECISION_GRID_30.index(d6)
    keyed = sorted((c for c, _t in names),
                   key=lambda c: hashlib.sha256(
                       f"{CYCLE}|SFV13-A6-H1|{c}|{idx}".encode()).hexdigest())
    vals_sorted = sorted(anchor6[c, d6] for c, _t in names)
    expected6 = {(c, d6): v for c, v in zip(keyed, vals_sorted)}
    check("a6sham_hash_order_assignment", sham6 == expected6,
          f"{sorted(sham6.items())} vs {sorted(expected6.items())}")
    check("a6sham_determinism_x2",
          sham6 == within_sector_hash_permutation_sham(anchor6, book6,
                                                       "SFV13-A6-H1"))
    # P2's sham uses its own hypothesis id (different hash stream)
    sham6b = within_sector_hash_permutation_sham(anchor6, book6,
                                                 "SFV13-A6-H2")
    check("a6sham_multiset_p2",
          sorted(sham6b.values()) == sorted(anchor6.values()))

    # ---- handler-level wiring: synthetic context through the registry ------
    C = type("Ctx", (), {})()
    C._d2p_cache = {
        "bookable": book1,
        "form4_stream_rows": stream1,
        "form4_accepts": acc1,
        "a5_panel_fields": panel,
        "macro_vintages_DFII10": dfii,
        "macro_vintages_DGS10": dgs,
        "macro_vintages_T10YIE": dgs,
        "eodhd_div": divs,
        "eodhd_splits": splits,
    }
    for pid in ("SFV13-A4-P1", "SFV13-A4-P2"):
        C._d2p_cache["bookable"] = book1 if pid == "SFV13-A4-P1" else book2
        C._d2p_cache["form4_stream_rows"] = (stream1 if pid == "SFV13-A4-P1"
                                             else stream2)
        a = machine.PROPOSAL_EXPOSURE_BUILDERS[pid](C)
        exp = p1 if pid == "SFV13-A4-P1" else p2
        check(f"handler_{pid}", a == exp, f"{len(a)} vs {len(exp)} keys")
    C._d2p_cache["bookable"] = book5
    C._d2p_cache["form4_stream_rows"] = []
    # handler A5 grid = the real 30-date grid; DFII10 fixture as-of reads 3.0
    # on every grid date (latest realtime_start 2018-02-01) -> r constant ->
    # HIGH bands, so w = 0.5 on forced-MID indices 0-4 (2018-07-03 is index 1)
    # and 1.0 elsewhere; panel fixture gives 120 defined (entity, date) cells.
    a = machine.PROPOSAL_EXPOSURE_BUILDERS["SFV13-A5-P1"](C)
    # pct(E1) at 2018-07-03 = 1/2 -> 0.5 * (1 - 0.5) = 0.25
    check("handler_a5p1", _approx(a.get((E1, "2018-07-03")), 0.25)
          and len(a) == 120,
          f"{a.get((E1, '2018-07-03'))} len={len(a)}")
    a = machine.PROPOSAL_EXPOSURE_BUILDERS["SFV13-A5-P2"](C)
    # pct_G(E1) at 2018-07-03 = 1 -> forced-MID 0.5 * 1 = 0.5
    check("handler_a5p2", _approx(a.get((E1, "2018-07-03")), 0.5),
          str(a.get((E1, "2018-07-03"))))
    ctrl = PROPOSAL_CONTROL_BUILDERS["SFV13-A5-P1"]["sham_macro_placebo"]["builder"](C)
    check("handler_a5p1_sham", isinstance(ctrl, dict) and len(ctrl) == 120,
          str(len(ctrl)))
    ctrl = PROPOSAL_CONTROL_BUILDERS["SFV13-A5-P1"]["exposure_form_control_dgs10"]["builder"](C)
    # DGS10 fixture as-of reads 1.0 on every grid date -> same forced-MID
    # shape -> (E1, 2018-07-03) = 0.5 * (1 - 0.5) = 0.25
    check("handler_a5p1_dgs10", _approx(ctrl.get((E1, "2018-07-03")), 0.25),
          str(ctrl.get((E1, "2018-07-03"))))
    C._d2p_cache["bookable"] = book6
    C._d2p_cache["macro_vintages_DFII10"] = dfii
    C._d2p_cache["macro_vintages_T10YIE"] = dgs
    C._d2p_cache["macro_vintages_DGS10"] = dgs
    a6h = machine.PROPOSAL_EXPOSURE_BUILDERS["SFV13-A6-P1"](C)
    # handler grid = the real 30-date grid (27 scored dates from 2019-01-03).
    # E2's single record (2018-06-01) leaves absence unassertable at
    # 2019-01-03 (earliest > D-730 = 2017-01-03) -> abstain there; it becomes
    # assertable once D >= earliest + 730 (2020-05-31), so E2 may carry 0.0
    # states at later scored dates.
    check("handler_a6p1_e2_abstain_at_first_scored",
          (E2, "2019-01-03") not in a6h, str(a6h.get((E2, "2019-01-03"))))
    check("handler_a6p1_e1_defined_someday",
          any(k[0] == E1 and isinstance(v, float) for k, v in a6h.items()),
          str(len(a6h)))
    a6h2 = machine.PROPOSAL_EXPOSURE_BUILDERS["SFV13-A6-P2"](C)
    # E5's unity ratio (2018-08-01) sits in the [D-180, D) window of scored
    # date 2019-01-03 only -> defect abstain there; outside that window the
    # declared default state 0 applies.
    check("handler_a6p2_e5_defect_abstain_at_2019_01_03",
          (E5, "2019-01-03") not in a6h2,
          str(a6h2.get((E5, "2019-01-03"))))
    check("handler_a6p2_e4_zero_states",
          any(k[0] == E4 and v == 0.0 for k, v in a6h2.items()),
          str(len(a6h2)))
    sh = PROPOSAL_CONTROL_BUILDERS["SFV13-A6-P1"]["within_sector_permutation"]["builder"](C)
    check("handler_a6p1_sham_multiset",
          sorted(sh.values()) == sorted(a6h.values())
          and set(sh) == set(a6h), "multiset/keys differ")

    # ---- macro fail-closed: missing as-of -> empty anchor dict -------------
    C2 = type("Ctx", (), {})()
    C2._d2p_cache = {"bookable": book5,
                     "a5_panel_fields": panel,
                     "macro_vintages_DFII10": [{"realtime_start": "2019-01-01",
                                                "value": "2.0"}],
                     "macro_vintages_T10YIE": [],
                     "macro_vintages_DGS10": dgs}
    a = machine.PROPOSAL_EXPOSURE_BUILDERS["SFV13-A5-P1"](C2)
    check("a5_failclosed_empty", a == {}, str(len(a)))

    # ---- whole-registry determinism x2 on the synthetic context ------------
    def _run_all():
        out = {}
        for pid in sorted(machine.PROPOSAL_EXPOSURE_BUILDERS):
            out[pid] = machine.PROPOSAL_EXPOSURE_BUILDERS[pid](C)
        for pid in sorted(PROPOSAL_CONTROL_BUILDERS):
            for cn, spec in sorted(PROPOSAL_CONTROL_BUILDERS[pid].items()):
                out[f"{pid}::{cn}"] = spec["builder"](C)
        return json.dumps({f"{k}": {f"{e}|{t}": v for (e, t), v in d.items()}
                           for k, d in out.items()}, sort_keys=True)
    C._d2p_cache["bookable"] = book6   # superset fixture (E1..E7, T1..T7)
    C._d2p_cache["form4_stream_rows"] = stream1
    r1 = _run_all()
    r2 = _run_all()
    check("registry_determinism_x2", r1 == r2 and len(r1) > 100,
          f"len={len(r1)} identical={r1 == r2}")

    if fails:
        for f in fails:
            print("SELFCHECK FAIL:", f, file=sys.stderr)
        return 1
    print("selfcheck OK")
    return 0


class _FakeRng:
    """Deterministic fake numpy-style generator for known-answer checks:
    permutation(n) returns the given order."""

    def __init__(self, order):
        self._order = list(order)

    def permutation(self, n):
        assert len(self._order) == n, (len(self._order), n)
        return list(self._order)


def main(argv):
    if "--selfcheck" in argv:
        return selfcheck()
    sys.stderr.write(
        "usage: d2_v13_proposal_handlers.py --selfcheck\n"
        "(measurement runs go through research/assets/stocks/d2_v13_run.py "
        "under the machine-wide heavy lock)\n")
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv))
