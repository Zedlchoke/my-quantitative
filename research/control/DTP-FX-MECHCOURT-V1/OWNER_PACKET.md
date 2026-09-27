# OWNER_PACKET — DTP-FX-MECHCOURT-V1 (2026-09-27)

Cycle đóng `DTP_FX_V1_BLOCKED_DATA_OR_COST`: 0 scored cells, 0 holdout looks,
S1 SEALED, không order, không đụng shadow/broker/dashboard. Không scored cell
vô nghĩa nào được chạy để "đạt chỉ tiêu" — đúng chỉ thị. GO phrase chưa từng
được tiêu (không gate nào mở).

| Cơ chế | Verdict | Lý do chính |
|---|---|---|
| A — month-end London fix | `F0_KILLED VETO_VARIANT_SAME_FAMILY` | Cùng skeleton/payer/exit với `TRACKA2-P4A-FIXCERT-01` đã chết (band dưới cost book đo); month-end subset + direction-MTD là re-gate/re-clock — RC cấm re-tune |
| B — news → rates-reaction → FX | `BLOCKED_DATA` | Leg "phản ứng lãi suất đã quan sát được" = 0 bytes intraday rates toàn hệ; PIT ledger 10/131 FETCHED-verified, không consensus/revision vintages |
| C — lệch quote 2 venue | `BLOCKED_DATA` | Chỉ 1 feed hai chiều tồn tại; venue-2 = 0 bytes trên mọi path đã đo (IBKR 0/357 obs/pair; Dukascopy re-download transport-blocked; TrueFX/OANDA owner-gated) |

Số đo mới banked (dù verdict âm): bucket chi phí London fix-window trên
EURUSD/GBPUSD/USDJPY đo trọn đủ lần đầu — p50 0.3 / 0.7–0.8 / 0.5 pip/crossing,
BẰNG giữa tháng (không phải bucket đắt; chỉ rollover 21–22UTC giãn p99 tới
7.8–16 pips). Barrier của fix-family là premium-evidence + venue, không phải
spread bucket. Xem `fixwindow_spread_census.json` (34,715 obs, DST-verified).

## Chính xác những gì owner cần cung cấp để mở lại (mỗi mục là một gate, không phải wishlist)

### 0. Chung — mở lại scored surface FX (chọn ≥1 reopener, DTP master §5)

- **R1 (broker cost authority)** — hai bước, đo lại bằng probe đã đóng băng:
  1. Trong TWS: Global Configuration → Manage Data Subscriptions → bật
     **FX delayed (free)** cho IDEALPRO (hoặc share market-data subs từ tài
     khoản funded). Restart TWS, giữ API socket 7497 Read-Only.
  2. Xuất **Activity Statement hoặc Flex Query** chứa giao dịch FX + vị thế
     overnight FX (cửa sổ tốt nhất T4–T7 gồm một cuối tuần), đặt file vào
     `~/.my-quantitative-data/ibkr_statement/`. KHÔNG gửi nội dung vào chat —
     chỉ cần đường dẫn file.
  → Probe `broker_cost_probe_FX_majors_2026-09/probe_fx_majors_raw.py` đo lại
  một lệnh: spread two-sided + commission + swap + min size. Lưu ý đã đo:
  minTick 0.5 pip tại IDEALPRO — mọi cơ chế cần crossing < 0.5 pip base là
  bất khả thi tại venue này bất kể data sub.
- **R2 (nguồn bid/ask độc lập)** — chọn MỘT path (EDQ1 packet 2026-09-22):
  (i) **TrueFX**: owner tự đăng ký tài khoản free (agent signup bị cấm), vào
  trang historical downloads, chụp nguyên văn license/TCU; nếu cho phép lưu
  trữ nghiên cứu nội bộ + lấy zip hàng tháng → PRIMARY candidate.
  (ii) **Dukascopy**: email Dukascopy Bank SA xin written consent truy xuất
  bi5 tự động cho nghiên cứu phi thương mại nội bộ; im lặng/từ chối → bỏ
  hẳn hướng Dukascopy.
  (iii) **OANDA v20 practice**: owner tự đăng ký practice account + chấp nhận
  terms; sau đó đọc API terms + probe M1 depth. (Runner-up: Polygon/Massive
  forex BBO.)
  Sau khi có bytes: probe 7–14 ngày TRƯỚC khi đổi plan + GO mới.
- **R3 (financing band)**: statement/swap broker-grade — mở lại mọi cơ chế
  giữ qua đêm (hiện structurally blocked NG6/NG7 F4).
- **R5 (information layer mới)**: artifact có authority, không-PnL.

### 1. Riêng cơ chế A (nếu muốn thực sự mở lại fix-family)

RC FIXCERT đòi "NEW economic basis" — cụ thể:
1. **Bằng chứng premium** ngoài panel giá: nguồn có license cho ước lượng
   fix order-flow / rebalancing-flow (ví dụ dữ liệu WM/Refinitiv fix order
   estimates, FX flow data có license) — phải có `available_at` PIT. KHÔNG
   chấp nhận band khai báo từ học thuyết (band khai báo chính là thứ đã giết
   FIXCERT: 1.0–3.0 bps vs cost book 6.2 bps stressed).
2. **Cheaper measured execution**: R1 hoặc R2 ở trên. (Số đo mới: spread
   bucket fix-window không phải rào cản — p50 0.3 pip EURUSD; rào cản là
   premium-evidence.)
3. **Bề mặt chưa exposure** để đo premium: corpus USDCHF-class (chưa từng
   search, cần data gate) sau khi có nguồn. CẢNH BÁO: holdout sealed
   AUDUSD/USDCAD 2026-H1 là ONE-LOOK CẤP LINEAGE — không tiêu cho cơ chế
   đang blocked.

### 2. Riêng cơ chế B

1. **Dữ liệu lãi suất intraday** (chân "phản ứng đã quan sát được"):
   - CME ZQ (30-Day Fed Funds) / ZZT (3-Month SOFR futures) tick hoặc
     1-minute: cần (a) network path tới *.cmegroup.com không bị SNI-filter
     (đã đo bởi FX-FUTURES-FRONTIER-V1 — cùng một unblock network với
     Dukascopy), (b) license dữ liệu CME (owner purchase — owner-only), hoặc
   - Nguồn broker-grade tương đương (yields intraday từ venue có license).
2. **PIT release feed đạt evidence floor**: ALFRED (keyless, có vintages) cho
   series US + lịch chính thức từng nền kinh tế; **consensus estimates** từ
   nguồn có license (vendor consensus với as-of timestamp) — ledger 131-event
   hiện có (10/131 FETCHED) không đủ và tự cấm dùng làm causal evidence.
3. **Bề mặt FX dev chưa exposure** cho class này (USDCHF-class sau data gate
   hoặc corpus từ nguồn R2 mới).

### 3. Riêng cơ chế C

1. **Venue thứ hai đồng bộ** (chọn một path EDQ1 ở R2), granularity **tick
   hoặc tốt hơn ở CẢ HAI venue** (M1 một nguồn rồi gọi là arbitrage bị cấm
   đúng chỉ thị owner), clock discipline đồng bộ hai nguồn.
2. **Cost authority hai chân**: R1 cho ít nhất một venue thực thi được
   (commission + spread two-sided measured; hiện 8/10 components UNMEASURED).
3. Khi có dữ liệu: định nghĩa phải mang sẵn Q-4 delay-pair + clairvoyant
   battery và shadows FXFV7-A6-P2 (own-lag out-earn) + DTPCX1-I002
   (fictional-counterparty veto) — court đã ghi đây là fences vũ trang.

## Trung thực kỳ vọng

Kể cả có đủ dữ liệu: A nằm trong class 5 VIABILITY (fix-window/clock/calendar
— DEAD), B kề class 7 (15 dead macro entries; DGS10-shadow shape đã giết
FXFV8/FXNG1 bằng control out-earn), C kề class cross-venue lead-lag (dead)
+ Q-4. Dữ liệu mở phép ĐO trung thực, không mở edge. `BLOCKED`/`REJECT` là
kết quả đúng của hạ tầng hiện tại (Q-16) — 245/245 forex scored trials 0
survivors là base rate mà mọi cơ chế mới phải đối mặt.
