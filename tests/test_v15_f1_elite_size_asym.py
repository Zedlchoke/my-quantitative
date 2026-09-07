"""A8-I lane tests for A5-V15-F1-ELITE-SIZE-ASYM: identity, features, book,
loader integrity and the refusal registry.

Every expected value below is HAND-COMPUTED (docstrings show the
arithmetic).  All data SYNTHETIC (tests/test_v15_f1_fixtures.py); the
machine-local staged root is never read by any test; nothing is scored and
no PnL on real data exists anywhere.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from pathlib import Path

import pytest

from research.v15.families.elite_size_asym import features as features_mod
from research.v15.families.elite_size_asym import loader as loader_mod
from research.v15.families.elite_size_asym.arms import (
    ANCHOR_SPEC,
    ARM_SPECS,
    CONTROL_SPEC,
    NEIGHBOR_SPEC,
    arm_spec,
)
from research.v15.families.elite_size_asym.book import (
    build_book,
    per_name_weight,
    side_count,
)
from research.v15.families.elite_size_asym.frozen_identity import (
    ANCHOR_ARM,
    ARM_CONFIG_DIGESTS,
    CONTROL_ARM,
    FOLDS,
    GLOBAL_DEFECT_DATES,
    MEASURED_BOUND_LAG_DAYS,
    NEIGHBOR_ARM,
    RECORDED_SPEC_SHA256,
    SPEC_AUTHORITY_RELPATHS,
    UNIVERSE,
    verify_arm_digests,
    verify_spec_sha256s,
)
from research.v15.families.elite_size_asym.refusal_registry import RefusalRegistry

from tests.test_v15_f1_fixtures import (
    TICK_SIZES,
    build_root,
    copy_root_with_mutated_metrics,
    day,
    default_count,
    default_sum,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# Frozen identity / spec pins
# --------------------------------------------------------------------------- #
def test_v15f1_spec_sha256_pins_match_on_disk():
    report = verify_spec_sha256s(REPO_ROOT)
    assert set(report) == set(RECORDED_SPEC_SHA256)
    assert report["proposal_P1"]["recorded_sha256"] == (
        "6d2bc25fc3d3e5ebd96ca60c8e428efed9823b94589073f41ddcbdf47392cb16"
    )
    for name, entry in report.items():
        assert entry["match"] is True, name


def test_v15f1_frozen_universe_20_with_solusdt_and_folds():
    # selection_freeze adjudication: binding universe = the frozen 20 (the
    # proposal's 19-name list is the adjudicated omission; SOLUSDT included)
    assert len(UNIVERSE) == 20
    assert "SOLUSDT" in UNIVERSE
    assert UNIVERSE[15] == "SOLUSDT"
    assert len(set(UNIVERSE)) == 20
    # folds F0/F1/F2 with the 1-day purges, frozen dates
    assert [(f["fold_id"], f["start"], f["end"]) for f in FOLDS] == [
        ("F0", "2025-08-22", "2025-12-20"),
        ("F1", "2025-12-22", "2026-04-20"),
        ("F2", "2026-04-22", "2026-08-21"),
    ]
    assert MEASURED_BOUND_LAG_DAYS == 3
    assert set(GLOBAL_DEFECT_DATES) == {
        "2025-07-21",
        "2025-07-22",
        "2025-08-29",
        "2026-08-12",
    }


def test_v15f1_arm_registry_frozen_and_structurally_bound():
    assert set(ARM_SPECS) == {ANCHOR_ARM, NEIGHBOR_ARM, CONTROL_ARM}
    assert ANCHOR_SPEC.feature == "asym"
    assert ANCHOR_SPEC.window_lookback_days == 7
    assert NEIGHBOR_SPEC.window_lookback_days == 12
    assert NEIGHBOR_SPEC.feature == "asym"
    # the causal control is structurally the SAME book on the level feature:
    # identical side shape, never reads the sum ratio
    assert CONTROL_SPEC.feature == "level"
    assert CONTROL_SPEC.window_lookback_days == 7
    assert CONTROL_SPEC.book_spec == ANCHOR_SPEC.book_spec
    assert arm_spec(ANCHOR_ARM) is ANCHOR_SPEC
    with pytest.raises(KeyError):
        arm_spec("A5-F1-NOT-FROZEN")


# --------------------------------------------------------------------------- #
# Feature golden values (hand-computed)
# --------------------------------------------------------------------------- #
def test_v15f1_feature_golden_value_hand_computed():
    # s_daily = ln(clip(sum)) - ln(clip(count)); golden: sum 3.0, count 1.5
    # -> ln(3.0) - ln(1.5) = ln(2.0)
    assert features_mod.s_daily(3.0, 1.5) == pytest.approx(math.log(2.0), abs=1e-15)
    # level feature: ln(clip(count))
    assert features_mod.c_daily(1.5) == pytest.approx(math.log(1.5), abs=1e-15)
    # clip rule [0.01, 100]: 0.001 -> ln(0.01); 200 -> ln(100); all-one-side
    # snapshots can never blow up ln
    assert features_mod.s_daily(200.0, 1.0) == pytest.approx(
        math.log(100.0), abs=1e-15
    )
    assert features_mod.s_daily(1.0, 0.001) == pytest.approx(
        -math.log(0.01), abs=1e-15
    )
    assert features_mod.clip_ratio(0.001) == 0.01
    assert features_mod.clip_ratio(200.0) == 100.0
    with pytest.raises(ValueError):
        features_mod.clip_ratio(float("nan"))


def test_v15f1_feature_window_median_hand_computed():
    # anchor window for D = 2025-08-22 is [2025-08-15 .. 2025-08-19] (5 days,
    # all <= D-3: the 2025-08-20/21/22 rows are UNREADABLE)
    window = features_mod.window_days(day("2025-08-22"), 7)
    assert [d.isoformat() for d in window] == [
        "2025-08-15",
        "2025-08-16",
        "2025-08-17",
        "2025-08-18",
        "2025-08-19",
    ]
    values = {
        window[0]: math.log(2.0),
        window[1]: 0.0,
        window[2]: math.log(4.0),
        window[3]: math.log(2.0),
        window[4]: math.log(2.0),
    }
    outcome = features_mod.feature_outcome(
        decision_date=day("2025-08-22"), lookback_days=7, daily_values=values
    )
    assert outcome.refused is False
    assert outcome.n_usable == 5
    assert outcome.signal == pytest.approx(math.log(2.0), abs=1e-15)


def test_v15f1_lag_reads_only_rows_up_to_D_minus_3():
    # MEASURED_BOUND_LAG_3D is structural: D-2, D-1, D never appear in the
    # window; mutating them cannot move the feature
    decision = day("2025-08-22")
    readable = set(features_mod.window_days(decision, 7))
    for forbidden in (day("2025-08-20"), day("2025-08-21"), day("2025-08-22")):
        assert forbidden not in readable
    base = {d: 0.1 for d in readable}
    base[day("2025-08-20")] = 99.0  # future day: outside every readable slot
    outcome = features_mod.feature_outcome(
        decision_date=decision, lookback_days=7, daily_values=base
    )
    assert outcome.signal == pytest.approx(0.1, abs=1e-15)


def test_v15f1_hole_rule_thresholds_hand_computed():
    # anchor window = 5 cells: >10% means ANY missing cell refuses (1/5 = 20%)
    window7 = features_mod.window_days(day("2025-08-22"), 7)
    values = {d: 0.1 for d in window7}
    values[window7[2]] = None  # one missing metrics-day cell
    outcome = features_mod.feature_outcome(
        decision_date=day("2025-08-22"), lookback_days=7, daily_values=values
    )
    assert outcome.refused is True
    assert outcome.n_missing == 1 and outcome.n_usable == 4
    assert outcome.refusal_reason.startswith("window_hole")

    # neighbour window = 10 cells: exactly 1 missing = 10% (NOT > 10%) ->
    # median over the available staged rows only; 2 missing = 20% -> refuse
    window12 = features_mod.window_days(day("2025-08-22"), 12)
    assert len(window12) == 10
    values10 = {d: 0.25 for d in window12}
    values10[window12[0]] = None
    outcome10 = features_mod.feature_outcome(
        decision_date=day("2025-08-22"), lookback_days=12, daily_values=values10
    )
    assert outcome10.refused is False
    assert outcome10.n_usable == 9
    assert outcome10.signal == pytest.approx(0.25, abs=1e-15)
    values10[window12[1]] = None
    outcome10b = features_mod.feature_outcome(
        decision_date=day("2025-08-22"), lookback_days=12, daily_values=values10
    )
    assert outcome10b.refused is True
    assert outcome10b.n_missing == 2


# --------------------------------------------------------------------------- #
# Book (hand-computed tercile/quintile shapes)
# --------------------------------------------------------------------------- #
def test_v15f1_book_7_6_7_weights_hand_computed():
    assert side_count(20, 1.0 / 3.0) == 7  # the frozen 7/6/7 split on 20
    w = per_name_weight(7)
    assert w == pytest.approx(0.5 / 7.0, abs=1e-15)
    signals = {sym: default_sum(sym, day("2025-08-22")) for sym in UNIVERSE}
    book = build_book(signals=signals, book_spec=ANCHOR_SPEC.book_spec)
    longs = sorted(s for s, v in book.items() if v > 0)
    shorts = sorted(s for s, v in book.items() if v < 0)
    # long the bottom-7 asymmetry ranks (universe indices 0..6: elite size
    # leans most SHORT there), short the top-7 (indices 13..19)
    assert longs == sorted(UNIVERSE[0:7])
    assert shorts == sorted(UNIVERSE[13:20])
    assert len(book) == 14  # middle 6 flat
    assert all(abs(abs(v) - 0.5 / 7.0) < 1e-15 for v in book.values())
    assert abs(sum(book.values())) < 1e-12  # dollar-neutral
    assert sum(abs(v) for v in book.values()) == pytest.approx(1.0, abs=1e-12)


def test_v15f1_book_cap_gross_and_tie_break_fail_closed():
    # a 2-name cross-section: side count 1 at fraction 1/3 -> weight capped
    # at the frozen 0.30 signed cap (never 0.5)
    tiny = build_book(
        signals={"AAAUSDT": 1.0, "BBBUSDT": -1.0}, book_spec=ANCHOR_SPEC.book_spec
    )
    assert set(tiny) == {"AAAUSDT", "BBBUSDT"}
    # the LOW signal side is the LONG side (frozen direction)
    assert tiny["BBBUSDT"] == 0.30 and tiny["AAAUSDT"] == -0.30
    # ties break deterministically by symbol id ascending: equal signals on
    # 6 names -> n_side = 2, weight = min(0.25, cap) = 0.25 per name,
    # long = first two ascending, short = last two, middle flat
    tied = build_book(
        signals={f"S{i}USDT": 1.0 for i in range(6)},
        book_spec=ANCHOR_SPEC.book_spec,
    )
    assert tied == {
        "S0USDT": 0.25,
        "S1USDT": 0.25,
        "S4USDT": -0.25,
        "S5USDT": -0.25,
    }


def test_v15f1_neighbor_book_5_10_5_weight_0p10_hand():
    assert side_count(20, 0.25) == 5  # the frozen 5/10/5 split on 20
    signals = {sym: default_sum(sym, day("2025-08-22")) for sym in UNIVERSE}
    book = build_book(signals=signals, book_spec=NEIGHBOR_SPEC.book_spec)
    longs = sorted(s for s, v in book.items() if v > 0)
    shorts = sorted(s for s, v in book.items() if v < 0)
    assert longs == sorted(UNIVERSE[0:5])
    assert shorts == sorted(UNIVERSE[15:20])
    assert len(book) == 10  # middle 10 flat
    assert all(abs(v) - 0.10 < 1e-15 for v in book.values())  # per-name 0.10


def test_v15f1_control_book_structurally_distinct_from_anchor(tmp_path):
    # Panel where the LEVEL ranking runs OPPOSITE to the ASYMMETRY ranking:
    # count_i = 1 + 0.1*(19-i) (reversed), sum_i = 1 + 0.1*i -> the anchor
    # ranks ascending in universe order while the control ranks descending.
    root = build_root(
        tmp_path / "inverted",
        count_fn=lambda sym, _day: 1.0 + 0.1 * (19 - UNIVERSE.index(sym)),
    )
    anchor_signals = {}
    control_signals = {}
    for sym in UNIVERSE:
        anchor_signals[sym] = features_mod.s_daily(
            default_sum(sym, day("2025-08-22")),
            1.0 + 0.1 * (19 - UNIVERSE.index(sym)),
        )
        control_signals[sym] = features_mod.c_daily(
            1.0 + 0.1 * (19 - UNIVERSE.index(sym))
        )
    anchor_book = build_book(
        signals=anchor_signals, book_spec=ANCHOR_SPEC.book_spec
    )
    control_book = build_book(
        signals=control_signals, book_spec=CONTROL_SPEC.book_spec
    )
    anchor_long = sorted(s for s, v in anchor_book.items() if v > 0)
    control_long = sorted(s for s, v in control_book.items() if v > 0)
    assert anchor_long == sorted(UNIVERSE[0:7])
    assert control_long == sorted(UNIVERSE[13:20])  # reversed
    assert anchor_book != control_book  # structurally NON-identical panels


# --------------------------------------------------------------------------- #
# Loader integrity (fail-closed + hole census)
# --------------------------------------------------------------------------- #
def _tiny_root(tmp_path, name="tiny"):
    return build_root(
        tmp_path / name,
        metrics_start=day("2025-08-10"),
        metrics_end=day("2025-08-21"),
        klines_start=day("2025-08-10"),
        klines_end=day("2025-08-21"),
        funding_end=day("2025-08-21"),
    )


def test_v15f1_loader_cell_census_and_global_defect_exclusion(tmp_path):
    root = build_root(
        tmp_path / "census",
        metrics_start=day("2025-08-25"),
        metrics_end=day("2025-09-02"),
        klines_start=day("2025-08-25"),
        klines_end=day("2025-09-02"),
        funding_end=day("2025-09-02"),
    )
    cells = loader_mod.load_metric_cells(root, "BTCUSDT")
    # every well-formed day is an ok cell with the 00:00 observation ...
    assert cells[day("2025-08-28")].ok is True
    assert cells[day("2025-08-28")].count_ratio_00 == pytest.approx(1.0)
    assert cells[day("2025-08-28")].sum_ratio_00 == pytest.approx(1.8)
    # ... but 2025-08-29 is a GLOBAL DEFECT DATE: dropped entirely, never
    # readable, a missing cell for the window census
    assert day("2025-08-29") not in cells
    assert day("2025-08-30") in cells
    # a day with a non-finite 00:00 observation is a MISSING cell, not data
    hole_root = build_root(
        tmp_path / "hole",
        metrics_start=day("2025-08-25"),
        metrics_end=day("2025-09-02"),
        klines_start=day("2025-08-25"),
        klines_end=day("2025-09-02"),
        funding_end=day("2025-09-02"),
        malformed_metrics_days={
            "ONGUSDT": {day("2025-08-27"): "nonfinite_midnight"}
        },
    )
    ong = loader_mod.load_metric_cells(hole_root, "ONGUSDT")
    assert ong[day("2025-08-27")].ok is False
    btc = loader_mod.load_metric_cells(hole_root, "BTCUSDT")
    assert btc[day("2025-08-27")].ok is True


def test_v15f1_loader_fail_closed_on_structural_malformation(tmp_path):
    # (1) missing symbol file
    root = _tiny_root(tmp_path)
    (root / "metrics" / "SOLUSDT.parquet").unlink()
    with pytest.raises(loader_mod.FailClosed, match="missing"):
        loader_mod.load_metric_cells(root, "SOLUSDT")
    # (2) missing required column
    no_sum = build_root(
        tmp_path / "nocol",
        metrics_start=day("2025-08-10"),
        metrics_end=day("2025-08-11"),
        klines_start=day("2025-08-10"),
        klines_end=day("2025-08-11"),
        funding_end=day("2025-08-11"),
        drop_metrics_columns=("sum_toptrader_long_short_ratio",),
    )
    with pytest.raises(loader_mod.FailClosed, match="columns missing"):
        loader_mod.load_metric_cells(no_sum, "BTCUSDT")
    # (3) unparsable create_time label
    corrupt = build_root(
        tmp_path / "corrupt",
        metrics_start=day("2025-08-10"),
        metrics_end=day("2025-08-11"),
        klines_start=day("2025-08-10"),
        klines_end=day("2025-08-11"),
        funding_end=day("2025-08-11"),
        corrupt_create_time_symbol="BTCUSDT",
    )
    with pytest.raises(loader_mod.FailClosed, match="unparsable"):
        loader_mod.load_metric_cells(corrupt, "BTCUSDT")
    # (4) kline day with a missing 15m slot (execution authority: the grid
    # check is zero tolerance per amendment_1)
    import pyarrow.parquet as pq

    gapped = build_root(
        tmp_path / "gap",
        metrics_start=day("2025-08-10"),
        metrics_end=day("2025-08-21"),
        klines_start=day("2025-08-10"),
        klines_end=day("2025-08-21"),
        funding_end=day("2025-08-21"),
    )
    bars_path = gapped / "klines" / "BTCUSDT.parquet"
    table = pq.read_table(bars_path)
    stamps = table.column("open_time_ms").to_pylist()
    # drop the SECOND bar of 2025-08-15 (its 00:15 slot) by UTC timestamp
    import datetime as _dt

    day_start_ms = int(
        _dt.datetime(2025, 8, 15, tzinfo=_dt.timezone.utc).timestamp()
    ) * 1000
    drop_ms = day_start_ms + 900_000
    keep = [i for i, ms in enumerate(stamps) if ms != drop_ms]
    assert len(keep) == len(stamps) - 1
    pq.write_table(
        table.take(keep),
        bars_path,
    )
    with pytest.raises(loader_mod.FailClosed, match="96"):
        loader_mod.load_klines(gapped, "BTCUSDT")
    # (5) funding beyond the documented extreme cap 0.0375 (the measured
    # -0.02 floor events are LEGITIMATE data and pass)
    capped = build_root(
        tmp_path / "fund",
        metrics_start=day("2025-08-10"),
        metrics_end=day("2025-08-11"),
        klines_start=day("2025-08-10"),
        klines_end=day("2025-08-11"),
        funding_end=day("2025-08-11"),
        funding_rate_fn=lambda sym, _day: -0.02,
    )
    assert len(loader_mod.load_funding(capped, "BTCUSDT")) == 2 * 3
    breach = build_root(
        tmp_path / "fund2",
        metrics_start=day("2025-08-10"),
        metrics_end=day("2025-08-11"),
        klines_start=day("2025-08-10"),
        klines_end=day("2025-08-11"),
        funding_end=day("2025-08-11"),
        funding_rate_fn=lambda sym, _day: 0.0376,
    )
    with pytest.raises(loader_mod.FailClosed, match="extreme cap"):
        loader_mod.load_funding(breach, "BTCUSDT")


def test_v15f1_staged_root_json_records_absolute_machine_root():
    import json

    payload = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "research/v15/families/elite_size_asym/staged_root.json"
        ).read_text(encoding="utf-8")
    )
    root = loader_mod.staged_data_root()
    assert payload["data_root"] == str(root)
    assert Path(payload["data_root"]).is_absolute()
    assert payload["read_only"] is True
    assert payload["subtrees"] == {
        "metrics": "metrics",
        "klines": "klines",
        "funding": "funding",
    }
    # the recorded root is the machine-local staged tree (existence only;
    # NO staged byte is read by any test)
    assert root.is_dir()


# --------------------------------------------------------------------------- #
# Refusal registry
# --------------------------------------------------------------------------- #
def test_v15f1_arm_config_digests_recorded_match_and_pairwise_unique():
    # recorded at implementation time with ZERO scored V15 cells; the
    # recorded digests carry the A1-ordered PRE-SCORE gross-cap remediation
    # (the sizing procedure is a digest input), so the values changed with
    # the remediation and are re-pinned in frozen_identity
    report = verify_arm_digests()
    assert report["all_match"] is True
    assert report["pairwise_unique"] is True
    assert report["ok"] is True
    assert set(report["arms"]) == {ANCHOR_ARM, NEIGHBOR_ARM, CONTROL_ARM}
    for arm_id, entry in report["arms"].items():
        assert entry["computed_from_identity"] == entry["recorded_in_freeze"]
        assert len(entry["computed_from_identity"]) == 64


def test_v15f1_sizing_procedure_carries_the_remediation_in_every_config():
    from research.v15.families.elite_size_asym.frozen_identity import (
        REMEDIATION_NOTE,
        frozen_arm_config,
    )

    for arm_id in (ANCHOR_ARM, NEIGHBOR_ARM, CONTROL_ARM):
        config = frozen_arm_config(arm_id)
        assert "residual budget GROSS_MAX - sum|carried refused weights|" in (
            config["sizing_procedure"]
        )
        assert config["remediation_note"] == REMEDIATION_NOTE
    # the control stays structurally the same book on the level feature and
    # never promotable
    assert frozen_arm_config(CONTROL_ARM)["control_never_promotable"] is True


def test_v15f1_staged_root_digest_table_mirrors_frozen_identity():
    import json

    payload = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "research/v15/families/elite_size_asym/staged_root.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["arm_config_digests"] == ARM_CONFIG_DIGESTS
    assert "gross-cap remediation A1-ordered pre-score" in payload[
        "remediation_note"
    ]
    assert "budget still 0/6" in payload["remediation_note"]


def test_v15f1_refusal_registry_append_once_and_digest():
    registry = RefusalRegistry()
    assert registry.record_window_hole("2025-09-01", "ONGUSDT", "detail-a")
    assert not registry.record_window_hole(
        "2025-09-01", "ONGUSDT", "detail-a-again"
    )  # append-ONCE per (date, symbol, reason)
    assert registry.record_window_hole("2025-09-02", "ONGUSDT", "detail-b")
    assert registry.record_window_hole("2025-09-01", "BTCUSDT", "detail-c")
    assert len(registry) == 3
    records = registry.records()
    assert [r["decision_date"] for r in records] == [
        "2025-09-01",
        "2025-09-01",
        "2025-09-02",
    ]
    summary = registry.summary()
    assert summary["n_refusals"] == 3
    assert summary["by_symbol"] == {"BTCUSDT": 1, "ONGUSDT": 2}
    # deterministic digest; different content -> different digest
    again = RefusalRegistry()
    again.record_window_hole("2025-09-01", "ONGUSDT", "detail-a")
    again.record_window_hole("2025-09-02", "ONGUSDT", "detail-b")
    again.record_window_hole("2025-09-01", "BTCUSDT", "detail-c")
    assert again.digest() == registry.digest()
    differing = RefusalRegistry()
    differing.record_window_hole("2025-09-01", "ONGUSDT", "other")
    assert differing.digest() != registry.digest()
