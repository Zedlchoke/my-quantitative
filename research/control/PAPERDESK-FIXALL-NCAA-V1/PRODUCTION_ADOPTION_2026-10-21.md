# PRODUCTION ADOPTION — runner chuyển sang HEAD của gói FIXALL+ NCAA

> Thực hiện 2026-10-21 theo lệnh owner (không GO mới, không bật cờ, không
> gỡ tạm dừng NBA). Chain: `12daf647` (áp) → `81860c64` (hotfix W0.6
> ET-slippage, sinh trong khi tiếp nhận).

## Dòng thời gian (UTC)

| Thời điểm | Sự kiện |
|---|---|
| 11:16:32 | Runner cũ (code trước gói, pid 10000) SERVICE_STOP sạch |
| 11:18:13 | Runner mới START từ worktree `paperdesk-fixall-ncaa-v1` @ `12daf647` (pid 80981) |
| 11:18:23 | Plane W0.3 bấm còi ngay tick đầu: SETTLE_STUCK_ALARM ×2 (đúng 2 lệnh kẹt) |
| 11:36:50 | **401909088 DET–BOS CHỐT: WIN +1.180c** (đường settle thường) |
| 11:37:24 | 401909090 bị giữ OPEN bởi luật W0.6 — FALSE POSITIVE: trận tip 01:30Z ngày D nằm ở board D−1 (ngày ET) = trượt múi giờ bình thường, KHÔNG phải reschedule |
| ~11:45 | Hotfix `81860c64`: rescheduled chỉ tính board D+1/D+2 (forward); battery 207/207 ×2 |
| 11:46:09 | Runner restart trên hotfix (pid 85142) |
| 12:07:43 | **401909090 SA–OKC CHỐT: LOSE −1.135c** (đường settle thường) |
| 12:08:54 | **Mẻ forecast NBA đầu tiên** (forecast --league NBA --date 2026-10-22, lệnh cadence sẽ chạy): refresh lookback 14 fetch board mới → 2 FORECAST rows, **2 distinct p** (0.6415/0.3585 và 0.6286/0.3714) — **KHÔNG còn hằng số**, không BLOCKED_CONSTANT_FORECAST |
| 12:09+ | Decide mẻ này bị chặn DUY NHẤT bởi `BLOCKED_LEAGUE_PAUSED` (QĐ1 — chờ owner gỡ sau khi thấy mẻ variance>0, điều kiện đã ĐẠT) |

## Sổ sách sau tiếp nhận

- Ledger: **86 dòng** (82 + 2 SETTLEMENT + 2 FORECAST), chain OK.
- Equity: 100.000 + 13.495 + 1.180 − 1.135 = **113.540c** (khớp tờ tính).
- Open bets còn lại: 401909836 (BKN–CHA, tip 23:30Z hôm nay).
- settle_last_why.json: đã dọn sạch ghost (0 entries; prune-at-settle chỉ
  dọn mục của lệnh vừa chốt nên các "ma" WSL từ 20/10 được dọn tay một
  lần — state plane, không đụng ledger).

## Hai lệnh kẹt — TRẢ LỜI

| Lệnh | Trận | Kết quả chốt | PnL |
|---|---|---|---|
| 401909088 | DET vs BOS | WIN (HOME 121–113) | +1.180c |
| 401909090 | SA vs OKC | LOSE (AWAY 116–104) | −1.135c |

Cả hai chốt TỰ ĐỘNG qua đường settle bình thường (không sửa tay ledger).

## NBA constant-forecast — TRẢ LỜI

KHÔNG còn. Mẻ forecast đầu tiên sau tiếp nhận có 2 xác suất KHÁC nhau
trên 2 trận (root cause: corpus trước giờ chỉ chứa snapshot SCHEDULED —
refresh lookback 14 ngày đã fetch board có FINAL; dry-run trước sửa cho
thấy 0 FINAL — bây giờ engine thấy trận final). Điều kiện gỡ pause QĐ1
("một mẻ NBA forecast variance > 0") ĐÃ ĐẠT — việc gỡ là hành động owner
(config `league_pauses.NBA.active=false`, commit có nhật ký).

## Lưu ý vận hành

- Runner đang chạy: pid 85142 từ worktree `paperdesk-fixall-ncaa-v1`
  (log: `ops/runner_fixall_ncaa.log`). App Electron PaperDesk KHÔNG chạy
  lúc tiếp nhận (đã tắt từ trước) — mở lại app build cũ sẽ ATTACH vào
  runner mới (attach-by-data-root); muốn app có code mới thì rebuild từ
  worktree này (việc sau, không khẩn).
- Forecast/quote slate 22/10 sẽ do cadence tự hoàn tất vào cửa sổ
  (từ ~16:50Z hôm nay); decide sẽ hiện BLOCKED_LEAGUE_PAUSED cho tới khi
  owner gỡ pause.

## QĐ1 LIFT — 2026-10-21 (owner order)

`league_pauses.NBA.active → false` (commit này). Điều kiện gỡ đã ghi lúc
đặt pause ("một mẻ NBA forecast variance > 0 trên production runner") ĐÃ
ĐẠT: ledger rows 85–86 — 401909093 PHI–CLE 0.6415029/0.3584971 vs
401909094 OKC–DEN 0.6286384/0.3713616 (2 distinct vectors; hằng số cũ
0.640065/0.359935). Runner pid 85142 đọc config từ đĩa mỗi lần decide —
lift có hiệu lực NGAY, không cần restart. NBA decide quay lại dưới toàn
bộ cổng deterministic không đổi (EV≥5%, PIT, stake, cap) + cổng AI v2
khi owner gõ GO riêng. Battery 207/207 ×2 (3 test NBA "frozen-era" cập
nhật thành age-independent theo luật refresh-manifest — corpus GIỮA được
lớp hóa là hành vi đúng của W1.3; law-pause test chuyển sang synthetic
config).

## OWNER GOs CONSUMED — 2026-10-21 ~12:53Z

Owner gõ trực tiếp 2 câu GO (verbatim): `GO SPORTS PAPERTRADE EXEC V1
POLYMARKET CUTOVER` + `GO SPORTS PAPERTRADE EXEC V1 AI AUTHORITY`. Agent
CHÉP (transcribe) — không tự đặt câu — vào `GO_TOKEN_CUTOVER.json` /
`GO_TOKEN_AI_AUTHORITY.json` (provenance đầy đủ), registry phase ghi
`EXEC_CUTOVER_GO_CONSUMED` + `EXEC_AI_AUTHORITY_GO_CONSUMED` (worktree +
root master). Commit `52973f17`:

- **Cổng 2 chìa (real mode):** cờ config + token verbatim + registry
  marker — thiếu 1 trong 3 là OFF, fail-closed. SANDBOX mặc định pre-GO,
  chỉ lật bằng control copy riêng → battery vẫn tập luyện đúng đường.
- **2 cờ config → true.** Runner restart lên code GO (pid mới) — verify
  `papertrade_flags(sandbox=False)` = ON cả hai qua token plane.
- **Headless AI producer** (`ai_producer.py`) vào tick của runner: quy
  trình quyền AI vận hành KHÔNG cần app Electron — pending → evidence →
  provider (model theo config, key Keychain đọc tại chỗ) → schema cứng
  ALLOW|VETO → opinion khóa-hash. Provider lỗi = sự kiện trung thực (lệnh
  chờ, không ai bị giết). Keychain key xác nhận đọc được headless.
- Kỳ vọng vận hành từ nay: quote PM là nguồn quyết định (fail-closed
  NOT_RUN_PM_QUOTE khi PM chưa niêm yết — soccer quốc tế vẫn(case-by-case));
  lệnh BET mới phải có opinion AI khóa-hash trước khi vào sổ; 48h đầu theo
  dõi theo kế hoạch trong CUTOVER_READINESS_NOTE (quote thành công %,
  NOT_RUN_PM_QUOTE, EV hai nguồn, CLV).
