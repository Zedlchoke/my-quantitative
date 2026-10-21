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
