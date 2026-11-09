# AUDIT KE_HOACH_V2 — GIAI ĐOẠN 3 (AUDITOR-1 ĐỘC LẬP), LANE PRO-WALLET-V1

## KẾT LUẬN (1 dòng, đầu file)

**CONFIRMED — ĐÃ XÁC NHẬN** (đối tượng là BẢN KẾ HOẠCH chưa chạy; verdict gốc của PLANNER GĐ2: KHÔNG CÓ verdict sống/chết — file tự ghi "BẢN KẾ HOẠCH V2 — CHƯA DUYỆT, CHƯA ĐÓNG BĂNG, CHƯA CHẠY"). Kế hoạch khớp luật đầu vào đã đóng băng, không tự mâu thuẫn ở mức luật/ngưỡng/cổng, không có rò rỉ tương lai, tính lại độc lập khớp ở 2/3 phần đo chính; 1 lệch nhỏ trong ước ngân sách (dòng mô tả, không phải luật) được ghi rõ ở mục Tính lại và mục Phát hiện phụ, không đổi verdict.

---

## 5 Ô ĐIỀN (theo mẫu chủ, điền từ FILE GỐC đã tự mở)

**1. Dự án và bước cần kiểm toán:** PRO-WALLET-V1 — Giai đoạn 2: PLANNER viết bản kế hoạch V2 cho lớp ý kiến ví pro chạy bóng (shadow) trên toàn bộ giải có dữ liệu. File: `/Users/hoangminhlong/my-quantitative/research/control/PRO-WALLET-V1/KE_HOACH_V2.md`, sha256 tự tính `61188913b9e0bb8b9a176807a65b35a07ce12c5c0c413c781e4db7d1710c5d59` (khớp sidecar, khớp GATE_LOG, khớp handoff GĐ2).

**2. Spec đã đóng băng để đối chiếu:** Bước này KHÔNG có MỘT spec đóng băng riêng của lớp ví pro (kế hoạch gốc tự ghi "BẢN KẾ HOẠCH, chưa đóng băng, chưa chạy" — dòng 3; KE_HOACH_V2 tự ghi "CHƯA ĐÓNG BĂNG" — dòng 4). Thân bài luật đối chiếu gồm 3 lớp, phân biệt rõ file-có-hash và văn-bản-lệnh:
   - **(a) Prompt chủ V2 ngày 2026-11-05** (mở rộng phạm vi toàn bộ giải có dữ liệu; trần 200 cộng dồn; phương án xếp hàng mặc định (a); GĐ7 cấm): là VĂN BẢN LỆNH TRONG CHAT — KHÔNG phải file, không tự tính hash được. Nội dung của nó được phản chiếu bởi 2 file trên đĩa đã tự mở và hash: `BUOC0_DOC_TRUOC.md` (sha256 `1c9db6a7bfd37821b1616dbb473122b491c7f5f884f0cdcbc885192a15d790bb`, khớp số GATE_LOG ghi) và `REVIEW_PROMPT_CHU_2026-11-05.md` (sha256 `94d24decd279cdb74ff93bee75ee52788ba618600434dae8ec162fdd5f29f5da`, chứa nguyên văn F2 "mặc định (a) xếp hàng", F3 pin theo FILE, F5 cycle registry GĐ6).
   - **(b) Kế hoạch gốc** FILE `ke-hoach-lop-y-kien-vi-pro-nba-wnba-2026-11-05.md`, sha256 tự tính `6196d282b68b631d799a5b6036111e07eac414517be3674a70444001679d887d` — khớp pin `6196d282…` của chủ (verify Bước 0). Chưa đóng băng nhưng là đầu vào bất biến theo pin; mọi lệch phạm vi của V2 so với nó phải ghi lý do (V2 mục 0.4 đã ghi).
   - **(c) Spec copytrade v2 FROZEN** FILE `/Users/hoangminhlong/Downloads/Polymarket/docs/polymarket-copytrade-20-SPEC-V2-FROZEN.md`, sha256 tự tính `ae504a97feb50204c7028644f78bfd0d1728b8d3f0c9b7a52d0dfb64cbee55d8` — KHỚP CHÍNH XÁC chuỗi pin `ae504a97…bee55d8` (đóng băng 2026-11-03; nguồn luật etiquette request + luật thị trường hợp lệ + luật chống rò rỉ tương lai mà V2 kế thừa).
   - Tham chiếu thêm: spec D2 gate invariant FILE sha256 tự tính `06e204d297a4273c116c669232695114a5d67b2192c19f8f93d5d34547f47e32` — khớp `06e204d2…` mà V2 mục 0 ghi (chỉ tham chiếu đường chính, không đụng).

**3. Báo cáo của agent đã làm việc:** (i) `KE_HOACH_V2.md` (hash ở ô 1); (ii) `handoffs/HANDOFF_GD2_PLANNER.json`, sha256 tự tính `417620842d437db56e1704df61b32c4c0f4cf594817d9704f13c7c9878da60e1`, schema `zcode_orch_v3_handoff@1`, status DONE — nội dung khớp file KE_HOACH_V2 (không khác nhau giữa chat và file gốc theo đối chiếu của tôi).

**4. Code và dữ liệu gốc của bước:** KHÔNG CÓ CODE — GĐ2 chỉ viết kế hoạch, chưa build, chưa chạy (tự ghi ở dòng 4; xác nhận bằng việc không có artifact nào của lane trên đĩa: `.my-quantitative-data/PRO-WALLET-V1/` chỉ chứa clone input, `research/control/PRO-WALLET-V1/` chỉ chứa văn bản + handoffs, không có thư mục `shadow/`, không có request log). Dữ liệu gốc đã đối chiếu: `NGHIEN_CUU_GIAI_DOAN1.md` (sha256 `61b6f68e6bef008fe11e2687f0235013008e6263900ecb0fffd0909648468f17` — khớp số V2 mục 0 ghi); `BUOC0_DOC_TRUOC.md`, `GATE_LOG.md` (sha256 `946c31930e763a3908365cea4e1061c848cb25c04bf63110e360f04e048b780c`), `REVIEW_PROMPT_CHU_2026-11-05.md` (các hash ở ô 2); bản đồ WSL `/Users/hoangminhlong/.my-quantitative-data/sports-polymarket-cutover-prep-v1/` (journal + live/gamma_events, chỉ đọc — đã tự đếm lại, thấy mục Tính lại); repo input `edge-hunt-ai-desk` detach HEAD `10d3eb7ff9495b2c5b309e9a05ff889f79ca3d80` — đúng commit chủ giao, working tree sạch.

**5. Verdict mà agent đã làm việc tuyên bố:** KHÔNG CÓ verdict sống/chết — ghi đúng chữ file: "BẢN KẾ HOẠCH V2 — CHƯA DUYỆT, CHƯA ĐÓNG BĂNG, CHƯA CHẠY" (dòng 4 KE_HOACH_V2); handoff ghi status "DONE" (hoàn thành việc VIẾT KẾ HOẠCH, không phải verdict chạy). Mọi ngưỡng trong file đều dán nhãn "SỐ ĐỀ XUẤT — chờ chủ chốt".

---

## DANH SÁCH FILE ĐÃ MỞ (hash tự tính bằng shasum -a 256) VÀ FILE KHÔNG MỞ ĐƯỢC

| # | File | sha256 tự tính | Khớp với |
|---|---|---|---|
| 1 | `research/control/PRO-WALLET-V1/KE_HOACH_V2.md` (đối tượng kiểm toán) | `61188913b9e0bb8b9a176807a65b35a07ce12c5c0c413c781e4db7d1710c5d59` | sidecar `.sha256` ✓, GATE_LOG ✓, handoff GĐ2 ✓ |
| 2 | `research/control/PRO-WALLET-V1/KE_HOACH_V2.md.sha256` | (sidecar chứa hash ở dòng 1) | ✓ |
| 3 | `research/control/PRO-WALLET-V1/NGHIEN_CUU_GIAI_DOAN1.md` | `61b6f68e6bef008fe11e2687f0235013008e6263900ecb0fffd0909648468f17` | số V2 mục 0 ghi ✓, GATE_LOG ✓ |
| 4 | `.my-quantitative-data/…/pro-wallet-pack/ke-hoach-lop-y-kien-vi-pro-nba-wnba-2026-11-05.md` | `6196d282b68b631d799a5b6036111e07eac414517be3674a70444001679d887d` | pin chủ `6196d282…` ✓ — kế hoạch gốc KHÔNG bị sửa |
| 5 | `.my-quantitative-data/…/pro-wallet-pack/PROMPT_AGENT_KIEM_TOAN_DOC_LAP_MOI_LAN.md` | `8eaaaa5e22c01e7ab0386fdb53fa9b994ed8a9efa2855471d19aced6900096da` | số V2 mục 10 ghi (`8eaaaa5e…`) ✓, BUOC0 ✓ |
| 6 | `~/Downloads/Polymarket/docs/polymarket-copytrade-20-SPEC-V2-FROZEN.md` | `ae504a97feb50204c7028644f78bfd0d1728b8d3f0c9b7a52d0dfb64cbee55d8` | pin `ae504a97…bee55d8` ✓ — spec CHƯA BỊ SỬA sau đóng băng |
| 7 | `.my-quantitative-data/…/pro-wallet-pack/paperdesk-spec-d2-gate-invariant-2026-10-26.md` | `06e204d297a4273c116c669232695114a5d67b2192c19f8f93d5d34547f47e32` | số V2 mục 0 ghi ✓ |
| 8 | `research/control/PRO-WALLET-V1/BUOC0_DOC_TRUOC.md` | `1c9db6a7bfd37821b1616dbb473122b491c7f5f884f0cdcbc885192a15d790bb` | số GATE_LOG ghi ✓ |
| 9 | `research/control/PRO-WALLET-V1/GATE_LOG.md` | `946c31930e763a3908365cea4e1061c848cb25c04bf63110e360f04e048b780c` | — |
| 10 | `research/control/PRO-WALLET-V1/REVIEW_PROMPT_CHU_2026-11-05.md` | `94d24decd279cdb74ff93bee75ee52788ba618600434dae8ec162fdd5f29f5da` | — |
| 11 | `research/control/PRO-WALLET-V1/handoffs/HANDOFF_GD2_PLANNER.json` | `417620842d437db56e1704df61b32c4c0f4cf594817d9704f13c7c9878da60e1` | — |
| 12 | `research/control/PRO-WALLET-V1/handoffs/HANDOFF_GD1_RESEARCHER.json` | `382e0f6b7b6dbec51ea955472fdab836de863dd1216c35adae65dd2d8956d6e5` | — |
| 13 | WSL journal `journal_wsl_lane_2026-11-05T131729Z.jsonl` (trong `~/.my-quantitative-data/sports-polymarket-cutover-prep-v1/journal/`) | ghi URL `events?tag_id=105959&closed=false` + snapshot_path + sha256 `1f110577…` | — |
| 14 | WSL snapshot `live/gamma_events/wsl_tag_p00_2026-11-05T131729Z.json` | `1f1105777688ba7aad8f24ff9fdb53314dbbeb0be9bd69cb06f3e83e56f23010` | sha256 ghi trong journal (dòng 13) ✓ |
| 15 | Repo input `.my-quantitative-data/PRO-WALLET-V1/input-edge-hunt-ai-desk` | HEAD (git) `10d3eb7ff9495b2c5b309e9a05ff889f79ca3d80`, detach, tree sạch | commit chủ giao ✓ |

Spot-check bằng chứng nguồn (mở đọc từng dòng được GĐ1 viện dẫn): `polymarket-copytrade-20-VIEC3-COUNT-REPORT.md` (dòng 13, 18, 19, 49, 57), `…VIEC3-FIX-INTERIM-2026-11-05.md` (dòng 10, 31–32, 38), `…VIEC-B-C-REPORT-V1.md` (dòng 15–20, 24–25), `…PROBE-REPORT-V2.md` (dòng 77–92) — đều tồn tại với nội dung như GĐ1 trích (chi tiết ở bảng đối chiếu).

**File không mở được: KHÔNG CÓ.** Ghi chú minh bạch: prompt chủ V2 gốc là văn bản lệnh trong chat, không phải file trên đĩa — tôi không tự hash được nó; kết luận về nội dung prompt chủ chỉ dựa trên 2 file phản chiếu đã hash (BUOC0, REVIEW_PROMPT) + trích nguyên văn trong dispatch, không dựa vào tóm tắt.

---

## BẢNG ĐỐI CHIẾU TỪNG LUẬT

Luật đánh số L1–L22. "V2" = KE_HOACH_V2.md; "gốc" = kế hoạch gốc; "spec v2" = copytrade SPEC-V2-FROZEN.

| # | Luật đầu vào (nguồn) | V2 làm gì | Đúng/Sai + bằng chứng |
|---|---|---|---|
| L1 | Spec v2 đóng băng không bị sửa (pin FILE ae504a97…) | V2 mục 6.5: trước mỗi phiên kiểm sha256 FILE đúng chuỗi pin; "Pin theo FILE, không pin HEAD repo (F3)" | ĐÚNG — hash tự tính khớp; trùng khuyến nghị F3 của REVIEW_PROMPT |
| L2 | Trần ~200 request/ngày CỘNG DỒN mọi tiến trình, 10 giây/request (spec v2 dòng 69, 100; VIEC3 interim dòng 10) | Mục 6.2: đếm 3 nguồn (Việc 3, worker WSL, lane này) trước mỗi phiên; nguồn không kiểm chứng được → KHÔNG CHẠY; mục 6.3: trần lane 120, tổng ≤ 200; mục 6.4: 10 giây, 1 tiến trình | ĐÚNG — chặt hơn luật gốc (thêm đếm 3 nguồn + cấm chạy khi thiếu bằng chứng); không có chỗ nào cho phép vượt 200 |
| L3 | 429/403/throttle/chậm bất thường → DỪNG toàn bộ, không tăng tốc bù (spec v2 dòng 101) | Mục 6.6 + mục 7 xử lý lỗi: dừng toàn bộ phiên, ghi Retry-After; mục 11: ngày không đủ trần → NOT_RUN, không chạy bù | ĐÚNG |
| L4 | Xếp hàng sau listing Việc 3 (REVIEW_PROMPT F2: mặc định (a) khi chủ không chọn) | Mục 6.1: không gọi API tới khi Việc 3 xong (bằng chứng interim log) HOẶC chủ chia trần riêng; mục 10/GĐ4a lặp lại | ĐÚNG — đúng phương án (a), giữ cửa (b) cho chủ |
| L5 | Đếm worker WSL đang tiêu request (phát hiện GĐ1 errata: 22 request ngày 05/11) | Mục 6.2(ii): đếm từ journal WSL, chỉ đọc | ĐÚNG — tôi đếm lại: đúng 22 snapshot WSL ngày 05/11 tới 13:17:29Z (chi tiết mục Tính lại) |
| L6 | Nhận diện thị trường thể thao trận đơn: tag 'Sports' đúng chữ + include_tag=true + sportsMarketType ≠ rỗng + gameStartTime ≠ rỗng + trận đơn + không mùa vụ (spec v2 mục 2.1.2/Q1; PROBE-V2 dòng 85–92: 23/23 đúng) | Mục 1 đoạn cuối + mục 7 dòng liệt kê NBA/SOCCER: y hệt luật, có xác minh gameStartTime | ĐÚNG |
| L7 | KHÔNG dùng volumeNum cuối (tương lai) (spec v2 mục 2.2) | Mục 2 điều 4: tổng tiền đặt đo từ trade, "KHÔNG dùng volumeNum cuối"; mục 3 lặp; mục 9.6 lặp | ĐÚNG |
| L8 | Cấm sàng thị trường theo lãi/PnL/kết quả (spec v2 mục 2.2) | Mục 3: "Sàng thị trường của cửa sổ chọn không dựa trên lãi/PnL/kết quả"; mục 7 liệt kê chỉ theo tag/gameStartTime; thu hẹp phạm vi (nếu quá lớn) "theo luật KHÔNG dựa trên lãi" (mục 6 cuối + mục 11) | ĐÚNG — lưu ý: xếp hạng VÍ theo lãi giữ-tới-chốt là yêu cầu của chính kế hoạch gốc (mục 5.3 "Lời ròng dương"), dùng dữ liệu quá khứ đã chốt, không phải sàng thị trường — không vi phạm L8 |
| L9 | Lãi chọn ví chỉ tính thị trường ĐÃ CHỘT trong cửa sổ (spec v2 mục 2.4.2 chống rò rỉ) | Mục 2 điều 3: lãi "giữ-tới-chốt" từ resolutions.payouts micro-USDC, "chỉ tính thị trường đã chốt trước mốc đóng băng; thị trường chưa chốt không tính lúc chọn" | ĐÚNG — kế thừa đúng |
| L10 | Cấm leaderboard làm nguồn chọn ví (spec v2 mục 0 cấm; VIEC-B-C dòng 15–20, 24–25: không có tháng quá khứ, bảng all chứa tương lai) | Mục 3: "Không dùng leaderboard làm nguồn chọn ví (đã chứng minh không có tháng quá khứ; bảng all chứa tương lai)"; mục 9.6 lặp | ĐÚNG — bằng chứng VIEC-B-C tôi đã mở, dòng trích có thật |
| L11 | Chọn ví TRƯỚC khi thấy kết quả; đóng băng cả tháng (gốc mục 5, mục 4) | Mục 3: T_freeze gắn TRƯỚC khi thu thập; cửa sổ chọn [T_freeze−183d, T_freeze); sau đóng băng bất biến, lỗi phát hiện sau chỉ ghi ERRATA, không sửa danh sách, không tính lại ý kiến đã chốt | ĐÚNG — chặt hơn gốc (thêm T_freeze tới giây + ERRATA-only) |
| L12 | Ngưỡng ý kiến ≥3 ví cùng phía + ≥60% tiền pro; ngược hướng bàn → cảnh báo bỏ; không đạt → không có ý kiến (gốc mục 6) | Mục 4: y hệt, thêm định nghĩa phía (token kết cục moneyline), bóng đá 3 phía, cấm ghi đè | ĐÚNG (dán SỐ ĐỀ XUẤT đúng — chủ chốt số cuối) |
| L13 | Reset 00:00 UTC, ý kiến không mang sang ngày sau, danh sách ví cố định cả tháng (gốc mục 4) | Mục 4: cắt ngày 00:00 UTC (07:00 VN), tính lại từ đầu mỗi ngày, cửa sổ fill [00:00:00 UTC, gameStartTime) | ĐÚNG |
| L14 | Sổ bóng riêng, không đụng sổ D2; 1 dòng/trận (gốc mục 7) | Mục 5: 2 file CSV append-only ngoài repo, TUYỆT ĐỐI không đụng sổ D2 (D2 chỉ ĐỌC lúc chấm — mục 0.1); 1 dòng/trận/ngày/file | ĐÚNG — tách 2 file có lý do kỹ thuật hợp lệ (append-only: ý kiến khóa trước trận, kết quả ghi sau chốt) |
| L15 | Chấm 4 nhóm: đồng ý / ngược nhau / pro có ý kiến / pro không có ý kiến; đo PnL giấy + tỉ lệ thắng + CLV (gốc mục 8) | Mục 8: 4 nhóm định nghĩa chặt (nhóm 3 chứa 1, 2 và cả trận bàn không đặt — hợp thức hóa phần chồng lấn vốn có trong gốc), đo đủ 3 chỉ tiêu, kèm 2 kịch bản (theo pro 100 USD giá VWAP; bàn đơn thuần theo sổ D2 chỉ đọc) | ĐÚNG |
| L16 | ≥30 trận có ý kiến mới kết luận; thiếu → "thiếu dữ liệu" (gốc mục 8) | Mục 8: tối thiểu 30 trận MỖI GIẢI, thiếu → THIẾU DỮ LIỆU từng giải, cấm gộp giải này bù giải khác | ĐÚNG — siết hơn gốc theo đúng khuyến nghị hệ quả 1 của GĐ1 mục 4; dán SỐ ĐỀ XUẤT |
| L17 | Lớp chỉ đạt khi nhóm nghe pro lời hơn nhóm không nghe + mẫu đủ + kiểm toán độc lập (gốc mục 8) | Mục 8: lặp đủ 3 điều kiện, thiếu 1 thì không đạt; "Mọi ngưỡng đóng băng trước khi chạy. Không đổi sau khi thấy kết quả" | ĐÚNG |
| L18 | Shadow-only; không thay đường chính; muốn vào đường chính cần spec + kiểm toán + GO riêng (gốc mục 1; prompt chủ: GĐ7 cấm) | Mục 0.1/0.3 + mục 9.3/9.9: SHADOW-ONLY, không sửa model/giá/cổng AI/sổ D2, shadow opinion không bao giờ lọt opinion binding cổng AI (khớp spec D2), GĐ7 CẤM cần spec riêng + CONFIRMED + GO riêng | ĐÚNG |
| L19 | Giấy 100%, 0 đồng, không tài khoản, không lệnh thật (gốc mục 1; spec v2 mục 6 ranh giới) | Mục 0.2 + mục 9.2: lặp đầy đủ, thêm không VPN, không bí mật trong file/log/chat | ĐÚNG |
| L20 | Endpoint kỹ thuật đúng bằng chứng đo thật: Gamma /markets include_tag=true + end_date_min/max + order=id + limit≤100; /events tag_id=105959 (WSL); condition_ids lặp từng mã; trades condition_id + taker_only=false + limit 500, market= bị 400; resolutions payouts micro-USDC + đối chiếu umaResolutionStatus; offset ≥2100 → 422 → bisection (GĐ1 mục 2; VIEC3 dòng 13/18/19/57; PROBE-V1/V2) | Mục 7 bảng endpoint: từng dòng khớp GĐ1/spec; thêm luật "lệch → DỪNG và báo" cho resolutions | ĐÚNG — tôi đã mở VIEC3-COUNT-REPORT và PROBE-V2 đối chiếu từng dòng trích: có thật, đúng nội dung |
| L21 | Phạm vi giải theo dữ liệu: NBA/bóng đá nam/WSL ĐỦ kênh; WNBA nghỉ mùa ~31/10/2026 về ~05/2027; NCAA nam/nữ mới mở 01/11/2026 chỉ thấy ncaa-football (GĐ1 bảng mục 4 + errata) | Mục 1 bảng: NBA/SOCCER/WSL VÀO; WNBA/NCAA NGOÀI — THIẾU DỮ LIỆU, đúng từng lý do; bổ sung giải phải qua 4 bước (bản sửa v3 + đo thật + kiểm toán + lệnh chủ); cấm mở rộng giữa tháng; mốc kiểm tra lại WNBA ~05/2027, NCAA khi ≥5 thị trường trận đơn đo thật | ĐÚNG — lệch phạm vi so với gốc ("Chỉ NBA và WNBA") là theo lệnh chủ mở rộng (BUOC0 ghi rõ), V2 mục 0.4 ghi lý do đúng quy trình |
| L22 | Trình tự còn lại có cửa chặn từng giai đoạn; GĐ6 phải đăng ký cycle + worktree `paperdesk-pro-wallet-shadow-v1` (REVIEW_PROMPT F5); mọi SỐ ĐỀ XUẤT chờ chủ chốt (luật nhãn của prompt chủ) | Mục 10: GĐ3 audit → GĐ4 preflight (DỪNG báo chủ duyệt ngân sách) → thu thập → đóng băng → GĐ5 audit → GĐ6 đăng ký cycle đúng F5; liệt kê đủ 7 nhóm SỐ ĐỀ XUẤT cần chủ chốt; không giai đoạn nào chạy khi chưa duyệt | ĐÚNG |

**Kết quả bảng: 22/22 ĐÚNG. Không tìm thấy chỗ nào V2 hạ ngưỡng đã có luật, nới lọc, hoặc tự cho phép chạy khi chưa duyệt.**

---

## TÍNH LẠI ĐỘC LẬP (3 phần, tự tính, không dùng số của PLANNER)

**Phần 1 — Đếm lại cột schema sổ bóng (khai báo vs thực tế trong file):** trích bảng mục 5 KE_HOACH_V2 và đếm bằng script riêng:
- File A `SO_BONG_Y_KIEN.csv`: khai báo ngầm 19 dòng bảng → tôi đếm được đúng **19 cột**, đánh số 1–19 liên tục không trống (ngay_utc … du_lieu_goc). Khớp câu kết thúc file ("19 cột file ý kiến").
- File B `SO_BONG_KET_QUA.csv`: đếm được đúng **14 cột**, đánh số 1–14 liên tục. Khớp ("14 cột file kết quả").
- Khóa nối (ngay_utc, giai, condition_id) có mặt ở cả 2 file. **KHỚP.**
- Đủ trường chấm 4 nhóm + CLV: y_kien_pro (file A) + y_kien_pro_sao_chep (file B, cấm tính lại) + nhom_phan_diet + ket_qua_tran + quyet_dinh_ban + gia_vao_theo_pro + gia_dong_cua + clv_phan_tram + paper_pnl_usd + paper_thang — kịch bản "theo pro" (100 USD @ VWAP pro) tính trọn từ schema. **ĐỦ cho mục tiêu chấm chính.** Ghi chú giới hạn (không chặn, xem Phát hiện phụ N3/N5): CLV của chính BÀN ở nhóm 4 phải join sổ D2 lúc chấm — kế hoạch cho phép đọc D2 đúng lúc đó (mục 0.1), nên tái lập được.

**Phần 2 — Đối chiếu và đếm lại bằng chứng WSL (claim duy nhất có dữ liệu thô kiểm chứng được):**
- Mở snapshot `wsl_tag_p00_2026-11-05T131729Z.json` (chính snapshot GĐ1 viện dẫn): **35 event**, tất cả `closed: false` — khớp claim "35 event WSL đang mở" của GĐ1 errata và V2 mục 1. Slug đúng dạng `wsl-avl-mnu-2026-11-08`, `wsl-cfc-eve-2026-11-07`… kèm biến thể exact-score/first-to-score/halftime-result đúng như mô tả; sha256 file = `1f110577…` trùng sha ghi trong journal — chuỗi bằng chứng nguyên vẹn.
- Đếm snapshot WSL ngày 2026-11-05 có tên file ≤ 13:17:29Z: **đúng 22** — khớp claim "worker WSL đã fetch 22 request (06:12Z → 13:17Z)" của GĐ1 và số V2 mục 6 viện dẫn. (Hiện tại có 23 vì worker còn sống, fetch thêm 13:32:45Z sau khi GĐ1 chốt — nhất quán với nhận định "worker còn sống".)
- Snapshot đầu tiên `wsl_tag_p00_2026-10-14T015119Z.json` — khớp "liên tục từ 14/10/2026". **KHỚP toàn bộ.**

**Phần 3 — Tính lại ước ngân sách request/ngày chạy bóng theo công thức trong chính kế hoạch (mục 6):**
- Liệt kê: WSL 1 + NBA [2,4] + SOCCER [4,8] = **[7, 13]**.
- Trade: NBA [10,15] trận × [1,2] request = [10,30]; SOCCER [10,30] trận × [1,3] = [10,90]; WSL [2,6] × 1 = [2,6]. Tổng trade = **[22, 126]**.
- Tổng cận theo đúng các khoảng thành phần: **[29, 139]** request/ngày.
- Kế hoạch ghi: "Tổng ước 40–110 request/ngày". **LỆCH**: cận dưới thật 29 (kế hoạch ghi 40, cao hơn 11 — thiên về an toàn), cận trên thật 139 (kế hoạch ghi 110, THẤP hơn 29 — làm nhẹ ngày xấu nhất). Chỉ khôi phục được số 40–110 nếu ngầm giả sử bóng đá trung bình 2 request/trận, trong khi dòng thành phần ghi 1–3.
- Đánh giá ảnh hưởng: đây là dòng ƯỚC MÔ TẢ đã dán nhãn "cận dưới — SỐ ĐỀ XUẤT; GĐ4a preflight đo lại và báo trước khi tiêu", không phải luật. Các luật ràng buộc thật không đổi và an toàn: trần lane 120/ngày + tổng ≤ 200 (mục 6.3), preflight GĐ4a bắt buộc đo lại và DỪNG báo chủ duyệt ngân sách trước khi tiêu (mục 6 cuối + mục 10), ngày không đủ trần → ghi NOT_RUN, không chạy bù (mục 11). Ngày xấu nhất 139 > 120 sẽ bị cắt bởi trần và sinh NOT_RUN theo đúng luật đã có — không mở đường vượt, không đổi kết quả nào đã có (chưa chạy gì cả). Kết luận: lệch số trong dòng mô tả, không đổi verdict, cần sửa chữ khi chủ duyệt (xem Phát hiện phụ N1).

---

## TRẢ LỜI 3 CÂU HỎI BẮT BUỘC

**1. Làm đúng chưa?** ĐÚNG, ở mức yêu cầu của một bản KẾ HOẠCH chưa chạy (khớp luật đầu vào + không tự mâu thuẫn + đủ mục chủ yêu cầu + không tuyên bố kết quả chạy). Bằng chứng: bảng đối chiếu 22/22 luật khớp (mục trên); toàn bộ 6 hash đầu vào tự tính và khớp pin (kể cả spec v2 FROZEN chưa bị sửa sau đóng băng); mọi số liệu dẫn từ GĐ1 đều đối chiếu được với GĐ1 và/hoặc dữ liệu thô (35 event, 22 request, 200/200 Việc 3 — VIEC3 interim dòng 10, còn ~3 ngày — dòng 31–32, EPL mở — PROBE-V2 dòng 80, luật tag 23/23 — PROBE-V2 dòng 90–92, mẫu 23 ví — VIEC3 dòng 49, leaderboard không có tháng quá khứ — VIEC-B-C dòng 15–20). RÒ RỈ TƯƠNG LAI: không tìm thấy — cửa sổ chọn tuyệt đối tách cửa sổ chạy bóng bằng T_freeze gắn trước thu thập; lãi chọn ví chỉ từ thị trường đã chốt trước T_freeze; cấm leaderboard, cấm volumeNum; ý kiến khóa trước gameStartTime; kết quả ghi sau chốt; danh sách đóng băng bất biến, lỗi sau đóng băng chỉ ERRATA. Không có chỗ nào chọn ví theo kết quả/lãi phát sinh sau mốc. Hai lệch nhỏ (ước ngân sách 40–110 vs [29,139]; cách dẫn bằng chứng NBA nén 2 thị trường vào một ngoặc) là lỗi chữ mô tả, không phải lỗi luật — chi tiết ở Phát hiện phụ, không đổi hướng xử lý của bất kỳ giai đoạn nào.

**2. Đã cố hết sức trong luật đóng băng chưa?** ĐÃ ĐỦ. Kế hoạch phủ đủ 11 chủ đề của kế hoạch gốc (phạm vi, định nghĩa pro, reset, tính ý kiến, sổ, chấm, trình tự, rủi ro, câu hỏi chờ chủ) + xử lý đủ 4 hệ quả thiết kế mà GĐ1 mục 4 trao lại (ngưỡng tối thiểu MỖI GIẢI; không dùng leaderboard → gom từ trades; ước ngân sách từng ngày có tính luồng worker WSL; xếp hàng sau Việc 3) + nội dung phản chiếu đủ 5 phát hiện của REVIEW_PROMPT (F2 phương án (a), F3 pin FILE, F5 đăng ký cycle GĐ6). Mọi con số chưa có lệnh chủ đều dán nhãn "SỐ ĐỀ XUẤT — chờ chủ chốt" — không ngưỡng nào bị lén đổi thành luật đã chốt. Không chạy sớm: 0 request API (không có artifact thu thập nào của lane trên đĩa), kế hoạch gốc không bị sửa (hash còn nguyên), không đụng journal WSL (chỉ đọc), không đụng sổ D2. Không bỏ đường hợp lệ nào trong luật cũ: các giải thiếu dữ liệu không bị đóng cửa vĩnh viễn mà có mốc kiểm tra lại định lượng (WNBA ~05/2027 khi có thị trường trận đơn đo thật; NCAA khi ≥5 thị trường trận đơn đang mở đo thật) — đúng dạng "mô tả, chưa chạy".

**3. Còn đường hợp lệ nào không, hay tịt hẳn?** CÒN, và được ghi đúng quy cách. Trong tháng chạy bóng đầu tiên: phạm vi NBA + bóng đá nam + WSL là toàn bộ giải có bằng chứng dữ liệu trên đĩa (GĐ1, đã kiểm chứng lại) — không còn giải nào đủ điều kiện bị bỏ sót. Ngoài tháng: đường WNBA (khi mùa 2027 mở) và NCAA nam/nữ (khi có ≥5 thị trường trận đơn đo thật) là đường hợp lệ theo chính kế hoạch, CHƯA ĐƯỢC CHẠY, chỉ được mô tả, và đã được đóng khung đúng 4 bước (bản sửa v3 + đo thật có snapshot/hash + kiểm toán lại + lệnh chủ) — đây là chỉnh tiếp spec cũ có kiểm soát, không phải spec mới hoàn toàn, cũng không phải nới luật sau khi thấy kết quả (chưa có kết quả nào). Riêng thu hẹp bóng đá nam nếu số thị trường quá lớn: kế hoạch đã trỏ đúng khuôn KHÔNG dựa trên lãi của Việc 3 (spec v2) và giao chủ quyết — không tự ý. Không phát hiện đường hợp lệ nào trong luật cũ bị bỏ qua chưa thử ở giai đoạn lập kế hoạch này.

---

## XỬ LÝ THEO VERDICT (CONFIRMED)

- Verdict của PLANNER GĐ2 (bản kế hoạch đạt yêu cầu của việc lập kế hoạch, chưa có verdict chạy) **từ lúc này mới có hiệu lực**, và chỉ sau khi chủ đọc file kiểm toán này.
- Bước tiếp theo (chủ duyệt KE_HOACH_V2 + chốt từng SỐ ĐỀ XUẤT + mở Giai đoạn 4) **vẫn cần lệnh GO riêng của chủ**. Tôi không ra GO. Kiểm toán này xác nhận kế hoạch KHÔNG LỆCH LUẬT — nó không phải là việc chủ đã duyệt các con số đề xuất.

**Phát hiện phụ KHÔNG CHẶN (đề nghị chủ/PLANNER xử lý bằng chữ ở vòng duyệt — tôi không sửa file):**

- **N1 (ước ngân sách, mục 6):** tổng ghi "40–110" không phải tổng cận của các khoảng thành phần (thật: [29,139], chỉ khớp nếu bóng đá ≈2 request/trận). Ảnh hưởng bị chặn bởi trần 120 + preflight GĐ4a + luật NOT_RUN ngày thiếu trần. Đề nghị sửa dòng thành "29–139 (thành phần), thường ~40–110 nếu bóng đá ~2 request/trận" khi chủ duyệt.
- **N2 (trích dẫn bằng chứng NBA, mục 1):** cụm "(slug `nba-mem-uta-2026-10-26`, mẫu 23 ví/thị trường)" gộp 2 bằng chứng của 2 thị trường khác nhau: slug mem-uta-2026-10-26 là bằng chứng tồn tại (PROBE-V2 dòng 26–27), còn mẫu 23 ví đo trên `nba-sas-dal-2025-10-22` (VIEC3 dòng 49). Cả hai số riêng lẻ đều ĐÚNG; cách gộp kế thừa từ bảng tổng hợp GĐ1 mục 4. Không đổi kết luận ĐỦ kênh của NBA. Đề nghị ghi rõ 2 nguồn khi duyệt.
- **N3 (enum `quyet_dinh_ban`, mục 5 file B):** chỉ có BAN_HOME | BAN_AWAY | KHONG_DAT — thiếu BAN_DRAW nếu sổ D2 có lệnh đặt HÒA trên thị trường bóng đá 3 cửa. Lối thoát đã có trong chính kế hoạch: "không ánh xạ được sổ D2 → ghi NOT_RUN ở trường tương ứng" (fail-closed, đúng bất biến evidence-first). Đề nghị chủ chốt thêm BAN_DRAW hoặc quy tắc ánh xạ tường minh ở vòng duyệt để không mất dòng.
- **N4 (quan sát về GĐ1, không phải lỗi của V2):** errata GĐ1 ghi `journal/` "395 file"; tôi đếm lại hiện 394 (worker chỉ thêm không bớt — khả năng GĐ1 đếm lệch 1). V2 không viện dẫn số này nên không ảnh hưởng kết luận audit lần này; ghi lại để GĐ1 biết nếu cần errata riêng.
- **N5 (một cột PnL vs hai kịch bản, mục 5/8):** `paper_pnl_usd` không ghi rõ thuộc kịch bản nào; kịch bản "theo pro" tính trọn từ các cột còn lại (100 USD, VWAP, kết quả), kịch bản "bàn đơn thuần" lấy từ sổ D2 được phép đọc lúc chấm — không mất tái lập, chỉ nên định nghĩa rõ cột thuộc kịch bản nào khi duyệt.

---

## XÁC NHẬN

Tôi xác nhận đã đọc file gốc, không dựa vào bản tóm tắt chat. Tôi không sửa file nào của bước đó, không chạy lại bước đó để thay kết quả, không áp dụng cơ chế nào vào hệ thống thật. Tôi không gọi bất kỳ request API Polymarket nào trong quá trình kiểm toán (0 request; mọi số liệu lấy từ file trên đĩa). Tôi là agent mới, không phải PLANNER Giai đoạn 2, không phải RESEARCHER Giai đoạn 1. Kiểm toán xong: DỪNG, chờ chủ và coordinator đọc file này; không tự mở Giai đoạn 4.

— AUDITOR-1 (Giai đoạn 3), lane PRO-WALLET-V1, 2026-11-05.

Giai đoạn 3 xong. Làm được: tự mở và tự tính sha256 toàn bộ 15 đầu vào (đối tượng kiểm toán KE_HOACH_V2 61188913… khớp sidecar/GATE_LOG/handoff; spec copytrade v2 FROZEN ae504a97…bee55d8 chưa bị sửa sau đóng băng; kế hoạch gốc 6196d282… còn nguyên; GĐ1 61b6f68e…, spec D2 06e204d2…, mẫu kiểm toán 8eaaaa5e…, BUOC0 1c9db6a7…, REVIEW_PROMPT 94d24dec…, handoff GĐ2 41762084…, repo input HEAD 10d3eb7 detach sạch); đối chiếu 22 luật của thân luật đầu vào (prompt chủ phản chiếu qua BUOC0/REVIEW_PROMPT, kế hoạch gốc, spec v2 đóng băng) với KE_HOACH_V2 — 22/22 khớp, không hạ ngưỡng, không nới lọc, không tự cho phép chạy; kiểm rò rỉ tương lai toàn bộ quy trình chọn-đóng băng-chạy bóng-chấm (T_freeze gắn trước thu thập, lãi chỉ từ thị trường đã chốt trước mốc, cấm leaderboard/volumeNum, ý kiến khóa trước gameStartTime, danh sách bất biến + ERRATA-only) — không tìm thấy rò rỉ; tính lại độc lập 3 phần: đếm cột schema (19/14 khớp), đếm lại bằng chứng WSL từ dữ liệu thô (35 event mở đúng, 22 request ngày 05/11 tới 13:17Z đúng, snapshot đầu 14/10 đúng, sha256 snapshot khớp journal), tính lại ước ngân sách theo công thức kế hoạch (thành phần [29,139] vs ghi "40–110" — lệch dòng mô tả, bị chặn bởi trần 120 + preflight GĐ4a + NOT_RUN, không đổi verdict); trả lời đủ 3 câu hỏi luật kiểm toán với bằng chứng từng câu; ghi 5 phát hiện phụ không chặn (N1 ước ngân sách, N2 trích dẫn gộp 2 thị trường NBA, N3 enum thiếu BAN_DRAW có sẵn lối NOT_RUN fail-closed, N4 đếm journal 394 vs 395 của GĐ1, N5 nghĩa cột paper_pnl_usd); verdict CONFIRMED kèm ghi rõ hiệu lực chỉ tới sau khi chủ đọc và Giai đoạn 4 vẫn cần lệnh GO riêng. Chưa làm được: không kiểm tra được code chạy (GĐ2 chưa có code — đúng bản chất kế hoạch, mã sẽ bị kiểm tra ở GĐ5/GĐ6); không tự tính hash prompt chủ V2 gốc vì đó là văn bản lệnh trong chat, chỉ đối chiếu qua 2 file phản chiếu đã hash; không đo đạc mới bất kỳ số thị trường/ví thật nào (trần 200 đang bận — đúng luật, việc của GĐ4a sau lệnh chủ); không sửa được các lỗi chữ N1–N5 vì auditor chỉ đọc (đề nghị chủ xử lý ở vòng duyệt). Cửa tiếp theo: chủ đọc file kiểm toán này → nếu chấp nhận CONFIRMED, chủ duyệt KE_HOACH_V2 + chốt từng SỐ ĐỀ XUẤT (ngưỡng pro từng giải, ≥3 ví/≥60%, tối đa 30 ví/giải, trần 120/ngày kèm sửa dòng ước N1, ≥30 trận/giải, vị trí sổ bóng, biến thể thị trường, BAN_DRAW N3, nghĩa cột PnL N5) và ra lệnh GO mở Giai đoạn 4 (GĐ4a preflight chỉ chạy sau khi listing Việc 3 xong hoặc chủ chia trần) — áp dụng vào đường chính (GĐ7) vẫn CẤM cho tới khi có spec riêng + kiểm toán CONFIRMED + GO riêng của chủ.
