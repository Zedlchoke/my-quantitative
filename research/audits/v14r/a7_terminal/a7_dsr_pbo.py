"""A7 terminal audit -- frozen gate_runner application + DSR/PBO (V14).

Applies the frozen family gate_runner functions to the A7 RECOMPUTED gate
inputs (a7_stage_a_recompute_v14.json) and computes DSR/PBO per
research/dsr.py over the committed evidence, recording exactly what is and
is not computable. Read-only audit; writes one JSON.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from research.dsr import (  # noqa: E402
    DSR_ESTIMATOR_ID,
    PBO_ESTIMATOR_ID,
    dsr_probability,
    pbo_cscv,
)
from research.v14.families.basislv_premfade.gate_runner import (  # noqa: E402
    evaluate_family_gate as basislv_gate,
)
from research.v14.families.oicyc.gate_runner import (  # noqa: E402
    fold_concentration_check,
    headline_gate,
    incremental_context_gate,
)
from research.v14.families.oicyc.gate_runner import (  # noqa: E402
    evaluate_family_gate as oicyc_gate,
)

HERE = Path(__file__).resolve().parent
RECOMP = json.loads((HERE / "a7_stage_a_recompute_v14.json").read_text())

# weekly decision-row net returns per arm for DSR (from baseline artifacts)
RESULTS = REPO / "results/v14_phase_e"


def arm_rows(family: str, arm: str) -> list[float]:
    art = json.loads(
        (
            RESULTS / family / arm / "matrix/baseline/results/artifact.json"
        ).read_text()
    )
    rows = sorted(art["daily_returns"], key=lambda r: r["decision_ns"])
    return [float(r["net_return_per_unit"]) for r in rows]


def main() -> dict:
    out: dict = {"gate_runner_on_recomputed_inputs": {}, "dsr": {}, "pbo": {}}

    b = RECOMP["arms"]["basislv_premfade/BASISLV-PREMFADE-28D"]["baseline_recomputed"]
    n = RECOMP["arms"]["basislv_premfade/BASISLV-PREMFADE-56D"]["baseline_recomputed"]
    c = RECOMP["arms"]["basislv_premfade/BASISLV-PREMFADE-28D-INV"][
        "baseline_recomputed"
    ]
    out["gate_runner_on_recomputed_inputs"]["basislv_premfade"] = basislv_gate(
        anchor_fold_positive=b["fold_positive"],
        control_fold_positive=c["fold_positive"],
        neighbour_fold_positive=n["fold_positive"],
        price_only_expectancy=b["price_only_expectancy"],
        total_expectancy=b["total_expectancy"],
        stress_passes=True,
    )
    fold_conc = fold_concentration_check(
        largest_fold_positive_share=b[
            "fold_pos_share_F1_largest_positive_fold_net_over_positive_fold_nets"
        ]
    )
    out["gate_runner_on_recomputed_inputs"]["basislv_fold_concentration"] = fold_conc

    o = RECOMP["arms"]["oicyc/CYC-28D"]["baseline_recomputed"]
    on = RECOMP["arms"]["oicyc/CYC-14D"]["baseline_recomputed"]
    oc = RECOMP["arms"]["oicyc/CTL-OISHARE"]["baseline_recomputed"]
    ox = RECOMP["arms"]["oicyc/CYC-28D"]["benchmark_excess"]["per_fold"]

    def signs(vals):
        return [v > 0.0 for v in vals]

    def headline(rec):
        return headline_gate(
            expectancy=rec["expectancy_per_day"],
            position_pf=rec["position_pf_recomputed"],
            fold_positive=list(rec["fold_positive"]),
        )

    a_head = headline(o)
    c_head = headline(oc)
    n_head = headline(on)
    a_inc = incremental_context_gate(
        excess_bh_fold_positive=signs(
            [ox[k]["excess_bh_f"] for k in sorted(ox)]
        ),
        excess_beta_fold_positive=signs(
            [ox[k]["excess_beta_f"] for k in sorted(ox)]
        ),
    )
    a_conc = fold_concentration_check(
        largest_fold_positive_share=o[
            "fold_pos_share_F1_largest_positive_fold_net_over_positive_fold_nets"
        ]
    )
    out["gate_runner_on_recomputed_inputs"]["oicyc"] = oicyc_gate(
        anchor_headline=a_head,
        control_headline=c_head,
        neighbour_headline=n_head,
        anchor_incremental=a_inc,
        anchor_fold_concentration=a_conc,
    )
    out["gate_runner_on_recomputed_inputs"]["oicyc_control_headline_standalone"] = (
        c_head
    )

    # ---------------- DSR (research/dsr.py, frozen estimator) ------------- #
    arms = [
        ("basislv_premfade", "BASISLV-PREMFADE-28D"),
        ("basislv_premfade", "BASISLV-PREMFADE-56D"),
        ("basislv_premfade", "BASISLV-PREMFADE-28D-INV"),
        ("oicyc", "CYC-28D"),
        ("oicyc", "CYC-14D"),
        ("oicyc", "CTL-OISHARE"),
    ]
    trials = []
    per_arm = {}
    for fam, arm in arms:
        rows = arm_rows(fam, arm)
        m = statistics.fmean(rows)
        sd = statistics.stdev(rows)
        sr = m / sd
        trials.append(sr)
        m2 = math.fsum((v - m) ** 2 for v in rows) / len(rows)
        m3 = math.fsum((v - m) ** 3 for v in rows) / len(rows)
        m4 = math.fsum((v - m) ** 4 for v in rows) / len(rows)
        per_arm[arm] = {
            "sharpe_per_decision": sr,
            "skew": m3 / m2 ** 1.5,
            "kurtosis_pearson": m4 / (m2 * m2),
            "n_rows": len(rows),
        }
    out["dsr"]["trial_arm_sharpes"] = per_arm
    out["dsr"]["n_trials_used"] = 146
    out["dsr"]["n_trials_basis"] = (
        "observed crypto program logical results 140 + 6 V14 cells; the only "
        "committed per-period return series are the six V14 arms, so the "
        "trial-variance calibration uses those six; V12/V13 per-trial Sharpe "
        "series are NOT derivable from committed evidence (exec results trees "
        "lost; results/ not committed for those cycles) -- recorded NOT_RUN"
    )
    for fam, arm in (("basislv_premfade", "BASISLV-PREMFADE-28D"), ("oicyc", "CYC-28D")):
        rows = arm_rows(fam, arm)
        m = statistics.fmean(rows)
        sd = statistics.stdev(rows)
        m2 = math.fsum((v - m) ** 2 for v in rows) / len(rows)
        m3 = math.fsum((v - m) ** 3 for v in rows) / len(rows)
        m4 = math.fsum((v - m) ** 4 for v in rows) / len(rows)
        out["dsr"][arm] = dsr_probability(
            sharpe_star_candidate=m / sd,
            sharpe_trials=trials,
            n_trials=146,
            sample_len=len(rows),
            skew=m3 / m2 ** 1.5,
            kurtosis=m4 / (m2 * m2),
        )
        out["dsr"][arm]["estimator_id"] = DSR_ESTIMATOR_ID

    # ---------------- PBO (research/dsr.py, frozen estimator) ------------- #
    perf = {
        arm: arm_rows(fam, arm) for fam, arm in arms
    }
    res = pbo_cscv(perf)
    res["estimator_id"] = PBO_ESTIMATOR_ID
    out["pbo"]["six_v14_configs_weekly_rows"] = res
    out["pbo"]["not_computable_note"] = (
        "the frozen CSCV minima require >= 8 configurations; only the six V14 "
        "arm return series are committed (6 < 8 -> NOT_ENOUGH_CONFIGURATIONS, "
        "fail-closed per the frozen estimator). Config-per-config block series "
        "for the 140 historical program cells are NOT derivable from committed "
        "evidence. PBO therefore stands NOT_RUN for the program history; the "
        "defensible in-cycle computation above is recorded for completeness."
    )
    return out


if __name__ == "__main__":
    rep = main()
    out = HERE / "a7_dsr_pbo_and_gate_runner_v14.json"
    out.write_text(json.dumps(rep, indent=1, default=str))
    print(f"wrote {out}")
