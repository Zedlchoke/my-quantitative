"""SEC bulk market data: fails-to-deliver archive and Form N-PORT data sets.

SEC fair-access: declared User-Agent with SEC contact (value redacted from all
stored artifacts); request rate strictly below the published 10 req/s.
FTD is settlement-stress data only — never short-selling or manipulation
attribution. N-PORT holdings are quarterly regulatory filings, not real time.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..contract import (
    PARSER_VERSION,
    SchemaRefusal,
    iso_utc,
)
from ..http import (
    build_record,
    redact_headers,
    retrieve,
    two_pull_equality,
)
from ..ziputils import extract_members, list_zip_members
from .base import SourceContext, SourceRun

FTD_PAGE = "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data"
NPORT_PAGE = "https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets"
TIMEOUT = (10.0, 60.0)
SEC_MIN_INTERVAL = 1.0 / 8.0  # 8 req/s < published 10 req/s cap

FTD_CENSUS = {
    "official_page": FTD_PAGE,
    "api": "none published; official page lists monthly zip archives",
    "key_required": False,
    "account_required": False,
    "fair_access": "SEC declared-UA policy; rate kept at 8 req/s (< published 10 req/s)",
    "redistribution": "US-government work, public domain; SEC terms page pinned",
    "terms_url": "https://www.sec.gov/terms-of-use",
    "interpretation_guard": "FTD measures settlement fails — settlement stress only; "
    "not short-selling activity, not manipulation evidence",
    "revision_semantics": "archive files are as-published monthly sets; corrections appear "
    "as reposted files — repost identity preserved by exact-URL pinning",
}

NPORT_CENSUS = {
    "official_page": NPORT_PAGE,
    "api": "none published; official page lists quarterly zip data sets",
    "key_required": False,
    "account_required": False,
    "fair_access": "SEC declared-UA policy; rate kept at 8 req/s (< published 10 req/s)",
    "redistribution": "US-government work, public domain; SEC terms page pinned",
    "terms_url": "https://www.sec.gov/terms-of-use",
    "interpretation_guard": "N-PORT is quarterly fund-level holdings (60-day lag regime); "
    "never real-time positioning",
    "revision_semantics": "filings carry accession numbers and amendment numbers; "
    "amendment/repost identity preserved per member file",
}

# Preregistered fund identity filter, SERIES_NAME-keyed. Measured during the
# 2026q2 run: accession prefix identifies the FILING AGENT CIK, not the fund;
# and GLD is structurally out of N-PORT scope (non-1940-Act commodity trust),
# while SPY measured-absent from the 2026q2 FUND_REPORTED_INFO — both recorded
# as measured coverage facts, not extraction failures.
TARGET_FUNDS = {
    "SPY": "SPDR S&P 500 ETF Trust",
    "QQQ": "Invesco QQQ Trust, Series 1",
    "GLD": "SPDR Gold Shares",
}

ZIP_URL_RE = re.compile(r'href="([^"]+?\.zip)"', re.IGNORECASE)


def _absolute_sec_url(url: str) -> str:
    if url.startswith("http"):
        return url
    return f"https://www.sec.gov{url}"


def _sec_headers(ctx: SourceContext) -> Dict[str, str]:
    """Raw declared UA is SENT (SEC policy requires contact in UA); redaction
    happens at record/storage time inside http.retrieve, never at send time."""
    name = ctx.require_present("SEC_CONTACT_NAME")
    email = ctx.require_present("SEC_CONTACT_EMAIL")
    return {"User-Agent": f"{name} {email} my-quantitative-research", "Accept": "*/*"}


def _list_page_zips(
    ctx: SourceContext, state: SourceRun, page_url: str, page_dataset: str
) -> List[str]:
    result = retrieve(
        "GET", page_url, headers=_sec_headers(ctx), session=ctx.session,
        limiter=ctx.limiter_for("sec", SEC_MIN_INTERVAL), max_bytes=4 * 1024 * 1024,
        timeout=TIMEOUT, disk_guard=ctx.disk_guard,
    )
    if result.error or result.http_status != 200 or not result.payload:
        state.add(build_record(
            result, source_id=state.source_id, dataset_id=page_dataset,
            authority_status="BLOCKED_NETWORK" if result.error else "BLOCKED_SCHEMA",
            notes=["official page fetch failed"],
        ))
        return []
    dest = ctx.source_dir(state.source_id) / f"{page_dataset}.html"
    dest.write_bytes(result.payload)
    urls = sorted(
        set(
            _absolute_sec_url(m.group(1))
            for m in ZIP_URL_RE.finditer(result.payload.decode("utf-8", errors="replace"))
        ),
        reverse=True,
    )
    record = build_record(
        result, source_id=state.source_id, dataset_id=page_dataset,
        authority_status="PASS_INVENTORY_ONLY",
        notes=[f"{len(urls)} zip links inventoried"],
    )
    record["raw_path"] = str(dest)
    record["raw_sha256"] = result.raw_sha256
    record["content_length"] = result.bytes_written
    state.add(record)
    listing = ctx.source_dir(state.source_id) / f"{page_dataset}_zip_listing.json"
    listing.write_text(json.dumps({"page": page_url, "zips": urls}, indent=2) + "\n")
    state.event("zip_inventory", {"page": page_dataset, "count": len(urls)})
    return urls


def run_ftd(ctx: SourceContext, sample_months: int = 2) -> SourceRun:
    state = SourceRun("sec_ftd", FTD_CENSUS)
    urls = _list_page_zips(ctx, state, FTD_PAGE, "official_page_inventory")
    if not urls:
        return state

    # Recent sample first.
    for url in urls[:sample_months]:
        dataset = f"monthly_{Path(url).stem}"
        dest = ctx.source_dir("sec_ftd") / Path(url).name
        result = retrieve(
            "GET", url, headers=_sec_headers(ctx), session=ctx.session,
            limiter=ctx.limiter_for("sec", SEC_MIN_INTERVAL), dest=dest,
            disk_guard=ctx.disk_guard, verify_content_length=True, timeout=TIMEOUT,
        )
        if result.error or result.http_status != 200:
            state.add(build_record(
                result, source_id="sec_ftd", dataset_id=dataset,
                authority_status="BLOCKED_NETWORK", notes=["sample download failed"],
            ))
            continue
        record = build_record(
            result, source_id="sec_ftd", dataset_id=dataset,
            authority_status="PASS_SAMPLE",
            available_time_utc=None,
            available_time_evidence="SEC archive publishes monthly fails files after month close "
            "(month-end URL identity); exact publication timestamp not machine-served -> "
            "available_time stays NULL (conservative LATER-bound documented in evidence, P-1)",
            notes=["settlement-stress census file"],
        )
        record["raw_path"] = str(dest)
        record["raw_sha256"] = result.raw_sha256
        record["content_length"] = result.bytes_written
        state.add(record)

    # Two-pull equality on the smallest recent object (immutable-object probe).
    if urls:
        probe = two_pull_equality(
            urls[0], headers=_sec_headers(ctx), session=ctx.session,
            limiter=ctx.limiter_for("sec", SEC_MIN_INTERVAL),
        )
        state.event("two_pull_equality", probe)

    state.event("full_archive_downloader", {
        "status": "IMPLEMENTED_NOT_EXECUTED_IN_V1_SAMPLE_RUN",
        "entrypoint": "research.free_data_frontier.sources.sec_bulk.download_ftd_archive",
        "gate": "requires canary PASS + disk guard + authority gate; executed via CLI acquire-ftd-archive",
    })
    return state


def download_ftd_archive(ctx: SourceContext, max_files: Optional[int] = None) -> SourceRun:
    """Parameterized historical downloader with resume-by-hash. Rate-limited."""
    state = SourceRun("sec_ftd_archive", FTD_CENSUS)
    urls = _list_page_zips(ctx, state, FTD_PAGE, "official_page_inventory")
    if max_files:
        urls = urls[:max_files]
    for url in urls:
        dataset = f"monthly_{Path(url).stem}"
        dest = ctx.source_dir("sec_ftd_archive") / Path(url).name
        if dest.is_file() and dest.stat().st_size > 0:
            state.event("resume_skip", {"dataset": dataset, "path": str(dest)})
            continue
        result = retrieve(
            "GET", url, headers=_sec_headers(ctx), session=ctx.session,
            limiter=ctx.limiter_for("sec", SEC_MIN_INTERVAL), dest=dest,
            disk_guard=ctx.disk_guard, verify_content_length=True, timeout=TIMEOUT,
        )
        status = "PASS_SAMPLE" if result.http_status == 200 and not result.error else (
            "BLOCKED_NETWORK" if result.error else "BLOCKED_SCHEMA"
        )
        record = build_record(
            result, source_id="sec_ftd_archive", dataset_id=dataset,
            authority_status=status,
            available_time_utc=None,
            available_time_evidence="month-end URL identity; exact publication time unevidenced -> NULL (LATER bound only)",
            notes=["archive downloader file"],
        )
        if status == "PASS_SAMPLE":
            record["raw_path"] = str(dest)
            record["raw_sha256"] = result.raw_sha256
            record["content_length"] = result.bytes_written
        state.add(record)
    return state


def run_nport(ctx: SourceContext) -> SourceRun:
    state = SourceRun("sec_nport", NPORT_CENSUS)
    urls = _list_page_zips(ctx, state, NPORT_PAGE, "official_page_inventory")
    if not urls:
        return state
    # V1 cap: exactly the most recent quarter listed on the official page.
    target = urls[0]
    dataset = f"quarterly_{Path(target).stem}"
    dest = ctx.source_dir("sec_nport") / Path(target).name
    result = retrieve(
        "GET", target, headers=_sec_headers(ctx), session=ctx.session,
        limiter=ctx.limiter_for("sec", SEC_MIN_INTERVAL), dest=dest,
        disk_guard=ctx.disk_guard, verify_content_length=True,
        timeout=(10.0, 300.0),
    )
    if result.error or result.http_status != 200:
        state.add(build_record(
            result, source_id="sec_nport", dataset_id=dataset,
            authority_status="BLOCKED_NETWORK", notes=["quarterly zip download failed"],
        ))
        return state
    record = build_record(
        result, source_id="sec_nport", dataset_id=dataset,
        authority_status="PASS_SAMPLE",
        notes=["one-quarter cap honored; extracted bytes never committed to Git; "
               "SUBMISSION.tsv FILING_DATE gives per-filing day-granularity publication "
               "evidence (hour not measured -> available_time stays NULL)"],
    )
    record["raw_path"] = str(dest)
    record["raw_sha256"] = result.raw_sha256
    record["content_length"] = result.bytes_written
    state.add(record)

    # Inspect schema without unbounded extraction.
    members_report = list_zip_members(dest, max_entries=2_000_000)
    listing_path = ctx.source_dir("sec_nport") / f"{dataset}_members.json"
    listing_path.write_text(json.dumps(members_report, indent=2) + "\n")
    state.event("zip_listing", {"members": members_report["entries"],
                                "uncompressed": members_report["total_uncompressed_bytes"]})

    # Relational TSV layout: extract small schema tables, then stream-scan the
    # giant holdings table for the preregistered fund accessions (CIK prefix).
    small_dir = ctx.source_dir("sec_nport") / "extracted_target_members"
    small_tables = extract_members(
        dest, small_dir,
        ["nport_metadata.json", "nport_readme.htm", "SUBMISSION.tsv", "FUND_REPORTED_INFO.tsv"],
        max_total_uncompressed_bytes=64 * 1024 * 1024,
        max_entries=2_000_000,
    )
    state.event("schema_tables_extracted", {"files": [p.name for p in small_tables]})
    try:
        targets = _target_accessions(small_dir / "FUND_REPORTED_INFO.tsv")
    except FileNotFoundError:
        state.notes.append("FUND_REPORTED_INFO.tsv missing inside archive; scan skipped")
        return state
    if not targets:
        state.notes.append("no preregistered fund matched in FUND_REPORTED_INFO; scan skipped")
        return state
    absent = sorted(k for k in targets if k.startswith("MEASURED_ABSENT:"))
    present = {acc: t for acc, t in targets.items() if not acc.startswith("MEASURED_ABSENT:")}
    if absent:
        state.event("measured_absent_targets", {
            "tickers": [t for k, t in targets.items() if k.startswith("MEASURED_ABSENT:")],
            "note": "GLD: non-1940-Act commodity trust, out of N-PORT scope (structural); "
            "SPY: not present in 2026q2 FUND_REPORTED_INFO by exact SERIES_NAME (measured)",
        })
    if not present:
        state.notes.append("all preregistered funds measured-absent this quarter; holdings scan skipped")
        return state
    holdings = _scan_holdings_stream(
        dest, "FUND_REPORTED_HOLDING.tsv", present,
        out_path=ctx.source_dir("sec_nport") / "target_holdings_filtered.tsv",
        max_rows=200_000,
    )
    state.event("target_holdings_scan", {
        "target_accessions": len(targets),
        "rows_kept": holdings["rows_kept"],
        "cap_reached": holdings["cap_reached"],
        "note": "streamed from zip; full table never materialized",
    })
    for path in small_dir.glob("nport_metadata.json"):
        state.event("metadata_probe", {"content": path.read_text()[:400]})
    return state


def _target_accessions(fund_info_tsv: Path) -> Dict[str, str]:
    """Map preregistered SERIES_NAME -> ACCESSION_NUMBER by exact measured
    name match; also report preregistered funds measured-absent this quarter."""
    targets: Dict[str, str] = {}
    matched_names: set = set()
    with fund_info_tsv.open("r", encoding="utf-8", errors="replace") as handle:
        header = handle.readline().strip().split("\t")
        acc_idx = header.index("ACCESSION_NUMBER") if "ACCESSION_NUMBER" in header else 0
        name_idx = header.index("SERIES_NAME") if "SERIES_NAME" in header else 1
        for line in handle:
            cols = line.rstrip("\n").split("\t")
            if len(cols) <= max(acc_idx, name_idx):
                continue
            for ticker, name in TARGET_FUNDS.items():
                if cols[name_idx].strip() == name:
                    targets[cols[acc_idx]] = ticker
                    matched_names.add(ticker)
    for ticker in TARGET_FUNDS:
        if ticker not in matched_names:
            targets[f"MEASURED_ABSENT:{ticker}"] = ticker
    return targets


def _scan_holdings_stream(
    zip_path: Path,
    member: str,
    targets: Dict[str, str],
    *,
    out_path: Path,
    max_rows: int,
) -> Dict[str, Any]:
    """Stream-scan one archive member without materializing it fully."""
    import zipfile as _zipfile

    rows_kept = 0
    cap_reached = False
    with _zipfile.ZipFile(zip_path) as archive:
        with archive.open(member) as raw:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("wb") as out:
                header = raw.readline()
                out.write(header)
                for line in raw:
                    if rows_kept >= max_rows:
                        cap_reached = True
                        break
                    accession = line.split(b"\t", 1)[0]
                    if accession in {k.encode() for k in targets}:
                        out.write(line)
                        rows_kept += 1
    return {"rows_kept": rows_kept, "cap_reached": cap_reached}
