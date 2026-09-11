"""CRYPTO-NG1 P0 plane adapter: consume_via_plane for the frozen S4 set.

Reference shape: ``research.platform_v3.pa4_pa5_authority.consume_via_plane``
(section 7A.4 of the platform v3 plan): AuthorityRegistry verdict ->
CADS resolve verify-on-read -> manifest-verified query.

Contract (fail-closed everywhere):

1. a series may only be consumed when the authority registry verdict is
   exactly ``GRANTED`` (anything else, including unknown series, refuses);
2. the CADS pin address must equal the FROZEN digest from the cycle plan
   (section 3) -- a mismatch is ``BLOCKED_DATA``: never re-downloaded,
   never repaired;
3. bytes come from ``CADS.resolve`` (verify-on-read); corruption raises
   and the adapter surfaces it as ``BLOCKED_DATA``;
4. the CADS store is used READ-ONLY: this adapter never calls
   register/pin/restore and never writes into the store root.  Missing
   store state fails closed instead of being created.

The manifest-verified query path materializes resolved bytes into a
temp file (outside the store) and runs a frozen DuckDB query through
``research.platform_v3.query_plane.QueryPlane`` with the manifest entry
pinned to the CADS address, so the query surface can never see bytes
that differ from the content-addressed object.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from typing import Any, Mapping

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

sys.path.insert(0, _REPO_ROOT)

from research.platform_v3.authority import AuthorityRegistry  # noqa: E402
from research.platform_v3.cads import (  # noqa: E402
    CADS, CADSError, CADSIntegrityError, ControlStateDrift,
)
from research.platform_v3.query_plane import (  # noqa: E402
    FrozenQuery, ManifestEntry, OutputColumn, QueryPlane, QueryPlaneError,
)

SCHEMA = "crypto_ng1/plane_adapter@1"

#: Read-only CADS store root (env override -> parameter -> default).
ENV_CADS_STORE_ROOT = "CRYPTO_NG1_CADS_STORE_ROOT"
DEFAULT_CADS_STORE_ROOT = (
    "/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store")

#: Authority registry journal (read-only projection; env override -> default).
ENV_AUTHORITY_JOURNAL = "CRYPTO_NG1_AUTHORITY_JOURNAL"
DEFAULT_AUTHORITY_JOURNAL = os.path.join(
    _REPO_ROOT, "research", "control", "research_platform_v3_run",
    "authority_registry_journal.jsonl")

#: Frozen S4 consumption set (cycle plan section 3; GA4 GRANTED, CADS S4).
#: entry name -> {series, sha256}.  Exactly these five, nothing else.
FROZEN_S4_ENTRIES: dict[str, dict[str, str]] = {
    "staging_v17/panel_BTCUSDT_h1.csv": {
        "series": "S4:binance-daily-h1-panels",
        "sha256": "111c1a2d6d62e26c1874bb428c10216e4926ae37ab0102ca098849ca25f5e7b1",
    },
    "staging_v17/panel_ETHUSDT_h1.csv": {
        "series": "S4:binance-daily-h1-panels",
        "sha256": "ebd487a69404a1104d9123584c93af044a2796c338185d8466599b9f34bb440b",
    },
    "staging_v17/panel_SOLUSDT_h1.csv": {
        "series": "S4:binance-daily-h1-panels",
        "sha256": "c4ca0b6eb719122054abec2a03fcac20d3f7794c5bf6d3c546ee6db1cb6e2107",
    },
    "staging_v17/panel_manifest.json": {
        "series": "S4:binance-daily-h1-panels",
        "sha256": "761190a52e6504a74e12748efdb232dba03b40fa3065d35820b025283122e08b",
    },
    "oi_series_reduced.json": {
        "series": "S4:binance-open-interest",
        "sha256": "f26a61e45a0f79322140c66a1a8862b6d933e0a831d7559af459ef638fbefbd3",
    },
}

#: Panel H1 CSV columns/types needed by the frozen bounds query (probed
#: against the frozen panels; the plane enforces exact schema match).
_PANEL_BOUNDS_SCHEMA = [
    OutputColumn("symbol", "VARCHAR"),
    OutputColumn("n_rows", "BIGINT"),
    OutputColumn("first_hour", "VARCHAR"),
    OutputColumn("last_hour", "VARCHAR"),
]


class PlaneConsumptionRefused(Exception):
    """Series is not GRANTED (or is outside the frozen set): refused."""


class PlaneDataBlocked(Exception):
    """Fail-closed data state: digest mismatch, corruption, malformed or
    missing store.  Never repaired, never retried here."""

    def __init__(self, message: str, reason: str = "BLOCKED_DATA"):
        super().__init__(message)
        self.reason = reason


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CryptoNG1Plane:
    """Read-only consume_via_plane adapter for the CRYPTO-NG1 frozen set."""

    def __init__(self, store_root: str | None = None,
                 registry_journal: str | None = None):
        self.store_root = os.path.abspath(
            store_root or os.environ.get(ENV_CADS_STORE_ROOT)
            or DEFAULT_CADS_STORE_ROOT)
        self.registry_journal = os.path.abspath(
            registry_journal or os.environ.get(ENV_AUTHORITY_JOURNAL)
            or DEFAULT_AUTHORITY_JOURNAL)
        # -- fail-closed existence checks BEFORE any object is built:
        #    constructing CADS would create directories, and this adapter
        #    must never create store state.
        if not os.path.isdir(self.store_root):
            raise PlaneDataBlocked(
                f"CADS store root missing: {self.store_root}", 
                "BLOCKED_STORE_MISSING")
        if not os.path.isdir(os.path.join(self.store_root, "objects")):
            raise PlaneDataBlocked(
                f"CADS objects dir missing under {self.store_root}",
                "BLOCKED_STORE_MALFORMED")
        if not os.path.isfile(os.path.join(self.store_root, "pins.jsonl")):
            raise PlaneDataBlocked(
                f"CADS pins.jsonl missing under {self.store_root}",
                "BLOCKED_STORE_MALFORMED")
        if not os.path.isfile(self.registry_journal):
            raise PlaneDataBlocked(
                f"authority journal missing: {self.registry_journal}",
                "BLOCKED_STORE_MISSING")
        # -- read-only projections (no write method is ever called) ------ #
        self._registry = AuthorityRegistry(self.registry_journal)
        self._store = CADS(self.store_root)
        try:
            self._pins = self._store.pins()
        except ControlStateDrift as exc:
            raise PlaneDataBlocked(
                f"CADS pins journal malformed: {exc}",
                "BLOCKED_STORE_MALFORMED") from exc

    # -- registry ---------------------------------------------------------- #
    def verdict(self, series_id: str) -> str:
        return self._registry.verdict(series_id)

    # -- pin lookup (pa4_pa5 shape: exact series, then stage prefix) ------ #
    def find_pin(self, series_id: str,
                 entry_name: str) -> Mapping[str, Any] | None:
        exact = [
            p for p in self._pins
            if p["metadata"].get("series") == series_id
            and (p["metadata"].get("file") or "").endswith(entry_name)
        ]
        if exact:
            return exact[-1]
        stage = series_id.split(":")[0]
        stage_pins = [
            p for p in self._pins
            if (p["metadata"].get("series") or "").startswith(stage)
            and (p["metadata"].get("file") or "").endswith(entry_name)
        ]
        if stage_pins:
            return stage_pins[-1]
        return None

    # -- resolve (verify-on-read + frozen digest) -------------------------- #
    def resolve_entry(self, series_id: str, entry_name: str,
                      expected_sha256: str | None = None) -> dict:
        verdict = self.verdict(series_id)
        if verdict != "GRANTED":
            raise PlaneConsumptionRefused(
                f"series {series_id} verdict={verdict!r}: consumption "
                "refused (fail-closed; only granted series may be consumed)")
        pin = self.find_pin(series_id, entry_name)
        if pin is None:
            raise PlaneDataBlocked(
                f"no CADS pin for series {series_id} entry {entry_name}",
                "BLOCKED_NO_PIN")
        address = pin["address"]
        expected = (expected_sha256
                    or FROZEN_S4_ENTRIES.get(entry_name, {}).get("sha256"))
        if expected is not None and address != expected:
            raise PlaneDataBlocked(
                f"digest mismatch for {entry_name}: CADS pin address "
                f"{address} != frozen {expected} (BLOCKED_DATA: no "
                "re-download, no repair)", "BLOCKED_DATA")
        try:
            data = self._store.resolve(address)   # verify-on-read
        except CADSIntegrityError as exc:
            raise PlaneDataBlocked(
                f"CADS integrity failure for {entry_name}: {exc} "
                "(corruption incident, fail-closed)", "BLOCKED_DATA") from exc
        except CADSError as exc:
            raise PlaneDataBlocked(
                f"CADS resolve failed for {entry_name}: {exc}",
                "BLOCKED_STORE_MALFORMED") from exc
        measured = sha256_bytes(data)
        if expected is not None and measured != expected:
            raise PlaneDataBlocked(
                f"digest mismatch for {entry_name}: resolved bytes hash to "
                f"{measured}, frozen digest is {expected} (BLOCKED_DATA: no "
                "re-download, no repair)", "BLOCKED_DATA")
        return {
            "schema": SCHEMA,
            "series_requested": series_id,
            "series_pinned": pin["metadata"].get("series"),
            "entry": entry_name,
            "cads_address": address,
            "sha256_measured": measured,
            "bytes": len(data),
            "verdict": verdict,
            "data": data,
        }

    def consume(self, entry_name: str) -> dict:
        """Consume one entry of the frozen S4 set by entry name."""
        if entry_name not in FROZEN_S4_ENTRIES:
            raise PlaneConsumptionRefused(
                f"entry {entry_name!r} is outside the frozen S4 consumption "
                "set (plan section 3): refused")
        meta = FROZEN_S4_ENTRIES[entry_name]
        return self.resolve_entry(meta["series"], entry_name, meta["sha256"])

    def object_path(self, address: str) -> str:
        return os.path.join(self.store_root, "objects", address[:2], address)

    # -- shadow parity (plane read vs direct CADS-object read) ------------- #
    def shadow_parity(self, entry_name: str, series: str | None = None,
                      expected_sha256: str | None = None) -> dict:
        """Bounded pilot: plane-read digest vs a plain direct read of the
        CADS-resolved object file (the V17-era consumption path).

        Production calls pass only ``entry_name`` (frozen set).  The
        optional ``series``/``expected_sha256`` explicit form exists for
        sandboxed tests on throwaway stores."""
        if series is not None:
            res = self.resolve_entry(series, entry_name, expected_sha256)
        else:
            res = self.consume(entry_name)
        plane_sha = res["sha256_measured"]
        path = self.object_path(res["cads_address"])
        if not os.path.isfile(path):
            raise PlaneDataBlocked(
                f"CADS object file absent for direct read: {path}",
                "BLOCKED_STORE_MALFORMED")
        h = hashlib.sha256()
        with open(path, "rb") as fh:               # direct file read
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        direct_sha = h.hexdigest()
        return {
            "schema": SCHEMA,
            "entry": entry_name,
            "cads_address": res["cads_address"],
            "plane_sha256": plane_sha,
            "direct_sha256": direct_sha,
            "identical": plane_sha == direct_sha,
            "bytes": res["bytes"],
        }

    # -- manifest-verified query (frozen DuckDB surface) ------------------- #
    def query_panel_bounds(self, entry_name: str, series: str | None = None,
                           expected_sha256: str | None = None) -> dict:
        """Run the frozen bounds query over a panel CSV through the
        manifest-verified query plane (bytes materialized to a temp file
        pinned by CADS address, never touching the store).

        Production calls pass only ``entry_name`` (frozen set).  The
        optional ``series``/``expected_sha256`` explicit form exists for
        sandboxed tests on throwaway stores."""
        if series is not None:
            res = self.resolve_entry(series, entry_name, expected_sha256)
        else:
            res = self.consume(entry_name)
        tmpdir = tempfile.mkdtemp(prefix="crypto_ng1_plane_")
        try:
            local = os.path.join(tmpdir, os.path.basename(entry_name))
            with open(local, "wb") as fh:
                fh.write(res["data"])
            mid = "ng1_p0:" + os.path.basename(entry_name)
            entry = ManifestEntry(manifest_id=mid, path=local,
                                  sha256=res["cads_address"])
            plane = QueryPlane({mid: entry})
            try:
                plane.register_views({mid: "v_panel"})
                frozen = FrozenQuery(
                    "crypto_ng1_p0_panel_bounds",
                    "SELECT symbol, count(*) AS n_rows, "
                    "min(hour_utc) AS first_hour, max(hour_utc) AS last_hour "
                    "FROM v_panel GROUP BY symbol ORDER BY symbol",
                    ["symbol"],
                    list(_PANEL_BOUNDS_SCHEMA),
                )
                result = plane.run(frozen, [mid])
            finally:
                plane.close()
            return {
                "schema": SCHEMA,
                "entry": entry_name,
                "cads_address": res["cads_address"],
                "query_verdict": result.verdict,
                "reason": result.reason,
                "identity": result.identity,
                "rows": [list(r) for r in result.rows],
                "row_count": result.row_count,
                "result_digest": result.result_digest,
            }
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
