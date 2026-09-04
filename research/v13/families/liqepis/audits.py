"""Audit-only evidence builders for the frozen LIQEPIS family (V13 I lane).

SCOPE BOUNDARY: this module computes NO PnL, no returns and no scored
metric on real data.  Every real-data output is a field verification, a
count, a timestamp comparison, a schedule verdict, a turnover/holding
estimate or a sha256 equality.  Publication-path exercises use explicitly
DUMMY constant metrics into fail-closed namespaced temporary ledgers only.

All raw data are READ-ONLY workspace files at fixed absolute paths, never
copied or committed (PLAN_crypto.md section 7):

* completed 15m bars -- ``/Users/hoangminhlong/my-quantitative/
  catalog_live_crypto/data/binance_bar`` (Nautilus layout; ``ts_event`` is
  the raw bar-close stamp in ns, forward-snapped to the 15m boundary it
  terminates; prices and volumes decode as raw i128 / 1e16, A9-F F7).

This is a BARS-ONLY family: no OI, mark-price or funding-rate field enters
any signal (proposal item 10); funding is exercised only through injected
synthetic settlements in the temporary-ledger dry-run and in the
funding-mirror checks, never read from a signal path.

Evidence builders (each returns a JSON-safe payload):

* :func:`evidence_identity` -- frozen identity payloads + the recomputed
  vs recorded per-arm ``arm_config_digest`` report;
* :func:`evidence_schedule_feasibility` -- schedule-only feasibility on the
  REAL snapshot: decisions per fold, purged stamps, per-stamp eligibility
  and refusals, cap/gross invariants, one-way turnover estimates, holding
  durations (NO PnL, no cost numbers);
* :func:`evidence_double_generation` -- the full effective-schedule target
  generation for all three arms computed twice; byte-identical canonical
  JSON (sha256 equality);
* :func:`evidence_drop_one` -- the pinned drop-one diagnostic on the real
  anchor schedule (held max-|weight| symbol, proven held);
* :func:`run_dummy_publication_dryrun` -- dummy publication dry-run into a
  namespaced TEMPORARY ledger: publish (DUMMY constants), zero-position
  refusal, out-of-contract refusal, exact replay with ZERO counter delta.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import numpy as np
import pyarrow.parquet as pq

from research.adapter_v10.protocol import (
    ContractViolation,
    PositionSpan,
    StressSpec,
)
from research.v12.data_contract import (
    BARS_ROOT,
    REQUIRED_SYMBOLS,
)
from research.v12.feasibility import (
    VERDICT_PASS,
    schedule_diagnostics,
    validate_stamp_schedule,
)
from research.v13.families.liqepis.frozen_identity import (
    LIQEPIS_ARM_CONFIG_DIGESTS,
    frozen_arm_config,
    frozen_arm_digest_report,
    frozen_identity,
)
from research.v13.families.liqepis.plugin import LiqepisPlugin, family_stress_cell
from research.v13.families.liqepis.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    BAR_INTERVAL_NS,
    BENCHMARK_SYMBOL,
    CAP_MAX,
    DAY_NS,
    FIRST_STAMP_ISO,
    FOLD_WINDOWS,
    FOLDS_CONTRACT,
    HOLDING_DAYS,
    LEGS_PER_SIDE,
    MIN_ELIGIBLE,
    PER_NAME_WEIGHT,
    PURGE_DAYS,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    FusionBarSeries,
    build_drop_one_book,
    compute_targets_at,
    effective_schedule,
    fold_assignments,
    fold_end_ns,
    force_flat_span_end,
    iso_utc,
    parse_iso_utc,
    schedule_drop_one,
    series_from_rows,
    stamp_calendar,
)

AUDITS_SCHEMA = "v13i.liqepis.audits.v1"
PRODUCER_ROLE = "I-LIQEPIS"

#: Price/quantity decode divisor (A9-F F7, binding): raw i128 / 1e16.
PRICE_DECODE_DIVISOR = 1e16

DEFAULT_LEDGER_PATH = "/tmp/v13i_liqepis_dryrun/dryrun_liqepis.jsonl"


# --------------------------------------------------------------------------- #
# Read-only loaders (absolute workspace paths; never copied or committed)
# --------------------------------------------------------------------------- #
def decode_i128(raw: bytes) -> tuple[float, int]:
    """Decode one Nautilus i128 price/quantity column value: ``raw / 1e16``."""
    raw_int = int.from_bytes(bytes(raw), "little", signed=True)
    decoded = raw_int / PRICE_DECODE_DIVISOR
    if not math.isfinite(decoded) or decoded <= 0.0:
        raise ValueError(f"i128 decode produced a non-positive value: {decoded}")
    return decoded, raw_int


def snap_close_to_boundary(ts: int) -> int:
    """Forward-snap a raw bar-close stamp to the 15m boundary it terminates.

    Binance kline closes sit ~1ms before the boundary they terminate; the
    snapped boundary is the PIT slot identity (v12 data contract).
    """
    remainder = int(ts) % BAR_INTERVAL_NS
    forward = (BAR_INTERVAL_NS - remainder) % BAR_INTERVAL_NS
    if forward < BAR_INTERVAL_NS // 2:
        return int(ts) + forward
    return int(ts)  # unexpected post-boundary stamp: keep raw


def _snap_close_to_boundary_vectorized(ts: "np.ndarray") -> "np.ndarray":
    """Vectorized :func:`snap_close_to_boundary` over an int64 array."""
    remainder = ts % BAR_INTERVAL_NS
    forward = (BAR_INTERVAL_NS - remainder) % BAR_INTERVAL_NS
    return np.where(forward < BAR_INTERVAL_NS // 2, ts + forward, ts)


def load_fusion_series(
    symbols: Optional[Sequence[str]] = None,
    *,
    bars_root: str = BARS_ROOT,
    start_ns: Optional[int] = None,
    end_ns: Optional[int] = None,
) -> dict[str, FusionBarSeries]:
    """Boundary-indexed fusion bar series per symbol (read-only snapshot).

    Reads ``ts_event``/``close``/``volume`` straight from the Nautilus
    parquet, snaps raw close stamps forward to the 15m boundary they
    terminate, decodes ``raw i128 / 1e16`` and keeps rows whose snapped
    boundary lies in ``[start_ns, end_ns]`` (default: the full file).
    Availability = the bar's close boundary (crypto_compat semantics).
    """
    wanted = [str(s) for s in (symbols or REQUIRED_SYMBOLS)]
    out: dict[str, FusionBarSeries] = {}
    for sym in wanted:
        sym_dir = Path(bars_root) / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
        paths = sorted(p for p in sym_dir.glob("*.parquet"))
        if not paths:
            raise FileNotFoundError(f"no bar parquets for {sym} under {bars_root}")
        rows: list[tuple[int, int, float, float]] = []
        seen: set[int] = set()
        for path in paths:
            table = pq.read_table(path, columns=["ts_event", "close", "volume"])
            ts = np.asarray(table.column("ts_event").to_pylist(), dtype=np.int64)
            boundary = _snap_close_to_boundary_vectorized(ts)
            mask = np.ones(boundary.shape[0], dtype=bool)
            if start_ns is not None:
                mask &= boundary >= int(start_ns)
            if end_ns is not None:
                mask &= boundary <= int(end_ns)
            close_col = table.column("close").to_pylist()
            volume_col = table.column("volume").to_pylist()
            for idx in np.nonzero(mask)[0]:
                b = int(boundary[idx])
                if b in seen:
                    raise ContractViolation(
                        f"{sym}: two bar closes snap to boundary {b}"
                    )
                seen.add(b)
                close, _ci = decode_i128(close_col[idx])
                volume, _vi = decode_i128(volume_col[idx])
                rows.append((b, b, close, volume))
        rows.sort(key=lambda r: r[0])
        out[sym] = series_from_rows(rows)
    return out


def tradeable_universe_symbols() -> tuple[str, ...]:
    """The 19 tradeable names: staged symbols minus the benchmark leg."""
    return tuple(sorted(set(REQUIRED_SYMBOLS) - {BENCHMARK_SYMBOL}))


def _schedule_series_inputs():
    """Shared read-only inputs for the schedule evidence builders.

    Bars cover the frozen window plus the neighbour warmup head (56d before
    the first stamp) so every stamp's 5376-slot formation window resolves.
    """
    universe = tradeable_universe_symbols()
    calendar = stamp_calendar()
    effective, purged_by_fold = effective_schedule(calendar)
    first_stamp = parse_iso_utc(FIRST_STAMP_ISO)
    series = load_fusion_series(
        sorted(set(universe) | {BENCHMARK_SYMBOL}),
        start_ns=first_stamp - 56 * DAY_NS,
        end_ns=parse_iso_utc(WINDOW_END_ISO),
    )
    return universe, calendar, effective, purged_by_fold, series


def build_plugins(
    *,
    symbols: Optional[Sequence[str]] = None,
    series_by_symbol: Optional[Mapping[str, FusionBarSeries]] = None,
) -> dict[str, LiqepisPlugin]:
    """Build the three frozen arm plugins on the read-only staged snapshot.

    Bars cover the frozen window plus the neighbour warmup head (56d before
    the first stamp); tick sizes are the schedule-only stub (cost arithmetic
    is exercised on synthetic injections only, never scored).  Callers that
    already hold loaded series may inject them to avoid a re-read.
    """
    universe = tuple(symbols) if symbols else tradeable_universe_symbols()
    first_stamp = parse_iso_utc(FIRST_STAMP_ISO)
    needed = sorted(set(universe) | {BENCHMARK_SYMBOL})
    if series_by_symbol is None:
        series_by_symbol = load_fusion_series(
            needed,
            start_ns=first_stamp - 56 * DAY_NS,
            end_ns=parse_iso_utc(WINDOW_END_ISO),
        )
    plugins: dict[str, LiqepisPlugin] = {}
    for arm_id in ARM_IDS:
        plugins[arm_id] = LiqepisPlugin(
            arm_id=arm_id,
            bars_by_symbol={
                sym: s for sym, s in series_by_symbol.items() if sym in set(needed)
            },
            tick_sizes={sym: 0.01 for sym in needed},
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
        "digest_provenance": (
            "the V13 selection freeze records no per-arm digests; this lane "
            "recorded the digests computed from the frozen identities at "
            "implementation time, BEFORE any scored metric exists for any "
            "V13 cell (V12 freeze-v2 pre-scored-metric convention)"
        ),
        "arms": arms,
        "digest_report": report,
        "recorded_digests": dict(LIQEPIS_ARM_CONFIG_DIGESTS),
        "all_match": bool(all_match),
    }


def build_schedule_records(
    arm_id: str,
    *,
    series_by_symbol: Mapping[str, FusionBarSeries],
    universe: Sequence[str],
    instants: Sequence[int],
) -> list[dict[str, Any]]:
    """The effective (purged) target-book schedule of one arm (schedule-only)."""
    records: list[dict[str, Any]] = []
    for stamp in instants:
        book = compute_targets_at(
            arm_id,
            bars_by_symbol=series_by_symbol,
            stamp_ns=int(stamp),
            universe=universe,
        )
        records.append(
            {
                "decision_ns": int(stamp),
                "arm_id": str(arm_id),
                "status": str(book["status"]),
                "weights": [[sym, float(w)] for sym, w in book["weights"]],
                "diagnostics": book["diagnostics"],
            }
        )
    return records


def evidence_schedule_feasibility() -> dict[str, Any]:
    """Schedule-only feasibility on the REAL snapshot (no PnL, no costs).

    Per arm: per-fold decision counts, purged stamps, eligibility/refusals,
    cap/gross invariants, one-way turnover estimates and holding durations
    via the inherited A4 validator/diagnostics (counts and durations only).
    """
    universe, calendar, effective, purged_by_fold, series = _schedule_series_inputs()
    assignments = fold_assignments(calendar)
    fold_counts = {label: len(members) for _i, label, members, _p in assignments}
    stamp_fold_label = {
        int(stamp): label
        for _i, label, members, _p in assignments
        for stamp in members
    }
    arms: dict[str, Any] = {}
    all_pass = True
    for arm_id in ARM_IDS:
        records = build_schedule_records(
            arm_id, series_by_symbol=series, universe=universe, instants=effective
        )
        verdict = validate_stamp_schedule(list(records), legs_per_side=LEGS_PER_SIDE)
        all_pass = all_pass and verdict["verdict"] == VERDICT_PASS
        eligible = [rec["diagnostics"]["n_eligible"] for rec in records]
        refused_total = sum(int(rec["diagnostics"]["n_refused"]) for rec in records)
        max_abs = max(rec["diagnostics"]["max_abs_weight"] for rec in records)
        gross_max = max(rec["diagnostics"]["gross_after_scale"] for rec in records)
        diagnostics = schedule_diagnostics(list(records))
        per_fold: dict[str, int] = {label: 0 for label, _s, _e in FOLD_WINDOWS}
        for record in records:
            label = stamp_fold_label[int(record["decision_ns"])]
            per_fold[label] += 1
        arms[arm_id] = {
            "verdict": verdict["verdict"],
            "n_fail": verdict["n_fail"],
            "failing_stamps": verdict["failing_stamps"][:5],
            "decisions_total": len(records),
            "decisions_per_fold": per_fold,
            "n_eligible_min": int(min(eligible)),
            "n_eligible_max": int(max(eligible)),
            "refused_symbol_stamps_total": int(refused_total),
            "max_abs_weight_observed": float(max_abs),
            "max_gross_observed": float(gross_max),
            "cap_max": float(CAP_MAX),
            "one_way_turnover_total": diagnostics["one_way_turnover"]["total"],
            "one_way_turnover_mean_per_step": round(
                math.fsum(diagnostics["one_way_turnover"]["per_step"])
                / max(1, len(diagnostics["one_way_turnover"]["per_step"])),
                12,
            ),
            "n_hold_spans": diagnostics["holdings"]["n_spans"],
            "median_holding_days": diagnostics["holdings"]["median_holding_days"],
        }
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "schedule_feasibility_real_snapshot",
        "producer_role": PRODUCER_ROLE,
        "authority_note": (
            "independent re-run via research.v12.feasibility (A4 validator, "
            "legs_per_side=6); counts, durations and turnover estimates "
            "only -- NO PnL, no returns, no cost numbers"
        ),
        "window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "folds_contract": FOLDS_CONTRACT,
        "n_schedule_stamps": len(calendar),
        "purged_stamps_by_fold": {
            label: [iso_utc(t) for t in stamps]
            for label, stamps in sorted(purged_by_fold.items())
        },
        "n_effective_stamps": len(effective),
        "fold_member_counts": fold_counts,
        "universe_size": len(universe),
        "min_eligible": int(MIN_ELIGIBLE),
        "purge_days": int(PURGE_DAYS),
        "legs_per_side": int(LEGS_PER_SIDE),
        "designed_per_name_weight": round(PER_NAME_WEIGHT, 12),
        "arms": arms,
        "all_arms_pass": bool(all_pass),
        "schedule_only": True,
        "pnl_computed": False,
    }


def _canonical_sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evidence_double_generation() -> dict[str, Any]:
    """Generate the full effective-schedule targets twice; byte-identical JSON.

    The records carry NO volatile metadata (no wall-clock stamps, no
    environment data), so the whole canonical JSON must be identical.
    """
    universe, _calendar, effective, _purged, series = _schedule_series_inputs()
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        first = build_schedule_records(
            arm_id, series_by_symbol=series, universe=universe, instants=effective
        )
        second = build_schedule_records(
            arm_id, series_by_symbol=series, universe=universe, instants=effective
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
        "volatile_metadata_excluded_note": (
            "records carry no volatile metadata at all (no wall-clock or "
            "environment fields), so the whole canonical payload must match"
        ),
        "arms": arms,
        "all_byte_identical": all(a["byte_identical"] for a in arms.values()),
    }


def evidence_drop_one() -> dict[str, Any]:
    """The pinned drop-one diagnostic on the real anchor schedule.

    The dropped symbol must be the HELD symbol with the largest absolute
    weight at the selected stamp (ties -> lexicographically smallest symbol
    id; stamp ties -> earliest), selected per :data:`DROP_ONE_PIN`; the
    renormalized 5v5 book at 1/10 must preserve gross 1.0.
    """
    universe, _calendar, effective, _purged, series = _schedule_series_inputs()
    records = build_schedule_records(
        ANCHOR_ARM, series_by_symbol=series, universe=universe, instants=effective
    )
    selection = schedule_drop_one(records)
    at_stamp = next(
        r for r in records if int(r["decision_ns"]) == int(selection["stamp_ns"])
    )
    weights = {str(sym): float(w) for sym, w in at_stamp["weights"]}
    dropped_book = build_drop_one_book(weights, dropped_symbol=selection["symbol"])
    dropped_side_long = weights[selection["symbol"]] > 0.0
    n_dropped_side = (
        len(dropped_book["longs"]) if dropped_side_long else len(dropped_book["shorts"])
    )
    n_other_side = (
        len(dropped_book["shorts"]) if dropped_side_long else len(dropped_book["longs"])
    )
    side_weights = [
        abs(w) for _s, w in dropped_book["weights"]
    ]
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "drop_one_diagnostic",
        "producer_role": PRODUCER_ROLE,
        "rule": selection["pin"],
        "selection": selection,
        "dropped_symbol_held_abs_weight": weights[selection["symbol"]],
        "renormalized_book": {
            "dropped_side": dropped_book["dropped_side"],
            "longs": dropped_book["longs"],
            "shorts": dropped_book["shorts"],
            "per_name_weight_dropped_side": dropped_book[
                "per_name_weight_dropped_side"
            ],
            "per_name_weight_untouched_side": dropped_book[
                "per_name_weight_untouched_side"
            ],
            "gross": dropped_book["gross"],
        },
        "renormalization_ok": bool(
            n_dropped_side == LEGS_PER_SIDE - 1
            and n_other_side == LEGS_PER_SIDE
            and abs(dropped_book["gross"] - 1.0) <= 1e-9
            and max(side_weights) <= CAP_MAX + 1e-12
        ),
        "non_vacuous": bool(
            selection["proven_held"] and abs(weights[selection["symbol"]]) > 1e-9
        ),
    }


# --------------------------------------------------------------------------- #
# Dummy publication dry-run (no real scored metric; temporary ledger only)
# --------------------------------------------------------------------------- #
DRYRUN_DUMMY_METRICS_KIND = "DUMMY_DRYRUN_METRICS"


def _dummy_metrics(*, n_positions: int, n_decisions: int) -> dict[str, Any]:
    """Constant, finite, explicitly DUMMY scored-metric-shaped payload.

    NOT strategy PnL: fixed synthetic constants exercising the publication
    gate plumbing only.  ZERO scored metrics exist anywhere in this lane.
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
    return _canonical_sha256(dict(metrics))


def run_dummy_publication_dryrun(
    *,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
    plugins: Optional[Mapping[str, LiqepisPlugin]] = None,
) -> dict[str, Any]:
    """Dummy publication dry-run per frozen arm into a temporary empty ledger.

    Per arm on the real snapshot: traverse the adapter primitives
    (identity, cost model, universe, schedule incl. purge, folds incl. the
    dropped-fold probe, targets/fills at the first effective stamp,
    force-flat span clamp) -- schedule-only, no PnL; then publish DUMMY
    finite metrics via ``research.v12.accounting.publish_v12_cell``:

    * zero-position DUMMY payload on the baseline cell -> REFUSED
      (``REFUSED_ZERO_POSITIONS``);
    * out-of-contract DUMMY payload on an unknown cell -> REFUSED
      (``REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT``, L-V11-1);
    * held-position DUMMY payload on the family stress cell -> one
      ``CELL_RESULT`` row (DUMMY, never a real scored metric);
    * exact replay of the published trial -> IDEMPOTENT_REPLAY_SKIPPED
      with ZERO counter delta.

    The ledger must end with EXACTLY two refusal rows and one DUMMY cell
    row per arm; any other content fails the dry-run closed.
    """
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

    path = require_temporary_ledger(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if plugins is None:
        plugins = build_plugins()
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        plugin = plugins[arm_id]
        identity = plugin.identity()
        baseline = plugin.baseline_stress()
        stress_cell = family_stress_cell(baseline)
        out_of_contract = StressSpec(
            name="generic_superset_probe_not_in_contract",
            fee_multiplier=2.5,
            tick_slip_ticks=int(baseline.tick_slip_ticks) + 9,
            event_delay_events=int(baseline.event_delay_events) + 4,
        )
        universe = plugin.universe(baseline)
        schedule = plugin.schedule()
        folds = plugin.folds(stress=baseline, instants=list(schedule.instants))
        probe_stress = StressSpec(name="drop_one_fold", dropped_fold_index=0)
        folds_with_drop = plugin.folds(
            stress=probe_stress, instants=list(schedule.instants)
        )
        first_stamp = int(plugin.effective_instants()[0])
        book = plugin.targets_at(first_stamp, universe=universe, stress=baseline)
        fills = plugin.fills_at(
            first_stamp, symbols=sorted(universe)[:2], stress=baseline
        )
        weights = {str(sym): float(w) for sym, w in book["weights"]}
        held_sym = sorted(weights)[0]
        span_end = force_flat_span_end(first_stamp, holding_days=HOLDING_DAYS)
        held_span = PositionSpan(
            symbol=held_sym,
            signed_weight=float(weights[held_sym]),
            start_ns=first_stamp,
            end_ns=span_end,
        )
        n_decisions = len(plugin.effective_instants())
        digest = LIQEPIS_ARM_CONFIG_DIGESTS[identity.arm_id]
        contract = freeze_family_cell_contract(
            identity.family_id, [baseline, stress_cell]
        )

        zero_metrics = _dummy_metrics(n_positions=0, n_decisions=n_decisions)
        held_metrics = _dummy_metrics(
            n_positions=len(weights), n_decisions=n_decisions
        )
        refused = publish_v12_cell(
            strategy_id=identity.strategy_id,
            family=identity.family_id,
            arm_id=identity.arm_id,
            arm_config_digest=str(digest),
            stress_signature=baseline.signature(),
            window_start_iso=identity.window_start_iso,
            window_end_iso=identity.window_end_iso,
            scored_metrics=zero_metrics,
            ledger_path=path,
            family_contract_cells=contract,
        )
        outside = publish_v12_cell(
            strategy_id=identity.strategy_id,
            family=identity.family_id,
            arm_id=identity.arm_id,
            arm_config_digest=str(digest),
            stress_signature=out_of_contract.signature(),
            window_start_iso=identity.window_start_iso,
            window_end_iso=identity.window_end_iso,
            scored_metrics=held_metrics,
            ledger_path=path,
            family_contract_cells=contract,
        )
        published = publish_v12_cell(
            strategy_id=identity.strategy_id,
            family=identity.family_id,
            arm_id=identity.arm_id,
            arm_config_digest=str(digest),
            stress_signature=stress_cell.signature(),
            window_start_iso=identity.window_start_iso,
            window_end_iso=identity.window_end_iso,
            scored_metrics=held_metrics,
            result_sha256=_dummy_result_sha256(held_metrics),
            ledger_path=path,
            family_contract_cells=contract,
        )
        counters_before = v12_denominator_view(path)
        replay = publish_v12_cell(
            strategy_id=identity.strategy_id,
            family=identity.family_id,
            arm_id=identity.arm_id,
            arm_config_digest=str(digest),
            stress_signature=stress_cell.signature(),
            window_start_iso=identity.window_start_iso,
            window_end_iso=identity.window_end_iso,
            scored_metrics=held_metrics,
            result_sha256=_dummy_result_sha256(held_metrics),
            ledger_path=path,
            family_contract_cells=contract,
        )
        counters_after = v12_denominator_view(path)
        zero_refused = refused["stage"] == STAGE_REFUSED and any(
            REFUSED_ZERO_POSITIONS in str(r) for r in refused["reasons"]
        )
        outside_refused = outside["stage"] == STAGE_REFUSED and any(
            REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT in str(r)
            for r in outside["reasons"]
        )
        dummy_ok = published["stage"] in (STAGE_PUBLISHED, STAGE_IDEMPOTENT_REPLAY)
        zero_delta = (
            counters_after["published"] == counters_before["published"]
            and counters_after["observed"] == counters_before["observed"]
            and replay["stage"] == STAGE_IDEMPOTENT_REPLAY
        )
        arms[arm_id] = {
            "adapter_traversal": {
                "strategy_id": identity.strategy_id,
                "arm_config_id": identity.arm_config_id,
                "n_universe": len(universe),
                "n_schedule_stamps": len(schedule.instants),
                "n_effective_stamps": n_decisions,
                "n_folds": len(folds),
                "fold_labels": [f.label for f in folds],
                "fold_members": [len(f.instants) for f in folds],
                "dropped_fold_accepted": any(f.dropped for f in folds_with_drop),
                "first_stamp": iso_utc(first_stamp),
                "first_stamp_book_symbols": len(weights),
                "first_stamp_max_abs_weight": book["diagnostics"]["max_abs_weight"],
                "probe_span_symbol": held_span.symbol,
                "force_flat_span_end_ns": int(span_end),
                "force_flat_within_fold": bool(
                    span_end <= fold_end_ns(first_stamp)
                ),
                "n_fills_applied_probe": sum(1 for f in fills if f.applied),
                "declared_execution_lag": plugin.declared_execution_lag(),
            },
            "zero_position_stage": refused["stage"],
            "zero_position_reason": (
                refused["reasons"][0] if refused["reasons"] else ""
            ),
            "zero_position_refused": bool(zero_refused),
            "out_of_contract_stage": outside["stage"],
            "out_of_contract_reason": (
                outside["reasons"][0] if outside["reasons"] else ""
            ),
            "out_of_contract_refused": bool(outside_refused),
            "dummy_publish_stage": published["stage"],
            "dummy_publish_cell": stress_cell.name,
            "dummy_publish_appended": bool(dummy_ok),
            "replay_stage": replay["stage"],
            "replay_zero_counter_delta": bool(zero_delta),
            "dummy_metrics_kind": DRYRUN_DUMMY_METRICS_KIND,
        }
    view = v12_denominator_view(path)
    expected_refusals = 2 * len(ARM_IDS)
    if view["published"] != len(ARM_IDS) or view["observed"] != expected_refusals:
        raise ContractViolation(
            "dry-run ledger must hold exactly one DUMMY cell row and two "
            f"refusal rows (zero-position + out-of-contract) per arm; got {view}"
        )
    state = read_v12_ledger(path)
    row_types = [str(row["row_type"]) for row in state["rows"]]
    if row_types.count(ROW_TYPE_CELL_RESULT) != len(ARM_IDS) or row_types.count(
        ROW_TYPE_OBSERVATION
    ) != expected_refusals:
        raise ContractViolation("dry-run ledger row types drifted")
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "dummy_publication_dryrun",
        "producer_role": PRODUCER_ROLE,
        "scored": False,
        "real_pnl": False,
        "scored_metrics_computed": 0,
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
            and a["dummy_publish_appended"]
            and a["replay_zero_counter_delta"]
            for a in arms.values()
        ),
    }


def build_all_evidence(out_dir: str | Path) -> dict[str, str]:
    """Run every real-data evidence builder and write JSON artifacts."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    builders = {
        "identity_digest_report.json": evidence_identity,
        "schedule_feasibility.json": evidence_schedule_feasibility,
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
    "DEFAULT_LEDGER_PATH",
    "DRYRUN_DUMMY_METRICS_KIND",
    "PRICE_DECODE_DIVISOR",
    "PRODUCER_ROLE",
    "build_all_evidence",
    "build_schedule_records",
    "decode_i128",
    "evidence_double_generation",
    "evidence_drop_one",
    "evidence_identity",
    "evidence_schedule_feasibility",
    "load_fusion_series",
    "require_temporary_ledger",
    "run_dummy_publication_dryrun",
    "snap_close_to_boundary",
    "tradeable_universe_symbols",
]
