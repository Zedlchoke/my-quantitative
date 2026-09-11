"""FOREX-NG4 P0c EZ HICP wide-window pull (A7-F1 remediation).

Audit A7 (research/control/forex_ng4_run/audits/a7_terminal_ng4.json,
finding NG4-A7-F1 + required_owner_action) established that the p0b A4
floor FAIL (17/30) was an artifact of the mandated as-of snapshot ingest
shape (every returned row's realtime window CLAMPED to the query day),
not a property of the feed: on the plan's frozen V8 basis (true vintage
windows, rows = binding periods intersecting the window) the SAME frozen
ng2 era law yields era_start <= 2015-02-27 (V8 committed evidence
p0_earliest_vintage_v8.json) and the pre-2018 cohort re-enters the
first-print era.  The owner prescription, implemented here VERBATIM:

- ONE wide-window ALFRED query shape (fewer calls than the 97-snapshot
  p0b ingest):
  GET /fred/series/observations?series_id=CP0000EZ19M086NEST
      &file_type=json&realtime_start=2015-01-01&realtime_end=9999-12-31
  (+ limit/offset paging ONLY if the response is larger than one page --
  still the same one wide query shape; etiquette backoff identical).
- The raw response is pinned UNTRACKED (data_raw/forex_ng4_ez/); the
  COMMITTED manifest carries the sha256 of every page AND of the merged
  document (verify-on-read).
- The response feeds rs.build_restricted_stream("EZ", ...) UNMODIFIED
  via a PURE input adapter (payload -> ng1 VintageRows); the ng2/ng3 era
  law, bulk rule, floors and S0 window logic are NEVER touched here.

Key law (inherited verbatim from ez_vintaged): FRED_API_KEY loaded
programmatically from the gitignored root .env; NEVER echoed into any
log, artifact, exception or URL record (only key_present booleans).

Etiquette law (identical constants, imported from ez_vintaged):
<= 1 request / 1.2 s, exponential backoff 2/4/8 s on retryable
4xx/5xx/transport errors, at most 3 retries per page; key-invalid /
quota / deterministic-request errors STOP fail-closed.

NO PnL, NO outcome, NO scoring anywhere in this module (P0 census law).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Mapping, Sequence

from research.assets.forex_ng1 import plane_adapter as pa
from research.assets.forex_ng4 import ez_vintaged as ezv

#: The wide-window query shape (A7-F1 prescription: realtime_start must
#: be <= the V8 earliest-vintage upper bound 2015-02-27 so the pull
#: captures the archive from its true beginning; realtime_end open).
WIDE_REALTIME_START = "2015-01-01"
WIDE_REALTIME_END = "9999-12-31"

#: Paging (same one wide query shape; only the offset moves).
PAGE_LIMIT = 1000
MAX_PAGES = 50          # structural safety bound (fail-closed)

#: Untracked pinned-bytes locations (committed manifest pins by sha256).
PIN_DIR_DEFAULT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data_raw",
    "forex_ng4_ez"))
WIDE_FILE_NAME = "wide_window.json"
PAGES_DIR_NAME = "wide_window_pages"

MANIFEST_SCHEMA = "forex_ng4_run/p0c_wide_window_manifest@1"

#: ALFRED open-vintage marker (final still-in-force version).
OPEN_END = ezv.OPEN_END          # "9999-12-31"


class WidePullError(Exception):
    """Fail-closed base for wide-pull errors (never carries the key)."""


class WideResponseError(WidePullError):
    """A wide-window response violates the true-archive contract."""


class PinnedWideBytesError(WidePullError):
    """Pinned wide bytes drifted or are absent (verify-on-read)."""


# --------------------------------------------------------------------------- #
# one wide-window fetch (etiquette law, paged)
# --------------------------------------------------------------------------- #

def _page_url(api_key: str, offset: int, limit: int) -> str:
    query = urllib.parse.urlencode({
        "series_id": ezv.SERIES_ID, "api_key": api_key,
        "file_type": ezv.FILE_TYPE,
        "realtime_start": WIDE_REALTIME_START,
        "realtime_end": WIDE_REALTIME_END,
        "limit": limit, "offset": offset})
    return f"{ezv.ENDPOINT}?{query}"
    # NOTE: the URL embeds the key and is NEVER recorded anywhere.


def fetch_page(offset: int, api_key: str | None,
               transport: Callable[..., object] | None = None,
               sleep_fn: Callable[[float], None] | None = None,
               timeout: float = ezv.TIMEOUT_S,
               limit: int = PAGE_LIMIT) -> dict:
    """ONE wide-window page fetch (+ backoff retries, max 3).

    Mirrors ezv.fetch_vintage's evidence law exactly (attempts carry
    outcome/http_status/classification only -- no bodies, no URLs, no
    key).  Returns an evidence dict; on OK additionally payload_bytes /
    payload / observations_count / count_declared.
    """
    sleep = sleep_fn if sleep_fn is not None else time.sleep

    def _record(status: str, attempts: list[dict], **extra) -> dict:
        rec = {
            "status": status,
            "offset": offset,
            "endpoint": ezv.ENDPOINT,
            "series_id": ezv.SERIES_ID,
            "params_recorded_without_apikey": {
                "series_id": ezv.SERIES_ID, "file_type": ezv.FILE_TYPE,
                "realtime_start": WIDE_REALTIME_START,
                "realtime_end": WIDE_REALTIME_END,
                "limit": limit, "offset": offset},
            "key_present": api_key is not None and bool(api_key),
            "attempts": attempts,
        }
        rec.update(extra)
        return rec

    if not api_key:
        rec = _record("FATAL_NO_KEY", [])
        rec["reason"] = (f"{ezv.KEY_NAME} absent/empty in the loaded .env: "
                         "pull refused without a call (fail-closed)")
        return rec

    opener = transport or urllib.request.urlopen
    url = _page_url(api_key, offset, limit)
    attempts: list[dict] = []
    retries_left = ezv.MAX_RETRIES
    while True:
        try:
            with opener(url, timeout=timeout) as resp:   # type: ignore[misc]
                http_status = getattr(resp, "status", None) or \
                    getattr(resp, "code", None)
                raw = resp.read()
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                attempts.append({"attempt": len(attempts) + 1,
                                 "outcome": "unparseable",
                                 "http_status": http_status})
                return _record("FATAL_PROTOCOL", attempts, reason=(
                    "200-class response is not JSON (fail-closed)"))
            observations = payload.get("observations")
            if not isinstance(observations, list) or not observations:
                attempts.append({"attempt": len(attempts) + 1,
                                 "outcome": "protocol_violation",
                                 "http_status": http_status,
                                 "classification": "EMPTY_OBSERVATIONS"})
                return _record("FATAL_PROTOCOL", attempts, reason=(
                    "page carries no observations (fail-closed)"))
            attempts.append({"attempt": len(attempts) + 1,
                             "outcome": "responded",
                             "http_status": http_status})
            return _record("OK", attempts,
                           payload_bytes=raw, payload=payload,
                           observations_count=len(observations),
                           count_declared=payload.get("count"))
        except urllib.error.HTTPError as exc:
            body = None
            try:
                body = exc.read()
            except Exception:                              # noqa: BLE001
                body = None
            classification = ezv._classify_http_failure(exc.code, body)
            attempts.append({"attempt": len(attempts) + 1,
                             "outcome": "http_error",
                             "http_status": exc.code,
                             "classification": classification})
            if classification is not None:
                return _record(f"FATAL_{classification}", attempts)
        except Exception:                                  # noqa: BLE001
            attempts.append({"attempt": len(attempts) + 1,
                             "outcome": "transport_error",
                             "error_class": "transport"})
            classification = None          # transport errors: retryable
        if retries_left <= 0:
            return _record("TRANSPORT_EXHAUSTED", attempts, reason=(
                f"still failing after {ezv.MAX_RETRIES} backoff retries "
                "(fail-closed)"))
        backoff = ezv.BACKOFF_BASE_S * (2 ** (ezv.MAX_RETRIES - retries_left))
        sleep(backoff)
        attempts[-1]["backoff_slept"] = backoff
        retries_left -= 1


def fetch_wide_window(api_key: str | None,
                      transport: Callable[..., object] | None = None,
                      sleep_fn: Callable[[float], None] | None = None,
                      monotonic_fn: Callable[[], float] | None = None,
                      timeout: float = ezv.TIMEOUT_S,
                      limit: int = PAGE_LIMIT,
                      max_pages: int = MAX_PAGES) -> dict:
    """The ONE wide-window pull: paged until the archive is exhausted.

    Etiquette: at least REQUEST_MIN_INTERVAL_S between consecutive page
    request issues; per-page backoff law inside fetch_page.  Any FATAL
    status stops immediately (fail-closed).  Returns an evidence dict:
    status, pages (per-page attempt evidence), page_payloads (raw bytes,
    in-memory only -- pinned by pin_wide_window), rows_total,
    count_declared, key_present.  Never carries the key or any URL.
    """
    sleep = sleep_fn if sleep_fn is not None else time.sleep
    mono = monotonic_fn if monotonic_fn is not None else time.monotonic
    ev: dict = {
        "endpoint": ezv.ENDPOINT,
        "series_id": ezv.SERIES_ID,
        "query_shape": {
            "realtime_start": WIDE_REALTIME_START,
            "realtime_end": WIDE_REALTIME_END,
            "file_type": ezv.FILE_TYPE,
            "limit": limit,
            "law": ("ONE wide-window ALFRED query (A7-F1 prescription, "
                    "realtime_start <= the V8 earliest-vintage bound "
                    "2015-02-27 .. realtime_end 9999-12-31) + limit/"
                    "offset paging of the SAME shape only while a full "
                    "page returns"),
        },
        "etiquette": {
            "min_interval_seconds": ezv.REQUEST_MIN_INTERVAL_S,
            "backoff_base_seconds": ezv.BACKOFF_BASE_S,
            "max_retries_per_page": ezv.MAX_RETRIES,
            "law": ("<= 1 request / 1.2 s + exponential backoff (2/4/8 s) "
                    "on retryable 4xx/5xx/transport errors, max 3 "
                    "retries per page; key-invalid/quota/deterministic-"
                    "4xx STOP fail-closed"),
        },
        "key_present": api_key is not None and bool(api_key),
        "pages": [],
        "status": "RUNNING",
    }
    page_payloads: list[bytes] = []
    rows_total = 0
    count_declared: int | None = None
    last_request_at: float | None = None
    offset = 0
    while True:
        if len(page_payloads) >= max_pages:
            ev["status"] = "FATAL_PROTOCOL"
            ev["reason"] = (f"archive exceeded the structural safety "
                            f"bound of {max_pages} pages (fail-closed)")
            break
        now = mono()
        if last_request_at is not None:
            wait = ezv.REQUEST_MIN_INTERVAL_S - (now - last_request_at)
            if wait > 0:
                sleep(wait)
        last_request_at = mono()
        rec = fetch_page(offset, api_key, transport=transport,
                         sleep_fn=sleep, timeout=timeout, limit=limit)
        if rec["status"] != "OK":
            ev["pages"].append({"offset": offset, "status": rec["status"],
                                "attempts": rec["attempts"],
                                "reason": rec.get("reason")})
            ev["status"] = rec["status"]
            ev["reason"] = rec.get("reason")
            break
        ev["pages"].append({"offset": offset, "status": "OK",
                            "attempts": rec["attempts"],
                            "observations": rec["observations_count"],
                            "count_declared": rec["count_declared"]})
        if count_declared is None:
            count_declared = rec["count_declared"]
        elif rec["count_declared"] is not None and \
                rec["count_declared"] != count_declared:
            ev["status"] = "FATAL_PROTOCOL"
            ev["reason"] = ("count changed between pages "
                            f"({count_declared} -> {rec['count_declared']}; "
                            "fail-closed)")
            break
        page_payloads.append(rec["payload_bytes"])
        rows_total += rec["observations_count"]
        offset += rec["observations_count"]
        if rec["observations_count"] < limit:
            break                            # archive exhausted
        if count_declared is not None and rows_total >= int(count_declared):
            break
    if ev["status"] == "RUNNING":
        ev["status"] = "COMPLETE"
    ev["rows_total"] = rows_total if page_payloads else 0
    ev["count_declared"] = count_declared
    ev["page_payloads"] = page_payloads      # in-memory; never in evidence
    return ev


# --------------------------------------------------------------------------- #
# pure page merge (the merged wide-window document)
# --------------------------------------------------------------------------- #

def merge_wide_pages(page_payloads: Sequence[Mapping],
                     limit: int = PAGE_LIMIT) -> dict:
    """PURE: merge validated wide-window pages into ONE document.

    Fail-closed consistency law: every page carries a non-empty
    observations list; the declared count is IDENTICAL across pages (a
    changing count means the archive moved mid-pull); page offsets are
    consecutive multiples of the page length; the merged total equals
    the declared count (no truncation, no silent gap).  Deterministic:
    same pages in, byte-identical document out.
    """
    if not page_payloads:
        raise WideResponseError("no pages to merge (fail-closed)")
    observations: list[Mapping] = []
    counts: set = set()
    expected_offset = 0
    for i, page in enumerate(page_payloads):
        obs = page.get("observations")
        if not isinstance(obs, list) or not obs:
            raise WideResponseError(
                f"page {i}: no observations (fail-closed)")
        if page.get("count") is not None:
            counts.add(int(page["count"]))
        declared_offset = page.get("offset")
        if declared_offset is not None and int(declared_offset) != \
                expected_offset:
            raise WideResponseError(
                f"page {i}: declared offset {declared_offset} != expected "
                f"{expected_offset} (paging gap or overlap; fail-closed)")
        if len(obs) > limit:
            raise WideResponseError(
                f"page {i}: {len(obs)} rows > page limit {limit} "
                "(fail-closed)")
        observations.extend(obs)
        expected_offset += len(obs)
    if len(counts) > 1:
        raise WideResponseError(
            f"declared count changed across pages {sorted(counts)} "
            "(archive moved mid-pull; fail-closed)")
    total = len(observations)
    if counts and next(iter(counts)) != total:
        raise WideResponseError(
            f"declared count {next(iter(counts))} != merged rows {total} "
            "(truncated or missing pages; fail-closed)")
    first = page_payloads[0]
    return {
        "realtime_start": first.get("realtime_start"),
        "realtime_end": first.get("realtime_end"),
        "count": total,
        "limit": limit,
        "offset": 0,
        "observations": observations,
    }


def serialize_merged(payload: Mapping) -> bytes:
    """PURE: deterministic serialization of the merged document."""
    return (json.dumps(payload, indent=1, sort_keys=True) + "\n").encode(
        "utf-8")


# --------------------------------------------------------------------------- #
# the PURE input adapter (wide response -> ng1 VintageRows)
# --------------------------------------------------------------------------- #

def validate_wide_response(payload: Mapping) -> list:
    """PURE adapter: wide-window payload -> ng1 ``VintageRow`` list.

    The as-of snapshot responses (p0b) carry rows CLAMPED to the query
    day; the wide-window response carries TRUE vintage windows (one row
    per distinct value version, the V8 archive shape).  Fail-closed
    canaries:

    - observations present and count == observations (no truncation);
    - every row parses under the ng1/d2-format FRED realtime parser
      (realtime_start/realtime_end/date/value on every row -- a
      current-vintage table refuses structurally);
    - NOT an as-of snapshot: a response whose rows all share one single
      (realtime_start, realtime_end) day is the CLAMPED shape, i.e. the
      wrong query shape for this pull (refuses);
    - every obs date is a first-of-month (the monthly feed identity,
      same law as the p0b canary);
    - every realtime window is well-formed (realtime_start <=
      realtime_end).

    Returns the parsed ``VintageRow`` rows; the caller feeds them
    UNMODIFIED into ng3 ``build_restricted_stream``.
    """
    observations = payload.get("observations")
    if not isinstance(observations, list) or not observations:
        raise WideResponseError("no observations (fail-closed)")
    count = payload.get("count")
    if count is not None and int(count) != len(observations):
        raise WideResponseError(
            f"count {count} != observations {len(observations)} "
            "(truncated response; fail-closed)")
    rows = pa.parse_fred_vintaged(observations)   # ng1 parser, strict
    starts = {r.realtime_start for r in rows}
    ends = {r.realtime_end for r in rows}
    if len(starts) == 1 and len(ends) == 1:
        raise WideResponseError(
            "every row's realtime window is clamped to one single day "
            f"({sorted(starts)[0]}): this is the AS-OF snapshot shape, "
            "not the wide-window true archive (wrong query shape; "
            "fail-closed)")
    for r in rows:
        if r.obs_date[8:10] != "01":
            raise WideResponseError(
                f"obs date {r.obs_date} is not a first-of-month (monthly "
                "feed identity; fail-closed)")
        if r.realtime_start > r.realtime_end:
            raise WideResponseError(
                f"row obs {r.obs_date} carries an invalid realtime window "
                f"[{r.realtime_start}, {r.realtime_end}] (fail-closed)")
    return rows


def open_version_stat(rows: Sequence) -> dict:
    """PURE: ALFRED open-vintage convention stats (recorded, not gating)."""
    open_rows = sum(1 for r in rows if r.realtime_end == OPEN_END)
    return {
        "open_version_rows": open_rows,
        "law": ("ALFRED convention: each obs month's final still-in-force "
                "version carries realtime_end 9999-12-31 (recorded as a "
                "measured identity, never a gate)"),
    }


# --------------------------------------------------------------------------- #
# pinning + verify-on-read (untracked bytes + committed sha manifest)
# --------------------------------------------------------------------------- #

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin_wide_window(page_payloads: Sequence[bytes],
                    manifest_path: str,
                    pin_dir: str = PIN_DIR_DEFAULT,
                    fetch_evidence: Mapping | None = None) -> dict:
    """Pin every raw page + the merged document UNTRACKED; write the
    committed sha256 manifest.  Returns the manifest evidence dict."""
    parsed = [json.loads(raw.decode("utf-8")) for raw in page_payloads]
    merged = merge_wide_pages(parsed)
    merged_bytes = serialize_merged(merged)
    rows = validate_wide_response(merged)

    pages_dir = os.path.join(pin_dir, PAGES_DIR_NAME)
    os.makedirs(pages_dir, exist_ok=True)
    pages_block = []
    for i, raw in enumerate(page_payloads):
        name = f"page_{i:03d}.json"
        with open(os.path.join(pages_dir, name), "wb") as fh:
            fh.write(raw)
        pages_block.append({
            "file": f"{PAGES_DIR_NAME}/{name}",
            "sha256": _sha256_bytes(raw),
            "bytes": len(raw),
            "observations": len(parsed[i]["observations"]),
            "offset": parsed[i].get("offset"),
        })
    wide_path = os.path.join(pin_dir, WIDE_FILE_NAME)
    with open(wide_path, "wb") as fh:
        fh.write(merged_bytes)

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "cycle_id": "FOREX-NG4",
        "task_id": "forex-ng4-p0c-wide-window",
        "series_id": ezv.SERIES_ID,
        "endpoint": ezv.ENDPOINT,
        "query_shape": {
            "realtime_start": WIDE_REALTIME_START,
            "realtime_end": WIDE_REALTIME_END,
            "file_type": ezv.FILE_TYPE,
            "limit": PAGE_LIMIT,
            "law": ("A7-F1 prescription (a7_terminal_ng4.json "
                    "required_owner_action): ONE wide-window ALFRED pull "
                    "with realtime_start <= the committed V8 "
                    "earliest-vintage bound 2015-02-27 and realtime_end "
                    "9999-12-31, same existing entitlement, limit/offset "
                    "paging of the SAME shape only while a full page "
                    "returns"),
        },
        "etiquette": {
            "min_interval_seconds": ezv.REQUEST_MIN_INTERVAL_S,
            "backoff_base_seconds": ezv.BACKOFF_BASE_S,
            "max_retries_per_page": ezv.MAX_RETRIES,
            "law": ("<= 1 request / 1.2 s + exponential backoff (2/4/8 s) "
                    "on retryable errors, max 3 retries per page; key-"
                    "invalid/quota/deterministic-4xx STOP fail-closed"),
        },
        "key_present": (fetch_evidence or {}).get(
            "key_present", True),
        "merged_document_law": (
            "the pinned wide_window.json is the deterministic merge of the "
            "pinned raw pages (merge_wide_pages + serialize_merged); "
            "verify-on-read re-merges the pinned pages and requires "
            "byte-equality with the pinned merged document"),
        "raw_bytes_policy": (
            f"UNTRACKED_NEVER_COMMITTED ({pin_dir}: {WIDE_FILE_NAME} + "
            f"{PAGES_DIR_NAME}/; the committed manifest pins every file "
            "by sha256, verify-on-read)"),
        "pages": pages_block,
        "merged": {
            "file": WIDE_FILE_NAME,
            "sha256": _sha256_bytes(merged_bytes),
            "bytes": len(merged_bytes),
            "observations": len(rows),
            "count_declared": merged.get("count"),
        },
        "status": "COMPLETE",
    }
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=False)
        fh.write("\n")
    return manifest


def load_pinned_wide(manifest_path: str,
                     pin_dir: str = PIN_DIR_DEFAULT) -> tuple[dict, list]:
    """Verify-on-read the pinned wide-window bytes; return
    (merged_payload, rows) fail-closed on any drift.

    Re-hashes every pinned page AND the merged document against the
    committed manifest, re-merges the pinned pages and requires
    byte-equality with the pinned merged document (a doctored merge
    cannot survive), then re-runs the full response canaries
    (validate_wide_response) before any row is handed to the machinery.
    """
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise PinnedWideBytesError(
            f"manifest schema {manifest.get('schema')!r} != "
            f"{MANIFEST_SCHEMA!r} (fail-closed)")
    if manifest.get("status") != "COMPLETE":
        raise PinnedWideBytesError(
            f"manifest status {manifest.get('status')!r} != COMPLETE: no "
            "census may be built (fail-closed)")
    page_payloads: list[dict] = []
    for i, entry in enumerate(manifest.get("pages", [])):
        path = os.path.join(pin_dir, entry["file"])
        if not os.path.exists(path):
            raise PinnedWideBytesError(f"pinned page ABSENT: {path}")
        with open(path, "rb") as fh:
            raw = fh.read()
        if _sha256_bytes(raw) != entry["sha256"]:
            raise PinnedWideBytesError(
                f"pinned page DRIFTED: {entry['file']} (fail-closed)")
        page_payloads.append(json.loads(raw.decode("utf-8")))
    if not page_payloads:
        raise PinnedWideBytesError("manifest pins no pages (fail-closed)")
    merged_entry = manifest.get("merged", {})
    wide_path = os.path.join(pin_dir, merged_entry.get("file", ""))
    if not os.path.exists(wide_path):
        raise PinnedWideBytesError(f"pinned wide document ABSENT: {wide_path}")
    with open(wide_path, "rb") as fh:
        merged_bytes = fh.read()
    if _sha256_bytes(merged_bytes) != merged_entry.get("sha256"):
        raise PinnedWideBytesError(
            "pinned wide document DRIFTED: "
            f"{merged_entry.get('file')} (fail-closed)")
    remerged = serialize_merged(merge_wide_pages(page_payloads))
    if remerged != merged_bytes:
        raise PinnedWideBytesError(
            "pinned merged document is NOT the merge of the pinned pages "
            "(fail-closed)")
    payload = json.loads(merged_bytes.decode("utf-8"))
    rows = validate_wide_response(payload)
    if len(rows) != merged_entry.get("observations"):
        raise PinnedWideBytesError(
            f"manifest observations {merged_entry.get('observations')} != "
            f"validated rows {len(rows)} (fail-closed)")
    return payload, rows
