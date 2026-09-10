#!/usr/bin/env python
"""V9 / A2 -- cohort-10 crypto universe + data audit (re-pinned under V9).

ENGINE / ENVIRONMENT SPLIT (MDP-V2R1 A3 remediation, plan D2)
-------------------------------------------------------------
This module is split into two halves so the audit no longer crashes when the
host data paths are absent (the original failure: the module fixture called
``main()`` against the REAL catalog/funding roots; after the owner cleaned
them, ``funding_raw`` came back empty, per-symbol funding audits became
``None`` and the gate assembly crashed with
``TypeError: 'NoneType' object is not a mapping``).

  * ``load_inputs(descriptor)`` -- ALL environment resolution: catalog root,
    funding root, pinned selection manifest (+ sha256 verification of manifest
    and selector script), per-symbol bar file lists, funding rows, instrument
    metadata, PIT metadata block.  Returns a typed ``InputsBundle``; a missing
    catalog/funding root yields the typed ``InputsUnavailable`` result (with
    the missing paths) instead of a crash.
  * ``run_audit_from_bundle(bundle, frozen_config=None)`` -- PURE computation
    from the bundle: returns ``{"manifest", "audit", "gate"}``.  Window
    constants (PRE/SCORED start/end seconds), FIRST_POSSIBLE_EXPOSURE,
    LISTING_AGE_MIN_DAYS, the generated_at stamp, the catalog/funding LABEL
    strings that go into the artifacts and the pinned manifest all come from
    the bundle/config (``FrozenConfig`` defaults equal today's module
    constants, so the REAL path output stays byte-identical in structure).
  * ``run_real_historical_audit(descriptor, out_dir)`` -- availability-aware
    wrapper: absent data produces an availability artifact (expected inputs +
    paths, availability census, invocation provenance, exact blocker, offline
    assertion, read-only hashes of any existing legacy states) with verdict
    ``NOT_RUN_DATA_UNAVAILABLE``; present data runs the real audit and
    byte-compares against the committed historical artifacts (PASS/FAIL).

Funding absence is TYPED and truthful: a selected symbol with no funding rows
gets a funding audit block with ``funding_data_present: false`` and
``complete: false`` (gate check tag ``FAIL_FUNDING_COVERAGE``) -- never a
TypeError, never fabricated completeness.

The audit still does NOT invent a new selection rule. It REUSES the corrected
V8 A8 deterministic selector (``scripts/v8x_crypto_universe_selection.py``,
committed byte-identical copy of the V8 worktree artifact, sha-pinned)
verbatim: exact 15-minute grid census, pre-window median daily quote-volume
metric, held-exposure funding completeness proof, instrument sanity and
listing-age >= 365d gates.  Performance-blind, fully offline and byte-
deterministic (fixed generated_at).
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import platform
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.v8x_crypto_universe_selection import (  # noqa: E402  (path shim above)
    BAR_INTERVAL_S,
    BAR_SUFFIX,
    BTC_SYMBOL,
    CATALOG_ROOT,
    FIRST_POSSIBLE_EXPOSURE,
    FUNDING_ROOT,
    LISTING_AGE_MIN_DAYS,
    PRE_END_S,
    PRE_START_S,
    QUOTE_REQUIRED,
    SCORED_END_S,
    SCORED_START_S,
    TOP_N,
    VENUE,
    analyze_funding,
    build_corroboration,
    census_for_symbol,
    dt_to_s,
    median_daily_quote_volume_pre_window,
    sha256_file,
    slot_opens_from_ts_event,
    utc_str,
)

import numpy as np  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

# --------------------------------------------------------------------------- #
# Frozen constants (V9 ownership pin; do NOT edit without a new prereg)
# --------------------------------------------------------------------------- #
SCHEMA_VERSION = "1.0.0"
AGENT = "A2-v9-universe"
GENERATED_AT_UTC = "2026-08-26T00:00:00Z"  # frozen for byte-reproducibility
AUDIT_LABEL = "S0_ALREADY_INSPECTED"

SOURCE_MANIFEST_RELPATH = Path("data/v8x_manifests/crypto_universe_selection.json")
SOURCE_SELECTOR_RELPATH = Path("scripts/v8x_crypto_universe_selection.py")
SOURCE_CANONICAL_V8_MANIFEST_PATH = (
    "/Users/hoangminhlong/my-quantitative-v8-wt/a8-crypto-breadth/data/"
    "v8x_manifests/crypto_universe_selection.json"
)
SOURCE_CANONICAL_V8_SELECTOR_PATH = (
    "/Users/hoangminhlong/my-quantitative-v8-wt/a8-crypto-breadth/scripts/"
    "v8x_crypto_universe_selection.py"
)
PINNED_SOURCE_MANIFEST_SHA256 = (
    "e73c703f5fb4dea7ff0c6c2c6c8c756b12218fa1960bf46c0ebb2509abb56376"
)
PINNED_SOURCE_SELECTOR_SHA256 = (
    "709b40c229d733aa08df867a3e207da46d5c86a111c54c0d502d2b809beda406"
)

DEFAULT_MANIFEST_OUT = REPO_ROOT / "data" / "v9_manifests" / "universe_selection_v9.json"
DEFAULT_AUDIT_OUT = REPO_ROOT / "research" / "audits" / "v9p" / "data_audit_v9.json"
DEFAULT_GATE_OUT = REPO_ROOT / "research" / "audits" / "v9p" / "t02_gate_v9.json"
DEFAULT_TIER_R_OUT = REPO_ROOT / "research" / "audits" / "v9_tier_r"

ARTIFACT_RELPATHS = (
    "data/v9_manifests/universe_selection_v9.json",
    "research/audits/v9p/data_audit_v9.json",
    "research/audits/v9p/t02_gate_v9.json",
)

GATE_ID = "P03/P04"

DOCUMENTED_CAPTURE_BOUNDARY_CLASSES = frozenset(
    {
        "local_capture_boundary_between_sessions",
        "local_capture_starts_after_window_start",
        "local_capture_ends_before_window_end",
    }
)

FUNDING_ASSUMPTION_TEXT = (
    "weekly Monday rebalance schedule; conservative first-possible-exposure "
    "= pre-window end = scored-window start 2025-08-21T00:00Z; funding "
    "settlement completeness required across any possible held-exposure time "
    "from that instant through the scored-window end inclusive"
)

PIT_METADATA_LIMITATION_TEXT = (
    "catalog stores ONE instrument-definition snapshot per symbol (single "
    "write timestamp in the filename); there is NO effective-dated "
    "versioning, so PIT changes to tickSize/stepSize/minNotional during the "
    "scored window cannot be attested from this store -- presence and values "
    "at snapshot time are attested here"
)

NOT_SELECTED_NOTE = (
    "see source_selection_artifact.verdict + pinned manifest "
    "not_selected_eligible (AVAXUSDT AAVEUSDT BCHUSDT NEARUSDT WLDUSDT "
    "BOMEUSDT ZECUSDT ACEUSDT ONGUSDT)"
)

SCORED_MEASURED_REQUIRED_BASIS_TMPL = (
    "MEASURED intersection of completed 15m bar coverage across the "
    "10 selected altcoins inside the contract scored window "
    "[{win_start}, {win_end}); endpoints are completed-bar CLOSE stamps; "
    "never trimmed to dodge gaps"
)
SCORED_MEASURED_ALL_BASIS = "same measurement including BTCUSDT as benchmark context"

# Committed synthetic fixture (repo-authored; schema-shaped after the pinned
# V8 manifest so the same engine consumes both).  See
# tests/fixtures/v9_universe_audit/build_fixture.py for the deterministic
# builder and the hand-computation documentation.
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "v9_universe_audit"
FIXTURE_CATALOG_RELPATH = "tests/fixtures/v9_universe_audit/catalog_root"
FIXTURE_FUNDING_RELPATH = "tests/fixtures/v9_universe_audit/funding"
FIXTURE_PINNED_MANIFEST_RELPATH = (
    "tests/fixtures/v9_universe_audit/pinned_selection_manifest.json"
)
FIXTURE_PINNED_MANIFEST_SHA256 = (
    "0c27f128a28671699cc1cc1a1dd13a02a6ec8ac6c45dcb008cba576e148cdb82"
)
FIXTURE_AGENT = "fx-v9audit-fixture"


class PinVerificationError(RuntimeError):
    """Raised when a pinned input artifact fails its sha256 verification."""


class AuditInputsUnavailable(RuntimeError):
    """Raised when the REAL audit path is asked to run without its inputs."""

    def __init__(self, unavailable: "InputsUnavailable") -> None:
        self.unavailable = unavailable
        blockers = "; ".join(
            f"{m['name']} not found at {m['path']}" for m in unavailable.missing
        )
        super().__init__(f"V9 audit inputs unavailable: {blockers}")


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_obj(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


# --------------------------------------------------------------------------- #
# Pinned-input loading + verification
# --------------------------------------------------------------------------- #
def load_pinned_selection(
    repo_root: Path = REPO_ROOT,
    pinned_manifest_sha256: str = PINNED_SOURCE_MANIFEST_SHA256,
    pinned_selector_sha256: str = PINNED_SOURCE_SELECTOR_SHA256,
    manifest_path: Path | None = None,
    selector_path: Path | None = None,
    manifest_label: str | None = None,
    selector_label: str | None = None,
    canonical_v8_manifest_path: str = SOURCE_CANONICAL_V8_MANIFEST_PATH,
    canonical_v8_selector_path: str = SOURCE_CANONICAL_V8_SELECTOR_PATH,
) -> tuple[dict, dict]:
    """Load + verify a frozen V8-shaped selection manifest and its selector.

    Defaults resolve the REAL tracked repo copies (data/v8x_manifests/... and
    scripts/v8x_crypto_universe_selection.py) against the pinned sha256
    values.  Bundle paths may override the files (synthetic fixture); labels
    only affect the provenance strings carried in the artifacts.
    """
    m_path = Path(manifest_path) if manifest_path is not None \
        else Path(repo_root) / SOURCE_MANIFEST_RELPATH
    s_path = Path(selector_path) if selector_path is not None \
        else Path(repo_root) / SOURCE_SELECTOR_RELPATH
    m_label = manifest_label if manifest_label is not None \
        else str(SOURCE_MANIFEST_RELPATH)
    s_label = selector_label if selector_label is not None \
        else str(SOURCE_SELECTOR_RELPATH)
    digest = sha256_file(m_path)
    if digest != pinned_manifest_sha256:
        raise PinVerificationError(
            f"pinned V8 selection manifest sha mismatch: {m_path} "
            f"sha256={digest} expected={pinned_manifest_sha256}"
        )
    sel_digest = sha256_file(s_path)
    if sel_digest != pinned_selector_sha256:
        raise PinVerificationError(
            f"pinned V8 selector script sha mismatch: {s_path} "
            f"sha256={sel_digest} expected={pinned_selector_sha256}"
        )
    return json.loads(m_path.read_text(encoding="utf-8")), {
        "path": m_label,
        "canonical_v8_path": canonical_v8_manifest_path,
        "sha256": digest,
        "schema_version": None,  # filled by caller from parsed content
        "selector_script": {
            "path": s_label,
            "canonical_v8_path": canonical_v8_selector_path,
            "sha256": sel_digest,
        },
    }


# --------------------------------------------------------------------------- #
# Current-bytes revalidation helpers (pure / environment-explicit)
# --------------------------------------------------------------------------- #
def bar_files_for_symbol(catalog_root: str | Path, symbol: str) -> list[str]:
    return sorted(
        glob.glob(
            os.path.join(str(catalog_root), "data", "binance_bar",
                         f"{symbol}-PERP.{VENUE}{BAR_SUFFIX}", "*.parquet")
        )
    )


def load_instrument_from(catalog_root: str | Path, symbol: str) -> dict | None:
    """Local mirror of v8x.load_instrument for a BUNDLE-supplied catalog root
    (the pinned v8x function reads its CATALOG_ROOT global and must not be
    modified)."""
    pat = os.path.join(str(catalog_root), "data", "crypto_perpetual",
                       f"{symbol}-PERP.{VENUE}", "*.parquet")
    files = sorted(glob.glob(pat))
    if not files:
        return None
    row = pq.read_table(files[0]).to_pandas().iloc[0]
    info = json.loads(bytes(row["info"]))
    return {
        "instrument_id": str(row["id"]),
        "quote_currency": str(info.get("quoteAsset", "")),
        "contract_type": str(info.get("contractType", "")),
        "status": str(info.get("status", "")),
        "onboard_date_utc": datetime.fromtimestamp(
            int(info["onboardDate"]) / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if info.get("onboardDate") else None,
        "onboard_ms": int(info["onboardDate"]) if info.get("onboardDate") else None,
    }


def observed_slot_opens(files) -> np.ndarray:
    """Union of unique 15m slot-open epoch seconds across files (rule reuse)."""
    opens = []
    for f in sorted(files):
        t = pq.read_table(f, columns=["ts_event"])["ts_event"].to_numpy()
        o = slot_opens_from_ts_event(np.asarray(t, dtype=np.int64))
        if o.size:
            opens.append(o)
    return np.unique(np.concatenate(opens)) if opens else np.empty(0, np.int64)


def duplicate_raw_stamps(files) -> int:
    """Exact-duplicate ts_event (ns) count across files."""
    seen: set[int] = set()
    dupes = 0
    for f in sorted(files):
        t = pq.read_table(f, columns=["ts_event"])["ts_event"].to_numpy()
        for ns in np.asarray(t, dtype=np.int64):
            v = int(ns)
            if v in seen:
                dupes += 1
            seen.add(v)
    return dupes


def measured_coverage(files, win_a: int, win_b: int) -> tuple[int, int] | None:
    """First/last completed-bar slot OPEN inside [win_a, win_b), or None."""
    opens = observed_slot_opens(files)
    in_win = opens[(opens >= win_a) & (opens < win_b)]
    if in_win.size == 0:
        return None
    return int(in_win[0]), int(in_win[-1])


def intersection_range(ranges: dict[str, tuple[int, int]]) -> tuple[int | None, int | None]:
    """Measured common window = max(first) .. min(last) (no trimming tricks)."""
    starts = [s for s, _ in ranges.values()]
    ends = [e for _, e in ranges.values()]
    if not starts or not ends:
        return None, None
    return max(starts), min(ends)


def close_stamp_iso(open_s: int, bar_interval_s: int = BAR_INTERVAL_S) -> str:
    """ISO UTC of the completed-bar CLOSE stamp of the slot opening open_s."""
    return utc_str(open_s + bar_interval_s)


def listing_age_check(inst, first_exposure_s: int,
                      min_days: int = LISTING_AGE_MIN_DAYS) -> dict:
    cutoff_ms = (dt_to_s(datetime.fromtimestamp(first_exposure_s, tz=timezone.utc)
                          - timedelta(days=min_days))) * 1000
    onboard_ms = inst["onboard_ms"] if inst else None
    age_days = ((first_exposure_s * 1000 - onboard_ms) / 86400000.0
                if onboard_ms else None)
    ok = bool(onboard_ms is not None and onboard_ms <= cutoff_ms)
    return {
        "onboard_date_utc": inst["onboard_date_utc"] if inst else None,
        "min_days": min_days,
        "cutoff_utc": utc_str(int(cutoff_ms // 1000)),
        "age_days_at_first_possible_exposure": round(age_days, 2) if age_days is not None else None,
        "ok": ok,
    }


def pit_metadata_via_catalog(catalog_root: str | Path, symbols: list[str]) -> dict:
    """tick/step/min-notional presence via data.catalog.Catalog instruments."""
    from data.catalog import Catalog

    cat = Catalog(str(catalog_root))
    out: dict[str, dict] = {}
    for sym in symbols:
        try:
            inst = cat.instrument(f"{sym}-PERP.BINANCE")
        except Exception as exc:  # noqa: BLE001 - record, never crash the audit
            out[sym] = {"present": False, "error": f"{type(exc).__name__}: {exc}"}
            continue
        if inst is None:
            out[sym] = {"present": False}
            continue
        min_not = getattr(inst, "min_notional", None)
        out[sym] = {
            "present": True,
            "instrument_id": str(inst.id),
            "tick_size": float(inst.price_increment.as_decimal()),
            "step_size": float(inst.size_increment.as_decimal()),
            "min_notional": str(min_not) if min_not else None,
        }
    all_ok = all(
        m.get("present")
        and isinstance(m.get("tick_size"), float) and m["tick_size"] > 0
        and isinstance(m.get("step_size"), float) and m["step_size"] > 0
        and m.get("min_notional")
        for m in out.values()
    )
    return {
        "method": "data.catalog.Catalog().instrument(<SYM>-PERP.BINANCE)",
        "limitation": PIT_METADATA_LIMITATION_TEXT,
        "per_symbol": out,
        "all_ten_present_with_tick_step_min_notional": bool(all_ok),
    }


def pit_metadata_via_instrument_parquet(catalog_root: str | Path, symbols: list[str],
                                        limitation_text: str) -> dict:
    """Bundle-path PIT provider: reads the same instrument parquets the v8x
    loader uses (id + info JSON bytes) and resolves tick/step/min-notional
    from the exchangeInfo-shaped ``filters`` block, without importing
    data.catalog (no nautilus dependency for the synthetic fixture)."""
    out: dict[str, dict] = {}
    for sym in symbols:
        pat = os.path.join(str(catalog_root), "data", "crypto_perpetual",
                           f"{sym}-PERP.{VENUE}", "*.parquet")
        files = sorted(glob.glob(pat))
        if not files:
            out[sym] = {"present": False}
            continue
        row = pq.read_table(files[0]).to_pandas().iloc[0]
        info = json.loads(bytes(row["info"]))
        filters = {f.get("filterType"): f for f in info.get("filters", [])}
        tick = filters.get("PRICE_FILTER", {}).get("tickSize")
        step = filters.get("LOT_SIZE", {}).get("stepSize")
        min_not = filters.get("MIN_NOTIONAL", {}).get("minNotional")
        out[sym] = {
            "present": True,
            "instrument_id": str(row["id"]),
            "tick_size": float(tick) if tick is not None else None,
            "step_size": float(step) if step is not None else None,
            "min_notional": str(min_not) if min_not else None,
        }
    all_ok = all(
        m.get("present")
        and isinstance(m.get("tick_size"), float) and m["tick_size"] > 0
        and isinstance(m.get("step_size"), float) and m["step_size"] > 0
        and m.get("min_notional")
        for m in out.values()
    )
    return {
        "method": "instrument_parquet_info_json_filters(<SYM>-PERP.BINANCE)",
        "limitation": limitation_text,
        "per_symbol": out,
        "all_ten_present_with_tick_step_min_notional": bool(all_ok),
    }


def collect_files_by_symbol(catalog_root: str | Path, funding_root: str | Path,
                            symbols: list[str]) -> dict[str, dict]:
    """V8 data-manifest hashing pattern (data_audit_v8.collect_source_files).

    Stored paths are relative to the respective root's parent, so fixture
    bundles yield host-independent relative strings.
    """
    cat = Path(catalog_root)
    fund = Path(funding_root)
    inventory: dict[str, dict] = {}
    for symbol in symbols:
        bt_dir = cat / "data" / "binance_bar" / f"{symbol}-PERP.{VENUE}{BAR_SUFFIX}"
        inst_dir = cat / "data" / "crypto_perpetual" / f"{symbol}-PERP.{VENUE}"
        fpath = fund / symbol / "funding.json"
        inventory[symbol] = {
            "bar_files": [
                {"path": str(p.relative_to(cat.parent)), "bytes": p.stat().st_size,
                 "sha256": sha256_file(p)}
                for p in sorted(bt_dir.glob("*.parquet"))
            ],
            "instrument_files": [
                {"path": str(p.relative_to(cat.parent)), "bytes": p.stat().st_size,
                 "sha256": sha256_file(p)}
                for p in sorted(inst_dir.glob("*.parquet"))
            ],
            "funding_files": (
                [{"path": str(fpath.relative_to(fund.parent)),
                  "bytes": fpath.stat().st_size, "sha256": sha256_file(fpath)}]
                if fpath.exists() else []
            ),
        }
    return inventory


def flatten_source_hashes(inventory: dict[str, dict]) -> dict[str, str]:
    flat: dict[str, str] = {}
    for groups in inventory.values():
        for group in ("bar_files", "instrument_files", "funding_files"):
            for item in groups[group]:
                flat[item["path"]] = item["sha256"]
    return flat


def _pinned_exact_volume(pinned: dict, symbol: str) -> str:
    """Exact Decimal volume string as recorded in candidates_evaluated (pinned)."""
    for cand in pinned.get("candidates_evaluated", []):
        if cand["symbol"] == symbol:
            return cand["volume"]["median_daily_quote_volume_usdt_exact"]
    raise KeyError(symbol)


# --------------------------------------------------------------------------- #
# Frozen configuration (engine inputs that used to be module globals)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FrozenConfig:
    """Everything the pure engine needs that used to be a module constant.

    Defaults are exactly today's frozen real-path constants, so the REAL
    artifact structure remains byte-identical; the synthetic fixture supplies
    the same values with fixture-local LABEL strings (no host paths).
    """
    schema_version: str = SCHEMA_VERSION
    agent: str = AGENT
    generated_at_utc: str = GENERATED_AT_UTC
    audit_label: str = AUDIT_LABEL
    gate_id: str = GATE_ID
    pre_start_s: int = PRE_START_S
    pre_end_s: int = PRE_END_S
    scored_start_s: int = SCORED_START_S
    scored_end_s: int = SCORED_END_S
    first_possible_exposure_s: int = dt_to_s(FIRST_POSSIBLE_EXPOSURE)
    listing_age_min_days: int = LISTING_AGE_MIN_DAYS
    top_n: int = TOP_N
    btc_symbol: str = BTC_SYMBOL
    venue: str = VENUE
    quote_required: str = QUOTE_REQUIRED
    bar_interval_s: int = BAR_INTERVAL_S
    bar_suffix: str = BAR_SUFFIX
    max_funding_interval_s: int = 28800
    documented_capture_boundary_classes: frozenset = DOCUMENTED_CAPTURE_BOUNDARY_CLASSES
    funding_assumption_text: str = FUNDING_ASSUMPTION_TEXT
    pit_limitation_text: str = PIT_METADATA_LIMITATION_TEXT
    not_selected_note: str = NOT_SELECTED_NOTE
    scored_measured_required_basis_tmpl: str = SCORED_MEASURED_REQUIRED_BASIS_TMPL
    scored_measured_all_basis: str = SCORED_MEASURED_ALL_BASIS
    catalog_label: str = str(CATALOG_ROOT)
    funding_label: str = str(FUNDING_ROOT)
    source_manifest_label: str = str(SOURCE_MANIFEST_RELPATH)
    selector_label: str = str(SOURCE_SELECTOR_RELPATH)
    canonical_v8_manifest_label: str = SOURCE_CANONICAL_V8_MANIFEST_PATH
    canonical_v8_selector_label: str = SOURCE_CANONICAL_V8_SELECTOR_PATH
    pinned_manifest_sha256: str = PINNED_SOURCE_MANIFEST_SHA256
    pinned_selector_sha256: str = PINNED_SOURCE_SELECTOR_SHA256
    artifact_relpaths: tuple = ARTIFACT_RELPATHS


REAL_FROZEN_CONFIG = FrozenConfig()


def fixture_frozen_config() -> FrozenConfig:
    """Frozen config for the committed synthetic fixture bundle.

    Identical window/gate constants to the real path; only the LABEL strings
    that land in the artifacts are fixture-relative (never host-absolute).
    """
    return FrozenConfig(
        catalog_label=FIXTURE_CATALOG_RELPATH,
        funding_label=FIXTURE_FUNDING_RELPATH,
        source_manifest_label=FIXTURE_PINNED_MANIFEST_RELPATH,
        canonical_v8_manifest_label=(
            FIXTURE_PINNED_MANIFEST_RELPATH
            + " (repo-authored synthetic replica of "
            + str(SOURCE_MANIFEST_RELPATH) + ")"
        ),
        canonical_v8_selector_label=(
            str(SOURCE_SELECTOR_RELPATH)
            + " (shared pinned selector; sha-verified)"
        ),
        pinned_manifest_sha256=FIXTURE_PINNED_MANIFEST_SHA256,
    )


# --------------------------------------------------------------------------- #
# Descriptors + typed inputs
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AuditDescriptor:
    """Environment resolution: WHERE every input lives and how to verify it."""
    repo_root: Path
    catalog_root: Path
    funding_root: Path
    pinned_manifest_path: Path
    pinned_manifest_sha256: str
    selector_path: Path
    pinned_selector_sha256: str
    frozen_config: FrozenConfig = REAL_FROZEN_CONFIG
    pit_provider: str = "data_catalog"  # or "instrument_parquet" (bundle path)

    def expected_inputs(self) -> list[dict]:
        return [
            {"name": "catalog_root", "path": str(self.catalog_root), "required": True},
            {"name": "funding_root", "path": str(self.funding_root), "required": True},
            {"name": "pinned_selection_manifest",
             "path": str(self.pinned_manifest_path), "required": True},
            {"name": "selector_script", "path": str(self.selector_path),
             "required": True},
        ]


def real_descriptor(repo_root: Path = REPO_ROOT,
                    catalog_root: str | Path | None = None,
                    funding_root: str | Path | None = None) -> AuditDescriptor:
    """Descriptor for the REAL host data paths (v8x env-overridable defaults)."""
    return AuditDescriptor(
        repo_root=Path(repo_root),
        catalog_root=Path(catalog_root if catalog_root is not None else CATALOG_ROOT),
        funding_root=Path(funding_root if funding_root is not None else FUNDING_ROOT),
        pinned_manifest_path=Path(repo_root) / SOURCE_MANIFEST_RELPATH,
        pinned_manifest_sha256=PINNED_SOURCE_MANIFEST_SHA256,
        selector_path=Path(repo_root) / SOURCE_SELECTOR_RELPATH,
        pinned_selector_sha256=PINNED_SOURCE_SELECTOR_SHA256,
        frozen_config=REAL_FROZEN_CONFIG,
        pit_provider="data_catalog",
    )


def fixture_descriptor(repo_root: Path = REPO_ROOT) -> AuditDescriptor:
    """Descriptor for the committed synthetic fixture under tests/fixtures/."""
    repo_root = Path(repo_root)
    return AuditDescriptor(
        repo_root=repo_root,
        catalog_root=repo_root / FIXTURE_CATALOG_RELPATH,
        funding_root=repo_root / FIXTURE_FUNDING_RELPATH,
        pinned_manifest_path=repo_root / FIXTURE_PINNED_MANIFEST_RELPATH,
        pinned_manifest_sha256=FIXTURE_PINNED_MANIFEST_SHA256,
        selector_path=repo_root / SOURCE_SELECTOR_RELPATH,
        pinned_selector_sha256=PINNED_SOURCE_SELECTOR_SHA256,
        frozen_config=fixture_frozen_config(),
        pit_provider="instrument_parquet",
    )


@dataclass(frozen=True)
class InputsBundle:
    """Typed, fully-resolved inputs; the pure engine consumes ONLY this."""
    descriptor: AuditDescriptor
    frozen_config: FrozenConfig
    pinned: dict
    source_block: dict
    chosen: list
    symbols: list[str]
    btc_in_selected: bool
    bar_files: dict
    funding_rows: dict
    funding_present: frozenset
    instruments: dict
    pit: dict
    availability_census: dict

    @property
    def available(self) -> bool:
        return True


@dataclass(frozen=True)
class InputsUnavailable:
    """Typed unavailable result: which inputs are missing and where."""
    descriptor: AuditDescriptor
    missing: list
    expected_inputs: list
    availability_census: dict

    @property
    def available(self) -> bool:
        return False


def _availability_census(descriptor: AuditDescriptor) -> dict:
    """Read-only existence/census probes (local filesystem metadata only)."""
    cat = Path(descriptor.catalog_root)
    fund = Path(descriptor.funding_root)
    bar_dirs = fund_dirs = 0
    if cat.exists():
        bar_dirs = sum(1 for p in (cat / "data" / "binance_bar").glob("*-PERP.*")
                       if p.is_dir()) if (cat / "data" / "binance_bar").exists() else 0
    if fund.exists():
        fund_dirs = sum(1 for p in fund.glob("*/funding.json") if p.is_file())
    return {
        "catalog_root_present": cat.exists(),
        "funding_root_present": fund.exists(),
        "pinned_selection_manifest_present":
            Path(descriptor.pinned_manifest_path).exists(),
        "selector_script_present": Path(descriptor.selector_path).exists(),
        "catalog_bar_symbol_dirs": bar_dirs,
        "funding_symbol_files": fund_dirs,
    }


def load_inputs(descriptor: AuditDescriptor) -> InputsBundle | InputsUnavailable:
    """Resolve ALL environment inputs for the V9 audit.

    Returns a typed InputsBundle, or -- when a required input root/file is
    absent -- the typed InputsUnavailable result carrying the missing paths.
    A present-but-tampered pinned artifact raises PinVerificationError
    (integrity failure is a different failure class than absence).
    """
    missing = [
        {"name": item["name"], "path": item["path"], "reason": "file_not_found"}
        for item in descriptor.expected_inputs()
        if not Path(item["path"]).exists()
    ]
    census = _availability_census(descriptor)
    if missing:
        return InputsUnavailable(
            descriptor=descriptor,
            missing=missing,
            expected_inputs=descriptor.expected_inputs(),
            availability_census=census,
        )

    pinned, source_block = load_pinned_selection(
        repo_root=descriptor.repo_root,
        pinned_manifest_sha256=descriptor.pinned_manifest_sha256,
        pinned_selector_sha256=descriptor.pinned_selector_sha256,
        manifest_path=descriptor.pinned_manifest_path,
        selector_path=descriptor.selector_path,
        manifest_label=descriptor.frozen_config.source_manifest_label,
        selector_label=descriptor.frozen_config.selector_label,
        canonical_v8_manifest_path=descriptor.frozen_config.canonical_v8_manifest_label,
        canonical_v8_selector_path=descriptor.frozen_config.canonical_v8_selector_label,
    )
    source_block["schema_version"] = pinned["schema_version"]
    source_block["agent"] = pinned["agent"]
    source_block["generated_at_utc"] = pinned["generated_at_utc"]
    source_block["verdict"] = pinned["verdict"]

    chosen = pinned["chosen_top10"]
    symbols = [c["symbol"] for c in chosen]

    funding_files = {
        os.path.basename(os.path.dirname(p)): p
        for p in sorted(glob.glob(os.path.join(str(descriptor.funding_root),
                                               "*", "funding.json")))
    }
    funding_rows = {sym: json.load(open(p))["rows"]
                    for sym, p in funding_files.items()}

    instruments = {sym: load_instrument_from(descriptor.catalog_root, sym)
                   for sym in symbols}
    if descriptor.frozen_config.btc_symbol not in instruments:
        instruments[descriptor.frozen_config.btc_symbol] = load_instrument_from(
            descriptor.catalog_root, descriptor.frozen_config.btc_symbol)

    if descriptor.pit_provider == "data_catalog":
        pit = pit_metadata_via_catalog(descriptor.catalog_root, symbols)
    elif descriptor.pit_provider == "instrument_parquet":
        pit = pit_metadata_via_instrument_parquet(
            descriptor.catalog_root, symbols,
            descriptor.frozen_config.pit_limitation_text)
    else:  # pragma: no cover - guarded by construction
        raise ValueError(f"unknown pit_provider: {descriptor.pit_provider}")

    return InputsBundle(
        descriptor=descriptor,
        frozen_config=descriptor.frozen_config,
        pinned=pinned,
        source_block=source_block,
        chosen=chosen,
        symbols=symbols,
        btc_in_selected=descriptor.frozen_config.btc_symbol in symbols,
        bar_files={sym: bar_files_for_symbol(descriptor.catalog_root, sym)
                   for sym in [*symbols, descriptor.frozen_config.btc_symbol]},
        funding_rows=funding_rows,
        funding_present=frozenset(funding_rows),
        instruments=instruments,
        pit=pit,
        availability_census=census,
    )


# --------------------------------------------------------------------------- #
# Typed funding block for ABSENT funding rows (the original crash site)
# --------------------------------------------------------------------------- #
def funding_audit_absent(cfg: FrozenConfig) -> dict:
    """Truthful typed block when a symbol has NO funding rows at all.

    Marks incompleteness on every gate so the funding coverage check fails
    (FAIL_FUNDING_COVERAGE) -- never a TypeError, never fabricated
    completeness.  Superset of the analyze_funding key set plus the
    ``funding_data_present`` marker (present-path blocks keep their exact
    v8x shape so real-path output bytes are unchanged).
    """
    return {
        "funding_data_present": False,
        "exposure_span_utc": [utc_str(cfg.scored_start_s), utc_str(cfg.scored_end_s)],
        "settlements_in_exposure_span": 0,
        "first_settlement_utc": None,
        "last_settlement_utc": None,
        "duplicate_timestamps": 0,
        "distinct_interval_seconds": [],
        "cadence_mode_minutes": None,
        "gate_sorted_unique_f1": False,
        "gate_legal_intervals_f2": False,
        "gate_boundary_coverage_f3": False,
        "flagged_interval_steps": [],
        "complete": False,
    }


# --------------------------------------------------------------------------- #
# Pure engine
# --------------------------------------------------------------------------- #
def run_audit_from_bundle(bundle: InputsBundle,
                          frozen_config: FrozenConfig | None = None) -> dict:
    """Pure computation: build {"manifest","audit","gate"} from the bundle.

    Reads NOTHING from the environment outside ``bundle``/``frozen_config``.
    """
    cfg = frozen_config if frozen_config is not None else bundle.frozen_config
    pinned = bundle.pinned
    source_block = dict(bundle.source_block)

    chosen = bundle.chosen
    symbols = list(bundle.symbols)
    assert len(symbols) == cfg.top_n, f"pinned selection must have exactly {cfg.top_n} symbols"
    assert len(set(symbols)) == cfg.top_n, "duplicate symbols in pinned selection"
    btc_symbol = cfg.btc_symbol
    btc_in_selected = btc_symbol in symbols

    # ---- current-bytes revalidation -------------------------------------- #
    funding_raw = bundle.funding_rows
    corroborate = build_corroboration(funding_raw)

    per_symbol_reval: dict[str, dict] = {}
    drifts: list[dict] = []
    selected_symbols: list[dict] = []
    coverage_required: dict[str, tuple[int, int]] = {}
    coverage_all: dict[str, tuple[int, int]] = {}

    for entry in chosen:
        sym = entry["symbol"]
        files = bundle.bar_files[sym]
        inst = bundle.instruments.get(sym)
        vol = median_daily_quote_volume_pre_window(files)
        cen_pre = census_for_symbol(files, cfg.pre_start_s, cfg.pre_end_s)
        cen_sc = census_for_symbol(files, cfg.scored_start_s, cfg.scored_end_s)
        fund = (analyze_funding(funding_raw[sym], corroborate)
                if sym in funding_raw else funding_audit_absent(cfg))
        age = listing_age_check(inst, cfg.first_possible_exposure_s,
                                cfg.listing_age_min_days)
        meta_ok = bool(inst and inst["quote_currency"] == cfg.quote_required
                       and inst["contract_type"] == "PERPETUAL"
                       and inst["status"] == "TRADING")

        cov_sc = measured_coverage(files, cfg.scored_start_s, cfg.scored_end_s)
        cov_pre = measured_coverage(files, cfg.pre_start_s, cfg.pre_end_s)
        if cov_sc is not None:
            coverage_all[sym] = cov_sc
            if sym != btc_symbol:
                coverage_required[sym] = cov_sc
        dups = duplicate_raw_stamps(files)

        # drift vs pinned metrics (exact decimal string comparison)
        pinned_exact_vol = _pinned_exact_volume(pinned, sym)
        if vol["median_daily_quote_volume_usdt_exact"] != pinned_exact_vol:
            drifts.append({"symbol": sym, "field": "median_daily_quote_volume_usdt_exact",
                           "pinned": pinned_exact_vol,
                           "current": vol["median_daily_quote_volume_usdt_exact"]})
        if entry["days_with_bars_pre_window"] != vol["days_with_bars_pre_window"]:
            drifts.append({"symbol": sym, "field": "days_with_bars_pre_window",
                           "pinned": entry["days_with_bars_pre_window"],
                           "current": vol["days_with_bars_pre_window"]})
        if entry["census_pre_window_gaps"] != cen_pre["gaps_found"]:
            drifts.append({"symbol": sym, "field": "census_pre_window_gaps",
                           "pinned": entry["census_pre_window_gaps"],
                           "current": cen_pre["gaps_found"]})
        if entry["census_scored_window_gaps"] != cen_sc["gaps_found"]:
            drifts.append({"symbol": sym, "field": "census_scored_window_gaps",
                           "pinned": entry["census_scored_window_gaps"],
                           "current": cen_sc["gaps_found"]})
        if entry["census_scored_window_unexplained"] != cen_sc["unexplained_gaps"]:
            drifts.append({"symbol": sym, "field": "census_scored_window_unexplained",
                           "pinned": entry["census_scored_window_unexplained"],
                           "current": cen_sc["unexplained_gaps"]})
        if entry["funding_held_exposure_complete"] != fund["complete"]:
            drifts.append({"symbol": sym, "field": "funding_held_exposure_complete",
                           "pinned": entry["funding_held_exposure_complete"],
                           "current": fund["complete"]})

        per_symbol_reval[sym] = {
            "instrument_id": f"{sym}-PERP.{cfg.venue}",
            "metadata_sanity_ok": meta_ok,
            "listing_age": age,
            "volume_pre_window": vol,
            "census_pre_window": cen_pre,
            "census_scored_window": cen_sc,
            "funding_held_exposure_audit": fund,
            "scored_window_first_open_utc": utc_str(cov_sc[0]) if cov_sc else None,
            "scored_window_last_open_utc": utc_str(cov_sc[1]) if cov_sc else None,
            "pre_window_first_open_utc": utc_str(cov_pre[0]) if cov_pre else None,
            "pre_window_last_open_utc": utc_str(cov_pre[1]) if cov_pre else None,
            "duplicate_bar_timestamps_scored_and_pre": dups,
        }

        selected_symbols.append({
            "rank": entry["rank"],
            "symbol": sym,
            "instrument_id": f"{sym}-PERP.{cfg.venue}",
            "median_daily_quote_volume_pre_window_usdt":
                vol["median_daily_quote_volume_usdt"],
            "median_daily_quote_volume_pre_window_usdt_exact":
                vol["median_daily_quote_volume_usdt_exact"],
            "days_with_bars_pre_window": vol["days_with_bars_pre_window"],
            "census_pre_window_gaps": cen_pre["gaps_found"],
            "census_pre_window_unexplained": cen_pre["unexplained_gaps"],
            "census_scored_window_gaps": cen_sc["gaps_found"],
            "census_scored_window_unexplained": cen_sc["unexplained_gaps"],
            "funding_held_exposure_complete": bool(fund["complete"]),
            "listing_age_days_at_first_possible_exposure":
                age["age_days_at_first_possible_exposure"],
            "listing_age_gate_ok": age["ok"],
            "metadata_sanity_ok": meta_ok,
        })

    selected_symbols.sort(key=lambda c: c["rank"])

    # ---- BTC benchmark context ------------------------------------------- #
    btc_context: dict | None = None
    btc_censuses: dict[str, dict] = {}
    btc_cov = None
    if not btc_in_selected:
        btc_files = bundle.bar_files.get(btc_symbol, [])
        if btc_files:
            btc_cov = measured_coverage(btc_files, cfg.scored_start_s, cfg.scored_end_s)
            if btc_cov is not None:
                coverage_all[btc_symbol] = btc_cov
            btc_censuses = {
                "pre_window": census_for_symbol(btc_files, cfg.pre_start_s, cfg.pre_end_s),
                "scored_window": census_for_symbol(btc_files, cfg.scored_start_s,
                                                   cfg.scored_end_s),
            }
            btc_fund = analyze_funding(funding_raw[btc_symbol], corroborate) \
                if btc_symbol in funding_raw else None
            btc_dups = duplicate_raw_stamps(btc_files)
            btc_context = {
                "symbol": btc_symbol,
                "instrument_id": f"{btc_symbol}-PERP.{cfg.venue}",
                "role": "benchmark_measurement_only_excluded_from_ranking",
                "census_pre_window_gaps": btc_censuses["pre_window"]["gaps_found"],
                "census_scored_window_gaps": btc_censuses["scored_window"]["gaps_found"],
                "census_scored_window_unexplained":
                    btc_censuses["scored_window"]["unexplained_gaps"],
                "funding_held_exposure_complete":
                    bool((btc_fund or {}).get("complete")),
                "funding_held_exposure_audit": btc_fund,
                "duplicate_bar_timestamps": btc_dups,
                "scored_window_first_open_utc": utc_str(btc_cov[0]) if btc_cov else None,
                "scored_window_last_open_utc": utc_str(btc_cov[1]) if btc_cov else None,
            }

    # ---- measured common completed-bar windows ---------------------------- #
    required_basis = cfg.scored_measured_required_basis_tmpl.format(
        win_start=utc_str(cfg.scored_start_s), win_end=utc_str(cfg.scored_end_s))
    req_start, req_end = intersection_range(coverage_required)
    all_start, all_end = intersection_range(coverage_all)
    scored_measured_required = {
        "start_utc": close_stamp_iso(req_start, cfg.bar_interval_s) if req_start is not None else None,
        "end_utc": close_stamp_iso(req_end, cfg.bar_interval_s) if req_end is not None else None,
        "basis": required_basis,
    }
    scored_measured_all = {
        "start_utc": close_stamp_iso(all_start, cfg.bar_interval_s) if all_start is not None else None,
        "end_utc": close_stamp_iso(all_end, cfg.bar_interval_s) if all_end is not None else None,
        "basis": cfg.scored_measured_all_basis,
    }

    # ---- gap-census totals ------------------------------------------------ #
    slots_checked = sum(
        per_symbol_reval[s]["census_pre_window"]["expected_15m_slots"]
        + per_symbol_reval[s]["census_scored_window"]["expected_15m_slots"]
        for s in symbols
    )
    gaps_found = sum(
        per_symbol_reval[s]["census_pre_window"]["gaps_found"]
        + per_symbol_reval[s]["census_scored_window"]["gaps_found"]
        for s in symbols
    )
    unexplained_total = sum(
        per_symbol_reval[s]["census_pre_window"]["unexplained_gaps"]
        + per_symbol_reval[s]["census_scored_window"]["unexplained_gaps"]
        for s in symbols
    )
    documented_runs = []
    non_boundary_explained: list[dict] = []
    for s in symbols:
        for wname in ("pre_window", "scored_window"):
            for g in per_symbol_reval[s][f"census_{wname}"]["gap_runs"]:
                rec = {"symbol": s, "window": wname, **{k: g[k] for k in
                        ("start_utc", "end_utc", "missing_slots", "cause",
                         "explained", "evidence")}}
                if g["cause"] in cfg.documented_capture_boundary_classes:
                    documented_runs.append(rec)
                elif g["explained"]:
                    non_boundary_explained.append(rec)

    # BTC context censuses were computed above; include their totals separately
    btc_slots = sum(v["expected_15m_slots"] for v in btc_censuses.values()) \
        if btc_censuses else 0
    btc_gaps = sum(v["gaps_found"] for v in btc_censuses.values()) if btc_censuses else 0
    btc_unexplained = sum(v["unexplained_gaps"] for v in btc_censuses.values()) \
        if btc_censuses else 0

    # ---- funding verdicts -------------------------------------------------- #
    # (typed blocks guarantee "complete" exists -- the historical
    #  TypeError 'NoneType' object is not a mapping crash site)
    funding_per_symbol = {
        s: {**per_symbol_reval[s]["funding_held_exposure_audit"],
            "verdict": ("COMPLETE"
                        if per_symbol_reval[s]["funding_held_exposure_audit"]["complete"]
                        else "INCOMPLETE")}
        for s in symbols
    }
    funding_all_complete = all(
        per_symbol_reval[s]["funding_held_exposure_audit"]["complete"] for s in symbols
    )

    # ---- PIT instrument metadata ------------------------------------------ #
    pit = bundle.pit

    # ---- gate -------------------------------------------------------------- #
    failed_ages = [s for s in symbols if not per_symbol_reval[s]["listing_age"]["ok"]]
    failed_meta = [s for s in symbols if not per_symbol_reval[s]["metadata_sanity_ok"]]

    checks = [
        {"id": "source_selection_artifact_pinned_sha256_verified",
         "ok": True,
         "detail": (f"{cfg.source_manifest_label} sha256 matches pinned value "
                    f"{cfg.pinned_manifest_sha256}; selector script sha256 "
                    f"matches {cfg.pinned_selector_sha256} (corrected rule "
                    "reused unmodified)")},
        {"id": "selection_rule_reuse_no_new_rule",
         "ok": True,
         "detail": ("all census/ranking/funding/gate logic imported verbatim from "
                    "scripts.v8x_crypto_universe_selection (V8 A8 corrected "
                    "selector); no new selection parameters introduced")},
        {"id": "top10_revalidated_against_current_catalog_bytes",
         "ok": not drifts,
         "detail": ("volume metric (Decimal-exact), days-with-bars, both-window "
                    "gap counts, funding completeness recomputed and compared to "
                    "the pinned manifest"),
         "drifts": drifts},
        {"id": "btc_excluded_from_traded_universe",
         "ok": not btc_in_selected,
         "detail": (f"{btc_symbol} absent from the 10 ranked symbols; carried as "
                    "benchmark measurement-only context")},
        {"id": "gap_census_unexplained_zero_both_windows",
         "ok": unexplained_total == 0,
         "detail": (f"slots_checked={slots_checked} gaps_found={gaps_found} "
                    f"unexplained={unexplained_total} over pre-window AND scored "
                    "window for the 10 alts; only permitted gap class is the "
                    "documented capture-boundary class"),
         "non_boundary_explained_classes": non_boundary_explained},
        {"id": "listing_age_min_365d_at_first_possible_exposure",
         "ok": not failed_ages,
         "failed_symbols": failed_ages,
         "detail": (f"onboard_date <= scored-window start minus "
                    f"{cfg.listing_age_min_days}d evaluated at the conservative "
                    f"first-possible-exposure {utc_str(cfg.first_possible_exposure_s)}")},
        {"id": "funding_held_exposure_completeness_all_selected",
         "ok": funding_all_complete,
         "assumption": cfg.funding_assumption_text,
         "detail": ("settlements contiguous with legal exchange intervals, no "
                    "duplicates, boundary coverage from first possible weekly "
                    "exposure through scored-window end; interval-regime steps "
                    "cross-symbol corroborated")},
        {"id": "pit_instrument_metadata_tick_step_min_notional_present",
         "ok": pit["all_ten_present_with_tick_step_min_notional"],
         "detail": pit["method"],
         "limitation": pit["limitation"]},
    ]
    status = "PASS"
    fail_tags = {
        "top10_revalidated_against_current_catalog_bytes": "FAIL_SELECTION_DRIFT",
        "btc_excluded_from_traded_universe": "FAIL_BTC_EXCLUSION_BROKEN",
        "gap_census_unexplained_zero_both_windows": "FAIL_UNEXPLAINED_GAPS",
        "listing_age_min_365d_at_first_possible_exposure": "FAIL_LISTING_AGE",
        "funding_held_exposure_completeness_all_selected": "FAIL_FUNDING_COVERAGE",
        "pit_instrument_metadata_tick_step_min_notional_present": "FAIL_PIT_METADATA",
    }
    for c in checks:
        if not c["ok"] and c["id"] in fail_tags:
            status = fail_tags[c["id"]]
            break

    # ---- normalized block (V8 data-manifest pattern) ----------------------- #
    inventory = collect_files_by_symbol(bundle.descriptor.catalog_root,
                                        bundle.descriptor.funding_root,
                                        [*symbols, btc_symbol])
    source_hashes_flat = flatten_source_hashes(inventory)

    def _sym_norm(sym: str) -> dict:
        if sym == btc_symbol and btc_context is not None:
            cen_sc_n = btc_censuses.get("scored_window", {})
            cen = btc_censuses
        else:
            r = per_symbol_reval[sym]
            cen_sc_n = r["census_scored_window"]
            cen = {"pre_window": r["census_pre_window"], "scored_window": cen_sc_n}
        hours = sum(
            cen[w]["unexplained_gaps"] * (cfg.bar_interval_s / 3600.0)
            for w in ("pre_window", "scored_window")
        )
        fund = (btc_context["funding_held_exposure_audit"]
                if sym == btc_symbol and btc_context is not None
                else per_symbol_reval[sym]["funding_held_exposure_audit"])
        cov = coverage_all.get(sym)
        return {
            "completed_bars_in_scored_window": cen_sc_n.get("expected_15m_slots", 0)
            - cen_sc_n.get("gaps_found", 0),
            "first_completed_close_utc":
                close_stamp_iso(cov[0], cfg.bar_interval_s) if cov else None,
            "last_completed_close_utc":
                close_stamp_iso(cov[1], cfg.bar_interval_s) if cov else None,
            "duplicate_timestamps":
                btc_context["duplicate_bar_timestamps"]
                if sym == btc_symbol and btc_context is not None
                else per_symbol_reval[sym]["duplicate_bar_timestamps_scored_and_pre"],
            "unexplained_gap_hours_both_windows": round(hours, 6),
            "funding_settlements_in_scored_window":
                (fund or {}).get("settlements_in_exposure_span", 0),
            "role": ("benchmark_context_only" if sym == btc_symbol else "required"),
            "verdict": ("PASS_CONTEXT_BENCHMARK_ONLY" if sym == btc_symbol
                        else "PASS"),
        }

    normalized = {
        "label": cfg.audit_label,
        "target_window": {
            "start": utc_str(cfg.scored_start_s),
            "end": utc_str(cfg.scored_end_s),
        },
        "common_window_required": scored_measured_required,
        "common_window_all_audited": scored_measured_all,
        "symbols": {s: _sym_norm(s) for s in sorted([*symbols, btc_symbol])
                    if s in inventory},
    }
    normalized_manifest_sha256 = sha256_obj(normalized)

    # ---- deliverable 2: universe_selection_v9.json ------------------------- #
    manifest = {
        "schema_version": cfg.schema_version,
        "artifact": "universe_selection_v9",
        "agent": cfg.agent,
        "generated_at_utc": cfg.generated_at_utc,
        "performance_blind": True,
        "source_selection_artifact": source_block,
        "selection_rule_reuse_note": (
            "V9 cohort-10 universe REUSES the corrected V8 A8 selection rule "
            "verbatim (pre-window median daily quote-volume ranking, BTC excluded "
            "before ranking, exact 15m gap census, held-exposure funding proof); "
            "re-pinned under V9 ownership with sha256 verification; no new rule "
            "or parameter was introduced"),
        "selection_window": pinned["selection_window"],
        "scored_window_contract": pinned["scored_window"],
        "scored_window": scored_measured_required,
        "ranking_rule": pinned["ranking_rule"],
        "btc_excluded": True,
        "btc_benchmark_context_only": {
            "symbol": btc_symbol,
            "instrument_id": f"{btc_symbol}-PERP.{cfg.venue}",
            "excluded_from_ranks_weights_pnl": True,
            "context_summary": btc_context,
        },
        "selected_symbols": selected_symbols,
        "not_selected_eligible_note": cfg.not_selected_note,
        "files_by_symbol": inventory,
        "source_hashes_flat": source_hashes_flat,
        "hash_algorithm": "sha256",
        "normalized": normalized,
        "normalized_manifest_sha256": normalized_manifest_sha256,
    }

    # ---- deliverable 3: data_audit_v9.json --------------------------------- #
    audit_doc = {
        "schema_version": cfg.schema_version,
        "artifact": "data_audit_v9",
        "agent": cfg.agent,
        "generated_at_utc": cfg.generated_at_utc,
        "label": cfg.audit_label,
        "catalog_path": cfg.catalog_label,
        "funding_dir": cfg.funding_label,
        "windows": {
            "pre_window": {"start_utc": utc_str(cfg.pre_start_s),
                           "end_utc": utc_str(cfg.pre_end_s)},
            "scored_window_contract": {"start_utc": utc_str(cfg.scored_start_s),
                                       "end_utc": utc_str(cfg.scored_end_s)},
            "scored_window_measured_required": scored_measured_required,
            "scored_window_measured_all_audited": scored_measured_all,
            "per_symbol_scored_coverage_open_stamps": {
                s: {"first_open_utc": per_symbol_reval[s]["scored_window_first_open_utc"],
                    "last_open_utc": per_symbol_reval[s]["scored_window_last_open_utc"]}
                for s in symbols
            },
        },
        "gap_census": {
            "method": ("exact 15-minute grid census over BOTH windows, imported "
                       "verbatim from the corrected V8 A8 selector "
                       "(scripts/v8x_crypto_universe_selection.census_for_symbol)"),
            "interval_seconds": cfg.bar_interval_s,
            "classification_rule": (
                "run strictly inside ONE capture session's observed range => "
                "unexplained; run bounded before/after/by capture-session edges "
                "=> explained capture-boundary cause"),
            "scope": "10 selected altcoins (BTCUSDT reported as context below)",
            "slots_checked_total": slots_checked,
            "gaps_found_total": gaps_found,
            "unexplained_gaps_total": unexplained_total,
            "documented_gap_classes_present": documented_runs,
            "non_boundary_explained_classes": non_boundary_explained,
            "btc_context_totals": {"slots_checked": btc_slots,
                                   "gaps_found": btc_gaps,
                                   "unexplained_gaps": btc_unexplained},
            "per_symbol": {
                s: {"pre_window": per_symbol_reval[s]["census_pre_window"],
                    "scored_window": per_symbol_reval[s]["census_scored_window"]}
                for s in symbols
            },
            "btc_context_census": btc_censuses,
        },
        "funding_coverage": {
            "assumption": cfg.funding_assumption_text,
            "first_possible_exposure_utc": utc_str(cfg.first_possible_exposure_s),
            "max_interval_seconds": cfg.max_funding_interval_s,
            "per_symbol_verdict": {s: funding_per_symbol[s]["verdict"]
                                   for s in symbols},
            "per_symbol": funding_per_symbol,
            "all_selected_complete": funding_all_complete,
        },
        "pit_instrument_metadata": pit,
        "listing_age_gate": {
            "min_days": cfg.listing_age_min_days,
            "first_possible_exposure_utc": utc_str(cfg.first_possible_exposure_s),
            "per_symbol": {s: per_symbol_reval[s]["listing_age"] for s in symbols},
            "all_ok": not failed_ages,
        },
        "btc_exclusion_check": {
            "btc_symbol": btc_symbol,
            "in_selected_ten": btc_in_selected,
            "benchmark_only_context_present": btc_context is not None,
            "excluded_before_ranking": True,
        },
        "revalidation_vs_pinned": {"matched": not drifts, "drifts": drifts},
        "source_hashes_flat": source_hashes_flat,
        "normalized_manifest_sha256": normalized_manifest_sha256,
        "verdict": ("V9_DATA_AUDIT_PASS" if status == "PASS"
                    else f"V9_DATA_AUDIT_{status}"),
    }

    # ---- deliverable 4: t02_gate_v9.json ----------------------------------- #
    gate = {
        "schema_version": cfg.schema_version,
        "artifact": "t02_gate_v9",
        "gate": cfg.gate_id,
        "agent": cfg.agent,
        "generated_at_utc": cfg.generated_at_utc,
        "status": status,
        "selected_symbols": [c["symbol"] for c in selected_symbols],
        "btc_excluded": True,
        "scored_window_measured": scored_measured_required,
        "gap_census_totals": {
            "slots_checked": slots_checked,
            "gaps_found": gaps_found,
            "unexplained": unexplained_total,
        },
        "funding_completeness": {
            "all_selected_complete": funding_all_complete,
            "assumption": cfg.funding_assumption_text,
        },
        "checks": checks,
        "artifacts": list(cfg.artifact_relpaths),
        "normalized_manifest_sha256": normalized_manifest_sha256,
    }

    return {"manifest": manifest, "audit": audit_doc, "gate": gate}


# --------------------------------------------------------------------------- #
# REAL-path wrappers (delegate through load_inputs + run_audit_from_bundle)
# --------------------------------------------------------------------------- #
def run_audit(
    *,
    catalog_root: str | Path = CATALOG_ROOT,
    funding_root: str | Path = FUNDING_ROOT,
    repo_root: Path = REPO_ROOT,
) -> dict:
    """Full offline audit over the REAL host data paths.

    Returns {'manifest':..., 'audit':..., 'gate':...}.  Raises
    AuditInputsUnavailable (typed, with the missing paths) when the data is
    absent -- use run_real_historical_audit for the availability-artifact
    behavior instead of an exception.
    """
    descriptor = real_descriptor(repo_root=repo_root, catalog_root=catalog_root,
                                 funding_root=funding_root)
    loaded = load_inputs(descriptor)
    if not loaded.available:
        raise AuditInputsUnavailable(loaded)
    return run_audit_from_bundle(loaded)


def main(manifest_out: Path = DEFAULT_MANIFEST_OUT,
         audit_out: Path = DEFAULT_AUDIT_OUT,
         gate_out: Path = DEFAULT_GATE_OUT) -> dict:
    res = run_audit()
    for path, payload in ((manifest_out, res["manifest"]),
                          (audit_out, res["audit"]),
                          (gate_out, res["gate"])):
        write_json(Path(path), payload)
    return res


# --------------------------------------------------------------------------- #
# Availability-aware historical run (Tier-R support)
# --------------------------------------------------------------------------- #
def build_availability_artifact(descriptor: AuditDescriptor,
                                unavailable: InputsUnavailable) -> dict:
    """Observational artifact for a NOT_RUN_DATA_UNAVAILABLE outcome.

    Records expected inputs + paths, the availability census, invocation
    provenance (command/cwd/code SHA/UTC/host), the exact blocker, an offline
    assertion, and read-only (zero-mutation) hashes of any existing legacy
    states.  Unlike the audit artifacts this document intentionally carries
    the actual observation time.
    """
    legacy_hashes = {}
    for relpath in ARTIFACT_RELPATHS:
        p = Path(descriptor.repo_root) / relpath
        if p.exists():
            legacy_hashes[relpath] = {
                "sha256": sha256_file(p),
                "bytes": p.stat().st_size,
                "mutation": "none (read-only hash of existing state)",
            }
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": "v9_universe_audit_availability",
        "agent": AGENT,
        "generated_at_utc": utc_str(int(time.time())),
        "verdict": "NOT_RUN_DATA_UNAVAILABLE",
        "expected_inputs": unavailable.expected_inputs,
        "availability_census": unavailable.availability_census,
        "missing_inputs": unavailable.missing,
        "exact_blocker": "; ".join(
            f"{m['name']} not found at {m['path']}" for m in unavailable.missing),
        "invocation": {
            "command": list(sys.argv),
            "cwd": os.getcwd(),
            "code_path": str(Path(__file__).resolve()),
            "code_sha256": sha256_file(Path(__file__)),
            "selector_script_sha256": sha256_file(descriptor.selector_path),
            "utc": utc_str(int(time.time())),
            "host": platform.node(),
            "python": platform.python_version(),
        },
        "offline_assertion": {
            "network_access_used": False,
            "provider_api_calls": 0,
            "method": ("local filesystem existence probes, directory censuses and "
                       "sha256 hashes only; no network, no provider calls"),
        },
        "legacy_state_hashes": legacy_hashes,
        "note": ("no manifest/audit/gate artifact was produced: absent inputs are "
                 "reported truthfully instead of fabricating a PASS"),
    }


def run_real_historical_audit(descriptor: AuditDescriptor | None = None,
                              out_dir: Path | None = None) -> dict:
    """Run the real historical audit with truthful availability handling.

    Absent data -> writes the availability artifact, verdict
    NOT_RUN_DATA_UNAVAILABLE, and NEVER a fake manifest/audit/gate.
    Present data -> runs the engine and byte-compares the fresh outputs
    against the committed historical artifacts (PASS / FAIL).
    """
    d = descriptor if descriptor is not None else real_descriptor()
    out = Path(out_dir) if out_dir is not None else DEFAULT_TIER_R_OUT
    loaded = load_inputs(d)
    if not loaded.available:
        artifact = build_availability_artifact(d, loaded)
        artifact_path = out / "v9_availability.json"
        write_json(artifact_path, artifact)
        return {
            "verdict": "NOT_RUN_DATA_UNAVAILABLE",
            "out_dir": str(out),
            "availability_artifact_path": str(artifact_path),
            "comparison": [],
        }

    res = run_audit_from_bundle(loaded)
    run_paths = {
        "manifest": out / "universe_selection_v9.json",
        "audit": out / "data_audit_v9.json",
        "gate": out / "t02_gate_v9.json",
    }
    committed_paths = {
        "manifest": DEFAULT_MANIFEST_OUT,
        "audit": DEFAULT_AUDIT_OUT,
        "gate": DEFAULT_GATE_OUT,
    }
    comparison = []
    for name in ("manifest", "audit", "gate"):
        run_bytes = None
        if run_paths[name].exists():
            run_bytes = run_paths[name].read_bytes()
        write_json(run_paths[name], res[name])
        run_bytes = run_paths[name].read_bytes()
        committed = committed_paths[name]
        c_sha = sha256_file(committed) if committed.exists() else None
        r_sha = hashlib.sha256(run_bytes).hexdigest()
        comparison.append({
            "name": name,
            "committed_path": str(committed),
            "run_path": str(run_paths[name]),
            "match": bool(c_sha is not None and c_sha == r_sha),
            "committed_sha256": c_sha,
            "run_sha256": r_sha,
        })
    verdict = "PASS" if all(c["match"] for c in comparison) else "FAIL"
    return {
        "verdict": verdict,
        "out_dir": str(out),
        "availability_artifact_path": None,
        "comparison": comparison,
    }


if __name__ == "__main__":
    outcome = run_real_historical_audit(
        out_dir=Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    print("verdict:", outcome["verdict"])
    print("out_dir:", outcome["out_dir"])
    if outcome["availability_artifact_path"]:
        print("availability_artifact:", outcome["availability_artifact_path"])
    for c in outcome["comparison"]:
        print(f"  {c['name']}: match={c['match']}")
    sys.exit({"PASS": 0, "FAIL": 1, "NOT_RUN_DATA_UNAVAILABLE": 3}[outcome["verdict"]])
