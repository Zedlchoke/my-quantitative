"""PIT data interface + keyless public REST client (plan sections 2, 8, G2).

Implements the frozen endpoints from
``research/control/prospective_shadow_v1/data_cost/data_manifest.json``:

- GET /fapi/v1/klines          completed 15m close + quote-volume bars
- GET /futures/data/basis      completed 15m perp-vs-index basis buckets
- GET /fapi/v1/fundingRate     settled funding history
- GET /fapi/v1/time, /fapi/v1/exchangeInfo  (measured supplementary)

PIT rules (frozen):
- a bar/bucket is FEATURE-eligible iff open + interval < decision_utc
  (fully completed STRICTLY BEFORE the decision);
- a virtual fill references the first completed bar STRICTLY AFTER the
  decision timestamp (its close); no intra-bar optimism anywhere;
- settled funding is usable iff fundingTime < decision_utc and books
  only within ts_opened <= fundingTime < ts_closed (accounting.py);
- late or missing data raises :class:`DataBlocked` — never synthesize a
  price, never reuse an old rank, never silently skip.

Client: urllib, GET only, no keys, no signing, only the documented
public endpoints (allowlist enforced). Every fetch records
{url, fetched_at_utc, response_sha256} for data_snapshot_digest.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

BASE_URL = "https://fapi.binance.com"

#: Frozen endpoint allowlist (data_manifest.json measured endpoints).
ALLOWED_PATHS = (
    "/fapi/v1/klines",
    "/futures/data/basis",
    "/fapi/v1/fundingRate",
    "/fapi/v1/time",
    "/fapi/v1/exchangeInfo",
)

INTERVAL_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}

FetchFn = Callable[[str], bytes]


class DataBlocked(Exception):
    """Late/missing data: fail closed, never synthesize or skip silently.

    ``data_blocked = True`` lets the scheduler convert this into a
    DATA_BLOCKED event record.
    """

    data_blocked = True

    def __init__(self, reason: str, context: Optional[dict] = None):
        super().__init__(reason)
        self.reason = reason
        self.context = context or {}


@dataclass(frozen=True)
class FetchRecord:
    url: str
    fetched_at_utc: str
    response_sha256: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "url": self.url,
            "fetched_at_utc": self.fetched_at_utc,
            "response_sha256": self.response_sha256,
        }


@dataclass(frozen=True)
class Bar:
    symbol: str
    interval: str
    open_time_utc: str
    close_time_utc: str
    close_price: float
    quote_volume: float


@dataclass(frozen=True)
class BasisBucket:
    pair: str
    interval: str
    open_time_utc: str
    close_time_utc: str
    futures_price: float
    index_price: float
    basis: float
    basis_rate: float


@dataclass(frozen=True)
class FundingSettlement:
    symbol: str
    funding_time_utc: str
    funding_rate: float
    mark_price: Optional[float]


def to_iso_z(moment_ms: int) -> str:
    moment = dt.datetime.fromtimestamp(moment_ms / 1000.0, tz=dt.timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_z(text: str) -> dt.datetime:
    return dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=dt.timezone.utc
    )


def compose_data_snapshot_digest(fetch_records: List[FetchRecord]) -> str:
    """Deterministic digest over this event's fetch set."""
    canonical = "\n".join(
        sorted(f"{rec.url}|{rec.response_sha256}" for rec in fetch_records)
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class KeylessBinanceFuturesClient:
    """Keyless GET-only client over the frozen endpoint allowlist."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        fetch_fn: Optional[FetchFn] = None,
        now_fn: Optional[Callable[[], dt.datetime]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self._fetch_fn = fetch_fn if fetch_fn is not None else self._urllib_get
        self._now_fn = now_fn or (lambda: dt.datetime.now(dt.timezone.utc))
        self.last_fetch_records: List[FetchRecord] = []

    @staticmethod
    def _urllib_get(url: str) -> bytes:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            if response.status != 200:
                raise DataBlocked(f"endpoint returned HTTP {response.status}: {url}")
            return response.read()

    def build_url(self, path: str, params: Dict[str, Any]) -> str:
        if path not in ALLOWED_PATHS:
            raise DataBlocked(
                f"endpoint {path!r} not in frozen data-manifest allowlist"
            )
        query = urllib.parse.urlencode(
            {k: v for k, v in sorted(params.items()) if v is not None}
        )
        return f"{self.base_url}{path}?{query}"

    def get_json(self, path: str, params: Dict[str, Any]) -> Tuple[Any, FetchRecord]:
        url = self.build_url(path, params)
        try:
            raw = self._fetch_fn(url)
        except DataBlocked:
            raise
        except Exception as exc:  # noqa: BLE001 - any transport failure blocks
            raise DataBlocked(f"fetch failed for {url}: {exc}") from exc
        fetched_at = self._now_fn().strftime("%Y-%m-%dT%H:%M:%SZ")
        record = FetchRecord(
            url=url,
            fetched_at_utc=fetched_at,
            response_sha256=hashlib.sha256(raw).hexdigest(),
        )
        self.last_fetch_records.append(record)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise DataBlocked(f"unparseable response from {url}: {exc}") from exc
        return parsed, record

    # ------------------------------------------------------------------
    # klines
    # ------------------------------------------------------------------
    def get_completed_bars(
        self,
        symbol: str,
        interval: str,
        start_exclusive: str,
        end_inclusive: str,
        cutoff_utc: str,
    ) -> List[Bar]:
        """Only bars whose canonical close (open + interval) is
        <= cutoff_utc and <= end_inclusive, with open > start_exclusive."""
        if interval not in INTERVAL_MS:
            raise DataBlocked(f"unsupported interval {interval!r}")
        step = INTERVAL_MS[interval]
        start_ms = int(parse_iso_z(start_exclusive).timestamp() * 1000) + 1
        end_ms = int(parse_iso_z(end_inclusive).timestamp() * 1000)
        cutoff_ms = int(parse_iso_z(cutoff_utc).timestamp() * 1000)
        bars: List[Bar] = []
        cursor = start_ms
        while cursor <= end_ms:
            payload, _ = self.get_json(
                "/fapi/v1/klines",
                {
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": cursor,
                    "endTime": end_ms,
                    "limit": 1500,
                },
            )
            if not isinstance(payload, list) or not payload:
                break
            for row in payload:
                open_ms = int(row[0])
                close_ms = open_ms + step  # canonical boundary
                if open_ms > end_ms:
                    continue
                if close_ms > cutoff_ms or close_ms > end_ms:
                    continue  # not completed by the cutoff: excluded
                if open_ms < start_ms:
                    continue  # open must be strictly after start_exclusive
                bars.append(
                    Bar(
                        symbol=symbol,
                        interval=interval,
                        open_time_utc=to_iso_z(open_ms),
                        close_time_utc=to_iso_z(close_ms),
                        close_price=float(row[4]),
                        quote_volume=float(row[7]),
                    )
                )
            last_open = int(payload[-1][0])
            nxt = last_open + step
            if nxt <= cursor:  # no forward progress: stop paging
                break
            cursor = nxt
        return bars

    # ------------------------------------------------------------------
    # basis buckets
    # ------------------------------------------------------------------
    def get_basis_buckets(
        self,
        pair: str,
        start_exclusive: str,
        end_inclusive: str,
        cutoff_utc: str,
        period: str = "15m",
        contract_type: str = "PERPETUAL",
    ) -> List[BasisBucket]:
        if period not in INTERVAL_MS:
            raise DataBlocked(f"unsupported basis period {period!r}")
        step = INTERVAL_MS[period]
        start_ms = int(parse_iso_z(start_exclusive).timestamp() * 1000) + 1
        end_ms = int(parse_iso_z(end_inclusive).timestamp() * 1000)
        cutoff_ms = int(parse_iso_z(cutoff_utc).timestamp() * 1000)
        buckets: List[BasisBucket] = []
        cursor = start_ms
        while cursor <= end_ms:
            payload, _ = self.get_json(
                "/futures/data/basis",
                {
                    "pair": pair,
                    "contractType": contract_type,
                    "period": period,
                    "startTime": cursor,
                    "endTime": end_ms,
                    "limit": 500,
                },
            )
            if not isinstance(payload, list) or not payload:
                break
            for row in payload:
                open_ms = int(row["timestamp"])
                close_ms = open_ms + step
                if close_ms > cutoff_ms or close_ms > end_ms:
                    continue
                buckets.append(
                    BasisBucket(
                        pair=pair,
                        interval=period,
                        open_time_utc=to_iso_z(open_ms),
                        close_time_utc=to_iso_z(close_ms),
                        futures_price=float(row["futuresPrice"]),
                        index_price=float(row["indexPrice"]),
                        basis=float(row.get("basis", 0.0)),
                        basis_rate=float(row.get("basisRate", 0.0)),
                    )
                )
            last_open = int(payload[-1]["timestamp"])
            nxt = last_open + step
            if nxt <= cursor:  # no forward progress: stop paging
                break
            cursor = nxt
        return buckets

    # ------------------------------------------------------------------
    # settled funding
    # ------------------------------------------------------------------
    def get_settled_funding(
        self,
        symbol: str,
        start_exclusive: str,
        end_inclusive: str,
        cutoff_utc: str,
    ) -> List[FundingSettlement]:
        """Only settlements with fundingTime <= cutoff (and in window)."""
        start_ms = int(parse_iso_z(start_exclusive).timestamp() * 1000) + 1
        end_ms = int(parse_iso_z(end_inclusive).timestamp() * 1000)
        cutoff_ms = int(parse_iso_z(cutoff_utc).timestamp() * 1000)
        settlements: List[FundingSettlement] = []
        cursor = start_ms
        while cursor <= end_ms:
            payload, _ = self.get_json(
                "/fapi/v1/fundingRate",
                {
                    "symbol": symbol,
                    "startTime": cursor,
                    "endTime": end_ms,
                    "limit": 1000,
                },
            )
            if not isinstance(payload, list) or not payload:
                break
            for row in payload:
                ft_ms = int(row["fundingTime"])
                if ft_ms > cutoff_ms or ft_ms > end_ms:
                    continue
                mark = row.get("markPrice")
                settlements.append(
                    FundingSettlement(
                        symbol=symbol,
                        funding_time_utc=to_iso_z(ft_ms),
                        funding_rate=float(row["fundingRate"]),
                        mark_price=float(mark) if mark is not None else None,
                    )
                )
            last_ft = int(payload[-1]["fundingTime"])
            nxt = last_ft + 1
            if nxt <= cursor:  # no forward progress: stop paging
                break
            cursor = nxt
        return settlements


def require_complete_bars(
    bars: List[Bar],
    interval: str,
    start_exclusive: str,
    end_inclusive: str,
    min_count: Optional[int] = None,
) -> List[Bar]:
    """Fail closed when the completed-bar window has gaps or is short."""
    if interval not in INTERVAL_MS:
        raise DataBlocked(f"unsupported interval {interval!r}")
    step_ms = INTERVAL_MS[interval]
    start_ms = int(parse_iso_z(start_exclusive).timestamp() * 1000)
    end_ms = int(parse_iso_z(end_inclusive).timestamp() * 1000)
    by_open = {int(parse_iso_z(b.open_time_utc).timestamp() * 1000): b for b in bars}
    missing: List[str] = []
    # expected opens: interval grid strictly after start_exclusive
    cursor = ((start_ms // step_ms) + 1) * step_ms
    while cursor <= end_ms:
        if cursor not in by_open:
            missing.append(to_iso_z(cursor))
        cursor += step_ms
    if missing:
        raise DataBlocked(
            f"missing {len(missing)} completed bar(s) in ({start_exclusive}, "
            f"{end_inclusive}]; first gap at {missing[0]}",
            {"missing": missing[:10]},
        )
    ordered = [by_open[c] for c in sorted(by_open) if start_ms < c <= end_ms]
    if min_count is not None and len(ordered) < min_count:
        raise DataBlocked(
            f"only {len(ordered)} completed bars available, {min_count} required"
        )
    return ordered


def feature_eligible_bucket(open_time_utc: str, interval: str, decision_utc: str) -> bool:
    """Frozen feature rule: open + interval < decision (strictly before)."""
    step_ms = INTERVAL_MS[interval]
    open_ms = int(parse_iso_z(open_time_utc).timestamp() * 1000)
    decision_ms = int(parse_iso_z(decision_utc).timestamp() * 1000)
    return open_ms + step_ms < decision_ms


def select_fill_bar(bars: List[Bar], decision_utc: str) -> Bar:
    """First completed bar STRICTLY AFTER the decision (close > decision).

    This bar's close is the fill reference; mutating any bar whose close
    is at or before the decision cannot change the selection.
    """
    decision_ms = int(parse_iso_z(decision_utc).timestamp() * 1000)
    best: Optional[Bar] = None
    best_ms: Optional[int] = None
    for bar in bars:
        close_ms = int(parse_iso_z(bar.close_time_utc).timestamp() * 1000)
        if close_ms <= decision_ms:
            continue
        if best_ms is None or close_ms < best_ms:
            best, best_ms = bar, close_ms
    if best is None:
        raise DataBlocked(
            f"no completed bar strictly after decision {decision_utc}"
        )
    return best
