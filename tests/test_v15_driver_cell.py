"""V15 I-TOOLS lane -- the run_v15_cell.py driver tests (synthetic-only).

Covers the lane's required areas on SYNTHETIC staged trees built in scratch
tmp trees (never the machine-local staged root, never the repo results
namespace, never a scored ledger outside tmp):

(a) flag validation: ``--dry-run`` refuses ``--publish``/``--ledger`` and
    requires an explicit scratch ``--out-root``; ``--tick-sizes-json`` is a
    synthetic-only wiring; ``--publish`` requires ``--ledger`` AND an
    ``--expect-head`` pin (which must equal git HEAD);
(b) six-arm digest pin: recomputed == recorded for all six arms, pairwise
    unique at DRIVER level; a tampered recorded digest fails closed
    (exit 2) BEFORE any data load (no preflight artifact exists after);
(c) staged-verification failure path: one corrupted parquet byte against a
    staging authority copy fails the run closed (exit 2) before any family
    load; the honest copy verifies per-file;
(d) synthetic dry-run end-to-end for ONE arm of each family using the
    family tests' own synthetic fixture builders -> exit 0, non-vacuity
    asserted (n_decisions > 0, n_fills > 0, refusal digests present,
    cost_holding_terms == 0), margin-to-fail recorded, NO ledger anywhere,
    no writes outside the scratch root;
(e) TECHABORT discipline: a ``--dry-run`` whose sink resolves under a
    ``research/control`` subtree is refused outright (exit 2, nothing
    written); an injected pre-metric crash writes the forensic file ONLY to
    the scratch sink with ZERO budget effect;
(f) exactly-once replay: a synthetic scored payload mirroring the cell dict
    shape published twice through the driver's publication entry point --
    the second publish is ``IDEMPOTENT_REPLAY_SKIPPED`` with ZERO
    denominator delta (the family runners refuse ``scored=True``; that
    guard is never bypassed, so publication is exercised via the frozen
    ``publish_v12_cell`` path with a synthetic payload);
(g) zero-decision cell -> exit 2 (the non-vacuity postcondition fed a
    synthetic empty result), with the failure recorded for forensics.

No real data file is read by these tests; nothing here computes PnL on real
data and no scored mode is ever run (the dry-run wires ``scored=False``).
Targeted only; the full pytest suite is reserved for A1.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

# --------------------------------------------------------------------------- #
# Load the driver module (plain file; tools/ is not imported as a package)
# --------------------------------------------------------------------------- #
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DRIVER_PATH = _REPO_ROOT / "research/control/v15_run/tools/run_v15_cell.py"
_SPEC = importlib.util.spec_from_file_location("run_v15_cell", _DRIVER_PATH)
run_v15_cell = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(run_v15_cell)

import research.adapter_v10  # noqa: E402,F401  (import-order contract)

from tests.test_v15_f1_fixtures import (  # noqa: E402  (family fixture builder)
    TICK_SIZES as ELITE_TICK_SIZES,
    build_constant_panel_root,
)
from research.v15.families.taker_sat.frozen_identity import (  # noqa: E402
    ANCHOR_ARM as TAKER_ANCHOR,
    TAKER_SAT_ARM_CONFIG_DIGESTS,
    UNIVERSE as TAKER_UNIVERSE,
)
from research.v15.families.elite_size_asym.frozen_identity import (  # noqa: E402
    ANCHOR_ARM as ELITE_ANCHOR,
    CONTROL_ARM as ELITE_CONTROL,
    NEIGHBOR_ARM as ELITE_NEIGHBOR,
)

CONTROL_TREE = _REPO_ROOT / "research" / "control"
V15_CONTROL_DIR = CONTROL_TREE / "v15_run"

DAY_MS = 86_400_000


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _stray_control_techaborts() -> list[Path]:
    return sorted(V15_CONTROL_DIR.glob("TECHABORT_*.json"))


# --------------------------------------------------------------------------- #
# Synthetic staged trees
# --------------------------------------------------------------------------- #
def _write_tiny_root(root: Path) -> Path:
    """A minimal (1 symbol, few days) synthetic staged parquet tree.

    Structurally valid subtrees for the dry-run staging self-verification;
    never used for a real family load in these tests.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    root = Path(root)
    for subtree in ("metrics", "klines", "funding"):
        (root / subtree).mkdir(parents=True, exist_ok=True)
    sym = "BTCUSDT"
    day0 = datetime(2025, 8, 1, tzinfo=timezone.utc)
    labels = [
        (day0 + timedelta(minutes=5 * i)).strftime("%Y-%m-%d %H:%M:%S")
        for i in range(288)
    ]
    metrics = pa.table(
        {
            "create_time": pa.array(labels, pa.string()),
            "symbol": pa.array([sym] * 288, pa.string()),
            "sum_open_interest": pa.array([1000.0] * 288, pa.float64()),
            "sum_open_interest_value": pa.array([1.0e7] * 288, pa.float64()),
            "count_toptrader_long_short_ratio": pa.array([1.0] * 288, pa.float64()),
            "sum_toptrader_long_short_ratio": pa.array([1.0] * 288, pa.float64()),
            "count_long_short_ratio": pa.array([1.0] * 288, pa.float64()),
            "sum_taker_long_short_vol_ratio": pa.array([0.5] * 288, pa.float64()),
            "ts": pa.array(
                [int(day0.timestamp()) * 1_000_000 + 300_000_000 * i for i in range(288)],
                pa.timestamp("us"),
            ),
        }
    )
    pq.write_table(metrics, root / "metrics" / f"{sym}.parquet")
    opens = [int(day0.timestamp()) * 1000 + 900_000 * i for i in range(96)]
    klines = pa.table(
        {
            "open_time_ms": pa.array(opens, pa.int64()),
            "open": pa.array([100.0] * 96, pa.float64()),
            "high": pa.array([100.0] * 96, pa.float64()),
            "low": pa.array([100.0] * 96, pa.float64()),
            "close": pa.array([100.0] * 96, pa.float64()),
            "volume": pa.array([1.0] * 96, pa.float64()),
            "close_time_ms": pa.array([ms + 899_999 for ms in opens], pa.int64()),
        }
    )
    pq.write_table(klines, root / "klines" / f"{sym}.parquet")
    funding = pa.table(
        {
            "funding_time_ms": pa.array(
                [int(day0.timestamp()) * 1000 + 8 * 3600 * 1000], pa.int64()
            ),
            "funding_rate": pa.array([1e-4], pa.float64()),
        }
    )
    pq.write_table(funding, root / "funding" / f"{sym}.parquet")
    return root


def _write_staging_report(root: Path, path: Path) -> Path:
    """A self-consistency staging authority for one synthetic tree."""
    files = {
        str(p.relative_to(root)): _sha256_file(p)
        for p in sorted(Path(root).rglob("*.parquet"))
    }
    payload = {
        "schema": "v15_staging_v1",
        "artifact": "staging_report",
        "synthetic_self_consistency": True,
        "STAGING_OVERALL": "PASS_UNDER_AMENDMENT_1",
        "gates": {"STAGING_OVERALL": "PASS_UNDER_AMENDMENT_1"},
        "parquet_sha256": files,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return path


def build_taker_world(root: Path) -> Path:
    """A FULL-FROZEN-SCALE synthetic staged tree for the taker family.

    Hand-engineered constant world over the frozen 20-symbol universe and
    the frozen F0/F1/F2 folds (the driver passes no family overrides):

    * metrics days 2025-07-01..2026-08-21, 288-label grid per day; the
      taker ratio is a per-symbol constant 1.0 + 0.02*i (universe order) so
      the clipped-log daily aggression is strictly increasing in the frozen
      symbol order; OI value constant (churn O = 0);
    * klines 15m at a constant 100.0 from 2025-08-01 through 2026-08-21
      (every decision fill and the F2 force-flat fill);
    * funding 8h stamps at 1e-4 (under the documented cap).

    The 5v5 fade book is therefore deterministic and populated at every
    decision (n_available = 20 >= 10), with price PnL 0 and balanced funding
    -- the only realized PnL is the hand-known fill cost.  Every byte is
    generated here; nothing is scored.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    root = Path(root)
    for subtree in ("metrics", "klines", "funding"):
        (root / subtree).mkdir(parents=True, exist_ok=True)
    symbols = sorted(TAKER_UNIVERSE)

    def daterange(start: date, end: date) -> list[date]:
        days = []
        cursor = start
        while cursor <= end:
            days.append(cursor)
            cursor += timedelta(days=1)
        return days

    metric_days = daterange(date(2025, 7, 1), date(2026, 8, 21))
    kline_days = daterange(date(2025, 8, 1), date(2026, 8, 21))
    labels = [
        f"{hour:02d}:{minute:02d}:00"
        for hour in range(24)
        for minute in (0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55)
    ]
    assert len(labels) == 288
    for idx, sym in enumerate(symbols):
        ratio = 1.0 + 0.02 * idx  # inside (0.2, 5): the clip never binds
        oi_value = 1_000_000.0 * (1.0 + 0.01 * idx)
        epoch_us = [
            int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
            * 1_000_000
            for d in metric_days
        ]
        base_us = [us for us in epoch_us for _ in labels]
        metrics = pa.table(
            {
                "create_time": pa.array(
                    [f"{d.isoformat()} {label}" for d in metric_days for label in labels],
                    pa.string(),
                ),
                "symbol": pa.array([sym] * len(base_us), pa.string()),
                "sum_open_interest": pa.array(
                    [1000.0] * len(base_us), pa.float64()
                ),
                "sum_open_interest_value": pa.array(
                    [oi_value] * len(base_us), pa.float64()
                ),
                "count_toptrader_long_short_ratio": pa.array(
                    [1.0] * len(base_us), pa.float64()
                ),
                "sum_toptrader_long_short_ratio": pa.array(
                    [1.0] * len(base_us), pa.float64()
                ),
                "count_long_short_ratio": pa.array([1.0] * len(base_us), pa.float64()),
                "sum_taker_long_short_vol_ratio": pa.array(
                    [ratio] * len(base_us), pa.float64()
                ),
                "ts": pa.array(
                    [us + 300_000_000 * k for us in epoch_us for k in range(288)],
                    pa.timestamp("us"),
                ),
            }
        )
        pq.write_table(metrics, root / "metrics" / f"{sym}.parquet")

        opens = [
            int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
            * 1000
            + 900_000 * slot
            for d in kline_days
            for slot in range(96)
        ]
        klines = pa.table(
            {
                "open_time_ms": pa.array(opens, pa.int64()),
                "open": pa.array([100.0] * len(opens), pa.float64()),
                "high": pa.array([100.0] * len(opens), pa.float64()),
                "low": pa.array([100.0] * len(opens), pa.float64()),
                "close": pa.array([100.0] * len(opens), pa.float64()),
                "volume": pa.array([1.0] * len(opens), pa.float64()),
                "close_time_ms": pa.array(
                    [ms + 899_999 for ms in opens], pa.int64()
                ),
            }
        )
        pq.write_table(klines, root / "klines" / f"{sym}.parquet")

        stamps = [
            int(datetime(d.year, d.month, d.day, hour, tzinfo=timezone.utc).timestamp())
            * 1000
            for d in daterange(date(2025, 8, 21), date(2026, 8, 21))
            for hour in (0, 8, 16)
        ]
        funding = pa.table(
            {
                "funding_time_ms": pa.array(stamps, pa.int64()),
                "funding_rate": pa.array([1e-4] * len(stamps), pa.float64()),
            }
        )
        pq.write_table(funding, root / "funding" / f"{sym}.parquet")
    return root


# --------------------------------------------------------------------------- #
# Session-cached synthetic worlds + shared tick map
# --------------------------------------------------------------------------- #
_WORLD_CACHE: dict[str, Path] = {}


def _cached_world(key: str, builder) -> Path:
    if key not in _WORLD_CACHE:
        import tempfile

        base = Path(tempfile.mkdtemp(prefix=f"v15_driver_{key}_"))
        _WORLD_CACHE[key] = builder(base / "staged")
    return _WORLD_CACHE[key]


@pytest.fixture(scope="session")
def tiny_root(tmp_path_factory) -> Path:
    return _write_tiny_root(tmp_path_factory.mktemp("v15_driver_tiny") / "staged")


@pytest.fixture(scope="session")
def elite_world(tmp_path_factory) -> Path:
    """The f1 family test suite's constant panel (full frozen universe)."""
    key = "elite"
    if key not in _WORLD_CACHE:
        base = tmp_path_factory.mktemp("v15_driver_elite")
        _WORLD_CACHE[key] = build_constant_panel_root(base / "staged")
    return _WORLD_CACHE[key]


@pytest.fixture(scope="session")
def taker_world(tmp_path_factory) -> Path:
    key = "taker"
    if key not in _WORLD_CACHE:
        base = tmp_path_factory.mktemp("v15_driver_taker")
        _WORLD_CACHE[key] = build_taker_world(base / "staged")
    return _WORLD_CACHE[key]


@pytest.fixture(scope="session")
def elite_tick_sizes_json(tmp_path_factory) -> str:
    path = tmp_path_factory.mktemp("v15_driver_ticks") / "tick_sizes.json"
    path.write_text(json.dumps(ELITE_TICK_SIZES), encoding="utf-8")
    return str(path)


def run_dry_run(
    world_root: Path,
    out_root: Path,
    family: str,
    arm: str,
    *,
    tick_sizes_json: str | None = None,
    staging_report: Path | None = None,
    extra: list[str] | None = None,
) -> int:
    argv = [
        "--family", family,
        "--arm", arm,
        "--data-root", str(world_root),
        "--out-root", str(out_root),
        "--techabort-dir", str(out_root / "TECHABORT"),
        "--dry-run",
    ]
    if tick_sizes_json:
        argv += ["--tick-sizes-json", tick_sizes_json]
    if staging_report is not None:
        argv += ["--staging-report", str(staging_report)]
    if extra:
        argv += list(extra)
    return run_v15_cell.main(argv)


# --------------------------------------------------------------------------- #
# (a) flag validation
# --------------------------------------------------------------------------- #
def test_v15drv_dry_run_refuses_publish_and_ledger(tiny_root, tmp_path):
    base = [
        "--family", "elite_size_asym",
        "--arm", ELITE_ANCHOR,
        "--data-root", str(tiny_root),
        "--out-root", str(tmp_path / "o"),
        "--dry-run",
    ]
    assert (
        run_v15_cell.main(
            base
            + ["--publish", "--ledger", str(tmp_path / "l.jsonl"),
               "--expect-head", "x"]
        )
        == run_v15_cell.EXIT_FAIL_CLOSED
    )
    assert (
        run_v15_cell.main(base + ["--ledger", str(tmp_path / "l.jsonl")])
        == run_v15_cell.EXIT_FAIL_CLOSED
    )
    # an explicit scratch out-root is REQUIRED under --dry-run
    assert (
        run_v15_cell.main(
            ["--family", "elite_size_asym", "--arm", ELITE_ANCHOR,
             "--data-root", str(tiny_root), "--dry-run"]
        )
        == run_v15_cell.EXIT_FAIL_CLOSED
    )


def test_v15drv_tick_sizes_json_is_synthetic_only(tiny_root, tmp_path):
    ticks = tmp_path / "ticks.json"
    ticks.write_text(json.dumps(ELITE_TICK_SIZES), encoding="utf-8")
    assert (
        run_v15_cell.main(
            [
                "--family", "elite_size_asym",
                "--arm", ELITE_ANCHOR,
                "--data-root", str(tiny_root),
                "--tick-sizes-json", str(ticks),
            ]
        )
        == run_v15_cell.EXIT_FAIL_CLOSED
    )


def test_v15drv_publish_requires_ledger_and_expect_head():
    base = ["--family", "taker_sat", "--arm", TAKER_ANCHOR]
    assert (
        run_v15_cell.main(base + ["--publish"])
        == run_v15_cell.EXIT_FAIL_CLOSED
    )
    assert (
        run_v15_cell.main(
            base + ["--publish", "--ledger", "/tmp/v15drv_should_not_exist.jsonl"]
        )
        == run_v15_cell.EXIT_FAIL_CLOSED
    )


def test_v15drv_publish_head_pin_enforced(tiny_root, tmp_path):
    """--publish with a WRONG --expect-head fails closed BEFORE any load."""
    rc = run_v15_cell.main(
        [
            "--family", "taker_sat",
            "--arm", TAKER_ANCHOR,
            "--data-root", str(tiny_root),
            "--out-root", str(tmp_path / "o"),
            "--ledger", str(tmp_path / "l.jsonl"),
            "--publish",
            "--expect-head", "0" * 40,
        ]
    )
    assert rc == run_v15_cell.EXIT_FAIL_CLOSED
    assert not (tmp_path / "l.jsonl").exists()
    assert list(tmp_path.rglob("*.jsonl")) == []


def test_v15drv_unknown_arm_refused(tiny_root, tmp_path, capsys):
    rc = run_dry_run(tiny_root, tmp_path / "o", "elite_size_asym", "NOT-FROZEN")
    assert rc == run_v15_cell.EXIT_FAIL_CLOSED
    assert "not frozen" in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# (b) six-arm digest pin
# --------------------------------------------------------------------------- #
def test_v15drv_six_arm_digest_pin_recomputed_recorded_pairwise_unique():
    registry = run_v15_cell.family_registry()
    report = run_v15_cell.verify_all_arm_digests(registry)
    assert report["ok"] is True
    assert report["n_arms"] == 6 and report["n_match"] == 6
    assert report["pairwise_unique"] is True and report["collisions"] == []
    digests = {arm: entry["module_digest"] for arm, entry in report["arms"].items()}
    assert len(set(digests.values())) == 6
    # the taker recorded pins are the frozen family records verbatim
    for arm, recorded in TAKER_SAT_ARM_CONFIG_DIGESTS.items():
        assert digests[arm] == recorded
    # the elite recorded pins are the driver's pre-score implementation record
    for arm, recorded in run_v15_cell.ELITE_ARM_CONFIG_DIGESTS_RECORDED.items():
        assert digests[arm] == recorded


def test_v15drv_digest_pin_fails_closed_on_tampered_record(
    tiny_root, tmp_path, monkeypatch
):
    tampered = dict(run_v15_cell.ELITE_ARM_CONFIG_DIGESTS_RECORDED)
    tampered[ELITE_ANCHOR] = "0" * 64
    monkeypatch.setattr(
        run_v15_cell, "ELITE_ARM_CONFIG_DIGESTS_RECORDED", tampered
    )
    out_root = tmp_path / "out"
    rc = run_dry_run(
        tiny_root, out_root, "elite_size_asym", ELITE_ANCHOR
    )
    assert rc == run_v15_cell.EXIT_FAIL_CLOSED
    # the pin fails BEFORE any data load: no preflight artifact exists
    assert not (out_root / "preflight.json").exists()


# --------------------------------------------------------------------------- #
# (c) staged-data authority verification
# --------------------------------------------------------------------------- #
def test_v15drv_staging_authority_honest_copy_verifies(tiny_root, tmp_path):
    report = _write_staging_report(tiny_root, tmp_path / "staging_report.json")
    verified = run_v15_cell.verify_staging_authority(tiny_root, report)
    assert verified["ok"] is True
    assert verified["problems"] == []
    assert verified["files_expected"] == verified["files_verified"] == 3
    assert verified["staging_overall"] == "PASS_UNDER_AMENDMENT_1"


def test_v15drv_corrupt_parquet_byte_fails_closed_before_load(
    tiny_root, tmp_path
):
    report = _write_staging_report(tiny_root, tmp_path / "staging_report.json")
    victim = tiny_root / "metrics" / "BTCUSDT.parquet"
    raw = bytearray(victim.read_bytes())
    raw[len(raw) // 2] ^= 0xFF
    victim.write_bytes(bytes(raw))
    out_root = tmp_path / "out"
    rc = run_dry_run(
        tiny_root, out_root, "elite_size_asym", ELITE_ANCHOR,
        staging_report=report,
    )
    assert rc == run_v15_cell.EXIT_FAIL_CLOSED
    # fail-closed per file, BEFORE any family load / preflight artifact
    assert not (out_root / "preflight.json").exists()


def test_v15drv_staging_overall_verdict_enforced(tiny_root, tmp_path):
    report = _write_staging_report(tiny_root, tmp_path / "report.json")
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["STAGING_OVERALL"] = "FAIL"
    payload["gates"]["STAGING_OVERALL"] = "FAIL"
    report.write_text(json.dumps(payload), encoding="utf-8")
    verified = run_v15_cell.verify_staging_authority(tiny_root, report)
    assert verified["ok"] is False
    assert any("STAGING_OVERALL" in p for p in verified["problems"])


# --------------------------------------------------------------------------- #
# (d) synthetic dry-run end-to-end (one arm per family)
# --------------------------------------------------------------------------- #
def test_v15drv_elite_dry_run_end_to_end(
    elite_world, elite_tick_sizes_json, tmp_path
):
    out_root = tmp_path / "out" / "elite_size_asym" / ELITE_ANCHOR
    report = _write_staging_report(elite_world, tmp_path / "staging_report.json")
    rc = run_dry_run(
        elite_world, out_root, "elite_size_asym", ELITE_ANCHOR,
        tick_sizes_json=elite_tick_sizes_json, staging_report=report,
    )
    assert rc == run_v15_cell.EXIT_OK
    preflight = json.loads((out_root / "preflight.json").read_text(encoding="utf-8"))
    assert preflight["mode"] == "synthetic_dry_run"
    assert preflight["no_scored_metric_yet"] is True
    assert preflight["scored_flag_wiring"]["family_run_arm_scored"] is False
    pin = preflight["six_arm_digest_pin"]
    assert pin["n_arms"] == 6 and pin["n_match"] == 6 and pin["pairwise_unique"]
    assert preflight["staged"]["ok"] is True
    assert preflight["staged"]["files_verified"] == 60  # 20 symbols x 3 subtrees
    metrics = json.loads(
        (out_root / "baseline_metrics.json").read_text(encoding="utf-8")
    )
    scored = metrics["scored_metrics"]
    assert metrics["scored"] is False  # the dry-run never wires scored=True
    assert scored["n_decisions"] > 0 and scored["n_fills"] > 0
    assert scored["cost_holding_terms"] == 0.0
    assert scored["remediated_kernel"] is True
    assert len(metrics["refusal_registry_digest"]) == 64
    margin = scored["margin_to_fail"]
    assert margin["thresholds"] == {
        "expectancy_per_day": 0.0,
        "largest_fold_positive_share": 0.5,
        "largest_symbol_positive_pnl_share": 0.7,
        "max_drawdown": 0.2,
        "position_pf": 1.1,
    }
    assert "expectancy_per_day" in margin["margins"]
    assert "max_drawdown" in margin["margins"]
    # constant-price world: every fold net is negative -> the fold-positive
    # and symbol-positive shares are undefined and recorded ABSENT
    assert "largest_fold_positive_share" in margin["absent_inputs"]
    assert "largest_symbol_positive_pnl_share" in margin["absent_inputs"]
    # NO ledger anywhere; no publication artifacts in dry-run
    assert list(tmp_path.rglob("*.jsonl")) == []
    assert not (out_root / "publish_record.json").exists()
    assert not (out_root / "cell_summary.json").exists()
    # the repo results namespace was never touched
    assert not (_REPO_ROOT / "results" / "v15_phase_e").exists()


def test_v15drv_taker_dry_run_end_to_end(
    taker_world, elite_tick_sizes_json, tmp_path
):
    out_root = tmp_path / "out" / "taker_sat" / TAKER_ANCHOR
    report = _write_staging_report(taker_world, tmp_path / "staging_report.json")
    rc = run_dry_run(
        taker_world, out_root, "taker_sat", TAKER_ANCHOR,
        tick_sizes_json=elite_tick_sizes_json,  # synthetic wiring (same universe)
        staging_report=report,
    )
    assert rc == run_v15_cell.EXIT_OK
    preflight = json.loads((out_root / "preflight.json").read_text(encoding="utf-8"))
    assert preflight["mode"] == "synthetic_dry_run"
    pin = preflight["six_arm_digest_pin"]
    assert pin["n_arms"] == 6 and pin["n_match"] == 6 and pin["pairwise_unique"]
    assert preflight["staged"]["files_verified"] == 60
    metrics = json.loads(
        (out_root / "baseline_metrics.json").read_text(encoding="utf-8")
    )
    scored = metrics["scored_metrics"]
    assert scored["n_decisions"] > 0
    assert scored["n_fills"] > 0
    assert scored["n_positions"] > 0
    assert scored["cost_holding_terms"] == 0.0
    assert scored["remediated_kernel"] is True
    assert len(metrics["refusal_registry_digest"]) == 64
    # the engineered world: longs pay 1e-4 funding, shorts receive it, the
    # balanced 5v5 book nets the funding to zero and only costs remain
    assert scored["funding_sum"] == pytest.approx(0.0, abs=1e-12)
    assert scored["price_pnl_sum"] == 0.0
    assert scored["cost_total"] > 0.0
    margin = scored["margin_to_fail"]
    assert "expectancy_per_day" in margin["margins"]
    assert "largest_symbol_positive_pnl_share" in margin["margins"]
    assert list(tmp_path.rglob("*.jsonl")) == []
    assert not (_REPO_ROOT / "results" / "v15_phase_e").exists()


# --------------------------------------------------------------------------- #
# (e) TECHABORT sink discipline
# --------------------------------------------------------------------------- #
def test_v15drv_dry_run_refuses_techabort_sink_under_control_tree(
    tiny_root, tmp_path
):
    assert _stray_control_techaborts() == []  # pre-state: control tree clean
    rc = run_dry_run(
        tiny_root, tmp_path / "out", "elite_size_asym", ELITE_ANCHOR,
        extra=["--techabort-dir", str(V15_CONTROL_DIR)],
    )
    assert rc == run_v15_cell.EXIT_FAIL_CLOSED
    assert _stray_control_techaborts() == []


def test_v15drv_techabort_fires_on_injected_crash_with_zero_budget(
    tiny_root, tmp_path, monkeypatch
):
    assert _stray_control_techaborts() == []

    real_registry = run_v15_cell.family_registry()

    def crashing_registry():
        registry = real_registry
        registry["elite_size_asym"]["run_arm"] = _crash_injector
        return registry

    monkeypatch.setattr(run_v15_cell, "family_registry", crashing_registry)
    out_root = tmp_path / "out" / "crash"
    with pytest.raises(SystemExit) as excinfo:
        run_dry_run(tiny_root, out_root, "elite_size_asym", ELITE_ANCHOR)
    assert excinfo.value.code == run_v15_cell.EXIT_CRASH
    forensic = out_root / "TECHABORT" / f"TECHABORT_{ELITE_ANCHOR}.json"
    assert forensic.is_file()
    payload = json.loads(forensic.read_text(encoding="utf-8"))
    assert payload["schema"] == "v15_driver_techabort_forensic_v1"
    assert payload["phase"].startswith("pre-metric")
    assert payload["scored_metric_computed"] is False
    assert "ZERO budget" in payload["budget_effect"]
    assert payload["crash"]["type"] == "RuntimeError"
    assert payload["fix_path"].startswith("driver-only")
    assert payload["ledger_state"]["ledger_exists"] is False
    assert _stray_control_techaborts() == []
    assert list(tmp_path.rglob("*.jsonl")) == []


def _crash_injector(*_args, **_kwargs):
    raise RuntimeError("injected pre-metric crash (driver test)")


# --------------------------------------------------------------------------- #
# (f) exactly-once replay through the driver publication entry point
# --------------------------------------------------------------------------- #
def _synthetic_scored_cell() -> dict[str, Any]:
    """A scored payload mirroring the frozen cell dict shape (SYNTHETIC).

    The family runners refuse run_arm(scored=True) and that guard is never
    bypassed, so the driver's publication path is exercised with this
    synthetic payload through publish_v12_cell exactly as the driver calls
    it.
    """
    return {
        "schema": "v15_driver_synthetic_cell_v1",
        "scored_metrics": {
            "score_valid": True,
            "net_return_sum": 0.01,
            "expectancy_per_day": 0.0001,
            "max_drawdown": 0.01,
            "position_pf": 1.4,
            "n_positions": 10,
            "n_decisions": 30,
            "n_fills": 20,
            "decisions": [{"symbol": "BTCUSDT", "decision_ts": 1}],
            "fills": [{"symbol": "BTCUSDT", "ts_ns": 2}],
            "cost_fills": 0.001,
            "cost_holding_terms": 0.0,
            "cost_total": 0.001,
            "funding_sum": 0.0,
            "price_pnl_sum": 0.011,
            "remediated_kernel": True,
        },
        "hashes": {"result_sha256": "a" * 64},
    }


@pytest.mark.parametrize("family,arm", [("taker_sat", TAKER_ANCHOR),
                                        ("elite_size_asym", ELITE_ANCHOR)])
def test_v15drv_publish_exactly_once_replay_zero_delta(family, arm, tmp_path):
    ledger = tmp_path / f"{family}_shard.jsonl"
    head = "b" * 40
    cell = _synthetic_scored_cell()
    first = run_v15_cell.publish_scored_cell(
        family=family, arm_id=arm, cell=cell, ledger_path=ledger, head=head,
    )
    assert first["publication"]["stage"] == "PUBLISHED"
    assert first["publication"]["published"] is True
    assert first["publication"]["published_delta"] == 1
    assert first["denominator_before"]["observed_total"] == 0
    assert first["denominator_after"]["observed_total"] == 1
    # exact replay: idempotent, ZERO denominator delta
    second = run_v15_cell.publish_scored_cell(
        family=family, arm_id=arm, cell=cell, ledger_path=ledger, head=head,
    )
    assert second["publication"]["stage"] == "IDEMPOTENT_REPLAY_SKIPPED"
    assert second["publication"]["published"] is False
    assert second["denominator_after"] == first["denominator_after"]
    from research.v12.accounting import read_v12_ledger

    state = read_v12_ledger(ledger)
    assert state["count"] == 1  # exactly one row for the trial, either way


# --------------------------------------------------------------------------- #
# (g) zero-decision cell -> exit 2
# --------------------------------------------------------------------------- #
def test_v15drv_nonvacuity_unit_rejects_empty_cell():
    fam = run_v15_cell.family_registry()["elite_size_asym"]
    empty = {
        "scored_metrics": {
            "n_decisions": 0,
            "n_fills": 0,
            "n_positions": 0,
            "cost_holding_terms": 0.0,
        },
        "refusal_registry": {"digest": "c" * 64},
    }
    problems = run_v15_cell.nonvacuity_problems(empty, fam)
    assert any("n_decisions" in p for p in problems)
    assert any("n_fills" in p for p in problems)
    assert not any("cost_holding_terms" in p for p in problems)
    # a missing refusal digest is its own problem
    no_digest = {"scored_metrics": dict(empty["scored_metrics"])}
    assert any(
        "refusal-registry digest" in p
        for p in run_v15_cell.nonvacuity_problems(no_digest, fam)
    )
    # a non-zero holding term fails L-V14-0
    holding = {
        "scored_metrics": {
            "n_decisions": 1,
            "n_fills": 1,
            "cost_holding_terms": 1e-6,
        },
        "refusal_registry": {"digest": "c" * 64},
    }
    assert any(
        "L-V14-0" in p
        for p in run_v15_cell.nonvacuity_problems(holding, fam)
    )


def test_v15drv_zero_decision_cell_fails_run_closed(tiny_root, tmp_path, monkeypatch):
    real_registry = run_v15_cell.family_registry()

    def empty_registry():
        registry = real_registry
        registry["elite_size_asym"]["run_arm"] = _empty_cell_runner
        return registry

    monkeypatch.setattr(run_v15_cell, "family_registry", empty_registry)
    out_root = tmp_path / "out" / "empty"
    rc = run_dry_run(tiny_root, out_root, "elite_size_asym", ELITE_ANCHOR)
    assert rc == run_v15_cell.EXIT_FAIL_CLOSED
    failure = json.loads(
        (out_root / "runner_nonvacuity.json").read_text(encoding="utf-8")
    )
    assert any("n_decisions" in p for p in failure["problems"])
    assert "FAILED run" in failure["disposition"]
    # nothing was published, nothing but the forensic record was written
    assert not (out_root / "baseline_metrics.json").exists()
    assert list(tmp_path.rglob("*.jsonl")) == []


def _empty_cell_runner(*_args, **_kwargs):
    return {
        "schema": "v15_driver_synthetic_empty_cell_v1",
        "scored_metrics": {
            "score_valid": True,
            "n_decisions": 0,
            "n_fills": 0,
            "n_positions": 0,
            "cost_holding_terms": 0.0,
        },
        "refusal_registry": {"digest": "c" * 64},
        "fold_signs": {"fold_net_sums": {}, "fold_positive": []},
        "hashes": {"result_sha256": "d" * 64},
    }


# --------------------------------------------------------------------------- #
# Margin-to-fail scaffolding unit pins
# --------------------------------------------------------------------------- #
def test_v15drv_margin_to_fail_signed_distances_and_absent_inputs():
    fam = run_v15_cell.family_registry()["taker_sat"]
    cell = {
        "scored_metrics": {
            "expectancy_per_day": 0.0002,
            "position_pf": 1.35,
            "max_drawdown": 0.08,
        },
        "fold_signs": {"fold_net_sums": {"F0": 0.02, "F1": 0.01, "F2": 0.005}},
        "per_symbol": {
            "positive_pnl_share_by_symbol": {"AAAUSDT": 0.3, "BBBUSDT": 0.2}
        },
    }
    margin = run_v15_cell.compute_margin_to_fail(cell, fam)
    assert margin["margins"]["expectancy_per_day"] == pytest.approx(0.0002)
    assert margin["margins"]["position_pf"] == pytest.approx(0.25)
    # largest positive fold share = 0.02/0.035 -> margin = 0.5 - 4/7
    assert margin["margins"]["largest_fold_positive_share"] == pytest.approx(
        0.5 - (0.02 / 0.035), abs=1e-12
    )
    assert margin["margins"]["largest_symbol_positive_pnl_share"] == pytest.approx(
        0.7 - 0.3
    )
    assert margin["margins"]["max_drawdown"] == pytest.approx(0.12)
    assert margin["absent_inputs"] == []

    # failing-side margins are NEGATIVE (signed distance, never clamped)
    losing = {
        "scored_metrics": {
            "expectancy_per_day": -0.001,
            "position_pf": 0.8,
            "max_drawdown": 0.31,
        },
        "fold_signs": {"fold_net_sums": {"F0": -0.01, "F1": 0.005, "F2": -0.002}},
        "per_symbol": {"positive_pnl_share_by_symbol": {}},
    }
    margin = run_v15_cell.compute_margin_to_fail(losing, fam)
    assert margin["margins"]["expectancy_per_day"] == pytest.approx(-0.001)
    assert margin["margins"]["position_pf"] == pytest.approx(-0.30)
    assert margin["margins"]["max_drawdown"] == pytest.approx(-0.11)
    # the single positive fold IS a defined (failing-side) share: 1.0
    assert margin["margins"]["largest_fold_positive_share"] == pytest.approx(-0.5)
    # an empty positive-symbol pool: the symbol share is ABSENT, never 0
    assert margin["absent_inputs"] == ["largest_symbol_positive_pnl_share"]


# --------------------------------------------------------------------------- #
# Preflight-only smoke on the tiny tree (all pins, no family load)
# --------------------------------------------------------------------------- #
def test_v15drv_preflight_only_smoke(tiny_root, tmp_path):
    out_root = tmp_path / "out" / "smoke"
    rc = run_dry_run(
        tiny_root, out_root, "taker_sat", TAKER_ANCHOR, extra=["--preflight-only"]
    )
    assert rc == run_v15_cell.EXIT_OK
    preflight = json.loads((out_root / "preflight.json").read_text(encoding="utf-8"))
    assert preflight["no_scored_metric_yet"] is True
    assert preflight["six_arm_digest_pin"]["ok"] is True
    assert len(preflight["arm_config_digest"]) == 64
    # preflight-only stops before any metric: no baseline artifact
    assert not (out_root / "baseline_metrics.json").exists()
