# CLOSEOUT — EDGE-SCANNER-TOOLING-V1 (GO-1 verified; TERMINAL UNWIRED)

```yaml
closed_utc: 2026-09-26
closed_by: Lead under owner delegation 2026-09-26 (closeout of GO-1 within plan scope)
authority_chain:
  - OWNER_DECISION_approval_2026-09-26.json (plan approval)
  - GO-1 phrase consumed verbatim -> GO1_RECORDED.json
  - A7 pre-merge D1-D7 PASS (A7_GO1_premerge_REPORT.md) after 3 process findings remediated
  - A7 delta review R1a-c/R2/R3 PASS + R4 conclusion confirmed (finding: row-5 inventory
    evidence corrected, same NO_WIRING conclusion) -> A7_DELTA_REVIEW note in this file
  - terminal flip via researchctl (writer-forced go_phrase_state DEAD per P-8 / RULES §7)
```

## 1. Final state choice: TERMINAL (not parked) — reasoning

1. **The GO-1 deliverable is complete and independently verified twice** (A7
   pre-merge D1–D7; A7 delta re-verification of tests, digests, remediations).
2. **NO_WIRING (see CONSUMER_INVENTORY_and_NO_WIRING.md) means there is no
   remaining in-scope work item.** The GO-2 WIRE template can never fire inside
   this cycle: no ASGI consumer exists, and any future guard for the measured
   surfaces (aiohttp.web gateway, stdlib http.server views) would be a
   framework-native reimplementation belonging to the CONSUMER's own cycle and
   its amendment law (e.g. LIVE-DATA-GATEWAY-V1 for row 5), not to this cycle.
3. **Registry law has no "parked" lifecycle.** The nearest non-terminal states
   all assert something false here: ACTIVE_LIGHT implies live heartbeat duty
   for a static vendored artifact; PAUSED_*/BLOCKED assert a pending reopener
   condition that does not exist. TERMINAL is the only closed, absorbing state
   (cycle_registry.py ALLOWED_TRANSITIONS — TERMINAL has an empty out-edge set).
4. **TERMINAL is also the authority-legal fix for the metadata debt** adjudged
   correct by A7 delta R3: phase records the GO-1 consumption (free-text
   convention, PWS precedent), and the writer forces go_phrase_state to
   "DEAD (consumed or extinguished at its cycle's close per P-8 / RULES §7)"
   on the TERMINAL transition (cycle_registry.py:321-324) — no hand-edit, no
   CONSUMED intermediary exists in the tooling. Regression pin:
   tests/test_cycle_registry.py::test_terminal_go_death_enforced_by_writer
   (28/28 governance suite green this session).
5. Nothing is lost by closing: history is append-only; a future ASGI surface
   or framework-native port references this cycle's evidence (VENDOR_PIN,
   branch, tests) under a NEW owner decision.

## 2. Provenance

- Upstream: github.com/simonro/edge-scanner @ `c927dcb0c5e8122269812d2cdfdc4a3ae71b2ab3`
  (MIT, "Tape to Edge" 2026; NOTICE vendored). Digests (sha256, upstream ==
  vendored, re-verified twice independently + once by Lead re-run):
  local_guard.py `4418a2e1…b762` / LICENSE `5d44f49c…28e3` / NOTICE `d84c264d…d133`.
- Vendored bytes: worktree branch `orca/edge-scanner-tooling-v1-integration`
  commit `938e80e3c3e16f47d00d559ef0c6ed46d4cd0c9b` (parent = main `c9956ac7`),
  exactly 10 additive files (3 vendored + 2 manifests + 5 test files).
- Root evidence commits: `b04447f0` (registration + plan + control dir), this
  closeout commit (corrected inventory + CLOSEOUT + handoff typo fix + registry
  terminal flip).

## 3. Test results (final)

- Vendored battery: **23 passed** — run three times independently: implementer
  (0.28s), A7 pre-merge (0.23s), Lead re-run + A7 delta fresh run (0.23–0.24s).
- Governance suite tests/test_cycle_registry.py: **28 passed** (2.35–2.60s),
  including the terminal-GO-death regression pin.
- No-egress property enforced permanently by test (socket denial across import
  + every guard branch, with non-vacuity sanity).

## 4. GO ledger / constraints honored

- **Consumed:** GO-1 `GO EDGE SCANNER TOOLING V1 VENDOR AND TESTS` (verbatim,
  2026-09-26T13:56Z; GO1_RECORDED.json).
- **Not consumed — extinguished at close:** the GO-2 WIRE template (no consumer;
  NO_WIRING decision). go_phrase_state now DEAD per P-8 / RULES §7.
- workers = 0; heavy lock never taken (light job only; FREE_PROVEN at every run).
- S1 SEALED_UNTOUCHED; no scoring, no OOS looks, no orders, no push, no merge
  to main, no service restarts, no middleware wired into any consumer, no
  changes to gateway/dashboard/shadow/PWS (their concurrent commits are theirs).
- Environment change (disclosed): `.venv` gained starlette 1.7.0 + anyio 4.15.1
  (additive; zero pre-existing dependents — A7 D6).

## 5. Vendor artifact status — precise wording

The vendored middleware exists **only in the worktree branch**
`orca/edge-scanner-tooling-v1-integration` @ `938e80e3` (worktree retained at
`.worktrees/edge-scanner-tooling-v1/integration`). It is **vendored and tested;
it is NOT integrated into any application and NOT on main** — merging branches
to main is an owner-only lever and nothing needs it while unwired.

## 6. Remaining owner levers (all optional; none required for this closeout)

1. Merge `orca/edge-scanner-tooling-v1-integration` into main (only if the
   tooling should be importable from the root checkout later).
2. Worktree cleanup (history-safe: the branch retains everything).
3. If the gateway's loopback WS exposure (`/ws/market`, 127.0.0.1:8792) should
   be hardened: an aiohttp-native Origin/Host guard under
   LIVE-DATA-GATEWAY-V1's amendment law — the vendored guard's `refusal()`
   logic is the ready-made spec; that work belongs to that cycle, not this one.

## 7. A7 delta review — disposition of findings

- R1a/R1b/R1c PASS; R2 PASS (fresh clone + digests + 23 & 28 test runs);
  R3 diagnosis CORRECT (terminal flip = the authority-legal metadata fix);
  R4 NO_WIRING conclusion CONFIRMED with row-5 evidence REFUTED.
- Finding 1 (MEDIUM, row-5 inventory evidence): FIXED — row 5 rewritten from
  A7's citations, re-verified by Lead against service.py:19/:538/:681/:718-733
  and config.py:14-15; §2/§3 and the residual-risk note rewritten honestly
  (the gateway's WS-upgrade Origin exposure is real and this cycle does NOT
  mitigate it); a corrections ledger entry added to the inventory.
- Finding 2 (LOW, handoff actual_start_sha typo): FIXED.
- Finding 3 (LOW, dangling CLOSEOUT.md reference): FIXED — this file.
- A7's authorization: "Once that single doc correction is committed, the
  TERMINAL flip is authorized without further re-review." → corrections
  committed in the closeout commit preceding the flip, then the flip executed.
