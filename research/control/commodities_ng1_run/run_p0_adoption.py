"""COMMODITIES-NG1 P0 data authority + platform-v3 adoption runner.

Executes the P0 work items of plan PLAN_commodities_ng1.md section 3:

1. deterministic pull + sha256 pin of the official free CFTC legacy
   futures-only annual archives (deacot2016..deacot2026, keyless);
2. full-market CoT coverage census (first/last report, weekly count,
   gaps) + normalized weekly CSV for the declared target markets;
3. PIT release-clock record (Friday 15:30 America/New_York rule) with
   the official schedule page sha-pinned as evidence;
4. EODHD family-1 commodity-linked ETP EOD pulls (owner key loaded
   programmatically from .env -- V13 law: never echoed, never in any
   recorded byte; every URL is stored REDACTED), RAW primary +
   adjusted_close corp-actions cross-check, delisted-channel probe;
5. market-pair join + verdict vs the frozen >= 15 qualifying-pair
   floor (fail-closed: under floor => BLOCKED_DATA);
6. P-7 canaries (each MUST fail: fabricated CFTC market code,
   fabricated release date, never-existed ETP ticker);
7. bounded shadow-parity pilot through the plane adapter (plane-read
   vs raw archive parse, canonical digest equality on overlap);
8. writes p0_raw_manifest.json + p0_gate.json in this directory.

Fail-closed everywhere: any unreachable source is recorded as failed
evidence; nothing is fabricated.  The 2026 archive and current-day ETP
bars are moving snapshots: pins are point-in-time at measured_utc.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _REPO_ROOT)

import requests  # noqa: E402

from research.assets.commodities_ng1 import cot_census, etp_census  # noqa: E402
from research.assets.commodities_ng1.cot_census import (  # noqa: E402
    CotLookupRefused, lookup_market, release_instant,
)
from research.assets.commodities_ng1.etp_census import (  # noqa: E402
    EtpLookupRefused,
)
from research.assets.commodities_ng1.plane_adapter import (  # noqa: E402
    CommoditiesNG1Plane, PlaneConsumptionRefused, PlaneDataBlocked,
)

RUN_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(RUN_DIR, "raw")
CFTC_RAW = os.path.join(RAW_DIR, "cftc")
EODHD_RAW = os.path.join(RAW_DIR, "eodhd")
ETP_EOD_DIR = os.path.join(RUN_DIR, "etp_eod")

MANIFEST_PATH = os.path.join(RUN_DIR, "p0_raw_manifest.json")
GATE_PATH = os.path.join(RUN_DIR, "p0_gate.json")

ENV_PATH = os.environ.get(
    "COMMODITIES_NG1_ENV_PATH", "/Users/hoangminhlong/my-quantitative/.env")

CFTC_YEARS = list(range(2016, 2027))          # 11 annual archives
CFTC_URL = "https://www.cftc.gov/files/dea/history/deacot{year}.zip"
SCHEDULE_URLS = [
    "https://www.cftc.gov/MarketReports/CommitmentsofTraders/"
    "Schedule/index.htm",
    "https://www.cftc.gov/MarketReports/CommitmentsofTraders/"
    "index.htm",
]
EODHD_EOD_URL = "https://eodhd.com/api/eod/{sym}.US?fmt=json&order=a"
EODHD_DELISTED_URL = ("https://eodhd.com/api/exchange-symbol-list/US"
                      "?delisted=1")
REDACTED_URL_EOD = ("https://eodhd.com/api/eod/{sym}.US?fmt=json&order=a"
                    "&api_token=<REDACTED>")
REDACTED_URL_DELISTED = ("https://eodhd.com/api/exchange-symbol-list/US"
                         "?delisted=1&api_token=<REDACTED>")

ETP_SYMBOLS = [
    # pure single-market funds first (declared), then baskets
    "GLD", "IAU", "SGOL", "BAR",            # gold legs
    "SLV", "SIVR", "DBS",                   # silver legs
    "USO", "DBO", "USL",                    # WTI crude legs
    "UNG",                                  # natural gas leg
    "CPER",                                 # copper leg
    "PPLT", "PALL",                         # platinum / palladium legs
    "CORN", "SOYB", "WEAT", "CANE",         # Teucrium single-commodity
    "JO", "NIB", "UGA",                     # coffee / cocoa / gasoline ETNs
    "COW",                                  # livestock basket
    "DBA", "DBC", "PDBC", "GCC",            # agriculture / broad baskets
]

#: Declared market-pair list (plan section 3 + dispatch packet example).
#: resolution: measured archive prefixes (+ optional CFTC exchange code
#: initials); purity: pure = single-market instrument, basket = the
#: instrument tracks a portfolio containing the market (declared basis:
#: dispatch packet "CORN/SOYBEANS/WHEAT->DBA components as the
#: instrument allows"); baskets other than DBA are recorded but earn no
#: pair credit (fail-closed: composition not declared in the packet).
DECLARED_PAIRS = [
    {"cot_prefixes": ["GOLD"], "exchanges": ["CMX"], "etp": "GLD", "purity": "pure"},
    {"cot_prefixes": ["GOLD"], "exchanges": ["CMX"], "etp": "IAU", "purity": "pure"},
    {"cot_prefixes": ["GOLD"], "exchanges": ["CMX"], "etp": "SGOL", "purity": "pure"},
    {"cot_prefixes": ["GOLD"], "exchanges": ["CMX"], "etp": "BAR", "purity": "pure"},
    {"cot_prefixes": ["SILVER"], "exchanges": ["CMX"], "etp": "SLV", "purity": "pure"},
    {"cot_prefixes": ["SILVER"], "exchanges": ["CMX"], "etp": "SIVR", "purity": "pure"},
    {"cot_prefixes": ["SILVER"], "exchanges": ["CMX"], "etp": "DBS", "purity": "pure"},
    {"cot_prefixes": ["CRUDE OIL, LIGHT SWEET"], "exchanges": ["NYME"],
     "etp": "USO", "purity": "pure"},
    {"cot_prefixes": ["CRUDE OIL, LIGHT SWEET"], "exchanges": ["NYME"],
     "etp": "DBO", "purity": "pure"},
    {"cot_prefixes": ["CRUDE OIL, LIGHT SWEET"], "exchanges": ["NYME"],
     "etp": "USL", "purity": "pure"},
    {"cot_prefixes": ["NATURAL GAS"], "exchanges": ["NYME"],
     "etp": "UNG", "purity": "pure"},
    {"cot_prefixes": ["COPPER"], "exchanges": ["CMX"],
     "etp": "CPER", "purity": "pure"},
    {"cot_prefixes": ["PLATINUM"], "exchanges": ["NYME"],
     "etp": "PPLT", "purity": "pure"},
    {"cot_prefixes": ["PALLADIUM"], "exchanges": ["NYME"],
     "etp": "PALL", "purity": "pure"},
    {"cot_prefixes": ["CORN"], "exchanges": ["CBT"],
     "etp": "CORN", "purity": "pure"},
    {"cot_prefixes": ["SOYBEANS"], "exchanges": ["CBT"],
     "etp": "SOYB", "purity": "pure"},
    {"cot_prefixes": ["WHEAT", "WHEAT-SRW"], "exchanges": ["CBT"],
     "etp": "WEAT", "purity": "pure"},
    {"cot_prefixes": ["SUGAR"], "exchanges": ["ICUS"],
     "etp": "CANE", "purity": "pure"},
    {"cot_prefixes": ["COFFEE"], "exchanges": ["ICUS"],
     "etp": "JO", "purity": "pure"},
    {"cot_prefixes": ["COCOA"], "exchanges": ["ICUS"],
     "etp": "NIB", "purity": "pure"},
    {"cot_prefixes": ["GASOLINE REFORMULATED"], "exchanges": ["NYME"],
     "etp": "UGA", "purity": "pure"},
    {"cot_prefixes": ["CORN"], "exchanges": ["CBT"], "etp": "DBA",
     "purity": "basket",
     "declared_basis": "dispatch packet: DBA components as instrument allows"},
    {"cot_prefixes": ["SOYBEANS"], "exchanges": ["CBT"], "etp": "DBA",
     "purity": "basket",
     "declared_basis": "dispatch packet: DBA components as instrument allows"},
    {"cot_prefixes": ["WHEAT", "WHEAT-SRW"], "exchanges": ["CBT"],
     "etp": "DBA", "purity": "basket",
     "declared_basis": "dispatch packet: DBA components as instrument allows"},
]

PAIR_FLOOR = 15

#: Delisted-channel probe: commodity-linked dead names + keyword scan.
DEAD_NAME_PROBES = ["BAL", "UHN", "OIL", "DJP", "JJA", "DNO"]

#: Honest library UA for official/keyed endpoints.
_HTTP_HEADERS = {
    "User-Agent": "my-quantitative-p0/1.0 (research; owner-run factory)"}
KEYWORD_SCAN = ["COMMODITY", "CRUDE", "NATURAL GAS", "GOLD", "SILVER",
                "COPPER", "PLATINUM", "PALLADIUM", "CORN", "SOYBEAN",
                "WHEAT", "SUGAR", "COFFEE", "COCOA", "CATTLE", "HOG"]

TEST_COMMAND = (f"cd {_REPO_ROOT} && "
                "/Users/hoangminhlong/my-quantitative/.venv/bin/python "
                "-m pytest tests/test_commodities_ng1_p0.py -q")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_eodhd_key() -> str:
    """Programmatic .env load (V13 law).  The key value NEVER leaves
    this function into logs/artifacts; os.environ only."""
    key = os.environ.get("EODHD_API_KEY")
    if key:
        return key
    if not os.path.isfile(ENV_PATH):
        raise SystemExit(
            "EODHD_API_KEY not in environment and .env absent - fail closed")
    with open(ENV_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("EODHD_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not key:
        raise SystemExit("EODHD_API_KEY not found in .env - fail closed")
    os.environ["EODHD_API_KEY"] = key
    return key


def _get(url: str, dest: str, attempts: int = 3, sleep_s: float = 2.0):
    """Bounded-retry GET.  Returns evidence dict (never the key: the
    caller passes a URL whose query carries the key, so any recorded
    url/error goes through redaction)."""
    redacted = re.sub(r"api_token=[^&\s]+", "api_token=<REDACTED>", url)
    evidence = {"url_redacted": redacted, "attempts": attempts,
                "status": "ERROR", "http_status": None,
                "bytes": 0, "fetched_utc": None, "last_error": None}
    for i in range(attempts):
        try:
            resp = requests.get(url, timeout=120, headers=_HTTP_HEADERS)
            evidence["http_status"] = resp.status_code
            if resp.status_code == 200 and resp.content:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as fh:
                    fh.write(resp.content)
                evidence.update({
                    "status": "FETCHED", "bytes": len(resp.content),
                    "fetched_utc": utc_now()})
                return evidence
            evidence["status"] = f"HTTP_{resp.status_code}"
            evidence["last_error"] = f"HTTP {resp.status_code}"
        except requests.RequestException as exc:
            evidence["last_error"] = re.sub(
                r"api_token=[^&\s]+", "api_token=<REDACTED>", str(exc))[:300]
        time.sleep(sleep_s * (i + 1))
    return evidence


def main() -> int:
    started = utc_now()
    os.makedirs(CFTC_RAW, exist_ok=True)
    os.makedirs(EODHD_RAW, exist_ok=True)
    os.makedirs(ETP_EOD_DIR, exist_ok=True)
    manifest = {
        "schema": "commodities_ng1_run/p0_raw_manifest@1",
        "cycle_id": "COMMODITIES-NG1",
        "measured_utc": started,
        "repo_root": _REPO_ROOT,
        "entries": {},
    }
    gate = {
        "schema": "commodities_ng1_run/p0_gate@1",
        "task_id": "commodities-ng1-p0-adoption",
        "cycle_id": "COMMODITIES-NG1",
        "lane": "p0",
        "measured_utc": started,
        "worktree": _REPO_ROOT,
        "sections": {},
    }

    # ------------------------------------------------------------------ #
    # Section 1: CFTC archive pull                                        #
    # ------------------------------------------------------------------ #
    print("[1/8] CFTC archive pull", flush=True)
    pull = {"command": "run_p0_adoption.py (cftc_pull)",
            "url_pattern": CFTC_URL, "years": CFTC_YEARS,
            "retries": 3, "sleep_between_s": 2, "entries": {}}
    ok = True
    for i, year in enumerate(CFTC_YEARS):
        name = f"cftc/deacot{year}"
        dest = os.path.join(CFTC_RAW, f"deacot{year}.zip")
        if os.path.isfile(dest) and os.path.getsize(dest) > 0:
            ev = {"status": "REUSED_PINNED", "bytes": os.path.getsize(dest),
                  "fetched_utc": None, "sha256": sha256_file(dest)}
        else:
            if i:
                time.sleep(2)
            ev = _get(CFTC_URL.format(year=year), dest)
            if ev["status"] == "FETCHED":
                ev["sha256"] = sha256_file(dest)
        pull["entries"][name] = ev
        if ev["status"] not in ("FETCHED", "REUSED_PINNED"):
            ok = False
        print(f"  {name}: {ev['status']}", flush=True)
    pull["verdict"] = "PASS" if ok else "FAIL"
    pull["margin"] = ("all 11 annual archives pinned" if ok else
                      "source unreachable after bounded retries; fail-closed")
    gate["sections"]["cftc_pull"] = pull

    # ------------------------------------------------------------------ #
    # Section 2: CoT census (ALL markets) + target-market weekly CSV      #
    # ------------------------------------------------------------------ #
    print("[2/8] CoT census", flush=True)
    all_records: list[cot_census.CotRecord] = []
    parse_errors = []
    for year in CFTC_YEARS:
        path = os.path.join(CFTC_RAW, f"deacot{year}.zip")
        if not os.path.isfile(path):
            continue
        try:
            all_records.extend(cot_census.parse_zip(path))
        except cot_census.CotParseError as exc:
            parse_errors.append(str(exc))
    full_census = cot_census.census_by_market(all_records)
    # name-prefix resolution universe: prefix (before " - ") -> entries
    universe: dict[str, list[dict]] = {}
    for rec in all_records:
        norm = re.sub(r"\s*-\s*", " - ", rec.market_name)
        prefix = norm.split(" - ")[0].strip().upper()
        universe.setdefault(prefix, []).append({
            "code": rec.contract_market_code,
            "exchange": rec.exchange_code,
            "name": rec.market_name,
        })
    prefix_universe = {p: sorted({e["code"]: e for e in v}.values(),
                                 key=lambda e: e["code"])
                       for p, v in universe.items()}

    target_codes: dict[str, dict] = {}
    resolutions = {}
    for pair in DECLARED_PAIRS:
        key = "|".join(pair["cot_prefixes"])
        if key in resolutions:
            continue
        hits = {}
        for entry_prefix, entries in prefix_universe.items():
            if not any(entry_prefix.startswith(p)
                       for p in pair["cot_prefixes"]):
                continue
            for entry in entries:
                if (pair["exchanges"]
                        and entry["exchange"] not in pair["exchanges"]):
                    continue
                cens = full_census.get(entry["code"])
                hits[entry["code"]] = {
                    "contract_market_code": entry["code"],
                    "market_name": entry["name"],
                    "exchange_code": entry["exchange"],
                    "weeks": cens["weeks"] if cens else 0,
                    "first_report": cens["first_report"] if cens else None,
                    "last_report": cens["last_report"] if cens else None,
                    "cot_leg_eligible": bool(cens and cens["cot_leg_eligible"]),
                }
        chosen = None
        if hits:
            eligible = [h for h in hits.values() if h["cot_leg_eligible"]]
            pool = eligible or list(hits.values())
            chosen = max(pool, key=lambda h: h["weeks"])
        resolutions[key] = {
            "cot_prefixes": pair["cot_prefixes"],
            "exchanges": pair["exchanges"],
            "resolved": sorted(hits.values(),
                               key=lambda h: -h["weeks"]),
            "chosen_code": chosen["contract_market_code"] if chosen else None,
        }
    for pair in DECLARED_PAIRS:
        key = "|".join(pair["cot_prefixes"])
        code = resolutions[key]["chosen_code"]
        if code:
            target_codes[code] = full_census[code]
    target_records = [r for r in all_records
                      if r.contract_market_code in target_codes]
    weekly_csv = os.path.join(RUN_DIR, "p0_cot_weekly_targets.csv")
    with open(weekly_csv, "w", encoding="utf-8") as fh:
        fh.write(cot_census.records_to_csv(target_records))
    census_path = os.path.join(RUN_DIR, "p0_cot_market_census.json")
    with open(census_path, "w", encoding="utf-8") as fh:
        json.dump({
            "schema": cot_census.SCHEMA,
            "measured_utc": utc_now(),
            "archives": [f"deacot{y}.zip" for y in CFTC_YEARS],
            "parse_errors": parse_errors,
            "market_count": len(full_census),
            "total_records": len(all_records),
            "cot_leg_eligible_markets": sorted(
                c for c, m in full_census.items() if m["cot_leg_eligible"]),
            "markets": full_census,
        }, fh, indent=1, sort_keys=True)
    cot_section = {
        "command": "run_p0_adoption.py (cot_census)",
        "exit_code": 0 if not parse_errors else 1,
        "observed": {
            "archives_parsed": len(CFTC_YEARS) - len(parse_errors),
            "total_weekly_records": len(all_records),
            "distinct_markets": len(full_census),
            "cot_leg_eligible_markets": sum(
                1 for m in full_census.values() if m["cot_leg_eligible"]),
            "target_markets_censused": len(target_codes),
        },
        "margin": ("format stable 2016..2026, zero parse errors" if not
                   parse_errors else f"parse errors: {parse_errors[:3]}"),
        "verdict": "PASS" if not parse_errors and all_records else "FAIL",
        "evidence_path": "research/control/commodities_ng1_run/"
                         "p0_cot_market_census.json",
    }
    gate["sections"]["cot_census"] = cot_section
    print(f"  markets={len(full_census)} eligible={cot_section['observed']['cot_leg_eligible_markets']}",
          flush=True)

    # ------------------------------------------------------------------ #
    # Section 3: PIT release-clock evidence                               #
    # ------------------------------------------------------------------ #
    print("[3/8] PIT release clock", flush=True)
    sched_dest = os.path.join(CFTC_RAW, "release_schedule_page.html")
    if os.path.isfile(sched_dest) and os.path.getsize(sched_dest) > 0:
        sched_ev = {"status": "REUSED_PINNED",
                    "bytes": os.path.getsize(sched_dest),
                    "http_status": None, "fetched_utc": None,
                    "attempts": 0, "last_error": None}
    else:
        sched_ev = {"status": "ERROR", "attempts": len(SCHEDULE_URLS) * 4,
                    "http_status": None, "bytes": 0, "fetched_utc": None,
                    "last_error": None, "url_redacted": SCHEDULE_URLS}
        for url in SCHEDULE_URLS:
            if sched_ev["status"] == "FETCHED":
                break
            sched_ev = _get(url, sched_dest, attempts=4, sleep_s=5.0)
    schedule_sha = (sha256_file(sched_dest)
                    if sched_ev["status"] in ("FETCHED", "REUSED_PINNED")
                    else None)
    quote = None
    if schedule_sha:
        with open(sched_dest, encoding="utf-8", errors="replace") as fh:
            page = fh.read()
        text = re.sub(r"<[^>]+>", " ", page)
        text = re.sub(r"\s+", " ", text)
        hit = re.search(
            r"[^.]*3:30[^.]*\.", text, flags=re.IGNORECASE)
        quote = hit.group(0).strip()[:500] if hit else None
    sample = {}
    if target_codes:
        code0 = sorted(target_codes)[0]
        recs = [r for r in target_records
                if r.contract_market_code == code0]
        if recs:
            d0 = min(r.report_date for r in recs)
            d1 = max(r.report_date for r in recs)
            sample = {
                "market_code": code0,
                "first_report": d0.isoformat(),
                "first_release_utc": release_instant(d0).isoformat(),
                "last_report": d1.isoformat(),
                "last_release_utc": release_instant(d1).isoformat(),
            }
    pit = {
        "command": "run_p0_adoption.py (pit_clock)",
        "rule": "release at Friday 15:30 America/New_York of the "
                "Tuesday-position week (DST-correct); data position date "
                "is the Tuesday carried in the legacy report 'As of Date'",
        "law": "no downstream consumer may read a report's positions "
               "before its release instant (plan sections 3/5)",
        "schedule_page": {
            **sched_ev,
            "sha256": schedule_sha,
            "release_quote_measured": quote,
        },
        "sample_release_instants": sample,
        "verdict": "PASS" if schedule_sha and quote else (
            "PASS_WITHOUT_QUOTE" if schedule_sha else "FAIL"),
    }
    gate["sections"]["pit_clock"] = pit
    manifest["entries"]["cftc/release_schedule"] = {
        "path": "research/control/commodities_ng1_run/raw/cftc/"
                "release_schedule_page.html",
        "sha256": schedule_sha or "",
        "bytes": sched_ev.get("bytes", 0),
        "series": "S6:cftc-cot-release-schedule",
        "source_urls_redacted": SCHEDULE_URLS,
        "provenance_note": ("pinned-page reuse: the html is a moving "
                            "surface; the pinned bytes carry the "
                            "release-rule statement, the originating "
                            "URL among the candidates is not "
                            "re-measured on reuse (bounded etiquette)"),
        "fetched_utc": sched_ev.get("fetched_utc"),
    }
    print(f"  quote={bool(quote)} sha={schedule_sha is not None}", flush=True)

    # ------------------------------------------------------------------ #
    # Section 4: EODHD ETP pulls                                          #
    # ------------------------------------------------------------------ #
    print("[4/8] EODHD ETP pulls", flush=True)
    key = _load_eodhd_key()
    etp_pull = {"command": "run_p0_adoption.py (etp_pull)",
                "url_redacted_pattern": REDACTED_URL_EOD.replace(
                    "{sym}", "<SYM>"),
                "key_loading": "programmatic .env load, never echoed "
                               "(V13 law)", "entries": {}}
    etp_ok = True
    for i, sym in enumerate(ETP_SYMBOLS):
        dest = os.path.join(EODHD_RAW, f"{sym}.json")
        name = f"etp/raw_json/{sym}"
        if os.path.isfile(dest) and os.path.getsize(dest) > 0:
            ev = {"status": "REUSED_PINNED", "bytes": os.path.getsize(dest),
                  "fetched_utc": None}
        else:
            if i:
                time.sleep(1.5)
            ev = _get(EODHD_EOD_URL.format(sym=sym)
                      + f"&api_token={key}", dest)
            if ev["status"] == "FETCHED":
                try:
                    json.load(open(dest, encoding="utf-8"))
                    ev["json_valid"] = True
                except json.JSONDecodeError:
                    ev["status"] = "ERROR"
                    ev["last_error"] = "response is not valid JSON"
        etp_pull["entries"][sym] = ev
        if ev["status"] not in ("FETCHED", "REUSED_PINNED"):
            etp_ok = False
        print(f"  {sym}: {ev['status']}", flush=True)
    etp_pull["verdict"] = "PASS" if etp_ok else "FAIL"
    gate["sections"]["etp_pull"] = etp_pull

    as_of = date.today()
    etp_censuses: dict[str, dict] = {}
    normalize_failures = []
    for sym in ETP_SYMBOLS:
        src = os.path.join(EODHD_RAW, f"{sym}.json")
        if not os.path.isfile(src):
            normalize_failures.append(f"{sym}: raw json absent")
            continue
        try:
            with open(src, encoding="utf-8") as fh:
                rows = etp_census.normalize_eod_payload(
                    json.load(fh), sym)
        except (etp_census.EtpCensusError, EtpLookupRefused,
                json.JSONDecodeError) as exc:
            normalize_failures.append(f"{sym}: {exc}")
            continue
        csv_text = etp_census.rows_to_csv(rows)
        csv_path = os.path.join(ETP_EOD_DIR, f"{sym}.csv")
        with open(csv_path, "w", encoding="utf-8") as fh:
            fh.write(csv_text)
        if os.path.isfile(src):
            manifest["entries"][f"etp/raw_json/{sym}"] = {
                "path": f"research/control/commodities_ng1_run/raw/eodhd/"
                        f"{sym}.json",
                "sha256": sha256_file(src),
                "bytes": os.path.getsize(src),
                "series": "S4:eodhd-etp-eod",
                "source_url_redacted": REDACTED_URL_EOD.format(sym=sym),
                "fetched_utc": etp_pull["entries"][sym].get("fetched_utc"),
                "committed": False,
            }
        manifest["entries"][f"etp/eod/{sym}"] = {
            "path": f"research/control/commodities_ng1_run/etp_eod/{sym}.csv",
            "sha256": sha256_file(csv_path),
            "bytes": os.path.getsize(csv_path),
            "series": "S4:eodhd-etp-eod",
            "source_url_redacted": REDACTED_URL_EOD.format(sym=sym),
            "fetched_utc": etp_pull["entries"][sym].get("fetched_utc"),
            "committed": True,
        }
        try:
            etp_censuses[sym] = etp_census.census_etp(rows, sym, as_of)
        except etp_census.EtpCensusError as exc:
            normalize_failures.append(f"{sym}: census: {exc}")
    for year in CFTC_YEARS:
        path = os.path.join(CFTC_RAW, f"deacot{year}.zip")
        if os.path.isfile(path):
            manifest["entries"][f"cftc/deacot{year}"] = {
                "path": f"research/control/commodities_ng1_run/raw/cftc/"
                        f"deacot{year}.zip",
                "sha256": sha256_file(path),
                "bytes": os.path.getsize(path),
                "series": "S6:cftc-cot-futures-only",
                "source_url_redacted": CFTC_URL.format(year=year),
                "fetched_utc": pull["entries"][f"cftc/deacot{year}"].get(
                    "fetched_utc"),
                "committed": False,
            }
    manifest["entries"]["cftc/cot_weekly_targets_csv"] = {
        "path": "research/control/commodities_ng1_run/"
                "p0_cot_weekly_targets.csv",
        "sha256": sha256_file(weekly_csv),
        "bytes": os.path.getsize(weekly_csv),
        "series": "S6:cftc-cot-futures-only",
        "note": "normalized weekly CoT surface for resolved target markets",
        "committed": True,
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)

    etp_census_section = {
        "command": "run_p0_adoption.py (etp_census)",
        "as_of": as_of.isoformat(),
        "observed": {
            "symbols_normalized": len(etp_censuses),
            "normalize_failures": normalize_failures,
            "eligible_legs": sorted(
                s for s, c in etp_censuses.items() if c["etp_leg_eligible"]),
        },
        "rule": etp_censuses[ETP_SYMBOLS[0]]["rule"] if etp_censuses else {},
        "cross_check_convention": "RAW close primary; adjusted_close "
                                  "corp-actions cross-check only (V8)",
        "verdict": "PASS" if etp_censuses and not normalize_failures
        else ("PASS_WITH_FAILURES" if etp_censuses else "FAIL"),
        "evidence_path": "research/control/commodities_ng1_run/"
                         "p0_etp_census.json",
    }
    with open(os.path.join(RUN_DIR, "p0_etp_census.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"schema": etp_census.SCHEMA,
                   "measured_utc": utc_now(),
                   "censuses": etp_censuses}, fh, indent=1, sort_keys=True)
    gate["sections"]["etp_census"] = etp_census_section
    print(f"  normalized={len(etp_censuses)} eligible="
          f"{len(etp_census_section['observed']['eligible_legs'])}",
          flush=True)

    # ------------------------------------------------------------------ #
    # Section 5: delisted-channel probe                                   #
    # ------------------------------------------------------------------ #
    print("[5/8] delisted-channel probe", flush=True)
    dest = os.path.join(EODHD_RAW, "us_delisted_symbol_list.csv")
    if os.path.isfile(dest) and os.path.getsize(dest) > 0:
        ev = {"status": "REUSED_PINNED", "bytes": os.path.getsize(dest)}
    else:
        ev = _get(EODHD_DELISTED_URL + f"&api_token={key}", dest,
                  attempts=2, sleep_s=2.0)
    dead_hits, keyword_counts = {}, {}
    listing_rows = 0
    if ev["status"] in ("FETCHED", "REUSED_PINNED"):
        try:
            with open(dest, encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                names = {}
                for row in reader:
                    listing_rows += 1
                    code = str(row.get("Code", "")).strip().upper()
                    if code:
                        names[code] = str(row.get("Name", ""))
            dead_hits = {c: names.get(c, "") for c in DEAD_NAME_PROBES
                         if c in names}
            for kw in KEYWORD_SCAN:
                hits = [c for c, n in names.items()
                        if kw in n.upper()][:10]
                if hits:
                    keyword_counts[kw] = hits
        except (OSError, csv.Error) as exc:
            ev["status"] = "ERROR"
            ev["last_error"] = f"listing parse failed: {exc}"
    delisted_section = {
        "command": "run_p0_adoption.py (delisted_probe)",
        "url_redacted": REDACTED_URL_DELISTED,
        "evidence": {k: v for k, v in ev.items() if k != "url_redacted"},
        "observed": {
            "listing_rows": listing_rows,
            "dead_name_hits": dead_hits,
            "keyword_scan_first10": keyword_counts,
        },
        "note": "dead commodity ETPs remain in the delisted channel "
                "(CSV shape measured 2026-09-12; the V8-era symbol-list "
                "JSON shape now 404s); dead legs do NOT qualify for the "
                "floor (not tradeable at measurement)",
        "verdict": "PASS" if (ev["status"] in ("FETCHED", "REUSED_PINNED")
                              and listing_rows > 0) else "FAIL",
    }
    gate["sections"]["delisted_probe"] = delisted_section
    print(f"  dead_hits={len(dead_hits)} keywords={len(keyword_counts)}",
          flush=True)

    # ------------------------------------------------------------------ #
    # Section 6: market-pair join + floor verdict                         #
    # ------------------------------------------------------------------ #
    print("[6/8] market-pair floor", flush=True)
    pairs_declared = []
    for pair in DECLARED_PAIRS:
        key2 = "|".join(pair["cot_prefixes"])
        code = resolutions[key2]["chosen_code"]
        pairs_declared.append({
            "cot_market_code": code,
            "cot_prefixes": pair["cot_prefixes"],
            "cot_resolution": resolutions[key2],
            "etp": pair["etp"],
            "purity": pair["purity"],
            "declared_basis": pair.get(
                "declared_basis", "plan section 3 candidate leg"),
        })
    floor_eligible_pairs = [
        p for p in pairs_declared if p["purity"] in ("pure", "basket")]
    joined = etp_census.join_pairs(
        floor_eligible_pairs, full_census, etp_censuses)
    qualifying = [p for p in joined if p["qualifying"]]
    floor_verdict = "PASS" if len(qualifying) >= PAIR_FLOOR else "BLOCKED_DATA"
    pairs_out = {
        "schema": "commodities_ng1_run/p0_market_pairs@1",
        "measured_utc": utc_now(),
        "floor": {
            "required_pairs": PAIR_FLOOR,
            "qualifying_pairs_measured": len(qualifying),
            "rule": ">= 15 markets with BOTH >= 10y continuous weekly CoT "
                    "coverage AND a matched tradeable ETP leg with >= 8y "
                    "EOD; under floor => BLOCKED_DATA (fail-closed, "
                    "plan section 3)",
            "floor_credit_rule": "pure single-market pairs + the dispatch-"
                                 "declared DBA basket triple; other baskets "
                                 "recorded but earn no credit (composition "
                                 "not declared)",
        },
        "pairs": joined,
        "verdict": floor_verdict,
    }
    with open(os.path.join(RUN_DIR, "p0_market_pairs.json"), "w",
              encoding="utf-8") as fh:
        json.dump(pairs_out, fh, indent=1, sort_keys=True)
    gate["sections"]["market_pairs_floor"] = {
        "command": "run_p0_adoption.py (market_pairs_floor)",
        "observed": {
            "qualifying_pairs": len(qualifying),
            "required": PAIR_FLOOR,
            "qualifying_list": sorted(
                f"{p['cot_market_code']}->{p['etp']}" for p in qualifying),
        },
        "margin": (f"{len(qualifying)} >= {PAIR_FLOOR}" if
                   floor_verdict == "PASS" else
                   f"{len(qualifying)} < {PAIR_FLOOR} => BLOCKED_DATA "
                   "(valid P0 outcome, fail-closed)"),
        "verdict": floor_verdict,
        "evidence_path": "research/control/commodities_ng1_run/"
                         "p0_market_pairs.json",
    }
    print(f"  qualifying={len(qualifying)} verdict={floor_verdict}",
          flush=True)

    # ------------------------------------------------------------------ #
    # Section 7: canaries (each must FAIL)                                #
    # ------------------------------------------------------------------ #
    print("[7/8] canaries", flush=True)
    canaries = []
    try:
        lookup_market(all_records, "ZZZ999")
        canaries.append({"canary": "fabricated_cftc_market_code_ZZZ999",
                         "observed": "NOT REFUSED (BAD)",
                         "failed_as_required": False})
    except CotLookupRefused as exc:
        canaries.append({"canary": "fabricated_cftc_market_code_ZZZ999",
                         "observed": str(exc)[:200],
                         "failed_as_required": True})
    try:
        release_instant(date(2025, 11, 19))   # a Wednesday: must refuse
        canaries.append({"canary": "fabricated_release_date_wednesday",
                         "observed": "NOT REFUSED (BAD)",
                         "failed_as_required": False})
    except CotLookupRefused as exc:
        canaries.append({"canary": "fabricated_release_date_wednesday",
                         "observed": str(exc)[:200],
                         "failed_as_required": True})
    try:
        etp_census.normalize_eod_payload(
            {"detail": "symbol not found"}, "ZZZZNOPE")
        canaries.append({"canary": "never_existed_etp_ticker",
                         "observed": "NOT REFUSED (BAD)",
                         "failed_as_required": False})
    except EtpLookupRefused as exc:
        canaries.append({"canary": "never_existed_etp_ticker",
                         "observed": str(exc)[:200],
                         "failed_as_required": True})
    # live-wire negative: real vendor call for a never-existed ticker
    time.sleep(1.5)
    wire = _get(f"https://eodhd.com/api/eod/ZZZZNOPE.US"
                f"?fmt=json&api_token={key}",
                os.path.join(RAW_DIR, "eodhd", "ZZZZNOPE_probe.json"),
                attempts=1, sleep_s=1.0)
    if os.path.isfile(os.path.join(RAW_DIR, "eodhd",
                                   "ZZZZNOPE_probe.json")):
        os.remove(os.path.join(RAW_DIR, "eodhd", "ZZZZNOPE_probe.json"))
    canaries.append({
        "canary": "never_existed_etp_ticker_live_wire_404",
        "observed": (f"vendor returned HTTP {wire['http_status']} "
                     "(no bar surface) for ZZZZZNOPE.US"),
        "failed_as_required": wire["status"] != "FETCHED"})
    # live-wire negative through the plane (fabricated ticker consume)
    # live-wire negative through the plane (fabricated ticker consume)
    try:
        plane = CommoditiesNG1Plane()
        plane.consume("etp/eod/ZZZZNOPE")
        canaries.append({"canary": "plane_consume_fabricated_ticker",
                         "observed": "NOT REFUSED (BAD)",
                         "failed_as_required": False})
    except (PlaneConsumptionRefused, PlaneDataBlocked) as exc:
        canaries.append({"canary": "plane_consume_fabricated_ticker",
                         "observed": str(exc)[:200],
                         "failed_as_required": True})
    canaries_ok = all(c["failed_as_required"] for c in canaries)
    with open(os.path.join(RUN_DIR, "p0_canaries.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"schema": "commodities_ng1_run/p0_canaries@1",
                   "measured_utc": utc_now(),
                   "canaries": canaries,
                   "all_failed_as_required": canaries_ok}, fh, indent=1)
    gate["sections"]["canaries"] = {
        "command": "run_p0_adoption.py (canaries)",
        "observed": canaries,
        "margin": ("every canary failed as required (P-7)" if canaries_ok
                   else "A CANARY PASSED -> evidence surface is broken"),
        "verdict": "PASS" if canaries_ok else "FAIL",
        "evidence_path": "research/control/commodities_ng1_run/"
                         "p0_canaries.json",
    }

    # ------------------------------------------------------------------ #
    # Section 8: shadow-parity pilot + adoption query (via adapter)       #
    # ------------------------------------------------------------------ #
    print("[8/8] shadow parity + adoption", flush=True)
    plane = CommoditiesNG1Plane()
    parity_rows, query_rows = [], []
    for name in ["cftc/deacot2016", "cftc/deacot2020", "cftc/deacot2026",
                 "etp/eod/GLD", "etp/eod/CORN"]:
        try:
            res = plane.shadow_parity(
                name, market_codes=sorted(target_codes)
                if name.startswith("cftc/") else None)
            parity_rows.append(res)
        except Exception as exc:   # noqa: BLE001 - recorded fail-closed
            parity_rows.append({"entry": name,
                                "error": str(exc)[:200], "identical": False})
        try:
            q = plane.query_entry(name)
            query_rows.append({
                "entry": name,
                "query_verdict": q["query"]["verdict"],
                "query_reason": q["query"]["reason"],
                "row_count": q["query"]["row_count"],
                "result_digest": q["query"]["result_digest"],
                "canonical_digest": q["canonical_digest"],
            })
        except Exception as exc:   # noqa: BLE001
            query_rows.append({"entry": name, "error": str(exc)[:200]})
    parity_ok = bool(parity_rows) and all(
        r.get("identical") for r in parity_rows)
    query_ok = bool(query_rows) and all(
        r.get("query_verdict") == "SUCCESS" for r in query_rows)
    with open(os.path.join(RUN_DIR, "p0_shadow_parity.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"schema": "commodities_ng1_run/p0_shadow_parity@1",
                   "measured_utc": utc_now(),
                   "pilot_bounded": "3 CoT archives + 2 ETP legs",
                   "parity": parity_rows,
                   "adoption_queries": query_rows}, fh, indent=1)
    gate["sections"]["shadow_parity"] = {
        "command": "run_p0_adoption.py (shadow_parity pilot)",
        "observed": parity_rows,
        "margin": ("plane-read canonical digest == raw archive parse "
                   "digest on overlap, all pilot entries" if parity_ok
                   else "digest mismatch on at least one pilot entry"),
        "verdict": "PASS" if parity_ok else "FAIL",
        "evidence_path": "research/control/commodities_ng1_run/"
                         "p0_shadow_parity.json",
    }
    gate["sections"]["adoption_query"] = {
        "command": "run_p0_adoption.py (consume_via_plane + frozen query)",
        "observed": query_rows,
        "margin": ("manifest-verified QueryPlane SUCCESS on all pilot "
                   "entries" if query_ok else "query plane refused/drifted"),
        "verdict": "PASS" if query_ok else "FAIL",
    }

    # ------------------------------------------------------------------ #
    # Final gate verdict                                                  #
    # ------------------------------------------------------------------ #
    sections = gate["sections"]
    data_failure = any(
        sections[s]["verdict"] == "FAIL"
        for s in ("cftc_pull", "cot_census", "etp_census", "pit_clock",
                  "shadow_parity", "canaries"))
    if data_failure:
        final = "BLOCKED_DATA"
        why = "one or more evidence sections FAILED (fail-closed)"
    elif sections["market_pairs_floor"]["verdict"] == "BLOCKED_DATA":
        final = "BLOCKED_DATA"
        why = ("qualifying market-pairs under the frozen floor of "
               f"{PAIR_FLOOR} (valid P0 outcome per plan section 3)")
    elif sections["etp_pull"]["verdict"] != "PASS" or \
            sections["delisted_probe"]["verdict"] != "PASS" or \
            sections["adoption_query"]["verdict"] != "PASS":
        final = "PASS_WITH_FAILURES"
        why = "core evidence PASS but a non-core section degraded"
    else:
        final = "PASS"
        why = (f"{len(qualifying)} qualifying market-pairs >= floor "
               f"{PAIR_FLOOR}; all evidence sections PASS")
    gate["final_verdict"] = final
    gate["final_why"] = why
    gate["test_command"] = TEST_COMMAND
    with open(GATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, indent=1, sort_keys=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    print(f"FINAL: {final} ({why})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
