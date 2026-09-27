# DATA GATE REPORT — DTP-CX-SOLUSDT-C1 (lane DG, PIT/data auditor)

- Ngày: 2026-09-27T05:55Z. Worktree
  `.worktrees/dtp-cx-solusdt-c1/integration`, branch
  `orca/dtp-cx-solusdt-c1-integration`, HEAD
  `9ba72e6cd2b28a039791cc6a6f75e8ac10ef1cb2` (= dispatch_sha; KHÔNG commit —
  A1 là authority tích hợp).
- Phạm vi: data gate mục 1–4, child plan `plans/PLAN_dtp_cx_solusdt_c1.md` §2;
  master `plans/PLAN_daytrade_playbooks_program_v1.md` §3.3/§3.4/§7 binding.
- Không thấy bất kỳ PnL/outcome nào; không đọc dữ liệu sealed; corpus PWS chỉ
  đọc, không sao chép 12 GB.

## Verdict tổng: **PASS_WITH_DISCLOSURES** — 0 FAIL, 0 BLOCKED_STORAGE

| # | Mục | Verdict | Bằng chứng chính |
|---|---|---|---|
| 1 | INHERIT-VERIFY corpus PWS | **PASS** | `data_gate/C1_machine_INHERIT_VERIFY_SOLUSDT.json` |
| 2 | Stage mới từ Binance Vision | **PASS** | `data_local/vision/MANIFEST_sha256_*.json` (4 file) |
| 3 | Census + PIT seam check | **PASS** | `data_gate/C1_machine_STAGED_CENSUS_SOLUSDT.json` |
| 4a | Coverage quote (bookTicker) | **PASS** (measured = 6 tháng) | PWS INVENTORY + sha re-verify mục 1 |
| 4b | Coverage trade (aggTrades) | **NOT_RUN** (budget) | `data_gate/C1_machine_VISION_PROBE_SOLUSDT.json` |
| 4c | Coverage mark (markPriceKlines) | **PASS** (full-span) | census + manifest mark |
| 4d | Coverage index (indexPriceKlines) | **PASS** (full-span) | census + manifest index |

## 1. INHERIT-VERIFY (tái xác minh bytes plane kế thừa)

Hash sha256 streaming (không copy) đối chiếu `INVENTORY.md` của
PWS-CX-SOLUSDT-C1: **84/84 MATCH, 0 MISMATCH, 0 MISSING** — gồm 72 zip klines
1h (2020-09..2026-08), 4 JSON funding, 6 zip bookTicker, +2 phụ (manifest 1h,
PDF ToU Binance Vision). 12 GB hash trong ~21s. Plane 1h kế thừa: 52,145 bars,
2 cửa sổ bảo trì venue (2022-02-26..28, 2022-04-01..02 = 120 bars thiếu);
funding 6,580 settlements — đã pin sha, mục 3 còn cross-check lại bằng 1m.

## 2. Stage mới (Vision keyless, monthly, um futures)

Đo đĩa TRƯỚC mỗi batch: 6.03 GiB free (floor 5.0 GiB, budget ≤0.5 GB). HEAD
probe trước khi tải: cả 4 dataset đều đủ 72/72 tháng (2020-09..2026-08).

| Dataset | Files | Bytes | CHECKSUM |
|---|---|---|---|
| klines 1m | 72/72 | 113,812,958 | 72/72 MATCH |
| klines 15m | 72/72 | 8,859,502 | 72/72 MATCH |
| markPriceKlines 1m | 72/72 | 66,980,878 | 72/72 MATCH |
| indexPriceKlines 1m | 72/72 | 79,609,457 | 72/72 MATCH |
| **Tổng** | **288** | **269,262,795 (269.3 MB)** | **288/288 MATCH** |

- Disk SAU stage: **5.61 GiB free** (≥ floor 5.0; dư địa 0.61 GiB). Không kích
  hoạt BLOCKED_STORAGE; không phải skip mark/index — cả hai vừa budget.
- Mỗi zip: tải về → tự tính sha256 → fetch `.CHECKSUM` của Vision → so khớp.
  0 trường hợp CHECKSUM thiếu/404. Manifest sha256 tự viết cho từng thư mục
  `data_local/vision/`; state tải lưu `_stage_state.jsonl` (resume-safe).
- Lưu ý đặt tên: Vision dùng cùng mẫu tên `SOLUSDT-<interval>-<tháng>.zip`
  cho cả mark/index; thư mục riêng của lane phân giải; manifest ghi URL gốc.
- **aggTrades KHÔNG tải** (đúng dispatch). HEAD probe 3 tháng mẫu:
  2024-01 = **528,597,302 B** (một tháng đã vượt trọn budget 0.5 GB),
  2025-06 = 173,764,124 B, 2026-06 = 129,853,235 B; ước lượng full-span
  ~20.0 GB ⇒ không thể stage trong budget/disk hiện tại.

## 3. Census + PIT seam (9,609,023 rows staged, 288 files)

| Dataset | Rows | First | Last | Thiếu | Gap events | Trùng key |
|---|---|---|---|---|---|---|
| 1m | 3,128,700 | 2020-09-14T07:00Z | 2026-08-31T23:59Z | 7,200 phút | 2 | 0 |
| 15m | 208,580 | 2020-09-14T07:00Z | 2026-08-31T23:45Z | 480 slot | 2 | 0 |
| mark 1m | 3,125,490 | 2020-09-13T11:58Z | 2026-08-31T23:59Z | 11,552 phút | 8 | 0 |
| index 1m | 3,149,253 | 2020-09-01T00:00Z | 2026-08-31T23:59Z | 5,787 phút | 7 | 0 |

- **Scale guard L-TRACKB1-1**: phát hiện scale **theo từng row** (≥1e14 ⇒ µs)
  trên mọi file. Kết quả: **toàn bộ ms** (không có nhảy µs trong span/product
  này — khác với biến cố spot; guard vẫn đã bắn và được ghi nhận, normalized
  grid trùng raw ms). Không có scale jump giữa các tháng.
- **Grid endpoint**: bar cuối của 2026-08 đúng trong 1 bar so với cuối cửa sổ
  khai báo, ở cả 4 dataset (endpoint_ok=True).
- **Gap census**: gap 1m/15m trùng khớp CHÍNH XÁC 2 cửa sổ bảo trì venue đã
  biết (4,320 + 2,880 phút = đúng 120 bars 1h thiếu của census PWS) — nhất
  quán kế thừa. mark/index có gap publication riêng của venue (lớn nhất
  5,760 phút, 2021-07-23→28); được công bố, KHÔNG vá/interpolate.
- **UTC day boundary**: UTC không DST; liên tục ngày kiểm qua gap census 1-bar;
  không có bất thường lịch ngoài các gap đã liệt kê.
- **Cross-granularity (2024-06)**: 15m == aggregate 1m: **2,880/2,880 khớp**;
  1h kế thừa (PWS) == aggregate 1m: **720/720 khớp** (tol abs 1e-6 / rel
  1e-9) ⇒ plane 1h kế thừa được tái xác nhận bằng bytes của lane này.

## 4. Coverage verdicts (master §3.3 binding)

- **Quote (bookTicker)** — `MEASURED_WINDOW` = ĐÚNG 6 tháng:
  **2023-05, 2023-07, 2023-09, 2023-11, 2024-01, 2024-03** (corpus PWS, đã
  re-verify sha ở mục 1; spread census p50 0.469 bps). Mọi tháng khác của
  2020-09..2026-08 = `DECLARED_BAND`: fill ngoài cửa sổ census tính phí theo
  declared band ×1.5/×2.0 kèm nhãn `FILL_QUALITY_CLASS_declared` — không tự
  ngoại suy measured.
- **Trade (aggTrades)** — `NOT_RUN` (NOT_RUN_STAGE_BUDGET): nguồn có trên
  Vision (probe 200 cả 3 tháng) nhưng 1 tháng 2024-01 đã 528.6 MB > trọn
  budget 0.5 GB; full-span ~20 GB. Không byte nào staged. Theo master §3.3,
  identity nào cần trade tape làm bề mặt đo (I002 lead-lag "chưa adjust")
  vào F-0 với `BLOCKED_DATA` nếu owner không cấp budget riêng — không thay
  proxy. Bytes-needed đã ghi trong verdict JSON.
- **Mark** — `PASS`: full-span measured, gap venue được công bố (cửa sổ gap
  = DECLARED_BAND, không nội suy).
- **Index** — `PASS`: full-span measured (index bắt đầu 2020-09-01, trước khi
  futures listing 2020-09-14), gap được công bố như mark.

## 5. Posture & giới hạn ghi nhận

- License: Binance Vision keyless public archives; PDF ToU đã sha-pin trong
  PWS `licenses/` (`94d6f61a…`). Capture license text riêng từng nguồn ngoài
  ToU chưa làm — ghi là posture note cho cost lane, không chặn data gate.
- Nhãn bắt buộc cho consumer của plane này: `SINGLE_VENUE_PANEL`,
  `PROXY_NOT_ORDERBOOK` (klines không phải orderbook), `ANCESTRY_EXPOSED_DEV`
  (1m/15m là re-clock của 1h — KHÔNG BAO GIỜ OOS), `FILL_QUALITY_CLASS_*`
  theo cửa sổ quote.
- Không commit, không đụng registry/plans/wayfinder/cycle khác; các file
  `cost_execution/`, `council/` trong cycle dir là của lane khác — không đọc
  nội dung ngoài phạm vi, không sửa.

## 6. Bằng chứng (đường dẫn tuyệt đối gốc worktree lane)

```
research/control/DTP-CX-SOLUSDT-C1/data_gate/DATA_GATE_VERDICT.json
research/control/DTP-CX-SOLUSDT-C1/data_gate/C1_machine_INHERIT_VERIFY_SOLUSDT.json
research/control/DTP-CX-SOLUSDT-C1/data_gate/C1_machine_VISION_PROBE_SOLUSDT.json
research/control/DTP-CX-SOLUSDT-C1/data_gate/C1_machine_STAGED_CENSUS_SOLUSDT.json
research/control/DTP-CX-SOLUSDT-C1/data_local/vision/MANIFEST_sha256_klines_1m.json
research/control/DTP-CX-SOLUSDT-C1/data_local/vision/MANIFEST_sha256_klines_15m.json
research/control/DTP-CX-SOLUSDT-C1/data_local/vision/MANIFEST_sha256_markPriceKlines_1m.json
research/control/DTP-CX-SOLUSDT-C1/data_local/vision/MANIFEST_sha256_indexPriceKlines_1m.json
research/control/DTP-CX-SOLUSDT-C1/data_local/vision/_stage_state.jsonl
research/control/DTP-CX-SOLUSDT-C1/data_local/scripts/dg_inherit_verify.py
research/control/DTP-CX-SOLUSDT-C1/data_local/scripts/dg_vision_probe.py
research/control/DTP-CX-SOLUSDT-C1/data_local/scripts/dg_vision_stage.py
research/control/DTP-CX-SOLUSDT-C1/data_local/scripts/dg_census_pit.py
research/control/DTP-CX-SOLUSDT-C1/handoffs/HANDOFF_dg.json
```
