#!/usr/bin/env python
"""FOREX-FREE-V4 P0a: append-only availability-evidence extension.

Authority: PLAN_forex_v4.md section 6 P0a — "Re-verify the pinned
announcement ledger byte-identical; extend it append-only with any
additional officially evidenced events (RBA, RBNZ, SNB, ECB static
listings were conservative in V3R); re-pin; regenerate evidenced
vintages through the inherited pipeline with the only-availability-
differs invariant."

What it does
------------
1.  Loads ``announcement_ledger_base_v1.jsonl`` (byte-identical copy of
    the V3R pinned ledger) and REFUSES to run unless its sha256 equals
    the V3R pin ``169b9e447f01ba0114396a3f26f208f57f61008a6ce6e30873e3b
    6642f8cf895``.  This is the P0a pre-extension gate.
2.  Targets only ``AVAILABILITY_UNEVIDENCED`` RATE_CHANGE rows in
    {AU, NZ, CH, EMU}.  CA (BoC) is NOT wired in this run (owner plan
    names RBA/RBNZ/SNB/ECB) and stays a recorded gap.
3.  Per-area evidence adapters (every fetch archived under sha256,
    verified or not; verification failure degrades, never invents
    precision):
      AU  rba.gov.au/statistics/cash-rate/  — official per-event table
          (Effective Date | Change | Level) + the page's own statement
          "A media release is issued at 2.30 pm ... taking effect the
          following day".  Announcement day = effective date minus one
          day (the page's own rule); instant = 14:30 Australia/Sydney
          on that day (AEST/AEDT resolved per date).  -> INSTANT /
          OFFICIAL_FIXED_SCHEDULE.
      NZ  rbnz.govt.nz/monetary-policy/official-cash-rate-decisions —
          official decision table (Date | OCR | documents).  Row date
          is the evidenced announcement date.  No release time on the
          page -> DAY / DAY_CONSERVATIVE (end of announcement UTC day).
      CH  snb.ch/en/news-publications/media-releases (paginated) —
          dated entries titled "Monetary policy assessment of ...".
          Entry date is the evidenced announcement date -> DAY.
      EMU ecb.europa.eu key-ECB-interest-rates table — official
          effective-date/level table used as a per-event CROSS-CHECK
          only; no announcement-date evidence exists keyless -> rows
          stay AVAILABILITY_UNEVIDENCED (gap recorded, never papered
          over).
4.  Emits upgrade rows of the IDENTICAL row schema, appended AFTER the
    159 base lines; ``index_ledger`` in the inherited vintage builder
    applies last-row-wins per (area, effective_date), so the appended
    rows govern.  The base 159 lines stay byte-identical (verified
    prefix check before pinning).
5.  Re-pins under THIS run dir (fresh pin file + manifest); the V3R
    pin continues to govern the V3R artifacts and is never touched.

Shared-page archives: one archive per source page (not one per event),
with the exact matched row text recorded per event in the row's
``announcement.evidence_extract`` — a documented deviation from the V3R
per-event archive naming, chosen so A7 can verify each row against the
archived bytes it cites (extract must appear in the archived page).

Usage
-----
  .venv/bin/python research/control/forex_free_v4_run/announcement_ledger_builder_v4_extension.py [--pin]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

RUN_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_LEDGER = os.path.join(RUN_DIR, "announcement_ledger_base_v1.jsonl")
OUT_LEDGER = os.path.join(RUN_DIR, "announcement_ledger.jsonl")
STAGING_SUFFIX = ".staging"
MANIFEST_PATH = os.path.join(RUN_DIR, "ledger_manifest.json")
PIN_PATH = os.path.join(RUN_DIR, "LEDGER_PINNED")
ARCHIVE_DIR = os.path.join(RUN_DIR, "announcement_archives_v4_extension")

BASE_PIN = "169b9e447f01ba0114396a3f26f208f57f61008a6ce6e30873e3b6642f8cf895"
WINDOW_START = "2019-01-01"
NY = ZoneInfo("America/New_York")
SYDNEY = ZoneInfo("Australia/Sydney")

# documented out-of-cycle announcement dates (flag only; never the bound)
UNSCHEDULED_ANNOUNCEMENT_DATES = {
    "AU": {"2020-03-03"},
}

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}
MONTHS.update({m[:3].lower(): i for m, i in
               [(k.capitalize(), v) for k, v in list(MONTHS.items())]})

BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0.0.0 Safari/537.36")
CURL_HEADERS = [
    "-H", f"User-Agent: {BROWSER_UA}",
    "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "-H", "Accept-Language: en-US,en;q=0.9",
    "-H", "Sec-Fetch-Dest: document",
    "-H", "Sec-Fetch-Mode: navigate",
    "-H", "Sec-Fetch-Site: none",
    "-H", "Sec-Fetch-User: ?1",
    "-H", "Upgrade-Insecure-Requests: 1",
]


# ---------------------------------------------------------------------------
# transport: curl first (RBA blocks python TLS fingerprints), urllib fallback;
# a response that fails the caller's sanity check falls through to the next
# transport (RBNZ serves an error shell to browser-UA curl but the real page
# to the repo-UA urllib client).
# ---------------------------------------------------------------------------
def _curl_get(url, timeout):
    import tempfile
    with tempfile.NamedTemporaryFile() as tmp:
        proc = subprocess.run(
            ["curl", "-s", "--compressed", "--max-time", str(timeout),
             "-o", tmp.name, "-w", "%{http_code}", *CURL_HEADERS, url],
            capture_output=True, timeout=timeout + 10)
        try:
            status = int(proc.stdout.decode().strip())
        except ValueError:
            status = 0
        raw = open(tmp.name, "rb").read()
    return status, raw


def _urllib_get(url, timeout):
    req = urllib.request.Request(url, headers={
        "User-Agent": "my-quantitative-forex-v4-ledger/1.0 "
                      "(research evidence builder; keyless public sources)",
        "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            import gzip as _gzip
            raw = _gzip.decompress(raw)
        return resp.status, raw


def fetch(url, sanity_tokens=(), timeout=60):
    """Returns (transport, status, text, raw_bytes).  Tries curl with
    browser-consistent headers, then urllib with the repo UA; a response
    is accepted only if it contains at least one sanity token (when any
    are given) — otherwise the next transport is tried.  Raises when all
    transports are exhausted."""
    errors = []
    for name, getter in (("curl_browser_headers", _curl_get),
                         ("urllib_repo_ua", _urllib_get)):
        for attempt in range(2):
            try:
                status, raw = getter(url, timeout)
            except Exception as exc:  # noqa: BLE001 - degradation is designed
                errors.append(f"{name}:{type(exc).__name__}")
                time.sleep(5 * (attempt + 1))
                continue
            text = raw.decode("utf-8", "latin-1")
            if raw and (not sanity_tokens
                        or any(s.lower() in text.lower()
                               for s in sanity_tokens)):
                return name, status, text, raw
            errors.append(f"{name}:http{status}:sanity_fail"
                          if status else f"{name}:empty")
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"transport exhausted for {url}: {errors}")


def archive(label, raw):
    digest = hashlib.sha256(raw).hexdigest()
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", label)
    name = f"{safe}.{digest[:12]}.bin"
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    path = os.path.join(ARCHIVE_DIR, name)
    if not os.path.exists(path):  # append-only archives
        with open(path, "wb") as handle:
            handle.write(raw)
    return os.path.relpath(path, RUN_DIR), digest


def normalize(text):
    text = text.replace("&nbsp;", " ").replace("\xa0", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# base ledger (P0a gate) + targets
# ---------------------------------------------------------------------------
def load_base():
    raw = open(BASE_LEDGER, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != BASE_PIN:
        raise SystemExit(f"BASE_PIN_MISMATCH: {digest} != {BASE_PIN} "
                         "(P0a pre-extension gate failed)")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()
            if line.strip()]
    return raw, rows


def targets(rows):
    out = []
    for row in rows:
        if row["row_type"] != "RATE_CHANGE":
            continue
        if row["area"] in ("AU", "NZ", "CH", "EMU") and \
                row["announcement"]["status"] == "AVAILABILITY_UNEVIDENCED":
            out.append(row)
    return out


# ---------------------------------------------------------------------------
# decision-clock mapping (identical to the inherited builder)
# ---------------------------------------------------------------------------
def ny_decision_instants():
    instants = []
    day = date(2019, 1, 1)
    end = date(2026, 9, 2)
    while day <= end:
        instants.append(datetime(day.year, day.month, day.day, 16, 0,
                                 tzinfo=NY).astimezone(timezone.utc))
        day += timedelta(days=1)
    return instants


_DECISIONS = None


def first_readable_decision(effective_instant, available_instant):
    global _DECISIONS
    if _DECISIONS is None:
        _DECISIONS = ny_decision_instants()
    threshold = max(effective_instant, available_instant)
    for instant in _DECISIONS:
        if instant >= threshold:
            return instant.isoformat().replace("+00:00", "Z")
    return None


def end_of_day_utc(day):
    return (datetime(day.year, day.month, day.day, 23, 59, 59,
                     tzinfo=timezone.utc)
            .isoformat().replace("+00:00", "Z"))


def parse_day(token):
    """'5 Jun 2019' / '5 June 2019' / '2 September 2026' -> date."""
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", token.strip())
    if not m:
        return None
    month = MONTHS.get(m.group(2).lower())
    if not month:
        return None
    return date(int(m.group(3)), month, int(m.group(1)))


# ---------------------------------------------------------------------------
# AU adapter — official cash-rate table + fixed-schedule statement
# ---------------------------------------------------------------------------
AU_URL = "https://www.rba.gov.au/statistics/cash-rate/"
AU_SCHEDULE_SUBSTRINGS = ["media release is issued at 2.30 pm",
                          "taking effect the following day"]


def au_evidence(manifest):
    transport, http_status, text, raw = fetch(
        AU_URL, sanity_tokens=["Cash Rate Target", "media release"])
    rel, digest = archive("AU__SOURCE__cash_rate_page", raw)
    record = {"url": AU_URL, "http_status": http_status,
              "transport": transport, "archive_path": rel,
              "archive_sha256": digest, "bytes": len(raw)}
    flat = normalize(re.sub(r"<[^>]+>", "\n", text))
    sched_ok = all(s in flat.lower() for s in AU_SCHEDULE_SUBSTRINGS)
    if not sched_ok:
        record["schedule_statement_found"] = False
        manifest["sources"].append(record)
        return None, record
    record["schedule_statement_found"] = True
    # per-event table rows: <tr> <th scope="row">5 Jun 2019</th>
    # <td>-0.25</td> <td>1.25</td> <td class="links">...</td> </tr>
    entries = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S | re.I):
        cells = [normalize(c) for c in
                 re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, flags=re.S | re.I)]
        if len(cells) < 3:
            continue
        day = parse_day(cells[0])
        if day is None:
            continue
        change_tok, level_tok = cells[1], cells[2]
        m_lvl = re.match(r"^(\d+\.\d+)$", level_tok)
        if not m_lvl:
            continue
        m_link = re.search(r'href="(/media-releases/[^"]+)"', tr)
        entries[day.isoformat()] = {
            "effective_date": day.isoformat(),
            "change": float(change_tok) if re.match(
                r"^[+-]?\d+(\.\d+)?$", change_tok) else None,
            "level": float(m_lvl.group(1)),
            "extract": " | ".join(cells[:3]),
            "detail_url": ("https://www.rba.gov.au" + m_link.group(1))
                          if m_link else None,
        }
    record["parsed_rows"] = len(entries)
    manifest["sources"].append(record)
    return entries, record


def apply_au(base_row, entries, src, manifest):
    eff = base_row["effective_date"]
    ev = entries.get(eff)
    if ev is None:
        return None, "no official table row for the effective date"
    new_value = float(base_row["new_value"])
    old_value = float(base_row["old_value"])
    rate_ok = (abs(ev["level"] - new_value) < 1e-9 and ev["change"] is not None
               and abs(ev["change"] - (new_value - old_value)) < 1e-9)
    eff_day = date.fromisoformat(eff)
    ann_day = eff_day - timedelta(days=1)   # the page's own rule
    instant = (datetime(ann_day.year, ann_day.month, ann_day.day, 14, 30,
                        tzinfo=SYDNEY).astimezone(timezone.utc)
               .isoformat().replace("+00:00", "Z"))
    return {
        "announcement_date": ann_day.isoformat(),
        "instant": instant,
        "precision": "INSTANT",
        "time_source": "OFFICIAL_FIXED_SCHEDULE",
        "rate_verified": rate_ok,
        "extract": ev["extract"],
        "detail_url": None,
        "src_record": src,
    }, None


# ---------------------------------------------------------------------------
# NZ adapter — official OCR decision table
# ---------------------------------------------------------------------------
NZ_URL = "https://www.rbnz.govt.nz/monetary-policy/official-cash-rate-decisions"


def nz_evidence(manifest):
    transport, http_status, text, raw = fetch(
        NZ_URL, sanity_tokens=["Official Cash Rate", "Past monetary policy"])
    rel, digest = archive("NZ__SOURCE__ocr_decisions", raw)
    record = {"url": NZ_URL, "http_status": http_status,
              "transport": transport, "archive_path": rel,
              "archive_sha256": digest, "bytes": len(raw)}
    entries = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S | re.I)
        if not tds or "colspan" in tr.split(">")[0]:
            continue
        day_tok = normalize(tds[0])
        m = re.match(r"^(\d{1,2}\s+[A-Za-z]+\s+\d{4})", day_tok)
        if not m:
            continue
        day = parse_day(m.group(1))
        if day is None or len(tds) < 2:
            continue
        level_tok = normalize(tds[1])
        m_lvl = re.match(r"^(\d+\.\d+)", level_tok)
        if not m_lvl:
            continue
        link = None
        m_link = re.search(r'href="([^"]+)"', tr)
        if m_link:
            link = m_link.group(1)
        entries[day.isoformat()] = {
            "announcement_date": day.isoformat(),
            "level": float(m_lvl.group(1)),
            "extract": f"{day_tok} | OCR {m_lvl.group(1)}",
            "detail_url": ("https://www.rbnz.govt.nz" + link)
                          if link and link.startswith("/") else link,
        }
    record["parsed_rows"] = len(entries)
    manifest["sources"].append(record)
    if not entries:
        return None, record
    return entries, record


def apply_nz(base_row, entries, src, manifest):
    eff_day = date.fromisoformat(base_row["effective_date"])
    new_value = float(base_row["new_value"])
    for offset in (0, -1, -2, -3):
        cand = (eff_day + timedelta(days=offset)).isoformat()
        ev = entries.get(cand)
        if ev is None:
            continue
        return {
            "announcement_date": cand,
            "instant": None,
            "precision": "DAY",
            "time_source": "DAY_CONSERVATIVE",
            "rate_verified": abs(ev["level"] - new_value) < 1e-9,
            "extract": ev["extract"],
            "detail_url": ev["detail_url"],
            "src_record": src,
        }, None
    return None, "no OCR table row within effective-0..-3 day window"


# ---------------------------------------------------------------------------
# CH adapter — paginated media-release listing
# ---------------------------------------------------------------------------
CH_LISTING = "https://www.snb.ch/en/news-publications/media-releases"
CH_PAGE = CH_LISTING + "~page-4={n}~"
CH_MAX_PAGES = 70


def ch_evidence(manifest):
    entries = {}
    archives = []
    oldest = None
    for n in range(1, CH_MAX_PAGES + 1):
        url = CH_LISTING if n == 1 else CH_PAGE.format(n=n)
        try:
            transport, http_status, text, raw = fetch(
                url, sanity_tokens=["publication-date",
                                    "Monetary policy assessment"])
        except RuntimeError as exc:
            archives.append({"url": url, "error": repr(exc)})
            break
        rel, digest = archive(f"CH__SOURCE__media_releases_p{n:02d}", raw)
        archives.append({"url": url, "http_status": http_status,
                         "transport": transport, "archive_path": rel,
                         "archive_sha256": digest, "bytes": len(raw)})
        page_dates = []
        for li in re.findall(r"<li[^>]*link-list-item[^>]*>(.*?)</li>",
                             text, flags=re.S | re.I):
            m_date = re.search(
                r'publication-date[^>]*>\s*(\d{1,2}\.\d{1,2}\.\d{4})', li)
            m_title = re.search(r"<h3[^>]*>([^<]+)</h3>", li)
            m_href = re.search(r'href="([^"]+)"', li)
            if not m_date or not m_title:
                continue
            d, mnt, y = (int(x) for x in m_date.group(1).split("."))
            day = date(y, mnt, d)
            title = normalize(m_title.group(1))
            page_dates.append(day)
            if not title.lower().startswith("monetary policy assessment"):
                continue
            entries[day.isoformat()] = {
                "announcement_date": day.isoformat(),
                "title": title,
                "extract": f"{m_date.group(1)} | {title}",
                "detail_url": ("https://www.snb.ch" + m_href.group(1))
                              if m_href else None,
                "page_index": len(archives) - 1,
            }
        if not page_dates:
            break
        page_min = min(page_dates).isoformat()
        oldest = page_min if oldest is None else min(oldest, page_min)
        if page_min < WINDOW_START:
            break
        time.sleep(1.0)   # polite listing crawl
    record = {"listing_pages_fetched": len(archives),
              "oldest_entry_date": oldest,
              "assessment_entries": len(entries), "pages": archives}
    manifest["sources"].append(record)
    if not entries:
        return None, record
    return entries, record


def apply_ch(base_row, entries, src, manifest):
    eff_day = date.fromisoformat(base_row["effective_date"])
    hits = []
    for offset in (0, -1, -2, -3):
        cand = (eff_day + timedelta(days=offset)).isoformat()
        if cand in entries:
            hits.append(entries[cand])
    if len(hits) == 1:
        ev = hits[0]
        page = src["pages"][ev["page_index"]]
        return {
            "announcement_date": ev["announcement_date"],
            "instant": None,
            "precision": "DAY",
            "time_source": "DAY_CONSERVATIVE",
            "rate_verified": False,   # listing carries no rate tokens
            "extract": ev["extract"],
            "detail_url": ev["detail_url"],
            "src_record": page,
        }, None
    if len(hits) > 1:
        return None, f"ambiguous: {len(hits)} assessment entries in window"
    return None, "no monetary-policy-assessment entry within window"


# ---------------------------------------------------------------------------
# EMU adapter — cross-check only (no announcement evidence keyless)
# ---------------------------------------------------------------------------
EMU_URL = ("https://www.ecb.europa.eu/stats/policy_and_exchange_rates/"
           "key_ecb_interest_rates/html/index.en.html")
MONTHS_EN = {m.lower(): i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct",
     "nov", "dec"], 1)}


def emu_crosscheck(base_rows, manifest):
    transport, http_status, text, raw = fetch(
        EMU_URL, sanity_tokens=["Key ECB interest rates", "Deposit facility"])
    rel, digest = archive("EMU__SOURCE__key_rates_table", raw)
    record = {"url": EMU_URL, "http_status": http_status,
              "transport": transport, "archive_path": rel,
              "archive_sha256": digest, "bytes": len(raw),
              "role": "cross_check_only"}
    # rows: the year appears in the FIRST row of each year group and is
    # carried forward; subsequent rows of the same year have an empty year
    # cell.  Rate columns: deposit facility, MRO (fixed rate), marginal.
    table = {}
    year = None
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S | re.I):
        cells = [normalize(c) for c in
                 re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S | re.I)]
        cells = [c for c in cells if c]
        if not cells:
            continue
        if re.match(r"^(19|20)\d\d$", cells[0]):
            year = int(cells[0])
            cells = cells[1:]
        if year is None or not cells:
            continue
        # date cell may carry a trailing footnote marker ("18 Sep. 5")
        m = re.match(r"^(\d{1,2})\s+([A-Za-z]{3,9})\.?(?:\s+\S{1,3})?$",
                     cells[0])
        if not m:
            continue
        month = MONTHS_EN.get(m.group(2).lower())
        if not month:
            continue
        day = date(year, month, int(m.group(1)))
        levels = [c for c in cells[1:] if re.match(r"^\d+\.\d+$", c)]
        if levels:
            entry = {"deposit_facility": float(levels[0])}
            if len(levels) > 1:
                entry["mro_fixed_rate"] = float(levels[1])
            table[day.isoformat()] = entry
    record["parsed_rows"] = len(table)
    manifest["sources"].append(record)
    checks = []
    for row in base_rows:
        if row["row_type"] == "RATE_CHANGE" and row["area"] == "EMU":
            expected = float(row["new_value"])
            got = table.get(row["effective_date"])
            checks.append({
                "decision_id": row["decision_id"],
                "effective_date": row["effective_date"],
                "bis_new_value": expected,
                "official": got,
                "matches_bis_new_value":
                    got is not None and
                    (abs(got.get("mro_fixed_rate",
                                 got["deposit_facility"]) - expected) < 1e-9
                     or abs(got["deposit_facility"] - expected) < 1e-9)})
    return checks


# ---------------------------------------------------------------------------
# upgrade rows
# ---------------------------------------------------------------------------
AREA_APPLY = {"AU": apply_au, "NZ": apply_nz, "CH": apply_ch}


def build_upgrade_row(base_row, ev, schedule_claim=None):
    area = base_row["area"]
    src = ev["src_record"]
    eff_instant = datetime.fromisoformat(
        base_row["effective_time_utc"].replace("Z", "+00:00"))
    if ev["precision"] == "INSTANT":
        available = ev["instant"]
    else:
        available = end_of_day_utc(date.fromisoformat(ev["announcement_date"]))
    unscheduled = (ev["announcement_date"]
                   in UNSCHEDULED_ANNOUNCEMENT_DATES.get(area, set()))
    announcement = {
        "status": "EVIDENCED",
        "announcement_date": ev["announcement_date"],
        "announcement_time_utc": ev["instant"],
        "operative_available_time_utc": available,
        "precision": ev["precision"],
        "time_source": ev["time_source"],
        "source_url": src["url"],
        "archive_path": src["archive_path"],
        "archive_sha256": src["archive_sha256"],
        "date_verified": True,
        "rate_verified": bool(ev["rate_verified"]),
        "schedule_claim_archive": schedule_claim or [],
        "unscheduled": unscheduled,
        "unscheduled_basis": ("documented out-of-cycle decision date; see "
                              "archived page" if unscheduled else None),
        "unverified_probe": None,
        "evidence_extract": ev["extract"],
        "detail_url": ev.get("detail_url"),
        "transport": src.get("transport"),
        "extension": "FOREX-FREE-V4 P0a append-only availability upgrade",
    }
    row = {
        "schema": base_row["schema"],
        "row_type": "RATE_CHANGE",
        "area": area,
        "area_name": base_row["area_name"],
        "decision_id": base_row["decision_id"],
        "effective_date": base_row["effective_date"],
        "effective_time_utc": base_row["effective_time_utc"],
        "old_value": base_row["old_value"],
        "new_value": base_row["new_value"],
        "bis_publication_stamp": None,
        "announcement": announcement,
        "first_readable_decision_utc": first_readable_decision(
            eff_instant,
            datetime.fromisoformat(available.replace("Z", "+00:00"))),
        "old_bound_end_of_effective_day":
            base_row["old_bound_end_of_effective_day"],
        "old_bound_first_readable_decision_utc":
            base_row["old_bound_first_readable_decision_utc"],
    }
    return row


def row_bytes(row):
    return json.dumps(row, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pin", action="store_true",
                        help="promote staging ledger + manifest to the pinned "
                             "names (refuses to overwrite existing pins)")
    args = parser.parse_args()

    base_raw, base_rows = load_base()
    tgt = targets(base_rows)
    manifest = {
        "schema": "forex_free_v4_announcement_ledger_extension_manifest_v1",
        "built_at_utc": datetime.now(timezone.utc)
                        .isoformat().replace("+00:00", "Z"),
        "stamp_source": "machine_date_u",
        "producer": "A1_FOREX_CONTROLLER (A2 lane, FOREX-FREE-V4 P0a)",
        "authority": "PLAN_forex_v4.md section 6 P0a",
        "base_ledger": {
            "path": "announcement_ledger_base_v1.jsonl",
            "sha256": hashlib.sha256(base_raw).hexdigest(),
            "v3r_pin": BASE_PIN,
            "pin_verified": True,
            "rows": len(base_rows),
        },
        "append_only_design": "v2 file = exact 159 base lines (byte-identical "
                              "prefix, verified) + appended upgrade rows of "
                              "the identical row schema; the inherited "
                              "vintage builder's index_ledger applies "
                              "last-row-wins per (area, effective_date)",
        "sources": [],
        "per_area": {},
        "emu_cross_check": None,
        "upgrades": [],
        "not_upgraded": [],
    }

    # EMU cross-check (no upgrades)
    manifest["emu_cross_check"] = emu_crosscheck(base_rows, manifest)

    per_area_evidence = {}
    results = {}
    # AU
    au_entries, au_src = au_evidence(manifest)
    per_area_evidence["AU"] = (au_entries, au_src)
    # NZ
    nz_entries, nz_src = nz_evidence(manifest)
    per_area_evidence["NZ"] = (nz_entries, nz_src)
    # CH
    ch_entries, ch_src = ch_evidence(manifest)
    per_area_evidence["CH"] = (ch_entries, ch_src)

    schedule_claim_archive = []
    if au_src and au_src.get("schedule_statement_found"):
        schedule_claim_archive = [{
            "url": AU_URL,
            "require_substrings": AU_SCHEDULE_SUBSTRINGS,
            "archive_path": au_src["archive_path"],
            "archive_sha256": au_src["archive_sha256"],
            "verified": True,
            "note": "page states media releases at 2.30 pm with any change "
                    "taking effect the following day (V3R-adjudged claim, "
                    "re-verified against this run's archived bytes)",
        }]

    upgrade_rows = []
    for base_row in tgt:
        area = base_row["area"]
        entries, src = per_area_evidence.get(area, (None, None))
        outcome = {"decision_id": base_row["decision_id"],
                   "area": area,
                   "effective_date": base_row["effective_date"]}
        if entries is None:
            outcome["status"] = "NOT_UPGRADED"
            outcome["reason"] = "source unavailable or unparsable"
            manifest["not_upgraded"].append(outcome)
            continue
        ev, reason = AREA_APPLY[area](base_row, entries, src, manifest)
        if ev is None:
            outcome["status"] = "NOT_UPGRADED"
            outcome["reason"] = reason
            manifest["not_upgraded"].append(outcome)
            continue
        row = build_upgrade_row(base_row, ev,
                                schedule_claim_archive if area == "AU" else None)
        outcome["status"] = "UPGRADED"
        outcome["announcement_date"] = ev["announcement_date"]
        outcome["precision"] = ev["precision"]
        outcome["time_source"] = ev["time_source"]
        outcome["rate_verified"] = bool(ev["rate_verified"])
        outcome["old_operative_bound"] = \
            base_row["announcement"]["operative_available_time_utc"]
        outcome["new_operative_bound"] = \
            row["announcement"]["operative_available_time_utc"]
        outcome["first_readable_decision_utc"] = \
            row["first_readable_decision_utc"]
        upgrade_rows.append(row)
        manifest["upgrades"].append(outcome)

    for area in ("AU", "NZ", "CH"):
        ups = [u for u in manifest["upgrades"] if u["area"] == area]
        nots = [u for u in manifest["not_upgraded"] if u["area"] == area]
        manifest["per_area"][area] = {
            "targeted": sum(1 for r in tgt if r["area"] == area),
            "upgraded": len(ups),
            "not_upgraded": len(nots),
            "precisions": sorted({u["precision"] for u in ups}),
        }
    emu_tgt = sum(1 for r in tgt if r["area"] == "EMU")
    manifest["per_area"]["EMU"] = {
        "targeted": emu_tgt, "upgraded": 0, "not_upgraded": emu_tgt,
        "note": "official key-rate table evidences effective dates/levels "
                "(cross-check) but no announcement-date evidence is "
                "reachable keyless; rows stay conservative-unevidenced "
                "(P-1: asserted bounds are never authorized)"}
    ca_unevidenced = sum(1 for r in base_rows if r["row_type"] == "RATE_CHANGE"
                         and r["area"] == "CA"
                         and r["announcement"]["status"]
                         == "AVAILABILITY_UNEVIDENCED")
    manifest["per_area"]["CA"] = {
        "targeted": 0, "upgraded": 0,
        "note": f"BoC not named by PLAN_forex_v4.md P0a; {ca_unevidenced} "
                "rate-change rows remain conservative-unevidenced (gap "
                "recorded, never papered over)"}

    # assemble v2 = base bytes (untouched) + appended upgrade rows
    payload = base_raw + b"".join(
        row_bytes(r).encode("utf-8") for r in upgrade_rows)
    staging_path = OUT_LEDGER + STAGING_SUFFIX
    with open(staging_path, "wb") as handle:
        handle.write(payload)
    # append-only verification: prefix must equal the base bytes exactly
    if payload[:len(base_raw)] != base_raw:
        raise SystemExit("APPEND_ONLY_PREFIX_VIOLATION")
    manifest["ledger_sha256"] = hashlib.sha256(payload).hexdigest()
    manifest["n_rows_total"] = len(base_rows) + len(upgrade_rows)
    manifest["n_appended_upgrade_rows"] = len(upgrade_rows)
    manifest["base_prefix_byte_identical"] = True
    manifest["note"] = ("staging artifacts are unpinned; --pin promotes to "
                        "the final append-only names after review")

    with open(MANIFEST_PATH + STAGING_SUFFIX, "w", encoding="utf-8") as h:
        json.dump(manifest, h, indent=1, sort_keys=True, ensure_ascii=False)

    if args.pin:
        if os.path.exists(OUT_LEDGER) or os.path.exists(PIN_PATH):
            raise SystemExit("REFUSING_TO_OVERWRITE_PINNED_LEDGER "
                             "(append-only)")
        os.replace(staging_path, OUT_LEDGER)
        os.replace(MANIFEST_PATH + STAGING_SUFFIX, MANIFEST_PATH)
        with open(PIN_PATH, "w") as handle:
            handle.write(json.dumps(
                {"ledger_sha256": manifest["ledger_sha256"],
                 "base_ledger_sha256": BASE_PIN,
                 "pinned_at_utc": manifest["built_at_utc"],
                 "n_rows_total": manifest["n_rows_total"],
                 "n_appended_upgrade_rows": len(upgrade_rows)},
                indent=1, sort_keys=True))

    print(json.dumps({
        "targeted": len(tgt),
        "upgraded": len(upgrade_rows),
        "not_upgraded": len(manifest["not_upgraded"]),
        "per_area": manifest["per_area"],
        "n_rows_total": manifest["n_rows_total"],
        "ledger_sha256": manifest["ledger_sha256"],
        "pinned": bool(args.pin),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
