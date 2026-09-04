"""STOCKS-FREE-V5 P2-b: normalize panel companyfacts into the PIT records store.

Every staged raw file (hash-pinned by the fetch log) goes through the V5
sanitizing shim and the FROZEN SecAdapter; surviving NormalizedRecords are
written to ``.staging_sec/pit_records.jsonl`` with the filer's frozen panel
sector tag and full provenance.  A coverage census reports, per sector, the
availability span of the common instant fields against the S0 window so D1
proposals know exactly what conditioning clock is fundable.

Run:  .venv/bin/python research/control/stocks_free_v5_run/p2_sec_normalize.py
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))

from datetime import datetime, timezone
import json
from hashlib import sha256
from pathlib import Path
import sys

from research.data_fusion.adapters.base import RawResponse, RequestSpec
from research.data_fusion.adapters.sec import SecAdapter
from research.assets.stocks.sec_sanitize import SANITIZER_VERSION, sanitize_companyfacts

REPO = Path(__file__).resolve().parents[3]
STAGE = REPO / ".staging_sec"
PANEL = STAGE / "panel.json"
RECORDS = STAGE / "pit_records.jsonl"
REPORT = STAGE / "normalize_report.json"

RETRIEVED = datetime(2026, 9, 4, 10, 50, 0, tzinfo=timezone.utc)
S0_START = "2018-04-04"
FIELDS_OF_INTEREST = [
    "us-gaap:Assets",
    "us-gaap:Asset",
    "us-gaap:StockholdersEquity",
    "us-gaap:Liabilities",
    "us-gaap:LongTermDebtNoncurrent",
    "us-gaap:CashAndCashEquivalentsAtCarryingValue",
    "us-gaap:EntityPublicFloat",
    "dei:EntityCommonStockSharesOutstanding",
]


def main() -> int:
    panel_evidence = json.loads(PANEL.read_text())
    sector_of = {
        c["cik"]: c["sector"]
        for sector, filers in panel_evidence["panel"].items()
        for c in filers
    }
    adapter = SecAdapter()

    files = sorted(STAGE.glob("companyfacts_CIK*.json"))
    n_records = 0
    file_reports = []
    with open(RECORDS, "w", encoding="utf-8") as out:
        for path in files:
            cik = int(path.stem.split("CIK")[1])
            if cik not in sector_of:
                continue
            raw_bytes = path.read_bytes()
            payload = json.loads(raw_bytes)
            sanitized, stats = sanitize_companyfacts(payload)
            request = RequestSpec(
                source_id="SEC_EDGAR",
                url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
            )
            response = RawResponse(
                request_id=request.request_id(),
                url=request.full_url(),
                status=200,
                reason="OK",
                headers=(("content-type", "application/json"),),
                body=json.dumps(sanitized, sort_keys=True).encode("utf-8"),
                retrieved_time_utc=RETRIEVED,
            )
            output = adapter.parse_company_facts(response)
            for record in output.records:
                out.write(json.dumps({
                    "source_id": record.source_id,
                    "dataset_id": record.dataset_id,
                    "entity_id": record.entity_id,
                    "sector": sector_of[cik],
                    "field": record.field,
                    "value": record.value,
                    "unit": record.unit,
                    "event_time_utc": record.event_time_utc.isoformat(),
                    "available_time_utc": record.available_time_utc.isoformat(),
                    "effective_time_utc": record.effective_time_utc.isoformat() if record.effective_time_utc else None,
                    "vintage_time_utc": record.vintage_time_utc.isoformat(),
                    "retrieved_time_utc": record.retrieved_time_utc.isoformat(),
                    "raw_path": f".staging_sec/{path.name}",
                    "file_raw_sha256": sha256(raw_bytes).hexdigest(),
                    "raw_sha256": record.raw_sha256,
                    "license_id": record.license_id,
                    "entitlement_id": record.entitlement_id,
                    "normalizer_version": f"{SANITIZER_VERSION}+{record.normalizer_version}",
                }, ensure_ascii=False) + "\n")
                n_records += 1
            file_reports.append({
                "cik": cik,
                "sector": sector_of[cik],
                "records": len(output.records),
                "sanitizer": stats.as_dict(),
                "file_raw_sha256": sha256(raw_bytes).hexdigest(),
            })

    # coverage census: per sector x field, availability span vs S0
    census: dict[str, dict[str, dict]] = {}
    with open(RECORDS, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row["field"] not in FIELDS_OF_INTEREST:
                continue
            bucket = census.setdefault(row["sector"], {}).setdefault(row["field"], {
                "n": 0, "first_available": None, "last_available": None, "n_pre_s0": 0,
            })
            bucket["n"] += 1
            avail = row["available_time_utc"]
            if bucket["first_available"] is None or avail < bucket["first_available"]:
                bucket["first_available"] = avail
            if bucket["last_available"] is None or avail > bucket["last_available"]:
                bucket["last_available"] = avail
            if avail < S0_START:
                bucket["n_pre_s0"] += 1

    report = {
        "schema": "stocks_free_v5_run/p2_sec_normalize_report@1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "panel_fil": len(sector_of),
        "files_processed": len(file_reports),
        "records_written": n_records,
        "records_path": ".staging_sec/pit_records.jsonl",
        "sanitizer_version": SANITIZER_VERSION,
        "adapter_version": "sec-adapter-1.0.0 (frozen core c6a0576)",
        "retrieved_time_pinned": RETRIEVED.isoformat(),
        "fields_of_interest_census": census,
        "file_reports": file_reports,
    }
    REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: report[k] for k in ("panel_fil", "files_processed", "records_written")}, indent=1))
    for sector in sorted(census):
        assets = census[sector].get("us-gaap:Assets") or {}
        print(f"  {sector}: Assets n={assets.get('n', 0)} first={str(assets.get('first_available'))[:10]} "
              f"last={str(assets.get('last_available'))[:10]} pre-S0={assets.get('n_pre_s0', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
