"""Formal fixtures for the two frozen candidate laws (ERP1-TRACKA-COHORT-2).

Classes (dispatch-mandated):
  (a) synthetic panel: each anchor law must be PIT-clean
      (battery M-T/M-F/M-V == PASS_PIT);
  (b) a deliberately leaky variant of each law (percentile pool consuming
      same-panel future / decision-day-inclusive pools) must FAIL M-T —
      proving the harness catches the leak class on these laws' own code;
  (c) wide-mirror twin non-vacuity on synthetic data (M-V >= 2%);
  (d) warmup boundary: no decision while traded-day ordinal < 61, decisions
      admissible from ordinal 61.

NO PnL anywhere: these fixtures consume target arrays and battery counts
only.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE / "scripts"))

from pit_battery2 import non_vacuity_test, run_battery  # noqa: E402
from qcrd_dinv_lib import (  # noqa: E402
    GATE_MIRROR, WARMUP_TRADED_DAYS, dinv_1d_target, dinv_day_table,
    epoch_secs, pooled_pct, qcrd_h1_target, session_day_ordinals,
)
from run_f2_battery import future_mutation_test_ext  # noqa: E402

SEED_SYNTH = 20260926


# ------------------------------------------------------------ synthetic --

def synth_df(n_days: int = 100, seed: int = SEED_SYNTH) -> pd.DataFrame:
    """Hourly synthetic plane + M1 aggregate columns.

    m1_med_spread is QUANTIZED to 5 uniform levels so that level-3 bars sit
    exactly on the p40 gate boundary (empirical percentile 0.40) — this
    makes the pool-shift twin non-vacuous and the leaky-pool failure
    decisive.
    """
    rng = np.random.default_rng(seed)
    n = n_days * 24
    ts = pd.date_range("2023-01-02", periods=n, freq="1h", tz="UTC")
    px = 0.65 + np.cumsum(rng.normal(0, 3e-4, n))
    b_o = px
    b_c = px + rng.normal(0, 1e-4, n)
    b_h = np.maximum(b_o, b_c) + np.abs(rng.normal(0, 1e-4, n))
    b_l = np.minimum(b_o, b_c) - np.abs(rng.normal(0, 1e-4, n))
    sprd = 2e-4 + np.abs(rng.normal(0, 3e-5, n))
    df = pd.DataFrame({
        "ts": ts, "b_o": b_o, "b_h": b_h, "b_l": b_l, "b_c": b_c,
        "a_o": b_o + sprd, "a_c": b_c + sprd,
        "s_open": sprd, "s_close": sprd,
    })
    levels = np.arange(1, 6) * 1.0e-4
    # level-3 carries 50% mass and its empirical percentile is exactly the
    # p40 gate boundary (p1+p2 = 0.4) -> pool perturbations flip it.
    df["m1_med_spread"] = levels[rng.choice(5, n, p=[0.2, 0.2, 0.5, 0.05, 0.05])]
    sgn = rng.choice([-1.0, 1.0, 0.0], n, p=[0.45, 0.45, 0.10])
    mag = rng.uniform(0.30, 0.60, n)
    df["m1_sum_dl"] = sgn * mag
    df["m1_sum_abs_dl"] = np.where(sgn == 0.0, 1.0, mag)
    df["m1_nmin"] = 60
    return df


# --------------------------------------------------- leaky variants (b) --

def leaky_full_panel_pct(ts, hour, values) -> np.ndarray:
    """LEAK: percentile pool = ALL same-hour bars of the given panel
    (includes the decision bar itself and same-panel future bars)."""
    out = np.full(len(ts), np.nan)
    for h in np.unique(hour):
        idx = np.flatnonzero(hour == h)
        v = values[idx]
        srt = np.sort(v)
        for j, i in enumerate(idx):
            out[i] = np.searchsorted(srt, v[j], side="left") / len(srt)
    return out


def leaky_qcrd_h1(df, mass=0.25, gate=0.40) -> np.ndarray:
    """Deliberately leaky P3-A: the percentile pool reads the decision bar
    and same-panel future bars (window unbounded on the right)."""
    ts = epoch_secs(df)
    hour = (ts // 3600) % 24
    day, dord, _ = session_day_ordinals(ts)
    sum_dl = df["m1_sum_dl"].to_numpy(float)
    sum_adl = df["m1_sum_abs_dl"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        s_mass = np.where(sum_adl > 0, sum_dl / sum_adl, np.nan)
    pct = leaky_full_panel_pct(ts, hour,
                               df["m1_med_spread"].to_numpy(float))
    fire = ((hour >= 0) & (hour <= 18) & (dord >= WARMUP_TRADED_DAYS)
            & np.isfinite(s_mass) & (pct <= gate))
    tgt = np.zeros(len(ts), dtype=np.int8)
    tgt[fire & (s_mass >= mass)] = 1
    tgt[fire & (s_mass <= -mass)] = -1
    return tgt


def leaky_dinv_1d(df, mass=0.20, gate=0.40, past_occ: int = 10,
                  future_occ: int = 60) -> np.ndarray:
    """Deliberately leaky P3-B: the same-weekday percentile pool re-anchored
    into the FUTURE (only 10 trailing occurrences kept, next 60 same-weekday
    occurrences added, decision day included) — future-window re-anchoring,
    the law's own F5/F6 probe direction, used here ONLY to prove the
    harness catches it."""
    ts = epoch_secs(df)
    hour = (ts // 3600) % 24
    rows, bar_day, bar_ord, ord_of = dinv_day_table(df)
    dec = [r for r in rows if r["dec_capable"]]
    tgt = np.zeros(len(ts), dtype=np.int8)
    by_day = {r["day"]: r for r in rows}
    session_days = [r["day"] for r in rows]
    next_session = {session_days[j]: (session_days[j + 1]
                                      if j + 1 < len(session_days) else None)
                    for j in range(len(session_days))}
    for j, r in enumerate(dec):
        if r["ord"] < WARMUP_TRADED_DAYS:
            continue
        pool = [q["med_s_close"] for k, q in enumerate(dec)
                if q["weekday"] == r["weekday"]
                and (0 <= j - k <= past_occ or 0 < k - j <= future_occ)]
        if not pool:
            continue
        ps = np.sort(np.asarray(pool, float))
        p_d = float(np.searchsorted(ps, r["med_s_close"], side="left")
                    / len(ps))
        if abs(r["s_d"]) >= mass and p_d <= gate:
            sign = 1 if r["s_d"] > 0 else -1
            nxt = next_session.get(r["day"])
            if r["i_close"] >= 0:
                tgt[r["i_close"]] = sign
            if nxt is not None and nxt in by_day:
                for i in by_day[nxt]["idx"]:
                    if 0 <= hour[i] <= 18:
                        tgt[i] = sign
    return tgt


P3A_TWINS = {
    "index_shift_pool": lambda d: qcrd_h1_target(d, mode="index_shift_pool"),
    "mirror_wide": lambda d: qcrd_h1_target(d, mode="mirror_wide"),
    "volgate": lambda d: qcrd_h1_target(d, mode="volgate"),
    "ungated": lambda d: qcrd_h1_target(d, mode="ungated"),
}
P3B_TWINS = {
    "weekday_shuffle": lambda d: dinv_1d_target(d, mode="weekday_shuffle"),
    "mirror_wide": lambda d: dinv_1d_target(d, mode="mirror_wide"),
    "ungated": lambda d: dinv_1d_target(d, mode="ungated"),
}


# ------------------------------------------------------------- fixtures --

def test_a_clean_p3a_battery_passes():
    df = synth_df()
    res = run_battery(qcrd_h1_target, df, P3A_TWINS,
                      decision_mask=None, label="P3A-clean-synthetic")
    assert res["M-T"]["status"] == "PASS", res["M-T"]
    assert res["M-F"]["status"] == "PASS", res["M-F"]
    for name, mv in res["M-V"].items():
        assert mv["status"] == "PASS", (name, mv)
    assert res["verdict"] == "PASS_PIT"
    ext = future_mutation_test_ext(qcrd_h1_target, df)
    assert ext["status"] == "PASS", ext


def test_a_clean_p3b_battery_passes():
    df = synth_df()
    mask = (epoch_secs(df) // 3600) % 24 == 19   # traded-day decision bars
    res = run_battery(dinv_1d_target, df, P3B_TWINS,
                      decision_mask=mask, label="P3B-clean-synthetic")
    assert res["M-T"]["status"] == "PASS", res["M-T"]
    assert res["M-F"]["status"] == "PASS", res["M-F"]
    for name, mv in res["M-V"].items():
        assert mv["status"] == "PASS", (name, mv)
    assert res["verdict"] == "PASS_PIT"
    ext = future_mutation_test_ext(dinv_1d_target, df,
                                   extra_cols=["s_close"])
    assert ext["status"] == "PASS", ext


def test_b_leaky_p3a_fails_MT():
    df = synth_df()
    full = leaky_qcrd_h1(df)
    assert (full != 0).any(), "fixture degenerate: leaky P3-A never fires"
    ts = epoch_secs(df)
    _, dord, _ = session_day_ordinals(ts)
    mask = (((ts // 3600) % 24 >= 7) & ((ts // 3600) % 24 <= 18)
            & (dord >= WARMUP_TRADED_DAYS))
    res = run_battery(leaky_qcrd_h1, df, {}, decision_mask=mask,
                      label="P3A-leaky")
    assert res["M-T"]["status"] == "FAIL", res["M-T"]
    assert res["M-T"]["kill_class"] == "KILL_PIT_SEAM"


def _harden_dinv_fixture(df: pd.DataFrame) -> pd.DataFrame:
    """Deterministic structure so the future-window leak bites at EVERY
    post-warmup decision day (not merely in expectation):
      - intraday monotone mid ramp -> S_d = +/-1 fires the mass condition
        every day;
      - downward spread ramp across the panel -> the future-inclusive pool
        systematically re-anchors P_d above the gate while the truncated
        (past-only) pool stays below it."""
    ts = epoch_secs(df)
    day = ts // 86400
    hour = (ts // 3600) % 24
    days = np.unique(day)
    for j, d in enumerate(days):
        m = day == d
        add = 2e-4 * hour[m] * (1.0 if j % 2 == 0 else -1.0)
        df.loc[m, "b_c"] = df.loc[m, "b_c"] + add
        df.loc[m, "a_c"] = df.loc[m, "a_c"] + add
    day_frac = (day - day.min()) / float(day.max() - day.min())
    df["s_close"] = 3.0e-4 * (1.0 - day_frac) + 5e-5
    return df


def test_b_leaky_p3b_fails_MT():
    df = _harden_dinv_fixture(synth_df())
    full = leaky_dinv_1d(df)
    assert (full != 0).any(), "fixture degenerate: leaky P3-B never fires"
    mask = (epoch_secs(df) // 3600) % 24 == 19
    res = run_battery(leaky_dinv_1d, df, {}, decision_mask=mask,
                      label="P3B-leaky")
    assert res["M-T"]["status"] == "FAIL", res["M-T"]
    assert res["M-T"]["kill_class"] == "KILL_PIT_SEAM"


def test_c_mirror_wide_nonvacuity():
    df = synth_df()
    base_a = qcrd_h1_target(df)
    mirror_a = qcrd_h1_target(df, mode="mirror_wide")
    mv_a = non_vacuity_test(base_a, mirror_a)
    assert mv_a["status"] == "PASS" and mv_a["share"] >= 0.02, mv_a
    base_b = dinv_1d_target(df)
    mirror_b = dinv_1d_target(df, mode="mirror_wide")
    mv_b = non_vacuity_test(base_b, mirror_b)
    assert mv_b["status"] == "PASS" and mv_b["share"] >= 0.02, mv_b
    # sanity of the mirror definition: gate really is the wide tail
    assert GATE_MIRROR == 0.60


def test_d_warmup_boundary():
    df = synth_df()
    ts = epoch_secs(df)
    _, dord, _ = session_day_ordinals(ts)
    for fn in (lambda d: qcrd_h1_target(d),
               lambda d: dinv_1d_target(d)):
        tgt = fn(df)
        # session bars only: dord == -1 marks non-session bars (evening /
        # weekend carry of the P3-B vector — never fill-eligible)
        warm_session = (dord >= 0) & (dord < WARMUP_TRADED_DAYS)
        assert int((tgt[warm_session] != 0).sum()) == 0, \
            "decision inside the 61-traded-day warmup"
    # and the laws are live after the warmup on this panel
    post = dord >= WARMUP_TRADED_DAYS
    assert int((qcrd_h1_target(df)[post] != 0).sum()) > 0
    assert int((dinv_1d_target(df)[post] != 0).sum()) > 0


def test_d_warmup_boundary_forced_fire():
    """Force conditions to fire at traded-day ordinals 60 and 61 explicitly:
    the law must stay flat at 60 and may fire at 61."""
    df = synth_df(seed=11)
    ts = epoch_secs(df)
    _, dord, _ = session_day_ordinals(ts)
    # P3-A: pick in-session bars on day ord 60 and 61 (hour 10), force a
    # low spread level + full mass.
    for target_ord in (60, 61):
        rows = np.flatnonzero((dord == target_ord) & ((ts // 3600) % 24 == 10))
        df.loc[rows, "m1_med_spread"] = 1.0e-4     # lowest level
        df.loc[rows, "m1_sum_dl"] = 0.5
        df.loc[rows, "m1_sum_abs_dl"] = 0.5
    tgt = qcrd_h1_target(df)
    rows60 = np.flatnonzero((dord == 60) & ((ts // 3600) % 24 == 10))
    assert (tgt[rows60] == 0).all(), "fired inside warmup (day ordinal 60)"
    rows61 = np.flatnonzero((dord == 61) & ((ts // 3600) % 24 == 10))
    assert (tgt[rows61] != 0).all(), "failed to fire at first legal day"
