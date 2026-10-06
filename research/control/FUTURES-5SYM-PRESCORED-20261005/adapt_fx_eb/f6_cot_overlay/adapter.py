"""FX-F6 CoT positioning overlay adapter — MACHINERY-ONLY (NEEDS_EVIDENCE).

PROPOSED; PB2 HOLD stands. 0 standalone identities. Implements ONLY the host
stratum split (>=80 HIGH / <=20 LOW / mid MID_NEGATIVE) on the 6E host and the
fail-closed evidence gate. 6B is the measured falsifier (corr -0.074): the 6B
side returns FALSIFIER_ONLY and never conditions. The measurement harness is
meas_fx/meas_fx_m2_transfer_harness.py — referenced, never duplicated.
"""
from __future__ import annotations

import fx_common
from fx_common import RefusedPendingEvidence

FAMILY = "FX-F6"
STANDALONE_IDENTITIES = 0
HARNESS = "meas_fx/meas_fx_m2_transfer_harness.py"
HIGH_PCTILE = 80.0
LOW_PCTILE = 20.0
COT_PIT_LAW = ("CoT net-noncomm, strict-past 3y-rolling percentile, release-safe "
               "obs+3 (Tue-observe / Fri-15:30 release, as_published)")
FALSIFIER_6B = {"corr_absz_fwd_vol20": -0.074, "n": 326,
                "reading": "near-zero cross-symbol falsifier — 6B is not a leg"}


def require_f6_evidence() -> None:
    raise RefusedPendingEvidence(
        "F6_INTRADAY_TRANSFER_NOT_RUN",
        f"the fwd-21d-vol -> intraday-sign transfer IS the hypothesis and is "
        f"NOT_RUN; harness: {HARNESS} (referenced, not duplicated); any scored "
        f"future must carry the release-clock control (rows 107-109 law)")


def stratum_of(pctile: float) -> str:
    if pctile >= HIGH_PCTILE:
        return "HIGH"
    if pctile <= LOW_PCTILE:
        return "LOW"
    return "MID_NEGATIVE"


def build_strata(series: list[dict]) -> dict:
    return {row["week_end"]: {"stratum": stratum_of(float(row["pctile"])),
                              "pctile": float(row["pctile"])}
            for row in series}


def build_observables(panel: dict, calendar: dict, sym: str,
                      pctile_series: list[dict]) -> dict:
    fx_common.require_synthetic(panel)
    if sym not in fx_common.SYMBOLS:
        raise ValueError(f"unknown symbol {sym!r}")
    base = {"family": FAMILY, "symbol": sym, "kind": "OVERLAY_SPLIT",
            "standalone_identities": STANDALONE_IDENTITIES,
            "strata": build_strata(pctile_series),
            "cot_pit_law": COT_PIT_LAW,
            "mde_inflation": "sqrt2 (host n halved per stratum) — disclosed",
            "provenance": panel["provenance"]}
    if sym == "6B":
        base["falsifier"] = FALSIFIER_6B
        base["conditioning_value"] = "NONE at today's evidence (measured falsifier)"
    return base


def apply_exclusions(panel: dict, calendar: dict, sym: str) -> dict:
    fx_common.require_synthetic(panel)
    return fx_common.apply_exclusions(sym, calendar, panel, family="__none__")


def signal(observables: dict, session_date: str, exclusions: dict, sym: str,
           calendar: dict, panel: dict, **_k) -> dict:
    fx_common.require_synthetic(panel)
    return {"session_date": session_date, "family": FAMILY, "symbol": sym,
            "status": "NO_TRADE", "flags": ["OVERLAY_NO_OWN_SIGNAL"],
            "blocking": ["OVERLAY_NO_OWN_SIGNAL"],
            "standalone_identities": STANDALONE_IDENTITIES,
            "host_stratum": observables["strata"].get(session_date, {}).get("stratum"),
            "evidence_gate": "F6_INTRADAY_TRANSFER_NOT_RUN "
                             "(require_f6_evidence raises)",
            "ancestry_fence": "rows 107-109 (COMMNG1-A4-P2): the bare release-"
                              "clock control out-earned every positioning book; "
                              "standalone/release-clock constructions void",
            "proposed": "PROPOSED — machinery only; not a scored signal",
            "decision_slot_dependencies": fx_common.decision_slot_dependencies()}
