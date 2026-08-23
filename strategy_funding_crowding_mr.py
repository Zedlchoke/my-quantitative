"""Funding-crowding gated reclaim mean-reversion — H-FUNDCROWD-MR-v2.

Sprint-V2 PHASE 2 research strategy (owner A4). The frozen
``strategy_reclaim_mr`` entry/exit engine is wrapped behind a NEW
pre-registered funding-percentile entry gate; the baseline module itself is
NOT modified. Spec: research/hypotheses/H-FUNDCROWD-MR-v2/candidate.yaml
(PLAN.md §11 contract, family ``funding_crowding``).

Gate (point-in-time strict, fail-closed)
----------------------------------------
Feature = point_in_time_funding_percentile: percentile rank of the most
recently SETTLED funding rate within its trailing 30d window of published
settlements, queried at ``decision_ts`` = the CURRENT signal bar's CLOSE
timestamp (``bar.ts_event``) — the moment of decision. No future row can be
observed because :class:`research.funding_pit.FundingPIT` only exposes
settlements with ``fundingTime <= ts``.

* LONG  blocked when ``percentile > threshold_p / 100``      (crowded longs).
* SHORT blocked when ``percentile <= (100 - threshold_p)/100`` (crowded shorts).
* Any ``FundingPIT`` failure (missing bundle, insufficient history, no
  settlement asof) BLOCKS BOTH sides — never guesses. Every block increments
  the ``funding_gate_blocks`` counter attribute.

Trial budget: exactly 3 combinations — ``threshold_p`` {70, 75, 80} with HTF
filter fixed ON and OI explicitly excluded from the signal. All other
parameters copy ``config.settings.ReclaimMeanReversionSettings`` defaults
EXACTLY and must not be tuned. Deterministic; settings live in THIS module
(config/settings.py is outside A4 ownership).
"""

from __future__ import annotations

from dataclasses import dataclass

from nautilus_trader.config import PositiveFloat
from nautilus_trader.config import PositiveInt
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide

from research.funding_pit import FundingPIT
from strategy_base import BaseFuturesStrategyConfig
from strategy_reclaim_mr import ReclaimMeanReversionStrategy

HYPOTHESIS_ID = "H-FUNDCROWD-MR-v2"
STRATEGY_TYPE = "funding_crowding"

# Frozen pre-registered trial grid (3 combinations, PLAN.md §11).
THRESHOLD_P_GRID = (70, 75, 80)

# Fixed gate constants (not tuned this candidate version).
FUNDING_WINDOW_DAYS = 30.0
DEFAULT_FUNDING_BUNDLE_DIR = "funding_data/scan_2026"

# Declared warmup for every grid combination (>= 320 bars).
DEFAULT_WARMUP_BARS = 320


@dataclass(frozen=True)
class FundingCrowdingMRSettings:
    """Research-facing settings (module-local by design).

    Only ``threshold_p`` is a trial knob. Every other value is FIXED for
    H-FUNDCROWD-MR-v2: the reclaim-MR block duplicates
    ``ReclaimMeanReversionSettings`` defaults exactly.
    """

    threshold_p: int = 70  # GRID {70, 75, 80}
    funding_window_days: float = FUNDING_WINDOW_DAYS  # fixed
    # -- frozen reclaim-MR baseline (identical to ReclaimMeanReversionSettings)
    bb_period: int = 20
    bb_k: float = 2.0
    rsi_period: int = 2
    rsi_oversold: float = 15.0
    rsi_overbought: float = 85.0
    vhf_period: int = 28
    vhf_max: float = 0.25
    adx_period: int = 14
    adx_max: float = 20.0
    volume_sma_period: int = 20
    volume_max_ratio: float = 1.8
    atr_period: int = 14
    atr_stop_multiple: float = 1.5
    take_profit_multiple: float = 2.0
    history_days: int = 220
    phase_gate: bool = True

    def validate(self) -> None:
        if self.threshold_p not in THRESHOLD_P_GRID:
            raise ValueError(
                f"threshold_p must be one of {THRESHOLD_P_GRID}, got {self.threshold_p!r}"
            )
        if self.funding_window_days <= 0:
            raise ValueError("funding_window_days must be > 0")
        if self.bb_period <= 0 or self.rsi_period <= 0 or self.vhf_period <= 0:
            raise ValueError("reclaim-MR indicator periods must be > 0")
        if not 0 <= self.rsi_oversold < self.rsi_overbought <= 100:
            raise ValueError("RSI levels must satisfy 0 <= oversold < overbought <= 100")
        if self.adx_period <= 0 or self.volume_sma_period <= 0:
            raise ValueError("reclaim-MR periods must be > 0")
        if self.vhf_max <= 0 or self.adx_max <= 0 or self.volume_max_ratio <= 0:
            raise ValueError("reclaim-MR thresholds must be > 0")
        if self.atr_stop_multiple <= 0 or self.take_profit_multiple <= 0:
            raise ValueError("reclaim-MR stop/TP must be > 0")

    def warmup_bars(self) -> int:
        """Declared warmup: widest indicator ramp plus a fixed exploratory floor."""
        needed = max(self.bb_period, self.vhf_period, self.adx_period) + max(
            self.bb_period, self.volume_sma_period, self.atr_period
        )
        return max(DEFAULT_WARMUP_BARS, needed)

    @classmethod
    def parameter_grid(cls) -> list["FundingCrowdingMRSettings"]:
        """The frozen 3-combination trial grid (order is deterministic)."""
        return [cls(threshold_p=threshold) for threshold in THRESHOLD_P_GRID]

    def to_nautilus_config(
        self,
        instrument_id,
        bar_type,
        *,
        enable_trading: bool = False,
        request_historical_bars: bool = True,
        **risk_kwargs,
    ) -> "FundingCrowdingMRConfig":
        """Build the Nautilus strategy config from these frozen settings.

        Mirrors the vol-compression module's factory pattern. Unlike the
        long-only breakout hypothesis, the shared risk ``allow_short``
        kwarg stays in ``risk_kwargs`` (shorts are part of this hypothesis).
        """
        return FundingCrowdingMRConfig(
            instrument_id=instrument_id,
            bar_type=bar_type,
            threshold_p=float(self.threshold_p),
            funding_window_days=self.funding_window_days,
            bb_period=self.bb_period,
            bb_k=self.bb_k,
            rsi_period=self.rsi_period,
            rsi_oversold=self.rsi_oversold,
            rsi_overbought=self.rsi_overbought,
            vhf_period=self.vhf_period,
            vhf_max=self.vhf_max,
            adx_period=self.adx_period,
            adx_max=self.adx_max,
            volume_sma_period=self.volume_sma_period,
            volume_max_ratio=self.volume_max_ratio,
            atr_stop_multiple=self.atr_stop_multiple,
            take_profit_multiple=self.take_profit_multiple,
            history_days=self.history_days,
            phase_gate=self.phase_gate,
            enable_trading=enable_trading,
            request_historical_bars=request_historical_bars,
            **risk_kwargs,
        )


class FundingCrowdingMRConfig(BaseFuturesStrategyConfig, frozen=True):
    """Nautilus config for the funding-crowding gated reclaim-MR hypothesis."""

    threshold_p: float = 70.0
    funding_window_days: PositiveFloat = FUNDING_WINDOW_DAYS
    # Frozen reclaim-MR block (defaults identical to ReclaimMeanReversionStrategyConfig)
    bb_period: PositiveInt = 20
    bb_k: PositiveFloat = 2.0
    rsi_period: PositiveInt = 2
    rsi_oversold: float = 15.0
    rsi_overbought: float = 85.0
    vhf_period: PositiveInt = 28
    vhf_max: float = 0.25
    adx_period: PositiveInt = 14
    adx_max: float = 20.0
    volume_sma_period: PositiveInt = 20
    volume_max_ratio: float = 1.8
    take_profit_multiple: float = 2.0
    phase_gate: bool = True


class FundingCrowdingMRStrategy(ReclaimMeanReversionStrategy):
    """Reclaim-MR entries gated by point-in-time funding percentile.

    All entry/exit logic (Bollinger reclaim, RSI extreme, range + phase gates,
    ATR stop / TP management, daily-risk limits) is inherited UNCHANGED from
    :class:`strategy_reclaim_mr.ReclaimMeanReversionStrategy`. This subclass
    only (a) records each signal bar's close timestamp as ``decision_ts`` and
    (b) interposes the pre-registered crowding gate in front of
    :meth:`_submit_entry`.
    """

    config: FundingCrowdingMRConfig

    def __init__(
        self,
        config: FundingCrowdingMRConfig,
        funding_pit=None,  # research.funding_pit.FundingPIT | None
    ) -> None:
        if not 0 < config.threshold_p < 100:
            raise ValueError(
                f"threshold_p must be in (0, 100), got {config.threshold_p!r}"
            )
        if config.funding_window_days <= 0:
            raise ValueError("funding_window_days must be > 0")
        super().__init__(config)
        self._injected_funding_pit = funding_pit
        self._funding_pit = funding_pit
        #: Cumulative count of entry signals blocked by the crowding gate
        #: (diagnostic across resets; never decremented).
        self.funding_gate_blocks = 0
        #: Close timestamp (epoch ms) of the current signal bar — set at the
        #: top of :meth:`on_bar`, BEFORE any decision uses it.
        self.last_decision_ts_ms: int | None = None

    # -- funding PIT resolution ------------------------------------------------ #

    def _resolve_funding_pit(self):
        """Injected instance wins; otherwise build once from the default bundle."""
        if self._funding_pit is None:
            symbol = str(self.config.instrument_id.symbol).removesuffix("-PERP")
            self._funding_pit = FundingPIT(symbol, DEFAULT_FUNDING_BUNDLE_DIR)
        return self._funding_pit

    def _gate_allows(self, side: OrderSide) -> tuple[bool, str | None]:
        """Pre-registered crowding gate. Fail-closed on any PIT failure."""
        pit = self._resolve_funding_pit()
        if pit is None:
            return False, "funding_pit_unavailable"
        decision_ts_ms = self.last_decision_ts_ms
        if decision_ts_ms is None:
            # No signal bar processed yet -> nothing observable -> block.
            return False, "no_decision_timestamp"
        percentile, reason = pit.percentile_asof(
            decision_ts_ms, window_days=self.config.funding_window_days
        )
        if reason is not None or percentile is None:
            return False, f"funding_pit_{reason or 'unavailable'}"
        long_block_level = self.config.threshold_p / 100.0
        short_block_level = (100 - self.config.threshold_p) / 100.0
        if side == OrderSide.BUY:
            if percentile > long_block_level:
                return False, "crowded_long_funding"
        else:
            if percentile <= short_block_level:
                return False, "crowded_short_funding"
        return True, None

    # -- main loop ------------------------------------------------------------- #

    def on_bar(self, bar: Bar) -> None:
        # Decision timestamp FIRST: every query below sees exactly the close
        # time of the bar under evaluation (no lookahead, no clock drift).
        self.last_decision_ts_ms = int(bar.ts_event) // 1_000_000
        super().on_bar(bar)

    def _submit_entry(
        self,
        side: OrderSide,
        close: float,
        atr: float,
        stop_multiple: float | None = None,
        risk_scale: float = 1.0,
    ) -> bool:
        allowed, reason = self._gate_allows(side)
        if not allowed:
            self.funding_gate_blocks += 1
            self.log.info(
                f"{side.name} entry blocked by funding-crowding gate: {reason}",
            )
            return False
        super()._submit_entry(side, close, atr, stop_multiple, risk_scale)
        return True

    # -- reset ------------------------------------------------------------------#

    def _on_reset(self) -> None:
        super()._on_reset()
        self.last_decision_ts_ms = None
