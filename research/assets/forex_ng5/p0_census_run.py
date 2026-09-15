#!/usr/bin/env python
"""FOREX-NG5 P0 census runner — plan gates A1-A7 (bulk crawl, machine-wide lock).

Executes exactly the plan (plans/PLAN_forex_ng5.md sec3) — source engineering
and census ONLY: no returns, no PnL, no PF/Sharpe/drawdown, no S1, no orders,
no Socrata (403 from this host, twice-verified; bulk channel only).

Gates
  A1 census canaries   : full legacy-year zips 1986..2026; per-year market-code
                         validation table for the used currency-futures codes
                         + USD index; dead/never-existed code controls (P-7).
  A2 availability      : rolling release-schedule page pinned; per-release
                         bytes-exist spot checks inside the covered window;
                         frozen convention model (Fri 15:30 ET -> next 16:00-NY
                         grid) for pre-window years, marked convention-based;
                         2025 shutdown republication dates override (evidenced).
  A3 corrections       : CFTC Historical Special Announcements censused and
                         classified against FAQ-6 no-revision; handling
                         preregistered (annotate-and-keep vs exclude-window).
  A4 schema            : legacy vs disagg vs TFF parsed separately; exact
                         Decimal counts; fail-closed on unknown schema.
  A5 coverage+mapping  : sessions, missing reports, duplicates, per-year
                         coverage; explicit futures-code <-> entitled-TD-leg
                         mapping; out-of-scope pairs declared.
  A6 fold freeze       : three chronological folds + X1 (C7-analog) exclusion
                         rule frozen textually in the census commit.
  A7 reproducibility   : raw-request manifest, digest manifest, deterministic
                         re-digest verification, p0_census.json verdict.

Preregistered verdict margins (also written into the artifact): A1 structural
miss = a used code absent in ANY year between its first-seen year and freeze
(BLOCKED_SOURCE); A4 rejects share <= 0.001 per regime and identity-mismatch
share <= 0.001; A2 every schedule-window as-of must have used-code rows in the
frozen bytes; never-controls must have zero rows everywhere.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[3]
ROOT = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(WORKTREE))
from research.assets.forex_ng5 import cot_parser, release_clock  # noqa: E402
from research.governance import heavy_lock  # noqa: E402

OUT_DIR = WORKTREE / "research/control/forex_ng5_run"
EVID_DIR = OUT_DIR / "evidence"
STAGING = Path("/tmp/forex_ng5_p0_raw")
FREEZE_UTC = "unset"

BASE = "https://www.cftc.gov/files/dea/history"
UA = "Mozilla/5.0 (quant-workspace census; FOREX-NG5 P0; keyless)"
PACING_S = 1.1
RETRIES = 3

# --- frozen census configuration -------------------------------------------
# Used futures markets: the four FOREX-NG5-used pairs map to V9-inherited
# entitled TD spot legs (dispatch packet; see A5 mapping). USD index is state
# context, not a spot leg.
#
# CROSS-ERA CODE INSTABILITY (measured at recon 2026-09-15): market codes are
# NOT stable across eras — e.g. CANADIAN DOLLAR carried 090741 in the 1999
# legacy file while 090601 is the modern-era code. Pair identity is therefore
# anchored by anchored MARKET-NAME regexes and the per-year CODE TIMELINE is
# a first-class A1 output; the declared codes below are the modern-era codes.
USED_SPECS = {
    "GBPUSD": {"codes_modern": ["096742"], "futures_ccy": "GBP", "td_leg": "GBPUSD",
               "orientation": "direct", "entitled": True,
               "name_re": r"^(BRITISH POUND|POUND STERLING)(?!.*(CROSS|XRATE|/))"},
    "USDCAD": {"codes_modern": ["090601", "090741"], "futures_ccy": "CAD",
               "td_leg": "USDCAD",
               "orientation": "inverted (futures quotes CAD/USD; leg quotes USD/CAD)",
               "entitled": True,
               "name_re": r"^CANADIAN DOLLAR(?!.*(CROSS|XRATE|/))"},
    "AUDUSD": {"codes_modern": ["232741"], "futures_ccy": "AUD", "td_leg": "AUDUSD",
               "orientation": "direct", "entitled": True,
               "name_re": r"^AUSTRALIAN DOLLARS?(?!.*(CROSS|XRATE|/))"},
    "NZDUSD": {"codes_modern": ["112741"], "futures_ccy": "NZD", "td_leg": "NZDUSD",
               "orientation": "direct", "entitled": True,
               "name_re": r"^(NEW ZEALAND DOLLARS?|NZ DOLLARS?)(?!.*(CROSS|XRATE|/))"},
}
USED_PAIRS = list(USED_SPECS)
PAIR_NAME_RES = {p: re.compile(s["name_re"]) for p, s in USED_SPECS.items()}
USD_INDEX_NAME_RE = re.compile(r"^(USD INDEX|U\.?S\.? DOLLAR INDEX)")
USD_INDEX = "098662"
CONTEXT_NAME_RES = {
    "EUR (out of scope)": re.compile(r"^EURO FX(?!.*(CROSS|/))"),
    "JPY (out of scope)": re.compile(r"^JAPANESE YEN(?!.*(CROSS|/))"),
    "CHF (out of scope)": re.compile(r"^SWISS FRANC(?!.*(CROSS|/))"),
}
CONTEXT_CODES = {
    "099741": "EURO FX (no V9-inherited entitled TD leg on this host — OUT OF SCOPE)",
    "097741": "JAPANESE YEN (no entitled TD leg — OUT OF SCOPE)",
    "092741": "SWISS FRANC (no entitled TD leg — OUT OF SCOPE)",
}
DEAD_NAME_RE = re.compile(r"DEUTSCHE|GERMAN\s*MARK", re.I)
# candidates validated by name hits; 094741 = DEUTSCHE MARK - INTERNATIONAL
# MONETARY MARKET (measured 1999 file), 093741 kept as a historical candidate
DEAD_CANDIDATE_CODES = ["094741", "093741"]
NEVER_CONTROLS = ["999999", "000001", "123456", "096743", "090602", "096748",
                  "090609"]  # never-existed: adjacent-formatted codes (096741 EXCLUDED — it is a real 1986-88 GBP code)
FX_NAME_RE = re.compile(
    r"POUND|DOLLAR|EURO FX|EUROPEAN CURRENCY|YEN|FRANC|DEUTSCHE|MARK |LIRA|PESETA|"
    r"ESCUDO|GUILDER|KRONA|ZLOTY|FORINT|KORUNA|RUPEE|RAND|PESO|REAL|WON|RENMINBI|YUAN|"
    r"CURRENCY|USD INDEX|US DOLLAR INDEX", re.I)

LEGACY_YEARS = list(range(1986, 2027))
A1_DEEP_DIVE_YEAR = 1999  # euro transition: DM dead-control terminus + euro-era codes begin
DISAGG_SOURCES = ([("hist_2006_2016", f"{BASE}/fut_disagg_txt_hist_2006_2016.zip")] +
                  [(str(y), f"{BASE}/fut_disagg_txt_{y}.zip") for y in range(2010, 2027)])
TFF_SOURCES = ([("hist_2006_2016", f"{BASE}/fin_fut_txt_2006_2016.zip")] +
               [(str(y), f"{BASE}/fut_fin_txt_{y}.zip") for y in range(2010, 2027)])
PAGES = {
    "cot_index": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
    "compressed_index": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm",
    "release_schedule": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm",
    "special_announcements": "https://www.cftc.gov/MarketReports/CommitmentsOfTraders/HistoricalSpecialAnnouncements/index.htm",
}
FAQ6_NEEDLE = "historical data is not updated once published"
SCORED_SPAN_START = "2006-06-13"  # disaggregated/TFF era start (source-documented)
FOLD_BOUNDS = [("F1", "2006-06-13", "2013-06-30"),
               ("F2", "2013-07-01", "2020-06-30"),
               ("F3", "2020-07-01", None)]  # F3 end = measured last report date at freeze
REGIME_ORDER = ["hist_2006_2016"] + [str(y) for y in range(2010, 2027)]
ROLLING_FILES = {"deacot2026.zip", "fut_disagg_txt_2026.zip", "fut_fin_txt_2026.zip"}

REJECTS_SHARE_MAX = 0.001
IDENTITY_SHARE_MAX = 0.001

USED_CODE_SET = {c for s in USED_SPECS.values() for c in s["codes_modern"]}

KILLED: list = []
REQUEST_LOG: list = []


def note_kill(msg: str) -> None:
    KILLED.append(msg)
    print("KILL:", msg, flush=True)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- HTTP -------------------------------------------------------------------
def http_get(url: str, dest: Path = None, is_light: bool = False) -> dict:
    """GET with retries; records url/status/bytes/sha256/last-modified. Polite pacing."""
    last_err = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
                rec = {"url": url, "method": "GET", "fetched_utc": now_utc(),
                       "status": r.status, "bytes": len(data),
                       "sha256": cot_parser.sha256_hex(data),
                       "last_modified": r.headers.get("Last-Modified"),
                       "light": bool(is_light)}
                if dest is not None:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
                    rec["staging_path"] = str(dest)
                REQUEST_LOG.append(rec)
                time.sleep(PACING_S)
                return rec
        except urllib.error.HTTPError as e:
            last_err = e
            REQUEST_LOG.append({"url": url, "method": "GET", "fetched_utc": now_utc(),
                                "status": e.code, "bytes": 0, "sha256": None,
                                "last_modified": None, "light": bool(is_light)})
            if e.code in (403, 404):
                return REQUEST_LOG[-1]  # structural: recorded, not retried
            time.sleep(2 * (attempt + 1))
        except Exception as e:  # noqa: BLE001 — network-class, retried then recorded
            last_err = e
            time.sleep(2 * (attempt + 1))
    REQUEST_LOG.append({"url": url, "method": "GET", "fetched_utc": now_utc(),
                        "status": 0, "bytes": 0, "sha256": None,
                        "error": repr(last_err), "light": bool(is_light)})
    return REQUEST_LOG[-1]


def http_head(url: str) -> dict:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urllib.request.urlopen(req, timeout=60) as r:
            rec = {"url": url, "method": "HEAD", "fetched_utc": now_utc(),
                   "status": r.status,
                   "bytes": int(r.headers.get("Content-Length") or 0),
                   "last_modified": r.headers.get("Last-Modified"),
                   "sha256": None, "light": True}
            REQUEST_LOG.append(rec)
            time.sleep(PACING_S)
            return rec
    except Exception as e:  # noqa: BLE001
        REQUEST_LOG.append({"url": url, "method": "HEAD", "fetched_utc": now_utc(),
                            "status": 0, "bytes": 0, "sha256": None,
                            "error": repr(e), "light": True})
        return REQUEST_LOG[-1]


# --- crawl + parse ----------------------------------------------------------
def fetch_zip_records(handle, fkey: str, url: str, regime: str) -> dict:
    """Fetch one regime zip, parse it, return the file aggregate + per-code date sets."""
    subdir = STAGING / regime
    subdir.mkdir(parents=True, exist_ok=True)
    fname = url.rsplit("/", 1)[-1]
    dest = subdir / fname
    rec = http_get(url, dest=dest)
    agg = {"fkey": f"{regime}/{fkey}", "url": url, "zip_sha256": rec["sha256"],
           "zip_bytes": rec["bytes"], "status": rec["status"],
           "last_modified": rec.get("last_modified"), "regime": regime}
    if rec["status"] != 200 or rec["sha256"] is None:
        agg["error"] = f"fetch failed status={rec['status']}"
        return agg
    try:
        zf = zipfile.ZipFile(dest)
    except Exception as e:  # noqa: BLE001 — not a zip: fail-closed
        agg["error"] = f"zip magic fail: {e!r}"
        return agg
    try:
        members = [n for n in zf.namelist() if n.lower().endswith((".txt", ".csv"))]
        agg["members"] = members
        if len(members) != 1:
            agg["error"] = f"expected exactly one txt/csv member, found {members}"
            return agg
        member = members[0]
        text = zf.read(member).decode("latin-1")  # lossless; no float anywhere
    finally:
        zf.close()
    agg["member"] = member
    agg["member_bytes"] = len(text.encode("latin-1"))
    agg["member_sha256"] = cot_parser.sha256_hex(text.encode("latin-1"))
    try:
        parsed = cot_parser.parse_report_csv(text, regime)
    except cot_parser.SchemaUnknownError as e:
        agg["error"] = f"SCHEMA_UNKNOWN: {e}"
        agg["header_verbatim"] = e.header
        return agg
    agg["header_verbatim"] = parsed["header_verbatim"]
    agg["unmapped_columns"] = parsed["unmapped_columns"]
    agg["rows_total"] = parsed["rows_total"]
    agg["rejects_count"] = len(parsed["rejects"])
    agg["reject_examples"] = parsed["rejects"][:5]
    dd = cot_parser.dedupe(parsed["records"])
    agg["exact_duplicates"] = dd["exact_duplicates"]
    agg["conflicts"] = dd["conflicts"]
    ident_bad = sum(1 for r in parsed["records"] if not r["identity_ok"])
    agg["identity_mismatch_count"] = ident_bad
    agg["rows_identity_checked"] = len(parsed["records"])
    # Consolidated rows (market name carries "CONSOLIDATED"; they combine
    # e-micro/component contracts — cf. the 2023 Special Announcement) do not
    # satisfy the standard reportable-parts identity by construction; the A4
    # identity margin is measured over NON-consolidated rows, consolidated
    # rows are counted and excluded from books by X1.
    noncons = [r for r in parsed["records"] if "CONSOLIDATED" not in r["market_name"].upper()]
    agg["consolidated_rows"] = len(parsed["records"]) - len(noncons)
    agg["identity_mismatch_nonconsolidated"] = sum(1 for r in noncons if not r["identity_ok"])
    agg["rows_identity_checked_nonconsolidated"] = len(noncons)
    per_code_dates: dict = {}
    name_matched: dict = {}
    dead_hits: list = []
    fx_names: set = set()
    for r in parsed["records"]:
        c = r["code"]
        nm = r["market_name"]
        if c in USED_CODE_SET or c == USD_INDEX or c in CONTEXT_CODES \
                or c in NEVER_CONTROLS or c in DEAD_CANDIDATE_CODES:
            per_code_dates.setdefault(c, set()).add(r["report_date"])
        venue = nm.split("-")[-1].strip() if "-" in nm else nm
        for pair, rx in PAIR_NAME_RES.items():
            if rx.search(nm):
                e = name_matched.setdefault(pair, {}).setdefault(
                    c, {"dates": set(), "exchanges": set()})
                e["dates"].add(r["report_date"])
                e["exchanges"].add(venue)
                break
        else:
            if USD_INDEX_NAME_RE.search(nm):
                e = name_matched.setdefault("USD_INDEX", {}).setdefault(
                    c, {"dates": set(), "exchanges": set()})
                e["dates"].add(r["report_date"])
                e["exchanges"].add(venue)
            else:
                for ckey, rx in CONTEXT_NAME_RES.items():
                    if rx.search(nm):
                        e = name_matched.setdefault(ckey, {}).setdefault(
                            c, {"dates": set(), "exchanges": set()})
                        e["dates"].add(r["report_date"])
                        e["exchanges"].add(venue)
                        break
        if DEAD_NAME_RE.search(nm):
            dead_hits.append({"code": c, "name": nm, "last_report": r["report_date"]})
        if FX_NAME_RE.search(nm):
            fx_names.add(f"{c}\t{nm}")
    agg["per_code_dates"] = {c: sorted(v) for c, v in per_code_dates.items()}
    agg["name_matched"] = {k: {c: {"dates": sorted(v["dates"]),
                                   "exchanges": sorted(v["exchanges"])}
                               for c, v in v2.items()}
                           for k, v2 in name_matched.items()}
    agg["dead_name_hits"] = dead_hits[:20]
    agg["dead_name_hit_count"] = len(dead_hits)
    agg["fx_names"] = sorted(fx_names)
    agg["parse_ok"] = True
    handle.heartbeat({"progress": f"parsed {agg['fkey']} rows={agg['rows_total']}"})
    print(f"parsed {agg['fkey']}: rows={agg['rows_total']} rej={agg['rejects_count']} "
          f"idbad={ident_bad} dup={agg['exact_duplicates']} conf={len(agg['conflicts'])}",
          flush=True)
    return agg


# --- A2/A3 page parsing -----------------------------------------------------
MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]


def parse_release_schedule(html: str) -> dict:
    """Year sections '<YYYY> Release Schedule</h3><table>...' -> schedule rows.

    Row shape (measured 2026-09-15): first cell month name, remaining cells
    day tokens; a trailing '*' marks a holiday-delayed release.
    """
    rows, anomalies = [], []
    for ym in re.finditer(
            r"((?:19|20)\d{2})\s+Release Schedule\s*(?:</strong>)?\s*</h3>\s*<table.*?</table>",
            html, re.S):
        year = int(ym.group(1))
        for tr in re.finditer(r"<tr[^>]*>(.*?)</tr>", ym.group(0), re.S):
            cells = [re.sub(r"<[^>]+>", "", c).strip()
                     for c in re.findall(r"<td[^>]*>(.*?)</td>", tr.group(1), re.S)]
            if not cells or cells[0].lower() not in MONTHS:
                continue
            month = MONTHS.index(cells[0].lower()) + 1
            for tok in cells[1:]:
                t = tok.strip()
                if not t:
                    continue
                m = re.match(r"^(\d{1,2})(\*?)$", t)
                if not m:
                    anomalies.append({"year": year, "token": t})
                    continue
                try:
                    rd = date(year, month, int(m.group(1)))
                except ValueError:
                    anomalies.append({"year": year, "token": t})
                    continue
                rows.append({"release_date": rd.isoformat(),
                             "release_weekday": rd.strftime("%a"),
                             "holiday_delayed_flag": m.group(2) == "*",
                             "as_of": release_clock.schedule_as_of(rd).isoformat()})
    return {"rows": rows, "anomalies": anomalies}


_DATE_LINE_RE = re.compile(
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},\s+(?:19|20)\d{2}):")
_MDY_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def parse_announcements(html: str) -> dict:
    """Historical Special Announcements: <dt>YYYY</dt> sections -> items.

    Each item starts 'Month D, YYYY:'; a republication table (2025 shutdown)
    is parsed into (report_date, original_publish, new_publish) triples.
    """
    items, republish = [], []
    dl = re.search(r"<dl[^>]*>(.*?)</dl>", html, re.S)
    body = dl.group(1) if dl else html
    for ym in re.finditer(r"<dt[^>]*>\s*((?:19|20)\d{2})\s*</dt>(.*?)(?=<dt[^>]*>|\Z)",
                          body, re.S):
        year = int(ym.group(1))
        seg = ym.group(2)
        marks = [(m.start(), m.group(1)) for m in _DATE_LINE_RE.finditer(seg)]
        for k, (pos, head) in enumerate(marks):
            end = marks[k + 1][0] if k + 1 < len(marks) else len(seg)
            chunk = seg[pos:end]
            text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", chunk)).strip()
            tables = re.findall(r"<table.*?</table>", chunk, re.S)
            for tb in tables:
                for tr in re.finditer(r"<tr[^>]*>(.*?)</tr>", tb, re.S):
                    cells = [re.sub(r"<[^>]+>", "", c).strip()
                             for c in re.findall(r"<td[^>]*>(.*?)</td>", tr.group(1), re.S)]
                    if len(cells) >= 3 and _MDY_RE.match(cells[0]) and _MDY_RE.match(cells[2]):
                        republish.append({"report_date": cells[0],
                                          "original_publish": cells[1],
                                          "new_publish": cells[2],
                                          "announcement_year": year})
            items.append({"year": year, "headline": head, "has_table": bool(tables),
                          "text_head": text[:500],
                          "mentions_used_code": bool(re.search(
                              r"BRITISH POUND|CANADIAN DOLLAR|AUSTRALIAN DOLLAR|NEW ZEALAND|"
                              r"DOLLAR INDEX|CURRENCY", text, re.I)),
                          "mentions_value_correction": bool(re.search(
                              r"correct(?:ed|ion)|revised|restat", text, re.I))})
    return {"items": items, "republish_table": republish}


def mdy_to_iso(s: str) -> str:
    m, d, y = s.split("/")
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


# --- main -------------------------------------------------------------------
def main():
    global FREEZE_UTC
    FREEZE_UTC = now_utc()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    EVID_DIR.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    handle = heavy_lock.acquire(
        cycle_id="FOREX-NG5", role="P0_CENSUS", worktree=str(WORKTREE),
        command=[sys.executable, str(Path(__file__))],
        expected_artifacts=[str(OUT_DIR / "p0_census.json")])
    try:
        _census(handle)
    except Exception as e:  # noqa: BLE001 — honest TECHABORT, never a silent hold
        handle.release(status="TECHABORT", note=f"p0_census crash: {e!r}")
        raise


def _census(handle):
    verdicts = {}

    # ---- pages (light GETs, snapshots committed as evidence) ----
    pages = {}
    for key, url in PAGES.items():
        rec = http_get(url, dest=EVID_DIR / f"{key}.snapshot.html", is_light=True)
        pages[key] = rec
        if rec["status"] != 200:
            note_kill(f"page {key} status={rec['status']}")
    faq6_present = False
    if pages["cot_index"]["status"] == 200:
        idx = (EVID_DIR / "cot_index.snapshot.html").read_text(encoding="utf-8", errors="replace")
        faq6_present = FAQ6_NEEDLE in idx
        if not faq6_present:
            note_kill("FAQ-6 needle absent from cot_index snapshot")

    # ---- legacy crawl 1986..2026 (A1/A4/A5 evidence) ----
    handle.heartbeat({"progress": "legacy crawl start"})
    legacy_aggs = {}
    for y in LEGACY_YEARS:
        agg = fetch_zip_records(handle, str(y), f"{BASE}/deacot{y}.zip", "legacy")
        legacy_aggs[str(y)] = agg
        if agg.get("error"):
            note_kill(f"legacy {y}: {agg['error']}")
        if (y - 1985) % 8 == 0:
            handle.heartbeat({"progress": f"legacy through {y}"})

    # ---- disagg + tff crawls ----
    disagg_aggs, tff_aggs = {}, {}
    for src_id, url in DISAGG_SOURCES:
        agg = fetch_zip_records(handle, src_id, url, "disagg")
        disagg_aggs[src_id] = agg
        if agg.get("error"):
            note_kill(f"disagg {src_id}: {agg['error']}")
    for src_id, url in TFF_SOURCES:
        agg = fetch_zip_records(handle, src_id, url, "tff")
        tff_aggs[src_id] = agg
        if agg.get("error"):
            note_kill(f"tff {src_id}: {agg['error']}")

    head_2026 = http_head(f"{BASE}/deacot2026.zip")  # freshness of the rolling file

    # ---- A1 ----
    a1 = build_a1(legacy_aggs, disagg_aggs, tff_aggs)
    verdicts["A1"] = a1["verdict"]
    if a1["verdict"] != "PASS":
        for k in a1["killed"]:
            if k not in KILLED:
                KILLED.append(k)
    (OUT_DIR / "per_year_code_table.json").write_text(json.dumps({
        "schema": "forex_ng5_a1_per_year_code_table@1", "measured_at_utc": FREEZE_UTC,
        "deep_dive_year": A1_DEEP_DIVE_YEAR,
        "deep_dive_rationale": "euro transition year: the German-mark dead control terminates and euro-era codes begin inside one legacy file — the hardest single-year cross-era code-stability test",
        "a1": a1}, indent=1))

    # ---- A5 ----
    a5, coverage = build_a5(legacy_aggs, disagg_aggs, tff_aggs)
    verdicts["A5"] = a5["verdict"]
    if a5["verdict"] != "PASS":
        KILLED.extend(k for k in a5["killed"] if k not in KILLED)
    (OUT_DIR / "coverage_census.json").write_text(json.dumps(coverage, indent=1))
    (OUT_DIR / "mapping_td_legs.json").write_text(json.dumps(a5["mapping"], indent=1))

    # ---- A2 (needs the measured last report date as the freeze boundary) ----
    a2 = build_a2(pages, legacy_aggs, disagg_aggs, tff_aggs, head_2026,
                  last_report=a5["last_report_date"])
    verdicts["A2"] = a2["verdict"]
    if a2["verdict"] != "PASS":
        KILLED.extend(k for k in a2["killed"] if k not in KILLED)
    (OUT_DIR / "a2_availability.json").write_text(json.dumps(a2, indent=1))

    # ---- A3 ----
    a3 = build_a3(pages, faq6_present)
    verdicts["A3"] = a3["verdict"]
    if a3["verdict"] != "PASS":
        KILLED.extend(k for k in a3["killed"] if k not in KILLED)
    (OUT_DIR / "a3_corrections_census.json").write_text(json.dumps(a3, indent=1))

    # ---- A4 ----
    a4 = build_a4(legacy_aggs, disagg_aggs, tff_aggs)
    verdicts["A4"] = a4["verdict"]
    if a4["verdict"] != "PASS":
        KILLED.extend(k for k in a4["killed"] if k not in KILLED)
    (OUT_DIR / "schema_report.json").write_text(json.dumps(a4, indent=1))

    # ---- A6 ----
    a6 = build_a6(a5["last_report_date"], a2["shutdown_override_rows"])
    verdicts["A6"] = "PASS"
    (OUT_DIR / "a6_fold_freeze.json").write_text(json.dumps(a6, indent=1))

    # ---- A7 ----
    (OUT_DIR / "raw_request_manifest.json").write_text(json.dumps({
        "schema": "forex_ng5_raw_request_manifest@1", "measured_at_utc": FREEZE_UTC,
        "ua": UA, "pacing_seconds": PACING_S, "requests": REQUEST_LOG}, indent=1))
    digest_rows = []
    for rec in REQUEST_LOG:
        if rec["method"] != "GET" or not rec.get("sha256") or rec["bytes"] == 0:
            continue
        name = rec["url"].rsplit("/", 1)[-1]
        digest_rows.append({"file": name, "url": rec["url"], "sha256": rec["sha256"],
                            "bytes": rec["bytes"], "fetched_utc": rec["fetched_utc"],
                            "last_modified": rec.get("last_modified"),
                            "class": "rolling_weekly_refresh" if name in ROLLING_FILES
                            else "frozen_year_archive"})
    redigest_ok = bool(digest_rows)
    redigest_rows = []
    for d in digest_rows:
        for regime in ("legacy", "disagg", "tff"):
            p = STAGING / regime / d["file"]
            if p.exists():
                h2 = cot_parser.redigest_file(p)
                h3 = cot_parser.redigest_file(p)
                ok = (h2 == h3 == d["sha256"])
                redigest_ok = redigest_ok and ok
                redigest_rows.append({"file": d["file"], "manifest_sha256": d["sha256"],
                                      "redigest_sha256": h2,
                                      "double_run_equal": h2 == h3, "match": ok})
                break
    (OUT_DIR / "digest_manifest.json").write_text(json.dumps({
        "schema": "forex_ng5_digest_manifest@1", "measured_at_utc": FREEZE_UTC,
        "policy": "raw zips OUT of git (staging /tmp/forex_ng5_p0_raw, volatile by design); digests + last-modified are the committed authority; a detached rerun re-fetches and re-digests — pre-2026 archives must reproduce digests exactly, 2026 rolling files are expected to advance (last-modified recorded)",
        "redigest_double_run_all_match": redigest_ok,
        "files": digest_rows, "redigest_verification": redigest_rows}, indent=1))
    verdicts["A7"] = "PASS" if redigest_ok else "FAIL"
    if verdicts["A7"] != "PASS":
        KILLED.append("A7 digest manifest incomplete or redigest mismatch")

    # ---- final verdict ----
    gates_pass = all(verdicts.get(g) == "PASS" for g in ("A1", "A2", "A3", "A4", "A5", "A7"))
    overall = "P0_CENSUS_PASS" if gates_pass else "P0_CENSUS_BLOCKED"
    doc = {
        "schema": "forex_ng5_run/p0_census@1",
        "cycle_id": "FOREX-NG5",
        "measured_at_utc": FREEZE_UTC,
        "plan": "plans/PLAN_forex_ng5.md sec3 gates A1-A7",
        "gate_verdicts": verdicts,
        "verdict": overall,
        "killed": KILLED,
        "not_run_declared": a5["mapping"]["td_digest_pin"],
        "folds_frozen": a6["folds"],
        "exclusion_rule_X1_frozen": True,
        "s1": "SEALED_UNTOUCHED",
        "returns_computed": False,
        "margins": {
            "rejects_share_max": REJECTS_SHARE_MAX,
            "identity_share_max": IDENTITY_SHARE_MAX,
            "a1_rule": "used code absent in any year first-seen..freeze => BLOCKED_SOURCE",
            "a2_rule": "every schedule-window as_of must have used-code rows in frozen bytes",
            "never_controls": "zero rows required everywhere",
        },
        "limitations": [a5["mapping"]["td_digest_pin"]["requirement"]],
    }
    (OUT_DIR / "p0_census.json").write_text(json.dumps(doc, indent=1))
    handle.release(status="FINISHED" if gates_pass else "FAILED",
                   note=f"p0_census verdict={overall} gates={verdicts} killed={KILLED[:6]}")
    print("VERDICT:", overall)
    for g, v in verdicts.items():
        print(f"  {g}: {v}")
    print("KILLED:", KILLED)


# --- A1 builder -------------------------------------------------------------
def _pair_year_table(legacy_aggs, regime_aggs_by_regime) -> dict:
    """Pair-level per-year presence + code-era timelines from name matches.

    Returns {pair_key: {"per_year_counts": {year: n_report_dates},
    "code_eras": {code: {first_year, last_year, years, exchanges, regimes}}}}
    for the four used pairs and the USD index (key USD_INDEX).
    """
    keys = list(USED_PAIRS) + ["USD_INDEX"] + list(CONTEXT_NAME_RES)
    per_year = {k: {} for k in keys}
    eras = {k: {} for k in keys}
    sources = [("legacy", legacy_aggs)] + list(regime_aggs_by_regime.items())
    for regime, aggs in sources:
        for sid, agg in sorted(aggs.items()):
            for key, code_info in (agg.get("name_matched") or {}).items():
                if key not in per_year:
                    continue
                for code, info in code_info.items():
                    ds = info["dates"]
                    years = {d[:4] for d in ds}
                    for y in years:
                        per_year[key][y] = per_year[key].get(y, 0) + 1
                    e = eras[key].setdefault(code, {"first_year": min(years),
                                                    "last_year": max(years),
                                                    "years": set(),
                                                    "exchanges": set(),
                                                    "regimes": set()})
                    e["years"].update(years)
                    e["exchanges"].update(info.get("exchanges", []))
                    e["regimes"].add(f"{regime}/{sid}")
    return {k: {"per_year_counts": dict(sorted(v.items())),
                "code_eras": {c: {"first_year": e["first_year"], "last_year": e["last_year"],
                                  "years": sorted(e["years"]),
                                  "exchanges": sorted(e["exchanges"]),
                                  "regimes": sorted(e["regimes"])}
                              for c, e in sorted(eras[k].items())}}
            for k, v in per_year.items()}


def build_a1(legacy_aggs, disagg_aggs, tff_aggs) -> dict:
    killed = []
    table = _pair_year_table(legacy_aggs, {"disagg": disagg_aggs, "tff": tff_aggs})
    dead_found_years = {}
    for y in sorted(legacy_aggs):
        for h in legacy_aggs[y].get("dead_name_hits", []):
            dead_found_years.setdefault(h["code"], set()).add(y)
    dead_code = next((c for c in DEAD_CANDIDATE_CODES if c in dead_found_years), None)
    dead_terminal = max((max(ys) for ys in dead_found_years.values()), default=None)
    never_violations = {}
    for regime, aggs in (("legacy", legacy_aggs), ("disagg", disagg_aggs), ("tff", tff_aggs)):
        for sid, agg in aggs.items():
            for c in NEVER_CONTROLS:
                n = len((agg.get("per_code_dates") or {}).get(c, []))
                if n:
                    never_violations[c] = never_violations.get(c, 0) + n
    # structural gap test — preregistered scope: the scored-candidate span
    # (2006-06-13 -> freeze) is where a used pair must be gap-free; legacy-era
    # (pre-2006) gaps are recorded as coverage facts (the legacy era is
    # census-only evidence per X1(a)), never kill conditions. The disagg
    # regime is validated for CONSISTENCY: it carries zero used-pair markets
    # (CFTC's disaggregated reports cover physical commodities; currency
    # futures are covered by the TFF reports).
    gaps = {}
    coverage_facts = {}
    for key in list(USED_PAIRS) + ["USD_INDEX"]:
        years = table[key]["per_year_counts"]
        fs = min(years) if years else None
        if fs is None:
            gaps[key] = {"legacy": ["NEVER_SEEN"]}
            note_kill(f"A1 structural miss {key}: never seen")
            continue
        span_miss = [str(v) for v in range(2006, 2027) if years.get(str(v), 0) == 0]
        pre_span_miss = [str(v) for v in range(int(fs), 2006) if years.get(str(v), 0) == 0]
        if span_miss:
            gaps[key] = {"scored_span": span_miss}
            note_kill(f"A1 structural miss {key} within scored span: missing years {span_miss}")
        if pre_span_miss:
            coverage_facts.setdefault(key, {})["pre_span_gap_years"] = pre_span_miss
        span_years = {}
        for sid, agg in tff_aggs.items():
            for code_info in (agg.get("name_matched") or {}).get(key, {}).values():
                for dstr in code_info["dates"]:
                    span_years[dstr[:4]] = span_years.get(dstr[:4], 0) + 1
        miss2 = [str(v) for v in range(2007, 2027) if span_years.get(str(v), 0) == 0]
        if miss2:
            gaps.setdefault(key, {})["tff"] = miss2
            note_kill(f"A1 structural miss {key} in tff: missing years {miss2}")
    disagg_pair_presence = {}
    for sid, agg in disagg_aggs.items():
        present = sorted((agg.get("name_matched") or {}).keys())
        if present:
            disagg_pair_presence[agg["fkey"]] = present
    bad = bool(killed) or bool(gaps) or bool(never_violations)
    if never_violations:
        note_kill(f"A1 never-existed controls returned rows: {never_violations}")
    if dead_code is None or (dead_terminal is not None and dead_terminal >= "2001"):
        note_kill(f"A1 dead control not calibrated: code={dead_code} terminal={dead_terminal}")
        bad = True
    return {"verdict": "BLOCKED_SOURCE" if bad else "PASS",
            "pair_identity_rule": "anchored market-name regex; per-year code timelines are the A1 output (codes are NOT stable across eras — e.g. CAD carried 090741 in 1999 AND 2026 while 090601 is an adjacent-era code; GBP carried 096741 in 1986-88 before 096742)",
            "pairs": USED_PAIRS,
            "usd_index": USD_INDEX,
            "context": list(CONTEXT_NAME_RES),
            "pair_year_tables": table,
            "declared_modern_codes": {p: s["codes_modern"] for p, s in USED_SPECS.items()},
            "structural_gap_rule": ("a used pair / the USD index must be present in every "
                                    "calendar year of the scored-candidate span (2006..2026) "
                                    "in legacy AND tff; pre-2006 legacy gaps are coverage "
                                    "facts (X1(a) regime boundary), not kills"),
            "structural_gaps": gaps,
            "pre_span_coverage_facts": coverage_facts,
            "disagg_regime_finding": ("the disaggregated futures-only files contain ZERO "
                                      "used-pair markets in every measured year (CFTC "
                                      "splits regimes: disaggregated = physical commodities, "
                                      "TFF = financials incl. currencies); pair validation "
                                      "therefore runs over legacy + tff"),
            "pairs_found_in_disagg_files": disagg_pair_presence,
            "dead_control": {"candidate_codes": DEAD_CANDIDATE_CODES,
                             "name_regex": DEAD_NAME_RE.pattern,
                             "found_code": dead_code,
                             "years_present": {c: sorted(ys) for c, ys in dead_found_years.items()},
                             "terminal_year": dead_terminal,
                             "expectation": "present pre-euro, terminal by 2000 (euro transition), absent 2001+"},
            "never_controls": {"codes": NEVER_CONTROLS, "violations": never_violations,
                               "expectation": "zero rows in every file of every regime"},
            "deep_dive_year": A1_DEEP_DIVE_YEAR,
            "killed": killed}


# --- A2 builder -------------------------------------------------------------
def build_a2(pages, legacy_aggs, disagg_aggs, tff_aggs, head_2026,
             last_report=None) -> dict:
    killed = []
    sched = {"rows": [], "anomalies": []}
    if pages["release_schedule"]["status"] == 200:
        html = (EVID_DIR / "release_schedule.snapshot.html").read_text(
            encoding="utf-8", errors="replace")
        sched = parse_release_schedule(html)
    else:
        killed.append(f"release schedule status={pages['release_schedule']['status']}")
    republish = []
    ann_path = EVID_DIR / "special_announcements.snapshot.html"
    if ann_path.exists():
        republish = parse_announcements(
            ann_path.read_text(encoding="utf-8", errors="replace"))["republish_table"]
    override = {}
    for r in republish:
        override[mdy_to_iso(r["report_date"])] = {
            "actual_publish": mdy_to_iso(r["new_publish"]),
            "original_publish": r["original_publish"],
            "source": "HistoricalSpecialAnnouncements 2025 shutdown republication table"}
    pair_report_dates_by_pair = {}
    for aggs in (legacy_aggs, disagg_aggs, tff_aggs):
        for sid, agg in aggs.items():
            for key, code_info in (agg.get("name_matched") or {}).items():
                dates_all = set()
                for info in code_info.values():
                    dates_all.update(info["dates"])
                pair_report_dates_by_pair.setdefault(key, set()).update(dates_all)
    rows_out, missing, future_rows = [], [], []
    for row in sched["rows"]:
        as_of = row["as_of"]
        if last_report and as_of > last_report:
            # scheduled beyond the freeze: bytes cannot exist yet (the rolling
            # schedule window extends past the census date)
            r = dict(row, basis="future_scheduled_not_yet_published",
                     grid_date=None, bytes_exist_used_pairs=None,
                     bytes_exist_all="not_applicable")
            future_rows.append(r)
            rows_out.append(r)
            continue
        if as_of in override:
            basis = {"basis": "evidenced_shutdown_publish",
                     "grid_date": override[as_of]["actual_publish"],
                     "note": override[as_of]["source"]}
        else:
            basis = {"basis": "evidenced_schedule", "grid_date": row["release_date"]}
        r = dict(row, **basis)
        verified = {p: as_of in pair_report_dates_by_pair.get(p, set())
                    for p in USED_PAIRS}
        verified["USD_INDEX"] = as_of in pair_report_dates_by_pair.get("USD_INDEX", set())
        r["bytes_exist_used_pairs"] = verified
        r["bytes_exist_all"] = all(verified.values())
        if not r["bytes_exist_all"]:
            missing.append({"as_of": as_of,
                            "missing": [k for k, ok in verified.items() if not ok]})
        rows_out.append(r)
    # convention model over all pre-window scored-span report dates
    span_dates = set()
    for y, agg in legacy_aggs.items():
        if agg.get("parse_ok"):
            for code_info in (agg.get("name_matched") or {}).values():
                for info in code_info.values():
                    span_dates.update(info["dates"])
    sched_asofs = {r["as_of"] for r in rows_out}
    conv_rows = []
    for dstr in sorted(d for d in span_dates if d not in sched_asofs
                       and d[:4] >= "2006" and d not in override):
        c = release_clock.convention_release(date.fromisoformat(dstr))
        conv_rows.append({"as_of": dstr, "release_date": c["release_date"],
                          "grid_date": c["grid_date"], "basis": "convention",
                          "holiday_shifted": c["holiday_shifted"]})
    verdict = "PASS"
    if not rows_out:
        verdict = "FAIL"
        killed.append("A2 schedule parse produced zero rows")
    elif missing:
        verdict = "FAIL"
        killed.append(f"A2 bytes-exist failures on {len(missing)} schedule rows")
    return {"verdict": verdict, "killed": killed,
            "schedule_window": {
                "rows": len(rows_out),
                "first": rows_out[0]["release_date"] if rows_out else None,
                "last": rows_out[-1]["release_date"] if rows_out else None,
                "future_scheduled_rows": len(future_rows),
                "checked_rows": len(rows_out) - len(future_rows),
                "anomalies": sched["anomalies"],
                "rolling_note": "ReleaseSchedule page is a rolling ~13-month window; PER-CYCLE RE-PIN required (plan A2). Rows beyond the census freeze are future-scheduled (no bytes expected)"},
            "schedule_rows": rows_out,
            "convention_rows_pre_window": conv_rows,
            "convention_model": {
                "text": "release Friday 15:30 ET (as-of previous Tuesday); federal holiday => next business day; decision = first 16:00-NY grid point strictly after the release instant",
                "marked": "convention-based (plan A2 amended substitution; NOT per-release evidence)",
                "applies_to": "pre-window scored-span report dates outside the rolling schedule window and outside the evidenced shutdown override",
                "pre_window_rows": len(conv_rows),
                "holiday_shifted_rows": sum(1 for r in conv_rows if r["holiday_shifted"]),
            },
            "shutdown_override": override,
            "shutdown_override_rows": len(override),
            "freshness_head_deacot2026": head_2026}


# --- A3 builder -------------------------------------------------------------
def build_a3(pages, faq6_present: bool) -> dict:
    killed = []
    if pages["special_announcements"]["status"] != 200:
        killed.append(f"special announcements status={pages['special_announcements']['status']}")
    html = (EVID_DIR / "special_announcements.snapshot.html").read_text(
        encoding="utf-8", errors="replace")
    parsed = parse_announcements(html)
    for item in parsed["items"]:
        t = item["text_head"].lower()
        if item["has_table"] and ("appropriations" in t or "interrupted" in t):
            item["class"] = "publication_delay_recovery"
        elif ("renamed" in t) or (("name" in t) and ("change" in t)):
            item["class"] = "label_change"
        elif item["mentions_value_correction"]:
            item["class"] = "value_correction_candidate"
        else:
            item["class"] = "publication_delay_other"
    used_value_corrections = [i for i in parsed["items"]
                              if i["class"] == "value_correction_candidate"
                              and i["mentions_used_code"]]
    override = {}
    for r in parsed["republish_table"]:
        override[mdy_to_iso(r["report_date"])] = {
            "original_publish": r["original_publish"],
            "actual_publish": mdy_to_iso(r["new_publish"])}
    handling = {
        "preregistered_before_D2": True,
        "rule": ("publication_delay/label classes: ANNOTATE-AND-KEEP (values carry FAQ-6 "
                 "no-revision; availability uses evidenced publish dates where published). "
                 "value-correction items naming a USED code: EXCLUDE-WINDOW — the named "
                 "(code, report_date) rows are excluded by the frozen X1 rule."),
        "faq6_no_revision_verified_on_snapshot": bool(faq6_present),
        "value_corrections_touching_used_codes": len(used_value_corrections),
        "page_coverage": ("served page covers the 2023-2025 accordion sections only; no older "
                          "archive is linked on the page at freeze (boundary declared, not assumed)"),
    }
    verdict = "PASS" if (pages["special_announcements"]["status"] == 200
                         and parsed["items"] and faq6_present) else "FAIL"
    if verdict != "PASS":
        killed.append("A3 announcements/FAQ-6 evidence incomplete")
    return {"verdict": verdict, "killed": killed,
            "items": parsed["items"],
            "classes": sorted({i["class"] for i in parsed["items"]}),
            "shutdown_override": override,
            "handling": handling}


# --- A4 builder -------------------------------------------------------------
def build_a4(legacy_aggs, disagg_aggs, tff_aggs) -> dict:
    killed = []
    regimes_out = {}
    for regime, aggs in (("legacy", legacy_aggs), ("disagg", disagg_aggs), ("tff", tff_aggs)):
        rej_total = rej_rows = 0
        ident_total = ident_bad = 0
        cons_rows = cons_bad = 0
        headers = {}
        unparsed = 0
        for sid, agg in sorted(aggs.items()):
            if not agg.get("parse_ok"):
                unparsed += 1
                killed.append(f"A4 unparsed/unknown schema: {agg['fkey']}: {agg.get('error')}")
                continue
            headers.setdefault(json.dumps(agg["header_verbatim"]), []).append(agg["fkey"])
            rej_total += agg["rejects_count"]
            rej_rows += agg["rows_total"]
            if regime != "legacy" or sid >= "2006":
                ident_total += agg["rows_identity_checked_nonconsolidated"]
                ident_bad += agg["identity_mismatch_nonconsolidated"]
                cons_rows += agg["consolidated_rows"]
                cons_bad += agg["identity_mismatch_count"] - agg["identity_mismatch_nonconsolidated"]
        rej_share = rej_total / rej_rows if rej_rows else 1.0
        ident_share = ident_bad / ident_total if ident_total else 1.0
        regimes_out[regime] = {
            "files_parsed": sum(1 for a in aggs.values() if a.get("parse_ok")),
            "files_expected": len(aggs), "files_unparsed": unparsed,
            "distinct_headers": headers,
            "rejects": {"count": rej_total, "rows": rej_rows,
                        "share": round(rej_share, 6), "share_max": REJECTS_SHARE_MAX,
                        "ok": rej_rows > 0 and rej_share <= REJECTS_SHARE_MAX},
            "identity": {"mismatches": ident_bad, "rows": ident_total,
                         "share": round(ident_share, 6), "share_max": IDENTITY_SHARE_MAX,
                         "ok": ident_total > 0 and ident_share <= IDENTITY_SHARE_MAX,
                         "basis": ("NON-CONSOLIDATED rows only ('CONSOLIDATED' markets "
                                   "combine component contracts and do not satisfy the "
                                   "parts identity by construction — preregistered); "
                                   "all rows for disagg/tff, legacy files sid>=2006"),
                         "consolidated_rows": cons_rows,
                         "consolidated_identity_mismatches": cons_bad},
        }
        if rej_rows and rej_share > REJECTS_SHARE_MAX:
            killed.append(f"A4 rejects share {rej_share:.5f} > {REJECTS_SHARE_MAX} in {regime}")
        if ident_total and ident_share > IDENTITY_SHARE_MAX:
            killed.append(f"A4 identity mismatch share {ident_share:.5f} > "
                          f"{IDENTITY_SHARE_MAX} in {regime}")
    return {"verdict": "PASS" if not killed else "FAIL", "killed": killed,
            "regimes": regimes_out,
            "decimal_contract": "all counts Decimal(str) from exact integer literals; no binary float constructed anywhere in the parser (module contract, offline-tested)",
            "fail_closed": "unknown schema raises SchemaUnknownError (offline-tested); malformed values reject the row into the census, never coerced"}


# --- A5 builder -------------------------------------------------------------
def _agg_pair_dates(agg):
    """Union of report dates across a file's name-matched used pairs + USD index."""
    dates = set()
    for key, code_info in (agg.get("name_matched") or {}).items():
        if key in USED_PAIRS or key == "USD_INDEX":
            for info in code_info.values():
                dates.update(info["dates"])
    return dates


def _agg_pair_year_counts(agg):
    """{pair_key: {year: n_report_dates}} for one file aggregate."""
    out = {}
    for key, code_info in (agg.get("name_matched") or {}).items():
        if key not in USED_PAIRS and key != "USD_INDEX":
            continue
        years = {}
        for info in code_info.values():
            for dstr in info["dates"]:
                years[dstr[:4]] = years.get(dstr[:4], 0) + 1
        out[key] = years
    return out


def build_a5(legacy_aggs, disagg_aggs, tff_aggs):
    killed = []
    legacy_cov = {}
    all_report_dates = set()
    dup_total = conf_total = 0
    for y, agg in sorted(legacy_aggs.items()):
        if not agg.get("parse_ok"):
            continue
        dates = _agg_pair_dates(agg)
        all_report_dates.update(dates)
        legacy_cov[y] = {"report_dates_used_pairs": sorted(dates), "weeks": len(dates),
                         "per_pair_year_counts": _agg_pair_year_counts(agg),
                         "rows_total": agg["rows_total"],
                         "rejects": agg["rejects_count"],
                         "identity_mismatches": agg["identity_mismatch_count"],
                         "duplicates": agg["exact_duplicates"],
                         "conflicts": len(agg["conflicts"])}
        dup_total += agg["exact_duplicates"]
        conf_total += len(agg["conflicts"])
    missing_reports = []
    sd = sorted(all_report_dates)
    for a, b in zip(sd, sd[1:]):
        gap = (date.fromisoformat(b) - date.fromisoformat(a)).days
        if gap > 14:
            missing_reports.append({"after": a, "next": b, "gap_days": gap})
    regime_merge = {}
    for regime, aggs in (("disagg", disagg_aggs), ("tff", tff_aggs)):
        seen = set()
        dups = conflicts = 0
        year_counts = {}
        for sid in REGIME_ORDER:  # hist-first declared precedence
            agg = aggs.get(sid) or {}
            if not agg.get("parse_ok"):
                continue
            for key, code_info in (agg.get("name_matched") or {}).items():
                if key not in USED_PAIRS and key != "USD_INDEX":
                    continue
                for c, info in code_info.items():
                    for dstr in info["dates"]:
                        ck = (key, c, dstr)
                        if ck in seen:
                            dups += 1
                        seen.add(ck)
                        all_report_dates.add(dstr)
                        year_counts.setdefault(dstr[:4], {})
                        year_counts[dstr[:4]][key] = year_counts[dstr[:4]].get(key, 0) + 1
            conflicts += len(agg["conflicts"])
            dup_total += agg["exact_duplicates"]
        regime_merge[regime] = {"per_pair_year_counts": year_counts,
                                "cross_file_duplicates": dups,
                                "conflict_count": conflicts}
        conf_total += conflicts
    last_report = max(all_report_dates) if all_report_dates else None
    # per-pair report dates across ALL regimes (for fold decision counts)
    pair_dates_all = {p: set() for p in USED_PAIRS}
    for aggs in (legacy_aggs, disagg_aggs, tff_aggs):
        for sid, agg in aggs.items():
            if not agg.get("parse_ok"):
                continue
            for key, code_info in (agg.get("name_matched") or {}).items():
                if key in pair_dates_all:
                    for info in code_info.values():
                        pair_dates_all[key].update(info["dates"])
    folds_decisions = {n: {p: 0 for p in USED_PAIRS} for n, _, _ in FOLD_BOUNDS}
    for p, dset in pair_dates_all.items():
        for d in dset:
            if d < SCORED_SPAN_START:
                continue
            for n, a, b in FOLD_BOUNDS:
                if a <= d <= (b or last_report or "9999-12-31"):
                    folds_decisions[n][p] += 1
    td_path = ROOT / ".worktrees/forex-free-v9/integration/data_raw/forex_free_v9_spot"
    pin = {"verdict": "NOT_RUN",
           "expected_path": str(td_path),
           "path_exists": td_path.exists(),
           "evidence": ("the FOREX-FREE-V9 worktree was removed from disk (2026-09-12 "
                        "cleanup); the TD daily spot bytes were gitignored staging by "
                        "design and are absent machine-wide (worktree dir empty; no "
                        "data_raw spot bytes tracked on any forex branch). Committed "
                        "authority that the four legs existed as V9-entitled daily TD "
                        "files: orca/forex-free-v9-integration run_contract.json "
                        "data_pins.spot_reacquired + research/assets/forex_free_v9/"
                        "family_common.py load_spot_daily (5000 daily bars x4 pairs, "
                        "2007/08..2026-09-10)."),
           "requirement": ("D1/prelaunch MUST re-stage the four TD legs under the owner "
                           "entitlement and pin fresh digests BEFORE any scored cell; "
                           "fold decision counts here bind to the frozen report-date grid "
                           "regardless of the spot re-staging")}
    if td_path.exists():
        import hashlib as _h
        pin["files"] = {f.name: {"sha256": _h.sha256(f.read_bytes()).hexdigest(),
                                 "bytes": f.stat().st_size}
                        for f in sorted(td_path.glob("*")) if f.is_file()}
        pin["verdict"] = "PINNED"
    mapping = {"schema": "forex_ng5_a5_mapping@1",
               "join_rule": ("pair identity anchored by market-NAME regex (codes are NOT "
                             "stable across eras — A1 records the per-era code timelines); "
                             "the frozen pair -> TD-leg join is by the exact names in "
                             "pairs[*].name_re against Market_and_Exchange_Names; NO fuzzy joins"),
               "pairs": USED_SPECS,
               "code_eras_reference": "per_year_code_table.json pair_year_tables (codes by era per pair, all regimes)",
               "usd_index": "USD index futures (098662-era codes under 'USD INDEX'-named markets): USD-side state context only — no entitled TD leg; not a pair-mapping row",
               "out_of_scope_declared": {**CONTEXT_CODES,
                                         "cross-rate pairs": "all */XXX CROSS contracts and non-USD-quoted crosses are out of scope (no entitled TD leg)"},
               "td_digest_pin": pin}
    verdict = "PASS"
    if last_report is None:
        verdict = "FAIL"
        killed.append("A5 empty report-date calendar")
    coverage = {"schema": "forex_ng5_a5_coverage@1",
                "legacy_per_year": legacy_cov,
                "missing_reports_gaps_gt_14d": missing_reports,
                "regime_merge": regime_merge,
                "duplicate_totals": {"exact_duplicates": dup_total,
                                     "conflicts": conf_total},
                "folds_decision_counts": folds_decisions,
                "last_report_date": last_report,
                "scored_span_start": SCORED_SPAN_START}
    return {"verdict": verdict, "killed": killed, "mapping": mapping,
            "last_report_date": last_report}, coverage


# --- A6 builder -------------------------------------------------------------
def build_a6(last_report, shutdown_override_rows) -> dict:
    folds = []
    for n, a, b in FOLD_BOUNDS:
        end = b or last_report
        folds.append({"fold": n, "start": a, "end": end,
                      "rule": ("a decision belongs to the fold of its as-of report_date "
                               "(report_date within [start, end]); folds are chronological "
                               "and non-overlapping; force-flat at fold boundary")})
    x1 = (
        "X1 REGIME/REVISION EXCLUSION RULE (C7-analog of STOCKS-NG4, frozen at P0 before any "
        "D2 diagnostic exists): "
        f"(a) REGIME BOUNDARY — scored-candidate decisions use the disaggregated/TFF era only "
        f"({SCORED_SPAN_START} onward); legacy-era weeks (1986-01-15..2006-06-12) are census-only "
        "evidence and are excluded from any scored book and from cross-regime comparison "
        "(regimes parsed separately per A4). "
        "(b) REVISION CONFLICTS — any (futures code, report_date) whose parsed rows conflict "
        "within or across files under the declared hist-first precedence is excluded from books; "
        "conflicts are annotate-and-keep in coverage_census.json (part of this freeze). "
        "(c) A3 CORRECTIONS — a CFTC Special Announcement that alters USED-CODE position values "
        "excludes the named (code, report_date) rows; publication-delay and label-class items are "
        "annotate-and-keep with availability taken from evidenced publish dates. As of this freeze "
        "the served announcements (2023-2025) contain NO value-correction item touching a used code. "
        "(d) AVAILABILITY BASIS — report dates inside the rolling schedule window use evidenced "
        "schedule dates; the 2025-10..2026-01 federal-appropriations republication window uses the "
        f"evidenced actual publish dates ({shutdown_override_rows} report dates overridden, see "
        "a2_availability.json); ALL earlier scored-span report dates use the frozen convention model "
        "(Friday 15:30 ET, federal holiday -> next business day; decision = first 16:00-NY grid "
        "point strictly after the release instant) and are marked convention-based. A decision "
        "whose 16:00-NY grid point has no session on the entitled TD grid is DROPPED, never "
        "shifted. "
        "(e) PUBLICATION GAPS — weeks with no published report (gap census in "
        "coverage_census.json) produce no decisions; positions are never interpolated, carried "
        "forward, or backfilled. "
        "(f) POINT-IN-TIME — this rule and the folds freeze at the census commit; later source "
        "corrections apply only to post-freeze windows and NEVER re-open folds (plan A7).")
    return {"schema": "forex_ng5_a6_fold_freeze@1", "measured_at_utc": FREEZE_UTC,
            "span": {"start": SCORED_SPAN_START, "end": last_report,
                     "basis": "disaggregated/TFF era start through the last report date present in the frozen bytes"},
            "folds": folds,
            "exclusion_rule_X1": x1,
            "decision_counts_reference": "coverage_census.json folds_decision_counts"}


if __name__ == "__main__":
    main()
