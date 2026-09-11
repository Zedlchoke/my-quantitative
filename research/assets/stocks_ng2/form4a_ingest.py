"""STOCKS-NG2 P0(a): targeted EDGAR Form 4/A re-ingest (keyless).

The ng1 census proved the pinned V13 substrate enumerated documentType
'4' only (3,062 '4/A' entries listed in the pinned submissions metadata,
0 accession dirs in the form4_xml tree).  This module lawfully RE-CREATES
amendment coverage: for every '4/A' accession of the pinned cohort it
fetches the accession dir (index.json + primary doc) from EDGAR, keyless,
under the declared research UA with <= 2 req/s etiquette and backoff.

Etiquette law (dispatch packet + plan section 3):
  * UA ``Research my-quantitative@example.com`` (V13-proven);
  * request START times are globally spaced >= MIN_INTERVAL seconds
    (hard ceiling 2 req/s across ALL workers/threads);
  * 403/429/5xx -> exponential-ish backoff (10/30/60s), max 4 attempts
    per URL, then the URL is recorded FAILED (never hammered);
  * >= ABORT_AFTER_CONSECUTIVE_FAILURES consecutive failed accessions
    aborts the session -> caller reports BLOCKED_PARTIAL honestly;
  * 404 is a definitive answer (no retry) -- canaries rely on this.

Nothing here writes to the inherited V13 pin (read-only) or S1 data.
Fetched bytes land under ``data_raw/form4a/`` (untracked); the sha256
manifest for pinning is written by :func:`build_manifest` to a path the
caller owns (committed control dir).

Transport is injectable (``transport=callable(url) -> (status, bytes)``)
so tests exercise etiquette/classification without any network.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping

#: Declared research UA (V13-proven; EDGAR fair-use).
USER_AGENT = "Research my-quantitative@example.com"

#: >= 0.55s between request START times -> hard ceiling < 2 req/s.
MIN_INTERVAL_SECONDS = 0.55

#: Backoff schedule for 403/429/5xx (seconds).
BACKOFF_SCHEDULE = (10.0, 30.0, 60.0)

#: Total attempts per URL before recording FAILED.
MAX_ATTEMPTS = 1 + len(BACKOFF_SCHEDULE)

#: Consecutive failed accessions that abort a fetch session.
ABORT_AFTER_CONSECUTIVE_FAILURES = 10

EDGAR_ARCHIVE_BASE = "https://www.sec.gov/Archives/edgar/data"
EDGAR_SUBMISSIONS_BASE = "https://data.sec.gov/submissions"

_RETRY_STATUSES = {403, 429, 500, 502, 503, 504}

Transport = Callable[[str], "tuple[int, bytes]"]


class RateLimiter:
    """Global start-time spacing: every acquire() blocks until
    MIN_INTERVAL_SECONDS has passed since the previous release, across
    all threads sharing the limiter (etiquette ceiling <= 2 req/s)."""

    def __init__(self, min_interval: float = MIN_INTERVAL_SECONDS,
                 clock: Callable[[], float] = time.monotonic,
                 sleeper: Callable[[float], None] = time.sleep) -> None:
        self.min_interval = float(min_interval)
        self._clock = clock
        self._sleep = sleeper
        self._lock = threading.Lock()
        self._last_start: float | None = None

    def acquire(self) -> float:
        with self._lock:
            now = self._clock()
            wait = 0.0
            if self._last_start is not None:
                elapsed = now - self._last_start
                if elapsed < self.min_interval:
                    wait = self.min_interval - elapsed
            if wait > 0:
                self._sleep(wait)
                now = self._clock()
            self._last_start = now
            return now


#: Process-wide limiter shared by every network call in this module
#: (a single physical etiquette budget, never per-worker).
_GLOBAL_LIMITER = RateLimiter()


def real_transport(url: str, timeout: float = 45.0) -> tuple[int, bytes]:
    """The one place raw HTTP happens: UA header, global rate limit,
    backoff on 403/429/5xx AND on transport-level errors (timeouts,
    resets -- raw TimeoutError/OSError escapes urlopen and must not
    crash the session).  Returns (http_status, body_bytes); status 0
    means transport exhausted its attempts (caller records FAILED)."""
    last_error = ""
    for attempt in range(MAX_ATTEMPTS):
        _GLOBAL_LIMITER.acquire()
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return int(resp.status), resp.read()
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            body = b""
            try:
                body = exc.read()
            except Exception:  # noqa: BLE001 - body is best-effort only
                body = b""
            if status in _RETRY_STATUSES and attempt < MAX_ATTEMPTS - 1:
                time.sleep(BACKOFF_SCHEDULE[attempt])
                last_error = f"HTTP {status}"
                continue
            return status, body
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # transport-level failure: backoff, never hammer; after the
            # final attempt report status 0 (no HTTP answer)
            last_error = (f"HTTP {exc.code}"
                          if isinstance(exc, urllib.error.HTTPError)
                          else f"{type(exc).__name__}: {exc}")
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(BACKOFF_SCHEDULE[attempt])
                continue
            return 0, b""
    raise RuntimeError(f"unreachable retry loop exit ({last_error})")


# --------------------------------------------------------------------- #
# target enumeration (pinned submissions metadata, cohort CIKs only)
# --------------------------------------------------------------------- #

def build_targets(submissions_dir: str) -> list[dict]:
    """Deterministic target list: every '4/A' entry in the PINNED
    submissions_alive metadata (the cohort of 410 pinned CIKs), sorted
    by (cik, accession).  Reuses the ng1 absence-crosscheck logic shape
    so the enumeration is checkable against the recorded census (3,062
    entries)."""
    rows: list[dict] = []
    for fname in sorted(os.listdir(submissions_dir)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(submissions_dir, fname)
        with open(path, "rb") as fh:
            d = json.loads(fh.read())
        recent = d.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accs = recent.get("accessionNumber", [])
        dates = recent.get("filingDate", [])
        pdocs = recent.get("primaryDocument", [])
        cik = fname.replace(".json", "")          # e.g. CIK0000001800
        cik_int = int(cik.replace("CIK", ""))
        for i, form in enumerate(forms):
            if form != "4/A":
                continue
            acc = (accs[i] or "").strip()
            if not acc:
                continue
            rows.append({
                "cik": cik,
                "cik_int": cik_int,
                "accession": acc,
                "accession_nodash": acc.replace("-", ""),
                "filing_date": dates[i] if i < len(dates) else None,
                "primary_document": (pdocs[i] if i < len(pdocs) else None),
                "form": "4/A",
            })
    rows.sort(key=lambda r: (r["cik"], r["accession_nodash"]))
    return rows


# --------------------------------------------------------------------- #
# URL construction + primary-doc selection
# --------------------------------------------------------------------- #

def accession_index_url(cik_int: int, accession_nodash: str) -> str:
    return f"{EDGAR_ARCHIVE_BASE}/{cik_int}/{accession_nodash}/index.json"


def accession_file_url(cik_int: int, accession_nodash: str,
                       filename: str) -> str:
    return f"{EDGAR_ARCHIVE_BASE}/{cik_int}/{accession_nodash}/{filename}"


def choose_primary_doc(index_body: bytes,
                       metadata_pdoc: str | None) -> dict:
    """Pick the primary Form 4/A document filename from the fetched
    accession index.json listing.

    Preference order (recorded in ``source``):
      metadata   - the pinned submissions primaryDocument appears in
                   the dir listing (authoritative);
      index_xml  - no metadata match: first .xml item in the listing
                   that is not an index/header artefact (covers the two
                   .txt-primaryDocument vintage rows where EDGAR still
                   stores the ownership XML in the dir);
      none       - nothing usable (counted fetched_non_xml upstream).
    """
    try:
        idx = json.loads(index_body)
        items = idx.get("directory", {}).get("item", [])
    except ValueError:
        return {"filename": None, "source": "unparseable_index"}
    names = {it.get("name", ""): it for it in items}
    if metadata_pdoc:
        # submissions primaryDocument may carry a path prefix
        # ("xslF345X05/form4a.xml") while the dir listing is bare
        # filenames -- match both forms.
        base = metadata_pdoc.rsplit("/", 1)[-1]
        for cand in (metadata_pdoc, base):
            if cand in names:
                return {"filename": cand, "source": "metadata"}
    skip = ("-index.htm", "-index-headers.htm", "index.json")
    for it in items:
        name = it.get("name", "")
        if name.lower().endswith(".xml") and not name.startswith("."):
            if not any(s in name for s in skip):
                return {"filename": name, "source": "index_xml"}
    return {"filename": None, "source": "none"}


# --------------------------------------------------------------------- #
# fetch state (crash-safe resume) + manifest
# --------------------------------------------------------------------- #

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_state(state_path: str) -> dict[str, dict]:
    """accession_nodash -> terminal state row (OK / NOT_FOUND / FAILED).
    In-flight (non-terminal) rows are ignored so a crash mid-accession
    refetches that accession cleanly."""
    out: dict[str, dict] = {}
    if not os.path.exists(state_path):
        return out
    with open(state_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("status") in ("OK", "NOT_FOUND", "FAILED"):
                out[row["accession_nodash"]] = row
    return out


class StateWriter:
    """Append-only jsonl fetch log (one row per accession, flushed)."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._fh = open(path, "a", encoding="utf-8")

    def append(self, row: dict) -> None:
        with self._lock:
            self._fh.write(json.dumps(row, sort_keys=True) + "\n")
            self._fh.flush()
            os.fsync(self._fh.fileno())

    def close(self) -> None:
        with self._lock:
            self._fh.close()


def fetch_targets(targets: list[dict], out_root: str, state_path: str,
                  transport: Transport | None = None,
                  limiter: RateLimiter | None = None,
                  max_accessions: int | None = None,
                  workers: int = 2,
                  ) -> dict:
    """Fetch index.json + primary doc for every target accession.

    Etiquette lives inside ``real_transport`` (global start-time
    spacing <= 2 req/s) when it is the transport; the optional
    ``limiter`` only gates injected test transports.  ``workers`` (>1)
    overlaps RESPONSE LATENCY only: every attempt still passes through
    the one global limiter, so request START times remain spaced >=
    MIN_INTERVAL seconds machine-wide -- the rate ceiling is unchanged.
    Crash-safe (resume via state file); honest accounting: returns
    counts + ``blocked_partial`` flag when the session aborted early
    (never retried past the abort rule)."""
    transport = transport or real_transport
    done = load_state(state_path)
    writer = StateWriter(state_path)
    summary: dict[str, Any] = {
        "targets": len(targets),
        "resumed_done": 0, "fetched_ok": 0, "not_found": 0,
        "failed": 0, "non_xml_primary": 0, "blocked_partial": False,
        "abort_reason": None, "workers": workers,
    }
    pending: list[dict] = []
    for t in targets:
        prev = done.get(t["accession_nodash"])
        if prev is not None:
            summary["resumed_done"] += 1
            if prev.get("primary_is_xml") is False:
                summary["non_xml_primary"] += 1
        else:
            pending.append(t)
    if max_accessions is not None:
        pending = pending[:max_accessions]

    if workers <= 1 or transport is not real_transport:
        consecutive = 0
        try:
            for t in pending:
                row = _fetch_guarded(t, out_root, transport, limiter,
                                     writer)
                done[row["accession_nodash"]] = row
                consecutive = _account(row, summary, consecutive)
                if consecutive >= ABORT_AFTER_CONSECUTIVE_FAILURES:
                    summary["blocked_partial"] = True
                    summary["abort_reason"] = (
                        f"{consecutive} consecutive failed accessions "
                        "-- etiquette stop (EDGAR blocking or outage); "
                        "NOT hammered")
                    break
        finally:
            writer.close()
        return summary

    # ---- latency-overlap mode: shared limiter, shared abort rule --- #
    from concurrent.futures import ThreadPoolExecutor
    lock = threading.Lock()
    state = {"consecutive": 0, "abort": False, "reason": None}

    def work(t: dict) -> None:
        with lock:
            if state["abort"]:
                return
        row = _fetch_guarded(t, out_root, transport, limiter, writer)
        with lock:
            done[row["accession_nodash"]] = row
            state["consecutive"] = _account(row, summary,
                                            state["consecutive"])
            if (state["consecutive"]
                    >= ABORT_AFTER_CONSECUTIVE_FAILURES):
                state["abort"] = True
                state["reason"] = (
                    f"{state['consecutive']} consecutive failed "
                    "accessions -- etiquette stop (EDGAR blocking or "
                    "outage); NOT hammered")

    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for t in pending:
                with lock:
                    if state["abort"]:
                        break
                ex.submit(work, t)
            ex.shutdown(wait=True)
    finally:
        writer.close()
    summary["blocked_partial"] = state["abort"]
    summary["abort_reason"] = state["reason"]
    return summary


def _fetch_guarded(t: dict, out_root: str, transport: Transport,
                   limiter: RateLimiter | None, writer: StateWriter,
                   ) -> dict:
    fallback_row = {"cik": t["cik"], "accession": t["accession"],
                    "accession_nodash": t["accession_nodash"],
                    "filing_date": t["filing_date"]}
    try:
        row = _fetch_one(t, out_root, transport, limiter)
    except Exception as exc:  # noqa: BLE001 - session survives
        row = dict(fallback_row, status="FAILED", stage="exception",
                   error=repr(exc))
    writer.append(row)
    return row


def _account(row: dict, summary: dict, consecutive: int) -> int:
    if row["status"] == "OK":
        summary["fetched_ok"] += 1
        if row.get("primary_is_xml") is False:
            summary["non_xml_primary"] += 1
        return 0
    if row["status"] == "NOT_FOUND":
        summary["not_found"] += 1
        return 0
    summary["failed"] += 1
    return consecutive + 1


def _fetch_one(t: dict, out_root: str, transport: Transport,
               limiter: RateLimiter) -> dict:
    """One accession: index.json + primary doc -> data_raw/form4a tree.

    Uses the injected transport for byte transfer but keeps its OWN
    per-URL retry/backoff policy on top (test transports are instant;
    the real transport already backs off internally too -- double
    safety, still <= 2 req/s because every attempt goes through the
    limiter)."""
    accn = t["accession_nodash"]
    cik = t["cik"]
    cik_int = t["cik_int"]
    acc_dir = os.path.join(out_root, cik, accn)
    base_row = {"cik": cik, "accession": t["accession"],
                "accession_nodash": accn,
                "filing_date": t["filing_date"]}
    row = dict(base_row)
    # real_transport self-limits globally; a manual limiter would only
    # apply to injected (instant, offline) test transports.
    gate = None if transport is real_transport else limiter

    # ---- index.json ----
    idx_status, idx_body = _get_with_backoff(
        accession_index_url(cik_int, accn), transport, gate)
    if idx_status == 404:
        row.update(status="NOT_FOUND", missing="index.json",
                   http_status=404)
        return row
    if idx_status != 200:
        row.update(status="FAILED", stage="index.json",
                   http_status=idx_status)
        return row
    picked = choose_primary_doc(idx_body, t["primary_document"])
    if picked["filename"] is None:
        os.makedirs(acc_dir, exist_ok=True)
        _atomic_write(os.path.join(acc_dir, "index.json"), idx_body)
        row.update(status="OK", primary_file=None,
                   primary_source=picked["source"],
                   primary_is_xml=False,
                   index_sha256=_sha256_bytes(idx_body),
                   note="no usable primary doc in dir listing")
        return row

    # ---- primary doc ----
    doc_status, doc_body = _get_with_backoff(
        accession_file_url(cik_int, accn, picked["filename"]),
        transport, gate)
    if doc_status == 404:
        row.update(status="NOT_FOUND", missing="primary_doc",
                   primary_file=picked["filename"],
                   http_status=404)
        return row
    if doc_status != 200:
        row.update(status="FAILED", stage="primary_doc",
                   primary_file=picked["filename"],
                   http_status=doc_status)
        return row
    os.makedirs(acc_dir, exist_ok=True)
    _atomic_write(os.path.join(acc_dir, "index.json"), idx_body)
    _atomic_write(os.path.join(acc_dir, picked["filename"]), doc_body)
    row.update(status="OK",
               primary_file=picked["filename"],
               primary_source=picked["source"],
               primary_is_xml=picked["filename"].lower().endswith(".xml"),
               index_sha256=_sha256_bytes(idx_body),
               primary_sha256=_sha256_bytes(doc_body),
               primary_bytes=len(doc_body))
    return row


def _get_with_backoff(url: str, transport: Transport,
                      limiter: RateLimiter | None) -> tuple[int, bytes]:
    """Attempts with honest backoff between retries.  ``limiter`` is
    OPTIONAL and must be None when the transport is ``real_transport``
    (which already enforces the global etiquette budget internally --
    double-gating would double per-request latency without changing the
    ceiling); injected test transports are instant and need no gate."""
    delay_idx = 0
    status, body = -1, b""
    for attempt in range(MAX_ATTEMPTS):
        if limiter is not None:
            limiter.acquire()
        status, body = transport(url)
        if status in _RETRY_STATUSES and attempt < MAX_ATTEMPTS - 1:
            time.sleep(BACKOFF_SCHEDULE[min(delay_idx,
                                            len(BACKOFF_SCHEDULE) - 1)])
            delay_idx += 1
            continue
        return status, body
    return status, body  # type: ignore[possibly-undefined]


def _atomic_write(path: str, data: bytes) -> None:
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


# --------------------------------------------------------------------- #
# P-7 canaries: 2 fabricated accessions + 1 dead CIK must FAIL
# --------------------------------------------------------------------- #

FABRICATED_ACCESSIONS = (
    # year segments 2099 are impossible on EDGAR (accession year <= now)
    {"cik": "CIK0000001800", "cik_int": 1800,
     "accession": "0000001800-99-999999",
     "accession_nodash": "000000180099999999",
     "filing_date": None, "primary_document": None, "form": "4/A"},
    {"cik": "CIK0000066740", "cik_int": 66740,
     "accession": "0000066740-99-000001",
     "accession_nodash": "000006674099000001",
     "filing_date": None, "primary_document": None, "form": "4/A"},
)

#: CIK far beyond the assigned range (assigned CIKs are << 9,999,999).
DEAD_CIK = {"cik": "CIK0009999999", "cik_int": 9999999}


def canary_checks(transport: Transport | None = None,
                  limiter: RateLimiter | None = None) -> dict:
    """P-7 law: fabricated accessions and a dead CIK MUST fail (404 /
    non-200).  A canary that unexpectedly SUCCEEDS is a positive
    anomaly (fail-closed verdict for the gate)."""
    transport = transport or real_transport
    checks: list[dict] = []
    for fab in FABRICATED_ACCESSIONS:
        if limiter is not None and transport is not real_transport:
            limiter.acquire()
        try:
            status, _body = transport(
                accession_index_url(fab["cik_int"], fab["accession_nodash"]))
        except Exception as exc:  # noqa: BLE001 - canary must be terminal
            checks.append({
                "kind": "fabricated_accession",
                "cik": fab["cik"], "accession": fab["accession"],
                "http_status": f"TRANSPORT_ERROR:{type(exc).__name__}",
                "expected": "FAIL (404)",
                "failed_as_expected": False,
            })
            continue
        checks.append({
            "kind": "fabricated_accession",
            "cik": fab["cik"], "accession": fab["accession"],
            "http_status": status,
            "expected": "FAIL (404)",
            "failed_as_expected": status == 404,
        })
    dead_url = f"{EDGAR_SUBMISSIONS_BASE}/{DEAD_CIK['cik']}.json"
    if limiter is not None and transport is not real_transport:
        limiter.acquire()
    try:
        status, _body = transport(dead_url)
    except Exception as exc:  # noqa: BLE001 - canary must be terminal
        status = f"TRANSPORT_ERROR:{type(exc).__name__}"
    checks.append({
        "kind": "dead_cik",
        "cik": DEAD_CIK["cik"], "probe_url": dead_url,
        "http_status": status,
        "expected": "FAIL (404)",
        "failed_as_expected": status == 404,
    })
    return {
        "rule": ("2 never-existed accessions + 1 dead CIK must FAIL "
                 "(404); a success is a positive anomaly"),
        "checks": checks,
        "all_failed_as_expected": all(c["failed_as_expected"]
                                      for c in checks),
    }


# --------------------------------------------------------------------- #
# manifest (sha256 per file + aggregate) for the committed control dir
# --------------------------------------------------------------------- #

def build_manifest(out_root: str, state_path: str) -> dict:
    """Digest every file actually on disk under out_root; cross-check
    against the fetch state (every state-OK accession must have both
    files present with matching digests); aggregate digest over the
    sorted per-file digests."""
    state = load_state(state_path)
    files: dict[str, str] = {}
    for dirpath, _dirnames, filenames in os.walk(out_root):
        for fn in filenames:
            if fn.endswith(".tmp"):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, out_root)
            files[rel] = _sha256_file(p)
    # cross-check state vs disk
    ok_rows = [r for r in state.values() if r["status"] == "OK"]
    cross_bad: list[dict] = []
    for r in ok_rows:
        base = os.path.join(r["cik"], r["accession_nodash"])
        idx_rel = os.path.join(base, "index.json")
        if r.get("primary_file"):
            doc_rel = os.path.join(base, r["primary_file"])
            want = [(idx_rel, r.get("index_sha256")),
                    (doc_rel, r.get("primary_sha256"))]
        else:
            want = [(idx_rel, r.get("index_sha256"))]
        for rel, want_sha in want:
            got = files.get(rel)
            if got != want_sha:
                cross_bad.append({"rel": rel, "state_sha256": want_sha,
                                  "disk_sha256": got})
    agg_input = "\n".join(f"{k} {files[k]}" for k in sorted(files))
    return {
        "files": {k: files[k] for k in sorted(files)},
        "file_count": len(files),
        "aggregate_sha256": _sha256_bytes(agg_input.encode("utf-8")),
        "state_ok_accessions": len(ok_rows),
        "state_disk_crosscheck_mismatches": cross_bad,
        "status": "OK" if not cross_bad else "MISMATCH",
    }


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
