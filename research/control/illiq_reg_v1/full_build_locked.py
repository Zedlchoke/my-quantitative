import subprocess, sys
from pathlib import Path
R = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(R))
from research.governance import heavy_lock
G = Path("/Users/hoangminhlong/my-quantitative/.worktrees/illiq-reg-v1/integration/research/control/illiq_reg_v1")
handle = heavy_lock.acquire(cycle_id="ILLIQ-REG-V1", role="gate-series-build",
                            worktree=str(R / ".worktrees/illiq-reg-v1/integration"),
                            command=[str(R / ".venv/bin/python"), str(G / "full_build_locked.py")],
                            expected_artifacts=[str(G / "gate_series")])
try:
    r = subprocess.run([str(R / ".venv/bin/python"), str(G / "gate_series_build.py"), "--full-build"],
                       cwd=str(G.parent), capture_output=True, text=True)
    (G / "full_build.log").write_text(r.stdout + "\n" + r.stderr)
    print(r.stdout[-2000:]); print("rc:", r.returncode)
    sys.exit(r.returncode)
finally:
    handle.release()
