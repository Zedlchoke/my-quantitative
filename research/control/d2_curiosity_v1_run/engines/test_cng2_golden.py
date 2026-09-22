"""test_cng2_golden.py — golden tests for the CNG2-A5-P1 engine (lane I).

Cycle D2-CURIOSITY-V1, cell CNG2-A5-P1. NON_GOVERNING_DIAGNOSTIC.
Every test runs on SYNTHETIC panels generated in-file — the REAL bound data
under ../data/cng2/ is never opened here and never scored (no outcome is
computed anywhere in this lane; the engine refuses aggregates).

Golden tests (all must PASS before scoring):
  a  no-lookahead: perturbing any bar >= B-1 never changes d/entry of
     decisions at earlier settlements; the press window never reads B-1/B
  b  fills: entry exactly last_price(B-2), exit exactly last_price(B),
     transfer booked at S only
  c  cost debit: every filled decision debits 2x(taker+spread) at the
     frozen tier constants (tier1 5+2 bps/fill; tier2 PRIMARY 10+4
     bps/fill); zero cost forbidden
  d  missing-data fail-closed: missing feature bar -> UNMEASURED_BAR (never
     imputed); missing settlement -> UNFUNDED_SKIP_NO_SETTLEMENT; missing
     or bad-price fill bar -> BLOCKED_MISSING_BAR; exact tie -> UNFUNDED_SKIP
  e  exactly-three-cell enforcement: registry == {SFNG2-A4-P1, FXNG3-A4-P1,
     CNG2-A5-P1}; any other id rejected
  f  S1 denial: any path containing '/S1/' or 's1_' raises
  g  zero-parameter-search: fixed public API surface, immutable frozen
     constants, no tuning knobs, folds NULL, score_cells refuses
  h  determinism: two runs over the same panels -> byte-identical rows
  smoke  REPLAY_NOT_PROSPECTIVE end-to-end run on a synthetic 3-symbol panel

Runs under pytest or plain python:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest test_cng2_golden.py -v
  /Users/hoangminhlong/my-quantitative/.venv/bin/python test_cng2_golden.py

Results are recorded honestly (pass/fail per test) to
engines/test_results_cng2.json via an atexit hook.
"""

import atexit as _atexit
import datetime as _dt
import inspect as _inspect
import json as _json
import pathlib as _pth
import sys as _sys

_HERE = _pth.Path(__file__).resolve().parent
if str(_HERE) not in _sys.path:
    _sys.path.insert(0, str(_HERE))

import cells_registry
import cng2_engine as engine

_UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
_H0 = int(_dt.datetime(2025, 8, 22, tzinfo=_dt.timezone.utc).timestamp()) // 3600
_N_HOURS = 96
_MS_PER_HOUR = 3_600_000

_RESULTS = []


def _golden(name):
    """Decorator: run the test, record an honest PASS/FAIL row, re-raise."""
    def deco(fn):
        def wrapped():
            try:
                fn()
                _RESULTS.append({"test": name, "status": "PASS", "detail": ""})
            except BaseException as exc:  # noqa: BLE001 — record honestly, re-raise
                _RESULTS.append(
                    {"test": name, "status": "FAIL",
                     "detail": ("%s: %s" % (type(exc).__name__, exc))[:500]}
                )
                raise
        wrapped.__name__ = name
        wrapped._golden_name = name
        return wrapped
    return deco


def _write_results_atexit():
    out = {
        "schema": "cng2_golden_test_results@1",
        "cycle_id": "D2-CURIOSITY-V1",
        "cell_id": "CNG2-A5-P1",
        "label": "NON_GOVERNING_DIAGNOSTIC REPLAY_NOT_PROSPECTIVE (synthetic panels only; real bound data never scored)",
        "python": _sys.version.split()[0],
        "engine_public_api": list(engine.PUBLIC_API),
        "results": _RESULTS,
        "all_pass": bool(_RESULTS) and all(r["status"] == "PASS" for r in _RESULTS),
    }
    try:
        path = _HERE / "test_results_cng2.json"
        path.write_text(_json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:  # pragma: no cover
        print("WARNING: could not write test_results_cng2.json: %r" % (exc,))


_atexit.register(_write_results_atexit)


# --------------------------------------------------------------------------
# Synthetic fixture builders (deterministic; stdlib only)
# --------------------------------------------------------------------------

class _LCG(object):
    """Tiny deterministic PRNG (no external deps, no randomness)."""

    def __init__(self, seed):
        self._s = seed & 0x7FFFFFFF

    def next(self):
        self._s = (1103515245 * self._s + 12345) & 0x7FFFFFFF
        return (self._s / float(1 << 30)) - 1.0  # [-1, 1)


_SEC_PER_HOUR = 3600  # datetime.fromtimestamp takes SECONDS; epoch hours x 3600


def _key(h):
    return _dt.datetime.fromtimestamp(h * _SEC_PER_HOUR, _dt.timezone.utc).strftime("%Y-%m-%dT%H")


def _key_to_int(hk):
    return int(_dt.datetime.strptime(hk, "%Y-%m-%dT%H").replace(tzinfo=_dt.timezone.utc).timestamp()) // _SEC_PER_HOUR


def _iso_s(h):
    return _dt.datetime.fromtimestamp(h * _SEC_PER_HOUR, _dt.timezone.utc).strftime("%Y-%m-%dT%H:00:00Z")


def _s_to_int(s_iso):
    return _key_to_int(s_iso.replace(":00:00Z", ""))


def _make_panels(seed=20260922, n_hours=_N_HOURS):
    """{symbol: {hour_key: bar}} — 3 symbols x n_hours contiguous H1 bars."""
    panels = {}
    for i, sym in enumerate(_UNIVERSE):
        rng = _LCG(seed + 1000 * i)
        price = 100.0 * (1.0 + i)
        bars = {}
        for j in range(n_hours):
            h = _H0 + j
            buy = 1000.0 + 500.0 * (rng.next() + 1.0)
            sell = 1000.0 + 500.0 * (rng.next() + 1.0)
            price = price * (1.0 + 0.005 * rng.next())
            bars[_key(h)] = {
                "buy_quote": buy,
                "sell_quote": sell,
                "quote_total": buy + sell,
                "last_price": price,
            }
        panels[sym] = bars
    return panels


def _make_funding(panels, n_hours=_N_HOURS):
    """Funding evidence in the engine's consumed shape (all grid hours of
    the panel evidenced; rates cycle {-2e-4..2e-4}, hitting exact 0.0)."""
    funding = {}
    for sym in panels:
        rates = {}
        for j in range(0, n_hours, 8):
            rates[_H0 + j] = ((j // 8) % 5 - 2) * 1e-4
        funding[sym] = {"rates": rates, "incidents": []}
    return funding


_GRID_HOURS = [_H0 + j for j in range(8, _N_HOURS - 3, 8)]  # eligible: B-7..B+3 in bounds -> H0+8 .. H0+88
_N_ROWS = len(_GRID_HOURS) * 3  # 11 instants x 3 symbols = 33 rows per arm


def _find(rows, sym, s_hour):
    for r in rows:
        if r["symbol"] == sym and r["S"] == _iso_s(s_hour):
            return r
    raise AssertionError("row not found for (%s, %s)" % (sym, _iso_s(s_hour)))


def _perturb_panels(panels, pred):
    """Deep-copy panels, perturbing flow numerator + last_price on bars
    matching pred (quote_total left untouched so a wrongly-read window
    would change press)."""
    out = {}
    for sym, bars in panels.items():
        nb = {}
        for hk, bar in bars.items():
            if pred(_key_to_int(hk)):
                nb[hk] = {
                    "buy_quote": bar["buy_quote"] + 4096.0,
                    "sell_quote": bar["sell_quote"] - 1024.0,
                    "quote_total": bar["quote_total"],
                    "last_price": bar["last_price"] * 1.31,
                }
            else:
                nb[hk] = dict(bar)
        out[sym] = nb
    return out


def _expect_raises(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    except BaseException as exc:  # noqa: BLE001
        raise AssertionError("expected %s, got %r" % (exc_type.__name__, exc))
    raise AssertionError("expected %s, nothing raised" % (exc_type.__name__,))


_BUILDERS = (
    engine.build_anchor_decisions,
    engine.build_ctl_shiftboundminus2h_decisions,
    engine.build_ctl_fundlevel_decisions,
)


# --------------------------------------------------------------------------
# (a) no-lookahead
# --------------------------------------------------------------------------

@_golden("a1_no_lookahead_sequential_perturbation")
def test_a1_no_lookahead_sequential_perturbation():
    """For each settlement S_k: perturbing ALL bars with open >= S_k - 1h
    (the decision close and later) never changes any field of decisions at
    earlier settlements, and never changes press/d/entry of the decision AT
    S_k (its outcome-side exit may change)."""
    panels = _make_panels()
    funding = _make_funding(panels)
    for builder in _BUILDERS:
        base = builder(panels, funding)
        m0 = {(r["symbol"], r["S"]): r for r in base["rows"]}
        assert len(m0) == _N_ROWS
        for k, s_k in enumerate(_GRID_HOURS):
            pert = _perturb_panels(panels, lambda h, _s=s_k: h >= _s - 1)
            after = builder(pert, funding)
            ma = {(r["symbol"], r["S"]): r for r in after["rows"]}
            assert set(m0) == set(ma), "perturbation changed the decision grid"
            for key, row0 in m0.items():
                s_h = _s_to_int(key[1])
                if s_h < s_k:
                    assert ma[key] == row0, (
                        "decision at earlier settlement %s changed when bars "
                        ">= %s were perturbed" % (key, _iso_s(s_k - 1))
                    )
                elif s_h == s_k:
                    for f in ("press", "d", "entry"):
                        assert ma[key][f] == row0[f], (
                            "decision at %s changed %s when bars >= B-1 were "
                            "perturbed (lookahead)" % (key, f)
                        )


@_golden("a2_press_window_exact_never_reads_future_bars")
def test_a2_press_window_exact_never_reads_future_bars():
    """press equals the hand-computed value over exactly B-4..B-2 (anchor)
    / B-6..B-4 (sham), with absurd flows planted on B-1/B (anchor) and
    B-3..B (sham) that would flip press if any future bar were read."""
    sym = "BTCUSDT"
    panels = _make_panels()
    funding = _make_funding(panels)

    # Anchor at S = H0+16: features 12,13,14h; plant absurd flows on 15,16h.
    s1 = _H0 + 16
    vals = ((300.0, 100.0), (500.0, 200.0), (700.0, 600.0))
    for off, (b, s) in zip((-4, -3, -2), vals):
        panels[sym][_key(s1 + off)] = {
            "buy_quote": b, "sell_quote": s, "quote_total": b + s, "last_price": 111.0,
        }
    for off in (-1, 0):
        panels[sym][_key(s1 + off)] = {
            "buy_quote": 1e12, "sell_quote": 1e-12, "quote_total": 1e12, "last_price": 1e6,
        }
    ds = engine.build_anchor_decisions(panels, funding)
    row = _find(ds["rows"], sym, s1)
    expected = (
        (300.0 - 100.0) + (500.0 - 200.0) + (700.0 - 600.0)
    ) / (
        (300.0 + 100.0) + (500.0 + 200.0) + (700.0 + 600.0)
    )
    assert row["press"] == expected, "anchor press != hand-computed [S-4h, S-1h) value"
    assert row["d"] == 1

    # Sham at S = H0+24: features 18,19,20h; plant absurd flows on 21..24h
    # (B-3..B relative to the true boundary). Sham must read none of them.
    s2 = _H0 + 24
    vals2 = ((200.0, 50.0), (400.0, 100.0), (800.0, 200.0))
    for off, (b, s) in zip((-6, -5, -4), vals2):
        panels[sym][_key(s2 + off)] = {
            "buy_quote": b, "sell_quote": s, "quote_total": b + s, "last_price": 222.0,
        }
    for off in (-3, -2, -1, 0):
        panels[sym][_key(s2 + off)] = {
            "buy_quote": 5e11, "sell_quote": -5e11, "quote_total": 1e12, "last_price": 333.0,
        }
    ds2 = engine.build_ctl_shiftboundminus2h_decisions(panels, funding)
    row2 = _find(ds2["rows"], sym, s2)
    expected2 = (
        (200.0 - 50.0) + (400.0 - 100.0) + (800.0 - 200.0)
    ) / (
        (200.0 + 50.0) + (400.0 + 100.0) + (800.0 + 200.0)
    )
    assert row2["press"] == expected2, "sham press != hand-computed [S-6h, S-3h) value"
    assert row2["d"] == 1


# --------------------------------------------------------------------------
# (b) fills
# --------------------------------------------------------------------------

@_golden("b_fills_exact_entry_exit_and_single_transfer_at_S")
def test_b_fills_exact_entry_exit_and_single_transfer_at_s():
    panels = _make_panels()
    funding = _make_funding(panels)

    ds = engine.build_anchor_decisions(panels, funding)
    n_funded = ds["counts"]["FUNDED"]
    n_transfer = 0
    for r in ds["rows"]:
        if r["status"] != "FUNDED":
            continue
        h = _s_to_int(r["S"])
        assert r["entry"] == panels[r["symbol"]][_key(h - 2)]["last_price"], "entry != last_price(B-2)"
        assert r["exit"] == panels[r["symbol"]][_key(h)]["last_price"], "exit != last_price(B)"
        assert r["rate"] == funding[r["symbol"]]["rates"][h], "rate != pulled settlement rate at S"
        assert r["transfer"] == -r["d"] * r["rate"], "transfer != -d*rate(S)"
        n_transfer += 1
    assert n_transfer == n_funded and n_funded > 0, "exactly one transfer per funded decision, at S only"

    ds_sh = engine.build_ctl_shiftboundminus2h_decisions(panels, funding)
    for r in ds_sh["rows"]:
        h = _s_to_int(r["S"])
        assert r["transfer"] is None, "sham books no transfer (trade entirely before the true boundary)"
        if r["status"] == "FUNDED":
            assert r["entry"] == panels[r["symbol"]][_key(h - 4)]["last_price"], "sham entry != last_price(S-3h bar)"
            assert r["exit"] == panels[r["symbol"]][_key(h - 2)]["last_price"], "sham exit != last_price(S-1h bar)"
            assert h - 2 < h, "sham exit bar opens strictly before the true boundary S"

    ds_fl = engine.build_ctl_fundlevel_decisions(panels, funding)
    for r in ds_fl["rows"]:
        if r["status"] != "FUNDED":
            continue
        h = _s_to_int(r["S"])
        rate = funding[r["symbol"]]["rates"][h]
        assert r["press"] is None, "FUNDLEVEL arm never computes press"
        assert r["d"] == (1 if rate < 0 else -1), "FUNDLEVEL d != -sign(rate(S))"
        assert r["entry"] == panels[r["symbol"]][_key(h - 2)]["last_price"]
        assert r["exit"] == panels[r["symbol"]][_key(h)]["last_price"]
        assert r["transfer"] == -r["d"] * rate


# --------------------------------------------------------------------------
# (c) cost debit
# --------------------------------------------------------------------------

@_golden("c_cost_debit_frozen_tiers_no_zero_cost")
def test_c_cost_debit_frozen_tiers_no_zero_cost():
    # Frozen pre-registered constants (cost_contract.json CNG2 section).
    assert engine.COST_TIERS["1.0"]["taker_bps_per_fill"] == 5.0
    assert engine.COST_TIERS["1.0"]["spread_bps_per_fill"] == 2.0
    assert engine.COST_TIERS["2.0"]["taker_bps_per_fill"] == 10.0
    assert engine.COST_TIERS["2.0"]["spread_bps_per_fill"] == 4.0
    assert engine.PRIMARY_TIER == "2.0"

    panels = _make_panels()
    funding = _make_funding(panels)
    expected_primary = 2.0 * (10.0 + 4.0) / 10000.0
    expected_tier1_bps = 2.0 * (5.0 + 2.0)
    for builder in _BUILDERS:
        ds = builder(panels, funding)
        assert ds["cost_tiers_bps_per_funded_decision"]["2.0"] == 28.0, "tier-2 PRIMARY debit must be 28 bps per funded decision"
        assert ds["cost_tiers_bps_per_funded_decision"]["1.0"] == expected_tier1_bps, "tier-1.0 debit must be 14 bps per funded decision"
        n_funded = 0
        for r in ds["rows"]:
            if r["status"] != "FUNDED":
                continue
            assert r["costs"] == expected_primary, "funded decision must debit 2x(10+4)bps at PRIMARY tier"
            assert r["costs"] > 0.0, "zero-cost fill is forbidden (no silent zero cost)"
            assert r["net"] == r["gross_before_costs"] + (r["transfer"] or 0.0) - r["costs"]
            n_funded += 1
        if builder is engine.build_ctl_fundlevel_decisions:
            # FUNDLEVEL ties: rate(S) exactly 0.0 -> d=0 -> UNFUNDED_SKIP.
            zero_rate_rows = sum(
                1 for sym in _UNIVERSE for h in _GRID_HOURS if funding[sym]["rates"][h] == 0.0
            )
            assert n_funded == _N_ROWS - zero_rate_rows
        else:
            assert n_funded == _N_ROWS, "press arms have no synthetic ties"


# --------------------------------------------------------------------------
# (d) missing-data fail-closed
# --------------------------------------------------------------------------

@_golden("d_missing_data_fail_closed")
def test_d_missing_data_fail_closed():
    panels = _make_panels()
    funding = _make_funding(panels)

    # Missing feature bar B-3 -> UNMEASURED_BAR, never imputed.
    del panels["BTCUSDT"][_key(_H0 + 13)]
    # Missing settlement row -> UNFUNDED_SKIP_NO_SETTLEMENT.
    del funding["ETHUSDT"]["rates"][_H0 + 24]
    # Missing exit bar B -> BLOCKED_MISSING_BAR.
    del panels["SOLUSDT"][_key(_H0 + 32)]
    # Bad fill price (must be finite and > 0) -> BLOCKED_MISSING_BAR.
    panels["BTCUSDT"][_key(_H0 + 38)]["last_price"] = 0.0
    # Exact press tie -> UNFUNDED_SKIP, counted (press recorded as exactly 0).
    for off in (-4, -3, -2):
        bar = panels["ETHUSDT"][_key(_H0 + 48 + off)]
        bar["buy_quote"] = 500.0
        bar["sell_quote"] = 500.0
        bar["quote_total"] = 1000.0

    ds = engine.build_anchor_decisions(panels, funding)
    r1 = _find(ds["rows"], "BTCUSDT", _H0 + 16)
    assert r1["status"] == "UNMEASURED_BAR"
    assert r1["press"] is None and r1["d"] is None and r1["entry"] is None and r1["costs"] is None

    r2 = _find(ds["rows"], "ETHUSDT", _H0 + 24)
    assert r2["status"] == "UNFUNDED_SKIP_NO_SETTLEMENT"
    assert r2["rate"] is None and r2["transfer"] is None and r2["costs"] is None

    r3 = _find(ds["rows"], "SOLUSDT", _H0 + 32)
    assert r3["status"] == "BLOCKED_MISSING_BAR"

    r4 = _find(ds["rows"], "BTCUSDT", _H0 + 40)
    assert r4["status"] == "BLOCKED_MISSING_BAR"

    r5 = _find(ds["rows"], "ETHUSDT", _H0 + 48)
    assert r5["status"] == "UNFUNDED_SKIP"
    assert r5["press"] == 0.0 and r5["d"] == 0 and r5["costs"] is None

    c = ds["counts"]
    assert c["UNMEASURED_BAR"] == 1 and c["UNFUNDED_SKIP_NO_SETTLEMENT"] == 1
    assert c["BLOCKED_MISSING_BAR"] == 2 and c["UNFUNDED_SKIP"] == 1
    assert c["FUNDED"] == _N_ROWS - 5
    assert sum(c.values()) == _N_ROWS

    # BLOCKED_DATA: empty funding series is never fabricated / assumed zero.
    _expect_raises(
        engine.BLOCKED_DATA,
        engine.build_anchor_decisions,
        _make_panels(),
        {"BTCUSDT": {"rates": {}, "incidents": []},
         "ETHUSDT": {"rates": {1: 1e-4}, "incidents": []},
         "SOLUSDT": {"rates": {1: 1e-4}, "incidents": []}},
    )

    # Digest pin verification on the loader (fail-closed, optional pin).
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p_csv = _pth.Path(td) / "panel.csv"
        _write_panel_csv(_make_panels(), p_csv)
        _expect_raises(ValueError, engine.load_panel, p_csv, "0" * 64)
        loaded = engine.load_panel(p_csv, _sha256_of(p_csv))
        assert set(loaded) == set(_UNIVERSE)


def _sha256_of(path):
    import hashlib
    return hashlib.sha256(_pth.Path(path).read_bytes()).hexdigest()


def _write_panel_csv(panels, path):
    lines = ["symbol,hour_utc,buy_quote,sell_quote,quote_total,last_price"]
    for sym in _UNIVERSE:
        for hk in sorted(panels[sym]):
            b = panels[sym][hk]
            lines.append(
                "%s,%s,%r,%r,%r,%r"
                % (sym, hk, b["buy_quote"], b["sell_quote"], b["quote_total"], b["last_price"])
            )
    _pth.Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_funding_json(funding, path):
    raw = {}
    for sym, f in funding.items():
        rows = []
        for h in sorted(f["rates"]):
            rows.append({
                "fundingTime": h * _MS_PER_HOUR + (h % 7),  # observed +ms jitter
                "fundingRate": repr(f["rates"][h]),
            })
        raw[sym] = rows
    _pth.Path(path).write_text(_json.dumps(raw), encoding="utf-8")


# --------------------------------------------------------------------------
# (e) exactly-three-cell enforcement
# --------------------------------------------------------------------------

@_golden("e_exactly_three_cells_registry")
def test_e_exactly_three_cells_registry():
    assert set(cells_registry.EXACTLY_THREE_CELLS) == {
        "SFNG2-A4-P1", "FXNG3-A4-P1", "CNG2-A5-P1",
    }
    assert len(cells_registry.EXACTLY_THREE_CELLS) == 3
    cells_registry.assert_registry_intact()
    for bad in ("CNG2-A5-P2", "CNG2-A5-P1-NEIGH", "sfng2-a4-p1", "", None, "SFNG2-A4-P1 "):
        _expect_raises(cells_registry.UnknownCellError, cells_registry.validate_cell_id, bad)
    for ok in ("SFNG2-A4-P1", "FXNG3-A4-P1", "CNG2-A5-P1"):
        assert cells_registry.validate_cell_id(ok) == ok
    _expect_raises(cells_registry.RegistryFrozenError, cells_registry.register_cell, "NEW-CELL")
    # The engine module asserted the registry at import time; prove it again.
    import importlib
    importlib.reload(engine)
    assert engine.CELL_ID == "CNG2-A5-P1"


# --------------------------------------------------------------------------
# (f) S1 access denial
# --------------------------------------------------------------------------

@_golden("f_s1_access_denial")
def test_f_s1_access_denial():
    for bad_path in ("/data/S1/panels/panel.csv", "/tmp/s1_probe/funding.json",
                     "S1_panel.csv", "dir/s1_funding_history.json"):
        _expect_raises(engine.S1_ACCESS_DENIED, engine.load_panel, bad_path)
        _expect_raises(engine.S1_ACCESS_DENIED, engine.load_funding_series, bad_path)


# --------------------------------------------------------------------------
# (g) zero-parameter-search / fixed public surface
# --------------------------------------------------------------------------

@_golden("g_zero_parameter_search_public_surface")
def test_g_zero_parameter_search_public_surface():
    public = sorted(n for n in vars(engine) if not n.startswith("_"))
    assert public == list(engine.PUBLIC_API), (
        "engine public surface drifted: %s" % (sorted(set(public) ^ set(engine.PUBLIC_API)),)
    )
    assert "PUBLIC_API" in (engine.__doc__ or ""), "public surface must be documented"
    assert engine.ALLOW_SCORE is False, "this lane never sets ALLOW_SCORE"
    assert isinstance(engine.GRID_HOURS_UTC, tuple) and engine.GRID_HOURS_UTC == (0, 8, 16)
    assert engine.UNIVERSE == ("BTCUSDT", "ETHUSDT", "SOLUSDT")

    # Frozen tables are immutable (no tuning knobs).
    def _attempt_item_assignment(mapping, key, value):
        mapping[key] = value  # must raise TypeError on frozen tables

    _expect_raises(TypeError, _attempt_item_assignment, engine.ARMS, "X", {})
    _expect_raises(TypeError, _attempt_item_assignment,
                   engine.COST_TIERS["1.0"], "taker_bps_per_fill", 0.0)

    # Builders take exactly (panels, funding) — no knob parameters.
    for fn in _BUILDERS:
        sig = _inspect.signature(fn)
        assert list(sig.parameters) == ["panels", "funding"], fn.__name__
        assert all(p.default is _inspect.Parameter.empty for p in sig.parameters.values())
    for fn in (engine.load_panel, engine.load_funding_series):
        sig = _inspect.signature(fn)
        assert list(sig.parameters) == ["path", "expected_sha256"]
        assert sig.parameters["expected_sha256"].default is None

    # score_cells refuses prelaunch.
    _expect_raises(engine.REFUSES_PRELAUNCH, engine.score_cells, [1, 2, 3])

    # Folds are NULL in source; the engine emits no fold split and exposes
    # no fold parameter (descriptive calendar thirds are reporting-layer).
    panels = _make_panels()
    funding = _make_funding(panels)
    for builder in _BUILDERS:
        ds = builder(panels, funding)
        assert ds["folds"] is None


# --------------------------------------------------------------------------
# (h) determinism
# --------------------------------------------------------------------------

@_golden("h_determinism_byte_identical_rows")
def test_h_determinism_byte_identical_rows():
    panels = _make_panels()
    funding = _make_funding(panels)
    for builder in _BUILDERS:
        b1 = _json.dumps(builder(panels, funding), sort_keys=True).encode("utf-8")
        b2 = _json.dumps(builder(panels, funding), sort_keys=True).encode("utf-8")
        assert b1 == b2, "two runs over the same panels differ (non-determinism)"

    # Same decision rows when rebuilt through the file loaders (CSV/JSON
    # repr round-trips floats exactly).
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p_csv = _pth.Path(td) / "panel.csv"
        p_fund = _pth.Path(td) / "funding_history.json"
        _write_panel_csv(panels, p_csv)
        _write_funding_json(funding, p_fund)
        panels2 = engine.load_panel(p_csv)
        funding2 = engine.load_funding_series(p_fund)
        for builder in _BUILDERS:
            b_mem = _json.dumps(builder(panels, funding), sort_keys=True).encode("utf-8")
            b_file = _json.dumps(builder(panels2, funding2), sort_keys=True).encode("utf-8")
            assert b_mem == b_file, "loader round-trip changed decision rows"


# --------------------------------------------------------------------------
# smoke: REPLAY_NOT_PROSPECTIVE end-to-end on synthetic 3-symbol panel
# --------------------------------------------------------------------------

@_golden("smoke_replay_not_prospective_synthetic")
def test_smoke_replay_not_prospective():
    panels = _make_panels(seed=777)  # different synthetic book, same laws
    funding = _make_funding(panels)
    ds_a = engine.build_anchor_decisions(panels, funding)
    ds_s = engine.build_ctl_shiftboundminus2h_decisions(panels, funding)
    ds_f = engine.build_ctl_fundlevel_decisions(panels, funding)

    for ds in (ds_a, ds_s, ds_f):
        assert len(ds["rows"]) == _N_ROWS
        assert sum(ds["counts"].values()) == _N_ROWS
        assert "NON_GOVERNING_DIAGNOSTIC" in ds["label"]
        assert "REPLAY_NOT_PROSPECTIVE" in ds["label"]
        assert ds["folds"] is None
        for r in ds["rows"]:
            if r["status"] == "FUNDED":
                assert r["entry"] > 0.0 and r["exit"] > 0.0
                assert r["costs"] > 0.0
                expected_net = r["gross_before_costs"] + (r["transfer"] or 0.0) - r["costs"]
                assert r["net"] == expected_net

    # Warmup law: the panel's first grid instant is INELIGIBLE_WARMUP (its
    # B-7 falls before the panel start); first eligible instant is +8h.
    keys_a = {(r["symbol"], r["S"]) for r in ds_a["rows"]}
    assert (_UNIVERSE[0], _iso_s(_H0)) not in keys_a
    assert (_UNIVERSE[0], _iso_s(_H0 + 8)) in keys_a
    assert len(keys_a) == _N_ROWS

    # The three arms share the identical frozen grid (descriptive
    # comparability), per symbol-major chronological order.
    for ds in (ds_s, ds_f):
        assert {(r["symbol"], r["S"]) for r in ds["rows"]} == keys_a

    # Machinery refuses aggregates: no PnL/expectancy can escape this lane.
    _expect_raises(engine.REFUSES_PRELAUNCH, engine.score_cells, ds_a["rows"])


# --------------------------------------------------------------------------
# runners
# --------------------------------------------------------------------------

def _run_all_plain():
    tests = [
        test_a1_no_lookahead_sequential_perturbation,
        test_a2_press_window_exact_never_reads_future_bars,
        test_b_fills_exact_entry_exit_and_single_transfer_at_s,
        test_c_cost_debit_frozen_tiers_no_zero_cost,
        test_d_missing_data_fail_closed,
        test_e_exactly_three_cells_registry,
        test_f_s1_access_denial,
        test_g_zero_parameter_search_public_surface,
        test_h_determinism_byte_identical_rows,
        test_smoke_replay_not_prospective,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print("PASS  %s" % t.__name__)
        except BaseException as exc:  # noqa: BLE001
            failed += 1
            print("FAIL  %s  ->  %s: %s" % (t.__name__, type(exc).__name__, exc))
    print("\n%d/%d passed" % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    _sys.exit(_run_all_plain())
