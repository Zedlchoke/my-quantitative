# COST BOOK PROPOSAL — DTP-CX-SOLUSDT-C1 (Lane COST, draft)

- Lane: **cost-execution-auditor (COST)** · Date: 2026-09-27 · Worktree
  `.worktrees/dtp-cx-solusdt-c1/integration`, branch
  `orca/dtp-cx-solusdt-c1-integration`, HEAD `9ba72e6cd2b28a039791cc6a6f75e8ac10ef1cb2`.
- Trạng thái: **PROPOSAL DRAFT — chưa frozen**. Freeze chỉ tiêu thụ khi council
  chấp nhận và toàn bộ caveat được khai nguyên văn vào freeze artifact.
- Lane này **KHÔNG thấy PnL**; mọi số dưới đây đến từ census/funding stats của
  sibling TERMINAL `PWS-CX-SOLUSDT-C1` (read-only) + quy ước DECLARED của plan.
- File máy: `cost_book@draft.json`, `CEILING_POWER_TEMPLATE.json`,
  `spread_repro_2023-05.json` (cùng thư mục).

## 0. Kết luận một dòng

Chi phí RT (round-trip) của identity taker intraday 1m trên SOLUSDT:
**in-window đo được ~11.9 bps (p50), out-window declared 12 bps; thang stress
1.5×/2.0× = 17.9–18.0 / 23.8–24.0 bps** — trong băng declared 11–13 bps của
plan I002. spread census của PWS **tái tạo được từ bytes thô** (MATCH — xem §1).

## 1. Tái lập census spread (nhiệm vụ INHERIT + RE-VERIFY)

- Nguồn: zip bookTicker 2023-05 (zip nhỏ nhất, 353,545,384 bytes) — sha256
  `394fa34c…00f8a` **khớp INVENTORY.md** của PWS trước khi chạy.
- Phương pháp stream (1 core, 55s, không extract ra disk, <0.1 GB temp):
  stride 1-in-K, K=13, offset 0, chronological;
  `spread_bps = (ask−bid)/((ask+bid)/2)×1e4` trên `transaction_time` (ms, UTC);
  percentile nội suy tuyến tính.
- So với census committed (`C1_machine_SPREAD_CENSUS_SOLUSDT.json`, month
  2023-05):

| Đại lượng | Máy (PWS) | Lane COST | Phán |
|---|---|---|---|
| Số dòng dữ liệu | 27,234,787 | 27,234,788 | +1 = dòng trống cuối stream; trừ 1 khớp **exact** |
| Sampled n | 2,094,971 | 2,094,983 | +12 (5.7e-6 rel) — cùng họ warm-up ≤K đã disclose ở PWS gate §3.3 |
| invalid sampled | 0 | 0 | MATCH |
| **max spread** | 96.86896223169141 | 96.86896223169141 | **BIT-EXACT** |
| first/last sampled tt | 11:49:49.824 / 23:59:59.922 | 11:49:49.353 / 23:59:58.925 | lệch ≤1.0 s (sách warming), đúng pattern đã disclose |
| p50 theo giờ | 24 blocks | **bit-exact 16/24**, 8 blocks lệch ≤3.7e-5 bps | MATCH (không material) |
| p25 / p75 theo giờ | 24 blocks | exact 20/24 và 16/24; lệch ≤9.3e-5 / ≤1.5e-4 bps | MATCH |
| p99 theo giờ | 24 blocks | exact 0/24; lệch tối đa **0.379 bps** (h03, trên p99 ~1.04 bps) | thứ tự thống kê p99 nhạy với ±13 dòng warm-up ở giờ đuôi dày — đã disclose, không đổi kết luận cost |

**Phán quyết: MATCH** (với residual bookkeeping đã disclose). Census PWS là
hàm thật của bytes thô; lane COST dùng nó làm MEASURED authority mà không cần
re-process 12 GB. Số liệu dùng chung: pooled n=13,805,136; p25 0.109 / **p50
0.469** / p75 0.515 / p99 2.350 / mean 0.442 bps.

**Đo mới từ chính lần tái lập này** (không có trong census committed):
median mid giá 2023-05 = **$20.3505**; p90 pooled tháng = 0.519 bps
(p90 theo giờ 0.516–0.526). Giá này cho **measured bound về tick geometry**:
spread p50 0.469 bps ≈ $0.00095 — bất khả thi với tick 0.01 USDT (4.91 bps);
grid ≤ 0.001 USDT (0.049 bps/tick) mới nhất quán với data. tickSize chuẩn
contract **chưa có artifact trên disk** (`NOT_RUN`) — xem blockers.

## 2. Sách chi phí theo lớp (master §7 binding)

### (a) Fee — DECLARED

- Taker **5 bps/mặt + 1 adverse tick/mặt** — quy ước frozen CHR3F, master §7
  binding (Q-8: chỉ lên lớp MEASURED khi validate vs fills thật).
- RT fee = 2×5 = **10 bps**.

### (b) Funding — MEASURED (dual-book), kế thừa PWS

Stats đo được (SOLUSDT, fapi H1+H2 một campaign — **không được gọi là
dual-source verified**; `cross_check_vision: NOT_RUN`):

| Stat | Giá trị |
|---|---|
| n settlements | 6,580 (2020-09-13T16:00Z .. 2026-08-21T16:00Z; đuôi 10.3 ngày chưa phủ) |
| median / settlement | 8.5755e-05 (= **0.858 bps**) |
| mean / settlement | 1.3762e-06 (= 0.0138 bps) |
| **negative share** | **28.62%** (down-trend state: 3,354 settlements, 40.28%) |
| **worst** | **−0.02 (−200 bps/settlement)** tại 2022-11-09T20:00:00.018Z (tuần FTX) |
| max | +0.00332469 (+33.25 bps) tại 2021-02-10T08:00Z |
| cadence | 101 spacing ≠8h gói trong 2022-11-09..11-18 — **path accounting phải dùng timestamp thật, không dùng grid 8h** (binding) |

- **Book A (native path)**: funding per-settlement đo được bám timestamp thật
  dọc path nắm giữ.
- **Book B (frozen-constant stress)**: hằng số frozen **−200 bps/settlement**
  (worst đo được của SOL, sâu hơn hằng −0.30%/8h của master — đó là hằng dòng
  BTC; dùng measured-worst là conservative và có nguồn đo).
- Với identity 1m-horizon: funding kỳ vọng/RT ≈ (2/480)×0.0138 ≈ **1e-4 bps**
  — không đáng kể; đuôi FTX-class là cái book B phủ. Funding-adjacent identity
  đã bị đại diện bởi level-window chết (autocorr dấu +0.853, P-29 — plan §2.4).

### (c) Spread — MEASURED theo giờ fill (in-window) + DECLARED ×1.5/×2.0 (out-window)

In-window = 6 tháng census (2023-05, 07, 09, 11, 2024-01, 03 — toàn bộ cửa sổ
keyless đo được 2023-05..2024-04). Bảng p50 theo giờ UTC (pooled, bps) lấy từ
`pooled_by_hour` của census committed:

| Giờ UTC | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| p50 | 0.478 | 0.471 | 0.460 | 0.461 | 0.461 | 0.456 | 0.454 | **0.437** | 0.448 | 0.454 | 0.454 | 0.453 |

| Giờ UTC | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| p50 | 0.472 | 0.480 | 0.484 | **0.486** | 0.481 | 0.483 | 0.479 | 0.468 | 0.462 | 0.464 | 0.467 | 0.454 |

- Biên p50 theo giờ: 0.437 (h07) .. 0.486 (h15); p99 theo giờ: 1.57 (h05) ..
  3.89 (h00). Giờ US (13–18 UTC) rộng và dày nhất.
- **p90 theo giờ cho cả 6 tháng: NOT_RUN** — census committed chỉ công bố
  p25/p50/p75/p99; tính p90 đủ 6 tháng cần re-stream ~12 GB (vượt ngân sách
  lane). Bù: p90 tháng 2023-05 đo được ở §1 (pooled 0.519 bps) làm demo; stress
  trong-window dùng p99 công bố + multiplier.
- **Out-window** (fill ngoài 6 tháng census): băng declared **0.5 bps** (số
  declared của plan I002) × **1.5 / 2.0**, nhãn bắt buộc
  `FILL_QUALITY_CLASS_declared` (A7-F8). Các tháng 2020-09..2023-04 và
  2024-05..2026-08 là **UNKNOWN_WIDER** — cấm cost ở pooled p50 (cảnh báo
  regime đo được: 2024-03 p50 ≈ 0.068 vs 2023-05 ≈ 0.492 bps — lệch ~7× ngay
  trong window).

### (d) Thang chi phí RT — identity taker intraday 1m

Quy ước (khai nguyên văn): RT = 2×fee(5) + 2×full-spread (quy ước plan I002:
spread bị cross ở cả 2 mặt) + 2×adverse tick (declared 0.5 bps/tick theo băng
11–13 của plan; conservative vs measured geometry 0.049 bps/tick — xem §1);
fee 10 bps cố định; funding 1m ~1e-4 bps (bỏ qua, tail book riêng).

| Kịch bản | RT (bps) | ×1.5 | ×2.0 |
|---|---|---|---|
| In-window MEASURED (p50 pooled 0.469) | **11.92** | 17.88 | 23.84 |
| In-window theo giờ p50 (0.437..0.486) | 11.87–11.97 | 17.81–17.96 | 23.75–23.95 |
| In-window p99 stress (2.350) | 15.70 | — | — |
| Out-window DECLARED (0.5 bps spread) | **12.00** | 18.00 | 24.00 |
| Băng declared binding của plan (11–13) | 11–13 | 16.5–19.5 | 22–26 |

⇒ Số declared 11–13 bps của plan I002 được xác nhận bởi measured ladder
(11.92) — band declared giữ làm **binding envelope** (conservative).

### (e) Gap / outage / latency — DECLARED

- **Venue outage**: band declared, precedent "outage 418" 2026-09-21 — khai
  theo dispatch packet; lane này **chưa định vị được artifact precedent trên
  disk** (verification `NOT_RUN` — xem blockers, không chặn vì đây là lớp
  DECLARED). Stress ×1.5/×2.0 áp cho band outage tại scoring.
- **Weekend: NONE** (crypto 24/7). Precedent measured: 120 bar 1h mất
  (2022-02-26..28 = 72; 2022-04-01..02 = 48) — cửa sổ maintenance venue thật.
- **Latency**: band DECLARED, số cụ thể pin tại freeze của từng identity
  (Q-4 delay-pair sub-hour).

### (f) Hai lệnh cứng

- **Maker-only: FORBIDDEN** tới khi queue-position đo được (master §7).
- **Unlevered 1x**: levered/borrow/liquidation-model BLOCKED ⇒ mọi arm 1x.

## 3. Ceiling × Power grid (P-29 — một dòng kill)

Template máy: `CEILING_POWER_TEMPLATE.json`. Mọi identity frozen phải điền
**trước PnL**:

```
net_bps/RT(mult)  = θ_gross_bps/RT − RT_cost_bps(mult),   mult ∈ {1.0, 1.5, 2.0}
VETO (K-COST)     ⇔ net ≤ 0 ở BẤT KỲ mult nào        (dạng strict theo plan I002)
K < 100 RT        ⇒ INCONCLUSIVE (không bao giờ PASS); reference PF≈1.3 ⇒ n≈236
```

Ví dụ minh họa **EXAMPLE-NOT-FROZEN** (I002, RT declared 12 bps): θ=15 ⇒
net +3.0/−3.0/−9.0 ⇒ **VETO strict**; chỉ θ ≥ 25 mới sống cả 3 multiplier.
Chi tiết đầy đủ trong template.

## 4. BLOCKERS (không đo được hôm nay + owner action mở chốt)

| # | Hạng mục | Lớp | Owner action để mở |
|---|---|---|---|
| 1 | Commission thật (maker/taker, BNB discount) trên Vision data — census bookTicker không chứa commission | NOT_MEASURED | Cấp fee schedule + đối chiếu fills thật (R1-style); hoặc owner duyệt giữ DECLARED vĩnh viễn cho paper-tier (Q-8) |
| 2 | Queue position | NOT_MEASURED | Cấp nguồn L2/queue (không có keyless); trước đó maker-only giữ FORBIDDEN |
| 3 | Slippage ngoài touch (depth) | NOT_MEASURED | Stage archive partial-book depth cho window hẹp được duyệt, hoặc duyệt study aggTrades-vs-quote |
| 4 | Spread 2020-09..2023-04 và 2024-05..2026-08 (56/72 tháng corpus) | BLOCKED (keyless 404) | Authorize nguồn có key hoặc windows hẹp do cost auditor duyệt như measured-band có công bố |
| 5 | Funding cross-check Vision | NOT_RUN (PWS) | Stage Vision `fundingRate_um_SOLUSDT` zips (nhỏ); luật xung đột row-diff ⇒ EXCLUDED đã armed |
| 6 | Coverage quote/aggTrades/mark-index trên plane 1m/15m mới (bắt buộc cho I002) | PENDING — data gate DTP chưa chạy | Chạy data gate của DTP tại GO-1 (mục 2.2–2.4 plan child) |
| 7 | tickSize SOLUSDT (contract spec) | NOT_VERIFIED_ON_DISK | Capture exchangeInfo snapshot (keyless) — 1 request, pin sha |
| 8 | Precedent "outage 418" 2026-09-21 | DECLARED, artifact chưa định vị | Owner trỏ đường dẫn evidence ở cycle gateway |
| 9 | BNBUSDT spread census | NOT_RUN_DISK_CONSTRAINT (program-level, ~25GB vs 6.1GiB free) | Giải phóng disk hoặc duyệt census cửa sổ hẹp |

## 5. Ghi chú sử dụng

- Mọi row scoring phải mang nhãn: `FILL_QUALITY_CLASS_<measured|declared>`,
  `PROXY_NOT_ORDERBOOK` (khi liên quan), `SINGLE_VENUE_PANEL`,
  `FUNDING_PATH_STRESSED`, `ANCESTRY_EXPOSED_DEV` (dev 1m/15m).
- Cost book này là **input cho F-5 (cost-survivability ceiling)** qua grid §3;
  ceiling âm ⇒ `VETO_K_COST` pre-PnL, không cứu.
- Toàn bộ caveat của PWS data gate (§2/§3/§6) là **điều kiện binding**, kế
  thừa nguyên văn.

— Lane COST (cost-execution-auditor), 2026-09-27.
