"""A9-F feasibility audit common library (read-only; NO strategy PnL computed).

Loads the frozen snapshot calendar and the frozen SEC PIT store, constructs the
declared decision clocks, and exposes the canonical PIT bridge
(research/assets/stocks/pit_conditioning.py) for feature build-through.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
import sys

import numpy as np

WORKTREE = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5/d2-a9-feasibility"
)
sys.path.insert(0, str(WORKTREE))

STAGING = Path(
    "/Users/hoangminhlong/.worktrees-placeholder"
)  # overwritten below
STAGING = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging")
SEC_STAGING = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5/p0-a3-data/.staging_sec"
)

from research.data_fusion.models import NormalizedRecord  # noqa: E402
from research.assets.stocks.pit_conditioning import (  # noqa: E402
    aggregate_sector_asof,
    conditioning_panel,
    session_gate_utc,
)

SECTORS = ("XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY")

FOLDS = [
    ("S0_FOLD_1", date(2018, 4, 4), date(2020, 9, 1)),
    ("S0_FOLD_2", date(2020, 9, 10), date(2023, 2, 9)),
    ("S0_FOLD_3", date(2023, 2, 17), date(2025, 7, 24)),
]
S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 31)

FIELDS_NEEDED = (
    "us-gaap:Assets",
    "us-gaap:AssetsCurrent",
    "us-gaap:CashAndCashEquivalentsAtCarryingValue",
    "dei:EntityPublicFloat",
    "us-gaap:LiabilitiesAndStockholdersEquity",
)

# ---------------------------------------------------------------- calendar ---

def load_spy_calendar() -> list[date]:
    d = json.loads((STAGING / "SPY_none_p1.json").read_text())
    dts = sorted(v["datetime"] for v in d["values"])
    return [datetime.strptime(x, "%Y-%m-%d").date() for x in dts]


def load_close(sym: str, path: str = "_all_p1") -> dict[date, float]:
    d = json.loads((STAGING / f"{sym}{path}.json").read_text())
    out = {}
    for v in d["values"]:
        dt = datetime.strptime(v["datetime"], "%Y-%m-%d").date()
        out[dt] = float(v["close"])
    return out


def s0_sessions(cal: list[date]) -> list[date]:
    return [d for d in cal if S0_START <= d <= S0_END]


def fold_sessions(s0: list[date]) -> dict[str, list[date]]:
    out = {}
    for fid, a, b in FOLDS:
        out[fid] = [d for d in s0 if a <= d <= b]
    return out


def quarterly_clock(folds: dict[str, list[date]], step: int = 63, max_offset: int = 567):
    """Per-fold reseeded clock: offsets 0, step, ..., <= max_offset."""
    ticks = {}
    for fid, sessions in folds.items():
        ticks[fid] = [sessions[i] for i in range(0, len(sessions), step) if i <= max_offset]
    return ticks


def global_clock(s0: list[date], step: int = 42):
    """Global grid over S0 from offset 0, every `step` sessions."""
    return [s0[i] for i in range(0, len(s0), step)]


def session_at(cal: list[date], tick: date, back: int) -> date:
    """SPY session exactly `back` sessions before `tick` on the frozen calendar."""
    idx = cal.index(tick)
    return cal[idx - back]


# --------------------------------------------------------------- SEC store ---

def iter_sec_records(fields=None):
    """Stream pit_records.jsonl, yielding dicts for the wanted fields only."""
    with open(SEC_STAGING / "pit_records.jsonl", "r") as fh:
        for line in fh:
            obj = json.loads(line)
            if fields is not None and obj["field"] not in fields:
                continue
            yield obj


def to_normalized(obj: dict) -> NormalizedRecord:
    return NormalizedRecord(
        source_id=obj["source_id"],
        dataset_id=obj["dataset_id"],
        entity_id=obj["entity_id"],
        field=obj["field"],
        value=obj["value"],
        unit=obj["unit"],
        event_time_utc=datetime.fromisoformat(obj["event_time_utc"]),
        available_time_utc=datetime.fromisoformat(obj["available_time_utc"]),
        effective_time_utc=(
            datetime.fromisoformat(obj["effective_time_utc"])
            if obj["effective_time_utc"] is not None
            else None
        ),
        vintage_time_utc=datetime.fromisoformat(obj["vintage_time_utc"]),
        retrieved_time_utc=datetime.fromisoformat(obj["retrieved_time_utc"]),
        raw_path=obj["raw_path"],
        raw_sha256=obj["raw_sha256"],
        license_id=obj["license_id"],
        entitlement_id=obj["entitlement_id"],
        normalizer_version=obj["normalizer_version"],
    )


def load_panel_sectors() -> dict[str, str]:
    """entity_id -> sector from the frozen 410-filer panel."""
    panel = json.loads((SEC_STAGING / "panel.json").read_text())
    out = {}
    for sector, filers in panel["panel"].items():
        for f in filers:
            out[f"CIK{f['cik']:010d}"] = sector
    return out


def store_sha256() -> str:
    h = hashlib.sha256()
    with open(SEC_STAGING / "pit_records.jsonl", "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ panels ---

def build_panel(records_by_field: dict[str, list], filer_sectors, sessions, field, gap):
    return conditioning_panel(
        records_by_field[field],
        filer_sectors=filer_sectors,
        sessions=sorted(set(sessions)),
        field=field,
        max_filing_gap_days=gap,
    )


def pre_s0_fractions(records_by_field, filer_sectors):
    """Recompute packet-census 'pre-S0 availability' per sector: fraction of
    panel filers with >=1 gated record available strictly before S0 start."""
    gate = session_gate_utc(S0_START)
    out = {}
    for field, recs in records_by_field.items():
        per_sector = {s: [0, 0] for s in SECTORS}
        seen = {}
        for r in recs:
            if r.available_time_utc < gate:
                seen[r.entity_id] = True
        for ent, sec in filer_sectors.items():
            if sec in per_sector:
                per_sector[sec][1] += 1
                if seen.get(ent):
                    per_sector[sec][0] += 1
        out[field] = {
            s: (inc / mapped if mapped else 0.0) for s, (inc, mapped) in per_sector.items()
        }
    return out


# ------------------------------------------------------------------ ranks ----

def spearman(xs, ys):
    """Spearman rank correlation with average ranks for ties."""
    def ranks(v):
        order = np.argsort(v, kind="mergesort")
        rk = np.empty(len(v), dtype=float)
        sv = np.asarray(v, dtype=float)[order]
        i = 0
        while i < len(sv):
            j = i
            while j + 1 < len(sv) and sv[j + 1] == sv[i]:
                j += 1
            rk[order[i : j + 1]] = (i + j) / 2.0 + 1.0
            i = j + 1
        return rk

    rx, ry = ranks(xs), ranks(ys)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    if denom == 0:
        return float("nan")
    return float((rx * ry).sum() / denom)


def rank_dict(values: dict, reverse: bool):
    """rank 1 = most extreme per `reverse` (reverse=True: largest value -> rank 1)."""
    keys = sorted(values)
    ordered = sorted(keys, key=lambda k: values[k], reverse=reverse)
    # ties: identical values get identical (average) rank
    out = {}
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and values[ordered[j + 1]] == values[ordered[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in ordered[i : j + 1]:
            out[k] = avg
        i = j + 1
    return out


def hysteresis_book(rank_series: dict, seed_ticks, K=3):
    """The declared 3+3 hysteresis automaton (shared surface form of A4 arms).

    rank_series: tick -> {sector: rank} with rank 1 = SHORT-most extreme.
    Returns tick -> {'long': frozenset, 'short': frozenset}.
    """
    state_long, state_short = set(), set()
    books = {}
    for tick in sorted(rank_series):
        ranks = rank_series[tick]
        keys = sorted(ranks)
        n = len(ranks)
        k = min(K, n // 3)
        if tick in seed_ticks:
            state_long = {s for s in keys if ranks[s] >= n - k + 1}
            state_short = {s for s in keys if ranks[s] <= k}
            books[tick] = {"long": frozenset(state_long), "short": frozenset(state_short)}
            continue
        # (i) exits
        for s in sorted(state_long):
            r = ranks.get(s)
            if r is None or r <= n - k - 1:
                state_long.discard(s)
                if r is not None and r <= k and len(state_short) < k:
                    state_short.add(s)
        for s in sorted(state_short):
            r = ranks.get(s)
            if r is None or r >= k + 2:
                state_short.discard(s)
                if r is not None and r >= n - k + 1 and len(state_long) < k:
                    state_long.add(s)
        # (ii) entries: FLAT sectors only
        flat = [s for s in keys if s not in state_long and s not in state_short]
        for s in sorted(flat, key=lambda x: (ranks[x], x)):
            if ranks[s] >= n - k + 1 and len(state_long) < k:
                state_long.add(s)
        for s in sorted(flat, key=lambda x: (-ranks[x], x)):
            if ranks[s] <= k and len(state_short) < k:
                state_short.add(s)
        books[tick] = {"long": frozenset(state_long), "short": frozenset(state_short)}
    return books


def top_bottom_book(rank_series: dict, k=3):
    """Fresh 3-long (ranks 1..k ascending) / 3-short (ranks N-k+1..N) book."""
    books = {}
    for tick, ranks in rank_series.items():
        keys = sorted(ranks)
        n = len(keys)
        longs = sorted([s for s in keys if ranks[s] <= k], key=lambda x: (ranks[x], x))[:k]
        shorts = sorted([s for s in keys if ranks[s] >= n - k + 1], key=lambda x: (-ranks[x], x))[:k]
        books[tick] = {"long": frozenset(longs), "short": frozenset(shorts)}
    return books


def basket_changes(books: dict):
    """Membership changes between consecutive ticks."""
    ticks = sorted(books)
    out = []
    for a, b in zip(ticks, ticks[1:]):
        ch = len(books[b]["long"] - books[a]["long"]) + len(books[b]["short"] - books[a]["short"])
        out.append({"from": str(a), "to": str(b), "legs_changed": ch})
    return out


def side_overlap_fraction(books_a: dict, books_b: dict, side: str, min_shared: int = 2):
    """Fraction of common ticks where >= min_shared legs of `side` are shared."""
    ticks = sorted(set(books_a) & set(books_b))
    hits = 0
    for t in ticks:
        shared = len(books_a[t][side] & books_b[t][side])
        if shared >= min_shared:
            hits += 1
    return hits / len(ticks) if ticks else float("nan")
