# TASK A5 — Ops tối thiểu (v2)

> Bạn là agent A5 trong sprint 24h (xem PLAN.md). Làm việc CHỈ trong worktree này,
> branch `wt/ops-reporting`. Scope đã bị A1 thu hẹp — đúng 2 deliverable.

## Deliverable 1 — `scripts/status_report.py`
- Gom JSON mới nhất trong `results/` (forward_test, scan_matrix/*/report.json,
  tradfi snapshot nếu có) → in 1 bảng markdown ngắn gọn:
  mục | ngày | chỉ số chính | trạng thái.
- Chạy < 5s, không cần network. Python:
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.

## Deliverable 2 — `python main.py status`
- Thêm subcommand `status` vào `main.py` gọi script trên (in ra stdout).
- Không đổi hành vi các subcommand hiện có.

## Test
- Thêm ít nhất 1 pytest cho status_report (fixture JSON nhỏ → assert dòng bảng).

## Hoàn thành & bàn giao
- Commit lên branch `wt/ops-reporting`, KHÔNG tự merge.
- PR description: "Đã làm / Không kịp / Rủi ro".
- Xong sớm thì DỪNG, hỗ trợ A4 nếu được yêu cầu (đọc data giúp, không tune).
