"""PC12A cost kernel: measured cells vs the audit numbers (dual-source law),
spread-once pricing, worst-fill grading, stress tiers, window cells."""

import datetime as dt
import json
import pathlib

import pytest

from research.pc12a import cost_kernel as ck

CTRL = pathlib.Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/"
    "portfolio-composite-12assets-100k-v1/integration/research/control/"
    "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1")

AUDIT_CELLS = {
    # DATA_AUDIT_REPORT.md section D(ii)/(iii)/(iv) + COST_AUTHORITY_TABLE
    "C1": {"EURUSD": (0.3, 0.5), "GBPUSD": (0.8, 1.3), "USDJPY": (0.5, 0.9)},
    "C2_MON_THU": {"EURUSD": (1.2, 3.7), "GBPUSD": (2.8, 7.8),
                   "USDJPY": (2.1, 7.4)},   # CORRECTED (governing)
    "C2_FRI": {"EURUSD": (0.5, 1.1), "GBPUSD": (1.2, 2.3),
               "USDJPY": (0.8, 1.8)},
    "C3": {"EURUSD": (5.9, 9.0), "GBPUSD": (13.4, 23.8),
           "USDJPY": (11.0, 22.0)},
}


@pytest.mark.parametrize("cell", list(AUDIT_CELLS))
@pytest.mark.parametrize("pair", ["EURUSD", "GBPUSD", "USDJPY"])
def test_measured_cells_match_audit(cell, pair):
    p50, p90 = AUDIT_CELLS[cell][pair]
    got = ck.MEASURED_CELLS[cell][pair]
    assert got["p50"] == p50 and got["p90"] == p90


def test_corrected_c2_mon_thu_governs_over_stale_table_column():
    """FILL_ACCOUNTING_SPEC 3 erratum: the table's Mon-Thu column (0.6/2.7,
    1.4/5.8, 1.0/4.9) matches the WRONG hour and is REFUSED here."""
    stale = {"EURUSD": (0.6, 2.7), "GBPUSD": (1.4, 5.8),
             "USDJPY": (1.0, 4.9)}
    for pair, (p50, p90) in stale.items():
        got = ck.MEASURED_CELLS["C2_MON_THU"][pair]
        assert (got["p50"], got["p90"]) != (p50, p90)
        assert got["p90"] > p90  # the corrected cell is the WIDER truth
    doc = ck.dual_source_c2_doc()
    assert "GOVERNING" in doc["C2_MON_THU"]
    assert "wrong hour" in doc["C2_MON_THU"]


def test_spread_once_law_ordinary_fill():
    k = ck.CostKernel("EURUSD", tier=1.0)
    q = k.price_ordinary_fill("buy", 10_000, bid_open=1.08432,
                              ask_open=1.08436)
    assert q.fill_price == pytest.approx(1.08436 + 0.00002, abs=1e-12)
    assert q.mid_at_fill == pytest.approx(1.08434, abs=1e-12)
    assert q.spread_once_usd == pytest.approx(0.2, abs=1e-9)   # 10k units
    assert q.slip_beyond_halfspread_usd == pytest.approx(0.2, abs=1e-9)
    # the two crossing lines sum EXACTLY to |fill - mid| * |delta|
    assert q.spread_once_usd + q.slip_beyond_halfspread_usd == \
        pytest.approx(q.cross_cost_usd, abs=1e-12)
    sell = k.price_ordinary_fill("sell", 10_000, 1.08502, 1.08506)
    assert sell.fill_price == pytest.approx(1.08500, abs=1e-12)


def test_commission_u2_and_notional_conventions():
    k = ck.CostKernel("EURUSD")
    # USD-quoted: notional = units x price (0.35 bps of it)
    assert k.commission(100_000, 1.08438) == pytest.approx(
        0.000035 * 100_000 * 1.08438, rel=1e-12)
    j = ck.CostKernel("USDJPY")
    # JPY-quoted: base currency IS USD -> notional = units
    assert j.notional_usd(100_000, 155.0) == 100_000.0
    assert j.commission(100_000, 155.0) == pytest.approx(3.5, rel=1e-12)


def test_swap_usd_u4u5_declared_band():
    k = ck.CostKernel("EURUSD")
    assert k.swap_usd(100_000, 1, 1.08) == pytest.approx(10.0, rel=1e-12)
    assert k.swap_usd(100_000, 3, 1.08) == pytest.approx(30.0, rel=1e-12)
    j = ck.CostKernel("USDJPY")
    # JPY pip converted at the accrual mid: 100k x 0.01 / 155 = ~$6.45
    assert j.swap_usd(100_000, 1, 155.0) == pytest.approx(
        100_000 * 0.01 / 155.0, rel=1e-12)


def test_worst_fill_grading_fx6_shape():
    """Spec 1.5: sell fills at worst(bid_open, bid_close) - band, NEVER at
    the stop; gap excess sits INSIDE the slip line."""
    k = ck.CostKernel("EURUSD")
    q = k.price_graded_fill("sell", 10_000, bid_open=1.0855,
                            ask_open=1.08554, bid_close=1.085,
                            ask_close=1.08504)
    assert q.fill_price == pytest.approx(1.08498, abs=1e-12)
    assert q.quoted_side == 1.0855
    assert q.mid_at_fill == pytest.approx(1.08552, abs=1e-12)
    assert q.gap_excess_pips == pytest.approx(5.0, abs=1e-9)
    assert q.slip_band_pips == pytest.approx(0.2, abs=1e-9)
    assert q.slip_pips == pytest.approx(5.2, abs=1e-9)
    assert q.loss_fill_candidate
    assert q.spread_once_usd + q.slip_beyond_halfspread_usd == \
        pytest.approx(q.cross_cost_usd, abs=1e-9)
    assert q.cross_cost_usd == pytest.approx(5.4, abs=1e-6)
    buy = k.price_graded_fill("buy", 10_000, 1.0850, 1.08504, 1.0855,
                              1.08554)
    assert buy.fill_price == pytest.approx(1.08554 + 0.00002, abs=1e-12)


def test_stress_tiers_scale_variable_components():
    base = ck.CostKernel("EURUSD", 1.0)
    t15 = ck.CostKernel("EURUSD", 1.5)
    q0 = base.price_ordinary_fill("buy", 10_000, 1.08432, 1.08436)
    q1 = t15.price_ordinary_fill("buy", 10_000, 1.08432, 1.08436)
    # crossing distance scales: |fill-mid| x1.5
    assert (q1.fill_price - q1.mid_at_fill) == pytest.approx(
        1.5 * (q0.fill_price - q0.mid_at_fill), rel=1e-12)
    assert t15.commission(10_000, 1.08438) == pytest.approx(
        1.5 * base.commission(10_000, 1.08438), rel=1e-12)
    assert t15.swap_usd(100_000, 3, 1.08) == pytest.approx(
        1.5 * base.swap_usd(100_000, 3, 1.08), rel=1e-12)  # Wed x3 preserved
    # spread-once identity holds at every tier
    assert q1.spread_once_usd + q1.slip_beyond_halfspread_usd == \
        pytest.approx(q1.cross_cost_usd, abs=1e-9)
    with pytest.raises(ValueError):
        ck.CostKernel("EURUSD", tier=1.2)


def test_window_fill_from_measured_cells():
    """Spec 3: S_eff = max(p90 window cell, p90 C1); fill = mid +/- (S_eff/2
    + 1.0 pip event slip). EURUSD Sunday reopen: max(9.0, 0.5) = 9.0.
    The reopen instant is tzdata-rebuilt at 17:00 America/New_York:
    summer 21:00Z, winter 22:00Z."""
    k = ck.CostKernel("EURUSD")
    ts = dt.datetime(2024, 6, 9, 21, 5, tzinfo=dt.timezone.utc)  # summer Sun
    q = k.price_window_fill("buy", 10_000, mid_at_fill=1.08500, ts_fill=ts)
    assert q.fill_price == pytest.approx(1.08500 + 0.00045 + 0.0001,
                                         abs=1e-12)
    assert q.cell_id == "C3"
    assert q.spread_once_usd == pytest.approx(4.5, abs=1e-9)
    assert q.slip_beyond_halfspread_usd == pytest.approx(1.0, abs=1e-9)
    # winter Sunday reopen sits at 22:00Z (EST)
    ts_w = dt.datetime(2024, 1, 7, 22, 5, tzinfo=dt.timezone.utc)
    qw = k.price_window_fill("buy", 10_000, 1.08500, ts_w)
    assert qw.cell_id == "C3"
    # Mon-Thu roll window uses the CORRECTED cell (EURUSD p90 3.7)
    ts2 = dt.datetime(2024, 6, 5, 21, 30, tzinfo=dt.timezone.utc)
    q2 = k.price_window_fill("buy", 10_000, 1.08500, ts2)
    assert q2.cell_id == "C2_MON_THU"
    assert q2.fill_price == pytest.approx(1.08500 + 0.000185 + 0.0001,
                                          abs=1e-12)
    # Friday roll window: max(1.1, 0.5) = 1.1
    ts3 = dt.datetime(2024, 6, 7, 21, 30, tzinfo=dt.timezone.utc)
    q3 = k.price_window_fill("sell", 10_000, 1.08500, ts3)
    assert q3.cell_id == "C2_FRI"
    assert q3.fill_price == pytest.approx(1.08500 - 0.000055 - 0.0001,
                                          abs=1e-12)
    # outside every window -> refused
    with pytest.raises(ValueError):
        k.price_window_fill("buy", 10_000, 1.08500,
                            dt.datetime(2024, 6, 5, 15, 0,
                                        tzinfo=dt.timezone.utc))


def test_estimate_all_in_uses_decision_close_quotes():
    k = ck.CostKernel("EURUSD")
    est = k.estimate_all_in("buy", 20_000, bid_close=1.08710,
                            ask_close=1.08714)
    assert est["est_fill_price"] == pytest.approx(1.08716, abs=1e-12)
    assert est["est_spread_once_usd"] == pytest.approx(0.4, abs=1e-9)
    assert est["est_slip_usd"] == pytest.approx(0.4, abs=1e-9)
    assert est["est_commission_usd"] == pytest.approx(
        0.000035 * 20_000 * 1.08716, rel=1e-9)
    assert est["est_total_usd"] == pytest.approx(
        est["est_spread_once_usd"] + est["est_slip_usd"]
        + est["est_commission_usd"], rel=1e-12)


def test_audit_summary_cross_check_c2_populations():
    """The corrected cells carry the audit's measured populations."""
    summary = json.loads(
        (CTRL / "poolB/data_audit/audit_summary.json").read_text())
    variants = summary["spread"]["EURUSD"]["c2_window_variants"]
    declared = variants["mon_thu_2100_2200_utc"]
    assert declared["p50_pips"] == pytest.approx(1.2, abs=1e-9)
    assert declared["p90_pips"] == pytest.approx(3.7, abs=1e-9)
    assert declared["n_obs"] == 65_109
    # the stale table column matches the 22:00-23:00Z hour instead
    stale_hour = variants["mon_thu_2200_2300_utc"]
    assert stale_hour["p90_pips"] == pytest.approx(2.6, abs=1e-9)
    assert variants["cost_table_mon_thu_p50_p90"][1] == pytest.approx(
        2.7, abs=1e-9)
