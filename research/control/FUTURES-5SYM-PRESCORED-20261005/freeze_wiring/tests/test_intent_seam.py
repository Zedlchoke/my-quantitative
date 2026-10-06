"""test_intent_seam — the REAL intent-execution seam (wave-4 WIRING-FIX).

Path under test (production seam):
  wired_intent@1 records -> wiring/intent_executor.build_intent_run
    (intent_packet@1: per-intent direction/signal/entry/exit/exit_reason
     VERBATIM; folds/warmup/calendar law from the SPEC packet)
  -> exec/scored_runner_v2.py intent-mode engine (compute_intents — SAME
     accounting/twin/ledger/publication/authority path as the positional
     encoding)
  -> append-only ledger (one TRIAL per identity; per-trade journal inside).

Defect fixed here (synth/ERRATUM_2_WIRING_CLAIMS.md +
freeze_wiring/repro_mixed_direction/REPRO_FAIL.json): the positional seam
dropped same-identity mixed-direction/extra legs. These tests prove EVERY
wired intent executes as ITS OWN trade, with SPEC law (folds, warmup,
calendar, roll identity routing, tick era, quote direction, costs,
SL-priority, horizon, session close) flowing into execution, and the
authority/denominator laws preserved.

SYNTHETIC fixtures only; sandbox authority only; no real data, no
governance writes, no scored outcome exists.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from conftest import CYCLE_DIR, PY
import panel_fixtures as pf
from wiring import intent_executor as ie
from wiring import spec_compiler as sc
from wiring.intent_contract import normalize_intent

TOL = 1e-6
EPOCH = "2026-10-05T00:00:00Z"


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "scored_runner_v2_intent_tests",
        str(CYCLE_DIR / "exec" / "scored_runner_v2.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RUNNER = _load_runner()


# ----------------------------------------------------------------- helpers

def weekdays(start: str, n: int) -> list[str]:
    out, d = [], date.fromisoformat(start)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def sessions_for(dates: list[str], px: float = 100.0) -> list[dict]:
    """The execution TIMELINE: one bar per session date. In intent mode the
    engine consumes the dates (fold/warmup/exclusion law); fill prices come
    from the intent records — the OHLC here is deliberately neutral."""
    return [{"session_date": d, "open": px, "high": px, "low": px,
             "close": px} for d in dates]


def mk(iid, sym, direction, entry, exit_, entry_px, exit_px, *,
       reason="horizon", signal=None, tier="S2", stress=1.0,
       source="freeze_wiring/tests/test_intent_seam", prov="SYNTHETIC"):
    return normalize_intent(
        identity_id=iid, symbol=sym, family="SEAM-TEST", direction=direction,
        entry_date=entry, exit_date=exit_, entry_price=entry_px,
        exit_price=exit_px, cost_tier=tier, stress=stress,
        source_adapter=source, provenance=prov, signal_ts=signal,
        exit_reason=reason)


def run(intents_or_groups, sessions, tmp_path, label, *, folds=None,
        warmup=0, excluded=None, horizons=None, anchors=None, tiers=None,
        stresses=None, cost_law=None, calibrated_era=None, gov_kwargs=None,
        test_fault=None):
    folds = folds or [{"fold_id": "F1", "start_bar": 0,
                       "end_bar": len(sessions)}]
    if intents_or_groups and isinstance(intents_or_groups[0], dict) and \
            "schema" in intents_or_groups[0]:
        groups = ie.group_intents(intents_or_groups, horizons=horizons,
                                  zero_trade_identities=anchors,
                                  cost_tiers=tiers, stresses=stresses)
    else:
        groups = intents_or_groups
    return ie.intent_and_run(
        groups, sessions, folds=folds, work_dir=str(tmp_path / label),
        run_label=label, warmup_bars=warmup,
        calendar_excluded_dates=excluded,
        cost_usd_law=cost_law or dict(sc.DEFAULT_COST_USD_LAW),
        calibrated_era=calibrated_era, epoch=EPOCH, gov_kwargs=gov_kwargs or {},
        test_fault=test_fault, python=PY)


def canonical(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False)
            + "\n").encode("utf-8")


# ------------------------------------------------- T-MD1 mixed directions

def test_tmd1_mixed_direction_same_identity_both_execute(tmp_path):
    """REPRO case: ONE identity, Long then Short — BOTH trades execute with
    their own direction/timestamps/PnL; ledger TRIAL accounting: one
    identity row, executed count 2; observed denominator +1 identity (not
    +2). This is the exact defect class of REPRO_FAIL.json."""
    iid = "FBNQ1-F1-CONT-UP-D0-S2"
    days = weekdays("2023-06-12", 4)               # 06-12..06-15
    intents = [
        mk(iid, "NQ", 1, days[1], days[1], 15110.0, 15130.0,
           reason="session_close"),                # Long  06-14
        mk(iid, "NQ", -1, days[2], days[2], 15110.0, 15090.0,
           reason="session_close"),                # Short 06-15
    ]
    res = run(intents, sessions_for(days), tmp_path, "tmd1")
    assert res["exit_code"] == 0, (res["final_status"], res["stderr"])
    assert res["final_status"]["status"] == "EXECUTION_COMPLETE"
    trials = res["trials"]
    assert len(trials) == 1                        # ONE identity row
    assert trials[0]["identity_id"] == iid
    assert trials[0]["counts_observed"] is True
    rec = trials[0]["payload"]
    assert rec["mode"] == "intent"
    assert rec["totals"]["n_trades"] == 2          # executed count 2
    journal = rec["journal"]
    assert [t["direction"] for t in journal] == [1, -1]
    assert [t["entry_ts"] for t in journal] == [days[1], days[2]]
    assert [t["exit_ts"] for t in journal] == [days[1], days[2]]
    for t in journal:                              # per-trade PnL exact
        assert abs(t["net_pnl_usd"] - 343.0) < TOL
    assert res["final_status"]["observed_identity_count"] == 1  # +1, not +2
    assert not [r for r in res["ledger_rows"]
                if r["row_type"] == "DUPLICATE_RETRY"]
    fold_row = [r for r in res["ledger_rows"] if r["row_type"] == "FOLD"][0]
    assert fold_row["payload"]["n_trades"] == 2
    # the ordering and both legs are also in the LEDGER payload itself
    led_journal = trials[0]["payload"]["journal"]
    assert [t["intent_seq"] for t in led_journal] == [0, 1]


# ------------------------------------------------- T-MD2 same-day ordering

def test_tmd2_same_day_trades_ordering_and_timestamps(tmp_path):
    """Multiple trades the same day: timestamps + submission ordering
    preserved exactly in journal AND ledger."""
    iid = "SEAM-MD2"
    days = weekdays("2023-06-12", 4)
    intents = [
        mk(iid, "NQ", 1, days[1], days[1], 15110.0, 15120.0,
           reason="session_close"),
        mk(iid, "NQ", 1, days[1], days[3], 15110.0, 15150.0,
           reason="horizon"),
        mk(iid, "NQ", -1, days[2], days[2], 15120.0, 15100.0,
           reason="stop_loss"),
    ]
    res = run(intents, sessions_for(days), tmp_path, "tmd2",
              horizons={iid: 2})
    assert res["exit_code"] == 0, (res["final_status"], res["stderr"])
    journal = res["journal"][iid]
    assert [t["intent_seq"] for t in journal] == [0, 1, 2]
    assert [(t["entry_ts"], t["exit_ts"]) for t in journal] == \
        [(days[1], days[1]), (days[1], days[3]), (days[2], days[2])]
    assert [t["exit_reason"] for t in journal] == \
        ["session_close", "horizon", "stop_loss"]
    assert [t["entry_bar"] for t in journal] == [1, 1, 2]
    assert [t["exit_bar"] for t in journal] == [1, 3, 2]
    # ledger carries the identical journal (byte-equal payloads)
    led = res["trials"][0]["payload"]["journal"]
    assert canonical(led) == canonical(journal)


# --------------------------------------------- T-MD3 per-arm horizon/exit

def test_tmd3_arms_own_horizons_and_exit_reasons(tmp_path):
    """D0 vs D30M arms exit at their own horizons; one arm exits via
    same-bar SL (SL-priority) and one via session close — each journal's
    exit_reason correct."""
    d0, d30 = "SEAM-MD3-D0", "SEAM-MD3-D30M"
    days = weekdays("2023-06-12", 5)
    groups = [
        {"identity_id": d0, "symbol": "NQ", "cost_tier": "S2",
         "stress": 1.0, "holding_horizon_bars": 1,
         "intents": [mk(d0, "NQ", 1, days[1], days[1], 15110.0, 15125.0,
                        reason="session_close")]},
        {"identity_id": d30, "symbol": "NQ", "cost_tier": "S2",
         "stress": 1.0, "holding_horizon_bars": 2,
         "intents": [
             mk(d30, "NQ", 1, days[1], days[3], 15110.0, 15150.0,
                reason="horizon"),
             mk(d30, "NQ", -1, days[2], days[2], 15120.0, 15100.0,
                reason="stop_loss")]},
    ]
    res = run(groups, sessions_for(days), tmp_path, "tmd3")
    assert res["exit_code"] == 0, (res["final_status"], res["stderr"])
    j0, j30 = res["journal"][d0], res["journal"][d30]
    # D0 arm: same-session close, its own (short) horizon
    assert len(j0) == 1
    assert j0[0]["exit_reason"] == "session_close"
    assert j0[0]["exit_ts"] == j0[0]["entry_ts"] == days[1]
    assert j0[0]["exit_bar"] == j0[0]["entry_bar"]
    # D30M arm: horizon exit exactly at entry+2 bars; SL closes same-bar
    assert [t["exit_reason"] for t in j30] == ["horizon", "stop_loss"]
    assert j30[0]["entry_bar"] == 1 and j30[0]["exit_bar"] == 3
    assert j30[0]["exit_ts"] == days[3]
    assert j30[1]["entry_bar"] == j30[1]["exit_bar"] == 2
    assert j30[1]["exit_ts"] == j30[1]["entry_ts"] == days[2]
    assert len(res["trials"]) == 2                 # two identities, 2 rows


# ------------------------------------------------- T-MD4 folds + warmup

def test_tmd4_fold_boundaries_and_warmup(tmp_path):
    """Trades before warmup-252 are excluded by fold law; a trade at the
    fold seam lands in EXACTLY one fold; folds come from the packet, not
    F-COMPILED."""
    iid = "SEAM-MD4"
    days = weekdays("2022-01-03", 300)
    folds = [{"fold_id": "F1", "start_bar": 252, "end_bar": 276},
             {"fold_id": "F2", "start_bar": 276, "end_bar": 300}]
    intents = [
        mk(iid, "NQ", 1, days[100], days[101], 15110.0, 15120.0),  # warmup
        mk(iid, "NQ", 1, days[275], days[276], 15110.0, 15120.0),  # F1
        mk(iid, "NQ", -1, days[276], days[277], 15120.0, 15100.0),  # F2 seam
    ]
    res = run(intents, sessions_for(days), tmp_path, "tmd4", folds=folds,
              warmup=252, horizons={iid: 1})
    assert res["exit_code"] == 0, (res["final_status"], res["stderr"])
    rec = res["trials"][0]["payload"]
    assert rec["totals"]["n_trades"] == 2
    assert rec["totals"]["n_excluded"] == 1
    excl = rec["excluded_intents"]
    assert len(excl) == 1 and excl[0]["reason"] == "warmup"
    assert excl[0]["intent_seq"] == 0 and excl[0]["entry_bar"] == 100
    journal = rec["journal"]
    assert [t["fold_id"] for t in journal] == ["F1", "F2"]   # seam: exactly 1
    assert journal[0]["entry_bar"] == 275 and journal[1]["entry_bar"] == 276
    folds_by_id = {f["fold_id"]: f for f in rec["folds"]}
    assert folds_by_id["F1"]["n_trades"] == 1
    assert folds_by_id["F2"]["n_trades"] == 1
    assert folds_by_id["F1"]["trades"][0]["intent_seq"] == 1
    assert folds_by_id["F2"]["trades"][0]["intent_seq"] == 2
    assert folds_by_id["F1"]["trades"][0]["net_pnl_usd"] != \
        folds_by_id["F2"]["trades"][0]["net_pnl_usd"]  # short flips the sign
    fold_rows = {r["payload"]["fold_id"]: r["payload"]
                 for r in res["ledger_rows"] if r["row_type"] == "FOLD"}
    assert fold_rows["F1"]["n_trades"] == 1 and \
        fold_rows["F2"]["n_trades"] == 1


# ------------------------------------------------- T-MD5 boundaries

def test_tmd5_calendar_roll_era_and_quote_boundaries(tmp_path):
    """Session/calendar/roll/tick-era/quote-direction laws flow from the
    SPEC into execution."""
    # (a) calendar-excluded day produces NO trade (run still succeeds)
    iid_a = "SEAM-MD5-CAL"
    days = weekdays("2023-06-12", 5)
    intents = [
        mk(iid_a, "NQ", 1, days[2], days[2], 15110.0, 15130.0,
           reason="session_close"),                 # excluded day
        mk(iid_a, "NQ", 1, days[3], days[3], 15110.0, 15130.0,
           reason="session_close"),                 # executes
    ]
    res = run(intents, sessions_for(days), tmp_path, "tmd5a",
              excluded=[days[2]])
    assert res["exit_code"] == 0, (res["final_status"], res["stderr"])
    rec = res["trials"][0]["payload"]
    assert rec["totals"]["n_trades"] == 1
    assert rec["totals"]["n_excluded"] == 1
    assert rec["excluded_intents"][0]["reason"] == "calendar_excluded"
    assert rec["excluded_intents"][0]["entry_ts"] == days[2]
    assert rec["journal"][0]["entry_ts"] == days[3]

    # (b) roll-week session routes to the POST-roll contract identity
    pre, post = "SEAM-MD5-ROLL-PRE", "SEAM-MD5-ROLL-POST"
    rdays = weekdays("2023-06-12", 6)
    roll_day = rdays[3]
    groups = [
        {"identity_id": pre, "symbol": "NQ", "cost_tier": "S2",
         "stress": 1.0, "holding_horizon_bars": 1,
         "intents": [mk(pre, "NQ", 1, rdays[1], rdays[2], 15110.0, 15120.0)]},
        {"identity_id": post, "symbol": "NQ", "cost_tier": "S2",
         "stress": 1.0, "holding_horizon_bars": 1,
         "intents": [mk(post, "NQ", 1, roll_day, rdays[4], 15150.0,
                        15160.0)]},
    ]
    res = run(groups, sessions_for(rdays), tmp_path, "tmd5b")
    assert res["exit_code"] == 0
    assert [t["entry_ts"] for t in res["journal"][pre]] == [rdays[1]]
    assert [t["entry_ts"] for t in res["journal"][post]] == [roll_day]
    assert roll_day not in [t["entry_ts"] for t in res["journal"][pre]]

    # (c) 6A era boundary: $10/tick era-1 vs $5/tick era-2 on ENTRY date;
    #     era-2-calibrated cost model refuses era-1 entries
    days_6a = weekdays("2020-11-16", 10)           # 11-16..11-27
    iid_6a = "SEAM-MD5-6A-ERA"
    groups = [{"identity_id": iid_6a, "symbol": "6A", "cost_tier": "S2",
               "stress": 1.0, "holding_horizon_bars": 1,
               "intents": [
                   mk(iid_6a, "6A", 1, days_6a[3], days_6a[4],
                      0.6550, 0.6600),            # era-1 entry 2020-11-19
                   mk(iid_6a, "6A", 1, days_6a[6], days_6a[7],
                      0.65500, 0.66000)]}]        # era-2 entry 2020-11-24
    res = run(groups, sessions_for(days_6a), tmp_path, "tmd5c")
    assert res["exit_code"] == 0, (res["final_status"], res["stderr"])
    j6a = res["journal"][iid_6a]
    assert [t["era"] for t in j6a] == ["6A-era1", "6A-era2"]
    assert [t["tick_value_usd"] for t in j6a] == [10.0, 5.0]
    assert [t["tick_size"] for t in j6a] == [0.0001, 0.00005]
    assert abs(j6a[0]["gross_pnl_usd"] - 500.0) < TOL
    assert abs(j6a[1]["gross_pnl_usd"] - 500.0) < TOL   # factor invariant
    # era-1-calibrated ticks on each entry era's tick value:
    assert abs(j6a[0]["cost_usd"] - 57.0) < TOL
    assert abs(j6a[1]["cost_usd"] - 30.75) < TOL
    with pytest.raises(sc.CompileRefusal) as ei:    # era-2 model vs era-1
        run(groups, sessions_for(days_6a), tmp_path, "tmd5c_refuse",
            calibrated_era="6A-era2")
    assert ei.value.code == "REFUSED_COMPILE_COST_ERA_MISMATCH"
    assert ei.value.exit_code == 41

    # (d) 6J quote direction: yen-STRENGTHENING (quoted USD-per-JPY number
    #     RISING) makes the long book POSITIVE; the short mirrors negative.
    jdays = weekdays("2023-09-04", 2)
    jl, js = "SEAM-MD5-6J-LONG", "SEAM-MD5-6J-SHORT"
    groups = [
        {"identity_id": jl, "symbol": "6J", "cost_tier": "S2", "stress": 1.0,
         "holding_horizon_bars": 1,
         "intents": [mk(jl, "6J", 1, jdays[0], jdays[1],
                        0.006550, 0.006575)]},
        {"identity_id": js, "symbol": "6J", "cost_tier": "S2", "stress": 1.0,
         "holding_horizon_bars": 1,
         "intents": [mk(js, "6J", -1, jdays[0], jdays[1],
                        0.006550, 0.006575)]},
    ]
    res = run(groups, sessions_for(jdays), tmp_path, "tmd5d",
              cost_law=dict(pf.COST_LAW_6J))
    assert res["exit_code"] == 0, (res["final_status"], res["stderr"])
    assert res["journal"][jl][0]["net_pnl_usd"] > 0
    assert res["journal"][js][0]["net_pnl_usd"] < 0


# ------------------------------------------------- T-MD6 zero-trade anchor

def test_tmd6_zero_trade_identity_processed(tmp_path):
    """A declared anchor with zero intents is a legitimate processed
    outcome: executed-count-0 TRIAL row, run succeeds, denominator per law
    (the identity counts as observed — processed, never not-run)."""
    iid = "SEAM-MD6-TRADER"
    anchor = "SEAM-MD6-ALW-ANCHOR"
    days = weekdays("2023-06-12", 4)
    intents = [mk(iid, "NQ", 1, days[1], days[1], 15110.0, 15130.0,
                  reason="session_close")]
    res = run(intents, sessions_for(days), tmp_path, "tmd6",
              anchors=[{"identity_id": anchor, "symbol": "NQ",
                        "holding_horizon_bars": 1}],
              tiers={anchor: "S2"}, stresses={anchor: 1.0})
    assert res["exit_code"] == 0, (res["final_status"], res["stderr"])
    assert res["final_status"]["status"] == "EXECUTION_COMPLETE"
    trials = {t["identity_id"]: t for t in res["trials"]}
    assert set(trials) == {iid, anchor}
    arec = trials[anchor]["payload"]
    assert arec["totals"]["n_trades"] == 0
    assert arec["journal"] == []
    assert arec["n_intents_declared"] == 0
    assert arec["folds"] and all(f["n_trades"] == 0 for f in arec["folds"])
    assert trials[anchor]["counts_observed"] is True
    assert res["final_status"]["observed_identity_count"] == 2
    pub = json.loads((tmp_path / "tmd6" / "runs" / "tmd6" /
                      "published_summary.json").read_text())
    assert pub["published_identity_count"] == 2
    assert sorted(pub["published_identity_ids"]) == sorted([iid, anchor])


# ------------------------------------- T-MD7 independent reference parity

CONTRACTS_DOC = json.loads(
    (CYCLE_DIR / "exec" / "symbol_contracts.json").read_text())

# SPEC cost law, transcribed here from the frozen cost-manifest constants
# (spec_compiler.DEFAULT_COST_USD_LAW text: per-side fee + USD spread/slip
# ladders) — NOT imported from executor code. The per-case tables are passed
# from the same literals the runs use (DEFAULT_COST_USD_LAW / COST_LAW_6J),
# and ref_net() itself contains only contract-SPEC arithmetic.
SPEC_COST_USD = {"fee_all_in_usd": 2.25, "spread_usd": 16.25,
                 "slip_usd_by_tier": {"S1": 5.00, "S2": 10.00, "S3": 15.00}}


def _era_of(sym: str, d: str) -> dict:
    rows = sorted(CONTRACTS_DOC["contracts"][sym]["era_table"],
                  key=lambda r: r["effective_from"])
    chosen = rows[0]
    for r in rows:
        if r["effective_from"] <= d:
            chosen = r
    return chosen


def ref_net(sym: str, entry_date: str, direction: int, entry_px: float,
            exit_px: float, *, tier: str = "S2", stress: float = 1.0,
            cost_usd: dict | None = None) -> float:
    """INDEPENDENT reference: contract-SPEC arithmetic —
    gross = direction * (exit - entry) * tick_value/tick_size of the ENTRY
    era; cost_side = fee + (spread_usd + slip_usd) * stress (per side,
    applied twice). Written from the SPEC text; imports no executor code."""
    cost_usd = cost_usd or SPEC_COST_USD
    era = _era_of(sym, entry_date)
    tick, tval = float(era["tick_size"]), float(era["tick_value_usd"])
    gross = direction * (exit_px - entry_px) * (tval / tick)
    side = cost_usd["fee_all_in_usd"] + stress * (
        cost_usd["spread_usd"] + cost_usd["slip_usd_by_tier"][tier])
    return round(gross - 2.0 * side, 6)


def test_tmd7_reference_parity_seven_cases(tmp_path):
    """Executor output == independent CONTRACT-SPEC arithmetic for 7 covering
    cases: both directions, both 6A eras, a 6J trade, an SL exit, and a 6E
    case; plus positional-vs-intent accounting parity on the single-trade
    case (the accounting-reuse proof)."""
    cases = [
        # (label, sym, dir, entry, exit_px, reason, cost_law)
        ("NQ-long", "NQ", 1, 15110.0, 15130.0, "horizon",
         dict(sc.DEFAULT_COST_USD_LAW)),
        ("NQ-short", "NQ", -1, 15110.0, 15090.0, "horizon",
         dict(sc.DEFAULT_COST_USD_LAW)),
        ("6A-era1-long", "6A", 1, 0.6550, 0.6600, "horizon",
         dict(sc.DEFAULT_COST_USD_LAW)),
        ("6A-era2-long", "6A", 1, 0.65500, 0.66000, "horizon",
         dict(sc.DEFAULT_COST_USD_LAW)),
        ("6J-long", "6J", 1, 0.006550, 0.006575, "horizon",
         dict(pf.COST_LAW_6J)),
        ("NQ-long-SL", "NQ", 1, 15110.0, 15100.0, "stop_loss",
         dict(sc.DEFAULT_COST_USD_LAW)),
        ("6E-short", "6E", -1, 1.08100, 1.08050, "horizon",
         dict(sc.DEFAULT_COST_USD_LAW)),
    ]
    entry_dates = {
        "NQ": weekdays("2023-06-12", 3),           # entry 06-13, exit 06-14
        "6A": weekdays("2020-11-16", 10),
        "6J": weekdays("2023-09-04", 2),
        "6E": weekdays("2023-06-12", 3),
    }
    for n, (label, sym, direction, epx, xpx, reason, cost_law) in \
            enumerate(cases):
        if sym == "6A":
            ed, xd = entry_dates["6A"][3], entry_dates["6A"][4]   # era-1
            if label.endswith("era2-long"):
                ed, xd = entry_dates["6A"][6], entry_dates["6A"][7]
        else:
            ed, xd = entry_dates[sym][0], entry_dates[sym][1]
        iid = f"SEAM-MD7-{label}"
        intents = [mk(iid, sym, direction, ed, xd, epx, xpx, reason=reason)]
        res = run(intents, sessions_for(entry_dates[sym]), tmp_path,
                  f"md7_{n}", cost_law=cost_law)
        assert res["exit_code"] == 0, (label, res["final_status"],
                                       res["stderr"])
        trade = res["journal"][iid][0]
        want = ref_net(sym, ed, direction, epx, xpx,
                       cost_usd=cost_law and {
                           "fee_all_in_usd": cost_law["fee_all_in_usd"],
                           "spread_usd": cost_law["spread_usd"],
                           "slip_usd_by_tier": cost_law["slip_usd_by_tier"]})
        assert abs(trade["net_pnl_usd"] - want) < TOL, \
            (label, trade["net_pnl_usd"], want)
        assert trade["direction"] == direction
        assert trade["era"] == _era_of(sym, ed)["era"]
        assert trade["exit_reason"] == reason

    # accounting-reuse parity on the single-trade case: the positional
    # encoding and the intent seam price the SAME declared trade identically.
    days = entry_dates["NQ"]
    iid = "SEAM-MD7-PARITY"
    intent = mk(iid, "NQ", 1, days[0], days[1], 15110.0, 15130.0)
    pos = sc.compile_and_run([intent], str(tmp_path / "parity_pos"),
                             run_label="p", epoch=EPOCH, python=PY)
    assert pos["exit_code"] == 0
    pos_net = pos["trials"][0]["payload"]["folds"][0]["trades"][0][
        "net_pnl_usd"]
    seam = run([intent], sessions_for(days), tmp_path, "parity_seam")
    seam_net = seam["journal"][iid][0]["net_pnl_usd"]
    assert abs(pos_net - seam_net) < TOL
    assert abs(seam_net - ref_net("NQ", days[0], 1, 15110.0, 15130.0)) < TOL


# --------------------------------------------- T-MD8 PIT prefix replay

def test_tmd8_pit_prefix_replay_byte_identical(tmp_path):
    """Replaying the panel/intent prefix [0..T] then the full panel produces
    identical completed trades up to T — byte-identical journal prefix."""
    iid = "SEAM-MD8"
    days = weekdays("2023-06-01", 10)              # d0..d9
    intents = [
        mk(iid, "NQ", 1, days[1], days[2], 15110.0, 15120.0),
        mk(iid, "NQ", 1, days[4], days[4], 15120.0, 15130.0,
           reason="session_close"),
        mk(iid, "NQ", -1, days[7], days[8], 15130.0, 15100.0),
    ]
    full = run(intents, sessions_for(days), tmp_path, "md8_full",
               horizons={iid: 1})
    assert full["exit_code"] == 0
    full_journal = full["journal"][iid]
    assert len(full_journal) == 3

    T = 7                                          # prefix = bars [0..7]
    prefix_days = days[:T + 1]
    prefix_intents = [i for i in intents
                      if i["exit_date"] <= prefix_days[-1]]  # fully resolved
    assert len(prefix_intents) == 2
    prefix = run(prefix_intents, sessions_for(prefix_days), tmp_path,
                 "md8_prefix", folds=[{"fold_id": "F1", "start_bar": 0,
                                       "end_bar": len(prefix_days)}],
                 horizons={iid: 1})
    assert prefix["exit_code"] == 0
    prefix_journal = prefix["journal"][iid]
    assert len(prefix_journal) == 2
    assert canonical(prefix_journal) == \
        canonical(full_journal[:len(prefix_journal)]), \
        "PIT law violated: prefix replay differs from the full replay"


# ----------------------------------------- T-MD9 retry idempotency

def test_tmd9_mixed_direction_retry_idempotent(tmp_path):
    """Re-submitting the same 2-intent mixed-direction group against the
    same ledger: no duplicate trades, identity/denominator unchanged, no
    recompute of terminal state."""
    iid = "SEAM-MD9"
    days = weekdays("2023-06-12", 4)
    intents = [
        mk(iid, "NQ", 1, days[1], days[1], 15110.0, 15130.0,
           reason="session_close"),
        mk(iid, "NQ", -1, days[2], days[2], 15110.0, 15090.0,
           reason="session_close"),
    ]
    work = str(tmp_path / "md9")
    folds = [{"fold_id": "F1", "start_bar": 0, "end_bar": len(days)}]
    r1 = ie.intent_and_run(ie.group_intents(intents), sessions_for(days),
                           folds=folds, work_dir=work, run_label="first",
                           epoch=EPOCH, python=PY)
    assert r1["exit_code"] == 0, (r1["final_status"], r1["stderr"])
    assert len(r1["trials"]) == 1
    ledger_after_1 = (Path(work) / "trial_ledger.jsonl").read_bytes()

    r2 = ie.intent_and_run(ie.group_intents(intents), sessions_for(days),
                           folds=folds, work_dir=work, run_label="retry",
                           epoch=EPOCH, python=PY)
    assert r2["exit_code"] == 0, (r2["final_status"], r2["stderr"])
    dups = [r for r in r2["ledger_rows"]
            if r["row_type"] == "DUPLICATE_RETRY"]
    assert len(dups) == 1 and dups[0]["identity_id"] == iid
    assert dups[0]["counts_observed"] is False
    trials = [r for r in r2["ledger_rows"] if r["row_type"] == "TRIAL"]
    assert len(trials) == 1                        # no duplicate trades
    assert r2["final_status"]["observed_identity_count"] == 1
    # no recompute: the TRIAL row is byte-identical to the first run's
    assert canonical(trials[0]) == \
        canonical([r for r in r1["ledger_rows"]
                   if r["row_type"] == "TRIAL"][0])
    pub = json.loads((Path(work) / "runs" / "retry" /
                      "published_summary.json").read_text())
    assert pub["duplicate_retry_ids"] == [iid]
    assert pub["observed_identity_count"] == 1
    assert pub["published_identity_count"] == 1
    # journal inside the surviving TRIAL still holds BOTH legs
    assert trials[0]["payload"]["totals"]["n_trades"] == 2
    del ledger_after_1


# --------------------------------------------- T-MD10 failure paths

def test_tmd10_failure_paths_through_intent_seam(tmp_path):
    """Missing authority / wrong GO / registry mismatch / input drift refuse
    PRE-computation; twin mismatch never success; publication failure keeps
    observed; a finalization fault exits non-zero; non-SYNTHETIC provenance
    refuses at the wiring layer and again in the runner."""
    iid = "SEAM-MD10"
    days = weekdays("2023-06-12", 4)
    intents = [
        mk(iid, "NQ", 1, days[1], days[1], 15110.0, 15130.0,
           reason="session_close"),
        mk(iid, "NQ", -1, days[2], days[2], 15110.0, 15090.0,
           reason="session_close"),
    ]

    # -- pre-computation refusals (exit 2, no TRIAL row) -------------------
    r = run(intents, sessions_for(days), tmp_path, "md10_auth",
            gov_kwargs={"authority_valid": False})
    assert r["exit_code"] == 2
    assert r["final_status"]["refusal_code"] == "REFUSED_AUTHORITY_INVALID"
    assert not [x for x in r["ledger_rows"] if x["row_type"] == "TRIAL"]

    work = str(tmp_path / "md10_noauth")
    built = ie.intent_and_run(ie.group_intents(intents), sessions_for(days),
                              folds=[{"fold_id": "F1", "start_bar": 0,
                                      "end_bar": len(days)}],
                              work_dir=work, run_label="build", epoch=EPOCH,
                              python=PY)
    assert built["exit_code"] == 0
    gov = sc.make_sandbox_authority(str(tmp_path / "md10_noauth" / "gov2"))
    Path(gov["authority_file"]).unlink()           # missing authority
    r = sc.invoke_runner(
        input_manifest=built["compile"]["input_manifest"],
        spec_packet=built["compile"]["intent_packet"],
        cost_manifest=built["compile"]["cost_manifest"], gov=gov,
        ledger=str(tmp_path / "md10_noauth" / "l2.jsonl"),
        run_dir=str(tmp_path / "md10_noauth" / "runs2"),
        final_status_out=str(tmp_path / "md10_noauth" / "FS2.json"),
        run_label="noauth", python=PY)
    assert r["exit_code"] == 2
    assert r["final_status"]["refusal_code"] == "REFUSED_NO_AUTHORITY"

    r = run(intents, sessions_for(days), tmp_path, "md10_go",
            gov_kwargs={"go_phrase": "GO - please run it"})
    assert r["exit_code"] == 2
    assert r["final_status"]["refusal_code"] == "REFUSED_GO_PHRASE_MISMATCH"

    r = run(intents, sessions_for(days), tmp_path, "md10_reg",
            gov_kwargs={"registry_cycle_present": False})
    assert r["exit_code"] == 2
    assert r["final_status"]["refusal_code"] == "REFUSED_REGISTRY_MISMATCH"

    # input drift: a FRESH build whose frozen timeline is tampered before
    # the run — re-hash must refuse (pre-computation, zero denominator)
    drift_dir = tmp_path / "md10_drift"
    comp_d = ie.build_intent_run(
        ie.group_intents(intents), sessions_for(days),
        folds=[{"fold_id": "F1", "start_bar": 0, "end_bar": len(days)}],
        work_dir=str(drift_dir))
    tl = Path(comp_d["timeline"])
    tl.write_text(tl.read_text().replace(days[1], "1999-01-01", 1))
    r = sc.invoke_runner(
        input_manifest=comp_d["input_manifest"],
        spec_packet=comp_d["intent_packet"],
        cost_manifest=comp_d["cost_manifest"],
        gov=sc.make_sandbox_authority(str(drift_dir / "gov")),
        ledger=str(drift_dir / "l.jsonl"),
        run_dir=str(drift_dir / "runs"),
        final_status_out=str(drift_dir / "FS.json"),
        run_label="drift", python=PY)
    assert r["exit_code"] == 2
    assert r["final_status"]["refusal_code"] == "REFUSED_INPUT_DRIFT"

    # -- twin mismatch never success ----------------------------------------
    r = run(intents, sessions_for(days), tmp_path, "md10_twin",
            test_fault="force_twin_drift")
    assert r["exit_code"] == 3
    assert r["final_status"]["failure_code"] == "FAILED_TWIN_MISMATCH"
    recon = json.loads((tmp_path / "md10_twin" / "runs" / "md10_twin" /
                        "reconciliation_report.json").read_text())
    assert recon["match"] is False
    recon_text = (tmp_path / "md10_twin" / "runs" / "md10_twin" /
                  "reconciliation_report.json").read_text()
    assert "EXECUTION_COMPLETE" not in recon_text

    # -- publication failure keeps observed ----------------------------------
    r = run(intents, sessions_for(days), tmp_path, "md10_pub",
            test_fault="fail_publication")
    assert r["exit_code"] == 3
    assert r["final_status"]["failure_code"] == "FAILED_PUBLICATION"
    trials = [x for x in r["ledger_rows"] if x["row_type"] == "TRIAL"]
    assert len(trials) == 1 and \
        r["final_status"]["observed_identity_count"] == 1   # kept
    q = tmp_path / "md10_pub" / "runs" / "md10_pub" / \
        "PUBLICATION_QUARANTINE.json"
    assert q.is_file()
    assert not (tmp_path / "md10_pub" / "runs" / "md10_pub" /
                "published_summary.json").exists()

    # -- finalization fault => non-zero exit, no handoff ----------------------
    r = run(intents, sessions_for(days), tmp_path, "md10_rel",
            test_fault="fail_release")
    assert r["exit_code"] == 3
    fs = r["final_status"]
    assert fs["status"] == "FAILED"
    assert fs["failure_code"] == "FAILED_LOCK_RELEASE"
    assert fs["lock"]["released_status"] == "RELEASE_RAISED"
    assert fs["handoff_written"] is False
    assert not (tmp_path / "md10_rel" / "runs" / "md10_rel" /
                "handoff.json").exists()
    assert fs["computation_complete"] is True   # compute stood; release didn't

    # -- non-SYNTHETIC provenance: wiring layer refuses pre-computation ------
    bad = [mk(iid, "NQ", 1, days[1], days[1], 15110.0, 15130.0,
              prov="REAL_DATA")]
    with pytest.raises(sc.CompileRefusal) as ei:
        run(bad, sessions_for(days), tmp_path, "md10_prov")
    assert ei.value.code == "REFUSED_COMPILE_INTENT_INVALID"

    # -- and the runner gate holds even for a tampered packet -----------------
    comp2 = built["compile"]
    packet = json.loads(Path(comp2["intent_packet"]).read_text())
    packet["provenance"] = "REAL"
    p2 = Path(comp2["intent_packet"]).parent / "intent_packet_tampered.json"
    p2.write_bytes(canonical(packet))
    manifest = json.loads(Path(comp2["input_manifest"]).read_text())
    manifest["spec_packet_sha256"] = hashlib.sha256(p2.read_bytes()).hexdigest()
    m2 = Path(comp2["input_manifest"]).parent / "manifest_tampered.json"
    m2.write_bytes(canonical(manifest))
    r = sc.invoke_runner(
        input_manifest=str(m2), spec_packet=str(p2),
        cost_manifest=comp2["cost_manifest"],
        gov=sc.make_sandbox_authority(str(tmp_path / "md10_noauth" / "gov4")),
        ledger=str(tmp_path / "md10_noauth" / "l4.jsonl"),
        run_dir=str(tmp_path / "md10_noauth" / "runs4"),
        final_status_out=str(tmp_path / "md10_noauth" / "FS4.json"),
        run_label="prov", python=PY)
    assert r["exit_code"] == 2
    assert r["final_status"]["refusal_code"] == "REFUSED_SPEC_INVALID"
    assert "SYNTHETIC" in json.dumps(r["final_status"])

# ------------------------------------- runner-side validator laws (unit)

def test_intent_validator_fail_closed_laws():
    """Direct proofs of the intent-packet validation surface (no CLI):
    horizon window, horizon-reason exactness, fold coverage/overlap/warmup,
    duplicate bar dates, panel-membership law."""
    days = weekdays("2023-06-12", 5)
    bars = [{"ts": date.fromisoformat(d), "open": 1.0, "high": 1.0,
             "low": 1.0, "close": 1.0} for d in days]
    contracts_doc = RUNNER.load_symbol_contracts(
        str(CYCLE_DIR / "exec" / "symbol_contracts.json"))
    cost = {"fee_per_side_usd_by_tier": {"S2": 2.25},
            "spread_ticks_by_stress": {"1.0": 3.25},
            "slip_ticks_by_stress": {"1.0": 2.0}}

    def packet(**over):
        p = {"schema": "futures_5sym_prescored/intent_packet@1",
             "provenance": "SYNTHETIC", "warmup_bars": 0,
             "calendar_excluded_dates": [],
             "identities": [{"identity_id": "V1", "symbol": "NQ",
                             "cost_tier": "S2", "stress": 1.0,
                             "holding_horizon_bars": 1,
                             "intents": [
                                 {"intent_seq": 0, "direction": 1,
                                  "signal_ts": days[0], "entry_ts": days[1],
                                  "exit_ts": days[2], "entry_price": 15110.0,
                                  "exit_price": 15120.0,
                                  "exit_reason": "horizon"}]}],
             "folds": [{"fold_id": "F1", "start_bar": 0, "end_bar": 5}]}
        p.update(over)
        return p

    RUNNER.validate_intent_spec(packet(), contracts_doc, cost,
                                {"NQ": 5}, bars_by_symbol={"NQ": bars})
    with pytest.raises(RUNNER.SpecError):   # horizon reason off-by-one
        p = packet()
        p["identities"][0]["intents"][0]["exit_ts"] = days[1]
        RUNNER.validate_intent_spec(p, contracts_doc, cost, {"NQ": 5},
                                    bars_by_symbol={"NQ": bars})
    with pytest.raises(RUNNER.SpecError):   # exit beyond holding window
        p = packet()
        p["identities"][0]["holding_horizon_bars"] = 1
        p["identities"][0]["intents"][0]["exit_ts"] = days[3]
        RUNNER.validate_intent_spec(p, contracts_doc, cost, {"NQ": 5},
                                    bars_by_symbol={"NQ": bars})
    with pytest.raises(RUNNER.SpecError):   # non-SYNTHETIC provenance
        RUNNER.validate_intent_spec(packet(provenance="REAL"), contracts_doc,
                                    cost, {"NQ": 5},
                                    bars_by_symbol={"NQ": bars})
    with pytest.raises(RUNNER.SpecError):   # overlapping folds
        RUNNER.validate_intent_spec(packet(folds=[
            {"fold_id": "F1", "start_bar": 0, "end_bar": 3},
            {"fold_id": "F2", "start_bar": 2, "end_bar": 5}]), contracts_doc,
            cost, {"NQ": 5}, bars_by_symbol={"NQ": bars})
    with pytest.raises(RUNNER.SpecError):   # fold starts before warmup
        RUNNER.validate_intent_spec(packet(warmup_bars=2), contracts_doc,
                                    cost, {"NQ": 5},
                                    bars_by_symbol={"NQ": bars})
    with pytest.raises(RUNNER.SpecError):   # entry date outside panel
        p = packet()
        p["identities"][0]["intents"][0]["entry_ts"] = "2023-07-04"
        RUNNER.validate_intent_spec(p, contracts_doc, cost, {"NQ": 5},
                                    bars_by_symbol={"NQ": bars})
    with pytest.raises(RUNNER.SpecError):   # duplicate bar dates
        bad_bars = bars + [dict(bars[-1])]
        RUNNER.validate_intent_spec(packet(), contracts_doc, cost,
                                    {"NQ": 6}, bars_by_symbol={"NQ": bad_bars})


# ------------------------------- positional scope relabel (defect closed)

def test_positional_compiler_refuses_multi_intent_groups(tmp_path):
    """The positional encoding is relabeled POSITIONAL_ACCOUNTING_TEST_ONLY
    and REFUSES groups with >1 intent or mixed directions
    (REFUSED_POSITIONAL_SCOPE) — it can never again silently encode a
    multi-intent identity. Single-intent groups still compile + run, and
    the spec packet carries the encoding label."""
    iid = "FBNQ1-F1-CONT-UP-D0-S2"
    intents = [
        mk(iid, "NQ", 1, "2023-06-14", "2023-06-14", 15110.0, 15130.0,
           reason="session_close"),
        mk(iid, "NQ", -1, "2023-06-15", "2023-06-15", 15110.0, 15090.0,
           reason="session_close"),
    ]
    with pytest.raises(sc.CompileRefusal) as ei:
        sc.compile_identity_group(intents, str(tmp_path / "refused"))
    assert ei.value.code == "REFUSED_POSITIONAL_SCOPE"
    assert ei.value.exit_code == 46
    assert ei.value.detail["n_intents"] == 2
    assert ei.value.detail["directions"] == [-1, 1]

    same_dir = [mk("X1", "NQ", 1, "2023-06-14", "2023-06-14", 15110.0,
                   15130.0),
                mk("X1", "NQ", 1, "2023-06-15", "2023-06-15", 15110.0,
                   15120.0)]
    with pytest.raises(sc.CompileRefusal) as ei:
        sc.compile_identity_group(same_dir, str(tmp_path / "refused2"))
    assert ei.value.code == "REFUSED_POSITIONAL_SCOPE"

    single = [mk(iid, "NQ", 1, "2023-06-14", "2023-06-14", 15110.0, 15130.0,
                 reason="session_close")]
    comp = sc.compile_identity_group(single, str(tmp_path / "ok"))
    assert comp["encoding"] == "POSITIONAL_ACCOUNTING_TEST_ONLY"
    spec = json.loads(Path(comp["spec_packet"]).read_text())
    assert spec["encoding"] == "POSITIONAL_ACCOUNTING_TEST_ONLY"
    assert spec["identities"][0]["identity_id"] == iid
