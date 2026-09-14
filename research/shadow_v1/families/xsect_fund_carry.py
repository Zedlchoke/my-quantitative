"""XSECT-FUND-CARRY-7D family adapter (plan section 3.3, lane A8).

Historical family H-XSECT-FUNDING-CARRY-v1 (V6 funding carry),
historical verdict ``CANDIDATE_FAIL`` — retained verbatim, with no
locked candidate.

Frozen mechanism (identity manifest, verbatim YAML lines):
- "traded_universe: [ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT,
  LINKUSDT, ADAUSDT]" — exactly these seven perpetuals;
- "benchmark_context: BTCUSDT" — BTC is context only, NEVER traded;
- "signal_clock: daily_00_00_utc" — daily 00:00Z decision;
- "feature: trailing_mean_of_published_settled_funding_only",
  "lookback_days: [1, 3, 7]" — this adapter is the 7D anchor member of
  the frozen scored-candidate set;
- "long_rule: bottom_2_funding", "short_rule: top_2_funding";
- "rebalance: 24h";
- "target_gross: 0.80", "hard_gross_cap: 1.00",
  "hard_abs_net_cap: 0.10", "max_abs_weight_per_symbol: 0.20" —
  enforced by the engine through the shared A2 risk surface
  (risk.check_and_apply); the adapter builds books that respect them
  by construction and declares the caps in its frozen config.

Minimum data availability: a symbol needs at least one settled funding
publication inside the trailing 7-day window to carry a signal;
symbols without one are ineligible. Fewer than (bottom + top) eligible
names fails closed with DataBlocked. Only settled funding strictly
before the decision stamp is used (A2 PIT rule).

The historically declared reverse control (reverse_funding_rank_3d) is
a mandatory diagnostic and never a family — namespace reserved only.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Dict, List, Mapping, Optional

from research.shadow_v1.data_feed import DataBlocked, parse_iso_z
from research.shadow_v1.families import (
    DECISION_CLOCK_DAILY,
    FamilyAdapter,
    FamilySnapshot,
    IdentityConfigError,
    DecisionProposal,
    parse_verbatim_int_list,
    parse_verbatim_number,
    parse_verbatim_symbol_list,
)

_BOTTOM_RULE_RE = re.compile(r"bottom_(\d+)_funding")
_TOP_RULE_RE = re.compile(r"top_(\d+)_funding")
_ANCHOR_LOOKBACK_RE = re.compile(r"-(\d+)D\b")
_WEIGHT_TOL = 1e-9


def _verbatim_tail(text: Any, key: str) -> str:
    """Value part of a verbatim ``key: value`` YAML line."""
    if not isinstance(text, str) or ":" not in text:
        raise IdentityConfigError(
            f"XSECT-FUND-CARRY-7D: cannot parse verbatim parameter {key!r} "
            f"from {text!r}"
        )
    return text.split(":", 1)[1].strip()


def _check_daily_clock(decision_utc: str) -> dt.datetime:
    moment = parse_iso_z(decision_utc)
    if (moment.hour, moment.minute, moment.second) != (0, 0, 0):
        raise ValueError(
            f"XSECT-FUND-CARRY-7D decides daily 00:00:00Z, got {decision_utc!r}"
        )
    return moment


class XsectFundCarryAdapter(FamilyAdapter):
    """Trailing 7-day settled-funding cross-sectional carry, daily 00Z."""

    FAMILY_ID = "XSECT-FUND-CARRY-7D"
    HISTORICAL_FAMILY_ID = "H-XSECT-FUNDING-CARRY-v1"
    HISTORICAL_VERDICT_LABEL = "CANDIDATE_FAIL"
    ARM_ID = "XSECT-FUND-CARRY-7D"
    EXIT_POLICY = "scheduled daily rebalance; rank removal; risk-cap block"
    DECISION_CLOCK = DECISION_CLOCK_DAILY
    HOLDING_PERIOD = "24H"
    MANIFEST_FAMILY_ID = "XSECT-FUND-CARRY-7D"

    @staticmethod
    def build_frozen(identity_params: Mapping[str, Any]) -> Dict[str, Any]:
        long_rule = str(identity_params["long_rule"])
        short_rule = str(identity_params["short_rule"])
        match_long = _BOTTOM_RULE_RE.search(long_rule)
        match_short = _TOP_RULE_RE.search(short_rule)
        if match_long is None or match_short is None:
            raise IdentityConfigError(
                "XSECT-FUND-CARRY-7D: cannot parse side counts from "
                f"{long_rule!r} / {short_rule!r}"
            )
        anchor_variant_full = str(identity_params["anchor_variant_recovered"])
        match_anchor = _ANCHOR_LOOKBACK_RE.search(anchor_variant_full)
        if match_anchor is None:
            raise IdentityConfigError(
                "XSECT-FUND-CARRY-7D: cannot parse anchor lookback from "
                f"{anchor_variant_full!r}"
            )
        anchor_lookback = int(match_anchor.group(1))
        lookback_options = parse_verbatim_int_list(
            identity_params["lookback_days"], "lookback_days"
        )
        if anchor_lookback not in lookback_options:
            raise IdentityConfigError(
                f"XSECT-FUND-CARRY-7D: anchor lookback {anchor_lookback} not in "
                f"frozen lookback set {lookback_options}"
            )
        universe = parse_verbatim_symbol_list(
            identity_params["traded_universe"], "traded_universe"
        )
        if not universe:
            raise IdentityConfigError("XSECT-FUND-CARRY-7D: empty traded universe")
        if len(set(universe)) != len(universe):
            raise IdentityConfigError("XSECT-FUND-CARRY-7D: duplicate universe entry")
        signal_clock = _verbatim_tail(identity_params["signal_clock"], "signal_clock")
        if signal_clock != "daily_00_00_utc":
            raise IdentityConfigError(
                f"XSECT-FUND-CARRY-7D: unexpected signal_clock {signal_clock!r}"
            )
        frozen: Dict[str, Any] = {
            "anchor_variant": anchor_variant_full.split()[0],
            "traded_universe": universe,
            "benchmark_context": _verbatim_tail(
                identity_params["benchmark_context"], "benchmark_context"
            ),
            "signal_clock": signal_clock,
            "feature_verbatim": str(identity_params["feature"]),
            "lookback_days_options": lookback_options,
            "anchor_lookback_days": anchor_lookback,
            "long_side_count": int(match_long.group(1)),
            "short_side_count": int(match_short.group(1)),
            "long_rule_verbatim": long_rule,
            "short_rule_verbatim": short_rule,
            "rebalance_hours": parse_verbatim_number(
                identity_params["rebalance"], "rebalance"
            ),
            "target_gross": parse_verbatim_number(
                identity_params["target_gross"], "target_gross"
            ),
            "hard_gross_cap": parse_verbatim_number(
                identity_params["hard_gross_cap"], "hard_gross_cap"
            ),
            "hard_abs_net_cap": parse_verbatim_number(
                identity_params["hard_abs_net_cap"], "hard_abs_net_cap"
            ),
            "max_abs_weight_per_symbol": parse_verbatim_number(
                identity_params["max_abs_weight_per_symbol"],
                "max_abs_weight_per_symbol",
            ),
            "purge_embargo_hours": parse_verbatim_number(
                identity_params["purge_embargo"], "purge_embargo"
            ),
            "negative_control_reserved": _verbatim_tail(
                identity_params["negative_control"], "negative_control"
            ),
        }
        if frozen["anchor_variant"] != XsectFundCarryAdapter.FAMILY_ID:
            raise IdentityConfigError(
                f"XSECT-FUND-CARRY-7D: anchor variant {frozen['anchor_variant']!r} "
                "disagrees with family id"
            )
        if frozen["target_gross"] > frozen["hard_gross_cap"]:
            raise IdentityConfigError(
                "XSECT-FUND-CARRY-7D: target gross exceeds hard gross cap"
            )
        if frozen["rebalance_hours"] <= 0:
            raise IdentityConfigError("XSECT-FUND-CARRY-7D: non-positive rebalance")
        return frozen

    # ------------------------------------------------------------------
    def decide(
        self,
        data_snapshot: FamilySnapshot,
        decision_utc: str,
        feature_cutoff_utc: str,
        previous_weights: Optional[Mapping[str, float]] = None,
    ) -> DecisionProposal:
        frozen = self.config["frozen"]
        decision_dt = _check_daily_clock(decision_utc)
        cutoff_dt = parse_iso_z(feature_cutoff_utc)
        # Settled funding is usable iff fundingTime < decision (A2 PIT
        # rule), so a cutoff exactly AT the daily 00:00Z stamp is the
        # natural declared feature boundary; anything later is not.
        if cutoff_dt > decision_dt:
            raise DataBlocked(
                f"feature cutoff {feature_cutoff_utc} is after decision "
                f"{decision_utc}; PIT contract violated"
            )

        lookback_days = int(frozen["anchor_lookback_days"])
        window_start_dt = decision_dt - dt.timedelta(days=lookback_days)
        universe = list(frozen["traded_universe"])
        benchmark = str(frozen["benchmark_context"])

        signals: Dict[str, float] = {}
        settlement_counts: Dict[str, int] = {}
        rejected: Dict[str, str] = {}
        considered = sorted(set(universe) | set(data_snapshot.funding_settlements))
        for symbol in considered:
            if symbol not in universe:
                rejected[symbol] = (
                    "benchmark_context_not_traded"
                    if symbol == benchmark
                    else "outside_traded_universe"
                )
                continue
            rates: List[float] = []
            for settlement in data_snapshot.funding_settlements.get(symbol) or ():
                ft_dt = parse_iso_z(str(settlement["funding_time_utc"]))
                # Only already-published settled funding strictly before the
                # decision stamp, inside the trailing lookback window.
                if window_start_dt <= ft_dt < decision_dt and ft_dt <= cutoff_dt:
                    rates.append(float(settlement["funding_rate"]))
            if not rates:
                rejected[symbol] = "insufficient_funding_history"
                continue
            signals[symbol] = sum(rates) / len(rates)
            settlement_counts[symbol] = len(rates)

        eligible = sorted(signals, key=lambda s: (signals[s], s))
        long_count = int(frozen["long_side_count"])
        short_count = int(frozen["short_side_count"])
        if len(eligible) < long_count + short_count:
            raise DataBlocked(
                f"XSECT-FUND-CARRY-7D: {len(eligible)} eligible names, "
                f"{long_count + short_count} required for the bottom/top books"
            )
        long_book = eligible[:long_count]
        short_book = eligible[-short_count:]
        per_name_weight = float(frozen["target_gross"]) / (long_count + short_count)
        if abs(per_name_weight) > float(frozen["max_abs_weight_per_symbol"]) + _WEIGHT_TOL:
            raise DataBlocked(
                f"XSECT-FUND-CARRY-7D: per-name weight {per_name_weight!r} "
                f"exceeds max_abs_weight_per_symbol "
                f"{frozen['max_abs_weight_per_symbol']!r}"
            )

        target_weights: Dict[str, float] = {}
        for symbol in long_book:
            target_weights[symbol] = per_name_weight
        for symbol in short_book:
            target_weights[symbol] = -per_name_weight

        return DecisionProposal(
            family_id=self.FAMILY_ID,
            arm_id=self.ARM_ID,
            eligible_symbols=tuple(eligible),
            rejected_symbols_with_reason=rejected,
            signal_values={s: signals[s] for s in eligible},
            target_weights=target_weights,
            exit_policy=self.EXIT_POLICY,
            decision_utc=decision_utc,
            feature_cutoff_utc=feature_cutoff_utc,
            previous_weights=dict(previous_weights or {}),
            diagnostics={
                "long_book": list(long_book),
                "short_book": list(short_book),
                "per_name_weight": per_name_weight,
                "target_gross": frozen["target_gross"],
                "hard_gross_cap": frozen["hard_gross_cap"],
                "hard_abs_net_cap": frozen["hard_abs_net_cap"],
                "max_abs_weight_per_symbol": frozen["max_abs_weight_per_symbol"],
                "lookback_days": lookback_days,
                "rebalance_hours": frozen["rebalance_hours"],
                "settlements_used": settlement_counts,
                "benchmark_context": benchmark,
            },
        )
