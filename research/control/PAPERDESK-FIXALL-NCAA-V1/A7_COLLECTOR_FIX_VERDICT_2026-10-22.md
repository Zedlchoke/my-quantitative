# A7 COLLECTOR FIX VERDICT 2026-10-22

Chu trình: collector evidence fix F1–F7 — worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/collector-evidence-fix-v1/integration`,
branch `orca/collector-evidence-fix-v1`, HEAD `7d3608c1`, base so diff
`main@9b0def27`. Kiểm toán ĐỘC LẬP (agent riêng, không qua lời kể của
agent thực thi), chỉ đọc; không sửa file, không commit/push.

## 1. Phạm vi kiểm

- Diff đầy đủ `9b0def27..7d3608c1`: đúng 9 file (3 code: `ai_research.py`
  +510/−360 dòng trọng tâm, `ai_producer.py` +9, `ops_service.py` +24;
  2 test: `test_upgrade_u5.py` re-base, `test_free_research.py` +9;
  4 artifact: báo cáo + 3 proof). Working tree sạch, HEAD khớp branch,
  remote `origin/orca/collector-evidence-fix-v1` cùng SHA `7d3608c1`
  (tuyên bố "đã commit + push" của báo cáo: XÁC THỰC).
- Grep đầy đủ diff cho `config.json` (0 hit),
  `AI_PROMPT|anchor|stake|cascade` (chỉ dòng ngữ cảnh không đổi + văn
  bản báo cáo/JSON nói rõ "không đổi").
- Đọc 3 proof + báo cáo; đối chiếu từng tuyên bố với đĩa; chạy lại
  battery; 3 spot-check GET sống; audit mọi URL construction trong
  `ai_research.py`/`ops_service.py`.

## 2. Kết quả từng mục F1–F7

| Mục | Kết quả | Bằng chứng kiểm toán |
|---|---|---|
| F1 WSL `soccer/eng.w.1` + khớp tên | ĐẠT | `SPORT_PATH["WSL"]="soccer/eng.w.1"`; `_find_event`: id-digits → id match, FD-* → khớp token tên cả 2 đội (bỏ marker nữ); test `test_f1_wsl_slug_and_name_based_board_match`; sống: `eng.w.1/scoreboard?dates=20261024` → 200, event 401902884 đúng Brighton & Hove Albion vs West Ham United, khớp proof_a |
| F2 injuries `$ref` 1 hop | ĐẠT (kèm LOW-1) | `_resolve_injury_item`: chỉ item bare-`$ref` (len==1) được ĐÚNG 1 GET, hop journal, hỏng → 0 nguồn; 2 test phủ OK + honest-zero; proof_b: 7 trích dẫn chấn thương qua 7 hop journaled, cả 2 đội có tên + trạng thái |
| F3 gỡ tầng roster | ĐẠT | `_ROSTER_CACHE`/`_roster_full_names`/`_roster_hit` xoá sạch; `ROSTER_REMOVAL_NOTE` journal mỗi lần thu; test khẳng định không GET `/roster` và `not hasattr(AR,"_ROSTER_CACHE")` |
| F4 board days ET ±1 | ĐẠT | `_board_days` = [D-1, D, D+1] America/New_York, ngày đấu trước, thấy là dừng (1 citation/trận), journal đủ; test + proof_a (`['20261024','20261023','20261025']`, et_date=2026-10-24) |
| F5 +2 host gamma + wslfootball | ĐẠT (kèm MED) | `_EXTRA_ALLOWED_HOSTS = {"gamma-api.polymarket.com","wslfootball.com"}` đúng 2 host; `_get_text` ép https + host + byte-cap; `_gamma_source` kiểm host trước fetch; test chặn `evil.example.com`; ops thread URL gamma từ `MARKET_QUOTE.event_id` |
| F6 quét lane | ĐẠT (đúng phạm vi) | Bảng F6 đối chứng sống bổ sung: NBA board 200 (11 events hiện tại — lúc quét 8, số event biến theo thời gian trong ngày), NBA news 200 (50 bài). SOCCER generic còn chết — báo cáo trung thực ghi rõ để dành chu trình crosswalk, KHÔNG sửa mù. Đúng kế hoạch |
| F7 đo trễ chấn thương | ĐẠT (kèm LOW-2) | `f7_injury_delay.json`: 67/67 measurable, 0 unmeasurable, `share_known_at_anchor=1.0`, `law` ghi rõ anchor KHÔNG đổi; kiểm toán tự tính lại toàn bộ 67 dòng: mọi timestamp đều TRƯỚC anchor, 0 ngoại lệ; 14 game, `teams_queried=28` |

## 3. CẤM ĐỤNG: KHÔNG VI PHẠM

- `config.json`: 0 hit trong diff; file trên đĩa nguyên vẹn,
  `"shadow": false` giữ nguyên.
- `AI_PROMPT_V2.md`/`AI_PROMPT_V3.md`: không nằm trong diff.
- anchor/stake: chỉ xuất hiện trong văn bản báo cáo + JSON F7 với nội
  dung "KHÔNG đổi"; không file luật nào bị đụng.
- cascade: chỉ 1 dòng docstring ngữ cảnh không đổi; logic chọn slot
  không sửa.
- `ai_free_research.py`, `laws.py`, `decision_pipeline.py`,
  `ai_gate_v2.py`: nguyên vẹn. Test chỉ đặt `shadow=True` TƯỜNG MINH
  trong môi trường test để chạy plane bóng ma — không đổi default
  production.
- Host audit: mọi URL được dựng chỉ từ 3 host ESPN + `wslfootball.com/
  fixtures/` + gamma (host-checked). Không thấy host nào khác.

## 4. Battery (kiểm toán tự chạy)

`pytest tests/papertrade_exec/ -q`: **316 passed, 0 failed, 0 panic,
58.06s** — khớp đúng con số báo cáo. Kiểm toán chạy 1 lần (đủ đối
chứng); tuyên bố "×2 lần liên tiếp" của agent thực thi không có
artifact lưu đĩa (xem INFO-1).

## 5. Proof đối chứng

- **proof_a (WSL FD-2026-M48)**: 3 nguồn không rỗng — scoreboard_status
  (event 401902884, "Sat, October 24th at 12:15 PM EDT"), gamma_event
  (`?id=1212928`, đúng title Brighton/West Ham), league_official
  (wslfootball, `team_name_hit=yes`). Đối chứng sống: cả 3 URL trả đúng
  nội dung proof. **≥1 nguồn Gamma/chính thức: ĐẠT**.
- **proof_b (NBA 401909093)**: 7 trích dẫn chấn thương thật qua đường
  `$ref` 1-hop, journal đủ ("cap 1" từng hop, team=20 items=4, team=5
  items=3); gamma skip trung thực vì chạy standalone; `athlete` vẫn là
  `$ref` được báo cáo thừa nhận trung thực không vượt trần. **ĐẠT**.
- **f7_injury_delay.json**: nhất quán nội tại 100% khi kiểm toán tự
  tính lại. **ĐẠT**.

## 6. FINDINGS

- **MED-1**: hop `$ref` (F2) fetch URL do payload cung cấp mà KHÔNG kiểm
  host allow-list (`ai_research.py:288-290`). Dữ liệu thật chỉ chứa host
  ESPN (proof_b xác nhận), nhưng một bare-`$ref` trỏ host lạ sẽ bị
  fetch — lỗ hổng latent đối với luật host đóng. Khuyến nghị: chặn
  hostname hop phải thuộc espn.com.
- **MED-2**: transport (`urlopen`) tự theo redirect mà không kiểm lại
  host cuối. Sống: `wslfootball.com/fixtures/` 302 → `www.wslfootball.com`
  (cùng domain, vô hại hôm nay, đã xác minh), nhưng cơ chế này có thể bị
  chuyển hướng ra ngoài allow-list mà không phát hiện. Cùng họ với
  MED-1 — nên kiểm lại host đích sau redirect/hop.
- **LOW-1**: `published_utc` bị lỗi định dạng "ZZ" trong citation F2
  đã-resolve (proof_b: `"2026-10-21T21:07ZZ"`) — `[:19]` giữ chữ Z cuối
  của timestamp ESPN không-giây rồi lại cộng thêm "Z"
  (`ai_research.py:318-323`). Chỉ pass-through xuống stream, không ai
  parse — lỗi provenance, không gãy gate.
- **LOW-2**: `f7_injury_delay.json`: tên trường
  `delay_hours_negative_is_early` NGƯỢC dấu với dữ liệu — cả 67 giá trị
  đều = anchor − timestamp (dương = sớm). File chỉ-số, không đụng luật,
  nhưng tên trường gây hiểu nhầm người đọc sau.
- **INFO-1**: tuyên bố "316/316 ×2 lần" không có artifact lưu đĩa;
  kiểm toán xác nhận 1 lần chạy xanh 316/316.
- **INFO-2**: báo cáo trỏ tới `A7_COLLECTOR_FIX_VERDICT_2026-10-22.md`
  chưa tồn tại trên đĩa (verdict này được nộp bằng tin nhắn theo lệnh
  owner) — file bạn đang đọc chính là bản ghi verdict đó.
- **INFO-3**: hai chỗ văn bản báo cáo lỏng: "28 đội" (rows chỉ mang 24
  đội khác nhau — 4/28 đội có 0 item đo được, file tự ghi
  `teams_queried=28`); "(22–26/10)" (kickoff của cả 14 game đều rơi
  22–24/10).
- **INFO-4**: thẩm mỹ — `ops_service.py:1534` có dòng dính whitespace,
  chạy đúng.
- **INFO-5**: lane SOCCER generic vẫn chết (chủ đích hoãn, cần crosswalk
  giải→slug) — production lane đó sẽ vẫn từ chối "insufficient evidence"
  (từ chối trung thực, không phê duyệt sai) cho đến chu trình riêng.

## 7. VERDICT

**PASS_WITH_FINDINGS** — CRITICAL: 0 | HIGH: 0 | MED: 2 | LOW: 2 |
INFO: 5.

Cả 7 mục F1–F7 đúng kế hoạch; CẤM ĐỤNG không bị vi phạm (không config,
không prompt, không anchor/stake/cascade, shadow=false nguyên vẹn);
battery 316/316 xanh do kiểm toán tự chạy; 3 proof sống được đối chứng
mạng thật khớp. Hai MED là lỗ hổng latent về kiểm-soát-host ở hop `$ref`
và redirect (không bị khai thác trong bằng chứng hiện có) — nên xử lý
trong chu trình kế tiếp, **KHÔNG chặn adoption trên các finding này**.
DỪNG TRƯỚC MERGE được tôn trọng: branch chưa merge vào main.
