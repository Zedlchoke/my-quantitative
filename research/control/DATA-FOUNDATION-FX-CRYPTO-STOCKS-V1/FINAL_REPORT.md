# FINAL REPORT — DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 (2026-09-26)

## Một dòng cho owner

Nền dữ liệu của chương trình đã được kiểm kê và kiểm định xong: **91 dataset
rows** (32 VALIDATED bằng đo lại từ bytes, 26 có-mà-chưa-validate, 28
NOT_RUN có lý do, 5 BLOCKED có chữ ký owner-action); cái thiếu đều đã có
runbook R1–R8; **kết luận kép: FOUNDATION_READY_FOR_NARROW_RESEARCH (crypto
+ stocks) và BLOCKED_WITH_ACQUISITION_RUNBOOK (forex after-cost)**. Không
có strategy nào được chứng minh có lời — cycle này 0 scored cell theo đúng
thiết kế.

## Đã làm gì (đơn giản)

1. **Intake thật** — đo lại HEAD/đĩa/lock/worktrees; đọc toàn bộ tài liệu
   quyền lực. Phát hiện sớm ràng buộc lớn nhất: **đĩa chỉ còn ~7 GiB**.
2. **Master plan + A7 review độc lập** trước khi làm (1 HIGH về đĩa đã sửa
   bằng amendment r1: cap tổng 2 GB kể cả worktree).
3. **5 lane khảo sát song song** (Forex / Crypto / Stocks / PIT-license /
   Cost), mỗi lane một worktree + dispatch packet + structured handoff,
   tích hợp tuần tự. 0 network ở lane, 0 seal bị đọc, 0 đụng cycle đang chạy.
4. **Kiểm định thật từ bytes**: 38/38 sample sha crypto ALL_MATCH; Dukascopy
   5 corpus khớp manifest; FTD 434 zips đếm lại; amihud 8,219/8,219 full
   re-hash; Form-4 substrate digest EXACT. File tồn tại chưa bao giờ được
   coi là PASS.
5. **1 probe nhỏ (11 requests / 1.2 MB)**: phát hiện **premiumIndexKlines
   có sẵn keyless trên Binance Vision** (sha khớp CHECKSUM nhà cung cấp)
   → gap "funding dự báo" từ không-biết thành chi phí ~7 MB khi cần.
6. **6 deliverables + exposure map + A7 terminal audit** (0 CRITICAL/HIGH;
   3 MEDIUM đều là sai số văn bản — đã sửa bằng erratum công khai).

## Những con số owner cần nhớ

- **Chi phí thực thi là cửa lớn nhất**: FX 2/10 thành phần đo được, crypto
  3/10, stocks 0/10. Sàn ERP1 3.6/4.4 pip chia đôi không gian FX — chỉ
  statement broker mới DI CHUYỂN được nó.
- **TWS của bạn đã chạy hôm nay và API Read-Only đã hoạt động phía server**
  — chỉ thiếu subscription FX delayed (free) và 1 lần xuất statement.
- **8/14 tarball trong ~/staging_backups đã mất** (kể cả corpus OI V14) —
  P-13 drift, cần bạn xác nhận (runbook R7).
- Staging 1.9G của stocks-search-v1 gần như không sha-pin (6/111,322) —
  sửa 2 phút, đã ghi N9.
- S1 SEALED toàn bộ; holdout ERP1 2026-H1 AUDUSD/USDCAD chưa đọc (chỉ pin
  manifest). 28 cửa sổ dữ liệu đã outcome-exposed đã được lập bản đồ để
  tách khỏi dữ liệu xác nhận.

## Việc owner cần làm (chi tiết trong OWNER_ACQUISITION_RUNBOOK.md)

Nếu chỉ làm MỘT việc: **R1 — xuất 1 statement IBKR có giao dịch FX qua đêm
+ bật FX delayed data, restart TWS**. Không gửi nội dung statement vào
chat — chỉ đường dẫn file trên máy. Hai việc: +R3 (giải phóng ≥25–40 GB
đĩa). Ba việc: +R2 (chọn TrueFX hoặc OANDA practice làm nguồn FX thứ hai).

## Hướng nghiên cứu kế tiếp (NEXT_RESEARCH_FRONTIER.md)

- **F1 (READY-PARTIAL)** — Stocks: họ filing-flow + trạng thái giá build
  lại PIT trên cohort chết-bao-gồm (planes chính đã VALIDATED; earnings
  timestamps = probe free N2).
- **F2 (READY)** — Crypto: sách đa symbol trên mặt phẳng chi phí ĐO ĐƯỢC
  (funding 11.8%/năm đo thực vs hằng số 1.5% cũ).
- **F3 (BLOCKED)** — FX after-cost: chờ R1/R2.

## Gate table

| Gate | Verdict | Evidence |
|---|---|---|
| G0 intake + plan + A7 plan review | PASS | 939d426e / 189c6d23; audits/A7_PLAN_REVIEW_r1.md AUTHORIZED_WITH_FINDINGS (remediated) |
| G1 packets + worktrees + registry | PASS | af7b1c3c; G1_BOOTSTRAP_EVIDENCE.md (6→7 worktrees, disk ledger 7.7→5.9 GiB free, cap giữ) |
| G2 inventory completeness | PASS | 91 rows; every lane target rowed or reasoned NOT_RUN |
| G3 validation in-budget, no inferred PASS | PASS (1 self-caught erratum) | lane tests in HANDOFFs; D1 erratum f05c1baf (validator VALID: 91) |
| G4 deliverables drafted | PASS | D1–D5 + exposure map + contracts committed |
| G5 probes within budget | PASS | probe_ledger.json 11 req / 1.2 MB / PS2 NOT_RUN_LOW_VALUE |
| G6 A7 terminal 0 HIGH/CRITICAL | PASS | audits/A7_TERMINAL_AUDIT.md 0C/0H/3M/3L — all remediated 5cbfebec |
| G7 two-half close | PASS (this close) | registry TERMINAL + ledger row + MAP bullet + push |

## Sự cố ghi nhận (không có gì bị che)

- P-19 erratum: commit D1 đầu ghi "validator PASS" khi file đang FAIL 265
  vi phạm — tự bắt, sửa công khai (f05c1baf + đính chính 109→265).
- L-CX I-1: 8/14 archive staging_backups mất (trên).
- L-ST: 1 tar-listing ~50MB viết tạm ra /tmp rồi xóa trong cùng lệnh (tự ghi).
- A7 F-A7-5 (LOW): 5 handoff JSON thiếu field mở rộng của schema
  (recommended_next_action…) — ghi làm luật cho cycle sau, không sửa lại.

## Denominators

0 scored cells (0/0). Program counters unchanged (P-9: ledger là authority).
S1 SEALED. Không order, không PnL, không shadow/dashboard bị đụng.

## Terminal label

`DATA_FOUNDATION_V1_FOUNDATION_READY_FOR_NARROW_RESEARCH__BLOCKED_WITH_ACQUISITION_RUNBOOK`
(kép theo asset: crypto + stocks ready; forex after-cost blocked on R1/R2).
Đây KHÔNG phải và không thể đọc là "strategy đã được chứng minh có lời".
