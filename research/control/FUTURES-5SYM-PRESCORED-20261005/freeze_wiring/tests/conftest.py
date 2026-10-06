"""conftest — sandbox paths, real-surface snapshot guard, lock-discipline log.

Isolation law (mirrors exec/test_runner_v2 T16): every lock, ledger,
registry, GO, authority, fixture and output path lives under pytest tmp dirs;
the REAL governance dir, the real CYCLE_REGISTRY.json are never written.
A session-scoped snapshot (content sha + size) of the real surfaces EXCEPT
the canonical heavy_runtime contents (they belong to other cycles' lock
lifecycles — the same disclosed exclusion the exec suite uses) is asserted
byte-identical after the whole suite (test_isolation.py).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

FREEZE_WIRING = Path(__file__).resolve().parents[1]
WIRING = FREEZE_WIRING / "wiring"
CYCLE_DIR = FREEZE_WIRING.parent
DISPATCH = CYCLE_DIR / "dispatch"
REAL_GOV = Path("/Users/hoangminhlong/.my-quantitative-governance")
REAL_REGISTRY = Path("/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json")
PY = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"
RESEARCHCTL = Path("/Users/hoangminhlong/my-quantitative/research/researchctl.py")
EPOCH = "2026-10-05T00:00:00Z"

for p in (str(FREEZE_WIRING), str(WIRING)):
    if p not in sys.path:
        sys.path.insert(0, p)

LOCK_LOG = FREEZE_WIRING / "tests" / "LOCKS_LOG.jsonl"


def sha256_path(p) -> str | None:
    p = Path(p)
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def record_lock_line(stage: str) -> dict:
    """locks inspect (read-only) + append a summary line to the lane log."""
    proc = subprocess.run([PY, str(RESEARCHCTL), "locks", "inspect"],
                          capture_output=True, text=True, timeout=60)
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        report = {"verdict": "UNPARSEABLE", "exit_code": proc.returncode}
    line = {"stage": stage, "verdict": report.get("verdict"),
            "exit_code": proc.returncode}
    try:
        LOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOCK_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, sort_keys=True) + "\n")
    except OSError:
        pass
    return line


def real_surface_snapshot() -> dict:
    """sha256+size for every file under the real governance dir EXCEPT
    heavy_runtime/ contents (canonical lock lifecycle of other cycles —
    disclosed exclusion, same as the exec suite), plus the real registry."""
    out = {}
    if REAL_GOV.is_dir():
        for p in sorted(REAL_GOV.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(REAL_GOV)
            if rel.parts[0] == "heavy_runtime":
                continue
            out[str(rel)] = sha256_path(p)
    out["__real_registry__"] = sha256_path(REAL_REGISTRY)
    return out


@pytest.fixture(scope="session")
def real_surface_before():
    return real_surface_snapshot()


@pytest.fixture(scope="session", autouse=True)
def lock_discipline():
    yield
    # lane-end locks line (start line is recorded by the first test module)
    record_lock_line("suite-end")


# ------------------------------------------------- freeze-builder scaffolding

GATE_FILES = {
    "d9": ("d9.json", {"schema": "d9_ratification@1",
                       "decision": "ADOPT-D9-OptionA",
                       "typed_by_owner": True, "ruling_ref": "sandbox-fake"}),
    "pb2": ("pb2.json", {"schema": "pb2_lift@1", "typed_by_owner": True,
                         "lift": "PB2-HOLD-LIFTED"}),
    "pb3": ("pb3.json", {"schema": "pb3_lift@1", "typed_by_owner": True,
                         "lift": "PB3-PARK-LIFTED"}),
    "d8": ("d8.json", {"schema": "d8_ratification@1",
                       "decision": "ADOPT-D8-OptionA",
                       "typed_by_owner": True}),
    "six_je_ceiling": ("6j_ceiling.json",
                       {"schema": "6j_ceiling@1", "option": "J-A",
                        "clock_shadow_reading": "a", "typed_by_owner": True}),
    "ceiling": ("ceiling.json", {"schema": "ceiling@1", "option": "owner-A",
                                 "ceiling": 22, "typed_by_owner": True,
                                 "identity_table": {"name": "sandbox-table",
                                                    "sha256": "0" * 64}}),
}


def write_gate_artifacts(tmp: Path, names, overrides=None) -> dict[str, str]:
    overrides = overrides or {}
    out = {}
    for name in names:
        fname, payload = GATE_FILES[name]
        payload = json.loads(json.dumps(payload))
        payload.update(overrides.get(name, {}))
        # keep the identity-table binding sha consistent with the real table
        if name == "ceiling" and "identity_table" not in (overrides.get(name) or {}):
            it_sha = sha256_path(tmp / "inputs" / "sandbox_identity_table.json") \
                or ("0" * 64)
            payload["identity_table"] = {
                "name": "sandbox_identity_table.json", "sha256": it_sha}
        p = tmp / fname
        p.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                     encoding="utf-8")
        out[name] = str(p)
    return out


INPUT_ROLES = [
    ("panel", "sandbox_panel.parquet", b"SYNTHETIC-PANEL-BYTES"),
    ("chain", "sandbox_chain.json", b'{"schema":"sandbox_chain@1","rolls":[]}'),
    ("calendar", "sandbox_calendar.json",
     b'{"schema":"sandbox_calendar@1","exclusions":[]}'),
    ("exclusion_table", "sandbox_exclusions.json",
     b'{"schema":"sandbox_exclusion_calendar@1","rows":[]}'),
    ("cost_manifest", "sandbox_costs.json", b'{"tier":"S2","modeled":true}'),
    ("identity_table", "sandbox_identity_table.json",
     b'{"schema":"sandbox_identity_table@1","identities":[]}'),
    ("spec_packet", "sandbox_spec.json", b'{"schema":"sandbox_spec@1"}'),
]


def write_freeze_input_manifest(tmp: Path, symbol: str,
                                params=None) -> str:
    inputs_dir = tmp / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    inputs = []
    for role, fname, payload in INPUT_ROLES:
        p = inputs_dir / fname
        p.write_bytes(payload)
        inputs.append({"role": role, "path": str(p),
                       "sha256": hashlib.sha256(payload).hexdigest(),
                       "bytes": len(payload)})
    manifest = {"schema": "futures_5sym_prescored/freeze_input_manifest@1",
                "cycle_id": "FUTURES-5SYM-PRESCORED-20261005",
                "symbol": symbol,
                "provenance": "SYNTHETIC-SANDBOX",
                "inputs": inputs,
                "params": params or {"k": 5, "sandbox": True}}
    mp = tmp / "freeze_input_manifest.json"
    mp.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n",
                  encoding="utf-8")
    return str(mp)


def run_builder(tmp: Path, symbol: str, manifest: str, gates: dict,
                label: str = "freeze1") -> tuple[int, dict, Path]:
    out_dir = tmp / f"bundle_{label}"
    status_out = tmp / f"FREEZE_FINAL_STATUS.{label}.json"
    argv = [PY, str(FREEZE_WIRING / "freeze_builder.py"),
            "--symbol", symbol, "--input-manifest", manifest,
            "--epoch", EPOCH, "--out-dir", str(out_dir),
            "--final-status-out", str(status_out), "--run-label", label]
    for name, path in gates.items():
        argv += ["--gate-artifact", f"{name}={path}"]
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    status = json.loads(status_out.read_text(encoding="utf-8")) \
        if status_out.is_file() else None
    return proc.returncode, status, out_dir
