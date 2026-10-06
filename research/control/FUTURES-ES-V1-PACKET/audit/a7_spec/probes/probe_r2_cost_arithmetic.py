#!/usr/bin/env python3
"""A7-SPEC probe R2/R3 — cost arithmetic + source binding for SPEC_PB1_ES r2 §5.

Recomputes all-in per side from the SPEC §5 component table and binds each
component to the D2 artifact (analysis/d2_feesrc/fees_table_es.json):
  commission 0.85  -> C5 Fixed (S1, LIVE_OFFICIAL 2026-10-03)
  exchange 1.386   -> X1 (S2 IBKR CME.php offset table)
  NFA 0.02 default -> X2n timeline (S5 NFA CFTC filing, LIVE_OFFICIAL)
  NFA 0.01 window 2014-10-01..2017-12-31 (inclusive) -> X2n
  spread 6.25      -> half of D5-reproduced 1.0-tick ($12.50) full-spread proxy
  slippage 12.50/25.00/37.50 -> D1 declared assumption (1/2/3 ticks x $12.50)
Asserts the IBKR regulatory offset 0.011 (X2) is NOT a term in the SPEC sum
(no double count), and that no bias-direction wording for historical fees
remains in SPEC/PLAN (R3).
"""
import json, os, re, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
D2 = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d2_feesrc/fees_table_es.json"
SPEC = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md"
PLAN = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-ES-V1-PACKET/PLAN_futures_es_v1.md"

d2 = json.load(open(D2))
comp = {r["row_id"]: r for r in d2["components_es_per_contract_per_side_usd"]}
plans = {r["row_id"]: r for r in d2["commission_plans_ibkr_es"]}

# --- source binding ---------------------------------------------------------
x1 = comp["X1"]["value_usd"]                      # exchange 1.386
x2_ibkr_offset = comp["X2"]["value_usd"]          # 0.011 (IBKR offset; must NOT be added)
x2n = {p["period"]: p["value"] for p in comp["X2n"]["values_usd_per_side"]}
c5_fixed = plans["C5"]["ibkr_execution_fee_usd_per_contract_per_side"]  # 0.85
tiered = [plans[f"C{i}"]["ibkr_execution_fee_usd_per_contract_per_side"] for i in (1, 2, 3, 4)]

binding = {
    "commission_0.85_source": "C5 Fixed PUBLIC_REFERENCE S1 (max of published tiers)" if c5_fixed == 0.85 and max(tiered + [c5_fixed]) == 0.85 else f"MISMATCH {c5_fixed}",
    "exchange_1.386_source": "X1 S2 IBKR CME.php offset" if x1 == 1.386 else f"MISMATCH {x1}",
    "nfa_default_0.02_source": "X2n pre-2014 & 2018+ (S5)" if x2n["2010-01-01..2014-09-30 (and prior to 2014-10-01)"] == 0.02 and x2n["2018-01-01..(open-ended; last official doc fetched)"] == 0.02 else "MISMATCH",
    "nfa_0.01_window_source": "X2n 2014-10-01..2017-12-31 (S5)" if x2n["2014-10-01..2017-12-31"] == 0.01 else "MISMATCH",
    "ibkr_regulatory_offset_0.011_value": x2_ibkr_offset,
    "cme_tariff_per_cell_extracted_in_d2": comp["X1o"]["value_usd"] is not None,  # False expected (NOT extractable -> R3 support)
    "d2_historical_ibkr_content_fetched": False,  # d2 limitation 5: snapshots 2022/23/25 exist, content NOT retrieved
}

# --- arithmetic -------------------------------------------------------------
COMM, EXCH, NFA_D, NFA_01, SPREAD = 0.85, 1.386, 0.02, 0.01, 6.25
SLIP = {"S1": 12.50, "S2": 25.00, "S3": 37.50}
base = round(COMM + EXCH + NFA_D + SPREAD, 6)
allin_default = {k: round(base + v, 6) for k, v in SLIP.items()}
allin_nfa001 = {k: round(base + v - 0.01, 6) for k, v in SLIP.items()}
spec_expect = {"S1": 21.006, "S2": 33.506, "S3": 46.006}
arith = {
    "base_components_sum": base,
    "sum_default_nfa_0.02": allin_default,
    "sum_window_2014_10_01_to_2017_12_31_nfa_0.01": allin_nfa001,
    "matches_spec_table": allin_default == spec_expect,
    "window_delta_minus_0.01": {k: round(allin_default[k] - allin_nfa001[k], 6) for k in SLIP},
    "terms_of_sum": {"commission": COMM, "exchange": EXCH, "nfa_default": NFA_D,
                     "spread_half": SPREAD, "slippage": SLIP},
}

# --- no double count: 0.011 must not appear as an additive term -------------
spec_txt = open(SPEC).read()
mentions_0011 = [ln.strip() for ln in spec_txt.splitlines() if "0.011" in ln]
sanctioned = len(mentions_0011) > 0 and all(("KHÔNG" in ln or "not" in ln.lower()) for ln in mentions_0011)
offset_value_not_a_term = x2_ibkr_offset not in (COMM, EXCH, NFA_D, NFA_01, SPREAD) and x2_ibkr_offset not in SLIP.values()
recomputed_matches = allin_default == spec_expect

# --- R3: no residual bias-direction claim for historical fees ---------------
def strip_diacritics(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

candidates = []
for doc_name, txt in (("SPEC", spec_txt), ("PLAN", open(PLAN).read())):
    t = strip_diacritics(txt).lower()
    for kw in ["thien cao", "thien thap", "overstat", "understat", "biases", "che tau",
               "giam chi phi", "higher-than-actual", "lower-than-actual", "conservative direction",
               "overstate", "understate"]:
        for m in re.finditer(re.escape(kw), t):
            candidates.append({"doc": doc_name, "kw": kw,
                               "ctx": t[max(0, m.start() - 110):m.end() + 110]})
# permitted contexts: spread-proxy statements (about spread, not fees) and the
# conservative-row-choice justification (about which public row is picked, not a
# historical-vs-current direction claim)
residual = [c for c in candidates
            if not any(p in c["ctx"] for p in ["spread", "proxy", "bao thu nhat", "tiered thap hon chi giam", "most conservative"])]

result = {
    "probe": "r2_cost_arithmetic",
    "binding": binding,
    "arithmetic": arith,
    "no_double_count": {
        "lines_mentioning_0.011": mentions_0011,
        "all_mentions_are_explicit_not_used": sanctioned,
        "offset_0.011_absent_from_terms": offset_value_not_a_term,
        "recomputed_matches_spec": recomputed_matches,
    },
    "r3_bias_direction": {
        "candidates_reviewed": len(candidates),
        "candidate_keywords": sorted({c["kw"] for c in candidates}),
        "permitted_contexts_retained": [c for c in candidates if c not in residual],
        "residual_fee_bias_direction_claims": residual,
        "clean": len(residual) == 0,
        "d2_support": {
            "cme_pdf_cells_not_extractable": not binding["cme_tariff_per_cell_extracted_in_d2"],
            "per_year_ibkr_fee_values_extractable": binding["d2_historical_ibkr_content_fetched"],
            "nfa_only_official_timeline": True,
        },
    },
}
result["verdict"] = "PASS" if (
    arith["matches_spec_table"] and sanctioned and offset_value_not_a_term
    and recomputed_matches and result["r3_bias_direction"]["clean"]
    and "MISMATCH" not in json.dumps(binding)
    and not result["r3_bias_direction"]["d2_support"]["per_year_ibkr_fee_values_extractable"]
    and result["r3_bias_direction"]["d2_support"]["cme_pdf_cells_not_extractable"]
) else "FAIL"

out = os.path.join(HERE, "out_probe_r2_cost_arithmetic.json")
with open(out, "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(json.dumps({k: result[k] for k in ("probe", "binding", "arithmetic", "no_double_count", "verdict")}, indent=2, ensure_ascii=False))
print("R3 residual:", json.dumps(result["r3_bias_direction"]["residual_fee_bias_direction_claims"], ensure_ascii=False))
print("R3 permitted:", json.dumps(result["r3_bias_direction"]["permitted_contexts_retained"], ensure_ascii=False)[:600])
