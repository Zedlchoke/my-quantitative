# VERIFY_REPORT — LANE-VERIFY, round FUTURES-5SYM-PRESCORED-20261005

- Auditor: LANE-VERIFY (independent; built none of the audited work)
- Audit anchor: `ac5c4c18dc1ab1253c61f84dc1fa9fc4f7583ed7`
  - `git rev-parse HEAD` = `ac5c4c18dc1ab1253c61f84dc1fa9fc4f7583ed7` (exit 0) — EQUAL, confirmed.
  - `git status --porcelain` = empty (exit 0) — clean, confirmed (re-confirmed clean again after the pytest re-run).
  - Commit chain `ffed828f → b051d61e → 059c0665 → fe250465 → ac5c4c18` confirmed via `git log --oneline ffed828f..ac5c4c18` (exit 0).
- Scope: 7 lanes (intake/ nq/ fx_eb/ fx_ja/ exec/ hypo/ cal_cost/) + synth/, audited from committed bytes (`git show ac5c4c18:<path>`), not lane prose.
- A7 posture: nothing repaired, nothing ratified, no S1/GO/registration, no network, no commits. Writes confined to `verify/` and `dispatch/handoff_VERIFY.json`.

## Overall verdict: **VERIFIED_WITH_NOTES**

The evidence chain of the round holds everywhere I struck it: 74/74 real-digest
`outputs[]` entries re-hash byte-exact against `ac5c4c18`; every arithmetic claim
recomputed reproduces exactly; the NQ 10/10 cache_v3 claim, the 3/3 A7 re-hash
claims, the checksum manifest (17/17 OK) and the pytest suite (42 passed, exit 0)
all reproduce independently at the audit SHA. Zero CRITICAL findings.

**1 MAJOR** must be addressed at controller level BEFORE/AT integration: the
committed `dispatch/handoff_FXJA.json` violates the `zcode_orch_v3_handoff@1`
sha law (finding V-1 below). The FXJA lane's *evidence* itself is intact
(9/9 outputs match, arithmetic reproduces), so this is a handoff-record defect,
not an evidence defect. 4 MINOR, 4 NOTE.

Finding counts: **CRITICAL 0 · MAJOR 1 · MINOR 4 · NOTE 4**.

---

## Per-lane verdicts

| lane | verdict | outputs[] re-hash @ac5c4c18 | key evidence re-verified by auditor |
|---|---|---|---|
| INTAKE | VERIFIED | 6/6 MATCH | schema fields present; dispatch==start (ffed828f); authority matrix 12/28/11 parse restated truthfully |
| NQ | VERIFIED | 8/8 MATCH | cache_v3 re-hash claim confirmed independently: 8 of 10 files re-hashed by auditor, 8/8 sha256+bytes match `adopt/cache_v3_hashes.json`; identity 22/29/36 with 36 unique draft IDs recomputed from `identity_budget_nq.json` |
| FXEB | VERIFIED_WITH_NOTES | 9/9 MATCH (+1 SELF placeholder, V-3) | 6E/6B identity restates sha-pinned committed evidence; per-symbol 22/33/48 recomputed (F×11/leg; CONV-D 44/66/96 = 2 legs); 0/42 + 34/42 declared verbatim |
| FXJA | VERIFIED_WITH_NOTES | 9/9 MATCH (+1 SELF placeholder, V-3; handoff metadata MAJOR, V-1) | RT $67.42 = 2×(2.46+25.00+6.25) and 8.4499 bp of $79,787.50 recomputed EXACT; 6A era $104.92/$54.92 = 2×(2.46+4t+t) at t=$10/$5 recomputed EXACT; era tick values carried in committed evidence |
| EXEC | VERIFIED_WITH_NOTES | 15/15 MATCH (after resolving round-dir-relative paths, V-4) | BUG1/BUG2 fixes present in code (not just claimed); observed≠published counters; DUPLICATE_RETRY idempotency; real-governance + `--allow-real-governance` refusals in code; 6A two-era + 6J direction in contracts+tests; **pytest re-run: `42 passed`, exit 0 at audit SHA** |
| HYPO | VERIFIED | 7/7 MATCH | census 29 rows + 2 diagnostics; per-symbol counts recomputed EXACT (NQ 3/1/0/0/1, 6E 0/3/4/0/0, 6B 0/2/4/0/0, 6J 2/4/0/0/0, 6A 0/0/0/5/0 in PREP/NEEDS/HOLD/PARK/REJECT order); 11 new-candidate adjudications; 0 new families honest-zero |
| CALCOST | VERIFIED_WITH_NOTES | 20/20 MATCH (+1 self entry omitting sha256 key, V-3) | `shasum -a 256 -c SHA256SUMS_calcost.txt`: 17/17 OK exit 0; fetch_log 18 lines (≤40), no URL >2 attempts, tools = {curl, webfetch} only; 3/3 A7 re-hash MATCH claims reproduced by auditor |
| synth | VERIFIED | n/a (packet; verified for consistency) | 6/6 namespace mappings verified incl. BOTH collision sets (P5-OD1/OD6→P5-FXEB-OD1/OD6; P5-OD-1/P5-OD-4→P5-HYPO-OD1/OD4) + P5-D1 + P5-NQ2/NQ6 + P5-CALC-*; shortlist leaders match draft (NQ-F1/F2 11; FX-F3/F1/F2 12; JF3 12; AF3 12); WORK_QUEUE residuals match CAL_COST_REPORT; REPORT_VI claims verified (34/42, 0/42, 20 refusal codes, 42/42) |

---

## Findings

### V-1 · MAJOR — handoff_FXJA.json violates the zcode_orch_v3_handoff@1 sha law
- `dispatch_sha` = `f9e7b400dfec5c064494a16c7bec0494b08545caa4a95b4e84736174d999ca7a` — a **64-hex digest, not a 40-hex git SHA**, and **≠ `actual_start_sha`** (`ffed828f73fa19fa0ff4aee3ac1b441909a43940`). Schema law (structured-handoff skill): "both 40-hex; must be EQUAL or the handoff is INVALID, full stop". No explanatory field is present in the file.
- Corroboration: the CALCOST completion pass (`handoff_CALCOST.json` incidents[]) found its **own stale draft carrying the same `f9e7b400...` value** plus "non-conforming task_id/role" and **replaced it**; the FXJA committed handoff shows the same stale-draft pattern (task_id `FXJA`, role `LANE-FXJA (...)` vs peers' `FUTURES-5SYM-PRESCORED-20261005/<LANE>` + `lane`).
- Impact: handoff-record validity only. All 9 real-digest FXJA outputs re-hash byte-exact at ac5c4c18 and the lane's arithmetic reproduces; no evidence is corrupted. Controller must re-issue/correct the FXJA handoff record (the committed lane files stay byte-untouched per append-only law).
- Evidence: `git show ac5c4c18:research/control/FUTURES-5SYM-PRESCORED-20261005/dispatch/handoff_FXJA.json` (exit 0), jq key dump; compare `handoff_CALCOST.json` incidents[].

### V-2 · MINOR — tests[] fields non-conformant across all 7 handoffs
Schema requires `tests[]: {command, exit_code, verdict PASS|FAIL|NOT_RUN, log_digest}`. Observed: INTAKE/NQ/EXEC put narrative strings in `verdict` (e.g. `"PASS - 10/10 sha256+bytes match..."` — informative but not the enum); FXEB tests lack `verdict`+`log_digest`; FXJA tests lack `exit_code`+`verdict`+`log_digest`; HYPO and CALCOST tests lack `verdict`+`log_digest`. The underlying commands/exit codes are present in prose or sibling fields; the auditor re-ran the decisive ones (pytest 42/42 exit 0; shasum -c 17/17 exit 0; git checks exit 0), so no evidence is missing — the canonical fields are. Controller-side normalization suggested.

### V-3 · MINOR — non-digest / missing `sha256` in outputs[] self-entries (3 handoffs)
- FXEB: `"sha256": "SELF (written last; hash recorded by controller at wave commit)"`.
- FXJA: `"sha256": "SELF (computed post-write by controller if needed)"`.
- CALCOST: self entry omits `sha256` entirely (uses `kind`/`note`).
All three are **disclosed** placeholders, and none was ever stamped by the controller. Clean alternative for future rounds: omit the self-entry from `outputs[]` and state the self-hash limitation in `known_limitations` (as this report's own handoff does).

### V-4 · MINOR — EXEC outputs[] paths are round-dir-relative
EXEC records `exec/...` while every other lane records repo-relative `research/control/...`. All 15 resolve under the round-dir prefix and all 15 hash MATCH at ac5c4c18 (`hash_binding_rerun.py`, second pass), so the binding holds — the defect is ambiguity of the path convention only.

### V-5 · MINOR — EXEC and CALCOST `dispatch_sha` ≠ `actual_start_sha` (disclosed)
EXEC: ffed828f vs b051d61e, with `actual_start_sha_note` (HEAD advanced by CONTROLLER wave checkpoints; lane made zero commits). CALCOST: ffed828f vs 059c0665, with incidents[] documenting the inherited agent death + completion pass. Cause is controller-made commits of other lanes' work, not tree drift of lane inputs; disclosed. Strictly the schema equality rule is tripped; graded MINOR because disclosed and benign (contrast V-1, undisclosed + malformed).

### V-6 · NOTE — `commit_sha` is null in all 7 handoffs
Consistent with the lanes-never-commit law; controller stamps at integration; none stamped. Same treatment suggested as V-3.

### V-7 · NOTE — census row schema varies by row type
All 29 rows carry `id/family/symbol/class/d_total/status/gates/ancestry/source_doc` (+ shared mechanism fields), but only 8/29 carry the literal `ids_minimal_conv_b`/`ids_full_grid`/`k6` keys; FX rows use `ids_conv_d`/`ids_native_conv_c`, overlays use `ids_standalone`, dead/diagnostic rows use `dead_at_gate`/`missing_evidence`. Every row carries an explicit falsifiability/deadness marker (checked: none lacking), and the md consumes the variants consistently. Information-complete; key-uniformity claim would be false if made literally (none found claiming it).

### V-8 · NOTE — synth compression drops two inline disclosures (both present upstream in-packet)
`synth/SHORTLIST_5SYM.md` states JF3=12 and AF3=12 without the draft's inline "(FXJA stricter 11 disclosed)" parenthetical — but line 1 declares the file a "controller synthesis over hypo/SHORTLIST_DRAFT.md", where the disclosure lives (also in CENSUS_5SYM/ANCESTRY_CHECK). The 6B row's "MDE 4.2bp" power note is FX-F1's census MDE (SPEC_6B.md L166) placed next to FX-F3/FX-F2 leaders; it is a leg-level honesty note, numerically correct, attribution compressed.

### V-9 · NOTE — untracked cache directories in working dir
`.pytest_cache/`, `exec/.pytest_cache/`, `exec/__pycache__/`, `exec/test_runner_v2/__pycache__/` exist in the working dir but are NOT tracked at ac5c4c18 (`git ls-tree` exit 1 for those paths) and are git-ignored; produced by test runs (lane's and auditor's). Not round artifacts.

---

## Checklist evidence (items 1–9)

### 1) HASH BINDINGS
Method: for each of the 7 handoffs, parsed from `git show ac5c4c18:<path>`; checked the 16 required schema fields (all present, 7/7); `dispatch_sha` vs `actual_start_sha` (see V-1/V-5); `tests[]` structure (V-2); then re-sha256'd EVERY `outputs[]` entry against `git show ac5c4c18:<path>` via hashlib (script: `verify/hash_binding_rerun.py`, exit 0).
- Totals: **74/74 real-digest entries MATCH, 0 real mismatches** (INTAKE 6/6, NQ 8/8, FXEB 9/9, FXJA 9/9, EXEC 15/15 under round-dir prefix, HYPO 7/7, CALCOST 20/20). 3 non-digest SELF placeholders (V-3). `commit_sha` null in all 7 (V-6).

### 2) DATA/EVIDENCE SPOT-RECOMPUTES (all from committed bytes / disk bytes)
- (a) NQ cache_v3: auditor re-hashed 8 of the 10 manifest files from disk (`shasum -a 256`, incl. both large parquets): **8/8 sha256+bytes match** `adopt/cache_v3_hashes.json` exactly. The lane's 10/10 claim stands on the auditor's 8/10 sample.
- (b) 6J: 2×(2.46+25.00+6.25) = **67.42 EXACT**; 67.42/79787.50 = **8.4499 bp EXACT**; notional 79,787.50 = 12.5M × 0.006383 cited to sha-pinned `6j_orientation_recheck.json`.
- (c) 6A: era-1 2×(2.46+4×10+10) = **104.92 EXACT** at $10.00/tick; era-2 2×(2.46+4×5+5) = **54.92 EXACT** at $5.00/tick; era ticks carried in committed evidence (`FREEZE_BUILDER_SPEC_6J_6A.md`; `aud_d2_tickera.json` sha cited; boundary 2020-11-20/23).
- (d) 6E/6B: 0.00005×125,000 = $6.25 and 0.0001×62,500 = $6.25 EXACT; both SPEC rows are PASS_BASELINE_RESTATE with sha-pinned citations (DATA_READINESS_6E/6B + machine twin + tick_constancy + K6GATES); 6B carries an explicit DERIVED arithmetic-check row.
- (e) IDENTITY_BUDGET: NQ-A 22 = 11+11, NQ-B 29 = 22+7, NQ-C 36 = 29+7, NQ-D 43 flagged not-signable; 36 listed IDs all unique. FX per-symbol 22 = 2 fam×11, 33 = 3×11, 48 = 33+11+4 RMM; CONV-D 44/66/96 = 2 legs. J-A 29 = 11+11+7 EXACT (JF1+JF3+JF2_host_JF1); J-B 36; J-C 33/40.
- (f) HYPO census: 29 rows + 2 diagnostics; per-symbol status counts recomputed EXACT (see per-lane table); `status_counts_by_symbol` in-file matches recount.

### 3) PIT / CALENDAR / COST
- IMM derivation: `git grep -i IMM/3rd-Wednesday/WEDNESDAY` over the round dir at ac5c4c18 — every substantive hit is a **prohibition statement** ("FORBIDDEN", "never rule-derived", "NO rule derivation used anywhere", hard-refuse at freeze); remaining hits are "immaterial" wording or capture HTML. No date-arithmetic code exists in lane dirs (only cal_cost/fetch_lane.py and the runner; neither derives calendar cells). 6J 2 identity-undetermined cells remain NOT_RUN/flagged, "Not re-derived".
- Fail-closed exclusion tables exist with dates: `nq/CALENDAR_PIT_POLICY_NQ.md` (H1–H5; 2026-04-03 Good Friday class-only EXCLUDE for NQ; MLK 2026-01-19; 2026-07-03; 154-session coverage law), `fx_eb/CALENDAR_PIT_POLICY_6E_6B.md` (per-quarter NOT_OBTAINED tables; 6E 34/42 + 8 aged-out; 6B 0/42 declared verbatim), `fx_ja/CALENDAR_PIT_POLICY_6J_6A.md` (6J 62/68, residual 2023Q1–Q4 + 2 flagged; 6A 66/68; whole-quarter EXCLUDE law).
- `shasum -a 256 -c SHA256SUMS_calcost.txt` → **17/17 OK, exit 0** (captures + reports).
- fetch_log.jsonl: 18 lines (≤40); max attempts per URL = 2 (none exceed); tools = curl(17) + webfetch(1) only.
- A7 re-hash claims (3/3) reproduced by auditor: `A7_FEE_REAUDIT.md` = `2c1095d6…211ad` MATCH; `a7_fee_digest.json` = `fa697c69…982e` MATCH; `a7_validator_report.json` = `a9078769…6722` MATCH.

### 4) STALE-COST + LANGUAGE SCAN (git grep at ac5c4c18, entire round dir)
- `21.006` (13 files), `33.506` (9), `46.006` (9), `1.386` (11): **every hit is a labeled stale/erratum/never-consumable/retired/hard-refuse context** ("stale SPEC print ... NEVER consumable", "1.386 is RETIRED", "retired-value ban ... asserted absent", REFUSED-style runner compat row RC-4.2). **Zero use-as-value.**
- PnL/profitability language: `sharpe` → 1 hit = "sharpest" (false positive); `expectancy >` → 1 hit = pre-registered gate definition (falsifiability criterion, not a claim); `profitable` → all negations/laws ("No profitability inference", "no profitability claim anywhere", "Zero profitability claims anywhere"); `edge` → meta/negative framing only. **Zero positive claims.**
- MODELED/UNDER-REVIEW framing spot-check (3 files): `fx_ja/COST_CONTRACT_6J_6A.md`, `nq/COST_CONTRACT_NQ.md`, `fx_eb/COST_CONTRACT_6E_6B.md` — each carries binding "MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN" on every number (header + per-section labels).

### 5) HYPOTHESIS ANCESTRY / FALSIFIABILITY
`research/wayfinder/FAMILY_FAILURES.jsonl` = 173 lines (matches lane claim "read in full (all 173 rows)").
- Sampled census rows vs the ledger: JF3 ancestry "near-miss row 34 (dead spot Tokyo→London) disclosed in full" → ledger line 34 = FXFV2-A4-P1 "Tokyo-range compression -> London-morning expansion" — REAL; binding stated, JF3 stays PREP_ABLE with the disclosure. FX-F1 "(rows 32/34/35)" → lines 32/34/35 = London-open session continuation / Tokyo-range / London-AM retest-hold — REAL (PB2 ancestry class); "gated-variant closure row 134 binds" → line 134 = TRACKA2 re-gated range-edge fade, VARIANT_SAME_FAMILY — REAL. Additional VOID citations verified real: row 4 (XSECT-VOLSHK-S15), rows 158/160 (DT100 vol-regime/vol-target), rows 132/140 (fix-window / WMR month-end). `ancestry_check.json`: ledger_rows_read=173, zero_re_entry_confirmed=true, reopenings=none; near_miss_register binds exactly "JF3 vs row 34" and "FX-F1 vs rows 32/34/35".
- 11 new-candidate adjudications present in `census_5sym.json` (SAME_MECHANISM / VOID / DATA_BLOCKED / NOT_A_FAMILY), `new_families_proposed: 0` — the honest zero is documented.
- Falsifiable null: every one of the 29 rows carries an explicit falsifiability/deadness marker (gate thresholds, pre-registered kills, dead_at_gate, missing_evidence conditions) — automated scan found none lacking.

### 6) IMPLEMENTATION vs SPEC (exec/)
Code-level verification of `scored_runner_v2.py` (1527 lines) against `RUNNER_SPEC_V2.md` + `FIX_LOG.md`:
- (a) BUG1-class: `finally:` block always attempts `lock.release()` even after exceptions; a raising release sets `RELEASE_RAISED` + `S.fail("FAILED_LOCK_RELEASE")` → `terminal_state()` returns FAILED/EXIT_FAILED non-zero; terminal handoff written only if `core_complete()` (which requires lock_release measured RELEASED); status computed AFTER release from measured evidence. PRESENT IN CODE (L1226–1248, L704–728, L1250).
- (b) BUG2-class: terminal handoff + FINAL_STATUS inside guarded try; handoff/final-status failures append `S.fail`/`finfail` → FAILED non-zero; `EXECUTION_COMPLETE` requires EVERY mandatory step incl. handoff_write (L1294–1299, L1313–1345). PRESENT.
- (c) `observed_count` vs `published_count` separate RunState fields (published starts None); publication failure quarantines with observed rows retained; `DUPLICATE_RETRY` rows never recomputed, observed unchanged (L632–663). PRESENT.
- (d) Sandbox law: `check_real_governance` refuses governance-dir/registry/outputs resolving under the real governance dir or root registry BEFORE any read/write; `--allow-real-governance` hard-refused (`REFUSED_ALLOW_REAL_GOVERNANCE_DISABLED`, "no code path that touches the real governance dir") and never combines with `--test-fault` (L858–872, L1448–1456). PRESENT.
- (e) 6A era + 6J direction: `symbol_contracts.json` carries the only two-era contract (6A: 1e-4/$10.00 from 1900-01-01; 5e-05/$5.00 from 2020-11-23) with entry-bar era law; direction-signed pnl law + 6J-era ticks; tests T17 (6A era switch) + T18 (6J quote direction) in `test_runner_v2/`. PRESENT.
- RE-RUN: `cd …/exec && /Users/hoangminhlong/.venv/bin/python -m pytest test_runner_v2 -q` → **`42 passed in 6.21s`, exit 0** at the audit SHA (log: `verify/pytest_rerun_ac5c4c18.log`). Matches the handoff's "42 passed" claim. No test fails at the audit SHA.
- Contract-number first pass (packet §4A.1): all six contracts' tick/tick_value match the lanes' verified identities (NQ 0.25/$5.00; 6E 5e-05/$6.25; 6B 1e-4/$6.25; 6J 5e-07/$6.25; 6A dual-era as above; ES compat 0.25/$12.50), every row honestly labeled `PLACEHOLDER-PENDING-PER-SYMBOL-LANE` with a verification_law that the runner consumes them as data.

### 7) ISOLATION RE-CHECK
- `/Users/hoangminhlong/.my-quantitative-governance/` contains ONLY `heavy_runtime/` + `mdp_dvc_remote/` (files under heavy_runtime: heavy_worker.lock, scheduler_jobs.json, heavy_worker.history.jsonl). **No `refusal_record.json`, no round artifacts** — the EXEC T16-guard incident's cleanup held.
- `shasum -a 256 plans/CYCLE_REGISTRY.json` = `b292229770b748442f58911da6e7ac8e79a3ef8d9c5b96503bce398efb6a9027`; `grep -c "FUTURES-5SYM"` = **0 (exit 1)** — the round registered NOTHING.
- `find research/control/FUTURES-5SYM-PRESCORED-20261005 -name "*GO_RECORDED*"` → **empty** — no GO artifact anywhere under the round dir.

### 8) SYNTH CONSISTENCY
- Namespace map: 6/6 sampled mappings verified against lane files, including BOTH former collision sets — fx_eb `P5-OD1` (PB2 lift) and `P5-OD6` (reg-basis 2.46 vs 2.47 DERIVED) → P5-FXEB-*; hypo `P5-OD-1` (EXPWITCH disposition) and `P5-OD-4` (JF2 zone-threshold) → P5-HYPO-*; plus fx_ja `P5-D1` (6J ceiling 29/36/33–40 + shadow reading) and nq `P5-NQ2`/`P5-NQ6`, cal_cost `P5-CALC-*`. All match the table's short questions.
- SHORTLIST_5SYM numbers vs SHORTLIST_DRAFT: NQ-F1 11 / NQ-F2 11; 6E FX-F3/F1/F2 12 each; 6B FX-F2 MPC 12 / FX-F3 12; 6J JF3 12, JF1 11; 6A AF3 12-in-PARK; SCORED_LEGAL_NOW = none; 0 new families. All match (see V-8 for the two compression NOTEs).
- WORK_QUEUE residual inventory vs CAL_COST_REPORT: NQ 0/10 (P5-CALC-NQ-HOLPROD); 6J 2 identity-undetermined (P5-CALC-6J-IDENT); 6A 2023Q1/Q2; 6E ECU26/ECZ26 + 8 aged-out; RBA forward Nov/Dec-2026 (P5-CALC-RBA-FWD); ABS/China — all match the calendar policies and CAL_COST_REPORT §5.
- REPORT_VI claims vs lanes: authority 12/28/11 ✓; cache_v3 10/10 ✓ (auditor 8/10 sample); NQ 22/29/36 + 36 IDs ✓; 6E 3.6–6.3bp / 6B 6.3–11.2bp and 34/42 vs 0/42 ✓ (CALENDAR_PIT_POLICY_6E_6B.md L107/L125); 6J $67.42 = 8.4499bp ✓ (recomputed); 6A $10→$5 @2020-11-20/23, 26-ID verbatim ✓; runner 20 refusal codes ✓ (exactly 20 unique `REFUSED_*` literals in the runner) + 42/42 ✓ (re-run); census 29+2 / 0 new / 173 ✓; contract numbers honestly declared PLACEHOLDER awaiting verifier — first pass done above, all match.

### 9) AUTHORITY
- `authority_claims[]`: empty in INTAKE/NQ/EXEC/CALCOST. Non-empty in FXEB/FXJA/HYPO — reviewed line-by-line: every entry is a RESTATEMENT of a standing hold/law (PB2 HOLD stands; PB3 PARK preserved 0 budget; D8/D9 pending "LAW-PENDING, never self-ratified"), a verified-from-committed-evidence statement, or the minting of NEW P5-* owner slots. **Zero self-ratification** of PB2/PB3/D8/D9/D3, ceilings, GO, or registration anywhere.
- Gates restated, not changed: `synth/OWNER_DECISION_PACKET_P5.md` §5 "Standing gates restated (never reopened by this round)" — PB2 HOLD · PB3 PARK · ES cap 24 FROZEN + ES BLOCKED_COST_FREEZE · EXPWITCH dead-at-gate · NQ v2 deprecated · BoJ stamps NOT_IN_CORPUS · no-IMM-derivation · P3 quarantine absolute. §1/§2 pose decisions as owner questions with fail-closed silent defaults; §4B's "minimal unlock sentence" is a signature REQUEST, not a ratification. All new decision IDs are P5-prefixed; prior decisions cited by original IDs only.

## Incidents during this audit
1. None affecting the audit. The pytest re-run created/updated `__pycache__`/`.pytest_cache` under `exec/` (git-ignored, untracked; worktree re-verified clean afterward).
2. The EXEC-hash pass initially reported 15 "not found" because the lane's paths are round-dir-relative (V-4); resolved by prefixing — all 15 MATCH. Recorded as a finding, not an incident.

## What the controller should do with this
- Fix V-1 (re-issue handoff_FXJA.json with a lawful 40-hex `dispatch_sha` == `actual_start_sha`, conforming task_id/role) — lane files untouched.
- Optionally normalize V-2/V-3/V-6 (tests[] fields; stamp or drop SELF entries; stamp commit_sha) at integration time.
- V-4/V-5/V-7/V-8/V-9: record; no action required.
