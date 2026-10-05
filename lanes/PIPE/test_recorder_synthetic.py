"""test_recorder_synthetic.py — PIPE lane, cycle NFL-WINPROB-NG-SCORED-V1.

pytest wrapper around the recorder's self-contained SYNTHETIC test modes. Adds
continuous-test coverage WITHOUT touching the existing suites (this file never
modifies lanes/T_SELECT/**, lanes/S_SYNTH/**, lanes/F_FREEZE/**, or the ported
ledger tool).

  - test_recorder_selftest: runs `record_batch.py --mode selftest` (hand-computed
    fixtures: margin arithmetic, kickoff-UTC canonicalization, state-carry Elo,
    identical-kickoff exclusion, future-score abort, p-format guard, fresh-pull
    guard, combined-vs-warmup equivalence, arm-digest law).
  - test_recorder_e2e_synth: runs `record_batch.py --mode e2e-synth` (nominal
    synthetic week -> sandbox ledger -> chain validation; margin-violation
    refusal; future-score abort; double-run byte-identical determinism).
  - test_frozen_bytes_unchanged: the frozen inputs the recorder imports still
    carry their freeze sha256s.

Everything the e2e writes goes to the lane-owned sandbox
~/.my-quantitative-data/nfl-ng-scored-v1/recorder_sandbox/e2e/** (SYNTH_ ids,
2027+ kickoffs). No real-game probability is ever computed: the real warmup
emits aggregate counts only, and only SYNTH_-prefixed games reach the predict
path (enforced inside the recorder by _assert_synth_only).

Run:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
      lanes/PIPE/test_recorder_synthetic.py -v
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parent.parent.parent
RECORDER = WORKTREE / "research" / "control" / "NFL-WINPROB-NG-SCORED-V1" / "recorder"
RECORD_BATCH = RECORDER / "record_batch.py"
INTERP = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"

FROZEN_SHA = {
    WORKTREE / "lanes" / "T_SELECT" / "arms.py":
        "19dddd3ff2bec808e549981473e0523b4178cfd8c7c0db7c08b7e41a86d7d3e8",
    WORKTREE / "research" / "control" / "NFL-WINPROB-NG-SCORED-V1" / "ledger" / "nfl_ng_ledger.py":
        "6fb0a1d41b347c16162742ee2591090d576af7633fd1d86b641d444156a1219c",
}


def _run_mode(mode: str) -> str:
    proc = subprocess.run(
        [INTERP, str(RECORD_BATCH), "--mode", mode],
        cwd=str(WORKTREE), capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode == 0, f"{mode} failed (rc={proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
    return proc.stdout + proc.stderr


def test_frozen_bytes_unchanged():
    import hashlib

    for path, sha in FROZEN_SHA.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha


def test_recorder_selftest():
    out = _run_mode("selftest")
    assert "SELFTEST OK" in out
    assert '"arm_digest_law": "PASS"' in out
    assert '"margin_arithmetic"' in out and '"kickoff_canonicalization"' in out
    assert '"state_carry_hand_elo"' in out and '"identical_kickoff_exclusion"' in out
    assert '"future_score_abort"' in out and '"p_format_guard"' in out


def test_recorder_e2e_synth():
    out = _run_mode("e2e-synth")
    assert "E2E-SYNTH OK" in out
    assert "BYTE-IDENTICAL (ledger + genesis sidecar)" in out
    assert '"refused": true' in out          # margin-violation scenario
    assert '"nothing_written": true' in out  # refusal + abort leave nothing
    assert '"aborted": true' in out          # future-score scenario
