# A7 TERMINAL AUDIT — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1

A7 terminal auditor: fresh context, independent, read-only. Audits the close;
never repairs. Written 2026-10-01 (UTC) against worktree
`.worktrees/portfolio-composite-12assets-100k-v1/integration` @ `e98f4fdd`
(branch `orca/portfolio-composite-12assets-100k-v1-integration`, chain
feb6f1e7 → c5f3b805 → e98f4fdd — verified), root main @ `b1138e70`
(registry head `e98f4fdd` — verified). All recomputation done with the root
`.venv` interpreter against the committed artifacts; verification scripts ran
from `/tmp` (nothing written into the lane outside the two A7 artifacts).

**Audited verdict (typed, provisional): `POLICY_NO_INCREMENTAL_VALUE`.**

---

## A7_TERMINAL_VERDICT: **CONFIRM_WITH_CONDITIONS**

Counts: **CRITICAL 0 / HIGH 1 / MEDIUM 2 / LOW 2 / INFO 3.**

The evidence supports the typed verdict: every governing bar was
independently recomputed from the arm artifacts and reproduced the published
number and status exactly — **zero status flips**. Partition, accounting,
budget and negative-first-class laws all hold. The conditions below are
recording obligations for the close (errata and disclosure corrections), not
re-runs: no condition, if unmet, could change the verdict type, and none
requires scored budget.

---

## 1. VERDICT LAW — PASS (every bar recomputed; no flips)

Recomputed independently from `diagnostics/stagec/` artifacts +
`TRIAL_LEDGER.jsonl` (not by re-invoking the bar evaluator except where
noted):

- **P1** (from `ARMS/POLICY/metrics.json` vs `ARMS/B1_ALWAYS_ON/metrics.json`):
  net(P) +$603,340.600648 < net(B1) +$688,604.0301 → PnL leg FAIL (strict);
  DD(P) $418,227.968075 > DD(B1) $397,156.85465 → DD leg FAIL. Both legs
  fail → **P1 FAIL, sub-tag P1_B1_PNL** — matches BARS. P1-B0: net(P) > 0 →
  PASS, matches. BARS P1 numbers == arm artifacts (exact equality).
- **P3-clause-1** (from `B4_BATTERY.json` per_seed, 128 seeds):
  obj(P) = −2,449,821.705255; seed objectives span
  [−1,778,186.11, −923,269.09] — **obj(P) is worse than ALL 128 seeds**
  (recomputed count of seeds below policy: 0; threshold 121.6) → FAIL,
  matches. obj(P) itself re-derived from the frozen formula
  (net − 208·SR0_frozen(0.319497)·σ_w(39,649.68) − maxDD = −2,449,821.71,
  matches to <0.01).
- **P3-clause-2** (independent medians over the 128 per_seed values, even-N
  = mean of central order statistics): median net $194,094.571032 and median
  DD $209,634.893984 reproduce exactly; PnL leg passes, DD leg fails
  ($418,228 > $209,635) → **clause-2 FAIL**, matches.
- **P5a DSR inputs from the ledger** (all recomputed exactly):
  N=134 (dedup by arm_config_digest+data_snapshot_digest over 846 rows;
  712 dupes), N_eff=29 (28 distinct (sleeve_id, cluster_id) + 1),
  n_sharpe_legs=55, V=0.024413642118595827, E[max]=2.0593797436671126,
  SR0=0.32177531461622605, SR0_rawN=0.4112327104677144 — all bitwise-equal
  to `BARS.json sr0_inputs`. SR̂=0.073252, skew −0.2058, kurt 5.5733,
  DSR(N_eff)=0.000208, PSR=0.850919, raw-N DSR=1e-06 — all match → **P5a
  FAIL** (>0.95 required). Note the verdict is deflation-robust in both
  directions: PSR 0.851 < 0.95 (fails even with zero deflation) and the
  raw-N DSR (more deflation) also fails.
- **P5b** (recomputed by re-invoking the deterministic pure CSCV core):
  PBO=0.346309 over 12,870 combinations, 70 trials — reproduces exactly →
  PASS, matches (not verdict-critical either way; P5 already fails on P5a).
- **P7** (from POLICY per_fold): Σ per-fold net = pooled net exactly;
  fold-0 share 89.75% > 50% (PnL breach) and 6 folds breach the DD cap
  (dd_f > 2·maxDD/8 = 104,556.992019 — cap value reproduced) → **P7 FAIL**,
  7 offenders, matches.
- **P2a/P2b, P4a/b/c, P6a/b/c/d** (from the respective arm metrics):
  all reproduce published numbers and statuses exactly (P2a PASS, P2b FAIL
  on DD, P4a FAIL DD leg, P4b PASS, P4c FAIL DD leg, P6a FAIL, P6d PASS,
  P6b ΔPnL@×2.0 +$80,927.60, P6c NO_LABEL since policy@×2.0 = +$494,103.59
  ≥ 0).
- **Verdict typing**: per PASS_BARS_V2 E-Law 7 and the plan §7 taxonomy, P1
  (PRIMARY) failing both legs types `POLICY_NO_INCREMENTAL_VALUE`
  irrespective of the other bars; all 8 governing bars are recorded FAIL in
  `failed_governing_bars` exactly as the engine's verdict law prescribes.

No bar's status flips on recompute → no CRITICAL.

## 2. PARTITION — PASS

- Engine fold calendar verified: 8 test folds spanning exactly
  2022-01-07 → 2025-12-26, each fold's TRAIN ending 14 days before its own
  test start (1-week embargo law), warmup 2021-01-08.., sealed tail
  2026-01-02..2026-06-26 structurally excluded (fail-closed raises if a
  fold intrudes).
- All 38 scored-arm journals scanned: every NET_ORDER fill inside its fold's
  window (0 violations across POLICY, B1, B2, B3, B7 spot-verified in
  detail; force-flat `-ff` exits excepted by law). The only timestamps past
  a fold's last Friday are fold-edge force-flat exits at next-session-open
  (max 2025-12-28T22:04Z — the Sunday reopen after 2025-12-26), booked
  inside the closing fold per E-Law 2, **before** the sealed tail. No
  journal row anywhere ≥ 2026-01-02. S1 SEALED_UNTOUCHED (registry + no
  sealed reads; the engine's `_force_flat_fill` forward-search hard-fails
  before reaching sealed_start).
- B3 selection TRAIN-only: `B3_SELECTION.json` frozen 2026-09-30T15:52:11Z
  (before the first test arm at 16:03:26Z), label TRAIN-ONLY, `written_
  before_any_test_arm: true`; candidate windows are the per-fold expanding
  TRAIN windows (2021-01-08..2025-06-20).
- **Disclosed overlap, verified (INFO-1)**: the fold-7 TRAIN prefix
  (through 2025-06-20) — the prefix Stage-B selected the frozen policy and
  the B3 statistic on — overlaps the test windows of folds 0–6. This is the
  SCORED_REPORT §5.2 disclosure, inherent to the frozen pooled E-Law-2
  design, favors the policy, and the verdict is negative under it. Not a
  partition breach against the frozen law; carried as disclosed.

## 3. ACCOUNTING — PASS

Random 3-arm sample (seed 20260929): `POLICY_MO_EURUSD-S013`,
`POLICY_MO_VC2-LVNFAIL-EURUSD`, `B5_CLOCK_GATE`; then generalized to all 38
arms:

- **Per-fill spread-once identity** `spread_once + slip_beyond_halfspread ==
  |fill − mid|·|Δunits| == cross_cost`: 238/238, 30/30, 2673/2673 OK in the
  sample.
- **Book identity** `net == Σ cash_delta_usd − Σ swap_usd` (swap charged
  AGAINST, never income — 0 negative swap rows anywhere): holds for **all
  38 arms**, worst residual $4.3e-6 (journal fields rounded to 6 dp).
  Weekly-equity cross-check `equity_last − $100k == net` holds for the
  sample (positions flat at every fold edge by construction).
- **Cost bills**: journal sums of spread/slip/commission/swap equal the
  metrics `cost_bill_totals_usd` per arm (Δ ≤ 1e-5).
- **F-7 fold-edge force-flat companion**: per-arm totals recomputed from
  `-ff` orders (exit crossing + commission) equal
  `fold_edge_force_flat_cost_total_usd` (e.g. POLICY $6,925.86; B5
  $3,745.38; S013 $7.55); per-fold sums equal totals. Present per arm and
  per fold → P1's PnL leg is readable net of the asymmetry as the law
  requires.

## 4. BUDGET / DENOMINATORS — PASS

- **40/48 identities, listed and counted**: POLICY 1, B0 1, B1 1, B2 1, B3
  1, B5/B6/B7 3, B8 1, P6a pair 2, P6b/c ×2.0 pair 2, P6d pair 2, P8 pairs
  24, B4 battery 1 (E-Law 8 own line, 128 seeded sub-runs 770000..770127,
  seed-list digest f432cdf05f8f9b8d…, 128 SEED dirs on disk) = **40**. The
  engine's ledger-mode `identity_names` list (40 names) matches this
  decomposition exactly.
- **Ledger**: 846/1500 rows (row-ids 1..846 continuous), stop line 1400
  respected; **C-SCORED = 41 rows** (CSCD-W1-0806..0846: 40 identity rows +
  1 BARS_VERDICT row) — published "41 C-SCORED rows" is correct.
- **Observed == published**: all 38 arms' net/DD/tier/digest12 agree
  pairwise across `ARMS/*/metrics.json`, handoff `STAGEC.json
  per_arm_table`, and the SCORED_REPORT §3 table (0 mismatches). Registry
  row at root main: head e98f4fdd, phase text "budget 40/48 identities,
  ledger 846/1500", S1 SEALED_UNTOUCHED (see L-2 for the registry's
  numeric `budget.used`/`go_phrase_state` fields).

## 5. DISCLOSED INCIDENTS — PASS (all 4 evidenced; none contaminated the verdict)

(i) **B3 wiring defect** — evidence: `B3_BEST_SINGLE.log` shows two runs
(16:30:03 defective, 17:22:31 correct re-run after deletion); the committed
B3 artifact is the CORRECT single-leg run — `legs=[EURUSD-S013]` (journal
header + arm config), digest `3fbac7a6…` ≠ POLICY `0f58a25a…`, net/DD/fills
identical to the single-leg identities; exactly one B3 row in the ledger;
selection frozen pre-test (15:52:11Z). **BARS uses the correct B3 run**
(P2b b3_net $1,731.424809 == B3 metrics). See M-2 for the code-digest
corollary of this fix. (ii) **Schedules bug** — ORCHESTRATOR_LOG.txt
16:12:55Z crash (train/test verdict nesting), fix, POLICY re-run 16:20:29 +
repro byte-identical 16:23:38, B1 re-run 16:26:51, schedules OK 16:30:03.
The repro being byte-identical on both sides of the fix proves engine-path
neutrality. (iii) **Two battery kills** — 16:55:27 b4 killed (leaked
semaphores in the log), 17:23:16 resume refused by the append-only journal
law on the half-written SEED770012 journal (JournalError in the log), final
resume 20:14:44 completed 128 seeds with the published medians; 128/128
SEED dirs present. (iv) **P5a N_eff correction** — verified conservative
and verdict-identical: N_eff 29 > 4 raises SR0 (more deflation); at the
original N_eff=4 my own recompute gives DSR ≈ 0.097, still ≪ 0.95 (and PSR
0.851 fails with zero deflation). All four incidents are disclosed in
SCORED_REPORT §5.6; the disclosure inventory is accurate.

## 6. NEGATIVE-FIRST-CLASS — PASS

- No parameter rescue: the policy digest `93077163…cbbbc` verified MATCH at
  entry (VERIFY.json) and constant across all 38 arm journals; winner V3
  frozen at Stage-B with the NEGATIVE TRAIN objective (−$1,054,702.22,
  B-FREEZE row BSTG-W1-0805) — the close is the honest prior's predicted
  outcome.
- No re-run-until-positive: among all 50 scored-class ledger rows
  (B-VARIANT 8 + B-FREEZE 1 + C-SCORED 41) the only repeated
  arm_config_digest is the frozen-policy digest on {B-FREEZE 0805,
  C-SCORED verdict row 0846} — a freeze record and its verdict row, not a
  re-execution. No B-VARIANT rows after the freeze; no non-C-SCORED rows
  after 0806. The only re-executions are the disclosed, determinism-proven
  ones (schedules-fix POLICY/B1 re-run; B3 delete+re-run; B4 deterministic
  resume) and the repro twins (byte/leaf-identical; no ledger rows).
- No post-PnL tuning: no engine-path code touched after the POLICY arm
  froze its digest — the mid-flight edits (B3 leg-subset wiring, P5a
  evaluation-code correction, report polish) are arm-assembly/evaluation
  side, and their neutrality is evidenced (M-2 cross-identity; repro
  1372-leaf identity).

## 7. CLOSE READINESS — PASS

- `TERMINAL_DECISION.md` draft: **not present** (expected — A1 writes it
  after this audit; prior cycles BTC-COMBO6-SCORED-V1 and
  PORTFOLIO-ROUTER-12ASSETS-100K-V1 follow that order).
- Honest-prior chain coherent: Stage-A wide discovery (846-row ledger) →
  Stage-B winner frozen WITH negative deflated objective → Stage-C scored
  evaluation → negative typed verdict, negative-first-class (plan §7 lists
  `POLICY_NO_INCREMENTAL_VALUE` as a first-class terminal outcome). Prior
  audit chain present: A7_PREREVIEW (REVISE_BEFORE_OWNER → remediated in
  PASS_BARS_V2), A7_PRELAUNCH (AUTHORIZED_WITH_FINDINGS 0C/0H/1M/2L/6I),
  A7_DELTA (CONFIRMED).
- Remaining budget (8 identities / 554 ledger rows under caps) is NOT
  needed: no governing bar is `NOT_RUN`; every bar has a final
  PASS/FAIL/REPORTING/NO_LABEL status; the verdict types from P1 alone.

---

## Findings

### HIGH

**H-1 — P8 was realized as single-leg isolation pairs, not the frozen
"WITHOUT leg i" re-runs.** PASS_BARS_V2 §8 freezes P8 as re-running the
policy WITHOUT leg i vs B1 WITHOUT leg i (remaining-legs book), and the
ledger rows describe it that way ("leave-one-leg (policy −X)"); the engine
instead builds `POLICY_MO_{lid}` / `B1_MO_{lid}` with `legs=[lid]` — each
leg ALONE through the machinery (run_scoredc.py:384-385, confirmed at the
run loop `keep = set(spec["legs"])`). Not verdict-changing: (a) P8's status
is FAIL under both readings — under the frozen reading, removing any of the
six legs whose single-leg pairs tie exactly (S013, S046, GBPUSD-S002, S003,
S014, S026) leaves the 11-leg policy still behind B1 on net (P−B1 ≈ −$85k
full-book, and e.g. P_{−S003} ≈ +$387k vs B1_{−S003} ≈ +$473k), i.e. ≥2
breaks → the same FAIL and the same `P8_COALITION` sub-code; (b) the
terminal type is governed by P1's failure regardless (E-Law 7). CONDITION
1: TERMINAL_DECISION.md must record this realization deviation as an
erratum (the P8 sub-comparison is per-leg isolation, not leave-one-out;
the 24 P8 identities are the isolation pairs).

### MEDIUM

**M-1 — Post-commit repro twin trips the byte comparator on the embedded
code_digest only (A1's finding, independently verified and adjudicated).**
Current `REPRO_CHECK.json` (working tree, post-commit twin) records
{journal: true, metrics: false}, while the committed in-flight repro
(e98f4fdd) records true/true. My independent field-diff of
`ARMS/POLICY/metrics.json` vs `REPRO/metrics.json`: **exactly 1 of 1,372
flattened leaves differs — `code_digest`** (5e23dbbd… as-ran vs 8cacead5…
at-commit); journals cmp-byte-identical; I recomputed the committed-tree
digest via the recipe (`run_dry.py:673` hashes all `research/pc12a/*.py`
at run time) and it equals 8cacead5… exactly, confirming the provenance
artifact. Adjudication: (a) the determinism law is satisfied substantively
— engine replay is proven by journal byte-identity plus 1,371/1,372 leaf
identity of results, and the byte standard was met in-flight by the code
as-ran; (b) the comparator's byte standard vs a canonical
(results-excluding-self-referential-digest) standard is a recorded
erratum/condition for the close, not a blocker — but REPRO_CHECK.json as
it stands contradicts the SCORED_REPORT §6 "True/True" sentence until the
erratum is written. CONDITION 2.

**M-2 — The battery does NOT carry one code digest, and §5.6(ii) says it
does.** Embedded digests: 37 arms 5e23dbbd… (orchestrate run 2, 16:20–16:54),
B3 b6189f67… (re-run 17:22 after the wiring fix), committed tree 8cacead5…
(B4 20:14 and bars 20:22 ran post-edits). Engine-path neutrality is
independently provable — B3's numbers equal to 1e-6 the same-leg identities
run under the old digest (B1_MO/POLICY_MO EURUSD-S013), and the repro's
1,372-leaf identity spans the polish — so no bar is touched (E-Law 3's
comparability list — freeze SHA, calendar, kernel digest, tier, fill model,
cash, vehicles — does not include code_digest, and holds). CONDITION 3:
correct the "one code digest" sentence at close to the three-digest
timeline with the neutrality evidence.

### LOW

**L-1 — sr_hat dual value.** `ARMS/POLICY/metrics.json sr_hat_weekly`
0.073158 (internal 208-return series including the initial-capital step) vs
`BARS.json P5a sr_hat` 0.073252 (207 first-differences of weekly_equity).
Both recompute exactly from their own definitions; DSR is 0.000208 under
either. Cosmetic; note in the close.

**L-2 — Registry numeric fields unsynced at root main.** CYCLE_REGISTRY
row: `budget.used = 0` and `go_phrase_state = REGISTERED_NOT_CONSUMED`
while the phase text and the lane evidence carry GO consumed + 40/48.
A1-owned bookkeeping; sync at the two-half close so a stale
"not-consumed" GO cannot be read as authority for further scored cells.

### INFO

**I-1** — Pooled-test-vs-selection overlap (§5.2) verified as disclosed;
fold-7 TRAIN prefix through 2025-06-20 overlaps folds 0–6 test windows;
favors the policy; verdict negative under it.
**I-2** — Fold-edge force-flat exits fill at next-session open after the
fold's last Friday (max 2025-12-28T22:04Z), inside the closing fold, before
the sealed tail — lawful E-Law 2, stated here because the 12-28 timestamps
visualy exceed the "2025-12-26" window label.
**I-3** — B4's first kill left SEED770012 half-written; the append-only
law refused the resume (fail-closed), the final battery is complete
(128/128), deterministic resume disclosed.

---

## Conditions (numbered, for the two-half close)

1. **Erratum — P8 realization** (H-1): TERMINAL_DECISION.md records that P8
   was executed as per-leg isolation pairs (legs=[lid]) rather than the
   frozen without-leg re-runs, with the non-flip analysis; the close never
   cites P8's per-removal numbers as leave-one-out results.
2. **Erratum — repro comparator** (M-1): the close records the two-level
   determinism proof (journal byte-identical; results leaf-identical
   1,371/1,372 with the single differing leaf the embedded run-time
   code_digest) and retires the raw byte-standard for self-referential
   artifacts; REPRO_CHECK.json's current false record is explained, not
   deleted.
3. **Disclosure correction — code digests** (M-2): "whole battery carries
   one code digest" corrected to the three-digest timeline (5e23dbbd / 
   b6189f67 / 8cacead5) with the neutrality evidence (B3 ≡ MO identities;
   repro leaf-identity).
4. **Registry sync** (L-2): budget.used and go_phrase_state updated to the
   consumed state when the two-half close lands (A1).

None of the conditions authorizes scored re-runs; the remaining 8
identities and 554 ledger rows stay untouched by the close.

## Evidence paths

- `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/`
  (BARS.json, B4_BATTERY.json + B4/SEED* 128, B3_SELECTION.json,
  TRAIN_EXTRACT.json, POLICY_SCHEDULES.json, ARMS/ 38 × journal+metrics,
  ORCHESTRATOR_LOG.txt, ORCHESTRATE_OUT.txt, REPRO/, REPRO_CHECK.json,
  VERIFY.json)
- `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/TRIAL_LEDGER.jsonl`
  (846 rows), `SCORED_REPORT.md`, `policy/PASS_BARS_V2.md`,
  `policy/POLICY_FROZEN.json`, `handoffs/STAGEC.json`
- `research/pc12a/run_scoredc.py` (:357-386 arm specs, :1080-1095 leg
  subset, :1368-1390 dsr, :1738-1787 sr0_from_ledger, :1938-2137 bars,
  :658-687 force-flat sealed-tail fail-closed), `research/pc12a/run_dry.py`
  (:673 _code_digest), `research/pc12a/calendar_service.py` (fold law),
  `research/pc12a/cost_kernel.py` (spread-once decomposition)
- Root: `plans/CYCLE_REGISTRY.json` (PC12A row),
  `plans/PLAN_portfolio_composite_12assets_100k_v1.md`
