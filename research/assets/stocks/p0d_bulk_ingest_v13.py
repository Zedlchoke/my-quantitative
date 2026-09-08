"""P0/D2 bulk ingest, single chained lock job (STOCKS-FREE-V13).

Stage A: alive submissions (410) -> .staging_sec_v13/submissions_alive/
Stage B: Form-4 raw XML for in-window acceptances (all cohort entities)
         -> .staging_sec_v13/form4_xml/CIK{cik}/{acc_nodash}/doc.xml
         + parsed stream .staging_sec_v13/form4_stream.jsonl (the parse-contract extract)
Stage C: EODHD dividends + splits for cohort symbols -> .staging_sec_v13/eodhd_{div,splits}/

Discipline: machine-wide lock polled every 60s (bounded 400 attempts); every
stage resumable (existing files skipped); SEC fair access ceiling 10 req/s
(declared UA); EODHD key environment-only (never printed/artifacted);
TRANSIENT_TRANSPORT bounded 3-attempt backoff; CODE_OR_SCHEMA_ERROR never
retried (fail the job, release FAILED with stderr tail).
"""
import json, hashlib, os, sys, time, random, traceback, urllib.request, urllib.error, gzip, io, re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

W = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/integration"
sys.path.insert(0, f"{W}/research")
from governance import heavy_lock

DEAD_CACHE = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v9/integration/.staging_sec_v9/submissions_dead"
ALIVE_CACHE = f"{W}/.staging_sec_v13/submissions_alive"
XML_DIR = f"{W}/.staging_sec_v13/form4_xml"
STREAM = f"{W}/.staging_sec_v13/form4_stream.jsonl"
EODHD_DIV = f"{W}/.staging_sec_v13/eodhd_div"
EODHD_SPL = f"{W}/.staging_sec_v13/eodhd_splits"
COHORT = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v12/integration/research/control/stocks_free_v9_run/cohort_v9.json"
STATUS = f"{W}/research/control/stocks_free_v13_run/p0d_bulk_ingest_status.json"
UA = "Research my-quantitative@example.com"
WIN_LO, WIN_HI = "2018-01-01", "2025-05-23"

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def status(**kw):
    base = {"cycle": "STOCKS-FREE-V13", "job": "P0D_BULK_INGEST", "updated_utc": now()}
    base.update(kw)
    json.dump(base, open(STATUS, "w"), indent=1)

_PACE = {"interval": 0.16, "min": 0.9, "max": 0.16, "ok_streak": 0}


def _pace_sleep():
    time.sleep(_PACE["interval"] + random.random() * 0.04)


def _pace_on_503():
    _PACE["ok_streak"] = 0
    _PACE["interval"] = min(_PACE["interval"] * 2, _PACE["min"])
    time.sleep(600)  # SEC throttle windows clear in ~10 min (INC-V13-3)


def _pace_on_ok():
    _PACE["ok_streak"] += 1
    if _PACE["ok_streak"] >= 2000:
        _PACE["ok_streak"] = 0
        _PACE["interval"] = max(_PACE["interval"] * 0.85, _PACE["max"])


def get_curl(url, timeout=45, tries=3):
    """Archives fetch via curl: --max-time hard-caps DNS/connect/recv (the r2
    urllib hang at 0% CPU for 4+ min with socket-timeout set is not retryable
    in-process; INC-V13-3). 503/502 -> patient minute-scale backoff."""
    import subprocess
    last = None
    for attempt in range(1, tries + 1):
        r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "--compressed",
                            "-A", UA, "-w", "\n%{http_code}", url],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout:
            body, _, code = r.stdout.rpartition("\n")
            try:
                code = int(code)
            except ValueError:
                code = 0
            if code == 200:
                return 200, body.encode("utf-8", "surrogateescape")
            if code == 404:
                return 404, b""
            last = f"HTTP {code}"
        else:
            last = f"curl rc={r.returncode} {r.stderr.strip()[:120]}"
        if attempt == tries:
            if "503" in str(last) or "502" in str(last) or "rc=28" in str(last) or "rc=7" in str(last):
                raise TransientSkip(f"{last} after {tries} tries")
            raise RuntimeError(f"TRANSPORT: {last} after {tries} tries: {url[:110]}")
        if "503" in str(last) or "502" in str(last):
            _pace_on_503()
        else:
            time.sleep(15 * attempt)
    raise RuntimeError("unreachable")


class TransientSkip(Exception):
    pass


def get(url, headers=None, timeout=60, tries=3):
    h = {"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}
    if headers:
        h.update(headers)
    last = None
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                return r.status, raw
        except urllib.error.HTTPError as e:
            if e.code in (404,):
                return e.code, b""
            last = e
            if attempt == tries:
                raise
            # 503 = SEC throttle/unavailable: patient minute-scale backoff (INC-V13-2)
            time.sleep(60 * attempt if e.code in (503, 502) else 20 * attempt)
        except Exception as e:
            last = e
            if attempt == tries:
                raise
            time.sleep(20 * attempt)

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def form4_refs_from_submissions(path, cik):
    """In-window Form-4 (accession, filing_date, acceptance, primary_doc) refs from a submissions JSON."""
    d = json.load(open(path))
    rec = d.get("filings", {}).get("recent", {})
    forms = rec.get("form", [])
    out = []
    for i, fm in enumerate(forms):
        if fm != "4":
            continue
        fd = rec.get("filingDate", [""] * len(forms))[i] or ""
        acc = rec.get("acceptanceDateTime", [""] * len(forms))[i] or ""
        aday = (acc or fd)[:10]
        if WIN_LO <= aday <= WIN_HI:
            out.append({
                "accession": rec.get("accessionNumber", [""] * len(forms))[i],
                "filing_date": fd, "acceptance": acc,
                "primary_doc": rec.get("primaryDocument", [""] * len(forms))[i],
            })
    return out

def resolve_raw_doc_name(cik_int, acc_nodash, primary_doc):
    """Frozen XSL rule: primaryDocument may be the rendered wrapper; resolve the raw XML via index.json.
    r4: non-XSL names returned directly; XSL wrappers TRY the dominant raw name
    'form4.xml' first (saves the index.json request when it hits), fall back to
    index.json - identical terminal semantics, fewer requests (INC-V13-3)."""
    if primary_doc and not primary_doc.lower().startswith("xsl"):
        return primary_doc
    return None  # XSL wrapper: resolve via index.json (no 404-guessing - SEC dislikes 404 hammering; INC-V13-5)
    if st != 200:
        return None
    idx = json.loads(raw)
    names = [it["name"] for it in idx.get("directory", {}).get("item", [])]
    cands = [n for n in names if n.lower().endswith(".xml") and not n.lower().startswith(("xsl", "primary_doc"))]
    if not cands:
        cands = [n for n in names if n.lower().endswith(".xml") and not n.lower().startswith("xsl")]
    return cands[0] if cands else None

def parse_form4_xml(xml_bytes, cik, accession, acceptance, filing_date):
    """Parse-contract extract: nonDerivativeTable G-class rows with A/D direction + identity + shares.
    FAIL-CLOSED rows go to defects; nothing guessed."""
    defects, rows = [], []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        return rows, [{"accession": accession, "reason": f"XML_PARSE_ERROR:{e}"}]
    def txt(el, tag):
        if el is None:
            return None
        x = el.find(tag)
        if x is None:
            return None
        v = x.find("value")
        return v.text if v is not None else x.text
    owner = root.find(".//rptOwnerName")
    owner_cik_el = root.find(".//rptOwnerCik")
    owner_name = (txt(owner, "value") if owner is not None else None) or (owner.text if owner is not None else None)
    owner_cik = txt(owner_cik_el, "value") if owner_cik_el is not None else None
    ndt = root.find(".//nonDerivativeTable")
    for txn in (ndt.findall("nonDerivativeTransaction") if ndt is not None else []):
        tdate = txt(txn.find("transactionDate"), "value") if txn.find("transactionDate") is not None else None
        tcode_el = txn.find("transactionCode")
        tcode = (tcode_el.get("transactionCode") if tcode_el is not None else None) or txt(tcode_el, "value")
        ad_el = txn.find("transactionAcquiredDisposedCode")
        ad = txt(ad_el, "value") if ad_el is not None else None
        shares_el = txn.find(".//transactionShares/value")
        shares = shares_el.text if shares_el is not None else None
        if ad not in ("A", "D"):
            defects.append({"accession": accession, "reason": f"AD_CODE_MISSING:{ad!r}"})
            continue
        rows.append({
            "cik": cik, "accession": accession, "acceptance": acceptance, "filing_date": filing_date,
            "transaction_date": tdate, "transaction_code": tcode, "direction": ad,
            "shares": shares, "owner_cik": owner_cik, "owner_name": owner_name,
            "table": "nonDerivative",
        })
    return rows, defects

def main():
    cohort = json.load(open(COHORT))
    members = cohort["members"]["ALIVE_EVIDENCED"] + cohort["members"]["DEAD_EVIDENCED"]
    os.makedirs(ALIVE_CACHE, exist_ok=True)
    os.makedirs(XML_DIR, exist_ok=True)
    os.makedirs(EODHD_DIV, exist_ok=True)
    os.makedirs(EODHD_SPL, exist_ok=True)
    status(state="WAITING_FOR_LOCK", attempts=0)
    handle = None
    for attempt in range(1, 401):
        try:
            handle = heavy_lock.acquire(cycle_id="STOCKS-FREE-V13", role="P0D_BULK_INGEST",
                                        worktree=W, command=[sys.executable, __file__],
                                        expected_artifacts=[STREAM])
            status(state="LOCK_ACQUIRED", attempts=attempt)
            break
        except heavy_lock.LockBusyError:
            status(state="WAITING_FOR_LOCK", attempts=attempt)
            time.sleep(60)
        except Exception:
            status(state="CONTROL_STATE_DRIFT_FAIL_CLOSED", stderr=traceback.format_exc()[-800:])
            return
    if handle is None:
        status(state="GAVE_UP_NOT_RUN_RESOURCE_CONFLICT", attempts=400)
        return
    try:
        # ---------------- Stage A: alive submissions ----------------
        alive = cohort["members"]["ALIVE_EVIDENCED"]
        for i, m in enumerate(alive):
            c10 = m["cik"].replace("CIK", "").zfill(10)
            p = f"{ALIVE_CACHE}/CIK{c10}.json"
            if not os.path.exists(p):
                st, raw = get(f"https://data.sec.gov/submissions/CIK{c10}.json")
                if st != 200:
                    raise RuntimeError(f"CODE stageA HTTP {st} for {c10}")
                open(p, "wb").write(raw)
                time.sleep(0.35)
            if (i + 1) % 50 == 0:
                status(state="STAGE_A_FETCHING", fetched=i + 1, total=len(alive))
        status(state="STAGE_A_DONE", fetched=len(alive))

        # ---------------- Stage C: EODHD dividends + splits ----------------
        env = {}
        for line in open("/Users/hoangminhlong/my-quantitative/.env"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k2, v2 = line.split("=", 1)
                env[k2.strip()] = v2.strip()
        token = env.get("EODHD_API_KEY", "")
        assert token, "EODHD_API_KEY missing (never printed)"
        sym_map = []
        for m in members:
            t = m.get("ticker") or m.get("ticker_eodhd")
            if t:
                sym_map.append((m["cik"], t))
        for j, (cik, sym) in enumerate(sym_map):
            for kind, urlt, ddir in (("div", "div", EODHD_DIV), ("splits", "splits", EODHD_SPL)):
                p = f"{ddir}/{sym.replace('/', '_')}.json"
                if os.path.exists(p):
                    continue
                st, raw = get(f"https://eodhd.com/api/{urlt}/{sym}?api_token={token}&fmt=json",
                              headers={"User-Agent": "my-quantitative-research"})
                if st == 200:
                    open(p, "wb").write(raw)
                time.sleep(0.9)
            if (j + 1) % 50 == 0:
                status(state="STAGE_C_FETCHING", symbols=j + 1, total=len(sym_map))
        # ---------------- Stage B: Form-4 XML ingest ----------------
        refs, missing_sub = [], 0
        for m in members:
            c10 = m["cik"].replace("CIK", "").zfill(10)
            for src in (f"{ALIVE_CACHE}/CIK{c10}.json", f"{DEAD_CACHE}/CIK{c10}.json"):
                if os.path.exists(src):
                    refs += [{"cik": m["cik"], "cik10": c10, **r} for r in form4_refs_from_submissions(src, m["cik"])]
                    break
            else:
                missing_sub += 1
        status(state="STAGE_B_ENUM", in_window_form4_filings=len(refs), missing_submissions=missing_sub)
        seen_stream = set()
        if os.path.exists(STREAM):
            for line in open(STREAM):
                try:
                    r = json.loads(line)
                    seen_stream.add((r["cik"], r["accession"], r.get("transaction_date"), r.get("direction"), r.get("owner_cik"), r.get("owner_name")))
                except Exception:
                    pass
        done_docs = set()
        if os.path.exists(f"{XML_DIR}/.done"):
            done_docs = set(open(f"{XML_DIR}/.done").read().split())
        sf = open(STREAM, "a")
        df = open(f"{XML_DIR}/.defects.jsonl", "a")
        ndocs = 0
        consecutive_skips = 0
        t0 = time.time()
        for k, ref in enumerate(refs):
            key = f"{ref['cik']}|{ref['accession']}"
            if key in done_docs:
                continue
            cik_int = int(ref["cik"].replace("CIK", ""))
            acc = ref["accession"].replace("-", "")
            dname = resolve_raw_doc_name(cik_int, acc, ref.get("primary_doc"))
            optimistic = False
            if dname is None:
                try:
                    st2, raw2 = get_curl(f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/index.json")
                except TransientSkip as ts:
                    df.write(json.dumps({"accession": ref["accession"], "reason": f"TRANSIENT_SKIPPED_IDX:{ts}"}) + "\n")
                    consecutive_skips += 1
                    if consecutive_skips >= 50:
                        raise RuntimeError("SYSTEMIC: 50 consecutive transient skips - abort for inspection")
                    continue
                consecutive_skips = 0
                if st2 == 200:
                    names = [it["name"] for it in json.loads(raw2).get("directory", {}).get("item", [])]
                    cands = [n for n in names if n.lower().endswith(".xml") and not n.lower().startswith(("xsl", "primary_doc"))]
                    dname = cands[0] if cands else None
            if dname is None:
                df.write(json.dumps({"accession": ref["accession"], "reason": "RAW_DOC_UNRESOLVED"}) + "\n")
                done_docs.add(key)
                continue
            try:
                st, raw = get_curl(f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/{dname}", tries=5)
            except TransientSkip as ts:
                df.write(json.dumps({"accession": ref["accession"], "reason": f"TRANSIENT_SKIPPED:{ts}"}) + "\n")
                consecutive_skips += 1
                if consecutive_skips >= 50:
                    raise RuntimeError("SYSTEMIC: 50 consecutive transient skips - abort for inspection")
                continue
            consecutive_skips = 0
            if st == 404:
                df.write(json.dumps({"accession": ref["accession"], "reason": "RAW_DOC_UNRESOLVED_OR_404"}) + "\n")
                done_docs.add(key)
                continue
            if st != 200:
                raise RuntimeError(f"CODE stageB HTTP {st} {ref['accession']}")
            od = f"{XML_DIR}/{ref['cik']}/{acc}"
            os.makedirs(od, exist_ok=True)
            open(f"{od}/{dname}", "wb").write(raw)
            rows, defects = parse_form4_xml(raw, ref["cik"], ref["accession"], ref["acceptance"], ref["filing_date"])
            for r in rows:
                sig = (r["cik"], r["accession"], r["transaction_date"], r["direction"], r["owner_cik"], r["owner_name"])
                if sig not in seen_stream:
                    sf.write(json.dumps(r) + "\n")
                    seen_stream.add(sig)
            for d in defects:
                df.write(json.dumps(d) + "\n")
            done_docs.add(key)
            ndocs += 1
            if ndocs % 100 == 0:
                sf.flush(); df.flush()
                open(f"{XML_DIR}/.done", "w").write("\n".join(sorted(done_docs)))
                rate = ndocs / max(time.time() - t0, 1)
                status(state="STAGE_B_FETCHING", docs_done=ndocs, total=len(refs),
                       rate_per_s=round(rate, 2), eta_h=round((len(refs) - k) / max(rate, 0.01) / 3600, 2))
            _pace_on_ok()
            _pace_sleep()
        sf.close(); df.close()
        open(f"{XML_DIR}/.done", "w").write("\n".join(sorted(done_docs)))
        status(state="STAGE_B_DONE", docs=len(done_docs), filings=len(refs))

        status(state="ALL_DONE", symbols=len(sym_map))
        handle.release(status="FINISHED", note=f"bulk ingest done: A submissions x{len(alive)}, B xml x{ndocs}, C symbols x{len(sym_map)}")
        print("ALL_DONE")
    except Exception:
        err = traceback.format_exc()
        status(state="FAILED", stderr=err[-1500:])
        try:
            handle.release(status="FAILED", note=("stderr tail: " + err.strip().splitlines()[-1][:300]))
        except Exception:
            pass
        raise

if __name__ == "__main__":
    main()
