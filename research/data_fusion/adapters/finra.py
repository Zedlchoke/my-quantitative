"""FINRA Reg SHO daily short-sale-volume adapter (DISCOVERY_ONLY).

Lane owner: A2 stocks.  Coded against the A1-owned shared foundation in
``research.data_fusion.adapters.base``.

Files (anonymous, no key, no account):

- daily equity NMS: ``https://cdn.finra.org/equity/regsho/nms/shrtYYYYMMDD``
- biweekly OTC equity: ``https://cdn.finra.org/equity/otcmarket/biweekly/shrtYYYYMMDD``

File format (pipe separated, fixed header)::

    Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market

Fail-closed contracts owned by this module:

- the header must match exactly, every data row must have exactly 6 columns,
  every row date must equal the requested trade date;
- volumes must be ASCII non-negative integers with
  ``short_exempt_volume <= short_volume <= total_volume``;
- a repeated symbol is a duplicate record and is refused, never merged;
- the trade date is date-only evidence: available_time is the end of the
  trade UTC day as a conservative *upper bound*, never an exact market
  availability claim (note ``FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY``);
- inference guard: short-sale volume is NEVER short interest, borrow fee or
  utilization.  ``forbidden_fields`` enforces it at record construction and
  the note ``FINRA_SHORT_SALE_NOT_SHORT_INTEREST`` documents it;
- retrieved_time never substitutes for available_time.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import ClassVar

from ..authority import AuthorityStatus
from .base import (
    AdapterError,
    AdapterNote,
    AdapterOutput,
    AvailabilityBasis,
    DUPLICATE_RECORD_ID,
    RateLimitPolicy,
    RawResponse,
    ReleaseEvidence,
    RequestSpec,
    SCHEMA_FIELD_MISSING,
    SCHEMA_INVARIANT_VIOLATED,
    SCHEMA_VALUE_TYPE_MISMATCH,
    SourceAdapter,
    end_of_utc_day,
    midnight_utc,
    timings_from_evidence,
    validate_response,
)

FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY = "FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY"
FINRA_SHORT_SALE_NOT_SHORT_INTEREST = "FINRA_SHORT_SALE_NOT_SHORT_INTEREST"

_BASE = "https://cdn.finra.org"
_TIERS: dict[str, str] = {
    "nms": "equity/regsho/nms",
    "otc": "equity/otcmarket/biweekly",
}
_HEADER = "Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market"
_COLUMN_COUNT = 6


class FinraAdapter(SourceAdapter):
    """Adapter for FINRA daily/biweekly short-sale-volume files."""

    source_id = "FINRA_SHORT"
    parser_version = "finra-adapter-1.0.0"
    license_id = "finra-attribution-required-v1"
    entitlement_id = "anonymous-no-key"
    authority_status = AuthorityStatus.DOCUMENTED_CANDIDATE
    # Inference guard: this source must never be mapped onto these fields.
    forbidden_fields: ClassVar[tuple[str, ...]] = (
        "short_interest",
        "borrow_fee",
        "utilization",
    )

    @classmethod
    def default_rate_limit(cls) -> RateLimitPolicy:
        return RateLimitPolicy(
            source_id=cls.source_id,
            documented_limit=(
                "FINRA public file downloads; no numeric limit is published, "
                "client keeps a conservative 1 request/second spacing"
            ),
            min_interval_seconds=1.0,
            max_retries=2,
            retry_backoff_seconds=2.0,
            retry_status_codes=(429, 500, 502, 503),
        )

    # -- request construction -------------------------------------------------

    def build_short_sale_request(self, trade_date: date, *, tier: str = "nms") -> RequestSpec:
        tier_path = _TIERS.get(tier)
        if tier_path is None:
            raise AdapterError(
                SCHEMA_INVARIANT_VIOLATED, f"tier must be one of {sorted(_TIERS)}, got {tier!r}"
            )
        day = self._require_plain_date(trade_date, "trade_date")
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/{tier_path}/shrt{day.strftime('%Y%m%d')}",
        )

    # -- parsing ---------------------------------------------------------------

    def parse_short_sale(self, response: RawResponse, *, trade_date: date) -> AdapterOutput:
        validate_response(response, allowed_content_types=("text/plain",))
        day = self._require_plain_date(trade_date, "trade_date")
        try:
            text = response.body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AdapterError(SCHEMA_VALUE_TYPE_MISMATCH, f"file is not UTF-8 text: {exc}")

        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise AdapterError(SCHEMA_FIELD_MISSING, "file has no header row")
        if lines[0] != _HEADER:
            raise AdapterError(
                SCHEMA_FIELD_MISSING,
                f"file header must be exactly {_HEADER!r}, got {lines[0]!r}",
            )

        evidence = ReleaseEvidence(
            captured_from="FINRA short-sale file trade date (date only)",
            available_time_utc=end_of_utc_day(day),
            basis=AvailabilityBasis.DATE_ONLY_UPPER_BOUND,
        )
        timings = timings_from_evidence(
            midnight_utc(day), evidence, effective_time_utc=midnight_utc(day)
        )

        records: list = []
        seen_symbols: set[str] = set()
        for line_number, line in enumerate(lines[1:], start=2):
            columns = line.split("|")
            if len(columns) != 6:
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"line {line_number} has {len(columns)} columns, expected 6",
                )
            row_date, raw_symbol, short_text, exempt_text, total_text, raw_market = columns
            if row_date != day.isoformat():
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"line {line_number} date {row_date!r} does not match requested "
                    f"{day.isoformat()}",
                )
            symbol = raw_symbol.strip()
            if not symbol or symbol != symbol.upper() or any(c.isspace() for c in symbol):
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"line {line_number} symbol {raw_symbol!r} is not a bare uppercase token",
                )
            if symbol in seen_symbols:
                raise AdapterError(
                    DUPLICATE_RECORD_ID,
                    f"line {line_number}: symbol {symbol!r} appears twice in the file",
                )
            seen_symbols.add(symbol)

            volumes = {
                "short_volume": self._parse_volume(short_text, "ShortVolume", line_number),
                "short_exempt_volume": self._parse_volume(
                    exempt_text, "ShortExemptVolume", line_number
                ),
                "total_volume": self._parse_volume(total_text, "TotalVolume", line_number),
            }
            if volumes["short_exempt_volume"] > volumes["short_volume"]:
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"line {line_number}: short exempt volume exceeds short volume",
                )
            if volumes["short_volume"] > volumes["total_volume"]:
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"line {line_number}: short volume exceeds total volume",
                )
            market = raw_market.strip()
            if len(market) != 1 or not ("A" <= market <= "Z"):
                raise AdapterError(
                    SCHEMA_INVARIANT_VIOLATED,
                    f"line {line_number} market {raw_market!r} is not a single uppercase letter",
                )

            for field_name in ("short_volume", "short_exempt_volume", "total_volume"):
                records.append(
                    self.make_record(
                        dataset_id="short_sale_volume_daily",
                        entity_id=f"FINRA:{symbol}",
                        field_name=field_name,
                        value=volumes[field_name],
                        unit="SHARES",
                        timings=timings,
                        retrieved_time_utc=response.retrieved_time_utc,
                        request_id=response.request_id,
                        raw_sha256=response.sha256_hex(),
                    )
                )
            records.append(
                self.make_record(
                    dataset_id="short_sale_volume_daily",
                    entity_id=f"FINRA:{symbol}",
                    field_name="market",
                    value=market,
                    unit="MARKET_CODE",
                    timings=timings,
                    retrieved_time_utc=response.retrieved_time_utc,
                    request_id=response.request_id,
                    raw_sha256=response.sha256_hex(),
                )
            )

        notes = [
            AdapterNote(
                FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY,
                "availability is the end of the trade UTC day: a conservative "
                "upper bound, never an exact market availability claim",
            ),
            AdapterNote(
                FINRA_SHORT_SALE_NOT_SHORT_INTEREST,
                "short-sale volume is never short interest, borrow fee or utilization",
            ),
        ]
        return self.make_output(
            dataset_id="short_sale_volume_daily",
            request_id=response.request_id,
            response=response,
            records=records,
            notes=notes,
        )

    # -- helpers ---------------------------------------------------------------

    @staticmethod
    def _require_plain_date(value: object, name: str) -> date:
        if isinstance(value, datetime) or not isinstance(value, date):
            raise AdapterError(
                SCHEMA_VALUE_TYPE_MISMATCH,
                f"{name} must be a datetime.date, not a datetime or other type",
            )
        return value

    @staticmethod
    def _parse_volume(text: str, field_name: str, line_number: int) -> int:
        if not text or not all(c in "0123456789" for c in text):
            raise AdapterError(
                SCHEMA_VALUE_TYPE_MISMATCH,
                f"line {line_number} {field_name} {text!r} is not a non-negative integer",
            )
        return int(text)
