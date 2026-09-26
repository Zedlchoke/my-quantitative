# A7 PLAN REVIEW — PWS-PROGRAM-V1 (master plan + caps amendment + owner packet)

**VERDICT: AUTHORIZED_FOR_OWNER_REVIEW** — no blocking (HIGH) findings. 1 MED
and 6 LOW findings below should be fixed (or acknowledged) before the owner
reads the packet; none of them weakens inherited law, pre-consumes an owner
decision, or grants execution authority.

- Auditor: A7 independent plan reviewer (fresh context; read-only toward
  everything except the two artifacts in `plan_review/`).
- Date: 2026-09-26. Measured base: root `main` @
  `a92664cd589008a051d07dc07b773b66777940b5`, heavy lock `FREE_PROVEN`,
  tree dirty with owner paths + untracked drafts (preserved, not staged).
- Files audited in full:
  `plans/PLAN_pws_program_v1.md`,
  `plans/DRAFT_amendment_PWS-PROGRAM-V1_caps_2026-09-26.md`,
  `research/control/PWS-PROGRAM-V1/OWNER_PACKET_program_open_2026-09-26.md`.
- Authority sources read in full: `CLAUDE.md`,
  `plans/PLAN_economic_robustness_program_v1.md`,
  `plans/PLAN_erp_forex_program_v1.md`, `plans/PLAN_srlv_program_v1.md`,
  `research/control/SRLV-PROGRAM-V1/DATACOST_FEASIBILITY_MATRIX.md`,
  `research/control/SRLV-PROGRAM-V1/OUTCOME_EXPOSURE_MAP.md`,
  `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/VIABILITY_cohort3_REPORT.md`,
  `.../OWNER_NOTE_cohort2_lessons_2026-09-26.md`, `plans/CYCLE_REGISTRY.json`
  (parsed), `research/wayfinder/LESSONS.md` (P-27/P-28),
  `research/wayfinder/FAMILY_FAILURES.jsonl` (count + tail),
  `forex_program/OWNER_PACKET_program_status_2026-09-26.md` (R1 probe row).

---

## Findings table

| # | Check | Verdict | Severity | Evidence (path + quote) | Required fix |
|---|---|---|---|---|---|
| A1 | Arithmetic | PASS with gap | **MED** | §4.1 table sums exactly 100: 20+15+15+10 (CX=60) + 10+10+5+5+5+5 (FX=40) = 100; frozen total "≤30" = 3×10 consistent; amendment §3 "≤96 cells ÷ 6 cells/identity = **≤16** … (≤24 nếu mọi identity chạy dạng 4 cells)" — 96/6=16, 96/4=24 correct; plan §4.2 "≥76/100 … KHÔNG BAO GIỜ được score" = 100−24 worst case, consistent. Caps are mutually consistent as ceilings (program cap ≤96 with FX≤48/CX≤48 binds first), BUT the non-additivity is never stated in words: nominal per-pair envelope is 10×18=180 cells (CX 4×18=72 > CX≤48; FX 6×18=108 > FX≤48), and frozen ceiling ≤30 identities × min 4 cells = 120 > 96 cells — per-pair and frozen ceilings cannot all bind simultaneously. Precedent: SRLV §9 has the same lattice (3×18=54 > FX/CX≤48), so this is inherited structure, not a new defect. | Add one sentence to amendment §3 or §5: "Per-pair ceilings (≤18) and the ≤30-frozen ceiling are non-additive; the program cap ≤96 (FX≤48/CX≤48) is the binding constraint; per-pair ceilings allocate, the program cap limits." |
| A2 | Law fidelity | PASS | LOW ×2 | Umbrella §5.2 inherited unchanged: plan §6.2 "Umbrella §5.2 giữ nguyên: một pair-child freeze tối đa 3 identity"; amendment §2.3 "Giữ nguyên được (không cần sửa): ≤3 cơ chế/cohort (umbrella §5.2)". S1 one-look: plan §8 "S1 program-wide `SEALED_UNTOUCHED`; sealed OOS per-identity MỘT LẦN sau GO riêng" = umbrella §5.10. AUDUSD/USDCAD 2026-H1 program-level one-look: "một cửa sổ transfer = MỘT look cấp chương trình (matrix L5)" = OUTCOME_EXPOSURE_MAP §3 + forex charter R5; registry confirms both windows "UNREAD preserved" at ERP1-TRACKA-COHORT-2 close. Q-3 re-clock veto: §1.2 + §7 `ANCESTRY_EXPOSED_RECLK … KHÔNG BAO GIỜ OOS (Q-3)`. No-rescue: §1.2, K-OOS §6.4. PAPER_TIER vocabulary: §7 "PAPER_TIER + SINGLE_SOURCE_PANEL + FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK" = SRLV §7.1.5. P-8: §10 "Prompt 2026-09-26 KHÔNG PHẢI GO nào cả". P-9/P-11: §6.3(1),(2). Amendment §5 correctly scopes the new budget to PWS ("không trừ vào cap 96 của SRLV") with P-9 cross-program totals kept — lawful as a *request* gated at Q2; SRLV §9 cap is SRLV-scoped by its own text. Goal "≥1 pair" (vs SRLV's ≥2) matches the forex charter goal and sibling goals do not bind each other; R0–R6 7/7 still required. LOW-1: §6.3(2) scopes terminal DSR to "TOÀN BỘ trial ledger của PWS" while §4.2/packet justify the program with cross-program ancestor base rates (N=146); N_registry disclosure compensates and this mirrors SRLV §8.4 sibling practice, but one clarifying sentence (ancestor trials counted in, or exclusion declared) would remove ambiguity. LOW-2: §2.1 status list has `DEFERRED` but the 100-ceiling clause exempts `DEFERRED_WITHDRAWN_BY_OWNER` — a status not in the transition list; pin one name. | LOW-1: one sentence fixing the DSR denominator scope vs ancestor trials. LOW-2: unify the withdrawn status name. |
| A3 | Cap discipline | PASS | — | Amendment header: "`DRAFT_FOR_OWNER_DECISION — KHÔNG HIỆU LỰC tới khi owner phê chuẩn`" + §6 "Chưa duyệt ⇒ PWS không đăng ký cycle nào, không freeze, không score". Plan §0: "KHÔNG hiệu lực tới khi owner duyệt amendment (P-8)"; plan authoring note: "không âm thầm dùng prompt này làm quyền vượt cap"; §4 header "đề xuất; hiệu lực theo amendment". Packet Q2 consequence: "Không duyệt ⇒ không cycle nào đăng ký được". No clause treats the 2026-09-26 prompt as authority to exceed current caps before approval. | None. |
| A4 | FX frontier law | PASS | LOW | Plan §5 reopener table R1/R2/R3/R5 (+R4 as non-reopener slate amendment) matches SRLV §6 evidence requirements verbatim-equivalent; "Không pair FX nào được score khi chưa có MỘT reopener … bằng chứng bytes + license + cost authority đo được tại GO-1" and §10 GO-1(FX) "chỉ có hiệu lực khi reopener §5 có bằng chứng bytes" — no FX scoring without reopener bytes anywhere. minTick ≠ all-in preserved: "minTick 0.5 pip … CẤM suy ra executable spread/all-in; two-sided NOT_SUBSCRIBED, commission NOT_RUN ⇒ all-in CHƯA ĐO. Ngưỡng P3-A ≤0.41 pip đã pin không re-derive" — exactly VIABILITY §D (0/12 classes, zero remainder; P3-A not satisfiable without owner action). LOW: §5 header compresses the measurement as "crossing tối thiểu 1.0 pip @k=2.0" — VIABILITY/OWNER_NOTE say crossing p50 1.0 whole-dev / 0.9 last-6m at the **base** book vs threshold ≤0.41 at **×2.0 stress** (and p25 is 0.8, so "tối thiểu" is wrong). The phrasing is inherited verbatim from `forex_program/OWNER_PACKET_program_status_2026-09-26.md` (R1 row), so it is a citation, not a new claim — but the binding artifact should carry the precise numbers. | State the numbers as in VIABILITY: "crossing p50 0.9–1.0 pip tại book cơ bản vs ngưỡng đóng băng ≤0.41 pip tại stress ×2.0". |
| A5 | Crypto law | PASS | — | Every DATACOST §3.2 element present: funding "MEASURED per-settlement path (native, while held; dual book với frozen constant; funding-path stress 24.7% settlements âm … worst −0.30%/8h ≈ 2.5 fee RT)"; fee "5 bps + 1 adverse tick = DECLARED book (từ CHR3F; lên lớp measured chỉ khi validate vs fills)"; spread census "bookTicker/aggTrades … thiếu ⇒ BLOCKED"; "maker-only CẤM tới khi queue-position đo được"; "levered/borrow/liquidation-model BLOCKED ⇒ mọi arm unlevered 1x"; labels `PROXY_NOT_ORDERBOOK`, `SINGLE_VENUE_PANEL`, `FUNDING_PATH_STRESSED`, `FILL_QUALITY_CLASS_<…>`; "15m/1m cùng giai đoạn giá đã outcome-exposed ở 1h = `ANCESTRY_EXPOSED_RECLK` … KHÔNG BAO GIỜ OOS (Q-3)". Inversion-rescue prohibition (LESSON P-28) present twice: §1.2 "inverted out-earn = kill, không phải signal — LESSON P-28" and §6.4 K-CTRL "không được đọc ngược thành signal, LESSON P-28". LESSONS.md P-28 verified (3/4 skeptic-veto pre-PnL; revival mechanism "chết ở dev gates bằng số đo"; "K-CTRL inverted là kill rẻ nhất chương trình"). | None. |
| A6 | Multiple-testing law | PASS | LOW (observation) | §6.3 coherent with P-9/P-11: observed-vs-published split incl. publication-fail; "DSR tại mọi terminal … N_eff = max(số scored trials, số identity đã score, số frozen identity khác nhau đã xem outcome) VÀ phải công khai N_registry (≤ 100) như cỡ không gian tìm kiếm (Harvey–Liu–Zhu)"; "PBO chỉ khi cấu trúc frozen ≥8 configs; else `NOT_RUN` (fail-closed)" = umbrella §5.14; smoke/dry-run "kill-được, không select-được" (P-15); "không có headline PnL nào được dùng để chọn pair/identity/cửa sổ". "100 = ceiling not quota" is binding, not aspirational: §0 "TRẦN KHẢO SÁT … KHÔNG phải chỉ tiêu", §1.2 "cấm dựng biến thể … để lấp số (K-F0 kill)", §2.1 "Trần này là luật chống multiple-testing … không phải target", enforced by §2.3 anti-variant law (≥2 of 3 differences: payer/information/risk; else `VETO_VARIANT_SAME_FAMILY`) + K-F0. Observation (LOW): 40/100 survey ceiling is allocated to FX pairs that are ĐÓNG/BLOCKED today (scoreable FX = 0 per §4.2); this inflates N_registry, which errs **conservative** for DSR, but spends proposer-space headroom — owner may re-weight at Q3. | Optional: note at Q3 that FX survey allocations can be re-weighted without an amendment since they are survey-only. |
| A7 | Pair-order law | PASS | LOW | §3.2: "Thứ tự pair được freeze tại charter approval (trước khi pair đầu tiên được score) — đổi thứ tự = owner amendment"; "Không quá MỘT pair-child đang ở giai đoạn scored tại một thời điểm"; proposal accumulation is outcome-blind; slate change = owner decision (§3.3). Replication cross-pair restricted: §8 "chỉ với identity đã freeze (qua đủ dev gates trên home pair) + evaluation pass duy nhất trên toàn window với identity frozen; đủ cả 3 limb R5 … Thiếu limb ⇒ không viết 'replicated'" = forex charter R5 + SRLV §8.5; transfer window = one program-level look (matrix L5). LOW: §3.2 cites "luật không xâm phạm §5.3" for the ETHUSDT-OPEN-SEARCH-V2 non-collision rule — §5.3 in this plan is the FX reopener table; the intended authority is OUTCOME_EXPOSURE_MAP §2.1 ("SRLV-CX KHÔNG được tiêu GO phrase hay surface S1 của cycle đó"). | Fix the citation to OUTCOME_EXPOSURE_MAP §2.1 (or drop the number). |
| A8 | GO phrases | PASS | — | Exact strings present and unique per child: `GO PWS CX SOLUSDT C1 COUNCIL AND FREEZE` / `GO PWS CX SOLUSDT C1 SCORED EXECUTION` / `GO PWS CX SOLUSDT C1 SEALED OOS AND REPLICATION`, with per-pair patterns `GO PWS CX <PAIR> C1 …` and `GO PWS FX <PAIR> C1 …` (pair token keeps phrases unique per child cycle; PWS prefix cannot collide with SRLV phrases). Charter approval correctly phraseless: "quyết định ghi, không phrase". Prompt declared NOT a GO in all three files (plan §0/§10; amendment header; packet §0/Q5 "GO gõ trước gate = intent chết (P-8)"). A7 prelaunch placement between GO-1→GO-2 and after dev before GO-3 matches forex charter §8. | None. |
| A9 | Owner packet intake | PASS | LOW ×2 | All re-measurable claims verified by command (see tests): registry 72 rows = 62 TERMINAL + 8 ACTIVE_LIGHT + 2 BLOCKED; `updated_at_utc` 2026-09-26T10:11:04Z; SRLV-CX-C1 `TERMINAL` with phase string matching the packet verbatim (two-half close, A7 CONFIRM_REJECT_ALL, FAMILY_FAILURES SRLVCX1-M1-SETTLE-RESOLVE, 6/18 observed, 0 OOS looks, S1 untouched, GO-3 never consumed); ERP1-TRACKA-COHORT-2 `TERMINAL` REJECT_ALL 0/18, holdouts preserved; ETHUSDT-OPEN-SEARCH-V2 `ACTIVE_LIGHT` STOP-1 awaiting owner GO, S1 SEALED; umbrella `ACTIVE_LIGHT`; PWS-PROGRAM-V1 absent from registry; HEAD `a92664cd…` = the SRLV-CX-C1 close commit; heavy lock `FREE_PROVEN`; doctor 46 findings / 14 HIGH all `FROZEN_ARTIFACT_DRIFT` on TERMINAL pause packets (PAUSE_CRYPTO_V17 ×5, PAUSE_FOREX_V8 ×5, V12_CLOSEOUT_VERIFICATION ×4); FAMILY_FAILURES = 136 entries, tail = SRLVCX1-M1-SETTLE-RESOLVE; "3/4 skeptic-veto, 1/1 frozen chết ở dev gates" verified in LESSONS P-28; "R1 probe session-2: minTick 0.5 pip ×5 pair" is verbatim from forex `OWNER_PACKET_program_status` R1 row. Decision table Q1–Q5 complete: each has a no-decision consequence; Q5 defers the first GO phrase to its own gate after A7 prelaunch — no owner decision is pre-consumed. LOW-1: "không finding nào thuộc PWS" is true for defects, but one MEDIUM `MONITORING_MUTATION` finding lists the PWS amendment draft among untracked files (that is the draft itself, expected). LOW-2: "dirty tree toàn owner paths + draft plans" understates the tree — untracked artifacts from other cycles also exist (ERP A1 gate JSON, PSV1 incident file, `SHARED-PORTFOLIO-100K-V1/`, ERP plan_review A7 reports); the operative commitment "giữ nguyên, không stage" is what matters and is correct. | Optionally tighten the two intake sentences; not blocking. |
| A10 | Cross-file consistency | PASS | — | Pair order identical in plan §3.2 and packet Q3 (SOLUSDT → BNBUSDT → BTCUSDT → ETHUSDT; FX locked until reopener); first GO phrase identical (packet Q5 = plan §10); cap options identical (packet Q2 Option A ≤96 recommended vs Option B ≤144/≤192 = amendment §3/§4); scored-identity expectation consistent (plan §4.2 [0,16] = amendment §3 ≤16 = packet §3.3); amendment's quotes of SRLV §9 / umbrella §5.2 / forex §8 verified accurate against the sources; 3-file handoff table (packet §2) matches actual filenames; identity per-track survey totals (CX 60 / FX 40) consistent between §4.1 and packet §3.1. | None. |

**Execution-authority / state-creation sweep: ZERO.** Plan header disclaims
registration, workers, downloads, S1/sealed access, shadow/daemon/dashboard,
orders, GO consumption; packet §0 "KHÔNG PHẢI GO"; amendment §6 gates all
effect on owner approval. `IDENTITY_REGISTRY.jsonl` is created only "tại
charter approval, 0 rows khi mở" and packet §2 repeats it. Re-measured:
`research/control/PWS-PROGRAM-V1/` currently contains ONLY
`OWNER_PACKET_program_open_2026-09-26.md`; PWS-PROGRAM-V1 has no registry
row; no worktree/branch created; no heavy lock taken; shadow workers
(FX-RANGEFADE, PSV1, ILLIQ, gateway) explicitly untouched and heavy-lock
immune (§4.3). Nothing in the three drafts claims execution authority.

## Severity tally

- HIGH (blocking): **0**
- MED: **1** (A1 — non-additive cap lattice never stated in the amendment)
- LOW: **6** (A2 DSR-scope sentence; A2 `DEFERRED` status-name mismatch;
  A4 crossing-number wording; A6 FX survey-headroom observation; A7 dangling
  "§5.3" citation; A9 two intake-precision notes)

## What stays binding

Regardless of the fixes above, the following remain binding exactly as
drafted and are NOT reopened by this review: umbrella §§1–11 (incl. §5.2
≤3 mechanisms/cohort, §5.10 S1 one-shot, §5.14 floors raise-only, §6 ancestry
0.20 bar, §9 vocabulary, §1.3 no-live-readiness); forex charter R0–R6
(7/7 `BACKTEST_CANDIDATE_REPLICATED`), roster §5, cohort loop §6, stops §7,
GO chain §8; SRLV F-0 court, PIT §3 list, cost contract §7, mass-test≠mass-
selection §8, kill rules §10, stops §11; DATACOST §3 fail-closed components
and OUTCOME_EXPOSURE_MAP roles (matrix L5 one-look transfer law; AUDUSD/
USDCAD 2026-H1 SEALED-UNREAD program-level single look; ETHUSDT-OPEN-SEARCH-V2
surface immunity); VIABILITY NO_CANDIDATE 0/12 with R1–R5 as the only
reopeners and P3-A frozen at ≤0.41 pip with no re-derive; LESSON P-27
("adding an observable is not a new mechanism") and P-28 (inverted
out-earn = kill, never signal); P-8 GO-phrase discipline (prompt 2026-09-26
is not a GO); P-9/P-11 denominators; and the amendment's own nullity until
owner approval. The owner still decides Q1–Q5; this audit grants nothing.

---

## Delta re-verify (post-fix)

Re-read in full after Lead's fix round:
`plans/DRAFT_amendment_PWS-PROGRAM-V1_caps_2026-09-26.md`,
`plans/PLAN_pws_program_v1.md`,
`research/control/PWS-PROGRAM-V1/OWNER_PACKET_program_open_2026-09-26.md`.
State re-measured unchanged: registry still 72 rows (62/8/2), no PWS row,
`updated_at_utc` 2026-09-26T10:11:04Z, HEAD still `a92664cd589008a051d07dc
07b773b66777940b5`, heavy lock `FREE_PROVEN` — the fix round created no
state, registered nothing, touched no lock.

**Result: 7/7 findings FIXED. No new defects introduced. Verdict maintained:
AUTHORIZED_FOR_OWNER_REVIEW.**

| Item | Status | Evidence (new text, quoted) |
|---|---|---|
| 1. MED A1 — cap binding order | **FIXED** | Amendment §3 new paragraph: "**Thứ tự ràng buộc khi các trần xung đột (binding order — luật):** các trần KHÔNG cộng dồn. Bao danh nghĩa per-pair là 10×18 = 180 cells (CX 4×18 = 72 > CX ≤ 48; FX 6×18 = 108 > FX ≤ 48) và bao danh nghĩa frozen là ≤30 identity × 4 cells = 120 > 96 — các con số đó KHÔNG BAO GIỜ khả dụng đồng thời. Program cap ≤96 (FX≤48/CX≤48) LUÔN thắng; trần per-pair (≤18) và ≤3 identity/pair chỉ PHÂN BỔ trong program cap, không mở rộng nó … (Cấu trúc bậc thang này kế thừa nguyên vẹn lattice của SRLV §9: 3 cohort × 18 = 54 > 48.)" — all arithmetic re-verified correct. PLAN §4.1 note under table: "Các trần KHÔNG cộng dồn: program cap ≤96 (FX≤48/CX≤48) luôn thắng; trần per-pair ≤18 và ≤3 identity/pair chỉ phân bổ trong program cap (binding order chi tiết trong amendment §3)." — consistent with amendment. |
| 2. LOW A2-1 — DSR denominator scope | **FIXED** | PLAN §6.3(2): "Phạm vi: denominator DSR là trial ledger CỦA PWS; các ancestor trial của program trước (V14 N=146, EURUSD 48, FX-MAJORS 96…) không nằm trong ledger PWS nhưng phải được disclose cùng bảng (cross-program totals P-9) — dùng làm bối cảnh base rate, không cộng vào N_eff của PWS." — exactly the recommended clarification; consistent with amendment A4's N_eff definition. |
| 3. LOW A2-2 — status vocabulary unified | **FIXED** | PLAN §2.1: transitions now "`PROPOSED → F0_KILLED \| FREEZE_ELIGIBLE → FROZEN → SCORED → <verdict> \| DEFERRED \| WITHDRAWN_BY_OWNER`" plus "`DEFERRED` (parked, có thể quay lại) vẫn chiếm chỗ trần; chỉ `WITHDRAWN_BY_OWNER` (owner rút bằng quyết định ghi) là ra khỏi trần"; ceiling clause now "status ≠ `WITHDRAWN_BY_OWNER`". DEFERRED kept inside the ceiling = conservative; consistent with §4.2 "(F0_KILLED/DEFERRED)". |
| 4. LOW A4 — P3-A crossing numbers | **FIXED** | PLAN §5 header now: "crossing p50 0.9–1.0 pip tại book cơ bản, p25 0.8 — mọi cách đọc đều vượt ngưỡng đóng băng ≤0.41 pip yêu cầu tại stress ×2.0" — exactly VIABILITY §D's measured numbers (0.9–1.0 base incl. p25 0.8 vs frozen ≤0.41 @×2.0). Residual note (non-blocking): OWNER_PACKET §3.1 still carries the compressed quote "crossing tối thiểu 1.0 pip @k=2.0 vs ngưỡng 0.41" — that is a verbatim citation of `forex_program/OWNER_PACKET_program_status_2026-09-26.md` (R1 row), and the binding artifact (PLAN §5) now carries the precise numbers, so no further action required. |
| 5. LOW A7 — collision citation | **FIXED** | PLAN §3.2 now: "luật không xâm phạm theo OUTCOME_EXPOSURE_MAP §2.1: PWS không tiêu GO phrase hay surface S1 của cycle đó, không re-stage corpus của nó." — correct target and the non-consumption clause spelled out (faithful generalization of map §2.1's SRLV wording). §4.1 ETH row remains consistent. |
| 6. LOW A9 — intake precision | **FIXED** | OWNER_PACKET §1: "dirty tree gồm owner paths, draft plans và untracked artifacts của các cycle khác (ERP plan_review, SHARED-PORTFOLIO, PSV1 incident…) — tất cả giữ nguyên, không stage" and "không finding nào là defect của PWS (một ghi chú MEDIUM monitoring liệt kê file draft này — mong đợi, vì nó untracked)." — both statements now match the re-measured tree and doctor output exactly. |
| 7. LOW A6 — Q3 survey re-weighting | **FIXED** | OWNER_PACKET Q3 row: "Trần khảo sát identity per pair (survey-only) có thể phân bổ lại tại Q3 mà không cần amendment — chúng không tiêu cells" — correct (survey identities consume no cells; scoreable set unchanged). |

New-defect sweep on the changed passages (A10 re-check): the seven edits are
internally consistent and consistent across files — binding-order paragraph
↔ §4.1 note agree; §6.3(2) scope ↔ amendment A4 N_eff definition agree;
§2.1 status names used consistently (no other file references the old
`DEFERRED_WITHDRAWN_BY_OWNER`); pair order (Q3/§3.2/§4.1), first GO phrase
(Q5/§10) and cap options (Q2/amendment §3/§4) unchanged and still mutually
consistent; packet §2b correctly records the original verdict (0 HIGH /
1 MED / 6 LOW) and the fix list. One wording nit, non-blocking: packet §2b
"Delta-verify của A7 ghi tại mục này khi owner duyệt" reads oddly — the
delta-verify is this section, recorded now, not upon owner approval; the
authoritative record is this report.

**Final verdict (delta): AUTHORIZED_FOR_OWNER_REVIEW — maintained.** 0 HIGH
/ 0 open MED / 0 open LOW (7/7 fixed; 2 non-blocking residual notes: packet
§3.1 verbatim-upstream P3-A quote, §2b phrasing nit). The three drafts are
ready for the owner's Q1–Q5 decisions; nothing in the fix round grants
execution authority or creates state.
