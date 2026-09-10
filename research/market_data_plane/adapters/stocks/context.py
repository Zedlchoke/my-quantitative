"""Frozen stocks-adapter context: entity identity + synthetic exchange calendar.

Lane A8 (MDP-V2 stocks adapter).  Freeze authority:
research/control/market_data_plane_v2_run/architecture_freeze_v2.json,
section ``adapters`` -> ``stocks``:

* identity: "permanent entity id distinct from ticker (adapter context
  table); ticker changes never change entity identity" — the ticker string
  is NEVER an identity at runtime; it is only a lookup key into the frozen
  entity table, where every historical name of an entity maps to the SAME
  permanent ``entity_id``.
* calendar: "exchange calendar, holidays, early closes from frozen synthetic
  calendar fixtures" — weekday sessions minus an explicit holiday date list,
  with an explicit early-close date list closing at 18:00 UTC.  Early closes
  are still full sessions (they change only the session close instant).
* delisting: delist dates per permanent entity; a bar dated strictly after
  its entity's delist date is a forward-fill and fails closed (the adapter
  raises; it is never quarantined-and-continued).
* adjustment availability rule (frozen): a corporate-action factor is
  available at its ex-date session OPEN.  An adjusted bar whose own
  availability (its session close, the frozen default) precedes that
  instant is a lookahead and fails closed.

The context is an immutable, defensively-copied value object: mappings
handed in are snapshotted at construction so later caller mutation can
never change identity resolution or calendar semantics mid-stream.

stdlib + sibling market_data_plane modules only; no network; never mutates
its inputs.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Mapping

from ... import models as _models

__all__ = [
    "ADJUSTMENT_AVAILABILITY_RULE",
    "ISO_DATE_RE",
    "AdapterContext",
    "parse_iso_date",
]

#: Frozen adjustment-availability rule (adapters.stocks.freeze): a split /
#: dividend factor carries EXACT availability at its ex-date session open.
ADJUSTMENT_AVAILABILITY_RULE = "FACTOR_AVAILABLE_AT_EX_DATE_SESSION_OPEN"

#: Strict ISO calendar-date grammar (zero-padded YYYY-MM-DD).
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_iso_date(value, field_name: str) -> dt.date:
    """Parse a strict zero-padded ISO calendar date; fail closed otherwise."""
    if not isinstance(value, str) or not ISO_DATE_RE.match(value):
        raise ValueError(
            f"{field_name}: expected strict ISO date YYYY-MM-DD, got {value!r}")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - regex already bounds this
        raise ValueError(f"{field_name}: not a real calendar date: {value!r}") from exc


def _utc_ns(day: dt.date, clock: dt.time) -> int:
    """Exact UTC nanoseconds for a wall-clock instant on an exchange day."""
    return _models.timestamp_to_ns(
        dt.datetime.combine(day, clock, tzinfo=dt.timezone.utc))


@dataclass(frozen=True)
class AdapterContext:
    """Frozen stocks adapter context (identity, calendar, precision, rule).

    Required (no defaults): ``entity_table``.  Everything else carries the
    frozen synthetic defaults documented per field; tests and S0 snapshots
    pass explicit values for the pieces they exercise.
    """

    # --- permanent entity identity -----------------------------------------
    #: ticker -> permanent entity_id.  EVERY historical name of an entity
    #: maps to the SAME entity_id (ticker changes never change identity);
    #: identity is never derived from the ticker string at runtime.
    entity_table: Mapping[str, str]

    # --- delisting ----------------------------------------------------------
    #: permanent entity_id -> ISO delist date.  The delist date itself is the
    #: entity's terminal session; any bar dated strictly AFTER it is a
    #: forbidden forward fill (fail closed in the adapter).
    delist_dates: Mapping[str, str] = field(default_factory=dict)

    # --- frozen synthetic exchange calendar ---------------------------------
    #: explicit ISO holiday dates (weekday sessions removed from the
    #: calendar; gaps on them are EXPECTED, never unexplained).
    holidays: Mapping[str, str] | frozenset[str] = field(default_factory=frozenset)
    #: explicit ISO early-close dates: full sessions closing at
    #: ``early_close_utc`` (18:00 UTC frozen).  Early closes still count as
    #: sessions for coverage.
    early_close_dates: Mapping[str, str] | frozenset[str] = field(default_factory=frozenset)
    #: regular session open (exchange-time frame, UTC ns semantics).
    session_open_utc: dt.time = dt.time(14, 30)
    #: regular session close.
    regular_close_utc: dt.time = dt.time(20, 0)
    #: early-close close instant — frozen to 18:00 UTC per the freeze.
    early_close_utc: dt.time = dt.time(18, 0)

    # --- precision / provenance carried onto every bar ----------------------
    price_precision: int = 4
    size_precision: int = 8
    normalizer_version: str = "stocks-daily-mdp-v2"
    #: frozen adjustment-availability rule identifier (declared, not guessed).
    adjustment_availability_rule: str = ADJUSTMENT_AVAILABILITY_RULE
    source_id: str = "SYNTH-STOCKS-S0"
    provider_id: str = "SYNTH"
    venue: str = "XSYN"
    asset_class: str = "equity"
    #: one daily bar per session (86,400 s in ns).
    bar_type: str = "1d-LAST"
    interval_ns: int = 86_400_000_000_000
    #: default upstream retrieval manifest id (mirrors the A3_Q4 ruling:
    #: retrieval manifest, not archive manifest); a raw record may override
    #: per record.  Empty means "must come from the record" (fail closed).
    manifest_sha256: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.entity_table, Mapping) or not self.entity_table:
            raise ValueError("entity_table must be a non-empty ticker -> entity_id mapping")
        for ticker, entity_id in self.entity_table.items():
            if not isinstance(ticker, str) or not ticker:
                raise ValueError(f"entity_table ticker must be a non-empty string: {ticker!r}")
            if not isinstance(entity_id, str) or not entity_id:
                raise ValueError(
                    f"entity_table[{ticker!r}]: entity_id must be a non-empty string")
        object.__setattr__(self, "entity_table", dict(self.entity_table))

        delists: dict[str, dt.date] = {}
        for entity_id, iso in dict(self.delist_dates).items():
            if not isinstance(entity_id, str) or not entity_id:
                raise ValueError("delist_dates keys must be non-empty entity ids")
            delists[entity_id] = parse_iso_date(iso, f"delist_dates[{entity_id!r}]")
        object.__setattr__(self, "_delist_dates", delists)

        object.__setattr__(self, "_holidays", frozenset(
            parse_iso_date(d, "holidays") for d in self.holidays))
        object.__setattr__(self, "_early_close_dates", frozenset(
            parse_iso_date(d, "early_close_dates") for d in self.early_close_dates))

        if not (self.session_open_utc < self.early_close_utc < self.regular_close_utc):
            raise ValueError(
                "frozen calendar sanity failed: require "
                "session_open_utc < early_close_utc < regular_close_utc")
        for name in ("price_precision", "size_precision"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be an int >= 1")
        if not isinstance(self.interval_ns, int) or isinstance(self.interval_ns, bool) \
                or self.interval_ns <= 0:
            raise ValueError("interval_ns must be an int > 0")
        if not isinstance(self.normalizer_version, str) or not self.normalizer_version:
            raise ValueError("normalizer_version must be a non-empty string")
        for name in ("source_id", "provider_id", "venue", "asset_class", "bar_type"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")
        if self.manifest_sha256:
            if not isinstance(self.manifest_sha256, str) or \
                    not re.match(r"^[0-9a-f]{64}$", self.manifest_sha256):
                raise ValueError(
                    "manifest_sha256 must be empty or lowercase 64-hex sha256")
        if self.adjustment_availability_rule != ADJUSTMENT_AVAILABILITY_RULE:
            raise ValueError(
                "adjustment_availability_rule is frozen to "
                f"{ADJUSTMENT_AVAILABILITY_RULE!r}; divergent rules are a "
                "different adapter and need a new freeze")

    # --- identity -----------------------------------------------------------

    def entity_for_ticker(self, ticker: str) -> str:
        """Resolve a ticker through the frozen table (never string-derived).

        Raises ``KeyError`` for a ticker absent from the table — the adapter
        turns that into a fail-closed UNKNOWN_INSTRUMENT.
        """
        if not isinstance(ticker, str) or not ticker:
            raise KeyError(ticker)
        return self.entity_table[ticker]

    def delist_date(self, entity_id: str) -> dt.date | None:
        """The entity's delist date (terminal session) or None if still listed."""
        return self._delist_dates.get(entity_id)

    # --- calendar -------------------------------------------------------------

    def is_session(self, day: dt.date) -> bool:
        """True iff ``day`` is an exchange session.

        Weekday sessions minus explicit holidays; early closes are still
        sessions (they only change the close instant).
        """
        return day.weekday() < 5 and day not in self._holidays

    def session_open_ns(self, day: dt.date) -> int:
        return _utc_ns(day, self.session_open_utc)

    def session_close_ns(self, day: dt.date) -> int:
        """Session close instant; early-close-aware (18:00 UTC on those days)."""
        clock = self.early_close_utc if day in self._early_close_dates \
            else self.regular_close_utc
        return _utc_ns(day, clock)

    def session_available_ns(self, day: dt.date) -> int:
        """Frozen default availability: the session close."""
        return self.session_close_ns(day)

    def factor_available_ns(self, ex_date: dt.date) -> int:
        """Exact availability instant of a corporate-action factor.

        Frozen rule: the factor is available at its ex-date session OPEN.
        The caller (adapter) must first establish ``is_session(ex_date)`` —
        a factor whose ex-date is not a session has an undefined availability
        and fails closed there.
        """
        return self.session_open_ns(ex_date)

    def next_session(self, day: dt.date, *, horizon_days: int = 30) -> dt.date:
        """First session strictly after ``day`` (bounded scan, fail closed)."""
        for offset in range(1, horizon_days + 1):
            candidate = day + dt.timedelta(days=offset)
            if self.is_session(candidate):
                return candidate
        raise ValueError(
            f"no exchange session within {horizon_days} days after {day.isoformat()}; "
            "calendar horizon exceeded (fail closed)")

    def sessions_between(self, start: dt.date, end: dt.date) -> list[dt.date]:
        """Sorted inclusive list of exchange sessions in ``[start, end]``."""
        if end < start:
            return []
        out = []
        cursor = start
        while cursor <= end:
            if self.is_session(cursor):
                out.append(cursor)
            cursor += dt.timedelta(days=1)
        return out

    def calendar_gap_days(self, start: dt.date, end: dt.date) -> list[dt.date]:
        """Non-session calendar days inside ``[start, end]`` (weekends+holidays).

        These are the EXPECTED gaps: coverage never counts them as unexplained.
        """
        out = []
        cursor = start
        while cursor <= end:
            if not self.is_session(cursor):
                out.append(cursor)
            cursor += dt.timedelta(days=1)
        return out
