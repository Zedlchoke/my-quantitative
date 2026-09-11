"""STOCKS-NG2 P0(b): EODHD field-family-2 probe (short-interests).

Probes ONE candidate second field family -- short interest -- under
the owner's EXISTING EODHD entitlement (the V13-era key, loaded
programmatically from .env; the key value is NEVER echoed into logs,
reports, or exceptions).

Law (plan section 3b): fail-closed -- if the entitlement does not
serve the family (HTTP 401/403 or an EODHD error payload), the verdict
is CANDIDATE_NOT_AUTHORIZED and lane A5 dies at P2; that is an honest
terminal outcome, not a gate failure.

Coverage law: 5-symbol deterministic entitlement probe first; only if
authorized, a 50-symbol deterministic coverage probe measures the
fraction of the pinned 2,168-symbol universe the family serves.  The
frozen floor for a live lane is >= 500 entities FULL coverage; P0
records the measured fraction and an explicitly-labelled PROJECTION
(full-universe verification belongs to the lane, not the probe).

Transport injectable; tests use fake responses and NO key.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable

ENV_PATH_DEFAULT = "/Users/hoangminhlong/my-quantitative/.env"
EODHD_API_BASE = "https://eodhd.com/api"
FAMILY_ENDPOINT = "short-interests"

#: pinned eodhd universe size (substrate manifest: eodhd_div 2,168)
PINNED_EODHD_UNIVERSE = 2168

#: floor for a LIVE A5 lane (plan section 4): >= 500 entities with
#: full coverage; P0 measures a 50-symbol fraction and projects.
FAMILY_ENTITIES_FLOOR = 500

PROBE_SYMBOLS_5 = 5
PROBE_SYMBOLS_50 = 50

_NOT_AUTHORIZED_HTTP = {401, 403}
_NOT_AUTHORIZED_CODES = {401, 403, 404}


class KeyLoadError(Exception):
    """The EODHD key could not be loaded (reported without the value)."""


def load_api_key(env_path: str = ENV_PATH_DEFAULT) -> str:
    """Programmatic .env load.  The value never appears in any message
    or artifact: errors describe the FILE, never the key."""
    if not os.path.isfile(env_path):
        raise KeyLoadError(f".env file absent: {env_path}")
    with open(env_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("EODHD_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if not key:
                    raise KeyLoadError(
                        "EODHD_API_KEY present but empty in .env "
                        f"({env_path})")
                return key
    raise KeyLoadError(
        f"EODHD_API_KEY not defined in {env_path}")


Transport = Callable[[str], "tuple[int, bytes]"]


def eodhd_transport(url: str, timeout: float = 30.0) -> tuple[int, bytes]:
    """Keyless-agnostic GET for eodhd.com (the key rides in the URL
    query built by the caller; responses never logged verbatim)."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "my-quantitative-research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status), resp.read()
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:  # noqa: BLE001
            body = b""
        return int(exc.code), body


def short_interest_url(symbol: str, api_key: str) -> str:
    return (f"{EODHD_API_BASE}/{FAMILY_ENDPOINT}/{symbol}"
            f"?api_token={api_key}&fmt=json")


def control_url(symbol: str, api_key: str) -> str:
    """Known-good entitlement CONTROL endpoint (EOD prices, served to
    this key at V13 time).  Its status separates 'key/transport dead'
    from 'family endpoint absent under the entitlement'."""
    return (f"{EODHD_API_BASE}/eod/{symbol}?api_token={api_key}"
            f"&fmt=json&period=d&from=2026-08-20")


def control_probe(api_key: str, symbol: str = "AAPL.US",
                  transport: Transport | None = None) -> dict:
    transport = transport or eodhd_transport
    try:
        status, body = transport(control_url(symbol, api_key))
    except urllib.error.URLError as exc:
        return {"http_status": None, "alive": False,
                "error": type(exc).__name__}
    return {"http_status": status, "alive": status == 200}


def classify_short_interest_response(status: int,
                                     body: bytes) -> dict:
    """Response-shape law for the short-interests family (pure; tested
    against fake responses without any key):

      NOT_AUTHORIZED - HTTP 401/403, or a JSON error payload carrying
                       an EODHD plan/entitlement code;
      OK_NONEMPTY    - HTTP 200 + JSON list with >= 1 record whose
                       shape looks like a short-interest row;
      OK_EMPTY       - HTTP 200 + empty list (served but no data for
                       the symbol: authorized, zero coverage);
      OK_OTHER_SHAPE - HTTP 200 + JSON list whose rows carry no
                       recognizable short-interest fields (recorded
                       honestly; treated as authorized-but-odd);
      MALFORMED      - HTTP 200 + non-JSON body.
    """
    if status in _NOT_AUTHORIZED_HTTP:
        return {"class": "NOT_AUTHORIZED", "records": 0,
                "http_status": status}
    if status != 200:
        return {"class": f"HTTP_{status}", "records": 0,
                "http_status": status}
    text = body.decode("utf-8", "replace").strip()
    try:
        payload = json.loads(text)
    except ValueError:
        return {"class": "MALFORMED", "records": 0, "http_status": status}
    if isinstance(payload, dict):
        code = payload.get("code")
        if code in _NOT_AUTHORIZED_CODES or "error" in payload:
            return {"class": "NOT_AUTHORIZED", "records": 0,
                    "http_status": status,
                    "payload_code": code,
                    "payload_message": payload.get("message")}
        return {"class": "OK_OTHER_SHAPE", "records": 0,
                "http_status": status}
    if isinstance(payload, list):
        n = len(payload)
        shape_ok = 0
        for rec in payload[:20]:
            if not isinstance(rec, dict):
                continue
            keys = set(rec.keys())
            if keys & {"shortInterest", "short_interest",
                       "daysToCover", "days_to_cover",
                       "shortInterestShareVolume"}:
                shape_ok += 1
        if n == 0:
            return {"class": "OK_EMPTY", "records": 0,
                    "http_status": status}
        cls = ("OK_NONEMPTY" if shape_ok >= 1 else "OK_OTHER_SHAPE")
        return {"class": cls, "records": n, "http_status": status,
                "shape_ok_rows": shape_ok}
    return {"class": "OK_OTHER_SHAPE", "records": 0,
            "http_status": status}


def probe_symbols(symbols: list[str], api_key: str,
                  transport: Transport | None = None,
                  symbol_forms: tuple[str, ...] = ("{s}", "{s}.US"),
                  sleep_between: float = 1.1) -> dict:
    """Probe each symbol under the family endpoint.  Bare and .US
    symbol forms are tried in order per symbol (first served wins --
    US symbols resolve through either); per-symbol class + serving form
    recorded.  When BOTH forms answer HTTP 404 the row is classified
    FAMILY_NOT_SERVED_404 (the endpoint is absent under the
    entitlement -- EODHD's gateway 404s families a plan does not
    include, it does not always emit a JSON 403).  Sleep between
    symbols is polite against plan quotas."""
    transport = transport or eodhd_transport
    rows: list[dict] = []
    form_labels = {"{s}": "probe_bare", "{s}.US": "probe_us"}
    for i, sym in enumerate(symbols):
        if i > 0:
            time.sleep(sleep_between)
        row: dict[str, Any] = {"symbol": sym, "class": "NO_FORM_SERVED",
                               "serving_form": None}
        saw_404_only = True
        for form in symbol_forms:
            target = form.format(s=sym)
            try:
                status, body = transport(short_interest_url(target,
                                                            api_key))
            except urllib.error.URLError as exc:
                row["class"] = f"TRANSPORT_ERROR:{type(exc).__name__}"
                saw_404_only = False
                break
            verdict = classify_short_interest_response(status, body)
            row[form_labels.get(form, form)] = {
                "http_status": verdict["http_status"],
                "class": verdict["class"], "records": verdict["records"]}
            if verdict["class"] == "NOT_AUTHORIZED":
                row["class"] = "NOT_AUTHORIZED"
                row["serving_form"] = None
                return {"rows": rows + [row], "aborted": True,
                        "abort_reason": "NOT_AUTHORIZED"}
            if verdict["class"] == "OK_NONEMPTY":
                row["class"] = "OK_NONEMPTY"
                row["serving_form"] = form
                row["records"] = verdict["records"]
                saw_404_only = False
                break          # first serving form wins
            if verdict["class"] == "OK_OTHER_SHAPE":
                row["class"] = "OK_OTHER_SHAPE"
                row["serving_form"] = form
                saw_404_only = False
                break
            if verdict["class"] == "OK_EMPTY":
                row["class"] = "OK_EMPTY"
                row["serving_form"] = form
                saw_404_only = False
                break          # served (authorized), no data
            if verdict["http_status"] != 404:
                saw_404_only = False
            # HTTP_5xx / MALFORMED / other -> try next form
        if saw_404_only:
            row["class"] = "FAMILY_NOT_SERVED_404"
        rows.append(row)
    return {"rows": rows, "aborted": False, "abort_reason": None}


def deterministic_sample(symbols: list[str], n: int) -> list[str]:
    """Deterministic spread sample of a sorted symbol list (indices
    i * len // n)."""
    ordered = sorted(symbols)
    if n >= len(ordered):
        return ordered
    return [ordered[i * len(ordered) // n] for i in range(n)]


def evaluate_family(probe_50: dict) -> dict:
    """Honest coverage evaluation of the 50-symbol probe + explicitly
    labelled projection against the >= 500-entities floor."""
    rows = probe_50["rows"]
    nonempty = sum(1 for r in rows if r["class"] == "OK_NONEMPTY")
    served = sum(1 for r in rows if r["class"] in
                 ("OK_NONEMPTY", "OK_EMPTY", "OK_OTHER_SHAPE"))
    not_auth = any(r["class"] == "NOT_AUTHORIZED" for r in rows)
    frac_cov = (nonempty / len(rows)) if rows else 0.0
    frac_served = (served / len(rows)) if rows else 0.0
    projected = round(frac_cov * PINNED_EODHD_UNIVERSE)
    return {
        "floor_entities_full_coverage": FAMILY_ENTITIES_FLOOR,
        "probe_symbols": len(rows),
        "symbols_nonempty_data": nonempty,
        "symbols_served_any": served,
        "measured_coverage_fraction": round(frac_cov, 4),
        "measured_served_fraction": round(frac_served, 4),
        "not_authorized_detected": not_auth,
        "pinned_universe_size": PINNED_EODHD_UNIVERSE,
        "projected_entities_with_data": projected,
        "projection_method": ("measured_coverage_fraction x 2168 "
                              "pinned eodhd symbols -- a PROJECTION, "
                              "not a measurement; full-universe "
                              "verification belongs to lane A5"),
        "floor_met_projected": projected >= FAMILY_ENTITIES_FLOOR,
        "floor_met_measured": nonempty >= FAMILY_ENTITIES_FLOOR,
    }
