# NGHIÊN CỨU GIAI ĐOẠN 1 — ENDPOINT LẤY VÍ PRO/BET POLYMARKET THEO TỪNG GIẢI

## ERRATA 2026-11-05 (sau đính chính đường dẫn của agent chính)

(a) Claim cũ SAI: đoạn "Nguồn hụt" cuối mục 1 dưới đây kết luận "thư mục `sports-polymarket-cutover-prep-v1/` KHÔNG tồn tại trên đĩa → THIẾU DỮ LIỆU". Sai vì agent chính giao sai đường dẫn trong dispatch gốc (đường dẫn trong repo). Phép `ls` hồi đó chỉ đúng cho đường dẫn sai; kết luận "không tồn tại" không đúng cho toàn bộ nguồn này.

(b) Đường dẫn ĐÚNG: `/Users/hoangminhlong/.my-quantitative-data/sports-polymarket-cutover-prep-v1/` (cấp HOME, ngoài repo my-quantitative). Thư mục TỒN TẠI, gồm: `journal/` (395 file), `live/` (`gamma_events/` 790 file, `clob_books/`, `espn_wc_euro/`), `pinned_core_copy/`, `pinned_dep_copy/`.

(c) Kết quả kiểm tra mới (CHỈ ĐỌC đĩa, 0 request API; mọi số dưới lấy từ journal/snapshot trên đĩa):

**CÓ bản đồ giải↔thị trường Polymarket — nhưng CHỈ cho WSL:**

- WSL ↔ Gamma `GET /events?tag_id=105959&closed=false`. Bằng chứng: `journal/journal_wsl_lane_2026-11-05T131729Z.jsonl` (1 dòng, URL nguyên văn + sha256 + snapshot_path); 210 snapshot `live/gamma_events/wsl_tag_p00_*.json` liên tục từ `wsl_tag_p00_2026-10-14T015119Z.json` đến `wsl_tag_p00_2026-11-05T131729Z.json`.
- Snapshot mới nhất hôm nay (`wsl_tag_p00_2026-11-05T131729Z.json`): **35 event WSL đang mở**, gồm trận đơn slug dạng `wsl-mci-whu-2026-11-07`, `wsl-avl-mnu-2026-11-08`, `wsl-cfc-eve-2026-11-07`… và biến thể (exact-score, first-to-score, halftime-result). Mỗi event có `conditionId`, `sportsMarketType` (moneyline / soccer_exact_score / soccer_halftime_result / soccer_first_to_score), `gameStartTime`, tag `['Sports','Games','Soccer',"Women's Super League"]`.
- **Đổi kết luận dòng WSL (mục 3.3 và bảng mục 4):** từ "THIẾU DỮ LIỆU" → **ĐỦ VỀ KÊNH DỮ LIỆU**: đã có sẵn đường liệt kê thị trường WSL theo tag (rẻ hơn quét `/markets`), snapshot sống tới hôm nay. Số VÍ pro WSL: vẫn "chưa có số" (snapshot chỉ có event, chưa có trade/ví nào).

**Các giải khác — kiểm trong cùng thư mục, không đổi kết luận cũ:**

- `events_open_*` (10-10 → 10-31, trang p00–p01): NBA chỉ bắt được thị trường MÙA VỤ (13 slug futures: `nba-2027-champion`, rookie-of-the-year, free-agency, play-in…); WNBA chỉ 1 slug futures `wnba-2026-champion-464`; NCAA toàn bộ 336 slug là `ncaa-football-*` (bóng bầu — KHÔNG phải bóng rổ); EPL/LaLiga chỉ futures (`epl-2027-champion`…). → Mục 3.2 (WNBA), 3.5 (NCAA nam), 3.6 (NCAA nữ) giữ nguyên THIẾU DỮ LIỆU; mục 3.1 (NBA) giữ nguyên ĐỦ kênh (bằng chứng trận đơn NBA vẫn từ probe V2).
- `live/clob_books/`: snapshot `clob.polymarket.com/book?token_id=…` cho event soccer 3 cửa (watch_1167584…, watch_1255696… HOME/AWAY/DRAW) — bổ sung bằng chứng kênh bóng đá nam; mục 3.4 không đổi.
- `live/espn_wc_euro/`: lịch ESPN vòng loại World Cup/Euro NAM các chu kỳ 2027–2031 — nguồn fixture bóng đá nam (ESPN, không phải Polymarket).
- `pinned_dep_copy/exec/research/papertrade_exec/config.json` (schema `sports_papertrade_exec_config@2`) và `__init__.py` dòng 29 `LEAGUES = ("NBA", "WNBA", "SOCCER")`: cấu hình lane theo The Odds API (`basketball_nba`, `basketball_wnba`, `soccer_uefa_nations_league`) — KHÔNG phải bản đồ tag Polymarket.

**Lưu ý vận hành mới cho GĐ2:** journal ghi WSL lane worker CÒN SỐNG, hôm nay 05/11 đã fetch Gamma **22 request** (06:12Z → 13:17Z, mỗi lần 1 request p00) — tức ngân sách Gamma hôm nay bị tiêu không chỉ bởi Việc 3 (200/200) mà còn bởi lane WSL. Việc xếp hàng trần ở GĐ2 phải tính cả luồng này.

- Ngày: 2026-11-05. Người thực hiện: subagent RESEARCHER Giai đoạn 1, lane PRO-WALLET-V1.
- Phạm vi: CHỈ ĐỌC. Không sửa file nào khác ngoài 2 file output của giai đoạn này (báo cáo này + handoff JSON). Không tạo tài khoản, không chi tiêu, không đặt lệnh.
- Số request API Polymarket đã gọi trong giai đoạn này: **0**. Lý do: trần 200 request/ngày là cộng dồn mọi tiến trình và hôm nay 05/11 Việc 3 (copytrade v2) đã dùng đúng 200/200 (bằng chứng: `polymarket-copytrade-20-VIEC3-FIX-INTERIM-2026-11-05.md` dòng 10: "Đúng 200/200 request thật… dừng vì hết trần — đúng luật"; dòng 38 xác nhận lại). Mọi số liệu Polymarket trong báo cáo này lấy từ tài liệu trên đĩa đã liệt kê ở mục 1.
- Web (WebSearch) chỉ dùng cho TRẠNG THÁI MÙA GIẢI (lịch thi đấu), có ghi nguồn từng dòng. Không dùng web để đếm thị trường Polymarket hay khẳng định số liệu ví.

## 1. Nguồn tài liệu đã dùng (trên đĩa)

| # | File | Vai trò |
|---|---|---|
| 1 | `.my-quantitative-data/PRO-WALLET-V1/input-edge-hunt-ai-desk/pro-wallet-pack/ke-hoach-lop-y-kien-vi-pro-nba-wnba-2026-11-05.md` (sha 6196d282…, đã verify Bước 0) | Kế hoạch gốc lớp ý kiến ví pro |
| 2 | `~/Downloads/Polymarket/docs/polymarket-copytrade-20-SPEC-V2-FROZEN.md` (sha ae504a97…bee55d8) | Luật endpoint + etiquette request |
| 3 | `~/Downloads/Polymarket/docs/polymarket-copytrade-20-PROBE-REPORT-V1.md` | Bằng chứng đo endpoint thật (16 request, 2026-11-02) |
| 4 | `~/Downloads/Polymarket/docs/polymarket-copytrade-20-PROBE-REPORT-V2.md` | Bằng chứng bổ sung (205 request, 2026-11-02): tag 'Sports', slug NBA, EPL mở, Chelsea |
| 5 | `~/Downloads/Polymarket/docs/polymarket-copytrade-20-VIEC-B-C-REPORT-V1.md` | Đối chứng leaderboard: KHÔNG có bảng tháng quá khứ; sổ PaperDesk (lane WSL) |
| 6 | `~/Downloads/Polymarket/docs/polymarket-copytrade-20-VIEC3-COUNT-REPORT.md` | Kỹ thuật liệt kê Gamma + trades theo condition_id; mẫu thị trường NBA đo thật |
| 7 | `~/Downloads/Polymarket/docs/polymarket-copytrade-20-VIEC3-FIX-INTERIM-2026-11-04.md`, `…-2026-11-05.md` | Trạng thái listing hiện tại (cận dưới, chưa xong) |
| 8 | `.my-quantitative-data/PRO-WALLET-V1/input-edge-hunt-ai-desk/pro-wallet-pack/paperdesk-spec-d2-gate-invariant-2026-10-26.md` | Xác nhận 6 lane PaperDesk: NBA, WSL, NCAA-M, NCAA-W, SOCCER, WNBA (mục 1: "MOI lane (NBA, WSL, NCAA-M, NCAA-W, SOCCER, WNBA)") |

Nguồn hụt: thư mục `.my-quantitative-data/sports-polymarket-cutover-prep-v1/` (dispatch ghi "nếu có bản đồ giải/thị trường") **KHÔNG tồn tại trên đĩa** — đã kiểm tra bằng `ls` (chỉ có `nfl-ng-scored-v1` và `PRO-WALLET-V1` trong `.my-quantitative-data/`). → Bản đồ giải/thị trường cutover PaperDesk↔Polymarket: **THIẾU DỮ LIỆU**.

## 2. Endpoint Polymarket lấy ví/bet — chung cho mọi giải (bằng chứng trên đĩa)

Không có endpoint riêng theo giải. Cách lấy dữ liệu ví/bet cho một giải: (1) liệt kê thị trường thể thao của giải bằng Gamma `/markets`, (2) lấy bet theo từng thị trường hoặc theo từng ví bằng Data API. Cụ thể:

| Việc cần làm | Endpoint + tham số | Bằng chứng (file + dòng) |
|---|---|---|
| Liệt kê thị trường thể thao | Gamma `GET /markets?include_tag=true` (+ `closed=true&end_date_min/max` + `order=id&ascending=true&limit=100`; server kẹp limit tại 100) | SPEC-V2-FROZEN dòng 77–79 (mục 2.1); VIEC3-COUNT-REPORT dòng 13 |
| Nhận diện thể thao + loại trận/trận đơn | tag label đúng chữ `'Sports'` khi `include_tag=true`; trong đó trận đơn ⇔ `sportsMarketType` ≠ rỗng VÀ `gameStartTime` ≠ rỗng | PROBE-V2 dòng 77–80, 85–92 (đúng 23/23 mẫu, đề xuất đã được spec v2 mục 1 luật Q1 sử dụng); SPEC-V2-FROZEN dòng 81–83 |
| Tra 1 thị trường theo mã/slug | lặp `condition_ids=` từng mã + `closed=any` (dạng comma KHÔNG hoạt động); đường dự phòng `slug=` | PROBE-V2 dòng 24–29; PROBE-V1 dòng 70, 74–76 (bẫy `closed` mặc định=false); VIEC3-COUNT-REPORT dòng 57 |
| Lấy BET theo THỊ TRƯỜNG (để gom ví đặt trận đó) | Data API `GET /v2/trades?condition_id=<cid>&taker_only=false&start&end&limit=500`. Tham số `market=` BỊ TỪ CHỐI (HTTP 400); KHÔNG cursor, KHÔNG offset → thị trường >500 fill phải chia nhỏ cửa sổ thời gian | VIEC3-COUNT-REPORT dòng 19 |
| Lấy BET theo VÍ (để biết ví pro đặt gì) | Data API `GET /v2/trades?user=<ví>&taker_only=false&start=<epoch>&end=<epoch>` (`taker_only=false` bắt buộc nếu muốn đủ cả maker; mặc định true làm mất dòng) | PROBE-V1 dòng 27, 59–60, 65–66; PROBE-V2 dòng 37–44 |
| Tiền USD từng lệnh | `usdc_size` CHỈ có trên `GET /v2/activity?user=&type=TRADE` (đối chiếu 100/100 khớp price×size) | PROBE-V1 dòng 61, 65; PROBE-V2 dòng 171–172 |
| Vị thế / thống kê ví | `GET /v2/positions?user=`; `GET /v2/user-stats?user=` (không có cửa sổ thời gian) | PROBE-V1 dòng 29, 31, 51 |
| Kết quả chốt (để tính pro lời/lỗ) | `GET /v2/resolutions?condition=` → `payouts` micro-USDC; đối chiếu Gamma `umaResolutionStatus` | PROBE-V1 dòng 32, 104–107; PROBE-V2 dòng 114–122 |
| Pool ví "pro" theo xếp hạng | `GET /v2/leaderboard?time_period=…&category=sports&sort_by=PNL` — chỉ `time_period ∈ {day, week, month, all}` TỪ HIỆN TẠI; KHÔNG có tham số tháng quá khứ (đã chứng minh bằng request: tham số `end=` bị bỏ qua) | PROBE-V1 dòng 30; VIEC-B-C-REPORT-V1 dòng 15–20, 24–25 |

### Giới hạn request (luật, áp cho MỌI giải)

- **~200 request/ngày, cộng dồn mọi tiến trình + 10 giây/request** — SPEC-V2-FROZEN dòng 69 ("ngân sách ~200 request/ngày, 10 giây/request") và dòng 100; nhịp ≥10 giây giữ nguyên khi chạy thật (VIEC3-FIX-INTERIM-2026-11-05 dòng 10: "0 khoảng cách <9 giây").
- 429/403/throttle/chậm bất thường → DỪNG toàn bộ, không tăng tốc bù (SPEC-V2-FROZEN dòng 101; tiền lệ watchdog PROBE-V2 dòng 13, VIEC3 dòng 70).
- **Offset-cap Gamma:** `offset ≥ 2100` bị từ chối HTTP 422 → mỗi query tối đa ~2.100 dòng; khắc phục bằng chia lát cửa sổ `end_date` (bisection) (VIEC3-COUNT-REPORT dòng 18).
- **Trần 500 fill/request** trên trades theo thị trường (không cursor/offset — VIEC3 dòng 19). Cửa sổ `prices-history` tối đa 15 ngày/request (PROBE-V1 dòng 117 — chỉ dẫn chứng, chưa cần cho lớp này).
- Hôm nay 05/11 trần 200 ĐÃ HẾT (Việc 3 dùng 200/200 — interim 11-05 dòng 10). Listing Việc 3 chưa xong: còn ~3 ngày dương lịch nữa @200/ngày, 87/105 ngày cửa sổ chưa phủ tự nhiên (interim 11-05 dòng 31–32). → Mọi thu thập thật của lane này mặc định XẾP HÀNG sau Việc 3 (đúng phát hiện F2 trong `REVIEW_PROMPT_CHU_2026-11-05.md`, phương án mặc định (a) của chủ).

## 3. BẢNG TỪNG GIẢI (trả lời đúng 4 cột yêu cầu)

### 3.1 NBA

- Endpoint lấy ví/bet: Gamma `/markets?include_tag=true` (thị trường NBA có tag 'Sports' + 'NBA' + 'Basketball'; tra theo slug dạng `nba-mem-uta-2026-10-26`) → `GET /v2/trades?condition_id=<cid>&taker_only=false` gom ví từng trận, hoặc `/v2/trades?user=<ví>` theo ví.
- Bằng chứng trên đĩa: PROBE-V2 dòng 20, 26–27 (thị trường "Grizzlies vs. Jazz, NBA", conditionId `0x401c1614a93ddc09…`, slug `nba-mem-uta-2026-10-26`, HTTP 200); dòng 78 (thị trường mùa vụ NBA có tag 'Sports' + NBA + Basketball); VIEC3-COUNT-REPORT dòng 49 — thị trường NBA đo thật `nba-sas-dal-2025-10-22 total`: 49 fills, 5.955 USD đoạn 1, **23 ví** (dưới ngưỡng 10.000 USD của spec v2 — số liệu đo mẫu 2025, không phải mùa hiện tại).
- Giới hạn request: như mục 2 (200/ngày cộng dồn + 10 giây + offset-cap 2100 + 500 fill/request).
- Trạng thái mùa: **ĐANG MỞ**. Mùa chính 2026-27 bắt đầu 20/10/2026, kết thúc 11/4/2027 (nguồn: [NBA.com key dates](https://www.nba.com/news/key-dates), [Wikipedia 2026-27 NBA season](https://en.wikipedia.org/wiki/2026%E2%80%9327_NBA_season)). Hôm 05/11/2026 đang giữa mùa chính.
- Đủ/thiếu cho lớp ví pro: **ĐỦ về kênh dữ liệu** (có trận đang chơi, endpoint đã đo hoạt động, có ví thật quan sát được 23 ví/thị trường mẫu). Chưa có: danh sách ví pro đóng băng, số ví NBA hiện tại ("chưa có số" — không đếm được hôm nay vì trần request hết).

### 3.2 WNBA

- Endpoint: cùng hệ endpoint chung (mục 2). KHÔNG có endpoint riêng WNBA.
- Bằng chứng trên đĩa: **KHÔNG có thị trường WNBA nào xuất hiện trong toàn bộ tài liệu nguồn đã liệt kê** (đã grep `wnba` trên 7 file: 0 kết quả). → **THIẾU DỮ LIỆU** thị trường/ví WNBA trên Polymarket: "chưa có số".
- Giới hạn request: như mục 2.
- Trạng thái mùa: **NGHỈ (off-season)** — khớp đúng ghi chú của chủ "WNBA nghỉ từ ~tháng 10". Mùa 2026 chạy 08/05/2026 → 31/10/2026 (nguồn: [Wikipedia 2026 WNBA season](https://en.wikipedia.org/wiki/2026_WNBA_season)); Finals 17–31/10/2026 (nguồn: [WNBA.com key dates](https://www.wnba.com/keydates)); ESPN đã phát hành hướng dẫn off-season cho các đội bị loại (nguồn: [ESPN WNBA offseason guides](https://www.espn.com/wnba/story/_/id/49860363/wnba-offseason-2026-playoffs-eliminated-teams-draft-trade-free-agency-guides)). Không có trận WNBA mới trong thời gian chạy bóng dự kiến.
- Đủ/thiếu: **THIẾU DỮ LIỆU** (hai lớp: mùa nghỉ → không trận mới; không có bằng chứng thị trường WNBA trên đĩa). Đây chính là rủi ro kế hoạch gốc đã ghi trước: "WNBA ít người đặt, có thể nhiều ngày không đủ 3 ví — lúc đó lớp này im lặng, đó là đúng, không phải lỗi" (kế hoạch gốc dòng 90).

### 3.3 WSL (bóng đá nữ Anh — Women's Super League)

- Endpoint: cùng hệ endpoint chung (mục 2). KHÔNG có endpoint riêng WSL.
- Bằng chứng trên đĩa: **KHÔNG có thị trường WSL nào trong tài liệu nguồn** (grep `wsl` trên 7 file: 0 kết quả thị trường Polymarket). Lưu ý tránh nhầm: `VIEC-B-C-REPORT-V1.md` dòng 11, 53 có nhắc WSL (M48, Brighton vs West Ham, BET_PAPER 22/10/2026) nhưng đó là dòng sổ PaperDesk, KHÔNG phải bằng chứng thị trường Polymarket WSL tồn tại. → Polymarket WSL: **chưa có số**.
- Giới hạn request: như mục 2.
- Trạng thái mùa: **ĐANG MỞ**. Mùa 2026-27 chạy 04/09/2026 → 23/05/2027 (nguồn: [Wikipedia 2026-27 Women's Super League](https://en.wikipedia.org/wiki/2026%E2%80%9327_Women%27s_Super_League), [Sky Sports WSL fixtures 2026/27](https://www.skysports.com/football/news/13567659/womens-super-league-fixtures-2026-27-man-city-host-birmingham-city-and-london-city-lionesses-face-man-utd-in-opening-round), [BBC Sport](https://www.bbc.com/sport/football/articles/c17j5e0ky9jo)).
- Đủ/thiếu: **THIẾU DỮ LIỆU** phía Polymarket (mùa đang mở nên có trận để đo, nhưng chưa có đo đạc thị trường/ví nào trên đĩa — cần ngân sách request riêng sau khi Việc 3 xong).

### 3.4 Bóng đá nam (lane SOCCER)

- Endpoint: cùng hệ endpoint chung (mục 2).
- Bằng chứng trên đĩa (đã đo thật):
  - "Ghana vs. Panama" ("Will Ghana win on 2026-06-17?") và "Spain vs. Argentina" (hòa?) — 2 thị trường bóng đá nam đã đóng, `sportsMarketType=moneyline`, có `gameStartTime`, volumeNum 12,68 triệu / 9,12 triệu USD (PROBE-V1 dòng 83–91). Đây là trận World Cup 06–07/2026 (đã qua).
  - Ví mẫu joseph00677 giữ vị thế "Chelsea win 2026-10-24" (PROBE-V2 dòng 56) — bóng đá nam nam Anh tháng 10/2026.
  - Lúc thăm dò 02/11/2026: nhóm "Thể thao đang mở" gồm "CS2, tennis, EPL" — **EPL có thị trường đang mở** (PROBE-V2 dòng 80). Lưu ý: đây là quan sát trên mẫu 23 thị trường thăm dò, KHÔNG phải đếm đầy đủ.
- Giới hạn request: như mục 2. Lưu ý riêng: World Cup nằm ngoài các đoạn kỷ nguyên B của copytrade (SPEC-V2-FROZEN dòng 67 "tránh World Cup") — không dính lớp này.
- Trạng thái mùa: **ĐANG MỞ**. Ngoại hạng Anh 2026-27 chạy 21/08/2026 → 30/05/2027 (nguồn: [PremierLeague.com](https://www.premierleague.com/en/news/4468487/dates-for-202627-premier-league-season-confirmed), [Wikipedia 2026-27 Premier League](https://en.wikipedia.org/wiki/2026%E2%80%9327_Premier_League)). Các giải nam châu Âu lớn khác cũng chạy dạng 08/2026–05/2027 (chỉ EPL được kiểm chứng nguồn; các giải khác chưa tra riêng — ghi trung thực).
- Đủ/thiếu: **ĐỦ về kênh dữ liệu** (có bằng chứng thị trường bóng đá nam trên Polymarket: đã đóng + đang mở; endpoint hoạt động). Chưa có: số ví pro, danh sách đóng băng — "chưa có số".

### 3.5 NCAA nam (bóng rổ nam, lane NCAA-M)

- Endpoint: cùng hệ endpoint chung (mục 2). KHÔNG có endpoint riêng NCAA.
- Bằng chứng trên đĩa: **KHÔNG có thị trường NCAA bóng rổ nào trong tài liệu nguồn**. Cẩn thận không nhầm: các mã `cfb-usc-ill-2025-09-27`, `cfb-ballst-wmich-2025-10-11` trong VIEC3-COUNT-REPORT dòng 43–44 là **bóng bầu đại học (college football)**, môn khác với bóng rổ; chúng chứng minh Polymarket có thị trường NCAA (đại học Mỹ) nói chung, không chứng minh có bóng rổ NCAA. → Bóng rổ NCAA nam trên Polymarket: **chưa có số**.
- Giới hạn request: như mục 2.
- Trạng thái mùa: **MỚI KHỞI ĐỘNG**. Mùa 2026-27 Division I nam bắt đầu 01/11/2026, mùa chính kết thúc 14/3/2027 (nguồn: [NCAA.com men's season start](https://www.ncaa.com/news/basketball-men/article/2026-08-28/when-does-2026-27-college-basketball-season-start), [Wikipedia](https://en.wikipedia.org/wiki/2026%E2%80%9327_NCAA_Division_I_men%27s_basketball_season)). Hôm 05/11/2026: mùa đã bắt đầu 4 ngày.
- Đủ/thiếu: **THIẾU DỮ LIỆU** (mùa mới bắt đầu nên thị trường có thể còn thưa; chưa có đo đạc thị trường/ví bóng rổ NCAA nào trên đĩa).

### 3.6 NCAA nữ (bóng rổ nữ, lane NCAA-W)

- Endpoint: cùng hệ endpoint chung (mục 2). KHÔNG có endpoint riêng NCAA.
- Bằng chứng trên đĩa: **KHÔNG có thị trường NCAA nữ nào trong tài liệu nguồn** (grep `ncaa`: chỉ ra cfb bóng bầu ở VIEC3). → **chưa có số**.
- Giới hạn request: như mục 2.
- Trạng thái mùa: **MỚI KHỞI ĐỘNG**. Mùa 2026-27 Division I nữ bắt đầu 01/11/2026 (trận mở màn Villanova vs. Notre Dame tại Rome), mùa chính kết thúc 14/3/2027 (nguồn: [NCAA.com women's season start](https://www.ncaa.com/news/basketball-women/article/2026-08-28/when-does-2026-27-womens-college-basketball-season-start)).
- Đủ/thiếu: **THIẾU DỮ LIỆU** (như NCAA nam; rủi ro liquidity thấp hơn nữa — kế hoạch gốc cảnh báo dạng này ở WNBA dòng 90).

## 4. Tổng hợp một dòng cho GĐ2 (PLANNER)

| Giải | Mùa (05/11/2026) | Thị trường Polymarket trên đĩa | Kết luận dữ liệu cho lớp ví pro |
|---|---|---|---|
| NBA | ĐANG MỞ (từ 20/10/2026) | CÓ bằng chứng (slug, mẫu 23 ví) | ĐỦ kênh — chưa có danh sách ví pro |
| WNBA | NGHỈ (mùa 2026 đã kết thúc) | KHÔNG có | THIẾU DỮ LIỆU |
| WSL | ĐANG MỞ (từ 04/09/2026) | KHÔNG có | THIẾU DỮ LIỆU (cần đo khi có ngân sách) |
| Bóng đá nam | ĐANG MỞ (EPL từ 21/08/2026) | CÓ bằng chứng (World Cup đã đóng, EPL mở, Chelsea 10/2026) | ĐỦ kênh — chưa có danh sách ví pro |
| NCAA nam | MỚI MỞ (từ 01/11/2026) | KHÔNG có (chỉ cfb bóng bầu, môn khác) | THIẾU DỮ LIỆU |
| NCAA nữ | MỚI MỞ (từ 01/11/2026) | KHÔNG có | THIẾU DỮ LIỆU |

Hệ quả thiết kế đáng chú ý nhất cho GĐ2:

1. Kế hoạch gốc chỉ phạm vi NBA + WNBA (dòng 23: "Chỉ NBA và WNBA. Chưa làm NCAA, bóng đá"). Prompt chủ mở rộng toàn bộ giải — nhưng ngay trong phạm vi gốc, WNBA đang nghỉ → tháng chạy bóng đầu tiên sẽ gần như chỉ có NBA có trận. GĐ2 phải quyết số trận tối thiểu mỗi giải để không kết luận từ mẫu quá mỏng (kế hoạch gốc dòng 73: <30 trận có ý kiến → "thiếu dữ liệu").
2. Đường dựng danh sách ví pro không thể dùng leaderboard tháng quá khứ (VIEC-B-C dòng 24–25) → phải gom từ trades theo thị trường từng giải (mục 2), đúng hướng spec v2 đã đóng băng.
3. Chi phí request mỗi ngày chạy bóng: cận dưới ~1 request/thị trường + 1 request/ví pro (tối đa 30 ví) + chia cửa sổ nếu thị trường >500 fill — GĐ2 phải ước và trình chủ trước khi build (kế hoạch gốc dòng 80: "Tôn trọng giới hạn 200 request/ngày").
4. Toàn bộ thu thập thật phải xếp hàng sau khi listing Việc 3 xong (~3 ngày nữa, interim 11-05 dòng 32) hoặc chờ chủ chọn chia trần — không được tự gọi API khi trần đã cạn.

## 5. Câu bắt buộc

Giai đoạn 1 xong (kèm ERRATA 2026-11-05 ở đầu file). Làm được: đọc đủ 8 nguồn trên đĩa (kế hoạch gốc, spec copytrade v2 đóng băng, 2 báo cáo thăm dò, báo cáo Việc B/C, 3 báo cáo Việc 3) + tra trạng thái mùa 6 giải có nguồn web; xác định endpoint lấy ví/bet cho từng giải (Gamma /markets include_tag=true → /v2/trades theo condition_id hoặc theo user; tiền USD qua /v2/activity usdc_size), ghi rõ giới hạn 200 request/ngày cộng dồn + 10 giây/request + offset-cap 2100 + 500 fill/request, xác nhận NBA và bóng đá nam đang mở mùa, WNBA nghỉ từ cuối tháng 10/2026, WSL đang mở, NCAA nam/nữ vừa khởi động 01/11/2026; sau errata: quét đúng thư mục cutover-prep cấp HOME, tìm được bản đồ giải↔thị trường WSL↔Gamma /events?tag_id=105959 với 35 event WSL mở trong snapshot 05/11/2026 (slug wsl-*, có conditionId + gameStartTime) và ĐỔI kết luận WSL từ THIẾU DỮ LIỆU sang ĐỦ VỀ KẾNH DỮ LIỆU; kết luận cuối: NBA, bóng đá nam, WSL ĐỦ kênh dữ liệu; WNBA (nghỉ mùa) và NCAA nam/nữ bóng rổ (mới mở, chỉ thấy ncaa-football trên đĩa) THIẾU DỮ LIỆU thị trường; phát hiện WSL lane worker vẫn đang tiêu request Gamma hôm nay (22 request 06:12–13:17Z) ngoài 200/200 của Việc 3; gọi 0 request API Polymarket, không sửa file nào ngoài 2 file output. Chưa làm được: đếm thị trường/ví thật cho từng giải (trần 200 request/ngày hôm nay đã hết vì Việc 3 dùng 200/200); chưa có số ví pro cho giải nào (danh sách ví pro chưa dựng — việc của các giai đoạn sau, sau lệnh của chủ); không tìm thấy bản đồ tag Polymarket cho NBA/WNBA/NCAA nam/NCAA nữ (chỉ có WSL; events_open chỉ bắt futures/mùa vụ và ncaa-football); ngày trận chung kết WNBA chính xác tới ngày chưa kiểm chứng riêng. Cửa tiếp theo: GĐ2 PLANNER soạn spec lớp ý kiến ví pro (dùng sẵn bản đồ tag_id=105959 cho WSL, phạm vi giải theo bảng mục 4 + errata, ngưỡng 3 ví/60%, reset 00:00 UTC, ước ngân sách request từng ngày chạy bóng có tính cả luồng WSL lane worker đang chạy, xếp hàng trần với Việc 3), trình chủ duyệt trước khi build.
