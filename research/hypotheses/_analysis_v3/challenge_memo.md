# A4 Challenge Memo — adversarial audit of the V3 pipeline (Sprint V3)

Author: A4 (Independent Quant Reviewer) · Date: 2026-08-24
Inputs: `results/matrix/v3_execution_truth`, `results/stage_a_v3/`,
`results/stage_a_v2/`, `results/matrix/v2_stage_a_final/`,
`research/hypotheses/H-FUNDCROWD-MR-v2/{candidate.yaml,status.yaml}`,
`research/funding_pit.py`, `tests/test_funding_pit.py`, `PLAN.md`.
Read-only audit; no pipeline artifacts modified.

---

## 1. (a) Is next-bar-close fill still optimistic?

**Semantics in force.** `strategy_base.py:86-91`: a signal on closed bar t is submitted
on the first subsequent bar event (t+1) and **fills at that bar's CLOSE ± slippage
ticks**; the code itself states this is "next-bar-close", never "next-open".
Ledger confirms `signal_ts < submit_ts = fill_ts` (t+1 close timestamp), 0 ordering
violations over all 17,320 entries, `missing_timestamp_rows=0`.

**Residual optimism — yes, structurally.** The order is submitted *at* the t+1 event
and filled at *the close of that same t+1 bar*. In live trading a market order released
right after bar t's close transacts within seconds — i.e., near the **next open**, not
15 minutes later at the next close. Filling at t+1 close therefore grants the strategy
up to one full bar of post-signal drift for free whenever that drift is favourable.
Empirically the drift is favourable on average here: across 17,320 V3 fills, longs fill
below the signal-bar reference 51.4% of the time (median −0.4 bps vs reference),
shorts above 51.5% of the time. That favourable drift is exactly why V3 expectancy
improved on the median combo (see `v2_v3_execution_impact.md`) — and it is *not*
guaranteed capturable.

**Counterweight (why this is a bounded concern).**
* Same-bar-close is quarantined as `DIAGNOSTIC_ONLY`; V3-C03/C04 hold.
* One-tick adverse slippage is booked per entry (`slippage_cost = qty × tick`).
* Mean-reversion entries benefit from patience; momentum/breakout cells were hurt by
  delay more often than helped (breakout family mean optimism −0.237 is noise-dominated,
  but trend_pullback improved 6/7). The direction of bias is strategy-dependent.

**Uncertainty bound / required action.** True next-open is not recorded in any artifact,
so |fill − next_open| cannot be computed post hoc. Required before any survivor lock:
(1) log fill-bar OHLC in execution records; (2) run G4's pre-registered stresses —
`H-FUNDCROWD-MR-v2/candidate.yaml` cost_assumptions already mandate "+50% fee stress
and one-bar-delayed-entry stress" and PLAN §9 G4 requires two-tick adverse fill +
additional delay stress; none are implemented (`G4 NOT_IMPLEMENTED ×98`). Until then,
next-bar-close should be read as an *upper-bound* execution assumption, not a
conservative one.

Severity: **MEDIUM-HIGH** — does not invalidate G0–G3 results, but blocks treating
survivor economics as conservative.

## 2. (b) Fundcrowd survivor scrutiny (EXP-20260824-0713 v0, EXP-20260824-0715 v2)

### b.1 Single-symbol concentration / universe-artifact rule

All fundcrowd positive-expectancy cells are ETH-only (v0 +0.619, v1 +0.592,
v2 +0.520 USDT/trade; best non-ETH cell is ADA v0 at ≈ −0.16 after improvement).
Symbol breadth = 1/7 — the same signature that invalidated volcomp positives in V2
(`H-VOLCOMP-BRKOUT-v1/candidate.yaml`: "edge confined to a single symbol with all
others <= 0 (universe artifact)").

Does the pre-registered invalidation still apply? Cite the locked text:
`H-FUNDCROWD-MR-v2/candidate.yaml` `invalidating_evidence` lists quantitative clauses:
aggregate exp ≤ 0 → REJECT; position PF < 1.10 → REJECT; positive folds < 2/3 → REJECT;
supporting: fold ≥5 trades & PF <0.80; **"single fold contributes >50% of total PnL
(concentration)"**; gated variant not beating ungated reclaim_mr baseline on identical
folds; fee/delay stress failure. Under **V2** numbers, ETH v0/v1/v2 tripped two clauses
each: fold0 negative (⇒ <2/3 positive folds) and top-fold share 81.4%/81.2%/68.2% >50%.
The coordinator stamped `verdict: REJECTED` into `status.yaml`
(`verdict_at_utc: 2026-08-23T12:20:00+00:00`, "…fold_concentration_high 68-81 percent
single-fold artifact; universe-artifact invalidation triggered per locked invalidation
clause"). Under **V3** numbers, *no listed quantitative clause fires* for v0/v2:
exp >0, PF 1.449/1.379 ≥ 1.10, folds 3/3, top-fold share 48.8%/34.8%, and the gated
variant beats the ungated baseline on identical folds (reclaim_mr ETH base: exp +0.437,
PF 1.333).

A4 ruling requested from coordinator, because the machine state is now contradictory:
`status.yaml` says REJECTED; `gate_result.json` says G3 PASS. Two defensible readings:
1. **REJECTED stands** (strictly pre-registration-faithful): the invalidation was
   triggered on scored evidence at V2; a re-run under different execution semantics
   cannot un-trigger a clause that legitimately fired, and PLAN §15.3 forbids re-tuning
   H-FUNDCROWD-MR-v2 on the same S0. Survivors list becomes empty ⇒ §15.3 zero-survivor
   path to V4 opens cleanly.
2. **Family verdict is round-scoped**: if the coordinator adopts this reading, the two
   cells are genuine survivors — but then §15.3 requires completing G4/G5/G2b and a
   formal lock decision *before* V4, and the single-symbol breadth problem must be
   answered explicitly (it is not a named clause in this spec's list; relying on it
   implicitly, as the stamp text does, is weaker than the volcomp precedent's explicit
   wording).

Either way these two cells must **not** be treated as S1-lockable edge today.

Severity: **HIGH** (state-machine contradiction inside frozen artifacts; affects the
only survivors of the sprint).

### b.2 Regime / fold concentration

All three folds are positive, but they are consecutive quarters of one symbol in one
year; fold windows overlap a single ETH regime complex. The pass is knife-edge against
its own clause: v1 fails G3 solely because its top fold holds 50.3% (>50%) while v0
holds 48.8%. A ±1 trade shift flips a verdict — evidence the concentration metric has
insufficient resolution near the boundary, not evidence of robust breadth.

### b.3 PIT funding-percentile correctness

`research/funding_pit.py` behaviour is pinned by `tests/test_funding_pit.py`
(8 tests): rate_asof between settlements returns the older settled rate (no lookahead);
never forward-fills beyond last published settlement; percentile math hand-checked;
bounds/min-rank; insufficient history / empty bundle / pre-history fail-closed;
invalid window rejected. The candidate spec pins `decision_ts` = signal bar close and
8h settlement lag respect. No violation found. Residual (minor): percentile window
(30d rolling rank) is stateless-PIT ✓, but funding *data completeness* is only asserted
at G0 ("7_of_7_COMPLETE" in data_contract); a mid-window publication-gap detector test
does not exist.

Severity: **LOW** for correctness; LOW-MEDIUM for completeness monitoring.

## 3. (c) Residual provenance gaps

1. **Commission decomposition null everywhere.** All 17,320 V3 ledger rows have
   `commission: null` (V2 rows too) despite `fee_model: maker_taker`
   (`backtest/engine.py:164-168` → MakerTakerFeeModel, Binance tier-0 maker 0.02% /
   taker 0.05%). Aggregate reconciliation (`Σ ledger canonical_pnl == net_canonical_pnl`)
   is true *by construction* and therefore proves nothing about fees. With survivor PF
   at 1.38–1.45 against a 1.10 gate, fee application must be verifiable from artifacts:
   extract commission totals from engine account events into `canonical_metrics.json`
   before G2b counts as independent verification. Severity: **HIGH** (auditability of
   the exact quantity G3 gates on).
2. **Row-level `execution_mode: null` in all 17,320 rows** and `slippage_ticks: null`;
   mode is evidenced only at experiment level (`execution_ordering.mode`,
   `observed_modes: []` empty rather than enumerated). Severity: MEDIUM.
3. **config_sha256 lifecycle pollution.** Stamping `state/rejected_*` lines into
   frozen `candidate.yaml` changed the identity hash of all 21 fundcrowd cells between
   rounds. Verdict metadata belongs in sidecars (`status.yaml` pattern), not in hashed
   spec bytes. Severity: MEDIUM (already caused cross-round identity ambiguity).
4. **Timestamp inconsistency between rejection stamps.** Frozen copy:
   `rejected_at_utc: "2026-08-24T12:20:00Z"`; authoritative sidecar:
   `verdict_at_utc: "2026-08-23T12:20:00+00:00"` citing identical reason text. One of
   them is wrong; given the file's own history of a future-dated lock stamp (status.yaml
   header note), treat sidecar+git-commit as truth and fix the frozen-copy annotation
   through the coordinator (append-only correction, no rewrite of scored artifacts).
   Severity: MEDIUM.
5. **Dirty worktree at launch captured** (`dirty_worktree_at_launch: true`, launch
   commit `450e235`): satisfies V3-C08's capture requirement, but the uncommitted
   `research/matrix_runner.py` diff means runner provenance for reruns depends on the
   dirty-state record alone. Commit or stash the runner diff before G2b reruns.
   Severity: LOW-MEDIUM.

Not findings: window bounds, warmup boundaries (per-fold warmup_start/scored ranges
recorded), transform N/A reasoning, universe freeze hash + launch commit, and
positions digest reconciliation all check out.

## 4. (d) Verdict recommendation per PLAN §15

Machine-checked status against §15.1:

| Criterion | Status |
|---|---|
| V3-C01/C02 tests green | PASS (365 passed, 0 failed/xfailed, this date) |
| V3-C03 signal_ts < fill_ts | PASS (0 violations / 17,320 entries) |
| V3-C04 same_bar diagnostic only | PASS |
| V3-C12 one independent rerun per family | **FAIL — G2B NOT_YET_TESTED ×98** |
| V3-C13 survivors independently rerun | **FAIL — both G3 survivors lack G2b** |
| V3-C14 report/index/registry reconcile | PASS (98/98 declared=indexed=files=completed) |
| V3-C16 inventory 98/98 completed | PASS |

Blockers to `V4_AUTHORIZED`:

1. **G2b independent reproducibility not started** (C12+C13). Mandatory for the two
   fundcrowd survivors at minimum; per §15.3 a V3 survivor requires G4/G5/G2b complete
   and an explicit lock-or-reject decision before V4 starts.
2. **G4 robustness/stress suite absent** (`NOT_IMPLEMENTED ×98`): +50% fee, two-tick
   adverse fill, extra delay stress, parameter neighborhood, drop-one-fold/symbol.
   The fundcrowd spec itself pre-commits to two of these; skipping them would violate
   the candidate's own invalidating_evidence contract.
3. **Survivor legitimacy unresolved** (§2 above): REJECTED status vs G3 PASS conflict
   needs a coordinator ruling recorded append-only. Recommended default: uphold the V2
   REJECTED (pre-registration-faithful), list zero clean survivors, proceed via the
   §15.3 zero-survivor path once C12–C13 pass on pipeline-correctness reruns.
4. **Fee-commission provenance gap** (§3.1) should be fixed before the G2b reruns so
   the rerun verifies costs, not just PnL bit-equality.

**Recommendation: `BLOCKED_BY_V3`.** Pipeline correctness is materially improved and
the matrix is clean, but §15.1 C12/C13 fail and survivor handling (§15.3) is
incomplete. Do not start V4 hypothesis work until items 1–3 resolve; do not tune
fundcrowd (or any V1/V2 candidate) on S0 regardless of outcome.

— A4, independent review.
