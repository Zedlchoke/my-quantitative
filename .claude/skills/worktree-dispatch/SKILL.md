---
name: worktree-dispatch
description: Freeze, create, verify, and dispatch exact PLAN-defined Git worktrees with branch/SHA identity, non-overlapping ownership, test commands, and A1-only integration.
allowed-tools: Bash, Read, Grep, Glob
---

# Worktree dispatch

Only A1 performs this workflow. Root must be clean and the owner must have
approved a full 40-character bootstrap SHA containing the plans.

1. Copy the exact path/branch from the applicable PLAN. Never invent a path.
2. Inspect `git worktree list --porcelain` and existing branches first.
3. If either path or branch exists, inspect it; do not force, delete, reset, or
   rerun `worktree add`.
4. For a fresh lane, use the PLAN's command with the literal placeholder
   replaced by the measured full SHA.
5. Verify with:

```bash
python3 .claude/skills/worktree-dispatch/scripts/verify_worktree.py \
  --path <absolute-path> --branch <expected-branch> \
  --head <full-40-character-sha> --require-clean
```

6. Freeze the record fields in [manifest-contract.md](references/manifest-contract.md),
commit the manifest, then dispatch the agent with exact cwd and ownership.

Detached execution/reproduction worktrees use `--detached`. A1 cherry-picks one
lane commit at a time; agents never integrate themselves.
