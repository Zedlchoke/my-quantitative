# CRYPTO-V13 Terminal Audit — A7

- **Auditor:** A7 (terminal, independent — audit artifacts only, no repair; everything recomputed)
- **Worktree:** `.worktrees/crypto/v13/r-a7-terminal` @ `bca7d7c` (branch `orca/v13-r-a7-terminal`)
- **Exec tree (read-only):** `.worktrees/crypto/v13/e-exec-1/results/v13_phase_e/` · **Repro tree:** `.worktrees/crypto/v13/r-reproduce/`
- **VERDICT: `V13_TERMINAL_APPROVED_0_FAIL`** — 7/7 items PASS, zero unresolved HIGH/CRITICAL.

## Terminal outcome statement (confirmed by independent recomputation)

**V13_REJECT_ALL.** Multiple-testing statement: **observed denominator 140** (134 historical + 6 V13), **published 137** (131 historical + 6 V13) logical cells; **no S1 candidate locked** — zero V13 Stage-A survivors.

## Per-item results

### 1. Ledger once-only accounting — PASS
- Both shard ledgers read from the exec tree: 3 rows each, 6 rows total, all `row_type=CELL_RESULT`; trial keys unique 6/6.
- Every row's `producer_head_sha` matches its family: oitd `bcb28536…`, liqepis `d0726645…`.
- Zero observation-only rows for scored cells (W1R refusals lived in temporary ledgers; the attempt-1 LIQEPIS crash emitted zero ledger rows).
- Digests: ledger `result_sha256` == `cell_summary.baseline_result_sha256` == `artifact.hashes.result_sha256` 6/6, **and A7 independently recomputed each digest** as `sha256(canonical_repr(artifact minus hashes/artifacts))` (floats-as-repr, `research/adapter_v10/runner.py:225`) — **6/6 exact match**.

### 2. Artifact-byte hashes — PASS
- `ledger_oitd.jsonl` = `4fa9f351…` and `ledger_liqepis.jsonl` = `1989a9c1…` — both match the expected values byte-for-byte.
- All 6 `repro_report.json` in the repro tree: `all_match=true`, `verdict=ALL_MATCH`; every compared field (15 fields incl. `baseline_result_sha256`, matrix digest, scored metrics, universe) has execution == reproduction. **Zero mismatched fields.**
- Canonical registry `experiments_v13.jsonl` in BOTH twins (e-exec-1 and r-reproduce) is 0 bytes = the empty seed `e3b0c442…`. Registry never written; shard-ledger authority design held.

### 3. Cost/funding reconciliation — PASS with adjudicated anomaly (the adjudication)

**The anomaly.** LIQEPIS `cost_charged_sum` 25.0252 (28D, SIGN-INV) / 15.8386 (56D) over 600 positions; price-only PnL −0.3065/−0.2053/+0.3065; funding 0.0.

**Defect class (precise).** *Driver-level cost-model parameterization defect* — not a double-charge and not a per-fill schedule violation. The driver's LIQEPIS lane hardcodes uniform default tick sizes `{sym: 0.01}` (`run_v13_cell.py`, `tick_sizes={sym: 0.01 for sym in needed}`) instead of loading symbol-specific exchange tick sizes from perp metadata as the OITD lane does (`load_tick_sizes`; OITD artifact shows PEPE 1e-7, ACE 1e-5). Under the frozen formula `rate = 5bps·mult + ticks·tick_size/price` (`adapter_v10/base.py::rebalance_cost_between`), the slip term becomes `0.01/p` = **0.87–4.26 per unit traded** on the sub-cent cohort (observed 1000PEPEUSDT entries 0.00235–0.01153) versus ~1e-5…1e-2 at true tick sizes.

**Cost path reconstruction (from the cell evidence).** The scored cost is **per-stamp, not per-fill**: `cost_charged = rebalance_cost_between(prior, target)` is charged once per weekly decision stamp on |Δw| turnover (`runner.py:610`), and `cost_charged_sum = Σ` over 52 daily rows. LIQEPIS-28D: 49/52 stamps cost-bearing, Σ gross_realised 50.0, cost/turnover = **0.5005 per unit** (= 0.0005 fee + 0.01/p; implies mean fill price ≈ 0.02 — matches the cohort). The 600 positions carry the pro-rata allocation (Σ 23.7627); the 1.2624 residual is the generic stamp-vs-position allocation residual present identically in OITD (~0.00066, ~10% of its cost) — pre-existing, not LIQEPIS-specific. Identities verified: per-position net = price − cost − funding (exact); stamp vs position price sums reconcile to 0.0 in all 6 cells. Counterfactual at corrected tick sizes: cost ≈ 0.028 (~900× lower) — confirming A1's "3–4 orders above the frozen per-fill schedule".

**Verdict impact: NONE — invariant.** Anchor LIQEPIS-28D is negative on price alone (−0.3065/52d ⇒ expectancy ≈ −0.0059/day < 0 even at ZERO cost); 56D likewise; PF 0.0475/0.1037 ≪ 1.10. Rejected under inflated, corrected, or zero costs. SIGN-INV (price-only +0.3065) cannot rescue: the falsification shadow requires the anchor to pass. OITD untouched by the defect (per-unit cost ≈ 0.00051 with real tick sizes; totals 0.00665/0.00496/0.00222 — consistent with the stated ~0.005–0.007 band and the frozen hysteresis schedule).

**Funding scope note: CONFIRMED.** funding = 0.0 on all LIQEPIS arms because the frozen bars-only producer reads no funding settlements; omission understates costs ⇒ rejection *a fortiori*.

**Disclosure & no-retrofit: CONFIRMED.** `anomaly_for_terminal_a7` in `family_verdicts_v13.json` + event_log seq 20, committed in `5c72040` before this audit. `git diff d0726645..HEAD -- research/v13/families/liqepis/plugin.py` is **empty**; driver diff likewise empty; exec/repro trees detached clean at `d0726645`; 6/6 repro at the frozen head.

### 4. Family verdicts — PASS
Recomputed from the frozen `stage_a_gates` (run_contract) against exec artifacts:
- **OITD anchor:** expectancy −0.005488 FAIL; PF 0.8785 FAIL; folds 1/3 positive FAIL; MDD 30.54% FAIL ⇒ REJECT. Control worse than anchor (−0.4501 vs −0.2854) ⇒ no falsification shadow; semantics honored.
- **LIQEPIS anchor:** expectancy −0.4871 FAIL; PF 0.0475 FAIL; folds 0/3 FAIL; MDD 2533% FAIL ⇒ REJECT catastrophic. SIGN-INV negative ⇒ mirror not fired.
- A1's verdict records match my recomputation number-for-number; no gate relaxed (all 6 ledger arm digests equal the pre-delta `w13_freeze.json` values).

### 5. Denominator math — PASS
131 published / 134 observed historical + 6/6 V13 = **137 published / 140 observed**. Budget 6/9 consistent everywhere; ILLIQ's 3 slots unused-never-reassigned (selection freeze note). Zero survivors ⇒ V13_REJECT_ALL; no S1 candidate locked; `s1_seal = SEALED_UNTOUCHED`.

### 6. S1 / deployment / workers / trees — PASS
`owned_workers=0`, `deployment_activity=none`. Forbidden-string scan of the control plane hits only the contract's own prohibition text. Exec + repro trees clean (detached `d0726645`); integration clean at `bca7d7c`; main (`50e0207`) has **no V13 ancestry** — all 18 `orca/v13-*` branches share the pre-V13 merge-base `b8876ef`. No push, no merge.

### 7. Process — PASS
TECHABORT forensics prove attempt-1 consumed zero budget (pre-metric ContractViolation crash; no BASELINE; liqepis ledger absent; oitd ledger sha byte-verified unchanged). Delta chronology from git DAG: driver-only `0253754` (adds files only), traversal `bcb2853` → A7 delta-1 `7bdd8eb` 16:44:03Z **before** OITD scoring 16:47:10Z; boundary `f2aef59` → A7 delta-2 `9b08750` 18:02:37Z **before** LIQEPIS scoring 18:04:03Z; all 6 arm digests unchanged vs the pre-delta freeze. Owner GO recorded verbatim with the exact-string deviation disclosed. Hand-stamp correction (`bca7d7c`) acknowledged — git DAG order used as authoritative.

## Findings
| ID | Severity | Status | Summary |
|----|----------|--------|---------|
| T1 | MEDIUM | RESOLVED_BY_ADJUDICATION | LIQEPIS uniform tick-size 0.01 defect (above). Verdict-invariant; any future LIQEPIS re-run must load real tick sizes from perp metadata. |
| T2 | LOW | OPEN_OBSERVATION (no verdict impact) | Generic stamp-vs-position cost allocation residual in both families; scored metric uses the conservative stamp-level sum; price PnL reconciles exactly. |
| T3 | INFO | NOTED | heartbeat/state pin integration `1e11cd9` (18:17:51Z) vs current `bca7d7c` (18:18:08Z stamp-fix commit) — expected append-only behavior. |

## Verdict

**`V13_TERMINAL_APPROVED_0_FAIL`** — terminal outcome **V13_REJECT_ALL** confirmed: observed denominator 140 (134+6), published 137 (131+6), no S1 candidate locked.
