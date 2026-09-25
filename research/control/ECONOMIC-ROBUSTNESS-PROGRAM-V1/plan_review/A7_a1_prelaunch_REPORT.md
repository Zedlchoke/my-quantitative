# A7 PRELAUNCH AUDIT — FX-RANGEFADE-2M-SHADOW-V1 A1-controls, Phase I

- Auditor: A7 fresh-context (audit only, never repair; read-only except this
  report + the handoff JSON).
- Date (UTC): 2026-09-25 (audit executed ~05:07Z).
- Object: worktree `/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1`,
  branch `orca/fx-rangefade-2m-shadow-v1`, HEAD measured
  `686bb8365db87b8b74b71843efe1ad13608a177d` (== expected dispatch SHA).
- Binding spec: `plans/DRAFT_amendment_FX-RANGEFADE-2M-SHADOW-V1_A1_controls.md`
  (root, committed at 88016399, working tree clean).
- Implementer handoff: `research/control/FX-RANGEFADE-2M-SHADOW-V1/HANDOFF_A1_phase1.json`
  (worktree, untracked post-commit by design).
- Lifecycle position: G (GO consumed) → I (done) → **V (this audit)** →
  A (controller-owned; not authorized by this verdict alone).

## VERDICT: AUTHORIZED_FOR_ACTIVATION

No code defect found. One MEDIUM process condition is binding on Phase A
(see M-1 / Q1): the cost book must be owner-pinned BEFORE the first new
cost-bearing journal row is written at T_ctrl. The change-set itself needs
no repair.

---

## C1 — GO gate exact-match + prerequisites: PASS

- `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/A1_gate/GO_RECORDED.json`:
  `go_phrase_typed` == `go_phrase_expected` ==
  `GO FX RANGEFADE AMENDMENT A1 CONTROLS MOUNT`, `form_check: EXACT_MATCH`,
  `consumed_at_utc: 2026-09-25T04:21:15Z` — matches the owner-GO context.
- Prerequisites verified: `draft_committed: true` (spec is tracked and clean
  at root, commit 88016399) and `independent_review: PASS r2`
  (DRAFTS_review_round2_REPORT.md present under plan_review/).
- Authority scope respected: GO granted "Phase I ONLY"; V gates A; the
  implementer did NOT restart the daemon ("A typed GO is never evidence the
  daemon changed" — confirmed: no restart occurred).

## C2 — Zero-diff law (frozen strategy surface untouched): PASS

Independently verified, not taken from the handoff:

1. `git show 686bb836 --stat`: exactly the 5 declared files
   (daemon/fx_shadow_core.py, daemon/shadow_daemon.py,
   session_spread_curve.json, tests/test_a1_controls_phase1.py,
   tests/golden_a1_phase1.json). `v2_lib.py` / `engine.py` untouched.
2. Whole-commit deletions: 2 lines, both in `main()` boot wiring
   (`Journal(` → `CostJournal(`, and the replay-lines split). Zero
   decision-path lines deleted. `fx_shadow_core.py` diff is purely
   additive (0 deleted lines; A1 code appended after line 214).
3. Frozen main-loop sleeve block: the 28-line block sha in
   `tests/golden_a1_phase1.json`
   (`sha256:3760ce6b6b1c242ba...`) recomputes exactly from the current
   file (test passes) AND I independently extracted the identical 28-line
   block from the PARENT commit `f8bb2b73` shadow_daemon.py (starts at
   0-based line 291) — same sha. The "captured BEFORE the change" claim is
   genuine.
4. Frozen files: pinned values are FULL sha256
   (`v2_lib.py efb87e37...`, `engine.py cc868402...`); the worktree's
   imported copies (`research/control/EURUSD-OPEN-SEARCH-V2/scripts/v2_lib.py`,
   `.../EURUSD-OPEN-SEARCH-V1/scripts/engine.py`) match on disk and are
   untouched by the commit. The 15 `inspect.getsource` function shas are
   enforced at test time and pass; combined with pure additivity this
   proves pre-change equality.
5. Journal purity: `shadow_journal.jsonl` (worktree) has 94 rows — event
   kinds {parity_selftest 22, shadow_start 11, boot_replay 12, bar_closed
   44, fill_open 2, force_flat 2, day_roll 1}; ZERO rows contain
   ctrl_open/ctrl_close/epoch_report/cost_book/short_beta_label/
   a1_cost_enrich and ZERO rows contain any cost field
   (fee_bps/cost_book_digest/stress_slip/round_trip_id/realized_net). The
   running daemon (pid 35609, started 2026-09-24 15:19 local, i.e. BEFORE
   the 2026-09-25 11:55 local commit) executes pre-A1 code — the new code
   has never run against the live journal.
6. Test suite re-run by auditor:
   `python -m pytest research/control/FX-RANGEFADE-2M-SHADOW-V1/tests/ -q`
   from the worktree root → **50 passed, 0 failed, 1.67s**. Breakdown
   measured by collect-only: 24 new (test_a1_controls_phase1.py) + 26
   pre-existing (3 bar_append_dtype + 12 core_restart_account + 6
   http_endpoints + 5 no_order_api). The 4 pre-existing test files were
   last touched at f8bb2b73 (parent) — not modified by the change-set.

## C3 — Control arms law: PASS

- **CTRL-SHORT-ALWAYS** is a DAY-SESSION construct: short 1.5 lots at the
  first fillable H1 open after 00:00 UTC per weekday (`fill_allowed_open`
  = new-bar hours 01..19), force-flat at the sleeve's own 20:00 UTC
  boundary (observer forces flat when the just-closed bar hour == 19,
  exactly the sleeve's own force-flat trigger), weekend-flat by
  construction (`is_weekday_utc` verified correct vs 1970-01-01=Thursday).
  The binding comparability note (ancestor +314 window-long SHORT_ALWAYS
  at bf4f07f1 NOT numerically comparable) is present in the class
  docstring, in the state `a1_controls.comparability_note`, and in the
  commit message.
- **CTRL-SHADOW-MATCHED**: mirror driven by observed sleeve transitions —
  entry sign-inverted (`pos = -sleeve_dir` at the sleeve's own fill px),
  exit applied IDENTICALLY at the sleeve's own close-px rule (bid if the
  sleeve was long, ask if short — mirrors the frozen block's rule). Never
  re-inverted at exit.
- **Same cost book**: both arms + the sleeve are enriched from the single
  `CostBook` instance loaded from session_spread_curve.json; same
  opposite-quote rule (short sells at bid / covers at ask).
- **The 01:00 interpretation is LAWFUL** (see Q2 below): the sleeve's own
  frozen fill law gates fills on `closed_hour <= 18`; at the 00:00 open the
  just-closed bar is hour 23 → not fillable; the first fillable open after
  00:00 is therefore 01:00. `fill_allowed_open` is a verified derived
  restatement of the frozen block's condition, not a new rule.

## C4 — USD exposure block (C-FX-2): PASS

`usd_exposure_block` emits per-pair direction, `usd_same_side_notional`
(lots + USD; 0 unless every open pair shares one direction) and
`usd_net_notional` (signed), per H1 decision epoch — journaled as
`epoch_report` rows (deduped per boot; basis string marks stress as
never-primary) and rendered in state. Display-only per owner D10: the
observer never writes a sleeve attribute and never gates a sleeve decision
(verified by code read; the sleeve block is byte-frozen).

## C5 — Stress-spread book (C-FX-3): PASS, with MEDIUM condition M-1

- Session bucket of every fill = UTC hour of the PIT quote timestamp;
  stress charge = session median × 2.0 (lane-F frozen tier) for the fill's
  bucket, USD-converted at $10/pip/lot × 1.5 lots. Parallel reporting view
  only — `realized_net_stress` is a separate field, `epoch_report` basis
  strings say "NEVER primary PnL"; primary PnL math is untouched.
- Single source: session_spread_curve.json, digest-pinned
  (`sha256:<16-hex>` recorded in every cost row via `cost_book_digest`),
  dated 2026-09-25, with single_source_law forbidding in-place rewrite.
- **SEED disclosure is prominent** — verified at every layer: file top-level
  `status: SEED_VALUES_PENDING_SHA_PINNED_CENSUS` + `seed_disclosure`
  paragraph; `declared_fee_schedule.class:
  DECLARED_SEED_PENDING_OWNER_PIN_AT_A1_GATE_REVIEW`; code docstrings
  (CostBook, session bucket helpers); state summary surfaces
  `cost_book.status`; a dedicated test
  (`test_e_seed_status_disclosed_and_digest_pinned`) asserts "SEED" in
  status and census in the disclosure; commit message and handoff repeat
  it. Nothing treats the seeds as measured.
- **M-1 (MEDIUM, process, binding on Phase A)**: the sha-pinned Dukascopy
  census artifacts that amendment §1.3 names DO exist in the repo and DO
  contain per-session-bucket p50 medians
  (`.worktrees/eurusd-open-search-v2/.../EURUSD-OPEN-SEARCH-V2/data_local/derived/census.json`
  `spread_pips.by_session_open` — buckets asia_00_07 / london_07_12 /
  ny_overlap_12_16 / ny_late_16_21 / rollover_21_22 / late_22_24; and
  `.worktrees/fx-majors-search-v1/.../FX-MAJORS-SEARCH-V1/data_local/GBPUSD/derived/census.json`
  EURUSD 0.30 / GBPUSD 0.80 global p50s confirm the seed order-of-magnitude).
  The pin is therefore actionable immediately, with no new measurement
  work. Per §2 the primary book must be pinned "before any new row is
  written" — see Q1.

## C6 — Cost journal law (C-FX-4): PASS

- New-row-only: `CostJournal.log` enriches only freshly written
  fill_open/fill_close/force_flat rows; `Journal` writes append-only
  (open-"a"); no backfill code path exists;
  `test_d_live_journal_old_rows_are_not_backfilled` asserts the LIVE
  journal's gross-only rows read NOT_RUN_COST_FIELDS and stay unmodified.
- Absence semantics: `cost_field_status` distinguishes open-row vs
  close-row field sets; absence is `NOT_RUN_COST_FIELDS`, never zero.
- Enrichment failure cannot break the sleeve: the row is written
  unenriched plus an `a1_cost_enrich_error` marker event (disclosed
  fail-open). Restart seam: a close of a position restored across a
  restart charges exit-side costs only and carries
  `rt_note=entry_cost_ctx_missing_restored_position` — disclosed, never
  silently zeroed (LOW L-3).
- Boot writes a `cost_book` disclosure row (digest, status, phase
  `PHASE_I_code_only_NOT_ACTIVATED`) — filtered out of sleeve replay.

## C7 — Dashboard/process: PASS

- daemon pid 35609 (started 2026-09-24 15:19) and dashboard pid 8093
  (serve.py, started 2026-09-24 12:00, LISTENING localhost:8766) both
  alive and untouched; exactly ONE shadow_daemon process machine-wide;
  daemon heartbeat fresh (2026-09-25T05:06:33Z). Auditor performed no
  restart/stop.
- No order path: no broker/order surface in the new code; no network calls
  added to fx_shadow_core.py (the only socket in the daemon remains the
  pre-existing TrueFX read-only poll); test_no_order_api (5 tests) passes.
- No credentials in any changed file (grep for password/token/secret/
  api_key/credential: clean).

---

## The three questions

### Q1 — Are the SEED values lawful for Phase A activation?

**As carried today (Phase V / prelaunch): yes.** The seeds are disclosed
prominently in file + code + state + tests, dated, digest-pinned, and
explicitly scoped to "plumbing tests only, NOT cost conclusions". That is
exactly the honest interim the draft's implementation phase allows.

**For Phase A emission of cost rows: not without an owner pin act.**
Amendment §2 is explicit: the primary book is "pinned at implementation
gate, BEFORE any new row is written". If the controller restarts the daemon
at T_ctrl while the book is still
`SEED_VALUES_PENDING_SHA_PINNED_CENSUS`, the first cost-bearing rows would
be written on an unpinned book — a §2 violation even though everything is
labeled. Two lawful paths, owner's choice:
1. **Pin the census (recommended)** — replace session_spread_curve.json via
   a NEW dated file + new digest boundary with the per-session p50 medians
   from the existing sha-pinned-able census artifacts (EURUSD-OPEN-SEARCH-V2
   + FX-MAJORS-SEARCH-V1; both found, both contain by-session medians —
   note the census buckets split Rollover/Late slightly differently from
   the seed convention, which the replacement must reconcile), or
2. **Owner explicitly affirms the current seed/declared values as the
   pinned book** at this gate (a recorded owner decision), keeping the
   digest boundary.

Until one of those is recorded, Phase A must not start emitting cost rows.

### Q2 — Is the 01:00 interpretation acceptable or an owner decision?

**Acceptable and lawful under §1.1; no separate owner decision required.**
The draft says "the first fillable H1 open after 00:00 UTC" and §2 binds
controls to "identical ... fill law as the sleeve". The sleeve's own frozen
law fills only at opens whose just-closed bar hour ≤ 18 — the 00:00 open
(just-closed hour 23) is not fillable — and the text "after 00:00" also
excludes the 00:00 open itself. Both readings converge on 01:00; the
implementation is the unique sleeve-consistent reading. Recommendation:
record this one-line interpretation in the Phase A activation artifact so
the gate record is self-contained (not a new decision, just its
documentation).

### Q3 — What Phase A requires

1. Owner completes the M-1 pin act (census file swap with new digest, or
   explicit seed affirmation) — BEFORE the restart.
2. Controller (not the implementer, not this auditor) restarts the daemon
   per the cycle's normal procedure; the typed GO alone restarts nothing.
3. Record `T_ctrl` to the second (UTC) in an activation artifact
   (amendment §4), alongside the cost-book digest in force at T_ctrl.
4. Arms begin emitting: ctrl_open/ctrl_close per pair, epoch_report rows,
   cost fields on NEW rows only; old 94 gross-only rows stay untouched.
5. The `SHORT_BETA_UNSEPARATED — NOT PROMOTABLE` label drops only when the
   control arms have emitted records (implemented: any ctrl fill after
   replay → `SHORT_BETA_SEPARATED`); until then every sleeve PnL line keeps
   the label and nothing is promotable.
6. Restart-idempotence proof at the seam: no duplicate event_ids; journal
   append-only (replay idempotence is already test-pinned, incl. duplicated
   A1 rows collapsing).

---

## Findings register

| ID | Severity | Finding | Disposition |
|----|----------|---------|-------------|
| M-1 | MEDIUM | Cost book still SEED/DECLARED-SEED; §2 requires pin before first new cost row. Census artifacts exist with per-session p50 medians — pin is immediately actionable. | Binding pre-Phase-A condition (Q1). Not a code defect; code correctly refuses to self-certify. |
| L-1 | LOW | 5 untracked paths in the FX worktree: HANDOFF_A1_phase1.json (post-commit by design) + dashboard/__pycache__, dashboard/assets, dist_phorec_stage, equity_curve.json (pre-existing runtime detritus, untouched by the lane). | Hygiene only; no law violation. |
| L-2 | LOW | `epochs_reported` dedupe is in-memory per boot; a restart may re-journal an epoch_report row for the same epoch. | Harmless: A1 rows filtered from sleeve replay and ignored by control replay; journal stays append-only. |
| L-3 | LOW | Close of a position restored across a restart realizes net with exit-side costs only (entry-side unknown), disclosed via `rt_note=entry_cost_ctx_missing_restored_position`. | Accepted as disclosed; complete round-trips exist only for post-T_ctrl open+close pairs. |

## Artifacts

- This report: `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/plan_review/A7_a1_prelaunch_REPORT.md`
- Handoff: `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/plan_review/HANDOFF_a7_a1_prelaunch.json`
  (schema `zcode_orch_v3_handoff@1`)
