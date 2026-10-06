# VERIFY_REPORT — FUTURES-ES-PB1-REGPREP-20261004 (fresh-context independent verifier)

Lane VERIFY, 2026-10-04. Worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
(branch `prep/futures-es-reg-20261004`). HEAD at verifier start (single
rev-parse): `ffed828f73fa19fa0ff4aee3ac1b441909a43940` — identical to the
round base, i.e. the entire round is untracked content under
`research/control/FUTURES-ES-PB1-REGPREP-20261004/`. Audit only; repair
nothing; zero network; zero PnL. Every number below re-measured from bytes,
not copied from lane claims.

## V1 — D3 record fidelity (auth/D3_RECORDED.json)

| check | result | evidence |
|---|---|---|
| (a) decision_quote_verbatim exact | PASS | Field is byte-exact `tôi chọn 2.25$`. Round-wide grep `tôi chọn` finds 6 occurrences (D3_RECORDED ×2 incl. context quote, REPORT_VI ×2, REGISTRATION_READINESS ×1, REGISTRATION_PACKET ×1) — all render the same string; no altered variant anywhere. |
| (b) effective cost table recomputes | PASS | Recomputed from components: 0.85+1.38+0.02 = 2.25; all-in S1/S2/S3 = 2.25+6.25+{12.50,25.00,37.50} = 21.00/33.50/46.00; RT = ×2 = 42.00/67.00/92.00; window fees 2.24 (reg 0.01) ⇒ 20.99/33.49/45.99. All cells recompute exactly. Cross-checked against both pinned sources read directly: COST_FREEZE_ERRATUM §2 Variant-A column and A7_FEE_REAUDIT §8 Variant-A column — identical values incl. NQ 23.50/28.50/33.50 (matches D3 nq_note). |
| (c) no over-claim | PASS | `labels_binding` states VERIFIED_VS_ACCOUNT = NOT_RUN (UNCHANGED, "not inferred"); `does_NOT_do` = not a typed GO / not cycle registration / not S1-order-purchase-push / does not lift D9, PB2, PB3, D8 or any cap / does not make fees VERIFIED_VS_ACCOUNT. Nothing registered. |
| (d) e.1-e.3 sufficiency wording | PASS with MINOR (F-V1) | REGISTRATION_READINESS.md quotes A7_EXECUTION_PACKET §4 verbatim (compared line-by-line against the original at `research/control/FUTURES-SIX-ADOPT-PREP-20261004/fee_es/A7_EXECUTION_PACKET.md` L111-116 — exact). Original scoping: e.1 = FX-group fee mapping (FX); e.3 = NYMEX reg epoch (NYMEX); **e.2 = account-geography basis of the IB-JP paren — neither FX nor NYMEX per se**. D3_RECORDED's own `authority_scope` describes e.2 correctly; only the `sufficiency_conclusion` blanket "e.1-e.3 are FX/NYMEX-scoped" over-scopes e.2. Operative conclusion (non-blocking for ES) is nonetheless sound: COST_FREEZE_ERRATUM §3.3 independently states e.1-e.3 do not block an ES cycle, and under Variant A the IBKR offset 0.011 is consumed nowhere. |

## V2 — No stale-value resurrection (round-wide)

Round .md/.json grep `1\.386|21\.006|33\.506|46\.006`: exactly 3 files hit,
all classification/law/program lines, zero use-as-value:

| file | line | class |
|---|---|---|
| auth/D3_RECORDED.json | 22 | forbidden-values LAW statement (naming them retired/never-consumable) |
| freeze/cost_freeze_check.json | 61 | classification detail (quotes the A7's disclosed false-positive trade price 19801.386) |
| synth/PRELAUNCH_A7_SPEC.md | 16 | forbidden-scan program line (the scan's own pattern) |

Silent-default language scan (`or default` / `default if silent` / `mặc định`,
case-insensitive): **0 hits round-wide**. Worktree-wide the pattern also
appears only in pre-existing committed rounds (K6GATE, OVERNIGHT, DEEPFOUR,
SIX-* — byte-frozen history with their own errata) — untouched by this round.

## V3 — Freeze-audit reproduction (spot-recompute)

| check | result | evidence |
|---|---|---|
| (a) 6 pins re-hashed vs disk | 6/6 MATCH | SPEC_PB1_ES.md `445f7499…7073` (== expected, exact); D3_RECORDED.json `99661246…715d8`; COST_FREEZE_ERRATUM.md `cf83bc2d…8ae8`; A7_FEE_REAUDIT.md `2c1095d6…11ad`; DATA_READINESS_ES.md `1407b1d4…7927`; ES_cache/es_1m_outright.parquet `7ae6de2d…7b95`. All equal freeze_pins.json entries. |
| (b) identity table | PASS | Programmatic count: 24 identities, 24 unique; composition P-A 8 + P-B 8 + FOMC 4 + C1-C4 4 = 24; `provisional_markers_found` = []. Spot-checked vs SPEC_PB1_ES §6 (read directly): C1 row note verbatim (seed 20261002; đơn seed đơn delay — giới hạn công bố, không claim permutation robustness), C2/C3/C4 IDs exact, P-A/P-B/FOMC patterns exact, "A-r4 đúng 24" header matches, D30×{S1,S3} absence law present. MINOR line-ref drift: F-V3. |
| (c) cost_freeze_check 18/18 | PASS | Document `cells_compared=18, matched_all_three_sources=18, mismatched=0`; the 11 arithmetic strings re-derived by this verifier all compute exactly; Variant-A columns of ERRATUM §2 and A7 §8 read directly and agree cell-for-cell (incl. the window note and the reg 0.02→0.01 in-window basis). |

## V4 — Registration packet law-conformance (synth/REGISTRATION_PACKET.md)

| check | result | evidence |
|---|---|---|
| (a) NOT REGISTERED, registers nothing | PASS | Header "PACKED FOR OWNER REGISTRATION. NOT REGISTERED. This packet registers nothing and authorizes nothing."; §3 explicit non-action list. |
| (b) gate order = CYCLE_LAUNCH_DRAFT §6 | PASS | §2 sequence registration → prelaunch A7 (key 1) → exact-arm dry-run → typed GO (key 2) → scored under heavy lock + reproduction twin + terminal A7 — matches CYCLE_LAUNCH_DRAFT §6 steps 1-7 verbatim order (read directly at `research/control/FUTURES-SIX-ADOPT-PREP-20261004/packet/CYCLE_LAUNCH_DRAFT.md` L195-232). |
| (c) F-A5 disposition | PASS | §5 canonical rule: GO phrase = registered id substituted into `GO <REGISTERED-CYCLE-ID> SCORED EXECUTION`; PLAN §6 example marked historical illustration, superseded by reference, PLAN file untouched. Premise verified: PLAN_futures_es_v1 L54 does print `GO FUTURES ES V1 SCORED EXECUTION`; the canonical form matches CYCLE_LAUNCH_DRAFT §7 GO law verbatim. PLAN zero-diff confirmed (V5a). |
| (d) §6 minimal action = registration only | PASS | §6: register at ROOT (or explicitly delegate root session); "Nothing else is missing on the ES path". |
| (e) e-ruling ledger vs V1(d) | PASS (consistent) | §4 ledger: e.4 CLOSED (Variant A); e.1 OPEN blocks FX cost cells; e.2 OPEN blocks geography-sensitive modeling only; e.3 OPEN blocks CL/NG cells. Consistent with the D3 record's authority_scope (which is the precise wording); packet header repeats the blanket FX/NYMEX label (see F-V1) while its ledger is exact. |
| PRELAUNCH_A7_SPEC post-registration-only | PASS | "Runs ONLY after registration." |
| DRYRUN_SPEC quarantine + counters | PASS | "Budget counters UNTOUCHED; output quarantined descriptive-only (zero scored cells consumed; observed denominator NOT incremented)"; heavy-lock law; "lawful ONLY post-registration; until registration exists, this spec is paper." |

## V5 — Non-action proof

| check | result | evidence |
|---|---|---|
| (a) diff scope | PASS | `git status --porcelain` at start: only `?? research/control/FUTURES-ES-PB1-REGPREP-20261004/`. `git diff --stat ffed828f <HEAD>` at end: empty (HEAD == ffed828f). No registry/ledger/plan/other-round/root changes; FUTURES-ES-V1-PACKET byte-untouched. |
| (b) root registry (read-only) | PASS | `/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json`: grep `FUTURES-ES-PB1` → 0 hits (ABSENT); `NBA-WINPROB-PREP-V1` present (write_token + cycle_id row); no FUTURES-ES-V1 either. |
| (c) language scan | PASS | All GO/scored/order/S1 mentions round-wide are law citations, F-A5 reporting, or explicit negations (REPORT_VI: "0 scored, 0 dry-run, 0 PnL, 0 S1/order/mua/push/merge"). No GO typed, no scored run, no S1/order claims. |

## V6 — FREEZE-AUDIT handoff

| check | result | evidence |
|---|---|---|
| parses / schema | PASS | Valid JSON; `schema` = `zcode_orch_v3_handoff@1`. |
| shas | PASS | `dispatch_sha` == `actual_start_sha` == `ffed828f73fa19fa0ff4aee3ac1b441909a43940`, both bare 40-hex; `commit_sha` null. |
| tests[] content | PASS | 4 tests; test 1 records SPEC-pin MATCH (445f7499…7073); test 2 records cost-cell counts (cells_compared=18, matched=18, mismatched=0, labels 3, use-as-value 0) + 24-ID composition + 34-pin re-hash; test 3 the forbidden-values grep; test 4 the panel byte-identity. |
| declared outputs | PASS | All 5 `outputs[]` sha256 re-hashed against disk: 5/5 identical. |

## Findings

| id | severity | finding |
|---|---|---|
| F-V1 | MINOR | Blanket label "e.1-e.3 are FX/NYMEX-scoped" (D3_RECORDED `sufficiency_conclusion`; echoed in REGISTRATION_PACKET header and REGISTRATION_READINESS) over-scopes e.2: per A7_EXECUTION_PACKET §4, e.2 is the account-geography basis of the IB-JP paren — neither FX- nor NYMEX-scoped. The D3 record's own `authority_scope` and the packet's §4 ledger characterize e.2 correctly; non-blocking-for-ES is independently supported (ERRATUM §3.3; IBKR offset unused under Variant A). Wording imprecision only; no operative effect. |
| F-V2 | MINOR | `freeze/cost_freeze_check.json` forbidden_values_scan bookkeeping is internally inconsistent: `total_hits: 17`, but its own `classification_of_hits` sums to 26, the FREEZE-AUDIT handoff test claims "26 raw line-hits", and verifier ground truth (grep -c per file) is 27 lines (D3 1; COST_FREEZE_ERRATUM 11 — the JSON says count 10 while enumerating 11 line numbers; A7 10; SHORTLIST 5). All 27 hits verified line-by-line as erratum-self-reference / glue-classification / disclosed false positive — the "0 use-as-value" conclusion is unaffected; only the counts are wrong. |
| F-V3 | NOTE | `freeze/identity_table_24.json` `source_line_ref` pointers drift +1 for rows after L121 (cited L123/L127/L128-131/L134-135 vs actual SPEC §6 lines 122/126/127-130/133-134; the L121 P-A citation is correct). Quoted content itself verbatim correct. PIT file's own line refs (L76, L80-81, L140-141, L143) verified accurate. |
| F-V4 | NOTE | FREEZE-AUDIT handoff `log_digest` fields reuse output-file digests (test 1 = freeze_pins.json sha `da72dfca…`; tests 2-3 both = cost_freeze_check.json sha `d6b9be83…`) rather than distinct test-log digests. The digests are real file hashes; provenance labeling imprecision only. |
| F-V5 | NOTE | cost_freeze_check `committed_history_note` correctly documents the erratum §2 PROPOSED → effective transition as carried by the D3=A record with zero edits (verified: no committed file modified, V5a). Recorded as a positive observation, no action. |

No CRITICAL findings. No MAJOR findings.

## Round verdict

**PASS — freeze, D3 record and registration packet verified faithful; round
stands GATED_ON_REGISTRATION with registration at ROOT as the single remaining
owner action.** Findings F-V1/F-V2/F-V3 are documentation-hygiene items inside
this round's own files; none affects any frozen value, gate order, authority
boundary, or the non-action proof. Nothing repaired (audit-only lane).

Verifier git log: rev-parse HEAD ×1 at start (`ffed828f…3940`); status
--porcelain at start and end; `git diff --stat ffed828f <HEAD>` at end (empty).

— End VERIFY_REPORT.md.
