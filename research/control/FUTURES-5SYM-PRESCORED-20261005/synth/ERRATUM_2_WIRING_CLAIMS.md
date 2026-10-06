# ERRATUM 2 — thu hẹp claim wiring wave-3 (append-only, trước fix)

- Round: FUTURES-5SYM-PRESCORED-20261005 wave-4 intake. Không sửa file cũ,
  không rút giá trị phần đúng đã verify.

## Claim bị thu hẹp

1. **"19 adapter đã nối hoàn chỉnh" (REPORT_VI wave-3, freeze_wiring handoff):**
   chỉ đúng ở mức binding + bằng chứng accounting synthetic cho các trường
   đơn giản. Owner-audit tại `d938e9a5` + repro của controller (file kèm,
   `freeze_wiring/repro_mixed_direction/REPRO_FAIL.json`) chứng minh seam
   positional **làm mất leg Short** khi một identity có nhiều intent khác
   hướng: `compile_identity_group` chọn arm theo `intents[0]["direction"]`
   (`spec_compiler.py:345`) và runner `compute_all` chỉ tạo 1 trade
   positional/identity → 2 intent (Long 2023-06-14 + Short 2023-06-15, cùng
   identity) cho **1 trial row thay vì 2** (repro exit 0, verdict FAIL, qua
   đúng production path intent_contract → compiler → UNMODIFIED runner CLI).
   Các test wave-3 không bắt được vì mỗi identity chỉ dùng 1 intent/1 hướng.
2. **"Giữ semantics thời gian/folds":** encoding positional
   `[signal, entry, filler, exit]`, `hold_bars=2`, fold `F-COMPILED` là
   **accounting test encoding**, không chứng minh timeline/folds/warmup của
   strategy thật được giữ nguyên.
3. **"Canonical integration":** `CANONICAL_INTEGRATION.md` là documented
   sequence — chưa phải code integration đã triển khai + test.

## Giá trị không bị rút

Binding 19 adapter tồn tại thật; 21 wiring test + 343 kiểm tra của round vẫn
đúng trong phạm vi chúngassert (đơn hướng, đơn intent); các bằng chứng
PIT/era/direction/isolation không phụ thuộc bug này.

— Hết ERRATUM 2 (kèm FAIL artifact; fix triển khai sau commit này).
