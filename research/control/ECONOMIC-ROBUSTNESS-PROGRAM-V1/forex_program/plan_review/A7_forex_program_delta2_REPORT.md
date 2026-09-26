# A7 DELTA REVIEW (round 2) — ERP-FOREX-PROGRAM-V1 + ERP1-TRACKA-COHORT-2 + LESSON_TO_GATE_MATRIX + OWNER_PACKET

**Verdict: `PASS_WITH_FINDINGS`** — all six delta items D1..D6 PASS on the
current bytes; 0 new HIGH/MEDIUM; 3 new LOW/INFO findings (N1..N3 below).
Every round-1 HIGH/MEDIUM closure is real, the two owner-mandated laws
(F-0 mechanism-class adjudication, unified PBO count-at-freeze) are correctly
encoded, GO-1 scope hygiene holds, and the tree is clean. Non-blocking
advisories only.

- Auditor: A7 independent delta-review lane, fresh context, READ-ONLY on the
  repo except this report + the companion handoff JSON. No strategy/PnL
  computation, no worker/registry/ledger/S1 touch, no commit.
- Measured HEAD: `git -C /Users/hoangminhlong/my-quantitative rev-parse HEAD`
  → `73ae43e1d04ad6f1f41d3abe1c3a17734da753b3`, branch `main`, 2026-09-26 —
  identical to the round-1 base; the remediation was done entirely in
  working-tree bytes, no commit.
- Bytes under review are **untracked working-tree files** (`git status
  --porcelain=v1` → `??` for `plans/PLAN_erp_forex_program_v1.md`,
  `plans/PLAN_erp1_tracka_cohort_2.md`, and the whole
  `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/` directory,
  which contains the matrix, the OWNER_PACKET, and the round-1 + round-2 A7
  artifacts). Nothing registered, nothing committed.
- Baseline: round-1 report
  `plan_review/A7_forex_program_plan_review_REPORT.md`
  (`AUTHORIZED_WITH_FINDINGS`, F1..F12, BC-1..BC-7) + round-1 handoff
  `HANDOFF_a7_forex_plan_review.json`.

---

## D1 — Round-1 HIGH/MEDIUM closures: **PASS** (all five)

**F1 (dangling ratification path) — CLOSED.**
`research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/
OWNER_PACKET_cohort2_2026-09-26.md` now exists (measured on disk, 9265
bytes). master:9-10 ("Owner phê chuẩn bản charter này bằng quyết định ghi vào
`forex_program/OWNER_PACKET_cohort2_2026-09-26.md`") and child:383 ("(xem
OWNER_PACKET)") both resolve to it. The packet carries what BC-1 demanded:
the A7 verdict + finding-disposition table (packet §4, lines 53-64, one row
per F1/F2/F5/F6/F8/BC-6/BC-7), the D2 decision list (§6, lines 106-113,
D2-0..D2-5), and the not-a-GO statement (§6 lines 115-117 "Prompt 2026-09-26
của owner KHÔNG phải bất kỳ GO nào ở trên; GO gõ trước gate = intent, chết
unconsumed (P-8)"; also header line 3). D2-0 ratifies the charter as a
recorded owner decision, not a scored GO.

**F2 (packet blindness) — CLOSED.**
child §3.4 (lines 119-125) is now LABEL-ONLY law: "proposer packets chứa **§3
ở dạng LABEL-ONLY** (tên cycle + nhãn verdict của ancestry, KHÔNG bất kỳ con
số PnL/PF/fold nào — kể cả các số trong §3.1, vì trong đó có +3207/+5030 pips
của arm lookahead R-ORIG) + §4 candidate text + §5 source table + KHÔNG
PnL/PF/win-rate/trade-count/journal/MAP outcome rows/dashboard. A7 prelaunch
kiểm packet build theo luật này." Unambiguity check: the packet contents are
an exhaustive whitelist (label-only §3 + §4 candidate text + §5 source table)
plus a numeric blackout that applies to the packet as built — so no number
from ANY source (including the OWNER_PACKET, which legitimately carries
+3207/+5030 at packet:59 as an owner document) can legally appear in a
proposer packet, and any that does is caught by the prelaunch byte check
regardless of provenance. Leak-number placement verified by grep:
+3207/+5030 appear only at child:122 (inside the elision rule itself), matrix
L1 evidence column (matrix:17, an audit artifact, not a packet source), and
OWNER_PACKET:59 (owner document). §4 candidate text (child:143-173) and §5
source table (child:177-204) contain zero outcome numbers. Master side
consistent: master:80-81 ("không PnL/PF/winner nào trong packet"), master:146
(blind proposers see "packet phi-outcome"). See N2 for one hardening note.

**F5 (transfer-window shopping) — CLOSED.**
The one-look-at-PROGRAM-level law is present and identical in all three
places: child:319-323 ("Một cửa sổ transfer = MỘT look CẤP CHƯƠNG TRÌNH,
không phải per-identity (A7 review F5 remediation): window USDCHF chỉ được
tiêu MỘT lần bởi MỘT identity trong toàn bộ chương trình; các identity sau
(cùng cohort hoặc cohort khác) không được nhìn nó lần nữa — từ look thứ hai,
mọi pass trên window đã lộ là void theo matrix L5"); master:123-126 ("Một cửa
sổ transfer = MỘT look cấp chương trình... look thứ hai trên cùng window là
void (matrix L5)"); matrix L5 gate + FAIL columns (matrix:21: "sealed map hai
cấp... cửa sổ replication-transfer MỘT look cấp chương trình (A7 review F5) —
A1 giữ sổ, cập nhật mỗi two-half close"; FAIL: "look thứ hai trên cùng window
transfer ⇒ void"). The old per-identity phrasing survives only where it is
immediately subordinated: child:193-194 ("evaluation pass MỘT LẦN ... một
look cấp chương trình — §9.1"). Sealed-map registration of transfer windows
and refresh at two-half close: child:323-325, child:386.

**F6 (companion single-pass) — CLOSED.**
child:310-316: "Companion membership — single pass (kế thừa cohort-1 §9.1
P2-extension, A7 review F6 remediation): mỗi pass holdout của một identity
gồm CHÍNH identity đó + các companion đã preregister (causal control,
inverted control, baseline books) được tính trong CÙNG một pass duy nhất —
companions không bao giờ là consumer độc lập và không được đòi pass thứ hai
cho bất kỳ mục đích nào (kể cả limb 'inverted strictly below anchor' của
R3)." This matches cohort-1 §9.1 P2-extension semantics exactly (same-pass
companions, never independent consumers, R3's OOS inversion limb evaluable
without a second look) and names the R3 motivation explicitly.

**F8 (matrix L1 scope) — CLOSED.**
matrix:17 gate column now reads "**F-PIT battery standing pre-PnL law cho
MỌI signal code mới của chương trình** (lớp lỗi được nhấn tên: mọi biến trạng
thái theo ngày/biên ngày — A7 review F8 align)" — the day-boundary class is
now a named error example, not the gate scope; the FAIL column still binds
any frozen signal ("Bất kỳ divergence >0 trên M-5 của tín hiệu đã freeze...").
This equals the child F-2 scope ("F-2 PIT audit mỗi signal code",
child:270). The binding input can no longer be read narrower than the child
battery.

## D2 — Owner law F-0 mechanism-class adjudication: **PASS**

Encoding (all verified in child bytes):
- **Ordered before F-1 and before all PnL**: child:230 "Thứ tự bắt buộc:
  F-0 → F-1 → F-2..F-7 (child chặt hơn master/umbrella — được phép)"; F-1
  rho runs "chỉ chạy SAU khi F-0 pass" (child:265-266); §8 header scopes the
  battery as the gate "TRƯỚC cell scored đầu tiên" (child:227) with the
  closing ordering law "fail F-* ⇒ NOT_SCORED_FALSIFIED, không mở vòng sửa"
  (child:295-296).
- **Covers C1, C2, C3 AND every open-call, before any rho fixture and before
  any PnL**: child:232-234 "F-0 MECHANISM-CLASS ADJUDICATION (owner law
  2026-09-26; skeptic lane; TRƯỚC mọi rho fixture, TRƯỚC mọi PnL, áp cho
  TOÀN BỘ candidate gồm C1, C2, C3 và mọi open-call)"; C2's header itself
  says "CHỈ SAU F-0" (child:150).
- **"Adding an observable" is NOT sufficient**: three named class tests —
  skeleton test (strip the new observable; if the remainder degenerates to
  the dead family's trigger + direction + exit ⇒ `VETO_VARIANT_SAME_FAMILY`,
  child:243-246), payer test (premium source must differ from break-then-
  revert stop-flow, else VETO, child:246-249), information test (the new
  observable must decide something other than "whether/when to trade under
  the old law"; "chỉ thêm gate lên luật cũ là không đủ", child:250-253).
  Restated in §0 forbidden list (child:52-53: "THÊM OBSERVABLE-GATE lên luật
  chết — 'thêm observable' không đủ là cơ chế mới, F-0 adjudicate") and §1.1
  (child:65-67). §4 intake refuses any freeze without F-0 (child:137-140).
- **VETO closes the slot permanently, no same-family replacement**: child:
  254-256 "VETO tại F-0 đóng slot vĩnh viễn trong cohort: không thay bằng
  biến thể cùng họ; slot chỉ được lấp lại bởi open-call candidate từ family
  KHÁC (owner D2-3)"; mirrored in §0 (child:53-54).
- **Weak hypotheses must not fill slots; empty slot is valid**: child:257-262
  "Slot policy (D2-3 + luật không lấp yếu)... một slot để trống
  (`SLOT_LEFT_EMPTY_NO_QUALIFIED_CANDIDATE`) là kết quả HỢP LỆ và được ưu
  tiên hơn lấp bằng giả thuyết không qua được F-0/F-5/control-
  constructibility. ≤3 cơ chế, fewer allowed"; all-P1/P2-vetoed end state
  `NO_ELIGIBLE_PROPOSAL` (child:139-140); both constants present. Packet §5
  (lines 78-88) restates the same law to the owner.

Adversarial enforceability check (the decisive question: can a motivated
implementer dodge the class veto?):
1. *Relabel to dodge the skeleton test* — cannot: the skeptic must FIRST
   freeze the dead-family signature in the artifact before mapping any
   candidate (child:235-240, signature defined by trigger/direction/exit/
   payer with enumerated ancestry sources: M1 cohort-1 + RANGEEXP/RANGEFADE/
   PDHLOC/FXFV2-A4-P2/displaced-fade), and the skeleton test is content-based
   (strip observable → compare to the frozen signature), so a renamed
   candidate with an identical stripped skeleton fails identically. For
   open-call candidates of other families, F-0 runs "với family signature
   riêng của family đó" (child:258-259), anchored to that family's death
   record; a genuinely new family trivially passes F-0 — which is correct,
   and it still faces F-1 rho vs FAMILY_FAILURES + MAP + cohort-1 shadows
   (child:126-130) and the inherited novelty law (child:168-170).
2. *Same-family variant resubmitted under a new name* — triple-banned: §0
   forbidden ("thay candidate bị F-0 veto bằng biến thể cùng họ"), the
   permanent slot closure (the vetoed family has no slot to re-enter — the
   only refill path is a different-family open-call), and the skeleton/payer
   tests which are name-invariant.
3. *Council re-running F-0 until pass* — deterred by three independent bars:
   the F-0 artifact must carry "shas/timestamps chứng minh nó committed
   TRƯỚC mọi rho fixture" and is a pre-GO-2 condition (child:263-264), so a
   second contradicting artifact against the same frozen signature is
   auditable evidence of tampering at A7 prelaunch; the slot stays closed
   regardless of any re-run verdict; and master:148-150 "Lead tổng hợp bất
   đồng — không bỏ phiếu ghi đè FAIL". A residual loophole is named as N3
   below (no explicit one-shot finality clause) — it does not rise to FAIL
   because a flipped re-run verdict cannot fill any slot and is visible in
   the artifact set.
Verdict: the law is unambiguous, correctly ordered, wired into §0/§1.1/§4/§8
(+ packet §5), and not dodgeable in any path I could construct.

## D3 — PBO law unified: **PASS**

- Child §10.2 (child:362-368) states exactly one law: "PBO — luật
  đếm-at-freeze duy nhất (sửa mâu thuẫn bản trước theo owner 2026-09-26): A1
  đếm distinct frozen config classes THỰC TẾ của slate tại freeze... count
  ≥ 8 ⇒ PBO BẮT BUỘC tính trên đúng tập đó (per-period series persisted,
  P-11); count < 8 ⇒ PBO = `NOT_RUN_FAIL_CLOSED` kèm số đếm measured trong
  ledger. Không có khẳng định tiên nghiệm 'sẽ/không sẽ' đủ ngưỡng."
- Child §10.3 (child:374-377) points at the same single law: "PBO theo luật
  đếm-at-freeze duy nhất ở §10.2 (≥8 distinct frozen config classes ⇒ tính;
  else `NOT_RUN_FAIL_CLOSED` với measured count — hai mục luôn dùng cùng một
  luật, không còn mâu thuẫn)."
- The round-1 pre-judgment ("sẽ không có — 6-arm classes", F11) is gone:
  grep for "sẽ không" across all four files returns no PBO assertion; the
  only "tiên nghiệm" occurrence is the law's own ban (child:368).
- Master:130-131 ("PBO chỉ khi ≥8 configs (else NOT_RUN)") and matrix L13
  (matrix:34, same conditional) are trigger conditions, not count
  pre-judgments; the child law is a strict refinement (adds measured count,
  fail-closed, count-at-freeze procedure). No contradiction master↔child↔§10.2↔§10.3.

## D4 — GO-1 scope and authority hygiene: **PASS**

- GO-1 phrase exact and identical in both documents: `GO ERP1 TRACKA COHORT
  2 REGISTER AND COUNCIL` (child:39, packet:111). Scope: "register, council
  dispatch (đã có slate input §4), data-gate probe nếu cần, PIT/cost audits,
  falsification battery, trial freeze — VÀ DỪNG" (child:40-42) — registration
  + council + falsifiers + freeze AND STOP.
- No USDCHF download anywhere in GO-1 scope: child:190-191 "owner amendment
  riêng chốt slate (D2-2) — GO-1 TỰ NÓ KHÔNG cấp quyền download USDCHF (A7
  review BC-7)". The GO-1 "data-gate probe nếu cần" clause is bounded by §5.2's
  amendment-first law; with D2-2 NOT GRANTED, even a USDCHF probe/download is
  out of scope until a separate owner phrase.
- Packet decision states: D2-2 "**NOT GRANTED 2026-09-26** — USDCHF giữ ngoài
  scope; KHÔNG download; chỉ mở lại khi owner gõ amendment phrase riêng"
  (packet:110); D2-0 "**DECIDED 2026-09-26: ĐỒNG Ý hướng master charter**"
  (packet:108); D2-3 "**DECIDED 2026-09-26: CÓ**" open-call (packet:109).
- Owner messages are not GOs: packet:115-117 + header (packet:3).
- GO-2 phrase unchanged and gated on A7 prelaunch: `GO ERP1 TRACKA COHORT 2
  SCORED` "chỉ sau A7 prelaunch PASS; authorizes dev cells trong cap 18"
  (child:43-44, packet:112). GO-3 phrase unchanged and gated on dev-gate
  survival: `GO ERP1 TRACKA COHORT 2 SEALED OOS AND REPLICATION` "chỉ cho
  identity qua đủ dev gates + R5 freeze... không có identity nào qua thì
  GO-3 không tồn tại" (child:45-48, packet:113). P-8 extinguish law intact
  (master:183-184, packet:115-117).

## D5 — Sealed-map two-tier + exposure labels: **PASS**

- Two-tier law consistent in all three artifacts: child:322-325 ("Sealed map
  của A1 đăng ký cả hai loại cửa sổ (holdout per-identity một lần; transfer
  per-program một lần) và cập nhật tại mỗi two-half close"; A1 keeps the
  ledger, child:309); matrix L5 ("sealed map hai cấp: holdout per-identity
  một look; cửa sổ replication-transfer MỘT look cấp chương trình — A1 giữ
  sổ, cập nhật mỗi two-half close", matrix:21); master R4/R5(iii)
  (master:114-115, 123-126) with two-half-close refresh at child:385-386.
- Exposure labels, cross-checked table↔table↔table:
  - EURUSD/GBPUSD/USDJPY = outcome-exposed, ancestry/fixture/spread-authority
    ONLY: master:68, matrix:40, child:182 ("chỉ ancestry/fixture/cost-
    authority (matrix)"). Consistent.
  - AUDUSD/USDCAD dev 2021-2025 = exposed for range-fade class; dev legal
    only for observables never searched there, D2-adjudicated: master:69
    ("dev cho observable MỚI (D2 adjudicate)"), matrix:41, child:113-117
    ("chỉ hợp pháp khi observable của nó chưa từng được search ở đó (D2 kiểm
    qua registry + trial ledger toàn chương trình)"). Consistent.
  - AUDUSD/USDCAD 2026-H1 = SEALED-UNREAD: master:70 ("**SEALED-UNREAD**"),
    matrix:42 ("**SEALED — UNREAD**"), child:181 + child:304-306 ("UNREAD từ
    cohort-1 — asset của chương trình"). Consistent.
  - USDCHF = outcome-free, transfer surface, amendment-gated, NOT GRANTED:
    master:71, matrix:43 ("sau khi data gate PASS + owner amendment chốt
    slate"), child:189-195 (amendment D2-2 first; "GO-1 TỰ NÓ KHÔNG cấp quyền
    download"), packet:110 (NOT GRANTED). Consistent.
  - Independent sources BLOCKED: master:60-64, matrix:44, child:199-204. Consistent.

## D6 — No regression: **PASS** (one stale cross-reference found → N1)

Regression greps across the four files, all clean:
- Old "cap 24": the child now says "18 scored cells MAX ... A7 review
  F6/BC-6: cap 18, không 24" (child:28-31), §10.2 "18 cells MAX
  (≤3 cơ chế × 6 arms × 1 home pair)" (child:360-361), GO-2 "cap 18"
  (child:44), packet §5 "18 cells max" (packet:91). **Residual**: master:178
  still carries the stale parenthetical "(cohort-2 đề xuất 24 như
  cohort-1)" — see N1. Operative law unaffected (the same line delegates:
  "child tự chốt"; program cap is owner-set per cohort).
- Per-identity transfer language: only the qualified survivals noted in D1-F5
  (child:193 immediately subordinated to the program-level law; master:120-122
  followed by master:123-126). No unqualified "per identity" transfer claim
  remains anywhere.
- "sẽ không có" PBO assertion: gone (verified in D3).
- Packet-blindness leak: leak numbers confined to owner/audit artifacts and
  the elision rule itself (D1-F2); no blind-packet source carries numbers.
- Standing-authority phrasing: "thường trực" appears only inside the P-8
  extinguish law (master:184); GO-1 ends "VÀ DỪNG" (child:42); master §8
  restates "Early-typed GO không bao giờ thành quyền thường trực"
  (master:183-184).
- Tree check: `git status --porcelain=v1` shows ONLY untracked (`??`) paths —
  zero modifications to tracked files. HEAD unchanged at `73ae43e1` (same as
  round-1 dispatch/actual shas). The four files under review and the round-1
  A7 artifacts (`A7_forex_program_plan_review_REPORT.md` 29147 bytes,
  `HANDOFF_a7_forex_plan_review.json`) are present under the untracked
  `forex_program/` tree. Owner untracked paths from the round-1 tree_status
  (`.zcode/`, `plan_at.md`, `plans/DRAFT_amendment_PSCTV1_A4_*`,
  `research/control/DASHBOARD-AND-SHADOW-RELIABILITY-V1/`,
  `SHARED-PORTFOLIO-100K-V1/`, `SANDBOX-OVERFIT-3ASSETS/`,
  `d2_curiosity_v1_sources/`, ERP control files incl. PSV1 incident/delegated-
  decision files and the other lanes' plan_review artifacts) are all still
  present and untouched. No unrelated file was modified by the remediation.

Residual carried advisories (unchanged from round 1, all classified
non-blocking there; NOT new): F3 master non-weakening pin not added (master:
7-8 inherits umbrella law; child:89 "Child chỉ được chặt hơn"); F4 pre-GO-3
A7 check not restated in child §11 (master:181-182 carries it; silence is not
weakening); F7 per-identity no-clean-window close label not added; F9 ±1-bar
H1 fill-delay fixture not added (master:87 keeps Q-4 sub-hour scoping
honestly). These may be taken up at any later byte-touch; they do not gate GO-1.

---

## New findings introduced by the remediation round

- **N1 [LOW] — Stale budget parenthetical in the master creates a
  master↔child number mismatch.** master:178 "Budget scored cells: child tự
  chốt (cohort-2 đề xuất 24 như cohort-1)" while the remediated child and
  packet everywhere say 18 (child:28-31, child:360, child:44, packet:91).
  BC-6 fixed the child but did not propagate to the master's descriptive
  clause. Non-operative (master defers the budget to the child in the same
  sentence; 18 < 24 so no overrun path; the child is the scored authority),
  but it is exactly the cross-document inconsistency class the round-1
  consistency scan certified clean, so it must be corrected at the next
  master byte-touch (one word: 24 → 18) or via a packet erratum note.
- **N2 [LOW] — The §3.4 packet whitelist does not name the OWNER_PACKET (or
  control files generally) as excluded packet sources.** Exclusion currently
  holds by exhaustive whitelist (label-only §3 + §4 + §5, child:119-125)
  plus the blackout applying to packet bytes regardless of source, enforced
  by A7 prelaunch. Since the OWNER_PACKET legitimately contains the leak
  numbers (packet:59), one explicit sentence ("OWNER_PACKET và mọi control
  file khác không phải nguồn packet") would remove the last inferential step
  for a packet builder.
- **N3 [LOW] — F-0 lacks an explicit one-shot finality clause.** Nothing
  literally forbids re-adjudicating the SAME candidate (as opposed to
  submitting a variant). The dodge is closed in effect — the vetoed slot is
  permanently closed (child:254-256), any second contradicting F-0 artifact
  against the same frozen signature is tampering evidence at the pre-GO-2
  A7 audit (child:263-264), and a FAIL cannot be voted away (master:148-150)
  — but the law would be airtight with one line: "một candidate = một F-0
  verdict trong cohort; re-adjudication của cùng candidate bị cấm."
- **N4 [INFO] — Carried advisories F3/F4/F7/F9 from round 1 remain
  unapplied.** As round 1 itself classified them, they are non-blocking and
  were not required of this remediation round; recorded here so the delta
  ledger is explicit about their status.

Finding count this round: 0 HIGH / 0 MEDIUM / 3 LOW / 1 INFO. All round-1
binding conditions BC-1..BC-7 are closed on the current bytes (BC-6's PBO
half and cap-18 half both done; BC-7 encoded at child:190-191 + packet:110).

**GO-1 READY: YES** — no blocking condition remains. Recommended (non-blocking,
next byte-touch): fix N1's stale "24" in the master parenthetical (or log an
erratum in the packet), add the N2 exclusion sentence and the N3 finality
clause to the child. Nothing in this audit authorizes, registers, scores,
downloads, or consumes anything; GO-1 remains a fresh owner-typed phrase at
the child's own gate.
