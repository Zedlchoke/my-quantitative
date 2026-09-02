"""V10 shared PIT data hooks (owner: A6, PLAN.md section 6 H07 / section 4.2).

Shared, hash-pinned, point-in-time-safe data access for V10 strategy
modules. Design rules encoded here (V9 lesson: provenance pins existed but
PIT semantics were implicit):

* :class:`HashPinnedCatalog` — open handle over a catalog tree that verifies
  :func:`research.data_audit_v10.catalog_hash` exactly once, lazily, on
  first read. If ``expected_merkle`` is supplied and mismatches, every read
  is refused (fail-closed) — no partial data ever leaves the handle.
  ``read_bars(symbol, start, end)`` returns an IMMUTABLE snapshot (tuple of
  frozen dataclasses) sorted by timestamp with strict completed-bar
  semantics: a bar's ``ts_event_ns`` IS its exchange close stamp (repo
  convention, see research/data_audit_v8.py), so any bar whose close time
  exceeds the requested end is dropped.
* :func:`pit_join` — joins side information (funding/OI/mark) onto bars
  using ONLY values published at or before each bar's decision time,
  ``decision_time = bar_close + info_lag_bars * BAR_INTERVAL_NS``.
* :func:`assert_no_lookahead` — leakage detector over joined rows; raises
  :class:`LookaheadError` if any joined info timestamp exceeds its decision
  time.
* :func:`canonical_repr` — deterministic serialization so identical inputs
  produce byte-identical outputs (sorted keys, compact separators).

Nothing in this module writes to ``data/``, catalog trees or any v9
worktree; readers are read-only by construction.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from research.data_audit_v10 import (
    INTERVAL_NS,
    AuditInputError,
    catalog_hash,
)

BAR_INTERVAL_NS = INTERVAL_NS


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class CatalogHashMismatch(RuntimeError):
    """Expected merkle root provided and the tree does not match — fail-closed."""


class CatalogNotVerified(RuntimeError):
    """Read attempted before the catalog pin could be verified."""


class DataIntegrityError(ValueError):
    """Bar stream violates basic integrity (unsortable/duplicate stamps)."""


class LookaheadError(RuntimeError):
    """Joined side-info timestamp exceeds the bar decision time."""


# --------------------------------------------------------------------------- #
# Immutable snapshots
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class BarSnapshot:
    """Immutable completed bar; ``ts_event_ns`` is the exchange CLOSE stamp."""

    symbol: str
    ts_event_ns: int
    ts_open_ns: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True, slots=True)
class InfoPoint:
    """Side-info observation published at ``publish_ts_ns``."""

    publish_ts_ns: int
    value: float
    kind: str = "info"


@dataclass(frozen=True, slots=True)
class JoinedRow:
    """Bar with the PIT-legal side-info value as of its decision time."""

    symbol: str
    ts_event_ns: int
    decision_time_ns: int
    close: float
    info_publish_ts_ns: Optional[int]
    info_value: Optional[float]
    info_kind: Optional[str]
    info_lag_bars: int


# --------------------------------------------------------------------------- #
# Readers
# --------------------------------------------------------------------------- #
BarReader = Callable[[Any, str, int, int], Iterable[Mapping[str, Any]]]


def _coerce_snapshot(symbol: str, row: Mapping[str, Any]) -> BarSnapshot:
    try:
        ts_event = int(row["ts_event_ns"])
        return BarSnapshot(
            symbol=str(symbol),
            ts_event_ns=ts_event,
            ts_open_ns=int(row.get("ts_open_ns", ts_event - BAR_INTERVAL_NS)),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row.get("volume", 0.0)),
        )
    except KeyError as exc:
        raise DataIntegrityError(f"bar row lacks field {exc}: keys={sorted(row)}") from exc


def _read_tabular_file(path: Any, symbol: str) -> List[Mapping[str, Any]]:
    suffix = str(path).rsplit(".", 1)[-1].lower()
    if suffix == "parquet":
        rows = _read_parquet_file(path)
    elif suffix == "csv":
        rows = _read_csv_file(path)
    else:
        raise DataIntegrityError(f"unsupported bar file type: {path}")
    return [_normalize_row(r, symbol) for r in rows]


def _normalize_row(raw: Mapping[str, Any], symbol: str) -> Dict[str, Any]:
    def _first(*names: str, default: Any = None) -> Any:
        for name in names:
            if name in raw:
                return raw[name]
        return default

    ts_event = _first("ts_event_ns", "ts_event", "close_time_ns", "timestamp_ns")
    if ts_event is None:
        raise DataIntegrityError(f"row lacks a close-stamp column: {sorted(raw)}")
    out = {
        "symbol": symbol,
        "ts_event_ns": int(ts_event),
        "open": float(_first("open", default="nan")),
        "high": float(_first("high", default="nan")),
        "low": float(_first("low", default="nan")),
        "close": float(_first("close", default="nan")),
        "volume": float(_first("volume", default=0.0)),
    }
    ts_open = _first("ts_open_ns", "ts_init_ns", "ts_init")
    if ts_open is not None:
        out["ts_open_ns"] = int(ts_open)
    return out


def _read_csv_file(path: Any) -> List[Dict[str, Any]]:
    import csv

    with open(path, newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_parquet_file(path: Any) -> List[Dict[str, Any]]:
    import pandas as pd

    frame = pd.read_parquet(path)
    return frame.to_dict(orient="records")


def nautilus_catalog_reader(root: Any, symbol: str, start_ns: int, end_ns: int):
    """Default reader for real Nautilus catalog trees (lazy heavy imports)."""
    from pathlib import Path as _Path

    bar_dir = (
        _Path(root)
        / "data"
        / "binance_bar"
        / f"{symbol}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    )
    if not bar_dir.is_dir():
        raise AuditInputError(
            f"no bar directory for {symbol} under {root}: {bar_dir} missing"
        )
    rows: List[Mapping[str, Any]] = []
    for path in sorted(bar_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".parquet", ".csv"}:
            rows.extend(_read_tabular_file(path, symbol))
    return rows


# --------------------------------------------------------------------------- #
# HashPinnedCatalog
# --------------------------------------------------------------------------- #
def _iter_snapshots(rows: Iterable[Mapping[str, Any]], symbol: str,
                    start_ns: int, end_ns: int) -> Tuple[BarSnapshot, ...]:
    seen: set[int] = set()
    snapshots: List[BarSnapshot] = []
    for raw in rows:
        snap = _coerce_snapshot(symbol, raw)
        # Strict completed-bar semantics: ts_event_ns IS the close stamp;
        # drop any bar whose close time lies outside [start, end].
        if snap.ts_event_ns < start_ns or snap.ts_event_ns > end_ns:
            continue
        if snap.ts_event_ns in seen:
            raise DataIntegrityError(
                f"duplicate close stamp {snap.ts_event_ns} for {symbol}"
            )
        seen.add(snap.ts_event_ns)
        snapshots.append(snap)
    snapshots.sort(key=lambda s: s.ts_event_ns)
    return tuple(snapshots)


class HashPinnedCatalog:
    """Lazy, once-verified, fail-closed read-only catalog handle.

    The first access hashes the whole tree via
    :func:`research.data_audit_v10.catalog_hash`; when ``expected_merkle``
    is provided and does not match, :class:`CatalogHashMismatch` is raised
    and the handle stays permanently refused (subsequent reads re-raise).
    """

    def __init__(
        self,
        root: Any,
        expected_merkle: Optional[str] = None,
        reader: Optional[BarReader] = None,
    ) -> None:
        self._root = root
        self._expected_merkle = expected_merkle.lower() if expected_merkle else None
        self._reader: BarReader = reader or nautilus_catalog_reader
        self._verified_report: Optional[Dict[str, Any]] = None
        self._refused_reason: Optional[str] = None

    @property
    def root(self) -> Any:
        return self._root

    @property
    def verified(self) -> bool:
        return self._verified_report is not None

    @property
    def merkle_root_hex(self) -> str:
        if self._verified_report is None:
            raise CatalogNotVerified("catalog hash not yet computed (lazily verified)")
        return str(self._verified_report["merkle_root_hex"])

    @property
    def hash_report(self) -> Dict[str, Any]:
        if self._verified_report is None:
            raise CatalogNotVerified("catalog hash not yet computed (lazily verified)")
        return dict(self._verified_report)

    def _ensure_verified(self) -> None:
        if self._verified_report is not None:
            return
        if self._refused_reason is not None:
            raise CatalogHashMismatch(self._refused_reason)
        report = catalog_hash(self._root)
        actual = str(report["merkle_root_hex"]).lower()
        if self._expected_merkle is not None and actual != self._expected_merkle:
            self._refused_reason = (
                f"catalog merkle mismatch for root={report['root']}: "
                f"expected={self._expected_merkle} actual={actual}"
            )
            raise CatalogHashMismatch(self._refused_reason)
        self._verified_report = report

    def read_bars(
        self, symbol: str, start: int | str, end: int | str
    ) -> Tuple[BarSnapshot, ...]:
        """Immutable, sorted completed-bar snapshot for [start, end].

        Accepts epoch-ns ints or ISO strings; bars whose close stamp
        (``ts_event_ns``) falls outside the window are dropped, never
        forward-filled.
        """
        self._ensure_verified()
        from research.data_audit_v10 import parse_window_ns

        start_ns, end_ns = parse_window_ns(start, end)
        rows = self._reader(self._root, str(symbol), start_ns, end_ns)
        return _iter_snapshots(rows, str(symbol), start_ns, end_ns)


# --------------------------------------------------------------------------- #
# PIT join + leakage detector
# --------------------------------------------------------------------------- #
def normalize_info_series(info_series: Iterable[Any]) -> Tuple[InfoPoint, ...]:
    points: List[InfoPoint] = []
    for item in info_series:
        if isinstance(item, InfoPoint):
            points.append(item)
        elif isinstance(item, Mapping):
            kind = str(item.get("kind", "info"))
            points.append(
                InfoPoint(int(item["publish_ts_ns"]), float(item["value"]), kind)
            )
        else:
            ts, value = item[0], item[1]
            kind = str(item[2]) if len(item) > 2 else "info"
            points.append(InfoPoint(int(ts), float(value), kind))
    points.sort(key=lambda p: p.publish_ts_ns)
    for prev, cur in zip(points, points[1:]):
        if prev.publish_ts_ns == cur.publish_ts_ns:
            raise DataIntegrityError(
                f"duplicate publication timestamp {cur.publish_ts_ns}"
            )
    return tuple(points)


def pit_join(
    bars: Sequence[BarSnapshot],
    info_series: Iterable[Any],
    info_lag_bars: int,
    *,
    interval_ns: int = BAR_INTERVAL_NS,
) -> Tuple[JoinedRow, ...]:
    """Join each bar with the latest side-info published at/before decision.

    ``decision_time_ns = bar.ts_event_ns + info_lag_bars * interval_ns``;
    the selected info point maximizes ``publish_ts_ns <= decision_time_ns``.
    Bars before the first publication get ``None`` info fields — absence of
    data is preserved, never back-filled with future values.
    """
    if info_lag_bars < 0:
        raise ValueError(f"info_lag_bars must be >= 0, got {info_lag_bars}")
    points = normalize_info_series(info_series)
    pub_times = [p.publish_ts_ns for p in points]
    lag_ns = info_lag_bars * interval_ns

    joined: List[JoinedRow] = []
    for bar in bars:
        decision_time = bar.ts_event_ns + lag_ns
        # bisect_right: last index with publish_ts <= decision_time
        lo, hi = 0, len(pub_times)
        while lo < hi:
            mid = (lo + hi) // 2
            if pub_times[mid] <= decision_time:
                lo = mid + 1
            else:
                hi = mid
        idx = lo - 1
        if idx >= 0:
            pt = points[idx]
            joined.append(JoinedRow(
                symbol=bar.symbol,
                ts_event_ns=bar.ts_event_ns,
                decision_time_ns=decision_time,
                close=bar.close,
                info_publish_ts_ns=pt.publish_ts_ns,
                info_value=pt.value,
                info_kind=pt.kind,
                info_lag_bars=info_lag_bars,
            ))
        else:
            joined.append(JoinedRow(
                symbol=bar.symbol,
                ts_event_ns=bar.ts_event_ns,
                decision_time_ns=decision_time,
                close=bar.close,
                info_publish_ts_ns=None,
                info_value=None,
                info_kind=None,
                info_lag_bars=info_lag_bars,
            ))
    return tuple(joined)


def assert_no_lookahead(joined: Sequence[JoinedRow]) -> None:
    """Raise :class:`LookaheadError` on any info timestamp > decision time."""
    for row in joined:
        if row.info_publish_ts_ns is None:
            continue
        if row.info_publish_ts_ns > row.decision_time_ns:
            raise LookaheadError(
                f"lookahead for {row.symbol} bar_close={row.ts_event_ns}: "
                f"info published {row.info_publish_ts_ns} > "
                f"decision time {row.decision_time_ns}"
            )


# --------------------------------------------------------------------------- #
# Determinism helpers
# --------------------------------------------------------------------------- #
def canonical_repr(obj: Any) -> str:
    """Byte-stable serialization: sorted keys, compact separators.

    Dataclasses become sorted-key dicts; tuples/lists keep order; floats use
    Python's deterministic repr. Same inputs always yield identical bytes.
    """
    return json.dumps(_to_canonical(obj), sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)


def _to_canonical(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: _to_canonical(getattr(obj, f.name)) for f in fields(obj)
        }
    if isinstance(obj, Mapping):
        return {str(k): _to_canonical(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_canonical(v) for v in obj]
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            raise ValueError(f"non-finite float cannot be canonically serialized: {obj}")
        return repr(obj)
    raise TypeError(f"cannot canonically serialize {type(obj)!r}")
