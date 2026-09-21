"""Normalized REST cache: canonical-key, TTL law, corruption quarantine.

TTLs [LEAD-FROZEN, plan §7]: klines/basis/funding closed historical
ranges = forever; premiumIndex 5 s; time 1 h; exchangeInfo 24 h. A
request whose exact canonical key exists and is complete is served
from cache and NOT re-downloaded. LRU-capped at 500 MiB with
eviction_refetch events. Corrupted cache files (bad JSON / truncated)
are quarantined (renamed) and treated as misses — never served.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from .persistence import atomic_write_json, read_json
from .timeutils import NowMs, default_now_ms

CACHE_TTL_MS = {
    "/fapi/v1/premiumIndex": 5_000,
    "/fapi/v1/time": 3_600_000,
    "/fapi/v1/exchangeInfo": 24 * 3_600_000,
    "/fapi/v1/klines": None,       # closed ranges: forever
    "/futures/data/basis": None,   # forever
    "/fapi/v1/fundingRate": None,  # forever
}
CACHE_DIR_NAME = "rest"
CACHE_MAX_BYTES = 500 * 1024**2


def canonical_key(path: str, params: Dict[str, Any]) -> Tuple[str, str]:
    """Canonical request identity: (sha256, identity-string)."""
    clean = {k: v for k, v in sorted(params.items()) if v is not None}
    query = urllib.parse.urlencode(clean)
    identity = f"GET {path}?{query}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest(), identity


def cache_path(root: str, key_sha: str) -> str:
    return os.path.join(root, CACHE_DIR_NAME, f"{key_sha}.json")


@dataclass
class CacheEntry:
    identity: str
    path: str
    params: Dict[str, Any]
    fetched_at_ms: int
    response_sha256: str
    payload: Any
    complete: bool

    def as_file(self) -> dict:
        return {
            "identity": self.identity,
            "path": self.path,
            "params": self.params,
            "fetched_at_ms": self.fetched_at_ms,
            "response_sha256": self.response_sha256,
            "payload": self.payload,
            "complete": self.complete,
        }

    @staticmethod
    def from_file(data: dict) -> "CacheEntry":
        return CacheEntry(
            identity=data["identity"],
            path=data["path"],
            params=data.get("params", {}),
            fetched_at_ms=int(data["fetched_at_ms"]),
            response_sha256=data["response_sha256"],
            payload=data.get("payload"),
            complete=bool(data.get("complete", False)),
        )


@dataclass
class RestCache:
    root: str
    now_ms: NowMs = field(default=default_now_ms)
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    quarantines: int = 0
    _evicted_recent: list = field(default_factory=list)  # key shas (bounded)

    def _verify(self, entry_file: dict) -> Optional[CacheEntry]:
        """Detect corruption: payload must re-hash to the stored digest."""
        try:
            entry = CacheEntry.from_file(entry_file)
        except (KeyError, TypeError, ValueError):
            return None
        recomputed = hashlib.sha256(
            json.dumps(
                entry.payload, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        if recomputed != entry.response_sha256:
            return None
        return entry

    def lookup(
        self, path: str, params: Dict[str, Any]
    ) -> Tuple[Optional[CacheEntry], bool]:
        """(entry, hit). A hit is only valid within TTL for fresh-sources."""
        key_sha, identity = canonical_key(path, params)
        cpath = cache_path(self.root, key_sha)
        entry_file = read_json(cpath)
        if entry_file is None:
            # corruption quarantine: file exists but unreadable JSON
            if os.path.exists(cpath):
                self.quarantine(cpath)
            self.misses += 1
            return None, False
        entry = self._verify(entry_file)
        if entry is None:
            self.quarantine(cpath)
            self.misses += 1
            return None, False
        ttl = CACHE_TTL_MS.get(path, 0)
        if ttl is not None and (self.now_ms() - entry.fetched_at_ms) > ttl:
            self.misses += 1
            return None, False
        if not entry.complete:
            self.misses += 1
            return None, False
        self.hits += 1
        os.utime(cpath, None)  # LRU touch
        return entry, True

    def store(
        self,
        path: str,
        params: Dict[str, Any],
        payload: Any,
        complete: bool,
    ) -> CacheEntry:
        key_sha, identity = canonical_key(path, params)
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        entry = CacheEntry(
            identity=identity,
            path=path,
            params=params,
            fetched_at_ms=self.now_ms(),
            response_sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            payload=payload,
            complete=complete,
        )
        atomic_write_json(cache_path(self.root, key_sha), entry.as_file())
        self.enforce_budget()
        return entry

    def quarantine(self, cpath: str) -> None:
        self.quarantines += 1
        qpath = cpath + f".quarantine.{self.now_ms()}"
        try:
            os.replace(cpath, qpath)
        except OSError:
            pass

    def enforce_budget(self) -> int:
        """LRU eviction down to 500 MiB. Returns bytes removed."""
        cdir = os.path.join(self.root, CACHE_DIR_NAME)
        try:
            names = [
                n for n in os.listdir(cdir) if n.endswith(".json")
            ]
        except FileNotFoundError:
            return 0
        stat = []
        total = 0
        for name in names:
            full = os.path.join(cdir, name)
            try:
                st = os.stat(full)
            except OSError:
                continue
            stat.append((st.st_atime, st.st_size, full))
            total += st.st_size
        removed = 0
        stat.sort()  # oldest access first
        while total > CACHE_MAX_BYTES and stat:
            _, size, full = stat.pop(0)
            try:
                os.remove(full)
                total -= size
                removed += size
                self.evictions += 1
                self._evicted_recent.append(os.path.basename(full)[:-5])
                if len(self._evicted_recent) > 2000:
                    del self._evicted_recent[:1000]
            except OSError:
                continue
        return removed

    def was_evicted(self, key_sha: str) -> bool:
        """True once for a key whose entry was LRU-evicted (lets the
        caller log an honest eviction_refetch event on re-download)."""
        if key_sha in self._evicted_recent:
            self._evicted_recent.remove(key_sha)
            return True
        return False

    def disk_bytes(self) -> int:
        cdir = os.path.join(self.root, CACHE_DIR_NAME)
        try:
            return sum(
                os.path.getsize(os.path.join(cdir, n))
                for n in os.listdir(cdir)
                if n.endswith(".json")
            )
        except FileNotFoundError:
            return 0

    def stats(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "quarantines": self.quarantines,
            "disk_bytes": self.disk_bytes(),
            "max_bytes": CACHE_MAX_BYTES,
        }
