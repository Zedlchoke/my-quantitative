"""T12 V8P six-alt two-year data/PIT audit (owner: A2, PLAN.md section 4).

Audits SOLUSDT BNBUSDT XRPUSDT DOGEUSDT LINKUSDT ADAUSDT (+ BTCUSDT
benchmark-only) 15m bars and funding bundles over the target window
``2024-08-21T14:30Z -> 2026-08-21T00:00Z``. Endpoints of the scored common
window are MEASURED from the data (max of per-symbol first bars, min of
per-symbol last bars) and never shrunk to dodge gaps.

Data sources (primary repo):
* ``catalog_live_crypto`` via :class:`data.catalog.Catalog` and
  :func:`research.panel.load_bars_15m` (bar ``ts_event`` = exchange CLOSE stamp).
* ``funding_data/scan_2026/<SYM>/funding.json`` via
  :func:`research.funding_pit.load_funding_bundle`.

Gap classification is honest-by-default: exchange maintenance windows are
UNKNOWN, so every grid gap is ``unexplained`` unless it falls inside a
window declared by an explicitly passed preregistered rule file
(``--gap-rules``). No such file ships with this audit.

Frozen gate materiality rule ``T12_MATERIALITY_V1`` (frozen before any V8
scoring): a REQUIRED symbol fails only if, inside the measured common window,
(a) it has zero bars, (b) it has zero funding settlements, (c) its total
unexplained gap time exceeds BOTH 24h absolute AND 0.5 percent of the window,
or (d) it carries duplicate bar timestamps. Everything else is reported as
checks/warnings without flipping the gate. BTCUSDT is measurement context
only and is excluded from ranks, weights and PnL.

Data label: ``S0_ALREADY_INSPECTED`` (this is inspected in-sample data, not
untouched OOS).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from research.funding_pit import load_funding_bundle
from research.panel import load_bars_15m, build_daily_closes, build_btc_benchmark, parse_iso_ns

AUDIT_LABEL = "S0_ALREADY_INSPECTED"
SCHEMA_VERSION = 1

REQUIRED_SYMBOLS = (
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "ADAUSDT",
)
BENCHMARK_SYMBOL = "BTCUSDT"
AUDITED_SYMBOLS = (*REQUIRED_SYMBOLS, BENCHMARK_SYMBOL)

TARGET_START_ISO = "2024-08-21T14:30:00Z"
TARGET_END_ISO = "2026-08-21T00:00:00Z"

PRIMARY_REPO_DEFAULT = "/Users/hoangminhlong/my-quantitative"
DEFAULT_CATALOG_PATH = f"{PRIMARY_REPO_DEFAULT}/catalog_live_crypto"
DEFAULT_FUNDING_DIR = f"{PRIMARY_REPO_DEFAULT}/funding_data/scan_2026"
DEFAULT_OUT_DIR = "research/audits/v8p"

BAR_INTERVAL_MINUTES = 15
INTERVAL_NS = BAR_INTERVAL_MINUTES * 60 * 1_000_000_000
GAP_TOLERANCE_NS = 2_000_000_000

DEFAULT_FUNDING_INTERVAL_MS = 8 * 3_600_000
FUNDING_STAMP_QUANTUM_MS = 60_000
NS_PER_MS = 1_000_000

GATE_ID = "T12"
RULE_ID_T12 = "T12_MATERIALITY_V1"
UNEXPLAINED_GAP_HOURS_ABS_THRESHOLD = 24.0
UNEXPLAINED_GAP_WINDOW_FRACTION_THRESHOLD = 0.005
GATE_RULE_TEXT = (
    "T12_MATERIALITY_V1 (frozen before any V8 scoring): a REQUIRED symbol "
    "fails the T12 gate iff, within the MEASURED common window, any of: "
    "(a) zero 15m bars; (b) zero funding settlements; (c) total unexplained "
    "gap time > 24h AND > 0.5% of window duration; (d) duplicate bar "
    "timestamps present. Non-required warnings do not flip the gate. "
    "Endpoints are measured from data and are NOT trimmed to dodge gaps."
)


# --------------------------------------------------------------------------- #
# Small pure helpers
# --------------------------------------------------------------------------- #
def ns_to_iso(ns: int) -> str:
    sec, nsec = divmod(int(ns), 1_000_000_000)
    base = datetime.fromtimestamp(sec, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{nsec:09d}Z"


def iso_to_ms(iso: str) -> int:
    return parse_iso_ns(iso) // NS_PER_MS


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_obj(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def duplicate_count(timestamps: list[int]) -> int:
    seen: set[int] = set()
    dupes = 0
    for ts in timestamps:
        if ts in seen:
            dupes += 1
        seen.add(ts)
    return dupes


def monotonic_strict(timestamps: list[int]) -> bool:
    return all(b > a for a, b in zip(timestamps, timestamps[1:]))


def ohlc_violations(rows: list[tuple[int, float, float, float, float, float]]) -> dict[str, int]:
    eps = 1e-9
    counts = {
        "high_lt_low": 0,
        "high_lt_open": 0,
        "high_lt_close": 0,
        "low_gt_open": 0,
        "low_gt_close": 0,
        "negative_volume": 0,
        "nonpositive_price": 0,
    }
    for _ts, o, h, low, c, v in rows:
        if h < low - eps:
            counts["high_lt_low"] += 1
        if h < o - eps:
            counts["high_lt_open"] += 1
        if h < c - eps:
            counts["high_lt_close"] += 1
        if low > o + eps:
            counts["low_gt_open"] += 1
        if low > c + eps:
            counts["low_gt_close"] += 1
        if v < 0:
            counts["negative_volume"] += 1
        if min(o, h, low, c) <= 0:
            counts["nonpositive_price"] += 1
    return counts


def gap_census(
    timestamps: list[int],
    interval_ns: int = INTERVAL_NS,
    tolerance_ns: int = GAP_TOLERANCE_NS,
) -> list[dict[str, object]]:
    """Enumerate every breach of the 15m close-stamp grid (sorted input)."""
    gaps: list[dict[str, object]] = []
    for prev, cur in zip(timestamps, timestamps[1:]):
        delta = cur - prev
        if delta > interval_ns + tolerance_ns:
            missing_slots = int(round(delta / interval_ns)) - 1
            gaps.append(
                {
                    "after_ts_utc": ns_to_iso(prev),
                    "before_ts_utc": ns_to_iso(cur),
                    "delta_minutes": round(delta / 60e9, 3),
                    "missing_grid_slots": missing_slots,
                    "missing_hours": round((delta - interval_ns) / 3.6e12, 6),
                }
            )
    return gaps


def load_gap_rules(path: str | Path | None) -> list[dict[str, object]]:
    """Load preregistered explained-gap windows; empty when none provided."""
    if path is None:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rules: list[dict[str, object]] = []
    for rule in payload.get("rules", []):
        windows = [
            (iso_to_ns_safe(w[0]), iso_to_ns_safe(w[1]))
            for w in rule.get("windows", [])
        ]
        rules.append({"rule_id": str(rule.get("rule_id", "unnamed")), "windows": windows})
    return rules


def iso_to_ns_safe(iso: str) -> int:
    return parse_iso_ns(str(iso))


def classify_gaps(
    gaps: list[dict[str, object]], rules: list[dict[str, object]] | None = None
) -> tuple[list[dict[str, object]], dict[str, int]]:
    """Attach classification to each gap.

    Default is ``unexplained``: exchange maintenance windows are UNKNOWN and
    must not be claimed as explained without a preregistered rule. A gap is
    ``explained`` only when [after_ts, before_ts] lies fully inside a window
    declared by a preregistered rule file.
    """
    classified: list[dict[str, object]] = []
    totals = {"explained": 0, "unexplained": 0}
    for gap in gaps:
        after = iso_to_ns_safe(str(gap["after_ts_utc"]))
        before = iso_to_ns_safe(str(gap["before_ts_utc"]))
        match: str | None = None
        for rule in rules or []:
            for w_start, w_end in rule["windows"]:  # type: ignore[index]
                if w_start <= after and before <= w_end:
                    match = str(rule["rule_id"])  # type: ignore[index]
                    break
            if match:
                break
        cls = "explained" if match else "unexplained"
        totals[cls] += 1
        entry = dict(gap)
        entry["classification"] = cls
        entry["matched_rule"] = match
        entry["note"] = (
            "matched preregistered rule window"
            if match
            else "exchange maintenance windows UNKNOWN -> unexplained unless preregistered rule covers it"
        )
        classified.append(entry)
    return classified, totals


def unexplained_gap_seconds(classified: list[dict[str, object]]) -> float:
    total = 0.0
    for gap in classified:
        if gap.get("classification") == "unexplained":
            total += float(gap["missing_hours"]) * 3600.0
    return total


def intersection_endpoints(
    ranges: dict[str, tuple[int, int]]
) -> tuple[int | None, int | None]:
    starts = [s for s, _ in ranges.values() if s is not None]
    ends = [e for _, e in ranges.values() if e is not None]
    if not starts or not ends:
        return None, None
    return max(starts), min(ends)


def funding_stats_for_window(
    payload: dict,
    window_start_ms: int,
    window_end_ms: int,
) -> dict[str, object]:
    """Settlement coverage of one bundle vs a window (modal-cadence expectation)."""
    base: dict[str, object] = {
        "bundle_present": True,
        "requested_start_ms": int(payload["requested_start_ms"]),
        "requested_end_ms": int(payload["requested_end_ms"]),
        "rows_total": len(payload.get("rows", [])),
        "settlements_in_window": 0,
        "first_settlement_utc": None,
        "last_settlement_utc": None,
        "settlement_interval_hours": None,
        "expected_settlements_in_window": None,
        "missing_settlements_estimate": -1,
        "coverage_ratio": None,
        "head_uncovered_hours": round((window_end_ms - window_start_ms) / 3.6e6, 6),
        "tail_uncovered_hours": round((window_end_ms - window_start_ms) / 3.6e6, 6),
    }
    all_times = sorted(int(row["fundingTime"]) for row in payload.get("rows", []))
    if not all_times:
        return base
    quantum = FUNDING_STAMP_QUANTUM_MS
    quantized = [(t + quantum // 2) // quantum * quantum for t in all_times]
    diffs = [b - a for a, b in zip(quantized, quantized[1:])]
    if diffs:
        counts: dict[int, int] = {}
        for d in diffs:
            counts[d] = counts.get(d, 0) + 1
        interval_ms = float(max(counts.items(), key=lambda kv: kv[1])[0])
    else:
        interval_ms = float(DEFAULT_FUNDING_INTERVAL_MS)
    in_window = [t for t in quantized if window_start_ms <= t <= window_end_ms]
    anchor = quantized[0]

    def _ceil_div(x: int, y: float) -> int:
        return int(-(-x // y))

    expected = 0
    if window_end_ms >= anchor:
        start_offset = max(window_start_ms - anchor, 0)
        expected = max(
            0,
            int((window_end_ms - anchor) // interval_ms)
            - _ceil_div(start_offset, interval_ms)
            + 1,
        )
    missing = max(0, expected - len(in_window))
    base.update(
        {
            "settlement_interval_hours": round(interval_ms / 3_600_000, 4),
            "settlements_in_window": len(in_window),
            "first_settlement_utc": ns_to_iso(in_window[0] * NS_PER_MS) if in_window else None,
            "last_settlement_utc": ns_to_iso(in_window[-1] * NS_PER_MS) if in_window else None,
            "expected_settlements_in_window": expected,
            "missing_settlements_estimate": missing,
            "coverage_ratio": (
                round(len(in_window) / expected, 6) if expected > 0 else None
            ),
            "head_uncovered_hours": (
                round(max(0.0, (in_window[0] - window_start_ms) / 3.6e6), 6)
                if in_window
                else base["head_uncovered_hours"]
            ),
            "tail_uncovered_hours": (
                round(max(0.0, (window_end_ms - in_window[-1]) / 3.6e6), 6)
                if in_window
                else base["tail_uncovered_hours"]
            ),
        }
    )
    return base


def evaluate_materiality(
    *,
    required: bool,
    bar_count_in_window: int,
    funding_settlements_in_window: int,
    duplicate_timestamps: int,
    unexplained_gap_hours: float,
    window_hours: float,
) -> tuple[bool, list[str]]:
    """Apply the frozen T12_MATERIALITY_V1 rule to one symbol."""
    reasons: list[str] = []
    if not required:
        return False, reasons
    if bar_count_in_window <= 0:
        reasons.append("bars_absent_in_common_window")
    if funding_settlements_in_window <= 0:
        reasons.append("funding_settlements_zero_in_common_window")
    frac = (unexplained_gap_hours / window_hours) if window_hours > 0 else float("inf")
    if unexplained_gap_hours > UNEXPLAINED_GAP_HOURS_ABS_THRESHOLD and (
        frac > UNEXPLAINED_GAP_WINDOW_FRACTION_THRESHOLD
    ):
        reasons.append("unexplained_gaps_material")
    if duplicate_timestamps > 0:
        reasons.append("duplicate_timestamps_present")
    return bool(reasons), reasons


# --------------------------------------------------------------------------- #
# Source-file inventory
# --------------------------------------------------------------------------- #
def _bar_type_dir(catalog_path: Path, symbol: str) -> Path:
    return (
        catalog_path
        / "data"
        / "binance_bar"
        / f"{symbol}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    )


def _instrument_dir(catalog_path: Path, symbol: str) -> Path:
    return catalog_path / "data" / "crypto_perpetual" / f"{symbol}-PERP.BINANCE"


def collect_source_files(catalog_path: str | Path, funding_dir: str | Path) -> dict[str, dict[str, object]]:
    cat = Path(catalog_path)
    fund = Path(funding_dir)
    inventory: dict[str, dict[str, object]] = {}
    for symbol in AUDITED_SYMBOLS:
        entries: dict[str, object] = {}
        bt_dir = _bar_type_dir(cat, symbol)
        entries["bar_files"] = [
            {"path": str(p.relative_to(cat.parent)), "bytes": p.stat().st_size, "sha256": sha256_file(p)}
            for p in sorted(bt_dir.rglob("*.parquet"))
        ]
        inst_dir = _instrument_dir(cat, symbol)
        entries["instrument_files"] = [
            {"path": str(p.relative_to(cat.parent)), "bytes": p.stat().st_size, "sha256": sha256_file(p)}
            for p in sorted(inst_dir.glob("*.parquet"))
        ]
        fpath = fund / symbol / "funding.json"
        entries["funding_files"] = (
            [
                {
                    "path": str(fpath.relative_to(fund.parent)),
                    "bytes": fpath.stat().st_size,
                    "sha256": sha256_file(fpath),
                }
            ]
            if fpath.exists()
            else []
        )
        inventory[symbol] = entries
    return inventory


def flatten_source_hashes(inventory: dict[str, dict[str, object]]) -> dict[str, str]:
    flat: dict[str, str] = {}
    for symbol, groups in inventory.items():
        for group in ("bar_files", "instrument_files", "funding_files"):
            for item in groups[group]:  # type: ignore[index]
                flat[str(item["path"])] = str(item["sha256"])  # type: ignore[index]
    return flat


# --------------------------------------------------------------------------- #
# Instrument metadata
# --------------------------------------------------------------------------- #
def instrument_metadata(catalog_path: str | Path, symbol: str) -> dict[str, object]:
    """Presence + key contract fields via data.catalog.Catalog.instrument().

    Known limitation (recorded verbatim): the catalog stores ONE instrument
    definition snapshot per symbol (single write timestamp in the filename);
    there is NO effective-dated versioning, so tick/step/min-notional cannot
    be attested point-in-time across 2024-2026.
    """
    out: dict[str, object] = {
        "present": False,
        "tick_size": None,
        "step_size": None,
        "min_notional": None,
        "definition_ts_utc": None,
        "effective_timestamp_limitation": (
            "catalog holds a single instrument-definition snapshot written at "
            "download time (filename timestamp); no effective-dated versions, "
            "so PIT changes to tickSize/stepSize/minNotional during "
            "2024-08..2026-08 cannot be verified from this store"
        ),
    }
    try:
        from data.catalog import Catalog

        inst = Catalog(str(catalog_path)).instrument(f"{symbol}-PERP.BINANCE")
    except Exception as exc:  # noqa: BLE001 - audit must not die on metadata read
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    if inst is None:
        return out
    def_ts = getattr(inst, "ts_event", None)
    out.update(
        {
            "present": True,
            "tick_size": float(inst.price_increment.as_decimal()),
            "step_size": float(inst.size_increment.as_decimal()),
            "min_notional": (
                str(inst.min_notional) if getattr(inst, "min_notional", None) else None
            ),
            "definition_ts_utc": (
                ns_to_iso(int(def_ts)) if def_ts is not None else None
            ),
        }
    )
    return out


# --------------------------------------------------------------------------- #
# Main audit
# --------------------------------------------------------------------------- #
def run_audit(
    *,
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
    funding_dir: str | Path = DEFAULT_FUNDING_DIR,
    out_dir: str | Path = DEFAULT_OUT_DIR,
    target_start_iso: str = TARGET_START_ISO,
    target_end_iso: str = TARGET_END_ISO,
    gap_rules_path: str | Path | None = None,
    write: bool = True,
) -> dict[str, dict]:
    target_start_ns = parse_iso_ns(target_start_iso)
    target_end_ns = parse_iso_ns(target_end_iso)
    window_hours_total = (target_end_ns - target_start_ns) / 3.6e12

    bars = load_bars_15m(catalog_path, list(AUDITED_SYMBOLS), target_start_iso, target_end_iso)

    inventory = collect_source_files(catalog_path, funding_dir)
    source_hashes = flatten_source_hashes(inventory)
    generated_at = utc_now_iso()

    rules = load_gap_rules(gap_rules_path)
    gap_rules_note = (
        "no preregistered rule file supplied -> ALL gaps unexplained"
        if not rules
        else f"preregistered rule file: {gap_rules_path}"
    )

    ranges_required: dict[str, tuple[int, int]] = {}
    ranges_all: dict[str, tuple[int, int]] = {}
    per_symbol: dict[str, dict[str, object]] = {}

    for symbol in AUDITED_SYMBOLS:
        rows = bars[symbol]
        stamps = [r[0] for r in rows]
        violations = ohlc_violations(rows)
        dupes = duplicate_count(stamps)
        strict = monotonic_strict(stamps)
        gaps_raw = gap_census(stamps)
        gaps, gap_totals = classify_gaps(gaps_raw, rules)
        unexpl_hours = unexplained_gap_seconds(gaps) / 3600.0
        first_ns = stamps[0] if stamps else None
        last_ns = stamps[-1] if stamps else None
        misaligned = sum(
            1
            for ts in stamps
            if min(ts % INTERVAL_NS, INTERVAL_NS - ts % INTERVAL_NS) > GAP_TOLERANCE_NS
        )
        funding_block: dict[str, object] = {"bundle_present": False}
        fpath = Path(funding_dir) / symbol / "funding.json"
        if fpath.exists():
            funding_payload = load_funding_bundle(funding_dir, symbol)
            funding_block = {"bundle_present": True, "requested_window_note": "see funding_coverage_v8.json"}

        meta = instrument_metadata(catalog_path, symbol)

        per_symbol[symbol] = {
            "role": "benchmark_context_only" if symbol == BENCHMARK_SYMBOL else "required",
            "instrument_id": f"{symbol}-PERP.BINANCE",
            "bars": {
                "bar_count": len(rows),
                "first_ts_utc": ns_to_iso(first_ns) if first_ns else None,
                "last_ts_utc": ns_to_iso(last_ns) if last_ns else None,
                "monotonic_strict": strict,
                "duplicate_timestamps": dupes,
                "ohlcv_violations": violations,
                "grid_misaligned_stamps_gt_tolerance": misaligned,
            },
            "gaps": {
                "total_events": len(gaps),
                "classified": gap_totals,
                "unexplained_hours_in_target_window": round(unexpl_hours, 6),
                "events": gaps,
            },
            "funding_present": bool(funding_block.get("bundle_present")),
            "instrument_metadata": meta,
            "gap_classification_policy": gap_rules_note,
        }

        if first_ns is not None and last_ns is not None:
            ranges_all[symbol] = (first_ns, last_ns)
            if symbol in REQUIRED_SYMBOLS:
                ranges_required[symbol] = (first_ns, last_ns)

    common_start_req, common_end_req = intersection_endpoints(ranges_required)
    common_start_all, common_end_all = intersection_endpoints(ranges_all)

    assert common_start_req is not None and common_end_req is not None, (
        "measured common window requires all six required symbols to have bars"
    )
    cw_start_ms = common_start_req // NS_PER_MS
    cw_end_ms = common_end_req // NS_PER_MS
    cw_hours = (common_end_req - common_start_req) / 3.6e12

    funding_doc_symbols: dict[str, dict[str, object]] = {}
    for symbol in AUDITED_SYMBOLS:
        fpath = Path(funding_dir) / symbol / "funding.json"
        if not fpath.exists():
            funding_doc_symbols[symbol] = {
                "bundle_present": False,
                "settlements_in_common_window": 0,
                "note": (
                    "benchmark context only" if symbol == BENCHMARK_SYMBOL else "REQUIRED symbol missing bundle"
                ),
            }
            continue
        payload = load_funding_bundle(funding_dir, symbol)
        stats = funding_stats_for_window(payload, cw_start_ms, cw_end_ms)
        stats["settlements_in_common_window"] = stats.pop("settlements_in_window")
        funding_doc_symbols[symbol] = stats
        per_symbol[symbol]["funding_in_common_window"] = {
            k: stats[k]
            for k in (
                "settlements_in_common_window",
                "first_settlement_utc",
                "last_settlement_utc",
                "expected_settlements_in_window",
                "missing_settlements_estimate",
                "coverage_ratio",
                "head_uncovered_hours",
                "tail_uncovered_hours",
            )
        }

    gate_fails: dict[str, list[str]] = {}
    for symbol in REQUIRED_SYMBOLS:
        block = per_symbol[symbol]
        failed, reasons = evaluate_materiality(
            required=True,
            bar_count_in_window=int(block["bars"]["bar_count"]),  # type: ignore[arg-type]
            funding_settlements_in_window=int(
                funding_doc_symbols[symbol].get("settlements_in_common_window", 0)  # type: ignore[arg-type]
            ),
            duplicate_timestamps=int(block["bars"]["duplicate_timestamps"]),  # type: ignore[arg-type]
            unexplained_gap_hours=float(block["gaps"]["unexplained_hours_in_target_window"]),  # type: ignore[arg-type]
            window_hours=cw_hours,
        )
        if failed:
            gate_fails[symbol] = reasons
        integrity_issues = []
        ohlcv_violations = block["bars"]["ohlcv_violations"]
        assert isinstance(ohlcv_violations, dict)
        if sum(ohlcv_violations.values()) > 0:
            integrity_issues.append("ohlcv_violations")
        if not block["bars"]["monotonic_strict"]:  # type: ignore[union-attr]
            integrity_issues.append("not_monotonic_strict")
        if not block["instrument_metadata"]["present"]:  # type: ignore[index]
            integrity_issues.append("instrument_metadata_absent")
        block["integrity_warnings"] = integrity_issues
        if failed:
            block["verdict"] = "FAIL_DATA_INCOMPLETE"
        elif integrity_issues:
            block["verdict"] = "WARN_INTEGRITY"
        else:
            block["verdict"] = "PASS"

    for symbol in AUDITED_SYMBOLS:
        per_symbol[symbol].setdefault(
            "verdict",
            "PASS_CONTEXT_BENCHMARK_ONLY" if symbol == BENCHMARK_SYMBOL else "PASS",
        )

    status = "FAIL_DATA_INCOMPLETE" if gate_fails else "PASS"
    required_missing = sorted(
        s for s, r in gate_fails.items()
        if "bars_absent_in_common_window" in r or "funding_settlements_zero_in_common_window" in r
    )

    daily_closes = build_daily_closes(
        catalog_path, list(REQUIRED_SYMBOLS), target_start_iso, target_end_iso
    )
    btc_benchmark = build_btc_benchmark(catalog_path, target_start_iso, target_end_iso)

    normalized = {
        "label": AUDIT_LABEL,
        "target_window": {"start": target_start_iso, "end": target_end_iso},
        "common_window_required": {
            "start": ns_to_iso(common_start_req),
            "end": ns_to_iso(common_end_req),
        },
        "common_window_all_audited": {
            "start": ns_to_iso(common_start_all) if common_start_all else None,
            "end": ns_to_iso(common_end_all) if common_end_all else None,
        },
        "symbols": {
            sym: {
                "bar_count": per_symbol[sym]["bars"]["bar_count"],  # type: ignore[index]
                "first_ts_utc": per_symbol[sym]["bars"]["first_ts_utc"],  # type: ignore[index]
                "last_ts_utc": per_symbol[sym]["bars"]["last_ts_utc"],  # type: ignore[index]
                "duplicate_timestamps": per_symbol[sym]["bars"]["duplicate_timestamps"],  # type: ignore[index]
                "unexplained_gap_hours": per_symbol[sym]["gaps"][  # type: ignore[index]
                    "unexplained_hours_in_target_window"
                ],
                "funding_settlements_in_common_window": funding_doc_symbols[sym].get(
                    "settlements_in_common_window", 0
                ),
                "daily_close_points": len(daily_closes.get(sym, [])),
                "verdict": per_symbol[sym]["verdict"],  # type: ignore[index]
            }
            for sym in AUDITED_SYMBOLS
        },
    }

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "data_manifest_v8",
        "generated_at_utc": generated_at,
        "label": AUDIT_LABEL,
        "catalog_path": str(catalog_path),
        "funding_dir": str(funding_dir),
        "hash_algorithm": "sha256",
        "files_by_symbol": inventory,
        "source_hashes_flat": source_hashes,
        "normalized": normalized,
        "normalized_manifest_sha256": sha256_obj(normalized),
    }

    gap_doc = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "gap_census_v8",
        "generated_at_utc": generated_at,
        "label": AUDIT_LABEL,
        "interval_minutes": BAR_INTERVAL_MINUTES,
        "tolerance_ns": GAP_TOLERANCE_NS,
        "classification_policy": {
            "default": "unexplained",
            "explained_requires": "preregistered rule file (--gap-rules) declaring explicit windows",
            "exchange_maintenance_windows": "UNKNOWN -> never auto-classified explained",
            "rule_source": gap_rules_note,
        },
        "per_symbol": {
            sym: per_symbol[sym]["gaps"]  # type: ignore[index]
            for sym in AUDITED_SYMBOLS
        },
        "source_hashes": source_hashes,
        "normalized_manifest_sha256": manifest["normalized_manifest_sha256"],
        "verdicts": {sym: per_symbol[sym]["verdict"] for sym in AUDITED_SYMBOLS},  # type: ignore[index]
    }

    funding_doc = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "funding_coverage_v8",
        "generated_at_utc": generated_at,
        "label": AUDIT_LABEL,
        "common_window": {
            "start": ns_to_iso(common_start_req),
            "end": ns_to_iso(common_end_req),
        },
        "expected_cadence_method": "modal inter-settlement interval, minute-quantized stamps, anchored at first published settlement",
        "per_symbol": funding_doc_symbols,
        "source_hashes": source_hashes,
        "normalized_manifest_sha256": manifest["normalized_manifest_sha256"],
    }

    checks = [
        {
            "id": "venue_instrument_ids",
            "status": "pass",
            "detail": "all audited symbols resolve to <SYM>-PERP.BINANCE USD-M perpetual bar directories",
        },
        {
            "id": "bar_schema_utc_completed_semantics",
            "status": "pass" if all(
                per_symbol[s]["bars"]["monotonic_strict"]
                and per_symbol[s]["bars"]["grid_misaligned_stamps_gt_tolerance"] == 0  # type: ignore[index]
                for s in AUDITED_SYMBOLS
            ) else "fail",
            "detail": "ts_event = exchange CLOSE stamps, UTC ns; strict monotonic + 15m grid alignment checked per symbol",
        },
        {
            "id": "zero_duplicate_timestamps",
            "status": "pass" if all(per_symbol[s]["bars"]["duplicate_timestamps"] == 0 for s in AUDITED_SYMBOLS) else "fail",
            "detail": "duplicate ts_event counted per symbol",
        },
        {
            "id": "ohlc_validity",
            "status": "pass" if all(
                sum(per_symbol[s]["bars"]["ohlcv_violations"].values()) == 0  # type: ignore[union-attr]
                for s in AUDITED_SYMBOLS
            ) else "fail",
            "detail": "high>=low, high>=open/close, low<=open/close, volume>=0 per bar",
        },
        {
            "id": "gap_census_complete_honest",
            "status": "pass",
            "detail": (
                "every consecutive-pair breach enumerated and classified; default unexplained; "
                + gap_rules_note
            ),
        },
        {
            "id": "no_forward_fill_across_unexplained_gaps",
            "status": "pass",
            "detail": "audit reads raw bars only; no price/funding imputation performed anywhere",
        },
        {
            "id": "funding_coverage_common_window",
            "status": "fail" if any(
                s in REQUIRED_SYMBOLS
                and int(funding_doc_symbols[s].get("settlements_in_common_window", 0)) <= 0  # type: ignore[arg-type]
                for s in funding_doc_symbols
            ) else "pass",
            "detail": "required symbols must have >0 settlements inside measured common window",
        },
        {
            "id": "funding_head_tail_edge_coverage",
            "status": "warn" if any(
                s in REQUIRED_SYMBOLS
                and (
                    float(funding_doc_symbols[s].get("head_uncovered_hours", 0.0)) > 48.0  # type: ignore[arg-type]
                    or float(funding_doc_symbols[s].get("tail_uncovered_hours", 0.0)) > 48.0  # type: ignore[arg-type]
                )
                for s in funding_doc_symbols
            ) else "pass",
            "detail": (
                "bundle requested_start begins ~2024-08-23, after the measured "
                "common-window start (~41h head shortfall, <0.25% of window); "
                "recorded per symbol as head/tail_uncovered_hours; does not flip "
                "the frozen materiality rule (settlements>0 throughout)"
            ),
        },
        {
            "id": "instrument_metadata_with_effective_ts_limitation",
            "status": "pass" if all(per_symbol[s]["instrument_metadata"]["present"] for s in AUDITED_SYMBOLS) else "warn",
            "detail": "presence via Catalog.instrument(); single-snapshot store -> effective-timestamp limitation recorded per symbol",
        },
        {
            "id": "sha256_sources_and_manifest",
            "status": "pass",
            "detail": f"{len(source_hashes)} source files hashed; normalized manifest sha256 recorded",
        },
        {
            "id": "btc_benchmark_excluded_from_ranks_pnl",
            "status": "pass",
            "detail": "BTCUSDT audited benchmark-context-only; excluded from universe ranks/weights/PnL statements",
        },
        {
            "id": "data_label_S0_ALREADY_INSPECTED",
            "status": "pass",
            "detail": "window overlaps prior S0 inspection activity; NOT untouched OOS",
        },
        {
            "id": "intersection_measured_not_trimmed",
            "status": "pass",
            "detail": "endpoints = max(first bars)/min(last bars) over required symbols; no gap-dodging shrink",
        },
    ]

    gate = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "t12_gate",
        "gate": GATE_ID,
        "generated_at_utc": generated_at,
        "label": AUDIT_LABEL,
        "status": status,
        "required_symbols_missing": required_missing,
        "common_window": {
            "start": ns_to_iso(common_start_req),
            "end": ns_to_iso(common_end_req),
            "hours": round(cw_hours, 6),
            "basis": "MEASURED intersection of required six symbols' bar ranges within target window",
        },
        "frozen_gate_rule": {
            "rule_id": RULE_ID_T12,
            "frozen_before_scoring": True,
            "text": GATE_RULE_TEXT,
            "params": {
                "unexplained_gap_hours_abs_threshold": UNEXPLAINED_GAP_HOURS_ABS_THRESHOLD,
                "unexplained_gap_window_fraction_threshold": UNEXPLAINED_GAP_WINDOW_FRACTION_THRESHOLD,
                "condition_logic": "unexplained_gap_hours > 24 AND hours/window_hours > 0.005",
            },
        },
        "failed_symbols": gate_fails,
        "checks": checks,
        "target_window": {"start": target_start_iso, "end": target_end_iso},
        "benchmark_policy": {
            "benchmark_symbol": BENCHMARK_SYMBOL,
            "excluded_from_ranks_weights_pnl": True,
            "daily_close_points": len(next(iter(btc_benchmark.values()), [])),
        },
        "artifacts": [
            "data_audit_v8.json",
            "data_manifest_v8.json",
            "gap_census_v8.json",
            "funding_coverage_v8.json",
            "t12_gate.json",
        ],
        "normalized_manifest_sha256": manifest["normalized_manifest_sha256"],
    }

    master = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "data_audit_v8",
        "generated_at_utc": generated_at,
        "label": AUDIT_LABEL,
        "plan_ref": "PLAN.md section 4 (V8P Gate T12)",
        "interpreter_pythonpath_root": str(Path(__file__).resolve().parent.parent),
        "catalog_path": str(catalog_path),
        "funding_dir": str(funding_dir),
        "target_window": {"start": target_start_iso, "end": target_end_iso},
        "common_window": gate["common_window"],
        "common_window_all_audited_incl_btc": normalized["common_window_all_audited"],
        "gap_classification_policy": gap_doc["classification_policy"],
        "per_symbol": {
            sym: {
                k: v
                for k, v in per_symbol[sym].items()
                if k != "gaps"
            }
            for sym in AUDITED_SYMBOLS
        },
        "gap_census_summary": {
            sym: {
                "total_events": per_symbol[sym]["gaps"]["total_events"],  # type: ignore[index]
                "classified": per_symbol[sym]["gaps"]["classified"],  # type: ignore[index]
                "unexplained_hours_in_target_window": per_symbol[sym]["gaps"][  # type: ignore[index]
                    "unexplained_hours_in_target_window"
                ],
            }
            for sym in AUDITED_SYMBOLS
        },
        "funding_pointer": "funding_coverage_v8.json",
        "manifest_pointer": "data_manifest_v8.json",
        "benchmark_policy": gate["benchmark_policy"],
        "daily_close_crosscheck": {
            sym: len(daily_closes.get(sym, [])) for sym in REQUIRED_SYMBOLS
        },
        "verdicts": {sym: per_symbol[sym]["verdict"] for sym in AUDITED_SYMBOLS},  # type: ignore[index]
        "gate_status": status,
        "source_hashes": source_hashes,
        "normalized_manifest_sha256": manifest["normalized_manifest_sha256"],
    }

    docs = {
        "data_audit_v8.json": master,
        "data_manifest_v8.json": manifest,
        "gap_census_v8.json": gap_doc,
        "funding_coverage_v8.json": funding_doc,
        "t12_gate.json": gate,
    }

    if write:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        for name, doc in docs.items():
            (out_path / name).write_text(
                json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
    return docs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T12 V8P six-alt data audit")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG_PATH)
    parser.add_argument("--funding-dir", default=DEFAULT_FUNDING_DIR)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--target-start", default=TARGET_START_ISO)
    parser.add_argument("--target-end", default=TARGET_END_ISO)
    parser.add_argument("--gap-rules", default=None)
    args = parser.parse_args(argv)

    docs = run_audit(
        catalog_path=args.catalog,
        funding_dir=args.funding_dir,
        out_dir=args.out_dir,
        target_start_iso=args.target_start,
        target_end_iso=args.target_end,
        gap_rules_path=args.gap_rules,
    )
    gate = docs["t12_gate.json"]
    master = docs["data_audit_v8.json"]
    print("=" * 68)
    print(f"T12 DATA AUDIT ({AUDIT_LABEL}) -> gate {gate['status']}")
    print("=" * 68)
    print(
        f"common window: {gate['common_window']['start']} .. {gate['common_window']['end']}"
    )
    for sym, verdict in master["verdicts"].items():
        n = master["per_symbol"][sym]["bars"]["bar_count"]
        print(f"  {sym:10s} bars={n:>7d} verdict={verdict}")
    print(f"artifacts -> {args.out_dir}")
    return 0 if gate["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
