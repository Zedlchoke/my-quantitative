"""VOL-NG1 P0 ingest: bounded pulls of the plan-frozen consumption set.

Channels (plan section 3, measured liveness 2026-09-12):

1. CBOE official CDN daily-history CSVs (keyless, deterministic):
   ``https://cdn.cboe.com/api/global/us_indices/daily_prices/{NAME}_History.csv``
   for NAME in (VIX, VIX9D, VIX3M, VIX6M).  The plan freezes exactly
   this name census; any other index name is refused (P-7).
2. EODHD family-1 daily EOD for US volatility ETP legs
   (``https://eodhd.com/api/eod/{SYM}.US?fmt=json``), RAW bars primary
   + ``adjusted_close`` cross-check carried in the same response
   (frozen V8 corporate-actions convention).  Living candidates:
   VXX/UVXY/SVXY (plan-named) + a bounded discovery probe (VIXY/VIXM/
   VXZ).  NO options-chain data anywhere (family-2 NOT entitled).
3. EODHD US delisted channel (``/exchange-symbol-list/US?delisted=1``)
   -- the ONLY lawful route to prove dead inverse-vol ETPs (XIV et al.
   returned empty on the plain eod endpoint in the Lead probe).

Key law: ``EODHD_API_KEY`` is loaded programmatically from the
gitignored root ``.env`` and NEVER echoed, logged, or embedded in any
recorded URL (V13; td_probe/ez_vintaged convention inherited verbatim).
Recorded URLs carry ``<REDACTED>`` in place of the key.

Etiquette: <= 1 request / 1.2 s per keyed channel + exponential backoff
(2/4/8 s), max 3 attempts; deterministic refusals (401/403/404) STOP
fail-closed.  Source unreachable after bounded retries => recorded
fail-closed evidence, never fabrication.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

#: The one contact UA this repository's crawlers already operate with
#: (V13 form4 census, 345k+ SEC files; canary_probes.py convention).
UA = "Research my-quantitative@example.com"
TIMEOUT = 60.0
ETIQUETTE_SLEEP_S = 1.2
RETRY_BACKOFF_S = (2.0, 4.0, 8.0)

CBOE_BASE = ("https://cdn.cboe.com/api/global/us_indices/"
             "daily_prices")
#: Plan-frozen index-name census (section 3: VIX, VIX9D, VIX3M, +VIX6M
#: if served).  Nothing else is requested, ever (P-7).
CBOE_INDEX_NAMES = ("VIX", "VIX9D", "VIX3M", "VIX6M")

EODHD_BASE = "https://eodhd.com/api"
#: Plan-named living legs.
ETP_LIVING_CANDIDATES = ("VXX", "UVXY", "SVXY")
#: Bounded living-leg discovery probes (same family, long-vol ETFs/ETNs).
ETP_EXTRA_CANDIDATES = ("VIXY", "VIXM", "VXZ")
#: Dead inverse-vol/short-vol candidates probed on the delisted channel.
DEAD_VOL_CANDIDATES = ("XIV", "TVIX", "ZIV", "XVIX")
#: Never-existed negative controls (must be ABSENT everywhere; P-7).
NEVER_EXISTED_CONTROLS = ("ZZZVIX", "QVIXX")

ENV_PATH_DEFAULT = "/Users/hoangminhlong/my-quantitative/.env"
KEY_NAME = "EODHD_API_KEY"


class IngestBlocked(Exception):
    """Fail-closed ingest state (key missing, deterministic refusal,
    or source unreachable after bounded retries).  Nothing fabricated."""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact(url: str) -> str:
    """Recorded-URL form: the api_token value is never written anywhere."""
    if "api_token=" in url:
        head, _, tail = url.partition("api_token=")
        token = tail.split("&", 1)[0]
        return url.replace(f"api_token={token}", "api_token=<REDACTED>")
    return url


def load_eodhd_key(env_path: str = ENV_PATH_DEFAULT) -> str | None:
    """Load ``EODHD_API_KEY`` from a .env-style file, programmatically.

    Returns the key, or None when absent/empty (fail-closed: the caller
    MUST treat None as ingest-impossible).  The value is never printed,
    logged, or embedded in any raised error or recorded URL.
    """
    if not os.path.exists(env_path):
        return None
    try:
        with open(env_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                if name.strip() == KEY_NAME:
                    value = value.strip().strip('"').strip("'")
                    return value or None
    except OSError:
        return None
    return None


def http_get(url: str, max_attempts: int = 3,
             timeout: float = TIMEOUT) -> dict:
    """Bounded GET with exponential backoff on retryable failures.

    Returns ``{ok, status, body(bytes)|None, attempts, url_redacted,
    retrieved_utc}``.  Deterministic refusals (401/403/404) stop after
    the first attempt (no retry storm); transport errors and 5xx retry
    with 2/4/8 s backoff.  The URL is recorded redacted only.
    """
    attempts = []
    for i in range(max_attempts):
        attempt_no = i + 1
        req = urllib.request.Request(
            url, headers={"User-Agent": UA})
        started = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                attempts.append({
                    "attempt": attempt_no, "status": resp.status,
                    "error": None,
                    "retrieved_utc": now_utc()})
                return {"ok": True, "status": resp.status, "body": body,
                        "attempts": attempts,
                        "url_redacted": redact(url),
                        "retrieved_utc": attempts[-1]["retrieved_utc"],
                        "seconds": round(time.time() - started, 2)}
        except urllib.error.HTTPError as exc:
            attempts.append({
                "attempt": attempt_no, "status": exc.code,
                "error": f"HTTPError {exc.code}",
                "retrieved_utc": now_utc()})
            if exc.code in (401, 403, 404):
                break                     # deterministic refusal: stop
        except Exception as exc:          # transport: retryable
            attempts.append({
                "attempt": attempt_no, "status": None,
                "error": f"{type(exc).__name__}: {exc}",
                "retrieved_utc": now_utc()})
        if i < max_attempts - 1:
            time.sleep(RETRY_BACKOFF_S[min(i, len(RETRY_BACKOFF_S) - 1)])
    last = attempts[-1] if attempts else {"status": None, "error": "no attempt"}
    return {"ok": False, "status": last.get("status"), "body": None,
            "attempts": attempts, "url_redacted": redact(url),
            "retrieved_utc": now_utc()}


# --------------------------------------------------------------------------- #
# CBOE official index histories (keyless)
# --------------------------------------------------------------------------- #

def cboe_url(index_name: str) -> str:
    if index_name not in CBOE_INDEX_NAMES:
        raise IngestBlocked(
            f"index name {index_name!r} is outside the plan-frozen CBOE "
            f"census {CBOE_INDEX_NAMES}: refused (P-7)")
    return f"{CBOE_BASE}/{index_name}_History.csv"


def _sink_body(body: bytes, raw_sink_path: str | None) -> None:
    if raw_sink_path:
        os.makedirs(os.path.dirname(raw_sink_path) or ".", exist_ok=True)
        with open(raw_sink_path, "wb") as fh:
            fh.write(body)


def pull_cboe(index_name: str,
              raw_sink_path: str | None = None) -> dict:
    """Pull one official CBOE daily-history CSV.  Fail-closed: a non-200
    is RECORDED (served/unserved census), never fabricated around.  The
    exact retrieved bytes are written to ``raw_sink_path`` (single
    retrieval; verify-on-read happens against this file)."""
    url = cboe_url(index_name)
    res = http_get(url)
    row: dict = {
        "index_name": index_name,
        "url": res["url_redacted"],
        "http_status": res["status"],
        "retrieved_utc": res["retrieved_utc"],
        "attempts": res["attempts"],
    }
    if res["ok"] and res["body"]:
        body = res["body"]
        _sink_body(body, raw_sink_path)
        row.update({
            "served": True,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        })
    else:
        row.update({"served": False, "bytes": 0, "sha256": None,
                    "note": "unserved under the official pattern; "
                            "fail-closed census row (no alternates invented)"})
    return row


# --------------------------------------------------------------------------- #
# EODHD family-1 EOD (keyed; RAW primary + adjusted cross-check)
# --------------------------------------------------------------------------- #

def eodhd_eod_url(symbol: str, key: str) -> str:
    return f"{EODHD_BASE}/eod/{symbol}.US?fmt=json&api_token={key}"


def pull_eodhd_eod(symbol: str, key: str,
                   raw_sink_path: str | None = None) -> dict:
    """Pull the full family-1 daily EOD history for one US ETP leg.

    RAW (``close``) is primary; ``adjusted_close`` rides along in the
    same response for the corp-actions cross-check (V8 convention).
    A 404/empty body is recorded as ``served: false`` (fail-closed
    census row) -- delisted names are proven only via the delisted
    channel, never by inventing bars.  Non-empty bytes are written to
    ``raw_sink_path`` (single retrieval).
    """
    url = eodhd_eod_url(symbol, key)
    time.sleep(ETIQUETTE_SLEEP_S)              # keyed-channel etiquette
    res = http_get(url)
    row: dict = {
        "symbol": symbol,
        "url": res["url_redacted"],
        "http_status": res["status"],
        "retrieved_utc": res["retrieved_utc"],
        "attempts": res["attempts"],
    }
    if not res["ok"] or not res["body"]:
        row.update({"served": False, "bytes": 0, "sha256": None,
                    "bars": 0, "note": "empty/unserved on the plain eod "
                                       "endpoint (fail-closed census row)"})
        return row
    body = res["body"]
    text = body.decode("utf-8", "replace")
    if text.strip() in ("", "[]"):
        row.update({"served": False, "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "bars": 0,
                    "note": "empty list on the plain eod endpoint "
                            "(Lead-probe semantics reproduced)"})
        return row
    try:
        bars = json.loads(text)
        if not isinstance(bars, list):
            raise ValueError("not a JSON list")
    except (ValueError, json.JSONDecodeError) as exc:
        row.update({"served": False, "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "bars": 0,
                    "note": f"unparseable eod payload: {type(exc).__name__}"})
        return row
    _sink_body(body, raw_sink_path)
    dates = sorted(b.get("date", "") for b in bars if isinstance(b, dict))
    row.update({
        "served": True,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "bars": len(bars),
        "first_bar": dates[0] if dates else None,
        "last_bar": dates[-1] if dates else None,
    })
    return row


# --------------------------------------------------------------------------- #
# EODHD US delisted channel (keyed; the only lawful dead-name route)
# --------------------------------------------------------------------------- #

def eodhd_delisted_url(key: str) -> str:
    return (f"{EODHD_BASE}/exchange-symbol-list/US"
            f"?delisted=1&fmt=json&api_token={key}")


def pull_eodhd_delisted(key: str, raw_sink_path: str | None = None) -> dict:
    """Pull the US delisted symbol list ONCE (single bounded request).

    The full response is a large array; it is sha256-digested, and the
    per-symbol records for the frozen candidate set (dead vol ETPs +
    living legs + never-existed controls) are extracted into the
    committed census.  If ``raw_sink_path`` is given, the full body is
    written there (UNTRACKED scratch, disclosed in the gate) so the
    digest is verify-on-read locally; the committed artifact stays the
    census + digest.
    """
    url = eodhd_delisted_url(key)
    time.sleep(ETIQUETTE_SLEEP_S)
    res = http_get(url, timeout=180.0)
    out: dict = {
        "url": res["url_redacted"],
        "http_status": res["status"],
        "retrieved_utc": res["retrieved_utc"],
        "attempts": res["attempts"],
    }
    if not res["ok"] or not res["body"]:
        out.update({"served": False, "sha256": None,
                    "total_symbols": 0, "matches": {},
                    "note": "delisted channel unserved (fail-closed)"})
        return out
    body = res["body"]
    digest = hashlib.sha256(body).hexdigest()
    if raw_sink_path:
        os.makedirs(os.path.dirname(raw_sink_path) or ".", exist_ok=True)
        with open(raw_sink_path, "wb") as fh:
            fh.write(body)
    text = body.decode("utf-8", "replace")
    try:
        entries = json.loads(text)
        if not isinstance(entries, list):
            raise ValueError("not a JSON list")
    except (ValueError, json.JSONDecodeError) as exc:
        out.update({"served": False, "sha256": digest,
                    "total_symbols": 0, "matches": {},
                    "note": f"unparseable delisted payload: "
                            f"{type(exc).__name__}"})
        return out
    by_code: dict[str, dict] = {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        # the delisted channel's records carry "Code" (capital C) --
        # matched case-insensitively so the census cannot miss a name
        # on a key-casing artifact (fail-closed both ways)
        code = e.get("Code") or e.get("code")
        if code:
            by_code[str(code).upper()] = e
    wanted = (DEAD_VOL_CANDIDATES + ETP_LIVING_CANDIDATES
              + ETP_EXTRA_CANDIDATES + NEVER_EXISTED_CONTROLS)
    matches = {c: by_code.get(c) for c in wanted if c in by_code}
    out.update({
        "served": True,
        "sha256": digest,
        "bytes": len(body),
        "total_symbols": len(entries),
        "wanted": list(wanted),
        "matches": matches,
        "dead_present": {c: (c in by_code) for c in DEAD_VOL_CANDIDATES},
        "controls_absent": {c: (c not in by_code)
                            for c in NEVER_EXISTED_CONTROLS},
        "raw_sink_path": raw_sink_path,
    })
    return out


def probe_plain_eod_empty(symbol: str, key: str) -> dict:
    """Explicit negative-semantics probe: the plain eod endpoint for a
    dead name (Lead probe: XIV.US returned an empty list there).  This
    is the fail-closed contrast that makes the delisted channel the
    only lawful proof route."""
    return pull_eodhd_eod(symbol, key)
