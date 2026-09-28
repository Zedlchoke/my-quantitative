# Kế hoạch đề xuất: tìm strategy có độ vững kinh tế

Trạng thái: **DRAFT FOR OWNER REVIEW**. Tài liệu này ghi lại đề xuất trao đổi với owner ngày 2026-09-25; không phải cycle đã đăng ký, không phải GO, không tự thay đổi quyền hạn của bất kỳ worker hay strategy nào. Khi triển khai, Lead phải đo lại `plans/CYCLE_REGISTRY.json`, các plan đang hiệu lực, ledger, heartbeat, lock và checkout. Số liệu shadow trong [review ngày 2026-09-24](research/control/SHADOW-PAPER-REVIEW-V1/REVIEW.md) là ảnh chụp lịch sử.

## 1. Mục tiêu và tiêu chuẩn thành công

Tìm một hoặc nhiều strategy có nguồn lợi nhuận giải thích được bằng cơ chế kinh tế, tồn tại sau chi phí giao dịch có thể thực thi, vượt kiểm định ngoài mẫu và được tái lập độc lập. Program cũng thành công khi bác bỏ toàn bộ giả thuyết một cách đáng tin. Kết quả backtest, paper/shadow, và khả năng dùng tiền thật là ba kết luận riêng.

Đề xuất tổ chức thành một **umbrella program 0 scored cell**. Mỗi family muốn tính PnL phải có child cycle, identity, worktree, trial budget, gate và owner GO riêng. Không mở sealed S1, đặt lệnh, dùng vốn, hay tự nâng cấp strategy dựa trên tài liệu này.

## 2. Quyết định đề xuất cho shadow hiện tại

Đây là đề nghị để owner phê duyệt và chuyển thành amendment/cycle riêng. Chưa có worker nào được dừng hoặc sửa bởi tài liệu này.

| Strategy | Trạng thái đề xuất | Điều kiện / câu hỏi quyết định |
|---|---|---|
| FX RANGEFADE EURUSD + GBPUSD | `KEEP_PROSPECTIVE` | Giữ identity. Bổ sung short-beta control, attribution từng cặp, aggregate USD exposure và stress-spread book qua amendment. Hai giao dịch đầu chưa đủ kết luận. |
| BASISLV | `KEEP_PROSPECTIVE_LOW_FREQUENCY` | Giữ identity. Audit lịch tuần, pre-decision data probe và gap telemetry. Quyết định mất dữ liệu không được backfill như prospective thật. |
| BTC4H-BANDRIDGE | `CONDITIONAL_KEEP` | Owner chốt sizing B cost-aware và fill law A nếu đồng ý; reconcile 6 bps/side trong identity với 5 bps + 1 tick ở executor **trước fill đầu**. Nếu chưa thống nhất, đánh dấu `BLOCKED_IDENTITY`. |
| ILLIQ | `DIAGNOSTIC_ONLY` | Không xét promotion từ shadow hiện tại. Đề xuất checkpoint tối đa 13 quyết định tuần hợp lệ để hiểu cơ chế; owner phải phê duyệt luật đóng. Không thêm variant cứu kết quả cũ. |
| XSECT-FUND-CARRY-7D V1 | `RETIRE_CURRENT_IDENTITY` khỏi candidate pool | Chi phí/turnover trong review lớn hơn funding nhận được. Giữ nguyên ledger và verdict. Việc ngừng sleeve đang chạy cần quyết định owner và closeout an toàn. Successor phải mang ID mới. |

XAUUSD đã được xử lý bởi cycle riêng sau review; kiểm tra registry hiện tại, không hồi sinh bằng plan này.

## 3. Chỉ nghiên cứu ba hướng cơ chế

### A. FX liquidity provision / RANGEFADE replication

Kiểm tra cơ chế cung cấp thanh khoản gần mép prior-day range trên cặp tiền và nguồn dữ liệu độc lập. Giữ giả thuyết và luật giao dịch đã khóa; đây là replication, không phải tìm threshold đẹp hơn. Bắt buộc so với short-beta, random-entry, range baseline và aggregate USD exposure. Kiểm tra chênh lệch giá executable giữa các vendor và spread stress.

### B. Delta-neutral basis/carry

Nghiên cứu spot–futures basis hoặc funding convergence với hai chân hedge có thể thực hiện. Hạch toán funding, borrow, margin, liquidation path, phí mở/đóng, slippage, venue và counterparty risk. [BIS Crypto Carry](https://www.bis.org/publications/working-paper-1087-crypto-carry) là nguồn tham khảo cho giả thuyết về segmentation và giới hạn vốn arbitrage; không phải bằng chứng strategy của repo có lãi.

### C. Forced-flow/event premium

Chỉ nghiên cứu sự kiện có đối tượng bị buộc hoặc có động cơ mạnh để giao dịch: liquidation, rebalance, expiry, inventory imbalance hoặc funding reset. Proposal phải nêu ai giao dịch, vì sao, vào thời điểm nào, observable point-in-time nào đo được áp lực đó, và điều kiện khiến premium biến mất. Không dùng indicator giá làm vật thay thế nếu thiếu dữ liệu trực tiếp về cơ chế.

Tạm tránh ghép indicator vào BANDRIDGE, router nhiều nhánh, cross-sectional turnover cao, đảo dấu strategy đã thất bại rồi coi là discovery mới, và quét hàng trăm parameter.

## 4. Sáu câu hỏi bắt buộc trước khi thấy PnL

Mỗi proposal phải trả lời bằng câu có thể bác bỏ:

1. Ai trả tiền cho ta?
2. Vì sao họ vẫn phải trả?
3. Edge tồn tại trong bao lâu?
4. Chi phí nào ăn edge?
5. Quan sát nào sẽ chứng minh giả thuyết sai?
6. Control đơn giản nào có thể tái tạo kết quả mà không cần cơ chế đề xuất?

Thiếu câu trả lời có thể kiểm chứng thì `REJECT_UNFALSIFIABLE` hoặc `BLOCKED_DATA_AUTHORITY`; chưa backtest.

## 5. Giới hạn tìm kiếm và trial accounting

Mỗi cơ chế trong một child cycle có tối đa **1 anchor, 2 neighbour, 1 control cùng chiều, 1 control đảo dấu**; thêm một baseline đơn giản được xác định trước. Council đề xuất tối đa ba cơ chế mỗi cohort. Chỉ một vòng sửa proposal trước freeze. Mọi phép tính PnL đã thực hiện phải vào **observed trial counter**, kể cả khi code lỗi hoặc publication thất bại; published counter tách riêng.

Không chọn lại hướng, timeframe, cost law hoặc threshold sau khi thấy scored PnL rồi gọi đó là cùng một thí nghiệm. Nếu có insight mới, mở identity/cycle mới và tính ancestry đầy đủ. Lý do: thử càng nhiều thì khả năng tình cờ gặp equity curve đẹp càng cao. [Harvey, Liu & Zhu](https://www.nber.org/papers/w20592) cho thấy ngưỡng ý nghĩa thông thường không đủ khi có nhiều phép thử; không áp dụng máy móc một ngưỡng t-stat chung cho mọi family.

## 6. Chuỗi kiểm định và điểm dừng

1. **Control-plane intake:** Đo registry, plan, branch, HEAD, dirty tree, worker/heartbeat và heavy lock. `CONTROL_STATE_DRIFT` hoặc ownership không rõ thì dừng dispatch/scoring; không chạm foreign worker.
2. **Mechanism proposal outcome-blind:** Ghi payer, premium, persistence, risk transferred, observable, holding horizon, capacity, costs, falsifier, control, baseline, ancestry. Proposer và critic không thấy candidate PnL hoặc sealed S1.
3. **Dữ liệu và chi phí:** Audit license, PIT timestamp, timezone, calendar, survivorship, missingness, input hash và executable price. Không có thẩm quyền dữ liệu/chi phí thì `BLOCKED`, không gán chi phí bằng 0.
4. **Falsification trước PnL:** Kiểm tra observable, matched controls, delay/placebo, sample power và khả năng cơ chế chỉ là beta/momentum cũ. Cơ chế bị control đơn giản tái tạo thì đóng.
5. **Trial freeze:** Khóa code SHA, input hash, folds, cost/fill/sizing/exit laws, variants, observed denominator, promote/kill/time-stop và artifact paths. Fresh-context audit trước owner GO tính điểm.
6. **Scored S0 walk-forward:** Nhiều fold theo thời gian, không rò rỉ dữ liệu. S0 là screening đã được nhìn thấy, không phải untouched OOS. Mọi scored cell tiêu thụ budget child cycle.
7. **Tái lập độc lập và A7:** Agent khác chạy lại frozen computation và audit assumptions, denominator, data, costs. Mismatch là kết quả cần giải quyết, không được nới tolerance sau khi thấy số.
8. **Sealed S1 một lần:** Chỉ sau freeze, reproduction, fresh review và một owner GO mới đúng child cycle. Không đổi luật sau khi xem S1. Fail thì terminal hoặc theo verdict đã khóa.
9. **Prospective shadow:** Chạy identity đã khóa với event/fill ledger và baseline/control đi kèm. Phán xét theo số quyết định/giao dịch hợp lệ và time-stop preregistered.
10. **Broker paper / micro-live:** Chỉ là cycle riêng sau khi owner GO, có broker cost, operational risk và portfolio capital gate riêng. Không suy từ shadow PnL ra quyền giao dịch bằng tiền.

## 7. Bộ số liệu bắt buộc

- Net PnL/expectancy sau chi phí chuẩn; cost stress `1.5×` và `2×` được báo cáo tách biệt. Ngưỡng pass cụ thể phải khóa bằng power/cost analysis trước scoring.
- Profit factor, drawdown, tail loss, turnover và capacity.
- Phân bổ lợi nhuận theo fold, sự kiện, tài sản, trạng thái biến động; không để một fold/sự kiện độc chiếm kết luận mà không được giải thích trước.
- Beta thực với BTC, USD và trend; correlation và drawdown overlap với các sleeve đang chạy.
- [Deflated Sharpe Ratio](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551) trên toàn bộ trial history, có nêu giả định và độ không chắc chắn.
- [Probability of Backtest Overfitting](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253) trên cả tập variants nếu cấu trúc folds/variants phù hợp; nếu không phù hợp, ghi `NOT_RUN` và lý do.
- Sai khác giữa declared, measured và stress execution costs; tổn thất khi fill xấu.

Không dùng một ngưỡng Sharpe/PF/DSR/PBO cố định cho mọi asset. Child plan phải khóa ngưỡng theo tần suất, power và cơ chế trước khi thấy scored outcome.

## 8. Luật shadow khởi điểm

Các mốc dưới đây là **sàn đề xuất**, không tự chứng minh đủ sức thống kê. Power analysis có thể yêu cầu số lớn hơn; time-stop và luật khi không đủ mẫu phải khóa trước.

| Loại strategy | Sàn bằng chứng prospective |
|---|---|
| FX intraday | Ít nhất 100 closed round trips và 6 tháng, có nhiều trạng thái volatility. |
| BTC 4H | Ít nhất 50 closed trades; no-trade decision chỉ chứng minh khả năng vận hành, không chứng minh profitability. |
| Daily | Ít nhất 100 valid decisions, cùng số trade/round-trip được báo cáo riêng. |
| Weekly | Ít nhất 52 valid decisions; tuần bị mất event không được tính. |

Promotion chỉ được xem xét khi net sau phí dương, thắng baseline và causal control theo luật khóa, không phụ thuộc một fold/sự kiện, không đảo dấu dưới stress cost đã preregister, và được tái lập độc lập. Cần xem cả rủi ro danh mục: crypto beta, USD beta, concentration, source/venue failure và capacity. `REJECT_ALL`, `INSUFFICIENT_POWER` hoặc `BLOCKED_DATA/COST` đều là kết quả hợp lệ.

## 9. Quyết định owner còn mở

1. Có đồng ý trạng thái đề xuất cho từng shadow sleeve, nhất là ILLIQ và XSECT V1, không?
2. Có đồng ý sizing B, fill law A và phương án reconcile cost identity cho BANDRIDGE trước fill đầu không?
3. Ai sở hữu các amendment FX control, weekly scheduler, stress-cost telemetry và closeout của sleeve nghỉ?
4. Có cho phép đăng ký umbrella program 0/0 và viết child plans outcome-blind không? Mỗi child cycle sẽ xin gate/GO riêng khi đủ điều kiện.
5. Budget nguồn lực, dữ liệu và thời gian cho ba track là bao nhiêu? Không mua/đăng ký dịch vụ bằng plan này.

## Giải thích như 5 tuổi

Ta chỉ mở quầy khi biết khách mua gì, vì sao họ trả tiền, tiền giao hàng là bao nhiêu, và nếu đổi mùa quầy còn bán được không. Một ngày đông khách chưa chứng minh quầy sẽ có lãi cả năm. Mỗi ý tưởng được thử ít lần, ghi cả lần thất bại, rồi nhờ người khác kiểm lại sổ trước khi owner quyết định dùng tiền thật.
