# PROPAGATION_COUNT_RECONCILIATION — definitive 25 / 26 / 27 adjudication

- Round: FUTURES-P3-QUARANTINE-20261004, lane Q3-FEE-A7-READY (PREP, read-only).
- Worktree: `prep/futures-behavior-10syms-20261002` @
  `0225b3c25bf1cf269dae5a835853b5b3904125a0` (== dispatch sha; re-measured
  2026-10-04 before writing; no drift). Tracked tree clean at start.
- Written: 2026-10-04 UTC. Companion machine mirror:
  `PROPAGATION_COUNT_RECONCILIATION.json` (same dir). Packet for the auditor:
  `A7_FEE_READINESS_PACKET.md` (same dir).
- Every claim below is FACT (command + output reproducible at this HEAD),
  INFERENCE (labeled), or NOT_RUN. No committed file was edited.

## 0. Executive answer

| Quoted number | What it actually counts | Verdict |
|---|---|---|
| **27** | Text in the overnight round's `dispatch/DISPATCH_MANIFEST.json` mission line for P0B ("27 files identified by Lead grep"). Never reproduced by any measurement. | **Clerical off-by-one — retire the number.** P0B measured 26 and flagged the discrepancy in its handoff; P0-VERIFY independently reproduced 26 and recorded "off-by-one stands as reported" (`P0_ERRATUM_VERDICT.md` §4). Plausible origin [INFERENCE, unverifiable from artifacts]: the Lead's verbal list may have included `PLAYBOOKS_DRAFT.md` (the supplementary rounded-value living site), i.e. 26 grep hits + 1 supplementary = 27. |
| **26** | File-level count of the canonical grep **restricted to the three pre-erratum dirs** (`FUTURES-ES-V1-PACKET`, `FUTURES-DATACONTRACT-QUAL-V1`, `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003`) — the universe that existed when the numbers were quoted. | **CORRECT and stable.** Reproduced 3× independently (Lead chat list; P0B re-run; P0-VERIFY) and reproduced a 4th time by this lane at HEAD 0225b3c2 (identical 26-file set; §2 below). |
| **25** | **Genuine fee-value sites** = 26 files − 1 false positive (`coverage_remeasure.json` sub-second timestamp `00:00:00.011588` at L1784) = **22 FROZEN-HISTORICAL + 3 LIVING-DOC**, plus `PLAYBOOKS_DRAFT.md` as a supplementary rounded-value living site (not matched by the pattern). | **CORRECT, definitive, and still the propagation count of stale parent values.** Zero new genuine stale sites appeared in the overnight round's non-erratum files (§3). |

**One-line law: 26 raw files − 1 false positive = 25 genuine propagation sites
(22 frozen + 3 living); "27" is a manifest-text clerical error that no
measurement ever supported.**

## 1. Canonical grep re-run (FACT)

Command, from worktree root, at HEAD `0225b3c2`:

```
grep -rln -E "1\.386|2\.247|0\.011|2\.461|2\.37\b|2\.47\b" \
  research/control/FUTURES-ES-V1-PACKET \
  research/control/FUTURES-DATACONTRACT-QUAL-V1 \
  research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 \
  research/control/FUTURES-OVERNIGHT-PREP-20261003
```

Exit 0; **46 files** today (the original three-dir universe returned exactly
26 — byte-identical list to the erratum's §3 map — plus 20 files inside the
overnight round dir, which did not exist when the original counts were made).

## 2. Decomposition of the 46 hits at HEAD 0225b3c2

| Bucket | Files | Class |
|---|---|---|
| `FUTURES-ES-V1-PACKET` | 7 | all GENUINE (FROZEN-HISTORICAL): SPEC_PB1_ES.md, PLAN_futures_es_v1.md, audit/a7_spec/A7_SPEC.md, a7_spec_checks.json, probes/probe_r2_cost_arithmetic.py, probes/out_probe_r2_cost_arithmetic.json, dispatch/handoff_A7-SPEC.json |
| `FUTURES-DATACONTRACT-QUAL-V1` | 6 | GENUINE: 3 FROZEN (analysis/d2_feesrc/ES_FEE_SOURCES.md, fees_table_es.json, dispatch/handoff_D2-FEESRC.json) + 3 LIVING (DATACONTRACT_QUALIFICATION.md, SUMMARY_QUAL_ACTIONS.md, OWNER_DECISION_PACKET.md) |
| `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003` | 13 | 12 GENUINE (FROZEN: fees/FEES_BY_CODE.md, fees_table_all.json, fetch_log.jsonl, validate_fees_table.py, REPORT_VI.md, verify/CROSSCHECK_REPORT.md, recompute_A4_fees.py, verify_findings.json, dispatch/handoff_A4-FEES.json, handoff_VERIFY.json, deep/es_nq/ES_DEEPFOUR_V3_ADDENDUM.md, evidence_index.json) + 1 FALSE-POSITIVE (events_bbo_coverage/coverage_remeasure.json L1784 `00:00:00.011588` timestamp) |
| `FUTURES-OVERNIGHT-PREP-20261003` | 20 | 19 **ERRATUM-SELFREF** + 1 FALSE-POSITIVE — see §3 |

Genuine total: **25** (7 + 6 + 12). False positives: **2**. Selfref: **19**.

## 3. The overnight round's 20 hits — classified file-by-file

The overnight round legitimately contains the erratum documents themselves:
their quoting of 1.386/0.011/2.247/… is the erratum describing its own subject
(self-reference), **not propagation of the stale values into decisions**.

| # | File | Matched content | Class |
|---|---|---|---|
| 1 | `fees_erratum/impact/FEE_ERRATUM_DRAFT.md` | both-scenario tables, site-by-site quotes (37 lines) | ERRATUM-SELFREF |
| 2 | `fees_erratum/impact/GATE_REVIEW_NOTE.md` | under-review cost-gate law, scenario quotes | ERRATUM-SELFREF |
| 3 | `fees_erratum/impact/validate_fee_sources.py` | parent-value test vectors + adverse checks | ERRATUM-SELFREF (test fixture) |
| 4 | `fees_erratum/source/CME.php.txt` | LIVE 2026-10-03 tag-stripped render printing glued `1.386`/`0.011` (L52/54/97-98) — the flattened render **is the evidenced defect mechanism**, byte authority is `archive_CME.php.html` (`1.38<sup>6</sup>`) | ERRATUM-SELFREF (evidence capture) |
| 5 | `fees_erratum/source/fees_corrected.json` | parent-vs-corrected comparison fields | ERRATUM-SELFREF |
| 6 | `fees_erratum/source/FEES_CORRECTED.md` | corrected table w/ "was 1.386" provenance | ERRATUM-SELFREF |
| 7 | `fees_erratum/source/fetch_log.jsonl` | fetch outcome lines quoting glued renders | ERRATUM-SELFREF |
| 8 | `fees_erratum/source/superscript_adjudication.md` | adjudication narrative quoting both forms | ERRATUM-SELFREF |
| 9 | `fees_erratum/verify/P0_ERRATUM_VERDICT.md` | verdict quoting both forms | ERRATUM-SELFREF |
| 10 | `fees_erratum/verify/p0_verdict.json` | machine verdict (parent/lane comparison cells) | ERRATUM-SELFREF |
| 11 | `fees_erratum/verify/p0_verify_expected.json` | P0-VERIFY's 37-check grid incl. deliberate adverse parent-value checks | ERRATUM-SELFREF |
| 12 | `fees_erratum/verify/p0_verify_validator_report.json` | validator output on the grid | ERRATUM-SELFREF |
| 13 | `fees_erratum/verify/p0_verify_validator_stdout.log` | validator stdout | ERRATUM-SELFREF |
| 14 | `dispatch/DISPATCH_MANIFEST.json` (L12) | owner-claim quote "Lane A4 of parent round read 1.386/0.011 - extra digit" | ERRATUM-SELFREF (governance text; also the origin of the "27" mission-text error) |
| 15 | `dispatch/handoff_P0-VERIFY.json` | verdict/retire-directive language | ERRATUM-SELFREF |
| 16 | `dispatch/handoff_P0A-FEESOURCE.json` | glue-confirmation summary + retire directive | ERRATUM-SELFREF |
| 17 | `dispatch/handoff_P0B-FEEIMPACT.json` | propagation-map result text (incl. the 26-vs-27 note) | ERRATUM-SELFREF |
| 18 | `dispatch/handoff_SYNTH-VERIFY.json` | retire-family directive | ERRATUM-SELFREF |
| 19 | `synth/REPORT_VI.md` (L26/L34) | reports the defect + "→ RETIRE làm SOURCE" directive | ERRATUM-SELFREF (reporting, not cost input) |
| 20 | `cme_cal_gap/equity/captures/nq_pcal_20110305184630.html` (L6998) | `esindex: 0.011` — JS variable inside a 2011 CME product-calendar capture; nothing to do with fees | **FALSE-POSITIVE** |

**Net new genuine stale-fee sites in the overnight round's non-erratum files:
ZERO.** The P1 hypothesis families were dispatched after P0A/P0B and consume
the CORRECTED table (§4).

## 4. hypo/** stale-fee audit (the mission's explicit check) — NEGATIVE, with one basis-divergence observation

Sweep of `FUTURES-OVERNIGHT-PREP-20261003/hypo/**` + all P1/P2 handoffs for
parent values in any form (`1.386|2.247|0.011|2.461|2.37|2.47|21.006|
33.506|46.006`):

- **ZERO occurrences of parent fee values used as cost inputs.** The canonical
  pattern matches no hypo/ file at all; the extended sweep matches only the
  erratum-reporting lines in `synth/REPORT_VI.md` already classified SELFREF.
- Every family carries corrected values with citations, e.g.:
  - `hypo/es_nq/esnq_hypotheses.json` L15: fees ES/NQ T1 **2.24**, tiers
    2.04/1.84/1.64 — "OBSERVED (FEES_CORRECTED.md @72c9bc5b)"; fee_status
    "MODELED COST; VERIFIED_VS_ACCOUNT=NOT_RUN; UNDER REVIEW until new A7".
  - `hypo/6j_6a/jpy_aud_hypotheses.json` L25/L37: **2.46/2.26/2.06/1.86**;
    `hypo/6e_6b/fx_hypotheses.json` L16: **2.46**;
    `hypo/comm/comm_hypotheses.json` L23-26: CL **2.36**, NG **2.46**, GC/SI
    **2.51** — all match `fees_corrected.json`.
  - `hypo/6j_6a/captures/source_sha256.tsv` L24 even sha-pins FEES_CORRECTED.md
    (`006d6372…d1bef` — recomputed by this lane, MATCH).

**Finding (NOT a stale parent value; flag-only, nothing edited) — reg-component
basis divergence in the ES/NQ family:**

- `hypo/es_nq/esnq_hypotheses.json` L17-18 and `dispatch/handoff_P1-ESNQ.json`
  L28 model ES all-in **20.99 / 33.49 / 45.99** and NQ **23.49 / 28.49 /
  33.49** per side, composed as "2.24 fees + spread proxy 6.25/16.25 +
  slippage tiers". The 2.24 fee all-in bundles the IBKR **regulatory offset
  0.01**.
- `SPEC_PB1_ES.md` §5 (L100-104, frozen r3) instead mandates the **NFA
  timeline 0.02 default / 0.01 for 2014-10-01→2017-12-31** as the single reg
  source and states the IBKR offset is "KHÔNG dùng, KHÔNG cộng kèm" (not used,
  not added). Under the erratum's corrected values, the SPEC-§5-consistent
  all-ins are **ES 21.00 / 33.50 / 46.00** and **NQ 23.50 / 28.50 / 33.50**
  (2.25 = 0.85+1.38+NFA 0.02, not 2.24).
- So the ES/NQ family's modeled cost floors are **$0.01/side lower** than the
  SPEC-law composition would give (cost understated ⇒ marginally
  less conservative for any future cost-gate use). Labeled MODELED/UNDER
  REVIEW by the lane itself; decision impact nil today (families are
  contingency-only, ES blocked by 24-identity cap, nothing scored/scheduled).
- **Ruling needed (A7/owner): standardize the reg basis for modeled all-ins**
  — IBKR offset 0.01 (current hypo/es_nq composition, 2.24) vs NFA timeline
  0.02 (SPEC §5 law, 2.25). Do not edit either file before the ruling.

## 5. Repo-wide out-of-scope sweep (completeness for the A7 auditor)

`grep -rln` over the whole worktree (excluding `.git` and `research/control`)
matches 7 additional files — **all non-fee contexts, all adjudicated
false-positive** (crypto/stocks cycles predating the futures fee work):

| File:Line | Matched | Actual meaning |
|---|---|---|
| `research/hypotheses/_analysis_v3/v2_v3_execution_impact.md:68,103` | `+0.0119` | crypto return metrics |
| `research/wayfinder/HYPOTHESIS_LEDGER.md:131` | `-0.011226` | stocks anchor expectancy |
| `research/wayfinder/FAMILY_FAILURES.jsonl:53` | `-0.011226` | same, ledger row |
| `research/wayfinder/FAMILY_FAILURES.jsonl:80` | `0.007-0.011` | z-score band prose |
| `research/audits/v7p/global_trial_ledger_before.json` (5 hits) / `..._after.json` (5 hits) | e.g. `11:36:22.461179` | sub-second timestamps / return floats |
| `plans/PLAN_crypto_historical_replication_3f_v1.md:160` | `0.0115504…` | numeric tolerance |
| `tests/test_sprint_eval_v2.py:309` | `exp_after_cost: 0.011228` | test fixture |

## 6. Definitive number table (the one to quote going forward)

| Metric | Value | Definition |
|---|---|---|
| Raw grep files, 3 pre-erratum dirs (original universe) | **26** | file-level hits of the canonical pattern |
| Raw grep files, 4 dirs incl. overnight round, at HEAD 0225b3c2 | **46** | 26 + 20 overnight |
| False positives (original universe) | **1** | `coverage_remeasure.json` L1784 timestamp |
| False positives (overnight round) | **1** | `nq_pcal_…html` L6998 `esindex: 0.011` |
| ERRATUM-SELFREF (overnight round) | **19** | erratum docs + captures + round governance quoting the numbers about themselves |
| **Genuine stale-parent-value propagation sites** | **25** | **22 FROZEN-HISTORICAL + 3 LIVING-DOC**; unchanged since P0B; zero new |
| Supplementary rounded-value living site | 1 | `PLAYBOOKS_DRAFT.md` (2.24/0.85 doc values; converges under correction) |
| New genuine sites in overnight non-erratum files | **0** | P1 families use corrected values |
| "27" | **invalid** | manifest mission-text clerical off-by-one; retire |

## 7. Commands (reproducible, exit codes)

- Canonical 4-dir grep: exit 0, 46 files (§1).
- 3-dir restriction: exit 0, 26 files, set-identical to FEE_ERRATUM_DRAFT §3.
- Per-file counts: `grep -rc` (same pattern) — outputs used for §2/§3.
- Token extraction: `grep -o` for FP adjudication (esindex/timestamp).
- `shasum -a 256` over all 21 fees_erratum inputs — all match
  `source/MANIFEST.md` 16-hex prefixes and handoff digests (see A7 packet §2).
