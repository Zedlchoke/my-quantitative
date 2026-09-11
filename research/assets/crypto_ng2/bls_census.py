"""CRYPTO-NG2 P0 BLS announcement-instant census (browser-class plan, lane A4).

Objective (plans/PLAN_crypto_ng2.md sections 2-3): CPI + NFP scheduled
release instants for the panel window 2025-08-22..2026-08-21, retrieved
from the OFFICIAL BLS schedule pages by a browser-class fetch
(``WebFetch`` tool, fallback browser-use skill) because curl-class
retrieval was Akamai-403-blocked at ng1.

Fail-closed rules (identical spirit to ng1 calendar_census):

- an instant is accepted ONLY when the official schedule row carries the
  full publication timestamp (calendar date + time-of-day + meridiem;
  zone ET per the plan's ``8:30 ET`` standard when the row omits it);
  anything missing is dropped, never inferred;
- a stated zone abbreviation (EST/EDT) must agree with the actual IANA
  offset for that date (DST-aware, reused from the ng1 module by import);
  bare ET accepts either offset;
- a stated weekday must agree with the date's real weekday and BLS print
  dates must be weekdays; disagreement refuses the row;
- canaries (P-7) are mandatory: 2 fabricated calendar days must FAIL to
  produce instants and 1 nonexistent series must be REFUSED by the
  authority registry;
- fetch etiquette: at most 3 attempts per URL with backoff, <= 5 URLs per
  source, definitive 4xx denials recorded immediately (no hammering, no
  sibling-URL hammering after a domain-level denial); a source that
  cannot be retrieved is recorded BLOCKED_PER_SOURCE, never fabricated.

The retrieval-method chain is recorded per source: ``curl_class`` is
always measured; ``webfetch_tool`` and ``browser_use_skill`` record their
availability in this lane (NOT_RUN with the exact reason when the tool is
not executable by a subagent lane).
"""

from __future__ import annotations

import html as _html
import json
import re
import urllib.request
from datetime import date, datetime, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo

# -- inherited ng1 machinery: IMPORT ONLY, never modified ---------------- #
from research.assets.crypto_ng1.calendar_census import (
    fetch_url as curl_class_fetch,
    local_to_utc,
    month_number,
)

SCHEMA = "crypto_ng2_run/p0_bls_census@1"
FUNDING_PROBE_SCHEMA = "crypto_ng2_run/p0_funding_probe@1"

#: official BLS release-schedule pages (news-release schedule surface)
BLS_SCHEDULE_URLS = {
    "CPI": "https://www.bls.gov/schedule/news_release/cpi.htm",
    "NFP": "https://www.bls.gov/schedule/news_release/empsit.htm",
}
#: alternate historical pattern named by the dispatch packet (CPI only)
BLS_ALTERNATE_URLS = {
    "CPI": "https://www.bls.gov/bls/news-release/cpi.htm",
}

SERIES_BY_RELEASE = {
    "CPI": "US-MACRO/BLS_CPI_RELEASE",
    "NFP": "US-MACRO/BLS_EMPLOYMENT_SITUATION_RELEASE",
}
#: the row's release text must name the expected release (guards against
#: cross-contaminated rows on a combined page)
_RELEASE_TITLE_RE = {
    "CPI": re.compile(r"consumer\s+price\s+index", re.I),
    "NFP": re.compile(r"employment\s+situation", re.I),
}

#: plan section 3 fixes the BLS print clock standard: 8:30 ET.
PLAN_PRINT_CLOCK = "8:30 ET"

FUNDING_RATE_URL = (
    "https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1000")

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

_TZ_NEW_YORK = "America/New_York"

_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL_RE = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.S | re.I)
_DATE_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),\s*(\d{4})\b", re.I)
_TIME_RE = re.compile(
    r"\b(\d{1,2}):(\d{2})\s*(a\.?m\.?|p\.?m\.?)\s*\b\s*(ET|EDT|EST)?\b",
    re.I)
_WEEKDAY_RE = re.compile(
    r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    re.I)
_WEEKDAY_NUM = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


# --------------------------------------------------------------------- #
# parsers (pure, network-free, unit-tested in tests/test_crypto_ng2_p0.py)
# --------------------------------------------------------------------- #
def _clean(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = _html.unescape(text)
    return " ".join(text.split())


def _meridiem(token: str) -> str:
    norm = token.lower().replace(".", "")
    return "a" if norm.startswith("a") else "p"


def _zone(token: str | None) -> str | None:
    if token is None:
        return None
    z = token.upper().rstrip(".")
    return z if z in ("ET", "EDT", "EST") else None


def parse_schedule_rows(page_html: str) -> list[dict]:
    """Extract candidate release rows (date + optional time/weekday/release
    text) from a BLS schedule page.  Pure; no network, no clock."""
    rows: list[dict] = []
    seen: set[tuple] = set()
    for row_m in _ROW_RE.finditer(page_html):
        cells = [_clean(c) for c in _CELL_RE.findall(row_m.group(1))]
        if not cells:
            continue
        joined = " | ".join(cells)
        dm = _DATE_RE.search(joined)
        if dm is None:
            continue
        try:
            day = date(int(dm.group(3)), month_number(dm.group(1)),
                       int(dm.group(2)))
        except ValueError:
            rows.append({"raw": joined, "invalid_date": dm.group(0)})
            continue
        key = (day.isoformat(), joined)
        if key in seen:
            continue
        seen.add(key)
        tm = _TIME_RE.search(joined)
        wm = _WEEKDAY_RE.search(joined)
        rows.append({
            "date": day,
            "date_text": dm.group(0),
            "time_text": tm.group(0) if tm else None,
            "hour": int(tm.group(1)) if tm else None,
            "minute": int(tm.group(2)) if tm else None,
            "meridiem": _meridiem(tm.group(3)) if tm else None,
            "zone": _zone(tm.group(4)) if tm else None,
            "weekday_stated": wm.group(1).lower() if wm else None,
            "release_text": joined,
        })
    return rows


def parse_bls_instants(page_html: str, release_key: str, source_url: str,
                       retrieved_utc: str | None, method: str,
                       window_start: date, window_end: date) -> tuple[
                           list[dict], list[dict], int]:
    """Turn parsed schedule rows into instants (fail-closed).

    Returns (instants, dropped, rows_in_window).  A row yields an instant
    ONLY when: it names the expected release, its date is a weekday inside
    the window, any stated weekday matches the real weekday, and the full
    time-of-day is present; the zone defaults to ET (plan ``8:30 ET``
    standard) when the row omits it, recorded in the evidence."""
    instants: list[dict] = []
    dropped: list[dict] = []
    in_window = 0
    title_re = _RELEASE_TITLE_RE[release_key]
    for row in parse_schedule_rows(page_html):
        if "invalid_date" in row:
            continue                      # malformed calendar text: never a row
        day = row["date"]
        if not (window_start <= day <= window_end):
            continue
        in_window += 1
        base = {"date": day.isoformat(), "row_text": row["release_text"],
                "source_url": source_url}
        if not title_re.search(row["release_text"]):
            dropped.append({**base, "reason":
                            "release text does not name the expected "
                            f"release {release_key} (dropped, never "
                            "inferred)"})
            continue
        if day.weekday() >= 5:
            dropped.append({**base, "reason":
                            "calendar date falls on a weekend (BLS print "
                            "dates are weekdays; dropped)"})
            continue
        if (row["weekday_stated"] is not None
                and _WEEKDAY_NUM[row["weekday_stated"]] != day.weekday()):
            dropped.append({**base, "reason":
                            f"stated weekday {row['weekday_stated']} != "
                            f"real weekday for {day.isoformat()} (three-way "
                            "check failed)"})
            continue
        if row["hour"] is None:
            dropped.append({**base, "reason":
                            "no official time-of-day on the schedule row "
                            "(dropped, never inferred)"})
            continue
        zone = row["zone"] or "ET"
        try:
            scheduled_utc = local_to_utc(
                day, row["hour"], row["minute"], row["meridiem"], zone)
        except ValueError as exc:
            dropped.append({**base, "reason": f"fail-closed: {exc}"})
            continue
        scheduled_local = (f"{day.isoformat()} {row['hour']}:"
                           f"{row['minute']:02d} {row['meridiem']}.m. "
                           f"{zone}")
        instants.append({
            "series": SERIES_BY_RELEASE[release_key],
            "scheduled_local": scheduled_local,
            "scheduled_utc": scheduled_utc,
            "source_url": source_url,
            "retrieved_utc": retrieved_utc,
            "method": method,
            "evidence": {
                "schedule_row": row["release_text"],
                "time_text_on_row": row["time_text"],
                "zone": zone,
                "zone_source": ("stated on row" if row["zone"]
                                else f"defaulted ({PLAN_PRINT_CLOCK} plan "
                                     "standard; BLS schedule pages publish "
                                     "Eastern times)"),
                "weekday_stated": row["weekday_stated"],
            },
        })
    return instants, dropped, in_window


# --------------------------------------------------------------------- #
# census runner                                                          #
# --------------------------------------------------------------------- #
def _fabricated_day_probe(day: date, instants: list[dict]) -> dict:
    produced = [i for i in instants
                if i["scheduled_utc"].startswith(day.isoformat())]
    return {
        "fabricated_day": day.isoformat(),
        "weekday": ["monday", "tuesday", "wednesday", "thursday", "friday",
                    "saturday", "sunday"][day.weekday()],
        "expected": "FAIL (no instant may be produced for a fabricated day)",
        "observed": (f"instant produced from {produced[0]['source_url']}!"
                     if produced else "no instant produced"),
        "verdict": "FAIL" if produced else "PASS",
    }


def run_bls_census(window_start: date, window_end: date,
                   fetch: Callable[[str], dict] | None = None,
                   verdict_fn: Callable[[str], str] | None = None,
                   fabricated_days: tuple[str, ...] = (
                       "2026-02-14", "2026-06-20"),
                   now_utc: str | None = None) -> dict:
    """Attempt the BLS CPI/NFP instant census for the panel window.

    ``fetch`` defaults to the inherited curl-class fetcher (measured);
    the browser-class chain (``webfetch_tool`` / ``browser_use_skill``)
    is recorded per its availability to this lane.  ``verdict_fn`` is the
    inherited plane adapter's authority-verdict function used by the P-7
    nonexistent-series canary."""
    measured_utc = now_utc or datetime.now(timezone.utc).isoformat()
    fetcher = fetch if fetch is not None else curl_class_fetch
    curl_class_measured = fetch is None

    method = "curl_class" if curl_class_measured else "stubbed_fetch"
    method_chain = {
        "curl_class": {
            "status": "MEASURED" if curl_class_measured else "STUBBED",
            "implementation": ("urllib with browser-class headers "
                               "(inherited crypto_ng1.calendar_census."
                               "fetch_url; import-only reuse)"),
        },
        "webfetch_tool": {
            "status": "NOT_RUN",
            "reason": "WebFetch tool is not present in this lane's "
                      "(quant-implementer subagent) toolset: the dispatch "
                      "fallback is not executable in-lane",
        },
        "browser_use_skill": {
            "status": "NOT_RUN",
            "reason": "browser-use control-browser skill contract states "
                      "'subagents must not load this skill or use Browser "
                      "Use'; this lane is a subagent (and no node_repl js "
                      "tool is exposed to it)",
        },
    }

    sources: dict[str, Any] = {}
    instants: list[dict] = []
    dropped: list[dict] = []
    for release_key, url in BLS_SCHEDULE_URLS.items():
        resp = fetcher(url)
        retrieved = resp.get("retrieved_utc")
        if resp["ok"]:
            src_inst, src_drop, in_win = parse_bls_instants(
                resp["body"], release_key, url, retrieved, method,
                window_start, window_end)
            instants.extend(src_inst)
            dropped.extend(src_drop)
            sources[release_key] = {
                "url": url, "status": "RETRIEVED",
                "http_status": resp["status"],
                "attempts": resp["attempts"],
                "retrieved_utc": retrieved,
                "method": method, "rows_in_window": in_win,
                "note": "schedule retrieved; every instant still carries "
                        "the official row timestamp",
            }
        else:
            status = resp["status"]
            definitive = status is not None and 400 <= status < 500
            sources[release_key] = {
                "url": url, "status": "BLOCKED",
                "http_status": status,
                "attempts": resp["attempts"],
                "retrieved_utc": retrieved,
                "method": method,
                "domain_level_denial": definitive,
                "note": ("no instants fabricated; BLS web denied retrieval "
                         "(definitive 4xx / network denial)" if definitive
                         else "no instants fabricated; retrieval failed"),
            }

    # etiquette bookkeeping (post-loop, exact): known BLS URLs that this
    # run never probed -- a domain-level denial means we stop there
    probed = {s["url"] for s in sources.values()}
    known_bls_urls = set(BLS_SCHEDULE_URLS.values()) | set(
        BLS_ALTERNATE_URLS.values())
    unprobed = known_bls_urls - probed
    for src in sources.values():
        if src["status"] == "BLOCKED":
            src["sibling_urls_skipped"] = sorted(unprobed)
            src["sibling_skip_reason"] = (
                "etiquette: domain-level 4xx denial observed; known BLS "
                "URLs not probed this run are listed here (no hammering)")

    # ---- canaries (P-7, mandatory) ------------------------------------ #
    canary_series = {
        "series": "S9:bls-cpi-instants-fabricated",
        "expected": "REFUSED (not GRANTED; nonexistent series)",
    }
    if verdict_fn is None:
        series_canary = {**canary_series, "observed": "NOT_RUN (no verdict_fn)",
                         "verdict": "NOT_RUN"}
    else:
        v = verdict_fn(canary_series["series"])
        refused = v != "GRANTED"
        series_canary = {**canary_series, "observed": f"verdict={v!r}",
                         "refused": refused,
                         "verdict": "PASS" if refused else "FAIL"}

    fabricated_canaries = []
    for fab in fabricated_days:
        fab_day = date.fromisoformat(fab) if isinstance(fab, str) else fab
        fabricated_canaries.append(_fabricated_day_probe(fab_day, instants))

    any_source_live = any(s["status"] == "RETRIEVED"
                          for s in sources.values())
    canaries_ok = (series_canary["verdict"] == "PASS"
                   and all(fc["verdict"] == "PASS"
                           for fc in fabricated_canaries))
    if not any_source_live:
        verdict = "BLOCKED_PER_SOURCE"
    elif not canaries_ok:
        verdict = "FAIL_CANARIES"
    elif instants:
        verdict = "PASS"
    else:
        verdict = "BLOCKED_NO_INSTANTS"

    for fc in fabricated_canaries:
        if not any_source_live:
            fc["note"] = ("measured against a blocked source: no instant "
                          "can exist; re-run this canary when a live "
                          "source is available")

    return {
        "schema": SCHEMA,
        "measured_utc": measured_utc,
        "window": {"start": window_start.isoformat(),
                   "end": window_end.isoformat()},
        "objective": "CPI + NFP scheduled release instants via browser-class "
                     "retrieval from official BLS schedule pages",
        "method_chain": method_chain,
        "sources": sources,
        "instants": instants,
        "dropped": dropped,
        "canaries": {
            "fabricated_days": fabricated_canaries,
            "series_probe": series_canary,
        },
        "instant_count": len(instants),
        "verdict": verdict,
    }


# --------------------------------------------------------------------- #
# p0b: controller-channel raw fold (lane-parser-validated)               #
# --------------------------------------------------------------------- #
#: schema of the controller-channel raw artifact committed by the A1 lead
#: (main-agent WebFetch, browser-class) as the fold input
CONTROLLER_RAW_SCHEMA = "crypto_ng2_controller_fetched_bls@1"
FOLD_CENSUS_SCHEMA = "crypto_ng2_run/p0_calendar_census_ng2@1"

#: controller raw verbatim section keys per release, plus the matching
#: source-url keys inside ``raw["sources"]``
_RAW_RELEASE_KEYS = {
    "CPI": ("cpi_schedule_verbatim", "cpi_archive_verbatim"),
    "NFP": ("empsit_schedule_verbatim", "empsit_archive_verbatim"),
}
_RAW_SOURCE_KEYS = {
    "CPI": ("cpi_schedule", "cpi_archive"),
    "NFP": ("empsit_schedule", "empsit_archive"),
}

_RAW_REF_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_RAW_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})\s*(a\.?m\.?|p\.?m\.?)$", re.I)


def _fold_ref_month(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value if _RAW_REF_MONTH_RE.match(value) else None


def _fold_time(value: Any) -> tuple[int, int, str] | None:
    """Parse a controller-verbatim time-of-day (``08:30 AM``) into the
    (hour, minute, meridiem) triple consumed by ``local_to_utc``."""
    if not isinstance(value, str):
        return None
    m = _RAW_TIME_RE.match(value.strip())
    if m is None:
        return None
    hour, minute = int(m.group(1)), int(m.group(2))
    if not (1 <= hour <= 12 and 0 <= minute <= 59):
        return None
    return hour, minute, _meridiem(m.group(3))


def _fold_iso_date(value: Any) -> date | None:
    """Strict ``YYYY-MM-DD`` calendar date (a 2025-02-30 style text refuses)."""
    if not isinstance(value, str):
        return None
    try:
        day = date.fromisoformat(value.strip())
    except ValueError:
        return None
    return day if day.isoformat() == value.strip() else None


def _fold_instant_utc(day: date, hour: int, minute: int, meridiem: str) -> str:
    """ET (plan print-clock zone standard) -> UTC, DST-aware, fail-closed
    (reuses the inherited ng1 ``local_to_utc`` by import)."""
    return local_to_utc(day, hour, minute, meridiem, "ET")


def _fold_release(raw: dict, release_key: str, window_start: date,
                  window_end: date) -> dict:
    """Fold ONE release (CPI|NFP) from the controller raw verbatim rows.

    Fail-closed: every malformed / weekend / duplicated row is recorded and
    refused, never repaired; a schedule-vs-archive date disagreement for
    the same ref_month refuses BOTH rows for that month.  Returns dict with
    instants / fail_closed / excluded (non-published months) /
    outside_window / cross_validation / urls / channels."""
    if release_key not in _RAW_RELEASE_KEYS:
        raise ValueError(
            f"unknown release key {release_key!r}: not in the fold registry "
            f"{sorted(_RAW_RELEASE_KEYS)} (fail-closed refusal)")
    sched_key, arch_key = _RAW_RELEASE_KEYS[release_key]
    src_sched, src_arch = _RAW_SOURCE_KEYS[release_key]

    sources_meta = (raw.get("sources")
                    if isinstance(raw.get("sources"), dict) else {})
    urls = {k: (sources_meta.get(k) or {}).get("url")
            for k in (src_sched, src_arch)}

    instants: list[dict] = []
    fail_closed: list[dict] = []
    excluded: list[dict] = []
    outside: list[dict] = []
    sched_map: dict[str, dict] = {}
    arch_map: dict[str, dict] = {}

    def _row_base(channel: str, row: Any, ref_month: str | None,
                  release_date: str | None) -> dict:
        return {"series": release_key, "channel": channel,
                "ref_month": ref_month, "release_date": release_date,
                "row_verbatim": row}

    schedule_rows = raw.get(sched_key)
    if isinstance(schedule_rows, list):
        for row in schedule_rows:
            if not isinstance(row, dict):
                fail_closed.append({**_row_base("schedule", row, None, None),
                                    "reason": "schedule row is not an object "
                                              "(dropped, never inferred)"})
                continue
            ref_month = _fold_ref_month(row.get("ref_month"))
            if ref_month is None:
                fail_closed.append({**_row_base("schedule", row, None, None),
                                    "reason": "missing/invalid ref_month "
                                              "(dropped, never inferred)"})
                continue
            day = _fold_iso_date(row.get("release"))
            if day is None:
                fail_closed.append({**_row_base("schedule", row, ref_month,
                                                None),
                                    "reason": "missing/invalid release date "
                                              "(dropped, never inferred)"})
                continue
            if not (window_start <= day <= window_end):
                outside.append({"series": release_key, "channel": "schedule",
                                "ref_month": ref_month,
                                "release_date": day.isoformat()})
                continue
            if ref_month in sched_map:
                fail_closed.append({**_row_base("schedule", row, ref_month,
                                                day.isoformat()),
                                    "reason": f"duplicate schedule row for "
                                              f"ref_month {ref_month} "
                                              f"(ambiguous; dropped)"})
                continue
            t = _fold_time(row.get("time"))
            if t is None:
                fail_closed.append({**_row_base("schedule", row, ref_month,
                                                day.isoformat()),
                                    "reason": "no official time-of-day on the "
                                              "schedule row (dropped, never "
                                              "inferred)"})
                continue
            if day.weekday() >= 5:
                fail_closed.append({**_row_base("schedule", row, ref_month,
                                                day.isoformat()),
                                    "reason": "calendar date falls on a weekend "
                                              "(BLS print dates are weekdays; "
                                              "dropped)"})
                continue
            hour, minute, meridiem = t
            sched_map[ref_month] = {
                "series": release_key,
                "ref_month": ref_month,
                "release_date": day.isoformat(),
                "instant_utc": _fold_instant_utc(day, hour, minute, meridiem),
                "source": "schedule",
                "file": None,
                "evidence": {
                    "series_id": SERIES_BY_RELEASE[release_key],
                    "time_text": row.get("time"),
                    "time_source": "schedule_row",
                    "zone": "ET",
                    "zone_source": f"defaulted ({PLAN_PRINT_CLOCK} plan "
                                   "standard; BLS schedule pages publish "
                                   "Eastern times)",
                    "archive_cross_validated": False,
                    "release_note": row.get("note"),
                    "schedule_url": urls[src_sched],
                    "archive_url": None,
                    "row_verbatim": row,
                },
            }
    else:
        fail_closed.append({"series": release_key, "channel": "schedule",
                            "ref_month": None, "release_date": None,
                            "row_verbatim": None,
                            "reason": f"raw verbatim section {sched_key!r} "
                                      "missing or not a list (no instants "
                                      "fabricated)"})

    archive_rows = raw.get(arch_key)
    if isinstance(archive_rows, list):
        for row in archive_rows:
            if not isinstance(row, dict):
                fail_closed.append({**_row_base("archive", row, None, None),
                                    "reason": "archive row is not an object "
                                              "(dropped, never inferred)"})
                continue
            ref_month = _fold_ref_month(row.get("ref_month"))
            if ref_month is None:
                fail_closed.append({**_row_base("archive", row, None, None),
                                    "reason": "missing/invalid ref_month "
                                              "(dropped, never inferred)"})
                continue
            if row.get("release") is None:
                # non-published month (e.g. the 2025 appropriations lapse):
                # recorded excluded_with_reason, NEVER fabricated
                excluded.append({
                    "series": release_key, "channel": "archive",
                    "ref_month": ref_month, "release_date": None,
                    "reason": row.get("note") or
                              "no release published (archive row)",
                    "row_verbatim": row})
                continue
            day = _fold_iso_date(row.get("release"))
            if day is None:
                fail_closed.append({**_row_base("archive", row, ref_month,
                                                None),
                                    "reason": "invalid release date on the "
                                              "archive row (dropped, never "
                                              "inferred)"})
                continue
            file_evidence = row.get("file")
            if not isinstance(file_evidence, str) or not file_evidence.strip():
                fail_closed.append({**_row_base("archive", row, ref_month,
                                                day.isoformat()),
                                    "reason": "archive row lacks file "
                                              "evidence (dropped, never "
                                              "inferred)"})
                continue
            if not (window_start <= day <= window_end):
                outside.append({"series": release_key, "channel": "archive",
                                "ref_month": ref_month,
                                "release_date": day.isoformat()})
                continue
            if ref_month in arch_map:
                fail_closed.append({**_row_base("archive", row, ref_month,
                                                day.isoformat()),
                                    "reason": f"duplicate archive row for "
                                              f"ref_month {ref_month} "
                                              f"(ambiguous; dropped)"})
                continue
            if day.weekday() >= 5:
                fail_closed.append({**_row_base("archive", row, ref_month,
                                                day.isoformat()),
                                    "reason": "calendar date falls on a weekend "
                                              "(BLS print dates are weekdays; "
                                              "dropped)"})
                continue
            # the archive listing carries date + file only: the print clock
            # is the plan's fixed 8:30 ET standard, disclosed as such (never
            # a silent inference)
            arch_map[ref_month] = {
                "series": release_key,
                "ref_month": ref_month,
                "release_date": day.isoformat(),
                "instant_utc": _fold_instant_utc(day, 8, 30, "a"),
                "source": "archive",
                "file": file_evidence,
                "evidence": {
                    "series_id": SERIES_BY_RELEASE[release_key],
                    "time_text": None,
                    "time_source": "plan_print_clock_default (archive "
                                   "listing carries date + file only; plan "
                                   f"section 3 fixes the {PLAN_PRINT_CLOCK} "
                                   "print clock)",
                    "zone": "ET",
                    "zone_source": f"defaulted ({PLAN_PRINT_CLOCK} plan "
                                   "standard)",
                    "archive_cross_validated": False,
                    "release_note": row.get("note"),
                    "schedule_url": None,
                    "archive_url": urls[src_arch],
                    "row_verbatim": row,
                },
            }
    else:
        fail_closed.append({"series": release_key, "channel": "archive",
                            "ref_month": None, "release_date": None,
                            "row_verbatim": None,
                            "reason": f"raw verbatim section {arch_key!r} "
                                      "missing or not a list (no instants "
                                      "fabricated)"})

    # cross-validation: a ref_month present on BOTH channels must agree on
    # the release date; a mismatch refuses both rows (fail-closed record)
    cross: dict[str, list] = {"matched": [], "mismatched": []}
    for ref_month in sorted(set(sched_map) & set(arch_map)):
        s, a = sched_map[ref_month], arch_map[ref_month]
        if s["release_date"] != a["release_date"]:
            cross["mismatched"].append({
                "series": release_key, "ref_month": ref_month,
                "schedule_date": s["release_date"],
                "archive_date": a["release_date"]})
            fail_closed.append({
                "series": release_key, "channel": "cross_validation",
                "ref_month": ref_month, "release_date": s["release_date"],
                "row_verbatim": {
                    "schedule": s["evidence"]["row_verbatim"],
                    "archive": a["evidence"]["row_verbatim"]},
                "reason": f"schedule date {s['release_date']} != archive "
                          f"date {a['release_date']} for ref_month "
                          f"{ref_month} (fail-closed: both refused, neither "
                          "inferred)"})
            continue
        merged = {
            **s, "file": a["file"],
            "evidence": {
                **s["evidence"],
                "archive_cross_validated": True,
                "archive_url": a["evidence"]["archive_url"],
                "release_note": (a["evidence"]["release_note"]
                                 or s["evidence"]["release_note"]),
                "row_verbatim": {
                    "schedule": s["evidence"]["row_verbatim"],
                    "archive": a["evidence"]["row_verbatim"]}}}
        cross["matched"].append({
            "series": release_key, "ref_month": ref_month,
            "release_date": s["release_date"], "file": a["file"]})
        instants.append(merged)
    instants.extend(arch_map[rm] for rm in sorted(set(arch_map) - set(sched_map)))
    instants.extend(sched_map[rm] for rm in sorted(set(sched_map) - set(arch_map)))

    return {"instants": instants, "fail_closed": fail_closed,
            "excluded": excluded, "outside_window": outside,
            "cross_validation": cross, "urls": urls,
            "channels": {"schedule": isinstance(schedule_rows, list),
                         "archive": isinstance(archive_rows, list)}}


def fold_controller_raw(raw: Any, window_start: date, window_end: date,
                        verdict_fn: Callable[[str], str] | None = None,
                        fabricated_days: tuple[str, ...] = (
                            "2026-02-14", "2026-06-20"),
                        now_utc: str | None = None,
                        input_meta: dict | None = None) -> dict:
    """Fold the controller-channel raw schedules into the P0b census.

    The raw artifact (controller WebFetch verbatim) is INPUT ONLY: every
    instant is re-derived in-lane by the fail-closed rules above (shapes,
    weekday, duplicates, window intersection, schedule/archive agreement,
    DST-correct 8:30 America/New_York -> UTC).  Non-published months are
    recorded ``excluded_with_reason``; nothing is ever fabricated.  The
    ng2-p0 canary set is re-run on the fold path: the 2 fabricated days
    must produce no instant, and a nonexistent series must be refused by
    the fold registry (plus the inherited plane authority probe when a
    ``verdict_fn`` is supplied)."""
    if not isinstance(raw, dict) or raw.get("schema") != CONTROLLER_RAW_SCHEMA:
        raise ValueError("fail-closed: raw input schema is not "
                         f"{CONTROLLER_RAW_SCHEMA!r} (refusing to fold)")
    measured_utc = now_utc or datetime.now(timezone.utc).isoformat()

    instants: list[dict] = []
    fail_closed: list[dict] = []
    excluded: list[dict] = []
    outside: list[dict] = []
    cross_validation: dict[str, dict] = {}
    sources: dict[str, Any] = {}
    for release_key in ("CPI", "NFP"):
        out = _fold_release(raw, release_key, window_start, window_end)
        instants.extend(out["instants"])
        fail_closed.extend(out["fail_closed"])
        excluded.extend(out["excluded"])
        outside.extend(out["outside_window"])
        cross_validation[release_key] = out["cross_validation"]
        sources[release_key] = {"urls": out["urls"],
                                "channels": out["channels"]}
    instants.sort(key=lambda i: (i["instant_utc"], i["series"],
                                 i["ref_month"]))

    # ---- canaries (P-7, mandatory): ng2-p0 set on the fold path --------- #
    fabricated_canaries = []
    for fab in fabricated_days:
        fab_day = date.fromisoformat(fab) if isinstance(fab, str) else fab
        produced = [i for i in instants
                    if i["instant_utc"].startswith(fab_day.isoformat())]
        fabricated_canaries.append({
            "fabricated_day": fab_day.isoformat(),
            "weekday": ["monday", "tuesday", "wednesday", "thursday",
                        "friday", "saturday", "sunday"][fab_day.weekday()],
            "expected": ("FAIL (no instant may be produced for a fabricated "
                         "day)"),
            "observed": (f"instant produced for {produced[0]['series']} "
                         f"ref {produced[0]['ref_month']}!" if produced
                         else "no instant produced"),
            "verdict": "FAIL" if produced else "PASS",
        })

    # nonexistent-series canary, fold-path form: a release key outside the
    # fold registry must be REFUSED (raises), never silently folded
    try:
        _fold_release(raw, "S9:bls-fabricated-release", window_start,
                      window_end)
        registry_canary = {"series": "S9:bls-fabricated-release",
                           "expected": "REFUSED (not in the fold registry)",
                           "observed": "NO REFUSAL (folded!)", "refused": False,
                           "verdict": "FAIL"}
    except ValueError:
        registry_canary = {"series": "S9:bls-fabricated-release",
                           "expected": "REFUSED (not in the fold registry)",
                           "observed": "refused (ValueError: not in the fold "
                                       "registry)",
                           "refused": True, "verdict": "PASS"}

    # belt-and-suspenders: the inherited plane authority probe (same
    # nonexistent series as the p0 census) when a verdict_fn is available
    if verdict_fn is None:
        plane_canary = {"series": "S9:bls-cpi-instants-fabricated",
                        "expected": "REFUSED (not GRANTED; nonexistent series)",
                        "observed": "NOT_RUN (no verdict_fn supplied)",
                        "verdict": "NOT_RUN"}
    else:
        v = verdict_fn("S9:bls-cpi-instants-fabricated")
        refused = v != "GRANTED"
        plane_canary = {"series": "S9:bls-cpi-instants-fabricated",
                        "expected": "REFUSED (not GRANTED; nonexistent series)",
                        "observed": f"verdict={v!r}", "refused": refused,
                        "verdict": "PASS" if refused else "FAIL"}

    canaries_ok = (all(fc["verdict"] == "PASS" for fc in fabricated_canaries)
                   and registry_canary["verdict"] == "PASS"
                   and plane_canary["verdict"] in ("PASS", "NOT_RUN"))
    any_channel = any(s["channels"]["schedule"] or s["channels"]["archive"]
                      for s in sources.values())
    if not any_channel:
        verdict = "BLOCKED_PER_SOURCE"
    elif not canaries_ok:
        verdict = "FAIL_CANARIES"
    elif fail_closed:
        verdict = "FAIL_CLOSED_ROWS"
    elif instants:
        verdict = "PASS"
    else:
        verdict = "BLOCKED_NO_INSTANTS"

    input_block = {
        "schema": raw.get("schema"),
        "fetched_by": raw.get("fetched_by"),
        "fetched_at_utc_verbatim": raw.get("fetched_at_utc"),
        "note": "RAW verbatim controller-channel input; every instant below "
                "is re-derived by this lane's fail-closed fold, never copied "
                "from controller conclusions",
    }
    if input_meta:
        input_block.update(input_meta)
    if "$ISO" in json.dumps(raw.get("sources", {})):
        input_block["timestamp_disclosure"] = (
            "controller raw carries '$ISO' placeholders for fetch "
            "timestamps; recorded verbatim, no retrieval timestamps claimed")

    counts = {k: sum(1 for i in instants if i["series"] == k)
              for k in ("CPI", "NFP")}
    return {
        "schema": FOLD_CENSUS_SCHEMA,
        "task_id": "crypto-ng2-p0b-fold",
        "cycle_id": "CRYPTO-NG2",
        "lane": "p0b",
        "measured_utc": measured_utc,
        "window": {"start": window_start.isoformat(),
                   "end": window_end.isoformat(),
                   "note": "panel hours 2025-08-22T00..2026-08-21T23 UTC; "
                           "only instants inside the window are kept"},
        "objective": "fold controller-fetched BLS CPI/NFP verbatim schedules "
                     "through the lane fail-closed parser into census "
                     "instants (reopen lane A4 per plan section 2)",
        "input": input_block,
        "method_chain": {
            "controller_fetch": {
                "status": "MEASURED_BY_CONTROLLER",
                "note": "main-agent WebFetch (browser-class) verbatim rows "
                        "committed as raw input "
                        "(controller_fetch/bls_schedules_raw.json); "
                        "disclosed channel, not re-fetched by this lane "
                        "(network forbidden in-lane)",
            },
            "lane_parser_validation": {
                "status": "MEASURED",
                "note": "every row re-validated fail-closed in-lane: "
                        "ref_month/date/time shapes, weekday rule, duplicate "
                        "refusal, window intersection, schedule-vs-archive "
                        "date agreement, DST-correct 8:30 America/New_York "
                        "-> UTC via the inherited ng1 local_to_utc "
                        "(import-only reuse)",
            },
        },
        "sources": sources,
        "instants": instants,
        "instant_count": len(instants),
        "counts": counts,
        "excluded_with_reason": excluded,
        "outside_window_rows": outside,
        "fail_closed": fail_closed,
        "cross_validation": cross_validation,
        "canaries": {"fabricated_days": fabricated_canaries,
                     "fold_registry_series_probe": registry_canary,
                     "authority_series_probe": plane_canary},
        "verdict": verdict,
    }


# --------------------------------------------------------------------- #
# funding-settlement keyless availability probe (OPTIONAL, non-blocking)  #
# --------------------------------------------------------------------- #
def funding_probe(symbols: list[str],
                  fetch_json: Callable[[str], dict] | None = None,
                  timeout: float = 15.0) -> dict:
    """Keyless public fapi fundingRate availability probe (ng2 schema).

    Same probe shape and endpoint as the ng1 P0 re-proof (imported
    machinery reused where possible): PROBES availability only, nothing
    is consumed, nothing enters CADS, lane A5 needs only settlement
    boundaries.  Failure is BLOCKED_NOT_CONSUMED and never blocks."""
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

    fetcher = fetch_json or _default
    probes = []
    for sym in symbols:
        url = FUNDING_RATE_URL.format(symbol=sym)
        r = fetcher(url)
        rows = r.get("payload") or []
        probe = {
            "symbol": sym, "url": url,
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
            # settlement micro-timing: 8h boundary structure sanity
            hours = {(t // 3600000) % 8 for t in times}
            probe["boundary_hours_mod8_observed"] = sorted(hours)
        else:
            probe["error"] = r.get("error")
        probes.append(probe)
    all_ok = all(p["ok"] for p in probes)
    return {
        "schema": FUNDING_PROBE_SCHEMA,
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "note": "OPTIONAL keyless availability probe only; not consumed by "
                "any lane at P0; non-blocking",
        "probes": probes,
        "status": "KEYLESS_ENDPOINT_PROVEN" if all_ok
                  else "BLOCKED_NOT_CONSUMED",
    }
