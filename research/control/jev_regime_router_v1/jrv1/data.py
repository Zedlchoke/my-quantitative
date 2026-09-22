"""Data loaders for jrv1: BTCUSDT 15m exec bars + H1 regime bars, SPY daily.

BTCUSDT (clock law per data_identity_freeze):
- 15m LAST-EXTERNAL bars from the machine-local catalog (read-only). Prices
  are nautilus raw ints (little-endian int64 scaled 1e9).
- ts_event snap convention: bar close is stamped up to ~1ms BEFORE the clean
  15m boundary; normalized close = snapped UP to the next 15m boundary;
  open_ts = snapped_close - 15m; H1 bucket = floor(open_ts / 1h).
- An hour is COMPLETE iff exactly four bars with snapped closes at
  :00/:15/:30/:45 land in it (open minute offsets 0/15/30/45). OHLCV:
  open=first open, close=last close, high/low=extremes, volume=sum.
- Census (fail-closed) must equal the freeze: 8759 complete hours, 0 interior
  15m gaps, partial hours only at the two capture edges (1 bar @
  2025-08-20T02:00Z, 2 bars @ 2026-08-20T02:00Z).

SPY:
- EODHD EOD daily cache (gzip JSON list), read-only snapshot.
- The entire leg runs on the back-adjusted series: adjfactor =
  adjusted_close/close; adj_open = open*adjfactor; adj_high/adj_low likewise;
  adj_close = adjusted_close. One consistent vehicle (Q-14).
- Session timestamps: ts_open = midnight UTC of the session date;
  ts_close = midnight UTC of the next day (session completion). Decision at
  close t, fill at next session open; no synthetic bars over closures.

All reads go through the S1-denying safe_open. Missing files raise
DataBlocked (BLOCKED_DATA), never silent empty results.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
from dataclasses import dataclass

import numpy as np

from .freezes import Freezes, sha256_file
from .security import safe_open

NS = 1_000_000_000
MIN15 = 15 * 60 * NS
HOUR = 60 * 60 * NS
DAY = 24 * 60 * 60 * NS

# The observed catalog stamp offsets are <= 1ms before the clean boundary.
SNAP_TOLERANCE_NS = 1_000_000


class DataBlocked(RuntimeError):
    """BLOCKED_DATA: a loader input is absent or fails identity checks."""


class CensusViolation(RuntimeError):
    """The re-run data census disagrees with the data identity freeze."""


@dataclass
class Bars:
    """OHLCV bars as numpy arrays (ns UTC ints for timestamps, float64 prices)."""

    ts_open: np.ndarray
    ts_close: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray

    def __len__(self) -> int:  # pragma: no cover - trivial
        return int(self.ts_close.shape[0])


# --------------------------------------------------------------------------
# BTCUSDT
# --------------------------------------------------------------------------


def snap_close_ns(ts_event: np.ndarray) -> np.ndarray:
    """Snap ts_event closes UP to the next 15m boundary (offset <= 1ms)."""
    q, r = np.divmod(ts_event.astype(np.int64), MIN15)
    ok = (r == 0) | ((MIN15 - r) <= SNAP_TOLERANCE_NS)
    if not bool(ok.all()):
        bad = int((~ok).sum())
        raise CensusViolation(f"{bad} bars violate the <=1ms snap convention")
    return (q + (r != 0).astype(np.int64)) * MIN15


def read_btc_parquet(path) -> Bars:
    """Read the catalog 15m parquet into exec Bars (nautilus raw decode)."""
    import pyarrow.parquet as pq

    table = pq.read_table(str(path))
    needed = {"open", "high", "low", "close", "volume", "ts_event"}
    if not needed.issubset(set(table.column_names)):
        raise DataBlocked(f"parquet missing columns: {needed - set(table.column_names)}")

    def decode(col: str) -> np.ndarray:
        raw = table.column(col).to_pylist()
        return np.array([int.from_bytes(b, "little") / 1e9 for b in raw], dtype=np.float64)

    ts_event = np.array(table.column("ts_event").to_pylist(), dtype=np.int64)
    order = np.argsort(ts_event, kind="stable")
    ts_event = ts_event[order]
    snapped = snap_close_ns(ts_event)
    # exec bar open/close on the EXECUTION clock: open = snapped - 15m,
    # close = snapped (a 15m bar is filled at its snapped close).
    bars = Bars(
        ts_open=snapped - MIN15,
        ts_close=snapped,
        open=decode("open")[order],
        high=decode("high")[order],
        low=decode("low")[order],
        close=decode("close")[order],
        volume=decode("volume")[order],
    )
    bars._raw_ts_close = ts_event  # RAW stamped closes (pre-snap) for census
    return bars


def h1_resample(exec_bars: Bars, raw_ts_close: np.ndarray | None = None) -> tuple[Bars, dict]:
    """Deterministic H1 resample + census of the 15m exec grid.

    raw_ts_close: the RAW (pre-snap) stamped closes, used for the census
    first/last bar close fields exactly as the freeze recorded them.
    Returns (h1_bars_with_only_complete_hours, census_dict). Partial hours are
    INVALID for trading but are reported in the census with their bar counts
    and hour starts (fail-closed verification happens in census_check).
    """
    ts_open = exec_bars.ts_open
    ts_close = exec_bars.ts_close
    if len(ts_open) == 0:
        raise CensusViolation("empty exec grid")
    if not bool(np.all(np.diff(ts_close) == MIN15)):
        gaps = int(np.count_nonzero(np.diff(ts_close) != MIN15))
        raise CensusViolation(f"{gaps} interior 15m gaps (freeze says 0)")
    if not bool(np.all(np.diff(ts_close) > 0)):
        raise CensusViolation("snapped closes not strictly increasing")

    bucket = ts_open // HOUR
    offsets = ts_open - bucket * HOUR
    complete_mask = np.zeros(len(bucket), dtype=bool)
    partials: list[dict] = []
    uniq, start_idx, counts = np.unique(bucket, return_index=True, return_counts=True)
    complete_hours = 0
    for b, s, c in zip(uniq.tolist(), start_idx.tolist(), counts.tolist()):
        seg_off = offsets[s : s + c]
        is_complete = c == 4 and bool(
            np.array_equal(np.sort(seg_off), np.array([0, 900 * NS, 1800 * NS, 2700 * NS]))
        )
        if is_complete:
            complete_mask[s : s + c] = True
            complete_hours += 1
        else:
            partials.append({"hour_start": _iso_ns(int(b * HOUR)), "bars": int(c)})

    idx = np.flatnonzero(complete_mask)
    # group complete bars per hour (bucket order == chronological order)
    agg = {k: [] for k in ("ts_open", "ts_close", "open", "high", "low", "close", "volume")}
    b_sorted = bucket[idx]
    boundaries = np.flatnonzero(np.diff(b_sorted)) + 1
    groups = np.split(idx, boundaries)
    h1_ts_open, h1_ts_close, o, h, l, c, v = [], [], [], [], [], [], []
    for g in groups:
        gb = int(bucket[g[0]])
        h1_ts_open.append(gb * HOUR)
        h1_ts_close.append(gb * HOUR + HOUR)
        o.append(float(exec_bars.open[g[0]]))
        c.append(float(exec_bars.close[g[-1]]))
        h.append(float(np.max(exec_bars.high[g])))
        l.append(float(np.min(exec_bars.low[g])))
        v.append(float(np.sum(exec_bars.volume[g])))
    h1 = Bars(
        ts_open=np.array(h1_ts_open, dtype=np.int64),
        ts_close=np.array(h1_ts_close, dtype=np.int64),
        open=np.array(o, dtype=np.float64),
        high=np.array(h, dtype=np.float64),
        low=np.array(l, dtype=np.float64),
        close=np.array(c, dtype=np.float64),
        volume=np.array(v, dtype=np.float64),
    )
    census = {
        "rows": int(len(ts_open)),
        "first_bar_close_utc": _iso_ns(int((raw_ts_close if raw_ts_close is not None else ts_close)[0])),
        "last_bar_close_utc": _iso_ns(int((raw_ts_close if raw_ts_close is not None else ts_close)[-1])),
        "complete_hours": complete_hours,
        "gap_15m_interior": 0 if bool(np.all(np.diff(ts_close) == MIN15)) else 1,
        "partial_hours": partials,
    }
    if len(h1_ts_close):
        census["first_complete_close"] = _iso_ns(int(h1.ts_close[0]))
        census["last_complete_close"] = _iso_ns(int(h1.ts_close[-1]))
    return h1, census


def census_check(census: dict, freeze_entry: dict) -> dict:
    """Hard-fail unless the re-run census equals the data identity freeze."""
    f = freeze_entry["h1_census"]
    checks = []

    def ck(name, actual, expected):
        checks.append({"check": name, "actual": actual, "expected": expected, "ok": actual == expected})

    ck("rows", census["rows"], freeze_entry["rows"])
    ck("complete_hours", census["complete_hours"], f["complete_hours"])
    ck("gap_15m_interior", census["gap_15m_interior"], f["gap_15m_interior"])
    ck("first_complete_close", census.get("first_complete_close"), f["first_complete_close"])
    ck("last_complete_close", census.get("last_complete_close"), f["last_complete_close"])
    ck("first_bar_close_utc", census["first_bar_close_utc"], freeze_entry["first_bar_close_utc"])
    ck("last_bar_close_utc", census["last_bar_close_utc"], freeze_entry["last_bar_close_utc"])
    ck("partial_hours", census["partial_hours"], f["partial_hours"])
    failed = [c for c in checks if not c["ok"]]
    if failed:
        raise CensusViolation(f"census != freeze: {failed}")
    return {"ok": True, "checks": checks}


def load_btcusdt(fz: Freezes, verify_census: bool = True) -> tuple[Bars, Bars, dict]:
    """Load exec 15m bars + H1 regime bars; verify identity + census vs freeze."""
    entry = fz.data_identity["BTCUSDT"]
    path = entry["file"]
    try:
        digest = sha256_file(path)
    except (FileNotFoundError, OSError) as e:
        raise DataBlocked(f"BLOCKED_DATA: BTC parquet unreadable: {e}") from e
    if digest != entry["file_sha256"]:
        raise DataBlocked(
            f"BLOCKED_DATA: BTC parquet sha mismatch: {digest} != {entry['file_sha256']}"
        )
    exec_bars = read_btc_parquet(path)
    h1, census = h1_resample(exec_bars, raw_ts_close=exec_bars._raw_ts_close)
    if verify_census:
        census_check(census, entry)
    else:
        # even without the full census check, interior gaps remain fatal
        if census["gap_15m_interior"] != 0:
            raise CensusViolation("interior 15m gap")
    return exec_bars, h1, census


# --------------------------------------------------------------------------
# SPY
# --------------------------------------------------------------------------


def parse_spy_records(records: list[dict]) -> tuple[Bars, list[str]]:
    """Build the adjusted daily Bars from raw EOD records (hand-checkable)."""
    recs = sorted(records, key=lambda r: r["date"])
    dates = [r["date"] for r in recs]
    if len(set(dates)) != len(dates):
        raise DataBlocked("BLOCKED_DATA: duplicate SPY sessions")
    ts_open = [_date_to_ns(r["date"]) for r in recs]
    ts_close = [t + DAY for t in ts_open]
    adj = []
    for r in recs:
        px_close = float(r["close"])
        if px_close <= 0:
            raise DataBlocked("BLOCKED_DATA: non-positive SPY close")
        adj.append(float(r["adjusted_close"]) / px_close)
    adj = np.array(adj, dtype=np.float64)
    return Bars(
        ts_open=np.array(ts_open, dtype=np.int64),
        ts_close=np.array(ts_close, dtype=np.int64),
        open=np.array([float(r["open"]) for r in recs]) * adj,
        high=np.array([float(r["high"]) for r in recs]) * adj,
        low=np.array([float(r["low"]) for r in recs]) * adj,
        close=np.array([float(r["adjusted_close"]) for r in recs], dtype=np.float64),
        volume=np.array([float(r["volume"]) for r in recs], dtype=np.float64),
    ), dates


def load_spy_records(path) -> tuple[list[dict], str]:
    """Read the gzip JSON cache; return (records, sha256). Raises DataBlocked."""
    try:
        digest = sha256_file(path)
    except (FileNotFoundError, OSError) as e:
        raise DataBlocked(f"BLOCKED_DATA: SPY cache unreadable: {e}") from e
    p = str(path)
    try:
        with gzip.open(p, "rb") as f:
            records = json.loads(f.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise DataBlocked(f"BLOCKED_DATA: SPY cache unreadable: {e}") from e
    if not isinstance(records, list) or not records:
        raise DataBlocked("BLOCKED_DATA: SPY cache is not a non-empty JSON list")
    return records, digest


def load_spy(fz: Freezes) -> tuple[Bars, list[str], dict]:
    """Load the adjusted SPY daily series; verify identity vs freeze."""
    entry = fz.data_identity["SPY"]
    path = entry["file"]
    records, digest = load_spy_records(path)
    if digest != entry["file_sha256"]:
        raise DataBlocked(
            f"BLOCKED_DATA: SPY sha mismatch: {digest} != {entry['file_sha256']}"
        )
    bars, dates = parse_spy_records(records)
    checks = {
        "records": (len(records), entry["records"]),
        "first_session": (dates[0], entry["first_session"]),
        "last_session": (dates[-1], entry["last_session"]),
    }
    bad = {k: v for k, v in checks.items() if v[0] != v[1]}
    if bad:
        raise DataBlocked(f"BLOCKED_DATA: SPY identity mismatch vs freeze: {bad}")
    return bars, dates, {"ok": True, "checks": {k: v[0] for k, v in checks.items()}}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _date_to_ns(date_str: str) -> int:
    d = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp() * NS)


def _iso_ns(ts_ns: int) -> str:
    d = dt.datetime.fromtimestamp(ts_ns / NS, dt.timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")
