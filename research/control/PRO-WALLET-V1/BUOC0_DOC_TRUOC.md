# BƯỚC 0 — GHI CHÚ ĐỌC TRƯỚC (PRO-WALLET-V1)

Ngày: 2026-11-05. Người viết: agent chính (Mac). Mục đích: đủ điều kiện mở Giai đoạn 1 theo prompt chủ V2.

## Đã verify (bằng chứng)

- Repo input `Zedlchoke/edge-hunt-ai-desk` clone về `.my-quantitative-data/PRO-WALLET-V1/input-edge-hunt-ai-desk`, checkout detach đúng commit `10d3eb7ff9495b2c5b309e9a05ff889f79ca3d80`.
- `shasum -a 256 -c MANIFEST.sha256`: **57/57 OK, 0 lệch**.
- 3 file pack hash khớp pin của chủ: ke-hoach `6196d282…`, spec D2 `06e204d2…`, mẫu kiểm toán `8eaaaa5e…`.
- Spec copytrade v2 (FILE `docs/polymarket-copytrade-20-SPEC-V2-FROZEN.md` trong clone `~/Downloads/Polymarket`): sha256 `ae504a97feb50204c7028644f78bfd0d1728b8d3f0c9b7a52d0dfb64cbee55d8` — khớp `ae504a97…bee55d8`. Pin theo FILE, không pin HEAD (HEAD clone đang `86a31b2e`, còn di chuyển vì Việc 3).

## Ghi chú từng file

**1. Kế hoạch gốc (NBA+WNBA, 101 dòng).** Lớp ý kiến ví pro = mắt thứ 4, shadow 1 tháng, không thay đường chính (model + giá Polymarket + cổng AI DeepSeek). Reset 00:00 UTC mỗi ngày; ý kiến hôm qua không mang sang; danh sách ví pro đóng băng cả tháng, chọn TRƯỚC khi thấy kết quả. Định nghĩa pro (đề xuất, chủ chốt cuối): ≥30 lệnh/6 tháng, lời ròng dương, tổng tiền đặt ≥5.000 đô, loại ví sàn/market-maker/ví mới, tối đa 30 ví. Ngưỡng ý kiến (đề xuất): ≥3 ví cùng phía + ≥60% tiền pro → "ủng hộ đặt"; pro ngược hướng bàn → "cảnh báo bỏ"; còn lại "không có ý kiến". Sổ bóng riêng, 1 dòng/trận. Chấm sau 1 tháng: 4 nhóm, đo paper PnL + win rate + CLV; <30 trận có ý kiến → THIẾU DỮ LIỆU. Kế hoạch gốc chỉ NBA+WNBA — prompt chủ V2 mở rộng toàn bộ giải có dữ liệu (việc của PLANNER GĐ2). Rủi ro đã ghi: 1 người nhiều ví, dữ liệu trễ, pro đặt dẫn dụ. Lưu ý thời gian: cửa sổ chấm D2 kết thúc ~9/11; build nên bắt đầu sau báo cáo D2.

**2. Spec D2 gate invariant (103 dòng, ĐÓNG BĂNG).** Luất: mọi dòng BET_PAPER phải có opinion binding hợp lệ (ai_gate object + candidate_hash + ALLOW + file opinion production khớp hash/match/verdict/digest + model DeepSeek-only); thiếu → TỪ CHỐI GHI, ứng viên về PENDING_AI, gate_event mã lý do; shadow opinion KHÔNG BAO GIỜ tính. Battery T1–T7; phán xét forward 14 ngày 0 vi phạm. Lane này KHÔNG đụng sổ D2, không đụng cổng AI, không sửa luật — chỉ đọc để hiểu đường chính khi so sánh ở GĐ6.

**3. Mẫu kiểm toán độc lập (101 dòng).** 5 ô điền mỗi lần (dự án+bước / spec đóng băng + hash / báo cáo agent + hash / code+dữ liệu gốc / verdict agent tuyên bố) — điền TỪ FILE GỐC, không từ tóm tắt chat. Auditor chỉ đọc, tự tính lại ≥1 phần quan trọng, trả lời 3 câu (đúng chưa / cố hết sức chưa / còn đường hợp lệ không), verdict CONFIRMED / BUG FOUND / SPEC FLAW (hoặc CHƯA ĐỦ BẰNG CHỨNG — không được CONFIRMED), ký file rồi DỪNG — auditor không có quyền GO. Dùng cho GĐ3 và GĐ5.

**4. Spec copytrade v2 FROZEN (160 dòng).** Pool từ quét thị trường kỷ nguyên B (T0 2025-09-13 → T1 2025-12-12), KHÔNG dùng leaderboard. Gamma `/markets?include_tag=true`, xác minh `gameStartTime`, thị trường hợp lệ: tag 'Sports' + sportsMarketType + trận đơn + trước trận + không mùa vụ. Sàng ≥10.000 USD giao dịch đoạn 1 (LUẬT, đo từ trade, cấm volumeNum cuối, cấm lọc theo lãi/PnL). Trades `taker_only=false`, giữ ts trong đoạn, checkpoint. Etiquette: ~200 request/ngày, 10 giây/request, 429/403/throttle → DỪNG không tăng tốc. Khả dụng cho lane này: endpoint Gamma/data-api, luật thị trường hợp lệ, etiquette request, kinh nghiệm offset-cap 2100 (HTTP 422 → bisection theo end_date).

**5. Trạng thái listing (Việc 3, đang chạy).** 49.748 id duy nhất / 15.013 hợp lệ = CẬN DƯỚI, chưa xong, còn ~3 ngày @200 request/ngày (preflight 06/11 đã commit). Trần 200/ngày CỘNG DỒN mọi tiến trình → GĐ4 của lane này XẾP HÀNG theo mặc định (a) của chủ.

## Kết luận Bước 0

Đủ 4 đầu vào, hash khớp, không có gì bịa. Mở Giai đoạn 1 (RESEARCHER, subagent riêng).
