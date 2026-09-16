"""USDA WASDE historical releases via the ESMIS publication API
(esmis.nal.usda.gov, DSpace 7 REST). Machine-readable artifacts acquired with
release/repost identity preserved; revised editions never merged with
originally-published editions."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from ..http import build_record, redact_headers, retrieve
from .base import SourceContext, SourceRun, strict_json_probe

SOURCE_ID = "usda_wasde"
ESMIS_ROOT = "https://esmis.nal.usda.gov"
SEARCH_PATH = "/server/api/discover/search/objects"
TIMEOUT = (10.0, 60.0)

CENSUS = {
    "official_page": ESMIS_ROOT + "/publication/world-agricultural-supply-and-demand-estimates",
    "api": "ESMIS DSpace 7 REST (search + items + bitstreams)",
    "key_required": False,
    "account_required": False,
    "redistribution": "US-government work, public domain",
    "release_semantics": "WASDE released ~12:00 ET on scheduled days (day documented per item); "
    "dc.date.issued supplies day-granularity release evidence",
    "revision_semantics": "each release/revision is a distinct item with distinct bitstreams; "
    "identity preserved per item uuid + bitstream; no merge of revised vs originally published",
}

QUERY = "world agricultural supply and demand estimates"
MAX_ITEMS = 40
ACQUIRE_RECENT = 6
ACQUIRE_HISTORICAL_SAMPLES = 2
HISTORICAL_YEAR_CEILING = 2015  # pick 2010+ samples at/below this year


def run(ctx: SourceContext) -> SourceRun:
    state = SourceRun(SOURCE_ID, CENSUS)
    limiter = ctx.limiter_for("usda", 0.34)
    headers = redact_headers({"Accept": "application/json"})

    search_url = (
        f"{ESMIS_ROOT}{SEARCH_PATH}?query={QUERY.replace(' ', '%20')}"
        f"&dsoType=item&size={MAX_ITEMS}"
    )
    result = retrieve(
        "GET", search_url, headers=headers, session=ctx.session, limiter=limiter,
        max_bytes=32 * 1024 * 1024, timeout=TIMEOUT, disk_guard=ctx.disk_guard,
    )
    if result.http_status != 200 or result.error or not result.payload:
        state.add(build_record(
            result, source_id=SOURCE_ID, dataset_id="search_inventory",
            authority_status="BLOCKED_NETWORK" if result.error else "BLOCKED_SCHEMA",
            notes=["ESMIS search API fetch failed"],
        ))
        return state
    try:
        data = strict_json_probe(result.payload, ["_embedded"], "esmis search")
    except Exception as exc:
        state.add(build_record(
            result, source_id=SOURCE_ID, dataset_id="search_inventory",
            authority_status="BLOCKED_SCHEMA", notes=[str(exc)],
        ))
        return state
    dest = ctx.source_dir(SOURCE_ID) / "search_inventory.json"
    dest.write_bytes(result.payload)
    record = build_record(
        result, source_id=SOURCE_ID, dataset_id="search_inventory",
        authority_status="PASS_INVENTORY_ONLY",
        notes=[f"query={QUERY!r}"],
    )
    record["raw_path"] = str(dest)
    record["raw_sha256"] = result.raw_sha256
    record["content_length"] = result.bytes_written
    state.add(record)

    items = _extract_items(data)
    state.event("items_found", {"count": len(items)})
    if not items:
        state.notes.append("search returned zero WASDE-like items; API shape kept as evidence")
        return state

    # Curated acquisition: most recent items + 2010+ historical samples.
    recent = items[:ACQUIRE_RECENT]
    historical = [
        item for item in items
        if item.get("issued_year") and item["issued_year"] <= HISTORICAL_YEAR_CEILING
    ][:ACQUIRE_HISTORICAL_SAMPLES]
    for item in recent + historical:
        _acquire_item(ctx, state, limiter, headers, item)
    return state


def _extract_items(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    objects = (
        data.get("_embedded", {})
        .get("searchResult", {})
        .get("_embedded", {})
        .get("objects", [])
    )
    items: List[Dict[str, Any]] = []
    for obj in objects:
        item_obj = obj.get("_embedded", {}).get("indexableObject", {})
        if not item_obj:
            continue
        metadata = item_obj.get("metadata", {})
        issued = metadata.get("dc.date.issued", [{}])
        issued_value = issued[0].get("value") if issued else None
        name = item_obj.get("name", "")
        if not re.search(r"wasde|supply and demand", name, re.IGNORECASE):
            continue
        items.append({
            "uuid": item_obj.get("uuid"),
            "name": name,
            "issued": issued_value,
            "issued_year": int(issued_value[:4]) if issued_value and issued_value[:4].isdigit() else None,
            "handle": item_obj.get("handle"),
        })
    return items


def _acquire_item(ctx, state, limiter, headers, item: Dict[str, Any]) -> None:
    uuid = item.get("uuid")
    if not uuid:
        return
    item_url = f"{ESMIS_ROOT}/server/api/core/items/{uuid}"
    detail = retrieve(
        "GET", item_url, headers=headers, session=ctx.session, limiter=limiter,
        max_bytes=8 * 1024 * 1024, timeout=TIMEOUT, disk_guard=ctx.disk_guard,
    )
    if detail.http_status != 200 or detail.error or not detail.payload:
        state.add(build_record(
            detail, source_id=SOURCE_ID, dataset_id=f"item_{uuid[:8]}",
            authority_status="BLOCKED_NETWORK" if detail.error else "BLOCKED_SCHEMA",
            notes=["item detail fetch failed"],
        ))
        return
    dest = ctx.source_dir(SOURCE_ID) / f"item_{_safe(uuid)}.json"
    dest.write_bytes(detail.payload)
    record = build_record(
        detail, source_id=SOURCE_ID, dataset_id=f"item_{_safe(uuid)}",
        authority_status="PASS_SAMPLE",
        notes=[f"name={item.get('name')!r}", f"issued={item.get('issued')!r}"],
    )
    record["raw_path"] = str(dest)
    record["raw_sha256"] = detail.raw_sha256
    record["content_length"] = detail.bytes_written
    state.add(record)

    # Bitstreams: look for machine-readable artifacts (xml/xls/txt/csv).
    bundles_url = f"{ESMIS_ROOT}/server/api/core/items/{uuid}/bundles"
    bundles = retrieve(
        "GET", bundles_url, headers=headers, session=ctx.session, limiter=limiter,
        max_bytes=8 * 1024 * 1024, timeout=TIMEOUT, disk_guard=ctx.disk_guard,
    )
    if bundles.http_status != 200 or not bundles.payload:
        state.event("bitstreams_unavailable", {"uuid": uuid})
        return
    try:
        bundle_data = json.loads(bundles.payload)
    except ValueError:
        state.event("bitstreams_unavailable", {"uuid": uuid, "reason": "non-json"})
        return
    for bundle in bundle_data.get("_embedded", {}).get("bundles", []):
        bitstreams_link = (
            bundle.get("_links", {}).get("bitstreams", {}).get("href")
        )
        if not bitstreams_link:
            continue
        bits = retrieve(
            "GET", bitstreams_link, headers=headers, session=ctx.session,
            limiter=limiter, max_bytes=8 * 1024 * 1024, timeout=TIMEOUT,
            disk_guard=ctx.disk_guard,
        )
        if bits.http_status != 200 or not bits.payload:
            continue
        try:
            bit_data = json.loads(bits.payload)
        except ValueError:
            continue
        for bs in bit_data.get("_embedded", {}).get("bitstreams", []):
            name = bs.get("name", "")
            if not name.lower().endswith((".xml", ".xls", ".txt", ".csv")):
                continue
            content_href = bs.get("_links", {}).get("content", {}).get("href")
            if not content_href:
                continue
            artifact = retrieve(
                "GET", content_href, headers=headers, session=ctx.session,
                limiter=limiter, max_bytes=64 * 1024 * 1024, timeout=TIMEOUT,
                disk_guard=ctx.disk_guard,
            )
            dataset = f"wasde_artifact_{_safe(uuid)}_{_safe(name)}"
            if artifact.http_status == 200 and not artifact.error and artifact.payload:
                adir = ctx.source_dir(SOURCE_ID) / "artifacts"
                adir.mkdir(exist_ok=True)
                apath = adir / f"{dataset}{name.lower()[-4:]}"
                apath.write_bytes(artifact.payload)
                arecord = build_record(
                    artifact, source_id=SOURCE_ID, dataset_id=dataset,
                    authority_status="PASS_SAMPLE",
                    available_time_utc=None,
                    available_time_evidence=(
                        "esmis dc.date.issued gives day granularity only; the ~12:00 ET release "
                        "hour is USDA-schedule-documented, not per-item measured -> "
                        "available_time stays NULL, vintage pins the issued day (Q-8)"
                        if item.get("issued") else None
                    ),
                    vintage=item.get("issued"),
                    notes=[f"item={item.get('name')!r}", f"bitstream={name!r}"],
                )
                arecord["raw_path"] = str(apath)
                arecord["raw_sha256"] = artifact.raw_sha256
                arecord["content_length"] = artifact.bytes_written
                state.add(arecord)
            else:
                state.add(build_record(
                    artifact, source_id=SOURCE_ID, dataset_id=dataset,
                    authority_status="BLOCKED_NETWORK" if artifact.error else "BLOCKED_SCHEMA",
                    notes=["artifact fetch failed"],
                ))


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(value))
