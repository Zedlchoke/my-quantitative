"""FINRA Reg SHO daily short-sale-volume adapter (DISCOVERY_ONLY).

The daily file is pipe-separated with a fixed header:
``Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market``.

Inference guards: short-sale volume is never short interest, never borrow
fee, never utilization.  Publication timestamps are not in the file, so
availability is an end-of-trade-day UTC upper bound and never an exact
market availability claim.
"""

from __future__ import annotations

from datetime import date

from ..authority import AuthorityStatus
from .base import (
    AdapterError,
    AdapterNote,
    AdapterOutput,
    AvailabilityBasis,
    RateLimitPolicy,
    RawResponse,
    ReleaseEvidence,
    RequestSpec,
    SourceAdapter,
    end_of_utc_day,
    midnight_utc,
    timings_from_evidence,
)

FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY = "FINRA_DATE_ONLY_NOT_EXACT_AVAILABILITY"
FINRA_SHORT_SALE_NOT_SHORT_INTEREST = "FINRA_SHORT_SALE_NOT_SHORT_INTEREST"

_BASE = "https://cdn.finra.org"
_HEADER = "Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market"
_TIERS = {"nms": "equity/regsho/nms", "otc": "equity/otcmarket/biweekly"}


class FinraAdapter(SourceAdapter):
    source_id = "FINRA_SHORT"
    parser_version = "finra-adapter-1.0.0"
    license_id = "finra-attribution-required-v1"
    entitlement_id = "anonymous-no-key"
    authority_status = AuthorityStatus.DOCUMENTED_CANDIDATE
    forbidden_fields = ("short_interest", "borrow_fee", "utilization")

    @classmethod
    def default_rate_limit(cls) -> RateLimitPolicy:
        return RateLimitPolicy(
            source_id=cls.source_id,
            documented_limit="FINRA public files; keep request spacing conservative",
            min_interval_seconds=1.0,
            max_retries=2,
            retry_backoff_seconds=2.0,
            retry_status_codes=(429, 500, 502, 503),
        )

    def build_daily_short_sale_request(self, trade_date: date, *, tier: str = "nms") -> RequestSpec:
        if tier not in _TIERS:
            raise AdapterError("SCHEMA_INVARIANT_VIOLATED", f"tier must be one of {sorted(_TIERS)}")
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/{_TIERS[tier]}/shrt{trade_date.strftime('%Y%m%d')}",
        )

    def parse_daily_short_sale(self, response: RawResponse, *, trade_date: date) -> AdapterOutput:
        try:
            text = response.body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AdapterError("SCHEMA_VALUE_TYPE_MISMATCH", f"file is not UTF-8 text: {exc}")
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines or lines[0] != _HEADER:
            raise AdapterError("SCHEMA_FIELD_MISSING", f"unexpected header, expected {_HEADER!r}")

        records: list = []
        seen: set[tuple[str, str]] = set()
        entity_note_symbols = set()
        for line_number, line in enumerate(lines[1:], start=2):
            columns = line.split("|")
            if len(columns) != 6:
                raise AdapterError(
                    "SCHEMA_INVARIANT_VIOLATED",
                    f"line {line_number} has {len(columns)} columns, expected 6",
                )
            row_date, raw_symbol, short_volume, short_exempt, total_volume, market = columns
            if row_date != trade_date.isoformat():
                raise AdapterError(
                    "SCHEMA_INVARIANT_VIOLATED",
                    f"line {line_number} date {row_date!r} does not match requested {trade_date.isoformat()}",
                )
            symbol = raw_symbol.strip().upper()
            if not symbol or any(character.isspace() for character in symbol):
                raise AdapterError("SCHEMA_INVARIANT_VIOLATED", f"line {line_number} has an invalid symbol")
            volumes = {
                "short_volume": self._parse_volume(short_volume, line_number),
                "short_exempt_volume": self._parse_volume(short_exempt, line_number),
                "total_volume": self._parse_volume(total_volume, line_number),
            }
            if volumes["short_exempt_volume"] > volumes["short_volume"]:
                raise AdapterError(
                    "SCHEMA_INVARIANT_VIOLATED",
                    f"line {line_number}: short exempt volume exceeds short volume",
                )
            if volumes["short_volume"] > volumes["total_volume"]:
                raise AdapterError(
                    "SCHEMA_INVARIANT_VIOLATED",
                    f"line {line_number}: short volume exceeds total volume",
                )
            market_code = market.strip().upper()
            if not market_code:
                raise AdapterError("SCHEMA_INVARIANT_VIOLATED", f"line {line_number} has an empty market")
            entity_id = f"FINRA:{symbol}"
            entity_note_symbols.add(symbol)
            evidence = ReleaseEvidence(
                captured_from="FINRA daily file trade date (date only)",
                available_time_utc=end_of_utc_day(trade_date),
                basis=AvailabilityBasis.DATE_ONLY_UPPER_BOUND,
            )
            timings = timings_from_evidence(
                midnight_utc(trade_date), evidence, effective_time_utc=midnight_utc(trade_date)
            )
            for field_name, value in volumes.items():
                key = (symbol, field_name)
                if key in seen:
                    raise AdapterError("DUPLICATE_RECORD_ID", f"duplicate row for {key}")
                seen.add(key)
                records.append(
                    self.make_record(
                        dataset_id="short_sale_volume_daily",
                        entity_id=entity_id,
                        field_name=field_name,
                        value=value,
                        unit="SHARES",
                        timings=timings,
                        retrieved_time_utc=response.retrieved_time_utc,
                        request_id=response.request_id,
                        raw_sha256=response.sha256_hex(),
                    )
                )
            if (symbol, "market") in seen:
                raise AdapterError("DUPLICATE_RECORD_ID", f"duplicate market row for {symbol}")
            seen.add((symbol, "market"))
            records.append(
                self.make_record(
                    dataset_id="short_sale_volume_daily",
                    entity_id=entity_id,
                    field_name="market",
                    value=market_code,
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
                "availability uses the end of the trade UTC day as a conservative upper bound",
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

    @staticmethod
    def _parse_volume(text: str, line_number: int) -> int:
        value = text.strip()
        if not value.isdigit():
            raise AdapterError(
                "SCHEMA_VALUE_TYPE_MISMATCH", f"line {line_number} volume {value!r} is not a non-negative integer"
            )
        return int(value)
