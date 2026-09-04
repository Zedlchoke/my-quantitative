"""TrueFX historical monthly tick archive adapter (DISCOVERY_ONLY).

Archive layout (documented by TrueFX): monthly ZIP archives under
``https://www.truefx.com/dev/data/YYYY-MM/{PAIR}-YYYY-MM.zip`` whose CSV
member lines look like ``USD/JPY,20240102 00:00:00.123,141.085,141.115``
(pair, GMT timestamp, bid, ask).

Guards:
- timestamps are GMT by specification and are parsed as UTC explicitly;
- a monthly archive cannot predate its own month end, so availability uses
  the end of the archive month as a conservative upper bound;
- TrueFX bid/ask is never a swap, rollover or financing authority.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import io
import calendar
import zipfile

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
    require_utc,
    timings_from_evidence,
)

TRUEFX_GMT_PARSED_AS_UTC = "TRUEFX_GMT_PARSED_AS_UTC"
TRUEFX_MONTH_END_UPPER_BOUND = "TRUEFX_MONTH_END_UPPER_BOUND"
TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY = "TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY"

_BASE = "https://www.truefx.com"


class TruefxAdapter(SourceAdapter):
    source_id = "TRUEFX"
    parser_version = "truefx-adapter-1.0.0"
    license_id = "truefx-internal-use-v1"
    entitlement_id = "anonymous-no-key"
    authority_status = AuthorityStatus.CANDIDATE_NOT_AUTHORIZED
    forbidden_fields = ("swap", "swap_rate", "rollover", "tom_next", "financing")

    @classmethod
    def default_rate_limit(cls) -> RateLimitPolicy:
        return RateLimitPolicy(
            source_id=cls.source_id,
            documented_limit="TrueFX public archives; large monthly ZIPs, no bulk fan-out",
            min_interval_seconds=2.0,
            max_retries=1,
            retry_backoff_seconds=5.0,
            retry_status_codes=(429, 500, 502, 503),
        )

    @staticmethod
    def normalize_pair(pair: str) -> tuple[str, str]:
        text = pair.strip().upper()
        if "/" in text:
            base, quote = text.split("/", 1)
        elif "-" in text and len(text) == 7:
            base, quote = text.split("-", 1)
        else:
            base, quote = text[:3], text[3:]
        for code in (base, quote):
            if len(code) != 3 or not code.isalpha():
                raise AdapterError("SCHEMA_INVARIANT_VIOLATED", f"pair {pair!r} is not an ISO currency pair")
        if base == quote:
            raise AdapterError("SCHEMA_INVARIANT_VIOLATED", "base and quote currencies must differ")
        return base, quote

    def build_monthly_archive_request(self, pair: str, year: int, month: int) -> RequestSpec:
        base, quote = self.normalize_pair(pair)
        if not 1 <= month <= 12:
            raise AdapterError("SCHEMA_INVARIANT_VIOLATED", f"month {month} out of range")
        stem = f"{year}-{month:02d}"
        return RequestSpec(
            source_id=self.source_id,
            url=f"{_BASE}/dev/data/{stem}/{base}{quote}-{stem}.zip",
        )

    def parse_archive(self, response: RawResponse, *, pair: str, year: int, month: int) -> AdapterOutput:
        try:
            with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
                members = archive.namelist()
                if len(members) != 1:
                    raise AdapterError(
                        "SCHEMA_INVARIANT_VIOLATED",
                        f"archive must contain exactly one member, found {len(members)}",
                    )
                text = archive.read(members[0]).decode("ascii")
        except zipfile.BadZipFile as exc:
            raise AdapterError("SCHEMA_VALUE_TYPE_MISMATCH", f"body is not a ZIP archive: {exc}")
        return self.parse_tick_csv(
            text,
            pair=pair,
            year=year,
            month=month,
            retrieved_time_utc=response.retrieved_time_utc,
            request_id=response.request_id,
            raw_sha256=response.sha256_hex(),
        )

    def parse_tick_csv(
        self,
        text: str,
        *,
        pair: str,
        year: int,
        month: int,
        retrieved_time_utc: datetime,
        request_id: str,
        raw_sha256: str,
    ) -> AdapterOutput:
        if not 1 <= month <= 12:
            raise AdapterError("SCHEMA_INVARIANT_VIOLATED", f"month {month} out of range")
        base, quote = self.normalize_pair(pair)
        expected_pair = f"{base}/{quote}"
        archive_day = date(year, month, calendar.monthrange(year, month)[1])
        evidence = ReleaseEvidence(
            captured_from="TrueFX monthly archive period (month end)",
            available_time_utc=end_of_utc_day(archive_day),
            basis=AvailabilityBasis.DATE_ONLY_UPPER_BOUND,
        )
        entity_id = f"FX:{base}{quote}"
        response_like = RawResponse(
            request_id=request_id,
            url=f"{_BASE}/dev/data/{year}-{month:02d}/{base}{quote}-{year}-{month:02d}.zip",
            status=200,
            reason="OK",
            headers=(),
            body=b"",
            retrieved_time_utc=retrieved_time_utc,
        )

        records: list = []
        seen_timestamps: set[datetime] = set()
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            columns = line.split(",")
            if len(columns) != 4:
                raise AdapterError(
                    "SCHEMA_INVARIANT_VIOLATED",
                    f"tick line {line_number} has {len(columns)} columns, expected 4",
                )
            line_pair, timestamp_text, bid_text, ask_text = (column.strip() for column in columns)
            if line_pair != expected_pair:
                raise AdapterError(
                    "SCHEMA_INVARIANT_VIOLATED",
                    f"tick line {line_number} pair {line_pair!r} does not match {expected_pair!r}",
                )
            try:
                tick = datetime.strptime(timestamp_text, "%Y%m%d %H:%M:%S.%f")
            except ValueError:
                raise AdapterError(
                    "SCHEMA_TIMESTAMP_INVALID",
                    f"tick line {line_number} timestamp {timestamp_text!r} is not TrueFX GMT format",
                )
            tick_utc = require_utc(
                tick.replace(tzinfo=timezone.utc), f"tick line {line_number} timestamp"
            )
            if (tick_utc.year, tick_utc.month) != (year, month):
                raise AdapterError(
                    "SCHEMA_INVARIANT_VIOLATED",
                    f"tick line {line_number} falls outside {year}-{month:02d}",
                )
            if tick_utc in seen_timestamps:
                raise AdapterError("DUPLICATE_RECORD_ID", f"tick {timestamp_text!r} appears twice")
            seen_timestamps.add(tick_utc)
            try:
                bid = float(bid_text)
                ask = float(ask_text)
            except ValueError:
                raise AdapterError(
                    "SCHEMA_VALUE_TYPE_MISMATCH",
                    f"tick line {line_number} prices are not numeric",
                )
            if bid <= 0 or ask <= 0 or ask < bid:
                raise AdapterError(
                    "SCHEMA_INVARIANT_VIOLATED",
                    f"tick line {line_number} violates 0 < bid <= ask",
                )
            timings = timings_from_evidence(
                tick_utc, evidence, effective_time_utc=None
            )
            for field_name, value in (("bid", bid), ("ask", ask)):
                records.append(
                    self.make_record(
                        dataset_id="top_of_book_ticks",
                        entity_id=entity_id,
                        field_name=field_name,
                        value=value,
                        unit="PRICE",
                        timings=timings,
                        retrieved_time_utc=retrieved_time_utc,
                        request_id=request_id,
                        raw_sha256=raw_sha256,
                    )
                )

        notes = [
            AdapterNote(TRUEFX_GMT_PARSED_AS_UTC, "TrueFX tick timestamps are GMT by spec; parsed as UTC"),
            AdapterNote(
                TRUEFX_MONTH_END_UPPER_BOUND,
                "availability uses the end of the archive month as a conservative upper bound",
            ),
            AdapterNote(
                TRUEFX_NOT_SWAP_ROLLOVER_AUTHORITY,
                "TrueFX bid/ask never authorizes swap, rollover or financing assumptions",
            ),
        ]
        return self.make_output(
            dataset_id="top_of_book_ticks",
            request_id=request_id,
            response=response_like,
            records=records,
            notes=notes,
        )
