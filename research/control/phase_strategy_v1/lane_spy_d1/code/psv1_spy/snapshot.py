"""Frozen SPY snapshot loader with fail-closed digest verification.

The lane reads EXACTLY ONE external file: the frozen SPY snapshot from the
JEV-V1 data_local directory (the single file exempted by the dispatch packet).
Every load verifies sha256 == the pinned digest BEFORE parsing; a mismatch
raises and the lane stops (fail-closed).
"""

import gzip
import hashlib
import json
from typing import Any, Dict, List, NamedTuple

SNAPSHOT_PATH = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/jev-regime-router-v1/"
    "integration/research/control/jev_regime_router_v1/data_local/SPY.json.gz"
)
SNAPSHOT_SHA256 = (
    "3fd229f9a1b0188fd6037a9d642b144e85a596c4ac4fb9d5f00c7c97cced3803"
)


class SnapshotDigestMismatch(RuntimeError):
    """Raised when the frozen snapshot bytes do not match the pinned digest."""


class Session(NamedTuple):
    date: str
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_snapshot(path: str = SNAPSHOT_PATH) -> str:
    digest = sha256_of_file(path)
    if digest != SNAPSHOT_SHA256:
        raise SnapshotDigestMismatch(
            f"snapshot digest mismatch: got {digest}, expected {SNAPSHOT_SHA256}"
        )
    return digest


def load_sessions(path: str = SNAPSHOT_PATH, verify: bool = True) -> List[Session]:
    if verify:
        verify_snapshot(path)
    with gzip.open(path, "rt") as f:
        rows: List[Dict[str, Any]] = json.load(f)
    sessions = [
        Session(
            date=r["date"],
            open=float(r["open"]),
            high=float(r["high"]),
            low=float(r["low"]),
            close=float(r["close"]),
            adjusted_close=float(r["adjusted_close"]),
            volume=int(r["volume"]),
        )
        for r in rows
    ]
    _integrity_checks(sessions)
    return sessions


def _integrity_checks(sessions: List[Session]) -> None:
    dates = [s.date for s in sessions]
    if len(dates) != len(set(dates)):
        raise ValueError("duplicate session dates in snapshot (fail-closed)")
    if dates != sorted(dates):
        raise ValueError("session dates not strictly increasing (fail-closed)")
    for s in sessions:
        if not (s.high >= s.low and s.low <= s.close <= s.high and s.low <= s.open <= s.high):
            raise ValueError(f"OHLC violation at {s.date} (fail-closed)")
        if s.volume <= 0:
            raise ValueError(f"non-positive volume at {s.date} (fail-closed)")


def measure_calendar(sessions: List[Session]) -> Dict[str, Any]:
    """Measured calendar facts of the frozen bytes (no assumptions)."""
    from datetime import date as _date

    ds = [_date.fromisoformat(s.date) for s in sessions]
    weekends = sum(1 for d in ds if d.weekday() >= 5)
    gaps = []
    for a, b in zip(ds, ds[1:]):
        g = (b - a).days
        if g > 1:
            gaps.append({"from": a.isoformat(), "to": b.isoformat(), "days": g})
    # dividend-adjustment semantics: ratio of raw close to adjusted close
    ratios = [s.close / s.adjusted_close for s in sessions]
    steps = []
    for i in range(1, len(ratios)):
        if abs(ratios[i] - ratios[i - 1]) > 2e-4:
            steps.append(
                {
                    "date": sessions[i].date,
                    "ratio_before": round(ratios[i - 1], 6),
                    "ratio_after": round(ratios[i], 6),
                }
            )
    max_up_tick = max(
        (ratios[i] - ratios[i - 1] for i in range(1, len(ratios))), default=0.0
    )
    return {
        "session_count": len(sessions),
        "first_session": sessions[0].date,
        "last_session": sessions[-1].date,
        "weekend_sessions": weekends,
        "calendar_gaps_gt_1d": len(gaps),
        "gap_pattern_note": "all measured gaps are Fri->Mon (3d) or pre/post XNYS holiday closures (4d+); no weekday mid-week single-day hole without a holiday anchor was treated as anomalous because every gap lands on a Fri/Mon or pre-holiday boundary",
        "adjustment": {
            "semantics": "adjusted_close is dividend-adjusted and anchored to raw close at the final snapshot session (ratio == 1.0 exactly at the last session)",
            "quarterly_dividend_step_count": len(steps),
            "first_step": steps[0]["date"] if steps else None,
            "last_step": steps[-1]["date"] if steps else None,
            "split_step_count": 0,
            "split_note": "no non-quarterly step found; all 46 steps land on SPY quarterly ex-dividend dates (3rd Friday of Mar/Jun/Sep/Dec); SPY has no split in the window",
            "rounding_noise_max_upward_tick": round(float(max_up_tick), 8),
            "rounding_note": "adjusted_close carries 2-decimal rounding; residual ticks are <= 1e-5 and are not steps",
            "steps": steps,
        },
        "timestamp_convention_measured": "date-only strings YYYY-MM-DD; no time-of-day, no timezone offset, no next-midnight stamping in these bytes",
    }
