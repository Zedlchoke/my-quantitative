"""STOCKS-FREE-V5 P2-b: SEC EDGAR acquisition tool (PLAN_stocks_v5.md §2, §6.P2).

Authorized dataset: SEC Company Facts / Submissions (keyless, fair access).
Everything lives under ``.staging_sec/`` (gitignored; no raw-data commits).

Subcommands
-----------
stage1  fetch submissions JSON for the first STAGE1_LIMIT registry entries
panel   build the frozen filer panel from stage-1 submissions (SIC -> sector,
        documented deterministic rule) and print the evidence summary
stage2  fetch companyfacts JSON for every panel CIK

Discipline: ~7.5 requests/s (< SEC fair-access 10/s), honest UA, resumable
(existing non-empty files are skipped and logged), every response hash-logged.
"""

from __future__ import annotations

import gzip
import io
import json
from hashlib import sha256
from pathlib import Path
import sys
import time
import urllib.request
import urllib.error

REPO = Path(__file__).resolve().parents[3]
STAGE = REPO / ".staging_sec"
LOG = STAGE / "fetch_log.jsonl"
PANEL = STAGE / "panel.json"
REGISTRY = STAGE / "company_tickers.json"

STAGE1_LIMIT = 1200
PANEL_PER_SECTOR = 40
MIN_10K_YEAR = 2015
UA = "my-quantitative-research/1.0 (local academic research; no public contact)"

SECTORS = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]

# Documented SIC -> sector mapping for the 11-ETF GICS cohort.  2-digit major
# groups by default, with explicit exceptions.  Anything not listed is
# UNMAPPED and excluded (counted, never silently dropped).
SIC_DEFAULT: dict[int, str] = {
    10: "XLB",  # metal mining (gold/silver 1040s default here; 138x exploration -> XLE by exception)
    12: "XLE",  # coal mining
    13: "XLE",  # oil & gas extraction
    14: "XLB",  # nonmetallic minerals mining
    15: "XLI",  # building construction
    16: "XLI",  # heavy construction
    17: "XLI",  # construction special trades
    20: "XLP",  # food & kindred
    21: "XLP",  # tobacco
    22: "XLY",  # textile mill products (apparel chain)
    23: "XLY",  # apparel
    24: "XLY",  # lumber & wood products
    25: "XLY",  # furniture & fixtures
    26: "XLB",  # paper & allied
    27: "XLI",  # printing & publishing (traditional placement)
    28: "XLB",  # chemicals (drugs 283 -> XLV by exception)
    29: "XLE",  # petroleum refining
    30: "XLY",  # rubber & plastics (auto-adjacent)
    31: "XLY",  # leather
    32: "XLB",  # stone, clay, glass
    33: "XLB",  # primary metals
    34: "XLI",  # fabricated metal
    35: "XLK",  # industrial & commercial machinery / computers
    36: "XLK",  # electronic & other electrical equipment
    37: "XLY",  # transportation equipment (autos)
    38: "XLK",  # instruments (3841/3845 surgical -> XLV by exception)
    39: "XLY",  # misc manufacturing (toys)
    40: "XLI",  # railroads
    41: "XLI",  # local transit
    42: "XLI",  # motor freight
    43: "XLI",  # US postal
    44: "XLI",  # water transport
    45: "XLI",  # air transport
    46: "XLE",  # pipelines
    47: "XLI",  # transportation services
    48: "XLC",  # communications
    49: "XLU",  # electric/gas/water utilities
    50: "XLP",  # wholesale durable (food-adjacent default; mixed)
    51: "XLP",  # wholesale nondurable
    52: "XLY",  # building materials retail
    53: "XLY",  # general merchandise retail
    54: "XLP",  # food retail
    55: "XLY",  # auto dealers
    56: "XLY",  # apparel retail
    57: "XLY",  # furniture retail
    58: "XLP",  # eating & drinking places
    59: "XLY",  # misc retail (5961 e-commerce -> XLY default)
    60: "XLF",  # depository banks
    61: "XLF",  # credit institutions
    62: "XLF",  # security & commodity brokers
    63: "XLF",  # insurance carriers
    64: "XLF",  # insurance agents
    65: "XLRE",  # real estate
    67: "XLF",  # holding/investment offices
    70: "XLY",  # hotels & lodging
    72: "XLY",  # personal services
    73: "XLK",  # business services (software/IT)
    75: "XLI",  # automotive repair
    76: "XLY",  # misc repair (personal-adjacent)
    78: "XLC",  # motion picture & entertainment
    79: "XLY",  # amusement & recreation
    80: "XLV",  # health services
    81: "XLY",  # legal services
    82: "XLV",  # educational services (health-adjacent placement)
    83: "XLV",  # social services
    84: "XLY",  # museums/botanical (discretionary)
    86: "XLF",  # membership organizations (credit-adjacent default)
    87: "XLK",  # engineering/accounting/research services
    89: "XLY",  # misc services
    99: None,   # nonclassifiable -> UNMAPPED
}
SIC_EXCEPTIONS: dict[int, str] = {
    2830: "XLV", 2831: "XLV", 2833: "XLV", 2834: "XLV", 2835: "XLV", 2836: "XLV",  # pharmaceuticals
    3841: "XLV", 3845: "XLV",  # surgical/orthopedic appliances, in vitro
    3826: "XLV",  # biological products (diagnostic-adjacent)
    6798: "XLRE", 6512: "XLRE", 6513: "XLRE", 6552: "XLRE",  # REITs / operators
    7374: "XLK",  # data processing
    4813: "XLC", 4822: "XLC", 4841: "XLC",  # telecom
    3663: "XLC",  # radio/TV broadcasting equipment? -> comm equipment tech; keep 36->XLK default, this one XLC
    3669: "XLC",
    100: "XLE", 1044: "XLE",  # gold/silver mining -> XLB by default rule 10/14; 138 exploration
    1380: "XLE", 1381: "XLE", 1382: "XLE", 1389: "XLE",
    4610: "XLE", 4612: "XLE", 4613: "XLE",  # pipelines detailed
    4911: "XLU", 4922: "XLU", 4923: "XLU", 4924: "XLU", 4931: "XLU",  # utilities detailed
    5912: "XLP",  # drug stores
    5122: "XLP",  # drugs wholesale
    5141: "XLP",  # groceries wholesale
    5411: "XLP",  # grocery retail
    5961: "XLY",  # e-commerce retail
    7389: "XLK",  # misc business services (tech-adjacent); default 73 anyway
}
SIC_EXCEPTIONS.pop(100)  # not a real SIC; guard


def sic_to_sector(sic: int | None) -> str | None:
    if not sic:
        return None
    if sic in SIC_EXCEPTIONS:
        return SIC_EXCEPTIONS[sic]
    return SIC_DEFAULT.get(sic // 100)


def http_get(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Encoding": "gzip",
        "Host": urllib.request.urlsplit(url).netloc,
    })
    last_error = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                return response.status, raw
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (403, 429, 503):
                time.sleep(2 ** attempt)
                continue
            raise
        except urllib.error.URLError as exc:
            last_error = exc
            time.sleep(2 ** attempt)
            continue
    raise RuntimeError(f"GET failed after retries: {url} ({last_error})")


def log_event(payload: dict) -> None:
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def fetch(cik: int, kind: str, url: str) -> Path:
    path = STAGE / f"{kind}_CIK{cik:010d}.json"
    if path.exists() and path.stat().st_size > 0:
        log_event({"ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cik": cik,
                   "kind": kind, "status": "skip-existing", "bytes": path.stat().st_size})
        return path
    started = time.time()
    status, raw = http_get(url)
    time.sleep(0.135)  # ~7.4 req/s sustained, under the 10/s fair-access cap
    path.write_bytes(raw)
    log_event({"ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cik": cik,
               "kind": kind, "status": status, "bytes": len(raw),
               "sha256": sha256(raw).hexdigest(), "elapsed_s": round(time.time() - started, 3)})
    return path


def stage1() -> None:
    registry = json.loads(REGISTRY.read_text())
    ordered = sorted((int(k), v) for k, v in registry.items())
    targets = ordered[:STAGE1_LIMIT]
    print(f"stage1: {len(targets)} submissions fetches -> {STAGE}")
    for index, (_key, entry) in enumerate(targets):
        cik = int(entry["cik_str"])
        fetch(cik, "submissions",
              f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        if index % 100 == 0:
            print(f"  {index}/{len(targets)} {entry['ticker']}", flush=True)


def build_panel() -> None:
    candidates = []
    unmapped = 0
    no_tenk = 0
    stage1_files = sorted(STAGE.glob("submissions_CIK*.json"))
    for path in stage1_files:
        data = json.loads(path.read_text())
        sic = data.get("sic")
        sector = sic_to_sector(sic)
        recent = (data.get("filings") or {}).get("recent") or {}
        forms = recent.get("form") or []
        dates = recent.get("filingDate") or []
        tenk_years = [d[:4] for f, d in zip(forms, dates) if f in ("10-K", "10-K/A") and d]
        if sector is None:
            unmapped += 1
            continue
        if not any(int(y) >= MIN_10K_YEAR for y in tenk_years):
            no_tenk += 1
            continue
        candidates.append({
            "cik": int(str(data["cik"]).lstrip("0")),
            "name": data.get("name", ""),
            "sic": sic,
            "sector": sector,
            "total_recent_filings": len(forms),
            "tenk_count": len(tenk_years),
            "latest_tenk": max(tenk_years),
        })
    panel: dict[str, list[dict]] = {sector: [] for sector in SECTORS}
    for sector in SECTORS:
        ranked = sorted(
            (c for c in candidates if c["sector"] == sector),
            key=lambda c: (-c["total_recent_filings"], c["cik"]),
        )
        panel[sector] = ranked[:PANEL_PER_SECTOR]
    evidence = {
        "schema": "stocks_free_v5_run/sec_panel@1",
        "stage1_submissions": len(stage1_files),
        "candidates_mapped": len(candidates),
        "unmapped_sic": unmapped,
        "no_recent_tenk": no_tenk,
        "panel_rule": (
            f"per sector: SIC-mapped stage-1 filers with a 10-K filed >= {MIN_10K_YEAR}, "
            f"ranked by total recent filings desc, CIK asc tie-break, top {PANEL_PER_SECTOR}"
        ),
        "stage1_limit": STAGE1_LIMIT,
        "registry_sha256": sha256(REGISTRY.read_bytes()).hexdigest(),
        "survivorship_note": (
            "panel is built from the CURRENT SEC registry (2026-09-04) - filers that "
            "left the registry are absent from history; PIT filing clocks inside the "
            "panel are exact; the tilt is constant across every V5 arm"
        ),
        "panel": panel,
        "panel_total": sum(len(v) for v in panel.values()),
    }
    PANEL.write_text(json.dumps(evidence, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: evidence[k] for k in
                      ("stage1_submissions", "candidates_mapped", "unmapped_sic",
                       "no_recent_tenk", "panel_total")}, indent=1))
    for sector in SECTORS:
        print(f"  {sector}: {len(panel[sector])}")


def stage2() -> None:
    evidence = json.loads(PANEL.read_text())
    ciks = sorted({c["cik"] for sector in evidence["panel"].values() for c in sector})
    print(f"stage2: {len(ciks)} companyfacts fetches -> {STAGE}")
    for index, cik in enumerate(ciks):
        fetch(cik, "companyfacts",
              f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
        if index % 50 == 0:
            print(f"  {index}/{len(ciks)}", flush=True)


def main() -> int:
    STAGE.mkdir(exist_ok=True)
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "stage1":
        stage1()
    elif command == "panel":
        build_panel()
    elif command == "stage2":
        stage2()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
