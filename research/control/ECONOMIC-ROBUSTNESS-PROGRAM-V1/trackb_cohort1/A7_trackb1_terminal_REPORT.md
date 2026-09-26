# A7_trackb1_terminal_REPORT — ERP1-TRACKB-COHORT-1 (fresh-context terminal audit)

VERDICT: CONFIRM_WITH_FINDINGS — 0 CRITICAL / 0 HIGH / 3 LOW. The kill-only
terminal close is lawful, coherent and zero-PnL; the Lead MAY proceed with the
second half of the two-half close (handbook §32) immediately. No finding blocks.

- Lane: trackb-cohort1-a7-terminal (fresh context, quant-auditor). 2026-09-26.
- Measured intake: worktree `orca/erp1-trackb-cohort-1-integration` @ `89fbb150…` (== dispatch_sha;
  clean); root `main` @ `b7f36772…`. No repair; nothing committed; only the two deliverables written.
- Standard audit applied (kill-only close; §22.2 positive-claims strictness would bind only if a
  positive claim existed — none found).

## T1 — Kill legality: CONFIRMED (recomputed from bytes)

- Frozen law chain mechanically produces the kill: plan §8 F-1 (pooled |rho|
  bar ≤ 0.20 immovable, one-shot, exact decision-state representation, before
  any PnL) + freeze `falsifier_order` + `kill_laws` (`KILL_ANCESTRY_RHO_GT_0.20`);
  plan §9.3 makes an F-1 breach terminal. Measured 0.5308 (binary CARRY-BAB)
  and 0.3337 (BASISLV) breach 0.20; the continuous identity makes it structural.
- Independent identity recompute (my own proxy, not the lane's code): from
  `data_local/funding/BTCUSDT/funding.json` (6,819 settlements, sha256
  `0fb1b92f…` = manifest and freeze pin) I rebuilt the trailing-90d settled-mean
  × 105 proxy under settle_time ≤ T, window [t−90d, t] inclusive. Max |diff|
  vs artifact `ec_bps` = **0.0 over all 318 epochs**; continuous Spearman =
  **1.0 exactly**. FN-1's estimator IS the dead carry observable.
- Grid: artifact = **318** weekly Friday-00:00 epochs, exact 7d steps,
  **2020-07-24..2026-08-21** — the µs-stamp fix landed. Ground truth verified:
  raw 2025-06 spot zip stamps are µs, 2024-06 are ms; loader `_norm_ms`
  normalizes. Manifest file sha256 = `f6028626…` matches the freeze pin.
- Recomputed gate facts match `BATTERY_RESULT_v2.json` exactly: fires at
  C*=45/50/60 = 221/201/166; non-overlapping 35d holds = 42; last-6m fires = 2
  (2026-08-14 ec 47.91, 2026-08-21 ec 49.43); min ec|fire 45.07 > max ec|flat
  44.91. M-1..M-5 re-executed read-only, byte-identical verdicts (M-2 20/318;
  M-3 0/318; M-5 0/50, 22 at-T; F-3 Jaccard 0.471 vs 0.467). All hash pins
  verify: 5 council/A7 report prefixes, F-0 ruling `310fe03e…`, both plan shas
  at e02bf36f.

## T2 — Zero-PnL claim: CONFIRMED

grep across scripts + artifacts + ledger: no net_pnl / profit-factor / returns /
equity / drawdown / sharpe anywhere. `trial_ledger.jsonl` has exactly 2 rows
(`NOT_SCORED_FALSIFIED` M1-ANCHOR KILL_ANCESTRY_RHO; `NOT_RUN_HOST_KILLED` DTX);
no PnL fields exist; the scripts structurally contain no accounting path.

## T3 — Scope discipline: HELD

Executed = GO-1 receipt scope exactly: registration (sha `cf3cf0b8…`, 0/7),
freeze (v1 + FN-1 pins), bounded staging under the heavy lock (manifest
committed, pins same-commit per P-19), coverage censuses (funding/perp/spot
zips; bookTicker probes 4/4 ABSENT → spread fail-closed to DECLARED+stress,
  never fabricated), falsifiers F-0/F-1/F-2 complete with F-3/F-6 as pre-PnL
  facts; F-4/F-5/F-7 moot under the terminal kill (plan §9.3). Forbidden list
  held: GO-2 REGISTERED_NOT_CONSUMED; GO-3 never existed; S1 SEALED_UNTOUCHED;
  no orders; terminal commit touches only the cycle namespace; branch local,
  NOT pushed/merged (measured); workers 0; lock FREE_PROVEN at audit.

## T4 — Ledger/verdict coherence: CONFIRMED

CYCLE_VERDICT (0/7 cells, 0 PnL, REJECT_ALL — umbrella §9 vocabulary) ↔
state.json (0/0/0, TERMINAL_REJECT_ALL_PENDING_CLOSE, S1 sealed) ↔ events.jsonl
(GO1 → register → staging → F-0 → battery → F-1 kill → TERMINAL_DRAFT) ↔
registry row (budget 0/7 used 0, S1 SEALED_UNTOUCHED). Registry phase/head is
stale at `b680c5d` by design — that IS the pending close half, anticipated by
its write_token. Not an incoherence.

## T5 — Incident handling I-1..I-4: HONEST

All four recorded (battery §5 + events), none silently repaired: I-1 staging
mkdir (zero exposure); I-2 µs-stamp silent truncation caught by the skeptic's
independent count, loader fix disclosed, series regenerated; I-3 two fixture v1
design defects re-derived to frozen semantics, v1 verdicts voided, v2 governs;
I-4 prose corrections propagated to verdict/battery/ledger/commit message.
Stale numbers ("0 fires", "34<40", 232/2024-12-27) survive ONLY inside incident
narratives marking them wrong; governing numbers are the corrected set, which
my recompute confirms.

## T6 — Reproduction: SUFFICIENT (ruling)

Plan §9.3/§11 requires the detached-twin reproduction BEFORE any GO-3 request;
handbook §22.1 reproduction proves self-consistency of scored records. No GO-3
was requested, no S1 touched, no scored cell exists — there is no positive
result to reproduce, so the full twin is not owed at this close. The
kill-carrying computation was nonetheless verified independently TWICE: the
skeptic's byte-exact machinery replay (1.14e-13) and this audit's
from-raw-bytes recompute (diff 0.0). Ruling: sufficient.

## T7 — Close readiness: half 1 DONE, half 2 PENDING, nothing blocking

Branch-side terminal chain landed at 89fbb150 (verdict + battery report + 2
ledger rows + artifacts + events + state). Pending per handbook §32: registry
TERMINAL (head measured via researchctl), FAMILY_FAILURES append (reopening:
non-funding-level PIT axis, or dated measured cost-regime break), MAP bullet,
LESSONS (µs-stamp lesson), HYPOTHESIS_LEDGER P-9 row, projection + doctor
verify, router docs. No owner decision owed; program stops per charter §7
absent new information.

## Findings

- **F1 (LOW)** CYCLE_VERDICT's two-half checklist omits the HYPOTHESIS_LEDGER
  P-9 denominators row that handbook §32 requires. Remediation: include the
  P-9 row (0/0 scored, kills ledgered, 0 looks) when executing the close half.
- **F2 (LOW)** "ZERO gaps" phrasing (events/verdict/commit) is
  quantization-sensitive: measured 2,169 inter-settlement gaps exceed 8h by
  ≤1 ms (.001-stamp residue), max 8.000013h — no true data gap, PIT unaffected.
  Remediation: in close-half FAMILY_FAILURES/MAP prose say "no gaps beyond the
  ≤1 ms .001-stamp residue (max 8.000013h)". Do not rewrite branch evidence.
- **F3 (LOW)** Binary CARRY-BAB 0.5308 is cited in CYCLE_VERDICT/ledger
  without its grid qualifier; the governing authority (SKEPTIC_F1_RHO_VERDICT
  §1) states it was computed on the pre-fix 232-epoch artifact. My recompute
  on the corrected 318-epoch grid gives **0.658** — same direction, still a
  breach; the continuous identity (1.0, grid-invariant) alone carries the kill.
  Remediation: cite the grid when writing the FAMILY_FAILURES row; no branch
  repair required.

## Coverage statement

T1–T7 recomputed from bytes (fixture script re-executed read-only; rho identity
rebuilt from raw funding bytes; hashes, pins, git chain, locks, registry all
measured). No hidden positive claim found (owner-facing statement is a
falsification-first claim, correctly labeled). No CRITICAL/HIGH finding; close may proceed.
