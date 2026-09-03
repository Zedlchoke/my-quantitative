"""Zero-cost data authority: snapshot pin revalidation and license evidence.

Owner: lane A3, STOCKS-FREE-V3 P1 (PLAN_stocks.md section 9 A3, deliverable 1
and section 4.1).

What this module does
---------------------
* Revalidates the EXISTING V2 staged snapshot (located outside this
  repository, in the V2 worktree staging directory) against the sha256 pins
  committed below.  The pins were transcribed from the V2 control artifact
  ``w1_freeze.json`` (``data_snapshot_hashes``, produced by V2 role A1 and
  sealed at ``2026-09-03T08:14:38Z``).  Hashes are metadata, not payloads:
  committing them copies no raw data into git.
* Revalidates the license/terms evidence by READING the V2 control artifacts
  (``da1_authority.json``, ``snapshot_manifest.json``).  No network request
  of any kind is performed, no terms page is re-fetched, and no credential is
  accessed or printed.  A control artifact that cannot be read is recorded as
  ``NOT_RUN`` — never an inferred PASS.

Verdict vocabulary is PASS / FAIL / NOT_RUN (fail-closed: missing evidence is
``NOT_RUN`` or ``UNAVAILABLE``, never an inferred PASS).

Revalidation may not expose S1 returns: this module hashes file BYTES and
reads control JSON metadata only.  It never parses bar payloads.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from research.assets.common.contracts import canonical_json, require_digest_hex

# --- frozen windows (PLAN_stocks.md section 4.1; w1_freeze.json s0_s1) ------- #
WARMUP_START = date(2018, 1, 2)
WARMUP_END = date(2018, 4, 3)
S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 31)
S1_START = date(2025, 8, 1)
S1_END = date(2026, 7, 31)
#: Observed common last session of the snapshot (V2 common_coverage.json).
COVERAGE_LAST = "2026-08-27"

# --- pinned corporate-action provenance (V2 split_factors.json control) ------ #
#: The five V2-pinned 2:1 sector-ETF splits, effective 2025-12-05 (a date
#: inside the sealed S1; the EVENTS are authorized corporate-action inputs,
#: not research data).  ``PINNED_CLOSE_RATIOS`` records the pre/post close
#: ratio per symbol as pinned by the A7-approved V2 control artifact.
SPLIT_EFFECTIVE_DATE = "2025-12-05"
SPLIT_FACTOR = 2.0
SPLIT_SYMBOLS = ("XLK", "XLE", "XLY", "XLU", "XLB")
#: The exact provenance dates a revalidation may read for split symbols —
#: the day before and the day of the split — and nothing else.
SPLIT_PROVENANCE_DATES = ("2025-12-04", "2025-12-05")
PINNED_CLOSE_RATIOS: Mapping[str, float] = {
    "XLK": 0.5037,
    "XLE": 0.4979,
    "XLY": 0.5028,
    "XLU": 0.4953,
    "XLB": 0.4984,
}

# --- frozen cohort ----------------------------------------------------------- #
#: The 11-ETF cohort; SPY is the broad benchmark, the other ten are the
#: sector ETFs.  XLC is pinned in the snapshot but remains EXCLUDED.
BENCHMARK_SYMBOL = "SPY"
COHORT_SYMBOLS = (
    "SPY",
    "XLK",
    "XLE",
    "XLF",
    "XLV",
    "XLI",
    "XLP",
    "XLY",
    "XLU",
    "XLB",
    "XLRE",
)
SECTOR_SYMBOLS = tuple(s for s in COHORT_SYMBOLS if s != BENCHMARK_SYMBOL)
EXCLUDED_SYMBOLS = ("XLC",)

# --- frozen digests (from V2 w1_freeze.json, A1-sealed) ---------------------- #
MANIFEST_PIN = "62ac324d7e683961b0d88f85153e4a072d09fe0a6745a54687b9e3b219d8f658"
#: Issuer distribution records: the State Street (SSGA) SPDR distributions
#: evidence file ``spdr-etf-historical-distributions.xlsx`` in the V2 staging.
ISSUER_DISTRIBUTION_RECORDS_SHA256 = (
    "1b952f87ca60ece4080b446d6c3b580f640d893ed33641797a2dd22dd61beca9"
)
COHORT_DIGEST = "c9d4e88a33c53448120e79138057bcb0d100abecc1d33fbec92bd3d9c541bc96"
PARTITION_DIGEST = "9b4ad7993f943edb1f4a995184eb85083879168f9f86eb1720b2a66623ef17c7"
#: Full digest behind the w1_freeze note "US_EQUITY_REGULAR_V1 (digest
#: 028a7b21...)": sha256 over the canonical frozen calendar table payload
#: (research.assets.stocks.calendar.USEquityRegularCalendar).
CALENDAR_DIGEST = "028a7b21c9e306c7399467309d18e3ed696181682ca01f1e3170c21bdceb69ab"

#: sha256 pins for every file of the V2 staged snapshot (transcribed from
#: w1_freeze.json ``data_snapshot_hashes``; 39 entries).  Files live in the
#: V2 worktree staging directory below and are NEVER copied into git.
SNAPSHOT_PINS: Mapping[str, str] = {
    "MANIFEST.json": MANIFEST_PIN,
    "SPY_all_p1.json": "881e6e53f92464af669b1fb232951716524b8bdee8592144fce40ed10d878c06",
    "SPY_none_p1.json": "2993ed37de077c6c05661686ed609b20b257f0d2d88b71ececa37bd1f976b436",
    "SPY_none_p2.json": "2993ed37de077c6c05661686ed609b20b257f0d2d88b71ececa37bd1f976b436",
    "XLB_all_p1.json": "ae447731ed38e3a9fcd6aef9d337cef25df8d10fb33353aa7b91812866bb987c",
    "XLB_none_p1.json": "a01de5e7fb1ac1179279651f2e8967ee56ed0a14b756d7b62d782e7e37fc3ac8",
    "XLB_none_p2.json": "a01de5e7fb1ac1179279651f2e8967ee56ed0a14b756d7b62d782e7e37fc3ac8",
    "XLC_all_p1.json": "9c91165ed0d76ed3b310e1e7460bbd5b8cfb31f1f02be8cea58efbdf2eda9424",
    "XLC_none_p1.json": "b6e70cf94e6773ec59219edff893c6188afd5d168dcaaf06ffb874e3a19eed78",
    "XLC_none_p2.json": "b6e70cf94e6773ec59219edff893c6188afd5d168dcaaf06ffb874e3a19eed78",
    "XLE_all_p1.json": "620ce59641b69fb4e1c1b42900516126a1ea14d5bd421c28c2fd5065bf15b9b1",
    "XLE_none_p1.json": "80c8239545a7d4495b77dd432332e197986d01f542db29a39e1f2978fb3ee0ef",
    "XLE_none_p2.json": "80c8239545a7d4495b77dd432332e197986d01f542db29a39e1f2978fb3ee0ef",
    "XLF_all_p1.json": "395cc219df66cf715b08723f6686031cf0c87b05d3042c53c7740625facc405d",
    "XLF_none_p1.json": "4d8f1eb08ff8bf1e5404a9c0b816d4308e2f721dfce2ec69cefc69323f09ed2f",
    "XLF_none_p2.json": "4d8f1eb08ff8bf1e5404a9c0b816d4308e2f721dfce2ec69cefc69323f09ed2f",
    "XLI_all_p1.json": "52e9dbfbc5ebcc28b032d99da28f0c42d91db27700136da1d60590f4a1afea1a",
    "XLI_none_p1.json": "eb5a5d0e5ff1a66702d2f8af0f83f873ad30da2701df50b2c2f19afbe17aac3e",
    "XLI_none_p2.json": "eb5a5d0e5ff1a66702d2f8af0f83f873ad30da2701df50b2c2f19afbe17aac3e",
    "XLK_all_p1.json": "3034671b326e3b136712b6cdb4f727ac082463f91f96188e814e4d94b0c1cbe1",
    "XLK_none_p1.json": "89ba7aaa57cc50755a514c873a6c6591d13ae373251a253443f53cab48725c5e",
    "XLK_none_p2.json": "89ba7aaa57cc50755a514c873a6c6591d13ae373251a253443f53cab48725c5e",
    "XLP_all_p1.json": "287563e212ffe4dd14f7130b1b6c79274bcc7a30a03272eea046ce7af40baa92",
    "XLP_none_p1.json": "8dede5c60f9fc4c5e268dff084361832574b3d73b6f8274044f89ad96db7e6c0",
    "XLP_none_p2.json": "8dede5c60f9fc4c5e268dff084361832574b3d73b6f8274044f89ad96db7e6c0",
    "XLRE_all_p1.json": "922a2f3dafc7ab43294ca0398613c20825df1eb9fd2867968d4c84b224c26050",
    "XLRE_none_p1.json": "f58c237253d8d35bc4408ecc06650051048389ab237398cff583139b6fb78d87",
    "XLRE_none_p2.json": "f58c237253d8d35bc4408ecc06650051048389ab237398cff583139b6fb78d87",
    "XLU_all_p1.json": "cdbd6101730b6907997ca96f681df575e98ed68e331fa6371da57c208d558bd0",
    "XLU_none_p1.json": "6470875cf84eb97432adf2aac422357afaedb6dd032aaaf2173ff37e3b52100c",
    "XLU_none_p2.json": "6470875cf84eb97432adf2aac422357afaedb6dd032aaaf2173ff37e3b52100c",
    "XLV_all_p1.json": "c3f2bb4d83db795cb3a83b7c3541a2524acabd4309e1fb6f195ac6d8d25c6534",
    "XLV_none_p1.json": "d3b9a9e5c800d5504f7ca37a9f891e35ef0f4caa79366f491dca2934f7dc2c71",
    "XLV_none_p2.json": "d3b9a9e5c800d5504f7ca37a9f891e35ef0f4caa79366f491dca2934f7dc2c71",
    "XLY_all_p1.json": "f32fe128cfdb9ec3e24cb76908e0248a5eff45de3a1ece7e7e770973e8e256f4",
    "XLY_none_p1.json": "0da3817e7643224b625d365e92626b40d5b922804b5b1278eee27642e6131f75",
    "XLY_none_p2.json": "0da3817e7643224b625d365e92626b40d5b922804b5b1278eee27642e6131f75",
    "common_coverage.json": "76ffd27c7c3defa89741788a18c1d241ddc254e87beedf0b53b3dcf9454ab92d",
    "fetch_log.json": "0fbd9dde2e19fc17f28e9888c28f87add3aedea57abe0f9809f6535e5746242c",
}

#: Absolute path of the V2 staging directory holding the snapshot (read-only
#: reference; the snapshot stays outside this worktree and outside git).
SNAPSHOT_STAGING_PATH = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/"
    "z8-exec-1/.staging"
)

#: Read-only V2 control directory (license/terms + freeze evidence).
V2_CONTROL_PATH = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/"
    "integration/research/control/stocks_free_v2_run"
)

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_NOT_RUN = "NOT_RUN"

PIN_VERIFIED = "VERIFIED"
PIN_MISMATCH = "MISMATCH"
PIN_UNAVAILABLE = "UNAVAILABLE"


def sha256_file(path: Path) -> str:
    """Chunked sha256 of a file (byte-level integrity only)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --- snapshot pin verification ------------------------------------------------ #


@dataclass(frozen=True)
class PinStatus:
    """Revalidation outcome for ONE pinned snapshot file."""

    name: str
    expected_sha256: str
    status: str  # VERIFIED / MISMATCH / UNAVAILABLE
    actual_sha256: str | None

    def __post_init__(self) -> None:
        require_digest_hex(self.expected_sha256, "expected_sha256")
        if self.status not in (PIN_VERIFIED, PIN_MISMATCH, PIN_UNAVAILABLE):
            raise ValueError(f"unknown pin status {self.status!r}")
        if self.status == PIN_UNAVAILABLE:
            if self.actual_sha256 is not None:
                raise ValueError("an unavailable pin must not carry an actual digest")
        else:
            require_digest_hex(self.actual_sha256 or "", "actual_sha256")

    def to_payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "expected_sha256": self.expected_sha256,
            "status": self.status,
            "actual_sha256": self.actual_sha256,
        }


@dataclass(frozen=True)
class SnapshotRevalidationReport:
    """Fail-closed report over the whole pinned snapshot."""

    root: str
    pins: tuple[PinStatus, ...]

    @property
    def verified(self) -> tuple[str, ...]:
        return tuple(p.name for p in self.pins if p.status == PIN_VERIFIED)

    @property
    def mismatched(self) -> tuple[str, ...]:
        return tuple(p.name for p in self.pins if p.status == PIN_MISMATCH)

    @property
    def unavailable(self) -> tuple[str, ...]:
        return tuple(p.name for p in self.pins if p.status == PIN_UNAVAILABLE)

    @property
    def verdict(self) -> str:
        if self.mismatched or self.unavailable:
            return VERDICT_FAIL
        return VERDICT_PASS

    def to_payload(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "verdict": self.verdict,
            "pin_count": len(self.pins),
            "verified_count": len(self.verified),
            "mismatched": list(self.mismatched),
            "unavailable": list(self.unavailable),
            "pins": [p.to_payload() for p in self.pins],
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_payload())


def verify_snapshot_pins(staging_root: str | Path) -> SnapshotRevalidationReport:
    """Hash-verify every pinned snapshot file under ``staging_root``.

    A file listed in :data:`SNAPSHOT_PINS` that is absent is recorded as
    ``UNAVAILABLE`` (fail-closed, never silently skipped); a present file
    whose sha256 differs from the pin is a ``MISMATCH``.  Only file BYTES are
    read — payloads are never parsed, so no S1 return can be exposed here.
    """
    root = Path(staging_root)
    statuses = []
    for name in sorted(SNAPSHOT_PINS):
        expected = SNAPSHOT_PINS[name]
        path = root / name
        if not path.is_file():
            statuses.append(
                PinStatus(
                    name=name,
                    expected_sha256=expected,
                    status=PIN_UNAVAILABLE,
                    actual_sha256=None,
                )
            )
            continue
        actual = sha256_file(path)
        statuses.append(
            PinStatus(
                name=name,
                expected_sha256=expected,
                status=PIN_VERIFIED if actual == expected else PIN_MISMATCH,
                actual_sha256=actual,
            )
        )
    return SnapshotRevalidationReport(root=str(root), pins=tuple(statuses))


# --- license/terms evidence revalidation (read-only, no network) ------------- #

_LICENSE_TERMS = {
    "provider": "Twelve Data",
    "plan": "Basic (free)",
    "cost_check_code": "1_basic_price_exactly_0",
    "noncommercial_check_code": "6_personal_internal_noncommercial_research_permitted",
    "no_redistribution_check_code": "8_no_redistribution_no_raw_in_git",
    "storage_check_code": "7_local_storage_snapshots_checksums_reproducibility",
}


@dataclass(frozen=True)
class AuthorityCheck:
    """One license/terms revalidation check."""

    name: str
    verdict: str
    detail: str

    def to_payload(self) -> dict[str, Any]:
        return {"name": self.name, "verdict": self.verdict, "detail": self.detail}


@dataclass(frozen=True)
class LicenseEvidenceReport:
    """Revalidation of the frozen zero-cost license/terms evidence."""

    control_dir: str
    artifact_digests: Mapping[str, str]
    checks: tuple[AuthorityCheck, ...]

    @property
    def verdict(self) -> str:
        verdicts = {check.verdict for check in self.checks}
        if VERDICT_FAIL in verdicts:
            return VERDICT_FAIL
        if VERDICT_NOT_RUN in verdicts:
            return VERDICT_NOT_RUN
        return VERDICT_PASS

    def to_payload(self) -> dict[str, Any]:
        return {
            "control_dir": self.control_dir,
            "verdict": self.verdict,
            "artifact_digests": dict(self.artifact_digests),
            "checks": [c.to_payload() for c in self.checks],
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_payload())


def revalidate_license_evidence(
    control_dir: str | Path = V2_CONTROL_PATH,
    staging_root: str | Path | None = None,
) -> LicenseEvidenceReport:
    """Revalidate FD0/FREE_DATA_AUTHORITY evidence by READING V2 artifacts.

    Reads ``da1_authority.json`` (the V2 DA1 ten-point authority review) and
    ``snapshot_manifest.json`` (storage/license note + issuer-evidence
    prefix) from the read-only V2 control directory.  Every claim below was
    frozen in V2 and is only RE-READ here, never re-fetched from the network
    and never re-derived from a live vendor call:

    * provider is Twelve Data, plan Basic (free), cost exactly USD 0;
    * use is personal/internal non-commercial research only;
    * redistribution is prohibited and raw data never enters git;
    * local persistent storage is bounded by the subscription terms (deletion
      within 30 days post-termination) — the recorded license-bound
      reproducibility window;
    * the issuer-evidence digest prefix pinned in the control manifest is a
      prefix of the digest committed in this module; when ``staging_root`` is
      given, the staging ``MANIFEST.json`` is byte-hash-verified against
      :data:`MANIFEST_PIN` BEFORE parsing, and its full issuer-evidence
      digest must equal the committed pin.

    A control artifact that cannot be read yields ``NOT_RUN`` for its checks
    (fail-closed), with the ``UNAVAILABLE`` reason in the detail.
    """
    control = Path(control_dir)
    digests: dict[str, str] = {}
    payloads: dict[str, dict[str, Any]] = {}
    for filename in ("da1_authority.json", "snapshot_manifest.json"):
        path = control / filename
        if not path.is_file():
            payloads[filename] = {}
            continue
        digests[filename] = sha256_file(path)
        try:
            payloads[filename] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payloads[filename] = {}

    checks: list[AuthorityCheck] = []
    da1 = payloads.get("da1_authority.json") or {}
    if not da1:
        checks.append(
            AuthorityCheck(
                name="da1_authority_present",
                verdict=VERDICT_NOT_RUN,
                detail=(
                    "UNAVAILABLE: V2 control artifact da1_authority.json could "
                    f"not be read from {control}; license evidence not revalidated"
                ),
            )
        )
    else:
        provider = str(da1.get("provider", ""))
        plan = str(da1.get("plan", ""))
        ten = da1.get("ten_point_checks") or {}
        checks.append(
            AuthorityCheck(
                name="provider_and_plan_frozen",
                verdict=VERDICT_PASS
                if provider == _LICENSE_TERMS["provider"] and plan == _LICENSE_TERMS["plan"]
                else VERDICT_FAIL,
                detail=f"provider={provider!r} plan={plan!r}",
            )
        )
        zero_cost = str(ten.get(_LICENSE_TERMS["cost_check_code"], ""))
        checks.append(
            AuthorityCheck(
                name="zero_cost_usd0",
                verdict=VERDICT_PASS if zero_cost.startswith("PASS") else VERDICT_FAIL,
                detail=zero_cost or "missing ten-point check",
            )
        )
        noncommercial = str(ten.get(_LICENSE_TERMS["noncommercial_check_code"], ""))
        checks.append(
            AuthorityCheck(
                name="internal_noncommercial_research_only",
                verdict=VERDICT_PASS if noncommercial.startswith("PASS") else VERDICT_FAIL,
                detail=noncommercial or "missing ten-point check",
            )
        )
        storage = str(ten.get(_LICENSE_TERMS["storage_check_code"], ""))
        checks.append(
            AuthorityCheck(
                name="local_storage_within_subscription",
                verdict=VERDICT_PASS if storage.startswith("PASS") else VERDICT_FAIL,
                detail=storage or "missing ten-point check",
            )
        )
        no_redist = str(ten.get(_LICENSE_TERMS["no_redistribution_check_code"], ""))
        checks.append(
            AuthorityCheck(
                name="no_redistribution_no_raw_in_git",
                verdict=VERDICT_PASS if no_redist.startswith("PASS") else VERDICT_FAIL,
                detail=no_redist or "missing ten-point check",
            )
        )

    manifest = payloads.get("snapshot_manifest.json") or {}
    if not manifest:
        checks.append(
            AuthorityCheck(
                name="snapshot_manifest_license_note",
                verdict=VERDICT_NOT_RUN,
                detail=(
                    "UNAVAILABLE: V2 control artifact snapshot_manifest.json "
                    f"could not be read from {control}"
                ),
            )
        )
    else:
        note = str(manifest.get("license_note", ""))
        ok_note = "redistribution forbidden" in note and "within subscription" in note
        checks.append(
            AuthorityCheck(
                name="license_note_revalidated",
                verdict=VERDICT_PASS if ok_note else VERDICT_FAIL,
                detail=(
                    note
                    + " (non-commercial use evidence is ten-point check 6)"
                    if ok_note
                    else note or "license_note missing"
                ),
            )
        )
        prefix = (manifest.get("issuer_evidence") or {}).get(
            "spdr_distributions_sha256_prefix"
        )
        checks.append(
            AuthorityCheck(
                name="issuer_distribution_records_prefix_match",
                verdict=VERDICT_PASS
                if prefix == ISSUER_DISTRIBUTION_RECORDS_SHA256[: len(str(prefix or ""))]
                and prefix
                else VERDICT_FAIL,
                detail=(
                    "control manifest issuer-evidence prefix "
                    f"{prefix!r} is a prefix of the committed pin"
                    if prefix and ISSUER_DISTRIBUTION_RECORDS_SHA256.startswith(str(prefix))
                    else f"issuer evidence prefix {prefix!r} inconsistent with the committed pin"
                ),
            )
        )

    if staging_root is not None:
        staging_manifest = Path(staging_root) / "MANIFEST.json"
        if not staging_manifest.is_file():
            checks.append(
                AuthorityCheck(
                    name="staging_manifest_issuer_digest",
                    verdict=VERDICT_NOT_RUN,
                    detail=(
                        "UNAVAILABLE: staging MANIFEST.json not found under "
                        f"{staging_root}"
                    ),
                )
            )
        else:
            staged_digest = sha256_file(staging_manifest)
            if staged_digest != MANIFEST_PIN:
                checks.append(
                    AuthorityCheck(
                        name="staging_manifest_issuer_digest",
                        verdict=VERDICT_FAIL,
                        detail=(
                            "staging MANIFEST.json sha256 does not match "
                            f"MANIFEST_PIN ({staged_digest} != {MANIFEST_PIN})"
                        ),
                    )
                )
            else:
                staged = json.loads(staging_manifest.read_text(encoding="utf-8"))
                full = (staged.get("issuer_evidence") or {}).get(
                    "spdr_distributions_sha256"
                )
                checks.append(
                    AuthorityCheck(
                        name="staging_manifest_issuer_digest",
                        verdict=VERDICT_PASS
                        if full == ISSUER_DISTRIBUTION_RECORDS_SHA256
                        else VERDICT_FAIL,
                        detail=(
                            "byte-verified staging MANIFEST.json carries the full "
                            "issuer-evidence digest matching the committed pin"
                            if full == ISSUER_DISTRIBUTION_RECORDS_SHA256
                            else f"staging issuer digest {full!r} != committed pin"
                        ),
                    )
                )

    return LicenseEvidenceReport(
        control_dir=str(control),
        artifact_digests=digests,
        checks=tuple(checks),
    )


__all__ = [
    "BENCHMARK_SYMBOL",
    "CALENDAR_DIGEST",
    "COHORT_DIGEST",
    "COHORT_SYMBOLS",
    "COVERAGE_LAST",
    "EXCLUDED_SYMBOLS",
    "ISSUER_DISTRIBUTION_RECORDS_SHA256",
    "MANIFEST_PIN",
    "PARTITION_DIGEST",
    "PINNED_CLOSE_RATIOS",
    "SPLIT_EFFECTIVE_DATE",
    "SPLIT_FACTOR",
    "SPLIT_PROVENANCE_DATES",
    "SPLIT_SYMBOLS",
    "PIN_MISMATCH",
    "PIN_UNAVAILABLE",
    "PIN_VERIFIED",
    "S0_END",
    "S0_START",
    "S1_END",
    "S1_START",
    "SECTOR_SYMBOLS",
    "SNAPSHOT_PINS",
    "SNAPSHOT_STAGING_PATH",
    "V2_CONTROL_PATH",
    "VERDICT_FAIL",
    "VERDICT_NOT_RUN",
    "VERDICT_PASS",
    "WARMUP_END",
    "WARMUP_START",
    "AuthorityCheck",
    "LicenseEvidenceReport",
    "PinStatus",
    "SnapshotRevalidationReport",
    "revalidate_license_evidence",
    "sha256_file",
    "verify_snapshot_pins",
]
