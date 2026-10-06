"""FX-F5 CIP / rate-differential overlay adapter — MACHINERY-ONLY (NEEDS_EVIDENCE).

PROPOSED; PB2 HOLD stands. 0 standalone identities: this package implements ONLY
the host-stratum split machinery (diff > 0 HIGH / diff <= 0 LOW, vintage as-of)
and the fail-closed evidence gate. The measurement harness is
meas_fx/meas_fx_m1_m3_cip_vintage.py — referenced, never duplicated. The
adapter structurally cannot emit a standalone signal (overlay law; DC s.1.3).
"""
from __future__ import annotations

import fx_common
from fx_common import RefusedPendingEvidence

FAMILY = "FX-F5"
STANDALONE_IDENTITIES = 0     # IDENTITY_BUDGET s.2: overlays carry no option cells
HARNESS = "meas_fx/meas_fx_m1_m3_cip_vintage.py"

VINTAGE_FLIP_MEASURED = {"6E": {"latest_vintage_r": 0.9097, "pit_asof_r": -0.107},
                         "6B": {"pearson_r": 0.8423, "spearman_r": 0.7445,
                                "n_rolls": 27}}


def require_f5_evidence() -> None:
    """NEEDS_EVIDENCE gate: CIP-vintage sensitivity quantification NOT_RUN +
    the owner real-time SOFR source decision (court s.d row 7) is mandatory
    before any F5-conditioned registration."""
    raise RefusedPendingEvidence(
        "F5_CIP_VINTAGE_QUANTIFICATION_NOT_RUN",
        "vintage flip r +0.9097 (latest) vs -0.107 (PIT as-of) measured on 6E; "
        "owner real-time SOFR decision (court s.d row 7) mandatory; harness: "
        f"{HARNESS} (referenced, not duplicated); PB2 HOLD stands")


def build_strata(series: list[dict]) -> dict:
    """Host-day strata from an injected differential series:
    diff > 0 -> HIGH, diff <= 0 -> LOW; as-of vintage stamps carried through."""
    out = {}
    for row in series:
        diff = float(row["diff_pp"])
        out[row["date"]] = {"stratum": "HIGH" if diff > 0 else "LOW",
                            "diff_pp": diff, "vintage_asof": row.get("vintage_asof")}
    return out


def build_observables(panel: dict, calendar: dict, sym: str,
                      differential_series: list[dict]) -> dict:
    fx_common.require_synthetic(panel)
    if sym not in fx_common.SYMBOLS:
        raise ValueError(f"unknown symbol {sym!r}")
    strata = build_strata(differential_series)
    return {"family": FAMILY, "symbol": sym, "kind": "OVERLAY_SPLIT",
            "standalone_identities": STANDALONE_IDENTITIES,
            "strata": strata, "vintage_law": "as-of decision date only",
            "mde_inflation": "sqrt2 (host n halved per stratum) — disclosed",
            "measured_correlations": VINTAGE_FLIP_MEASURED[sym],
            "provenance": panel["provenance"]}


def apply_exclusions(panel: dict, calendar: dict, sym: str) -> dict:
    """Pass-through posture only: the HOST family's exclusion pass governs."""
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
            "evidence_gate": "F5_CIP_VINTAGE_QUANTIFICATION_NOT_RUN "
                             "(require_f5_evidence raises)",
            "ancestry_fence": "standalone differential entry OUT-OF-LAW "
                              "(DC s.1.3 + H-G); rows 56/64/65/83 bind",
            "proposed": "PROPOSED — machinery only; not a scored signal",
            "decision_slot_dependencies": fx_common.decision_slot_dependencies()}
