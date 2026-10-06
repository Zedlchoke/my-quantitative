"""Trade journal: full per-trade records with PIT feature snapshots.

Required fields per record (owner spec):
  PIT entry-feature snapshot (with its as-of session; enforced <= decision),
  trigger/veto reason, order/fill/roll/exit events, TP/SL/time exit
  classification, net cost components, MAE/MFE labels, censoring.

AMBIGUOUS_ORDER: when TP and SL are both touched inside the SAME bar, the
intraday path is unknown; inventing a hit order is forbidden. The record is
flagged AMBIGUOUS_ORDER, point PnL is None, and bounded scenarios
(tp_first / sl_first) are stored. Downstream summarizers must either skip
ambiguous records or use the declared scenario policy — never a point value.

Breakeven tolerance is FROZEN at journal construction and stamped into every
dump; comparing net PnL to zero afterwards always uses the frozen value.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field

from .taxonomy import PolicyError

EXIT_TYPES = ("TP", "SL", "TIME", "END_OF_DATA", "FORCED_ROLL", "MANUAL",
              "TP_SL_SAME_BAR")


class PITViolationError(PolicyError):
    pass


def validate_feature_snapshot(snapshot: dict,
                              decision_session: dt.date) -> None:
    """Every feature value may carry its own as-of via a parallel
    '<key>__asof' entry or a ('value','asof') tuple; all as-of dates must be
    <= decision_session (strictly available information)."""
    for key, val in snapshot.items():
        if key.endswith("__asof"):
            continue
        asof: dt.date | None = None
        if isinstance(val, tuple) and len(val) == 2:
            val, asof = val
        elif f"{key}__asof" in snapshot:
            raw = snapshot[f"{key}__asof"]
            asof = (dt.date.fromisoformat(raw) if isinstance(raw, str) else raw)
        if asof is None:
            raise PITViolationError(
                f"feature '{key}' has no as-of date; every PIT feature must "
                "carry one (value, asof) or a '<key>__asof' entry")
        if asof > decision_session:
            raise PITViolationError(
                f"feature '{key}' as-of {asof} is AFTER decision session "
                f"{decision_session} — future information")


@dataclass
class OrderRecord:
    session: dt.date
    intent: str            # ENTER_LONG / ENTER_SHORT / EXIT / ROLL
    qty: int
    limit_or_ref_price: float | None = None
    reason: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "session": self.session.isoformat(), "intent": self.intent,
            "qty": self.qty, "limit_or_ref_price": self.limit_or_ref_price,
            "reason": self.reason, "note": self.note,
        }


@dataclass
class FillRecord:
    session: dt.date
    local_symbol: str
    conid: int
    signed_qty: int
    price: float
    cost_breakdown: dict
    cost_total_usd: float
    fill_timing: str = "next_open"    # or same_close (flagged OPTIMISTIC)
    # close-only fill law (audit M3 fix, 2026-10-02): a FillRecord stamped
    # is_close_only_bar=True is refused by TradeJournal.add() below —
    # settlement-derived bars can never fill on ANY path (entry, exits,
    # roll legs). Every engine fill carries False here.
    is_close_only_bar: bool = False

    def __post_init__(self) -> None:
        if self.is_close_only_bar:
            raise PolicyError(
                f"fill on {self.local_symbol} {self.session}: bar is "
                "close-only settlement-derived — close-only bars can "
                "never fill (entry, exits, and roll legs alike)")

    def to_dict(self) -> dict:
        return {
            "session": self.session.isoformat(),
            "local_symbol": self.local_symbol, "conid": self.conid,
            "signed_qty": self.signed_qty, "price": self.price,
            "cost_breakdown": self.cost_breakdown,
            "cost_total_usd": self.cost_total_usd,
            "fill_timing": self.fill_timing,
            "is_close_only_bar": self.is_close_only_bar,
        }


@dataclass
class RollEvent:
    session: dt.date
    from_contract: str
    to_contract: str
    from_conid: int
    to_conid: int
    old_close: float | None
    new_close: float | None
    raw_gap: float | None
    reason_code: str
    reason_text: str

    def to_dict(self) -> dict:
        return {
            "session": self.session.isoformat(),
            "from": self.from_contract, "to": self.to_contract,
            "from_conid": self.from_conid, "to_conid": self.to_conid,
            "old_close": self.old_close, "new_close": self.new_close,
            "raw_gap": self.raw_gap, "reason_code": self.reason_code,
            "reason_text": self.reason_text,
        }


@dataclass
class JournalRecord:
    trade_id: str
    symbol: str
    decision_session: dt.date      # session whose close produced the decision
    entry_decision_reason: str     # trigger
    veto_reason: str | None        # non-None if a veto applied (no trade)
    direction: int                 # +1 long / -1 short / 0 vetoed
    qty: int
    entry_fill: FillRecord | None
    exit_fill: FillRecord | None
    exit_type: str | None          # TP/SL/TIME/END_OF_DATA/FORCED_ROLL/MANUAL
    exit_session: dt.date | None
    rolls: list[RollEvent] = field(default_factory=list)
    orders: list[OrderRecord] = field(default_factory=list)
    feature_snapshot: dict = field(default_factory=dict)
    gross_pnl_usd: float | None = None
    net_pnl_usd: float | None = None          # None iff AMBIGUOUS_ORDER
    cost_components_total_usd: float = 0.0
    cost_breakdown: dict = field(default_factory=dict)
    mae_usd: float | None = None
    mfe_usd: float | None = None
    mae_mfe_method: str = (
        "per-contract segments: daily low/high vs the segment's entry "
        "(roll legs close their segment; the new contract's segment counts "
        "bars only AFTER the roll fill timestamp); close-only settlement "
        "closes count as descriptive excursions; intrabar path NOT_RUN; "
        "OHLC after an exit/roll fill can only BOUND, never resolve exactly")
    right_censored: bool = False
    ambiguity: str | None = None              # 'AMBIGUOUS_ORDER' when set
    scenario_bounds: dict | None = None       # {'tp_first': pnl, 'sl_first': pnl}
    scenario_policy: str = "bounds_only"
    stress_level: float = 1.0
    cost_incomplete: bool = False
    # ---- EXEC-FIX co-owner-review-fix-1 (2026-10-02) additions -------
    # every realized gross leg of the lifecycle: roll old-contract legs and
    # the final exit; gross_pnl_usd == sum(gross_usd) for closed records
    # (R2: the roll segment used to vanish from the record)
    gross_segments: list[dict] = field(default_factory=list)
    # per-contract MAE/MFE segments: one per contract held; each computed
    # on that contract's bars vs that segment's own entry (R3: no
    # cross-contract frame mixing)
    mae_mfe_segments: list[dict] = field(default_factory=list)
    # what the deterministic ledger booked for an AMBIGUOUS_ORDER record
    # (worst-case bound); None for point records
    ledger_booked_gross_usd: float | None = None
    # ALL cost components that were missing (NULL/NOT_RUN) on this trade's
    # fills — commission, exchange fee, slippage, any others (R1)
    cost_missing_components: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.feature_snapshot:
            validate_feature_snapshot(self.feature_snapshot,
                                      self.decision_session)
        if self.exit_type is not None and self.exit_type not in EXIT_TYPES:
            raise PolicyError(f"unknown exit_type {self.exit_type!r}")

    def segment_mae_mfe(self) -> tuple[float, float]:
        """Aggregate MAE/MFE across per-contract segments (min / max)."""
        if not self.mae_mfe_segments:
            return 0.0, 0.0
        return (min(s["mae_usd"] for s in self.mae_mfe_segments),
                max(s["mfe_usd"] for s in self.mae_mfe_segments))

    def to_dict(self) -> dict:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "decision_session": self.decision_session.isoformat(),
            "entry_decision_reason": self.entry_decision_reason,
            "veto_reason": self.veto_reason,
            "direction": self.direction,
            "qty": self.qty,
            "entry_fill": self.entry_fill.to_dict() if self.entry_fill else None,
            "exit_fill": self.exit_fill.to_dict() if self.exit_fill else None,
            "exit_type": self.exit_type,
            "exit_session": self.exit_session.isoformat()
                            if self.exit_session else None,
            "rolls": [r.to_dict() for r in self.rolls],
            "orders": [o.to_dict() for o in self.orders],
            "feature_snapshot": _jsonable(self.feature_snapshot),
            "gross_pnl_usd": self.gross_pnl_usd,
            "net_pnl_usd": self.net_pnl_usd,
            "cost_components_total_usd": self.cost_components_total_usd,
            "cost_breakdown": _jsonable(self.cost_breakdown),
            "mae_usd": self.mae_usd,
            "mfe_usd": self.mfe_usd,
            "mae_mfe_method": self.mae_mfe_method,
            "right_censored": self.right_censored,
            "ambiguity": self.ambiguity,
            "scenario_bounds": self.scenario_bounds,
            "scenario_policy": self.scenario_policy,
            "stress_level": self.stress_level,
            "cost_incomplete": self.cost_incomplete,
            "gross_segments": _jsonable(self.gross_segments),
            "mae_mfe_segments": _jsonable(self.mae_mfe_segments),
            "ledger_booked_gross_usd": self.ledger_booked_gross_usd,
            "cost_missing_components": list(self.cost_missing_components),
            "notes": list(self.notes),
        }


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, dt.date):
        return obj.isoformat()
    return obj


class TradeJournal:
    """Append-only journal with a frozen breakeven tolerance."""

    def __init__(self, breakeven_tolerance_usd: float, scenario_policy: str = "bounds_only"):
        if breakeven_tolerance_usd < 0:
            raise PolicyError("breakeven tolerance must be >= 0")
        if scenario_policy not in ("bounds_only", "conservative_worst"):
            raise PolicyError(
                "scenario_policy must be bounds_only | conservative_worst "
                "(never a point estimate for ambiguous bars)")
        self.breakeven_tolerance_usd = float(breakeven_tolerance_usd)  # FROZEN
        self.scenario_policy = scenario_policy                        # FROZEN
        self.records: list[JournalRecord] = []

    def add(self, rec: JournalRecord) -> JournalRecord:
        if rec.ambiguity == "AMBIGUOUS_ORDER" and rec.net_pnl_usd is not None:
            raise PolicyError(
                "AMBIGUOUS_ORDER record carries a point net PnL — inventing a "
                "hit order is forbidden; store scenario bounds only")
        if rec.scenario_bounds is not None:
            for k in ("tp_first", "sl_first"):
                if k not in rec.scenario_bounds:
                    raise PolicyError(f"scenario_bounds missing '{k}'")
        if rec.right_censored and rec.exit_type not in (None, "END_OF_DATA"):
            raise PolicyError(
                "right-censored record must not claim a resolved exit")
        self.records.append(rec)
        return rec

    def assert_breakeven(self, net_usd: float) -> str:
        """Classify vs zero using the FROZEN tolerance set at construction."""
        tol = self.breakeven_tolerance_usd
        if abs(net_usd) <= tol:
            return "BREAKEVEN_WITHIN_FROZEN_TOLERANCE"
        return "PROFIT" if net_usd > 0 else "LOSS"

    def point_pnl_records(self) -> list[JournalRecord]:
        """Records whose net PnL may be treated as a point value."""
        return [r for r in self.records if r.ambiguity is None]

    def summary(self) -> dict:
        by_exit: dict[str, int] = {}
        for r in self.records:
            if r.veto_reason is not None:
                by_exit["VETOED"] = by_exit.get("VETOED", 0) + 1
            else:
                k = r.exit_type or "OPEN"
                by_exit[k] = by_exit.get(k, 0) + 1
        return {
            "n_records": len(self.records),
            "n_vetoed": sum(1 for r in self.records if r.veto_reason is not None),
            "n_ambiguous": sum(1 for r in self.records
                               if r.ambiguity == "AMBIGUOUS_ORDER"),
            "n_right_censored": sum(1 for r in self.records if r.right_censored),
            "by_exit": by_exit,
            "breakeven_tolerance_usd_frozen": self.breakeven_tolerance_usd,
            "scenario_policy": self.scenario_policy,
            "note": "descriptive counts only — no performance metrics in prep",
        }

    def to_json(self) -> str:
        doc = {
            "journal_header": {
                "breakeven_tolerance_usd_frozen": self.breakeven_tolerance_usd,
                "scenario_policy_frozen": self.scenario_policy,
                "summary": self.summary(),
            },
            "records": [r.to_dict() for r in self.records],
        }
        return json.dumps(doc, indent=1, sort_keys=True)
