"""FOREX-NG1 P1 spot series adapter: pinned FX spot daily bars.

Serves the four funded-pair spot series (GBPUSD/USDCAD/AUDUSD/NZDUSD,
Twelve Data ``time_series`` 1day provider format) pinned from the V9
integration staging by this lane's pin manifest:

- ``research/control/forex_ng1_run/p1_spot/spot_pin_manifest.json``
  (committed; raw bytes live untracked in ``data_raw/forex_ng1_spot/``).

Access law (fail-closed everywhere):

1. VERIFY-ON-READ -- every serve re-hashes the pinned file against the
   manifest sha256; a single-byte drift raises ``SpotIntegrityError``
   and nothing is served (never a silent fix).
2. STRICT SCHEMA -- provider payload must carry status=="ok",
   meta.interval=="1day", the expected pair symbol, and bars whose
   ``close`` parses to a finite positive float. Duplicate bar dates are
   STRUCTURALLY REJECTED (unlike the V9 reader, which kept the last
   write: this census proves the pinned bytes carry zero duplicates, so
   the stricter law costs nothing and protects downstream).
3. AUTHORITY GATE -- the channel (Twelve Data, keyed, under the owner's
   existing entitlement) is a DOCUMENTED_CANDIDATE that is
   CANDIDATE_NOT_AUTHORIZED for scored consumption until the owner /
   this cycle's authority lane grants it; ``require_scored_authority``
   reads the committed authority proof and raises unless the recorded
   status is AUTHORIZED. This module never self-promotes authority.

Representation identity (V9 frozen representation, inherited verbatim
from ``research/assets/forex_free_v9/family_common.py`` -- P-12):

- decision instant of calendar day D = 16:00 America/New_York on D,
  DST-correct via zoneinfo (``ny_decision_instant_utc``);
- the decision-instrument close at that instant = the ``close`` of the
  daily bar dated D (provider daily bars aggregate the provider's day;
  V9 consumed exactly this mapping through its scored-phase driver);
- the decision grid = FX 24/5 weekdays within the window, intersected
  across the funded pairs' staged daily calendars (weekend bars exist
  in the provider bytes and are deterministically excluded).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Mapping
from zoneinfo import ZoneInfo

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

#: Committed pin manifest produced by this lane (see module docstring).
DEFAULT_PIN_MANIFEST = os.path.join(
    REPO_ROOT, "research/control/forex_ng1_run/p1_spot/",
    "spot_pin_manifest.json")

#: Untracked pinned raw bytes (data_raw/ is NOT gitignored in this
#: worktree: the raw files stay untracked; only the manifest commits).
DEFAULT_DATA_DIR = os.path.join(REPO_ROOT, "data_raw/forex_ng1_spot")

#: Committed authority proof artifact (the authority gate's source of
#: truth; an owner promotion edits THAT artifact, never this module).
DEFAULT_AUTHORITY_PROOF = os.path.join(
    REPO_ROOT, "research/control/forex_ng1_run/p1_spot/",
    "spot_authority_proof.json")

PIN_MANIFEST_SCHEMA = "forex_ng1_p1_spot_pin_manifest@1"
AUTHORITY_PROOF_SCHEMA = "forex_ng1_p1_spot_authority_proof@1"

#: FOREX-NG1 P1 dispatch census window (the V9 run contract carried
#: 2018-04-04..2025-07-24; NG1 trims the tail per plan section 3).
S0_WINDOW_START = date(2018, 4, 4)
S0_WINDOW_END = date(2025, 4, 30)

FUNDED_PAIRS = ("GBPUSD", "USDCAD", "AUDUSD", "NZDUSD")

NY_TZ = ZoneInfo("America/New_York")
UTC = timezone.utc

_REQUIRED_BAR_FIELDS = ("datetime", "open", "high", "low", "close")


class SpotDataError(Exception):
    """Base: nothing is served on any SpotDataError (fail-closed)."""


class SpotIntegrityError(SpotDataError):
    """Pinned bytes drifted/missing: sha256 verify-on-read failed."""


class SpotStructureError(SpotDataError):
    """Payload is not the pinned provider schema (status/meta/bars)."""


class SpotAuthorityError(SpotDataError):
    """Consumption refused: channel not authorized for this regime."""


# --------------------------------------------------------------------------- #
# integrity primitives
# --------------------------------------------------------------------------- #

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_pin_manifest(path: str = DEFAULT_PIN_MANIFEST) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    if manifest.get("schema") != PIN_MANIFEST_SCHEMA:
        raise SpotStructureError(
            f"pin manifest schema {manifest.get('schema')!r} != "
            f"{PIN_MANIFEST_SCHEMA!r}")
    if not isinstance(manifest.get("files"), dict) or not manifest["files"]:
        raise SpotStructureError("pin manifest carries no files map")
    return manifest


def _manifest_entry(manifest: Mapping, pair: str) -> dict:
    entry = manifest["files"].get(pair)
    if entry is None:
        known = sorted(manifest["files"])
        raise SpotIntegrityError(
            f"pair {pair!r} is not pinned (pinned: {known}): "
            "consumption refused (fail-closed)")
    return entry


def _pinned_path(entry: Mapping, pair: str, data_dir: str | None) -> str:
    if data_dir is None:
        path = entry.get("copy_path")
        if not path:
            raise SpotIntegrityError(
                f"pin entry {pair!r} carries no copy_path")
        return path
    return os.path.join(data_dir, entry["file"])


def verify_spot_file(manifest: Mapping, pair: str,
                     data_dir: str | None = None) -> str:
    """Verify-on-read the pinned file for ``pair``; returns its sha256.

    Fail-closed: a missing file or a single-byte drift raises
    SpotIntegrityError and nothing is served.
    """
    entry = _manifest_entry(manifest, pair)
    path = _pinned_path(entry, pair, data_dir)
    if not os.path.exists(path):
        raise SpotIntegrityError(f"pinned file ABSENT: {path}")
    actual = sha256_file(path)
    pinned = entry.get("copy_sha256") or entry.get("source_sha256")
    if actual != pinned:
        raise SpotIntegrityError(
            f"pinned file DRIFTED for {pair}: expected sha256 {pinned}, "
            f"got {actual} ({path}): nothing served (fail-closed)")
    return actual


# --------------------------------------------------------------------------- #
# strict provider-schema parse
# --------------------------------------------------------------------------- #

def _parse_day(s: str) -> date:
    y, m, d = str(s).split("-")
    if len(y) != 4 or len(m) != 2 or len(d) != 2:
        raise SpotStructureError(f"non-ISO bar datetime: {s!r}")
    return date(int(y), int(m), int(d))


def parse_spot_payload(payload: Mapping, pair: str) -> list[dict]:
    """Strict parse of the Twelve Data 1day provider payload.

    Returns bars ascending by date as
    ``[{"date": date, "close": float, "raw": {...}}, ...]``.

    Fail-closed on: non-ok status, non-1day interval, symbol mismatch,
    missing bar fields, unparseable/non-finite/non-positive close,
    duplicate bar dates, non-ISO datetimes.
    """
    if payload.get("status") != "ok":
        raise SpotStructureError(
            f"{pair}: provider status {payload.get('status')!r} != 'ok'")
    meta = payload.get("meta") or {}
    if meta.get("interval") != "1day":
        raise SpotStructureError(
            f"{pair}: meta.interval {meta.get('interval')!r} != '1day'")
    expected_symbol = f"{pair[:3]}/{pair[3:]}"
    if meta.get("symbol") != expected_symbol:
        raise SpotStructureError(
            f"{pair}: meta.symbol {meta.get('symbol')!r} != "
            f"{expected_symbol!r}")
    values = payload.get("values")
    if not isinstance(values, list) or not values:
        raise SpotStructureError(f"{pair}: no bars in payload")

    bars: dict[date, dict] = {}
    storage_order: list[date] = []
    for i, v in enumerate(values):
        if not isinstance(v, Mapping):
            raise SpotStructureError(f"{pair}: bar {i} not an object")
        missing = [k for k in _REQUIRED_BAR_FIELDS if k not in v]
        if missing:
            raise SpotStructureError(
                f"{pair}: bar {i} lacks fields {missing}")
        try:
            day = _parse_day(v["datetime"])
            close = float(v["close"])
        except (TypeError, ValueError) as exc:
            raise SpotStructureError(
                f"{pair}: bar {i} unparseable: {v!r}") from exc
        if not math.isfinite(close) or close <= 0.0:
            raise SpotStructureError(
                f"{pair}: bar {i} close not finite-positive: {v!r}")
        if day in bars:
            raise SpotStructureError(
                f"{pair}: DUPLICATE bar datetime {day.isoformat()} "
                f"(bars {bars[day]['raw']!r} and {v!r}): "
                "fail-closed, nothing served")
        bars[day] = {"date": day, "close": close, "raw": dict(v)}
        storage_order.append(day)

    storage_monotonic_desc = all(
        storage_order[i] > storage_order[i + 1]
        for i in range(len(storage_order) - 1))
    storage_monotonic_asc = all(
        storage_order[i] < storage_order[i + 1]
        for i in range(len(storage_order) - 1))
    if not (storage_monotonic_desc or storage_monotonic_asc):
        raise SpotStructureError(
            f"{pair}: bar storage order is not monotonic "
            f"(provider contract is newest-first): fail-closed")
    return [bars[d] for d in sorted(bars)]


# --------------------------------------------------------------------------- #
# served series
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class SpotSeries:
    pair: str
    bars: int
    first_day: date
    last_day: date
    days: tuple[date, ...]
    closes: Mapping[date, float]
    sha256: str

    def lookup_close(self, day_iso: str) -> dict:
        """Canary-capable lookup: fabricated days MUST return
        found=False, never an inferred value."""
        day = _parse_day(day_iso)
        return {"pair": self.pair, "date": day.isoformat(),
                "found": day in self.closes,
                "close": self.closes.get(day)}

    def window_days(self, start: date, end: date,
                    weekdays_only: bool = True) -> list[date]:
        out = [d for d in self.days
               if start <= d <= end and (d.weekday() < 5 or not weekdays_only)]
        return out


def resolve_spot_series(pair: str,
                        manifest_path: str = DEFAULT_PIN_MANIFEST,
                        data_dir: str | None = DEFAULT_DATA_DIR,
                        ) -> SpotSeries:
    """Verify-on-read then serve the pinned spot series for ``pair``.

    ``data_dir`` overrides where the pinned files live (tests use tmp
    dirs); the FILE NAME always comes from the manifest (never caller
    input), and the sha256 always from the manifest (never the bytes).
    """
    manifest = load_pin_manifest(manifest_path)
    sha = verify_spot_file(manifest, pair, data_dir)
    path = _pinned_path(_manifest_entry(manifest, pair), pair, data_dir)
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    bars = parse_spot_payload(payload, pair)
    days = tuple(b["date"] for b in bars)
    closes = {b["date"]: b["close"] for b in bars}
    return SpotSeries(pair=pair, bars=len(bars), first_day=days[0],
                      last_day=days[-1], days=days, closes=closes,
                      sha256=sha)


def resolve_all_pairs(manifest_path: str = DEFAULT_PIN_MANIFEST,
                      data_dir: str | None = DEFAULT_DATA_DIR,
                      pairs: tuple[str, ...] = FUNDED_PAIRS,
                      ) -> dict[str, SpotSeries]:
    return {p: resolve_spot_series(p, manifest_path, data_dir)
            for p in pairs}


# --------------------------------------------------------------------------- #
# the 16:00-NY decision clock (V9 frozen representation, DST-correct)
# --------------------------------------------------------------------------- #

def ny_decision_instant_utc(day: date) -> datetime:
    """16:00 America/New_York on ``day``, as a UTC datetime.

    Identical semantics to V9 ``family_common.ny_close_ts``: zoneinfo
    resolves the DST offset at that wall-clock instant (fold=0; 16:00
    never falls inside the repeated 01:00-01:59 fall-back hour, so the
    mapping day -> instant is a total, deterministic function).
    """
    return datetime(day.year, day.month, day.day, 16, 0,
                    tzinfo=NY_TZ).astimezone(UTC)


def instant_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def common_weekday_grid(serieses: Mapping[str, SpotSeries],
                        start: date, end: date) -> list[date]:
    """V9 ``build_grid`` law: FX 24/5 weekdays in [start, end]
    intersected across every served pair calendar."""
    common = None
    for pair in sorted(serieses):
        s = {d for d in serieses[pair].days
             if start <= d <= end and d.weekday() < 5}
        common = s if common is None else (common & s)
    return sorted(common) if common else []


# --------------------------------------------------------------------------- #
# authority gate (fail-closed; no self-promotion)
# --------------------------------------------------------------------------- #

def spot_authority_status(proof_path: str = DEFAULT_AUTHORITY_PROOF) -> dict:
    """Read the committed authority proof; return its status block."""
    with open(proof_path, "r", encoding="utf-8") as fh:
        proof = json.load(fh)
    if proof.get("schema") != AUTHORITY_PROOF_SCHEMA:
        raise SpotAuthorityError(
            f"authority proof schema {proof.get('schema')!r} != "
            f"{AUTHORITY_PROOF_SCHEMA!r}")
    block = proof.get("authority_status")
    if not isinstance(block, dict):
        raise SpotAuthorityError("authority proof carries no status block")
    return block


def require_scored_authority(proof_path: str = DEFAULT_AUTHORITY_PROOF,
                             ) -> dict:
    """Scored-consumption gate: raises SpotAuthorityError unless the
    committed proof records scored_consumption == AUTHORIZED.

    The pinned channel currently sits at CANDIDATE_NOT_AUTHORIZED
    (documented candidate; owner decision outstanding), so scored
    consumption through this module is refused by construction.
    Staging/census consumption is allowed; the caller records which
    regime it is operating in.
    """
    block = spot_authority_status(proof_path)
    scored = block.get("scored_consumption")
    if scored != "AUTHORIZED":
        raise SpotAuthorityError(
            f"spot channel scored_consumption={scored!r}: scored "
            "consumption refused (fail-closed; owner/authority-lane "
            "decision recorded in the authority proof, never here)")
    return block
