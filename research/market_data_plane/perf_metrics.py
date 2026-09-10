"""Portable peak-RSS normalization (F4, lane A4).

Freeze authority: research/control/market_data_plane_v2_run/architecture_freeze_v2.json
(p3_wave_sha 09a223f6ce166e219beb67b25b8151361979ca21),
findings_and_negative_matrices.F4.schema_bump.

Problem being fixed (F4): ``resource.getrusage(...).ru_maxrss`` is
platform-dependent — DARWIN reports BYTES while LINUX reports KiB — and the
V1 bench recorded the raw value under a unit-bearing field name
(``peak_rss_kb``) that actually held darwin bytes.  V2 records the raw value
WITH its unit and the normalized byte/MiB derivations, so numbers are
portable across hosts.

Conversion (frozen):
* unit ``bytes`` (darwin)   -> ``peak_rss_bytes = peak_rss_raw``
* unit ``kib``   (linux)    -> ``peak_rss_bytes = peak_rss_raw * 1024``
* unit ``unknown`` (other)  -> ``peak_rss_bytes = None`` plus a visible
  UNMEASURABLE note (never a guess, never a silent zero)
* ``peak_rss_mib = peak_rss_bytes / 1048576`` (exact binary-float division;
  None when unmeasurable)

stdlib only.  Unit tests assert the conversions EXACTLY (see
tests/test_mdp_perf_portable.py); the heavy bench that consumes this module
(research/control/market_data_plane_v2_run/perf_bench_v2.py) is never run by
tests.
"""

from __future__ import annotations

import resource

__all__ = [
    "MIB",
    "normalize_rss",
    "peak_rss_now",
]

#: Bytes per MiB (frozen divisor of the F4 conversion rule).
MIB = 1048576

_UNITS = ("bytes", "kib", "unknown")


def _unit_for(platform: str) -> str:
    token = str(platform).lower()
    if "darwin" in token:
        return "bytes"
    if "linux" in token:
        return "kib"
    return "unknown"


def normalize_rss(platform: str, peak_rss_raw: int) -> dict:
    """Normalize one raw ``ru_maxrss`` value into portable F4 fields.

    Returns exactly::

        {"peak_rss_raw": int,          # verbatim input
         "peak_rss_raw_unit": "bytes" | "kib" | "unknown",
         "peak_rss_bytes": int | None, # None only when the unit is unknown
         "peak_rss_mib": float | None, # bytes / 1048576; None when unknown
         "note": str}                  # visible UNMEASURABLE note when unknown

    ``peak_rss_raw`` must be a non-negative plain int (bools and negatives
    raise ValueError — a negative RSS is never clamped into a fake number).
    """
    if isinstance(peak_rss_raw, bool) or not isinstance(peak_rss_raw, int):
        raise ValueError(
            f"peak_rss_raw must be a plain int, got {type(peak_rss_raw).__name__}")
    if peak_rss_raw < 0:
        raise ValueError(f"peak_rss_raw must be >= 0, got {peak_rss_raw}")
    unit = _unit_for(platform)
    if unit == "bytes":
        peak_rss_bytes: int | None = peak_rss_raw
        note = ""
    elif unit == "kib":
        peak_rss_bytes = peak_rss_raw * 1024
        note = ""
    else:
        peak_rss_bytes = None
        note = (
            f"UNMEASURABLE: ru_maxrss unit unknown for platform {platform!r}; "
            f"peak_rss_bytes/peak_rss_mib are None (F4: never guess, never "
            f"silently zero)")
    peak_rss_mib = (peak_rss_bytes / MIB) if peak_rss_bytes is not None else None
    return {
        "peak_rss_raw": peak_rss_raw,
        "peak_rss_raw_unit": unit,
        "peak_rss_bytes": peak_rss_bytes,
        "peak_rss_mib": peak_rss_mib,
        "note": note,
    }


def peak_rss_now(platform: str) -> dict:
    """Measure and normalize the process's current peak RSS (F4 fields)."""
    return normalize_rss(platform, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
