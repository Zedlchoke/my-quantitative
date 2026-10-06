"""Per-symbol contract-law tests for scored_runner_v2.

  T17 6A era switch: a fixture crossing 2020-11-23 must produce era-1
      ($10/tick) and era-2 ($5/tick) cost rows that differ exactly per the
      era table, with the era chosen by the ENTRY bar timestamp.
  T18 6J quote direction: the CME 6J quote is USD per 1 JPY; a long position
      on a RISING quoted series must yield POSITIVE gross PnL under the
      contract's sign convention (and the JPY-per-USD misread would flip
      every sign — asserted explicitly).

All contract NUMBERS remain VERIFICATION: PLACEHOLDER-PENDING-PER-SYMBOL-
LANE (see symbol_contracts.json); these tests prove the RUNNER APPLIES the
declared numbers correctly — they do not verify the numbers themselves.
"""
from __future__ import annotations

import json

from conftest import CONTRACTS, Sandbox, default_spec


def _contract(sym):
    return json.loads(CONTRACTS and open(CONTRACTS, encoding="utf-8")
                      .read())["contracts"][sym]


def _trials_by_id(sb, label="run1"):
    rows = sb.ledger_rows()
    return {x["identity_id"]: x["payload"] for x in rows
            if x["row_type"] == "TRIAL"}


def test_static_contract_table_internal_consistency():
    """tick_value/tick_size == multiplier for EVERY era of EVERY contract —
    the invariant the pnl_law and cost_law both rest on."""
    doc = json.loads(open(CONTRACTS, encoding="utf-8").read())
    for sym, c in doc["contracts"].items():
        for era in c["era_table"]:
            ratio = float(era["tick_value_usd"]) / float(era["tick_size"])
            assert abs(ratio - float(era["multiplier"])) < 1e-6, (sym, era)
        assert c["long_base_sign"] == 1, sym
        assert "PLACEHOLDER-PENDING-PER-SYMBOL-LANE" in c["verification"]


def test_T17_6A_era_switch_cost_rows(tmp_path):
    sb = Sandbox(tmp_path).build(
        symbols=["6A"], start="2020-11-16",
        spec=default_spec(symbols=["6A"]))
    r = sb.run()
    assert r.returncode == 0, r.stderr
    payload = _trials_by_id(sb)["6A-L1"]
    trades = [t for fold in payload["folds"] for t in fold["trades"]]
    eras = {t["era"] for t in trades}
    assert eras == {"6A-era1", "6A-era2"}, (
        "fixture must straddle the 2020-11-23 boundary")
    fee = 2.5  # tier t1 (default spec)
    spread, slip = 1.0, 0.5  # stress 1.0
    for t in trades:
        want_tval = 10.0 if t["era"] == "6A-era1" else 5.0
        assert t["tick_value_usd"] == want_tval
        want_cost = 2.0 * (fee + (spread + slip) * want_tval)
        assert abs(t["cost_usd"] - round(want_cost, 6)) < 1e-9
        # gross per unit of price is era-INDEPENDENT (100000 = multiplier):
        move = t["exit_price"] - t["entry_price"]
        if move != 0:
            usd_per_unit = t["gross_pnl_usd"] / (t["direction"] * move)
            assert abs(usd_per_unit - 100000.0) < 1e-4
    # and the two eras really price the SAME tick move differently
    by_era = {e: [t for t in trades if t["era"] == e]
              for e in ("6A-era1", "6A-era2")}
    assert by_era["6A-era1"] and by_era["6A-era2"]
    assert by_era["6A-era1"][0]["tick_value_usd"] == 10.0
    assert by_era["6A-era2"][0]["tick_value_usd"] == 5.0


def test_T18_6J_quote_direction_law(tmp_path):
    sb = Sandbox(tmp_path).build(
        symbols=["6J"],
        spec=default_spec(symbols=["6J"]))
    c = _contract("6J")
    assert c["quote_ccy"] == "USD" and c["base_ccy"] == "JPY"
    assert c["long_base_sign"] == 1
    assert "USD per 1 JPY" in c["quote_direction_note"]
    r = sb.run()
    assert r.returncode == 0, r.stderr
    long_payload = _trials_by_id(sb)["6J-L1"]
    short_payload = _trials_by_id(sb)["6J-S1"]
    mult = float(c["multiplier"])
    for payload, direction in ((long_payload, 1), (short_payload, -1)):
        for fold in payload["folds"]:
            for t in fold["trades"]:
                assert t["direction"] == direction
                move = t["exit_price"] - t["entry_price"]
                # the quoted series convention: pnl = dir * move * multiplier
                want = direction * move * mult
                assert abs(t["gross_pnl_usd"] - round(want, 6)) < 1e-6
                # sign consistency: rising quote + long => positive gross
                if move != 0:
                    assert (t["gross_pnl_usd"] > 0) == \
                        (direction * move > 0)
    # the classic misread (JPY-per-USD, inverting the series) would flip
    # every sign: assert the runner did NOT apply it
    long_first = next(t for fold in long_payload["folds"]
                      for t in fold["trades"] if t["direction"] == 1)
    inverted_want = -(long_first["exit_price"] -
                      long_first["entry_price"]) * mult
    assert long_first["gross_pnl_usd"] != round(inverted_want, 6) or \
        long_first["exit_price"] == long_first["entry_price"]


def test_per_symbol_symbols_all_exercised_in_T1_shape(tmp_path):
    """Compatibility proof: the default 2x2 spec drives ALL FIVE symbols
    plus ES-compat arithmetic through the same engine path."""
    sb = Sandbox(tmp_path).build()
    r = sb.run()
    assert r.returncode == 0, r.stderr
    payloads = _trials_by_id(sb)
    assert set(payloads) == {f"{s}-L1" for s in
                             ["NQ", "6E", "6B", "6J", "6A"]} | \
        {f"{s}-S1" for s in ["NQ", "6E", "6B", "6J", "6A"]}
    for iid, p in payloads.items():
        assert p["totals"]["n_trades"] > 0, f"{iid} produced zero trades"
