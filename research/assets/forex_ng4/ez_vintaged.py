"""FOREX-NG4 P0b EZ HICP vintaged re-ingest + realtime panel (ALFRED).

Owner directive 2026-09-12 authorizes re-acquiring the lost EZ HICP
vintaged bytes (the V8 manifest pin 886f0afe... has no resolvable
bytes, measured by the p0a census) through the EXISTING FRED
entitlement.  Series: CP0000EZ19M086NEST (Euro area 19 HICP all-items
index, FRED/OECD MEI-derived) -- the series the V8 evidence pinned.

Ingest law (dispatch forex-ng4-p0b-ez-ingest):

- FRED_API_KEY loaded PROGRAMMATICALLY from the gitignored root .env;
  the value is NEVER echoed into any log, artifact, exception or URL
  record (only key_present booleans; td_probe key law, inherited).
- One ALFRED as-of snapshot per vintage date: the 1st of every month
  2017-12-01..2025-12-01 (96 in-window vintages + the 2017-12 warmup;
  strictly increasing grid, exactly 97 dates).
- Etiquette: <= 1 request / 1.2 s, exponential backoff (2/4/8 s) on
  retryable 4xx/5xx/transport errors, at most 3 retries per vintage;
  key-invalid / quota / deterministic-request errors STOP the ingest
  fail-closed (no retries -- retrying a deterministic refusal wastes
  the etiquette budget).
- Raw response bytes are pinned UNTRACKED under
  data_raw/forex_ng4_ez/vintages/; the COMMITTED manifest carries the
  per-file sha256 (ng1/ng4 spot pin law, inherited).

Measured ALFRED semantics (live probe 2026-09-12, 3 etiquette-spaced
calls): a single-day realtime query returns the binding values in
force on that day with every row's realtime window CLAMPED to the
query day (rs == re == VD).  The true archive (wide-window query)
carries one row per distinct value version with the true vintage day
(~17th-23rd of each month for this OECD MEI feed); a monthly 1st-of-
month snapshot grid resolves each ~monthly true vintage exactly once.

Panel law (this module's reconstruction, disclosed):

- Each snapshot is ONE sampling of every binding value in force on
  its vintage date.  Consecutive snapshots carrying the SAME value for
  an obs month are ONE version (a re-publication that does not change
  the value creates no archive row -- measured on the wide-window
  probe); a value change (including '.' -> value, the genuine first
  print) opens a NEW version dated at the FIRST snapshot that carries
  it, and the previous version's window closes the day before.
- The final still-open version carries realtime_end = 9999-12-31
  (ALFRED open-vintage convention, the V8 archive shape).
- Clock identity: version realtime days are the CLAMPED snapshot days
  (1st of month), not the true intra-month vintage days -- the true
  day is not recoverable from the mandated monthly grid.  A true
  version whose entire binding period falls strictly inside one
  inter-snapshot gap is invisible (at most one ~monthly true vintage
  lands per gap; measured cadence makes this rare).  Both identities
  are disclosed, never silently applied.
- Era law (ng2 machinery, frozen): realtime_era_start = min
  realtime_start over the panel rows = the first snapshot day, so obs
  months >= 2017-12 are first-print era and earlier months are
  backfill history.  The 2017-11 obs month (true first print
  ~2017-12-15, inside coverage) is era-excluded by this frozen law --
  one disclosed month of loss caused by the mandated warmup choice.

Census law: the reconstructed VintageRow panel feeds the ng2/ng3
machinery VIA IMPORT, unmodified (dedupe -> strict-monotonicity
vintages_by_month -> v1/v2 first-to-second-version events ->
S0-window usable filter -> first-print restriction + bulk
re-referencing exclusion).  Fail-closed canaries: a fabricated vintage
response (rows not clamped to the vintage date, count truncation,
non-monthly obs dates) refuses; pinned-byte drift refuses; a
fabricated obs month must look up found=False.

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
from datetime import date, timedelta
from typing import Callable, Mapping, Sequence

from research.assets.forex_ng1 import plane_adapter as pa

#: Root .env of the main checkout (owner-placed key; gitignored there).
ENV_PATH_DEFAULT = "/Users/hoangminhlong/my-quantitative/.env"

KEY_NAME = "FRED_API_KEY"

#: The ONLY endpoint this module may ever call.
ENDPOINT = "https://api.stlouisfed.org/fred/series/observations"
SERIES_ID = "CP0000EZ19M086NEST"
FILE_TYPE = "json"

#: Vintage grid: 1st of every month, 2017-12 (warmup) .. 2025-12.
VINTAGE_START = "2017-12-01"
VINTAGE_END = "2025-12-01"

#: Etiquette law (dispatch): <= 1 request / 1.2 s; backoff 2/4/8 s on
#: retryable errors; at most 3 retries per vintage.
REQUEST_MIN_INTERVAL_S = 1.2
BACKOFF_BASE_S = 2.0
MAX_RETRIES = 3
TIMEOUT_S = 30.0

#: ALFRED open-vintage marker (final still-in-force version).
OPEN_END = "9999-12-31"

#: Untracked pinned-bytes directory (data_raw/ is NOT gitignored in
#: this worktree: the raw files stay untracked; only the committed
#: manifest pins them by sha256).
PIN_DIR_DEFAULT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data_raw",
    "forex_ng4_ez", "vintages"))

MANIFEST_SCHEMA = "forex_ng4_run/p0b_ez_vintages_manifest@1"

#: Error-body classification substrings (lowercased).  The body text
#: itself is NEVER recorded -- only the classification label.
_FATAL_KEY_MARKERS = ("api_key", "api key", "apikey")
_FATAL_KEY_VERBS = ("invalid", "not valid", "not registered", "missing")
_FATAL_QUOTA_MARKERS = ("quota", "rate limit", "exceeded", "too many")


class EZIngestError(Exception):
    """Fail-closed base for ingest/panel errors (never carries the key)."""


class VintageResponseError(EZIngestError):
    """A vintage response violates the as-of snapshot contract."""


class PinnedBytesError(EZIngestError):
    """Pinned vintage bytes drifted or are absent (verify-on-read)."""


class VersionConflictError(EZIngestError):
    """Conflicting versions in the panel reconstruction (fail-closed)."""


# --------------------------------------------------------------------------- #
# key law (td_probe.load_api_key convention, inherited verbatim)
# --------------------------------------------------------------------------- #

def load_fred_key(env_path: str = ENV_PATH_DEFAULT) -> str | None:
    """Load ``FRED_API_KEY`` from a .env-style file.

    Returns the key, or None when absent/empty (fail-closed: the
    caller MUST treat None as ingest-impossible).  The value is never
    printed, logged, or embedded in any raised error.
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


# --------------------------------------------------------------------------- #
# vintage grid
# --------------------------------------------------------------------------- #

def vintage_dates(start: str = VINTAGE_START,
                  end: str = VINTAGE_END) -> list[str]:
    """The 1st of every month from ``start`` to ``end`` inclusive."""
    out: list[str] = []
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}-01")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def _day_before(iso_day: str) -> str:
    d = date.fromisoformat(iso_day) - timedelta(days=1)
    return d.isoformat()


# --------------------------------------------------------------------------- #
# single-vintage fetch (etiquette law)
# --------------------------------------------------------------------------- #

def _classify_http_failure(http_status: int | None,
                           body: bytes | None) -> str | None:
    """Classify a failed response from its status + JSON error body.

    Returns a classification label ONLY (the body text never enters
    any evidence): KEY_INVALID / QUOTA_EXCEEDED / REQUEST_FATAL for
    deterministic refusals that must STOP the ingest, or None when the
    failure is retryable (5xx, ambiguous 4xx, no body).
    """
    if http_status in (401, 403):
        return "KEY_INVALID"          # forbidden/unauthorized: entitlement
    text = ""
    if body:
        try:
            err = json.loads(body.decode("utf-8", "replace"))
            msg = err.get("error_message") or err.get("message") or ""
            if isinstance(msg, list):
                msg = " ".join(str(x) for x in msg)
            text = str(msg).lower()
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            text = ""
    if text:
        keyish = any(k in text for k in _FATAL_KEY_MARKERS) and any(
            v in text for v in _FATAL_KEY_VERBS)
        if keyish:
            return "KEY_INVALID"
        if any(q in text for q in _FATAL_QUOTA_MARKERS):
            return "QUOTA_EXCEEDED"
        if http_status is not None and 400 <= http_status < 500:
            return "REQUEST_FATAL"    # deterministic 4xx, not key/quota
    return None


def fetch_vintage(vintage_date: str, api_key: str | None,
                  transport: Callable[..., object] | None = None,
                  sleep_fn: Callable[[float], None] | None = None,
                  timeout: float = TIMEOUT_S) -> dict:
    """ONE ALFRED as-of snapshot fetch (+ backoff retries, max 3).

    Returns an evidence dict (never carries the key or the URL):

    - ``status``: "OK" | "FATAL_KEY_INVALID" | "FATAL_QUOTA_EXCEEDED"
      | "FATAL_REQUEST" | "FATAL_PROTOCOL" | "TRANSPORT_EXHAUSTED";
    - ``attempts``: per-attempt rows (outcome, http_status,
      classification, backoff_slept) -- no bodies, no URLs;
    - on OK additionally ``payload_bytes`` / ``payload`` /
      ``observations_count`` / ``count_declared``.
    """
    sleep = sleep_fn if sleep_fn is not None else time.sleep

    def _record(status: str, attempts: list[dict], **extra) -> dict:
        rec = {
            "status": status,
            "vintage_date": vintage_date,
            "endpoint": ENDPOINT,
            "series_id": SERIES_ID,
            "params_recorded_without_apikey": {
                "series_id": SERIES_ID, "file_type": FILE_TYPE,
                "realtime_start": vintage_date,
                "realtime_end": vintage_date},
            "key_present": api_key is not None and bool(api_key),
            "attempts": attempts,
        }
        rec.update(extra)
        return rec

    if not api_key:
        rec = _record("FATAL_NO_KEY", [])
        rec["reason"] = (f"{KEY_NAME} absent/empty in the loaded .env: "
                         "ingest refused without a call (fail-closed)")
        return rec

    opener = transport or urllib.request.urlopen
    query = urllib.parse.urlencode({
        "series_id": SERIES_ID, "api_key": api_key,
        "file_type": FILE_TYPE,
        "realtime_start": vintage_date, "realtime_end": vintage_date})
    url = f"{ENDPOINT}?{query}"
    # NOTE: `url` embeds the key and is NEVER recorded anywhere.

    attempts: list[dict] = []
    retries_left = MAX_RETRIES
    while True:
        try:
            with opener(url, timeout=timeout) as resp:   # type: ignore[misc]
                http_status = getattr(resp, "status", None) or \
                    getattr(resp, "code", None)
                raw = resp.read()
            payload = None
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
                    "response carries no observations (fail-closed)"))
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
            classification = _classify_http_failure(exc.code, body)
            attempts.append({"attempt": len(attempts) + 1,
                             "outcome": "http_error",
                             "http_status": exc.code,
                             "classification": classification})
            if classification is not None:
                return _record(f"FATAL_{classification}", attempts)
        except Exception as exc:                           # noqa: BLE001
            attempts.append({"attempt": len(attempts) + 1,
                             "outcome": "transport_error",
                             "error_class": type(exc).__name__})
            classification = None          # transport errors: retryable
        if retries_left <= 0:
            return _record("TRANSPORT_EXHAUSTED", attempts, reason=(
                f"still failing after {MAX_RETRIES} backoff retries "
                "(fail-closed)"))
        backoff = BACKOFF_BASE_S * (2 ** (MAX_RETRIES - retries_left))
        sleep(backoff)
        attempts[-1]["backoff_slept"] = backoff
        retries_left -= 1


# --------------------------------------------------------------------------- #
# response integrity (the fabricated-vintage canaries, pre-pin)
# --------------------------------------------------------------------------- #

def validate_vintage_response(vintage_date: str, payload: Mapping) -> list:
    """Validate one as-of snapshot response; return the parsed rows.

    Fail-closed canaries (a fabricated or corrupted vintage refuses):

    - the observation set parses under the ng1/d2-format FRED realtime
      parser (every row carries realtime_start/realtime_end/date/value);
    - count == observations returned (no silent truncation);
    - every row's realtime window is CLAMPED to the vintage date
      (rs == re == VD -- the measured ALFRED as-of identity);
    - obs dates are unique, strictly increasing and all first-of-month
      (a monthly feed identity).
    """
    observations = payload.get("observations")
    if not isinstance(observations, list) or not observations:
        raise VintageResponseError(
            f"vintage {vintage_date}: no observations (not an as-of "
            "snapshot; fail-closed)")
    count = payload.get("count")
    if count is not None and int(count) != len(observations):
        raise VintageResponseError(
            f"vintage {vintage_date}: count {count} != observations "
            f"{len(observations)} (truncated response; fail-closed)")
    rows = pa.parse_fred_vintaged(observations)   # ng1/d2-format parser
    prev = None
    for r in rows:
        if r.realtime_start != vintage_date or r.realtime_end != vintage_date:
            raise VintageResponseError(
                f"vintage {vintage_date}: row obs {r.obs_date} carries "
                f"realtime window [{r.realtime_start}, {r.realtime_end}] "
                "not clamped to the vintage date (fabricated or corrupted "
                "as-of response; fail-closed)")
        if r.obs_date[8:10] != "01":
            raise VintageResponseError(
                f"vintage {vintage_date}: obs date {r.obs_date} is not a "
                "first-of-month (monthly feed identity; fail-closed)")
        if prev is not None and r.obs_date <= prev:
            raise VintageResponseError(
                f"vintage {vintage_date}: obs dates not strictly "
                f"increasing ({prev} -> {r.obs_date}; fail-closed)")
        prev = r.obs_date
    return rows


# --------------------------------------------------------------------------- #
# the ingest (etiquette-paced loop -> untracked raw + committed manifest)
# --------------------------------------------------------------------------- #

def vintage_file_name(vintage_date: str) -> str:
    return f"{SERIES_ID}_{vintage_date}.json"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ingest_all(api_key: str | None,
               manifest_path: str,
               vintages_dir: str = PIN_DIR_DEFAULT,
               transport: Callable[..., object] | None = None,
               sleep_fn: Callable[[float], None] | None = None,
               monotonic_fn: Callable[[], float] | None = None,
               vintage_list: Sequence[str] | None = None,
               interval_s: float = REQUEST_MIN_INTERVAL_S) -> dict:
    """Fetch every planned vintage; pin raw bytes UNTRACKED; write the
    committed sha manifest.

    Etiquette: at least ``interval_s`` seconds between consecutive
    request issues (injected monotonic/sleep for tests).  Any FATAL
    status stops the loop immediately (fail-closed; the manifest
    records the partial state and status FAILED).  Returns the
    manifest evidence dict (also written to ``manifest_path``).
    """
    sleep = sleep_fn if sleep_fn is not None else time.sleep
    mono = monotonic_fn if monotonic_fn is not None else time.monotonic
    planned = list(vintage_list) if vintage_list is not None else \
        vintage_dates()
    if planned != sorted(planned) or len(set(planned)) != len(planned):
        raise EZIngestError("vintage grid must be strictly increasing "
                            "and unique (fail-closed)")
    os.makedirs(vintages_dir, exist_ok=True)

    manifest: dict = {
        "schema": MANIFEST_SCHEMA,
        "cycle_id": "FOREX-NG4",
        "task_id": "forex-ng4-p0b-ez-ingest",
        "series_id": SERIES_ID,
        "endpoint": ENDPOINT,
        "realtime_semantics": (
            "ALFRED as-of vintage: realtime_start=realtime_end=VD "
            "returns the binding values in force on VD with every row's "
            "realtime window clamped to the query day (measured live "
            "2026-09-12); the monthly 1st-of-month grid resolves each "
            "~monthly true vintage exactly once"),
        "planned_vintage_dates": planned,
        "vintage_count_planned": len(planned),
        "etiquette": {
            "min_interval_seconds": interval_s,
            "backoff_base_seconds": BACKOFF_BASE_S,
            "max_retries_per_vintage": MAX_RETRIES,
            "law": ("<= 1 request / 1.2 s + exponential backoff (2/4/8 s) "
                    "on retryable 4xx/5xx/transport errors, max 3 "
                    "retries; key-invalid/quota/deterministic-4xx STOP "
                    "the ingest fail-closed"),
        },
        "key_present": api_key is not None and bool(api_key),
        "raw_bytes_policy": (
            f"UNTRACKED_NEVER_COMMITTED ({vintages_dir}; the committed "
            "manifest pins every file by sha256, verify-on-read)"),
        "files": {},
        "failures": [],
        "status": "RUNNING",
    }

    def _write_manifest() -> None:
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=1, sort_keys=False)
            fh.write("\n")

    _write_manifest()
    last_request_at: float | None = None
    for vd in planned:
        now = mono()
        if last_request_at is not None:
            wait = interval_s - (now - last_request_at)
            if wait > 0:
                sleep(wait)
        last_request_at = mono()
        rec = fetch_vintage(vd, api_key, transport=transport,
                            sleep_fn=sleep)
        if rec["status"] != "OK":
            manifest["failures"].append({
                "vintage_date": vd,
                "status": rec["status"],
                "attempts": rec["attempts"],
                "reason": rec.get("reason"),
            })
            manifest["status"] = "FAILED"
            manifest["vintage_count_fetched"] = len(manifest["files"])
            _write_manifest()
            return manifest
        try:
            validate_vintage_response(vd, rec["payload"])
        except (VintageResponseError, pa.VintageStructureError) as exc:
            manifest["failures"].append({
                "vintage_date": vd, "status": "FATAL_PROTOCOL",
                "reason": str(exc)[:300]})
            manifest["status"] = "FAILED"
            manifest["vintage_count_fetched"] = len(manifest["files"])
            _write_manifest()
            return manifest
        path = os.path.join(vintages_dir, vintage_file_name(vd))
        with open(path, "wb") as fh:
            fh.write(rec["payload_bytes"])
        manifest["files"][vd] = {
            "file": vintage_file_name(vd),
            "sha256": _sha256_bytes(rec["payload_bytes"]),
            "bytes": len(rec["payload_bytes"]),
            "observations": rec["observations_count"],
            "count_declared": rec["count_declared"],
        }
    manifest["status"] = "COMPLETE"
    manifest["vintage_count_fetched"] = len(manifest["files"])
    _write_manifest()
    return manifest


def load_pinned_vintages(manifest_path: str,
                         vintages_dir: str = PIN_DIR_DEFAULT) -> list[tuple]:
    """Verify-on-read every pinned vintage file; return
    [(vintage_date, payload)] ascending (fail-closed on drift).

    Re-runs the full response-integrity canaries on every file so a
    tampered/fabricated vintage cannot enter the panel unnoticed.
    """
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise PinnedBytesError(
            f"manifest schema {manifest.get('schema')!r} != "
            f"{MANIFEST_SCHEMA!r} (fail-closed)")
    if manifest.get("status") != "COMPLETE":
        raise PinnedBytesError(
            f"manifest status {manifest.get('status')!r} != COMPLETE: "
            "the ingest did not complete; no panel may be built "
            "(fail-closed)")
    out: list[tuple[str, dict]] = []
    for vd in sorted(manifest.get("files", {})):
        entry = manifest["files"][vd]
        path = os.path.join(vintages_dir, entry["file"])
        if not os.path.exists(path):
            raise PinnedBytesError(f"pinned vintage ABSENT: {path}")
        with open(path, "rb") as fh:
            raw = fh.read()
        sha = _sha256_bytes(raw)
        if sha != entry["sha256"]:
            raise PinnedBytesError(
                f"pinned vintage DRIFTED: manifest {entry['sha256']} != "
                f"measured {sha} for {entry['file']} (fail-closed)")
        payload = json.loads(raw.decode("utf-8"))
        validate_vintage_response(vd, payload)   # integrity canaries
        out.append((vd, payload))
    if len(out) != manifest.get("vintage_count_planned"):
        raise PinnedBytesError(
            f"manifest files {len(out)} != planned "
            f"{manifest.get('vintage_count_planned')} (fail-closed)")
    return out


# --------------------------------------------------------------------------- #
# realtime panel reconstruction (snapshots -> archive-shaped VintageRows)
# --------------------------------------------------------------------------- #

def build_realtime_panel(vintage_payloads: Sequence[tuple]) -> dict:
    """Reconstruct the archive-shaped vintaged panel from snapshots.

    Input: [(vintage_date, payload)] ascending, each payload already
    integrity-validated (clamped as-of rows).  For every obs month the
    consecutive-snapshot value trajectory collapses into VERSIONS
    (equal consecutive values = one version); each version becomes one
    ng1 ``VintageRow`` with rs = the first snapshot carrying it, re =
    the day before the next version's first snapshot (9999-12-31 for
    the still-open final version).  Fails closed on version conflicts.
    """
    snapshots = [vd for vd, _ in vintage_payloads]
    if snapshots != sorted(snapshots) or len(set(snapshots)) != len(
            snapshots):
        raise EZIngestError("snapshots must be strictly increasing and "
                            "unique (fail-closed)")
    # sampled[vd] = {obs_date: value}; plus per-vd row validation
    sampled: dict[str, dict[str, str]] = {}
    for vd, payload in vintage_payloads:
        rows = validate_vintage_response(vd, payload)
        sampled[vd] = {r.obs_date: r.value for r in rows}
        if len(sampled[vd]) != len(rows):
            raise VintageResponseError(
                f"vintage {vd}: duplicate obs dates (fail-closed)")

    obs_months: set[str] = set()
    for vd in snapshots:
        obs_months.update(sampled[vd])
    panel: list = []
    version_count = 0
    value_change_count = 0
    for obs in sorted(obs_months):
        open_value: str | None = None
        open_start: str | None = None
        for vd in snapshots:
            value = sampled[vd].get(obs)
            if value is None:
                continue          # obs month not carried by this snapshot
            if open_value is None:
                open_value, open_start = value, vd
                version_count += 1
                continue
            if value != open_value:
                panel.append(pa.VintageRow(
                    obs_date=obs, realtime_start=open_start,
                    realtime_end=_day_before(vd), value=open_value))
                open_value, open_start = value, vd
                version_count += 1
                value_change_count += 1
        if open_value is not None:
            panel.append(pa.VintageRow(
                obs_date=obs, realtime_start=open_start,
                realtime_end=OPEN_END, value=open_value))
    # structural self-check: per obs month, strictly increasing rs and
    # valid windows (rs <= re) -- the realtime-window law on the panel
    by_obs: dict[str, list] = {}
    for r in panel:
        by_obs.setdefault(r.obs_date, []).append(r)
    for obs, versions in by_obs.items():
        starts = [v.realtime_start for v in versions]
        if starts != sorted(starts) or len(set(starts)) != len(starts):
            raise VersionConflictError(
                f"obs {obs}: reconstructed version realtime_starts not "
                f"strictly increasing ({starts}; fail-closed)")
        for v in versions:
            if v.realtime_start > v.realtime_end:
                raise VersionConflictError(
                    f"obs {obs}: version window [{v.realtime_start}, "
                    f"{v.realtime_end}] invalid (fail-closed)")
    return {
        "rows": panel,
        "rows_count": len(panel),
        "snapshots": len(snapshots),
        "first_snapshot": snapshots[0] if snapshots else None,
        "last_snapshot": snapshots[-1] if snapshots else None,
        "obs_months": len(obs_months),
        "versions": version_count,
        "value_changes": value_change_count,
        "reconstruction_law": (
            "monthly as-of snapshots collapsed to archive-shaped "
            "versions: equal consecutive sampled values = one version; "
            "a value change opens a version dated at the first snapshot "
            "carrying it (clamped clock: the true intra-month vintage "
            "day is not recoverable from the mandated monthly grid; a "
            "true version living entirely inside one inter-snapshot gap "
            "is invisible -- both identities disclosed); the final "
            "open version carries realtime_end 9999-12-31 (ALFRED "
            "convention)"),
    }


# --------------------------------------------------------------------------- #
# EZ-vs-US differential join (A5 floor basis)
# --------------------------------------------------------------------------- #

def ez_us_differential_months(
        ez_events: Sequence, us_events: Sequence) -> dict:
    """Months carrying BOTH an EZ restricted event and a US restricted
    event (obs-month-key join, ng2 join law; US leg from the pinned
    ng3 restricted stream)."""
    ez_months = sorted({e.month_key for e in ez_events})
    us_months = sorted({e.month_key for e in us_events})
    both = sorted(set(ez_months) & set(us_months))
    return {
        "ez_restricted_months": ez_months,
        "us_restricted_months": us_months,
        "differential_months": both,
        "total": len(both),
        "join_key_law": ("obs month key (ng2): a differential month "
                         "requires an EZ restricted event AND a US "
                         "restricted event in the same obs month"),
    }
