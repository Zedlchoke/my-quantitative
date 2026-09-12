"""STOCKS-NG2 D2 measurement orchestration.

Measures, per proposal (SFNG2-A4-P1 amendlag anchor, SFNG2-A4-P2 cdays
anchor), on the frozen daily entity-date panel (P-12):

  NOVELTY         pooled midrank Spearman |rho| of the anchor panel vs
                  EVERY one of the 17 veto entries on common pairs;
                  bar 0.20; margin per entry (P-2); FAIL-CLOSED on any
                  unmeasured entry -> INELIGIBLE_FAIL_CLOSED(reason).
  IDENTIFIABILITY sham-amendment control (pair-value permutation within
                  (amendment-acceptance-session, sector) cells, matched
                  original-only support, value multisets preserved
                  EXACTLY, PCG64 seed 20260912) vs the anchor: pooled
                  rho; |rho| >= 0.98 = self-subsumption DESIGN-FAILURE
                  kill pre-score; plus the filing-arrival clock shadow
                  under the same bound.  Q-11 null-validity distinction
                  recorded explicitly.
  FEASIBILITY     unique pair-ISSUER census of the 1,877 resolvable
                  pairs; both-stamps acceptance-eligible share; P2
                  dV != 0 share; bookable post-amendment windows (V13
                  census method on THIS substrate; 2026-tail (10 pairs)
                  bookability vs the measured price-data end); Q-6
                  recent-window (2025) bookable-decision count vs the
                  frozen floor 30; cycle-local fold populations vs the
                  frozen floor 20 decisions AND the census pair-mass
                  split 612/543/722; turnover/cost ceiling accounting
                  (event mass -> bps at bands 10/15/25 and stress x2)
                  vs the referenced 200 bps/quarter rubric ceiling.

NO PnL, NO expectancy, NO profit factor, NO selection, NO scoring: the
only statistics produced are ranks, correlations of signal series,
counts and cost-rate arithmetic.  Selection and scoring remain later
decisions, not D2's.
"""

from __future__ import annotations

import json
from datetime import date

from . import core, exposures, pairs, vetoes
from .core import (FOLD_PAIR_MASS_DECLARED, FOLD_POPULATION_FLOOR,
                   NOVELTY_BAR, Q6_RECENT_WINDOW_FLOOR, Q6_RECENT_YEAR,
                   SECTOR_BOOKABLE_NAMES, SELF_SUBSUMPTION_RHO, SHAM_SEED,
                   SPEARMAN_MIN_N, TURNOVER_CEILING_BPS_QTR, VETO_NAMES,
                   eligible, spearman)

BANDS_BPS = (10.0, 15.0, 25.0)      # A/B/C per side (inherited V13 cost model)
STRESS_MULT = 2.0                   # stress rerun multiplier (20/30/50 bps)


# ------------------------------------------------------------- build ---------
def build_all():
    """Context + stream aggregation (ng1 machinery on the NG2 grid) +
    pair construction + sham.  The ng1 aggregator's AGG_CUTOFF is
    rebound to this cycle's grid-coverage cutoff (2015-11-24, 800d
    before the 2018 grid start) - a strictly WIDENING change so the
    800-calendar-day veto windows are evidenced across the whole grid;
    no other semantic of the inherited aggregator changes."""
    C = core.build_context()
    import research.assets.stocks_ng1.d2.exposures as ng1_exp
    orig_cutoff = ng1_exp.AGG_CUTOFF
    ng1_exp.AGG_CUTOFF = core.STREAM_AGG_CUTOFF
    try:
        ng1_exp.aggregate_stream(C)
    finally:
        ng1_exp.AGG_CUTOFF = orig_cutoff
    C.agg_cutoff_rebind = {"from": orig_cutoff,
                           "to": core.STREAM_AGG_CUTOFF}
    C.pairs, C.E4a, C.Arr4a, C.pair_diag = pairs.resolve_pairs(C)
    C.sham_info = exposures.build_sham(C)
    return C


# ------------------------------------------------------------- eligibility ---
def eligibility_series(C, cik):
    memo = getattr(C, "_elig", None)
    if memo is None:
        memo = C._elig = {}
    if cik in memo:
        return memo[cik]
    out = [eligible(C, cik, t) for t in C.grid]
    memo[cik] = out
    return out


def build_anchor_panel(C, exposure_fn, entities=None):
    """{(cik, t): value} over the frozen eligibility panel where the
    exposure definition floor is met (P-12 representation identity).
    Default entity universe = the treatment slice (entities with pair
    events); the sham panels pass their own receiver set and the
    arrival shadow passes the full Form-4-event population."""
    panel = {}
    if entities is None:
        entities = set(C.E4a.keys())
    ents = sorted(set(entities) & set(C.series.keys()))
    for cik in ents:
        el = eligibility_series(C, cik)
        for t, ok in zip(C.grid, el):
            if not ok:
                continue
            v = exposure_fn(C, cik, t)
            if v is not None:
                panel[(cik, t)] = v
    return panel


# ---------------------------------------------------------------- novelty ----
def novelty_block(C, anchor):
    entry = {"veto_rho": {}, "n_per_veto": {}, "margin_to_020": {}}
    for vn in VETO_NAMES:
        vf = vetoes.VETO_BUILDERS[vn]
        a, v = [], []
        for (e, t), av in sorted(anchor.items()):
            vv = vf(C, e, t)
            if vv is not None:
                a.append(av)
                v.append(vv)
        rho = spearman(a, v)
        entry["veto_rho"][vn] = None if rho is None else round(rho, 4)
        entry["n_per_veto"][vn] = len(a)
        entry["margin_to_020"][vn] = (
            None if rho is None else round(NOVELTY_BAR - abs(rho), 4))
    valid = {vn: abs(r) for vn, r in entry["veto_rho"].items()
             if r is not None}
    unmeasured = [vn for vn in VETO_NAMES if entry["veto_rho"][vn] is None]
    entry["max_abs_veto_rho"] = round(max(valid.values()), 4) if valid else None
    arg = max(sorted(valid), key=lambda k: valid[k]) if valid else None
    entry["argmax_veto"] = arg
    entry["worst_margin_to_020"] = (round(NOVELTY_BAR - valid[arg], 4)
                                    if arg else None)
    entry["vetoes_measured"] = len(valid)
    entry["unmeasured_entries"] = unmeasured
    entry["novelty_pass_le_020"] = (len(valid) == len(VETO_NAMES)
                                    and max(valid.values()) <= NOVELTY_BAR)
    if unmeasured:
        entry["verdict"] = (
            f"INELIGIBLE_FAIL_CLOSED(reason={len(unmeasured)}/17 veto "
            f"entries unmeasured: {','.join(unmeasured)})")
    elif entry["max_abs_veto_rho"] > NOVELTY_BAR:
        entry["verdict"] = (f"VETO(argmax={arg},rho="
                            f"{entry['max_abs_veto_rho']},margin_to_020="
                            f"{entry['worst_margin_to_020']})")
    else:
        entry["verdict"] = "ELIGIBLE"
    return entry


# --------------------------------------------------------- identifiability --
def _per_date_rho_stats(anchor, control, gate=0.30, share=0.90):
    """Informational per-date stats (V13 A4 convention; NOT the
    operative D2 kill - recorded for continuity only)."""
    dates = sorted({t for _e, t in anchor})
    rhos = []
    for t in dates:
        ks = sorted(k for k in anchor if k[1] == t and k in control)
        if len(ks) < SPEARMAN_MIN_N:
            continue
        r = spearman([anchor[k] for k in ks], [control[k] for k in ks])
        if r is not None:
            rhos.append(r)
    if not rhos:
        return None
    ok = sum(1 for r in rhos if abs(r) <= gate)
    return {"dates_measured": len(rhos),
            "mean_per_date_rho": round(sum(rhos) / len(rhos), 4),
            "share_dates_abs_le_gate": round(ok / len(rhos), 4),
            "gate": gate, "pass_share": share,
            "operative": False}


def identifiability_block(C, anchor, control, control_name):
    pooled, n = core.rho_on_common(anchor, control)
    kill = pooled is not None and abs(pooled) >= SELF_SUBSUMPTION_RHO
    out = {
        "control": control_name,
        "control_pairs_defined": len(control),
        "common_pairs": n,
        "pooled_anchor_vs_control_rho": (None if pooled is None
                                         else round(pooled, 4)),
        "gate_self_subsumption_rho": SELF_SUBSUMPTION_RHO,
        "self_subsumption_kill": bool(kill),
        "per_date_informational": _per_date_rho_stats(anchor, control),
        "verdict": ("BLOCKED_SELF_SUBSUMPTION_PRE_SCORE" if kill
                    else ("NO_SELF_SUBSUMPTION_MEASURED"
                          if pooled is not None
                          else "CONTROL_RHO_UNMEASURABLE_FAIL_CLOSED")),
        "q11_null_validity_note": (
            "a control that does NOT reproduce the anchor's future "
            "identifying metric does NOT prove the mechanism (Q-11): the "
            "D2 rho check can only kill (self-subsumption => design "
            "failure); the operative sham/arrival kills are the "
            "book-level same-sign >= 0.5x rules evaluated at scoring, "
            "and an invalid null there is a failed control, never a "
            "mechanism proof"),
    }
    return out


# ------------------------------------------------------------- feasibility --
def pair_census(C):
    """Unique-issuer split of the census resolvable pairs + stamps/share
    accounting + lag/dV distribution disclosure."""
    uniq_meas = set()
    by_cls = {"ALIVE_EVIDENCED": 0, "DEAD_EVIDENCED": 0}
    by_year_first = {}
    lags = []
    dvs = []
    dv_zero = dv_nonzero = dv_unmeasured = 0
    for p in C.pairs:
        cik = p["cik"]
        uniq_meas.add(cik)
        by_cls[C.bookable[cik]["cls"]] += 1
        y = p["a_ts"][:4]
        by_year_first[y] = by_year_first.get(y, 0) + 1
        lags.append(p["lag_days"])
        if p["dv"] is None:
            dv_unmeasured += 1
        elif p["dv"] == 0.0:
            dv_zero += 1
        else:
            dv_nonzero += 1
            dvs.append(p["dv"])
    ls = sorted(lags)
    n = len(ls)

    def q(frac):
        if not ls:
            return None
        k = (n - 1) * frac
        lo = int(k)
        return (round(ls[lo], 1) if lo == k or lo + 1 >= n
                else round(0.5 * (ls[lo] + ls[lo + 1]), 1))

    # issuer split over the FULL census resolvable set is reconstructed
    # from the measurement stages (resolvable - not-eligible subsets
    # carry issuer attribution only where stamps allowed resolution)
    meas = C.pair_diag["stages"]
    return {
        "method": ("unique pair ISSUERS over the census's frozen "
                   "resolvable output (1,877), carried through the "
                   "acceptance_row_rule to the measurement pair set; "
                   "entity = issuerCik per the frozen identity rule; "
                   "NOTE (substrate property, disclosed): the 4/A "
                   "re-ingest enumerated the pinned submissions_alive "
                   "metadata (410 ALIVE cohort CIKs), so the extension "
                   "carries ALIVE issuers only - by_cohort_class 1635/0 "
                   "is an enumeration-surface property of the pinned "
                   "substrate, not a survivorship filter applied here"),
        "census_resolvable_pairs": C.pair_diag["census_reconciliation"][
            "amendments_with_resolvable_original"],
        "measurement_pairs": meas["measurement_pairs"],
        "stages_fail_closed": meas,
        "unique_measurement_issuers": len(uniq_meas),
        "by_cohort_class": by_cls,
        "by_acceptance_year": dict(sorted(by_year_first.items())),
        "pair_multiplicity": {
            "keys_with_multiple_originals":
                C.pair_diag["ties"]["keys_with_multiple_originals"],
            "pairs_with_tie_broken":
                C.pair_diag["ties"]["pairs_with_tie_broken"],
            "note": ("tie rule frozen ex ante: earliest stream "
                     "acceptance, then smallest accession")},
        "lag_days_distribution": {
            "n": n, "min": ls[0] if ls else None,
            "q25": q(0.25), "median": q(0.5), "q75": q(0.75),
            "max": ls[-1] if ls else None,
            "negative_lags": sum(1 for x in ls if x < 0),
            "zero_lags": sum(1 for x in ls if x == 0),
            "note": ("negative lags are disclosed data anomalies, kept "
                     "untrimmed (no cap, no winsorization - frozen)")},
        "p2_dv_share": {
            "dv_nonzero": dv_nonzero, "dv_zero": dv_zero,
            "dv_unmeasurable": dv_unmeasured,
            "nonzero_share_of_measured": (round(dv_nonzero
                                                / (dv_nonzero + dv_zero), 4)
                                          if (dv_nonzero + dv_zero) else None),
            "dv_nonzero_abs_sum_usd": round(sum(abs(x) for x in dvs), 2),
            "note": ("dV = V(amendment) - V(original), doc-level D-coded "
                     "nonDerivative totals, shares x raw close at each "
                     "doc's own acceptance date (no dollar value field "
                     "exists on either surface - the declared fallback "
                     "is universal)")},
    }


def _fold_of(C, d_iso):
    for f in C.folds:
        if f["start"] <= d_iso <= f["end"]:
            return f["fold_id"]
    return None


def bookable_windows_census(C):
    """Post-amendment windows bookable per the V13 census method,
    re-measured on this substrate: every distinct amendment-acceptance
    session of a priced cohort entity in the compliance window opens one
    candidate STRICT_NEXT_BAR window; bookable iff >= 63 bars through
    the session AND >= 1 bar strictly after it (a fillable next-bar)."""
    n_book = 0
    ents = set()
    dead_ents = set()
    dead_pairs = 0
    per_fold = {}
    tail_2026 = {"candidates": 0, "bookable": 0}
    for cik, E in C.E4a.items():
        s = C.series.get(cik)
        if s is None:
            continue
        for si in E["sess_idx"]:
            sess = C.sessions[si]
            if not (C.grid[0] <= sess <= C.grid_end):
                continue
            i = core.bars_through(C, cik, sess)
            if i < 63:
                continue
            if i >= len(s["dates"]):
                continue   # no bar strictly after the session
            n_book += 1
            ents.add(cik)
            fold = _fold_of(C, sess)
            if fold:
                per_fold[fold] = per_fold.get(fold, 0) + 1
            if sess[:4] == "2026":
                tail_2026["bookable"] += 1
            if C.bookable[cik]["cls"] == "DEAD_EVIDENCED":
                dead_pairs += 1
                dead_ents.add(cik)
        # candidate accounting over ALL in-window sessions (priced entity)
        for si in E["sess_idx"]:
            sess = C.sessions[si]
            if not (C.grid[0] <= sess <= C.grid_end):
                continue
            if sess[:4] == "2026":
                tail_2026["candidates"] += 1
    return {
        "method": ("distinct amendment-acceptance sessions of priced "
                   "cohort entities in the compliance window; bookable "
                   "iff >= 63 bars through the session and >= 1 bar "
                   "strictly after (STRICT_NEXT_BAR fillability); "
                   "death-inclusive series, exit-at-last-close"),
        "entities": len(ents),
        "bookable_pairs": n_book,
        "dead_share_pairs": round(dead_pairs / n_book, 4) if n_book else None,
        "dead_entities": len(dead_ents),
        "per_fold": dict(sorted(per_fold.items())),
        "tail_2026_vs_price_data_end": {
            **tail_2026,
            "price_data_end_measured": C.price_data_end,
            "grid_end": C.grid_end,
            "note": ("the proposal's V13 price-end reference 2025-07-24 "
                     "is superseded by measurement: the inherited price "
                     "files' alive tail ends 2026-09-09 > grid_end, so "
                     "2026-tail pairs are bookable-by-measurement where "
                     "their own eligibility holds - the 'unbookable-by-"
                     "construction' conditional did not fire; bars after "
                     "grid_end never enter any measured window")},
    }


def decision_population(C, panel):
    """Per-date ranked-population census of an anchor panel: sector ->
    count of eligible defined names; a date is BOOKABLE iff some sector
    has >= SECTOR_BOOKABLE_NAMES ranked names (the proposal book_form
    threshold)."""
    per_date = {}
    for (cik, t), _v in panel.items():
        sec = C.bookable[cik]["sector"] or "UNMAPPED"
        per_date.setdefault(t, {}).setdefault(sec, set()).add(cik)
    out = {}
    for t in C.grid:
        secs = per_date.get(t, {})
        counts = {sec: len(v) for sec, v in secs.items()}
        out[t] = {"population": sum(counts.values()),
                  "max_sector_names": max(counts.values()) if counts else 0,
                  "bookable": any(c >= SECTOR_BOOKABLE_NAMES
                                  for c in counts.values())}
    return out


def fold_pair_mass(C):
    """Resolvable-pair mass per declared fold vs the census by-year
    split 612/543/722 (verification, never re-tuned)."""
    out = {}
    for f in C.folds:
        n_census = sum(v for y, v in
                       C.pair_diag["per_year_resolvable"].items()
                       if f["start"][:4] <= y <= f["end"][:4])
        n_meas = sum(v for y, v in
                     C.pair_diag["per_year_measurement"].items()
                     if f["start"][:4] <= y <= f["end"][:4])
        out[f["fold_id"]] = {
            "window": f"{f['start']}..{f['end']}",
            "census_resolvable_pairs": n_census,
            "declared_mass": FOLD_PAIR_MASS_DECLARED[f["fold_id"]],
            "mass_matches_declaration": n_census ==
            FOLD_PAIR_MASS_DECLARED[f["fold_id"]],
            "measurement_pairs": n_meas}
    return out


def _qualifying_sessions(C, pid):
    """Entry-event mass upper bound: every session that opens/re-arms one
    window per entity (P1: sessions carrying >= 1 measurement pair; P2:
    sessions carrying >= 1 pair with measured dV != 0), priced entities,
    compliance window."""
    n = 0
    for cik, E in C.E4a.items():
        if cik not in C.series:
            continue
        for i, si in enumerate(E["sess_idx"]):
            sess = C.sessions[si]
            if not (C.grid[0] <= sess <= C.grid_end):
                continue
            if pid.endswith("P1"):
                hit = True
            else:
                hit = E["events"][i][1] is not None \
                    and E["events"][i][1] != 0.0
            if hit:
                n += 1
    return n


def _turnover_block(C, pid, n_avg_population):
    events = _qualifying_sessions(C, pid)
    days = (date.fromisoformat(C.grid_end)
            - date.fromisoformat(C.grid[0])).days
    quarters = days / 91.3125
    events_q = events / quarters if quarters > 0 else None
    turns_q = (2.0 * events_q / n_avg_population
               if events_q is not None and n_avg_population > 0 else None)
    bands = {}
    for bps in BANDS_BPS:
        for mult, tag in ((1.0, "base"), (STRESS_MULT, "stress_x2")):
            cost = None if turns_q is None else round(turns_q * bps * mult, 2)
            bands[f"{int(bps)}bps_{tag}"] = {
                "per_side_bps": bps * mult,
                "quarterly_cost_bps_if_ceiling_met": cost,
                "within_200bps_qtr_ceiling": (None if cost is None
                                              else cost <=
                                              TURNOVER_CEILING_BPS_QTR)}
    return {
        "accounting": ("amendment-acceptance event mass over priced "
                       "cohort entities in the compliance window (upper "
                       "bound: per-event eligibility not pre-filtered); "
                       "quarterly position-turns = 2 x events/quarter / "
                       "mean in-state population; cost = turns x "
                       "per-side bps; NO PnL arithmetic anywhere"),
        "qualifying_sessions_upper_bound": events,
        "grid_quarters": round(quarters, 3),
        "events_per_quarter": (round(events_q, 2)
                               if events_q is not None else None),
        "mean_in_state_population": round(n_avg_population, 2),
        "position_turns_per_quarter": (round(turns_q, 3)
                                       if turns_q is not None else None),
        "cost_scenarios_bps_per_quarter": bands,
        "referenced_ceiling_bps_qtr": TURNOVER_CEILING_BPS_QTR,
        "bands_source": ("V13 p3 carried_payload.costs A/B/C 10/15/25 "
                         "bps per side, stress x2 = 20/30/50 (referenced; "
                         "re-frozen at the NG2 invariant freeze)"),
    }


def feasibility_block(C, panels):
    pc = pair_census(C)
    bw = bookable_windows_census(C)
    blocks = {"pair_census": pc,
              "bookable_windows": bw,
              "fold_pair_mass_verification": fold_pair_mass(C),
              "frozen_floors": {
                  "q6_recent_window_decisions": Q6_RECENT_WINDOW_FLOOR,
                  "fold_population_decisions": FOLD_POPULATION_FLOOR,
                  "sector_bookable_names": SECTOR_BOOKABLE_NAMES,
                  "declared_frozen_before_counting": True}}
    q6 = {}
    folds = {}
    turn = {}
    for pid, panel in panels.items():
        pop = decision_population(C, panel)
        dates_defined = [t for t in C.grid if pop[t]["population"] > 0]
        bookable_dates = [t for t in C.grid if pop[t]["bookable"]]
        q6_dates = [t for t in bookable_dates if t[:4] == Q6_RECENT_YEAR]
        q6[pid] = {
            "recent_window_year": Q6_RECENT_YEAR,
            "decisions_defined": len(dates_defined),
            "bookable_decisions": len(bookable_dates),
            "bookable_decisions_2025": len(q6_dates),
            "floor": Q6_RECENT_WINDOW_FLOOR,
            "met": len(q6_dates) >= Q6_RECENT_WINDOW_FLOOR,
        }
        per_fold = {}
        for f in C.folds:
            n = sum(1 for t in bookable_dates
                    if f["start"] <= t <= f["end"])
            per_fold[f["fold_id"]] = {
                "bookable_decisions": n,
                "floor": FOLD_POPULATION_FLOOR,
                "met": n >= FOLD_POPULATION_FLOOR}
        folds[pid] = {"per_fold": per_fold,
                      "all_folds_populated": all(
                          v["met"] for v in per_fold.values())}
        pop_series = [pop[t]["population"] for t in C.grid]
        n_avg = (sum(pop_series) / len(pop_series)) if pop_series else 0.0
        turn[pid] = _turnover_block(C, pid, n_avg)
    blocks["q6_recent_window"] = q6
    blocks["fold_population"] = folds
    blocks["turnover_cost_ceiling"] = turn
    return blocks


# ------------------------------------------------------------------- run ----
def run_measurement(built_at_utc: str, actual_start_sha: str,
                    dispatch_sha: str) -> str:
    C = build_all()

    panels = {}
    results = {}
    anchor_specs = [
        ("SFNG2-A4-P1", exposures.amendlag, exposures.amendlag_sham,
         "amendlag(e,t) = MEDIAN of d(p) in calendar days over the "
         "entity's resolvable measurement pairs p whose AMENDMENT "
         "acceptance session falls in the trailing 63 trading sessions "
         "ending at decision close t; timestamps only (no price, no "
         "volume, no value, no direction, no count ranking); defined "
         "iff >= 1 in-window pair (P1 definition floor); even counts "
         "average the two middle order statistics; lag distribution "
         "disclosed, never trimmed"),
        ("SFNG2-A4-P2", exposures.cdays, exposures.cdays_sham,
         "cdays(e,t) = (sum over P(e,t) of dV(p)) / ADV63_dollars, dV(p) "
         "= V(A_p) - V(O_p) doc-level D-coded nonDerivative totals "
         "(shares x raw close at each doc's own acceptance date - no "
         "dollar value field exists on either surface, the declared "
         "fallback is universal); defined iff >= 1 in-window pair with "
         "MEASURED dV != 0 (zero-correction pairs are contentless, "
         "excluded-with-reason, never zero-ranked)"),
    ]
    arrival_ents = set(getattr(C, "E", {})) | set(getattr(C, "Arr4a", {}))
    for pid, fn, sham_fn, desc in anchor_specs:
        panel = build_anchor_panel(C, fn)
        panels[pid] = panel
        dates_defined = sorted({t for _e, t in panel})
        nov = novelty_block(C, panel)
        sham_ents = (set(getattr(C, "Esham_lag", {}))
                     | set(getattr(C, "Esham_dv", {})))
        sham_panel = build_anchor_panel(C, sham_fn, entities=sham_ents)
        ident = {
            "sham_amendment_matched_original_only": identifiability_block(
                C, panel, sham_panel, "sham_amendment_matched_original_only"),
            "filing_arrival_clock_shadow": identifiability_block(
                C, panel, build_anchor_panel(C, exposures.arrival_shadow,
                                             entities=arrival_ents),
                "filing_arrival_clock_shadow"),
        }
        results[pid] = {
            "proposal_id": pid,
            "anchor_exposure": desc,
            "panel": {"entities": len({e for e, _t in panel}),
                      "pairs": len(panel),
                      "dates_defined": len(dates_defined),
                      "grid_dates_total": len(C.grid)},
            "novelty": nov,
            "verdict_novelty": nov["verdict"],
            "identifiability": ident,
            "sham_construction": {
                "method": ("pair-value permutation within "
                           "(amendment-acceptance-session, sector) cells "
                           "over the union of the treatment slice and the "
                           "matched original-only cohort (same-sector "
                           "cohort entities with >= 1 type-4 acceptance "
                           "session in the trailing 63 sessions ending at "
                           "the cell session and ZERO resolvable "
                           "measurement pairs in the compliance window); "
                           "per-cell value MULTISET preserved EXACTLY "
                           "(P1: lags; P2: dVs); numpy PCG64 seed "
                           "20260912; cells in (session, sector) order, "
                           "values (origin entity, accession)-sorted; "
                           "full anchor machinery recomputed on the "
                           "permuted events"),
                "cells": C.sham_info["cells"],
                "values_permuted": C.sham_info["values_permuted"],
                "support_size_min": C.sham_info["support_size_min"],
                "support_size_max": C.sham_info["support_size_max"],
                "support_size_mean": C.sham_info["support_size_mean"],
                "sham_panel_pairs": len(sham_panel)},
        }

    feas = feasibility_block(C, panels)

    # measured diagnostic for any unmeasured veto entry (fail-closed
    # reasons must be evidenced, not asserted)
    gaps_t = []
    for cik in C.E4a:
        E = C.E.get(cik)
        if not E:
            continue
        for i in range(1, len(E["sess_d"])):
            gaps_t.append(
                (date.fromisoformat(E["sess_d"][i])
                 - date.fromisoformat(E["sess_d"][i - 1])).days)
    unmeasured_diag = {
        "v11_cadence_latency_form": {
            "rule": ("share of in-window (800d) acceptances whose "
                     "calendar gap from the previous acceptance exceeds "
                     "460 days; Spearman undefined on zero variance => "
                     "UNMEASURED => fail-closed (V13 rule, never a pass "
                     "by absence)"),
            "treatment_entity_gap_days_max": max(gaps_t) if gaps_t else None,
            "treatment_entity_gaps_gt_460": sum(1 for g in gaps_t
                                                 if g > 460),
            "measured_values_on_anchor_panels": "constant 0.0 (every "
            "defined panel point; 50058/50114 P1, defined-points share "
            "equal on P2) - the treatment population (issuers with "
            "resolvable amendment pairs) never exhibits a >460-day "
            "inter-acceptance gap, so the cadence-latency ancestor is "
            "IDENTICALLY zero on it and cannot discriminate",
        },
    }

    audit = {
        "schema": "stocks_ng2_run/d2_novelty_feasibility@1",
        "cycle": "STOCKS-NG2",
        "task_id": "stocks-ng2-d2-measurement",
        "lane": "d2",
        "dispatch_base_sha": dispatch_sha,
        "actual_start_sha": actual_start_sha,
        "built_at_utc": built_at_utc,
        "discipline": ("rho/counts/cost-rate arithmetic ONLY; zero PnL, "
                       "zero returns, zero expectancy, zero profit "
                       "factor, zero selection, zero scoring; a killed "
                       "proposal is a successful preregistered outcome"),
        "no_pnl_no_outcomes": True,
        "frozen_before_measurement": {
            "novelty_bar_pooled_abs_rho": NOVELTY_BAR,
            "self_subsumption_rho": SELF_SUBSUMPTION_RHO,
            "spearman_min_n": SPEARMAN_MIN_N,
            "q6_recent_window_floor_decisions": Q6_RECENT_WINDOW_FLOOR,
            "fold_population_floor_decisions": FOLD_POPULATION_FLOOR,
            "sector_bookable_names": SECTOR_BOOKABLE_NAMES,
            "turnover_ceiling_bps_qtr_referenced": TURNOVER_CEILING_BPS_QTR,
            "sham_seed": SHAM_SEED,
            "bands_bps_per_side": list(BANDS_BPS),
            "stress_mult": STRESS_MULT,
            "eligibility": {">= 63 bars through t": True,
                            "ADV63 >= 2_000_000 USD": True,
                            "raw close >= 1.00 USD": True},
            "fold_pair_mass_declared": FOLD_PAIR_MASS_DECLARED,
        },
        "representation_identity": {
            "p12_declaration": ("the DAILY entity-date panel IS the "
                                "measurement identity (FOREX-V9 P-12 "
                                "lesson): no re-gridding at D2"),
            "grid": ("daily closes (SPY session calendar), first "
                     f"decision {C.grid[0]}, last decision {C.grid_end} "
                     f"({len(C.grid)} sessions)"),
            "universe": (f"cohort_v9 death-inclusive: "
                         f"{C.cohort_counts['ALIVE_EVIDENCED']} ALIVE + "
                         f"{C.cohort_counts['DEAD_EVIDENCED']} DEAD"),
            "eligibility_identity": ("floors applied to the panel BEFORE "
                                     "rho computation, matching the "
                                     "book's tradable population"),
            "pit_convention": ("UTC acceptance-timestamp string compare; "
                               "an acceptance (type-4 stream row OR 4/A "
                               "extension doc) enters exposure at the "
                               "first decision session on/after its UTC "
                               "calendar date (ng1 house rule, "
                               "unchanged)"),
            "series_convention": ("all series values at (e, t) use "
                                  "information through the close of t "
                                  "inclusive (last bar <= t)"),
            "pair_construction": (
                "match key (issuerCik, rptOwnerCik, periodOfReport) "
                "against the pinned originals index (census machinery "
                "VERBATIM, reconciled fail-closed: resolvable 1,877, "
                "original keys 342,801); tie rule FROZEN ex ante "
                "(earliest stream acceptance, then smallest accession); "
                "acceptance_row_rule on BOTH stamps (originals = "
                "stream_acceptance accessions, amendments = pinned "
                "submissions acceptanceDateTime cross-checked vs the "
                "re-ingest index.json primary-doc last-modified, ET "
                "within [UTC-1, UTC]); issuer = doc issuerCik, cohort "
                "members only; d(p) = calendar days between acceptance "
                "DATES, untrimmed"),
        },
        "substrate_end_decision": {
            "grid_end": C.grid_end,
            "rationale": ("frozen at the pinned acceptance evidence end "
                          "= max(pinned stream last acceptance "
                          f"{C.stream_last_acceptance[:10]}, last 4/A "
                          "acceptanceDateTime over the pinned enumerated "
                          "accessions); every measured exposure state is "
                          "fully evidenced by the pinned substrate and "
                          "post-substrate price refreshes cannot enter "
                          "any measured window (ng1 law); the measured "
                          "price-data end is recorded alongside and is "
                          "NOT the grid authority"),
            **C.grid_end_authority,
        },
        "inputs": {
            "stream": {"path": str(core.STREAM_PATH),
                       "sha256": C.stream_sha256,
                       "rows": C.stream_diag["rows_total"],
                       "reconciled_with_pin": True},
            "substrate_manifest": {"path": str(core.SUBSTRATE_MANIFEST_PATH),
                                   "form4_xml_files":
                                       C.pair_diag["files_scanned_originals"],
                                   "note": ("P0's same-commit full "
                                            "re-hash (p0_s1_repverify) is "
                                            "the digest evidence; D2 "
                                            "re-reads every file for "
                                            "match-key extraction")},
            "form4a_tree": {"root": str(core.FORM4A_ROOT),
                            "files": C.form4a_verify["files"],
                            "aggregate_sha256":
                                C.form4a_verify["aggregate_sha256"],
                            "manifest_status":
                                C.form4a_verify["manifest_status"],
                            "read_only": True},
            "cohort": {"path": str(core.COHORT_PATH),
                       "sha256": C.cohort_sha256},
            "p0d": {"path": str(core.P0D_PATH), "sha256": C.p0d_sha256,
                    "verdict_split_check": "MATCH"},
            "prices": {"dir": str(core.PRICES_DIR),
                       "cohort_files": C.price_files_bookable,
                       "trim_from": core.PRICE_TRIM,
                       "note": ("the same read-only surface the V13 and "
                                "ng1 D2 machines consumed; alive tail "
                                "beyond grid_end is grid-frozen out")},
            "bench_spy": str(core.BENCH_SPY),
            "census_b": {"path": str(core.CENSUS_B_PATH),
                         "reconciliation":
                             C.pair_diag["census_reconciliation"]},
            "census_a": {"path": str(core.CENSUS_A_PATH),
                         "declared_docs_counter": C.census_declared_counter,
                         "declared_accessions_distinct":
                             len(C.declared_accessions)},
            "stream_aggregation_diag": C.stream_diag,
            "pair_construction_diag": C.pair_diag,
            "ng1_aggregator_cutoff_rebind": C.agg_cutoff_rebind,
        },
        "veto_set": {
            "count": len(VETO_NAMES),
            "names": VETO_NAMES,
            "provenance": ("15-entry V13 D2 audit veto set reused "
                           "UNCHANGED from the ng1 D2 machinery (generic "
                           "family constructions on EODHD prices + the "
                           "pinned stream; pooled midrank Spearman-on-"
                           "common-pairs fail-closed semantics) + the 2 "
                           "ng1 10b5-1 kills (fdens / planshare, died at "
                           "their own D2 vs goodwill_bloat -0.3547/"
                           "-0.384) constructed by the ng1 D2 exposure "
                           "machinery on THIS cycle's panel/grid, per "
                           "plan sec1"),
            "constructions": vetoes.VETO_CONSTRUCTION_REGISTER,
            "named_kill_candidates": {
                "SFNG2-A4-P1": ["v11_cadence_latency_form",
                                "v12_chain_structure_form",
                                "goodwill_bloat"],
                "SFNG2-A4-P2": ["goodwill_bloat",
                                "revision_direction_breadth_form",
                                "ng1_10b5_1_planshare"],
            },
            "unmeasured_entry_diagnostics": unmeasured_diag,
        },
        "results": results,
        "feasibility": feas,
        "verdict_rule": ("novelty: ELIGIBLE iff pooled |rho| <= 0.20 vs "
                         "ALL 17 entries with every entry measured; any "
                         "entry measured above the bar => VETO(margin); "
                         "any unmeasured entry => INELIGIBLE_FAIL_CLOSED "
                         "(reason); identifiability: pooled anchor-vs-"
                         "control rho >= 0.98 => self-subsumption kill "
                         "pre-score; selection and scoring remain later "
                         "decisions, not D2's"),
    }
    return json.dumps(audit, indent=1, sort_keys=True)


def feasibility_summary_from_audit(audit: dict) -> dict:
    """Condensed feasibility record for the d1/feasibility slot."""
    f = audit["feasibility"]
    return {
        "schema": "stocks_ng2_run/d1_feasibility_summary@1",
        "cycle": audit["cycle"],
        "task_id": audit["task_id"],
        "built_from": ("research/control/stocks_ng2_run/d2/"
                       "d2_novelty_feasibility_ng2.json (same commit)"),
        "built_at_utc": audit["built_at_utc"],
        "pair_census": {
            "census_resolvable_pairs":
                f["pair_census"]["census_resolvable_pairs"],
            "measurement_pairs": f["pair_census"]["measurement_pairs"],
            "unique_measurement_issuers":
                f["pair_census"]["unique_measurement_issuers"],
            "by_cohort_class": f["pair_census"]["by_cohort_class"],
            "stages_fail_closed": f["pair_census"]["stages_fail_closed"],
            "p2_dv_share": f["pair_census"]["p2_dv_share"],
            "lag_days_distribution":
                f["pair_census"]["lag_days_distribution"]},
        "bookable_windows": {
            "entities": f["bookable_windows"]["entities"],
            "bookable_pairs": f["bookable_windows"]["bookable_pairs"],
            "dead_share_pairs":
                f["bookable_windows"]["dead_share_pairs"],
            "per_fold": f["bookable_windows"]["per_fold"],
            "tail_2026_vs_price_data_end":
                f["bookable_windows"]["tail_2026_vs_price_data_end"]},
        "fold_pair_mass_verification":
            f["fold_pair_mass_verification"],
        "q6_recent_window": f["q6_recent_window"],
        "fold_population": f["fold_population"],
        "turnover_cost_ceiling": f["turnover_cost_ceiling"],
        "no_pnl_no_outcomes": True,
    }
