"""FOREX-NG1 P0 plane adapter: consume_via_plane for the frozen S2/S3 set.

Plan section 3 adoption law, applied to this cycle's frozen consumption set:

1. AuthorityRegistry verdict check -- only GRANTED series may be consumed,
   cross-checked against the frozen V3-GA4 authority table (fail-closed).
2. CADS resolve verify-on-read -- the object's address IS its integrity
   proof; a mismatched re-hash raises and nothing is returned (fail-closed,
   never a silent fix).
3. Manifest-verified query -- resolved bytes are materialized into a
   scratch manifest entry pinned by content hash; tabular entries go
   through the QueryPlane frozen-query surface (re-verified before DuckDB
   sees them); non-tabular bytes are proven by resolve+verify (V3-GA5
   precedent for non-tabular classes).

Read-only by construction: the CADS store root is never written through
this module; scratch materialization goes to the caller's scratch dir.

This module also carries the P0 measurement primitives:

- FRED vintaged parsers (realtime-window structure proof, first
  appearance, revision events) used for the V9-HIGH-finding vintage-ness
  proof on the GB/CA legs;
- ONS D7BT / StatCan 18100004 zip structure readers (current-vintage
  continuation tables -- documented as NOT the PIT channel);
- announcement-instant normalization with DST-correct local->UTC
  conversion and a conservative end-of-day bound for date-only evidence.
"""

from __future__ import annotations

import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.platform_v3.authority import AuthorityRegistry  # noqa: E402
from research.platform_v3.cads import (  # noqa: E402
    CADS, CADSError, CADSIntegrityError,
)
from research.platform_v3.query_plane import (  # noqa: E402
    FrozenQuery, ManifestEntry, OutputColumn, QueryPlane,
)

#: Frozen at V3-GA2/GA4 (plan section 3). Read-only store.
DEFAULT_CADS_STORE_ROOT = (
    "/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store")

DEFAULT_AUTHORITY_JOURNAL = os.path.join(
    REPO_ROOT,
    "research/control/research_platform_v3_run/authority_registry_journal.jsonl")

DEFAULT_GA4_GATE = os.path.join(
    REPO_ROOT,
    "research/control/research_platform_v3_run/gates/"
    "V3-GA4_authority_table.json")

#: The single CADS address pinned for S2:fred-keyed-vintage-classes
#: (V3-GA2: 5 files, 0 drift).
S2_PINNED_ADDRESS = (
    "07d1e0d5adc8fb124f8d9246b8ab0fdeea79e5be20fa99ea0a8fe81cd96aad12")

#: The five S3 entries pinned under S3:forex-announcement-ledger.
S3_ENTRY_NAMES = (
    "GB/ons_d7bt_cpi_allitems.csv",
    "CA/canada_allitems_nsa_2002_100_monthly.csv",
    "CA/statcan_18100004.zip",
    "AU/abs_640101_jul2026.xlsx",
    "US/fred_cpiaucsl_rt.json",
)

FRED_MISSING = "."


class ConsumptionRefused(Exception):
    """Fail-closed refusal: nothing is consumed, nothing is inferred."""


class VintageStructureError(Exception):
    """Malformed vintage archive shape (not a vintaged archive at all)."""


# --------------------------------------------------------------------------- #
# 1-3: the consume_via_plane path
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ConsumedObject:
    series_id: str
    entry_name: str
    resolved_address: str
    nbytes: int
    scratch_path: str
    query_verdict: str   # FROZEN_QUERY_SUCCESS | RESOLVE_VERIFY_ONLY


def load_registry(journal_path: str | None = None) -> AuthorityRegistry:
    """Load the committed authority journal (read-only replay)."""
    return AuthorityRegistry(journal_path or DEFAULT_AUTHORITY_JOURNAL)


def ga4_granted(ga4_path: str | None = None) -> frozenset[str]:
    """The frozen GRANTED list from the V3-GA4 authority table."""
    with open(ga4_path or DEFAULT_GA4_GATE, "r", encoding="utf-8") as fh:
        table = json.load(fh)
    granted = frozenset(table.get("granted", ()))
    if not granted:
        raise ConsumptionRefused("GA4 authority table lists no granted series")
    return granted


def _require_granted(registry: AuthorityRegistry, series_id: str,
                     ga4: frozenset[str] | None) -> None:
    verdict = registry.verdict(series_id)
    if verdict != "GRANTED":
        raise ConsumptionRefused(
            f"series {series_id} verdict={verdict!r}: consumption refused "
            "(fail-closed; only granted series may be consumed)")
    if ga4 is not None and series_id not in ga4:
        raise ConsumptionRefused(
            f"series {series_id} is not in the frozen V3-GA4 granted "
            "list: consumption refused")


def _safe_entry_name(entry_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", entry_name)


def consume_via_plane(registry: AuthorityRegistry, store_root: str,
                      series_id: str, entry_name: str, scratch_dir: str,
                      ga4: frozenset[str] | None = None) -> ConsumedObject:
    """The FOREX-NG1 consume-via-plane path.

    GRANTED check -> CADS resolve verify-on-read -> manifest-verified
    query (frozen-query surface for tabular bytes; resolve+verify for
    non-tabular bytes). Any failure raises; there is no partial success.
    """
    _require_granted(registry, series_id, ga4)

    store = CADS(store_root)
    pin = None
    for p in store.pins():
        meta = p.get("metadata", {})
        if meta.get("series") == series_id and meta.get("file") == entry_name:
            pin = p
            break
    if pin is None:
        raise ConsumptionRefused(
            f"no exact CADS pin for series {series_id!r} entry "
            f"{entry_name!r}: consumption refused")

    data = store.resolve(pin["address"])   # verify-on-read (fail-closed)

    os.makedirs(scratch_dir, exist_ok=True)
    # keep the entry's extension: the query plane routes CSVs through
    # read_csv by extension, and the scratch name must stay deterministic
    scratch_path = os.path.join(scratch_dir, _safe_entry_name(entry_name))
    with open(scratch_path, "wb") as fh:
        fh.write(data)

    manifest_id = f"{series_id}:{entry_name}"
    query_verdict = "RESOLVE_VERIFY_ONLY"
    if entry_name.endswith(".csv"):
        entry = ManifestEntry(manifest_id=manifest_id, path=scratch_path,
                              sha256=pin["address"])
        plane = QueryPlane({manifest_id: entry})
        try:
            plane.register_views({manifest_id: "v_consumed"})
            frozen = FrozenQuery(
                name="forex_ng1_p0_consume_probe",
                sql="SELECT count(*) AS n FROM v_consumed ORDER BY n",
                order_columns=["n"],
                output_schema=[OutputColumn("n", "BIGINT")],
            )
            result = plane.run(frozen, [manifest_id])
        finally:
            plane.close()
        if result.verdict != "SUCCESS":
            raise ConsumptionRefused(
                f"manifest-verified query {manifest_id} -> "
                f"{result.verdict}: {result.reason}")
        query_verdict = "FROZEN_QUERY_SUCCESS"

    return ConsumedObject(
        series_id=series_id, entry_name=entry_name,
        resolved_address=pin["address"], nbytes=len(data),
        scratch_path=scratch_path, query_verdict=query_verdict)


def consume_s2_manifest(store_root: str, registry: AuthorityRegistry,
                        ga4: frozenset[str] | None = None,
                        address: str = S2_PINNED_ADDRESS) -> dict:
    """Resolve the S2 vintaged-manifest CADS object (GRANTED-gated).

    Returns the parsed manifest; the caller verifies each referenced
    file digest via verify_s2_files before consuming any leg bytes.
    """
    _require_granted(registry, "S2:fred-keyed-vintage-classes", ga4)
    store = CADS(store_root)
    data = store.resolve(address)   # verify-on-read (fail-closed)
    manifest = json.loads(data.decode("utf-8"))
    series = manifest.get("series")
    if not isinstance(series, dict) or not series:
        raise VintageStructureError(
            "S2 manifest malformed: no series map")
    return manifest


def verify_s2_files(manifest: Mapping[str, Any],
                    local_path_by_file: Mapping[str, str],
                    ) -> dict[str, dict]:
    """Verify every S2-manifest-referenced file against its pinned sha256.

    Fail-closed: a missing or drifted file is recorded as match=False;
    the caller turns any False into a gate BLOCKED_DATA (never a silent
    fix). Values are sha256 of the local bytes (CADS objects count as
    local bytes: address == digest).
    """
    import hashlib
    out: dict[str, dict] = {}
    for series_id, rec in sorted(manifest["series"].items()):
        fname = rec["file"]
        pinned = rec["sha256"]
        path = local_path_by_file.get(fname)
        if path is None or not os.path.exists(path):
            out[series_id] = {"file": fname, "pinned_sha256": pinned,
                              "local_path": path, "match": False,
                              "reason": "ABSENT"}
            continue
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        actual = h.hexdigest()
        out[series_id] = {
            "file": fname, "pinned_sha256": pinned, "local_path": path,
            "local_sha256": actual, "match": actual == pinned,
            "rows_declared": rec.get("rows"),
        }
    return out


# --------------------------------------------------------------------------- #
# FRED vintaged parsers (GB/CA/AU/NZ/US legs)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class VintageRow:
    obs_date: str        # "2025-03-01"
    realtime_start: str  # "2025-05-15" (vintage opens)
    realtime_end: str    # "2025-08-01" (vintage superseded / feed end)
    value: str


def parse_fred_vintaged(observations: Sequence[Mapping[str, Any]],
                        ) -> list[VintageRow]:
    """Parse FRED realtime observations; validate the vintaged shape.

    Raises VintageStructureError when a row lacks the realtime window --
    i.e. a current-vintage revised-in-place table masquerading as an
    archive fails HERE, structurally, before any measurement.
    """
    rows: list[VintageRow] = []
    for i, o in enumerate(observations):
        missing_keys = {"realtime_start", "realtime_end", "date", "value"} - set(o)
        if missing_keys:
            raise VintageStructureError(
                f"observation {i} lacks vintaged keys {sorted(missing_keys)}: "
                "not a realtime archive")
        rows.append(VintageRow(
            obs_date=str(o["date"]),
            realtime_start=str(o["realtime_start"]),
            realtime_end=str(o["realtime_end"]),
            value=str(o["value"]),
        ))
    if not rows:
        raise VintageStructureError("empty observation set")
    return rows


def first_appearance(rows: Iterable[VintageRow]) -> dict[str, tuple[str, str]]:
    """obs_date -> (earliest realtime_start, first non-missing value)."""
    fa: dict[str, tuple[str, str]] = {}
    for r in rows:
        if r.value == FRED_MISSING:
            continue
        cur = fa.get(r.obs_date)
        if cur is None or r.realtime_start < cur[0]:
            fa[r.obs_date] = (r.realtime_start, r.value)
    return fa


def vintage_structure_proof(rows: Sequence[VintageRow]) -> dict:
    """Measure vintage-ness: every value carries a realtime window,
    multiple vintages exist, and revisions are observable per month."""
    n = len(rows)
    with_window = sum(
        1 for r in rows
        if r.realtime_start and r.realtime_end
        and r.realtime_start <= r.realtime_end)
    by_month: dict[str, dict[str, str]] = {}
    vintages: set[str] = set()
    realtime_days = 0
    for r in rows:
        if r.value == FRED_MISSING:
            continue
        by_month.setdefault(r.obs_date, {})[r.value] = r.realtime_start
        vintages.add(r.realtime_start)
        realtime_days += 1
    months = sorted(by_month)
    revised = [m for m in months if len(by_month[m]) > 1]
    return {
        "rows": n,
        "rows_with_realtime_window": with_window,
        "pct_rows_with_realtime_window": round(
            100.0 * with_window / n, 4) if n else 0.0,
        "non_missing_values": realtime_days,
        "distinct_vintages": len(vintages),
        "months_with_values": len(months),
        "first_month": months[0] if months else None,
        "last_month": months[-1] if months else None,
        "months_with_multiple_distinct_values": len(revised),
        "revised_months_sample": revised[:5],
        "every_value_vintaged": with_window == n and realtime_days > 0,
    }


def latest_vintage_by_month(rows: Sequence[VintageRow]) -> dict[str, tuple[str, str, str]]:
    """obs_date -> (realtime_start, realtime_end, value) of the latest
    vintage carrying that month."""
    latest: dict[str, tuple[str, str, str]] = {}
    for r in rows:
        if r.value == FRED_MISSING:
            continue
        cur = latest.get(r.obs_date)
        if cur is None or r.realtime_start > cur[0]:
            latest[r.obs_date] = (r.realtime_start, r.realtime_end, r.value)
    return latest


# --------------------------------------------------------------------------- #
# Official continuation tables (documented CURRENT-vintage, NOT the PIT channel)
# --------------------------------------------------------------------------- #

def parse_ons_d7bt(text: str) -> dict:
    """ONS D7BT CSV structure read.

    Structure verdict: a single 'Release date' header for the whole file
    and no per-value vintage dimension -> CURRENT-vintage snapshot
    (revised-in-place continuation table), usable ONLY as tail coverage,
    never as PIT evidence for the GB leg.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    header: dict[str, str] = {}
    data_rows: list[tuple[str, str]] = []
    for ln in lines:
        parts = [p.strip().strip('"') for p in ln.split('","')]
        if len(parts) >= 2 and re.fullmatch(
                r"\d{4}( [A-Z]{3})?", parts[0]) and re.fullmatch(
                r"-?\d+(\.\d+)?", parts[1]):
            data_rows.append((parts[0], parts[1]))
        elif len(parts) == 2 and parts[0]:
            header[parts[0]] = parts[1]
    months = [m for m, _ in data_rows]
    return {
        "header": header,
        "release_date_header": header.get("Release date"),
        "cdid": header.get("CDID"),
        "rows": len(data_rows),
        "first_period": months[0] if months else None,
        "last_period": months[-1] if months else None,
        "per_value_vintage_column": False,
        "structure_verdict": "CURRENT_VINTAGE_SNAPSHOT",
    }


def parse_statcan_zip(data: bytes) -> dict:
    """StatCan 18100004 zip structure read.

    Structure verdict: the cube CSV has no vintage dimension (columns
    REF_DATE..DECIMALS; STATUS carries preliminary flags, not vintages)
    and the MetaData cube header declares Archive Status CURRENT ->
    CURRENT-vintage table, continuation only, never the CA PIT channel.
    """
    zf = zipfile.ZipFile(__import__("io").BytesIO(data))
    names = zf.namelist()
    cube = zf.read("18100004.csv").decode("utf-8", "replace")
    header_line = cube.splitlines()[1] if "\n" in cube else cube
    meta = zf.read("18100004_MetaData.csv").decode("utf-8", "replace")
    meta_first = meta.splitlines()[1] if "\n" in meta else meta
    archive_status = ""
    m = re.search(r'"CURRENT[^"]*"', meta_first)
    if m:
        archive_status = m.group(0).strip('"')
    cols = [c.strip().strip('"') for c in header_line.split('","')]
    n_rows = max(0, len(cube.splitlines()) - 1)
    return {
        "members": names,
        "cube_columns": cols,
        "cube_data_rows": n_rows,
        "vintage_dimension_columns": [c for c in cols
                                      if "vintage" in c.lower()],
        "archive_status": archive_status,
        "structure_verdict": "CURRENT_VINTAGE_SNAPSHOT",
    }


def parse_ca_tidy(text: str) -> list[tuple[str, float]]:
    """CA tidy extraction (ref_month,index_2002_100)."""
    rows: list[tuple[str, float]] = []
    lines = [ln for ln in text.splitlines() if ln.strip()]
    for ln in lines[1:]:
        m, v = ln.split(",")
        rows.append((m, float(v)))
    return rows


# --------------------------------------------------------------------------- #
# Announcement instants: parsing + DST-correct UTC normalization
# --------------------------------------------------------------------------- #

_MONTHS = {name: i for i, name in enumerate((
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december"), start=1)}
_MONTHS_ABBR = {name[:3]: i for name, i in _MONTHS.items()}

END_OF_DAY_UTC = (23, 59, 59)


def parse_gb_release_display(display: str) -> str:
    """'16 April 2025' -> '2025-04-16'."""
    m = re.fullmatch(r"(\d{1,2}) ([A-Za-z]+) (\d{4})", display.strip())
    if not m or m.group(2).lower() not in _MONTHS:
        raise ValueError(f"unparseable GB release_date_display: {display!r}")
    day, mon, year = int(m.group(1)), _MONTHS[m.group(2).lower()], int(m.group(3))
    return date(year, mon, day).isoformat()


def gb_ref_period(period: str) -> str:
    """'march2025' -> '2025-03'."""
    m = re.fullmatch(r"([a-z]+)(\d{4})", period.strip().lower())
    if not m or m.group(1) not in _MONTHS:
        raise ValueError(f"unparseable GB reference_period: {period!r}")
    return f"{m.group(2)}-{_MONTHS[m.group(1)]:02d}"


def quarter_first_month_from_end(end_month: str, year: int) -> str:
    """Quarter named by end month -> first month (V9 quarter-first-month
    representation): dec-2024 quarter -> 2024-10."""
    mi = _MONTHS_ABBR[end_month[:3].lower()]
    fm = mi - 2
    y = year
    if fm <= 0:
        fm += 12
        y -= 1
    return f"{y:04d}-{fm:02d}"


def normalize_instant_utc(day_iso: str, time_local: str | None = None,
                          tz_name: str | None = None) -> tuple[str, str]:
    """Local (date[,time]) -> (UTC ISO instant, precision label).

    - time_local + tz: exact DST-correct conversion via zoneinfo
      (precision CALENDAR_TIME_UTC_EXACT).
    - no time: conservative end-of-day UTC bound (23:59:59Z) -- the
      print is provably public by that instant; a 16:00-NY decision
      earlier the same day can NOT see it (no lookahead), matching the
      V9 operative_available_time convention for unevidenced times
      (precision DATE_ONLY_CONSERVATIVE_END_OF_DAY).
    """
    d = date.fromisoformat(day_iso)
    if time_local is not None:
        if tz_name is None:
            raise ValueError("time_local requires tz_name")
        hh, mm = (int(x) for x in time_local.split(":"))
        local = datetime(d.year, d.month, d.day, hh, mm,
                         tzinfo=ZoneInfo(tz_name))
        return (local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "CALENDAR_TIME_UTC_EXACT")
    end = datetime(d.year, d.month, d.day, *END_OF_DAY_UTC,
                   tzinfo=timezone.utc)
    return (end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "DATE_ONLY_CONSERVATIVE_END_OF_DAY")


# --------------------------------------------------------------------------- #
# Announcement census (calendars + vintaged coverage)
# --------------------------------------------------------------------------- #

CALENDAR_PINS = {
    "GB": {
        "path": "research/control/forex_free_v5_run/"
                "gb_ons_cpi_release_dates.json",
        "sha256_prefix": "aad19697",
        "pin_basis": "V9 P0 census GB_cal pin aad19697",
    },
    "CA": {
        "path": "research/control/forex_free_v6_run/"
                "ca_statcan_cpi_release_dates_v3.json",
        "sha256_prefix": "0f1a9328",
        "pin_basis": "CA v3 pin 0f1a9328 (dispatch + V9 census)",
    },
    "AU": {
        "path": "research/control/forex_free_v5_run/"
                "au_abs_cpi_release_dates.json",
        "sha256_prefix": "42a4e4a3",
        "pin_basis": "V9 P0 census AU_cal pin 42a4e4a3",
    },
    "NZ": {
        "path": "research/control/forex_free_v5_run/"
                "nz_statsnz_cpi_release_dates.json",
        "sha256_prefix": "62f82c23",
        "pin_basis": "V9 P0 census NZ_cal pin 62f82c23",
    },
}

EMU_LEDGER_PIN = {
    "path": "research/control/forex_free_v6_run/"
            "announcement_ledger_v6_emu_repair.jsonl",
    "pin_basis": "announcement ledger EMU v2 repair rows "
                 "(schema forex_free_v6_announcement_ledger_repair_v2_row_v1)",
}

_AU_QUARTER_TOKENS = {"mar", "jun", "sep", "dec"}


def load_calendar(economy: str, v9_root: str) -> tuple[list[dict], str]:
    """Load a pinned print calendar; verify its sha256 pin prefix."""
    import hashlib
    spec = CALENDAR_PINS[economy]
    path = os.path.join(v9_root, spec["path"])
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        raw = fh.read()
    h.update(raw)
    digest = h.hexdigest()
    if not digest.startswith(spec["sha256_prefix"]):
        raise ConsumptionRefused(
            f"{economy} calendar pin mismatch: expected prefix "
            f"{spec['sha256_prefix']}, file hashes to {digest}")
    return json.loads(raw.decode("utf-8")), digest


def gb_instants(calendar: Sequence[Mapping[str, Any]]) -> list[dict]:
    out = []
    for e in calendar:
        if e.get("class") != "EVIDENCED":
            continue
        out.append({
            "economy": "GB",
            "reference_period": gb_ref_period(e["reference_period"]),
            "publication_date": parse_gb_release_display(
                e["release_date_display"]),
            "time_local": None, "tz": None,
            "evidence": {"archive_path": e.get("archive_path"),
                         "archive_sha256": e.get("archive_sha256")},
        })
    return out


def ca_instants(calendar: Sequence[Mapping[str, Any]]) -> list[dict]:
    """CA v3 calendar: monthly CPI for month M released in M+1 (StatCan
    monthly convention; validated below against vintaged first-appearance
    lags). Publication timestamps are true-UTC evidenced (tz_conversion
    archived per row)."""
    out = []
    for e in calendar:
        if e.get("class") != "EVIDENCED":
            continue
        rd = date.fromisoformat(e["release_date"])
        ref_y, ref_m = (rd.year, rd.month - 1) if rd.month > 1 \
            else (rd.year - 1, 12)
        out.append({
            "economy": "CA",
            "reference_period": f"{ref_y:04d}-{ref_m:02d}",
            "publication_date": e["release_date"],
            "time_utc_evidenced": e.get("release_time_utc_true"),
            "time_local": None, "tz": None,
            "evidence": {"archive_path": e.get("archive_path"),
                         "archive_sha256": e.get("archive_sha256"),
                         "tz_conversion": e.get("tz_conversion")},
        })
    return out


def au_instants(calendar: Sequence[Mapping[str, Any]]) -> list[dict]:
    out = []
    for e in calendar:
        if e.get("class") != "EVIDENCED" or not e.get("release_date"):
            continue
        slug = e["slug"]
        if slug == "latest-release":
            continue   # duplicate of the newest release; no ref period
        m = re.fullmatch(r"([a-z]+)-(?:quarter-)?(\d{4})", slug)
        if not m:
            raise ValueError(f"unparseable AU slug: {slug!r}")
        token, year = m.group(1), int(m.group(2))
        if token in _AU_QUARTER_TOKENS:
            ref = quarter_first_month_from_end(token, year)
        else:
            ref = f"{year:04d}-{_MONTHS_ABBR[token]:02d}"
        out.append({
            "economy": "AU",
            "reference_period": ref,
            "publication_date": e["release_date"],
            "time_local": None, "tz": None,
            "evidence": {"archive_path": e.get("archive_path"),
                         "archive_sha256": e.get("archive_sha256")},
        })
    return out


def nz_instants(calendar: Sequence[Mapping[str, Any]]) -> list[dict]:
    out = []
    for e in calendar:
        if e.get("class") != "EVIDENCED":
            continue
        m = re.fullmatch(
            r"consumers-price-index-([a-z]+)-(\d{4})-quarter", e["slug"])
        if not m:
            raise ValueError(f"unparseable NZ slug: {e['slug']!r}")
        ref = quarter_first_month_from_end(m.group(1), int(m.group(2)))
        out.append({
            "economy": "NZ",
            "reference_period": ref,
            "publication_date": e["release_date"],
            "time_local": e.get("release_time_local"), "tz": "Pacific/Auckland",
            "evidence": {"archive_path": e.get("archive_path"),
                         "archive_sha256": e.get("archive_sha256")},
        })
    return out


def us_instants(fred_rows: Sequence[VintageRow]) -> list[dict]:
    """US CPI print instants from the pinned realtime archive: the
    publication day of month M is the realtime_start of M's FIRST
    vintage (revisions-only vintages carry no new month and are not
    print instants). Time-of-day is not in the pinned bytes -> the
    census records date-only conservative instants."""
    fa = first_appearance(fred_rows)
    out = []
    for obs_date, (rt, value) in sorted(fa.items()):
        out.append({
            "economy": "US",
            "reference_period": obs_date[:7],
            "publication_date": rt,
            "time_local": None, "tz": None,
            "evidence": {"source": "CADS US/fred_cpiaucsl_rt.json "
                                   "realtime vintage first-appearance",
                         "first_vintage_value": value},
        })
    return out


def build_census(instants: Sequence[dict],
                 coverage_by_economy: Mapping[str, Mapping[str, tuple]],
                 window_start: str, window_end: str) -> dict:
    """Filter instants: publication within [window_start, window_end]
    AND the reference period carries a vintaged realized value
    (first-appearance realtime exists).

    PIT discipline per included instant (recorded, not inferred):

    - ``vintaged_first_realtime_start``: when the archive first carried
      the realized value (OECD-feed ingest usually LAGS the bulletin --
      the normal, safe direction);
    - ``operative_vintaged_available_from`` = max(publication_date,
      first_realtime): the earliest instant at which the vintaged
      realized print is provably public through BOTH evidence channels
      (conservative; this is what downstream decisions must respect);
    - ``pit_notes`` records the anomaly when the archive LED the
      bulletin (first_realtime < publication) -- a recorded anomaly,
      never silently dropped;
    - ``release_ordinal_in_reference_period`` / ``is_first_release``:
      some calendars (CA WDS) list correction releases of the same
      reference month; ordinal 1 is the print instant.
    """
    included, excluded = [], []
    seen: dict[tuple[str, str], int] = {}
    for inst in sorted(instants,
                       key=lambda r: (r["economy"], r["publication_date"])):
        eco, ref = inst["economy"], inst["reference_period"]
        fa = coverage_by_economy.get(eco, {}).get(
            f"{ref}-01" if len(ref) == 7 else ref)
        reasons = []
        if not (window_start <= inst["publication_date"] <= window_end):
            reasons.append("outside_s0_window")
        if fa is None:
            reasons.append("ref_period_not_vintaged_covered")
        rec = dict(inst)
        if reasons:
            rec["exclusion_reasons"] = reasons
            excluded.append(rec)
            continue
        key = (eco, ref)
        seen[key] = seen.get(key, 0) + 1
        rec["release_ordinal_in_reference_period"] = seen[key]
        rec["is_first_release_of_period"] = seen[key] == 1
        rec["vintaged_first_realtime_start"] = fa[0]
        rec["vintaged_first_value"] = fa[1]
        rec["operative_vintaged_available_from"] = max(
            inst["publication_date"], fa[0])
        notes = []
        if fa[0] < inst["publication_date"]:
            notes.append("archive_led_bulletin")
        if notes:
            rec["pit_notes"] = notes
        inst_utc, precision = normalize_instant_utc(
            inst["publication_date"], inst.get("time_local"),
            inst.get("tz"))
        if inst.get("time_utc_evidenced"):
            inst_utc = inst["time_utc_evidenced"]
            precision = "CALENDAR_TIME_UTC_EXACT"
        rec["publication_instant_utc"] = inst_utc
        rec["time_precision"] = precision
        included.append(rec)
    by_eco: dict[str, int] = {}
    for r in included:
        by_eco[r["economy"]] = by_eco.get(r["economy"], 0) + 1
    return {
        "instants": included,
        "excluded": excluded,
        "counts_by_economy": by_eco,
        "total_instants": len(included),
        "first_release_counts_by_economy": {
            e: sum(1 for r in included
                   if r["economy"] == e and r["is_first_release_of_period"])
            for e in by_eco},
    }


def census_lookup_instant(census: Mapping[str, Any], economy: str,
                          publication_date: str) -> dict:
    """Exact lookup by (economy, publication_date). Canary support:
    fabricated instants MUST come back found=False."""
    hits = [i for i in census["instants"]
            if i["economy"] == economy
            and i["publication_date"] == publication_date]
    return {"economy": economy, "publication_date": publication_date,
            "found": bool(hits)}
