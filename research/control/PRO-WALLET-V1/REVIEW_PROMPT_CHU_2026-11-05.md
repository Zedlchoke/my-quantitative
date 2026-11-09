# REVIEW LUẬT ĐÓNG BĂNG — PROMPT CHỦ "LỚP Ý KIẾN VÍ PRO CHO PAPERDESK"

- Ngày: 2026-11-05. Người review: Mac agent (vai lead), theo yêu cầu trong chính prompt: "Prompt này CHƯA ĐƯỢC PHÉP CHẠY. Lead phải review luật đóng băng trước khi chạy."
- Phạm vi: chỉ review. Không chạy giai đoạn nào. Không lấy dữ liệu. Không sửa file nguồn, sổ cũ, code PaperDesk.
- Repo: /Users/hoangminhlong/my-quantitative, branch `main`, HEAD `d2575fe22e9b5db774427472b8cd90181fa54d0c`. Tree bẩn chỉ gồm file untracked của chủ trong `research/control/` và `.my-quantitative-data/` — đúng mô hình vận hành hiện hữu, không phải lỗi chưa giải thích.

## 1. Trạng thái đo được (re-measure)

- Lock heavy toàn máy: FREE_PROVEN (không ai giữ, flock free). Lệnh: `researchctl locks inspect`.
- Registry `plans/CYCLE_REGISTRY.json`: 99 TERMINAL, 18 PAUSED_MAINTENANCE (chủ archive 2026-10-31), 37 ACTIVE_LIGHT.
- Không có cycle "PRO-WALLET" hay lớp ví pro nào trong registry → không trùng lane.
- 37 lane ACTIVE_LIGHT đều là họ PaperDesk/sports paper — đúng hướng chủ "giữ PaperDesk". Lane mới không đụng đến chúng.

## 2. Kiểm tra 4 đầu vào Giai đoạn 0

| Đầu vào | Trạng thái | Bằng chứng |
|---|---|---|
| Kế hoạch gốc `ke-hoach-lop-y-kien-vi-pro-nba-wnba-2026-11-05.md` | **THIẾU — không tìm thấy trên đĩa** | Đã find trong repo, `~/workspace`, `~/Downloads`: 0 kết quả |
| Spec D2 `SPEC_D2_GATE_INVARIANT_2026-10-26.md` | CÓ, hash khớp | `research/control/PAPERDESK-FIXALL-NCAA-V1/`, sha256 `06e204d2…7f47e32` khớp sidecar byte-đối-byte |
| Spec copytrade v2 đóng băng | CÓ, hash khớp | `~/Downloads/Polymarket/docs/polymarket-copytrade-20-SPEC-V2-FROZEN.md`, sha256 `ae504a97feb50204c7028644f78bfd0d1728b8d3f0c9b7a52d0dfb64cbee55d8` = đúng chuỗi chủ ghi `ae504a97…bee55d8` |
| Báo cáo đếm listing copytrade v2 | CÓ | `docs/polymarket-copytrade-20-VIEC3-COUNT-REPORT.md` + interim 11-04, 11-05. Trạng thái: listing CHƯA xong, còn ~3 ngày chạy @200 request/ngày, cận dưới 49.748 id duy nhất / 15.013 hợp lệ |

## 3. So khớp prompt với luật đóng băng

Những điểm prompt KHÔNG vi phạm luật (khớp CLAUDE.md / AGENTS.md / handbook):

- 0 đồng chi tiêu, không tài khoản mới, chỉ đặt giấy → khớp lệnh cấm orders/purchases.
- Không sửa model dự báo, cổng AI, sổ D2, không ép lệnh → khớp ranh giới lane.
- Kiểm toán Giai đoạn 3 và 5 bằng agent khác, không tự audit → khớp luật A7 độc lập (handbook §12.3).
- Mỗi giai đoạn có cửa chặn, thiếu bằng chứng thì NOT_RUN/THIẾU DỮ LIỆU → khớp evidence-first.
- Giai đoạn 7 CẤM, cần spec + hash + kiểm toán CONFIRMED + GO riêng của chủ → khớp P-8 (GO chỉ gõ tại cổng riêng của nó).

## 4. Phát hiện cần chủ quyết

**F1 — BLOCKER Giai đoạn 0: thiếu file kế hoạch gốc.**
Prompt ghi "chủ chuyển file, hoặc lead chuyển". Lead không thể tự tạo file này. Không có nó thì ghi chú đọc không đủ điều kiện mở Giai đoạn 1.
→ Cần: chủ chuyển `ke-hoach-lop-y-kien-vi-pro-nba-wnba-2026-11-05.md` vào repo (đề xuất `research/control/PRO-WALLET-V1/`).

**F2 — BLOCKER chung cho Giai đoạn 1 và 4: tranh nhau trần 200 request/ngày Polymarket.**
Trần 200 request/ngày là cộng dồn mọi tiến trình (luật Việc 3, commit a74a382). Việc 3 đếm listing copytrade v2 vẫn đang chạy hằng ngày (preflight ngày 06/11 đã commit, còn ~3 ngày). Nếu lane này cũng gọi Gamma API trong ngày đó thì vượt trần chung.
→ Cần chủ chọn 1 trong 2: (a) xếp hàng — lane này chờ Việc 3 xong (~08–09/11) rồi mới bắt đầu request; (b) chia trần — ghi rõ lane này được bao nhiêu request/ngày và Việc 3 giảm xuống tương ứng. Không có lựa chọn nào thì mặc định (a) xếp hàng.

**F3 — CẦN CHỈNH PIN HASH: `ae504a97…bee55d8` là sha256 của FILE spec, không phải HEAD repo.**
Clone `~/Downloads/Polymarket` (origin Zedlchoke/polymarket) đang ở HEAD `86a31b2e…`, đã đi qua nhiều commit sau đóng băng (Việc 3 đang sửa code). Mọi bước "kiểm tra hash spec trước khi chạy" phải hiểu là: sha256 của `polymarket-copytrade-20-SPEC-V2-FROZEN.md` == `ae504a97feb5…bee55d8`. Không pin theo HEAD repo được vì repo còn di chuyển.

**F4 — THIẾU TRƯỚC GIAI ĐOẠN 3: mẫu prompt kiểm toán 5 chỗ trống của chủ.**
Đã grep repo + Downloads/Polymarket/docs: không tìm thấy. Không chặn Giai đoạn 0–2, nhưng không có mẫu thì Giai đoạn 3 không mở được.
→ Cần: chủ chuyển mẫu hoặc chỉ đường dẫn.

**F5 — GHI CHÚ Giai đoạn 6: lane bóng cần đăng ký đúng quy trình.**
Giai đoạn 0–5 chỉ tạo văn bản trong `research/control/PRO-WALLET-V1/` (vùng chủ, đúng tiền lệ PAPERDESK-FIXALL-NCAA-V1 — không cần cycle registry). Giai đoạn 6 chạy worker 1 tháng trong worktree/branch mới `paperdesk-pro-wallet-shadow-v1` → lúc đó phải qua /worktree-dispatch và ghi cycle vào `plans/CYCLE_REGISTRY.json`. Ghi trước để khỏi quên.

## 5. Kết luận review

- Thực chất prompt KHÔNG ngược luật đóng băng: đúng hướng "giữ PaperDesk", paper-only, có cửa chặn, audit độc lập, cấm áp dụng đường chính.
- Nhưng CHƯA ĐƯỢC MỞ CỦA CHẠY: còn 2 blocker (F1 thiếu kế hoạch gốc; F2 tranh trần request với Việc 3) và 1 pin hash cần chỉnh (F3).
- Lead không chạy bất kỳ giai đoạn nào cho đến khi chủ gỡ F1 và chọn phương án F2.

---

"Giai đoạn 0 (đọc trước) CHƯA xong. Làm được: review luật đóng băng, verify hash 2 spec, đo lock/registry, xác nhận không trùng lane. Chưa làm được: đọc kế hoạch gốc (thiếu file), ghi chú đọc. Cửa tiếp theo: chủ chuyển file kế hoạch gốc + chọn phương án trần request (xếp hàng hay chia), rồi Giai đoạn 0 mới bắt đầu."
