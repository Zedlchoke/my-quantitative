"""Hand-computed golden tests for F6 family-1 (FXFV1-A3-P1), FROZEN spec.

Covers: continuation sign (anchor / NY-open neighbour / sign-flipped causal
control), flatten-bar selection across BOTH US DST transitions (March
spring-forward and November fall-back; exit bar ends 20:00Z in EDT weeks,
21:00Z in EST weeks, always strictly before 17:00 America/New_York),
next-allowed-bar fills (entry bar = the bar AFTER the signal bar; the S3
one-event delay shifts one more bar), exact hand-computed proxy costs,
distinct stable arm digests, double-generation determinism, idempotent
publish, fail-closed NO_TRADE on missing bars, and an exact-arm synthetic
dry run (2 pairs x ~400 H1 hours spanning one DST transition) published to
the gitignored temporary ledger under data_raw/forex_free_v1/dryrun/.

ALL fixtures are SYNTHETIC_TEST_ONLY: no real provider data, no scored PnL,
no bid/ask, no volume.  Label: RESEARCH_CANDIDATE_NOT_LIVE_READY.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from research.assets.forex_free_v1 import family1 as f1
from tests.assets.forex_free_v1 import goldens_family1 as g

UTC = timezone.utc
NY = ZoneInfo("America/New_York")
LDN = ZoneInfo("Europe/London")
ONE_HOUR = timedelta(hours=1)


def z(stamp: str) -> datetime:
    """Parse a 'YYYY-MM-DDTHH:MM:SSZ' golden instant into aware UTC."""
    return g.parse_z(stamp)


def loaded(rows: list[dict]) -> tuple:
    return f1.load_bars(rows)


def rising_day(day: date, first_hour_z: int) -> tuple:
    return loaded(g.anchor_day_bars(day, g.rising_closes(), first_hour_z=first_hour_z))


# --- (a) load_bars validation: fail closed --------------------------------- #
def test_load_bars_valid_and_sorted() -> None:
    bars = rising_day(date(2026, 1, 19), first_hour_z=7)
    assert len(bars) == 14
    assert all(bars[i].ts < bars[i + 1].ts for i in range(13))
    # A bar timestamped T (open) completes at T + 1h.
    assert bars[0].ts == z("2026-01-19T07:00:00Z") and bars[0].end == z("2026-01-19T08:00:00Z")


@pytest.mark.parametrize(
    "mutate,pattern",
    [
        (lambda rows: rows + [dict(rows[0])], "duplicate"),
        (lambda rows: [{**rows[0], "timestamp": "2026-01-19T07:00:00"}] + rows[1:], "naive"),
        (lambda rows: [{**rows[0], "timestamp": "not-a-stamp"}], "malformed"),
        (lambda rows: [{k: v for k, v in row.items() if k != "close"} for row in rows], "missing"),
        (lambda rows: [{**rows[0], "close": float("nan")}], "finite"),
        (lambda rows: [{**rows[0], "close": 0.0}], "positive"),
        (lambda rows: [{**rows[2], "high": 1.0, "low": 2.0}], "inconsistent"),
        (lambda rows: [{**rows[0], "timestamp": "2026-01-19T07:30:00Z"}], "bar boundary"),
        (lambda rows: [], "at least one bar"),
    ],
)
def test_load_bars_fails_closed(mutate, pattern: str) -> None:
    rows = g.anchor_day_bars(date(2026, 1, 19), g.rising_closes(), first_hour_z=7)
    with pytest.raises(f1.Family1Error, match=pattern):
        loaded(mutate(rows))


# --- (b) continuation sign: anchor / control / neighbour -------------------- #
def test_anchor_continuation_sign_rising_falling_flat() -> None:
    day = date(2026, 1, 19)  # GMT + EST golden day
    rising = rising_day(day, first_hour_z=7)
    # c0 = 1.1000 (bar ends 08:00Z), c3 = 1.1030 (3rd London bar, ends 11:00Z):
    # m = 1.1030/1.1000 - 1 = +0.000272727... > 0 -> +1.
    cfg = {"arm_id": "anchor", "signal_date": day}
    assert f1.signal(rising, cfg) == 1
    plan = f1.arm_day_plan(rising, "anchor", day)
    assert plan["c0"] == g.RISING_C0 and plan["c3"] == g.RISING_C3
    assert plan["momentum"] == pytest.approx(g.RISING_M, rel=1e-12)
    assert plan["signal_ts"] == z("2026-01-19T11:00:00Z")  # public at 11:00 London

    falling = loaded(g.anchor_day_bars(day, g.falling_closes(), first_hour_z=7))
    # c0 = 1.1000, c3 = 1.0970: m = 1.0970/1.1000 - 1 < 0 -> -1.
    assert f1.signal(falling, cfg) == -1

    flat = loaded(g.anchor_day_bars(day, g.flat_closes(), first_hour_z=7))
    # c3 == c0 exactly: m = 0 -> no trade.
    assert f1.signal(flat, cfg) == 0


def test_control_flips_sign_with_identical_timing() -> None:
    day = date(2026, 1, 19)
    rising = rising_day(day, first_hour_z=7)
    falling = loaded(g.anchor_day_bars(day, g.falling_closes(), first_hour_z=7))
    anchor_plan = f1.arm_day_plan(rising, "anchor", day)
    control_up = f1.arm_day_plan(rising, "control", day)
    control_down = f1.arm_day_plan(falling, "control", day)
    # Sign-flipped anti-momentum; identical session, signal instant, fills, flatten.
    assert control_up["position"] == -anchor_plan["position"] == -1
    assert control_down["position"] == 1
    assert control_up["signal_ts"] == anchor_plan["signal_ts"] == z("2026-01-19T11:00:00Z")
    assert control_up["schedule"]["entry_fill_instant"] == anchor_plan["schedule"]["entry_fill_instant"]
    assert control_up["schedule"]["flatten_end_utc"] == anchor_plan["schedule"]["flatten_end_utc"]


def test_neighbour_is_own_ny_zone_construction() -> None:
    day = date(2026, 1, 19)  # EST: N = 08:00 New York = 13:00Z
    rising = rising_day(day, first_hour_z=7)
    plan = f1.arm_day_plan(rising, "neighbour", day)
    # Same-signed (+1) but computed from the NY session: c0' closes 13:00Z,
    # 3rd NY bar closes 16:00Z (signal public at 11:00 New York wall clock).
    assert plan["position"] == 1
    assert plan["session_zone"] == "America/New_York"
    assert plan["signal_ts"] == z("2026-01-19T16:00:00Z")
    assert plan["signal_ts"].astimezone(NY).hour == 11
    # Session membership in the named zone: bars at 08/09/10 New York wall.
    for offset in range(3):
        start = z("2026-01-19T13:00:00Z") + offset * ONE_HOUR
        assert start.astimezone(NY).hour == 8 + offset
    # Fill at the next completed bar = 12:00 NY; same flatten rule as the anchor.
    assert plan["schedule"]["entry_fill_instant"] == z("2026-01-19T17:00:00Z")
    assert plan["schedule"]["flatten_end_utc"] == z("2026-01-19T21:00:00Z")

    # The arms are independent constructions: a day whose London morning
    # falls but whose NY morning rises gives anchor -1, neighbour +1.
    closes = [
        1.1000,  # end 08:00Z  c0
        1.0990, 1.0980, 1.0970,  # ends 09..11Z: London falls -> c3 = 1.0970 < c0 -> -1
        1.0950,  # end 12:00Z
        1.0945,  # end 13:00Z  c0' (NY)
        1.0960, 1.0975, 1.0990,  # ends 14..16Z: NY rises -> c3' > c0' -> +1
        1.1000,  # end 17:00Z  (NY entry fill close)
        1.1005, 1.1010, 1.1015,  # ends 18..20Z
        1.1020,  # end 21:00Z  flatten
    ]
    mixed = loaded(g.anchor_day_bars(day, closes, first_hour_z=7))
    assert f1.signal(mixed, {"arm_id": "anchor", "signal_date": day}) == -1
    assert f1.signal(mixed, {"arm_id": "neighbour", "signal_date": day}) == 1
    assert f1.signal(mixed, {"arm_id": "control", "signal_date": day}) == 1


# --- (c) DST flatten-bar selection across BOTH US transitions --------------- #
@pytest.mark.parametrize(
    "day_iso,first_hour_z",
    [
        ("2026-03-06", 7),  # Fri, GMT + EST  (before US spring-forward 2026-03-08)
        ("2026-03-09", 6),  # Mon, GMT + EDT  (after; London/NY DST mismatch week)
        ("2026-06-15", 6),  # Mon, BST + EDT  (pure summer control)
        ("2026-10-30", 6),  # Fri, GMT + EDT  (before US fall-back 2026-11-01; UK already GMT)
        ("2026-11-02", 7),  # Mon, GMT + EST  (after)
    ],
)
def test_flatten_bar_across_march_and_november_dst(day_iso: str, first_hour_z: int) -> None:
    golden = g.GOLDEN_DAYS[day_iso]
    y, m, d = (int(p) for p in day_iso.split("-"))
    day = date(y, m, d)
    bars = rising_day(day, first_hour_z=first_hour_z)
    schedule = f1.build_schedule(bars, z(f"{day_iso}T{golden['signal_ts_z']}"))

    flatten_end = schedule["flatten_end_utc"]
    rollover = schedule["rollover_utc"]
    # Exit bar ends 20:00Z in EDT weeks, 21:00Z in EST weeks -- the golden.
    assert flatten_end == z(f"{day_iso}T{golden['flatten_end_z']}")
    # ...and strictly before the 17:00 America/New_York rollover.
    assert flatten_end < rollover == z(f"{day_iso}T{golden['rollover_z']}")
    assert rollover - flatten_end == ONE_HOUR
    # The flatten bar always ends at 16:00 New York wall clock (EST and EDT alike).
    assert (flatten_end.astimezone(NY).hour, flatten_end.astimezone(NY).minute) == (16, 0)
    # Independent zoneinfo truth for the session clocks (never fixed offsets).
    assert datetime(y, m, d, 17, tzinfo=NY).astimezone(UTC) == rollover
    assert datetime(y, m, d, 8, tzinfo=LDN).astimezone(UTC) == z(f"{day_iso}T{golden['london_open_z']}")
    # Entry bar is the bar AFTER the signal bar (never the signal bar itself).
    assert schedule["signal_bar_start"] == schedule["signal_ts"] - ONE_HOUR
    assert schedule["entry_bar_start"] == schedule["signal_ts"]
    assert schedule["entry_fill_instant"] == z(f"{day_iso}T{golden['entry_fill_z']}")
    # No overnight: entry and flatten sit on the signal's own NY trade day.
    assert schedule["entry_fill_instant"].astimezone(NY).date() == day
    assert flatten_end.astimezone(NY).date() == day


def test_march_and_november_flatten_goldens_differ_by_one_hour() -> None:
    # Hand-computed: EST weeks flatten at 21:00Z (< 22:00Z rollover),
    # EDT weeks at 20:00Z (< 21:00Z rollover).
    assert g.GOLDEN_DAYS["2026-03-06"]["flatten_end_z"] == "21:00Z"
    assert g.GOLDEN_DAYS["2026-03-09"]["flatten_end_z"] == "20:00Z"
    assert g.GOLDEN_DAYS["2026-10-30"]["flatten_end_z"] == "20:00Z"
    assert g.GOLDEN_DAYS["2026-11-02"]["flatten_end_z"] == "21:00Z"
    assert z("2026-03-06T21:00:00Z") < z("2026-03-06T22:00:00Z")
    assert z("2026-03-09T20:00:00Z") < z("2026-03-09T21:00:00Z")


# --- (d) next-allowed-bar fill and the S3 one-event delay ------------------- #
def test_next_allowed_bar_fill_and_s3_delay() -> None:
    day = date(2026, 1, 19)
    bars = rising_day(day, first_hour_z=7)
    # S1: entry bar = bar AFTER the signal bar; fill at its close (12:00Z).
    s1 = f1.run_arm(bars, "anchor", 1.0)
    entry_s1 = s1["fills"][0]
    assert entry_s1["role"] == "ENTRY" and entry_s1["instant"] == z("2026-01-19T12:00:00Z")
    assert entry_s1["price"] == g.RISING_ENTRY_S1 == 1.1040  # close of bar [11:00Z, 12:00Z)
    # S3 (tier 2.0): entry fill shifted one additional completed bar later.
    s3 = f1.run_arm(bars, "anchor", 2.0)
    entry_s3 = s3["fills"][0]
    assert entry_s3["instant"] == z("2026-01-19T13:00:00Z")
    assert entry_s3["price"] == g.RISING_ENTRY_S3 == 1.1050  # close of bar [12:00Z, 13:00Z)
    # Flatten rule unchanged by the delay: 21:00Z EST flatten bar in both cells.
    assert s1["fills"][1]["instant"] == s3["fills"][1]["instant"] == z("2026-01-19T21:00:00Z")
    assert s3["extra_delay_events"] == 1 and s1["extra_delay_events"] == 0
    # Delay arithmetic: fill instant - signal_ts == 1h (S1) / 2h (S3).
    signal_ts = z("2026-01-19T11:00:00Z")
    assert entry_s1["instant"] - signal_ts == ONE_HOUR
    assert entry_s3["instant"] - signal_ts == 2 * ONE_HOUR
    with pytest.raises(f1.Family1Error, match="extra_delay_events"):
        f1.build_schedule(bars, signal_ts, extra_delay_events=2)


# --- (e) exact hand-computed costs: 3-trade scenario at each tier ----------- #
def test_costs_exact_bps_three_fills_each_tier() -> None:
    bars = loaded(g.multi_day_rising_bars(g.COST_SCENARIO_DAYS))  # Jan 20..22, 3 weekdays
    for tier, gold in g.COST_GOLDENS.items():
        run = f1.run_arm(bars, "anchor", tier)
        # Hand arithmetic: 3 trades x 2 fills; per-side = 1.5 x tier bps.
        assert run["costs_bps"]["per_side_bps"] == gold["per_side_bps"]  # 1.5 / 2.25 / 3.0
        assert run["costs_bps"]["round_trip_bps"] == gold["round_trip_bps"]  # 3.0 / 4.5 / 6.0
        assert run["costs_bps"]["total_bps"] == gold["total_bps"]  # 9.0 / 13.5 / 18.0
        assert run["costs_bps"]["fills"] == 6
        # First THREE fills (entry, flatten, entry) book 3 x 1.5 x tier bps:
        # 4.5 / 6.75 / 9.0 bps.
        assert sum(fill["cost_bps"] for fill in run["fills"][:3]) == pytest.approx(gold["three_fill_bps"])
        # Per-trade cashflow cost = round trip / 1e4: 0.0003 / 0.00045 / 0.0006.
        assert all(cf["cost_frac"] == pytest.approx(gold["cost_frac_per_trade"]) for cf in run["cashflows"])
        assert len(run["cashflows"]) == 3
        # Entry/flatten sides follow the position (+1 -> BUY then SELL).
        assert run["fills"][0]["side"] == "BUY" and run["fills"][1]["side"] == "SELL"


# --- (f) arm identity digests ------------------------------------------------ #
def test_arm_identity_three_distinct_and_stable() -> None:
    configs = f1.frozen_arm_configs()
    digests = {arm: f1.arm_identity(arm, configs[arm]) for arm in f1.ARM_IDS}
    assert len(set(digests.values())) == 3  # anchor / neighbour / control distinct
    for arm in f1.ARM_IDS:  # stable across calls
        assert f1.arm_identity(arm, configs[arm]) == digests[arm]
        assert f1.arm_identity(arm, dict(configs[arm])) == digests[arm]
    tampered = dict(configs["anchor"])
    tampered["position_sign"] = -1
    assert f1.arm_identity("anchor", tampered) != digests["anchor"]


# --- (g) double generation determinism --------------------------------------- #
def test_double_generation_identical_canonical_json_sha256() -> None:
    bars = rising_day(date(2026, 1, 19), first_hour_z=7)
    first = f1.run_arm(bars, "anchor", 1.5, pair="EUR/USD")
    second = f1.run_arm(bars, "anchor", 1.5, pair="EUR/USD")
    assert first["canonical_json"] == second["canonical_json"]
    assert first["run_digest"] == second["run_digest"]
    assert first["run_digest"] == f1.sha256_hex(first["canonical_json"])
    assert len(first["run_digest"]) == 64


# --- (h) idempotent publish --------------------------------------------------- #
def test_publish_idempotent_on_identical_digest(tmp_path: Path) -> None:
    ledger = tmp_path / "dryrun" / "ledger.jsonl"
    d1 = "a" * 64
    d2 = "b" * 64
    first = f1.publish(ledger, d1)
    assert first["status"] == "APPENDED" and first["total_rows"] == 1
    text_after_first = ledger.read_text(encoding="utf-8")
    # Replay of the identical digest is a strict NO-OP.
    replay = f1.publish(ledger, d1)
    assert replay["status"] == "NOOP" and replay["total_rows"] == 1 and replay["appended"] is False
    assert ledger.read_text(encoding="utf-8") == text_after_first
    # A different digest appends exactly one row.
    second = f1.publish(ledger, d2)
    assert second["status"] == "APPENDED" and second["total_rows"] == 2
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 2
    with pytest.raises(f1.Family1Error, match="64-char"):
        f1.publish(ledger, "xyz")
    with pytest.raises(f1.Family1Error, match="lacks a run_digest"):
        bad = tmp_path / "bad.jsonl"
        bad.write_text('{"schema": "x"}\n', encoding="utf-8")
        f1.publish(bad, d1)


# --- (i) missing bars -> NO_TRADE fail closed -------------------------------- #
@pytest.mark.parametrize(
    "drop_start_z,role",
    [
        ("2026-01-19T07:00:00Z", "c0"),      # c0 bar (pre-open close)
        ("2026-01-19T10:00:00Z", "session"),  # 3rd London session bar = signal bar
        ("2026-01-19T11:00:00Z", "entry"),   # entry fill bar
        ("2026-01-19T20:00:00Z", "flatten"),  # flatten bar (ends 21:00Z EST)
    ],
)
def test_missing_bar_no_trade_fail_closed(drop_start_z: str, role: str) -> None:
    day = date(2026, 1, 19)
    rows = [r for r in g.anchor_day_bars(day, g.rising_closes(), first_hour_z=7) if r["timestamp"] != drop_start_z]
    bars = loaded(rows)
    # c0 and the 3rd session bar are signal inputs: signal() fails closed
    # directly.  The entry/flatten bars are schedule requirements, so
    # signal() still completes; the schedule layer fails closed instead.
    if role in {"c0", "session"}:
        with pytest.raises(f1.SignalUnavailable, match=role):
            f1.signal(bars, {"arm_id": "anchor", "signal_date": day})
    else:
        assert f1.signal(bars, {"arm_id": "anchor", "signal_date": day}) == 1
    # Either way, run_arm records a counted NO_TRADE with an explicit reason.
    run = f1.run_arm(bars, "anchor", 1.0)
    assert run["feasibility"]["no_trade_by_reason"] == {"MISSING_BAR": 1}
    decision = run["decisions"][0]
    assert decision["date"] == "2026-01-19"
    assert decision["decision"] == "NO_TRADE" and decision["position"] == 0
    assert decision["reason"] == "MISSING_BAR" and role in decision["detail"]
    assert len(run["decisions"]) == 1
    assert run["fills"] == [] and run["cashflows"] == []
    assert run["costs_bps"]["total_bps"] == 0.0 and run["turnover"]["units"] == 0


def test_weekend_and_invalid_arguments_fail_closed() -> None:
    bars = rising_day(date(2026, 1, 19), first_hour_z=7)
    with pytest.raises(f1.Family1Error, match="weekend"):  # 2026-01-18 is a Sunday
        f1.signal(bars, {"arm_id": "anchor", "signal_date": "2026-01-18"})
    with pytest.raises(f1.Family1Error, match="arm_id"):
        f1.run_arm(bars, "bogus", 1.0)
    with pytest.raises(f1.Family1Error, match="cost_tier"):
        f1.run_arm(bars, "anchor", 1.75)


def test_compute_metrics_finite_placeholder() -> None:
    book = [
        {"net_return_frac": 0.001, "cost_frac": 0.0003},
        {"net_return_frac": -0.0005, "cost_frac": 0.0003},
        {"net_return_frac": 0.0002, "cost_frac": 0.0003},
    ]
    metrics = f1.compute_metrics(book)
    assert metrics["n_trades"] == 3
    assert metrics["win_rate"] == pytest.approx(2.0 / 3.0)  # 2 wins of 3
    assert metrics["mean_net_return_frac"] == pytest.approx((0.001 - 0.0005 + 0.0002) / 3.0)
    empty = f1.compute_metrics([])
    assert empty == {
        "schema": "forex_free_v1_family1_metrics_v1",
        "family_id": f1.FAMILY_ID,
        "placeholder": True,
        "n_trades": 0,
        "win_rate": 0.0,
        "mean_net_return_frac": 0.0,
    }
    with pytest.raises(f1.Family1Error, match="finite"):
        f1.compute_metrics([{"net_return_frac": float("inf")}])


# --- (j) exact-arm synthetic dry run: 2 pairs x ~400h, one DST transition ---- #
def test_exact_arm_dry_run_two_pairs_dst_transition(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    assert (repo_root / "research" / "assets" / "forex_free_v1" / "family1.py").exists()
    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")
    assert "data_raw/" in gitignore  # the dry-run ledger can never be committed

    ledger = repo_root / "data_raw" / "forex_free_v1" / "dryrun" / "f6_family1_dst_fixture_ledger.jsonl"
    if ledger.exists():  # the test owns its scratch file
        ledger.unlink()

    printed: list[str] = []
    digests: dict[tuple[str, str], str] = {}
    for pair, base in (("EUR/USD", 1.08), ("GBP/USD", 1.26)):
        bars = f1.load_bars(g.dryrun_pair_bars(base))
        assert len(bars) == g.DRYRUN_N_BARS == 408  # ~400 hours, 17 weekdays
        assert bars[0].ts == z("2026-03-02T00:00:00Z")
        assert bars[-1].end == z("2026-03-25T00:00:00Z")  # spans US spring-forward 2026-03-08
        for arm in f1.ARM_IDS:  # all 3 arms run: anchor, neighbour, control
            run = f1.run_arm(bars, arm, 1.0, pair=pair)  # base cost cell S1
            assert run["label"] == "RESEARCH_CANDIDATE_NOT_LIVE_READY"
            assert run["schedule_only"] is True and run["scoring_authorized"] is False
            assert run["run_digest"] == f1.sha256_hex(run["canonical_json"])
            # Feasibility goldens (hand arithmetic; the intraday-monotone
            # path makes every one of the 17 weekdays trade; span = 23 days):
            #   decisions_per_year = 17 * 365.25 / 23 = 269.96739130434784
            #   turnover units/yr  = 34 * 365.25 / 23 = 539.9347826086957
            #   cost drag (S1)     = 269.967... * 3.0 = 809.9021739130435 bps/yr
            assert run["feasibility"]["trade_days"] == g.DRYRUN_N_WEEKDAYS == 17
            assert run["feasibility"]["no_trade_days"] == 0
            assert run["decisions_per_year"] == pytest.approx(g.DRYRUN_DECISIONS_PER_YEAR, rel=1e-9)
            assert run["turnover"]["units"] == 34
            assert run["turnover"]["units_per_year"] == pytest.approx(g.DRYRUN_TURNOVER_UNITS_PER_YEAR, rel=1e-9)
            assert run["feasibility"]["cost_drag_bps_per_year"] == pytest.approx(
                g.DRYRUN_COST_DRAG_BPS_PER_YEAR_S1, rel=1e-9
            )
            assert len(run["fills"]) == 34 and len(run["cashflows"]) == 17
            # DST check inside the fixture: the EST week (Fri 2026-03-06)
            # flattens at 21:00Z, the mismatch EDT week (Mon 2026-03-09,
            # London GMT + New York EDT) at 20:00Z -- both strictly before
            # 17:00 New York.
            by_date = {dec["date"]: dec for dec in run["decisions"]}
            assert by_date["2026-03-06"]["flatten_end_utc"] == z("2026-03-06T21:00:00Z")
            assert by_date["2026-03-06"]["flatten_end_utc"] < z("2026-03-06T22:00:00Z")
            assert by_date["2026-03-09"]["flatten_end_utc"] == z("2026-03-09T20:00:00Z")
            assert by_date["2026-03-09"]["flatten_end_utc"] < z("2026-03-09T21:00:00Z")
            digests[(pair, arm)] = run["run_digest"]
            outcome = f1.publish(ledger, run["run_digest"])
            assert outcome["status"] == "APPENDED"
            printed.append(
                f"[FXFV1-A3-P1 dry-run] {pair:8s} {arm:9s} trades=17 "
                f"decisions/yr={run['decisions_per_year']:.4f} "
                f"turnover(units/yr)={run['turnover']['units_per_year']:.4f} "
                f"cost_drag={run['feasibility']['cost_drag_bps_per_year']:.4f} bps/yr "
                f"digest={run['run_digest'][:16]}..."
            )

    for line in printed:  # feasibility values recorded in the test output
        print(line)

    # Ledger: 6 rows, all digests distinct, under the gitignored scratch dir.
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 6 and len({row["run_digest"] for row in rows}) == 6
    assert {row["run_digest"] for row in rows} == set(digests.values())
    assert "data_raw" in str(ledger)

    # Replay every digest: a strict NO-OP, zero rows added.
    for key in sorted(digests):
        assert f1.publish(ledger, digests[key])["status"] == "NOOP"
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 6
    print(f"[FXFV1-A3-P1 dry-run] replay of all 6 digests added 0 rows; ledger={ledger}")
