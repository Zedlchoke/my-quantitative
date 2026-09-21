"""Coalesced, cached, circuit-broken upstream REST fetcher (plan §5/§7).

``RestGate.fetch(path, params)`` is the ONLY path to upstream REST:
cache lookup -> coalescer -> breaker gate -> rate budget -> paced,
bounded-retry, timeout-guarded transport -> classification -> cache
store. Pagination helpers (klines/basis/funding) compose page fetches
and report canonical-grid completeness — the gateway serves RAW venue
rows; PIT filtering stays the consumer's law (zero decision-input
drift).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from .circuit import CircuitBreaker, SURFACE_REST
from .ratelimit import (
    MAX_TRANSPORT_RETRIES,
    CALL_TIMEOUT_S,
    RateLimiter,
    Coalescer,
    backoff_delay_ms,
)
from .reststore import RestCache
from .timeutils import NowMs, default_now_ms, ms_to_iso_z

TransportFn = Callable[
    [str, Dict[str, Any]], Awaitable[Tuple[int, Dict[str, str], bytes]]
]

def make_aiohttp_transport(session: Any) -> TransportFn:
    """Real upstream transport over one shared aiohttp ClientSession."""

    async def transport(url: str, params: Dict[str, Any]):
        async with session.get(url) as resp:
            body = await resp.read()
            headers = {str(k): str(v) for k, v in resp.headers.items()}
            return resp.status, headers, body

    return transport


ALLOWED_PATHS = (
    "/fapi/v1/klines",
    "/futures/data/basis",
    "/fapi/v1/fundingRate",
    "/fapi/v1/premiumIndex",
    "/fapi/v1/time",
    "/fapi/v1/exchangeInfo",
)

def _row_open(row: Any, key_field: str) -> int:
    """Venue rows are lists (klines: index 0) or dicts (basis:
    'timestamp', funding: 'fundingTime')."""
    if isinstance(row, list):
        return int(row[int(key_field)])
    return int(row[key_field])


PAGE_LIMITS = {
    "/fapi/v1/klines": 1500,
    "/futures/data/basis": 500,
    "/fapi/v1/fundingRate": 1000,
}


class GatewayFetchError(Exception):
    """Base; carries machine-readable context."""

    def __init__(self, kind: str, detail: dict):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


class CircuitOpenError(GatewayFetchError):
    pass


class BudgetBlockedError(GatewayFetchError):
    pass


class NonRetryableStatusError(GatewayFetchError):
    pass


class TransportExhaustedError(GatewayFetchError):
    pass


@dataclass
class RestGate:
    rest_base: str
    cache: RestCache
    breaker: CircuitBreaker
    limiter: RateLimiter
    coalescer: Coalescer = field(default_factory=Coalescer)
    transport: Optional[TransportFn] = None
    now_ms: NowMs = field(default=default_now_ms)
    sleeper: Callable[[float], Awaitable[None]] = field(
        default=lambda s: asyncio.sleep(s / 1000.0)
    )
    rng: Optional[Any] = None
    counts: Dict[str, int] = field(default_factory=lambda: {
        "upstream_calls": 0, "per_endpoint": {}
    })

    # ------------------------------------------------------------------
    def _url(self, path: str, params: Dict[str, Any]) -> str:
        query = urllib.parse.urlencode(
            {k: v for k, v in sorted(params.items()) if v is not None}
        )
        return f"{self.rest_base}{path}?{query}"

    async def fetch(
        self,
        path: str,
        params: Dict[str, Any],
        refresh: bool = False,
    ) -> dict:
        """One canonical request through the whole §5 law."""
        if path not in ALLOWED_PATHS:
            raise GatewayFetchError(
                "forbidden_path", {"path": path}
            )
        if not refresh:
            entry, hit = self.cache.lookup(path, params)
            if hit:
                return self._envelope(path, params, entry.payload, [entry], True)
        key, identity = self._canonical(path, params)
        try:
            return await self.coalescer.run(
                key, lambda: self._fetch_upstream(path, params, identity)
            )
        except CircuitOpenError:
            raise
        except BudgetBlockedError:
            raise
        except (NonRetryableStatusError, TransportExhaustedError):
            raise

    @staticmethod
    def _canonical(path: str, params: Dict[str, Any]) -> Tuple[str, str]:
        query = urllib.parse.urlencode(
            {k: v for k, v in sorted(params.items()) if v is not None}
        )
        identity = f"GET {path}?{query}"
        return hashlib.sha256(identity.encode()).hexdigest(), identity

    async def _fetch_upstream(
        self, path: str, params: Dict[str, Any], identity: str
    ) -> dict:
        url = self._url(path, params)
        last_error: Optional[BaseException] = None
        for attempt in range(1 + MAX_TRANSPORT_RETRIES):
            gate = self.breaker.gate(url)
            if gate is not None:
                raise CircuitOpenError("circuit_open", gate)
            block = self.limiter.budget_block(path)
            if block is not None:
                raise BudgetBlockedError("budget_blocked", {"reason": block, "url": url})
            gap = self.limiter.gap_wait_ms()
            if gap:
                await self.sleeper(gap)
            self.limiter.note_issued()
            self.counts["upstream_calls"] += 1
            per = self.counts["per_endpoint"].setdefault(path, 0)
            self.counts["per_endpoint"][path] = per + 1
            try:
                status, headers, body = await asyncio.wait_for(
                    self.transport(url, params), timeout=CALL_TIMEOUT_S
                )
            except asyncio.TimeoutError:
                last_error = asyncio.TimeoutError()
                await self.sleeper(backoff_delay_ms(attempt, self.rng))
                continue
            except (asyncio.CancelledError,):
                raise
            except Exception as exc:  # noqa: BLE001 - transport failure
                last_error = exc
                await self.sleeper(backoff_delay_ms(attempt, self.rng))
                continue
            weight = headers.get("X-MBX-USED-WEIGHT-1M") or headers.get(
                "x-mbx-used-weight-1m"
            )
            self.limiter.observe_weight_header(weight)
            body_text = body.decode("utf-8", "replace") if body else ""
            verdict = self.breaker.observe_response(
                status, headers.get("Retry-After") or headers.get("retry-after"),
                body_text, url,
            )
            if verdict.opens_breaker:
                raise CircuitOpenError(
                    "rate_limited",
                    {
                        "http_status": status,
                        "url": url,
                        "allowed_retry_at_utc": (
                            ms_to_iso_z(verdict.retry_after_ms_expiry)
                            if verdict.retry_after_ms_expiry
                            else None
                        ),
                        "breaker": self.breaker.stats(),
                    },
                )
            if verdict.kind == "ok":
                try:
                    payload = json.loads(body_text)
                except ValueError as exc:
                    # unparseable 200: treat as transport failure (retry)
                    last_error = exc
                    await self.sleeper(backoff_delay_ms(attempt, self.rng))
                    continue
                entry = self.cache.store(path, params, payload, complete=True)
                return self._envelope(path, params, payload, [entry], False)
            if verdict.retryable:
                last_error = GatewayFetchError(
                    "server_error", {"status": status, "url": url}
                )
                await self.sleeper(backoff_delay_ms(attempt, self.rng))
                continue
            # non-retryable 4xx or 5xx-with-RA: fail fast/closed
            raise NonRetryableStatusError(
                verdict.kind,
                {
                    "status": status,
                    "url": url,
                    "retry_after_utc": (
                        ms_to_iso_z(verdict.retry_after_ms_expiry)
                        if verdict.retry_after_ms_expiry
                        else None
                    ),
                },
            )
        raise TransportExhaustedError(
            "transport_exhausted",
            {"url": url, "attempts": 1 + MAX_TRANSPORT_RETRIES,
             "last_error": repr(last_error)},
        )

    def _envelope(
        self,
        path: str,
        params: Dict[str, Any],
        payload: Any,
        pages: List[Any],
        cache_hit: bool,
    ) -> dict:
        return {
            "provider": "binance_fapi",
            "endpoint": path,
            "params": params,
            "payload": payload,
            "cache_hit": cache_hit,
            "pages": [
                {
                    "identity": p.identity,
                    "fetched_at_utc": ms_to_iso_z(p.fetched_at_ms),
                    "response_sha256": p.response_sha256,
                }
                for p in pages
            ],
        }

    # ------------------------------------------------------------------
    # pagination (klines / basis / funding historical windows)
    # ------------------------------------------------------------------
    async def fetch_window(
        self,
        path: str,
        grid_ms: Optional[int],
        key_field: str,
        base_params: Dict[str, Any],
        start_ms: int,
        end_ms: int,
    ) -> dict:
        """Page through [start_ms, end_ms]; merge rows; completeness =
        every expected grid open present (klines/basis) or, for funding,
        rows ordered and within bounds (venue cadence varies)."""
        limit = PAGE_LIMITS.get(path)
        if limit is None:
            return await self.fetch(path, base_params)
        rows: List[Any] = []
        pages_meta: List[Any] = []
        cache_any = False
        cursor = start_ms
        while cursor < end_ms:  # a bar OPENING at end closes after end
            params = dict(base_params)
            params.update({"startTime": cursor, "endTime": end_ms, "limit": limit})
            envelope = await self.fetch(path, params)
            pages_meta.extend(envelope["pages"])
            cache_any = cache_any or envelope["cache_hit"]
            payload = envelope["payload"]
            if not isinstance(payload, list) or not payload:
                break
            rows.extend(payload)
            last_open = _row_open(payload[-1], key_field)
            nxt = last_open + (grid_ms or 1)
            if nxt <= cursor:
                break
            cursor = nxt
        in_window = [
            r for r in rows
            if start_ms <= _row_open(r, key_field) < end_ms
        ]
        rows_sorted = sorted(
            in_window, key=lambda r: _row_open(r, key_field)
        )
        gaps: List[str] = []
        complete = True
        if grid_ms:
            seen = {_row_open(r, key_field) for r in rows_sorted}
            # expected grid opens: first aligned open >= start, < end
            probe = ((start_ms + grid_ms - 1) // grid_ms) * grid_ms
            while probe < end_ms:
                if probe not in seen:
                    gaps.append(ms_to_iso_z(probe))
                probe += grid_ms
            complete = not gaps
        merged_digest = hashlib.sha256(
            json.dumps(rows_sorted, sort_keys=True).encode()
        ).hexdigest()
        return {
            "provider": "binance_fapi",
            "endpoint": path,
            "params": {**base_params, "start_ms": start_ms, "end_ms": end_ms},
            "rows": rows_sorted,
            "row_count": len(rows_sorted),
            "complete": complete,
            "gaps": gaps[:50],
            "cache_hit": cache_any,
            "pages": pages_meta,
            "merged_sha256": merged_digest,
        }

    def stats(self) -> dict:
        return {
            "upstream_calls": self.counts["upstream_calls"],
            "per_endpoint": dict(self.counts["per_endpoint"]),
            "rate_limiter": self.limiter.stats(),
            "breaker": self.breaker.stats(),
            "coalescer_suppressed": self.coalescer.suppressed_duplicates,
            "cache": self.cache.stats(),
        }
