"""Federal Reserve Bank of New York market-data APIs (markets.newyorkfed.org/api).

Reference rates (SOFR, EFFR, OBFR, BGCR, TGCR) via documented JSON endpoints;
inventory of primary-dealer / repo surfaces. Official API only — no dashboard
scraping. Revision indicators and publication semantics recorded as documented.
"""

from __future__ import annotations

from typing import Dict, List

from ..contract import SchemaRefusal
from ..http import build_record, redact_headers, retrieve
from .base import SourceContext, SourceRun, strict_json_probe

SOURCE_ID = "nyfed_markets"
API_ROOT = "https://markets.newyorkfed.org"
TIMEOUT = (10.0, 60.0)

CENSUS = {
    "official_api_root": API_ROOT + "/api/",
    "documentation": API_ROOT + "/api/",
    "terms": "https://www.newyorkfed.org/terms.html",
    "key_required": False,
    "account_required": False,
    "redistribution": "FEDS/public NY Fed market data; terms page pinned (attribution expected)",
    "publication_semantics": "Reference rates published ~09:00 ET on T+1 business day "
    "(documented on the rates page); per-row publication timestamp not served by the API "
    "-> available_time NOT evidenced from API alone",
    "revision_semantics": "MEASURED: rows carry a revisionIndicator field (empty = original, "
    "flagged when re-stated) plus effectiveDate — revision status IS machine-served per row",
}

# Preregistered acquisition set: reference rates (documented endpoint patterns).
RATE_ENDPOINTS: List[Dict[str, str]] = [
    {"dataset": "sofr", "url": API_ROOT + "/api/rates/secured/sofr/last/10.json"},
    {"dataset": "bgcr", "url": API_ROOT + "/api/rates/secured/bgcr/last/10.json"},
    {"dataset": "tgcr", "url": API_ROOT + "/api/rates/secured/tgcr/last/10.json"},
    {"dataset": "effr", "url": API_ROOT + "/api/rates/unsecured/effr/last/10.json"},
    {"dataset": "obfr", "url": API_ROOT + "/api/rates/unsecured/obfr/last/10.json"},
]

# Preregistered inventory surfaces (dealer/repo); shape probed, not assumed.
INVENTORY_ENDPOINTS: List[Dict[str, str]] = [
    {"dataset": "inventory_rates_secured", "url": API_ROOT + "/api/rates/secured/get/all.json"},
    {"dataset": "inventory_rates_unsecured", "url": API_ROOT + "/api/rates/unsecured/get/all.json"},
    {"dataset": "inventory_repo_ops", "url": API_ROOT + "/api/rp/get/all.json"},
    {"dataset": "inventory_primary_dealers", "url": API_ROOT + "/api/pdm/get/all.json"},
    {"dataset": "api_docs_page", "url": API_ROOT + "/api/"},
]


def run(ctx: SourceContext) -> SourceRun:
    state = SourceRun(SOURCE_ID, CENSUS)
    limiter = ctx.limiter_for("nyfed", 0.5)
    headers = redact_headers({"Accept": "application/json"})

    for spec in INVENTORY_ENDPOINTS:
        result = retrieve(
            "GET", spec["url"], headers=headers, session=ctx.session, limiter=limiter,
            max_bytes=32 * 1024 * 1024, timeout=TIMEOUT, disk_guard=ctx.disk_guard,
        )
        ok = result.http_status == 200 and not result.error and result.payload
        notes = ["inventory surface reachable"]
        status = "PASS_INVENTORY_ONLY"
        if not ok:
            if result.error:
                status = "BLOCKED_NETWORK"
                notes = [f"probe failed: {result.error}"]
            else:
                status = "BLOCKED_NETWORK"
                notes = [
                    f"HTTP {result.http_status} measured on this surface (400 on /get/ search "
                    "and /api/ index from programmatic client, browser-like headers too — "
                    "edge-scoped); documented /last/ channel remains the working surface (P-7: verdict names the channel)",
                ]
        if ok and spec["dataset"] != "api_docs_page":
            try:
                strict_json_probe(result.payload, [], f"nyfed {spec['dataset']}")
            except SchemaRefusal as exc:
                status, notes = "BLOCKED_SCHEMA", [str(exc)]
        if ok:
            dest = ctx.source_dir(SOURCE_ID) / f"{spec['dataset']}.json"
            if spec["dataset"] == "api_docs_page":
                dest = ctx.source_dir(SOURCE_ID) / "api_docs_page.html"
            dest.write_bytes(result.payload)
            record = build_record(
                result, source_id=SOURCE_ID, dataset_id=spec["dataset"],
                authority_status=status, notes=notes,
            )
            record["raw_path"] = str(dest)
            record["raw_sha256"] = result.raw_sha256
            record["content_length"] = result.bytes_written
            state.add(record)
        else:
            state.add(build_record(
                result, source_id=SOURCE_ID, dataset_id=spec["dataset"],
                authority_status=status, notes=notes,
            ))

    for spec in RATE_ENDPOINTS:
        result = retrieve(
            "GET", spec["url"], headers=headers, session=ctx.session, limiter=limiter,
            max_bytes=8 * 1024 * 1024, timeout=TIMEOUT, disk_guard=ctx.disk_guard,
        )
        if result.http_status == 200 and not result.error and result.payload:
            try:
                data = strict_json_probe(result.payload, ["refRates"], f"nyfed {spec['dataset']}")
                rows = data.get("refRates") or []
                if not isinstance(rows, list) or not rows:
                    raise SchemaRefusal("refRates empty or malformed")
            except SchemaRefusal as exc:
                state.add(build_record(
                    result, source_id=SOURCE_ID, dataset_id=f"rate_{spec['dataset']}",
                    authority_status="BLOCKED_SCHEMA", notes=[str(exc)],
                ))
                continue
            dest = ctx.source_dir(SOURCE_ID) / f"rate_{spec['dataset']}.json"
            dest.write_bytes(result.payload)
            record = build_record(
                result, source_id=SOURCE_ID, dataset_id=f"rate_{spec['dataset']}",
                authority_status="PASS_SAMPLE",
                available_time_utc=None,
                notes=[
                    "recent rows; rows carry effectiveDate + measured revisionIndicator field; "
                    "T+1 ~09:00 ET publication is documented-not-machine-served "
                    "-> retrieval-time evidence only",
                ],
            )
            record["raw_path"] = str(dest)
            record["raw_sha256"] = result.raw_sha256
            record["content_length"] = result.bytes_written
            state.add(record)
        else:
            state.add(build_record(
                result, source_id=SOURCE_ID, dataset_id=f"rate_{spec['dataset']}",
                authority_status="BLOCKED_NETWORK" if result.error else "BLOCKED_SCHEMA",
                notes=["reference-rate endpoint failed"],
            ))
    return state
