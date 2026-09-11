"""CRYPTO-NG2 D2 tests: hand-computed fixtures for the measurement law.

Covers (dispatch contract):
  1. a small rho pair hand-computed (Pearson 19/21 through the NG2
     shared-key alignment path, average-rank Spearman, and the shifted-key
     low-N guard; a hand-computed F5 daily-aggregation case);
  2. fail-closed behaviour: unevidenced settlement instant -> counted
     UNFUNDED_SKIP_NO_SETTLEMENT never an inferred PASS; funding pull retry
     exhaustion aborts with nothing swallowed; identifiability twin fails;
     census loader fails closed on a tampered declaration;
  3. the funding-grid case: evidence matching absorbs the observed
     boundary+1ms quirk, an off-grid 04:00 settlement is an incident and
     evidences nothing, duplicate grid hours are recorded, and transfers
     book with the correct sign (-d*rate) on a synthetic panel, including
     the P1-exit == P2-entry boundary handoff.

Network-free: no panel store, no CADS, no endpoints.
"""

from __future__ import annotations

import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_WORKTREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_WORKTREE))

from research.assets.crypto_ng2.d2 import measure as M   # noqa: E402


def _dec(sym, instant, r, status="FUNDED"):
    return M.NG2Decision(
        symbol=sym, instant=instant, decision_ts=instant,
        decision_bar=instant[:13], decision_date=instant[:10],
        proj_day=instant[:10], role="anchor", arm_id="T",
        status=status, r_gross=r)


# --------------------------------------------------------------------------- #
# 1. hand-computed rho (through the NG2 shared-key alignment)
# --------------------------------------------------------------------------- #

def test_rho_shared_keys_hand_computed_19_over_21():
    # x = 1..8 aligned to keys k1..k8; y = [2,1,4,3,6,5,8,7]
    # dx = [-3.5,-2.5,-1.5,-0.5,.5,1.5,2.5,3.5], sxx = 42
    # dy = [-2.5,-3.5,-.5,-1.5,1.5,.5,3.5,2.5], syy = 42
    # sum(dx*dy) = 38 -> r = 38/42 = 19/21 (y distinct -> Spearman == Pearson)
    xs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    ys = [2.0, 1.0, 4.0, 3.0, 6.0, 5.0, 8.0, 7.0]
    keys = [f"2026-01-{d:02d}T08:00:00Z" for d in range(1, 9)]
    a = [_dec("BTCUSDT", k, x) for k, x in zip(keys, xs)]
    b = [_dec("BTCUSDT", k, y) for k, y in zip(keys, ys)]
    res = M.rho_on_shared_keys(a, b)
    assert res["shared_grid_keys"] == 8
    pair = res["pair"]
    assert pair["status"] == "MEASURED"
    assert abs(pair["pearson"] - 19.0 / 21.0) < 1e-6
    assert abs(pair["spearman"] - 19.0 / 21.0) < 1e-6
    assert pair["pair_verdict"] == "VETO"           # 0.9048 > 0.20
    assert abs(pair["margin_to_bar"] - (0.20 - 19.0 / 21.0)) < 1e-6


def test_rho_shifted_keys_drop_below_min_pairs():
    # placebo keys shifted one session: a on k1..k8, b on k2..k9
    # shared = k2..k8 = 7 pairs < MIN_PAIRS(8) -> NOT_COMPUTABLE_LOW_N
    xs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    ys = [2.0, 1.0, 4.0, 3.0, 6.0, 5.0, 8.0, 7.0]
    ka = [f"2026-01-{d:02d}T08:00:00Z" for d in range(1, 9)]
    kb = [f"2026-01-{d:02d}T08:00:00Z" for d in range(2, 10)]
    a = [_dec("BTCUSDT", k, x) for k, x in zip(ka, xs)]
    b = [_dec("BTCUSDT", k, y) for k, y in zip(kb, ys)]
    res = M.rho_on_shared_keys(a, b)
    assert res["shared_grid_keys"] == 7
    assert res["pair"]["status"] == "NOT_COMPUTABLE_LOW_N"
    assert res["pair"]["pair_verdict"] == "UNMEASURED"


def test_spearman_average_ranks_hand_case():
    # x2 -> ranks [1.5,1.5,3.5,3.5,5.5,5.5,7.5,7.5]; y2 -> [1.5,3.5,1.5,3.5,...]
    # dx=[-3,-3,-1,-1,1,1,3,3]; dy=[-3,-1,-3,-1,1,3,1,3]
    # sxx=syy=40; sum=32 -> rho = 0.8 (re-checked for the shared primitives)
    x2 = [1.0, 1.0, 2.0, 2.0, 3.0, 3.0, 4.0, 4.0]
    y2 = [1.0, 2.0, 1.0, 2.0, 3.0, 4.0, 3.0, 4.0]
    s = M.N1.spearman(x2, y2)
    assert s is not None
    assert abs(s - 0.8) < 1e-12


def test_f5_daily_aggregated_hand_case():
    # eight symbol-days; each day's projection = the sum of its 3 instant
    # rows (one non-zero carrying the day value):
    #   A day-sums = 0.01 x [1..8],  B day-sums = 0.01 x [2,1,4,3,6,5,8,7]
    # -> the same hand arithmetic as the 19/21 case, at the day level:
    #    Pearson = Spearman = 19/21 (distinct values on both sides)
    def rows(day, total):
        return [_dec("BTCUSDT", f"{day}T{h:02d}:00:00Z", v)
                for h, v in zip((0, 8, 16), (total, 0.0, 0.0))]
    ys = [2, 1, 4, 3, 6, 5, 8, 7]
    days = [f"2026-01-{d:02d}" for d in range(1, 9)]
    a = [r for d in days for r in rows(d, 0.01 * int(d[-2:]))]
    b = [r for d, y in zip(days, ys) for r in rows(d, 0.01 * y)]
    res = M.f5_daily_aggregated(a, b)
    assert res["shared_days"] == 8
    assert res["status"] == "MEASURED"
    assert abs(res["daily"]["pearson"] - 19.0 / 21.0) < 1e-6
    assert res["daily"]["spearman"] == res["daily"]["pearson"]
    assert res["f5_fired"] is True                  # 0.9048 > 0.20
    # the per-decision shared-key rho is NOT the day-level rho (alignment
    # differs); it is recorded alongside, here over 24 keys
    assert res["per_decision_shared_keys"] == 24


# --------------------------------------------------------------------------- #
# 2. fail-closed cases
# --------------------------------------------------------------------------- #

def test_required_ng2_veto_failure_is_fail_closed():
    vp = M.N1.VetoPanel()
    vp.add("generic_tsmom28", "GENERIC", "generic", "tsmom",
           fn=lambda s, d: 1.0, hourly=False)
    vp.build_failures["v17_oi_level"] = "not supplied (fixture)"
    pairs = {"generic_tsmom28": M.N1.rho_pair_status(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0])}
    verdict = M.ng2_novelty_verdict(pairs, vp.build_failures)
    assert verdict["novelty_verdict"] == "INELIGIBLE_FAIL_CLOSED"
    assert "v17_oi_level" in verdict["reason"]
    # the NG2 additions are inside the required set too
    assert "cng2_funding_level_pull" in M.NG2_REQUIRED_VETOES
    assert "cng2_dead_fomc_a4p1" in M.NG2_REQUIRED_VETOES
    assert "cng2_dead_fomc_a4p2" in M.NG2_REQUIRED_VETOES


def test_no_measurable_pair_fails_closed():
    verdict = M.ng2_novelty_verdict({}, {})
    assert verdict["novelty_verdict"] == "INELIGIBLE_FAIL_CLOSED"


def test_pull_retry_exhaustion_raises_fail_closed():
    calls, sleeps = [], []

    def boom(url):
        calls.append(url)
        raise RuntimeError("http 451")

    raised = False
    try:
        M.pull_funding_symbol("BTCUSDT", fetch=boom, sleep=sleeps.append)
    except RuntimeError as exc:
        raised = True
        assert "funding pull failed" in str(exc)
    assert raised
    assert len(calls) == M.FUNDING_RETRIES      # 3 attempts, then abort
    assert sleeps == [5.0, 10.0, 15.0]          # backoff 5s x attempt


def test_pull_paginates_by_start_time_with_etiquette():
    # two full pages + a final short page ending exactly at the window end;
    # etiquette sleep between requests, never after the terminal page
    page1 = [{"fundingTime": t, "fundingRate": "0.0001"}
             for t in range(1000, 1500)]
    page2 = [{"fundingTime": t, "fundingRate": "0.0001"}
             for t in range(1500, 2000)]
    page3 = [{"fundingTime": t, "fundingRate": "0.0002"}
             for t in range(2000, 2011)]
    pages = [page1, page2, page3]
    urls, sleeps = [], []

    def fake_fetch(url):
        urls.append(url)
        return pages.pop(0)

    rows, rep = M.pull_funding_symbol(
        "BTCUSDT", start_ms=1000, end_ms=2010,
        fetch=fake_fetch, sleep=sleeps.append)
    assert len(rows) == 1011                     # window filter keeps all
    assert rep["pages"] == 3
    assert rows[0]["fundingTime"] == 1000 and rows[-1]["fundingTime"] == 2010
    # cursor advanced strictly (startTime = last + 1)
    assert "startTime=1500" in urls[1]
    assert "startTime=2000" in urls[2]
    assert sleeps == [0.55, 0.55]                # etiquette between requests


def test_identifiability_twin_fails():
    keys = [f"2026-01-{d:02d}T08:00:00Z" for d in range(1, 9)]
    # alternating-sign anchor vs block-pattern control: both zero-mean and
    # sum(x*y) = 1-1-1+1+1-1-1+1 (x 1e-4) = 0 -> Pearson EXACTLY 0
    xs = [0.01, -0.01, 0.01, -0.01, 0.01, -0.01, 0.01, -0.01]
    ys = [0.01, 0.01, -0.01, -0.01, 0.01, 0.01, -0.01, -0.01]
    anchor = [_dec("BTCUSDT", k, x) for k, x in zip(keys, xs)]
    twin = [_dec("BTCUSDT", k, x) for k, x in zip(keys, xs)]   # rho = 1.0
    distinct = [_dec("BTCUSDT", k, y) for k, y in zip(keys, ys)]
    res = M.identifiability(anchor, twin, distinct)
    assert res["status"] == "IDENTIFIABILITY_FAIL_CONTROL_TWIN"
    assert res["verdict"] == "FAIL"
    assert res["worst_abs_rho"] == 1.0
    assert res["worst_arm"] == "clock_shadow"
    assert res["margin_to_bar"] == round(M.IDENT_BAR - 1.0, 6)
    # both controls distinct -> PASS under the 0.98 bar, rho exactly 0
    ok = M.identifiability(anchor, distinct, distinct)
    assert ok["verdict"] == "PASS"
    assert ok["worst_abs_rho"] == 0.0


def test_census_loader_fail_closed_on_tampered_declaration():
    good_path = Path(_WORKTREE) / "research" / "control" / "crypto_ng2_run" \
        / "p0_calendar_census_ng2.json"
    import json
    bad = json.loads(good_path.read_text())
    bad["instants"] = [r for r in bad["instants"] if not (
        r["series"] == "CPI" and r["instant_utc"].startswith("2026-08"))]
    with tempfile.NamedTemporaryFile("w", suffix=".json",
                                     delete=False) as fh:
        json.dump(bad, fh)
        tmp = fh.name
    try:
        raised = False
        try:
            M.load_census_instants(tmp)
        except ValueError as exc:
            raised = True
            assert "cpi_count_11" in str(exc)
        assert raised
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_census_loader_passes_on_the_real_artifact():
    res = M.load_census_instants(
        Path(_WORKTREE) / "research" / "control" / "crypto_ng2_run"
        / "p0_calendar_census_ng2.json")
    assert len(res["instants"]["CPI"]) == 11
    assert len(res["instants"]["NFP"]) == 11
    assert all(res["checks"].values())
    assert res["checks"]["cpi_nfp_date_disjoint"] is True


# --------------------------------------------------------------------------- #
# 3. funding-grid cases
# --------------------------------------------------------------------------- #

def _ms(y, mo, d, h, msec=0):
    return int(datetime(y, mo, d, h, 0, 0, msec * 1000,
                        tzinfo=timezone.utc).timestamp() * 1000)


def test_evidence_absorbs_plus_1ms_quirk_and_flags_off_grid():
    rows = [
        # grid instant 2025-08-22T08 with the observed +1ms quirk -> evidenced
        {"fundingTime": _ms(2025, 8, 22, 8, msec=1), "fundingRate": "0.0001"},
        # exact grid instant 16:00 -> evidenced
        {"fundingTime": _ms(2025, 8, 22, 16), "fundingRate": "-0.0002"},
        # OFF-GRID 04:00 settlement (a 4h-interval artefact) -> incident,
        # evidences nothing on the 8h grid
        {"fundingTime": _ms(2025, 8, 23, 4, msec=3), "fundingRate": "0.0003"},
        # duplicate fold onto 2025-08-23T08 -> recorded, first kept
        {"fundingTime": _ms(2025, 8, 23, 8, msec=2), "fundingRate": "0.0004"},
        {"fundingTime": _ms(2025, 8, 23, 8, msec=9), "fundingRate": "0.0005"},
    ]
    ev = M.build_funding_evidence("BTCUSDT", rows)
    assert ev.rate_at("2025-08-22T08") == 0.0001     # +1ms absorbed
    assert ev.rate_at("2025-08-22T16") == -0.0002
    assert ev.rate_at("2025-08-23T08") == 0.0004     # first kept, dup recorded
    assert ev.rate_at("2025-08-23T04") is None       # off-grid evidences none
    assert len(ev.off_grid_rows) == 1
    assert ev.off_grid_rows[0]["fundingRate"] == "0.0003"
    assert len(ev.duplicate_grid_hours) == 1
    assert ev.raw_rows[0] == (_ms(2025, 8, 22, 8, msec=1), 0.0001)
    rep = ev.report()
    assert rep["off_grid_rows"] == 1
    assert rep["duplicate_grid_hours"] == 1


def test_eligible_grid_is_1094_on_the_8h_clock():
    instants = M.eligible_grid_instants()
    assert len(instants) == 1094
    assert instants[0].strftime("%Y-%m-%dT%H:%M:%SZ") == M.GRID_FIRST_INSTANT
    assert instants[-1].strftime("%Y-%m-%dT%H:%M:%SZ") == M.GRID_LAST_INSTANT
    assert all(t.hour in (0, 8, 16) for t in instants)
    assert instants[0].hour == 8      # 2025-08-22T00 is the warmup exclusion


def _synthetic_evidence(rate_by_day=lambda i: 0.0001):
    """Evidence rows for every eligible grid instant (+1ms quirk), with the
    2025-09-01T08 instant removed to exercise the fail-closed skip."""
    skip = "2025-09-01T08"
    rows, rates = [], {}
    for i, t in enumerate(M.eligible_grid_instants()):
        if M.N1.fmt_hour(t) == skip:
            continue
        rate = rate_by_day(i)
        rates[M.N1.fmt_hour(t)] = rate
        rows.append({"fundingTime": int(t.timestamp() * 1000) + 1,
                     "fundingRate": repr(rate)})
    return M.build_funding_evidence("BTCUSDT", rows), skip, rates


def _synthetic_panel(symbol="BTCUSDT"):
    """Complete H1 panel over the frozen window with deterministic prices."""
    import io
    import csv as _csv
    from datetime import timedelta
    buf = io.StringIO()
    w = _csv.writer(buf)
    w.writerow(["symbol", "hour_utc", "day_utc", "n_trades", "buy_count",
                "buy_qty", "sell_qty", "buy_quote", "sell_quote",
                "quote_total", "qty_total", "vwap", "first_price",
                "last_price", "max_trade_quote", "entry_gap_s", "max_run_buy",
                "max_run_sell", "last_ts_ms"])
    t0 = datetime(2025, 8, 22, tzinfo=timezone.utc)
    hours = int((datetime(2026, 8, 22, tzinfo=timezone.utc) - t0)
                .total_seconds() // 3600)
    for i in range(hours):
        dt = t0 + timedelta(hours=i)
        h = dt.strftime("%Y-%m-%dT%H")
        px = 100.0 + (i % 17) * 0.25
        bq, sq = 55.0 + (i % 7), 45.0 + (i % 11)
        w.writerow([symbol, h, dt.strftime("%Y-%m-%d"), 100, 50, 1.0, 1.0,
                    bq, sq, bq + sq, 2.0, px, px - 0.25, px, 5.0,
                    1.0 + (i % 3) * 0.5, 10, 9,
                    int((dt + timedelta(hours=1)).timestamp() * 1000) - 1])
    return M.N1.Panel.from_bytes(symbol, buf.getvalue().encode())


def test_a5_anchor_missing_evidence_is_counted_fail_closed():
    panel = _synthetic_panel()
    ev, skip, _ = _synthetic_evidence()
    rows = M.build_a5_arm(panel, ev, "CNG2-A5-P1", "anchor")
    assert len(rows) == 1094
    skipped = [r for r in rows if r.status == "UNFUNDED_SKIP_NO_SETTLEMENT"]
    assert len(skipped) == 1
    assert skipped[0].instant == "2025-09-01T08:00:00Z"
    assert skipped[0].r_gross is None and skipped[0].direction is None
    assert sum(1 for r in rows if r.status == "FUNDED") == 1093
    rep = ev.report()
    assert rep["evidenced_grid_instants"] == 1093
    assert rep["unevidenced_grid_instants"] == 1


def test_a5_p1_anchor_transfer_sign_and_hand_computed_return():
    panel = _synthetic_panel()
    ev, _, rates = _synthetic_evidence()
    rows = M.build_a5_arm(panel, ev, "CNG2-A5-P1", "anchor")
    row = [r for r in rows if r.instant == "2025-10-01T08:00:00Z"][0]
    # hand-computed from the synthetic generator constants:
    # bq(i) = 55 + i%7, sq(i) = 45 + i%11, px(i) = 100 + (i%17)*0.25
    i_of = lambda hstr: int(
        (datetime.strptime(hstr, "%Y-%m-%dT%H")
         .replace(tzinfo=timezone.utc)
         - datetime(2025, 8, 22, tzinfo=timezone.utc)).total_seconds() // 3600)
    iA, i5, i6, iB = (i_of("2025-10-01T04"), i_of("2025-10-01T05"),
                      i_of("2025-10-01T06"), i_of("2025-10-01T08"))
    bq, sq = lambda i: 55.0 + i % 7, lambda i: 45.0 + i % 11
    num = (bq(iA) - sq(iA)) + (bq(i5) - sq(i5)) + (bq(i6) - sq(i6))
    den = (bq(iA) + sq(iA)) + (bq(i5) + sq(i5)) + (bq(i6) + sq(i6))
    assert num > 0 and num / den > 0
    assert row.direction == 1
    px = lambda i: 100.0 + (i % 17) * 0.25
    rate = rates["2025-10-01T08"]
    expected = 1.0 * (px(iB) / px(i6) - 1.0) + (-1.0 * rate)  # long pays
    assert abs(row.r_gross - expected) < 1e-12
    assert row.transfer == -rate                       # transfer < 0 booked
    assert row.entry_bar == "2025-10-01T06"
    assert row.exit_bar == "2025-10-01T08"
    assert row.decision_bar == "2025-10-01T06"         # decision at S-1h


def test_a5_p2_placebo_books_true_s_transfer_others_do_not():
    panel = _synthetic_panel()
    ev, _, _ = _synthetic_evidence()
    anchor = M.build_a5_arm(panel, ev, "CNG2-A5-P2", "anchor")
    placebo = M.build_a5_arm(panel, ev, "CNG2-A5-P2", "placebo")
    s = "2025-10-01T08:00:00Z"
    a = [r for r in anchor if r.instant == s][0]
    p = [r for r in placebo if r.instant == s][0]
    assert a.transfer is None                          # hold crosses no S
    assert p.transfer == -p.direction * ev.rate_at("2025-10-01T08")
    # placebo fills: entry close B' (=S-1h) at bar 06, exit close B'+3 at 09
    assert p.entry_bar == "2025-10-01T06"
    assert p.exit_bar == "2025-10-01T09"
    assert p.decision_bar == "2025-10-01T06"
    # anchor fills: entry close B (=S+1h) at bar 08, exit close B+3 at 11
    assert a.entry_bar == "2025-10-01T08"
    assert a.exit_bar == "2025-10-01T11"


def test_p1_exit_bar_is_p2_entry_bar_on_the_boundary():
    # the structural handoff: P1 exits exactly where P2 enters (close of B)
    panel = _synthetic_panel()
    ev, _, _ = _synthetic_evidence()
    p1 = M.build_a5_arm(panel, ev, "CNG2-A5-P1", "anchor")
    p2 = M.build_a5_arm(panel, ev, "CNG2-A5-P2", "anchor")
    k1 = {(r.symbol, r.instant): r.exit_bar for r in p1
          if r.status == "FUNDED"}
    k2 = {(r.symbol, r.instant): r.entry_bar for r in p2
          if r.status == "FUNDED"}
    shared = [k for k in k1 if k in k2]
    assert len(shared) == 1093
    assert all(k1[k] == k2[k] for k in shared)


def test_dead_form_directions_on_synthetic_bars():
    panel = _synthetic_panel()
    i_of = lambda hstr: int(
        (datetime.strptime(hstr, "%Y-%m-%dT%H")
         .replace(tzinfo=timezone.utc)
         - datetime(2025, 8, 22, tzinfo=timezone.utc)).total_seconds() // 3600)
    bar = "2025-10-01T06"
    i0 = i_of(bar)
    bq, sq = lambda i: 55.0 + i % 7, lambda i: 45.0 + i % 11
    # dead CNG1-A4-P1 rule: sign(imb on the decision bar)
    imb = (bq(i0) - sq(i0)) / (bq(i0) + sq(i0))
    assert M.dead_form_direction(panel, bar, "cng2_dead_fomc_a4p1") == (
        1 if imb > 0 else -1)
    # dead CNG1-A4-P2 rule: sign(press over decision bar-4..-1)
    num = sum(bq(i0 + k) - sq(i0 + k) for k in (-4, -3, -2, -1))
    den = sum(bq(i0 + k) + sq(i0 + k) for k in (-4, -3, -2, -1))
    assert M.dead_form_direction(panel, bar, "cng2_dead_fomc_a4p2") == (
        1 if num / den > 0 else -1)
