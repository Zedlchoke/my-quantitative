"""ONE team-name normalization + identity crosswalk for the exec runner
(PAPERDESK-FIXALL-NCAA-V1 W0.1, owner work package 2026-10-21).

ROOT CAUSE THIS REPLACES: `results_fetch.py` compared ESPN abbreviations
(DET/BOS/SA/OKC) against full ledger names (Detroit Pistons / …) with a bare
`!=`, so every NBA bet stayed OPEN forever (runtime audit B1, 2 live stuck
bets on 2026-10-21). Three divergent normalizers existed (`pm_moneyline._norm`,
`wsl_results._norm`, `execute.norm_team`) — two different algorithms.

LAWS
  * `norm()` is THE single normalization (casefold + strip every non
    [a-z0-9] character — byte-identical to the pinned polymarket_source
    norm_name, so the PM lanes keep their exact semantics).
  * Identity resolution goes through the PINNED crosswalk
    (TEAM_NAME_CROSSWALK.csv, sha256 enforced from pins.json —
    BLOCKED_PIN_DRIFT on any drift). Unknown names resolve to NOTHING and the
    caller keeps the bet OPEN + journals an incident: never guess, never
    fuzzy-match.
  * `same_team()` is the ONLY identity comparison the settle path may use.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

CROSSWALK_NAME = "TEAM_NAME_CROSSWALK.csv"

_NORM_RE = re.compile(r"[^a-z0-9]+")
_norm_cache: dict[str, str] = {}
_crosswalk_cache: dict | None = None


class TeamIdentityError(Exception):
    """A name could not be resolved through the pinned crosswalk (fail-closed
    — the caller keeps the bet OPEN and journals; never guesses)."""


def norm(name: str) -> str:
    """THE single team-name normalization (casefold, strip non-alnum)."""
    s = str(name)
    if s not in _norm_cache:
        _norm_cache[s] = _NORM_RE.sub("", s.casefold())
    return _norm_cache[s]


def crosswalk_path() -> Path:
    return Path(__file__).resolve().parent / CROSSWALK_NAME


def _expected_sha() -> str:
    from research.papertrade_exec import load_pins
    pin = load_pins().get("data", {}).get("team_name_crosswalk_csv", {})
    return str(pin.get("sha256", ""))


def load_crosswalk(*, expected_sha: str | None = None,
                   path: Path | None = None) -> dict:
    """{league: {norm(abbr_or_name): canonical_name}} — sha-pinned,
    fail-closed. Cached; tests may inject `path`."""
    global _crosswalk_cache
    if _crosswalk_cache is not None and path is None and \
            expected_sha is None:
        return _crosswalk_cache
    p = Path(path) if path is not None else crosswalk_path()
    body = p.read_bytes()
    want = expected_sha if expected_sha is not None else _expected_sha()
    if want:
        got = hashlib.sha256(body).hexdigest()
        if got != want:
            raise TeamIdentityError(
                f"BLOCKED_PIN_DRIFT: {p.name} sha {got[:12]} != pinned "
                f"{want[:12]}; re-pin required (identity law)")
    table: dict[str, dict[str, str]] = {}
    for row in csv.DictReader(body.decode("utf-8").splitlines()):
        league = row["league"].strip().upper()
        ab = norm(row["provider_abbr"])
        canon = row["canonical_name"].strip()
        if not league or not ab or not canon:
            continue
        slot = table.setdefault(league, {})
        slot[ab] = canon
        slot[norm(canon)] = canon          # full name resolves to itself
    if path is None and expected_sha is None:
        _crosswalk_cache = table
    return table


def reset_cache() -> None:
    global _crosswalk_cache
    _crosswalk_cache = None


def resolve(name: str, league: str) -> str | None:
    """Canonical team id through the pinned crosswalk, or None (unknown —
    the caller keeps OPEN + journals; NEVER a guess). Leagues without a
    crosswalk table (SOCCER/WSL/NCAA-*) resolve a name to itself only when
    it already IS a canonical-looking full name; comparison then happens via
    `norm()` equality on both sides."""
    table = load_crosswalk().get(str(league).upper())
    if not table:
        return str(name).strip()
    n = norm(name)
    if not n:
        return None
    return table.get(n)


def same_team(a: str, b: str, league: str) -> tuple[bool, str]:
    """Identity comparison for the settle path. Returns (ok, reason). Both
    sides MUST resolve (None on either side => not same, with the specific
    reason — fail-closed). Leagues WITHOUT a crosswalk table compare via
    the one normalization (norm equality) — full-name spellings."""
    ra, rb = resolve(a, league), resolve(b, league)
    if ra is None:
        return False, f"team name unresolved in pinned crosswalk: {a!r} " \
                      f"(league {league})"
    if rb is None:
        return False, f"team name unresolved in pinned crosswalk: {b!r} " \
                      f"(league {league})"
    table = load_crosswalk().get(str(league).upper())
    if table:
        same = ra == rb
        how = f"via {ra}" if same else f"{ra!r} != {rb!r}"
    else:
        same = norm(ra) == norm(rb)
        how = "norm equality (no crosswalk table)" if same else \
            f"{ra!r} != {rb!r}"
    return same, (f"{a!r} == {b!r} {how}" if same else
                  f"{a!r} != {b!r} {how}")


def team_count(league: str) -> int:
    table = load_crosswalk().get(str(league).upper(), {})
    return len({v for v in table.values()})
