"""Deterministic audit-artifact builders for V11-SEED-LOTTERY-MAX-SKEW.

Produces the three lane deliverables under ``research/audits/v11i/``:

* ``lottery_max_skew_c1_fields.json``  -- C1 field verification of the
  read-only staged inputs this family consumes (bars, funding, tick sizes),
  full history and scored-window scopes, plus the frozen-contract echo with
  the arm_config_digest equality check against ``selection_freeze.json``;
* ``lottery_max_skew_a3_gate.json``    -- the schedule-only cost feasibility
  gate (:mod:`research.v11.cost_feasibility`) run on THIS family's
  deterministic Monday schedule + target books through the generic adapter
  cost arithmetic (no scored outcome series exists in that gate);
* ``lottery_max_skew_a4_dryrun.json``  -- the no-real-PnL exact-arm dry-run
  (:func:`research.v11.exact_arm_dryrun.run_exact_arm_dryrun`) over the
  three frozen arms on SYNTHETIC data through the REAL adapter path, plus
  the v2 arm-identity distinctness block.

Every value is a deterministic function of the staged snapshot; no scored
PnL of the family is computed, exposed or persisted.
"""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import pyarrow.parquet as pq

from research.adapter_v10.hashes import payload_sha256
from research.adapter_v10.protocol import ContractViolation, StressSpec
from research.v11.cost_feasibility import (
    ScheduleArtifacts,
    ScheduleDecision,
    SignalAvailability,
    evaluate_schedule_cost_feasibility,
)
from research.v11.exact_arm_dryrun import run_exact_arm_dryrun
from research.v11.families.lottery_max_skew.data import (
    DEFAULT_CATALOG_ROOT,
    DEFAULT_FUNDING_ROOT,
    BAR_DIR_SUFFIX,
    staged_symbol_names,
)
from research.v11.families.lottery_max_skew.plugin import (
    ANCHOR_ARM,
    ARM_IDS,
    CONTROL_ARM,
    FAMILY_ID,
    NEIGHBOUR_ARM,
    LotteryMaxSkewPlugin,
    build_arm_plugin,
    frozen_identity,
)
from research.v11.families.lottery_max_skew.strategy import (
    BARS_PER_DAY,
    DAY_NS,
    HISTORY_DAYS_REQUIRED,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    day_index,
)
from research.v11.families.lottery_max_skew.synthetic import build_synthetic_bars
from research.v11.publication_identity import arm_config_digest

AUDIT_DIR = Path("research/audits/v11i")
FREEZE_PATH = Path("research/control/v11_run/selection_freeze.json")
SPEC_PATH = (
    Path("research/control/v11_run/selection_freeze_specs")
    / "V11-SEED-LOTTERY-MAX-SKEW.json"
)
PRICE_SCALE = 10**16
#: repository-root anchor so the artifacts can run from any cwd
REPO_ROOT = Path(__file__).resolve().parents[4]

ARTIFACT_C1 = "lottery_max_skew_c1_fields.json"
ARTIFACT_A3 = "lottery_max_skew_a3_gate.json"
ARTIFACT_A4 = "lottery_max_skew_a4_dryrun.json"


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def _utc_date(day: int) -> str:
    import datetime as _dt

    return _dt.datetime.fromtimestamp(
        day * DAY_NS / 1e9, tz=_dt.timezone.utc
    ).date().isoformat()


def _freeze_digests(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    doc = json.loads((repo_root / FREEZE_PATH).read_text())
    return {
        cell["arm_id"]: cell["arm_config_digest"]
        for cell in doc["frozen_cells"]
        if cell["family"] == FAMILY_ID
    }


def _frozen_spec(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    return json.loads((repo_root / SPEC_PATH).read_text())


def _identity_echo() -> dict[str, Any]:
    """Frozen-contract echo + digest equality (fail closed on drift)."""
    frozen = _freeze_digests()
    computed: dict[str, str] = {}
    for arm in ARM_IDS:
        computed[arm] = arm_config_digest(frozen_identity(arm), arm_id=arm)
    return {
        "family_id": FAMILY_ID,
        "strategy_id": frozen_identity(ANCHOR_ARM).strategy_id,
        "window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "arms": ARM_IDS,
        "arm_config_digests": computed,
        "frozen_digests": frozen,
        "digest_equality": {
            arm: computed[arm] == frozen[arm] for arm in ARM_IDS
        },
        "digests_match_freeze": all(computed[arm] == frozen[arm] for arm in ARM_IDS),
    }


# --------------------------------------------------------------------------- #
# C1 -- field verification of the staged inputs (read-only)
# --------------------------------------------------------------------------- #
def _bar_field_stats(
    catalog_root: Path, window_start_ns: int, window_end_ns: int
) -> dict[str, Any]:
    """Per-field verification over every staged bar shard (read-only)."""
    per_symbol: dict[str, Any] = {}
    agg_rows = 0
    agg_window_rows = 0
    negatives = {"open": 0, "close": 0, "quote_volume": 0}
    window_negatives = {"open": 0, "close": 0, "quote_volume": 0}
    null_like = 0
    zero_qv_rows = 0
    window_zero_qv_rows = 0
    non_monotonic_symbols: list[str] = []
    duplicate_stamp_symbols: list[str] = []
    incomplete_day_census: dict[str, list[str]] = {}
    warmup_start_day = day_index(window_start_ns) - HISTORY_DAYS_REQUIRED - 1
    warmup_end_day = day_index(window_end_ns)

    for instrument_id in staged_symbol_names(catalog_root):
        directory = (
            Path(catalog_root) / "data" / "binance_bar" / f"{instrument_id}{BAR_DIR_SUFFIX}"
        )
        files = sorted(directory.rglob("*.parquet"))
        rows: list[tuple[int, float, float, float]] = []
        for path in files:
            table = pq.read_table([str(path)])
            ts = table.column("ts_event").to_pylist()
            opens = table.column("open").to_pylist()
            closes = table.column("close").to_pylist()
            qv = table.column("quote_volume").to_pylist()
            for i in range(len(ts)):
                rows.append(
                    (
                        int(ts[i]),
                        float(int.from_bytes(opens[i], "little", signed=True)) / PRICE_SCALE,
                        float(int.from_bytes(closes[i], "little", signed=True)) / PRICE_SCALE,
                        float(qv[i]),
                    )
                )
        rows.sort(key=lambda r: r[0])
        stamps = [r[0] for r in rows]
        non_monotonic = any(b <= a for a, b in zip(stamps, stamps[1:]))
        duplicates = len(stamps) - len(set(stamps))
        if non_monotonic:
            non_monotonic_symbols.append(instrument_id)
        if duplicates:
            duplicate_stamp_symbols.append(instrument_id)
        window_rows = [r for r in rows if window_start_ns <= r[0] < window_end_ns]
        agg_rows += len(rows)
        agg_window_rows += len(window_rows)
        for r in rows:
            if r[1] < 0.0:
                negatives["open"] += 1
            if r[2] < 0.0:
                negatives["close"] += 1
            if r[3] < 0.0:
                negatives["quote_volume"] += 1
            if r[3] == 0.0:
                zero_qv_rows += 1
        for r in window_rows:
            if r[1] < 0.0:
                window_negatives["open"] += 1
            if r[2] < 0.0:
                window_negatives["close"] += 1
            if r[3] < 0.0:
                window_negatives["quote_volume"] += 1
            if r[3] == 0.0:
                window_zero_qv_rows += 1
        null_like += sum(1 for r in rows if r[1] != r[1] or r[2] != r[2] or r[3] != r[3])
        # incomplete-day census over warmup + scored window
        per_day: dict[int, int] = {}
        for stamp in stamps:
            day = day_index(stamp)
            if warmup_start_day <= day <= warmup_end_day:
                per_day[day] = per_day.get(day, 0) + 1
        bad_days = sorted(d for d, n in per_day.items() if n != BARS_PER_DAY)
        # days with NO row at all inside the census range are missing days
        census_days = range(warmup_start_day, warmup_end_day + 1)
        missing_days = sorted(d for d in census_days if d not in per_day)
        incomplete_day_census[instrument_id] = {
            "incomplete_days": [_utc_date(d) for d in bad_days],
            "absent_days": [_utc_date(d) for d in missing_days],
        }
        per_symbol[instrument_id] = {
            "shards": [str(p.name) for p in files],
            "rows_total": len(rows),
            "rows_in_window": len(window_rows),
            "first_ts_ns": stamps[0],
            "last_ts_ns": stamps[-1],
            "close_min": min(r[2] for r in rows),
            "close_max": max(r[2] for r in rows),
            "close_positive_all": all(r[2] > 0.0 for r in rows),
            "strictly_increasing_ts": not non_monotonic,
            "duplicate_stamps": duplicates,
        }

    return {
        "catalog_root_readonly": str(catalog_root),
        "symbols_scanned": len(per_symbol),
        "rows_total_scope": agg_rows,
        "rows_window_scope": agg_window_rows,
        "null_like_rows": null_like,
        "negative_counts_total": negatives,
        "negative_counts_window": window_negatives,
        "zero_quote_volume_rows_total": zero_qv_rows,
        "zero_quote_volume_rows_window": window_zero_qv_rows,
        "non_monotonic_symbols": sorted(non_monotonic_symbols),
        "duplicate_stamp_symbols": sorted(duplicate_stamp_symbols),
        "incomplete_day_census": incomplete_day_census,
        "per_symbol": per_symbol,
    }


def _funding_field_stats(funding_root: Path, symbols: Sequence[str]) -> dict[str, Any]:
    per_symbol: dict[str, Any] = {}
    for instrument_id in sorted(symbols):
        base = instrument_id[: -len("-PERP.BINANCE")]
        path = funding_root / base / "funding.json"
        if not path.exists():
            per_symbol[instrument_id] = {"present": False}
            continue
        doc = json.loads(path.read_text())
        times = [int(row["fundingTime"]) for row in doc["rows"]]
        rates = [float(row["fundingRate"]) for row in doc["rows"]]
        per_symbol[instrument_id] = {
            "present": True,
            "rows": len(times),
            "first_publish_ms": min(times),
            "last_publish_ms": max(times),
            "duplicate_publish_stamps": len(times) - len(set(times)),
            "rate_min": min(rates),
            "rate_max": max(rates),
            "rates_finite": all(math.isfinite(r) for r in rates),
        }
    return {"funding_root_readonly": str(funding_root), "per_symbol": per_symbol}


def _tick_size_stats(catalog_root: Path, symbols: Sequence[str]) -> dict[str, Any]:
    root = Path(catalog_root) / "data" / "crypto_perpetual"
    out: dict[str, float] = {}
    missing: list[str] = []
    for instrument_id in sorted(symbols):
        directory = root / instrument_id
        files = sorted(directory.rglob("*.parquet")) if directory.exists() else []
        if not files:
            missing.append(instrument_id)
            continue
        row = pq.read_table([str(files[0])]).to_pylist()[0]
        size = float(row["price_increment"])
        if not (math.isfinite(size) and size > 0.0):
            missing.append(instrument_id)
            continue
        out[instrument_id] = size
    return {
        "tick_sizes": out,
        "missing_or_invalid": sorted(missing),
    }


def build_c1_artifact(
    *,
    catalog_root: Path = DEFAULT_CATALOG_ROOT,
    funding_root: Path = DEFAULT_FUNDING_ROOT,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    """Full C1 field-verification payload (deterministic, read-only)."""
    import datetime as _dt

    window_start_ns = int(
        _dt.datetime(2025, 8, 22, tzinfo=_dt.timezone.utc).timestamp() * 1e9
    )
    window_end_ns = int(
        _dt.datetime(2026, 8, 21, tzinfo=_dt.timezone.utc).timestamp() * 1e9
    )
    symbols = staged_symbol_names(catalog_root)
    bars = _bar_field_stats(catalog_root, window_start_ns, window_end_ns)
    funding = _funding_field_stats(funding_root, symbols)
    ticks = _tick_size_stats(catalog_root, symbols)
    identity = _identity_echo()
    spec = _frozen_spec(repo_root)

    checks = {
        "all_20_staged_symbols_present": bars["symbols_scanned"] == 20,
        "benchmark_symbol_present": "BTCUSDT-PERP.BINANCE" in symbols,
        "no_negative_prices_or_volumes": not any(bars["negative_counts_total"].values()),
        "all_closes_strictly_positive": all(
            s["close_positive_all"] for s in bars["per_symbol"].values()
        ),
        "all_series_strictly_increasing": not bars["non_monotonic_symbols"],
        "no_duplicate_stamps": not bars["duplicate_stamp_symbols"],
        "no_null_like_rows": bars["null_like_rows"] == 0,
        "window_coverage_complete": all(
            s["rows_in_window"] > 0 for s in bars["per_symbol"].values()
        ),
        "funding_present_for_every_symbol": all(
            v.get("present") for v in funding["per_symbol"].values()
        ),
        "funding_rows_complete": all(
            v.get("rows", 0) > 0 and v.get("duplicate_publish_stamps", 1) == 0
            and v.get("rates_finite", False)
            for v in funding["per_symbol"].values()
        ),
        "tick_sizes_present_for_every_symbol": not ticks["missing_or_invalid"],
        "identity_digests_match_freeze": identity["digests_match_freeze"],
    }
    artifact = {
        "artifact": "v11i_lottery_max_skew_c1_field_verification",
        "family_id": FAMILY_ID,
        "freeze_condition": "V11-SEED-LOTTERY-MAX-SKEW selection_freeze_specs",
        "frozen_spec_echo": {
            "window": spec["common"]["window"],
            "folds": spec["common"]["folds"],
            "fold_policy": spec["common"]["fold_policy"],
            "decision_clock": spec["common"]["decision_clock"],
            "universe": spec["common"]["universe"],
            "benchmark": spec["common"]["benchmark"],
            "costs": spec["common"]["costs"],
            "flags": spec["flags"],
        },
        "scored_window": [WINDOW_START_ISO, WINDOW_END_ISO],
        "bars": bars,
        "funding": funding,
        "tick_sizes": ticks,
        "identity": identity,
        "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "failed_checks": sorted(k for k, ok in checks.items() if not ok),
        "read_only": True,
    }
    return artifact


# --------------------------------------------------------------------------- #
# A3 -- schedule-only cost feasibility gate
# --------------------------------------------------------------------------- #
def _fill_price_map(
    plugin: LotteryMaxSkewPlugin,
    instant_ns: int,
    symbols: Sequence[str],
    stress: StressSpec,
) -> dict[str, float]:
    """Fill-price cost inputs: applied fill price first, mark fallback."""
    prices: dict[str, float] = {}
    pending: list[str] = []
    for record in plugin.fills_at(int(instant_ns), symbols=symbols, stress=stress):
        if record.applied and record.price is not None:
            prices[record.symbol] = float(record.price)
        else:
            pending.append(record.symbol)
    if pending:
        marks = plugin.marks_at(pending, int(instant_ns))
        for sym, price in marks.items():
            if price is None or not math.isfinite(float(price)) or float(price) <= 0.0:
                raise ContractViolation(f"no fill/mark price for {sym} at {instant_ns}")
            prices[sym] = float(price)
    return prices


def build_a3_gate_artifact(
    *,
    catalog_root: Path = DEFAULT_CATALOG_ROOT,
    funding_root: Path = DEFAULT_FUNDING_ROOT,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    """Run the frozen A3 gate on this family's deterministic schedule."""
    from research.v11.families.lottery_max_skew.data import load_market_inputs

    inputs = load_market_inputs(
        catalog_root=Path(catalog_root), funding_root=Path(funding_root)
    )
    plugin = build_arm_plugin(ANCHOR_ARM, inputs)
    baseline = plugin.baseline_stress()
    universe = plugin.universe(baseline)
    instants = [int(v) for v in plugin.schedule().instants]

    decisions: dict[int, ScheduleDecision] = {}
    availability: dict[int, SignalAvailability] = {}
    fill_prices: dict[int, dict[str, float]] = {}
    previous: dict[str, float] = {}
    skip_instants: list[int] = []
    for instant in instants:
        book = plugin.targets_at(instant, universe=universe, stress=baseline)
        weights = {str(sym): float(w) for sym, w in (book.get("weights") or [])}
        reason = book.get("reason_code")
        if reason in ("fold_boundary_force_flat", "terminal_force_flat"):
            kind = "FORCED_FLAT"
        else:
            if book.get("status") != "OK":
                skip_instants.append(instant)
                raise ContractViolation(
                    f"SKIP book at {instant} ({reason}): the frozen staged "
                    "snapshot must yield a selection at every open instant"
                )
            kind = "DISCRETIONARY"
        decisions[instant] = ScheduleDecision(
            instant_ns=instant, kind=kind, weights=weights
        )
        availability[instant] = SignalAvailability(
            instant_ns=instant, available=True, missing_symbols=()
        )
        touched = sorted(set(previous) | set(weights))
        if touched:
            fill_prices[instant] = _fill_price_map(plugin, instant, touched, baseline)
        previous = weights

    gate_inputs = ScheduleArtifacts(
        instants_ns=instants,
        decisions=decisions,
        fill_prices=fill_prices,
        settlements={
            sym: plugin.settlements(sym)
            for sym in sorted(
                {s for d in decisions.values() for s in d.weights}
            )
        },
        cost_model=plugin.cost_model(),
        signal_availability=availability,
        source="research.v11.families.lottery_max_skew.plugin.LotteryMaxSkewPlugin.schedule",
    )
    report = evaluate_schedule_cost_feasibility(gate_inputs)
    artifact = {
        "artifact": "v11i_lottery_max_skew_a3_cost_gate",
        "family_id": FAMILY_ID,
        "arm_id": ANCHOR_ARM,
        "schedule_scope": {
            "window": [WINDOW_START_ISO, WINDOW_END_ISO],
            "decision_clock": "Mondays 00:00:00Z + terminal force-flat",
            "instants": len(instants),
            "discretionary": sum(
                1 for d in decisions.values() if d.kind == "DISCRETIONARY"
            ),
            "forced_flat": sum(
                1 for d in decisions.values() if d.kind == "FORCED_FLAT"
            ),
        },
        "gate_payload": report.payload,
        "verdict": report.verdict,
        "schedule_sha256": report.payload["schedule_sha256"],
        "outcome_blind": True,
    }
    if report.verdict != "PASS":
        artifact["failed_floors"] = [
            row for row in report.payload["floors"] if row["status"] != "PASS"
        ]
    return artifact


# --------------------------------------------------------------------------- #
# A4 -- exact-arm dry-run (synthetic data, real adapter path)
# --------------------------------------------------------------------------- #
_A4_ROLE_BY_ARM = {
    ANCHOR_ARM: "anchor",
    NEIGHBOUR_ARM: "neighbour",
    CONTROL_ARM: "causal_control",
}


def _synthetic_window_inputs():
    """Synthetic inputs spanning the warmup + the whole frozen window."""
    start_day = day_index(_utc_midnight("2025-08-22")) - 130
    end_day = day_index(_utc_midnight("2026-08-21"))
    return build_synthetic_bars(start_day=start_day, n_days=end_day - start_day + 3)


def _utc_midnight(day: str) -> int:
    import datetime as _dt

    d = _dt.date(int(day[0:4]), int(day[5:7]), int(day[8:10]))
    return int(
        _dt.datetime(d.year, d.month, d.day, tzinfo=_dt.timezone.utc).timestamp()
    ) * 1_000_000_000


def build_a4_dryrun_artifact(
    *, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    """Exact-arm dry-run over the three frozen arms + v2 identity block."""
    inputs, _frames = _synthetic_window_inputs()
    arms = {
        _A4_ROLE_BY_ARM[arm]: build_arm_plugin(arm, inputs) for arm in ARM_IDS
    }
    with tempfile.TemporaryDirectory(prefix="v11i_lot_a4_") as tmp:
        ledger = Path(tmp) / "dryrun_lottery_max_skew.jsonl"
        result = run_exact_arm_dryrun(ledger_path=ledger, arms=arms)

    identity = _identity_echo()
    digests = {
        role: arm_config_digest(frozen_identity(arm), arm_id=arm)
        for arm, role in _A4_ROLE_BY_ARM.items()
    }
    identity_block = {
        "scheme": "research.v11.publication_identity.arm_config_digest (v2)",
        "arm_config_digests_by_role": digests,
        "pairwise_distinct": len(set(digests.values())) == len(digests),
        "frozen_digest_equality": identity["digest_equality"],
        "digests_match_freeze": identity["digests_match_freeze"],
    }
    artifact = {
        "artifact": "v11i_lottery_max_skew_a4_exact_arm_dryrun",
        "family_id": FAMILY_ID,
        "arms": {arm: _A4_ROLE_BY_ARM[arm] for arm in ARM_IDS},
        "data": "synthetic deterministic fixture through the REAL adapter path",
        "dryrun_result": result,
        "arm_identity_v2": identity_block,
        "verdict": "PASS" if (result["ok"] and identity_block["digests_match_freeze"]) else "FAIL",
    }
    return artifact


# --------------------------------------------------------------------------- #
# Emission
# --------------------------------------------------------------------------- #
def _atomic_write(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=1, sort_keys=False) + "\n")
    tmp.replace(path)


def emit_all(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Build + write all three lane artifacts; refuse any non-PASS verdict."""
    summary: dict[str, Any] = {}
    c1 = build_c1_artifact(repo_root=repo_root)
    a3 = build_a3_gate_artifact(repo_root=repo_root)
    a4 = build_a4_dryrun_artifact(repo_root=repo_root)
    for name, payload in (
        (ARTIFACT_C1, c1),
        (ARTIFACT_A3, a3),
        (ARTIFACT_A4, a4),
    ):
        if payload.get("verdict") != "PASS":
            raise ContractViolation(f"{name} verdict {payload.get('verdict')!r} != PASS")
        _atomic_write(payload, repo_root / AUDIT_DIR / name)
        summary[name] = {
            "path": str(AUDIT_DIR / name),
            "verdict": "PASS",
            "sha256": payload_sha256(payload),
        }
    return summary


__all__ = [
    "ARTIFACT_A3",
    "ARTIFACT_A4",
    "ARTIFACT_C1",
    "AUDIT_DIR",
    "build_a3_gate_artifact",
    "build_a4_dryrun_artifact",
    "build_c1_artifact",
    "emit_all",
]
