# TASK A2 — Data & Forward-test pipeline

> Bạn là agent A2 trong sprint 24h (xem PLAN.md). Làm việc CHỈ trong worktree này,
> branch `wt/data-pipeline`. KHÔNG đụng file YAML params chiến lược. KHÔNG gỡ guard LIVE.

## Mục tiêu
Forward-test W2 chạy sạch bằng 1 lệnh; phát hiện sớm bẫy skip-im-lặng của W1.

## Việc 1 — Test tái hiện bẫy overlap (H0–H2)
- Đọc `scripts/weekly_forward_test.sh` và NOTES.md §12.
- Viết test (pytest) mô phỏng: catalog đã có bar đến thời điểm T, script phải
  fetch từ T+buffer chứ không fetch chồng lấn, và PHẢI fail-loud/log rõ khi
  `bars_written == 0` trong khi sàn có bar mới hơn T.

## Việc 2 — Cứng hoá fetch step (H2–H6)
- Sửa phần Python inline trong `weekly_forward_test.sh`: sau khi download, in rõ
  số bar mới theo symbol; nếu 0 bar mới nhưng `now - last_bar > 1h` thì exit 1
  với thông báo lỗi rõ ràng (không âm thầm pass).

## Việc 3 — Chạy W2 forward test (H6–H10) — ƯU TIÊN CAO, chạy sớm nhất có thể
```bash
cd /Users/hoangminhlong/my-quantitative-wt/data-pipeline
/Users/hoangminhlong/my-quantitative/.venv/bin/python scripts/... # hoặc ./scripts/weekly_forward_test.sh
```
- Dùng python tuyệt đối: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
- Artifact JSON vào `results/forward_test/` (local), copy artifact cuối về
  `/Users/hoangminhlong/my-quantitative/results/forward_test/`.

## Việc 4 — Bảng log W2 (H10–H12)
- Thêm bảng W2 vào cuối NOTES.md (mục mới "## 19. Forward test W2") dạng:
  Trades | Exp | PF | PnL | Ghi chú thị trường. **KHÔNG rút kết luận tune.**

## Hoàn thành & bàn giao
- Commit lên branch `wt/data-pipeline`, KHÔNG tự merge vào main.
- Cuối ca append vào PR description: "Đã làm / Không kịp / Rủi ro".
- Tiêu chí: script chạy 1 lệnh không lỗi; test overlap pass; W2 có artifact;
  bảng W2 được điền.
