# GATE_REVIEW_NOTE — freeze & cost-gate consequences of the fee-value hypothesis

Round FUTURES-OVERNIGHT-PREP-20261003 / lane P0B-FEEIMPACT. DRAFT — no value
scenario adopted; corrections are locked by a later P0-VERIFY lane. Nothing
in this note edits or unfreezes any committed artifact; it records status
only. Companion: `FEE_ERRATUM_DRAFT.md`, `validate_fee_sources.py` (same dir).

## 1. SPEC_PB1_ES r3 §5 cost numbers — UNDER REVIEW (not edited)

Affected rows under the correction scenario (Scenario B in the erratum):

- `| Exchange (CME) | 1.386 | public LIVE_OFFICIAL (IBKR CME.php offset
  table); current-as-approximation mọi năm lịch sử |` → 1.38 under B.
- All-in/side `S1 21.006 · S2 33.506 · S3 46.006` (and the 2014-2017 window
  −0.01 variant) → 21.00 / 33.50 / 46.00 under B (exchange delta −0.006).
- The `IBKR offset 0.011 KHÔNG dùng, KHÔNG cộng kèm` note → the offset
  value itself becomes 0.01 under B; the *not-used* policy is unchanged.

NOT affected: Commission 0.85 row; NFA 0.02/0.01 official timeline row
(independent S5 source); spread 6.25 proxy; slippage 12.50/25.00/37.50;
S1-over-SL priority; sizing; the 24 trial identities.

Status law: SPEC r3 stays freeze-ready-as-committed, but **its §5
exchange-dependent numbers and every cost gate derived from them are
recorded as UNDER REVIEW** until a new A7 re-audits cost arithmetic against
corrected, capture-backed sources (A7's R2 "recomputed exact" was arithmetic
vs the transcribed D2 table, not a source re-read — see
`a7_spec_checks.json` L47 and the CROSSCHECK blind spot, erratum §3).

## 2. D2 r6 public-reference table — stale under correction

`DATACONTRACT_QUALIFICATION.md` §3 L206-207 (r6 summary: "+exchange 1.386
+regulatory 0.011; all-in tính 2.247 @≤1k") and its backing artifacts
(`analysis/d2_feesrc/ES_FEE_SOURCES.md` E3/E4, `fees_table_es.json`) become
stale under B: components 1.38/0.01, all-in 2.24, tiers 2.04/1.84/1.64.
Noteworthy: §1.7 L162 already records the doc row "1.38+reg → all-in 2.24
(doc)" — under B the computed value CONVERGES to it (the 2.247-vs-2.24
"khớp" rounding in SUMMARY_QUAL_ACTIONS L15 collapses to exact agreement).
Labels that stay true either way: SOURCE=PUBLIC_REFERENCE,
VERIFIED_VS_ACCOUNT=NOT_RUN, MODELED_COST, current-schedule-as-approximation
disclosure, NFA timeline.

## 3. Parent-round fees_table_all.json — stale under correction

`FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/fees/fees_table_all.json` (all 9
codes) + `FEES_BY_CODE.md` §4.7 grid + the expectations hard-coded in
`fees/validate_fees_table.py` L56-71 and `verify/recompute_A4_fees.py` L35`
all embed the A-values. Under B: NQ 2.247→2.24 (2.047/1.847/1.647 →
−0.007 each), FX 2.461→2.46, CL 2.37→2.36, NG 2.47→2.46, GC/SI 2.51
unchanged. `CROSSCHECK_REPORT.md`'s "VERIFIED / 45/45 exact" must be read
as arithmetic-consistency-of-the-table-with-itself; it does not survive as
source verification, and any future re-run of those scripts against
corrected values will (correctly) fail until their expectations are updated
by the owning lane after P0-VERIFY.

## 4. NQ cost gate — decidable only with corrected numbers + pending layers

- The gate's all-in input (REPORT_VI L60, handoff_VERIFY L98: "all-in
  2.247 tier-1") is UNDER REVIEW; under B it is 2.24. No gate pass/fail
  threshold observed so far flips on Δ ≤ $0.01/side, but the number feeding
  the gate must be the verified one before adjudication.
- Still-pending layers independent of this defect:
  1. VERIFIED_VS_ACCOUNT = NOT_RUN (r6b: owner account artifacts had no
     futures/fee/plan lines; plan/tier of the live account unknown).
  2. Slippage = NOT_RUN_NO_DECLARED_VALUE (DATACONTRACT §1.7) — owner
     declaration required.
  3. Spread = close-proxy (conservative), BBO measured NOT_RUN.
- Therefore the NQ sibling-unlock decision remains gated on: corrected
  fee values (P0-VERIFY + new A7) AND account verification AND declared
  slippage. Missing evidence is NOT_RUN, never inferred PASS.

## 5. What this round does NOT change

No committed file edited; no ledger/registry touched; no gate re-adjudicated
here; no scenario adopted. This note + the erratum + the validator are the
complete writable surface of this lane.
