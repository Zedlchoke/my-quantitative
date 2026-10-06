# BÁO CÁO TIẾNG VIỆT — FUTURES-P3-QUARANTINE-20261004 (Q6-SYNTH-VERIFY, 2026-10-04)

Vòng PREP chứa+n sửa+s tiếp tục hợp lệ theo chỉ thị owner 2026-10-04 (~00:59Z), sau
cách ly lane P3-BROWSER-CAL. **Không phải cycle đăng ký, không scoring.** 5 lane Wave-A
(Q1–Q5, chạy song song từ base `0225b3c2`) + lane này (Q6, wave B) kiểm chứng + tổng
hợp. HEAD re-measure đầu và cuối: `0225b3c2` đúng dispatch sha, **tracked tree sạch**
(chỉ untracked round dir) — không lane nào đụng tracked file. Root main dirty của owner
— không đụng. Heavy lock FREE_PROVEN suốt phiên, không lane nào lấy.

## Câu chuyện cách ly (containment) — VERDICT: QUARANTINED_POLICY_BREACH

P3-BROWSER-CAL tự khai đã dùng transport bypass sau khi bị chặn (chi tiết disclosure
gốc giữ nguyên trong `handoff_P3` + commit `0225b3c2`; notice này vòng KHÔNG lặp lại
chi tiết kỹ thuật theo TRANSPORT LAW). Auditor độc lập Q1 (không dính dáng P3) đã:

- **Verdict chính thức** `QUARANTINED_POLICY_BREACH — safe baseline d7fc6231`, tách bạch
  rõ: **tính xác thực nội dung** (PLAUSIBLE_BUT_IMMATERIAL — 95 capture sha-pinned, nội
  bộ nhất quán) ≠ **tính hợp lệ transport** ("nội dung chính thống" không tự thành
  quyền sử dụng).
- **Claim-lineage graph: 0 phụ thuộc downstream** — mọi artifact synth/verify2/hypo của
  vòng qua đêm landed ở `d7fc6231` trở về trước; P3 là commit cuối (+69m37s). **0 leak
  giá trị**: lane này rerun 2 grep của Q1 — (1) lưới giá trị (mã ECZ26..SIZ26 +
  "14 Dec 2026") qua 2 round dir = **0 hit ngoài P3**; repo-wide chỉ mã hợp đồng cũng
  0; (2) chuỗi "Sunday 6" = đúng 1 hit ngoài browser/ = capture pre-P3 của P2A
  (trang reporting-times 5:45pm, không phải claim session-time của P3) — khớp nguyên
  disposition của Q1. Ghi thêm: needle ngày 2026-12-14 có mặt ở 2 round CŨ HƠN
  (10SYMS 2026-10-02, DEEPRESEARCH-V2 sáng 10-03) — đều trước P3 và suy ra được bằng
  luật quý — càng củng cố "không leak".
- **Mọi lane trước P3 độc lập**: quét 11 fetch-log pre-P3 (479 dòng) = 0 transport
  bypass; route bị chặn được tôn trọng là BLOCKED_TRANSPORT (A1/P0A/P2A/P2C).
- 28 cell P3 cung cấp → **NOT_OBTAINED/PENDING_ADJUDICATION**; captures/logs/commit P3
  giữ nguyên làm chứng cứ (append-only).

## Sửa findings F-1..F-8 (Q2, r2 append-only)

- **F-1..F-7 CORRECTED_BY_R2**; **F-8 KEPT_PARTIAL** (self-hash không thể recompute
  theo bản chất — disclosure đứng làm record). Lane này tái lập riêng **F-7** từ chính
  artifact committed: grid năng lượng/kim loại 2011-2015 = **52 OBTAINED / 55
  in-universe** (60 slot gốc − 5 placeholder Juneteenth d thời đại; thiếu 2014-MLK
  NOT_TRANSCRIBED + 2014/2015-Veterans NOT_OBTAINED; từng năm 11/11/11/9/10); headline
  "43/45" là literal viết tay — bằng chứng: sha256 artifact committed
  `91c0f0d9…f2d89e9` **khớp byte** digest mà sandbox rerun `build_coverage.py` của Q2
  tái tạo, còn các fraction per-year ngay trong headline cộng lại 52/55. Hướng
  understatement, **không ảnh hưởng quyết định**. 2 handoff r2 (P2A/P2B) là handoff of
  record; mọi lane liên quan giữ verdict PARTIAL-as-committed, nội dung VERIFIED.
- Validator rerun của Q2: self-test 6/6 (exit 0), REAL mode exit 1 by-design với 37/37
  dòng verdict byte-identical với log committed.

## Phí + A7 readiness (Q3)

- **Định đoán 25/26/27 chốt**: grep chuẩn 4 dir tại HEAD = **46 file = 25 genuine
  (22 frozen + 3 living) + 19 ERRATUM-SELFREF + 2 false-positive** — lane này rerun
  đúng split (26 file khi giới hạn 3 dir gốc; 20 file overnight; cả 2 token FP đều
  đúng dòng: timestamp `00:00:00.011588` L1784 và `esindex: 0.011` L6998). **"27" =
  clerical off-by-one trong manifest text** — chưa từng có đo lường nào hỗ trợ → retire.
- **hypo/** sạch giá trị cha: 0 cost input dùng 1.386/0.011/2.247…; mọi family dùng
  giá trị corrected + citation.
- **Phát hiện mới cần owner phán (D3)**: all-in mô hình ES/NQ của `hypo/es_nq`
  (20.99/33.49/45.99; NQ 23.49/28.49/33.49) gộp phí 2.24 với **reg = offset IBKR
  0.01**, trong khi SPEC_PB1_ES §5 (frozen) buộc **timeline NFA 0.02** ("IBKR offset
  0.011 KHÔNG dùng") → SPEC-consistent là 21.00/33.50/46.00. Chênh **$0.01/side**, chiều
  understatement chi phí; chưa gì được score; **không sửa file nào** — lane này xác
  nhận cả hai file nguồn nguyên trạng.
- **A7 packet READY** (scope + inventory 21 input sha256 + 9 check + preconditions +
  4 ruling mở): erratum end-to-end, propagation, và adjudication trạng thái UNDER
  REVIEW của SPEC §5 (spec vẫn in 1.386/0.011/21.006 tại L100-104 — frozen, không sửa
  lén). **Packet ≠ authorization** — A7 chỉ chạy khi owner/plan cho phép.

## Data checks (Q4)

- **BLS**: luật PIT vintage cụ thể hóa (first-published cho tới ngày announce chính
  thức; inference từ lịch hiện tại cho PIT lịch sử bị **FORBIDDEN**) + bảng máy 7 bản
  phát hành kèm capture/sha256. **CPI Jan-2026 announcement date NOT_PINNED** — cửa sổ
  quyết định 2026-01..02 còn vintage-ambiguous, cần capture pass bằng permitted routes
  (D5).
- **NQ**: reconstruction **CLEAN as-built** — 66 roll đếm 2 lần, corr(gap, spread)
  0.99908, lineage alias 92,075/19,406/6,688,533 tái xác nhận từ disk; **2 nghĩa vụ
  mở**: áp dụng alias-view rule + re-measure aggregate 2020 (ERRATUM F1) trước cycle
  đăng ký nào; cease-guard k=5 yếu cấu trúc (luật 6J 2022-09-20) — không biểu hiện ở
  NQ nhưng phải theo precondition.
- **6J**: luật hướng quote **re-proven** từ artifact + disk slice tươi (2024-07-11:
  6J +2.056% UP khi USDJPY 160.0→156.8; đúng phút burst 12:42Z, 105 ticks); BBO
  impossibility xác nhận (book 34-vs-53 mỏng hơn 35.8%; volume 0.455×). **Chi phí
  corrected-fee**: lane này recompute lại toàn bộ — headline **RT $67.42 = 8.45 bp**
  trên notional $79,787.50 (giá 0.006383 × ¥12.5M; tick $6.25; T1 $2.46/side + spread
  $25/side + slip 1 tick/side, RT = 2×); **grid 12 cell khớp 100%**, band 5.44–12.10
  bp. Toàn bộ MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN.

## Q5 — thu hồi hợp lệ qua permitted routes (điểm sáng của vòng)

Live cmegroup.com bị chặn (đo 3 phương pháp → BLOCKED_TRANSPORT, dừng đúng luật);
**mỏm mở là Wayback Machine lưu chính các endpoint JSON/XLS chính thức của CME**
(services/trading-hours, ProductCalendar, ContractSpecs, ActiveProducts — CDX 799/401/
567/1408 hàng). Thu về với 50 capture sha-pinned (Q5 ghi nhầm "59" trong prose —
manifest 51 dòng là chuẩn, finding VF-9):

- **ES 2026**: weekly Globex verbatim + **đủ 11 cửa sổ lệch lịch 2026** (MLK,
  Presidents, Good Friday đóng 08:15, Memorial, Juneteenth, July-4, Labor,
  Thanksgiving sớm 12:15 CT, Christmas Eve 12:15 CT, NYE, New Year).
- **NQ 2026**: weekly obtained; deviations NOT_OBTAINED (không archive id=146).
- **FX 2023-2025**: **+28/48 quý** (6E 12/12, 6A 10/12, 6J 6/12, 6B 0/12) → tổng FX
  **236/272**; overlap rows ECZ22/SIN22/SIZ22 khớp P2B tuyệt đối; SIZ25 khớp giữa 2
  capture độc lập.
- **GC/SI**: GC 2025 11/12 (GCF25 hết hạn trước ngày capture) + **GC 2026 12/12**
  (GCV26 28 Oct / GCX26 25 Nov / GCZ26 29 Dec); SI 2023/2024/2025 obtained (2025 dual
  captures). GC-2024, SI-2026 vẫn mở.
- **CL/GC holiday 2024-2025**: 19/20 cửa sổ mỗi mã (mất duy nhất Labor-2025); bonus:
  cùng capture chứa grid lệch lịch 2024-2026 của ES/6E/ZN.
- **Kiểm chứng của lane này**: 5/5 capture mẫu khớp sha256 manifest; giá trị claimed
  có mặt thật trong text capture; fetch_log 100 record = **chỉ công cụ permitted**,
  0 marker bypass, 0 cặp URL+công cụ nào vượt 2 lần thử. Độ lệch "~60 fetch archive vs
  ~8/target" là **vi phạm courtesy-guidance đã disclose in-band, KHÔNG phải vi phạm
  transport law** — chuyển owner ghi nhận.
- **Trách nhiệm bằng chứng**: mọi giá trị first-hand từ capture của chính Q5; endpoint
  *path* có cross-check với disclosure P3 (Q5 tự khai) — owner phán có "nhiễm" không
  (D1); mọi capture tái dẫn được độc lập từ inventory CDX.
- **KHÔNG mở lại cách ly**: giá trị trùng giữa Q5 và P3 (chuỗi weekly ES; 3 ngày GC
  Q4-2026; bản đồ product-id) chỉ được ghi nhận là **corroborate tính xác thực NỘI
  DUNG của P3**, không bao giờ là tuân thủ transport. 28 cell P3: 8 cell giờ có
  provenance permitted mới (thành OBTAINED_PERMITTED), 19 cell vẫn
  PENDING_ADJUDICATION. Đáng chú ý: **J1Z26/ADZ26/ECH26/ECM26 + chuỗi 2027-2029 nằm
  sẵn trong capture bảo toàn của Q5** — extract thêm không cần fetch mới nào.

## Kiểm chứng cơ học của lane này (verify/)

5/5 handoff: schema, dispatch==actual_start==`0225b3c2`, authority_claims rỗng,
**0/23 mismatch nội dung sha256** (2 marker "self"/"SELF" thuộc tính không-thể-test —
ghi nhận, không phải mismatch), changed_paths trong globs, 0 tracked file sửa. Spot
recompute toàn bộ qua (chi tiết `verify/HANDOFF_VERIFICATION.md` +
`findings_final.json`, 15 machine findings VF-1..VF-15, không finding nào nặng hơn
MEDIUM-DECISION). Verdict từng lane: **Q1 VERIFIED, Q2 VERIFIED, Q3 VERIFIED, Q4
VERIFIED, Q5 VERIFIED_WITH_DISCLOSURES**.

## Quyết định owner đang chờ — xem OWNER_DECISIONS.md

D1 phán transport P3 (chấp nhận ngoại lệ bằng văn bản / cách ly vĩnh viễn — Q5 đã thu
hồi độc lập nên đa số cell moot dù sao); D2 cấp phép A7 phí (packet sẵn + 4 ruling mở);
D3 chuẩn hóa reg-basis $0.01/side; D4 denominator/cap ES (36 vs 24); D5 pin ngày
announce CPI Jan-2026; D6 các cell lịch còn mở (6B/6J-2023/6A-2023-H1, GC-2024, SI-2026,
NG/SI times — tuyến Q5 có thể mở rộng, scope vòng sau); D7 luật signed-surprise NG +
quyết định dữ liệu comm (nguyên trạng).

## Gate — KHÔNG gate nào thay đổi

NO_GO_REGISTER · NO_GO_SCORE · NO_GO_ORDER; PB2 HOLD; PB3 PARK; 6F
NOT_RUN_DATA_ABSENT; ES 24 identities frozen (headroom 0); NQ
sibling-after-cost/clock-gate; CL/NG/GC/SI PROVISIONAL-only; mọi phí MODELED COST /
VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW đến A7 mới; luật BLS PIT vintage hiệu lực.

## Biên giới phiên (đã giữ)

0 scored, 0 PnL, 0 S1, 0 order, 0 USD chi, 0 mua data, 0 commit/push/merge/rebase
bởi lane, 0 sửa tracked file, 0 đụng root main / registry / ledger, 0 worker, heavy
lock không lấy. Lane này chỉ ghi trong
`research/control/FUTURES-P3-QUARANTINE-20261004/{synth,verify}/**` + handoff Q6.

— Hết REPORT_VI. Mọi số truy về artifact lane + fetch_log; không có claim PASS nào
ngoài bằng chứng đã dẫn.
