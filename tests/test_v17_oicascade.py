"""CRYPTO-V17 A8 OICASCADE lane tests (V17-A6-P2-OICASCADE, selection v3).

Synthetic only: every expected number below is computed BY HAND from the
frozen proposal (research/control/v17_run/d1/a6/proposal_P2.json, blob sha
ff38f2c5c7d617fa2fbf2debff0007f3d73a003f).  No real data file is read
(the frozen spec's endpoint path is repointed at a synthetic fixture in
every staged test), nothing is scored outside ``tmp_path``.

Fixture map (task items a-g):

* (a) H4 bucketing + OI alignment availability law
      - test_h4_bucketing_from_h1_rows            (H1 -> H4 frames: the
      LAST H1 close in the bucket is the close the gate decides on)
      - test_endpoint_availability_no_after_close_influence  (decisions at
      bucket i are invariant to every endpoint value after i)
      - test_endpoint_gap_undefined_substitutes_zero (frozen "undefined=0"
      substitution at a null bucket, in gate AND window)
      - test_irregular_grid_refused               (24h index law fail-closed)
* (b) P10 rolling window boundary
      - test_p10_window_strictly_past_boundary    (window = prior 6 closes,
      <= inclusive, current bucket excluded -- hand-separated hypotheses)
* (c) event gate (both conditions)
      - test_event_gate_requires_both_conditions
* (d) 24h long holding + force-flat at purge
      - test_anchor_suppression_and_rearm         (no pyramiding, re-arm
      after flat: taken events pairwise >= 6 buckets apart)
      - test_anchor_books_24h_and_force_flats_at_purge (e2e: entry t+1 vwap
      -> exit t+6 vwap = the T+24h bucket; purge/fold-edge/grid-end events
      never booked; neighbour span 11)
* (e) sham same-count windows + seed determinism
      - test_sham_determinism_matched_count_and_exclusions (independent
      re-derivation of the default_rng(1717) rejection stream)
      - test_sham_refuses_nonfrozen_seed
      - test_sham_zero_events_mirrors_empty_book
      - test_purged_day_mirror_matches_driver
* (f) frozen falsification rules wired fail-closed
      - test_rules_malformed_blocks_refused_at_load
      - test_control_reproduces_rule_unit         (K1 arithmetic, >= 0.5
      boundary, positive-sign requirement, unevaluable refusal)
      - test_ancestry_rule_carries_frozen_measurement (K3: 0.1899 PASS;
      tampered 0.25 -> DEAD)
      - test_fold_negative_rule_end_to_end_dead   (K2 fires on a crafted
      declining panel; wrapper AND-combines; F0 recorded null, not hidden)
      - test_enforcement_refuses_unevaluable_books
* (g) spec + diag contract load through the frozen paths
      - test_spec_loads_through_driver_schema
      - test_spec_end_to_end_scored_sanitized_and_enforced
      - test_diag_contract_passes_persistability_gate
* (h) warmup-extended endpoint authority (A8 remediation r2)
      - test_loader_warmup_extended_alignment       (series_start_utc +
      bucket_hours: the loader serves the full warmup+S0 array whose last
      len(grid) slots land on the S0 grid -- value at S0 start == cache[714]
      at production geometry; legacy strict-length contract byte-identical
      without the hints; misalignment / short cache / lone hints refused)
      - test_formula_consumes_warmup_slots          (the trailing P10 window
      and the T-24h denominator reach into the pre-S0 slots via the fixed
      warmup offset: the SAME S0 collapse that is honest-warmup None on a
      grid-length cache FIRES on the warmup-extended authority; a warmup
      slot inside the early-S0 window is decision load-bearing; with a
      720-slot warmup the FIRST S0 H4 close has 720 prior closes and is
      decided, never None)
      - test_no_after_close_influence_with_warmup   (the availability law
      holds unchanged on the extended authority: no endpoint value strictly
      after a decision's close can influence it)
"""

from __future__ import annotations

import copy
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from research.control.v17_run.driver import family_registry_v17 as reg
from research.control.v17_run.driver import run_v17_cell as d
from research.governance.diagnostic_persistability import (
    CONDITIONAL_REQUIRED_FIELDS,
    expected_artifacts_from_contract,
    validate_contract,
)

REPO = Path(__file__).resolve().parents[1]
FAMILIES_DIR = REPO / "research/control/v17_run/driver/families"
SPEC_PATH = FAMILIES_DIR / "V17-A6-P2-OICASCADE.spec.json"
CONTRACT_PATH = FAMILIES_DIR / "V17-A6-P2-OICASCADE.diag_contract.json"
S0 = date(2025, 8, 22)  # frozen S0 window start
UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
#: Warmup offset of the corrected real cache: 119 pre-S0 days x 6 H4 = 714
#: slots before S0 ordinal 0 (the spec's series_start_utc 2025-04-25T00:00Z
#: + bucket_hours 4 land the last len(grid) slots exactly on the S0 grid).
WARMUP_SLOTS = 119 * 6

#: Frozen arm parameters exactly as pinned by the spec.
ANCHOR_PARAMS = {
    "oi_percentile": 10.0,
    "window_closes": 720,
    "h4_per_day": 6,
    "holding_buckets": 5,
}
NEIGHBOUR_PARAMS = {
    "oi_percentile": 5.0,
    "window_closes": 720,
    "h4_per_day": 6,
    "holding_buckets": 11,
}
CONTROL_PARAMS = {
    "seed": 1717,
    "oi_percentile": 10.0,
    "window_closes": 720,
    "h4_per_day": 6,
    "holding_buckets": 5,
    "event_exclusion_days": 3,
    "max_draw_attempts": 200000,
}


def _day(i: int) -> str:
    return (S0 + timedelta(days=i)).isoformat()


def _h4_key(i: int) -> str:
    return f"{_day(i // 6)}T{(i % 6) * 4:02d}"


def _h4_rows(prices, symbol: str = "BTCUSDT") -> list:
    """Minimal H4-frame rows (the shape the driver derives and passes)."""
    return [
        {
            "symbol": symbol,
            "hour_utc": _h4_key(i),
            "day_utc": _day(i // 6),
            "last_price": float(prices[i]),
            "vwap": float(prices[i]),
        }
        for i in range(len(prices))
    ]


def _h1_row(idx: int, last: float) -> dict:
    """One complete H1 panel row (all schema columns the driver reads)."""
    day, hour = idx // 24, idx % 24
    return {
        "symbol": "BTCUSDT", "hour_utc": f"{_day(day)}T{hour:02d}",
        "day_utc": _day(day), "n_trades": 10, "buy_count": 5,
        "sell_count": 5, "buy_qty": 10.0, "sell_qty": 10.0,
        "buy_quote": 10.0 * last, "sell_quote": 10.0 * last,
        "quote_total": 20.0 * last, "qty_total": 20.0, "vwap": last,
        "first_price": last, "last_price": last,
        "high_price": last * 1.002, "low_price": last * 0.998,
        "max_trade_quote": 5.0, "sum_qty_squared": 400.0,
        "n_price_moves": 60, "sum_squared_log_ret": 0.001,
        "gap_sum_s": 2.5, "gap_count": 10, "entry_gap_s": 0.3,
        "run_close_dir": "buy", "run_close_len": 3,
        "run_switch_count": 2, "max_run_buy": 5, "max_run_sell": 4,
        "first_ts_ms": 1_755_820_800_000 + idx * 3_600_000,
        "last_ts_ms": 1_755_820_800_000 + idx * 3_600_000 + 3_599_000,
    }


def oi_from_r(r_seq, base: float = 1.0) -> list:
    """Endpoint OI series realizing EXACTLY r_oi[i] = r_seq[i] (forward
    solve of OI[i] = (1 + r_i) * OI[i-6] from OI[0..5] = base), so the
    gate arithmetic is hand-checkable bucket by bucket."""
    oi = [float(base)] * 6 + [0.0] * (len(r_seq) - 6)
    for i in range(6, len(r_seq)):
        oi[i] = (1.0 + float(r_seq[i])) * oi[i - 6]
    return oi


def _gate_params(win: int, percentile: float = 10.0, holding: int = 5) -> dict:
    return {
        "oi_percentile": percentile,
        "window_closes": win,
        "h4_per_day": 6,
        "holding_buckets": holding,
    }


# ------------------------------------------------------------------------- #
# (a) H4 bucketing + OI alignment availability law
# ------------------------------------------------------------------------- #
def test_h4_bucketing_from_h1_rows():
    """The H4 frame the gate decides on: bucket last_price = the LAST H1
    close inside the bucket (the panel row with close_ts <= T), grid keys
    at UTC 00/04/08/12/16/20; a mid-bucket print never decides."""
    h1 = [_h1_row(i, 100.0 + i) for i in range(24)]
    h1[3]["last_price"] = 555.0  # last print of the 00:00 H4 bucket (0..3)
    h1[1]["last_price"] = 111.0  # earlier print in the SAME H4 bucket
    frames, grid = d.derive_frames({"BTCUSDT": h1}, "H4")
    assert grid[0] == f"{_day(0)}T00"
    assert [g[11:13] for g in grid[:6]] == ["00", "04", "08", "12", "16", "20"]
    first = frames["BTCUSDT"][0]
    assert first["last_price"] == 555.0  # LAST close <= the H4 close T
    assert first["day_utc"] == _day(0)


def test_endpoint_availability_no_after_close_influence():
    """Availability law at the formula level: the decision at bucket i is
    a function of endpoint values at buckets <= i ONLY -- rewriting every
    endpoint value AFTER a taken event's close leaves the path up to and
    including that decision byte-identical (no snapshot after the close
    may influence it)."""
    n = 40
    event_i = 30
    prices = [100.0 - 0.5 * i for i in range(n)]  # r24 < 0 everywhere
    r = [0.001 * i for i in range(n)]  # strictly rising: calm never fires
    r[event_i] = -0.5  # engineered OI collapse
    oi = oi_from_r(r)
    panels = {"BTCUSDT": _h4_rows(prices)}
    params = _gate_params(10)
    series = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": oi}
    )["BTCUSDT"]
    assert series[event_i] == 1.0
    # perturb EVERY value strictly after the event close: the path up to
    # and including the event decision is untouched
    tampered = list(oi)
    for j in range(event_i + 1, n):
        tampered[j] = tampered[j] * 3.0 + 7_000_000.0
    series2 = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": tampered}
    )["BTCUSDT"]
    assert series2[: event_i + 1] == series[: event_i + 1]
    # the event's OWN close endpoint is load-bearing: replacing the
    # collapse with a +50% OI print (r_OI = +0.5, far above the window
    # decile) un-fires the event
    no_collapse = list(oi)
    no_collapse[event_i] = no_collapse[event_i - 6] * 1.5
    series3 = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": no_collapse}
    )["BTCUSDT"]
    assert series3[event_i] == 0.0


def test_endpoint_gap_undefined_substitutes_zero():
    """A null endpoint bucket = no admissible snapshot within the +/-30 min
    tolerance -> the frozen substitution 'undefined = 0': the bucket's
    r_OI is 0.0 in the gate AND contributes 0.0 to the trailing window
    (the SUBSTITUTED value enters the machinery -- never a skip)."""
    n = 20
    prices = [100.0 - 0.5 * i for i in range(n)]
    r = [0.02] * n
    r[6:12] = [0.02, 0.04, 0.01, 0.03, 0.05, 0.02]
    r[12] = 0.5  # far above the window p10 -> gate off on the OI side
    oi = oi_from_r(r)
    params = _gate_params(6)
    panels = {"BTCUSDT": _h4_rows(prices)}
    base_series = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": oi}
    )["BTCUSDT"]
    assert base_series[12] == 0.0  # 0.5 <= p10([0.01..0.05]) is false
    # gap the 24h-ago endpoint of bucket 12 (bucket 6) AND every bucket of
    # the window's denominators (0..5): r_OI(12) := 0.0, window r_OI all
    # 0.0 -> p10 = 0.0 and 0.0 <= 0.0 fires with r24 < 0
    gapped = list(oi)
    for j in range(0, 7):
        gapped[j] = None
    gap_series = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": gapped}
    )["BTCUSDT"]
    # first decision (6) fires on the substituted zeros and suppresses
    # 7..11; at 12 the book has re-armed and 0.0 <= p10(0.0) fires again
    assert gap_series[6] == 1.0
    assert all(gap_series[i] == 0.0 for i in range(7, 12))
    assert gap_series[12] == 1.0
    # a SINGLE missing denominator (bucket 6) with an otherwise intact
    # window: r_OI(12) := 0.0 <= p10([0.0, 0.04, 0.01, 0.03, 0.05, 0.02])
    # = 0.005 -> fires; the substituted value, not a skip, decided it
    one_gap = list(oi)
    one_gap[6] = None
    one_gap_series = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": one_gap}
    )["BTCUSDT"]
    assert one_gap_series[6] == 1.0  # its own numerator gapped -> 0.0 <= 0.0
    assert one_gap_series[12] == 1.0


def test_irregular_grid_refused():
    """The 24h endpoint is the value 6 buckets back; a non-4h grid breaks
    that index law -> fail closed."""
    rows = _h4_rows([100.0] * 12)
    rows[7]["hour_utc"] = f"{_day(1)}T03"  # off-grid bucket key
    oi = [1000.0] * 12
    with pytest.raises(ValueError, match="4h UTC grid"):
        reg.resolve("OICASCADE.anchor")(
            {"BTCUSDT": rows}, _gate_params(6), endpoint={"BTCUSDT": oi},
        )


# ------------------------------------------------------------------------- #
# (b) P10 rolling window boundary (hand-separated hypotheses)
# ------------------------------------------------------------------------- #
def test_p10_window_strictly_past_boundary():
    """window_closes = 6, decision at i = 12; the window is the six
    PRIOR closes r_oi[6..11] = [0.02, 0.01, 0.00, -0.01, 0.03, 0.05] ->
    p10 = numpy.percentile(..., 10) = -0.005 (linear interpolation).
    r_oi[12] == -0.005 fires (<= inclusive); r_oi[12] == -0.004 does NOT
    (strictly above).  The current bucket is EXCLUDED from its own
    window: including it (r_oi[12] = -0.005 inside the window) would give
    p10 = -0.007 and NOT fire -- the fire/no-fire outcomes separate the
    two hypotheses.  Prices rise through i = 11 so the early buckets
    (whose windows contain availability-substituted zeros) can never
    fire; only i = 12 has r24 < 0."""
    w = [0.02, 0.01, 0.00, -0.01, 0.03, 0.05]
    expected_p10 = float(np.percentile(w, 10.0))
    assert expected_p10 == pytest.approx(-0.005)
    prices = [100.0 + 2.0 * i for i in range(12)] + [100.0, 97.0]
    assert prices[12] < prices[6]  # r24(12) < 0: the event bucket
    assert all(
        prices[i] > prices[i - 6] for i in range(6, 12)
    )  # r24 > 0 on every earlier fireable bucket (price-side guard)

    def series_with(r12: float) -> list:
        oi = [1.0] * 6 + [1.0 + v for v in w]      # r_oi[6..11] = w exactly
        oi.append((1.0 + r12) * oi[6])             # r_oi[12] = r12 exactly
        oi.append(oi[12] * 1.04)                   # bucket 13 (irrelevant)
        return reg.resolve("OICASCADE.anchor")(
            {"BTCUSDT": _h4_rows(prices)}, _gate_params(6),
            endpoint={"BTCUSDT": oi},
        )["BTCUSDT"]

    s = series_with(-0.005)  # exactly at the strictly-past threshold
    assert s[:6] == [None] * 6  # honest warmup before the window exists
    assert s[6:12] == [0.0] * 6  # price-side guard: rising r24, no events
    assert s[12] == 1.0  # fires: -0.005 <= -0.005 (and current NOT in window)
    s = series_with(-0.004)  # strictly above the threshold
    assert s[12] == 0.0


# ------------------------------------------------------------------------- #
# (c) event gate: BOTH conditions required
# ------------------------------------------------------------------------- #
def test_event_gate_requires_both_conditions():
    """r baseline strictly increasing -> the OI-side gate never fires on a
    calm bucket (r[i] > p10 of its own past window) and fires exactly at
    the engineered collapse; a rising price panel never fires at all."""
    n = 16
    falling = [100.0 - 1.0 * i for i in range(n)]
    rising = [100.0 + 1.0 * i for i in range(n)]
    r = [0.001 * i for i in range(n)]
    r[8] = -0.5  # THE collapse
    oi = oi_from_r(r)
    params = _gate_params(6)
    down = reg.resolve("OICASCADE.anchor")(
        {"BTCUSDT": _h4_rows(falling)}, params, endpoint={"BTCUSDT": oi}
    )["BTCUSDT"]
    assert down[:6] == [None] * 6
    fired = {i for i, v in enumerate(down) if v == 1.0}
    assert fired == {8}  # collapse AND r24 < 0: the ONLY event
    assert down[9] == 0.0  # suppressed (book open), not None
    up = reg.resolve("OICASCADE.anchor")(
        {"BTCUSDT": _h4_rows(rising)}, params, endpoint={"BTCUSDT": oi}
    )["BTCUSDT"]
    assert up[8] == 0.0  # collapse present but r24 > 0: gate off
    assert all(v == 0.0 for v in up[6:])
    # and a calm-OI falling-price world with the collapse removed: no
    # event anywhere (the OI side is exactly the frozen decile comparison)
    r_calm = [0.001 * i for i in range(n)]
    oi_calm = oi_from_r(r_calm)
    calm = reg.resolve("OICASCADE.anchor")(
        {"BTCUSDT": _h4_rows(falling)}, params, endpoint={"BTCUSDT": oi_calm}
    )["BTCUSDT"]
    assert all(v == 0.0 for v in calm[6:])


# ------------------------------------------------------------------------- #
# (d) 24h long holding + force-flat (formula + driver)
# ------------------------------------------------------------------------- #
def test_anchor_suppression_and_rearm():
    """One position per symbol: an event at t suppresses events at
    t+1..t+5 (ignored, series 0.0) and the book re-arms at t+6 (the exit
    fill bucket) -- taken events are pairwise >= 6 buckets apart."""
    n = 24
    prices = [100.0 - 1.0 * i for i in range(n)]
    r = [0.001 * i for i in range(n)]
    for c in (12, 15, 18):  # +0, +3 (suppressed), +6 (re-armed)
        r[c] = -0.5
    oi = oi_from_r(r)
    series = reg.resolve("OICASCADE.anchor")(
        {"BTCUSDT": _h4_rows(prices)}, _gate_params(6),
        endpoint={"BTCUSDT": oi},
    )["BTCUSDT"]
    assert series[12] == 1.0
    assert series[15] == 0.0  # fired while open: IGNORED (not None)
    assert series[18] == 1.0  # flat again at the exit fill: re-armed
    taken = [i for i, v in enumerate(series) if v == 1.0]
    assert taken == [12, 18]
    assert all(b - a >= 6 for a, b in zip(taken, taken[1:]))


def test_purged_day_mirror_matches_driver():
    """The sham's purge-zone exclusion mirrors the driver's frozen purge
    exactly (on 365 days: the frozen {120, 121, 242, 243})."""
    for n_days in (30, 100, 365):
        assert reg._oic_purged_bucket_days(n_days) == d.purged_day_indices(
            n_days
        )
    assert reg._oic_purged_bucket_days(365) == frozenset({120, 121, 242, 243})


# ------------------------------------------------------------------------- #
# staging helpers: synthetic H1 panels + endpoint series through the REAL
# loader path (csv + sha manifest + endpoint json)
# ------------------------------------------------------------------------- #
def _write_oic_csv(directory: Path, symbol: str, n_days: int) -> None:
    path = directory / d.PANEL_FILE.format(symbol=symbol)
    lines = [",".join(d.H1_SCHEMA)]
    for idx in range(n_days * 24):
        day, hour = idx // 24, idx % 24
        # gently declining: every 24h long loses (gross -4.8bp < costs) and
        # prices stay positive over the full window
        last = 100.0 * (1.0 - 0.00002 * idx)
        row = {
            "symbol": symbol, "hour_utc": f"{_day(day)}T{hour:02d}",
            "day_utc": _day(day), "n_trades": 10, "buy_count": 5,
            "sell_count": 5, "buy_qty": 10.0, "sell_qty": 10.0,
            "buy_quote": 10.0 * last, "sell_quote": 10.0 * last,
            "quote_total": 20.0 * last, "qty_total": 20.0, "vwap": last,
            "first_price": last, "last_price": last,
            "high_price": last * 1.002, "low_price": last * 0.998,
            "max_trade_quote": 5.0, "sum_qty_squared": 400.0,
            "n_price_moves": 60, "sum_squared_log_ret": 0.001,
            "gap_sum_s": 2.5, "gap_count": 10, "entry_gap_s": 0.3,
            "run_close_dir": "buy", "run_close_len": 3,
            "run_switch_count": 2, "max_run_buy": 5, "max_run_sell": 4,
            "first_ts_ms": 1_755_820_800_000 + idx * 3_600_000,
            "last_ts_ms": 1_755_820_800_000 + idx * 3_600_000 + 3_599_000,
        }
        lines.append(",".join(
            repr(row[c]) if isinstance(row[c], float) else str(row[c])
            for c in d.H1_SCHEMA
        ))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _synthetic_endpoint(n_days: int, collapse_buckets) -> dict:
    """Reduced OI series per symbol, WARMUP-EXTENDED exactly as the frozen
    spec's alignment hints describe (WARMUP_SLOTS pre-S0 slots + n_days x 6
    S0 slots; ``collapse_buckets`` are S0-ordinals, mapped behind the
    warmup offset): a STRICTLY INCREASING r_OI baseline (r = 1e-5 x slot
    index -> the current r is always above its own window's decile, so the
    calm book can never fire -- a stationary series would fire ~10% of
    buckets by decile construction and saturate the sham's +/-3-day
    exclusion space) plus engineered collapses (r_OI(c) = -0.5, far under
    any window P10).  Events are therefore EXACTLY the engineered set, per
    symbol."""
    oi = {}
    total = WARMUP_SLOTS + n_days * 6
    for sym in UNIVERSE:
        series = [1_000_000.0] * 6
        for i in range(6, total):
            r = (
                -0.5
                if (i - WARMUP_SLOTS) in collapse_buckets
                else 1e-5 * i
            )
            series.append(series[i - 6] * (1.0 + r))
        oi[sym] = series
    return oi


def _stage(tmp_path: Path, spec: d.FamilySpec, n_days: int, collapse_buckets):
    panel_dir = tmp_path / "staging"
    for sym in UNIVERSE:
        _write_oic_csv(panel_dir, sym, n_days)
    endpoint = _synthetic_endpoint(n_days, collapse_buckets)
    endpoint_path = panel_dir / "oi_series_reduced_synthetic.json"
    endpoint_path.write_text(json.dumps(endpoint), encoding="utf-8")
    doc = {
        "schema": "v17_run_artifact_v1",
        "artifact": "staging_panel_manifest",
        "symbols": list(UNIVERSE),
        "window": [_day(0), _day(n_days - 1)],
        "panel_sha256": {
            sym: d.sha256_bytes(
                (panel_dir / d.PANEL_FILE.format(symbol=sym)).read_bytes()
            )
            for sym in UNIVERSE
        },
        "hourly_rows": {sym: n_days * 24 for sym in UNIVERSE},
    }
    (panel_dir / "panel_manifest_v17_published.json").write_text(
        json.dumps(doc, sort_keys=True, indent=1), encoding="utf-8")
    manifest = d.load_manifest(
        panel_dir / "panel_manifest_v17_published.json")
    manifest["_panel_dir"] = panel_dir
    # repoint the frozen spec's endpoint paths at the synthetic fixture
    for arm in spec.arms:
        arm.exposure["endpoint_series"]["path"] = str(endpoint_path)
    return manifest


def _loaded_spec():
    _, (spec,) = d.load_selection(SPEC_PATH)
    return spec


# ------------------------------------------------------------------------- #
# (d, e2e) 24h holding + force-flat on the real driver path
# ------------------------------------------------------------------------- #
def test_anchor_books_24h_and_force_flats_at_purge(tmp_path, monkeypatch):
    """250-day world on the warmup-extended authority (the staged endpoint
    carries the spec's 714 pre-S0 slots, so the gate is decided from S0
    ordinal 6): engineered collapses in F1 (day 130) and F2 (day 200) book
    6-bucket round trips (entry t+1 vwap -> exit t+6 vwap = the T+24h
    bucket); no booked trip touches a purged fold-boundary day or escapes
    its fold; an event at the last H4 close never books (grid-end
    force-flat); the neighbour's 48h holding books 11-bucket trips."""
    spec = _loaded_spec()
    collapse = [130 * 6 + 2, 200 * 6 + 4]
    manifest = _stage(tmp_path, spec, n_days=250, collapse_buckets=collapse)
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    h1 = d.load_panels(d.repo_root(), manifest, spec.universe)
    state = d.compute_family(spec, h1, base_dir=tmp_path, allow_example=False)
    folds, purged = d.build_folds(250)
    trips = state["arms"]["anchor"]["trips"]
    assert trips, "engineered collapses must book"
    for trip in trips:
        assert trip["exit_bucket"] - trip["entry_bucket"] == 5  # 24h span
        assert trip["position"] == 1.0  # long-only book
    # the ONLY events are the engineered collapses: exactly one booking
    # per symbol per collapse; the formula decides at the collapse close c
    # and the driver's lag-0 convention books it at the position bucket
    # c+1 (= the entry bucket, the next H4 bucket whose vwap fills)
    for c in collapse:
        for sym in UNIVERSE:
            assert any(
                t["symbol"] == sym and t["decision_bucket"] == c + 1
                for t in trips
            ), f"engineered collapse {c} missing for {sym}"
    assert sorted(t["decision_bucket"] for t in trips) == sorted(
        [c + 1 for c in collapse for _ in UNIVERSE]
    )
    # force-flat proof on every booked trip (the driver's purge law)
    fold_by_day = {day: f for f in folds for day in f.member_days}
    for trip in trips:
        decision_day = state["bucket_day"][trip["decision_bucket"]]
        fold = fold_by_day[decision_day]
        assert trip["fold_label"] == fold.label
        window_days = {
            state["bucket_day"][b]
            for b in range(trip["entry_bucket"], trip["exit_bucket"] + 1)
        }
        assert not (window_days & set(purged))
        assert window_days <= set(fold.member_days)
    # grid-end force-flat: a collapse at the LAST H4 close is taken in the
    # series but never books (the exit would run off the grid)
    end_c = 250 * 6 - 1
    manifest2 = _stage(
        tmp_path / "end", spec, n_days=250, collapse_buckets=[end_c]
    )
    monkeypatch.setattr(d, "PANEL_DIR", manifest2["_panel_dir"])
    h1b = d.load_panels(d.repo_root(), manifest2, spec.universe)
    state_b = d.compute_family(
        spec, h1b, base_dir=tmp_path / "end", allow_example=False
    )
    assert state_b["arms"]["anchor"]["trips"] == []
    # neighbour span: the 48h holding books 11-bucket round trips
    nb_trips = state["arms"]["neighbour"]["trips"]
    assert nb_trips, "neighbour must book on the same collapses"
    for trip in nb_trips:
        assert trip["exit_bucket"] - trip["entry_bucket"] == 11
    # control windows are duration-matched 24h books too
    for trip in state["arms"]["control"]["trips"]:
        assert trip["exit_bucket"] - trip["entry_bucket"] == 5


# ------------------------------------------------------------------------- #
# (e) sham: same-count windows + seed determinism (independent re-derivation)
# ------------------------------------------------------------------------- #
def _reference_gate(prices, oi, win: int, percentile: float):
    """Independent reference implementation of the frozen gate (written
    from the proposal text, not the registry code): returns (taken, all
    fired events) index lists."""
    n = len(prices)
    r_oi = [
        (oi[i] / oi[i - 6] - 1.0)
        if i >= 6 and oi[i] is not None and oi[i - 6] is not None else 0.0
        for i in range(n)
    ]
    taken, events = [], []
    last = None
    for i in range(win, n):
        p10 = float(np.percentile(r_oi[i - win: i], percentile))
        r24 = prices[i] / prices[i - 6] - 1.0
        if r_oi[i] <= p10 and r24 < 0.0:
            events.append(i)
            if last is None or i - last > 5:
                taken.append(i)
                last = i
    return taken, events


def test_sham_determinism_matched_count_and_exclusions():
    """The sham is a pure function of seed 1717 and the symbol's true
    event set: matched count, uniform draws over S0, purge-zone and +/-3d
    and 24h-overlap exclusions with redraw-on-collision -- re-derived BY
    HAND from an independent gate implementation."""
    n = 150  # 25 days
    win = 12
    prices = [100.0 - 0.5 * i for i in range(n)]
    r = [0.001 * i for i in range(n)]  # increasing: calm never fires
    for c in (30, 70, 110):
        r[c] = -0.5
    oi = oi_from_r(r)
    panels = {"BTCUSDT": _h4_rows(prices)}
    params = {
        "seed": 1717,
        "oi_percentile": 10.0,
        "window_closes": win,
        "h4_per_day": 6,
        "holding_buckets": 5,
        "event_exclusion_days": 3,
        "max_draw_attempts": 200000,
    }
    control = reg.resolve("OICASCADE.control")(
        panels, params, endpoint={"BTCUSDT": oi}
    )["BTCUSDT"]
    again = reg.resolve("OICASCADE.control")(
        panels, params, endpoint={"BTCUSDT": oi}
    )["BTCUSDT"]
    assert control == again  # deterministic: pure function of the seed
    taken, events = _reference_gate(prices, oi, win, 10.0)
    assert events == [30, 70, 110] and taken == events  # fixture sanity
    starts = [i for i, v in enumerate(control) if v == 1.0]
    assert len(starts) == len(taken) == 3  # SAME COUNT of 24h windows
    assert all(v in (0.0, 1.0) for v in control)  # no warmup None
    # independent re-derivation of the frozen rejection stream
    n_days = n // 6
    purged_days = d.purged_day_indices(n_days)
    day_of = [i // 6 for i in range(n)]
    rng = np.random.default_rng(1717)
    expected = []
    attempts = 0
    while len(expected) < len(taken):
        attempts += 1
        assert attempts <= 200000 * len(taken)
        k = int(rng.integers(0, n))
        if day_of[k] in purged_days:
            continue  # +/-1-day fold purge zones
        if any(abs(k - e) <= 18 for e in events):  # +/-3 days = 18 buckets
            continue
        if any(abs(k - a) < 6 for a in expected):  # 24h window overlap
            continue
        expected.append(k)
    assert starts == expected
    # the structural properties hold of the result itself
    assert all(b - a >= 6 for a, b in zip(starts, starts[1:]))
    for s in starts:
        assert all(abs(s - e) > 18 for e in events)
        assert day_of[s] not in purged_days
    # a different true-event set draws a different book, still matched
    r2 = list(r)
    r2[30] = 0.03  # un-collapse bucket 30 (above every past window p10)
    oi2 = oi_from_r(r2)
    control2 = reg.resolve("OICASCADE.control")(
        panels, params, endpoint={"BTCUSDT": oi2}
    )["BTCUSDT"]
    taken2, _ = _reference_gate(prices, oi2, win, 10.0)
    assert [i for i, v in enumerate(control2) if v == 1.0] != starts
    assert sum(1 for v in control2 if v == 1.0) == len(taken2) == 2


def test_sham_refuses_nonfrozen_seed():
    prices = [100.0 - 0.5 * i for i in range(60)]
    r = [0.001 * i for i in range(60)]
    r[20] = -0.5
    oi = oi_from_r(r)
    params = {
        "seed": 1718,
        "oi_percentile": 10.0,
        "window_closes": 12,
        "h4_per_day": 6,
        "holding_buckets": 5,
    }
    with pytest.raises(ValueError, match="1717"):
        reg.resolve("OICASCADE.control")(
            {"BTCUSDT": _h4_rows(prices)}, params,
            endpoint={"BTCUSDT": oi},
        )


def test_sham_zero_events_mirrors_empty_book():
    """No anchor windows -> the matched sham is the empty book (a scored
    cell would refuse the whole family as vacuous, never fake windows)."""
    prices = [100.0 + 0.5 * i for i in range(60)]  # rising: no events
    r = [0.001 * i for i in range(60)]
    oi = oi_from_r(r)
    params = {
        "seed": 1717,
        "oi_percentile": 10.0,
        "window_closes": 12,
        "h4_per_day": 6,
        "holding_buckets": 5,
    }
    control = reg.resolve("OICASCADE.control")(
        {"BTCUSDT": _h4_rows(prices)}, params, endpoint={"BTCUSDT": oi}
    )["BTCUSDT"]
    assert control == [0.0] * 60


# ------------------------------------------------------------------------- #
# (f) frozen falsification rules wired fail-closed
# ------------------------------------------------------------------------- #
OIC_RULES = {
    "control_reproduces": {
        "rule": "falsification_rule (K1), verbatim",
        "book": "anchor",
        "control_book": "control",
        "tier": "T2.0",
        "sham_expectancy_ratio": 0.5,
        "action": "mark_dead",
    },
    "fold_negative_majority": {
        "rule": "falsification_rule (K2), verbatim",
        "book": "anchor",
        "tier": "T2.0",
        "max_negative_folds": 2,
        "folds_total": 3,
        "action": "mark_dead",
    },
    "ancestry_veto_measured": {
        "rule": "falsification_rule (K3), verbatim",
        "source_artifact": "research/control/v17_run/d2/"
                           "d2_novelty_endpoint_v17.json",
        "measured_proxy": "panel_daily:ret (spearman)",
        "measured_pooled_abs_rho": 0.1899,
        "veto_threshold": 0.2,
        "frozen_verdict": "PASS",
        "action": "mark_dead",
    },
}

OIC_SPEC_BASE = {
    "family_id": "SYNTH-OIC-RULES", "clock": "H4",
    "universe": ["BTCUSDT"],
    "entry": {"lag_buckets": 0}, "exit": {"holding_buckets": 5},
    "fill_price": "vwap",
    "arms": [
        {"arm_id": "anchor", "kind": "anchor",
         "exposure": {"type": "panel_formula",
                      "formula_id": "OICASCADE.anchor", "params": {}}},
        {"arm_id": "neighbour", "kind": "neighbour",
         "exposure": {"type": "panel_formula",
                      "formula_id": "OICASCADE.neighbour", "params": {}}},
        {"arm_id": "control", "kind": "control",
         "exposure": {"type": "panel_formula",
                      "formula_id": "OICASCADE.control", "params": {}}},
    ],
}


def test_rules_malformed_blocks_refused_at_load():
    def parsed(block):
        doc = copy.deepcopy(OIC_SPEC_BASE)
        doc["frozen_falsification_rules"] = block
        return d._parse_family(doc, base_dir=Path("/"))

    spec = parsed(copy.deepcopy(OIC_RULES))
    assert set(spec.frozen_rules) == set(OIC_RULES)
    bad_blocks = []
    # book-based rules: book/tier/action shape mutations refuse
    for rid in ("control_reproduces", "fold_negative_majority"):
        for field, bad in (
            ("book", "control"), ("tier", "T9.9"), ("action", "warn"),
        ):
            broken = copy.deepcopy(OIC_RULES)
            broken[rid][field] = bad
            bad_blocks.append(broken)
    # the measured-veto rule: action/source/threshold-shape mutations
    for field, bad in (("action", "warn"),):
        broken = copy.deepcopy(OIC_RULES)
        broken["ancestry_veto_measured"][field] = bad
        bad_blocks.append(broken)
    broken = copy.deepcopy(OIC_RULES)
    broken["control_reproduces"]["control_book"] = "anchor"
    bad_blocks.append(broken)
    broken = copy.deepcopy(OIC_RULES)
    broken["control_reproduces"]["sham_expectancy_ratio"] = 0.75
    bad_blocks.append(broken)
    broken = copy.deepcopy(OIC_RULES)
    broken["control_reproduces"].pop("sham_expectancy_ratio")
    bad_blocks.append(broken)
    broken = copy.deepcopy(OIC_RULES)
    broken["fold_negative_majority"]["max_negative_folds"] = 0
    bad_blocks.append(broken)
    broken = copy.deepcopy(OIC_RULES)
    broken["fold_negative_majority"]["folds_total"] = 4
    bad_blocks.append(broken)
    broken = copy.deepcopy(OIC_RULES)
    broken["ancestry_veto_measured"]["measured_pooled_abs_rho"] = 1.5
    bad_blocks.append(broken)
    broken = copy.deepcopy(OIC_RULES)
    broken["ancestry_veto_measured"]["veto_threshold"] = 0.0
    bad_blocks.append(broken)
    broken = copy.deepcopy(OIC_RULES)
    broken["ancestry_veto_measured"]["frozen_verdict"] = "VETO_MEASURED"
    bad_blocks.append(broken)
    broken = copy.deepcopy(OIC_RULES)
    broken["ancestry_veto_measured"].pop("source_artifact")
    bad_blocks.append(broken)
    bad_blocks.append({"some_novel_rule": {"action": "mark_dead"}})
    bad_blocks.append({})
    for bad in bad_blocks:
        with pytest.raises(d.DriverError):
            parsed(bad)


def _fake_state(anchor_pnl, control_pnl, trips=4):
    """Minimal state for the enforcement arithmetic (real Fold objects,
    real BookResult instances)."""
    metrics = d.ArmMetrics(
        expectancy=0.0, pf=1.0, mdd=0.0, series_len=10,
        positive_folds=0, fold_concentration=0.0,
    )

    def book(pnl):
        return d.BookResult(
            tier="T2.0", pnl=pnl, gross_pnl=pnl, cost_fills_total=0.0,
            cost_holding_terms_total=0.0, n_fills=2 * trips,
            n_round_trips=trips,
        )

    return {
        "arms": {
            "anchor": {
                "metrics": metrics,
                "books": {"T2.0": book(anchor_pnl)},
            },
            "control": {
                "metrics": metrics,
                "books": {"T2.0": book(control_pnl)},
            },
        },
        "folds": d.build_folds(30)[0],
    }


def _rules_spec():
    doc = copy.deepcopy(OIC_SPEC_BASE)
    doc["frozen_falsification_rules"] = copy.deepcopy(OIC_RULES)
    return d._parse_family(doc, base_dir=Path("/"))


def test_control_reproduces_rule_unit():
    """K1 arithmetic: dead iff the sham is POSITIVE and |sham exp| >= 0.5 x
    |anchor exp| (pooled after-cost expectancy = pnl / trips)."""
    spec = _rules_spec()
    # anchor +0.004/4 = +0.001; control +0.003/4 = +0.00075 >= 0.0005 -> DEAD
    rec = d._enforce_control_reproduces_rule(
        spec, _fake_state(anchor_pnl=0.004, control_pnl=0.003)
    )
    assert rec["verdict"] == "DEAD_FROZEN_RULE_CONTROL_REPRODUCES"
    assert rec["family_alive"] is False
    assert rec["anchor_expectancy"] == pytest.approx(0.001)
    assert rec["control_expectancy"] == pytest.approx(0.00075)
    # exactly at the frozen ratio: >= is inclusive -> DEAD
    rec = d._enforce_control_reproduces_rule(
        spec, _fake_state(anchor_pnl=0.004, control_pnl=0.002)
    )
    assert rec["verdict"] == "DEAD_FROZEN_RULE_CONTROL_REPRODUCES"
    # positive but below half the anchor: PASS
    rec = d._enforce_control_reproduces_rule(
        spec, _fake_state(anchor_pnl=0.004, control_pnl=0.001)
    )
    assert rec["verdict"] == "PASS" and rec["family_alive"] is True
    # negative sham never "reproduces" (the same-positive-sign requirement)
    rec = d._enforce_control_reproduces_rule(
        spec, _fake_state(anchor_pnl=0.004, control_pnl=-0.003)
    )
    assert rec["verdict"] == "PASS"
    # a zero-trip control book is UNEVALUABLE -> hard refusal
    state = _fake_state(0.004, 0.003)
    state["arms"]["control"]["books"]["T2.0"].n_round_trips = 0
    with pytest.raises(d.DriverError, match="fail closed"):
        d._enforce_control_reproduces_rule(spec, state)


def test_ancestry_rule_carries_frozen_measurement():
    """K3/G12: the D2 measurement is carried FROZEN (0.1899 <= 0.20 ->
    PASS, never re-measured in-cell); a doctored record cannot pass."""
    spec = _rules_spec()
    rec = d._enforce_ancestry_rule(spec, {"arms": {}})
    assert rec["rule_id"] == "ancestry_veto_measured"
    assert rec["verdict"] == "PASS" and rec["family_alive"] is True
    assert rec["measured_pooled_abs_rho"] == 0.1899
    assert rec["veto_threshold"] == 0.2
    assert "NOT re-measured" in rec["note"]
    # tampered measurement above the frozen threshold: mechanically DEAD
    doc = copy.deepcopy(OIC_SPEC_BASE)
    rules = copy.deepcopy(OIC_RULES)
    rules["ancestry_veto_measured"]["measured_pooled_abs_rho"] = 0.25
    doc["frozen_falsification_rules"] = rules
    spec2 = d._parse_family(doc, base_dir=Path("/"))
    rec2 = d._enforce_ancestry_rule(spec2, {"arms": {}})
    assert rec2["verdict"] == "DEAD_FROZEN_RULE_ANCESTRY_VETO"
    assert rec2["family_alive"] is False


def test_fold_negative_rule_end_to_end_dead(tmp_path, monkeypatch):
    """K2 on the real path: a crafted declining panel makes EVERY 24h long
    lose, so both populated folds (F1: 3 trips, F2: 3 trips -- exactly the
    engineered events, all negative) are negative -> the family is MARKED
    DEAD via the AND-combined wrapper while K1 (negative sham) and K3
    (frozen 0.1899) PASS; F0 has zero scored events (the fixture's calm
    OI baseline fires nowhere in days 0..119 even though the
    warmup-extended authority now decides every early-S0 bucket) and is
    recorded NULL -- disclosed, never counted hidden-negative."""
    spec = _loaded_spec()
    collapse = [130 * 6 + 2, 200 * 6 + 4]
    manifest = _stage(tmp_path, spec, n_days=250, collapse_buckets=collapse)
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    out = tmp_path / "out"
    result = d.run_family(
        spec, manifest, d.repo_root(), out,
        sanitized=False, base_dir=tmp_path, code_freeze_sha="0" * 40,
    )
    enf = result["frozen_rule_enforcement"]  # MUST exist: fail-closed
    assert enf["rule_id"] == "frozen_falsification_rules"
    assert enf["fail_closed"] is True
    assert set(enf["rules"]) == {
        "control_reproduces", "fold_negative_majority", "ancestry_veto_measured"
    }
    k2 = enf["rules"]["fold_negative_majority"]
    assert k2["book"] == "anchor" and k2["tier"] == "T2.0"
    assert k2["per_fold_population"] == {"F0": 0, "F1": 3, "F2": 3}
    assert k2["per_fold_expectancy"]["F0"] is None
    assert k2["per_fold_expectancy"]["F1"] < 0.0
    assert k2["per_fold_expectancy"]["F2"] < 0.0
    assert k2["unevaluable_folds"] == ["F0"]
    assert k2["negative_folds"] == 2
    assert k2["verdict"] == "DEAD_FROZEN_RULE_FOLD_NEGATIVE"
    k1 = enf["rules"]["control_reproduces"]
    assert k1["verdict"] == "PASS"  # negative sham: no reproduction
    assert k1["control_expectancy"] < 0.0
    assert k1["control_round_trips"] > 0
    k3 = enf["rules"]["ancestry_veto_measured"]
    assert k3["verdict"] == "PASS" and k3["measured_pooled_abs_rho"] == 0.1899
    assert enf["verdict"] == "DEAD_FROZEN_RULES"
    assert enf["family_alive"] is False
    assert enf["dead_rules"] == ["fold_negative_majority"]
    # the pre-registered death is a legal REJECT path: diagnostics emitted
    assert result["arms"]["anchor"]["kernel"]["n_round_trips"] == 6


def test_enforcement_refuses_unevaluable_books():
    spec = _rules_spec()
    with pytest.raises(d.DriverError, match="fail closed"):
        d.enforce_frozen_rules(spec, {"arms": {}})
    empty = copy.deepcopy(OIC_SPEC_BASE)
    empty["family_id"] = "SYNTH-NORULES"
    spec_norules = d._parse_family(empty, base_dir=Path("/"))
    with pytest.raises(d.DriverError, match="without a"):
        d.enforce_frozen_rules(spec_norules, {"arms": {}})


# ------------------------------------------------------------------------- #
# (g) frozen spec + diag contract load through the driver/governance paths
# ------------------------------------------------------------------------- #
def test_spec_loads_through_driver_schema():
    cycle, (spec,) = d.load_selection(SPEC_PATH)
    assert cycle == "CRYPTO-V17"
    assert (spec.family_id, spec.clock, spec.universe) == (
        "V17-A6-P2-OICASCADE", "H4", UNIVERSE)
    # frozen fills: decision at the H4 close T, lag-0 fill at the NEXT H4
    # bucket's published vwap, exit at the T+24h bucket vwap => span 5
    assert (spec.lag_buckets, spec.holding_buckets, spec.fill_price) == (
        0, 5, "vwap")
    assert spec.booking == "event"
    by_kind = {arm.kind: arm for arm in spec.arms}
    assert {arm.arm_id for arm in spec.arms} == {
        "anchor", "neighbour", "control"}
    # anchor: frozen P10 / 720-close strictly-past window / 24h span
    assert by_kind["anchor"].exposure["formula_id"] == "OICASCADE.anchor"
    assert by_kind["anchor"].exposure["params"] == ANCHOR_PARAMS
    assert by_kind["anchor"].holding_override is None
    # neighbour: frozen P5 / 48h span override
    assert by_kind["neighbour"].exposure["formula_id"] == "OICASCADE.neighbour"
    assert by_kind["neighbour"].exposure["params"] == NEIGHBOUR_PARAMS
    assert by_kind["neighbour"].holding_override == 11
    # control: the frozen sham (seed verbatim 1717, matched 24h windows)
    assert by_kind["control"].exposure["formula_id"] == "OICASCADE.control"
    assert by_kind["control"].exposure["params"] == CONTROL_PARAMS
    assert by_kind["control"].holding_override is None  # the 24h span
    assert by_kind["control"].exposure["params"]["seed"] == reg.OIC_SHAM_SEED
    # all three arms carry the availability-aligned endpoint series block,
    # pinned to the CORRECTED warmup-extended cache authority (A8 r2):
    # series_start_utc 2025-04-25T00:00:00Z + bucket_hours 4 => the loader
    # serves 2,904 slots whose last 2,190 land on the S0 H4 grid
    for arm in spec.arms:
        block = arm.exposure["endpoint_series"]
        assert block["format"] == "json"
        assert block["path"].endswith("oi_series_reduced.json")
        assert "availability" in block["alignment"]
        assert block["series_start_utc"] == "2025-04-25T00:00:00Z"
        assert block["bucket_hours"] == 4
        assert callable(reg.resolve(arm.exposure["formula_id"]))
        assert not reg.is_example_only(arm.exposure["formula_id"])
    # the THREE frozen falsification rules ride the spec and parse
    assert set(spec.frozen_rules) == {
        "control_reproduces", "fold_negative_majority",
        "ancestry_veto_measured",
    }
    assert spec.frozen_rules["control_reproduces"][
        "sham_expectancy_ratio"] == 0.5
    assert spec.frozen_rules["fold_negative_majority"][
        "max_negative_folds"] == 2
    assert spec.frozen_rules["ancestry_veto_measured"][
        "measured_pooled_abs_rho"] == 0.1899
    assert spec.frozen_rules["ancestry_veto_measured"][
        "veto_threshold"] == 0.2
    assert spec.frozen_rules["ancestry_veto_measured"][
        "frozen_verdict"] == "PASS"
    for rule in spec.frozen_rules.values():
        assert rule["action"] == "mark_dead"
    # the sham-calendar descriptor matches the diag contract's marker
    doc = json.loads(CONTRACT_PATH.read_text())
    assert (
        spec.sham_calendar["calendar"]
        == doc["concretization"]["sham_row_marker"]
        == "NOT_APPLICABLE:RANDOMIZED_EVENT_TIME_SHAM"
    )
    assert doc["concretization"]["calendar_conditioned"] is False


SCORED_CATEGORIES = {
    "identity.jsonl", "per_period_series.jsonl",
    "per_symbol_breakdown.jsonl", "per_fold_breakdown.jsonl",
    "stress_tiers.jsonl", "drop_one_inputs.jsonl",
    "benchmark_context.jsonl", "margins_to_fail.jsonl", "counters.jsonl",
    "reproduction_inputs.jsonl", "sham_control_calendar.jsonl",
}


def test_spec_end_to_end_scored_sanitized_and_enforced(tmp_path, monkeypatch):
    spec = _loaded_spec()
    collapse = [130 * 6 + 2, 200 * 6 + 4]
    manifest = _stage(tmp_path, spec, n_days=250, collapse_buckets=collapse)
    monkeypatch.setattr(d, "PANEL_DIR", manifest["_panel_dir"])
    out = tmp_path / "out"
    result = d.run_family(
        spec, manifest, d.repo_root(), out,
        sanitized=False, base_dir=tmp_path, code_freeze_sha="0" * 40,
    )
    for arm_id in ("anchor", "neighbour", "control"):
        res = result["arms"][arm_id]
        assert res["kernel"]["n_round_trips"] > 0
        assert res["kernel"]["remediated_kernel"] is True
        assert res["kernel"]["cost_holding_terms"] == 0.0
        arm_dir = out / "results/v17/V17-A6-P2-OICASCADE" / arm_id
        assert {p.name for p in arm_dir.iterdir()} == SCORED_CATEGORIES
        # the event-time sham class emits its NOT_APPLICABLE rows per arm
        sham = [
            json.loads(ln)
            for ln in (arm_dir / "sham_control_calendar.jsonl")
            .read_text().splitlines()
            if ln.strip()
        ]
        assert sham == [{
            "cycle_id": "CRYPTO-V17",
            "arm_id": arm_id,
            "calendar": "NOT_APPLICABLE:RANDOMIZED_EVENT_TIME_SHAM",
            "note": spec.sham_calendar["note"],
        }]
        # margins carry arm identity (P-3 attribution)
        margins = [
            json.loads(ln)
            for ln in (arm_dir / "margins_to_fail.jsonl")
            .read_text().splitlines()
            if ln.strip()
        ]
        assert [m["gate_id"] for m in margins] == [
            "G1", "G2", "G3", "G4", "G5"]
        assert all(m["arm_id"] == arm_id for m in margins)
    dsr = out / "results/v17/V17-A6-P2-OICASCADE/dsr_per_period_series.jsonl"
    assert dsr.exists()
    # the enforcement wrapper rode the cell record (fail-closed)
    assert "frozen_rule_enforcement" in result
    # sanitized dry-run: decisions only, non-vacuous, no outcome fields
    san = tmp_path / "san"
    summary = d.run_family(
        spec, manifest, d.repo_root(), san,
        sanitized=True, base_dir=tmp_path, code_freeze_sha="0" * 40,
    )
    assert sum(summary["decisions"].values()) > 0
    for arm_id in ("anchor", "neighbour", "control"):
        recs = [
            json.loads(ln)
            for ln in (
                san / "research/control/v17_run/q_dry_run/"
                f"V17-A6-P2-OICASCADE/{arm_id}/decisions.jsonl"
            ).read_text().splitlines()
            if ln.strip()
        ]
        assert recs and all(
            set(r) == {"cycle_id", "family_id", "arm_id", "date", "hour",
                       "decision_taken", "symbol"}
            for r in recs
        )
    # determinism: two scored runs are byte-identical
    out2 = tmp_path / "out2"
    d.run_family(
        spec, manifest, d.repo_root(), out2,
        sanitized=False, base_dir=tmp_path, code_freeze_sha="0" * 40,
    )
    base = out / "results/v17/V17-A6-P2-OICASCADE"
    base2 = out2 / "results/v17/V17-A6-P2-OICASCADE"
    for arm in ("anchor", "neighbour", "control"):
        for name in SCORED_CATEGORIES:
            assert (base / arm / name).read_bytes() == (
                base2 / arm / name).read_bytes()
    assert (base / "dsr_per_period_series.jsonl").read_bytes() == (
        base2 / "dsr_per_period_series.jsonl").read_bytes()


def test_diag_contract_passes_persistability_gate():
    doc = json.loads(CONTRACT_PATH.read_text())
    contract = doc["contract"]
    assert contract["cycle_id"] == "CRYPTO-V17"
    assert contract["calendar_conditioned"] is False  # event-time sham class
    verdict, findings = validate_contract(contract)
    assert verdict == "DIAGNOSTIC_CONTRACT_PASS"
    assert not [f for f in findings if f["severity"] == "HIGH"]
    # the recorded verdict block matches a fresh run of the gate
    assert doc["validate_contract"]["verdict"] == verdict
    assert doc["validate_contract"]["high_findings"] == 0
    assert doc["validate_contract"]["findings"] == findings
    # the artifact list derives from the contract and carries the canon;
    # the sham rows derive from the contract iff the frozen predicate
    # applies (calendar_conditioned is FALSE for this event-time-sham
    # family -- the rows are still persisted under the accepted LOW
    # finding and carry the not-applicable marker)
    artifacts, problems = expected_artifacts_from_contract(contract)
    assert not problems
    categories = {a["category"] for a in artifacts}
    assert ("sham_control_calendar" in categories) is False
    assert "dsr_per_period_series" in categories
    lows = [
        f for f in findings
        if f["severity"] == "LOW" and f["category"] == "sham_control_calendar"
    ]
    assert lows and "not applicable" in lows[0]["detail"]
    # the persisted conditional's canon mirrors the governance canon
    assert set(d.CANON_FIELDS["sham_control_calendar"]) == set(
        CONDITIONAL_REQUIRED_FIELDS["sham_control_calendar"])


# ------------------------------------------------------------------------- #
# (h) warmup-extended endpoint authority (A8 remediation r2)
# ------------------------------------------------------------------------- #
def _loader_grid(n_buckets: int) -> list:
    """An S0 H4 bucket grid (bucket-START keys, the loader's alignment law)."""
    return [_h4_key(i) for i in range(n_buckets)]


def _hinted_cache(warmup: int, n_buckets: int) -> list:
    """A warmup-extended cache: `warmup` pre-S0 slots + n_buckets S0 slots,
    slot value = 1_000.0 + slot index (hand-checkable alignment)."""
    return [1_000.0 + k for k in range(warmup + n_buckets)]


def _hints_for(warmup: int) -> dict:
    """Alignment hints whose series_start_utc sits EXACTLY `warmup` H4
    slots before the frozen S0 grid start (2025-08-22T00:00Z)."""
    s0_start = datetime(2025, 8, 22, tzinfo=timezone.utc)
    start = s0_start - timedelta(hours=4 * warmup)
    return {
        "format": "json",
        "series_start_utc": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bucket_hours": 4,
    }


def _load_endpoint(tmp_path: Path, cache, grid, block) -> list:
    path = tmp_path / "oi_warm.json"
    path.write_text(json.dumps({"BTCUSDT": cache}), encoding="utf-8")
    return d._load_endpoint_series(
        dict(block, path=str(path)),
        family_id="F", arm_id="A", universe=["BTCUSDT"],
        grid=grid, base_dir=tmp_path,
    )["BTCUSDT"]


def test_loader_warmup_extended_alignment(tmp_path):
    """The hinted loader serves the FULL warmup+S0 array (contiguous,
    float-or-null): its value at S0 start IS cache[warmup] and its LAST
    len(grid) entries land exactly on the S0 grid -- at production
    geometry, cache[714].  Misaligned starts, trailing shortfalls, caches
    shorter than the grid, lone hints and naive timestamps all refuse
    (fail closed)."""
    grid = _loader_grid(12)
    # production geometry, scaled grid: value at S0 start == cache[714]
    cache = _hinted_cache(WARMUP_SLOTS, 12)
    series = _load_endpoint(tmp_path, cache, grid, _hints_for(WARMUP_SLOTS))
    assert len(series) == WARMUP_SLOTS + len(grid)
    assert series[WARMUP_SLOTS] == cache[WARMUP_SLOTS]
    assert series == [float(v) for v in cache]  # contiguous warmup+S0 view
    assert series[-len(grid):] == [float(v) for v in cache[-len(grid):]]
    # a null warmup slot passes through as None
    cache[3] = None
    series = _load_endpoint(tmp_path, cache, grid, _hints_for(WARMUP_SLOTS))
    assert series[3] is None
    assert series[WARMUP_SLOTS] == float(1_000.0 + WARMUP_SLOTS)
    # misaligned series_start (+1 slot): the last slots miss the grid keys
    bad = _hints_for(2)
    bad["series_start_utc"] = "2025-08-21T20:00:00Z"  # one slot late
    with pytest.raises(d.DriverError, match="warmup alignment broken"):
        _load_endpoint(tmp_path, _hinted_cache(2, 12), grid, bad)
    # a shortfall at the trailing end lands the last slot off-grid too
    with pytest.raises(d.DriverError, match="warmup alignment broken"):
        _load_endpoint(tmp_path, _hinted_cache(2, 12)[:-1], grid, _hints_for(2))
    # a cache SHORTER than the grid is refused even under hints
    with pytest.raises(d.DriverError, match="shorter than the bucket grid"):
        _load_endpoint(tmp_path, _hinted_cache(2, 12)[:6], grid, _hints_for(2))
    # lone hints refused (both-or-neither), at loader AND parse-time gate
    lone = _hints_for(2)
    del lone["bucket_hours"]
    with pytest.raises(d.DriverError, match="given together"):
        _load_endpoint(tmp_path, _hinted_cache(2, 12), grid, lone)
    with pytest.raises(d.DriverError, match="given together"):
        d._validate_endpoint_alignment_hints(
            {"series_start_utc": "2025-04-25T00:00:00Z"}, "F", "A"
        )
    # bucket_hours must be a positive int, series_start_utc must carry UTC
    for bad_bh in ("4", 4.0, 0, True):
        with pytest.raises(d.DriverError, match="bucket_hours"):
            d._validate_endpoint_alignment_hints(
                {"series_start_utc": "2025-04-25T00:00:00Z", "bucket_hours": bad_bh},
                "F", "A",
            )
    with pytest.raises(d.DriverError, match="explicit UTC offset"):
        d._validate_endpoint_alignment_hints(
            {"series_start_utc": "2025-04-25T00:00:00", "bucket_hours": 4},
            "F", "A",
        )


def test_loader_legacy_contract_byte_identical(tmp_path):
    """Without the hints the strict-length contract is untouched: a
    grid-length cache loads to exactly the same float-or-null list, and
    any other length gets the legacy '!= bucket grid' refusal."""
    grid = _loader_grid(12)
    cache = _hinted_cache(0, 12)
    series = _load_endpoint(tmp_path, cache, grid, {"format": "json"})
    assert len(series) == len(grid)
    assert series == [float(v) for v in cache]
    cache[5] = None
    series = _load_endpoint(tmp_path, cache, grid, {"format": "json"})
    assert series[5] is None and series[4] == float(1_004.0)
    with pytest.raises(d.DriverError, match="length 5 != bucket grid 12"):
        _load_endpoint(
            tmp_path, _hinted_cache(0, 12)[:5], grid, {"format": "json"}
        )


def test_formula_consumes_warmup_slots():
    """The fixed warmup offset (S0 ordinal i -> authority slot i + warmup)
    puts the trailing P10 window AND the T-24h denominator into the pre-S0
    slots.  Hand-separated hypotheses on a warmup-14 authority (win 12):
    ordinal 6's window is slots [8..19] -- six of them pre-S0.  Variant A
    parks two WARMUP slots (8, 9) at -0.01 -> window p10 = -0.007 and the
    collapse r_OI = -0.009 at ordinal 6 fires; variant B parks them at
    -0.02 -> p10 = -0.016 and the IDENTICAL S0 data does NOT fire: a
    warmup slot inside the early-S0 window is decision load-bearing.  On
    the grid-length legacy authority the same collapse at ordinal 6 is an
    honest-warmup None -- the exact remediation delta."""
    warmup, n, win = 14, 30, 12
    collapse_r = -0.009

    def extended(low_slots: float) -> list:
        r = [0.02] * (warmup + n)
        r[8] = r[9] = low_slots  # two WARMUP slots of ordinal 6's window
        r[warmup + 6] = collapse_r  # the engineered S0 collapse
        return oi_from_r(r)

    prices = [100.0 - 0.5 * i for i in range(n)]  # r_24 < 0 from ordinal 6
    panels = {"BTCUSDT": _h4_rows(prices)}
    params = _gate_params(win)

    p10_a = float(np.percentile([-0.01, -0.01] + [0.02] * 10, 10.0))
    assert p10_a == pytest.approx(-0.007)
    warm_series = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": extended(-0.01)}
    )["BTCUSDT"]
    assert warm_series[:6] == [0.0] * 6  # decided; panel r_24 warmup: no fire
    assert warm_series[6] == 1.0  # fires on the warmup-funded window
    p10_b = float(np.percentile([-0.02, -0.02] + [0.02] * 10, 10.0))
    assert p10_b == pytest.approx(-0.016)
    cold_series = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": extended(-0.02)}
    )["BTCUSDT"]
    assert cold_series[6] == 0.0  # -0.009 now sits ABOVE its window p10
    # the legacy contract on the SAME S0 data: no warmup slots -> the
    # ordinal-6 collapse is never even decided (honest warmup None)
    r_s0 = [0.02] * n
    r_s0[6] = collapse_r
    legacy_series = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": oi_from_r(r_s0)}
    )["BTCUSDT"]
    assert legacy_series[:win] == [None] * win
    assert legacy_series[6] is None


def test_first_s0_close_fully_windowed_at_720_warmup():
    """With a 720-slot warmup the FIRST S0 H4 close has exactly 720 prior
    closes -- every one of them pre-S0 -- and is DECIDED (never the
    honest-warmup None); the same close on a grid-length legacy authority
    is None because its window cannot exist there."""
    warmup, n = 720, 12
    prices = [100.0 - 0.5 * i for i in range(n)]
    panels = {"BTCUSDT": _h4_rows(prices)}
    params = _gate_params(720)
    extended = oi_from_r([0.02] * (warmup + n))
    assert len(extended) == warmup + n
    warm_series = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": extended}
    )["BTCUSDT"]
    assert warm_series[0] == 0.0  # window = slots [0:720], all pre-S0
    legacy_series = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": oi_from_r([0.02] * n)}
    )["BTCUSDT"]
    assert legacy_series == [None] * n


def test_no_after_close_influence_with_warmup():
    """Availability law on the warmup-extended authority: the decision at
    S0 ordinal i is a function of authority slots <= i + warmup ONLY --
    rewriting every endpoint value strictly AFTER a taken event's
    authority slot leaves the path up to and including that decision
    byte-identical, and the event's OWN close endpoint stays
    load-bearing."""
    warmup, n, event_i = 10, 40, 30
    event_w = warmup + event_i
    prices = [100.0 - 0.5 * i for i in range(n)]  # r_24 < 0 everywhere
    r = [0.001 * k for k in range(warmup + n)]  # strictly rising: calm
    r[event_w] = -0.5  # engineered OI collapse at S0 ordinal 30
    oi = oi_from_r(r)
    panels = {"BTCUSDT": _h4_rows(prices)}
    params = _gate_params(10)
    series = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": oi}
    )["BTCUSDT"]
    assert series[event_i] == 1.0
    # perturb EVERY authority slot strictly after the event close: the
    # path up to and including the event decision is untouched
    tampered = list(oi)
    for k in range(event_w + 1, warmup + n):
        tampered[k] = tampered[k] * 3.0 + 7_000_000.0
    series2 = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": tampered}
    )["BTCUSDT"]
    assert series2[: event_i + 1] == series[: event_i + 1]
    # the event's OWN close endpoint is load-bearing: a +50% OI print
    # (r_OI = +0.5, far above the window decile) un-fires the event
    no_collapse = list(oi)
    no_collapse[event_w] = no_collapse[event_w - 6] * 1.5
    series3 = reg.resolve("OICASCADE.anchor")(
        panels, params, endpoint={"BTCUSDT": no_collapse}
    )["BTCUSDT"]
    assert series3[event_i] == 0.0
