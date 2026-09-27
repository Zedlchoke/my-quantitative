"""R3 re-comparison of the r3-canonical books (lane I engine vs lane_x).

Post-r3 rebuild of BOTH implementations (G3_FREEZE_ADDENDUM_r3 re-run
protocol).  Target: record-key sets identical + fields byte-identical on
the intersection; every residual diff classified
r3-SPEC_AMBIGUITY / DEFECT / DATA_VARIANT with counts.

R2-6 boundary: records only — key sets, per-record field diffs and
population counts.  NO return/expectancy/PnL aggregate is computed.

Run: .venv/bin/python research/control/EVENT-MECHANISMS-V1/reconciliation/compare_r3.py
"""
from __future__ import annotations

import gzip
import json
import os
import sys

WT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
CTL = os.path.join(WT, "research", "control", "EVENT-MECHANISMS-V1")
LANE_I = os.path.join(CTL, "engine", "evidence")
LANE_X = os.path.join(CTL, "lane_x", "output")
OUT_DIR = os.path.join(CTL, "reconciliation")

# Shared decision fields compared byte-identically on the intersection.
SHARED_FIELDS = (
    "direction_session", "direction", "entry_session", "entry_price",
    "exit_session", "exit_price", "delisting_exit", "fold", "stratum",
    "hold_sessions", "exclusions_applied", "dv_band_class",
    "dvmed60_decision", "cost_entry_bps_x1", "cost_exit_bps_x1",
    "ticker_reuse_risk",
)


def read_jsonl(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:
        return [json.loads(l) for l in f if l.strip()]


def key_of(rec):
    return (rec["cik"], rec["acceptance_utc"])


def field_bytes(v):
    return json.dumps(v, sort_keys=True)


def compare_arm(arm, lane_i_records, lane_x_records, results, residual,
                i_excl_reasons=None):
    i_map = {}
    for r in lane_i_records:
        i_map[key_of(r)] = r
    x_map = {}
    for r in lane_x_records:
        x_map[key_of(r)] = r
    i_keys, x_keys = set(i_map), set(x_map)
    inter = i_keys & x_keys
    only_i, only_x = i_keys - x_keys, x_keys - i_keys

    field_stats = {f: {"mismatch": 0, "samples": []} for f in SHARED_FIELDS}
    identical = 0
    diff_records = []
    for k in sorted(inter):
        ri, rx = i_map[k], x_map[k]
        bad = []
        for f in SHARED_FIELDS:
            if field_bytes(ri.get(f)) != field_bytes(rx.get(f)):
                field_stats[f]["mismatch"] += 1
                if len(field_stats[f]["samples"]) < 3:
                    field_stats[f]["samples"].append(
                        {"key": k, "lane_i": ri.get(f), "lane_x": rx.get(f),
                         "lane_i_forced_flat": ri.get("forced_flat"),
                         "lane_x_exit_rolled": rx.get("exit_rolled")})
                bad.append(f)
        if bad:
            diff_records.append({"key": k, "fields": bad,
                                 "lane_i_forced_flat": ri.get("forced_flat"),
                                 "lane_x_exit_rolled": rx.get("exit_rolled"),
                                 "lane_i_exit": ri.get("exit_session"),
                                 "lane_x_exit": rx.get("exit_session")})
        else:
            identical += 1

    # residual attribution of key diffs
    DAY_BASIS = ("SPEC_AMBIGUITY: A2 issuer-day basis unruled at r3 "
                 "(lane I keys (cik, UTC acceptance date); lane_x (cik, transaction_date))")
    VALUE_AGG = ("SPEC_AMBIGUITY: A2 value aggregation / unpriced-drop semantics "
                 "(unruled at r3): row-level drop (lane I) vs transaction-level drop (lane_x)")
    x_instants = {(r.get("cik"), r.get("acceptance_utc")) for r in lane_x_records}
    i_instants = {(r.get("cik"), r.get("acceptance_utc")) for r in lane_i_records}
    for k in sorted(only_i):
        r = i_map[k]
        if r.get("forced_flat"):
            cls = "SPEC_AMBIGUITY: fold force-flat at book stage (lane I convention, unruled at r3)"
        elif arm == "A2_anchor":
            # same triggering instant regrouped under another day on lane_x
            if (k[0], k[1]) in x_instants:
                cls = DAY_BASIS + " [same instant present on lane_x]"
            elif any(c == k[0] for c, _ in x_instants):
                cls = DAY_BASIS + " [issuer present on lane_x under other day]"
            else:
                cls = VALUE_AGG
        else:
            cls = "UNATTRIBUTED"
        residual.append({"arm": arm, "side": "only_lane_i", "key": k,
                         "class": cls})
    for k in sorted(only_x):
        if arm == "A2_anchor":
            if (k[0], k[1]) in i_instants:
                cls = DAY_BASIS + " [same instant present on lane_i]"
            elif any(c == k[0] for c, _ in i_instants):
                cls = DAY_BASIS + " [issuer present on lane_i under other day]"
            else:
                cls = VALUE_AGG
        else:
            reason = (i_excl_reasons or {}).get(k)
            if reason == "FOLD_BOUNDARY_NO_WINDOW":
                cls = "SPEC_AMBIGUITY: fold force-flat at book stage (lane I convention, unruled at r3)"
            elif reason:
                cls = f"UNATTRIBUTED (lane I excludes: {reason})"
            else:
                cls = "UNATTRIBUTED"
        residual.append({"arm": arm, "side": "only_lane_x", "key": k,
                         "class": cls})
    for d in diff_records:
        if d["lane_i_forced_flat"]:
            cls = "SPEC_AMBIGUITY: fold force-flat at book stage (lane I convention, unruled at r3)"
        elif d["fields"] == ["exit_session", "exit_price"] or (
                "exit_session" in d["fields"] and set(d["fields"]) <= {"exit_session", "exit_price", "delisting_exit", "exclusions_applied"}):
            cls = "UNATTRIBUTED"
        else:
            cls = "UNATTRIBUTED"
        residual.append({"arm": arm, "side": "field_diff", "key": d["key"],
                         "fields": d["fields"], "class": cls})

    arm_res = {
        "lane_i_records": len(lane_i_records),
        "lane_x_records": len(lane_x_records),
        "intersection": len(inter),
        "only_lane_i": len(only_i),
        "only_lane_x": len(only_x),
        "key_sets_identical": not only_i and not only_x,
        "field_identical_records": identical,
        "field_diff_records": len(diff_records),
        "byte_identical": identical == len(inter) and not only_i and not only_x,
        "field_mismatches": {f: s["mismatch"] for f, s in field_stats.items()},
        "field_samples": {f: s["samples"] for f, s in field_stats.items() if s["samples"]},
    }
    results[arm] = arm_res
    return diff_records


_PIPELINE_ORDER = (
    "NO_PANEL_FOR_TICKER", "NO_SESSION_AFTER_ACCEPTANCE", "NO_ENTRY_SESSION",
    "ZERO_DIRECTION_SESSION_MOVE", "FOLD_BOUNDARY_NO_WINDOW",
    "CORP_ACTION_IN_WINDOW", "ENTRY_BAR_UNFILLABLE_B1B2",
    "BELOW_DV_FLOOR_AT_DECISION",
)


def first_exclusion_reason(excl_rows):
    """key -> highest-pipeline-order exclusion reason (lane I side).

    lane I exclusion rows carry (cik, reason, event_id) but not always the
    acceptance instant; the event_id embeds it as
    '<arm>:<cik>:<acceptance_utc>:<accession>' (acceptance itself contains
    ':' so re-join the middle segments).
    """
    rank = {r: i for i, r in enumerate(_PIPELINE_ORDER)}
    first = {}
    for e in excl_rows:
        eid = e.get("event_id", "")
        parts = eid.split(":")
        if len(parts) < 4:
            k = (e.get("cik"), e.get("acceptance_utc"))
        else:
            k = (parts[1], ":".join(parts[2:-1]))
        reason = e.get("reason")
        if reason not in rank:
            continue
        if k not in first or rank[reason] < rank[first[k]]:
            first[k] = reason
    return first


def main():
    i_a1 = [r for r in read_jsonl(os.path.join(LANE_I, "a1_decisions.jsonl"))
            if r["control_variant"] == "PRIMARY"]
    i_anchor = [r for r in i_a1 if r["arm_id"] == "A1-ANCHOR"]
    i_n2 = [r for r in i_a1 if r["arm_id"] == "A1-N2"]
    i_a2 = [r for r in read_jsonl(os.path.join(LANE_I, "a2_decisions.jsonl"))
            if r["control_variant"] == "PRIMARY" and r["arm_id"] == "A2-ANCHOR"]
    i_a1_excl = [e for e in read_jsonl(os.path.join(LANE_I, "a1_exclusions.jsonl"))
                 if e.get("arm_id") == "A1-ANCHOR"]
    i_n2_excl = [e for e in read_jsonl(os.path.join(LANE_I, "a1_exclusions.jsonl"))
                 if e.get("arm_id") == "A1-N2"]
    i_a2_excl = [e for e in read_jsonl(os.path.join(LANE_I, "a2_exclusions.jsonl"))
                 if e.get("arm_id") == "A2-ANCHOR"]

    x_anchor = read_jsonl(os.path.join(LANE_X, "A1_anchor_book.jsonl.gz"))
    x_n2 = read_jsonl(os.path.join(LANE_X, "A1_N2_book.jsonl.gz"))
    x_a2 = read_jsonl(os.path.join(LANE_X, "A2_anchor_book.jsonl.gz"))

    results = {}
    residual = []
    for arm, li, lx, iex in (("A1_anchor", i_anchor, x_anchor, i_a1_excl),
                             ("A1_N2", i_n2, x_n2, i_n2_excl),
                             ("A2_anchor", i_a2, x_a2, i_a2_excl)):
        compare_arm(arm, li, lx, results, residual, first_exclusion_reason(iex))

    # A2 secondary match on the shared triggering filing (cik, acceptance_utc)
    # primary A2 key bases differ (structural): lane I = UTC acceptance date,
    # lane_x = transaction_date (unruled at r3 -> residual SPEC_AMBIGUITY).
    i_map = {key_of(r): r for r in i_a2}
    x_map = {key_of(r): r for r in x_a2}
    inter = sorted(set(i_map) & set(x_map))
    a2_fields_bad = 0
    a2_bad_samples = []
    for k in inter:
        ri, rx = i_map[k], x_map[k]
        bad = [f for f in SHARED_FIELDS
               if field_bytes(ri.get(f)) != field_bytes(rx.get(f))]
        if bad:
            a2_fields_bad += 1
            if len(a2_bad_samples) < 5:
                a2_bad_samples.append({"key": k, "fields": bad,
                                       "lane_i": {f: ri.get(f) for f in bad},
                                       "lane_x": {f: rx.get(f) for f in bad}})
    results["A2_anchor_secondary_match_on_triggering_filing"] = {
        "lane_i_unique_instants": len(i_map),
        "lane_x_unique_instants": len(x_map),
        "matched": len(inter),
        "field_identical": len(inter) - a2_fields_bad,
        "field_diff": a2_fields_bad,
        "samples": a2_bad_samples,
    }

    # residual classification counts
    class_counts = {}
    for r in residual:
        class_counts[r["class"]] = class_counts.get(r["class"], 0) + 1

    out = {
        "schema": "emv1_r3_recomparison@1",
        "inputs": {
            "lane_i": "research/control/EVENT-MECHANISMS-V1/engine/evidence/{a1,a2}_decisions.jsonl (PRIMARY)",
            "lane_x": "research/control/EVENT-MECHANISMS-V1/lane_x/output/*_book.jsonl.gz",
            "shared_fields_compared": list(SHARED_FIELDS),
        },
        "arms": results,
        "residual_classification_counts": class_counts,
        "residual_records": residual,
        "r2_6_note": "records-only comparison; no return/expectancy/PnL aggregate computed",
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "comparison_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)

    for arm in ("A1_anchor", "A1_N2", "A2_anchor"):
        r = results[arm]
        print(f"[{arm}] I={r['lane_i_records']} X={r['lane_x_records']} "
              f"inter={r['intersection']} onlyI={r['only_lane_i']} "
              f"onlyX={r['only_lane_x']} field_identical={r['field_identical_records']}/{r['intersection']}")
    sec = results["A2_anchor_secondary_match_on_triggering_filing"]
    print(f"[A2 secondary] matched={sec['matched']} field_identical={sec['field_identical']}")
    print("residual classes:", json.dumps(class_counts, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
