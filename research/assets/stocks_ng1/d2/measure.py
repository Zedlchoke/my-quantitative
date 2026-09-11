"""STOCKS-NG1 D2 measurement orchestration.

Measures, per proposal (SFNG1-A4-P1 fdens anchor, SFNG1-A4-P2 planshare
anchor), on the frozen daily entity-date panel (P-12):

  NOVELTY         pooled midrank Spearman |rho| of the anchor panel vs
                  EVERY one of the 15 veto entries on common pairs;
                  bar 0.20; margin per entry (P-2); FAIL-CLOSED on any
                  unmeasured entry -> INELIGIBLE_FAIL_CLOSED(reason).
  IDENTIFIABILITY sham-insider flag-permutation control (matched
                  no-flag support, (acceptance-session, sector) cells,
                  flag-count marginals preserved, PCG64 seed 20260911)
                  vs the anchor: pooled rho; |rho| >= 0.98 =
                  self-subsumption DESIGN-FAILURE kill pre-score; plus
                  the filing-arrival clock shadow under the same bound.
                  Q-11 null-validity distinction recorded explicitly.
  FEASIBILITY     unique flagged-issuer census; bookable post-filing
                  windows (V13 census method re-measured on this
                  substrate); Q-6 recent-window (2025) bookable-decision
                  count vs the frozen floor 30; cycle-local fold
                  populations vs the frozen floor 20 decisions/fold;
                  turnover/cost ceiling accounting (event mass -> bps at
                  bands 10/15/25 and stress x2) vs the referenced 200
                  bps/quarter rubric ceiling.

NO PnL, NO expectancy, NO profit factor, NO selection, NO scoring: the
only statistics produced are ranks, correlations of signal series,
counts and cost-rate arithmetic.  Selection and scoring remain A7+
decisions.
"""

from __future__ import annotations

import json
from datetime import date

from . import core, exposures, vetoes
from .core import (FOLD_POPULATION_FLOOR, NOVELTY_BAR, Q6_RECENT_WINDOW_FLOOR,
                   Q6_RECENT_YEAR, SECTOR_BOOKABLE_NAMES,
                   SELF_SUBSUMPTION_RHO, SPEARMAN_MIN_N,
                   TURNOVER_CEILING_BPS_QTR, VETO_NAMES, eligible, spearman)

BANDS_BPS = (10.0, 15.0, 25.0)      # A/B/C per side (inherited V13 cost model)
STRESS_MULT = 2.0                   # stress rerun multiplier (20/30/50 bps)


# ------------------------------------------------------------- eligibility --
def eligibility_series(C, cik):
    """Boolean list over C.grid for one entity; memoized on the context
    (both anchors and the sham share the same frozen floors)."""
    memo = getattr(C, "_elig", None)
    if memo is None:
        memo = C._elig = {}
    if cik in memo:
        return memo[cik]
    out = [eligible(C, cik, t) for t in C.grid]
    memo[cik] = out
    return out


def build_anchor_panel(C, exposure_fn):
    """{(cik, t): value} over the frozen eligibility panel where the
    exposure definition floor is met (P-12 representation identity)."""
    panel = {}
    ents = sorted(set(C.E.keys()) & set(C.series.keys()))
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
            f"INELIGIBLE_FAIL_CLOSED(reason={len(unmeasured)}/15 veto "
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
def flagged_issuer_census(C):
    issuers = {}
    sessions_flagged = 0
    for (cik, acc), d in C.docs.items():
        if not d["flag"]:
            continue
        si = d["session"]
        sess = C.sessions[si]
        if not (C.grid[0] <= sess <= C.grid_end):
            continue
        issuers.setdefault(cik, {"sessions": set(), "years": set()})
        issuers[cik]["sessions"].add(si)
        issuers[cik]["years"].add(sess[:4])
        sessions_flagged += 1
    by_cls = {"ALIVE_EVIDENCED": 0, "DEAD_EVIDENCED": 0}
    for cik in issuers:
        by_cls[C.bookable[cik]["cls"]] += 1
    by_year = {}
    for cik, rec in issuers.items():
        for y in rec["years"]:
            by_year[y] = by_year.get(y, 0) + 1
    return {
        "method": ("unique issuers with >= 1 DECLARED aff10b5One doc "
                   "whose stream acceptance falls in the compliance "
                   "window (doc-level flag projected onto stream rows "
                   "via the accession join, P0 census method); all "
                   "flagged issuers are cohort members (non-member "
                   "flagged rows: 0 measured)"),
        "unique_flagged_issuers": len(issuers),
        "by_cohort_class": by_cls,
        "by_year_first_flag": dict(sorted(by_year.items())),
        "flagged_entity_sessions": sessions_flagged,
        "flagged_transactions_post_2023": C.flagged_tx_post_2023,
        "flagged_transactions_by_year": C.flagged_tx_by_year,
        "census_a_crosscheck": {
            "flagged_tx_census": C.census_flagged_tx_expected,
            "flagged_tx_measured": C.flagged_tx_post_2023,
            "declared_docs_counter": C.census_declared_counter,
            "declared_accessions_distinct": len(C.declared_accessions),
            "verdict": ("MATCH" if C.flagged_tx_post_2023
                        == C.census_flagged_tx_expected else "MISMATCH"),
        },
    }


def bookable_windows_census(C):
    """Post-filing windows bookable per the V13 census method, re-measured
    on this substrate: every distinct acceptance session of a priced
    cohort entity in the compliance window opens one candidate
    STRICT_NEXT_BAR window; bookable iff >= 63 bars through the session
    AND >= 1 bar strictly after it (a fillable next-bar)."""
    pairs = dead_pairs = 0
    ents = set()
    dead_ents = set()
    per_fold = {}
    for cik, E in C.E.items():
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
            pairs += 1
            ents.add(cik)
            fold = _fold_of(C, sess)
            if fold:
                per_fold[fold] = per_fold.get(fold, 0) + 1
            if C.bookable[cik]["cls"] == "DEAD_EVIDENCED":
                dead_pairs += 1
                dead_ents.add(cik)
    return {
        "method": ("distinct acceptance sessions of priced cohort "
                   "entities in the compliance window; bookable iff "
                   ">= 63 bars through the session and >= 1 bar strictly "
                   "after (STRICT_NEXT_BAR fillability); death-inclusive "
                   "series, exit-at-last-close"),
        "entities": len(ents),
        "bookable_pairs": pairs,
        "dead_share_pairs": round(dead_pairs / pairs, 4) if pairs else None,
        "dead_entities": len(dead_ents),
        "per_fold": dict(sorted(per_fold.items())),
        "v13_backbone_reference": {"entities": 1960, "pairs": 27454,
                                   "dead_share": 0.6218,
                                   "note": "V13 census backbone over the "
                                           "2018-2025 window; this cycle's "
                                           "compliance window is "
                                           "2023-01-03..substrate_end"},
    }


def _fold_of(C, d_iso):
    for f in C.folds:
        if f["start"] <= d_iso <= f["end"]:
            return f["fold_id"]
    return None


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


def feasibility_block(C, panels):
    flag = flagged_issuer_census(C)
    bw = bookable_windows_census(C)
    blocks = {"flagged_issuer_census": flag,
              "bookable_windows": bw,
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


def _qualifying_sessions(C, pid):
    """Entry-event mass upper bound: every session that opens/re-arms one
    window per entity (P1: flagged sessions; P2: sessions carrying >= 1
    nonDerivative D-coded row), priced entities, compliance window."""
    n = 0
    for cik, E in C.E.items():
        if cik not in C.series:
            continue
        for i, si in enumerate(E["sess_idx"]):
            sess = C.sessions[si]
            if not (C.grid[0] <= sess <= C.grid_end):
                continue
            if pid.endswith("P1"):
                hit = E["cum"]["flag_sess"][i] - (
                    E["cum"]["flag_sess"][i - 1] if i > 0 else 0) > 0
            else:
                hit = E["cum"]["nndD"][i] - (
                    E["cum"]["nndD"][i - 1] if i > 0 else 0) > 0
            if hit:
                n += 1
    return n


def _turnover_block(C, pid, n_avg_population):
    events = _qualifying_sessions(C, pid)
    days = (date.fromisoformat(C.grid_end)
            - date.fromisoformat(C.grid[0])).days
    quarters = days / 91.3125
    events_q = events / quarters if quarters > 0 else None
    # normalized position-turns per quarter: each qualifying session
    # re-arms ONE position of the (on average) n_avg_population in-state
    # names; a window costs one entry + one exit fill (2 sides).
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
        "accounting": ("entry/re-arm event mass over priced cohort "
                       "entities in the compliance window (upper bound: "
                       "per-event eligibility not pre-filtered); "
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
                         "re-frozen at the NG1 invariant freeze)"),
    }


# ------------------------------------------------------------------- run ----
def run_measurement(built_at_utc: str, actual_start_sha: str,
                    dispatch_sha: str) -> str:
    C = core.build_context()
    exposures.aggregate_stream(C)

    panels = {}
    results = {}
    anchor_specs = [
        ("SFNG1-A4-P1", exposures.fdens,
         "fdens(e,t) = count of DISTINCT flagged acceptance sessions in "
         "the trailing 63 trading sessions ending at decision close t "
         "(document-level aff10b5One truthy flag projected onto stream "
         "rows via the accession join); defined iff >= 1 flagged session "
         "in window (P1 definition floor)"),
        ("SFNG1-A4-P2", exposures.planshare,
         "planshare(e,t) = V_flagged_dispose / V_all_dispose over "
         "nonDerivative D-coded rows accepted in the trailing 63 trading "
         "sessions; value = shares x raw EODHD close at the acceptance "
         "date (the stream carries no value field - declared fallback); "
         "floor: V_all >= 2,000 USD AND >= 2 D-coded rows"),
    ]
    sham_info = exposures.build_sham(C)
    sham_controls = {
        "SFNG1-A4-P1": (exposures.fdens_sham, "sham_insider_matched_noflag"),
        "SFNG1-A4-P2": (exposures.planshare_sham,
                        "sham_insider_matched_noflag"),
    }
    for pid, fn, desc in anchor_specs:
        panel = build_anchor_panel(C, fn)
        panels[pid] = panel
        dates_defined = sorted({t for _e, t in panel})
        nov = novelty_block(C, panel)
        sfn, cname = sham_controls[pid]
        sham_panel = build_anchor_panel(C, sfn)
        ident = {
            cname: identifiability_block(C, panel, sham_panel, cname),
            "filing_arrival_clock_shadow": identifiability_block(
                C, panel, build_anchor_panel(C, exposures.arrival_shadow),
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
                "method": ("flag-permutation within (acceptance-session, "
                           "sector) cells over cohort docs in the "
                           "compliance window; per-cell flag-count "
                           "marginal preserved EXACTLY; numpy PCG64 seed "
                           "20260911; cells in decision-date session "
                           "order, docs (cik, accession)-sorted; full "
                           "anchor machinery recomputed on permuted "
                           "flags"),
                "cells": sham_info["cells"],
                "docs_in_support": sham_info["docs_in_support"],
                "flagged_docs_assigned": sham_info["flagged_docs_assigned"],
                "sham_panel_pairs": len(sham_panel)},
        }

    feas = feasibility_block(C, panels)

    audit = {
        "schema": "stocks_ng1_run/d2_novelty_feasibility@1",
        "cycle": "STOCKS-NG1",
        "task_id": "stocks-ng1-d2-measurement",
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
            "sham_seed": exposures.SHAM_SEED,
            "bands_bps_per_side": list(BANDS_BPS),
            "stress_mult": STRESS_MULT,
            "eligibility": {">= 63 bars through t": True,
                            "ADV63 >= 2_000_000 USD": True,
                            "raw close >= 1.00 USD": True},
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
                               "an acceptance enters exposure at the "
                               "first decision close on/after its UTC "
                               "date; stream_acceptance rows only "
                               "(measured: 0 null-acceptance rows of "
                               "546,039)"),
            "series_convention": ("all series values at (e, t) use "
                                  "information through the close of t "
                                  "inclusive (last bar <= t)"),
        },
        "substrate_end_decision": {
            "grid_end": C.grid_end,
            "rationale": ("frozen at the pinned stream's last acceptance "
                          f"date ({C.stream_last_acceptance}): every "
                          "measured exposure state is fully evidenced by "
                          "the pinned substrate and post-substrate price "
                          "refreshes (the inherited price files' alive "
                          "tail extends beyond) cannot enter any "
                          "measured window; conservative vs the V13 "
                          "final-close reference 2025-07-24; F3 end "
                          "resolved to this date dynamically as declared"),
        },
        "inputs": {
            "stream": {"path": str(core.STREAM_PATH),
                       "sha256": C.stream_sha256,
                       "rows": C.stream_diag["rows_total"],
                       "reconciled_with_pin": True},
            "cohort": {"path": str(core.COHORT_PATH),
                       "sha256": C.cohort_sha256},
            "p0d": {"path": str(core.P0D_PATH), "sha256": C.p0d_sha256,
                    "verdict_split_check": "MATCH"},
            "prices": {"dir": str(core.PRICES_DIR),
                       "cohort_files": C.price_files_bookable,
                       "note": ("the same read-only surface the V13 D2 "
                                "machine consumed; bars trimmed from "
                                f"{core.PRICE_TRIM}; alive tail refresh "
                                "is grid-frozen out (see "
                                "substrate_end_decision)")},
            "bench_spy": str(core.BENCH_SPY),
            "census_a": {"path": str(core.CENSUS_A_PATH),
                         "declared_docs_counter": C.census_declared_counter,
                         "declared_accessions_distinct":
                             len(C.declared_accessions)},
            "stream_aggregation_diag": C.stream_diag,
        },
        "veto_set": {
            "count": len(VETO_NAMES),
            "names": VETO_NAMES,
            "provenance": ("names + method = the V13 D2 audit veto set "
                           "($L1194-1213) and its pooled midrank "
                           "Spearman-on-common-pairs fail-closed "
                           "semantics; constructions rebuilt as GENERIC "
                           "family forms on this cycle's consumption "
                           "surfaces (EODHD prices + pinned stream) per "
                           "the dispatch packet"),
            "constructions": vetoes.__doc__.strip(),
        },
        "construction_incidents": [
            {"entry": "goodwill_bloat",
             "incident": ("first generic form (derivative-table share of "
                          "all rows) had provably EMPTY support: the "
                          "pinned stream carries zero derivative-table "
                          "rows (546,039 of 546,039 rows table="
                          "nonDerivative; the derivative table is a "
                          "separate unstaged stream per the frozen parse "
                          "contract)"),
             "resolution": ("replaced BEFORE any rho for this entry "
                            "existed, on a-priori family-fidelity and "
                            "support grounds, with the NON-open-market "
                            "P/S share form (see veto_set.construct"
                            "ions entry 5); the empty-support attempt is "
                            "recorded here, not hidden"),
             "bias_disclosure": ("the replacement was chosen without "
                                 "measuring its rho against either "
                                 "anchor (no construction shopping); "
                                 "its rho is measured only after the "
                                 "form is frozen in committed code")},
        ],
        "results": results,
        "feasibility": feas,
        "verdict_rule": ("novelty: ELIGIBLE iff pooled |rho| <= 0.20 vs "
                         "ALL 15 entries with every entry measured; any "
                         "entry measured above the bar => VETO(margin); "
                         "any unmeasured entry => INELIGIBLE_FAIL_CLOSED "
                         "(reason); identifiability: pooled anchor-vs-"
                         "control rho >= 0.98 => self-subsumption kill "
                         "pre-score; selection and scoring remain A7+ "
                         "decisions, not D2's"),
    }
    return json.dumps(audit, indent=1, sort_keys=True)


def feasibility_summary_from_audit(audit: dict) -> dict:
    """Condensed feasibility record for the d1/feasibility slot."""
    f = audit["feasibility"]
    return {
        "schema": "stocks_ng1_run/d1_feasibility_summary@1",
        "cycle": audit["cycle"],
        "task_id": audit["task_id"],
        "built_from": ("research/control/stocks_ng1_run/d2/"
                       "d2_novelty_feasibility_ng1.json (same commit)"),
        "built_at_utc": audit["built_at_utc"],
        "flagged_issuer_census": {
            "unique_flagged_issuers":
                f["flagged_issuer_census"]["unique_flagged_issuers"],
            "by_cohort_class":
                f["flagged_issuer_census"]["by_cohort_class"],
            "flagged_entity_sessions":
                f["flagged_issuer_census"]["flagged_entity_sessions"],
            "flagged_transactions_post_2023":
                f["flagged_issuer_census"]["flagged_transactions_post_2023"],
            "census_a_crosscheck":
                f["flagged_issuer_census"]["census_a_crosscheck"]},
        "bookable_windows": {
            "entities": f["bookable_windows"]["entities"],
            "bookable_pairs": f["bookable_windows"]["bookable_pairs"],
            "dead_share_pairs": f["bookable_windows"]["dead_share_pairs"],
            "per_fold": f["bookable_windows"]["per_fold"]},
        "q6_recent_window": f["q6_recent_window"],
        "fold_population": f["fold_population"],
        "turnover_cost_ceiling": f["turnover_cost_ceiling"],
        "no_pnl_no_outcomes": True,
    }
