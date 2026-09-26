# A7 TERMINAL AUDIT — ERP1-TRACKA-COHORT-2 — A7_terminal_REPORT.md

**Verdict: `TERMINAL_AUDIT_PASS`** — certified terminal label **`REJECT_ALL`** (umbrella §9).

- Lane: a7-terminal (fresh context, independent recompute; inherits NO implementer verdict).
- Audited HEAD: `a7c3c5c60f44125a1034251c3ccfd6a564655530` (branch `orca/erp1-tracka-cohort-2-integration`,
  worktree `.worktrees/erp1-tracka-cohort-2/integration`, tree clean at lane start and before this lane's two outputs).
- Audit date: 2026-09-26. Findings: **0 CRITICAL / 0 HIGH / 2 LOW / 3 INFO** (§ Findings).
- Recompute basis: all verdicts below were recomputed from committed bytes
  (.npy arrays, parquet spread columns, F6 histograms, census JSONs, git objects) — not from prose.

---

## T1 — GO lawfulness: **CONFIRMED**

1. `GO1_RECORDED.json` (root `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort2/`):
   `go_phrase_expected` == `go_phrase_received_verbatim` ==
   `GO ERP1 TRACKA COHORT 2 REGISTER AND COUNCIL`, `exact_match: true` — verbatim match to
   plan §0 GO-1 phrase in `plans/PLAN_erp1_tracka_cohort_2.md` (measured in the worktree).
2. Registration row in root `plans/CYCLE_REGISTRY.json`: `ERP1-TRACKA-COHORT-2`,
   `lifecycle: ACTIVE_LIGHT`, `budget: used 0 / max 18`, `head: a7c3c5c60f44…`,
   `s1: SEALED_UNTOUCHED`, `go_phrase: GO ERP1 TRACKA COHORT 2 SCORED` (GO-2),
   `go_phrase_state: REGISTERED_NOT_CONSUMED`, `workers: 0`.
   `CYCLE_REGISTRY.events.jsonl`: `CYCLE_REGISTERED` 2026-09-26T01:47:31Z at head
   `017d2464…` with the exact-phrase GO reason (typed 01:46:48Z AT its own gate, P-8);
   later `CYCLE_UPDATED` to head `a7c3c5c6…` / phase "GO-1 COMPLETE — slate EMPTY … REJECT_ALL".
   Registry writes carry `REGISTRY_SAVED` researchctl write tokens (no out-of-band edits).
3. GO-2 never typed: no GO2/GO-2-named artifact exists anywhere in either cycle namespace
   (root + worktree, searched); the GO-2 phrase appears in no consumed artifact; registry
   `go_phrase_state` remains `REGISTERED_NOT_CONSUMED`. GO-1 scope = register + council +
   falsifiers + freeze, then STOP — exactly what the artifact chain shows.

## T2 — Seven kill verdicts recomputed from machine artifacts: **CONFIRMED (7/7)**

(a) **F-0 (C1, C2, C3)** — `SKEPTIC_F0_cohort2_REPORT.md` §2.1–2.3 each carry the full
three-test table (SKELETON / PAYER / INFORMATION) with the proposal's own text as evidence;
verdicts `VETO_VARIANT_SAME_FAMILY` ×3; §2.8 summary table consistent; §5 one-shot
declaration present (adjudicated once, on measured base `6a507f5820612975…` — full sha of
the council round-1 root commit, verified `git rev-parse 6a507f58`). F-0 predates all
measurements (root commit `dc94824c` before worktree impl/F-1/F-5 commits).

(b) **F-1 rho (P3-A, P3-B)** — `falsifier/F1_rho_results.json`:
- **Sha chain verified end-to-end**: `manifest_sha256 7cdf3104…` == sha256 of
  `data_local/derived/t2_planes_manifest.json`; runner pin `76f2a01c…` == sha256 of
  `scripts/f1_rho_run.py`; `tracka_lib_sha256 1e09b368…` == sha256 of `scripts/tracka_lib.py`.
  **All 112 committed .npy arrays** (10 target planes + 102 shadows) re-hashed — **every
  sha256 matches the manifest**, no mismatches.
- **Independent recompute** (this lane's own average-tie-rank Spearman, not `tracka_lib`):
  P3-A AUDUSD vs FX2-SESSMA-C2 = **−0.078552** (recorded −0.078552); P3-A USDCAD vs
  FX2-SESSMA-C4 = **−0.088284** (recorded −0.088284); P3-B AUDUSD vs FX2-H1DONCH-C1 =
  **+0.310253** (recorded +0.310253); P3-B USDCAD vs FX2-H1TSMOM-C1 = **+0.303153**
  (recorded +0.303153). Exact to 6 dp on the full dev grid (27,608 / 27,583 rows).
- Pooled rule (max |rho| over 47 named shadows) re-derived from the recorded per-shadow
  tables — argmax matches `worst_shadow` / `pooled_worst_abs_rho` in all four pair blocks.
- Gate 0.20 (immovable): P3-A 0.0786/0.0883 → PASS_F1 both pairs; P3-B 0.3103/0.3032 →
  ANCESTRY_RHO_BLOCK both pairs, home USDCAD blocked ⇒ candidate dead, per §4.6.
- One-shot law: two pre-measurement fail-closed aborts disclosed in the artifact
  (warmup-invariant scope fix; assembly TypeError) — no rho computed-and-discarded,
  attempt-3 is the single persisted measurement (P-19/P-23 honesty class). See F-2 INFO.

(c) **F-5 (P3-A measured ceiling; P4-A/P4-B declared-band)** —
`falsifier/F5_ceiling_measured.json` + `falsifier/F6_census_counts.json` + census/bars bytes:
- **P3-A recomputed from bytes**: fill-hour-weighted pooled entry/exit medians from
  `F6` histograms × `bars1h_AUDUSD` `s_open` → **1.0 / 1.0 pips** (whole dev),
  **0.9 / 0.9 pips** (last6m 2025-07-01..2025-12-31); RT 2.0 / 1.8 pips; RT@k2.0 4.0 / 3.6
  pips = 5.98 / 5.50 bps at measured mid (recorded 5.98/5.50 — exact). Binding test:
  conditional crossing 1.0 / 0.9 pips vs required ≤ 0.41 @k=2.0 (≤ 0.81 @k=1.0) — **fails at
  both stress levels** (also fails on the entry p25 = 0.8). Ceiling vs skeptic-pinned band
  upper 2.5 bps ≈ 1.62 pips: **−2.38 / −1.98 / −0.38 / −0.18 pips** — exact match to the
  recorded four ceilings. Verdict `CEILING_NEGATIVE_VETO` arithmetic confirmed; this despite
  P3-A passing F-0, F-2 (PASS_PIT ×4) and F-1 — killed by the bill (Q-1 class).
- **P3-B cross-check recomputed from bytes**: hist {h0:205, h1:20, h4:1}; entry hour-0
  `s_open` p50 = **1.3 pips**, exit = hour-19 `s_close` p50 = **1.2 pips**, mid median
  **1.35137** (exact), RT@k2.0 = 5.0 pips = 3.70 bps, ceiling vs band upper 5 bps =
  **+1.30 bps** (exact); last6m +1.24 bps. `CEILING_PASSED_MEASURED` with thin-margin,
  precedent-fragile (2×-stressed RT 7.40/7.52 bps > band 5 bps) and AUDUSD-replicate-negative
  disclosures — moot: P3-B is killed by F-1 (home pair blocked ⇒ candidate dead), which
  this audit independently confirmed in (b).
- **P4-A declared-band kill** (SKEPTIC_F0 §2.6) recomputed from `census_AUDUSD/USDCAD.json`
  `by_session.open` p50s: AUDUSD RT base = 1.0+1.0 = 2.0 pips = **3.10 bps** (recorded 3.1),
  ×2.0 = **6.20 bps** (recorded 6.2); USDCAD RT base = 1.2+1.2 = 2.4 pips = **1.80 bps**
  (recorded 1.8), ×2.0 = 3.60 bps (recorded 3.5 — mid-rounding, see F-5 INFO). Band uppers
  3.0 / 2.5 bps < stressed RT on both pairs; AUDUSD 3.0 < base 3.1. **Kill confirmed.**
- **P4-B declared-band kill** (SKEPTIC_F0 §2.7): AUDUSD band upper 2.0 bps < base book
  3.10 bps; USDCAD 1.6 bps < base 1.80–1.95 bps in every session bucket — below the ×1.0
  book before any stress. **Kill confirmed.** No re-tune legal (frozen bands; own field-8
  kill rules fire).

(d) **F-2 PIT battery** — `falsifier/F2_battery_results.json`: 4/4 laws
(`P3A-QCRD-H1/{AUDUSD,USDCAD}`, `P3B-DINV-1D/{AUDUSD,USDCAD}`) verdict **PASS_PIT**
(M-T, M-F, M-F-ext, M-V {index_shift_pool/mirror_wide/volgate or weekday_shuffle/ungated}
all PASS), `all_pass: true`; harness sha `7daf5dfe…`, law-lib `d5d8d79f…`, dev-loader
`9b3c7b7d…` — all three match the current script bytes. Tests: `pytest tests/` → **13 passed**.

**Kill map (all 7):** C1 = F-0 + F-5 (double kill); C2 = F-0; C3 = F-0; P4-A = F-5
declared-band; P4-B = F-5 declared-band; P3-A = F-5 measured CEILING_NEGATIVE_VETO
(after F-0 PASS + F-2 PASS_PIT + F-1 PASS_F1); P3-B = F-1 ANCESTRY_RHO_BLOCK.
Trial ledger rows 1–7 carry exactly these grounds; observed == published on every row.

## T3 — Zero-PnL: **CONFIRMED**

- Full recursive walk of every committed JSON in the cycle namespace for pnl/equity/profit/
  net_pips/sharpe-like scalar fields: **only `null` values or verdict labels**
  (single non-null hit is the handoff verdict string `no_pnl: "verified by construction…"`,
  not a value). `git grep` for pips/equity/net_pnl fields across committed artifacts: only
  `trial_ledger.jsonl` (all null), the ledger template in `falsifier_run.py` (writes null),
  and `engine.py` (an inherited code path whose outputs are stripped at source — F6's
  `counts_only_law` states it; no committed artifact retains engine pips/equity output).
- The pips numbers that DO exist (F5/F6/census) are **cost/spread-layer** (fill-bar
  `s_open`/`s_close`, session p50s, histograms) — no outcome PnL anywhere.
- `trial_ledger.jsonl`: exactly **7 rows**; every row `net_pnl: null`, `gross_pnl: null`,
  `exclusion_zones: null`, `verdict: NOT_SCORED_FALSIFIED`,
  `fold_or_holdout_tag: PRE_PNL_FALSIFICATION`, labels present on all rows
  (`SINGLE_SOURCE_PANEL`, `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`, `PAPER_TIER`);
  mechanisms C1/C2/C3/P4A/P4B/P3A/P3B; `arm_config_digest: NA_PRE_PNL` everywhere;
  sha-chain evidence pins (`dc94824c`, `0e2e2ab8`, `cf5ef82c`, `c474ef44`) all resolve to
  real ancestor commits on this branch.

## T4 — Zero-holdout-look + sealed integrity: **CONFIRMED (with one LOW disclosure, F-1)**

- `series/` directory does not exist anywhere in the cycle dir (committed or untracked) —
  no scored series persisted.
- `scripts/dev_plane2.py sealed_audit` (run by this lane): `all_pins_match: true`;
  dev pins 27,608 (AUDUSD) / 27,583 (USDCAD) at 1h and 118,275 / 118,231 at 15m —
  identical to the A1 sealed-map pins in SKEPTIC_F0 §4.2 and the manifest `dev_row_pin`s;
  `dev_end 2025-12-31 23:59:59Z`. Holdout rows are **physically present but unfiltered**
  in the bars parquets (2,812 / 2,803 rows @1h; 11,885 / 11,871 @15m in 2026-01-01..06-30) —
  as claimed; the m1agg planes are dev-only (27,608 / 27,583 rows; zero 2026 rows).
- Every consumed plane (.npy targets/shadows) is exactly dev-row-length; F-1/F-2/F-6
  inputs are dev-masked by construction with re-asserted row pins.
- F6 windows: F1..F6 + last6m = 2025-07-01..2025-12-31 (dev-only); the gated round-2 books
  have zero 2026 population.
- **F-1 (LOW)**: the committed `census_AUDUSD.json` / `census_USDCAD.json` span
  2021-01-03..2026-06-30, i.e. their aggregate spread/cost percentiles include the sealed
  2026-H1 (cost-layer only; inherited cohort-1 archive bytes, sha-pinned `d337ff2c…` /
  `27958f5a…`; no returns/PnL). F5 round-2 re-keyed the BINDING measurements to dev-only
  windows and disclosed round-1's census-last6m-2026 usage for the unconditioned family
  book; SKEPTIC_F0 §2.6/2.7 P4 kills used the whole-window census book, whose numbers are
  candidate-ADVERSE (kill direction conservative-safe). No verdict input consumed holdout
  outcome data; "0 holdout looks" holds under the program's outcome-look definition.
  Close arc should carry this disclosure (condition C-2).

## T5 — Freeze artifact: **CONFIRMED**

`freeze/GO1_freeze_art.json` (`erp1_tracka_cohort2_go1_freeze@1`, created 2026-09-26T04:55:00Z):
- `slate: EMPTY — 0 mechanisms survived`; kills table for all 7 mechanisms **matches the T2
  recomputed verdicts field-for-field** (C1/C2/C3 F-0 same-family; P4A/P4B F-5 declared-band;
  P3A F-5 measured veto with 0.9–1.0 vs ≤0.41 @k2.0 and ceiling −2.38/−1.98; P3B F-1
  0.3032/0.3103 representation-robust).
- `budget: used 0 / max 18`, note "0 scored cells; 0 holdout looks; COUNTS ONLY".
- `sealed_windows`: both 2026-H1 windows UNREAD/preserved; sealed map unchanged.
- Pins verified real: worktree `5ed2457b`, `0e2e2ab8`, `752b9028`, `cf5ef82c`, `c474ef44`
  (all ancestors of HEAD); root `3de439ab`, `6a507f58`, `dc94824c` (all in root history).
  Engine inheritance: `tracka_lib 1e09b368` == pinned A7-certified bytes (re-hashed).
  See F-4 LOW for the `pending:` root-report pins item.

## T6 — Budget/denominators: **CONFIRMED**

Registry `used: 0 / max: 18`; freeze `used 0 / max 18`; the ledger contains **zero scored
cells** (all 7 rows `NOT_SCORED_FALSIFIED`, `NA_PRE_PNL`); no fold_or_holdout row anywhere
carries a score; observed == published for all 7 pre-PnL rows (each row's kill grounds
reproduced in T2). P-9 program counters (`researchctl program counters`): 257 published /
260 observed, 0 survivors — cohort-2 adds +0/+0 at close (condition C-3).

## T7 — Governance: **CONFIRMED**

- Worktree tree clean at `a7c3c5c6` at lane start (porcelain empty); this lane adds exactly
  two files under `audits/`, commits nothing.
- No push: branch has **no upstream**; no remote branch contains HEAD.
- Heavy lock: `researchctl locks inspect` → `FREE_PROVEN` (flock free, no live pid).
- Shadow namespaces: `git diff --name-only 017d2464..a7c3c5c6` touches **only
  `research/control/ERP1-TRACKA-COHORT-2/**`** (153 files: data_local/derived 125,
  scripts 16, falsifier 5, freeze 3, tests 2, handoffs 1, root 1). Root-side cycle commits
  (`3de439ab`, `6a507f58`, `dc94824c`, `2fea8fb8`, `11a3497d`) touch only
  `ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort2/**` + registry files. Zero writes under
  FX-RANGEFADE-2M-SHADOW-V1 or PROSPECTIVE-SHADOW-V1 from this cycle; shadow code consumed
  read-only with shas recorded in the manifest (`efb87e37`, `6147beff`).

## T8 — Terminal label adjudication: **`REJECT_ALL` certified**

Umbrella §9 definition: "no mechanism survived its falsifier battery" — exactly the state
proven in T2: 7/7 mechanisms dead pre-PnL (3 at F-0, 2 at F-5, 1 at F-1, 1 at F-5 measured),
slate empty, 0/18 cells. Alternatives ruled out:
- `NO_ELIGIBLE_PROPOSAL` — FALSE: the council produced two freezable, slated mechanisms
  (P3-A, P3-B passed F-0 with armed intake conditions and entered the trial freeze path);
  they died in falsification, not at council.
- `BLOCKED_DATA_OR_SELECTION` / `BLOCKED_SOURCE_OR_SCHEMA` — FALSE: data gates passed
  (census/gate margins, dev planes built, 47/47 shadows constructible); nothing was blocked.
- `BLOCKED_COST_AUTHORITY` — FALSE: cost was MEASURED in authorized space (F-5 round-2
  produced byte-recomputable numbers); the cost kills are vetoes, not blocks.
- `CANDIDATE_PENDING_PROSPECTIVE` / `PROSPECTIVE_*` — FALSE: nothing survived to scoring
  (0 cells, 0 fold looks).
- `TECHABORT_PRESERVED` — FALSE: the two F-1 pre-measurement aborts were fail-closed and
  re-executed cleanly within the one-shot law, fully disclosed; no technical invalidation.

`REJECT_ALL` is therefore the strongest-allowed and correct label; it is an explicit,
expected, non-failure outcome per umbrella §9.

---

## Findings (0 CRITICAL / 0 HIGH / 2 LOW / 3 INFO)

- **F-1 [LOW, T4]** — Census files span the sealed window at the cost layer.
  `census_{AUDUSD,USDCAD}.json` (2021-01-03..2026-06-30) contain spread percentiles
  computed over a window including 2026-H1; inherited cohort-1 archive bytes (sha-pinned),
  spread/cost layer only, zero outcome fields. F5 round-2 binding numbers are dev-only;
  round-1's census-2026 usage for the unconditioned family book was disclosed and superseded;
  P4 kills used the whole-window book in the candidate-adverse direction. No holdout
  outcome look occurred. Action: carry the disclosure into the close arc (condition C-2).
- **F-2 [INFO, T2b]** — F-1 artifact honestly discloses two pre-measurement fail-closed
  aborts (P-19/P-23) and `fold_diagnostics_status: NOT_RUN` (benign dtype-comparison error);
  diagnostics are report-only per SKEPTIC_F0 §4.7 — the immovable gate is unaffected.
- **F-3 [INFO, T3]** — `scripts/engine.py` (inherited cohort-1 engine by value) retains a
  live `net_pips` computation path. For this cycle every engine invocation was counts-only
  with pips/equity stripped at source (F6 `counts_only_law`; verified no committed artifact
  retains engine outputs). Fine as-is; the close commit may note that any future cycle
  copying the engine should strip at the call site, not rely on post-hoc scans.
- **F-4 [LOW, T5]** — Freeze `pins.root_control_plane` lists
  "pending: skeptic F-1 + cost F-5 reports" — accurate at freeze creation, resolved after by
  root commit `2fea8fb8` (both reports now committed). The close commit/registry flip should
  record the resolution so the freeze pin block is not read as unresolved.
- **F-5 [INFO, T2c]** — P4-A USDCAD ×2.0-stressed RT: recorded 3.5 bps vs 3.60 bps by exact
  arithmetic at mid 1.3333 (skeptic's mid ≈ 1.371). Rounding-level; kill direction unchanged
  (band upper 2.5 bps fails either way).

## Binding close-out conditions (owner-gated close arc; none blocks this PASS)

- **C-1 Registry flip** (root, via researchctl): `ERP1-TRACKA-COHORT-2` lifecycle
  `ACTIVE_LIGHT → TERMINAL`; phase → terminal close text; verdict field/labels →
  `REJECT_ALL` (umbrella §9) + `SINGLE_SOURCE_PANEL`, `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`,
  `PAPER_TIER`; head → the close commit sha on `orca/erp1-tracka-cohort-2-integration`
  (Lead commits this lane's two outputs there; this lane does NOT commit);
  `budget: used 0 / max 18` unchanged; `go_phrase_state` stays `REGISTERED_NOT_CONSUMED`
  (GO-2 never consumed, never will be); `s1: SEALED_UNTOUCHED` unchanged;
  `workers: 0`; `next_authorized_action` cleared; note F-4 resolution.
- **C-2 Disclosure carry-forward**: append the F-1 census cost-layer disclosure (census
  aggregates include sealed-window spread stats, inherited cohort-1 bytes, binding verdicts
  dev-only) to the cycle's terminal record so the "0 holdout looks" claim is scoped
  precisely (outcome-look definition).
- **C-3 P-9 stamp** (`research/wayfinder/HYPOTHESIS_LEDGER.md`): cohort-2 row +
  denominators **+0 published / +0 observed scored cells (0/18 used; 7 pre-PnL falsified
  rows; 0 holdout looks; 0 survivors)** — program total re-stamped at 257+0 / 260+0,
  0 survivors. Row content mirrors T8: council 2 slated + slot-left-empty; kills C1/C2/C3
  F-0 same-family (S1 re-confirmed), P3-A F-5 measured veto after F-0/F-1/F-2 PASS
  (killed by the bill), P3-B F-1 ANCESTRY_RHO_BLOCK (0.3032/0.3103), P4-A/P4-B F-5
  declared-band; terminal head `a7c3c5c6` (+ close commit).
- **C-4 FAMILY_FAILURES entries to append** (`research/wayfinder/FAMILY_FAILURES.jsonl`,
  schema `family_failures/entry@1`, append-only; `no_reentry` per handbook §14.3/Q-3):
  1. `TRACKA2-P3A-QCRD-H1` (family: quote-state-gated H1 continuation, AUDUSD+USDCAD
     dev 2021–2025) — CLOSED / SCIENTIFIC_REJECTION; primary `CEILING_NEGATIVE_VETO_F5`
     (measured tight-state conditional crossing 1.0/0.9 pips vs ≤0.41 required @k=2.0;
     ceiling −2.38/−1.98 pips vs band upper 1.62 pips; fails even ×1.0; USDCAD replicate
     −1.05 bps) — with the explicit note that the mechanism passed F-0, F-2 (PASS_PIT ×4)
     and F-1 (worst |rho| 0.0786/0.0883, genuinely decorrelated): the kill is economic,
     not methodological.
  2. `TRACKA2-P3B-DINV-1D` (family: spread-percentile day continuation, USDCAD home) —
     CLOSED / SCIENTIFIC_REJECTION; primary `ANCESTRY_RHO_BLOCK_F1` (pooled worst |rho|
     0.3103 AUDUSD / 0.3032 USDCAD vs H1DONCH/H1TSMOM; STOCH/PDHLOC 0.20–0.29 secondary;
     zero-excluded 0.60–0.74 representation-robust): day-continuation is a momentum-family
     re-label; family collapsses into the census-momentum class.
  3. `TRACKA2-P4A-FIXCERT-01` (fix-window certainty premium) — CLOSED /
     SCIENTIFIC_REJECTION; primary `DECLARED_BAND_COST_KILL_F5` (band upper 3.0/2.5 bps <
     ×2.0-stressed RT 6.2/3.6 bps at own fill hours; AUDUSD 3.0 < base 3.1); re-entry only
     by owner amendment with a new declared band or a cheaper-book pair.
  4. `TRACKA2-P4B-QSKEW-01` (dealer quote-skew inventory signal) — CLOSED /
     SCIENTIFIC_REJECTION; primary `DECLARED_BAND_COST_KILL_F5` (band upper 2.0/1.6 bps <
     base RT 3.1/1.8 bps in every session bucket, before stress); carry-forward: any
     re-entry must add the missing vol-content control.
  5. Addendum (or cross-reference on the existing `TRACKA1-M1-RANGEFADE-PIT` entry):
     cohort-2 F-0 re-confirmed S1 range-edge closure — C1/C2/C3 all
     `VETO_VARIANT_SAME_FAMILY` (three gates, one dead family); range-edge slot space
     permanently closed to same-family replacement within Track A cohorts.
- **C-5 LESSONS entry guidance** (`research/wayfinder/LESSONS.md`): the headline lesson is
  Q-1-class — "a mechanism can be genuinely novel (F-0), genuinely decorrelated from every
  named dead shadow (F-1: 0.0786/0.0883 vs gate 0.20) and PIT-clean (F-2 ×4) and still die
  on measured cost by 2.2–2.4× the required margin (0.9–1.0 pips actual vs 0.41 needed)".
  Sub-points worth recording: (a) cost-first pre-screening — measuring the tight-state
  conditional crossing BEFORE the full falsifier phase would have killed P3-A at council
  cost, not battery cost; the binding cost authority must be the candidate's own
  fill-hour distribution, not the proposer's prior (0.2–0.4 pip/fill was off by ~3×);
  (b) cadence transfer of the momentum null — day-continuation hypotheses must be
  pre-screened against H1TSMOM/H1DONCH-class rho (the momentum family is the default
  hypothesis at every cadence; P3-B died exactly there at 0.30–0.31); (c) declared
  proposer cost bands are systematically optimistic — both open-call P4 candidates died on
  their own frozen bands vs the measured book, validating the frozen-band/no-rescue law;
  (d) process wins to keep: one-shot fail-closed F-1 (two disclosed aborts, zero
  re-litigation), counts-only engine runs, slot-left-empty over weak filler.

---

## Tests executed by this lane (evidence commands)

1. `git -C <worktree> rev-parse HEAD` → `a7c3c5c60f44…`; `status --porcelain` → clean.
2. sha256 re-hash of `t2_planes_manifest.json` (`7cdf3104…`), `f1_rho_run.py` (`76f2a01c…`),
   `tracka_lib.py` (`1e09b368…`), `pit_battery2.py` (`7daf5dfe…`), `qcrd_dinv_lib.py`
   (`d5d8d79f…`), `dev_plane2.py` (`9b3c7b7d…`) — all match artifact pins; **112/112 .npy
   sha256 match the manifest**.
3. Independent Spearman recompute (own average-tie-rank implementation, NumPy only) of the
   four worst shadows from `t2_*_anchor.npy` × `t2shadow_*.npy` — exact to 6 dp (T2b).
4. F5 recompute from `F6_census_counts.json` histograms × `bars1h_*.parquet`
   s_open/s_close — P3-A and P3-B medians/mids/ceilings exact (T2c); P4-A/P4-B census
   session arithmetic (T2c).
5. `dev_plane2.py sealed_audit` → all pins match; holdout rows physical, unfiltered (T4).
6. Recursive PnL-field walk over all committed cycle JSONs + `git grep` sweep → nulls only (T3).
7. `pytest tests/` → 13 passed. `researchctl locks inspect` → FREE_PROVEN.
8. `git diff --name-only 017d2464..a7c3c5c6` → cycle-dir only; upstream check → none.

— Lane `a7-terminal` (A7 terminal audit), 2026-09-26. Read-only except the two output files
in `audits/`; no commit, no registry write, no push.
