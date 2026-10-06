"""Roll engine: PIT-legal contract selection and roll tables.

DECLARED BASELINE (FUTURES-DATA-10SYMS-V1 roll rule, owner-adopted):
  hold a contract until the LAST SESSION BEFORE day-1 of its expiry month,
  then roll to the next listed contract at that session's close.
  'Expiry month' = month of the contract's last-trade date (the raw
  `expiry_month` header field, caveat C3). The expiry schedule is published
  by the exchange years in advance, so the decision uses only information
  available at decision time (PIT-legal).

CANONICAL BASIS (audit M2 reconciliation, 2026-10-02): the reading above —
"expiry month" = the LAST-TRADE-date month carried by the raw `expiry_month`
header — is THE single authoritative basis for this rule, across this code,
BACKTEST_LAUNCH_DRAFT.md §0, INTEGRATION_SUMMARY.md and every dossier. It is
NOT the delivery month (S1's `expiry_date` field is the delivery month and
must not be used for this rule). A delivery-month reading is what made the
NG dossier's original text call the rule "infeasible as written": an NG front
stops trading on the 3rd-last business day of the month BEFORE its delivery
month, i.e. before the last session of that month, so under that reading the
scheduled roll binds at the front's own final session — the same rule's
boundary consequence, not a fork. On the canonical last-trade-month basis NG
is feasible exactly like CL: the roll session (last session before day-1 of
the LTD month) precedes the front's final session by ~4 weeks (NGX26: LTD
2026-10-28, canonical roll 2026-09-30). Verified on the raw snapshot
(2026-10-02): every expired NG/CL file is cut exactly at the canonical roll
session, except each symbol's most-recently-expired contract (NGV26 through
2026-09-29, CLV6 through 2026-09-23), which extends to its true final
session.

PIT legality of alternatives:
  * volume/OI-triggered rolls are allowed ONLY if the decision input is
    same-day-OR-EARLIER data and NEVER the final same-day volume/OI (final
    volume of session t is not known at the close of t). VolumeRollRule
    therefore enforces a strictly-earlier cutoff (t-1 default) and refuses
    `final same-day` configuration outright.
  * OI is NOT present in the raw IBKR daily bars -> open interest in roll
    tables is NOT_RUN unless an external OI provider supplies it.

Continuous adjustment is built for FEATURES ONLY, causally: the adjustment
factor visible at session t includes only rolls whose decision session is
strictly before t (the factor is SUBTRACTED from raw for additive mode /
raw is DIVIDED by it for ratio mode — post-roll segments are shifted onto
the previous contract's frame so the roll jump cancels). Execution and MTM
always use raw per-contract prices.
Additive (panama) adjustment is the default because CL traded negative
(ratio adjustment is undefined/non-monotone there); ratio adjustment is
guarded and refuses non-positive closes.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum

from .calendarx import ExchangeCalendar
from .rawdata import ContractData, contracts_by_symbol
from .taxonomy import Evidence, EvidenceTag, PolicyError


class ExpiryMonthBasis(str, Enum):
    LAST_TRADE_DATE = "last_trade_date"   # default; derivable from raw header
    DELIVERY_MONTH = "delivery_month"     # NYMEX letter-month +1 conventions;
    # NOT derivable from raw headers for all symbols -> NOT_RUN without a
    # per-symbol exchange-published mapping table


DELIVERY_MONTH_STATUS = Evidence(
    tag=EvidenceTag.NOT_RUN,
    note="delivery-month basis requires exchange mapping tables not fetched "
         "(CME transport-blocked 2026-10-02); raw expiry_month field holds "
         "lastTradeDate (data-lane caveat C3)",
)

OI_STATUS = Evidence(
    tag=EvidenceTag.NOT_RUN,
    note="open interest absent from IBKR daily bar JSON; roll-table OI fields "
         "stay None unless an external PIT OI provider is attached",
)


def _expiry_month(cd: ContractData, basis: ExpiryMonthBasis) -> tuple[int, int]:
    if basis is ExpiryMonthBasis.LAST_TRADE_DATE:
        return cd.identity.expiry_month_key
    raise PolicyError(
        f"ExpiryMonthBasis {basis} is NOT_RUN: {DELIVERY_MONTH_STATUS.note}")


def roll_decision_session(cd: ContractData, cal: ExchangeCalendar,
                          basis: ExpiryMonthBasis = ExpiryMonthBasis.LAST_TRADE_DATE
                          ) -> dt.date:
    """Last session strictly before day-1 of the contract's expiry month."""
    y, m = _expiry_month(cd, basis)
    day1 = dt.date(y, m, 1)
    return cal.last_session_before(day1)


@dataclass
class RollRow:
    symbol: str
    decision_session: dt.date          # decision + execution at this close
    old_contract: str                  # localSymbol
    old_conid: int
    new_contract: str
    new_conid: int
    reason_code: str                   # e.g. CALENDAR_EXPIRY_MONTH_BASELINE
    reason_text: str
    old_volume_at_decision: float | None   # as-of cutoff session (see cutoff)
    new_volume_at_decision: float | None
    old_oi_at_decision: float | None       # NOT_RUN without OI provider
    new_oi_at_decision: float | None
    volume_cutoff_session: dt.date | None  # PIT cutoff used for volume inputs
    old_close_at_decision: float | None
    new_close_at_decision: float | None
    raw_price_gap: float | None = None       # new.close - old.close
    adjustment_additive: float | None = None  # same as raw gap (per roll)
    adjustment_ratio: float | None = None     # new.close / old.close (positives only)
    decision_inputs: dict = field(default_factory=dict)

    def validate(self) -> "RollRow":
        if self.old_close_at_decision is not None \
                and self.new_close_at_decision is not None:
            if self.raw_price_gap is None:
                self.raw_price_gap = (self.new_close_at_decision
                                      - self.old_close_at_decision)
            if self.adjustment_additive is None:
                self.adjustment_additive = self.raw_price_gap
            if (self.adjustment_ratio is None
                    and self.old_close_at_decision > 0
                    and self.new_close_at_decision > 0):
                self.adjustment_ratio = (self.new_close_at_decision
                                         / self.old_close_at_decision)
        return self

    def to_dict(self) -> dict:
        d = {
            "symbol": self.symbol,
            "decision_session": self.decision_session.isoformat(),
            "old_contract": self.old_contract,
            "old_conid": self.old_conid,
            "new_contract": self.new_contract,
            "new_conid": self.new_conid,
            "reason_code": self.reason_code,
            "reason_text": self.reason_text,
            "old_volume_at_decision": self.old_volume_at_decision,
            "new_volume_at_decision": self.new_volume_at_decision,
            "old_oi_at_decision": self.old_oi_at_decision,
            "new_oi_at_decision": self.new_oi_at_decision,
            "oi_status": OI_STATUS.to_dict(),
            "volume_cutoff_session": (self.volume_cutoff_session.isoformat()
                                      if self.volume_cutoff_session else None),
            "old_close_at_decision": self.old_close_at_decision,
            "new_close_at_decision": self.new_close_at_decision,
            "raw_price_gap": self.raw_price_gap,
            "adjustment_additive": self.adjustment_additive,
            "adjustment_ratio": self.adjustment_ratio,
        }
        d.update(self.decision_inputs)
        return d


@dataclass
class CalendarRollRule:
    """Declared baseline rule (see module docstring)."""
    basis: ExpiryMonthBasis = ExpiryMonthBasis.LAST_TRADE_DATE
    reason_code: str = "CALENDAR_EXPIRY_MONTH_BASELINE"

    def decision_inputs_used(self) -> dict:
        return {
            "inputs": ["expiry_schedule (exchange-published, years ahead)",
                       "session_calendar"],
            "pit_note": "no market data used at decision time; schedule known "
                        "in advance -> PIT-legal by construction",
        }


@dataclass
class VolumeRollRule:
    """Volume-triggered roll (alternative rule for framework test #11).

    Switch when the next contract's volume has exceeded the current's on
    `confirm_sessions` consecutive sessions, evaluated at the close of t with
    a STRICTLY-EARLIER cutoff (default t-1). Final same-day volume/OI at the
    decision close is forbidden — it does not exist yet at decision time.
    """
    confirm_sessions: int = 2
    cutoff_lag_sessions: int = 1          # >= 1 enforced
    use_same_day_final_volume: bool = False  # must stay False; True -> PolicyError
    oi_provider: object | None = None     # optional external PIT OI source
    reason_code: str = "VOLUME_MIGRATION"

    def __post_init__(self) -> None:
        if self.use_same_day_final_volume:
            raise PolicyError(
                "final same-day volume/OI at decision time is NOT PIT-legal "
                "(the session's final volume is unknown at its own close)")
        if self.cutoff_lag_sessions < 1:
            raise PolicyError(
                "VolumeRollRule requires cutoff_lag_sessions >= 1 "
                "(same-day-or-earlier data only; never final same-day volume)")
        if self.confirm_sessions < 1:
            raise PolicyError("confirm_sessions must be >= 1")

    def decision_inputs_used(self) -> dict:
        return {
            "inputs": [f"daily volume up to decision_session "
                       f"minus {self.cutoff_lag_sessions} session(s)",
                       "expiry_schedule", "session_calendar"],
            "pit_note": "volume cutoff strictly earlier than the decision "
                        "session; final same-day volume forbidden",
        }


@dataclass
class RollTable:
    symbol: str
    rule_config: dict
    rows: list[RollRow]

    def gaps_before(self, d: dt.date) -> list[float]:
        """Raw gaps of rolls decided strictly before d (causal window)."""
        return [r.raw_price_gap for r in self.rows
                if r.decision_session < d and r.raw_price_gap is not None]

    def to_dicts(self) -> list[dict]:
        return [r.to_dict() for r in self.rows]


class RollEngine:
    """Builds roll tables and continuous chains for one symbol."""

    def __init__(self, symbol: str, contracts: list[ContractData],
                 cal: ExchangeCalendar,
                 rule: CalendarRollRule | VolumeRollRule | None = None):
        self.symbol = symbol
        self.contracts = sorted(contracts, key=lambda c: c.identity.order_key())
        if not self.contracts:
            raise ValueError(f"{symbol}: no contracts")
        self.cal = cal
        self.rule = rule or CalendarRollRule()
        self._closes = [c.close_map() for c in self.contracts]
        self._vols = [c.volume_map() for c in self.contracts]

    # ------------------------------------------------------------------ #
    def build_roll_table(self) -> RollTable:
        if isinstance(self.rule, CalendarRollRule):
            rows = self._build_calendar()
        elif isinstance(self.rule, VolumeRollRule):
            rows = self._build_volume()
        else:
            raise PolicyError(f"unknown roll rule {type(self.rule).__name__}")
        cfg = dict(getattr(self.rule, "__dict__", {}) or {})
        cfg["rule_type"] = type(self.rule).__name__
        if hasattr(self.rule, "decision_inputs_used"):
            cfg["decision_inputs"] = self.rule.decision_inputs_used()
        return RollTable(symbol=self.symbol, rule_config=cfg, rows=rows)

    def _next_contract(self, idx: int) -> int | None:
        return idx + 1 if idx + 1 < len(self.contracts) else None

    def _row(self, i_old: int, i_new: int, t: dt.date, reason_code: str,
             reason_text: str, cutoff: dt.date | None) -> RollRow:
        old, new = self.contracts[i_old], self.contracts[i_new]
        oc, nc = self._closes[i_old].get(t), self._closes[i_new].get(t)
        ov = nv = None
        if cutoff is not None:
            ov = self._vols[i_old].get(cutoff)
            nv = self._vols[i_new].get(cutoff)
        oi_old = oi_new = None
        if isinstance(self.rule, VolumeRollRule) and self.rule.oi_provider is not None:
            oi_old = self.rule.oi_provider.get((old.identity.conid, cutoff))
            oi_new = self.rule.oi_provider.get((new.identity.conid, cutoff))
        row = RollRow(
            symbol=self.symbol, decision_session=t,
            old_contract=old.identity.local_symbol,
            old_conid=old.identity.conid,
            new_contract=new.identity.local_symbol,
            new_conid=new.identity.conid,
            reason_code=reason_code, reason_text=reason_text,
            old_volume_at_decision=ov, new_volume_at_decision=nv,
            old_oi_at_decision=oi_old, new_oi_at_decision=oi_new,
            volume_cutoff_session=cutoff,
            old_close_at_decision=oc, new_close_at_decision=nc,
        ).validate()
        if oc is None or nc is None:
            row.decision_inputs["price_gap_status"] = (
                "NOT_COMPUTED_MISSING_BAR_ON_DECISION_SESSION")
        return row

    def _build_calendar(self) -> list[RollRow]:
        rows: list[RollRow] = []
        i = 0
        guard = 0
        while True:
            guard += 1
            if guard > 10_000:
                raise RuntimeError("roll table construction did not terminate")
            nxt = self._next_contract(i)
            if nxt is None:
                break
            t = roll_decision_session(self.contracts[i], self.cal, self.rule.basis)
            rows.append(self._row(
                i, nxt, t, self.rule.reason_code,
                "declared baseline: last session before day-1 of expiry month "
                f"({_expiry_month(self.contracts[i], self.rule.basis)}), "
                "roll at that close to next listed contract",
                cutoff=None))
            i = nxt
        return rows

    def _build_volume(self) -> list[RollRow]:
        rule: VolumeRollRule = self.rule  # type: ignore[assignment]
        rows: list[RollRow] = []
        i = 0
        sessions = self.cal.sessions()
        streak = 0
        for t in sessions:
            nxt = self._next_contract(i)
            if nxt is None:
                break
            cutoff_idx = self.cal.session_index(t) - rule.cutoff_lag_sessions
            if cutoff_idx < 0:
                continue
            cutoff = sessions[cutoff_idx]
            ov = self._vols[i].get(cutoff)
            nv = self._vols[nxt].get(cutoff)
            if ov is None or nv is None:
                streak = 0
                continue
            streak = streak + 1 if nv > ov else 0
            if streak >= rule.confirm_sessions:
                rows.append(self._row(
                    i, nxt, t, rule.reason_code,
                    f"next-contract volume exceeded current for "
                    f"{rule.confirm_sessions} consecutive sessions "
                    f"(cutoff {cutoff}, strictly before decision {t})",
                    cutoff=cutoff))
                i = nxt
                streak = 0
        return rows

    # ------------------------------------------------------------------ #
    def held_contract_index_by_session(self, table: RollTable
                                       ) -> dict[dt.date, int]:
        """Index of the held (front) contract on each session, per roll table.

        On a roll's decision session the OLD contract is still the traded
        vehicle (the roll executes at that close), so the switch to the new
        contract applies from the NEXT session onward.
        """
        switches: list[tuple[dt.date, int]] = []
        for r in table.rows:
            idx = next(j for j, c in enumerate(self.contracts)
                       if c.identity.conid == r.new_conid)
            switches.append((r.decision_session, idx))
        out: dict[dt.date, int] = {}
        cur = 0
        k = 0
        for t in self.cal.sessions():
            while k < len(switches) and switches[k][0] < t:
                cur = switches[k][1]
                k += 1
            out[t] = cur
        return out

    def raw_chain(self, table: RollTable
                  ) -> dict[dt.date, tuple[str, int, dict[str, float]]]:
        """Raw per-contract front chain: session -> (localSymbol, conid, OHLCV).

        Execution/MTM series — NO adjustment ever applied here.
        """
        held = self.held_contract_index_by_session(table)
        out: dict[dt.date, tuple[str, int, dict[str, float]]] = {}
        for t, i in held.items():
            cd = self.contracts[i]
            bm = cd.bar_map().get(t)
            if bm is None:
                continue
            out[t] = (cd.identity.local_symbol, cd.identity.conid,
                      {"o": bm.o, "h": bm.h, "l": bm.l, "c": bm.c, "v": bm.v})
        return out

    def adjusted_chain(self, table: RollTable, how: str = "additive"
                       ) -> dict[dt.date, dict[str, float]]:
        """Continuous FEATURE series with causal adjustment.

        how='additive' (panama): adjusted = raw - A(t), where
        A(t) = sum(raw gaps of rolls decided strictly before t). The gap is
        subtracted from post-roll segments, which removes the roll jump:
        across a roll at t_r the adjusted move equals the true same-contract
        daily move new_c(t_r+1) - new_c(t_r). Works for negative CL prices.
        how='ratio': adjusted = raw / R(t), R(t) = prod(new/old of rolls
        decided strictly before t). Refuses non-positive closes (undefined
        for negative prices).
        """
        held = self.held_contract_index_by_session(table)
        out: dict[dt.date, dict[str, float]] = {}
        for t, i in sorted(held.items()):
            cd = self.contracts[i]
            bm = cd.bar_map().get(t)
            if bm is None:
                continue
            past = [r for r in table.rows if r.decision_session < t]
            if how == "additive":
                adj = sum(r.raw_price_gap for r in past
                          if r.raw_price_gap is not None)
                out[t] = {"o": bm.o - adj, "h": bm.h - adj, "l": bm.l - adj,
                          "c": bm.c - adj, "adj_factor": adj, "raw_c": bm.c}
            elif how == "ratio":
                has_ratio = any(r.adjustment_ratio is not None for r in past)
                if has_ratio and min(bm.o, bm.h, bm.l, bm.c) <= 0:
                    raise PolicyError(
                        f"ratio adjustment undefined at {t}: non-positive raw "
                        "price on this chain (CL traded negative in 2020); "
                        "use how='additive'")
                fac = 1.0
                for r in past:
                    if r.adjustment_ratio is not None:
                        fac *= r.adjustment_ratio
                out[t] = {"o": bm.o / fac, "h": bm.h / fac, "l": bm.l / fac,
                          "c": bm.c / fac, "adj_factor": fac, "raw_c": bm.c}
            else:
                raise ValueError(f"unknown adjustment {how!r}")
        return out

    def adjustment_factor_at(self, table: RollTable, d: dt.date,
                             how: str = "additive") -> float:
        """Causality-checkable factor: only rolls decided strictly before d.

        Additive: A(d) = sum(gaps) — SUBTRACT this from raw to get the
        adjusted feature price. Ratio: R(d) = prod(new/old) — DIVIDE raw.
        """
        past = [r for r in table.rows if r.decision_session < d]
        if how == "additive":
            return sum(r.raw_price_gap for r in past
                       if r.raw_price_gap is not None)
        fac = 1.0
        for r in past:
            if r.adjustment_ratio is not None:
                fac *= r.adjustment_ratio
        return fac


def build_universe_roll_tables(
        contracts: dict[tuple[str, int], ContractData],
        cal: ExchangeCalendar,
        rule: CalendarRollRule | VolumeRollRule | None = None,
        ) -> dict[str, RollTable]:
    """Roll tables for every symbol in the universe (calendar rule default)."""
    out: dict[str, RollTable] = {}
    for sym, cds in sorted(contracts_by_symbol(contracts).items()):
        eng = RollEngine(sym, cds, cal, rule=rule)
        out[sym] = eng.build_roll_table()
    return out
