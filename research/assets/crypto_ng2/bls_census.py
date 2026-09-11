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
