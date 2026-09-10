"""FOREX-FREE-V2 family1 (FXFV2-A4-P1) evidence tests.

Synthetic-fixture evidence for the frozen module
research/assets/forex_free_v2/family1.py, per the required evidence list:
hand-calculated feature goldens, an end-to-end long+short golden booked
through the accounting kernel, PIT/one-event-lag mutation tests, DST mapping,
forced-flat, missing-bar fail-closed, determinism, governor caps,
drop-one-pair independence, distinct arm digests, dummy publication refusal,
and the REAL-SNAPSHOT schedule-only frequency audit (counts only, NO PnL).
"""
from __future__ import annotations

import datetime as _dt
import json
import os
from zoneinfo import ZoneInfo

import pytest

from research.assets.forex_free_v1 import td_loader
from research.assets.forex_free_v2 import family1
from research.assets.forex_free_v2.accounting import (
    PositionBook,
    trades_from_fills,
    turnover_from_fills,
)
from research.assets.forex_free_v2.data_authority import (
    SNAPSHOT_DATA_ROOT,
    flat_bar_instant_utc,
    parse_stamp,
)
from tests.assets.forex_free_v2 import goldens_family1 as G
from tests.assets.forex_free_v2.fixtures_family1 import bar as mk_bar

UTC = _dt.timezone.utc


def _rows_by_pair(rows: list[dict], *pairs: str) -> dict[str, list[dict]]:
    return {pair: [dict(r) for r in rows] for pair in pairs}


def _replace_bar(rows: list[dict], day: str, hour: int,
                 ohlc: tuple[float, float, float, float]) -> list[dict]:
    """Return a copy of ``rows`` with the bar stamped {day} {hour}:00Z replaced."""
    stamp_prefix = f"{day} {hour:02d}:00"
    out = []
    for r in rows:
        if r["datetime"].startswith(stamp_prefix):
            out.append(mk_bar(_dt.date.fromisoformat(day), hour, ohlc))
        else:
            out.append(dict(r))
    return out


def _drop_bar(rows: list[dict], day: str, hour: int) -> list[dict]:
    stamp_prefix = f"{day} {hour:02d}:00"
    return [dict(r) for r in rows if not r["datetime"].startswith(stamp_prefix)]


# ------------------------------------------------------------------------------ #
# 1. hand-calculated feature goldens
# ------------------------------------------------------------------------------ #
def test_01_feature_goldens_tokyo_range_median_compression_quartile_midpoint():
    rows = G.e2e_world()
    sessions = family1.tokyo_sessions(rows)

    # Tokyo session geometry of the 2025-06-03 trade day:
    # 9 envelope bars, high=T_H=1.1015, low=T_L=1.0985 (07Z/08Z are the
    # inside-dead bars of the London head and never widen the range)
    jun3 = sessions[_dt.date(2025, 6, 3)]
    assert jun3["t_high"] == G.GOLDEN_JUN3_STATE["t_high"]          # max(high) = 1.1015
    assert jun3["t_low"] == G.GOLDEN_JUN3_STATE["t_low"]            # min(low)  = 1.0985
    # range = max(high) - min(low) = 1.1015 - 1.0985 = 0.0030 (float-exact
    # subtraction carries ~1e-16 noise; the comparison is exact to 1e-15)
    assert jun3["range"] == pytest.approx(G.GOLDEN_JUN3_STATE["tokyo_range"], abs=1e-15)
    assert jun3["mid"] == G.GOLDEN_JUN3_STATE["mid"]                # (1.1015+1.0985)/2 = 1.1000

    # trailing 20 sessions strictly before the day, within 30 calendar days
    feats = family1.state_features(rows, _dt.date(2025, 6, 3), "anchor")
    assert feats is not None
    assert len(feats["trailing_ranges"]) == 20
    assert feats["median20"] == pytest.approx(G.GOLDEN_JUN3_STATE["median20"], abs=1e-15)
    assert feats["q20"] == pytest.approx(G.GOLDEN_JUN3_STATE["q20"], abs=1e-15)
    assert feats["compressed"] is G.GOLDEN_JUN3_STATE["compressed_anchor"]
    # 0.0030 < 0.75 * 0.0050 = 0.00375 (strict)

    # 2025-06-10 golden day: anchor NOT compressed, neighbour compressed, control = anchor
    a10 = family1.state_features(rows, _dt.date(2025, 6, 10), "anchor")
    n10 = family1.state_features(rows, _dt.date(2025, 6, 10), "neighbour")
    c10 = family1.state_features(rows, _dt.date(2025, 6, 10), "control")
    assert a10["tokyo_range"] == pytest.approx(G.GOLDEN_JUN10_STATE["tokyo_range"], abs=1e-15)
    assert a10["median20"] == pytest.approx(G.GOLDEN_JUN10_STATE["median20"], abs=1e-15)
    assert a10["q20"] == pytest.approx(G.GOLDEN_JUN10_STATE["q20"], abs=1e-15)
    assert a10["compressed"] is G.GOLDEN_JUN10_STATE["compressed_anchor"]    # 0.0044 >= 0.00375
    assert n10["compressed"] is G.GOLDEN_JUN10_STATE["compressed_neighbour"]  # 0.0044 < 0.0050
    assert c10["compressed"] is G.GOLDEN_JUN10_STATE["compressed_control"]

    # trailing-window bounds: 21 valid sessions in [D-30, D); most recent 20 used
    day = _dt.date(2025, 6, 10)
    inside = [d for d in sessions if day - _dt.timedelta(days=30) <= d < day]
    assert len(inside) == 21
    assert a10["day"] == day

    # incomplete Tokyo session / short history fail closed
    assert family1.state_features(_drop_bar(rows, "2025-06-03", 3),
                                  _dt.date(2025, 6, 3), "anchor") is None
    assert family1.state_features(rows[:100], _dt.date(2025, 6, 3), "anchor") is None


# ------------------------------------------------------------------------------ #
# 2. end-to-end golden: one LONG + one SHORT, booked through the kernel
# ------------------------------------------------------------------------------ #
def test_02_e2e_long_and_short_golden_booked_through_accounting_kernel():
    schedule = family1.compute_arm_schedule("anchor", {"EUR/USD": G.e2e_world()},
                                            cost_tier=1.0)
    assert schedule["family_id"] == "family1"
    assert schedule["proposal_id"] == "FXFV2-A4-P1"
    assert schedule["arm"] == "anchor"
    assert schedule["cost_tier"] == 1.0
    assert len(schedule["trades"]) == 2
    assert schedule["trades"][0] == G.E2E_ANCHOR_LONG
    assert schedule["trades"][1] == G.E2E_ANCHOR_SHORT
    # decisions: only compressed days evaluate the trigger (Jun 3 + Jun 5)
    assert schedule["decisions"] == G.E2E_ANCHOR_DECISIONS
    # 30 scanned weekdays = 20 warmup days (fewer than 20 trailing sessions,
    # fail-closed) + 8 evaluable-but-not-compressed + 2 traded
    assert schedule["no_trade_days"]["trailing_state_unavailable"] == G.E2E_WARMUP_DAYS
    assert schedule["no_trade_days"]["not_in_compression_state"] == G.E2E_NOT_COMPRESSED
    assert sum(schedule["no_trade_days"].values()) + 2 == G.E2E_DATES
    assert schedule["warmup_first_evaluable_date"] == "2025-06-03"
    # no PnL fields anywhere in the schedule
    assert not any("pnl" in k.lower() or "profit" in k.lower() or "cost" in k.lower()
                   for t in schedule["trades"] for k in t)

    # book the schedule through the frozen accounting kernel (side +1 LONG / -1 SHORT)
    book = PositionBook()
    for t in schedule["trades"]:
        book.open_position(trade_id=t["trade_id"], pair=t["pair"],
                           side="LONG" if t["side"] == 1 else "SHORT",
                           notional_usd=t["notional_usd"], price=t["entry_price"],
                           ts_utc=t["entry_ts"], cost_tier=1.0)
        book.close_position(t["trade_id"], t["exit_price"], t["exit_ts"])
    closed = book.closed_trades
    assert len(closed) == 2
    assert closed[0].pnl_usd == G.LONG_PNL      # 10000 * (1.1012/1.1016 - 1)
    assert closed[0].net_pnl_usd == G.LONG_NET  # LONG_PNL - 1.50 - 1.50
    assert closed[1].pnl_usd == G.SHORT_PNL     # -10000 * (1.0989/1.0982 - 1)
    assert closed[1].net_pnl_usd == G.SHORT_NET
    assert book.pnl_usd_total == G.TOTAL_GROSS
    assert book.total_cost_usd == G.TOTAL_COST  # 4 fills x 1.50
    assert book.net_usd_total == G.TOTAL_NET
    assert turnover_from_fills(book.fills)["total_notional_usd"] == 40000.0  # 4 x 10000
    assert trades_from_fills(book.fills)["round_trips"] == 2


# ------------------------------------------------------------------------------ #
# 3. completed-bar PIT + one-event lag (mutation tests)
# ------------------------------------------------------------------------------ #
def test_03_pit_one_event_lag_mutations():
    base_rows = G.e2e_world()
    base = family1.compute_arm_schedule("anchor", {"EUR/USD": base_rows})
    base_long = base["trades"][0]
    assert base_long["decision_ts"] == "2025-06-03T09:00:00Z"
    assert base_long["entry_ts"] == "2025-06-03T10:00:00Z"

    # (a) a bar AFTER the exit (15Z, exit was at 14Z) must not change anything
    rows_a = _replace_bar(base_rows, "2025-06-03", 15, (1.1000, 1.1002, 1.0948, 1.0950))
    sched_a = family1.compute_arm_schedule("anchor", {"EUR/USD": rows_a})
    assert sched_a["schedule_digest"] == base["schedule_digest"]

    # (b) the ENTRY bar's close (known only after the decision) never feeds the
    #     decision: entry/decision identical; it only drives the lagged exit.
    rows_b = _replace_bar(base_rows, "2025-06-03", 10, (1.1016, 1.1022, 1.0988, 1.0990))
    sched_b = family1.compute_arm_schedule("anchor", {"EUR/USD": rows_b})
    t_b = sched_b["trades"][0]
    assert t_b["decision_ts"] == base_long["decision_ts"]
    assert t_b["entry_ts"] == base_long["entry_ts"]
    assert t_b["entry_price"] == base_long["entry_price"]
    assert (t_b["exit_ts"], t_b["exit_price"], t_b["exit_reason"]) == \
        ("2025-06-03T11:00:00Z", 1.1019, "invalidation")   # entry-bar close -> NEXT open

    # (c) a mid-hold close (12Z) triggers invalidation -> exit at the NEXT open
    rows_c = _replace_bar(base_rows, "2025-06-03", 12, (1.1017, 1.1018, 1.1010, 1.1005))
    sched_c = family1.compute_arm_schedule("anchor", {"EUR/USD": rows_c})
    t_c = sched_c["trades"][0]
    assert t_c["decision_ts"] == base_long["decision_ts"]
    assert t_c["entry_ts"] == base_long["entry_ts"]
    assert (t_c["exit_ts"], t_c["exit_price"]) == ("2025-06-03T13:00:00Z", 1.1016)

    # (d) control: mutating the decision bar itself DOES move the decision
    #     (09Z no longer breaches; 10Z fires; entry shifts one event later)
    rows_d = _replace_bar(base_rows, "2025-06-03", 9, (1.1010, 1.1014, 1.1005, 1.1012))
    sched_d = family1.compute_arm_schedule("anchor", {"EUR/USD": rows_d})
    t_d = sched_d["trades"][0]
    assert (t_d["decision_ts"], t_d["entry_ts"], t_d["entry_price"]) == \
        ("2025-06-03T10:00:00Z", "2025-06-03T11:00:00Z", 1.1019)


# ------------------------------------------------------------------------------ #
# 4. DST mapping (US 2025-03-09 spring / 2025-11-02 fall; EU 03-30 / 10-26)
# ------------------------------------------------------------------------------ #
@pytest.mark.parametrize("case", G.DST_CASES,
                         ids=[str(c[0]) for c in G.DST_CASES])
def test_04_dst_london_window_and_16ny_flat_map(case):
    last_day, decision_ts, entry_ts, entry_px, exit_ts, exit_px = case
    schedule = family1.compute_arm_schedule("anchor", {"EUR/USD": G.dst_world(last_day)})
    assert len(schedule["trades"]) == 1
    t = schedule["trades"][0]
    assert t["decision_ts"] == decision_ts
    assert t["entry_ts"] == entry_ts
    assert t["entry_price"] == entry_px
    assert t["exit_ts"] == exit_ts
    assert t["exit_price"] == exit_px
    assert t["exit_reason"] == "forced_flat"
    # the exit instant is exactly the 16:00 New York bar open of the entry day
    entry_day = _dt.datetime.strptime(entry_ts, "%Y-%m-%dT%H:%M:%SZ").date()
    assert parse_stamp(t["exit_ts"], "exit") == flat_bar_instant_utc(entry_day)
    # position never held at/after 17:00 New York (exit at the 16:00 NY open)
    exit_instant = parse_stamp(t["exit_ts"], "exit")
    rollover = _dt.datetime.combine(entry_day, _dt.time(17, 0),
                                    tzinfo=ZoneInfo("America/New_York"))
    assert exit_instant < rollover.astimezone(UTC)


# ------------------------------------------------------------------------------ #
# 5. forced flat at the 16:00 NY bar open; never held into the rollover
# ------------------------------------------------------------------------------ #
def test_05_forced_flat_and_early_forced_flat():
    # (a) flat bar present: exit at its OPEN (20:00Z = 16:00 NY EDT)
    sched = family1.compute_arm_schedule("anchor", {"EUR/USD": G.forced_flat_world(True)})
    t = sched["trades"][0]
    assert (t["exit_ts"], t["exit_price"], t["exit_reason"]) == G.FF_EXIT_EDT
    assert t["entry_ts"] == "2025-06-03T10:00:00Z"
    assert t["entry_price"] == 1.1016
    # 30 weekdays in the world (Apr 23..Jun 3) = 20 warmup days (fewer than 20
    # trailing sessions) + 9 evaluable-but-not-compressed + 1 traded
    assert sched["no_trade_days"]["trailing_state_unavailable"] == 20
    assert sched["no_trade_days"]["not_in_compression_state"] == 9
    assert sched["decisions"] == 1

    # (b) flat bar absent -> frozen fallback: exit at the OPEN of the
    #     immediately preceding existing H1 bar (19:00Z), still before 17:00 NY
    sched_e = family1.compute_arm_schedule("anchor", {"EUR/USD": G.forced_flat_world(False)})
    t_e = sched_e["trades"][0]
    assert (t_e["exit_ts"], t_e["exit_price"], t_e["exit_reason"]) == G.FF_EXIT_EARLY

    # (c) flat bar absent AND no existing bar after the entry => no flat exit
    #     available that day => NO_TRADE (void entry, decision counted)
    sched_u = family1.compute_arm_schedule("anchor", {"EUR/USD": G.flat_unavailable_world()})
    assert sched_u["trades"] == []
    assert sched_u["decisions"] == 1
    assert sched_u["no_trade_days"]["flat_exit_unavailable"] == 1


# ------------------------------------------------------------------------------ #
# 6. missing bars: state / London window / entry -- never fill-forward
# ------------------------------------------------------------------------------ #
def test_06_missing_bar_fail_closed():
    base_rows = G.forced_flat_world(True)
    day = "2025-06-03"

    # (a) missing Tokyo bar (03:00Z) => state NOT evaluated that day
    sched = family1.compute_arm_schedule("anchor", {"EUR/USD": _drop_bar(base_rows, day, 3)})
    assert sched["trades"] == []
    assert sched["decisions"] == 0
    assert sched["no_trade_days"]["tokyo_session_incomplete"] == 1

    # (b) missing London window bar (10:00Z BST -- in the window, NOT in the
    #     Tokyo session) => NO_TRADE, no decision
    sched_w = family1.compute_arm_schedule("anchor", {"EUR/USD": _drop_bar(base_rows, day, 10)})
    assert sched_w["trades"] == []
    assert sched_w["decisions"] == 0
    assert sched_w["no_trade_days"]["london_window_incomplete"] == 1

    # (c) missing TRIGGER bar (09:00Z): the window is invalid even though the
    #     10:00Z bar exists => no trade, never fill-forward
    sched_t = family1.compute_arm_schedule("anchor", {"EUR/USD": _drop_bar(base_rows, day, 9)})
    assert sched_t["trades"] == []
    assert sched_t["decisions"] == 0
    assert sched_t["no_trade_days"]["london_window_incomplete"] == 1

    # (d) missing ENTRY bar: decision at 10Z (09Z mutated to a non-firing bar,
    #     10Z fires), the entry slot 11Z is outside the window and missing =>
    #     decision counted (go), entry voided
    no_fire_9 = _replace_bar(base_rows, day, 9, (1.1010, 1.1014, 1.1005, 1.1012))
    sched_e = family1.compute_arm_schedule(
        "anchor", {"EUR/USD": _drop_bar(no_fire_9, day, 11)})
    assert sched_e["trades"] == []
    assert sched_e["decisions"] == 1
    assert sched_e["no_trade_days"]["entry_bar_missing"] == 1


# ------------------------------------------------------------------------------ #
# 7. determinism
# ------------------------------------------------------------------------------ #
def test_07_determinism_identical_digests():
    rows = {"EUR/USD": G.e2e_world()}
    again = {"EUR/USD": G.e2e_world()}
    a = family1.compute_arm_schedule("anchor", rows)
    b = family1.compute_arm_schedule("anchor", again)
    assert a == b
    assert a["schedule_digest"] == b["schedule_digest"]
    world = _rows_by_pair(G.arms_differ_world(), "EUR/USD")
    for arm in family1.ARMS:
        s1 = family1.compute_arm_schedule(arm, world)
        s2 = family1.compute_arm_schedule(arm, world)
        assert s1["schedule_digest"] == s2["schedule_digest"]


# ------------------------------------------------------------------------------ #
# 8. governor caps: 1 entry/pair/UTC-day, 3 RT/pair/week (cap-binding case)
# ------------------------------------------------------------------------------ #
def test_08_governor_daily_structural_and_weekly_cap_binding():
    # (a) second same-day break never re-enters (daily cap is structural)
    sched = family1.compute_arm_schedule("anchor", {"EUR/USD": G.second_break_world()})
    assert len(sched["trades"]) == 1
    t = sched["trades"][0]
    assert (t["entry_ts"], t["exit_ts"], t["exit_price"]) == (
        G.SECOND_BREAK_TRADE["entry_ts"], G.SECOND_BREAK_TRADE["exit_ts"],
        G.SECOND_BREAK_TRADE["exit_price"])

    # (b) five compressed days in one UTC week: exactly 3 trades, Thu/Fri dropped
    sched_w = family1.compute_arm_schedule("anchor", {"EUR/USD": G.governor_week_world()})
    assert len(sched_w["trades"]) == G.GOV_TRADES
    assert [t["entry_ts"][:10] for t in sched_w["trades"]] == G.GOV_ENTRY_DAYS
    assert sched_w["decisions"] == G.GOV_DECISIONS
    assert sched_w["no_trade_days"]["governor_week_cap"] == G.GOV_CAPPED_DAYS
    # independent cap verification from the emitted trades
    per_day: dict[tuple[str, str], int] = {}
    per_week: dict[tuple[str, _dt.date], int] = {}
    for t in sched_w["trades"]:
        day = _dt.datetime.strptime(t["entry_ts"], "%Y-%m-%dT%H:%M:%SZ").date()
        per_day[(t["pair"], day.isoformat())] = per_day.get((t["pair"], day.isoformat()), 0) + 1
        week = day - _dt.timedelta(days=day.weekday())
        per_week[(t["pair"], week)] = per_week.get((t["pair"], week), 0) + 1
    assert max(per_day.values()) <= family1.MAX_ENTRIES_PER_PAIR_PER_UTC_DAY
    assert max(per_week.values()) <= family1.MAX_ROUND_TRIPS_PER_PAIR_PER_UTC_WEEK


# ------------------------------------------------------------------------------ #
# 9. drop-one-pair: no cross-pair coupling
# ------------------------------------------------------------------------------ #
def test_09_drop_one_pair_independence():
    rows = G.e2e_world()
    full = family1.compute_arm_schedule("anchor", _rows_by_pair(rows, "EUR/USD", "GBP/USD"))
    only_gbp = family1.compute_arm_schedule("anchor", {"GBP/USD": [dict(r) for r in rows]})
    only_eur = family1.compute_arm_schedule("anchor", {"EUR/USD": [dict(r) for r in rows]})

    full_gbp = [t for t in full["trades"] if t["pair"] == "GBP/USD"]
    full_eur = [t for t in full["trades"] if t["pair"] == "EUR/USD"]
    assert full_gbp == only_gbp["trades"]
    assert full_eur == only_eur["trades"]
    assert full["decisions"] == only_gbp["decisions"] + only_eur["decisions"]
    assert full["warmup_first_evaluable_date"] == only_gbp["warmup_first_evaluable_date"]
    # schedules differ (different pair sets) but per-pair content is identical
    assert full["schedule_digest"] != only_gbp["schedule_digest"]

    # decision-day view: per-pair days independent of the other pair's presence
    dd_full = family1.arm_decision_days("anchor", _rows_by_pair(rows, "EUR/USD", "GBP/USD"))
    dd_gbp = family1.arm_decision_days("anchor", {"GBP/USD": [dict(r) for r in rows]})
    assert dd_full["decisions_by_pair"]["GBP/USD"] == dd_gbp["decisions_by_pair"]["GBP/USD"]


# ------------------------------------------------------------------------------ #
# 10. anchor / neighbour / control digests all differ where all three fire
# ------------------------------------------------------------------------------ #
def test_10_arms_distinct_digests_and_expected_trades():
    world = _rows_by_pair(G.arms_differ_world(), "EUR/USD")
    schedules = {arm: family1.compute_arm_schedule(arm, world) for arm in family1.ARMS}
    digests = {arm: s["schedule_digest"] for arm, s in schedules.items()}
    assert len(set(digests.values())) == 3

    a = schedules["anchor"]
    assert a["decisions"] == G.ARMS_EXPECTED["anchor"]["decisions"]
    assert [t["entry_ts"] for t in a["trades"]] == G.ARMS_EXPECTED["anchor"]["entries"]
    assert a["trades"][0]["entry_price"] == G.ARMS_EXPECTED["anchor"]["entry_price"]
    assert a["trades"][0]["exit_price"] == G.ARMS_EXPECTED["anchor"]["exit_price"]
    assert a["trades"][0]["exit_reason"] == G.ARMS_EXPECTED["anchor"]["exit_reason"]

    n = schedules["neighbour"]
    assert n["decisions"] == G.ARMS_EXPECTED["neighbour"]["decisions"]
    assert [t["entry_ts"] for t in n["trades"]] == G.ARMS_EXPECTED["neighbour"]["entries"]
    n10 = n["trades"][1]
    assert n10["entry_price"] == G.ARMS_EXPECTED["neighbour"]["jun10_entry_price"]
    assert n10["exit_price"] == G.ARMS_EXPECTED["neighbour"]["jun10_exit_price"]
    assert n10["exit_reason"] == G.ARMS_EXPECTED["neighbour"]["jun10_exit_reason"]

    c = schedules["control"]
    assert c["decisions"] == G.ARMS_EXPECTED["control"]["decisions"]
    assert [t["entry_ts"] for t in c["trades"]] == G.ARMS_EXPECTED["control"]["entries"]
    ct = c["trades"][0]
    assert ct["decision_ts"] == G.ARMS_EXPECTED["control"]["decision_ts"]
    assert ct["side"] == -1
    assert ct["entry_price"] == G.ARMS_EXPECTED["control"]["entry_price"]
    assert ct["exit_price"] == G.ARMS_EXPECTED["control"]["exit_price"]
    assert ct["exit_reason"] == G.ARMS_EXPECTED["control"]["exit_reason"]
    # the control trades the same day the anchor does but fires one bar earlier
    assert ct["decision_ts"] < a["trades"][0]["decision_ts"]


# ------------------------------------------------------------------------------ #
# 11. dummy publication refusal (no authorization => raise; flag false => refuse)
# ------------------------------------------------------------------------------ #
def test_11_publication_authorization_guard(tmp_path):
    schedule = family1.compute_arm_schedule("anchor", {"EUR/USD": G.e2e_world()})
    ledger = tmp_path / "ledger.jsonl"
    missing = tmp_path / "nope.json"
    auth_false = tmp_path / "auth_false.json"
    auth_false.write_text(json.dumps({"schema": "x", "score_authorized": False}))
    auth_true = tmp_path / "auth_true.json"
    auth_true.write_text(json.dumps({"schema": "x", "score_authorized": True}))

    # no authorization file => raises (dry-run or not)
    with pytest.raises(family1.PublicationNotAuthorized):
        family1.publish_schedule_once(schedule, str(ledger), str(missing))
    with pytest.raises(family1.PublicationNotAuthorized):
        family1.publish_schedule_once(schedule, str(ledger), str(missing), dry_run=True)

    # authorization file that does not grant scoring => raises
    with pytest.raises(family1.PublicationNotAuthorized):
        family1.publish_schedule_once(schedule, str(ledger), str(auth_false))

    # score-authorized=false dummy flag: publish REFUSED; dry-run reports without writing
    status = family1.publish_schedule_once(schedule, str(ledger), str(auth_true),
                                           score_authorized=False, dry_run=True)
    assert status["status"] == "REFUSED_SCORE_NOT_AUTHORIZED"
    assert status["written"] is False and status["dry_run"] is True
    with pytest.raises(family1.PublicationNotAuthorized):
        family1.publish_schedule_once(schedule, str(ledger), str(auth_true),
                                      score_authorized=False, dry_run=False)
    assert not ledger.exists()          # nothing was ever written

    # fully authorized: once-only publication of the digest summary (no PnL)
    published = family1.publish_schedule_once(schedule, str(ledger), str(auth_true),
                                              score_authorized=True)
    assert published["status"] == "PUBLISHED" and published["written"] is True
    lines = ledger.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["schedule_digest"] == schedule["schedule_digest"]
    assert not any("pnl" in k.lower() for k in record)
    replay = family1.publish_schedule_once(schedule, str(ledger), str(auth_true),
                                           score_authorized=True)
    assert replay["published_now"] == 0          # idempotent once-only replay
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 1


# ------------------------------------------------------------------------------ #
# 13. cost-tier semantics: tier 2.0 delays every fill by one event; 1.5 is cost-only
# ------------------------------------------------------------------------------ #
def test_13_tier_fill_delay_semantics():
    world = G.e2e_world()
    t1 = family1.compute_arm_schedule("anchor", {"EUR/USD": world}, cost_tier=1.0)
    t15 = family1.compute_arm_schedule("anchor", {"EUR/USD": world}, cost_tier=1.5)
    t2 = family1.compute_arm_schedule("anchor", {"EUR/USD": world}, cost_tier=2.0)

    # tier 1.5 changes the recorded tier only -- the emitted trades are identical
    # (the digest payload correctly includes cost_tier, so only trades are compared)
    assert t15["cost_tier"] == 1.5
    assert t15["trades"] == t1["trades"]
    assert t15["decisions"] == t1["decisions"]
    assert t15["schedule_digest"] != t1["schedule_digest"]

    # tier 2.0 delays each fill one extra event, recomputing the schedule:
    # long: decision 09Z -> entry 11Z @1.1019; 13Z close 1.1010 < T_H triggers
    # invalidation -> fill 15Z @1.1000 (still strictly before the 20Z flat)
    # short: decision 09Z -> entry 11Z @1.0981; 13Z close 1.0987 > T_L -> 15Z @1.1000
    assert t2["schedule_digest"] != t1["schedule_digest"]
    assert t2["cost_tier"] == 2.0
    assert len(t2["trades"]) == 2
    long2, short2 = t2["trades"]
    assert (long2["entry_ts"], long2["entry_price"]) == \
        (G.TIER2_LONG["entry_ts"], G.TIER2_LONG["entry_price"])
    assert (long2["exit_ts"], long2["exit_price"], long2["exit_reason"]) == \
        (G.TIER2_LONG["exit_ts"], G.TIER2_LONG["exit_price"], G.TIER2_LONG["exit_reason"])
    assert long2["decision_ts"] == t1["trades"][0]["decision_ts"]  # decision unchanged
    assert (short2["entry_ts"], short2["entry_price"]) == \
        (G.TIER2_SHORT["entry_ts"], G.TIER2_SHORT["entry_price"])
    assert (short2["exit_ts"], short2["exit_price"], short2["exit_reason"]) == \
        (G.TIER2_SHORT["exit_ts"], G.TIER2_SHORT["exit_price"], G.TIER2_SHORT["exit_reason"])
    # tier-2 entries remain strictly before the forced-flat instant of the day
    for t in t2["trades"]:
        day = _dt.datetime.strptime(t["entry_ts"], "%Y-%m-%dT%H:%M:%SZ").date()
        assert parse_stamp(t["entry_ts"], "entry") < flat_bar_instant_utc(day)

    # invalid cost tiers fail closed
    with pytest.raises(ValueError):
        family1.compute_arm_schedule("anchor", {"EUR/USD": world}, cost_tier=1.1)
    with pytest.raises(ValueError):
        family1.compute_arm_schedule("anchor", {"EUR/USD": world}, cost_tier="1.0")


# ------------------------------------------------------------------------------ #
# 14. REAL-SNAPSHOT schedule-only frequency audit (counts only, NO PnL)
# ------------------------------------------------------------------------------ #
FOLD_BOUNDS = (
    (_dt.date(2020, 3, 1), _dt.date(2022, 5, 2)),   # F1
    (_dt.date(2022, 5, 2), _dt.date(2024, 7, 2)),   # F2
    (_dt.date(2024, 7, 2), _dt.date(2026, 9, 3)),   # F3 (proposal end 2026-09-02 incl.)
)


def _load_snapshot() -> dict[str, list[dict]]:
    rows_by_pair = {}
    for pair in td_loader.PAIRS:
        rows, _quarantined = td_loader.load_pair_h1(pair, SNAPSHOT_DATA_ROOT)
        rows_by_pair[pair] = rows
    return rows_by_pair


def test_14_real_snapshot_frequency_audit_schedule_only(tmp_path):
    if not os.path.isdir(SNAPSHOT_DATA_ROOT):
        pytest.skip(f"read-only V1 snapshot not present: {SNAPSHOT_DATA_ROOT}")
    rows_by_pair = _load_snapshot()
    assert set(rows_by_pair) == set(td_loader.PAIRS)

    per_arm = {}
    for arm in family1.ARMS:
        schedule = family1.compute_arm_schedule(arm, rows_by_pair, cost_tier=1.0)
        dd = family1.arm_decision_days(arm, rows_by_pair, cost_tier=1.0)
        # module consistency: decisions == total per-pair decision days
        assert schedule["decisions"] == dd["decisions"]
        assert schedule["decisions"] == sum(len(v) for v in dd["decisions_by_pair"].values())

        trades = schedule["trades"]
        per_day: dict[tuple[str, str], int] = {}
        per_week: dict[tuple[str, _dt.date], int] = {}
        fold_trades = [0, 0, 0]
        for t in trades:
            day = _dt.datetime.strptime(t["entry_ts"], "%Y-%m-%dT%H:%M:%SZ").date()
            per_day[(t["pair"], day.isoformat())] = per_day.get((t["pair"], day.isoformat()), 0) + 1
            week = day - _dt.timedelta(days=day.weekday())
            per_week[(t["pair"], week)] = per_week.get((t["pair"], week), 0) + 1
            for fi, (lo, hi) in enumerate(FOLD_BOUNDS):
                if lo <= day < hi:
                    fold_trades[fi] += 1
                    break

        # frozen schedule caps (frequency contract)
        assert max(per_day.values()) <= family1.MAX_ENTRIES_PER_PAIR_PER_UTC_DAY
        assert max(per_week.values()) <= family1.MAX_ROUND_TRIPS_PER_PAIR_PER_UTC_WEEK

        # decision floors (proposal minimum_decisions) from decision days
        fold_decisions: dict[tuple[str, int], int] = {}
        pair_total: dict[str, int] = {}
        for pair, days in dd["decisions_by_pair"].items():
            pair_total[pair] = len(days)
            for d in days:
                day = _dt.date.fromisoformat(d)
                for fi, (lo, hi) in enumerate(FOLD_BOUNDS):
                    if lo <= day < hi:
                        key = (pair, fi)
                        fold_decisions[key] = fold_decisions.get(key, 0) + 1
                        break
        assert min(fold_decisions.values()) >= 80     # per_pair_per_fold_minimum
        assert min(pair_total.values()) >= 300        # per_pair_full_sample_minimum

        # trade-cell floors (proposal minimum_trades_per_cell)
        assert len(trades) >= 1200                    # full_sample_aggregate_minimum
        assert min(fold_trades) >= 400                # per_fold_aggregate_minimum
        assert schedule["warmup_first_evaluable_date"] is not None

        per_arm[arm] = {
            "decisions": schedule["decisions"],
            "trades": len(trades),
            "fold_trades": fold_trades,
            "min_decisions_pair_fold": min(fold_decisions.values()),
            "min_decisions_pair_full": min(pair_total.values()),
            "max_entries_pair_utc_day": max(per_day.values()),
            "max_rt_pair_week": max(per_week.values()),
            "pair_weeks_at_cap3": sum(1 for v in per_week.values() if v == 3),
            "first_evaluable": schedule["warmup_first_evaluable_date"],
        }

    # audit-side record (ephemeral; counts only, never PnL) -- the persisted
    # counts live in research/control/forex_free_v2_run/lane_report_family1.json
    audit_path = tmp_path / "_family1_frequency_audit.json"
    with open(audit_path, "w", encoding="utf-8") as handle:
        json.dump({"schema": "forex_free_v2_family1_frequency_audit_v1",
                   "scope": "REAL-SNAPSHOT schedule-only counts; NO PnL computed or stored",
                   "arms": per_arm}, handle, indent=2, sort_keys=True)
    assert audit_path.exists()
