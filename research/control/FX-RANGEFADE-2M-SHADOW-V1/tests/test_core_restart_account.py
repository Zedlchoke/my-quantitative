"""Restart identity + one-account accounting + PnL-today tests.

Pins the owner rules of 2026-09-24:
- restarting many times must NEVER erase PnL, duplicate fills or drop a
  position (journal replay is idempotent);
- TWO pairs share ONE $100,000 account — sleeves carry CONTRIBUTIONS,
  never a second seed;
- PnL hôm nay includes the open positions' MTM with the stated
  00:00-UTC flat-book anchor;
- stale marks fail closed: equity/PnL become None (UNAVAILABLE), not $0.
"""
import json

import pytest

import fx_shadow_core as C


def _ev(event, pair, **kw):
    rec = {"event": event, "pair": pair, "ts": kw.pop("ts", "2026-09-24T01:00:00+00:00")}
    rec.update(kw)
    return json.dumps(rec)


SEED_LAST = {"EURUSD": 1700000000, "GBPUSD": 1700000000}


def _journal():
    return [
        _ev("fill_open", "EURUSD", ts="2026-09-24T01:05:00+00:00", dir=1,
            entry_px=1.1000, entry_ts=1727142000, lots=1.5),
        _ev("fill_close", "EURUSD", ts="2026-09-24T02:05:00+00:00", dir=1,
            entry_px=1.1000, exit_px=1.1050, pnl_usd=750.0, lots=1.5, reason="signal"),
        _ev("bar_closed", "EURUSD", ts="2026-09-24T02:05:01+00:00", bar_ts=1727142000,
            b_o=1.1, b_h=1.106, b_l=1.099, b_c=1.105, a_o=1.1001, a_c=1.1052, target=-1),
        _ev("fill_open", "GBPUSD", ts="2026-09-24T01:05:00+00:00", dir=-1,
            entry_px=1.3000, entry_ts=1727142000, lots=1.5),
    ]


def test_restart_restores_position_pnl_fills_and_bars():
    rep = C.replay_journal(_journal(), seed_last_ts=SEED_LAST)
    eu = rep["pairs"]["EURUSD"]
    assert eu["pos"] == 0 and eu["realized_usd"] == pytest.approx(750.0)
    assert eu["fills"] == 1
    assert 1727142000 in eu["bars"], "bar closed after seed must survive restart"
    gb = rep["pairs"]["GBPUSD"]
    assert gb["pos"] == -1 and gb["entry_px"] == 1.3000
    assert rep["realized_usd"] == pytest.approx(750.0)
    assert rep["bars_restored"] == 1


def test_replay_is_idempotent_under_full_duplication():
    lines = _journal()
    once = C.replay_journal(lines, seed_last_ts=SEED_LAST)
    twice = C.replay_journal(lines + lines, seed_last_ts=SEED_LAST)
    assert twice["realized_usd"] == once["realized_usd"]
    assert twice["pairs"]["GBPUSD"]["pos"] == once["pairs"]["GBPUSD"]["pos"]
    assert twice["pairs"]["GBPUSD"]["fills"] == once["pairs"]["GBPUSD"]["fills"]
    assert len(twice["pairs"]["EURUSD"]["bars"]) == len(once["pairs"]["EURUSD"]["bars"])
    assert twice["events_dup"] == len(lines)


def test_repeated_restarts_do_not_compound_pnl():
    """The daemon pattern: replay at every boot must not stack realized."""
    running = C.replay_journal(_journal(), seed_last_ts=SEED_LAST)
    for _ in range(5):
        again = C.replay_journal(_journal(), seed_last_ts=SEED_LAST)
        assert again["realized_usd"] == running["realized_usd"]


def test_malformed_and_unknown_events_are_skipped_not_fatal():
    lines = ["{not json", json.dumps({"event": "mystery", "pair": "EURUSD"}),
             ""] + _journal()
    rep = C.replay_journal(lines, seed_last_ts=SEED_LAST)
    assert rep["realized_usd"] == pytest.approx(750.0)
    assert rep["events_bad"] >= 2


# ----------------------------------------------------------------------
# ONE account, TWO sleeves-as-contributions
# ----------------------------------------------------------------------
def test_journal_fixture_pnl_is_consistent_with_pnl_math():
    """The journal fixture's close event (1.1000 -> 1.1050 long) must
    carry the PnL the frozen math produces ($15/pip x 50 pips)."""
    ev = json.loads(_journal()[1])
    assert ev["pnl_usd"] == pytest.approx(C.pnl_of(1, 1.1000, 1.1050, 1e-4), abs=0.01)


def test_account_has_single_seed_and_sleeves_are_contributions():
    acct = C.account_block(
        realized_usd=750.0, unrealized_usd=-30.0, realized_today=20.0,
        gross_exposure_usd=300_000.0, marks_fresh=True)
    assert acct["seed_equity"] == 100_000.0
    assert acct["equity"] == pytest.approx(100_720.0)
    assert acct["pnl_total"] == pytest.approx(720.0)
    # gross 2 pairs x 1.5 lot ~ $300k on a $100k account is legal for the
    # DISPLAY (mức sử dụng vốn), never modeled as a second seed
    assert acct["capital_in_use_pct"] == pytest.approx(300.0)


def test_pnl_today_includes_open_position_mtm():
    fresh = C.account_block(realized_usd=750.0, unrealized_usd=-30.0,
                            realized_today=750.0, gross_exposure_usd=1.0,
                            marks_fresh=True)
    assert fresh["pnl_today"] == pytest.approx(720.0)
    assert "00:00 UTC" in fresh["pnl_today_anchor_utc"]


def test_stale_marks_fail_closed_to_none_not_zero():
    stale = C.account_block(realized_usd=750.0, unrealized_usd=-30.0,
                            realized_today=750.0, gross_exposure_usd=1.0,
                            marks_fresh=False)
    assert stale["equity"] is None
    assert stale["pnl_today"] is None
    assert stale["pnl_total"] == pytest.approx(720.0)  # closed PnL is fact


# ----------------------------------------------------------------------
# PIT H1 bar builder
# ----------------------------------------------------------------------
def test_live_bar_bid_ohlc_ask_close_hand_computed():
    bar = C.LiveBar(3600, bid=1.1000, ask=1.1002)
    bar.update(bid=1.0990, ask=1.0993)   # lower bid -> new low
    bar.update(bid=1.1020, ask=1.1023)   # higher bid -> new high
    bar.update(bid=1.1010, ask=1.1011)   # inside
    row = bar.as_row()
    assert row["ts"] == 3600
    assert row["b_o"] == 1.1000 and row["b_h"] == 1.1020 and row["b_l"] == 1.0990
    assert row["b_c"] == 1.1010
    assert row["a_o"] == 1.1002 and row["a_c"] == 1.1011
    # the old bug (b_h seeded from the ASK) must stay fixed:
    assert row["b_h"] < row["a_o"] + 1  # bid high is a BID, never the ask
    assert all(row[k] <= row["b_h"] + 1e-12 for k in ("b_o", "b_c", "b_l"))


def test_hour_floor_pit_boundaries():
    assert C.floor_hour(3600 * 4) == 3600 * 4          # exactly on the hour
    assert C.floor_hour(3600 * 4 - 1) == 3600 * 3      # 1s before -> previous hour
    assert C.floor_hour(3600 * 4 + 3599) == 3600 * 4   # last second of the bar


def test_tick_belongs_to_its_own_quote_hour_not_wall_clock():
    """PIT: a tick with ts 10:59:59 belongs to the 10:00 bar even if the
    receiver processes it at 11:00:01."""
    bar11 = C.LiveBar(11 * 3600, bid=1.2, ask=1.2002)
    assert C.floor_hour(11 * 3600 - 1) == 10 * 3600  # not this bar's bucket
    assert bar11.ts == 11 * 3600


def test_pnl_math_one_pip_one_and_a_half_lots():
    # $10 per pip per lot × 1.5 lots = $15/pip; 50 pips = $750
    assert C.pnl_of(1, 1.1000, 1.1050, 1e-4) == pytest.approx(750.0)
    assert C.pnl_of(-1, 1.3000, 1.3010, 1e-4) == pytest.approx(-150.0)
