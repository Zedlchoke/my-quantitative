# V6 CLOSURE ADDENDUM — 2026-08-25 (A2)

> **Status:** ADDITIVE closure artifact. No V6 evidence file is modified; stale claims below are superseded by this addendum only.
> **Author:** A2 (closure/provenance), worktree `/Users/hoangminhlong/my-quantitative-v7-wt/a2-closure`, branch `orca/v7-a2-closure`, bootstrap `dd026c0`.
> **Source of truth:** PRIMARY repo `/Users/hoangminhlong/my-quantitative` (read-only). Every cited artifact is pinned by sha256 in the checksum block.

---

## 1. Lineage and tree state at V6 closure

- **Final HEAD at V6 closure:** `fbd2e9d36b5349489ef29deec4cdeb8bca2b89ad` — *"A7 independent audit V6: PASS, family verdict V6P_PASS_V6_CANDIDATE_FAIL agreed; MDD sub-claim corrected (7D mdd 0.0884 not 0.2885); 0 unresolved HIGH/CRIT"*.
- **Working tree at closure: CLEAN.** Verified against `research/audits/v6/final_transition.json` (`final_head`, `immutable: true`) and `research/control/twelve_hour_run/shutdown_report.json` (created after the audit commit, terminal outcomes recorded).
- One post-closure commit `563810787…` by A1 added shutdown/closure evidence (`final_transition.json`, `v7_authorization.json`, `shutdown_report.json`).
- **V7P bootstrap:** `dd026c0` (*BOOTSTRAP: V7P→V7 execution contract*). `fbd2e9d` is a verified git ancestor of `dd026c0` (`merge-base --is-ancestor` in this worktree), so the V7P sprint starts from the exact closed-V6 lineage.

## 2. Terminal verdicts

| Surface | Verdict |
|---|---|
| V6P | `V6P_PASS_V6_AUTHORIZED` (20/20 gates, A7 PASS) |
| V6 | `V6P_PASS_V6_CANDIDATE_FAIL` — 4/4 scored trials consumed, **0 candidates locked** |
| V7 | **NOT_RUN 0/4** — NOT_AUTHORIZED at V6 shutdown (A04 wiring absent / A08 no launch-head attestation / A10 <180 min) → `SKIPPED_TIME_BUDGET`; still 0/4 today |
| S1 | NOT_STARTED / UNTOUCHED |
| Live money | UNCHANGED_DISABLED |

Pipeline surfaces VALID: FG0/FG1 measured-clean, hashes clean, matrix COMPLETE with `mismatches: []`, registry append-only verified, full-surface reproductions green post-env-bug-fix (R4/R3 supersede R1/R2 FAIL rows). A7 v6 audit: **PASS, 0 unresolved HIGH/CRITICAL**.

## 3. The four V6 rows — EXACTLY per PLAN §0.2

Numbers sourced from raw `results/portfolio_v6/*/canonical_metrics.json` (PnL / PF / MDD / fold PnLs) plus `results/matrix/v6_xsect_funding_carry/family_summary.json` (funding totals). All pinned in §7.

| Trial | Net PnL | PF | MDD | Funding | Fold PnLs | Kết luận |
|---|---:|---:|---:|---:|---|---|
| Funding Carry 1D | −5,679.96 | 0.9784 | 24.50% | +1,958.03 | +10,112 / +7,782 / −23,575 | Reject |
| Funding Carry 3D | +2,076.03 | 1.0116 | 15.18% | +2,129.47 | +6,949 / +8,704 / −13,578 | Reject |
| Funding Carry 7D | +20,580.87 | 1.1570 | 8.84% | +2,277.23 | +10,866 / +10,169 / −454 | Reject: top positive fold 51.66% > 50% |
| Reverse 3D control | −20,102.83 | 0.8699 | 28.52% | −1,677.84 | negative control | Expected failure |

Per-trial reject taxonomy (A7-agreed):

1. **1D — mechanism_failure:** pnl < 0, PF 0.978 < 1.10 (co-failures: MDD 24.50%, top symbol XRP 60.78%).
2. **3D — edge_too_weak:** PF 1.0116 < 1.10 hard minimum (co-failures: MDD 15.18%, top fold F2 55.60%, top symbol ETH 53.68%).
3. **7D — concentration fail (see §4):** passes PF/pnl/funding/MDD but top positive fold F1 = 51.66% > 50%; XG4 robustness INCONCLUSIVE/un-gated; DSR unavailable (fold series n=3).
4. **Reverse 3D — failed as designed:** sign-flip loses to best directional (−20,102.83 vs +20,580.87) so the "reverse beats best" invalidation trigger did NOT fire; funding −1,677.84 confirms the flip; `CONTROL_ONLY`/DIAGNOSTIC_ONLY — never promotable, never counted as a family member.

Family-level: no trial satisfies full FG3 ⇒ no FG4+ escalation ⇒ `eligible_candidate: null` ⇒ family REJECT_ALL. Adjacency note (`adjacent_positive_pair=true` on raw PnL for 3D+7D) does not rescue eligibility because each member independently fails its own hard gates.

## 4. Mandatory reading on 7D: MDD correction

- **REFUTED claim:** "7D MDD = 28.85% > 10%, hard risk fail." The 0.28852 figure exists ONLY in the superseded env-bug rerun `VERIFY-V6-CARRY-7D-R2` (harness env-deletion bug, fixed at `fe31440`) and coincides with the unrelated v6p MOM trial.
- **Authoritative MDD(XSECT-FUND-CARRY-7D) = 0.088350 → 8.84% ≤ 10% ⇒ PASS.** Identical across canonical_metrics, ledger recomputation, and the R4 independent rerun (`mdd_match=true`; XG5 PASS, `mdd_lock_blocker=false`). A7 check A7-V6-2 = PASS_WITH_CORRECTION.
- **Actual 7D reject reason: FG3 top positive fold concentration — F1 carries 51.66% of positive pnl (>50% cap).** A7 classification: `fg3_concentration_fail_top_fold_gt_50pct_with_robustness_inconclusive`. The edge is real but concentrated; it is research signal to retain, not a promotable candidate.

## 5. V7 status

**0/4 trials run. NOT_RUN / NOT_AUTHORIZED.** It is forbidden to describe V7 as "completed", "backtested", or "failed". Next authorized step is the V7P repair phase (PLAN §§6–7); V7 launches only after 18/18 prelaunch gates including an A7 prelaunch attestation.

## 6. Stale files SUPERSEDED by this addendum

| Stale item | Why stale | Resolution |
|---|---|---|
| Old `CONTINUE.md` (commit 5638107) | Handoff written for old lineage ("fbd2e9d + 1 shutdown commit"), pre-dates dd026c0 V7P topology | Rewritten on this branch as current handoff |
| `results/matrix/v6_xsect_funding_carry/family_summary.json` | `fg3` dict omits the concentration sub-clauses (top fold ≤50%, top symbol ≤40%) — machine record lacks the true reason 7D was rejected (A7 finding F-2) | This addendum's §3 table + reject reasons; original untouched |
| `research/hypotheses/H-XSECT-FUNDING-CARRY-v1/status.yaml` | Showed `scored_trials_used: 0`, `verdict: none` despite 4 scored trials and terminal fail | Synced on this branch: 4 / CANDIDATE_FAIL / locked none |
| `research/hypotheses/H-XSECT-FUNDING-PRICE-DIVERGENCE-v1/status.yaml` | Verdict unset while lifecycle moved forward | Confirmed on this branch: 0 scored, FROZEN_FOR_EXECUTION awaiting V7 |

No retry/error history deleted; no result metrics rewritten in place; corrections exist only through this hashed addendum.

## 7. Checksums (sha256, computed via hashlib over PRIMARY bytes)

```
84f88249a966538c71ee10af15423ef7994edfdf6b497be151799886ec1be11f  research/audits/v6/final_transition.json
0eb500a32d3c5c52adf3fb21315e4eec91936eeace7eb3eb18c46eb13282d7e5  research/audits/v6/v6_family_transition_input.json
34859a649bd74e9a494a30cf01c4beabbbaa4e1fc75d5da88255ff677404d527  research/audits/v6/scientific_audit.json
48390548b1260b4c1af64c2d1baa494147a631c07aed70129853edfa0478ba51  results/matrix/v6_xsect_funding_carry/family_summary.json
1ab55a829fc8591c58df2b98452f18c329d3a086095c856b5eee3970e4aebd6b  results/matrix/v6_xsect_funding_carry/reconciliation.json
8dfa3c458559515cc878fdf1b839a47a58a1476f44f5cfc3a10c37594efe1bac  results/portfolio_v6/XSECT-FUND-CARRY-1D/canonical_metrics.json
5840e2cbb4a3d0fb8f1fde2fa34eb15eeb290903b709da2d906ae55244caa00d  results/portfolio_v6/XSECT-FUND-CARRY-1D/gate_result.json
f8145ff2b2b22f8c69d5cff32a8ead7e81c7593133e172259c3e73bc511b0b37  results/portfolio_v6/XSECT-FUND-CARRY-3D/canonical_metrics.json
3b71f282bee19018e3a070a61ed27895406a4d51ab822cfd45b9b462ddc346d7  results/portfolio_v6/XSECT-FUND-CARRY-3D/gate_result.json
a90b77414476f41d4d0ad3daea23542f3b7af17f97d8771427db200eba3624c3  results/portfolio_v6/XSECT-FUND-CARRY-7D/canonical_metrics.json
311c4814db906e367bc37463ec6582bb291f79f4c6cc493e9db5261214343c17  results/portfolio_v6/XSECT-FUND-CARRY-7D/gate_result.json
c71bae3839803e744c38313dd3957e0869018a573ba05e1342a4401488936ed1  results/portfolio_v6/XSECT-FUND-REVERSE-3D-CONTROL/canonical_metrics.json
912b32c3159662503ad41d42d94174f377453a5da53f1c5b8db202d945969e80  results/portfolio_v6/XSECT-FUND-REVERSE-3D-CONTROL/gate_result.json
a659e5c67ca2369a77f69eda425ef600d9bfb0b91f3245203fe22d2cd2b38915  research/audits/v6p/scientific_audit_v6p.json
c6a95da08ded3c91583e5b95ac029dc4ea55ee80d3f0e4443b3d296d4d17ed4a  research/control/twelve_hour_run/shutdown_report.json
```

Cross-check: `sha256(research/audits/v6/scientific_audit.json)` begins `34859a64`, exactly matching `final_transition.json → audit.json_sha256_prefix` — the pinned audit bytes are those referenced at transition time.

---
*A2 closure/provenance · branch orca/v7-a2-closure · bootstrap dd026c0 · 2026-08-25*
