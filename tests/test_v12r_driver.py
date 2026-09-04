"""V12R scored-cell driver tests (hand-computed fixtures; no real data).

Covers the owner-mandated driver gates:

* 6/6 frozen arm-config digests recompute from the family modules and match
  ``research/control/v12_run/selection_freeze.json`` v2 (fail-closed pin);
* flag-combination validation (no publish without ledger/pin; repro never
  publishes; compare-with only with repro);
* the settlements reader mirrors the frozen OILEV loader row mapping
  (hand-computed funding bundle);
* scored-metric extraction carries REAL decision/fill evidence;
* staged-snapshot pin (digest + 90-file inventory) fails closed;
* end-to-end synthetic frame through the REAL adapter path: family contract
  derivation, baseline-only scoring, exactly-once publication
  (published +1), idempotent replay (zero delta), zero-position refusal
  (observed +1 on a scratch ledger), and repro exact-match comparison
  (ALL_MATCH; perturbation detected as MISMATCH);
* BAB frozen-mechanism sanity through the driver path: the anchor book is
  long the designed lowest-beta quartile and the INV control negates it.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

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

driver = importlib.import_module(
    "research.control.v12_run.tools_stronghost.run_v12_cell"
)

FREEZE = json.loads(
    (REPO_ROOT / "research" / "control" / "v12_run" / "selection_freeze.json")
    .read_text(encoding="utf-8")
)
FROZEN_DIGESTS = {
    c["arm_id"]: c["arm_config_digest"] for c in FREEZE["frozen_cells"]
}

ALL_SIX_ARMS = tuple(sorted(FROZEN_DIGESTS))


# --------------------------------------------------------------------------- #
# 6/6 frozen digest equality (the driver's fail-closed pin)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("arm_id", ALL_SIX_ARMS)
def test_six_arm_digests_recompute_and_match_freeze(arm_id: str) -> None:
    registry = driver.family_registry()
    family = next(name for name in registry if arm_id in registry[name]["arms"])
    assert registry[family]["digest"](arm_id) == FROZEN_DIGESTS[arm_id]


def test_driver_rejects_arm_outside_freeze() -> None:
    registry = driver.family_registry()
    for family in registry:
        with pytest.raises(ValueError):
            if family == "oilev_v2":
                driver.build_oilev(Path("unused"), "NOT-A-FROZEN-ARM")
            else:
                driver.build_bab(Path("unused"), "NOT-A-FROZEN-ARM", Path("unused"))


# --------------------------------------------------------------------------- #
# Flag-combination validation
# --------------------------------------------------------------------------- #
def _args(**overrides):
    argv = ["--family", "oilev_v2", "--arm", "OILEV-V2-28D-FLOW-W"]
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
    bad_family.family = "v11_lot"  # argparse choices also reject this earlier
    assert driver.validate_args(bad_family) is not None


# --------------------------------------------------------------------------- #
# Settlements reader: hand-computed mirror of the frozen loader mapping
# --------------------------------------------------------------------------- #
def test_load_settlements_root_hand_computed(tmp_path: Path) -> None:
    root = tmp_path / "funding_scan_2026"
    (root / "AAAUSDT").mkdir(parents=True)
    (root / "BBBUSDT").mkdir(parents=True)
    (root / "AAAUSDT" / "funding.json").write_text(
        json.dumps(
            {
                "rows": [
                    {"fundingTime": 1_800_000_500, "fundingRate": "0.0001"},
                    {"fundingTime": 900_000_000, "fundingRate": "-0.00025"},
                ]
            }
        ),
        encoding="utf-8",
    )
    out = driver.load_settlements_root(root, ["AAAUSDT", "BBBUSDT", "CCCUSDT"])
    # hand-computed: ms -> ns (x1e6), sorted ascending; missing -> empty tuple
    assert out["AAAUSDT"] == (
        {"publish_ts_ns": 900_000_000_000_000, "value": -0.00025},
        {"publish_ts_ns": 1_800_000_500_000_000, "value": 0.0001},
    )
    assert out["BBBUSDT"] == ()
    assert out["CCCUSDT"] == ()
    # duplicate stamps are a hard error, never silently deduplicated
    (root / "BBBUSDT" / "funding.json").write_text(
        json.dumps(
            {
                "rows": [
                    {"fundingTime": 900_000_000, "fundingRate": "0.0001"},
                    {"fundingTime": 900_000_000, "fundingRate": "0.0002"},
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate settlement"):
        driver.load_settlements_root(root, ["BBBUSDT"])


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
    broken["portfolio_metrics"] = {"net_return_sum": None, "expectancy_per_day": 0.005, "max_drawdown": 0.04}
    assert driver.scored_metrics_from_baseline(broken)["score_valid"] is False


# --------------------------------------------------------------------------- #
# Staged snapshot pin
# --------------------------------------------------------------------------- #
def test_verify_staged_snapshot_fail_closed(tmp_path: Path) -> None:
    staged = tmp_path / "staged_data"
    for label in driver.STAGED_BARS, driver.STAGED_PERP_META, driver.STAGED_FUNDING, driver.STAGED_OI:
        (staged / label).mkdir(parents=True)
    manifest = staged / driver.STAGED_MANIFEST_NAME
    manifest.write_text(
        json.dumps(
            {
                "files_count": 90,
                "files": {
                    f"{label}/probe.bin": {"sha256": "0" * 64, "bytes": 1}
                    for label in (
                        driver.STAGED_BARS,
                        driver.STAGED_PERP_META,
                        driver.STAGED_FUNDING,
                        driver.STAGED_OI,
                    )
                },
            }
        ),
        encoding="utf-8",
    )
    good = driver.verify_staged_snapshot(staged, driver.sha256_file(manifest))
    assert good["ok"] is True and good["files_count"] == 90

    wrong_digest = driver.verify_staged_snapshot(staged, "f" * 64)
    assert wrong_digest["ok"] is False and any("mismatch" in p for p in wrong_digest["problems"])

    manifest.write_text(json.dumps({"files_count": 89, "files": {}}), encoding="utf-8")
    wrong_count = driver.verify_staged_snapshot(staged, driver.sha256_file(manifest))
    assert wrong_count["ok"] is False and any("files_count" in p for p in wrong_count["problems"])

    missing = driver.verify_staged_snapshot(tmp_path / "nope", "0" * 64)
    assert missing["ok"] is False and any("missing" in p for p in missing["problems"])


# --------------------------------------------------------------------------- #
# Synthetic OILEV frame: deterministic OI/bars/settlements (pipeline only)
# --------------------------------------------------------------------------- #
DAY_NS = 86_400_000_000_000
BAR_NS = 900_000_000_000
OILEV_UNIVERSE = (
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "DOGEUSDT", "ENAUSDT", "ETHUSDT",
    "LINKUSDT", "NEARUSDT", "ONGUSDT", "SOLUSDT", "SUIUSDT", "WLDUSDT",
    "XRPUSDT", "ZECUSDT",
)


def _synthetic_oilev_data() -> dict[str, Any]:
    from datetime import datetime, timedelta, timezone

    from research.v11.families.oilever_delev.strategy import Bar
    from research.v12.data_contract import parse_iso_utc_ns
    from research.v12.families.oilev_v2.strategy import (
        WINDOW_END_ISO,
        WINDOW_START_ISO,
        stamp_calendar,
    )

    instants = list(stamp_calendar())
    symbols = tuple(OILEV_UNIVERSE) + ("BTCUSDT",)

    start_ns = parse_iso_utc_ns(WINDOW_START_ISO)
    end_ns = parse_iso_utc_ns(WINDOW_END_ISO)
    day0 = datetime.fromtimestamp(start_ns // 10**9, tz=timezone.utc)

    # daily OI rows from 400d before the window through the window end, so
    # every decision stamp has a PIT row strictly inside the 48h gate
    oi: dict[str, tuple[tuple[int, float], ...]] = {}
    for index, sym in enumerate(symbols):
        if sym == "BTCUSDT":
            continue  # frozen plugin: the benchmark leg is never tradeable
        base = 1_000.0 + 13.0 * index
        rows = []
        for offset in range(-400, 366):
            ts = int((day0 + timedelta(days=offset)).timestamp()) * 10**9
            rows.append((ts, base * (1.0 + 0.001 * ((offset % 7) - 3))))
        oi[sym] = tuple(sorted(rows))

    bars: dict[str, tuple[Any, ...]] = {}
    for sym in symbols:
        price = 2.0 + 0.5 * symbols.index(sym)
        seq: list[Bar] = []
        for instant in instants:
            for k in (1, 2, 3):  # covering bar + strictly-later events
                close = price
                seq.append(
                    Bar(
                        ts_event_ns=instant + k * BAR_NS,
                        open=price,
                        high=price,
                        low=price,
                        close=close,
                    )
                )
        bars[sym] = tuple(sorted(seq, key=lambda b: b.ts_event_ns))

    settlements: dict[str, tuple[dict[str, Any], ...]] = {
        sym: tuple(
            {"publish_ts_ns": start_ns + 8 * 3_600 * 10**9 * k, "value": 0.0001}
            for k in range(1, 240)
        )
        for sym in OILEV_UNIVERSE
    }
    ticks = {sym: 0.01 for sym in symbols}
    return {"oi": oi, "bars": bars, "settlements": settlements, "ticks": ticks}


@pytest.fixture(scope="module")
def oilev_frame() -> dict[str, Any]:
    return _synthetic_oilev_data()


def _oilev_plugin(arm_id: str, frame: dict[str, Any]):
    from research.v12.families.oilev_v2.plugin import OilevV2Plugin

    return OilevV2Plugin(
        arm_id=arm_id,
        oi_by_symbol=frame["oi"],
        bars_by_symbol=frame["bars"],
        settlements_by_symbol=frame["settlements"],
        tick_sizes=frame["ticks"],
    )


# --------------------------------------------------------------------------- #
# End-to-end synthetic publication path (OILEV anchor)
# --------------------------------------------------------------------------- #
def test_oilev_end_to_end_publish_replay_refusal(tmp_path: Path, oilev_frame) -> None:
    plugin = _oilev_plugin("OILEV-V2-28D-FLOW-W", oilev_frame)
    result = driver.compute_cell(
        family="oilev_v2",
        arm_id="OILEV-V2-28D-FLOW-W",
        plugin=plugin,
        out_dir=tmp_path / "exec",
    )
    assert result["matrix_cells"][0] == "baseline"
    assert "baseline" in result["runs"]
    assert result["universe"] == list(OILEV_UNIVERSE)
    scored = result["scored_metrics"]
    assert scored["score_valid"] is True
    assert scored["n_positions"] > 0
    assert scored["n_fills"] == scored["n_positions"]
    assert scored["n_decisions"] > 0

    identity = plugin.identity()
    from research.v11.publication_identity import arm_config_digest

    digest = arm_config_digest(identity, arm_id="OILEV-V2-28D-FLOW-W")
    ledger = tmp_path / "shard_oilev.jsonl"
    first = publish_v12_cell(
        strategy_id=identity.strategy_id,
        family=identity.family_id,
        arm_id="OILEV-V2-28D-FLOW-W",
        arm_config_digest=digest,
        stress_signature=plugin.baseline_stress().signature(),
        window_start_iso=identity.window_start_iso,
        window_end_iso=identity.window_end_iso,
        scored_metrics=scored,
        result_sha256=str(result["baseline_run"]["hashes"]["result_sha256"]),
        ledger_path=ledger,
        family_contract_cells=result["contract"],
        producer_head_sha="0" * 40,
    )
    assert first["stage"] == STAGE_PUBLISHED
    assert first["published_delta"] == 1 and first["observed_delta"] == 0

    replay = publish_v12_cell(
        strategy_id=identity.strategy_id,
        family=identity.family_id,
        arm_id="OILEV-V2-28D-FLOW-W",
        arm_config_digest=digest,
        stress_signature=plugin.baseline_stress().signature(),
        window_start_iso=identity.window_start_iso,
        window_end_iso=identity.window_end_iso,
        scored_metrics=scored,
        result_sha256=str(result["baseline_run"]["hashes"]["result_sha256"]),
        ledger_path=ledger,
        family_contract_cells=result["contract"],
        producer_head_sha="0" * 40,
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
        strategy_id=identity.strategy_id,
        family=identity.family_id,
        arm_id="OILEV-V2-28D-FLOW-W",
        arm_config_digest=digest,
        stress_signature=plugin.baseline_stress().signature(),
        window_start_iso=identity.window_start_iso,
        window_end_iso=identity.window_end_iso,
        scored_metrics=zero,
        result_sha256=str(result["baseline_run"]["hashes"]["result_sha256"]),
        ledger_path=scratch,
        family_contract_cells=result["contract"],
        producer_head_sha="0" * 40,
    )
    assert refusal["stage"] == STAGE_REFUSED
    assert any(str(r).startswith(REFUSED_ZERO_POSITIONS) for r in refusal["reasons"])
    assert refusal["observed_delta"] == 1
    assert v12_denominator_view(scratch)["published"] == 0


# --------------------------------------------------------------------------- #
# Reproduction comparison: identical recompute ALL_MATCH; perturbation caught
# --------------------------------------------------------------------------- #
def test_repro_comparison_all_match_and_mismatch(tmp_path: Path, oilev_frame) -> None:
    plugin = _oilev_plugin("OILEV-V2-56D-STOCK-W", oilev_frame)
    first = driver.compute_cell(
        family="oilev_v2",
        arm_id="OILEV-V2-56D-STOCK-W",
        plugin=plugin,
        out_dir=tmp_path / "exec",
        write_artifacts=False,
    )
    second = driver.compute_cell(
        family="oilev_v2",
        arm_id="OILEV-V2-56D-STOCK-W",
        plugin=plugin,
        out_dir=tmp_path / "repro",
        write_artifacts=False,
    )
    from research.v11.publication_identity import arm_config_digest

    digest = arm_config_digest(plugin.identity(), arm_id="OILEV-V2-56D-STOCK-W")

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


# --------------------------------------------------------------------------- #
# BAB frozen mechanism through the driver path (hand-computed fixture)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def bab_frame():
    from research.v12.families.bab_lowbeta.audits import build_beta_ranking_frame

    bars, design = build_beta_ranking_frame()
    return {"bars": bars, "design": design}


def test_bab_anchor_long_lowbeta_and_inv_negates(tmp_path: Path, bab_frame) -> None:
    from research.v12.families.bab_lowbeta.audits import make_plugin
    from research.v12.families.bab_lowbeta.strategy import frozen_arm_config_digest

    anchor = make_plugin("BAB-90D-W", bab_frame["bars"])
    control = make_plugin("BAB-90D-W-INV", bab_frame["bars"])
    result = driver.compute_cell(
        family="bab_lowbeta",
        arm_id="BAB-90D-W",
        plugin=anchor,
        out_dir=tmp_path / "bab_anchor",
        write_artifacts=False,
    )
    assert result["scored_metrics"]["score_valid"] is True
    assert result["scored_metrics"]["n_positions"] > 0
    # hand-computed fixture design: the anchor book is long the four lowest
    # betas (SYMA00..SYMA03) and short the four highest (SYMA08..SYMA11)
    books = [
        book for book in result["baseline_run"]["books"] if book.get("weights")
    ]
    weights = {sym: w for sym, w in books[0]["weights"]}
    longs = sorted(sym for sym, w in weights.items() if w > 0)
    shorts = sorted(sym for sym, w in weights.items() if w < 0)
    assert longs == ["SYMA00", "SYMA01", "SYMA02", "SYMA03"]
    assert shorts == ["SYMA08", "SYMA09", "SYMA10", "SYMA11"]
    assert frozen_arm_config_digest("BAB-90D-W") == FROZEN_DIGESTS["BAB-90D-W"]

    # the causal negative control negates the anchor book exactly
    inv_result = driver.compute_cell(
        family="bab_lowbeta",
        arm_id="BAB-90D-W-INV",
        plugin=control,
        out_dir=tmp_path / "bab_inv",
        write_artifacts=False,
    )
    inv_books = [b for b in inv_result["baseline_run"]["books"] if b.get("weights")]
    inv_weights = {sym: w for sym, w in inv_books[0]["weights"]}
    assert set(inv_weights) == set(weights)
    for sym in weights:
        assert inv_weights[sym] == pytest.approx(-weights[sym], abs=1e-12)
