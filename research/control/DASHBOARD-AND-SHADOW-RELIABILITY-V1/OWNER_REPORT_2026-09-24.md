# BÁO CÁO OWNER — DASHBOARD-AND-SHADOW-RELIABILITY-V1 (2026-09-24)

Phạm vi: paper/shadow, không broker/lệnh thật, không push/merge. Bắt đầu
bằng đo lường lại toàn bộ (không tin trạng thái cũ). Toàn bộ bằng chứng:
`research/control/DASHBOARD-AND-SHADOW-RELIABILITY-V1/` (GATES.md,
A7-RELIABILITY-AUDIT-2026-09-24.md, owner packet).

## 1. Bảng 6 strategy (chụp lúc 09:00Z)

| Strategy | Data | Worker | Last decision | Last fill | Next decision | Accounting | PnL/valuation | Gate |
|---|---|---|---|---|---|---|---|---|
| XSECT-FUND-CARRY-7D | OK | pid 35779, loop 8, 0 lỗi | 09-24T00:00Z **OK** | trong 48 fill sách (realized +3,936.27) | 09-25T00:00Z | OK | RUNNING 99,614.74 (mark 08:55Z) | **PASS** (sự kiện daily tiếp = 09-25, chờ thị trường) |
| ILLIQ-AMIHUD-28D-W | OK | pid 35779 | 09-21T00:00Z **OK** | 8 fill (gross ~1.0, không đếm thiếu) | 09-28T00:00Z | OK | RUNNING 99,477.90 | **PASS** (weekly tiếp = 09-28, chờ) |
| BASISLV-PREMFADE-28D | BLOCKED tại 09-21 (thiếu 286 bar từ 09-18T00:15Z — fail-closed đúng; **nguồn đã lành**: probe 30 ngày × 13 symbol, 0 gap) | pid 35779 | 09-21T00:00Z DATA_BLOCKED (event_id đã tiêu thụ, không backfill) | 0 (chưa từng có signal) | 09-28T00:00Z | UNAVAILABLE_FAIL_CLOSED (trung thực) | FLAT_OK 100,000.00 | **BLOCKED** → chuyển PASS/FAIL tại sự kiện 09-28 |
| BTC4H-BANDRIDGE | OK | pid 35779 | 09-24T08:00Z **OK đầu tiên** (band ON + không breakout → FLAT, không lệnh) | **0 fill — có nguyên nhân gốc, chờ quyết định owner** | 09-24T12:00Z | 56 quyết định đầu UNAVAILABLE_FAIL_CLOSED (xem §3), sự kiện 08:00Z OK | FLAT_OK 100,000.00 | **PASS máy** / **chờ owner** cho luật sizing (packet đính kèm) |
| EURUSD (RANGEFADE-2M) | OK — TrueFX 15s, mark tươi 0.3s | daemon pid 35609, heartbeat 09:00Z | bar 08:00–09:00Z đóng 09:00Z, target 0 | 0 (thị trường chưa tạo tín hiệu — hợp lệ) | 09:00Z ranh giờ H1 | OK (parity PASS 4 lần boot) | FLAT 100,000.00 | **PASS** |
| GBPUSD (RANGEFADE-2M) | như trên | như trên | như trên | 0 | như trên | OK | FLAT | **PASS** |

Trạng thái tổng: e-worker + valuation worker + FX daemon đều chạy đúng
HEAD sau khi được restart có kiểm soát (ledger byte-count **giống hệt**
trước/sau restart — không nhân đôi event).

## 2. Bảng 2 app

| | Quant Shadow Dashboard | Phorec |
|---|---|---|
| Source SHA | dashboard worktree `61d86b43` (orca/shv1-dashboard) | FX worktree `f8bb2b73` (orca/fx-rangefade-2m-shadow-v1) |
| Bundle | `.worktrees/prospective-shadow-v1/dashboard/dist/Quant Shadow Dashboard.app`, binary sha256 `939387ec2bcad877…` (cũ `a67229d3…` giữ tại `dist_prev_20260924-0810Z`) | `~/Applications/Phorec.app`, binary sha256 `e6af66fccc644ac2…` (cũ giữ tại `~/Applications/Phorec-prev-20260924-150714.app`; build stage trả lời `--check` trước khi thay) |
| Visual QA | **PASS** — screenshot thật: LIVE, 4 sleeve, BANDRIDGE hiện FLAT "0 fill" + banner fail-closed (không bao giờ giả RUNNING), BASISLV DATA BLOCKED, tổng 399,347.12 = đúng tổng 4 sleeve | **PASS** — screenshot thật ×2: LIVE (paper), "Daemon sống", 1 TK $100k chung, 2 sleeve FLAT mark tươi sub-giây, countdown 16:00 VN, chart equity render |
| Tests | engine 236 passed + app 57 passed | 26 passed (gồm 3 regression dtype mới) |
| Lưu ý | owner tự mở/đóng app nhiều lần trong phiên (exit 0, workers untouched) — tách app/worker là thiết kế, đã verify | tab-click QA bị gián đoạn do owner đang dùng máy; nội dung tab đã verify qua API cùng trang |

## 3. Lỗi gốc đã sửa (kèm test trước/sau)

1. **FX daemon chết ở mốc H1 đầu tiên** (đã chết từ 06:00Z, và thực ra
   chưa bao giờ sống qua 1 giờ kể từ khi cycle mở — 4 thế hệ crash trong
   daemon.log). Gốc: seed parquet `datetime64[ms,UTC]` + bar append
   `datetime64[ns,UTC]` → `pd.concat` hạ cột `ts` về object → `.dt` của
   engine frozen chết. Sửa ở mép nạp (`seed_bars`), lossless; test
   trước 26 fail-đường-crash (chưa có test dtype) → sau 26/26 pass với
   3 regression mới; daemon thật qua 2 mốc H1 (08:00Z partial — công
   bố, 09:00Z hoàn chỉnh) + restart SIGTERM replay sạch. Commit
   `f8bb2b73`.
2. **BANDRIDGE 0 fill — nguyên nhân đến exception gốc**: sizing dùng
   giá ref (`w*equity/ref`) còn guard tiền mặch buy yêu cầu
   `qty*fill_price + fee ≤ cash` với fill = ref + 1 tick + fee 0.05% →
   weight 1.0 cần ≈ 100,050.02 > 100,000 → `InsufficientCashError` →
   fail-closed trung thực, KHÔNG phải bug sizing qty (cùng target với
   book 0- phí fill đúng 1.0 — đã chứng minh bằng test). **Không tự
   sửa** vì đổi exposure cần quyền owner: regression pin 2 chiều
   (commit `12540ebe`) + packet quyết định
   `OWNER_DECISION_PACKET_bandridge_sizing_and_fill_law.md` (A/B/C cho
   sizing, A/B cho luật mốc fill "H4 open vs bar 15m" — mục a8062b1a).
3. **Identity manifest BANDRIDGE thiếu chuẩn byte-level** (không có
   sha256/byte_len/blob; label verdict là chuỗi tổng hợp nhưng không
   được công bố): hoàn thiện theo đúng chuẩn 3 family sáng lập + công
   bố label_kind=composite với từng thành phần pin-byte + policy
   not-rewritable phủ đủ 4 label (commit `28d923b2`). Verifier mở rộng
   trung thực: path `.worktrees/*` resolve theo gốc main checkout.
4. **Hiển thị**: `anchor_note` vẫn ghi "300,000" sau khi constant đổi
   400k (commit `3bf495b7`); test engine pin 3-sleeve → đồng bộ 4-sleeve
   với phép cộng xác minh lại từ byte.
5. **Diff chưa commit tiếp quản được bảo toàn và commit đúng provenance**:
   valuation FAMILY_ORDER +BANDRIDGE (đã là code production đang chạy
   từ 08:11 local — commit `302d5f52`); artifact A7 phiên trước
   (`887deb71`); caps map key verbatim `max_abs_weight` (additive,
   `236bf2f7`).

## 4. Kiểm toán độc lập & toàn vẹn ledger

- **A7 fresh-context: VERDICT CONFIRM** (artifact đính kèm) — 5/5 nhóm
  xác nhận: diff scope, 78 tests rerun, manifest re-hash khớp, ledger
  0 event_id trùng + 56 fill khớp đúng luật chi phí đóng băng,
  arithmetic 2,033 điểm khớp, status semantics trung thực. 3 finding
  đều non-blocking; xử lý: journal rows legacy 1–15 GIỮ NGUYÊN
  (append-only), không churn code sau CONFIRM (option cải thiện ghi
  lại cho owner), mark-gap BANDRIDGE đã được banner công bố đúng.
- **Xác minh độc lập của người sửa code** (trước A7): 2,031 điểm
  combined-history so với byte thô: 1,981 khớp tuyệt đối, 50 gap
  fail-closed equity=null, 0 lệch; bất biến ngày mount
  `pnl = end − start − 100,000` residual = 0.0; baseline 300,000 +
  flow 100,000 BANDRIDGE @ 09-24T01:10Z — đúng mốc thời gian.

## 5. Đã xong vs còn chờ

**Đã xong**: cả 2 lỗi gốc chính (FX daemon, BANDRIDGE nguyên nhân +
regression), identity 4 family đạt chuẩn byte, hiển thị trung thực,
2 app rebuild + QA trực quan, restart/kill semantics, audit A7 CONFIRM,
ledger append-only nguyên vẹn.

**Còn chờ thị trường / nguồn / owner** (ghi đúng NOT_RUN/BLOCKED, không
có gì bị "chạy hộ"):
- BANDRIDGE 12:00Z hôm nay và các mốc H4 tiếp theo — nếu breakout nổ,
  quyết định sẽ fail-closed cho tới khi owner chọn A/B/C trong packet.
- XSECT daily 09-25T00:00Z; ILLIQ + BASISLV weekly 09-28T00:00Z
  (BASISLV chỉ PASS khi nguồn còn liền mạch tại thời điểm quyết định —
  hiện có mọi dấu hiệu tốt).
- FX: cadence H1 tiếp diễn (đã chứng minh 2 mốc; soak tiếp tục).

## 6. Kết luận thẳng

**HAI APP ĐÃ CHUẨN VỀ MẶT CÔNG CỤ + HẠCH TOÁN**: mở được, hiển thị đúng
và trung thực (không số nào không truy được artifact; FAIL-CLOSED hiển
thị thành FAIL-CLOSED), số khớp byte ledger tuyệt đối, worker sống sót
restart và mất feed, không broker/order/credential, test suite xanh
toàn diện, audit độc lập CONFIRM.

**Nhưng chương trình shadow chưa "xong" theo nghĩa bằng chứng
prospective**: gate tổng là **PARTIAL** — BANDRIDGE chỉ mới có 1 quyết
định OK dạng no-trade (đường fill weight-1.0 chờ quyết định owner trong
packet), BASISLV chờ sự kiện weekly 09-28 với nguồn đã lành, các mốc
daily/weekly còn lại chưa tới lịch. Không sự kiện nào bị backfill hay
"chạy hộ".
