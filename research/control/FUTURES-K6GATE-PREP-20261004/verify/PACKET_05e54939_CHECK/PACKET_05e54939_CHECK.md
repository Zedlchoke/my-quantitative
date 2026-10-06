# PACKET_05e54939_CHECK — independent pre-use integrity check of 05e54939

- Verifier: fresh-context independent verifier (audit only; repairs nothing; rules nothing).
- Commit under audit: `05e5493971116eec8db5ea49e30c06930e8cc6bc` (follow-up final commit,
  FUTURES-SIX-SCORED-GATE-PREP-20261004). Baseline for before/after: `4531c5f5321d12e38a257c24b2951c0ed4dabd34`.
- Date: 2026-10-04. Zero network. Zero PnL by construction. All values re-measured from bytes.
- Claim ledger consumed first: `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/verify/followup/VERIFY_FOLLOWUP_REPORT.md`
  (2 MAJOR F-1/F-2 + 1 MINOR F-3 found by the prior verifier; fixed by the controller in 05e54939 after that verifier measured).
- Write boundary respected: this dir (`verify/PACKET_05e54939_CHECK/`) in the k6gate worktree is the only artifact written.
- The six-gate worktree was not modified in any way (reads only).

## Precondition — exact-HEAD + clean tree — **PASS**

| Command | Result |
|---|---|
| `git -C /Users/hoangminhlong/my-quantitative/.worktrees/futures-six-gate/prep rev-parse HEAD` | `05e5493971116eec8db5ea49e30c06930e8cc6bc` — EXACT match |
| `git -C … status --porcelain` | EMPTY (clean) — working tree read directly; no `git show` fallback needed |

## Git evidence log (all read-only; every command disclosed)

1. `git -C <six-gate-prep> rev-parse HEAD`
2. `git -C <six-gate-prep> status --porcelain`
3. `git -C <six-gate-prep> show 4531c5f5:research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/REPORT_VI.md` piped to `grep -n "chữ ký"` / `grep -n "3 chữ ký"`
4. `git -C <six-gate-prep> show 05e54939:research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/REPORT_VI.md` piped to `grep -n "chữ ký"` / `grep -n "3 chữ ký"`
5. `git -C <six-gate-prep> show 4531c5f5:…synth/OWNER_DECISION_PACKET.md` piped to `grep -ni "or default"`
6. `git -C <six-gate-prep> show 05e54939:…synth/OWNER_DECISION_PACKET.md` piped to `grep -ni "or default"`
7. `git -C <six-gate-prep> show 4531c5f5:…synth/CYCLE_PROPOSAL.md` piped to `grep -ni "or default"`
8. `git -C <six-gate-prep> show 05e54939:…synth/CYCLE_PROPOSAL.md` piped to `grep -ni "or default"`
9. `git -C <six-gate-prep> show 05e54939:…synth/OWNER_DECISION_PACKET.md` piped to `sed -n '15,45p'`
10. `git -C <six-gate-prep> diff 4531c5f5 05e54939 --stat` (6-file change set, quoted under C4)
11. `git -C <six-gate-prep> diff 4531c5f5 05e54939 -- research/control/FUTURES-ES-V1-PACKET/ research/control/FUTURES-SIX-ADOPT-PREP-20261004/ research/control/FUTURES-OVERNIGHT-PREP-20261003/`

Non-git reads (working tree, clean at the audited HEAD): `ls`, `sed -n`, `grep -rn` over the
round dir, `shasum -a 256` (SPEC + 5 fee inputs), `find` (A7_EXECUTION_PACKET location),
`python3` (Decimal recomputation). No writes outside the k6gate verify dir. Never staged/committed/pushed.

---

## C1 — The three defects are GONE at exactly this HEAD — **PASS (all three)**

### F-1 (was MAJOR) — REPORT_VI.md one-line summary — **FIXED**

| Commit | Evidence |
|---|---|
| 4531c5f5 (before) | L8: `đóng 10/10 advisory NQ 2026, đưa ES về trạng thái chỉ còn 3 chữ ký trước` (grep `"3 chữ ký"` → 1 hit; `"chữ ký"` → L8, L20–21) |
| 05e54939 (after) | grep `"3 chữ ký"` → **0 hits (exit 1)**. `"chữ ký"` remaining hits are all D3-requirement/BLOCKED statements: L11 `erratum + **CYCLE-1 = BLOCKED_COST_FREEZE chờ chữ ký D3 tường minh**`; L82 status-table row `BLOCKED_COST_FREEZE: chữ ký D3 cơ sở phí`; L72 `rút lại câu "chỉ còn registration+A7+GO"` (explicit WITHDRAWAL). The new summary (L3–16) leads with the fee erratum + BLOCKED_COST_FREEZE + `Số trial scored thực tế đã chạy: 0`. |

### F-2 (was MAJOR) — OWNER_DECISION_PACKET.md OD-1 CYCLE-1 row — **FIXED**

| Commit | Evidence |
|---|---|
| 4531c5f5 (before) | L22: `\| **CYCLE-1 FUTURES-ES-PB1-V1 (RECOMMENDED)** \| ES, PB1 only \| **24** (no cap change) \| OD-2 (or default A) + registration + prelaunch A7 + typed GO \| …` |
| 05e54939 (after) | grep `"or default"` (case-insensitive) → **0 hits (exit 1)** in the whole file. L22 signatures column now: `**OD-2 D3 signature (EXPLICIT — no silent default)** + registration + prelaunch A7 + typed GO` — consistent with OD-2 L26 (`REQUIRED, EXPLICIT, before CYCLE-1 freeze`) and L40–43 (default WITHDRAWN, fail-closed). |

### F-3 (was MINOR) — synth/CYCLE_PROPOSAL.md — **FIXED**

| Commit | Evidence |
|---|---|
| 4531c5f5 (before) | L101: `choice (or default), then registration and the typed GO phrase.` |
| 05e54939 (after) | grep `"or default"` → **0 hits (exit 1)**. L112–113 now: `one scope choice, one D3 signature (explicit; no silent default), then registration and the typed GO phrase.` |

## C2 — Whole-tree residue scan at this HEAD — **PASS for C1-class defects; shortlist residue FOUND (new findings F-4/F-5/F-6)**

Greps over ALL of `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/` (.md/.json/.txt/.log) at HEAD.

### (a) `1.386` — every hit classified; **zero hits use 1.386 as a value**

All hits fall in the allowed classes:
- COST_FREEZE_ERRATUM quotes labeling it retired/never-consumable: `synth/COST_FREEZE_ERRATUM.md` L23, L25, L27, L58, L71, L74; `synth/CYCLE_PROPOSAL.md` L85 ("1.386 retired"); `synth/OWNER_DECISION_PACKET.md` L28 ("glued 1.386 retired").
- A7 audit artifacts describing the SPEC's historical print / glue defect: `fee_a7/A7_FEE_REAUDIT.md` (L54–55, 69, 78, 88, 112, 153, 169, 182), `fee_a7/arithmetic_check.txt` L45, `fee_a7/a7_fee_digest.json` (L78, 109, 135, 160, 171), `fee_a7/a7_validator_report.json` (L9, 85, 239, 245–255), `fee_a7/validator_selftest.log` (L1, 8), `fee_a7/validator_realmode.log` (L1, 13, 36–39), `fee_a7/reextraction_cells.txt` (L129–131, 136), `fee_a7/propagation_grep.txt` L161 (false-positive note: trade price `19801.386`), `fee_a7/language_scan.txt` L13 (scan record quoting sibling frozen round's D2 row — NOTE N-4 below), `dispatch/handoff_FEE-A7.json` (L62, 86, 141), `verify/rerun_validator_*.{log,json}`, `verify/VERIFY_REPORT.md` L30 ("stale 1.386"), `verify/followup/VERIFY_FOLLOWUP_REPORT.md` (L46, 58, 81 — prior verifier's own quotes).

**N-4 (NOTE)**: `fee_a7/language_scan.txt` L13 quotes `FUTURES-DATACONTRACT-QUAL-V1/OWNER_DECISION_PACKET.md` L17 containing `+exchange 1.386 +regulatory 0.011; all-in tính 2.247`. That is an A7 audit artifact's scan record of ANOTHER round's frozen text, not a use in this round; that round is outside this audit's scope. No consumption.

### (b) `21.006|33.506|46.006` — every hit classified; **shortlist hits are NOT historical-print citations → F-4/F-5**

Allowed (labels stale/NEVER-consumable or audit artifacts): REPORT_VI.md L10, L66, L82 (all state stale/erratum'd); synth/COST_FREEZE_ERRATUM.md L6, L26, L32, L50, L59; synth/CYCLE_PROPOSAL.md L41 ("never consumable"); synth/OWNER_DECISION_PACKET.md L37 ("NEVER consumable"); fee_a7/* (A7_FEE_REAUDIT L78, L155, L169; arithmetic_check L45–47; a7_fee_digest L95, L162; batch1_commit_stat L5); verify/VERIFY_REPORT.md L30; verify/followup/* ; dispatch/handoff_FEE-A7.json L86.

**NOT allowed — found (pre-existing residue, byte-identical at 4531c5f5; NOT touched by the fix wave):**

- **F-4 (CRITICAL)** `shortlist/shortlist_6sym.json` L56 and `shortlist/SHORTLIST_6SYM.md` L71:
  `"cost": "S1 21.006 / S2 33.506 / S3 46.006 per side FROZEN Variant A (SPEC s5), binds until D3"` /
  `**S1 21.006 / S2 33.506 / S3 46.006 per side FROZEN (Variant A)** — binds until D3 (SPEC §5)`.
  This presents the retired stale print as the operative frozen cost ("binds until D3") with NO stale/erratum label — a use-as-value outside the allowed set (check program: any hit that uses the value is CRITICAL). It contradicts COST_FREEZE_ERRATUM §2 L50 ("Stale SPEC print (NEVER consumable)"), §1.2–1.3, and OD-2 L37–39. The "binds until D3" claim is exactly the silent-default binding ERRATUM §3.4/§4 withdrew. Same defect class the erratum itself fixed in the six-adopt packet and in the synthesis.
- **F-5 (CRITICAL)** `shortlist/SHORTLIST_6SYM.md` L72 (ES-F1 row, power-honesty cell):
  `court-method MDE not separately computed in baseline — armed n≈91 × tail-split with S2 33.506/side floor; K2 governs`
  — numeric USE of the retired value 33.506 as an MDE floor in a decision-support cell.

Mitigating facts (disclosed, they do not downgrade the classification under this check program): the hits live in a wave-1 lane artifact (generated at HEAD `893db28c`, before the A7 result and the erratum); the file header states fees are `MODELED / UNDER REVIEW … every cost number here remains MODELED`; lanes are append-only by round law; 0 trials / 0 freeze consumption ever occurred; the authority chain (OWNER packet + ERRATUM + CYCLE_PROPOSAL + REPORT_VI) is fully corrected and retires the values program-wide; the round's wave-3 VERIFY (VERIFY_REPORT D1) spot-checked shortlist dims/ranks/schedulability only, not cost cells, and predates the erratum. Proven pre-existing: `git diff 4531c5f5 05e54939 --stat` shows exactly 6 files changed (REPORT_VI.md, cal_close/ERRATUM_F1.md, synth/COST_FREEZE_ERRATUM.md, synth/CYCLE_PROPOSAL.md, synth/OWNER_DECISION_PACKET.md, verify/followup/VERIFY_FOLLOWUP_REPORT.md) — shortlist/ untouched, so this is NOT a regression of the fix commit; it is residue the whole-tree C2 grep was designed to surface and the doc-scoped prior verification could not see.

### (c) Silent-default language — every hit classified; **all allowed or historical**

- `synth/COST_FREEZE_ERRATUM.md` L5, L71 — withdrawal narrative (§3.4 answers and withdraws). ALLOWED.
- `verify/VERIFY_REPORT.md` L43 — wave-3 record quoting the THEN-state of OD-2 ("A (default if silent)") — historical audit record, pre-erratum, not an operating rule. ALLOWED (NOTE N-5).
- `verify/followup/VERIFY_FOLLOWUP_REPORT.md` L86, L92, L148, L149, L158 — prior verifier quoting the defects it found. ALLOWED.
- Zero live `(or default)` / `default if silent` / `mặc định A nếu im lặng` / `default A` in synth/OWNER_DECISION_PACKET.md or synth/CYCLE_PROPOSAL.md at this HEAD.

### (d) Three-signature phrasing — every hit classified; **all allowed or historical**

- `chỉ còn 3 chữ ký`: 0 hits anywhere at HEAD (only the prior verifier's quotes).
- `only registration + A7 + GO` / `registration + prelaunch A7 + typed GO only` (English patterns): 0 hits.
- `synth/COST_FREEZE_ERRATUM.md` L86 — `The earlier "chỉ còn registration + A7 + GO" phrasing is withdrawn` — explicit withdrawal. ALLOWED.
- `REPORT_VI.md` L72 — `rút lại câu "chỉ còn registration+A7+GO"` — explicit withdrawal. ALLOWED.
- NOTE (folded into F-6): `shortlist/SHORTLIST_6SYM.md` L71 (C7 cell) and `shortlist/shortlist_6sym.json` L58 + PB1 `blockers` array enumerate `needs registration + prelaunch A7 + typed GO` (and `["registration at ROOT", "prelaunch A7…", "typed owner GO", "D2 fee A7 prior…"]`) WITHOUT the now-REQUIRED D3 signature — the withdrawn three-signature enumeration, unstale-labelled. Same artifact family as F-4.

## C3 — Both variant arithmetics — **PASS (0 mismatches, every printed cell)**

Independent Decimal recomputation (this verifier): comm 0.85; exchange 1.38; spread 6.25; slip {12.50, 25.00, 37.50}.

| Quantity | Recomputed | ERRATUM §2 (L45–54) | OD-2 table (ODP L32–35) | A7 §8 (L161–172) | Match |
|---|---|---|---|---|---|
| A fee/side (reg 0.02) | 0.85+1.38+0.02 = **2.25** | 2.25 | 2.25 | 2.25 | YES ×3 |
| A all-in S1/S2/S3 | **21.00 / 33.50 / 46.00** | same | same (window: = B's row) | same | YES ×3 |
| A RT | **42.00 / 67.00 / 92.00** | same | same | same | YES ×3 |
| B fee/side (reg 0.01) | **2.24** | 2.24 | 2.24 | 2.24 | YES ×3 |
| B all-in | **20.99 / 33.49 / 45.99** | same | same | same | YES ×3 |
| B RT | **41.98 / 66.98 / 91.98** | same | same | same | YES ×3 |
| NQ all-in A (0.85+1.38+0.02+6.25+{15,20,25}) | **23.50 / 28.50 / 33.50** | same | (n/a) | same | YES ×2 |
| NQ all-in B | **23.49 / 28.49 / 33.49** | same | (n/a) | same | YES ×2 |
| Stale SPEC print (1.386 + 0.02) | **21.006 / 33.506 / 46.006** (RT 42.012/67.012/92.012) | 21.006/33.506/46.006 (stale row, NEVER consumable) | stale row | same + stale RT | YES |
| Delta A−B | **$0.01/side = $0.02/RT** | +$0.01/side = +$0.02/RT | — | −$0.01/side = −$0.02/RT (B-relative sign; NOTE N-2 of prior ledger stands) | YES |
| Window rule | A in 2014-10-01→2017-12-31 ⇒ reg 0.01 ⇒ **= B's row** (20.99/33.49/45.99) | ERRATUM L53–54 window note | "(window: = B's row)" | "both bases agree at 0.01 inside the window" | YES |

Every cell printed in both documents matches the recomputation exactly. The three documents agree cell-for-cell (reg rows, fee rows, ES all-ins, RTs, NQ rows, stale-print row; N-2 sign-convention and N-3 stale-RT-omission notes carry over unchanged from the prior ledger).

## C4 — Frozen documents zero-diff + byte pins — **PASS**

| Check | Command | Result |
|---|---|---|
| Frozen dirs zero-diff | `git diff 4531c5f5 05e54939 -- research/control/FUTURES-ES-V1-PACKET/ research/control/FUTURES-SIX-ADOPT-PREP-20261004/ research/control/FUTURES-OVERNIGHT-PREP-20261003/` | **EMPTY output, exit 0** — zero diff, quoted here as the empty string between the command and `EXIT=0` |
| SPEC_PB1_ES.md re-hash | `shasum -a 256 research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` | `445f749906481f33080185cab1628e6365ef2f6db3b9c4f9f0847646eb6b7073` — EXACT match to the recorded pin (byte-frozen) |
| Fix-wave scope | `git diff 4531c5f5 05e54939 --stat` | 6 files, all in-round: REPORT_VI.md (+35−x), cal_close/ERRATUM_F1.md (+23 new), synth/COST_FREEZE_ERRATUM.md (+92 new), synth/CYCLE_PROPOSAL.md, synth/OWNER_DECISION_PACKET.md, verify/followup/VERIFY_FOLLOWUP_REPORT.md (+163 new) |

Fee-input evidence chain — 5 of 21 spot-checked against A7_EXECUTION_PACKET §2 (research/control/FUTURES-SIX-ADOPT-PREP-20261004/fee_es/A7_EXECUTION_PACKET.md L52–90); all 5 **MATCH** at this HEAD:

| File | Recorded sha256 (packet §2) | This verifier re-hash | Verdict |
|---|---|---|---|
| source/archive_CME.php.html | `0f726c52ce90a2e159b376ef40e11e78afd8d279bceb263719038d4c3a3b9e85` | identical | MATCH |
| source/CME.php.txt | `75a8647065d1590e06db7b1244f72a759b09ec672f8eb2072fd09343a5978565` | identical | MATCH |
| source/fees_corrected.json | `7cd65f253f51ed0bc8fad25dc939797fb4e874ce1d975269f98affa128a2aca8` | identical | MATCH |
| impact/GATE_REVIEW_NOTE.md | `5d50ac79c9bca82c696caa7315cbc9c81bcdd4e9a2c09745c6a713efd11161d0` | identical | MATCH |
| verify/p0_verdict.json | `f1e5b6363af9271be931477d3b6e9197ba57b779c469a0c0dadbc6138c60d347` | identical | MATCH |

(The 21 inputs = 16 under `fees_erratum/source/` + 3 under `impact/` + 2 under `verify/`, per packet §2.)

## C5 — Status law consistency at this HEAD — **PASS**

| Requirement | Evidence at 05e54939 |
|---|---|
| CYCLE-1 = BLOCKED_COST_FREEZE in CYCLE_PROPOSAL (≥2 sites) | L38 (`STATUS: **BLOCKED_COST_FREEZE** pending the owner's D3/e.4 basis ruling`), L47–48 (gate 1: `CYCLE-1 freeze is BLOCKED_COST_FREEZE without it`), L105–106 (`BLOCKED_COST_FREEZE until signed`) — 3 sites |
| …and in REPORT_VI status table | L11 (one-line summary) + L82 (status-table ES row: `BLOCKED_COST_FREEZE: chữ ký D3 cơ sở phí` with corrected A/B numbers) |
| OD-2 REQUIRED/EXPLICIT, silent default WITHDRAWN | OWNER_DECISION_PACKET L26 (`REQUIRED, EXPLICIT, before CYCLE-1 freeze`); L40–43 (`default is WITHDRAWED as an operating rule … explicit signature instead (fail-closed). **CYCLE-1 is BLOCKED_COST_FREEZE until this lands.**`); CYCLE_PROPOSAL L47–50 (withdrawal + lawful-silent-reading-only note) |
| Minimal decision sentence leads with D3 | ODP L87–89: `"D3 basis = [A|B] (A: 2.25/side, 21.00/33.50/46.00 · B: 2.24/side, 20.99/33.49/45.99). Chọn CYCLE-1 …"` — all six numbers exact per C3; L91–92 ties CYCLE-1 unblock to the D3 half |
| No text claims any owner signed anything; D3 empty; no GO exists | ODP L3 (`NOTHING HERE IS RATIFIED BY THIS THREAD`), L94 (`Slots empty; nothing self-ratified`), decision sentence is an unfilled `[A|B]` template; GO phrase template-only L79 + `Early/paraphrased GO = intent only, dies unconsumed` L81; CYCLE_PROPOSAL L7 (`It is NOT a typed GO … 0 scored runs`), L101 (`Scored trials actually run: 0`); REPORT_VI L13–14 (`Số trial scored thực tế đã chạy: 0`), L56–57 (no registration, no GO). Positive-form ratification grep over synth/+REPORT_VI: only ODP L15 ("D2 stays open **pending** explicit ratification") — a pending-statement, not a claim. |

## Findings ledger (this check)

| id | severity | finding | citations |
|---|---|---|---|
| F-4 | **CRITICAL** | Retired stale SPEC print (21.006/33.506/46.006) presented as the operative frozen cost — `"per side FROZEN Variant A (SPEC s5), binds until D3"` — with no stale/erratum label, in this round's shortlist deliverables (.md + .json). Use-as-value outside the allowed C2(b) set; the "binds until D3" claim is the binding ERRATUM §3.4/§4 withdrew; contradicts ERRATUM §2 L50 / §1.2–1.3 and OD-2 L37–39. NOT a regression of 05e54939 — byte-identical at 4531c5f5 (6-file fix-wave diff excludes shortlist/); residue the whole-tree grep surfaces for the first time. Mitigations: wave-1 lane artifact at 893db28c, MODELED/UNDER-REVIEW header, append-only lane law, 0 trials/0 consumption, authority chain fully corrected. | shortlist/shortlist_6sym.json L56; shortlist/SHORTLIST_6SYM.md L71 |
| F-5 | **CRITICAL** | Numeric USE of retired value as decision-support floor: `armed n≈91 × tail-split with S2 33.506/side floor` in ES-F1's power-honesty cell. Same provenance/mitigations as F-4. | shortlist/SHORTLIST_6SYM.md L72 |
| F-6 | MINOR | Withdrawn silent-default / three-signature language surviving in the same shortlist artifacts: ESNQ-F5 row `ES S1/S2/S3 per §8 (20.99/33.49/45.99 composition) with SPEC §5 frozen variant default-binding (delta $0.01/side)` (mixes corrected-B composition with the withdrawn default-binding phrase); PB1 schedulability cells and `blockers` array enumerate `registration + prelaunch A7 + typed GO` without the now-REQUIRED explicit D3 signature. | shortlist/SHORTLIST_6SYM.md L71 (C5+C7 cells), shortlist/shortlist_6sym.json L56–58 |
| N-4 | NOTE | `fee_a7/language_scan.txt` L13 quotes the sibling frozen round's D2 fee row (1.386/0.011/2.247) — A7 scan record of another round's frozen text; no use in this round. | fee_a7/language_scan.txt L13 |
| N-5 | NOTE | `verify/VERIFY_REPORT.md` L43 quotes the pre-erratum OD-2 default ("A (default if silent)") as a historical audit record. | verify/VERIFY_REPORT.md L43 |

C1, C3, C4, C5: clean. C2: clean everywhere except the shortlist residue (F-4/F-5/F-6).

## Verdict

**VERDICT: FAIL — the three prior defects (F-1/F-2/F-3) are provably FIXED at 05e54939 with zero
regression in the touched documents, the arithmetic is exact in every printed cell, the frozen
documents and fee-evidence chain are byte-intact, and the status law is consistently
BLOCKED_COST_FREEZE with the silent default withdrawn — BUT the whole-tree residue scan finds the
retired stale cost print still standing as "FROZEN Variant A — binds until D3" (plus a numeric
33.506/side floor use and withdrawn default/signature language) in this round's own shortlist
deliverables (F-4/F-5 CRITICAL, F-6 MINOR), unannotated and outside every allowance of check C2.
2 CRITICAL + 1 MINOR unresolved ⇒ FAIL. Nothing was consumed (0 trials, 0 freeze); the owner
packet / erratum / proposal / REPORT_VI chain that later rounds consume as AUTHORITY is itself
clean; the defect sits in the wave-1 shortlist lane artifacts those authorities supersede but
never explicitly name.**

- No handoff JSON is required for this sub-check (per dispatch) — this report + `packet_check.json` are the artifacts.
- Repair nothing; ruling and any erratum extension (e.g., naming the shortlist artifacts in the correction of record) belong to the controller/owner.

— End PACKET_05e54939_CHECK.md (verifier output; audit only).
