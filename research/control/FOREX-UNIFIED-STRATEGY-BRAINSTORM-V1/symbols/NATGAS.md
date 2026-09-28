# NATGAS (Henry Hub) — Deep Dive & 100 Strategy Ideas

- Program: `FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1` · Lane: **NATGAS** · Ngày: 2026-09-28.
- Chế độ: **knowledge-only brainstorm** — không backtest, không data pull. Mọi con số thời điểm Sep-2026 đã kiểm chứng qua WebSearch (nguồn ghi kèm ngày); mục chưa chắc gắn **(cần kiểm chứng)**. Mọi correlation/range mang tính stylized, phải tái đo bằng pipeline chung của chương trình trước khi tin.
- Cấu trúc: §1 bản chất instrument · §2 đúng 100 ý (10 family × 10) · §3 tổng hợp + bẫy overfitting + checklist.

---

## 1. Bản chất instrument

### 1.1 Instrument & underlying

- `NATGAS` CFD tại broker forex = proxy của hợp đồng **Natural Gas futures (mã NG)** sàn NYMEX/CME, settle tại **Henry Hub** (Erath, Louisiana) — benchmark gas **nội địa Mỹ**, quote USD/MMBtu.
- Thông số futures NG: 10.000 MMBtu/hợp đồng; tick $0.001/MMBtu = $10/contract; ngày giao dịch cuối ~3 ngày làm việc trước delivery month → **roll front-month hằng tháng** là một event microstructure cố hữu.
- Henry Hub **options (mã ON)**: American-style, expiry vài ngày trước futures → hiệu ứng "pinning" quanh expiry, psychology quanh strike OI lớn.
- Chart "continuous" của broker nối front-month **không điều chỉnh roll yield** → nhìn lùi bị méo bởi contango/backwardation; mọi backtest phải dùng chuỗi roll-adjusted chuẩn (xem bẫy ở §3.2).
- Khác BRENT/WTI (global oil), NATGAS là market **nội địa với 1 van xuất khẩu (LNG) đang mở dần**: LNG export ~2 Bcf/d (2016) → **17.4 Bcf/d H1-2026, +23% YoY, hướng ~20 Bcf/d cuối 2026** (AGA 2026-09-03; Plaquemines, Corpus Christi Stage 3, Golden Pass đang ramp — mốc Golden Pass startup **(cần kiểm chứng)**). Đây là thay đổi cấu trúc demand lớn nhất thập kỷ.
- Thang giá tham chiếu để đọc mọi con số trong file: bình thường $2–6/MMBtu; spike winter 2014 ~$6; Uri 2021 ~$23 intraday (front futures); 2022 avg ~$6.4; 2023–2026 về lại $2–4. Mức Sep-2026 $2.50–3.35 thuộc vùng thấp của history hiện đại.

### 1.2 Sessions & microstructure

- Globex gần 24/5: Chủ nhật 18:00 ET → Thứ Sáu 17:00 ET; nghỉ maintenance 17:00–18:00 ET hằng ngày (lịch CME hiện hành **(cần kiểm chứng)**).
- Phân bổ liquidity: **Á mỏng nhất** (market Mỹ nội địa — overnight chỉ có desk Asia trôi tự do), London khiêm tốn, **NY 09:00–14:30 ET đậm nhất**; settlement 14:30 ET (di sản pit) vẫn là mốc kỹ thuật.
- Không có **daily price limit cứng** như nông sản (NYMEX energy); chỉ có exchange halt/circuit breaker trong cực đoan — nhưng move 5–10%/ngày là bình thường, 15–25% từng xảy ra trong freeze-off (Feb 2003, Jan 2014, **Feb 2021 Uri**).
- Hai "event hằng ngày" riêng NATGAS: **model runs GFS/ECMWF 00Z & 12Z** (output ~07:00–08:00 ET và ~13:00–15:00 ET; ensemble chạy 4 lần/ngày) — mùa đông mỗi lần chạy có thể dịch giá 1–3% vì toàn thị trường re-price HDD forecast cùng lúc.

Bảng tóm tắt phiên (ET):

| Khung giờ | Liquidity | Việc gì xảy ra | Hệ quả strategy |
|---|---|---|---|
| 18:00–02:00 (Chủ nhật–Thứ Sáu) | Rất mỏng (Á) | Drift OU quanh fair value NY close | Fade range Á (S43/S88), cẩn thận event đêm |
| 02:00–07:00 | Mỏng | Overnight weather flows, desk Á mở | S50 overnight-cold logic |
| 07:00–09:00 | Trung bình | 00Z digest + feedgas nominations ra | S60 pre-positioning |
| 09:00–10:30 | Đậm dần | NY mở, ORB, hedge flow | S22/S44 |
| **10:30 (Thứ Năm)** | **Đỉnh event** | **EIA storage** | S21/S30/S41/S51/S92 |
| 13:00–15:00 | Đậm | 12Z digest + settlement approach | S42/S49 |
| 14:30 | Điểm neo | Settlement | S49 |
| 15:00–17:00 | Giảm | Marking, flattening | S45 |

### 1.3 CFD broker treatment (phải biết trước khi design strategy)

- **Spread riêng, rộng**: ~$0.02–0.06/MMBtu (≈0.7–2% ở giá $3) hằng ngày; nới 3–10x quanh **EIA Thursday 10:30 ET**, quanh model-run mùa đông, và lúc open Chủ nhật.
- **Margin/leverage riêng**: xếp nhóm energy với margin 1–5% (đòn bẩy 20–100x thấp hơn nhiều so với FX); một số broker hạ đòn bẩy mùa đông hoặc quanh bão. Backtest phải dùng margin thực của symbol, không mượn của FX.
- **Financing/swap hằng ngày** âm với long (điển hình vài %/năm quy đổi); carry các vị thế đa tuần phải trừ.
- **Weekend gap**: thị trường đóng Thứ Sáu ~17:00 ET, mở Chủ nhật ~18:00 ET; stop **không tồn tại qua cuối tuần**. Weather tiến triển 48h không giao dịch → gap mở 2–5% là thường, 10%+ khi cuối tuần có cold snap/hurricane. Mọi strategy "giữ qua cuối tuần" phải model gap; không model được thì giảm size.
- **Broker expiry riêng** (không trùng NYMEX): liquidity mỏng 1–2 ngày trước broker-expiry; một số broker auto-close/adjust — kiểm tra contract specification từng broker **(cần kiểm chứng theo broker cụ thể)**.
- Quoting hai kiểu: ×100 (`3.250`) hoặc ×1000 (`3250.0`) — chuẩn hóa trước khi ghép data đa broker.
- **Slippage quanh 10:30 ET Thursday**: stop-market thường fill xấu 0.5–2% trong 5 giây đầu. Mọi ý EIA-reaction phải giả định fill thực, không fill giá stop lý tưởng.

### 1.4 Điểm ĐẶC BIỆT riêng NATGAS (so với 11 symbol còn lại trong universe)

1. **Weather chi phối**: HDD/CDD forecast là driver số 1 ở horizon 1–15 ngày; đây là commodity duy nhất trong universe mà biến ngoại sinh (thời tiết) định giá ngắn hạn gần như toàn phần.
2. **Mean-reverting quanh storage norm nhưng tail cực đậm**: anchor trung hạn là *storage vs 5-year norm* — giá có lực kéo về mức tương ứng balance; nhưng distribution có tail đậm (freeze-off, hurricane, LNG outage). Hình dung: bán bảo hiểm lũ lụt — thu phí đều 10 tháng, mất nhà 1 đêm.
3. **"Widow-maker"**: spread Mar/Apr lịch sử giết người short — cold snap cuối mùa đông đẩy contract tháng 3 (trước khi heat demand tháng 4 xuất hiện) lên thẳng đứng. Với CFD đơn-symbol: biểu hiện là front-month spike rồi decay cấp số trong 2 tuần cuối Feb–Mar.
4. **Vol cao nhất (hoặc gần nhất) universe**: annualized vol front-month thường 60–100%, gấp 3–5 lần majors FX; sizing theo ATR/ATR%-based là bắt buộc.
5. **Seasonal structure mạnh nhất universe**: injection season (Apr–Oct) nạp storage, withdrawal season (Nov–Mar) rút — hai regime có hành vi giá khác nhau đến mức mọi signal phải được eval tách season.
6. **Demand đang dịch cấu trúc** (LNG 2→20 Bcf/d 2016→2026 + power burn/data-center): seasonality của 2010s không còn đúng nguyên bản — mọi seasonal rule phải tái chuẩn hóa theo era LNG.
7. **Fundamental data công khai dày nhất universe**: EIA (storage, production, STEO), NOAA/CPC (weather), CFTC (positioning), pipeline nominations (feedgas) — symbol duy nhất mà data cơ bản có thể cạnh tranh với giá về tần suất.

Season calendar — hành vi giá điển hình theo tháng (stylized, mỗi năm gate bằng storage):

| Tháng | Trạng thái | Hành vi điển hình | Watch |
|---|---|---|---|
| Jan | Withdrawal đỉnh | Trend/loud, spike-prone | Cold snaps, freeze watch |
| Feb | Withdrawal + freeze-off risk | Vol đỉnh năm, widow-maker build | Production loss, Mar/Apr spread |
| Mar | Kết thúc heating | Premium decay, widow-maker resolve | HDD cuối mùa, roll Mar |
| Apr | Chuyển shoulder | Drift âm, mất premium | Exit các long winter |
| May | Injection bắt đầu | Yên, range | Sell-in-May (S39) |
| Jun | Pre-cooling | Bắt đầu price heat | CDD forecast, ERCOT load |
| Jul | Cooling đỉnh | Heat premium, power burn | Heat domes, CDD |
| Aug | Cooling + hurricane | Bid rủi ro bão | NHC, Gulf |
| Sep | Shoulder đáy | Yên/soft, đáy giá năm hay gặp | Hurricane, injection pace |
| Oct | Pre-winter | Premium bắt đầu build | Halloween (S38), S91 straddle |
| Nov | Withdrawal bắt đầu | Winter trend có hướng | First cold, S31/S5 |
| Dec | Withdrawal | Trend continuation | Pace vs required (S53) |

### 1.5 Tin tức & sự kiện — transmission channel

**Scheduled (lặp lại, biết trước):**

| Event | Thời điểm | Transmission channel | Biên độ điển hình |
|---|---|---|---|
| EIA Weekly Storage Report | Thứ Năm 10:30 ET | build/draw vs consensus → re-rate surplus/deficit vs 5-yr norm | 1–4% trong 5 phút, nhánh 1–3 ngày |
| GFS/ECMWF model runs | ~07:00 & ~13:00 ET (00Z/12Z) | HDD/CDD 6–10/8–14 ngày revise → re-price demand kỳ vọng | 1–3%, hai chiều quanh năm |
| NOAA/CPC 6–10 & 8–14 day outlook | cập nhật hằng ngày/tuần | xác nhận hoặc bẻ consensus model | 1–3% |
| EIA STEO (Short-Term Energy Outlook) | hàng tháng, đầu/thứ hai thứ Ba | forecast supply/demand/giá → narrative tuần | 1–2% gián tiếp |
| Baker Hughes rig count | Thứ Sáu 13:00 ET | tín hiệu supply tương lai (lag 6–12 tháng, yếu) | <1% |
| CFTC COT report | Thứ Sáu ~15:00–15:30 ET **(cần kiểm chứng giờ)** | positioning → contrarian/fuel cho tuần sau | <0.5% |
| NHC Atlantic tropical outlook | Jun–Nov, nhiều bulletin/ngày | Gulf shut-ins + LNG feedgas rủi ro | 1–5% khi bão nhắm Gulf |
| Futures/options expiry + roll | hàng tháng | pinning quanh expiry, roll flow | 0.5–2% |

**Unscheduled (đột ngột):**

| Event | Transmission channel | Biên độ |
|---|---|---|
| **Freeze-off** (thường tháng 2) | production loss 5–15 Bcf/d vài ngày (giếng đóng băng) → supply shock tức thời, không phải weather-demand | spike 10–30% trong 1–3 ngày; tail lớn nhất của NATGAS |
| **Hurricane** Gulf (Aug–Oct) | shut-in production + LNG terminal đóng | 3–15% tùy đường bão |
| **LNG outage** (Freeport-style) | feedgas −1.5–2 Bcf/d tức thì → demand shock | −5–10% |
| **Geopolitik global** (vd. Hormuz 2026) | TTF/JKM gap; HH chỉ nhận qua kênh export-pull — **phần lớn KHÔNG truyền sang HH** (xem §1.7) | HH thường <2% |
| Pipeline/storage incident | supply/basis cục bộ | 1–5% |

**Case studies shock lịch sử** (kiến thức nền, con số stylized — dùng làm sanity check cho backtest):

| Sự kiện | Thời điểm | Cơ chế | Bài học cho strategy |
|---|---|---|---|
| Freeze Feb 2003 | 2003 | supply+demand cùng lúc, storage thấp | Tail hai bên; short-vol chết |
| Polar Vortex | Jan 2014 | demand spike, pipeline constraint | Spike được giá trước; decay sau đỉnh HDD (S14 đúng) |
| Hurricane Katrina/Rita | 2005 | shut-in Gulf khổng lồ | Event-long pre-landfall có edge (S4) |
| Uri | Feb 2021 | freeze-off Texas, cả supply lẫn demand, $23+ intraday (futures) / spot Texas astronomically cao | Một đêm xóa 10 năm premium-harvest; mọi short có cap (S98) |
| TTF crisis | 2022 | global, hầu như KHÔNG truyền sang HH ($6 vs TTF $30+ lúc đỉnh) | Tiền lệ đầu tiên của decoupling; Hormuz 2026 lặp lại |

### 1.6 Parameter dashboard — thông số ảnh hưởng (trạng thái Sep-2026)

| Parameter | Giá trị/Giới hạn | Trạng thái Sep-2026 | Channel |
|---|---|---|---|
| Storage vs 5-yr norm | ±2σ của phân phối theo mùa | surplus ~159 Bcf đầu Sep (từ 185 = +6.2% giữa T8), hẹp dần; deficit ~28 Bcf vs năm ngoái (MarketWatch 2026-09-02) | Anchor trung hạn |
| Injection pace vs required | pace cần đạt target cuối Mar ~1.750–2.000 Bcf | Injection chạy dưới pace 5-yr (29 vs 37 Bcf/tuần) | Drift nền nhiều tuần |
| HDD/CDD forecast + revisions | 6–10 & 8–14 ngày, weighted consuming regions | mùa giao mùa — flip thường | Driver ngắn hạn số 1 |
| LNG feedgas | Bcf/d nominations | 17.4 Bcf/d TB H1-2026, hướng ~20 cuối năm (AGA 2026-09-03) | Demand floor mới |
| Dry gas production | ~105–107 Bcf/d (2025–26, stylized **(cần kiểm chứng)**) | ổn định | Supply; freeze watch tháng 2 |
| Winter risk premium | Nov–Feb forward > spot expectation | chưa build (Sep) | Seasonal drift |
| Price | $2.50–3.35 spot; 2026 avg ~$3.43; 2027 ~$3.28 (STEO 09/09 hạ từ ~$4.60) | vùng thấp history hiện đại | Đầu ra |
| TTF/JKM | TTF ~€60/MWh (~$18–21/MMBtu); JKM ~$21.99 (Platts 2026-08-21) | ratio TTF/HH ~6–7x — cực đoan (norm 2.5–4x) | Kênh global |

### 1.7 Bối cảnh Sep-2026: Hormuz và câu hỏi phân tách HH vs TTF — kết quả kiểm chứng

- **Việc đã xảy ra**: xung đột Mỹ–Iran làm eo Hormuz disrupted nghiêm trọng (chỉ ~13 lượt tàu/ngày qua eo ngày 09/08 theo Engie EnergyScan — con số mới nhất **(cần kiểm chứng)**); LNG Qatar (~20% LNG toàn cầu) không ra được; Goldman dời kỳ vọng phục hồi Persian Gulf LNG về **10/2026** (Anadolu 2026-07-22).
- **TTF (global) hấp thụ shock**: ~€60/MWh khi "lạc quan mở lại eo" tan biến; Europe storage thấp; JKM–TTF spread nới; freight LNG thắt chặt (Global LNG Hub 2026-05-06; Hellenic Shipping News 2026-09-07; WisdomTree ~2026-09-23).
- **HH (nội địa) gần như KHÔNG theo**: spot vẫn $2.50–3.35, storage surplus +6%, production dồi dào, forecast 2027 bị *hạ* xuống $3.28. Có analyst bắt đầu argue risk premium sẽ giảm nếu Hormuz de-escalate (phân tích PEG/TradingView ~2026-09-23) — narrative đang lật lệnh, **(cần kiểm chứng tin tức Hormuz mới nhất trước khi trade)**.
- **Kênh lan duy nhất HH nhận**: (i) spread TTF/JKM − HH giãn rộng → tăng pull feedgas — nhưng terminal đã gần capacity (17–20 Bcf/d), biên độ thêm nhỏ dần (saturation); (ii) sentiment "energy complex" vài giờ.
- **Kết luận cho chương trình**: HH = block **energy nội địa Mỹ**; TTF = **global**. Giả định "xung đột Trung Đông → mua NATGAS" đã bị dữ liệu Sep-2026 bác phần lớn. Cross-asset NG–TTF phải đi qua **kênh đo lường được** (feedgas nominations, TTF−HH spread) chứ không qua correlation trừu tượng (thể hiện thành checklist S100). Đây cũng là minh họa lớn nhất cho luận điểm "NATGAS = diversifier thấp tương quan của danh mục".

### 1.8 Correlation map với 11 symbol (universe của chương trình)

Số liệu stylized — **daily log-return correlation, range điển hình 2015–2026**, bắt buộc tái đo bằng data thực **(cần kiểm chứng)**:

| Symbol | ρ vs NATGAS (daily) | Kênh dẫn | Ghi chú |
|---|---|---|---|
| WTI | +0.25 … +0.40 | energy risk complex, associated gas (Permian), USD | liên kết **mạnh nhất** nhưng vẫn yếu |
| BRENT | +0.20 … +0.35 | global energy complex | trong global shock (Hormuz 2026) có thể **tách hoàn toàn**: BRENT up, HH flat → ρ thậm chí âm cục bộ |
| XAUUSD | 0.00 … +0.15 | real rates / inflation-hedge narrative | beta nhỏ |
| XAGUSD | 0.00 … +0.15 | commodity beta chung | beta nhỏ hơn XAU |
| USDCAD | −0.10 … +0.10 (bất ổn) | CAD là currency năng lượng nhưng qua **dầu**, không gas; gas Canada giá AECO riêng | sign không ổn định — đừng xây strategy trên này |
| AUDUSD | +0.05 … +0.15 | risk-on commodity chung | chỉ đáng làm gate |
| NZDUSD | +0.05 … +0.10 | risk-on chung | yếu nhất nhóm commodity-FX |
| EURUSD | 0.00 … +0.10 | USD channel | gần như vô nghĩa — NATGAS định giá nội địa USD |
| GBPUSD | 0.00 … +0.10 | USD channel | như EURUSD, yếu hơn |
| USDJPY | −0.05 … +0.05 | risk channel | không dùng được |
| USDCHF | −0.05 … +0.05 | risk channel | không dùng được |

**Verdict**: NATGAS có **average |ρ| thấp nhất danh sách 12 symbol** (~0.05–0.15 với FX, tối đa ~0.2–0.4 với oil). Là diversifier tốt nhất danh mục ở tầng allocation; nhưng cũng có nghĩa các "co-movement filter" mượn từ FX (DXY gate, risk gate) cho edge gần bằng 0.

**Breakdown theo regime:**

- *Freeze-off mùa đông*: ρ với oil tăng nhẹ (cùng supply-shock sentiment), FX ~0.
- *Global energy shock* (Hormuz 2026): BRENT/TTF up, HH flat — ρ BRENT–NATGAS có thể tạm âm (minh chứng Sep-2026).
- *USD-selloff risk-on*: mọi commodity nhẹ cùng chiều, NATGAS beta nhỏ nhất.

### 1.9 Note trung thực — bối cảnh nào các họ strategy hay chết trên NATGAS

1. **Naive trend trong season**: giá chop quanh weather-revision 2 ngày đảo chiều liên tiếp; breakout-trend không weather-gate bị whipsaw chết bởi chính noise nó định bắt.
2. **Tight-stop scalping quanh model-run/EIA**: stop-hunt quanh các mức rõ (prior high/low ngày) trước khi run thật; sau đó mới breakout hoặc reverse. Stop <1 ATR quanh event = donat máu.
3. **Naked short-vol / short straddle mùa đông**: premium harvest trông đẹp 9 mùa, chết trong 1 đêm Uri/2014. Chỉ làm khi có cap hoặc gate supply-shock.
4. **Seasonal cứng không gate bằng storage**: "luôn long tháng 11" chết trong các năm surplus lớn; "luôn short tháng 9" chết trong năm deficit + hurricane.
5. **Hold qua cuối tuần với stop gần**: gap Chủ nhật xuyên stop — PnL thực khác PnL backtest dạng bar.
6. **Mean-reversion vào spike có cause mới**: fade spike freeze-off/outage (đổi fundamentals) khác fade spike model-revision (noise) — fade sai loại là mất tài khoản (S3 vs S12/S14 phân biệt).

### 1.10 Khung thực thi & dependency giữa các ý (đọc trước phase backtest)

Thứ tự triển khai đề xuất — mỗi tầng chỉ chạy khi tầng trên đã verify:

| Tầng | Ý | Lý do |
|---|---|---|
| 0 — Hygiene | S86, S97, S46 | Không PnL riêng nhưng quyết định mọi PnL phía sau đo đúng/sai |
| 1 — Regime | S94, S37, S36, S53 | Dispatcher: xác định khối nào của lane được bật tuần đó |
| 2 — Core signals | S51, S11, S1, S21/S30, S19 | 5 cơ chế độc lập: event, anchor, weather, session-event, seasonal |
| 3 — Cross/context | S61, S81, S62, S63, S65 | Chỉ bật khi data TTF/feedgas/load đầy đủ |
| 4 — Advanced | S83, S84, S91, S93, S20/S87 | Cần futures/options/data thứ cấp — chấp nhận NOT_RUN nếu thiếu |

Quan hệ phụ thuộc chính ( ý → phụ thuộc ):

- S10, S52 → cần chuỗi consensus EIA ổn định; thiếu thì dùng proxy S53.
- S61, S82, S83, S100 → cần giá TTF/JKM + feedgas; thiếu thì cả family cross-asset rớt xuống NOT_RUN.
- S32, S40, S75, S76, S78, S84, S91, S93, S98 → cần futures/options thật; CFD-only account chỉ chạy bản proxy đã ghi trong Coupling.
- S1, S8, S14, S42, S58 → cần forecast archives có timestamp; dùng verified-HDD thay thế là vi phạm (bẫy §3.2-1).
- S71, S77, S74 → cần COT/OI history; lag 3 ngày phải được mô hình hóa.

---

## 2. 100 strategy ideas

Template mỗi ý: **S<n> — tên (family)** / dòng 1: Hypothesis · Signal / dòng 2: Trade · Risk · Data · Coupling. Mỗi ý là một cơ chế kinh tế khác nhau — đổi threshold không tính là ý mới. Ý nào cần futures/options thật (không có trên CFD broker) ghi rõ trong Data/Coupling.

Bản đồ family — cơ chế trung tâm và horizon:

| Family | Ý | Cơ chế trung tâm | Horizon điển hình |
|---|---|---|---|
| Trend/Momentum | S1–S10 | Under-reaction chuỗi weather-revision / supply-shock thông tin thật | 2–10 ngày |
| Mean-reversion | S11–S20 | Anchor storage-norm + phân biệt spike có/không cause | 1–15 ngày |
| Breakout/Vol-expansion | S21–S30 | Nén→giãn quanh event/model-run; kỷ luật retest | Intraday–5 ngày |
| Carry/Seasonal | S31–S40 | Winter premium build/decay; roll-yield | 3 tuần–3 tháng |
| Session/Time-of-day | S41–S50 | Cấu trúc liquidity theo phiên + 2 event hằng ngày | Intraday–2 ngày |
| Event/Data-driven | S51–S60 | Surprise đo được (EIA, feedgas, STEO, flip NOAA) | 1–5 ngày |
| Cross-asset/Correlation | S61–S70 | Kênh TTF/WTI/power có đo được, KHÔNG correlation trừu tượng | 1–4 tuần |
| Positioning/Flows | S71–S80 | Crowd đầy/rỗng + flow cơ học (roll, ETF) | 3 ngày–3 tuần |
| Pattern/Pairs/Stat-arb | S81–S90 | Ratio band, residual, OU phiên Á, analog | 2 ngày–6 tuần |
| Regime/Options-flavored | S91–S100 | Dispatcher regime + VRP mùa đông + tail-hedge | 1–3 tháng |

### 2.1 Family: Trend/Momentum — weather-trend riding (S1–S10)

**S1 — HDD-revision momentum (Trend/Momentum)**
Hypothesis: thị trường under-react chuỗi revision HDD cùng chiều nhiều ngày (anchoring bias của desks) · Signal: HDD 6–10 ngày (weighted consuming regions) revise lên ≥3 ngày liên tiếp, magnitude lũy kế > percentile-80 của 1 năm.
Trade: long theo hướng revision vào 14:00 ET sau khi 12Z digest; exit khi 1 revision ngược ≥50% magnitude trung bình; stop 1.5×ATR(14) daily · Risk: model flip 1 ngày (pattern đảo) — phải cắt sớm; mùa ấm signal thưa · Data: HDD forecast archives (Bespoke/EarthNC/NOAA), giá NG · Coupling: chỉ Oct–Mar; gate storage không surplus cực đại (> +300 Bcf).

**S2 — Donchian-20 mùa đông (Trend/Momentum)**
Hypothesis: breakout 20 ngày trong withdrawal season có follow vì weather-trend cluster (blocking pattern kéo dài 2–4 tuần) · Signal: đóng cửa > Donchian-20 upper trong Nov–Feb.
Trade: vào close ngày breakout, stop dưới median 9 ngày, trailing 2.5×ATR; time-stop 10 ngày · Risk: năm đông ấm liên tục → chuỗi false breakout · Data: giá NG roll-adjusted · Coupling: gate nhiệt (HDD forecast không quá -1σ norm) để tránh breakout do short-squeeze thứ Sáu.

**S3 — Freeze-off continuation (Trend/Momentum)**
Hypothesis: supply-shock freeze-off tạo gap thông tin thật (production loss đo được) — khác weather-noise, continuation xác suất cao · Signal: dry gas production giảm ≥5 Bcf/d vs 30-day avg trong Dec–Feb + giá gap >5%.
Trade: long gap-and-go (vào khi giá giữ trên mức pre-gap 60% phiên); stop dưới pre-gap low; exit khi production hồi ≥70% loss · Risk: ấm lên nhanh → spike mất utility · Data: EIA daily/weekly production, báo cáo freeze-off (NGI) · Coupling: chỉ Q1; không được fade bằng mean-reversion (phân biệt với S14).

**S4 — Hurricane shut-in ride (Trend/Momentum)**
Hypothesis: bão nhắm Gulf tạo drift lên theo xác suất đường đi — pricing tăng dần trước landfall, giảm ngay sau · Signal: NHC cone ≥40% nhắm vùng production/Gulf LNG trong 72h.
Trade: long pre-landfall 2–3 ngày, exit lúc landfall (sell the news); stop 1.2×ATR · Risk: bão đổi hướng; shut-in nhỏ hơn sợ · Data: NHC bulletins, BSEE shut-in stats (post), feedgas · Coupling: chỉ Aug–Oct; size nhỏ vì outcome binary.

**S5 — Winter-premium season drift (Trend/Momentum)**
Hypothesis: risk premium mùa đông được build dần Oct–Nov (hedger + fund bidding) chứ không một lần — drift dương dài · Signal: vào ngày giao dịch đầu tiên sau 15-Oct hằng năm.
Trade: long 40 ngày nếu storage surplus < +250 Bcf; trailing 20-day low + time-stop · Risk: năm surplus khổng lồ + forecast ấm → premium không build (2015-16 style) · Data: storage vs 5-yr norm, giá · Coupling: hủy nếu CPC seasonal outlook gọi đông ấm rõ ràng (>60% above-normal).

**S6 — Model-consensus convergence (Trend/Momentum)**
Hypothesis: khi GFS lạnh hơn ECMWF (hoặc ngược) nhiều ngày, thị trường đứng; khi hai model hội tụ về một phía, giá move mạnh (uncertainty resolve) · Signal: |GFS HDD − ECMWF HDD| (day 6–10) > 1σ trong ≥2 ngày rồi đồng phẳng về một phía.
Trade: vào theo phía hội tụ sau 12Z; exit 2–4 ngày; stop 1.5×ATR · Risk: hội tụ giả (1 model nhảy lại) · Data: bảng so model (PointLogic/EarthNC/Bespoke) · Coupling: tránh ngày EIA.

**S7 — Prompt-spread trend proxy (Trend/Momentum)**
Hypothesis: spread front/tháng sau mùa withdrawal là thước physical tightness dẫn hướng giá — spread nới liên tiếp thì giá front có xu hướng đi tiếp · Signal: spread front−2nd (hay Mar−Apr khi áp dụng) nới ≥3 phiên liên tiếp.
Trade: long front CFD khi spread tiếp tục nới; exit khi spread chạm hẹp 2 phiên; stop 1.8×ATR · Risk: roll mechanics nhiễu quanh expiry · Data: term structure futures (CFD broker có thể thiếu — ràng buộc data) · Coupling: mùa withdrawal.

**S8 — 8–14-day flip regime (Trend/Momentum)**
Hypothesis: flip "above-normal → below-normal" (hoặc ngược) trong NOAA 8–14 day là đổi regime kỳ vọng — move kéo dài hơn 1 ngày · Signal: NOAA 8–14 map flip cho vùng consuming chính (Midwest/NE, ≥40% diện tích).
Trade: theo hướng flip, hold 3–7 ngày, stop 1.5×ATR; thoát nếu flip lật lại trong 2 ngày · Risk: flip lặp qua lại (progressive pattern) · Data: NOAA CPC archive · Coupling: mùa giao mùa (Sep–Oct, Mar–Apr) mạnh nhất.

**S9 — ADX trend regime tách season (Trend/Momentum)**
Hypothesis: trend persistence khác nhau giữa hai season — cùng signal ADX phải đọc hai cách; eval tách khung tránh lai mẫu · Signal: ADX(14) > 25 cắt lên + DI+ > DI− (long), chỉ khi season có catalyst (withdrawal: HDD revise lên; injection: CDD revise lên).
Trade: classic DI trailing; time-stop 15 ngày · Risk: chop giữa season · Data: giá + HDD/CDD index · Coupling: expectancy phải tính TỪNG season, không gộp.

**S10 — Storage-miss streak momentum (Trend/Momentum)**
Hypothesis: 3 EIA liên tiếp lệch cùng hướng vs consensus cho thấy market定价 sai balance nền → drift định giá lại 1–2 tuần · Signal: 3 tuần liên tiếp actual tighten hơn consensus cùng hướng.
Trade: long (nếu tighten) vào close Thursday sau miss thứ 3; hold 10 ngày; stop 1.5×ATR · Risk: tuần thứ 4 đảo vì weather đổi · Data: EIA weekly + consensus poll (S&P/Reuters) · Coupling: hợp nhất với hướng storage-deviation đang co.

### 2.2 Family: Mean-reversion — storage-norm anchor là trục (S11–S20)

**S11 — Storage-norm band fade (Mean-reversion)**
Hypothesis: giá mean-revert quanh mức tương ứng balance; storage lệch norm quá xa + giá đã move cùng hướng cực đại → fade ngược có xác suất · Signal: storage deviation vs 5-yr norm vượt ±2σ của phân phối 10-năm THEO MÙA + giá move cùng hướng ≥15% trong 20 ngày.
Trade: fade ngược hướng giá (nghịch lệch storage), tối đa 2 lần avg-down; target khi deviation co về 1σ; stop 2.5×ATR · Risk: era-shift (LNG demand mới) làm norm cũ sai — dùng rolling 5-yr · Data: EIA storage + norm series, giá · Coupling: tắt khi supply-shock event active (freeze/bão).

**S12 — Spike-no-cause fade (Mean-reversion)**
Hypothesis: intraday move ≥8% KHÔNG kèm news/production/feedgas change là liquidation/squeeze — hoàn lại phần lớn trong 1–3 ngày · Signal: daily move >8%; xác nhận không event trong calendar + feedgas/production flat.
Trade: fade 30% vào close ngày spike; target 40–60% retrace; stop trên high/low ngày spike +0.3×ATR · Risk: đó là leak/freeze bắt đầu — check production trước khi vào · Data: calendar events, feedgas nominations, giá · Coupling: không dùng giữa bão/đông lạnh active.

**S13 — RSI(2) extremum mùa ấm (Mean-reversion)**
Hypothesis: injection season (Apr–Oct) giá bị cap bởi demand yếu — oversold ngắn hạn bounce đều đặn · Signal: RSI(2) < 10 trên daily, chỉ Apr–Oct.
Trade: long close hôm đó; exit khi RSI(2) > 60 hoặc 4 ngày; stop 2×ATR(10) · Risk: rơi tự do khi LNG outage (Freeport-style) — feedgas check trước · Data: giá, feedgas · Coupling: bỏ qua nếu feedgas đang giảm >1 Bcf/d ngày đó.

**S14 — Cold-snap exhaustion short (Mean-reversion)**
Hypothesis: spike do cold snap được giá trước 3–5 ngày; đến khi HDD forecast plateau (đỉnh), giá đã phản ánh xong — "buy rumor sell fact" ở mức aggregate · Signal: giá +15% trong 3 ngày + HDD forecast ngừng revise lên (plateau) + RSI daily >75.
Trade: short phiên sau khi plateau xác nhận; cover khi 8–14 day về neutral; stop trên high của spike +0.5×ATR · Risk: freeze-off song song (supply mất) — KHÔNG short nếu production đang giảm · Data: HDD forecasts, production, giá · Coupling: phân biệt nghiêm với S3 (continuation).

**S15 — Summer-range cap short (Mean-reversion)**
Hypothesis: injection season không heat-wave → storage build áp đầu giá — biên trên range nhiều lần không xuyên được · Signal: giá chạm biên trên 60-day range lần 2+ mà CDD forecast không revise lên; volume giảm dần.
Trade: short tại biên, stop trên biên +0.7×ATR; target giữa range; time-stop 10 ngày · Risk: heat dome bất thường (Jul-Aug kiểu 2023) · Data: giá, CDD forecasts · Coupling: tắt trong heat advisory active.

**S16 — Weekend-gap fill (Mean-reversion)**
Hypothesis: gap mở Chủ nhật từ weather-news cuối tuần thường over-shoot vì liquidity mỏng — phần lớn fill trong tuần · Signal: gap >2.5% theo hướng bất kỳ, không kèm event structural (freeze/outage).
Trade: fade về mức close Thứ Sáu cũ; stop 1.2×ATR; time-stop 3 ngày · Risk: gap đúng hướng xu hướng mùa đông mạnh (gap-and-continue) — chỉ fade gap ngược hướng 20-day trend · Data: session open/close · Coupling: mùa đông giảm size một nửa.

**S17 — Fair-value residual revert (Mean-reversion)**
Hypothesis: fair-value regression đơn giản (giá ~ f(storage deviation, feedgas, HDD 30 ngày)) → residual cực đoan revert · Signal: |residual| > 2σ rolling 1 năm.
Trade: fade residual về 0.5σ; stop khi residual > 2.5σ; horizon 10 ngày · Risk: model spec sai (era shift) → residual walk; re-fit rolling · Data: storage, feedgas, HDD, giá · Coupling: dùng làm allocator (chỉ long-block khi residual âm).

**S18 — Post-EIA vol crush (Mean-reversion)**
Hypothesis: sau 1 EIA lớn, realized vol ngày 2–5 co lại rõ (uncertainty release) — range nhỏ fade được · Signal: |EIA surprise| ≥ 30 Bcf; đo HV(5) trước/sau.
Trade: fade chạm biên range 2 phiên quanh mức close ngày EIA; stop 0.8×ATR · Risk: tuần sau có model flip · Data: EIA, giá intraday · Coupling: không dùng nếu 8–14 day đang flip (S8).

**S19 — Widow-maker decay (Mean-reversion)**
Hypothesis: winter premium tích trong Nov–Feb decay cấp số vào 2 tuần cuối Feb–Mar khi heating season chấm dứt mechanically · Signal: vào 15-Feb hằng năm.
Trade: short bias 3 tuần (tài khoản futures: short Mar/long Apr spread — phần spread logic của ý); stop nếu HDD revise lên mạnh lần cuối; trailing 20-day high · Risk: cold burst cuối mùa — chính là cái tên widow-maker; size nhỏ + gate production ổn · Data: giá Mar/Apr futures, HDD · Coupling: tắt khi forecast cực lạnh (guard S14).

**S20 — Weather-analog kNN path (Mean-reversion)**
Hypothesis: các năm có cấu trúc (storage deviation, HDD path, LNG) tương tự cho path 5–15 ngày có khuynh hướng revert quanh mean của nhóm analog · Signal: kNN k=15 trên (storage dev, 30d HDD, feedgas); giá đang ở percentile 10/90 của path phân phối analog.
Trade: fade về median path analogs; stop ngoài min/max analogs; time-stop 15 ngày · Risk: event chưa từng có trong history (Uri 2021 không analog) · Data: bảng lịch sử biến + giá · Coupling: luôn báo khoảng min–max analog như confidence band.

### 2.3 Family: Breakout/Vol-expansion (S21–S30)

**S21 — Pre-EIA range break (Breakout/Vol-expansion)**
Hypothesis: biên range 20h trước EIA xác nhận consensus; break biên sau số liệu là đường re-pricing thật · Signal: đánh dấu high/low từ 14:30 ET T4 đến 10:30 ET T5; break sau số liệu giữ được sau 10:45 ET.
Trade: vào pullback đầu tiên phía break (không chase 5 phút đầu); stop bên kia biên range; target 1.5R rồi trailing · Risk: whipsaw hai biên 15 phút đầu · Data: EIA + consensus, giá intraday · Coupling: cùng hướng storage-miss streak (S10) thì size lớn hơn.

**S22 — NY ORB có model-catalyst (Breakout/Vol-expansion)**
Hypothesis: opening range breakout 09:00–10:30 ET chỉ có edge khi có catalyst weather mới (12Z/revision) — không catalyst thì fade · Signal: range 09:00–10:30 ngày có HDD revision ≥1σ; break + giữ 30 phút.
Trade: vào retest của break; stop nửa range; exit cuối phiên (không hold) · Risk: catalyst đã priced overnight — check gap trước · Data: HDD revisions timestamps, giá intraday · Coupling: không dùng ngày EIA.

**S23 — NR7 compression breakout (Breakout/Vol-expansion)**
Hypothesis: ngày range hẹp nhất 7 ngày (NR7) trước weather-report mới → nén rồi giãn có hướng theo revision đầu · Signal: NR7 ngày T; ngày T+1 break biên T cùng hướng HDD revision.
Trade: stop-order hai biên T+1 (OCO); stop nửa range T; target 2R · Risk: breakout ngược hướng revision (trap) — cắt nhanh · Data: giá, HDD revision T+1 · Coupling: mùa giao mùa tốt nhất.

**S24 — Quiet-weather compression → first-revision break (Breakout/Vol-expansion)**
Hypothesis: 3 ngày "boring weather" nén vol; revision đầu sau im lặng là ignition của xu hướng mới · Signal: 3 ngày revision gần 0 + ATR(5) < 0.6×ATR(50).
Trade: break theo hướng revision đầu, stop 1×ATR sau expansion; trailing 3×ATR · Risk: revision đơn lẻ rồi lại im (fade) · Data: revision series, giá · Coupling: xác nhận bằng break biên 20 ngày (không chỉ intraday).

**S25 — Stop-hunt sweep & reclaim (Breakout/Vol-expansion)**
Hypothesis: quanh 13:00–14:00 ET, giá quét prior-day high/low rõ rồi reclaim — bẫy stop trước khi chạy thật · Signal: sweep prior-day extreme >0.4×ATR rồi đóng lại trong biên trong 30 phút.
Trade: vào khi reclaim xác nhận (close 15-min trong biên cũ); stop tại sweep extreme; target đối biên range · Risk: breakout thật (không reclaim) — cắt khi 2 nến 15' đóng xuyên · Data: giá intraday · Coupling: mạnh quanh expiry/pinning hằng tháng.

**S26 — HV-percentile expansion entry (Breakout/Vol-expansion)**
Hypothesis: HV(10) percentile >90 rồi co về 60–70 là "armed" state — direction trade sau đó có expectancy tốt hơn baseline · Signal: chuỗi HV như trên + breakout 10-day high/low.
Trade: theo break, stop 1.2×ATR, trailing — không target cứng · Risk: vol spike do event một lần (fade ngay) · Data: giá · Coupling: meta-filter cho S23–S25.

**S27 — Weekend gap continuation-vs-fill (Breakout/Vol-expansion)**
Hypothesis: gap >3% Chủ nhật: tiếp tục hướng gap nếu có cause structural (freeze/bão/path đổi), fill nếu chỉ noise weather-chat · Signal: gap ≥3% + phân loại cause.
Trade: continuation: vào 30' sau open, stop nửa gap; fill: fade như S16 · Risk: misclassify cause · Data: news scan cuối tuần, giá · Coupling: feedgas Monday 06:00 ET check confirm cause.

**S28 — Contract-roll range reset breakout (Breakout/Vol-expansion)**
Hypothesis: sau broker roll sang contract mới, reference levels reset — breakout biên 3 ngày đầu contract dễ follow vì thiếu "memory" stops cũ · Signal: high/low 3 phiên đầu tiên contract mới.
Trade: break + giữ, stop nửa range 3 ngày · Risk: roll trùng boring weather → false · Data: lịch expiry broker, giá · Coupling: season catalyst đang active mới dùng.

**S29 — 52-week-high kèm deficit (Breakout/Vol-expansion)**
Hypothesis: new 52-week high trong Nov–Jan kèm storage deficit = trend thuật mùa cực mạnh (mean-revert bị碾) · Signal: close > 52-week high + storage deficit >100 Bcf.
Trade: long pullback đầu về mức cũ (support flip); stop dưới swing 5-day; hold đến khi storage chuyển surplus hoặc HDD season kết thúc · Risk: đỉnh giá winter đột ngột (S19 decay bắt kịp) · Data: giá, storage · Coupling: COT managed money chưa quá dài (guard S71).

**S30 — EIA-candle breakout retest (Breakout/Vol-expansion)**
Hypothesis: nến 5 phút đầu sau EIA vẽ biên thật; retest biên trong 60–90 phút là entry chuẩn xác nhất (không chase) · Signal: nến 5' break biên pre-report; giá retest biên từ phía đúng.
Trade: limit tại biên nến; stop bên kia 50% nến; target 2R/trailing · Risk: retest xuyên (failed break) — cắt khi 2 nến 5' đóng xuyên · Data: giá 5', EIA · Coupling: phiên bản kỷ luật hơn S21 — dùng một trong hai.

### 2.4 Family: Carry/Seasonal — winter/summer spread logic, seasonal roll (S31–S40)

**S31 — Classic Nov long (gate storage) (Carry/Seasonal)**
Hypothesis: long "winter coming" từ giữa Oct có drift dương lịch sử khi storage không quá surplus · Signal: 15-Oct hằng năm.
Trade: long 45 ngày nếu surplus < +250 Bcf; ngược lại không trade (hoặc chuyển S39 short context) · Risk: năm ấm surplus → drift âm · Data: storage, CPC winter outlook · Coupling: HDD forecast đầu Nov không cực ấm.

**S32 — Short-March/long-April decay (Carry/Seasonal)**
Hypothesis: widow-maker spread Mar−Apr co về 0 khi heating season kết thúc — carry decay đều đặn; spread kinh điển nhất của gas · Signal: vào 10–15 Feb.
Trade: futures: short Mar/long Apr 1:1 hold đến 25 Mar, stop khi HDD Mar revise cực mạnh; CFD: proxy short NATGAS 10 ngày size nửa · Risk: cold burst cuối mùa (tên gọi widow-maker); size ≤ nửa bình thường · Data: Mar/Apr futures (cần futures thật), HDD · Coupling: production ổn định (không freeze watch active).

**S33 — Injection-season fade Apr (Carry/Seasonal)**
Hypothesis: premium winter còn sót trong giá đầu Apr evaporates khi demand heating mất — drift âm 2–4 tuần · Signal: 01–05 Apr hằng năm.
Trade: short bias 15–20 ngày; stop 1.5×ATR; cover khi 12-month spread về norm · Risk: năm cold April kéo dài (hiếm) · Data: giá, spreads · Coupling: không dùng nếu forecast Apr below-normal rõ.

**S34 — September shoulder weakness (Carry/Seasonal)**
Hypothesis: Sep = đáy demand (hết nóng chưa lạnh) + injection cao điểm → drift âm/flat; nhiều năm đáy giá năm vào Aug–Sep · Signal: 01 Sep hằng năm.
Trade: short 3 tuần nếu (i) storage surplus, (ii) không bão active trong Gulf; stop 1.5×ATR · Risk: hurricane Sep trực tiếp Gulf; heat dome Sep hiếm · Data: giá, NHC, storage · Coupling: thoát ngay khi có storm name nhắm Gulf.

**S35 — Jul–Aug heat premium (Carry/Seasonal)**
Hypothesis: power burn mùa nóng đẩy giá khi CDD forecast trên norm — premium nằm trong Jul hơn là Aug muộn (demand decay) · Signal: 20 Jun – 10 Jul, CDD forecast > norm + storage không quá surplus.
Trade: long 3 tuần; stop 1.5×ATR; exit khi CDD về norm · Risk: mùa hè mát (kiểu 2024) · Data: CDD forecasts, storage · Coupling: ERCOT/PJM load tăng (S65) tăng chất lượng.

**S36 — End-March storage projection trade (Carry/Seasonal)**
Hypothesis: market giá theo projected end-of-winter storage — projection <1.750 Bcf → bid winter; >2.100 → offering · Signal: projection = storage hiện tại + pace HDD-weighted (mô hình 10 dòng), từ 01 Dec.
Trade: bias long/short theo projection; re-eval mỗi EIA; exit cuối Feb · Risk: projection sai vì weather path đổi — re-eval tuần bắt buộc · Data: storage, HDD pace · Coupling: trục nhận thức cho S11/S37.

**S37 — Season×storage regime matrix (Carry/Seasonal)**
Hypothesis: 2×3 matrix (injection/withdrawal × deficit/neutral/surplus) = 6 regime với drift/vol khác nhau — phân bổ bias theo bảng thay vì signal đơn · Signal: phân loại mỗi thứ Hai.
Trade: bias theo bảng (withdrawal+deficit = long-bias 70% size; injection+surplus = short-bias); các ý khác overlay · Risk: era shift — bảng tính lại rolling mỗi năm · Data: giá, storage · Coupling: khung regime của lane.

**S38 — Halloween entry (Carry/Seasonal)**
Hypothesis: 31-Oct là mốc sentiment "winter on" — vào long đúng mốc có median return dương trong nhóm năm không surplus · Signal: 31-Oct, storage deficit hoặc neutral.
Trade: long đến 15-Dec; stop 2×ATR · Risk: trùng bản chất S31 nhưng mốc khác — chọn bằng backtest; tồn tại song song như hypothesis rival · Data: giá, storage · Coupling: Halloween lạnh đầu tiên = confirm nhanh.

**S39 — May shoulder short (Carry/Seasonal)**
Hypothesis: "sell in May" bản gas: hết暖气 demand, chưa cooling — drift âm 3 tuần trung bình · Signal: 01 May hằng năm.
Trade: short 15–20 ngày, stop 1.5×ATR, thoát sớm nếu CDD revision lên sớm · Risk: LNG outage/supply đột ngột · Data: giá, feedgas · Coupling: feedgas ổn định mới vào.

**S40 — Calendar-spread roll-yield harvest (Carry/Seasonal)**
Hypothesis: curve backwardation sâu (tight) → long front + short deferred thu roll yield dương không cần giá đi · Signal: (front − m+3) > 60th percentile lịch sử.
Trade: cấu trúc trên hold 2 tuần; exit khi spread co về 40th pct · Risk: supply-shock đảo balance nhanh · Data: term structure (cần futures data) · Coupling: chỉ withdrawal + storage deficit; CFD proxy: long-bias front khi backwardated.

### 2.5 Family: Session/Time-of-day — EIA reaction, model-run reaction (S41–S50)

**S41 — EIA first-5min vs 30-min divergence (Session/Time-of-day)**
Hypothesis: khi 5' đầu đi một hướng rồi 30' đảo (failed knee-jerk), hướng 30' có follow đến cuối phiên · Signal: so close 10:35 vs 11:00.
Trade: theo hướng 11:00; stop 1×ATR intraday; exit 14:30 ET · Risk: cả hai cùng hướng (trend day) — không trade nếu không divergence · Data: giá 1–5', EIA · Coupling: surprise >25 Bcf mới dùng.

**S42 — Post-12Z drift (Session/Time-of-day)**
Hypothesis: 12Z outputs ~13:00 ET tạo drift có hướng đến 14:30–15:00 ET khi revision đáng kể; drift có momentum qua phiên sau · Signal: HDD revision 12Z ≥1σ.
Trade: vào 13:30 ET theo hướng; exit 15:00 ET hoặc hold đến 10:00 ET hôm sau nếu NY cùng hướng; stop 0.8×ATR · Risk: 00Z qua đêm phủ revision · Data: model output timestamps, giá intraday · Coupling: mùa đông only.

**S43 — Asian-session range fade (Session/Time-of-day)**
Hypothesis: 20:00–02:00 ET liquidity mỏng, giá OU quanh fair của NY close — fade biên range Á khi không tin · Signal: giá chạm biên ±0.8×ATR-intraday phiên Á.
Trade: fade về giữa; stop 0.5×ATR; thoát trước 07:00 ET · Risk: overnight weather surprise/bão — tắt khi NHC active · Data: giá intraday · Coupling: không dùng đêm post-EIA.

**S44 — NY 09:00 momentum ignition (Session/Time-of-day)**
Hypothesis: 09:00–09:30 với gap nhỏ + tin weather mới tạo ignition move có follow đến 11:00 · Signal: move >0.6×ATR daily trong 09:00–09:30, gap mở <1%.
Trade: vào 09:35 pullback; stop 09:00 open; exit 11:00 ET · Risk: ignition trap (revert trước 10:00) · Data: giá intraday, news · Coupling: EIA-day bỏ (chuyển S21/S30).

**S45 — Friday-into-weekend flat fade (Session/Time-of-day)**
Hypothesis: 13:00–17:00 ET Friday, books flatten trước weekend → drift ngược vị thế tuần (profit taking) nhẹ nhưng đều · Signal: tuần có trend rõ (|5-day return| >2×ATR).
Trade: fade nhỏ hướng trend 13:00–16:00 ET Friday; flat 17:00 ET · Risk: Friday trend day · Data: giá intraday · Coupling: chỉ tuần KHÔNG có event cuối tuần chờ đợi (bão/model).

**S46 — Vol-adjusted event policy (Session/Time-of-day)**
Hypothesis: meta-rule: giảm size 50% và không mở position mới sau 10:00 ET Thursday — EV của pre-EIA entries tệ vì spread/vol chờ · Signal: calendar.
Trade: policy layer trên mọi ý khác; flat hoặc giảm trước 10:30 · Risk: mất vài entry đẹp hiếm — chấp nhận · Data: lịch · Coupling: áp toàn lane; giá trị nằm ở cost avoidance.

**S47 — Sunday-open 30-minute rules (Session/Time-of-day)**
Hypothesis: 18:00–18:30 ET Chủ nhật liquidity tệ nhất tuần — moves đầu thường false/over-shot; 18:30–19:00 mới có fair price · Signal: thống kê gap retention 18:30 vs 20:00.
Trade: mọi gap-trade (S27) execute sau 18:30 ET · Risk: bỏ phần đầu gap thật · Data: giá intraday Chủ nhật · Coupling: kết hợp S27.

**S48 — Pre-holiday liquidity drain fade (Session/Time-of-day)**
Hypothesis: trước Thanksgiving/Christmas/July-4 desks rút → range nhỏ + spike nhỏ tự hoàn (noise không ai defend levels) · Signal: calendar ±1 ngày lễ Mỹ lớn.
Trade: fade mọi move >0.7×ATR trong phiên; stop 0.5×ATR; flat trước close · Risk: thật sự có weather event trong lễ · Data: calendar, giá · Coupling: không trade 24-Dec và 31-Dec (dead market).

**S49 — 14:30 settlement momentum (Session/Time-of-day)**
Hypothesis: nến đóng settlement 14:30 ET chứa index/ETF marking flow — nếu break biên ngày với volume, hướng đó có follow vào Globex tối · Signal: nến 14:30 break prior high/low ngày + volume >1.5× trung bình nến cùng giờ.
Trade: vào 14:45; stop nửa nến; exit 20:00 ET · Risk: marking noise (no follow) · Data: giá/volume intraday · Coupling: mùa đông hiệu quả hơn.

**S50 — Overnight-cold-gap reward (Session/Time-of-day)**
Hypothesis: mùa đông, đêm lạnh bất thường (nowcast < forecast) tạo động lượng 02:00–06:00 ET ít người canh — giữ long overnight trong cold pattern có premium kỳ vọng · Signal: nowcast overnight temps ≥8°F dưới forecast cho consuming regions + pattern below-normal active.
Trade: long 20:00 ET, exit gap-up open NY; stop 1×ATR · Risk: đêm ấm hơn nowcast (gap xuống) · Data: nowcast temps (METAR), giá · Coupling: chỉ khi S8 regime below-normal active.

### 2.6 Family: Event/Data-driven — EIA surprise, forecast revisions (S51–S60)

**S51 — EIA surprise directional trade (Event/Data-driven)**
Hypothesis: surprise |actual − consensus| ≥ 25 Bcf move giá 2–5 ngày theo hướng surprise (under-reaction tuần đầu) · Signal: surprise Bcf so poll consensus.
Trade: vào 11:00 ET Thursday theo hướng; stop 1.5×ATR; exit 3–5 ngày hoặc khi streak đối dấu · Risk: surprise bị weather tin mới phủ · Data: EIA + consensus poll · Coupling: cùng hướng storage-deviation trend thì size×1.5.

**S52 — Norm-crossing regime shift (Event/Data-driven)**
Hypothesis: storage cross 0-deviation vs 5-yr norm (sau ≥6 tuần một phía) đổi volatility regime — tuần đầu sau crossing có xu hướng chạy tiếp hướng crossing · Signal: EIA weekly deviation đổi dấu.
Trade: theo hướng crossing, hold 2 tuần; stop 1.5×ATR · Risk: crossing giả (nhảy qua lại quanh 0) · Data: storage series · Coupling: xác nhận bằng injection pace (S53).

**S53 — Required-pace tracker bias (Event/Data-driven)**
Hypothesis: pace thực 4 tuần so pace cần để đạt target cuối mùa = fundamental bias nền — chênh lệch lớn → drift nhiều tuần · Signal: (pace thực − pace cần) > +10 Bcf/tuần (bearish) hoặc < −10 (bullish).
Trade: bias tuần theo chênh lệch; re-eval mỗi EIA; time-stop 4 tuần · Risk: weather path đổi làm "pace cần" nhảy · Data: storage, HDD forecasts · Coupling: nền tảng của S36; regime cho mọi ý trend.

**S54 — Feedgas-drop short (Event/Data-driven)**
Hypothesis: feedgas giảm >1.5 Bcf/d day-over-day (outage unplanned) là demand-shock đo trực tiếp — giá phản ứng 1–2 ngày đủ dài để theo · Signal: nominations sáng sớm vs hôm trước.
Trade: short khi xác nhận drop không phải maintenance plan; cover khi feedgas hồi ≥70%; stop 1.5×ATR · Risk: drop do bão (supply cũng mất) — phân loại cause · Data: daily feedgas, maintenance calendar · Coupling: cross-check S4 hurricane state.

**S55 — Outage-headline spike fade (Event/Data-driven)**
Hypothesis: headline LNG outage đầu tiên spike quá mức so impact thực (Bcf/d mất × số ngày) — fade sau 15–30 phút khi sizing đúng · Signal: spike >4% trong 15 phút + impact tính toán < mức spike ngụ ý.
Trade: fade về mức implied; stop trên spike high; time-stop trong ngày · Risk: theo sau là outage lớn hơn (chuỗi sự kiện) · Data: news real-time, feedgas, giá · Coupling: không fade nếu song song supply-shock tự nhiên.

**S56 — STEO revision trade (Event/Data-driven)**
Hypothesis: STEO làm việc hóa narrative — revision lớn forecast production/giá tạo drift tuần · Signal: STEO tháng này vs trước: production ±0.5 Bcf/d hoặc price forecast ±8%.
Trade: theo hướng revision (bearish forecast → short bias) 1 tuần; stop 1.5×ATR · Risk: STEO lag market (đã priced) · Data: EIA STEO history · Coupling: case sống Sep-2026: 2027 hạ $4.60→$3.28.

**S57 — Rig-count confirmation (Event/Data-driven)**
Hypothesis: rig count là supply signal yếu-lag; chỉ đáng dùng làm confirmation cùng hướng trend giá, không entry · Signal: rig ±≥5 rigs cùng hướng trend giá 4 tuần.
Trade: giữ position theo trend; exit sớm nếu rig ngược dấu giá 2 tuần liên tiếp · Risk: quan hệ rig–production broken (efficiency) · Data: Baker Hughes, giá · Coupling: filter cho S9/S29.

**S58 — NOAA 8–14 flip entry (Event/Data-driven)**
Hypothesis: 8–14 day flip nguyên vùng consuming là "second opinion" xác nhận model — entry theo flip có xác suất cao hơn single-model revision · Signal: 8–14 map flip dấu cho Midwest+NE (≥40% diện tích).
Trade: theo flip ngày release; hold 5 ngày; stop 1.5×ATR · Risk: flip lặp (progressive) · Data: NOAA CPC archive · Coupling: aggregate version của S8 — chọn 1 trong 2 sau backtest, không chạy trùng.

**S59 — Nowcast-vs-model discrepancy (Event/Data-driven)**
Hypothesis: actual temps đầu tuần lệch mạnh so forecast đã priced → "catch-up revision" tuần sau — trade trước khi model kịp cập nhật · Signal: |nowcast 3 ngày − forecast priced| > 4°F consuming region.
Trade: theo hướng revision sẽ đi (nóng hơn forecast → short heating bid); hold 3 ngày; stop 1×ATR · Risk: discrepancy tự nhiên (microclimate) · Data: nowcast vs forecast, giá · Coupling: mùa giao mùa mạnh nhất.

**S60 — Morning feedgas pre-positioning (Event/Data-driven)**
Hypothesis: nominations 06:00–08:00 ET báo record/đáy trước NY open → NY定价 theo — position trước 09:00 có edge nhỏ nhưng đều · Signal: feedgas sáng = max/min 30 ngày.
Trade: long/short vào 08:30 ET; exit 13:00 ET; stop 0.7×ATR · Risk: renomination đổi số liệu sau 2 giờ · Data: pipeline nominations · Coupling: mùa đông + cold pattern tăng xác suất.

### 2.7 Family: Cross-asset/Correlation — TTF-Europe linkage, WTI weak link, power demand (S61–S70)

**S61 — TTF−HH spread channel monitor (Cross-asset/Correlation)**
Hypothesis: HH chỉ nhận global shock QUA kênh export: TTF/JKM − HH giãn → feedgas tăng → HH nhận phần nhỏ; khi spread cực đại nhưng feedgas KHÔNG tăng (terminal bão hòa — trạng thái Sep-2026), kênh tắc · Signal: spread TTF−HH > 90th pct + feedgas flat 5 ngày.
Trade: fade mọi spike HH do "global gas news" (short HH vào spike); stop trên spike; time-stop 2 ngày · Risk: supply-shock nội địa song song · Data: TTF/JKM, feedgas, HH · Coupling: minh chứng sống Sep-2026 (Hormuz: TTF €60 vs HH $3).

**S62 — WTI-confirm gate (Cross-asset/Correlation)**
Hypothesis: breakout NATGAS có WTI cùng chiều cùng ngày có độ tin cao hơn — energy-complex confirmation lọc bớt noise weather đơn lẻ · Signal: NG break 20-day + WTI cùng hướng ≥1%.
Trade: dùng làm gate cho S2/S24; stop như ý gốc · Risk: oil bị factor riêng (OPEC) chi phối làm gate sai · Data: NG, WTI · Coupling: không dùng khi oil có meeting/geo event riêng.

**S63 — USDCAD divergence tell (Cross-asset/Correlation)**
Hypothesis: NATGAS spike mà USDCAD không phản ứng kiểu energy-shock (CAD không mạnh) → spike nội địa weather, sẽ fade; oil-shock thật thì CAD theo · Signal: NG +5% intraday, USDCAD flat/up.
Trade: classify spike: internal (fade như S12) vs complex (để chạy); execute theo classification · Risk: CAD bị domestic chi phối · Data: NG, USDCAD realtime · Coupling: phân loại cho S12/S55.

**S64 — XAUUSD risk-gate (Cross-asset/Correlation)**
Hypothesis: session risk-off thật (XAU spike + USD mạnh) làm mọi commodity bid yếu — NATGAS breakout trong khung đó follow kém; gate loại bớt · Signal: XAU +1% và USD index +0.5% cùng phiên.
Trade: chặn entry breakout mới trong khung 4h; treo entry chờ hết khung · Risk: gate quá dãn (miss entries) · Data: XAUUSD, USD index · Coupling: meta-filter cho family breakout.

**S65 — ERCOT/PJM load-pull (Cross-asset/Correlation)**
Hypothesis: forecast load ERCOT/PJM cao kỷ lục (heat) → power burn gas tăng theo mix — NATGAS có bid trước heat thật 1–2 ngày · Signal: ERCOT 3-day load forecast > 95th pct mùa.
Trade: long 1 ngày trước peak-load; exit sau peak; stop 1×ATR · Risk: renewables lấp (wind/solar cao) làm gas-burn thấp hơn · Data: ERCOT/PJM load forecasts (public) · Coupling: kết hợp S35 (Jul–Aug window).

**S66 — Coal-to-gas switching band (Cross-asset/Correlation)**
Hypothesis: giá gas thấp so coal → power burn co giãn tối đa (demand floor cứng); vùng giá cao hơn gas mất share đột ngột (ceiling mềm) · Signal: ngưỡng thermal parity ± transport tính từ giá gas & coal.
Trade: long-bias tại zone floor; né/short-bias tại zone ceiling (overlay các ý khác) · Risk: policy/coal retirements dịch band · Data: gas, coal prices (EIA công khai) · Coupling: biến đầu vào cho S17 fair-value.

**S67 — BRENT-ratio extremes (Cross-asset/Correlation)**
Hypothesis: ratio NATGAS/BRENT cực đoan (percentile 5 năm) phản ánh associated-gas economics + relative-value flow — revert chậm · Signal: ratio z-score |z| > 2.
Trade: fade ratio bằng long weak/short strong (cần cả 2 symbol — có trong universe); hold 2–4 tuần; stop z > 2.8 · Risk: structural shift LNG dịch band (2016+, 2025-26) · Data: NG, BRENT · Coupling: S81 là bản WTI chi tiết hơn — chọn 1 tránh double-count.

**S68 — EURUSD beta gate (Cross-asset/Correlation)**
Hypothesis: NATGAS beta EURUSD ~0 nhưng có túi âm nhỏ với "USD-complex rally" — chỉ đáng làm gate size, không phải signal · Signal: EURUSD −0.8% trong ngày.
Trade: giảm 30% size mọi long commodity hôm sau · Risk: quan hệ giả (noise) · Data: EURUSD · Coupling: meta-filter yếu — chỉ giữ nếu backtest chương trình xác nhận.

**S69 — Beta-neutral long NG/short WTI mùa đông (Cross-asset/Correlation)**
Hypothesis: withdrawal season NG có drift dương riêng (weather premium) mà WTI không có — cặp long NG/short WTI (beta 60-day) thu seasonal premium giảm energy-market risk · Signal: vào 15-Nov hằng năm.
Trade: exit 15-Feb hoặc khi spread −2×ATR; rebalance beta hàng tuần · Risk: oil rally geo trong khi gas flat — margin 2 chân · Data: NG, WTI, beta rolling · Coupling: S31 + beta hedge; cần 2 symbol.

**S70 — Correlation-break regime alert (Cross-asset/Correlation)**
Hypothesis: khi corr(NATGAS, WTI) 60-day sập về 0/âm, NATGAS bị factor nội địa (weather/storage) chi phối — tăng weight ý weather/storage; ngược lại tăng weight ý oil-complex sync · Signal: rolling corr cross ±0.15 band.
Trade: allocation layer — không entry riêng · Risk: corr nhảy lặp · Data: NG, WTI · Coupling: dispatcher giữa các ý theo regime.

### 2.8 Family: Positioning/Flows — COT specs cực đoan (S71–S80)

**S71 — COT managed-money extreme fade (Positioning/Flows)**
Hypothesis: specs net-long percentile >90 (non-winter) → crowd full, cần catalyst mới để lên — fade; percentile <10 → squeeze fuel · Signal: COT net position z-score 3 năm.
Trade: fade hướng cực đoan sau báo cáo Thứ Sáu, hold 2 tuần; stop 1.5×ATR · Risk: cực đoan còn cực đoan hơn (momentum year) · Data: CFTC COT · Coupling: không fade cực đoan dài trong withdrawal+deficit (guard S77).

**S72 — Price-new-high/positioning-divergence (Positioning/Flows)**
Hypothesis: giá break 20-day high mà specs không tăng net-long = thiếu fuel — breakout dễ thối; ngược lại specs new-high + giá chưa = fuel chờ spark · Signal: so swing highs giá với swing COT.
Trade: breakout không fuel → short lại breakout (stop trên high); fuel-chờ → long sớm style S2 · Risk: passive/index flow (UNG) phá quan hệ · Data: COT, giá · Coupling: filter cho S2/S29.

**S73 — UNG-flow squeeze proxy (Positioning/Flows)**
Hypothesis: UNG ETF creations lớn (shares tăng nhanh) đẩy mua front-month cơ học — giá trên mép flows vài ngày rồi decay · Signal: UNG shares outstanding tăng >3%/tuần.
Trade: long cùng flows 3–5 ngày; exit khi creations chậm; stop 1×ATR · Risk: AUM data lag 1 ngày · Data: UNG shares/NAV (công khai) · Coupling: mạnh trong winter-vol week.

**S74 — OI-spike-on-cold-forecast fade (Positioning/Flows)**
Hypothesis: OI nổ 2 ngày giá lên vì cold forecast = crowd vào cùng lúc — khi forecast revise lại, tháo hàng cấp số · Signal: OI +10% 2 ngày cùng giá +8%, forecast đã plateau.
Trade: short khi plateau xác nhận; cover khi OI co về baseline; stop trên crowd-high · Risk: forecast upgrade lần 2 (crowd đúng) · Data: OI futures (cần futures data), giá, HDD · Coupling: cousin S14 — S14 price-first, S74 positioning-first.

**S75 — Producer-hedging pressure calendar (Positioning/Flows)**
Hypothesis: producers bán forward theo lịch (post-winter, vào injection season) — pressure bán deferred cản rallies xa trên curve trong Apr–Jun · Signal: (m+3 − front) spread trend theo mùa, nửa đầu năm.
Trade: fade rally front mạnh quá trong Apr–Jun khi deferred không theo; stop 1.5×ATR · Risk: demand-shock (LNG record) đổi pattern · Data: term structure · Coupling: context cho S33/S39.

**S76 — Options-expiry pinning (Positioning/Flows)**
Hypothesis: quanh NG options expiry (vài ngày trước futures expiry), giá bị hút về strike OI lớn nhất — mean-reversion quanh strike mạnh hơn baseline · Signal: strike max-OI xác định; còn 2 ngày expiry; |giá − strike| > 0.5×ATR.
Trade: fade về strike; stop 0.6×ATR; bắt buộc thoát trước expiry 1 ngày · Risk: event/weather trùng tuần expiry (pin fail) · Data: options OI (cần options data) · Coupling: tắt khi có EIA surprise lớn cùng tuần.

**S77 — COT×storage interaction (Positioning/Flows)**
Hypothesis: extremes COT chỉ có nghĩa khi cùng dấu storage deviation: specs-max-long + surplus = fade mạnh nhất; specs-max-long + deficit = trend hợp lệ (đừng fade) · Signal: bảng 2×2 (dấu COT × dấu storage).
Trade: chỉ fade góc "cùng dấu cực đoan"; góc còn lại giữ trend-follow · Risk: COT lag 3 ngày · Data: COT, storage · Coupling: gate trung thực cho S71.

**S78 — Prompt-spread-as-flow indicator (Positioning/Flows)**
Hypothesis: spread front−m+1 phản ánh physical bid (cần gas ngay) — dẫn đường giá cash 1–3 ngày · Signal: spread 3-day trend rõ (nới/chặt) cùng storage dev.
Trade: bias giá theo hướng spread-trend; stop 1.2×ATR; exit khi spread đảo · Risk: roll mechanics nhiễu tuần expiry · Data: term structure · Coupling: không dùng tuần expiry.

**S79 — Retail-sentiment contrarian (Positioning/Flows)**
Hypothesis: retail long% >75% kèm giá flat/down = crowd mắc kẹt wrong-side — revert nhanh khi có shove · Signal: broker sentiment% + price action diverge.
Trade: ngược đám 1–3 ngày; stop 1×ATR · Risk: retail đôi khi đúng (bắt được trend) · Data: broker sentiment feed · Coupling: chỉ quanh price-event (EIA/weekend gap).

**S80 — Index-roll monthly flows (Positioning/Flows)**
Hypothesis: commodity index roll (GSCI/BCOM) tạo buy/sell cơ học vài ngày cố định quanh NG roll — micro drift đo được · Signal: lịch index rebalance + hướng flow cần roll.
Trade: cùng hướng flow cơ học trong cửa sổ 2–3 ngày; size nhỏ; stop 0.8×ATR · Risk: quy mô nhỏ, dễ bị weather lấp · Data: lịch index, term structure · Coupling: chỉ khi quiet weather.

### 2.9 Family: Pattern/Pairs/Stat-arb — NATGAS-WTI ratio, NATGAS-BRENT, HH-TTF nếu có data (S81–S90)

**S81 — NG/WTI ratio band trade (Pattern/Pairs/Stat-arb)**
Hypothesis: ratio NG/WTI (per MMBtu) dao quanh band dài hạn vì substitution + associated gas; vượt band revert chậm (2–6 tuần) · Signal: ratio z-score 3 năm |z| > 2.
Trade: long weak/short strong; exit z về 0.5; stop z 2.8; rebalance theo vol từng chân · Risk: structural break (LNG wave 2025-26 dịch band) · Data: NG, WTI dài hạn · Coupling: tắt khi storage deficit cực đoan (NG có mind riêng).

**S82 — NG/BRENT LNG-oil-indexed linkage (Pattern/Pairs/Stat-arb)**
Hypothesis: một phần LNG Á-Âu giá theo oil-indexed contracts → BRENT cực đoan kéo JKM/TTF → pull feedgas → HH liên kết chậm chỉ hiện ở monthly horizon · Signal: BRENT 20-day move >±12% + HH flat.
Trade: position HH theo hướng oil-delayed (1–3 tuần, size nhỏ); stop 2×ATR · Risk: oil move là geo-spike không bền (bài học Sep-2026) · Data: NG, BRENT, feedgas · Coupling: cần S61 spread channel chưa bão hòa.

**S83 — HH–TTF spread stat-arb nếu có data (Pattern/Pairs/Stat-arb)**
Hypothesis: spread TTF−HH bị arbitrage band (freight+liquefaction ~$2.5–4) giằng — vượt band cực đoan (Sep-2026 ~$15+) không arb thêm được vì capacity limit; chỉ trade HH khi spread mở TRONG band · Signal: spread trong band và mở nhanh >1σ/tuần.
Trade: long HH nhỏ khi spread mở trong band (export pull sẽ tới); stop 1.5×ATR; exit khi feedgas confirm rồi nhường cho trend ý khác · Risk: broker không có TTF — cần data thứ cấp **(cần kiểm chứng availability)** · Data: TTF (ICE), HH, feedgas · Coupling: trái tim phân tích Hormuz Sep-2026.

**S84 — Nov–Mar spread vs storage stat-arb (Pattern/Pairs/Stat-arb)**
Hypothesis: winter spread Nov−Mar tương quan âm với storage projection — spread lệch khỏi regression (quá rẻ cho mức storage) → mua spread và ngược lại · Signal: residual regression |z| > 2.
Trade: spread futures (cần futures account); exit z về 0.7; stop z 2.6 · Risk: năm weather path cực đoan phá quan hệ · Data: term structure, storage · Coupling: futures-only; CFD dùng proxy S19.

**S85 — Energy-residual reversion (Pattern/Pairs/Stat-arb)**
Hypothesis: phần return NG không giải thích bằng beta×(BRENT, WTI) là component nội địa weather/storage — residual cực đoan revert · Signal: |residual 5-day| > 2σ phân phối 2 năm.
Trade: fade residual; stop 2.5σ; time 10 ngày · Risk: residual là trend thật (freeze) — check production trước · Data: NG, WTI, BRENT · Coupling: bản đơn giản của S17 (chỉ prices, không fundamentals).

**S86 — Continuous-vs-front basis drift (Pattern/Pairs/Stat-arb)**
Hypothesis: chuỗi continuous broker trượt so front thật theo roll cost — đo drift để (i) chỉnh backtest, (ii) biết khi nào carry đang ăn người long (contango sâu) · Signal: tracking continuous − front thực quanh roll.
Trade: không entry riêng — hygiene layer; khi contango >90th pct, hạ weight các ý long-carry · Risk: data risk hơn PnL risk · Data: giá broker vs giá NYMEX front · Coupling: bắt buộc cho mọi backtest lane NATGAS.

**S87 — Analog-day clustering direction (Pattern/Pairs/Stat-arb)**
Hypothesis: mỗi ngày một feature vector (storage dev Δ, HDD rev Δ, feedgas Δ, season, vol) → kNN ngày-láng-giềng cho次日 return phân phối lệch trade được · Signal: k=20 neighbors, mean次日 return |z| > 1.5.
Trade: theo hướng mean neighbors; stop 1×ATR; exit 1–3 ngày · Risk: overfit clusters — walk-forward bắt buộc · Data: bảng fundamentals + giá · Coupling: cousin daily-horizon của S20 (15 ngày).

**S88 — OU Asian-session parameters (Pattern/Pairs/Stat-arb)**
Hypothesis: phiên Á là Ornstein-Uhlenbeck ổn định (không news) — ước lượng θ, μ, σ rolling; chỉ trade khi half-life ngắn và đủ biên · Signal: OU half-life < 3h + giá cách mean > 1.5×σ_eq.
Trade: fade về mean, stop 2.2×σ_eq; thoát trước 07:00 ET · Risk: đêm có event (bão/model-leak) · Data: giá tick/5' đêm · Coupling: bản có model của S43 — chọn một.

**S89 — Vol-surface filter (implied vs realized) (Pattern/Pairs/Stat-arb)**
Hypothesis: IV > HV mạnh (variance risk premium cao) = thị trường kỳ vọng event — giảm weight mean-reversion, tăng breakout; IV ≤ HV: premium rẻ, thiên về fade · Signal: IV30/HV20 ratio percentile.
Trade: allocation layer giữa các families · Risk: IV data cần nguồn công khai (CME quotes — cần kiểm chứng availability) · Data: implied vol NG · Coupling: meta-filter toàn lane.

**S90 — Monthly-contract memory pattern (Pattern/Pairs/Stat-arb)**
Hypothesis: mỗi contract-month có "personality" (Jan = winter-peak bid, Apr = widow decay, Sep = shoulder đáy) — return phân phối theo contract-month khác baseline · Signal: vào nửa đầu contract-month theo drift lịch sử tháng đó (gate storage).
Trade: bias theo bảng contract-month × storage-regime; stop 1.5×ATR; exit nửa sau tháng · Risk: double-count với S31–S40 — góc nhìn contract-month khác calendar-entry; chọn sau backtest · Data: giá theo contract, storage · Coupling: khung tổng hợp của S31–S39.

### 2.10 Family: Regime-conditioned/Options-flavored — vol premium mùa đông, straddle quanh forecasts (S91–S100)

**S91 — Pre-winter straddle buy (Regime/Options-flavored)**
Hypothesis: vol mùa đông ramp từ cuối Oct — mua straddle 60 ngày (futures-options) trước khi IV ramp thu VRP direction-agnostic · Signal: vào 15-Oct khi IV < 60th pct mùa.
Trade: long straddle ATM; exit 15-Dec hoặc IV > 85th pct; stop theta 30% premium · Risk: đông ấm + vol không tới (theta bleed) · Data: NG options (cần options account) · Coupling: CFD-proxy = S50 + S26 gộp như synthetic long-vol.

**S92 — Pre-EIA OCO straddle-proxy (Regime/Options-flavored)**
Hypothesis: chờ EIA với biên volatility rõ — 2 stop-order hai biên (OCO) ngay trước 10:30 ET bắt break theo hướng surprise, như long straddle tự chế · Signal: biên ±0.6×expected-move (dựa 8 EIA gần nhất).
Trade: 2 stop orders 10:25 ET; hủy leg còn lại khi 1 side fill; stop gốc 1×biên; target 2×biên · Risk: whipsaw cả hai biên — hiếm nhưng chết; size nhỏ · Data: EIA history, giá · Coupling: phiên bản tools-available của S21 cho broker không options.

**S93 — Winter IV term-structure trade (Regime/Options-flavored)**
Hypothesis: IV các tháng winter thường đắt hơn deferred (hump); khi hump phẳng bất thường, thị trường không price winter risk → mua winter vol/bán deferred vol · Signal: IV(Nov-Feb) − IV(Jun-Aug) < 20th pct vào tháng Sep.
Trade: calendar spread vol (options account); exit khi hump phục hồi; stop khi spread −1.5σ · Risk: năm vol summer cao (heat) giữ cấu trúc phẳng · Data: vol surface NG · Coupling: Sep-2026 là thời điểm check sống (HH $3 + surplus — hump có thể phẳng, cần kiểm chứng).

**S94 — Storage×weather dual-regime switch (Regime/Options-flavored)**
Hypothesis: hai biến regime (dấu storage dev, dấu HDD forecast) tạo 4 khối: long-bias (deficit+cold), short-bias (surplus+warm), còn lại neutral range — bền vì là chính fundamentals · Signal: phân loại mỗi sáng 09:00 ET.
Trade: theo bias khối; neutral chỉ chạy mean-reversion (S13/S16/S43); flip khối → flatten + re-enter · Risk: hai biến flip lặp quanh ngưỡng — thêm hysteresis ±0.25σ · Data: storage, HDD · Coupling: dispatcher trung tâm — nhiều ý reference nó.

**S95 — Hurricane-season event-long bias (Regime/Options-flavored)**
Hypothesis: Aug–Oct, khi có tropical system được number/name, drift dài nhẹ lên (priced rủi ro) decay sau — event-long có xác suất trong cửa sổ · Signal: NHC invest/depression/storm nhắm hướng Gulf 5 ngày.
Trade: long 2 ngày sau khi có number; exit khi path rời Gulf hoặc landfall; stop 1.2×ATR · Risk: path dance (drift lặp) · Data: NHC · Coupling: size nhỏ vì theo path probability.

**S96 — Freeze-off playbook (Regime/Options-flavored)**
Hypothesis: tháng 2, khi temp forecast vùng production (Permian/Haynesville/Appalachia) < 10°F, freeze-off onset có checklist đo được — long theo khung với exit theo production recovery · Signal: forecast < 10°F production regions + giá gap pre-emptive.
Trade: long thoái lui về mức pre-run (không chase đỉnh spike); exit khi production dailies hồi; stop 2×ATR vì noise · Risk: run-up priced hoàn toàn rồi ấm; guard bằng S14 · Data: temps, production dailies · Coupling: đối trọng S14 — cùng mùa, khác cause (supply vs demand).

**S97 — ATR-percentile inverse sizing (Regime/Options-flavored)**
Hypothesis: vol clustering làm size cố định quá rủi ro khi vol đỉnh — inverse-ATR sizing nâng Sharpe của MỌI ý khác không thêm signal mới · Signal: ATR(14) percentile rolling.
Trade: size = base × (median ATR / ATR hiện tại); cap ×1.5, floor ×0.3 · Risk: giảm size đúng lúc breakout lớn — đánh đổi chấp nhận · Data: giá · Coupling: policy layer toàn lane.

**S98 — Winter tail-hedge overlay (Regime/Options-flavored)**
Hypothesis: mỗi Oct mua OTM call ladder (scenario freeze) giá rẻ bảo vệ short-bias book — cấu trúc bảo hiểm dương kỳ vọng trong era LNG pull · Signal: 01-Oct khi book có short-bias cấu trúc.
Trade: call ladder 10–20% OTM; budget premium 1–1.5% NAV/năm; roll tháng 12 nếu chưa dùng · Risk: premium bleed năm ấm · Data: NG options · Coupling: cho phép S33/S34/S39 chạy size đầy mà cap drawdown.

**S99 — Structural-demand dip-buy era (Regime/Options-flavored)**
Hypothesis: era LNG + data-center power demand tạo floor cấu trúc (feedgas 17→20 Bcf/d, narrative EIA 2025-26) — giá <$2.6 kèm storage không nổ surplus là vùng dip-buy có đối trọng fundamentals dài hạn · Signal: giá <$2.6 + surplus < +250 Bcf + feedgas ≥ 16 Bcf/d.
Trade: long scale-in 3 bậc, horizon 1–3 tháng; stop dưới đáy 5 năm −1×ATR; target trung bình mùa · Risk: production tăng nhanh hơn demand · Data: giá, feedgas, storage, STEO · Coupling: case sống Sep-2026 ($2.50–3.35 với 2027 forecast hạ nhưng era-demand vẫn positive).

**S100 — Global-shock transmission checklist (Regime/Options-flavored)**
Hypothesis: mỗi global gas event (Hormuz-type), HH chỉ đáng trade khi checklist kênh truyền mở: (i) TTF/JKM−HH spread còn trong arbitrage band, (ii) feedgas còn capacity headroom, (iii) freight/insurance không tắc — checklist chặn các flop "mua gas vì Trung Đông" · Signal: 3 điều kiện đánh giá mỗi khi có geopolitical headline gas.
Trade: chỉ long HH khi ≥2/3 điều kiện mở; ngược lại fade spike (S61) · Risk: dữ liệu JKM/TTF realtime khó — dùng proxy giá ngày · Data: TTF/JKM, feedgas, freight · Coupling: tổng kết bài học Sep-2026 — chuyển "intuition geo-long" thành checklist đo được.

---

## 3. Tổng hợp cho symbol

### 3.1 Top-10 ideas (tiêu chí: lý do kinh tế rõ, data khả thi, cơ chế không trùng)

| # | Idea | Vì sao chọn |
|---|---|---|
| 1 | **S51 — EIA surprise directional** | Event lớn nhất tuần, data công khai + consensus poll, under-reaction 2–5 ngày chứng kiến được; đúng chất "data-driven" của symbol |
| 2 | **S94 — Storage×weather dual-regime switch** | Dispatcher trung tâm gói fundamentals thật của gas; cấu trúc đơn giản chống overfit; nhiều ý reference nó |
| 3 | **S11 — Storage-norm band fade** | Trục mean-reversion đặc thù NATGAS (anchor norm) — edge cấu trúc không symbol FX nào có |
| 4 | **S1 — HDD-revision momentum** | Driver số 1 của symbol thành signal có quy tắc; họ trend duy nhất sống qua weather-gate |
| 5 | **S61 — TTF−HH spread channel monitor** | Bài học sống Sep-2026 (Hormuz): phân tách HH nội địa vs TTF global đo bằng spread+feedgas; hiếm cross-asset logic được verify real-time |
| 6 | **S21/S30 — Pre-EIA range break + retest** | Kỷ luật hóa phản ứng EIA, chạy được trên CFD broker, risk định nghĩa rõ |
| 7 | **S19 — Widow-maker decay** | Seasonal mechanical mạnh nhất lịch sử symbol; futures-spread hoặc CFD-proxy đều thiết kế được |
| 8 | **S71+S77 — COT extremes có storage-gate** | Positioning công khai; chỉ dùng khi tương tác storage mới tránh fade-against-trend |
| 9 | **S81 — NG/WTI ratio band** | Cặp stat-arb trong universe chương trình; tận dụng tương quan thấp + mean-revert chậm |
| 10 | **S97 — Inverse-ATR sizing policy** | Không phải signal nhưng nâng chất mọi ý trên symbol vol 60–100% — bắt buộc từ ngày 1 |

### 3.2 Bẫy overfitting đặc thù khi backtest NATGAS

1. **Weather data snooping**: dùng HDD/CDD *final verified* thay vì *forecast real-time* là lookahead nghiêm trọng — thị trường giao dịch revision, không giao dịch actual. Phải dùng forecast archives (hoặc GFS reforecast) có timestamp; không có → các ý weather phải khai NOT_RUN.
2. **Survivorship các năm đông**: backtest 2014–2026 bị chi phối bởi 3–4 winter spike (2014, Uri 2021, 2022); mọi short-vol/mean-reversion trông ổn đến khi một năm đông giết. Bắt buộc report per-year PnL + max drawdown per-event, không chỉ aggregate.
3. **Storage-norm regime shift**: 5-year norm tự lăn (kỳ COVID 2020 rời cửa sổ, LNG wave 2025-26 vào) — "revert về norm" fit trên pre-2019 bị bias; threshold phải tính trên rolling window có giới hạn.
4. **Roll methodology**: chuỗi continuous không roll-adjust sẽ chế tạo/phá hủy PnL vì contango/backwardation hàng tháng; bắt buộc back-adjusted series (S86 là hygiene check).
5. **Weekend gap và stop fills**: daily-bar backtest với stop "fill tại giá stop" là ảo — NATGAS gap qua stop; phải model open-fill; các ý hold-weekend giảm EV theo gap statistics thật.
6. **Spread/slippage quanh EIA**: spread nới 3–10x trong 60 giây quanh 10:30 ET — mọi ý event phải trừ cost thực; đặc biệt S21/S30/S92.
7. **Contract-month contamination**: đỉnh/đáy tháng expiry (widow-maker) trộn vào chuỗi continuous tạo "pattern" giả; tách phân tích theo contract-month khi kiểm seasonal.
8. **Broker symbol khác NYMEX**: giờ expiry, quoting ×100/×1000, spread schedule khác nhau — kết quả không chuyển giữa broker nếu không normalize (ghi rõ trong khâu data).
9. **Consensus data scarcity**: lịch sử consensus poll EIA khó thu thập full — nếu thiếu, các ý surprise phải dùng proxy (5-yr norm deviation làm "consensus tĩnh"), và khai rõ khác biệt.

### 3.3 MUST-WATCH weekly macro checklist (cho lane NATGAS)

| Thứ | Việc | Nguồn |
|---|---|---|
| Hằng ngày 07:00 & 13:00 ET | GFS/ECMWF runs + HDD/CDD 6–10/8–14 revisions | NOAA/CPC + dịch vụ weather |
| Hằng ngày 06:00–08:00 ET | LNG feedgas nominations (record/drop) | NGI, Wood Mackenzie daily |
| Thứ Hai | Phân loại regime S94 (storage dev × HDD sign) | internal |
| Thứ Ba đầu tháng | EIA STEO — forecast revision | EIA |
| Thứ Tư | Chốt consensus poll cho EIA mai | S&P Global/Reuters poll |
| **Thứ Năm 10:30 ET** | **EIA Weekly Storage** — surprise, deviation vs 5-yr norm, pace vs required | EIA |
| Thứ Năm | NOAA/CPC 8–14 day flip check (S8/S58) | NOAA/CPC |
| Thứ Sáu 13:00 ET | Baker Hughes rig count | Baker Hughes |
| Thứ Sáu ~15:00 ET | CFTC COT managed money (S71/S77) | CFTC |
| Hằng tuần Jun–Nov | NHC tropical outlook cho Gulf (S4/S95) | NHC |
| Hằng tuần | TTF/JKM − HH spread & freight state (S61/S100) — kênh global | ICE/Platts proxy |
| Cuối tháng | Options/futures expiry & roll (S76/S78/S86) | broker calendar |

### 3.4 Data cần cho phase sau (nếu được cấp phép data)

- EIA weekly storage + 5-yr norm series; EIA monthly production; STEO history.
- HDD/CDD **forecast** archives có timestamp (điều kiện sống còn cho họ weather); NOAA CPC 6–10/8–14 history.
- Daily LNG feedgas nominations; LNG maintenance calendar.
- CME NG futures theo contract-month + settlement (roll-adjust, term structure); options IV nếu có.
- TTF (ICE) daily + JKM estimate cho S61/S83; freight LNG proxy.
- CFTC COT history; UNG shares outstanding.
- Broker-specific: NATGAS CFD spread schedule, expiry calendar, quoting convention (S86).

### 3.5 Câu hỏi mở chuyển cho lane khác

- Lane USDCAD/BRENT: xác nhận tín hiệu Hormuz trên dầu (Brent spike bao nhiêu, đã decay chưa) để đối chiếu kênh S61/S63/S100.
- Lane宏观: nếu Hormuz de-escalate trong Q4-2026, TTF risk premium giải phóng → JKM−HH co lại → feedgas vẫn cao nhờ capacity mới (kênh S99 era-demand) — HH có bị kéo xuống không? (Câu hỏi cho S83/S100 forward test.)

### 3.6 Phụ lục — định nghĩa & đơn vị dùng trong file

| Thuật ngữ | Định nghĩa |
|---|---|
| MMBtu | Million British Thermal Units — đơn vị chuẩn quote NG ($/MMBtu); 1 futures NG = 10.000 MMBtu |
| Bcf / Bcf/d | Billion cubic feet (tổng lượng) / mỗi ngày (tốc độ: production, feedgas, exports) |
| HDD / CDD | Heating / Cooling Degree Days — độ lệch nhiệt độ trung bình ngày so chuẩn 65°F, cộng dồn; proxy demand sưởi/lạnh |
| 5-yr norm (storage) | Trung bình trượt 5 năm working gas cùng tuần — mốc so lech (surplus/deficit) của EIA weekly report |
| Injection / withdrawal season | Apr–Oct nạp storage / Nov–Mar rút storage |
| Freeze-off | Giếng production đóng băng khi nhiệt độ vùng sản xuất cực thấp — supply shock, KHÔNG phải demand-shock |
| Widow-maker | Spread Mar/Apr — cold burst cuối mùa làm contract Mar thẳng đứng, decay vào Apr |
| Feedgas | Khí nomination vào các terminal LNG — proxy trực tiếp export demand |
| HH / TTF / JKM | Henry Hub (Mỹ nội địa) / Title Transfer Facility ( benchmark Âu, €/MWh) / Japan-Korea Marker (Á) |
| Đổi đơn vị TTF | €/MWh ÷ 3,412 = €/MMBtu; ×tỷ giá EURUSD = $/MMBtu (ví dụ €60/MWh ≈ $20/MMBtu — mức Sep-2026) |
| VRP | Variance Risk Premium — phần IV cao hơn HV thực; nguồn food cho các ý options-flavored |
| Roll / continuous | Đổi contract front-month hằng tháng / chuỗi giá nối các contract — phải back-adjusted khi backtest |
| OCO | One-Cancels-Other — cặp lệnh dừng hai biên, một bên khơi thì bên kia hủy |

*Mọi ý trên chỉ là hypothesis đến khi qua gate backtest + cost + trial accounting của chương trình — không số nào ở đây được coi là kết quả.*
