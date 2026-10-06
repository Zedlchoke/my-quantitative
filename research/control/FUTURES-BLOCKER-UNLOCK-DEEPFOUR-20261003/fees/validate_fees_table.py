import json, sys

BASE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/fees"
failures = []

# 1. JSON validity
with open(f"{BASE}/fees_table_all.json") as f:
    data = json.load(f)

# 2. Structural checks
required_keys = ["schema","cycle_id","task_id","lane","rows_flat","sources"]
for k in required_keys:
    if k not in data: failures.append(f"missing key {k}")

codes_expected = {"NQ","6E","6B","6J","6A","CL","NG","GC","SI"}
rows = data["rows_flat"]
codes_seen = {r["code"] for r in rows}
if codes_seen != codes_expected:
    failures.append(f"code set mismatch: {codes_seen ^ codes_expected}")

# 3. Label law: every row SOURCE=PUBLIC_REFERENCE, VERIFIED_VS_ACCOUNT=NOT_RUN
for r in rows:
    if r.get("SOURCE") != "PUBLIC_REFERENCE": failures.append(f"row {r['code']}/{r['component']}/{r.get('tier')}: SOURCE!=PUBLIC_REFERENCE")
    if r.get("VERIFIED_VS_ACCOUNT") != "NOT_RUN": failures.append(f"row {r['code']}/{r['component']}: VERIFIED_VS_ACCOUNT!=NOT_RUN")

# 4. Arithmetic recompute: ALL_IN = commission + exchange + regulatory per code/plan/tier
comp = {}
for r in rows:
    if r["component"] == "IBKR_COMMISSION":
        comp[(r["code"], r["plan"], r["tier"])] = r["value_usd"]
    elif r["component"] == "EXCHANGE_FEE_OFFSET":
        comp[(r["code"], "exchange")] = r["value_usd"]
    elif r["component"] == "REGULATORY_FEE_OFFSET_NFA":
        comp[(r["code"], "regulatory")] = r["value_usd"]

checked = 0
for r in rows:
    if r["component"] != "ALL_IN_COMPUTED": continue
    key = (r["code"], r["plan"], r["tier"])
    expr_terms = [t.strip() for t in r["expression"].split("+")]
    expr_sum = round(sum(float(t) for t in expr_terms), 6)
    c = comp.get(key)
    e = comp.get((r["code"], "exchange"))
    g = comp.get((r["code"], "regulatory"))
    if c is None or e is None or g is None:
        failures.append(f"{key}: missing component"); continue
    recomputed = round(c + e + g, 6)
    if abs(recomputed - r["value_usd"]) > 1e-9:
        failures.append(f"{key}: allin {r['value_usd']} != recomputed {recomputed}")
    if abs(expr_sum - recomputed) > 1e-9:
        failures.append(f"{key}: expression {expr_sum} != recomputed {recomputed}")
    checked += 1

# 5. Component spot-checks vs verbatim source values
spot = {
    ("NQ","exchange"):1.386, ("6E","exchange"):1.60, ("6B","exchange"):1.60,
    ("6J","exchange"):1.60, ("6A","exchange"):1.60,
    ("CL","exchange"):1.50, ("NG","exchange"):1.60, ("GC","exchange"):1.65, ("SI","exchange"):1.65,
    ("NQ","regulatory"):0.011, ("6E","regulatory"):0.011, ("6B","regulatory"):0.011,
    ("6J","regulatory"):0.011, ("6A","regulatory"):0.011,
    ("CL","regulatory"):0.02, ("NG","regulatory"):0.02, ("GC","regulatory"):0.01, ("SI","regulatory"):0.01,
}
for k,v in spot.items():
    got = comp.get(k)
    if got != v: failures.append(f"spot {k}: {got} != {v}")

# 6. Expected all-in summary grid
grid = {
 "NQ":[2.247,2.047,1.847,1.647], "6E":[2.461,2.261,2.061,1.861], "6B":[2.461,2.261,2.061,1.861],
 "6J":[2.461,2.261,2.061,1.861], "6A":[2.461,2.261,2.061,1.861],
 "CL":[2.37,2.17,1.97,1.77], "NG":[2.47,2.27,2.07,1.87], "GC":[2.51,2.31,2.11,1.91], "SI":[2.51,2.31,2.11,1.91]}
allin_rows = [r for r in rows if r["component"]=="ALL_IN_COMPUTED"]
for code, vals in grid.items():
    got = [r["value_usd"] for r in allin_rows if r["code"]==code and r["plan"]=="Tiered"]
    got_sorted = sorted(got, reverse=True)
    if got_sorted != vals: failures.append(f"grid {code}: {got_sorted} != {vals}")
    fixed = [r["value_usd"] for r in allin_rows if r["code"]==code and r["plan"]=="Fixed"]
    if fixed != [vals[0]]: failures.append(f"grid Fixed {code}: {fixed} != {[vals[0]]}")

# 7. fetch_log.jsonl: every line valid JSON with utc/url/tool/outcome
n_log = 0
with open(f"{BASE}/fetch_log.jsonl") as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line: continue
        n_log += 1
        try:
            rec = json.loads(line)
            for k in ("utc","url","tool","outcome"):
                if k not in rec: failures.append(f"fetch_log line {i}: missing {k}")
        except json.JSONDecodeError as ex:
            failures.append(f"fetch_log line {i}: invalid JSON ({ex})")

print(f"rows_flat: {len(rows)} (ALL_IN checked: {checked}); fetch_log lines: {n_log}")
if failures:
    print("FAIL:"); [print(" -", x) for x in failures]; sys.exit(1)
print("PASS: JSON valid, labels lawful, arithmetic recomputes, spot-checks match verbatim sources")
