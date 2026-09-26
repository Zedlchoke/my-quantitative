# OWNER PACKET — ERP Forex program continuation + ERP1-TRACKA-COHORT-2
Ngày 2026-09-26 · soạn bởi Lead từ owner instruction 2026-09-26 (khảo sát +
lập plan + trình owner; prompt KHÔNG phải GO).

## 1. Snapshot repo/worker/lock/gate (đo 2026-09-26, root checkout)

- Root `main` @ `73ae43e1d04ad6f1f41d3abe1c3a17734da753b3`; tree mang các
  path untracked của owner (`.zcode/`, `plan_at.md`,
  `plans/DRAFT_amendment_PSCTV1_A4_*`, `research/control/DASHBOARD-*`,
  `SANDBOX-OVERFIT-3ASSETS/`, `SHARED-PORTFOLIO-100K-V1/`,
  `d2_curiosity_v1_sources/`, ERP control files 2026-09-25/26) — P0-4: không
  stage, không tidy.
- Heavy lock: **FREE_PROVEN** (không holder; history row cuối = cohort-1
  falsifier-plane FINISHED).
- Registry: `ECONOMIC-ROBUSTNESS-PROGRAM-V1` ACTIVE_LIGHT (umbrella 0/0);
  `ERP1-TRACKA-COHORT-1` **TERMINAL CLOSED_REJECT_ALL** (12/24 cells, 0
  survivors, holdout 2026-H1 hai pair UNREAD); các ACTIVE_LIGHT khác:
  FX-RANGEFADE-2M-SHADOW-V1 (2 workers — daemon sống, KHÔNG đụng),
  PROSPECTIVE-SHADOW-V1 (PSV1; đang chạy engine-fix arc theo owner delegated
  decision 2026-09-26 — restart-wipe incident HIGH đã root-cause, recovery
  bằng ledger replay trước thứ Hai 09-28), LIVE-DATA-GATEWAY-V1,
  ETHUSDT-OPEN-SEARCH-V2 (STOP-1 chờ GO), ILLIQ-LOSS-MECH-V1 (phase-2 chờ
  GO), CRYPTO-HISTORICAL-REPLICATION-3F-V1 (scored đang chạy), SHADOW-PAPER-
  REVIEW-V1 (REVIEW_COMPLETE; O1/O2/O4/O5/O6 mở).
- Cycle doctor: chỉ findings LOW/MEDIUM loại accepted-historical (worktree
  TERMINAL đã archive — P0-3). EURUSD-DATA-QUALIFICATION-V1 vẫn BLOCKED chờ
  owner chọn 1 trong 3 unblock path nguồn.
- Gate đang chờ owner (ngoài chương trình này): P-G1/P-G2/P-G3 (amendment GO
  phrases), EDQ1 source decision, ETHUSDT-V2 GO, ILLIQ phase-2 GO.

## 2. Lesson-to-gate matrix (tóm tắt)

`forex_program/LESSON_TO_GATE_MATRIX.md` — 5 hàng bắt buộc (L1 PIT-seam
RANGEFADE + luật thứ ba của daemon; L2 parity cùng code tái tạo lỗi; L3
PIT-clean chết @×1.5 trong khi lookahead thắng = leak; L4 baseline/beta/
clock-placebo/inverted/measured-cost; L5 outcome-exposure map + sealed map
hai cấp) + 8 hàng hỗ trợ (P-1, P-8, P-12, P-15, P-19, L-FIBV1/L-FXFF-1,
P-25, P-2/Q-12) + bảng outcome-exposure binding. Mỗi hàng: bằng chứng (file/
số liệu cụ thể) → gate phòng ngừa → điều kiện FAIL.

## 3. Artifacts của phiên này (đều UNCOMMITTED — xem §7 hygiene)

1. `plans/PLAN_erp_forex_program_v1.md` — master plan DRAFT (charter tầng
   program dưới umbrella; mục tiêu `BACKTEST_CANDIDATE_REPLICATED` với
   định nghĩa 7 điều kiện R0–R6; loop cohort; điều kiện dừng NO_CANDIDATE).
2. `plans/PLAN_erp1_tracka_cohort_2.md` — child plan DRAFT_FOR_OWNER_GO.
3. `forex_program/LESSON_TO_GATE_MATRIX.md`.
4. `forex_program/plan_review/A7_forex_program_plan_review_REPORT.md` +
   `HANDOFF_a7_forex_plan_review.json` (A7 độc lập, fresh-context).

## 4. A7 plan-review verdict

**`AUTHORIZED_WITH_FINDINGS` — 0 CRITICAL / 3 HIGH / 2 MEDIUM / 5 LOW / 2 INFO.**
Ba HIGH + hai MEDIUM đã được remediate NGAY trong draft (phiên bản hiện tại):

| Finding | Nội dung | Trạng thái remediation |
|---|---|---|
| F1 HIGH | OWNER_PACKET chưa tồn tại (nơi owner decision đáp xuống) | File này (BC-1) |
| F2 HIGH | Packet proposer có thể chứa số PnL R-ORIG (+3207/+5030) — taint blind lanes | Child §3.4 đổi thành **label-only disclosure** (BC-2) |
| F5 HIGH | USDCHF transfer pass "per identity" ⇒ cửa sổ bị nhìn nhiều lần qua các cohort | **Một look cấp chương trình** cho window transfer; sealed map hai cấp (BC-3) |
| F6 MED | Thiếu clause companion-membership single-pass ⇒ có thể đòi pass holdout thứ hai | Child §9.1 restated (BC-4) |
| F8 MED | Matrix L1 scope hẹp hơn child F-2 | Matrix L1 align "mọi signal code mới" (BC-5) |
| BC-6 | Cap 24 cells vô lý với 3×6×1; PBO re-adjudicate | Cap **18**; PBO điều kiện ≥8 config classes (BC-6) |
| BC-7 | GO-1 có thể bị đọc là cho phép download USDCHF | Child §5.2 ghi rõ: cần amendment riêng D2-2 (BC-7) |

**Vòng 2 (owner instruction 2026-09-26, phiên thứ hai — remediate trước delta
review):**

| Mục | Nội dung | Trạng thái |
|---|---|---|
| F-0 law | Skeptic adjudicate C1/C2/C3 + mọi open-call ở cấp **mechanism class TRƯỚC rho/PnL**; "thêm observable" không đủ là cơ chế mới; skeleton/payer/information tests; `VETO_VARIANT_SAME_FAMILY` đóng slot vĩnh viễn, không thay bằng biến thể cùng họ; slot trống hợp lệ hơn lấp yếu | Child plan §8 F-0 + §0 forbidden + §1.1 + §4 |
| PBO unify | Bỏ mâu thuẫn §10.2/§10.3: một luật duy nhất — đếm distinct frozen config classes tại freeze; ≥8 ⇒ PBO bắt buộc; <8 ⇒ `NOT_RUN_FAIL_CLOSED` kèm measured count | Child plan §10.2 + §10.3 |

**A7 DELTA REVIEW (round 2, fresh-context, trên bytes sau sửa): verdict
`PASS_WITH_FINDINGS` — GO-1 READY: YES.** D1 (đóng 3 HIGH + 2 MEDIUM vòng 1):
PASS đủ 5 mục. D2 (F-0 class-veto law): PASS — kiểm adversarial: relabel
không thoát skeleton test (content-based vs signature đóng băng trước);
resubmission bị cấm ba lớp; re-run-until-pass bị chặn bởi artifact
sha/timestamp tiền-rho + đóng slot vĩnh viễn. D3 (PBO unify): PASS. D4
(GO-1 scope + authority hygiene): PASS. D5 (sealed map + exposure): PASS.
D6 (no regression): PASS. Finding mới: 3 LOW (N1 stale "24" ở master — đã
sửa thành 18; N2 thêm câu OWNER_PACKET-không-là-nguồn-packet — đã thêm vào
child §3.4; N3 one-shot F-0 finality — đã thêm vào child §8) + 1 INFO
(advisories vòng 1 giữ nguyên, non-blocking). Cả 3 LOW được Lead áp dụng
đúng nguyên văn A7 chỉ định NGAY SAU delta review, trước commit — được ghi
nhận công khai tại đây và trong commit message; báo cáo delta2 review bytes
TRƯỚC 3 fix này và chính nó là nguồn của 3 fix (không có nội dung mới nào
được thêm). Báo cáo: `plan_review/A7_forex_program_delta2_REPORT.md` +
`HANDOFF_a7_forex_delta2.json`.

LOW/INFO: ghi trong report A7, mang tính advisory — không chặn GO-1.

## 5. Slate cohort-2 (đề xuất — owner chốt)

- **Cơ chế input cho council (freeze tối đa 3; MỌI candidate — kể cả
  C1/C2/C3 — phải qua F-0 mechanism-class adjudication TRƯỚC rho/PnL;
  skeptic có VETO pre-PnL):** C1 PROV-ABSORB (provenance của biên —
  observable session-of-formation); C2 RECLAIM-ABSORB (fade band sweep đóng
  lại trong band; chết ngay tại F-0 nếu class retest/second-probe chết);
  C3 PROBE-DEPLETION GATE (đếm M1 probe cùng biên — microstructure mới);
  + **open-call cơ chế NGOÀI range-edge family — D2-3 DECIDED: CÓ** —
  open-call lấy slot như candidate thường qua cùng chuẩn; slot trống
  (`SLOT_LEFT_EMPTY_NO_QUALIFIED_CANDIDATE`) hợp lệ hơn lấp yếu. Không có
  biến thể nào của RANGEFADE được vào slate (luật cấm rescue + F-0
  skeleton test).
- **Pair**: home = AUDUSD và/hoặc USDCAD (corpora sẵn, không download);
  replication-transfer = USDCHF (outcome-free, cần D2-2 + data gate).
- **Budget**: 18 cells max; falsification F-1..F-7 (+F-PIT mở rộng: panel-
  truncation + future-mutation cho MỌI signal; class adjudication trước rho)
  chạy xong trước PnL đầu tiên; gates G1–G8 + kill laws kế thừa nguyên văn
  cohort-1; power gate ≥236 RT hoặc bootstrap CI; DSR toàn ledger; PBO
  theo điều kiện.
- **Roster subagent** (mù outcome theo ranh giới master §5): A. PIT/data
  auditor (không xem PnL) · B. economic skeptic (VETO pre-PnL) · C.
  cost/execution auditor (BLOCKED khi thiếu nguồn) · D. independent
  reproducer/A7 (outcome-staged) · P-lanes blind proposers · A1 controller.
- **Định nghĩa replication** (mục tiêu chương trình): R0–R6 ở master §4 —
  ba limb replication (impl độc lập / thời gian chưa chọn / bề mặt độc
  lập), thiếu một limb thì cấm viết "replicated".

## 6. Quyết định + GO phrase cần gõ (gate TIẾP THEO)

| # | Quyết định | GO phrase (gõ đúng nguyên văn, tại gate của nó) |
|---|---|---|
| D2-0 | Phê chuẩn charter master plan | **DECIDED 2026-09-26: ĐỒNG Ý hướng master charter** (không cần registry row mới; ghi nhận tại packet này) |
| D2-3 | Open-call cơ chế ngoài range-edge family | **DECIDED 2026-09-26: CÓ** — open-call có cơ hội lấy slot như candidate thường, qua F-0/F-5/control-constructibility; slot trống hợp lệ hơn lấp yếu |
| D2-2 | Amendment USDCHF (replication-transfer + download) | **NOT GRANTED 2026-09-26** — USDCHF giữ ngoài scope; KHÔNG download; chỉ mở lại khi owner gõ amendment phrase riêng |
| D2-1 | **GO đăng ký cohort-2 + council + falsifiers + freeze (rồi DỪNG)** | `GO ERP1 TRACKA COHORT 2 REGISTER AND COUNCIL` ← gate kế tiếp |
| D2-4 | Sau A7 prelaunch PASS — scored dev cells (cap 18) | `GO ERP1 TRACKA COHORT 2 SCORED` |
| D2-5 | CHỈ khi identity qua đủ dev gates: mở sealed OOS + replication MỘT LẦN | `GO ERP1 TRACKA COHORT 2 SEALED OOS AND REPLICATION` |

Prompt 2026-09-26 của owner KHÔNG phải bất kỳ GO nào ở trên; GO gõ trước
gate = intent, chết unconsumed (P-8). Không có identity nào qua dev gates thì
GO-3 không tồn tại.

## 7. Commit hygiene (P-H1 class)

**Owner đã cấp có giới hạn 2026-09-26 (phiên thứ hai): commit hygiene CHỈ với
pathspec cohort-2.** Lead commit đúng các file của cohort-2 (2 plan drafts +
matrix + owner packet + A7 report/handoff các vòng), KHÔNG stage `.zcode/`,
dashboard, shadow, incident file khác, PSCTV1 draft; không push/merge.

## 8. Lời nhắc chuẩn kết luận

Nếu cohort-2 (và các cohort sau) không sinh được identity đạt R0–R6, kết luận
đưa owner là `NO_CANDIDATE`/`BLOCKED_*` kèm cơ chế nào chết vì sao — không hạ
chuẩn, không chạy vô hạn, OOS giữ nguyên làm tài sản. Nếu có identity đạt
R0–R6, báo `BACKTEST_CANDIDATE_REPLICATED` kèm phát ngôn bắt buộc: "ứng viên
backtest đáng tin" — chưa chắc chắn kiếm tiền, chưa được phép shadow/live
thiếu GO riêng.
