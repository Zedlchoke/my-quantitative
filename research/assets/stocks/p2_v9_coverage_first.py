"""V9 P2: coverage-first for the death-inclusive cohort (PLAN_stocks_v9 §3).

Published BEFORE any D1 proposal brief. Two questions, no returns computed:

1. per-clock DEAD-leg fundamentals coverage: for each of the 154 frozen
   fundable clocks (field, age bound) the pooled multi-vintage as-of
   coverage among dead filers at the same 30 frozen quarterly S0 decision
   dates, using the inherited V6 semantics (latest vintage strictly before
   the gate, age-bounded). Denominator = dead filers mapped to the field
   (identical to the V6 "covered / mapped" convention).
2. per-name price coverage from the P0d integrity scan (already computed
   there; summarised here for the proposal gate).

S1 is never listed. Proposals may cite only clocks that are funded for the
dead leg by this artifact (plus the price leg).

Usage:
  python -m research.assets.stocks.p2_v9_coverage_first build
"""

import json
import os
import sys
import datetime

from research.assets.stocks.p0a_multivintage import date_to_ord, parse_iso_utc

CONTROL = "research/control/stocks_free_v9_run"
OUT = f"{CONTROL}/p2_v9_coverage_first.json"
PANEL = ".staging_sec_v9/multivintage_panel.jsonl"
PANEL_SHA = "67591464ee49acc159886143a379bda5890b1df602818b600d7938df92af1447"
COHORT = f"{CONTROL}/cohort_v9.json"
SCAN = f"{CONTROL}/p0d_v9_integrity_scan.json"
CLOCKS = "research/control/stocks_free_v6_run/p0a_fundable_clocks.json"
V6_CENSUS = "research/control/stocks_free_v6_run/p0a_coverage_census.json"
S0_START, S0_END = "2018-04-04", "2025-07-24"


def build():
    clocks_doc = json.load(open(CLOCKS))
    funded = [c for c in clocks_doc["clocks"] if c.get("proposed_status") == "FUNDED_CANDIDATE"]
    assert len(funded) == 154, f"expected 154 funded clocks, got {len(funded)}"

    cohort = json.load(open(COHORT))
    dead = {m["cik"] for m in cohort["members"]["DEAD_EVIDENCED"]}

    v6 = json.load(open(V6_CENSUS))
    decision_dates = v6["decision_dates"]
    date_ords = sorted(date_to_ord(parse_iso_utc(d + "T00:00:00+00:00").date()) for d in decision_dates)

    # single streaming pass over the panel: avail-day sets per (dead entity, field)
    avail_sets = {}
    total_rows = dead_rows = 0
    with open(PANEL, "r", encoding="utf-8") as f:
        for line in f:
            total_rows += 1
            r = json.loads(line)
            e = r["e"]
            if e not in dead:
                continue
            dead_rows += 1
            avail_sets.setdefault((e, r["f"]), set()).add(
                date_to_ord(parse_iso_utc(r["avail"] + "T00:00:00+00:00").date()))

    mapped = {}
    for (e, f), avails in avail_sets.items():
        mapped.setdefault(f, {})[e] = sorted(avails)

    per_clock = []
    for c in funded:
        field, age = c["field"], c.get("max_age_days")
        filers = mapped.get(field, {})
        denom = len(filers)
        if denom == 0:
            per_clock.append({"field": field, "age_days": age, "clock": c["clock"],
                              "dead_pooled_mean_coverage": 0.0, "dead_mapped": 0})
            continue
        per_date = []
        for t in date_ords:
            covered = 0
            for e, avails in filers.items():
                # latest filed vintage strictly before the gate, age-bounded
                lo = (t - age) if age is not None else None
                hit = False
                for a in reversed(avails):
                    if a < t:
                        hit = lo is None or a >= lo
                        break
                if hit:
                    covered += 1
            per_date.append(covered / denom)
        per_clock.append({
            "field": field, "age_days": age, "clock": c["clock"],
            "dead_mapped": denom,
            "dead_pooled_mean_coverage": round(sum(per_date) / len(per_date), 4),
            "dead_dates_at_or_above_0.4_of_30": sum(1 for x in per_date if x >= 0.4),
            "dead_dates_at_or_above_0.6_of_30": sum(1 for x in per_date if x >= 0.6),
        })

    scan = json.load(open(SCAN))
    counts = scan["counts"]
    last_dates = sorted(
        (v.get("last_trade_date") or "")[-10:] for v in scan["dead_verdicts"].values()
        if v.get("last_trade_date"))
    artifact = {
        "schema": "stocks_free_v9_run/p2_v9_coverage_first@1",
        "built_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer_role": "A1 (PLAN_stocks_v9 sec3 P2)",
        "authority": "coverage-first before D1: proposals may cite only clocks funded for the dead leg by this artifact and servable names; NO returns computed in Phase P; S1 never listed",
        "panel": {"path": PANEL, "sha256": PANEL_SHA,
                  "rows_total": total_rows, "rows_dead_entities": dead_rows},
        "cohort": {
            "alive": len(cohort["members"]["ALIVE_EVIDENCED"]),
            "dead_evidenced": len(cohort["members"]["DEAD_EVIDENCED"]),
            "gap_coverage_recorded": len(cohort["members"]["GAP_COVERAGE"]),
            "not_dead_name_alive": len(cohort["members"]["NOT_DEAD_NAME_ALIVE"]),
        },
        "price_leg": {
            "dead_price_confirmed": counts["DEAD_PRICE_CONFIRMED"],
            "not_dead_price_survival_excluded": counts["NOT_DEAD_PRICE_SURVIVAL"],
            "price_unavailable": counts["PRICE_UNAVAILABLE"],
            "dead_last_trade_range": [last_dates[0], last_dates[-1]] if last_dates else None,
        },
        "clock_semantics": "inherited V6 multi-vintage as-of: latest filed vintage strictly before the session gate, optional age bound; pooled coverage denominator = dead filers mapped to the field; same 30 frozen quarterly S0 decision dates as the V6 freeze",
        "n_funded_clocks_evaluated_on_dead_leg": len(per_clock),
        "per_clock_dead_coverage": per_clock,
    }
    funded_dead = [c for c in per_clock
                   if c["dead_mapped"] >= 50
                   and c["dead_pooled_mean_coverage"] >= 0.6]
    artifact["dead_leg_funded_clocks"] = {
        "rule": "dead mapped >= 50 filers AND pooled mean coverage >= 0.6 (inherit the V6 spirit; thresholds stated before any proposal exists)",
        "count": len(funded_dead),
        "clocks": [{"field": c["field"], "max_age_days": c["age_days"],
                    "coverage": c["dead_pooled_mean_coverage"],
                    "mapped": c["dead_mapped"]} for c in funded_dead],
    }
    json.dump(artifact, open(OUT, "w"), indent=1)
    print(json.dumps({"per_clock": len(per_clock), "dead_leg_funded": len(funded_dead), "out": OUT}))


if __name__ == "__main__":
    {"build": build}[sys.argv[1]]()
