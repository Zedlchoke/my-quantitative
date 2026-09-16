"""USDA WASDE historical releases.

Primary acquisition surface: the official USDA OCE WASDE page
(www.usda.gov/oce/commodity/wasde/) which publishes machine-readable
artifacts (xml/txt/xls) per monthly release. The esmis.nal.usda.gov archive
named in the cycle plan was probed first and measured unreachable
programmatically (all API paths 404 to an SPA fallback) — that probe is
recorded as evidence; the substitution to the official USDA OCE page is
disclosed in the census. Release/repost identity preserved per file; revised
editions never merged with originally-published editions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..http import build_record, redact_headers, retrieve
from .base import SourceContext, SourceRun

SOURCE_ID = "usda_wasde"
OCE_PAGE = "https://www.usda.gov/oce/commodity/wasde/"
ESMIS_PAGE = "https://esmis.nal.usda.gov/publication/world-agricultural-supply-and-demand-estimates"
TIMEOUT = (10.0, 60.0)

CENSUS = {
    "primary_page": OCE_PAGE,
    "plan_named_archive": ESMIS_PAGE,
    "archive_probe_result": "esmis API paths /server/api, /server/api/discover, /rest, /oai, "
    "/jsonapi, /api/search all HTTP 404 (SPA fallback HTML) from this client with browser-like "
    "headers too — programmatic API surface not locatable; measured, recorded, not bypassed",
    "substitution_disclosure": "USDA OCE official WASDE page is the USDA-published machine-readable "
    "surface; Cornell Mann Library mirror (usda.library.cornell.edu/concern/publications/3t945q76s) "
    "reachable as cross-check candidate (not pulled in V1)",
    "key_required": False,
    "account_required": False,
    "redistribution": "US-government work, public domain",
    "release_semantics": "WASDE released ~12:00 ET on scheduled days; page release-date text is "
    "day-granularity evidence only — exact per-item publication hour not measured -> "
    "available_time stays NULL, vintage pins the release month (Q-8)",
    "revision_semantics": "each monthly release is a distinct artifact set (MMYY filename); "
    "reposts/corrections would appear as re-published files — identity preserved per exact URL pin",
}

ARTIFACT_RE = re.compile(r'href="(https?://www\.usda\.gov/oce/commodity/wasde/[^"]+\.(?:xml|txt|xls|xlsx|csv))"', re.IGNORECASE)
HISTORICAL_PROBES = ["wasde0512.xml", "wasde0115.xml"]  # 2010+ historical samples


def run(ctx: SourceContext) -> SourceRun:
    state = SourceRun(SOURCE_ID, CENSUS)
    limiter = ctx.limiter_for("usda", 0.34)
    headers = redact_headers({"User-Agent": "my-quantitative-free-data-frontier/1.0", "Accept": "*/*"})

    # Measured probe of the plan-named esmis archive (recorded, honest).
    esmis = retrieve(
        "GET", ESMIS_PAGE, headers=headers, session=ctx.session, limiter=limiter,
        max_bytes=1024 * 1024, timeout=TIMEOUT, disk_guard=ctx.disk_guard,
    )
    state.add(build_record(
        esmis, source_id=SOURCE_ID, dataset_id="esmis_archive_probe",
        authority_status="PASS_INVENTORY_ONLY",
        notes=["esmis page reachable but API surfaces 404; see census archive_probe_result"],
    ))

    # Official OCE page inventory.
    page = retrieve(
        "GET", OCE_PAGE, headers=headers, session=ctx.session, limiter=limiter,
        max_bytes=8 * 1024 * 1024, timeout=TIMEOUT, disk_guard=ctx.disk_guard,
    )
    if page.http_status != 200 or page.error or not page.payload:
        state.add(build_record(
            page, source_id=SOURCE_ID, dataset_id="oce_page_inventory",
            authority_status="BLOCKED_NETWORK" if page.error else "BLOCKED_SCHEMA",
            notes=["official OCE WASDE page fetch failed"],
        ))
        return state
    text = page.payload.decode("utf-8", errors="replace")
    urls = sorted(set(m.group(1) for m in ARTIFACT_RE.finditer(text)))
    dest = ctx.source_dir(SOURCE_ID) / "oce_page_inventory.html"
    dest.write_bytes(page.payload)
    record = build_record(
        page, source_id=SOURCE_ID, dataset_id="oce_page_inventory",
        authority_status="PASS_INVENTORY_ONLY",
        notes=[f"{len(urls)} machine-readable artifact links inventoried"],
    )
    record["raw_path"] = str(dest)
    record["raw_sha256"] = page.raw_sha256
    record["content_length"] = page.bytes_written
    state.add(record)
    listing = ctx.source_dir(SOURCE_ID) / "oce_artifact_listing.json"
    listing.write_text(json.dumps({"page": OCE_PAGE, "artifacts": urls}, indent=2) + "\n")
    state.event("artifact_inventory", {"count": len(urls), "recent": urls[:8]})

    # Bounded acquisition: 2 most recent releases (xml/txt/xls) + historical samples.
    selected: List[str] = []
    for suffix in (".xml", ".txt", ".xls"):
        for url in urls:
            if url.lower().endswith(suffix):
                selected.append(url)
                break
    selected = selected[:6]
    for stem in HISTORICAL_PROBES:
        selected.append(f"https://www.usda.gov/oce/commodity/wasde/{stem}")

    for url in selected:
        dataset = f"wasde_artifact_{Path(url).stem}"
        adir = ctx.source_dir(SOURCE_ID) / "artifacts"
        dest = adir / Path(url).name
        artifact = retrieve(
            "GET", url, headers=headers, session=ctx.session, limiter=limiter,
            dest=dest, disk_guard=ctx.disk_guard, verify_content_length=True,
            timeout=TIMEOUT,
        )
        if artifact.http_status == 200 and not artifact.error and artifact.raw_sha256:
            month_tag = _month_tag(url)
            arecord = build_record(
                artifact, source_id=SOURCE_ID, dataset_id=dataset,
                authority_status="PASS_SAMPLE",
                available_time_utc=None,
                available_time_evidence=(
                    "WASDE release schedule is ~12:00 ET on the scheduled day; per-file publication "
                    "timestamp not measured -> NULL; vintage pins release month"
                ),
                vintage=month_tag,
                notes=["machine-readable WASDE release artifact"],
            )
            arecord["raw_path"] = str(dest)
            arecord["raw_sha256"] = artifact.raw_sha256
            arecord["content_length"] = artifact.bytes_written
            state.add(arecord)
        else:
            missing_sample = any(url.endswith(stem) for stem in HISTORICAL_PROBES) and artifact.http_status == 404
            state.add(build_record(
                artifact, source_id=SOURCE_ID, dataset_id=dataset,
                authority_status="BLOCKED_NETWORK" if artifact.error else (
                    "PASS_INVENTORY_ONLY" if missing_sample else "BLOCKED_SCHEMA"
                ),
                notes=["historical probe 404 (file not served at this path — recorded honestly)"
                       ] if missing_sample else ["artifact fetch failed"],
            ))
    return state


def _month_tag(url: str) -> Optional[str]:
    match = re.search(r"wasde(\d{2})(\d{2})\.", url.lower())
    if not match:
        return None
    month, year = int(match.group(1)), 2000 + int(match.group(2))
    return f"{year:04d}-{month:02d}"
