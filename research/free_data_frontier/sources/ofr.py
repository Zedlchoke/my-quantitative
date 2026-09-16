"""OFR Short-Term Funding Monitor (data.financialresearch.gov/v1).

Census -> inventory mnemonics -> curated funding/liquidity timeseries.
Selection is keyword-based on preregistered metadata terms; never PnL-based.
"""

from __future__ import annotations

from urllib.parse import urlencode

from ..contract import SchemaRefusal
from ..http import build_record, redact_headers, retrieve
from .base import SourceContext, SourceRun, strict_json_probe

SOURCE_ID = "ofr_stfm"
BASE_URL = "https://data.financialresearch.gov/v1"
TIMEOUT = (10.0, 60.0)
CURATED_MNEMONICS = (
    "FNYR-SOFR-A",
    "FNYR-EFFR-A",
    "FNYR-BGCR-A",
    "FNYR-TGCR-A",
    "FNYR-OBFR-A",
)

CENSUS = {
    "official_api_root": BASE_URL + "/",
    "documentation": "https://www.financialresearch.gov/short-term-funding-monitor/",
    "terms": "https://www.financialresearch.gov/data/",
    "api_shape": "GET /v1/metadata/mnemonics/, GET /v1/series/full/?mnemonic=...",
    "key_required": False,
    "account_required": False,
    "redistribution": "US-government-authored data; OFR data disclaimers pinned at census",
    "revision_semantics": "OFR publishes revised STFM data; per-row revision indicator not assumed",
}

def mnemonics_url() -> str:
    return f"{BASE_URL}/metadata/mnemonics/"


def full_series_url(mnemonic: str) -> str:
    return f"{BASE_URL}/series/full/?{urlencode({'mnemonic': mnemonic})}"


def run(ctx: SourceContext) -> SourceRun:
    state = SourceRun(SOURCE_ID, CENSUS)
    limiter = ctx.limiter_for("ofr", 0.5)  # <= 2 req/s polite
    headers = redact_headers({"Accept": "application/json"})

    inv = retrieve(
        "GET", mnemonics_url(), headers=headers, session=ctx.session,
        limiter=limiter, max_bytes=8 * 1024 * 1024, timeout=TIMEOUT,
        disk_guard=ctx.disk_guard,
    )
    if inv.error or inv.http_status != 200:
        state.add(build_record(
            inv, source_id=SOURCE_ID, dataset_id="inventory_mnemonics",
            authority_status="BLOCKED_NETWORK" if inv.error else "BLOCKED_SCHEMA",
            notes=["GET /v1/metadata/mnemonics/ failed"],
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

    missing = sorted(set(CURATED_MNEMONICS) - set(mnemonics))
    if missing:
        state.notes.append(f"curated mnemonics absent from inventory: {missing}")
    selected = [m for m in CURATED_MNEMONICS if m in set(mnemonics)]
    state.event("curated_selection", {
        "selection_basis": "preregistered reference-rate identities; no outcomes",
        "inventory_count": len(mnemonics),
        "count": len(selected),
        "mnemonics": selected,
    })

    series_dir = ctx.source_dir(SOURCE_ID) / "series"
    series_dir.mkdir(parents=True, exist_ok=True)
    for mnemonic in selected:
        ts = retrieve(
            "GET", full_series_url(mnemonic),
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
                notes=["full series response; revisions unverified: retrieval-time evidence only"],
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
