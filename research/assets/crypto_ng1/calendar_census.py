"""CRYPTO-NG1 P0 announcement-instant census (official, keyless).

Collects OFFICIAL publication calendars for scheduled US macro prints
inside the panel window: the Federal Reserve FOMC meeting calendar plus
the per-meeting FOMC statement pages (which carry the official
"For release at h:mm a.m./p.m. EST/EDT" publication timestamp), and the
BLS release schedules for CPI and The Employment Situation (NFP).

Fail-closed rules:

- an instant is accepted ONLY when the official publication timestamp
  (date + time-of-day + zone abbreviation) is present on the official
  page; anything missing is dropped, never inferred;
- a stated zone abbreviation (EST/EDT) must agree with the actual IANA
  offset for that date (DST-aware), otherwise the instant is refused;
- canaries (P-7) are mandatory: nonexistent series probes must be
  refused and a fabricated calendar day must fail to produce an instant;
- fetch etiquette: at most 3 attempts per URL with backoff; definitive
  4xx denials are recorded immediately (no hammering); a source that
  cannot be retrieved is recorded BLOCKED, never fabricated.

Pure parsing/conversion helpers are network-free and unit-tested with
hand-computed fixtures (tests/test_crypto_ng1_p0.py).
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo

SCHEMA = "crypto_ng1_run/p0_calendar_census@1"

FOMC_CALENDAR_URL = (
    "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm")
BLS_SCHEDULE_URLS = {
    "CPI": "https://www.bls.gov/schedule/news_release/cpi.htm",
    "NFP": "https://www.bls.gov/schedule/news_release/empsit.htm",
}
FUNDING_RATE_URL = (
    "https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1000")

SERIES_FOMC_DECISION = "US-MACRO/FOMC_DECISION"

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
    "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
}

_YEAR_SECTION_RE = re.compile(
    r"(\d{4}) FOMC Meetings</a></h4>(.*?)(?=\d{4} FOMC Meetings</a></h4>"
    r"|<div class=\"panel panel-default footnotes|\Z)", re.S)
_MEETING_RE = re.compile(
    r"fomc-meeting__month[^>]*>\s*<strong>([A-Z][a-z]+)</strong>\s*</div>\s*"
    r"<div class=\"fomc-meeting__date[^\"]*\">\s*(\d{1,2})-(\d{1,2})(\*?)"
    r"\s*</div>")
_FOR_RELEASE_RE = re.compile(
    r"For release at\s+(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(EST|EDT|ET)\b")
_ARTICLE_DATE_RE = re.compile(
    r'article__time[^>]*>\s*((?:January|February|March|April|May|June|July|'
    r'August|September|October|November|December)\s+\d{1,2},\s+\d{4})\s*<')
_ANY_DATE_RE = re.compile(
    r'((?:January|February|March|April|May|June|July|August|September|'
    r'October|November|December)\s+\d{1,2},\s+\d{4})')

_TZ_NEW_YORK = "America/New_York"


# --------------------------------------------------------------------- #
# fetch layer (etiquette: <=3 attempts per URL, backoff, no hammering)  #
# --------------------------------------------------------------------- #
def fetch_url(url: str, max_attempts: int = 3, timeout: float = 25.0,
              backoff_s: tuple[float, float] = (1.5, 4.0)) -> dict:
    """Fetch one URL politely.  Retries only on network errors and 5xx;
    a definitive 4xx is recorded immediately.  Returns a measurement
    record, never raises for HTTP outcomes."""
    attempts: list[dict] = []
    body: str | None = None
    status: int | None = None
    for i in range(1, max_attempts + 1):
        retrieved = datetime.now(timezone.utc).isoformat()
        err: str | None = None
        try:
            req = urllib.request.Request(
                url, headers={
                    "User-Agent": _USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,"
                              "application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
                raw = resp.read()
                body = raw.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            status = exc.code
            err = f"HTTPError {exc.code}"
        except Exception as exc:                    # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
            status = None
        attempts.append({"attempt": i, "retrieved_utc": retrieved,
                         "status": status, "error": err})
        # definitive denial (4xx) or success: stop, do not hammer
        if status is not None and not (500 <= status < 600):
            break
        if status is not None and 500 <= status < 600 and i < max_attempts:
            time.sleep(backoff_s[min(i - 1, len(backoff_s) - 1)])
        elif status is None and i < max_attempts:
            time.sleep(backoff_s[min(i - 1, len(backoff_s) - 1)])
    ok = status is not None and 200 <= status < 300 and body is not None
    return {"url": url, "ok": ok, "status": status, "attempts": attempts,
            "body": body if ok else None,
            "retrieved_utc": attempts[-1]["retrieved_utc"] if attempts
            else None}


# --------------------------------------------------------------------- #
# parsers (pure, unit-tested)                                           #
# --------------------------------------------------------------------- #
def month_number(name: str) -> int:
    key = name.strip().lower()
    if key not in _MONTHS:
        raise ValueError(f"unknown month name: {name!r}")
    return _MONTHS[key]


def parse_fomc_meetings(html: str) -> list[dict]:
    """Parse year sections + meeting rows from the FOMC calendar page."""
    meetings: list[dict] = []
    for year_m in _YEAR_SECTION_RE.finditer(html):
        year = int(year_m.group(1))
        for m in _MEETING_RE.finditer(year_m.group(2)):
            month = month_number(m.group(1))
            first_day, last_day = int(m.group(2)), int(m.group(3))
            meetings.append({
                "year": year, "month": month,
                "first_day": first_day, "last_day": last_day,
                "decision_day": f"{year:04d}-{month:02d}-{last_day:02d}",
                "sep_projection": m.group(4) == "*",
            })
    return meetings


def statement_url(decision_day: date) -> str:
    return ("https://www.federalreserve.gov/newsevents/pressreleases/"
            f"monetary{decision_day.strftime('%Y%m%d')}a.htm")


def parse_release_instant(html: str) -> dict | None:
    """Extract the official 'For release at h:mm a.m./p.m. ZONE' line."""
    m = _FOR_RELEASE_RE.search(html)
    if m is None:
        return None
    return {"hour": int(m.group(1)), "minute": int(m.group(2)),
            "meridiem": m.group(3), "zone": m.group(4),
            "text": " ".join(m.group(0).split())}


def parse_statement_date(html: str) -> date | None:
    """The article's own publication date (article__time element first)."""
    m = _ARTICLE_DATE_RE.search(html)
    if m is None:
        m = _ANY_DATE_RE.search(html)
    if m is None:
        return None
    return datetime.strptime(m.group(1), "%B %d, %Y").date()


def local_to_utc(day: date, hour: int, minute: int, meridiem: str,
                 zone_abbr: str, tz_name: str = _TZ_NEW_YORK) -> str:
    """Convert an official local publication time to UTC (DST-aware).

    Fail-closed: the stated zone abbreviation must agree with the actual
    IANA offset on that date (EDT = UTC-4, EST = UTC-5; bare ET accepts
    either); a disagreement refuses the instant instead of guessing.
    """
    hour24 = hour % 12 + (12 if meridiem == "p" else 0)
    local = datetime(day.year, day.month, day.day, hour24, minute,
                     tzinfo=ZoneInfo(tz_name))
    offset = local.utcoffset()
    total = int(offset.total_seconds()) if offset else 0
    hours_off = total // 3600
    expected = {"EDT": -4, "EST": -5}.get(zone_abbr)
    if expected is not None and hours_off != expected:
        raise ValueError(
            f"zone mismatch: {day} {zone_abbr} stated but "
            f"{tz_name} offset is {hours_off:+d}h (DST check failed)")
    return local.astimezone(timezone.utc).isoformat()


def make_instant(series: str, scheduled_utc: str, source_url: str,
                 retrieved_utc: str, evidence: dict) -> dict:
    return {"series": series, "scheduled_utc": scheduled_utc,
            "source_url": source_url, "retrieved_utc": retrieved_utc,
            "evidence": evidence}


# --------------------------------------------------------------------- #
# census runner                                                         #
# --------------------------------------------------------------------- #
def run_census(window_start: date, window_end: date,
               fetch: Callable[[str], dict] = fetch_url,
               verdict_fn: Callable[[str], str] | None = None,
               fabricated_day: date | str = "2026-02-14",
               now_utc: str | None = None) -> dict:
    """Collect official announcement instants inside the panel window.

    ``verdict_fn`` is the plane adapter's authority-verdict function used
    for the P-7 series-name canaries (two nonexistent series must be
    refused).  The fabricated calendar day canary must fail to produce
    an instant.
    """
    measured_utc = now_utc or datetime.now(timezone.utc).isoformat()

    # ---- source 1: FOMC calendar + statement publication timestamps -- #
    fomc_sources: dict[str, dict] = {}
    cal = fetch(FOMC_CALENDAR_URL)
    fomc_sources[FOMC_CALENDAR_URL] = cal
    instants: list[dict] = []
    dropped: list[dict] = []
    meetings_in_window: list[dict] = []
    if cal["ok"]:
        meetings = parse_fomc_meetings(cal["body"])
        for mtg in meetings:
            day = date.fromisoformat(mtg["decision_day"])
            if window_start <= day <= window_end:
                meetings_in_window.append(mtg)
                resp = fetch(statement_url(day))
                fomc_sources[resp["url"]] = resp
                if not resp["ok"]:
                    dropped.append({
                        "meeting": mtg, "source_url": resp["url"],
                        "reason": f"statement page not retrievable "
                                  f"(status={resp['status']})"})
                    continue
                rel = parse_release_instant(resp["body"])
                page_date = parse_statement_date(resp["body"])
                if rel is None or page_date is None:
                    dropped.append({
                        "meeting": mtg, "source_url": resp["url"],
                        "reason": "no official release timestamp on page "
                                  "(dropped, never inferred)"})
                    continue
                if page_date != day:
                    dropped.append({
                        "meeting": mtg, "source_url": resp["url"],
                        "reason": f"page date {page_date} != decision day "
                                  f"{day} (three-way check failed)"})
                    continue
                try:
                    scheduled_utc = local_to_utc(
                        page_date, rel["hour"], rel["minute"],
                        rel["meridiem"], rel["zone"])
                except ValueError as exc:
                    dropped.append({"meeting": mtg, "source_url": resp["url"],
                                    "reason": f"fail-closed: {exc}"})
                    continue
                local_dt = (f"{rel['hour']}:{rel['minute']:02d} "
                            f"{rel['meridiem']}.m. {rel['zone']}")
                instants.append(make_instant(
                    SERIES_FOMC_DECISION, scheduled_utc, resp["url"],
                    resp["retrieved_utc"], {
                        "for_release_text": rel["text"],
                        "local_time": local_dt,
                        "page_date": page_date.isoformat(),
                        "meeting": (f"{mtg['year']}-{mtg['month']:02d} "
                                    f"days {mtg['first_day']}-{mtg['last_day']}"
                                    f"{'*' if mtg['sep_projection'] else ''}"),
                        "calendar_url": FOMC_CALENDAR_URL,
                        "calendar_retrieved_utc": cal["retrieved_utc"],
                    }))
    fomc_ok = cal["ok"] and bool(instants)

    # ---- source 2: BLS release schedules (CPI / NFP) ----------------- #
    bls_sources: list[dict] = []
    bls_all_blocked = True
    for series, url in BLS_SCHEDULE_URLS.items():
        resp = fetch(url)
        blocked = not resp["ok"]
        bls_sources.append({
            "series": series, "url": url, "status":
                "BLOCKED" if blocked else "RETRIEVED",
            "http_status": resp["status"], "attempts": resp["attempts"],
            "note": ("no instants fabricated; BLS web denied retrieval "
                     "(definitive 4xx / network denial)" if blocked else
                     "schedule retrieved; instants must still carry "
                     "official publication timestamps"),
        })
        if not blocked:
            bls_all_blocked = False
        if blocked:
            # domain-level denial observed: do not hammer the sibling URL
            break

    # ---- canaries (P-7, mandatory) ------------------------------------ #
    canary_series = [
        {"series": "S4:binance-funding-settlements",
         "expected": "REFUSED (not GRANTED)"},
        {"series": "S9:not-a-real-series",
         "expected": "REFUSED (not GRANTED)"},
    ]
    series_canaries = []
    for c in canary_series:
        if verdict_fn is None:
            series_canaries.append({**c, "observed": "NOT_RUN (no verdict_fn)",
                                    "verdict": "NOT_RUN"})
            continue
        v = verdict_fn(c["series"])
        refused = v != "GRANTED"
        series_canaries.append({
            **c, "observed": f"verdict={v!r}", "refused": refused,
            "verdict": "PASS" if refused else "FAIL"})

    fab = fabricated_day
    fab_day = (date.fromisoformat(fab) if isinstance(fab, str) else fab)
    fab_url = statement_url(fab_day)
    fab_resp = fetch(fab_url)
    fab_rel = (parse_release_instant(fab_resp["body"])
               if fab_resp["ok"] else None)
    fab_instant = None
    if fab_rel is not None:
        fab_page_date = parse_statement_date(fab_resp["body"])
        if fab_page_date == fab_day:
            try:
                fab_instant = local_to_utc(
                    fab_day, fab_rel["hour"], fab_rel["minute"],
                    fab_rel["meridiem"], fab_rel["zone"])
            except ValueError:
                fab_instant = None
    fabricated_day_canary = {
        "fabricated_day": fab_day.isoformat(),
        "source_url": fab_url,
        "http_status": fab_resp["status"],
        "attempts": fab_resp["attempts"],
        "expected": "FAIL (no instant may be produced for a fabricated day)",
        "observed": ("instant produced!"
                     if fab_instant else "no instant produced"),
        "verdict": "FAIL" if fab_instant else "PASS",
    }
    canaries_ok = (
        fabricated_day_canary["verdict"] == "PASS"
        and all(sc["verdict"] == "PASS" for sc in series_canaries))

    # ---- verdict ------------------------------------------------------ #
    any_source_ok = fomc_ok or not bls_all_blocked
    if not any_source_ok:
        verdict = "BLOCKED_ALL_SOURCES_FAILED"
    elif not canaries_ok:
        verdict = "FAIL_CANARIES"
    elif fomc_ok:
        verdict = "PASS_WITH_BLS_BLOCKED" if bls_all_blocked else "PASS"
    else:
        verdict = "BLOCKED_NO_INSTANTS"

    return {
        "schema": SCHEMA,
        "measured_utc": measured_utc,
        "window": {"start": window_start.isoformat(),
                   "end": window_end.isoformat()},
        "sources": {
            "fomc": {
                "calendar_url": FOMC_CALENDAR_URL,
                "status": "PASS" if fomc_ok else
                          ("BLOCKED" if not cal["ok"] else "NO_INSTANTS"),
                "urls_measured": len(fomc_sources),
                "http_measurements": {
                    u: {"status": r["status"],
                        "attempts": len(r["attempts"])}
                    for u, r in fomc_sources.items()},
            },
            "bls": {"status": "BLOCKED" if bls_all_blocked else "PARTIAL",
                    "probes": bls_sources},
        },
        "meetings_in_window": len(meetings_in_window),
        "instants": instants,
        "dropped": dropped,
        "canaries": {"series_probes": series_canaries,
                     "fabricated_day": fabricated_day_canary},
        "instant_count": len(instants),
        "verdict": verdict,
    }


# --------------------------------------------------------------------- #
# funding re-proof (OPTIONAL probe, never a blocker)                    #
# --------------------------------------------------------------------- #
def funding_reproof(symbols: list[str],
                    fetch_json: Callable[[str], dict] | None = None,
                    timeout: float = 15.0) -> dict:
    """Keyless public fapi fundingRate availability probe.

    This PROBES endpoint availability only: nothing is consumed, nothing
    enters CADS, and D1 lanes do not need funding data.  Failure is
    recorded BLOCKED_NOT_CONSUMED and never blocks the gate.
    """
    def _default(url: str) -> dict:
        retrieved = datetime.now(timezone.utc).isoformat()
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": _USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            return {"ok": True, "status": resp.status, "payload": payload,
                    "retrieved_utc": retrieved}
        except Exception as exc:                    # noqa: BLE001
            return {"ok": False, "status": None,
                    "error": f"{type(exc).__name__}: {exc}",
                    "retrieved_utc": retrieved}

    fetch = fetch_json or _default
    probes = []
    for sym in symbols:
        r = fetch(FUNDING_RATE_URL.format(symbol=sym))
        rows = r.get("payload") or []
        probe = {
            "symbol": sym, "url": FUNDING_RATE_URL.format(symbol=sym),
            "ok": bool(r["ok"] and isinstance(rows, list) and rows),
            "http_status": r.get("status"),
            "rows_observed": len(rows) if isinstance(rows, list) else 0,
            "retrieved_utc": r.get("retrieved_utc"),
        }
        if probe["ok"]:
            times = sorted(int(x["fundingTime"]) for x in rows)
            probe["funding_time_min_ms"] = times[0]
            probe["funding_time_max_ms"] = times[-1]
            probe["funding_time_max_utc"] = datetime.fromtimestamp(
                times[-1] / 1000.0, tz=timezone.utc).isoformat()
        else:
            probe["error"] = r.get("error")
        probes.append(probe)
    all_ok = all(p["ok"] for p in probes)
    return {
        "schema": "crypto_ng1_run/p0_funding_reproof@1",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "note": "OPTIONAL keyless availability probe only; not consumed "
                "by any lane; non-blocking",
        "probes": probes,
        "status": "KEYLESS_ENDPOINT_PROVEN" if all_ok
                  else "BLOCKED_NOT_CONSUMED",
    }
