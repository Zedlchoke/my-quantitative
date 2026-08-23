"""Point-in-time (PIT) funding feature helper for Sprint V2 (owner: A2).

Consumer: A4 hypothesis H-FUNDCROWD. The bundle layout mirrors
``reports.funding._load_bundle`` conventions:
``<bundle_dir>/<SYMBOL>/funding.json`` with audit metadata
(``requested_start_ms``, ``requested_end_ms``) and ``rows`` entries carrying
``fundingTime`` (epoch ms) and ``fundingRate`` (string decimal).

Fail-closed contract
--------------------
Every query method returns ``(value, reason)``. ``value`` is ``None`` if and
only if ``reason`` is not ``None``:

* ``"empty_bundle"``      -- bundle has zero published settlements.
* ``"insufficient_history"`` -- fewer than ``min_settlements`` (default 10)
  settlements published; features must not be computed (fail-closed).
* ``"no_settlement_asof"`` -- query timestamp precedes the first published
  settlement.

Lookahead safety: ``rate_asof`` returns the LAST settlement whose published
``fundingTime <= ts`` and never invents data beyond what was published at that
point. A timestamp between two settlements therefore resolves to the OLDER
settlement. ``percentile_asof`` ranks that last rate among the trailing window
of PUBLISHED settlements only.

Usage::

    pit = FundingPIT("ETHUSDT", "funding_data/scan_2026")
    settlement, reason = pit.rate_asof("2026-01-15T05:30:00Z")
    pct, reason = pit.percentile_asof("2026-01-15T05:30:00Z", window_days=30)
    if reason is not None:
        ...  # fail closed: skip feature / mark cell incomplete
"""

from __future__ import annotations

import json
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from pathlib import Path

MIN_PUBLISHED_SETTLEMENTS = 10
MS_PER_DAY = 86_400_000


@dataclass(frozen=True)
class PITSettlement:
    """A published funding settlement as observable point-in-time."""

    funding_time_utc: str
    rate: float

    @staticmethod
    def _iso_from_ms(epoch_ms: int) -> str:
        import pandas as pd  # local import keeps module import light for callers

        return pd.Timestamp(int(epoch_ms), unit="ms", tz="UTC").isoformat()


def load_funding_bundle(root: str | Path, symbol: str) -> dict:
    """Load a funding bundle following reports.funding._load_bundle conventions."""
    path = Path(root) / symbol / "funding.json"
    if not path.exists():
        raise ValueError(f"Missing funding bundle for {symbol}: {path}")
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    required = {"requested_start_ms", "requested_end_ms", "rows"}
    missing = required.difference(payload)
    if missing:
        raise ValueError(f"Funding bundle {path} missing audit metadata: {sorted(missing)}")
    return payload


class FundingPIT:
    """Point-in-time accessor over one symbol's published funding settlements."""

    def __init__(
        self,
        symbol: str,
        bundle_dir: str | Path,
        min_settlements: int = MIN_PUBLISHED_SETTLEMENTS,
    ) -> None:
        payload = load_funding_bundle(bundle_dir, symbol)
        rows = sorted(payload["rows"], key=lambda row: int(row["fundingTime"]))
        self.symbol = str(symbol)
        self.bundle_dir = str(bundle_dir)
        self.min_settlements = int(min_settlements)
        self._times_ms: list[int] = [int(row["fundingTime"]) for row in rows]
        self._rates: list[float] = [float(str(row["fundingRate"])) for row in rows]
        self.n_settlements = len(rows)
        self.first_settlement_utc = (
            PITSettlement._iso_from_ms(self._times_ms[0]) if rows else None
        )
        self.last_settlement_utc = (
            PITSettlement._iso_from_ms(self._times_ms[-1]) if rows else None
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def rate_asof(self, ts: str | int) -> tuple[PITSettlement | None, str | None]:
        """Last published settlement with ``fundingTime <= ts``.

        Returns ``(PITSettlement, None)``, or ``(None, reason)`` when the
        fail-closed gate trips. NO forward-fill beyond published data: a
        timestamp after the last settlement still resolves to that last
        settlement (bounded by publication), never to an extrapolated value.
        """
        reason = self._gate_failure()
        if reason is not None:
            return None, reason
        ts_ms = _to_epoch_ms(ts)
        idx = bisect_right(self._times_ms, ts_ms) - 1
        if idx < 0:
            return None, "no_settlement_asof"
        return self._settlement_at(idx), None

    def percentile_asof(
        self, ts: str | int, window_days: float = 30.0
    ) -> tuple[float | None, str | None]:
        """Percentile rank of the last-asof rate within the trailing window of
        published settlements ``(ts - window_days, ts]``.

        Rank = (# window rates <= last rate) / (# window rates), in [0, 1].
        Same fail-closed gates as :meth:`rate_asof`.
        """
        if float(window_days) <= 0:
            raise ValueError(f"window_days must be positive, got {window_days!r}")
        reason = self._gate_failure()
        if reason is not None:
            return None, reason
        ts_ms = _to_epoch_ms(ts)
        idx = bisect_right(self._times_ms, ts_ms) - 1
        if idx < 0:
            return None, "no_settlement_asof"
        last_rate = self._rates[idx]
        lo_ms = ts_ms - int(round(float(window_days) * MS_PER_DAY))
        lo_idx = bisect_right(self._times_ms, lo_ms)  # half-open (ts - window, ts]
        window = self._rates[lo_idx : idx + 1]
        rank = sum(1 for rate in window if rate <= last_rate) / len(window)
        return rank, None

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _gate_failure(self) -> str | None:
        if self.n_settlements == 0:
            return "empty_bundle"
        if self.n_settlements < self.min_settlements:
            return "insufficient_history"
        return None

    def _settlement_at(self, idx: int) -> PITSettlement:
        return PITSettlement(
            funding_time_utc=PITSettlement._iso_from_ms(self._times_ms[idx]),
            rate=self._rates[idx],
        )


def _to_epoch_ms(ts: str | int) -> int:
    import pandas as pd  # local import keeps module import light for callers

    if isinstance(ts, (int, float)):
        return int(ts)
    parsed = pd.Timestamp(ts)
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    return int(parsed.value // 1_000_000)
