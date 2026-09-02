"""V10 H07 data/PIT audit gates (owner: A6, PLAN.md section 6 H07 + section 11).

Makes the V9 implicit data checks explicit and machine-readable:

* :func:`catalog_hash` — deterministic content hash of a Nautilus catalog
  tree: sorted relative file paths + per-file streaming sha256 folded into a
  single ``merkle_root_hex``. Root-independent (two trees with identical
  content under different roots produce the same merkle root) and stable
  across repeated runs.
* :func:`audit_s0_window` — per-symbol S0 window audit over a universe
  manifest: coverage fraction of expected 15m close stamps, gap census
  (count + locations), first/last timestamps, verdict
  ``PASS`` / ``GAP_FAIL`` / ``MISSING_REQUIRED`` (fail-closed when a
  required symbol has no bars at all). Data label stays
  ``S0_ALREADY_INSPECTED`` (PLAN section 2): this window was inspected, it
  is NOT untouched OOS.
* :func:`clock_audit` — timestamp clock gates for bars/funding/OI/mark
  streams: 15m grid alignment for bars, configurable funding boundary
  cadence (default 8h UTC-anchored), monotonicity and duplicate detection,
  one machine-readable verdict row per stream/check.
* :func:`warmup_purge_audit` — arithmetic enforcement of the PLAN section 11
  contract: warmup must sit outside scored OOS, purge+embargo must be >=
  holding horizon; returns computed boundary indices so runners can be
  cross-checked against the same numbers.
* :func:`write_audit_report` — atomic JSON report writer (tmp + fsync +
  rename) matching the repo's controller conventions.

All inputs are plain Python data (lists of epoch-ns integers / small dicts)
so every gate is unit-testable on synthetic fixtures with zero I/O from the
real catalog. Nothing here writes into ``data/`` or any catalog tree.

V9 lesson encoded: provenance pins existed but PIT coverage/clock/warmup/
purge were implicit — these functions make each an explicit gate row that
fails closed.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

SCHEMA_VERSION = 1
ARTIFACT = "data_audit_v10"
DATA_LABEL = "S0_ALREADY_INSPECTED"

BAR_INTERVAL_MINUTES = 15
INTERVAL_NS = BAR_INTERVAL_MINUTES * 60 * 1_000_000_000
GAP_TOLERANCE_NS = 2_000_000_000          # ±2s stamp jitter tolerated (v8 parity)

DEFAULT_FUNDING_INTERVAL_HOURS = 8
FUNDING_BOUNDARY_TOLERANCE_NS = 120_000_000_000   # ±2min around cadence slots
DEFAULT_SIDE_GRID_NS = INTERVAL_NS                 # OI/mark snapshots on 15m grid

NS_PER_S = 1_000_000_000


class AuditInputError(ValueError):
    """Raised when audit input material is unusable (fail-closed)."""


# --------------------------------------------------------------------------- #
# Small pure helpers
# --------------------------------------------------------------------------- #
def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_obj(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def ns_to_iso(ns: int | None) -> str | None:
    if ns is None:
        return None
    sec, nsec = divmod(int(ns), NS_PER_S)
    from datetime import datetime, timezone

    base = datetime.fromtimestamp(sec, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{nsec:09d}Z"


def parse_window_ns(window_start: str | int, window_end: str | int) -> Tuple[int, int]:
    """Accept ISO-8601 strings or integer epoch-ns for both window edges."""

    def _one(value: str | int, name: str) -> int:
        if isinstance(value, int):
            return value
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise AuditInputError(f"{name} not ISO-8601/epoch-ns: {value!r}") from exc
        if dt.tzinfo is None:
            from datetime import timezone

            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * NS_PER_S)

    start_ns = _one(window_start, "window_start")
    end_ns = _one(window_end, "window_end")
    if end_ns <= start_ns:
        raise AuditInputError(
            f"window_end {end_ns} must be > window_start {start_ns}"
        )
    return start_ns, end_ns


def duplicate_count(timestamps: Sequence[int]) -> int:
    seen: set[int] = set()
    dupes = 0
    for ts in timestamps:
        if ts in seen:
            dupes += 1
        seen.add(ts)
    return dupes


def monotonic_strict(timestamps: Sequence[int]) -> bool:
    return all(b > a for a, b in zip(timestamps, timestamps[1:]))


def grid_misaligned_count(timestamps: Sequence[int], grid_ns: int, tolerance_ns: int) -> int:
    return sum(
        1
        for ts in timestamps
        if min(ts % grid_ns, grid_ns - ts % grid_ns) > tolerance_ns
    )


def off_boundary_count(
    timestamps: Sequence[int], interval_ns: int, anchor_ns: int, tolerance_ns: int
) -> int:
    return sum(
        1
        for ts in timestamps
        if abs((ts - anchor_ns) - round((ts - anchor_ns) / interval_ns) * interval_ns)
        > tolerance_ns
    )


def gap_census(
    timestamps: Sequence[int],
    interval_ns: int = INTERVAL_NS,
    tolerance_ns: int = GAP_TOLERANCE_NS,
) -> List[Dict[str, object]]:
    """Enumerate consecutive-pair breaches of the expected cadence (sorted input)."""
    gaps: List[Dict[str, object]] = []
    ordered = sorted(timestamps)
    for prev, cur in zip(ordered, ordered[1:]):
        delta = cur - prev
        if delta > interval_ns + tolerance_ns:
            gaps.append(
                {
                    "after_ts_utc": ns_to_iso(prev),
                    "before_ts_utc": ns_to_iso(cur),
                    "delta_minutes": round(delta / 60e9, 3),
                    "missing_grid_slots": int(round(delta / interval_ns)) - 1,
                }
            )
    return gaps


# --------------------------------------------------------------------------- #
# catalog_hash
# --------------------------------------------------------------------------- #
def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def catalog_hash(root: str | os.PathLike) -> Dict[str, object]:
    """Deterministic content hash over a directory tree.

    Walks every regular file under ``root``, hashes each file with streamed
    chunked sha256, sorts by POSIX relative path, then folds
    ``"<relpath>  <file_sha256>\\n"`` lines into one sha256 ``merkle_root_hex``.
    The absolute root path never enters the digest, so two trees with
    byte-identical content under different roots hash identically.
    """
    root_path = Path(root)
    if not root_path.exists():
        raise AuditInputError(f"catalog root does not exist: {root_path}")
    if not root_path.is_dir():
        raise AuditInputError(f"catalog root is not a directory: {root_path}")

    entries: List[Tuple[str, int, str]] = []
    total_bytes = 0
    for path in sorted(root_path.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root_path).as_posix()
        size = path.stat().st_size
        entries.append((rel, size, _sha256_file(path)))
        total_bytes += size
    entries.sort(key=lambda item: item[0])

    merkle = hashlib.sha256()
    for rel, size, file_hash in entries:
        merkle.update(f"{rel}  {size}  {file_hash}\n".encode("utf-8"))

    return {
        "root": str(root_path),
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "merkle_root_hex": merkle.hexdigest(),
    }


# --------------------------------------------------------------------------- #
# audit_s0_window
# --------------------------------------------------------------------------- #
VERDICT_PASS = "PASS"
VERDICT_GAP_FAIL = "GAP_FAIL"
VERDICT_MISSING_REQUIRED = "MISSING_REQUIRED"


def _stamps_from_report_entry(entry: Any) -> List[int]:
    if isinstance(entry, dict):
        for key in ("ts_event_ns", "bar_timestamps_ns", "timestamps_ns", "bars"):
            if key in entry:
                entry = entry[key]
                break
        else:
            raise AuditInputError(f"report entry lacks timestamp list: keys={sorted(entry)}")
    if isinstance(entry, dict):  # bars given as {ts: row}
        stamps = [int(k) for k in entry.keys()]
    else:
        stamps = [int(ts) for ts in entry]
    return sorted(stamps)


def normalize_catalog_report(catalog_report: Mapping[str, Any]) -> Dict[str, List[int]]:
    """Accept ``{"symbols": {...}}`` or a flat ``{symbol: stamps}`` mapping."""
    body = catalog_report.get("symbols", catalog_report)
    if not isinstance(body, Mapping):
        raise AuditInputError("catalog_report must map symbols to bar timestamps")
    return {str(sym): _stamps_from_report_entry(entry) for sym, entry in body.items()}


def required_symbols_from_manifest(universe_manifest: Mapping[str, Any]) -> List[str]:
    selected = universe_manifest.get("selected_symbols")
    if isinstance(selected, list) and selected:
        symbols: List[str] = []
        for entry in selected:
            if isinstance(entry, dict):
                sym = entry.get("symbol") or entry.get("instrument_id")
            else:
                sym = entry
            if not sym:
                raise AuditInputError(f"selected_symbols entry lacks symbol: {entry!r}")
            symbols.append(str(sym))
        return symbols
    required = universe_manifest.get("required_symbols")
    if isinstance(required, list) and required:
        return [str(sym) for sym in required]
    raise AuditInputError(
        "universe_manifest lacks selected_symbols/required_symbols; refusing to guess"
    )


def benchmark_symbol_from_manifest(universe_manifest: Mapping[str, Any]) -> str | None:
    bench = universe_manifest.get("btc_benchmark_context_only")
    if isinstance(bench, dict):
        return bench.get("symbol")
    return universe_manifest.get("benchmark_symbol")


def audit_s0_window(
    catalog_report: Mapping[str, Any],
    universe_manifest: Mapping[str, Any],
    window_start: str | int,
    window_end: str | int,
    *,
    interval_ns: int = INTERVAL_NS,
    tolerance_ns: int = GAP_TOLERANCE_NS,
) -> Dict[str, Any]:
    """Per-symbol S0 window audit; fails closed on missing required symbols.

    ``catalog_report`` maps symbol → iterable of bar close-stamp epochs in ns
    (optionally wrapped as ``{"symbols": {...}}``). Expected-bar counts are
    grid-aligned slot counts across [window_start, window_end]; any breach of
    the cadence (or coverage < 1.0) yields ``GAP_FAIL``; a required symbol
    with zero bars yields ``MISSING_REQUIRED`` which flips the overall status
    unconditionally. Benchmark-context symbols are reported but cannot flip
    the gate.
    """
    start_ns, end_ns = parse_window_ns(window_start, window_end)
    stamps_by_symbol = normalize_catalog_report(catalog_report)
    required = required_symbols_from_manifest(universe_manifest)
    benchmark = benchmark_symbol_from_manifest(universe_manifest)

    k_first = -(-start_ns // interval_ns)          # ceil division to grid
    k_last = end_ns // interval_ns                  # floor division to grid
    expected_slots = max(0, k_last - k_first + 1)
    grid_start = k_first * interval_ns
    grid_end = k_last * interval_ns

    rows: Dict[str, Dict[str, Any]] = {}
    failed_required: List[str] = []
    missing_required: List[str] = []

    audited = set(required) | set(stamps_by_symbol)
    if benchmark:
        audited.add(benchmark)

    for symbol in sorted(audited):
        role = (
            "benchmark_context_only" if symbol == benchmark else "required"
        )
        stamps = stamps_by_symbol.get(symbol, [])
        reasons: List[str] = []

        if not stamps:
            row: Dict[str, Any] = {
                "role": role,
                "bar_count": 0,
                "first_ts_utc": None,
                "last_ts_utc": None,
                "expected_grid_slots_in_window": expected_slots,
                "coverage_fraction": 0.0,
                "gap_census": [],
                "duplicate_timestamps": 0,
                "monotonic_strict": True,
                "reasons": ["zero_bars"],
                "verdict": VERDICT_GAP_FAIL if role != "required" else VERDICT_MISSING_REQUIRED,
            }
            if role == "required":
                missing_required.append(symbol)
            rows[symbol] = row
            continue

        in_window = [ts for ts in stamps if start_ns <= ts <= end_ns]
        observed_unique = len(set(in_window))
        coverage = (
            round(observed_unique / expected_slots, 6) if expected_slots > 0 else 0.0
        )
        gaps = gap_census(in_window, interval_ns=interval_ns, tolerance_ns=tolerance_ns)
        dupes = duplicate_count(stamps)
        strict = monotonic_strict(stamps)

        if len(in_window) == 0:
            reasons.append("no_bars_inside_window")
        if gaps:
            reasons.append("grid_gaps_present")
        if coverage < 1.0:
            reasons.append("coverage_below_full")
        if dupes:
            reasons.append("duplicate_timestamps")
        if not strict:
            reasons.append("not_monotonic_strict")

        verdict = VERDICT_PASS if not reasons else VERDICT_GAP_FAIL
        if role == "required" and verdict != VERDICT_PASS:
            failed_required.append(symbol)

        rows[symbol] = {
            "role": role,
            "bar_count": len(stamps),
            "bars_in_window": len(in_window),
            "first_ts_utc": ns_to_iso(stamps[0]),
            "last_ts_utc": ns_to_iso(stamps[-1]),
            "first_ts_in_window_utc": ns_to_iso(in_window[0]) if in_window else None,
            "last_ts_in_window_utc": ns_to_iso(in_window[-1]) if in_window else None,
            "expected_grid_slots_in_window": expected_slots,
            "expected_window_grid_span_utc": [ns_to_iso(grid_start), ns_to_iso(grid_end)],
            "coverage_fraction": coverage,
            "gap_census": gaps,
            "gap_event_count": len(gaps),
            "duplicate_timestamps": dupes,
            "monotonic_strict": strict,
            "reasons": reasons,
            "verdict": verdict,
        }

    status = (
        "FAIL_MISSING_REQUIRED"
        if missing_required
        else ("FAIL" if failed_required else "PASS")
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": f"{ARTIFACT}_s0_window",
        "label": DATA_LABEL,
        "window_start_ns": start_ns,
        "window_end_ns": end_ns,
        "interval_minutes": interval_ns // 60_000_000_000,
        "tolerance_ns": tolerance_ns,
        "required_symbols": list(required),
        "benchmark_context_only": benchmark,
        "per_symbol": rows,
        "missing_required_symbols": missing_required,
        "failed_required_symbols": failed_required,
        "status": status,
        "note": (
            "S0 screening window already inspected in V9; NOT untouched OOS "
            "(PLAN.md section 2). Verdicts are fail-closed: any required-symbol "
            "gap, shortfall vs full grid-slot coverage, duplicates or "
            "non-monotonic stamps blocks."
        ),
    }


# --------------------------------------------------------------------------- #
# clock_audit
# --------------------------------------------------------------------------- #
def clock_audit(
    bar_rows: Sequence[int],
    funding_rows: Sequence[int],
    oi_rows: Sequence[int],
    mark_rows: Sequence[int],
    *,
    interval_ns: int = INTERVAL_NS,
    bar_tolerance_ns: int = GAP_TOLERANCE_NS,
    funding_interval_ns: int = DEFAULT_FUNDING_INTERVAL_HOURS * 3_600 * NS_PER_S,
    funding_anchor_ns: int = 0,
    funding_tolerance_ns: int = FUNDING_BOUNDARY_TOLERANCE_NS,
    oi_grid_ns: int = DEFAULT_SIDE_GRID_NS,
    mark_grid_ns: int = DEFAULT_SIDE_GRID_NS,
) -> Dict[str, Any]:
    """Clock gates for all four streams; one machine-readable row per check.

    Bars must sit on the (configurable) 15m grid within tolerance; funding
    stamps must land on ``funding_anchor_ns + k*funding_interval_ns`` slots
    (default UTC 00:00/08:00/16:00 boundaries ±2min); OI/mark default to the
    15m snapshot grid. Every stream additionally requires strictly monotonic
    stamps with zero duplicates.
    """
    streams: List[Tuple[str, Sequence[int], int, str]] = [
        ("bars", bar_rows, interval_ns, "bar_close_grid"),
        ("funding", funding_rows, funding_interval_ns, "funding_boundary"),
        ("open_interest", oi_rows, oi_grid_ns, "oi_snapshot_grid"),
        ("mark", mark_rows, mark_grid_ns, "mark_snapshot_grid"),
    ]
    checks: List[Dict[str, Any]] = []
    for name, stamps, grid_ns, label in streams:
        as_given = [int(ts) for ts in stamps]
        ordered = sorted(as_given)
        tolerance = funding_tolerance_ns if label == "funding_boundary" else bar_tolerance_ns
        misaligned_idx = [
            ts for ts in ordered
            if min(ts % grid_ns, grid_ns - ts % grid_ns) > tolerance
        ]
        if label == "funding_boundary":
            off_boundary = [
                ts for ts in ordered
                if abs((ts - funding_anchor_ns)
                       - round((ts - funding_anchor_ns) / grid_ns) * grid_ns)
                > funding_tolerance_ns
            ]
        else:
            off_boundary = []
        off = sorted(set(misaligned_idx) | set(off_boundary))
        # Monotonicity is checked in the ORDER GIVEN by the caller: sorting
        # here would silently repair out-of-order streams.
        non_mono_pairs = [
            (prev, cur) for prev, cur in zip(as_given, as_given[1:]) if cur <= prev
        ]
        dupes = duplicate_count(ordered)

        checks.append({
            "stream": name,
            "check": f"{label}_alignment",
            "status": "PASS" if not off else "FAIL",
            "violation_count": len(off),
            "violation_examples_utc": [ns_to_iso(ts) for ts in off[:5]],
            "detail": (
                f"{label}: stamps within tolerance of expected "
                + ("cadence boundaries anchored at funding_anchor_ns"
                   if label == "funding_boundary" else "grid")
            ),
        })
        checks.append({
            "stream": name,
            "check": "monotonic_strict",
            "status": "PASS" if not non_mono_pairs else "FAIL",
            "violation_count": len(non_mono_pairs),
            "violation_examples_utc": [
                ns_to_iso(cur) for _prev, cur in non_mono_pairs[:5]
            ],
            "detail": "strictly increasing timestamps",
        })
        checks.append({
            "stream": name,
            "check": "no_duplicate_timestamps",
            "status": "PASS" if dupes == 0 else "FAIL",
            "violation_count": dupes,
            "violation_examples_utc": [],
            "detail": "each stamp appears at most once",
        })

    failed = [row for row in checks if row["status"] != "PASS"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": f"{ARTIFACT}_clock",
        "rows_total": {
            "bars": len(bar_rows),
            "funding": len(funding_rows),
            "open_interest": len(oi_rows),
            "mark": len(mark_rows),
        },
        "config": {
            "interval_ns": interval_ns,
            "bar_tolerance_ns": bar_tolerance_ns,
            "funding_interval_hours": funding_interval_ns // (3_600 * NS_PER_S),
            "funding_interval_ns": funding_interval_ns,
            "funding_anchor_ns": funding_anchor_ns,
            "funding_tolerance_ns": funding_tolerance_ns,
            "oi_grid_ns": oi_grid_ns,
            "mark_grid_ns": mark_grid_ns,
        },
        "checks": checks,
        "failed_checks": [f"{c['stream']}:{c['check']}" for c in failed],
        "verdict": "PASS" if not failed else "FAIL",
    }


# --------------------------------------------------------------------------- #
# warmup_purge_audit
# --------------------------------------------------------------------------- #
def warmup_purge_audit(
    window_start: int,
    window_end: int,
    warmup_bars: int,
    purge_bars: int,
    embargo_bars: int,
    holding_horizon_bars: int,
    *,
    min_warmup_bars: int = 0,
) -> Dict[str, Any]:
    """Arithmetic enforcement of PLAN section 11 fold hygiene.

    Bar indices delimit a half-open scored-OOS span ``[window_start,
    window_end)``. Warm-up consumes bars strictly before the span;
    purging removes the last ``purge_bars`` pre-span bars from training and
    embargoes the first ``embargo_bars`` post-span bars before any later
    evaluation may resume. Gates:

    * ``warmup_outside_oos``: ``warmup_bars >= min_warmup_bars`` and the
      warm-up region ``[window_start - warmup_bars, window_start)`` never
      overlaps the scored span (a negative warm-up means features are being
      computed inside OOS — fail).
    * ``warmup_within_data``: ``window_start - warmup_bars >= 0``.
    * ``purge_embargo_ge_holding``: ``purge_bars + embargo_bars >=
      holding_horizon_bars``.
    * ``window_valid``: ``window_end > window_start``.
    """
    checks: List[Dict[str, Any]] = []

    def _add(cid: str, ok: bool, detail: str) -> None:
        checks.append({"id": cid, "status": "PASS" if ok else "FAIL", "detail": detail})

    warmup_start = window_start - max(warmup_bars, 0)
    overlaps_oos = warmup_bars < 0
    _add(
        "warmup_outside_oos",
        warmup_bars >= min_warmup_bars and not overlaps_oos,
        f"warmup region [{warmup_start}, {window_start}) must precede scored OOS "
        f"with >= {min_warmup_bars} bars (got warmup_bars={warmup_bars})",
    )
    _add(
        "warmup_within_data",
        warmup_start >= 0,
        f"warmup start index {warmup_start} must be >= 0 (enough history before OOS)",
    )
    _add(
        "purge_embargo_ge_holding",
        purge_bars + embargo_bars >= holding_horizon_bars,
        f"purge+embargo ({purge_bars}+{embargo_bars}) must be >= holding horizon "
        f"{holding_horizon_bars}",
    )
    _add(
        "window_valid",
        window_end > window_start,
        f"scored OOS span [{window_start}, {window_end}) must be non-empty and ordered",
    )

    failed = [c["id"] for c in checks if c["status"] != "PASS"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": f"{ARTIFACT}_warmup_purge",
        "boundary_indices": {
            "oos_start": window_start,
            "oos_end": window_end,
            "warmup_start": warmup_start,
            "warmup_end": window_start,
            "train_effective_end": window_start - purge_bars,
            "purged_zone": [window_start - purge_bars, window_start],
            "embargo_zone": [window_end, window_end + embargo_bars],
            "next_evaluable_index": window_end + embargo_bars,
        },
        "params": {
            "warmup_bars": warmup_bars,
            "purge_bars": purge_bars,
            "embargo_bars": embargo_bars,
            "holding_horizon_bars": holding_horizon_bars,
            "min_warmup_bars": min_warmup_bars,
        },
        "checks": checks,
        "failed_checks": failed,
        "verdict": "PASS" if not failed else "FAIL",
    }


# --------------------------------------------------------------------------- #
# Atomic report writer
# --------------------------------------------------------------------------- #
def write_audit_report(report_dict: Mapping[str, Any], path: str | os.PathLike) -> Path:
    """Atomically persist a report dict: unique tmp file + fsync + replace."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_name(f".{out_path.name}.{uuid.uuid4().hex}.tmp")
    payload = json.dumps(report_dict, indent=2, sort_keys=True) + "\n"
    try:
        with open(tmp_path, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, out_path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
    dir_fd = os.open(out_path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
    return out_path
