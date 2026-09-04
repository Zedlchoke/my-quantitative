#!/usr/bin/env python
"""FOREX-FREE-V3R R1: official central-bank announcement ledger builder.

STATUS: DRAFT -- UNRUN (authored during a session shell outage; every URL
pattern below was probed 2026-09-05 via an independent reader, but the
script itself has never executed).  The next run must:
  1. run under the repo venv alone (.venv/bin/python, light work);
  2. treat its own output as UNPINNED until reviewed;
  3. hash-pin the ledger (``--pin``) only after the coverage report is
     reviewed against the frozen vintage union.

Authority: PLAN_forex_v3r.md section 2 (the ONLY scientific change of V3R:
available_time_utc for macro rows comes from this ledger).  The strategy is
FROZEN byte-identical; nothing here edits any frozen file.

What it builds
--------------
``announcement_ledger.jsonl`` -- one row per policy-rate change event per
currency area over the frozen scored window (2019-01-01 .. 2026-09-02),
plus one BASELINE_LEVEL provenance row per area.  Per event:

  * the event itself (area, effective date, old/new value) is DERIVED from
    the frozen byte-pinned BIS vintage files (data_raw/forex_free_v3_macro,
    hashes in w3_freeze.json) -- never retyped from memory;
  * announcement evidence comes ONLY from official, public, keyless central
    bank sources; every fetched candidate is archived under sha256 whether
    or not it verifies, so the evidence trail is complete;
  * announcement timestamp is recorded as precisely as the evidence
    supports: INSTANT (release-time line on the archived page, or a
    VERIFIED official fixed-schedule claim) or DAY (announcement date
    evidenced, time not) -- and otherwise the event is recorded
    ``AVAILABILITY_UNEVIDENCED`` and takes the conservative LATER bound
    (end of effective UTC day, vs first BIS publication stamp if one ever
    existed -- historically none does, recorded as null);
  * announcement timestamp and effective date are recorded SEPARATELY;
  * unscheduled/out-of-cycle decisions are flagged from the documented
    out-of-cycle date table below (each row cites its own page as the
    evidence; the flag is a claim, reviewable in the archive);
  * the decision-clock mapping (first 16:00 America/New_York decision at
    which the change is readable under the evidence) is computed from the
    operative availability bound and the effective instant.

Honesty rules (the V3 defect was an unproven availability ASSERTION; this
builder may not repeat it):
  * a timestamp enters the ledger only if its bytes were fetched from the
    official source and archived, or a schedule claim was verified against
    archived official bytes;
  * any verification failure degrades the row one step (INSTANT -> DAY ->
    UNEVIDENCED); it never invents precision;
  * rate old/new values always come from the frozen vintages; when the
    archived page also contains parseable rate tokens they are cross-checked
    and the result recorded (rate_verified), never substituted.

Sources probed 2026-09-05 (reader-level verification, keyless):
  VERIFIED   US  press release  monetaryYYYYMMDDa.htm carries a literal
                 "For release at 2:00 p.m. EDT" line + old/new range text
  VERIFIED   US  openmarket.htm  official change table (Date/Increase/
                 Decrease/Level), 2003..2025+
  VERIFIED   CA  Valet V39079    official target-rate series, keyless JSON
  VERIFIED   AU  statistics/cash-rate/  official table (Effective Date |
                 Change | level) AND the page itself states releases at
                 "2.30 pm", effective the following day
  VERIFIED   GB  monetary-policy-summary-and-minutes/YYYY/<month>-YYYY
                 pages exist per decision with dates (no release times)
  VERIFIED   JP  mopo/mpmdeci/mpr_<year>/index.htm  static per-year list of
                 monetary policy releases with dates + document links
  FAILED     ECB yearly PR listing is JS-rendered / 404; the static key-rate
                 stats page (effect-from dates + levels) is the fallback
                 cross-check; per-event announcement evidence will likely
                 degrade to UNEVIDENCED for ECB unless the run finds the
                 pages -- reported as an evidence gap, never papered over
  BLOCKED    RBNZ 403 (UA block suspected), SNB paths 404 (site redesign)
                 -- both degrade to the conservative bound automatically

Usage
-----
  .venv/bin/python research/control/forex_free_v3r_run/announcement_ledger_builder.py \
      [--vintage-dir data_raw/forex_free_v3_macro] [--pin] [--offline-selftest]

``--offline-selftest`` derives the union and writes the coverage report
WITHOUT network (every event -> AVAILABILITY_UNEVIDENCED), proving the
deterministic half of the pipeline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

RUN_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_DIR = os.path.join(RUN_DIR, "announcement_archives")
LEDGER_PATH = os.path.join(RUN_DIR, "announcement_ledger.jsonl")
LEDGER_PIN_PATH = LEDGER_PATH  # pinned final name
STAGING_SUFFIX = ".staging"
MANIFEST_PATH = os.path.join(RUN_DIR, "ledger_manifest.json")

WINDOW_START = "2019-01-01"
WINDOW_END = "2026-09-02"
USER_AGENT = "my-quantitative-forex-v3r-ledger/1.0 (research evidence builder; keyless public sources)"
NY = ZoneInfo("America/New_York")

# Documented out-of-cycle / emergency decision dates (announcement date keyed
# where the decision itself was out-of-cycle).  Each flagged row still cites
# its own archived official page; this table only drives the FLAG, never the
# availability bound.
UNSCHEDULED_ANNOUNCEMENT_DATES = {
    "US": {"2020-03-03", "2020-03-15"},
    "GB": {"2020-03-19"},            # special MPC meeting, decision brought forward
    "AU": {"2020-03-03"},
    "CA": {"2020-03-13", "2020-03-27"},
}

# ---------------------------------------------------------------------------
# area adapter configuration
# ---------------------------------------------------------------------------
# history_sources: fetched once, archived, used as a union cross-check.
# parsed: whether this builder implements a mechanical parser for that source
#         (False = ARCHIVED_ONLY; an unparsed history source is honest
#         evidence of coverage intent, not a completeness proof).
# announcement_candidates(event) -> list of (kind, url):
#         kind "release_page"  expected to carry decision content; a page that
#                              verifies becomes the event's source
#         kind "listing"       a static index to locate a release link first
# schedule_claims: (url, required_substrings, tz_name, hh, mm) -- a claim that
#         the area publishes decisions at a fixed local time.  Used ONLY if
#         the fetch succeeds AND every substring is found in the archived
#         bytes; the claim row is archived and its hash cited in the ledger.

AREAS = {
    "US": {
        "name": "Federal Reserve",
        "history_sources": [
            {"url": "https://www.federalreserve.gov/monetarypolicy/openmarket.htm",
             "parsed": True,
             "require_substrings": ["target federal funds rate", "Level"]},
        ],
        # decision press release: decision day = day BEFORE the BIS effective
        # date (Fed changes take effect the day after the announcement).  Probe
        # the effective date itself too (2020-03-15 Sunday announcement,
        # 2020-03-16 effective) plus one earlier day for boundary safety.
        "announcement_candidate_offsets": (-1, 0),
        "candidate_url_builder": "fed_pr",
        "schedule_claims": [
            # Secondary only: the release line on each page is primary.
            {"url": "https://www.federalreserve.gov/monetarypolicy/fomc.htm",
             "require_substrings": [], "tz": None, "hh": None, "mm": None,
             "note": " informational archive only"},
        ],
    },
    "EMU": {
        "name": "European Central Bank",
        "history_sources": [
            {"url": "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/"
                    "key_ecb_interest_rates/html/index.en.html",
             "parsed": False,  # table exists but parser not implemented in draft
             "require_substrings": ["Key ECB interest rates", "Deposit facility"]},
        ],
        "announcement_candidate_offsets": (),   # no deterministic PR URL (hash suffix)
        "candidate_url_builder": None,
        "listing_probe": None,
        "schedule_claims": [
            {"url": "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html",
             "require_substrings": ["14:15"], "tz": "Europe/Berlin", "hh": 14, "mm": 15,
             "note": "claimed fixed publication time of GC monetary policy decisions"},
        ],
    },
    "GB": {
        "name": "Bank of England",
        "history_sources": [
            {"url": "https://www.bankofengland.co.uk/boeapps/database/"
                    "show-table.asp?TIndex=3&Start=2019-01-01&End=2026-09-02&R=1",
             "parsed": False,
             "require_substrings": ["Date"], "note": "official Bank Rate table (IADB)"},
        ],
        # Decision pages live at /monetary-policy-summary-and-minutes/YYYY/<m>-YYYY
        # with the DECISION month; BoE effective date is typically the decision
        # day or next day.  Probe the effective date and the day before.
        "announcement_candidate_offsets": (-1, 0),
        "candidate_url_builder": "boe_summary",
        "schedule_claims": [
            {"url": "https://www.bankofengland.co.uk/monetary-policy",
             "require_substrings": ["12pm", "12:00"], "tz": "Europe/London", "hh": 12, "mm": 0,
             "note": "claimed midday publication of MPC decisions; requires verification"},
        ],
    },
    "JP": {
        "name": "Bank of Japan",
        "history_sources": [],
        "announcement_candidate_offsets": (0,),
        "candidate_url_builder": None,
        "listing_probe": {
            # static per-year release list (VERIFIED 2026-09-05); the runner
            # fetches it once and selects the release dated the decision day
            "url": "https://www.boj.or.jp/en/mopo/mpmdeci/mpr_{year}/index.htm",
            "per_year": True,
        },
        "schedule_claims": [
            {"url": "https://www.boj.or.jp/en/mopo/mpmdeci/koukai/index.htm",
             "require_substrings": [], "tz": "Asia/Tokyo", "hh": None, "mm": None,
             "note": "informational archive only; BoJ states no fixed clock time"},
        ],
    },
    "CH": {
        "name": "Swiss National Bank",
        "history_sources": [
            {"url": "https://data.snb.ch/api/cube/devkum/data/csv/en",
             "parsed": False,
             "require_substrings": [], "note": "SNB policy rate cube CSV export (candidate)"},
        ],
        "announcement_candidate_offsets": (0, -1),
        "candidate_url_builder": "snb_press",
        "listing_probe": {
            "url": "https://www.snb.ch/en/publications/monetary-policy-assessments",
            "per_year": False,
        },
        "schedule_claims": [],
    },
    "CA": {
        "name": "Bank of Canada",
        "history_sources": [
            {"url": "https://www.bankofcanada.ca/valet/observations/V39079/json?start_date=2018-01-01",
             "parsed": True,
             "require_substrings": ["V39079"]},
        ],
        "announcement_candidate_offsets": (0,),
        "candidate_url_builder": None,
        "listing_probe": None,
        "schedule_claims": [
            {"url": "https://www.bankofcanada.ca/press/",
             "require_substrings": ["10:00"], "tz": "America/Toronto", "hh": 10, "mm": 0,
             "note": "claimed fixed 10:00 ET announcement time; requires verification"},
        ],
    },
    "AU": {
        "name": "Reserve Bank of Australia",
        "history_sources": [
            {"url": "https://www.rba.gov.au/statistics/cash-rate/",
             "parsed": False,
             "require_substrings": ["Cash Rate Target", "Effective Date"]},
        ],
        "announcement_candidate_offsets": (-1,),
        "candidate_url_builder": None,
        "listing_probe": None,
        "schedule_claims": [
            {"url": "https://www.rba.gov.au/statistics/cash-rate/",
             "require_substrings": ["2.30 pm"], "tz": "Australia/Sydney", "hh": 14, "mm": 30,
             "note": "VERIFIED 2026-09-05: the page itself states releases at 2.30 pm, "
                     "effective the following day"},
        ],
    },
    "NZ": {
        "name": "Reserve Bank of New Zealand",
        "history_sources": [],
        "announcement_candidate_offsets": (0,),
        "candidate_url_builder": None,
        "listing_probe": {
            "url": "https://www.rbnz.govt.nz/monetary-policy-about-monetary-policy/"
                   "history-of-the-official-cash-rate",
            "per_year": False,
        },
        "schedule_claims": [
            {"url": "https://www.rbnz.govt.nz/monetary-policy-about-monetary-policy/"
                    "history-of-the-official-cash-rate",
             "require_substrings": ["2pm", "2pm", "14:00"], "tz": "Pacific/Auckland",
             "hh": 14, "mm": 0,
             "note": "claimed 2pm Wellington OCR release; requires verification"},
        ],
    },
}

MONTH_NAMES = {1: "january", 2: "february", 3: "march", 4: "april", 5: "may",
               6: "june", 7: "july", 8: "august", 9: "september",
               10: "october", 11: "november", 12: "december"}


# ---------------------------------------------------------------------------
# frozen-vintage event derivation
# ---------------------------------------------------------------------------
def derive_events(vintage_dir):
    """Derive the change-event union from the frozen BIS vintage files.

    Deterministic: consecutive daily rows, value change => one event.  Also
    returns per-area baseline context (the level in force at the first row).
    """
    events = []
    baselines = {}
    for area in AREAS:
        path = os.path.join(vintage_dir, f"{area}.json")
        with open(path, "r", encoding="utf-8") as handle:
            rows = json.load(handle)
        rows.sort(key=lambda r: r["effective_time_utc"])
        prev = None
        for row in rows:
            value = row["value"]
            eff = row["effective_time_utc"][:10]
            if prev is not None and value != prev[0]:
                events.append({"area": area, "effective_date": eff,
                               "old_value": prev[0], "new_value": value})
            prev = (value, eff)
        baselines[area] = {"level": rows[0]["value"],
                           "first_effective": rows[0]["effective_time_utc"][:10],
                           "n_rows": len(rows)}
    events.sort(key=lambda e: (e["area"], e["effective_date"]))
    return events, baselines


# ---------------------------------------------------------------------------
# fetch + archive + verify engine
# ---------------------------------------------------------------------------
def fetch_bytes(url, timeout=90):
    """GET with the repo UA; returns (status, content_type, raw bytes)."""
    request = urllib.request.Request(url, method="GET")
    request.add_header("User-Agent", USER_AGENT)
    request.add_header("Accept", "*/*")
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, response.headers.get_content_type(), response.read()
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (429, 500, 502, 503, 504):
                time.sleep(20 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
            time.sleep(10 * (attempt + 1))
    raise last_error if last_error else RuntimeError("unreachable")


def archive_bytes(area, decision_id, label, raw, content_type):
    """Persist exact bytes under announcement_archives/; returns relative
    path + sha256.  Everything fetched is archived, verified or not."""
    digest = hashlib.sha256(raw).hexdigest()
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", f"{area}__{decision_id}__{label}")
    name = f"{safe}.{digest[:12]}.bin"
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    path = os.path.join(ARCHIVE_DIR, name)
    if not os.path.exists(path):  # append-only archives
        with open(path, "wb") as handle:
            handle.write(raw)
    return os.path.relpath(path, RUN_DIR), digest, content_type


def page_text(raw, content_type):
    """Best-effort text for HTML/plain; PDFs return '' (bytes still archived;
    rate/date verification degrades honestly)."""
    if "pdf" in (content_type or ""):
        return ""
    for encoding in ("utf-8", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return ""


def contains_all(text, substrings):
    return all(s.lower() in text.lower() for s in substrings if s)


RATE_TOKEN_PATTERNS = [
    r"([0-9]+\.[0-9]+)\s*(?:per\s*cent|percent|%)",
    r"([0-9]+)\s*(?:per\s*cent|percent|%)",
    r"([0-9]+)[-–]([0-9]+/[0-9]+)\s*(?:per\s*cent|percent|%)",   # 2-1/4 percent
    r"([0-9]+)[½¾¼]", r"([0-9]+)\.[0-9]+\s*(?:per\s*cent|percent|%)",
]
FRACTIONS = {"¼": 0.25, "½": 0.5, "¾": 0.75, "1/4": 0.25, "1/2": 0.5, "3/4": 0.75}


def parse_rate_tokens(text):
    """Tolerant set of numeric rates mentioned as percentages (exact match
    against vintage old/new values is done by the caller)."""
    found = set()
    for value in re.findall(r"(\d+(?:[.,]\d+)?|\d+[-–]\d/\d|\d+[½¾¼])\s*(?:per\s*cent|percent|%)",
                            text, flags=re.IGNORECASE):
        token = value.replace(",", ".")
        match = re.match(r"^(\d+)[-–](\d)/(\d)$", token)
        if match:
            found.add(float(match.group(1)) + FRACTIONS.get(f"{match.group(2)}/{match.group(3)}", 0.0))
            continue
        match = re.match(r"^(\d+)([½¾¼])$", token)
        if match:
            found.add(float(match.group(1)) + FRACTIONS[match.group(2)])
            continue
        try:
            found.add(float(token))
        except ValueError:
            continue
    return found


RELEASE_TIME_RE = re.compile(
    r"(?:for release at|released at|publication.*?\bat)\s+(\d{1,2}:\d{2})\s*"
    r"(a\.?m\.?|p\.?m\.?)?\s*(?:\(?([A-Za-z]{2,5}T?)\)?)?", flags=re.IGNORECASE)


def parse_release_time(text):
    """(hh, mm, tz_token) from a page release line, or None."""
    match = RELEASE_TIME_RE.search(text)
    if not match:
        return None
    hh, mm = (int(part) for part in match.group(1).split(":"))
    meridiem = (match.group(2) or "").lower()
    if meridiem.startswith("p") and hh < 12:
        hh += 12
    if meridiem.startswith("a") and hh == 12:
        hh = 0
    return hh, mm, match.group(3)


TZ_TOKENS = {
    "EDT": "America/New_York", "EST": "America/New_York",
    "ET": "America/New_York",
    "BST": "Europe/London", "GMT": "Europe/London",
    "CEST": "Europe/Berlin", "CET": "Europe/Berlin",
    "AEDT": "Australia/Sydney", "AEST": "Australia/Sydney",
    "NZDT": "Pacific/Auckland", "NZST": "Pacific/Auckland",
    "JST": "Asia/Tokyo",
}


def local_to_utc(day, tz_name, hh, mm):
    tz = ZoneInfo(tz_name)
    local = datetime(day.year, day.month, day.day, hh, mm, tzinfo=tz)
    return local.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# candidate URL builders (deterministic probes; first VERIFIED page wins)
# ---------------------------------------------------------------------------
def fed_pr_candidates(event):
    """FOMC decision press release; decision day precedes BIS effective date.
    Returns candidate URLs in probe order."""
    eff = date.fromisoformat(event["effective_date"])
    urls = []
    for offset in (-1, 0, -3):
        day = eff + timedelta(days=offset)
        urls.append((day.isoformat(),
                     "https://www.federalreserve.gov/newsevents/pressreleases/"
                     f"monetary{day:%Y%m%d}a.htm"))
    return urls


def boe_summary_candidates(event):
    eff = date.fromisoformat(event["effective_date"])
    urls = []
    for offset in (0, -1, -2):
        day = eff + timedelta(days=offset)
        urls.append((day.isoformat(),
                     "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/"
                     f"{day.year}/{MONTH_NAMES[day.month]}-{day.year}"))
    return urls


def snb_press_candidates(event):
    eff = date.fromisoformat(event["effective_date"])
    urls = []
    for offset in (0, -1):
        day = eff + timedelta(days=offset)
        urls.append((day.isoformat(),
                     "https://www.snb.ch/en/mmr/reference/"
                     f"monet_policy_{day:%Y_%m}/source"))
    return urls


CANDIDATE_BUILDERS = {
    "fed_pr": fed_pr_candidates,
    "boe_summary": boe_summary_candidates,
    "snb_press": snb_press_candidates,
}


# ---------------------------------------------------------------------------
# decision-clock mapping
# ---------------------------------------------------------------------------
def ny_decision_instants(start_day, end_day):
    """Completed 16:00 America/New_York daily bars as UTC instants."""
    instants = []
    day = start_day
    while day <= end_day:
        instants.append(datetime(day.year, day.month, day.day, 16, 0, tzinfo=NY)
                        .astimezone(timezone.utc))
        day += timedelta(days=1)
    return instants


_DECISIONS = None


def first_readable_decision(effective_instant, available_instant):
    global _DECISIONS
    if _DECISIONS is None:
        _DECISIONS = ny_decision_instants(date(2019, 1, 1), date(2026, 9, 2))
    threshold = max(effective_instant, available_instant)
    for instant in _DECISIONS:
        if instant >= threshold:
            return instant.isoformat().replace("+00:00", "Z")
    return None


# ---------------------------------------------------------------------------
# verification per candidate
# ---------------------------------------------------------------------------
def verify_candidate(event, kind, url, schedule_ok_claim=None):
    """Fetch + archive + verify one candidate.

    Returns a result dict; NEVER raises for content problems (only for
    unexpected transport errors, which the caller degrades)."""
    status, content_type, raw = fetch_bytes(url)
    rel, digest, ctype = archive_bytes(event["area"], event["effective_date"],
                                       kind + "_" + url.split("/")[-1][:40], raw, content_type)
    text = page_text(raw, ctype)
    result = {"kind": kind, "url": url, "http_status": status,
              "archive_path": rel, "archive_sha256": digest,
              "content_type": ctype, "verified": False, "date_verified": False,
              "rate_verified": False, "release_time": None}
    if status != 200 or not raw:
        return result
    eff_day = date.fromisoformat(event["effective_date"])
    # date evidence: the candidate's own derivation day appears in the page,
    # or the URL itself encodes the day (Fed press releases) -- for listing
    # kinds the listing text must show the derived decision date.
    derived_day = date.fromisoformat(url_basis_day(event, url) or event["effective_date"])
    month_full = MONTH_NAMES[derived_day.month]
    month_abbr = month_full[:3]
    date_tokens = [
        f"{month_full} {derived_day.day}, {derived_day.year}",
        f"{derived_day.day:02d} {month_full} {derived_day.year}",
        f"{derived_day.isoformat()}",
        f"{derived_day.day:02d}.{derived_day.month:02d}.{derived_day.year}",
        f"{derived_day.day:02d} {month_abbr} {derived_day.year}",
        f"{month_abbr}. {derived_day.day}, {derived_day.year}",
    ]
    result["date_verified"] = any(token.lower() in text.lower() for token in date_tokens)
    # rate evidence: vintage old/new appear as percentage tokens
    tokens = parse_rate_tokens(text)
    needed = {float(event["old_value"]), float(event["new_value"])}
    result["rate_verified"] = bool(tokens) and needed.issubset(tokens)
    result["verified"] = result["date_verified"]
    # release time line (primary precision evidence)
    parsed = parse_release_time(text)
    if parsed and result["verified"]:
        hh, mm, tz_token = parsed
        tz_name = TZ_TOKENS.get((tz_token or "").upper())
        if tz_name:
            result["release_time"] = {
                "utc": local_to_utc(derived_day, tz_name, hh, mm)
                        .isoformat().replace("+00:00", "Z"),
                "basis": f"page release line ({tz_token})",
            }
                # a release line is bound to the decision day (page date)
    return result


def url_basis_day(event, url):
    match = re.search(r"(\d{8})\.htm", url)   # Fed monetaryYYYYMMDDa.htm
    if match:
        return f"{match.group(1)[:4]}-{match.group(1)[4:6]}-{match.group(1)[6:]}"
    match = re.search(r"(\d{6})[a-z]?\.(?:htm|pdf)", url)  # BoJ k240319a.htm
    if match:
        raw = match.group(1)
        return f"20{raw[:2]}-{raw[2:4]}-{raw[4:6]}"
    return None


# ---------------------------------------------------------------------------
# schedule claims (verified once per area, archived, then applied per event)
# ---------------------------------------------------------------------------
def verify_schedule_claims(area, config):
    verified = []
    for claim in config.get("schedule_claims", []):
        if not claim.get("hh") or not claim.get("tz"):
            continue
        try:
            status, ctype, raw = fetch_bytes(claim["url"])
        except Exception:  # noqa: BLE001 - degradation is the designed path
            continue
        text = page_text(raw, ctype)
        if status == 200 and claim["require_substrings"] and \
                not contains_all(text, claim["require_substrings"]):
            continue
        rel, digest, _ = archive_bytes(area, "SCHEDULE_CLAIM",
                                       claim["url"].split("/")[-1][:40], raw, ctype)
        verified.append({**claim, "archive_path": rel, "archive_sha256": digest,
                         "verified": True})
    return verified


# ---------------------------------------------------------------------------
# per-event evidence assembly
# ---------------------------------------------------------------------------
def end_of_day_utc(day):
    return (datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=timezone.utc)
            .isoformat().replace("+00:00", "Z"))


def build_row(event, baselines, schedule_by_area, offline=False):
    area = event["area"]
    config = AREAS[area]
    eff_day = date.fromisoformat(event["effective_date"])
    effective_instant = datetime(eff_day.year, eff_day.month, eff_day.day,
                                 tzinfo=timezone.utc)
    row = {
        "schema": "forex_free_v3r_announcement_ledger_row_v1",
        "row_type": "RATE_CHANGE",
        "area": area,
        "area_name": config["name"],
        "decision_id": f"{area}:{event['effective_date']}",
        "effective_date": event["effective_date"],
        "effective_time_utc": effective_instant.isoformat().replace("+00:00", "Z"),
        "old_value": event["old_value"],
        "new_value": event["new_value"],
        "bis_publication_stamp": None,   # none exists historically; explicit
        "announcement": None,
        "old_bound_end_of_effective_day": end_of_day_utc(eff_day),
    }
    evidence = None
    if not offline:
        builder = config.get("candidate_url_builder")
        if builder:
            for derived_day, url in CANDIDATE_BUILDERS[builder](event):
                try:
                    candidate = verify_candidate(event, "release_page", url)
                except Exception as exc:  # noqa: BLE001 - degrade, never abort the ledger
                    candidate = {"kind": "release_page", "url": url, "verified": False,
                                 "error": repr(exc)}
                if candidate.get("verified"):
                    evidence = candidate
                    break
        listing = config.get("listing_probe")
        if evidence is None and listing:
            evidence = probe_listing(config, event, listing)
    if evidence:
        announcement_day = date.fromisoformat(
            url_basis_day(event, evidence["url"]) or event["effective_date"])
        if evidence.get("release_time"):
            instant = evidence["release_time"]["utc"]
            precision, time_source = "INSTANT", "PAGE_RELEASE_LINE"
        elif any(c.get("verified") for c in schedule_by_area.get(area, [])):
            claim = next(c for c in schedule_by_area[area] if c.get("verified"))
            instant = local_to_utc(announcement_day, claim["tz"], claim["hh"], claim["mm"]) \
                .isoformat().replace("+00:00", "Z")
            precision, time_source = "INSTANT", "OFFICIAL_FIXED_SCHEDULE"
        else:
            instant = end_of_day_utc(announcement_day)
            precision, time_source = "DAY", "DAY_CONSERVATIVE"
        status = "EVIDENCED"
    else:
        announcement_day = None
        instant = None
        precision = time_source = None
        status = "AVAILABILITY_UNEVIDENCED"
    unscheduled = bool(announcement_day
                       and announcement_day.isoformat()
                       in UNSCHEDULED_ANNOUNCEMENT_DATES.get(area, set()))
    # operative availability bound: never earlier than the LATER-of rule for
    # unevidenced events; evidenced instants stand as evidenced.
    if status == "EVIDENCED":
        available = instant
    else:
        bis_stamp = row["bis_publication_stamp"]
        candidates = [row["old_bound_end_of_effective_day"]]
        if bis_stamp:
            candidates.append(bis_stamp)
        available = max(candidates)
    row["announcement"] = {
        "status": status,
        "announcement_date": announcement_day.isoformat() if announcement_day else None,
        "announcement_time_utc": instant if precision == "INSTANT" else None,
        "operative_available_time_utc": available,
        "precision": precision,
        "time_source": time_source,
        "source_url": evidence["url"] if evidence else None,
        "archive_path": evidence["archive_path"] if evidence else None,
        "archive_sha256": evidence["archive_sha256"] if evidence else None,
        "date_verified": bool(evidence and evidence.get("date_verified")),
        "rate_verified": bool(evidence and evidence.get("rate_verified")),
        "schedule_claim_archive": schedule_by_area.get(area, []),
        "unscheduled": unscheduled,
        "unscheduled_basis": ("documented out-of-cycle decision date; see archived page"
                              if unscheduled else None),
    }
    row["first_readable_decision_utc"] = first_readable_decision(
        effective_instant,
        datetime.fromisoformat(available.replace("Z", "+00:00")))
    row["old_bound_first_readable_decision_utc"] = first_readable_decision(
        effective_instant,
        datetime.fromisoformat(row["old_bound_end_of_effective_day"].replace("Z", "+00:00")))
    return row


def probe_listing(config, event, listing):
    """Fetch a static listing page and select a release link for the event's
    decision day (BoJ year index pattern).  The listing itself is archived;
    a selected link is fetched and verified like a release page."""
    area = event["area"]
    eff_day = date.fromisoformat(event["effective_date"])
    years = {eff_day.year}
    url = listing["url"].format(year=eff_day.year)
    try:
        status, ctype, raw = fetch_bytes(url)
    except Exception as exc:  # noqa: BLE001
        return {"kind": "listing", "url": url, "verified": False, "error": repr(exc)}
    rel, digest, _ = archive_bytes(area, event["effective_date"], "listing", raw, ctype)
    text = page_text(raw, ctype)
    if status != 200:
        return {"kind": "listing", "url": url, "verified": False,
                "archive_path": rel, "archive_sha256": digest}
    # find links whose neighbouring text shows the decision day
    links = re.findall(r'href="([^"]+)"[^>]*>([^<]{0,120})', text, flags=re.IGNORECASE)
    day_tokens = {eff_day.strftime(fmt).lower() for fmt in
                  ("%Y-%m-%d", "%b. %d, %Y", "%B %d, %Y", "%d %B %Y")}
    for href, label in links:
        if not any(token in label.lower() for token in day_tokens):
            continue
        if "http" in href:
            link = href
        elif href.startswith("/"):
            link = f"https://www.boj.or.jp{href}" if "boj" in listing["url"] else None
        else:
            base = listing["url"].rsplit("/", 1)[0]
            link = f"{base}/{href}"
        if not link:
            continue
        try:
            candidate = verify_candidate(event, "release_page", link)
        except Exception as exc:  # noqa: BLE001
            continue
        if candidate.get("verified"):
            candidate["listing"] = {"url": url, "archive_path": rel,
                                    "archive_sha256": digest}
            return candidate
    return {"kind": "listing", "url": url, "verified": False,
            "archive_path": rel, "archive_sha256": digest,
            "note": "listing archived; no release link matched the decision day"}


# ---------------------------------------------------------------------------
# baseline rows
# ---------------------------------------------------------------------------
def build_baseline_row(area, baselines, schedule_by_area):
    config = AREAS[area]
    level = baselines[area]["level"]
    first_eff = baselines[area]["first_effective"]
    first_day = date.fromisoformat(first_eff)
    row = {
        "schema": "forex_free_v3r_announcement_ledger_row_v1",
        "row_type": "BASELINE_LEVEL",
        "area": area,
        "area_name": config["name"],
        "decision_id": f"{area}:BASELINE:{first_eff}",
        "effective_date": None,          # pre-window establishing event, not dated here
        "effective_time_utc": None,
        "old_value": None,
        "new_value": level,
        "bis_publication_stamp": None,
        "baseline_note": (
            "level in force from the first frozen vintage row; the establishing "
            "pre-window change is evidenced only if the run finds it; its "
            "availability cannot change any readable value inside the window "
            "(the level is constant at window start), so the conservative bound "
            "is the V3 baseline end-of-first-vintage-day and is NOT "
            "computationally load-bearing"),
        "announcement": {
            "status": "AVAILABILITY_UNEVIDENCED",
            "announcement_date": None,
            "announcement_time_utc": None,
            "operative_available_time_utc": end_of_day_utc(first_day),
            "precision": None,
            "time_source": None,
            "source_url": None,
            "archive_path": None,
            "archive_sha256": None,
            "date_verified": False,
            "rate_verified": False,
            "schedule_claim_archive": schedule_by_area.get(area, []),
            "unscheduled": False,
            "unscheduled_basis": None,
        },
        "first_readable_decision_utc": None,
        "old_bound_first_readable_decision_utc": None,
    }
    return row


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vintage-dir", default="data_raw/forex_free_v3_macro")
    parser.add_argument("--pin", action="store_true",
                        help="after writing staging artifacts, promote them to the "
                             "pinned final names (append-only: refuses to overwrite "
                             "an existing pinned ledger)")
    parser.add_argument("--offline-selftest", action="store_true",
                        help="no network: derive the union, write an all-unevidenced "
                             "staging ledger + coverage report")
    args = parser.parse_args()

    events, baselines = derive_events(args.vintage_dir)
    coverage = {
        "derived_by": "frozen vintage value-change scan",
        "window": [WINDOW_START, WINDOW_END],
        "per_area": {},
    }
    for area in AREAS:
        area_events = [e for e in events if e["area"] == area]
        coverage["per_area"][area] = {
            "n_rows": baselines[area]["n_rows"],
            "baseline_level": baselines[area]["level"],
            "changes_in_window": len(area_events),
            "first_change_effective": area_events[0]["effective_date"] if area_events else None,
            "last_change_effective": area_events[-1]["effective_date"] if area_events else None,
        }
    coverage["total_change_events"] = len(events)
    print(json.dumps({"coverage": coverage}, indent=1))

    schedule_by_area = {}
    if not args.offline_selftest:
        for area, config in AREAS.items():
            schedule_by_area[area] = verify_schedule_claims(area, config)

    rows = []
    for event in events:
        rows.append(build_row(event, baselines, schedule_by_area,
                              offline=args.offline_selftest))
    for area in AREAS:
        rows.append(build_baseline_row(area, baselines, schedule_by_area))

    statuses = {}
    for row in rows:
        statuses[row["announcement"]["status"]] = \
            statuses.get(row["announcement"]["status"], 0) + 1

    manifest = {
        "schema": "forex_free_v3r_announcement_ledger_manifest_v1",
        "built_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "offline_selftest": args.offline_selftest,
        "n_rows": len(rows),
        "n_change_events": len(events),
        "n_baseline_rows": len(AREAS),
        "status_counts": statuses,
        "coverage": coverage,
        "note": "staging artifacts are unpinned; --pin promotes to the final "
                "append-only names after review",
    }

    with open(LEDGER_PATH + STAGING_SUFFIX, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False) + "\n")
    ledger_staging_bytes = open(LEDGER_PATH + STAGING_SUFFIX, "rb").read()
    manifest["ledger_sha256"] = hashlib.sha256(ledger_staging_bytes).hexdigest()
    with open(MANIFEST_PATH + STAGING_SUFFIX, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1, sort_keys=True)

    if args.pin:
        if os.path.exists(LEDGER_PIN_PATH):
            raise SystemExit("REFUSING_TO_OVERWRITE_PINNED_LEDGER (append-only)")
        os.replace(LEDGER_PATH + STAGING_SUFFIX, LEDGER_PIN_PATH)
        os.replace(MANIFEST_PATH + STAGING_SUFFIX, MANIFEST_PATH)
        with open(os.path.join(RUN_DIR, "LEDGER_PINNED"), "w") as handle:
            handle.write(json.dumps({"ledger_sha256": manifest["ledger_sha256"],
                                     "pinned_at_utc": manifest["built_at_utc"]},
                                    indent=1, sort_keys=True))
    print(json.dumps({"n_rows": len(rows), "statuses": statuses,
                      "ledger_sha256_staging": manifest["ledger_sha256"],
                      "pinned": bool(args.pin)}))


if __name__ == "__main__":
    sys.exit(main())
