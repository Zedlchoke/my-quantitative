# OWNER DIRECTIVE — 2026-10-02 (verbatim task, preserved)

Nhiệm vụ: kiểm tra và thu thập dữ liệu futures cho đúng 10 mã NQ, ES, CL, NG, GC, SI, 6E, 6J, 6B, 6A. Đây là lane dữ liệu độc lập, không phải lệnh GO nghiên cứu strategy.
Mục tiêu là lấy ngay mọi dữ liệu lịch sử đúng hợp đồng, hợp pháp và đã có quyền truy cập mà môi trường hiện tại cho phép, rồi trả lời từng mã có đủ dữ liệu cho nghiên cứu daily, intraday, và backtest giao dịch futures thực tế hay chưa. Ưu tiên lấy dữ liệu có thể dùng thật; không thay giá futures bằng ETF, spot, hoặc chuỗi liên tục không giải thích được roll.
1. Kiểm tra quyền và trạng thái trước khi làm
- Đọc AGENTS.md, plan áp dụng, CLAUDE.md, HOW_TO_BE_A_LEAD_ENGINEER.md; đo lại CYCLE_REGISTRY, cycle doctor, HEAD/branch/worktree, dirty tree và heavy lock. Dùng lane/worktree riêng đúng authority. Không sửa root checkout của owner hoặc cycle đã TERMINAL.
- Đọc bằng chứng cũ về CME bị chặn và CL/NG CONTFUT: research/control/DAYTRADER-100-V1/OWNER_FRONTIER_STATUS_2026-09-28.md, research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/ibkr_capability_probe_2026-09-30/, plans/PLAN_fx_futures_frontier_v1.md. Đây là bằng chứng quá khứ, phải đo lại; không mở lại cycle cũ.
- Nếu quy trình repo yêu cầu cycle mới, tạo cycle dữ liệu 0/0 scored với kế hoạch và worktree riêng theo đúng cổng quản trị. Chỉ làm kiểm tra/thu thập dữ liệu; không dùng GO cũ.
2. Kiểm tra đủ 10 hợp đồng, từng mã một
- Dùng TWS paper tại 127.0.0.1:7497 với API readonly=True, client ID riêng, nếu cổng còn hoạt động. Không ghi số tài khoản, credential hay API key vào artifact.
- Với từng mã, xác minh secType=FUT, exchange cụ thể, conId, localSymbol, tháng đáo hạn, multiplier, minTick, currency, trading hours, last trade/delivery rules. Phân biệt hợp đồng front, next và hợp đồng đã đáo hạn; thử includeExpired đúng cách.
- Kiểm tra riêng quyền giá live/delayed và quyền HMDS lịch sử. Mã lỗi của quote live không tự động có nghĩa là lịch sử cũng không lấy được.
- Đặc biệt, 6J được niêm yết JPY/USD, không phải USD/JPY; ghi rõ quy ước giá và không đảo chiều âm thầm.
3. Lấy dữ liệu ngay sau khi probe đạt
- Bắt đầu bằng mẫu nhỏ có giới hạn cho mỗi mã: front, next, một hợp đồng đáo hạn gần, một hợp đồng cũ; thử daily TRADES, hourly, 1-minute và bid/ask nếu có. Ghi chính xác dữ liệu nào là trade, settlement, bid/ask hay quote delayed.
- Sau đó tải theo từng lô có pacing, ưu tiên lịch sử daily của từng hợp đồng có ngày đáo hạn rõ ràng, rồi hourly, rồi 1-minute trong khoảng thực tế nguồn cho phép. Ưu tiên độ phủ lịch sử và dữ liệu đủ để dựng roll; không tải CONTFUT rồi gọi đó là chuỗi hợp đồng thật.
- Giới hạn đợt đầu theo dung lượng đĩa và API: giữ ít nhất 20 GB trống, công bố trần byte/request trước khi tải, lưu checkpoint để tiếp tục được, không chiếm heavy lock nếu worker khác đang giữ. Nếu một mã bị chặn, tiếp tục các mã còn lại.
- Kiểm tra nguồn CME chính thức và các nguồn đã có entitlement. Chỉ tải từ kênh cho phép; không vượt paywall, CAPTCHA, chặn mạng, điều khoản sử dụng, không mua dữ liệu hoặc kích hoạt gói thuê bao.
- Lưu raw bytes ngoài Git dưới một thư mục dữ liệu riêng; lưu manifest SHA-256, thời gian lấy, endpoint/channel, tham số request, timezone, số dòng và khoảng ngày. Trong Git chỉ lưu code kiểm tra, manifest không nhạy cảm, báo cáo và handoff.
4. Kiểm định khả năng dùng cho research
- Đếm coverage theo từng hợp đồng/tháng, khoảng trống trong phiên, trùng lặp, bar đang hình thành, sai timezone/DST, thay đổi giá bất thường, volume/open interest, bid/ask, phiên và ngày nghỉ.
- Viết quy tắc roll chỉ từ thông tin đã có ở thời điểm quyết định; tách giá settlement khỏi giá có thể khớp. Không nội suy khoảng trống, không dùng giá front hiện tại viết lại quá khứ, không dùng roll/back-adjustment nhìn tương lai.
- Lập bảng chi phí theo từng mã: commission IBKR, exchange/regulatory fees, spread quan sát được hay NOT_RUN, slippage khai báo, chi phí roll và margin. Không đặt chi phí thiếu bằng 0.
- Xếp ba nhãn độc lập cho mỗi mã: SIGNAL_RESEARCH_READY, DAILY_FUTURES_BACKTEST_READY, INTRADAY_FUTURES_BACKTEST_READY; mỗi nhãn phải là PASS / FAIL / NOT_RUN / BLOCKED với bằng chứng. Giá spot EIA của CL/NG và XAUUSD/GLD của GC chỉ được xếp proxy/signal, không được tính là giá khớp futures.
5. Đầu ra bắt buộc
- Bảng 10 dòng: mã, venue, dữ liệu mới đã tải, độ sâu daily/H1/M1, số hợp đồng thực, quyền live/delayed/historical, chất lượng, chi phí, ba nhãn readiness, blocker chính xác và hành động mở khóa rẻ nhất.
- Danh sách artifact/raw manifest và SHA, script tái lập, báo cáo lỗi từng nguồn, dung lượng còn trống, trạng thái lock, worktree/HEAD. Có kiểm tra độc lập ít nhất đối với nhận dạng hợp đồng, coverage và roll.
- Nếu dữ liệu lấy được chỉ đủ một phần, báo đúng phần đó và tiếp tục các mã khác. Kết thúc bằng câu trả lời rõ: mã nào nghiên cứu được ngay, mã nào cần entitlement hoặc nhà cung cấp lịch sử, cần loại dữ liệu nào và khoảng thời gian nào.

Ranh giới: không backtest PnL, không scored cell, không mở S1, không đặt lệnh paper/live, không kích hoạt subscription, không mua dữ liệu, không push/merge. Có thể dùng các agent phụ cho tra cứu hợp đồng/nguồn/phí và kiểm định độc lập; chỉ một worker được gọi API tải dữ liệu tại một thời điểm để tránh đụng pacing và heavy lock.
