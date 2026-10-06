#!/usr/bin/env python3
"""mirror_batch.py — iCloud mirror step for ACQ-DOWNLOAD (owner instruction:
'đẩy lên icloud luôn để tôi lưu trữ').

Per QA-passed batch: copy the raw .dbn.zst + parquet + the batch's QA JSON +
its manifest/ledger entry into
/Users/hoangminhlong/Library/Mobile Documents/com~apple~CloudDocs/my-quantitative-futures/av1-trim/
and SHA256-verify each copy against its source.

Honesty law: a file present in CloudDocs is COPIED. Actual cloud upload is
macOS/iCloud's job -> every record is labeled SYNC_PENDING_UNVERIFIED; we
never claim cloud-stored. If local disk pressure requires it, previously
copied mirror files may be evicted from local disk via `brctl evict`
(iCloud keeps them; a dataless placeholder remains) -> recorded as
COPIED_EVICTED_SYNC_PENDING_UNVERIFIED. This is the owner's personal backup
of licensed data; no redistribution.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ICLOUD_BASE = Path("/Users/hoangminhlong/Library/Mobile Documents/"
                   "com~apple~CloudDocs/my-quantitative-futures/av1-trim")


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def free_gb() -> float:
    import os
    s = os.statvfs("/Users/hoangminhlong/my-quantitative-data")
    return s.f_bavail * s.f_frsize / 1e9


def evict(path: Path) -> bool:
    """Ask iCloud to evict a local copy (dataless placeholder). Best-effort."""
    try:
        r = subprocess.run(["/usr/bin/brctl", "evict", str(path)],
                           capture_output=True, text=True, timeout=120)
        return r.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def mirror_chunk(chunk: dict, *, manifest_blob: dict,
                 evict_threshold_gb: float | None = 6.0,
                 allow_evict: bool = True) -> dict:
    """Copy one chunk's artifacts to iCloud; SHA-verify; evict if needed."""
    line_id = chunk["line_id"]
    chunk_key = chunk["chunk_key"]
    dest_dir = ICLOUD_BASE / line_id / chunk_key
    dest_dir.mkdir(parents=True, exist_ok=True)
    out: dict = {"state": "COPIED", "sync": "SYNC_PENDING_UNVERIFIED",
                 "copied_utc": now_utc(), "files": [], "evicted": False,
                 "note": "Owner's personal iCloud backup of licensed "
                         "Databento data; no redistribution."}

    sources: list[tuple[Path, str]] = []
    for f in chunk.get("files", []):
        p = Path(f["local_path"])
        if p.exists():
            sources.append((p, p.name))
    qa_path = chunk.get("qa", {}).get("report_path")
    if qa_path and Path(qa_path).exists():
        sources.append((Path(qa_path), "qa.json"))
    pq = chunk.get("qa", {}).get("parquet_path")
    if pq and Path(pq).exists():
        sources.append((Path(pq), Path(pq).name))
    entry_path = dest_dir / "ledger_entry.json"
    entry_path.write_text(json.dumps({"chunk": chunk,
                                      "manifest": manifest_blob},
                                     default=str))
    out["files"].append({"name": "ledger_entry.json",
                         "bytes": entry_path.stat().st_size})

    for src, name in sources:
        dst = dest_dir / name
        shutil.copy2(src, dst)
        src_sha = sha256_of(src)
        dst_sha = sha256_of(dst)
        if src_sha != dst_sha:
            out["state"] = "COPY_FAILED_SHA_MISMATCH"
            out["mismatch"] = name
            return out
        out["files"].append({"name": name, "bytes": dst.stat().st_size,
                             "sha256": dst_sha, "sha256_match": True})

    if allow_evict and evict_threshold_gb is not None \
            and free_gb() < evict_threshold_gb:
        evicted = []
        for src, name in sources:
            p = dest_dir / name
            if evict(p):
                evicted.append(name)
        if evicted:
            out["evicted"] = True
            out["state"] = "COPIED_EVICTED"
            out["evicted_files"] = evicted
    return out


if __name__ == "__main__":
    ledger = json.loads(Path(sys.argv[1]).read_text())
    key = sys.argv[2]
    chunk = ledger["chunks"][key]
    print(json.dumps(mirror_chunk(chunk, manifest_blob={}),
                     default=str)[:2000])
