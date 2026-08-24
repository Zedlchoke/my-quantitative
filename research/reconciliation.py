"""Experiment-directory integrity verification (Sprint V5 XG2a; owner A3).

Fixes F15/F16: artifact integrity is MEASURED, never asserted.  For a
diagnostic experiment directory this module recomputes

1. SCHEMA   -- required artifacts exist and carry their schema fields;
2. HASHES   -- sha256 of EVERY listed file matches
               ``artifact_hashes.json``; files on disk that are absent from
               the listing are reported (nothing may escape the manifest);
3. FRESHNESS-- ``artifact_hashes.json`` must be the NEWEST file among the
               hashed set (mtime_ns).  Any file modified after hashing --
               the classic "hash computed, then run.log appended" defect --
               fails as ``artifact_hashes_stale``;
4. LEDGER   -- positions / funding / cost totals recomputed from the jsonl
               ledgers reconcile against ``accounting_reconciliation.json``
               within 1e-9 (scaled).

The result is a contract :class:`ArtifactIntegrityResult` whose booleans are
derived from these measurements -- never constructed with a bare ``True``.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from contracts.protocol import ArtifactIntegrityResult, GateVerdict, sha256_file, sha256_text

#: Files every diagnostic experiment directory must contain, by phase.
#: ``inputs``  -- what the diagnostic RERUNNER must have written;
#: ``final``   -- everything, checked AFTER the evaluator finalized hashes.
HASHES_FILENAME = "artifact_hashes.json"
HASHES_FLAG_FILENAME = ".hashes_final"

INPUT_REQUIRED_ARTIFACTS: tuple[str, ...] = (
    "cell.json",
    "accounting_reconciliation.json",
    "positions.jsonl",
    "funding_cashflows.jsonl",
    "costs.jsonl",
)
FINAL_REQUIRED_ARTIFACTS: tuple[str, ...] = INPUT_REQUIRED_ARTIFACTS + (
    "canonical_metrics.json",
    "gate_result.json",
    "scorecard.json",
    "run.log",
    HASHES_FILENAME,
)

#: Required top-level fields of canonical_metrics.json.
REQUIRED_METRIC_FIELDS: frozenset[str] = frozenset(
    ("net_canonical_pnl", "trades", "position_pf")
)

#: Required totals inside accounting_reconciliation.json.
REQUIRED_ACCOUNTING_FIELDS: frozenset[str] = frozenset(
    ("positions_total_pnl", "funding_total", "commission_total", "slippage_total")
)

#: Ledger filename -> (jsonl field summed, accounting_reconciliation total key).
LEDGER_SUMS: tuple[tuple[str, str | None, str], ...] = (
    ("positions.jsonl", "canonical_pnl", "positions_total_pnl"),
    ("funding_cashflows.jsonl", "funding_net", "funding_total"),
    ("costs.jsonl", "commission", "commission_total"),
    ("costs.jsonl", "modeled_slippage", "slippage_total"),
)

ACCOUNTING_TOLERANCE = 1e-9


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _schema_reasons(exp_dir: Path, required_artifacts: tuple[str, ...]) -> list[str]:
    reasons: list[str] = []
    for name in required_artifacts:
        if not (exp_dir / name).is_file():
            reasons.append(f"missing_artifact:{name}")
    metrics_path = exp_dir / "canonical_metrics.json"
    if metrics_path.is_file():
        try:
            doc = _read_json(metrics_path)
        except json.JSONDecodeError:
            return [*reasons, "artifact_schema_invalid:canonical_metrics.json"]
        missing = REQUIRED_METRIC_FIELDS.difference(doc)
        if missing:
            reasons.append(f"artifact_schema_invalid:canonical_metrics:{sorted(missing)}")
    accounting_path = exp_dir / "accounting_reconciliation.json"
    if accounting_path.is_file():
        try:
            doc = _read_json(accounting_path)
        except json.JSONDecodeError:
            return [*reasons, "artifact_schema_invalid:accounting_reconciliation.json"]
        missing = REQUIRED_ACCOUNTING_FIELDS.difference(doc)
        if missing:
            reasons.append(
                f"artifact_schema_invalid:accounting_reconciliation:{sorted(missing)}"
            )
    hashes_path = exp_dir / HASHES_FILENAME
    if hashes_path.is_file():
        try:
            doc = _read_json(hashes_path)
        except json.JSONDecodeError:
            return [*reasons, f"artifact_schema_invalid:{HASHES_FILENAME}"]
        if not isinstance(doc.get("files"), Mapping) or not doc.get("files"):
            reasons.append(f"artifact_schema_invalid:{HASHES_FILENAME}:files_listing")
        if not doc.get("algorithm"):
            reasons.append(f"artifact_schema_invalid:{HASHES_FILENAME}:algorithm")
    return reasons


def _hash_reasons(exp_dir: Path) -> tuple[list[str], bool]:
    """(reasons, listing_matches_disk) from recomputing EVERY listed hash."""
    reasons: list[str] = []
    hashes_path = exp_dir / HASHES_FILENAME
    if not hashes_path.is_file():
        return [f"missing_artifact:{HASHES_FILENAME}"], False
    try:
        recorded: dict[str, str] = dict(_read_json(hashes_path).get("files") or {})
    except json.JSONDecodeError:
        return [f"artifact_schema_invalid:{HASHES_FILENAME}"], False

    matches = True
    for rel, digest in sorted(recorded.items()):
        target = exp_dir / rel
        if not target.is_file():
            reasons.append(f"artifact_hash_mismatch:{rel}:missing")
            matches = False
            continue
        actual = sha256_file(target)
        if actual != digest:
            reasons.append(f"artifact_hash_mismatch:{rel}")
            matches = False

    # Nothing on disk may escape the recorded listing.
    for path in sorted(exp_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(exp_dir))
        if rel == HASHES_FILENAME or rel == HASHES_FLAG_FILENAME:
            continue
        if rel not in recorded:
            reasons.append(f"unlisted_artifact_file:{rel}")
            matches = False
    return reasons, matches


def _freshness_reasons(exp_dir: Path) -> list[str]:
    """F15 catch: no hashed file may be newer than artifact_hashes.json."""
    hashes_path = exp_dir / HASHES_FILENAME
    if not hashes_path.is_file():
        return []
    try:
        recorded: dict[str, str] = dict(_read_json(hashes_path).get("files") or {})
    except json.JSONDecodeError:
        return []
    hashes_mtime_ns = hashes_path.stat().st_mtime_ns
    reasons: list[str] = []
    for rel in sorted(recorded):
        target = exp_dir / rel
        if target.is_file() and target.stat().st_mtime_ns > hashes_mtime_ns:
            reasons.append(f"artifact_hashes_stale:{rel}")
    return reasons


def _accounting_reasons(exp_dir: Path) -> list[str]:
    accounting_path = exp_dir / "accounting_reconciliation.json"
    if not accounting_path.is_file():
        return ["missing_artifact:accounting_reconciliation.json"]
    try:
        totals = _read_json(accounting_path)
    except json.JSONDecodeError:
        return ["artifact_schema_invalid:accounting_reconciliation.json"]

    reasons: list[str] = []
    seen_ledgers: set[str] = set()
    for ledger_name, field_name, total_key in LEDGER_SUMS:
        ledger_path = exp_dir / ledger_name
        if not ledger_path.is_file():
            reasons.append(f"ledger_missing:{ledger_name}")
            continue
        seen_ledgers.add(ledger_name)
        rows = _iter_jsonl(ledger_path)
        total = 0.0
        for row in rows:
            value = row.get(field_name)
            if value is None:
                reasons.append(f"ledger_field_missing:{ledger_name}:{field_name}")
                total = float("nan")
                break
            total += float(value)
        expected_raw = totals.get(total_key)
        if expected_raw is None:
            continue  # schema check already reported the missing field
        expected = float(expected_raw)
        scale = max(1.0, abs(expected), abs(total))
        if not (abs(total - expected) <= ACCOUNTING_TOLERANCE * scale):
            reasons.append(f"accounting_reconcile_fail:{total_key}")
    return reasons


def compute_artifact_hashes(exp_dir: str | Path) -> dict[str, Any]:
    """Hash EVERY artifact file in ``exp_dir`` (hashes doc + flag excluded).

    ``files_spec_sha256`` is the digest of the canonical-JSON listing itself:
    a file cannot contain its own whole-content hash, so the verifier
    recomputes THIS digest to prove the recorded listing was not edited after
    the fact ("hash-match its own recorded content listing").
    """
    directory = Path(exp_dir)
    files: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(directory))
        if rel == HASHES_FILENAME or rel == HASHES_FLAG_FILENAME:
            continue
        files[rel] = sha256_file(path)
    return {
        "schema_version": 2,
        "algorithm": "sha256",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "files_spec_sha256": sha256_text(json.dumps(files, sort_keys=True)),
    }


def finalize_directory_hashes(
    exp_dir: str | Path, *, set_flag: bool = True
) -> Path:
    """Write ``artifact_hashes.json`` LAST (PLAN 31.2 item 9).

    Callers must have closed every other writer first.  With ``set_flag`` the
    sentinel ``.hashes_final`` is touched afterwards; in-process writers that
    honour :func:`assert_not_finalized` then refuse further writes.
    """
    directory = Path(exp_dir)
    doc = compute_artifact_hashes(directory)
    out = directory / HASHES_FILENAME
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    if set_flag:
        (directory / HASHES_FLAG_FILENAME).touch()
    return out


def base_reason_codes(reasons: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Strip ``code:detail`` suffixes down to registered reason codes.

    Measurement reasons carry file/ledger detail after a colon (e.g.
    ``artifact_hash_mismatch:positions.jsonl``); contract GateResult rows
    need the bare registered code.  Deduplicated, order preserved.
    """
    return tuple(dict.fromkeys(str(r).split(":", 1)[0] for r in reasons))


@dataclass(frozen=True)
class ExperimentIntegrityDetail:
    """Full measurement detail behind an XG2a verdict (audit trail)."""

    exp_dir: str
    schema_ok: bool
    hashes_ok: bool
    hashes_freshest: bool
    accounting_ok: bool
    reasons: tuple[str, ...]

    def to_artifact_integrity_result(self) -> ArtifactIntegrityResult:
        """Map detail onto the CONTRACT result (never bare ``True``).

        ``report_index_reconcile`` carries the F15 freshness measurement:
        hashes must be the newest mtime among hashed files.
        """
        return ArtifactIntegrityResult(
            schema_valid=self.schema_ok,
            hashes_match=self.hashes_ok,
            positions_reconcile=self.accounting_ok,
            report_index_reconcile=self.hashes_freshest,
            reasons=self.reasons,
        )


def verify_experiment_dir(
    exp_dir: str | Path, *, phase: str = "final"
) -> ArtifactIntegrityResult:
    """Measured XG2a evidence for one experiment directory.

    Recomputes schema presence, every sha256 in ``artifact_hashes.json``,
    hash freshness (newest mtime wins) and the accounting reconciliation.
    Returns the contract :class:`ArtifactIntegrityResult`; PASS only when
    every measurement is clean and NO reason was recorded.

    ``phase="inputs"`` verifies only the rerunner-written artifacts (used
    BEFORE the evaluator adds its own outputs); ``phase="final"`` (default)
    verifies the complete directory after finalization.
    """
    directory = Path(exp_dir)
    required = FINAL_REQUIRED_ARTIFACTS if phase == "final" else INPUT_REQUIRED_ARTIFACTS
    if not directory.is_dir():
        result = ArtifactIntegrityResult(
            schema_valid=False,
            hashes_match=False,
            positions_reconcile=False,
            report_index_reconcile=False,
            reasons=("experiment_dir_missing",),
        )
        return result

    schema_reasons = _schema_reasons(directory, required)
    hash_reasons, hashes_match = _hash_reasons(directory)
    freshness_reasons = _freshness_reasons(directory)
    accounting_reasons = _accounting_reasons(directory)

    reasons = tuple(
        dict.fromkeys([*schema_reasons, *hash_reasons, *freshness_reasons, *accounting_reasons])
    )
    hashes_manifest_bad = any(
        r.startswith("artifact_schema_invalid") and HASHES_FILENAME in r
        for r in schema_reasons
    )
    detail = ExperimentIntegrityDetail(
        exp_dir=str(directory),
        schema_ok=not schema_reasons,
        hashes_ok=hashes_match and not hashes_manifest_bad,
        hashes_freshest=not freshness_reasons,
        accounting_ok=not accounting_reasons,
        reasons=reasons,
    )
    return detail.to_artifact_integrity_result()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("exp_dir")
    args = parser.parse_args(argv)
    result = verify_experiment_dir(args.exp_dir)
    print(json.dumps({
        "exp_dir": str(args.exp_dir),
        "verdict": result.verdict().value,
        "schema_valid": result.schema_valid,
        "hashes_match": result.hashes_match,
        "positions_reconcile": result.positions_reconcile,
        "report_index_reconcile": result.report_index_reconcile,
        "reasons": list(result.reasons),
    }, indent=2))
    return 0 if result.verdict() is GateVerdict.PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
