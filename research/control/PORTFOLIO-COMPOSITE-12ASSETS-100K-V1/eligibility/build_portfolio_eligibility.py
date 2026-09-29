#!/usr/bin/env python
"""Portfolio eligibility table v2 — owner directive 2026-09-29 (2nd):

Novelty/ancestry NO LONGER EXCLUDES an idea from portfolio exploration.
Old-family rows and previously-rejected rows enter as DIAGNOSTIC
candidates carrying their failure history as an outcome_exposed label.
Remaining blocking gates are IMPLEMENTABILITY only: price data, PIT
evidence, cost authority (swap-profit), mechanizability, data ceiling.

v1 ladder preserved at git-history/session-1; this builder supersedes it
for the portfolio-complementarity question per the recorded owner
directive (see plan/AMENDMENT_OWNER_DIRECTIVE_2026-09-29.md).
"""
import csv, collections, json

REPO = "/Users/hoangminhlong/my-quantitative"
CENSUS = f"{REPO}/research/control/PORTFOLIO-ROUTER-12ASSETS-100K-V1/census/CENSUS_1200.tsv"
OUT = f"{REPO}/research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/eligibility/PORTFOLIO_ELIGIBILITY_1200.tsv"

F0 = {  # SLEEVE-FX5 F-0 court, kept as LABEL not exclusion (directive #2)
    "GBPUSD-S079": "REJECT_VARIANT_SAME_FAMILY", "USDJPY-S012": "REJECT_VARIANT_SAME_FAMILY",
    "EURUSD-S027": "REJECT_VARIANT_SAME_FAMILY", "AUDUSD-S001": "REJECT_VARIANT_SAME_FAMILY",
    "AUDUSD-S003": "REJECT_VARIANT_SAME_FAMILY", "AUDUSD-S017": "REJECT_VARIANT_SAME_FAMILY",
    "AUDUSD-S087": "REJECT_DATA_OR_COST", "AUDUSD-S088": "REJECT_DATA_OR_COST",
    "AUDUSD-S002": "REJECT_VARIANT_SAME_FAMILY", "USDCAD-S002": "REJECT_VARIANT_SAME_FAMILY",
    "AUDUSD-S046": "REJECT_NOT_STANDALONE", "USDCAD-S047": "REJECT_DATA_OR_COST",
    "EURUSD-S009": "REJECT_NOT_STANDALONE", "USDCAD-S025": "REJECT_VARIANT_SAME_FAMILY",
    "USDCAD-S004": "REJECT_VARIANT_SAME_FAMILY",
}
PRICE_AXIS = {
    "EURUSD": "M1_BIDASK_PANEL", "GBPUSD": "M1_BIDASK_PANEL", "USDJPY": "M1_BIDASK_PANEL",
    "USDCAD": "H1_BAR_PANEL", "AUDUSD": "H1_BAR_PANEL",
    "NZDUSD": "MISSING", "USDCHF": "MISSING", "XAGUSD": "MISSING",
    "BRENT": "MISSING", "WTI": "MISSING", "NATGAS": "MISSING", "XAUUSD": "DAILY_REFERENCE_ONLY",
}
COST_AXIS = {s: "PROVISIONAL_PENDING_COST_AUTHORITY" for s in
             ("EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD")}
for s in ("NZDUSD", "USDCHF", "XAUUSD", "XAGUSD", "BRENT", "WTI", "NATGAS"):
    COST_AXIS[s] = "NONE_NO_PANEL"

def pit_class(req: str) -> str:
    t = req.lower()
    # Macro keywords FIRST (calendar never rescues a row that also needs an
    # unevidenced macro series); bare 'news' removed so "Japan news calendar
    # (public schedule)" falls through to PRICE_PLUS_CALENDAR (skeptic F-4).
    if any(k in t for k in ["cot", "commitment"]):
        return "NEEDS_COT_PIT_UNEVIDENCED"
    if any(k in t for k in ["eia", "storage", "cushing", "feedgas", "weather", "inventor"]):
        return "NEEDS_EIA_PHYSICAL_PIT_UNEVIDENCED"
    if any(k in t for k in ["ois", "tips", "dxy", "forward", "yield", "breakeven", "sight",
                            "gdt", "opec", "options", "skew", "etf", "headline", "newswire",
                            "positioning", "flow", "implied", "swap rate", "sonia", "sofr"]):
        return "NEEDS_MACRO_PIT_UNEVIDENCED"
    # PIT-evidenced macro set is EXACTLY what the pr12a100k dossier pins:
    # EFFR, VIX, Brent−WTI (skeptic F-5: SOFR liveness-checked, NOT dossier-pinned).
    if any(k in t for k in ["vix", "effr", "brent-wti", "brent−wti"]):
        return "MACRO_PIT_EVIDENCED_PARTIAL"
    if "calendar" in t or "schedule" in t:
        return "PRICE_PLUS_CALENDAR"
    return "PRICE_ONLY"

def main() -> None:
    rows = list(csv.DictReader(open(CENSUS), delimiter="\t"))
    assert len(rows) == 1200
    fields = ["gid", "symbol", "s_id", "family", "title_short", "mech_key", "horizon",
              "census_verdict", "f0_verdict", "price_axis", "cost_axis", "pit_class",
              "mechanizable", "outcome_exposed_label", "known_negative_prior",
              "exploratory_status", "block_reason"]
    counts, sym_counts, fam_counts = collections.Counter(), collections.defaultdict(collections.Counter), collections.Counter()
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        for r in rows:
            gid, sym, verdict = r["gid"], r["symbol"], r["verdict"]
            pa, ca, pc = PRICE_AXIS[sym], COST_AXIS[sym], pit_class(r["required_pit_data"])
            mechanizable = "NO" if verdict == "NOT_FALSIFIABLE" else "YES"
            f0 = F0.get(gid, "n/a")
            # outcome-exposure LABEL (never an exclusion under directive #2)
            if gid in F0:
                label = "F0_INDIVIDUAL_REJECT"
            elif verdict == "VARIANT_OR_DUPLICATE" or (r["ancestry_hits"] and r["ancestry_hits"] != "none-found"):
                label = "FAMILY_HISTORY_NEGATIVE"
            else:
                label = "PRIOR_NOT_SCORED"
            known_neg = "YES" if label != "PRIOR_NOT_SCORED" else "NO"
            # implementability ladder (ancestry removed)
            if mechanizable == "NO":
                status, reason = "BLOCKED_NOT_MECHANIZABLE", "no mechanical decision rule / no falsifier (census NOT_FALSIFIABLE)"
            elif pa == "MISSING":
                status, reason = "BLOCKED_NO_PRICE_DATA", "symbol has no repo price panel; stays BLOCKED until owner data unlock (directive #3)"
            elif pa == "DAILY_REFERENCE_ONLY":
                status, reason = "BLOCKED_VENUE_UNEVIDENCED", "daily archive venue != executable; PIT lag unmeasured"
            elif verdict == "BLOCKED_COST":
                status, reason = "BLOCKED_COST_SWAP", "swap-profit-dependent economics; cost authority UNMEASURED until owner statement"
            elif pc in ("NEEDS_COT_PIT_UNEVIDENCED", "NEEDS_EIA_PHYSICAL_PIT_UNEVIDENCED", "NEEDS_MACRO_PIT_UNEVIDENCED"):
                status, reason = "BLOCKED_PIT_UNEVIDENCED", f"required PIT source unevidenced ({pc})"
            elif verdict == "BLOCKED_DATA":
                status, reason = "BLOCKED_DATA_FEATURE", "census BLOCKED_DATA: feature panel missing at declared ceiling"
            elif r["horizon"] == "INTRADAY" and pa == "H1_BAR_PANEL":
                status, reason = "BLOCKED_DATA_CEILING", "intraday features on H1-only pairs (USDCAD/AUDUSD M1 ceiling, sleeve PIT freeze R6)"
            else:
                status, reason = "EXPLORATORY_CANDIDATE", "rules+data+cost testable on evidenced panels; ancestry carried as label only (directive #2)"
            counts[status] += 1
            sym_counts[sym][status] += 1
            if status == "EXPLORATORY_CANDIDATE":
                fam_counts[r["family"]] += 1
            w.writerow({"gid": gid, "symbol": sym, "s_id": r["s_id"], "family": r["family"],
                        "title_short": r["title_short"], "mech_key": r["mech_key"],
                        "horizon": r["horizon"], "census_verdict": verdict, "f0_verdict": f0,
                        "price_axis": pa, "cost_axis": ca, "pit_class": pc,
                        "mechanizable": mechanizable, "outcome_exposed_label": label,
                        "known_negative_prior": known_neg, "exploratory_status": status,
                        "block_reason": reason})
    print("=== exploratory_status x count (1,200) — ladder v2 (owner directive 2026-09-29 #2) ===")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<32} {v}")
    print("\n=== EXPLORATORY_CANDIDATE per symbol ===")
    for s in ("EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF", "XAUUSD", "XAGUSD", "BRENT", "WTI", "NATGAS"):
        print(f"  {s:<8} {sym_counts[s]['EXPLORATORY_CANDIDATE']}")
    print("\n=== EXPLORATORY_CANDIDATE per family ===")
    for k, v in fam_counts.most_common():
        print(f"  {k:<14} {v}")
    print("\n=== outcome_exposed_label among candidates ===")
    lab = collections.Counter()
    for r in csv.DictReader(open(OUT), delimiter="\t"):
        if r["exploratory_status"] == "EXPLORATORY_CANDIDATE":
            lab[r["outcome_exposed_label"]] += 1
    print(dict(lab))
    json.dump(dict(counts), open(OUT.replace(".tsv", "_counts.json"), "w"), indent=1)
    print(f"\nwrote {OUT}")

if __name__ == "__main__":
    main()
