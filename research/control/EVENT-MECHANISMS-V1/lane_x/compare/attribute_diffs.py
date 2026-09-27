"""Attribution of every key-set difference to a named reason on one side,
plus per-arm strata sanity counts (P5).  Records only; no return aggregates."""

from __future__ import annotations

import collections
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compare.build_comparison import (  # noqa: E402
    ENGINE_EV, WT_ROOT, a1_key, load_mine, load_theirs)
from engine_x.divsplits import ExDateIndex  # noqa: E402


def rd(p):
    with gzip.open(p, "rt") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def main() -> int:
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    ex = ExDateIndex(
        os.path.join(WT_ROOT, ".staging_eventmech", "integration", ".staging_sec_v13", "eodhd_div"),
        os.path.join(WT_ROOT, ".staging_eventmech", "integration", ".staging_sec_v13", "eodhd_splits"))
    dv = os.path.join(WT_ROOT, ".staging_eventmech", "integration", ".staging_sec_v13", "eodhd_div")
    div_stems_exact = {f[:-5] for f in os.listdir(dv) if f.endswith(".json")}

    their_excl = {"A1-ANCHOR": {}, "A1-N2": {}}
    for r in rd(os.path.join(ENGINE_EV, "a1_exclusions.jsonl.gz")):
        if r.get("arm_id") in their_excl:
            their_excl[r["arm_id"]][(r["cik"], ":".join(r["event_id"].split(":")[2:5]))] = r["reason"]

    attribution = {}
    strata = {}
    for arm, arm_id in (("A1_anchor", "A1-ANCHOR"), ("A1_N2", "A1-N2")):
        m = load_mine(f"{arm.replace('_', '_')}_book.jsonl.gz".replace("A1_anchor", "A1_anchor"))
        t = load_theirs("a1_decisions.jsonl.gz", arm_id)
        mm = {a1_key(r): r for r in m}
        tt = {a1_key(r): r for r in t}
        only_x = sorted(set(mm) - set(tt))
        only_i = sorted(set(tt) - set(mm))

        reasons = collections.Counter(their_excl[arm_id].get(k, "UNMAPPED") for k in only_x)
        decomp = collections.Counter()
        my_side = {}
        for row in rd(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "output", "exclusions.json.gz")):
            if row.get("arm") != ("A1_anchor" if arm == "A1_anchor" else "A1_N2"):
                continue
            for r in row.get("excluded", []):
                my_side[(r["cik"], r["acceptance_utc"])] = r["reason"]
            for r in row.get("dropped", []):
                my_side[(r["cik"], r["acceptance_utc"])] = r["reason"]
        for k in only_i:
            r = my_side.get(k, "NOT_IN_MY_EXCLUSIONS")
            my_side_reason = r
            trec = tt[k]
            d, s = ex.ex_dates(trec["ticker"])
            inside = [x for x in d | s
                      if trec["entry_session"] <= x <= trec["exit_session"]]
            exact = trec["ticker"] in div_stems_exact
            if my_side_reason != "CA_EXCLUSION":
                sub = f"my_side:{my_side_reason}"
            elif not exact:
                sub = "lane_i_div_file_case_miss"
            elif not inside:
                sub = "lane_i_force_flat_shortened_window"
            else:
                sub = "other"
            decomp[sub] += 1

        attribution[arm] = {
            "only_lane_x_total": len(only_x),
            "only_lane_x_mapped_to_lane_i_exclusion_reason": dict(reasons.most_common()),
            "only_lane_x_unmapped": sum(v for k, v in reasons.items() if k == "UNMAPPED"),
            "only_lane_i_total": len(only_i),
            "only_lane_i_decomposition": dict(decomp.most_common()),
        }
        strata[arm] = {
            "lane_x_booked_by_stratum": dict(collections.Counter(
                r["stratum"] for r in m)),
            "lane_i_booked_by_stratum": dict(collections.Counter(
                r["stratum"] for r in t)),
            "lane_x_booked_by_fold": dict(collections.Counter(r["fold"] for r in m)),
            "lane_i_booked_by_fold": dict(collections.Counter(r["fold"] for r in t)),
        }

    # A2 secondary match (same triggering filing) — mechanics comparison
    m = load_mine("A2_anchor_book.jsonl.gz")
    t = load_theirs("a2_decisions.jsonl.gz", "A2-ANCHOR")
    mm, tt = {}, {}
    for r in m:
        mm.setdefault((r["cik"], r["acceptance_utc"]), []).append(r)
    for r in t:
        tt.setdefault((r["cik"], r["acceptance_utc"]), []).append(r)
    inter = sorted(set(mm) & set(tt))

    def peq(a, b):
        return a is not None and b is not None and abs(float(a) - float(b)) <= 1e-9

    cnt = collections.Counter()
    entry_shift = collections.Counter()
    for k in inter:
        a, b = mm[k][0], tt[k][0]
        for f, eq in (("entry_session", a["entry_session"] == b["entry_session"]),
                      ("exit_session", a["exit_session"] == b["exit_session"]),
                      ("entry_price", peq(a["entry_price"], b["entry_price"])),
                      ("exit_price", peq(a["exit_price"], b["exit_price"])),
                      ("direction_session_shape", (a["direction_session"] == b["direction_session"])),
                      ("stratum", a["stratum"] == b["stratum"]),
                      ("fold", a["fold"] == b["fold"]),
                      ("delisting_exit", bool(a["delisting_exit"]) == bool(b["delisting_exit"]))):
            if not eq:
                cnt[f] += 1
    attribution["A2_anchor_secondary_match_on_acceptance_instant"] = {
        "lane_x_unique_instants": len(mm),
        "lane_i_unique_instants": len(tt),
        "matched": len(inter),
        "field_mismatches": dict(cnt.most_common()),
        "note": "stratum/fold/delisting agree fully; entry/exit differences are the "
                "A2 entry-law divergence (lane I uses A1-style direction+1 entry "
                "for A2 vs R2-3 'first session open strictly after the acceptance instant')",
    }

    with open(os.path.join(out_dir, "key_diff_attribution.json"), "w") as fh:
        json.dump({"attribution": attribution, "strata_sanity": strata}, fh,
                  sort_keys=True, indent=1)
        fh.write("\n")
    print(json.dumps({"attribution": attribution, "strata": strata}, sort_keys=True)[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
