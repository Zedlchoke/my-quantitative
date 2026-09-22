"""Circuit breaker + response classification law (plan §5).

Surfaces are independent (REST vs WS). Per-surface states are exactly
the seven owner-verbatim values:

    HEALTHY DEGRADED RATE_LIMITED DISCONNECTED STALE GAP_DETECTED
    RECOVERING

Response classification (total, any status):
  (a) ANY response carrying Retry-After (any class, incl. 5xx/403)
      suppresses retries to that surface until expiry;
  (b) 418/429 opens the RATE_LIMITED breaker (Retry-After header AND
      body "banned until <ms>" parsed, longer wins, default 120 s);
  (c) 5xx without Retry-After: bounded retry budget elsewhere; 3
      consecutive 5xx => DEGRADED;
  (d) non-retryable 4xx (403/451/404/400...): fail fast, distinct
      non_retryable_status event, zero retry consumption, DEGRADED.

While a breaker is OPEN: zero retries to that surface; every
suppressed attempt is counted; exactly ONE half-open probe fires when
the window expires; probe success => RECOVERING -> HEALTHY, failure =>
OPEN again with a doubled window (cap 15 min). Error history is
append-only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from .timeutils import NowMs, default_now_ms, parse_http_date_ms

SURFACE_REST = "binance_fapi_rest"
SURFACE_WS = "binance_fapi_ws"

SURFACE_STATES = (
    "HEALTHY",
    "DEGRADED",
    "RATE_LIMITED",
    "DISCONNECTED",
    "STALE",
    "GAP_DETECTED",
    "RECOVERING",
)

OPEN_DEFAULT_MS = 120_000
OPEN_MAX_MS = 900_000  # 15 min cap after doubling
CONSECUTIVE_5XX_FOR_DEGRADED = 3
PROBE_GRACE_MS = 30_000  # half-open probe must conclude within this

BANNED_UNTIL_RE = re.compile(r"banned until (\d{9,14})")


class ResponseVerdict:
    """Classification outcome for one upstream HTTP response."""

    __slots__ = (
        "status",
        "retry_after_ms_expiry",
        "opens_breaker",
        "retryable",
        "non_retryable",
        "kind",
    )

    def __init__(
        self,
        status: int,
        retry_after_ms_expiry: Optional[int] = None,
        opens_breaker: bool = False,
        retryable: bool = False,
        non_retryable: bool = False,
        kind: str = "ok",
    ):
        self.status = status
        self.retry_after_ms_expiry = retry_after_ms_expiry
        self.opens_breaker = opens_breaker
        self.retryable = retryable
        self.non_retryable = non_retryable
        self.kind = kind


def parse_retry_after_ms(
    header_value: Optional[str], body: str, now_ms: int
) -> Optional[int]:
    """Absolute-ms expiry of the LONGER of header / banned-until body.

    Header may be delta-seconds or HTTP-date; body may carry
    ``banned until <ms epoch>`` (or seconds). Returns None when neither
    is present/parsable.
    """
    candidates: List[int] = []
    if header_value:
        text = header_value.strip()
        if text:
            if text.isdigit():
                candidates.append(now_ms + int(text) * 1000)
            else:
                as_date = parse_http_date_ms(text)
                if as_date is not None:
                    candidates.append(as_date)
    match = BANNED_UNTIL_RE.search(body or "")
    if match:
        raw = int(match.group(1))
        if raw > 10**12:  # ms epoch
            candidates.append(raw)
        else:  # s epoch
            candidates.append(raw * 1000)
    if not candidates:
        return None
    return max(candidates)


def classify_response(
    status: int,
    retry_after_header: Optional[str],
    body: str,
    now_ms: int,
) -> ResponseVerdict:
    """The total classification law (plan §5 response-classification)."""
    retry_after = parse_retry_after_ms(retry_after_header, body, now_ms)
    if status == 418 or status == 429:
        return ResponseVerdict(
            status,
            retry_after_ms_expiry=retry_after,
            opens_breaker=True,
            kind="rate_limited",
        )
    if 500 <= status <= 599:
        return ResponseVerdict(
            status,
            retry_after_ms_expiry=retry_after,
            retryable=retry_after is None,
            kind="server_error",
        )
    if 400 <= status <= 499:
        return ResponseVerdict(
            status,
            retry_after_ms_expiry=retry_after,
            non_retryable=True,
            kind="non_retryable_status",
        )
    return ResponseVerdict(status, kind="ok")


@dataclass
class BreakerRecord:
    """One breaker transition, kept forever (append-only history)."""

    at_utc: str
    from_state: str
    to_state: str
    reason: str
    http_status: Optional[int] = None
    retry_after_ms: Optional[int] = None
    allowed_retry_at_utc: Optional[str] = None
    triggering_url: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "at_utc": self.at_utc,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "reason": self.reason,
            "http_status": self.http_status,
            "retry_after_ms": self.retry_after_ms,
            "allowed_retry_at_utc": self.allowed_retry_at_utc,
            "triggering_url": self.triggering_url,
        }


@dataclass
class CircuitBreaker:
    """Per-surface breaker state machine (single half-open probe)."""

    surface: str
    now_ms: NowMs = field(default=default_now_ms)
    state: str = "HEALTHY"
    opened_at_ms: Optional[int] = None
    window_ms: int = OPEN_DEFAULT_MS
    suppressed: int = 0
    consecutive_5xx: int = 0
    last_record_utc: Optional[str] = None
    history: List[BreakerRecord] = field(default_factory=list)
    retry_suppressed_until_ms: Optional[int] = None  # law (a), any class
    _probe_inflight: bool = field(default=False, repr=False)

    # -- introspection -------------------------------------------------
    def allowed_retry_at_ms(self) -> Optional[int]:
        if self.state == "RATE_LIMITED" and self.opened_at_ms is not None:
            return self.opened_at_ms + self.window_ms
        return None

    def stats(self) -> dict:
        return {
            "surface": self.surface,
            "state": self.state,
            "opened_at_utc": (
                ms_iso(self.opened_at_ms) if self.opened_at_ms else None
            ),
            "allowed_retry_at_utc": (
                ms_iso(self.allowed_retry_at_ms())
                if self.allowed_retry_at_ms() is not None
                else None
            ),
            "window_ms": self.window_ms,
            "suppressed_during_open": self.suppressed,
            "consecutive_5xx": self.consecutive_5xx,
        }

    # -- transitions ----------------------------------------------------
    def _record(self, to_state: str, reason: str, **extra: Any) -> None:
        from_state = self.state
        self.state = to_state
        rec = BreakerRecord(
            at_utc=ms_iso(self.now_ms()),
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            **extra,
        )
        self.history.append(rec)
        self.last_record_utc = rec.at_utc

    def observe_response(
        self,
        status: int,
        retry_after_header: Optional[str],
        body: str,
        url: Optional[str] = None,
    ) -> ResponseVerdict:
        """Feed one response through the classification law."""
        now = self.now_ms()
        verdict = classify_response(status, retry_after_header, body, now)
        # law (a): Retry-After on ANY class suppresses retries until expiry
        if verdict.retry_after_ms_expiry is not None:
            prior = self.retry_suppressed_until_ms or 0
            self.retry_suppressed_until_ms = max(
                prior, verdict.retry_after_ms_expiry
            )
        if verdict.opens_breaker:
            self._probe_inflight = False  # probe concluded (failed)
            if self.state != "RATE_LIMITED":
                # window law (plan §5): Retry-After header AND
                # banned-until body parsed, longer wins; 120 s default
                # only when neither is present
                if verdict.retry_after_ms_expiry is not None:
                    self.window_ms = max(
                        1000, verdict.retry_after_ms_expiry - now
                    )
                else:
                    self.window_ms = OPEN_DEFAULT_MS
                self.opened_at_ms = now
                self.suppressed = 0
                self._record(
                    "RATE_LIMITED",
                    f"HTTP {status}",
                    http_status=status,
                    retry_after_ms=verdict.retry_after_ms_expiry,
                    allowed_retry_at_utc=(
                        ms_iso(self.allowed_retry_at_ms())
                        if self.allowed_retry_at_ms() is not None
                        else None
                    ),
                    triggering_url=url,
                )
            else:
                # already open (e.g. half-open probe got re-banned):
                # a FRESH Retry-After/banned-until wins over doubling
                # (A7 impl-r1 FND-3: the venue's own window is the law);
                # doubling (cap 15 min) applies only when the venue
                # gave no window
                if verdict.retry_after_ms_expiry is not None:
                    self.window_ms = max(
                        1000, verdict.retry_after_ms_expiry - now
                    )
                    reason_tail = "fresh venue window honored"
                else:
                    self.window_ms = min(self.window_ms * 2, OPEN_MAX_MS)
                    reason_tail = "window doubled"
                self.opened_at_ms = now
                self._record(
                    "RATE_LIMITED",
                    f"half-open probe re-banned HTTP {status}; {reason_tail}",
                    http_status=status,
                    retry_after_ms=verdict.retry_after_ms_expiry,
                    allowed_retry_at_utc=(
                        ms_iso(self.allowed_retry_at_ms())
                        if self.allowed_retry_at_ms() is not None
                        else None
                    ),
                    triggering_url=url,
                )
            return verdict
        if verdict.kind == "server_error":
            self.consecutive_5xx += 1
            if (
                self.consecutive_5xx >= CONSECUTIVE_5XX_FOR_DEGRADED
                and self.state not in ("RATE_LIMITED", "DISCONNECTED")
            ):
                self._record(
                    "DEGRADED",
                    f"{self.consecutive_5xx} consecutive 5xx",
                    http_status=status,
                )
            return verdict
        if verdict.kind == "non_retryable_status":
            # fail fast; no retry-budget consumption; surface DEGRADED
            if self.state not in ("RATE_LIMITED", "DISCONNECTED"):
                self._record(
                    "DEGRADED",
                    f"non-retryable HTTP {status}",
                    http_status=status,
                    triggering_url=url,
                )
            return verdict
        # success path
        self.observe_success()
        return verdict

    def observe_success(self) -> None:
        self.consecutive_5xx = 0
        self._probe_inflight = False
        if self.state == "RATE_LIMITED":
            # the half-open probe succeeded
            self._record("RECOVERING", "half-open probe success")
            self.state = "HEALTHY"
            self.history[-1].to_state = "HEALTHY"
        elif self.state in (
            "DEGRADED", "RECOVERING", "DISCONNECTED", "GAP_DETECTED",
        ):
            self._record("HEALTHY", "success after degraded state")

    def note_ws_state(self, connected: bool, reason: str) -> None:
        """WS surface connection state (not HTTP-class driven)."""
        if connected and self.state in ("DISCONNECTED",):
            self._record("HEALTHY", reason)
        elif not connected and self.state != "DISCONNECTED":
            self._record("DISCONNECTED", reason)

    # -- gating ----------------------------------------------------------
    def gate(self, url: Optional[str] = None) -> Optional[dict]:
        """Return a suppression dict when a request must NOT be issued."""
        now = self.now_ms()
        if self.state == "RATE_LIMITED":
            until = self.allowed_retry_at_ms()
            # law (a) across surfaces: a venue Retry-After window seen on
            # ANY response wins if longer than the breaker window
            if self.retry_suppressed_until_ms is not None:
                until = max(until or 0, self.retry_suppressed_until_ms)
            if until is not None and now < until:
                self.suppressed += 1
                return {
                    "suppressed": True,
                    "reason": "circuit_open",
                    "allowed_retry_at_utc": ms_iso(until),
                    "suppressed_count": self.suppressed,
                    "url": url,
                }
            # window expired: allow exactly ONE probe (single-flight;
            # A7 impl-r1 FND-2: concurrent callers must not all pass).
            # A probe that dies without concluding (timeout path) is
            # unstuck after PROBE_GRACE_MS.
            if self._probe_inflight:
                if now < self._probe_deadline_ms:
                    self.suppressed += 1
                    return {
                        "suppressed": True,
                        "reason": "half_open_probe_inflight",
                        "suppressed_count": self.suppressed,
                        "url": url,
                    }
                self._probe_inflight = False  # grace expired: re-probe
            self._probe_inflight = True
            self._probe_deadline_ms = now + PROBE_GRACE_MS
            self._record(
                "RECOVERING", "window expired; single half-open probe allowed"
            )
            # state stays RATE_LIMITED while the probe is in flight:
            # re-arms on failure, observe_success() heals to HEALTHY
            self.state = "RATE_LIMITED"
            return None  # the probe goes out; everything else suppressed
        if self.retry_suppressed_until_ms is not None:
            if now < self.retry_suppressed_until_ms:
                return {
                    "suppressed": True,
                    "reason": "retry_after_window",
                    "allowed_retry_at_utc": ms_iso(
                        self.retry_suppressed_until_ms
                    ),
                    "url": url,
                }
            self.retry_suppressed_until_ms = None
        return None


def ms_iso(ms: Optional[int]) -> Optional[str]:
    if ms is None:
        return None
    from .timeutils import ms_to_iso_z

    return ms_to_iso_z(ms)
