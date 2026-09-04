"""V13R scored-cell driver tests (hand-computed fixtures; no real data).

Covers the owner-mandated driver gates, mirroring tests/test_v12r_driver.py:

* 6/6 frozen arm-config digests recompute from the frozen V13 identity
  modules and match ``research/control/v13_run/w13_freeze.json`` (W1
  c0d0673); a tampered freeze fails the pin (fail-closed);
* flag-combination validation (no publish without ledger/pin; repro never
  publishes; compare-with only with repro);
* the funding-bundle reader mirrors the frozen OITD
  ``load_marks_and_settlements`` row mapping with an explicit root
  (hand-computed funding bundle; the ONE loader without a root parameter);
* scored-metric extraction carries REAL decision/fill evidence;
* staged-snapshot pin (frozen digest + a3-authority inventory equality +
  90/90 per-file sha256) fails closed on every corruption;
* end-to-end synthetic frames through the REAL adapter path for BOTH
  families: family contract derivation, baseline-only scoring, exactly-once
  publication (published +1), idempotent replay (zero delta), zero-position
  refusal (observed +1 on a scratch ledger), repro exact-match comparison
  (ALL_MATCH; perturbation detected as MISMATCH);
* frozen-mechanism sanity through the driver path: the OITD causal control
  is constructed WITHOUT the OI/mark bundles and its signal layer refuses
  them; the LIQEPIS SIGN-INV control negates the anchor book exactly;
* driver-level main() behavior: preflight-only writes pins with no scored
  metric, no ledger write ever happens without --publish, publish writes
  exactly one row then replays idempotently, and --repro matches the
  execution evidence (exit 0) or reports MISMATCH (exit 6).
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import research.adapter_v10  # noqa: F401  (import-order contract)

from research.adapter_v10.hashes import payload_sha256  # noqa: E402
from research.v12.accounting import (  # noqa: E402
    REFUSED_ZERO_POSITIONS,
    STAGE_IDEMPOTENT_REPLAY,
    STAGE_PUBLISHED,
    STAGE_REFUSED,
    publish_v12_cell,
    v12_denominator_view,
)

driver = importlib.import_module("research.control.v13_run.tools.run_v13_cell")

FREEZE = json.loads(
    (REPO_ROOT / "research" / "control" / "v13_run" / "w13_freeze.json").read_text(
        encoding="utf-8"
    )
)
FROZEN_DIGESTS = {
    arm: digest
    for arm, digest in FREEZE["arm_config_digests"].items()
    if arm != "pairwise_unique"
}

ALL_SIX_ARMS = tuple(sorted(FROZEN_DIGESTS))

DAY_NS = 86_400_000_000_000
BAR_NS = 900_000_000_000


# --------------------------------------------------------------------------- #
# 6/6 frozen digest equality (the driver's fail-closed pin)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("arm_id", ALL_SIX_ARMS)
def test_six_arm_digests_recompute_and_match_freeze(arm_id: str) -> None:
    registry = driver.family_registry()
    family = next(name for name in registry if arm_id in registry[name]["arms"])
    assert registry[family]["digest"](arm_id) == FROZEN_DIGESTS[arm_id]
    assert registry[family]["recorded_digests"][arm_id] == FROZEN_DIGESTS[arm_id]


def test_verify_all_arm_digests_pass_and_tamper(tmp_path: Path) -> None:
    registry = driver.family_registry()
    freeze_path = REPO_ROOT / "research" / "control" / "v13_run" / "w13_freeze.json"
    report = driver.verify_all_arm_digests(registry, freeze_path)
    assert report["ok"] is True
    assert report["n_arms"] == 6 and report["n_match"] == 6
    assert report["freeze_extra_keys"] == ["pairwise_unique"]

    tampered = json.loads(freeze_path.read_text(encoding="utf-8"))
    tampered["arm_config_digests"]["OITD-28D"] = "0" * 64
    bad = tmp_path / "w13_freeze.json"
    bad.write_text(json.dumps(tampered), encoding="utf-8")
    bad_report = driver.verify_all_arm_digests(registry, bad)
    assert bad_report["ok"] is False
    assert bad_report["arms"]["OITD-28D"]["match"] is False
    assert sum(1 for v in bad_report["arms"].values() if v.get("match")) == 5

    missing = json.loads(freeze_path.read_text(encoding="utf-8"))
    del missing["arm_config_digests"]["LIQEPIS-56D"]
    bad2 = tmp_path / "w13_freeze_missing.json"
    bad2.write_text(json.dumps(missing), encoding="utf-8")
    missing_report = driver.verify_all_arm_digests(registry, bad2)
    assert missing_report["ok"] is False
    assert "error" in missing_report["arms"]["LIQEPIS-56D"]


def test_driver_rejects_arm_outside_freeze() -> None:
    registry = driver.family_registry()
    for family in ("oitd", "liqepis"):
        with pytest.raises(ValueError):
            registry[family]["build"](Path("unused"), "NOT-A-FROZEN-ARM")


# --------------------------------------------------------------------------- #
# Flag-combination validation
# --------------------------------------------------------------------------- #
def _args(**overrides):
    argv = ["--family", "oitd", "--arm", "OITD-28D"]
    for key, value in overrides.items():
        flag = "--" + key.replace("_", "-")
        if value is True:
            argv.append(flag)
        elif value is not False:
            argv.extend([flag, str(value)])
    return driver.parse_args(argv)


def test_validate_args_flag_combinations() -> None:
    assert driver.validate_args(_args()) is None
    assert "requires --ledger" in driver.validate_args(
        _args(publish=True, expect_head="a" * 40)
    )
    assert "expect-head" in driver.validate_args(_args(publish=True, ledger="l.jsonl"))
    assert "--repro must never write" in driver.validate_args(
        _args(repro=True, publish=True, ledger="l.jsonl", expect_head="a" * 40)
    )
    assert "only valid together with --repro" in driver.validate_args(
        _args(compare_with="somewhere")
    )
    bad_family = _args()
    bad_family.family = "oilev_v2"  # argparse choices also reject this earlier
    assert driver.validate_args(bad_family) is not None


# --------------------------------------------------------------------------- #
# Funding-bundle reader: hand-computed mirror of the frozen OITD loader
# --------------------------------------------------------------------------- #
def test_load_marks_and_settlements_root_hand_computed(tmp_path: Path) -> None:
    root = tmp_path / "funding_scan_2026"
    (root / "AAAUSDT").mkdir(parents=True)
    (root / "BBBUSDT").mkdir(parents=True)
    (root / "AAAUSDT" / "funding.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "fundingTime": 1_800_000_500,
                        "fundingRate": "0.0001",
                        "markPrice": "111.5",
                    },
                    {
                        "fundingTime": 900_000_000,
                        "fundingRate": "-0.00025",
                        "markPrice": "110.25",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    marks, settlements = driver.load_marks_and_settlements_root(
        root, ["AAAUSDT", "BBBUSDT", "CCCUSDT"]
    )
    # hand-computed: ms -> ns (x1e6), sorted ascending; missing -> empty
    assert marks["AAAUSDT"] == ((900_000_000_000_000, 110.25), (1_800_000_500_000_000, 111.5))
    assert settlements["AAAUSDT"] == (
        {"publish_ts_ns": 900_000_000_000_000, "value": -0.00025},
        {"publish_ts_ns": 1_800_000_500_000_000, "value": 0.0001},
    )
    assert marks["BBBUSDT"] == () and settlements["BBBUSDT"] == ()
    assert marks["CCCUSDT"] == () and settlements["CCCUSDT"] == ()

    # a missing markPrice is a hard error (the A9-F staged mark root)
    (root / "BBBUSDT" / "funding.json").write_text(
        json.dumps({"rows": [{"fundingTime": 900_000_000, "fundingRate": "0.0001"}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="markPrice"):
        driver.load_marks_and_settlements_root(root, ["BBBUSDT"])

    # duplicate stamps are a hard error, never silently deduplicated
    (root / "CCCUSDT").mkdir()
    (root / "CCCUSDT" / "funding.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "fundingTime": 900_000_000,
                        "fundingRate": "0.0001",
                        "markPrice": "1.0",
                    },
                    {
                        "fundingTime": 900_000_000,
                        "fundingRate": "0.0002",
                        "markPrice": "1.0",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        driver.load_marks_and_settlements_root(root, ["CCCUSDT"])


# --------------------------------------------------------------------------- #
# Scored-metric extraction carries real evidence
# --------------------------------------------------------------------------- #
def test_scored_metrics_extraction_hand_computed() -> None:
    baseline = {
        "portfolio_metrics": {
            "net_return_sum": 0.25,
            "expectancy_per_day": 0.005,
            "max_drawdown": 0.04,
            "n_positions": 2,
        },
        "positions": [
            {"symbol": "AAAUSDT", "entry_ns": 111},
            {"symbol": "BBBUSDT", "entry_ns": 222},
        ],
        "books": [
            {
                "decision_ns": 1000,
                "status": "OPEN_REBALANCE",
                "weights": [["AAAUSDT", 0.3], ["BBBUSDT", -0.3]],
            },
            {"decision_ns": 2000, "status": "OPEN_CARRIED_FORWARD", "weights": []},
        ],
    }
    scored = driver.scored_metrics_from_baseline(baseline)
    assert scored["score_valid"] is True
    assert scored["net_return_sum"] == 0.25
    assert scored["expectancy_per_day"] == 0.005
    assert scored["max_drawdown"] == 0.04
    assert scored["n_positions"] == 2
    assert scored["n_fills"] == 2
    assert scored["n_decisions"] == 2  # only non-zero book weights count
    assert {"symbol": "AAAUSDT", "decision_ts": 1000} in scored["decisions"]
    assert {"symbol": "BBBUSDT", "ts_ns": 222} in scored["fills"]

    broken = dict(baseline)
    broken["portfolio_metrics"] = {
        "net_return_sum": None,
        "expectancy_per_day": 0.005,
        "max_drawdown": 0.04,
    }
    assert driver.scored_metrics_from_baseline(broken)["score_valid"] is False


def test_series_digest_mapping_branch_regression() -> None:
    """TECHABORT regression carried from V12R: encode AFTER concat."""
    rows = {"AAAUSDT": ({"publish_ts_ns": 900_000_000_000, "value": -0.00025},)}
    first = driver._series_digest(rows)
    second = driver._series_digest(
        {"AAAUSDT": ({"value": -0.00025, "publish_ts_ns": 900_000_000_000},)}
    )
    assert first == second  # key-order independent
    assert driver._series_digest({"AAAUSDT": ({"publish_ts_ns": 1, "value": 0.0},)}) != first


def test_fusion_series_digest_deterministic() -> None:
    from research.v13.families.liqepis.strategy import BAR_INTERVAL_NS, FusionBarSeries

    def make(price: float, volume: float) -> FusionBarSeries:
        n = 97
        grid = 2 * BAR_INTERVAL_NS + np.arange(n, dtype=np.int64) * BAR_INTERVAL_NS
        close = np.full(n, price, dtype=np.float64)
        vol = np.full(n, volume, dtype=np.float64)
        return FusionBarSeries(
            origin_ns=2 * BAR_INTERVAL_NS,
            close=close,
            volume=vol,
            available_ns=grid,
            _q_cache=close * vol,
        )

    first = driver.fusion_series_digest({"AAAUSDT": make(2.0, 100.0)})
    second = driver.fusion_series_digest({"AAAUSDT": make(2.0, 100.0)})
    assert first == second  # deterministic across recompute
    assert driver.fusion_series_digest({"AAAUSDT": make(2.0, 101.0)}) != first
    assert driver.fusion_series_digest({"AAAUSDT": make(3.0, 100.0)}) != first


# --------------------------------------------------------------------------- #
# Staged snapshot pin (frozen digest + a3 authority + 90/90 per-file sha256)
# --------------------------------------------------------------------------- #
def _staged_fixture_files(tmp_path: Path) -> dict[str, Path]:
    """Exactly 90 tiny staged files across the five frozen labels (18 each)."""
    files: dict[str, Path] = {}
    per_label = driver.STAGED_FILES_EXPECTED // len(driver.STAGED_LABELS)
    for label in driver.STAGED_LABELS:
        for k in range(per_label):
            sub = tmp_path / "staged" / label / f"sym{k:02d}"
            sub.mkdir(parents=True, exist_ok=True)
            path = sub / "probe.bin"
            path.write_bytes(f"{label[:3]}{k:02d}".encode())
            files[f"{label}/sym{k:02d}/probe.bin"] = path
    assert len(files) == driver.STAGED_FILES_EXPECTED
    return files


def _write_staged_manifest(staged: Path, files: dict[str, Path]) -> Path:
    manifest = staged / driver.STAGED_MANIFEST_NAME
    payload = {
        "schema": "v12_staged_manifest_v1",
        "files_count": len(files),
        "files": {
            rel: {"sha256": driver.sha256_file(path), "bytes": path.stat().st_size}
            for rel, path in files.items()
        },
    }
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_verify_staged_snapshot_pass_and_fail_closed(tmp_path: Path) -> None:
    staged = tmp_path / "staged"
    files = _staged_fixture_files(tmp_path)
    manifest = _write_staged_manifest(staged, files)
    authority = {
        rel: {"sha256": driver.sha256_file(path), "bytes": path.stat().st_size}
        for rel, path in files.items()
    }

    good = driver.verify_staged_snapshot(staged, driver.sha256_file(manifest), authority)
    assert good["ok"] is True
    assert good["files_verified"] == len(files)

    wrong_digest = driver.verify_staged_snapshot(staged, "f" * 64, authority)
    assert wrong_digest["ok"] is False
    assert any("mismatch" in p for p in wrong_digest["problems"])

    # inventory drift vs the committed a3 authority
    drifted_authority = dict(authority)
    drifted_authority[f"{driver.STAGED_OI}/extra.bin"] = {"sha256": "0" * 64}
    drifted = driver.verify_staged_snapshot(staged, driver.sha256_file(manifest), drifted_authority)
    assert drifted["ok"] is False
    assert any("authority" in p for p in drifted["problems"])

    # a staged file missing / corrupted is caught by the 90/90 sha256 sweep
    (staged / driver.STAGED_OI / "sym00" / "probe.bin").unlink()
    missing = driver.verify_staged_snapshot(staged, driver.sha256_file(manifest), authority)
    assert missing["ok"] is False
    assert any("staged file missing" in p for p in missing["problems"])

    (staged / driver.STAGED_OI / "sym00").mkdir(parents=True, exist_ok=True)
    (staged / driver.STAGED_OI / "sym00" / "probe.bin").write_bytes(b"zzz")
    corrupted = driver.verify_staged_snapshot(staged, driver.sha256_file(manifest), authority)
    assert corrupted["ok"] is False
    assert any("sha256 mismatch" in p for p in corrupted["problems"])

    # missing manifest and missing subtree both fail closed
    bare = driver.verify_staged_snapshot(tmp_path / "nope", "0" * 64, authority)
    assert bare["ok"] is False
    assert any("staged manifest missing" in p for p in bare["problems"])
    assert any("staged subtree missing" in p for p in bare["problems"])


# --------------------------------------------------------------------------- #
# Synthetic OITD frame: deterministic turnover/OI/marks/bars (pipeline only)
# --------------------------------------------------------------------------- #
def _synthetic_oitd_data() -> dict[str, Any]:
    from datetime import datetime, timedelta, timezone

    from research.v11.families.oilever_delev.strategy import Bar
    from research.v13.families.oitd.audits import (
        fold_end_instants,
        tradeable_universe_symbols,
    )
    from research.v13.families.oitd.strategy import (
        WINDOW_END_ISO,
        WINDOW_START_ISO,
        parse_iso_utc,
        stamp_calendar,
    )

    instants = list(stamp_calendar()) + list(fold_end_instants())
    universe = tradeable_universe_symbols()
    symbols = tuple(sorted(set(universe) | {"BTCUSDT"}))

    start_ns = parse_iso_utc(WINDOW_START_ISO)
    end_ns = parse_iso_utc(WINDOW_END_ISO)
    start_day = datetime.fromtimestamp(start_ns // 10**9, tz=timezone.utc)
    end_day = datetime.fromtimestamp(end_ns // 10**9, tz=timezone.utc)
    n_days = (end_day - start_day).days

    def day_index(offset: int) -> int:
        return int((start_day + timedelta(days=offset)).timestamp()) // 86_400

    # daily turnover buckets: every day of the span + the 57d/56d warmup
    turnover: dict[str, dict[int, float]] = {}
    for index, sym in enumerate(universe):
        base = 10_000.0 + 977.0 * index
        turnover[sym] = {
            day_index(offset): base * (1.0 + 0.01 * ((offset % 11) - 5))
            for offset in range(-60, n_days + 3)
        }

    # daily OI + marks rows (distinct levels per symbol)
    oi: dict[str, tuple[tuple[int, float], ...]] = {}
    marks: dict[str, tuple[tuple[int, float], ...]] = {}
    for index, sym in enumerate(universe):
        oi_base = 1_000.0 + 13.0 * index
        mark_base = 2.0 + 0.5 * index
        oi_rows = []
        mark_rows = []
        for offset in range(-15, n_days + 3):
            day = start_day + timedelta(days=offset)
            oi_rows.append(
                (int(day.timestamp()) * 10**9, oi_base * (1.0 + 0.001 * (offset % 7)))
            )
            mark_rows.append(
                (
                    (int(day.timestamp()) + 23 * 3_600) * 10**9,
                    mark_base * (1.0 + 0.0001 * (offset % 5)),
                )
            )
        oi[sym] = tuple(sorted(oi_rows))
        marks[sym] = tuple(sorted(mark_rows))

    # execution/valuation bars around every schedule instant + fold boundary
    bars: dict[str, tuple[Bar, ...]] = {}
    for sym in symbols:
        price = 2.0 + 0.5 * symbols.index(sym)
        seq: list[Bar] = []
        for instant in instants:
            for k in range(1, 6):  # covering bar + strictly-later fill slots
                seq.append(
                    Bar(
                        ts_event_ns=instant + k * BAR_NS,
                        open=price,
                        high=price,
                        low=price,
                        close=price,
                    )
                )
        bars[sym] = tuple(sorted(seq, key=lambda b: b.ts_event_ns))

    settlements: dict[str, tuple[dict[str, Any], ...]] = {
        sym: tuple(
            {"publish_ts_ns": start_ns + 8 * 3_600 * 10**9 * k, "value": 0.0001}
            for k in range(1, 400)
        )
        for sym in universe
    }
    ticks = {sym: 0.01 for sym in symbols}
    return {
        "turnover": turnover,
        "oi": oi,
        "marks": marks,
        "bars": bars,
        "settlements": settlements,
        "ticks": ticks,
    }


def _oitd_plugin(arm_id: str, frame: dict[str, Any]):
    from research.v13.families.oitd.plugin import OitdPlugin

    is_control = arm_id == "CTL-FLOW-ONLY"
    return OitdPlugin(
        arm_id=arm_id,
        day_turnover_by_symbol=frame["turnover"],
        bars_by_symbol=frame["bars"],
        oi_by_symbol=None if is_control else frame["oi"],
        mark_by_symbol=None if is_control else frame["marks"],
        settlements_by_symbol=frame["settlements"],
        tick_sizes=frame["ticks"],
    )


@pytest.fixture(scope="module")
def oitd_frame() -> dict[str, Any]:
    return _synthetic_oitd_data()


# --------------------------------------------------------------------------- #
# Synthetic LIQEPIS frame: dense fusion bar grid (pipeline only)
# --------------------------------------------------------------------------- #
def _synthetic_liqepis_series() -> dict[str, Any]:
    from research.v13.families.liqepis.audits import tradeable_universe_symbols
    from research.v13.families.liqepis.strategy import (
        BAR_INTERVAL_NS,
        FIRST_STAMP_ISO,
        FusionBarSeries,
        WINDOW_END_ISO,
        parse_iso_utc,
    )

    universe = tradeable_universe_symbols()
    symbols = tuple(sorted(set(universe) | {"BTCUSDT"}))
    origin = parse_iso_utc(FIRST_STAMP_ISO) - 56 * DAY_NS
    end_ns = parse_iso_utc(WINDOW_END_ISO)
    n_slots = (end_ns - origin) // BAR_INTERVAL_NS + 1
    grid = origin + np.arange(n_slots, dtype=np.int64) * BAR_INTERVAL_NS

    series: dict[str, FusionBarSeries] = {}
    for index, sym in enumerate(symbols):
        price = 2.0 + 0.5 * index
        volume = 100.0 + 7.0 * index
        # one burst slot per UTC day at a symbol-specific offset: distinct
        # episodicity H per symbol (H is scale-invariant, amplitude is not)
        burst = (np.arange(n_slots) % 96) == (index % 96)
        close = np.full(n_slots, price, dtype=np.float64)
        vol = np.where(burst, volume * (1.5 + 0.1 * index), volume)
        series[sym] = FusionBarSeries(
            origin_ns=int(origin),
            close=close,
            volume=vol,
            available_ns=grid.copy(),
            _q_cache=close * vol,
        )
    return {"series": series, "universe": universe, "symbols": symbols}


def _liqepis_plugin(arm_id: str, frame: dict[str, Any]):
    from research.v13.families.liqepis.plugin import LiqepisPlugin

    return LiqepisPlugin(
        arm_id=arm_id,
        bars_by_symbol=frame["series"],
        tick_sizes={sym: 0.01 for sym in frame["symbols"]},
    )


@pytest.fixture(scope="module")
def liqepis_frame() -> dict[str, Any]:
    return _synthetic_liqepis_series()


# --------------------------------------------------------------------------- #
# End-to-end synthetic publication path (LIQEPIS anchor traverses the frozen
# generic adapter fully; the OITD frozen conflict is pinned separately below)
# --------------------------------------------------------------------------- #
def test_liqepis_end_to_end_publish_replay_refusal(
    tmp_path: Path, liqepis_frame
) -> None:
    plugin = _liqepis_plugin("LIQEPIS-28D", liqepis_frame)
    result = driver.compute_cell(
        family="liqepis",
        arm_id="LIQEPIS-28D",
        plugin=plugin,
        out_dir=tmp_path / "liq_exec",
    )
    assert result["matrix_cells"][0] == "baseline"
    assert len(result["matrix_cells"]) == 6  # every accepted matrix cell recorded
    assert result["universe"] == sorted(liqepis_frame["universe"])
    scored = result["scored_metrics"]
    assert scored["score_valid"] is True
    assert scored["n_positions"] > 0
    assert scored["n_fills"] == scored["n_positions"]
    assert scored["n_decisions"] > 0

    identity = plugin.identity()
    digest = driver.family_registry()["liqepis"]["digest"]("LIQEPIS-28D")
    ledger = tmp_path / "ledger_liqepis.jsonl"
    common = dict(
        strategy_id=identity.strategy_id,
        family=identity.family_id,
        arm_id="LIQEPIS-28D",
        arm_config_digest=digest,
        stress_signature=plugin.baseline_stress().signature(),
        window_start_iso=identity.window_start_iso,
        window_end_iso=identity.window_end_iso,
        family_contract_cells=result["contract"],
        producer_head_sha="0" * 40,
    )
    first = publish_v12_cell(
        scored_metrics=scored,
        result_sha256=str(result["baseline_run"]["hashes"]["result_sha256"]),
        ledger_path=ledger,
        **common,
    )
    assert first["stage"] == STAGE_PUBLISHED
    assert first["published_delta"] == 1 and first["observed_delta"] == 0

    replay = publish_v12_cell(
        scored_metrics=scored,
        result_sha256=str(result["baseline_run"]["hashes"]["result_sha256"]),
        ledger_path=ledger,
        **common,
    )
    assert replay["stage"] == STAGE_IDEMPOTENT_REPLAY
    assert replay["published_delta"] == 0 and replay["observed_delta"] == 0
    view = v12_denominator_view(ledger)
    assert (view["published"], view["observed"]) == (1, 0)

    # a zero-position payload must be refused (compute-once observation on
    # its own scratch ledger, observed +1, never publishable)
    scratch = tmp_path / "scratch_zero.jsonl"
    zero = dict(scored)
    zero["n_positions"] = 0
    zero["decisions"] = []
    zero["fills"] = []
    refusal = publish_v12_cell(
        scored_metrics=zero,
        result_sha256=str(result["baseline_run"]["hashes"]["result_sha256"]),
        ledger_path=scratch,
        **{k: v for k, v in common.items() if k != "ledger_path"},
    )
    assert refusal["stage"] == STAGE_REFUSED
    assert any(str(r).startswith(REFUSED_ZERO_POSITIONS) for r in refusal["reasons"])
    assert refusal["observed_delta"] == 1
    assert v12_denominator_view(scratch)["published"] == 0


def test_liqepis_sign_inv_negates_anchor(tmp_path: Path, liqepis_frame) -> None:
    anchor = _liqepis_plugin("LIQEPIS-28D", liqepis_frame)
    result = driver.compute_cell(
        family="liqepis",
        arm_id="LIQEPIS-28D",
        plugin=anchor,
        out_dir=tmp_path / "liq_anchor",
        write_artifacts=False,
    )
    books = [book for book in result["baseline_run"]["books"] if book.get("weights")]
    weights = {sym: w for sym, w in books[0]["weights"]}
    assert len(weights) == 12  # the frozen 6v6 tercile book
    assert max(abs(w) for w in weights.values()) <= 0.5 / 6 + 1e-9

    # the causal negative control negates the anchor book exactly
    control = _liqepis_plugin("LIQEPIS-SIGN-INV", liqepis_frame)
    inv_result = driver.compute_cell(
        family="liqepis",
        arm_id="LIQEPIS-SIGN-INV",
        plugin=control,
        out_dir=tmp_path / "liq_inv",
        write_artifacts=False,
    )
    inv_books = [b for b in inv_result["baseline_run"]["books"] if b.get("weights")]
    inv_weights = {sym: w for sym, w in inv_books[0]["weights"]}
    assert set(inv_weights) == set(weights)
    for sym in weights:
        assert inv_weights[sym] == pytest.approx(-weights[sym], abs=1e-12)


# --------------------------------------------------------------------------- #
# RESOLVED FROZEN CONFLICT (V13R OITD delta, V12R2-precedent freeze delta):
# the frozen OITD plugin used to fail-close-refuse the purged (gap) schedule
# stamps that the frozen generic runner mandatorily queries
# (runner._collect_books asks targets_at at EVERY non-final schedule
# instant; OITD.decision_instants excludes the purged Mondays), making the
# scored traversal impossible.  Resolved on the PLUGIN side, science
# surface = traversal semantics only: at a NON-decision instant the
# hysteresis book CARRIES (the previous retained decision's book,
# byte-equal; flat start when none precedes) and NO signal is computed
# there, exactly as the frozen hysteresis convention implies and the
# frozen V12 family plugins answer the same mandatory queries.  Fail-closed
# refusals at RETAINED decision stamps are unchanged; identity, parameters,
# schedule bytes and the 3 arm-config digests are unchanged.  The tests
# below pin the traversal pin PASSING plus the carry/no-signal/fail-closed
# evidence so neither side can regress silently.
# --------------------------------------------------------------------------- #
def test_frozen_oitd_runner_traversal_now_completes(oitd_frame) -> None:
    """compute_cell (full frozen runner traversal, all matrix cells)
    completes for the anchor arm on the synthetic frame."""
    plugin = _oitd_plugin("OITD-28D", oitd_frame)
    result = driver.compute_cell(
        family="oitd",
        arm_id="OITD-28D",
        plugin=plugin,
        out_dir=Path("/tmp/v13r_oitd_traversal_must_not_write"),
        write_artifacts=False,
    )
    assert result["matrix_cells"]
    books = result["baseline_run"]["books"]
    assert books, "the traversal produced the baseline books"


def test_frozen_oitd_traversal_pin_passes_all_cells(oitd_frame) -> None:
    """verify_runner_traversal probes every non-final instant of every
    accepted cell; the purged/dropped stamps are answered with the carried
    book instead of refused."""
    from research.adapter_v10.protocol import StressSpec
    from research.v13.families.oitd.strategy import iso_utc, stamp_calendar

    schedule = list(stamp_calendar())
    interior = set(schedule[:-1])
    for arm_id in ("OITD-28D", "OITD-56D", "CTL-FLOW-ONLY"):
        plugin = _oitd_plugin(arm_id, oitd_frame)
        pin = driver.verify_runner_traversal(plugin)
        assert pin["ok"] is True, pin["problems"]
        assert pin["problems"] == []
        assert len(pin["cells_probed"]) == 6
        baseline_stress = plugin.baseline_stress()
        retained = set(plugin.decision_instants(stress=baseline_stress))
        purged_interior = sorted(iso_utc(t) for t in interior - retained)
        # the interior purged Mondays really are inside the probed set
        assert purged_interior, "expected the purged Mondays in the interior"
        dropfold = StressSpec(name="drop_one_fold", dropped_fold_index=0)
        dropped = {
            int(v)
            for fold in plugin.folds(stress=dropfold, instants=schedule)
            if fold.dropped
            for v in fold.instants
        }
        assert dropped, "expected dropped-fold stamps inside the probed set"


def test_oitd_off_schedule_stamp_still_refuses(oitd_frame) -> None:
    """The carry covers only the frozen SCHEDULE stamps (purged Mondays,
    dropped-fold stamps); an off-schedule instant is refused fail-closed
    exactly as before the delta (the frozen runner never queries it)."""
    from research.adapter_v10.protocol import ContractViolation
    from research.v13.families.oitd.strategy import parse_iso_utc

    plugin = _oitd_plugin("OITD-28D", oitd_frame)
    stress = plugin.baseline_stress()
    universe = plugin.tradeable_universe()
    off_grid = parse_iso_utc("2025-12-08T00:00:00Z") + 3_600_000_000_000
    with pytest.raises(ContractViolation):
        plugin.targets_at(off_grid, universe=universe, stress=stress)


def test_oitd_final_purged_monday_carries_when_queried(oitd_frame) -> None:
    """The third purged Monday (2026-08-17) is the schedule-final instant:
    the runner force-flattens it itself and _collect_books never queries
    it, but the plugin still answers it with the carried book."""
    from research.v13.families.oitd.strategy import iso_utc, stamp_calendar

    plugin = _oitd_plugin("OITD-28D", oitd_frame)
    stress = plugin.baseline_stress()
    universe = plugin.tradeable_universe()
    schedule = list(stamp_calendar())
    final = schedule[-1]
    assert iso_utc(final) == "2026-08-17T00:00:00Z"
    retained = set(plugin.decision_instants(stress=stress))
    assert final not in retained
    prior = max(s for s in retained if s < final)
    prior_book = plugin.targets_at(prior, universe=universe, stress=stress)
    carried = plugin.targets_at(final, universe=universe, stress=stress)
    assert carried == prior_book


# --------------------------------------------------------------------------- #
# Carry evidence (V13R OITD delta):
#   (a) the purged Mondays and the drop-one-fold F0 stamps traverse with
#       the CARRIED book, byte-equal to the prior decision stamp's book
#       (flat start where no decision precedes);
#   (b) mutation proof that NO signal is computed at purged stamps;
#   (c) fail-closed refusals at decision stamps are unchanged.
# --------------------------------------------------------------------------- #
def _mutate_frame_at(
    frame: dict[str, Any], start_ns: int, *, span_days: int
) -> dict[str, Any]:
    """Copy of the synthetic frame with every record whose availability
    stamp lies in ``[start_ns, start_ns + span_days)`` perturbed with a
    DISTINCT factor per symbol (the OI factor DECREASES with the
    symbol's index while the base signal level increases with it, so the
    cross-sectional ranking provably reshuffles -- a uniform factor or a
    mild one would leave every D_s rank, hence the hysteresis book,
    unchanged).
    """
    from research.v13.families.oitd.audits import tradeable_universe_symbols

    universe = sorted(tradeable_universe_symbols())
    n = len(universe)
    start = int(start_ns)
    end = start + int(span_days) * 86_400_000_000_000
    out: dict[str, Any] = dict(frame)
    out["turnover"] = {}
    for sym, days in frame["turnover"].items():
        if sym not in universe:
            out["turnover"][sym] = dict(days)
            continue
        t_factor = 1.0 + 0.25 * (n - universe.index(sym))
        out["turnover"][sym] = {
            d: (v * t_factor if start <= d * 86_400_000_000_000 < end else v)
            for d, v in days.items()
        }
    out["oi"] = {}
    out["marks"] = {}
    for index, sym in enumerate(universe):
        oi_factor = 1.0 + 100.0 * (n - index)
        mark_factor = 1.0 + 5.0 * (n - index)
        if sym in frame.get("oi", {}):
            out["oi"][sym] = tuple(
                (int(t), v * oi_factor if start <= int(t) < end else v)
                for t, v in frame["oi"][sym]
            )
        if sym in frame.get("marks", {}):
            out["marks"][sym] = tuple(
                (int(t), v * mark_factor if start <= int(t) < end else v)
                for t, v in frame["marks"][sym]
            )
    return out


def test_oitd_purged_mondays_carry_byte_equal_prior_decision(
    oitd_frame,
) -> None:
    """(a) The interior purged Mondays traverse with the CARRIED book,
    byte-equal (payload hash) to the prior decision stamp's book."""
    from research.v13.families.oitd.strategy import iso_utc

    plugin = _oitd_plugin("OITD-28D", oitd_frame)
    stress = plugin.baseline_stress()
    universe = plugin.tradeable_universe()
    schedule = list(plugin.schedule().instants)
    retained = set(plugin.decision_instants(stress=stress))
    purged = sorted(t for t in schedule[:-1] if t not in retained)
    assert [iso_utc(t) for t in purged] == [
        "2025-12-15T00:00:00Z",
        "2026-04-20T00:00:00Z",
    ]
    for stamp in purged:
        prior = max(s for s in retained if s < stamp)
        prior_book = plugin.targets_at(prior, universe=universe, stress=stress)
        carried = plugin.targets_at(stamp, universe=universe, stress=stress)
        assert carried == prior_book
        assert payload_sha256(carried) == payload_sha256(prior_book)
        assert carried["status"] == "OK"
        assert carried["weights"], "the carried book is the prior 12-leg book"


def test_oitd_drop_one_fold_f0_stamps_carry(oitd_frame) -> None:
    """(a) Under the drop-one-fold stress (F0 dropped) every F0 stamp is a
    gap instant with NO preceding retained decision: the carried book is
    the flat start (status OK, zero legs, explicit reason code)."""
    from research.adapter_v10.protocol import StressSpec
    from research.v13.families.oitd.plugin import REASON_CARRIED_FLAT_START
    from research.v13.families.oitd.strategy import iso_utc

    plugin = _oitd_plugin("OITD-28D", oitd_frame)
    probe = StressSpec(name="drop_one_fold", dropped_fold_index=0)
    universe = plugin.tradeable_universe()
    schedule = list(plugin.schedule().instants)
    f0 = sorted(
        int(v)
        for fold in plugin.folds(stress=probe, instants=schedule)
        if fold.dropped
        for v in fold.instants
    )
    retained = set(plugin.decision_instants(stress=probe))
    assert f0 and all(s not in retained for s in f0)
    assert min(retained) > max(f0)  # no retained decision precedes any F0 stamp
    for stamp in f0:
        carried = plugin.targets_at(stamp, universe=universe, stress=probe)
        assert carried["status"] == "OK"
        assert carried["carried_forward"] is True
        assert carried["reason_code"] == REASON_CARRIED_FLAT_START
        assert carried["weights"] == []
        assert carried["decision_ns"] == int(stamp)
    assert iso_utc(f0[0]) == "2025-08-25T00:00:00Z"


def test_oitd_mutation_at_purged_stamp_leaves_carried_book_unchanged(
    oitd_frame,
) -> None:
    """(b) Mutating OI/mark/turnover records readable ONLY at/after a
    purged Monday leaves that stamp's carried book byte-unchanged (no
    signal is computed there) and leaves the prior decision unchanged;
    the SAME mutation moves the NEXT retained decision (the harness
    bites)."""
    from research.v13.families.oitd.strategy import iso_utc, parse_iso_utc

    purged = parse_iso_utc("2025-12-15T00:00:00Z")
    base = _oitd_plugin("OITD-28D", oitd_frame)
    # span 7d: the records readable at/after the purged Monday up to the
    # NEXT retained decision -- none of them readable by the PRIOR decision
    mutated = _oitd_plugin("OITD-28D", _mutate_frame_at(oitd_frame, purged, span_days=7))
    universe = base.tradeable_universe()
    stress = base.baseline_stress()
    retained = sorted(base.decision_instants(stress=stress))
    prior = max(s for s in retained if s < purged)
    nxt = min(s for s in retained if s > purged)
    assert iso_utc(prior) == "2025-12-08T00:00:00Z"
    assert iso_utc(nxt) == "2025-12-22T00:00:00Z"

    base_prior = base.targets_at(prior, universe=universe, stress=stress)
    base_next = base.targets_at(nxt, universe=universe, stress=stress)
    mut_prior = mutated.targets_at(prior, universe=universe, stress=stress)
    mut_next = mutated.targets_at(nxt, universe=universe, stress=stress)
    carried_base = base.targets_at(purged, universe=universe, stress=stress)
    carried_mut = mutated.targets_at(purged, universe=universe, stress=stress)

    # no signal at the purged stamp: the carried book is byte-identical
    assert payload_sha256(carried_mut) == payload_sha256(carried_base)
    assert payload_sha256(carried_mut) == payload_sha256(mut_prior)
    assert payload_sha256(carried_mut) == payload_sha256(base_prior)
    # the prior decision cannot read records stamped at/after the purge
    assert payload_sha256(mut_prior) == payload_sha256(base_prior)
    # the mutation bites at the next retained decision stamp
    assert payload_sha256(mut_next) != payload_sha256(base_next)


def test_oitd_mutation_at_decision_stamp_moves_the_book(oitd_frame) -> None:
    """(b) The same mutation applied at a retained decision stamp moves
    that stamp's book (the chain computes real signals at decisions)."""
    from research.v13.families.oitd.strategy import iso_utc, parse_iso_utc

    decision = parse_iso_utc("2025-12-08T00:00:00Z")
    base = _oitd_plugin("OITD-28D", oitd_frame)
    mutated = _oitd_plugin(
        "OITD-28D", _mutate_frame_at(oitd_frame, decision, span_days=1)
    )
    universe = base.tradeable_universe()
    stress = base.baseline_stress()
    assert iso_utc(decision) in {
        iso_utc(s) for s in base.decision_instants(stress=stress)
    }
    base_book = base.targets_at(decision, universe=universe, stress=stress)
    mut_book = mutated.targets_at(decision, universe=universe, stress=stress)
    assert payload_sha256(mut_book) != payload_sha256(base_book)


def test_oitd_fail_closed_still_fires_at_decision_stamps(oitd_frame) -> None:
    """(c) Genuinely-unreadable inputs still refuse fail-closed.  With the
    OI warm-up gapped so the FIRST retained decision holds fewer than 7 OI
    records in its trailing 10d span, that decision stamp raises
    EligibilityShortfall -- and a purged-stamp query downstream refuses
    too (the frozen chain itself is unreadable from the flat start).
    (Mid-chain eligibility collapses carry per the frozen hysteresis rule
    5a -- that semantic is unchanged by the delta; the golden PIT suite
    pins the refusal paths.)"""
    from research.v13.families.oitd.book import EligibilityShortfall
    from research.v13.families.oitd.strategy import iso_utc

    plugin_clean = _oitd_plugin("OITD-28D", oitd_frame)
    stress = plugin_clean.baseline_stress()
    universe = plugin_clean.tradeable_universe()
    retained = sorted(plugin_clean.decision_instants(stress=stress))
    first = retained[0]
    # keep only 3 of the 7 OI records the first decision would read
    keep_from = first - 3 * 86_400_000_000_000
    truncated = dict(oitd_frame)
    truncated["oi"] = {
        sym: tuple((t, v) for t, v in rows if t >= keep_from)
        for sym, rows in oitd_frame["oi"].items()
    }
    plugin = _oitd_plugin("OITD-28D", truncated)
    n_readable = sum(
        1
        for t, _v in truncated["oi"][universe[0]]
        if first - 10 * 86_400_000_000_000 < t <= first
    )
    assert n_readable < 7  # the warm-up is genuinely insufficient
    with pytest.raises(EligibilityShortfall):
        plugin.targets_at(first, universe=universe, stress=stress)
    # the purged Monday inside the broken chain refuses as well
    purged_broken = next(
        t
        for t in sorted(plugin.schedule().instants)[:-1]
        if t not in set(retained) and t > first
    )
    assert iso_utc(purged_broken) == "2025-12-15T00:00:00Z"
    with pytest.raises(EligibilityShortfall):
        plugin.targets_at(purged_broken, universe=universe, stress=stress)
    # the untouched frame still computes the first decision normally
    payload = plugin_clean.targets_at(first, universe=universe, stress=stress)
    assert payload["status"] == "OK" and payload["weights"]


def test_liqepis_traversal_pin_passes(liqepis_frame) -> None:
    plugin = _liqepis_plugin("LIQEPIS-28D", liqepis_frame)
    pin = driver.verify_runner_traversal(plugin)
    assert pin["ok"] is True
    assert pin["problems"] == []
    assert len(pin["cells_probed"]) == 6


def test_oitd_control_arm_refuses_numerator_bundle(oitd_frame) -> None:
    """The causal control is constructed WITHOUT the OI/mark bundles."""
    from research.adapter_v10.protocol import ContractViolation
    from research.v13.families.oitd.plugin import OitdPlugin

    with pytest.raises(ContractViolation, match="CTL-FLOW-ONLY"):
        OitdPlugin(
            arm_id="CTL-FLOW-ONLY",
            day_turnover_by_symbol=oitd_frame["turnover"],
            bars_by_symbol=oitd_frame["bars"],
            oi_by_symbol=oitd_frame["oi"],
            settlements_by_symbol=oitd_frame["settlements"],
            tick_sizes=oitd_frame["ticks"],
        )

    # built correctly (numerator deleted), the control answers the frozen
    # primitives at a RETAINED decision stamp (schedule-only; no PnL here)
    control = _oitd_plugin("CTL-FLOW-ONLY", oitd_frame)
    stress = control.baseline_stress()
    stamp = control.decision_instants(stress=stress)[0]
    payload = control.targets_at(
        stamp, universe=control.tradeable_universe(), stress=stress
    )
    assert payload["arm_id"] == "CTL-FLOW-ONLY"
    assert payload["status"] == "OK"


# --------------------------------------------------------------------------- #
# Reproduction comparison: identical recompute ALL_MATCH; perturbation caught
# --------------------------------------------------------------------------- #
def test_repro_comparison_all_match_and_mismatch(tmp_path: Path, liqepis_frame) -> None:
    first = driver.compute_cell(
        family="liqepis",
        arm_id="LIQEPIS-28D",
        plugin=_liqepis_plugin("LIQEPIS-28D", liqepis_frame),
        out_dir=tmp_path / "exec",
        write_artifacts=False,
    )
    second = driver.compute_cell(
        family="liqepis",
        arm_id="LIQEPIS-28D",
        plugin=_liqepis_plugin("LIQEPIS-28D", liqepis_frame),
        out_dir=tmp_path / "repro",
        write_artifacts=False,
    )
    digest = driver.family_registry()["liqepis"]["digest"]("LIQEPIS-28D")

    def _view(computed):
        return driver.repro_view(
            {**computed, "arm_config_digest": digest},
            staged_sha="e" * 64,
            head="1" * 40,
        )

    report = driver.compare_repro(_view(first), _view(second))
    assert report["verdict"] == "ALL_MATCH"

    perturbed = dict(_view(second))
    perturbed["scored_net_return_sum"] = float(perturbed["scored_net_return_sum"]) + 1e-9
    report_bad = driver.compare_repro(_view(first), perturbed)
    assert report_bad["verdict"] == "MISMATCH"
    assert report_bad["fields"]["scored_net_return_sum"]["match"] is False
    assert report_bad["artifact"] == "v13r_repro_cell_comparison"


def test_matrix_digest_deterministic_across_recompute(
    tmp_path: Path, liqepis_frame
) -> None:
    runs_a = driver.compute_cell(
        family="liqepis",
        arm_id="LIQEPIS-56D",
        plugin=_liqepis_plugin("LIQEPIS-56D", liqepis_frame),
        out_dir=tmp_path / "a",
        write_artifacts=False,
    )
    runs_b = driver.compute_cell(
        family="liqepis",
        arm_id="LIQEPIS-56D",
        plugin=_liqepis_plugin("LIQEPIS-56D", liqepis_frame),
        out_dir=tmp_path / "b",
        write_artifacts=False,
    )
    assert runs_a["matrix_digest"] == runs_b["matrix_digest"]
    assert runs_a["matrix_digest"] == payload_sha256(
        {name: runs_a["runs"][name]["hashes"] for name in runs_a["runs"]}
    )


# --------------------------------------------------------------------------- #
# Driver main(): preflight pins, publish exactly-once, repro via artifacts
# --------------------------------------------------------------------------- #
class _MainHarness:
    """Runs driver.main() offline: fake staged pin + synthetic plugin build."""

    def __init__(self, tmp_path: Path, family: str, arm: str, frame: dict, plugin_builder) -> None:
        self.tmp = tmp_path
        self.family = family
        self.arm = arm
        self.frame = frame
        self.plugin_builder = plugin_builder
        self.staged = tmp_path / "staged_data"
        self.staged.mkdir(parents=True, exist_ok=True)
        self.exec_root = tmp_path / "exec_tree"
        (self.exec_root / "research" / "audits" / "v12p").mkdir(parents=True, exist_ok=True)
        (self.exec_root / "research" / "control" / "v13_run").mkdir(parents=True, exist_ok=True)
        (self.exec_root / "research" / "audits" / "v12p" / "a3_staging_manifest.json").write_text(
            json.dumps({"files": {}, "files_count": 0}), encoding="utf-8"
        )
        import shutil

        shutil.copy(
            REPO_ROOT / "research" / "control" / "v13_run" / "w13_freeze.json",
            self.exec_root / "research" / "control" / "v13_run" / "w13_freeze.json",
        )
        self.head = "b" * 40
        self.publish_calls: list[dict] = []
        self._patchers = []

    def _fake_verify(self, staged_root, expected, authority):  # noqa: ANN001
        return {
            "staged_root": str(staged_root),
            "staged_manifest_sha256": expected,
            "expected_staged_manifest_sha256": expected,
            "files_count": 90,
            "files_verified": 90,
            "authority_files": 90,
            "problems": [],
            "ok": True,
        }

    def install(self, monkeypatch, *, frame_override=None):  # noqa: ANN001
        registry = driver.family_registry()
        frame = frame_override if frame_override is not None else self.frame

        def _build(staged_root, arm_id, exec_root=None):
            assert Path(staged_root) == self.staged.resolve()
            plugin = self.plugin_builder(arm_id, frame)
            return plugin, {"synthetic": True}

        registry[self.family]["build"] = _build
        monkeypatch.setattr(driver, "family_registry", lambda: registry)
        monkeypatch.setattr(driver, "git_head", lambda root: self.head)
        monkeypatch.setattr(driver, "verify_staged_snapshot", self._fake_verify)
        return self

    def run(self, out_name: str, *extra: str):
        out_root = self.tmp / out_name
        argv = [
            "--family",
            self.family,
            "--arm",
            self.arm,
            "--exec-root",
            str(self.exec_root),
            "--staged-root",
            str(self.staged),
            "--out-root",
            str(out_root),
            *extra,
        ]
        return out_root, driver.main(argv)


@pytest.fixture(scope="module")
def oitd_harness_frame(tmp_path_factory) -> dict[str, Any]:
    return _synthetic_oitd_data()


@pytest.fixture(scope="module")
def liqepis_harness_frame(tmp_path_factory) -> dict[str, Any]:
    return _synthetic_liqepis_series()


def test_main_preflight_only_no_scored_metric(
    tmp_path, monkeypatch, liqepis_harness_frame
) -> None:
    harness = _MainHarness(
        tmp_path, "liqepis", "LIQEPIS-28D", liqepis_harness_frame, _liqepis_plugin
    ).install(monkeypatch)
    out_dir, code = harness.run("pf", "--preflight-only")
    assert code == driver.EXIT_OK
    preflight = json.loads((out_dir / "preflight.json").read_text(encoding="utf-8"))
    assert preflight["no_scored_metric_yet"] is True
    assert preflight["digest_matches_freeze"] is True
    assert preflight["all_arm_digests_match_freeze"]["n_match"] == 6
    assert preflight["runner_traversal_pin"]["ok"] is True
    assert not (out_dir / "baseline_metrics.json").exists()
    assert not (out_dir / "matrix_summary.json").exists()


def test_main_oitd_traversal_pin_now_passes_and_compute_runs(
    tmp_path, monkeypatch, oitd_harness_frame
) -> None:
    """RESOLVED (V13R OITD delta): the frozen OITD/runner conflict no
    longer blocks the scored path.  main() preflight records the
    traversal pin PASSING; the matrix compute then runs on the synthetic
    frame, and with no --publish no ledger write and no cell summary
    ever happen (the fail-closed publication gate is unchanged).
    (Formerly this test pinned the exit-2 refusal of the unresolved
    conflict; that refusal semantics is what the plugin-side carry fix
    replaced, with digests and identity unchanged.)
    """
    harness = _MainHarness(
        tmp_path, "oitd", "OITD-28D", oitd_harness_frame, _oitd_plugin
    ).install(monkeypatch)
    out_dir, code = harness.run("traverses")
    assert code == driver.EXIT_OK
    preflight = json.loads((out_dir / "preflight.json").read_text(encoding="utf-8"))
    pin = preflight["runner_traversal_pin"]
    assert pin["ok"] is True
    assert pin["problems"] == []
    assert preflight["digest_matches_freeze"] is True
    # the matrix compute ran (schedule-only traversal completed) ...
    assert (out_dir / "baseline_metrics.json").exists()
    assert (out_dir / "matrix_summary.json").exists()
    # ... but without --publish nothing was published
    assert not (out_dir / "cell_summary.json").exists()


def test_main_no_ledger_write_without_publish(
    tmp_path, monkeypatch, liqepis_harness_frame
) -> None:
    import research.v12.accounting as accounting

    original = accounting.publish_v12_cell

    def spy(**kwargs):
        harness.publish_calls.append(kwargs)
        return original(**kwargs)

    harness = _MainHarness(
        tmp_path, "liqepis", "LIQEPIS-28D", liqepis_harness_frame, _liqepis_plugin
    ).install(monkeypatch)
    monkeypatch.setattr(accounting, "publish_v12_cell", spy)
    ledger = tmp_path / "must_stay_absent.jsonl"
    out_dir, code = harness.run("nopub")
    assert code == driver.EXIT_OK
    assert ledger.exists() is False
    assert harness.publish_calls == []
    assert (out_dir / "baseline_metrics.json").exists()
    assert not (out_dir / "cell_summary.json").exists()


def test_main_publish_exactly_once_then_idempotent(
    tmp_path, monkeypatch, liqepis_harness_frame
) -> None:
    harness = _MainHarness(
        tmp_path, "liqepis", "LIQEPIS-28D", liqepis_harness_frame, _liqepis_plugin
    ).install(monkeypatch)
    ledger = tmp_path / "ledger_liqepis.jsonl"
    out_dir, code = harness.run(
        "pub", "--publish", "--ledger", str(ledger), "--expect-head", harness.head
    )
    assert code == driver.EXIT_OK
    summary = json.loads((out_dir / "cell_summary.json").read_text(encoding="utf-8"))
    assert summary["publish_stage"] == STAGE_PUBLISHED
    assert summary["published_delta"] == 1
    assert summary["denominator_after"]["published"] == 1
    before = v12_denominator_view(ledger)

    # exact replay: idempotent skip, ZERO counter delta, still exit 0
    out_dir2, code2 = harness.run(
        "pub2", "--publish", "--ledger", str(ledger), "--expect-head", harness.head
    )
    assert code2 == driver.EXIT_OK
    summary2 = json.loads((out_dir2 / "cell_summary.json").read_text(encoding="utf-8"))
    assert summary2["publish_stage"] == STAGE_IDEMPOTENT_REPLAY
    assert summary2["published_delta"] == 0 and summary2["observed_delta"] == 0
    assert v12_denominator_view(ledger) == before

    # repro against the published execution evidence: identical frame ALL_MATCH
    repro_out, code3 = harness.run(
        "repro", "--repro", "--compare-with", str(out_dir)
    )
    assert code3 == driver.EXIT_OK
    report = json.loads((repro_out / "repro_report.json").read_text(encoding="utf-8"))
    assert report["verdict"] == "ALL_MATCH"
    assert v12_denominator_view(ledger) == before  # repro never writes

    # a perturbed frame must be caught as MISMATCH (exit 6): scaled closes
    # change fills/marks (and therefore PnL and hashes), never the frozen
    # identity, digests or universe
    different = dict(liqepis_harness_frame)
    from research.v13.families.liqepis.strategy import FusionBarSeries

    different["series"] = {
        sym: FusionBarSeries(
            origin_ns=s.origin_ns,
            close=s.close * 1.5,
            volume=s.volume,
            available_ns=s.available_ns,
            _q_cache=(s.close * 1.5) * s.volume,
        )
        for sym, s in liqepis_harness_frame["series"].items()
    }
    harness.install(monkeypatch, frame_override=different)
    mismatch_out, code4 = harness.run(
        "repro_bad", "--repro", "--compare-with", str(out_dir)
    )
    assert code4 == driver.EXIT_REPRO_MISMATCH
    bad_report = json.loads(
        (mismatch_out / "repro_report.json").read_text(encoding="utf-8")
    )
    assert bad_report["verdict"] == "MISMATCH"
    assert v12_denominator_view(ledger) == before


def test_main_rejects_arm_of_the_other_family(
    tmp_path, monkeypatch, liqepis_harness_frame
) -> None:
    harness = _MainHarness(
        tmp_path, "oitd", "LIQEPIS-28D", liqepis_harness_frame, _liqepis_plugin
    ).install(monkeypatch)
    _out, code = harness.run("reject")
    assert code == driver.EXIT_FAIL_CLOSED


def test_main_rejects_publish_with_wrong_head_pin(
    tmp_path, monkeypatch, liqepis_harness_frame
) -> None:
    harness = _MainHarness(
        tmp_path, "liqepis", "LIQEPIS-28D", liqepis_harness_frame, _liqepis_plugin
    ).install(monkeypatch)
    ledger = tmp_path / "never.jsonl"
    _out, code = harness.run(
        "badpin", "--publish", "--ledger", str(ledger), "--expect-head", "c" * 40
    )
    assert code == driver.EXIT_FAIL_CLOSED
    assert ledger.exists() is False
