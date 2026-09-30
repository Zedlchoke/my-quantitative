# EOSV2 STOP-1 SCORED REPORT — ETHUSDT-OPEN-SEARCH-V2

**Typed STOP-1 verdict (per freezes/STOP1_charter.md and the frozen verdict
enum): `ETHUSDT_OPEN_SEARCH_V2_NO_INCREMENTAL_VALUE`** — zero of 4 scored
lane-B cells pass the gate battery. `all_pass_cells: []`. This matches the
charter's preregistered honest prior (lane-B weights correlate 0.45–0.67
with the ETH-trend reference; the G3 ALWAYS_ON wall is +1.65M raw net).

All numbers below are transcribed verbatim from the frozen runner's own
artifact `scored/scored_summary.json` (schema `eosv2.scored_run@1`,
built 2026-09-30 by `scripts/run_scored.py` scored mode, engine
`eosv2_engine.py` sha256 `cf1f36d5…` byte-frozen). Nothing recomputed,
reformatted-in-value, or adjusted by this lane.

## 1. Run identity and authorization

| item | value |
|---|---|
| GO | `GO ETHUSDT OPEN SEARCH V2 SCORED EXECUTION`, transmitted 2026-09-30T21:20:00Z by co-owner delegation (two-key complete) |
| Two-key evidence | `auth/GO_RECORDED_STOP1_COWNER.json` (match EXACT; A7 prelaunch AUTHORIZED_FOR_STOP1 = key 1; owner GO = key 2) |
| Runner authorization artifact | `audits_a7/go_authorization.json` (schema `eosv2.go_authorization@1`, written at execution per V1 precedent; the frozen runner refuses scored mode without it) |
| Worktree / branch | `.worktrees/ethusdt-open-search-v2/integration`, `orca/ethusdt-open-search-v2-integration` |
| HEAD at dispatch | expected `f672e01e`; measured `d613786b` = `f672e01e` + ONE additive file (the GO auth record itself, 28 lines; diff verified, engine/freeze/data byte-identical to the A7-audited state). The audited code state is the state being run — disclosed, not silent. |
| Corpus | staged V2 corpus 2020-01..2026-08, 7 series, 551 zip files (census BUILD_PASS; V1 cross-check 80/80×3) |
| Budget cap | 8 scored cells (see §8 accounting) |

## 2. Attempt-1 TECHABORT (pre-publication) and remediation r1 — full disclosure

Attempt 1 (2026-09-30T21:23:21Z) crashed inside the frozen runner BEFORE
any publication: `KeyError: 'all_pass'` at `run_scored.py:201` — the
scored-mode aggregation iterates `E.ARMS`, and the four lane-A cells are
`{"status": "NOT_RUN_THIN"}` dicts with no gate fields. The bug was
structurally unexposed pre-GO: the P3 dry-run never executes `scored()`,
and the A7 prelaunch audit exercised the refusal path (exit 2), never the
authorized path. `scored/scored_summary.json` was NOT written and the
stdout artifact was empty — **zero scored-PnL outcome exposure**. Heavy
lock released FAILED with the stderr tail preserved (history row pid
21026).

Remediation r1 (V1 precedent: its SCORED_ATTEMPT_1/2 events record the
identical arc in the same scripts family): `run_scored.py` line 201 only,
`g["all_pass"]` → `g.get("all_pass")`. NOT_RUN_THIN cells can never be
all-pass (never computed), so eligibility and verdict semantics are
unchanged; no PnL math, gates, folds, arms, or verdict enum touched.
Freeze red line ("any change after scored PnL is visible = new
experiment") not crossed — no scored artifact existed. The freeze's
`code_freeze` digest for `run_scored.py` was superseded with an additive
`freeze_remediations.r1` record in `freezes/eosv2_freeze.json`
(974111c5… → 28f0ff88…; `eosv2_engine.py` digest unchanged). Governance
note: V1 additionally obtained a fresh A7 delta AUTHORIZED_FOR_SCORED_RERUN
before re-running; no A7 lane was dispatched at this gate, so the re-run
proceeded under the consumed STOP-1 GO with this record — flagged for P5
A7 terminal (G9) adjudication.

## 3. Lane A — never computed (pre-PnL feasibility kill)

EOSV2-A1..A4 are `NOT_RUN_THIN` per the frozen per-arm per-fold population
floor (F1 decisions 28/0/0/0 < 100; rvol warmup 395d from the 2020-01 data
floor exceeds F1 end). Zero denominator; never computed, never scored
(freeze `lane_a_disposition`).

## 4. Scored cells (lane B) — engine-published values

Engine "net" is fully cost-inclusive by the frozen cost law (taker
5 bps/side + 1 adverse tick/side per tier + measured funding). The tier
ladder 1.0×/1.5×/2.0× IS the measured cost sensitivity; Δ(1.0×→2.0×) is
the extra cost of doubling fee+tick. `cost/rt bps` is the G7
execution-cost (2 adverse ticks per round trip, ES1 semantics — slippage
only; fees already inside net).

| cell | law | net @1.0× | net @1.5× | net @2.0× | Δcost 1.0→2.0× | fills@1.5× | cost/rt bps@1.5× | G11 spearman vs TREND_LF |
|---|---|---|---|---|---|---|---|---|
| EOSV2-B1 | breadth{SOL,BNB,XRP,ADA}>SMA200 ≥3/4 | 288,423.80 | 275,195.63 | 261,967.46 | 26,456.34 | 516 | 0.1330 | 0.628185 |
| EOSV2-B2 | ≥2/4 | 403,801.90 | 392,230.95 | 380,660.01 | 23,141.89 | 450 | 0.1386 | 0.665877 |
| EOSV2-B3 | ==4/4 | 139,444.50 | 129,803.23 | 120,161.96 | 19,282.54 | 380 | 0.1197 | 0.453501 |
| EOSV2-B4 | breadth(SMA600) ≥3/4 | 228,882.71 | 222,793.94 | 216,705.16 | 12,177.55 | 236 | 0.1343 | 0.455075 |

Fold nets @1.0× (cost-inclusive), verbatim:

| cell | F1 (2020-01..21-05) | F2 (21-05..23-01) | F3 (23-01..25-01) | F4 (25-01..26-09) | max pos-fold share (G5) |
|---|---|---|---|---|---|
| B1 | 176,290.70 | 10,594.17 | 50,529.24 | 51,009.69 | 0.6112 |
| B2 | 249,741.54 | −27,143.87 | 76,740.48 | 104,463.74 | 0.5795 |
| B3 | −2,363.18 | 60,864.86 | 25,903.59 | 55,039.22 | 0.4292 |
| B4 | 183,074.41 | −55,391.93 | 43,859.68 | 57,340.55 | 0.6440 |

## 5. References and V1-reproduction check

Plan §4: "recomputed on this cycle's restaged corpus (expected to
reproduce V1's numbers byte-close; material divergence = STOP +
investigate before PnL)". Result: **all four references reproduce V1's
terminal numbers (V1 commit 8196e3ea, `eos1.scored_run@1`) EXACTLY, to
the cent, on every tier and every fold.**

| reference | net @1.0× | net @1.5× | net @2.0× | V1 @1.0× | reproduction |
|---|---|---|---|---|---|
| BASE_CASH | 0.00 | 0.00 | 0.00 | 0.00 | EXACT |
| BASE_ALWAYS_ON_LONG | 1,653,470.33 | 1,652,725.15 | 1,651,979.97 | 1,653,470.33 | EXACT (all folds identical: 1,627,403.92 / −72,559.42 / 130,354.40 / −31,728.56) |
| BASE_TREND_LF | 472,864.82 | 463,602.29 | 454,339.76 | 472,864.82 | EXACT (folds identical: 296,861.29 / 40,179.87 / 58,005.25 / 77,818.42) |
| REF_SHORT_ALWAYS | −1,656,451.03 | −1,657,196.21 | −1,657,941.38 | −1,656,451.03 | EXACT (folds identical) |

## 6. Controls (G6; part of each cell's evaluation per the frozen law)

| cell | block-shuffle(30-bar) net @1.0× | sign-inverted net @1.0× | cell net @1.0× | G6 |
|---|---|---|---|---|
| B1 | 106,573.76 | −341,336.46 | 288,423.80 | PASS (neither out-earns) |
| B2 | 310,630.58 | −450,085.67 | 403,801.90 | PASS |
| B3 | 42,140.88 | −178,009.58 | 139,444.50 | PASS |
| B4 | 178,600.27 | −253,237.82 | 228,882.71 | PASS |

## 7. Gate-by-gate (as computed by the frozen runner; collected, not reinterpreted)

| gate | B1 | B2 | B3 | B4 |
|---|---|---|---|---|
| G1 net>0 @1.0× | PASS | PASS | PASS | PASS |
| G2 net>0 @1.5× | PASS | PASS | PASS | PASS |
| G3 beats ALL references @1.0× | FAIL | FAIL | FAIL | FAIL |
| G4 ≥3/4 folds>0 OR best-fold-removed>0 | PASS | PASS | PASS | PASS |
| G5 max pos-fold share ≤0.50 | FAIL (0.6112) | FAIL (0.5795) | PASS (0.4292) | FAIL (0.6440) |
| G6 controls must not out-earn @1.0× | PASS | PASS | PASS | PASS |
| G7 fills@1.5× ≤10k AND cost/rt ≤10 bps | PASS | PASS | PASS | PASS |
| G8 repro byte-match (detached twin) | P5 (frozen sequencing; determinism double re-run below supports readiness) | ← | ← | ← |
| G9 A7 terminal clean | P5 (frozen sequencing; note §2 governance flag) | ← | ← | ← |
| G10 vs BASE_TREND_LF: net up AND no pos→neg fold flips | FAIL | FAIL (F2 flip) | FAIL (F1 flip) | FAIL (F2 flip) |
| G11 ancestry disclosure | 0.628 | 0.666 | 0.454 | 0.455 |
| **all_pass** | **FALSE** | **FALSE** | **FALSE** | **FALSE** |

G3 margins @1.0× (cell − reference), verbatim from the runner:

| cell | vs BASE_ALWAYS_ON_LONG | vs BASE_TREND_LF | vs REF_SHORT_ALWAYS |
|---|---|---|---|
| B1 | −1,365,046.53 | −184,441.02 | +1,944,874.83 |
| B2 | −1,249,668.43 | −69,062.92 | +2,060,252.93 |
| B3 | −1,514,025.82 | −333,420.31 | +1,795,895.53 |
| B4 | −1,424,587.61 | −243,982.10 | +1,885,333.74 |

**The structural wall stands**: the best breadth cell (B2, 403,801.90) is
1.25M below ALWAYS_ON_LONG's 1,653,470.33 and 69K below TREND_LF's
472,864.82. Every cell also loses G10 (no incremental value over the
trend reference; B2/B3/B4 additionally flip a TREND_LF-positive fold to
negative).

## 8. Determinism, budget, and lock record

Determinism (mission step 6): after the battery, cell EOSV2-B1 was
recomputed in TWO fresh processes (ROOT `.venv` python, frozen engine);
canonical JSON dumps (folds ×3 tiers + fills_total + net_total +
avg_raw_fill_px) are **byte-identical**
(sha256 `0287ea23…` == `0287ea23…`), and the rounded nets/fold-nets
cross-check against `scored/scored_summary.json` exactly
(`scored/determinism_b1.json`, pass=true).

Budget (observed == published): the frozen runner's own denominator is
`{scored_cells: 4, computations: 4×3=12, controls: 4×2×3=24, references:
4×3=12}` (48 books total, matching the P3 dry-run). Against the 8-cell
cap the dispatch accounting counts 4 arms + 4 references = **8/8 cells
consumed**; plan §4 counts references as "NOT cells" (which would read
4/8). Both countings disclosed; the conservative 8/8 is recorded in
state.json so no later lane infers spare budget.

Heavy lock (machine-wide, `research/governance/heavy_lock.py`):
attempt 1 TAKEN 2026-09-30T21:23:21Z → RELEASED FAILED 21:23:36Z
(TECHABORT, stderr tail in release note); attempt 2 TAKEN
21:25:31Z → RELEASED FINISHED 21:26:06Z (pid 21182; battery +
determinism; history rows under role `stop1-scored-execution`). Lock held
end-to-end across all compute; verified FREE_PROVEN before each take.

## 9. Verdict and preregistered next steps (quoted)

The runner's verdict line, verbatim:
`"verdict": "ETHUSDT_OPEN_SEARCH_V2_NO_INCREMENTAL_VALUE"`,
`"all_pass": []`.

Charter (freezes/STOP1_charter.md): "A NO is a valid terminal and ends
the posthoc open space on keyless data (campaign then parks at the
owner-redirection decision per plan §8)."

Plan §8 (campaign law), verbatim: "Candidate ⇒ owner decides prospective
sleeve (preregistered promote/kill/time-stop + short-beta control +
pre-fill cost-identity reconcile). NO candidate ⇒ standing directive
authorizes tranche V3 ONLY with new lawful tuples; if A7 vetoes both
lanes here, the posthoc open space on keyless data is EXHAUSTED and the
campaign parks at an owner-redirection decision (asset change / new data
authority / wall-redesign successor — each an owner decision per §34.5,
not agent-derivable)."

Branch determination is NOT this lane's call: the A7 prelaunch did NOT
veto lane B (adjudicated genuinely novel, NO_VETO), so the operative
continuation for a gates-NO is the first clause (tranche V3 with new
lawful tuples) — but the P5 A7 terminal (G9, which also adjudicates the
§2 remediation flag) is the remaining frozen phase before the P6 two-half
close settles the campaign's final branch. Frozen sequencing (state.json
`phase_next`): "P4 scored execution on typed GO -> P5 repro twin + A7
terminal -> P6 two-half close".

## 10. Artifacts

- `scored/scored_summary.json` — frozen runner's scored artifact (verbatim)
- `scored/run_scored_stdout.json` — frozen runner's verdict print (verbatim)
- `scored/determinism_b1.json` — determinism assertion record
- `audits_a7/go_authorization.json` — runner-required authorization artifact
- `scripts/stop1_execute.py` — execution harness (lock + battery + determinism; NOT frozen engine code)
- `freezes/eosv2_freeze.json` — code_freeze supersession + `freeze_remediations.r1` (additive)
- `scripts/run_scored.py` — remediation r1 (one line, disclosed §2)
- `state.json`, `events.jsonl` — ledger updates
- heavy-lock history: `~/.my-quantitative-governance/heavy_runtime/heavy_worker.history.jsonl` (2 rows, role `stop1-scored-execution`)
