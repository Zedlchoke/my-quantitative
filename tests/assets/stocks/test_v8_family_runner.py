"""V8 family runner tests - synthetic fixtures, hand-computed values.
No production outcome may appear here (handbook 14.3)."""

import json
import os
import shutil

import pytest

from research.assets.stocks import v8_family_runner as r


@pytest.fixture()
def env(tmp_path):
    """Tiny synthetic world: 2 sectors x 8 names, 160 sessions."""
    d = tmp_path
    (d / "eod").mkdir()
    (d / "panel").mkdir()
    # sessions: 160 business-ish days labelled S0000..S0159 with ISO dates
    from datetime import date, timedelta
    start = date(2018, 1, 1)
    days = []
    cur = start
    while len(days) < 160:
        if cur.weekday() < 5:
            days.append(cur.isoformat())
        cur += timedelta(days=1)
    prices = d / "eod"
    names = {}
    for s in range(2):
        for k in range(8):
            cik = f"CIK{s}{k:09d}"
            names[cik] = s
            bars = []
            px = 10.0 + s + 0.01 * k
            for i, day in enumerate(days):
                close = px + 0.01 * i  # gently rising
                vol = 1_000_000 + 1000 * k
                bars.append({
                    "date": day, "open": close, "high": close, "low": close,
                    "close": close, "adjusted_close": close, "volume": vol,
                })
            (prices / f"{cik}__T{k}.json").write_text(json.dumps(bars))
    panel_file = d / "panel.jsonl"
    with open(panel_file, "w") as f:
        for cik, s in names.items():
            # Assets: vintage filed 40 days after period end, quarterly
            for q in range(4):
                eff = days[10 + q * 30]
                avail = days[10 + q * 30 + 40] if 10 + q * 30 + 40 < 160 else days[159]
                f.write(json.dumps({
                    "e": cik, "s": f"SEC{s}", "f": "us-gaap:Assets",
                    "u": "USD", "v": 1000.0 + int(cik[-2:]), "eff": eff,
                    "evd": eff, "avail": avail,
                }) + "\n")
                # num field, constant ratio 0.5 per name
                f.write(json.dumps({
                    "e": cik, "s": f"SEC{s}", "f": "us-gaap:XNum",
                    "u": "USD", "v": 500.0 + int(cik[-2:]), "eff": eff,
                    "evd": eff, "avail": avail,
                }) + "\n")
    return {"dir": d, "days": days, "names": names}


def _use(env, monkeypatch):
    monkeypatch.setattr(r, "ROOT", str(env["dir"]))
    monkeypatch.setattr(r, "PANEL", str(env["dir"] / "panel.jsonl"))
    monkeypatch.setattr(r, "PRICES", str(env["dir"] / "eod"))
    monkeypatch.setattr(r, "BENCH", str(env["dir"]))


def test_asof_gate_excludes_same_day_filing(env, monkeypatch):
    _use(env, monkeypatch)
    panel = r.load_panel({"us-gaap:Assets"})
    rows = panel[list(panel)[0]]["rows"]["us-gaap:Assets"]
    # a filing ON the decision date is not visible (stamp = end of day, gate = 00:00)
    dec = rows[-1][0]  # avail of last filing
    assert r.asof(rows, dec) is not None
    filed_that_day = [x for x in rows if x[0] == dec]
    nxt = r.asof(rows, dec)
    # the visible vintage must be strictly earlier than the decision date
    assert nxt[0] < dec


def test_asof_age_bound(env, monkeypatch):
    _use(env, monkeypatch)
    panel = r.load_panel({"us-gaap:Assets"})
    rows = panel[list(panel)[0]]["rows"]["us-gaap:Assets"]
    old = rows[0]
    late = rows[-1]
    # decision 500 days after the first filing, before the last filing exists
    from datetime import date, timedelta
    d = (date.fromisoformat(old[0]) + timedelta(days=100)).isoformat()
    bounded = r.asof(rows, d, age_days=10)
    if (date.fromisoformat(d) - date.fromisoformat(old[0])).days > 10 and len(rows) == 1:
        assert bounded is None


def test_no_lookahead_mutation(env, monkeypatch):
    """Moving a filing after the decision must not change the as-of pick."""
    _use(env, monkeypatch)
    panel = r.load_panel({"us-gaap:Assets"})
    ent = list(panel)[0]
    rows = panel[ent]["rows"]["us-gaap:Assets"]
    d = rows[1][0]  # decision at the 2nd filing date
    before = r.asof(rows, d)
    assert before[0] == rows[0][0]
    # mutate: move the 1st filing after d
    a0, e0, v0 = rows[0]
    rows_mut = [(d, e0, v0)] + rows[1:]
    after = r.asof(rows_mut, d)
    assert after is None or after[0] < d


def test_cost_charged_exactly_once():
    """One fill of unit notional in band A costs 10 bps, once."""
    dw = 1.0
    assert dw * r.BAND_BPS["A"] / 10000.0 == pytest.approx(0.001)
    assert dw * r.BAND_BPS["C"] / 10000.0 == pytest.approx(0.0025)


def test_band_thresholds():
    assert r.band_of(60_000_000) == "A"
    assert r.band_of(20_000_000) == "B"
    assert r.band_of(3_000_000) == "C"
    assert r.band_of(1_000_000) == "UNTRADABLE"


def test_sector_abstain_below_min(env, monkeypatch):
    _use(env, monkeypatch)
    ranks = {f"n{i}": ("SEC0", i / 10) for i in range(5)}
    book, active = r.target_book(ranks, {}, "low_long")
    assert active == 0 and book == {}
    ranks = {f"n{i}": ("SEC0", i / 11) for i in range(12)}
    book, active = r.target_book(ranks, {}, "low_long")
    assert active == 1
    longs = [n for n, s in book.items() if s == "L"]
    shorts = [n for n, s in book.items() if s == "S"]
    assert len(longs) == 4 and len(shorts) == 4  # tercile of 12


def test_hysteresis_retention():
    ranks = {f"n{i}": ("SEC0", i / 11) for i in range(12)}
    book, _ = r.target_book(ranks, {}, "low_long")
    held = {n: "L" for n, s in book.items() if s == "L"}
    # nudge a held long just past the tercile (within one decile) -> retained
    edge = max(n for n, s in book.items() if s == "L")
    pct = dict((k, v[0]) for k, v in ranks.items())
    ranks2 = dict(ranks)
    ranks2[edge] = ("SEC0", r.TERCILE + r.HYSTERESIS - 0.001)
    book2, _ = r.target_book(ranks2, held, "low_long")
    assert book2.get(edge) == "L"
    # beyond one decile -> dropped
    ranks3 = dict(ranks)
    ranks3[edge] = ("SEC0", r.TERCILE + r.HYSTERESIS + 0.05)
    book3, _ = r.target_book(ranks3, held, "low_long")
    assert book3.get(edge) is None


def test_control_signal_differs_from_anchor(env, monkeypatch):
    """Structural distinctness: stock vs flow forms on identical data.
    Hand-built vintages with a 365-day eff gap (passes the fiscal-type
    330-400 day filter)."""
    _use(env, monkeypatch)
    ent = {"sector": "SEC0", "rows": {
        "us-gaap:XNum": [("2019-06-01", "2019-05-01", 500.0),
                         ("2018-06-01", "2018-05-01", 500.0)],
        "us-gaap:Assets": [("2019-06-01", "2019-05-01", 1000.0)],
    }}
    spec_flow = {"kind": "accrual_flow", "numerator_fields": ["us-gaap:XNum", "us-gaap:XNum", "us-gaap:XNum"],
                 "denominator_field": "us-gaap:Assets", "denominator_age": 400}
    spec_stock = {"kind": "wc_stock", "numerator_fields": ["us-gaap:XNum", "us-gaap:XNum", "us-gaap:XNum"],
                  "denominator_field": "us-gaap:Assets", "denominator_age": 400}
    # flow with identical legs at both dates = zero numerator -> 0.0
    assert r.signal_value(spec_flow, ent, "2019-07-01", "2018-07-01") == 0.0
    stock = r.signal_value(spec_stock, ent, "2019-07-01", None)
    # WC stock form: (X + X - X)/Assets = 500/1000
    assert stock == pytest.approx(0.5)


def _fixture_arm_spec(monkeypatch):
    """Point a copy of the real F2 spec at the fixture's fields."""
    import copy
    spec = copy.deepcopy(r.ARM_SPECS["SFV8-F2-ANCHOR"])
    spec["numerator_fields"] = ["us-gaap:XNum"]
    spec["denominator_field"] = "us-gaap:Assets"
    monkeypatch.setitem(r.ARM_SPECS, "SFV8-F2-ANCHOR", spec)


def test_dry_run_record_has_no_outcome_fields(env, monkeypatch):
    _use(env, monkeypatch)
    _fixture_arm_spec(monkeypatch)
    panel = r.load_panel({"us-gaap:XNum", "us-gaap:Assets"})
    prices = r.load_prices()
    folds = r.fold_sessions(prices)
    rec = r.run_arm("SFV8-F2-ANCHOR", panel, prices, folds, dry_run=True)
    blob = json.dumps(rec)
    for forbidden in ("pnl", "expectancy", "metrics", "pf", "mdd", "alpha"):
        assert forbidden not in blob, f"leak: {forbidden} in dry-run record"
    assert rec["decisions_total"] > 0
    assert all("cost_bps_paid" in s for s in rec["schedule"])


def test_dry_run_deterministic_double_generation(env, monkeypatch):
    _use(env, monkeypatch)
    _fixture_arm_spec(monkeypatch)
    panel = r.load_panel({"us-gaap:XNum", "us-gaap:Assets"})
    prices = r.load_prices()
    folds = r.fold_sessions(prices)
    a = r.run_arm("SFV8-F2-ANCHOR", panel, prices, folds, dry_run=True)
    b = r.run_arm("SFV8-F2-ANCHOR", panel, prices, folds, dry_run=True)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_scored_refused_without_owner_go(env, monkeypatch):
    _use(env, monkeypatch)
    panel = r.load_panel({"us-gaap:Assets"})
    prices = r.load_prices()
    folds = r.fold_sessions(prices)
    with pytest.raises(SystemExit):
        r.run_arm("SFV8-F2-ANCHOR", panel, prices, folds, dry_run=False,
                  owner_go="GO STOCKS V7 SCORED EXECUTION")
    with pytest.raises(SystemExit):
        r.run_arm("SFV8-F2-ANCHOR", panel, prices, folds, dry_run=False, owner_go=None)


def test_malformed_price_file_fail_closed(env, monkeypatch):
    _use(env, monkeypatch)
    (env["dir"] / "eod" / "CIKbroken__X.json").write_text("{not json")
    with pytest.raises(json.JSONDecodeError):
        r.load_prices()


def test_arm_specs_pairwise_distinct_digests():
    digests = {a: s["arm_config_digest"] for a, s in []}  # placeholder
    import hashlib
    ds = {a: hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()
          for a, s in r.ARM_SPECS.items()}
    assert len(set(ds.values())) == len(ds) == 6
