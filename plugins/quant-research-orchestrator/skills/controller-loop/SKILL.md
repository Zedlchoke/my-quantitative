---
name: controller-loop
description: "The 12-step ZCODE-ORCHESTRATION-V3 controller loop for the primary Lead: reconcile truth, validate authority, register dependency graph, dispatch READY tasks within slot caps, integrate one commit at a time, queue heavy work under the machine-wide lock, then reproduction and A7, terminal reconcile. Use when starting or resuming a Lead session for this cycle."
---

# Controller loop (plan sec 8)

Run in order; never skip reconcile:

1. **Reconcile** repository/runtime truth: git HEAD/branch/dirty/worktrees,
   registry (researchctl cycle list / doctor), heavy lock (locks inspect),
   orchestrator waiting_summary + terminal_check. Malformed state is
   CONTROL_STATE_DRIFT: record it, do not invent a clean state.
2. **Validate authority**: the plan in full is the contract; owner authority
   boundaries are in plan sec 13. When missing, stop — never self-grant.
3. **Register** the dependency graph (orchestrator_register_task; cycles and
   unknown deps are refused by the store).
4. **Dispatch** all READY disjoint light tasks (orchestrator_list_ready) within
   the slot cap: 8GB host = Lead + max 3 light lanes; ONE heavy job
   machine-wide under the global lock, never alongside full-suite tests.
   Background for long work; foreground for fast reads.
5. **Keep integration moving** while lanes run: review returned artifacts,
   prepare validation commands.
6. **Accept** returned handoffs automatically (background results arrive in
   this conversation; the store binds them by digest).
7. **Validate independently**: dispatch_sha == actual_start_sha, commit exists,
   changed_paths within allowed_paths, tests re-run or digested — prose is
   advisory, artifacts are authority.
8. **Integrate** one commit at a time (cherry-pick/merge lane branch), run the
   targeted gates after each pick, orchestrator_mark_integrated, then unlock
   dependents.
9. **Queue/wait** heavy work under the global heavy lock; NOT_RUN_RESOURCE_CONFLICT
   if the lock is held; no spin, no stealing foreign workers.
10. **Dispatch reproduction** (detached twin, frozen inputs), then **A7**
    (fresh context, claim+evidence only).
11. **Terminal reconcile**: all tasks TERMINAL, workers 0, evidence complete.
12. **Notify the owner** only at: credential/account/license/purchase, S1 or
    scored GO, push/merge/deploy, irreconcilable ownership choice, repeated
    blocker, or the terminal verdict. Ordinary PASS/FAIL handoffs never need
    the owner.
