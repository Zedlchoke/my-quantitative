"""Cost model with component-level provenance.

Every cost component carries one of PUBLISHED / MEASURED / DECLARED / NOT_RUN.
No fake measured costs: components without a value stay None with
provenance=NOT_RUN and any "complete total" request then fails loudly.

Sources (all 2026-10-02, FUTURES-DATA-10SYMS-V1):
  commission IBKR broker  : PUBLISHED 0.85 USD/contract/side (tier<=1000,
    tiered & fixed identical) — IBKR public pricing page.
  exchange+regulatory     : only ES has a documented all-in example
    (0.85 + 1.38 + 0.00/0.01 = 2.24). Per-symbol exchange fees for the other
    nine: NOT_RUN_NOT_FETCHED (JS table did not render; CME blocked).
  spread (observed)       : MEASURED median front spread over 20 sessions,
    close-to-close BID/ASK proxy (S6_FRONT_SPREADS.json). DAILY BID/ASK is
    NOT synchronous -> it does NOT prove an executable spread, an intrabar
    path, or capacity. Attached as an explicit caveat on every spread
    component.
  slippage                : DECLARED scenario hook. There is NO declared
    value in the repo for futures (data-lane: NOT_RUN_NO_DECLARED_VALUE).
    A scenario must declare an EXPLICIT NONZERO value with a rationale and
    declarer; zero/negative declarations are rejected (no silent
    zero-slippage). Absent declaration -> component stays NOT_RUN.
  roll cost               : observable from adjacent-contract close gaps on
    roll dates (computed by the roll engine, not by the cost book).

Stress interface: x1 / x1.5 / x2 multipliers on VARIABLE execution costs
(spread + declared slippage) by default; PUBLISHED commissions are fixed
schedule fees and are not scaled unless explicitly included.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from .instruments import get_instrument
from .taxonomy import CostProvenance, PolicyError

SAMPLED_BBO_CAVEAT = (
    "spread measured from DAILY BID/ASK closes is a close-to-close proxy, "
    "not a synchronous executable quote; it does NOT prove intrabar path, "
    "executable spread at fill time, or capacity"
)

IBKR_PAGE = ("https://www.interactivebrokers.com/en/pricing/"
             "commissions-futures.php?re=amer")
S6_SOURCE = ("research/control/FUTURES-DATA-10SYMS-V1/S6_FRONT_SPREADS.json "
             "(median of 20 front sessions, close-to-close proxy)")

SPREAD_USD = {  # MEASURED median front spread, USD per contract
    "ES": 12.50, "NG": 20.00, "6A": 20.00, "6E": 18.75, "6B": 18.75,
    "6J": 25.00, "NQ": 32.50, "CL": 30.00, "GC": 50.00, "SI": 112.50,
}

BROKER_COMMISSION_USD = 0.85          # PUBLISHED, IBKR, all 10 symbols
ES_EXCHANGE_PLUS_REG_EXAMPLE = 1.39   # 1.38 exchange + 0.01 regulatory cap
ES_ALL_IN_EXAMPLE = 2.24              # verbatim documented example

VALID_STRESS_LEVELS = (1.0, 1.5, 2.0)
VARIABLE_COMPONENTS = ("spread", "slippage")


@dataclass(frozen=True)
class CostComponent:
    name: str
    usd_per_contract_side: float | None
    provenance: CostProvenance
    source: str
    note: str = ""
    declared_by: str | None = None
    declared_rationale: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "usd_per_contract_side": self.usd_per_contract_side,
            "provenance": self.provenance.value,
            "source": self.source,
            "note": self.note,
            "declared_by": self.declared_by,
            "declared_rationale": self.declared_rationale,
        }


class IncompleteCostModelError(PolicyError):
    pass


@dataclass
class CostBook:
    symbol: str
    components: dict[str, CostComponent] = field(default_factory=dict)

    # ---------------------------------------------------------------- #
    @classmethod
    def for_symbol(cls, symbol: str) -> "CostBook":
        get_instrument(symbol)  # unknown symbol -> KeyError early
        book = cls(symbol=symbol)
        book.components["commission_broker"] = CostComponent(
            name="commission_broker",
            usd_per_contract_side=BROKER_COMMISSION_USD,
            provenance=CostProvenance.PUBLISHED,
            source=f"IBKR public pricing page, fetched 2026-10-02: {IBKR_PAGE}",
            note="tier<=1000; tiered and fixed both 0.85 USD/contract/side",
        )
        if symbol == "ES":
            book.components["exchange_plus_regulatory"] = CostComponent(
                name="exchange_plus_regulatory",
                usd_per_contract_side=ES_EXCHANGE_PLUS_REG_EXAMPLE,
                provenance=CostProvenance.PUBLISHED,
                source=f"IBKR documented example (ES all-in {ES_ALL_IN_EXAMPLE}), "
                       "fetched 2026-10-02",
                note="1.38 exchange + 0.00-0.01 regulatory; only symbol with a "
                     "rendered per-product example",
            )
        else:
            book.components["exchange_plus_regulatory"] = CostComponent(
                name="exchange_plus_regulatory",
                usd_per_contract_side=None,
                provenance=CostProvenance.NOT_RUN,
                source="IBKR per-product fee tables JS-driven, not rendered; "
                       "CME official fee pages transport-blocked 2026-10-02",
                note="NOT_RUN_NOT_FETCHED — do not fabricate; ES-style example "
                     "values must not be copied to other symbols",
            )
        book.components["spread"] = CostComponent(
            name="spread",
            usd_per_contract_side=SPREAD_USD[symbol],
            provenance=CostProvenance.MEASURED,
            source=S6_SOURCE,
            note=SAMPLED_BBO_CAVEAT,
        )
        book.components["slippage"] = CostComponent(
            name="slippage",
            usd_per_contract_side=None,
            provenance=CostProvenance.NOT_RUN,
            source="no declared futures slippage value in repo "
                   "(data lane 2026-10-02: NOT_RUN_NO_DECLARED_VALUE)",
            note="declare an explicit NONZERO scenario via declare_slippage()",
        )
        return book

    # ---------------------------------------------------------------- #
    def declare_slippage(self, usd_per_contract_side: float, declared_by: str,
                         rationale: str) -> "CostBook":
        """Explicit nonzero declared-slippage scenario hook."""
        if usd_per_contract_side <= 0:
            raise PolicyError(
                "declared slippage must be an explicit NONZERO positive value "
                f"(got {usd_per_contract_side}); zero would be a silent "
                "no-slippage assumption")
        if not rationale or not declared_by:
            raise PolicyError("declared slippage requires declared_by + rationale")
        self.components["slippage"] = CostComponent(
            name="slippage",
            usd_per_contract_side=float(usd_per_contract_side),
            provenance=CostProvenance.DECLARED,
            source=f"declared by {declared_by}",
            note="DECLARED assumption, not measured",
            declared_by=declared_by,
            declared_rationale=rationale,
        )
        return self

    def missing_components(self) -> list[str]:
        return [n for n, c in self.components.items()
                if c.usd_per_contract_side is None]

    def missing_component_status(self) -> dict[str, dict]:
        """EXEC-FIX R1 disclosure: every missing component recorded as
        NULL with its provenance and the source class a future value must
        carry — never a fabricated 0 and never an upgrade to MEASURED
        (a bar-side proxy spread cannot claim MEASURED execution)."""
        expected_class = {
            "slippage": "DECLARED",
            "exchange_plus_regulatory": "PUBLISHED",
            "commission_broker": "PUBLISHED",
        }
        return {
            name: {
                "value_usd_per_contract_side": None,
                "provenance": comp.provenance.value,
                "source": comp.source,
                "expected_source_class_when_provided":
                    expected_class.get(name, "PUBLISHED/DECLARED"),
            }
            for name, comp in self.components.items()
            if comp.usd_per_contract_side is None
        }

    def total_per_contract_side(self, allow_incomplete: bool = False
                                ) -> dict:
        """Sum of valued components + completeness disclosure."""
        missing = self.missing_components()
        total = sum(c.usd_per_contract_side for c in self.components.values()
                    if c.usd_per_contract_side is not None)
        if missing and not allow_incomplete:
            raise IncompleteCostModelError(
                f"{self.symbol}: cost components {missing} are NOT_RUN; a "
                "'complete' total would fabricate them. Pass "
                "allow_incomplete=True for a partial total with flags.")
        return {
            "symbol": self.symbol,
            "total_usd_per_contract_side": total,
            "missing_components": missing,
            "cost_incomplete": bool(missing),
            "components": {n: c.to_dict() for n, c in self.components.items()},
        }

    def round_trip_per_contract(self, allow_incomplete: bool = False) -> dict:
        t = self.total_per_contract_side(allow_incomplete=allow_incomplete)
        t["round_trip_usd_per_contract"] = 2.0 * t["total_usd_per_contract_side"]
        return t

    # ---------------------------------------------------------------- #
    def stressed_copy(self, stress: float,
                      include: tuple[str, ...] = VARIABLE_COMPONENTS
                      ) -> "CostBook":
        """x1 / x1.5 / x2 stress interface over variable execution costs."""
        if stress not in VALID_STRESS_LEVELS:
            raise PolicyError(
                f"stress multiplier must be one of {VALID_STRESS_LEVELS}, "
                f"got {stress}")
        book = CostBook(symbol=self.symbol)
        for name, comp in self.components.items():
            if name in include and comp.usd_per_contract_side is not None:
                comp = replace(
                    comp,
                    usd_per_contract_side=comp.usd_per_contract_side * stress,
                    note=(f"[stressed x{stress}] " + (comp.note or "")),
                )
            book.components[name] = comp
        book.stress_multiplier_applied = stress  # type: ignore[attr-defined]
        return book

    @staticmethod
    def stress_levels() -> tuple[float, ...]:
        return VALID_STRESS_LEVELS

    # ---------------------------------------------------------------- #
    def fill_adjustment_usd(self, side: int) -> dict:
        """USD price worsenment to apply on a fill of given side (+1 buy,
        -1 sell): half-spread + declared slippage, tagged. Returns a
        breakdown; converting to a PRICE shift is the engine's job (it owns
        ticks/instrument)."""
        if side not in (1, -1):
            raise ValueError("side must be +1 or -1")
        parts: dict[str, float] = {}
        spread = self.components.get("spread")
        if spread is not None and spread.usd_per_contract_side is not None:
            parts["half_spread_usd"] = spread.usd_per_contract_side / 2.0
        slip = self.components.get("slippage")
        if slip is not None and slip.usd_per_contract_side is not None:
            parts["slippage_usd"] = slip.usd_per_contract_side
        total = sum(parts.values())
        parts["side"] = side
        parts["total_usd"] = total
        parts["caveats"] = [SAMPLED_BBO_CAVEAT] if "half_spread_usd" in parts else []
        return parts

    def commission_cash_usd(self, contracts: int) -> dict:
        """Cash commission+fees for `contracts` fills (one side each).

        EXEC-FIX R1 (2026-10-02): the count multiplies EVERY priced
        component (base bug: the engine called this with 1 regardless of
        order size). Missing components stay None — a partial result
        deducts the KNOWN fees and discloses the missing ones; it never
        zeroes everything."""
        q = abs(int(contracts))
        if q < 1:
            raise PolicyError(
                f"contracts must be a positive integer (got {contracts!r}); "
                "a zero-quantity fill cannot carry commission arithmetic")
        parts = {}
        total = 0.0
        for name in ("commission_broker", "exchange_plus_regulatory"):
            c = self.components.get(name)
            if c is None or c.usd_per_contract_side is None:
                parts[name] = None
            else:
                parts[name] = c.usd_per_contract_side * q
                total += parts[name]
        return {
            "usd": total,
            "contracts": q,
            "components": parts,
            "missing": [n for n, v in parts.items() if v is None],
        }
