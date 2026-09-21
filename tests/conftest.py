"""Test scaffolding for the Quant Shadow Dashboard app (lane shv1-dashboard).

Fixtures are small copies built from the REAL PROSPECTIVE-SHADOW-V1
bytes (ledgers byte-exact; valuation marks sliced at complete-line
boundaries; synthetic heartbeats with controllable clocks). The real
runtime is never modified.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

LANE_ROOT = Path(__file__).resolve().parent.parent
if str(LANE_ROOT) not in sys.path:
    sys.path.insert(0, str(LANE_ROOT))

from dashboard_app.resolve import RuntimePaths, find_runtime  # noqa: E402
from dashboard_app.store import load_engine  # noqa: E402

FAMILIES = (
    "XSECT-FUND-CARRY-7D",
    "ILLIQ-AMIHUD-28D-W",
    "BASISLV-PREMFADE-28D",
)

# Marks files are ~1-2.5 MB; keep fixtures small. We slice the TAIL
# (most recent complete lines) so every family covers the latest
# local-midnight boundary. Ledgers stay byte-exact (full history) so
# the engine's per-event accounting identity validation still holds.
MARK_TAIL_LINES_PER_FAMILY = 400


@pytest.fixture(scope="session")
def real_runtime() -> RuntimePaths:
    try:
        return find_runtime()
    except RuntimeError as exc:  # pragma: no cover - machine-dependent
        pytest.skip(f"no PROSPECTIVE-SHADOW-V1 runtime on this machine: {exc}")


@pytest.fixture(scope="session")
def engine(real_runtime):
    return load_engine(real_runtime.worktree or real_runtime.runtime_root)


def _complete_tail_lines(path: Path, limit: int) -> list[str]:
    data = path.read_bytes()
    if not data.endswith(b"\n"):
        data = data[: data.rfind(b"\n") + 1]
    lines = data.decode("utf-8").splitlines()
    return lines[-limit:]


def _is_valid_mark(record: dict) -> bool:
    """A near-real valuation mark: seeds (CAPITAL_SEED_NO_MARK) and
    gap/fail-closed records are excluded — mark records carry
    status RUNNING/FLAT_OK + accounting_status OK."""
    return (
        record.get("record_type") != "CAPITAL_SEED_NO_MARK"
        and record.get("accounting_status") == "OK"
        and isinstance(record.get("equity"), (int, float))
        and isinstance(record.get("mark_timestamp_utc"), str)
        and record["mark_timestamp_utc"]
    )


@pytest.fixture()
def fixture_runtime(tmp_path, real_runtime) -> tuple[RuntimePaths, dict]:
    """A small honest copy of the real runtime in tmp_path."""
    ledgers = tmp_path / "ledgers"
    marks = tmp_path / "valuation_marks"
    runtime = tmp_path / "runtime"
    ledgers.mkdir()
    marks.mkdir()
    runtime.mkdir()

    marks_tail = {}
    for fam in FAMILIES:
        src_ledger = Path(real_runtime.ledgers_dir) / f"{fam}.jsonl"
        if src_ledger.is_file():
            (ledgers / f"{fam}.jsonl").write_bytes(src_ledger.read_bytes())
        src_marks = Path(real_runtime.valuation_dir) / f"{fam}.jsonl"
        lines = _complete_tail_lines(src_marks, MARK_TAIL_LINES_PER_FAMILY)
        (marks / f"{fam}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        marks_tail[fam] = lines

    last_ts = max(
        (
            rec["mark_timestamp_utc"]
            for lines in marks_tail.values()
            for line in lines
            if _is_valid_mark(rec := json.loads(line))
        ),
        default="2026-09-20T00:00:00Z",
    )

    def write_heartbeats(*, loop_utc, mark_loop_utc=None, last_error=None):
        (runtime / "heartbeat.json").write_text(
            json.dumps(
                {
                    "schema": "shv1_e_worker_heartbeat@1",
                    "pid": 999001,
                    "interval_seconds": 300.0,
                    "last_loop_utc": loop_utc,
                    "last_error": None,
                    "loop_count": 1,
                    "last_completed": {
                        fam: {
                            "accounting_status": "OK",
                            "data_status": "OK",
                            "risk_status": "OK",
                        }
                        for fam in FAMILIES
                    },
                    "next_decision_per_family": {},
                }
            ),
            encoding="utf-8",
        )
        (runtime / "valuation_heartbeat.json").write_text(
            json.dumps(
                {
                    "schema": "shv1_valuation_worker_heartbeat@1",
                    "worker_schema": "shv1_valuation_worker@1",
                    "pid": 999002,
                    "last_loop_utc": mark_loop_utc or loop_utc,
                    "last_error": last_error,
                    "loop_count": 1,
                    "marks_written": 0,
                    "next_mark_utc": loop_utc,
                    "runtime_root": str(tmp_path),
                    "shadow_start_utc": "2026-09-14T23:48:01Z",
                }
            ),
            encoding="utf-8",
        )

    paths = RuntimePaths(
        repo_root=None,
        worktree=None,
        runtime_root=str(tmp_path),
        source="test-fixture",
        identity_manifest=None,
    )
    return paths, {
        "write_heartbeats": write_heartbeats,
        "last_mark_ts": last_ts,
        "marks_tail": marks_tail,
        "ok_marks": lambda fam: [
            rec
            for rec in (json.loads(line) for line in marks_tail[fam])
            if _is_valid_mark(rec)
        ],
        "tmp": tmp_path,
    }
