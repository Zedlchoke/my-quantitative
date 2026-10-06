# A7_EXECUTION_PACKET — fee A7 re-audit run-order (FEE-ES lane, owner "Việc 3")

- Round: FUTURES-SIX-ADOPT-PREP-20261004, lane FEE-ES (decision-packet lane). Written 2026-10-04.
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-adopt/prep`, branch
  `codex/futures-six-adopt-prep-20261004`, HEAD measured `9fb66c88d464fd90748bc04d78280c2d87939cd3`
  (== dispatch base; one `git rev-parse HEAD`, no other git).
- Canonical readiness packet: sibling
  `…/FUTURES-P3-QUARANTINE-20261004/fee_a7_readiness/A7_FEE_READINESS_PACKET.md`
  (read-only). THIS packet re-states it as the executable run-order the owner would authorize,
  with every input re-hashed **in this worktree**.
- **STATUS: NOT_RUN — no D2 ruling exists.** This packet is preparation only; its existence is
  NOT authorization. This lane proposes, never decides.

## 0. NOT_RUN re-verification (method + hits, this worktree, 2026-10-04)

Method: recursive grep over `research/control/FUTURES-*/` for authorization patterns
(`GO_FOR_A7 | authorize the (fee )?A7 | D2 … GO/authorized/approved | approved to run | run the (fee )?A7`,
case-insensitive), every hit manually classified.

- **16 lines in 4 files, ALL inside `FUTURES-SIX-READINESS-20261004` (the prior round); ZERO hits
  in `FUTURES-SIX-ADOPT-PREP-20261004` (this round).** Classification of all 16:
  12 = `verify/fee_a7_status.json` (the verify lane's own record of the same search),
  2 = `verify/t6_t7_inventory_fee.py` (the search script itself),
  1 = `synth/OWNER_DECISIONS.md` L11 (**decision REQUEST**, "D2 Authorize the fee A7 … Until ruled …"),
  1 = `verify/verify_findings.json` (describes the prior search: "71 raw pattern hits, every hit a
  negation/status restatement").
- **Zero authorization artifacts.** The prior readiness verify additionally searched the sibling
  post-2026-10-04 round (`FUTURES-P3-QUARANTINE-20261004`): 71 raw hits, all negations.
- Conclusion: **fee A7 = NOT_RUN; D2 OPEN; fees UNDER REVIEW** (standing defaults hold).

## 1. Run order (what the authorized A7 does, in sequence)

| step | action | reads/writes |
|---|---|---|
| 0 | Confirm the written D2 authorization exists; re-measure the anchor HEAD (the dispatch-approved HEAD of the authorizing round) and record drift vs this packet's pins | read-only |
| 1 | **Input integrity** — recompute sha256 of all 21 §2 inputs; diff against this packet, `source/MANIFEST.md`, and `p0_verdict.json.outputs_recomputed`. Any drift ⇒ STOP and report | read-only |
| 2 | **Source-text re-extraction, per load-bearing cell**, in marker-preserving RAW HTML (`archive_*.html`) with row-label scoping and footnote-marker disambiguation (ES/NQ `1.38<sup>6</sup>` appears exactly twice — NQ L1691-1695, ES L1703-1707; `1.38<sup>2</sup>` on the Housing row must NOT be attributed to ES/NQ). Classify each cell LITERAL / LITERAL-marker-adjacent / FOOTNOTE_GLUED / NOT_LOCATED. Tag-stripped `*.php.txt` renders are glue-demonstration exhibits, never value authority | read-only |
| 3 | **Arithmetic re-check, independent** — commission ladder deltas (−0.20/−0.40/−0.60), per-code tier-2/3/4 all-ins, IBKR worked examples (`0.85+1.38+0.00+0.01=2.24` Fixed; Tiered example's stale reg-0.00 cell characterized, not inherited), IB-JP paren tax arithmetic (`0.011 = 0.01×1.1`) | read-only |
| 4 | **Validator real-mode reproduction** — run `impact/validate_fee_sources.py`: self-test expect 6/6 exit 0; real mode vs `verify/p0_verify_expected.json` (37-check grid) expect exit 1 (≥1 NOT_LOCATED from the deliberate adverse parent-value checks; corrected values LITERAL; `1.386` FOOTNOTE_GLUED ×2). Account for the 3 known validator warts (argv value parsing; span-wrapped marker missed; spurious MARKERS_PRESENT on `CME.php.txt`) | executes one committed script, writes its own output dir |
| 5 | **Propagation grep reproduction** — re-run the canonical grep at the authorized HEAD; reproduce 25 genuine = 22 frozen + 3 living (+ ERRATUM-SELFREF set + false positives; "27" retired as clerical off-by-one); confirm zero new genuine sites in non-erratum round files | read-only |
| 6 | **Frozen-vs-living classification audit** — verify no frozen-historical file was modified by the erratum rounds (batch-1 commit `72c9bc5b` = 359 files, 100% additions inside the round dir; re-measure git state rather than trusting this packet) | read-only |
| 7 | **"No-measured-cost" language scan** — every fee value carries MODELED_COST / VERIFIED_VS_ACCOUNT=NOT_RUN; "measured cost"/"complete cost" forbidden in family docs | read-only |
| 8 | **SPEC_PB1_ES under-review consistency adjudication** — spec still prints the stale §5 lines byte-identically (L100 `1.386`, L101 offset-0.011 not-used note, L104 `21.006/33.506/46.006`); `GATE_REVIEW_NOTE.md` §1 + `FEE_ERRATUM_DRAFT.md` §4 record them UNDER REVIEW; P1 families consume `fees_corrected.json`. **Consume ruling e.4 (= D3): which reg basis is canonical for modeled all-ins** | read-only |
| 9 | **Verdict + handoff** — every claim FACT (capture byte citation) / INFERENCE (labeled) / NOT_RUN; missing evidence never PASS; R2 must not repeat the parent A7's blind spot ("recomputed exact" = arithmetic-vs-transcribed-table, `a7_spec_checks.json` L47); write artifacts to the authorizing round's own dir + handoff | writes own dir only |

## 2. Inputs inventory — 21 inputs, re-hashed in THIS worktree (all matched)

All under `research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/`. Recorded sha256 from the
sibling packet §b (taken at HEAD `0225b3c2`); "this worktree" column = re-hash by FEE-ES lane
2026-10-04 at HEAD `9fb66c88`. **All 21 files are present in this worktree — zero sibling-only
inputs, zero NOT_REHASHED_HERE rows.** 21/21 MATCH.

Source captures (`source/`):

| File | Recorded sha256 (sibling packet) | This worktree | Verdict |
|---|---|---|---|
| `archive_CME.php.html` | `0f726c52ce90a2e159b376ef40e11e78afd8d279bceb263719038d4c3a3b9e85` | identical | REHASHED_HERE_MATCH |
| `archive_COMEX.php.html` | `8809dec04e5c9c15c7f15dda38f38f4417f96d249a284fbffeacffa6c02d13a4` | identical | REHASHED_HERE_MATCH |
| `archive_NYMEX.php.html` | `9031e0d9a274488d5aba14d256c97b0c4460bce5636c2bb25e5f351b214806ff` | identical | REHASHED_HERE_MATCH |
| `archive_NYMEX.php.html.gz_raw` | `64ecfd220713c2fe765192727d6607500c3fa8998f135601050e1d37916a32a9` | identical | REHASHED_HERE_MATCH |
| `archive_commissions-futures.php.html` | `6df03fd5645b67d46ca0d6db8c9689ed92d298571ceb99d59c92e9365040964f` | identical | REHASHED_HERE_MATCH |
| `archive_commissions-futures.php.html.gz_raw` | `50a950c9d2843b331d6b4df122b0bdfc56bc82ece9c3b4f75a9fa191c6e8b0eb` | identical | REHASHED_HERE_MATCH |
| `CME.php.txt` | `75a8647065d1590e06db7b1244f72a759b09ec672f8eb2072fd09343a5978565` | identical | REHASHED_HERE_MATCH |
| `COMEX.php.txt` | `4317c15a187162aef9a80c76e63af372b7034a4157e0317b9b634237e798997a` | identical | REHASHED_HERE_MATCH |
| `NYMEX.php.txt` | `dbcc25b3cf519925eebfd9388312c6eca940a27287319a329767b4e58129ed1a` | identical | REHASHED_HERE_MATCH |
| `commissions-futures-amer.php.txt` | `14d79331c4255addefd7a573c83730f08832508b1ceb3b3b64f9cc4fb0348cda` | identical | REHASHED_HERE_MATCH |
| `CME.php.md` (QUARANTINED — not evidence) | `469d8220a061384a0ec80a8d5c1091c06c617a688d1cbb46fc7bb5f4c8de545c` | identical | REHASHED_HERE_MATCH |
| `fees_corrected.json` | `7cd65f253f51ed0bc8fad25dc939797fb4e874ce1d975269f98affa128a2aca8` | identical | REHASHED_HERE_MATCH |
| `FEES_CORRECTED.md` | `006d6372fb5a6f09595d24297174a3a0c1390d27ac869b027adf12bd1b5d1bef` | identical | REHASHED_HERE_MATCH |
| `superscript_adjudication.md` | `e36a01239329a869ae64ab5867c50087f23c6977fcdc7f801d18dbaab7d37356` | identical | REHASHED_HERE_MATCH |
| `fetch_log.jsonl` | `f370f305e53ad6706574bf975f2e935dfc8a2137ac8721016e2b4d0fe1544bf6` | identical | REHASHED_HERE_MATCH |
| `MANIFEST.md` | `c8c8ff5a06d5091689d028666633cecba27cb55b9c9ac64d0e3a543958ffed4f` | identical | REHASHED_HERE_MATCH |

Impact layer (`impact/`):

| File | Recorded sha256 | This worktree | Verdict |
|---|---|---|---|
| `FEE_ERRATUM_DRAFT.md` | `3796579d51027d951f527d6989b3da9fcdd3f1395ed4925085782303ce39e5d1` | identical | REHASHED_HERE_MATCH |
| `validate_fee_sources.py` | `fdead766f84521337ff4b7af3a861437a24317831bda9874494fc2c8fe780050` | identical | REHASHED_HERE_MATCH |
| `GATE_REVIEW_NOTE.md` | `5d50ac79c9bca82c696caa7315cbc9c81bcdd4e9a2c09745c6a713efd11161d0` | identical | REHASHED_HERE_MATCH |

Verify layer (`verify/`):

| File | Recorded sha256 | This worktree | Verdict |
|---|---|---|---|
| `P0_ERRATUM_VERDICT.md` | `6967a804468f9a095a45297f1200f49d537d47c3d1442c9a5548af01b0c03575` | identical | REHASHED_HERE_MATCH |
| `p0_verdict.json` | `f1e5b6363af9271be931477d3b6e9197ba57b779c469a0c0dadbc6138c60d347` | identical | REHASHED_HERE_MATCH |

Supporting (context, also re-hashed here, all match their recorded pins):
`FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` `445f749906481f33080185cab1628e6365ef2f6db3b9c4f9f0847646eb6b7073` MATCH ·
`audit/a7_spec/A7_SPEC.md` `0ce63a0d6181379c6b2f2fee1ea720168ee57ae74a198695caa51e018855f5d0` MATCH ·
`audit/a7_spec/a7_spec_checks.json` `ac33414563fbecaf13dba99e4eefb1a8215282e09bf31811d9e7593db33ecd38` MATCH ·
`PLAN_futures_es_v1.md` `06140882f13d96fd1325c472ef3788da7d4ce1c6b571c7c27d75b8e8e0c7a06b` MATCH.

## 3. Execution preconditions

1. **Written owner/plan authorization for the A7 exists** (packet existence ≠ authorization;
   standing ruling: "cho agent làm đi" for PREP does NOT ratify D2/D3/D4 and grants no typed GO).
2. Anchor HEAD = dispatch-approved HEAD of the authorizing round; drift re-measured and recorded at start.
3. A7 is read-only over the evidence universe; writable surface = its own round dir + handoff.
   **Append-only law**: no edits to committed or frozen files; corrections supersede by reference.
4. Standing gates stay through and after the run: NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER;
   PB2 HOLD; PB3 PARK; ES 24 identities BLOCKED_TRIAL_BUDGET. No scoring, no GO, no ledger/registry
   write, no order of any kind rides on the A7 result without the owner lifting them in writing.
5. Zero network fetches required or recommended (all evidence is committed captures; P0-VERIFY §6).
   Heavy global lock respected, though nothing heavy is expected.
6. The 4 open rulings (§4) decided with or ahead of authorization — e.4 (= D3) gates check 8.

## 4. Open rulings the run consumes (owner/plan, not A7-derivable)

- **e.1** FX-group fee mapping corroboration — accept PARTIAL (CME "Forex Futures" row aliases, 1.60
  confirmed; 6E/6B/6J/6A never printed verbatim) or name the binding page.
- **e.2** Account geography basis for the IB-JP paren (`0.011 = 0.01×1.1` tax artifact) — confirm
  US-entity pages are the operative basis.
- **e.3** NYMEX reg 0.02→0.01 temporal window / epoch-binding rule for historical-year modeling.
- **e.4** (= **D3**) Reg-component basis for modeled all-ins: NFA 0.02 vs IBKR offset 0.01 —
  quantified in `D3_QUANT_SHEET.md` (same dir).

## 5. Artifacts a run would produce

All under the authorizing round's own control dir (append-only):

1. `A7_FEE_REAUDIT.md` (or round-equivalent) — verdict + findings ledger (FACT/INFERENCE/NOT_RUN),
   per-cell re-extraction table with byte citations, R2-non-inheritance statement.
2. Machine digest JSON — per-check results (inputs 21/21, cells classified, arithmetic, propagation
   25 = 22+3, frozen-integrity, language scan, SPEC-consistency adjudication).
3. Validator outputs — self-test log (expect 6/6, exit 0) + real-mode report vs the 37-check grid
   (expect exit 1 with the documented adverse-check NOT_LOCATEDs).
4. Propagation reproduction table — canonical grep output + classification (25 genuine / 2 FP /
   19 ERRATUM-SELFREF at HEAD `0225b3c2`) re-run at the authorized HEAD.
5. Handoff JSON in the authorizing round's `dispatch/` (schema `zcode_orch_v3_handoff@1`).

No value is "fixed" by the A7: corrected §5 lines (1.38 / 21.00 / 33.50 / 46.00; offset note 0.01)
are applied only afterwards by the owner/owning lane, by committed round (GATE_REVIEW_NOTE §1;
FEE_ERRATUM_DRAFT §4 LAW 3).

— End A7_EXECUTION_PACKET.md. Nothing here is ratified; A7 remains NOT_RUN as of 2026-10-04.
