# A7 CHILD PLAN REVIEW — PWS-CX-BNBUSDT-C1 (draft child plan, pre-GO-1 gate)

**VERDICT: AUTHORIZED_FOR_GO1_GATE** — meaning: when SOLUSDT's A7 terminal +
two-half close is recorded (master §3.2, sprint S2), and the gate's structural
conditions are met (child plan ✓ = the draft audited here; A7 child-plan
review AUTHORIZED_FOR_GO1_GATE ✓ = this verdict; Q3 approved order ✓ =
BNBUSDT is pair #2 after a closed pair #1), the standing delegation
`OWNER_DELEGATED_DECISION_charter_and_go1_2026-09-26.json` covers consumption
of `GO PWS CX BNBUSDT C1 COUNCIL AND FREEZE` (register child + worktree +
Phase C0→C3, then STOP before GO-2), with a GO RECORD citing the delegation.
**0 blocking findings.** 1 MED — a gate-time sequencing precondition already
encoded in the plan text itself (header: "mở sau khi SOLUSDT được A7 terminal
+ two-half close (master §3.2)"), requiring no plan edit: at review time the
SOLUSDT registry row still reads "verdict NO_ELIGIBLE_PROPOSAL pending A7
terminal", so GO-1 BNBUSDT must not be consumed until that close is recorded.
3 LOW prose findings; none loosens any law.

- Auditor: A7 independent plan reviewer (fresh context; read-only toward
  everything except the two artifacts in this directory; audits, never
  repairs, never grants).
- Date: 2026-09-26. Measured base: root `main` @
  `987a4ed5f814a030dd411582794c4aea9ce9e2c3`, branch `main`, tree dirty with
  owner paths + untracked drafts incl. the plan under review (preserved, not
  staged).
- File under audit (read in full): `plans/PLAN_pws_cx_bnbusdt_c1.md`.
- Authority sources read (cited parts in full):
  `plans/PLAN_pws_program_v1.md` (all),
  `plans/PLAN_pws_cx_solusdt_c1.md` (all, precedent child),
  `plans/DRAFT_amendment_PWS-PROGRAM-V1_caps_2026-09-26.md` (all; Option A in
  force per delegation Q2),
  `research/control/PWS-PROGRAM-V1/OWNER_DELEGATED_DECISION_charter_and_go1_2026-09-26.json`
  (all),
  `research/control/PWS-PROGRAM-V1/SPRINT_2026-09-26_evening.md` (all),
  `research/control/SRLV-PROGRAM-V1/DATACOST_FEASIBILITY_MATRIX.md` (BNB/SOL
  rows + 4-pair funding row + §3.2 + §4),
  `research/control/SRLV-PROGRAM-V1/OUTCOME_EXPOSURE_MAP.md` (SOL/BNB rows),
  `research/control/PWS-PROGRAM-V1/plan_review/A7_child_plan_review_REPORT.md`
  (SOL precedent review — format mirror + carried findings),
  `plans/CYCLE_REGISTRY.json` (PWS-CX-SOLUSDT-C1 row, parsed),
  `research/control/PWS-PROGRAM-V1/IDENTITY_REGISTRY.jsonl` (both rows,
  parsed).

---

## Findings table (R1–R8)

| # | Check | Verdict | Severity | Evidence (path + quote) | Required fix |
|---|---|---|---|---|---|
| R1 | Inheritance completeness | **PASS** | LOW ×1 (R1-1) | Header: "Kế thừa nguyên văn: umbrella §§1–11; forex-program §3/§4/§5/§8; SRLV master §§2–11 + child SRLV-CX-C1 §2 (luật crypto); PWS master toàn bộ; child tiền lệ `PLAN_pws_cx_solusdt_c1.md` (C0–C6, freeze fields, cost law). Chỉ chặt hơn." — identical section scope to the A7-audited SOL child header (which expanded the same four forex-program sections as "cấu trúc cohort, R0–R6, roster, chuỗi GO"; the BNB draft drops the parenthetical but cites the same sections — no scope loss). Spot-checked clauses equal-or-stricter on every axis: forbidden data sources + unlevered 1x (§2.1 = SOL §2.1 + matrix §3.2.6–7); exposure classes + ANCESTRY_EXPOSED_DEV labeling + prospective-OOS default + all three collisions plus SOL-worktree append-only (§2.2 = map §2.1); G8 same-by-law with 0.50 floor not lowered (§2.3); cost layering measured/declared with per-pair re-measurement "không kế thừa hằng số SOL/BTC/ETH" (§2.4 = SOL §2.4 tightening); PIT/freeze incorporation "nguyên văn" (§3, §4); terminal vocabulary complete (§5). **LOW (R1-1): funding floor unpinned; Vision cross-check made conditional.** §2.1: "Funding: fapi `/fapi/v1/fundingRate` pagination + Vision cross-check **khi corpus sẵn**" — the DATACOST 4-pair row mandates "funding (fapi + Vision cross-check) … conflict ⇒ symbol-month EXCLUDED" and pins "floor fapi 2020-07-18 (SOL 2020-09-13)"; the BNB draft retains conflict⇒EXCLUDED but states no BNB funding floor and conditions the cross-check on corpus availability. No law is weakened (the general fail-closed law covers an unstaged cross-check as NOT_RUN-class), but the C1 data gate should pin the numbers. | R1-1 (LOW, optional prose): at C1, pin the funding floor (matrix 4-pair row: fapi 2020-07-18) and state that if the Vision funding corpus is not staged, the cross-check is recorded `NOT_RUN` (measured-but-uncrosschecked, disclosed) — fail-closed retained either way. |
| R2 | GO phrases exact | **PASS** | — | Child §0: `GO PWS CX BNBUSDT C1 COUNCIL AND FREEZE` / `GO PWS CX BNBUSDT C1 SCORED EXECUTION` / `GO PWS CX BNBUSDT C1 SEALED OOS AND REPLICATION` — character-exact substitutions of the master §10 pattern (`GO PWS CX SOLUSDT C1 …`), which itself pre-authorizes the substitution: "GO-1/2/3 (CX pair kế) \| như trên, thay tên pair (BNBUSDT, BTCUSDT, ETHUSDT)". Sprint S3 quotes the GO-1 phrase identically. No clause anywhere grants or consumes a phrase early: header "NOT REGISTERED, NOT EXECUTED"; worktree "CHỈ SAU GO-1 được tiêu tại gate"; C3 ends "DỪNG chờ GO-2"; C4 GO-2 conditional; C5 "(GO-3) … ngoài sprint". | None. |
| R3 | BNB specifics vs DATACOST | **PASS** | — | Klines floor "2020-02-10 (DATACOST matrix)" (§2.1) = matrix BNB row "1h 2020-02..2026-08 (floor 2020-02-10)". Exposure class "ELIGIBLE_DEV_BASELINE_EXPOSED (DATACOST)" (§2.2) = matrix BNB verdict, and = OUTCOME_EXPOSURE_MAP BNB row `OUTCOME_EXPOSED_baseline (như SOL)`. Funding fapi pagination + Vision cross-check + "conflict ⇒ symbol-month EXCLUDED (precedent frozen)" (§2.1) = matrix 4-pair row; funding PIT "một settlement chỉ available TẠI `fundingTime`" = SOL child §2.1 verbatim. Spread census required at C1 from bookTicker/aggTrades (§2.1, §3 C1) — matrix BNB C column "như SOL" → "spread census NOT_RUN" today, census mandatory. Forbidden sources (liquidationSnapshot, OI lịch sử, order book L2, maker-fill) + "mọi arm unlevered 1x" = matrix §3.2.6–7. Re-verify-by-bytes at C1 satisfies master §3.3 ("child re-verify bằng bytes tại GO-1 của mình"). The two LOW notes live in R1-1 (funding floor, cross-check conditionality). | None beyond R1-1. |
| R4 | Information-novelty test lawful? | **PASS** | LOW ×1 (R4-1) | §1 requires each proposal to prove (i) information layer/payer/risk-shape khác ≥2/3 trục vs TOÀN BỘ fence đã đo, HOẶC (ii) bằng chứng thông tin mới có authority (R5-class) hoặc cost-regime break có ngày tháng. **Lawful TIGHTENING, not a new law:** derived from master §2.2 F-0 test (3) (information test: "thông tin gì chưa có trong clock/trend/spread"), master §9(a) ("không pair mới khi không có observable/nguồn/giả thuyết payer mới CÓ BẰNG CHỨC"), and the measured SOLUSDT C3 fences — IDENTITY_REGISTRY: `PWS-CX-SOLUSDT-I001` F0_KILLED "VETOED_SAME_FAMILY: ancestry rho 0.353–0.615 vs CARRY 1D/3D/7D/30D level-window proxies + unconditional receiver …; ceiling × power joint EMPTY …; K-CONC 2022=59.1% / FTX 9d=42.2%". The plan's factual premise "SOLUSDT C3 fences là pair-agnostic trong lớp observable giống hệt" matches this evidence. Clause (i) extends the 2-of-3 comparison surface to all measured fences — strictly MORE demanding than master §2.3 (which compares registry proposals only). Clause (ii) is an entry-evidence alternative that bypasses nothing: F-0 court, skeptic VETO pre-PnL, K-ANC/K-COST at C3, and the 2-of-3 anti-variant law between proposals ("anti-variant law" retained in §3 C3) all still apply; R5-class authority / dated cost-regime break are themselves high evidence bars consistent with forex-program R5 and §9(a). Kill path preserved verbatim: "Cùng observables cũ (klines 1h + funding + spread) sinh lại dead family ⇒ F-0 kill / slate rỗng ⇒ đóng `NO_ELIGIBLE_PROPOSAL` với ghi rõ no-new-information (master §9(a) ngôn ngữ), KHÔNG chạy backtest cho chạy" = sprint S4 requirement. **LOW (R4-1): vocabulary alignment** — sprint S4 labels the close `NO_NEW_INFORMATION`; the child closes `NO_ELIGIBLE_PROPOSAL` + explicit no-new-information note (the SOLUSDT registry precedent string); master §11 umbrella term is `NO_CANDIDATE`. | R4-1 (LOW, optional): in the GO RECORD / close artifact, keep one canonical close string (`NO_ELIGIBLE_PROPOSAL` per registry precedent) and map it explicitly to `NO_NEW_INFORMATION` (sprint) and `NO_CANDIDATE` (master §11) so no vocabulary drift is readable as a new terminal class. |
| R5 | Disk-constraint spread census | **PASS** | — | §2.1: "thiếu ⇒ `NOT_RUN_DISK_CONSTRAINT` ghi trung thực, cost gate **fail-closed** (K-COST/BLOCKED cho scoring; không điền số đẹp, không dùng census của pair khác thay thế)" — exactly master §7 ("thiếu ⇒ BLOCKED") + DATACOST §3.2.3 ("NOT_RUN ⇒ BLOCKED, không điền số đẹp") + mission invariant (missing evidence is NOT_RUN, never inferred PASS). Refusing another pair's census is exactly the matrix header law ("không âm thầm thay cặp, không 'tạm dùng' nguồn khác") — a SOL/BTC/ETH census substituted for BNB would be fabricated evidence-class laundering. The ≥25GB pre-stage disk check (sprint budget §; SOL precedent ~12GB/6-month stratified) is an honest feasibility gate — tightening only. §3 C4 correctly makes GO-2 "KHÔNG khả thi nếu spread census `NOT_RUN_DISK_CONSTRAINT`". | None. |
| R6 | Sprint bounds | **PASS** | — | §5: "time-stop sprint 23:30+07 2026-09-26 (chặt hơn luật 14 ngày — được phép, chỉ chặt hơn)" — lawful: inheritance clauses everywhere read "trừ khi child chặt hơn"; a tighter time-stop tightens §9(f), never loosens. §3 C4 GO-2 conditional clause ("chỉ chạy khi đủ điều kiện sprint (slate + A7 prelaunch PASS + ≥45' trước 23:59+07)") = sprint S5 verbatim (slate khác rỗng VÀ A7 prelaunch PASS VÀ ≥45'; thiếu ⇒ freeze-and-park + owner packet); the cost-missing case independently fails closed via R5. §3 C5 "ngoài sprint" + C6 = sprint S6 (GO-3/shadow/orders ngoài sprint; hard wrap 23:30+07). The GO chain is not skipped by the sprint bounds: GO-1 → DỪNG → GO-2 → GO-3 per master §10; GO-3 remains unconsumed and available after the sprint under the same delegation pattern ("ủy quyền tiếp TUYỀN ĐỐI điều kiện cấu trúc tại gate"). | None. |
| R7 | GO-1 authority path | **PASS** | MED ×1 (R7-1, gate-time precondition — no plan edit) | Independent reading: the delegation **DOES cover BNBUSDT GO-1** (full reasoning in the dedicated section below). The plan's assertion matches the sprint S3 conditions (child plan ✓ + A7 AUTHORIZED_FOR_GO1_GATE ✓ + Q3 order ✓ + GO RECORD). **MED (R7-1):** master §3.2 orders pair #2 to start only after pair #1's "A7 terminal + two-half close"; at review time the registry row for `PWS-CX-SOLUSDT-C1` reads "verdict NO_ELIGIBLE_PROPOSAL **pending A7 terminal**" — the close is PENDING. The child plan already encodes the condition (header: "mở sau khi SOLUSDT được A7 terminal + two-half close (master §3.2)"), so this is a gate-time check, not a text defect: GO-1 BNBUSDT must be consumed only after sprint S2 completes and is recorded. | R7-1 (MED, binding at gate, no plan edit): record SOLUSDT A7 terminal + two-half close (sprint S2) in CYCLE_REGISTRY before consuming BNBUSDT GO-1; GO RECORD cites delegation + this authorization + the SOLUSDT terminal evidence path. |
| R8 | Internal consistency | **PASS** | LOW ×1 (R8-1) | Budget closes arithmetically: "≤ 18 scored cells (≤3 identity × 4–6 arms × 1 home pair) + references; baseline set = MỘT arm slot (cash 0% + long BNB + TREND_LF); short-beta control = reference khi cơ chế có chiều" (§0) — carries forward the SOL post-fix accounting (precedent finding B2-1 FIXED), max 3×6=18; consistent with amendment A2/A5 and master §4.1 BNB row (trần khảo sát 15, ≤3 frozen, ≤18 cells); program cap ≤96 (CX≤48) binding in §5. Fold proposal re-based to the BNB floor correctly (F1 2020-02→2021-12 … F4 2025-01→2026-08, "pin trước outcome, chỉnh theo power" — vs SOL F1 2020-09) — pre-outcome pinning intact. G8: "BNB: treated same-by-law" with all three lawful exits (short-capability / pre-outcome replacement statistic sha-pinned / prospective-only) and "Thanh 0.50 không hạ (K-CONC)" = SOL child §2.3 + matrix CX conclusion (iii). Freeze fields §4 = SOL child §4 nguyên văn (named items match). Terminal vocabulary §5 = umbrella §9 + master §11 + all CX labels. No contradiction with master §4/§6 found. **LOW (R8-1):** §2.2/C5 omit the D13/D26/D52(/D104) prospective-gate enumeration the SOL child carries — harmless: umbrella §5.12 is inherited nguyên văn via the header clause; same class as SOL review B4-1. | R8-1 (LOW, optional): write "theo D13/D26/D52 (D104 final per umbrella §5.12)" at §2.2 to make the child self-contained. |

**Execution-authority / state-creation sweep: ZERO.** Header
"`DRAFT_FOR_GO1_GATE — NOT REGISTERED, NOT EXECUTED`"; worktree/branch
creation deferred ("tạo qua researchctl CHỈ SAU GO-1 được tiêu tại gate"); C0
inherits "(sau GO-1)" from the SOL child §3 incorporated by §3's header; C3
ends "DỪNG chờ GO-2" after freeze artifact → A7 prelaunch; "Slate rỗng ⇒ đóng
tại đây"; C5 is the one-look GO-3; collisions all named with their guards
(`ETHUSDT-OPEN-SEARCH-V2` ACTIVE/S1 sealed — no phrase/surface/corpus;
`CRYPTO-HISTORICAL-REPLICATION-3F-V1` heavy lock — dispatch only FREE_PROVEN
or held-by-self; `PROSPECTIVE-SHADOW-V1` + shadow workers untouched; SOL
worktree append-only evidence). No registration, worktree, lane, download,
or scoring before GO-1; no S1 access; no orders; heavy-lock law honored in C4.
Re-measured: no `pws-cx-bnbusdt-c1` worktree or branch exists; no BNBUSDT
rows in IDENTITY_REGISTRY.jsonl; the PWS registry contains only
`PWS-CX-SOLUSDT-C1`.

---

## Independent reading — R7: delegation coverage of BNBUSDT GO-1

The delegation's operative grant and boundary read: "Ủy quyền này bao trùm
**chuỗi GO của PWS-PROGRAM-V1** (bắt đầu GO-1 PWS-CX-SOLUSDT-C1) với điều
kiện gate từng bước như trên; KHÔNG bao gồm: live/shadow promotion, slate
change ngoài thứ tự đã duyệt (trừ stop-condition), mở nguồn/pair mới cần data
authority ngoài DATACOST hiện có, hoặc bất kỳ thay đổi luật/plan đã
A7-audit mà không qua A7 delta mới."

**My independent reading: the delegation covers BNBUSDT GO-1**, conditional
on the per-gate structural conditions. Reasoning:

1. **Grant scope is the program's GO CHAIN, not one child.** "bao trùm chuỗi
   GO của PWS-PROGRAM-V1" is program-level; "(bắt đầu GO-1
   PWS-CX-SOLUSDT-C1)" marks the chain's START, not its end. "với điều kiện
   gate từng bước như trên" presumes a sequence of future gates beyond
   SOLUSDT's three — the same conditional-at-gate pattern the decision item
   applies to SOLUSDT GO-2/GO-3 ("ủy quyền tiếp TUYỀN ĐỐI điều kiện cấu trúc
   tại gate của chúng"). A reading that ends coverage at SOLUSDT would have
   to say "chuỗi GO của PWS-CX-SOLUSDT-C1"; the text does not.
2. **None of the four exclusions fires.** BNBUSDT GO-1 is not live/shadow
   promotion; it is not a slate change ngoài thứ tự — Q3 approved exactly
   "SOLUSDT → BNBUSDT → BTCUSDT → ETHUSDT", so BNBUSDT-as-#2 is INSIDE the
   approved order (the exclusion only removes out-of-order changes); it
   needs no data authority beyond DATACOST — BNBUSDT has its own row
   (Vision um klines 1h floor 2020-02-10; funding fapi + Vision cross-check;
   bookTicker/aggTrades census), verdict `ELIGIBLE_DEV_BASELINE_EXPOSED`,
   all sources already in existing authority; and the "thay đổi luật/plan
   đã A7-audit mà không qua A7 delta mới" exclusion is satisfied because the
   only new plan text (this child plan) is itself passing through A7 review
   (this artifact), while the A7-audited master plan and the owner-approved
   amendment are unchanged.
3. **The approved charter pre-authorizes this exact gate.** Master §10
   (approved under Q1) defines the per-pair pattern: "GO-1/2/3 (CX pair kế)
   | như trên, thay tên pair (BNBUSDT, BTCUSDT, ETHUSDT)". Consuming
   BNBUSDT GO-1 executes the charter; it amends nothing.
4. **The latest explicit owner instruction concurs.** The sprint (received
   ~2026-09-26T13:41Z, highest in the authority order after the delegation)
   directs S3 to consume BNBUSDT GO-1 "theo ủy quyền chuỗi GO hiện hành"
   with the three structural conditions, records the interpretation
   transparently, and preserves the owner fallback: "Nếu owner không đồng ý
   diễn giải này: mọi artifacts còn reversible (child plan DRAFT, registry
   row có thể pause) — decision packet kèm báo cáo cuối."
5. **Guardrails survive untouched.** The delegation's interpretation_binding
   clause ("Mọi kill law / gate / floor / cap không bị thay đổi bởi ủy quyền
   này") is intact: this plan only tightens; GO-1's scope remains
   "register child + worktree + C0→C3 rồi DỪNG"; GO RECORD required; no new
   data authority; no unreviewed law change.

**Binding precondition (the MED, R7-1):** master §3.2 — "Pair tiếp theo chỉ
bắt đầu sau khi pair trước được A7 terminal + two-half close" — is itself
part of the approved order the delegation incorporates. At review time the
SOLUSDT registry row reads "verdict NO_ELIGIBLE_PROPOSAL pending A7
terminal". Therefore GO-1 BNBUSDT is consumable only after sprint S2 records
the SOLUSDT terminal close. GO-1 creates only reversible state (worktree/
branch/control-plane lanes), so no irreversibility attaches to the
interpretation either way.

## Severity tally

- HIGH (blocking): **0**
- MED: **1** (R7-1 — gate-time sequencing precondition: SOLUSDT A7 terminal
  + two-half close must be recorded before GO-1 BNBUSDT is consumed; already
  encoded in the plan text and sprint order; no plan edit required)
- LOW: **3** (R1-1 funding floor + cross-check conditionality note; R4-1
  close-vocabulary alignment; R8-1 D-gate enumeration for
  self-containedness — all optional prose, none loosens any law)

## Gate reading (what AUTHORIZED_FOR_GO1_GATE authorizes)

1. **S2 first:** record SOLUSDT A7 terminal + two-half close in
   CYCLE_REGISTRY (master §3.2 precondition; currently "pending A7
   terminal").
2. **Structural conditions at the gate** (sprint S3 + delegation GO-1
   pattern): child plan ✓ (the draft audited here); A7 child-plan review
   AUTHORIZED_FOR_GO1_GATE ✓ (this verdict); Q3 approved order ✓ (BNBUSDT is
   #2 and pair #1 is closed).
3. **Consume `GO PWS CX BNBUSDT C1 COUNCIL AND FREEZE`** under the standing
   delegation with a GO RECORD citing the delegation + boundary + this
   authorization + the SOLUSDT terminal evidence path. Scope: register child
   + worktree + Phase C0→C3 (control plane, data plane with disk-check,
   exposure verify, council outcome-blind with information-novelty test,
   falsifiers, trial freeze), then STOP before GO-2 — or close
   `NO_ELIGIBLE_PROPOSAL` with the no-new-information note at C3 on an empty
   slate, 0 scored cells. GO-2 only via its own phrase at its own gate under
   the sprint S5 conditions (or freeze-and-park + owner packet); GO-3 only
   at its own gate, outside tonight's sprint.

## Tests run (all read-only)

- `git -C … rev-parse HEAD` → `987a4ed5f814a030dd411582794c4aea9ce9e2c3`;
  `branch --show-current` → `main`; `status --short` → owner paths +
  untracked drafts preserved, none staged.
- CYCLE_REGISTRY.json parsed → `PWS-CX-SOLUSDT-C1`: "GO-1 COMPLETE -> SLATE
  EMPTY … verdict NO_ELIGIBLE_PROPOSAL pending A7 terminal; 0/18 cells, 0
  outcome views, GO-2 UNCONSUMED"; no BNBUSDT row exists.
- IDENTITY_REGISTRY.jsonl parsed → 2 rows, both `PWS-CX-SOLUSDT-I001`
  (PROPOSED 13:02Z → F0_KILLED 13:59Z, VETOED_SAME_FAMILY, rho
  0.353–0.615); no BNBUSDT identity rows.
- OUTCOME_EXPOSURE_MAP grep SOL/BNB → BNB row `OUTCOME_EXPOSED_baseline`
  (như SOL), floor 2020-02-10; funding 4-pair row (fapi + Vision
  cross-check, conflict ⇒ symbol-month EXCLUDED, floor fapi 2020-07-18).
- String-compare GO phrases child §0 vs master §10 (pair-substituted) →
  byte-identical ×3.
- No heavy jobs, no scoring, no sealed-window access, no writes outside the
  two artifacts in this directory.

## Final verdict

**AUTHORIZED_FOR_GO1_GATE** — 0 HIGH, 0 plan-text-blocking findings; 1 MED
gate-time precondition (SOLUSDT terminal close first — encoded in the plan
and sprint already), 3 LOW optional prose notes. The draft is equal-or-
stricter than the audited SOLUSDT precedent on every inherited axis, adds
only tightenings (information-novelty test, disk-constraint fail-closed
census, sprint time-stop), and creates no state before GO-1. Gate reading as
above; GO RECORD must cite the delegation and this review.
