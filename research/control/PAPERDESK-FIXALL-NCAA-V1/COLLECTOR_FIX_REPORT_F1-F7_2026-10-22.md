# CHU TRÌNH SỬA BỘ THU THẬP BẰNG CHỨNG — BÁO CÁO F1–F7
(2026-10-22; theo kế hoạch điều phối viên, dựa trên
DIAGNOSIS_EMPTY_EVIDENCE_2026-10-22.md đã kiểm toán CONFIRMED.
Branch: `orca/collector-evidence-fix-v1` — DỪNG TRƯỚC merge/adoption.)

## Trạng thái 7 mục

| Mục | Nội dung | Trạng thái |
|---|---|---|
| F1 | WSL → `soccer/eng.w.1`; tra trận trên board bằng KHỚP TÊN ĐỘI (token match bỏ marker nữ); lookup theo mã FD-* đã bỏ hẳn cho lane không-phải-id-ESPN (NBA/NCAA giữ id match) | ✅ code + battery |
| F2 | Injuries: follow `$ref` đúng 1 hop (trần cứng 1, từng hop journal); hỏng → 0 nguồn + journal rõ ràng | ✅ code + battery |
| F3 | Roster: cả 3 endpoint ứng viên đều không có athletes (site roster=0, `?season=`=0, core athletes 404, teams endpoint=0 — kiểm sống) → **GỠ tầng trung thực**, mọi lần thu thập đều journal ghi chú gỡ | ✅ code + battery |
| F4 | Board-day: ngày ET của kickoff + 2 ngày lân cận; **ngày đấu tra trước**, láng giềng là dự phòng; tìm thấy là dừng (1 citation/trận); các ngày đã tra ghi journal | ✅ code + battery |
| F5 | WSL tự chụp thêm ĐÚNG +2 host: `gamma-api.polymarket.com` (URL sự kiện của chính trận, thread từ event_id trong hàng MARKET_QUOTE của ledger qua ops) + `wslfootball.com/fixtures/` (trang giải chính thức, đã verify 200 nội dung WSL) | ✅ code + battery |
| F6 | Quét MỌI lane — bảng bên dưới; slug chết khác: **SOCCER generic** (cùng bệnh WSL) — KHÔNG sửa mù trong gói này vì cần bảng đối chiếu giải→slug (mỗi giải một slug, bịa là vi phạm evidence-first) — ghi làm việc tiếp theo có chu trình riêng | ✅ bảng |
| F7 | Đo độ trễ tin chấn thương NBA vs T−6h10m — CHỈ ghi số, không đổi anchor law | ✅ bảng số |

## CỔNG

- **Battery: `tests/papertrade_exec/` 316/316 PASSED × 2 lần liên tiếp**
  (battery U5 được re-base lên luật collector mới với erratum F1–F5;
  3 test bóng ma trong test_free_research đặt cờ shadow tường minh vì
  production default đã là false sau GO kích hoạt V3).
- Không đụng: luật quyết định, AI_PROMPT_V2/V3, anchor law, luật
  vốn/stake, cascade model; `ai_free_research.shadow` giữ nguyên false;
  config KHÔNG đổi khóa nào (F5 host-allow nằm trong code collector,
  không phải config).

## BẰNG CHỨNG SỐNG (mạng thật, `evidence/collector_fix_20261022/`)

**(a) Gói WSL FD-2026-M48 (trận sắp đấu 24/10)** — `proof_a_wsl_packet_
FD-2026-M48.json`: **3 nguồn, không rỗng** —
`scoreboard_status` (khớp tên → tìm thấy event ESPN 401902884 "Brighton
& Hove Albion vs West Ham United", trạng thái "Sat, October 24th at
12:15 PM EDT") + `gamma_event` (gamma-api…id=1212928, tiêu đề trận +
mô tả WSL) + `league_official` (wslfootball.com/fixtures, excerpt nêu
trận đấu). ≥1 nguồn chính thức/Gamma: **ĐẠT**.

**(b) Gói NBA 401909093 (76ers@Cavaliers, đêm gần nhất)** —
`proof_b_nba_packet_401909093.json`: **7 trích dẫn chấn thương thật qua
đường $ref**, mỗi hop journal đầy đủ. Chất lượng citation sau khi nâng
extractor (trong trần 1 hop — `shortComment` có sẵn tên + bối cảnh,
KHÔNG cần hop thứ hai): "Fall (quadriceps) is out for Thursday's game
against Cleveland.", "Wade (ankle) is questionable…", "Allen (knee) is
questionable for Thursday's game against the 76ers." — CẢ HAI ĐỘI đều
có tên người và trạng thái. **ĐẠT**. Ghi nhận trung thực: tên cầu thủ
nằm trong `shortComment`; trường `athlete` bên trong item vẫn là
`$ref` nữa — vượt trần 1 hop của F2 nên KHÔNG follow (nếu owner muốn
tên từ trường athlete riêng thì đó là quyết định nâng trần, chu trình
khác).

**(c) Bảng F6 — mọi lane trong SPORT_PATH, GET sống 2026-10-22:**

| Lane | Địa chỉ | Board | News | Kết luận |
|---|---|---|---|---|
| NBA | basketball/nba | 200 (8 events) | 200 OK | khỏe |
| WNBA | basketball/wnba | 200 (1 event) | 200 OK | khỏe |
| SOCCER | soccer (generic) | **FAIL** | **FAIL** | **bệnh giống WSL** — cần crosswalk giải→slug (chưa sửa trong gói này, không bịa slug) |
| WSL | soccer (generic) → **soccer/eng.w.1** | FAIL → **200** | FAIL → **200** | **ĐÃ SỬA (F1)** |
| NCAA-M | basketball/mens-college-basketball | 200 (0 events 24/10 — ngoài mùa/vòng) | 200 OK | khỏe |
| NCAA-W | basketball/womens-college-basketball | 200 (0 events) | 200 OK | khỏe |

## F7 — độ trễ tin chấn thương NBA so với mốc chụp T−6h10m
(`f7_injury_delay.json`; CHỈ SỐ, anchor law không đổi)

- 14 trận tuần này (22–26/10), 28 đội, **67 mục chấn thương đo được,
  0 không đo được** (trường `lastUpdate` hoặc `date` có mặt trên mọi
  item đã resolve).
- **67/67 (100%) đã đăng TRƯỚC mốc T−6h10m** của trận tương ứng
  (`share_known_at_anchor = 1.0`).
- Kết luận bằng số: với slate NBA tuần này, **thời điểm chụp không phải
  nút thắt** — tin chấn thương sẵn có từ trước mốc; thủ phạm gói rỗng
  đúng như chẩn đoán là tầng collector (đã sửa F2). Không khuyến nghị
  đổi anchor law.

## DỪNG TRƯỚC MERGE/ADOPTION

Branch đã commit + push (`orca/collector-evidence-fix-v1`), KHÔNG merge
vào main, KHÔNG đụng production đang chạy (app/service vẫn chạy bộ thu
thập cũ trên main). Chờ lệnh adoption riêng của owner. Kiểm toán A7 độc
lập trên diff + proof: xem `A7_COLLECTOR_FIX_VERDICT_2026-10-22.md`.
