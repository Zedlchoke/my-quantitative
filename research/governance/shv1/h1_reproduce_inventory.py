#!/usr/bin/env python3
"""SHV1 Gate H1 - reproduce the frozen inventory from bytes.

Recomputes every claim in H1_CONTRACT_FREEZE.json#inventory_at_freeze from the
live tree and exits non-zero on any mismatch. Fresh-context reproducible: the
only inputs are this script + the freeze file (A7 at H6 re-runs it).
"""
import hashlib, json, os, subprocess, sys

ROOT = "/Users/hoangminhlong/my-quantitative"
FREEZE = os.path.join(ROOT, ".worktrees/system-hardening-v1/integration/research/governance/shv1/H1_CONTRACT_FREEZE.json")

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def main():
    fz = json.load(open(FREEZE))
    inv = fz["inventory_at_freeze"]
    failures = []

    wt_count = len([l for l in sh(f"git -C {ROOT} worktree list").stdout.splitlines() if l.strip()])
    if wt_count != inv["worktrees_total"]:
        failures.append(f"worktree count {wt_count} != frozen {inv['worktrees_total']}")

    br = sh(f"git -C {ROOT} branch").stdout
    br_count = len([l for l in br.splitlines() if l.strip()])
    if br_count != inv["local_branches_total"]:
        failures.append(f"branch count {br_count} != frozen {inv['local_branches_total']}")

    for lane, meta in fz["lane_topology"].items():
        p = os.path.join(ROOT, meta["path"])
        head = sh(f"git -C {p} rev-parse HEAD").stdout.strip()
        branch = sh(f"git -C {p} branch --show-current").stdout.strip()
        dirty = sh(f"git -C {p} status --porcelain=v1").stdout.strip()
        anc = sh(f"git -C {p} merge-base --is-ancestor {meta['head_at_creation']} HEAD && echo OK").stdout.strip()
        if anc != "OK":
            failures.append(f"lane {lane} head {head[:7]} does not descend from frozen creation head {meta['head_at_creation'][:7]}")
        if branch != meta["branch"]:
            failures.append(f"lane {lane} branch {branch} != frozen {meta['branch']}")
        if dirty:
            failures.append(f"lane {lane} dirty: {dirty[:80]}")

    for rel, want in inv["hashes"].items():
        got = sha16(os.path.join(ROOT, rel))
        if got != want.split(" ")[0]:
            failures.append(f"hash {rel} {got} != frozen {want}")

    for cyc, want in inv["cycle_authority_heads"].items():
        wt = {"CRYPTO-V17": ".worktrees/crypto/v17/integration",
              "FOREX-FREE-V8": ".worktrees/forex-free-v8/integration",
              "STOCKS-FREE-V12": ".worktrees/stocks-free-v12/integration"}[cyc]
        got = sh(f"git -C {os.path.join(ROOT, wt)} rev-parse HEAD").stdout.strip()
        if got != want:
            failures.append(f"{cyc} head {got[:7]} != frozen {want[:7]}")

    # wave ancestry: every lane head descends from SHV1_WAVE_SHA
    for lane, meta in fz["lane_topology"].items():
        r = sh(f"git -C {os.path.join(ROOT, meta['path'])} merge-base --is-ancestor {fz['shv1_wave_sha']} HEAD && echo OK")
        if r.stdout.strip() != "OK":
            failures.append(f"lane {lane} does not descend from SHV1_WAVE_SHA")

    for f in failures:
        print("FAIL:", f)
    print(f"GATE H1: {len(failures)} mismatches -> exit {min(len(failures),1)}")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
