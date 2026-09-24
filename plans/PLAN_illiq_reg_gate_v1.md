# PLAN — ILLIQ-REG-V1 (regime-gated ILLIQ-AMIHUD: gate ON/OFF on the frozen anchor)

- Status: REGISTERED `PLANNED_NOT_STARTED`. Nothing scored has run under this
  plan. Registration is the only authority surface; the draft dossier
  (`research/control/illiq_reg_gate_v1_draft/`) is input evidence, not law.
- Authored: 2026-09-24 · Lead/bootstrap session per dispatch of owner 2026-09-24
- Parent context: `CRYPTO-HISTORICAL-REPLICATION-3F-V1` (CHR3F, amendments
  A2..A5, A7 rounds r1..r6) — family `A8-V11-ILLIQ-AMIHUD`, engine frozen at
  `c97283e0`, 18 files byte-identical per A7-r5 §7.

## 0. Authority order

1. Latest explicit owner instruction.
2. This plan (highest registered live law for cycle `ILLIQ-REG-V1`).
3. `CLAUDE.md` + `HOW_TO_BE_A_LEAD_ENGINEER.md` (§31 bootstrap playbook).
4. Frozen PREREG draft `research/control/illiq_reg_gate_v1_draft/PREREG_ILLIQ-REG-V1.yaml`
   — its frozen constants are carried into §3/§5/§6/§7 VERBATIM. The draft is
   superseded only where this plan is stricter (staged budget §8).
5. CHR3F plan and terminal/partial artifacts: historical evidence, never
   current truth.

## 1. Mission and non-mission

**Mission.** Decide — on a preregistered falsification surface, then (only in
a later owner-gated stage) a forward window — whether the frozen
`ILLIQ-AMIHUD-28D-W` anchor book may be held **only when a two-variable regime
gate is ON** (liquidity-rotation direction + BTC realized-vol floor). The gate
is a pure OVERLAY on the frozen engine: engine, adapter, universe law, costs,
folds and all frozen constants stay untouched. On/off of the overlay is the
only degree of freedom this cycle measures.

**Non-mission.** No parameter rescue of the ILLIQ anchor; no gate-threshold
tuning on or after 2024-08-22; no new engine features; no S1 access; no
shadow/paper/live deployment surface; no confirmation claim from any
historical window; no gate-variant iteration inside this cycle.

## 2. Ancestry disclosure (binding, verbatim)

> family ILLIQ-AMIHUD-28D-W = V11 FAMILY_REJECT (fold-share 0.7055) → cycle
> CHR3F chạy replication outcome-exposed (A3/A4/A4b/A5) → DIAG S0R −58.9%
> (funded −56.3%) ĐÃ ĐƯỢC QUAN SÁT trước khi gate được thiết kế → mọi kết quả
> của ILLIQ-REG-V1 mang OUTCOME_EXPOSED_ANCESTRY vĩnh viễn, trọng số xác nhận
> = 0 trên mọi window lịch sử; bề mặt xác nhận duy nhất = forward/shadow.

Observed outcomes carried by that disclosure (artifact `result_sha256`-pinned
in the PREREG draft §provenance_hashes):

| artifact | window | net | MDD | funding |
|---|---|---|---|---|
| `illiq_diag/S0R-ANCHOR-A5` | 2024-08-26..2025-08-18 | −0.589312 (no-funding DIAG, B2) | 0.624507 | 0.0 (missing, B2) |
| `illiq_diag/S0R-ANCHOR-A5` funding-wired re-disclosure (commit `8ec3965d`) | same | −0.5631 | — | wired per-fold |
| `illiq_diag/Y2024P-ANCHOR-A4` | 2024-01-08..2024-08-19 | +0.137736 | 0.205031 | +0.020440 |
| `illiq_diag/Y2021-ANCHOR-v2` | 2021-01-04..2021-12-27 | +1.036025 | 0.132299 | +0.028863 |
| `recovered/v11_root/baseline_wave2.json` W2-1 | 2025-08-22..2026-08-21 | +0.581969 | 0.091822 | +0.110859 |

The single-shot gate replay in the dossier (`pit_conc_gate_single_shot.json`)
was ONE descriptive application of the already-frozen thresholds; it carries
zero confirmation weight and is registered as stated — including its honest
reading that the a-priori combo misses loss phases A and B (~80% of the S0R
loss) and is expected to FAIL the falsification rule.

## 3. Gate spec — FROZEN (from the PREREG draft, verbatim constants)

Apply law:

- Gate state computed at each Monday 00:00:00Z stamp T from COMPLETED daily
  UTC blocks strictly before T (PIT; same bar law as the engine).
- State changes only at stamps (weekly cadence, no intra-week trading).
- `GATED = (V1_state == ON) AND (V2_state == ON)`. The book formed at T is
  taken only when GATED; otherwise the book is flat for that week.

Variable 1 — liquidity-rotation direction (O1, frozen):

- `CONC28(T)` = mean over trailing 28 daily UTC blocks of
  `DV(BTCUSDT) / sum(DV(symbols PIT-eligible that day))`, where
  `DV = sum(quote_volume)` of completed 15m bars in the block; a symbol is
  eligible on a day when it has ≥28 prior daily blocks (listing-age law of the
  frozen engine).
- `S90(T)` = `CONC28(T)` − mean of `CONC28` over the trailing 90 days ending T.
- Thresholds from pre-window Mondays 2020-01-06..2024-08-19 (n=242):
  ON if `S90 ≤ 0.021317` (p70); OFF if `S90 ≥ 0.057702` (p90); between the
  two: carry previous state (initial state ON).
- `O2` (majors-minus-alt 90d momentum) is `POST_HOC_PROPOSED_OUTCOME_EXPOSED`:
  proposed AFTER observing S0R forensics, never replayed, and may replace O1
  ONLY by an explicit owner amendment BEFORE any cell runs — in which case the
  random-gate bar rises to ≥97.5th percentile (§7).

Variable 2 — BTC 30d realized-vol floor (V2, frozen):

- `VOL(T)` = pstdev of the 30 daily log closes of BTCUSDT (completed daily
  blocks) × √365.
- Thresholds from pre-window Mondays (n=238): ON if `VOL ≥ 0.328930` (p10);
  OFF if `VOL < 0.296037` (= floor × 0.90, hysteresis); between: carry state.

Anti-tuning declaration: no threshold was chosen by inspecting P&L on
2024-08-22 or later; calibration source is `catalog_live_crypto_b20`
(2020-01-01..2024-08-21) only.

## 4. Universe — PIT declaration

`PIT_LISTED_AT_WINDOW_START` (CHR3F amendment-A4 law), declared NOT
book-identical (A7-r3 F1 measured 6/53 divergence on Y2023); S0R: all 20
perpetuals of the frozen SYMS list are listed by 2024-04-02, so
listed-at-start = full universe, no divergence (A5). Engine eligibility is
unchanged and fail-closed: MIN_ELIGIBLE=10, quintile law, CAP 0.30, beta
hedge, SKIP_NO_SELECTION.

## 5. Windows — preregistered before any PnL

| fold | span | role |
|---|---|---|
| Y2021 | 2021-01-01..2021-12-31 | exploratory, outcome-exposed (zero confirmation weight) |
| Y2024P | 2024-01-01..2024-08-19 | exploratory secondary, outcome-exposed |
| **S0R** | **2024-08-22..2025-08-21** | **falsification surface (phase 1)** |
| FWD | 2025-08-22..2026-08-21 | confirmation-only — **NOT scored in this cycle**; shadow/paper only, after data-coverage verification |

Every line reporting any ILLIQ result must state its window fold explicitly
(artifact metadata `identity.window_*` fields are template-frozen and are NOT
window evidence — A7-r5 N6).

## 6. Falsification rule — VERBATIM (phase-1 bar)

Surface: S0R DIAG, funding-wired (per-fold scan law, §9). The combo O1+V2 is
**FALSIFIED unless BOTH hold**:

- gated baseline `net_sum ≥ −0.2947` (≥50% improvement vs −0.589312);
- gated baseline `max_drawdown ≤ 0.4372` (≥30% reduction vs 0.624507).

On fail: `FALSIFIED`; **no gate variants are permitted in this cycle** (no
tuning loop); the family returns to NOT_PROSPECTIVE diagnostics only.

Re-basing rule (declared in the draft, applied now): the falsification
thresholds re-base only if a funding-wired S0R anchor re-run moves `net_sum`
by more than 5 points. The funding-wired disclosure (commit `8ec3965d`) moved
it from −0.589312 to −0.5631 (Δ = 2.62 points) → **thresholds are NOT
re-based**; the −58.9% figure always travels labeled "no-funding DIAG (B2)".

## 7. Controls and stress

- **INV-gated** (causal negative control): frozen sign-inverted
  `ILLIQ-AMIHUD-28D-W-INV` book on the SAME gate series. In phase 1 (a losing
  anchor window) INV-gated is expected positive; an INV-gated that fails to
  sign-flip is a control-coherence failure to disclose, not a rescue.
- **Random-gate controls**: 200 seeded permutations of the gate series
  preserving toggle count and minimum run length 4 stamps; RNG seed derived
  from the cycle id string (declared, reproducible). Confirmation bar
  (FWD window, later owner-gated stage, NOT this cycle): gated `net_sum > 0`;
  gated `net_sum > ungated net_sum` (same window/engine); gated result ranks
  ≥ p95 of the 200 random gates (≥ p97.5 if O2 was ever adopted by amendment);
  INV-gated `net_sum < 0` on FWD; gate ON ≥ 8 of 52 stamps, else
  `INCONCLUSIVE_GATE` (test lacks force, no GO).
- **Stress** (applied to ALL gated cells): taker fee ×1.5 and ×2.0 with the
  baseline slip floor +1 tick kept; the engine-native stress
  (×1.5 fee, +2 ticks, +1 event delay) additionally reported where the runner
  exposes it. Stress rows live inside the cell.

## 8. Budget — STAGED (phase 2 is NOT authorized by this plan)

Registry `budget-max` = **4**, which is phase 1 only. Phase 2 opens ONLY if
phase 1 passes its own bar (§6) AND the owner approves an amendment that
raises the cap; the menu below is presented for that decision and is not
self-summed into a pre-approved total.

- **Phase 1 (≤4 cells, falsification on S0R):**
  1. `S0R / ANCHOR-gated / baseline` — the falsification cell;
  2. `S0R / ANCHOR-gated / ×1.5`;
  3. `S0R / ANCHOR-gated / ×2.0`;
  4. `S0R / INV-gated / baseline` — causal control.
  All four are `scored=False` diagnostics, namespace
  `REPLICATION_NOT_PROSPECTIVE`, each still counted as one budget unit.
- **Phase 2 menu (owner-approved amendment only):** `{Y2021, Y2024P} ×
  {ANCHOR-gated baseline, INV-gated baseline}` (4) + `S0R / INV-gated /
  {×1.5, ×2.0}` (2) + at most 2 owner-selected extras — ceiling 8 additional
  cells, consistent with the draft's 12-cell proposal ceiling.
- FWD shadow: zero scored budget in this cycle.

## 9. Data authority and wiring law (CHR3F lessons, binding)

- **Funding scan PHẢI THEO FOLD**: pre-window folds (Y2021, Y2024P) read
  `funding_data_scan/scan_2026` (2020-07-01..2024-08-20); **S0R and FWD read
  `funding_data_scan/scan_2026_a`** (2024-08-20..2026-08-21, 2196 BTC rows).
  The B2 incident (runner hardcoded `scan_2026` → funding 0.0 on all 336 S0R
  positions) must not recur; every cell verifies per-fold scan coverage before
  compute and records the scan id in its artifact.
- **Bars load-end +3d**: the runner loads bars to window_end + 3 days so the
  terminal Monday stamp has a covering bar (A4/F2); pre-window load = window
  start − 125 days.
- **Catalogs READ-ONLY at absolute CHR3F paths** (verified to exist
  2026-09-24):
  - `/Users/hoangminhlong/my-quantitative/.worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1/catalog_live_crypto_s0r` (2024-04..2025-09)
  - `.../catalog_live_crypto_b20` (2020-01..2024-08)
  - `.../funding_data_scan/` (both scans)
  - `.../illiq_cell_runner.py`, `.../chr3f_illiq_plugin.py`
  - `.../recovered/v11_root` (frozen engine, `c97283e0`)
  Never copy over, never edit any CHR3F file; reference only by absolute path.
  FWD window needs bars/funding coverage to 2026-08-21 from `scan_2026_a` —
  PIT coverage verification of that span is the FIRST step of the cycle and a
  hard prerequisite for any future FWD stage.

## 10. Gate sequence (§31 playbook, condensed)

1. Bootstrap: this registration + worktree
   `.worktrees/illiq-reg-v1/integration`, branch
   `orca/illiq-reg-v1-integration`, cut from the HEAD measured at
   registration; control files committed clean.
2. M0: hand-fixture tests of the gate module (hysteresis state machine, PIT
   completed-blocks law, no-lookahead mutation, quantile thresholds pinned to
   §3 constants) + wiring invariants (per-fold funding scan id; +3d load end;
   4-label invariant below) — all `PASS` before anything heavier.
3. Gate-series build (b20 + s0r catalogs) → frozen threshold constants
   verified byte-identical to §3; gate series + 200 random controls written
   to the cycle control namespace with digests.
4. Sanitized dry-run of the gated cell path: `scored=false`, no PnL/PF/stress
   fields at any depth, non-vacuous, IDs pairwise distinct, denominator delta 0.
5. **A7 prelaunch, independent** (hashes, identity, PIT authority, dry-run
   hygiene, labels, windows, gate law — the draft's prerequisite).
6. **STOP — owner gate.** The owner types the fresh exact phrase (§12) at
   this gate only, BEFORE the first scored cell.
7. Phase-1 cells under heavy lock; per-cell post-run report (identity, exit
   code, runtime, denominators, gate verdicts, workers, S1 status); no early
   stop for bad results.
8. Verdict per §6 → phase-2 owner decision request (or terminal close);
   reproduction + A7 terminal + two-half close per handbook §32.

## 11. Reporting contract — the 4-label invariant

Every produced ILLIQ-REG-V1 row (artifact, status line, report cell) carries
ALL FOUR labels or the row is invalid:

1. `WINDOW_FOLD=<Y2021|Y2024P|S0R|FWD>` explicit (template metadata is not
   window evidence);
2. `OUTCOME_EXPOSED_ANCESTRY` (§2), confirmation weight 0 on all history;
3. `REPLICATION_NOT_PROSPECTIVE` / `scored=False` namespace on every
   historical-window cell of this cycle;
4. `FUNDING_WIRING=funded(scan_2026|scan_2026_a)` or
   `no-funding DIAG (B2)` — the −58.9% figure never travels unlabeled.

## 12. Owner GO gate

After A7 prelaunch passes, the owner must type the exact fresh phrase:

```
GO ILLIQ REG V1 SCORED EXECUTION
```

Typed earlier, it dies unconsumed; mis-typed is refused and recorded; it does
not survive a pause and does not transfer to another cycle. Phase 2 and any
FWD stage need their own owner decisions regardless of this GO.

## 13. Terminal outcome vocabulary (decided now, incl. negative)

- `FALSIFIED` — phase-1 bar failed: gate combo dies for this cycle, no
  variants, family back to NOT_PROSPECTIVE diagnostics. This is the expected
  negative outcome per the dossier's honest single-shot reading and is a
  perfectly valid terminal state.
- `NOT_FALSIFIED_BUT_NOT_CONFIRMED` — phase-1 bar passed; zero confirmation
  weight accrues; next step is only the phase-2/owner decision request.
- `INCONCLUSIVE_GATE` — gate ON < 8/52 stamps on the deciding window.
- `NOT_RUN_DATA` / `NOT_RUN_IDENTITY` / `BLOCKED_DATA_AUTHORITY` /
  `BLOCKED_RESOURCE` — standard fail-closed states, with evidence.

## 14. Worktree and namespace law

- Implementation ONLY in `.worktrees/illiq-reg-v1/integration` on branch
  `orca/illiq-reg-v1-integration`; control namespace
  `research/control/illiq_reg_v1/` inside that worktree. Lanes never merge,
  rebase, push, or touch ledgers/registries.
- `research/control/illiq_reg_gate_v1_draft/` (root checkout) is committed as
  read-only input evidence of this plan and is not written again.
- CHR3F worktree is READ-ONLY (§9). The frozen engine is never modified; any
  suspicion of drift stops the cycle (`ENGINE_FROZEN_DRIFT`).
