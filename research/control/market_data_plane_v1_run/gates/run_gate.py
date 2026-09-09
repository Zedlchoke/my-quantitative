#!/usr/bin/env python
"""MDP-V1 gate evidence recorder.

Runs one gate command, captures exit code / UTC / HEAD / stderr tail, and
writes a gate JSON under gates/. Every gate is recorded as PASS, FAIL,
NOT_RUN or BLOCKED — never inferred. Usage:

    python run_gate.py <gate_name> <PASS|FAIL|NOT_RUN|BLOCKED-expected> -- <command...>

The verdict recorded is derived from the exit code, not from expectation:
exit 0 => PASS, else FAIL, unless --verdict overrides (for resource
conflicts where the command could not legitimately run).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("gate_name")
    ap.add_argument("--verdict", default=None, help="force NOT_RUN/BLOCKED for resource-conflict cases")
    ap.add_argument("--note", default="")
    ap.add_argument("--out", default=None)
    ap.add_argument("cmd", nargs="+")
    args = ap.parse_args()

    run_dir = Path(__file__).resolve().parent
    started = datetime.datetime.now(datetime.timezone.utc)
    proc = subprocess.run(args.cmd, capture_output=True, text=True, cwd=str(run_dir.parents[4]))
    ended = datetime.datetime.now(datetime.timezone.utc)

    head = "unknown"
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(run_dir.parents[4])
        ).stdout.strip()
    except Exception:
        pass

    verdict = args.verdict or ("PASS" if proc.returncode == 0 else "FAIL")
    record = {
        "gate": args.gate_name,
        "verdict": verdict,
        "command": args.cmd,
        "exit_code": proc.returncode,
        "started_utc": started.isoformat(),
        "ended_utc": ended.isoformat(),
        "elapsed_s": round((ended - started).total_seconds(), 3),
        "head": head,
        "note": args.note,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }
    blob = json.dumps(record, indent=1).encode()
    record["record_sha256"] = hashlib.sha256(blob).hexdigest()
    out = Path(args.out) if args.out else run_dir / f"{args.gate_name}.json"
    out.write_text(json.dumps(record, indent=1) + "\n")
    print(f"{args.gate_name}: {verdict} (exit {proc.returncode}) -> {out}")
    return 0 if verdict in ("PASS", "NOT_RUN", "BLOCKED") else 1


if __name__ == "__main__":
    sys.exit(main())
