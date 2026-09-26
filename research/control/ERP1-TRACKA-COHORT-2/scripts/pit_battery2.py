"""ERP1-TRACKA-COHORT-2 — generic pre-PnL PIT battery (child plan §8 F-2).

Mechanism-agnostic harness. A candidate signal is a pure function
    target = signal_fn(df_bars) -> np.ndarray[int8]  (len == len(df), values -1/0/+1)
computed on the bar dataframe given to it. The battery proves — behaviorally,
on the candidate's OWN code — the three PIT laws:

  M-T  panel-truncation replay : for sampled truncation points t, running the
        signal on bars[:t] must reproduce the full-panel target prefix over
        decision bars <= t EXACTLY (a deterministic leak "passes" every OOS
        window; only this test catches it — P-18(ERP1) lesson).
  M-F  future-data mutation    : perturbing bars AFTER t (prices scaled,
        order shuffled) must not change the full-panel target prefix <= t.
  M-V  non-vacuity             : each preregistered mutation twin (index
        shift / gate flip / sham) must move >= 2% of in-session targets.

Verdicts are per-check PASS/FAIL with counts; FAIL of M-T or M-F is
KILL_PIT_SEAM-class for the candidate (child plan §8 F-2 v/vi).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd


def _prefix_equal(a: np.ndarray, b: np.ndarray, upto: int) -> bool:
    if upto < 0:
        return True
    x, y = a[: upto + 1], b[: upto + 1]
    # NaN-aware exact equality on float-castable arrays; ints compare directly
    both_nan = np.isnan(x.astype(float)) & np.isnan(y.astype(float))
    eq = (x == y) | both_nan
    return bool(eq.all())


def truncation_test(
    signal_fn, df: pd.DataFrame, n_points: int = 24, min_history: int = 200,
    decision_mask=None, seed: int = 20260926,
) -> dict:
    """Replay signal_fn on panels truncated at sampled decision bars."""
    rng = np.random.default_rng(seed)
    full = signal_fn(df)
    n = len(df)
    idx_pool = np.arange(min_history, n)
    if decision_mask is not None:
        idx_pool = idx_pool[decision_mask[min_history:]]
    if len(idx_pool) == 0:
        return {"check": "M-T", "status": "NOT_RUN", "reason": "empty decision pool"}
    pts = np.unique(np.linspace(0, len(idx_pool) - 1, n_points).astype(int))
    pts = idx_pool[pts]
    diffs = []
    for t in pts:
        # truncated panel: bars strictly up to and including t (bar t is the
        # just-closed decision bar; anything after it is the future)
        trunc = df.iloc[: t + 1].reset_index(drop=True)
        sub = signal_fn(trunc)
        # compare sub's LAST value (decision made at t on truncated info)
        # against full-panel target AT t
        if not _prefix_eq_scalar(sub[-1], full[t]):
            diffs.append(int(t))
    status = "PASS" if not diffs else "FAIL"
    return {
        "check": "M-T", "status": status, "n_points": int(len(pts)),
        "n_diff": len(diffs), "diff_sample": diffs[:10],
        "kill_class": "KILL_PIT_SEAM" if diffs else None,
    }


def _prefix_eq_scalar(a, b) -> bool:
    if a is None or b is None:
        return a is b
    try:
        if np.isnan(float(a)) and np.isnan(float(b)):
            return True
    except (TypeError, ValueError):
        pass
    return bool(a == b)


def future_mutation_test(
    signal_fn, df: pd.DataFrame, t_frac: float = 0.7, seed: int = 20260926,
) -> dict:
    """Mutate bars strictly after a cut point; prefix target must not move."""
    rng = np.random.default_rng(seed)
    full = signal_fn(df)
    n = len(df)
    t = int(n * t_frac)
    mut = df.copy()
    cols = ["b_o", "b_h", "b_l", "b_c", "a_o", "a_c"]
    for c in cols:
        v = mut[c].to_numpy(dtype=float).copy()
        tail = v[t + 1:]
        perm = rng.permutation(len(tail))
        v[t + 1:] = tail[perm] * rng.uniform(0.9, 1.1, len(tail)) + rng.normal(0, 1e-4, len(tail))
        mut[c] = v
    mut_full = signal_fn(mut)
    moved = int((mut_full[: t + 1] != full[: t + 1]).sum())
    return {
        "check": "M-F", "status": "PASS" if moved == 0 else "FAIL",
        "cut_index": t, "n_prefix_bars": t + 1, "n_moved": moved,
        "kill_class": "KILL_PIT_SEAM" if moved else None,
    }


def non_vacuity_test(base, twin, decision_mask=None) -> dict:
    """A preregistered mutation twin must move >= 2% of decision targets."""
    if decision_mask is None:
        decision_mask = np.ones(len(base), dtype=bool)
    pool = decision_mask & (np.asarray(base) != 0) | decision_mask & (np.asarray(twin) != 0)
    n_pool = int(pool.sum())
    if n_pool == 0:
        return {"check": "M-V", "status": "NOT_RUN", "reason": "empty pool"}
    n_diff = int((np.asarray(base)[pool] != np.asarray(twin)[pool]).sum())
    share = n_diff / n_pool
    return {
        "check": "M-V", "status": "PASS" if share >= 0.02 else "FAIL",
        "n_pool": n_pool, "n_diff": n_diff, "share": round(float(share), 6),
        "kill_class": "KILL_VACUOUS_MUTATION" if share < 0.02 else None,
    }


def run_battery(
    signal_fn, df: pd.DataFrame, twins: dict, decision_mask=None,
    n_points: int = 24, seed: int = 20260926, label: str = "",
) -> dict:
    base = signal_fn(df)
    res = {
        "label": label,
        "M-T": truncation_test(signal_fn, df, n_points=n_points,
                               decision_mask=decision_mask, seed=seed),
        "M-F": future_mutation_test(signal_fn, df, seed=seed),
        "M-V": {},
    }
    for name, twin_fn in twins.items():
        res["M-V"][name] = non_vacuity_test(base, twin_fn(df), decision_mask)
    res["verdict"] = (
        "PASS_PIT" if res["M-T"]["status"] == "PASS" and res["M-F"]["status"] == "PASS"
        and all(v["status"] == "PASS" for v in res["M-V"].values())
        else "FAIL_PIT"
    )
    return res


def in_session_mask(df: pd.DataFrame, hh: tuple = (7, 18)) -> np.ndarray:
    """Decision-bar mask: hours hh[0]..hh[1] UTC (the family session law)."""
    hrs = df["ts"].dt.hour.to_numpy()
    return (hrs >= hh[0]) & (hrs <= hh[1])


if __name__ == "__main__":  # smoke: self-test on synthetic bars
    n = 2000
    rng = np.random.default_rng(7)
    px = 1.0 + np.cumsum(rng.normal(0, 1e-4, n))
    df = pd.DataFrame({
        "ts": pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"),
        "b_o": px, "b_h": px + 1e-4, "b_l": px - 1e-4, "b_c": px,
        "a_o": px + 2e-4, "a_c": px + 2e-4,
        "s_open": 2e-4, "s_close": 2e-4, "v": 100.0,
    })

    def clean_sig(d):  # decision at bar i uses bar i-1 only
        t = np.zeros(len(d), dtype=int)
        t[1:] = np.where(d["b_c"].to_numpy()[1:] > d["b_c"].to_numpy()[:-1], 1, -1)
        return t

    def leaky_sig(d):  # RANGEFADE-class: uses same-panel FUTURE max/min
        t = np.zeros(len(d), dtype=int)
        hi = d["b_h"].to_numpy().max()
        lo = d["b_l"].to_numpy().min()
        c = d["b_c"].to_numpy()
        t = np.where(c > (hi + lo) / 2, -1, 1)  # fade toward full-panel mid
        return t

    r_clean = run_battery(clean_sig, df, {"flip": lambda d: -clean_sig(d)},
                          label="clean-synthetic")
    r_leaky = run_battery(leaky_sig, df, {"flip": lambda d: -leaky_sig(d)},
                          label="leaky-synthetic")
    print(json.dumps({"clean": r_clean["verdict"], "leaky": r_leaky["verdict"],
                      "leaky_MT": r_leaky["M-T"]["status"]}, indent=1))
    assert r_clean["verdict"] == "PASS_PIT"
    assert r_leaky["M-T"]["status"] == "FAIL"  # harness must catch the leak class
