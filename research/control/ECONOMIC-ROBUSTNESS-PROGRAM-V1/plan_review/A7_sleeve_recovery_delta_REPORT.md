# A7 DELTA AUDIT — PSV1 sleeve-recovery fix (pre-restart gate)

- Auditor: A7 fresh-context delta auditor (independent, read-only + this report + handoff)
- Date: 2026-09-26
- Verdict: **AUTHORIZED_FOR_RESTART** — 0 HIGH, 0 MED, 4 LOW
- Object: worktree `/Users/hoangminhlong/my-quantitative/.worktrees/prospective-shadow-v1/integration`,
  branch `orca/prospective-shadow-v1-integration`, HEAD `f7f6705dc974b0d9c25be8241d174fdec65dbc05`
  (parent `3cca6833`), tree clean at audit time.
- Governing authority: `OWNER_DELEGATED_DECISION_engine_fix_2026-09-26.json` (arc: patch +
  fixtures + A7 delta THEN restart); incident
  `INCIDENT_psv1_restart_wipes_sleeve_accounts_2026-09-26.md`; implementer handoff
  `.worktrees/prospective-shadow-v1/integration/research/control/prospective_shadow_v1/handoff_sleeve_recovery.json`.
- No process restarted; production ledgers byte-verified unchanged by this audit
  (sha256 before == after every audit action; hashes in R3 below).

## R1 — Diff scope and live-path equivalence: PASS

`git show f7f6705d --stat` = exactly the 5 declared files (accounting.py +100,
executor.py +236, shadow_worker.py +65, tests/test_sleeve_recovery.py +731, handoff
json +101; 1233 insertions, 0 deletions). All 7 hunks across the 3 source files are
accounted for (2 accounting, 1 executor, 4 worker); nothing else changed.

Live-path equivalence of `apply_fill` is **proven at AST level**, not assumed
(parent `3cca6833` vs HEAD, statement-by-statement `ast.dump` comparison):

- HEAD `apply_fill` = 12 leading statements + `return self._apply_fill_mutation(...)`.
  The 12 leading statements are AST-identical to the parent's first 12 (guards AND
  the `econ = self._fill_economics(...)` computation sit at the identical position);
  the return call passes the already-computed `econ`.
- Parent's remaining 14 statements are AST-identical to HEAD `_apply_fill_mutation`
  minus its two leading lines (`primary_fill... = econ[...]`, `signed = ...`) — the
  unified diff over unparsed statements shows exactly those 2 added lines, nothing
  else differs.
- The core's `if econ is None` branch is dead on the live path (apply_fill always
  passes non-None econ), so ordering/guards/costs/identity-assert for LIVE fills are
  unchanged. `apply_funding` (live) is AST-identical (verified).

## R2 — The two implementer deviations: PASS (both independently reproduced)

(a) **Recorded-economics replay without re-admission guards — SOUND and NECESSARY.**
I ran the dispatch's original suggestion as a counterfactual (replay via the
guard-bearing `apply_fill(gross_cap_equity=<sleeve equity>)` against the real
ledgers, read-only): ILLIQ's recorded XRP short is refused
(`InsufficientCashError: gross 100000.0 above equity 99943.91` — stale fill-ref
marks) and XSECT degenerates to **final cash 17033.132935328777 with 48 refusals** —
bit-matching the implementer's disclosed falsification ("XSECT 17,033; ILLIQ lost
its XRP short"). Mechanism confirmed: per-row full-universe marks are not in the
ledger (row key set verified), so guard re-evaluation re-litigates settled history
with degraded information. `apply_recorded_fill` keeps invalid-input validation
(side/qty/ref/tick positive) and the equity-identity assertion; refusals are
recorded as FILL_REFUSED without aborting; admission was enforced live pre-mutation.

(b) **Lineage reseed at diverging rebalance rows — SOUND; ledger evidence verified
byte-exact.** XSECT row 5 (2026-09-19T00:00:00Z): `previous_weights {}`, 0 funding,
cash `99947.2560345751` == 100000 − fee 40.0 − slippage 12.743965424904808 (exact to
1e-9). XSECT row 11 (2026-09-25T00:00:00Z): `previous_weights {}`, 0 funding, cash
`99948.37724941608` == 100000 − 40.0 − 11.62275058390965 (exact). Both rows are
flat-evidenced wipes fired BEFORE the incident's stated wipe #1 — the ledger proves
the damage window opened at the 09-24 08:21 worker-35779 start (earlier than the
incident table states). Row 12 (2026-09-26) is the 0-fill artifact: cash 100000.0,
`target_weights {}`, vacuous decomposition (decision_count 1, fill_count 0). The
reseed rule adopts the fresh basis only at rows that EXECUTED a rebalance, and
carries `flat_evidenced` honestly — a hypothetical non-flat reset row would be
disclosed `flat_evidenced: false` (best-effort positions), not silently trusted.

## R3 — Recovery law and dry-run reproducibility: PASS (reproduced bit-for-bit)

I re-ran the recovery dry-run myself, read-only: executors built against a throwaway
runtime root in /tmp, each `ledger_file` re-pointed at the production ledger,
`recover_sleeve_from_ledger()` run twice per family.

- XSECT: `RECOVERED_WITH_DISCONTINUITIES`, cash_after **99948.37724941608**, 4
  positions (ADAUSDT −79968.01279488204, BNBUSDT 25.653194464040634, DOGEUSDT
  −207684.31983385255, XRPUSDT 12925.74161442513), fills 4 — the incident's "row-11
  truthful book" exactly.
- Exactly 3 discontinuities, deltas matching the handoff to the last digit:
  09-19 RESEEDED_TO_FRESH_LINEAGE (delta −1542.735360583174, flat_evidenced true,
  reseeded_verifies true), 09-25 RESEEDED (delta +428.1533459807979,
  reseeded_verifies true), 09-26 TRUTH_KEPT (delta **−51.6227505839197** — the
  disclosed artifact, the incident's 51.62 jump seen from the replay side).
- ILLIQ: RECOVERED_CLEAN, 1 row, 8/8 fills, cash **99936.78612475483** (== its row-1
  recorded cash), 0 discontinuities. BANDRIDGE: 67 rows, 0 fills, clean.
  BASISLV: 1 row, 0 fills, clean.
- Double-recovery idempotent on all four families (summaries equal).
- Per-row verification law in code: `abs(replay_cash − recorded_cash) > 0.01` →
  disclosed RECOVERY_DISCONTINUITY, never silently absorbed; corrupt/partial ledger
  → `LedgerCorruptError` from `scan_events` → worker build fails closed.
- **Production ledger sha256 unchanged by all audit actions** (before == after):
  XSECT `319bbbe0a4beb742…`, ILLIQ `900675d8d2c07e42…`, BANDRIDGE
  `4e4be9da0bcd4856…`, BASISLV `7cc66e6c27b0ca71…`.

## R4 — Marker rows: PASS

- `event_id = events.compute_event_id(family, arm, "RECOVERY-" + first_row_ts)`;
  decision stamps come from frozen schedules (ISO stamps) and can never equal a
  `RECOVERY-…` string; test_c proves absence of collision against the full frozen
  stamp set over 2026→2031.
- `ledger.append_event` skips on existing event_id (code-verified) with mandatory
  read-back verification; test_c asserts the double-build ledger is **byte-identical**
  (`read_raw_bytes` equality) — restart-idempotent, exactly one marker.
- No marker for families that never held anything (fills 0 AND no discontinuities →
  `_append_recovery_marker` returns None; test_c_families; BANDRIDGE/BASISLV were
  marker-free no-ops in my dry-run).
- Scheduler/heartbeat safety: marker carries `scheduled_decision_utc = anchor`
  (the ledger's OLDEST stamp), so `max()` scans (scheduler.run_once from_utc,
  `_last_completed`) are undistorted; `run_due`'s known_ids = `ledger.event_ids`
  (schema-agnostic) — decision ids unaffected; `scan_events` requires only dict +
  string event_id, so the marker scans cleanly; `valuation.rebuild_positions` reads
  it as a no-op (no `funding_cashflow`, no `virtual_fill_events` keys); recovery
  itself skips marker rows by schema on second boot. All ledger-scan consumers
  enumerated and checked marker-tolerant.

## R5 — Tests: PASS

- My run, from the worktree integration dir with the absolute venv python, the
  7 required suites: **102 passed** in 14.77s (matches the gate exactly; 11 new
  fixtures a–h in tests/test_sleeve_recovery.py, incl. funding parity vs live
  apply_funding and fill parity vs apply_fill).
- Parent spot-check via a THROWAWAY detached worktree at `3cca6833` in /tmp
  (the production checkout was never touched; worktree removed after): the two
  reported pre-existing failing FILES fail **identically at parent and HEAD**
  (failure sets diffed: identical). Precision: that is 2 files but **8 failing test
  items** — `test_family_failures.py` 7 (registry validation + 6 signature params,
  verdict_class/signature registry-data drift) + `test_shv1_identity_recovery.py::test_every_listed_file_exists_and_hashes_match`
  (sha256 drift of a WORKING_TREE_TRACKED SPEC.md in the foreign worktree
  .worktrees/btc-h4-band-risk-v1). Pre-existing environmental; untouched by this
  lane. (The implementer handoff's "2 pre-existing failures" counts files, not items.)

## R6 — Restart safety: PASS with disclosed risks (all LOW)

What the restart will do (verified in code, worker `main` → `build_executors` →
`run_loop`): per family in fixed order, recovery replays the ledger BEFORE the first
`run_due`; appends exactly ONE marker row to XSECT (anchor 2026-09-15T00:00:00Z) and
ILLIQ (anchor 2026-09-21T00:00:00Z), none to BANDRIDGE/BASISLV; `run_due` then
continues unchanged. XSECT's next frozen decision 2026-09-27T00:00Z runs under the
retire law (`XSECT_RETIRE_AFTER_UTC = "2026-09-25T05:45:00Z"`, config-injected at
worker L786): flat-only targets → the 4 restored positions close with REAL fills and
a SECOND terminal row fires — this time a faithful decomposition of the current
lineage; the 09-26 vacuous row stays canonical per the A7 F1 advisory, with
`RETIRE_TERMINAL_CORRECTION` as the sequenced append-only follow-up. ILLIQ's book is
restored before its Mon 2026-09-28T00:00Z weekly decision (the urgency driver).
BANDRIDGE continuity is protected before any first fill. The running worker
(pid 65078) boots from this same checkout; tree is clean at f7f6705d.

Residual risks (LOW, disclosed, none blocking):
1. Cost-regime change while positions are open would need regime-aware replay
   (out of scope; no regime change occurred — per-fill economics re-verified 1e-9).
2. `funding_paid` attribution and decision/order-intent counters restart at
   replay-derived values — informational fields only (verified nothing in
   sizing/caps/retire reads them).
3. Valuation worker's ghost XSECT marks persist until its own owner-gated restart —
   dashboard MTM vs ledger divergence in the interim (sequenced follow-up #3).
4. The ledger will contain TWO terminal rows (09-26 vacuous artifact + 09-27
   faithful); all consumers must treat 09-26 as the canonical artifact row until the
   correction record lands — operational discipline, not a code defect.
5. `CODE_FREEZE_SHA` intentionally not re-pinned (A2/A3 precedent); the constant's
   "audited engine bytes" claim is now historical — owner-level note.
6. Boot-time marker append mutates ledgers by design (inside the delegation's arc);
   restart must follow the standard SIGTERM-then-start sequence against pid 65078.

## LOW findings (precision notes, no remediation required before restart)

- L1: Handoff's "2 pre-existing failures" = 2 files / 8 test items (stated precisely
  in R5).
- L2: The dispatch's implementer-handoff path (`research/control/prospective_shadow_v1/
  handoff_sleeve_recovery.json`) exists only inside the worktree (self-committed per
  the handoff's own note), not at the repo-root checkout.
- L3: CODE_FREEZE_SHA staleness (see R6.5) — already disclosed by the implementer.
- L4: Incident addendum recommended: ledger rows 5/11 prove the wipe also fired at
  the 09-24 08:21 start, so the incident's trigger table understates the damage
  window (implementer already flagged; remediation unchanged).

## Verdict

**AUTHORIZED_FOR_RESTART** — the fix is scoped exactly, live-path behavior is proven
unchanged, both deviations are measured and correct (the falsification reproduces
bit-for-bit), the recovery law reproduces its claimed numbers exactly against the
real ledgers without touching them, marker mechanics are idempotent and
scheduler-safe, the gate suites pass 102/102, and the pre-existing failures are
proven pre-existing. Proceed to the controller's restart window per the owner
delegation, then sequence the follow-ups (RETIRE_TERMINAL_CORRECTION after the
09-27 decision; valuation ghost-mark reconcile under its own gate).
