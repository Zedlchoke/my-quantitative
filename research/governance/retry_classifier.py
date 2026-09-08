"""Retry classifier - SHV1 sec7.4 error taxonomy.

One exception signature must never loop indefinitely. The SAFE default for an
unrecognized failure is CODE_OR_SCHEMA_ERROR (no automatic retry) - an unknown
failure is never assumed transient (fail closed). Policies:

- RESOURCE_BUSY          queue without consuming a scientific attempt
- TRANSIENT_TRANSPORT    bounded backoff, frozen retry limit
- RATE_LIMITED           honor provider reset evidence / quota policy
- CODE_OR_SCHEMA_ERROR   no automatic retry (single execution)
- DATA_AUTHORITY_FAILURE terminal/blocking for the applicable gate
- HASH_OR_CONTRACT_DRIFT immediate hard stop
- OPERATOR_CANCELLED     clean resource release, recorded cancellation

Measured signal sources in this program: the V12 fromisoformat TypeError
(INC_V12_4 - deterministic code/schema), the V17 BrokenPipeError / stalled
socket (transient transport), heavy_lock.LockBusyError (resource busy),
sha256 mismatches (hash drift).
"""
from __future__ import annotations

import dataclasses

TRANSIENT_MAX_ATTEMPTS = 3          # frozen limit (execution attempts)
TRANSIENT_BACKOFF_SECONDS = (30.0, 60.0, 120.0)   # bounded exponential-ish backoff

RESOURCE_BUSY = "RESOURCE_BUSY"
TRANSIENT_TRANSPORT = "TRANSIENT_TRANSPORT"
RATE_LIMITED = "RATE_LIMITED"
CODE_OR_SCHEMA_ERROR = "CODE_OR_SCHEMA_ERROR"
DATA_AUTHORITY_FAILURE = "DATA_AUTHORITY_FAILURE"
HASH_OR_CONTRACT_DRIFT = "HASH_OR_CONTRACT_DRIFT"
OPERATOR_CANCELLED = "OPERATOR_CANCELLED"

ALL_CLASSES = (RESOURCE_BUSY, TRANSIENT_TRANSPORT, RATE_LIMITED,
               CODE_OR_SCHEMA_ERROR, DATA_AUTHORITY_FAILURE,
               HASH_OR_CONTRACT_DRIFT, OPERATOR_CANCELLED)

# exception types per class (matched by exact type walk up the MRO)
_EXCEPTION_MAP = {
    RESOURCE_BUSY: (),
    TRANSIENT_TRANSPORT: ("ConnectionError", "TimeoutError", "InterruptedError", "socket.timeout"),
    RATE_LIMITED: (),
    CODE_OR_SCHEMA_ERROR: ("TypeError", "ValueError", "KeyError", "AttributeError",
                            "IndexError", "json.JSONDecodeError", "UnicodeDecodeError"),
    DATA_AUTHORITY_FAILURE: (),
    HASH_OR_CONTRACT_DRIFT: (),
    OPERATOR_CANCELLED: ("KeyboardInterrupt",),
}

# message regexes -> class (first match wins; order is load-bearing)
_MESSAGE_RULES = (
    ("fromisoformat", CODE_OR_SCHEMA_ERROR),
    ("sha256 mismatch", HASH_OR_CONTRACT_DRIFT),
    ("hash drift", HASH_OR_CONTRACT_DRIFT),
    ("contract drift", HASH_OR_CONTRACT_DRIFT),
    ("rate limit", RATE_LIMITED),
    ("quota exceeded", RATE_LIMITED),
    ("http 429", RATE_LIMITED),
    ("lock busy", RESOURCE_BUSY),
    ("broken pipe", TRANSIENT_TRANSPORT),
    ("connection reset", TRANSIENT_TRANSPORT),
    ("timed out", TRANSIENT_TRANSPORT),
    ("timeout", TRANSIENT_TRANSPORT),
    ("stalled", TRANSIENT_TRANSPORT),
    ("temporary failure", TRANSIENT_TRANSPORT),
    ("unavailable", DATA_AUTHORITY_FAILURE),
    ("coverage insufficient", DATA_AUTHORITY_FAILURE),
    ("entitlement", DATA_AUTHORITY_FAILURE),
)


@dataclasses.dataclass
class Classification:
    kind: str
    detail: str
    retryable: bool
    consumes_attempt: bool          # RESOURCE_BUSY / RATE_LIMITED do NOT consume one
    max_attempts: int               # meaningful for TRANSIENT_TRANSPORT
    backoff_hint: tuple             # seconds schedule for TRANSIENT_TRANSPORT
    hard_stop: bool                 # HASH_OR_CONTRACT_DRIFT
    terminal: bool                  # DATA_AUTHORITY_FAILURE / CODE_OR_SCHEMA_ERROR
    retry_after: float = None       # RATE_LIMITED provider reset hint


def _policy(kind: str, detail: str, retry_after: float = None) -> Classification:
    return Classification(
        kind=kind, detail=detail,
        retryable=kind in (RESOURCE_BUSY, TRANSIENT_TRANSPORT, RATE_LIMITED),
        consumes_attempt=kind in (TRANSIENT_TRANSPORT,),
        max_attempts=TRANSIENT_MAX_ATTEMPTS if kind == TRANSIENT_TRANSPORT else 1,
        backoff_hint=TRANSIENT_BACKOFF_SECONDS if kind == TRANSIENT_TRANSPORT else (),
        hard_stop=kind == HASH_OR_CONTRACT_DRIFT,
        terminal=kind in (CODE_OR_SCHEMA_ERROR, DATA_AUTHORITY_FAILURE),
        retry_after=retry_after,
    )


def classify_exception(exc: BaseException) -> Classification:
    name = type(exc).__name__
    msg = str(exc)
    lower = msg.lower()
    for needle, kind in _MESSAGE_RULES:
        if needle in lower:
            retry_after = None
            if kind == RATE_LIMITED:
                retry_after = getattr(exc, "retry_after", None)
            return _policy(kind, f"{name}: {msg[:200]}", retry_after=retry_after)
    # exception-type walk (module-qualified names in _EXCEPTION_MAP)
    for klass in type(exc).__mro__:
        qualname = f"{klass.__module__}.{klass.__name__}"
        simple = klass.__name__
        for kind, names in _EXCEPTION_MAP.items():
            if simple in names or qualname in names:
                return _policy(kind, f"{name}: {msg[:200]}")
        if klass is Exception:
            break
    if name == "LockBusyError" or "lock" in lower and "busy" in lower:
        return _policy(RESOURCE_BUSY, f"{name}: {msg[:200]}")
    # fail closed: unknown failures get NO automatic retry
    return _policy(CODE_OR_SCHEMA_ERROR, f"unclassified -> fail-closed no-retry ({name}: {msg[:200]})")
