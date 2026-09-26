# A7_TERMINAL_REPORT — SRLV-CX-C1 — CONFIRM_REJECT_ALL

- Lane: `a7-terminal`, role `a7-independent`. Date: 2026-09-26.
- Worktree verified: `.worktrees/srlv-cx-c1/integration`, branch
  `orca/srlv-cx-c1-integration`, HEAD `2940a113…` at lane start (measured).
- Independent: the implementer's engine (`scripts/engine_m1.py`) was NOT
  imported or run. All Task-1 numbers below come from two minimal
  re-implementations of the frozen anchor law written by A7 from the freeze +
  PROPOSAL_P1 §5/§6 + impl-pins, reading ONLY raw staged bytes under
  `data_local/` (80 monthly 1h-kline zips per pair, 0 gaps, 58,440 bars,
  2020-01-01..2026-08-31; BTC settlements from `funding_events.parquet`
  (7,643 rows), ETH from `fundingRate_um_ETHUSDT` zips col0 (7,305 rows)).
- Read-only on all audited artifacts; touched only this file +
  `HANDOFF_a7_terminal.json`. No commit.

## VERDICT: **CONFIRM_REJECT_ALL**

The claim under audit is CONFIRMED on every element: M1 SETTLE-RESOLVE dies at
dev gates on BOTH pairs under an independent re-implementation; 6/18 scored
cells observed (exactly); 0 OOS looks; S1 untouched; sealed/prospective NOT
consumed; freeze chain intact; kill laws applied as frozen with no weakening.
Five non-blocking findings recorded (§6) — none blocks the verdict.

---

## 1. Independent recomputation (Task 1)

A7 wrote its own code twice, to separate (a) the strict freeze-literal reading
from (b) the implementer's documented tie-handling conventions, and to prove
the verdict is invariant across both.

- **Variant A — strict freeze-literal** (exit (iii) at the open of the last
  bar whose close-time ≤ S_next−2h, exactly as the freeze sentence reads;
  fold-straddling trades force-flattened; disaster extreme = min/max of
  low/high over s..c; breakdown-buffer ATR24 ending at the sweep bar).
- **Variant B — convention-aligned** (settle-exit at the open of the NEXT bar
  after the last close ≤ S−2h — i.e. the uniform decision-at-close /
  fill-at-next-open convention used everywhere else in the law; fold
  straddlers DROPPED; disaster extreme = sweep-bar extreme; stop/breakdown
  ATR24 at the trigger bar). Variant B was derived only after reading the
  engine source to identify conventions; the numbers are still A7's own code
  and own data path.

### A7 numbers — anchor N=6, base cost ×1.0 (RT = 10 bps + 2 adverse ticks)

| Metric | BTC (A7-B / A7-A) | impl | ETH (A7-B / A7-A) | impl |
|---|---|---|---|---|
| n trades | **1,482** / 1,562 | 1,482 | **1,518** / 1,593 | 1,518 |
| n candidates | **2,761** / — | 2,761 | **2,936** / — | 2,936 |
| net bps | **−25,831** / −16,457 | −24,955 | **−33,363** / −19,708 | −33,515 |
| PF | **0.642** / 0.712 | 0.651 | **0.635** / 0.724 | 0.634 |
| folds F1..F4 | all negative / all negative | all negative | all negative / all negative | all negative |
| long / short | 755/−17,140 · 727/−8,691 (B); both neg (A) | 749/−16,645 · 733/−8,311 | 788/−19,321 · 730/−14,043 (B); both neg (A) | 781/−19,325 · 737/−14,190 |
| net @×1.5 | **−33,292** / −24,321 | −32,416 | **−41,099** / −27,825 | −41,250 |
| net @×2.0 | −40,753 / −32,185 | −39,877 | −48,834 / −35,942 | −48,986 |
| A5 inverted | **−4,013** / −14,998 | −4,889 | **+2,422** / −12,761 | +2,573 |
| exit mix (B) | settle 960 · reclaim 522 · stop 0 | — | settle 1,021 · reclaim 497 · stop 0 | — |

Neighbors (A7-B): A2 N=3 n **2,407 / 2,433** (impl exact), net −44,567 / −43,478
(impl −44,558 / −43,320); A3 N=10 n **937 / 980** (impl exact), net −17,423 /
−18,480 (impl −17,418 / −18,622). A4 +4h placebo negative both pairs under both
variants (A7-B not rerun for A4; A7-A: BTC −5,405 n=314, ETH −9,200 n=341);
ungated clock negative both pairs (A7-A: −20,995 / −26,673).

**Agreement statement.** Under convention-aligned Variant B, A7 reproduces the
implementer's trade counts EXACTLY (1,482/1,518; candidates 2,761/2,936;
neighbors exact) and net within 0.5% (ETH) to 3.5% (BTC) — the residual is
boundary-bar tie-order noise, not a law difference. Under strict-literal
Variant A the anchor is LESS negative but every verdict-relevant fact holds
under BOTH readings:

1. **G1 FAIL both pairs** (net < 0 @×1.0) — this alone kills the identity
   per-pair and under BOTH-pairs adjudication.
2. **G2 FAIL** (PF 0.64–0.72 < 1.20), **G3 FAIL** (0/4 folds positive — all
   eight fold values across both variants negative), **G4 FAIL** (@×1.5
   negative under both readings).
3. **Both directions negative** per pair under both readings.
4. **K-CTRL fires under both readings**: inverted out-earns the anchor on both
   pairs (BTC −4,013 > −25,831; ETH +2,422 > −33,363 in A7-B; likewise A7-A);
   ETH inverted is POSITIVE under both.
5. Placebo windows, ungated clock, and N=3/10 neighbors all negative → G6a/c/d
   PASS and moot; the anchor's death is real, not a window or level artifact.
6. **G5 PASS** (power 749/733 and 781/737 ≥ 100/direction/pair — matches impl).
7. **Funding baselines sane, measured from raw grids**: BTC 7,870.5 bps over
   the 6.667-year window = **11.81 %/yr** (freeze declared 11.80; impl
   baseline 7,705.6 bps — within ~2% of A7's raw sum, window-boundary
   convention); ETH 9,304.3 bps = **13.96 %/yr** (freeze 13.95; impl
   9,125.2). G7 therefore crushes the anchor under any reading.

Convention deltas identified and disclosed (not violations): exit (iii)
off-by-one bar (freeze sentence vs uniform decision→fill convention — both
flat by settlement, F-P1A-FLAT 0 violations); fold straddlers dropped instead
of force-flattened; disaster-stop extreme = sweep bar (and it never fires under
either reading — the opposite-reclaim exit threshold always binds first, so
exit (ii) is a pinned-but-redundant safety). None of these can rescue the
anchor; the only law that could rescue it (anchor net > 0) is false under both
readings.

## 2. Counters and law (Task 2)

- `trial_ledger.jsonl`: **13 rows** = 5 pre-outcome (4 council adjudications +
  1 freeze, all `outcome_viewed: false`, `scored_cells: 0`) + **6 scored
  cells** (A1, A2, A3, A4, A5, A6 — exactly six, all `observed: true`) +
  1 battery + 1 cohort_verdict (`REJECT_ALL`, `oos_looks: 0`,
  `s1: SEALED_UNTOUCHED`, `prospective_consumed: false`). Pooled A1 row is
  internally consistent (n=3,000 = 1,482+1,518; net −58,470.4 = sum of the
  two pair nets; PF list = per-pair PFs).
- **Scored cells observed = 6, not more.** The ±4h placebo sub-variants are
  identical by the 8h grid (disclosed) and counted as the single A4 cell.
- **No holdout/OOS/prospective artifact exists anywhere** under the cycle tree
  (file inventory + keyword sweep hit only prose asserting the negation).
  C2 binding conclusion stands: history OOS = NONE for all four pairs at 1h;
  cohort OOS = prospective post-freeze, never opened.
- **S1 untouched**: registry `s1: SEALED_UNTOUCHED`; owner packet scopes GO-2
  "NOT GO-3/OOS/shadow/FX"; no sealed-read code paths in engine/driver.
- **GO-3 never requested, never consumed**: no GO-3 phrase is registered for
  this cycle; the verdict requests none.
- **Heavy lock FREE_PROVEN** at audit time (flock free, no live worker,
  `workers: 0`); lock history shows the single heavy job `run_go2.py` ran
  under lock with exactly the two expected artifacts.

## 3. Freeze chain (Task 3)

- `GO1_freeze_sha256.txt` carries both freeze shas; A7 independently
  reproduced both: original `41ef0624…` via `git show 2104a5b9:…`, amended
  `64aba7c3…` = working tree = the `freeze_sha` field in ALL FOUR outcome
  artifacts (FIXTURES_RUN1, SCORED_RUN1, both fixture blocks). All five
  council-report shas match disk byte-for-byte.
- Amendment is **pre-outcome**: commit order 2104a5b9 (GO-1, original freeze)
  → e24560e1 (amendment + A7 prelaunch, before any scored artifact existed)
  → 2940a113 (GO-2 scored execution). Budget and verdict rows byte-identical
  across the amendment (A7 prelaunch §1(a) verified; diff direction strictly
  toward the sha-pinned proposal).
- `A7_PRELAUNCH_REPORT.md` exists, **PASS**, at GO-1 head; its O8 (commit the
  amendment) was honored in e24560e1.
- `FIXTURES_RUN1.json`: **all pass** (F_GRID hour-aligned 8h; F_WARMUP;
  F-P1A-FLAT 0 violations; F-P1-OFFBYONE; F7 fold-flat; F4 non-vacuity
  4.06%/4.16% ≥ 2%; power 749/733 + 781/737; F1 truncation 0/512; F2
  future-mutation 0/25). FIXTURES and SCORED carry identical fixture blocks
  and the same engine sha `711e574f…`, which equals the current
  `scripts/engine_m1.py` sha (recomputed by A7).
- **P-19 disclosures**: the 2 harness fixes + 2 funding-load fixes are
  disclosed in verdict §5 and the GO-2 commit message. FINDING (minor): the
  artifact trail of the two blocked runs is thin — `RUN1_console.log` is a
  21-byte stub (`done: FAIL_SEE_GATES`), so the intermediate failures are
  self-reported rather than logged per-run. The final state is internally
  consistent (one fixture block, one engine sha, verdict invariant across 3
  runs per the implementer); non-blocking because the verdict rests on the
  final run, which A7 reproduced independently.

## 4. Kill-law application (Task 4)

Laws fired are exactly the frozen ones (impl-pin 8 + kill-laws row); **no law
was weakened, re-interpreted post-hoc, or needed to reach REJECT_ALL** — G1
alone kills each pair; every other kill is redundant confirmation:

- **G1–G4** FAIL on both pairs (frozen thresholds applied verbatim: net>0,
  PF≥1.20, ≥3/4 folds positive, net>0 @×1.5; per-pair primary, BOTH-pairs
  adjudication — under which failure of either pair kills the identity).
- **K-CTRL (G6b)**: inverted out-earns the anchor on BOTH pairs — impl BTC
  −4,889 vs −24,956, ETH +2,573 (PF 1.035) vs −33,515, read from
  SCORED_RUN1.json and confirmed by A7's recompute (BTC −4,013, ETH +2,422
  under B; less-negative under A; positive-ETH under both).
- **K-ANC**: |rho| > 0.20 — BTC 0.2483 (rev24), ETH 0.2565 (bandfade), rest
  ≤ 0.125 (SCORED_RUN1.json). The shadow representations are impl-pinned
  approximations, so A7 consistency-checks rather than independently
  recomputes the rho values; acceptable because REJECT_ALL does not depend on
  K-ANC.
- **G7**: anchor negative vs long-hold +64,758/+114,166 and SMA720 +89,665/
  +121,359 bps with measured funding deducted — sane rates verified from raw
  grids (11.81/13.96 %/yr vs declared 11.80/13.95).
- **G8** fail-closed correctly reported N/A (no positive PnL to concentrate).
- Diagnostics consistent with death (delay-1, ungated, ±4h placebo ≡ one
  placebo on the 8h grid — disclosed, placebo-levels, block-shuffle p=1.0 BTC,
  weekday/weekend and hour buckets all ≈ negative; DSR 0.0 at N=6 trials).

## 5. Forbidden actions (Task 5) — NONE found

- No orders: engine/driver contain no network, order, credential, or broker
  code paths (grepped); everything is geometric from staged klines.
- No push/merge: branch `orca/srlv-cx-c1-integration` has no remote tracking
  ref — all 5 cycle commits are local-only; `main`'s new commits are
  owner/registry-space bookkeeping (owner packet recording the owner's own
  GO-2 typing; registry projection), not lane writes.
- No foreign lane/worktree edits; worktree was clean before A7's two writes.
- S1/sealed never read; no shadow or heavy worker running (lock FREE_PROVEN,
  workers 0).

## 6. Findings (non-blocking; for the two-half close and failure memory)

1. **Registry bookkeeping staleness**: the SRLV-CX-C1 row still carries
   `go_phrase_state: REGISTERED_NOT_CONSUMED` for the GO-2 phrase although
   consumption is recorded in `phase`, the `write_token`, and the owner
   packet; `budget.used` is 0/18 while the ledger records 6/18 cells
   observed. Normalize both at the two-half close (ledger remains trial
   authority).
2. **P-19 trail thin**: `RUN1_console.log` is a stub; the two blocked scored
   runs and the funding-load bug are self-reported (verdict §5 + commit
   message) and consistent with the final artifacts, but no per-run artifact
   of the failures exists. Future cycles: append per-run console digests.
3. **Freeze-literal vs implementation off-by-one on exit (iii)** and
   **fold-straddler drop vs force-flat**: both readings computed by A7; the
   verdict is invariant. The implementation's reading is the one consistent
   with the law's uniform decision-at-close/fill-at-next-open convention.
   Recommend one clarifying line in failure memory to prevent re-litigation.
4. **Exit (ii) disaster stop never fires** under either reading (its close
   threshold is always beyond exit (i)'s). Harmless pinned redundancy; note
   for future sweep-books that (ii) as drafted is dead code.
5. **Residual 3.5% BTC net delta** (A7-B −25,831 vs impl −24,955) with exact
   n agreement is boundary tie-order noise; if the two-half close wants
   bit-identity, the tie order (low-before-high at equal entry bar) must be
   pinned — it changes no verdict-relevant fact.

## 7. Gate state after this audit

1. A7 terminal: **CONFIRM_REJECT_ALL** (this artifact +
   `HANDOFF_a7_terminal.json`).
2. Next: owner two-half close — program §11 stop-condition accounting for
   track CX (cohort-1 empty), registry normalization (finding 1),
   failure-memory append (finding 3/4 lessons already drafted in verdict §6).
3. Sealed/prospective remain unconsumed: any future cohort for this family
   opens only with a new payer/observable per the plan's revival rules.
