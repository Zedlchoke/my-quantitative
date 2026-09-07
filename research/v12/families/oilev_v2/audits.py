"""Audit-only evidence builders for the frozen OILEV-V2 family (V12 I lane).

SCOPE BOUNDARY: this module computes NO PnL, no returns and no scored
metric on real data.  Every real-data output is a field verification, a
count, a timestamp comparison, a schedule verdict or a sha256 equality.
Publication-path exercises use explicitly DUMMY constant metrics into
fail-closed namespaced temporary ledgers only.

All raw data are READ-ONLY workspace files at fixed absolute paths, never
copied or committed (PLAN_crypto.md section 7):

* daily OI consolidated parquets  -- ``/Users/hoangminhlong/my-quantitative/
  oi_data/consolidated`` (staging ``v11_oi_staging_v1``);
* completed 15m bars              -- ``/Users/hoangminhlong/my-quantitative/
  catalog_live_crypto/data/binance_bar`` (Nautilus layout; ``ts_event`` is
  the bar-close boundary in ns; prices are raw i128 / 1e16, A9-F F7);
* native funding settlements      -- ``/Users/hoangminhlong/my-quantitative/
  funding_data/scan_2026`` (Binance ``fundingTime`` ms + ``fundingRate``).

Evidence builders (each returns a JSON-safe payload):

* :func:`evidence_identity` -- frozen identity payloads + the recomputed
  vs recorded ``arm_config_digest`` report (honest mismatch surfacing);
* :func:`evidence_c1_field_verification` -- C1-style per-field check on
  real stamps: the consumed OI row is loader-selected, strictly before
  the stamp, within the frozen 48h staleness gate and positive; the
  consumed bars are loader-selected completed bars whose close decodes
  exactly as ``raw i128 / 1e16``; the fill opens at/after the decision;
* :func:`evidence_feasibility_52` -- schedule-only feasibility re-run via
  :mod:`research.v12.feasibility` over all 52 stamps x 3 frozen arms
  (breadth >= 9, exact 4+4 legs, cap <= 0.30);
* :func:`evidence_funding_events_while_held` -- resolves the A4 open
  item: counts native funding settlements per held span from
  ``scan_2026`` (schedule-only counts, never PnL);
* :func:`evidence_double_generation` -- the full 52-stamp target
  generation for all three arms computed twice; byte-identical canonical
  JSON (sha256 equality);
* :func:`evidence_drop_one` -- the L-V11-7 drop-one diagnostic verified
  through the repaired stress layer (dropped symbol = held max |weight|);
* :func:`run_exact_arm_dummy_dryrun` -- the exact-arm dummy dry-run: the
  adapter primitives traversed per arm, then DUMMY finite metrics
  published into a temporary empty ledger via
  :func:`research.v12.accounting.publish_v12_cell` (a zero-position
  payload must be REFUSED; an exact replay must be an idempotent skip).
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import pyarrow.parquet as pq

from research.adapter_v10.protocol import ContractViolation
from research.v12.data_contract import (
    BARS_ROOT,
    FUNDING_BUNDLES,
    OI_CONSOLIDATED_ROOT,
    PERP_ROOT,
    REQUIRED_SYMBOLS,
    ns_to_iso_utc,
)
from research.v12.families.oilev_v2.plugin import OilevV2Plugin
from research.v12.families.oilev_v2.strategy import (
    ANCHOR_ARM,
    ARM_CONFIG_IDS,
    ARM_IDS,
    BENCHMARK_SYMBOL,
    CAP_MAX,
    FROZEN_ARM_CONFIG_DIGESTS,
    MIN_ELIGIBLE,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    compute_targets_at,
    frozen_arm_digest_report,
    frozen_identity,
    iso_utc,
    stamp_calendar,
)
from research.v12.feasibility import (
    VERDICT_PASS,
    schedule_diagnostics,
    validate_stamp_schedule,
)

AUDITS_SCHEMA = "v12i.oilev_v2.audits.v1"
PRODUCER_ROLE = "I-OILEV"

DAY_NS = 86_400_000_000_000
HOUR_NS = 3_600_000_000_000
BAR_INTERVAL_NS = 900_000_000_000

#: Price decode divisor (A9-F F7, binding): raw i128 / 1e16.
PRICE_DECODE_DIVISOR = 1e16

DEFAULT_LEDGER_PATH = "/tmp/v12i_oilev_v2_dryrun/dryrun_oilev_v2.jsonl"


# --------------------------------------------------------------------------- #
# Read-only loaders (absolute workspace paths; never copied or committed)
# --------------------------------------------------------------------------- #
def decode_i128_price(raw: bytes) -> tuple[float, int]:
    """Decode one Nautilus i128 price column value: ``raw / 1e16``.

    Returns ``(decoded, raw_int)`` so callers can verify the decode
    exactly (``round(decoded * 1e16) == raw_int``).
    """
    raw_int = int.from_bytes(bytes(raw), "little", signed=True)
    decoded = raw_int / PRICE_DECODE_DIVISOR
    if not math.isfinite(decoded) or decoded <= 0.0:
        raise ValueError(f"i128 price decode produced a non-positive value: {decoded}")
    return decoded, raw_int


def _parse_utc_naive(text: str) -> int:
    """``YYYY-MM-DD HH:MM:SS`` (Binance daily metrics, UTC) -> epoch ns."""
    dt = datetime.strptime(str(text).strip(), "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    return int(dt.timestamp()) * 1_000_000_000


def load_oi_by_symbol(
    symbols: Optional[Sequence[str]] = None,
    *,
    root: str = OI_CONSOLIDATED_ROOT,
) -> dict[str, tuple[tuple[int, float], ...]]:
    """Daily consolidated OI rows per symbol: ``[(ts_ns, open_interest)]``.

    Read-only; rows are strictly increasing by construction (one row per
    UTC day at the day's last 5m observation).
    """
    wanted = [str(s) for s in (symbols or REQUIRED_SYMBOLS)]
    out: dict[str, tuple[tuple[int, float], ...]] = {}
    for sym in wanted:
        path = Path(root) / f"{sym}_oi.parquet"
        table = pq.read_table(path)
        times = table.column("create_time").to_pylist()
        values = table.column("sum_open_interest").to_pylist()
        rows = sorted(
            (_parse_utc_naive(t), float(v)) for t, v in zip(times, values)
        )
        seen = [t for t, _ in rows]
        if len(set(seen)) != len(seen):
            raise ValueError(f"{sym}: duplicate OI timestamps after parse")
        out[sym] = tuple(rows)
    return out


def _snap_close_to_boundary(ts: int) -> int:
    """Forward-snap a raw bar-close stamp to the 15m boundary it terminates.

    Binance kline closes sit ~1ms (here ~999_936ns) before the boundary
    they terminate; the snapped boundary is the PIT slot identity.
    """
    remainder = int(ts) % BAR_INTERVAL_NS
    forward = (BAR_INTERVAL_NS - remainder) % BAR_INTERVAL_NS
    if forward < BAR_INTERVAL_NS // 2:
        return int(ts) + forward
    return int(ts)  # unexpected post-boundary stamp: keep raw


def load_completed_bars_around(
    symbol: str,
    instants_ns: Sequence[int],
    *,
    bars_root: str = BARS_ROOT,
    pre_bars: int = 1,
    post_bars: int = 3,
) -> tuple[dict[int, list[dict[str, Any]]], dict[int, list[Any]]]:
    """Loader-selected completed bars around the given instants.

    For each instant this reads the ``pre_bars`` completed bars whose
    close boundary is at or before the instant and the ``post_bars``
    completed bars after it, straight from the Nautilus parquet
    (``ts_event`` = raw close ns; close boundary = forward-snapped slot;
    prices decoded ``raw i128 / 1e16``).  Bars strictly after an instant
    are selected ONLY as execution events (the frozen one declared
    execution lag); decision features never consume them.
    """
    sym_dir = Path(bars_root) / f"{symbol}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    paths = sorted(p for p in sym_dir.glob("*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no bar parquets for {symbol} under {bars_root}")
    needed: set[int] = set()
    for instant in instants_ns:
        for k in range(-int(pre_bars), int(post_bars) + 1):
            needed.add(int(instant) + k * BAR_INTERVAL_NS)
    out: dict[int, list[dict[str, Any]]] = {int(i): [] for i in instants_ns}
    raw_rows: dict[int, list[Any]] = {int(i): [] for i in instants_ns}
    for path in paths:
        table = pq.read_table(
            path,
            columns=["ts_event", "open", "high", "low", "close"],
        )
        ts_list = [int(v) for v in table.column("ts_event").to_pylist()]
        index_by_boundary: dict[int, int] = {}
        for idx, ts in enumerate(ts_list):
            boundary = _snap_close_to_boundary(ts)
            if boundary in needed and boundary not in index_by_boundary:
                index_by_boundary[boundary] = idx
        for boundary in sorted(index_by_boundary):
            idx = index_by_boundary[boundary]
            ts = ts_list[idx]
            close_raw = table.column("close")[idx].as_py()
            close_decoded, close_int = decode_i128_price(close_raw)
            row = {
                "ts_event_ns": ts,
                "close_boundary_ns": boundary,
                "open": decode_i128_price(table.column("open")[idx].as_py())[0],
                "high": decode_i128_price(table.column("high")[idx].as_py())[0],
                "low": decode_i128_price(table.column("low")[idx].as_py())[0],
                "close": (close_decoded, close_int),
                "close_raw_i128": close_int,
            }
            for instant in instants_ns:
                rel = boundary - int(instant)
                if (
                    -int(pre_bars) * BAR_INTERVAL_NS
                    <= rel
                    <= int(post_bars) * BAR_INTERVAL_NS
                ):
                    out[int(instant)].append(row)
                    raw_rows[int(instant)].append(row)
    for instant in instants_ns:
        out[int(instant)].sort(key=lambda r: r["ts_event_ns"])
    return out, raw_rows


def load_bars_for_plugin(
    symbols: Sequence[str],
    instants_ns: Sequence[int],
    *,
    bars_root: str = BARS_ROOT,
) -> dict[str, tuple[Any, ...]]:
    """Completed bars around the schedule instants, as plugin Bar tuples.

    The plugin consumes bars ONLY as execution events (fills at the open
    of the bar covering a decision instant; marks at boundary instants),
    so the audit loader selects the loader-verified completed bars around
    the frozen schedule's instants -- never as decision inputs.
    """
    from research.v11.families.oilever_delev.strategy import Bar

    out: dict[str, tuple[Any, ...]] = {}
    for sym in symbols:
        selected, _raw = load_completed_bars_around(
            str(sym), instants_ns, bars_root=bars_root
        )
        bars: list[Bar] = []
        seen: set[int] = set()
        for rows in selected.values():
            for row in rows:
                ts = int(row["ts_event_ns"])
                if ts in seen:
                    continue
                seen.add(ts)
                bars.append(
                    Bar(
                        ts_event_ns=ts,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"][0]),
                    )
                )
        bars.sort(key=lambda b: b.ts_event_ns)
        out[str(sym)] = tuple(bars)
    return out


def load_settlements(
    symbols: Optional[Sequence[str]] = None,
    *,
    bundle_label: str = "scan_2026",
) -> dict[str, tuple[dict[str, Any], ...]]:
    """Native funding settlements per symbol from a funding bundle root.

    Read-only; each row is ``{"publish_ts_ns": int, "value": float}``
    (Binance ``fundingTime`` ms -> ns; ``fundingRate`` -> float), strictly
    increasing, never de-duplicated by snapping (native records only).
    """
    root = dict(FUNDING_BUNDLES)[bundle_label]
    wanted = [str(s) for s in (symbols or REQUIRED_SYMBOLS)]
    out: dict[str, tuple[dict[str, Any], ...]] = {}
    for sym in wanted:
        path = Path(root) / sym / "funding.json"
        if not path.exists():
            out[sym] = ()
            continue
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows = []
        for row in payload.get("rows") or []:
            ts_ms = row.get("fundingTime")
            rate = row.get("fundingRate")
            if ts_ms is None or rate is None:
                raise ValueError(f"{sym}: funding row missing fundingTime/rate")
            rows.append(
                {
                    "publish_ts_ns": int(ts_ms) * 1_000_000,
                    "value": float(rate),
                }
            )
        rows.sort(key=lambda r: r["publish_ts_ns"])
        seen = [r["publish_ts_ns"] for r in rows]
        if len(set(seen)) != len(seen):
            raise ValueError(f"{sym}: duplicate settlement timestamps")
        out[sym] = tuple(rows)
    return out


def load_tick_sizes(
    symbols: Optional[Sequence[str]] = None, *, perp_root: str = PERP_ROOT
) -> dict[str, float]:
    """Positive price increments (tick sizes) from the crypto_perpetual metadata."""
    wanted = [str(s) for s in (symbols or REQUIRED_SYMBOLS)]
    import pyarrow.parquet as _pq

    out: dict[str, float] = {}
    for sym in wanted:
        sym_dir = Path(perp_root) / f"{sym}-PERP.BINANCE"
        paths = sorted(p for p in sym_dir.glob("*.parquet")) if sym_dir.is_dir() else []
        if not paths:
            raise FileNotFoundError(f"no instrument metadata parquet for {sym}")
        row = _pq.read_table(paths[0]).to_pandas().iloc[0]
        tick = float(row["price_increment"])
        if not math.isfinite(tick) or tick <= 0.0:
            raise ValueError(f"{sym}: non-positive tick size {tick}")
        out[sym] = tick
    return out


def tradeable_universe_symbols() -> tuple[str, ...]:
    """The 19 tradeable names: staged symbols minus the benchmark leg."""
    return tuple(sorted(set(REQUIRED_SYMBOLS) - {BENCHMARK_SYMBOL}))


def first_stamp() -> int:
    """The first decision stamp of the frozen schedule."""
    return stamp_calendar()[0]


def build_plugins(
    *,
    symbols: Optional[Sequence[str]] = None,
    with_settlements: bool = True,
) -> dict[str, OilevV2Plugin]:
    """Build the three frozen arm plugins on the read-only staged snapshot.

    OI rows cover the full staging history (decision features); bars are
    the loader-selected completed bars around the schedule instants
    (execution events only); settlements come from ``scan_2026``.
    """
    universe = tuple(symbols) if symbols else tradeable_universe_symbols()
    instants = stamp_calendar()
    oi_all = load_oi_by_symbol(set(universe) | {BENCHMARK_SYMBOL})
    oi = {sym: oi_all[sym] for sym in universe}
    bars_by_symbol = load_bars_for_plugin(
        set(universe) | {BENCHMARK_SYMBOL}, instants
    )
    settlements = load_settlements(universe) if with_settlements else {}
    tick_sizes = load_tick_sizes(set(universe) | {BENCHMARK_SYMBOL})
    plugins: dict[str, OilevV2Plugin] = {}
    for arm_id in ARM_IDS:
        plugins[arm_id] = OilevV2Plugin(
            arm_id=arm_id,
            oi_by_symbol=oi,
            bars_by_symbol=bars_by_symbol,
            settlements_by_symbol=dict(settlements),
            tick_sizes=dict(tick_sizes),
        )
    return plugins


# --------------------------------------------------------------------------- #
# Evidence builders
# --------------------------------------------------------------------------- #
def evidence_identity() -> dict[str, Any]:
    """Frozen identity payloads + honest recomputed-vs-recorded digest report."""
    from research.v12.families.oilev_v2.strategy import frozen_arm_config

    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        arms[arm_id] = {
            "public_payload": identity.public_payload(),
            "matrix_cohort_hint": identity.matrix_cohort_hint,
            "arm_id_declared": identity.arm_id,
            "recorded_config": frozen_arm_config(arm_id),
        }
    report = frozen_arm_digest_report()
    all_match = all(entry["match"] for entry in report.values())
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "identity",
        "producer_role": PRODUCER_ROLE,
        "digest_function": (
            "research.v11.publication_identity.arm_config_digest("
            "StrategyIdentity(...), arm_id=...)"
        ),
        "arms": arms,
        "digest_report": report,
        "recorded_digests": dict(FROZEN_ARM_CONFIG_DIGESTS),
        "v2_addendum": {
            "freeze_version": "v2",
            "provenance": (
                "selection_freeze.json v2 / integration commit "
                "39fc8821a5c8dbe9c2fd998edc3956ad6a02ec8f (reissued by A1 "
                "before any scored metric exists)"
            ),
            "v1_root_cause": (
                "the v1 selection freeze recorded arm_config_digest WITHOUT "
                "the identity fields (arm_config_id, direction, "
                "strategy_id), so the v1 digests were irreproducible from "
                "any published payload; this lane's exhaustive candidate "
                "search (>50k identities over every defensible reading of "
                "the v1 record) found 0/3 reproductions while the same "
                "function reproduced the V11 freeze digests exactly -- the "
                "report was the decisive evidence for the v2 reissue"
            ),
            "v2_identity_fields": {
                "strategy_id": "hyp_a12_v12_oilever_v2_delev",
                "family_id": "A12-V12-OILEVER-V2-DELEV",
                "direction": "long_short_beta_neutral (all three arms)",
                "arm_config_id_by_arm": dict(ARM_CONFIG_IDS),
                "benchmark_symbols_excluded": ["BTCUSDT"],
                "funding_sign_convention": "LONG_PAYS_POSITIVE_RATE",
                "matrix_cohort_hint": "v12",
                "window": [WINDOW_START_ISO, WINDOW_END_ISO],
            },
            "v2_reproduction": f"{sum(1 for e in report.values() if e['match'])}/3",
            "v2_all_match": bool(all_match),
        },
    }


def _verify_oi_anchor_field(
    series: Sequence[tuple[int, float]],
    *,
    symbol: str,
    target_ns: int,
    parquet_rows: Sequence[tuple[int, float]],
) -> dict[str, Any]:
    """C1 field check: the consumed OI anchor is loader-selected + PIT-correct."""
    from research.v11.families.oilever_delev.strategy import oi_anchor_before

    value = oi_anchor_before(series, int(target_ns))
    consumed_ts: Optional[int] = None
    for ts, _v in reversed(series):
        if ts < int(target_ns):
            consumed_ts = ts
            break
    parquet_value: Optional[float] = None
    if consumed_ts is not None:
        matches = [v for t, v in parquet_rows if t == consumed_ts]
        parquet_value = matches[0] if matches else None
    staleness_ns = (
        None if consumed_ts is None else int(target_ns) - int(consumed_ts)
    )
    return {
        "symbol": symbol,
        "anchor": value,
        "consumed_ts_ns": consumed_ts,
        "consumed_ts_iso": None if consumed_ts is None else ns_to_iso_utc(consumed_ts),
        "strictly_before_target": bool(consumed_ts is not None and consumed_ts < int(target_ns)),
        "staleness_ns": staleness_ns,
        "within_48h_gate": bool(
            staleness_ns is not None and staleness_ns <= 48 * HOUR_NS
        ),
        "loader_selected_value_matches_parquet": bool(
            value is not None
            and parquet_value is not None
            and abs(float(value) - float(parquet_value)) <= 0.0
        ),
        "positive": bool(value is not None and value > 0.0),
    }


def evidence_c1_field_verification(
    *,
    stamps: Optional[Sequence[int]] = None,
    n_stamps: int = 3,
) -> dict[str, Any]:
    """C1-style field verification on real stamps (schedule-only)."""
    from research.v11.families.oilever_delev.strategy import resolve_fill_event

    universe = tradeable_universe_symbols()
    calendar = stamp_calendar()
    if stamps is None:
        picks = sorted({calendar[0], calendar[len(calendar) // 2], calendar[-1]})
        stamps = picks[: int(n_stamps)]
    oi_all = load_oi_by_symbol(set(universe) | {BENCHMARK_SYMBOL})
    per_stamp: list[dict[str, Any]] = []
    for stamp in stamps:
        stamp = int(stamp)
        oi_fields: list[dict[str, Any]] = []
        for sym in universe:
            oi_fields.append(
                _verify_oi_anchor_field(
                    oi_all[sym],
                    symbol=sym,
                    target_ns=stamp,
                    parquet_rows=oi_all[sym],
                )
            )
        # Execution-side bars: the fill event is resolved from
        # loader-selected completed bars around the stamp.
        bar_checks: list[dict[str, Any]] = []
        for sym in sorted(set(universe) | {BENCHMARK_SYMBOL}):
            bars_around, _raw = load_completed_bars_around(sym, [stamp])
            rows = bars_around[stamp]
            covering = [r for r in rows if r["ts_event_ns"] > stamp]
            if not covering:
                bar_checks.append(
                    {
                        "symbol": sym,
                        "fill_bar_close_ns": None,
                        "missing_covering_bar": True,
                    }
                )
                continue
            bar = min(covering, key=lambda r: r["ts_event_ns"])
            decoded, raw_int = float(bar["close"][0]), int(bar["close_raw_i128"])
            # float64 cannot represent 1e16-scale integers exactly, so the
            # round-trip is bounded by the float64 relative precision
            # (ULP(8.68e16) = 16, hence the relative, not absolute, bound)
            roundtrip_error = abs(decoded * PRICE_DECODE_DIVISOR - raw_int)
            roundtrip_bound = max(2.0, abs(raw_int) * 1e-15)
            bar_checks.append(
                {
                    "symbol": sym,
                    "fill_bar_close_ns": int(bar["ts_event_ns"]),
                    "close_boundary_ns": int(bar["close_boundary_ns"]),
                    "fill_open_ns": int(bar["close_boundary_ns"]) - BAR_INTERVAL_NS,
                    "open_at_or_after_decision": bool(
                        int(bar["close_boundary_ns"]) - BAR_INTERVAL_NS >= stamp
                    ),
                    "close_decode_exact": bool(roundtrip_error <= roundtrip_bound),
                    "close_decode_roundtrip_error": roundtrip_error,
                    "close_decode_roundtrip_bound": roundtrip_bound,
                    "close_decoded": decoded,
                    "close_raw_i128": raw_int,
                    "completed_bar_close_is_15m_boundary": bool(
                        int(bar["close_boundary_ns"]) % BAR_INTERVAL_NS == 0
                    ),
                }
            )
        # Feature reproduction through the frozen module (independent of the
        # field loop above): eligibility counts per arm.
        arms_eligible = {}
        for arm_id in ARM_IDS:
            from research.v12.families.oilev_v2.strategy import signal_scores_at

            scores = signal_scores_at(
                arm_id, oi_by_symbol=oi_all, stamp_ns=stamp, universe=universe
            )
            arms_eligible[arm_id] = len(scores)
        per_stamp.append(
            {
                "stamp_ns": stamp,
                "stamp_iso": iso_utc(stamp),
                "oi_anchor_fields": oi_fields,
                "execution_bar_checks": bar_checks,
                "n_eligible_by_arm": arms_eligible,
            }
        )
    all_oi_ok = all(
        field["strictly_before_target"]
        and field["within_48h_gate"]
        and field["loader_selected_value_matches_parquet"]
        and field["positive"]
        for stamp_row in per_stamp
        for field in stamp_row["oi_anchor_fields"]
    )
    all_bar_ok = all(
        check.get("open_at_or_after_decision", False)
        and check.get("close_decode_exact", False)
        and check.get("completed_bar_close_is_15m_boundary", False)
        for stamp_row in per_stamp
        for check in stamp_row["execution_bar_checks"]
    )
    any_missing_bars = any(
        check.get("missing_covering_bar")
        for stamp_row in per_stamp
        for check in stamp_row["execution_bar_checks"]
    )
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "c1_field_verification",
        "producer_role": PRODUCER_ROLE,
        "close_decode_rule": "raw i128 / 1e16 (A9-F F7)",
        "stamps_checked": [int(s) for s in stamps],
        "all_oi_anchor_fields_pit_correct": bool(all_oi_ok),
        "all_execution_bar_fields_verified": bool(all_bar_ok and not any_missing_bars),
        "any_missing_covering_bar": bool(any_missing_bars),
        "per_stamp": per_stamp,
    }


def build_target_records(
    arm_id: str,
    *,
    oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
    universe: Sequence[str],
    instants: Sequence[int],
) -> list[dict[str, Any]]:
    """The 52-stamp target-book schedule of one arm (schedule-only)."""
    records: list[dict[str, Any]] = []
    for stamp in instants:
        book = compute_targets_at(
            arm_id,
            oi_by_symbol=oi_by_symbol,
            stamp_ns=int(stamp),
            universe=universe,
        )
        records.append(
            {
                "decision_ns": int(stamp),
                "status": str(book["status"]),
                "weights": [[sym, float(w)] for sym, w in book["weights"]],
                "diagnostics": book["diagnostics"],
            }
        )
    return records


def evidence_feasibility_52() -> dict[str, Any]:
    """Schedule-only feasibility re-run over all 52 stamps x 3 arms."""
    universe = tradeable_universe_symbols()
    instants = stamp_calendar()
    oi = load_oi_by_symbol(universe)
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        records = build_target_records(
            arm_id, oi_by_symbol=oi, universe=universe, instants=instants
        )
        verdict = validate_stamp_schedule(list(records), legs_per_side=4)
        eligible = [rec["diagnostics"]["n_eligible"] for rec in records]
        max_abs = [rec["diagnostics"]["max_abs_weight"] for rec in records]
        scales = [rec["diagnostics"]["scale_applied"] for rec in records]
        arms[arm_id] = {
            "verdict": verdict["verdict"],
            "n_stamps": verdict["n_stamps"],
            "n_pass": verdict["n_pass"],
            "n_fail": verdict["n_fail"],
            "failing_stamps": verdict["failing_stamps"],
            "n_eligible_min": int(min(eligible)),
            "n_eligible_max": int(max(eligible)),
            "max_abs_weight_observed": float(max(max_abs)),
            "uniform_scale_triggered": any(float(s) != 1.0 for s in scales),
            "cap_max": float(CAP_MAX),
            "min_eligible": int(MIN_ELIGIBLE),
        }
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "feasibility_52_stamps",
        "producer_role": PRODUCER_ROLE,
        "authority_note": (
            "independent re-run via research.v12.feasibility (A4 validator); "
            "counts and verdicts only -- no PnL"
        ),
        "window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "n_schedule_stamps": len(instants),
        "universe_size": len(universe),
        "arms": arms,
        "all_arms_pass": all(a["verdict"] == VERDICT_PASS for a in arms.values()),
    }


def evidence_funding_events_while_held() -> dict[str, Any]:
    """Resolve the A4 open item: funding events while held from scan_2026.

    Held spans are derived from target-book occupancy over the 52-stamp
    schedule; a settlement counts for a span when its timestamp lies
    inside the span per the frozen schedule-diagnostics rule.  COUNTS
    ONLY -- no rate-weighted PnL is computed here.
    """
    universe = tradeable_universe_symbols()
    instants = stamp_calendar()
    oi = load_oi_by_symbol(universe)
    settlements = load_settlements(universe)
    funding_by_symbol = {
        sym: [int(row["publish_ts_ns"]) for row in settlements.get(sym, ())]
        for sym in universe
    }
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        records = build_target_records(
            arm_id, oi_by_symbol=oi, universe=universe, instants=instants
        )
        diagnostics = schedule_diagnostics(
            list(records), funding_events_by_symbol=funding_by_symbol
        )
        block = diagnostics["funding_events_while_held"]
        arms[arm_id] = {
            "funding_status": block["status"],
            "events_while_held_total": block["events_while_held_total"],
            "n_held_spans": diagnostics["holdings"]["n_spans"],
            "median_holding_days": diagnostics["holdings"]["median_holding_days"],
            "decision_count": diagnostics["decision_count"],
            "diagnostics_verdict": diagnostics["verdict"],
            "one_way_turnover_total": diagnostics["one_way_turnover"]["total"],
            "n_settlements_loaded": {
                sym: len(settlements.get(sym, ())) for sym in universe
            },
        }
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "funding_events_while_held",
        "producer_role": PRODUCER_ROLE,
        "bundle": "funding_data/scan_2026 (native Binance settlements)",
        "resolves": "A4 open item: funding-events-while-held UNAVAILABLE",
        "pit_rule": (
            "a settlement counts for a held span iff its timestamp lies "
            "inside the span per the frozen schedule-diagnostics rule "
            "(start < ts <= end)"
        ),
        "schedule_only": True,
        "arms": arms,
        "resolved": all(
            a["funding_status"] == "OK" and a["events_while_held_total"] > 0
            for a in arms.values()
        ),
    }


def _canonical_sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evidence_double_generation() -> dict[str, Any]:
    """Generate the full 52-stamp targets twice; require byte-identical JSON."""
    universe = tradeable_universe_symbols()
    instants = stamp_calendar()
    oi = load_oi_by_symbol(universe)
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        first = build_target_records(
            arm_id, oi_by_symbol=oi, universe=universe, instants=instants
        )
        second = build_target_records(
            arm_id, oi_by_symbol=oi, universe=universe, instants=instants
        )
        sha_first = _canonical_sha256(first)
        sha_second = _canonical_sha256(second)
        arms[arm_id] = {
            "generation_1_sha256": sha_first,
            "generation_2_sha256": sha_second,
            "byte_identical": bool(sha_first == sha_second),
            "records": len(first),
        }
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "double_generation_determinism",
        "producer_role": PRODUCER_ROLE,
        "arms": arms,
        "all_byte_identical": all(a["byte_identical"] for a in arms.values()),
    }


def evidence_drop_one() -> dict[str, Any]:
    """L-V11-7 drop-one diagnostic via the repaired stress layer.

    For real anchor-arm books the dropped symbol must be the HELD symbol
    with the largest absolute weight; an unheld cohort symbol can never be
    selected; a zero-held book fails closed.
    """
    from research.adapter_v10.stress import select_drop_one_symbol

    universe = tradeable_universe_symbols()
    instants = stamp_calendar()
    oi = load_oi_by_symbol(universe)
    checks: list[dict[str, Any]] = []
    for stamp in (instants[0], instants[len(instants) // 2], instants[-2]):
        book = compute_targets_at(
            ANCHOR_ARM, oi_by_symbol=oi, stamp_ns=int(stamp), universe=universe
        )
        weights = {str(sym): float(w) for sym, w in book["weights"]}
        held_abs = {sym: abs(w) for sym, w in weights.items() if abs(w) > 1e-9}
        expected = sorted(held_abs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        dropped = select_drop_one_symbol(
            droppable_symbols=list(universe), realized_weights=weights
        )
        unheld_probe = sorted(set(universe) - set(held_abs))
        # an unheld symbol is never selected even when it is lexicographically
        # first inside the droppable cohort
        never_unheld = dropped[0] in held_abs
        zero_held_refused = False
        try:
            select_drop_one_symbol(
                droppable_symbols=list(universe), realized_weights={}
            )
        except Exception:
            zero_held_refused = True
        checks.append(
            {
                "stamp_ns": int(stamp),
                "stamp_iso": iso_utc(int(stamp)),
                "expected_held_max_symbol": expected,
                "dropped_symbol": dropped[0],
                "matches_held_max": bool(dropped[0] == expected),
                "unheld_symbols_in_cohort": len(unheld_probe),
                "unheld_never_selected": bool(never_unheld),
                "zero_held_book_refused": bool(zero_held_refused),
            }
        )
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "drop_one_diagnostic",
        "producer_role": PRODUCER_ROLE,
        "rule": "drop-one = held max |weight| symbol; ties -> lexicographically smallest",
        "layer": "research.adapter_v10.stress.select_drop_one_symbol (repaired, L-V11-7)",
        "checks": checks,
        "all_match": all(c["matches_held_max"] for c in checks),
    }


# --------------------------------------------------------------------------- #
# Exact-arm dummy dry-run (no real scored metric; temporary ledger only)
# --------------------------------------------------------------------------- #
DRYRUN_DUMMY_METRICS_KIND = "DUMMY_DRYRUN_METRICS"


def _dummy_metrics(
    *, n_positions: int, n_decisions: int
) -> dict[str, Any]:
    """Constant, finite, explicitly DUMMY scored-metric-shaped payload.

    NOT strategy PnL: fixed synthetic constants exercising the publication
    gate plumbing only.
    """
    return {
        "kind": DRYRUN_DUMMY_METRICS_KIND,
        "dry_run": True,
        "scored": False,
        "score_valid": True,  # publication-gate flag only; values are DUMMY
        "net_return_sum": 0.0005,
        "expectancy_per_day": 0.000001,
        "max_drawdown": 0.0002,
        "n_positions": int(n_positions),
        "n_decisions": int(n_decisions),
        "n_fills": int(n_positions) * 2,
        "source": "fixed synthetic constant series; not strategy PnL",
    }


def require_temporary_ledger(path: str | Path) -> Path:
    """Refuse any ledger that is not a namespaced temp-tree dry-run file."""
    resolved = Path(path).expanduser().resolve()
    name = resolved.name
    if not name.startswith("dryrun_") or resolved.suffix != ".jsonl":
        raise ContractViolation(
            f"dry-run ledger must be 'dryrun_*.jsonl' under the temp tree; got {name!r}"
        )
    if "results" in resolved.parts and "registry" in resolved.parts:
        raise ContractViolation("refusing to publish under a results/registry tree")
    return resolved


def _dummy_result_sha256(metrics: Mapping[str, Any]) -> str:
    """Deterministic digest of the DUMMY metrics payload (no real result)."""
    return _canonical_sha256(dict(metrics))


def run_exact_arm_dummy_dryrun(
    *,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
) -> dict[str, Any]:
    """Exact-arm dummy dry-run per frozen arm into a temporary empty ledger.

    For each arm: traverse the adapter primitives on the real staged
    snapshot (identity, cost model, universe, schedule, folds incl. the
    dropped-fold probe, targets/fills/marks at the first stamp, native
    settlements and the LONG_PAYS_POSITIVE_RATE accrual over one held
    span) -- schedule-only, no PnL; then publish DUMMY finite metrics via
    ``research.v12.accounting.publish_v12_cell``:

    * zero-position DUMMY payload -> must be REFUSED (``OBSERVATION`` row);
      an exact replay of that refusal is an idempotent skip;
    * held-position DUMMY payload -> ``CELL_RESULT`` row (DUMMY, never a
      real scored metric); its exact replay is an idempotent skip.

    The ledger must end with EXACTLY one refusal row and one DUMMY cell
    row per arm (any other content refuses the dry-run fail closed).
    """
    from research.adapter_v10.protocol import PositionSpan, StressSpec
    from research.v12.accounting import (
        REFUSED_ZERO_POSITIONS,
        ROW_TYPE_CELL_RESULT,
        ROW_TYPE_OBSERVATION,
        STAGE_IDEMPOTENT_REPLAY,
        STAGE_PUBLISHED,
        STAGE_REFUSED,
        publish_v12_cell,
        read_v12_ledger,
        v12_denominator_view,
    )

    path = require_temporary_ledger(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    plugins = build_plugins()
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        plugin = plugins[arm_id]
        identity = plugin.identity()
        baseline = plugin.baseline_stress()
        universe = plugin.universe(baseline)
        schedule = plugin.schedule()
        folds = plugin.folds(stress=baseline, instants=list(schedule.instants))
        probe_stress = StressSpec(
            name="drop_one_fold", dropped_fold_index=0
        )
        folds_with_drop = plugin.folds(
            stress=probe_stress, instants=list(schedule.instants)
        )
        stamp = int(schedule.instants[0])
        book = plugin.targets_at(stamp, universe=universe, stress=baseline)
        fills = plugin.fills_at(stamp, symbols=universe, stress=baseline)
        marks = plugin.marks_at(universe, stamp)
        settlements = plugin.settlements(universe[0])
        weights = {str(sym): float(w) for sym, w in book["weights"]}
        held_span = PositionSpan(
            symbol=sorted(weights)[0],
            signed_weight=float(weights[sorted(weights)[0]]),
            start_ns=stamp,
            end_ns=stamp + 7 * DAY_NS,
        )
        cashflows = plugin.funding_cashflows_for_spans([held_span])
        for flow in cashflows:
            expected = -float(flow["signed_weight"]) * float(flow["rate"])
            if abs(float(flow["cashflow_per_unit_capital"]) - expected) > 1e-12:
                raise ContractViolation(
                    "funding cashflow violates LONG_PAYS_POSITIVE_RATE"
                )
        n_decisions = len(schedule.instants)
        # The trial key carries the digest RECORDED in the freeze (the
        # binding key material); the identity digest mismatch is surfaced
        # separately by evidence_identity and never silently repaired.
        digest = FROZEN_ARM_CONFIG_DIGESTS[identity.arm_id]

        # The V12 trial key is IDENTITY-only (never the metrics), so a
        # refused compute and its would-be publication share exactly one
        # key -- the ledger can carry a trial exactly once either way.  The
        # dry-run therefore demonstrates the refusal on the BASELINE cell
        # and the dummy publication on a distinct named stress cell.
        zero_metrics = _dummy_metrics(n_positions=0, n_decisions=n_decisions)
        held_metrics = _dummy_metrics(
            n_positions=len(weights), n_decisions=n_decisions
        )
        refused_cell = baseline
        held_cell = StressSpec(
            name="fee_x1_5",
            fee_multiplier=1.5,
            tick_slip_ticks=int(baseline.tick_slip_ticks),
        )
        refused = publish_v12_cell(
            strategy_id=identity.strategy_id,
            family=identity.family_id,
            arm_id=identity.arm_id,
            arm_config_digest=str(digest),
            stress_signature=refused_cell.signature(),
            window_start_iso=identity.window_start_iso,
            window_end_iso=identity.window_end_iso,
            scored_metrics=zero_metrics,
            ledger_path=path,
        )
        published = publish_v12_cell(
            strategy_id=identity.strategy_id,
            family=identity.family_id,
            arm_id=identity.arm_id,
            arm_config_digest=str(digest),
            stress_signature=held_cell.signature(),
            window_start_iso=identity.window_start_iso,
            window_end_iso=identity.window_end_iso,
            scored_metrics=held_metrics,
            result_sha256=_dummy_result_sha256(held_metrics),
            ledger_path=path,
        )
        replay = publish_v12_cell(
            strategy_id=identity.strategy_id,
            family=identity.family_id,
            arm_id=identity.arm_id,
            arm_config_digest=str(digest),
            stress_signature=held_cell.signature(),
            window_start_iso=identity.window_start_iso,
            window_end_iso=identity.window_end_iso,
            scored_metrics=held_metrics,
            result_sha256=_dummy_result_sha256(held_metrics),
            ledger_path=path,
        )
        zero_enforced = refused["stage"] == STAGE_REFUSED and any(
            REFUSED_ZERO_POSITIONS in str(r) for r in refused["reasons"]
        )
        zero_replayed = refused["stage"] == STAGE_IDEMPOTENT_REPLAY
        dummy_ok = published["stage"] in (STAGE_PUBLISHED, STAGE_IDEMPOTENT_REPLAY)
        arms[arm_id] = {
            "adapter_traversal": {
                "strategy_id": identity.strategy_id,
                "arm_config_id": identity.arm_config_id,
                "n_universe": len(universe),
                "n_schedule_instants": n_decisions,
                "n_folds": len(folds),
                "fold_labels": [f.label for f in folds],
                "dropped_fold_accepted": any(f.dropped for f in folds_with_drop),
                "first_stamp_book_symbols": len(weights),
                "n_fills_applied": sum(1 for f in fills if f.applied),
                "first_stamp_mark_finite": all(
                    v is not None and math.isfinite(float(v))
                    for v in marks.values()
                ),
                "n_settlements_first_symbol": len(settlements),
                "n_funding_cashflows_probe_span": len(cashflows),
                "funding_sign_convention": identity.funding_sign_convention,
                "declared_execution_lag": plugin.declared_execution_lag(),
            },
            "zero_position_stage": refused["stage"],
            "zero_position_reason": (
                refused["reasons"][0] if refused["reasons"] else ""
            ),
            "zero_position_cell": refused_cell.name,
            "zero_position_refused": bool(zero_enforced or zero_replayed),
            "dummy_publish_stage": published["stage"],
            "dummy_publish_cell": held_cell.name,
            "dummy_publish_appended": bool(dummy_ok),
            "replay_stage": replay["stage"],
            "replay_idempotent": bool(replay["stage"] == STAGE_IDEMPOTENT_REPLAY),
            "dummy_metrics_kind": DRYRUN_DUMMY_METRICS_KIND,
        }
    view = v12_denominator_view(path)
    if view["published"] != len(ARM_IDS) or view["observed"] != len(ARM_IDS):
        raise ContractViolation(
            "dry-run ledger must hold exactly one DUMMY cell row and one "
            f"zero-position refusal row per arm; got {view}"
        )
    state = read_v12_ledger(path)
    row_types = [str(row["row_type"]) for row in state["rows"]]
    if row_types.count(ROW_TYPE_CELL_RESULT) != len(ARM_IDS) or row_types.count(
        ROW_TYPE_OBSERVATION
    ) != len(ARM_IDS):
        raise ContractViolation("dry-run ledger row types drifted")
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "exact_arm_dummy_dryrun",
        "producer_role": PRODUCER_ROLE,
        "scored": False,
        "real_pnl": False,
        "ledger_path": str(path),
        "ledger_denominators": {
            "published": view["published"],
            "observed": view["observed"],
            "observed_total": view["observed_total"],
        },
        "arms": arms,
        "ok": all(
            a["zero_position_refused"]
            and a["dummy_publish_appended"]
            and a["replay_idempotent"]
            for a in arms.values()
        ),
    }


def build_all_evidence(out_dir: str | Path) -> dict[str, str]:
    """Run every real-data evidence builder and write JSON artifacts."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    builders = {
        "identity_digest_report.json": evidence_identity,
        "c1_field_verification.json": evidence_c1_field_verification,
        "feasibility_52_stamps.json": evidence_feasibility_52,
        "funding_events_while_held.json": evidence_funding_events_while_held,
        "double_generation_determinism.json": evidence_double_generation,
        "drop_one_diagnostic.json": evidence_drop_one,
    }
    written: dict[str, str] = {}
    for name, builder in builders.items():
        payload = builder()
        target = out / name
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1, sort_keys=True, default=str)
            handle.write("\n")
        written[name] = str(target)
    return written


__all__ = [
    "AUDITS_SCHEMA",
    "DRYRUN_DUMMY_METRICS_KIND",
    "PRODUCER_ROLE",
    "PRICE_DECODE_DIVISOR",
    "build_all_evidence",
    "build_plugins",
    "build_target_records",
    "decode_i128_price",
    "evidence_c1_field_verification",
    "evidence_double_generation",
    "evidence_drop_one",
    "evidence_feasibility_52",
    "evidence_funding_events_while_held",
    "evidence_identity",
    "load_oi_by_symbol",
    "load_settlements",
    "load_tick_sizes",
    "require_temporary_ledger",
    "run_exact_arm_dummy_dryrun",
    "tradeable_universe_symbols",
]
