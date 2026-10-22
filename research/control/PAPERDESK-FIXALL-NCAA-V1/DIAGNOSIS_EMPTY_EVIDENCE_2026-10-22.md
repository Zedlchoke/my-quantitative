# CHẨN ĐOÁN — GÓI BẰNG CHỨNG RỖNG Ở LANE THẬT (FD-2026-M48 + 2 NBA)
(PAPERDESK-FIXALL-NCAA-V1 / FREE-RESEARCH; 2026-10-22. Lượt CHẨN ĐOÁN:
không sửa code, không đổi hành vi production.)

## 1. FD-2026-M48 (WSL Brighton–West Ham, hash ead4e5fb…): collector đã
thử gì, từng cái trả về gì

Nhật ký: `~/.my-quantitative-data/sports-papertrade-exec-v1/ai_review/
evidence/evidence_FD-2026-M48_20261022T070{234,404,606}Z.json` (3 lượt,
cùng kết quả):

| Nguồn đã thử | Kết quả trên nhật ký | Kiểm sống 2026-10-22 |
|---|---|---|
| `soccer/news?limit=50` (window 48h, lọc tên 2 đội) | `news_error: HTTPError 404` | GET generic soccer/news → exception (endpoint KHÔNG tồn tại khi không có slug giải) |
| `soccer/scoreboard?dates=20261024` và `?dates=20261022` | `board fetch failed (cached)` ×2 | GET generic soccer/scoreboard → exception |
| core injuries (2 đội) | `skipped, 0 sources — no team_id provided by caller` | không tới được: team_ids=None, lookup trên board đã hỏng |

- Trả lời câu hỏi "rỗng thật / lỗi / bị allow-list chặn": **LỖI cấu trúc
  — không nguồn nào bị allow-list chặn; toàn bộ endpoint của
  allow-list cho WSL đều chết** vì `SPORT_PATH["WSL"] = "soccer"`
  (slug generic) mà ESPN site API bắt buộc phải có slug giải.
- Kết quả: `sources: []` → V2 buộc VETO `INSUFFICIENT_EVIDENCE`
  (opinion trên đĩa, cited 0).

## 2. Hai candidate NBA đêm 21/10: gói KHÔNG rỗng — nhưng thiếu hạng mục

**401909093 (76ers @ Cavaliers)** — 4 nguồn: preview TRẬN NÀY, recap của
MỘT trận 76ers khác, tin Silver nhắc tên 76ers, dòng trạng thái board
"Thu, October 22nd at 7:00 PM EDT". Verdict VETO
`INSUFFICIENT_EVIDENCE + NO_AWAY_TEAM_CONTEXT + NO_INJURY_LINEUP_CONFIRMATION`
(cited 3). **Thiếu**: tin đội KHÁCH (Cavaliers) = 0; injury/lineup = 0.

**401909094 (OKC @ Nuggets)** — 2 nguồn (preview trận này + recap trận
OKC khác); không tin Denver; verdict VETO
`INSUFFICIENT_EVIDENCE + MISSING_DENVER_NEWS + MISSING_INJURY_LINEUP_STATUS`.
**Thiếu thêm**: toàn bộ tầng roster/injuries KHÔNG hề được chạy —
queries không có dòng roster/injuries vì `team_ids` không tra được từ
board (board-day tra 20261023+20261021, không tra 20261022 — xem F-4).

Hai mã VETO của model gọi tên ĐÚNG hạng mục thiếu — model không vu
oan; gói thật sự thiếu.

## 3. Nguyên nhân gốc theo tầng — mỗi tầng một bằng chứng

**L1 — Ánh xạ fixture (XÁC NHẬN, nguyên nhân chính của WSL):**
`ai_research.SPORT_PATH["WSL"] = "soccer"` — slug generic chết ở cả
news lẫn scoreboard (bảng trên). Đồng thời **không-gian id lệch**:
`FD-2026-M48` là mã crosswalk của lane WSL (`wsl_results.py:170`
"FD-name -> title match THROUGH the pinned crosswalk") — lookup
ESPN-theo-event-id sẽ không bao giờ trúng kể cả khi board sống. NBA
dùng đúng id ESPN nên 093 tra được team_ids (20/5) — 094 thì không.

**L2 — Danh sách nguồn quá hẹp cho bóng đá/giải nữ (XÁC NHẬN, phụ):**
ESPN tin tức generic gần như không phủ WSL nữ; slug ĐÚNG của ESPN cho
giải là **`eng.w.1` (dấu chấm)** — kiểm sống:
`soccer/eng.w.1/scoreboard?dates=20261024` → 200, 2 events;
`eng_w.1` (gạch dưới) → 400. Không có gì bị "danh sách chặn" — allow-
list ESPN-only đơn giản là không phủ giải này.

**L3 — Thời điểm chụp (PHỤ, chỉ NBA):** chụp tại anchor T-6h10m;
injury report thường ra sát giờ. Không định lượng được khi extractor
injury đang chết (L4a) — ghi nhận, chưa kết luận.

**L4 — Lỗi code (XÁC NHẬN bằng kiểm sống, đúng luật "trung thực"):**
- **(a) Injuries chỉ toàn `$ref`**: core API trả
  `items: [{...}, ...]` mà từng item chỉ có khóa `$ref`
  (journal: `items=4 sources=0`); `_injury_sources` bỏ qua item
  thuần-$ref theo thiết kế → **0 citation mọi lần**. Follow `$ref` đầu
  tiên (sống) trả dữ liệu thật: `status: Out, details: Quadriceps` —
  chỉ cần 1 hop GET là có citation.
- **(b) Roster endpoint chết**: `site.../basketball/nba/teams/20/roster`
  trả **200 với `athletes: 0`** (kiểm sống) → `athletes=0` trong mọi
  journal → bộ lọc tin theo tên cầu thủ vô hiệu (roster_names=0).
- **(c) Đạo hàm board-day bất nhất (nhỏ)**: hai trận cùng 19:00 ET
  22/10 nhưng 093 tra board 20261022 (trúng) còn 094 tra 20261023+
  20261021 (trượt ngày) — nghi lệch UTC/ET ở đạo hàm kickoff-day.

## 4. Thí nghiệm tự nhiên trên CHÍNH trận này (V2 vs V3)

Cùng FD-2026-M48: **V2** (gói rỗng) → VETO INSUFFICIENT_EVIDENCE,
cited 0. **V3 bóng ma** (tự tra cứu) → VETO với mã thật
(`EVIDENCE_CONTRADICTS_LEG`, `MODEL_MARKET_DIVERGENCE`,
`SOURCE_FIXTURE_MISMATCH`) kèm **7 nguồn web trong đó có trang chính
thức whufc.com** ("Brighton & Hove Albion v West Ham United — all you
need to know") + bảng xếp hạng WSL + BBC. Kết luận: V3 đã TỰ bù phần
lớn khoảng trống này NGAY HÔM NAY, không cần sửa gì; nhưng V2 vẫn là
đường dự phòng và gói nền vẫn là điểm xuất phát của V3 nên bệnh gốc
vẫn phải sửa.

## 5. Đề xuất sửa NHỎ NHẤT (chưa làm gì trong lượt này)

| # | Sửa | Tác động | Gate |
|---|-----|----------|------|
| 1 | `SPORT_PATH["WSL"] = "soccer/eng.w.1"` + đổi lookup WSL sang **khớp TÊN đội trên board** (không dùng event id FD-*) | lane WSL: news/scoreboard/injuries sống lại | **Phải qua chu trình + A7** — đổi collector = đổi luật bằng chứng cho cả V2 (dự phòng) lẫn gói nền V3 |
| 2 | `_injury_sources` follow `$ref` 1 hop (GET thêm, journal từng hop) | NBA (mọi giải có core API): injury citation sống lại | **Chu trình + A7** |
| 3 | Roster: đổi sang endpoint trả đủ athletes (core roster hoặc site roster + season param) hoặc bỏ tầng roster một cách trung thực | NBA: bộ lọc tin theo tên cầu thủ sống lại | **Chu trình + A7** |
| 4 | Đạo hàm board-day: chốt luật ngày (ET của kickoff) và tra đủ 2 ngày lân cận | NBA: hết trượt ngày lookup | Gộp chu trình với #2 |
| 5 | Lane WSL tự chụp thêm: trang sự kiện Gamma (lane đã đọc Gamma cho quote — dẫn URL vào collector) + trang chính thức whufc.com/wslfootball (đã thấy V3 tự tìm được) | WSL: nguồn "trên cấp tin đồn" ngay trong gói nền | **Chu trình + A7**; allow-list collector mở thêm 2 host này |

## 6. Trạng thái lượt này

KHÔNG file code nào đổi, KHÔNG config nào đổi, KHÔNG hành vi production
nào đổi. Bằng chứng: các nhật ký dẫn ở mục 1–2 + các GET read-only
ghi trong mục 3. Tất cả đề xuất ở mục 5 CHỜ owner phê chu trình.
