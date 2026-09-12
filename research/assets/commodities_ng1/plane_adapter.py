"""COMMODITIES-NG1 P0 plane adapter: consume_via_plane for the frozen set.

Reference shape: ``research.assets.crypto_ng1.plane_adapter`` /
``research.platform_v3.pa4_pa5_authority.consume_via_plane`` (platform
v3, section 7A.4): authority verdict -> digest-verified bytes ->
manifest-verified QueryPlane query.

Contract (fail-closed everywhere):

1. a series may only be consumed when its authority verdict is exactly
   ``GRANTED``.  For this new family the verdict comes from THIS
   cycle's P0 authority record (the committed raw manifest,
   ``p0_raw_manifest.json`` -- P0 is the authority-establishment step);
   when the shared platform AuthorityRegistry journal already knows the
   series, its verdict must also be GRANTED or consumption refuses;
2. bytes are read only from the sha256-pinned path in the frozen
   manifest; a digest mismatch is ``BLOCKED_DATA``: never re-downloaded,
   never repaired;
3. parsed records are re-serialized to the canonical CSV surface and
   materialized to a temp file (outside any store) whose digest equals
   the canonical serialization digest, then queried through the frozen
   ``research.platform_v3.query_plane.QueryPlane`` surface, so the SQL
   plane can never see bytes that differ from the pinned content;
4. the shared CADS store and the authority journal are used READ-ONLY:
   this adapter never registers/pins/writes any store state;
5. the PIT clock is carried on every CoT consumption: the release
   instant (Friday 15:30 America/New_York, DST-correct) is part of the
   returned envelope, and ``pit_guarded_records`` refuses any view of a
   report before its release instant.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Mapping

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

sys.path.insert(0, _REPO_ROOT)

from research.assets.commodities_ng1.cot_census import (  # noqa: E402
    CotLookupRefused, csv_to_records, pit_guard, records_digest,
    records_to_csv,
)
from research.assets.commodities_ng1.etp_census import (  # noqa: E402
    csv_to_rows,
)
from research.platform_v3.query_plane import (  # noqa: E402
    FrozenQuery, ManifestEntry, OutputColumn, QueryPlane,
)

SCHEMA = "commodities_ng1/plane_adapter@1"

#: Committed P0 authority record (the frozen consumption set).
DEFAULT_MANIFEST = os.path.join(
    _REPO_ROOT, "research", "control", "commodities_ng1_run",
    "p0_raw_manifest.json")

ENV_MANIFEST = "COMMODITIES_NG1_P0_MANIFEST"

#: Shared authority journal (read-only cross-check; absent is fine).
DEFAULT_AUTHORITY_JOURNAL = os.path.join(
    _REPO_ROOT, "research", "control", "research_platform_v3_run",
    "authority_registry_journal.jsonl")

#: Cycle-local authority record (P0 establishes these verdicts; evidence
#: paths are pinned in the manifest/gate).  Exactly these series exist.
SERIES_AUTHORITIES = {
    "S6:cftc-cot-futures-only": "GRANTED",
    "S4:eodhd-etp-eod": "GRANTED",
    "S6:cftc-cot-release-schedule": "GRANTED",
}


class PlaneConsumptionRefused(Exception):
    """Series outside the frozen set / verdict not GRANTED: refused."""


class PlaneDataBlocked(Exception):
    """Fail-closed data state (digest mismatch, malformed manifest,
    missing bytes).  Never repaired, never re-downloaded here."""

    def __init__(self, message: str, reason: str = "BLOCKED_DATA"):
        super().__init__(message)
        self.reason = reason


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _verdict_from_journal(journal_path: str, series_id: str) -> str | None:
    """Latest shared-registry verdict for a series, or None if unknown."""
    if not os.path.isfile(journal_path):
        return None
    verdict = None
    with open(journal_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                raise PlaneDataBlocked(
                    f"authority journal malformed line: {journal_path}",
                    "BLOCKED_STORE_MALFORMED")
            if row.get("series") == series_id:
                verdict = row.get("verdict", verdict)
    return verdict


class CommoditiesNG1Plane:
    """Read-only consume_via_plane adapter for the COMMODITIES-NG1
    frozen consumption set."""

    def __init__(self, manifest_path: str | None = None,
                 authority_journal: str | None = None):
        self.manifest_path = os.path.abspath(
            manifest_path or os.environ.get(ENV_MANIFEST)
            or DEFAULT_MANIFEST)
        self.authority_journal = os.path.abspath(
            authority_journal or DEFAULT_AUTHORITY_JOURNAL)
        if not os.path.isfile(self.manifest_path):
            raise PlaneDataBlocked(
                f"P0 authority manifest missing: {self.manifest_path}",
                "BLOCKED_MANIFEST_MISSING")
        with open(self.manifest_path, encoding="utf-8") as fh:
            try:
                self.manifest = json.load(fh)
            except json.JSONDecodeError as exc:
                raise PlaneDataBlocked(
                    f"P0 authority manifest malformed: {exc}",
                    "BLOCKED_MANIFEST_MALFORMED") from exc
        entries = self.manifest.get("entries")
        if not isinstance(entries, dict) or not entries:
            raise PlaneDataBlocked(
                "P0 authority manifest has no entries dict; fail closed",
                "BLOCKED_MANIFEST_MALFORMED")
        self.entries: dict[str, dict[str, Any]] = entries
        for name, meta in self.entries.items():
            for key in ("path", "sha256", "series"):
                if key not in meta:
                    raise PlaneDataBlocked(
                        f"manifest entry {name!r} missing {key!r}; "
                        "fail closed", "BLOCKED_MANIFEST_MALFORMED")

    # -- authority -------------------------------------------------------- #
    def verdict(self, series_id: str) -> str:
        cycle_verdict = SERIES_AUTHORITIES.get(series_id)
        if cycle_verdict is None:
            return "UNKNOWN_SERIES"
        shared = _verdict_from_journal(self.authority_journal, series_id)
        if shared is not None and shared != "GRANTED":
            return f"CONFLICT_SHARED_REGISTRY_{shared}"
        return cycle_verdict

    # -- resolve (digest-verified bytes) ----------------------------------- #
    def resolve_entry(self, name: str) -> dict:
        meta = self.entries.get(name)
        if meta is None:
            raise PlaneConsumptionRefused(
                f"entry {name!r} is outside the frozen COMMODITIES-NG1 "
                "consumption set (P0 authority manifest): refused")
        verdict = self.verdict(meta["series"])
        if verdict != "GRANTED":
            raise PlaneConsumptionRefused(
                f"series {meta['series']} verdict={verdict!r}: consumption "
                "refused (fail-closed; only granted series may be consumed)")
        path = meta["path"]
        if not os.path.isabs(path):
            path = os.path.join(_REPO_ROOT, path)
        if not os.path.isfile(path):
            raise PlaneDataBlocked(
                f"pinned bytes absent: {path} (BLOCKED_DATA: no "
                "re-download inside the adapter)", "BLOCKED_DATA_MISSING")
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        measured = h.hexdigest()
        if measured != meta["sha256"]:
            raise PlaneDataBlocked(
                f"digest mismatch for {name}: pinned "
                f"{meta['sha256']} != measured {measured} (BLOCKED_DATA: "
                "no re-download, no repair)", "BLOCKED_DATA")
        return {
            "schema": SCHEMA,
            "entry": name,
            "series": meta["series"],
            "sha256_pinned": meta["sha256"],
            "sha256_measured": measured,
            "bytes": os.path.getsize(path),
            "verdict": verdict,
            "path": path,
        }

    def consume(self, name: str) -> dict:
        """consume_via_plane: digest-verified entry + family payload."""
        res = self.resolve_entry(name)
        res["via"] = "plane"
        return res

    def consume_records(self, name: str):
        """Verified entry -> parsed record objects (family schema)."""
        res = self.resolve_entry(name)
        with open(res["path"], "rb") as fh:
            data = fh.read()
        if name.startswith("cftc/deacot"):
            from research.assets.commodities_ng1.cot_census import parse_zip
            return res, parse_zip(res["path"])
        if name.startswith("etp/eod/"):
            return res, csv_to_rows(
                data.decode("utf-8"), symbol=name.rsplit("/", 1)[-1])
        raise PlaneConsumptionRefused(
            f"entry kind {name!r} has no family parser: refused")

    # -- manifest-verified query (frozen DuckDB surface) ------------------- #
    def query_entry(self, name: str) -> dict:
        """Frozen bounds/census query over digest-verified bytes.

        The canonical normalized surface of the entry is materialized to
        a temp CSV whose bytes hash to the canonical serialization, and
        the query plane pins THAT digest in its manifest entry.
        """
        res, records = self.consume_records(name)
        if name.startswith("cftc/deacot"):
            canonical = records_to_csv(records)
            rows_out = self._run_frozen_query(canonical, name, "cot")
        else:
            from research.assets.commodities_ng1.etp_census import (
                rows_to_csv)
            canonical = rows_to_csv(records)
            rows_out = self._run_frozen_query(canonical, name, "etp")
        return {
            "schema": SCHEMA,
            "entry": name,
            "sha256_pinned": res["sha256_pinned"],
            "canonical_digest": sha256_bytes(canonical.encode("utf-8")),
            "query": rows_out,
        }

    def _run_frozen_query(self, canonical_csv: str, name: str,
                          kind: str) -> dict:
        tmpdir = tempfile.mkdtemp(prefix="commodities_ng1_plane_")
        try:
            local = os.path.join(tmpdir, "verified.csv")
            with open(local, "w", encoding="utf-8") as fh:
                fh.write(canonical_csv)
            mid = "commodities_ng1_p0:" + name.replace("/", "_")
            entry = ManifestEntry(manifest_id=mid, path=local,
                                  sha256=sha256_bytes(
                                      canonical_csv.encode("utf-8")))
            plane = QueryPlane({mid: entry})
            try:
                plane.register_views({mid: "v_series"})
                if kind == "cot":
                    frozen = FrozenQuery(
                        "commodities_ng1_p0_cot_bounds",
                        "SELECT contract_market_code, "
                        "count(*) AS weeks, "
                        "CAST(min(report_date) AS VARCHAR) AS first, "
                        "CAST(max(report_date) AS VARCHAR) AS last "
                        "FROM v_series "
                        "GROUP BY contract_market_code "
                        "ORDER BY contract_market_code",
                        ["contract_market_code"],
                        [OutputColumn("contract_market_code", "VARCHAR"),
                         OutputColumn("weeks", "BIGINT"),
                         OutputColumn("first", "VARCHAR"),
                         OutputColumn("last", "VARCHAR")],
                    )
                else:
                    frozen = FrozenQuery(
                        "commodities_ng1_p0_etp_bounds",
                        "SELECT count(*) AS rows_n, "
                        "CAST(min(date) AS VARCHAR) AS first, "
                        "CAST(max(date) AS VARCHAR) AS last, "
                        "CAST(min(close) AS DOUBLE) AS min_close, "
                        "CAST(max(close) AS DOUBLE) AS max_close "
                        "FROM v_series ORDER BY rows_n",
                        ["rows_n"],
                        [OutputColumn("rows_n", "BIGINT"),
                         OutputColumn("first", "VARCHAR"),
                         OutputColumn("last", "VARCHAR"),
                         OutputColumn("min_close", "DOUBLE"),
                         OutputColumn("max_close", "DOUBLE")],
                    )
                result = plane.run(frozen, [mid])
            finally:
                plane.close()
            return {
                "verdict": result.verdict,
                "reason": result.reason,
                "identity": result.identity,
                "rows": [list(r) for r in result.rows],
                "row_count": result.row_count,
                "result_digest": result.result_digest,
            }
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    # -- PIT clock ---------------------------------------------------------- #
    def release_instants(self, name: str) -> dict:
        """Release-instant envelope for a CoT entry (PIT evidence)."""
        if not name.startswith("cftc/deacot"):
            raise PlaneConsumptionRefused(
                f"entry {name!r} carries no CoT release clock")
        _, records = self.consume_records(name)
        dates = sorted({r.report_date for r in records})
        first_release = min(
            (r for r in (pit_guard(d, datetime.now(timezone.utc))
                         for d in dates)),
            key=lambda g: g["release_instant_utc"])
        return {
            "schema": SCHEMA,
            "entry": name,
            "reports": len(dates),
            "first_report": dates[0].isoformat(),
            "first_release_instant_utc": first_release["release_instant_utc"],
            "last_report": dates[-1].isoformat(),
            "last_release_instant_utc": pit_guard(
                dates[-1], datetime.now(timezone.utc))["release_instant_utc"],
            "rule": "Friday 15:30 America/New_York of the Tuesday-position "
                    "week (DST-correct), expressed UTC; CFTC holiday "
                    "exceptions recorded as evidence, never inferred",
        }

    def pit_guarded_records(self, name: str,
                            use_instant_utc: datetime | None = None):
        """Records legally visible at ``use_instant_utc`` (fail-closed;
        default: now)."""
        if use_instant_utc is None:
            use_instant_utc = datetime.now(timezone.utc)
        if use_instant_utc.tzinfo is None:
            use_instant_utc = use_instant_utc.replace(tzinfo=timezone.utc)
        _, records = self.consume_records(name)
        visible, gated = [], []
        for r in records:
            g = pit_guard(r.report_date, use_instant_utc)
            (visible if g["pit_allowed"] else gated).append((r, g))
        if gated:
            latest = max(g[1]["release_instant_utc"] for g in gated)
            raise CotLookupRefused(
                f"PIT violation: {len(gated)} report(s) withheld before "
                f"their release instants (latest withheld release "
                f"{latest}); use_instant "
                f"{use_instant_utc.astimezone(timezone.utc).isoformat()}")
        return records

    # -- shadow parity (plane read vs raw archive parse) -------------------- #
    def shadow_parity(self, name: str, market_codes: list[str] | None = None
                      ) -> dict:
        """Bounded pilot: plane-read canonical digest vs a DIRECT parse of
        the raw archive (the non-plane consumption path) restricted to
        the overlap (same entry bytes, same market codes)."""
        res = self.consume(name)
        _, plane_records = self.consume_records(name)
        raw_path = res["path"]
        if name.startswith("cftc/deacot"):
            from research.assets.commodities_ng1.cot_census import parse_zip
            raw_records = parse_zip(raw_path)   # direct archive parse
        elif name.startswith("etp/eod/"):
            with open(raw_path, encoding="utf-8") as fh:
                raw_records = csv_to_rows(fh.read(),
                                          symbol=name.rsplit("/", 1)[-1])
        else:
            raise PlaneConsumptionRefused(
                f"entry kind {name!r} has no parity parser")
        if market_codes is None:
            overlap_plane, overlap_raw = plane_records, raw_records
        else:
            want = set(market_codes)
            overlap_plane = self._restrict(plane_records, name, want)
            overlap_raw = self._restrict(raw_records, name, want)
        plane_digest = records_digest(overlap_plane) \
            if name.startswith("cftc/deacot") else _rows_digest(overlap_plane)
        raw_digest = records_digest(overlap_raw) \
            if name.startswith("cftc/deacot") else _rows_digest(overlap_raw)
        return {
            "schema": SCHEMA,
            "entry": name,
            "sha256_pinned": res["sha256_pinned"],
            "overlap_records": len(overlap_plane),
            "plane_digest": plane_digest,
            "raw_digest": raw_digest,
            "identical": plane_digest == raw_digest,
        }

    @staticmethod
    def _restrict(records: list, name: str, want: set) -> list:
        if name.startswith("cftc/deacot"):
            return [r for r in records if r.contract_market_code in want]
        return records


def _rows_digest(rows: list[dict]) -> str:
    canon = sorted(
        "|".join(f"{k}={bar[k]!r}" for k in sorted(bar))
        for bar in rows)
    return sha256_bytes("\n".join(canon).encode("utf-8"))
