"""SHV1 sec7.6 doctor - read-only consistency diagnostics for the control plane.

Doctor LABELS stale and contradictory state; it NEVER repairs it (sec7.5).
Detections (all read-only):
 1. STALE_ROUTER_ENTRY / ROUTER_GAP   - committed projection vs canonical registry
 2. BRANCH_MISMATCH / HEAD_MISMATCH   - worktree vs registry authority
 3. STATE_MISSING / CONTROL_STATE_DRIFT - legacy state files
 4. STALE_HEARTBEAT                    - non-terminal cycles, >24h
 5. LIVE_WORKER_UNREPRESENTED          - repo python workers vs registry workers
 6. LOCK_OWNER_DEAD                    - heavy-lock registry row with dead pid
 7. BUDGET_DISAGREEMENT                - registry vs legacy states
 8. S1_SEAL_DISAGREEMENT               - registry vs legacy states
 9. FROZEN_ARTIFACT_DRIFT              - re-hash packet/freeze recorded pins
10. MONITORING_MUTATION                - git status dirt beyond the owner's
                                        pre-existing .zcode/ space

Self-contained: reads the canonical registry plainly (schema id + ids) so it
works from any lane tree; deep registry validation lives in cycle_registry.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

OWNER_PREEXISTING_UNTRACKED = {".zcode/"}  # owner space, classified at H0
STALE_HEARTBEAT_HOURS = 24


def _sh(cmd: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True)


def main_root() -> Path:
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, check=True).stdout.strip()
    return Path(common).parent


def _read_json(path: Path):
    try:
        return json.loads(path.read_bytes().decode("utf-8")), None
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, str(exc)


def check(root: Path = None, ps_lines: list = None) -> list:
    """Return findings as (kind, detail) tuples; empty list = no findings.

    `ps_lines` overrides the host process scan (detection 5) for hermetic
    tests; None = scan the live host.
    """
    root = (root or main_root()).resolve()
    findings = []
    registry, reg_err = _read_json(root / "plans" / "CYCLE_REGISTRY.json")
    reg_ids = set()
    if reg_err:
        # expected BEFORE the owner merges the SHV1 wave (registry lives on the
        # integration branch until adoption) - labeled, not treated as drift
        findings.append(("REGISTRY_NOT_ADOPTED",
                         f"canonical registry not present at {root.name}: {reg_err}"))
    elif registry.get("schema") != "cycle_registry@1":
        findings.append(("CONTROL_STATE_DRIFT",
                         f"registry schema {registry.get('schema')!r} != cycle_registry@1"))
    else:
        reg_ids = {c["cycle_id"] for c in registry["cycles"]}

    # 1. stale router entries (projection vs registry)
    projection, perr = _read_json(root / "plans" / "ACTIVE_CYCLES.json")
    if perr:
        findings.append(("CONTROL_STATE_DRIFT", f"ACTIVE_CYCLES.json: {perr}"))
    else:
        for ghost in sorted({c["cycle_id"] for c in projection.get("cycles", [])} - reg_ids):
            findings.append(("STALE_ROUTER_ENTRY",
                             f"projection names {ghost}; canonical registry does not (closed/historical)"))
        for missing in sorted(reg_ids - {c["cycle_id"] for c in projection.get("cycles", [])}):
            findings.append(("ROUTER_GAP", f"projection omits registry cycle {missing}"))

    legacy_sources = {
        "CRYPTO-V17": ".worktrees/crypto/v17/integration/research/control/v17_run/state_v17.json",
        "FOREX-FREE-V8": ".worktrees/forex-free-v8/integration/research/control/forex_free_v8_run/state.json",
        "STOCKS-FREE-V12": ".worktrees/stocks-free-v12/integration/research/control/stocks_free_v12_run/cycle_state.json",
    }
    states = {}
    for cid, rel in legacy_sources.items():
        state, err = _read_json(root / rel)
        if err:
            findings.append(("STATE_MISSING" if "No such file" in (err or "")
                             or "[Errno 2]" in (err or "") else "CONTROL_STATE_DRIFT",
                             f"{cid}: {rel}: {err}"))
        else:
            states[cid] = state

    # per-registry-cycle checks
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    for rec in (registry or {}).get("cycles", []):
        cid = rec["cycle_id"]
        wt = rec.get("integration_worktree")
        if wt:
            wt_path = Path(wt)
            if not wt_path.exists():  # 2. branch/worktree mismatch
                findings.append(("WORKTREE_MISSING", f"{cid}: {wt}"))
            else:
                branch = _sh("branch --show-current", wt_path).stdout.strip()
                head = _sh("rev-parse HEAD", wt_path).stdout.strip()
                if branch != rec["branch"]:
                    findings.append(("BRANCH_MISMATCH",
                                     f"{cid}: on {branch!r} registry says {rec['branch']!r}"))
                if head and head != rec["head"]:
                    findings.append(("HEAD_MISMATCH",
                                     f"{cid}: branch {head[:7]} vs registry {rec['head'][:7]}"))
        hb = rec.get("heartbeat_utc") or ""
        if hb and rec.get("lifecycle") not in ("TERMINAL",):  # 4. stale heartbeat
            try:
                age = now - datetime.datetime.strptime(hb, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=datetime.timezone.utc)
                if age > datetime.timedelta(hours=STALE_HEARTBEAT_HOURS):
                    findings.append(("STALE_HEARTBEAT",
                                     f"{cid}: heartbeat {hb} is {age.days}d old "
                                     "(expected-stale while PAUSED_MAINTENANCE; label only)"))
            except ValueError:
                findings.append(("CONTROL_STATE_DRIFT", f"{cid}: heartbeat {hb!r} unparseable"))
        state = states.get(cid)
        if state:  # 7./8. budget + S1 disagreement
            used = state.get("budget_used", (state.get("budget") or {}).get("used"))
            if used is not None and used != rec["budget"]["used"]:
                findings.append(("BUDGET_DISAGREEMENT",
                                 f"{cid}: legacy used={used} vs registry {rec['budget']['used']}"))
            if state.get("s1") != rec.get("s1"):
                findings.append(("S1_SEAL_DISAGREEMENT",
                                 f"{cid}: legacy {state.get('s1')!r} vs registry {rec.get('s1')!r}"))

    # 5. live workers not represented in state (self/monitoring processes excluded)
    if ps_lines is None:
        ps = _sh("ps aux | grep -E 'research/.*\\.py|pytest' | grep -v grep", root).stdout
        ps_lines = ps.splitlines()
    live_worker_lines = []
    for line in ps_lines:
        if "/my-quantitative/" not in line or "Visual Studio" in line:
            continue
        parts = line.split()
        if len(parts) > 1 and parts[1] == str(os.getpid()):
            continue  # the diagnostic process itself is not a cycle worker
        live_worker_lines.append(line)
    if registry:
        claimed_workers = sum(int(c.get("workers", 0) or 0) for c in registry["cycles"])
        if live_worker_lines and claimed_workers == 0:
            findings.append(("LIVE_WORKER_UNREPRESENTED",
                             f"{len(live_worker_lines)} repo worker process(es) alive while "
                             f"registry claims workers=0 total"))

    # 6. lock owner without a live process
    runtime = Path.home() / ".my-quantitative-governance" / "heavy_runtime"
    reg_lock, lerr = _read_json(runtime / "heavy_worker.registry.json")
    if reg_lock:
        rows = reg_lock if isinstance(reg_lock, list) else reg_lock.get("rows", [reg_lock])
        for row in rows:
            pid = row.get("pid")
            if isinstance(pid, int) and not _pid_alive(pid):
                findings.append(("LOCK_OWNER_DEAD",
                                 f"heavy-lock registry row pid {pid} ({row.get('cycle_id', '?')}) "
                                 "is not alive - CONTROL_STATE_DRIFT fail closed, reclaim only per round-2"))

    # 9. frozen-artifact hash drift (re-hash pins recorded in SHV1 artifacts).
    # Pin paths may be worktree-relative (cycle branches) or root-relative -
    # resolve against the packet's own recorded worktree as fallback.
    pins_dir = root / "plans" / "system_hardening_v1"
    if pins_dir.exists():
        for packet in sorted(pins_dir.glob("*.json")):
            data, err = _read_json(packet)
            if err:
                continue
            packet_worktree = data.get("worktree")
            for item in (data.get("frozen_artifacts") or []) + (data.get("frozen_artifact_pins_rehashed") or []):
                rel = item.get("path") or item.get("path_on_disk")
                want = item.get("sha256")
                if not (rel and want) or item.get("verification"):
                    continue
                candidates = [Path(rel) if rel.startswith("/") else root / rel]
                if packet_worktree and not rel.startswith("/"):
                    candidates.append(Path(packet_worktree) / rel)
                got = None
                for cand in candidates:
                    try:
                        got = hashlib.sha256(cand.read_bytes()).hexdigest()
                        break
                    except (FileNotFoundError, IsADirectoryError):
                        continue
                if got is None:
                    findings.append(("FROZEN_ARTIFACT_DRIFT",
                                     f"{packet.name}: {rel} unresolvable from root or packet worktree"))
                elif got != want:
                    findings.append(("FROZEN_ARTIFACT_DRIFT",
                                     f"{packet.name}: {Path(rel).name} {got[:12]} != pinned {want[:12]}"))

    # 10. tracked-file mutation caused by monitoring
    status = _sh("git status --porcelain=v1", root).stdout
    dirty = []
    for line in status.splitlines():
        line = line.strip()
        if not line:
            continue
        path = line[3:].strip() if len(line) > 3 else line  # strip XY status prefix
        if path in OWNER_PREEXISTING_UNTRACKED or path.rstrip("/") in OWNER_PREEXISTING_UNTRACKED:
            continue
        dirty.append(line)
    if dirty:
        findings.append(("MONITORING_MUTATION",
                         f"main checkout dirty beyond owner .zcode/ space: {dirty[:3]}"))
    return findings


def _pid_alive(pid: int) -> bool:
    try:
        os_kill = subprocess.run(["kill", "-0", str(pid)], capture_output=True)
        return os_kill.returncode == 0
    except Exception:
        return False


def render(findings: list) -> str:
    if not findings:
        return "doctor: no findings"
    return "\n".join(f"[{kind}] {detail}" for kind, detail in findings)


if __name__ == "__main__":
    print(render(check()))
