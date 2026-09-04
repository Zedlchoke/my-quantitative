"""Audit-only evidence builders for the frozen OITD family (V13 I lane).

SCOPE BOUNDARY: this module computes NO PnL, no returns and no scored
metric on real data.  Every real-data output is a field verification, a
count, a timestamp comparison, a schedule verdict, a turnover estimate, a
cost-drag verdict or a sha256 equality.  Publication-path exercises use
explicitly DUMMY constant metrics into fail-closed namespaced temporary
ledgers only.  Zero scored metrics exist anywhere in this lane.

All raw data are READ-ONLY workspace files at fixed absolute paths, never
copied or committed:

* completed 15m bars              -- ``/Users/hoangminhlong/my-quantitative/
  catalog_live_crypto/data/binance_bar`` (Nautilus layout; ``ts_event`` is
  the bar-close boundary in ns; prices AND base volume decode raw
  i128 / 1e16, A9-F F7);
* daily OI consolidated parquets  -- ``/Users/hoangminhlong/my-quantitative/
  oi_data/consolidated`` (staging ``v11_oi_staging_v1``; BASE units);
* mark-price snapshots            -- the ``markPrice`` field of the native
  funding settlement rows in ``/Users/hoangminhlong/my-quantitative/
  funding_data/scan_2026`` (the A9-F staged mark root: present on EVERY
  row, all 20 symbols; availability = the settlement stamp, max staleness
  8h -- inside the frozen 24h pairing tolerance);
* native funding settlements      -- the same ``scan_2026`` rows
  (``fundingTime`` ms + ``fundingRate``), COST ONLY;
* instrument tick sizes           -- ``catalog_live_crypto/data/
  crypto_perpetual`` (frozen V12 audit loader reused verbatim).

Evidence builders (each returns a JSON-safe payload):

* :func:`evidence_identity` -- frozen identity payloads + the recomputed
  vs recorded ``arm_config_digest`` report;
* :func:`build_target_records` -- the chained hysteresis target schedule
  of one arm;
* :func:`evidence_schedule_only_real` -- schedule-only feasibility on the
  REAL snapshot for all three arms: decisions/folds/carried stamps/
  breadth/turnover estimates/availability + the frozen
  ``research.v11.cost_feasibility`` gate (base and stress drag floors) --
  decisions, folds, holding, turnover and cost estimates ONLY (no PnL);
* :func:`evidence_drop_one` -- the drop-one diagnostic: at every stamp the
  dropped symbol IS the held max-|weight| symbol, was actually held, the
  remaining weights are unchanged, and zero-position books are refused;
* :func:`run_dummy_dryrun` -- the dummy publication dry-run into a
  TEMPORARY namespaced ledger: adapter traversal per arm, zero-position
  refusal, out-of-contract refusal, one DUMMY publish per arm, exact
  replays with ZERO counter delta (DUMMY constants, never real metrics).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence

import pyarrow.parquet as pq

from research.adapter_v10.protocol import (
    ContractViolation,
    PositionSpan,
    StressSpec,
)
from research.v11.cost_feasibility import (
    KIND_DISCRETIONARY,
    KIND_FORCED_FLAT,
    ScheduleArtifacts,
    ScheduleDecision,
    SignalAvailability,
    STRESS_EXTRA_TICKS,
    STRESS_FEE_MULTIPLIER,
    STRESS_NAME,
    evaluate_schedule_cost_feasibility,
)
from research.v12.accounting import (
    REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT,
    REFUSED_ZERO_POSITIONS,
    ROW_TYPE_CELL_RESULT,
    ROW_TYPE_OBSERVATION,
    STAGE_IDEMPOTENT_REPLAY,
    STAGE_PUBLISHED,
    STAGE_REFUSED,
    freeze_family_cell_contract,
    publish_v12_cell,
    read_v12_ledger,
    v12_denominator_view,
)
from research.v12.data_contract import (
    BARS_ROOT,
    FUNDING_BUNDLES,
    OI_CONSOLIDATED_ROOT,
    REQUIRED_SYMBOLS,
    ns_to_iso_utc,
)
from research.v12.families.oilev_v2.audits import (
    decode_i128_price,
    load_tick_sizes,
    require_temporary_ledger,
)
from research.v12.feasibility import (
    schedule_diagnostics,
    validate_stamp_schedule,
)
from research.v13.families.oitd.book import (
    EligibilityShortfall,
    drop_one_book,
    held_max_abs_weight_symbol,
)
from research.v13.families.oitd.plugin import OitdPlugin
from research.v13.families.oitd.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    BENCHMARK_SYMBOL,
    BAR_INTERVAL_NS,
    BARS_PER_DAY,
    CAP_MAX,
    CONTROL_ARM,
    FAMILY_ID,
    FROZEN_ARM_CONFIG_DIGESTS,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    frozen_arm_config,
    frozen_arm_digest_report,
    frozen_identity,
    snap_close_to_boundary,
    stamp_calendar,
)

AUDITS_SCHEMA = "v13i.oitd.audits.v1"
PRODUCER_ROLE = "I-OITD"

DAY_NS = 86_400_000_000_000

#: Price AND base-volume decode divisor (A9-F F7, binding): raw i128 / 1e16.
PRICE_DECODE_DIVISOR = 1e16

DEFAULT_LEDGER_PATH = "/tmp/v13i_oitd_dryrun/dryrun_oitd.jsonl"

DRYRUN_DUMMY_METRICS_KIND = "DUMMY_DRYRUN_METRICS"

#: Frozen stressed cell (L-V11-1): fee x1.5 / +2 adverse ticks / +1 delay.
STRESS_EVENT_DELAY = 1


def tradeable_universe_symbols() -> tuple[str, ...]:
    """The 19 tradeable names: the frozen REQUIRED_SYMBOLS minus BTCUSDT."""
    return tuple(sorted(set(REQUIRED_SYMBOLS) - {BENCHMARK_SYMBOL}))


def fold_end_instants() -> list[int]:
    """The three fold-boundary instants (force-flat points, frozen windows).

    F0/F1/F2 calendar ends from the pinned ``FOLD_WINDOWS``; the last one is
    the screen-window end.  At each boundary the family force-flats (the
    purge guarantees no in-fold book straddles it), so the cost-feasibility
    artifacts record one ``FORCED_FLAT`` decision per boundary -- counted
    and reported SEPARATELY from discretionary decisions (frozen A3
    vocabulary; OITD.md decision clock).
    """
    from research.v13.families.oitd.strategy import FOLD_WINDOWS, parse_iso_utc

    return [
        int(parse_iso_utc(f"{end}T00:00:00Z"))
        for _label, _start, end in FOLD_WINDOWS
    ]


# --------------------------------------------------------------------------- #
# Read-only loaders (absolute workspace paths; never copied or committed)
# --------------------------------------------------------------------------- #
def _parse_utc_naive(text: str) -> int:
    """``YYYY-MM-DD HH:MM:SS`` (Binance daily metrics, UTC) -> epoch ns."""
    from datetime import datetime, timezone

    dt = datetime.strptime(str(text).strip(), "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    return int(dt.timestamp()) * 1_000_000_000


def load_day_turnover_by_symbol(
    symbols: Optional[Sequence[str]] = None,
    *,
    bars_root: str = BARS_ROOT,
    span_start_day_ns: int,
    span_end_day_ns: int,
) -> dict[str, dict[int, float]]:
    """Per-UTC-day dollar turnover from completed 15m bars (READ-ONLY).

    A day bucket is COMPLETE iff exactly ``BARS_PER_DAY`` (96) completed
    bars close inside it; incomplete days are OMITTED (they become gaps
    downstream -- fail closed, never filled).  Dollar turnover per bar is
    ``close x volume`` with BOTH decoded ``raw i128 / 1e16``.  The day
    bucket of a bar is the UTC day containing its slot
    (``(boundary - 1) // day_ns``), so the ``W`` buckets before a Monday
    00:00:00Z stamp are exactly ``W`` full trading days.
    """
    wanted = [str(s) for s in (symbols or tradeable_universe_symbols())]
    out: dict[str, dict[int, float]] = {}
    for sym in wanted:
        sym_dir = Path(bars_root) / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
        paths = sorted(sym_dir.glob("*.parquet"))
        if not paths:
            raise FileNotFoundError(f"no bar parquets for {sym} under {bars_root}")
        per_day_sum: dict[int, float] = {}
        per_day_count: dict[int, int] = {}
        for path in paths:
            table = pq.read_table(path, columns=["ts_event", "close", "volume"])
            n = table.num_rows
            batch = 50_000
            for start in range(0, n, batch):
                chunk = table.slice(start, batch)
                ts_list = chunk.column("ts_event").to_pylist()
                close_col = chunk.column("close")
                vol_col = chunk.column("volume")
                for idx in range(chunk.num_rows):
                    boundary = snap_close_to_boundary(int(ts_list[idx]))
                    day = (boundary - 1) // DAY_NS
                    if day < span_start_day_ns or day > span_end_day_ns:
                        continue
                    close = int.from_bytes(
                        bytes(close_col[idx].as_py()), "little", signed=True
                    ) / PRICE_DECODE_DIVISOR
                    volume = int.from_bytes(
                        bytes(vol_col[idx].as_py()), "little", signed=True
                    ) / PRICE_DECODE_DIVISOR
                    if not (close > 0.0) or volume < 0.0:
                        raise ValueError(f"{sym}: non-positive close / negative volume")
                    per_day_sum[day] = per_day_sum.get(day, 0.0) + close * volume
                    per_day_count[day] = per_day_count.get(day, 0) + 1
        days: dict[int, float] = {}
        for day in sorted(per_day_sum):
            if per_day_count.get(day, 0) == BARS_PER_DAY:
                days[int(day)] = per_day_sum[day]
        out[sym] = days
    return out


def load_bars_for_plugin(
    symbols: Sequence[str],
    instants_ns: Sequence[int],
    *,
    bars_root: str = BARS_ROOT,
    pre_bars: int = 1,
    post_bars: int = 4,
) -> dict[str, tuple[Any, ...]]:
    """Completed bars around the schedule instants, as plugin Bar tuples.

    The plugin consumes bars ONLY as execution/valuation events (fills at
    the slot-open at/after decision + 15m; marks at the covering bar
    open), so the audit loader selects the loader-decoded completed bars
    around the frozen schedule's instants -- never as decision inputs.
    """
    from research.v11.families.oilever_delev.strategy import Bar

    out: dict[str, tuple[Any, ...]] = {}
    for sym in [str(s) for s in symbols]:
        sym_dir = Path(bars_root) / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
        paths = sorted(sym_dir.glob("*.parquet"))
        if not paths:
            raise FileNotFoundError(f"no bar parquets for {sym} under {bars_root}")
        needed: set[int] = set()
        for instant in instants_ns:
            for k in range(-int(pre_bars), int(post_bars) + 1):
                needed.add(int(instant) + k * BAR_INTERVAL_NS)
        bars: list[Bar] = []
        seen: set[int] = set()
        for path in paths:
            table = pq.read_table(
                path, columns=["ts_event", "open", "high", "low", "close"]
            )
            n = table.num_rows
            batch = 50_000
            for start in range(0, n, batch):
                chunk = table.slice(start, batch)
                ts_list = chunk.column("ts_event").to_pylist()
                for idx in range(chunk.num_rows):
                    ts = int(ts_list[idx])
                    boundary = snap_close_to_boundary(ts)
                    if boundary not in needed or ts in seen:
                        continue
                    seen.add(ts)
                    bars.append(
                        Bar(
                            ts_event_ns=ts,
                            open=decode_i128_price(chunk.column("open")[idx].as_py())[0],
                            high=decode_i128_price(chunk.column("high")[idx].as_py())[0],
                            low=decode_i128_price(chunk.column("low")[idx].as_py())[0],
                            close=decode_i128_price(chunk.column("close")[idx].as_py())[0],
                        )
                    )
        bars.sort(key=lambda b: b.ts_event_ns)
        out[sym] = tuple(bars)
    return out


def load_oi_by_symbol(
    symbols: Optional[Sequence[str]] = None,
    *,
    root: str = OI_CONSOLIDATED_ROOT,
) -> dict[str, tuple[tuple[int, float], ...]]:
    """Daily consolidated OI rows per symbol: ``[(ts_ns, open_interest)]``.

    Read-only; rows strictly increasing; availability = the snapshot stamp.
    """
    wanted = [str(s) for s in (symbols or tradeable_universe_symbols())]
    out: dict[str, tuple[tuple[int, float], ...]] = {}
    for sym in wanted:
        path = Path(root) / f"{sym}_oi.parquet"
        table = pq.read_table(path)
        times = table.column("create_time").to_pylist()
        values = table.column("sum_open_interest").to_pylist()
        rows = sorted((_parse_utc_naive(t), float(v)) for t, v in zip(times, values))
        seen = [t for t, _ in rows]
        if len(set(seen)) != len(seen):
            raise ValueError(f"{sym}: duplicate OI timestamps after parse")
        out[sym] = tuple(rows)
    return out


def load_marks_and_settlements(
    symbols: Optional[Sequence[str]] = None,
    *,
    bundle_label: str = "scan_2026",
) -> tuple[dict[str, tuple[tuple[int, float], ...]], dict[str, tuple[dict[str, Any], ...]]]:
    """Mark snapshots and native settlements from one funding bundle.

    Marks: the ``markPrice`` field of EVERY native settlement row (the
    A9-F staged mark root); availability = the settlement stamp.
    Settlements: ``{"publish_ts_ns", "value"}`` rows (COST ONLY inputs).
    """
    root = dict(FUNDING_BUNDLES)[bundle_label]
    wanted = [str(s) for s in (symbols or tradeable_universe_symbols())]
    marks: dict[str, tuple[tuple[int, float], ...]] = {}
    settlements: dict[str, tuple[dict[str, Any], ...]] = {}
    for sym in wanted:
        path = Path(root) / sym / "funding.json"
        if not path.exists():
            marks[sym] = ()
            settlements[sym] = ()
            continue
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        mark_rows: list[tuple[int, float]] = []
        settle_rows: list[dict[str, Any]] = []
        for row in payload.get("rows") or []:
            ts_ms = row.get("fundingTime")
            rate = row.get("fundingRate")
            mark = row.get("markPrice")
            if ts_ms is None or rate is None:
                raise ValueError(f"{sym}: funding row missing fundingTime/rate")
            stamp_ns = int(ts_ms) * 1_000_000
            settle_rows.append({"publish_ts_ns": stamp_ns, "value": float(rate)})
            if mark is None:
                raise ValueError(f"{sym}: funding row missing markPrice (mark root)")
            mark_rows.append((stamp_ns, float(mark)))
        settle_rows.sort(key=lambda r: r["publish_ts_ns"])
        mark_rows.sort(key=lambda r: r[0])
        if len({t for t, _ in mark_rows}) != len(mark_rows):
            raise ValueError(f"{sym}: duplicate mark/settlement stamps")
        marks[sym] = tuple(mark_rows)
        settlements[sym] = tuple(settle_rows)
    return marks, settlements


@dataclass(frozen=True)
class OitdSnapshotData:
    """The injected observable bundle for the frozen arms (read-only)."""

    day_turnover_by_symbol: dict[str, dict[int, float]]
    bars_by_symbol: dict[str, tuple[Any, ...]]
    oi_by_symbol: dict[str, tuple[tuple[int, float], ...]]
    mark_by_symbol: dict[str, tuple[tuple[int, float], ...]]
    settlements_by_symbol: dict[str, tuple[dict[str, Any], ...]]
    tick_sizes: dict[str, float]
    turnover_span_days: tuple[int, int]


def load_snapshot_data(
    *,
    symbols: Optional[Sequence[str]] = None,
    bundle_label: str = "scan_2026",
    turnover_margin_days: int = 1,
) -> OitdSnapshotData:
    """Load the full read-only snapshot bundle the three arms consume.

    Turnover day buckets span the 56d neighbour window before the first
    stamp through the last stamp's bucket (plus a declared margin).  Bars
    are the execution/valuation windows around the schedule stamps
    (context-only benchmark included; never a candidate).
    """
    universe = tuple(symbols) if symbols else tradeable_universe_symbols()
    instants = stamp_calendar()
    # The fold-terminal force-flat instants (frozen A3 vocabulary): the
    # execution/valuation windows must also cover them so the cost-feasibility
    # gate can price the boundary flat transitions.
    fold_ends = fold_end_instants()
    first_day = int(instants[0]) // DAY_NS
    last_day = int(instants[-1]) // DAY_NS
    span_start = first_day - 56 - int(turnover_margin_days)
    span_end = last_day + int(turnover_margin_days)
    day_turnover = load_day_turnover_by_symbol(
        universe, span_start_day_ns=span_start, span_end_day_ns=span_end
    )
    bars = load_bars_for_plugin(
        set(universe) | {BENCHMARK_SYMBOL}, list(instants) + list(fold_ends)
    )
    oi = load_oi_by_symbol(universe)
    marks, settlements = load_marks_and_settlements(
        universe, bundle_label=bundle_label
    )
    ticks = load_tick_sizes(set(universe) | {BENCHMARK_SYMBOL})
    return OitdSnapshotData(
        day_turnover_by_symbol=day_turnover,
        bars_by_symbol=bars,
        oi_by_symbol=oi,
        mark_by_symbol=marks,
        settlements_by_symbol=settlements,
        tick_sizes=ticks,
        turnover_span_days=(span_start, span_end),
    )


def build_plugins(
    *,
    data: OitdSnapshotData,
    symbols: Optional[Sequence[str]] = None,
) -> dict[str, OitdPlugin]:
    """Build the three frozen arm plugins on the read-only snapshot.

    The causal control instance is constructed WITHOUT the OI/mark bundles
    (its numerator is deleted by construction and its signal layer refuses
    them outright).
    """
    universe = tuple(symbols) if symbols else tradeable_universe_symbols()
    plugins: dict[str, OitdPlugin] = {}
    for arm_id in ARM_IDS:
        is_control = arm_id == CONTROL_ARM
        plugins[arm_id] = OitdPlugin(
            arm_id=arm_id,
            day_turnover_by_symbol=dict(data.day_turnover_by_symbol),
            bars_by_symbol=dict(data.bars_by_symbol),
            oi_by_symbol=None if is_control else dict(data.oi_by_symbol),
            mark_by_symbol=None if is_control else dict(data.mark_by_symbol),
            settlements_by_symbol=dict(data.settlements_by_symbol),
            tick_sizes=dict(data.tick_sizes),
        )
    return plugins


# --------------------------------------------------------------------------- #
# Evidence builders
# --------------------------------------------------------------------------- #
def evidence_identity() -> dict[str, Any]:
    """Frozen identity payloads + honest recomputed-vs-recorded digest report."""
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        identity = frozen_identity(arm_id)
        arms[arm_id] = {
            "public_payload": identity.public_payload(),
            "matrix_cohort_hint": identity.matrix_cohort_hint,
            "arm_id_declared": identity.arm_id,
            "recorded_config": frozen_arm_config(arm_id),
        }
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "identity",
        "producer_role": PRODUCER_ROLE,
        "digest_function": (
            "research.v11.publication_identity.arm_config_digest("
            "StrategyIdentity(...), arm_id=...)"
        ),
        "arms": arms,
        "digest_report": frozen_arm_digest_report(),
        "recorded_digests": dict(FROZEN_ARM_CONFIG_DIGESTS),
    }


def build_target_records(
    arm_id: str,
    *,
    data: OitdSnapshotData,
    instants: Sequence[int],
) -> list[dict[str, Any]]:
    """The chained hysteresis target schedule of one arm over the stamps."""
    plugin = build_plugins(data=data)[arm_id]
    stress = plugin.baseline_stress()
    universe = plugin.tradeable_universe()
    return [
        plugin.targets_at(int(stamp), universe=universe, stress=stress)
        for stamp in sorted(int(v) for v in instants)
    ]


def canonical_sha256(payload: Any) -> str:
    """Canonical-JSON sha256 (volatile metadata excluded by construction)."""
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evidence_schedule_only_real(
    *,
    data: Optional[OitdSnapshotData] = None,
) -> dict[str, Any]:
    """Schedule-only feasibility on the REAL snapshot for all three arms.

    Per arm: 52 decision stamps, pinned F0/F1/F2 folds (declared and
    purged counts), hysteresis carried-stamp count, per-stamp breadth and
    side sizes, cap/gross invariants, one-way turnover estimates, signal
    availability, AND the frozen ``research.v11.cost_feasibility`` gate
    (base <= 8%/yr and stressed <= 12%/yr of average gross, decisions per
    365d <= 60, median intended holding >= 3d, max symbol turnover share
    <= 0.25).  The gate artifacts carry each fold-terminal force-flat as a
    ``FORCED_FLAT`` decision (frozen A3 vocabulary: counted separately,
    excluded from the per-365d floor).  Decisions, folds, holding, turnover
    and cost estimates ONLY -- no PnL, no returns, no scored metric.
    """
    if data is None:
        data = load_snapshot_data()
    universe = tradeable_universe_symbols()
    plugins = build_plugins(data=data, symbols=universe)
    instants = list(stamp_calendar())
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        plugin = plugins[arm_id]
        stress = plugin.baseline_stress()
        retained = plugin.decision_instants(stress=stress)
        folds = plugin.folds(stress=stress, instants=instants)
        books: list[dict[str, float]] = []
        payload_by_stamp: dict[int, dict[str, Any]] = {}
        carried = 0
        for stamp in retained:
            payload = plugin.targets_at(stamp, universe=universe, stress=stress)
            payload_by_stamp[stamp] = payload
            if payload["carried_forward"]:
                carried += 1
            books.append({str(s): float(w) for s, w in payload["weights"]})
        records = [payload_by_stamp[stamp] for stamp in retained]
        validation = validate_stamp_schedule(records, cap_max=CAP_MAX)
        funding_stamps = {
            sym: tuple(int(r["publish_ts_ns"]) for r in rows)
            for sym, rows in data.settlements_by_symbol.items()
        }
        diagnostics = schedule_diagnostics(
            records, funding_events_by_symbol=funding_stamps
        )
        max_abs = max(
            (max((abs(w) for w in book.values()), default=0.0) for book in books),
            default=0.0,
        )
        max_gross = max(
            (math.fsum(abs(w) for w in book.values()) for book in books), default=0.0
        )
        min_side = min(
            (
                min(
                    sum(1 for w in book.values() if w > 0.0),
                    sum(1 for w in book.values() if w < 0.0),
                )
                for book in books
            ),
            default=0,
        )
        fill_prices: dict[int, dict[str, float]] = {}
        for stamp in retained:
            fills = plugin.fills_at(stamp, symbols=universe, stress=stress)
            fill_prices[stamp] = {
                f.symbol: float(f.price) for f in fills if f.applied and f.price
            }
        availability = {
            stamp: SignalAvailability(
                instant_ns=stamp, available=True, missing_symbols=()
            )
            for stamp in retained
        }
        decisions = {
            stamp: ScheduleDecision(
                instant_ns=stamp, kind=KIND_DISCRETIONARY, weights=book
            )
            for stamp, book in zip(retained, books)
        }
        # Fold-terminal force-flat artifacts (frozen A3 vocabulary): one
        # FORCED_FLAT decision per fold boundary, counted separately from
        # discretionary decisions and excluded from the per-365d floor.  The
        # purge already stripped each fold's trailing stamp, so no book
        # opened inside a fold straddles its boundary; the flat transition
        # itself is the boundary action.  Availability at a boundary records
        # that the signal was computable there (it opens no book); fill
        # prices price the flat transition via the pinned fill convention.
        gate_fold_ends = fold_end_instants()
        gate_instants = sorted(list(retained) + gate_fold_ends)
        for boundary in gate_fold_ends:
            decisions[boundary] = ScheduleDecision(
                instant_ns=boundary, kind=KIND_FORCED_FLAT, weights={}
            )
            availability[boundary] = SignalAvailability(
                instant_ns=boundary, available=True, missing_symbols=()
            )
            fills = plugin.fills_at(boundary, symbols=universe, stress=stress)
            fill_prices[boundary] = {
                f.symbol: float(f.price) for f in fills if f.applied and f.price
            }
        from research.adapter_v10.protocol import SettlementPoint

        settlement_points = {
            sym: tuple(
                SettlementPoint(publish_ts_ns=int(r["publish_ts_ns"]), value=float(r["value"]))
                for r in rows
            )
            for sym, rows in data.settlements_by_symbol.items()
        }
        gate = evaluate_schedule_cost_feasibility(
            ScheduleArtifacts(
                instants_ns=gate_instants,
                decisions=decisions,
                fill_prices=fill_prices,
                settlements=settlement_points,
                cost_model=plugin.cost_model(),
                signal_availability=availability,
                source="research.v13.families.oitd.audits.evidence_schedule_only_real",
            )
        )
        gate_floors = {
            str(f["floor_id"]): {
                "observed": f["observed"],
                "threshold": f["frozen_threshold"],
                "status": f["status"],
            }
            for f in gate.payload.get("floors", ())
        }
        arms[arm_id] = {
            "n_schedule_stamps": len(instants),
            "n_retained_decisions": len(retained),
            "folds": [
                {
                    "label": f.label,
                    "declared": len(f.instants) + plugin.purge_days(),
                    "retained": len(f.instants),
                    "purge_days": f.purge_days,
                    "dropped": f.dropped,
                }
                for f in folds
            ],
            "carried_stamps": carried,
            "n_eligible_min": min(
                p["diagnostics"]["n_eligible"] for p in payload_by_stamp.values()
            ),
            "n_eligible_max": max(
                p["diagnostics"]["n_eligible"] for p in payload_by_stamp.values()
            ),
            "min_side_members_observed": int(min_side),
            "max_abs_weight_observed": round(max_abs, 12),
            "max_gross_observed": round(max_gross, 12),
            # Per-symbol signal coverage at the worst stamp (the honest
            # eligible/universe ratio; a data gap makes one symbol
            # ineligible fail-closed at the first stamp).
            "signal_availability_ratio_min": min(
                p["diagnostics"]["signal_availability_ratio"]
                for p in payload_by_stamp.values()
            ),
            # The frozen floor's own metric: a computable book at >= 95%
            # of the retained decision stamps (here: every stamp).
            "stamps_with_book_ratio": sum(
                1 for p in payload_by_stamp.values()
                if p["weights"]
            ) / float(len(retained)),
            "book_validation": {
                "verdict": validation["verdict"],
                "n_pass": validation["n_pass"],
                "n_fail": validation["n_fail"],
            },
            "schedule_diagnostics": {
                "diagnostics_verdict": diagnostics["verdict"],
                "decision_count": diagnostics["decision_count"],
                "one_way_turnover_total": diagnostics["one_way_turnover"]["total"],
                "one_way_turnover_per_step": diagnostics["one_way_turnover"]["per_step"],
                "median_intended_holding_days": diagnostics["holdings"][
                    "median_holding_days"
                ],
                "n_held_spans": diagnostics["holdings"]["n_spans"],
                "funding_events_while_held": diagnostics["funding_events_while_held"][
                    "events_while_held_total"
                ],
            },
            "cost_gate": {
                "verdict": gate.verdict,
                "forced_flat_decisions": gate.payload["metrics"][
                    "forced_flat_decision_count"
                ]["value"],
                "one_way_turnover_forced_flat": gate.payload["metrics"][
                    "one_way_turnover_forced_flat"
                ]["value"],
                "floors": gate_floors,
            },
        }
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "schedule_only_feasibility_real",
        "producer_role": PRODUCER_ROLE,
        "scored": False,
        "real_pnl": False,
        "window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "universe_size": len(universe),
        "turnover_span_days": list(data.turnover_span_days),
        "arms": arms,
    }


def evidence_drop_one(
    *, data: Optional[OitdSnapshotData] = None
) -> dict[str, Any]:
    """Drop-one diagnostic on the real snapshot (schedule-only, no PnL).

    At every retained stamp the drop-one selection IS the held
    max-|weight| symbol of the baseline book (tie-break ascending name),
    the dropped symbol was actually HELD, the dropped book keeps the
    remaining weights UNCHANGED (no post-score renormalisation), and a
    zero-position book is REFUSED.
    """
    if data is None:
        data = load_snapshot_data()
    universe = tradeable_universe_symbols()
    plugins = build_plugins(data=data, symbols=universe)
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        plugin = plugins[arm_id]
        stress = plugin.baseline_stress()
        retained = plugin.decision_instants(stress=stress)
        checks: list[dict[str, Any]] = []
        for stamp in retained:
            payload = plugin.targets_at(stamp, universe=universe, stress=stress)
            weights = {str(s): float(w) for s, w in payload["weights"]}
            selected = held_max_abs_weight_symbol(weights)
            held = selected is not None and abs(weights.get(selected or "", 0.0)) > 0.0
            weights_unchanged: Optional[bool] = None
            zero_refused = False
            if selected is None:
                zero_refused = True
                try:
                    drop_one_book(weights)
                except EligibilityShortfall:
                    zero_refused = True
                weights_unchanged = True  # nothing held: vacuously unchanged
            else:
                dropped = drop_one_book(weights)
                baseline_remaining = {
                    s: w for s, w in weights.items() if s != selected
                }
                after = {s: w for s, w in dropped["weights"]}
                weights_unchanged = (
                    set(after) == set(baseline_remaining)
                    and all(
                        after[s] == baseline_remaining[s] for s in baseline_remaining
                    )
                )
            checks.append(
                {
                    "stamp": ns_to_iso_utc(stamp),
                    "selected": selected,
                    "held": bool(held),
                    "unheld_never_selected": bool(held or selected is None),
                    "zero_held_book_refused": bool(zero_refused),
                    "dropped_book_weights_unchanged": bool(weights_unchanged),
                }
            )
        arms[arm_id] = {
            "n_stamps": len(retained),
            "n_held_at": sum(1 for c in checks if c["held"]),
            "checks": checks,
        }
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "drop_one_diagnostic",
        "producer_role": PRODUCER_ROLE,
        "scored": False,
        "all_match": all(
            c["held"] and c["unheld_never_selected"] and c["dropped_book_weights_unchanged"]
            for arm in arms.values()
            for c in arm["checks"]
        ),
        "any_zero_held": any(
            c["selected"] is None for arm in arms.values() for c in arm["checks"]
        ),
        "arms": arms,
    }


# --------------------------------------------------------------------------- #
# Frozen family cell matrix (L-V11-1 derivation over the frozen folds)
# --------------------------------------------------------------------------- #
def family_cell_matrix(*, drop_symbol: Optional[str] = None) -> list[StressSpec]:
    """The family's own preregistered stress cells (never the generic superset).

    ``[baseline, stress_fee_x1_5_plus_2_ticks_delay_1, (drop-one),
    dropped-fold]``; the drop-one cell carries the per-arm max-|w| symbol
    when one is supplied.
    """
    cells = [
        StressSpec(
            name="baseline",
            fee_multiplier=1.0,
            tick_slip_ticks=1,
            event_delay_events=0,
            drop_symbols=(),
            dropped_fold_index=None,
        ),
        StressSpec(
            name=STRESS_NAME,
            fee_multiplier=float(STRESS_FEE_MULTIPLIER),
            tick_slip_ticks=1 + int(STRESS_EXTRA_TICKS),
            event_delay_events=int(STRESS_EVENT_DELAY),
            drop_symbols=(),
            dropped_fold_index=None,
        ),
    ]
    if drop_symbol:
        cells.append(
            StressSpec(
                name="drop_one_max_abs_weight",
                fee_multiplier=1.0,
                tick_slip_ticks=1,
                event_delay_events=0,
                drop_symbols=(str(drop_symbol),),
                dropped_fold_index=None,
            )
        )
    cells.append(
        StressSpec(
            name="drop_one_fold",
            fee_multiplier=1.0,
            tick_slip_ticks=1,
            event_delay_events=0,
            drop_symbols=(),
            dropped_fold_index=0,
        )
    )
    return cells


def _dummy_metrics(*, n_positions: int, n_decisions: int) -> dict[str, Any]:
    """Constant, finite, explicitly DUMMY scored-metric-shaped payload.

    NOT strategy PnL: fixed synthetic constants exercising the publication
    gate plumbing only.  ZERO scored metrics are produced by this lane.
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


def run_dummy_dryrun(
    *,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
    data: Optional[OitdSnapshotData] = None,
) -> dict[str, Any]:
    """Dummy publication dry-run per frozen arm into a TEMPORARY ledger.

    For each arm: traverse the adapter primitives on the real staged
    snapshot (identity, cost model, universe, schedule, folds incl. the
    dropped-fold probe, chained targets/fills/marks at the first retained
    stamp, native settlements and the LONG_PAYS_POSITIVE_RATE accrual over
    one held span) -- schedule-only, no PnL; then publish DUMMY finite
    metrics via ``research.v12.accounting.publish_v12_cell`` against the
    FROZEN family cell matrix:

    * zero-position DUMMY payload on the baseline cell -> REFUSED
      (``OBSERVATION`` row); its exact replay is an idempotent skip;
    * an OUT-OF-CONTRACT cell (anchor only) -> REFUSED outside the frozen
      family matrix (``OBSERVATION`` row);
    * held-position DUMMY payload on the frozen stress cell -> ONE
      ``CELL_RESULT`` row (DUMMY constants, never a real scored metric);
      its exact replay is an idempotent skip with ZERO counter delta.
    """
    path = require_temporary_ledger(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if data is None:
        data = load_snapshot_data()
    universe = tradeable_universe_symbols()
    plugins = build_plugins(data=data, symbols=universe)
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        plugin = plugins[arm_id]
        identity = plugin.identity()
        baseline = plugin.baseline_stress()
        stress_cell = family_cell_matrix(drop_symbol=None)[1]
        off_contract_cell = StressSpec(
            name="off_contract_fee_x2",
            fee_multiplier=2.0,
            tick_slip_ticks=1,
            event_delay_events=0,
        )
        contract = freeze_family_cell_contract(
            FAMILY_ID, family_cell_matrix(drop_symbol=None)
        )
        folds = plugin.folds(stress=baseline, instants=list(stamp_calendar()))
        probe_stress = StressSpec(name="drop_one_fold", dropped_fold_index=0)
        folds_with_drop = plugin.folds(
            stress=probe_stress, instants=list(stamp_calendar())
        )
        retained = plugin.decision_instants(stress=baseline)
        stamp = int(retained[0])
        book = plugin.targets_at(stamp, universe=universe, stress=baseline)
        fills = plugin.fills_at(stamp, symbols=universe, stress=baseline)
        marks = plugin.marks_at(universe, stamp)
        settlements = plugin.settlements(universe[0])
        weights = {str(sym): float(w) for sym, w in book["weights"]}
        first_held = sorted(weights)[0]
        held_span = PositionSpan(
            symbol=first_held,
            signed_weight=float(weights[first_held]),
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
        digest = FROZEN_ARM_CONFIG_DIGESTS[identity.arm_id]
        n_decisions = len(retained)

        common = dict(
            strategy_id=identity.strategy_id,
            family=identity.family_id,
            arm_id=identity.arm_id,
            arm_config_digest=str(digest),
            window_start_iso=identity.window_start_iso,
            window_end_iso=identity.window_end_iso,
            ledger_path=path,
            family_contract_cells=contract,
        )
        zero_metrics = _dummy_metrics(n_positions=0, n_decisions=n_decisions)
        held_metrics = _dummy_metrics(
            n_positions=len(weights), n_decisions=n_decisions
        )
        refused = publish_v12_cell(
            stress_signature=baseline.signature(),
            scored_metrics=zero_metrics,
            **common,
        )
        refused_replay = publish_v12_cell(
            stress_signature=baseline.signature(),
            scored_metrics=zero_metrics,
            **common,
        )
        # The out-of-contract refusal is a FAMILY-level probe of the frozen
        # cell matrix (L-V11-1); it is exercised once, on the anchor arm --
        # the other arms inherit the same frozen matrix.
        if arm_id == ANCHOR_ARM:
            off_contract = publish_v12_cell(
                stress_signature=off_contract_cell.signature(),
                scored_metrics=held_metrics,
                result_sha256=canonical_sha256(dict(held_metrics)),
                **common,
            )
            off_contract_stage = off_contract["stage"]
            off_contract_refused = bool(
                any(
                    REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT in str(r)
                    for r in off_contract["reasons"]
                )
                or off_contract["stage"] == STAGE_IDEMPOTENT_REPLAY
            )
            off_contract_reason = (
                off_contract["reasons"][0] if off_contract["reasons"] else ""
            )
        else:
            off_contract_stage = "NOT_PROBED_ANCHOR_ONLY"
            off_contract_refused = True
            off_contract_reason = ""
        before = v12_denominator_view(path)
        published = publish_v12_cell(
            stress_signature=stress_cell.signature(),
            scored_metrics=held_metrics,
            result_sha256=canonical_sha256(dict(held_metrics)),
            **common,
        )
        after = v12_denominator_view(path)
        replay = publish_v12_cell(
            stress_signature=stress_cell.signature(),
            scored_metrics=held_metrics,
            result_sha256=canonical_sha256(dict(held_metrics)),
            **common,
        )
        final = v12_denominator_view(path)
        zero_enforced = refused["stage"] == STAGE_REFUSED and any(
            REFUSED_ZERO_POSITIONS in str(r) for r in refused["reasons"]
        )
        arms[arm_id] = {
            "adapter_traversal": {
                "strategy_id": identity.strategy_id,
                "arm_config_id": identity.arm_config_id,
                "n_universe": len(universe),
                "n_schedule_instants": len(stamp_calendar()),
                "n_retained_decisions": n_decisions,
                "n_folds": len(folds),
                "fold_labels": [f.label for f in folds],
                "dropped_fold_accepted": any(f.dropped for f in folds_with_drop),
                "first_stamp_book_symbols": len(weights),
                "n_fills_applied": sum(1 for f in fills if f.applied),
                "first_stamp_mark_finite": all(
                    v is not None and math.isfinite(float(v)) for v in marks.values()
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
            "zero_position_refused": bool(
                zero_enforced or refused["stage"] == STAGE_IDEMPOTENT_REPLAY
            ),
            "zero_position_replay_stage": refused_replay["stage"],
            "out_of_contract_stage": off_contract_stage,
            "out_of_contract_reason": off_contract_reason,
            "out_of_contract_refused": bool(off_contract_refused),
            "dummy_publish_stage": published["stage"],
            "counter_delta_on_publish": {
                "published": after["published"] - before["published"],
                "observed": after["observed"] - before["observed"],
            },
            "replay_stage": replay["stage"],
            "replay_idempotent": bool(replay["stage"] == STAGE_IDEMPOTENT_REPLAY),
            "counter_delta_on_replay": {
                "published": final["published"] - after["published"],
                "observed": final["observed"] - after["observed"],
            },
            "dummy_metrics_kind": DRYRUN_DUMMY_METRICS_KIND,
        }
    view = v12_denominator_view(path)
    n_arms = len(ARM_IDS)
    expected_observed = n_arms + 1  # one zero-position refusal per arm + one off-contract
    if view["published"] != n_arms or view["observed"] != expected_observed:
        raise ContractViolation(
            "dry-run ledger must hold exactly one DUMMY cell row per arm, one "
            f"zero-position refusal per arm and one off-contract refusal; got {view}"
        )
    state = read_v12_ledger(path)
    row_types = [str(row["row_type"]) for row in state["rows"]]
    if row_types.count(ROW_TYPE_CELL_RESULT) != n_arms or row_types.count(
        ROW_TYPE_OBSERVATION
    ) != expected_observed:
        raise ContractViolation("dry-run ledger row types drifted")
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "dummy_publication_dryrun",
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
            and a["out_of_contract_refused"]
            and a["dummy_publish_stage"] in (STAGE_PUBLISHED, STAGE_IDEMPOTENT_REPLAY)
            and a["replay_idempotent"]
            and a["counter_delta_on_replay"] == {"published": 0, "observed": 0}
            for a in arms.values()
        ),
    }


__all__ = [
    "AUDITS_SCHEMA",
    "DEFAULT_LEDGER_PATH",
    "DRYRUN_DUMMY_METRICS_KIND",
    "OitdSnapshotData",
    "PRODUCER_ROLE",
    "build_plugins",
    "build_target_records",
    "canonical_sha256",
    "evidence_drop_one",
    "evidence_identity",
    "evidence_schedule_only_real",
    "family_cell_matrix",
    "load_bars_for_plugin",
    "load_day_turnover_by_symbol",
    "load_marks_and_settlements",
    "load_oi_by_symbol",
    "load_snapshot_data",
    "require_temporary_ledger",
    "run_dummy_dryrun",
    "tradeable_universe_symbols",
]
