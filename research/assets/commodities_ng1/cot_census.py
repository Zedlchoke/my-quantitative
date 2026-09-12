"""COMMODITIES-NG1: CFTC Commitments of Traders census + PIT clock.

Parses the official legacy futures-only annual archive zips
(``https://www.cftc.gov/files/dea/history/deacot{YYYY}.zip`` -- free,
keyless) into per-market weekly records and computes the frozen
coverage census (plan section 3):

- market identity is the CFTC Contract Market Code (stable across
  display-name changes; a rename is recorded as a name event, never a
  new market);
- coverage per market: first/last report date, distinct weekly report
  count, span, max gap, missing-week census;
- a market qualifies on the CoT leg only when (frozen rule):
  ``weeks >= 520`` AND ``span_years >= 10.0`` AND ``max_gap_days <= 21``.

PIT clock law (plan sections 3/5): the legacy report carries Tuesday
position data ("As of Date"); the official release instant is Friday
15:30 America/New_York of the same week (DST-correct).  No downstream
consumer may see a report's positions before that instant; this module
provides the rule and the fail-closed guard.  Known CFTC holiday
exceptions shift individual releases earlier; the per-report census
records measured as-of dates only, and the frozen rule is recorded as
the program convention with the schedule-page evidence sha-pinned in
the run directory.
"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

SCHEMA = "commodities_ng1/cot_census@1"

#: Frozen CoT-leg qualification rule (plan section 3, floor condition (a)).
COT_MIN_WEEKS = 520          # >= 10 years of weekly reports
COT_MIN_SPAN_YEARS = 10.0
COT_MAX_GAP_DAYS = 21

#: Exchange that publishes at 15:30 ET; the schedule page is the evidence.
_RELEASE_TZ = ZoneInfo("America/New_York")
_RELEASE_CLOCK = time(15, 30)

#: Inner archive member name for the legacy futures-only annual file.
INNER_MEMBER = "annual.txt"

#: Header columns (whitespace-normalized, lowercased) consumed from the
#: annual.txt CSV surface.
_COLUMN_ALIASES = {
    "market and exchange names": "market_name",
    "as of date in form yyyy-mm-dd": "report_date",
    "cftc contract market code": "contract_market_code",
    "cftc market code in initials": "exchange_code",
    "open interest (all)": "open_interest",
    "noncommercial positions-long (all)": "noncomm_long",
    "noncommercial positions-short (all)": "noncomm_short",
    "noncommercial positions-spreading (all)": "noncomm_spreading",
    "commercial positions-long (all)": "comm_long",
    "commercial positions-short (all)": "comm_short",
}

_INT_FIELDS = (
    "open_interest", "noncomm_long", "noncomm_short",
    "noncomm_spreading", "comm_long", "comm_short",
)


class CotParseError(Exception):
    """Fail-closed parse failure: never fabricate a record."""


class CotLookupRefused(Exception):
    """Unknown market code / nonexistent report lookup: refused."""


@dataclass(frozen=True)
class CotRecord:
    market_name: str
    report_date: date
    contract_market_code: str
    exchange_code: str
    open_interest: int
    noncomm_long: int
    noncomm_short: int
    noncomm_spreading: int
    comm_long: int
    comm_short: int

    def as_row(self) -> list:
        return [
            self.contract_market_code, self.market_name,
            self.report_date.isoformat(), self.exchange_code,
            self.open_interest, self.noncomm_long, self.noncomm_short,
            self.noncomm_spreading, self.comm_long, self.comm_short,
        ]


#: canonical weekly CSV header (committed normalized surface)
CSV_HEADER = [
    "contract_market_code", "market_name", "report_date", "exchange_code",
    "open_interest", "noncomm_long", "noncomm_short", "noncomm_spreading",
    "comm_long", "comm_short",
]


def parse_annual_text(text: str, source: str = "annual.txt") -> list[CotRecord]:
    """Parse one legacy futures-only annual.txt payload (CSV w/ header)."""
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise CotParseError(f"{source}: empty archive member")
    stripped = {" ".join(f.split()).lower(): f for f in reader.fieldnames}
    alias = {}
    for canon, mapped in _COLUMN_ALIASES.items():
        hit = stripped.get(canon)
        if hit is None:
            raise CotParseError(
                f"{source}: required column {canon!r} absent "
                f"(have {sorted(stripped)[:4]}...); format drift -> fail closed")
        alias[mapped] = hit
    records: list[CotRecord] = []
    for lineno, raw in enumerate(reader, start=2):
        if not raw.get(alias["market_name"]):
            continue
        try:
            rdate = datetime.strptime(
                raw[alias["report_date"]].strip(), "%Y-%m-%d").date()
            values = {f: int(raw[alias[f]].strip())
                      for f in _INT_FIELDS}
        except (ValueError, TypeError) as exc:
            raise CotParseError(
                f"{source}:{lineno}: malformed row ({exc}); fail closed"
            ) from exc
        records.append(CotRecord(
            market_name=raw[alias["market_name"]].strip(),
            report_date=rdate,
            contract_market_code=raw[alias["contract_market_code"]].strip(),
            exchange_code=raw[alias["exchange_code"]].strip(),
            **values))
    if not records:
        raise CotParseError(f"{source}: zero records parsed; fail closed")
    return records


def parse_zip(path: str) -> list[CotRecord]:
    """Parse a deacotYYYY.zip archive (inner member annual.txt)."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if INNER_MEMBER not in names:
            raise CotParseError(
                f"{path}: inner member {INNER_MEMBER!r} absent "
                f"(have {names}); format drift -> fail closed")
        with zf.open(INNER_MEMBER) as fh:
            return parse_annual_text(fh.read().decode("utf-8"), source=path)


def records_to_csv(records: list[CotRecord]) -> str:
    """Canonical CSV serialization (deterministic order: code, date)."""
    ordered = sorted(records, key=lambda r: (r.contract_market_code,
                                             r.report_date))
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(CSV_HEADER)
    for rec in ordered:
        writer.writerow(rec.as_row())
    return buf.getvalue()


def csv_to_records(text: str) -> list[CotRecord]:
    """Inverse of records_to_csv (used by the plane-consumption path)."""
    reader = csv.DictReader(io.StringIO(text))
    missing = set(CSV_HEADER) - set(reader.fieldnames or [])
    if missing:
        raise CotParseError(f"normalized CSV missing columns {sorted(missing)}")
    out = []
    for raw in reader:
        out.append(CotRecord(
            market_name=raw["market_name"],
            report_date=datetime.strptime(raw["report_date"],
                                          "%Y-%m-%d").date(),
            contract_market_code=raw["contract_market_code"],
            exchange_code=raw["exchange_code"],
            open_interest=int(raw["open_interest"]),
            noncomm_long=int(raw["noncomm_long"]),
            noncomm_short=int(raw["noncomm_short"]),
            noncomm_spreading=int(raw["noncomm_spreading"]),
            comm_long=int(raw["comm_long"]),
            comm_short=int(raw["comm_short"])))
    return out


def records_digest(records: list[CotRecord]) -> str:
    """Order-independent canonical digest of a record set (parity use)."""
    import hashlib
    canon = sorted(
        "|".join(str(x) for x in r.as_row()) for r in records)
    return hashlib.sha256("\n".join(canon).encode("utf-8")).hexdigest()


# -- coverage census --------------------------------------------------------- #

def census_market(records: list[CotRecord]) -> dict:
    """Frozen coverage census for ONE market (all records same code)."""
    if not records:
        raise CotLookupRefused("census of empty market record set")
    codes = {r.contract_market_code for r in records}
    if len(codes) != 1:
        raise CotLookupRefused(f"mixed market codes in census: {sorted(codes)}")
    dates = sorted({r.report_date for r in records})
    first, last = dates[0], dates[-1]
    span_days = (last - first).days
    span_years = round(span_days / 365.25, 4)
    gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
    max_gap = max(gaps) if gaps else 0
    expected = span_days // 7 + 1
    missing = expected - len(dates)
    names = {}
    for r in records:
        names.setdefault(r.market_name, []).append(
            r.report_date.isoformat())
    name_events = [
        {"market_name": n, "first_seen": v[0], "last_seen": v[-1]}
        for n, v in sorted(names.items())]
    eligible = (len(dates) >= COT_MIN_WEEKS
                and span_years >= COT_MIN_SPAN_YEARS
                and max_gap <= COT_MAX_GAP_DAYS)
    return {
        "contract_market_code": codes.pop(),
        "market_names": name_events,
        "exchange_codes": sorted({r.exchange_code for r in records}),
        "first_report": first.isoformat(),
        "last_report": last.isoformat(),
        "weeks": len(dates),
        "span_days": span_days,
        "span_years": span_years,
        "max_gap_days": max_gap,
        "expected_weeks": expected,
        "missing_weeks": max(missing, 0),
        "cot_leg_eligible": eligible,
        "rule": {
            "min_weeks": COT_MIN_WEEKS,
            "min_span_years": COT_MIN_SPAN_YEARS,
            "max_gap_days": COT_MAX_GAP_DAYS,
        },
    }


def census_by_market(records: list[CotRecord]) -> dict[str, dict]:
    """Census every market in a record set, keyed by contract market code."""
    by_code: dict[str, list[CotRecord]] = {}
    for r in records:
        by_code.setdefault(r.contract_market_code, []).append(r)
    return {code: census_market(recs)
            for code, recs in sorted(by_code.items())}


def lookup_market(records: list[CotRecord], contract_market_code: str
                  ) -> list[CotRecord]:
    """Fail-closed lookup: an unknown code is refused, never empty."""
    hit = [r for r in records
           if r.contract_market_code == contract_market_code]
    if not hit:
        raise CotLookupRefused(
            f"contract market code {contract_market_code!r} not present in "
            "the measured archive (fabricated-code canary semantics)")
    return hit


# -- PIT release clock -------------------------------------------------------- #

def release_instant(report_date: date) -> datetime:
    """Official release instant for a Tuesday-position report.

    Rule (plan sections 3/5, CFTC schedule evidence): Friday 15:30
    America/New_York of the report week, DST-correct, expressed in UTC.
    """
    if report_date.weekday() != 1:            # 1 == Tuesday
        raise CotLookupRefused(
            f"report date {report_date.isoformat()} is not a Tuesday "
            "(fabricated-release-date canary semantics)")
    friday = report_date + timedelta(days=3)
    local = datetime.combine(friday, _RELEASE_CLOCK, tzinfo=_RELEASE_TZ)
    return local.astimezone(timezone.utc)


def pit_guard(report_date: date, use_instant_utc: datetime) -> dict:
    """Fail-closed PIT gate: refuse any use before the release instant."""
    release = release_instant(report_date)
    if use_instant_utc.tzinfo is None:
        use_instant_utc = use_instant_utc.replace(tzinfo=timezone.utc)
    allowed = use_instant_utc >= release
    return {
        "report_date": report_date.isoformat(),
        "release_instant_utc": release.isoformat(),
        "use_instant_utc": use_instant_utc.astimezone(
            timezone.utc).isoformat(),
        "pit_allowed": allowed,
    }
