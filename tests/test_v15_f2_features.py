"""V15 I lane (i-family-2) -- TAKER-SAT feature goldens + fail-closed loader.

HAND-COMPUTED synthetic fixtures only; no real staged data is read.

* clip/log hygiene goldens (r=10 -> 1.609; r=e -> 1.0; r=0.01 -> -1.609;
  in-band values pass through as ln r);
* the daily FLOW aggregate: 288 labels consumed exactly once per
  metrics_date -- a boundary stamp appears in exactly one 5-minute bucket of
  one day (no double-count across adjacent days);
* positioning churn + the frozen saturation ratio-of-ratio goldens;
* the lag structure: window ends at D-3; mutating rows at D-2..D cannot
  move a score (no-lookahead);
* the amendment-1 hole rule at the exact 10% boundary (integer-exact);
* the causal control's structural independence (no OI consumed);
* loader integrity: global defect dates, incomplete grid, NaN fields,
  duplicate labels, missing file, ts/label mismatch -- all fail closed.

Nothing is scored; no PnL anywhere.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest
from research.adapter_v10.protocol import ContractViolation

from research.v15.families.taker_sat import features
from research.v15.families.taker_sat.features import (
    DEFECT_BAD_VALUE,
    DEFECT_DUPLICATE_LABEL,
    DEFECT_GRID_INCOMPLETE,
    LABELS_PER_DAY,
    MISSING_GLOBAL_DEFECT_DATE,
    REFUSE_ENDPOINT_MISSING,
    REFUSE_HOLE_FRACTION,
    StagedDataError,
)

SYM = "BTCX"


def _labels() -> list[str]:
    out: list[str] = []
    for hour in range(24):
        for minute in (0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55):
            out.append(f"{hour:02d}:{minute:02d}:00")
    return out


# --------------------------------------------------------------------------- #
# Hygiene + daily aggregate goldens (hand-computed)
# --------------------------------------------------------------------------- #
def test_v15f2_clip_log_ratio_goldens():
    assert features.clip_log_ratio(10.0) == 1.609
    assert features.clip_log_ratio(math.e) == 1.0
    assert features.clip_log_ratio(0.01) == -1.609
    assert features.clip_log_ratio(0.1) == -1.609  # clip to 0.2 first
    assert features.clip_log_ratio(5.0) == 1.609   # ln 5 clips at the top
    assert features.clip_log_ratio(0.2) == -1.609  # ln 0.2 clips at the floor
    assert features.clip_log_ratio(4.9) == pytest.approx(math.log(4.9))  # in-band
    assert features.clip_log_ratio(0.21) == pytest.approx(math.log(0.21))
    assert features.clip_log_ratio(0.3) == pytest.approx(-1.2039728043259361)
    assert features.clip_log_ratio(3.0) == pytest.approx(1.0986122886681098)
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ContractViolation):
            features.clip_log_ratio(bad)


def test_v15f2_daily_aggression_flow_bucket_goldens():
    # 288 identical in-band labels: the mean is the clipped log itself.
    assert features.daily_aggression(
        {label: math.e for label in _labels()}
    ) == 1.0
    # dead-hour near-zero denominators clip to the 0.2 floor: a = -1.609.
    assert features.daily_aggression(
        {label: 0.05 for label in _labels()}
    ) == -1.609
    # half e / half e^0.5: (144*1.0 + 144*0.5)/288 = 0.75 exactly.
    labels = _labels()
    ratios = {label: math.e for label in labels[:144]}
    ratios.update({label: math.e**0.5 for label in labels[144:]})
    assert features.daily_aggression(ratios) == 0.75
    # a stamp must appear in EXACTLY ONE bucket: a mapping whose iteration
    # repeats a label refuses (append-once bucket identity), and the count
    # is pinned at 288 (a refused cell never aggregates).
    class _RepeatMap(dict):
        def items(self):
            pairs = list(dict.items(self))
            return pairs + [pairs[0]]

    with pytest.raises(Exception) as exc:
        features.daily_aggression(_RepeatMap({label: math.e for label in labels}))
    assert "exactly one bucket" in str(exc.value)
    with pytest.raises(Exception):
        features.daily_aggression({label: math.e for label in labels[:100]})


def test_v15f2_flow_boundary_no_double_count_across_days():
    """The 23:55 label of day d covers [23:55, 00:00) and belongs to day d's
    aggregate only; day d+1's 00:00 stamp is a different bucket."""
    day1 = {"2025-01-08 " + label: math.e for label in _labels()}
    day2 = {"2025-01-09 " + label: math.e**0.5 for label in _labels()}
    both = {**day1, **day2}
    assert len(both) == 2 * LABELS_PER_DAY  # no shared stamps
    day1_keys = [k for k in both if k.startswith("2025-01-08")]
    day2_keys = [k for k in both if k.startswith("2025-01-09")]
    assert len(day1_keys) == LABELS_PER_DAY and len(day2_keys) == LABELS_PER_DAY
    # aggregating each day separately == aggregating any partition of the
    # concatenated stream by its own labels (no cross-day bleed)
    a1 = features.daily_aggression({k: both[k] for k in day1_keys})
    a2 = features.daily_aggression({k: both[k] for k in day2_keys})
    assert a1 == 1.0 and a2 == 0.5
    # mutating the NEXT day's 00:00 flow can never move day 1's aggregate
    mutated = dict(both)
    mutated["2025-01-09 00:00:00"] = 4.999
    a1_mutated = features.daily_aggression(
        {k: mutated[k] for k in day1_keys}
    )
    assert a1_mutated == a1


def test_v15f2_churn_and_saturation_goldens():
    assert features.positioning_churn(100.0, 110.0) == pytest.approx(
        0.09531017980432486
    )
    assert features.positioning_churn(100.0, 200.0) == pytest.approx(
        math.log(2.0)
    )
    assert features.positioning_churn(110.0, 100.0) == pytest.approx(
        0.09531017980432486
    )  # absolute value: direction-free churn
    score = features.saturation_score(0.5, features.positioning_churn(100.0, 110.0))
    assert score == pytest.approx(0.5 / (0.09531017980432486 + 0.02))
    # the frozen floor: zero churn still divides by c = 0.02
    assert features.saturation_score(1.0, 0.0) == 50.0
    for bad in ((0.0, 1.0), (1.0, 0.0), (-5.0, 1.0)):
        with pytest.raises(Exception):
            features.positioning_churn(*bad)


# --------------------------------------------------------------------------- #
# Window / lag / hole-rule structure
# --------------------------------------------------------------------------- #
def _day_ns(date_str: str) -> int:
    return features.date_str_to_ns(date_str)


def test_v15f2_window_ends_exactly_at_D_minus_3():
    d = _day_ns("2025-01-20")
    window10 = features.window_dates(d, 10)
    window21 = features.window_dates(d, 21)
    assert features.ns_to_date_str(window10[-1]) == "2025-01-17"  # D-3
    assert features.ns_to_date_str(window10[0]) == "2025-01-08"   # D-12
    # ADJUDICATED_BY_A1 (pre-score): the neighbour binds the explicit dated
    # range [D-23, D-3] inclusive = 21 daily aggregates (the prose count
    # "20" was a draft remnant)
    assert features.ns_to_date_str(window21[0]) == "2024-12-28"   # D-23
    assert features.ns_to_date_str(window21[-1]) == "2025-01-17"  # D-3
    assert len(window10) == 10 and len(window21) == 21
    assert all(stamp < d for stamp in window10 + window21)


def _daily_fixture(
    dates: list[str], a: float = 0.5, oi: float | dict[str, float] = 100.0
) -> dict[int, dict[str, float]]:
    out: dict[int, dict[str, float]] = {}
    for date_str in dates:
        value = oi.get(date_str, 100.0) if isinstance(oi, dict) else oi
        out[_day_ns(date_str)] = {"a": a, "oi2355": value}
    return out


WINDOW10 = [f"2025-01-{day:02d}" for day in range(8, 18)]  # [D-12, D-3]


def test_v15f2_anchor_feature_golden():
    daily = _daily_fixture(WINDOW10, a=0.5, oi={"2025-01-08": 100.0, "2025-01-17": 110.0})
    score, reason = features.evaluate_symbol_feature(
        window_days=10,
        with_churn=True,
        daily_by_date=daily,
        decision_date_ns=_day_ns("2025-01-20"),
    )
    assert reason is None
    assert score == pytest.approx(0.5 / (math.log(1.1) + 0.02))


def test_v15f2_neighbour_window_golden():
    # ADJUDICATED_BY_A1: [D-23, D-3] inclusive = 21 daily aggregates
    dates = [f"2024-12-{day:02d}" for day in range(28, 32)] + [
        f"2025-01-{day:02d}" for day in range(1, 18)
    ]
    assert len(dates) == 21
    daily = _daily_fixture(dates, a=0.5, oi={"2024-12-28": 100.0, "2025-01-17": 200.0})
    score, reason = features.evaluate_symbol_feature(
        window_days=21,
        with_churn=True,
        daily_by_date=daily,
        decision_date_ns=_day_ns("2025-01-20"),
    )
    assert reason is None
    assert score == pytest.approx(0.5 / (math.log(2.0) + 0.02))


def test_v15f2_lag_no_lookahead_mutation():
    """A decision at D never reads metrics dated after D-3: mutating the
    daily aggregates at D-2, D-1, D moves NOTHING."""
    d = _day_ns("2025-01-20")
    daily = _daily_fixture(WINDOW10, a=0.5, oi={"2025-01-08": 100.0, "2025-01-17": 110.0})
    baseline, reason = features.evaluate_symbol_feature(
        window_days=10, with_churn=True, daily_by_date=daily, decision_date_ns=d
    )
    assert reason is None
    mutated = dict(daily)
    for date_str in ("2025-01-18", "2025-01-19", "2025-01-20"):
        mutated[_day_ns(date_str)] = {"a": 100.0, "oi2355": 999.0}
    after, reason_after = features.evaluate_symbol_feature(
        window_days=10, with_churn=True, daily_by_date=mutated, decision_date_ns=d
    )
    assert reason_after is None
    assert after == baseline


def test_v15f2_hole_rule_exact_10_percent_boundary():
    # 1 missing day in 10 = exactly 10% -> computes over the available days.
    drop1 = _day_ns("2025-01-12")
    holey = {
        d: v
        for d, v in _daily_fixture(
            WINDOW10, oi={"2025-01-08": 100.0, "2025-01-17": 110.0}
        ).items()
        if d != drop1
    }
    score, reason = features.evaluate_symbol_feature(
        window_days=10, with_churn=True, daily_by_date=holey,
        decision_date_ns=_day_ns("2025-01-20"),
    )
    assert reason is None
    assert score == pytest.approx(0.5 / (math.log(1.1) + 0.02))
    # 2 missing days in 10 = 20% > 10% -> REFUSED
    holey2 = {d: v for d, v in holey.items() if d != _day_ns("2025-01-13")}
    score2, reason2 = features.evaluate_symbol_feature(
        window_days=10, with_churn=True, daily_by_date=holey2,
        decision_date_ns=_day_ns("2025-01-20"),
    )
    assert score2 is None and reason2 == REFUSE_HOLE_FRACTION
    # neighbour window n=21 ([D-23, D-3], A1 adjudication): 2 missing
    # (2/21 ~= 9.5%, not more than 10%) computes, 3 (3/21 ~= 14.3%) refuses.
    dates21 = [f"2024-12-{day:02d}" for day in range(28, 32)] + [
        f"2025-01-{day:02d}" for day in range(1, 18)
    ]
    assert len(dates21) == 21
    daily21 = _daily_fixture(dates21, oi={"2024-12-28": 100.0, "2025-01-17": 200.0})
    drop2 = {d: v for d, v in daily21.items() if d not in (_day_ns("2025-01-05"), _day_ns("2025-01-06"))}
    score3, reason3 = features.evaluate_symbol_feature(
        window_days=21, with_churn=True, daily_by_date=drop2,
        decision_date_ns=_day_ns("2025-01-20"),
    )
    assert reason3 is None
    assert score3 == pytest.approx(0.5 / (math.log(2.0) + 0.02))
    drop3 = {d: v for d, v in drop2.items() if d != _day_ns("2025-01-07")}
    score4, reason4 = features.evaluate_symbol_feature(
        window_days=21, with_churn=True, daily_by_date=drop3,
        decision_date_ns=_day_ns("2025-01-20"),
    )
    assert score4 is None and reason4 == REFUSE_HOLE_FRACTION


def test_v15f2_churn_endpoint_missing_refuses_anchor_but_not_control():
    daily = {
        d: v
        for d, v in _daily_fixture(WINDOW10).items()
        if d != _day_ns("2025-01-08")  # the FIRST churn endpoint is missing
    }
    score, reason = features.evaluate_symbol_feature(
        window_days=10, with_churn=True, daily_by_date=daily,
        decision_date_ns=_day_ns("2025-01-20"),
    )
    assert score is None and reason == REFUSE_ENDPOINT_MISSING
    # the causal control consumes NO OI: identical data, identical window,
    # computes the raw intensity (structural independence from the anchor).
    score_ctl, reason_ctl = features.evaluate_symbol_feature(
        window_days=10, with_churn=False, daily_by_date=daily,
        decision_date_ns=_day_ns("2025-01-20"),
    )
    assert reason_ctl is None
    assert score_ctl == pytest.approx(0.5)


def test_v15f2_control_is_structurally_distinct_from_anchor():
    """Equal raw intensity, different churn: the anchor separates, the
    control ties -> the churn denominator does causal work."""
    x = _daily_fixture(WINDOW10, a=1.0, oi={"2025-01-08": 100.0, "2025-01-17": 164.872127})
    y = _daily_fixture(WINDOW10, a=0.9, oi=100.0)  # zero churn
    d = _day_ns("2025-01-20")
    x_anchor, _ = features.evaluate_symbol_feature(
        window_days=10, with_churn=True, daily_by_date=x, decision_date_ns=d
    )
    y_anchor, _ = features.evaluate_symbol_feature(
        window_days=10, with_churn=True, daily_by_date=y, decision_date_ns=d
    )
    x_ctl, _ = features.evaluate_symbol_feature(
        window_days=10, with_churn=False, daily_by_date=x, decision_date_ns=d
    )
    y_ctl, _ = features.evaluate_symbol_feature(
        window_days=10, with_churn=False, daily_by_date=y, decision_date_ns=d
    )
    # anchor: Y (45.0) ranks far above X (~1.92); control: X (1.0) above Y (0.9)
    assert x_ctl == pytest.approx(1.0) and y_ctl == pytest.approx(0.9)
    assert y_anchor == pytest.approx(45.0)
    assert x_anchor == pytest.approx(1.0 / (math.log(1.64872127) + 0.02))
    assert x_anchor < y_anchor
    assert x_ctl > y_ctl
    assert y_anchor > 40.0 > x_anchor  # separated by an order of magnitude


# --------------------------------------------------------------------------- #
# Loader: synthetic parquet world (fail-closed integrity)
# --------------------------------------------------------------------------- #
def _metrics_frame(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame["ts"] = pd.to_datetime(frame["create_time"], format="%Y-%m-%d %H:%M:%S")
    return frame


def _day_rows(
    date_str: str, ratio: float, oi: float, *, oi_2355: float | None = None
) -> list[dict]:
    rows = []
    for label in _labels():
        rows.append(
            {
                "create_time": f"{date_str} {label}",
                "symbol": SYM,
                "sum_open_interest": 1000.0,
                "sum_open_interest_value": oi_2355 if (oi_2355 is not None and label == "23:55:00") else oi,
                "count_toptrader_long_short_ratio": 1.0,
                "sum_toptrader_long_short_ratio": 1.0,
                "count_long_short_ratio": 1.0,
                "sum_taker_long_short_vol_ratio": ratio,
            }
        )
    return rows


def _write_symbol(root: Path, rows: list[dict], *, sym: str = SYM) -> None:
    (root / "metrics").mkdir(parents=True, exist_ok=True)
    _metrics_frame(rows).to_parquet(root / "metrics" / f"{sym}.parquet", index=False)


def test_v15f2_loader_golden_and_bucket_identity(tmp_path):
    rows = _day_rows("2025-01-08", math.e, 100.0, oi_2355=250.0)
    rows += _day_rows("2025-01-09", math.e**0.5, 100.0)
    _write_symbol(tmp_path, rows)
    daily, defects = features.load_metrics_daily(tmp_path, (SYM,))
    assert defects == []
    assert daily[SYM][_day_ns("2025-01-08")]["a"] == 1.0
    assert daily[SYM][_day_ns("2025-01-08")]["oi2355"] == 250.0
    assert daily[SYM][_day_ns("2025-01-09")]["a"] == 0.5
    assert daily[SYM][_day_ns("2025-01-09")]["oi2355"] == 100.0
    # boundary no-double-count through the LOADER: rewriting day 2's 00:00
    # flow stamp cannot move day 1's aggregate (each label lands in exactly
    # one daily bucket of its own metrics_date).
    rows2 = list(rows)
    idx = len(_labels()) + 0  # first row of day 2 == its 00:00 stamp
    rows2[idx]["sum_taker_long_short_vol_ratio"] = 4.999
    root2 = tmp_path / "mutated"
    _write_symbol(root2, rows2)
    daily2, _ = features.load_metrics_daily(root2, (SYM,))
    assert daily2[SYM][_day_ns("2025-01-08")] == daily[SYM][_day_ns("2025-01-08")]


def test_v15f2_loader_global_defect_dates_excluded(tmp_path):
    rows = _day_rows("2025-01-08", math.e, 100.0)
    rows += _day_rows("2025-08-29", math.e, 100.0)  # global defect date
    _write_symbol(tmp_path, rows)
    daily, defects = features.load_metrics_daily(tmp_path, (SYM,))
    assert _day_ns("2025-08-29") not in daily[SYM]
    assert defects == [
        {"symbol": SYM, "date": "2025-08-29", "reason": MISSING_GLOBAL_DEFECT_DATE}
    ]


@pytest.mark.parametrize(
    "mutate,reason",
    [
        ("drop_row", DEFECT_GRID_INCOMPLETE),
        ("nan_ratio", DEFECT_BAD_VALUE),
        ("duplicate_label", DEFECT_DUPLICATE_LABEL),
    ],
)
def test_v15f2_loader_defect_cells_fail_closed(tmp_path, mutate, reason):
    rows = _day_rows("2025-01-08", math.e, 100.0)
    rows += _day_rows("2025-01-09", math.e, 100.0)
    if mutate == "drop_row":
        rows = rows[:-1]  # 287 rows on day 2
    elif mutate == "nan_ratio":
        rows[len(_labels())]["sum_taker_long_short_vol_ratio"] = float("nan")
    elif mutate == "duplicate_label":
        rows[len(_labels()) + 1]["create_time"] = "2025-01-09 00:00:00"
    _write_symbol(tmp_path, rows)
    daily, defects = features.load_metrics_daily(tmp_path, (SYM,))
    assert daily[SYM].keys() == {_day_ns("2025-01-08")}
    assert len(defects) == 1
    assert defects[0]["reason"] == reason
    assert defects[0]["date"] == "2025-01-09"


def test_v15f2_loader_missing_file_and_ts_mismatch_raise(tmp_path):
    with pytest.raises(StagedDataError):
        features.load_metrics_daily(tmp_path, (SYM,))
    rows = _day_rows("2025-01-08", math.e, 100.0)
    _write_symbol(tmp_path, rows)
    # ts column disagreeing with the create_time label -> fail closed
    frame = _metrics_frame(rows)
    frame.loc[0, "ts"] = frame.loc[0, "ts"] + pd.Timedelta(minutes=5)
    root2 = tmp_path / "tsmut"
    (root2 / "metrics").mkdir(parents=True)
    frame.to_parquet(root2 / "metrics" / f"{SYM}.parquet", index=False)
    with pytest.raises(StagedDataError):
        features.load_metrics_daily(root2, (SYM,))


def test_v15f2_loader_rejects_nonpositive_ratio_and_oi(tmp_path):
    rows = _day_rows("2025-01-08", 0.0, 100.0)  # non-positive ratio
    _write_symbol(tmp_path, rows)
    daily, defects = features.load_metrics_daily(tmp_path, (SYM,))
    assert daily[SYM] == {}
    assert defects[0]["reason"] == DEFECT_BAD_VALUE
    rows2 = _day_rows("2025-01-09", math.e, 0.0)  # non-positive OI value
    root2 = tmp_path / "oi"
    _write_symbol(root2, rows2)
    daily2, defects2 = features.load_metrics_daily(root2, (SYM,))
    assert daily2[SYM] == {}
    assert defects2[0]["reason"] == DEFECT_BAD_VALUE
