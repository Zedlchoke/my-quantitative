"""TrueFX historical monthly tick archive adapter (DISCOVERY_ONLY).

Archive layout (documented public format): monthly ZIP archives under
``https://www.truefx.com/dev/data/YYYY-MM/{PAIR}-YYYY-MM.zip`` whose single
CSV member carries lines like::

    USD/JPY,20240102 00:00:00.123,141.085,141.115

(pair, GMT timestamp, bid, ask).

Fail-closed contracts implemented here:

- pair spellings ("usd/jpy", "USDJPY", "USD-JPY") normalize to ISO 3-letter
  base/quote with ``base != quote``; the request identity is deterministic
  across spellings;
- the archive must contain exactly one CSV member; multi-member or non-ZIP
  bodies are refused, never partially parsed;
- every tick row is validated: exactly 4 columns, pair match, TrueFX GMT
  timestamp in the archive month, ``0 < bid <= ask`` (crossed quotes are
  refused), and duplicate tick timestamps are refused;
- TrueFX tick timestamps are GMT by specification, so they are attached to
  UTC explicitly and flagged with a note;
- a monthly archive carries no publication timestamp, so availability uses
  the END of the archive month (UTC) as a conservative
  ``DATE_ONLY_UPPER_BOUND``; exact availability is never claimed;
- the bid/ask feed is indicative top-of-book data: fields are named
  ``bid``/``ask`` under dataset ``top_of_book_ticks`` with unit ``PRICE``
  and must never be treated as executable broker prices;
- swap/rollover/financing-style fields are forbidden inference targets;
  TrueFX is not a swap or rollover authority;
- license/internal-use status is UNKNOWN/PENDING verification (see
  ``TRUEFX_evidence.md``): ``license_id`` is a pure label, and the adapter's
  authority verdict stays ``CANDIDATE_NOT_AUTHORIZED``.
"""

from __future__ import annotations

import calendar
import io
import math
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone

from ..authority import AuthorityStatus
from ..models import require_utc
from .base import (
    DUPLICATE_RECORD_ID,
    AdapterError,
    AdapterNote,
    AdapterOutput,
    AvailabilityBasis,
    RateLimitPolicy,
    RawResponse,
    ReleaseEvidence,
    RequestSpec,
    SCHEMA_INVARIANT_VIOLATED,
    SCHEMA_TIMESTAMP_INVALID,
    SCHEMA_VALUE_TYPE_MISMATCH,
    SourceAdapter,
    end_of_utc_day,
    timings_from_evidence,
    validate_response,
)

# Stable note codes carried on every successful parse.
TRUEFX_GMT_PARSED_AS_UTC = "TRUEFX_GMT_PARSED_AS_UTC"
TRUEFX_MONTH_END_UPPER_BOUND = "TRUEFX_MONTH_END_UPPER_BOUND"
TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY = "TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY"
TRUEFX_INDICATIVE_TOP_OF_BOOK_ONLY = "TRUEFX_INDICATIVE_TOP_OF_BOOK_ONLY"
TRUEFX_ARCHIVE_MEMBER = "TRUEFX_ARCHIVE_MEMBER"

_TRUEFX_BASE_URL = "https://www.truefx.com"
_TICK_TIMESTAMP_FORMAT = "%Y%m%d %H:%M:%S.%f"
# TrueFX serves the monthly archives as ZIP; accept the common ZIP content
# types only.  Anything else (HTML error pages, JSON) is refused.
_ARCHIVE_CONTENT_TYPES: tuple[str, ...] = (
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream",
)

# Dataset naming states the role boundary explicitly: these are indicative
# top-of-book quote ticks, never executable broker prices.
TOP_OF_BOOK_TICKS_DATASET = "top_of_book_ticks"
PRICE_UNIT = "PRICE"


@dataclass(frozen=True, slots=True)
class TruefxTick:
    """One validated tick row (GMT timestamp attached to UTC)."""

    timestamp_utc: datetime
    bid: float
    ask: float


class TruefxAdapter(SourceAdapter):
    source_id = "TRUEFX"
    parser_version = "truefx-adapter-1.0.0"
    # Pure label only: internal-use terms are UNKNOWN/PENDING; this string
    # carries no authorization meaning (see TRUEFX_evidence.md).
    license_id = "truefx-internal-use-v1"
    entitlement_id = "anonymous-public-archive-no-key"
    authority_status = AuthorityStatus.CANDIDATE_NOT_AUTHORIZED
    forbidden_fields = ("swap", "swap_rate", "rollover", "tom_next", "financing")

    @classmethod
    def default_rate_limit(cls) -> RateLimitPolicy:
        return RateLimitPolicy(
            source_id=cls.source_id,
            documented_limit="TrueFX public monthly ZIP archives; large files, no bulk fan-out",
            min_interval_seconds=2.0,
            max_retries=1,
            retry_backoff_seconds=5.0,
            retry_status_codes=(429, 500, 502, 503),
        )

    # ------------------------------------------------------------------
    # Pair and archive-month normalization
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_pair(pair: str) -> tuple[str, str]:
        """Normalize a currency-pair spelling to (base, quote) ISO codes.

        Accepts "usd/jpy", "USDJPY", "USD-JPY" (and "USD_JPY"); anything
        that is not exactly two alphabetic 3-letter codes with differing
        base and quote is refused.
        """

        if not isinstance(pair, str):
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, "pair must be a string")
        text = pair.strip().upper()
        if "/" in text:
            base, _, quote = text.partition("/")
        elif "-" in text or "_" in text:
            base = text[:3]
            quote = text[4:]
        else:
            base, quote = text[:3], text[3:]
        base = base.strip()
        quote = quote.strip()
        for name, code in (("base", base), ("quote", quote)):
            if len(code) != 3 or not code.isalpha() or not code.isascii():
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"pair {pair!r} does not normalize to two ISO 3-letter currency codes "
                    f"({name}={code!r})",
                )
        if base == quote:
            raise AdapterError(
                SCHEMA_INVARIANT_VIOLATED,
                f"pair {pair!r} has identical base and quote currencies",
            )
        return base, quote

    @staticmethod
    def _archive_month(year: int, month: int) -> tuple[date, date]:
        """Validate (year, month) and return (first_day, last_day)."""

        if not isinstance(year, int) or isinstance(year, bool):
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, "archive year must be an integer")
        if not isinstance(month, int) or isinstance(month, bool):
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, "archive month must be an integer")
        if not 1 <= month <= 12:
            raise AdapterError(SCHEMA_INVARIANT_VIOLATED, f"archive month {month} out of range 1..12")
        try:
            first_day = date(year, month, 1)
            last_day = date(year, month, calendar.monthrange(year, month)[1])
        except ValueError as exc:
            raise AdapterError(SCHEMA_INVARIANT_VIOLATED, f"{year}-{month:02d} is not a real month: {exc}")
        return first_day, last_day

    @staticmethod
    def _month_end_evidence(year: int, month: int) -> ReleaseEvidence:
        """Conservative availability evidence for a monthly archive.

        TrueFX publishes no publication timestamp for a monthly archive, so
        the archive cannot be treated as available before the end of its own
        month (UTC).  This is an upper bound only — never an exact claim.
        """

        _, last_day = TruefxAdapter._archive_month(year, month)
        return ReleaseEvidence(
            captured_from=(
                "TrueFX monthly archive layout: no publication timestamp is published; "
                f"upper bound taken as end of archive month {year}-{month:02d} (UTC)"
            ),
            available_time_utc=end_of_utc_day(last_day),
            basis=AvailabilityBasis.DATE_ONLY_UPPER_BOUND,
        )

    # ------------------------------------------------------------------
    # Request construction
    # ------------------------------------------------------------------

    def build_monthly_archive_request(self, pair: str, year: int, month: int) -> RequestSpec:
        """Deterministic HTTPS GET for the documented monthly archive URL."""

        base, quote = self.normalize_pair(pair)
        _, _ = self._archive_month(year, month)
        stem = f"{year}-{month:02d}"
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_TRUEFX_BASE_URL}/dev/data/{stem}/{base}{quote}-{stem}.zip",
        )

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def parse_archive(
        self,
        response: RawResponse,
        *,
        pair: str,
        year: int,
        month: int,
    ) -> AdapterOutput:
        """Parse a monthly ZIP archive response into normalized tick records."""

        validate_response(response, allowed_content_types=_ARCHIVE_CONTENT_TYPES)
        base, quote = self.normalize_pair(pair)
        self._archive_month(year, month)
        try:
            with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
                members = archive.namelist()
                if len(members) != 1:
                    raise AdapterError(
                        SCHEMA_INVARIANT_VIOLATED,
                        f"TrueFX monthly archive must contain exactly one member, found {len(members)}",
                    )
                member_name = members[0]
                if not member_name.lower().endswith(".csv"):
                    raise AdapterError(
                        SCHEMA_INVARIANT_VIOLATED,
                        f"TrueFX archive member {member_name!r} is not the documented CSV member",
                    )
                try:
                    text = archive.read(member_name).decode("ascii")
                except UnicodeDecodeError as exc:
                    raise AdapterError(
                        SCHEMA_VALUE_TYPE_MISMATCH,
                        f"TrueFX archive member {member_name!r} is not ASCII CSV: {exc}",
                    )
        except zipfile.BadZipFile as exc:
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"response body is not a ZIP archive: {exc}")

        entity_id, ticks = self.parse_tick_csv(text, pair=pair, year=year, month=month)

        evidence = self._month_end_evidence(year, month)
        request_id = response.request_id
        raw_sha256 = response.sha256_hex()
        records = []
        for tick in ticks:
            timings = timings_from_evidence(tick.timestamp_utc, evidence, effective_time_utc=None)
            for field_name, value in (("bid", tick.bid), ("ask", tick.ask)):
                records.append(
                    self.make_record(
                        dataset_id=TOP_OF_BOOK_TICKS_DATASET,
                        entity_id=entity_id,
                        field_name=field_name,
                        value=value,
                        unit=PRICE_UNIT,
                        timings=timings,
                        retrieved_time_utc=response.retrieved_time_utc,
                        request_id=request_id,
                        raw_sha256=raw_sha256,
                    )
                )

        stem = f"{year}-{month:02d}"
        notes = [
            AdapterNote(
                TRUEFX_GMT_PARSED_AS_UTC,
                "TrueFX tick timestamps are GMT by specification; parsed as naive and attached to UTC",
            ),
            AdapterNote(
                TRUEFX_MONTH_END_UPPER_BOUND,
                "monthly archive publishes no availability timestamp; available_time_utc is the "
                "END of the archive month (UTC) as a DATE_ONLY_UPPER_BOUND, never an exact claim",
            ),
            AdapterNote(
                TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY,
                "TrueFX indicative bid/ask never authorizes swap, rollover, tom_next or financing values",
            ),
            AdapterNote(
                TRUEFX_INDICATIVE_TOP_OF_BOOK_ONLY,
                f"dataset {TOP_OF_BOOK_TICKS_DATASET!r} with unit {PRICE_UNIT!r}: indicative "
                "top-of-book quotes from a non-broker feed, never executable broker prices",
            ),
            AdapterNote(
                TRUEFX_ARCHIVE_MEMBER,
                f"parsed single CSV member {member_name!r} from archive "
                f"{base}{quote}-{stem}.zip (raw_sha256={raw_sha256})",
            ),
        ]
        return self.make_output(
            dataset_id=TOP_OF_BOOK_TICKS_DATASET,
            request_id=request_id,
            response=response,
            records=records,
            notes=notes,
        )

    def parse_tick_csv(
        self,
        text: str,
        *,
        pair: str,
        year: int,
        month: int,
    ) -> tuple[str, list[TruefxTick]]:
        """Validate TrueFX tick CSV rows; return (entity_id, ticks).

        Any violated invariant raises :class:`AdapterError` — rows are never
        coerced, skipped silently or repaired.
        """

        base, quote = self.normalize_pair(pair)
        self._archive_month(year, month)
        expected_pair = f"{base}/{quote}"
        entity_id = f"FX:{base}{quote}"

        ticks: list[TruefxTick] = []
        seen_timestamps: set[datetime] = set()
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            columns = line.split(",")
            if len(columns) != 4:
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"tick line {line_number} has {len(columns)} columns, expected 4",
                )
            line_pair, timestamp_text, bid_text, ask_text = (column.strip() for column in columns)

            if line_pair != expected_pair:
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"tick line {line_number} pair {line_pair!r} does not match {expected_pair!r}",
                )

            try:
                naive = datetime.strptime(timestamp_text, _TICK_TIMESTAMP_FORMAT)
            except ValueError:
                raise AdapterError(
                    SCHEMA_TIMESTAMP_INVALID,
                    f"tick line {line_number} timestamp {timestamp_text!r} is not in TrueFX GMT "
                    f"format {_TICK_TIMESTAMP_FORMAT!r}",
                )
            tick_utc = require_utc(
                naive.replace(tzinfo=timezone.utc),
                f"tick line {line_number} timestamp",
            )
            if (tick_utc.year, tick_utc.month) != (year, month):
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"tick line {line_number} timestamp {timestamp_text!r} falls outside archive "
                    f"month {year}-{month:02d}",
                )
            if tick_utc in seen_timestamps:
                raise AdapterError(
                    DUPLICATE_RECORD_ID,
                    f"tick line {line_number} timestamp {timestamp_text!r} duplicates an earlier tick",
                )
            seen_timestamps.add(tick_utc)

            try:
                bid = float(bid_text)
                ask = float(ask_text)
            except ValueError:
                raise AdapterError(
                    SCHEMA_VALUE_TYPE_MISMATCH,
                    f"tick line {line_number} prices ({bid_text!r}, {ask_text!r}) are not numeric",
                )
            if not (math.isfinite(bid) and math.isfinite(ask)):
                raise AdapterError(
                    SCHEMA_VALUE_TYPE_MISMATCH,
                    f"tick line {line_number} prices must be finite, got ({bid!r}, {ask!r})",
                )
            if bid <= 0 or ask <= 0:
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"tick line {line_number} violates bid > 0 and ask > 0 ({bid!r}, {ask!r})",
                )
            if bid > ask:
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"tick line {line_number} is a crossed quote (bid {bid!r} > ask {ask!r}); "
                    "crossed quotes are refused",
                )

            ticks.append(TruefxTick(timestamp_utc=tick_utc, bid=bid, ask=ask))

        return entity_id, ticks
