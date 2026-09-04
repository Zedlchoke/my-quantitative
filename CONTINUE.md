# CONTINUE.md — V10R → V11 ENTRY STATE

Read `PLAN.md` completely. It is the fresh-context authority.

## Measured entry state

- Prior sprint V10P-R closed `V10_BLOCKED_PRELAUNCH` with budget 0/3
  consumed (now 0/9 under the owner amendment) and denominator 117.
- Full record: `research/control/v10p_run/terminal_closeout_v10p.json`;
  integration `orca/v10-integration@86b7274`, clean, pushed to GitHub.
- The reusable adapter pipeline (BG1–BG6, G15, F2, G17, H08 12–20) is built,
  accepted (52-test matrix) and frozen at `W2=d61a483` with detached
  `exec-v10-R1b`/`exec-v10-R2b`. Do not rebuild any of it.
- Single remaining HIGH: `G05_COVERAGE_SHORTFALL` — staged bars end 21.5 h
  before the preregistered window end `2026-08-21T00:00:00Z`; the daily-close
  builder silently synthesizes the stale tail instead of failing closed.
- Owner directives (2026-08-28): **Option A** (fetch the missing data, window
  unchanged), **24 h clock**, second wave = **2 families / 6 cells**
  (authorized ceiling now 3 families / 9 cells total).

## Immediate critical path

1. Go-live: record the 24 h deadline in
   `research/control/v10r_run/heartbeat.json`.
2. R0: extend staged bars (and funding if short) through the window end using
   existing download infra; make `build_daily_closes`/coverage fail-closed
   with a regression test pinning the V10P defect; re-stage + byte-verify.
3. R1: freeze W3; detached `exec-v10-R1c`/`exec-v10-R2c`; full suite alone.
4. R2: fresh A7 prelaunch audit on W3; launch only on authorized verdict +
   fresh resource probe ≥1 heavy worker + ≥120 min left.
5. R3/R4: M01 anchor → neighbor → C2, serial; reproduce 3/3 from R2c; family
   terminal science; write lessons into the register.
6. V11: blinded proposals → novelty + rescue → freeze 2 families → implement
   through the adapter → prelaunch audit → 3 cells each → reproduce → close.

## Boundaries

Unchanged from PLAN §10. Honest evidence first: REJECT_ALL, BLOCKED,
INCOMPLETE are valid outcomes; no tuning on observed PnL; no S1, equity
scored runs, paper/testnet/live, orders; historical trees preserved; push
only on owner instruction.

## First fresh-thread report

Return measured UTC, deadline remaining, integration HEAD, budget, and the
R0 plan; then continue without repeated GO.

## Host handoff — 2026-08-28T00:56Z (A1, mid-sprint, machine move to 16GB host)

- R0 DONE: D1 fail-closed coverage (`78d77e1`) + D2 restage verify (`1a66e90`)
  merged; D2 premise correction: staged tree already covers window end
  (filename-range artifact caused the V10P stale-tail reading); BTC/ETH
  duplicate-parts flag routed to R2 A7 recompute. Fixtures aligned per lesson
  (d) (`c968b5c`).
- R1 DONE: full suite alone **1283 passed / 1 skipped / 0 failed**;
  **W3 = `2d5c30dcd32e4e3bfa02fe7d41de8804212327a5`** (code-identity vs suite
  SHA verified); exec `R1c`/`R2c` detached at W3, staged read-only,
  byte-identical 50/50, manifests 27+20 all_match.
- Budget 0/9, denominator 117, deadline **2026-08-29T00:05:50Z** absolute.
- NEXT (on the 16GB host): clone `orca/v10-integration` at W3, migration bundle
  `/Users/hoangminhlong/v10r_migration_bundle/` (README inside) → R2 fresh A7 +
  fresh `--probe-resource` (gate `measured_safe_cap ≥ 1`) → R3 3 M01 cells
  serial → R4 reproduce → V11 wave. Open questions for A7 are listed in
  `research/control/v10r_run/r1_freeze_W3.json`.
- Old host's `exec-v10-R1c`/`R2c` are machine-local: recreate detached at W3 on
  the new host per `worktree_manifest_v10r.json`; do NOT carry stale trees.

## Owner amendment — 2026-08-28 (ceiling)

Heavy-worker ceiling raised to **3**, scoped ONLY to: R4 reproduction
processes, V11 cross-family chains (within-family serial preserved), V11
reproduction waves. **R3 M01 cells stay serial ceiling=1.** G17 floor
`min(ceiling, measured_safe_cap)` unchanged; measured 0 still = no launch.
See `research/control/v10r_run/owner_amendment_ceiling_v10r.json`; A7 audits
against this amended contract.

## Host-3 bootstrap + R2 remediation — 2026-08-28 (A1)

- Host 3 = Windows 11, 31.86 GB RAM measured. Migration bundle ABSENT →
  staging rebuilt by re-fetch (Option A); composition after the A7-remediation
  pass: 24 digit-exact bar parts + 20 funding + 3 instrument defs. EVERY
  resolved value verified digit-exact vs live fapi on all 9 consumed fields
  over prewindow+window (`host3_full_window_8field_report.json`, 20/20 PASS).
- A7 first verdict `V10_BLOCKED_PRELAUNCH` (B1 non-digit-exact dedupe picks on
  BTC/ETH, B2 POSIX-bound suite, B3 manifest provenance, B4 G17 port labels,
  B6 suite side-effect) → remediated: non-digit-exact parts excluded from
  staging, exec trees re-staged + byte-verified 47/47 (`stage_verify_v10r_
  R1c_R2c_host3.json` v2), worktrees re-smudged to blob bytes (core.autocrlf
  false), `resource` import shim for collection, G17 port artifact corrected
  (`measured_safe_cap=81`; R3 final=1, R4/V11 final=3 per amendment), golden
  vector file restored after each suite run.
- Suite on host 3 (R1c, alone): **1259 passed / 16 failed / 8 errors / 2
  skipped** vs freeze-time macOS 1283/0/1 (same blobs). Residue clusters in
  V9-era process-control/fault-injection and audit-tooling tests
  (POSIX process-group/signal semantics, path idioms) — the adapter/M01/panel/
  publish execution path for R3 is fully green. Re-audit by A7 pending.
- Known host-3 deviations for every audit: PEPE/BOME volume fixed-point scale
  1e8 (loader reads live*1e-8 vs *1e-7 elsewhere) — verified NOT material to
  M01 (scale-free within-symbol ratio); float64-to-int64 quantization ~1e-16
  on 6 residual rows eliminated by the Decimal-exact rewrite.
- R3 data-feed pin: bars fed to M01Plugin use the panel dedupe rule
  (lexically-last part wins); `hyp_a8_m01.read_bars_15m`'s strict duplicate
  rejection is recorded as inapplicable to the inherited overlap layout.

## R3/R4 terminal — 2026-08-28 (A1) — M01_FAMILY_REJECT

Anchor published (denom 1): net −578,745.7 scaled, expectancy −1,585.6/day,
PF 2.4e-08, 0/3 folds positive, loss ≈ 100% costs (gross ≈ 0). Neighbour
computed, same profile (−515,951.9) but UNPUBLISHED — frozen publisher's
trial key cannot express M01-N (arm_config_id=control_mode collision with
M01-A; neighbour_mode outside the key). Fail-closed, escalated to owner.
C2 placebo published (denom 2): −607,353.9 ≈ anchor → zero incremental flow
information. R4 reproduction from R2c: ALL_MATCH 3/3 (3 concurrent per owner
amendment; only each tree's own absolute paths differ). Stage-A: family
**REJECT**. Budget 2/9 published (+1 unpublished documented); denominator
117+2=119. Full detail: `research/control/v10r_run/family_terminal_m01.json`.
Owner directives standing: announce results (ELI5) → push → WAIT for owner
response before starting V11.

## V11 intake delta — 2026-09-02 (A1, bootstrap merge)

- V11 sprint opened on this branch per owner PLAN `b8876ef8e0f7dd235d66f5cae5bfd8fd9034147f`
  (= `main`/`origin/main` at bootstrap; owner-committed). V10 terminal truth above is
  preserved verbatim; `orca/v10-integration@e6fa2b1` remains the V10 terminal authority.
- Measured intake: merge-base(owner, V10 terminal) = `e5b0bab`; root checkout on branch
  `forex` at `b8876ef` with owner-dirty `M PLAN_forex.md` (owner space, preserved, untouched);
  published ledger denominator **119**, observed scored denominator **120** (V10 M01
  neighbour, computed-unpublished contract gap) — reconciliation is P1/A2 append-only work
  and gates scored launch until A7 approves.
- V11 budget **0/12** (4 families x 3 cells ceiling), S1 untouched, no paper/testnet/live.
- Standing owner directive (2026-09-02): A1 runs all safe local phases
  (P0→P1→L0/D1→D2/D3→freeze→implement→QA→A7 prelaunch) and STOPS before the first scored
  cell (Phase E); scored execution moves to a stronger owner machine. `V11_BLOCKED_PRELAUNCH`
  on this host's measured resource cap is an acceptable honest state at handoff.
- V11 control plane: `research/control/v11_run/` (run_contract, state, heartbeat, event_log,
  worktree_manifest, v10_terminal_intake, denominator_reconciliation=PENDING, lessons_register).

## V11 deadline close — 2026-09-02T23:5xZ (A1) — V11_INCOMPLETE_NOT_PROMOTABLE

Clock expired before selection freeze; closed honestly per PLAN 4.1. Budget
**0/12** (zero scored cells, zero scored artifacts, S1 untouched, no push, no
main merge). Branch `orca/v11-integration` carries the full sprint state.

### Done (all committed on this branch)
1. Bootstrap `0a96bf2` = owner plan `b8876ef` x V10 terminal `e6fa2b1` merge
   (PLAN.md=V11 owner; CONTINUE.md=V10 truth+delta); 54/54 targeted PASS.
2. P1 `V11P_REPAIR_SHA 7566ca2`: A2 identity v2 + M01 append-only
   reconciliation (119 published / 120 observed, mechanism implemented,
   A7-approval still required before any scored launch); A3 schedule-only
   cost gate (frozen floors); A4 exact-arm dry-run. Full suite **1367
   passed / 1 skipped, tree clean** (gate V11P_FULL_SUITE).
3. L0 `0684914`: literature packet (Pyo&Jang 2026 FRL; Grobys 2021 JIFMIM;
   Ozdamar 2021 FinInnovation; Binance docs) + 2 seed briefs, hashed.
4. D1: 6 outcome-blind proposals (A5 `e7f6f7f`, A6 `9a340c1`, A8 `d9e16c0`)
   — three independent lanes converged on 2 mechanism groups:
   ILLIQUIDITY_PREMIUM and OI_POSITIONING. Pool manifest `903ed49`.
5. D2-A9-F `bc4bd4c`: staged snapshot has **NO OI series (0/20 symbols)** ->
   OI group UNAVAILABLE fail-closed; seeds DEF/LOT schedule-PASS; ILLIQ PASS
   (canonical `a8_prop1`; a5_prop1 runner-up; a6_prop1 breadth FAIL: only 9
   symbols above DV median -> quintile = 1 name/leg, HIGH flag).
6. A1 prewindow rho evidence (`research/control/v11_run/
   a1_prewindow_rho_evidence.json`): DEF vs LOT **0.565 FAIL(<0.35)** — the
   two owner seeds cannot be co-frozen; LOT vs ILLIQ 0.310 PASS; DEF vs
   ILLIQ 0.482 FAIL; all vs rejected ancestors PASS (<0.50).

### NOT done / next thread (stronger machine welcome)
1. **OI staging is owner-AUTHORIZED but NOT executed** — see
   `research/control/v11_run/owner_amendment_oil_staging.json`
   (data.binance.vision daily metrics, 2025-07-01..2026-08-21, 20 symbols,
   /oi_data/ untracked; openInterestHist API cannot serve history).
2. **A7-N novelty audit incomplete** (two subagent timeouts; uncommitted
   partials on `orca/v11d-a7-novelty`). Then D3 freeze with the evidence:
   expected dispositions — LOT seed eligible, DEF seed orthogonality-blocked
   (BLOCKED_PRE_SCORE) pending A7-N, ILLIQ eligible, OI pending staging
   re-audit. If OI passes: freeze 1 seed + 2 discovered, budget 9 cells.
   If not: `V11_BLOCKED_SELECTION_INSUFFICIENT` per PLAN 10 (no threshold
   changes).
3. Then I -> Q -> A7 prelaunch -> scored cells ONLY on the owner's stronger
   machine (this 8GB host measured_safe_cap=0). Deadline handling per the
   fresh thread's own go-live; the expired clock must NOT be extended.

## V11 prelaunch terminal — 2026-09-03 (A1) — V11_LAUNCH_AUTHORIZED, awaiting strong host

A7 prelaunch audit (`862934ab`, independently recomputed): 13/13 PASS,
0 unresolved HIGH/CRITICAL. W11 = `befbd20`; exec/repro detached trees
`.worktrees/v11/{exec,repro}-v11-1` staged byte-identical (91 files,
`staged_manifest_w11.json`). Full suites: V11P 1367/1, Q **1421 passed /
1 skipped**, both tree-clean. Budget **0/9 eligible** (0/12 plan; DEF seed
BLOCKED_PRE_SCORE, 3 slots unused). Zero scored cells; S1 untouched; no push;
no main merge.

### Strong-host launch conditions (A7 SC1–SC6)
SC1 fresh probe measured_safe_cap>=1 on the launch host; SC2 byte-identical
re-staging with hash-equal exec/repro manifests; SC3 launch-time manifest
hash check + W11 tree identity; SC4 verify the 9 cells against the frozen
arm_config_digests (selection_freeze.json), first-publish + replay-zero;
SC5 Stage-A concentration gates bind (OILEV 1-name/leg risk), controls
published, stress cells run; SC6 budget 9 cells max, DEF stays blocked.

### Phase E execution order (on the strong machine, A1 authority)
Per family serial: anchor -> neighbour -> causal control; up to 3 families
concurrent per fresh probe; every computed cell counts in the observed
denominator (120 + n) even if publication fails; A1 sole publisher; no
pytest while a scored worker runs; then R: reproduce all computed cells from
repro-v11-1 equivalent, terminal A7 audit, family verdicts per PLAN 15.

## V11 terminal + V11R reconciliation — 2026-09-03 (A1)

V11 closed terminal at `orca/v11-integration@df18f53` (pushed): sprint verdict
**V11_REJECT_ALL**, A7 terminal audit wave-1 10/10 PASS + wave-2 **APPROVED,
0 FAIL**, reproduction **ALL_MATCH 33/33** (LOT 3×5, ILLIQ 3×6), budget 6/9
eligible cells published (LOT REJECT 7 gates; ILLIQ REJECT on sole gate
positive-fold concentration 0.7055 > 0.50; OILEV BLOCKED pre-score 52/52 cap
breach; DEF seed blocked pre-score, 3 slots unused). Logical denominators
**125 published / 128 observed**; S1 SEALED_UNTOUCHED; owned workers 0; no
paper/testnet/live; push COMPLETE, no main merge, no history rewrite.

V11R metadata-only reconciliation (PLAN_crypto.md §5) applied on branch
`orca/v11r-integration`: state/heartbeat/terminal_report stale terminal
claims corrected (P0_IN_PROGRESS verdict, ILLIQ-computing, archive-wait,
old remote tip a335e385, pending-push, obsolete next actions), MAP.md and
this file updated, one append-only event row added. No scientific byte
changed — immutable artifact hashes pinned in
`research/control/v11_run/v11r_reconciliation_intake.json` and asserted by
`tests/test_v11_terminal_metadata.py`. Independent A7 metadata audit pending;
`V11R_TERMINAL_SHA` freezes only after `V11R_METADATA_RECONCILED`.

**Next safe action:** V12 control plane per `PLAN_crypto.md` from
`V11R_TERMINAL_SHA` (125/128, budget 0/9); V12 scored execution requires an
explicit owner `GO V12 SCORED EXECUTION`.

## V12 strong-host E0 blocked — 2026-09-04 (A1)

Owner issued `GO V12 SCORED EXECUTION`; strong-host E0 ran on the Windows
execution host (`ROYAL`) at integration tip `474d811` (W12 `f0799cae`
verified present and ancestral; exec/repro trees created detached at W12,
clean, nothing staged). E0 verdict **FAIL, zero scored cells, budget 0/9**,
clock never started. Two independent blockers:

1. `V12_E0_STAGING_ARCHIVE_ABSENT` — `v12-staging-W12-f0799cae.tar.gz`
   (expected sha256 `dc760859...ed8`) is not on this host (Downloads,
   profile, D:, recycle, GitHub all checked). 83/90 staged files exist
   locally byte-exact vs `a3_staging_manifest.json`; the 7
   `funding_20240820_20260821` S0R funding bundles are absent, so the
   equal-twin 90/90 re-verification (A7 launch condition 1) cannot pass.
   Partial staging was deliberately NOT written.
2. `V12_BLOCKED_EXECUTION_DRIVER_ABSENT` — W12 contains no complete scored
   execution entrypoint for the V12 families. The only cell drivers in W12
   are the V10R M01 and V11 drivers, both hardwired to their own cycles;
   the V12 plugins declare "never scores" and the audit modules are
   NO-PnL evidence-only. Per strong-host runbook §5: no ad-hoc post-freeze
   scorer; a driver requires a new code freeze + independent A7 delta audit.

Passed gates measured on this host: resource probe `measured_safe_cap=3`;
6/6 arm digests recomputed from W12 code match `selection_freeze.json` v2;
portable empty-ledger package verified and seeded (`e3b0c442`).
Denominators 125/128, S1 SEALED_UNTOUCHED, workers 0, no deployment, no push,
no main merge. Evidence:
`research/control/v12_run/stronghost_e0_royal_20260904.json`.

**Next safe action:** owner re-transfers the staging archive (verify
`dc760859...`) AND authorizes a V12 driver lane (implement the scored-cell
driver from the frozen V10R/V11 pattern, integrate, freeze `W12R`, independent
A7 delta audit) before any scored cell.

## V12 TERMINAL: V12_REJECT_ALL — 2026-09-04 (A1)

Six frozen cells computed, published exactly once, reproduced 6/6 ALL_MATCH
from the detached reproduction trees (budget 6/9; logical denominators
125/128 -> 131/134; S1 SEALED_UNTOUCHED; workers 0; no deployment). Clock
closed within 12h. Terminal report:
`research/control/v12_run/terminal_report_v12.json`.

- OILEV-V2 **V12_FAMILY_REJECT** — anchor -0.821 (PF 0.717), neighbour
  -0.845, MDD 82%; inverted control +0.758 (PF 1.360): falsification
  evidence only, never a candidate (V11 LOT pattern).
- BAB-LOWBETA **V12_FAMILY_REJECT** — anchor -0.0199 (PF 0.992), neighbour
  -0.087, 1/3 positive folds, MDD 69%; inverted control beats the anchor.
  Low-beta long/short dies after taker costs + funding.
- ILLIQ replication stayed BLOCKED_DATA (3 slots unused).
- TECHABORT x1 (driver preflight digest bug) — zero budget, forensic on
  file; W12R2 fix audited by A7 (both LAUNCH_AUTHORIZED verdicts).

**Next safe action:** none pending for V12; no S1 candidate locked. Await
new owner instruction.

## V13 terminal (2026-09-04)

V13 closed **V13_REJECT_ALL** (A7: V13_TERMINAL_APPROVED_0_FAIL).
Branch `orca/v13-integration`, W1 c0d0673, W1R2 d0726645. 6/6 cells published,
6/6 reproduced ALL_MATCH, budget 6/9 (ILLIQ slots unused). OILEV-successor
OILEV... both selected families REJECT: OITD anchor -0.2854 (PF 0.879, MDD 30.5%),
LIQEPIS anchor -25.33 (driver tick-size parameterization defect, adjudicated
verdict-invariant; price-only -0.31). Data Fusion V1 core adopted byte-identical
(c6a0576e) with decision-time availability pin. Denominators now 137 published /
140 observed logical. No S1 candidate locked. S1 SEALED_UNTOUCHED, workers 0.
Terminal report: research/control/v13_run/terminal_report_v13.json.
