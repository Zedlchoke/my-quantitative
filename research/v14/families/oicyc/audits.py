"""Audit-only evidence builders for the frozen OICYC family (V14 I lane).

SCOPE BOUNDARY: this module computes NO PnL, no returns and no scored
metric on real data.  Every real-data output is a field verification, a
count, a timestamp comparison, a SHA-256 equality, a schedule verdict or a
SHA-paired target record.  Nothing here publishes or scores.

All raw data are READ-ONLY workspace files at fixed absolute paths, never
copied or committed:

* daily OI consolidated parquets  -- ``/Users/hoangminhlong/my-quantitative/
  oi_data/consolidated`` (staging ``v11_oi_staging_v1``; schema
  ``{create_time, sum_open_interest}``; 417 daily rows x 20 symbols; BASE
  units).  EVERY load SHA-256-verifies each parquet against
  ``research/control/v11_run/oi_staging_manifest.json`` and FAILS CLOSED on
  any mismatch (the A7-N verified-load pattern, reused);
* completed 15m bars              -- the staged bar authority (a3 staging
  manifest); the loader is the FROZEN V13 OITD loader reused verbatim
  (Nautilus layout; ``ts_event`` is the bar-close boundary in ns; prices
  decode raw i128 / 1e16);
* mark-price snapshots and native funding settlements -- the frozen V13
  OITD loader reused verbatim (funding COST ONLY, never a signal input);
* instrument tick sizes           -- the frozen V12 audit loader
  (REAL perp-metadata tick sizes -- L-V14-0, never a uniform stub).

Evidence builders (each returns a JSON-safe payload):

* :func:`evidence_identity` -- frozen identity payloads + the recomputed
  vs recorded ``arm_config_digest`` report + the CONFIRMATORY status
  metadata;
* :func:`build_target_records` -- the chained hysteresis target schedule
  of one arm on the verified staged OI (schedule-only; no PnL, no
  positions persisted);
* :func:`verify_oi_staging` -- the SHA-256 staging verification payload.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

import pyarrow.parquet as pq

from research.adapter_v10.protocol import ContractViolation
from research.v12.data_contract import OI_CONSOLIDATED_ROOT, REQUIRED_SYMBOLS
from research.v12.families.oilev_v2.audits import load_tick_sizes
from research.v13.families.oitd.audits import (
    load_bars_for_plugin,
    load_marks_and_settlements,
)
from research.v14.families.oicyc.plugin import OicycPlugin
from research.v14.families.oicyc.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    BENCHMARK_SYMBOL,
    CONFIRMATORY,
    CONTROL_ARM,
    FAMILY_ID,
    FIRST_STAMP_ISO,
    NEIGHBOUR_ARM,
    SECTION_1_1_DISCLOSURE,
    compute_targets_at,
    effective_schedule,
    frozen_arm_digest_report,
    frozen_identity,
    parse_iso_utc,
    stamp_calendar,
)

AUDITS_SCHEMA = "v14i.oicyc.audits.v1"
PRODUCER_ROLE = "I-OICYC"

DAY_NS = 86_400_000_000_000

#: The OI staging authority (p_freeze_v14 ``staged_oi_axis_authority``).
OI_MANIFEST_PATH = (
    "research/control/v11_run/oi_staging_manifest.json"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tradeable_universe_symbols() -> tuple[str, ...]:
    """The 19 tradeable names: the frozen REQUIRED_SYMBOLS minus BTCUSDT."""
    return tuple(sorted(set(REQUIRED_SYMBOLS) - {BENCHMARK_SYMBOL}))


def verify_oi_staging(
    symbols: Optional[Sequence[str]] = None,
    *,
    root: str = OI_CONSOLIDATED_ROOT,
    manifest_path: str | Path = OI_MANIFEST_PATH,
) -> dict[str, Any]:
    """SHA-256-verify every staged OI parquet against the v11 manifest.

    FAILS CLOSED (raises ``RuntimeError``) on any missing file, hash
    mismatch or manifest gap -- a stale or altered parquet can never enter
    the family's evidence path.  Returns the verification payload.
    """
    wanted = [str(s) for s in (symbols or tradeable_universe_symbols())]
    manifest_file = Path(manifest_path)
    if not manifest_file.is_absolute():
        candidate = Path(__file__).resolve().parents[4]
        manifest_file = candidate / manifest_path
    manifest = json.loads(Path(manifest_file).read_text(encoding="utf-8"))
    if manifest.get("schema") != "v11_oi_staging_v1":
        raise RuntimeError(
            f"unexpected OI staging schema {manifest.get('schema')!r} "
            f"(expected v11_oi_staging_v1); refusing to load"
        )
    per_symbol: dict[str, dict[str, Any]] = {}
    mismatches: list[str] = []
    for sym in wanted:
        spec = (manifest.get("symbols") or {}).get(sym)
        if not spec:
            raise RuntimeError(f"manifest gap: symbol {sym} absent from the OI staging manifest")
        path = Path(root) / f"{sym}_oi.parquet"
        if not path.exists():
            raise RuntimeError(f"missing staged OI parquet for {sym}: {path}")
        digest = sha256_file(path)
        expected = str(spec["parquet_sha256"])
        ok = digest == expected
        if not ok:
            mismatches.append(sym)
        per_symbol[sym] = {
            "sha256": digest,
            "expected_sha256": expected,
            "match": ok,
            "days_present": int(spec.get("days_present", -1)),
        }
    if mismatches:
        raise RuntimeError(
            "OI staging SHA-256 mismatch for "
            f"{sorted(mismatches)}; refusing to load (fail-closed)"
        )
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "oi_staging_verification",
        "producer_role": PRODUCER_ROLE,
        "root": str(root),
        "manifest": str(manifest_file),
        "staging": "v11_oi_staging_v1",
        "symbols_verified": len(per_symbol),
        "sha_all_match": True,
        "per_symbol": per_symbol,
    }


def _parse_utc_naive(text: str) -> int:
    """``YYYY-MM-DD HH:MM:SS`` (Binance daily metrics, UTC) -> epoch ns."""
    dt = datetime.strptime(str(text).strip(), "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    return int(dt.timestamp()) * 1_000_000_000


def load_oi_by_symbol_verified(
    symbols: Optional[Sequence[str]] = None,
    *,
    root: str = OI_CONSOLIDATED_ROOT,
    manifest_path: str | Path = OI_MANIFEST_PATH,
) -> dict[str, tuple[tuple[int, float], ...]]:
    """SHA-verified staged daily OI rows per symbol: ``[(ts_ns, oi)]``.

    The ONLY sanctioned real-data OI load path for this family: every
    parquet is SHA-256-verified against the v11 staging manifest BEFORE
    reading (fail-closed), then parsed to strictly increasing
    ``(create_time -> epoch ns, sum_open_interest)`` rows with duplicate
    stamps refused.  Availability = the row's own stamp (read per row).
    """
    wanted = [str(s) for s in (symbols or tradeable_universe_symbols())]
    verify_oi_staging(wanted, root=root, manifest_path=manifest_path)
    out: dict[str, tuple[tuple[int, float], ...]] = {}
    for sym in wanted:
        table = pq.read_table(Path(root) / f"{sym}_oi.parquet")
        times = table.column("create_time").to_pylist()
        values = table.column("sum_open_interest").to_pylist()
        rows = sorted((_parse_utc_naive(t), float(v)) for t, v in zip(times, values))
        seen = [t for t, _ in rows]
        if len(set(seen)) != len(seen):
            raise RuntimeError(f"{sym}: duplicate OI timestamps after parse")
        out[sym] = tuple(rows)
    return out


def load_snapshot_data(
    *,
    oi_root: str = OI_CONSOLIDATED_ROOT,
    bars_root: Optional[str] = None,
    oi_manifest_path: str | Path = OI_MANIFEST_PATH,
    funding_bundle: str = "scan_2026",
    universe: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    """SHA-verified bundles for plugin construction (READ-ONLY).

    OI is the SHA-verified consolidated staging; bars are selected around
    the frozen schedule's instants (execution/valuation events only);
    marks/settlements and tick sizes come through the frozen V13/V12
    loaders.  No PnL, no scoring.
    """
    uni = tuple(sorted(str(s) for s in (universe or tradeable_universe_symbols())))
    feed_symbols = tuple(sorted(set(uni) | {BENCHMARK_SYMBOL}))
    oi = load_oi_by_symbol_verified(
        uni, root=oi_root, manifest_path=oi_manifest_path
    )
    instants = list(stamp_calendar())
    fold_ends = fold_end_instants()
    kwargs: dict[str, Any] = {}
    if bars_root is not None:
        kwargs["bars_root"] = str(bars_root)
    bars = load_bars_for_plugin(
        feed_symbols, instants + list(fold_ends), **kwargs
    )
    marks, settlements = load_marks_and_settlements(uni, bundle_label=funding_bundle)
    ticks = load_tick_sizes(set(uni) | {BENCHMARK_SYMBOL})
    return {
        "universe": uni,
        "oi": oi,
        "bars": bars,
        "marks": marks,
        "settlements": settlements,
        "tick_sizes": {str(k): float(v) for k, v in dict(ticks).items()},
    }


def fold_end_instants() -> list[int]:
    """The three fold-boundary instants (force-flat points, frozen windows)."""
    from research.v14.families.oicyc.strategy import fold_end_instants as _impl

    return _impl()


def build_plugins(
    *,
    data: Optional[dict[str, Any]] = None,
    oi_root: str = OI_CONSOLIDATED_ROOT,
    bars_root: Optional[str] = None,
    oi_manifest_path: str | Path = OI_MANIFEST_PATH,
    arms: Sequence[str] = ARM_IDS,
) -> dict[str, OicycPlugin]:
    """Audit-only plugin construction on the SHA-verified staged snapshot.

    The driver-side ``build(staged_root, arm_id)`` wiring mirrors this
    constructor exactly (explicit roots, SHA-verified OI, real tick
    sizes).  Nothing here computes PnL or scores.
    """
    if data is None:
        data = load_snapshot_data(
            oi_root=oi_root, bars_root=bars_root, oi_manifest_path=oi_manifest_path
        )
    out: dict[str, OicycPlugin] = {}
    for arm_id in arms:
        if arm_id not in ARM_IDS:
            raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
        out[str(arm_id)] = OicycPlugin(
            arm_id=str(arm_id),
            oi_by_symbol=data["oi"],
            bars_by_symbol=data["bars"],
            settlements_by_symbol=data["settlements"],
            tick_sizes=data["tick_sizes"],
        )
    return out


def evidence_identity() -> dict[str, Any]:
    """Frozen identity payloads + digest report + CONFIRMATORY metadata."""
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "evidence_identity",
        "producer_role": PRODUCER_ROLE,
        "family_id": FAMILY_ID,
        "arms": {
            arm_id: {
                "role": {"CYC-28D": "anchor", "CYC-14D": "neighbour", "CTL-OISHARE": "causal_negative_control"}[arm_id],
                "identity": frozen_identity(arm_id)._asdict()
                if hasattr(frozen_identity(arm_id), "_asdict")
                else dict(frozen_identity(arm_id).__dict__),
            }
            for arm_id in ARM_IDS
        },
        "digest_report": frozen_arm_digest_report(),
        "confirmatory": {
            "status": CONFIRMATORY,
            "disclosure": SECTION_1_1_DISCLOSURE,
        },
        "schedule": {
            "first_stamp": stamp_calendar()[0],
            "last_stamp": stamp_calendar()[-1],
            "scheduled": len(stamp_calendar()),
            "effective": len(effective_schedule(stamp_calendar())[0]),
            "purged_by_fold": {
                label: [iso(t) for t in stamps]
                for label, stamps in effective_schedule(stamp_calendar())[1].items()
            },
            "first_stamp_iso": FIRST_STAMP_ISO,
        },
        "no_pnl": True,
    }


def iso(ns: int) -> str:
    from research.v14.families.oicyc.strategy import iso_utc

    return iso_utc(int(ns))


def build_target_records(
    arm_id: str,
    *,
    data: dict[str, Any],
) -> dict[str, Any]:
    """The chained hysteresis target schedule of one arm (schedule-only).

    Replays the frozen weekly stamps over the SHA-verified staged OI and
    records per stamp: weights, longs/shorts, carried flags, eligibility
    and availability diagnostics.  NO PnL, no returns, no positions
    persisted beyond this payload.
    """
    if arm_id not in ARM_IDS:
        raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {ARM_IDS}")
    oi = data["oi"]
    universe = data.get("universe") or tradeable_universe_symbols()
    prev: dict[str, float] = {}
    records: list[dict[str, Any]] = []
    for stamp in stamp_calendar():
        payload = compute_targets_at(
            str(arm_id),
            oi_by_symbol=oi,
            stamp_ns=int(stamp),
            universe=universe,
            prev_book=prev,
        )
        records.append(
            {
                "decision_ns": int(stamp),
                "decision_iso": iso(int(stamp)),
                "arm_id": str(arm_id),
                "weights": [[sym, float(w)] for sym, w in payload["weights"]],
                "longs": [[sym, float(w)] for sym, w in payload["longs"]],
                "shorts": [[sym, float(w)] for sym, w in payload["shorts"]],
                "carried_forward": bool(payload["carried_forward"]),
                "reason_code": payload["reason_code"],
                "n_eligible": int(payload["diagnostics"]["n_eligible"]),
                "n_longs": int(payload["diagnostics"]["n_longs"]),
                "n_shorts": int(payload["diagnostics"]["n_shorts"]),
                "signal_availability_ratio": float(
                    payload["diagnostics"]["signal_availability_ratio"]
                ),
                "confirmatory_status": payload["confirmatory"]["status"],
            }
        )
        prev = {sym: float(w) for sym, w in payload["weights"] if abs(float(w)) > 0.0}
    return {
        "schema": AUDITS_SCHEMA,
        "artifact": "target_records",
        "producer_role": PRODUCER_ROLE,
        "arm_id": str(arm_id),
        "n_stamps": len(records),
        "records": records,
        "no_pnl": True,
    }


def canonical_sha256(payload: Any) -> str:
    """SHA-256 of the canonical JSON encoding (sorted keys, no whitespace)."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def first_stamp_ns() -> int:
    return int(parse_iso_utc(FIRST_STAMP_ISO))


__all__ = [
    "AUDITS_SCHEMA",
    "OI_MANIFEST_PATH",
    "PRODUCER_ROLE",
    "build_plugins",
    "build_target_records",
    "canonical_sha256",
    "evidence_identity",
    "first_stamp_ns",
    "fold_end_instants",
    "load_oi_by_symbol_verified",
    "load_snapshot_data",
    "sha256_file",
    "tradeable_universe_symbols",
    "verify_oi_staging",
]
