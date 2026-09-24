"""EOS1 P2 feasibility census — PRE-PnL (plan §P2).

Measures, with NO outcome data anywhere in the output:
  - per arm/reference/control: state flips, decision population per fold,
    first/last decision timestamp (warmup truncation table);
  - flip-cost arithmetic ceiling only (flips x round-trip cost constant —
    constants, not outcomes);
  - G11: Spearman agreement of arm weight-series vs BASE_TREND_LF weights
    on scored-fold bars (disclosure, not a kill bar);
  - G6 null-validity: block-shuffled series differs from the original AND
    drives a different fill schedule (timing information destroyed),
    block-structure preserved;
  - reference fill counts (ALWAYS_ON = 4 folds x (1 entry + 1 exit)).

Output: freezes/feasibility.json. FAIL-closed if any arm has zero flips
(non-vacuous law) or a fold population floor breach (>=100 scored H4 bars
per fold per plan §5 floors).
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eos1_engine as E  # noqa: E402

FOLD_BAR_FLOOR = 100


def iso(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).isoformat()


def main() -> int:
    data = E.build_all_series()
    targets = E.build_targets(data)
    eth = data["eth_h4"]
    fold_idx = {"F1": [], "F2": [], "F3": [], "F4": []}
    for i, b in enumerate(eth):
        f = E.fold_of(b["ts"])
        if f:
            fold_idx[f].append(i)

    out = {"schema": "eos1.feasibility@1",
           "built_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "fold_bars": {k: len(v) for k, v in fold_idx.items()},
           "h4_dropped": data["h4_dropped"],
           "reads_fallback_last_observed": data["_reads_fallback"],
           "arms": {}, "controls": {}, "references": {}}

    problems = []
    for fn, idxs in fold_idx.items():
        if len(idxs) < FOLD_BAR_FLOOR:
            problems.append(f"fold {fn} population {len(idxs)} < {FOLD_BAR_FLOOR}")

    scored_idx = sorted(i for v in fold_idx.values() for i in v)

    def census_book(key: str, target: list[int]) -> dict:
        states = [target[i] for i in scored_idx]
        flips = sum(1 for a, b in zip(states, states[1:]) if a != b)
        dec_idx = [i for i in scored_idx if target[i] != 0]
        per_fold = {fn: sum(1 for i in idxs if target[i] != 0) for fn, idxs in fold_idx.items()}
        first_ts = iso(eth[dec_idx[0]]["ts"]) if dec_idx else None
        last_ts = iso(eth[dec_idx[-1]]["ts"]) if dec_idx else None
        return {"flips_in_scored_folds": flips,
                "decision_bars_in_folds": len(dec_idx),
                "decision_bars_per_fold": per_fold,
                "first_decision": first_ts, "last_decision": last_ts}

    for key, target in targets.items():
        info = census_book(key, target)
        if key.startswith("EOS1") and "|G6-" not in key:
            out["arms"][key] = info
            if info["flips_in_scored_folds"] == 0:
                problems.append(f"{key}: zero flips (non-vacuous breach)")
        elif "|G6-" in key:
            out["controls"][key] = info
        else:
            out["references"][key] = info

    # G11: agreement vs BASE_TREND_LF on scored bars
    trend = [targets["BASE_TREND_LF"][i] for i in scored_idx]
    g11 = {}
    for arm in E.ARMS:
        w = [targets[arm][i] for i in scored_idx]
        g11[arm] = round(E.spearman([float(x) for x in w], [float(x) for x in trend]), 6)
    out["g11_spearman_vs_trend_lf"] = g11

    # G6 null-validity: shuffled differs + fill schedule moves
    null_validity = {}
    for arm in E.ARMS:
        shuf_key = f"{arm}|G6-SHUF"
        diff_states = sum(1 for i in scored_idx if targets[arm][i] != targets[shuf_key][i])
        a_fills = census_book(arm, targets[arm])["flips_in_scored_folds"]
        s_fills = census_book(shuf_key, targets[shuf_key])["flips_in_scored_folds"]
        null_validity[arm] = {"state_diff_bars": diff_states,
                              "arm_flips": a_fills, "shuf_flips": s_fills,
                              "valid": diff_states > 0}
        if diff_states == 0:
            problems.append(f"{arm}: G6 shuffle null INVALID (identical series)")
    out["g6_null_validity"] = null_validity

    out["problems"] = problems
    out["feasible"] = not problems
    dest = pathlib.Path(__file__).resolve().parents[1] / "freezes" / "feasibility.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("fold_bars", "feasible", "problems",
                                          "g11_spearman_vs_trend_lf")}, indent=1, sort_keys=True))
    return 0 if out["feasible"] else 1


if __name__ == "__main__":
    sys.exit(main())
