"""OFR Short-Term Funding Monitor (data.financialresearch.gov/v1).

Census -> inventory mnemonics -> curated funding/liquidity timeseries.
Selection is keyword-based on preregistered metadata terms; never PnL-based.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ..contract import SchemaRefusal
from ..http import build_record, redact_headers, retrieve
from .base import SourceContext, SourceRun, strict_json_probe

SOURCE_ID = "ofr_stfm"
BASE_URL = "https://data.financialresearch.gov/v1"
TIMEOUT = (10.0, 60.0)
MAX_METADATA_SCANS = 400
MAX_SERIES = 12

CENSUS = {
    "official_api_root": BASE_URL + "/",
    "documentation": "https://www.financialresearch.gov/short-term-funding-monitor/",
    "terms": "https://www.financialresearch.gov/data/",
    "api_shape": "GET /v1/mnemonics/, GET /v1/metadata/{mnemonic}, GET /v1/timeseries/{mnemonic}",
    "key_required": False,
    "account_required": False,
    "redistribution": "US-government-authored data; OFR data disclaimers pinned at census",
    "revision_semantics": "OFR publishes revised STFM data; per-row revision indicator not assumed",
}

# Preregistered keyword curation over mnemonic metadata (no PnL involvement).
FUNDING_KEYWORDS = [
    "repo",
    "repurchase",
    "sofr",
    "funding",
    "money market",
    "commercial paper",
    "certificate of deposit",
    "treasury collateral",
    "lending",
]


def run(ctx: SourceContext) -> SourceRun:
    state = SourceRun(SOURCE_ID, CENSUS)
    limiter = ctx.limiter_for("ofr", 0.5)  # <= 2 req/s polite
    headers = redact_headers({"Accept": "application/json"})

    inv = retrieve(
        "GET", f"{BASE_URL}/mnemonics/", headers=headers, session=ctx.session,
        limiter=limiter, max_bytes=8 * 1024 * 1024, timeout=TIMEOUT,
        disk_guard=ctx.disk_guard,
    )
    if inv.error or inv.http_status != 200:
        state.add(build_record(
            inv, source_id=SOURCE_ID, dataset_id="inventory_mnemonics",
            authority_status="BLOCKED_NETWORK" if inv.error else "BLOCKED_SCHEMA",
            notes=["GET /v1/mnemonics/ failed"],
        ))
        return state
    try:
        data = strict_json_probe(inv.payload or b"", [], "ofr mnemonics")
    except SchemaRefusal as exc:
        state.add(build_record(
            inv, source_id=SOURCE_ID, dataset_id="inventory_mnemonics",
            authority_status="BLOCKED_SCHEMA", notes=[str(exc)],
        ))
        return state
    if isinstance(data, dict) and "mnemonics" in data:
        data = data["mnemonics"]
    if not isinstance(data, list) or not data:
        state.add(build_record(
            inv, source_id=SOURCE_ID, dataset_id="inventory_mnemonics",
            authority_status="BLOCKED_SCHEMA", notes=["mnemonics payload is not a non-empty list"],
        ))
        return state
    mnemonics = [str(m) for m in data]

    dest = ctx.source_dir(SOURCE_ID) / "inventory_mnemonics.json"
    dest.write_bytes(inv.payload or b"")
    record = build_record(
        inv, source_id=SOURCE_ID, dataset_id="inventory_mnemonics",
        authority_status="PASS_INVENTORY_ONLY", notes=[f"{len(mnemonics)} mnemonics"],
    )
    record["raw_path"] = str(dest)
    run_state_set_raw(record, inv.raw_sha256, inv.bytes_written)
    state.add(record)

    # Bounded metadata scan for the preregistered funding/liquidity keywords.
    selected: List[str] = []
    scanned = 0
    for mnemonic in mnemonics:
        if scanned >= MAX_METADATA_SCANS:
            state.notes.append(f"metadata scan bounded at {MAX_METADATA_SCANS}")
            break
        meta = retrieve(
            "GET", f"{BASE_URL}/metadata/{mnemonic}", headers=headers,
            session=ctx.session, limiter=limiter, max_bytes=512 * 1024,
            timeout=TIMEOUT, disk_guard=ctx.disk_guard,
        )
        scanned += 1
        if meta.error or meta.http_status != 200 or not meta.payload:
            continue
        text = meta.payload.decode("utf-8", errors="replace").lower()
        if any(keyword in text for keyword in FUNDING_KEYWORDS):
            selected.append(mnemonic)

    state.event("curated_selection", {"scanned": scanned, "count": len(selected),
                                      "mnemonics": selected})

    series_dir = ctx.source_dir(SOURCE_ID) / "series"
    for mnemonic in selected[:MAX_SERIES]:
        ts = retrieve(
            "GET", f"{BASE_URL}/timeseries/{mnemonic}?format=json&limit=120",
            headers=headers, session=ctx.session, limiter=limiter,
            max_bytes=8 * 1024 * 1024, timeout=TIMEOUT, disk_guard=ctx.disk_guard,
        )
        if ts.http_status == 200 and not ts.error and ts.payload:
            ok = _looks_like_timeseries(ts.payload)
            if not ok:
                state.add(build_record(
                    ts, source_id=SOURCE_ID, dataset_id=f"series_{mnemonic}",
                    authority_status="BLOCKED_SCHEMA",
                    notes=["timeseries payload unexpected shape"],
                ))
                continue
            dest = series_dir / f"{_safe_name(mnemonic)}.json"
            dest.write_bytes(ts.payload)
            record = build_record(
                ts, source_id=SOURCE_ID, dataset_id=f"series_{mnemonic}",
                authority_status="PASS_SAMPLE",
                notes=["bounded recent sample; revisions unverified: retrieval-time evidence only"],
            )
            record["raw_path"] = str(dest)
            run_state_set_raw(record, ts.raw_sha256, ts.bytes_written)
            state.add(record)
        else:
            state.add(build_record(
                ts, source_id=SOURCE_ID, dataset_id=f"series_{mnemonic}",
                authority_status="BLOCKED_NETWORK" if ts.error else "BLOCKED_SCHEMA",
                notes=["timeseries retrieval failed"],
            ))
    return state


def _looks_like_timeseries(payload: bytes) -> bool:
    import json

    try:
        data = json.loads(payload)
    except ValueError:
        return False
    return isinstance(data, (list, dict))


def run_state_set_raw(record, sha256_hex: str, length: int) -> None:
    record["raw_sha256"] = sha256_hex
    record["content_length"] = length


def _safe_name(mnemonic: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in mnemonic)
