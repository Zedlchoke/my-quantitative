# D2_QUANT_SHEET — authorize the fee A7 vs defer (FEE-ES lane, 2026-10-04)

**Decision requested (owner D2, carried): authorize the fee A7 re-audit (packet READY, NOT_RUN) or
defer. This sheet quantifies both branches. Nothing here is a ruling.**

## 1. What is at stake — per-symbol tier-1 all-ins (USD/contract/side, MODELED COST)

Capture-backed corrected values (`fees_corrected.json`, sha `7cd65f25…aca8`) vs the stale parent
values they supersede; every row SOURCE=PUBLIC_REFERENCE, VERIFIED_VS_ACCOUNT=NOT_RUN:

| code | exchange+reg (corrected) | tier-1 all-in corrected | stale parent | Δ/side | tiers T2/T3/T4 (corrected) |
|---|---|---|---|---|---|
| **ES** | 0.85 + 1.38 + 0.01 | **2.24** | 2.247 | −0.007 | 2.04 / 1.84 / 1.64 |
| **NQ** | 0.85 + 1.38 + 0.01 | **2.24** | 2.247 | −0.007 | 2.04 / 1.84 / 1.64 |
| **6E / 6B / 6J / 6A** | 0.85 + 1.60 + 0.01 | **2.46** | 2.461 | −0.001 | 2.26 / 2.06 / 1.86 |
| **CL** | 0.85 + 1.50 + 0.01 | **2.36** | 2.37 | −0.01 | 2.16 / 1.96 / 1.76 |
| **NG** | 0.85 + 1.60 + 0.01 | **2.46** | 2.47 | −0.01 | 2.26 / 2.06 / 1.86 |
| **GC / SI** | 0.85 + 1.65 + 0.01 | **2.51** | 2.51 (unchanged) | 0 | 2.31 / 2.11 / 1.91 |

Max magnitude of the whole erratum: **$0.01/side (CL/NG)**; no observed pass/fail threshold flips.
The issue is correctness of published numbers, not magnitude (FEE_ERRATUM_DRAFT §3.4).

## 2. The 25-site propagation surface (what the A7 re-validates)

Definitive count (`PROPAGATION_COUNT_RECONCILIATION.md`, sibling, reconciled at HEAD `0225b3c2`):
canonical grep 26 files − 1 false positive = **25 genuine stale-parent-value sites = 22 FROZEN-HISTORICAL
+ 3 LIVING-DOC**; the "27" in the overnight dispatch mission text is a clerical off-by-one — retired.

| bucket | files | class |
|---|---|---|
| FUTURES-ES-V1-PACKET | 7 (SPEC_PB1_ES.md, PLAN, A7_SPEC.md, a7_spec_checks.json, probe_r2 py+out, handoff_A7-SPEC) | FROZEN |
| FUTURES-DATACONTRACT-QUAL-V1 | 3 frozen (ES_FEE_SOURCES.md, fees_table_es.json, handoff_D2-FEESRC) + **3 LIVING** (DATACONTRACT_QUALIFICATION.md, SUMMARY_QUAL_ACTIONS.md, OWNER_DECISION_PACKET.md) | mixed |
| FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 | 12 frozen (FEES_BY_CODE.md, fees_table_all.json, fetch_log, validate_fees_table.py, REPORT_VI, CROSSCHECK_REPORT, recompute_A4_fees.py, verify_findings.json, 2 handoffs, ES_DEEPFOUR_V3_ADDENDUM, evidence_index) + 1 FP excluded | FROZEN |
| Supplementary rounded-value living site | 1 — `PLAYBOOKS_DRAFT.md` (2.24/0.85 doc values; converges under correction) | LIVING (supplementary) |

Frozen sites stay byte-identical forever (append-only law — the erratum lives beside them); the
3 living docs get corrected by their owning lane in a future committed round **after** the A7.

## 3. SPEC_PB1_ES §5 exit-from-UNDER-REVIEW path

Current state (GATE_REVIEW_NOTE §1, FEE_ERRATUM_DRAFT §4 LAW 2): SPEC r3 stays freeze-ready-as-committed
but its three §5 exchange-dependent lines and every cost gate derived from them are recorded
UNDER REVIEW. The exact exit sequence:

1. **D2** — owner authorizes the A7 (this decision).
2. **A7 runs** — 9 checks re-derive every load-bearing cell from raw captures; adjudicate the
   under-review governance state; consume ruling e.4 (= D3) on the reg basis (see `D3_QUANT_SHEET.md`).
3. **Owner/owning lane applies corrected values by committed round** (not by the A7, not in-place):
   L100 exchange `1.386 → 1.38`; L101 offset note `0.011 → 0.01` (not-used policy unchanged);
   L104 all-in `21.006 / 33.506 / 46.006 → 21.00 / 33.50 / 46.00` (Δ −0.006/side; window
   2014-10-01..2017-12-31 variant shifts by the same −0.006).
4. Cost gates re-derive from the corrected §5; then, and only then, D2's other half — account
   verification (VERIFIED_VS_ACCOUNT) — can be scheduled. **The A7 closes source verification;
   it does NOT close account verification.** Both are needed for the fee layer to leave
   NOT_RUN/UNDER REVIEW.

## 4. Option A — authorize now: what unblocks (quantified)

- Independent re-derivation of all **10 code rows × 4 tiers** fee cells from raw capture bytes
  (the parent's "45/45 VERIFIED" was arithmetic-consistency-of-a-table-with-itself — the exact
  blind spot; no raw capture existed at parent time).
- Formal closure of the **25-site** propagation classification and the **3-line** SPEC §5
  under-review state (steps 2-4 above).
- Un-queues, downstream: NQ unlock (needs corrected fee **AND** account verification **AND**
  declared slippage — GATE_REVIEW_NOTE §4 lists all three pending layers); 6J exact-layer cost
  adjudication ($67.42 RT = 8.45 bp pinned, currently non-adjudicable); ES PB1's G1
  (after-modeled-cost expectancy) which sits on §5 numbers.
- Cash cost: **$0** (all evidence committed; zero fetches). Risk: none identified beyond audit time.

## 5. Option B — defer: quantified consequence of continued deferral

- **All cost gates stay open**: every symbol's fee layer remains MODELED COST /
  VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW (FX-EB/FX-JA/ES/NQ readiness artifacts all carry this
  label; re-verified this round). No cost-gate adjudication is legal before standardization
  (D3) + A7 (correctness) + account verification.
- **No scored successor can open per plan law**: NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER stand;
  the two-key GO requires key 1 = independent A7 prelaunch AUTHORIZED with 0 HIGH/CRITICAL
  unresolved — for any fee-consuming cycle that sits downstream of this A7; ES stays
  BLOCKED_TRIAL_BUDGET (24 frozen, headroom 0 — see `D4_QUANT_SHEET.md`); registry = 85 cycles,
  none futures-scored.
- Deferral cost is $0 cash today (max exposure of the underlying defect is $0.01/side) but
  **unbounded time**: the entire futures fee layer stays quarantined behind one signature, and
  every future round must re-verify the OPEN state (this packet's §0 grep becomes a standing tax).

## 6. Fail-closed default if undecided

Fees stay UNDER REVIEW; A7 stays NOT_RUN; D2/D3 remain open; nothing downstream moves. This is the
standing default and requires no action.

— Proposals only. FEE-ES raises no gate and grants no GO.
