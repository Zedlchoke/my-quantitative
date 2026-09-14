"""ILLIQ-AMIHUD-28D-W family adapter (plan section 3.1, lane A8).

Historical family A8-V11-ILLIQ-AMIHUD, historical verdict
``V11_FAMILY_REJECT`` — retained verbatim, never rewritten.

Frozen mechanism (identity manifest, verbatim):
- feature: "28d mean daily Amihud |r|/dollar-volume (15m agg daily UTC)"
- book: "long illiquid / short liquid quintiles, beta-neutral"
- clock: "Mondays 00:00:00Z; features from completed 15m bars + last
  COMPLETED OI 5m row strictly before stamp; one declared execution lag
  after availability"
- universe: "20 staged binance_bar symbols; PIT eligibility by listing
  + DV filter; quintile buckets as specced"

Implementation of the prose universe rule (no numeric threshold is
pinned by the manifest, so the thresholds are engine config, fail
closed):
- PIT listing: a symbol is eligible only if its listing evidence
  (first completed bar) is at least ``engine.min_listing_age_days``
  old at the decision stamp;
- DV filter: the trailing mean daily dollar volume over the formation
  window must be at least ``engine.min_daily_dollar_volume``.

Daily aggregation from completed 15-minute bars per UTC day (open-time
date, 96 bars/day): sum quote volume, compound closes (last close of
the day vs last close of the previous day). The trailing window carries
one extra base day so the formation window yields exactly
``formation_days`` daily returns.

Dollar neutrality is exact by construction (long notional ==
short notional: equal counts x equal weight). BTC-beta neutrality is
enforced by the engine through the frozen risk caps
(risk.check_and_apply) using snapshot betas; the adapter reports the
book beta as a diagnostic.

Counterfactual diagnostics (56d neighbour, inverted book) are NOT
built here — arm_id namespaces are reserved strings only. Funding is
never read by this adapter: it is an accounting cost/credit booked by
the engine, never a signal input (plan section 3.1).
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Mapping, Optional, Tuple

from research.shadow_v1.data_feed import DataBlocked, parse_iso_z
from research.shadow_v1.families import (
    BARS_PER_DAY_15M,
    DECISION_CLOCK_WEEKLY_MONDAY,
    FamilyAdapter,
    FamilySnapshot,
    IdentityConfigError,
    DecisionProposal,
    parse_leading_int,
    parse_verbatim_number,
)


def _check_weekly_monday_clock(decision_utc: str) -> dt.datetime:
    moment = parse_iso_z(decision_utc)
    if moment.weekday() != 0 or (moment.hour, moment.minute, moment.second) != (0, 0, 0):
        raise ValueError(
            "ILLIQ-AMIHUD-28D-W decides weekly Monday 00:00:00Z, got "
            f"{decision_utc!r}"
        )
    return moment


class IlliqAmihudAdapter(FamilyAdapter):
    """Trailing 28-day Amihud illiquidity quintile book, weekly Monday."""

    FAMILY_ID = "ILLIQ-AMIHUD-28D-W"
    HISTORICAL_FAMILY_ID = "A8-V11-ILLIQ-AMIHUD"
    HISTORICAL_VERDICT_LABEL = "V11_FAMILY_REJECT"
    ARM_ID = "ILLIQ-AMIHUD-28D-W"
    EXIT_POLICY = "scheduled weekly rebalance; rank removal; risk-cap block"
    DECISION_CLOCK = DECISION_CLOCK_WEEKLY_MONDAY
    HOLDING_PERIOD = "7D"
    MANIFEST_FAMILY_ID = "ILLIQ-AMIHUD-28D-W"

    @staticmethod
    def build_frozen(identity_params: Mapping[str, Any]) -> Dict[str, Any]:
        bucketing = str(identity_params["bucketing"])
        if "quintile" not in bucketing:
            raise IdentityConfigError(
                f"ILLIQ-AMIHUD-28D-W: bucketing prose {bucketing!r} does not "
                "specify quintile buckets; refusing"
            )
        universe_rule = str(identity_params["universe"])
        frozen: Dict[str, Any] = {
            "anchor_arm_id": str(identity_params["anchor_arm_id"]),
            "formation_days": parse_verbatim_number(
                identity_params["formation_days"], "formation_days"
            ),
            "holding_days": parse_verbatim_number(
                identity_params["holding_days"], "holding_days"
            ),
            "quintiles": 5,  # from "quintile buckets as specced" (structural)
            "expected_staged_universe_size": parse_leading_int(
                universe_rule, "universe"
            ),
            "book_rule_verbatim": str(identity_params["book"]),
            "universe_rule_verbatim": universe_rule,
            "decision_clock_verbatim": str(identity_params["decision_clock"]),
            "bucketing_verbatim": bucketing,
            "neighbour_arm_id_reserved": str(identity_params["neighbour_arm_id"]),
            "control_arm_id_reserved": str(identity_params["control_arm_id"]),
            "gross_by_construction": 1.0,
            "dollar_neutral": True,
            "btc_beta_neutral": True,
        }
        if frozen["anchor_arm_id"] != IlliqAmihudAdapter.FAMILY_ID:
            raise IdentityConfigError(
                f"ILLIQ-AMIHUD-28D-W: anchor_arm_id "
                f"{frozen['anchor_arm_id']!r} disagrees with family id"
            )
        if frozen["formation_days"] <= 0 or frozen["holding_days"] <= 0:
            raise IdentityConfigError("ILLIQ-AMIHUD-28D-W: non-positive window")
        return frozen

    @classmethod
    def required_engine_keys(cls) -> tuple:
        return (
            "min_listing_age_days",
            "min_daily_dollar_volume",
            "btc_beta_tolerance",
            "hard_gross_cap",
            "hard_abs_net_cap",
        )

    # ------------------------------------------------------------------
    def decide(
        self,
        data_snapshot: FamilySnapshot,
        decision_utc: str,
        feature_cutoff_utc: str,
        previous_weights: Optional[Mapping[str, float]] = None,
    ) -> DecisionProposal:
        frozen = self.config["frozen"]
        engine = self.config["engine"]
        decision_dt = _check_weekly_monday_clock(decision_utc)
        cutoff_dt = parse_iso_z(feature_cutoff_utc)
        if cutoff_dt >= decision_dt:
            raise DataBlocked(
                f"feature cutoff {feature_cutoff_utc} is not before decision "
                f"{decision_utc}; PIT window empty"
            )

        formation_days = int(frozen["formation_days"])
        quintiles = int(frozen["quintiles"])
        # Formation dates: the last `formation_days` UTC dates before the
        # decision, plus one base day supplying the prior close.
        base_date = (decision_dt - dt.timedelta(days=formation_days + 1)).date()
        expected_dates = [base_date + dt.timedelta(days=k) for k in range(formation_days + 1)]
        formation_dates = expected_dates[1:]

        signals: Dict[str, float] = {}
        dv_means: Dict[str, float] = {}
        rejected: Dict[str, str] = {}

        min_listing_age = float(engine["min_listing_age_days"])
        listing_cutoff_dt = decision_dt - dt.timedelta(days=min_listing_age)
        min_dv = float(engine["min_daily_dollar_volume"])

        for symbol in sorted(data_snapshot.bars):
            listing_utc = None
            if data_snapshot.listing_utc is not None:
                listing_utc = data_snapshot.listing_utc.get(symbol)
            if listing_utc is None:
                bars_all = data_snapshot.bars.get(symbol) or ()
                listing_utc = bars_all[0]["open_time_utc"] if bars_all else None
            if listing_utc is None:
                rejected[symbol] = "no_bars_in_snapshot"
                continue
            if parse_iso_z(listing_utc) > listing_cutoff_dt:
                rejected[symbol] = "pit_listing_too_recent"
                continue

            try:
                daily = self._daily_aggregates(
                    data_snapshot.bars.get(symbol) or (),
                    expected_dates,
                    cutoff_dt,
                    decision_dt,
                )
            except _IncompleteFormation as exc:
                rejected[symbol] = f"insufficient_formation_bars: {exc}"
                continue

            closes = [daily[d][0] for d in formation_dates]
            dvs = [daily[d][1] for d in formation_dates]
            if any(dv <= 0.0 for dv in dvs):
                rejected[symbol] = "zero_dollar_volume"
                continue
            prev_closes = [daily[d][0] for d in expected_dates[:-1]]
            amihud_values = []
            for close, prev_close, dv in zip(closes, prev_closes, dvs):
                daily_return = close / prev_close - 1.0
                amihud_values.append(abs(daily_return) / dv)
            amihud = sum(amihud_values) / len(amihud_values)
            dv_mean = sum(dvs) / len(dvs)
            if dv_mean < min_dv:
                rejected[symbol] = "below_dv_filter"
                continue
            signals[symbol] = amihud
            dv_means[symbol] = dv_mean

        eligible = sorted(signals, key=lambda s: (-signals[s], s))
        if len(eligible) < quintiles:
            raise DataBlocked(
                f"ILLIQ-AMIHUD-28D-W: {len(eligible)} eligible names; quintile "
                f"buckets require at least {quintiles}"
            )
        quintile_size = len(eligible) // quintiles
        long_book = eligible[:quintile_size]
        short_book = eligible[-quintile_size:]
        weight = 1.0 / (2.0 * quintile_size)

        target_weights: Dict[str, float] = {}
        for symbol in long_book:
            target_weights[symbol] = weight
        for symbol in short_book:
            target_weights[symbol] = -weight

        betas = data_snapshot.btc_betas
        book_beta: Optional[float] = None
        if betas is not None and all(s in betas for s in target_weights):
            book_beta = sum(
                w * float(betas.get(s, 0.0)) for s, w in target_weights.items()
            )

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
                "quintile_size": quintile_size,
                "long_book": list(long_book),
                "short_book": list(short_book),
                "book_btc_beta": book_beta,
                "btc_beta_tolerance": float(engine["btc_beta_tolerance"]),
                "trailing_daily_dollar_volume": dv_means,
                "formation_days": formation_days,
                "holding_days": frozen["holding_days"],
                "long_notional": weight * quintile_size,
                "short_notional": -weight * quintile_size,
            },
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _daily_aggregates(
        bars: Any,
        expected_dates: List[dt.date],
        cutoff_dt: dt.datetime,
        decision_dt: dt.datetime,
    ) -> Dict[dt.date, Tuple[float, float]]:
        """Group completed 15m bars into UTC days: (last close, sum DV)."""
        grouped: Dict[dt.date, List[Tuple[dt.datetime, float, float]]] = {
            day: [] for day in expected_dates
        }
        for bar in bars:
            open_dt = parse_iso_z(str(bar["open_time_utc"]))
            close_dt = parse_iso_z(str(bar["close_time_utc"]))
            if not (close_dt <= cutoff_dt and close_dt < decision_dt):
                continue  # not completed strictly before the decision
            day = open_dt.date()
            if day in grouped:
                grouped[day].append((open_dt, float(bar["close_price"]), float(bar["quote_volume"])))
        required_bars = BARS_PER_DAY_15M
        daily: Dict[dt.date, Tuple[float, float]] = {}
        last_day = expected_dates[-1]
        for day in expected_dates:
            rows = grouped[day]
            # PIT boundary: a bar opening 23:45 on the last calendar day
            # closes exactly AT the Monday 00:00Z stamp, so it is not yet
            # completed strictly before the decision (A2 frozen feature
            # rule: open + interval < decision). The last day therefore
            # contributes 95 completed bars, every earlier day 96.
            expected = required_bars - 1 if day == last_day else required_bars
            if len(rows) != expected:
                raise _IncompleteFormation(
                    f"{day.isoformat()} has {len(rows)} completed 15m bars, "
                    f"{expected} required"
                )
            rows.sort(key=lambda r: r[0])
            daily[day] = (rows[-1][1], sum(r[2] for r in rows))
        return daily


class _IncompleteFormation(Exception):
    """Internal: formation window is not PIT-complete for one symbol."""
