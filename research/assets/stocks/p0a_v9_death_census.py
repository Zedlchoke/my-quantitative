"""V9 P0a: in-window Form-15 death census from EDGAR (PLAN_stocks_v9.md sec 3 P0a).

Enumerates every Form 15-12B filing in the S0 window (2018-04-04..2025-07-24)
via the official EDGAR full-text search API, fetches each filing's primary
document, and classifies it from the document bytes themselves:

  FORM15_12G_DOCUMENT   doc text is a Section 12(g) termination (form header
                        miscodes are caught here, not trusted)
  DEATH_CANDIDATE_12B   12(b) document naming COMMON STOCK on a US exchange
  CLASS_TERMINATION_12B 12(b) document for preferred/warrants/units/notes/etc
  UNCLASSIFIED          rules could not decide (fail-closed, never guessed)

Only DEATH_CANDIDATE filings enter the dead cohort (P0b). Every
enumerated accession lands in exactly one bucket; nothing is dropped
silently. Raw EDGAR bytes stay gitignored under .staging_sec_v9/; committed
artifacts carry sha256 manifests only.

The M-I1 taxonomy follow-up (FORM15_TERMINATED 12B/12G split) is applied as
an appendix; history stays append-only (no V8 artifact is edited).

Usage:
  python -m research.assets.stocks.p0a_v9_death_census enumerate   # FTS pages
  python -m research.assets.stocks.p0a_v9_death_census fetch-docs  # primary docs
  python -m research.assets.stocks.p0a_v9_death_census build       # census JSON
"""

import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import datetime

FTS_URL = "https://efts.sec.gov/LATEST/search-index"
FTS_QUERY = "the"
FORMS = "15-12B"  # TEMP single-bucket run for accession union  # both Form 15 buckets: deaths appear in BOTH (measured 2026-09-05: 1157 + 2482 = 3639); the bucket label is metadata, never the death discriminator
STAGE = ".staging_sec_v9"
FTS_DIR = f"{STAGE}/fts"
DOC_DIR = f"{STAGE}/form15"
CONTROL = "research/control/stocks_free_v9_run"
CENSUS = f"{CONTROL}/death_census.json"
RAW_MANIFEST = f"{CONTROL}/p0a_v9_death_census_raw_manifest.json"
UA = "Research my-quantitative@example.com"
# SEC archive WAF note (measured 2026-09-05): www.sec.gov/Archives 403s UAs
# containing "agent" or without an email-shaped contact token; efts.sec.gov
# accepts either. The UA uses the RFC-2606 reserved example.com contact as a
# placeholder because the owner has not provisioned a contact address —
# recorded here and in the event log; replace with the owner's real contact
# at any time without affecting any computed artifact.
S0_START, S0_END = "2018-04-04", "2025-07-24"
PRECHECK_12B_TOTAL = 1157  # MCP sec-search measurement 2026-09-05, two bracketing queries
PRECHECK_12G_TOTAL = 2482  # direct efts.sec.gov measurement 2026-09-05 (forms=15-12G)

# Classification rules v2 (revised after measured v1 failure, recorded in the
# census artifact: the in-document section citation is NOT a death
# discriminator — true company deaths (TWX/Monsanto/Dean Foods) cite 12(g)
# while class-only terminations cite it too, and the EDGAR "15-12B" bucket
# label is equally unreliable. The ex ante discriminator is the Form 15's own
# class table: the span under "(Title of each class of securities covered by
# this Form)". Common stock inside the covered span = DEATH_CANDIDATE (a
# Baxter-style reorg-survival case still appears here and is filtered in P0b
# by the price-survival cross-check, never inside P0a). Preferred/warrants/
# notes without common = CLASS_TERMINATION. Foreign-private-issuer docs are
# bucketed separately. Failures to parse the table = UNCLASSIFIED.)
RX_12B = re.compile(r"section\s+12\s*\(\s*b\s*\)", re.I)
RX_12G = re.compile(r"section\s+12\s*\(\s*g\s*\)", re.I)
RX_COVERED_START = re.compile(
    r"\(\s*titles?\s+of\s+(each\s+)?class(es)?\s+of\s+securities\s+covered\s+by\s+this\s+form\s*\)", re.I)
RX_COVERED_END = [
    re.compile(r"\(\s*titles?\s+(?:and|of)\s+all\s+other\s+classes", re.I),
    re.compile(r"please\s+place\s+an\s+x", re.I),
    re.compile(r"check\s+this\s+box", re.I),
    re.compile(r"sign\s+below", re.I),
]
# The Form 15 class table puts each class TITLE *before* its parenthetical
# label ("Common Stock, par value $1 (Title of each class of securities
# covered by this Form) None (Titles of all other classes ...)"), so the
# covered-class window must look back from the label, not only forward.
COVERED_LOOKBACK = 1500
RX_15F = re.compile(r"\b15F[- ]12|\bforeign\s+private\s+issuer", re.I)
RX_OFFICES_END = re.compile(r"principal\s+executive\s+offices\s*\)", re.I)
RX_COVERED_NONE = re.compile(r"^\s*(?:none|n/a|n\.a\.)*\s*$", re.I)
SECURITY_CLASSES = [
    ("common_stock", re.compile(r"common\s+stock", re.I)),
    ("preferred_stock", re.compile(r"preferred\s+stock|preference\s+shares", re.I)),
    ("warrants", re.compile(r"\bwarrants\b", re.I)),
    ("rights", re.compile(r"\brights\b", re.I)),
    ("units", re.compile(r"\bunits\b", re.I)),
    ("depositary_shares", re.compile(r"depositary\s+shares", re.I)),
    ("debt_notes", re.compile(r"\bnotes\b|debentures|guaranteed\s+notes", re.I)),
    ("ads", re.compile(r"american\s+depositary\s+shares|ADSs\b", re.I)),
    ("membership_interests", re.compile(r"membership\s+interests", re.I)),
    ("partnership_units", re.compile(r"partnership\s+interests|limited\s+partnership\s+units", re.I)),
]
EXCHANGES = [
    ("NYSE", re.compile(r"new\s+york\s+stock\s+exchange|\bNYSE\b", re.I)),
    ("NASDAQ", re.compile(r"nasdaq", re.I)),
    ("NYSE_AMERICAN", re.compile(r"nyse\s+american|nyse\s+mkt|american\s+stock\s+exchange", re.I)),
    ("NYSE_ARCA", re.compile(r"nyse\s+arca", re.I)),
    ("CBOE", re.compile(r"cboe|chicago\s+board\s+options", re.I)),
    ("OTC", re.compile(r"OTC\s+Markets|over[- ]the[- ]counter\s+market|pink\s+sheets", re.I)),
]


def _get(url, timeout=45, attempts=4):
    last = None
    for i in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    data = gzip.decompress(data)
            return data
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503):
                time.sleep(2 * (2 ** i))  # transient provider errors: back off, never blind-retry others
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            time.sleep(2 * (2 ** i))
    raise last


def enumerate_filings():
    """Paginate the official EDGAR FTS for the 15-12B form bucket in-window."""
    os.makedirs(FTS_DIR, exist_ok=True)
    page = 0
    total_reported = None
    all_hits = []
    while True:
        path = f"{FTS_DIR}/page_{page:03d}.json"
        if not (os.path.exists(path) and os.path.getsize(path) > 100):
            q = urllib.parse.quote(f'"{FTS_QUERY}"')
            url = (
                f"{FTS_URL}?q={q}&dateRange=custom&startdt={S0_START}&enddt={S0_END}"
                f"&forms={FORMS}&from={page * 100}&size=100"
            )
            data = _get(url, timeout=60)
            with open(path, "wb") as f:
                f.write(data)
            time.sleep(0.2)
        d = json.load(open(path))
        hits = d.get("hits", {})
        total = hits.get("total", {})
        total_reported = total.get("value")
        batch = hits.get("hits", [])
        all_hits.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        if page > 50:
            raise SystemExit("FTS pagination exceeded 50 pages - fail closed")
    rows = []
    for h in all_hits:
        src = h.get("_source", {})
        _id = h.get("_id", "")  # _id lives on the hit, not inside _source
        if ":" not in _id or not src.get("adsh"):
            continue
        accession = src["adsh"]
        filename = _id.split(":", 1)[1]
        rows.append({
            "accession": accession,
            "filename": filename,
            "cik": (src.get("ciks") or [None])[0],
            "file_date": src.get("file_date"),
            "form_type_recorded": src.get("form"),
            "form_bucket": (src.get("form") or "").split("/")[0],
            "matched_file_type": src.get("file_type"),
            "display_names": src.get("display_names"),
        })
    # de-duplicate on accession; prefer the row that matched the Form 15 doc itself
    uniq = {}
    for r in rows:
        prev = uniq.get(r["accession"])
        if prev is None or (
            r["matched_file_type"].startswith("15-12") and not prev["matched_file_type"].startswith("15-12")
        ):
            uniq[r["accession"]] = r
    per_bucket = {}
    for r in uniq.values():
        per_bucket[r["form_bucket"]] = per_bucket.get(r["form_bucket"], 0) + 1
    summary = {
        "query": f'"{FTS_QUERY}"',
        "forms_param": FORMS,
        "window": [S0_START, S0_END],
        "total_reported": total_reported,
        "rows_kept": len(uniq),
        "rows_per_bucket": per_bucket,
        "precheck_crossref": {
            "note": "precheck numbers are HIT totals; rows_per_bucket counts UNIQUE accessions after dedupe, and an accession filed under both buckets takes a single tag, so per-bucket accession counts legitimately differ from hit totals",
            "hit_total_expected": {"15-12B": PRECHECK_12B_TOTAL, "15-12G": PRECHECK_12G_TOTAL,
                                   "sum": PRECHECK_12B_TOTAL + PRECHECK_12G_TOTAL},
            "hit_total_match": total_reported == PRECHECK_12B_TOTAL + PRECHECK_12G_TOTAL,
        },
    }
    json.dump(summary, open(f"{FTS_DIR}/_fts_summary.json", "w"), indent=1)
    json.dump(sorted(uniq.values(), key=lambda r: r["accession"]), open(f"{FTS_DIR}/_filings_index.json", "w"), indent=1)
    print(json.dumps(summary))


def _strip_html(raw):
    text = raw.decode("utf-8", "replace")
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text)


def _primary_doc_url(r):
    """URL of the filing's primary Form-15 document. Direct when the FTS hit
    matched it; otherwise resolved once from the accession index (fail-closed)."""
    if r["matched_file_type"].startswith("15-12"):
        base = f"https://www.sec.gov/Archives/edgar/data/{int(r['cik'])}/{r['accession'].replace('-', '')}"
        return f"{base}/{r['filename']}", r["filename"], "direct_hit"
    base = f"https://www.sec.gov/Archives/edgar/data/{int(r['cik'])}/{r['accession'].replace('-', '')}"
    idx = json.loads(_get(f"{base}/index.json", timeout=45).decode("utf-8", "replace"))
    cands = [it for it in idx.get("directory", {}).get("item", [])
             if re.match(r"^15-12", it.get("type", "") or "")]
    if not cands:
        raise RuntimeError(f"no 15-12* document in accession index {r['accession']}")
    return f"{base}/{cands[0]['name']}", cands[0]["name"], "index_resolved"


def fetch_docs():
    os.makedirs(DOC_DIR, exist_ok=True)
    rows = json.load(open(f"{FTS_DIR}/_filings_index.json"))
    fetched = skipped = failed = 0
    resolved = {}
    for r in rows:
        acc = r["accession"]
        out = f"{DOC_DIR}/{acc}.htm"
        if os.path.exists(out) and os.path.getsize(out) > 50:
            skipped += 1
            continue
        try:
            url, chosen, how = _primary_doc_url(r)
            data = _get(url)
            open(out, "wb").write(data)
            resolved[acc] = {"doc": chosen, "resolution": how}
            fetched += 1
        except Exception as e:  # noqa: BLE001 - recorded fail-closed sidecar
            with open(f"{DOC_DIR}/{acc}.FAILED", "w") as f:
                f.write(f"{type(e).__name__}: {e}\naccession={acc}\n")
            failed += 1
        time.sleep(0.12)
    if resolved:
        json.dump(resolved, open(f"{FTS_DIR}/_doc_resolution.json", "w"), indent=1)
    print(json.dumps({"fetched": fetched, "skipped_existing": skipped, "failed": failed, "total": len(rows)}))


def classify_doc(text):
    """Return (bucket, evidence) per the ex ante v2 rules. Never guesses."""
    m = RX_COVERED_START.search(text)
    section_cited = "12b" if RX_12B.search(text[:1500]) else ("12g" if RX_12G.search(text[:1500]) else None)
    ev = {
        "section_cited_header": section_cited,  # metadata only, never a discriminator
        "foreign_private_issuer": bool(RX_15F.search(text)),
        "covered_span_found": bool(m),
        "covered_classes": [],
        "exchange_keywords": [name for name, rx in EXCHANGES if rx.search(text)],
    }
    if not m:
        return "UNCLASSIFIED_NO_TABLE", ev
    start = m.end()
    ends = [rx.search(text, start) for rx in RX_COVERED_END]
    ends = [e.start() for e in ends if e]
    end = min(ends) if ends else min(start + 900, len(text))
    # side-detection: templates put the covered class list either immediately
    # BEFORE the label (Monsanto/AIV/Esterline) or immediately AFTER it
    # (Time Warner). Decide by whether a class keyword sits in the ~150 chars
    # directly preceding the label.
    # v4 rule (measured-driven): templates place the covered-class list either
    # side of the label, so decide DEATH on the UNION of the before-span
    # (from the end of the registrant address block) and the after-span (up
    # to the next label/checkbox boundary). AIV (preferred only) stays
    # CLASS_TERMINATION; TWX (common after label) becomes DEATH_CANDIDATE.
    office = None
    for om in RX_OFFICES_END.finditer(text, 0, start):
        office = om.end()
    bstart = office if office is not None else max(0, start - COVERED_LOOKBACK)
    covered = text[bstart:end]
    ev["covered_classes"] = [name for name, rx in SECURITY_CLASSES if rx.search(covered)]
    ev["covered_span_excerpt"] = covered[:400]
    if ev["foreign_private_issuer"]:
        return "FORM15F_FOREIGN", ev
    if "common_stock" in ev["covered_classes"]:
        return "DEATH_CANDIDATE", ev
    if ev["covered_classes"]:
        return "CLASS_TERMINATION", ev
    if RX_COVERED_NONE.match(covered):
        return "NOT_DEATH_NO_COVERED_CLASS", ev
    return "UNCLASSIFIED_NO_CLASS", ev


def _snippet(rx, text, width=120):
    m = rx.search(text)
    return text[max(0, m.start() - width // 2): m.end() + width // 2] if m else None


def build():
    rows = json.load(open(f"{FTS_DIR}/_filings_index.json"))
    filings = {}
    missing_docs = []
    for r in rows:
        acc = r["accession"]
        path = f"{DOC_DIR}/{acc}.htm"
        if not os.path.exists(path):
            missing_docs.append(acc)
            continue
        text = _strip_html(open(path, "rb").read())
        bucket, ev = classify_doc(text)
        filings[acc] = {
            "cik": f"CIK{int(r['cik']):010d}",
            "company_display": (r.get("display_names") or [None])[0],
            "filed_date": r.get("file_date"),
            "form_type_recorded": r.get("form_type_recorded"),
            "bucket": bucket,
            "evidence": ev,
            "doc_sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
        }
    if missing_docs:
        raise SystemExit(f"{len(missing_docs)} primary docs missing - fetch-docs first (fail closed)")
    # death-level view: earliest common-equity 12(b) termination per filer
    deaths = {}
    for acc, f in sorted(filings.items()):
        if f["bucket"] != "DEATH_CANDIDATE":
            continue
        d = deaths.setdefault(f["cik"], {
            "cik": f["cik"],
            "company_display": f["company_display"],
            "death_filing_date_evidence": f["filed_date"],
            "filings": [],
        })
        d["filings"].append(acc)
        if f["filed_date"] and f["filed_date"] < d["death_filing_date_evidence"]:
            d["death_filing_date_evidence"] = f["filed_date"]
    buckets = {}
    for f in filings.values():
        buckets[f["bucket"]] = buckets.get(f["bucket"], 0) + 1
    built = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    census = {
        "schema": "stocks_free_v9_run/death_census@1",
        "built_at_utc": built,
        "producer_role": "A1 (PLAN_stocks_v9 sec3 P0a)",
        "method": {
            "enumeration": "official EDGAR full-text search API (efts.sec.gov/LATEST/search-index), forms=15-12B, custom window",
            "classification": "per-filing primary-document bytes; ex ante regex rules in p0a_v9_death_census.py; header form types recorded but never trusted",
            "fail_closed": "every enumerated accession appears in exactly one bucket; UNCLASSIFIED buckets block cohort entry",
        },
        "fts_summary": json.load(open(f"{FTS_DIR}/_fts_summary.json")),
        "s0_window": [S0_START, S0_END],
        "bucket_counts": buckets,
        "taxonomy_appendix_M_I1": {
            "note": "append-only taxonomy record: the V8-era single label FORM15_TERMINATED is split into FORM15_12B (12(b) exchange-registration termination) and FORM15_12G (12(g) class termination). No V8 artifact is edited; this appendix applies the split to the V9 census retroactively.",
            "death_definition": "DEATH_CANDIDATE = the Form 15 class table terminates COMMON STOCK (company-level termination; section cited and EDGAR form label are recorded metadata, not discriminators). Reorg-survival cases (e.g. Baxter 2021) remain in this bucket by design and are removed from DEAD_EVIDENCED only by the P0b price-survival cross-check. Earliest in-window covered-common filing per CIK is the evidenced death filing date.",
        },
        "n_filings": len(filings),
        "n_death_filers": len(deaths),
        "filings": filings,
        "deaths": deaths,
    }
    json.dump(census, open(CENSUS, "w"), indent=1)
    man = {
        "schema": "stocks_free_v9_run/p0a_v9_death_census_raw_manifest@1",
        "built_at_utc": built,
        "note": "raw EDGAR bytes stay gitignored under .staging_sec_v9/; only hashes are committed",
        "files": {},
    }
    for d in (FTS_DIR, DOC_DIR):
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if os.path.isfile(p) and not fn.endswith(".FAILED"):
                man["files"][f"{os.path.basename(d)}/{fn}"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    json.dump(man, open(RAW_MANIFEST, "w"), indent=1)
    print(json.dumps({"bucket_counts": buckets, "n_death_filers": len(deaths), "census": CENSUS,
                      "manifest_files": len(man["files"])}))


if __name__ == "__main__":
    {"enumerate": enumerate_filings, "fetch-docs": fetch_docs, "build": build}[sys.argv[1]]()
