#!/usr/bin/env python
"""FUTURES-ES-PB1-V1 / lane HOLIDAY-CLOSURE — M2 day-level evidence extraction.

Extracts the "CME Group Equity Products" sections and their dated statements
from the 53 committed per-holiday official CME Globex schedule PDFs
(2011-2015) in the fx_comm calendar corpus. Zero network: reads committed
bytes only. Output feeds exposure_proof.py (candidate + adjudicated-regular
date sets for the 2011-2016 exposure proof).

Run:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python \
    research/control/FUTURES-ES-PB1-V1/holiday/extract_equity_pdf_evidence.py

Output (write boundary: this directory only):
  pdf_equity_evidence_2011_2015.json
"""
import hashlib
import json
import os
import re
from datetime import date

from pypdf import PdfReader

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
PDF_DIR = ("research/control/FUTURES-OVERNIGHT-PREP-20261003/"
           "cme_cal_gap/fx_comm/captures")
COVERAGE_JSON = ("research/control/FUTURES-OVERNIGHT-PREP-20261003/"
                 "cme_cal_gap/fx_comm/fxcomm_gapfill_coverage.json")
OUT_REL = "research/control/FUTURES-ES-PB1-V1/holiday/pdf_equity_evidence_2011_2015.json"

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"])}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday"]

# A date-line is a line that is (essentially) only the date. Mid-sentence
# date mentions (e.g. "Regular open for trade date Friday, Nov 29*" inside a
# Wednesday block) are NOT date-lines.
DATE_LINE = re.compile(
    r"^\s*(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*,?\s+"
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})\s*:?\s*$",
    re.I | re.M)
SECTION_HEADER = re.compile(
    r"(Equity Products|Interest Rate Products|Interest Products|FX Products|"
    r"NYMEX|COMEX|Other CME Group Products|KOSPI|Bursa Malaysia|"
    r"Green Exchange|DME Products|Agricultural)", re.I)
TIME_CT = re.compile(r"(\d{3,4})\s*(?:CT|ct)\b")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_block(block):
    b = block.lower()
    if "globex is closed" in b or "globex closed" in b:
        return "CLOSED"
    if "trading halt" in b or "globex trading halt" in b:
        return "HALT"
    if "early cme globex close" in b or "early close" in b:
        return "EARLY_CLOSE"
    if "regular cme globex open" in b or "regular open" in b:
        return "REGULAR_OPEN"
    if "regular cme globex close" in b or "regular close" in b:
        return "REGULAR_CLOSE"
    if "normal schedule" in b or "unaffected" in b:
        return "NORMAL_SCHEDULE"
    if b.strip():
        return "OTHER"
    return "NO_STATEMENT"


def first_time_ct(block):
    times = [int(t) for t in TIME_CT.findall(block)]
    if not times:
        return None
    # keep plausible clock tokens (100..1800)
    times = [t for t in times if 100 <= t <= 1859]
    return min(times) if times else None


def resolve_year(pdf_year, month, filename):
    # New-year transition PDFs: named for the January holiday year N;
    # December statements belong to N-1, Jan..Jun statements to N.
    if "new-year" in filename:
        return pdf_year - 1 if month == 12 else pdf_year
    return pdf_year


def equity_section(text):
    """Return the text of the first '... Equity Products' section, or None."""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if re.search(r"Equity Products", ln, re.I) and len(ln.strip()) < 60:
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        ln = lines[j].strip()
        if not ln or len(ln) > 90:
            continue  # page footers / wrapped lines
        if SECTION_HEADER.search(ln) and not re.search(r"equity", ln, re.I):
            end = j
            break
    return "\n".join(lines[start:end])


def main():
    cov = json.load(open(os.path.join(WORKTREE, COVERAGE_JSON), encoding="utf-8"))
    gap4 = cov["gap4_energy_metals_holiday_times_2011_2015"]["cells"]
    # file -> (year, holiday, cell meta)
    file_meta = {}
    for yr, cells in gap4.items():
        for hol, cell in cells.items():
            if isinstance(cell, dict) and "file" in cell:
                file_meta[cell["file"]] = {
                    "pdf_year": int(yr), "holiday_key": hol,
                    "gap4_status": cell.get("status"),
                    "capture_ts": cell.get("capture_ts"),
                    "url": cell.get("url")}

    files = sorted(f for f in os.listdir(os.path.join(WORKTREE, PDF_DIR))
                   if f.startswith(("2011", "2012", "2013", "2014", "2015"))
                   and f.endswith(".pdf"))
    assert len(files) == 53, f"expected 53 committed 2011-2015 PDFs, got {len(files)}"

    out_files, rollup, anomalies = [], {}, []
    for fn in files:
        rel = f"{PDF_DIR}/{fn}"
        path = os.path.join(WORKTREE, rel)
        sha = sha256_file(path)
        meta = file_meta.get(fn, {})
        reader = PdfReader(path)
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        sec = equity_section(text)
        rec = {
            "file": fn, "path": rel, "sha256": sha,
            "pdf_year": meta.get("pdf_year"), "holiday_key": meta.get("holiday_key"),
            "gap4_status": meta.get("gap4_status"),
            "capture_ts": meta.get("capture_ts"), "url": meta.get("url"),
            "n_pages": len(reader.pages), "text_chars": len(text),
            "equity_section_found": sec is not None,
            "equity_section_verbatim": sec,
            "statements": [],
        }
        if sec is None:
            anomalies.append({"file": fn, "issue": "no 'Equity Products' section located"})
        else:
            matches = list(DATE_LINE.finditer(sec))
            if not matches:
                # one-pager normal-schedule statements carry no dated lines
                cls = classify_block(sec)
                rec["undated_block_classification"] = cls
                if cls not in ("NORMAL_SCHEDULE", "NO_STATEMENT"):
                    anomalies.append({"file": fn,
                                      "issue": f"undated non-regular block: {cls}"})
            for k, m in enumerate(matches):
                wd, mon, dd = m.group(1).lower(), m.group(2).lower(), int(m.group(3))
                block_end = matches[k + 1].start() if k + 1 < len(matches) else len(sec)
                block = sec[m.end():block_end]
                cls = classify_block(block)
                month = MONTHS[mon[:3]]
                year = resolve_year(meta.get("pdf_year"), month, fn)
                try:
                    d = date(year, month, dd)
                    wd_true = WEEKDAYS[d.weekday()]
                    wd_ok = wd_true == wd
                except ValueError:
                    d, wd_true, wd_ok = None, None, False
                stmt = {
                    "date": d.isoformat() if d else None,
                    "pdf_weekday": wd, "computed_weekday": wd_true,
                    "weekday_match": wd_ok,
                    "classification": cls,
                    "time_ct": first_time_ct(block),
                    "verbatim": " ".join(block.split())[:400],
                }
                rec["statements"].append(stmt)
                if not wd_ok:
                    anomalies.append({"file": fn, "date": stmt["date"],
                                      "issue": f"weekday mismatch pdf={wd} computed={wd_true}"})
                if d is not None and wd_ok:
                    rollup.setdefault(d.isoformat(), []).append(
                        {"file": fn, "sha256": sha, "classification": cls,
                         "time_ct": stmt["time_ct"]})
        out_files.append(rec)

    cand_classes = {"CLOSED", "HALT", "EARLY_CLOSE"}
    candidates = {}
    regular_adjudicated = {}
    for d, entries in sorted(rollup.items()):
        if any(e["classification"] in cand_classes for e in entries):
            candidates[d] = entries
        elif all(e["classification"] in ("REGULAR_CLOSE", "REGULAR_OPEN",
                                        "NORMAL_SCHEDULE") for e in entries):
            regular_adjudicated[d] = entries

    # Lemma-2 input: HALT/EARLY_CLOSE truncation times must pre-date 15:00 CT.
    # CLOSED days carry no session; a reopen time inside a CLOSED block (for
    # the next trade date) is not a truncation time and is exempt.
    trunc_classes = {"HALT", "EARLY_CLOSE"}
    trunc_times = {d: [e["time_ct"] for e in entries
                       if e["time_ct"] is not None
                       and e["classification"] in trunc_classes]
                   for d, entries in candidates.items()}
    trunc_times = {d: t for d, t in trunc_times.items() if t}
    bad_times = {d: t for d, t in trunc_times.items()
                 if t and any(x >= 1500 for x in t)}

    out = {
        "schema": "pdf_equity_evidence_2011_2015@1",
        "cycle_id": "FUTURES-ES-PB1-V1",
        "lane": "HOLIDAY-CLOSURE (M2)",
        "generated_utc": "2026-10-04",
        "method": "pypdf text extraction of committed per-holiday official CME Globex "
                  "schedule PDFs (2011-2015); 'CME Group Equity Products' section isolated; "
                  "dated statements classified CLOSED/HALT/EARLY_CLOSE/REGULAR_OPEN/"
                  "REGULAR_CLOSE/NORMAL_SCHEDULE; weekday of every parsed date re-computed "
                  "and cross-checked (mismatch => anomaly, excluded from rollup). "
                  "Zero network; committed bytes only.",
        "family_authority_note": "CME publishes ONE venue-wide CME Globex holiday schedule; "
                                 "the 'CME Group Equity Products' sections are equity-family "
                                 "authority (ES is a CME Group equity-index product). The 2010 "
                                 "official PDF parsed by NQ_CALENDAR_EVIDENCE.md carries no "
                                 "product carve-outs in equity sections (sole named exception: "
                                 "Nikkei). ES-specific transcription remains NOT_RUN at this SHA "
                                 "— these are candidate/adjudication INPUTS, not wired into the "
                                 "frozen exclude builder.",
        "source_corpus": {
            "dir": PDF_DIR,
            "catalog": COVERAGE_JSON,
            "n_pdfs": len(files),
            "duplicate_note": "FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/comm/"
                              "2011-thanksgiving.pdf is byte-identical (same sha256) to "
                              "fx_comm/captures/2011-thanksgiving.pdf",
        },
        "n_files": len(out_files),
        "n_equity_sections_found": sum(1 for r in out_files if r["equity_section_found"]),
        "candidate_dates_closed_halt_early": {
            d: {"entries": e,
                "truncation_times_ct": trunc_times.get(d)}
            for d, e in sorted(candidates.items())},
        "regular_adjudicated_dates": {
            d: e for d, e in sorted(regular_adjudicated.items())},
        "lemma2_truncation_times_all_below_1500ct":
            bool(trunc_times) and not bad_times,
        "lemma2_violations": bad_times,
        "anomalies": anomalies,
        "files": out_files,
    }
    path = os.path.join(WORKTREE, OUT_REL)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": OUT_REL,
        "n_files": len(out_files),
        "n_equity_sections": out["n_equity_sections_found"],
        "n_candidate_dates": len(candidates),
        "n_regular_adjudicated_dates": len(regular_adjudicated),
        "lemma2_ok": out["lemma2_truncation_times_all_below_1500ct"],
        "anomalies": len(anomalies),
        "candidate_date_span": [min(candidates), max(candidates)] if candidates else None,
    }, indent=2))


if __name__ == "__main__":
    main()
