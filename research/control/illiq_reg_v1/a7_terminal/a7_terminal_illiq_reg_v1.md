# A7 TERMINAL — ILLIQ-REG-V1 · VERDICT: CONFIRM

- schema `illiq_reg_v1.a7_terminal@1` · machine mirror: `a7_terminal_illiq_reg_v1.json`
- head audited `0995044cbe4a736050b46b6693eac7491164278a` (branch `orca/illiq-reg-v1-integration`, worktree `.worktrees/illiq-reg-v1/integration`, git-clean)
- audit_utc `2026-09-24T06:27:29Z` · auditor: A7 independent terminal auditor, fresh context, read-only except this artifact
- blocking findings: **0** · non-blocking: 5 (NB-1..NB-5 below)

## 1. Freeze chain — PASS

`git log 482dc81b..0995044c` shows exactly: `58b93de3` (M0, 35 tests) → `b9ae22df`
(gate-series full build, sanitized dry-run) → `eb86951e` (handoff — head audited by
prelaunch A7) → `8f476744` (A7 prelaunch artifact + corrected incident; **GO
consumption head**) → `bcaa34dc` (launch machinery) → `31985732` (**phase-1 scored
complete, VERDICT FALSIFIED**) → `0995044c` (reproduction twin ALL_MATCH).
`31985732` is an ancestor of `0995044c`. Integration tree clean at `0995044c`.

## 2. Cell truth — PASS (recomputed from artifact bytes)

For each `phase1/P1-C*/results/artifact.json`, from its own 52 `daily_returns` rows:
sum of `net_return_per_unit` and additive peak-to-trough MDD on its cumsum.

| cell | arm / stress | recomputed net_sum | recomputed MDD | matches portfolio_metrics & claim |
|---|---|---|---|---|
| P1-C1 | ANCHOR `ILLIQ-AMIHUD-28D-W` baseline fee 1.0 | **-0.345788758154** | **0.419177956499** | yes |
| P1-C2 | ANCHOR x1.5 | -0.349759248019 | 0.421401422724 | yes |
| P1-C3 | ANCHOR x2.0 | -0.353729737883 | 0.423624888948 | yes |
| P1-C4 | INV `ILLIQ-AMIHUD-28D-W-INV` baseline | +0.329724146812 | 0.165130031833 | yes |

All `scored=False`. Additivity re-sums (cost + funding + price == net) hold per cell;
C4's price/funding are exact negatives of C1 (coherent INV). C1 decomposition:
price_pnl −0.36507438395 / costs +0.008032305671 / funding +0.027317931467 —
price-driven loss, costs immaterial, as claimed.

**Falsification recompute (preregistered rule, both bars must hold):** C1 net
−0.345789 < −0.2947 → FAIL (margin −0.051089); MDD 0.419178 ≤ 0.4372 → PASS
(margin +0.018022). Not both ⇒ **FALSIFIED** — identical to `phase1_verdict.json`.

## 3. Gate law — PASS

- `gate_series.json` sha256 recomputed == `e09187f925e761cfabe94e0766ca2104b3b45f5def76fadc061cdbc09c51702d` (both worktrees).
- S0R fold: 52 Monday 00:00Z stamps, **43 ON / 9 OFF** (per-stamp walk of `per_day`).
- The 9 OFF stamps (2025-06-23 .. 2025-08-18): 8 carry book entries with `n_legs=0`,
  `gross_realised=0.0`, `SKIP_NO_SELECTION`, `weights {}`, reason `GATE_OFF`; the
  terminal stamp 2025-08-18 is `FORCE_FLAT`. The first OFF stamp also carries the
  settlement fills of the prior week's book (exact reversals of `prior_weights`) —
  engine-native transition-to-flat. **No NEW book formation at any OFF stamp;
  0 violations in all 4 cells.**
- Enforcement path verified in source: `phase1_sweep.py` refuses to run unless the
  gate-series digest equals the pinned audited digest; `illiq_reg_cell.py` schema-checks
  the series; `gated_plugin.py` binds the full stamp map fail-closed and is a pure
  suppressor (engine-native skip channel) delegating verbatim to the frozen plugin at ON.

## 4. Reproduction — PASS (independently re-hashed)

Repro twin HEAD == `31985732` == `primary_freeze_sha` (the commit the original cells
ran at). Full 64-hex sha256 computed in **both** worktrees, compared as full strings:

- `P1-C1` artifact `51360cab688b624b…0f406a7`, `P1-C2` `880a535684aaa0aa…5745a830`,
  `P1-C3` `803de1cdb66b5aa9…a1029393`, `P1-C4` `955dd1973ebab3f7…cd1558503`,
  shard common `11068057f27bb9e1…c97cc8d` — **8/8 byte-identical across worktrees**;
  prefixes equal the 16-hex values recorded in `reproduction_verdict.json`.
- `phase1_status.json` + `phase1_verdict.json`: structural walk identical modulo
  worktree absolute path + wall-clock (`finished_utc`) — every metric, margin, label,
  verdict identical.
- Artifact self-hashes (`hashes.result_sha256`) match the per-cell logs (4/4).
- Caveat (as disclosed in the source): reproduction proves computational
  self-consistency of the frozen computation, not the economics.

## 5. Labels — PASS

All 9 rows (4 status cells + verdict base + 4 verdict cells) carry the plan SS11 four
labels (`WINDOW_FOLD=S0R`, `OUTCOME_EXPOSED_ANCESTRY`,
`REPLICATION_NOT_PROSPECTIVE` + `scored=False`, `FUNDING_WIRING=funded(scan_2026_a)`),
validated by executing `wiring.py::validate_labels` — all VALID.

## 6. Budget / denominator — PASS

Exactly 4 computed outcomes in the namespace (exactly 4 `results/artifact.json`;
dry-run `non_vacuous=true`, `no_pnl_fields=true`; no other PnL surface; the draft
single-shot replay is pre-cycle read-only input evidence). Cap 4 — no overspend.
Registry row: lifecycle `ACTIVE_HEAVY`, `budget.max=4`, phase text documents
"PHASE 1 COMPLETE: FALSIFIED … Budget 4/4". See NB-1/NB-5 for stale structured fields.

## 7. GO chain — PASS

`GO_RECORDED.json`: exact registered phrase, `received_after_a7_prelaunch=true`,
A7 AUTHORIZED @ `eb86951e` audit_utc 2026-09-24T05:09:04Z; consumption head
`8f476744`. Journal: 05:31:59Z early-GO misclassification → 05:40:00Z two-key
completion (lifecycle → ACTIVE_HEAVY). The early-go incident correction is judged
**honest and complete**: it names its own stale-context error (measured at
`58b93de3`), re-measures (A7 artifact at 05:09:04Z precedes the phrase), and commits
both the error and its repair. Full timeline coheres (host UTC+7): A7 05:09:04Z →
journal 05:31:59/05:40:00Z → failed attempts (stale row pid 15924, started 05:46:31Z,
`reclaim_reason=pid_dead`) → successful sweep 05:50:47–06:00:14Z FINISHED → cells
05:53:09..06:00:13Z → verdict 06:00:14Z → registry 06:02:00Z → repro sweep
06:02:35–06:12:03Z → `0995044c`.

## 8. Launcher-bugs incident — PASS (plausible, no exposure)

Structurally real package-binding failure mode (gated_plugin prepends v11_root to
sys.path; process isolation is the cure, documented in the sweep docstring); the stale
RUNNING lock row exists in heavy-runtime history with `reclaim_reason=pid_dead`, lock
now FREE_PROVEN; both failures precede the first cell (05:53:09Z) and cannot have
produced artifacts; budget 0/4 at the time. No outcome exposure: consistent with all
measured evidence.

## 9. Boundaries — PASS

- S1 `SEALED_UNTOUCHED`; no S1 access surface anywhere in the namespace.
- CHR3F worktree git-clean (head `25504fb9`); read-only absolute-path references only.
- Credential scan: none found (py/json/md/yaml/log).
- Root plan + prereg draft committed clean; no pushes/merges in the audited range.

## 10. Post-freeze drift — judged LAWFUL (NB-3)

The launcher (`bcaa34dc`) was authored after the prelaunch audit (`eb86951e`) and
after GO consumption (`8f476744`), before cells ran. Plan SS10 requires
A7 → owner GO → cells; it does not require the launcher frozen before A7. The gap is
closed by (a) the launcher's fail-closed run-time preconditions (A7 verdict, GO record,
gate digest, lifecycle, budget 0/4, funding coverage), (b) the executed cells
demonstrably implementing the audited conformance description (verified in §3/§5 and
via lock history), and (c) this terminal audit's recompute.

## Non-blocking findings

- **NB-1 (MEDIUM)** Live registry structured fields stale vs its own phase narrative:
  `budget.used=0` (narrative "Budget 4/4"), `go_phrase_state=REGISTERED_NOT_CONSUMED`,
  `head=482dc81b`, `active_heavy=false` — uncommitted A1 write awaiting the two-half
  close normalization. No overspend possible/observed (4 cells vs cap 4, verified from
  artifacts). The close MUST sync these before TERMINAL.
- **NB-2 (LOW)** `identity.window_*` in artifacts reads the FWD template window
  (2025-08-22..2026-08-21) — pre-declared by plan SS5 as NOT window evidence
  (A7-r5 N6); binding window evidence is the 52 Monday stamps inside S0R + WINDOW_FOLD.
- **NB-3 (LOW)** Post-freeze drift judgment — lawful launch (see §10).
- **NB-4 (LOW)** Scan id travels via the `FUNDING_WIRING` label on cell rows rather
  than an artifact.json field; substantive risk excluded by non-zero funding
  (+0.027317931467, exactly negated in INV), pre-compute `verify_funding_scan_coverage`,
  and the M0 live test (20/20, 26208 rows).
- **NB-5 (LOW)** Registry journal has no explicit budget event (0→4); denominator
  truth established from the namespace inventory; normalize at close (with NB-1).

## Bottom line

Terminal claims survive adversarial recompute from bytes. **FALSIFIED** stands on the
preregistered rule; zero confirmation weight on history; no gate variants; family
returns to NOT_PROSPECTIVE diagnostics. Normalize NB-1/NB-5 at the two-half close.
