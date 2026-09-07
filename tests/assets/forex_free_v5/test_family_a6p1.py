#!/usr/bin/env python
"""FOREX-FREE-V5 family FXFV5-A6-P1 tests (I1 implementation lane).

Hand-computed SYNTHETIC fixtures only (no scored PnL anywhere, no network,
no real-data execution beyond read-only authority parsing): the frozen law's
feature golden, the one-event/one-bar lag and one-session window semantics,
the no-lookahead mutation, DST 16:00-NY stamps, fold force-flat refusal,
costs-exactly-once, zero-position refusal, control-schedule identifiability,
sham-calendar validity, deterministic replay and fail-closed clock rows.

Every expected number is written next to its hand arithmetic (the inherited
tests/assets/forex_free_v3/test_accounting.py convention).

FIXTURE GEOMETRY (the main golden): 16:00 America/New_York bars (EST ->
21:00Z in January) over consecutive NY weekdays from 2024-01-02 (Tue); a GB
evidenced clock at 2024-01-18T22:00:00Z gives
    F = Thu 2024-01-18 21:00Z (last completed bar strictly before a)
    D = Wed 2024-01-17 21:00Z (the previous valid session's bar)
    X = Fri 2024-01-19 21:00Z (first completed bar strictly after a)
so the window [F, X] spans the release instant by construction
(2024-01-18T21:00Z < 2024-01-18T22:00Z < 2024-01-19T21:00Z) and holds no
post-release session.

THE FEATURE GOLDEN: closes 1.26 * 1.001**k (k = 0..10) strictly before D
give ten identical daily log returns ln(1.001), so x = 10*ln(1.001) > 0 and
direction = -1 (SHORT); mirrored closes 1.26 * 0.999**k give
x = 10*ln(0.999) < 0 -> direction = +1 (LONG); equal closes give x = 0.0
EXACTLY -> NO_TRADE (fail-closed).

THE COST GOLDEN (inherited frozen kernel): one round trip at notional
10000 USD-units pays 1.5 bps per side, EXACTLY ONCE per fill:
    per side 10000 * 1.5 / 10000 = 1.50 USD; round trip 3.00 USD.

The clocks fixtures are FULL 246-row p3-shaped authorities (the frozen
per-economy counts GB 88 / CA 105 / AU 23 / NZ 30 are part of the fail-closed
contract); deterministic filler rows are kept clear of every engineered
window so only the story clocks trade inside the synthetic snapshot.
"""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from research.assets.forex_free_v3 import accounting as A          # noqa: E402
from research.assets.forex_free_v3 import scored_runner as R       # noqa: E402
from research.assets.forex_free_v5 import family_a6p1 as F         # noqa: E402

UTC = timezone.utc
FAMILY_ID = "FXFV5-A6-P1"

# ------------------------------------------------------------------ #
# fixture builders (synthetic only)                                   #
# ------------------------------------------------------------------ #
def ny_1600(day: date) -> datetime:
    """The 16:00 America/New_York instant of `day` as UTC (DST-aware)."""
    return F.ny_decision_stamp(day)


def weekday_dates(start: date, n: int) -> list:
    out, cur = [], start
    while len(out) < n:
        if cur.weekday() < 5:
            out.append(cur)
        cur += timedelta(days=1)
    return out


def _write_pair_bars(tmp, pair, closes, opens=None):
    """One 16:00-NY bar per NY weekday; open defaults to the close
    (`opens` overrides per-index, for fill-at-the-OPEN goldens)."""
    tag = pair.replace("/", "")
    rows = []
    for k, (day, close) in enumerate(closes):
        o = (opens or {}).get(k, close)
        rows.append({"datetime": ny_1600(day).strftime("%Y-%m-%d %H:%M:%S"),
                     "open": f"{o:.12f}",
                     "high": f"{max(o, close) * 1.00001:.12f}",
                     "low": f"{min(o, close) * 0.99999:.12f}",
                     "close": f"{close:.12f}"})
    path = os.path.join(tmp, f"{tag}_1h_2024-01-01_a.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"meta": {"symbol": pair, "interval": "1h"},
                   "values": rows, "status": "ok"}, handle)
    return path


STORY_A = datetime(2024, 1, 18, 22, 0, tzinfo=UTC)  # the golden release instant


def _story_closes(n=40, base=1.26, step=1.001):
    """base * step**k over `n` consecutive NY weekdays from 2024-01-02."""
    days = weekday_dates(date(2024, 1, 2), n)
    return [(day, base * step ** k) for k, day in enumerate(days)]


def _filler_dates(count, avoid):
    """Deterministic filler clock dates spread across the S0 window (three
    candidates per month: the 5th/15th/25th), kept clear of every story
    instant and its +7d sham shift by > 17 days."""
    out = []
    month_k = 0
    base = date(2018, 6, 1)
    while len(out) < count:
        y = base.year + (base.month - 1 + month_k) // 12
        m = (base.month - 1 + month_k) % 12 + 1
        for dd in (5, 15, 25):
            if len(out) >= count:
                break
            day = date(y, m, dd)
            if day > date(2025, 7, 24):
                raise RuntimeError("fixture filler generation ran out of S0")
            t = datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=UTC)
            if any(abs((t - a).total_seconds()) < 17 * 86400
                   or abs((t - (a + timedelta(days=7))).total_seconds())
                   < 17 * 86400
                   for a in avoid):
                continue
            out.append(day)
        month_k += 1
    return out


def _clock_row(economy, a):
    return {
        "decision_date": a.astimezone(UTC).date().isoformat(),
        "available_time_utc": a.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "precision": "DAY (fixture)",
        "reference_period": f"fixture-{a.date().isoformat()}",
        "archive_sha256": "ab" * 32,
        "economy": economy,
    }


def write_clocks_file(path, story):
    """A full 246-row p3-shaped conditioning-clocks fixture: the engineered
    `story` rows ((economy, available datetime), DAY-precision stamps) plus
    deterministic fillers to the frozen per-economy counts (GB 88 / CA 105 /
    AU 23 / NZ 30)."""
    avoid = [a for _, a in story]
    story_by_economy = {}
    for economy, a in story:
        story_by_economy.setdefault(economy, []).append(a)
    rows = []
    for economy in F.ECONOMY_ORDER:
        need = F.EXPECTED_CLOCK_COUNTS[economy] \
            - len(story_by_economy.get(economy, []))
        for day in _filler_dates(need, avoid):
            rows.append(_clock_row(economy, datetime(
                day.year, day.month, day.day, 23, 59, 59, tzinfo=UTC)))
        for a in sorted(story_by_economy.get(economy, [])):
            rows.append(_clock_row(economy, a))
    payload = {
        "schema": "forex_free_v5_conditioning_clocks_v1",
        "S0_window": {"start": "2018-04-04", "end": "2025-07-24"},
        "per_economy_in_S0": dict(F.EXPECTED_CLOCK_COUNTS),
        "total_clocks_published": len(rows),
        "clocks": rows,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    assert len(rows) == F.TOTAL_CLOCKS_PUBLISHED
    return path


def write_ledger(path, rates=None):
    """A tiny pinned-ledger fixture: one evidenced RATE_CHANGE row per
    area, effective 2018-01-01, available 2018-01-01T23:59:59Z -- so every
    day-start accrual in the fixture windows reads a CONSTANT differential
    (hand-computable financing)."""
    rates = rates or {"US": 1.0, "GB": 0.75, "CA": 1.5, "AU": 2.0, "NZ": 2.0}
    with open(path, "w", encoding="utf-8") as handle:
        for area, value in sorted(rates.items()):
            handle.write(json.dumps({
                "row_type": "RATE_CHANGE",
                "schema": "forex_free_v3r_announcement_ledger_row_v1",
                "area": area,
                "effective_date": "2018-01-01",
                "effective_time_utc": "2018-01-01T00:00:00Z",
                "old_value": 0.25, "new_value": value,
                "first_readable_decision_utc": "2018-01-02T20:00:00Z",
                "announcement": {
                    "operative_available_time_utc": "2018-01-01T23:59:59Z",
                    "status": "EVIDENCED", "archive_sha256": "cd" * 32},
            }) + "\n")
    return path


def make_fixture(tmp, story=None, closes=None, opens=None, pairs=None,
                 rates=None):
    """The full synthetic data_paths: 16:00-NY bars for the four evidenced
    pairs, a 246-row conditioning-clocks file and the tiny pinned ledger.
    `closes` is a [(ny_day, close)] list shared by all pairs unless `pairs`
    gives {pair: closes}."""
    story = story if story is not None else [("GB", STORY_A)]
    closes = closes if closes is not None else _story_closes()
    pairs = pairs or {p: closes for p in F.ECONOMY_PAIR.values()}
    for pair, pair_closes in pairs.items():
        _write_pair_bars(tmp, pair, pair_closes, opens=opens)
    clocks_path = write_clocks_file(os.path.join(tmp, "clocks.json"), story)
    ledger_path = write_ledger(os.path.join(tmp, "ledger.jsonl"),
                               rates=rates)
    return {
        "price_h1_dir": str(tmp),
        "conditioning_clocks": clocks_path,
        "announcement_ledger": ledger_path,
    }


def schedule_of(decisions):
    """{(pair, decision_ts, entry_ts, exit_ts)} -- the arm's schedule."""
    return {(d["pair"], d["decision_ts"], d["entry_bar_ts"], d["exit_bar_ts"])
            for d in decisions}


def _three_gb_clocks():
    """Three GB story clocks a month apart, all inside a 70-bar snapshot
    (Jan 2 .. Apr 19), so the anchor's last clock also trades."""
    return [("GB", STORY_A),
            ("GB", datetime(2024, 2, 15, 22, 0, tzinfo=UTC)),
            ("GB", datetime(2024, 3, 15, 22, 0, tzinfo=UTC))]


GOLDEN_DECISION_TS = "2024-01-17T21:00:00+00:00"
GOLDEN_ENTRY_TS = "2024-01-18T21:00:00+00:00"
GOLDEN_EXIT_TS = "2024-01-19T21:00:00+00:00"


def _golden_decision(out):
    """The golden GB decision of an anchor run on the default fixture."""
    matches = [d for d in out["decisions"] if d["pair"] == "GBP/USD"
               and d["decision_ts"] == GOLDEN_DECISION_TS]
    assert len(matches) == 1
    return matches[0]


# ------------------------------------------------------------------ #
# 1. feature golden: trailing 10-NY-day return sum + -sign law        #
# ------------------------------------------------------------------ #
def test_trailing_return_sum_golden():
    """x = 10 * ln(1.001) over 1.26*1.001**k (k=0..10); -sign -> SHORT."""
    closes = [1.26 * 1.001 ** k for k in range(11)]   # 11 closes, 10 returns
    x = F.trailing_return_sum(closes)
    assert x == pytest.approx(10 * math.log(1.001), rel=1e-12)
    assert x > 0
    assert F.direction_of(x) == -1


def test_trailing_return_sum_golden_inverted():
    """Mirrored closes: x = 10 * ln(0.999) < 0 -> direction +1 (LONG)."""
    closes = [1.26 * 0.999 ** k for k in range(11)]
    x = F.trailing_return_sum(closes)
    assert x == pytest.approx(10 * math.log(0.999), rel=1e-12)
    assert F.direction_of(x) == 1


def test_trailing_return_sum_exact_zero_is_no_trade():
    """Equal closes -> x == 0.0 EXACTLY -> direction 0 (NO_TRADE,
    fail-closed; never a sign guess)."""
    assert F.trailing_return_sum([1.26] * 11) == 0.0
    assert F.direction_of(0.0) == 0


def test_trailing_return_sum_warmup_fail_closed():
    """10 closes (9 returns) violate the 11-close warmup: DataBlocked."""
    with pytest.raises(F.DataBlocked, match="warmup violated"):
        F.trailing_return_sum([1.26 * 1.001 ** k for k in range(10)])


def test_feature_golden_via_full_schedule():
    """The golden window end-to-end: closes strictly before D are
    1.26*1.001**k (k=0..10) -> x = 10*ln(1.001) > 0 -> one SHORT decision
    entering at F's open and exiting at X's open."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = make_fixture(td)
        out = F.run_arm("anchor", data_paths)
        d = _golden_decision(out)
        assert d["side"] == -1
        assert d["decision_ts"] == GOLDEN_DECISION_TS            # D
        assert d["entry_bar_ts"] == GOLDEN_ENTRY_TS              # F
        assert d["exit_bar_ts"] == GOLDEN_EXIT_TS                # X
        # one NY-day in January (EST): 21:00Z stamps exactly one session apart
        assert (datetime.fromisoformat(d["entry_bar_ts"])
                - datetime.fromisoformat(d["decision_ts"])) == timedelta(days=1)


# ------------------------------------------------------------------ #
# 2. one-event / one-bar lag + one-session window semantics           #
# ------------------------------------------------------------------ #
def test_one_event_lag_and_window_span_golden():
    """F is exactly the next session after D (never same-bar), a lies
    STRICTLY inside (entry, exit), and the exit is the FIRST bar after a
    (no post-release session held)."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = make_fixture(td)
        out = F.run_arm("anchor", data_paths)
        d = _golden_decision(out)
        dec = datetime.fromisoformat(d["decision_ts"])
        ent = datetime.fromisoformat(d["entry_bar_ts"])
        ext = datetime.fromisoformat(d["exit_bar_ts"])
        assert dec < ent < STORY_A < ext                    # F < a < X
        assert ent - dec == timedelta(days=1)               # one session
        # fills at the OPEN of the fill bars (bar k's close = 1.26*1.001**k)
        assert d["entry_price"] == pytest.approx(1.26 * 1.001 ** 12, rel=1e-12)
        assert d["exit_price"] == pytest.approx(1.26 * 1.001 ** 13, rel=1e-12)


def test_fill_at_open_not_close():
    """The fill price is the fill bar's OPEN even when the open differs
    from the close (entry bar open 1.30)."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = make_fixture(td, closes=_story_closes(), opens={12: 1.30})
        out = F.run_arm("anchor", data_paths)
        d = _golden_decision(out)
        assert d["entry_price"] == 1.30
        assert d["exit_price"] == pytest.approx(1.26 * 1.001 ** 13)


def test_kernel_accepts_the_golden_decision_stream():
    """The emitted decisions pass the frozen kernel validator (16:00-NY
    stamps, one-event lag, 4-day cap, no fold crossing) unchanged."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = make_fixture(td)
        out = F.run_arm("anchor", data_paths)
        trades, adjustments, formula = R.validate_decisions(
            out["decisions"], out["financing_events"])
        assert len(trades) == len(out["decisions"]) > 0
        assert set(adjustments) == {d["decision_id"] for d in trades}
        assert formula == F.FINANCING_FORMULA_ID


def test_exit_is_first_bar_after_availability():
    """The window holds NO post-release session: the exit is exactly the
    first completed 16:00-NY bar strictly after a -- a bar one session
    later must NOT be the exit."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = make_fixture(td)
        out = F.run_arm("anchor", data_paths)
        d = _golden_decision(out)
        assert d["exit_bar_ts"] == GOLDEN_EXIT_TS
        later = ny_1600(date(2024, 1, 22)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        assert d["exit_bar_ts"] != later


# ------------------------------------------------------------------ #
# 3. no-lookahead mutation: shifting available_time changes/mutes     #
# ------------------------------------------------------------------ #
def test_no_lookahead_mutation_shift_changes_decisions():
    """Moving the evidenced instant forward moves D/F/X (the decision
    recomputes at the LATER availability-lagged bar)."""
    with tempfile.TemporaryDirectory() as td:
        base = schedule_of(F.run_arm(
            "anchor", make_fixture(td))["decisions"])
    with tempfile.TemporaryDirectory() as td2:
        moved = schedule_of(F.run_arm(
            "anchor",
            make_fixture(td2, story=[("GB", STORY_A + timedelta(days=30))]))
            ["decisions"])
    assert moved != base
    # a+30d = Sat 2024-02-17 22:00Z -> F = Fri Feb 16, D = Thu Feb 15
    assert any(ts == "2024-02-15T21:00:00+00:00"
               for (_, ts, _, _) in moved)


def test_no_lookahead_mutation_beyond_data_mutes():
    """Moving the evidenced instant beyond the snapshot voids the clock
    (x_missing_void): NO decision, never an inferred one."""
    with tempfile.TemporaryDirectory() as td:
        base = schedule_of(F.run_arm(
            "anchor", make_fixture(td))["decisions"])
    with tempfile.TemporaryDirectory() as td2:
        data_paths2 = make_fixture(td2, story=[
            ("GB", STORY_A + timedelta(days=300))])
        out = F.run_arm("anchor", data_paths2)
        assert out["meta"]["schedule_totals"]["GBP/USD"]["x_missing_void"] >= 1
        assert schedule_of(out["decisions"]) != base


def test_decision_is_availability_lagged():
    """Every golden decision instant is strictly BEFORE its conditioning
    print's available_time (the decision never sees the release it
    front-runs; no feature reads data at/after the computation instant)."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = make_fixture(td)
        out = F.run_arm("anchor", data_paths)
        d = _golden_decision(out)
        assert datetime.fromisoformat(d["decision_ts"]) < STORY_A
        assert datetime.fromisoformat(d["entry_bar_ts"]) < STORY_A


def test_warmup_gap_fails_closed():
    """A clock whose decision bar sits inside the warmup prefix produces NO
    decision (warmup_void), never an inferred one (the AU documented-gap
    discipline)."""
    with tempfile.TemporaryDirectory() as td:
        # a between the 5th and 6th bars: D = idx 4 -> warmup impossible
        early = datetime(2024, 1, 9, 22, 0, tzinfo=UTC)
        data_paths = make_fixture(td, story=[("GB", early)])
        out = F.run_arm("anchor", data_paths)
        gb = out["meta"]["schedule_totals"]["GBP/USD"]
        assert gb["warmup_void"] >= 1
        assert not any(d["pair"] == "GBP/USD"
                       and d["decision_ts"].startswith("2024-01")
                       for d in out["decisions"])


# ------------------------------------------------------------------ #
# 4. DST 16:00-NY boundary                                            #
# ------------------------------------------------------------------ #
def test_ny_stamp_dst_golden():
    """16:00 New York is 21:00Z in EST and 20:00Z in EDT (zoneinfo; never
    a fixed offset)."""
    assert ny_1600(date(2024, 1, 16)).strftime("%Y-%m-%dT%H:%M:%S") \
        == "2024-01-16T21:00:00"
    assert ny_1600(date(2024, 7, 16)).strftime("%Y-%m-%dT%H:%M:%S") \
        == "2024-07-16T20:00:00"


def test_dst_transition_window_golden():
    """A clock just after the Fri 2024-11-01 bar (EDT, 20:00Z) exits at the
    Mon 2024-11-04 bar (EST, 21:00Z) -- the window crosses the DST switch
    with correct stamps and a 3-calendar-day financing accrual."""
    with tempfile.TemporaryDirectory() as td:
        days = weekday_dates(date(2024, 10, 15), 16)
        closes = [(day, 1.26 * 1.001 ** k) for k, day in enumerate(days)]
        a = datetime(2024, 11, 1, 21, 0, tzinfo=UTC)  # after Fri 20:00Z bar
        data_paths = make_fixture(td, story=[("GB", a)], closes=closes)
        out = F.run_arm("anchor", data_paths)
        d = next(x for x in out["decisions"]
                 if x["entry_bar_ts"].startswith("2024-11-01"))
        assert d["decision_ts"] == "2024-10-31T20:00:00+00:00"    # EDT
        assert d["entry_bar_ts"] == "2024-11-01T20:00:00+00:00"   # EDT
        assert d["exit_bar_ts"] == "2024-11-04T21:00:00+00:00"    # EST
        # financing over [Nov 1, Nov 4): three day-start accruals of
        # (0.75 - 1.0)% each, SHORT side: 3 * 10000 * 0.0025 / 365
        ev = next(e for e in out["financing_events"]
                  if e["decision_id"] == d["decision_id"])
        assert ev["financing_adjustment_usd"] == pytest.approx(
            3 * 10000.0 * 0.0025 / 365.0, rel=1e-12)


# ------------------------------------------------------------------ #
# 5. fold force-flat                                                  #
# ------------------------------------------------------------------ #
FOLD_A_AFTER_BAR = datetime(2022, 4, 29, 21, 0, tzinfo=UTC)
FOLD_A_AT_BAR = datetime(2022, 4, 29, 20, 0, tzinfo=UTC)


def _fold_fixture(td, a):
    days = weekday_dates(date(2022, 4, 1), 25)   # Fri Apr 1 .. Fri May 5
    closes = [(day, 1.26 * 1.001 ** k) for k, day in enumerate(days)]
    return make_fixture(td, story=[("GB", a)], closes=closes)


def test_fold_boundary_window_refused():
    """A window that would cross the 2022-05-01 internal boundary is
    refused at entry (fold_boundary_no_entry): no scheduled trade ever
    spans a fold boundary (the kernel's FOLD_FORCE_FLAT_VIOLATION backstop
    stays armed but must never fire on this family's stream)."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = _fold_fixture(td, FOLD_A_AFTER_BAR)
        out = F.run_arm("anchor", data_paths)
        gb = out["meta"]["schedule_totals"]["GBP/USD"]
        assert gb["fold_boundary_no_entry"] == 1
        for d in out["decisions"]:
            ent = datetime.fromisoformat(d["entry_bar_ts"])
            ext = datetime.fromisoformat(d["exit_bar_ts"])
            assert not (ent < datetime(2022, 5, 1, tzinfo=UTC) <= ext)
    # kernel backstop regression: a hand-built spanning decision raises
    dec = {"decision_id": "X", "pair": "GBP/USD", "side": 1,
           "notional_usd": 10000.0,
           "decision_ts": "2022-04-28T20:00:00+00:00",
           "entry_bar_ts": "2022-04-29T20:00:00+00:00",
           "entry_price": 1.26, "exit_bar_ts": "2022-05-02T20:00:00+00:00",
           "exit_price": 1.27}
    with pytest.raises(R.DecisionRuleError, match="FOLD_FORCE_FLAT_VIOLATION"):
        R.validate_decisions([dec], [{"decision_id": "X",
                                      "financing_adjustment_usd": 0.0,
                                      "formula": F.FINANCING_FORMULA_ID}])


def test_fold_truncation_voids_when_span_breaks():
    """a exactly at the last pre-boundary bar's instant: the truncated exit
    would not span the release -> the clock is voided (fold_window_voided),
    never shortened into a non-spanning trade."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = _fold_fixture(td, FOLD_A_AT_BAR)
        out = F.run_arm("anchor", data_paths)
        assert out["meta"]["schedule_totals"]["GBP/USD"][
            "fold_window_voided"] == 1


# ------------------------------------------------------------------ #
# 6. costs exactly once (inherited frozen kernel convention)          #
# ------------------------------------------------------------------ #
def test_costs_charged_exactly_once_per_fill():
    """One round trip pays 1.5 bps per side EXACTLY ONCE: round trip
    10000*1.5/10000*2 = 3.00 USD; price_only = gross - 3.00; the financing
    adjustment is carried, never double-booked.
    gross (SHORT 1.26 -> 1.255): 10000 * (1 - 1.255/1.26) = 10000/252."""
    spec = A.TradeSpec(trade_id="G1", pair="GBP/USD", side="SHORT",
                       notional_usd=10000.0, entry_price=1.26,
                       exit_price=1.255,
                       entry_ts_utc=GOLDEN_ENTRY_TS,
                       exit_ts_utc=GOLDEN_EXIT_TS)
    gross = 10000.0 * (1.0 - 1.255 / 1.26)
    dual = A.book_dual([spec], cost_tier=1.0,
                       financing_adjustment_usd={"G1": 25.0 / 365.0})
    col = dual[0]
    assert col.gross_price_pnl_usd == pytest.approx(gross, rel=1e-12)
    assert col.round_trip_cost_usd == 3.0           # 1.50 entry + 1.50 exit
    assert col.price_only_pnl_usd == pytest.approx(gross - 3.0, rel=1e-12)
    assert col.financing_adjusted_pnl_usd == pytest.approx(
        gross - 3.0 + 25.0 / 365.0, rel=1e-12)


def test_financing_golden_from_module_kernel():
    """The module's financing kernel on the golden trip: SHORT GBP/USD over
    [Jan 18, Jan 19) = ONE day-start accrual of (0.75-1.0)% :
    -1 * 10000 * (-0.0025) / 365 = +25/365 USD."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = make_fixture(td)
        out = F.run_arm("anchor", data_paths)
        d = _golden_decision(out)
        ev = next(e for e in out["financing_events"]
                  if e["decision_id"] == d["decision_id"])
        assert d["side"] == -1
        assert ev["financing_adjustment_usd"] == pytest.approx(
            -1 * 10000.0 * -0.0025 / 365.0, rel=1e-12)
        assert ev["formula"] == F.FINANCING_FORMULA_ID


def test_stress_rows_pairwise_distinct_convention():
    """Convention compatibility: the frozen F1-fixed stress application
    keeps tier rows pairwise distinct (the STRESS_ROWS_NOT_DISTINCT
    regression stays armed) with EXACT hand deltas."""
    spec = A.TradeSpec(trade_id="G1", pair="GBP/USD", side="SHORT",
                       notional_usd=10000.0, entry_price=1.26,
                       exit_price=1.255,
                       entry_ts_utc=GOLDEN_ENTRY_TS,
                       exit_ts_utc=GOLDEN_EXIT_TS)
    booked = A.book_stress([spec])
    tiers = sorted(booked)
    assert tiers == [1.0, 1.5, 2.0]
    assert booked[1.0].booked_rows != booked[1.5].booked_rows
    assert booked[1.0].booked_rows != booked[2.0].booked_rows
    assert booked[1.5].booked_rows != booked[2.0].booked_rows
    # net deltas are EXACT (same float gross at every tier): each tier step
    # adds 10000 * 1.5 * 0.5 / 10000 = 0.75 USD per side, 1.50 per round trip
    assert booked[1.5].net_pnl_usd - booked[1.0].net_pnl_usd \
        == pytest.approx(-1.5)
    assert booked[2.0].net_pnl_usd - booked[1.0].net_pnl_usd \
        == pytest.approx(-3.0)


# ------------------------------------------------------------------ #
# 7. zero-position refusal                                            #
# ------------------------------------------------------------------ #
class _NoReader:
    """Placeholder macro_reader: the family's financing goes through the
    pinned ledger; the kernel only needs a non-None reader."""


def test_zero_positions_refuse_publication():
    """A book whose every in-snapshot clock voids emits NO decisions; the
    kernel cell keeps zero trades and Stage-A carries the frozen refusal
    (STRESS_EMPTY_TRADE_SET)."""
    R.register_family(FAMILY_ID, F)  # the runner contract needs the family
    with tempfile.TemporaryDirectory() as td:
        # only 6 bars: the golden clock sits beyond the snapshot's warmup
        days = weekday_dates(date(2024, 1, 2), 6)
        closes = [(day, 1.26 * 1.001 ** k) for k, day in enumerate(days)]
        data_paths = make_fixture(td, closes=closes)
        out = F.run_arm("anchor", data_paths)
        assert out["decisions"] == []
        rec = R.compute_cell(FAMILY_ID, "anchor", data_paths,
                             freeze_token=None, macro_reader=_NoReader())
        assert rec["n_trades_kept"] == 0
        assert rec["scored"] is False and rec["real_pnl"] is False
        ok, reasons = R.stage_a_gates(rec)
        assert ok is False
        assert "STRESS_EMPTY_TRADE_SET" in reasons


# ------------------------------------------------------------------ #
# 8. control schedules differ from anchor (identifiability)           #
# ------------------------------------------------------------------ #
def test_control_schedule_is_anchor_minus_last_clock_per_economy():
    """Stale-calendar (c_prev) identifiability: the control trades each
    economy's clocks[1:] at the PREVIOUS clock's window -- its emitted
    schedule is the anchor's minus each economy's LAST clock window (the
    control target list skips the first clock, so no target carries the
    final window) -- a PROPER SUBSET that differs from the anchor.

    The snapshot (2018-05 .. 2021-08) is spanned so every economy's LAST
    filler clock (GB 2020-11-05 / CA 2021-04-25 / AU 2019-01-15 /
    NZ 2019-03-25 in this fixture) trades in the anchor."""
    with tempfile.TemporaryDirectory() as td:
        days = weekday_dates(date(2018, 5, 21), 790)
        closes = [(day, 1.26 * 1.001 ** k) for k, day in enumerate(days)]
        data_paths = make_fixture(td, story=[], closes=closes)
        anchor = F.run_arm("anchor", data_paths)
        control = F.run_arm("control", data_paths)
        a_sched = schedule_of(anchor["decisions"])
        c_sched = schedule_of(control["decisions"])
        assert a_sched
        assert c_sched < a_sched                      # proper subset
        assert a_sched - c_sched                      # non-empty difference
        # exactly one dropped window per economy (the last clock's)
        assert len(a_sched - c_sched) == 4
        assert anchor["meta"]["clock_counters"]["skipped_no_predecessor"] == 0
        assert control["meta"]["clock_counters"]["skipped_no_predecessor"] == 4
        # target counts: anchor carries every clock, control skips one per
        # economy (246 - 4 = 242)
        assert anchor["meta"]["clock_counters"]["arm_candidates"] == 246
        assert control["meta"]["clock_counters"]["arm_candidates"] == 242
        # and the benchmark_treatment slot (the kernel's aux arm) is the
        # SAME frozen c_prev schedule as the control
        bench = F.run_arm("benchmark_treatment", data_paths)
        assert schedule_of(bench["decisions"]) == c_sched


def test_sham_schedule_differs_from_anchor():
    """Sham-calendar (+7d) identifiability: decision dates move off the
    anchor's dates (day-of-week preserved, dates shifted); schedule date
    identity stays far below the 90% identifiability bar."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = make_fixture(td, story=_three_gb_clocks(),
                                  closes=_story_closes(n=70))
        anchor = F.run_arm("anchor", data_paths)
        sham = F.run_arm("neighbour", data_paths)
        a_dates = {s[1] for s in schedule_of(anchor["decisions"])}
        n_dates = {s[1] for s in schedule_of(sham["decisions"])}
        assert n_dates
        assert len(a_dates & n_dates) / max(len(n_dates), 1) < 0.10


def test_sham_windows_hold_no_release_and_drops_are_counted():
    """Sham validity: a +7d anchor whose window would contain ANY evidenced
    clock of ANY economy is dropped fail-closed (sham_dropped); every
    EMITTED sham window contains no evidenced instant."""
    with tempfile.TemporaryDirectory() as td:
        # a second evidenced clock engineered strictly inside the +7d
        # window of the golden clock: a' = Jan 25 22:00Z, F' = Jan 25 21:00Z,
        # X' = Jan 26 21:00Z; the second clock at Jan 25 23:00Z is inside.
        story = [("GB", STORY_A),
                 ("GB", STORY_A + timedelta(days=7, hours=1))]
        data_paths = make_fixture(td, story=story)
        sham = F.run_arm("neighbour", data_paths)
        assert sham["meta"]["clock_counters"]["sham_dropped"] == 1
        instants = [c["available"]
                    for c in F.load_clocks(data_paths["conditioning_clocks"])]
        for d in sham["decisions"]:
            ent = datetime.fromisoformat(d["entry_bar_ts"])
            ext = datetime.fromisoformat(d["exit_bar_ts"])
            assert not any(ent < i < ext for i in instants)


# ------------------------------------------------------------------ #
# 9. deterministic replay                                             #
# ------------------------------------------------------------------ #
def test_family_replay_deterministic():
    """Same inputs -> byte-identical run_arm payloads (canonical JSON),
    twice, for the anchor and the neighbour arms alike."""
    with tempfile.TemporaryDirectory() as td:
        data_paths = make_fixture(td, story=_three_gb_clocks(),
                                  closes=_story_closes(n=70))
        for arm in ("anchor", "neighbour", "control"):
            p1 = json.dumps(F.run_arm(arm, data_paths), sort_keys=True,
                            separators=(",", ":"))
            p2 = json.dumps(F.run_arm(arm, data_paths), sort_keys=True,
                            separators=(",", ":"))
            assert p1 == p2


# ------------------------------------------------------------------ #
# 10. malformed / missing clock rows fail closed                      #
# ------------------------------------------------------------------ #
def _full_clocks_fixture(td):
    """A generated full 246-row clocks payload + its header counts."""
    with tempfile.TemporaryDirectory() as inner:
        data_paths = make_fixture(str(inner), story=_three_gb_clocks())
        payload = json.load(open(data_paths["conditioning_clocks"],
                                 encoding="utf-8"))
    return payload


def _rewrite(tmp_path, drop_field=None, mutate=None, drop_row=False):
    """Write a full 246-row clocks file with one row dropped/mutated; the
    header keeps the FROZEN per-economy counts (so only the injected defect
    can fire)."""
    payload = _full_clocks_fixture(tmp_path)
    clocks = payload["clocks"]
    if drop_row:
        clocks.pop(0)
    if drop_field is not None:
        clocks[0].pop(drop_field, None)
    if mutate is not None:
        mutate(clocks)
    out = tmp_path / "mutated.json"
    with open(out, "w", encoding="utf-8") as handle:
        json.dump({"schema": payload["schema"],
                   "S0_window": payload["S0_window"],
                   "per_economy_in_S0": payload["per_economy_in_S0"],
                   "total_clocks_published": len(clocks),
                   "clocks": clocks}, handle)
    return str(out)


def test_missing_clock_file_fails_closed(tmp_path):
    with pytest.raises(F.DataBlocked, match="not found"):
        F.load_clocks(str(tmp_path / "absent.json"))


def test_dropped_row_count_mismatch_fails_closed(tmp_path):
    """One row removed -> 245 parsed vs the frozen 246 header: DataBlocked
    (documented gaps fail closed, never inferred)."""
    with pytest.raises(F.DataBlocked, match="count mismatch"):
        F.load_clocks(_rewrite(tmp_path, drop_row=True))


def test_missing_available_time_fails_closed(tmp_path):
    with pytest.raises(F.DataBlocked, match="available_time_utc"):
        F.load_clocks(_rewrite(tmp_path, drop_field="available_time_utc"))


def test_unparsable_instant_fails_closed(tmp_path):
    def mutate(cs):
        cs[0]["available_time_utc"] = "not-an-instant"
    with pytest.raises(F.DataBlocked, match="unparsable UTC instant"):
        F.load_clocks(_rewrite(tmp_path, mutate=mutate))


def test_timezone_naive_instant_fails_closed(tmp_path):
    def mutate(cs):
        cs[0]["available_time_utc"] = "2024-01-18T22:00:00"
    with pytest.raises(F.DataBlocked, match="timezone-naive"):
        F.load_clocks(_rewrite(tmp_path, mutate=mutate))


def test_missing_archive_sha_fails_closed(tmp_path):
    with pytest.raises(F.DataBlocked, match="archive_sha256"):
        F.load_clocks(_rewrite(tmp_path, drop_field="archive_sha256"))


def test_short_archive_sha_fails_closed(tmp_path):
    def mutate(cs):
        cs[0]["archive_sha256"] = "ab" * 31
    with pytest.raises(F.DataBlocked, match="archive_sha256"):
        F.load_clocks(_rewrite(tmp_path, mutate=mutate))


def test_unevidenced_economy_fails_closed(tmp_path):
    """A US clock row is NOT an evidenced economy of this family (US CPI is
    UNAVAILABLE_FAIL_CLOSED per the p0 verdict): DataBlocked."""
    def mutate(cs):
        cs[0]["economy"] = "US"
    with pytest.raises(F.DataBlocked, match="not an evidenced economy"):
        F.load_clocks(_rewrite(tmp_path, mutate=mutate))


def test_duplicate_clock_fails_closed(tmp_path):
    def mutate(cs):
        cs.append(dict(cs[0]))
    with pytest.raises(F.DataBlocked, match="duplicate"):
        F.load_clocks(_rewrite(tmp_path, mutate=mutate))


def test_out_of_s0_clock_fails_closed(tmp_path):
    def mutate(cs):
        cs[0]["decision_date"] = "2026-01-15"
        cs[0]["available_time_utc"] = "2026-01-15T23:59:59Z"
    with pytest.raises(F.DataBlocked, match="outside the authority's own S0"):
        F.load_clocks(_rewrite(tmp_path, mutate=mutate))


def test_header_count_mismatch_fails_closed(tmp_path):
    payload = _full_clocks_fixture(tmp_path)
    payload["per_economy_in_S0"]["GB"] = 87
    out = tmp_path / "header.json"
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    with pytest.raises(F.DataBlocked, match="count mismatch"):
        F.load_clocks(str(out))


def test_missing_precision_and_reference_fail_closed(tmp_path):
    with pytest.raises(F.DataBlocked, match="precision"):
        F.load_clocks(_rewrite(tmp_path, drop_field="precision"))
    with pytest.raises(F.DataBlocked, match="reference_period"):
        F.load_clocks(_rewrite(tmp_path, drop_field="reference_period"))


def test_run_arm_refuses_missing_data_paths():
    with pytest.raises(F.DataBlocked, match="missing the"):
        F.run_arm("anchor", {"price_h1_dir": "/x"})
    with pytest.raises(ValueError, match="arm must be one of"):
        F.run_arm("nonexistent", {})


# ------------------------------------------------------------------ #
# 11. S0 cap + governor                                               #
# ------------------------------------------------------------------ #
def test_s0_cap_excludes_windows_running_past_the_cap():
    """The S0 cap (2025-07-25T00:00:00Z, the clocks authority's S0 end):
    a GB DAY-stamp clock on 2025-07-24 (available 23:59:59Z) has
    F = Thu Jul 24 20:00Z but X = Fri Jul 25 20:00Z AFTER the cap ->
    excluded and counted (s0_cap_excluded); a mid-July clock whose window
    completes inside S0 still trades (July bars are EDT: 20:00Z)."""
    with tempfile.TemporaryDirectory() as td:
        days = weekday_dates(date(2025, 6, 2), 45)   # Jun 2 .. ~Jul 31
        closes = [(day, 1.26 * 1.001 ** k) for k, day in enumerate(days)]
        story = [
            ("GB", datetime(2025, 7, 16, 23, 59, 59, tzinfo=UTC)),
            ("GB", datetime(2025, 7, 24, 23, 59, 59, tzinfo=UTC)),
        ]
        data_paths = make_fixture(td, story=story, closes=closes)
        out = F.run_arm("anchor", data_paths)
        gb = out["meta"]["schedule_totals"]["GBP/USD"]
        assert gb["s0_cap_excluded"] == 1
        entries = [d["entry_bar_ts"] for d in out["decisions"]
                   if d["pair"] == "GBP/USD"]
        assert "2025-07-16T20:00:00+00:00" in entries
        assert "2025-07-24T20:00:00+00:00" not in entries


def test_governor_blocks_second_entry_while_open():
    """Governor (max 1 position per pair; blocked signals are NO_TRADE,
    never deferred): a second clock whose window opens while the first
    position is still open is NO_TRADE, counted.  (The frozen same-NY-day
    entry clause is subsumed by the open-position rule for one-session
    windows -- an exit never lands on its entry's NY-day -- and stays in
    the module as belt-and-braces.)"""
    with tempfile.TemporaryDirectory() as td:
        story = [
            ("GB", datetime(2024, 1, 19, 22, 0, tzinfo=UTC)),  # Fri
            ("GB", datetime(2024, 1, 20, 12, 0, tzinfo=UTC)),  # Sat
        ]
        data_paths = make_fixture(td, story=story)
        out = F.run_arm("anchor", data_paths)
        entries = [d["entry_bar_ts"] for d in out["decisions"]
                   if d["pair"] == "GBP/USD"]
        assert entries == ["2024-01-19T21:00:00+00:00"]
        assert out["meta"]["clock_counters"]["governor_blocked_open"] == 1
