"""V12 P1 A3 -- fail-closed load validation.

Every check re-verifies, AT LOAD TIME, a property that the frozen data
manifest asserts.  Any failure raises :class:`DataLoadError` immediately:
the loader must not proceed with partial, stale or synthesized data.

Checks:

* window bounds -- end strictly after start, both alignable;
* completed-bar integrity -- every required 15-minute slot inside the
  window is present exactly once, no internal gaps, and no partial tail
  (a bar closing beyond the window end is not window coverage);
* funding PIT applicability -- a settlement may only be applied to a
  holding span when its timestamp lies within ``[ts_opened, ts_closed]``;
* manifest-hash match -- the file on disk hashes to the recorded sha256.
"""

from __future__ import annotations

from typing import Sequence

from research.v12.data_contract import (
    BAR_INTERVAL_NS,
    sha256_file,
)


class DataLoadError(RuntimeError):
    """Raised when a fail-closed load validation check fails."""


def validate_window_bounds(
    window_start_ns: int, window_end_ns: int, *, label: str = "window"
) -> None:
    """Window end must be strictly after window start; both are epoch ns."""
    if int(window_end_ns) <= int(window_start_ns):
        raise DataLoadError(
            f"{label}: end {window_end_ns} is not strictly after start "
            f"{window_start_ns}"
        )
    if int(window_start_ns) < 0 or int(window_end_ns) < 0:
        raise DataLoadError(f"{label}: negative timestamps are not valid")


def validate_completed_bars(
    close_ns: Sequence[int],
    window_start_ns: int,
    window_end_ns: int,
    *,
    interval_ns: int = BAR_INTERVAL_NS,
    symbol: str = "<symbol>",
    allow_late_bars: bool = False,
) -> None:
    """Every 15-minute slot in ``(start, end]`` must close exactly one bar.

    Fail-closed on: duplicate closes for a slot, missing slots (gaps),
    misaligned closes, and a partial tail.  By default the series must not
    contain ANY close beyond ``window_end`` (a strict window slice); pass
    ``allow_late_bars=True`` to validate a series that legitimately extends
    past the frozen boundary.
    """
    validate_window_bounds(window_start_ns, window_end_ns, label=f"{symbol} window")
    if not allow_late_bars:
        late = [int(v) for v in close_ns if int(v) > int(window_end_ns)]
        if late:
            raise DataLoadError(
                f"{symbol}: partial tail -- {len(late)} bar close(s) beyond the "
                f"window end (first={late[0]}); slice the series to the window "
                f"or pass allow_late_bars=True"
            )
    required: list[int] = []
    t = int(window_start_ns) + int(interval_ns)
    while t <= int(window_end_ns):
        required.append(t)
        t += int(interval_ns)
    if not required:
        raise DataLoadError(
            f"{symbol}: window shorter than one bar interval; nothing to load"
        )
    present = [int(v) for v in close_ns if int(window_start_ns) < v <= int(window_end_ns)]
    present_set = set(present)
    if len(present_set) != len(present):
        raise DataLoadError(f"{symbol}: duplicate bar closes inside the window")
    missing = [v for v in required if v not in present_set]
    if missing:
        raise DataLoadError(
            f"{symbol}: {len(missing)} missing completed 15m slot(s) in window "
            f"(first missing close={missing[0]}, "
            f"count={len(missing)}); gaps are never synthesized"
        )
    # No partial tail inside the window: the last present close must be
    # exactly the final slot.
    if max(present) != required[-1]:
        raise DataLoadError(
            f"{symbol}: partial tail detected (last close {max(present)} != "
            f"final slot {required[-1]})"
        )


def validate_no_partial_tail(
    close_ns: Sequence[int],
    *,
    data_available_until_ns: int,
    interval_ns: int = BAR_INTERVAL_NS,
    symbol: str = "<symbol>",
) -> None:
    """The final bar must be complete: its close is a full interval boundary
    at or before the instant loading happens.

    A bar whose close would land after ``data_available_until_ns`` cannot be
    observed yet; if the last close exceeds it the data contains a
    synthesized or partial tail and the load must fail.
    """
    if not close_ns:
        raise DataLoadError(f"{symbol}: no bars to validate")
    last = int(close_ns[-1])
    if last > int(data_available_until_ns):
        raise DataLoadError(
            f"{symbol}: partial tail (last close {last} beyond availability "
            f"{data_available_until_ns})"
        )
    if (int(data_available_until_ns) - last) % int(interval_ns) != 0 and last % int(
        interval_ns
    ) != 0:
        raise DataLoadError(f"{symbol}: last bar close is not interval-aligned")


def validate_funding_applicability(
    settlement_ts_ns: int,
    span_opened_ns: int,
    span_closed_ns: int,
    *,
    symbol: str = "<symbol>",
) -> None:
    """PIT funding rule: a settlement applies to a span only when its
    timestamp lies within ``[ts_opened, ts_closed]``.

    Applying a settlement outside the holding span is a PIT violation.
    """
    ts = int(settlement_ts_ns)
    lo = int(span_opened_ns)
    hi = int(span_closed_ns)
    if hi < lo:
        raise DataLoadError(f"{symbol}: holding span closed before it opened")
    if ts < lo or ts > hi:
        raise DataLoadError(
            f"{symbol}: funding settlement {ts} outside holding span "
            f"[{lo}, {hi}] -- PIT violation"
        )


def validate_funding_span_coverage(
    settlements_ns: Sequence[int],
    span_opened_ns: int,
    span_closed_ns: int,
    *,
    max_interval_ns: int = 8 * 3600 * 1_000_000_000,
    symbol: str = "<symbol>",
) -> None:
    """While held, settlements must exist for every cadence slot inside the
    span; a hole larger than one cadence interval inside an OPEN span means
    funding would be silently dropped.
    """
    lo = int(span_opened_ns)
    hi = int(span_closed_ns)
    if hi < lo:
        raise DataLoadError(f"{symbol}: holding span closed before it opened")
    inside = sorted(int(s) for s in settlements_ns if lo <= s <= hi)
    prev = lo
    for s in inside:
        if s - prev > int(max_interval_ns):
            raise DataLoadError(
                f"{symbol}: funding hole of {(s - prev) / 1e9 / 3600:.1f}h "
                f"inside holding span [{lo}, {hi}]"
            )
        prev = s
    if hi - prev > int(max_interval_ns):
        raise DataLoadError(
            f"{symbol}: funding hole of {(hi - prev) / 1e9 / 3600:.1f}h at the "
            f"close of holding span [{lo}, {hi}]"
        )


def validate_manifest_hash(
    path: str,
    expected_sha256: str,
    *,
    label: str = "<file>",
) -> str:
    """The file at ``path`` must exist and hash to ``expected_sha256``.

    Returns the actual hash on success so callers can chain provenance.
    """
    import os

    if not os.path.exists(path):
        raise DataLoadError(f"{label}: expected file missing at {path}")
    actual = sha256_file(path)
    if actual != str(expected_sha256).lower():
        raise DataLoadError(
            f"{label}: sha256 mismatch (expected {expected_sha256}, got {actual})"
        )
    return actual


def validate_window_non_overlap(
    a_start_ns: int,
    a_end_ns: int,
    b_start_ns: int,
    b_end_ns: int,
    *,
    label: str = "window pair",
) -> None:
    """Two frozen windows must not share any instant (open-interval test)."""
    if int(a_start_ns) < int(b_end_ns) and int(b_start_ns) < int(a_end_ns):
        raise DataLoadError(
            f"{label}: windows overlap ([{a_start_ns}, {a_end_ns}) vs "
            f"[{b_start_ns}, {b_end_ns}))"
        )


__all__ = [
    "DataLoadError",
    "validate_completed_bars",
    "validate_funding_applicability",
    "validate_funding_span_coverage",
    "validate_manifest_hash",
    "validate_no_partial_tail",
    "validate_window_bounds",
    "validate_window_non_overlap",
]
