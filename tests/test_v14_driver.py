"""V14 I TOOLS lane -- the run_v14_cell.py driver tests (synthetic-only).

Covers the lane's six required areas on a TINY SYNTHETIC staged root built
in a scratch tmp tree (never the real snapshot, never any repo results
namespace, never a scored ledger outside tmp):

(a) all six frozen arms CONSTRUCT through the driver registry on the
    synthetic root and produce PAIRWISE-UNIQUE preflight digests
    (recomputed == recorded, 6/6); the digest pin also fails closed
    (exit 2) when a recorded digest is tampered with; the basislv arms
    traverse the FULL preflight incl. the frozen runner-compatibility pin
    (exit 0);
(b) scored records carry the L-V14-0 remediated-kernel cost breakout:
    ``cost_fills`` and ``cost_holding_terms`` present, holding terms
    EXACTLY 0 (charged on fills only, by construction), and the basislv
    scored runs carry the price-only vs total expectancy split;
(c) ``--dry-run`` refuses to write any scored ledger (and refuses
    ``--publish``/``--ledger`` outright, and requires an explicit scratch
    ``--out-root``);
(d) oicyc scored records carry the CONFIRMATORY status metadata and the
    denominator note (plan Section 1.1 carry-through);
(e) the basislv gate-input contract: the frozen gate returns the BLOCKED
    verdict when the price-only clause inputs are missing (never an
    inferred PASS), and the driver's anchor-side gate record is BLOCKED
    (never PASS) while sibling evidence is missing, then evaluates with
    the REQUIRED clause inputs once siblings exist;
(f) the TECHABORT hook fires on an injected pre-metric crash: forensic
    file written ONLY to the temp sink (never into any ``research/control``
    tree), ``scored_metric_computed`` false, ZERO budget effect, no ledger
    anywhere; and a ``--dry-run`` whose TECHABORT sink resolves under a
    ``research/control`` subtree is refused outright (the structural fix
    for the cancelled lane's six stray control-tree TECHABORT files).

RECORDED BLOCKED EVIDENCE (frozen-family defect; owner decision required):
the frozen oicyc plugin accepts the drop_one_fold cell at the
folds-contract probe, but its chained ``targets_at`` crashes under ANY
dropped-fold stress (``_fold_terminal_stamps`` -> ``fold_assignments``
refuses a fold with no retained members), while the frozen generic runner
queries ``targets_at`` at EVERY open instant including a dropped fold's
stamps.  The oicyc drop_one_fold cell therefore cannot traverse; the
driver's preflight pin fails the oicyc arms closed pre-metric (exit 2,
zero budget) and the blocked state is PINNED by
``test_v14drv_oicyc_traversal_pin_blocked_frozen_conflict`` -- that test
must flip to exit-0 when an owner-authorized family delta lands.

No real data file is read by these tests: the synthetic world uses the
frozen universe NAMES (the driver's code path is identical) but every byte
of data is generated here.  Targeted only; the full pytest suite is
reserved for A1.
"""

from __future__ import annotations

import importlib.util
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

# --------------------------------------------------------------------------- #
# Load the driver module (plain file; tools/ is not a package)
# --------------------------------------------------------------------------- #
_DRIVER_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/control/v14_run/tools/run_v14_cell.py"
)
_SPEC = importlib.util.spec_from_file_location("run_v14_cell", _DRIVER_PATH)
run_v14_cell = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(run_v14_cell)

from research.v14.families.basislv_premfade.gate_runner import (  # noqa: E402
    VERDICT_BLOCKED_CLAUSE_INPUTS,
    evaluate_family_gate,
)
from research.v14.families.basislv_premfade.strategy import (  # noqa: E402
    ANCHOR_ARM as BASISLV_ANCHOR,
    BUCKET_NS,
    BENCHMARK_SYMBOL,
    CONTROL_ARM as BASISLV_CONTROL,
    DAY_NS,
    FIRST_STAMP_ISO,
    NEIGHBOUR_ARM as BASISLV_NEIGHBOUR,
    WINDOW_END_ISO,
    parse_iso_utc,
)
from research.v14.families.oicyc.audits import (  # noqa: E402
    tradeable_universe_symbols,
)
from research.v14.families.oicyc.strategy import (  # noqa: E402
    ANCHOR_ARM as OICYC_ANCHOR,
    fold_end_instants as oicyc_fold_ends,
    stamp_calendar as oicyc_calendar,
)

V14_UNIVERSE = tuple(tradeable_universe_symbols())  # the frozen 19 names
FEED_SYMBOLS = tuple(sorted(set(V14_UNIVERSE) | {BENCHMARK_SYMBOL}))

T0_NS = parse_iso_utc(FIRST_STAMP_ISO)
T_END_NS = parse_iso_utc(WINDOW_END_ISO)
PRICE_I128_SCALE = 10**16

SIX_ARMS = (
    ("basislv_premfade", BASISLV_ANCHOR),
    ("basislv_premfade", BASISLV_NEIGHBOUR),
    ("basislv_premfade", BASISLV_CONTROL),
    ("oicyc", OICYC_ANCHOR),
    ("oicyc", "CYC-14D"),
    ("oicyc", "CTL-OISHARE"),
)

GATE_PASS_VERDICTS = {
    "FAMILY_ADVANCES_TO_STAGE_A",
    "REJECTED_ANCHOR_FAIL",
    "REJECTED_PRICE_ONLY_CARRY_HARVEST",
    "REJECTED_NEIGHBOUR_SIGN_FLIP",
    "FALSIFIED_CONTROL_REPRODUCED_TILT_ARTIFACT",
}


def _i128(price: float) -> bytes:
    """One Nautilus i128 price cell (little-endian signed, raw / 1e16)."""
    return int(round(price * PRICE_I128_SCALE)).to_bytes(16, "little", signed=True)


def _sha256_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Synthetic staged root (tiny; constant worlds; every byte generated here)
# --------------------------------------------------------------------------- #
def build_synthetic_world(root: Path) -> dict[str, Path]:
    """Write the synthetic staged-equivalent tree + basis/OI authorities.

    Layout:
      <root>/staged/                     -- --staged-root (a3 label layout)
        staged_manifest_.json            -- self-describing SHA manifest
        binance_bar_15m/...              -- 15m bars for the 20 feed names
        crypto_perpetual_meta/...        -- real-shaped tick sizes (0.01)
        funding_scan_2026/...            -- native funding.json bundles
        funding_20240820_20260821/       -- empty label subtree
        oi_consolidated/...              -- 19 staged OI parquets (oicyc)
        oi_manifest_v11.json             -- synthetic v11 OI staging manifest
        basis/                           -- A9-F-shaped basis bulk
        basis/manifest.json              -- synthetic staged basis manifest
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    staged = root / "staged"
    bars_dir = staged / "binance_bar_15m"
    perp_dir = staged / "crypto_perpetual_meta"
    funding_dir = staged / "funding_scan_2026"
    funding_long_dir = staged / "funding_20240820_20260821"
    oi_dir = staged / "oi_consolidated"
    basis_dir = staged / "basis"
    for label_dir in (
        bars_dir,
        perp_dir,
        funding_dir,
        funding_long_dir,
        oi_dir,
        basis_dir,
    ):
        label_dir.mkdir(parents=True, exist_ok=True)

    manifest_files: dict[str, dict[str, str]] = {}

    # -- bars ------------------------------------------------------------- #
    # basislv loads a FULL-RANGE 15m grid (columns ts_event+close suffice);
    # oicyc loads runner-needed stamps through the frozen oitd loader, which
    # reads ts_event/open/high/low/close (i128 prices).  ts_event is the bar
    # CLOSE (= the slot-open + 15m convention of the frozen loaders); the
    # full grid covers both consumers.
    bar_start = T0_NS - 7 * DAY_NS
    bar_end = T_END_NS + 8 * BUCKET_NS  # fold-end force-flat slots spill past WINDOW_END
    bar_stamps = np.arange(bar_start, bar_end + BUCKET_NS, BUCKET_NS, dtype=np.int64)
    for sym in FEED_SYMBOLS:
        sym_dir = bars_dir / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
        sym_dir.mkdir(exist_ok=True)
        table = pa.table(
            {
                "ts_event": pa.array(bar_stamps, type=pa.int64()),
                "open": pa.array(
                    [_i128(100.0)] * bar_stamps.shape[0], type=pa.binary()
                ),
                "high": pa.array(
                    [_i128(100.0)] * bar_stamps.shape[0], type=pa.binary()
                ),
                "low": pa.array(
                    [_i128(100.0)] * bar_stamps.shape[0], type=pa.binary()
                ),
                "close": pa.array(
                    [_i128(100.0)] * bar_stamps.shape[0], type=pa.binary()
                ),
            }
        )
        path = sym_dir / "part-0.parquet"
        pq.write_table(table, path)
        manifest_files[str(path.relative_to(staged))] = {
            "sha256": _sha256_file(path)
        }

    # -- perp metadata tick sizes (real-shaped; L-V14-0, no uniform stub) -- #
    for sym in FEED_SYMBOLS:
        sym_dir = perp_dir / f"{sym}-PERP.BINANCE"
        sym_dir.mkdir(exist_ok=True)
        table = pa.table({"price_increment": pa.array([0.01], type=pa.float64())})
        path = sym_dir / "meta.parquet"
        pq.write_table(table, path)
        manifest_files[str(path.relative_to(staged))] = {
            "sha256": _sha256_file(path)
        }

    # -- funding bundles (settlements; COST ONLY) -------------------------- #
    t0 = datetime.fromtimestamp(T0_NS / 1e9, tz=timezone.utc)
    t_end = datetime.fromtimestamp(T_END_NS / 1e9, tz=timezone.utc)
    fund_start = t0 - timedelta(days=7)
    stamps_ms: list[int] = []
    day = fund_start
    while day <= t_end:
        for hour in (0, 8, 16):
            stamp = day.replace(hour=hour, minute=0, second=0, microsecond=0)
            stamps_ms.append(int(stamp.timestamp() * 1000))
        day += timedelta(days=1)
    for sym in FEED_SYMBOLS:
        sym_dir = funding_dir / sym
        sym_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "rows": [
                {"fundingTime": ms, "fundingRate": 0.0001, "markPrice": 100.0}
                for ms in stamps_ms
            ]
        }
        path = sym_dir / "funding.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        manifest_files[str(path.relative_to(staged))] = {
            "sha256": _sha256_file(path)
        }

    # -- staged OI (oicyc; the ONLY OI load path is SHA-verified) ---------- #
    oi_start = t0 - timedelta(days=85)  # >= the frozen 55-row warmup guard
    oi_manifest_symbols: dict[str, dict[str, object]] = {}
    for idx, sym in enumerate(sorted(V14_UNIVERSE)):
        # Alternating +/- daily log growth with a per-symbol phase offset:
        # the leave-one-out aggregate then has STRICTLY positive variance at
        # every stamp (a monotone world would give Var(M) == 0 and fail the
        # frozen complete-cross-section slope closed) and per-symbol slopes
        # are distinct, so ranks and books are deterministic.
        amplitude = 0.01 + 0.001 * idx
        level = 1000.0 * (1.0 + 0.05 * idx)
        times: list[str] = []
        values: list[float] = []
        day = oi_start
        day_idx = 0
        while day <= t_end:
            times.append(day.replace(hour=23, minute=55).strftime("%Y-%m-%d %H:%M:%S"))
            step = amplitude if (day_idx + idx) % 2 == 0 else -amplitude
            level = level * math.exp(step)
            values.append(level)
            day += timedelta(days=1)
            day_idx += 1
        table = pa.table(
            {
                "create_time": pa.array(times, type=pa.string()),
                "sum_open_interest": pa.array(values, type=pa.float64()),
            }
        )
        path = oi_dir / f"{sym}_oi.parquet"
        pq.write_table(table, path)
        manifest_files[str(path.relative_to(staged))] = {
            "sha256": _sha256_file(path)
        }
        oi_manifest_symbols[sym] = {
            "parquet_sha256": _sha256_file(path),
            "days_present": len(times),
        }
    oi_manifest_path = staged / "oi_manifest_v11.json"
    oi_manifest_path.write_text(
        json.dumps(
            {
                "schema": "v11_oi_staging_v1",
                "staging": "synthetic-dry-run",
                "symbols": oi_manifest_symbols,
            }
        ),
        encoding="utf-8",
    )
    manifest_files[str(oi_manifest_path.relative_to(staged))] = {
        "sha256": _sha256_file(oi_manifest_path)
    }

    # -- A9-F-shaped staged basis bulk ------------------------------------- #
    # Rows indexed by bucket CLOSE (open_time_ms + 15m); the neighbour needs
    # 5376 completed buckets before the first stamp, so start 5400 back.
    basis_close_start = T0_NS - 5400 * BUCKET_NS
    basis_close_end = T_END_NS + 96 * BUCKET_NS
    closes = np.arange(
        basis_close_start, basis_close_end + BUCKET_NS, BUCKET_NS, dtype=np.int64
    )
    opens_ms = ((closes - BUCKET_NS) // 1_000_000).astype(np.int64)
    basis_manifest_entries: dict[str, dict[str, object]] = {}
    for idx, sym in enumerate(sorted(V14_UNIVERSE)):
        premium = 0.0005 + 1e-5 * idx  # distinct constant premium per symbol
        index_price = 1000.0
        futures_price = index_price * (1.0 + premium)  # |p_b - basis_rate| == 0
        table = pa.table(
            {
                "open_time_ms": pa.array(opens_ms, type=pa.int64()),
                "futures_price": pa.array(
                    np.full(opens_ms.shape[0], futures_price), type=pa.float64()
                ),
                "index_price": pa.array(
                    np.full(opens_ms.shape[0], index_price), type=pa.float64()
                ),
                "basis_rate": pa.array(
                    np.full(opens_ms.shape[0], premium), type=pa.float64()
                ),
            }
        )
        path = basis_dir / f"{sym}_basis_15m.parquet"
        pq.write_table(table, path)
        manifest_files[str(path.relative_to(staged))] = {
            "sha256": _sha256_file(path)
        }
        basis_manifest_entries[f"basis|{sym}"] = {
            "file": str(path),
            "sha256": _sha256_file(path),
            "bytes": path.stat().st_size,
            "rows": int(opens_ms.shape[0]),
            "expected_buckets": int(opens_ms.shape[0]),
            "missing_buckets": 0,
        }
    basis_manifest_path = basis_dir / "manifest.json"
    basis_manifest_path.write_text(
        json.dumps(
            {
                "schema": "v14_d2_a9f_staged_basis_manifest_v1",
                "synthetic": True,
                "universe": sorted(V14_UNIVERSE),
                "entries": basis_manifest_entries,
            }
        ),
        encoding="utf-8",
    )
    manifest_files[str(basis_manifest_path.relative_to(staged))] = {
        "sha256": _sha256_file(basis_manifest_path)
    }

    # -- the self-describing staged manifest (fail-closed at verify) ------- #
    staged_manifest = staged / "staged_manifest_.json"
    staged_manifest.write_text(
        json.dumps(
            {
                "schema": "v14_synthetic_staged_manifest_v1",
                "files": manifest_files,
            }
        ),
        encoding="utf-8",
    )
    return {
        "staged_root": staged,
        "basis_staged_root": basis_dir,
        "basis_manifest": basis_manifest_path,
        "oi_root": oi_dir,
        "oi_manifest": oi_manifest_path,
    }


@pytest.fixture(scope="module")
def synthetic_world(tmp_path_factory) -> dict[str, Path]:
    return build_synthetic_world(tmp_path_factory.mktemp("v14_driver_synthetic"))


#: The V14 run control dir: no test may ever drop a TECHABORT forensic
#: file into it -- the cancelled lane's strays were exactly that bug.
#: (The committed historical V12/V13 TECHABORT_* evidence files elsewhere
#: under research/control are legitimate artifacts and are not consulted.)
CONTROL_TREE = Path(__file__).resolve().parents[1] / "research" / "control"
V14_CONTROL_DIR = CONTROL_TREE / "v14_run"


def _stray_control_techaborts() -> list[Path]:
    return sorted(V14_CONTROL_DIR.glob("TECHABORT_*.json"))


def run_driver(world: dict[str, Path], out_root: Path, argv: list[str]) -> int:
    base = [
        "--staged-root",
        str(world["staged_root"]),
        "--basis-staged-root",
        str(world["basis_staged_root"]),
        "--basis-manifest",
        str(world["basis_manifest"]),
        "--oi-root",
        str(world["oi_root"]),
        "--oi-manifest",
        str(world["oi_manifest"]),
        "--out-root",
        str(out_root),
        # explicit temp sink; --dry-run would default to <out-root>/TECHABORT
        # (also temp) -- either way nothing ever leaves the scratch tree
        "--techabort-dir",
        str(out_root / "TECHABORT"),
        "--dry-run",
    ]
    return run_v14_cell.main(argv + base)


# --------------------------------------------------------------------------- #
# (a) six-arm construction + pairwise-unique preflight digests
# --------------------------------------------------------------------------- #
def _build_arm(world: dict[str, Path], family: str, arm: str):
    """One frozen arm plugin through the driver registry (importable path)."""
    fam = run_v14_cell.family_registry()[family]
    if family == "basislv_premfade":
        plugin, inputs = fam["build"](
            world["staged_root"],
            arm,
            None,
            synthetic=True,
            basis_staged_root=world["basis_staged_root"],
            basis_manifest_path=world["basis_manifest"],
        )
    else:
        plugin, inputs = fam["build"](
            world["staged_root"],
            arm,
            None,
            synthetic=True,
            oi_root=world["oi_root"],
            oi_manifest_path=world["oi_manifest"],
        )
    return plugin, inputs


@pytest.mark.parametrize("family,arm", SIX_ARMS)
def test_v14drv_six_arms_construct_with_pairwise_unique_digests(
    synthetic_world, family, arm
):
    """All six frozen arms CONSTRUCT on the synthetic root and the driver
    digest pin reports recomputed==recorded, pairwise-unique, 6/6."""
    plugin, inputs = _build_arm(synthetic_world, family, arm)
    assert plugin.identity().arm_id == arm
    assert inputs["tick_sizes"]  # real-shaped perp ticks injected (L-V14-0)
    registry = run_v14_cell.family_registry()
    report = run_v14_cell.verify_all_arm_digests(registry)
    assert report["ok"] is True
    assert report["n_arms"] == 6 and report["n_match"] == 6
    assert report["pairwise_unique"] is True and report["collisions"] == []
    assert report["arms"][arm]["module_digest"] == registry[family]["digest"](arm)
    assert (
        report["arms"][arm]["module_digest"]
        == report["arms"][arm]["recorded_digest"]
    )


def test_v14drv_basislv_preflight_traversal_pin_ok(synthetic_world, tmp_path):
    """basislv arms traverse the FULL preflight (incl. the frozen
    runner-compatibility pin across every matrix cell) -- exit 0."""
    out_root = tmp_path / "out" / "basislv" / BASISLV_ANCHOR
    rc = run_driver(
        synthetic_world,
        out_root,
        ["--family", "basislv_premfade", "--arm", BASISLV_ANCHOR, "--preflight-only"],
    )
    assert rc == run_v14_cell.EXIT_OK
    preflight = json.loads((out_root / "preflight.json").read_text(encoding="utf-8"))
    assert preflight["mode"] == "synthetic_dry_run"
    assert preflight["no_scored_metric_yet"] is True
    pin = preflight["six_arm_digest_pin"]
    assert pin["n_arms"] == 6 and pin["n_match"] == 6 and pin["pairwise_unique"] is True
    assert preflight["runner_traversal_pin"]["ok"] is True
    assert preflight["remediated_kernel"] is True
    assert preflight["staged"]["mode"] == "synthetic"
    assert preflight["staged"]["ok"] is True
    assert preflight["staged"]["files_verified"] == preflight["staged"]["files_expected"]


def test_v14drv_oicyc_traversal_pin_blocked_frozen_conflict(
    synthetic_world, tmp_path
):
    """BLOCKED evidence (recorded, fail-closed pre-metric, ZERO budget):

    The frozen oicyc plugin accepts the drop_one_fold cell at the
    folds-contract probe, but its chained targets_at crashes under ANY
    dropped-fold stress: ``_fold_terminal_stamps(retained_instants)`` calls
    ``fold_assignments``, which refuses when a fold has no retained members
    ("pinned fold F0 received no decision stamps").  The frozen generic
    runner queries targets_at at EVERY open instant -- including a dropped
    fold's stamps -- so the drop_one_fold cell cannot traverse and the
    three oicyc scored cells are BLOCKED until an owner-authorized
    family-side delta (never a driver-side workaround).  This test pins the
    blocked state: when the family delta lands it MUST be flipped to the
    basislv-style exit-0 assertion.
    """
    out_root = tmp_path / "out" / "oicyc" / OICYC_ANCHOR
    rc = run_driver(
        synthetic_world,
        out_root,
        ["--family", "oicyc", "--arm", OICYC_ANCHOR, "--preflight-only"],
    )
    assert rc == run_v14_cell.EXIT_FAIL_CLOSED
    preflight = json.loads((out_root / "preflight.json").read_text(encoding="utf-8"))
    assert preflight["no_scored_metric_yet"] is True
    pin = preflight["runner_traversal_pin"]
    assert pin["ok"] is False and pin["problems"]
    first = pin["problems"][0]
    assert first["cell"] == "drop_one_fold"
    assert "received no decision stamps" in first["error"]
    # construction + digests were fine: the block is traversal-only
    assert preflight["six_arm_digest_pin"]["pairwise_unique"] is True


def test_v14drv_digest_pin_driver_level_values_and_uniqueness(synthetic_world):
    """The driver-level digest report: recomputed == recorded, six distinct."""
    registry = run_v14_cell.family_registry()
    report = run_v14_cell.verify_all_arm_digests(registry)
    assert report["ok"] is True
    assert report["n_arms"] == 6 and report["n_match"] == 6
    assert report["pairwise_unique"] is True
    digests = {arm: entry["module_digest"] for arm, entry in report["arms"].items()}
    assert len(set(digests.values())) == 6
    # the recorded lane-handoff digest values must be among them
    assert (
        digests["CYC-28D"]
        == "0e7b084c4755f63d25fdc2a175123ca78c48bdffb93da962a5e6d0b0875a61b6"
    )
    assert (
        digests["BASISLV-PREMFADE-28D"]
        == "8d7704663b923815e0bb2b201c339c9a2c209875c3348752c721d17265247d52"
    )


def test_v14drv_digest_pin_fails_closed_on_tampered_record(
    synthetic_world, tmp_path, monkeypatch
):
    real_registry = run_v14_cell.family_registry()

    def tampered_registry():
        registry = real_registry
        registry["oicyc"]["recorded_digests"]["CYC-28D"] = "0" * 64
        return registry

    monkeypatch.setattr(run_v14_cell, "family_registry", tampered_registry)
    rc = run_driver(
        synthetic_world,
        tmp_path / "out",
        ["--family", "oicyc", "--arm", "CYC-28D", "--preflight-only"],
    )
    assert rc == run_v14_cell.EXIT_FAIL_CLOSED


# --------------------------------------------------------------------------- #
# (b) cost breakout fields (fills vs holding terms) on scored records
# --------------------------------------------------------------------------- #
def test_v14drv_basislv_scored_record_cost_breakout_and_expectancy_split(
    synthetic_world, tmp_path
):
    out_root = tmp_path / "out" / "basislv" / BASISLV_ANCHOR
    rc = run_driver(
        synthetic_world,
        out_root,
        ["--family", "basislv_premfade", "--arm", BASISLV_ANCHOR],
    )
    assert rc == run_v14_cell.EXIT_OK
    metrics = json.loads(
        (out_root / "baseline_metrics.json").read_text(encoding="utf-8")
    )
    scored = metrics["scored_metrics"]
    assert "cost_fills" in scored and "cost_holding_terms" in scored
    assert scored["remediated_kernel"] is True
    assert scored["cost_holding_terms"] == 0.0
    assert scored["cost_fills"] > 0.0
    assert scored["cost_total"] == pytest.approx(scored["cost_fills"], abs=1e-12)
    split = metrics["expectancy_split"]
    assert split["price_only_expectancy"] == scored["price_only_expectancy"]
    assert split["total_expectancy"] == scored["total_expectancy"]
    assert "funding_credit_sum" in split
    # fold-sign vectors recorded for the family gate
    assert len(metrics["fold_signs"]["fold_positive"]) == 3


def test_v14drv_oicyc_scored_record_cost_breakout(synthetic_world):
    """The remediated-kernel cost breakout (cost_fills / cost_holding_terms,
    holding terms EXACTLY 0 by construction, remediated_kernel=true) is part
    of the scored record for EVERY family: the record builder is
    family-independent, so the oicyc record carries the same fields (the
    full oicyc matrix itself is BLOCKED, see the traversal-pin evidence
    test; the basislv full-path tests pin the end-to-end assertion)."""
    baseline = {
        "daily_returns": [
            {
                "decision_ns": T0_NS + day * DAY_NS,
                "fold_index": day % 3,
                "price_pnl_per_unit": 0.001,
                "funding_cashflow_per_unit": 0.00005,
                "cost_charged_per_unit": 0.0002 if day in (0, 3) else 0.0,
                "net_return_per_unit": 0.00085 if day in (0, 3) else 0.00105,
            }
            for day in range(6)
        ],
        "books": [
            {
                "decision_ns": T0_NS + day * DAY_NS,
                "carried_forward": day in (1, 2, 4, 5),
                "weights": [],
            }
            for day in range(6)
        ],
        "positions": [],
        "portfolio_metrics": {
            "n_days_with_records": 6,
            "net_return_sum": 0.0058,
            "expectancy_per_day": 0.0010,
            "max_drawdown": 0.0005,
            "position_pf": 1.5,
            "price_pnl_sum": 0.006,
            "funding_sum": 0.0003,
            "cost_charged_sum": 0.0004,
        },
    }
    plugin, _inputs = _build_arm(synthetic_world, "oicyc", OICYC_ANCHOR)
    assert plugin.identity().arm_id == OICYC_ANCHOR
    scored = run_v14_cell.scored_metrics_from_baseline(baseline)
    assert scored["remediated_kernel"] is True
    assert "cost_fills" in scored and "cost_holding_terms" in scored
    assert scored["cost_holding_terms"] == 0.0
    assert scored["cost_fills"] == pytest.approx(0.0004, abs=1e-12)
    assert scored["score_valid"] is True


# --------------------------------------------------------------------------- #
# (c) dry-run refuses any scored ledger
# --------------------------------------------------------------------------- #
def test_v14drv_dry_run_writes_no_ledger(synthetic_world, tmp_path):
    out_root = tmp_path / "out" / "basislv" / BASISLV_NEIGHBOUR
    rc = run_driver(
        synthetic_world,
        out_root,
        ["--family", "basislv_premfade", "--arm", BASISLV_NEIGHBOUR],
    )
    assert rc == run_v14_cell.EXIT_OK
    ledgers = [
        p
        for p in out_root.rglob("*")
        if p.suffix in (".jsonl", ".ledger") or "ledger" in p.name
    ]
    assert ledgers == []
    assert not (out_root / "publish_record.json").exists()
    assert not (out_root / "cell_summary.json").exists()
    # no ledger anywhere in the scratch tree rooted at tmp_path
    assert list(tmp_path.rglob("*.jsonl")) == []


def test_v14drv_dry_run_refuses_publish_and_missing_out_root(synthetic_world, tmp_path):
    base = [
        "--staged-root",
        str(synthetic_world["staged_root"]),
        "--basis-staged-root",
        str(synthetic_world["basis_staged_root"]),
        "--basis-manifest",
        str(synthetic_world["basis_manifest"]),
        "--oi-root",
        str(synthetic_world["oi_root"]),
        "--oi-manifest",
        str(synthetic_world["oi_manifest"]),
        "--family",
        "oicyc",
        "--arm",
        "CYC-14D",
        "--dry-run",
    ]
    # publish refused outright under --dry-run
    assert (
        run_v14_cell.main(
            base
            + [
                "--out-root",
                str(tmp_path / "o"),
                "--publish",
                "--ledger",
                str(tmp_path / "l.jsonl"),
                "--expect-head",
                "x",
            ]
        )
        == run_v14_cell.EXIT_FAIL_CLOSED
    )
    # ledger flag refused outright under --dry-run
    assert (
        run_v14_cell.main(
            base + ["--out-root", str(tmp_path / "o"), "--ledger",
                    str(tmp_path / "l.jsonl")]
        )
        == run_v14_cell.EXIT_FAIL_CLOSED
    )
    # an explicit scratch out-root is REQUIRED (default results tree refused)
    assert run_v14_cell.main(base) == run_v14_cell.EXIT_FAIL_CLOSED


# --------------------------------------------------------------------------- #
# (d) oicyc CONFIRMATORY carry-through into the scored record
# --------------------------------------------------------------------------- #
def test_v14drv_oicyc_records_carry_confirmatory_metadata(
    synthetic_world,
):
    """The driver's scored-record extension embeds the plugin's CONFIRMATORY
    block (plan Section 1.1) into the scored record -- confirmatory_status
    AND the denominator note -- for EVERY oicyc arm (the extension is
    family-keyed and applied identically to anchor/neighbour/control; the
    full oicyc matrix itself is BLOCKED, see the traversal-pin evidence
    test)."""
    fabricated_baseline = {
        "daily_returns": [
            {
                "decision_ns": T0_NS + day * DAY_NS,
                "fold_index": day % 3,
                "net_return_per_unit": 0.001 if day % 3 else -0.0005,
            }
            for day in range(6)
        ],
        "portfolio_metrics": {
            "n_days_with_records": 6,
            "price_pnl_sum": 0.003,
            "funding_sum": 0.0001,
            "cost_charged_sum": 0.0002,
        },
    }
    for family, arm in SIX_ARMS:
        if family != "oicyc":
            continue
        plugin, _inputs = _build_arm(synthetic_world, family, arm)
        result = {"scored_metrics": {}}
        signs, split, confirmatory = run_v14_cell.apply_family_scored_record_extensions(
            family=family,
            plugin=plugin,
            result=result,
            baseline=fabricated_baseline,
        )
        scored = result["scored_metrics"]
        assert scored["confirmatory_status"] == "CONFIRMATORY"
        assert "denominator" in scored["denominator_note"]
        assert "CONFIRMATORY" in scored["denominator_note"]
        assert confirmatory["scored_status"] == "CONFIRMATORY"
        assert confirmatory["control_never_promotable"] is True
        assert confirmatory["gates_unrelaxed"] is True
        assert "CONFIRMATORY" in json.dumps(confirmatory)
        assert len(signs["fold_positive"]) == 3


# --------------------------------------------------------------------------- #
# (e) basislv gate-input contract (missing clause inputs => BLOCKED)
# --------------------------------------------------------------------------- #
def test_v14drv_gate_missing_clause_inputs_blocked_not_pass():
    verdict = evaluate_family_gate(
        anchor_fold_positive=[True, True, True],
        control_fold_positive=[False, False, False],
        neighbour_fold_positive=[True, True, True],
        price_only_expectancy=None,
        total_expectancy=None,
    )
    assert verdict["verdict"] == VERDICT_BLOCKED_CLAUSE_INPUTS


def test_v14drv_anchor_gate_blocked_while_siblings_missing(synthetic_world, tmp_path):
    out_root = tmp_path / "out" / "basislv" / BASISLV_ANCHOR
    rc = run_driver(
        synthetic_world,
        out_root,
        ["--family", "basislv_premfade", "--arm", BASISLV_ANCHOR],
    )
    assert rc == run_v14_cell.EXIT_OK
    gate = json.loads((out_root / "gate_record.json").read_text(encoding="utf-8"))
    assert gate["verdict"] == "BLOCKED_SIBLING_EVIDENCE_MISSING"
    assert gate["verdict"] != "FAMILY_ADVANCES_TO_STAGE_A"
    assert BASISLV_CONTROL in gate["missing_inputs"]
    assert BASISLV_NEIGHBOUR in gate["missing_inputs"]
    # the anchor's REQUIRED clause inputs were computed and carried anyway
    assert gate["expectancy_split"]["price_only_expectancy"] is not None
    assert gate["expectancy_split"]["total_expectancy"] is not None


def test_v14drv_anchor_gate_evaluates_with_sibling_evidence_and_clause_inputs(
    synthetic_world, tmp_path
):
    family_out = tmp_path / "out" / "basislv"
    for arm in (BASISLV_CONTROL, BASISLV_NEIGHBOUR):
        rc = run_driver(
            synthetic_world,
            family_out / arm,
            ["--family", "basislv_premfade", "--arm", arm, "--preflight-only"],
        )
        assert rc == run_v14_cell.EXIT_OK
        # preflight-only does not produce a scored record; simulate the
        # sibling evidence the driver itself writes after a scored run.
        (family_out / arm / "baseline_metrics.json").write_text(
            json.dumps({"fold_signs": {"fold_positive": [False, False, False]}}),
            encoding="utf-8",
        )
    anchor_out = family_out / BASISLV_ANCHOR
    rc = run_driver(
        synthetic_world,
        anchor_out,
        ["--family", "basislv_premfade", "--arm", BASISLV_ANCHOR],
    )
    assert rc == run_v14_cell.EXIT_OK
    gate = json.loads((anchor_out / "gate_record.json").read_text(encoding="utf-8"))
    assert gate["missing_inputs"] == []
    assert gate["price_only_clause_inputs_supplied"] is True
    # a real frozen verdict was reached (never BLOCKED, never an inferred PASS)
    assert gate["verdict"] in GATE_PASS_VERDICTS


# --------------------------------------------------------------------------- #
# (f) TECHABORT hook: injected pre-metric crash, zero budget effect, temp-only
# --------------------------------------------------------------------------- #
def test_v14drv_techabort_fires_on_injected_crash_with_zero_budget(
    synthetic_world, tmp_path, monkeypatch
):
    assert _stray_control_techaborts() == []  # pre-state: control tree clean
    techabort_dir = tmp_path / "forensics"

    def inject(*_args, **_kwargs):
        raise RuntimeError("injected pre-metric crash (driver test)")

    monkeypatch.setattr(run_v14_cell, "compute_cell", inject)
    with pytest.raises(SystemExit) as excinfo:
        run_v14_cell.main(
            [
                "--family",
                "basislv_premfade",
                "--arm",
                BASISLV_ANCHOR,
                "--staged-root",
                str(synthetic_world["staged_root"]),
                "--basis-staged-root",
                str(synthetic_world["basis_staged_root"]),
                "--basis-manifest",
                str(synthetic_world["basis_manifest"]),
                "--oi-root",
                str(synthetic_world["oi_root"]),
                "--oi-manifest",
                str(synthetic_world["oi_manifest"]),
                "--out-root",
                str(tmp_path / "out" / "crash"),
                "--techabort-dir",
                str(techabort_dir),
                "--dry-run",
            ]
        )
    assert excinfo.value.code == run_v14_cell.EXIT_CRASH
    forensic = techabort_dir / f"TECHABORT_{BASISLV_ANCHOR}.json"
    assert forensic.is_file()
    payload = json.loads(forensic.read_text(encoding="utf-8"))
    assert payload["schema"] == "v14_techabort_forensic_v1"
    assert payload["phase"].startswith("pre-metric")
    assert payload["scored_metric_computed"] is False
    assert "ZERO budget" in payload["budget_effect"]
    assert payload["crash"]["type"] == "RuntimeError"
    assert "injected" in payload["crash"]["message"]
    assert payload["fix_path"].startswith("driver-only")
    assert payload["ledger_state"]["ledger_exists"] is False
    # the ONLY forensic file is the temp one: the control tree stays clean
    # and no scored ledger exists anywhere in the scratch tree
    assert _stray_control_techaborts() == []
    assert list(tmp_path.rglob("*.jsonl")) == []


def test_v14drv_dry_run_refuses_techabort_sink_under_control_tree(
    synthetic_world, tmp_path
):
    """The structural fix: a synthetic run can never sink TECHABORT
    forensics into a research/control subtree (the cancelled lane's six
    stray control-tree files were exactly that bug)."""
    rc = run_v14_cell.main(
        [
            "--family",
            "oicyc",
            "--arm",
            "CTL-OISHARE",
            "--staged-root",
            str(synthetic_world["staged_root"]),
            "--oi-root",
            str(synthetic_world["oi_root"]),
            "--oi-manifest",
            str(synthetic_world["oi_manifest"]),
            "--out-root",
            str(tmp_path / "out"),
            "--techabort-dir",
            str(CONTROL_TREE / "v14_run"),
            "--dry-run",
        ]
    )
    assert rc == run_v14_cell.EXIT_FAIL_CLOSED
    assert _stray_control_techaborts() == []


# --------------------------------------------------------------------------- #
# Auxiliary: the synthetic world respects the frozen calendars it must cover
# --------------------------------------------------------------------------- #
def test_v14drv_synthetic_covers_frozen_calendars(synthetic_world):
    instants = list(oicyc_calendar()) + list(oicyc_fold_ends())
    needed = {
        int(instant) + k * BUCKET_NS for instant in instants for k in range(-1, 5)
    }
    bar_start = T0_NS - 7 * DAY_NS
    bar_end = T_END_NS + 8 * BUCKET_NS
    assert min(needed) >= bar_start and max(needed) <= bar_end
    assert synthetic_world["basis_staged_root"].is_dir()
    assert synthetic_world["oi_manifest"].is_file()
