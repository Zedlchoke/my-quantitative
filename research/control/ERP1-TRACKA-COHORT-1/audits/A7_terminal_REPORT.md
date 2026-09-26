# A7 TERMINAL AUDIT — ERP1-TRACKA-COHORT-1 (fresh context, independent recompute)

**Verdict: TERMINAL_AUDIT_PASS_WITH_CONDITIONS**

- Auditor: A7 terminal lane (fresh context; no prior A7 terminal artifact of this
  cycle read; independent recompute from bytes only — ledger rows, series files,
  machine artifacts, code, and verification re-runs of committed entry points).
- Measured base: branch `orca/erp1-tracka-cohort-1-integration` @
  `4aae62269a8d7dd1736b0d05dd6081cce032da01`, tree clean.
- Certified cohort terminal label (checklist G): **`REJECT_ALL`** (umbrella §9,
  paper-tier bound, `SINGLE_SOURCE_PANEL`). See §G.

---

## A. Terminal-verdict recomputation from source — CONFIRMED

All numbers below recomputed by this audit from `trial_ledger.jsonl` (41 rows),
`series/*.json` (12 files), `scored_dev_cells.json`, `scored_seam_law.json`,
`scored_kill_laws.json`, `scored_dsr.json`, `scored_holdout_look.json`, and the
freeze — NOT from the prose report. Additionally, the engine was re-run from the
committed entry points (`scored_lib.build_targets` + `placebo_target_full_panel`
+ `engine.run_strategy`) on the committed planes: **all 16 books (8 arms × 2
pairs, incl. FLAT) reproduce published nets AND trade counts exactly**.

### A.1 Anchor gates (k=1.0 book), recomputed vs published — MATCH

| pair | G1 net | G2 PF | G3 pos folds | G4 net@1.5 | G5 RT | G6 | G7 | G8 |
|---|---|---|---|---|---|---|---|---|
| AUDUSD | 323.3 PASS | 1.0334 FAIL (−0.1666) | 3/6 FAIL | −652.35 FAIL | 923 PASS | 0.042864 PASS | 0.070563 PASS | 0.490883 PASS (margin +0.0091) |
| USDCAD | 681.0 PASS | 1.0509 FAIL (−0.1491) | 3/6 FAIL | −509.4 FAIL | 962 PASS | 0.071704 PASS | 0.060320 PASS | PASS |

Recomputed per-fold nets (from series daily pips mapped through the frozen fold
table) equal the published per-fold tables to the pip; per-fold sums ==
per-trade sums == daily sums == ledger `net_pnl` at k ∈ {1.0, 1.5, 2.0} for all
12 scored cells (36/36 equalities exact).

### A.2 Seam law — all three limbs fire on both pairs (recomputed)

- AUDUSD: S = 3207.4 − 323.3 = **2884.1** vs c_rt 2.0 (recomputed from the
  frozen formula = frozen 2.0). Limb (i) S > 20 FIRES; limb (ii) S > 6 AND S>0
  on 4/6 folds (F1 +499.3, F2 +1520.1, F3 −362.2, F4 +515.7, F5 +774.8,
  F6 −63.6) FIRES; limb (iii) 337 matched pairs ≥ 20 floor, delta +8.0451 >
  2.0 FIRES (excluded 29 orig-only + 25 anchor-only = frozen 366/362).
- USDCAD: S = 5029.6 − 681.0 = **4348.6** vs c_rt 2.4 (recomputed = frozen).
  Limb (i) > 24 FIRES; limb (ii) > 7.2 with 4/6 folds positive FIRES;
  limb (iii) 306 ≥ 20, delta +12.9562 > 2.4 FIRES (excluded 29+24 = 335/330).
- M-2 non-vacuity holds (ledger `PASS_NON_VACUOUS` rows; dry-run non_vacuous
  true; R-ANCHOR≠R-ORIG on ~50% of in-session dev bars measured pre-PnL).
- Terminal labels confirmed on BOTH pairs: **KILL_PIT_SEAM**.

### A.3 Kill laws — recomputed from series fold nets — MATCH

- **KILL_INVERSION fires on both pairs** via the §9.3 fold-residue clause:
  AUDUSD F5 anchor −391.2 / inverted +92.1; USDCAD F1 −244.7 / +12.3 and
  F6 −510.3 / +103.1 (anchor fold net ≤ 0 while inverted > 0 — the natural
  fold-level G1 analog; interpretation disclosed in the scored handoff). The
  overall limb (inverted ≥ anchor over the union) does NOT fire (−2274.6 /
  −3061.8 vs +323.3 / +681.0). Both pairs' terminal records carry fired_kills
  = [KILL_PIT_SEAM, KILL_INVERSION].
- KILL_CONTROL_REPRODUCED: does NOT fire (placebo −2207.3 / −978.3; band limb
  no; fold-residue 1/6 and 2/6 < 4).
- KILL_BETA_EXPLAINED: does NOT fire (anchor − beta = +341.5 AUDUSD /
  +1807.5 USDCAD; both limbs no).
- **No promotable outcome exists under the frozen laws**: the anchor fails
  G2, G3 and G4 on both pairs (any single FAIL at dev is terminal per §9.3),
  the seam law kills independently, and PROMOTE additionally requires all
  G1–G8 dev PASS + a holdout look that the dead anchor may not take (§9.1).
  R-ORIG passed all EIGHT gates on BOTH pairs (machine-verified in the ledger
  rows) and is never selectable by law — the decisive falsification point:
  the edge WAS the seam.

### A.4 Kills are real, not machinery artifacts — four independent proofs

1. **Cost charged exactly once per side.** Costs live inside the fills (one
   spread adjustment per fill, `engine.run_strategy`); `decompose()` derives
   gross = net + (s_entry + s_exit) × k. Verified: cost exactly k-linear in k
   for all 10 arm-books (k·cost(1.0) to <1e-6), net = gross − cost at every k,
   gross and n_trades invariant across k (the cost book changes no fill).
2. **Mirror identity holds in bytes.** INVERTED is the negated target of
   R-ANCHOR through the identical executor, so for mirrored same-bar trades
   net_inv ≡ −(Δbid + s_B) = −gross_anchor at k=1.0. Verified EXACT in the
   ledger rows and cells on both pairs: net_inv == −gross_anchor
   (−2274.6 == −2274.6; −3061.8 == −3061.8), gross_inv == −net_anchor, and
   cost_inv == cost_anchor (1951.3 / 2380.8) with equal trade counts (923 /
   962). Any double-charging, missing charging, or non-mirrored schedule
   would break this equality; it holds to the pip at every k for cost and at
   k=1.0 for the nets (the theorem is stated at the base book).
3. **Force-flat law in the fill records.** Re-run of the engine on the
   committed planes: across all 16 books, 0 entries on day-close bars, 0
   trades crossing a UTC day boundary (no overnight), 0 exits after the
   day's last tradable bar, day-close exits land exactly on
   `last_tradable_of_day`. The H1 close law (`SignalPlane`: fill_ok = hour ≤
   18 & not day-close; force-flat at the 19:00-bar close) matches freeze pin
   (iv). Fold boundaries: `fold_straddles = 0` for all 12 scored cells;
   per-fold sums reconcile with per-day sums under the frozen F1..F6 windows.
   One executor property decoded and disclosed (scored handoff already
   discloses it as the "ghost-trip mechanic"): a signal occupying the
   prior day's last in-session bar can fill at the next day's first fillable
   bar (00:00/01:00; 17 AUDUSD / 11 USDCAD anchor fills) and exits one bar
   later — PIT-clean (signal bar closed), same-day, costed, symmetric under
   the mirror, identical in the falsifier counts. No frozen law breached.
4. **Full independent re-execution.** All 16 books' nets and trade counts
   reproduce exactly from the committed entry points (see §A preamble);
   38/38 committed tests pass (`pytest tests/ -q`).

## B. Reproduction chain — CONFIRMED

- `repro/REPRO_REPORT.md` verdict **ALL_MATCH** with a complete difference
  inventory. Independently re-verified in bytes:
  - Twin ledger (55 lines) preserves the published 41-line prefix exactly;
    the 14 twin-appended rows differ from the published rows in EXACTLY one
    field path — `sha_chain.scored_code["scripts/scored_lib.py"]`
    (published `eabe8e84…` = uncommitted run-time state; twin `1a5a9e00…` =
    committed bytes). This matches REPRO §3.4 and the scored handoff's
    disclosed post-run float-coercion fix; the twin's byte-exact numeric
    equality empirically proves the fix changed no serialized number.
  - Dry-run sequence-metadata diffs (ledger sha of the 27-line pre-scored
    ledger vs the 41-line ledger at twin time) verified: the published
    `5830065a…` equals the hash of the 41-line ledger's 27-line prefix.
  - Wall-clock fields: exactly the 5 enumerated (`created_utc` ×4 + the
    Generated line). 12 series files + seam + kill files byte-identical.
- **SCORED_REPORT erratum verified against machine artifacts**: the prose
  "USDCAD R-ORIG 5/6 folds" is wrong — machine truth is **6/6 positive folds**
  (F1 +1231.3, F2 +1481.1, F3 +91.8, F4 +542.9, F5 +664.1, F6 +1018.4;
  ledger G3 row: PASS 6/6). AUDUSD R-ORIG is 5/6. Erratum recorded
  (REPRO §3.3 + harvest commit 4aae6226); the wrong prose is left in place,
  not silently repaired. The same paragraph's "passes ALL EIGHT gates on BOTH
  pairs" is machine-true.
- Note (F7): the comparison tool's strict machine `VERDICT` field is
  "MISMATCH" (byte/digest semantics counting wall-clock, sequence metadata,
  the authored paragraph and the provenance sha) while the report adjudicates
  ALL_MATCH with the full inventory; every flagged item was re-verified by
  this audit and is classified. Semantics difference, no information lost.

## C. Freeze discipline — CONFIRMED with one pin erratum (F1)

- The freeze file was last modified at the recorded E1 erratum
  (2026-09-25T19:38:44Z, commit 5ca85682) — BEFORE GO-2 (registry write token
  23:30:37Z) and BEFORE the scored run (23:52–23:55Z). **Nothing touched the
  freeze after the scored run.** E1 is recorded inside the artifact with the
  c28577ef incident note.
- Census shas (AUDUSD/USDCAD) and M1 manifest shas match current bytes.
- Code pins: `build_signal_plane.py` and `falsifier_run.py` match the frozen
  bytes. **`tracka_lib.py` does NOT** — see Finding F1.
- Seeds 20260925 (bootstrap + mode-sham) as frozen and consumed as frozen;
  c_rt 2.0/2.4 recomputed from the frozen formula = frozen values; N_diff
  728/665 = frozen; limb-3 machinery counts (337/306 matched; 366/335
  orig-only; 362/330 anchor-only) reconcile exactly between freeze and scored.
- Holdout membership sha in `scored_holdout_look.json`
  (`45ff897d…`) equals the freeze pin; both pairs' statuses
  HOLDOUT_UNREAD_CONSUMED_BY_NONE; ledger rows 33/40 present; all 12 series
  files' daily keys end ≤ 2025-12-31 (no holdout day anywhere in any series);
  scored cells run on `include_holdout=False` planes. The one-look holdout
  windows (2026-01-01..2026-06-30) remain UNREAD.

## D. Denominators + budget — CONFIRMED

- Ledger: 41 rows (27 pre-PnL battery rows + 12 scored dev cells + 2
  HOLDOUT_UNREAD bookkeeping rows). Verdict vocabulary consistent with the
  plan/umbrella sets; every row carries the three mandatory labels.
- Budget: **12 scored cells consumed of the 24 cap** (18 effective after the
  D2 veto); M3 consumed 0 cells (F-5 pre-PnL kill), M2 0 (D2 veto). Holdout
  looks consumed: 0.
- Observed == published for all rows in the cycle ledger (every published row
  is machine-generated and re-derived; no unbacked publication). Program/asset
  denominator re-stamp happens at the two-half close per P-9 (precedent:
  ILLIQ-REG-V1) — the close must stamp 12 scored cells (+2 bookkeeping rows,
  0 holdout looks) and 0 survivors.
- DSR persisted per anchor (Bailey–Lopez de Prado 2014; N = all 12 cohort
  scored cells; FLAT null book SR=0 convention — conservative-widened;
  AUDUSD DSR 0.000798, USDCAD DSR 0.001631). **PBO = NOT_RUN fail-closed**
  with the stated reason (12 cells but < 8 distinct config classes for CSCV).

## E. Governance — CONFIRMED (registry staleness = expected pre-close, F4)

- GO-1 and GO-2 records: exact-phrase EXACT matches, correct authorizations
  and forbids. GO-2 preconditions text matches the measured state.
- GO-2 record timestamp note (F3): `received_utc` "2026-09-26T00:00:00Z" is an
  exactly-midnight stamp LATER than the authorized artifacts' creation times
  (dry-run 23:52:56Z, scored cells 23:55:17Z). The registry write token
  (updated 2026-09-25T23:30:37Z, "GO-2 typed exact … scored phase open")
  establishes the lawful order GO-2 → dry-run → scored. Timestamp imprecision
  only; no gate-order violation.
- Registry entry stale vs measured tip (F4): head `5ca85682` vs measured
  `4aae6226` (later commits: 9e21ce6f scored-handoff bookkeeping, 4aae6226
  repro harvest); budget.used 0 vs 12 consumed; workers 1 vs measured 0;
  go_phrase_state REGISTERED_NOT_CONSUMED vs GO-2 consumed per the writer
  token. Lifecycle ACTIVE_LIGHT / phase P6_SCORED is accurate for a cycle
  awaiting its two-half close. Same residual-staleness class the owner
  accepted at ILLIQ-REG-V1 (P-9 carries the truth; the close must update).
- S1 SEALED_UNTOUCHED (no S1 surface exists in this cycle; no S1 path in any
  changed file). FX shadow daemon PID 79157 alive (17h+ uptime, running from
  its own worktree), untouched; this cycle wrote nothing under the
  FX-RANGEFADE-2M-SHADOW-V1 namespace. Heavy lock FREE_PROVEN (no holder, no
  live worker; measured workers = 0).
- Root `main` @ `ed0683a2`: since the cycle base `69ddc604`, exactly four
  commits, ALL control-plane (plans/ registry+events+ACTIVE_CYCLES, the plan
  itself, council/audit artifacts, GO gates): `460d2acd` (registration),
  `76fb5a8e`, `fe4766d5` (phase control), `ed0683a2` (GO-2 record). No engine,
  ledger-of-record, or shared-code change.
- No push anywhere: `main` is ahead 29 of origin/main (never pushed); the
  cycle branch has NO upstream. Cycle worktree tree clean at the tip.

## F. Incident register completeness — CONFIRMED

1. c28577ef overclaim (commit message claimed the E1 freeze fix; edit script
   had failed) — recorded in the freeze artifact's E1 `incident_note` and in
   the corrective commit 5ca85682's message; history not rewritten.
2. Freeze erratum E1 (arm_config_digest_old duplication) — recorded in the
   artifact `errata[]`, corrected values verified against 3931aed8 bytes.
3. Scored lane's two pre-scored machinery fixes (ts→index map for
   trip_cost_pips; np.float64 repr / numpy-scalar coercion) — recorded in the
   scored handoff INCIDENTS with the explicit no-rerun/numbers-unchanged
   claim the twin byte-confirms.
4. Repro prose slip (USDCAD R-ORIG "5/6") + erratum — recorded in REPRO §3.3
   and the harvest commit 4aae6226 message.
   Nothing was silently repaired: the wrong prose stands, the provenance gap
   stands, the freeze keeps its errata block.

## G. Strongest-allowed cohort terminal label — `REJECT_ALL`

Facts: M1 (mandatory slot) KILL_PIT_SEAM + KILL_INVERSION on BOTH pairs —
scored, terminal for the identity on those pairs (§9.3); M2 NOT_SCORED_FALSIFIED
at D2 (V-4_BLEND); M3 NOT_SCORED_FALSIFIED at F-5 (stress RT 4.8 ≥ 2.0 kill
line, measured pre-PnL; all M3-only conditions moot). No mechanism survived its
falsifier battery.

Umbrella §9 enumeration: `REJECT_ALL` = "no mechanism survived its falsifier
battery" — exactly this state. It is the correct and strongest-allowed cohort
enum:

- NOT `CANDIDATE_PENDING_PROSPECTIVE` (nothing survived), and the per-pair
  KILL_* labels are pair/arm-level records, not a cohort enum;
- NOT any `BLOCKED_*` class: the deciding events are EXECUTED falsification
  results (scored kills on M1; pre-PnL falsifier/veto kills on M3/M2 recorded
  `NOT_SCORED_FALSIFIED` per plan §8 ordering law), not data/selection/
  source/cost-authority closures of the cohort space;
- `TIME-STOP`/§9.3 acknowledge `REJECT_ALL` as a valid cohort close; plan §1.2
  declares it an expected, valid terminal verdict; §11 binds the vocabulary to
  umbrella §9, paper-tier bound.

**Certified cohort terminal label: `REJECT_ALL`** — with per-pair terminal
records KILL_PIT_SEAM (fired kills incl. KILL_INVERSION) on AUDUSD and USDCAD,
M2 `NOT_SCORED_FALSIFIED (D2 V-4_BLEND)`, M3 `NOT_SCORED_FALSIFIED (F-5)`,
0 holdout looks consumed, 12/24 cells (12/18 effective), DSR reported, PBO
NOT_RUN fail-closed, `SINGLE_SOURCE_PANEL` + `PAPER_TIER` +
`FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` on every verdict.

---

## Findings

- **F1 [MEDIUM — provenance; no numeric impact] Stale freeze code pin for
  scripts/tracka_lib.py.** The freeze pins `27f21671…` (the 3931aed8 bytes);
  the sanctioned ADJUDICATION #2 rebuild commit 43cb8b1f appended +87 lines
  (`placebo_rebuild` — append-only, verified: zero deletions, no existing line
  touched) and edited the freeze artifact's arm digests but did NOT refresh
  the code pin. The scored run and the repro twin executed/current bytes are
  `1e09b368…`; all 12 scored ledger rows cite the stale pin in
  `sha_chain.code_freeze`. Numeric invariance is nonetheless proven twice:
  (a) the appended function is not on the scored execution path
  (`scored_lib.placebo_target_full_panel` reimplements the frozen recipe);
  (b) the twin re-ran the committed `1e09b368` bytes and reproduced every
  numeric artifact byte-exact. Disposition: **close-out condition C-1** — the
  close record must state the true scored-time code identity (3931aed8 pins +
  43cb8b1f's tracka_lib.py `1e09b368` + scored_lib executed `eabe8e84` /
  committed `1a5a9e00`); no re-run required.
- **F2 [MEDIUM — provenance; on record] Scored rows cite an uncommittable
  scored_lib.py sha** (`eabe8e84…`, the post-run-float-coercion working state;
  committed as `1a5a9e00…` without a re-run). Already recorded (scored handoff
  INCIDENTS + REPRO §3.4); this audit re-verified the row-level diff is
  exactly that one field and that the committed bytes reproduce all numbers.
  Disposition: carry into the close record (part of condition C-1).
- **F3 [LOW] GO-2 record timestamp imprecision.** `received_utc`
  2026-09-26T00:00:00Z post-dates the artifacts it authorizes; the registry
  write token (23:30:37Z) carries the true receipt order. Disposition: note in
  the close record; no action.
- **F4 [LOW — expected pre-close] Registry fields stale vs measured state**
  (head −2 commits; budget.used 0 vs 12; workers 1 vs 0; go_phrase_state not
  flipped to consumed). Precedent ILLIQ-REG-V1 (owner-accepted residual
  staleness class; P-9 ledger row carries truth). Disposition: **close-out
  condition C-2** — the two-half close must update the registry row
  (terminal head, budget 12/24, workers 0, GO phrase extinguished-consumed,
  phase → closed REJECT_ALL) and append the P-9 ledger row.
- **F5 [LOW — on record] SCORED_REPORT prose slip** (USDCAD R-ORIG "5/6" vs
  machine 6/6). Erratum recorded; not silently repaired. Disposition: carry the
  erratum into the close record (condition C-1).
- **F6 [INFO — disclosed] Executor ghost-trip mechanic** (next-day first-bar
  fills from the prior day's last in-session signal bar; 17/11 anchor fills;
  PIT-clean, same-day, costed, mirror-symmetric) — already disclosed in the
  scored handoff; re-verified harmless by this audit's fill-law re-run.
- **F7 [INFO] Repro tool strict VERDICT ("MISMATCH") vs report ALL_MATCH** —
  label-semantics difference; inventory complete; every item re-verified here.
- **F8 [INFO] BASELINE-SET dual-digest scheme** (registry digest governs dev
  rows; membership digest governs holdout rows; payload adds beta_matched) —
  explained in the scored handoff; dev-row digests verified against the
  registry (ALL MATCH).

## Binding close-out conditions

- **C-1:** the two-half close record must carry the errata bundle: F1 stale
  tracka_lib pin (true scored-time code identity), F2 scored_lib provenance
  shas (executed vs committed), F3 GO-2 timestamp note, F5 USDCAD R-ORIG 6/6
  prose erratum.
- **C-2:** the close must update the registry row (terminal head, budget 12/24,
  workers 0, go_phrase consumed/extinguished, phase closed) and append the P-9
  hypothesis-ledger row with denominators (12 scored cells; 2 HOLDOUT_UNREAD
  bookkeeping rows; 0 holdout looks; 0 survivors) — stamping `REJECT_ALL`.
- **C-3:** the holdout windows 2026-01-01..2026-06-30 (both pairs) remain
  UNREAD and preserved for any future re-derivation under the one-look law.

## Auditor limits

Recompute performed on the committed artifacts + committed planes/parquets as
found (the twin's limitation about parquet-vs-.bi5 rebuild applies here too).
No S1, no orders, no registry/plan/FX-shadow writes, no worker touched, no
commits by this lane. Heavy lock not needed (no heavy job run). Verified test
suite: 38 passed. This audit ran only read-only measurement plus verification
re-runs of committed entry points in /tmp.
