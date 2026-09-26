# OWNER_PACKET — PWS-PROGRAM-V1 — mở chương trình tìm kiếm ≤100 strategy identity theo từng pair & các quyết định chờ owner

- Ngày: 2026-09-26. Người viết: Lead (phiên survey + planning theo owner
  instruction ngày 2026-09-26). Packet này KHÔNG PHẢI GO; không thay thế
  GO-1/GO-2/GO-3; không tiêu phrase nào.

## 0. GO RECORD (hiện trạng)

- **[2026-09-26T11:14:33Z] Owner ủy quyền toàn quyền quyết định** (nguyên
  văn: "bạn hãy đóng vai tôi quyết định theo kết quả mong muốn đỉnh cao
  nhứt. Mọi quyền quyết ở bạn"). Quyết định ghi tại
  `OWNER_DELEGATED_DECISION_charter_and_go1_2026-09-26.json`: Q1 APPROVE,
  Q2 Option A, Q3 giữ đề xuất (SOLUSDT-first), Q4 giữ NO_CANDIDATE, và
  **GO-1 ĐƯỢC TIÊU THỤ tại gate đã dựng** (child plan ✓ + A7 child-plan
  `AUTHORIZED_FOR_GO1_GATE` delta-verified ✓ + Q1/Q2 ghi ✓) — phrase khớp
  nguyên văn intent 10:55Z. Phạm vi: register + Phase C0→C3 rồi DỪNG trước
  GO-2; ranh giới không-ủy-quy (orders/S1-unseal/subscriptions/law-weaken)
  ghi trong artifact.
- **[2026-09-26T10:55:14Z] Owner đã gõ nguyên văn**
  `GO PWS CX SOLUSDT C1 COUNCIL AND FREEZE` (phản hồi trực tiếp sau bàn giao
  #1). **Phân loại theo P-8: EARLY-TYPED INTENT — KHÔNG PHẢI KEY.** Gate của
  GO-1 chưa tồn tại tại thời điểm gõ vì: (1) quyết định Q1 (phê chuẩn
  charter) và Q2 (amendment Option A/B) chưa được ghi vào packet này;
  (2) child plan `PLAN_pws_cx_solusdt_c1.md` chưa tồn tại; (3) A7 plan
  review của child plan chưa chạy/PASS. Phrase đúng nguyên văn, đúng tên
  pair đề xuất — được ghi là **intent sống của owner: mở PWS-CX-SOLUSDT-C1
  làm pair-child đầu tiên** (bao hàm quyết định phần "pair đầu" của Q3);
  early-typed GO không bao giờ thành quyền thường trực (P-8; forex charter
  §8) ⇒ khi gate được dựng xong (Q1+Q2 ghi + child plan A7 PASS), owner gõ
  LẠI đúng phrase tại gate đó thì nó mới được tiêu thụ. Không registries,
  không worktree, không lane nào được mở từ intent này.
- **Không GO nào của PWS khác tồn tại.** Prompt 2026-09-26 của owner được ghi
  nhận là instruction khảo sát + lập plan, KHÔNG phải GO-1/GO-2/GO-3, không
  cho đặt lệnh/sửa shadow/push-merge/mở S1.
- GO record các cycle liên quan gần nhất (đối soát tại intake):
  SRLV-CX-C1 GO-1 + GO-2 đã CONSUMED, GO-3 chết UNCONSUMED tại close;
  `ETHUSDT-OPEN-SEARCH-V2` STOP-1 đang chờ owner GO (phrase của cycle đó
  thuộc cycle đó — PWS không tiêu).

## 1. Đã đo lại tại intake (re-measure, bằng chứng lệnh chạy được)

- Root `main` @ `a92664cd589008a051d07dc07b773b66777940b5`; dirty tree gồm
  owner paths, draft plans và untracked artifacts của các cycle khác (ERP
  plan_review, SHARED-PORTFOLIO, PSV1 incident…) — tất cả giữ nguyên, không
  stage. Heavy lock `FREE_PROVEN` (không worker giữ). Registry: 72 rows —
  62 TERMINAL, 8 ACTIVE_LIGHT, 2 BLOCKED (registry `updated_at`
  2026-09-26T10:11:04Z).
- `cycle doctor --json`: 46 findings — 14 HIGH đều là `FROZEN_ARTIFACT_DRIFT`
  trên pause packets của cycle TERMINAL đã archive (CRYPTO-V17 / FOREX-FREE-
  V8 / STOCKS-FREE-V12) = lớp accepted-historical per umbrella §3 P0-3,
  không chặn phase lập plan; không finding nào là defect của PWS (một ghi
  chú MEDIUM monitoring liệt kê file draft này — mong đợi, vì nó untracked).
- **SRLV-CX-C1 đã TERMINAL hoàn chỉnh** (registry row + commit `a92664cd`):
  two-half close xong, A7 `CONFIRM_REJECT_ALL`, FAMILY_FAILURES
  `SRLVCX1-M1-SETTLE-RESOLVE` (entry #136), MAP bullet + LESSONS P-28,
  6/18 observed, 0 OOS looks, S1 SEALED. **Premise "đang chờ A7 terminal/
  two-half close" trong instruction đã lỗi thời — không còn blocker nào từ
  cycle này.** ERP1-TRACKA-COHORT-2 cũng đã two-half close (REJECT_ALL,
  0/18). Không ledger nào chưa đối soát chặn việc mở program mới.
- Đã đọc đầy đủ: CLAUDE.md, handbook, umbrella plan §§1–11, ERP-FOREX
  charter (R0–R6, roster, reopening), SRLV master + DATACOST matrix +
  OUTCOME_EXPOSURE_MAP + OWNER_PACKET, VIABILITY_cohort3_REPORT (NO_CANDIDATE
  0/12), OWNER_NOTE cohort-2 lessons, OWNER_PACKET forex program status
  (R1 probe session-2: minTick 0.5 pip ×5 pair, P3-A measured-dead tại IBKR
  tick geometry), MAP/LESSONS/FAMILY_FAILURES (136 entries).

## 2. Bàn giao (3 file DRAFT mới, chưa commit — chờ owner duyệt)

| File | Nội dung |
|---|---|
| `plans/PLAN_pws_program_v1.md` | Master plan: pair-by-pair, ceiling ≤100 identity + registry law, phân bổ per pair, FX frontier law R1–R5, crypto cost/PIT law, multiple-testing law (DSR N_registry, PBO), kill rules, stops, GO phrases |
| `plans/DRAFT_amendment_PWS-PROGRAM-V1_caps_2026-09-26.md` | Amendment caps: Option A (≤96 cells, ≤6 FX + ≤4 CX pair-child, ≤3 identity/pair, ceiling 100 + DSR law) vs Option B (≤144/≤192); chờ owner chọn |
| `research/control/PWS-PROGRAM-V1/OWNER_PACKET_program_open_2026-09-26.md` | File này |

`IDENTITY_REGISTRY.jsonl` (0 rows) chỉ được tạo sau phê chuẩn charter.

## 2b. A7 plan review (đã chạy trước bàn giao này)

- Verdict: **AUTHORIZED_FOR_OWNER_REVIEW** — 0 HIGH, 1 MED, 6 LOW (báo cáo
  `plan_review/A7_plan_review_REPORT.md`; handoff
  `plan_review/HANDOFF_a7_plan_review.json`).
- Toàn bộ MED/LOW đã được Lead sửa trong bản draft hiện hành (binding order
  caps trong amendment §3; thống nhất tên status `WITHDRAWN_BY_OWNER`;
  phạm vi denominator DSR; số liệu crossing P3-A theo đúng VIABILITY; sửa
  citation OUTCOME_EXPOSURE_MAP §2.1; hai câu intake precision; ghi chú
  re-weight trần survey tại Q3). Delta-verify của A7 ghi tại mục này khi
  owner duyệt (xem cuối báo cáo A7).

## 2c. Sau intent GO-1 (cập nhật 2026-09-26T11:2xZ)

- Child plan `plans/PLAN_pws_cx_solusdt_c1.md` đã soạn (DRAFT; caps
  option-invariant; GO phrases byte-identical master §10).
- **A7 child-plan review: `AUTHORIZED_FOR_GO1_GATE`** — 0 HIGH, 1 MED, 4
  LOW; MED (pin shadow-array ancestry theo crypto failure memory) + toàn
  bộ LOW đã sửa và **delta-verify 5/5 PASS** (báo cáo
  `plan_review/A7_child_plan_review_REPORT.md` + delta section; handoff
  `plan_review/HANDOFF_a7_child_plan_review.json`).
- **Trạng thái gate GO-1:** thành phần (2) child plan ✓ và (3) A7 child
  PASS ✓ đã xong. Còn duy nhất: **(1) quyết định Q1 (phê chuẩn charter) +
  Q2 (Option A/B) được ghi vào packet này** — sau đó owner gõ LẠI đúng
  phrase tại gate thì GO-1 được tiêu thụ và Lead register child qua
  researchctl + mở Phase C0→C3 rồi DỪNG chờ GO-2.

## 3. Phát hiện trọng yếu ảnh hưởng quyết định

1. **FX hôm nay = 0 identity scoreable** (VIABILITY: 0/12 class qua pre-PnL,
   zero remainder; sàn chi phí 3.6/4.4 pips stressed RT; P3-A đo chết tại
   IBKR: crossing tối thiểu 1.0 pip @k=2.0 vs ngưỡng 0.41). Mọi pair-child
   FX sẽ mở `BLOCKED_FRONTIER_NOT_REOPENED` 0 cell trừ khi owner chọn R1/
   R2/R3 (đều owner-only: subscription/đăng ký nguồn/broker statement).
   Tran 40 identity FX trong bảng phân bổ là trần KHẢO SÁT, không phải dự
   báo eligible.
2. **CX mở được nhưng hẹp**: ≤3 identity/pair × 4 pair = ≤12 identity tối đa
   về cấu trúc; bị cắt tiếp bởi fences (crypto-ng 11/11 chết |rho| 0.20;
   BTC-BEAR double veto; PSV1 CONTROL_OUTEARNED; EOS1-E1/E2; G5 fold-conc
   0.50 structurally unpassable cho BTC-long) và cost ceiling (funding
   measured; fee declared; spread census 4 pair đều NOT_RUN — phải chạy tại
   data gate, thiếu ⇒ BLOCKED). Đề xuất thứ tự: SOLUSDT → BNBUSDT →
   BTCUSDT → ETHUSDT (ETH cuối do va chạm EOS-V2 đang ACTIVE).
3. **Multiple-testing là rủi ro thiết kế đã được luật hóa trong draft**:
   trần 100 là ceiling của proposer space; identity khác biệt tối thiểu
   (khác ≥2/3: payer/information/risk — anti-variant law); F0 kill trước
   PnL; DSR tại mọi terminal với N_eff ≥ scored trials VÀ công khai
   N_registry ≤ 100; PBO ≥8 configs; K-OOS one-shot không rescue. Với
   Option A, ≤16 identity được score tối đa — phần còn lại của 100 sống/
   chết ở registry (base rate đo được: 7/7 và 11/11 chết pre-PnL gần nhất;
   1/48 gate-eligible rồi fail holdout).
4. **OOS khan hiếm là ràng buộc cứng**: FX chỉ còn AUDUSD/USDCAD 2026-H1
   sealed (một look CẤP CHƯƠNG TRÌNH cho MỘT identity); crypto history
   gần hết exposed ở 1h, 15m/1m cùng giai đoạn = ANCESTRY_EXPOSED_RECLK
   (không phải OOS) ⇒ OOS thật của CX chủ yếu là prospective sau freeze.
5. **Không có cặp nào bị chọn theo PnL**: thứ tự pair freeze tại charter
   trước khi pair đầu được score; replication cross-pair chỉ với identity
   đã freeze + one-look riêng (R5 3-limb).

## 4. Quyết định chờ owner (theo thứ tự)

| # | Quyết định | Hệ quả |
|---|---|---|
| **Q1** | Phê chuẩn charter PWS-PROGRAM-V1 (`PLAN_pws_program_v1.md`) — ghi quyết định vào packet này | Không phê chuẩn ⇒ chương trình không mở; 3 file giữ dạng DRAFT |
| **Q2** | Duyệt amendment caps: **Option A ≤96 cells** (khuyến nghị) hoặc Option B ≤144/≤192 | Không duyệt ⇒ không cycle nào đăng ký được (cần vượt "≤3 cohort/track" hiện hành) |
| **Q3** | Duyệt thứ tự pair + pair đầu tiên: đề xuất **CX: SOLUSDT → BNBUSDT → BTCUSDT → ETHUSDT**; FX khóa tới khi có reopener (pair FX đầu tùy reopener nào mở: R2 ⇒ pair có corpus mới sớm nhất; R1/R3 ⇒ AUDUSD/USDCAD). Trần khảo sát identity per pair (survey-only) có thể phân bổ lại tại Q3 mà không cần amendment — chúng không tiêu cells | Sai thứ tự mong muốn ⇒ ghi đè tại đây trước khi GO-1 |
| **Q4** | FX frontier: chọn R1 (IBKR two-sided + Flex) / R2 (TrueFX/OANDA/Dukascopy consent) / R3 (financing band) — hoặc xác nhận giữ NO_CANDIDATE | Không chọn ⇒ mọi pair-child FX đóng BLOCKED_FRONTIER_NOT_REOPENED 0 cell (first-class close) |
| **Q5** | Sau Q1–Q3: gõ đúng GO phrase đầu tiên **tại gate của nó** (sau khi A7 prelaunch của child plan PASS): `GO PWS CX SOLUSDT C1 COUNCIL AND FREEZE` (hoặc pair owner chọn) | GO gõ trước gate = intent chết (P-8); prompt 2026-09-26 không phải GO |

## 5. Cam kết vận hành (đã ghi trong plan)

- Không đặt lệnh, không sửa shadow/dashboard/worker ngoại, không push/merge,
  không mở sealed OOS, heavy lock tôn trọng (một scored run tại một thời
  điểm), mọi lane có dispatch packet + worktree đúng registry + handoff
  `zcode_orch_v3_handoff@1` tại đúng `handoff_path`.
- Trial ledger ghi mọi outcome-viewed trial; observed/published tách (P-9);
  DSR + N_registry mọi terminal; PBO khi đủ cấu trúc; kết quả âm là
  first-class; dừng đúng stop conditions — không chạy vô hạn để ép winner;
  REJECT_ALL/NO_CANDIDATE/BLOCKED là thành phẩm (Q-16).

## 6. Kết quả pair-child #1 (cập nhật cuối phiên 2026-09-26, dưới ủy quyền)

- **PWS-CX-SOLUSDT-C1 đóng TERMINAL `NO_ELIGIBLE_PROPOSAL`** (A7 terminal
  `CONFIRM_NO_ELIGIBLE_PROPOSAL`, 0 HIGH/1 MED/4 LOW; two-half close đầy
  đủ: FAMILY_FAILURES entry #137, MAP bullet, LESSONS P-29, errata, registry
  flip). 0/18 scored cells, 0 outcome views, 0 OOS looks, S1 SEALED, GO-2
  chết UNCONSUMED. Chi tiết: CYCLE_VERDICT tại worktree
  `orca/pws-cx-solusdt-c1-integration` @ `c3671fad`.
- IDENTITY_REGISTRY: 1/100 (I001 PROPOSED → F0_KILLED).
- Tài sản để lại: data plane SOL đã kiểm (tái dùng không tải lại), phương
  pháp kill rẻ (representation-rho + ceiling×power grid) cho BNB/BTC/ETH.
- **Quyết định master tiếp theo (chưa tiêu — không tự mở)**: pair #2
  BNBUSDT hợp pháp theo thứ tự đã duyệt (stop-rule cần 2 slate trống liên
  tiếp), NHƯNG fences của pair #1 pair-agnostic trên cùng lớp observable —
  khuyến nghị A1/A7: chỉ mở pair #2 kèm proposer angle có bằng chứng thông
  tin mới; nếu không, cân nhắc viability council sớm cho track CX thay vì
  đốt slot registry lặp lại. Quyết định này thuộc owner (hoặc ủy quyền mới).

## 7. Kết quả pair-child #2 + sprint tối 2026-09-26 (dưới ủy quyền + chỉ thị sprint 13:41Z)

- **PWS-CX-BNBUSDT-C1 đóng TERMINAL `NO_ELIGIBLE_PROPOSAL`** (A7 terminal
  `CONFIRM_WITH_FINDINGS` 0 chặn + 3 LOW errata'd; two-half close đầy đủ).
  0/18 scored cells, 0 outcome views, 0 OOS looks, S1 SEALED, GO-2 chết
  UNCONSUMED, **0 slot registry tiêu** (N_registry = 1/100). Chi tiết:
  CYCLE_VERDICT tại worktree `orca/pws-cx-bnbusdt-c1-integration` @
  `33a69f10`. Kill được ĐO trên chính chuỗi BNB (rho 1.12–2.97× bar 0.20,
  persistence +0.759, ceiling 80 < 100) — P-29 "pair-swap opens nothing"
  xác nhận bằng số đo trên pair thứ hai.
- **Stop-rule track CX §9(a) KÍCH HOẠT** (2 pair-child liên tiếp slate rỗng):
  viability council bắt buộc trước khi mở pair mới.

### Quyết định owner đang chờ (một quyết định)

| Option | Nội dung | Khuyến nghị A1 |
|---|---|---|
| **O1** | Dừng mở pair-child CX trên cùng lớp observable; duyệt MỘT information layer mới có authority (ứng viên đo sẵn: **BNB event calendar** — burn quý/SEC-DOJ 2023/Launchpool, sự kiện công khai có ngày) ⇒ DATACOST row mới + child plan + A7 + council | **KHUYẾN NGHỊ** — cửa duy nhất có bằng chứng tonight-recorded |
| O2 | Vẫn mở BTCUSDT/ETHUSDT trên lớp observable cũ | Không khuyến nghị (P-29 đo 2 lần; đốt slot/OCR 14 ngày mỗi pair) |
| O3 | Giải phóng disk ≥25GB để spread census BNB chạy lại | Chỉ có nghĩa sau O1 có identity vượt F-0 |
| FX | Không đổi: chờ reopener R1/R2/R3 bằng chứng bytes (owner-external) | Giữ nguyên |

GO chain hiện trạng: GO-1 SOLUSDT + GO-1 BNBUSDT đã tiêu dưới ủy quyền;
GO-2 chưa từng tiêu; GO-3 chưa từng; S1 SEALED mọi nơi.
