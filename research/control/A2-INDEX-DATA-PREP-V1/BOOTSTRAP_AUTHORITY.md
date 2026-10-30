# Owner authority — bootstrap only
Nguồn: câu trả lời owner trong chat hiện tại, nguyên văn “A — Duyệt tạo cycle/worktree chuẩn bị”.
Owner đã đọc đề xuất A2-INDEX-DATA-PREP-V1, branch codex/a2-index-data-prep-v1, worktree .worktrees/a2-index-data-prep-v1/integration, plan draft R08. Quyền gồm đăng ký cycle/tạo worktree/hoàn thiện hồ sơ kỹ thuật; không chạy IBKR/count, không đổi R3, không chi tiền hoặc bật bàn.
Bootstrap control commits cục bộ và registry qua researchctl là bước thực hiện quyền này; không push/merge/history rewrite. Base đã đo trước bootstrap: 8461fb814a68e2186946817b04d0b097584df1b7. Các commit tiếp theo là hồ sơ kiểm tra được, không tự tạo quyền execution. Root main chỉ bootstrap/control docs, lane riêng chỉ docs bootstrap lúc này.
Root tracked/index sạch trước bootstrap; untracked có sẵn giữ nguyên theo intake. Không gom source/data/prompt untracked của owner vào commit. Không sửa lane khác hoặc nguồn đã ký.
