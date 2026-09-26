# A7 TERMINAL REPORT — PWS-CX-SOLUSDT-C1 — (second independent run, supersedes prior at same paths)

## VERDICT: CONFIRM_WITH_FINDINGS — the terminal claim `NO_ELIGIBLE_PROPOSAL` is CONFIRMED

- 0 HIGH / 0 CRITICAL; 1 MEDIUM (verdict-neutral, kill re-verified on the missing
  half); 4 LOW. No blocking issue. The close is sound as a pre-PnL empty-slate
  termination.
- Auditor: A7 independent terminal auditor, fresh context, no inherited
  conclusions. All recomputation below is from raw bytes with throwaway scripts
  under `/tmp/a7_audit/` (never inside the worktree); interpreter strictly
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`. No network, no sealed
  data opened, no repairs made to any implementer artifact.

## 0. Scope and independence

- Audited: the terminal close of `PWS-CX-SOLUSDT-C1` — verdict
  `NO_ELIGIBLE_PROPOSAL`; GO-1 consumed 2026-09-26T11:14Z under owner delegation
  (`research/control/PWS-PROGRAM-V1/OWNER_DELEGATED_DECISION_charter_and_go1_2026-09-26.json`,
  referenced by C0 §header); council P1 0 proposals (11 directions self-killed at
  F-0), P2-1 TAILPAYER-RUN-REGIME CAPTURE `VETOED_SAME_FAMILY`; 0/18 scored
  cells; 0 outcome views; S1 `SEALED_UNTOUCHED`; GO-2 phrase dies UNCONSUMED;
  IDENTITY_REGISTRY I001 PROPOSED→F0_KILLED (1/100 ceiling consumed).
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-solusdt-c1/integration`,
  branch `orca/pws-cx-solusdt-c1-integration`. HEAD at session start
  `caccc2e6d587486c8f78018f39eef31b30bc29cd` (= dispatch sha, verified) — see
  §5/L4 for the mid-flight branch advancement.
- Independence: the dispatch-expected prior state (`lifecycle ACTIVE_LIGHT`,
  `go_phrase_state REGISTERED_NOT_CONSUMED`) no longer held when I read the root
  registry (already flipped TERMINAL at 13:57:18Z by the owner, citing a prior
  A7 audit committed as `033c2bef` + errata `c3671fad` while my session ran).
  I did NOT read the prior A7 report until my own recomputation was complete;
  every number below was produced and pinned by my own scripts first. My report
  replaces the prior lane's report at the shared `audits_a7/` path; my handoff
  lands at the dispatch-mandated `handoffs/` path, which was unoccupied (the
  prior lane had placed its handoff at `audits_a7/HANDOFF_a7_terminal.json`,
  which remains intact as committed evidence at `033c2bef`).

## 1. Artifact inventory + sha256

All 16 required artifacts exist under `research/control/PWS-CX-SOLUSDT-C1/`:

| Artifact | sha256 | bytes |
|---|---|---|
| C0_control_plane.md | b3874fa787d932cc9dad89103a5776f5d8321217ab4b7c2277e55218895d5cd3 | 1986 |
| C1_data_gate_REPORT.md | 2aac860b46cbbd7ca16289c46c07708a6a2e62006e16994da1ff3ab17126ea5c | 15528 |
| C1_machine_KLINE_CENSUS_SOLUSDT.json | cf567ff5249732b175590f03de6b0089b186700c4148ddb5e5005c386e76776d | 8600 |
| C1_machine_FUNDING_STATS_SOLUSDT.json | 688619e4eab5c12d0dff630f16ca8be09c48712403e88e0036b85e049b71dfbe | 10106 |
| C1_machine_SPREAD_CENSUS_SOLUSDT.json | a6d0d58c1dfb30d810a10b0e95d5ba67df7a2870f4342a52fa87956ae0bb42ab | 30508 |
| C2_EXPOSURE_VERIFICATION.md | 5f0b02a15435baa31d621d4bcb6e02d13d18fde27edb46a99b0ed5ed968e4550 | 7163 |
| C3_council_synthesis_and_freeze.md | 12287bdd067dad51f2caa90befd603ac10241a4d44d62572d47f70af28217de4 | 2927 |
| CYCLE_VERDICT.md | c985c73f32ed7198af651b2933453cc5fb91be426546292387cf670d1db9a62c | 3497 |
| council/P1_PROPOSALS.md | e3135e1b38dd16d7222dbe8dd2c7cc8d453d12f02a762b646655d20890086026 | 13541 |
| council/P2_PROPOSALS.md | a1e236fddf1464728826950202922fc08bedd8419aba7f53134757c27bcc6347 | 20826 |
| council/SKEPTIC_F0_REPORT.md | ef25fb097aa785c457d8c06ccad813fc3d6355942584466ab618666c9ab0dc36 | 16828 |
| handoffs/HANDOFF_council_P1.json | 0e86c05a1dcb30ae1f71961fa8ce11af8eed6a499b846954955f588c12d267fa | 5035 |
| handoffs/HANDOFF_council_P2.json | ae1bd651640c1b225980bc030c21460b005dfb4f89d34fc2444b485ed8ff10a5 | 8002 |
| handoffs/HANDOFF_skeptic_f0.json | 15d37d82c7fd0f46dd33dd664e6abc7e867b8251016679d6aaeffd14f606932d | 12604 |
| handoffs/HANDOFF_c1c2_data_pit.json | a6bfea8a6230d55fce072c82735bf87384b713673e7c3dbf38f7c86a333fa237 | 13068 |
| trial_ledger.jsonl | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 (empty-file hash) | 0 |

Raw-source manifest check: `data_local/funding/fapi_scan2026_H1_SOLUSDT.json`
sha `3dcac8d8…332c0`, `fapi_scan2026a_H2_SOLUSDT.json` sha `3c536649…1cb1c`,
`SOLUSDT_funding.json` sha `9e850cb4…a1036` — all three match
`C1_machine_FUNDING_STATS_SOLUSDT.json` `sources` pins exactly. All 72 kline
zips match `C1_machine_KLINE_CENSUS_SOLUSDT.json` `zip_sha256_manifest_json`
(0 mismatches).

## 2. Independent recomputation (raw bytes → my numbers vs expected)

### 2a. Funding census — EXACT

Merged H1+H2, deduped on `fundingTime` (boundary duplicate dropped), sorted.

| Stat | Mine | Expected (C1/skeptic) | Delta |
|---|---|---|---|
| n settlements | 6580 | 6580 | 0 |
| mean | +1.37616869300912e-06 rate = +0.0137617 bps | +0.0138 bps | rounding only (bit-exact to machine float) |
| median | +0.85755 bps (8.5755e-05) | +0.858 bps | rounding only (bit-exact) |
| neg_share | 1883/6580 = 28.6170% | 28.62% | 0.0030 pp |
| zero-rate settlements | 1 | 1 | 0 |
| 6y sum | +0.9055% | +0.906% (P2 §0) | 0.0005 pp |
| worst / max | −200.00 / +33.25 bps | −200 / +33.2 | 0 |
| first / last | 2020-09-13T16:00:00.004Z / 2026-08-21T16:00:00.001Z | same | 0 |
| anomalous spacings (<7h) | 101, confined to 2022-11-09T16:00Z..2022-11-18T08:00Z | 101 | 0 |

### 2b. Run-structure math — EXACT

Maximal same-sign stretches, zeros break runs (on the 6580 grid):

- Maximal runs: **1234** (expected 1234, Δ0). len≥3/5/8: **484/258/153**
  (expected 484/258/153, Δ0).
- Theta sweep (K=3, entry observable = first-K mean): the skeptic counts are
  reproduced **exactly only under the positive-side signed convention** — runs
  of positive settlements with first-3 mean ≥ θ, no span pin:
  θ≥1 → **56**; ≥2 → **3**; ≥3 → **2**; ≥4 → **0** (all Δ0).
- Skeptic §2 episode table reproduced exactly under: positive-side runs,
  len≥3, whole-run wall-clock span ≥ K×6h (=18h), state ON from the K-th
  settlement through run end: episodes **147/48/8/3/1** and occupancies
  **48.5/26.7/3.9/1.9/0.2%** at θ=0.5/1.0/1.5/2.0/3.49 — all five rows Δ0.

### 2c. Ceiling × power emptiness — CONFIRMED

RT_base = 10 bps fee + 0.469 bps spread p50 = **10.469 bps** (spread p50
0.46883 present in the machine census); ×1.5 = 15.703, ×2.0 = 20.938;
θ_min = RT/3 (proposal's H_min=3) = **3.490 / 5.234 / 6.979 bps** (expected
3.49/5.23/6.98, Δ≤0.004).

- One-sided (skeptic) convention, θ≥5.23: K=3 → **0** episodes; K=5 → **1**
  (12 settlements); K=8 → **1** (12 settlements). θ≥6.98: 0/0/1. vs the ≥100
  closed-RT power floor: missed by ~two orders of magnitude at every cell.
- Grid maximum: scanning ALL θ satisfying the ceiling law per (K, book), the
  most permissive cell (K=5, base book, θ≥3.49) yields **17 episodes** —
  ∩(θ, K) feasible set for (ceiling law ∧ ≥100 RT) is **EMPTY**, as claimed.
- Two-sided re-check (my MED finding below): |first-3 mean| ≥ 5.23 with the
  span pin yields 8 additional negative-side episodes (196 settlements) —
  8 ≪ 100, so the intersection stays empty under the literal two-sided
  reading as well.

### 2d. Ancestry rho spot-check — CONFIRMED (bar 0.20 broken at every power-viable gate)

Gate state θ=0.50 bps (pinned convention of §2b), pooled Spearman on the
6580-settlement grid, shadows = trailing-W funding-level receiver states and
unconditional receiver:

| Shadow | Mine (trailing incl. current) | Mine (trailing excl. current) | Skeptic | 
|---|---|---|---|
| W=3 (1D) | +0.623 | +0.608 | +0.607 |
| W=9 (3D) | +0.566 | +0.541 | +0.540 |
| W=21 (7D) | +0.510 | +0.496 | +0.493 |
| W=90 (30D) | +0.371 | +0.366 | +0.353 |
| unconditional receiver | **+0.615** | +0.615 | **+0.615 (exact)** |

Max deviation 0.018 (incl.-current) — exact match need not be expected across
shadow warm-up conventions, and the unconditional anchor pins the gate-state
construction exactly. At θ=1.00 (48 episodes, also power-viable): +0.387 /
+0.347 / +0.321 / +0.231, uncond +0.383 (skeptic +0.377/+0.333/+0.310/+0.203/
+0.383). Verdict implication: rho = 0.23–0.62 at every gate with ≥48 episodes —
1.15–3.1× the immovable 0.20 K-ANC bar; the run-gate is a smoothed funding
LEVEL, not an incremental representation. Persistence mechanics also reproduce:
rate autocorr lag-1/2/3/6 = **0.853/0.780/0.731/0.527** (exact), P(next
settlement same sign) = **0.813** (claim 0.812).

Two-sided signed re-check (position +1 short-receiver in positive regimes,
−1 long-receiver in negative): θ=0.5 (248 episodes, 60.0% occ) rho 0.428–0.699;
θ=1.0 (101 episodes, 34.3% occ) rho **0.332–0.506** — all above the bar. The
same-family kill holds under both the skeptic's one-sided measurement and the
proposal's literal two-sided text.

K-CONC arithmetic: negative mass **7252.5 bps** (exact); 2022 share **59.1%**
(exact); FTX anomaly-window share **42.3%** (claimed 42.2% — window-edge
rounding); deepest capped prints — see finding L1.

### 2e. Klines census — EXACT

Full recount of all 72 monthly zips (`data_local/vision/klines_um_SOLUSDT_1h/`,
72/72 zip sha256 verified against the machine manifest): **52,145 bars**
(expected ~52,145, Δ0); 0 duplicate open times; first 2020-09-14T07:00Z, last
2026-08-31T23:00Z; ideal grid 52,265; **missing exactly 120** in exactly two
windows — 2022-02-26T00:00Z..2022-02-28T23:00Z (72) and
2022-04-01T00:00Z..2022-04-02T23:00Z (48); all 72 monthly counts match the
machine file.

## 3. Trial accounting & gate consistency — PASS

- `trial_ledger.jsonl`: **0 rows** (0 bytes; `wc -l` = 0).
- Root registry `plans/CYCLE_REGISTRY.json` row PWS-CX-SOLUSDT-C1: budget
  **{used: 0, max: 18}**; go_phrase `GO PWS CX SOLUSDT C1 SCORED EXECUTION`;
  s1 `SEALED_UNTOUCHED`; workers **0**; events trail documents GO-1 consumption
  11:14Z under owner delegation (heartbeat 11:15:21Z; C0 authored 11:15Z under
  the charter) and the terminal flip at 13:57:18Z with phase "GO-2 died
  UNCONSUMED". Dispatch-era expectations (`ACTIVE_LIGHT`,
  `REGISTERED_NOT_CONSUMED`) match the C0-time state; the root row had already
  been flipped TERMINAL by the owner before my artifact commit — see L4.
- Root `IDENTITY_REGISTRY.jsonl`: exactly **2 rows**, both id
  `PWS-CX-SOLUSDT-I001`: PROPOSED (13:02:13Z) → F0_KILLED (13:59:00Z),
  `status_evidence` citing `council/SKEPTIC_F0_REPORT.md` +
  `handoffs/HANDOFF_skeptic_f0.json` (VETOED_SAME_FAMILY; rho 0.353–0.615;
  ceiling×power empty; K-CONC 59.1%/42.2%) — evidence paths resolve in-worktree.
  1/100 identity ceiling consumed.
- Outcome sweep: grep over the cycle control namespace for
  `pnl|scored_cell|outcome_view|SCORED_RUN|net_edge|sharpe|drawdown` — every
  hit is prose inside verdict/council/skeptic/handoff documents asserting
  outcome-blindness or quoting cost-book-class statistics. **No outcomes/ dir,
  no scored-run file, no return series, no PnL number exists anywhere in the
  cycle's artifacts.** The only numbers are funding/spread/kline census
  statistics and funding-plane representation correlations — cost-book class,
  per dispatch authorization.
- Shadow/worker: registry `workers: 0`; no worker/shadow files touched by any
  lane artifact; heavy lock `FREE_PROVEN` at audit time.

## 4. Findings

| ID | Severity | Finding | Verdict impact |
|---|---|---|---|
| M1 | MEDIUM | **The skeptic's F-0 representation arithmetic is one-sided** (positive-rate/short-receiver runs only) while P2-1 is explicitly two-sided. Pinned by exact reproduction: every skeptic count (episodes 147/48/8/3/1; sweep 56/3/2/0; ceiling 0/1/1) matches ONLY under the positive-side convention. Under the literal two-sided reading the headline zeros change: sweep \|first-3 mean\|≥4 bps → 10–12 runs (not 0); ceiling (K=3, θ=5.23) → 8 negative-side episodes (2020-11-22, 2020-11-26..12-02, 2020-12-12..16, 2021-01-04..07, 2022-11-08..13 FTX len-51, 2022-11-17..12-02, 2022-12-28..2023-01-09, 2025-10-11..13). | **None — kill verified on the missing half by my own recompute:** 8 ≪ 100 power floor (ceiling×power stays empty two-sided); 4/8 deep runs are 2022-11..2023-01 FTX-season (K-CONC remains structurally unreachable); two-sided signed rho 0.332–0.506 at θ=1.0 and 0.428–0.699 at θ=0.5 — all > 0.20 bar. `VETOED_SAME_FAMILY` survives both readings. Binding on any REUSE of the F-0 math: state the gate convention explicitly. |
| L1 | LOW | Deep-print concentration misstated in skeptic prose: "the 4 deepest settlements (−200 bps each) = 13.8%". Raw bytes: **7 settlements at exactly −200 bps = 1,400 bps = 19.3%** of the 7,252.5 bps negative mass; 13.8% corresponds to 5 prints. | None — the error UNDERSTATES concentration; K-CONC kill is strengthened. |
| L2 | LOW | C3/CYCLE_VERDICT prose "rho 0.353–0.615 at every power-viable gate" quotes only the θ=0.5 row; at θ=1.0 (also power-viable, 48 episodes) the W=90 cell is 0.203 (skeptic) / 0.231 (mine, incl-current) — effectively at the 0.20 bar. | None — the three nearest-ancestor windows and the unconditional receiver stay 0.31–0.62 at every power-viable gate; the load-bearing kill is the skeleton test + measured gate-incrementality failure. |
| L3 | LOW | C3 says "handoffs/ (5 handoff JSON đúng schema)"; `handoffs/` holds **4**. The 5th valid cycle handoff is the pre-GO-1 child-plan review at root `research/control/PWS-PROGRAM-V1/plan_review/HANDOFF_a7_child_plan_review.json` (existence verified). | None — bookkeeping pointer imprecision; all evidence resolves. |
| L4 | LOW (governance) | Stale-dispatch / audit supersession: my dispatch expected HEAD `caccc2e6` + registry `ACTIVE_LIGHT`/`REGISTERED_NOT_CONSUMED`; while my session ran, a prior A7 lane committed audit artifacts (report at the shared `audits_a7/` path, handoff at `audits_a7/`) in `033c2bef` plus errata `c3671fad`, and the owner flipped the registry to TERMINAL (13:57:18Z) citing it. My independent re-audit replaces the report at the shared path and adds the handoff at the dispatch-mandated `handoffs/` path (prior versions preserved in history at `033c2bef`); registry `head` lags my commit until the owner re-points it — the same same-commit limitation prior lanes recorded. Master reconciliation note: this report is a SECOND independent confirmation with convergent numbers and the same findings class. | None for the technical close; master may re-point the registry head and record the double-confirmation. |

## 5. Verdict

**CONFIRM_WITH_FINDINGS.** The terminal claim `NO_ELIGIBLE_PROPOSAL` is
CONFIRMED: the council legitimately produced 0 freezable mechanisms after F-0
courts; the single P2 proposal is correctly `VETOED_SAME_FAMILY` on measured
evidence that I independently reproduced from raw bytes (funding census exact;
run/episode/theta-sweep arithmetic exact under the identified convention;
ceiling×power intersection empty at every (K, θ); ancestry rho 1.15–3.1× the
0.20 bar at every power-viable gate, robust two-sided; K-CONC 59.1% single-fold);
trial accounting is clean (0/18 cells, empty ledger, zero outcome views, S1
sealed, workers 0, GO-2 unconsumed→dead at close, I001 PROPOSED→F0_KILLED at
1/100). 0 HIGH / 0 CRITICAL. The MEDIUM finding is verdict-neutral (kill
re-verified on the missing half) and binds only future REUSE of the F-0
method; the four LOW findings are documentation/governance precision items.

— A7 INDEPENDENT TERMINAL AUDITOR, PWS-CX-SOLUSDT-C1, 2026-09-26.
Recompute scripts (throwaway, outside the worktree): `/tmp/a7_audit/
a7_funding_runs.py`, `a7_sweep_explore2.py`, `a7_rho.py`, `a7_refine.py`,
`a7_klines.py`, `a7_two_sided_rho.py`.
