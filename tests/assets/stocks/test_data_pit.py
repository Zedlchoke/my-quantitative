"""Provider entitlement policy, parquet loader, checksums and PIT audit.

All datasets are SYNTHETIC and built under pytest ``tmp_path``; nothing in the
repository is written by a test run (proven by ``test_suite_writes_nothing``).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from research.assets.stocks.data_audit import (
    VERDICT_FAIL,
    VERDICT_NOT_RUN,
    VERDICT_PASS,
    run_pit_audit,
)
from research.assets.stocks.loader import (
    BarLoader,
    ChecksumError,
    GapError,
    LoaderError,
    MANIFEST_FILENAME,
    MissingPartitionError,
    SchemaError,
    partition_relpath,
    write_bars,
    write_checksum_manifest,
)
from research.assets.stocks.provider import (
    AUTHORITY,
    DIAGNOSTIC_ONLY,
    DiagnosticDataCannotSatisfyAuthorityError,
    ENTITLEMENT_VERIFIED,
    EntitlementError,
    EntitlementRecord,
    EntitlementRequirement,
    NO_ENTITLEMENT_FAIL_CLOSED,
    REQUIRED_LICENSE_SCOPE,
    SOURCE_FREE_CONVENIENCE,
    SOURCE_VENDOR_ENTITLED,
    UnentitledDiagnosticStub,
)
from research.assets.stocks.universe import (
    SecurityMaster,
    SecurityRecord,
    TickerRecord,
)

# --- synthetic session vocabulary (NOT the official calendar) ------------------ #
SYNTHETIC_HOLIDAYS = frozenset(
    {
        date(2020, 1, 1),
        date(2020, 7, 3),
        date(2020, 11, 26),
        date(2020, 12, 25),
        date(2021, 1, 1),
        date(2021, 7, 5),
        date(2021, 11, 25),
        date(2021, 12, 24),
    }
)


def synth_is_session_day(day: date) -> bool:
    """Injectable predicate standing in for the (other-lane) official calendar."""
    return day.weekday() < 5 and day not in SYNTHETIC_HOLIDAYS


def _session_days(first: date, last: date) -> list[date]:
    days = []
    cursor = first
    while cursor <= last:
        if synth_is_session_day(cursor):
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


# --- synthetic dataset ---------------------------------------------------------- #
COVERAGE = {
    # security_id: (first session, last session, ticker)
    "SEC_A": (date(2020, 1, 2), date(2021, 12, 31), "AAA"),
    "SEC_DEL": (date(2020, 1, 2), date(2020, 11, 25), "BBB"),  # delisted name
    "SEC_GAP": (date(2020, 1, 2), date(2021, 12, 31), "GGG"),
}
GAP_DAY = date(2021, 6, 18)  # a Friday regular session that goes missing
LATEST_COMPLETE = date(2021, 12, 31)


def build_master(include: tuple[str, ...] = ("SEC_A", "SEC_DEL", "SEC_GAP")) -> SecurityMaster:
    """Master matching the dataset include-list (audit and data must agree)."""
    return SecurityMaster(
        [
            SecurityRecord(
                security_id=security_id,
                primary_exchange="XNYS",
                listed_date=first,
                ticker_history=(
                    TickerRecord(ticker, first, last if security_id == "SEC_DEL" else None),
                ),
                delisted_date=last if security_id == "SEC_DEL" else None,
                last_valid_event=last if security_id == "SEC_DEL" else None,
            )
            for security_id, (first, last, ticker) in COVERAGE.items()
            if security_id in include
        ]
    )


CLEAN_INCLUDE = ("SEC_A", "SEC_DEL")


def make_frame(security_id: str, first: date, last: date, drop: tuple[date, ...] = ()) -> pd.DataFrame:
    rows = []
    for index, day in enumerate(_session_days(first, last)):
        if day in drop:
            continue
        exchange_ts = pd.Timestamp(day, tz="UTC") + pd.Timedelta(hours=21)
        rows.append(
            {
                "security_id": security_id,
                "ts_exchange": exchange_ts,
                "ts_ingest": exchange_ts + pd.Timedelta(days=2),
                "open": 10.0 + (index % 7),
                "high": 11.0 + (index % 7),
                "low": 9.5 + (index % 7),
                "close": 10.5 + (index % 7),
                "volume": 1_000.0 * (1 + index % 5),
                "year": day.year,
            }
        )
    return pd.DataFrame(rows)


def build_dataset(
    root: Path,
    *,
    include: tuple[str, ...] = ("SEC_A", "SEC_DEL", "SEC_GAP"),
    drops: dict[str, tuple[date, ...]] | None = None,
    truncations: dict[str, date] | None = None,
) -> Path:
    root = Path(root)
    drops = drops or {}
    truncations = truncations or {}
    for security_id in include:
        first, last, _ = COVERAGE[security_id]
        last = truncations.get(security_id, last)
        write_bars(
            root,
            security_id,
            make_frame(security_id, first, last, drop=drops.get(security_id, ())),
        )
    write_checksum_manifest(root)
    return root


@pytest.fixture()
def clean_root(tmp_path: Path) -> Path:
    # no gaps anywhere: SEC_GAP is excluded from the clean dataset
    return build_dataset(tmp_path / "dataset", include=("SEC_A", "SEC_DEL"))


@pytest.fixture()
def gap_root(tmp_path: Path) -> Path:
    return build_dataset(
        tmp_path / "dataset",
        drops={"SEC_GAP": (GAP_DAY,)},
    )


# --- provider entitlement policy -------------------------------------------------- #
class _VendorEntitledDouble:
    """Test double factory: an authority-capable vendor adapter (NOT a real
    provider implementation — it fetches nothing and exists only in tests)."""

    _SCHEMA_DOC = "synthetic-vendor:schema-v1:test-only"

    @classmethod
    def make(cls):
        import hashlib

        from research.assets.stocks.provider import ProviderAdapter

        digest = hashlib.sha256(cls._SCHEMA_DOC.encode("utf-8")).hexdigest()

        class _Adapter(ProviderAdapter):
            @property
            def provider_id(self):
                return "SYNTH_VENDOR_PIT"

            @property
            def provider_schema_digest(self):
                return digest

            @property
            def source_class(self):
                return SOURCE_VENDOR_ENTITLED

            def entitlement_requirement(self):
                return EntitlementRequirement(
                    provider_id=self.provider_id,
                    provider_schema_digest=self.provider_schema_digest,
                    source_class=SOURCE_VENDOR_ENTITLED,
                    required_credentials=("LICENSE_KEY",),
                    required_permissions=("EQUITY_PIT_HISTORY",),
                    verification_procedure="vendor authorization API query",
                    licensed_scope=("DELISTINGS",),
                    vendor_documentation=("vendor docs",),
                )

        return _Adapter()


class TestProviderEntitlementPolicy:
    def test_default_is_fail_closed(self):
        stub = UnentitledDiagnosticStub()
        assert NO_ENTITLEMENT_FAIL_CLOSED == "NO_ENTITLEMENT_FAIL_CLOSED"
        assert stub.entitlement_status == NO_ENTITLEMENT_FAIL_CLOSED
        assert stub.data_tier() == DIAGNOSTIC_ONLY

    def test_free_convenience_never_satisfies_authority(self):
        stub = UnentitledDiagnosticStub()
        assert stub.source_class == SOURCE_FREE_CONVENIENCE
        with pytest.raises(DiagnosticDataCannotSatisfyAuthorityError):
            stub.require_authority(purpose="score an S0 arm")
        # even a forged attached record cannot promote a free source
        record = EntitlementRecord(
            provider_id=stub.provider_id,
            provider_schema_digest=stub.provider_schema_digest,
            verified_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            evidence=("forged",),
            licensed_scope=REQUIRED_LICENSE_SCOPE,
        )
        with pytest.raises(EntitlementError):
            stub.attach_entitlement_record(record)
        object.__setattr__(stub, "_entitlement_record", record)  # bypass the guard
        with pytest.raises(DiagnosticDataCannotSatisfyAuthorityError):
            stub.require_authority(purpose="score an S0 arm")
        assert stub.data_tier() == DIAGNOSTIC_ONLY

    def test_requirement_records_what_a_real_check_needs(self):
        stub = UnentitledDiagnosticStub()
        requirement = stub.entitlement_requirement()
        assert isinstance(requirement, EntitlementRequirement)
        assert requirement.required_credentials
        assert requirement.required_permissions
        assert "entitlement" in requirement.verification_procedure.lower()
        assert requirement.vendor_documentation
        assert requirement.canonical_json()  # byte-stable evidence record
        # free convenience sources must never claim authority scope
        assert not (
            set(requirement.licensed_scope) & set(REQUIRED_LICENSE_SCOPE)
        )
        provenance = stub.provenance()
        assert provenance["provider_id"] == "UNENTITLED_DIAGNOSTIC_STUB"
        assert len(provenance["provider_schema_digest"]) == 64
        assert provenance["data_tier"] == DIAGNOSTIC_ONLY

    def test_verified_entitlement_unlocks_authority_on_capable_sources(self):
        adapter = _VendorEntitledDouble.make()
        assert adapter.entitlement_status == NO_ENTITLEMENT_FAIL_CLOSED
        with pytest.raises(EntitlementError, match=NO_ENTITLEMENT_FAIL_CLOSED):
            adapter.require_authority(purpose="score an S0 arm")
        record = EntitlementRecord(
            provider_id=adapter.provider_id,
            provider_schema_digest=adapter.provider_schema_digest,
            verified_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            evidence=("vendor-authorization-response-sha256",),
            licensed_scope=REQUIRED_LICENSE_SCOPE,
        )
        adapter.attach_entitlement_record(record)
        assert adapter.entitlement_status == ENTITLEMENT_VERIFIED
        assert adapter.data_tier() == AUTHORITY
        adapter.require_authority(purpose="score an S0 arm")  # must not raise

    def test_record_identity_mismatch_fails_closed(self):
        adapter = _VendorEntitledDouble.make()
        mismatched = EntitlementRecord(
            provider_id="OTHER_PROVIDER",
            provider_schema_digest=adapter.provider_schema_digest,
            verified_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            evidence=("evidence",),
            licensed_scope=REQUIRED_LICENSE_SCOPE,
        )
        with pytest.raises(EntitlementError, match="provider"):
            adapter.attach_entitlement_record(mismatched)

    def test_partial_scope_entitlement_rejected(self):
        with pytest.raises(ValueError, match="required license scope"):
            EntitlementRecord(
                provider_id="P",
                provider_schema_digest="a" * 64,
                verified_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                evidence=("evidence",),
                licensed_scope=("PIT_SECURITY_MASTER",),  # missing the rest
            )


# --- loader --------------------------------------------------------------------- #
class TestLoader:
    def test_happy_path_returns_pit_columns(self, clean_root: Path):
        loader = BarLoader(clean_root, gap_tolerance_days=0,
                           session_predicate=synth_is_session_day)
        frame = loader.load("SEC_A", date(2020, 1, 2), LATEST_COMPLETE)
        assert {"ts_exchange", "ts_ingest"} <= set(frame.columns)
        assert frame["ts_exchange"].dt.tz is not None
        assert frame["ts_ingest"].dt.tz is not None
        assert (frame["ts_ingest"] >= frame["ts_exchange"]).all()
        dates = frame["ts_exchange"].dt.date
        assert dates.min() == COVERAGE["SEC_A"][0]
        assert dates.max() == LATEST_COMPLETE
        expected = len(_session_days(COVERAGE["SEC_A"][0], LATEST_COMPLETE))
        assert len(frame) == expected

    def test_missing_partition_fails_closed(self, clean_root: Path):
        (clean_root / partition_relpath("SEC_A", 2021)).unlink()
        loader = BarLoader(clean_root, gap_tolerance_days=4)
        with pytest.raises(MissingPartitionError, match="bars_2021"):
            loader.load("SEC_A", date(2020, 1, 2), LATEST_COMPLETE)

    def test_tampered_partition_fails_checksum(self, clean_root: Path):
        target = clean_root / partition_relpath("SEC_A", 2020)
        target.write_bytes(target.read_bytes() + b"\x00")
        loader = BarLoader(clean_root, gap_tolerance_days=4)
        with pytest.raises(ChecksumError, match="checksum mismatch"):
            loader.load("SEC_A", date(2020, 1, 2), LATEST_COMPLETE)

    def test_unmanifested_partition_fails_closed(self, clean_root: Path):
        manifest_path = clean_root / MANIFEST_FILENAME
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        del payload["files"][partition_relpath("SEC_A", 2020)]
        manifest_path.write_text(json.dumps(payload), encoding="utf-8")
        loader = BarLoader(clean_root, gap_tolerance_days=4)
        with pytest.raises(ChecksumError, match="not in the manifest"):
            loader.load("SEC_A", date(2020, 1, 2), LATEST_COMPLETE)

    def test_gap_beyond_declared_tolerance_fails_closed(self, gap_root: Path):
        loader = BarLoader(
            gap_root, gap_tolerance_days=0, session_predicate=synth_is_session_day
        )
        with pytest.raises(GapError, match=GAP_DAY.isoformat()):
            loader.load("SEC_GAP", date(2020, 1, 2), LATEST_COMPLETE)

    def test_declared_tolerance_absorbs_small_gap(self, gap_root: Path):
        loader = BarLoader(
            gap_root, gap_tolerance_days=1, session_predicate=synth_is_session_day
        )
        frame = loader.load("SEC_GAP", date(2020, 1, 2), LATEST_COMPLETE)
        assert GAP_DAY not in set(frame["ts_exchange"].dt.date)

    def test_predicate_scopes_gap_accounting_to_sessions(self, gap_root: Path):
        # GAP_DAY (Friday) sits next to a weekend: without a session predicate
        # the Saturday/Sunday calendar days count against the tolerance too,
        # so the same declared tolerance=1 passes WITH the predicate (test
        # above) but fails WITHOUT it.
        loader = BarLoader(gap_root, gap_tolerance_days=1)
        with pytest.raises(GapError):
            loader.load("SEC_GAP", date(2021, 6, 1), date(2021, 6, 30))

    def test_weekends_and_holidays_are_not_gaps(self, clean_root: Path):
        loader = BarLoader(
            clean_root, gap_tolerance_days=0, session_predicate=synth_is_session_day
        )
        frame = loader.load("SEC_A", date(2020, 3, 1), date(2020, 3, 31))
        assert len(frame) == len(
            _session_days(date(2020, 3, 1), date(2020, 3, 31))
        )

    def test_empty_window_fails_closed(self, clean_root: Path):
        # a weekend-only window inside an existing partition: partitions are
        # all present, so this reaches the empty-window guard, not the
        # missing-partition guard.
        loader = BarLoader(clean_root, gap_tolerance_days=4)
        with pytest.raises(LoaderError, match="no observations"):
            loader.load("SEC_A", date(2020, 3, 7), date(2020, 3, 8))

    def test_missing_root_fails_closed(self, tmp_path: Path):
        with pytest.raises(LoaderError, match="does not exist"):
            BarLoader(tmp_path / "absent", gap_tolerance_days=0)

    def test_gap_tolerance_must_be_declared(self, clean_root: Path):
        with pytest.raises(TypeError):
            BarLoader(clean_root)  # type: ignore[call-arg]
        with pytest.raises(ValueError, match="declared"):
            BarLoader(clean_root, gap_tolerance_days=-1)

    def test_duplicate_exchange_timestamps_fail_closed(self, tmp_path: Path):
        root = tmp_path / "dup"
        frame = make_frame("SEC_A", date(2020, 1, 2), date(2020, 1, 31))
        frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
        write_bars(root, "SEC_A", frame)
        write_checksum_manifest(root)
        loader = BarLoader(root, gap_tolerance_days=0,
                           session_predicate=synth_is_session_day)
        with pytest.raises(SchemaError, match="duplicate exchange timestamps"):
            loader.load("SEC_A", date(2020, 1, 2), date(2020, 1, 31))
        # event streams may opt out explicitly
        frame2 = loader.load(
            "SEC_A", date(2020, 1, 2), date(2020, 1, 31),
            allow_duplicate_timestamps=True,
        )
        assert len(frame2) == len(frame)

    def test_ingest_before_exchange_fails_closed(self, tmp_path: Path):
        root = tmp_path / "late"
        frame = make_frame("SEC_A", date(2020, 1, 2), date(2020, 1, 31))
        frame.loc[frame.index[3], "ts_ingest"] = (
            frame.loc[frame.index[3], "ts_exchange"] - pd.Timedelta(days=1)
        )
        write_bars(root, "SEC_A", frame)
        write_checksum_manifest(root)
        loader = BarLoader(root, gap_tolerance_days=0,
                           session_predicate=synth_is_session_day)
        with pytest.raises(SchemaError, match="ts_ingest before ts_exchange"):
            loader.load("SEC_A", date(2020, 1, 2), date(2020, 1, 31))

    def test_delisted_name_loads_through_final_event(self, clean_root: Path):
        loader = BarLoader(
            clean_root, gap_tolerance_days=0, session_predicate=synth_is_session_day
        )
        first, last, _ = COVERAGE["SEC_DEL"]
        frame = loader.load("SEC_DEL", first, last)
        assert frame["ts_exchange"].dt.date.max() == last


# --- PIT audit --------------------------------------------------------------------- #
class TestPitAudit:
    def test_clean_dataset_passes_with_injected_predicate(self, clean_root: Path):
        report = run_pit_audit(
            root=clean_root,
            master=build_master(CLEAN_INCLUDE),
            latest_complete_date=LATEST_COMPLETE,
            session_predicate=synth_is_session_day,
        )
        assert report.verdict == VERDICT_PASS
        for check in report.checks:
            assert check.verdict == VERDICT_PASS, check

    def test_unexplained_regular_session_gap_fails(self, gap_root: Path):
        report = run_pit_audit(
            root=gap_root,
            master=build_master(("SEC_A", "SEC_DEL", "SEC_GAP")),
            latest_complete_date=LATEST_COMPLETE,
            session_predicate=synth_is_session_day,
        )
        assert report.verdict == VERDICT_FAIL
        gap_check = report.check("regular_session_gaps_explained")
        assert gap_check.verdict == VERDICT_FAIL
        assert GAP_DAY.isoformat() in gap_check.detail
        # the other checks are unaffected
        assert report.check("checksum_and_partitions").verdict == VERDICT_PASS
        assert report.check("delisting_retention").verdict == VERDICT_PASS

    def test_calendar_explained_holiday_is_not_a_gap(self, clean_root: Path):
        # 2020-07-03 is in the synthetic holiday set: no bar, but explained.
        report = run_pit_audit(
            root=clean_root,
            master=build_master(CLEAN_INCLUDE),
            latest_complete_date=LATEST_COMPLETE,
            session_predicate=synth_is_session_day,
        )
        assert report.check("regular_session_gaps_explained").verdict == VERDICT_PASS

    def test_gap_check_not_run_without_injected_predicate(self, clean_root: Path):
        report = run_pit_audit(
            root=clean_root,
            master=build_master(CLEAN_INCLUDE),
            latest_complete_date=LATEST_COMPLETE,
            session_predicate=None,
        )
        gap_check = report.check("regular_session_gaps_explained")
        assert gap_check.verdict == VERDICT_NOT_RUN
        assert "calendar" in gap_check.detail
        assert report.verdict == VERDICT_NOT_RUN

    def test_truncated_delisted_name_fails_retention(self, tmp_path: Path):
        root = build_dataset(
            tmp_path / "dataset",
            include=("SEC_A", "SEC_DEL"),
            truncations={"SEC_DEL": date(2020, 11, 10)},  # 11 days early
        )
        report = run_pit_audit(
            root=root,
            master=build_master(CLEAN_INCLUDE),
            latest_complete_date=LATEST_COMPLETE,
            session_predicate=synth_is_session_day,
        )
        retention = report.check("delisting_retention")
        assert retention.verdict == VERDICT_FAIL
        assert "final valid event" in retention.detail
        assert report.verdict == VERDICT_FAIL

    def test_checksum_failure_fails_audit(self, clean_root: Path):
        target = clean_root / partition_relpath("SEC_DEL", 2020)
        target.write_bytes(target.read_bytes() + b"\x00")
        report = run_pit_audit(
            root=clean_root,
            master=build_master(CLEAN_INCLUDE),
            latest_complete_date=LATEST_COMPLETE,
            session_predicate=synth_is_session_day,
        )
        assert report.check("checksum_and_partitions").verdict == VERDICT_FAIL
        assert report.verdict == VERDICT_FAIL

    def test_gate_evidence_payload(self, clean_root: Path):
        report = run_pit_audit(
            root=clean_root,
            master=build_master(CLEAN_INCLUDE),
            latest_complete_date=LATEST_COMPLETE,
            session_predicate=synth_is_session_day,
        )
        evidence = report.gate_evidence("SD0_DATA_PIT_PASS")
        assert evidence["gate"] == "SD0_DATA_PIT_PASS"
        assert evidence["verdict"] == VERDICT_PASS
        json.dumps(evidence)  # must be JSON-serializable for the gate writer
        assert report.canonical_json()


# --- the suite writes nothing into the repository ---------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[3]

_MODULES = (
    "research.assets.stocks",
    "research.assets.stocks.provider",
    "research.assets.stocks.universe",
    "research.assets.stocks.loader",
    "research.assets.stocks.data_audit",
)


def _git_status() -> str:
    out = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout


def test_suite_writes_nothing_to_the_repository(tmp_path: Path):
    before = _git_status()
    probe = "import importlib\n"
    probe += "".join(f"importlib.import_module({name!r})\n" for name in _MODULES)
    probe += "print('imported-ok')\n"
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "imported-ok" in completed.stdout
    # a full synthetic audit run inside tmp must also leave the tree untouched
    dataset = build_dataset(tmp_path / "ds", include=CLEAN_INCLUDE)
    report = run_pit_audit(
        root=dataset,
        master=build_master(CLEAN_INCLUDE),
        latest_complete_date=LATEST_COMPLETE,
        session_predicate=synth_is_session_day,
    )
    assert report.verdict == VERDICT_PASS
    assert _git_status() == before
