"""Point-in-time hygiene: as-of views over statistics and definitions,
vintage settlement reconstruction, feature-only roll adjustments.

Publication semantics:
  * a statistic is KNOWABLE only after its publication ts (ts_recv /
    ts_event), even though it describes an earlier trading date (ts_ref).
    Settlements publish after the session; cleared volume next morning;
    open interest after the close. `asof()` filters on publication time.
  * instrument definitions are actions: an identity exists at time T only
    if its latest action at/before T was A or M (D deletes it).
  * revisions (preliminary -> final settlement) are both retained; the
    PIT-visible value at T is the latest publication <= T, with its
    final/preliminary flag carried through.

Adjustments: raw prices are always stored raw. Continuous/adjusted series
are computed ONLY as explicitly declared FEATURE transforms with the
factors recorded (and continuous vendor series never touch execution,
per ingest.require_outright).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..taxonomy import PolicyError
from .ingest import Bar, ContractIdentity, DefinitionAction, Statistic
from .ohlcv import SettlementRecord
from .session import utc_to_exchange


class PitViolation(PolicyError):
    pass


def asof_statistics(statistics: list[Statistic], asof_ns: int) -> list[Statistic]:
    """Statistics PUBLISHED at or before `asof_ns` (publication-gated)."""
    return [s for s in statistics if s.ts_event <= asof_ns]


def asof_identity(defs: list[DefinitionAction], raw_symbol: str,
                  asof_ns: int) -> ContractIdentity | None:
    """Latest definition state for `raw_symbol` as known at `asof_ns`."""
    actions = sorted((d for d in defs
                      if d.raw_symbol == raw_symbol and d.ts_event <= asof_ns),
                     key=lambda d: d.ts_event)
    if not actions or actions[-1].action == "D":
        return None
    d = actions[-1]
    return ContractIdentity(
        raw_symbol=d.raw_symbol, instrument_id=d.instrument_id,
        activation=d.activation, expiration=d.expiration,
        maturity_year=d.maturity_year, maturity_month=d.maturity_month,
        min_price_increment=d.min_price_increment,
        unit_of_measure_qty=d.unit_of_measure_qty, exchange=d.exchange)


@dataclass(frozen=True)
class VintageSettlement:
    session_date: str
    visible_price: int
    final: bool
    published_ts: int


def settlement_vintage(settlements: list[SettlementRecord], asof_ns: int
                       ) -> dict[str, VintageSettlement]:
    """What settlement prices were visible at `asof_ns`, per trading date:
    the latest publication <= asof, with its revision stage."""
    out: dict[str, VintageSettlement] = {}
    for s in sorted(settlements, key=lambda s: s.published_ts):
        if s.published_ts > asof_ns:
            continue
        out[s.session_date] = VintageSettlement(
            session_date=s.session_date, visible_price=s.price,
            final=s.final, published_ts=s.published_ts)
    return out


def require_asof_order(publish_ts: int, ref_ts: int, what: str) -> None:
    """Guard: a statistic referencing trading date X must publish >= X
    (publication never precedes the referenced date)."""
    ref_date = utc_to_exchange(ref_ts).date()
    pub_date = utc_to_exchange(publish_ts).date()
    if pub_date < ref_date:
        raise PitViolation(
            f"{what}: published {pub_date} but references trading date "
            f"{ref_date} — a time-traveling statistic; refusing")


# ---------------------------------------------------------------------------
# feature-only roll adjustment
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RollAdjustmentFactor:
    raw_symbol_old: str
    raw_symbol_new: str
    roll_session: str          # session at which the switch happens
    old_close: int             # raw, nanos
    new_close: int             # raw, nanos
    method: str                # 'additive' | 'ratio'
    additive_nanos: int | None = None
    ratio: float | None = None
    feature_only: bool = True  # hard flag: never an execution transform
    declared_by: str = ""

    def to_dict(self) -> dict:
        return {
            "old": self.raw_symbol_old, "new": self.raw_symbol_new,
            "roll_session": self.roll_session,
            "old_close": self.old_close, "new_close": self.new_close,
            "method": self.method, "additive_nanos": self.additive_nanos,
            "ratio": self.ratio, "feature_only": self.feature_only,
            "declared_by": self.declared_by,
        }


def compute_roll_factor(old_close: int, new_close: int, *,
                        raw_symbol_old: str, raw_symbol_new: str,
                        roll_session: str, method: str = "additive",
                        declared_by: str = "") -> RollAdjustmentFactor:
    """Record the adjustment factor for a roll (descriptive measurement of
    the adjacent-contract gap). Raw prices stay raw; adjusted series are a
    FEATURE-ONLY transform that must be declared."""
    if not declared_by:
        raise PolicyError(
            "roll adjustment requires a declarer (declared_by) — undeclared "
            "transforms are how silent adjustments leak into execution")
    if method == "additive":
        return RollAdjustmentFactor(
            raw_symbol_old, raw_symbol_new, roll_session, old_close, new_close,
            "additive", additive_nanos=old_close - new_close,
            declared_by=declared_by)
    if method == "ratio":
        if old_close <= 0 or new_close <= 0:
            raise PolicyError(
                "ratio adjustment impossible on non-positive prices "
                "(negative-price CL regime); use additive or none")
        return RollAdjustmentFactor(
            raw_symbol_old, raw_symbol_new, roll_session, old_close, new_close,
            "ratio", ratio=new_close / old_close, declared_by=declared_by)
    raise PolicyError(f"unknown adjustment method {method!r}")


def apply_feature_adjustment(bars: list[Bar], factors: list[RollAdjustmentFactor],
                             *, execution_context: bool = False) -> list[Bar]:
    """Apply recorded factors to build a FEATURE series (additive splice).

    Anchor convention (verified against the tests): the series is anchored
    at the FIRST (oldest) contract's price level. Every bar AT/after a roll
    session shifts by that roll's additive factor (old_close - new_close),
    cumulatively across rolls, so the spliced series is continuous at each
    roll boundary while the EARLIEST raw prices stay untouched. Raises if
    called in an execution context: adjusted series can never be fill
    prices."""
    if execution_context:
        raise PolicyError(
            "apply_feature_adjustment in execution context: adjusted series "
            "are feature-only by construction; fills must use raw prices")
    if not factors:
        return list(bars)
    adjusted: list[Bar] = []
    offset = 0
    fi = 0
    fs = sorted(factors, key=lambda f: _session_start_ns(f.roll_session))
    for b in sorted(bars, key=lambda b: b.ts_event):
        while (fi < len(fs)
               and b.ts_event >= _session_start_ns(fs[fi].roll_session)):
            offset += fs[fi].additive_nanos or 0
            fi += 1
        adjusted.append(Bar(
            ts_event=b.ts_event, instrument_id=b.instrument_id,
            open=b.open + offset, high=b.high + offset, low=b.low + offset,
            close=b.close + offset, volume=b.volume, rtype=b.rtype))
    return adjusted


def _session_start_ns(session_date: str) -> int:
    import datetime as dt
    from .session import _session_bounds
    y, m, d = (int(x) for x in session_date.split("-"))
    return _session_bounds(dt.date(y, m, d))[0]
