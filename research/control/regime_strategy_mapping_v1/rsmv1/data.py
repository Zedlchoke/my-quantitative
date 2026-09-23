"""Data loaders for jrv2: BTCUSDT 15m exec bars + H1/H4 regime bars, SPY daily.

BTCUSDT (clock law per data_identity_freeze, identical to V1):
- 15m LAST-EXTERNAL bars from the machine-local catalog (read-only). Prices
  are nautilus raw ints (little-endian int64 scaled 1e9).
- ts_event snap convention: bar close is stamped up to ~1ms BEFORE the clean
  15m boundary; normalized close = snapped UP to the next 15m boundary;
  open_ts = snapped_close - 15m; H1 bucket = floor(open_ts / 1h);
  H4 bucket = floor(open_ts / 4h) (UTC 00/04/08/12/16/20).
- An hour is COMPLETE iff exactly four bars with snapped closes at
  :00/:15/:30/:45 land in it. An H4 bucket is COMPLETE iff exactly SIXTEEN
  aligned 15m bars (offsets 0..15 x 15m) land in it. OHLCV: open=first open,
  close=last close, high/low=extremes, volume=sum.
- Census (fail-closed) must equal the v2 freeze:
  H1 8759 complete / 0 interior gaps / partial 1 bar @2025-08-20T02:00Z and
  2 bars @2026-08-20T02:00Z;
  H4 2189 complete / 0 interior gaps / partial 5 bars @2025-08-20T00:00Z and
  10 bars @2026-08-20T00:00Z.

SPY:
- EODHD EOD daily cache (gzip JSON list) — the V2 data_local COPY of the V1
  frozen snapshot (SAME bytes, sha-verified against the v2 freeze; no re-pull,
  disclosed snapshot semantics SPY-SHA-MISMATCH-DISCLOSED). v2 code NEVER
  opens the V1 worktree path (the isolation guard refuses it); the freeze's
  SPY.file field is lineage disclosure only, not a runtime path.
- The entire leg runs on the back-adjusted series (adjfactor =
  adjusted_close/close). ts_open = midnight UTC of the session date;
  ts_close = midnight UTC of the next day. Decision at close t, fill at next
  session open; no synthetic bars over closures.

All reads go through the S1-denying, V1-isolating safe_open. Missing files
raise DataBlocked (BLOCKED_DATA), never silent empty results.
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
H4 = 4 * HOUR
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


def _bucket_resample(
    exec_bars: Bars,
    span_bars: int,
    span_ns: int,
    label: str,
) -> tuple[Bars, dict]:
    """Deterministic bucket resample of the 15m exec grid (span_bars per bucket).

    A bucket is COMPLETE iff exactly span_bars bars land in it AND their open
    offsets are exactly 0..span_bars-1 multiples of 15m (aligned). Returns
    (bars_with_only_complete_buckets, census_dict). Partial buckets are
    INVALID for regime decisions but reported in the census.
    """
    ts_open = exec_bars.ts_open
    ts_close = exec_bars.ts_close
    if len(ts_open) == 0:
        raise CensusViolation("empty exec grid")
    gaps = int(np.count_nonzero(np.diff(ts_close) != MIN15))
    if gaps:
        raise CensusViolation(f"{gaps} interior 15m gaps (freeze says 0)")
    if not bool(np.all(np.diff(ts_close) > 0)):
        raise CensusViolation("snapped closes not strictly increasing")

    bucket = ts_open // span_ns
    offsets = ts_open - bucket * span_ns
    aligned = np.arange(span_bars, dtype=offsets.dtype) * MIN15
    complete_mask = np.zeros(len(bucket), dtype=bool)
    partials: list[dict] = []
    complete_buckets = 0
    uniq, start_idx, counts = np.unique(bucket, return_index=True, return_counts=True)
    for b, s, c in zip(uniq.tolist(), start_idx.tolist(), counts.tolist()):
        seg_off = offsets[s : s + c]
        is_complete = c == span_bars and bool(np.array_equal(np.sort(seg_off), aligned))
        if is_complete:
            complete_mask[s : s + c] = True
            complete_buckets += 1
        else:
            partials.append(
                {"bucket_start": _iso_ns(int(b * span_ns)), "bars": int(c)}
            )

    idx = np.flatnonzero(complete_mask)
    agg = {k: [] for k in ("ts_open", "ts_close", "open", "high", "low", "close", "volume")}
    b_sorted = bucket[idx]
    boundaries = np.flatnonzero(np.diff(b_sorted)) + 1
    groups = np.split(idx, boundaries)
    for g in groups:
        gb = int(bucket[g[0]])
        agg["ts_open"].append(gb * span_ns)
        agg["ts_close"].append(gb * span_ns + span_ns)
        agg["open"].append(float(exec_bars.open[g[0]]))
        agg["close"].append(float(exec_bars.close[g[-1]]))
        agg["high"].append(float(np.max(exec_bars.high[g])))
        agg["low"].append(float(np.min(exec_bars.low[g])))
        agg["volume"].append(float(np.sum(exec_bars.volume[g])))
    bars = Bars(
        ts_open=np.array(agg["ts_open"], dtype=np.int64),
        ts_close=np.array(agg["ts_close"], dtype=np.int64),
        open=np.array(agg["open"], dtype=np.float64),
        high=np.array(agg["high"], dtype=np.float64),
        low=np.array(agg["low"], dtype=np.float64),
        close=np.array(agg["close"], dtype=np.float64),
        volume=np.array(agg["volume"], dtype=np.float64),
    )
    partial_bars = int(sum(p["bars"] for p in partials))
    census = {
        "complete": complete_buckets,
        "partial": partials,
        "align_ok": True,
        # builder formula: all rows must be accounted for by complete buckets
        # plus partial buckets (0 = no unaccounted bars)
        "interior_gaps": int(complete_buckets * span_bars + partial_bars - len(ts_open)),
        "first_complete_close": _iso_ns(int(bars.ts_close[0])) if len(bars.ts_close) else None,
        "last_complete_close": _iso_ns(int(bars.ts_close[-1])) if len(bars.ts_close) else None,
    }
    return bars, census


def h1_resample(exec_bars: Bars, raw_ts_close: np.ndarray | None = None) -> tuple[Bars, dict]:
    """H1 resample (4 aligned 15m bars per hour) — identical law to V1."""
    bars, census = _bucket_resample(exec_bars, 4, HOUR, "h1")
    if raw_ts_close is not None:
        census["first_bar_close_utc"] = _iso_ns(int(raw_ts_close[0]))
        census["last_bar_close_utc"] = _iso_ns(int(raw_ts_close[-1]))
    return bars, census


def h4_resample(exec_bars: Bars) -> tuple[Bars, dict]:
    """H4 resample: bucket = floor(open/4h)*4h (UTC 00/04/08/12/16/20).

    Complete iff exactly 16 aligned 15m bars (freeze law verbatim). An
    independent cell: own regime clock, own folds, own trial accounting.
    """
    return _bucket_resample(exec_bars, 16, H4, "h4")


def census_check(census: dict, h1_freeze: dict, h4_freeze: dict) -> dict:
    """Hard-fail unless the re-run census equals the data identity freeze."""
    checks: list[dict] = []

    def ck(name, actual, expected):
        checks.append({"check": name, "actual": actual, "expected": expected, "ok": actual == expected})

    for key, f in (("h1", h1_freeze), ("h4", h4_freeze)):
        ck(f"{key}.complete", census[key]["complete"], f["complete"])
        ck(f"{key}.align_ok", census[key]["align_ok"], f["align_ok"])
        ck(f"{key}.interior_gaps", census[key]["interior_gaps"], f["interior_gaps"])
        ck(f"{key}.partial", census[key]["partial"], f["partial"])
    failed = [c for c in checks if not c["ok"]]
    if failed:
        raise CensusViolation(f"census != freeze: {failed}")
    return {"ok": True, "checks": checks}


def load_btcusdt(fz: Freezes, verify_census: bool = True) -> tuple[Bars, Bars, Bars, dict]:
    """Load exec 15m bars + H1 + H4 regime bars; verify identity + census."""
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
    h1, c1 = h1_resample(exec_bars, raw_ts_close=exec_bars._raw_ts_close)
    h4, c4 = h4_resample(exec_bars)
    census = {"rows": int(len(exec_bars.ts_close)), "h1": c1, "h4": c4}
    if verify_census:
        census_check(census, entry["h1_census"], entry["h4_census"])
    else:
        if c1["interior_gaps"] != 0 or c4["interior_gaps"] != 0:
            raise CensusViolation("interior 15m gap")
    return exec_bars, h1, h4, census


# --------------------------------------------------------------------------
# SPY
# --------------------------------------------------------------------------


def spy_local_path(fz: Freezes):
    """The V2 data_local copy of the frozen SPY snapshot (V1-isolated)."""
    return fz.cycle_dir / "data_local" / "SPY.json.gz"


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
    """Load the adjusted SPY daily series from the V2 local copy.

    Identity is verified against the FREEZE digest; the file read is the v2
    data_local copy (same frozen bytes; the V1 worktree path is never opened
    — the security guard would refuse it).
    """
    entry = fz.data_identity["SPY"]
    path = spy_local_path(fz)
    if not path.exists():
        raise DataBlocked(
            f"BLOCKED_DATA: SPY snapshot missing in v2 data_local: {path}"
        )
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
# cell abstraction
# --------------------------------------------------------------------------


def load_cell(fz: Freezes, cell: str, verify_census: bool = True):
    """Load (exec_bars, regime_bars, regime_period_ns) for a cell.

    Cells: BTC_H1 (regime H1), BTC_H4 (regime H4, independent cell), SPY_D1.
    """
    from . import CELLS

    if cell not in CELLS:
        raise DataBlocked(f"unknown cell {cell}")
    spec = CELLS[cell]
    if spec["asset"] == "btcusdt":
        exec_bars, h1, h4, _ = load_btcusdt(fz, verify_census=verify_census)
        regime = h1 if spec["regime_clock"] == "H1" else h4
        period = HOUR if spec["regime_clock"] == "H1" else H4
        return exec_bars, regime, period
    exec_bars, _, _ = load_spy(fz)
    return exec_bars, exec_bars, DAY


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _date_to_ns(date_str: str) -> int:
    d = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp() * NS)


def _iso_ns(ts_ns: int) -> str:
    d = dt.datetime.fromtimestamp(ts_ns / NS, dt.timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")
