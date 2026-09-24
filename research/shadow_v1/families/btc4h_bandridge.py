"""Family adapter: BTC4H-BANDRIDGE (owner-mounted sleeve 4, 2026-09-24).

Frozen law (documented in plans/PLAN_prospective_shadow_v1.md amendment A1
and research/control/btc_h4_band_risk_v1/shadow_bandridge/SPEC.md):
  gate  = C3 band state on the H4 grid of BTCUSDT closes:
          ON when close > SMA200(H4) * 1.03; OFF when close < SMA200 * 0.97
          (hysteretic; NO extra dilation)
  book  = PSV1 Donchian continuation long, VERBATIM parameters:
          entry close > max(prior 30 H4 closes) only while gate ON;
          exits DONCHIAN_STOP (close < min(prior 15 H4 closes) after
          min-hold 12), GATE_INACTIVE (gate off), MAX_HOLD 450
  exec  = decision at each H4 bucket close; the engine fills at the next
          H4 open; long-only, fraction 1.0; no stops beyond the frozen law.

Identity provenance: the ancestors' verdict labels are NOT rewritable —
the Donchian arm was G6-control-killed in PHASE-STRATEGY-V1 and the C3
band book failed G5 in BTC-H4-EDGE-SEARCH-V1; this sleeve is a POSTHOC
discovery candidate mounted for prospective observation only.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Mapping, Optional

from research.shadow_v1.data_feed import DataBlocked
from research.shadow_v1.families import (
    DecisionProposal,
    FamilyAdapter,
    parse_verbatim_int_list,
    parse_verbatim_number,
)

H4_MS = 4 * 3600 * 1000


class Btc4hBandridgeAdapter(FamilyAdapter):
    FAMILY_ID = "BTC4H-BANDRIDGE"
    HISTORICAL_FAMILY_ID = (
        "PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION x ES1-C3-BAND-SMA200"
    )
    HISTORICAL_VERDICT_LABEL = (
        "POSTHOC_DISCOVERY_CANDIDATE (PSV1 arm G6-control-killed; ES1 C3 "
        "G5-killed; prospective observation only — never OOS, never live)"
    )
    ARM_ID = "BTC4H-BANDRIDGE"
    EXIT_POLICY = "BAND_GATE_DONCHIAN"
    DECISION_CLOCK = "H4_EVERY_4H_0000Z"
    HOLDING_PERIOD = "variable (Donchian law)"
    MANIFEST_FAMILY_ID = "BTC4H-BANDRIDGE"
    SYMBOL = "BTCUSDT"

    @staticmethod
    def build_frozen(identity_params: Mapping[str, Any]) -> dict:
        return {
            "band_up": parse_verbatim_number(identity_params["band_up"], "band_up"),
            "band_down": parse_verbatim_number(identity_params["band_down"], "band_down"),
            "sma_len_h4": int(parse_verbatim_number(identity_params["sma_len_h4"], "sma_len_h4")),
            "donch_entry_h4": int(parse_verbatim_number(identity_params["donch_entry_h4"], "donch_entry_h4")),
            "donch_stop_h4": int(parse_verbatim_number(identity_params["donch_stop_h4"], "donch_stop_h4")),
            "min_hold_h4": int(parse_verbatim_number(identity_params["min_hold_h4"], "min_hold_h4")),
            "max_hold_h4": int(parse_verbatim_number(identity_params["max_hold_h4"], "max_hold_h4")),
        }

    @classmethod
    def required_engine_keys(cls) -> tuple:
        return ()

    # -- decision --------------------------------------------------------
    def decide(
        self,
        data_snapshot,
        decision_utc: str,
        feature_cutoff_utc: str,
        previous_weights: Optional[Mapping[str, float]] = None,
    ) -> DecisionProposal:
        frozen = self.config["frozen"]
        bars = (data_snapshot.bars or {}).get(self.SYMBOL)
        if not bars:
            raise DataBlocked(f"{self.FAMILY_ID}: no completed bars for {self.SYMBOL}")
        cutoff = dt.datetime.fromisoformat(feature_cutoff_utc.replace("Z", "+00:00"))
        # aggregate completed 15m bars into COMPLETE H4 buckets, PIT:
        # only bars whose close_time is strictly <= feature cutoff
        buckets: dict = {}
        for bar in bars:
            ct = dt.datetime.fromisoformat(str(bar["close_time_utc"]).replace("Z", "+00:00"))
            if ct > cutoff:
                continue
            ot = dt.datetime.fromisoformat(str(bar["open_time_utc"]).replace("Z", "+00:00"))
            b = int(ot.timestamp() * 1000) // H4_MS * H4_MS
            bk = buckets.setdefault(b, {"n": 0, "close": None})
            bk["n"] += 1
            bk["close"] = float(bar["close_price"])
        h4 = [buckets[b]["close"] for b in sorted(buckets) if buckets[b]["n"] == 16]
        need = frozen["sma_len_h4"] + frozen["donch_entry_h4"]
        if len(h4) < need:
            raise DataBlocked(
                f"{self.FAMILY_ID}: need >= {need} complete H4 buckets, have {len(h4)}"
            )
        t = len(h4) - 1  # the decision bucket (its close is <= cutoff)
        sma = sum(h4[t - frozen["sma_len_h4"] + 1: t + 1]) / frozen["sma_len_h4"]
        r = h4[t] / sma - 1.0
        # hysteretic band gate: recover the prior gate state by walking back
        gate_on = False
        for s in range(t, frozen["sma_len_h4"] - 1, -1):
            sma_s = sum(h4[s - frozen["sma_len_h4"] + 1: s + 1]) / frozen["sma_len_h4"]
            r_s = h4[s] / sma_s - 1.0
            if gate_on:
                if r_s < -frozen["band_down"]:
                    gate_on = False
            else:
                if r_s > frozen["band_up"]:
                    gate_on = True
        # single forward walk (O(n)) for gate + machine
        gate_series = []
        gate_on = False
        for s in range(frozen["sma_len_h4"] - 1, t + 1):
            sma_s = sum(h4[s - frozen["sma_len_h4"] + 1: s + 1]) / frozen["sma_len_h4"]
            r_s = h4[s] / sma_s - 1.0
            if gate_on:
                if r_s < -frozen["band_down"]:
                    gate_on = False
            else:
                if r_s > frozen["band_up"]:
                    gate_on = True
            gate_series.append(gate_on)
        start = frozen["sma_len_h4"] - 1
        pos_signal = []
        state, held, off_run = 0, 0, 0
        for idx, s in enumerate(range(start, t + 1)):
            g = gate_series[idx]
            hh = h4[s - frozen["donch_entry_h4"]: s]
            ll = h4[s - frozen["donch_stop_h4"]: s]
            if state == 0:
                if g and h4[s] > max(hh):
                    state, held, off_run = 1, 0, 0
            else:
                held += 1
                off_run = 0 if g else off_run + 1
                reason = None
                if h4[s] < min(ll) and held >= frozen["min_hold_h4"]:
                    reason = "DONCHIAN_STOP"
                if reason is None and not g:
                    reason = "GATE_INACTIVE"
                if reason is None and held >= frozen["max_hold_h4"]:
                    reason = "MAX_HOLD"
                if reason:
                    state, held, off_run = 0, 0, 0
            pos_signal.append(state)
        want_long = bool(pos_signal[-1] == 1)
        weights = {self.SYMBOL: 1.0} if want_long else {}
        return DecisionProposal(
            family_id=self.FAMILY_ID,
            arm_id=self.ARM_ID,
            eligible_symbols=(self.SYMBOL,),
            rejected_symbols_with_reason={},
            signal_values={
                "band_gate_on": float(gate_series[-1]),
                "band_r": round(float(r), 6),
                "donch_state": float(state),
            },
            target_weights=weights,
            exit_policy=self.EXIT_POLICY,
            decision_utc=decision_utc,
            feature_cutoff_utc=feature_cutoff_utc,
            previous_weights=dict(previous_weights or {}),
            diagnostics={"h4_buckets_used": len(h4), "law": "frozen amendment A1"},
        )
