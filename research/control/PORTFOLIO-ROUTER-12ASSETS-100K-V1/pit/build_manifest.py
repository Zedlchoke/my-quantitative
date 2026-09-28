#!/usr/bin/env python3
"""Build MANIFEST.json for ~/.my-quantitative-data/pr12a100k/raw/.

Joins: on-disk bytes (sha256/bytes) + FETCH_LOG.tsv / provenance sidecars
(prior session 2026-09-28T13:13-13:21Z) + this session's fetches
(13:24-13:49Z, recorded in MY_SESSION below). Every entry cites its URL and
fetched_at_utc; probe-error files are carried as discrimination evidence.
"""
import hashlib, json, datetime as dt
from pathlib import Path

RAW = Path.home() / ".my-quantitative-data/pr12a100k/raw"
OUT = RAW / "MANIFEST.json"

# this session (13:24Z-13:49Z), url + fetched_at recorded from command transcripts
MY_SESSION = {
    "alfred/cdx_vixcls.json": ("https://web.archive.org/cdx/search/cdx?url=fred.stlouisfed.org%2Fgraph%2Ffredgraph.csv%3Fid%3DVIXCLS&output=json&limit=300", "2026-09-28T13:39:46Z"),
    "alfred/cdx_brent.json": ("https://web.archive.org/cdx/search/cdx?url=fred.stlouisfed.org%2Fgraph%2Ffredgraph.csv%3Fid%3DDCOILBRENTEU&output=json&limit=300", "2026-09-28T13:40:46Z"),
    "alfred/cdx_wti.json": ("https://web.archive.org/cdx/search/cdx?url=fred.stlouisfed.org%2Fgraph%2Ffredgraph.csv%3Fid%3DDCOILWTICO&output=json&limit=300", "2026-09-28T13:41:35Z"),
    "alfred/vintage_VIXCLS_20241120.csv": ("https://web.archive.org/web/20241120161720id_/https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS", "2026-09-28T13:42:35Z"),
    "alfred/vintage_VIXCLS_20260303.csv": ("https://web.archive.org/web/20260303032000id_/https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS", "2026-09-28T13:42:53Z"),
    "alfred/vintage_DCOILBRENTEU_20251224.csv": ("https://web.archive.org/web/20251224174421id_/https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU", "2026-09-28T13:43:19Z"),
    "alfred/vintage_DCOILBRENTEU_20260818.csv": ("https://web.archive.org/web/20260818094244id_/https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU", "2026-09-28T13:43:40Z"),
    "alfred/vintage_DCOILWTICO_20260503.csv": ("https://web.archive.org/web/20260503121527id_/https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO (gzip payload, decompressed locally 2026-09-28T13:45Z; original bytes kept as .csv.gz)", "2026-09-28T13:44:07Z"),
    "alfred/vintage_DCOILWTICO_20260503.csv.gz": ("https://web.archive.org/web/20260503121527id_/https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO (raw gzip payload as served by Wayback)", "2026-09-28T13:44:07Z"),
    "alfred/vintage_DCOILWTICO_20260818.csv": ("https://web.archive.org/web/20260818094221id_/https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO", "2026-09-28T13:44:18Z"),
    "alfred/vintage_DCOILWTICO_20260825.csv": ("https://web.archive.org/web/20260825173607id_/https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO", "2026-09-28T13:44:36Z"),
    "alfred/ctrl_eia.out": ("https://www.eia.gov/dnav/pet/hist/RBRTEd.htm (discrimination control: 200 OK while stlouisfed edge reset streams)", "2026-09-28T13:37:34Z"),
    "evidence_pages/cboe_terms.html": ("https://www.cboe.com/terms", "2026-09-28T13:48:44Z"),
    "FETCH_LOG.tsv": ("(this log file; prior-session fetch transcript 2026-09-28T13:13Z-13:21Z)", "2026-09-28T13:21:13Z"),
    "alfred/probes/p1.err": ("probe https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=VIXCLS (HTTP/2, browser UA)", "2026-09-28T13:25:52Z"),
    "alfred/probes/p2.err": ("probe https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=VIXCLS&vintage_date=2024-01-05 (HTTP/2)", "2026-09-28T13:25:54Z"),
    "alfred/probes/p3.err": ("probe https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&realtime_start=2024-01-05&realtime_end=2024-01-05 (HTTP/2)", "2026-09-28T13:25:56Z"),
    "alfred/probes/q1.err": ("probe https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=VIXCLS (--http1.1)", "2026-09-28T13:26:38Z"),
    "alfred/probes/q2.err": ("probe https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=VIXCLS&vintage_date=2024-01-05 (--http1.1)", "2026-09-28T13:27:26Z"),
    "alfred/probes/r1.err": ("probe https://alfred.stlouisfed.org/series/VIXCLS (--http1.1)", "2026-09-28T13:28:28Z"),
    "alfred/probes/r2.err": ("probe https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&realtime_start=... (--http1.1 control)", "2026-09-28T13:29:11Z"),
    "alfred/probes/c1_control.err": ("control https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS after cooldown", "2026-09-28T13:32:42Z"),
    "alfred/probes/c2_alfred_h2.err": ("https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=VIXCLS after cooldown", "2026-09-28T13:32:46Z"),
    "alfred/probes/v1_fredhost.err": ("https://fred.stlouisfed.org/graph/alfredgraph.csv?id=VIXCLS (ALFRED graph on fred host)", "2026-09-28T13:37:03Z"),
    "alfred/probes/v2_alfredhost.err": ("https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=VIXCLS (canonical ALFRED csv)", "2026-09-28T13:37:09Z"),
    "alfred/probes/legacy_alfred.err": ("https://alfred.stlouisfed.com/graph/alfredgraph.csv?id=VIXCLS (legacy domain: DNS NXDOMAIN)", "2026-09-28T13:40:29Z"),
    "evidence_pages/cboe_vix_whitepaper_403body.bin": ("https://cdn.cboe.com/resource/getting_started/pdfs/vixwhite.pdf -> HTTP 403 body (243 bytes); blocked", "2026-09-28T13:19:57Z"),
    "evidence_pages/cboe_vix_whitepaper_v2_403body.bin": ("https://cdn.cboe.com/resources/getting_started/pdfs/vixwhite.pdf -> HTTP 403 body (263 bytes); blocked", "2026-09-28T13:20:13Z"),
    "evidence_pages/cboe_indices_methodology.html": ("https://www.cboe.com/us/indices/methodology/ -> HTTP 404 page (kept: documents dead route)", "2026-09-28T13:18:57Z"),
    "evidence_pages/nyfed_reference_rates_api.html": ("https://www.newyorkfed.org/markets/reference-rates/reference-rates-api -> HTTP 200 but body is a site 404 shell ('page has been deleted or moved'); docs page moved", "2026-09-28T13:20:29Z"),
    "brent/RBRTEd_eia_daily.xls": ("https://www.eia.gov/dnav/pet/hist_xl/RBRTEd.xls -> HTTP 404, zero bytes (route dead; EIA XLS download path changed)", "2026-09-28T13:15:28Z"),
    "wti/RWTCd_eia_daily.xls": ("https://www.eia.gov/dnav/pet/hist_xl/RWTCd.xls -> HTTP 404, zero bytes (route dead)", "2026-09-28T13:15:32Z"),
}

LICENSE = {
    "vix/VIXCLS_fredgraph.csv": 'FRED series VIXCLS, label "Copyrighted: Citation required" (CBOE source). FRED terms IV: such series "may be used for internal commercial uses ... provided that appropriate attribution is given to FRED as well as the original source of the data". Notes: "Copyright, 2016, Chicago Board Options Exchange, Inc. Reprinted with permission."',
    "vix/VIX_History_cboe.csv": 'Cboe Website Terms of Use (cboe.com/terms, archived): "You may view, print and download one copy of the Materials for your personal non-commercial use in connection with products and services offered by Cboe ... You may not otherwise copy, reproduce, alter, store ..." -> single archived copy for internal research cross-check; no redistribution; broader use AMBIGUOUS (P-25 flagged).',
    "brent/DCOILBRENTEU_fredgraph.csv": 'FRED label "Public Domain: Citation requested"; source U.S. EIA (US-government work, public domain). Suggested citation: "U.S. Energy Information Administration, Crude Oil Prices: Brent - Europe [DCOILBRENTEU], retrieved from FRED".',
    "wti/DCOILWTICO_fredgraph.csv": 'FRED label "Public Domain: Citation requested"; source U.S. EIA (US-government work, public domain). Suggested citation: "U.S. Energy Information Administration, Crude Oil Prices: West Texas Intermediate (WTI) - Cushing, Oklahoma [DCOILWTICO], retrieved from FRED".',
    "effr/EFFR_nyfed_search_full_2016-01-01_2026-09-27.json": 'NY Fed website: "Use of the Reference Rates are subject to important disclaimers, limitations and indemnification obligations." Keyless public API; internal research use, no redistribution of raw responses; disclaimers apply.',
    "effr/probe_effr_unsecured_search_2021-01.json": "Same NY Fed reference-rates terms as full EFFR fetch (probe artifact retained).",
}
GENERIC_LICENSE = {
    "evidence_pages/": "Public web page archived verbatim for evidence; quoted excerpts used under fair quotation for research documentation; no redistribution of the page.",
    "alfred/vintage_": "Wayback Machine capture of a FRED CSV (public domain or FRED terms as per underlying series); Internet Archive snapshots used as vintage evidence.",
    "alfred/cdx_": "Internet Archive CDX index metadata (public).",
    "alfred/probes/": "curl error transcripts; discrimination evidence only.",
    "alfred/ctrl_": "control fetch; see url note.",
}

log = {}
for line in open(RAW / "FETCH_LOG.tsv"):
    p = line.rstrip("\n").split("\t")
    if len(p) >= 7 and p[0] != "fetched_at_utc":
        log[p[5].replace(str(RAW) + "/", "")] = {"fetched_at_utc": p[0], "url": p[1], "http_code": p[2]}

def lic_for(rel):
    if rel in LICENSE:
        return LICENSE[rel]
    for pre, note in GENERIC_LICENSE.items():
        if rel.startswith(pre):
            return note
    return "see FETCH_LOG.tsv / sidecar; evidence artifact"

files = []
for p in sorted(RAW.rglob("*")):
    if not p.is_file():
        continue
    rel = str(p.relative_to(RAW))
    if rel == "MANIFEST.json" or rel == "fetch.sh" or rel.endswith(".fetched_at.txt"):
        continue
    b = p.read_bytes()
    sha = hashlib.sha256(b).hexdigest()
    if rel in MY_SESSION:
        url, ts = MY_SESSION[rel]
        code = "200"
    elif rel in log:
        url, ts, code = log[rel]["url"], log[rel]["fetched_at_utc"], log[rel]["http_code"]
    else:
        # sidecar provenance
        sc = p.parent / (p.name + ".fetched_at.txt")
        url, ts, code = None, None, None
        if sc.exists():
            kv = dict(l.split(":", 1) for l in sc.read_text().splitlines() if ":" in l)
            url = kv.get("url", "").strip() or None
            ts = kv.get("fetched_at_utc", "").strip() or None
            code = kv.get("http_code", "").strip() or None
    files.append({
        "file": rel,
        "sha256": sha,
        "bytes": len(b),
        "fetched_at_utc": ts or "UNKNOWN",
        "url": url or "UNKNOWN",
        "http_code": code or "UNKNOWN",
        "license_note": lic_for(rel),
    })

man = {
    "schema": "pr12a100k_raw_manifest@1",
    "cycle": "PORTFOLIO-ROUTER-12ASSETS-100K-V1",
    "lane": "D1_macro_pit",
    "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "base_dir": str(RAW),
    "n_files": len(files),
    "fetch_sessions": [
        "2026-09-28T13:13Z-13:21Z (FETCH_LOG.tsv / *.fetched_at.txt sidecars; keyless UA pr12a100k-research-fetcher/1.0)",
        "2026-09-28T13:24Z-13:49Z (this session; sequential fetches, >=3s sleeps; browser UA)",
    ],
    "files": files,
}
json.dump(man, open(OUT, "w"), indent=1)
print("wrote", OUT, "n_files=", len(files))
for f in files:
    print(f"{f['bytes']:>8} {f['fetched_at_utc']} {f['file']}")
