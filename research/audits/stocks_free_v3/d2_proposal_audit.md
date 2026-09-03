# STOCKS-FREE-V3 D2 — A7 independent proposal audit

- schema: `stocks_free_v3/d2_proposal_audit@1` (machine-readable twin: `d2_proposal_audit.json`)
- auditor: A7 (independent; objections only, no repairs)
- audited pool SHA: `9a9f5fd5b78e124ff7fd73dcf56557f2ea2b101c` (verified == HEAD of `orca/stocks-free-v3-d2-a7-audit`; tree clean)
- measured_utc: `2026-09-03T13:34:32Z`
- restrictions honored: no network, no market-data reads, no S1, no scoring, no V2 PnL (V2 consumed at mechanism level only via `research/control/stocks_free_v3_run/forbidden_family_inventory.json`; `research/control/stocks_free_v2_run/` existence confirmed only). Exactly two files written.

## 1. Procedural verification (checklist item 1)

| commit | lane | parent | files |
|---|---|---|---|
| `6022c10` | A4 | `d388f8c` | 2 added, `a4_family_*` only |
| `363169c` | A5 | `d388f8c` | 2 added, `a5_family_*` only |
| `b1acf1c` | A6 | `d388f8c` | 2 added, `a6_family_*` only |

All three lanes added exactly two proposal documents, scoped to their own prefixes, all parented at the P1-freeze commit `d388f8c` (parent `e97153a` = P1_SHA). **No outcome, results, audit or control files appear in any diff.** A5's documented sha256 of the blind packet was independently recomputed and matches (`034cf4d6…8106`). Outcome-blind access: **plausible. PASS.**

Code-claim verifications (signatures only, no data): `VolScalingRule` validation admits the A5 constant-scale rule (min==max) and the A6 clip bands; `build_risk_matched_spy` scales SPY TR ex ante (strictly-before-d) with any frozen rule; `compute_fold_alpha` defaults `require_beta_isolation=True`; `value_book` marks fills at **raw_close on fill_date** (canonical fill event = session close — load-bearing for one objection below); `etf_leg_turnover/fill_cost/normalize_entry_targets/select_drop_one_symbol/fold_concentration` and `BarLoader` (checksummed, `GapError` fail-closed) all exist as cited.

## 2. Pool verdict

**POOL_VALID_WITH_OBJECTIONS** — six eligible candidates, zero HIGH/CRITICAL objections, objections itemized below. Binding selection constraint found: the three idio-shock-reversal proposals form **one mechanism cluster; at most one is selectable**.

## 3. Per-proposal results

| # | family | verdict | novelty | ctrl info | events | impl risk | sources | rank |
|---|---|---|---|---|---|---|---|---|
| 1 | SFV3-A5-IDIO-SHOCK-REVERSAL | ELIGIBLE_WITH_OBJECTIONS | no veto (cluster) | HIGH | adequate (~12/fold, fold-1 conc.) | MEDIUM | STRONG | **1** |
| 2 | SFV3-A4-IDIO-SHOCK-REVERSAL | ELIGIBLE_WITH_OBJECTIONS | no veto (cluster) | HIGH | adequate (~15/fold, thin) | LOW | STRONG | **2** |
| 3 | SFV3-A6-TOM-SETTLE | ELIGIBLE_WITH_OBJECTIONS | no veto | HIGH | strong (~24 windows/fold) | LOW | STRONG | **3** |
| 4 | SFV3-A4-QEND-FLOW-REBAL | ELIGIBLE_WITH_OBJECTIONS | no veto | HIGH | adequate (~10 decisions/fold) | LOW | STRONG | **4** |
| 5 | SFV3-A5-MKT-SHOCK-DIFFUSION | ELIGIBLE_WITH_OBJECTIONS | no veto (distinct class) | HIGH | adequate w/ risk (fold-2 sparse) | MEDIUM | STRONG | **5** |
| 6 | SFV3-A6-IDIO-SHOCK-REV | ELIGIBLE_WITH_OBJECTIONS | no veto (cluster) | HIGH | insufficient-risk (~2–6/yr) | MEDIUM | MEDIUM | **6** |

Top objections (full list with LOWs in the JSON):

- **SFV3-A5-IDIO-SHOCK-REVERSAL** — MEDIUM: open-of-next-session execution is not representable by the canonical close-fill `value_book` contract; the pure-reuse claim conflicts with the proposed clock and must be resolved at selection freeze. MEDIUM: fold-1 event concentration vs drop-one-fold / positive-fold-share gates (predeclared).
- **SFV3-A4-IDIO-SHOCK-REVERSAL** — MEDIUM: stress survival demands ~+70 bps per-event 3-session market-adjusted reversal — the optimistic top of documented ranges for an arbitrageable sector ETF. LOWs: "Jegadeesh, S." citation initial; fixed −2% threshold regime-fragility; late-entry control can be killed by a mechanism-consistent weekly-horizon reversal (over-strict, conservative direction).
- **SFV3-A6-TOM-SETTLE** — MEDIUM: benchmark gross-path mismatch — the vol-targeted benchmark (clip [0.30,0.50]) does not replicate the arm's calendar step path despite the doc's claim; identification of the TOM premium rests on the anchor-vs-mid-month-placebo contrast (which the gates require, so falsification power is preserved). LOW: Lakonishok-Smidt title misstated ("Fifty-" vs actual "Ninety-Year Perspective").
- **SFV3-A4-QEND-FLOW-REBAL** — MEDIUM: required effect (~60 bps relative per tilt sector, ~2.5x for stress) at/above documented turn-of-period magnitudes. MEDIUM: the V2 mechanism-level lesson (rank direction in this cohort failed to separate anchor from reversed-rank control) gives any cross-sectional quarterly tilt a low prior; the family's own winner-tilt control tests exactly this, honestly.
- **SFV3-A5-MKT-SHOCK-DIFFUSION** — MEDIUM: same open-fill clock conflict as its companion. MEDIUM: fold-2 (2020-09..2023-02) trigger scarcity for +2σ SPY days; sparse/unpopulated fold likely and predeclared as insufficiency, not rescue.
- **SFV3-A6-IDIO-SHOCK-REV** — MEDIUM: benchmark gross-path mischaracterization ("replicates the arm's path", "beta-only arm earns ~0" are both incorrect as written; the mirror-control contrast remains clean). MEDIUM: no structural turnover governor (≤7 events/yr needed; threshold depth is the only constraint; fail-closed death on breach). MEDIUM: event sparsity — deep 5-day idio threshold + non-systemic filter risks ~2–6 events/yr and a possible zero-entry fold (predeclared death); borderline HIGH on pass-probability grounds, held MEDIUM because it is predeclared and fail-closed.

## 4. In-pool duplication adjudication

The three idio-shock-reversal proposals (A4-IDIO, A5-IDIO, A6-IDIO) all trade **one economic hypothesis**: post-idiosyncratic-shock liquidity-provision reversion — the packet's single priority search space. They are **not literal pseudo-replicates** (event definitions and horizon economics differ: raw −2% daily / z≤−3σ daily / −5% 5-day cumulative; 3/5/20-session holds; three book architectures), but selecting two would spend 2 of the 2-family budget on one hypothesis — functional pseudo-replication. **At most one member of this cluster is selectable.**

**Strongest of the three: SFV3-A5-IDIO-SHOCK-REVERSAL.** Reasons: (i) the sigma-standardized trigger is scale-free and cross-regime comparable, where A4's fixed −2% and A6's fixed −5% thresholds are regime-fragile; (ii) its sign-inverted control is the sharpest mechanism test in the pool — transitory-overshoot reversion implies sign symmetry, while drift/attention alternatives pay both sides the same, so reproducing the anchor kills it; (iii) the constant-scale risk-matched benchmark cleanly separates beta per unit of average exposure; (iv) turnover is structurally guaranteed by the 5/252 budget rather than hoped for from threshold depth (A6's specific weakness). Its cost is the open-fill plumbing objection — a bounded implementation fix, not a design defect. A4-IDIO ranks second: best implementation safety and the airtightest beta-cancellation construction, but the weakest event-definition robustness and the pool's most demanding effect-size condition; A1 weighting rubric item 6 above trigger robustness could reasonably swap ranks 1–2. A6-IDIO ranks third: most careful trigger isolation in principle (non-systemic filter), weakest on event sufficiency, turnover governance, and benchmark characterization.

Other relations: A4-QEND vs A6-TOM are genuinely distinct calendar mechanisms (quarter-boundary cross-sectional loser-unwind vs month-turn uniform settlement concentration) — not replicates, though selecting both would concentrate the budget in calendar seasonality. A5-MKT-SHOCK-DIFFUSION is genuinely distinct from the idio cluster (Lo-MacKinlay's cross term vs own term, cited by the proposal for exactly that separation) and is the pool's only continuation-type claim.

## 5. Hidden-rescue and beta-separation summary

No proposal shows momentum/trend/vol-target rescue scent: all idio variants select opposite-signed single events (no lookback/top-K); QEND uses prior-quarter ranks with an inverted sign at a fixed calendar clock plus a momentum-direction negative control; TOM's state is the calendar itself. Vol-scaling rules appear only as (a) the packet's identical risk-match convention on both sides of the alpha subtraction (A4 lane — cancels by construction, verified) or (b) benchmark-side declarations (A5 constant scale, A6 clip bands) — never as a claimed edge. Beta separation is strongest in the A4 lane (identical gross paths), adequate in the A5 lane (constant-scale per-unit-exposure claim), and control-dependent in the A6 lane (path mismatch; anchor-minus-control remains clean).

## 6. Writes

Exactly two files written, both uncommitted, for A1 integration:
- `research/audits/stocks_free_v3/d2_proposal_audit.json`
- `research/audits/stocks_free_v3/d2_proposal_audit.md` (this file)

A7 does not select. The ranking and objections above are the audit record for A1's frozen rubric.
