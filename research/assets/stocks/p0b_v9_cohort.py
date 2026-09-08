"""V9 P0b: dead+alive cohort reconciliation (PLAN_stocks_v9.md sec 3 P0b).

Inputs (authorities):
  - P0a death census (research/control/stocks_free_v9_run/death_census.json)
  - V8 submissions cohort census for the frozen 410-filer alive panel
    (tracked, stocks_free_v8_run/p0a_submissions_cohort_census.json)
  - EODHD US delisted symbol list (owner-entitled; cached once here, sha256
    pinned; the probe's 59,923-symbol measurement was never persisted, so
    this cache re-pull IS the pinned cache)
  - SEC submissions per dead CIK (raw gitignored, hash manifest)

Every cohort member is classified ALIVE_EVIDENCED or DEAD_EVIDENCED or
GAP_COVERAGE. A death EODHD cannot serve is a recorded coverage gap, never
silently dropped. Every ticker join names its method and the exact matched
strings; joins are deterministic (normalized-name equality, no fuzzy scores).

Sector tag for dead filers: an empirical SIC-code -> SPDR-sector map derived
from the frozen alive panel itself (sector from the panel entities file,
SIC from the V8-staged raw submissions, each byte verified against the V8
raw hash manifest before use). Codes with a majority vote map; ties and
unseen codes leave sector UNMAPPED (recorded, never guessed).

Usage:
  python -m research.assets.stocks.p0b_v9_cohort pull-delisted
  python -m research.assets.stocks.p0b_v9_cohort pull-submissions
  python -m research.assets.stocks.p0b_v9_cohort build
"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import datetime

CONTROL = "research/control/stocks_free_v9_run"
CENSUS = f"{CONTROL}/death_census.json"
COHORT_OUT = f"{CONTROL}/cohort_v9.json"
DELISTED_RAW = ".staging_sec_v9/eodhd_us_delisted.json"
DELISTED_MANIFEST = f"{CONTROL}/p0b_v9_delisted_cache_manifest.json"
SUB_DIR = ".staging_sec_v9/submissions_dead"
RAW_MANIFEST = f"{CONTROL}/p0b_v9_raw_hash_manifest.json"
V8_CENSUS = "research/control/stocks_free_v8_run/p0a_submissions_cohort_census.json"
V8_RAW_MANIFEST = "research/control/stocks_free_v8_run/p0a_raw_hash_manifest.json"
V8_STAGING = os.environ.get(
    "V8_STAGING_DIR",
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v8/integration/.staging_sec_v8",
)
V8_ALIVE_SUBMISSIONS = f"{V8_STAGING}/submissions"
V8_PANEL_ENTITIES = f"{V8_STAGING}/_panel_entities.json"  # CIK -> sector tag of the frozen panel
EODHD_LIST_URL = "https://eodhd.com/api/exchange-symbol-list/US?api_token={key}&delisted=1"
UA_SEC = "Research my-quantitative@example.com"  # see p0a_v9_death_census UA note
S0_START, S0_END = "2018-04-04", "2025-07-24"
DEATH_DATE_TOLERANCE_DAYS = 120  # |last EODHD trade - Form 15 filing| sanity bound

LEGAL_SUFFIXES = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "LTD", "LIMITED", "PLC",
    "CO", "COMPANY", "HOLDINGS", "HOLDING", "GROUP", "INTERNATIONAL", "INTL",
    "THE", "SA", "NV", "AG", "LP", "LLP", "LLC", "TRUST", "REIT", "CLASS",
    "A", "B", "COMMON", "STOCK", "NEW",
}


def load_key():
    key = os.environ.get("EODHD_API_KEY")
    if key:
        return key
    env_path = os.environ.get("V9_REPO_ROOT", "/Users/hoangminhlong/my-quantitative")
    with open(os.path.join(env_path, ".env")) as f:
        for line in f:
            line = line.strip()
            if line.startswith("EODHD_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not key:
        raise SystemExit("EODHD_API_KEY not found - fail closed")
    os.environ["EODHD_API_KEY"] = key  # environment only
    return key


def redact(text):
    return re.sub(r"api_token=[^&\s\"]+", "api_token=REDACTED", str(text))


def normalize_name(name):
    text = re.sub(r"[^A-Z0-9 ]", " ", (name or "").upper())
    tokens = [t for t in text.split() if t not in LEGAL_SUFFIXES]
    return " ".join(tokens)


def pull_delisted():
    import csv
    import io
    key = load_key()
    req = urllib.request.Request(
        EODHD_LIST_URL.format(key=key), headers={"User-Agent": "my-quantitative-research/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if data[:1] == b"{":
        raise SystemExit(f"EODHD delisted list refused: {redact(data[:300].decode('utf-8', 'replace'))}")
    os.makedirs(os.path.dirname(DELISTED_RAW), exist_ok=True)
    with open(DELISTED_RAW, "wb") as f:
        f.write(data)
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8", "replace"))))
    sha = hashlib.sha256(data).hexdigest()
    man = {
        "schema": "stocks_free_v9_run/p0b_v9_delisted_cache_manifest@1",
        "pulled_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "url": redact(EODHD_LIST_URL.format(key="REDACTED")),
        "format": "application/csv (Code,Name,Country,Exchange,Currency,Type,Isin)",
        "sha256": sha,
        "symbols": len(rows),
        "probe_crossref": "probe measured 59,923 symbols 2026-09-05 (never persisted); this cache is the pinned authority from here on",
    }
    json.dump(man, open(DELISTED_MANIFEST, "w"), indent=1)
    print(json.dumps({"symbols": len(rows), "sha256": sha[:16] + "..."}))


def _pull_one(cik, out):
    url = f"https://data.sec.gov/submissions/CIK{cik[3:]}.json"
    req = urllib.request.Request(url, headers={"User-Agent": UA_SEC, "Accept-Encoding": "gzip, deflate"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            import gzip
            data = gzip.decompress(data)
    with open(out, "wb") as f:
        f.write(data)


def pull_submissions():
    deaths = json.load(open(CENSUS))["deaths"]
    os.makedirs(SUB_DIR, exist_ok=True)
    pulled = skipped = failed = 0
    for cik in sorted(deaths):
        out = f"{SUB_DIR}/{cik}.json"
        if os.path.exists(out) and os.path.getsize(out) > 100:
            skipped += 1
            continue
        try:
            _pull_one(cik, out)
            pulled += 1
        except Exception as e:  # noqa: BLE001 - recorded fail-closed sidecar
            with open(f"{SUB_DIR}/{cik}.FAILED", "w") as f:
                f.write(f"{type(e).__name__}: {redact(e)}\n")
            failed += 1
        time.sleep(0.25)
    print(json.dumps({"pulled": pulled, "skipped": skipped, "failed": failed, "total": len(deaths)}))


def _sic_sector_map():
    """Empirical SIC -> SPDR-sector map derived from the frozen alive panel.

    Bytes of every alive submissions file are hash-verified against the V8
    raw manifest before reading; a mismatch aborts (fail closed).
    """
    v8man = json.load(open(V8_RAW_MANIFEST))["files"]
    panel_entities = json.load(open(V8_PANEL_ENTITIES))
    census = json.load(open(V8_CENSUS))
    votes = {}
    for cik, info in census["filers"].items():
        if info.get("status") == "FETCH_FAILED":
            continue
        fn = f"{cik}.json"
        expected = v8man.get(fn)
        path = os.path.join(V8_ALIVE_SUBMISSIONS, fn)
        if not expected or not os.path.exists(path):
            continue
        if hashlib.sha256(open(path, "rb").read()).hexdigest() != expected:
            raise SystemExit(f"alive submissions byte mismatch for {cik} - fail closed")
        raw = json.load(open(path))
        sic = raw.get("sic")
        sector = panel_entities.get(cik, {}).get("sector")
        if sic and sector:
            votes.setdefault(sic, {}).setdefault(sector, 0)
            votes[sic][sector] += 1
    mapping, ambiguous = {}, []
    for sic, counts in sorted(votes.items()):
        top = max(counts.values())
        winners = sorted(s for s, n in counts.items() if n == top)
        if len(winners) == 1:
            mapping[sic] = {"sector": winners[0], "votes": counts}
        else:
            ambiguous.append({"sic": sic, "votes": counts})
    return mapping, ambiguous


def build():
    census = json.load(open(CENSUS))
    deaths = census["deaths"]
    v8census = json.load(open(V8_CENSUS))
    panel_entities = json.load(open(V8_PANEL_ENTITIES))
    import csv
    import io
    delisted_raw = list(csv.DictReader(io.StringIO(
        open(DELISTED_RAW, encoding="utf-8", errors="replace").read())))
    # EODHD delisted rows: list of {Code, Name, Exchange, ...}
    by_norm_name = {}
    for row in delisted_raw:
        n = normalize_name(row.get("Name") or "")
        if n:
            by_norm_name.setdefault(n, []).append(row)

    sector_map, ambiguous_sics = _sic_sector_map()

    def join_symbol(info):
        """Deterministic ticker join; returns (row, method) or (None, reason)."""
        candidates = []
        name_sources = [("sec_name", info.get("name"))]
        name_sources += [(f"former_name_{i}", fn.get("name"))
                         for i, fn in enumerate(info.get("former_names") or [])]
        for method_src, name in name_sources:
            n = normalize_name(name)
            if n and n in by_norm_name:
                rows = by_norm_name[n]
                if len(rows) == 1:
                    return rows[0], f"{method_src}:exact_normalized"
                candidates.append((method_src, rows))
        if candidates:
            method_src, rows = candidates[0]
            return sorted(rows, key=lambda r: r.get("Code", ""))[0], f"{method_src}:exact_normalized_multi_ambiguous_first_code"
        return None, "no_normalized_name_match"

    members = {"ALIVE_EVIDENCED": [], "DEAD_EVIDENCED": [], "GAP_COVERAGE": [],
               "NOT_DEAD_NAME_ALIVE": []}
    # alive-panel lookup for the class-termination guard (M-I1 lesson: a Form
    # 15 for a class of a STILL-LISTED company is not a company death)
    alive_norm = {}
    alive_tickers = set()
    for cik, info in v8census["filers"].items():
        n = normalize_name(info.get("name"))
        if n:
            alive_norm.setdefault(n, cik)
        for t in info.get("tickers_current") or []:
            alive_tickers.add(str(t).upper())
    # route each census death: guard -> join -> dead or gap
    submissions_missing = []
    routed_dead_ciks = set()
    dead_rows = {}
    gap_rows = {}
    for cik, d in sorted(deaths.items()):
        path = f"{SUB_DIR}/{cik}.json"
        info = {"name": d.get("company_display"), "former_names": [],
                "tickers": [], "sic": None}
        if os.path.exists(path):
            raw = json.load(open(path))
            info = {
                "name": raw.get("name") or d.get("company_display"),
                "former_names": raw.get("formerNames") or [],
                "tickers": raw.get("tickers") or [],
                "sic": raw.get("sic"),
            }
        else:
            submissions_missing.append(cik)
        sector_entry = sector_map.get(str(info["sic"])) if info["sic"] else None
        sector = sector_entry["sector"] if sector_entry else "UNMAPPED"
        base = {
            "cik": cik, "name": info["name"], "sic": info["sic"], "sector": sector,
            "death_filing_date_evidence": d["death_filing_date_evidence"],
        }
        # guard 1: the death candidate names a company that is still an
        # evidenced trading member of the frozen panel
        n = normalize_name(info["name"])
        if n in alive_norm:
            members["NOT_DEAD_NAME_ALIVE"].append({**base, "matched_alive_cik": alive_norm[n],
                                                   "guard": "normalized_name_equals_alive_panel_member"})
            continue
        row, method = join_symbol(info)
        # guard 2: the joined symbol is a current ticker of the alive panel
        if row is not None and str(row.get("Code", "")).upper() in alive_tickers:
            members["NOT_DEAD_NAME_ALIVE"].append({**base, "matched_alive_cik": None,
                                                   "joined_code": row.get("Code"),
                                                   "guard": "joined_code_is_alive_panel_ticker"})
            continue
        if row is None:
            gap_rows[cik] = {**base, "gap_reason": method}
            continue
        routed_dead_ciks.add(cik)
        dead_rows[cik] = {
            **base,
            "ticker_eodhd": row.get("Code"),
            "exchange_eodhd": row.get("Exchange"),
            "eodhd_name": row.get("Name"),
            "join_method": method,
            "death_census_filings": d["filings"],
        }
    members["DEAD_EVIDENCED"] = [dead_rows[c] for c in sorted(dead_rows)]
    members["GAP_COVERAGE"] = [gap_rows[c] for c in sorted(gap_rows)]
    # alive: the frozen 410 panel minus only CIKs routed genuinely DEAD
    for cik, info in sorted(v8census["filers"].items()):
        if cik in routed_dead_ciks:
            continue
        if info.get("status") in ("ACTIVE_FILER", "FILINGS_STALE", "TERMINATED_REGISTRATION"):
            members["ALIVE_EVIDENCED"].append({
                "cik": cik,
                "ticker": (info.get("tickers_current") or [None])[0],
                "name": info.get("name"),
                "sector": panel_entities.get(cik, {}).get("sector"),
                "v8_status": info.get("status"),
                "v8_termination_note": info.get("termination_form_dates") or None,
            })
    cohort = {
        "schema": "stocks_free_v9_run/cohort_v9@1",
        "built_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer_role": "A1 (PLAN_stocks_v9 sec3 P0b)",
        "alive_panel_source": "frozen 410-filer V8 submissions census (tracked); census CIKs also present in the death census are routed to DEAD",
        "dead_join_rule": "normalized-name equality (declared suffix-stripping) between SEC names/former names and the EODHD US delisted cache; no fuzzy scores; multi-ambiguity resolves to first Code with the method recorded",
        "sector_rule": "empirical SIC->SPDR-sector majority map derived from the hash-verified alive panel (sector tags from _panel_entities.json, SIC codes from the V8 raw submissions, bytes verified against the V8 raw manifest); unseen/tied SICs are UNMAPPED and never guessed",
        "price_death_confirmation": "PENDING_P0D_INTEGRITY_SCAN - DEAD_EVIDENCED here means census-covered-common + EODHD symbol joined; reorg-survival cases (e.g. Baxter 2021) are removed only by the P0d last-trade-date check and recorded there, never silently",
        "counts": {
            "alive": len(members["ALIVE_EVIDENCED"]),
            "dead": len(members["DEAD_EVIDENCED"]),
            "gap_coverage": len(members["GAP_COVERAGE"]),
            "not_dead_name_alive": len(members["NOT_DEAD_NAME_ALIVE"]),
            "dead_submissions_missing": len(submissions_missing),
        },
        "sic_sector_map": {k: v["sector"] for k, v in sorted(sector_map.items())},
        "sic_sector_ambiguous": ambiguous_sics,
        "members": members,
    }
    json.dump(cohort, open(COHORT_OUT, "w"), indent=1)
    # raw hash manifest for the dead submissions pulls
    man = {"schema": "stocks_free_v9_run/p0b_v9_raw_hash_manifest@1",
           "built_at_utc": cohort["built_at_utc"], "files": {}}
    for d in (SUB_DIR,):
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                p = os.path.join(d, fn)
                if os.path.isfile(p) and not fn.endswith(".FAILED"):
                    man["files"][f"{os.path.basename(d)}/{fn}"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    man["files"]["eodhd_us_delisted.json"] = hashlib.sha256(open(DELISTED_RAW, "rb").read()).hexdigest()
    json.dump(man, open(RAW_MANIFEST, "w"), indent=1)
    print(json.dumps(cohort["counts"]))


if __name__ == "__main__":
    {"pull-delisted": pull_delisted, "pull-submissions": pull_submissions,
     "build": build}[sys.argv[1]]()
