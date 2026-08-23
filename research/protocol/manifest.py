"""Experiment manifest construction, ID generation and YAML persistence.

IDs are ``EXP-YYYYMMDD-NNNN`` where ``NNNN`` comes from a monotonic counter
file (never decreases, even across days) at ``results/registry/counter.txt``.
``random_seed`` is the only nullable manifest field; when it is null a reason
code ``seed_unavailable`` is recorded alongside it in the YAML payload under
``random_seed_reason``.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from contracts.protocol import ManifestSpec, MetricValue, require_reason

DEFAULT_REGISTRY_DIR = Path("results") / "registry"
COUNTER_FILENAME = "counter.txt"
SEED_REASON = "seed_unavailable"


def build_manifest(**kwargs: Any) -> ManifestSpec:
    """Validate kwargs against :class:`contracts.protocol.ManifestSpec`.

    Raises ``ValueError`` with reason code ``manifest_missing_field`` and the
    sorted missing field names when any required field is absent/None.
    ``random_seed`` may be None (recorded with reason ``seed_unavailable``).
    """
    missing = sorted(
        name
        for name in ManifestSpec.REQUIRED_FIELDS
        if kwargs.get(name) is None and name not in ManifestSpec.NULLABLE_FIELDS
    )
    unknown = sorted(set(kwargs) - set(ManifestSpec.REQUIRED_FIELDS))
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"{require_reason('manifest_missing_field')}: {missing}")
        if unknown:
            parts.append(f"unknown fields: {unknown}")
        raise ValueError("; ".join(parts))
    return ManifestSpec(**kwargs)


def next_experiment_id(registry_dir: str | Path | None = None) -> str:
    """Return a new monotonic ``EXP-YYYYMMDD-NNNN`` identifier.

    The counter file is read, incremented and atomically replaced so repeated
    calls never reuse an ordinal.  The date component is the current UTC date;
    the ordinal is global and strictly increasing.
    """
    directory = Path(registry_dir) if registry_dir is not None else DEFAULT_REGISTRY_DIR
    directory.mkdir(parents=True, exist_ok=True)
    counter_path = directory / COUNTER_FILENAME
    current = 0
    if counter_path.exists():
        text = counter_path.read_text(encoding="utf-8").strip()
        if text:
            current = int(text)
    nxt = current + 1
    tmp_path = counter_path.with_suffix(".txt.tmp")
    tmp_path.write_text(str(nxt), encoding="utf-8")
    os.replace(tmp_path, counter_path)
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"EXP-{today}-{nxt:04d}"


def manifest_seed_reason(manifest: ManifestSpec) -> str | None:
    """Return the recorded seed reason code when ``random_seed`` is null."""
    if manifest.random_seed is None:
        return require_reason(SEED_REASON)
    return None


def write_manifest(manifest: ManifestSpec, path: str | Path) -> Path:
    """Dump the manifest to YAML via ``yaml.safe_dump`` (types preserved).

    When ``random_seed`` is null a sibling key ``random_seed_reason`` records
    the ``seed_unavailable`` reason code alongside it.
    """
    payload: dict[str, Any] = manifest.to_dict()
    seed_reason = manifest_seed_reason(manifest)
    if seed_reason is not None:
        payload["random_seed_reason"] = seed_reason
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(payload, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return target


def read_manifest(path: str | Path) -> ManifestSpec:
    """Load a manifest from YAML via ``yaml.safe_load`` and re-validate.

    Unknown extra keys other than ``random_seed_reason`` are rejected.
    """
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"manifest payload must be a mapping: {path}")
    allowed = set(ManifestSpec.REQUIRED_FIELDS) | {"random_seed_reason"}
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(f"manifest has unknown fields: {unknown}")
    missing = sorted(
        name
        for name in ManifestSpec.REQUIRED_FIELDS
        if data.get(name) is None and name not in ManifestSpec.NULLABLE_FIELDS
    )
    if missing:
        raise ValueError(f"{require_reason('manifest_missing_field')}: {missing}")
    seed_reason = data.get("random_seed_reason")
    if data.get("random_seed") is None:
        if seed_reason != require_reason(SEED_REASON):
            raise ValueError("null random_seed requires random_seed_reason=seed_unavailable")
    elif seed_reason is not None:
        raise ValueError("random_seed_reason only allowed when random_seed is null")
    fields = {name: data[name] for name in ManifestSpec.REQUIRED_FIELDS}
    manifest = ManifestSpec(**fields)
    problems = manifest.validate()
    if problems:
        raise ValueError(f"manifest invalid: {problems}")
    return manifest


def metric_or_missing(value: float | None, reason: str) -> MetricValue:
    """Small helper for callers building MetricValues from raw floats."""
    return MetricValue.known(value) if value is not None else MetricValue.missing(reason)
