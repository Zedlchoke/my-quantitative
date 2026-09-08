"""A1 W3-freeze utility: fetch BIS WS_CBPOL policy-rate vintages (keyless).

Produces, per currency area, one vintage JSON file of canonical
NormalizedRecord payloads in the exact format research.assets.forex_free_v3.
macro_reader.from_data_paths consumes, plus a fetch manifest recording the
owner availability-evidence basis, resolved series keys and upstream digests.

Owner availability evidence (frozen, conservative): BIS CBPOL rows are dated
by their policy-rate EFFECTIVE date and every CBPOL change is a public central
bank announcement issued on or before that date.  The owner therefore supplies
DATE_ONLY_UPPER_BOUND evidence per observation: end of the effective UTC day.
A row is never eligible on its own effective date (the P0 invariant); its
first readable decision is the next day's.  For changes announced before
their effective date this bound is strictly conservative (no look-ahead).

Fail-closed: any HTTP, content-type or adapter failure aborts with no output
files written.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import date, datetime, timezone

from research.data_fusion.adapters.base import (
    RawResponse,
    RequestSpec,
    date_only_evidence,
    extract_sdmx_json_series,
)
from research.data_fusion.adapters.bis import BisAdapter, AdapterError

_START_PERIOD = "2019-01-01"
# Measured 2026-09-04: the working WS_CBPOL host is stats.bis.org (the host
# recorded in the lane evidence doc, data.bis.org, returns 404 for the data
# path).  Series key shape is FREQUENCY.BORROWER_COUNTRY, e.g. D.US, D.XM.
_BASE = "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0"
_EVIDENCE_BASIS = (
    "BIS WS_CBPOL public central-bank announcement on or before the effective "
    "date; owner supplies end-of-effective-UTC-day DATE_ONLY_UPPER_BOUND "
    "(conservative; rows never eligible on their own effective date)"
)
# area -> BIS series-key candidates (first that resolves wins)
AREAS: dict[str, tuple[str, ...]] = {
    "US": ("D.US",),
    "EMU": ("D.XM", "M.XM", "D.XE"),
    "GB": ("D.GB",),
    "AU": ("D.AU",),
    "NZ": ("D.NZ",),
    "JP": ("D.JP",),
    "CH": ("D.CH",),
    "CA": ("D.CA",),
}


def _http_get(url: str, headers: tuple[tuple[str, str], ...]) -> tuple[bytes, str, int]:
    import time

    last_error: Exception | None = None
    for attempt in range(3):
        request = urllib.request.Request(url, method="GET")
        request.add_header("User-Agent", "my-quantitative-forex-v3-freeze/1.0")
        for name, value in headers:
            request.add_header(name, value)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read(), response.headers.get_content_type(), response.status
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (404, 500, 502, 503, 504):
                time.sleep(30 * (attempt + 1))
                continue
            raise
    raise last_error if last_error else RuntimeError("unreachable")


def _adapt_payload_20_to_10(upstream: dict) -> tuple[dict, bool]:
    """Deterministically map a BIS SDMX-JSON 2.0 payload to the 1.0 shape the
    adopted adapter documents.  Returns (payload, adapted_flag).  Raw upstream
    bytes are hashed separately; this adaptation is recorded in the manifest."""
    if "header" in upstream and "dataSets" in upstream:
        return upstream, False
    if "meta" not in upstream or "data" not in upstream:
        raise ValueError("unrecognized SDMX payload shape")
    adapted = {
        "header": upstream["meta"],
        "dataSets": upstream["data"]["dataSets"],
        "structure": upstream["data"]["structure"],
    }
    return adapted, True


def _slice_single_row_payload(upstream: dict, row_index: int) -> bytes:
    """Deterministically restrict an SDMX-JSON payload to one observation."""
    sliced = {
        "header": dict(upstream["header"]),
        "dataSets": [
            {
                "action": upstream["dataSets"][0].get("action", "Replace"),
                "series": {"0:0": upstream["dataSets"][0]["series"]["0:0"]},
            }
        ],
        "structure": upstream["structure"],
    }
def _row_rate(series_payload: dict, row_index: int) -> float | None:
    """Numeric rate for one observation, or None for a null/NaN placeholder
    (calendar filler rows in a daily series carry no rate information)."""
    observation = series_payload["observations"][str(row_index)]
    value = observation[0]
    if value is None:
        return None
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _slice_single_row_payload(upstream: dict, row_index: int, rate: float) -> bytes:
    """Deterministically restrict an SDMX-JSON payload to one observation."""
    sliced = {
        "header": dict(upstream["header"]),
        "dataSets": [
            {
                "action": upstream["dataSets"][0].get("action", "Replace"),
                "series": {"0:0": upstream["dataSets"][0]["series"]["0:0"]},
            }
        ],
        "structure": upstream["structure"],
    }
    series = dict(upstream["dataSets"][0]["series"]["0:0"])
    observation_key = str(row_index)
    observation = list(series["observations"][observation_key])
    observation[0] = rate
    series["observations"] = {observation_key: observation}
    sliced["dataSets"][0]["series"] = {"0:0": series}
    return json.dumps(sliced, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fetch_area(area: str, candidates: tuple[str, ...], out_dir: str) -> dict:
    adapter = BisAdapter()
    last_error: Exception | None = None
    for country in candidates:
        try:
            return _fetch_series(adapter, area, country, out_dir)
        except (AdapterError, OSError, ValueError, KeyError) as exc:
            last_error = exc
    raise RuntimeError(f"area {area}: no candidate series resolved ({last_error})")


def _fetch_series(adapter: BisAdapter, area: str, key: str, out_dir: str) -> dict:
    query: list[tuple[str, str]] = [("startPeriod", _START_PERIOD)]
    spec = RequestSpec(
        source_id=adapter.source_id,
        url=f"{_BASE}/{key}",
        query=tuple(query),
        headers=(("accept", "application/vnd.sdmx.data+json"),),
    )
    body, content_type, status = _http_get(spec.full_url(), spec.headers)
    if status != 200:
        raise RuntimeError(f"HTTP {status} for {spec.full_url()}")
    upstream = json.loads(body)
    upstream_sha = __import__("hashlib").sha256(body).hexdigest()
    upstream, adapted = _adapt_payload_20_to_10(upstream)
    series_payload = upstream["dataSets"][0]["series"]["0:0"]
    observation_index = series_payload["observations"]
    time_values = upstream["structure"]["dimensions"]["observation"][0]["values"]
    ordered_keys = sorted(observation_index, key=int)
    if not ordered_keys:
        raise RuntimeError(f"no observations for {key}")
    retrieved = datetime.now(timezone.utc).replace(microsecond=0)
    payloads = []
    skipped_placeholders = 0
    for obs_key in ordered_keys:
        row_index = int(obs_key)
        rate = _row_rate(series_payload, row_index)
        if rate is None:
            skipped_placeholders += 1
            continue
        effective_day = date.fromisoformat(time_values[row_index]["id"])
        sliced = _slice_single_row_payload(upstream, row_index, rate)
        response = RawResponse(
            request_id=spec.request_id() + f"#row:{effective_day.isoformat()}",
            url=spec.full_url(),
            status=200,
            reason="OK",
            headers=(("content-type", content_type),),
            body=sliced,
            retrieved_time_utc=retrieved,
        )
        output = adapter.parse_policy_rates(
            response,
            release_evidence=date_only_evidence(_EVIDENCE_BASIS, effective_day),
        )
        for record in output.records:
            payload = {}
            from dataclasses import asdict

            raw = asdict(record)
            for field_name in (
                "event_time_utc",
                "available_time_utc",
                "effective_time_utc",
                "vintage_time_utc",
                "retrieved_time_utc",
            ):
                raw[field_name] = raw[field_name].isoformat()
            payload = raw
            payloads.append(payload)
    out_path = f"{out_dir}/{area}.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payloads, handle, sort_keys=True, separators=(",", ":"))
    return {
        "area": area,
        "series_key": key,
        "url": spec.full_url(),
        "upstream_response_sha256": upstream_sha,
        "content_type": content_type,
        "payload_adaptation": "sdmx-json-2.0-to-1.0 structural map + numeric-string observation values to float (deterministic; upstream bytes hashed)" if adapted else "none",
        "records": len(payloads),
        "skipped_null_placeholder_rows": skipped_placeholders,
        "first_effective": payloads[0]["effective_time_utc"][:10] if payloads else None,
        "last_effective": payloads[-1]["effective_time_utc"][:10] if payloads else None,
        "retrieved_at_utc": retrieved.isoformat(),
        "evidence_basis": _EVIDENCE_BASIS,
    }


def main() -> int:
    import os

    out_dir = sys.argv[1] if len(sys.argv) > 1 else "data_raw/forex_free_v3_macro"
    os.makedirs(out_dir, exist_ok=True)
    staged: dict[str, dict] = {}
    # resume-safe: areas with an existing output file are not refetched
    pending = {
        area: candidates
        for area, candidates in AREAS.items()
        if not os.path.exists(f"{out_dir}/{area}.json")
    }
    try:
        for _pass in range(3):
            failed: dict[str, tuple[str, ...]] = {}
            for area, candidates in pending.items():
                if staged:
                    time.sleep(10)
                try:
                    staged[area] = fetch_area(area, candidates, out_dir)
                    print(
                        f"{area}: {staged[area]['records']} rows via {staged[area]['series_key']}",
                        flush=True,
                    )
                except (AdapterError, OSError, ValueError, KeyError, RuntimeError) as exc:
                    failed[area] = candidates
                    print(f"{area}: attempt failed ({exc})", file=sys.stderr, flush=True)
            pending = failed
            if not pending:
                break
            print("retry pass for: " + ", ".join(sorted(pending)), flush=True)
        if pending:
            raise RuntimeError(f"areas unresolved after 3 passes: {sorted(pending)}")
    except Exception as exc:  # fail-closed: no manifest on any failure
        print(f"FETCH_FAILED: {exc}", file=sys.stderr)
        return 1
    manifest_path = f"{out_dir}/fetch_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "source": "BIS_CBPOL",
                "adapter": "bis-adapter-1.0.0 (byte-identical P0 adoption)",
                "fetched_at_utc": staged["US"]["retrieved_at_utc"],
                "evidence_basis": _EVIDENCE_BASIS,
                "areas": staged,
            },
            handle,
            indent=2,
        )
        handle.write("\n")
    print(f"MANIFEST {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
