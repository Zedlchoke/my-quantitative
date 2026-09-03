"""STOCKS-FREE-V2 shared scoring harness (A1 wiring, Z6).

Single authority for: trial counters (observed/published, idempotent replay),
S1 denial, issuer-TR reconstruction, portfolio valuation of frozen
TargetBooks, stress variants, drop-one diagnostics, benchmark contexts and
canonical artifact publication.

Scientific definitions live in the frozen family modules and specs; this
harness only executes them. Valuation semantics (documented for goldens):

- equity is a normalized multiple starting at 1.0 (flat hard benchmark = 1.0);
- between fills the ETF leg i compounds with split-adjusted raw returns plus
  distributions on ex-dates: r_i(t) = (splitadj_raw_t + dist_t) / splitadj_raw_{t-1};
- at a fill date the book rebalances to target weights at that day's RAW close
  (split-adjusted raw equals raw after the last split; S0 ends before the
  2025-12-05 sector splits, so S0 fills use unadjusted prices identically);
- turnover cost = one_way_turnover_notional x cost_bps / 10_000, deducted from
  equity at the fill; adverse slippage stress adds bps against each trade;
- +N event delay shifts every fill N sessions later (targets unchanged);
- per-period PnL is the equity delta across each holding period (decision to
  next decision or force-flat); expectancy = mean(period PnL); PF = sum of
  positive period PnLs / |sum of negative period PnLs|; MDD from the daily
  equity curve.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from dataclasses import dataclass
from typing import Mapping, Sequence

CANONICAL_JSON_KW = {"sort_keys": True, "separators": (",", ":")}


def canonical_json(payload) -> str:
    return json.dumps(payload, **CANONICAL_JSON_KW)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return sha256_hex(f.read())


# --------------------------------------------------------------------------- #
# trial counters
# --------------------------------------------------------------------------- #

class TrialLedger:
    """Append-only trial ledger with observed/published counters.

    compute_recorded(): call exactly once per scored computation, BEFORE
    publication is attempted; increments observed exactly once.
    publish(artifact): first call publishes (published +1, returns True);
    identical replays return False and change nothing.
    """

    def __init__(self, path: str | None = None):
        self.path = path
        self.entries: list[dict] = []
        self.observed = 0
        self.published_keys: set[str] = set()
        if path and os.path.exists(path):
            with open(path) as f:
                state = json.load(f)
            self.entries = state["entries"]
            self.observed = state["observed"]
            self.published_keys = set(state["published_keys"])

    def compute_recorded(self, key: str) -> None:
        self.observed += 1
        self._touch(key=key, event="COMPUTE_RECORDED")

    def publish(self, key: str, artifact: dict) -> bool:
        if key in self.published_keys:
            self._touch(key=key, event="REPLAY_ZERO_DELTA")
            return False
        self.published_keys.add(key)
        self.entries.append({"key": key, "artifact_digest": sha256_hex(canonical_json(artifact).encode()),
                             "published_at_utc": _utc()})
        self._touch(key=key, event="FIRST_PUBLICATION")
        return True

    def _touch(self, key: str, event: str) -> None:
        self.entries.append({"key": key, "event": event, "at_utc": _utc()})

    def save(self) -> None:
        if not self.path:
            return
        with open(self.path, "w") as f:
            json.dump({"observed": self.observed, "published": len(self.published_keys),
                       "published_keys": sorted(self.published_keys), "entries": self.entries},
                      f, indent=2)
            f.write("\n")


def _utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# S1 denial
# --------------------------------------------------------------------------- #

def s1_denied(path: str, s1_start: str, s1_end: str) -> bool:
    """True when a path embeds a sealed-S1 marker: an exact 's1'/'S1' path
    segment, an s1_ file prefix, or a date/month inside the sealed range."""
    norm = path.replace("\\", "/")
    segments = norm.split("/")
    if "s1" in [seg.lower() for seg in segments]:
        return True
    filename = segments[-1].lower()
    if filename.startswith("s1_") or filename.startswith("s1-"):
        return True
    for y, m in _months(s1_start, s1_end):
        if f"{y:04d}-{m:02d}" in norm:
            return True
    for token in (s1_start, s1_end):
        if token in norm:
            return True
    return False


def _months(start: str, end: str) -> list[tuple[int, int]]:
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    out = []
    while (y, m) <= (ey, em):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


# --------------------------------------------------------------------------- #
# issuer-TR reconstruction (amended FD2 formula)
# --------------------------------------------------------------------------- #

def reconstruct_tr(raw_close: Mapping[str, float], distributions: Mapping[str, float],
                   split_factors: Mapping[str, float]) -> dict[str, float]:
    """Split-adjusted raw close chained with issuer distributions.

    split_factors map effective_date -> multiplier (e.g. 2.0 for a 2:1 split):
    pre-split history is multiplied by the factor so the series is continuous.
    """
    dates = sorted(raw_close)
    cum = 1.0
    out: dict[str, float] = {}
    prev_raw = None
    prev_level = None
    for d in dates:
        if d in split_factors:
            cum *= split_factors[d]
        sadj = raw_close[d] * cum
        if prev_level is None:
            level = 1.0
        else:
            # total return growth = price growth + distribution yield (additive)
            growth = sadj / prev_raw
            level = prev_level * (growth + distributions.get(d, 0.0) / prev_raw)
        out[d] = level
        prev_raw, prev_level = sadj, level
    return out


# --------------------------------------------------------------------------- #
# valuation of a frozen target book
# --------------------------------------------------------------------------- #

@dataclass
class ValuationResult:
    equity_curve: dict          # date -> equity multiple (trading days)
    period_pnls: list           # (decision_date, pnl) per holding period
    total_pnl: float
    expectancy: float
    profit_factor: float | None
    max_drawdown: float
    total_cost: float


def value_book(entries: Sequence[dict], raw_close: Mapping[str, Mapping[str, float]],
               distributions: Mapping[str, Mapping[str, float]],
               split_factors: Mapping[str, Mapping[str, float]],
               sessions: Sequence[str], cost_bps: float,
               extra_delay_sessions: int = 0, adverse_bps: float = 0.0,
               excluded_symbol: str | None = None) -> ValuationResult:
    """Value one arm's target book. Rebalances happen AT the fill close: the
    fill day itself earns no same-day return on new weights; the next session
    does. Turnover cost counts ETF-leg changes only (cash is the residual).
    entries: ascending list of {fill_date, targets, cash_weight, entry_type}."""
    fill_dates: list[tuple[str, dict]] = []
    for e in entries:
        if e.get("entry_type") == "FORCE_FLAT":
            fill_dates.append((e["fill_date"], {}))
            continue
        targets = {s: w for s, w in e["targets"].items() if s != excluded_symbol}
        cash = e.get("cash_weight", 0.0)
        if excluded_symbol:
            cash = 1.0 - sum(targets.values())
        fill_dates.append((e["fill_date"], dict(targets, CASH=cash)))
    if extra_delay_sessions:
        shifted = []
        n = len(sessions)
        for fd, tg in fill_dates:
            i = sessions.index(fd) if fd in sessions else None
            j = min(n - 1, (i + extra_delay_sessions) if i is not None else n - 1)
            shifted.append((sessions[j], tg))
        fill_dates = shifted

    symbols = sorted({s for _, tg in fill_dates for s in tg if s != "CASH"})
    referenced = [d for d in sessions if any(d in raw_close[s] for s in symbols)]
    all_dates = referenced or list(sessions)
    equity = 1.0
    curve: dict[str, float] = {}
    weights: dict[str, float] = {"CASH": 1.0}
    period_pnls: list[tuple[str, float]] = []
    pending_decision: str | None = None
    period_start = 1.0
    total_cost = 0.0
    fill_map = dict(fill_dates)

    def day_return(d: str) -> float:
        ret = 0.0
        for s, w in weights.items():
            if s == "CASH" or not w:
                continue
            prev = _prev(raw_close[s], d)
            if not prev or not raw_close[s].get(d):
                continue
            sf = split_factors.get(s, {})
            r = _split_adj(raw_close[s], d, sf) / _split_adj(raw_close[s], prev, sf) - 1.0
            r += distributions.get(s, {}).get(d, 0.0) / _split_adj(raw_close[s], prev, sf)
            ret += w * r
        return ret

    first = True
    for d in all_dates:
        if not first:
            equity *= (1.0 + day_return(d))
        else:
            first = False
        if d in fill_map:
            if pending_decision is not None:
                period_pnls.append((pending_decision, equity - period_start))
            targets = {s: w for s, w in fill_map[d].items() if s != "CASH"}
            if excluded_symbol:
                targets = {s: w for s, w in targets.items() if s != excluded_symbol}
            turnover = sum(abs(targets.get(s, 0.0) - weights.get(s, 0.0))
                           for s in (set(targets) | set(weights)) - {"CASH"})
            cost = equity * turnover * (cost_bps + adverse_bps) / 10_000.0
            equity -= cost
            total_cost += cost
            weights = dict(targets, CASH=1.0 - sum(targets.values()))
            period_start = equity
            pending_decision = d
        curve[d] = equity
    if pending_decision is not None:
        period_pnls.append((pending_decision, equity - period_start))
    gains = sum(p for _, p in period_pnls if p > 0)
    losses = sum(p for _, p in period_pnls if p < 0)
    pf = (gains / abs(losses)) if losses < 0 else None
    mdd = _max_drawdown(curve)
    return ValuationResult(curve, period_pnls, equity - 1.0,
                           (sum(p for _, p in period_pnls) / len(period_pnls)) if period_pnls else 0.0,
                           pf, mdd, total_cost)


def _prev(series: Mapping[str, float], d: str) -> str | None:
    earlier = [x for x in sorted(series) if x < d]
    return earlier[-1] if earlier else None


def _split_adj(raw_close: Mapping[str, float], d: str, factors: Mapping[str, float]) -> float:
    cum = 1.0
    for eff, f in factors.items():
        if d < eff:
            cum *= f
    return raw_close[d] * cum


def _max_drawdown(curve: Mapping[str, float]) -> float:
    peak, mdd = 0.0, 0.0
    for d in sorted(curve):
        v = curve[d]
        peak = max(peak, v)
        if peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    return mdd
