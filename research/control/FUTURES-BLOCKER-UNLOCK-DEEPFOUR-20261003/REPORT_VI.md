# BÁO CÁO TIẾNG VIỆT — FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 (Lead, 2026-10-03)

Vòng PREP theo chỉ thị owner (bản cập nhật: Lead tự chọn số lane; boundary
read-only/prep giữ nguyên). **Phương thức dispatch: ZCode built-in Agent tool**
(vì orchestrator MCP không khả dụng trong session — disclosed; handoff vẫn theo
schema `zcode_orch_v3_handoff@1`, Lead kiểm chứng thủ công theo skill
structured-handoff). **8 lane nghiên cứu + 2 vòng fix**: A1-A5 (blocker tách theo
nguồn), B1-B2 (deep-four tách theo cặp symbol), VERIFY (đối chiếu độc lập).
Base `7149425d` (prep), root main `4f266528` dirty của owner — không đụng.
Heavy lock FREE_PROVEN suốt phiên, không lane nào lấy lock.

## Kết quả blocker (A1-A5) — mọi claim FACT có URL + ngày capture

- **A1 CME calendar NQ+ES**: NQ holidays/early-closes **17/17 năm** (2010 PDF
  chính thức 38 trang re-fetch + parse; 2026 LIVE). NQ expirations **68/68 quý**
  (quy tắc 3rd Friday verbatim 3 era spec-pages; lệch duy nhất 2026-06-18 =
  Juneteenth shift, đúng như ES). **ES expirations 36 → 63/68** (đóng đủ
  2019-2023 + 2026 + Mar/Jun 2024 ở mức ARCHIVED_OFFICIAL_FAMILY "Equity Index
  Roll Dates", 4 capture độc lập khớp). Còn thiếu: ES 2026 giờ Globex cụ thể
  (widget/host block — NOT_OBTAINED, không bypass) + ES Sep/Dec 2010,
  Mar-Jun/Sep 2011.
- **A2 CME calendar FX (6E/6B/6J/6A)**: holidays **2010-2016 PASS product-level**
  (PDF/XLS chính thức từng ngày; FX-family bảng riêng, không mượn bảng equity);
  2017-2025 chỉ windows-level (NOT_OBTAINED product-times); 2026 windows +
  Holiday Notes verbatim. **Expiry rule verbatim x4 mã, không đổi 2011→2023**:
  "9:16 a.m. CT on the second business day immediately preceding the third
  Wednesday of the contract month (usually Monday)". Expiry dates **96/272 quý**
  (6E 17, 6B 31, 6J 13, 6A 35 — sau khi sửa F-1; 96/96 khớp quy tắc, 0 conflict
  giữa các capture); 2019-2026 NOT_OBTAINED (JS-shell era).
- **A3 CME calendar CL/NG/GC/SI** (feasibility, không claim qualification):
  CL rule + **183 tháng dates** (Apr2010-Feb2027, chứa cả sub-rule weekend/
  holiday-shift mà v1 dossier thiếu); NG rule (2021 chính thức **trùng nguyên
  văn** rule v1) + **240 tháng**; GC/SI rules verbatim 2 era — phát hiện
  **SI 12:25 vs GC 12:30 CT** (offset 5 phút vàng/bạc, xác nhận chính thức);
  GC/SI dates partial (GC 2013-2019, SI 2015-2019; 2019-2026 NOT_OBTAINED).
  Holidays energy+metals = 1 family NYMEX/COMEX (2010 verbatim đầy đủ).
- **A4 Phí public 9 mã** (IBKR LIVE_OFFICIAL fetch 2026-10-03 13:05-13:25Z;
  mọi dòng SOURCE=PUBLIC_REFERENCE, VERIFIED_VS_ACCOUNT=NOT_RUN, MODELED COST):
  **NQ all-in 2.247/2.047/1.847/1.647** (tier 1-4; = 0.85+1.386+0.011);
  **6E/6B/6J/6A 2.461/2.261/2.061/1.861** (FX group row 0.85+1.60+0.011 —
  corroboration PARTIAL, cần 1 trang dated bind tường minh 4 mã vào fee-class
  1.60); CL 2.37…; NG 2.47…; GC/SI 2.51…. CME fee-schedule PDFs + TradeStation
  live + AMP mirror: BLOCKED_TRANSPORT (29 lần thử logged). Phi/historical
  per-year: vẫn CURRENT_SCHEDULE_AS_APPROXIMATION (NFA timeline 2014/2018 đã có).
- **A5 Events/BBO/Coverage**: **BLS CPI + NFP/Payrolls 17/17 năm
  PASS_EVIDENCED_CALENDAR** (204+204 releases, tất cả 08:30 ET, chuỗi timezone
  chứng minh 2 tuyến: landing page + bls.ics TZID; 32 snapshot archive.org).
  2 anomaly ghi nguyên văn không đoán nguyên nhân: CPI 2016-04 double-entry;
  **late-2025 vintage divergence** (CPI Oct 15→24, Dec 10→18; EMPSIT Nov 7→20,
  Dec 5→16 giữa trang cũ archive và ics hiện tại — lưu ý PIT khi dùng 2025+).
  BBO: tài liệu hóa bbo-1m/1s = single-level BBOMsg (SDK dbn), mbp-1/10, mbo
  RType160; D5 law giữ nguyên (**bbo-1m không chứng minh intrabar fill/queue**).
  Coverage: IBKR staleness 0.825-0.891 ngày (10 nhóm, max-mtime 2026-10-02);
  **CL/NG/GC/SI zero file O1M** ở vendor root — xác nhận cơ học v1-only.

## Deep-four (B1-B2) — không PnL, không selection, mọi tham số [PROVISIONAL]

- **B1 ES+NQ v3 addenda (12 mục mỗi mã)**: ES **không đổi** SPEC_PB1_ES r3
  (freeze-ready, 24 identities đứng nguyên). NQ sibling-after-cost-gate — giờ
  có all-in tier-1 2.247 từ A4 (cost gate còn lớp account + slippage + spread
  proxy 6.5 tick thiên cao). Phát hiện mới: **NQ 2020 re-measure +38.43%**
  (sau alias-recovery, cũ +13.20%); **NEW-4 falsifier**: chuỗi NQ không adjust
  embedding 4-5%/yr phantom drift 2023-26 (roll-gap corr 0.999 với spread);
  adjudication **ES acf1 = 5/7 eras âm là ĐÚNG** (prose v2 dossier ghi 6/7 sai
  — erratum chờ lane sở hữu dossier, B1 chỉ disclose). Ancestry: PB1 là
  **first-generation** (không họ scored tiền nhiệm trong program; FOREX-FREE
  London chỉ là cảnh báo cost-domination, không transplant veto được).
- **B2 6E+6B v3 addenda + PB2_ANCESTRY_COURT_DRAFT**: khai quật đủ **4 dead
  families** từ PLAN_forex_v2 + git artifacts (cả hai V2 là London-window,
  12/12 cells EXPECTANCY_NONPOSATIVE @ proxy 3.0bp spot). Phân biệt 3 trục:
  information-source **STRONG** (sàn CME 23h + local-clock windows + event-day
  structure vs dealer spot), mechanism/causal-control **PARTIAL**, **cost-level
  CHƯA thiết lập** — 6B futures proxy 5.8-10.4bp RT > dead base 3.0bp (A4
  exchange 1.60/side ≈ 0.23-0.25bp RT không đảo ngược kết luận này). Power:
  MDE 3.3-15.4bp vs cost 3.3-10.4bp — court chỉ khả thi cho edge ≥ cost; đề
  xuất trigger-census gate tối thiểu. **KHÔNG kết luận mở lại PB2 — HOLD giữ**;
  dependencies liệt kê rõ (A2 calendar r2, A4 binding page, BBO/fill realism,
  trigger census, telemetry dead-family NOT_LOCATABLE, multi-seed placebo
  budget, CIP-vintage owner decision).

## VERIFY (đối chiếu độc lập) + fix

**0 CRITICAL.** 38/38 sha256 outputs khớp; mọi số headline recompute reproduce
(45/45 all-in A4 exact; 68/68 + 67 conform + 1 Juneteenth A1; 96/96 rule-check
A2; 183/240/22/20 A3; 204+204 + staleness A5; 26/26 pins B1; MDE 12 cells
≤0.01bp B2). Ngôn ngữ cấm: 6 hit đều là câu phủ định/law, 0 dùng tích cực.
Findings: **F-1 MAJOR** (đếm 6E 18-vs-17 mâu thuẫn nội bộ A2) và **F-2 MAJOR**
(authority_claims ≠ [] ở A2/A3 — vi phạm luật cơ học) **đã sửa bằng handoff r2**
(A2: 6E 17, tổng 96/272 nhất quán 3 chỗ, ECH12 grep-proven absent qua 9 capture;
A3: authority_claims=[], changed_paths 51 đường dẫn; r1 preserve nguyên vẹn).
Residual MINOR/NOTE: F-3 (tests[] shape 6 lane — A3 r2 vẫn tests rỗng, validations
do VERIFY thực hiện độc lập thay thế), F-4 (path cosmetics), F-5 (URL 2011 của A1
là evidence kế thừa D3, disclosed), F-6 (A5 log timestamps reconstructed),
**F-7 (A2 pip-install xlrd vào shared venv — environment mutation ngoài file
boundary, disclosed; Lead ghi nhận)**, F-8 ("17.2x" là FOMC không phải ECB —
shorthand của dispatch, artifact đúng), F-9 (ES acf1 5/7 adjudicated).

## Ảnh hưởng gate — KHÔNG gate nào được nâng trong phiên này

- Mọi phán quyết giữ nguyên: **NO_GO_REGISTER · NO_GO_SCORE · NO_GO_ORDER**;
  PB2 HOLD; PB3 PARK; 6F NOT_RUN_DATA_ABSENT (không đụng); ES cycle ES-only
  24 identities; D2 account verification vẫn NOT_RUN; mọi phí chỉ MODELED COST.
- **Fold-in các nâng cấp vào DATACONTRACT_QUALIFICATION / SUMMARY là việc của
  owner/Co-Owner + A7 round sau** (không tự sửa tài liệu committed của round
  trước trong phiên này): holiday/expiration authority (ES 63/68, NQ 68/68,
  FX 2010-16 + rule verbatim, CL/NG full), BLS PIT PASS_EVIDENCED_CALENDAR,
  fee tables 9 mã public-reference, và 2 erratum chờ (ES acf1 5/7; A2/A3 r2).
- Còn thiếu cho cost authority: account verification (owner), FX fee binding
  page dated, slippage declared, BBO/fill (chủ sở hữu quyết định mua — lane chỉ
  tài liệu hóa). Còn thiếu calendar: ES 2026 giờ cụ thể, ES 5 quý 2010-11, FX
  2017-2025 product-times + 2019-2026 dates, GC/SI 2019-2026, CME fee PDFs
  (transport), 2011-2015 per-holiday PDFs energy/metals.

## Biên giới phiên (đã giữ)

0 scored, 0 PnL, 0 S1, 0 order/paper/live, 0 USD chi (toàn bộ $0 read-only),
0 mua data, 0 push/merge, 0 sửa tracked file, 0 đụng root main/dirty files,
0 đăng ký cycle, 0 worker bị kill. Tree prep: chỉ untracked
`research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/` (+ commit tích hợp
của Lead trên branch prep).

— Hết REPORT_VI. Mọi số truy về artifact lane + fetch_log; không có claim PASS
nào ngoài bằng chứng đã dẫn.
