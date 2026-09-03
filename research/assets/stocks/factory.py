"""V3 measurement factory: ONE canonical target-book accounting path (A2).

PLAN_stocks.md section 9 (A2).  Repairs the two STOCKS-FREE-V2 terminal-audit
defects (research/audits/stocks_free_v2/z9_a7_terminal/AUDIT_REPORT.md) in a
single canonical implementation that every V3 scorer must use:

(a) ``CASH`` is excluded from tradable-leg turnover EVERYWHERE.  Turnover for
    costs counts only non-CASH weight changes — A4-style books (targets
    without explicit CASH, separate ``cash_weight``) and A5-style books
    (targets carrying an explicit ``"CASH"`` leg) are treated identically.
    The V2 sidecar summed the ``CASH`` leg for A5 books, roughly doubling
    per-fill cost.
(b) Every cost is charged EXACTLY ONCE: the equity deduction and the cost
    accumulator each move once per fill and must agree.  The V2 sidecar ran
    ``total_cost += cost`` twice — equity was deducted once but the reported
    accumulator doubled.

Canonical semantics (pinned by tests/stocks_free_v3, hand-computed fixtures):

* valuation mirrors research/stocks_free_v2/harness.py ``value_book`` exactly
  on valid inputs (proven equivalent in tests): equity starts at 1.0; between
  fills each ETF leg compounds split-adjusted raw returns plus distributions
  on ex-dates; a fill rebalances AT the fill close (the fill day itself earns
  no same-day return on the new weights); cost = equity x ETF-leg one-way
  turnover x (cost_bps + adverse_bps) / 1e4, deducted from equity at the fill;
* attribution identity (exact up to float rounding, frozen tolerance 1e-12)::

      sum(symbol_contribution) - total_cost = total_pnl

  where ``symbol_contribution[s]`` accumulates ``equity_before_growth x
  weight_s x return_s`` each session and CASH contributes zero.  A result
  that fails the identity or reports a cost accumulator unequal to the sum of
  its per-fill costs is an accounting break, not a strategy result.
* fold concentration has ONE definition: per-arm positive fold contribution
  divided by that SAME arm's total positive fold contribution.  No family
  pool, no neighbour substitution, no mixed gross/net denominator.
* drop-one-ETF selects a HELD ETF with the largest realized absolute-weight
  contribution, tie-broken lexicographically by symbol; dropping a non-held
  or zero-contribution ETF is rejected.
* trial publication refuses zero-event / zero-position results while keeping
  the observed-vs-published semantics of the V2 ledger: the compute is
  recorded (observed) even when publication is refused, and replays of an
  already-published key increment neither counter.

Deliberate divergences from harness ``value_book`` (both fail-closed repairs
on inputs where the V2 code silently produced a wrong book; behavior on valid
inputs is bit-identical and proven so in tests):

* an explicit ``"CASH"`` leg inside ``targets`` must agree with the entry's
  ``cash_weight`` (otherwise error); with no ``cash_weight`` key the explicit
  ``"CASH"`` weight is honored instead of being silently overwritten by 0.0;
* with ``excluded_symbol`` set on a book carrying explicit ``CASH``, the cash
  weight is the residual of the non-excluded ETF legs (1 - sum(ETF targets)),
  not a residual polluted by the excluded leg.

This module is accounting only: no strategy logic, no data access, no disk
writes, no network.  Diagnostic replicas of the historical V2 bug pattern
live in the tests (tests/stocks_free_v3/test_v2_diagnostic_replay.py), never
here — the canonical path must not carry a known-wrong implementation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from research.stocks_free_v2.harness import TrialLedger

#: The reserved cash-leg symbol inside target books.
CASH_SYMBOL = "CASH"

#: Frozen tolerance for the attribution identity on synthetic fixtures
#: (PLAN_stocks.md section 9 A2, deliverable 5).  The identity is exact up to
#: float rounding; measured residuals on hand fixtures are <= ~1e-16.
ATTRIBUTION_TOLERANCE = 1e-12

#: Relative tolerance for "cost accumulator == sum of per-fill costs".
#: The V2 double-add defect produced a 2x discrepancy; anything above float
#: noise is a break.
COST_ACCUMULATION_REL_TOLERANCE = 1e-12


# --------------------------------------------------------------------------- #
# canonical turnover and cost
# --------------------------------------------------------------------------- #
def etf_leg_turnover(previous_weights: Mapping[str, float],
                     targets: Mapping[str, float]) -> float:
    """One-way turnover over TRADABLE legs only: ``CASH`` never counts.

    ``sum(|targets[s] - previous[s]| for s in (targets | previous) - {CASH})``.
    Moving weight between ETFs and CASH costs nothing extra; only ETF-to-ETF
    weight changes are charged.  This is the single canonical definition for
    V3 (audit defect (a) repair).
    """
    legs = (set(targets) | set(previous_weights)) - {CASH_SYMBOL}
    return sum(abs(float(targets.get(s, 0.0)) - float(previous_weights.get(s, 0.0)))
               for s in legs)


def fill_cost(equity: float, turnover: float, cost_bps: float,
              adverse_bps: float = 0.0) -> float:
    """Cost of one fill: ``equity * turnover * (cost_bps + adverse_bps) / 1e4``."""
    return equity * turnover * (cost_bps + adverse_bps) / 10_000.0


def normalize_entry_targets(entry: Mapping[str, Any]) -> tuple[dict[str, float], float]:
    """Split one book entry into (ETF targets in entry order, cash weight).

    Fail-closed on disagreement between an explicit ``"CASH"`` leg inside
    ``targets`` and the entry's ``cash_weight``; honors the explicit CASH leg
    when no ``cash_weight`` key exists (harness silently overwrote it with
    0.0).  FORCE_FLAT entries normalize to empty targets, cash 1.0.
    """
    if entry.get("entry_type") == "FORCE_FLAT":
        return {}, 1.0
    targets = {s: float(w) for s, w in entry["targets"].items()}
    cash_in_targets = targets.pop(CASH_SYMBOL, None)
    cash = entry.get("cash_weight")
    if cash is not None:
        cash = float(cash)
        if cash_in_targets is not None and abs(cash_in_targets - cash) > ATTRIBUTION_TOLERANCE:
            raise ValueError(
                f"book entry at {entry.get('fill_date')!r}: explicit CASH leg "
                f"{cash_in_targets!r} disagrees with cash_weight {cash!r}"
            )
    elif cash_in_targets is not None:
        cash = cash_in_targets
    else:
        cash = 0.0
    return targets, cash


# --------------------------------------------------------------------------- #
# canonical valuation + attribution
# --------------------------------------------------------------------------- #
@dataclass
class ValuationResult:
    """Canonical result of valuing one target book.

    Shared field names with the V2 harness ``ValuationResult`` carry the same
    semantics (tests prove bit-equivalence on valid inputs).  New fields:

    * ``fill_costs``: one ``(fill_date, etf_turnover, cost)`` tuple per fill,
      in order — ``total_cost`` MUST equal the fsum of these (charged once);
    * ``symbol_contribution``: per-ETF realized PnL contribution;
    * ``attribution_residual``:
      ``fsum(contrib) - total_cost - total_pnl`` (must be ~0).
    """

    equity_curve: dict
    period_pnls: list
    total_pnl: float
    expectancy: float
    profit_factor: float | None
    max_drawdown: float
    total_cost: float
    fill_costs: list = field(default_factory=list)
    symbol_contribution: dict = field(default_factory=dict)
    attribution_residual: float = 0.0


def value_book(entries: Sequence[Mapping[str, Any]],
               raw_close: Mapping[str, Mapping[str, float]],
               distributions: Mapping[str, Mapping[str, float]],
               split_factors: Mapping[str, Mapping[str, float]],
               sessions: Sequence[str], cost_bps: float,
               extra_delay_sessions: int = 0, adverse_bps: float = 0.0,
               excluded_symbol: str | None = None) -> ValuationResult:
    """Value one arm's target book through the canonical accounting path.

    Same documented valuation contract as ``research.stocks_free_v2.harness
    .value_book`` (see module docstring), plus the attribution decomposition
    and per-fill cost records.  ``entries`` is an ascending list of
    ``{entry_type, fill_date, targets, cash_weight?}`` books — both A4-style
    (no explicit CASH in targets) and A5-style (explicit ``"CASH"`` leg) are
    accepted and valued identically because CASH never enters turnover.
    """
    fill_dates: list[tuple[str, dict]] = []
    for e in entries:
        if e.get("entry_type") == "FORCE_FLAT":
            fill_dates.append((e["fill_date"], {}))
            continue
        targets, cash = normalize_entry_targets(e)
        if excluded_symbol:
            targets = {s: w for s, w in targets.items() if s != excluded_symbol}
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

    symbols = sorted({s for _, tg in fill_dates for s in tg if s != CASH_SYMBOL})
    referenced = [d for d in sessions if any(d in raw_close[s] for s in symbols)]
    all_dates = referenced or list(sessions)
    equity = 1.0
    curve: dict[str, float] = {}
    weights: dict[str, float] = {CASH_SYMBOL: 1.0}
    period_pnls: list[tuple[str, float]] = []
    pending_decision: str | None = None
    period_start = 1.0
    total_cost = 0.0
    fill_costs: list[tuple[str, float, float]] = []
    symbol_contribution: dict[str, float] = {}
    fill_map = dict(fill_dates)

    def symbol_returns(d: str) -> dict[str, float]:
        out: dict[str, float] = {}
        for s in weights:
            if s == CASH_SYMBOL:
                continue
            prev = _prev(raw_close[s], d)
            if not prev or not raw_close[s].get(d):
                continue
            sf = split_factors.get(s, {})
            r = _split_adj(raw_close[s], d, sf) / _split_adj(raw_close[s], prev, sf) - 1.0
            r += distributions.get(s, {}).get(d, 0.0) / _split_adj(raw_close[s], prev, sf)
            out[s] = r
        return out

    first = True
    for d in all_dates:
        rets = symbol_returns(d) if not first else {}
        if not first:
            port = 0.0
            for s, w in weights.items():
                if s == CASH_SYMBOL or not w:
                    continue
                r = rets.get(s)
                if r is not None:
                    port += w * r
                    symbol_contribution[s] = (
                        symbol_contribution.get(s, 0.0) + equity * w * r)
            equity *= (1.0 + port)
        else:
            first = False
        if d in fill_map:
            if pending_decision is not None:
                period_pnls.append((pending_decision, equity - period_start))
            targets = {s: w for s, w in fill_map[d].items() if s != CASH_SYMBOL}
            if excluded_symbol:
                targets = {s: w for s, w in targets.items() if s != excluded_symbol}
            turnover = etf_leg_turnover(weights, targets)
            cost = fill_cost(equity, turnover, cost_bps, adverse_bps)
            equity -= cost                      # charged against equity ONCE
            total_cost += cost                  # accumulated ONCE (audit defect (b) repair)
            fill_costs.append((d, turnover, cost))
            weights = dict(targets, CASH=1.0 - sum(targets.values()))
            period_start = equity
            pending_decision = d
        curve[d] = equity
    if pending_decision is not None:
        period_pnls.append((pending_decision, equity - period_start))
    gains = sum(p for _, p in period_pnls if p > 0)
    losses = sum(p for _, p in period_pnls if p < 0)
    pf = (gains / abs(losses)) if losses < 0 else None
    total_pnl = equity - 1.0
    contrib_sum = math.fsum(symbol_contribution.values())
    residual = math.fsum((contrib_sum, -total_cost, -total_pnl))
    return ValuationResult(curve, period_pnls, total_pnl,
                           (sum(p for _, p in period_pnls) / len(period_pnls)) if period_pnls else 0.0,
                           pf, _max_drawdown(curve), total_cost,
                           fill_costs=fill_costs, symbol_contribution=symbol_contribution,
                           attribution_residual=residual)


def assert_reconciles(result: ValuationResult,
                      tolerance: float = ATTRIBUTION_TOLERANCE) -> None:
    """Fail closed unless the canonical books close.

    Two checks, both pinned by regression tests (ALL violations reported):

    1. attribution identity: ``|fsum(contrib) - total_cost - total_pnl| <= tol``;
    2. cost charged exactly once: ``total_cost`` equals the fsum of the
       per-fill costs (a reintroduced double-add pattern fails here).
    """
    problems = []
    if abs(result.attribution_residual) > tolerance:
        problems.append(
            f"attribution residual {result.attribution_residual!r} exceeds "
            f"frozen tolerance {tolerance!r}")
    cost_sum = math.fsum(c for _, _, c in result.fill_costs)
    scale = max(1.0, abs(result.total_cost))
    if abs(result.total_cost - cost_sum) > COST_ACCUMULATION_REL_TOLERANCE * scale:
        problems.append(
            f"cost accumulator {result.total_cost!r} != fsum(per-fill costs) "
            f"{cost_sum!r}; double-add pattern detected")
    if problems:
        raise AttributionBreakError("; ".join(problems))


class AttributionBreakError(AssertionError):
    """The canonical identity does not close within the frozen tolerance."""


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


# --------------------------------------------------------------------------- #
# fold concentration (ONE definition, per arm)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FoldConcentration:
    """Per-arm fold concentration under the single frozen definition.

    ``shares[f] = max(fold_pnl[f], 0) / positive_total`` where
    ``positive_total = sum(max(fold_pnl, 0))`` of the SAME arm.  A
    non-positive fold contributes 0.0 to both numerator and denominator.
    When the arm has no positive fold at all, ``positive_total == 0`` and all
    shares (and ``max_share``) are 0.0: no gains exist, so no fold
    concentrates gains.  ``max_share`` is the gate statistic.
    """

    arm_id: str
    shares: tuple[float, ...]
    positive_total: float

    @property
    def max_share(self) -> float:
        return max(self.shares) if self.shares else 0.0


def fold_concentration(fold_pnls: Sequence[float], arm_id: str = "") -> FoldConcentration:
    """Fold-concentration shares of ONE arm (see :class:`FoldConcentration`)."""
    if not isinstance(fold_pnls, (list, tuple)) or not fold_pnls:
        raise ValueError("fold_pnls must be a non-empty sequence of fold PnLs")
    positives = [max(float(p), 0.0) for p in fold_pnls]
    total = math.fsum(positives)
    if total > 0.0:
        shares = tuple(p / total for p in positives)
    else:
        shares = tuple(0.0 for _ in positives)
    return FoldConcentration(arm_id=arm_id, shares=shares, positive_total=total)


def per_arm_fold_concentration(
        arms: Mapping[str, Sequence[float]]) -> dict[str, FoldConcentration]:
    """Fold concentration computed independently PER ARM.

    Each arm's denominator is its own positive fold total.  Adding, removing
    or reordering other arms never changes an arm's result (pinned by test);
    there is no family pool and no neighbour substitution.
    """
    return {arm: fold_concentration(folds, arm_id=arm) for arm, folds in arms.items()}


# --------------------------------------------------------------------------- #
# drop-one-ETF selection
# --------------------------------------------------------------------------- #
def select_drop_one_symbol(contribution: Mapping[str, float],
                           weights: Mapping[str, float]) -> str:
    """Pick the HELD ETF with the largest realized absolute-weight contribution.

    Held means a non-CASH symbol with a non-zero weight.  Ranking key is
    ``(-|contribution|, symbol)`` so ties break lexicographically by symbol
    (deterministic).  A book that holds nothing, or whose largest realized
    contribution is exactly zero (nothing was realized), is rejected.
    """
    held = sorted(s for s, w in weights.items()
                  if s != CASH_SYMBOL and float(w) != 0.0)
    if not held:
        raise ValueError("drop-one rejected: book holds no ETF position")
    best = min(held, key=lambda s: (-abs(float(contribution.get(s, 0.0))), s))
    assert_drop_one_allowed(best, contribution, weights)
    return best


def assert_drop_one_allowed(symbol: str, contribution: Mapping[str, float],
                            weights: Mapping[str, float]) -> None:
    """Reject dropping a non-held or zero-contribution ETF (fail closed)."""
    if symbol == CASH_SYMBOL:
        raise ValueError("drop-one rejected: CASH is not a tradable leg")
    if float(weights.get(symbol, 0.0)) == 0.0:
        raise ValueError(f"drop-one rejected: {symbol!r} is not held (zero weight)")
    if abs(float(contribution.get(symbol, 0.0))) == 0.0:
        raise ValueError(
            f"drop-one rejected: {symbol!r} has zero realized contribution")


# --------------------------------------------------------------------------- #
# publication gate (extends the V2 trial ledger additively)
# --------------------------------------------------------------------------- #
class GatedTrialLedger(TrialLedger):
    """TrialLedger + publication gate for zero-event / zero-position results.

    Inherits the V2 observed/published semantics unchanged (single
    implementation): ``compute_recorded`` increments observed exactly once
    BEFORE publication is attempted — including when publication is then
    refused — and ``publish`` is idempotent (replays increment neither
    counter).  New: :meth:`publish_result` REFUSES to publish a result with
    no decision-fill events or no held position; the refusal is recorded in
    the append-only entries, the key stays unpublished, and counters keep
    their observed-only delta.
    """

    def __init__(self, path: str | None = None):
        super().__init__(path)
        self.refusals: list[dict] = []

    def publish_result(self, key: str, artifact: dict, *,
                       n_fill_events: int, n_held_positions: int) -> bool:
        """Gate-then-publish.  Replay of a published key stays zero-delta."""
        if key in self.published_keys:
            self._touch(key=key, event="REPLAY_ZERO_DELTA")
            return False
        reasons = []
        for name, value in (("ZERO_FILL_EVENTS", n_fill_events),
                            ("ZERO_HELD_POSITIONS", n_held_positions)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} requires an int count, got {value!r}")
            if value <= 0:
                reasons.append(name)
        if reasons:
            record = {"key": key, "event": "PUBLICATION_REFUSED_ZERO_RESULT",
                      "reasons": reasons, "at_utc": _utc_now()}
            self.entries.append(record)
            self.refusals.append({"key": key, "reasons": list(reasons)})
            return False
        return self.publish(key, artifact)


def publication_metrics(entries: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """``n_fill_events`` / ``n_held_positions`` for the publication gate.

    ``n_fill_events`` counts decision fills (FORCE_FLAT is bookkeeping, not
    an event); ``n_held_positions`` is the maximum number of concurrent
    non-CASH targets across those fills.  A book that never decides or never
    holds anything must never be published.
    """
    fills = [e for e in entries if e.get("entry_type") != "FORCE_FLAT"]
    held = 0
    for e in fills:
        targets, _ = normalize_entry_targets(e)
        held = max(held, sum(1 for w in targets.values() if w != 0.0))
    return {"n_fill_events": len(fills), "n_held_positions": held}


def _utc_now() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
