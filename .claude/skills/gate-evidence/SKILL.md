---
name: gate-evidence
description: Execute or record a research/release gate with exact SHA, command, exit code, clean-tree state, expected/observed result, logs, and PASS/FAIL/NOT_RUN semantics.
allowed-tools: Bash, Read, Grep, Glob
---

# Gate evidence

Run a gate from its authorized clean integration/detached worktree:

```bash
python3 .claude/skills/gate-evidence/scripts/run_gate.py \
  --gate-id <ID> --owner <role> --expected '<contract>' \
  --evidence-dir <run>/gates -- <command> <args...>
```

The runner does not use a shell, refuses to overwrite existing evidence unless
`--overwrite` is explicit, captures stdout/stderr, and records full SHA plus
before/after tree state. It reports PASS only for exit 0 from a clean tree that
stays clean. To document a gate that could not run, add `--not-run-reason` and
omit the command.

Never weaken a command after failure. Record the failure, repair through the
authorized lane, integrate, and rerun as a new honest measurement according to
the PLAN's evidence policy.
