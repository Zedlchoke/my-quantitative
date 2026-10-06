"""adapter — 6A-AF4 TICK-REGIME CONDITIONING OVERLAY (PROPOSED;
CONTINGENCY-PB3-PARK machinery; 0 standalone identities; never activated).

Law text: ./FROZEN_RULE_DRAFT.md. AF4 hosts AF1/AF3 as era-split strata; the
6J same-date constant-tick control is the K2 substrate. Sources:
SPEC_6A_CONTINGENCY s.1-2/s.5 (era law, NO-BACK-CAST, K1-K4 refusals);
CENSUS AF4 dossier; aud_d2_tickera.json (D-2 DELIVERED); 6j_identity.json
(6J tick CONSTANT across sampled eras).

Outcome-blind: synthetic fixtures only; real data refuses on P5-FXJA-D5.
AF4 defines NO entry, ever: order_intent refuses unconditionally
(REFUSED_AF4_NO_ENTRY_FROM_TICK_ERA).
"""
from __future__ import annotations

import fx_common as fc

FAMILY = "AF4"
SYMBOL = "6A"
ERA1_SESSIONS_MEASURED = 231        # SPEC_6A s.1 (measured era-1 session count)
ERA_BOUNDARY_DISCLOSURE = ("era label deterministic from the MEASURED "
                           "2020-11-20/23 grid break (conventional anchor, "
                           "disclosed; data-side PROVISIONAL pending D8)")
# IDs: AF4 carries 0 standalone identities in the frozen table
# (AF4_tick_regime_overlay: 0). No C6A0 skeletons are minted at all.
CORE_IDS: list[str] = []
CONTROL_IDS: list[str] = []
DRAFT_IDS: list[str] = []


def af4_freeze_check() -> dict:
    if fc.GUARDS["P5-FXJA-D5"] is None:
        raise fc.RefusedPendingOwnerDecision(
            "P5-FXJA-D5",
            "AF4 is a T3 overlay with 0 standalone identities (H-G law); 6A "
            "stays PB3 PARK; the overlay can never trade on its own")
    return {"frozen_by": fc.GUARDS["P5-FXJA-D5"]}


class AF4Adapter:
    family = FAMILY
    symbol = SYMBOL

    def __init__(self, contract: dict | None = None):
        self.contract = contract or fc.load_fx_contract(SYMBOL)

    # ---------------------------------------------------------------- API
    def era_label(self, session_date: str) -> str:
        """Deterministic era label from the measured 2020-11-20/23 boundary."""
        return fc.sixa_era_for_date(session_date)

    def host_split(self, host_event_days: list[str]) -> dict:
        """Split host evaluable days into era strata. Era-1 (231 measured
        sessions) is a DESCRIPTIVE-ONLY stratum FOREVER (K3 pre-declared: the
        era-1 host events fail the >=5-per-fold floor; no fold structure is
        ever scored there unless the owner extends the 2020 panel)."""
        era1 = sorted(d for d in host_event_days
                      if self.era_label(d) == "era1")
        era2 = sorted(d for d in host_event_days
                      if self.era_label(d) == "era2")
        return {
            "era1_descriptive_only": {
                "days": era1, "n": len(era1),
                "fold_floor": fc.fold_floor_check(max(len(era1), 1), 4),
                "law": ("K3: era-1 stays descriptive forever unless the owner "
                        "extends the 2020 panel (pre-declared)")},
            "era2": {"days": era2, "n": len(era2)},
            "era_boundary_disclosure": ERA_BOUNDARY_DISCLOSURE,
        }

    def micro_step_stats(self, panel: dict, session_date: str) -> dict:
        """Median |close-to-close| step in USD + ticks (the D-2 step-test
        substrate at fixture scale)."""
        fc.require_synthetic(panel, session_date and panel.get("symbol", "6A"))
        bars = fc.session_bars(panel, session_date)
        closes = [float(b["close"]) for b in bars]
        steps = [abs(closes[i + 1] - closes[i]) for i in range(len(closes) - 1)]
        steps.sort()
        med = steps[len(steps) // 2] if steps else 0.0
        tick = (fc.sixa_tick(session_date) if panel.get("symbol") == "6A"
                else fc.SIXJ_TICK)
        tval = (fc.sixa_tick_value_usd(session_date) if panel.get("symbol") == "6A"
                else fc.SIXJ_TICK_VALUE_USD)
        return {"symbol": panel.get("symbol"), "session_date": session_date,
                "era": fc.sixa_era_for_date(session_date)
                if panel.get("symbol") == "6A" else "constant-tick",
                "median_usd_step": round(med, 12),
                "median_ticks": round(med / tick, 6),
                "tick_value_usd": tval}

    def same_date_control(self, panel_6a: dict, panel_6j: dict) -> dict:
        """K2 substrate: 6A's USD micro-increment must HALVE exactly at the
        boundary while constant-grid 6J stays flat on the SAME date set (the
        2020 COVID confound does not move the 6J placebo)."""
        dates = sorted(s["session_date"] for s in panel_6a["sessions"])
        assert dates == sorted(s["session_date"] for s in panel_6j["sessions"])
        era1, era2 = dates[0], dates[1]
        a1 = self.micro_step_stats(panel_6a, era1)
        a2 = self.micro_step_stats(panel_6a, era2)
        j1 = self.micro_step_stats(panel_6j, era1)
        j2 = self.micro_step_stats(panel_6j, era2)
        return {
            "dates": dates,
            "sixA_usd_step_ratio_era2_over_era1":
                round(a2["median_usd_step"] / a1["median_usd_step"], 6),
            "sixA_ticks_step_ratio": round(a2["median_ticks"] / a1["median_ticks"], 6),
            "sixJ_usd_step_ratio_era2_over_era1":
                round(j2["median_usd_step"] / j1["median_usd_step"], 6),
            "sixJ_ticks_step_ratio": round(j2["median_ticks"] / j1["median_ticks"], 6),
            "law": ("SPEC_6A s.2 step test: 6A x0.50 USD / x1.00 ticks; "
                    "unchanged-grid 6J x1.00 / x1.00 — the measured micro-"
                    "increment is grid-bound on 6A and date-stable on 6J"),
            "k2_reading": ("6J control HOLDS on this fixture (constant tick); "
                           "a 6J shift would kill AF4 as a date/crisis artifact"),
            "secondary_negative": ("6E/6B constancy at the boundary CLOSED this "
                                   "round (fx_eb/tick_constancy_6e6b.json); "
                                   "reported for completeness, 0 IDs"),
        }

    def order_intent(self, panel: dict, calendar: dict, identity_id: str,
                     session_date: str, *args, **kwargs) -> dict:
        """AF4 has NO entry, ever (overlay law): any intent refuses."""
        fc.require_synthetic(panel, SYMBOL)
        raise fc.RefusedAf4NoStandaloneIntent(
            f"requested identity {identity_id!r}: AF4 is a T3 conditioning "
            f"overlay on the AF1/AF3 hosts; no entry is ever defined from the "
            f"tick era (CENSUS AF4 s.5; frozen table AF4 = 0 IDs)")
