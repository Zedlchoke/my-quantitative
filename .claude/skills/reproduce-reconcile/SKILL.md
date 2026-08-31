---
name: reproduce-reconcile
description: Independently rerun frozen trials in clean isolated processes and reconcile artifacts, hashes, metrics, stresses, ledgers, trial collisions, and observed-versus-published denominators before a terminal verdict.
allowed-tools: Bash, Read, Grep, Glob
---

# Reproduce and reconcile

Use the exact frozen SHA, environment lock, data/spec/config digests, arm keys and
commands. Reproduce from fresh detached worktrees or clean isolated processes;
do not reuse mutable caches unless their keys and contents are verified.

Compare canonical artifact content, not worktree-local absolute paths. Reconcile:

- every planned, computed, published, collided and technical-abort cell;
- metrics and fold outputs, fills, costs, stresses and terminal policy;
- ledger rows, trial registry and observed/published counters;
- source/config/data hashes and clean before/after tree state;
- S1 non-access and absence of replacement/tuning.

Classify each item `MATCH`, `MISMATCH`, `MISSING`, or `NOT_RUN`. Any unexplained
surface prevents terminal PASS. Use existing protocol reproduction utilities and
tests rather than creating a second metric implementation.
