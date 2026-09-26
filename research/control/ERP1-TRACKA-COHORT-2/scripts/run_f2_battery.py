"""ERP1-TRACKA-COHORT-2 — F-2 PIT battery on the two frozen candidate laws.

Runs scripts/pit_battery2.py (M-T truncation replay / M-F future-mutation /
M-V non-vacuity) on each anchor law + its declared twins, on the DEV planes
produced through scripts/dev_plane2.py ONLY (sealed window never read):

  P3-A TRACKA2-P3A-QCRD-H1 (home AUDUSD, replicate USDCAD)
      decision mask for sampling/pooling = in-session 7..18 UTC (dispatch).
      twins: index_shift_pool, mirror_wide (P_t >= p60), volgate
      (trailing realized-vol percentile), ungated.
  P3-B TRACKA2-P3B-DINV-1D (home USDCAD, replicate AUDUSD)
      decision mask = traded-day decision bars (hour-19, day close).
      twins: weekday_shuffle (seeded, S_d marginal preserved), mirror_wide
      (P_d >= p60), ungated.

M-F is run TWICE per law:
  (i)  pit_battery2.future_mutation_test — mutates the six price columns
       (the frozen harness; catches b_*/a_* consumption, e.g. P3-B mid
       closes);
  (ii) future_mutation_test_ext (this module, same logic and seed) — adds
       the M1-aggregate columns and s_close to the mutation list, because
       pit_battery2's fixed 6-column list cannot perturb M1-derived inputs
       (mechanical necessity: P3-A consumes ONLY M1 aggregates; disclosed
       in FALSIFIER2_PREP_REPORT.md). Both must PASS.

Verdicts: per-check PASS/FAIL counts only. NO PnL exists anywhere in this
pipeline or its output.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE / "scripts"))

import dev_plane2  # noqa: E402
import pit_battery2  # noqa: E402
from qcrd_dinv_lib import (  # noqa: E402
    dinv_1d_target, epoch_secs, qcrd_h1_target,
)
from build_t2_planes import attach_m1agg  # noqa: E402

OUT = LANE / "falsifier" / "F2_battery_results.json"
SEED = 20260926
M1_COLS = ("m1_sum_dl", "m1_sum_abs_dl", "m1_med_spread", "m1_nmin")


def future_mutation_test_ext(signal_fn, df, t_frac: float = 0.7,
                             seed: int = SEED, extra_cols=()) -> dict:
    """pit_battery2.future_mutation_test with the mutation column set
    extended to every column the candidate laws consume. Identical logic,
    seed and perturbation; report-only addition (see module docstring)."""
    rng = np.random.default_rng(seed)
    full = signal_fn(df)
    n = len(df)
    t = int(n * t_frac)
    mut = df.copy()
    cols = ["b_o", "b_h", "b_l", "b_c", "a_o", "a_c", *extra_cols,
            *[c for c in M1_COLS if c in mut.columns]]
    for c in cols:
        v = mut[c].to_numpy(dtype=float).copy()
        tail = v[t + 1:]
        perm = rng.permutation(len(tail))
        v[t + 1:] = (tail[perm] * rng.uniform(0.9, 1.1, len(tail))
                     + rng.normal(0, 1e-4, len(tail)))
        mut[c] = v
    mut_full = signal_fn(mut)
    moved = int((mut_full[: t + 1] != full[: t + 1]).sum())
    return {
        "check": "M-F-ext", "status": "PASS" if moved == 0 else "FAIL",
        "cut_index": t, "n_prefix_bars": t + 1, "n_moved": moved,
        "mutated_cols": list(cols),
        "kill_class": "KILL_PIT_SEAM" if moved else None,
    }


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def p3a_in_session_mask(df) -> np.ndarray:
    """Dispatch: in-session mask 7..18 UTC for P3-A battery sampling."""
    return pit_battery2.in_session_mask(df, (7, 18))


def p3b_decision_mask(df) -> np.ndarray:
    """Dispatch: traded-day decision mask (hour-19 day-close bars)."""
    return (epoch_secs(df) // 3600) % 24 == 19


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


def main() -> int:
    results = {
        "schema": "tracka2.f2_battery@1",
        "seed": SEED,
        "harness": "scripts/pit_battery2.py",
        "harness_sha256": sha256_file(LANE / "scripts" / "pit_battery2.py"),
        "law_lib": "scripts/qcrd_dinv_lib.py",
        "law_lib_sha256": sha256_file(LANE / "scripts" / "qcrd_dinv_lib.py"),
        "dev_loader": "scripts/dev_plane2.py",
        "dev_loader_sha256": sha256_file(LANE / "scripts" / "dev_plane2.py"),
        "sealed_window": "2026-01-01..2026-06-30 never read; all planes "
                         "via dev_plane2.load_bars (row pins asserted)",
        "laws": {},
    }
    for sym in ("AUDUSD", "USDCAD"):
        df = attach_m1agg(dev_plane2.load_bars("bars1h_ANC", sym), sym)
        print(f"[{sym}] dev rows={len(df)} — battery P3-A ...", flush=True)
        res_a = pit_battery2.run_battery(
            qcrd_h1_target, df, P3A_TWINS,
            decision_mask=p3a_in_session_mask(df),
            label=f"P3A-QCRD-H1/{sym}", seed=SEED)
        res_a["M-F-ext"] = future_mutation_test_ext(qcrd_h1_target, df)
        res_a["verdict"] = (
            "PASS_PIT" if res_a["M-T"]["status"] == "PASS"
            and res_a["M-F"]["status"] == "PASS"
            and res_a["M-F-ext"]["status"] == "PASS"
            and all(v["status"] == "PASS" for v in res_a["M-V"].values())
            else "FAIL_PIT")
        print(f"[{sym}] battery P3-B ...", flush=True)
        res_b = pit_battery2.run_battery(
            dinv_1d_target, df, P3B_TWINS,
            decision_mask=p3b_decision_mask(df),
            label=f"P3B-DINV-1D/{sym}", seed=SEED)
        res_b["M-F-ext"] = future_mutation_test_ext(
            dinv_1d_target, df, extra_cols=["s_close"])
        res_b["verdict"] = (
            "PASS_PIT" if res_b["M-T"]["status"] == "PASS"
            and res_b["M-F"]["status"] == "PASS"
            and res_b["M-F-ext"]["status"] == "PASS"
            and all(v["status"] == "PASS" for v in res_b["M-V"].values())
            else "FAIL_PIT")
        results["laws"][f"P3A-QCRD-H1/{sym}"] = res_a
        results["laws"][f"P3B-DINV-1D/{sym}"] = res_b
        print(json.dumps({k: v["verdict"] for k, v in
                          ((f"P3A/{sym}", res_a), (f"P3B/{sym}", res_b))},
                         indent=1), flush=True)

    results["all_pass"] = all(
        v["verdict"] == "PASS_PIT" for v in results["laws"].values())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1))
    print(json.dumps({"out": str(OUT), "all_pass": results["all_pass"]},
                     indent=1))
    return 0 if results["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
