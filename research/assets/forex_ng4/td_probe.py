"""FOREX-NG4 P0 Twelve Data EURUSD probe (single-shot, fail-closed).

The plan (plans/PLAN_forex_ng4.md sec 2-3) funds the EZ-economy frontier
on EURUSD spot under the OWNER's EXISTING Twelve Data entitlement and
mandates a P0 probe: ``time_series`` 1day, 5000 bars, ONE call (+ at most
ONE retry, and only on transport timeout).  If the key is absent, the
endpoint errors, or the entitlement refuses (403/quota), EURUSD is
UNAVAILABLE and the gate records BLOCKED_DATA honestly -- the cycle dies
in P0 rather than borrowing a bar.

Key law (V9/V1 precedent, inherited):

- ``TWELVE_DATA_API_KEY`` is loaded PROGRAMMATICALLY from the gitignored
  root ``.env``; the value is NEVER echoed into any log, artifact,
  exception message or URL record (only ``key_present`` booleans and the
  key NAME are ever recorded);
- no endpoint other than ``/time_series`` is ever called by this module;
- the raw response bytes are pinned UNTRACKED under
  ``data_raw/forex_ng4_spot/``; the committed pin manifest carries the
  sha256 (FOREX-NG1 spot pin law, inherited).

Network isolation: tests inject a fake transport, so this module's test
coverage performs zero network calls.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Mapping

#: Root .env of the main checkout (owner-placed key; gitignored there).
ENV_PATH_DEFAULT = "/Users/hoangminhlong/my-quantitative/.env"

KEY_NAME = "TWELVE_DATA_API_KEY"

#: The ONLY endpoint this module may ever call.
ENDPOINT = "https://api.twelvedata.com/time_series"
SYMBOL = "EUR/USD"
PAIR = "EURUSD"
INTERVAL = "1day"
OUTPUTSIZE = 5000
TIMEOUT_SECONDS = 30.0

#: Untracked pinned-bytes directory (data_raw/ is NOT gitignored in this
#: worktree: the raw file stays untracked; only the committed manifest
#: pins it by sha256).
PIN_DIR_DEFAULT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data_raw",
    "forex_ng4_spot"))
PIN_FILE = "EURUSD.json"

#: Params recorded in evidence -- the apikey is NEVER part of any record.
SAFE_PARAMS = {"symbol": SYMBOL, "interval": INTERVAL,
               "outputsize": OUTPUTSIZE}


class ProbeError(Exception):
    """Base: probe bookkeeping error (never carries the key)."""


class ProbeUnavailable(ProbeError):
    """EURUSD is UNAVAILABLE under the current entitlement (honest
    BLOCKED_DATA path -- the caller records it, never repairs it)."""


def load_api_key(env_path: str = ENV_PATH_DEFAULT) -> str | None:
    """Load ``TWELVE_DATA_API_KEY`` from a .env-style file.

    Returns the key, or ``None`` when the file/key is absent or empty
    (fail-closed: the caller MUST treat None as UNAVAILABLE).  The value
    is never printed, logged, or embedded in any raised error.
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


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _describe_http_error(exc: Exception) -> dict:
    """Evidence for an HTTP error -- never includes the URL/query (the
    query embeds the key)."""
    if isinstance(exc, urllib.error.HTTPError):
        return {
            "class": "HTTPError",
            "http_status": exc.code,
            "reason": str(exc.reason)[:200],
        }
    return {"class": type(exc).__name__,
            "reason": str(exc)[:200]}


def probe_eurusd(
    api_key: str | None,
    timeout: float = TIMEOUT_SECONDS,
    transport: Callable[..., object] | None = None,
) -> dict:
    """ONE ``time_series`` call for EUR/USD 1day 5000 bars (+ at most one
    retry, only on transport timeout).

    Returns an evidence dict (never carries the key):

    - ``status``: ``"OK"`` | ``"UNAVAILABLE"``;
    - ``key_present``: bool;
    - on OK additionally ``payload_bytes`` (the exact response bytes),
      ``sha256``, ``payload`` (parsed JSON) and provider ``meta``.
    """

    def _record(status: str, **extra) -> dict:
        rec = {
            "status": status,
            "endpoint": ENDPOINT,
            "params_recorded_without_apikey": dict(SAFE_PARAMS),
            "key_present": api_key is not None and bool(api_key),
            "attempts": [],
        }
        rec.update(extra)
        return rec

    if not api_key:
        # fail-closed BEFORE any network: no key -> no call, UNAVAILABLE.
        rec = _record("UNAVAILABLE")
        rec["reason"] = (
            f"{KEY_NAME} absent/empty in the loaded .env: EURUSD probe "
            "refused without a call (fail-closed; owner action named in "
            "the gate: place the existing-entitlement key in .env)")
        return rec

    opener = transport or urllib.request.urlopen
    query = urllib.parse.urlencode({
        "symbol": SYMBOL, "interval": INTERVAL, "outputsize": OUTPUTSIZE,
        "apikey": api_key})
    url = f"{ENDPOINT}?{query}"
    # NOTE: `url` embeds the key and is NEVER recorded anywhere (the
    # V1 probe_td.py urlencode convention, inherited).

    attempts: list[dict] = []
    last_error: dict | None = None
    for attempt_no in (1, 2):
        if attempt_no == 2:
            # Only a transport TIMEOUT on attempt 1 justifies the single
            # permitted retry (dispatch law: 1 call + 1 timeout retry).
            if not any(a.get("timeout") for a in attempts):
                break
        try:
            with opener(url, timeout=timeout) as resp:  # type: ignore[misc]
                raw = resp.read()
            attempts.append({
                "attempt": attempt_no,
                "outcome": "responded",
                "bytes": len(raw),
                "sha256": _sha256_bytes(raw),
                "timeout": False,
            })
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                err = _record(
                    "UNAVAILABLE",
                    attempts=attempts,
                    http_error={"class": "UnparseableResponse",
                                "reason": str(exc)[:200]})
                err["reason"] = ("response bytes are not JSON: EURUSD "
                                 "UNAVAILABLE (fail-closed)")
                return err
            rec = _record(
                "OK" if payload.get("status") == "ok" else "UNAVAILABLE",
                attempts=attempts, sha256=_sha256_bytes(raw))
            rec["payload_bytes"] = raw
            rec["payload"] = payload
            rec["provider_status"] = payload.get("status")
            if payload.get("status") != "ok":
                rec["http_error"] = {
                    "class": "ProviderStatus",
                    "code": payload.get("code"),
                    "reason": str(payload.get("message"))[:300],
                }
                rec["reason"] = (
                    "provider status != ok (quota/entitlement/key "
                    "refusal): EURUSD UNAVAILABLE (fail-closed; owner "
                    "action named in the gate)")
            return rec
        except Exception as exc:                     # noqa: BLE001
            is_timeout = isinstance(
                exc, (TimeoutError,)) or "timed out" in str(exc).lower()
            attempts.append({
                "attempt": attempt_no,
                "outcome": "error",
                "error": _describe_http_error(exc),
                "timeout": is_timeout,
            })
            last_error = attempts[-1]["error"]

    rec = _record("UNAVAILABLE", attempts=attempts)
    if last_error is not None:
        rec["http_error"] = last_error
    rec["reason"] = ("transport/HTTP error on the single permitted call "
                     "(+ single timeout retry): EURUSD UNAVAILABLE "
                     "(fail-closed; owner action named in the gate)")
    return rec


def pin_probe_bytes(raw: bytes, pin_dir: str = PIN_DIR_DEFAULT) -> dict:
    """Write the exact probe response bytes UNTRACKED to
    ``<pin_dir>/EURUSD.json``; return the pin evidence (path + sha256).

    The file is never committed; the committed manifest pins it by the
    returned sha256 (FOREX-NG1 spot pin law).
    """
    os.makedirs(pin_dir, exist_ok=True)
    path = os.path.join(pin_dir, PIN_FILE)
    with open(path, "wb") as fh:
        fh.write(raw)
    after = open(path, "rb").read()
    if _sha256_bytes(after) != _sha256_bytes(raw):
        raise ProbeError("pinned bytes drifted on write (fail-closed)")
    return {
        "file": PIN_FILE,
        "copy_path_absolute": os.path.abspath(path),
        "copy_sha256": _sha256_bytes(raw),
        "bytes": len(raw),
        "raw_bytes_policy": "UNTRACKED_NEVER_COMMITTED",
    }


def verify_pinned_bytes(pin_dir: str = PIN_DIR_DEFAULT,
                        pinned_sha256: str | None = None,
                        ) -> dict:
    """Verify-on-read the pinned EURUSD bytes (fail-closed)."""
    path = os.path.join(pin_dir, PIN_FILE)
    if not os.path.exists(path):
        raise ProbeError(f"pinned EURUSD bytes ABSENT: {path}")
    with open(path, "rb") as fh:
        raw = fh.read()
    sha = _sha256_bytes(raw)
    if pinned_sha256 is not None and sha != pinned_sha256:
        raise ProbeError(
            f"pinned EURUSD bytes DRIFTED: manifest {pinned_sha256} != "
            f"measured {sha} (fail-closed)")
    return {"copy_path_absolute": os.path.abspath(path),
            "copy_sha256": sha, "bytes": len(raw)}


def strict_payload_check(payload: Mapping) -> dict:
    """Cheap provider-contract pre-check before pinning: status ok,
    EUR/USD 1day meta, non-empty values (full strictness lives in the
    ng1 spot parser reused by the census: duplicates/monotonicity/
    finite-positive closes all fail-closed there)."""
    meta = payload.get("meta") or {}
    values = payload.get("values")
    problems = []
    if payload.get("status") != "ok":
        problems.append(f"status={payload.get('status')!r}")
    if meta.get("symbol") != SYMBOL:
        problems.append(f"meta.symbol={meta.get('symbol')!r}")
    if meta.get("interval") != INTERVAL:
        problems.append(f"meta.interval={meta.get('interval')!r}")
    if not isinstance(values, list) or not values:
        problems.append("values missing/empty")
    return {"ok": not problems, "problems": problems,
            "meta": meta, "bars": len(values) if isinstance(values, list)
            else None}
