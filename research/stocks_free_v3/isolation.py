"""S0/S1 isolation: every S1 path or date access is denied, fail-closed.

Owner: lane A3, STOCKS-FREE-V3 P1 (PLAN_stocks.md section 9 A3, deliverable 3
and section 4.1 "Revalidation may not expose S1 returns").

Contract
--------
* :class:`S1Seal` denies (path-level) any path that embeds an ``s1`` path
  segment, an ``s1_``/``s1-`` file prefix, a ``YYYY-MM`` month token inside
  the sealed range, or an exact sealed boundary date token — in the style of
  the V2 harness ``s1_denied`` — and denies (date-level) any calendar date
  inside the sealed S1 window 2025-08-01..2026-07-31.
* :class:`S0WindowPolicy` states the positive rule: a research read window is
  allowed only when it lies fully inside S0 (2018-04-04..2025-07-31).  Warmup
  dates are not S1 (the seal does not deny them) but are not S0 read windows
  either; both facts are representable and tested.
* :class:`SealedSnapshotReader` is the ONLY filesystem entry of this lane for
  bar payloads: it refuses sealed paths, verifies the pin sha256 of a file
  BEFORE parsing it, and truncates returned rows to the requested window,
  which itself must be S0-bounded.  A file that legitimately contains
  post-S0 rows (the shared snapshot does) therefore cannot leak an
  S1-dated observation through this lane: the returned frame never contains
  a date >= S1 start, and asking for one raises :class:`S1SealError`.

The tests for this module operate on SYNTHETIC paths and fixtures; real S1
data is never opened by this lane.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from research.assets.common.contracts import canonical_json
from research.stocks_free_v3.authority import (
    S0_END,
    S0_START,
    S1_END,
    S1_START,
    SPLIT_PROVENANCE_DATES,
    SPLIT_SYMBOLS,
    SNAPSHOT_PINS,
    sha256_file,
)

__all__ = [
    "S0_END",
    "S0_START",
    "S1_END",
    "S1_START",
    "S0WindowPolicy",
    "S1Seal",
    "S1SealError",
    "SealedSnapshotReader",
]

_DATE_TOKEN = re.compile(r"(?<!\d)(\d{4})-?(\d{2})-?(\d{2})(?!\d)")
_MONTH_TOKEN = re.compile(r"(?<!\d)(\d{4})-(\d{2})(?!\d)")


class S1SealError(PermissionError):
    """Raised when a research path/window touches the sealed S1."""


def _require_date(value: object, name: str) -> date:
    if isinstance(value, bool) or not isinstance(value, date):
        raise ValueError(f"{name} must be a datetime.date, got {type(value).__name__}")
    return value


@dataclass(frozen=True)
class S1Seal:
    """The sealed S1 window with path-level and date-level denial.

    ``denies_path`` mirrors the V2 harness ``s1_denied`` semantics: an exact
    ``s1``/``S1`` path segment, an ``s1_``/``s1-`` filename prefix, any
    ``YYYY-MM`` month token whose month intersects the sealed range, or an
    exact sealed boundary date token (ISO or compact) inside the path.
    ``denies_date`` is the date-level twin: True exactly for dates inside
    ``[s1_start, s1_end]``.
    """

    s1_start: date
    s1_end: date

    def __post_init__(self) -> None:
        _require_date(self.s1_start, "s1_start")
        _require_date(self.s1_end, "s1_end")
        if self.s1_end < self.s1_start:
            raise ValueError("s1_end precedes s1_start")

    # -- date-level --------------------------------------------------------- #
    def denies_date(self, day: date) -> bool:
        """True exactly when ``day`` lies inside the sealed S1 window."""
        _require_date(day, "day")
        return self.s1_start <= day <= self.s1_end

    def require_unsealed_date(self, day: date) -> date:
        if self.denies_date(day):
            raise S1SealError(
                f"SEALED_WINDOW denial for date {day.isoformat()}: inside the "
                f"sealed S1 range [{self.s1_start.isoformat()}, "
                f"{self.s1_end.isoformat()}]"
            )
        return day

    # -- path-level ---------------------------------------------------------- #
    _SEALED_SEGMENT_PREFIXES = ("s1_", "s1-", "s1.")

    def _sealed_months(self) -> list[tuple[int, int]]:
        y, m = self.s1_start.year, self.s1_start.month
        out = []
        while (y, m) <= (self.s1_end.year, self.s1_end.month):
            out.append((y, m))
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        return out

    def denies_path(self, path: str | Path) -> str | None:
        """Denial reason for ``path``, or None when the path is readable.

        S1-shaped markers: an ``s1`` path segment (case-insensitive), a
        segment or filename starting with ``s1_``/``s1-``/``s1.``, any
        ``YYYY-MM`` month token intersecting the sealed range, or an embedded
        date inside the sealed window.  Conservative: a false-positive denial
        is acceptable, a miss is not.
        """
        norm = str(path).replace("\\", "/")
        segments = norm.split("/")
        lowered = [seg.lower() for seg in segments]
        if "s1" in lowered:
            return "path contains an 's1' segment"
        for seg in lowered[:-1]:
            if seg.startswith(self._SEALED_SEGMENT_PREFIXES):
                return f"path contains sealed-prefixed segment {seg!r}"
        filename = segments[-1].lower()
        if filename.startswith(self._SEALED_SEGMENT_PREFIXES):
            return "filename carries an 's1_'/'s1-'/'s1.' sealed prefix"
        for match in _MONTH_TOKEN.finditer(norm):
            token = (int(match.group(1)), int(match.group(2)))
            if token in self._sealed_months():
                return f"month token {match.group(0)} intersects the sealed S1 range"
        for match in _DATE_TOKEN.finditer(norm):
            try:
                found = date(
                    int(match.group(1)), int(match.group(2)), int(match.group(3))
                )
            except ValueError:
                continue
            if self.denies_date(found):
                return (
                    f"embedded date {found.isoformat()} is inside the sealed "
                    f"S1 range [{self.s1_start.isoformat()}, {self.s1_end.isoformat()}]"
                )
        return None

    def check_path(self, path: str | Path) -> Path:
        """Return the path or raise :class:`S1SealError`."""
        reason = self.denies_path(path)
        if reason is not None:
            raise S1SealError(f"SEALED_WINDOW denial for {path}: {reason}")
        return Path(path)

    def definition_digest(self) -> str:
        import hashlib

        payload = {
            "schema": "stocks_free_v3/s1_seal@1",
            "s1": [self.s1_start.isoformat(), self.s1_end.isoformat()],
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class S0WindowPolicy:
    """Positive statement of what a V3 research read window may be.

    A read window is allowed only when BOTH bounds lie inside S0
    (2018-04-04..2025-07-31).  The seal denies S1 dates independently; this
    policy additionally forbids warmup/pre-S0 and post-S1 dates as research
    read windows, so a caller cannot argue "not S1 therefore readable".
    """

    s0_start: date = S0_START
    s0_end: date = S0_END

    def __post_init__(self) -> None:
        _require_date(self.s0_start, "s0_start")
        _require_date(self.s0_end, "s0_end")
        if self.s0_end < self.s0_start:
            raise ValueError("s0_end precedes s0_start")

    def allows_window(self, start: date, end: date) -> bool:
        return self.s0_start <= start <= end <= self.s0_end

    def require_s0_window(self, start: date, end: date) -> tuple[date, date]:
        if not self.allows_window(start, end):
            raise S1SealError(
                f"window {start.isoformat()}..{end.isoformat()} is not fully "
                f"inside S0 [{self.s0_start.isoformat()}, {self.s0_end.isoformat()}]; "
                "V3 research reads are S0-only"
            )
        return start, end


class SealedSnapshotReader:
    """The only bar-payload filesystem entry of the A3 lane.

    Guarantees (all fail-closed, all tested on synthetic fixtures):

    1. the requested path passes the :class:`S1Seal` path-level denial;
    2. the requested window passes the :class:`S0WindowPolicy` (S0-bounded);
    3. when a pin is declared for the file, its sha256 is verified BEFORE the
       payload is parsed;
    4. the returned rows are restricted to the requested window, so a shared
       snapshot file that also contains post-S0 rows cannot leak them here.
    """

    def __init__(
        self,
        staging_root: str | Path,
        *,
        seal: S1Seal,
        policy: S0WindowPolicy,
    ) -> None:
        self._root = Path(staging_root)
        if not self._root.is_dir():
            raise S1SealError(f"snapshot root does not exist: {self._root}")
        self._seal = seal
        self._policy = policy

    @property
    def seal(self) -> S1Seal:
        return self._seal

    @property
    def policy(self) -> S0WindowPolicy:
        return self._policy

    def resolve(self, relpath: str | Path) -> Path:
        """Path-level gate: refuse any S1-shaped path, then anchor under root."""
        self._seal.check_path(relpath)
        candidate = (self._root / relpath).resolve()
        root = self._root.resolve()
        if root != candidate and root not in candidate.parents:
            raise S1SealError(
                f"refusing to escape the snapshot root via {relpath!r}"
            )
        return candidate

    def read_pinned_text(self, relpath: str) -> str:
        """Hash-verified text read of a pinned snapshot file.

        The path must pass the seal and the file must carry a committed pin;
        the sha256 is verified BEFORE a single byte is parsed.
        """
        path = self.resolve(relpath)
        pin = SNAPSHOT_PINS.get(PurePosixPath(str(relpath)).name)
        if pin is None:
            raise S1SealError(
                f"refusing to read unpinned snapshot file {relpath!r}; the V3 "
                "lane only reads files carrying a committed sha256 pin"
            )
        actual = sha256_file(path)
        if actual != pin:
            raise S1SealError(
                f"checksum mismatch for {relpath!r}: pin {pin} != actual {actual}"
            )
        return path.read_text(encoding="utf-8")

    def read_provenance_closes(
        self,
        relpath: str,
        *,
        dates: tuple[str, ...] = SPLIT_PROVENANCE_DATES,
    ) -> dict[str, float]:
        """The pinned corporate-action provenance closes — and nothing else.

        This is the ONLY method that may return a post-S0 observation: the
        two dates bracketing the pinned 2025-12-05 2:1 splits, for the five
        split-symbol files only.  Any other request, symbol, or date fails
        closed.  These closes corroborate the A7-approved split-factor
        provenance; no S1 return series may be formed from them.
        """
        if tuple(dates) != SPLIT_PROVENANCE_DATES:
            raise S1SealError(
                f"provenance read restricted to {SPLIT_PROVENANCE_DATES}, "
                f"got {dates}"
            )
        symbol = PurePosixPath(str(relpath)).name.split("_", 1)[0]
        if symbol not in SPLIT_SYMBOLS:
            raise S1SealError(
                f"provenance closes are restricted to the split symbols "
                f"{SPLIT_SYMBOLS}, got {symbol!r}"
            )
        payload = json.loads(self.read_pinned_text(relpath))
        rows = {
            str(row.get("datetime")): float(row["close"])
            for row in payload.get("values", [])
            if str(row.get("datetime")) in dates
        }
        missing = [d for d in dates if d not in rows]
        if missing:
            raise S1SealError(f"provenance closes missing for {missing} in {relpath!r}")
        return {d: rows[d] for d in dates}

    def load_symbol_file(
        self,
        relpath: str,
        *,
        start: date,
        end: date,
    ) -> dict[str, Any]:
        """Load a pinned snapshot JSON, S0-truncated to ``[start, end]``.

        The window must be a declared S0 window (raise otherwise); rows dated
        after ``end`` — including every sealed S1 row present in the shared
        file — are dropped BEFORE the payload is returned.
        """
        self._policy.require_s0_window(start, end)
        payload = json.loads(self.read_pinned_text(relpath))
        if not isinstance(payload, dict) or not isinstance(payload.get("values"), list):
            raise S1SealError(f"unexpected snapshot payload shape in {relpath!r}")
        kept = [
            row
            for row in payload["values"]
            if start.isoformat() <= str(row.get("datetime", "")) <= end.isoformat()
        ]
        kept.sort(key=lambda row: str(row.get("datetime", "")))
        return {"meta": payload.get("meta"), "status": payload.get("status"), "values": kept}

    def load_symbol_closes(
        self,
        relpath: str,
        *,
        start: date,
        end: date,
    ) -> Mapping[str, float]:
        """S0-truncated ``{ISO date: raw close}`` mapping for one symbol file."""
        loaded = self.load_symbol_file(relpath, start=start, end=end)
        closes: dict[str, float] = {}
        for row in loaded["values"]:
            closes[str(row["datetime"])] = float(row["close"])
        return dict(sorted(closes.items()))
