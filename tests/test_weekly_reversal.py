"""V8P T13 unit tests: weekly reversal signal + runner wiring (PLAN section 5).

Frozen-behavior coverage mandated by PLAN section 5.2 items 1-4 and 6:

* Monday 00:00 UTC scheduling across year/month boundaries, duplicate-free;
* no forming/future bar ever enters the formation return (PIT <= cutoff);
* deterministic tie-breaking (symbol ascending at 1e-12 tolerance);
* missing symbol / short panel skips the WHOLE rebalance (all-six rule);
* bottom/top legs exact for reversal and WMOM control directions;
* weight normalization to the 0.80 gross target;
* 7-day fold purge/embargo stamp filter;
* dispatcher/env wiring (family routing, --control-momentum passthrough,
  derived diagnostics rows including skipped_reason).
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research import portfolio_runner as pr  # noqa: E402
from research.weekly_reversal import (  # noqa: E402
    DAY_NS,
    compute_target_weights_weekly_reversal as wrev,
    formation_return,
    monday_cutoffs,
    weekly_rebalance_stamps,
)

UTC = timezone.utc
ANCHOR = datetime(2025, 12, 1, tzinfo=UTC)  # day 0
CUTOFF_DT = ANCHOR + timedelta(days=42)  # 2026-01-12T00:00Z (Monday)
CUTOFF_NS = int(CUTOFF_DT.timestamp() * 1_000_000_000)

SYMBOLS = ("AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT", "EEEUSDT", "FFFUSDT")


def ns(day_index: int) -> int:
    return int((ANCHOR + timedelta(days=day_index)).timestamp() * 1_000_000_000)


def flat_panel(price: float = 100.0) -> dict[str, list[tuple[int, float]]]:
    return {
        sym: [(ns(d), price) for d in range(43)] for sym in SYMBOLS
    }


def directional_panel() -> dict[str, list[tuple[int, float]]]:
    """Formation returns at the Jan12 cutoff (refs: 7D -> day 35, 3D -> day 39):

        symbol   7D      3D
        AAA      -60%    -60%
        BBB      -50%    -4.7619%
        CCC        0       0
        DDD      +1%     +1%
        EEE      +41%    +0.714286%
        FFF      +150%     0

    so the 7D reversal shorts are {EEE, FFF} but the 3D shorts are
    {EEE, DDD} -- lookback routing is observable in the picks."""
    panel = flat_panel()
    panel["AAAUSDT"][35] = (ns(35), 100.0)
    panel["AAAUSDT"][39] = (ns(39), 100.0)
    panel["AAAUSDT"][42] = (ns(42), 40.0)
    panel["BBBUSDT"][35] = (ns(35), 200.0)
    panel["BBBUSDT"][39] = (ns(39), 105.0)
    panel["BBBUSDT"][42] = (ns(42), 100.0)
    panel["DDDUSDT"][42] = (ns(42), 101.0)
    panel["EEEUSDT"][35] = (ns(35), 100.0)
    panel["EEEUSDT"][39] = (ns(39), 140.0)
    panel["EEEUSDT"][42] = (ns(42), 141.0)
    panel["FFFUSDT"][39] = (ns(39), 250.0)
    panel["FFFUSDT"][42] = (ns(42), 250.0)
    return panel


def run_signal(panel, *, lookback=7, reverse=False, control=False,
               symbols=SYMBOLS, target_gross=0.80):
    return wrev(
        signal_cutoff_ns=CUTOFF_NS,
        formation_lookback_days=lookback,
        reverse=reverse,
        daily_closes=panel,
        traded_symbols=symbols,
        target_gross=target_gross,
        control_momentum=control,
    )


# --------------------------------------------------------------------------- #
# 1) Monday schedule: UTC, year/month boundary, duplicates (PLAN 5.2 item 1)
# --------------------------------------------------------------------------- #
def test_monday_schedule_year_month_boundary_no_duplicates():
    stamps = monday_cutoffs(datetime(2025, 12, 28, tzinfo=UTC),
                            datetime(2026, 1, 8, tzinfo=UTC))
    assert [s.isoformat() for s in stamps] == [
        "2025-12-29T00:00:00+00:00", "2026-01-05T00:00:00+00:00",
    ]
    month_edge = monday_cutoffs(datetime(2026, 1, 31, tzinfo=UTC),
                                datetime(2026, 2, 9, tzinfo=UTC))
    assert [s.isoformat() for s in month_edge] == ["2026-02-02T00:00:00+00:00"]
    for stamp in (*stamps, *month_edge):
        assert stamp.tzinfo is UTC or stamp.utcoffset() == timedelta(0)
        assert stamp.weekday() == 0
        assert (stamp.hour, stamp.minute, stamp.second, stamp.microsecond) == \
            (0, 0, 0, 0)
    span = monday_cutoffs(datetime(2025, 1, 1, tzinfo=UTC),
                          datetime(2026, 1, 1, tzinfo=UTC))
    assert len(span) == len({s.isoformat() for s in span}) == 52
    assert all(a < b for a, b in zip(span, span[1:]))


def test_monday_schedule_half_open_end_and_tz_normalization():
    # End-edge Monday excluded ([start, end) mirrors daily_rebalance_stamps).
    assert [s.day for s in monday_cutoffs(
        datetime(2026, 1, 5, tzinfo=UTC), datetime(2026, 1, 12, tzinfo=UTC))] \
        == [5]
    # Non-UTC input normalized: 02:00+02:00 == 00:00Z that Monday.
    tz_input = datetime(2026, 1, 5, 2, 0, tzinfo=timezone(timedelta(hours=2)))
    stamps = monday_cutoffs(tz_input, datetime(2026, 1, 13, tzinfo=UTC))
    assert [s.isoformat() for s in stamps] == [
        "2026-01-05T00:00:00+00:00", "2026-01-12T00:00:00+00:00",
    ]


# --------------------------------------------------------------------------- #
# 2) PIT: forming/future bars never enter the rank (PLAN 5.2 item 2)
# --------------------------------------------------------------------------- #
def test_lookahead_exclusion_future_and_forming_bars():
    panel = directional_panel()
    baseline = run_signal(panel)

    contaminated = directional_panel()
    contaminated["AAAUSDT"].append((CUTOFF_NS + 1, 10_000.0))  # 1ns future
    contaminated["FFFUSDT"].append((CUTOFF_NS + 12 * 3_600_000_000, 0.0001))
    assert run_signal(contaminated) == baseline

    # The close stamped EXACTLY at the cutoff IS completed and used.
    formed = directional_panel()
    formed["EEEUSDT"][-1] = (ns(42), 90.0)
    moved = run_signal(formed)
    assert formation_return(formed["EEEUSDT"], cutoff_ns=CUTOFF_NS,
                            lookback_days=7) == pytest.approx(-0.10)
    # ... which re-ranks EEE into the middle: shorts swap FFF out for DDD.
    assert moved["shorts"] == [["DDDUSDT", -0.2], ["FFFUSDT", -0.2]]


def test_reference_close_is_latest_at_or_before_cutoff_minus_lookback():
    series = [(ns(35), 100.0), (ns(36), 500.0), (ns(42), 141.0)]
    # Decoy close INSIDE the window (day 36) must not become the reference.
    assert formation_return(series, cutoff_ns=CUTOFF_NS,
                            lookback_days=7) == pytest.approx(0.41)
    assert formation_return([(ns(34), 80.0), (ns(35), 100.0), (ns(42), 120.0)],
                            cutoff_ns=CUTOFF_NS, lookback_days=7) \
        == pytest.approx(0.20)


# --------------------------------------------------------------------------- #
# 3) Deterministic ties + missing-symbol whole-rebalance skip (item 3)
# --------------------------------------------------------------------------- #
def test_ties_deterministic_symbol_asc_at_1e_12():
    panel = directional_panel()
    panel["EEEUSDT"][-1] = (ns(42), 150.0)  # EEE + FFF now tied at +50%
    first = run_signal(panel)
    for _ in range(3):
        again = run_signal(panel)
        assert again == first
    assert [s for s, _ in first["shorts"]] == ["EEEUSDT", "FFFUSDT"]

    # Sub-tolerance difference counts as a tie -> symbol asc decides even
    # though CCC has the strictly LOWER true return than BBB.
    near = flat_panel()
    near["AAAUSDT"][-1] = (ns(42), 40.0)  # unambiguous bottom leg
    near["CCCUSDT"][-1] = (ns(42), 49.99999999999995)
    near["BBBUSDT"][-1] = (ns(42), 50.00000000000005)
    out = run_signal(near)
    assert out["status"] == "OK"
    assert [s for s, _ in out["longs"]] == ["AAAUSDT", "BBBUSDT"]
    rerun = run_signal(near)
    assert rerun == out


def test_missing_symbol_skips_whole_rebalance():
    panel = directional_panel()
    incomplete = {k: v for k, v in panel.items() if k != "EEEUSDT"}
    out = run_signal(incomplete)
    assert out == {"status": "SKIP_INCOMPLETE",
                   "reason_code": "weekly_panel_incomplete"}
    # Fewer than six declared symbols: all-six eligibility fails closed.
    assert run_signal(panel, symbols=SYMBOLS[:5])["status"] == "SKIP_INCOMPLETE"
    # Symbol with no completed close at/before the cutoff.
    late = directional_panel()
    late["BBBUSDT"] = [(CUTOFF_NS + DAY_NS, 100.0)]
    assert run_signal(late)["reason_code"] == "weekly_panel_incomplete"
    # Non-positive reference price.
    broken = directional_panel()
    broken["BBBUSDT"][35] = (ns(35), 0.0)
    assert run_signal(broken)["status"] == "SKIP_INCOMPLETE"
    # Empty history entirely.
    empty = directional_panel()
    empty["BBBUSDT"] = []
    assert run_signal(empty)["status"] == "SKIP_INCOMPLETE"


# --------------------------------------------------------------------------- #
# 4) Direction legs exact: reversal vs control vs reverse (PLAN 5.2 item 4)
# --------------------------------------------------------------------------- #
def test_reversal_vs_control_directions_exact():
    panel = directional_panel()
    rev = run_signal(panel)
    assert rev["status"] == "OK"
    assert rev["longs"] == [["AAAUSDT", 0.2], ["BBBUSDT", 0.2]]
    assert rev["shorts"] == [["EEEUSDT", -0.2], ["FFFUSDT", -0.2]]

    mom = run_signal(panel, control=True)
    assert mom["longs"] == [["EEEUSDT", 0.2], ["FFFUSDT", 0.2]]
    assert mom["shorts"] == [["AAAUSDT", -0.2], ["BBBUSDT", -0.2]]

    flipped = run_signal(panel, reverse=True)
    assert flipped["longs"] == [["EEEUSDT", 0.2], ["FFFUSDT", 0.2]]
    assert flipped["shorts"] == [["AAAUSDT", -0.2], ["BBBUSDT", -0.2]]

    # End-to-end inversion invariant: plain reversal == control + reverse.
    ctrl_rev = run_signal(panel, control=True, reverse=True)
    assert ctrl_rev == rev


def test_three_day_formation_changes_selection_exactly():
    # Same panel, 3D formation (ref at day 39 == cutoff - 3d): FFF sits flat
    # between its move and the cutoff, so the SHORT leg drops FFF for DDD.
    panel = directional_panel()
    out = run_signal(panel, lookback=3)
    assert out["status"] == "OK"
    assert [s for s, _ in out["longs"]] == ["AAAUSDT", "BBBUSDT"]
    assert [s for s, _ in out["shorts"]] == ["EEEUSDT", "DDDUSDT"]
    assert out["shorts"] == [["EEEUSDT", -0.2], ["DDDUSDT", -0.2]]


# --------------------------------------------------------------------------- #
# 5) Weight normalization
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("gross", [0.80, 0.40, 1.00])
def test_weights_normalized_to_target_gross(gross):
    out = run_signal(directional_panel(), target_gross=gross)
    book = [*out["longs"], *out["shorts"]]
    assert abs(sum(abs(w) for _, w in book) - gross) <= 1e-12
    assert abs(sum(w for _, w in book)) <= 1e-12
    for _sym, w in book:
        assert abs(abs(w) - gross / 4) <= 1e-12


# --------------------------------------------------------------------------- #
# 6) Purge/embargo stamp filter (PLAN 5.2 item 6, unit level)
# --------------------------------------------------------------------------- #
def test_purge_embargo_filter_excludes_first_seven_days():
    stamps = weekly_rebalance_stamps(datetime(2026, 1, 5, tzinfo=UTC),
                                     datetime(2026, 2, 16, tzinfo=UTC))
    # Jan5 fold-start Monday is inside the embargo; Jan12 (== start+7d) is not.
    assert [s.date().isoformat() for s in stamps] == [
        "2026-01-12", "2026-01-19", "2026-01-26", "2026-02-02", "2026-02-09",
    ]
    no_embargo = weekly_rebalance_stamps(datetime(2026, 1, 5, tzinfo=UTC),
                                         datetime(2026, 1, 19, tzinfo=UTC),
                                         embargo_days=0)
    assert [s.date().isoformat() for s in no_embargo] == [
        "2026-01-05", "2026-01-12",
    ]
    midweek = weekly_rebalance_stamps(datetime(2026, 1, 7, tzinfo=UTC),
                                      datetime(2026, 2, 16, tzinfo=UTC))
    assert [s.date().isoformat() for s in midweek] == [
        "2026-01-19", "2026-01-26", "2026-02-02", "2026-02-09",
    ]
    for stamp in (*stamps, *midweek):
        assert stamp.weekday() == 0 and stamp.utctimetuple().tm_hour == 0
    assert len(stamps) == len(set(stamps))


def test_effective_warmup_floor_for_weekly_family(monkeypatch):
    monkeypatch.delenv(pr.SIGNAL_FAMILY_ENV, raising=False)
    assert pr.effective_warmup_days(3) == 10
    monkeypatch.setenv(pr.SIGNAL_FAMILY_ENV, "weekly_reversal")
    assert pr.effective_warmup_days(3) == 14   # floored (>= 14 days)
    assert pr.effective_warmup_days(7) == 14
    assert pr.effective_warmup_days(14) == 21  # lookback-driven above floor


# --------------------------------------------------------------------------- #
# 7) Dispatcher wiring: family routing, control env, diagnostics rows
# --------------------------------------------------------------------------- #
@pytest.fixture()
def family_env(monkeypatch):
    saved = {key: os.environ.get(key)
             for key in (pr.SIGNAL_FAMILY_ENV, pr.CONTROL_MOMENTUM_ENV)}
    yield monkeypatch
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _dispatch_call(panel, **kwargs):
    base = lambda **_k: {"status": "BASE_NEVER_CALLED"}  # noqa: E731
    wrapped = pr._signal_family_dispatch(base, funding_bundles_dir="/unused")
    payload = {
        "daily_closes": panel,
        "signal_cutoff_ns": CUTOFF_NS,
        "lookback_days": kwargs.pop("lookback", 7),
        "reverse": kwargs.pop("reverse", False),
        **kwargs,
    }
    return wrapped(**payload)


def test_dispatcher_routes_weekly_family_without_funding_bundles(family_env,
                                                                 monkeypatch):
    monkeypatch.setenv(pr.SIGNAL_FAMILY_ENV, "weekly_reversal")
    panel = directional_panel()
    out = _dispatch_call(panel)
    assert out["status"] == "OK"
    assert [s for s, _ in out["longs"]] == ["AAAUSDT", "BBBUSDT"]
    assert [s for s, _ in out["shorts"]] == ["EEEUSDT", "FFFUSDT"]

    monkeypatch.setenv(pr.CONTROL_MOMENTUM_ENV, "1")
    control = _dispatch_call(panel)
    assert [s for s, _ in control["longs"]] == ["EEEUSDT", "FFFUSDT"]
    assert [s for s, _ in control["shorts"]] == ["AAAUSDT", "BBBUSDT"]


def test_dispatcher_attaches_derived_diagnostics_rows(family_env, monkeypatch):
    monkeypatch.setenv(pr.SIGNAL_FAMILY_ENV, "weekly_reversal")
    out = _dispatch_call(directional_panel())
    row = out.pop(pr.WEEKLY_DIAGNOSTICS_KEY)
    assert row["derived_diagnostics"] is True
    assert row["rebalance_ts_utc"] == "2026-01-12T00:00:00+00:00"
    assert row["signal_cutoff_ns"] == CUTOFF_NS
    assert row["formation_lookback_days"] == 7
    assert row["skipped_reason"] is None
    assert row["per_symbol"]["AAAUSDT"]["formation_return"] == \
        pytest.approx(-0.60, abs=1e-12)
    assert row["per_symbol"]["AAAUSDT"]["rank"] == 1
    assert row["per_symbol"]["FFFUSDT"]["rank"] == 6
    assert [s for s, _ in row["selected_longs"]] == ["AAAUSDT", "BBBUSDT"]
    assert out == {"status": "OK",
                   "longs": [["AAAUSDT", 0.2], ["BBBUSDT", 0.2]],
                   "shorts": [["EEEUSDT", -0.2], ["FFFUSDT", -0.2]]}

    missing = {k: v for k, v in directional_panel().items()
               if k != "EEEUSDT"}
    skipped = _dispatch_call(missing)
    row = skipped.pop(pr.WEEKLY_DIAGNOSTICS_KEY)
    assert skipped == {"status": "SKIP_INCOMPLETE",
                       "reason_code": "weekly_panel_incomplete"}
    assert row["skipped_reason"] == "weekly_panel_incomplete"
    assert row["selected_longs"] == [] and row["selected_shorts"] == []


def test_cli_flags_resolve_family_and_control_env(family_env, monkeypatch):
    monkeypatch.delenv(pr.SIGNAL_FAMILY_ENV, raising=False)
    monkeypatch.delenv(pr.CONTROL_MOMENTUM_ENV, raising=False)
    argv = ["--signal-family", "weekly_reversal", "--control-momentum"]
    args = pr.build_parser().parse_args(argv)
    assert args.control_momentum is True
    pr.apply_signal_family_flags(args, argv)
    pr._apply_control_momentum_flag(args)
    assert os.environ[pr.SIGNAL_FAMILY_ENV] == "weekly_reversal"
    assert os.environ[pr.CONTROL_MOMENTUM_ENV] == "1"

    # Without the flag an inherited control value is never deleted.
    args = pr.build_parser().parse_args(["--experiment-id", "x"])
    pr._apply_control_momentum_flag(args)
    assert os.environ.get(pr.CONTROL_MOMENTUM_ENV) == "1"


def test_default_momentum_base_survives_other_families():
    seen = {}

    def base(**kwargs):
        seen.update(kwargs)
        return {"status": "OK", "longs": [], "shorts": []}

    wrapped = pr._signal_family_dispatch(base, funding_bundles_dir="/unused")
    out = wrapped(signal_cutoff_ns=CUTOFF_NS, lookback_days=3,
                  reverse=False, daily_closes={})
    assert out["status"] == "OK"
    assert seen["signal_cutoff_ns"] == CUTOFF_NS
