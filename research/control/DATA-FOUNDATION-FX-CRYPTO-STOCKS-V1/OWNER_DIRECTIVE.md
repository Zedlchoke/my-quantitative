# OWNER DIRECTIVE — DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 (2026-09-26)

Verbatim anchor of the owner instruction opening this cycle. Binding scope.
Nothing below may be narrowed or widened by any agent; conflicts resolve to
this text, then to the plan, then to CLAUDE.md/RULES.md.

---

Tôi là owner. Hãy orchestrate một chương trình DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1
làm bước đệm cho việc tìm strategy có bằng chứng tốt hơn. Đây là cycle dữ liệu
và phương pháp, không phải cycle săn PnL. Hãy lập master plan, kiểm tra độc lập
rồi thực thi các phần được phép theo gate của repo.

Bắt đầu bằng intake thật: đọc AGENTS.md, CLAUDE.md, handbook, registry, các plan
sống, MAP, LESSONS, FAMILY_FAILURES, data manifests và outcome-exposure map. Đo
lại HEAD, worktrees, dirty tree, dung lượng đĩa, workers và heavy lock. Không coi
ghi chú cũ là trạng thái hiện tại. Không đọc sealed S1/holdout.

Tổ chức các lane độc lập cho Forex, Crypto, Stocks, PIT/license, cost/execution
và A7 reproduction. Mỗi lane có dispatch packet, phạm vi file rõ ràng và
structured handoff; A1 là người duy nhất tích hợp kết quả. Cho các lane khảo sát
song song, nhưng không cho nhiều job tải/xử lý nặng tranh tài nguyên.

Không gom dữ liệu vô hạn. Với từng loại dữ liệu, phải ghi nó mở được giả thuyết
kinh tế nào, khắc phục lỗ hổng nào đã làm strategy chết, và control nào sẽ bác
bỏ ích lợi của nó. Ưu tiên:

- Forex: bid/ask có timestamp đủ mịn, spread đúng giờ đặt lệnh,
  commission/slippage và swap/financing từ broker; lịch phiên và DST; sự kiện
  kinh tế với thời điểm công bố và các lần sửa số liệu. Phân biệt giá
  indicative với quote có thể giao dịch, dữ liệu một nguồn với replication
  độc lập.
- Crypto: trades/quotes, spot–perp basis, mark/index, funding đã settle so với
  funding dự báo, fees và exchange rules theo thời gian; OI, liquidation và L2
  chỉ khi thật sự có lịch sử PIT, coverage và license hợp lệ. Không suy ra
  order book hay forced flow từ nến.
- Stocks: universe không survivorship bias, symbol/identifier history,
  split/dividend và corporate actions biết tại thời điểm đó; trades/quotes với
  phạm vi SIP/IEX được ghi rõ; earnings/filings có publication timestamp và
  revision; halts/auction, borrow/short fees nếu định short; chi phí khớp lệnh
  thực tế.

Với mỗi dataset, lập một authority row gồm: nguồn và điều khoản sử dụng; tài
sản/symbol và giai đoạn; độ phân giải; event_time, available_at, ingested_at và
revision; timezone; missingness/gaps; checksum/manifest; chi phí lấy và lưu;
giới hạn API; khả năng tái tạo; trạng thái AVAILABLE_VALIDATED,
AVAILABLE_UNVALIDATED, BLOCKED_LICENSE, BLOCKED_ACCOUNT, BLOCKED_COST,
BLOCKED_STORAGE hoặc NOT_RUN. Không suy PASS từ việc file tồn tại.

Thiết kế pipeline raw bất biến → normalized có provenance → PIT/quality tests →
cost book → query/replay read-only. Có fixture bắt future leak, sửa số liệu,
DST, symbol changes, duplicate/missing bars, quote crossed/stale và nguồn bất
đồng. Tách dữ liệu nghiên cứu đã outcome-exposed khỏi dữ liệu xác nhận chưa mở.
Không đưa licensed raw bytes, token, statement cá nhân hoặc dữ liệu lớn vào Git.

Thực thi tự động trong phạm vi cho phép: census và validate dữ liệu đã có;
probe nhỏ nguồn công khai/keyless khi license cho phép, có disk/network budget
và plan/GO hợp lệ. Không tự đăng ký tài khoản, mua subscription, dùng
credential, kích hoạt market-data plan, tải hàng trăm GB, mở S1, score strategy,
sửa shadow/dashboard hoặc đặt lệnh. Nếu cần owner action, dừng đúng gate và ghi
chính xác việc tôi phải làm.

Deliverables bắt buộc khi dừng:

1. DATA_INVENTORY: toàn bộ dữ liệu hiện có, vị trí, SHA/manifest, coverage,
   chất lượng và trạng thái authority — chia FX/Crypto/Stocks.
2. DATA_GAP_MATRIX: dữ liệu còn thiếu, vì sao cần, hypothesis class được mở,
   mức ưu tiên và chi phí/khối lượng ước tính; phân biệt "cần ngay" với "chỉ
   lấy khi có cơ chế cụ thể".
3. OWNER_ACQUISITION_RUNBOOK: hướng dẫn từng bước để tôi lấy hoặc cấp quyền
   cho mỗi nguồn bị chặn; link tài liệu chính thức, loại tài khoản/subscription
   cần có, cách xuất dữ liệu an toàn, dữ liệu nào không được gửi vào chat/Git.
   Không yêu cầu tôi cung cấp mật khẩu hoặc API secret.
4. PIT_AND_COST_CONTRACTS: schema, quality thresholds, tests và cách chứng minh
   dữ liệu đủ để backtest sau phí.
5. NEXT_RESEARCH_FRONTIER: tối đa ba hướng nghiên cứu mới mà dữ liệu đã
   validated thực sự cho phép; hướng còn thiếu dữ liệu phải gắn BLOCKED, không
   đưa vào scored cycle.
6. A7 audit độc lập, handoffs, danh sách gate PASS/FAIL/NOT_RUN/BLOCKED, và
   báo cáo cuối cho owner bằng ngôn ngữ đơn giản.

Điểm dừng: dừng khi inventory và gap matrix đã bao phủ ba asset class, các
nguồn sẵn có đã được kiểm định trong ngân sách, và mọi cửa còn lại đã có runbook
owner-action cụ thể. Không kéo dài cycle chỉ để "có thêm dữ liệu". Kết luận có
thể là FOUNDATION_READY_FOR_NARROW_RESEARCH hoặc
BLOCKED_WITH_ACQUISITION_RUNBOOK; không được gọi là strategy đã được chứng minh
có lời.
