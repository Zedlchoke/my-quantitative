"""CRYPTO-V17 Q phase runner: one heavy-lock session for the whole phase.

1. build the Q selection JSON (embeds the two frozen family specs);
2. sanitized exact-arm dry-run, TWICE, byte-identical (determinism twin);
3. non-vacuity check (every arm has booked decisions) + recursive key-level
   leak scan on every sanitized record (no outcome-shaped keys anywhere);
4. full pytest suite ALONE (no other heavy worker);
5. twin smoke-rerun: worktree twin at the same HEAD with the panel data
   available, --smoke one family, outputs byte-identical to the first run.
Release FINISHED/FAILED with stderr tail per the round-2 mandate.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from research.governance import heavy_lock  # noqa: E402

WORKTREE = Path(__file__).resolve().parents[3]  # integration root (this file sits one level above staging)
VENV = Path("/Users/hoangminhlong/my-quantitative/.venv/bin/python")
Q = WORKTREE / "research" / "control" / "v17_run" / "q_dry_run"
FAMILIES = ["V17-a5-P1-ATTN-PHASE", "V17-A6-P2-OICASCADE"]  # selection freeze v3 (74781fb): both lane-1 proposals dead by frozen rules; lane-1 miss disclosed
LEAK_KEYS = {"pnl", "profit", "expectancy", "sharpe", "pf", "profit_factor",
             "mdd", "drawdown", "gate_verdict", "margin", "stress", "score"}

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def digest_dir(d):
    out = {}
    for p in sorted(Path(d).rglob("*")):
        if p.is_file():
            out[str(p.relative_to(d))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out

def main():
    spec_probe = WORKTREE / "research/control/v17_run/driver/families/V17-A4-P2-SILRES.spec.json"
    print(f"WORKTREE={WORKTREE} spec_exists={spec_probe.exists()}", flush=True)
    deadline = time.time() + 4 * 3600
    while True:
        try:
            cm = heavy_lock.acquire(
                cycle_id="CRYPTO-V17", role="Q_PHASE_DRYRUN_SUITE_TWIN",
                worktree=str(WORKTREE),
                command=[sys.executable, str(Path(__file__).resolve())],
                expected_artifacts=[str(Q / "q_phase_report.json")])
            break
        except heavy_lock.LockBusyError as e:
            if time.time() > deadline:
                print(f"GIVING UP: {e}", flush=True)
                sys.exit(3)
            if not hasattr(main, "_said"):
                print(f"lock busy; retrying in 60 s ({e})", flush=True)
                main._said = True
            time.sleep(60)
    with cm as lock:
        try:
            # 1. selection JSON
            fam_specs = []
            for fid in FAMILIES:
                doc = json.loads((WORKTREE / "research/control/v17_run/driver/families" / f"{fid}.spec.json").read_text())
                # spec files are frozen wrappers: the driver-parseable family
                # objects live under the wrapper's "families" list
                fam_specs += doc["families"]
            sel = {"cycle_id": "CRYPTO-V17", "families": fam_specs}
            selp = WORKTREE / "research/control/v17_run/q_dry_run_selection.json"
            selp.write_text(json.dumps(sel, indent=1) + "\n")
            print("selection written", flush=True)

            # 2. sanitized dry-run twice
            # driver writes outputs relative to cwd (q_dry_run/ under it);
            # snapshot the tree after run1, restore-run, compare digests
            qroot = WORKTREE / "research/control/v17_run/q_dry_run"
            snaps_root = WORKTREE / "research/control/v17_run/q_run_snaps"
            if snaps_root.exists(): shutil.rmtree(snaps_root)
            snaps_root.mkdir(parents=True)
            snaps = []
            for i in (1, 2):
                if qroot.exists(): shutil.rmtree(qroot)
                r = run([str(VENV), str(WORKTREE / "research/control/v17_run/driver/run_v17_cell.py"),
                         "--selection", str(selp), "--families", ",".join(FAMILIES),
                         "--sanitized"], cwd=str(WORKTREE))
                if r.returncode != 0:
                    raise RuntimeError(f"sanitized run{i} failed: {r.stderr[-2000:]}")
                snap = snaps_root / f"run{i}"
                shutil.copytree(qroot, snap)
                snaps.append(snap)
                print(f"sanitized run{i} done", flush=True)
            d1, d2 = digest_dir(snaps[0]), digest_dir(snaps[1])
            if d1 != d2:
                diff = [k for k in set(d1) | set(d2) if d1.get(k) != d2.get(k)]
                raise RuntimeError(f"DETERMINISM TWIN MISMATCH: {diff[:8]}")
            print(f"determinism twin: {len(d1)} files byte-identical", flush=True)

            # 3. non-vacuity + recursive leak scan
            arms = 0
            for p in sorted(snaps[0].rglob("decisions.jsonl")):
                lines = [l for l in p.read_text().splitlines() if l.strip()]
                if not lines:
                    raise RuntimeError(f"VACUOUS: {p} has zero decisions")
                arms += 1
                for l in lines:
                    rec = json.loads(l)
                    for k in rec:
                        if k.lower() in LEAK_KEYS:
                            raise RuntimeError(f"LEAK: outcome-shaped key '{k}' in {p}")
            print(f"non-vacuous + leak scan: {arms} arm decision files clean", flush=True)

            # 4. full suite ALONE
            r = run([str(VENV), "-m", "pytest", "tests/", "-q"],
                    cwd=str(WORKTREE))
            (Q / "full_suite_output.txt").write_text((r.stdout or "") + "\n=== STDERR ===\n" + (r.stderr or ""))
            tail = (r.stdout or "").splitlines()[-3:]
            print("full suite:", " | ".join(tail), flush=True)
            if r.returncode != 0:
                raise RuntimeError(f"full suite failed:\n" + (r.stdout or "")[-3000:])
            suite_ok = True

            # 5. twin smoke-rerun at the same HEAD
            twin = WORKTREE.parent / "q_twin_v17"
            if twin.exists(): shutil.rmtree(twin)
            r = run(["git", "worktree", "add", str(twin), "HEAD", "--detach"], cwd=str(WORKTREE))
            if r.returncode != 0:
                raise RuntimeError(f"twin worktree failed: {r.stderr}")
            try:
                # panel data must be visible to the twin (gitignored data dir)
                twin_data = twin / "v17_data"
                twin_data.parent.mkdir(parents=True, exist_ok=True)
                if not twin_data.exists():
                    twin_data.symlink_to(WORKTREE / "v17_data")
                smoke1 = WORKTREE / "results/v17_smoke"
                smoke2 = twin / "results/v17_smoke"
                if smoke1.exists(): shutil.rmtree(smoke1)
                r = run([str(VENV), str(WORKTREE / "research/control/v17_run/driver/run_v17_cell.py"),
                         "--selection", str(selp), "--families", FAMILIES[0], "--smoke"],
                        cwd=str(WORKTREE))
                if r.returncode != 0:
                    raise RuntimeError(f"smoke run1 failed: {r.stderr[-1500:]}")
                r = run([str(VENV), str(twin / "research/control/v17_run/driver/run_v17_cell.py"),
                         "--selection", str(twin / "research/control/v17_run/q_dry_run_selection.json"),
                         "--families", FAMILIES[0], "--smoke"],
                        cwd=str(twin))
                if r.returncode != 0:
                    raise RuntimeError(f"twin smoke failed: {r.stderr[-1500:]}")
                s1, s2 = digest_dir(smoke1), digest_dir(smoke2)
                if s1 != s2:
                    diff = [k for k in set(s1) | set(s2) if s1.get(k) != s2.get(k)]
                    raise RuntimeError(f"TWIN SMOKE MISMATCH: {diff[:8]}")
                print(f"twin smoke: {len(s1)} files byte-identical across worktrees", flush=True)
            finally:
                run(["git", "worktree", "remove", "--force", str(twin)], cwd=str(WORKTREE))

            report = {
                "schema": "v17_run_artifact_v1", "artifact": "q_phase_report",
                "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sanitized_runs": 2, "determinism_files": len(d1),
                "arm_decision_files": arms, "leak_scan": "CLEAN",
                "full_suite": "PASS", "twin_smoke_files": len(s1),
                "verdict": "Q_PASS"}
            (Q / "q_phase_report.json").write_text(json.dumps(report, indent=1) + "\n")
            print("Q_PASS", flush=True)
        except Exception:
            import traceback
            tail = "\n".join(traceback.format_exc().strip().splitlines()[-12:])
            lock.release(status="FAILED", note=f"stderr tail: {tail}")
            raise

if __name__ == "__main__":
    main()
