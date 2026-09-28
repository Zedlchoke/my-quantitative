"""Lane E gate evaluation — the PREREGISTERED bars (G3_FREEZE + r1), applied
mechanically with margins-to-fail. No new bars, no tuning.

Bar order (preregistered; first fired name goes into KILLED_BY_<bar>):
  cell-level:
    PF_BAR_1X          pooled PF >= 1.10 at x1.0 (freeze floor bar)
    FOLD_BAR           >=3 of 4 folds net-positive at x1.0 (freeze ">=2/3"
                       with 4 folds -> >=3, preregistered in A7/go record)
    CONCENTRATION_BAR  max single-name share of |book net| <= 20%
    DROP_ONE_BAR       anchor verdict class unchanged after removing the
                       largest-|net| name
    STRESS_BAR         net expectancy > 0 at x2.0 (survival bar, dispatch E2)
  identity-level (fired once, kill the identity => every cell):
    BAND1_DATEONLY     net_expectancy(date-only control) >= 0.50 x
                       net_expectancy(anchor) at x1.0 pooled (r1 Band 1;
                       adjudicated only when the anchor net > 0)
    BAND2_STRATA       E[gross, anchor strata S1uS3uS4uWKND] -
                       E[gross, N2 monitored S2] <= measured round-trip band
                       cost at x2.0 => identity DIES (r1 Band 2, gross basis)
    PERMUTED_PLACEBO   a permuted-acceptance draw reproduces >= 0.50 of the
                       anchor net expectancy at x1.0 (0.50 = the r1 ILLIQ
                       convention; "reproduction => clock is noise")

Reported diagnostics (no numeric bar preregistered): clock-only shadow
expectancy, buy-and-hold equal-weight cohort baseline per fold.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from . import score as S

PF_BAR = 1.10
FOLD_BAR_MIN_POSITIVE = 3          # of 4
CONCENTRATION_BAR = 0.20
BAND1_RATIO_BAR = 0.50
PLACEBO_REPRODUCTION_BAR = 0.50    # r1 ILLIQ convention, disclosed
FOLD_ORDER = ("F1", "F2", "F3", "F4")


def _pf_pass(agg: dict) -> bool:
    return agg["pf_class"] == "NO_LOSSES" or (agg["pf"] is not None and agg["pf"] >= PF_BAR)


def fold_positive_count(fold_aggs: dict) -> int:
    return sum(1 for f in FOLD_ORDER
               if f in fold_aggs and fold_aggs[f]["net_expectancy_bps"] is not None
               and fold_aggs[f]["net_expectancy_bps"] > 0)


def cell_bars(records: Sequence[dict], arm_label: str) -> dict:
    """Evaluate the cell-level bars for one arm's book. Returns bar verdicts
    with margins + the aggregate payloads at x1.0/x1.5/x2.0."""
    agg1 = S.aggregate([S.event_net_return(r, 1.0) for r in records])
    agg15 = S.aggregate([S.event_net_return(r, 1.5) for r in records])
    agg2 = S.aggregate([S.event_net_return(r, 2.0) for r in records])
    folds1 = S.fold_aggregates(records, 1.0, FOLD_ORDER)
    folds15 = S.fold_aggregates(records, 1.5, FOLD_ORDER)
    folds2 = S.fold_aggregates(records, 2.0, FOLD_ORDER)
    conc = S.concentration(records, 1.0)

    # ---- drop-one (largest |sum net| name at x1.0) ----
    victim = S.largest_net_name(records, 1.0)
    dropped = S.drop_records_of_name(records, victim) if victim else records
    agg1_d = S.aggregate([S.event_net_return(r, 1.0) for r in dropped])
    folds1_d = S.fold_aggregates(dropped, 1.0, FOLD_ORDER)
    class_before = {
        "pf_pass": _pf_pass(agg1),
        "net_positive": agg1["net_expectancy_bps"] is not None and agg1["net_expectancy_bps"] > 0,
        "folds_positive": fold_positive_count(folds1),
    }
    class_after = {
        "pf_pass": _pf_pass(agg1_d),
        "net_positive": agg1_d["net_expectancy_bps"] is not None and agg1_d["net_expectancy_bps"] > 0,
        "folds_positive": fold_positive_count(folds1_d),
    }
    drop_one_unchanged = (
        class_before["pf_pass"] == class_after["pf_pass"]
        and class_before["net_positive"] == class_after["net_positive"]
        and (class_before["folds_positive"] >= FOLD_BAR_MIN_POSITIVE)
        == (class_after["folds_positive"] >= FOLD_BAR_MIN_POSITIVE)
    )

    pos_folds = class_before["folds_positive"]
    bars = {
        "PF_BAR_1X": {
            "fired": not _pf_pass(agg1),
            "value": agg1["pf"],
            "bar": PF_BAR,
            "margin": None if agg1["pf"] is None else round(agg1["pf"] - PF_BAR, 4),
            "note": "margin = PF - 1.10 (negative => fired); NO_LOSSES passes",
        },
        "FOLD_BAR": {
            "fired": pos_folds < FOLD_BAR_MIN_POSITIVE,
            "value": pos_folds,
            "bar": FOLD_BAR_MIN_POSITIVE,
            "margin": pos_folds - FOLD_BAR_MIN_POSITIVE,
            "fold_nets_bps_1x": {f: folds1[f]["net_expectancy_bps"] for f in sorted(folds1)},
            "fold_n_positive": {f: folds1[f]["positive_events"] for f in sorted(folds1)},
        },
        "CONCENTRATION_BAR": {
            "fired": conc["max_share"] is not None and conc["max_share"] > CONCENTRATION_BAR,
            "value": conc["max_share"],
            "bar": CONCENTRATION_BAR,
            "margin": None if conc["max_share"] is None else round(CONCENTRATION_BAR - conc["max_share"], 6),
            "top": conc["top"],
        },
        "DROP_ONE_BAR": {
            "fired": not drop_one_unchanged,
            "dropped_name": victim,
            "class_before": class_before,
            "class_after": class_after,
            "pf_after": agg1_d["pf"],
            "net_bps_after": agg1_d["net_expectancy_bps"],
            "note": "verdict class = (PF-bar pass, net sign, folds-positive>=3) triple unchanged",
        },
        "STRESS_BAR": {
            "fired": agg2["net_expectancy_bps"] is None or agg2["net_expectancy_bps"] <= 0,
            "value": agg2["net_expectancy_bps"],
            "bar": 0.0,
            "margin": None if agg2["net_expectancy_bps"] is None else round(agg2["net_expectancy_bps"], 4),
            "note": "survival = net expectancy > 0 at x2.0 (margin = net bps at x2.0)",
        },
    }
    return {
        "arm": arm_label,
        "n_events": agg1["n"],
        "agg_1x": agg1,
        "agg_1_5x": agg15,
        "agg_2x": agg2,
        "folds_1x": folds1,
        "folds_1_5x": folds15,
        "folds_2x": folds2,
        "concentration": conc,
        "drop_one": bars["DROP_ONE_BAR"],
        "bars": bars,
    }


def identity_bars(
    anchor_records: Sequence[dict],
    n2_records: Sequence[dict],
    dateonly_anchor_records: Sequence[dict],
    permuted_records_by_draw: Dict[int, List[dict]],
) -> dict:
    """Identity-level preregistered kills (r1 Band 1 / Band 2 + placebo)."""
    anchor_net = S.net_expectancy_bps(anchor_records, 1.0)
    anchor_gross = S.net_expectancy_bps(anchor_records, 1.0, gross=True)
    n2_gross = S.net_expectancy_bps(n2_records, 1.0, gross=True)

    # ---- Band 1: date-only kill (adjudicated only for positive anchors) ----
    do_net = S.net_expectancy_bps(dateonly_anchor_records, 1.0)
    if anchor_net is not None and anchor_net > 0 and do_net is not None:
        ratio = round(do_net / anchor_net, 4)
        band1 = {
            "adjudicated": True,
            "fired": ratio >= BAND1_RATIO_BAR,
            "value": ratio,
            "bar": BAND1_RATIO_BAR,
            "margin": round(BAND1_RATIO_BAR - ratio, 4),
            "dateonly_net_bps_1x": do_net,
            "anchor_net_bps_1x": anchor_net,
            "note": "identity DIES if ratio >= 0.50 (r1 Band 1, ILLIQ convention)",
        }
    else:
        band1 = {
            "adjudicated": False,
            "fired": False,
            "note": "r1: Band 1 adjudicates the redundant-clock question only "
                    "for positive anchors; anchor net <= 0 -> dead by PF/fold bars",
            "dateonly_net_bps_1x": do_net,
            "anchor_net_bps_1x": anchor_net,
        }

    # ---- Band 2: strata-spread (r1: GROSS spread vs measured RT band x2.0) ----
    rt2_measured = S.mean_round_trip_bps(anchor_records, 2.0)
    bandc_rt2 = 217.5  # frozen band-C bound: (25x3.35 + 25x1) x 2.0 = 217.50 bps
    spread = None
    if anchor_gross is not None and n2_gross is not None:
        spread = round(anchor_gross - n2_gross, 4)
    band2 = {
        "adjudicated": spread is not None and rt2_measured is not None,
        "fired": (spread is not None and rt2_measured is not None and spread <= rt2_measured),
        "value": spread,
        "threshold_measured_rt_x2_bps": rt2_measured,
        "threshold_bandc_bound_x2_bps": bandc_rt2,
        "margin": None if (spread is None or rt2_measured is None) else round(spread - rt2_measured, 4),
        "anchor_gross_bps_1x": anchor_gross,
        "n2_gross_bps_1x": n2_gross,
        "net_basis_spread_bps": None,
        "note": "r1 Band 2 canonical: gross expectancy spread <= measured RT band "
                "at x2.0 => spread is zero for decision purposes => identity DIES. "
                "Gross basis (before costs); net-basis spread reported alongside.",
    }
    anchor_net_v = S.net_expectancy_bps(anchor_records, 1.0)
    n2_net_v = S.net_expectancy_bps(n2_records, 1.0)
    if anchor_net_v is not None and n2_net_v is not None:
        band2["net_basis_spread_bps"] = round(anchor_net_v - n2_net_v, 4)

    # ---- permuted-acceptance placebo x3 ----
    # Structural-invariance check FIRST: the frozen shuffle permutes stamps
    # WITHIN issuer x form x year. Folds are year-aligned and every scored
    # field is a deterministic function of (ticker, stamp, hold), so a
    # within-group shuffle preserves the multiset of (ticker, stamp) pairs
    # and therefore the multiset of booked records — EVERY aggregate is then
    # identical to the anchor BY CONSTRUCTION and the placebo is vacuous
    # (Q-11 "a null must move the signal" can never be asked). Detected
    # mechanically here; classified NOT_INFORMATIVE, never evidence that the
    # clock is (or is not) noise.
    from collections import Counter

    def _stamp_multiset(recs):
        return Counter((r["ticker"], r.get("acceptance_utc")) for r in recs)

    def _record_multiset(recs):
        return Counter((r["ticker"], r.get("entry_session"), r["entry_price"],
                        r["exit_price"], r["direction"], r["fold"]) for r in recs)

    anchor_stamps = _stamp_multiset(anchor_records)
    anchor_record_ms = _record_multiset(anchor_records)
    draws = {}
    placebo_reproduced = False
    placebo_structurally_invariant = bool(permuted_records_by_draw)
    for draw in sorted(permuted_records_by_draw):
        drecs = permuted_records_by_draw[draw]
        stamps_invariant = _stamp_multiset(drecs) == anchor_stamps
        records_invariant = _record_multiset(drecs) == anchor_record_ms
        placebo_structurally_invariant = (
            placebo_structurally_invariant and stamps_invariant and records_invariant)
        d_net = S.net_expectancy_bps(drecs, 1.0)
        ratio = None
        if d_net is not None and anchor_net not in (None, 0):
            ratio = round(d_net / anchor_net, 4)
        reproduced = ratio is not None and ratio >= PLACEBO_REPRODUCTION_BAR
        placebo_reproduced = placebo_reproduced or reproduced
        draws[str(draw)] = {
            "net_expectancy_bps_1x": d_net,
            "ratio_vs_anchor": ratio,
            "n_records": len(drecs),
            "stamp_multiset_invariant": stamps_invariant,
            "booked_record_multiset_invariant": records_invariant,
            "reproduced_at_0.50": reproduced,
        }
    placebo = {
        "fired": placebo_reproduced and not placebo_structurally_invariant,
        "bar": PLACEBO_REPRODUCTION_BAR,
        "draws": draws,
        "structurally_invariant": placebo_structurally_invariant,
        "adjudicated": not placebo_structurally_invariant,
        "note": "anchor-level expectancy must NOT be reproduced; reproduction bar "
                "operationalized with the r1 0.50 ILLIQ convention (disclosed). "
                "SCORING-TIME FINDING: the frozen shuffle (within issuer x form x "
                "year) preserves the (ticker, stamp) multiset — booked-record "
                "multisets of every draw are EXACTLY the anchor's, so all draws "
                "reproduce the anchor BY CONSTRUCTION. The placebo is "
                "structurally non-informative: it adjudicates nothing about the "
                "clock and is NOT treated as a kill. Re-specification (owner/A1) "
                "required before any placebo-based clock adjudication.",
    }
    return {"BAND1_DATEONLY": band1, "BAND2_STRATA_SPREAD": band2,
            "PERMUTED_PLACEBO": placebo}


def clock_shadow_diagnostic(records: Sequence[dict]) -> dict:
    """Clock-only shadow expectancy (expect ~0 gross if the payload carries
    information; net carries the round-trip cost). Diagnostic only — no
    numeric bar preregistered."""
    return {
        "n_events": len(records),
        "net_expectancy_bps_1x": S.net_expectancy_bps(records, 1.0),
        "gross_expectancy_bps_1x": S.net_expectancy_bps(records, 1.0, gross=True),
        "net_expectancy_bps_2x": S.net_expectancy_bps(records, 2.0),
        "mean_round_trip_bps_1x": S.mean_round_trip_bps(records, 1.0),
        "note": "diagnostic; ~0 GROSS expected if the event payload carries "
                "information (net additionally carries the RT band cost)",
    }


def baseline_buy_hold(records: Sequence[dict]) -> dict:
    """Buy-and-hold equal-weight cohort baseline (context, not a bar):
    every anchor event taken LONG over its own window, same cost law."""
    nets = []
    folds: Dict[str, List[float]] = {}
    for r in records:
        ratio = r["exit_price"] / r["entry_price"]
        net = (ratio - 1.0) - (r["cost_entry_bps_x1"] + r["cost_exit_bps_x1"]) / S.BPS
        nets.append(net)
        folds.setdefault(r["fold"], []).append(net)
    out = {
        "pooled_net_expectancy_bps": round(sum(nets) / len(nets) * S.BPS, 4) if nets else None,
        "per_fold_net_expectancy_bps": {
            f: round(sum(v) / len(v) * S.BPS, 4) for f, v in sorted(folds.items())
        },
        "note": "buy-and-hold equal-weight cohort per fold; context only",
    }
    return out


BAR_ORDER = ("PF_BAR_1X", "FOLD_BAR", "CONCENTRATION_BAR", "DROP_ONE_BAR",
             "STRESS_BAR", "BAND1_DATEONLY", "BAND2_STRATA_SPREAD",
             "PERMUTED_PLACEBO")


def overall_verdict(cell_b: dict, ident_b: dict) -> dict:
    """Assemble the per-cell verdict: fired-bar list + overall class."""
    fired: List[str] = []
    for name in BAR_ORDER:
        if name in cell_b["bars"] and cell_b["bars"][name]["fired"]:
            fired.append(name)
    for name in ("BAND1_DATEONLY", "BAND2_STRATA_SPREAD", "PERMUTED_PLACEBO"):
        if ident_b.get(name, {}).get("fired"):
            fired.append(name)
    return {
        "fired_bars": fired,
        "overall_cell_verdict": "PASS_ALL_BARS" if not fired else f"KILLED_BY_{fired[0]}",
    }
