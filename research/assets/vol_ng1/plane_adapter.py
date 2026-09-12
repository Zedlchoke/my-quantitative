"""VOL-NG1 P0 plane adapter: consume_via_plane for the frozen S7/EODHD-F1 set.

Reference shape: ``research.assets.crypto_ng1.plane_adapter`` and
``research.assets.forex_ng1.plane_adapter`` (section 7A.4 of the
platform v3 plan): authority verdict -> CADS resolve verify-on-read ->
manifest-verified query.

Contract (fail-closed everywhere):

1. a series may only be consumed when the authority registry verdict is
   exactly ``GRANTED`` (anything else, including unknown series,
   refuses);
2. the CADS pin address must equal the FROZEN digest recorded below
   (the P0-measured snapshot of the plan section-3 consumption set) --
   a mismatch is ``BLOCKED_DATA``: never re-downloaded, never repaired;
3. bytes come from ``CADS.resolve`` (verify-on-read); corruption raises
   and the adapter surfaces it as ``BLOCKED_DATA``;
4. the cycle store is used READ-ONLY after adoption: this adapter never
   calls register/pin; missing store state fails closed instead of
   being created.

Cycle authority: platform v3's ``FROZEN_TARGET_SET`` is the platform's
own S1-S4 set; the VOL-NG1 plan (section 3, registered 2026-09-12) IS
this cycle's plan amendment and freezes exactly the three series below.
``VolNg1Authority`` therefore widens ONLY the registration target set
to the plan-frozen trio and inherits the entire state machine
unchanged: GRANT still requires PIT=PASS_PIT_EVIDENCED + license +
entitlement + a PASS channel canary + >= 1 CADS pin, unknown series
stay BLOCKED_DATA by default, and no backward transitions exist.

Shadow parity (bounded pilot): sha256(CADS-resolved bytes via the
plane) == sha256(the committed raw bytes on disk), per entry.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.platform_v3.authority import (  # noqa: E402
    AuthorityError, AuthorityRegistry, NotInTargetSet,
)
from research.platform_v3.cads import (  # noqa: E402
    CADS, CADSError, CADSIntegrityError, ControlStateDrift,
)
from research.platform_v3.query_plane import (  # noqa: E402
    FrozenQuery, ManifestEntry, OutputColumn, QueryPlane,
)

SCHEMA = "vol_ng1/plane_adapter@1"

#: Cycle-scoped CADS store + authority journal (COMMITTED adoption
#: artifacts under this cycle's own control directory; read-only here).
DEFAULT_STORE_ROOT = os.path.join(
    REPO_ROOT, "research", "control", "vol_ng1_run", "cads_store")
DEFAULT_AUTHORITY_JOURNAL = os.path.join(
    REPO_ROOT, "research", "control", "vol_ng1_run",
    "authority_registry_journal.jsonl")

#: Committed raw-byte snapshots (the shadow-parity "raw" side).
RAW_ROOT = os.path.join(REPO_ROOT, "research", "assets", "vol_ng1", "raw")

#: Cycle-frozen series ids (plan section 3 -- nothing else exists).
SERIES_CBOE = "S7:cboe-vol-index-histories"
SERIES_ETP_EOD = "EODHD-F1:eodhd-vol-etp-eod"
SERIES_ETP_DELISTED = "EODHD-F1:eodhd-vol-etp-delisted"

#: The complete VOL-NG1 frozen target set.  Additions need a plan
#: amendment (defaults BLOCKED_DATA).
FROZEN_TARGET_SET = frozenset({
    SERIES_CBOE, SERIES_ETP_EOD, SERIES_ETP_DELISTED,
})

#: Channels (one canary probe each, recorded in the journal).
CHANNEL_CBOE = "cboe-official"
CHANNEL_EODHD_EOD = "eodhd-eod"
CHANNEL_EODHD_DELISTED = "eodhd-delisted"

#: ------------------------------------------------------------------ #
#: Frozen consumption set: entry name -> {series, sha256, raw_path}.
#: Digests are the P0-measured snapshot (2026-09-12 pulls, committed
#: under research/assets/vol_ng1/raw/).  A later re-pull gains a new
#: official daily row by construction and is a NEW dated snapshot, not
#: a repair of this one.
#: ------------------------------------------------------------------ #
FROZEN_ENTRIES: dict[str, dict[str, str]] = {
    "VIX_History.csv": {
        "series": SERIES_CBOE,
        "sha256": "cb3515efe5577d39df5c59ab44fb69171e28927e0fd01b50ce101076e7951e93",
        "raw_path": "cboe/VIX_History.csv",
    },
    "VIX9D_History.csv": {
        "series": SERIES_CBOE,
        "sha256": "7b3db3ecfa3d4e4506c540f82358e8d726daa76572f3ba4a5dc2bf41a4a32aea",
        "raw_path": "cboe/VIX9D_History.csv",
    },
    "VIX3M_History.csv": {
        "series": SERIES_CBOE,
        "sha256": "519408c5638f731eb47177ef7bcfbdd315a376ec353df52cd92ea67c9a51be65",
        "raw_path": "cboe/VIX3M_History.csv",
    },
    "VIX6M_History.csv": {
        "series": SERIES_CBOE,
        "sha256": "090544e05ee19151df4a8a12544c9b9c376b81034de51b3295b6b04c4bc314f5",
        "raw_path": "cboe/VIX6M_History.csv",
    },
}

#: EODHD-F1 living legs (measured 2026-09-12 pulls, committed under
#: research/assets/vol_ng1/raw/eodhd/).
_LIVING_LEG_ENTRIES: dict[str, dict[str, str]] = {
    "VXX.US_eod.json": {
        "series": SERIES_ETP_EOD,
        "sha256": "128bb58923d70e0f9c28a9b72924b32920cbc6ea382808f1785d2319c28f6bb7",
        "raw_path": "eodhd/VXX.US_eod.json",
    },
    "UVXY.US_eod.json": {
        "series": SERIES_ETP_EOD,
        "sha256": "22121044ed86ee64d2c2ea4ab79d74e09759eb2e8ff13dcda380bc175d908c63",
        "raw_path": "eodhd/UVXY.US_eod.json",
    },
    "SVXY.US_eod.json": {
        "series": SERIES_ETP_EOD,
        "sha256": "5d2e17b8dc41da41329130b30ad5a5858d122710f0e4d8f4a406401eacb9561c",
        "raw_path": "eodhd/SVXY.US_eod.json",
    },
    "VIXY.US_eod.json": {
        "series": SERIES_ETP_EOD,
        "sha256": "51719dde8ba4def1e3c4a14d5d99c37a8e621079660bcec66b2ba3c00b1276da",
        "raw_path": "eodhd/VIXY.US_eod.json",
    },
    "VIXM.US_eod.json": {
        "series": SERIES_ETP_EOD,
        "sha256": "ad28db0e6eedb5484253cf6b41f85c6421ac80889ca3de247961417ed34f4d54",
        "raw_path": "eodhd/VIXM.US_eod.json",
    },
    "VXZ.US_eod.json": {
        "series": SERIES_ETP_EOD,
        "sha256": "3a5e5e3f37c61420a09fadac16c25931b9441c797e180125fcb6ab6f9079e1d1",
        "raw_path": "eodhd/VXZ.US_eod.json",
    },
}

#: EODHD-F1 delisted-channel census (the committed control artifact;
#: raw_path is relative to RAW_ROOT and reaches this cycle's control
#: directory).
_DELISTED_ENTRIES: dict[str, dict[str, str]] = {
    "eodhd_us_delisted_census.json": {
        "series": SERIES_ETP_DELISTED,
        "sha256": "e35a9ae5442b0ba6a46ca2f0746a70c1cdf59c13975a8b1fb13ca5cbbdb32fc9",
        "raw_path": "../../../control/vol_ng1_run/p0_delisted_census.json",
    },
}


def register_entry_digest(entry_name: str, series: str, sha256: str,
                          raw_path: str) -> None:
    """Ingest-stage registration of a frozen digest (called by the P0
    runner with the measured values; refuses re-registration with a
    different digest)."""
    existing = _LIVING_LEG_ENTRIES.get(entry_name) \
        or _DELISTED_ENTRIES.get(entry_name) \
        or FROZEN_ENTRIES.get(entry_name)
    if existing is not None:
        if existing["sha256"] != sha256:
            raise PlaneDataBlocked(
                f"entry {entry_name} already frozen at "
                f"{existing['sha256']}, refusing {sha256}",
                "BLOCKED_DATA")
        return
    target = (_LIVING_LEG_ENTRIES if series == SERIES_ETP_EOD
              else _DELISTED_ENTRIES if series == SERIES_ETP_DELISTED
              else None)
    if target is None:
        raise PlaneConsumptionRefused(
            f"series {series!r} is outside the frozen target set")
    target[entry_name] = {"series": series, "sha256": sha256,
                          "raw_path": raw_path}


def all_frozen_entries() -> dict[str, dict[str, str]]:
    merged = dict(FROZEN_ENTRIES)
    merged.update(_LIVING_LEG_ENTRIES)
    merged.update(_DELISTED_ENTRIES)
    return merged


def raw_path_for(entry_name: str) -> str:
    return os.path.join(RAW_ROOT, all_frozen_entries()[entry_name]["raw_path"])


class PlaneConsumptionRefused(Exception):
    """Series/entry is not GRANTED (or outside the frozen set): refused."""


class PlaneDataBlocked(Exception):
    """Fail-closed data state: digest mismatch, corruption, malformed or
    missing store.  Never repaired, never retried here."""

    def __init__(self, message: str, reason: str = "BLOCKED_DATA"):
        super().__init__(message)
        self.reason = reason


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class VolNg1Authority(AuthorityRegistry):
    """AuthorityRegistry with the cycle's plan-frozen target set.

    Only ``register``'s target-set check is narrowed to the VOL-NG1
    trio; every state-machine rule is inherited unchanged.
    """

    def register(self, series_id: str, source: str, channel: str) -> None:
        if series_id not in FROZEN_TARGET_SET:
            raise NotInTargetSet(
                f"{series_id} is outside the VOL-NG1 frozen consumption "
                "set (plan section 3); additions need a plan amendment "
                "(defaults BLOCKED_DATA)")
        # bypass the platform's S1-S4 set, then run the SAME append+apply
        self._append_and_apply(
            {"event": "REGISTER", "series_id": series_id,
             "source": source, "channel": channel})

    def verdict(self, series_id: str) -> str:
        row = self._series.get(series_id)
        if row is None:
            return "BLOCKED_DATA: not in registry (VOL-NG1 frozen set)"
        if row["state"] == "GRANTED":
            return "GRANTED"
        return f"BLOCKED: {row.get('blocked_reason') or row['state']}"


class VolNg1Plane:
    """Read-only consume_via_plane adapter for the VOL-NG1 frozen set."""

    def __init__(self, store_root: str | None = None,
                 registry_journal: str | None = None,
                 raw_root: str | None = None):
        self.store_root = os.path.abspath(
            store_root or DEFAULT_STORE_ROOT)
        self.registry_journal = os.path.abspath(
            registry_journal or DEFAULT_AUTHORITY_JOURNAL)
        self.raw_root = os.path.abspath(raw_root or RAW_ROOT)
        # fail-closed existence checks BEFORE any object is built:
        # constructing CADS would create directories, and this adapter
        # must never create store state.
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
        self._registry = VolNg1Authority(self.registry_journal)
        self._store = CADS(self.store_root)
        try:
            self._pins = self._store.pins()
        except ControlStateDrift as exc:
            raise PlaneDataBlocked(
                f"CADS pins journal malformed: {exc}",
                "BLOCKED_STORE_MALFORMED") from exc

    # -- registry ------------------------------------------------------- #
    def verdict(self, series_id: str) -> str:
        return self._registry.verdict(series_id)

    # -- pin lookup ------------------------------------------------------ #
    def find_pin(self, series_id: str,
                 entry_name: str) -> dict | None:
        exact = [
            p for p in self._pins
            if p["metadata"].get("series") == series_id
            and (p["metadata"].get("file") or "") == entry_name
        ]
        if exact:
            return exact[-1]
        return None

    # -- resolve (verify-on-read + frozen digest) ------------------------ #
    def resolve_entry(self, series_id: str, entry_name: str,
                      expected_sha256: str | None = None) -> dict:
        verdict = self.verdict(series_id)
        if verdict != "GRANTED":
            raise PlaneConsumptionRefused(
                f"series {series_id} verdict={verdict!r}: consumption "
                "refused (fail-closed; only granted series may be "
                "consumed)")
        pin = self.find_pin(series_id, entry_name)
        if pin is None:
            raise PlaneDataBlocked(
                f"no CADS pin for series {series_id} entry {entry_name}",
                "BLOCKED_NO_PIN")
        address = pin["address"]
        expected = (expected_sha256
                    or all_frozen_entries().get(entry_name, {}).get("sha256"))
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
                f"digest mismatch for {entry_name}: resolved bytes hash "
                f"to {measured}, frozen digest is {expected} "
                "(BLOCKED_DATA: no re-download, no repair)", "BLOCKED_DATA")
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
        """Consume one entry of the frozen set by entry name."""
        entries = all_frozen_entries()
        if entry_name not in entries:
            raise PlaneConsumptionRefused(
                f"entry {entry_name!r} is outside the frozen VOL-NG1 "
                "consumption set (plan section 3): refused")
        meta = entries[entry_name]
        return self.resolve_entry(meta["series"], entry_name,
                                  meta["sha256"])

    # -- shadow parity (bounded pilot: plane vs raw committed bytes) ----- #
    def shadow_parity(self, entry_name: str, series: str | None = None,
                      expected_sha256: str | None = None) -> dict:
        """Plane-read digest vs a plain direct read of the committed raw
        snapshot bytes.  Production calls pass only ``entry_name``; the
        optional explicit form exists for sandboxed tests on throwaway
        stores."""
        if series is not None:
            res = self.resolve_entry(series, entry_name, expected_sha256)
        else:
            res = self.consume(entry_name)
        plane_sha = res["sha256_measured"]
        raw = os.path.join(
            self.raw_root,
            all_frozen_entries()[entry_name]["raw_path"])
        if not os.path.isfile(raw):
            raise PlaneDataBlocked(
                f"raw snapshot absent for direct read: {raw}",
                "BLOCKED_STORE_MALFORMED")
        h = hashlib.sha256()
        with open(raw, "rb") as fh:
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

    # -- manifest-verified query (frozen DuckDB surface, CBOE CSVs) ------ #
    def query_csv_bounds(self, entry_name: str, series: str | None = None,
                         expected_sha256: str | None = None) -> dict:
        """Bounds query over one CBOE official CSV through the
        manifest-verified query plane (bytes materialized to a temp file
        pinned by content hash, never touching the store)."""
        if series is not None:
            res = self.resolve_entry(series, entry_name, expected_sha256)
        else:
            res = self.consume(entry_name)
        tmpdir = tempfile.mkdtemp(prefix="vol_ng1_plane_")
        try:
            local = os.path.join(tmpdir, os.path.basename(entry_name))
            with open(local, "wb") as fh:
                fh.write(res["data"])
            mid = "vol_ng1_p0:" + os.path.basename(entry_name)
            entry = ManifestEntry(manifest_id=mid, path=local,
                                  sha256=res["cads_address"])
            plane = QueryPlane({mid: entry})
            try:
                plane.register_views({mid: "v_index"})
                frozen = FrozenQuery(
                    "vol_ng1_p0_index_bounds",
                    "SELECT count(*) AS n_rows, "
                    "min(COALESCE(TRY_CAST(\"DATE\" AS DATE), "
                    "TRY_CAST(strptime(CAST(\"DATE\" AS VARCHAR), "
                    "'%m/%d/%Y') AS DATE))) AS first_date, "
                    "max(COALESCE(TRY_CAST(\"DATE\" AS DATE), "
                    "TRY_CAST(strptime(CAST(\"DATE\" AS VARCHAR), "
                    "'%m/%d/%Y') AS DATE))) AS last_date "
                    "FROM v_index ORDER BY n_rows",
                    ["n_rows"],
                    [OutputColumn("n_rows", "BIGINT"),
                     OutputColumn("first_date", "DATE"),
                     OutputColumn("last_date", "DATE")],
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
