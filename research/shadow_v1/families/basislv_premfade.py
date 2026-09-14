"""BASISLV-PREMFADE-28D family adapter (plan section 3.2, lane A8).

Historical family A14-V14-A5-BASISLV-PREMFADE, historical verdict
``V14_FAMILY_REJECT`` — retained verbatim, never rewritten.

Frozen mechanism (identity manifest, verbatim):
- signal: "mean_15m_perp_index_premium_level" — trailing 28 days of
  completed 15-minute perp-vs-index premium buckets per symbol
  (anchor_formation_buckets = 2688 = 28 x 96);
- side rule: "long = floor(n_eligible/3) lowest premium (low/discount
  tier), short = floor(n_eligible/3) highest premium (high/premium
  tier), equal weight 1/(2*floor(n_eligible/3)), gross 1.0, middle
  flat, ranks ascend by (b_i, symbol id), min 12 eligible names,
  max |w| = 0.125 <= 0.30";
- clock: weekly, every Monday 00:00:00Z; one declared execution lag;
- fill rule: "fills at the close of the first completed 15m bar
  strictly after the decision stamp (Monday 00:15:00Z close)". The
  adapter only DECLARES this reference rule; execution runs through
  the shared A2 fill convention;
- tie-break: symbol_id_ascending_on_equal_b_i;
- benchmark_symbols_excluded: BTCUSDT (never traded by this family);
- holding 7 days; funding is booked once by the engine while held and
  is NEVER a signal input (price-only premium fade is the mechanism;
  funding_sign_convention LONG_PAYS_POSITIVE_RATE lives in accounting).

Per-name weights are clamped to the manifest bounds: the equal-weight
construction must satisfy |w| <= designed_max_abs_weight (0.125) which
is itself <= adapter_weight_cap_max (0.30); a violation is fail-closed.

Counterfactual diagnostics (56d neighbour, sign-inverted book) are NOT
built here — arm_id namespaces are reserved strings only.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Dict, List, Mapping, Optional, Tuple

from research.shadow_v1.data_feed import DataBlocked, parse_iso_z
from research.shadow_v1.families import (
    BARS_PER_DAY_15M,
    DECISION_CLOCK_WEEKLY_MONDAY,
    FamilyAdapter,
    FamilySnapshot,
    IdentityConfigError,
    DecisionProposal,
    parse_verbatim_number,
    parse_verbatim_symbol_list,
)

_TIER_DIVISOR_RE = re.compile(r"floor\(n_eligible/(\d+)\)")
_WEIGHT_TOL = 1e-12


def _check_weekly_monday_clock(decision_utc: str) -> dt.datetime:
    moment = parse_iso_z(decision_utc)
    if moment.weekday() != 0 or (moment.hour, moment.minute, moment.second) != (0, 0, 0):
        raise ValueError(
            "BASISLV-PREMFADE-28D decides weekly Monday 00:00:00Z, got "
            f"{decision_utc!r}"
        )
    return moment


class BasislvPremfadeAdapter(FamilyAdapter):
    """Trailing 28-day perp-vs-index premium level tercile book."""

    FAMILY_ID = "BASISLV-PREMFADE-28D"
    HISTORICAL_FAMILY_ID = "A14-V14-A5-BASISLV-PREMFADE"
    HISTORICAL_VERDICT_LABEL = "V14_FAMILY_REJECT"
    ARM_ID = "BASISLV-PREMFADE-28D"
    EXIT_POLICY = "scheduled weekly rebalance; rank removal; risk-cap block"
    DECISION_CLOCK = DECISION_CLOCK_WEEKLY_MONDAY
    HOLDING_PERIOD = "7D"
    MANIFEST_FAMILY_ID = "BASISLV-PREMFADE-28D"

    @staticmethod
    def build_frozen(identity_params: Mapping[str, Any]) -> Dict[str, Any]:
        side_rule = str(identity_params["side_rule"])
        match = _TIER_DIVISOR_RE.search(side_rule)
        if match is None:
            raise IdentityConfigError(
                f"BASISLV-PREMFADE-28D: cannot parse tier divisor from side "
                f"rule {side_rule!r}"
            )
        tier_divisor = int(match.group(1))
        frozen: Dict[str, Any] = {
            "anchor_arm_id": str(identity_params["anchor_arm_id"]),
            "anchor_arm_config_id": str(identity_params["anchor_arm_config_id"]),
            "formation_buckets": parse_verbatim_number(
                identity_params["anchor_formation_buckets"], "anchor_formation_buckets"
            ),
            "formation_days": parse_verbatim_number(
                identity_params["anchor_formation_days"], "anchor_formation_days"
            ),
            "tier_divisor": tier_divisor,
            "min_eligible": int(
                parse_verbatim_number(identity_params["min_eligible"], "min_eligible")
            ),
            "gross": parse_verbatim_number(identity_params["gross"], "gross"),
            "designed_max_abs_weight": parse_verbatim_number(
                identity_params["designed_max_abs_weight"], "designed_max_abs_weight"
            ),
            "adapter_weight_cap_max": parse_verbatim_number(
                identity_params["adapter_weight_cap_max"], "adapter_weight_cap_max"
            ),
            "direction": str(identity_params["direction"]),
            "funding_sign_convention": str(identity_params["funding_sign_convention"]),
            "side_rule_verbatim": side_rule,
            "tie_break": str(identity_params["tie_break"]),
            "holding_days": parse_verbatim_number(
                identity_params["holding_days"], "holding_days"
            ),
            "benchmark_symbols_excluded": parse_verbatim_symbol_list(
                identity_params["benchmark_symbols_excluded"],
                "benchmark_symbols_excluded",
            ),
            "fill_rule_verbatim": str(identity_params["fill_rule"]),
            "signal_name": str(identity_params["signal_name"]),
            "neighbour_arm_id_reserved": str(identity_params["neighbour_arm_id"]),
            "control_arm_id_reserved": str(identity_params["control_arm_id"]),
        }
        if frozen["anchor_arm_id"] != BasislvPremfadeAdapter.FAMILY_ID:
            raise IdentityConfigError(
                f"BASISLV-PREMFADE-28D: anchor_arm_id "
                f"{frozen['anchor_arm_id']!r} disagrees with family id"
            )
        if frozen["formation_buckets"] != frozen["formation_days"] * BARS_PER_DAY_15M:
            raise IdentityConfigError(
                f"BASISLV-PREMFADE-28D: formation_buckets "
                f"{frozen['formation_buckets']!r} != formation_days x "
                f"{BARS_PER_DAY_15M}"
            )
        if frozen["direction"] != "long_short_dollar_neutral":
            raise IdentityConfigError(
                f"BASISLV-PREMFADE-28D: unexpected direction "
                f"{frozen['direction']!r}"
            )
        if frozen["funding_sign_convention"] != "LONG_PAYS_POSITIVE_RATE":
            raise IdentityConfigError(
                "BASISLV-PREMFADE-28D: unexpected funding sign convention "
                f"{frozen['funding_sign_convention']!r}"
            )
        if frozen["designed_max_abs_weight"] > frozen["adapter_weight_cap_max"]:
            raise IdentityConfigError(
                "BASISLV-PREMFADE-28D: designed max |w| exceeds adapter cap"
            )
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
        decision_dt = _check_weekly_monday_clock(decision_utc)
        cutoff_dt = parse_iso_z(feature_cutoff_utc)
        if cutoff_dt >= decision_dt:
            raise DataBlocked(
                f"feature cutoff {feature_cutoff_utc} is not before decision "
                f"{decision_utc}; PIT window empty"
            )

        formation_days = int(frozen["formation_days"])
        required_buckets = int(frozen["formation_buckets"])
        excluded = set(frozen["benchmark_symbols_excluded"])

        signals: Dict[str, float] = {}
        rejected: Dict[str, str] = {}
        for symbol in sorted(data_snapshot.basis_buckets):
            if symbol in excluded:
                rejected[symbol] = "benchmark_excluded"
                continue
            try:
                mean_premium = self._mean_premium(
                    data_snapshot.basis_buckets.get(symbol) or (),
                    required_buckets,
                    formation_days + 1,
                    cutoff_dt,
                    decision_dt,
                )
            except _IncompleteFormation as exc:
                rejected[symbol] = f"insufficient_formation_buckets: {exc}"
                continue
            except _InvalidBucket as exc:
                rejected[symbol] = f"invalid_bucket: {exc}"
                continue
            signals[symbol] = mean_premium

        eligible = sorted(signals, key=lambda s: (signals[s], s))
        min_eligible = int(frozen["min_eligible"])
        if len(eligible) < min_eligible:
            raise DataBlocked(
                f"BASISLV-PREMFADE-28D: {len(eligible)} eligible names, "
                f"{min_eligible} required (min_eligible)"
            )
        tier_size = len(eligible) // int(frozen["tier_divisor"])
        long_tier = eligible[:tier_size]
        short_tier = eligible[-tier_size:]
        weight = 1.0 / (2.0 * tier_size)
        # Weight clamp: equal-weight construction must respect the frozen
        # designed bound (itself <= adapter cap); fail closed otherwise.
        if abs(weight) > float(frozen["designed_max_abs_weight"]) + _WEIGHT_TOL:
            raise DataBlocked(
                f"BASISLV-PREMFADE-28D: equal weight {weight!r} exceeds "
                f"designed max {frozen['designed_max_abs_weight']!r}"
            )

        target_weights: Dict[str, float] = {}
        for symbol in long_tier:
            target_weights[symbol] = weight
        for symbol in short_tier:
            target_weights[symbol] = -weight

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
                "tier_size": tier_size,
                "long_tier": list(long_tier),
                "short_tier": list(short_tier),
                "gross_by_construction": abs(weight) * 2.0 * tier_size,
                "designed_max_abs_weight": frozen["designed_max_abs_weight"],
                "adapter_weight_cap_max": frozen["adapter_weight_cap_max"],
                "fill_reference_rule": frozen["fill_rule_verbatim"],
                "formation_buckets": required_buckets,
                "holding_days": frozen["holding_days"],
            },
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _mean_premium(
        buckets: Any,
        required_buckets: int,
        max_span_days: int,
        cutoff_dt: dt.datetime,
        decision_dt: dt.datetime,
    ) -> float:
        """Mean premium over the trailing ``required_buckets`` completed
        15m buckets (anchor_formation_buckets = 2688 = 28 x 96 nominal).

        The trailing-count reading reconciles the frozen 2688-bucket
        formation with the strict A2 PIT completion rule: at a Monday
        00:00Z stamp the bar opening 23:45 closes exactly at the stamp,
        so the last calendar day contributes 95 completed buckets. The
        mean is taken over the LAST 2688 completed buckets, which never
        spans more than formation_days + 1 calendar days.
        """
        completed: List[Tuple[dt.datetime, float]] = []
        for bucket in buckets:
            open_dt = parse_iso_z(str(bucket["open_time_utc"]))
            close_dt = parse_iso_z(str(bucket["close_time_utc"]))
            if not (close_dt <= cutoff_dt and close_dt < decision_dt):
                continue  # not completed strictly before the decision
            index_price = float(bucket["index_price"])
            futures_price = float(bucket["futures_price"])
            if index_price <= 0.0 or futures_price <= 0.0:
                raise _InvalidBucket("non-positive price")
            completed.append((open_dt, futures_price / index_price - 1.0))
        if len(completed) < required_buckets:
            raise _IncompleteFormation(
                f"{len(completed)} completed buckets available, "
                f"{required_buckets} required"
            )
        completed.sort(key=lambda r: r[0])
        window = completed[-required_buckets:]
        span = window[-1][0] - window[0][0]
        if span > dt.timedelta(days=max_span_days):
            raise _IncompleteFormation(
                f"trailing {required_buckets} buckets span {span}; more than "
                f"{max_span_days} days"
            )
        return sum(p for _, p in window) / required_buckets


class _IncompleteFormation(Exception):
    """Internal: formation grid is not PIT-complete for one symbol."""


class _InvalidBucket(Exception):
    """Internal: a basis bucket carries unusable prices."""
