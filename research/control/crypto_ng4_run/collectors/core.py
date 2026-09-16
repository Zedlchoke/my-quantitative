"""Shared capture core for the CRYPTO-NG4 prospective collectors.

Implements the frozen A3 contract conventions (cng4-a3 dossier, freeze
fields 2/5/6/7/8):

- envelope  : one JSON object per raw line {recv_utc, channel, seq, payload}
              with recv_utc at microsecond resolution; seq equals the
              Deribit change_id where served, else null.
- shards    : content-addressed root
              <data_root>/<venue>/<YYYY>/<MM>/<DD>/<conn_epoch>.jsonl
              one shard per (venue, UTC day, connection_epoch); created
              as ``<conn_epoch>.jsonl.open`` and closed via temp+atomic
              rename; a closed shard is NEVER rewritten.
- manifests : append-only JSONL at the raw root; every row chains
              prev_manifest_sha256 = sha256 of the full prior manifest
              head so truncation/tamper is detectable.
- gaps      : explicit gap record lines {type:'gap', venue, channel,
              instrument, from_seq, to_seq, missing_count, first_recv_utc}
              appended INTO the raw shard — the gap is DATA, never dropped.
- duplicates: raw capture is verbatim and never deduplicated; dup_count is
              counted per shard and reported in the manifest row.
- rejections: messages failing parse/schema go raw to a shard-rejected
              subrecord (<shard-stem>.rejected.jsonl) with reason; nothing
              is dropped unlogged.  Mismatch fails LOUD (stderr + counters).
- handles   : inode-check on every append so a rotated/replaced file is
              caught instead of silently mis-written.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Hashable, List, Optional

DEFAULT_DATA_ROOT = Path(
    "/Users/hoangminhlong/.my-quantitative-data/crypto-ng4-ws/raw"
)
MANIFEST_NAME = "manifest.jsonl"
DUP_TRACK_WINDOW = 4096  # bounded recent-line-hash window for unsequenced channels


def utc_now_iso(clock: Optional[Callable[[], datetime]] = None) -> str:
    dt = (clock or _default_now)()
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


def shard_rel_path(venue: str, day_utc: str, conn_epoch: int) -> str:
    """(venue, UTC day, connection_epoch) -> relative shard path."""
    y, m, d = day_utc[0:4], day_utc[5:7], day_utc[8:10]
    return f"{venue}/{y}/{m}/{d}/{conn_epoch:08d}.jsonl"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class LoudError(RuntimeError):
    """Raised for conditions that must never be papered over."""


class AppendHandle:
    """Append handle with inode verification on every write.

    plan §7 hygiene: inode-check on append handles.  If the file the handle
    points at was replaced/rotated under us, raise LoudError instead of
    writing into the wrong inode.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "ab")
        self.inode = os.fstat(self._fh.fileno()).st_ino
        self.bytes_written = 0

    def write_line(self, raw: bytes) -> None:
        st = os.fstat(self._fh.fileno())
        if st.st_ino != self.inode:
            raise LoudError(
                f"inode-check FAILED on {self.path}: handle inode {self.inode} "
                f"!= current {st.st_ino} (handle replaced)"
            )
        # path-side check: catches the file being replaced/rotated while our
        # (still open) fd silently points at the now-unlinked old inode
        if os.path.exists(self.path) and os.stat(self.path).st_ino != self.inode:
            raise LoudError(
                f"inode-check FAILED on {self.path}: file replaced under "
                f"append handle (path inode {os.stat(self.path).st_ino} != "
                f"handle inode {self.inode})"
            )
        self._fh.write(raw + b"\n")
        self._fh.flush()
        os.fsync(self._fh.fileno())
        self.bytes_written += len(raw) + 1

    def close(self) -> None:
        try:
            self._fh.flush()
            os.fsync(self._fh.fileno())
        finally:
            self._fh.close()


class ShardWriter:
    """One open shard per (venue, UTC day, connection_epoch).

    Created as ``<epoch>.jsonl.open``; closed via atomic rename to
    ``<epoch>.jsonl``.  Appends are line-atomic and fsynced.
    """

    def __init__(
        self,
        data_root: Path,
        venue: str,
        day_utc: str,
        conn_epoch: int,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self.data_root = data_root
        self.venue = venue
        self.day_utc = day_utc
        self.conn_epoch = conn_epoch
        self.clock = clock or _default_now
        self.rel = shard_rel_path(venue, day_utc, conn_epoch)
        self.final_rel = self.rel
        self.open_rel = self.rel + ".open"
        self.open_path = data_root / self.open_rel
        self.handle: Optional[AppendHandle] = None
        self.sha = hashlib.sha256()
        self.lines = 0
        self.bytes = 0
        self.first_recv_utc: Optional[str] = None
        self.last_recv_utc: Optional[str] = None
        self.per_channel_counts: Dict[str, int] = {}
        self.gap_count = 0
        self.dup_count = 0
        self.rejected_count = 0
        self.heartbeat_count = 0
        self.rejected_handle: Optional[AppendHandle] = None
        self.rejected_path = data_root / (self.open_rel.replace("/", "_") + ".rejected.jsonl")
        self.closed_utc: Optional[str] = None
        # dup tracking: exact (channel, seq) key for sequenced channels;
        # bounded recent raw-line hashes for unsequenced ones.
        self._seq_keys: set = set()
        self._recent_line_hashes: Dict[str, set] = {}

    # -- lifecycle -------------------------------------------------------
    def open(self) -> None:
        if self.handle is not None:
            raise LoudError(f"shard {self.rel} already open")
        self.handle = AppendHandle(self.open_path)
        self.rejected_handle = AppendHandle(self.rejected_path)

    def _envelope_line(
        self, recv_utc: str, channel: str, seq: Optional[int], payload: Dict[str, Any]
    ) -> bytes:
        obj = {"recv_utc": recv_utc, "channel": channel, "seq": seq, "payload": payload}
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    # -- writes ----------------------------------------------------------
    def append_message(
        self, recv_utc: str, channel: str, seq: Optional[int], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Append one envelope line verbatim (no field renaming, no
        reordering, no dedup).  Returns capture bookkeeping."""
        raw = self._envelope_line(recv_utc, channel, seq, payload)
        assert self.handle is not None, "shard not open"
        self.handle.write_line(raw)
        self.sha.update(raw + b"\n")
        self.lines += 1
        self.bytes += len(raw) + 1
        if self.first_recv_utc is None:
            self.first_recv_utc = recv_utc
        self.last_recv_utc = recv_utc
        self.per_channel_counts[channel] = self.per_channel_counts.get(channel, 0) + 1
        return {"bytes": len(raw) + 1, "channel": channel}

    def append_gap_record(
        self,
        recv_utc: str,
        channel: str,
        instrument: str,
        from_seq: int,
        to_seq: int,
        missing_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Contract freeze field 5: the gap is DATA.  Appended into the raw
        shard as an explicit record, never dropped, never interpolated.
        missing_count defaults to the sequence-arithmetic estimate; a venue
        tracker may override it (e.g. -1 = unknown for Deribit aggregated
        book where lost-update counts are not derivable)."""
        if missing_count is None:
            missing_count = to_seq - from_seq - 1
        rec = {
            "type": "gap",
            "venue": self.venue,
            "channel": channel,
            "instrument": instrument,
            "from_seq": from_seq,
            "to_seq": to_seq,
            "missing_count": missing_count,
            "first_recv_utc": recv_utc,
        }
        raw = json.dumps(rec, separators=(",", ":")).encode("utf-8")
        assert self.handle is not None, "shard not open"
        self.handle.write_line(raw)
        self.sha.update(raw + b"\n")
        self.lines += 1
        self.bytes += len(raw) + 1
        self.gap_count += 1
        return rec

    def append_rejection(self, recv_utc: str, reason: str, raw_line: str) -> None:
        """Contract freeze field 5 'silent_data_never': a message failing
        parse/schema is written RAW to the shard-rejected subrecord with
        reason.  Nothing is dropped unlogged."""
        rec = {
            "type": "rejected",
            "venue": self.venue,
            "reason": reason,
            "recv_utc": recv_utc,
            "raw_line": raw_line[:4096],
        }
        raw = json.dumps(rec, separators=(",", ":")).encode("utf-8")
        assert self.rejected_handle is not None, "shard not open"
        self.rejected_handle.write_line(raw)
        self.rejected_count += 1
        print(
            f"[{self.venue}] LOUD payload-shape failure #{self.rejected_count}: "
            f"{reason}",
            file=sys.stderr,
            flush=True,
        )

    # -- duplicate accounting (verbatim capture; count only) -------------
    def note_duplicate(self, channel: str, key: Optional[Hashable], raw_line_hash: str) -> bool:
        """Count a duplicate for the shard manifest row (dup_count).  The
        raw line itself is STILL WRITTEN verbatim (field 8: raw capture is
        never deduplicated).  Keyed by the venue-native sequence identity
        when one exists (contract dedupe key), else by a bounded window of
        recent raw-line hashes for unsequenced channels (venue tickers)."""
        if key is not None:
            if key in self._seq_keys:
                self.dup_count += 1
                return True
            self._seq_keys.add(key)
            return False
        bucket = self._recent_line_hashes.setdefault(channel, set())
        if raw_line_hash in bucket:
            self.dup_count += 1
            return True
        if len(bucket) >= DUP_TRACK_WINDOW:
            bucket.clear()
        bucket.add(raw_line_hash)
        return False

    # -- close ------------------------------------------------------------
    def close(self, closed_utc: str) -> Path:
        """Temp+atomic rename; a closed shard is NEVER rewritten."""
        if self.handle is None:
            raise LoudError(f"shard {self.rel} close called but not open")
        self.handle.close()
        if self.rejected_handle is not None:
            self.rejected_handle.close()
        final_path = self.data_root / self.final_rel
        if final_path.exists():
            raise LoudError(f"closed shard {self.final_rel} already exists — refusing rewrite")
        os.replace(self.open_path, final_path)  # atomic
        self.closed_utc = closed_utc
        return final_path

    # -- digest -----------------------------------------------------------
    def sha256_hex(self) -> str:
        """Incremental sha256 over exactly the bytes this process appended
        (equals sha256 of the closed file for a fresh shard)."""
        return self.sha.hexdigest()

    def manifest_row(self, closed_utc: str, prev_manifest_sha256: str) -> Dict[str, Any]:
        return {
            "schema": "cng4_shard_manifest_row@1",
            "venue": self.venue,
            "connection_epoch": self.conn_epoch,
            "day_utc": self.day_utc,
            "path": self.final_rel,
            "sha256": self.sha256_hex(),
            "bytes": self.bytes,
            "lines": self.lines,
            "per_channel_counts": dict(self.per_channel_counts),
            "gap_count": self.gap_count,
            "dup_count": self.dup_count,
            "rejected_count": self.rejected_count,
            "heartbeat_count": self.heartbeat_count,
            "first_recv_utc": self.first_recv_utc,
            "last_recv_utc": self.last_recv_utc,
            "closed_utc": closed_utc,
            "prev_manifest_sha256": prev_manifest_sha256,
        }


class ManifestAppender:
    """Append-only JSONL manifest with head-hash chaining.

    hash-of-manifest-head is chained into each new row
    (prev_manifest_sha256 = sha256 of the full prior manifest bytes), so
    truncation/tamper of the manifest is detectable.
    """

    def __init__(self, manifest_path: Path) -> None:
        self.path = manifest_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self._head_sha = sha256_file(self.path)
            self._rows = sum(1 for ln in self.path.open("rb") if ln.strip())
        else:
            self._head_sha = hashlib.sha256(b"").hexdigest()
            self._rows = 0
        self._inode: Optional[int] = None
        if self.path.exists():
            self._inode = os.stat(self.path).st_ino

    def head_sha256(self) -> str:
        return self._head_sha

    def row_count(self) -> int:
        return self._rows

    def append_row(self, row: Dict[str, Any]) -> None:
        """Flock-guarded append with re-chaining + chain verification.

        Three venue processes share one root manifest: sibling appends
        between THIS process's last append and now are legitimate, so the
        row's prev_manifest_sha256 is REBOUND to the current head under the
        lock.  Truncation/tamper of already-written manifest bytes is
        detected by verifying the per-row prev_manifest_sha256 chain over
        the full file BEFORE appending (raise LoudError on breakage).
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(row, separators=(",", ":"), sort_keys=False).encode("utf-8")
        with open(self.path, "a+b") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                fh.seek(0)
                head = fh.read()
                self._verify_chain_bytes(head)
                current_head_sha = hashlib.sha256(head).hexdigest()
                if row.get("prev_manifest_sha256") != current_head_sha:
                    row["prev_manifest_sha256"] = current_head_sha  # re-chain
                    raw = json.dumps(row, separators=(",", ":"), sort_keys=False).encode("utf-8")
                fh.seek(0, os.SEEK_END)
                fh.write(raw + b"\n")
                fh.flush()
                os.fsync(fh.fileno())
                self._inode = os.fstat(fh.fileno()).st_ino
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        # head sha after our append (authoritative for the next row)
        self._head_sha = hashlib.sha256(head + raw + b"\n").hexdigest()
        self._rows += 1

    @staticmethod
    def _verify_chain_bytes(head: bytes) -> None:
        """Each row's prev_manifest_sha256 must equal sha256 of ALL manifest
        bytes preceding it.  A break means the manifest was truncated or
        edited outside the appending processes."""
        cumulative = hashlib.sha256(b"").hexdigest()
        offset = 0
        for ln in head.splitlines(keepends=True):
            if ln.strip():
                try:
                    row = json.loads(ln)
                except ValueError as exc:
                    raise LoudError(f"corrupt manifest line at byte {offset}: {exc}")
                prev = row.get("prev_manifest_sha256")
                if prev is not None and prev != cumulative:
                    raise LoudError(
                        f"manifest prev_manifest_sha256 chain BROKEN at byte "
                        f"{offset}: manifest truncated or tampered "
                        f"(expected {cumulative[:16]}..., found {str(prev)[:16]}...)"
                    )
            cumulative = hashlib.sha256(head[: offset + len(ln)]).hexdigest()
            offset += len(ln)


def finalize_orphan_shards(
    data_root: Path,
    venue: str,
    manifest: ManifestAppender,
    closed_utc: str,
) -> List[Dict[str, Any]]:
    """On startup, shards left ``.open`` by a hard kill are finalized:
    renamed to their closed name, hashed, and appended to the manifest with
    a ``finalized_on_restart`` note.  A closed shard is never rewritten —
    this only closes files that were never closed."""
    finalized = []
    open_files = sorted(set(data_root.glob(f"{venue}/*/*/*/*.jsonl.open")))
    for open_path in open_files:
        rel = str(open_path.relative_to(data_root)).removesuffix(".open")
        # skip if a manifest row already covers this path
        if manifest_has_path(manifest.path, rel):
            continue
        final_rel = rel
        final_path = data_root / final_rel
        if final_path.exists():
            # name collision with an already-closed shard (e.g. a previous
            # instance reused the epoch): keep BOTH — closed shards are
            # never rewritten, the orphan lands as a -rN correction name
            stem = rel[: -len(".jsonl")]
            n = 1
            while final_path.exists():
                final_rel = f"{stem}-r{n}.jsonl"
                final_path = data_root / final_rel
                n += 1
        os.replace(open_path, final_path)
        digest = sha256_file(final_path)
        size = final_path.stat().st_size
        rows = sum(1 for ln in final_path.open("rb") if ln.strip())
        digits = "".join(ch for ch in rel.rsplit("/", 1)[1].split(".")[0] if ch.isdigit())[:13]
        row = {
            "schema": "cng4_shard_manifest_row@1",
            "venue": venue,
            "connection_epoch": int(digits) if digits else -1,
            "day_utc": rel.split("/")[1] + "-" + rel.split("/")[2] + "-" + rel.split("/")[3],
            "path": final_rel,
            "sha256": digest,
            "bytes": size,
            "lines": rows,
            "per_channel_counts": {},
            "gap_count": -1,  # unknown: counters lived in the dead process
            "dup_count": -1,
            "rejected_count": -1,
            "heartbeat_count": -1,
            "first_recv_utc": None,
            "last_recv_utc": None,
            "closed_utc": closed_utc,
            "finalized_on_restart": True,
            **({"name_correction": True} if final_rel != rel else {}),
            "prev_manifest_sha256": manifest.head_sha256(),
        }
        manifest.append_row(row)
        finalized.append(row)
    return finalized


def manifest_has_path(manifest_path: Path, rel: str) -> bool:
    if not manifest_path.exists():
        return False
    with manifest_path.open("rb") as fh:
        for ln in fh:
            if not ln.strip():
                continue
            try:
                if json.loads(ln).get("path") == rel:
                    return True
            except ValueError:
                raise LoudError(f"corrupt manifest line in {manifest_path}")
    return False
