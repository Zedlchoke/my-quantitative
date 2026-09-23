# A7 TERMINAL Audit — JEV-REGIME-ROUTER-V2

**Verdict: TERMINAL_VERDICT_AUTHORIZED_JEV_NO_INCREMENTAL_VALUE**
(zero unresolved HIGH/CRITICAL; auditor AGREES with the proposed `JEV_NO_INCREMENTAL_VALUE`)
**Audited HEAD:** `bfbb6e7802ea9b9d3a8e185a0f449df5fedc0eb0` on `orca/jev-regime-router-v2-integration`, clean tree (measured by the auditor)
**Machine-readable authority:** `audits/a7_terminal_audit.json` (schema `jrv2_a7_terminal_audit@1`)
**Auditor:** A7 independent fresh-context terminal (plan §9 E/R/T). Audit + write only; nothing repaired. Zero live API calls; zero new outcome computations beyond reading existing artifacts and the mandated byte-compares.

## 1. GO chain (verified end-to-end)

- `sha256("GO JEV REGIME V2 SCORED BACKTEST")` recomputed by the auditor = `a7794ac8…8ed2` — **matches** the `SCORED_GO.json` pin exactly (no trailing newline).
- `cmd_backtest` gating re-read in code AND behaviorally re-tested: without a token it prints `REFUSED_BACKTEST_QUARANTINE` and exits 20; per-cell/per-arm invocation is refused before any compute; `test_backtest_quarantine_is_fail_closed_against_forced_authority` is in the 127-green suite.
- Ordering (root-checkout registry is the ledger; `28ccbee9` lives on main, not on the lane): STOP-2 registry events `2026-09-22T16:08:31Z` ("awaiting owner exact GO phrase") → owner GO (2026-09-23 message, attested in the authority file) → code freeze `13ecc2e6` 00:06:04Z + pre-run fixes, last `b1b1494a` **00:25:39Z** → run start **00:25:40Z** (`started_at_utc`; heavy-lock FINISHED lease 00:25:39→00:26:54Z) → results commit `bfbb6e78` 00:38:09Z touching ONLY `evidence/` + `tools/scored_worker.py` (launcher, no computation). **Zero code/freeze commits after the run started.** A failed attempt (lock TECHABORT 00:17:08→00:17:22Z) left partials deleted unread per `b1b1494a`.
- Freeze integrity today: all 10 freeze files sha-match `freeze_manifest.json`; `verify-freezes` ok.

## 2. Independent recompute from raw tier files (54 files)

Recomputed from `runtime/scored/{cell}/{arm}/{tier}.json` trade ledgers, not from any summary:

- Totals (gross/fee/slip/funding/net = Σ trades), trade counts, and profit factor (Σwins/|Σlosses| on per-trade net) match stored values in **54/54** files. Zero problems.
- Engine identity recomputed (`100,000 + net == equity[-1]` and `net == gross − costs`) holds in every file; stored `engine_identity[0]` and `fold_reconciliation[0]` are TRUE in **all 54**; recomputed `|Σ fold_net − net| < 1e-9` everywhere.
- `scored_summary.json` base-tier block (net/trades/PF/folds/flags for all 18 cell-arms) matches the tier files **exactly**; `evidence/scored/scored_summary.json` is byte-identical to the runtime copy.
- **JEV_ONLY fold nets, base tier:** BTC_H1 `[-40997, -37419, -4923, -4802]`; BTC_H4 `[-44582, -27241, -6522, -6930]`; SPY_D1 `[-25488, +4985, -14810, -16310]` → **negative 11/12**, sole positive SPY fold 2 (+4,985), exactly as reported (at tier 1.5x it is negative too).

## 3. Reproduction — ALL_MATCH verified by the auditor

Byte-compared `runtime/scored` vs `runtime/scored_repro` myself: **54/54 tier files byte-identical**; the two summaries differ **only** in `started_at_utc`/`finished_at_utc` (00:25:40/00:26:54 vs 00:35:27/00:36:42; repro lease FINISHED 00:35:27→00:36:42Z, also post-freeze). The ALL_MATCH claim holds with no qualification.

## 4. Verdict test vs the frozen evaluation_contract

`JEV_INCREMENTAL_VALUE_SUPPORTED` preconditions (base tier, all recomputed):

| Precondition | Result |
|---|---|
| Net-positive after costs | **FAILS everywhere** — JEV_ONLY −88,140 / −85,274 / −51,623; every non-always-on arm negative on every cell |
| Beats always-on arms | **FAILS** — loses to ALWAYS_ON_MR on all 3 cells (−35,008 / −31,373 / −50,700). NB: JEV marginally beats ALWAYS_ON_TREND on BTC (+3,395 / +4,225) — see F1 |
| Beats deterministic router | FAILS on SPY (−19,747); marginal on BTC (+8,514 / +2,871) among deeply-negative arms |
| Beats random matched | FAILS on all 3 (−13,863 / −1,317 / −21,608); `null_invalid=True` on **all 9** cell×tier combos — honestly disclosed |
| Confirmation-arm non-inferiority | Insufficient — CONFIRM deeply negative everywhere; agreement share 0.399 / 0.620 / 0.561 |
| Reproduction ALL_MATCH | PASS |
| A7 terminal clean | PASS (this audit) |

**Refutation attempt: FAILED.** No cell/arm comparison qualifies JEV. The random-null weakness does not matter to the verdict: net-negative-everywhere plus losing to ALWAYS_ON_MR everywhere already preclude the supported verdict without the random arm. `JEV_INCONSISTENT_ACROSS_FOLDS_OR_ASSETS` would be the wrong label — the negative result is *consistent* (11/12 base, 12/12 at 1.5x, all 3 assets). **The strongest allowed verdict is `JEV_NO_INCREMENTAL_VALUE`; the auditor agrees.**

## 5. Budget, trial accounting, non-promotion

- Bulk manifests sum exactly **58,360,983 in / 1,744,755 out** (auditor recomputed; matches A7-2's byte-equal claim). Formula cap `4,369 × 13,315 = 58,173,235` verified. **Used-only 58,050,872 = −0.21% vs cap — no breach** (raw all-cache +0.32% was the disclosed conservative-overstated convention at bulk time).
- Trial accounting **18/18 observed** of 18 planned; buy-hold is reference-only (structurally outside ARMS; dedicated test in the green suite).
- SPY ALWAYS_ON_TREND **+19,813** (recomputed; 143 trades, PF 1.14, **concentration 0.6876 > 0.50 kill**) is reported as a BASELINE, explicitly **not promoted**; the cycle has no promotion authority and the vocabulary has no promotion token. No report makes a profitability claim beyond evidence.

## 6. Hygiene

- `pytest tests_py`: **127 passed** (auditor run). `verify-freezes`: ok, 10/10, security scan 0 findings, V1-isolation scan 0 findings. Census equals freeze (35,039 rows; H1 8,759 / H4 2,189 / SPY 2,943; 0 interior gaps). Heavy lock `FREE_PROVEN` at audit time. Credential-pattern grep over the cycle dir: zero hits. S1-path denial + V1-isolation guards live and tested.
- Report traceability: **every** number in all three base-tier tables, all margins, tier degradation (−88,140 → −93,415 → −96,345), SPY JEV folds, occupancy/switches (90/31/34), effUNKNOWN (0.427/0.272/0.291), agreement shares, skipped-trade fractions, buy-hold refs, and the classification report's corpus/usage reproduced from artifacts — far beyond the 10 mandated spot-checks. **Numbers not reproduced: none.**
- Honest disclosures confirmed: random null invalid on all cells; provider nondeterminism (evidence-backed at A7-1); canary 9/10 honest FAIL; SPY ran complete 2,751/2,751 (1 error fail-closed) — blockers did **not** block SPY.

## 7. Findings (0 HIGH / 0 CRITICAL / 3 LOW / 4 INFO)

| # | Sev | Finding |
|---|---|---|
| F1 | LOW | Verdict-basis gloss "loses to always-on … everywhere" is imprecise: JEV beats ALWAYS_ON_TREND on BTC_H1/H4 (+3,395/+4,225) and DETERMINISTIC on BTC. Formal precondition unaffected (must beat BOTH always-on arms; ALWAYS_ON_MR wins everywhere; all comparisons among deeply-negative arms). Report Q1/Q2 wordings are precise. |
| F2 | LOW | `margin_to_fail` is contract-listed and implemented (metrics.py:200) but never computed/persisted in scored artifacts (raw-delta margins only). Cannot flip any precondition (all decided by ≥1,317 net against JEV). |
| F3 | LOW | Backtest report Q7 says "12 bps/side BTC"; frozen law is 5 fee + 1 slip = **6 bps/side** (12 round-trip) — verified from trade ledgers. Prose slip; computations correct. SPY "10 bps/fill" correct. |
| F4 | INFO | A7-2 F5 arithmetic nit: 58,360,983 − 310,109 = 58,050,874 vs recorded 58,050,872 (2 tokens; immaterial vs the verified cap). |
| F5 | INFO | `runtime/` is gitignored by design; tracked terminal evidence = byte-identical evidence summary + reports. Byte-compare performed on the working tree and holds. |
| F6 | INFO | `tools/scored_worker.py` (pure lock/subprocess launcher, no computation) landed with the results commit; computation code was frozen pre-run. |
| F7 | INFO | Cosmetic garbled words in the report's Vietnamese five-year-old summary ("巨星", "tribal"); qualitative content unaffected. |

## 8. Authorization

The strongest-allowed terminal verdict from the frozen vocabulary is **`JEV_NO_INCREMENTAL_VALUE`**. All GO-chain, recompute, reproduction, budget, accounting, hygiene and honesty checks pass; zero unresolved HIGH/CRITICAL. This audit authorizes the terminal verdict and expresses no opinion beyond the evidence.
