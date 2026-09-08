"""FOREX-FREE-V2 data authority: replay of the V1 snapshot, H1 grid audit,
DST-correct flatten clock, fold/purge boundaries, D1/S1 boundaries, offline guard.

Cycle FOREX-FREE-V2, lane A3 (PLAN_forex_v2.md section 6 P2 "data, clock and
DST replay" and section 15 "Hard boundaries").  This module REPLAYS existing
evidence with NO new download: the V1 snapshot is reused byte-for-byte.

Authority chain
---------------
* ``research/control/forex_free_v2_run/data_manifest.json``: "V2 reuses the
  authorized FOREX-FREE-V1 snapshot byte-for-byte; NO new download is performed
  in V2 intake".
* ``research/control/forex_free_v1_run/staged_data_manifest.json`` (schema
  ``forex_free_v1_staged_data_manifest_v2``): 156 digest entries per tree
  (``digests_exec2``), staged at W1 f33a32a, ``byte_identical_exec_repro=true``.
  That manifest is the byte-level authority and :func:`replay_staged_manifest`
  re-hashes every entry against the read-only snapshot.
* ``SNAPSHOT_ROOT`` is the FOREX-FREE-V1 integration worktree, READ-ONLY:
  no module may modify, move or copy anything under it, and no data file may
  ever be committed.

Provider timestamp semantics (validated in V1, frozen here)
-----------------------------------------------------------
Twelve Data H1 FX bars are stamped with the bar OPEN instant in UTC (the
committed V1 family modules assert: "a bar timestamped T (bar open)"; bar
bodies cover ``[T, T+1h)``).  Stamps arrive as naive strings and are
interpreted as UTC, never as any local wall clock.

Completed-bar rule (PIT)
------------------------
A bar stamped T is COMPLETED only from T+1h.  A signal computed on completed
bar ``i`` is actionable at bar ``i+1`` open at the earliest (one-event lag);
:func:`next_actionable_index` encodes exactly that.

Last-flat rule (no carry authority exists)
------------------------------------------
Because authoritative rollover/swap financing is UNAVAILABLE_FAIL_CLOSED,
every position must be flat strictly before the 17:00 America/New_York daily
rollover.  :func:`last_flat_bar_index` locates the H1 bar stamped 16:00
America/New_York on the entry date (DST-correct via :mod:`zoneinfo`); exiting
at that bar's OPEN is the 16:00 New York instant itself -- one full hour
before the rollover, so flatness never depends on bar-close semantics.  In UTC
the stamp maps to 21:00Z in EST weeks (UTC-5) and 20:00Z in EDT weeks (UTC-4).
The mapping depends ONLY on the New York offset: the EU transitions
(Europe/London / CET) provably do not alter it, including inside the brief
EU/US desync windows (US on DST while EU is not, and vice versa).

H1 grid audit
-------------
:func:`h1_grid_audit` classifies every hourly grid position between the first
and last observed bar of one pair against the frozen V1 trading-week window
(open Sunday 21:00 America/New_York, close Friday 16:00 America/New_York,
half-open ``[open, close)``, DST-correct via
:class:`research.assets.forex.sessions.FxWeekConvention`):

* inside-open positions with no bar are MISSING and are enumerated (allowed,
  but each maps to ``NO_TRADE`` fail-closed -- never silent fill-forward);
* weekend/closed positions are classified separately and NEVER count as
  missing (the provider emits known stale out-of-session bars, which V1
  already classified and excluded by the calendar rule).

Boundaries
----------
* :func:`d1_never_in_scored` -- scored datasets may come only from canonical
  ``*_1h_*`` window files; D1 is CONTEXT_ONLY, H4/TRUNCATED are fail-closed.
* :func:`s1_boundary_assert` -- S1 (stage 1) is SEALED_UNTOUCHED: no module
  may list, open, hash or copy anything under an S1/stage-1 area.

Offline guard
-------------
This module performs no network I/O and imports no HTTP client anywhere.
:func:`no_network_guard` additionally makes ACCIDENTAL network use fail
closed: while active it monkeypatches the :mod:`socket` chokepoints
(``socket.socket``, ``create_connection``, ``getaddrinfo``, ``gethostbyname``)
so that any client -- requests, urllib, httpx all funnel through them --
raises :class:`NetworkAccessForbidden` before any syscall.  The guard is
engaged explicitly (tests, replay entry points); it is not auto-installed at
import time because a process-global monkeypatch must never leak into
unrelated suites.  :func:`assert_offline_source` statically re-checks this
file's own source for forbidden HTTP-client imports.
"""

from __future__ import annotations

import contextlib
import datetime as _dt
import hashlib
import json
import os
import re
from typing import Any, Iterable, Sequence

from research.assets.forex.sessions import (
    DEFAULT_FX_WEEK_CONVENTION,
    local_wall_to_utc,
    weekly_close_utc,
    weekly_open_utc,
)

__all__ = [
    "SNAPSHOT_ROOT",
    "V2_DATA_SUBDIR",
    "SNAPSHOT_DATA_ROOT",
    "STAGED_MANIFEST_RELPATH",
    "MISSING_BAR_NO_TRADE",
    "NO_TRADE_SENTINEL",
    "StagedManifestReplayError",
    "MissingBarNoTradeError",
    "DataClassificationError",
    "S1BoundaryViolation",
    "NetworkAccessForbidden",
    "replay_staged_manifest",
    "no_network_guard",
    "assert_offline_source",
    "h1_grid_audit",
    "next_actionable_index",
    "last_flat_bar_index",
    "fold_boundaries",
    "purge_ok",
    "d1_never_in_scored",
    "is_s1_path",
    "s1_boundary_assert",
    "flat_bar_instant_utc",
]

# --- authority constants ------------------------------------------------------ #
# READ-ONLY FOREX-FREE-V1 integration tree.  Never modify, move or copy anything
# under it; never commit any file under its data_raw/ subtree.
SNAPSHOT_ROOT = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v1/integration"
# V2 reuses the V1 snapshot byte-for-byte: td_loader.load_pair_h1(pair, data_root)
# joins data_root + "forex_free_v1", so the V1 data root plugs straight in.
V2_DATA_SUBDIR = "forex_free_v1"
SNAPSHOT_DATA_ROOT = os.path.join(SNAPSHOT_ROOT, "data_raw")
STAGED_MANIFEST_RELPATH = os.path.join(
    "research", "control", "forex_free_v1_run", "staged_data_manifest.json"
)

# <repo>/research/assets/forex_free_v2/data_authority.py -> <repo>
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_MANIFEST_PATH = os.path.join(_REPO_ROOT, STAGED_MANIFEST_RELPATH)

NEW_YORK_ZONE = "America/New_York"

MISSING_BAR_NO_TRADE = "MISSING_BAR_NO_TRADE"
NO_TRADE_SENTINEL = "NO_TRADE_FAIL_CLOSED"

_UTC = _dt.timezone.utc


# --- errors -------------------------------------------------------------------- #
class StagedManifestReplayError(RuntimeError):
    """Fail-closed: the staged manifest did not replay byte-for-byte.

    Carries the full structured ``results`` mapping as ``.results`` so the
    evidence of a failed replay is never lost.
    """

    def __init__(self, message: str, results: dict) -> None:
        super().__init__(message)
        self.results = results


class MissingBarNoTradeError(ValueError):
    """A required bar (e.g. the 16:00 New York flatten bar) is absent.

    Per the frozen rule, a missing required bar means NO_TRADE -- never a
    fill-forward, never a fabricated bar.
    """


class DataClassificationError(ValueError):
    """A dataset outside the H1 research classification entered a scored path."""


class S1BoundaryViolation(RuntimeError):
    """A path under the SEALED_UNTOUCHED S1/stage-1 area was about to be touched."""


class NetworkAccessForbidden(RuntimeError):
    """Raised while the offline guard is active and network use is attempted."""


# --- stamp parsing (provider semantics frozen here) ---------------------------- #
def parse_stamp(value: Any, field: str = "stamp") -> _dt.datetime:
    """Parse a provider bar stamp into an aware UTC instant.

    Accepts ``"YYYY-MM-DD HH:MM:SS"`` (Twelve Data native, naive => UTC),
    ISO-8601 strings, or aware datetimes (converted to UTC).  Naive stamps are
    UTC by provider semantics -- never by local-wall guesswork.
    """
    if isinstance(value, _dt.datetime):
        moment = value
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=_UTC)
        return moment.astimezone(_UTC)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}: malformed stamp {value!r}")
    text = value.strip().replace(" ", "T")
    try:
        moment = _dt.datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field}: malformed stamp {value!r}: {exc}") from exc
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=_UTC)
    return moment.astimezone(_UTC)


def _require_rows(pair_rows: Sequence[Any]) -> None:
    if not isinstance(pair_rows, Sequence) or isinstance(pair_rows, (str, bytes)):
        raise ValueError("pair_rows must be a sequence of bar dicts")
    for i, row in enumerate(pair_rows):
        if not isinstance(row, dict) or "datetime" not in row:
            raise ValueError(f"pair_rows[{i}]: bar dict with 'datetime' required")


# --- staged manifest replay ----------------------------------------------------- #
def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replay_staged_manifest(
    manifest_path: str | None = None,
    snapshot_root: str = SNAPSHOT_ROOT,
) -> dict:
    """Re-hash EVERY entry of ``digests_exec2`` against the read-only snapshot.

    The staged manifest is the V1 W1 byte-level authority (156 entries per
    tree).  Each listed relative path is resolved under ``snapshot_root`` and
    sha256-hashed; per-file evidence (expected vs observed digest, byte size,
    status) is collected for every entry.

    Fail-closed: any mismatch or missing file raises
    :class:`StagedManifestReplayError` carrying the full results -- a caller
    can never receive a pass-looking return while a digest disagrees.
    """
    path = manifest_path or DEFAULT_MANIFEST_PATH
    with open(path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    digests = manifest.get("digests_exec2")
    if not isinstance(digests, dict) or not digests:
        raise ValueError(f"{path}: no digests_exec2 map")
    repro = manifest.get("digests_repro2")
    files: list[dict] = []
    matched = mismatches = missing = 0
    repro_disagreements = 0
    for rel in sorted(digests):
        expected = digests[rel]
        s1_boundary_assert(rel)  # defense in depth: manifest entries stay out of S1
        full = os.path.join(snapshot_root, rel)
        entry: dict[str, Any] = {
            "path": rel,
            "expected_sha256": expected,
            "status": None,
        }
        if repro is not None and rel in repro and repro[rel] != expected:
            repro_disagreements += 1
        if not os.path.exists(full):
            entry["status"] = "MISSING"
            missing += 1
        else:
            observed = _sha256_file(full)
            entry["observed_sha256"] = observed
            entry["bytes"] = os.path.getsize(full)
            if observed == expected:
                entry["status"] = "MATCH"
                matched += 1
            else:
                entry["status"] = "MISMATCH"
                mismatches += 1
        files.append(entry)
    checked = len(digests)
    results = {
        "schema": "forex_free_v2_staged_manifest_replay_v1",
        "manifest_path": os.path.abspath(path),
        "manifest_schema": manifest.get("schema"),
        "manifest_staged_utc": manifest.get("staged_utc"),
        "W1": manifest.get("W1"),
        "byte_identical_exec_repro_declared": manifest.get("byte_identical_exec_repro"),
        "exec_vs_repro_disagreements": repro_disagreements,
        "snapshot_root": os.path.abspath(snapshot_root),
        "checked": checked,
        "matched": matched,
        "mismatches": mismatches,
        "missing": missing,
        "fail_closed_ok": mismatches == 0 and missing == 0 and checked == matched,
        "files": files,
    }
    if mismatches or missing:
        raise StagedManifestReplayError(
            f"STAGED_MANIFEST_REPLAY_FAILED: checked={checked} matched={matched} "
            f"mismatches={mismatches} missing={missing}",
            results,
        )
    return results


# --- offline guard --------------------------------------------------------------- #
_GUARDED_SOCKET_ATTRS = (
    "socket",
    "create_connection",
    "getaddrinfo",
    "gethostbyname",
    "gethostbyname_ex",
)

_OFFLINE_SOURCE_FORBIDDEN = re.compile(
    r"^\s*(?:import|from)\s+(?:requests|urllib|httpx|aiohttp|httplib2)\b",
    re.MULTILINE,
)


def no_network_guard():
    """Context manager: while active, any network use fails closed.

    Monkeypatch approach (documented per mission): the guard replaces
    ``socket.socket`` (every TCP client must construct one), plus
    ``socket.create_connection``, ``socket.getaddrinfo``,
    ``socket.gethostbyname`` and ``socket.gethostbyname_ex`` with raisers of
    :class:`NetworkAccessForbidden`.  requests/urllib/httpx/aiohttp all
    funnel through these chokepoints, so an accidental download attempt dies
    in-process before any syscall.  Originals are restored on exit, including
    on exception.
    """
    import socket

    @contextlib.contextmanager
    def _guard():
        originals = {name: getattr(socket, name) for name in _GUARDED_SOCKET_ATTRS}

        def _deny(name):
            def _raised(*_args, **_kwargs):
                raise NetworkAccessForbidden(
                    f"NETWORK_FORBIDDEN: {name} called while the FOREX-FREE-V2 "
                    "no-network guard is active (replay is download-free by design)"
                )

            return _raised

        try:
            for name in _GUARDED_SOCKET_ATTRS:
                setattr(socket, name, _deny(name))
            yield
        finally:
            for name, original in originals.items():
                setattr(socket, name, original)

    return _guard()


def assert_offline_source(source_path: str | None = None) -> True:
    """Statically assert a module source imports no HTTP client.

    Applied to this module itself (default): any ``import requests|urllib|
    httpx|aiohttp|httplib2`` line raises -- the replay must stay download-free
    by construction, not merely by discipline.
    """
    path = source_path or os.path.abspath(__file__)
    with open(path, "r", encoding="utf-8") as handle:
        source = handle.read()
    hit = _OFFLINE_SOURCE_FORBIDDEN.search(source)
    if hit:
        raise AssertionError(
            f"OFFLINE_SOURCE_VIOLATION: {path} imports an HTTP client ({hit.group(0)!r})"
        )
    return True


# --- H1 grid audit ---------------------------------------------------------------- #
def _weekly_open_windows(first: _dt.datetime, last: _dt.datetime) -> list[tuple[_dt.datetime, _dt.datetime]]:
    """Half-open weekly ``[open, close)`` UTC windows covering [first, last]."""
    convention = DEFAULT_FX_WEEK_CONVENTION
    day = convention.week_open_day_for(first.astimezone(
        _dt.timezone.utc).date())  # week_open_day_for is date-based; Sunday anchor
    windows = []
    while True:
        open_i = weekly_open_utc(day, convention)
        if open_i > last:
            break
        close_i = weekly_close_utc(day, convention)
        if close_i > first:
            windows.append((open_i, close_i))
        day = day + _dt.timedelta(days=7)
    if not windows:
        raise ValueError("no weekly open window overlaps the observed bar range")
    return windows


def h1_grid_audit(pair_rows: Sequence[dict], tz_ny: str = NEW_YORK_ZONE) -> dict:
    """Classify every H1 grid position of one pair: present / missing / weekend.

    ``pair_rows`` are bars as loaded by ``td_loader.load_pair_h1`` (stamps are
    bar-open UTC instants).  The frozen V1 weekly window (Sun 21:00 New York
    open -> Fri 16:00 New York close, half-open, DST-correct) decides which
    hourly grid positions are inside market-open hours.

    Returns structured evidence:

    * ``n_bars`` / ``first`` / ``last`` / ``duplicates`` (duplicates must be 0);
    * ``inside_open_missing`` -- every hourly open-grid position inside the
      weekly window with no bar, each mapped to the ``NO_TRADE_FAIL_CLOSED``
      sentinel (missing bars are ALLOWED but enumerated, never fill-forward);
    * ``out_of_session_present`` -- bars stamped outside the window (known
      stale weekend/holiday bars, V1-classified): reported separately, NEVER
      counted as missing;
    * ``closed_positions_absent`` -- out-of-window grid positions with no bar
      (the weekend gap; not an anomaly).
    """
    from research.assets.forex.sessions import require_zone_name

    require_zone_name(tz_ny)
    _require_rows(pair_rows)
    stamps = [parse_stamp(row["datetime"], f"pair_rows[{i}].datetime")
              for i, row in enumerate(pair_rows)]
    duplicates = len(stamps) - len(set(stamps))
    non_hour_aligned = sum(1 for t in stamps if (t.minute, t.second, t.microsecond) != (0, 0, 0))
    if not stamps:
        return {
            "n_bars": 0, "first": None, "last": None, "duplicates": 0,
            "non_hour_aligned": 0, "inside_open_total": 0, "inside_open_present": 0,
            "inside_open_missing": 0, "missing_inside_open": [],
            "out_of_session_present": 0, "closed_positions_absent": 0,
            "convention": _convention_note(),
        }
    present = set(stamps)
    first, last = min(stamps), max(stamps)
    windows = _weekly_open_windows(first, last)
    missing_inside_open: list[dict] = []
    inside_open_total = inside_open_present = 0
    out_of_session_present = closed_absent = 0
    hour = _dt.timedelta(hours=1)
    w_idx = 0
    t = first
    while t <= last:
        while w_idx < len(windows) and t >= windows[w_idx][1]:
            w_idx += 1
        in_open = w_idx < len(windows) and t >= windows[w_idx][0]
        if in_open:
            inside_open_total += 1
            if t in present:
                inside_open_present += 1
            else:
                missing_inside_open.append(
                    {"stamp_utc": _iso(t), "action": NO_TRADE_SENTINEL}
                )
        elif t in present:
            out_of_session_present += 1
        else:
            closed_absent += 1
        t = t + hour
    return {
        "n_bars": len(stamps),
        "first": _iso(first),
        "last": _iso(last),
        "duplicates": duplicates,
        "non_hour_aligned": non_hour_aligned,
        "inside_open_total": inside_open_total,
        "inside_open_present": inside_open_present,
        "inside_open_missing": len(missing_inside_open),
        "missing_inside_open": missing_inside_open,
        "out_of_session_present": out_of_session_present,
        "closed_positions_absent": closed_absent,
        "convention": _convention_note(),
    }


def _convention_note() -> dict:
    return {
        "weekly_window": "Sun 21:00 America/New_York -> Fri 16:00 America/New_York "
                         "(half-open [open, close), DST-correct via zoneinfo; V1 convention)",
        "stamp_semantics": "bar-open UTC (V1-validated provider semantics)",
        "missing_bar_rule": "missing inside-open bar => NO_TRADE fail-closed; never fill-forward",
    }


def _iso(moment: _dt.datetime) -> str:
    return moment.astimezone(_UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- completed-bar rule and the last-flat clock ------------------------------------- #
def next_actionable_index(i: int) -> int:
    """Index of the first bar on which a signal from completed bar ``i`` may act.

    Completed-bar rule: bar ``i`` (open-stamped T) is complete only from
    T+1h, so its signal is actionable at bar ``i+1`` OPEN at the earliest
    (one-event lag).  Fail-closed on non-integer or negative indices.
    """
    if isinstance(i, bool) or not isinstance(i, int) or i < 0:
        raise ValueError(f"next_actionable_index: completed-bar index must be an int >= 0, got {i!r}")
    return i + 1


def flat_bar_instant_utc(entry_date: Any, tz_ny: str = NEW_YORK_ZONE) -> _dt.datetime:
    """Exact UTC instant of ``16:00`` New York wall time on ``entry_date``.

    DST-correct via zoneinfo through ``local_wall_to_utc`` (which itself fails
    closed on nonexistent wall times and resolves fall-back ambiguity by the
    earlier instant).  16:00 New York is never in a transition gap or fold, so
    the mapping is unambiguous year-round.
    """
    from research.assets.forex.sessions import require_zone_name

    require_zone_name(tz_ny)
    if isinstance(entry_date, str):
        entry_date = _dt.date.fromisoformat(entry_date)
    if isinstance(entry_date, _dt.datetime):
        entry_date = entry_date.date()
    if not isinstance(entry_date, _dt.date):
        raise ValueError(f"entry_date must be a date or YYYY-MM-DD string, got {entry_date!r}")
    return local_wall_to_utc(tz_ny, _dt.datetime.combine(entry_date, _dt.time(16, 0)))


def last_flat_bar_index(
    rows: Sequence[dict],
    entry_date: Any,
    tz_ny: str = NEW_YORK_ZONE,
) -> int:
    """Index of the H1 bar stamped 16:00 America/New_York on ``entry_date``.

    Exiting at that bar's OPEN is the 16:00 New York instant -- strictly
    before the 17:00 New York rollover -- so the position is guaranteed flat
    before rollover regardless of bar-close semantics.  Raises
    :class:`MissingBarNoTradeError` (sentinel ``MISSING_BAR_NO_TRADE``) when
    that bar is absent: no bar, no trade, no fill-forward.
    """
    target = flat_bar_instant_utc(entry_date, tz_ny)
    _require_rows(rows)
    for i, row in enumerate(rows):
        if parse_stamp(row["datetime"], f"rows[{i}].datetime") == target:
            return i
    raise MissingBarNoTradeError(
        f"{MISSING_BAR_NO_TRADE}: no H1 bar stamped {_iso(target)} "
        f"(16:00 {tz_ny} on {entry_date}); flat-before-rollover exit impossible -> NO_TRADE"
    )


# --- folds and purge ------------------------------------------------------------------ #
def fold_boundaries(
    first_ts: Any,
    last_ts: Any,
    n_folds: int = 3,
) -> list[_dt.datetime]:
    """``n_folds`` chronological UTC fold-start boundaries over the observed range.

    The observed H1 range ``[first_ts, last_ts]`` is split into ``n_folds``
    equal chronological folds; the returned instants are the fold STARTS
    ``[first, first + span/n, ..., first + (n-1)*span/n]`` (fold k spans
    ``[b_k, b_{k+1})`` with ``b_n = last_ts``).  These are the S0 fold anchors
    for leakage-safe scoring (frequency contract: 3 chronological folds).
    """
    start = parse_stamp(first_ts, "first_ts")
    end = parse_stamp(last_ts, "last_ts")
    if isinstance(n_folds, bool) or not isinstance(n_folds, int) or n_folds < 1:
        raise ValueError(f"n_folds must be an int >= 1, got {n_folds!r}")
    if end <= start:
        raise ValueError(f"last_ts {_iso(end)} must be after first_ts {_iso(start)}")
    span = (end - start) / n_folds
    return [start + span * k for k in range(n_folds)]


def purge_ok(entry_ts: Any, fold_start_ts: Any, warmup_hours: float) -> bool:
    """Leakage-safe fold admission: purge entries inside the post-boundary warmup.

    An entry stamped within ``[fold_start, fold_start + warmup_hours)`` would
    score on bars whose warmup window crosses the fold boundary and is
    therefore purged (returns False).  Entries at or after the warmup horizon
    (and entries before the fold start, which belong to an earlier fold) are
    admitted (True).  Fail-closed on naive or malformed timestamps and on a
    negative warmup.
    """
    entry = parse_stamp(entry_ts, "entry_ts")
    start = parse_stamp(fold_start_ts, "fold_start_ts")
    if isinstance(warmup_hours, bool) or not isinstance(warmup_hours, (int, float)) or warmup_hours < 0:
        raise ValueError(f"warmup_hours must be a number >= 0, got {warmup_hours!r}")
    horizon = start + _dt.timedelta(hours=float(warmup_hours))
    return not (start <= entry < horizon)


# --- dataset classification boundaries -------------------------------------------------- #
def _is_canonical_h1_name(name: str) -> bool:
    base = os.path.basename(str(name))
    return (
        "_1h_" in base
        and base.endswith("_a.json")
        and "TRUNCATED" not in base
        and "DUPLICATE" not in base
    )


def d1_never_in_scored(rows_dirnames_or_tags: Iterable[str]) -> list[str]:
    """Guard: scored datasets come only from canonical ``*_1h_*`` files.

    D1 is CONTEXT_ONLY and never enters scored H1 returns; H4 and truncated
    windows are UNAVAILABLE_FAIL_CLOSED.  Any name lacking the canonical H1
    window shape (``*_1h_*_a.json``, no TRUNCATED/DUPLICATE marker) raises
    :class:`DataClassificationError`; the validated canonical names are
    returned.  (Final canonical-window selection additionally comes from the
    V1 ``canonical_manifest_final.json``, verified byte-level by the replay.)
    """
    names = list(rows_dirnames_or_tags)
    offenders = [n for n in names if not _is_canonical_h1_name(n)]
    if offenders:
        raise DataClassificationError(
            "SCORED_DATASET_CLASSIFICATION_VIOLATION: scored inputs must be canonical "
            f"*_1h_* window files; offenders={offenders!r} "
            "(D1 context-only / H4+TRUNCATED fail-closed)"
        )
    return names


# --- S1 sealed-area boundary -------------------------------------------------------------- #
_S1_SEALED_PREFIXES = ("s1", "stage-1", "stage1", "stage_1")


def is_s1_path(path: str) -> bool:
    """True when ``path`` lies under an S1/stage-1 (SEALED_UNTOUCHED) area.

    Matches case-insensitively on whole path components equal to or prefixed
    by the sealed names, on both POSIX and Windows separators.
    """
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"path must be a non-empty string, got {path!r}")
    normalized = path.replace("\\", "/")
    for component in normalized.split("/"):
        lowered = component.strip().lower()
        if lowered.startswith(_S1_SEALED_PREFIXES):
            return True
    return False


def s1_boundary_assert(path: str) -> str:
    """Assert ``path`` is NOT under any S1/stage-1 area; return its absolute form.

    S1 is SEALED_UNTOUCHED (V1 state, carried into V2): no module may list,
    open, hash or copy anything under it.  Raises :class:`S1BoundaryViolation`
    otherwise -- callers must invoke this before any file operation on a
    path whose provenance is not hardcoded.
    """
    if is_s1_path(path):
        raise S1BoundaryViolation(
            f"S1_BOUNDARY_VIOLATION: {path!r} is under the SEALED_UNTOUCHED "
            "S1/stage-1 area; listing/opening/hashing/copying it is forbidden"
        )
    return os.path.abspath(path)
