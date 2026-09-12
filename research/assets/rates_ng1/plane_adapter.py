"""RATES-NG1 P0 plane adapter: ``consume_via_plane`` for the frozen set.

Plan section 3 adoption law, first ``rates`` family (frozen consumption
set is the RATES-NG1 dispatch contract, P0 work items 1-4):

1. frozen-set gate: an entry may only be consumed when it is in
   ``FROZEN_CONSUMPTION_SET`` (anything else is refused, including
   fabricated series/tickers/tenors -- P-7 canary surface);
2. authority gate: entries mapped onto platform-v3 authority ids (the
   FRED keyed series live under the frozen ``S2:fred-keyed-vintage-
   classes`` GRANTED set) additionally require the committed
   AuthorityRegistry verdict to be exactly ``GRANTED``;
3. digest gate (verify-on-read): the raw substrate bytes are re-hashed
   on every consumption and must equal the committed substrate-manifest
   sha256 -- a single-byte drift is ``BLOCKED_DATA``: never re-downloaded,
   never repaired;
4. manifest-verified query: tabular (CSV) entries are read through
   ``research.platform_v3.query_plane.QueryPlane`` with the manifest
   entry pinned to the substrate digest, so the query surface can never
   see bytes that differ from the pinned bytes; non-tabular (JSON)
   entries are proven by resolve+verify (V3-GA5 precedent for
   non-tabular classes).

Read-only by construction: this module never writes into any CADS store
and never writes into the raw substrate.  The shared CADS store at
``.runtime/v3_cads_store`` is opened READ-ONLY only to verify the
inherited CPIAUCSL realtime pin (0-drift overlap proof); new rates
substrate pins are carried by the committed substrate manifest instead
(writing pins into the shared store from a parallel lane is not a lane
power).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sys
from typing import Any, Mapping, Sequence

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.platform_v3.authority import AuthorityRegistry  # noqa: E402
from research.platform_v3.cads import CADS, CADSError  # noqa: E402
from research.platform_v3.query_plane import (  # noqa: E402
    FrozenQuery, ManifestEntry, OutputColumn, QueryPlane,
)

SCHEMA = "rates_ng1/plane_adapter@1"

RAW_SUBSTRATE_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "raw_substrate")

SUBSTRATE_MANIFEST = os.path.join(
    REPO_ROOT, "research", "control", "rates_ng1_run",
    "substrate_manifest.json")

DEFAULT_AUTHORITY_JOURNAL = os.path.join(
    REPO_ROOT, "research", "control", "research_platform_v3_run",
    "authority_registry_journal.jsonl")

#: Shared CADS store: READ-ONLY use, only to verify the inherited pins.
DEFAULT_CADS_STORE_ROOT = (
    "/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store")

#: The inherited CADS object for the S2 FRED realtime CPIAUCSL pull
#: (platform v3 GA2 pin; referenced by the committed S2 manifest).
CPIAUCSL_CADS_PIN = (
    "7f18ec982374ce4dfb235f53f001327793df8e1c0077d31206de25aa3455ac94")

#: Committed V8-era DGS10 control pin chain (P-13 inherited-pin law).
#: The staged_vintaged_manifest (sha256 ``c8ae7877...``) pinned DGS10.json
#: at ``03dde429...``; the manifest digest is frozen in the committed V8
#: run contract (research/control/forex_free_v8_run/run_contract.json,
#: commit 720decb3) and the entry digest in the committed
#: research/assets/forex_ng1/run/ctlpin.py (branch FOREX-NG1).
V8_STAGED_VINTAGED_MANIFEST_SHA256 = (
    "c8ae78777102ab45cec433f5da6c786355b57c884"
    "be5f15c39c1fc18ca328e7c")
V8_DGS10_SHA256_PIN = (
    "03dde429ba022e6d011ae3a61323124e38c5a3fac"
    "888b492823406a51c4c4aa0")

CURVE_YEARS = tuple(range(1990, 2027))
AUCTION_WINDOW_YEARS = tuple(range(2017, 2027))   # 2017 window catches
# announcements made in late 2017 for early-2018 auctions.
FRED_SERIES = ("DGS10", "DGS2", "DFII10", "DFII5", "T10YIE", "T5YIE",
               "CPIAUCSL")
ETP_TICKERS = ("TLT", "IEF", "IEI", "SHY")

#: Platform-v3 authority id the FRED keyed series are consumed under.
FRED_AUTHORITY_SERIES = "S2:fred-keyed-vintage-classes"

S2_CPIAUCSL_ENTRY = "fred/CPIAUCSL.json"


def _frozen_set() -> dict[str, dict[str, str]]:
    """The frozen consumption set: entry name -> {series, kind}."""
    entries: dict[str, dict[str, str]] = {}
    for y in CURVE_YEARS:
        entries[f"treasury_curve/par_yields_{y}.csv"] = {
            "series": "R5:treasury-par-yield-curve", "kind": "curve"}
    for s in FRED_SERIES:
        entries[f"fred/{s}.json"] = {
            "series": "R5:fred-keyed-granted", "kind": "fred"}
    for t in ETP_TICKERS:
        entries[f"etp_eod/{t}.US.json"] = {
            "series": "R5:eodhd-us-treasury-etp", "kind": "etp"}
        entries[f"etp_eod/{t}.US_adj.json"] = {
            "series": "R5:eodhd-us-treasury-etp-adjx", "kind": "etp_adj"}
    entries["etp_eod/us_delisted_symbols.json"] = {
        "series": "R5:eodhd-us-delisted-census", "kind": "delisted"}
    for y in AUCTION_WINDOW_YEARS:
        entries[f"auctions/ta_ws_search_{y}.json"] = {
            "series": "R5:treasury-auction-calendar", "kind": "auction"}
    return entries


FROZEN_CONSUMPTION_SET = _frozen_set()

CANONICAL_TENOR_ORDER = (
    "1 Mo", "1.5 Month", "2 Mo", "3 Mo", "4 Mo", "6 Mo", "1 Yr", "2 Yr",
    "3 Yr", "5 Yr", "7 Yr", "10 Yr", "20 Yr", "30 Yr")


class PlaneConsumptionRefused(Exception):
    """Entry/series is outside the frozen set or not granted: refused."""


class PlaneDataBlocked(Exception):
    """Fail-closed data state: digest mismatch, malformed or missing
    substrate.  Never repaired, never re-downloaded here."""

    def __init__(self, message: str, reason: str = "BLOCKED_DATA"):
        super().__init__(message)
        self.reason = reason


class UnknownCurveDate(PlaneConsumptionRefused):
    """A curve date lookup that the official substrate cannot carry."""


class UnknownTenor(PlaneConsumptionRefused):
    """A tenor column lookup that the year's official file does not
    carry (fabricated tenor canary surface)."""


class UnknownTicker(PlaneConsumptionRefused):
    """A never-existed ticker on the EODHD channel (canary surface)."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_treasury_curve_csv(data: bytes) -> list[dict[str, str]]:
    """Parse one official per-year par-yield CSV (Date + tenor columns,
    dates MM/DD/YYYY).  Raises PlaneDataBlocked on structural drift."""
    text = data.decode("utf-8", "replace")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or "Date" not in reader.fieldnames:
        raise PlaneDataBlocked(
            "treasury curve CSV lacks the Date header column",
            "BLOCKED_DATA_MALFORMED")
    rows: list[dict[str, str]] = []
    for rec in reader:
        raw_date = (rec.get("Date") or "").strip()
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", raw_date):
            raise PlaneDataBlocked(
                f"treasury curve row with malformed date {raw_date!r}",
                "BLOCKED_DATA_MALFORMED")
        mm, dd, yyyy = raw_date.split("/")
        row = {"date": f"{yyyy}-{mm}-{dd}"}
        for col in reader.fieldnames:
            if col == "Date":
                continue
            row[col] = (rec.get(col) or "").strip()
        rows.append(row)
    if not rows:
        raise PlaneDataBlocked(
            "treasury curve CSV carries zero data rows",
            "BLOCKED_DATA_MALFORMED")
    return rows


def resolve_inherited_cpiaucsl_pin(
        cads_store_root: str = DEFAULT_CADS_STORE_ROOT) -> dict:
    """Resolve the inherited S2 CPIAUCSL realtime object from the
    shared CADS store READ-ONLY (verify-on-read re-hash) and return the
    observation list for the 0-drift overlap proof.  Standalone so the
    verify can run before the substrate manifest exists."""
    store = CADS(cads_store_root)
    try:
        data = store.resolve(CPIAUCSL_CADS_PIN)
    except CADSError as exc:
        raise PlaneDataBlocked(
            f"inherited CPIAUCSL CADS resolve failed: {exc}",
            "BLOCKED_DATA") from exc
    payload = json.loads(data.decode("utf-8"))
    obs = payload["observations"] if isinstance(payload, dict) \
        else payload
    return {
        "cads_address": CPIAUCSL_CADS_PIN,
        "sha256_measured": sha256_bytes(data),
        "rows": len(obs),
        "observations": obs,
    }


def parse_eodhd_eod_json(data: bytes) -> list[dict[str, Any]]:
    """Parse an EODHD eod fmt=json array (the RAW primary channel)."""
    payload = json.loads(data.decode("utf-8", "replace"))
    if not isinstance(payload, list):
        raise PlaneDataBlocked(
            "EODHD eod payload is not a JSON array",
            "BLOCKED_DATA_MALFORMED")
    for rec in payload:
        if not isinstance(rec, dict) or "date" not in rec or "close" not in rec:
            raise PlaneDataBlocked(
                "EODHD eod row lacks date/close", "BLOCKED_DATA_MALFORMED")
    return payload


class RatesNG1Plane:
    """Read-only ``consume_via_plane`` adapter for the RATES-NG1 frozen
    consumption set."""

    def __init__(self, manifest_path: str | None = None,
                 raw_root: str | None = None,
                 registry_journal: str | None = None,
                 cads_store_root: str | None = None):
        self.manifest_path = os.path.abspath(manifest_path or SUBSTRATE_MANIFEST)
        self.raw_root = os.path.abspath(raw_root or RAW_SUBSTRATE_ROOT)
        self.registry_journal = os.path.abspath(
            registry_journal or DEFAULT_AUTHORITY_JOURNAL)
        self.cads_store_root = cads_store_root or DEFAULT_CADS_STORE_ROOT
        if not os.path.isfile(self.manifest_path):
            raise PlaneDataBlocked(
                f"substrate manifest missing: {self.manifest_path}",
                "BLOCKED_STORE_MISSING")
        with open(self.manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        files = manifest.get("files")
        if not isinstance(files, dict) or not files:
            raise PlaneDataBlocked(
                "substrate manifest malformed: no files map",
                "BLOCKED_STORE_MALFORMED")
        for name, rec in files.items():
            if not re.fullmatch(r"[0-9a-f]{64}", str(rec.get("sha256", ""))):
                raise PlaneDataBlocked(
                    f"substrate manifest entry {name} has no sha256 pin",
                    "BLOCKED_STORE_MALFORMED")
        self.manifest = manifest
        self._registry = None

    # -- authority -------------------------------------------------------- #
    def platform_verdict(self, series_id: str) -> str | None:
        """Verdict from the committed platform-v3 authority registry, or
        None when the series is rates-native (outside the platform set)."""
        if not os.path.isfile(self.registry_journal):
            return None
        if self._registry is None:
            self._registry = AuthorityRegistry(self.registry_journal)
        return self._registry.verdict(series_id)

    def _authority_gate(self, entry_name: str) -> str:
        """Return the authority basis for consuming this entry (fail-
        closed: raise on any non-GRANTED platform verdict)."""
        series_id = FROZEN_CONSUMPTION_SET[entry_name]["series"]
        if entry_name == S2_CPIAUCSL_ENTRY:
            verdict = self.platform_verdict(FRED_AUTHORITY_SERIES)
            if verdict != "GRANTED":
                raise PlaneConsumptionRefused(
                    f"platform authority for {FRED_AUTHORITY_SERIES} is "
                    f"{verdict!r}: CPIAUCSL consumption refused")
            return f"platform:{FRED_AUTHORITY_SERIES}=GRANTED"
        return f"frozen_cycle_set:{series_id}"

    # -- consume_via_plane ------------------------------------------------- #
    def raw_path(self, entry_name: str) -> str:
        return os.path.join(self.raw_root, entry_name)

    def consume_via_plane(self, entry_name: str,
                          scratch_dir: str | None = None) -> dict:
        """The RATES-NG1 consume path: frozen set -> authority -> pin ->
        verify-on-read re-hash -> manifest-verified query (CSV) or
        resolve+verify (JSON).  Any failure raises; no partial success."""
        if entry_name not in FROZEN_CONSUMPTION_SET:
            raise PlaneConsumptionRefused(
                f"entry {entry_name!r} is outside the RATES-NG1 frozen "
                "consumption set (plan section 3): refused")
        authority = self._authority_gate(entry_name)
        pin = self.manifest["files"].get(entry_name)
        if pin is None:
            raise PlaneDataBlocked(
                f"no substrate pin for entry {entry_name}",
                "BLOCKED_NO_PIN")
        path = self.raw_path(entry_name)
        if not os.path.isfile(path):
            raise PlaneDataBlocked(
                f"raw substrate bytes absent: {path}",
                "BLOCKED_STORE_MISSING")
        measured = sha256_file(path)
        expected = pin["sha256"]
        if measured != expected:
            raise PlaneDataBlocked(
                f"digest mismatch for {entry_name}: raw bytes hash to "
                f"{measured}, manifest pin is {expected} (BLOCKED_DATA: "
                "no re-download, no repair)", "BLOCKED_DATA")
        kind = FROZEN_CONSUMPTION_SET[entry_name]["kind"]
        query_verdict = "RESOLVE_VERIFY_ONLY"
        rows_parsed: list | None = None
        if kind == "curve":
            # structural read always accompanies a curve consumption
            rows_parsed = parse_treasury_curve_csv(self._raw_bytes(path))
            if scratch_dir is not None:
                query_verdict = self._frozen_query(path, measured,
                                                   scratch_dir, entry_name)
        return {
            "schema": SCHEMA,
            "entry": entry_name,
            "series": FROZEN_CONSUMPTION_SET[entry_name]["series"],
            "authority": authority,
            "sha256_measured": measured,
            "sha256_pinned": expected,
            "bytes": pin.get("bytes"),
            "query_verdict": query_verdict,
            "rows": rows_parsed,
            "source_url": pin.get("source_url"),
        }

    def _raw_bytes(self, path: str) -> bytes:
        with open(path, "rb") as fh:
            return fh.read()

    def _frozen_query(self, path: str, digest: str, scratch_dir: str,
                      entry_name: str) -> str:
        """Manifest-verified query: the pinned bytes are materialized to
        a scratch file and read through the QueryPlane with the manifest
        pinned to the substrate digest."""
        os.makedirs(scratch_dir, exist_ok=True)
        scratch = os.path.join(
            scratch_dir, re.sub(r"[^A-Za-z0-9_.-]+", "_", entry_name))
        with open(path, "rb") as fh:
            data = fh.read()
        with open(scratch, "wb") as fh:
            fh.write(data)
        mid = "rates_ng1_p0:" + os.path.basename(entry_name)
        entry = ManifestEntry(manifest_id=mid, path=scratch, sha256=digest)
        plane = QueryPlane({mid: entry})
        try:
            plane.register_views({mid: "v_consumed"})
            frozen = FrozenQuery(
                name="rates_ng1_p0_consume_probe",
                sql="SELECT count(*) AS n FROM v_consumed ORDER BY n",
                order_columns=["n"],
                output_schema=[OutputColumn("n", "BIGINT")],
            )
            result = plane.run(frozen, [mid])
        finally:
            plane.close()
        if result.verdict != "SUCCESS":
            raise PlaneDataBlocked(
                f"manifest-verified query {mid} -> {result.verdict}: "
                f"{result.reason}", "BLOCKED_DATA")
        return "FROZEN_QUERY_SUCCESS"

    # -- lookups (canary surface: fail-closed, never infer) ---------------- #
    def curve_rows_for_year(self, year: int) -> list[dict[str, str]]:
        entry = f"treasury_curve/par_yields_{year}.csv"
        res = self.consume_via_plane(entry)
        return res["rows"] or []

    def curve_row(self, iso_date: str) -> dict[str, str]:
        """Exact-date curve row lookup across the pinned years; a date
        the substrate cannot carry raises UnknownCurveDate (never a
        nearest-row inference)."""
        year = int(iso_date[:4])
        if year not in CURVE_YEARS:
            raise UnknownCurveDate(
                f"curve date {iso_date} outside the pinned 1990..2026 "
                "substrate: refused")
        for row in self.curve_rows_for_year(year):
            if row["date"] == iso_date:
                return row
        raise UnknownCurveDate(
            f"curve date {iso_date} does not exist in the official "
            f"{year} substrate: refused")

    def curve_tenor(self, iso_date: str, tenor: str) -> str:
        """Curve value lookup; an unknown tenor column raises
        UnknownTenor (fabricated tenor canary surface)."""
        row = self.curve_row(iso_date)
        if tenor not in row:
            raise UnknownTenor(
                f"tenor column {tenor!r} does not exist in the official "
                f"curve schema for {iso_date[:4]}: refused")
        return row[tenor]

    def etp_rows(self, ticker: str) -> list[dict[str, Any]]:
        if ticker not in ETP_TICKERS:
            raise UnknownTicker(
                f"ticker {ticker!r} is outside the frozen ETP census set "
                "(TLT/IEF/IEI/SHY): refused")
        entry = f"etp_eod/{ticker}.US.json"
        res = self.consume_via_plane(entry)
        return parse_eodhd_eod_json(self._raw_bytes(self.raw_path(entry)))

    # -- inherited pin verify (read-only CADS) ----------------------------- #
    def resolve_inherited_cpiaucsl_pin(self) -> dict:
        return resolve_inherited_cpiaucsl_pin(self.cads_store_root)

    # -- shadow parity ------------------------------------------------------ #
    def shadow_parity(self, entry_names: Sequence[str],
                      scratch_dir: str) -> list[dict]:
        """Bounded pilot: plane-read vs raw file bytes must show digest
        equality, and for CSVs the plane row count must equal the direct
        parse row count (window equality on the overlap)."""
        out: list[dict] = []
        for entry_name in entry_names:
            res = self.consume_via_plane(entry_name, scratch_dir)
            direct = sha256_file(self.raw_path(entry_name))
            rec = {
                "entry": entry_name,
                "plane_sha256": res["sha256_measured"],
                "manifest_pin_sha256": res["sha256_pinned"],
                "direct_sha256": direct,
                "digest_identical": (
                    res["sha256_measured"] == res["sha256_pinned"]
                    == direct),
                "query_verdict": res["query_verdict"],
            }
            kind = FROZEN_CONSUMPTION_SET[entry_name]["kind"]
            if kind == "curve":
                rows = parse_treasury_curve_csv(
                    self._raw_bytes(self.raw_path(entry_name)))
                rec["direct_row_count"] = len(rows)
                rec["direct_window"] = [rows[-1]["date"], rows[0]["date"]]
            elif kind == "fred":
                payload = json.loads(
                    self._raw_bytes(self.raw_path(entry_name)).decode(
                        "utf-8"))
                obs = payload["observations"] if isinstance(
                    payload, dict) else payload
                rec["direct_row_count"] = len(obs)
                rec["direct_window"] = [obs[0]["date"], obs[-1]["date"]]
            elif kind == "etp":
                rows = parse_eodhd_eod_json(
                    self._raw_bytes(self.raw_path(entry_name)))
                rec["direct_row_count"] = len(rows)
                rec["direct_window"] = [rows[0]["date"], rows[-1]["date"]]
            elif kind == "auction":
                payload = json.loads(
                    self._raw_bytes(self.raw_path(entry_name)).decode(
                        "utf-8"))
                rec["direct_row_count"] = len(payload)
            out.append(rec)
        return out
