"""NOAA/NWS api.weather.gov station metadata + observations for a small
preregistered energy/agriculture location set. No NOAA mirroring; raw weather
is not a trading signal; historical PIT authority fails closed (observation
timestamps are event times; publication times are not served)."""

from __future__ import annotations

from typing import Any, Dict

from ..http import build_record, redact_headers, retrieve
from .base import SourceContext, SourceRun, strict_json_probe

SOURCE_ID = "nws_observations"
API_ROOT = "https://api.weather.gov"
TIMEOUT = (10.0, 60.0)
LIMIT = 24  # bounded recent observations per station

CENSUS = {
    "official_api_root": API_ROOT,
    "documentation": "https://www.weather.gov/documentation/services-web-api",
    "terms": "https://www.weather.gov/disclaimer",
    "key_required": False,
    "account_required": False,
    "rate_limit": "polite rate limits honored (<= 4 req/s here); User-Agent required",
    "redistribution": "US-government work; NOAA/NWS disclaimers pinned",
    "preregistered_locations": {
        "KOKC": "Oklahoma City OK — natural-gas/energy demand hub",
        "KDDC": "Dodge City KS — wheat-belt agriculture",
        "KBIS": "Bismarck ND — spring-wheat agriculture + energy state",
        "KLBB": "Lubbock TX — cotton/wheat agriculture near Permian energy",
    },
    "pit_note": "observations carry event timestamps only; publication time not served -> "
    "retrieval-time evidence only; historical scored joins unauthorized without "
    "separate release-time evidence",
}


def run(ctx: SourceContext) -> SourceRun:
    state = SourceRun(SOURCE_ID, CENSUS)
    limiter = ctx.limiter_for("nws", 0.25)
    headers = redact_headers({
        "User-Agent": "my-quantitative-free-data-frontier/1.0 (internal research use)",
        "Accept": "application/geo+json",
    })

    for station in CENSUS["preregistered_locations"]:
        meta = retrieve(
            "GET", f"{API_ROOT}/stations/{station}", headers=headers,
            session=ctx.session, limiter=limiter, max_bytes=2 * 1024 * 1024,
            timeout=TIMEOUT, disk_guard=ctx.disk_guard,
        )
        if meta.http_status == 200 and not meta.error and meta.payload:
            dest = ctx.source_dir(SOURCE_ID) / f"station_{station}.json"
            dest.write_bytes(meta.payload)
            record = build_record(
                meta, source_id=SOURCE_ID, dataset_id=f"station_{station}",
                authority_status="PASS_SAMPLE",
                notes=["station metadata"],
            )
            record["raw_path"] = str(dest)
            record["raw_sha256"] = meta.raw_sha256
            record["content_length"] = meta.bytes_written
            state.add(record)
        else:
            state.add(build_record(
                meta, source_id=SOURCE_ID, dataset_id=f"station_{station}",
                authority_status="BLOCKED_NETWORK" if meta.error else "BLOCKED_SCHEMA",
                notes=["station metadata fetch failed"],
            ))

        obs = retrieve(
            "GET", f"{API_ROOT}/stations/{station}/observations?limit={LIMIT}",
            headers=headers, session=ctx.session, limiter=limiter,
            max_bytes=8 * 1024 * 1024, timeout=TIMEOUT, disk_guard=ctx.disk_guard,
        )
        if obs.http_status == 200 and not obs.error and obs.payload:
            try:
                data = strict_json_probe(obs.payload, [], f"nws observations {station}")
                if isinstance(data, dict):
                    features = data.get("features", [])
                else:
                    features = []
            except Exception as exc:
                state.add(build_record(
                    obs, source_id=SOURCE_ID, dataset_id=f"observations_{station}",
                    authority_status="BLOCKED_SCHEMA", notes=[str(exc)],
                ))
                continue
            dest = ctx.source_dir(SOURCE_ID) / f"observations_{station}.json"
            dest.write_bytes(obs.payload)
            record = build_record(
                obs, source_id=SOURCE_ID, dataset_id=f"observations_{station}",
                authority_status="PASS_SAMPLE",
                notes=[f"{len(features)} recent observations; event-time only (PIT note in census)"],
            )
            record["raw_path"] = str(dest)
            record["raw_sha256"] = obs.raw_sha256
            record["content_length"] = obs.bytes_written
            state.add(record)
        else:
            state.add(build_record(
                obs, source_id=SOURCE_ID, dataset_id=f"observations_{station}",
                authority_status="BLOCKED_NETWORK" if obs.error else "BLOCKED_SCHEMA",
                notes=["observations fetch failed"],
            ))
    return state
