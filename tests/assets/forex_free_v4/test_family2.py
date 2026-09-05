"""FOREX-FREE-V4 family2 (FXFV4-A6-P2) tests.

All expected numbers are hand-computed literals pinned to the frozen
proposal (research/proposals/forex_free_v4/d1-a6-proposals/
PROPOSAL_FXFV4-A6-P2.json) and the binding selection_freeze directives.
Synthetic fixtures ONLY -- a tiny synthetic ledger jsonl + synthetic H1
bars; NO real snapshots, NO network, NO scored PnL on real data anywhere.
The V3 frozen kernel (research/assets/forex_free_v3) is imported READ-ONLY
for cross-checks and booking; no V3 file is modified.
"""
import json
import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from research.assets.forex_free_v4 import family2 as F
from research.assets.forex_free_v3 import accounting
from research.assets.forex_free_v3 import scored_runner as V3R

NY = ZoneInfo("America/New_York")
UTC = timezone.utc


# ------------------------------------------------------------------ #
# synthetic fixture builders (16:00-NY weekday bars + a tiny ledger)  #
# ------------------------------------------------------------------ #
def weekday_dates(start: date, count: int) -> list:
    out, d = [], start
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def month_weekdays(year: int, month: int) -> list:
    out, d, nxt = [], date(year, month, 1), None
    ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
    end = date(ny, nm, 1)
    d = date(year, month, 1)
    while d < end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def bar_stamp(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 16, 0, tzinfo=NY).astimezone(UTC)


def write_bars(h1_dir: str, pairs, days, skip=()):
    """One snapshot file per pair whose bars are ONLY the 16:00-NY weekday
    stamps of ``days`` (minus ``skip``); opens step by +1 so fills are
    hand-checkable (bar i has open 100.0 + i within a pair's file)."""
    days = [d for d in days if d not in skip]
    for pair in pairs:
        tag = pair.replace("/", "")
        vals = []
        for i, d in enumerate(days):
            ts = bar_stamp(d)
            vals.append({"datetime": ts.strftime("%Y-%m-%d %H:%M:%S"),
                         "open": 100.0 + i, "high": 101.0 + i,
                         "low": 99.0 + i, "close": 100.5 + i})
        with open(os.path.join(h1_dir, f"{tag}_1h_fix.json"), "w") as f:
            json.dump({"values": vals}, f)


def _first_16ny_bar_iso(t: datetime) -> str:
    """First Mon-Fri 16:00-NY bar instant >= t (the ledger's precomputation
    of first_readable_decision_utc from max(availability, effective))."""
    d = t.astimezone(NY).date()
    while True:
        if d.weekday() < 5:
            bar = datetime(d.year, d.month, d.day, 16, 0,
                           tzinfo=NY).astimezone(UTC)
            if bar >= t:
                return bar.strftime("%Y-%m-%dT%H:%M:%SZ")
        d += timedelta(days=1)


def rc_row(area, eff, old, new, op, status="EVIDENCED", row_type="RATE_CHANGE",
           fr="AUTO"):
    """One RATE_CHANGE row as the pinned ledger carries it.

    ``fr`` is the row's PRECOMPUTED ``first_readable_decision_utc`` (the
    A1-adjudicated eligibility field).  ``fr="AUTO"`` mimics the ledger's
    precomputation: the first 16:00-NY weekday bar at/after
    max(operative availability, effective).  ``fr=None`` builds the
    fail-closed class (null first_readable, MISSING_AVAILABLE_TIME_
    EVIDENCE)."""
    if fr == "AUTO":
        if eff is None:  # BASELINE rows carry no first-readable stamp
            fr = None
        else:
            anchor = datetime.fromisoformat(eff + "T00:00:00+00:00")
            if op is not None:
                anchor = max(anchor, datetime.fromisoformat(
                    op.replace("Z", "+00:00")))
            fr = _first_16ny_bar_iso(anchor)
    return {"schema": "forex_free_v3r_announcement_ledger_row_v1",
            "row_type": row_type, "area": area,
            "effective_date": eff,
            "effective_time_utc": (eff + "T00:00:00Z") if eff else None,
            "first_readable_decision_utc": fr,
            "old_value": old, "new_value": new,
            "decision_id": f"{area}:{eff}" if eff else f"{area}:baseline",
            "announcement": {"status": status,
                             "operative_available_time_utc": op}}


def bl_row(area, value):
    """BASELINE_LEVEL floor row exactly as the pinned ledger carries them
    (effective null, availability = 2019-01-01T23:59:59Z conservative
    bound, AVAILABILITY_UNEVIDENCED)."""
    row = rc_row(area, None, None, value, "2019-01-01T23:59:59Z",
                 status="AVAILABILITY_UNEVIDENCED", row_type="BASELINE_LEVEL")
    row["baseline_note"] = "synthetic floor"
    return row


def write_ledger(path: str, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


BASE_RATES = {"US": 0.50, "EMU": 0.50, "GB": 0.50, "JP": 0.10,
              "CH": 0.50, "CA": 0.50, "AU": 0.10, "NZ": 0.30}


def baseline_rows(overrides=None):
    """BASELINE_LEVEL floor for ALL 8 areas (financing accruals read both
    legs of every pair), with optional per-area value overrides."""
    rates = dict(BASE_RATES)
    rates.update(overrides or {})
    return [bl_row(a, v) for a, v in sorted(rates.items())]


def make_env(tmp_path, ledger_rows, days, skip=(), pairs=None):
    h1 = tmp_path / "h1"
    h1.mkdir(parents=True, exist_ok=True)
    write_bars(str(h1), pairs or F.PAIR_UNIVERSE, days, skip=skip)
    led = tmp_path / "ledger.jsonl"
    write_ledger(str(led), ledger_rows)
    return {"h1_dir": str(h1), "announcement_ledger": str(led)}


def canon(payload) -> str:
    return json.dumps(payload, sort_keys=True)


# ------------------------------------------------------------------ #
# constants: frozen kernel cross-check (read-only V3 import)          #
# ------------------------------------------------------------------ #
def test_frozen_constants_equal_the_inherited_kernel():
    assert F.FOLD_BOUNDARIES == V3R.FOLD_BOUNDARIES
    assert F.INTERNAL_BOUNDARIES == V3R.INTERNAL_BOUNDARIES
    assert F.PURGE_DAYS == V3R.PURGE_DAYS
    assert F.MIN_EXPECTANCY == V3R.MIN_EXPECTANCY
    assert F.MIN_PF == V3R.MIN_PF
    assert F.MIN_POSITIVE_FOLDS == V3R.MIN_POSITIVE_FOLDS
    assert F.MIN_FOLD_PF == V3R.MIN_FOLD_PF
    assert F.FOLD_POPULATED_MIN_TRADES == V3R.FOLD_POPULATED_MIN_TRADES
    assert F.MDD_CEILING_USD == V3R.MDD_CEILING_USD
    assert F.MAX_POS_FOLD_SHARE == V3R.MAX_POS_FOLD_SHARE
    assert F.MAX_PAIR_POS_SHARE == V3R.MAX_PAIR_POS_SHARE
    assert F.STRESS_MIN_PF == V3R.STRESS_MIN_PF
    assert F.DROPOUT_SCENARIOS == V3R.DROPOUT_SCENARIOS == 8
    assert F.DROPOUT_MIN_SURVIVAL == V3R.DROPOUT_MIN_SURVIVAL == 6
    assert F.USD_CORR_CEILING == V3R.USD_CORR_CEILING == 0.30
    assert F.MIN_DECISIONS_PER_ARM == V3R.MIN_DECISIONS_PER_ARM == 40
    assert F.MAX_FILL_LAG_DAYS == V3R.MAX_FILL_LAG_DAYS == 4
    assert F.NOTIONAL_USD == 10000
    assert F.ANCHOR_HOLD_NY_DAYS == 10
    assert F.NEIGHBOUR_CUT_HOLD_NY_DAYS == 3
    assert F.BENCHMARK_LAG_DAYS == 180
    assert F.NO_EVAL_CUTOFF_UTC == datetime(2020, 2, 11, tzinfo=UTC)


def test_frozen_direction_maps_match_the_packet():
    # packet arms.control.sham_derangement_frozen.mapping (verbatim table)
    assert F.SHAM_AREA == {"US": "CH", "EMU": "CA", "GB": "AU", "JP": "NZ",
                           "CH": "US", "CA": "EMU", "AU": "GB", "NZ": "JP"}
    assert F.AREA_ORDER == ("US", "EMU", "GB", "JP", "CH", "CA", "AU", "NZ")
    assert F.AREA_OWN_PAIR == {"EMU": "EUR/USD", "GB": "GBP/USD",
                               "AU": "AUD/USD", "NZ": "NZD/USD",
                               "JP": "USD/JPY", "CH": "USD/CHF",
                               "CA": "USD/CAD"}
    # long-USD map on a US hike (packet mechanism, verbatim)
    assert F.US_HIKE_SIDE == {"EUR/USD": -1, "GBP/USD": -1, "AUD/USD": -1,
                              "NZD/USD": -1, "USD/JPY": 1, "USD/CHF": 1,
                              "USD/CAD": 1}


# ------------------------------------------------------------------ #
# feature golden: one hand-computed event                             #
# ------------------------------------------------------------------ #
def test_feature_golden_au_hike_eligibility_direction_hold_exit(tmp_path):
    # AU hike announced 2021-06-01 04:30Z (INSTANT evidenced), effective
    # 2021-06-02: the pre-effective announcement is NOT eligible until the
    # row's first_readable_decision_utc (A1 adjudication A-2) = first
    # 16:00-NY bar at/after effective = Tue Jun 2 20:00Z (EDT).  Entry at
    # the open of the next session bar (Jun 3 20:00Z).  Exit at the open
    # of the 10th existing bar after entry:
    # Jun 4,7,8,9,10,11,14,15,16,17 -> Jun 17 20:00Z.  Side +1 (AU is the
    # AUD/USD base; delta > 0).
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows() + [rc_row("AU", "2021-06-02", 0.10, 0.15,
                                     "2021-06-01T04:30:00Z")]
    dp = make_env(tmp_path, rows, days)
    out = F.run_arm("anchor", dp)
    assert len(out["decisions"]) == 1
    d = out["decisions"][0]
    assert d["pair"] == "AUD/USD"
    assert d["side"] == 1
    assert d["decision_ts"] == "2021-06-02T20:00:00+00:00"
    assert d["entry_bar_ts"] == "2021-06-03T20:00:00+00:00"
    assert d["exit_bar_ts"] == "2021-06-17T20:00:00+00:00"
    assert d["force_flat"] is False
    assert d["notional_usd"] == 10000
    # entry price = OPEN of the Jun 3 bar (May 2021 has 21 weekdays, so
    # Jun 1 is bar index 21, Jun 2 index 22, Jun 3 index 23)
    assert d["entry_price"] == pytest.approx(123.0)
    # exit price = OPEN of the Jun 17 bar (10 sessions after entry, index 33)
    assert d["exit_price"] == pytest.approx(133.0)
    # the decision never reads the event before its availability stamp nor
    # before the row's first_readable instant
    assert datetime.fromisoformat(d["decision_ts"]) >= \
        datetime.fromisoformat("2021-06-01T04:30:00+00:00")
    assert datetime.fromisoformat(d["decision_ts"]) >= \
        datetime.fromisoformat("2021-06-02T20:00:00+00:00")
    # financing: accrual days Jun 3..Jun 16 (14 calendar days) at the
    # day-start differential: AU 0.15% (effective+available by Jun 2) -
    # US 0.50% = -0.35% => +1 * 10000 * 14 * (-0.0035)/365
    ev = out["financing_events"][0]
    assert ev["decision_id"] == d["decision_id"]
    assert ev["formula"] == F.FINANCING_FORMULA_ID
    assert ev["financing_adjustment_usd"] == pytest.approx(
        1 * 10000 * 14 * (-0.0035) / 365.0, abs=1e-9)


def test_feature_golden_quote_area_cut_and_us_cut_map(tmp_path):
    # JP cut (JP is the QUOTE of USD/JPY): delta < 0 -> sign flipped -> +1
    # (BoJ cut weakens JPY => USD/JPY rises => long base USD).  A US cut on
    # the same decision instant drives all 7 pairs with the long-USD map
    # flipped (cut): EUR/USD +1 ... USD/JPY -1 ...
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows({"JP": 0.10}) + [
        rc_row("JP", "2021-06-02", 0.10, 0.05, "2021-06-01T03:00:00Z"),
        rc_row("US", "2021-06-02", 0.50, 0.25, "2021-06-01T18:00:00Z"),
    ]
    dp = make_env(tmp_path, rows, days)
    out = F.run_arm("anchor", dp)
    by_pair = {d["pair"]: d for d in out["decisions"]}
    assert set(by_pair) == set(F.PAIR_UNIVERSE)
    assert by_pair["USD/JPY"]["side"] == 1  # JP cut, quote area, flipped
    # the US cut (later operative availability 18:00Z vs JP 03:00Z; both
    # first_readable stamps land on Jun 2 20:00Z) loses the tie-break on
    # USD/JPY and drives the other 6 pairs, flipped map:
    assert by_pair["EUR/USD"]["side"] == 1
    assert by_pair["GBP/USD"]["side"] == 1
    assert by_pair["AUD/USD"]["side"] == 1
    assert by_pair["NZD/USD"]["side"] == 1
    assert by_pair["USD/CHF"]["side"] == -1
    assert by_pair["USD/CAD"]["side"] == -1
    # every decision shares the same decision instant; ids unique
    instants = {d["decision_ts"] for d in out["decisions"]}
    assert instants == {"2021-06-02T20:00:00+00:00"}
    ids = [d["decision_id"] for d in out["decisions"]]
    assert len(ids) == len(set(ids)) == 7


def test_control_directions_use_the_sham_base_quote_roles(tmp_path):
    # anchor: area X events on X's own pair; control: sham(X)'s pair with
    # the delta re-expressed in the SHAM currency's base/quote role.
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows() + [rc_row("AU", "2021-06-02", 0.10, 0.15,
                                     "2021-06-01T04:30:00Z")]
    dp = make_env(tmp_path, rows, days)
    ctl = F.run_arm("control", dp)["decisions"]
    assert len(ctl) == 1
    # AU -> sham GB -> GBP/USD; GB is the pair's base; delta > 0 -> +1
    assert ctl[0]["pair"] == "GBP/USD"
    assert ctl[0]["side"] == 1
    rows2 = baseline_rows() + [rc_row("CA", "2021-06-02", 0.50, 0.75,
                                      "2021-06-01T04:30:00Z")]
    dp2 = make_env(tmp_path / "env2", rows2, days)
    ctl2 = F.run_arm("control", dp2)["decisions"]
    assert len(ctl2) == 1
    # CA -> sham EMU -> EUR/USD; EMU is the base; delta > 0 -> +1
    assert ctl2[0]["pair"] == "EUR/USD"
    assert ctl2[0]["side"] == 1
    # sham == US: the full long-USD map applies (CH event, hike)
    rows3 = baseline_rows() + [rc_row("CH", "2021-06-02", 0.50, 0.75,
                                      "2021-06-01T04:30:00Z")]
    dp3 = make_env(tmp_path / "env3", rows3, days)
    ctl3 = F.run_arm("control", dp3)["decisions"]
    assert {d["pair"]: d["side"] for d in ctl3} == dict(F.US_HIKE_SIDE)


# ------------------------------------------------------------------ #
# availability-lag mutation (PLAN section 9 MANDATORY)                 #
# ------------------------------------------------------------------ #
def test_availability_lag_mutation_moves_or_kills_the_decision(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6) + \
        month_weekdays(2021, 7)
    base = baseline_rows()
    # golden: first_readable Tue Jun 2 20:00Z -> decision Jun 2 20:00Z
    env1 = make_env(tmp_path / "a", base + [rc_row(
        "AU", "2021-06-02", 0.10, 0.15, "2021-06-01T04:30:00Z")], days)
    d1 = F.run_arm("anchor", env1)["decisions"][0]
    assert d1["decision_ts"] == "2021-06-02T20:00:00+00:00"
    # MUTATION (PLAN section 9): shift the row's first_readable (the
    # eligibility field) later, past the golden decision instant -> the
    # decision MUST move to the next bar and never run earlier.
    env2 = make_env(tmp_path / "b", base + [rc_row(
        "AU", "2021-06-02", 0.10, 0.15, "2021-06-01T04:30:00Z",
        fr="2021-06-03T21:00:00Z")], days)
    d2 = F.run_arm("anchor", env2)["decisions"][0]
    assert d2["decision_ts"] == "2021-06-04T20:00:00+00:00"
    # MUTATION on the operative availability where availability BINDS the
    # precomputation (unevidenced-style op AFTER effective): shifting it
    # later must move the decision (the AUTO first_readable moves with it).
    env3 = make_env(tmp_path / "c", base + [rc_row(
        "AU", "2021-06-02", 0.10, 0.15, "2021-06-02T23:59:59Z",
        status="AVAILABILITY_UNEVIDENCED")], days)
    d3 = F.run_arm("anchor", env3)["decisions"][0]
    assert d3["decision_ts"] == "2021-06-03T20:00:00+00:00"
    env4 = make_env(tmp_path / "d", base + [rc_row(
        "AU", "2021-06-02", 0.10, 0.15, "2021-06-03T23:59:59Z",
        status="AVAILABILITY_UNEVIDENCED")], days)
    d4 = F.run_arm("anchor", env4)["decisions"][0]
    assert d4["decision_ts"] == "2021-06-04T20:00:00+00:00"  # moved +1 session
    # MUTATION: eligibility beyond the snapshot -> the event is never
    # read (no decision bar available; no fabricated backfill).
    env5 = make_env(tmp_path / "e", base + [rc_row(
        "AU", "2021-06-02", 0.10, 0.15, "2021-06-01T04:30:00Z",
        fr="2021-08-02T00:00:00Z")], days)
    out5 = F.run_arm("anchor", env5)
    assert out5["decisions"] == []
    assert out5["meta"]["skipped_counts"].get("NO_DECISION_BAR_AVAILABLE") == 1


def test_eligibility_uses_first_readable_decision_utc(tmp_path):
    # A1 adjudication A-2 discriminator: the eligibility instant is the
    # row's PRECOMPUTED first_readable_decision_utc -- never re-derived
    # from operative availability or from the effective instant.
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6) + \
        month_weekdays(2021, 7)
    base = baseline_rows()
    # (a) announcement BEFORE effective (the 87-row evidenced class: US/AU
    # INSTANT the day before, NZ/CH/JP DAY rows): the row must NOT be
    # eligible until the first decision at/after EFFECTIVE.  Availability-
    # only eligibility would give Jun 1 20:00Z -- refused.
    dp_a = make_env(tmp_path / "a", base + [rc_row(
        "AU", "2021-06-02", 0.10, 0.15, "2021-06-01T04:30:00Z")], days)
    da = F.run_arm("anchor", dp_a)["decisions"][0]
    assert da["decision_ts"] == "2021-06-02T20:00:00+00:00"
    assert datetime.fromisoformat(da["decision_ts"]) >= \
        datetime.fromisoformat("2021-06-02T00:00:00+00:00")  # >= effective
    # (b) pure discriminator: a row whose first_readable sits later than
    # ANY locally derivable instant (Jun 1 availability, Jun 2 effective):
    # only the precomputed field can produce the Jun 7 decision.
    dp_b = make_env(tmp_path / "b", base + [rc_row(
        "AU", "2021-06-02", 0.10, 0.15, "2021-06-01T04:30:00Z",
        fr="2021-06-07T20:00:00Z")], days)
    db = F.run_arm("anchor", dp_b)["decisions"][0]
    assert db["decision_ts"] == "2021-06-07T20:00:00+00:00"


# ------------------------------------------------------------------ #
# dedupe semantics: (area, effective_date) last-row-wins              #
# ------------------------------------------------------------------ #
def test_dedupe_last_row_wins_upgrade_moves_eligibility_earlier(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    base = baseline_rows()
    # eff 2021-06-01 (the real AU pattern): the unevidenced row's
    # conservative bound sits at the END of the effective day -> its
    # first_readable is the NEXT day's bar (Jun 2); the EVIDENCED upgrade's
    # first_readable is the effective day's own bar (Jun 1).
    unevidenced = rc_row("AU", "2021-06-01", 0.10, 0.15,
                         "2021-06-01T23:59:59Z", status="AVAILABILITY_UNEVIDENCED")
    evidenced = rc_row("AU", "2021-06-01", 0.10, 0.15,
                       "2021-05-31T04:30:00Z", status="EVIDENCED")
    assert unevidenced["first_readable_decision_utc"] == "2021-06-02T20:00:00Z"
    assert evidenced["first_readable_decision_utc"] == "2021-06-01T20:00:00Z"
    # unevidenced row ALONE: conservative LATER bound -> decision Jun 2
    dp_unev = make_env(tmp_path / "unev", base + [unevidenced], days)
    d_unev = F.run_arm("anchor", dp_unev)["decisions"][0]
    assert d_unev["decision_ts"] == "2021-06-02T20:00:00+00:00"
    # duplicated (area, effective_date): the EVIDENCED upgrade must govern
    # (last-row-wins) -> decision Jun 1, NOT the unevidenced Jun 2 read
    dp_dedup = make_env(tmp_path / "dedup", base + [unevidenced, evidenced], days)
    out = F.run_arm("anchor", dp_dedup)
    assert len(out["decisions"]) == 1
    assert out["decisions"][0]["decision_ts"] == "2021-06-01T20:00:00+00:00"
    assert out["meta"]["events"]["raw_rows"] == len(base) + 2
    assert out["meta"]["events"]["deduped_rate_change_rows"] == 1
    assert out["meta"]["events"]["events_used"] == 1


# ------------------------------------------------------------------ #
# one-event/one-bar lag, no-lookahead, fail-closed fills              #
# ------------------------------------------------------------------ #
def _assert_one_event_lag(decisions):
    for d in decisions:
        dec = datetime.fromisoformat(d["decision_ts"])
        ent = datetime.fromisoformat(d["entry_bar_ts"])
        ext = datetime.fromisoformat(d["exit_bar_ts"])
        assert ent > dec  # never a same-bar fill (no lookahead)
        assert ent - dec <= timedelta(days=F.MAX_FILL_LAG_DAYS)
        assert ext > ent


def test_missing_next_session_bar_fails_closed_no_trade(tmp_path):
    days = month_weekdays(2021, 6)
    rows = baseline_rows() + [rc_row("AU", "2021-06-30", 0.10, 0.15,
                                     "2021-06-29T21:00:00Z")]
    # first_readable = Jun 30 20:00Z, the LAST existing bar: no
    # next-session bar exists, so the signal is voided fail-closed
    # (never backfilled)
    dp = make_env(tmp_path, rows, days)
    out = F.run_arm("anchor", dp)
    assert out["decisions"] == []
    assert out["meta"]["skipped_counts"].get("MISSING_NEXT_FILL_BAR") == 1
    assert out["meta"]["skipped_decisions"][0]["reason"] == "MISSING_NEXT_FILL_BAR"
    assert out["financing_events"] == []


def test_missing_session_bar_shifts_fill_to_next_existing_bar(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows() + [rc_row("AU", "2021-06-02", 0.10, 0.15,
                                     "2021-06-01T04:30:00Z")]
    # first_readable Jun 2 20:00Z; Jun 3 absent on AUD/USD: the fill goes
    # to the next EXISTING 16:00-NY bar (Jun 4), still inside the frozen
    # one-session/4-day convention
    dp = make_env(tmp_path, rows, days, skip={date(2021, 6, 3)})
    out = F.run_arm("anchor", dp)
    assert len(out["decisions"]) == 1
    d = out["decisions"][0]
    assert d["decision_ts"] == "2021-06-02T20:00:00+00:00"
    assert d["entry_bar_ts"] == "2021-06-04T20:00:00+00:00"
    assert d["exit_bar_ts"] == "2021-06-18T20:00:00+00:00"


def test_fill_gap_over_4_days_fails_closed_no_trade(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows() + [rc_row("AU", "2021-06-02", 0.10, 0.15,
                                     "2021-06-01T04:30:00Z")]
    # first_readable Jun 2 (decision bar exists); Jun 3..Jun 9 bars missing
    # on AUD/USD: the next existing bar is Jun 10, 8 days after the Jun 2
    # decision -> over the frozen 4-day allowance
    skip = {date(2021, 6, d) for d in (3, 4, 7, 8, 9)}
    dp = make_env(tmp_path, rows, days, skip=skip)
    out = F.run_arm("anchor", dp)
    assert out["decisions"] == []
    assert out["meta"]["skipped_counts"].get("FILL_LAG_EXCEEDS_4_DAYS") == 1


def test_golden_schedule_respects_the_one_event_lag(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows({"JP": 0.10}) + [
        rc_row("JP", "2021-06-02", 0.10, 0.05, "2021-06-01T03:00:00Z"),
        rc_row("US", "2021-06-02", 0.50, 0.25, "2021-06-01T18:00:00Z")]
    dp = make_env(tmp_path, rows, days)
    out = F.run_arm("anchor", dp)
    _assert_one_event_lag(out["decisions"])
    # no decision ever trades a pair outside the frozen universe; cash is
    # never an instrument
    assert {d["pair"] for d in out["decisions"]} <= set(F.PAIR_UNIVERSE)
    assert "USD" not in {d["pair"] for d in out["decisions"]}


# ------------------------------------------------------------------ #
# DST boundary weeks (fall-back and spring-forward)                   #
# ------------------------------------------------------------------ #
def test_dst_fall_back_week_stamps_20z_then_21z(tmp_path):
    # EDT through Fri Nov 5 2021; EST from Mon Nov 8 (DST ends Sun Nov 7).
    # Pre-effective announcement (Nov 3) of an eff-Nov-4 change: eligible
    # only from the effective day's bar (Nov 4 20:00Z, EDT).
    days = month_weekdays(2021, 11)
    rows = baseline_rows() + [rc_row("AU", "2021-11-04", 0.10, 0.15,
                                     "2021-11-03T18:00:00Z")]
    dp = make_env(tmp_path, rows, days)
    d = F.run_arm("anchor", dp)["decisions"][0]
    assert d["decision_ts"] == "2021-11-04T20:00:00+00:00"  # Thu, EDT
    assert d["entry_bar_ts"] == "2021-11-05T20:00:00+00:00"  # Fri, EDT
    # 10 sessions after entry: Nov 8,9,10,11,12,15,16,17,18,19 -> EST 21:00Z
    assert d["exit_bar_ts"] == "2021-11-19T21:00:00+00:00"


def test_dst_spring_forward_week_stamps_21z_then_20z(tmp_path):
    # EST through Fri Mar 11 2022; EDT from Mon Mar 14 (DST starts Sun 13).
    # Pre-effective announcement (Mar 8) of an eff-Mar-9 change: eligible
    # only from the effective day's bar (Mar 9 21:00Z, EST).
    days = month_weekdays(2022, 3)
    rows = baseline_rows() + [rc_row("AU", "2022-03-09", 0.10, 0.15,
                                     "2022-03-08T05:00:00Z")]
    dp = make_env(tmp_path, rows, days)
    d = F.run_arm("anchor", dp)["decisions"][0]
    assert d["decision_ts"] == "2022-03-09T21:00:00+00:00"  # Wed, EST
    assert d["entry_bar_ts"] == "2022-03-10T21:00:00+00:00"  # Thu, EST
    # 10 sessions after entry: Mar 11, 14..18, 21..24 -> EDT 20:00Z
    assert d["exit_bar_ts"] == "2022-03-24T20:00:00+00:00"


# ------------------------------------------------------------------ #
# force-flat, earliest-scheduled exit, costs, cash                    #
# ------------------------------------------------------------------ #
def test_force_flat_at_internal_fold_boundary(tmp_path):
    # GB hike effective 2022-04-20 (announced pre-effective on Apr 18):
    # first_readable = Wed Apr 20 20:00Z; entry Thu Apr 21; the scheduled
    # exit (10 sessions) would be May 5 but the internal boundary
    # 2022-05-01 force-flattens at the LAST decision bar before it:
    # Fri Apr 29 20:00Z (force_flat=true).
    days = month_weekdays(2022, 4) + month_weekdays(2022, 5)
    rows = baseline_rows() + [rc_row("GB", "2022-04-20", 0.50, 0.75,
                                     "2022-04-18T09:00:00Z")]
    dp = make_env(tmp_path, rows, days)
    out = F.run_arm("anchor", dp)
    assert len(out["decisions"]) == 1
    d = out["decisions"][0]
    assert d["pair"] == "GBP/USD"
    assert d["decision_ts"] == "2022-04-20T20:00:00+00:00"
    assert d["entry_bar_ts"] == "2022-04-21T20:00:00+00:00"
    assert d["exit_bar_ts"] == "2022-04-29T20:00:00+00:00"
    assert d["force_flat"] is True


def test_earliest_scheduled_exit_at_data_end_never_fill_forward(tmp_path):
    # entry with fewer than 10 remaining sessions: exit at the LAST
    # existing bar (earliest-scheduled exit), never beyond the snapshot.
    days = month_weekdays(2021, 6)
    rows = baseline_rows() + [rc_row("AU", "2021-06-18", 0.15, 0.20,
                                     "2021-06-16T21:00:00Z")]
    dp = make_env(tmp_path, rows, days)
    out = F.run_arm("anchor", dp)
    assert len(out["decisions"]) == 1
    d = out["decisions"][0]
    # first_readable = Fri Jun 18 20:00Z; entry Mon Jun 21
    assert d["decision_ts"] == "2021-06-18T20:00:00+00:00"
    assert d["entry_bar_ts"] == "2021-06-21T20:00:00+00:00"
    # only 7 sessions remain after entry: exit at the last June bar
    assert d["exit_bar_ts"] == "2021-06-30T20:00:00+00:00"
    assert d["force_flat"] is False
    assert out["meta"]["schedule_totals"]["AUD/USD"][
        "earliest_scheduled_exit_data_end"] == 1


def test_costs_charged_exactly_once_per_fill(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows() + [rc_row("AU", "2021-06-02", 0.10, 0.15,
                                     "2021-06-01T04:30:00Z")]
    dp = make_env(tmp_path, rows, days)
    out = F.run_arm("anchor", dp)
    specs = F.build_trade_specs(out["decisions"])
    dual = accounting.book_dual(specs, cost_tier=1.0,
                                financing_adjustment_usd={
                                    out["financing_events"][0]["decision_id"]:
                                        out["financing_events"][0]["financing_adjustment_usd"]})
    col = dual[0]
    gross = 10000 * (col.exit_price / col.entry_price - 1.0)
    # 1.5 bps per side, charged once at entry and once at exit = 3.00 USD
    assert col.round_trip_cost_usd == pytest.approx(3.00, abs=1e-9)
    assert col.price_only_pnl_usd == pytest.approx(gross - 3.00, abs=1e-9)
    assert col.financing_adjusted_pnl_usd == pytest.approx(
        gross - 3.00 + out["financing_events"][0]["financing_adjustment_usd"],
        abs=1e-9)


def test_cash_is_never_an_instrument():
    bad = {"decision_id": "X", "pair": "USD", "side": 1, "notional_usd": 10000,
           "decision_ts": "2021-06-01T20:00:00+00:00",
           "entry_bar_ts": "2021-06-02T20:00:00+00:00", "entry_price": 100.0,
           "exit_bar_ts": "2021-06-16T20:00:00+00:00", "exit_price": 101.0,
           "force_flat": False}
    with pytest.raises(Exception) as ei:
        V3R.validate_decisions([bad], [])
    assert "DECISION_CLOCK_VIOLATION" in str(ei.value)
    with pytest.raises(accounting.PositionBookError):
        F.build_trade_specs([bad])


# ------------------------------------------------------------------ #
# stress-tier scaling: re-booking, multipliers reach booked PnL        #
# ------------------------------------------------------------------ #
def _hand_specs():
    t = "2021-06-02T20:00:00+00:00"
    t2 = "2021-06-16T20:00:00+00:00"
    return [
        accounting.TradeSpec(trade_id="t1", pair="EUR/USD", side="LONG",
                             notional_usd=10000.0, entry_price=100.0,
                             exit_price=101.0, entry_ts_utc=t, exit_ts_utc=t2),
        accounting.TradeSpec(trade_id="t2", pair="EUR/USD", side="LONG",
                             notional_usd=10000.0, entry_price=100.0,
                             exit_price=99.0, entry_ts_utc=t, exit_ts_utc=t2),
        accounting.TradeSpec(trade_id="t3", pair="USD/JPY", side="SHORT",
                             notional_usd=10000.0, entry_price=100.0,
                             exit_price=99.0, entry_ts_utc=t, exit_ts_utc=t2),
    ]


def test_stress_tiers_rebook_the_same_trade_set():
    specs = _hand_specs()
    booked = accounting.book_stress(specs)
    assert sorted(booked) == [1.0, 1.5, 2.0]
    grosses = {t: round(booked[t].gross_price_pnl_usd, 9) for t in booked}
    assert len(set(grosses.values())) == 1  # gross is tier-invariant
    # multipliers REACH the booked PnL: the identical 3-trade set re-books
    # at each tier's per-side cost (2 sides x 3 trades x 1.5bps x tier on
    # the 10000 USD-unit notional = 9.00 / 13.50 / 18.00 USD round trips)
    for tier, rt_cost in ((1.0, 9.00), (1.5, 13.50), (2.0, 18.00)):
        r = booked[tier]
        assert r.round_trip_cost_usd == pytest.approx(rt_cost, abs=1e-9)
        assert r.net_pnl_usd == pytest.approx(100.0 - rt_cost, abs=1e-9)
    # rows pairwise distinct across tiers (the V2 defect regression pin)
    accounting.assert_stress_rows_distinct(booked)
    # and never compounded (tier 2.0 costs 18.00, not 9.00 + 18.00)
    assert booked[2.0].net_pnl_usd == pytest.approx(82.0, abs=1e-9)


def test_cell_record_stress_block_matches_the_kernel(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows() + [rc_row("AU", "2021-06-02", 0.10, 0.15,
                                     "2021-06-01T04:30:00Z")]
    dp = make_env(tmp_path, rows, days)
    out = F.run_arm("anchor", dp)
    rec = F.assemble_cell_record(out["decisions"], out["financing_events"],
                                 arm="anchor")
    specs = F.build_trade_specs(out["decisions"])
    ids = {out["decisions"][0]["decision_id"]}
    kernel_stress = F.stress_book(specs, ids)
    assert rec["stress"].keys() == kernel_stress.keys()
    for tier in rec["stress"]:
        assert rec["stress"][tier]["total_pnl"] == \
            pytest.approx(kernel_stress[tier]["total_pnl"], abs=1e-9)
        assert rec["stress"][tier]["stress_rows_distinct_certified"] is True
    # gross tier-invariant across the record's stress block
    # (single trade: gross +10.0 from open 121 -> exit 131 on 10000 notional)
    gross = 10000 * (out["decisions"][0]["exit_price"]
                     / out["decisions"][0]["entry_price"] - 1.0)
    for tier, rt in (("tier1.0", 3.0), ("tier1.5", 4.5), ("tier2.0", 6.0)):
        assert rec["stress"][tier]["total_pnl"] == pytest.approx(
            gross - rt, abs=1e-6)


# ------------------------------------------------------------------ #
# control arm: differs from the anchor and completes fail-closed      #
# ------------------------------------------------------------------ #
def test_control_fires_different_pairs_than_the_anchor(tmp_path):
    # US hike (drives all 7 in the anchor; only USD/CHF in the control)
    # + AU hike (AUD/USD anchor; GBP/USD control).  Same decision instant,
    # so the AUD/USD tie-break also resolves to the earlier AU availability.
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows() + [
        rc_row("US", "2021-06-02", 0.50, 0.75, "2021-06-01T18:00:00Z"),
        rc_row("AU", "2021-06-02", 0.10, 0.15, "2021-06-01T04:30:00Z"),
    ]
    dp = make_env(tmp_path, rows, days)
    anchor = F.run_arm("anchor", dp)["decisions"]
    control = F.run_arm("control", dp)["decisions"]
    # anchor: 7 pair decisions (US drives 6 pairs; the AUD/USD candidate
    # from the US event loses the tie-break to the earlier AU availability)
    assert {(d["pair"], d["side"]) for d in anchor} == {
        ("EUR/USD", -1), ("GBP/USD", -1), ("AUD/USD", 1), ("NZD/USD", -1),
        ("USD/JPY", 1), ("USD/CHF", 1), ("USD/CAD", 1)}
    assert len(anchor) == 7
    # control: exactly two different (pair, side) reads
    assert {(d["pair"], d["side"]) for d in control} == {
        ("USD/CHF", -1),   # US -> sham CH (quote of USD/CHF); hike -> -1
        ("GBP/USD", 1)}    # AU -> sham GB (base of GBP/USD); hike -> +1
    assert {(d["pair"], d["side"]) for d in control} != \
        {(d["pair"], d["side"]) for d in anchor}


def test_control_completes_under_fail_closed_missing_bar(tmp_path):
    # the control's first_readable lands on the LAST bar: no next-session
    # bar exists for its sham pair, so the signal is voided fail-closed and
    # the control still COMPLETES (returns; no decision, no financing row).
    days = month_weekdays(2021, 6)
    rows = baseline_rows() + [rc_row("US", "2021-06-30", 0.50, 0.75,
                                     "2021-06-29T21:00:00Z")]
    dp = make_env(tmp_path, rows, days)
    out = F.run_arm("control", dp)
    assert out["decisions"] == []  # US -> sham CH -> USD/CHF only
    assert out["meta"]["skipped_counts"].get("MISSING_NEXT_FILL_BAR") == 1
    assert out["meta"]["skipped_decisions"][0]["pair"] == "USD/CHF"
    assert out["financing_events"] == []  # voided signal books nothing


def test_family_control_gate_preregistered_rule():
    def rec(exp, pf):
        return {"base": {"expectancy": exp, "pf": pf}}
    # clause A: control expectancy > 0 AND pf >= 1.10 -> reproduces
    g = F.family_control_gate(rec(0.10, 1.20), rec(0.20, 1.30))
    assert g["control_reproduces"] is True and g["clause_a_expectancy_and_pf"]
    # clause B: control expectancy >= 0.5 x anchor -> reproduces
    g = F.family_control_gate(rec(0.10, 5.0), rec(0.06, 0.90))
    assert g["control_reproduces"] is True and g["clause_b_half_anchor_expectancy"]
    # neither clause -> does NOT reproduce
    g = F.family_control_gate(rec(0.10, 5.0), rec(0.04, 0.90))
    assert g["control_reproduces"] is False
    # positive-but-thin control PnL never overrides a firing pf clause
    g = F.family_control_gate(rec(0.10, 5.0), rec(0.05, 1.10))
    assert g["control_reproduces"] is True


# ------------------------------------------------------------------ #
# neighbour asymmetry: hike 10 / cut 3                                #
# ------------------------------------------------------------------ #
def test_neighbour_asymmetric_holds_by_direction(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows() + [
        rc_row("AU", "2021-06-02", 0.10, 0.15, "2021-06-01T04:30:00Z"),  # hike
        rc_row("NZ", "2021-06-02", 0.30, 0.25, "2021-06-01T03:00:00Z"),  # cut
    ]
    dp = make_env(tmp_path, rows, days)
    anchor = {d["pair"]: d for d in F.run_arm("anchor", dp)["decisions"]}
    neigh = {d["pair"]: d for d in F.run_arm("neighbour", dp)["decisions"]}
    # first_readable Jun 2 -> entry Jun 3; hike: hold 10 in BOTH arms
    # (Jun 4,7,8,9,10,11,14,15,16,17)
    assert anchor["AUD/USD"]["exit_bar_ts"] == "2021-06-17T20:00:00+00:00"
    assert neigh["AUD/USD"]["exit_bar_ts"] == "2021-06-17T20:00:00+00:00"
    # cut: anchor still holds 10; the neighbour exits after 3 sessions
    # (Jun 4, Jun 7, Jun 8)
    assert anchor["NZD/USD"]["exit_bar_ts"] == "2021-06-17T20:00:00+00:00"
    assert neigh["NZD/USD"]["exit_bar_ts"] == "2021-06-08T20:00:00+00:00"
    assert neigh["NZD/USD"]["side"] == -1  # NZ base, delta < 0
    # everything else is byte-identical to the anchor modulo the arm tag
    strip = lambda ds: [{k: v for k, v in d.items() if k != "decision_id"}
                        for d in ds]
    assert strip([anchor["AUD/USD"]]) == strip([neigh["AUD/USD"]])


def test_hold_ny_days_law():
    hike = {"delta": 0.25}
    cut = {"delta": -0.25}
    for arm in ("anchor", "causal_negative_control", "bench"):
        assert F.hold_ny_days(hike, arm) == 10
        assert F.hold_ny_days(cut, arm) == 10
    assert F.hold_ny_days(hike, "neighbour") == 10
    assert F.hold_ny_days(cut, "neighbour") == 3


# ------------------------------------------------------------------ #
# benchmark treatment: +180d staleness, else byte-identical            #
# ------------------------------------------------------------------ #
def test_benchmark_shifts_availability_180d_else_identical(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6) + \
        month_weekdays(2021, 12)
    rows = baseline_rows() + [rc_row("AU", "2021-06-02", 0.10, 0.15,
                                     "2021-06-01T04:30:00Z")]
    dp = make_env(tmp_path, rows, days)
    anchor = F.run_arm("anchor", dp)["decisions"][0]
    bench_out = F.run_arm("benchmark_treatment", dp)
    assert bench_out["meta"]["benchmark_treatment"]["bench_schedule_id"] == \
        "FXFV4-A6-P2-bench"
    assert bench_out["meta"]["benchmark_treatment"]["lag_days"] == 180
    # +180d puts availability on 2021-11-28: the first December bar decides
    bench = bench_out["decisions"][0]
    assert bench["decision_ts"] == "2021-12-01T21:00:00+00:00"  # EST
    assert bench["side"] == anchor["side"]
    assert bench["entry_bar_ts"] != anchor["entry_bar_ts"]
    # a December event whose stale twin falls beyond the snapshot drops out
    rows2 = baseline_rows() + [rc_row("GB", "2021-12-10", 0.50, 0.75,
                                      "2021-12-09T10:00:00Z")]
    dp2 = make_env(tmp_path / "e2", rows2, days)
    anchor2 = F.run_arm("anchor", dp2)
    bench2 = F.run_arm("benchmark_treatment", dp2)
    assert len(anchor2["decisions"]) == 1
    assert bench2["decisions"] == []
    assert bench2["meta"]["skipped_counts"].get("NO_DECISION_BAR_AVAILABLE") == 1


def test_no_decision_ever_reads_its_event_before_availability(tmp_path):
    # SYSTEMATIC no-lookahead property over every arm on a multi-event
    # fixture: each decision's instant is >= the earliest operative
    # availability among the events that map to its pair under that arm,
    # and the fill is strictly later (one-event lag, never same-bar).
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    events = [
        rc_row("US", "2021-06-02", 0.50, 0.75, "2021-06-01T18:00:00Z"),
        rc_row("AU", "2021-06-02", 0.10, 0.15, "2021-06-01T04:30:00Z"),
        rc_row("NZ", "2021-06-02", 0.30, 0.25, "2021-06-01T03:00:00Z"),
    ]
    dp = make_env(tmp_path, baseline_rows() + events, days)
    evs = F.extract_events(F.dedupe_ledger_rows(baseline_rows() + events))["events"]
    for arm in ("anchor", "neighbour", "control"):
        arm_id = {"control": "causal_negative_control"}.get(arm, arm)
        earliest = {}
        for ev in evs:
            for pair in F.mapped_directions(ev, arm_id):
                earliest[pair] = min(earliest.get(pair, ev["eligible_dt"]),
                                     ev["eligible_dt"])
        for d in F.run_arm(arm, dp)["decisions"]:
            assert datetime.fromisoformat(d["decision_ts"]) >= \
                earliest[d["pair"]]
            assert datetime.fromisoformat(d["entry_bar_ts"]) > \
                datetime.fromisoformat(d["decision_ts"])


# ------------------------------------------------------------------ #
# malformed / missing rows: fail closed                               #
# ------------------------------------------------------------------ #
def test_malformed_rows_fail_closed(tmp_path):
    days = month_weekdays(2021, 6)
    good = baseline_rows() + [rc_row("AU", "2021-06-02", 0.10, 0.15,
                                     "2021-06-01T04:30:00Z")]
    bad_stamp = rc_row("GB", "2021-06-03", 0.50, 0.75, "2021-06-02T09:00:00Z")
    bad_stamp["effective_time_utc"] = "not-a-date"
    dp = make_env(tmp_path / "a", good + [bad_stamp], days)
    with pytest.raises(F.DataBlocked):
        F.run_arm("anchor", dp)
    bad_value = rc_row("GB", "2021-06-03", 0.50, 0.75, "2021-06-02T09:00:00Z")
    bad_value["new_value"] = "cheap"
    dp = make_env(tmp_path / "b", good + [bad_value], days)
    with pytest.raises(F.DataBlocked):
        F.run_arm("anchor", dp)
    bad_type = rc_row("GB", "2021-06-03", 0.50, 0.75, "2021-06-02T09:00:00Z")
    bad_type["row_type"] = "MYSTERY_ROW"
    dp = make_env(tmp_path / "c", good + [bad_type], days)
    with pytest.raises(F.DataBlocked):
        F.run_arm("anchor", dp)
    with open(tmp_path / "d_ledger.jsonl", "w") as f:
        f.write("{not json}\n")
    dp = {"h1_dir": str(tmp_path / "a" / "h1"),
          "announcement_ledger": str(tmp_path / "d_ledger.jsonl")}
    with pytest.raises(F.DataBlocked):
        F.run_arm("anchor", dp)
    with pytest.raises(F.DataBlocked):
        F.run_arm("anchor", {"announcement_ledger": "/no/such/file.jsonl"})
    with pytest.raises(F.DataBlocked):
        F.run_arm("anchor", {"announcement_ledger": good and "x"})


def test_missing_availability_stamp_never_read_but_others_trade(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    # null first_readable_decision_utc: the MISSING_AVAILABLE_TIME_EVIDENCE
    # fail-closed class (A1 adjudication A-2) -- NEVER read
    stampless = rc_row("AU", "2021-06-02", 0.10, 0.15,
                       "2021-06-01T04:30:00Z", fr=None)
    good = rc_row("GB", "2021-06-02", 0.50, 0.75, "2021-06-01T09:00:00Z")
    dp = make_env(tmp_path, baseline_rows() + [stampless, good], days)
    out = F.run_arm("anchor", dp)
    pairs = {d["pair"] for d in out["decisions"]}
    assert pairs == {"GBP/USD"}  # the stampless event is NEVER read
    assert out["meta"]["events"]["n_unavailable_never_read"] == 1
    assert out["meta"]["events"]["unavailable_never_read"] == [
        {"area": "AU", "effective_date": "2021-06-02",
         "reason": "MISSING_AVAILABLE_TIME_EVIDENCE"}]


def test_no_eval_cutoff_is_fail_closed(tmp_path):
    # an event fully decidable before the frozen 2020-02-11 cutoff is
    # NO_EVAL, never backfilled
    days = month_weekdays(2020, 1)
    rows = baseline_rows() + [rc_row("AU", "2020-01-15", 0.10, 0.15,
                                     "2020-01-14T04:30:00Z")]
    dp = make_env(tmp_path, rows, days)
    out = F.run_arm("anchor", dp)
    assert out["decisions"] == []
    assert out["meta"]["eligibility"]["no_eval_before_cutoff"] == 1


# ------------------------------------------------------------------ #
# determinism: byte-identical double run                              #
# ------------------------------------------------------------------ #
def test_deterministic_double_run(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows() + [
        rc_row("US", "2021-06-02", 0.50, 0.75, "2021-06-01T18:00:00Z"),
        rc_row("AU", "2021-06-02", 0.10, 0.15, "2021-06-01T04:30:00Z"),
        rc_row("NZ", "2021-06-02", 0.30, 0.25, "2021-06-01T03:00:00Z"),
    ]
    dp = make_env(tmp_path, rows, days)
    for arm in ("anchor", "neighbour", "control", "benchmark_treatment"):
        a = F.run_arm(arm, dp)
        b = F.run_arm(arm, dp)
        assert canon(a) == canon(b)


# ------------------------------------------------------------------ #
# cell-record margin-to-fail fields (hand-computed book)              #
# ------------------------------------------------------------------ #
def _hand_decisions():
    """Three decisions with hand-computable PnL, all inside fold F1, each
    entry one session AFTER its decision instant (one-event lag; fills on
    Tue/Wed/Mon so the frozen session gate keeps them)."""
    def dec(tid, pair, side, d_ts, e_ts, e_px, x_ts, x_px):
        return {"decision_id": tid, "pair": pair, "side": side,
                "decision_ts": d_ts, "notional_usd": 10000,
                "entry_bar_ts": e_ts, "entry_price": e_px,
                "exit_bar_ts": x_ts, "exit_price": x_px, "force_flat": False}
    return [
        # LONG 100 -> 101: gross +100.00; price_only +97.00
        dec("t1", "EUR/USD", 1, "2020-06-01T20:00:00+00:00",
            "2020-06-02T20:00:00+00:00", 100.0,
            "2020-06-16T20:00:00+00:00", 101.0),
        # LONG 100 -> 99: gross -100.00; price_only -103.00
        dec("t2", "EUR/USD", 1, "2020-06-30T20:00:00+00:00",
            "2020-07-01T20:00:00+00:00", 100.0,
            "2020-07-15T20:00:00+00:00", 99.0),
        # SHORT 100 -> 99: gross +100.00; price_only +97.00
        dec("t3", "USD/JPY", -1, "2020-07-31T20:00:00+00:00",
            "2020-08-03T20:00:00+00:00", 100.0,
            "2020-08-17T20:00:00+00:00", 99.0),
    ]


def test_margin_to_fail_fields_hand_computed():
    decs = _hand_decisions()
    fin = [{"decision_id": d["decision_id"], "financing_adjustment_usd": 0.0,
            "formula": F.FINANCING_FORMULA_ID} for d in decs]
    rec = F.assemble_cell_record(decs, fin, arm="anchor")
    base = rec["base"]
    assert base["trades"] == 3
    assert base["total_pnl"] == pytest.approx(91.0, abs=1e-9)
    assert base["expectancy"] == pytest.approx(91.0 / 3.0, abs=1e-9)
    assert base["pf"] == pytest.approx(194.0 / 103.0, abs=1e-9)
    assert rec["base_price_only"]["expectancy"] == \
        pytest.approx(91.0 / 3.0, abs=1e-9)
    assert rec["mdd_usd"] == pytest.approx(103.0, abs=1e-9)
    mtf = rec["margin_to_fail"]
    assert mtf["gate_expectancy_gt_0"]["margin"] == \
        pytest.approx(91.0 / 3.0, abs=1e-9)
    assert mtf["gate_pf_ge_1_10"]["margin"] == \
        pytest.approx(194.0 / 103.0 - 1.10, abs=1e-9)
    assert mtf["gate_price_only_expectancy_no_inversion"]["margin"] == \
        pytest.approx(91.0 / 3.0, abs=1e-9)
    assert mtf["gate_positive_populated_folds_ge_2_of_3"] == {
        "threshold": 2, "populated_folds": 0, "value": 0, "margin": -2}
    assert mtf["gate_fold_positive_share_le_0_50"]["margin"] == \
        pytest.approx(-0.5, abs=1e-9)  # share 1.0 (single populated-label fold)
    assert mtf["gate_mdd_le_2500_usd"]["margin"] == pytest.approx(2397.0, abs=1e-9)
    assert mtf["gate_pair_concentration_le_0_40"]["value"] == \
        pytest.approx(0.5, abs=1e-6)
    assert mtf["gate_pair_concentration_le_0_40"]["margin"] == \
        pytest.approx(-0.1, abs=1e-9)
    assert mtf["gate_usd_drift_abs_corr_le_0_30"]["evaluated"] is False
    assert mtf["gate_usd_drift_abs_corr_le_0_30"]["margin"] is None
    # dropouts: excluding USD/JPY leaves [97, -103] (not survived) and the
    # fold drop leaves an empty book (not survived); the other six pair
    # drops keep a positive book (survived)
    assert mtf["gate_dropout_survival_ge_6_of_8"]["value"] == 6
    assert mtf["gate_dropout_survival_ge_6_of_8"]["margin"] == 0
    assert mtf["gate_incremental_alpha_gt_0"]["value"] is None
    assert mtf["gate_incremental_alpha_gt_0"]["margin"] is None
    assert mtf["gate_decisions_ge_40"]["margin"] == 3 - 40
    # break-even bps: mean gross (+100,-100,+100 => 100/3 USD) over 2 sides
    assert rec["break_even_cost_bps"] == pytest.approx(100.0 / 3.0 / 2.0,
                                                       abs=1e-6)
    gates, reasons = F.stage_a_gates(rec)
    assert gates is False
    for expected in ("DECISION_FLOOR_NOT_MET",
                     "FEWER_THAN_2_POSITIVE_POPULATED_FOLDS",
                     "POSITIVE_FOLD_SHARE_ABOVE_50PCT",
                     "PAIR_CONCENTRATION_ABOVE_40PCT"):
        assert expected in reasons
    # pf 1.88 >= 1.10 and dropout 6-of-8: those two gates correctly absent
    assert "PF_BELOW_1.10" not in reasons
    assert "DROPOUT_SURVIVAL_BELOW_6_OF_8" not in reasons


def test_margin_to_fail_alpha_and_exit_side_purge():
    # benchmark expectancy feeds the incremental-alpha margin; an exit
    # inside the 14-day pre-boundary window is purge-excluded
    decs = _hand_decisions()
    fin = [{"decision_id": d["decision_id"], "financing_adjustment_usd": 0.0,
            "formula": F.FINANCING_FORMULA_ID} for d in decs]
    rec = F.assemble_cell_record(decs, fin, arm="anchor",
                                 benchmark_expectancy=91.0 / 6.0)
    mtf = rec["margin_to_fail"]
    # alpha = anchor expectancy - benchmark expectancy = 91/3 - 91/6 = 91/6
    assert mtf["gate_incremental_alpha_gt_0"]["value"] == \
        pytest.approx(91.0 / 6.0, abs=1e-9)
    # t2 exits 2020-07-15, far from any boundary: NOT purge-excluded;
    # swap t2 to an entry 2022-04-11 (decision Fri 2022-04-08) with an exit
    # 7 days before the 2022-05-01 boundary: purge-excluded on the exit side
    decs2 = [dict(decs[0]), dict(decs[1]), dict(decs[2])]
    decs2[1] = dict(decs2[1], decision_ts="2022-04-08T20:00:00+00:00",
                    entry_bar_ts="2022-04-11T20:00:00+00:00",
                    exit_bar_ts="2022-04-24T20:00:00+00:00")
    fin2 = [dict(f) for f in fin]
    rec2 = F.assemble_cell_record(decs2, fin2, arm="anchor")
    assert rec2["purge_excluded_exit_side"] == 1
    assert rec2["n_trades_kept"] == 3
    assert rec2["base"]["trades"] == 2  # only the non-purged trades score


def test_kernel_fold_semantics_mirrored():
    # fold_of mirrors the kernel exactly (warmup region + entry-side purge)
    assert F.fold_of("2020-02-20T20:00:00+00:00") is None  # warmup region
    assert F.fold_of("2020-03-05T20:00:00+00:00") is None  # entry-side purge
    assert F.fold_of("2020-03-15T20:00:00+00:00") == 0
    assert F.fold_of("2022-05-10T20:00:00+00:00") is None  # entry-side purge
    assert F.fold_of("2022-05-20T20:00:00+00:00") == 1
    assert F.fold_of("2024-08-01T20:00:00+00:00") == 2
    assert F.fold_of("2027-01-01T00:00:00+00:00") is None


# ------------------------------------------------------------------ #
# schedule-only replay                                                #
# ------------------------------------------------------------------ #
def test_schedule_counts_no_pnl(tmp_path):
    days = month_weekdays(2021, 5) + month_weekdays(2021, 6)
    rows = baseline_rows() + [
        rc_row("US", "2021-06-02", 0.50, 0.75, "2021-06-01T18:00:00Z"),
        rc_row("AU", "2021-06-02", 0.10, 0.15, "2021-06-01T04:30:00Z"),
    ]
    dp = make_env(tmp_path, rows, days)
    counts = F.schedule_counts(dp)
    assert counts["no_pnl"] is True
    assert counts["events_used"] == 2
    # anchor: US event -> 7 pair-candidates, AU -> 1
    assert counts["per_arm_decision_counts"]["anchor"]["total"] == 8
    # control: US -> 1 (USD/CHF), AU -> 1 (GBP/USD)
    assert counts["per_arm_decision_counts"]["control"]["total"] == 2


# ------------------------------------------------------------------ #
# run_arm contract hygiene                                            #
# ------------------------------------------------------------------ #
def test_run_arm_rejects_unknown_arms_and_shapes(tmp_path):
    days = month_weekdays(2021, 6)
    dp = make_env(tmp_path, baseline_rows(), days)
    with pytest.raises(ValueError):
        F.run_arm("not-an-arm", dp)
    with pytest.raises(F.DataBlocked):
        F.run_arm("anchor", "not-a-mapping")


def test_real_ledger_semantics_smoke_against_pinned_counts():
    """SHAPE-ONLY check against the pinned v2 ledger when it is staged in
    this worktree: deduped counts and availability-field presence.  No PnL,
    no prices, no outcomes."""
    ledger = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                          "research", "control", "forex_free_v4_run",
                          "announcement_ledger.jsonl")
    ledger = os.path.abspath(ledger)
    if not os.path.exists(ledger):
        pytest.skip("pinned v2 announcement ledger not staged in this worktree")
    rows = F.load_ledger_rows(ledger)
    deduped = F.dedupe_ledger_rows(rows)
    extracted = F.extract_events(deduped)
    assert len(rows) == 220
    assert len(deduped) == 159
    assert extracted["zero_delta_rows"] == 0
    assert len(extracted["events"]) == 151
    assert extracted["unavailable"] == []  # every RATE_CHANGE row carries a stamp
    from collections import Counter
    areas = Counter(e["area"] for e in extracted["events"])
    assert areas == {"AU": 25, "NZ": 25, "CA": 22, "GB": 22, "US": 22,
                     "EMU": 19, "CH": 11, "JP": 5}
    reader = F.LedgerVintageReader(deduped)
    # a US rate is never read before its own effective instant (the frozen
    # reader invariant) even though its availability stamp precedes it
    assert reader.policy_rate("US", datetime(2019, 7, 31, 12, 0, tzinfo=UTC)) \
        == pytest.approx(2.375)
    assert reader.policy_rate("US", datetime(2019, 8, 1, 0, 0, tzinfo=UTC)) \
        == pytest.approx(2.125)
    # A1 adjudication A-2 alignment on the PINNED rows: every event's
    # eligibility instant is its precomputed first_readable_decision_utc,
    # never before the effective instant, always a 16:00-NY instant; the
    # pre-effective announcement class (availability < effective, e.g.
    # every US INSTANT row) becomes eligible only at/after the effective
    # instant.  EXACTLY ONE pinned row (CA eff 2020-03-27, COVID era)
    # carries a SATURDAY-stamped first_readable (2020-03-28T20:00Z); the
    # frozen rule handles it fail-safe -- no completed 16:00-NY flat bar
    # exists that day, so the decision lands on the first EXISTING weekday
    # decision bar at/after the stamp (Mon 2020-03-30).
    rows_by_key = {(r["area"], r.get("effective_date")): r
                   for r in deduped if r.get("row_type") == "RATE_CHANGE"}
    ca = [e for e in extracted["events"] if e["area"] == "CA"]
    assert len(ca) == 22
    assert any(e["effective_date"] == "2020-03-27"
               and e["eligible_dt"] == datetime.fromisoformat(
                   "2020-03-28T20:00:00+00:00") for e in ca)
    for ev in extracted["events"]:
        row = rows_by_key[(ev["area"], ev["effective_date"])]
        assert ev["eligible_dt"] == datetime.fromisoformat(
            row["first_readable_decision_utc"].replace("Z", "+00:00"))
        assert ev["eligible_dt"] >= ev["effective_dt"]
        local = ev["eligible_dt"].astimezone(NY)
        assert local.hour == 16 and local.minute == 0
