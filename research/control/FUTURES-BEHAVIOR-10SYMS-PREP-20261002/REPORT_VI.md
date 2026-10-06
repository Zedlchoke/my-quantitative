# Báo cáo ELI5 tiếng Việt — FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (2026-10-02)

## Tóm tắt 1 đoạn
Owner đưa 1 framework nghiên cứu + 10 file từng mã (NQ ES CL NG GC SI 6E 6J 6B 6A). Chúng tôi đã snapshot nguyên bản (kèm hash), tạo worktree riêng, cho 10 nghiên cứu viên riêng (mỗi mã một người) + 1 lane viết code backtest + 1 lane lập kế hoạch mua dữ liệu, chạy song song. Kết quả: 10 dossier hoàn chỉnh, bộ code backtest 147 test PASS (140 gốc + 7 regression close-only sau audit; chạy trên dữ liệu giả lập, KHÔNG chạy chiến lược thật), bản nháp kế hoạch backtest, bản spec mua dữ liệu, và 1 audit độc lập A7. **Chưa có backtest nào chạy, chưa tốn tiền mua gì, chưa đăng ký gì** — đúng phạm vi prep owner yêu cầu.

## Hôm nay làm được gì (không cần thêm gì)
- Nghiên cứu hành vi daily trên chuỗi front "volume thật" ~14-16 tháng của cả 10 mã; giá tham chiếu sâu 2019-nay (loại settlement-derived đã khai báo).
- Đo được: cấu trúc curve/carry từng mã, vol, spread proxy, lịch sự kiện verify từ nguồn chính (EIA, CFTC, BoJ, BoE, RBA, BLS, MOF Nhật) kèm URL + ngày truy cập.
- Đặc biệt: 6J là năm MOF can thiệp tỷ giá kỷ lục 2026 (xác nhận từ mof.go.jp); SI có regime squeeze-crash +217%/−31%; CL backwardation dốc toàn bộ cửa sổ đo.

## 3 phát hiện quan trọng nhất
1. **Quy tắc roll khai báo bị hỏng theo nhiều cách khác nhau ở 9/10 mã**: FX + SI phải roll theo chuỗi quý HMUZ (serial là "sổ chết" — có ngày serial 26 lots vs quarterly 118,886); NG thì front hết giao dịch TRƯỚC ngày 1 tháng đáo hạn nên quy tắc vô hiệu; ES/NQ/GC/6A roll sớm 4-9 phiên trong khi sổ cũ vẫn dày gấp 3-7 lần.
2. **Snapshot thiếu các hợp đồng serial đã hết hạn** (GC 6, 6J 8, 6B hết, 6A 6) — sửa $0 nhưng **có thời hạn**: cửa resolve hợp đồng hết hạn ~1 năm, mấy serial già nhất sẽ "age out" khoảng Q1-2027. Owner cần quyết định re-fetch sớm.
3. **S6 đo spread SI/6A trên sổ serial chết** → con số đúng trên sổ thanh khoản: SI ~$100/hợp đồng (không $112.5 trên serial), 6A $10 (không $20). Phí sàn 9/10 mã vẫn NOT_FETCHED.

## Muốn backtest thật thì cần gì (owner quyết)
1. Re-fetch serial (free, gấp) + thử useRTH=false để có phiên overnight/Globex (free).
2. Chọn 1 trong 3: (a) mua lịch sử vendor (spec Databento đã soạn: BẮT BUỘC chạy probe miễn phí Phase-0 trước khi tiêu tiền — không bịa giá); (b) tích lũy prospective; (c) chấp nhận backtest 14 tháng với chi phí khai báo.
3. Khai báo slippage + phí sàn 9 mã, lịch lễ thật, đóng băng bộ luật R.

## Backtest xong dữ liệu phải qua gate nào
Code đã dựng và test luật: PIT không nhìn tương lai, roll chỉ dùng thông tin quá khứ, giá CL âm, quy đổi 6J, tick rounding, TP+SL cùng bar = AMBIGUOUS_ORDER (không bịa thứ tự), chi phí ×1/1.5/2, walk-forward có purge/embargo, cấm cộng PnL từng leg thành marginal. Trước khi chạy scored: phải đăng ký budget/freeze + GO của owner theo luật workspace. BACKTEST_LAUNCH_DRAFT.md là NHÁP, không tự cấp GO.

## Trạng thái phiên
- 14/14 handoff COMPLETE = 12 lane (10 dossier + engine + data) + A7 audit + lane FIX-A7-FINDINGS (sửa số đếm 2026-10-02, vòng co-owner-review-fix-1 — commit message của Lead đếm nhầm "13"). Bản gốc giữ nguyên từng byte trong dispatch/archive_attempt1/; bản thay thế dạng canonical được kiểm bằng script dispatch/validate_handoffs.py 14/14 (MCP validator NOT_RUN trong phiên này — chỉ bằng chứng dạng script). A7 audit độc lập: audit/A7_AUDIT.md + handoff_A7.json.
- 0 scored, 0 PnL/event-study/rule-sweep, 0 mua hàng, 0 credential, 0 merge/push. Worktree prep/futures-behavior-10syms-20261002, mọi artifact untracked trong namespace task để owner duyệt.
