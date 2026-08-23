# TASK A3 — Safety guards (scope thu hẹp v2)

> Bạn là agent A3 trong sprint 24h (xem PLAN.md). Làm việc CHỈ trong worktree này,
> branch `wt/quality-safety`. KHÔNG sửa logic production — chỉ THÊM test.

## Mục tiêu duy nhất: chứng minh không có đường nào tới live tiền thật

1. Đọc `main.py`, `config/settings.py`, `config/live*.yaml`, các entry point
   chạy live. Liệt kê mọi đường dẫn có thể đặt lệnh.
2. Viết pytest chứng minh với `enable_trading: false`:
   - Không order nào được submit qua mọi entry point.
   - Chặn cả đường vòng: env var override, config merge sau load, CLI flag
     (nếu tồn tại đường nào bypass được → BÁO NGAY cho A1, đây là bug nghiêm trọng,
     không tự vá logic production).
3. Nếu phát hiện guard thiếu sót: ghi vào `research/audit_live_guards.md`
   (mô tả + cách tái hiện), KHÔNG tự sửa code production.

## Hoàn thành & bàn giao
- Commit lên branch `wt/quality-safety`, KHÔNG tự merge.
- PR description: "Đã làm / Không kịp / Rủi ro".
- Tiêu chí: ≥1 test chứng minh LIVE bị chặn; audit report liệt kê đủ đường dẫn;
  full suite xanh (`/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/ -q`).
