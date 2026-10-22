# AUDIT RUNTIME — PaperDesk paper trading (dữ liệu thật)

Nguồn: 6 file chụp từ Mac của user lúc 2026-10-21 ~13:47 giờ VN (snapshot cuối: incidents dừng ở 2026-10-21T06:49:41Z = 13:49 giờ VN). Mọi con số dưới đây đều đếm trực tiếp từ file bằng python, không ước lượng. Chỗ nào dữ liệu không đủ kết luận thì ghi rõ.

## VERDICT — 5 dòng

1. Hệ thống còn SỐNG: runner vẫn tick tới đúng giây chụp (incident cuối 06:49:41Z là DASHBOARD_REBUILT), nhưng sổ lệnh (ledger) không có dòng mới nào từ 2026-10-20T16:51:50Z (23:51 giờ VN) — gần 14 tiếng không có quyết định mới.
2. Tiền không mất, sổ khớp tuyệt đối: tự cộng lại 10 settlement trong ledger được equity 113.495c, đúng từng cent với dashboard; chuỗi hash của ledger tự kiểm tra lại = OK.
3. Lệnh kẹt THẬT chỉ có 2 (không phải 8): hai lệnh NBA đã đá xong mà chưa chốt được vì lỗi so tên đội (viết tắt DET/BOS vs tên đầy đủ). 6 dòng "kẹt" WSL trong file settle_last_why là BÓNG MA — các lệnh đó đã chốt xong từ 2026-10-20 rồi, file lý do không được dọn sau khi chốt.
4. AI gần như CHƯA làm gì: toàn bộ lịch sử chỉ có 2 ý kiến AI thật, cả hai đều do người bấm tay (manual), cả hai đều ABSTAIN (không ý kiến), 0 lần KEEP/VETO/SWITCH; cổng AI trong config đang OFF nên kể cả có ý kiến cũng không chặn được lệnh nào.
5. Lỗi lặp nhiều nhất không nằm ở lệnh mà ở vòng lặp nền: 1 ngày bão lỗi FileNotFoundError (446 lần, 2026-10-09) + 1.972 lần gọi API vào một giải bóng đá không tồn tại (404) chiếm phần lớn nhật ký; và "forecast" NBA là một con số hằng — cả 14 trận đều p=0,640065 giống hệt nhau.

---

## 1. Ledger census — sổ lệnh thật

Ledger có đúng **82 dòng**: GENESIS 1 / FORECAST 27 / MARKET_QUOTE 17 / DECISION 27 / SETTLEMENT 10. Khớp với handover round 17.

### Đếm theo loại × giải

| Loại | NBA | WNBA | SOCCER | WSL | Tổng |
|---|---|---|---|---|---|
| FORECAST | 14 | 4 | 2 | 7 | 27 |
| MARKET_QUOTE | 6 | 4 | 0 | 7 | 17 |
| DECISION | 14 | 4 | 1 | 8 | 27 |
| SETTLEMENT | 0 | 4 | 0 | 6 | 10 |

### Quyết định (DECISION) theo trạng thái × giải

| Trạng thái | NBA | WNBA | SOCCER | WSL | Tổng |
|---|---|---|---|---|---|
| BET_PAPER | 3 | 4 | 0 | 6 | **13** |
| NO_EDGE | 3 | 0 | 0 | 1 | 4 |
| NO_QUOTE | 8 | 0 | 1 | 0 | 9 |
| NOT_RUN_UNMAPPED_TEAM | 0 | 0 | 0 | 1 | 1 |

Ghi chú cấu trúc: 27 DECISION nhưng chỉ 26 trận khác nhau — trận WSL FD-2026-M37 có 2 DECISION (lần đầu NOT_RUN_UNMAPPED_TEAM vì tên đội lạ "Bitcoin", lần sau BET_PAPER thành công). Trận SOCCER England–Croatia có 2 FORECAST (hai model khác nhau, xem mục 7) nhưng chỉ 1 DECISION.

### Từng lệnh BET_PAPER (13 lệnh)

| # | Giải | Trận | Chân | Stake (c) | EV_net | Giá (odds) | Vào lệnh (UTC) | Kickoff (UTC) | Chốt? |
|---|---|---|---|---|---|---|---|---|---|
| 1 | WNBA | ATL vs NY (401918297) | HOME | 500 | +20,91% | 1,79 | 10-07 11:16 | 10-07 23:30 | ✅ WIN +395 |
| 2 | WNBA | GS vs LV (401918298) | HOME | 500 | +15,37% | 1,81 | 10-07 11:17 | 10-08 01:30 | ✅ WIN +405 |
| 3 | WNBA | NY vs ATL (401918299) | AWAY | 500 | +27,18% | 2,34 | 10-08 17:24 | 10-09 23:30 | ✅ WIN +670 |
| 4 | WNBA | LV vs GS (401918300) | AWAY | 500 | +24,78% | 2,49 | 10-08 19:32 | 10-10 01:30 | ✅ WIN +745 |
| 5 | WSL | Arsenal vs Birmingham City (M37) | DRAW | 1.022 | +56,98% | 12,01 | 10-14 02:24 | 10-17 11:45 | ✅ WIN +11.253 |
| 6 | WSL | Crystal Palace vs West Ham (M40) | HOME | 1.022 | +21,68% | 3,02 | 10-18 00:10 | 10-18 11:00 | ✅ LOSE −1.022 |
| 7 | WSL | Aston Villa vs Liverpool (M36) | HOME | 1.022 | +40,45% | 3,71 | 10-18 00:10 | 10-18 13:00 | ✅ WIN +2.769 |
| 8 | WSL | London City Lionesses vs Everton (M39) | AWAY | 1.022 | **+196,68%** | 10,04 | 10-18 00:10 | 10-18 13:00 | ✅ LOSE −1.022 |
| 9 | WSL | Charlton vs Man United (M42) | HOME | 1.022 | +44,31% | 8,88 | 10-18 00:10 | 10-18 13:00 | ✅ LOSE −1.022 |
| 10 | WSL | Man City vs Brighton (M38) | HOME | 1.022 | +6,54% | 1,32 | 10-18 00:10 | 10-18 13:30 | ✅ WIN +324 |
| 11 | NBA | Detroit Pistons vs Boston Celtics (401909088) | HOME | 1.135 | +28,57% | 2,04 | 10-20 12:02 | 10-20 19:00 | ❌ **KẸT** |
| 12 | NBA | San Antonio Spurs vs OKC Thunder (401909090) | HOME | 1.135 | +17,69% | 1,87 | 10-20 12:02 | 10-21 01:30 | ❌ **KẸT** |
| 13 | NBA | Brooklyn Nets vs Charlotte Hornets (401909836) | HOME | 1.135 | +6,17% | 1,69 | 10-20 16:51 | 10-21 23:30 | ⏳ Chưa đá |

### Lệnh chưa chốt — kẹt bao lâu (tính tới lúc chụp 2026-10-21T06:49:41Z)

| Lệnh | Trận đấu ngày | Tình trạng lúc chụp |
|---|---|---|
| NBA 401909088 DET vs BOS | Đá 2026-10-20 19:00Z, xong khoảng 21:30Z | Đã xong ~9,3 giờ mà chưa chốt. Lần thử chốt duy nhất được ghi: 2026-10-20T22:00:28Z → bị chặn vì identity mismatch. Sau đó ~8,8 giờ không có lần thử nào nữa trong incidents. |
| NBA 401909090 SA vs OKC | Đá 2026-10-21 01:30Z, xong khoảng 04:00Z | Đã xong ~2,3–2,8 giờ mà chưa chốt. Lần thử duy nhất: 2026-10-21T04:30:15Z → identity mismatch. |
| NBA 401909836 BKN vs CHA | Đá 2026-10-21 23:30Z (chưa tới) | Mở hợp lệ, không phải kẹt. |

**Giải thích "open 13" vs "open 3":** 13 là TỔNG SỐ lệnh BET_PAPER từ trước tới nay. Trong đó 10 lệnh đã có SETTLEMENT (4 WNBA + 6 WSL). Còn mở thật = 13 − 10 = **3 lệnh NBA**, exposure = 3 × 1.135c = **3.405c** — đúng với dashboard (open_count=3, open_exposure_cents=3405). Handover ghi "open 13 bets (3 NBA + 4 WNBA + 6 WSL), open exposure 3405c" là tự mâu thuẫn: nếu 13 lệnh còn mở thật thì exposure phải là 3×1.135 + 4×500 + 6×1.022 = 11.537c. Dashboard đúng, câu chữ handover sai (dán nhãn "tổng lệnh đã vào" thành "đang mở").

---

## 2. Settlement — chốt sổ

10 settlement: **WIN 7 / LOSE 3 / REFUND 0**. Khớp dashboard (outcomes WIN 7, LOSE 3, REFUND 0; hit rate 0,7).

| Giải | Số lệnh chốt | W/L | PnL đếm từ ledger | PnL dashboard | Khớp? |
|---|---|---|---|---|---|
| WNBA | 4 | 4W / 0L | +2.215c | +2.215c | ✅ |
| WSL | 6 | 3W / 3L | +11.280c | +11.280c | ✅ |
| NBA | 0 | — | 0 | 0 | ✅ |
| SOCCER | 0 | — | 0 | 0 | ✅ |
| **Tổng** | **10** | **7W / 3L** | **+13.495c** | **+13.495c** | ✅ |

Equity: 100.000c (GENESIS) + 13.495c = **113.495c**, khớp dashboard từng cent. Lưu ý: riêng 1 lệnh WSL M37 (DRAW ở giá 12,01) đóng góp +11.253c = 83% tổng lãi; bỏ lệnh đó ra, hệ thống chỉ lãi +2.242c trên 9 lệnh.

### Thời gian từ kickoff tới lúc chốt sổ (số đo thật; giờ kết thúc trận là ước lượng +2h bóng đá / +2,5h bóng rổ)

| Nhóm | Lag từ kickoff (từng lệnh) | Trung bình từ kickoff | Ước lượng sau khi trận kết thúc |
|---|---|---|---|
| WNBA (4) | 9,85h / 7,85h / 3,01h / 3,02h | 5,93h | ~0,5–7,3h |
| WSL (6) | 61,94h / 38,69h / 36,69h / 36,69h / 36,69h / 36,38h | 41,18h | ~34–60h |
| Toàn bộ (10) | — | **27,08h** | — |

WSL chốt rất chậm và chốt theo ĐỢT: 5/6 lệnh cùng chốt ở 2026-10-20T01:41:21–22Z, lệnh M38 chốt sau đó 11 phút (01:52:47Z) — tức là phải đợi người/vòng chạy riêng can thiệp, không phải chốt tự động ngay sau trận. Trước đó các lệnh WSL bị giữ mở qua 2 vòng lý do khác nhau (xem mục 3 và incidents: "results source not pinned" ngày 10-17/18, rồi "not a finished 90-minute resolution" lúc 01:38 ngày 10-20, chốt được lúc 01:41 cùng ngày qua đường UMA).

---

## 3. settle_last_why.json — phân loại lý do kẹt

File có **8 mục**, nhưng chỉ **2 mục là kẹt thật ở hiện tại**:

| Lý do | Số mục | Lệnh | Còn kẹt thật? |
|---|---|---|---|
| Identity mismatch — nguồn kết quả ghi tên viết tắt (DET/BOS, SA/OKC), ledger ghi tên đầy đủ (Detroit Pistons/Boston Celtics, San Antonio Spurs/Oklahoma City Thunder), hệ thống không nối được hai cách ghi nên giữ OPEN | 2 | NBA 401909088, 401909090 | ✅ CÒN KẸT |
| "Not a finished 90-minute resolution" — chân DRAW có `date_ok=False` | 5 | WSL M36, M37, M39, M40, M42 | ❌ ĐÃ CHỐT 2026-10-20T01:41Z |
| "Not a finished 90-minute resolution" — cả 3 chân `id_ok=False` (bản ghi cuối; vòng trước đó là DRAW date_ok=False) | 1 | WSL M38 | ❌ ĐÃ CHỐT 2026-10-20T01:52:47Z |

Kết luận mục 3:

- **100% lệnh kẹt thật (2/2) cùng một nguyên nhân: thiếu bảng nối tên viết tắt ↔ tên đầy đủ cho nguồn kết quả NBA.** Đây là lỗi dữ liệu đơn giản, không phải lỗi logic chốt sổ.
- File settle_last_why **không được dọn sau khi chốt thành công**: 6/8 mục (75%) là lý do cũ của lệnh đã chốt xong từ hôm trước. Ai chỉ đọc file này sẽ tưởng 8 lệnh đang kẹt — con số thật là 2. File này hiện là nguồn gây hiểu lầm số 1 về trạng thái hệ thống.
- Chi tiết WSL: ở vòng kiểm tra 90-phút, chân DRAW luôn là chân hỏng (5/6 trận date_ok=False ở đúng chân DRAW; các chân HOME/AWAY đều date_ok=True). Các trận này cuối cùng chốt được bằng đường Polymarket UMA (source_ref trong SETTLEMENT ghi `polymarket_uma … uma=resolved`), tức là có 2 đường kiểm tra cho ra 2 kết quả khác nhau trên cùng một trận, và file "why" chỉ giữ kết quả của đường fail.

---

## 4. Incidents census — nhật ký sự cố

Tổng **3.657 dòng**, từ 2026-10-08T09:21:03Z tới 2026-10-21T06:49:41Z, 0 dòng hỏng. Đếm theo loại:

| # | Loại | Số lần | % file | Lần gần nhất | Ghi chú |
|---|---|---|---|---|---|
| 1 | DASHBOARD_REBUILT | 2.245 | 61,4% | 2026-10-21T06:49:41Z | Không phải sự cố — là nhịp rebuild dashboard ~5 phút/lần, chiếm gần 2/3 file, làm loãng mọi tín hiệu lỗi thật. |
| 2 | TICK_ERROR | 448 | 12,3% | 2026-10-14T01:15:55Z | Xem bão lỗi bên dưới. |
| 3 | CADENCE_FORECAST_BLOCKED | 292 | 8,0% | 2026-10-20T07:58:46Z | NBA 190 lần + WNBA 102 lần: entry của engine dự báo KHÔNG TỒN TẠI (BLOCKED_NBA_ENTRY / BLOCKED_WNBA_ENTRY) — kéo dài nhiều ngày (riêng WNBA ngày 2026-10-11: 97 lần; NBA ngày 10-15: 64 lần, 10-16: 94 lần). |
| 4 | CADENCE_QUOTE_OK | 171 | 4,7% | — | 167/171 là WSL. |
| 5 | CADENCE_DECIDE_OK | 171 | 4,7% | — | 167/171 là WSL. |
| 6 | CADENCE_FORECAST_OK | 170 | 4,6% | — | 167/170 là WSL; NBA chỉ OK 1 lần, WNBA 2 lần trong 13 ngày. |
| 7 | SERVICE_START | 49 | 1,3% | 2026-10-20T11:58:08Z | START 49 vs STOP 47 (chênh 2). Riêng ngày 2026-10-19 có **26 lần start** — service bị khởi động lại liên tục. |
| 8 | SERVICE_STOP | 47 | 1,3% | 2026-10-20T11:33:30Z | |
| 9 | DECISIONS_RESUMED_BY_UI | 30 | 0,8% | 2026-10-20T12:47:33Z | RESUMED 30 vs PAUSED 4 — cờ pause bị gỡ liên tục (riêng 2026-10-19: ~19 lần resume), cho thấy flag pause_decisions không ổn định/bị ghi đè. |
| 10 | SETTLE_KEEP_OPEN | 15 | 0,4% | 2026-10-21T04:30:15Z | WSL 13 lần (2 vòng lý do khác nhau) + NBA 2 lần (identity mismatch). |

Ngoài top 10: SETTLE_DONE 10, SETTLE_SKIP 4, DECISIONS_PAUSED_BY_UI 4, DASHBOARD_BLOCKED 1.

### Bão lỗi lặp mỗi tick (storm)

- **446/448 TICK_ERROR (99,6%) là cùng một lỗi**: `FileNotFoundError: …/research/papertrade_exec/pins.json` không tồn tại, lặp liên tục trong một ngày duy nhất **2026-10-09, từ 04:16:48Z tới 13:28:06Z (9,2 giờ)**. Cơn bão này = **12,2% toàn bộ file incidents**. 2 TICK_ERROR còn lại là AttributeError `module 'spt_core' has no attribute 'ledger'` (10-13 và 10-14).
- Hai loại nhiễu lớn nhất (DASHBOARD_REBUILT + TICK_ERROR) cộng lại = 2.693/3.657 = **73,6% file**.

### Các loại sự cố được hỏi đích danh

| Hỏi | Có/không trong incidents | Bằng chứng |
|---|---|---|
| Quota cạn / bị chặn quota | **Không có** sự cố quota nào. Chỉ 3 dòng CADENCE_QUOTE_OK nhắc `quota_remaining` (490/489/488). Không có HALT_KEY, không có 401/403 từ Odds API trong incidents. |
| Pin drift | **Có, 5 lần**: SETTLE_SKIP ×4 + DASHBOARD_BLOCKED ×1, đều BLOCKED_PIN_DRIFT (paper_core/__init__.py missing/sha mismatch ngày 10-09, 10-10 ×2; soccer_crosswalk_extension_csv sha mismatch — lần gần nhất **2026-10-21T00:36:48Z**, tức ngay trong ngày chụp). Mỗi lần pin drift là một vòng settle bị BỎ QUA hoàn toàn. |
| Stale corpus | **Không thấy** dòng nào nhắc STALE_CORPUS/stale trong incidents (handover nói tính năng này mới thêm ở round 17 — dữ liệu chụp không chứa bằng chứng nó đã chạy; không đủ dữ liệu để kết luận nó hoạt động hay không). |
| Missed window (lỡ cửa sổ vào lệnh) | Không có loại sự cố riêng. Bằng chứng gián tiếp: 8 lệnh NBA NO_QUOTE trong ledger (mục 7) và việc thử chốt NBA chỉ xuất hiện 1 lần/lệnh trong ~9 giờ (mục 1) — nhịp thử lại thưa, không phải mỗi tick. |

Một quan sát vận hành nữa: SETTLE_KEEP_OPEN cho NBA 401909088 chỉ xuất hiện **đúng 1 lần** (2026-10-20T22:00:28Z) dù lệnh kẹt ~9 giờ tới lúc chụp; heartbeat tại lúc chụp còn ghi `last_settle_tick_utc = null, settle attempted = 0`. Việc thử chốt dường như chạy theo đợt/sự kiện, không chạy đều mỗi tick.

---

## 5. Quota journal — Odds API

Tổng **4.423 lần gọi** từ 2026-10-07T11:10:30Z tới 2026-10-21T06:49:09Z.

| Chỉ số | Giá trị |
|---|---|
| Tổng số lần gọi | 4.423 |
| Lần gọi tốn credit (endpoint /odds) | **9 lần duy nhất** (WNBA 5, NBA 2, SOCCER UNL 2) |
| Tổng credit theo journal (cost_credits) | 9 |
| Credit theo tháng 2026-10 | 9 / cap 120 — rất xa cap tháng |
| Lần gọi tốn credit gần nhất | 2026-10-20T16:51:50Z (NBA odds) |
| Bộ đếm của nhà cung cấp (used/remaining ở dòng cuối) | used=13, remaining=487 (gói 500) |

### Theo ngày (chỉ ngày có tốn credit)

| Ngày | Tổng lần gọi | Lần tốn credit | Credit (journal) | Nhận xét |
|---|---|---|---|---|
| 2026-10-07 | 13 | 4 | 4 | **Đúng bằng cap 4/ngày** theo cách đếm của journal |
| 2026-10-08 | 173 | 3 | 3 | Dưới cap |
| 2026-10-20 | 396 | 2 | 2 | Dưới cap |
| Các ngày còn lại (10-09 → 10-21) | 4.027 | 0 | 0 | Toàn bộ là gọi /events miễn phí |

**Không có ngày nào vượt cap theo cách đếm của journal** (ngày cao nhất = 4 = đúng cap). Nhưng có một lệch đếm quan trọng:

- Bộ đếm `used` của nhà cung cấp tăng từ 3 → 13 trong cửa sổ journal (tức 10 credit), trong khi journal tự ghi tổng cost = 9. Nguyên nhân thấy được trong dữ liệu: mỗi lần gọi WNBA /odds làm `used` tăng **+2** (3→5→7) nhưng journal ghi cost_credits = 1. Nếu cap 4/ngày được hiểu theo credit của nhà cung cấp, riêng ngày 2026-10-07 đã tiêu **8 credit** (used cuối ngày = 8) — **vượt cap 4/ngày theo cách đếm của nhà cung cấp**. Dữ liệu không cho biết hệ thống chủ ý đếm theo cách nào; đây là điểm phải làm rõ, vì cơ chế chặn cap đang đếm khác với cơ chế trừ tiền thật.

### Lãng phí gọi API (không tốn credit nhưng bất thường)

- **1.972/4.423 lần gọi (44,6%) trả về HTTP 404**, tất cả vào cùng một endpoint `/v4/sports/soccer_fifa_world_cup_group/events` — một sport key mà chính config của hệ thống đã ghi chú là không tồn tại trên nguồn này ("the ONLY active men's-international soccer key … is soccer_uefa_nations_league").
- Note đi kèm mỗi dòng 404 ghi "(5xx retry policy: max 1/day)" — nhưng thực tế endpoint này bị gọi **232–282 lần/ngày** vào các ngày cao điểm (10-16: 282 lần) và vẫn đang bị gọi ở dòng cuối cùng của journal (2026-10-21T06:49:09Z, ngay lúc chụp). Chính sách "tối đa 1 lần/ngày" ghi trong note không khớp hành vi thật (sai lệch ~200 lần/ngày).
- Endpoint UNL events hợp lệ được gọi 2.441 lần; tổng 4.413/4.423 lần gọi (99,8%) là poll /events miễn phí — hệ thống gọi API rất nhiều nhưng gần như không bao giờ lấy odds mới (9 lần trong 15 ngày).

---

## 6. AI review index — AI đã thật sự làm gì chưa

File có **7 dòng nhưng chỉ 2 ý kiến khác nhau** (mỗi ý kiến bị ghi lặp 3–4 dòng trong index, kể cả dòng COMPLETED của ý kiến 401909090 bị ghi trùng 2 lần).

| Ý kiến | Trận | Lúc ghi (UTC) | Ai khởi tạo | Provider | Verdict cuối |
|---|---|---|---|---|---|
| 440a4f26… | FD-2026-M44 (WSL, trận không có dòng nào trong ledger; deadline 2026-10-24) | 2026-10-20T10:48:10Z | `manual-live-verify` | mock-local → openrouter | ABSTAIN |
| 5ed1b766… | NBA 401909090 (SA vs OKC) | 2026-10-20T12:49:04Z | `manual` | mock-local → openrouter | ABSTAIN |

Phân bố verdict trên toàn bộ lịch sử: **KEEP 0 / VETO 0 / SWITCH 0 / ABSTAIN 2 / failed 0**. Trạng thái RUNNING (verdict "nil") xuất hiện trong các dòng trung gian của cả 2 ý kiến rồi đều kết thúc COMPLETED.

Kết luận mục 6:

- **AI chưa từng tự động đánh giá một lệnh nào.** Cả 2 ý kiến đều do người khởi tạo tay (`scheduled_by` = manual / manual-live-verify), không có ý kiến nào do runner/cadence tự sinh. Ý kiến gần nhất: 2026-10-20T12:49:04Z, cách lúc chụp ~24 giờ.
- **Có 1 ý kiến gắn với lệnh BET_PAPER thật** (401909090), nhưng nó đến **sau** khi lệnh đã vào 47 phút (DECISION lúc 12:02:12Z, ý kiến lúc 12:49:04Z) — đây là xem lại sau (post-hoc), không phải cổng chặn trước lệnh.
- Ý kiến đó verdict ABSTAIN. Theo luật cổng AI mô tả trong handover (ABSTAIN ⇒ NOT_PLACED), nếu cổng này thật sự bật thì lệnh 401909090 đã không được vào. Nhưng config ghi `ai_authority_active: false` và `pm_cutover_active: false` — cổng đang OFF, nên ý kiến không có bất kỳ tác dụng nào, và lệnh hiện đang nằm trong nhóm kẹt chưa chốt (mục 1).
- **Dữ liệu không ghi tên model**: index chỉ ghi provider (mock-local lúc khởi tạo, openrouter lúc hoàn thành), không có trường model. Không thể kết luận model nào đã chạy từ dữ liệu này.
- Ý kiến còn lại (FD-2026-M44) là bài kiểm tra tay trên một trận chưa hề xuất hiện trong ledger — không gắn với bất kỳ quyết định thật nào.

Nói ngắn: về mặt dữ liệu, lớp AI hiện là một tính năng đã đấu nối và được test tay 2 lần, **chưa vận hành thật một lần nào**.

---

## 7. FORECAST/QUOTE không thành lệnh — rơi ở đâu

27 DECISION cho 26 trận: 13 BET_PAPER (48,1%), 9 NO_QUOTE (33,3%), 4 NO_EDGE (14,8%), 1 NOT_RUN (3,7%, sau thử lại thành công).

### NO_QUOTE — 9 trường hợp, 2 nguyên nhân

| Nguyên nhân | Số | Chi tiết |
|---|---|---|
| NBA: "no provider event matched 1:1 (commence_time + team set); fail-closed" | 8 | Toàn bộ xảy ra trong **một đợt duy nhất** 2026-10-20T16:51:49Z, cho 8/11 trận NBA ngày 10-21/10-22 (Orlando–Atlanta, Miami–Minnesota, Toronto–Chicago, Memphis–Utah, New Orleans–Indiana, Houston–Dallas, Portland–Phoenix, LA Clippers–Sacramento). Không có MARKET_QUOTE nào được ghi cho các trận này — hệ thống không nối được trận của mình với sự kiện của nhà cung cấp nên không có giá, không tính được EV. |
| SOCCER: "pinnacle absent from payload; fail-closed" | 1 | England–Croatia (kickoff 2026-11-12). Đã tốn 2 credit odds (10-07 và 10-08) mà payload vẫn không có Pinnacle. |

Dashboard ghi `not_run_by_cause.missing_or_invalid_odds = 9` — khớp đúng 9 NO_QUOTE này.

### NO_EDGE — phân bố EV quanh ngưỡng 5%

EV tốt nhất (best EV_net) của 4 trường hợp NO_EDGE, đọc từ reason trong ledger:

| Trận | Best EV_net | Cách ngưỡng 5% |
|---|---|---|
| WSL Chelsea vs Tottenham (M41) | **+1,84%** | Âm dưới ngưỡng 3,16 điểm % — trường hợp "suýt" duy nhất có EV dương |
| NBA Lakers vs Golden State (401909092) | −0,50% | EV âm |
| NBA Knicks vs Philadelphia (401909089) | −1,51% | EV âm |
| NBA Washington vs Milwaukee (401909835) | −2,79% | EV âm |

- **Không có lệnh nào bị loại oan sát ngưỡng**: ngoài M41 (+1,84%), mọi NO_EDGE đều có EV âm — kể cả giá có nhích một chút cũng chưa tới 5%.
- Phía trên ngưỡng, 2 lệnh BET sát nhất là NBA 401909836 (+6,17%) và WSL M38 (+6,54%) — chỉ hơn bar 1,17 và 1,54 điểm %. Đây là các lệnh "mỏng" nhất trong sổ.
- Toàn bộ EV của 13 lệnh BET: 6,17% / 6,54% / 15,37% / 17,69% / 20,91% / 21,68% / 24,78% / 27,18% / 28,57% / 40,45% / 44,31% / 56,98% / **196,68%**. Lệnh cuối (WSL M39, AWAY giá 10,04 với xác suất model 29,76%) là điểm ngoại lai cực đoan — EV gần 200% trong một trận WSL thường là dấu hiệu giá quote sai/thị trường mỏng hơn là cơ hội thật; lệnh này cuối cùng LOSE −1.022c.

### Hai bất thường dữ liệu phát hiện thêm ở mục này

1. **Forecast NBA là hằng số.** Cả 14/14 FORECAST NBA có xác suất giống hệt nhau tới 6 chữ số thập phân: HOME 0,640065 / AWAY 0,359935 — bất kể đội nào đấu với đội nào, sân nhà sân khách ra sao. Nghĩa là với dữ liệu hiện tại, "dự báo NBA" không mang thông tin riêng theo trận; mọi EV NBA chỉ là lấy con số cố định 64% so với giá Pinnacle. (WNBA và WSL thì mỗi trận một xác suất khác nhau, bình thường.) Handover không hề nhắc tới việc này.
2. **Quote WSL bị trùng giá giữa các trận khác nhau.** Odds chân DRAW của M39 và M42 giống hệt nhau tới 15 chữ số: 5,647962497524461. Odds DRAW của M38 và M41 cũng giống hệt: 5,9980806141780825. Hai trận khác nhau có cùng một giá tới 15 chữ số thập phân là điều gần như không thể xảy ra với quote độc lập — nghi ngờ cùng một snapshot Polymarket bị dùng lại cho nhiều trận (quote contamination). Chỉ với dữ liệu runtime thì chưa chứng minh được join sai trận, nhưng EV của M39 (+196,68%) và M42 (+44,31% cho chân HOME giá 8,88 trong khi model cho AWAY 65,47%) đều sinh ra từ các quote này.
3. **SOCCER được forecast 2 lần, quyết định 1 lần.** Cùng trận England–Croatia có FORECAST của model `soccer_b1_replay` (2026-10-07, p HOME 0,6288) và của `soccer_b1r_v1` (2026-10-10, p HOME 0,5878). DECISION NO_QUOTE duy nhất ghi ngày 10-08 (theo forecast đầu). Forecast thứ hai không bao giờ có DECISION đi kèm.

---

## 8. Bất nhất số liệu — handover vs dashboard vs ledger

| # | Điểm không khớp | Handover nói | Dashboard nói | Ledger/dữ liệu thật nói | Bên nào đúng |
|---|---|---|---|---|---|
| 1 | Số lệnh đang mở | "open 13 bets (3 NBA + 4 WNBA + 6 WSL)" | open_count = 3 | 13 BET_PAPER tổng, 10 đã có SETTLEMENT → mở thật = 3 (toàn NBA) | **Dashboard + ledger**. Handover gọi tổng lệnh tích lũy là "open"; đồng thời ghi exposure 3.405c — con số chỉ đúng cho 3 lệnh, tự mâu thuẫn ngay trong cùng câu. |
| 2 | Exposure nếu 13 lệnh mở thật | 3.405c | 3.405c | 13 lệnh mở thật phải là 11.537c (3×1.135 + 4×500 + 6×1.022) | Dashboard (vì mở thật = 3). |
| 3 | Số lệnh kẹt chưa chốt | (không nêu) | open_count = 3 | settle_last_why liệt kê 8 trận "chưa chốt được" | **Ledger**: kẹt thật 2 (NBA), 1 lệnh chưa đá (hợp lệ), 6 mục trong settle_last_why là lý do cũ của lệnh WSL đã chốt — file không được dọn sau khi chốt. |
| 4 | WSL đã chốt hết chưa | "6/6 settled +11280c" | settled_count = 10, WSL PnL +11.280c | 6 SETTLEMENT WSL, PnL cộng lại +11.280c | Cả ba khớp nhau ✅ — nhưng mâu thuẫn với settle_last_why (mục 3): cùng 6 trận vừa "đã chốt" vừa "not a finished resolution". |
| 5 | PnL / equity / chain | equity 113.495c, chain_ok | equity 113.495c, chain_ok=true, PnL WNBA +2.215 / WSL +11.280 / NBA 0 / SOCCER 0 | Tự cộng lại từ ledger: y hệt; tự kiểm tra chuỗi hash: OK | Cả ba khớp ✅ (điểm sáng duy nhất của bộ số liệu). |
| 6 | Cấu trúc ledger | "82 rows: GENESIS 1 / FORECAST 27 / QUOTE 17 / DECISION 27 / SETTLEMENT 10" | status_counts cộng = 27 DECISION | Đếm thật: đúng từng con số | Khớp ✅. |
| 7 | NBA forecast "live" | "Production forecast live: 11 B1* rows (ledger FORECAST)" | — | Ledger có **14** FORECAST NBA, và cả 14 có xác suất y hệt nhau (0,640065/0,359935) | Ledger. Handover vừa sai số đếm (11 vs 14) vừa không hề nhắc việc forecast không phân biệt được trận nào với trận nào. |
| 8 | Lớp AI gate | Mô tả như một cổng đang hoạt động trong chuỗi quyết định (KEEP/VETO/SWITCH/ABSTAIN) | — | Index: 2 ý kiến, đều manual, đều ABSTAIN, 1 ý kiến đến sau lệnh 47 phút; config `ai_authority_active=false` | Dữ liệu thật: cổng **chưa từng chặn/giữ lệnh nào**. |
| 9 | Đếm credit quota | Config: cap 4 credits/ngày + 120/tháng, "journal every call" | — | Journal ghi cost 1/lần gọi (ngày cao nhất = 4 = cap), nhưng bộ đếm `used` của nhà cung cấp tăng +2 cho mỗi lần gọi WNBA odds; ngày 2026-10-07 tiêu 8 credit theo nhà cung cấp | Không khớp nhau — cơ chế đếm để chặn cap ≠ cơ chế trừ credit thật. Ngày 10-07 vượt cap nếu tính theo nhà cung cấp. |
| 10 | Chính sách retry 404 | Note trong journal: "5xx retry policy: max 1/day" | — | Endpoint WC-group bị gọi 1.972 lần, 232–282 lần/ngày, vẫn gọi ở giây chụp cuối cùng | Hành vi thật trái với note ~200 lần/ngày. |
| 11 | Nhịp chốt sổ (settle) | Handover: WSL settlement law "unchanged", hệ thống tự vận hành | Heartbeat lúc chụp: `last_settle_tick_utc = null`, settle attempted = 0 | Incidents: SETTLE_KEEP_OPEN cho 1 lệnh kẹt chỉ xuất hiện 1 lần trong ~9 giờ; WSL phải đợi 36–62h và chốt theo đợt | Vận hành thật: settle chạy thưa/theo đợt, không phải mỗi tick; tại tick chụp, settle không chạy. |
| 12 | Trạng thái pause | — | dashboard `paused: false` | Incidents: PAUSED 4 lần nhưng RESUMED 30 lần; ngày 10-19 cờ pause bị gỡ ~19 lần | Không đủ dữ liệu để kết luận ai gỡ cờ, nhưng tỉ lệ 30/4 cho thấy cơ chế flag pause không ổn định. |
| 13 | Tính duy nhất của index AI | — | — | ai_review_index có 7 dòng cho 2 ý kiến (1 dòng COMPLETED bị ghi trùng) | Index tự nó không phải nguồn đếm đáng tin nếu không khử trùng lặp theo opinion_id. |

---

## Phụ lục — những chỗ dữ liệu không đủ để kết luận

- **Tên model AI**: index chỉ ghi provider, không ghi model — không kết luận được model nào đã chạy 2 ý kiến ABSTAIN.
- **STALE_CORPUS**: handover nói đã thêm ở round 17, nhưng incidents chụp tới 2026-10-21T06:49:41Z không chứa dòng nào — không xác nhận được nó đã chạy thật hay chưa.
- **Giờ kết thúc trận**: ledger/incidents không ghi giờ final của trận; mọi con số "kẹt sau khi trận kết thúc" ở mục 1–2 dùng ước lượng chuẩn (bóng rổ +2,5h, bóng đá +2h từ kickoff) và đã ghi rõ là ước lượng. Lag từ kickoff là số đo thật.
- **Quote WSL trùng giá**: dữ liệu runtime cho thấy giá trùng 15 chữ số giữa các trận — đủ để gắn cờ nghi ngờ, chưa đủ để kết luận join sai trận (cần đối chiếu snapshot Polymarket gốc, không có trong bộ file này).
- **Runner tại lúc chụp**: incidents dừng đúng 06:49:41Z khớp heartbeat (pid 10000, tick 1938) — tin được là runner sống tại thời điểm chụp; dữ liệu không nói gì về sau thời điểm đó. Ledger không có dòng mới từ 2026-10-20T16:51:50Z — trong cửa sổ chụp, khoảng lặng này trùng với việc không có trận NBA/WNBA nào qua được cổng forecast/quote (CADENCE_FORECAST_BLOCKED gần nhất 2026-10-20T07:58:46Z cho NBA và 8 trận NO_QUOTE lúc 16:51), nhưng nguyên nhân đầy đủ của khoảng lặng nằm ngoài bộ file này.

