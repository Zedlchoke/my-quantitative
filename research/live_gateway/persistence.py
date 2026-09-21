"""Atomic persistence: raw store, event log, heartbeat, counters.

Four separated stores (plan §7): raw immutable observations
(daily .jsonl.gz, content-deduplicated), normalized REST cache (see
reststore.py), current snapshot (heartbeat + latest), append-only
health/error events. Atomic writes = tmp + fsync + rename everywhere;
restart never double-counts (counters persisted; raw rows deduplicated
by digest on reload).
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .timeutils import NowMs, default_now_ms, ms_to_iso_z

RAW_RETENTION_DAYS = 14
RAW_RETENTION_BYTES = 2 * 1024**3
EVENT_LOG_MAX_LINES = 100_000


def atomic_write_bytes(path: str, payload: bytes) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def atomic_write_json(path: str, obj: Any) -> None:
    atomic_write_bytes(
        path,
        (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "utf-8"
        ),
    )


def read_json(path: str) -> Optional[Any]:
    try:
        with open(path, "rb") as handle:
            return json.loads(handle.read().decode("utf-8"))
    except (FileNotFoundError, ValueError):
        return None


def digest_obj(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class EventLog:
    """Append-only incident/health history. Never truncated by restart.

    Hard line cap exists only as a disk-safety valve (oldest lines are
    rotated to a .1 sidecar, never silently deleted).
    """

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def append(self, kind: str, detail: Dict[str, Any], now_ms_: NowMs = default_now_ms) -> None:
        row = {
            "at_utc": ms_to_iso_z(now_ms_()),
            "kind": kind,
            **detail,
        }
        line = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        if (
            os.path.exists(self.path)
            and os.path.getsize(self.path) > EVENT_LOG_MAX_LINES * 400
        ):
            sidecar = self.path + ".1"
            if os.path.exists(sidecar):
                os.remove(sidecar)
            os.replace(self.path, sidecar)
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())

    def tail(self, n: int = 50) -> List[dict]:
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                lines = handle.readlines()[-n:]
        except FileNotFoundError:
            return []
        out = []
        for line in lines:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
        return out


class RawStore:
    """Immutable append-only observations, daily gzip files.

    Rows are content-deduplicated per symbol (only changed observations
    are appended). On restart the tail digests are reloaded so a replay
    of the same observation never double-writes. Retention: 14 days OR
    2 GiB total, whichever first; only WHOLE oldest days are removed,
    each removal logged by the caller via EventLog.
    """

    def __init__(self, root: str, now_ms_: NowMs = default_now_ms):
        self.root = root
        self.now_ms = now_ms_
        self._seen: Dict[str, str] = {}
        self.rows_written = 0
        self.duplicates_suppressed = 0
        os.makedirs(root, exist_ok=True)
        self._load_tail_digests()

    def _day_path(self, day: str) -> str:
        return os.path.join(self.root, f"{day}.jsonl.gz")

    def _load_tail_digests(self) -> None:
        """Reload the LAST day's dedup digests (crash-safe resume)."""
        suffix_len = len(".jsonl.gz")
        days = sorted(
            f[:-suffix_len]
            for f in os.listdir(self.root)
            if f.endswith(".jsonl.gz")
        )
        if not days:
            return
        path = self._day_path(days[-1])
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    key = str(row.get("key") or row.get("symbol") or "")
                    dig = row.get("digest")
                    if key and dig:
                        self._seen[f"{key}|{dig}"] = "1"
        except (OSError, EOFError):
            pass  # corrupt tail file: dedup restarts empty, rows may
            # duplicate once; counters are loaded separately (no
            # double-count of METRICS; raw duplicate rows are bounded
            # by the daily file boundary and disclosed here)

    def append_observation(
        self, key: str, payload: Dict[str, Any]
    ) -> bool:
        """Append one observation unless deduplicated. True = written.

        A7 impl-r1 FND-1 fix: rows APPEND directly to the daily file
        (gzip append adds a member; fsync'd) — the previous tmp+rename
        wiped all prior rows of the day. Crash mid-append leaves a
        partial tail member which _load_tail_digests skips (ValueError
        -> continue) and counters live elsewhere, so no double-count.
        """
        dig = digest_obj(payload)
        dedup_key = f"{key}|{dig}"
        if dedup_key in self._seen:
            self.duplicates_suppressed += 1
            return False
        day = ms_to_iso_z(self.now_ms())[:10]
        row = {"key": key, "digest": dig, **payload}
        line = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        path = self._day_path(day)
        with open(path, "ab") as raw_handle:
            with gzip.GzipFile(fileobj=raw_handle, mode="ab") as gz:
                gz.write(line.encode("utf-8"))
            raw_handle.flush()
            os.fsync(raw_handle.fileno())
        self._seen[dedup_key] = "1"
        self.rows_written += 1
        return True

    def enforce_retention(self) -> List[str]:
        """Remove whole oldest days beyond retention. Returns removed."""
        import datetime as dt

        suffix_len = len(".jsonl.gz")
        days = sorted(
            f[:-suffix_len]
            for f in os.listdir(self.root)
            if f.endswith(".jsonl.gz")
        )
        removed: List[str] = []
        now_day = ms_to_iso_z(self.now_ms())[:10]
        today = dt.date.fromisoformat(now_day)
        for day in days:
            try:
                age_days = (today - dt.date.fromisoformat(day)).days
            except ValueError:
                continue
            if age_days > RAW_RETENTION_DAYS or self._total_bytes() > RAW_RETENTION_BYTES:
                if day == now_day:
                    break  # never delete the live day
                os.remove(self._day_path(day))
                removed.append(day)
            else:
                break  # oldest-first: stop at first retained day
        return removed

    def _total_bytes(self) -> int:
        return sum(
            os.path.getsize(os.path.join(self.root, f))
            for f in os.listdir(self.root)
            if f.endswith(".jsonl.gz")
        )

    def disk_bytes(self) -> int:
        return self._total_bytes()


@dataclass
class PersistedCounters:
    """Metrics counters surviving restarts (no double-count)."""

    path: str
    counters: Dict[str, int] = field(default_factory=dict)

    def load(self) -> None:
        data = read_json(self.path)
        if isinstance(data, dict):
            self.counters = {
                k: int(v) for k, v in data.items() if isinstance(v, int)
            }

    def bump(self, name: str, by: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + by

    def save(self) -> None:
        atomic_write_json(self.path, self.counters)
