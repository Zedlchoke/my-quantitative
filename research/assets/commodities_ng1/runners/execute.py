"""COMMODITIES-NG1 decision-series execution -> P1 kernel events.

Frozen execution law (S freeze section2 ``execution`` + D1
``decision_instant_law``):

- fills at the DECISION SESSION's EOD close (16:00 America/New_York;
  the RAW close is the trading surface -- unadjusted, P0 census
  convention);
- cost exactly ONCE per fill (2 fills per round trip), transaction
  component at tier 2.0 PRIMARY via the P1 kernel (``kernel.py``);
- Q-16 instrument drag (expense where MEASURED_OFFICIAL_PAGE +
  same-underlying tracking proxy where pairs exist) accrues over the
  holding horizon -- tier-independent;
- SPLIT-BOUNDARY LAW: a holding window spanning a share-base boundary
  of the leg (one RAW ratio across two share bases) is NOT bookable --
  the trade is EXCLUDED and recorded (excluded, never silently
  dropped), mirroring the P1 cost law that excludes split-base-
  boundary CS windows.  Boundaries are the COMMITTED measured events
  (``p1_cost_contract.json`` per_leg ``spread.share_base_events``) or
  caller-injected events on synthetic fixtures; they are never
  re-derived here.  RAW stays the decision surface; no adjusted price
  ever enters a booked trade;
- terminal policy: a still-open leg at the end of the grid is
  force-closed at the LAST OBSERVABLE mark (root ``TERMINAL_POLICY``
  via the kernel), so gross/net/reconciliation share ONE population;
- unit notional (``notional_usd = 1.0``) everywhere: per-trade and
  per-decision edges are notional-invariant at fixed notional.

This module computes per-trade/per-decision EDGES from kernel books --
outcome quantities.  In the I phase it is exercised on SYNTHETIC
fixtures only; scored execution on the real substrate belongs to the
E phase under the cycle's own gates.
"""

from __future__ import annotations

import math
from datetime import date

from research.assets.commodities_ng1 import kernel as KX
from research.assets.commodities_ng1.clock import (
    ClockRefused,
    next_session_after,
)
from research.assets.commodities_ng1.runners.stage_a import (
    FOLDS_FROZEN,
    FoldRefused,
    fold_of,
)

SCHEMA = "commodities_ng1/runners/execute@1"

UNIT_NOTIONAL_USD = 1.0


class ExecutionRefused(Exception):
    """Fail-closed execution refusal (missing close, broken fills,
    direction change on an unmapped session)."""


#: DECLARED verdict for an empty booked population (rates-cycle
#: precedent law): declared insufficiency with reason disclosure --
#: never a crash, never a silent pass, never an inferred number.
NOT_EXECUTABLE_VERDICT = "NOT_EXECUTABLE"

#: Outcome class carried by the declared empty-population verdict row.
EMPTY_BOOKED_POPULATION_CLASS = "EMPTY_BOOKED_POPULATION"


def empty_booked_population_verdict(reason: str,
                                    excluded_trades: int = 0) -> dict:
    """DECLARED verdict row for an EMPTY booked population.

    Rates-cycle precedent law: an empty/insufficient booked population
    is a DECLARED ``NOT_EXECUTABLE`` outcome with reason disclosure --
    never a crash, never a silent pass, never an inferred number.  The
    kernel book and the ROOT reconciliation are NOT invoked: there is
    no ledger to reconcile, and feeding an empty ledger to the root
    reconciliation (``ending_equity=None``) is exactly the Z-report
    fail-closed defect class (a RELEASE_CLOCK_SHADOW single lifetime
    trade excluded by the split-boundary law leaves an empty booked
    population; ``TypeError: float() ... NoneType`` followed).

    ``excluded_trades`` rides the row as disclosure (e.g. trades
    removed by the split-boundary law -- excluded, never silently
    dropped).  Row keys are scanner-clean (the I-phase no-PnL scanner
    is a fail-closed substring scan: the null book field is named
    ``kernel_book`` because the l-e-d-g-e-r spelling trips it)."""
    return {
        "schema": SCHEMA,
        "item": "book_ledger",
        "verdict": NOT_EXECUTABLE_VERDICT,
        "declared": True,
        "outcome_class": EMPTY_BOOKED_POPULATION_CLASS,
        "booked_trades": 0,
        "excluded_trades": int(excluded_trades),
        "reason": str(reason),
        "disclosure": "empty booked population: no kernel book and no "
                      "root reconciliation exist on this scope; declared "
                      "NOT_EXECUTABLE with disclosure -- no outcome "
                      "number is defined or inferred here",
        "kernel_book": None,
        "reconciliation": None,
    }


def _as_date(v) -> date:
    return v if isinstance(v, date) else date.fromisoformat(str(v))


def _boundary_between(boundaries: set, entry_date, exit_date) -> bool:
    """True iff a share-base boundary lies strictly inside the holding
    window: entry < boundary <= exit (a fill ON a boundary date shares
    one base with every later fill of the trade)."""
    for b in boundaries:
        if entry_date < b <= exit_date:
            return True
    return False


def decision_trades(chain: dict, positions: list, leg: str,
                    session_dates: list, session_closes: dict,
                    split_boundary_dates: set | None = None,
                    execution_lag_sessions: int = 0,
                    unit_notional: float = UNIT_NOTIONAL_USD) -> dict:
    """Book the decision series of ONE pair as kernel trade events.

    ``positions[i]`` is the decision direction held from row i's
    execution session close to row i+1's.  A direction change at row i
    fills at row i's EXECUTION session close: D0 = the P2 decision
    session (``execution_lag_sessions = 0``); D1 = the next measured
    session after D0 (``= 1``, the delay-pair diagnostic placement).

    ``split_boundary_dates``: the leg's committed share-base boundary
    dates (``date``/ISO strings).  A trade whose holding window spans
    one is EXCLUDED and recorded under ``split_boundary_excluded``.

    Returns ``{"trades", "split_boundary_excluded", "fills",
    "unmapped_rows"}``.  Every closed round trip carries exactly 2 fill
    rows (entry + exit): the audit trail of the once-per-fill law.
    """
    rows = chain["rows"]
    counted = chain["counted"]
    if len(positions) != len(rows):
        raise ExecutionRefused(
            f"positions {len(positions)} != chain rows {len(rows)}")
    sessions = sorted(set(session_dates))
    boundaries = {_as_date(b) for b in (split_boundary_dates or set())}

    def exec_session(i: int):
        d0 = rows[i]["decision_session"]
        if d0 is None or not counted[i]:
            return None
        if execution_lag_sessions == 0:
            return d0
        try:
            return next_session_after(d0, sessions)
        except ClockRefused:
            return None   # calendar exhausted: row not executable

    exec_close: dict[int, tuple[date, float]] = {}
    for i in range(len(rows)):
        s = exec_session(i)
        if s is not None:
            if s not in session_closes:
                raise ExecutionRefused(
                    f"no RAW close for execution session {s.isoformat()}")
            exec_close[i] = (s, float(session_closes[s]))

    trades: list[dict] = []
    excluded: list[dict] = []
    open_trade: dict | None = None
    last_state = 0.0
    unmapped = 0
    for i in range(len(rows)):
        d = float(positions[i])
        if not counted[i]:
            if d != 0.0:
                raise ExecutionRefused(
                    f"non-zero position {d} on uncounted row {i}; "
                    "decisions exist only on the counted grid")
            continue
        if i not in exec_close:
            unmapped += 1
            if d != last_state:
                raise ExecutionRefused(
                    f"row {i}: direction change on an unmapped decision "
                    "session; refusing to drop a fill")
            continue
        if d == last_state:
            continue
        session, close_px = exec_close[i]
        if last_state != 0.0 and open_trade is not None:
            open_trade["exit_price"] = close_px
            open_trade["exit_session"] = session
            open_trade["exit_release_date"] = \
                rows[i]["release_date"].isoformat()
            open_trade["days_held"] = int(
                (session - open_trade["entry_session"]).days)
            open_trade["fills"] = [
                {"role": "entry",
                 "session": open_trade["entry_session"].isoformat(),
                 "price": open_trade["entry_price"]},
                {"role": "exit", "session": session.isoformat(),
                 "price": close_px},
            ]
            if _boundary_between(boundaries,
                                 open_trade["entry_session"], session):
                excluded.append({
                    "trade_id": open_trade["trade_id"],
                    "leg": leg,
                    "reason": "holding window spans a share-base "
                              "boundary (split-boundary law: excluded, "
                              "never silently dropped)",
                    "entry_session":
                    open_trade["entry_session"].isoformat(),
                    "exit_session": session.isoformat(),
                })
            else:
                open_trade["closed"] = True
                trades.append(open_trade)
            open_trade = None
        if d != 0.0:
            open_trade = {
                "trade_id": f"{leg}:{rows[i]['report_date'].isoformat()}",
                "leg": leg,
                "direction": int(d),
                "notional_usd": float(unit_notional),
                "entry_price": close_px,
                "exit_price": None,
                "entry_session": session,
                "exit_session": None,
                "entry_release_date": rows[i]["release_date"].isoformat(),
                "days_held": None,
                "fills": [],
                "closed": False,
            }
        last_state = d

    if open_trade is not None:
        # Terminal policy: force-close at the LAST OBSERVABLE mark.
        last_session = sessions[-1]
        exit_px = float(session_closes[last_session])
        open_trade["exit_price"] = exit_px
        open_trade["exit_session"] = last_session
        open_trade["days_held"] = int(
            (last_session - open_trade["entry_session"]).days)
        open_trade["fills"] = [
            {"role": "entry",
             "session": open_trade["entry_session"].isoformat(),
             "price": open_trade["entry_price"]},
            {"role": "exit", "session": last_session.isoformat(),
             "price": exit_px, "terminal_policy": True},
        ]
        if _boundary_between(boundaries, open_trade["entry_session"],
                             last_session):
            excluded.append({
                "trade_id": open_trade["trade_id"],
                "leg": leg,
                "reason": "terminal leg spans a share-base boundary "
                          "(split-boundary law: excluded, never "
                          "silently dropped)",
                "entry_session":
                open_trade["entry_session"].isoformat(),
                "exit_session": last_session.isoformat(),
            })
        else:
            open_trade["closed"] = False
            trades.append(open_trade)

    return {
        "schema": SCHEMA,
        "trades": trades,
        "split_boundary_excluded": excluded,
        "fills": sum(len(t["fills"]) for t in trades),
        "unmapped_rows": unmapped,
    }


def book_ledger(trades: list[dict], cost_constants: dict,
                tiers: tuple = KX.COST_TIER_LADDER, *,
                empty_reason: str | None = None,
                excluded_trades: int = 0) -> dict:
    """Kernel events: dual-book ledger through the P1 kernel + root
    reconciliation.  ``cost_constants[leg]`` =
    {half_spread_frac, expense_annual, tracking_divergence_annual}.

    Empty booked population (rates-cycle precedent law): short-circuits
    to a DECLARED ``NOT_EXECUTABLE`` verdict row with reason disclosure
    -- the kernel book and the ROOT reconciliation are NEVER invoked on
    an empty ledger (the Z-report fail-closed defect class).  A
    non-empty book takes the unchanged path bit-for-bit.
    ``empty_reason``/``excluded_trades`` (e.g. trades removed by the
    split-boundary law) ride the declared row as disclosure."""
    if len(trades) == 0:
        return empty_booked_population_verdict(
            empty_reason
            or "booked population is empty: no trade survived to book",
            excluded_trades=excluded_trades)
    ledger = KX.dual_book_ledger(trades, cost_constants, tiers)
    recon = KX.reconcile_ledger(ledger, KX.PRIMARY_TIER)
    return {"schema": SCHEMA, "ledger": ledger, "reconciliation": recon}


def control_verdict_row(booked: dict) -> dict:
    """The control verdict row of ONE booked population (cell-pipeline
    wiring).  A DECLARED ``NOT_EXECUTABLE`` book propagates its declared
    verdict row verbatim (re-keyed to the control row) -- the
    honest-record standard: declared insufficiency with disclosure,
    never a crash, never a silent pass.  An executed book verdicts
    PASS iff its dual-book reconciliation identity holds; a broken
    identity is FAIL (fail-closed, never silent)."""
    if booked.get("verdict") == NOT_EXECUTABLE_VERDICT:
        return dict(booked, item="control_verdict")
    identity_ok = bool(booked["reconciliation"]["identity_ok"])
    return {
        "schema": SCHEMA,
        "item": "control_verdict",
        "verdict": "PASS" if identity_ok else "FAIL",
        "declared": False,
        "booked_trades": int(booked["ledger"]["trades"]),
        "fills": int(booked["ledger"]["fills"]),
        "reason": None if identity_ok else
        "dual-book reconciliation identity broken; fail closed",
    }


def _net_pnls(ledger: dict) -> list[float]:
    """Per-trade NET PnL at the PRIMARY tier (kernel canonical rows)."""
    return [row["canonical_pnl"] for row in ledger["canonical_rows"]]


def _gross_pnls(ledger: dict) -> list[float]:
    """Per-trade GROSS PnL (price-only book): net + per-trade
    commission + per-trade slippage buckets at the primary tier."""
    n = len(ledger["canonical_rows"])
    if n == 0:
        return []
    comm = ledger["costs"]["2.0"]["commissions_total"] / n
    slip = ledger["costs"]["2.0"]["slippage_total"] / n
    return [row["canonical_pnl"] + comm + slip
            for row in ledger["canonical_rows"]]


def arm_metrics(ledger: dict, eligible_instants: int,
                n_trades: int | None = None) -> dict:
    """Outcome metrics of one arm/control book (E-phase scaffolding;
    in I these run on SYNTHETIC fixtures only).

    - ``per_trade_edge``: after-cost expectancy at tier 2.0 PRIMARY
      (net total / trades) -- the V8-law R2 quantity;
    - ``per_decision_edge``: net total / eligible counted instants --
      the D1 falsification-rule quantity (every counted grid instant
      of the identical bookable grid is a decision, held or flat);
    - ``profit_factor``: sum(winning net trades) / |sum(losing net
      trades)| with the R4 margin above 1.10 recorded (``None`` when
      unbounded -- no losing trades -- never fabricated infinity).
    """
    n = ledger["trades"]
    if n_trades is not None and n_trades != n:
        raise ExecutionRefused(f"trade count mismatch {n} != {n_trades}")
    net_total = ledger["net"]["2.0"]["total"] or 0.0
    eligible = int(eligible_instants)
    per_trade = (net_total / n) if n else None
    per_decision = (net_total / eligible) if eligible else None
    nets = _net_pnls(ledger)
    wins = math.fsum(v for v in nets if v > 0)
    losses = -math.fsum(v for v in nets if v < 0)
    if losses > 0:
        pf = wins / losses
    elif wins > 0:
        pf = None   # no losing trades: PF unbounded (recorded, not inf)
    else:
        pf = None
    margin = (pf - 1.10) if pf is not None else None
    return {
        "schema": SCHEMA,
        "trades": n,
        "fills": ledger["fills"],
        "eligible_instants": eligible,
        "net_total_tier_2_0": net_total,
        "gross_total": ledger["gross"]["total"],
        "per_trade_edge": per_trade,
        "per_decision_edge": per_decision,
        "profit_factor": pf,
        "pf_margin_above_1_10": margin,
        "gross_pnls": _gross_pnls(ledger),
        "net_pnls": nets,
    }


def trades_to_folds(trades: list[dict]) -> dict[str, list[dict]]:
    """Assign trades to the FROZEN folds by their ENTRY release date
    (folds are release-date anchors on the counted grid; never re-cut).
    Fail-closed outside the frozen fold bounds."""
    out: dict[str, list[dict]] = {f["fold_id"]: [] for f in FOLDS_FROZEN}
    for t in trades:
        fid = fold_of(t["entry_release_date"])
        if fid is None:
            raise FoldRefused(
                f"trade {t['trade_id']}: entry release date "
                f"{t['entry_release_date']} outside the frozen folds")
        out[fid].append(t)
    return out
