"""Forex adapter context — pair identity, provider clock, session rule (A6).

Freeze authority: research/control/market_data_plane_v2_run/architecture_freeze_v2.json
(p3_wave_sha 09a223f6ce166e219beb67b25b8151361979ca21), section
``"adapters" -> "forex"``:

* identity: "canonical pair identity base/quote from provider symbol;
  instrument_id 'EUR/USD' form; venue from adapter context" — the pair
  identity is DECLARED in the context table and never derived by string
  surgery at runtime;
* clock: "provider timezone -> UTC with explicit DST fixtures" — conversion
  is zoneinfo-based and fold-aware; ambiguous (fall-back) and imaginary
  (spring-forward) local wall times are REJECTED fail-closed, never guessed;
* session rule: the frozen synthetic weekly session — market closed from
  Friday 21:00 UTC until Sunday 21:00 UTC unless the context overrides;
* default interval 1h; price precision and normalizer version carried here.

Adapter-local reason codes (``FOREX_ADAPTER_REASON_CODES``) classify
quarantine entries only.  They deliberately live OUTSIDE the frozen
reason_codes@1 + mdp.bar_reason_codes@2 registries and can therefore never
appear inside a bar's ``reason_codes`` (module assertion + test-enforced);
where a frozen code fits (``UNKNOWN_INSTRUMENT``, ``MISSING_REQUIRED_FIELD``,
``MALFORMED_SHAPE``) the frozen code is used.

stdlib only.  This module never mutates its inputs.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from market_data_plane import bars as _bars

# --- frozen constants -------------------------------------------------------

#: Default bar interval: 1 hour in nanoseconds (frozen interface default).
DEFAULT_INTERVAL_NS: int = 3_600_000_000_000

#: Frozen synthetic weekly session rule name: market closed from Friday
#: 21:00 UTC until Sunday 21:00 UTC (architecture_freeze_v2.json
#: adapters.forex clock rule; the context may override with a callable).
DEFAULT_SESSION_RULE_NAME = "WEEKLY_CLOSED_FRI_2100_TO_SUN_2100_UTC"

#: Seconds per day (UTC session arithmetic).
_NS_PER_SECOND = 1_000_000_000
_NS_PER_MINUTE = 60 * _NS_PER_SECOND
_NS_PER_HOUR = 60 * _NS_PER_MINUTE
_SECONDS_PER_DAY = 86_400

#: 1970-01-01 was a Thursday; Monday=0 weekday of an epoch day offset.
_EPOCH_WEEKDAY_OFFSET = 3

#: Adapter-local reason codes: quarantine classification ONLY.  Never bar
#: reason_codes (see module docstring; disjointness is asserted below and
#: test-enforced).
FOREX_ADAPTER_REASON_CODES: tuple[str, ...] = (
    "FOREX_MACRO_DATE_ONLY_ROW",
    "FOREX_FORBIDDEN_MICROSTRUCTURE_FIELD",
    "FOREX_AMBIGUOUS_LOCAL_TIME",
    "FOREX_IMAGINARY_LOCAL_TIME",
    "FOREX_PROVIDER_TZ_MISMATCH",
)

assert frozenset(FOREX_ADAPTER_REASON_CODES).isdisjoint(_bars.ALL_BAR_REASON_CODES)


# --- error family ------------------------------------------------------------

class ForexAdapterError(_bars.BarError):
    """Adapter-contract rejection carrying an adapter-local reason code.

    Subclasses :class:`market_data_plane.bars.BarError` so one ``except
    BarError`` catches the whole adapter family, but bypasses the frozen
    bar-reason-code registry check ON PURPOSE: the ``FOREX_*`` codes classify
    adapter quarantine entries and are barred from the bar model itself
    (``bars.validate_bar`` rejects them if anyone attempts to smuggle them
    into a bar's ``reason_codes``).
    """

    def __init__(self, reason_code: str, message: str):
        if reason_code not in FOREX_ADAPTER_REASON_CODES:
            raise AssertionError(
                f"internal error: {reason_code!r} is not a FOREX adapter code")
        ValueError.__init__(self, f"[{reason_code}] {message}")
        self.reason_code = reason_code


# --- pair identity (declared, never derived) -----------------------------------

@dataclass(frozen=True)
class PairIdentity:
    """Canonical declared pair identity: base/quote + 'BASE/QUOTE' id."""

    base: str
    quote: str
    instrument_id: str

    def __post_init__(self):
        for field in ("base", "quote", "instrument_id"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value:
                raise ValueError(f"PairIdentity.{field} must be a non-empty string")
        expected = f"{self.base}/{self.quote}"
        if self.instrument_id != expected:
            raise ValueError(
                f"PairIdentity.instrument_id must be the canonical "
                f"'BASE/QUOTE' form ({expected!r}), got {self.instrument_id!r}")


#: The declared EUR/USD table: both provider spellings map to ONE canonical
#: identity.  Pair identity comes from THIS table — never from string surgery.
EURUSD_PAIR_TABLE: Mapping[str, PairIdentity] = MappingProxyType({
    "EUR_USD": PairIdentity(base="EUR", quote="USD", instrument_id="EUR/USD"),
    "EURUSD": PairIdentity(base="EUR", quote="USD", instrument_id="EUR/USD"),
})


# --- session rules -------------------------------------------------------------

def session_closed_weekly_fri21_sun21_utc(open_ns: int) -> bool:
    """Frozen synthetic weekly session: closed Fri 21:00Z -> Sun 21:00Z.

    Classified at the slot OPEN instant in UTC (exact integer arithmetic, no
    float timestamps).  The closure interval is half-open [Fri 21:00Z,
    Sun 21:00Z): Friday 21:00 is closed, Sunday 21:00 is open.
    """
    seconds, _ = divmod(int(open_ns), _NS_PER_SECOND)
    days, seconds_of_day = divmod(seconds, _SECONDS_PER_DAY)
    weekday = (days + _EPOCH_WEEKDAY_OFFSET) % 7  # Monday=0 .. Sunday=6
    minute_of_day = seconds_of_day // 60
    if weekday == 4:  # Friday
        return minute_of_day >= 21 * 60
    if weekday == 5:  # Saturday
        return True
    if weekday == 6:  # Sunday
        return minute_of_day < 21 * 60
    return False


_SESSION_RULES: Mapping[str, object] = MappingProxyType({
    DEFAULT_SESSION_RULE_NAME: session_closed_weekly_fri21_sun21_utc,
})


def resolve_session_rule(session_rule) -> object:
    """Resolve the context session rule to a callable (int ns -> bool)."""
    if callable(session_rule):
        return session_rule
    if isinstance(session_rule, str):
        rule = _SESSION_RULES.get(session_rule)
        if rule is None:
            raise ValueError(
                f"unknown session rule {session_rule!r}; known rules: "
                f"{sorted(_SESSION_RULES)} or pass a callable")
        return rule
    raise ValueError(
        "session_rule must be a known rule name or a callable(int ns) -> bool")


# --- provider clock: zoneinfo DST handling ---------------------------------------

def load_provider_timezone(tz_name: str) -> ZoneInfo:
    """Load + validate the IANA provider timezone name (fail closed)."""
    if not isinstance(tz_name, str) or not tz_name:
        raise ValueError("provider timezone must be a non-empty IANA name")
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"unknown IANA timezone {tz_name!r}") from exc


def _parse_local_wall_time(ts: str) -> datetime:
    if not isinstance(ts, str):
        raise _bars.BarError(
            "MALFORMED_SHAPE", "provider ts must be an ISO-8601 local wall-time string")
    try:
        naive = datetime.fromisoformat(ts)
    except ValueError as exc:
        raise _bars.BarError(
            "MALFORMED_SHAPE", f"unparseable provider ts {ts!r}") from exc
    if naive.tzinfo is not None:
        raise _bars.BarError(
            "MALFORMED_SHAPE",
            "provider ts must be a local wall time without offset; the tz name "
            "field (and the context provider_timezone) govern the conversion")
    return naive


def local_wall_to_utc_ns(ts: str, tz: ZoneInfo) -> int:
    """Provider-local wall time -> integer UTC ns, fold-aware, fail-closed.

    Raises :class:`ForexAdapterError`:

    * ``FOREX_AMBIGUOUS_LOCAL_TIME`` — the local time occurs twice (fall-back
      DST boundary); converting would be a guess, so it is rejected;
    * ``FOREX_IMAGINARY_LOCAL_TIME`` — the local time does not exist
      (spring-forward DST boundary); rejected by UTC round-trip.

    Unparseable or offset-bearing ``ts`` raises ``MALFORMED_SHAPE``
    (:class:`market_data_plane.bars.BarError`).
    """
    naive = _parse_local_wall_time(ts)
    fold0 = naive.replace(tzinfo=tz, fold=0)
    fold1 = naive.replace(tzinfo=tz, fold=1)

    def _roundtrips(aware: datetime) -> bool:
        return aware.astimezone(timezone.utc).astimezone(tz).replace(
            tzinfo=None) == naive

    if not (_roundtrips(fold0) or _roundtrips(fold1)):
        raise ForexAdapterError(
            "FOREX_IMAGINARY_LOCAL_TIME",
            f"local time {ts!r} does not exist in {str(tz)} (spring-forward "
            f"boundary); rejecting instead of guessing")
    if fold0.utcoffset() != fold1.utcoffset():
        raise ForexAdapterError(
            "FOREX_AMBIGUOUS_LOCAL_TIME",
            f"local time {ts!r} is ambiguous in {str(tz)} (fall-back boundary; "
            f"occurs twice); rejecting instead of guessing a fold")
    utc = fold0.astimezone(timezone.utc)
    # Exact integer arithmetic (no float): days/seconds/micro -> ns.
    delta = utc - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return ((delta.days * 86_400 + delta.seconds) * 1_000_000
            + delta.microseconds) * 1000


def local_wall_fold_candidates_ns(ts: str, tz: ZoneInfo) -> tuple[int, ...]:
    """Both fold interpretations of a local wall time, as UTC ns candidates.

    Used ONLY by coverage diagnostics to correlate quarantined DST-boundary
    records with missing UTC slots (the record itself was already rejected —
    this never re-admits it).  Returns the distinct fold-0/fold-1 instants.
    """
    naive = _parse_local_wall_time(ts)
    candidates: list[int] = []
    for fold in (0, 1):
        aware = naive.replace(tzinfo=tz, fold=fold)
        utc = aware.astimezone(timezone.utc)
        delta = utc - datetime(1970, 1, 1, tzinfo=timezone.utc)
        candidates.append(((delta.days * 86_400 + delta.seconds) * 1_000_000
                           + delta.microseconds) * 1000)
    return tuple(sorted(set(candidates)))


# --- adapter context -------------------------------------------------------------

def _interval_label(interval_ns: int) -> str:
    if interval_ns % _NS_PER_HOUR == 0:
        return f"{interval_ns // _NS_PER_HOUR}h"
    if interval_ns % _NS_PER_MINUTE == 0:
        return f"{interval_ns // _NS_PER_MINUTE}m"
    return f"{interval_ns}ns"


def default_bar_type(interval_ns: int) -> str:
    """Deterministic neutral bar_type: OHLCV creates no bid/ask evidence."""
    return f"{_interval_label(interval_ns)}-OHLC"


@dataclass(frozen=True)
class AdapterContext:
    """Frozen forex adapter context (the A6 half of the frozen interface).

    Fields per the frozen interface: the declared pair table, venue,
    provider timezone (IANA), the frozen synthetic weekly session rule
    (overrideable), the default 1h interval, price precision and the
    normalizer version.  Provenance fields (``provider_id``/``source_id``)
    are required — declared provenance, never assumed; ``publication_lag_ns``
    is the frozen provider publication lag constant (default 0:
    available_time == close_time).
    """

    venue: str
    provider_id: str
    source_id: str
    provider_timezone: str
    pair_table: Mapping[str, PairIdentity]
    interval_ns: int = DEFAULT_INTERVAL_NS
    price_precision: int = 5
    size_precision: int = 2
    session_rule: object = DEFAULT_SESSION_RULE_NAME
    publication_lag_ns: int = 0
    manifest_sha256: str | None = None
    normalizer_version: str = "mdp-forex-ohlcv@2"
    bar_type: str | None = None

    def __post_init__(self):
        for field in ("venue", "provider_id", "source_id", "normalizer_version"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value:
                raise ValueError(f"AdapterContext.{field} must be a non-empty string")
        load_provider_timezone(self.provider_timezone)  # fail-closed IANA check

        table = dict(self.pair_table)
        if not table:
            raise ValueError("AdapterContext.pair_table must not be empty")
        for symbol, identity in table.items():
            if not isinstance(symbol, str) or not symbol:
                raise ValueError("pair table symbols must be non-empty strings")
            if not isinstance(identity, PairIdentity):
                raise ValueError(
                    f"pair table entry for {symbol!r} must be a PairIdentity")
        object.__setattr__(self, "pair_table", MappingProxyType(dict(table)))

        if not isinstance(self.interval_ns, int) or isinstance(self.interval_ns, bool) \
                or self.interval_ns <= 0:
            raise ValueError("AdapterContext.interval_ns must be an int > 0")
        for field in ("price_precision", "size_precision"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"AdapterContext.{field} must be an int >= 1")
        if not isinstance(self.publication_lag_ns, int) \
                or isinstance(self.publication_lag_ns, bool) \
                or self.publication_lag_ns < 0:
            raise ValueError("AdapterContext.publication_lag_ns must be an int >= 0")
        if self.bar_type is not None and (not isinstance(self.bar_type, str)
                                          or not self.bar_type):
            raise ValueError("AdapterContext.bar_type must be None or a non-empty string")
        # session rule resolved eagerly (fail closed on a bad rule name)
        object.__setattr__(self, "_resolved_session_rule",
                           resolve_session_rule(self.session_rule))

    # -- derived accessors ----------------------------------------------------

    @property
    def resolved_bar_type(self) -> str:
        return self.bar_type if self.bar_type is not None \
            else default_bar_type(self.interval_ns)

    def pair_identity(self, provider_symbol: str) -> PairIdentity:
        """DECLARED pair lookup — unknown symbols never get parsed/salvaged."""
        if not isinstance(provider_symbol, str) or not provider_symbol:
            raise _bars.BarError(
                "MALFORMED_SHAPE", "provider symbol must be a non-empty string")
        identity = self.pair_table.get(provider_symbol)
        if identity is None:
            raise _bars.BarError(
                "UNKNOWN_INSTRUMENT",
                f"provider symbol {provider_symbol!r} is not declared in the "
                f"adapter context pair table; pair identity is declared, never "
                f"derived by string surgery at runtime")
        return identity

    def is_session_closed(self, open_ns: int) -> bool:
        """Session calendar at a slot-open instant (bool, exact ns input)."""
        return bool(self._resolved_session_rule(open_ns))  # type: ignore[attr-defined]
