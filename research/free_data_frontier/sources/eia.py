"""EIA Open Data v2 (api.eia.gov/v2) with keyless bulk probe.

The API key is read from the root .env at request-construction time only;
stored URLs always redact the api_key query parameter.
"""

from __future__ import annotations

import json
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..contract import CredentialMissing, utc_now_iso
from ..http import build_record, redact_headers, retrieve
from .base import SourceContext, SourceRun, strict_json_probe

SOURCE_ID = "eia_open_data"
API_ROOT = "https://api.eia.gov/v2"
BULK_ROOT = "https://api.eia.gov/bulk"
TIMEOUT = (10.0, 60.0)

CENSUS = {
    "official_api_root": API_ROOT + "/",
    "documentation": "https://www.eia.gov/opendata/documentation.php",
    "terms": "https://www.eia.gov/about/copyrights_reuses.cfm",
    "key_required": True,
    "account_required": False,
    "redistribution": "US-government work; EIA reuse guidance pinned (public domain with caveat requests)",
    "revision_semantics": "EIA revises historical values routinely; the v2 API does not serve "
    "per-row publication timestamps -> retrieval-time evidence only; release-time evidence "
    "must come from separate release-calendar evidence before any historical scored join",
}

# Preregistered route walk (small curated energy set).
ROUTE_WALK: List[Dict[str, Any]] = [
    {"route": "petroleum", "children_of_interest": ["stve", "sum", "crude-imports"]},
    {"route": "natural-gas", "children_of_interest": ["stor", "sum"]},
    {"route": "electricity", "children_of_interest": ["rto", "retail-sales", "epm"]},
    {"route": "total-energy", "children_of_interest": []},
]

DATA_PROBES: List[Dict[str, str]] = [
    {"dataset": "petroleum_stve_weekly", "route": "petroleum/stve/data",
     "params": {"frequency": "weekly", "data[0]": "value", "sort[0][column]": "period",
                "sort[0][direction]": "desc", "offset": 0, "length": 60}},
    {"dataset": "natural_gas_storage_monthly", "route": "natural-gas/stor/data",
     "params": {"frequency": "monthly", "data[0]": "value", "sort[0][column]": "period",
                "sort[0][direction]": "desc", "offset": 0, "length": 60}},
    {"dataset": "electricity_rto_hourly_sample", "route": "electricity/rto/data",
     "params": {"frequency": "hourly", "data[0]": "value", "sort[0][column]": "period",
                "sort[0][direction]": "desc", "offset": 0, "length": 48}},
]


def _keyed(ctx: SourceContext, path: str, params: Optional[Dict[str, Any]] = None) -> str:
    key = ctx.require_present("EIA_API_KEY")
    query = {"api_key": key}
    if params:
        query.update(params)
    return f"{API_ROOT}{path}?{urllib.parse.urlencode(query)}"


def run(ctx: SourceContext) -> SourceRun:
    state = SourceRun(SOURCE_ID, CENSUS)
    limiter = ctx.limiter_for("eia", 0.25)  # <= 4 req/s polite
    headers = redact_headers({"Accept": "application/json"})

    try:
        ctx.require_present("EIA_API_KEY")
    except CredentialMissing:
        state.add({
            "source_id": SOURCE_ID, "dataset_id": "api_access",
            "canonical_request_id": "NOT_APPLIED", "source_url_redacted": API_ROOT + "/",
            "retrieved_time_utc": utc_now_iso(),
            "http_status": None, "content_type": None, "content_length": None,
            "raw_path": None, "raw_sha256": "NOT_APPLIED",
            "parser_version": "free_data_frontier@1",
            "authority_status": "BLOCKED_CREDENTIAL",
            "event_time_utc": None, "effective_time_utc": None,
            "available_time_utc": None, "available_time_evidence": None,
            "vintage": None, "retrieval_time_only": True,
            "notes": ["EIA_API_KEY MISSING"],
        })
        return state

    # Route inventory walk.
    for walk in ROUTE_WALK:
        route = walk["route"]
        result = retrieve(
            "GET", _keyed(ctx, f"/{route}"), headers=headers, session=ctx.session,
            limiter=limiter, max_bytes=8 * 1024 * 1024, timeout=TIMEOUT,
            disk_guard=ctx.disk_guard,
        )
        if result.http_status == 200 and not result.error and result.payload:
            dest = ctx.source_dir(SOURCE_ID) / f"route_{route.replace('/', '_')}.json"
            dest.write_bytes(result.payload)
            record = build_record(
                result, source_id=SOURCE_ID, dataset_id=f"route_{route}",
                authority_status="PASS_INVENTORY_ONLY",
                notes=[f"children of interest: {walk['children_of_interest']}"],
            )
            record["raw_path"] = str(dest)
            record["raw_sha256"] = result.raw_sha256
            record["content_length"] = result.bytes_written
            state.add(record)
        else:
            state.add(build_record(
                result, source_id=SOURCE_ID, dataset_id=f"route_{route}",
                authority_status="BLOCKED_NETWORK" if result.error else "BLOCKED_SCHEMA",
                notes=["route metadata fetch failed"],
            ))

    # Bounded data samples.
    for probe in DATA_PROBES:
        result = retrieve(
            "GET", _keyed(ctx, f"/{probe['route']}", probe["params"]), headers=headers,
            session=ctx.session, limiter=limiter, max_bytes=16 * 1024 * 1024,
            timeout=TIMEOUT, disk_guard=ctx.disk_guard,
        )
        if result.http_status == 200 and not result.error and result.payload:
            try:
                strict_json_probe(result.payload, ["response"], probe["dataset"])
            except Exception as exc:
                state.add(build_record(
                    result, source_id=SOURCE_ID, dataset_id=probe["dataset"],
                    authority_status="BLOCKED_SCHEMA", notes=[str(exc)],
                ))
                continue
            dest = ctx.source_dir(SOURCE_ID) / f"{probe['dataset']}.json"
            dest.write_bytes(result.payload)
            record = build_record(
                result, source_id=SOURCE_ID, dataset_id=probe["dataset"],
                authority_status="PASS_SAMPLE",
                notes=["bounded recent sample; EIA revises history — retrieval-time evidence only"],
            )
            record["raw_path"] = str(dest)
            record["raw_sha256"] = result.raw_sha256
            record["content_length"] = result.bytes_written
            state.add(record)
        else:
            state.add(build_record(
                result, source_id=SOURCE_ID, dataset_id=probe["dataset"],
                authority_status="BLOCKED_NETWORK" if result.error else "BLOCKED_SCHEMA",
                notes=["data probe failed"],
            ))

    # Keyless bulk facility probe (HEAD only; no download without a preflight plan).
    bulk = retrieve(
        "HEAD", f"{BULK_ROOT}/EBA.zip", headers=headers, session=ctx.session,
        limiter=limiter, max_bytes=1, timeout=TIMEOUT, disk_guard=ctx.disk_guard,
    )
    state.event("bulk_probe", {
        "url_redacted": f"{BULK_ROOT}/EBA.zip",
        "http_status": bulk.http_status,
        "content_length": bulk.content_length,
        "note": "HEAD-only probe; any bulk pull requires its own disk preflight",
    })
    return state
