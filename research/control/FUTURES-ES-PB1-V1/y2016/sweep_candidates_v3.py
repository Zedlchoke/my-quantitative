#!/usr/bin/env python
# Y2016-AUDIT (FUTURES-ES-PB1-V1) — corpus-wide unproven-candidate sweep + v3 exclusion build.
# Zero network; committed artifacts only; no panel parquet read (universe JSON carries bars).
# Writes ONLY inside research/control/FUTURES-ES-PB1-V1/y2016/**.
import json, hashlib, os
from datetime import date, timedelta

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
REL = {
    "universe":   "research/control/FUTURES-K6GATE-PREP-20261004/es/session_dispersion_es.json",
    "v2":         "research/control/FUTURES-ES-PB1-V1/repair/exclude_list_v2.json",
    "pdf1115":    "research/control/FUTURES-ES-PB1-V1/holiday/pdf_equity_evidence_2011_2015.json",
    "readiness":  "research/control/FUTURES-SIX-READINESS-20261004/es/es_session_holiday.json",
    "cmecal":     "research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/cmecal_coverage.json",
    "pdf2010":    "research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/comm/globex_2010_holiday.pdf",
    "es_calev":   "research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/ES_CALENDAR_EVIDENCE.md",
    "nq_calev":   "research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/nq_es/NQ_CALENDAR_EVIDENCE.md",
}
def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
shas = {k: sha256(os.path.join(WT, v)) for k, v in REL.items()}

uni = json.load(open(os.path.join(WT, REL["universe"])))
v2 = json.load(open(os.path.join(WT, REL["v2"])))
pdf = json.load(open(os.path.join(WT, REL["pdf1115"])))

sessions = {r["session_date"]: r for r in uni["sessions"]}
v2_by_date = {}
for e in v2["exclusions"]:
    v2_by_date.setdefault(e["session_date"], []).append(e)

# ---------------- candidate family rules (pattern-derived CANDIDACY, not adjudication) ----
def nth_weekday(y, m, weekday, n):
    d = date(y, m, 1)
    c = 0
    while True:
        if d.weekday() == weekday:
            c += 1
            if c == n:
                return d
        d += timedelta(days=1)

def last_weekday(y, m, weekday):
    d = date(y, m + 1, 1) - timedelta(days=1) if m < 12 else date(y, 12, 31)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d

def easter(y):
    a = y % 19; b = y // 100; c = y % 100; dd = b // 4; e = b % 4
    f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - dd - g + 15) % 30
    i = c // 4; k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mo = (h + l - 7 * m + 114) // 31
    da = ((h + l - 7 * m + 114) % 31) + 1
    return date(y, mo, da)

def prev_weekday(d):
    p = d - timedelta(days=1)
    while p.weekday() > 4:
        p -= timedelta(days=1)
    return p

def candidates_for_year(y):
    """Return {iso_date: (family, config, basis_tag)}. Weekday positions only."""
    out = {}
    def add(d, fam, cfg, tag):
        if d.weekday() <= 4:
            out[d.isoformat()] = (fam, cfg, tag)
    # NEW YEAR
    j1 = date(y, 1, 1)
    if j1.weekday() <= 4:
        add(j1, "NEWYEAR", "jan1_weekday", "2011-15 pattern: weekday Jan 1 CLOSED (2013/2014/2015)")
    elif j1.weekday() == 6:
        add(date(y, 1, 2), "NEWYEAR", "jan2_observed_mon", "observed closure when Jan1=Sun (2012-01-02 corpus; 2016 page names Jan 2 2017)")
    if date(y - 1, 12, 31).weekday() == 4 and j1.weekday() == 5:
        add(date(y - 1, 12, 31), "NEWYEAR", "dec31_fri_before_sat", "corpus day-level PDF proof exists ONLY for 2010-12-31 (REGULAR); any other year UNPROVEN")
    # MLK / PRESIDENTS / MEMORIAL / LABOR (Monday families; adjacent Fridays 5/5 PDF-regular -> NOT candidates)
    add(nth_weekday(y, 1, 0, 3), "MLK", "3rd_mon_jan", "HALT family every corpus year")
    add(nth_weekday(y, 2, 0, 3), "PRES", "3rd_mon_feb", "HALT family every corpus year")
    add(last_weekday(y, 5, 0), "MEM", "last_mon_may", "HALT family every corpus year")
    add(nth_weekday(y, 9, 0, 1), "LABOR", "1st_mon_sep", "HALT family every corpus year")
    # GOOD FRIDAY
    add(easter(y) - timedelta(days=2), "GOODFRI", "easter_minus_2", "CLOSED 3/5 corpus years, EC-0815 2/5 (2012/2015)")
    # JULY 4 family: main day (or observed) + immediately preceding weekday
    j4 = date(y, 7, 4)
    if j4.weekday() <= 4:
        add(j4, "JUL4", "jul4_main", "HALT/EC in every weekday corpus year (2011/2012/2013/2014)")
        add(prev_weekday(j4), "JUL4", "day_before_main",
            "EC-1215 proven when Jul4=Tue/Wed/Thu (2012/2013/2014); owner directive extends candidacy to Sun/Mon configs (2015 Sat config had Thu+Fri EC)")
    elif j4.weekday() == 6:
        add(date(y, 7, 5), "JUL4", "jul5_observed_mon", "observed when Jul4=Sun (2010 corpus HALT; 2021)")
        add(prev_weekday(date(y, 7, 5)), "JUL4", "day_before_observed",
            "owner directive: day-before-July-4 in Sun/Mon configs is candidate; 2010 analog PDF-REGULAR proves 2010 only")
    else:  # Saturday
        add(date(y, 7, 3), "JUL4", "jul3_observed_fri", "observed when Jul4=Sat (2020 corpus; 2015 EC-1200)")
        add(date(y, 7, 2), "JUL4", "day_before_observed_sat",
            "2015 Sat config: Thu Jul 2 EC-1215 + Fri Jul 3 EC-1200; 2020 note names NO equities EC Jul 2 -> ambiguous -> candidate")
    # THANKSGIVING family: 4th Thu + following Friday (Wed-before 5/5 PDF-regular -> NOT candidate)
    t4 = nth_weekday(y, 11, 3, 4)
    add(t4, "THANKS", "4th_thu_nov", "HALT family every corpus year")
    add(t4 + timedelta(days=1), "THANKS", "black_friday", "EC-1215 every corpus year 2011-2015")
    # CHRISTMAS family: main (or observed) + Dec 24 when weekday (Dec 23: 1/1 analog PDF-regular + 2016 floor omits equities -> NOT candidate)
    x = date(y, 12, 25)
    if x.weekday() <= 4:
        add(x, "XMAS", "dec25_main", "CLOSED every corpus year")
    elif x.weekday() == 6:
        add(date(y, 12, 26), "XMAS", "dec26_observed_mon", "observed when Dec25=Sun (2011 corpus CLOSED; 2016 page names Dec 26 2016)")
    else:  # Saturday
        add(date(y, 12, 24), "XMAS", "dec24_observed_fri", "observed when Dec25=Sat (2010 corpus: Globex CLOSED; 2021 readiness legality date)")
    d24 = date(y, 12, 24)
    if d24.weekday() <= 4:
        add(d24, "XMAS", "dec24_weekday", "EC-1215 proven 2012/2013/2014/2015 when weekday")
    # JUNETEENTH (2022+, first CME displacement; 2021-06 NOT a displacement per readiness ERRATUM)
    if y >= 2022:
        j = date(y, 6, 19)
        if j.weekday() <= 4:
            add(j, "JUNETEENTH", "jun19_weekday", "CME displacement 2022+")
        else:
            add(j + timedelta(days=(7 - j.weekday()) % 7 or 1), "JUNETEENTH", "jun20_observed_mon", "observed when Jun19=weekend (2022 corpus)")
    return out

# ---------------- day-level proof registers --------------------------------------------
PDF1115_CAND = pdf["candidate_dates_closed_halt_early"]
PDF1115_REG = pdf["regular_adjudicated_dates"]
# 2010 official PDF, equity sections, page-cited (this lane's direct pypdf extraction of committed bytes)
PDF2010 = {
    "2010-01-01": ("CLOSED", "globex_2010_holiday.pdf p1 'Friday, Jan 1 CME Globex is closed'"),
    "2010-07-02": ("REGULAR", "globex_2010_holiday.pdf p18 'Friday, Jul 2 1515 CT - Regular CME Globex close for trade date Friday, July 2' (equity section)"),
    "2010-07-05": ("HALT", "globex_2010_holiday.pdf p18 'Monday, Jul 5 1030 CT - Trading halt ... 1700 CT resume' (equity section)"),
    "2010-09-03": ("REGULAR", "globex_2010_holiday.pdf p21 'Friday, Sep 3 1515 CT - Regular CME Globex close' (equity section)"),
    "2010-09-06": ("HALT", "globex_2010_holiday.pdf p21 'Monday, Sep 6 1030 CT - Trading halt' (equity section)"),
    "2010-11-24": ("REGULAR", "globex_2010_holiday.pdf p29 'Wednesday, Nov 24 1515 CT - Regular CME Globex close' (equity section)"),
    "2010-11-25": ("HALT", "globex_2010_holiday.pdf p29 'Thursday, Nov 25 1030 CT - CME Globex trading halt' (equity section)"),
    "2010-11-26": ("EARLY_CLOSE", "globex_2010_holiday.pdf p29 'Friday, Nov 26 1215 CT - Early CME Globex close for trade date Friday, Nov 26' (equity section)"),
    "2010-12-23": ("REGULAR", "globex_2010_holiday.pdf p33 'Thursday, Dec 23 1515 CT - Regular CME Globex close' (equity section)"),
    "2010-12-24": ("CLOSED", "globex_2010_holiday.pdf p33 'Friday, Dec 24 CME Globex is closed' (equity section)"),
    "2010-12-31": ("REGULAR", "globex_2010_holiday.pdf p36 'Friday, Dec 31 1515 CT - Regular CME Globex close' (equity section); corroborated by 2011-new-years.pdf"),
}
# 2016 committed evidence (transcriptions of archived 2016 calendar page; NONE is Globex-equity day-level session-hours)
E2016 = {
    "2016-03-25": ("CLOSED_NAMED", "cmecal_coverage.json year-2016 note 'closures Good Friday Mar 25' (tier primary)"),
    "2016-11-25": ("FLOOR_EQUITY_EC", "cmecal_coverage.json year-2016 note 'Equities floor close 12:15 CT Nov 25; ClearPort early close 13:45 ET Nov 25 (Globex equity times NOT transcribed)'"),
    "2016-12-26": ("CLOSED_NAMED", "cmecal_coverage.json year-2016 note 'closures ... Dec 26' (tier primary)"),
    "2017-01-02": ("CLOSED_NAMED", "cmecal/ES_CALENDAR_EVIDENCE 2016: 'New Year's Mon Jan 2 2017 closed'"),
}
# readiness floor-named equity early closes 2017-2020 (Globex NOT transcribed) + legality lists
READINESS_FLOOR_EQ = {
    "2017-07-03": "2017 floor: Jul 3 EQUITIES 12:15 CT",
    "2017-11-24": "2017 floor: Nov 24 EQUITIES 12:15 CT",
    "2018-07-03": "2018 floor: Jul 3 EQUITIES 12:15 CT",
    "2018-11-23": "2018 floor: Nov 23 EQUITIES 12:15 CT",
    "2018-12-24": "2018 floor: Dec 24 EQUITIES 12:15 CT",
    "2019-11-29": "2019 floor: Nov 29 EQUITIES 12:15 CT",
    "2019-12-24": "2019 floor: Dec 24 EQUITIES 12:15 CT",
    "2020-11-27": "2020 floor: Nov 27 EQUITIES 12:15 CT",
    "2020-12-24": "2020 floor: Dec 24 EQUITIES 12:15 CT",
}
# 2026 product-level FACT cells (cal_close lane, ES id=133 events, sha-pinned captures) —
# the ONLY product-level day-level Globex evidence in the corpus, 2026-only.
FACT2026_REGULAR = {
    "2026-07-02": "calendar_close_delta.json cells_obtained 'ES_2026_holiday_deviation_FACT_upgrade x3 windows (July-4 2026-07-02)': evd_2026-07-02 = [16:00 closed, 16:45 preopen, 17:00 open] = NORMAL daily template (vs evd_2026-07-03 = [12:00 closed] = the early-close deviation); capture svc_20260702_20260129012310.json, ES id=133, cross-round sha EXACT",
}

FOLDS = [("F1", "2010-06-01", "2012-12-31"), ("F2", "2013-01-01", "2017-12-31"),
         ("F3", "2018-01-01", "2021-12-31"), ("F4", "2022-01-01", "2026-09-30")]
def fold_of(d):
    for f, a, b in FOLDS:
        if a <= d <= b:
            return f
    return None

all_dates = sorted(sessions.keys())
def warmup_set(fold):
    f, a, b = next(x for x in FOLDS if x[0] == fold)
    ds = [d for d in all_dates if a <= d <= b]
    return set(ds[:252]), ds
warmups = {}
fold_sessions = {}
for f, a, b in FOLDS:
    ds = [d for d in all_dates if a <= d <= b]
    fold_sessions[f] = ds
    warmups[f] = set(ds[:252])

# ---------------- sweep ----------------------------------------------------------------
rows = []
for y in range(2010, 2027):
    for iso, (fam, cfg, basis) in sorted(candidates_for_year(y).items()):
        s = sessions.get(iso)
        v2e = v2_by_date.get(iso, [])
        v2_classes = sorted({e["reason_class"] for e in v2e if e["in_panel"]})
        in_panel = s is not None
        bars = s["bars_rth_core_held"] if s else None
        cov = s["rth_core_coverage"] if s else None
        # proof tier
        if iso in FACT2026_REGULAR:
            proof = "PROVEN_REGULAR_FACT2026"
        elif iso in PDF1115_CAND:
            proof = "PROVEN_TRUNCATED_CLOSED_PDF1115"
        elif iso in PDF2010 and PDF2010[iso][0] in ("CLOSED", "HALT", "EARLY_CLOSE"):
            proof = "PROVEN_TRUNCATED_CLOSED_PDF2010"
        elif iso in PDF1115_REG:
            proof = "PROVEN_REGULAR_PDF1115"
        elif iso in PDF2010 and PDF2010[iso][0] == "REGULAR":
            proof = "PROVEN_REGULAR_PDF2010"
        else:
            proof = "UNPROVEN"
        # WARMUP-closed unproven candidates (e.g. 2022-07-01): exposure already closed, no new entry
        in_warmup_any = any(iso in warmups[f] for f in warmups)
        if in_panel and proof == "UNPROVEN" and in_warmup_any and not y == 2016:
            action = "UNPROVEN_CLOSED_BY_WARMUP"
        elif in_panel and y == 2016:
            action = "V3_EXCLUDE_2016_UNPROVEN" if proof != "PROVEN_REGULAR_PDF1115" else "KEEP_PROVEN"
        elif in_panel and proof == "UNPROVEN":
            action = "V3_NEW_EXCLUDE_UNPROVEN" if not v2_classes else "ALREADY_EXCLUDED"
        elif in_panel and proof.startswith("PROVEN_TRUNCATED"):
            action = "ALREADY_EXCLUDED" if v2_classes else "V3_NEW_EXCLUDE_PROVEN_TRUNCATED_NOT_EXCLUDED"
        else:
            action = "KEEP_PROVEN_REGULAR" if proof.startswith("PROVEN_REGULAR") else "ABSENT_FROM_PANEL"
        rows.append({
            "date": iso, "year": y, "family": fam, "config": cfg, "basis": basis,
            "in_panel": in_panel, "bars_rth_core": bars, "coverage": cov,
            "fold": fold_of(iso), "in_warmup": any(iso in warmups[f] for f in warmups),
            "v2_classes": v2_classes, "proof": proof,
            "pdf2010_note": PDF2010.get(iso, (None, None))[1],
            "e2016_note": E2016.get(iso, (None, None))[1],
            "readiness_floor_note": READINESS_FLOOR_EQ.get(iso),
            "fact2026_note": FACT2026_REGULAR.get(iso),
            "action": action,
        })

# ---------------- v3 eval re-measure ----------------------------------------------------
new_cls = "HOLIDAY_2016_UNPROVEN_FAILCLOSED"
v3_added = {}
for r in rows:
    if r["action"] in ("V3_EXCLUDE_2016_UNPROVEN", "V3_NEW_EXCLUDE_UNPROVEN",
                       "V3_NEW_EXCLUDE_PROVEN_TRUNCATED_NOT_EXCLUDED"):
        v3_added[r["date"]] = r

def eval_n(v2_only_extra=None):
    per = {}
    for f, a, b in FOLDS:
        ds = fold_sessions[f]
        w = set(ds[:252])
        excl = set()
        for d in ds:
            cls = {e["reason_class"] for e in v2_by_date.get(d, []) if e["in_panel"]}
            if v2_only_extra and d in v2_only_extra:
                cls = cls | {new_cls}
            if cls:
                excl.add(d)
        ev = [d for d in ds if d not in w and d not in excl]
        per[f] = {"sessions": len(ds), "excluded_nonwarmup": len([d for d in ds if d not in w and d in excl]),
                  "warmup": len(w), "eval_n": len(ev),
                  "eval_first": ev[0] if ev else None, "eval_last": ev[-1] if ev else None}
    return per

old_eval = eval_n(v2_only_extra=None)
new_eval = eval_n(v2_only_extra=set(v3_added.keys()))
# eval membership deltas
def eval_set(per):
    out = {}
    for f, a, b in FOLDS:
        ds = fold_sessions[f]
        w = set(ds[:252])
        out[f] = set()
    return out
old_sets, new_sets = {}, {}
for f, a, b in FOLDS:
    ds = fold_sessions[f]
    w = set(ds[:252])
    ex_o = {d for d in ds if any(e["in_panel"] for e in v2_by_date.get(d, []))}
    ex_n = ex_o | set(v3_added.keys())
    old_sets[f] = {d for d in ds if d not in w and d not in ex_o}
    new_sets[f] = {d for d in ds if d not in w and d not in ex_n}
removed_from_eval = {f: sorted(old_sets[f] - new_sets[f]) for f in old_sets}

result = {
    "schema": "y2016_audit_sweep@1",
    "cycle_id": "FUTURES-ES-PB1-V1",
    "lane": "Y2016-AUDIT",
    "input_shas": shas,
    "input_paths": REL,
    "candidate_rule_basis": "pattern-derived CANDIDACY from 56 committed 2011-15 PDF candidate dates + 2010 official PDF + owner directive (day-before-July-4 Sun/Mon configs); candidacy != adjudication",
    "n_candidates_2010_2026": len(rows),
    "rows": rows,
    "v3_added_dates": sorted(v3_added.keys()),
    "v3_added_detail": {d: {k: v for k, v in v3_added[d].items() if k in
                            ("family", "config", "basis", "bars_rth_core", "coverage", "fold", "in_warmup",
                             "v2_classes", "proof", "pdf2010_note", "e2016_note", "readiness_floor_note", "action")}
                        for d in sorted(v3_added)},
    "eval_old": old_eval,
    "eval_new": new_eval,
    "removed_from_eval": removed_from_eval,
}
outp = os.path.join(WT, "research/control/FUTURES-ES-PB1-V1/y2016/sweep_candidates_v3.json")
with open(outp, "w") as f:
    json.dump(result, f, indent=1, sort_keys=False)

print("== v2 eval reproduction (must equal 375/949/711/890):")
for f in old_eval:
    print(" ", f, old_eval[f])
print("== v3 eval:")
for f in new_eval:
    print(" ", f, new_eval[f])
print("== v3 added exclusions (%d):" % len(v3_added))
for d in sorted(v3_added):
    r = v3_added[d]
    print("  ", d, r["family"], r["config"], "| bars:", r["bars_rth_core"], "| v2:", r["v2_classes"], "|", r["action"], "| fold:", r["fold"], "| warmup:", r["in_warmup"])
print("== non-2016 unproven candidates already excluded (sample check) + absents:")
for r in rows:
    if r["action"] in ("ABSENT_FROM_PANEL", "ALREADY_EXCLUDED") and r["year"] != 2016:
        print("  ", r["date"], r["family"], r["config"], r["action"], "proof:", r["proof"], "v2:", r["v2_classes"])
