# C2_EXPOSURE_VERIFICATION — SRLV-CX-C1 (Phase C2)

- Đối chiếu registry (`plans/CYCLE_REGISTRY.json` @ d3f063a0) +
  HYPOTHESIS_LEDGER + MAP với corpus staged tại C1. Mục đích: phân loại
  exposure từng pair × plane × window; chọn vai trò dev/OOS hợp pháp.

## Bảng verification

| Pair × plane × window | Bằng chứng registry/ledger | Phân loại | Vai trò được phép |
|---|---|---|---|
| BTCUSDT 1h 2020-01..2026-08 | BTC-H4 ×4 (trục giá 2020–2026); PSV1; ETH-V1/V2 E1 input; CHR3F baselines | `OUTCOME_EXPOSED` | dev `ANCESTRY_EXPOSED_DEV` (kill/engineering) + ancestry disclosure; KHÔNG OOS |
| ETHUSDT 1h 2020-01..2026-08 | ETHUSDT-OPEN-SEARCH-V1 terminal (8 cells); V2 lane B 4 scored cells; ETHBTC ratio G6 | `OUTCOME_EXPOSED` | như BTC; KHÔNG OOS; KHÔNG đụng S1/phrase của ETH-V2 (đang sống) |
| SOLUSDT 1h 2020-09..2026-08 | chỉ xsect baselines (V11/V14/funding-carry) | `OUTCOME_EXPOSED_baseline` | dev với disclosure; không tự động OOS |
| BNBUSDT 1h 2020-02..2026-08 | như SOL | `OUTCOME_EXPOSED_baseline` | như SOL |
| BTCUSDT 15m 2024-08..2026-08 | CHR3F staged+scored trên window đó | `OUTCOME_EXPOSED` | không dùng |
| ETHUSDT 15m 2024-08..2026-08 | cùng lịch sử giá 1h đã exposed (V1/V2 lane B) | `ANCESTRY_EXPOSED_RECLK` | không tạo surface sạch; chỉ `ANCESTRY_EXPOSED_DEV` nếu staged |
| Plane 15m/1m khác (chưa stage) | cùng lịch sử giá đã exposed | `ANCESTRY_EXPOSED_RECLK` (re-clock veto Q-3) | KHÔNG phải OOS; chỉ `ANCESTRY_EXPOSED_DEV` |
| Funding series (4 cặp) | đo bởi nhiều cycle (ETH 7,305 floor-exact; BTC 7,643) | cost-authority data | cost book measured; không phải surface signal |

## Kết luận OOS (binding)

- **KHÔNG window lịch sử nào của 4 cặp ở plane 1h được dùng làm sealed/OOS**
  — toàn bộ outcome-exposed ở cấp lịch sử giá (mức độ exposure khác nhau:
  search đầy đủ vs baseline, đều đủ để cấm dùng làm OOS chọn lọc).
- Một history window chỉ được one-look nếu chứng minh chưa-exposed ở cấp lịch
  sử giá — với 4 cặp này, sau verification: **không có**. Do đó OOS của cohort
  = **prospective accumulation sau freeze** (D13/D26/D52) đúng CX plan C5 và
  trackb §4.2 precedent. `ETHUSDT-OPEN-SEARCH-V2` S1 (sealed, của cycle đó)
  không thuộc cohort này, không tiêu.
- Window seam 2026-08-31..freeze = `SEAM_CONSISTENCY_ONLY` (parity/PIT check,
  không chọn lọc).

## Dev fold contract (mặc định đưa vào council, pin tại freeze)

F1 2020-01(-09/-02 floor từng pair)..2021-04-30 · F2 2021-05-01..2022-12-31 ·
F3 2023-01-01..2024-12-31 · F4 2025-01-01..2026-08-31. Force-flat mọi fold
boundary; mọi số dev mang `ANCESTRY_EXPOSED_DEV`.

**C2 verdict: PASS (với kết luận "history OOS = không có; OOS = prospective").**
