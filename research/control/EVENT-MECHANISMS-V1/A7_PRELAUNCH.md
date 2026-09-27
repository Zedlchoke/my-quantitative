# A7 PRELAUNCH AUDIT — EVENT-MECHANISMS-V1 (2026-09-27)

Auditor: A7, independent, fresh context, no stake in the cycle passing.
Scope: verify from artifacts (not claims) that the cycle may proceed to the
owner GO-scored gate. This audit repairs nothing; it records verdicts and
findings only.

Measured state at audit: worktree
`.worktrees/event-mechanisms-v1/integration`, branch
`orca/event-mechanisms-v1-integration`, HEAD `71eab88f` (delta-r3 handoff
commit); root `main` at `4bb4a4e4`; all 13 main-branch control files
byte-identical to their worktree copies (diff-verified 13/13 SAME).
Audit worktree status: only the disclosed untracked raw `.jsonl` record
tables + this A7 file; nothing modified.

---

## 1. Chain verification — PASS

All named control files exist and were read in full (main + worktree):
OWNER_DIRECTIVE, INTAKE_2026-09-27, LESSON_TO_GATE_MATRIX,
SCREENING_MATRIX (+ court section), SKEPTIC_REPORT, G2_DATA_GATE,
G3_FREEZE + ADDENDA r1/r2/r3, A7_PLAN_REVIEW, OWNER_PACKET,
DATA_GAP_OWNER_ACTION_MATRIX, TRIAL_LEDGER.jsonl, data_gate/ (7 probes +
sha256 manifest). Worktree artifacts read: lane_s/ (REPORT, RESTORE,
MUTATION, N4, S7 fixtures), engine/ (REPORT incl. DELTA r3, emv1/ code,
run/, tests/, evidence/, dryrun/), lane_x/ (ambiguities.md AMB-01..16,
engine_x/, output/ books+census, compare/, evidence/), G5_VERDICT.md,
reconciliation/ (compare_r3.py + comparison_results.json), handoffs/
(4 × zcode_orch_v3_handoff@1).

Commit chain on `orca/event-mechanisms-v1-integration` (git log verified,
each handoff commit exists):

| edge | dispatch_sha | substance commit | handoff commit |
|---|---|---|---|
| G3 r2 → lane S | `656c106a` | `33b9a0e5` | `f1fc2bd3` |
| lane S → lane I | `f1fc2bd3` | `d275ec50` | `50cbd728` |
| lane I → lane X | `50cbd728` | `33d43210` + `26e8983b` | `33467159` |
| lane X → delta r3 | `33467159` | `f32951a3` | `71eab88f` (HEAD) |

Every handoff JSON's dispatch_sha equals the prior handoff's commit_sha;
lineage chains exactly as claimed.

## 2. Owner-directive conformance — PASS

**G4 PIT battery — ran, with evidence.** (a) Unfinished-window:
`guard.assert_readable` raises `LookaheadRead` on bars whose 16:00-ET close
is after the decision instant; planted-future-bars invariance tested
(`tests/test_unfinished_window.py`, 3 tests). (b) Future-mutation: lane S
S6 re-fetch mutation check 20/20 byte-identical → NO_MUTATION
(`lane_s/MUTATION_CHECK.md`); engine digest pins fail-closed at load.
(c) Panel-truncation: replay 318/318 V1 entry-prefix + 318/318 V2
full-record byte-identical (seed 7, 300 sampled + 18 fold-boundary events;
`evidence/truncation_replay.json` `all_match: true` — re-verified by this
audit). DST/session fixtures S7 3/3 + 9 hand fixtures reproduced.
Determinism: full-chain double-run 10/10 (lane I, delta re-run) + 6/6
(lane X). Tests re-run logs: 35/35 and 42/35→**42/42** passed (both
`pytest_run.txt` tails read directly).

**G5 independence — preserved.** Commit order verified: lane X
implementation `33d43210` (20:24:31Z+0700) contains ONLY lane_x files
(24 files: engine_x, tests, pre-built books, ambiguities) — zero
comparison code, zero lane-I artifacts; comparison lands later in
`26e8983b` (20:40:38). Books were built from G3_FREEZE + r1/r2 alone
before any comparison, per the P-4 law. Residual: both implementations
co-locate in one worktree; separation is by agent author context (see L2).

**G6 cost ceiling — traceable, verified by hash.** Engine
`cost_evidence.json` pins `frozen_contract.blob_sha256 =
b7d4464e8aa91588eb01adf39d48da32e96b8fa9b4d1c14554683f5a918b8593`,
`source_path research/control/stocks_amihud_retest_v1/d1/cost_contract.json`
@ `orca/stocks-amihud-retest-v1-integration`, frozen 2026-09-23
(pre-cycle). **This audit re-measured**: `git show
orca/stocks-amihud-retest-v1-integration:research/control/stocks_amihud_retest_v1/d1/cost_contract.json | shasum`
= `1d5708f7d5d24d121169def45cc91480b0f1ba8d` (SHA-1 of content); git blob
object sha = `62fe611f26bf29c602dea9920d245f9b9ce6afc8`; content SHA-256 =
`b7d4464e8aa91588eb01adf39d48da32e96b8fa9b4d1c14554683f5a918b8593` —
**EXACT match** to the engine's pinned claim. Bands 10/15/25 bps, DV
floor $2M/60s, cap 0.15, stress ×2.0 all read from that contract; no new
numbers introduced. PROXY-PRIOR label carried (0/10 measured components).

**A2 NOT_RUN_THIN — immutable floor applied without relaxation.**
F-ADJ-1 (r3) declares A2 NOT_RUN_THIN; frozen floors {≥100/fold, ≥400
total} appear unchanged in `dryrun_manifest.json` (`floors:
{per_fold_min: 100, total_per_anchor_min: 400}`); no test or census
relaxes them; no scored A2 cell is presented at the GO gate. BTC-H4-TWO-
REGIME precedent honored.

**FX/crypto boundaries — clean.** No scored or PnL computation exists
anywhere (§3). Recursive grep over all output/evidence/dryrun/compare/
reconciliation trees for fx/crypto surfaces (eurusd|gbpusd|usdjpy|audusd|
usdcad|xauusd|dukascopy|binance|btcusd|ethusd|solusd|funding|perp|
liquidation): **zero files hit**. Both engines read only stocks staging
(`.staging_eventmech`, NG6 panel, form4 estate). G1 court verdicts (D5/D7
VETO, D6 BLOCKED_DATA, D8 NOT SCORED) hold; no crypto/FX surface was
touched by any lane.

## 3. PnL-absence proof — PASS (independently re-scanned)

This audit ran its own recursive scan (not the engine's): 50 structured
output files (json/jsonl/csv, incl. gzip) under the cycle tree
(engine/evidence, engine/dryrun, lane_x/output, lane_x/compare,
lane_x/evidence, reconciliation, lane_s, data_gate) — **0 forbidden keys**
at any depth for {pnl, profit_factor, expectancy, drawdown, sharpe,
net_return, gross_return, win_rate, hit_rate, avg_trade, per_trade, pnr,
_ret, ret_, return}. Record-level sampling: `a1_decisions.jsonl.gz`,
`a2_decisions.jsonl.gz`, `lane_x/output/A1_anchor_book.jsonl.gz` carry
decision-record fields only (prices, sessions, cost bps, flags, strata,
folds) — no exit-minus-entry return exists in any record; lane X books use
the same whitelist. Dry-run evidence verified: `arms_scored: false`,
`real_money: false`, `record_kind: DECISION_RECORDS_ONLY...`,
`pairwise_all_distinct: true` (15 arm pairs), engine's own
`forbidden_field_scan` clean (16 files). TRIAL_LEDGER.jsonl: 0/0
denominators, seed + exposure-map rows only, no scored rows — identical
(main and worktree, byte-diff SAME).

## 4. Freeze discipline — PASS

Commit ordering: r1 landed in `ead23f6c`, r2 in `656c106a` — both BEFORE
any book existed (first books `33b9a0e5`→`d275ec50`). No outcome-bearing
artifact exists anywhere (§3), so "no PnL before addenda" holds trivially
and is proven, not assumed. r3 + the rebuilt books landed atomically in
`f32951a3` (see L1).

r3 frozen-constants spot-check (all unchanged): strata S1[00:00,09:30)/
S2[09:30,16:00)/S3[16:00,20:00)/S4[20:00,24:00) ET unchanged (S7 fixtures
+ tzlaw tests pin them); holds 5/10/20 unchanged (hold_sessions on
records; G5 compared hold_sessions byte-identically); $100k A2 value floor
unchanged (BELOW_VALUE_FLOOR census); folds F1–F4 unchanged (boundary
fixtures); floors {100, 400} unchanged; cost bands 10/15/25 bps + DV
thresholds unchanged. r3 contains only mechanics/ambiguity rulings (D-1
spec-compliance fix, D-2 loader fix, AMB-01..16). AMB-1 (WKND as anchor
member) has **measured zero production effect**: lane X census
`weekend_bucket_booked: 0` for both A1 arms, lane I "weekend candidates: 0
(both lanes, measured)" — the population movement came from the AMB-7 exit
roll (412 rows) and the D-2 case-fix, both mechanics.

## 5. Populations — PASS

Cross-checked across three independent artifacts (engine REPORT DELTA
table, lane_x/output/census.json, dryrun_manifest.json — all agree):

| arm | F1 | F2 | F3 | F4 | total | floors |
|---|---|---|---|---|---|---|
| A1-ANCHOR (lane I) | 3,679 | 4,013 | 2,553 | 3,851 | 14,096 | PASS |
| A1-ANCHOR (lane X) | 3,679 | 4,013 | 2,554 | 3,852 | 14,098 | PASS |
| A1-N2 | 4,873 | 4,778 | 2,633 | 2,281 | 14,565 | PASS |
| A2-ANCHOR (lane I) | **0** | 1,606 | 664 | 633 | 2,903 | F1 FAIL → NOT_RUN_THIN |
| A2-ANCHOR (lane X) | **0** | 1,727 | 665 | 445 | 2,837 | F1 FAIL → NOT_RUN_THIN |

A2 F1=0 substrate fact evidenced: engine REPORT E3 measures form4_stream
P-row coverage by year (2018: 8,463 … 2025: 1,048; **no 2015–2017 rows
exist in the staged bytes**); G5_VERDICT states the span 2018-01..2025-05;
pre-2018 re-fetch is www.sec.gov 403-blocked = BLOCKED_DATA. Contamination
under the 40% bar: A1 max 9.81% (F4); A2 pre-delta max 23.88%.

Ancestry rho battery (pre-PnL, on committed bytes): bar 0.20 immovable,
`any_over_bar: false`, `over_bar_rows: []`; max |pearson| observed 0.1588
(declared_plan_cadence_180d, F4). Merge-condition stream rho A1-vs-A2 =
2.3e-05 — A2 does NOT collapse into A1 (but overlap_points = 26; see L7).

## 6. Denominator / budget — PASS

Root `plans/CYCLE_REGISTRY.json` EVENT-MECHANISMS-V1 row (read at ROOT):
`budget {used: 0, max: 6}`; `go_phrase "GO EVENT MECHANISMS V1 SCORED
EXECUTION"`, `go_phrase_state REGISTERED_NOT_CONSUMED`; `s1
SEALED_UNTOUCHED`; `workers 0`; S0 OPEN. Trial ledger denominators 0/0.
Observed M2 below: the row's phase text and head field predate the lanes.

## 7. Residual-risk list (owner briefing before typing GO)

1. **A2 is not adjudicated this cycle — twice over.** It is NOT_RUN_THIN
   on a substrate gap (no 2015–2017 Form-4 bytes exist; re-fetch 403-
   blocked), and where A2 does exist its event definition remains
   implementation-dependent: 762 of the 789 residuals (599 issuer-day
   basis + 163 unpriced-drop semantics) are unruled spec ambiguity, so the
   two implementations build structurally different (both lawful) A2 event
   sets (2,903 vs 2,837, only 2,271 shared instants). Any future A2
   attempt needs an owner door (GA-1 unblock or owner-directed substrate-
   honest re-freeze) AND an r4-style adjudication first.
2. **What a GO buys is proxy-priced and reconstruction-screened.** All G6
   ceilings are PROXY-PRIOR (stocks cost plane 0/10 measured; the band
   contract is verified-authentic but proxy). The 8-direction screening
   enumeration was reconstructed from the owner's directive text (E-P1;
   plan_at.md is an unapproved DRAFT). Owner ratification items remain
   open by design: D3 event-book veto (F-4), D5/D7 vetoes, D6
   BLOCKED_DATA, direction-list confirmation.
3. Registry row staleness (M2) — must be refreshed at landing before the
   owner consumes the packet.
4. Positives worth the owner's attention: A1 anchor populations are deep
   (14k events, ≥2,500 per fold), both implementations agree 99.97–100% on
   key sets with all 789 residuals attributed, zero defects, and the
   entire evidence chain is hash-pinned and independently re-verifiable.

## Findings

| # | Severity | Finding | Disposition |
|---|---|---|---|
| M1 | MEDIUM | A2 event definition implementation-dependent: 762/789 residuals (issuer-day basis 599, unpriced-drop 163) are unruled spec ambiguity; two lawful A2 event sets exist | NOT blocking this gate (A2 NOT_RUN_THIN, no scored A2 cell presented); MUST be adjudicated before any future A2 scoring |
| M2 | MEDIUM | Registry row stale: phase text still "G4–G7 NOT_RUN", head `6ac5f36d` vs worktree HEAD `71eab88f` | Refresh by integration lead in the landing commit that carries this A7 file; required before owner consumes packet |
| M3 | MEDIUM | Screening enumeration is a reconstruction (E-P1); D3/D5/D7 veto ratifications open | Owner ratifies/amends at the GO gate; already surfaced in OWNER_PACKET |
| L1 | LOW | r3 addendum + rebuilt books landed in one commit — commit granularity cannot independently prove addendum preceded rebuild | Mitigated: zero-outcome state proven, both-lane convergence to byte-identity on all 16 ruled AMBs |
| L2 | LOW | G5 independence is protocol-preserved (commit order + file contents) but implementations co-locate in one worktree; author-context separation unverifiable from git | Inherent to the P-4 protocol; accepted with note |
| L3 | LOW | Cost ceilings PROXY-PRIOR (0/10 measured) | Label carried; GA-2 upgrade path recorded |
| L4 | LOW | A2 thin where it exists (F2–F4 only; 2.8–2.9k events) | NOT_RUN_THIN stands; owner doors recorded |
| L5 | LOW | Append-only REPORT layering: E8/E6 pre-delta counts (14,109 / 15/15) coexist with delta r3 numbers (14,096 / 10/10) | Honest layering; reader must use DELTA section; no action |
| L6 | LOW | 26/2,169 panel names produce no series (A1 606 NO_PANEL exclusions); N4 map join is load-bearing | Disclosed + counted; N4 verified 12/12 alive + 13/13 dead at SEC |
| L7 | LOW | Merge-condition stream rho measured on only 26 overlap points | Value 2.3e-05 far under 0.20; moot this cycle (A2 not presented) |

**Severities: 0 CRITICAL / 0 HIGH / 3 MEDIUM / 7 LOW.** All MEDIUMs are
either not blocking this gate (M1) or are landing-time actions with named
owners (M2, M3).

## Verdict

Chain, owner-directive conformance (G4/G5/G6, A2 immutable floor, FX/crypto
boundaries), PnL-absence, freeze discipline, populations, and
denominator/budget all verify from artifacts. No HIGH or CRITICAL issue is
unresolved.

**A7_PRELAUNCH_AUTHORIZED** (0 HIGH/CRITICAL unresolved)
