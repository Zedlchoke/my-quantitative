#!/usr/bin/env python
"""JRV2-DECISION-AUDIT-V1 — unblind the blind review.

Joins blind_reviews.jsonl with the sealed sampling design and computes
blind-vs-JEV agreement. This is CONSENSUS measurement, NOT accuracy: no
pre-registered independent ground truth exists for these states.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

AUDIT = Path(__file__).resolve().parent.parent
BLIND = AUDIT / "blind"

LAB = {"ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND",
       "TRANSITION_UNKNOWN"}


def main():
    reviews = {json.loads(l)["case_id"]: json.loads(l)
               for l in open(BLIND / "blind_reviews.jsonl")}
    design = json.load(open(BLIND / "sampling.json"))
    sample = {s["case_id"]: s for s in design["sample_sealed"]}

    assert set(reviews) == set(sample), "review/sample id mismatch"

    rows = []
    for cid, r in reviews.items():
        s = sample[cid]
        blind = r["blind_verdict"]
        jev = s["effective_label_sealed"]
        rows.append({
            "case_id": cid, "cell": s["cell"], "stratum": s["stratum"],
            "zone": s["zone"], "strength": s["strength"], "fold": s["fold"],
            "blind": blind, "blind_conf": r["confidence"],
            "jev": jev, "jev_reason": s["effective_reason_sealed"],
            "jev_conf": float(s["phase_conf_sealed"]) if s["phase_conf_sealed"] else None,
            "agree": blind == jev,
            "agree_conditional": (blind == jev) if blind in
                                 ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND") else None,
        })

    n = len(rows)
    labeled = [r for r in rows if r["blind"] != "UNDETERMINED"]
    overall = {
        "n": n,
        "blind_undetermined_n": n - len(labeled),
        "blind_undetermined_share": round((n - len(labeled)) / n, 4),
        "agree_exact_n": sum(1 for r in rows if r["agree"]),
        "agree_exact_share": round(sum(1 for r in rows if r["agree"]) / n, 4),
        "agree_excl_undetermined_n": sum(1 for r in labeled if r["agree_conditional"]),
        "agree_excl_undetermined_share": round(
            sum(1 for r in labeled if r["agree_conditional"]) / max(1, len(labeled)), 4),
    }

    by_stratum = {}
    for key in sorted({(r["cell"], r["stratum"]) for r in rows}):
        rs = [r for r in rows if (r["cell"], r["stratum"]) == key]
        lab = [r for r in rs if r["blind"] != "UNDETERMINED"]
        by_stratum[f"{key[0]}|{key[1]}"] = {
            "n": len(rs),
            "blind_undetermined": len(rs) - len(lab),
            "jev_label": key[1],
            "agree_exact": sum(1 for r in rs if r["agree"]),
            "agree_excl_und": sum(1 for r in lab if r["agree_conditional"]),
            "agree_excl_und_share": round(
                sum(1 for r in lab if r["agree_conditional"]) / max(1, len(lab)), 3),
        }

    # what does each side say when the other declines?
    blind_und_when_jev_labeled = sum(
        1 for r in rows if r["blind"] == "UNDETERMINED" and r["jev"] != "TRANSITION_UNKNOWN")
    jev_unk_when_blind_labeled = sum(
        1 for r in rows if r["blind"] != "UNDETERMINED" and r["jev"] == "TRANSITION_UNKNOWN")
    refusal = {
        "blind_UNDETERMINED_while_JEV_labeled": blind_und_when_jev_labeled,
        "JEV_UNKNOWN_while_blind_labeled": jev_unk_when_blind_labeled,
        "both_decline": sum(1 for r in rows if r["blind"] == "UNDETERMINED"
                            and r["jev"] == "TRANSITION_UNKNOWN"),
    }

    # confusion: blind-labeled cases vs JEV's phase (excluding UNKNOWN strata)
    conf = defaultdict(Counter)
    for r in rows:
        if r["blind"] != "UNDETERMINED":
            conf[r["blind"]][r["jev"]] += 1
    confusion = {k: dict(v) for k, v in conf.items()}

    # confidence-weighted
    conf_wise = {}
    for conf_level in ("high", "medium", "low"):
        rs = [r for r in rows if r["blind_conf"] == conf_level]
        lab = [r for r in rs if r["blind"] != "UNDETERMINED"]
        conf_wise[conf_level] = {
            "n": len(rs),
            "agree_exact_share": round(sum(1 for r in rs if r["agree"]) / max(1, len(rs)), 3),
            "agree_excl_und_share": round(
                sum(1 for r in lab if r["agree_conditional"]) / max(1, len(lab)), 3),
        }

    # zone / strength cuts
    cuts = {}
    for attr in ("zone", "strength"):
        cuts[attr] = {}
        for val in sorted({r[attr] for r in rows}):
            rs = [r for r in rows if r[attr] == val]
            lab = [r for r in rs if r["blind"] != "UNDETERMINED"]
            cuts[attr][val] = {
                "n": len(rs),
                "agree_excl_und_share": round(
                    sum(1 for r in lab if r["agree_conditional"]) / max(1, len(lab)), 3),
            }

    out = {
        "schema": "jrv2_decision_audit_unblind@1",
        "disclaimer": "blind-vs-JEV consensus measurement; NOT accuracy — "
                      "no pre-registered independent ground truth exists",
        "n_cases": n,
        "overall": overall,
        "by_cell_x_stratum": by_stratum,
        "refusal_matrix": refusal,
        "confusion_blind_label_to_jev": confusion,
        "by_blind_confidence": conf_wise,
        "by_zone_and_strength": cuts,
        "rows": rows,
    }
    (BLIND / "unblinded_agreement.json").write_text(json.dumps(out, indent=1))

    print("overall:", json.dumps(overall))
    for k, v in by_stratum.items():
        print(f"  {k}: n={v['n']} blind_und={v['blind_undetermined']} "
              f"agree_exact={v['agree_exact']} agree_excl_und={v['agree_excl_und_share']}")
    print("refusal:", json.dumps(refusal))
    print("by_blind_confidence:", json.dumps(conf_wise))
    print("by_zone:", json.dumps(cuts["zone"]))
    print("by_strength:", json.dumps(cuts["strength"]))


if __name__ == "__main__":
    main()
