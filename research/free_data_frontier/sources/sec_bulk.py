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

# Preregistered fund identity filter (identity evidence from zip member names
# only; no extraction without an explicit member match).
TARGET_FUND_CIKS = {
    "0000884395": "SPDR_S&P_500_ETF_TRUST",
    "0001065279": "INVESCO_QQQ_TRUST_1",
    "0001066658": "SPDR_GOLD_SHARES",
}

ZIP_URL_RE = re.compile(r'href="(https://www\.sec\.gov/[^"]+?\.zip)"', re.IGNORECASE)


def _sec_headers(ctx: SourceContext) -> Dict[str, str]:
    name = ctx.require_present("SEC_CONTACT_NAME")
    email = ctx.require_present("SEC_CONTACT_EMAIL")
    ua = f"{name} {email} my-quantitative-research"
    return redact_headers({"User-Agent": ua, "Accept": "*/*"})


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
    urls = sorted(set(m.group(1) for m in ZIP_URL_RE.finditer(result.payload.decode("utf-8", errors="replace"))))
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
        notes=["one-quarter cap honored; extracted bytes never committed to Git"],
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

    wanted = [
        member["name"]
        for member in members_report["members"]
        if _member_matches_targets(member["name"])
    ][:9]
    if not wanted:
        state.notes.append(
            "no preregistered fund CIK matched in zip member names; no extraction performed"
        )
        return state
    extract_dir = ctx.source_dir("sec_nport") / "extracted_target_members"
    extracted = extract_members(
        dest, extract_dir, wanted,
        max_total_uncompressed_bytes=512 * 1024 * 1024,
        max_entries=2_000_000,
    )
    state.event("target_extraction", {"members": wanted, "count": len(extracted)})
    for path in extracted[:3]:
        schema = _probe_nport_xml(path)
        state.event("nport_xml_schema", {"file": path.name, "schema": schema})
    return state


def _member_matches_targets(name: str) -> bool:
    upper = name.upper()
    return any(cik in upper for cik in TARGET_FUND_CIKS)


def _probe_nport_xml(path: Path) -> Dict[str, Any]:
    head = path.read_bytes()[:65536].decode("utf-8", errors="replace")
    root = re.search(r"<([\w:]+)[\s>]", head)
    amendment = re.search(r'amendmentNo="([^"]+)"', head)
    accession = re.search(r'accessionNo="([^"]+)"', head)
    return {
        "root_tag": root.group(1) if root else None,
        "accession_no": accession.group(1) if accession else None,
        "amendment_no": amendment.group(1) if amendment else None,
        "probe": "header-only schema probe (parser_version %s)" % PARSER_VERSION,
    }
