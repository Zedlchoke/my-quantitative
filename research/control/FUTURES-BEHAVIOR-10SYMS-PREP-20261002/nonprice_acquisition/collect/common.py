"""Shared collector infrastructure for NONPRICE-DATA-ACQUISITION.

Laws enforced here (dispatch 2026-10-02):
- raw files OUTSIDE git at RAW_ROOT; manifest raw_manifest.jsonl append-only
- SHA256 checkpoint per file; dedupe = skip if (path exists + sha matches + status ok)
- polite rate limits, bounded retries w/ backoff
- total cap raw+derived 2 GiB + per-family subcaps; over-cap -> typed
  WAIT_STORAGE and the collector STOPS that family (no deletions ever)
- no credentials, no key routes, no 403/login/captcha bypass: on 403/401 the
  blocker is RECORDED and the collector moves on (HTTP status preserved)
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import time
import datetime as dt
from pathlib import Path

import requests

RAW_ROOT = Path("/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
MANIFEST = RAW_ROOT / "raw_manifest.jsonl"
GLOBAL_CAP_BYTES = 2 * 1024**3          # 2 GiB raw+derived initial cap
# NOAA subcap 1.1 GiB (bounded plan 2026-10-02: 610temp full 2012-09..2025-06
# + weekly big-file regime sample + 814temp 30d pilot + climdiv observed +
# NDFD 30d pilot; projected ~0.9 GiB; see PUBLIC_DATA_ACQUISITION_REPORT_VI.md)
FAMILY_SUBCAPS = {"noaa": 1_181_116_211}
MACHINE_RESERVE_BYTES = 4 * 1024**3      # keep >= 4 GiB free on the volume
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) nonprice-collector/1.0 (research; contact-via-repo)")

_session = requests.Session()
_session.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
_last_request_ts = 0.0
_bytes_written = 0
# ERRATUM 2026-10-02 (NONPRICE-FIX, audit m-2): the pre-fix collector deduped
# across runs (sha256 checkpoint) but not WITHIN a session - 60 duplicate
# (url, sha256) fetch pairs were recorded in raw_manifest.jsonl for this task
# (58 ALFRED vintage verification re-fetches ~20 s apart, 1 CPC zip, 3 NCEI
# dir listings; identical shas, no integrity impact). Session-level rule
# added: a URL already fetched OK in this process is skipped (recorded with
# dedupe=True, no second network fetch).
_session_ok_urls: set[str] = set()


def utcnow_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _manifest_index() -> dict:
    idx = {}
    if MANIFEST.exists():
        with open(MANIFEST) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                idx[rec.get("path", "")] = rec
    return idx


_IDX = _manifest_index()


def already_ok(rel_path: str) -> bool:
    rec = _IDX.get(rel_path)
    if not rec or rec.get("status") != "ok":
        return False
    abs_path = RAW_ROOT / rel_path
    if not abs_path.exists():
        return False
    return sha256_file(abs_path) == rec.get("sha256")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def disk_free_bytes() -> int:
    st = os.statvfs(RAW_ROOT)
    return st.f_bavail * st.f_frsize


def family_bytes_used(family: str) -> int:
    used = 0
    for rec in _IDX.values():
        if rec.get("family") == family and rec.get("status") == "ok":
            used += int(rec.get("bytes", 0))
    return used


def total_bytes_used() -> int:
    return sum(int(r.get("bytes", 0)) for r in _IDX.values() if r.get("status") == "ok")


def check_budget(family: str, incoming: int) -> tuple[bool, str]:
    """Return (allowed, reason)."""
    used = total_bytes_used()
    if used + incoming > GLOBAL_CAP_BYTES:
        return False, (f"WAIT_STORAGE: global cap {GLOBAL_CAP_BYTES} would be exceeded "
                       f"(used {used} + {incoming})")
    sub = FAMILY_SUBCAPS.get(family)
    if sub is not None:
        fu = family_bytes_used(family)
        if fu + incoming > sub:
            return False, (f"WAIT_STORAGE: family subcap {sub} for '{family}' would be "
                           f"exceeded (used {fu} + {incoming})")
    free = disk_free_bytes()
    if free - incoming < MACHINE_RESERVE_BYTES:
        return False, (f"WAIT_STORAGE: machine reserve {MACHINE_RESERVE_BYTES} "
                       f"(free {free}, incoming {incoming})")
    return True, ""


def append_manifest(rec: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    rec.setdefault("retrieved_at_utc", utcnow_iso())
    with open(MANIFEST, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    _IDX[rec.get("path", "")] = rec


def rate_limit_sleep(min_interval_s: float) -> None:
    global _last_request_ts
    wait = _last_request_ts + min_interval_s - time.time()
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.time()


def http_get(url: str, *, family: str, rel_path: str, rate_limit_s: float = 0.5,
             retries: int = 3, backoff_s: float = 2.0, timeout: int = 120,
             max_bytes: int | None = None, force: bool = False,
             params: dict | None = None) -> dict:
    """Download url -> RAW_ROOT/rel_path with checkpoint/dedupe/caps.

    Returns manifest record dict (status ok | http_error | wait_storage ...).
    On HTTP 403/401/407/429-exhausted the blocker is recorded, never bypassed.
    """
    if not force and url in _session_ok_urls and already_ok(rel_path):
        prev = _IDX[rel_path]
        return dict(prev, dedupe=True, dedupe_scope="session")
    if not force and already_ok(rel_path):
        prev = _IDX[rel_path]
        return dict(prev, dedupe=True)

    est = max_bytes or 64 * 1024**2  # conservative pre-check estimate if size unknown
    ok, reason = check_budget(family, 0)  # final exact check happens post-download
    if not ok:
        rec = {"family": family, "path": rel_path, "source_url": url, "status": "wait_storage",
               "reason": reason, "retrieved_at_utc": utcnow_iso()}
        append_manifest(rec)
        return rec

    abs_path = RAW_ROOT / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = abs_path.with_suffix(abs_path.suffix + ".part")

    status = None
    resp = None
    for attempt in range(1, retries + 1):
        rate_limit_sleep(rate_limit_s)
        try:
            resp = _session.get(url, timeout=timeout, params=params, stream=True)
            status = resp.status_code
            if status == 200:
                break
            if status in (403, 401, 407, 451):
                break  # lawful gate: record, do not retry-bypass
        except requests.RequestException as exc:
            status = f"exception:{type(exc).__name__}"
            resp = None
        if attempt < retries:
            time.sleep(backoff_s * attempt)

    if resp is None or status != 200:
        body_snippet = ""
        rec = {"family": family, "path": rel_path, "source_url": url,
               "http_status": status, "status": "http_error",
               "attempts": retries,
               "reason": f"HTTP {status} - lawful gate or transient; recorded, not bypassed",
               "retrieved_at_utc": utcnow_iso()}
        append_manifest(rec)
        return rec

    size = 0
    with open(tmp_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            size += len(chunk)
            f.write(chunk)
            if max_bytes is not None and size > max_bytes:
                f.close()
                tmp_path.unlink(missing_ok=True)
                rec = {"family": family, "path": rel_path, "source_url": url,
                       "http_status": 200, "status": "wait_storage",
                       "reason": f"WAIT_STORAGE: exceeded per-file max_bytes {max_bytes}",
                       "retrieved_at_utc": utcnow_iso()}
                append_manifest(rec)
                return rec

    ok, reason = check_budget(family, size)
    if not ok:
        tmp_path.unlink(missing_ok=True)
        rec = {"family": family, "path": rel_path, "source_url": url,
               "http_status": 200, "status": "wait_storage", "bytes": size,
               "reason": reason, "retrieved_at_utc": utcnow_iso()}
        append_manifest(rec)
        return rec

    tmp_path.replace(abs_path)
    digest = sha256_file(abs_path)
    _session_ok_urls.add(url)
    rec = {"family": family, "path": rel_path, "source_url": url,
           "http_status": 200, "status": "ok", "sha256": digest,
           "bytes": size, "retrieved_at_utc": utcnow_iso()}
    append_manifest(rec)
    global _bytes_written
    _bytes_written += size
    return rec


def summary() -> dict:
    fams = {}
    for rec in _IDX.values():
        fam = rec.get("family", "?")
        s = fams.setdefault(fam, {"files_ok": 0, "bytes_ok": 0, "errors": 0, "wait_storage": 0})
        if rec.get("status") == "ok":
            s["files_ok"] += 1
            s["bytes_ok"] += int(rec.get("bytes", 0))
        elif rec.get("status") == "wait_storage":
            s["wait_storage"] += 1
        else:
            s["errors"] += 1
    return {"total_bytes": total_bytes_used(), "cap_bytes": GLOBAL_CAP_BYTES,
            "disk_free_bytes": disk_free_bytes(), "families": fams}


def year_chunks(start_year: int, end_year: int):
    for y in range(start_year, end_year + 1):
        yield y


def record_count_generic(path: Path) -> int | None:
    """Best-effort record count for text/csv/jsonl files."""
    try:
        if path.suffix in (".csv", ".txt", ".tsv", ".jsonl"):
            with open(path, "rb") as f:
                return sum(1 for _ in f)
        if path.suffix == ".json":
            data = json.load(open(path))
            return len(data) if isinstance(data, list) else 1
    except Exception:
        return None
    return None
