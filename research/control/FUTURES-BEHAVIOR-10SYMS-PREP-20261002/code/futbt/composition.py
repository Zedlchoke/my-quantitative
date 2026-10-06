"""Composition: sleeves, descriptives, risk caps, baselines + the wired
portfolio gate (MULTIASSET-WIRING, steering round 2, 2026-10-02).

Hard rule (owner spec): NEVER sum attributed leg PnL as a marginal
contribution. Marginal effects of a leg (or of a rule) are measured by
FULL-PATH re-runs of the whole portfolio without that leg/rule, because risk
caps and interactions make leg PnL non-additive. `additive_attribution_guard`
raises on any attempt to hand in precomputed leg PnLs for summation.

Combine weights must be DECLARED (fixed, provenance DECLARED). Weights fitted
on the same history being evaluated are IN_SAMPLE_MASQUERADE and rejected
unless the caller explicitly opts in with `acknowledge_in_sample=True`, which
stamps every output with a warning — this prevents historical selection from
masquerading as OOS.

Portfolio wiring laws (enforced with engine.PortfolioEngine):
  * risk caps are enforced in VETO mode — `PortfolioRiskCaps.enforce_veto`
    never clips, rescales or partially admits a signal: a blocked signal is
    returned with a machine code and must land in the journal (the engine
    files it); the legacy clip-mode `enforce` is analysis-only;
  * `PortfolioRiskGate` is the reference gate handed to
    PortfolioEngine.run(gate=...): structural caps at the decision close
    (per-sleeve / concurrency / gross contracts / gross notional) and
    margin admission at the fill open (aggregated book vs aggregated
    equity, MarginModel over PUBLISHED broker tables). Every gate call is
    appended to an audit trail;
  * existing positions are NEVER force-closed by the cap layer (no
    undeclared de-risking policy) — caps block NEW exposure only.
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from itertools import combinations

from .accounting import MarginModel
from .engine import Decision
from .taxonomy import PolicyError


class AdditiveAttributionForbidden(PolicyError):
    pass


def additive_attribution_guard(leg_pnls: dict[str, float]) -> None:
    """Refuse the (wrong) shortcut of summing attributed leg PnLs."""
    raise AdditiveAttributionForbidden(
        "summing attributed leg PnLs as marginal contributions is forbidden; "
        "measure each removal by a full-path re-run of the portfolio "
        f"(got legs: {sorted(leg_pnls)})")


@dataclass
class SleeveSeries:
    """One sleeve's daily net-PnL path (from a full-path replay) + exposure."""
    symbol: str
    pnl_by_session: dict[dt.date, float]
    exposed_sessions: set[dt.date]

    def __post_init__(self) -> None:
        extra = set(self.pnl_by_session) - self.exposed_sessions
        if extra:
            raise PolicyError(
                f"sleeve {self.symbol}: pnl on non-exposed sessions {sorted(extra)[:3]}"
                " — pnl must come from the replay's own exposure")


# --------------------------------------------------------------------- #
def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def _ranks(v: list[float]) -> list[float]:
    order = sorted(range(len(v)), key=lambda i: v[i])
    ranks = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _spearman(xs: list[float], ys: list[float]) -> float:
    return _pearson(_ranks(xs), _ranks(ys))


def pairwise_descriptives(a: SleeveSeries, b: SleeveSeries) -> dict:
    """Overlap, correlation (Pearson + Spearman), co-loss stats.

    Description only — computed over the OVERLAP window; no selection, no
    performance claim.
    """
    common = sorted(set(a.pnl_by_session) & set(b.pnl_by_session))
    xs = [a.pnl_by_session[d] for d in common]
    ys = [b.pnl_by_session[d] for d in common]
    n = len(common)
    co_loss = sum(1 for x, y in zip(xs, ys) if x < 0 and y < 0)
    losses_a = sum(1 for x in xs if x < 0) or 1
    tail = 0
    if n:
        joint_sorted = sorted(zip(xs, ys))
        q = max(1, int(0.05 * n))
        thresh_x = sorted(xs)[q - 1]
        thresh_y = sorted(ys)[q - 1]
        tail = sum(1 for x, y in zip(xs, ys)
                   if x <= thresh_x and y <= thresh_y)
    return {
        "pair": f"{a.symbol}/{b.symbol}",
        "n_overlap_sessions": n,
        "overlap_ratio_vs_union": (n / len(set(a.pnl_by_session)
                                           | set(b.pnl_by_session))
                                   if (set(a.pnl_by_session)
                                       | set(b.pnl_by_session)) else float("nan")),
        "pearson_r": _pearson(xs, ys) if n else float("nan"),
        "spearman_rho": _spearman(xs, ys) if n else float("nan"),
        "co_loss_days": co_loss,
        "co_loss_given_a_losing": co_loss / losses_a,
        "joint_tail_5pct_days": tail,
        "note": "descriptive statistics on the overlap window only; "
                "correlation != causation; no selection performed",
    }


# --------------------------------------------------------------------- #
@dataclass(frozen=True)
class PortfolioRiskCaps:
    per_sleeve_max_contracts: dict[str, int]
    max_concurrent_sleeves: int
    max_gross_contracts: int
    max_gross_notional_usd: float | None = None

    def enforce(self, target: dict[str, int],
                prices_usd_notional_per_contract: dict[str, float]
                ) -> dict:
        """ANALYSIS-ONLY clip-mode enforcement (legacy, standalone audits).
        The WIRED portfolio path is `enforce_veto` — the replay never
        silently clips quantities."""
        actions: list[str] = []
        out: dict[str, int] = {}
        for sym in sorted(target):
            q = int(target[sym])
            cap = self.per_sleeve_max_contracts.get(sym, 0)
            if abs(q) > cap:
                actions.append(
                    f"{sym}: clipped {q} -> {cap if q > 0 else -cap} "
                    "(per-sleeve cap)")
                q = (cap if q > 0 else -cap) if cap else 0
            if q != 0:
                out[sym] = q
        active = [s for s, q in out.items() if q != 0]
        if len(active) > self.max_concurrent_sleeves:
            keep = active[:self.max_concurrent_sleeves]
            for s in active:
                if s not in keep:
                    actions.append(f"{s}: vetoed (max concurrent sleeves)")
                    out[s] = 0
        gross = sum(abs(q) for q in out.values())
        if gross > self.max_gross_contracts:
            actions.append(
                f"gross {gross} > {self.max_gross_contracts}: rescaling all")
            scale = self.max_gross_contracts / gross
            out = {s: int(math.copysign(int(abs(q) * scale), q))
                   for s, q in out.items()}
        if self.max_gross_notional_usd is not None:
            notional = sum(
                abs(out.get(s, 0)) * prices_usd_notional_per_contract.get(s, 0.0)
                for s in out)
            if notional > self.max_gross_notional_usd:
                actions.append(
                    f"gross notional {notional:.0f} > "
                    f"{self.max_gross_notional_usd:.0f}: vetoing expansion")
                out = {s: 0 for s in out}
                actions.append("all positions vetoed (notional cap)")
        out = {s: q for s, q in out.items() if q != 0}
        return {"positions": out, "actions": actions}

    def enforce_veto(self, target: dict[str, int],
                     held: dict[str, int],
                     prices_usd_notional_per_contract: dict[str, float] | None
                     = None) -> dict:
        """VETO-mode enforcement — THE WIRED PATH (MULTIASSET-WIRING
        2026-10-02). NEVER clips, rescales or partially admits: every
        blocked signal comes back with a machine code and lands in the
        journal as a blocked/veto record; admitted signals keep their
        exact requested quantity.

        target: proposed NEW entry quantities {symbol: signed qty} for
        symbols NOT currently held (the replay proposes entries only
        while flat, so additions are new sleeves).
        held: the CURRENT portfolio book {symbol: signed qty} (never
        modified — existing positions are never force-closed here; a
        de-risking/liquidation policy would have to be declared first).

        Deterministic evaluation order: symbols sorted; per symbol the
        checks run per-sleeve cap -> notional -> concurrency -> gross
        contracts, and admitted exposure accumulates first-come-first-
        served across symbols. Codes:
          BLOCKED_PER_SLEEVE_CAP, BLOCKED_MAX_CONCURRENT_SLEEVES,
          BLOCKED_MAX_GROSS_CONTRACTS, BLOCKED_GROSS_NOTIONAL_USD,
          BLOCKED_NOTIONAL_PRICE_MISSING.
        """
        admitted: dict[str, int] = {}
        blocked: dict[str, dict] = {}
        actions: list[str] = []
        held = {s: q for s, q in held.items() if q}
        running_qty = sum(abs(int(q)) for q in held.values())
        running_sleeves = len(held)
        use_notional = self.max_gross_notional_usd is not None
        prices = prices_usd_notional_per_contract or {}
        if use_notional:
            for s in held:
                if s not in prices:
                    raise PolicyError(
                        f"notional cap set but no USD-notional price for held "
                        f"{s} — missing evidence is never zero (pass the "
                        "symbol's |close x multiplier|)")
            running_notional = sum(abs(int(held[s])) * prices[s] for s in held)
        else:
            running_notional = 0.0
        for sym in sorted(target):
            q = int(target[sym])
            want = abs(q)
            cap = self.per_sleeve_max_contracts.get(sym, 0)
            if want > cap:
                blocked[sym] = {"qty": q, "code": "BLOCKED_PER_SLEEVE_CAP",
                                "detail": {"requested_contracts": want,
                                           "per_sleeve_cap": cap}}
                actions.append(f"{sym}: blocked (per-sleeve cap {cap} < {want})")
                continue
            notional_add = 0.0
            if use_notional:
                if sym not in prices:
                    blocked[sym] = {
                        "qty": q, "code": "BLOCKED_NOTIONAL_PRICE_MISSING",
                        "detail": {"reason": "no PIT notional price for the "
                                             "symbol — never treated as 0"}}
                    actions.append(f"{sym}: blocked (notional price missing)")
                    continue
                notional_add = want * prices[sym]
                if running_notional + notional_add > self.max_gross_notional_usd:
                    blocked[sym] = {
                        "qty": q, "code": "BLOCKED_GROSS_NOTIONAL_USD",
                        "detail": {
                            "held_notional_usd": running_notional,
                            "added_notional_usd": notional_add,
                            "cap_usd": self.max_gross_notional_usd}}
                    actions.append(
                        f"{sym}: blocked (gross notional "
                        f"{running_notional + notional_add:.0f} > "
                        f"{self.max_gross_notional_usd:.0f})")
                    continue
            new_sleeve = sym not in held and q != 0
            if new_sleeve and running_sleeves + 1 > self.max_concurrent_sleeves:
                blocked[sym] = {
                    "qty": q, "code": "BLOCKED_MAX_CONCURRENT_SLEEVES",
                    "detail": {"held_sleeves": running_sleeves,
                               "max_concurrent": self.max_concurrent_sleeves}}
                actions.append(
                    f"{sym}: blocked (max concurrent sleeves "
                    f"{self.max_concurrent_sleeves})")
                continue
            if running_qty + want > self.max_gross_contracts:
                blocked[sym] = {
                    "qty": q, "code": "BLOCKED_MAX_GROSS_CONTRACTS",
                    "detail": {"held_gross_contracts": running_qty,
                               "requested": want,
                               "max_gross": self.max_gross_contracts}}
                actions.append(
                    f"{sym}: blocked (gross {running_qty}+{want} > "
                    f"{self.max_gross_contracts})")
                continue
            admitted[sym] = q
            running_qty += want
            running_sleeves += 1 if new_sleeve else 0
            running_notional += notional_add
            actions.append(f"{sym}: admitted {q:+d}")
        return {
            "admitted": admitted,
            "blocked": blocked,
            "actions": actions,
            "mode": "veto",
            "held_unchanged": dict(held),
            "note": "quantities are never clipped or rescaled; blocked "
                    "signals must be journaled (never silent)",
        }


# --------------------------------------------------------------------- #
@dataclass(frozen=True)
class CombineSpec:
    weights: dict[str, float]
    weight_provenance: str            # 'DECLARED' expected
    declared_by: str
    rationale: str
    acknowledge_in_sample: bool = False

    def __post_init__(self) -> None:
        if self.weight_provenance != "DECLARED" and not self.acknowledge_in_sample:
            raise PolicyError(
                "combine weights must be DECLARED (fixed ex ante). Weights "
                "fitted on the evaluated history are IN_SAMPLE_MASQUERADE; "
                "pass acknowledge_in_sample=True to stamp and allow analysis-"
                "only use — never present it as OOS")
        total = sum(abs(w) for w in self.weights.values())
        if total <= 0:
            raise PolicyError("weights must not all be zero")


@dataclass
class FullPathRunner:
    """Callable that re-runs the WHOLE portfolio for a given sleeve set.

    The combine prototype never sums precomputed leg PnLs; it calls this
    runner with different sleeve subsets and records every re-run.
    """
    runner: callable                  # runner(sleeves: list[str]) -> dict
    runs: list[dict] = field(default_factory=list)

    def run(self, sleeves: list[str], tag: str) -> dict:
        res = self.runner(sorted(sleeves))
        rec = {"tag": tag, "sleeves": sorted(sleeves), "result": res}
        self.runs.append(rec)
        return res


@dataclass(frozen=True)
class LeaveOneLegSpec:
    """Spec for a full-path leave-one-leg-out run (never additive)."""
    all_sleeves: tuple[str, ...]
    runner: FullPathRunner

    def marginal_effect(self, removed_leg: str) -> dict:
        if removed_leg not in self.all_sleeves:
            raise KeyError(removed_leg)
        base = self.runner.run(list(self.all_sleeves), tag="base_all")
        without = self.runner.run(
            [s for s in self.all_sleeves if s != removed_leg],
            tag=f"leave_out_{removed_leg}")
        return {
            "removed_leg": removed_leg,
            "base": base,
            "without_leg": without,
            "method": "full-path re-run difference (NOT additive attribution)",
            "runs": list(self.runner.runs),
        }


@dataclass(frozen=True)
class LeaveOneRuleSpec:
    """Spec for full-path rule ablation: remove one rule, re-run everything."""
    all_rules: tuple[str, ...]
    runner: FullPathRunner

    def marginal_effect(self, removed_rule: str) -> dict:
        if removed_rule not in self.all_rules:
            raise KeyError(removed_rule)
        base = self.runner.run(list(self.all_rules), "base_all_rules")
        without = self.runner.run(
            [r for r in self.all_rules if r != removed_rule],
            f"leave_out_rule_{removed_rule}")
        return {
            "removed_rule": removed_rule,
            "base": base,
            "without_rule": without,
            "method": "full-path re-run difference (NOT additive attribution)",
            "runs": list(self.runner.runs),
        }


# --------------------------------------------------------------------- #
def flat_baseline(sessions: list[dt.date]) -> dict:
    """Baseline 1: no positions at all."""
    return {
        "name": "flat",
        "pnl_by_session": {s: 0.0 for s in sessions},
        "note": "zero-position baseline; all comparison must survive costs "
                "vs this floor",
    }


def always_on_baseline(sleeve_runners: dict[str, callable],
                       sessions: list[dt.date],
                       direction: str = "long") -> dict:
    """Baseline 2: always-on single contract per sleeve for the whole window.

    Implemented as full-path sleeve re-runs with an always-in-market rule —
    NOT as constructed returns.
    """
    if direction not in ("long", "short"):
        raise ValueError("direction must be long|short")
    pnl: dict[dt.date, float] = {s: 0.0 for s in sessions}
    for sym, runner in sorted(sleeve_runners.items()):
        res = runner(direction)
        for s in sessions:
            pnl[s] += res.get("pnl_by_session", {}).get(s, 0.0)
    return {
        "name": f"always_on_{direction}",
        "pnl_by_session": pnl,
        "note": "always-on baseline (declared rule, full-path sleeve runs); "
                "descriptive only",
    }


def single_leg_baselines(sleeve_runners: dict[str, callable],
                         sessions: list[dt.date]) -> dict:
    """Baseline 3: each sleeve alone (full-path runs, one at a time)."""
    out = {}
    for sym, runner in sorted(sleeve_runners.items()):
        res = runner("long")
        out[sym] = {
            "name": f"single_leg_{sym}",
            "pnl_by_session": {s: res.get("pnl_by_session", {}).get(s, 0.0)
                               for s in sessions},
            "method": "full-path re-run",
        }
    return out


# ===================================================================== #
# Portfolio wiring (MULTIASSET-WIRING, steering round 2, 2026-10-02)
# ===================================================================== #
@dataclass
class PortfolioRiskGate:
    """Reference portfolio gate for engine.PortfolioEngine.run(gate=...).

    Two hooks, both returning None (admit) or {"code": ..., "detail": ...}
    (block — the engine files a journal record; quantities are never
    adjusted):

    * vet_entry_decision(symbol, t, decision) at the DECISION close:
      structural caps via PortfolioRiskCaps.enforce_veto on the marginal
      signal vs the live portfolio book (per-sleeve / concurrency / gross
      contracts / gross notional at the latest PIT closes);
    * admit_entry_fill(symbol, t, bar, signed_qty) at the FILL open:
      aggregated margin admission — MarginModel.check over the
      hypothetical post-fill book vs aggregated equity (Σ cash + Σ MTM
      at the marks of the LAST COMPLETED session — the current session's
      close is never visible at its own open; a just-filled position
      marks at its own fill price, MTM 0; fill commissions excluded —
      disclosed, conservative direction is to block earlier not later).

    Every call appends to `decisions` (audit trail: session, symbol,
    kind, code) — the gate never mutates the portfolio itself.
    """
    caps: PortfolioRiskCaps | None = None
    margin_model: MarginModel | None = None
    margin_level: str = "initial"
    decisions: list[dict] = field(default_factory=list)

    def bind(self, portfolio_engine) -> None:
        self._pe = portfolio_engine

    def _audit(self, session, symbol, kind, code, detail=None) -> None:
        self.decisions.append({
            "session": session.isoformat() if isinstance(session, dt.date)
            else session,
            "symbol": symbol, "kind": kind, "code": code,
            "detail": detail,
        })

    def vet_entry_decision(self, symbol: str, t, decision) -> dict | None:
        pe = getattr(self, "_pe", None)
        if self.caps is None or pe is None:
            return None
        # held = live book MERGED with same-close pending signals (the
        # effective book: concurrency/gross caps must count entries that
        # already decided and fill tomorrow — see effective_book)
        held = pe.effective_book()
        prices = None
        if self.caps.max_gross_notional_usd is not None:
            # notional at the LATEST PIT closes (sessions stepped so far);
            # a missing price blocks that symbol (never treated as 0)
            prices = {}
            for s in sorted(set(held) | {symbol}):
                try:
                    prices[s] = pe.usd_notional_per_contract(s)
                except PolicyError:
                    pass   # missing -> enforce_veto blocks with its own code
        out = self.caps.enforce_veto({symbol: int(decision.qty)}, held,
                                     prices)
        blk = out["blocked"].get(symbol)
        if blk is not None:
            self._audit(t, symbol, "decision_veto", blk["code"], blk["detail"])
            return blk
        self._audit(t, symbol, "decision_admit", None,
                    {"qty": int(decision.qty)})
        return None

    def admit_entry_fill(self, symbol: str, t, bar, signed_qty: int
                         ) -> dict | None:
        pe = getattr(self, "_pe", None)
        if self.margin_model is None or pe is None:
            return None
        held = {s: q for s, q in pe.net_positions().items() if s != symbol}
        book = dict(held)
        book[symbol] = int(signed_qty)
        equity = pe.equity_usd()
        status = self.margin_model.check(book, equity, level=self.margin_level)
        if status["breach"]:
            detail = {
                "required_usd": status["required_usd"],
                "equity_usd": status["equity_usd"],
                "shortfall_usd": status["shortfall_usd"],
                "per_symbol_usd": status["per_symbol_usd"],
                "level": self.margin_level,
                "equity_basis": "pre-fill aggregated cash + MTM at last "
                                "COMPLETED session marks (fill commissions "
                                "excluded; just-filled positions mark at "
                                "their own fill price)",
                "official_cme_span": status["official_cme_span"],
            }
            code = f"BLOCKED_MARGIN_{self.margin_level.upper()}"
            self._audit(t, symbol, "fill_block", code, detail)
            return {"code": code, "detail": detail}
        self._audit(t, symbol, "fill_admit", None,
                    {"signed_qty": int(signed_qty),
                     "required_usd": status["required_usd"],
                     "equity_usd": equity})
        return None


class AlwaysOn:
    """Baseline strategy: enter on its first session and hold to the end
    of data (record right-censors END_OF_DATA). Full-path, no selection."""

    def __init__(self, direction: str = "long"):
        if direction not in ("long", "short"):
            raise ValueError("direction must be long|short")
        self.direction = direction
        self._done = False

    def __call__(self, ctx):
        if ctx.position is None and not self._done:
            self._done = True
            return Decision(
                action=f"enter_{self.direction}", reason="baseline_always_on")
        return Decision(action="none")


def sleeve_series_from_result(result) -> dict[str, SleeveSeries]:
    """Per-sleeve daily PnL series from a PortfolioRunResult.

    Daily sleeve PnL = Δ(cash_s + MTM_s) — realized + unrealized + costs,
    the honest equity attribution (rolls included via their costs and the
    mark rebasing). Exposure = sessions from the entry fill through the
    exit (inclusive); vetoed/blocked/lapsed signals carry no exposure.
    AMBIGUOUS_ORDER exits contribute their LEDGER-BOOKED worst-case bound
    (disclosed in the note) — never a point value.
    """
    symbols = sorted(result.journals)
    if not result.sessions:
        return {}
    pnl_by = {sym: {} for sym in symbols}
    exposed = {sym: set() for sym in symbols}
    for sym in symbols:
        for r in result.journals[sym].records:
            if r.entry_fill is None:
                continue          # veto / blocked / lapsed: no exposure
            start = r.entry_fill.session
            end = r.exit_session or result.sessions[-1]
            exposed[sym].update(s for s in result.sessions if start <= s <= end)
    prev = dict(result.initial_cash_by_symbol)
    for t in result.sessions:
        for sym in symbols:
            cur = (result.cash_by_session[t].get(sym, prev.get(sym, 0.0))
                   + result.mtm_by_session[t].get(sym, 0.0))
            if t in exposed[sym]:
                pnl_by[sym][t] = cur - prev[sym]
            prev[sym] = cur
    out = {}
    for sym in symbols:
        out[sym] = SleeveSeries(symbol=sym,
                                pnl_by_session=pnl_by[sym],
                                exposed_sessions=exposed[sym])
    return out


def portfolio_pairwise_descriptives(result) -> list[dict]:
    """Co-loss / overlap / correlation descriptives across sleeves, from
    the wired portfolio run's own journals + series (description only)."""
    sleeves = sleeve_series_from_result(result)
    return [pairwise_descriptives(sleeves[a], sleeves[b])
            for a, b in combinations(sorted(sleeves), 2)]


def blocked_signal_accounting(result) -> dict:
    """Surface EVERY vetoed/blocked signal (never silent): per symbol and
    code, with the gate audit cross-check. A blocked record that carries
    an entry fill would mean a cap was enforced after execution — hard
    failure."""
    by_symbol: dict[str, int] = {}
    by_code: dict[str, int] = {}
    records = []
    for sym in sorted(result.journals):
        for r in result.journals[sym].records:
            if r.veto_reason is None:
                continue
            if r.entry_fill is not None:
                raise AssertionError(
                    f"{r.trade_id}: vetoed record carries an entry fill — a "
                    "blocked signal must never execute")
            by_symbol[sym] = by_symbol.get(sym, 0) + 1
            by_code[r.veto_reason] = by_code.get(r.veto_reason, 0) + 1
            records.append({
                "symbol": sym, "trade_id": r.trade_id,
                "decision_session": r.decision_session.isoformat(),
                "code": r.veto_reason, "qty": r.qty,
                "reason": r.entry_decision_reason,
            })
    gate_blocks = [d for d in result.gate_audit
                   if d["kind"] in ("decision_veto", "fill_block")]
    if len(gate_blocks) != sum(by_code.get(code, 0) for code in (
            "BLOCKED_PER_SLEEVE_CAP", "BLOCKED_MAX_CONCURRENT_SLEEVES",
            "BLOCKED_MAX_GROSS_CONTRACTS", "BLOCKED_GROSS_NOTIONAL_USD",
            "BLOCKED_NOTIONAL_PRICE_MISSING")) + by_code.get(
                "BLOCKED_MARGIN_INITIAL", 0) + by_code.get(
                "BLOCKED_MARGIN_MAINTENANCE", 0):
        raise AssertionError(
            f"gate audit trail ({len(gate_blocks)} blocks) disagrees with "
            f"journal blocked records ({sum(by_code.values())} vetoed) — "
            "blocked-signal accounting diverged")
    return {
        "total_blocked": sum(by_symbol.values()),
        "by_symbol": by_symbol,
        "by_code": by_code,
        "records": records,
        "gate_blocks_audited": len(gate_blocks),
        "note": "every blocked signal is journaled with its code; nothing "
                "is silently clipped, dropped or resized",
    }


def combined_breakeven(result) -> dict:
    """Breakeven classification of the COMBINED portfolio point-PnL under
    the sleeves' FROZEN journal tolerance. All member journals must share
    ONE frozen tolerance (mixing tolerances is refused). AMBIGUOUS_ORDER
    and right-censored records are never netted into the point total —
    they are disclosed as bounds/censored counts."""
    tolerances = {j.breakeven_tolerance_usd
                  for j in result.journals.values()}
    if len(tolerances) != 1:
        raise PolicyError(
            f"combined breakeven requires one shared frozen tolerance; got "
            f"{sorted(tolerances)} — journals must be constructed alike")
    tol = tolerances.pop()
    point_total = 0.0
    n_ambiguous = 0
    n_censored = 0
    bounds = []
    for sym in sorted(result.journals):
        for r in result.journals[sym].records:
            if r.entry_fill is None:
                continue
            if r.right_censored:
                n_censored += 1
                continue
            if r.net_pnl_usd is None:
                n_ambiguous += 1
                bounds.append({"symbol": sym, "trade_id": r.trade_id,
                               "scenario_bounds": r.scenario_bounds})
                continue
            point_total += r.net_pnl_usd
    if abs(point_total) <= tol:
        classification = "BREAKEVEN_WITHIN_FROZEN_TOLERANCE"
    else:
        classification = "PROFIT" if point_total > 0 else "LOSS"
    return {
        "classification": classification,
        "point_net_usd": point_total,
        "frozen_tolerance_usd": tol,
        "ambiguous_excluded": n_ambiguous,
        "ambiguous_bounds": bounds,
        "right_censored_excluded": n_censored,
        "note": "ambiguous records are bounded, censored records are never "
                "netted into point totals",
    }


def portfolio_run_summary(result) -> dict:
    """Standard comparable summary of one full-path portfolio run (used by
    the leave-one-leg harness and the baselines; never additive
    attribution)."""
    blocked = blocked_signal_accounting(result)
    be = combined_breakeven(result)
    return {
        "symbols": list(result.symbols),
        "sessions": len(result.sessions),
        "initial_cash_total_usd": sum(result.initial_cash_by_symbol.values()),
        "final_cash_total_usd": result.final_cash_usd(),
        "realized_point_net_usd": be["point_net_usd"],
        "max_drawdown_usd": (min(result.drawdown_by_session.values())
                             if result.drawdown_by_session else 0.0),
        "n_records": sum(len(j.records) for j in result.journals.values()),
        "n_blocked": blocked["total_blocked"],
        "blocked_by_code": blocked["by_code"],
        "ambiguous_excluded": be["ambiguous_excluded"],
        "right_censored_excluded": be["right_censored_excluded"],
    }


def portfolio_leave_one_leg(portfolio_factory: callable,
                            legs: tuple[str, ...]) -> dict:
    """Leave-one-leg FULL-PATH harness over wired portfolio runs.

    portfolio_factory(sleeves: list[str]) must build and return a FRESH
    runnable (e.g. a bound PortfolioEngine.run callable taking
    strategies) — every removal re-runs the WHOLE portfolio, never a sum
    of attributed leg PnLs. Uses FullPathRunner so every re-run is
    recorded; interactions (a margin cap blocking one leg because another
    holds margin) make results genuinely non-additive, which is exactly
    what this harness measures.
    """
    def runner(sleeves: list[str]) -> dict:
        return portfolio_run_summary(portfolio_factory(sorted(sleeves))())

    fp = FullPathRunner(runner=runner)
    spec = LeaveOneLegSpec(all_sleeves=tuple(sorted(legs)), runner=fp)
    out = {"base": runner(list(legs)), "leave_one_leg": {}}
    for leg in sorted(legs):
        res = spec.marginal_effect(leg)
        out["leave_one_leg"][leg] = {
            "without_leg": res["without_leg"],
            "marginal_effect_total_net_usd": (
                res["base"]["realized_point_net_usd"]
                - res["without_leg"]["realized_point_net_usd"]),
            "method": res["method"],
        }
    out["method"] = ("full-path portfolio re-runs (engine re-run minus the "
                     "leg; NEVER attributed-PnL sums)")
    out["runs"] = list(fp.runs)
    return out
