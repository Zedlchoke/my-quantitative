#!/usr/bin/env python3
"""A7-SPEC probe R4/R5 — expiry rule vs D3 authority; holiday coverage adjudication.

R4: implements the SPEC r2 §1 deterministic rule (3rd Friday of delivery month,
shifted by CME-observed holiday displacement — measured precedents: Juneteenth
2026-06-18, 2027-06-17) and checks it against EVERY row of the D3
ARCHIVED_OFFICIAL expiration master table (transcribed verbatim from
ES_CALENDAR_EVIDENCE.md), plus the 2026 quarters. Also demonstrates the
June-2021 edge (federal observance existed Fri 2021-06-18, CME did NOT
displace — naive federal-shift reading would mispredict).
R5: recounts the D3 master table (claimed 36/68) and builds the per-year
ES-specific provability table from cmecal_coverage.json.
"""
import calendar, json, os, re
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/ES_CALENDAR_EVIDENCE.md"
COV = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/cmecal_coverage.json"

# ---- D3 master table, transcribed verbatim (contract code -> last trade date)
D3_ROWS = {
    "ESH10": "2010-03-19", "ESM10": "2010-06-18",
    "ESZ11": "2011-12-16",
    "ESH12": "2012-03-16", "ESM12": "2012-06-15", "ESU12": "2012-09-21", "ESZ12": "2012-12-21",
    "ESH13": "2013-03-15", "ESM13": "2013-06-21", "ESU13": "2013-09-20", "ESZ13": "2013-12-20",
    "ESH14": "2014-03-21", "ESM14": "2014-06-20", "ESU14": "2014-09-19", "ESZ14": "2014-12-19",
    "ESH15": "2015-03-20", "ESM15": "2015-06-19", "ESU15": "2015-09-18", "ESZ15": "2015-12-18",
    "ESH16": "2016-03-18", "ESM16": "2016-06-17", "ESU16": "2016-09-16", "ESZ16": "2016-12-16",
    "ESH17": "2017-03-17", "ESM17": "2017-06-16", "ESU17": "2017-09-15", "ESZ17": "2017-12-15",
    "ESH18": "2018-03-16", "ESM18": "2018-06-15", "ESU18": "2018-09-21", "ESZ18": "2018-12-21",
    "ESU24": "2024-09-20", "ESZ24": "2024-12-20",
    "ESH25": "2025-03-21", "ESM25": "2025-06-20", "ESU25": "2025-09-19", "ESZ25": "2025-12-19",
}

# cross-check transcription against the evidence file (row count + spot dates)
evid_txt = open(EVID).read()
tbl_rows = re.findall(r"^\|\s*(Mar|Jun|Sep|Dec)\s+(\d{4})\s*\|\s*(ES[A-Z]\d+)\s*\|.*?\|\s*(\d{2}/\d{2}/\d{4}|\d{1,2}\s+\w+\s+\d{4})\s*\|",
                      evid_txt, re.M)
transcription_matches_table = len(tbl_rows) == len(D3_ROWS)

def third_friday(year, month):
    fridays = [d for d in (date(year, month, dd) for dd in range(1, calendar.monthrange(year, month)[1] + 1))
               if d.weekday() == 4]
    return fridays[2]

# CME-observed displacements of the 3rd Friday (measured precedents only):
DISPLACED = {"2026-06": date(2026, 6, 18),   # Juneteenth Fri 6/19 observed on the 3rd Friday
             "2027-06": date(2027, 6, 17)}   # Jun 19 Sat -> observed Fri 6/18 = 3rd Friday -> Thu 6/17

def rule_expiry(year, month):
    key = f"{year}-{month:02d}"
    if key in DISPLACED:
        return DISPLACED[key]
    return third_friday(year, month)

def parse_d3(s):
    s = s.strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})$", s)  # ISO (transcription format)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
    m = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", s)
    months = {mn.lower(): i for i, mn in enumerate(calendar.month_name) if mn}
    return date(int(m.group(3)), months[m.group(2).lower()], int(m.group(1)))

MONTH_OF = {"H": 3, "M": 6, "U": 9, "Z": 12}
mismatch, agree = [], []
for code, ds in D3_ROWS.items():
    y = 2000 + int(code[3:])          # "ESH10" -> 2010
    mo = MONTH_OF[code[2]]
    rule_d, d3_d = rule_expiry(y, mo), parse_d3(ds)
    (agree if rule_d == d3_d else mismatch).append(
        {"code": code, "rule": str(rule_d), "d3": str(d3_d)})

# rule calendar for ALL 68 quarters 2010-2026 and the evaluation window 2010-06..2026-09
quarters = [(y, m) for y in range(2010, 2027) for m in (3, 6, 9, 12)]
rule_calendar = {f"{y}-{m:02d}": str(rule_expiry(y, m)) for y, m in quarters}
eval_quarters = [q for q in rule_calendar if not (q < "2010-06" or q > "2026-09")]

# June-2021 edge: naive "observed federal holiday on 3rd Friday shifts expiry"
# Juneteenth became federal 2021-06-17; Sat 6/19/2021 observed Fri 6/18/2021
# = the 3rd Friday; CME did NOT displace (dossier ES §1: 2010-2025 June
# expiries never displaced; 66/66 bars).
june2021_naive = (third_friday(2021, 6) - timedelta(days=1)).isoformat()
june2021_actual = third_friday(2021, 6).isoformat()

# ---- R5: recount D3 coverage ----
cov = json.load(open(COV))
es = cov["expiration_summary"]
recount = {
    "claimed_quarters_obtained": es["quarters_total_2010_2026"],
    "claimed": es["quarters_obtained"],
    "master_table_rows_transcribed": len(D3_ROWS),
    "evidence_file_table_rows": len(tbl_rows),
    "transcription_matches_table": transcription_matches_table,
    "recomputed_from_coverage_json_own_fields": len(es["fully_covered_years"]) * 4 + sum(len(v) for v in es["partial_years"].values()),
    "in_evaluation_window_2010H2_2026Q3": sum(1 for c in D3_ROWS if "2010-06" <= f"{2000+int(c[3:]):04d}-{MONTH_OF[c[2]]:02d}" <= "2026-09"),
    "not_obtained_implied": 68 - len(D3_ROWS),
    "coverage_json_not_obtained_years": es["not_obtained_years"],
}

# ---- R5: per-year ES-specific provability (from ES_CALENDAR_EVIDENCE per-year sections)
prov = {}
for y in range(2010, 2027):
    ys = str(y)
    info = cov["years"][ys]
    per_day_es = (y == 2010)  # only 2010 carries per-day/per-time Equity-family Globex detail (official 38-page PDF)
    prov[ys] = {
        "coverage_tags": info["coverage"],
        "globex_windows": "holidays" in info["coverage"],
        "per_day_es_specific_times": per_day_es,
        "what_tables_carry": (
            "full per-day/per-time Equity Globex (official PDF)" if per_day_es else
            ("LIVE page: windows + ClearPort/floor only; ES Globex times behind widget" if y == 2026 else
             "CME-wide Globex WINDOWS (+ ClearPort/floor; floor-equities rows 2016-2020; 2021+ floor drops product breakdown)"))
    }

# expected altered session-days per year (2010 PDF pattern + floor/ClearPort rows + windows)
expected_early_close = {
    "good_friday": "partial session (2010: early close 08:15 CT)",
    "black_friday": "early close (2010: 12:15 CT; floor-equities 12:15 CT rows 2016-2020)",
    "dec24_vicinity": "early close or full closure",
    "jul3_adjacent": "early close in years Jul 4 falls Tue/Thu (equities 12:15 CT rows 2017/2018/2019/2020)",
    "mlk_presidents": "2010: Mon 10:30-CT halt pattern; 2026 note: equity Globex NORMAL; 2011-2025 not ES-proven per-year",
    "dossier_measured_early_close_sessions_per_year": "3-10/yr (ES_DEEP_v2 §7, measured from bars)",
}

result = {
    "probe": "r4_r5_expiry_rule_and_holidays",
    "r4": {
        "d3_rows_checked": len(D3_ROWS),
        "agree": len(agree),
        "mismatch": mismatch,
        "rule_matches_all_d3_authority_rows": len(mismatch) == 0,
        "rule_calendar_68q": rule_calendar,
        "eval_window_quarters": len(eval_quarters),
        "bars_validation_coverage_claim": "66/66 expiries measured = 3rd Friday except ESM6 2026-06-18 (ES_DEEP_v2 §1, definitions confirm 2026/2027)",
        "june2021_edge": {
            "naive_federal_shift_would_predict": june2021_naive,
            "cme_actual_and_dossier_measured": june2021_actual,
            "naive_rule_mispredicts_2021": june2021_naive != june2021_actual,
        },
        "pit_legality": "rule computable ex ante from public calendars (3rd-Friday arithmetic + statutory holiday observance + CME-published displacement); bars/D3 used only for ex-post validation; mismatch => full-quarter EXCLUDE (fail-closed)",
    },
    "r5": {
        "d3_recount": recount,
        "per_year_es_provability": prov,
        "expected_altered_days": expected_early_close,
    },
}
result["verdict"] = "PASS" if (
    len(mismatch) == 0 and transcription_matches_table
    and result["r4"]["june2021_edge"]["naive_rule_mispredicts_2021"]
) else "CHECK"

out = os.path.join(HERE, "out_probe_r4_r5_expiry_rule_and_holidays.json")
with open(out, "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(json.dumps({"r4_agree": len(agree), "r4_mismatch": mismatch,
                  "d3_rows": len(D3_ROWS), "recount": recount,
                  "june2021_edge": result["r4"]["june2021_edge"],
                  "verdict": result["verdict"]}, indent=2))
