# VERIFY_FOLLOWUP_REPORT — correction-wave audit, FUTURES-SIX-SCORED-GATE-PREP-20261004

- Verifier: fresh-context independent verifier (audit only; repairs nothing, rules nothing).
- Baseline: HEAD `4531c5f5321d12e38a257c24b2951c0ed4dabd34` (confirmed by
  `git rev-parse HEAD`); corrections under audit = uncommitted changes on top.
- Date: 2026-10-04. Zero network. All values re-measured from bytes.
- Write boundary respected: this file is the only artifact written.

## Git evidence log (all read-only, all `git -C <worktree>`)

1. `rev-parse HEAD` → `4531c5f5321d12e38a257c24b2951c0ed4dabd34` (matches dispatch baseline).
2. `status --porcelain` (start and end) →
   ` M research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/REPORT_VI.md`
   ` M research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/synth/CYCLE_PROPOSAL.md`
   ` M research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/synth/OWNER_DECISION_PACKET.md`
   `?? research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/cal_close/ERRATUM_F1.md`
   `?? research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/synth/COST_FREEZE_ERRATUM.md`
   (+ this verifier's own `verify/followup/VERIFY_FOLLOWUP_REPORT.md` once written)
3. `diff 4531c5f5 --stat` → quoted under V4.
4. `diff 4531c5f5 --stat -- research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md research/control/FUTURES-SIX-ADOPT-PREP-20261004` → empty output, exit 0 (V4).

---

## V1 — Byte evidence for the settled exchange value — **PASS**

Target: `research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/source/archive_CME.php.html`
(156,432 bytes, wayback id_ 2026-06-08 snapshot).

| Item | Measured | Verdict |
|---|---|---|
| Literal `1.38<sup` count | **3** occurrences: L1659, L1694, L1706 | see NOTE N-1 |
| `1.38<sup>6</sup>` count | **exactly 2**: L1694 (`E-mini Equity Futures` row, aliases `BQX, ER2, NQ, QCN, …`), L1706 (`E-Mini S&P; Equity Futures` row, aliases `EMD, ES, SMC, …`) | PASS (expectation met for the footnote-6-glued value) |
| Housing row | L1656 label `<strong>Housing Index</strong>` / L1659 value `1.38<sup>2</sup>` — footnote **2**, different product row (BOS, CHI, CUS, DEN, LAV, LAX, MIA, NYM, SDG, SFR, WDC); NOT attributed to ES/NQ | PASS (trap correctly excluded) |
| Footnote 6 text | footnote `<ol>` L1903–1912; item 6 = L1909: `Non-Member spread orders will be charged $1.30 per contract.` (byte-identical in the text render `CME.php.txt` numbered item 6) — a spread-order note, not a decimal | PASS |
| Worked example | In a DIFFERENT capture — `archive_commissions-futures.php.html` (RAW 2026-09-25) L4055, Fixed Example, verbatim: `1 ES Futures Contract = IBKR Execution Fee USD 0.85 + Exchange Fee USD 1.38 + Clearing Fee USD 0.00 + Regulatory Fee USD 0.01 = USD 2.24` (arithmetic exact). L4049 Tiered example prints reg `0.00` yet sums `2.24` — the documented IBKR-side stale cell, not inherited (A7 §2 cell 14, §3) | PASS |

**NOTE N-1**: the check text says "count occurrences of `1.38<sup` (expect exactly 2)". The
literal prefix occurs 3×; the footnote-6-glued value `1.38<sup>6</sup>` occurs exactly 2×. The
check's own next clause (Housing `1.38<sup>2</sup>` is a different row) reconciles this, and
A7_FEE_REAUDIT §2 cell 3 records precisely the same duality ("exactly 3× … sup-6 count = exactly 2").
No defect — recorded for precision.

## V2 — Arithmetic of the corrected dual-variant table — **PASS (0 mismatches)**

SPEC_PB1_ES.md §5 decomposition cited (file byte-frozen, see V4):
- L99 commission `0.85`; L100 exchange `1.386` (the stale print); L101 regulatory `0.02` default / `0.01` for 2014-10-01→2017-12-31; L102 spread half-turn `6.25`; L103 slippage `S1/S2/S3 = 12.50/25.00/37.50`; L104 all-in default `S1 21.006 · S2 33.506 · S3 46.006`.

Independent recomputation (this verifier, from the components above):

| Quantity | Recomputed | Claimed (A7 §8 / ERRATUM §2 / OD-2) | Match |
|---|---|---|---|
| A fees/side (X=1.38, reg 0.02) | 0.85+1.38+0.02 = **2.25** | 2.25 | YES |
| A all-in S1/S2/S3 | 2.25+6.25+{12.5,25,37.5} = **21.00 / 33.50 / 46.00** | 21.00 / 33.50 / 46.00 | YES |
| A round-trip | **42.00 / 67.00 / 92.00** | 42.00 / 67.00 / 92.00 | YES |
| B fees/side (X=1.38, reg 0.01) | **2.24** | 2.24 | YES |
| B all-in S1/S2/S3 | **20.99 / 33.49 / 45.99** | 20.99 / 33.49 / 45.99 | YES |
| B round-trip | **41.98 / 66.98 / 91.98** | 41.98 / 66.98 / 91.98 | YES |
| Stale SPEC (X=1.386, reg 0.02) | 0.85+1.386+0.02+6.25+{12.5,25,37.5} = **21.006 / 33.506 / 46.006** | 21.006 / 33.506 / 46.006 | YES |
| NQ all-in A / B (both docs) | A 0.85+1.38+0.02+6.25+{15,20,25} = 23.50/28.50/33.50; B −0.01 = 23.49/28.49/33.49 | 23.50/28.50/33.50 · 23.49/28.49/33.49 | YES |
| Delta | A−B = 2.25−2.24 = **$0.01/side** = **$0.02/RT** | $0.01/side = $0.02/RT | YES |
| Window statement | SPEC L101 grants reg 0.01 inside 2014-10-01→2017-12-31 ⇒ A-in-window = 0.85+1.38+0.01+6.25+slip = **exactly B's row** (20.99/33.49/45.99) | "A within window equals B's row" (ERRATUM §2 window note; OD-2 table "(window: = B's row)") | YES |

Cross-check A7_FEE_REAUDIT §8 table (L162–172) vs COST_FREEZE_ERRATUM §2 table (L43–54)
vs OD-2 table (OWNER_DECISION_PACKET L32–35): **every cell equal** (reg rows, fee rows,
ES all-in rows, RT rows, NQ rows, stale-print row). **NOTE N-2**: the delta row's sign
convention differs — A7 L170 prints B-relative "−$0.01/side = −$0.02/RT"; ERRATUM L51
prints "Delta A−B: +$0.01/side = +$0.02/RT". Same magnitude, opposite explicit labels;
not a numeric mismatch. **NOTE N-3**: stale SPEC round-trip 42.012/67.012/92.012 appears
only in A7 L169 (= 2× the stale side values, arithmetic consistent); ERRATUM omits the
stale RT — an omission, not a conflict.

## V3 — Consistency of the corrected synthesis (current working tree) — **PASS with findings**

Read in full: `synth/OWNER_DECISION_PACKET.md`, `synth/CYCLE_PROPOSAL.md`, `REPORT_VI.md`,
`synth/COST_FREEZE_ERRATUM.md`; token greps over all four.

| Assertion | Result | Evidence |
|---|---|---|
| (a) No operating/default text presents 21.006… or 2.24-as-default-A as consumable | **PASS** | All `21.006/33.506/46.006` occurrences are: OD-2 L37 "Stale SPEC print … is NEVER consumable"; CYCLE_PROPOSAL L41 "never consumable"; ERRATUM L50 "NEVER consumable" + historical descriptions (L6, L26, L32, L59); REPORT_VI L63 describes the retired defect. `2.24` appears only as labeled Option B (OD-2 L35, OD sentence L87, CYCLE_PROPOSAL L84, REPORT_VI L79) or as the worked example / defect narrative. Zero consumable presentation. |
| (b) CYCLE-1 status BLOCKED_COST_FREEZE everywhere stated | **FAIL at 1 site → F-1 (MAJOR)** | Correct at: OD-2 L43, OD packet L91–92, CYCLE_PROPOSAL L38, L47–48, L89, L105–106, ERRATUM §4 L84, REPORT_VI L69 + status-table L79. **Violation: REPORT_VI L8–9 one-line summary still reads "đưa ES về trạng thái chỉ còn 3 chữ ký trước scored (đăng ký + A7 prelaunch + GO)"** — the exact phrasing ERRATUM §4 withdraws and REPORT_VI's own §Follow-up (L69–70) says was withdrawn ("rút lại câu 'chỉ còn registration+A7+GO'"). The summary was not updated. |
| (c) Withdrawn silent-default documented with lawful residual reading (A × 1.38) | **PASS** (with residual language findings F-2/F-3) | ERRATUM §3.4 L71–80 ("the lawful reading … is the NFA-basis RULE inherits; the glued VALUE 1.386 does not … executable default … Variant A × corrected 1.38 = 2.25 / 21.00-33.50-46.00. However … requires the explicit D3 signature (fail-closed)"); OD-2 L40–43 ("WITHDRAWN as an operating rule; its only lawful reading was 'Variant A basis × corrected 1.38' … explicit signature instead (fail-closed)"); CYCLE_PROPOSAL L47–50 ("silent-default operating rule is withdrawn … lawful silent reading, if ever needed, is Variant A × corrected 1.38 only"). |
| (d) Minimal decision sentence includes D3 signature with both variants' exact numbers | **PASS** | OD packet L87–89: `"D3 basis = [A|B] (A: 2.25/side, 21.00/33.50/46.00 · B: 2.24/side, 20.99/33.49/45.99). Chọn CYCLE-1 FUTURES-ES-PB1-V1 (PB1-only 24), và tôi đăng ký cycle + gõ GO đúng mẫu ở gate."` — all six numbers exact per V2; L91–92 ties CYCLE-1 unblock to the D3 half. |
| (e) No text claims the owner ratified anything | **PASS** | All ratification mentions are negations: OD packet L3 "NOTHING HERE IS RATIFIED BY THIS THREAD", L12–16 (audit-execution reading, D2 stays open if owner disagrees, 0 trials), L94 "nothing self-ratified"; CYCLE_PROPOSAL L6–10 ("NOT a typed GO. Nothing in this proposal runs anything"); ERRATUM L91–92 ("picks nothing; ratifies nothing"); REPORT_VI L4–5, L10, L45 ("không tự phê"). Grep for positive-form ratification: zero hits. |

**F-2 (MAJOR)**: OWNER_DECISION_PACKET L22, OD-1 CYCLE-1 row, signatures column:
"**OD-2 (or default A)** + registration + prelaunch A7 + typed GO" — contradicts OD-2
L26 ("REQUIRED, EXPLICIT, before CYCLE-1 freeze") and L40–43 (default WITHDRAWN;
explicit signature required, fail-closed) in the same file, and ERRATUM §3.4/§4. It
re-opens the exact silent-default path the wave closed. No stale number is printed, but
the signature requirement is misstated.

**F-3 (MINOR)**: CYCLE_PROPOSAL L113: "one scope choice, one D3 choice **(or default)**,
then registration and the typed GO phrase" — same defect class as F-2 (generic wording,
contradicts the same file's L47–50 and §3 blocker line L104–107).

## V4 — Historical non-modification — **PASS**

`git diff 4531c5f5 --stat` (tracked changes only), quoted:

```
 .../REPORT_VI.md                                   | 26 ++++++++++++---
 .../synth/CYCLE_PROPOSAL.md                        | 32 +++++++++++++------
 .../synth/OWNER_DECISION_PACKET.md                 | 39 ++++++++++++++--------
 3 files changed, 70 insertions(+), 27 deletions(-)
```

Untracked additions per `status --porcelain`: the 2 new erratum files
(`synth/COST_FREEZE_ERRATUM.md`, `cal_close/ERRATUM_F1.md`) — untracked files do not
appear in `diff --stat`; the combination of the two outputs yields exactly the expected
5-file change set (plus this verifier's own `verify/followup/` output).

Restricted pathspec diff `git diff 4531c5f5 --stat -- research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md research/control/FUTURES-SIX-ADOPT-PREP-20261004`:
**empty output, exit 0** — SPEC_PB1_ES.md and the entire six-adopt round are byte-frozen
(zero diff). Verdict: PASS.

## V5 — ERRATUM_F1 safety — **PASS**

- Recomputed `shasum -a 256 cal_close/captures/svc_20260401_20260722114222.json` =
  `cdba0a6550c433978ef2818881d3f80efd34a5f8b1746bb764457d7c7bb3e5da` ==
  `cal_close/SHA256SUMS_lane.txt` line 9 (exact). All **10/10** SUMS rows recomputed
  MATCH by this verifier (adv_gf pdf/txt, bls ×3, cdx ×2, svc ×3).
- ERRATUM_F1's authority claim confirmed: `calendar_close_delta.json` keys the recovery
  cell off THIS round's own hashes — L33 `sha256_wire` `cdba0a65…` (== SUMS row) and L63
  provenance arrays (`sha256_wire` includes `cdba0a65…`). Round-1's claimed `0700f57c…`
  appears ONLY inside narrative evidence strings (delta JSON L61, L107; CAL_CLOSE_REPORT
  L21, L78), always as a disclosed non-match; `c8388564` (round-1's verify-reported
  value) has **zero** occurrences in cal_close. No arithmetic consumes round-1's claimed
  hashes — the only roles are narrative citations. ERRATUM_F1's safety claim ("the delta
  JSON keys off this round's own hashes") is byte-true. Verdict: PASS.

## V6 — Erratum law compliance (COST_FREEZE_ERRATUM.md) — **PASS**

| Requirement | Evidence |
|---|---|
| (a) Historical-frozen vs executable-at-freeze classified | §1.2 ("The frozen SPEC's numbers are historical evidence of the SPEC, not executable cost"), §1.3 (six-adopt packet "stands as history"), §3.1 ("Historical frozen evidence") vs §3.2 ("Proposed executable cost at a new freeze") |
| (b) Evidence-settled value named with citations | §1.1: exchange ES/NQ = 1.38 "EVIDENCE-SETTLED, not a choice"; RAW-HTML `1.38<sup>6</sup>` ×2 (NQ L1694, ES L1706); footnote-6 text quoted; sibling glue proof `0.95<sup>4</sup>`→"0.954"; worked example `0.85+1.38+0.00+0.01=2.24`; citations `[FEES_CORRECTED.md; P0_ERRATUM_VERDICT; A7_FEE_REAUDIT §2-§4 — all committed]`. All independently re-verified under V1. |
| (c) D3/e.4 marked REQUIRED explicit ruling | §3.3 ("**D3 (= e.4) — the regulatory basis choice — is REQUIRED and now EXPLICIT for CYCLE-1**"), §4 ("BLOCKED_COST_FREEZE pending the owner's D3/e.4 basis ruling") |
| (d) NO self-ratification | Header "(append-only correction of record)"; §2 titled "PROPOSED; MODELED COST; VERIFIED_VS_ACCOUNT=NOT_RUN"; §3 titled "(no self-ratification)"; §3.2 "decided ONLY by the owner"; §3.4's under-silence residual reading is immediately fail-closed ("the packet now requires the explicit D3 signature (fail-closed) and CYCLE-1 is declared BLOCKED_COST_FREEZE"); footer "picks nothing; ratifies nothing". Grep: "chosen" zero hits; "ratif" only in negations. |
| (e) Supersedes six-adopt packet by reference, without editing | Header L10–12 ("superseded **by reference** … no frozen historical file is touched (SPEC_PB1_ES and the six-adopt packet stand as committed)"); §1.3 ("superseded by this erratum for every future freeze. Nothing in it is edited"); byte-proven by V4's empty pathspec diff on `FUTURES-SIX-ADOPT-PREP-20261004/**`. |

---

## Findings ledger

| id | severity | finding | citations |
|---|---|---|---|
| F-1 | **MAJOR** | REPORT_VI one-line summary (L8–9) still carries the withdrawn "chỉ còn 3 chữ ký trước scored (đăng ký + A7 prelaunch + GO)" status claim; contradicts COST_FREEZE_ERRATUM §4, REPORT_VI's own §Follow-up (L69–70) and corrected status table (L79). No stale fee number involved, but the round's headline status contradicts the binding BLOCKED_COST_FREEZE state. | REPORT_VI.md L8–9 |
| F-2 | **MAJOR** | OD-1 CYCLE-1 row still offers "OD-2 (or default A)" as the signature path; contradicts OD-2 L26/L40–43 (REQUIRED EXPLICIT; default withdrawn, fail-closed) in the same file and ERRATUM §3.4/§4. Re-opens the silent-default loophole in the signature-requirements column of the decision packet. | OWNER_DECISION_PACKET.md L22 |
| F-3 | MINOR | CYCLE_PROPOSAL §3 summary line "one D3 choice (or default)" — same defect class as F-2, generic wording, contradicts the same file's L47–50 and L104–107. | CYCLE_PROPOSAL.md L113 |
| N-1 | NOTE | `1.38<sup` literal count is 3 (incl. Housing footnote-2 row); the footnote-6-glued `1.38<sup>6</sup>` count is exactly 2 — matches the check's intent and A7 §2 cell 3. | archive_CME.php.html L1659/L1694/L1706 |
| N-2 | NOTE | Delta-row sign convention differs between A7 §8 (B-relative, "−$0.01/side") and ERRATUM §2 ("A−B +$0.01/side"); magnitude $0.01/side = $0.02/RT identical. | A7 L170; ERRATUM L51 |
| N-3 | NOTE | Stale round-trip 42.012/67.012/92.012 printed only in A7 §8; ERRATUM §2 omits stale RT row — omission, not conflict. | A7 L169; ERRATUM L50 |

## Verdict

**FOLLOWUP-WAVE VERDICT: PASS_WITH_FINDINGS — fee correction is arithmetic-exact and
evidence-settled end-to-end (V1/V2/V4/V5/V6 clean); 2 MAJOR residual-language defects
(F-1 REPORT_VI summary retains withdrawn "3 signatures" status; F-2 OD-1 "(or default A)"
contradicts the fail-closed explicit-D3 requirement) + 1 MINOR (F-3) remain in the
corrected files. No CRITICAL. Nothing consumed, nothing ratified; the substantive
BLOCKED_COST_FREEZE law is correctly stated in all decision-bearing locations.**

— End VERIFY_FOLLOWUP_REPORT.md (verifier output; audit only).
