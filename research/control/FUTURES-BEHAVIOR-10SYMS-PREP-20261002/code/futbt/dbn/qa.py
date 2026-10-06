"""QA layer: SHA256 manifest, gap/duplicate/monotonic-time checks,
crossed-quote statistics, coverage-by-contract report, fail-closed schema
surprise handling.

All checks are descriptive (no strategy logic, no performance selection).
Gap semantics honor the documented Databento convention that ohlcv bars
are SPARSE (no trade -> no bar): a missing minute inside a session is
reported as NO_TRADE_GAP (an inference, not an error); duplicates and
non-monotonic timestamps ARE anomalies.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import spec as S
from .ingest import Bar, ContractRegistry, Ingested, Statistic
from .ohlcv import SessionBar, aggregate_1m_to_session, settlement_series
from .session import (NS, DAILY_RTYPES, SessionMap, SessionKind,
                      build_session_map, session_date_of)

MINUTE_NS = 60 * NS


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_manifest(paths: list[str | Path]) -> dict:
    return {str(Path(p).resolve()): sha256_file(p) for p in sorted(paths, key=str)}


@dataclass
class TimeSeriesCheck:
    raw_symbol: str
    n_records: int
    n_duplicate_ts: int
    duplicate_ts: list[int]
    n_non_monotonic: int       # violations in AS-RECEIVED order (file order)
    first_ts: int
    last_ts: int
    n_no_trade_gaps: int       # missing 1m bars inside a session (inference:
                               # Databento ohlcv is sparse — no trade, no bar)
    no_trade_gap_ts: list[int]

    def ok(self) -> bool:
        return self.n_non_monotonic == 0


def check_bars_time_series(bars: list[Bar], raw_symbol: str,
                           gap_scan: bool = True,
                           max_gap_report: int = 100) -> TimeSeriesCheck:
    ordered = sorted(bars, key=lambda b: b.ts_event)
    seen: dict[int, int] = {}
    for b in ordered:
        seen[b.ts_event] = seen.get(b.ts_event, 0) + 1
    dup_ts = sorted(t for t, n in seen.items() if n > 1)
    # Monotonicity is a property of the AS-RECEIVED order (sorted input is
    # vacuously monotonic and would hide a shuffled/broken export).
    non_mono = sum(1 for i in range(1, len(bars))
                   if bars[i].ts_event < bars[i - 1].ts_event)
    gaps: list[int] = []
    # Minute-gap scan only makes sense at 1m cadence: a 1d/1h series has
    # legitimate multi-minute spacing between bars.
    minute_bars = [b for b in ordered if b.rtype == S.RTYPE_OHLCV_1M]
    if gap_scan and minute_bars:
        by_session: dict = {}
        for b in minute_bars:
            by_session.setdefault(session_date_of(b.ts_event), []).append(b)
        for d, day in sorted(by_session.items()):
            stamps = sorted(b.ts_event for b in day)
            for a, b2 in zip(stamps, stamps[1:]):
                if b2 - a > MINUTE_NS:
                    # missing minutes: sparse no-trade convention (inference)
                    gaps.extend(range(a + MINUTE_NS, b2, MINUTE_NS))
    return TimeSeriesCheck(
        raw_symbol=raw_symbol, n_records=len(ordered),
        n_duplicate_ts=len(dup_ts), duplicate_ts=dup_ts[:max_gap_report],
        n_non_monotonic=non_mono,
        first_ts=ordered[0].ts_event if ordered else 0,
        last_ts=ordered[-1].ts_event if ordered else 0,
        n_no_trade_gaps=len(gaps), no_trade_gap_ts=gaps[:max_gap_report])


@dataclass
class ContractCoverage:
    raw_symbol: str
    instrument_id: int
    n_bars: int
    n_sessions_with_bars: int
    sessions: list[dict] = field(default_factory=list)
    n_negative_price_bars: int = 0
    n_close_only_sessions: int = 0      # settlement exists, no bars
    n_stale_flat_bars: int = 0


def coverage_report(frames: list[Ingested], registry: ContractRegistry,
                    statistics_by_raw: dict | None = None) -> dict:
    """Per-contract coverage: sessions, negative-price bars, stale-flat
    bars, close-only (settlement-without-bars) sessions."""
    stats = statistics_by_raw or {}
    by_raw: dict[str, list[Bar]] = {}
    for f in frames:
        for b in f.bars:
            raw = registry.raw_for(b.instrument_id)
            by_raw.setdefault(raw, []).append(b)
    out: dict[str, ContractCoverage] = {}
    for raw, bars in sorted(by_raw.items()):
        ident = registry.require(raw_symbol=raw)
        # partition by cadence: session classification is cadence-aware and
        # mixing daily + intraday bars in one map is ambiguous (raises)
        bars_daily = [b for b in bars if b.rtype in DAILY_RTYPES]
        bars_intra = [b for b in bars if b.rtype not in DAILY_RTYPES]
        windows: dict = {}
        for chunk in (bars_intra, bars_daily):
            if chunk:
                smap = build_session_map(raw, chunk, registry)
                for d, w in smap.sessions.items():
                    if (d not in windows or w.n_bars > 0
                            or windows[d].n_bars == 0):
                        windows[d] = w
        cov = ContractCoverage(raw_symbol=raw, instrument_id=ident.instrument_id,
                               n_bars=len(bars),
                               n_sessions_with_bars=sum(
                                   1 for w in windows.values() if w.n_bars > 0),
                               sessions=[])
        prev_close = None
        ordered = sorted(bars, key=lambda b: b.ts_event)
        for b in ordered:
            if b.negative():
                cov.n_negative_price_bars += 1
            if b.is_stale_flat(prev_close):
                cov.n_stale_flat_bars += 1
            prev_close = b.close
        settle_dates = {s.session_date for s in stats.get(raw, [])}
        bar_dates = {d.isoformat() for d, w in windows.items() if w.n_bars > 0}
        cov.n_close_only_sessions = len(settle_dates - bar_dates)
        for d in sorted(windows):
            w = windows[d]
            cov.sessions.append({
                "date": d.isoformat(), "kind": w.kind.value,
                "inferred": w.inferred_short, "n_bars": w.n_bars,
                "coverage_ratio": w.coverage_ratio})
        out[raw] = cov
    return out


def qa_report(frames: list[Ingested], registry: ContractRegistry) -> dict:
    """Full QA bundle: manifest, per-contract time checks, coverage,
    crossed-quote stats, settlement-only sessions, unknown-stat-type census,
    roll-window observation (volume/OI migration from statistics)."""
    files = sorted({f.source for f in frames})
    # Monotonicity is a PER-FILE property: pooling several files (e.g. a
    # 1d and a 1m export with overlapping windows) interleaves two valid
    # streams and would report spurious reversals at every file boundary.
    bars_by_file: dict[tuple[str, str], list[Bar]] = {}
    for f in frames:
        for b in f.bars:
            key = (f.source, registry.raw_for(b.instrument_id))
            bars_by_file.setdefault(key, []).append(b)
    from .bbo import crossed_quote_stats
    quotes = [q for f in frames for q in f.quotes]
    all_stats = [s for f in frames for s in f.statistics]

    # final settlements per raw (for close-only session accounting)
    settlements_by_raw: dict[str, list] = {}
    for raw in sorted(registry.by_raw):
        settlements_by_raw[raw] = settlement_series(all_stats, registry, raw)
    cov = coverage_report(frames, registry,
                          statistics_by_raw=settlements_by_raw)

    unknown_stat_types = sorted(
        {s.stat_type for s in all_stats
         if s.stat_type not in S.STAT_TYPE_NAMES})
    return {
        "manifest": sha256_manifest(files),
        "time_series": {
            f"{raw}@{src.rsplit('/', 1)[-1]}":
                vars(check_bars_time_series(b, raw))
            for (src, raw), b in sorted(bars_by_file.items())},
        "coverage": {raw: vars(c) for raw, c in cov.items()},
        "crossed_quotes": crossed_quote_stats(quotes),
        "unknown_stat_types": unknown_stat_types,
        "failures": [raw for raw, c in cov.items()
                     if c.n_close_only_sessions > 0],
        "roll_window": roll_window_summary(all_stats, registry),
    }


def roll_window_summary(statistics: list[Statistic],
                        registry: ContractRegistry) -> dict:
    """Volume/OI migration across a two-contract roll window, computed from
    venue statistics only (cleared_volume published with a one-morning lag;
    open_interest published after the close). Returns the crossover dates:
    the first trading date the NEW contract's volume (resp. OI) reaches the
    OLD contract's. Descriptive only — the roll rule itself is declared
    elsewhere (roll engine), never selected here."""
    import datetime as dt
    by_raw_stat: dict[tuple[str, int], dict[str, int]] = {}
    for s in statistics:
        if s.stat_type not in (S.STAT_TYPE_CLEARED_VOLUME,
                               S.STAT_TYPE_OPEN_INTEREST):
            continue
        try:
            raw = registry.raw_for(s.instrument_id)
        except Exception:
            continue
        d = dt.datetime.fromtimestamp(s.ts_ref / NS,
                                      tz=dt.timezone.utc).date().isoformat()
        by_raw_stat.setdefault((raw, s.stat_type), {})[d] = s.quantity

    def _pair(stat_type: int) -> list[str] | None:
        """The two contracts with the most overlapping dates at this stat
        type; 'old' is the one with the higher quantity on the FIRST common
        date (the front contract at the start of the window). Returns a
        list (JSON-serializable) [old, new]."""
        raws = sorted({raw for (raw, st) in by_raw_stat if st == stat_type})
        best, best_ov = None, -1
        for i in range(len(raws)):
            for j in range(i + 1, len(raws)):
                ov = len(set(by_raw_stat.get((raws[i], stat_type), {}))
                         & set(by_raw_stat.get((raws[j], stat_type), {})))
                if ov > best_ov:
                    best, best_ov = (raws[i], raws[j]), ov
        if best is None or best_ov <= 0:
            return None
        a, b = best
        first = min(set(by_raw_stat.get((a, stat_type), {}))
                    & set(by_raw_stat.get((b, stat_type), {})))
        qa_, qb_ = (by_raw_stat[(a, stat_type)][first],
                    by_raw_stat[(b, stat_type)][first])
        return [a, b] if qa_ >= qb_ else [b, a]

    def crossover(stat_type: int) -> str | None:
        pair = _pair(stat_type)
        if pair is None:
            return None
        old, new = pair
        m_old = by_raw_stat.get((old, stat_type), {})
        m_new = by_raw_stat.get((new, stat_type), {})
        for d in sorted(set(m_old) & set(m_new)):
            if m_new[d] >= m_old[d] > 0:
                return d
        return None

    return {
        "volume_pair": _pair(S.STAT_TYPE_CLEARED_VOLUME),
        "volume_crossover": crossover(S.STAT_TYPE_CLEARED_VOLUME),
        "open_interest_pair": _pair(S.STAT_TYPE_OPEN_INTEREST),
        "open_interest_crossover": crossover(S.STAT_TYPE_OPEN_INTEREST),
        "note": ("volume crossover precedes OI crossover when OI migrates "
                 "slower than traded volume; both are OBSERVED from "
                 "statistics records, publication-lagged (PIT)"),
    }
