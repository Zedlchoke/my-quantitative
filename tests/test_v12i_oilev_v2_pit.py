"""V12 I lane -- PIT / completed-bar / close-decode tests for OILEV-V2.

Covers the PIT obligations the freeze binds:

* the OI anchor is the last COMPLETED daily row STRICTLY BEFORE the
  stamp (a row AT or AFTER the stamp is never consumed);
* the frozen 48h staleness gate fails a symbol closed (ineligible, never
  guessed);
* non-positive or uncomputable features are ineligible;
* fills execute at the open of the 15m bar covering the decision
  instant (the one declared execution lag), walking strictly later bars
  under event delay, with NO_EVENT when no bar exists;
* the A9-F F7 close decode (raw i128 / 1e16) is exact and round-trips;
* real-data C1-style field verification (skipped when the read-only
  workspace data is absent).

No scored metric is computed anywhere.
"""

from __future__ import annotations

import math

import pytest

from research.v11.families.oilever_delev.strategy import (
    Bar,
    oi_anchor_before,
    oi_flow_growth,
    oi_stock_percentile,
    resolve_fill_event,
)
from research.v12.families.oilev_v2.audits import (
    decode_i128_price,
    evidence_c1_field_verification,
)
from research.v12.families.oilev_v2.plugin import OilevV2Plugin
from research.v12.families.oilev_v2.strategy import (
    ANCHOR_ARM,
    parse_iso_utc,
    signal_scores_at,
    stamp_calendar,
)

DAY_NS = 86_400_000_000_000
HOUR_NS = 3_600_000_000_000


def _iso(iso: str) -> int:
    return parse_iso_utc(iso)


def _daily(sym_value_by_day: dict[int, float], *, start_day_ns: int, days: int) -> tuple[tuple[int, float], ...]:
    return tuple(
        (start_day_ns + d * DAY_NS + 23 * HOUR_NS + 55 * 60 * 1_000_000_000, value)
        for d, value in (
            (d, sym_value_by_day.get(d, 1_000_000.0 + d)) for d in range(days)
        )
    )


def _world(rows_by_symbol: dict[str, tuple[tuple[int, float], ...]]):
    stamp = stamp_calendar()[0]
    from research.v11.families.oilever_delev.strategy import Bar

    bars = {
        sym: (
            Bar(
                ts_event_ns=stamp + 900_000_000_000,
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
            ),
            Bar(
                ts_event_ns=stamp + 1_800_000_000_000,
                open=100.5,
                high=101.5,
                low=100.0,
                close=101.0,
            ),
        )
        for sym in rows_by_symbol
    }
    bars["BTCUSDT"] = bars[next(iter(rows_by_symbol))]
    return stamp, bars


def test_oi_row_at_the_stamp_is_never_consumed() -> None:
    stamp = stamp_calendar()[0]
    # a row EXACTLY at the stamp must be ignored; the strictly-before row wins
    series = (
        (stamp - 29 * DAY_NS, 1_000_000.0),
        (stamp - 1 * DAY_NS + 23 * HOUR_NS + 55 * 60 * 1_000_000_000, 1_200_000.0),
        (stamp, 9_999_999.0),  # planted trap AT the stamp
    )
    anchor = oi_anchor_before(series, stamp)
    assert anchor == 1_200_000.0


def test_oi_row_after_the_stamp_is_never_consumed() -> None:
    stamp = stamp_calendar()[0]
    series = (
        (stamp - 2 * DAY_NS, 1_000_000.0),
        (stamp + 1, 2_000_000.0),  # fresher but AFTER the stamp
    )
    assert oi_anchor_before(series, stamp) == 1_000_000.0


def test_stale_oi_beyond_48h_is_ineligible() -> None:
    stamp = stamp_calendar()[0]
    stale = stamp - 49 * HOUR_NS
    series = ((stale, 5_000_000.0),)
    assert oi_anchor_before(series, stamp) is None
    world = {"GOODSYM": _daily({}, start_day_ns=stamp - 40 * DAY_NS, days=40)}
    world["OLDSYM"] = tuple(
        (stamp - 3 * DAY_NS - d * DAY_NS, 1_000_000.0 + d) for d in range(40)
    )
    # OLDSYM's last row is 3 days stale -> ineligible at the stamp
    scores = signal_scores_at(
        ANCHOR_ARM, oi_by_symbol=world, stamp_ns=stamp, universe=sorted(world)
    )
    assert "OLDSYM" not in scores
    assert "GOODSYM" in scores


def test_non_positive_oi_is_ineligible() -> None:
    stamp = stamp_calendar()[0]
    series = ((stamp - DAY_NS, 0.0),)
    assert oi_anchor_before(series, stamp) is None
    assert oi_flow_growth(series, stamp) is None


def test_oi_stock_needs_two_window_points() -> None:
    stamp = stamp_calendar()[0]
    one_point = ((stamp - DAY_NS, 1_000_000.0),)
    assert oi_stock_percentile(one_point, stamp) is None
    two_points = (
        (stamp - 2 * DAY_NS, 1_000_000.0),
        (stamp - DAY_NS, 1_500_000.0),
    )
    assert oi_stock_percentile(two_points, stamp) == 1.0


def test_oi_flow_growth_is_the_inherited_28d_log_growth() -> None:
    stamp = stamp_calendar()[0]
    past = math.exp(-0.4)
    now = 1.0
    series = (
        (stamp - 29 * DAY_NS, past),
        (stamp - DAY_NS + 23 * HOUR_NS + 55 * 60 * 1_000_000_000, now),
    )
    assert oi_flow_growth(series, stamp, formation_days=28) == pytest.approx(
        0.4, abs=1e-12
    )


def test_fill_at_open_of_covering_bar_with_declared_lag() -> None:
    stamp = stamp_calendar()[0]
    bars = (
        # the completed bar terminating at the stamp boundary (raw ~1ms
        # artifact: the close sits 999_936ns before the nominal grid line)
        Bar(ts_event_ns=stamp - 999_936, open=99.0, high=100.0, low=98.0,
            close=99.5),
        Bar(ts_event_ns=stamp + 900_000_000_000, open=100.0, high=101.0,
            low=99.0, close=100.5),
        Bar(ts_event_ns=stamp + 1_800_000_000_000, open=100.5, high=101.5,
            low=100.0, close=101.0),
    )
    event = resolve_fill_event(bars, "SYM00", decision_ns=stamp)
    assert event is not None
    assert event.fill_open_ns == stamp  # bar opening exactly at the decision
    assert event.price == 100.0
    assert event.event_offset == 0
    delayed = resolve_fill_event(
        bars, "SYM00", decision_ns=stamp, event_delay_events=1
    )
    assert delayed is not None
    assert delayed.fill_open_ns == stamp + 900_000_000_000
    assert delayed.price == 100.5
    assert resolve_fill_event((), "SYM00", decision_ns=stamp) is None


def test_close_decode_i128_over_1e16_is_exact() -> None:
    for price in (100.0, 123.4567890123, 0.00012345, 98765.4321):
        raw = round(price * 1e16)
        blob = raw.to_bytes(16, "little", signed=True)
        decoded, raw_int = decode_i128_price(blob)
        assert raw_int == raw
        # the decode IS the frozen rule: raw i128 / 1e16 (bit-identical to
        # the same division); round-trip error is float64 ULP-scale only
        assert decoded == raw_int / 1e16
        rel_err = abs(decoded - price) / price
        assert rel_err <= 1e-15
    with pytest.raises(ValueError):
        decode_i128_price((-5).to_bytes(16, "little", signed=True))


def test_plugin_marks_and_fills_use_completed_bars_only() -> None:
    stamp = stamp_calendar()[0]
    bars = (
        Bar(ts_event_ns=stamp - 999_936, open=99.0, high=100.0, low=98.0,
            close=99.5),
        Bar(ts_event_ns=stamp + 900_000_000_000, open=100.0, high=101.0,
            low=99.0, close=100.5),
    )
    plugin = _plugin_with_bars({"SYM00": bars, "SYM01": bars})
    marks = plugin.marks_at(["SYM00"], stamp)
    assert marks["SYM00"] == pytest.approx(100.0)  # open of the covering bar
    fills = plugin.fills_at(stamp, symbols=["SYM00"], stress=plugin.baseline_stress())
    assert fills[0].applied and fills[0].price == pytest.approx(100.0)
    # an instant whose covering bar does not exist -> NO_EVENT, never a
    # shifted substitute (the only bars live 30 days away from the stamp)
    far = Bar(ts_event_ns=stamp + 30 * DAY_NS, open=50.0, high=51.0,
              low=49.0, close=50.5)
    empty = _plugin_with_bars({"SYM00": (far,), "SYM01": (far,)})
    records = empty.fills_at(stamp, symbols=["SYM00"], stress=empty.baseline_stress())
    assert records[0].applied is False
    assert records[0].price is None


def _plugin_with_bars(bars_by_symbol, stamp=None):
    base = parse_iso_utc("2025-06-20T00:00:00Z")
    oi = {
        sym: tuple(
            (base + d * DAY_NS + 23 * HOUR_NS + 55 * 60 * 1_000_000_000,
             1_000_000.0 + i * 1000.0 + d)
            for d in range(90)
        )
        for i, sym in enumerate(sorted(set(bars_by_symbol) - {"BTCUSDT"}))
    }
    bars = dict(bars_by_symbol)
    bars.setdefault("BTCUSDT", next(iter(bars_by_symbol.values())))
    return OilevV2Plugin(
        arm_id=ANCHOR_ARM,
        oi_by_symbol=oi,
        bars_by_symbol=bars,
    )


def _has_real_data() -> bool:
    from pathlib import Path

    return Path("/Users/hoangminhlong/my-quantitative/oi_data/consolidated").is_dir()


@pytest.mark.skipif(not _has_real_data(), reason="read-only workspace data absent")
def test_real_data_c1_field_verification_passes() -> None:
    payload = evidence_c1_field_verification()
    assert payload["all_oi_anchor_fields_pit_correct"] is True
    assert payload["all_execution_bar_fields_verified"] is True
    for stamp_row in payload["per_stamp"]:
        assert len(stamp_row["oi_anchor_fields"]) == 19
        for field in stamp_row["oi_anchor_fields"]:
            assert field["strictly_before_target"] is True
            assert field["within_48h_gate"] is True
            assert field["loader_selected_value_matches_parquet"] is True
        for check in stamp_row["execution_bar_checks"]:
            assert check["close_decode_exact"] is True
            assert check["open_at_or_after_decision"] is True
