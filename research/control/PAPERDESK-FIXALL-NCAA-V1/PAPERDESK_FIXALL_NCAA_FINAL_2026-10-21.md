# PAPERDESK FIX-ALL + NCAA — BÁO CÁO TỔNG KẾT (PAPERDESK-FIXALL-NCAA-V1)

> **Ngày:** 2026-10-21 · **Lane:** worktree
> `.worktrees/paperdesk-fixall-ncaa-v1/integration` · branch
> `orca/paperdesk-fixall-ncaa-v1-integration` · **HEAD cuối: `6b7a60f5`**
> (10 commit từ base `11da8071`; KHÔNG push, KHÔNG merge).
> **Gói việc:** `plans/PLAN_paperdesk_fixall_ncaa_v1.md` (owner, qua Muse).
> **A7 độc lập (fresh context, hai vòng):** vòng 1 tại `e071c0da` =
> PASS_WITH_FINDINGS 0 CRITICAL / 0 HIGH / 3 MED / 4 LOW → sửa cả 3 MED →
> vòng delta tại `af40456f` = **PASS_WITH_FINDINGS 0 CRITICAL / 0 HIGH /
> 0 MED / 6 LOW — CỔNG GÓI ĐÃ ĐẠT**; 2 LOW mới phát hiện đã sửa tiếp tại
> `6b7a60f5`. Artifacts: `A7_FINAL_VERDICT_FIXALL.md`,
> `A7_FINAL_EVIDENCE.json`.
> **Test:** Python battery **206/206 × 2 lần chạy liên tiếp** ở HEAD cuối;
> JS batteries xanh (ai-gate 17/17, seam 43/43, policy 27/27, chart
> lifecycle).
> **Các cấm luật giữ nguyên:** `pm_cutover_active = false`,
> `ai_authority_active = false` (config), `LiveExecution` vẫn SEALED
> (submit() ném lỗi — đã verify), ledger production vẫn đúng **82 dòng**
> (không một chữ nào bị ghi), branch không có upstream (không push).

## Trạng thái production tại thời điểm bàn giao (để owner biết chính xác)

- Runner paper **vẫn đang chạy code CŨ** (PID 10000, worktree
  `sports-papertrade-exec-v1/integration`) — gói này không được phép chạm
  lane đang chạy. **Mọi sửa chỉ có hiệu lực trên sổ thật sau khi owner áp
  HEAD `6b7a60f5` vào runner production** (restart runner từ worktree mới
  hoặc hợp nhất branch — là hành động của owner).
- 2 lệnh NBA kẹt (401909088, 401909090) **chưa chốt trên sổ thật** —
  chúng sẽ tự chốt qua đường settle thường ngay khi runner mới chạy lần
  đầu (nghiệm thu W0 đã replay đúng 2 lệnh này trên BẢN SAO ledger bằng
  chính payload ESPN đã journal: 401909088 WIN +1.180c, 401909090 LOSE
  −1.135c, chain OK — `evidence/W0_ACCEPTANCE_REPLAY_2026-10-21.json`).

## Trả lời 3 câu CHO TỪNG W

### W0 — Sửa đường chốt sổ
1. **Đúng spec chưa:** ĐÚNG. W0.1 crosswalk ghim sha (30 NBA + 15 WNBA,
   đo từ payload thật; fail-closed tên lạ); 3 hàm `_norm` gom một nguồn;
   identity settle qua `same_team`. W0.2 requeue mỗi tick +
   `settle_attempts.jsonl`. W0.3 alarm +6h / dead-letter +48h / dọn
   settle_last_why / resolve-stuck có token owner qua đường settle chuẩn.
   W0.4 WSL DRAW = event-pair + market id. W0.5 soccer VOID sau
   kickoff+grace ngoài stage-law. W0.6 cửa sổ [D−1, D+2] + hoãn/huỷ cấu
   trúc + rescheduled.
2. **Đã cố hết chưa:** CÓ — nghiệm thu replay 2 lệnh kẹt thật PASS.
3. **Dở dang:** Việc chốt 2 lệnh NBA + dọn 6 "ma" trên MÁY THẬT chờ owner
   áp HEAD vào runner (lý do: không được chạm lane production).

### W1 — Ngừng đốt công + chốt chặn dữ liệu sai
1. **Đúng spec:** ĐÚNG. W1.1 key 404 poll ≤1 lần/ngày (trước ~230–280/ngày);
   W1.2 quota theo ĐƠN VỊ NHÀ CUNG CẤP (2 credit/basketball odds call — đo
   thật) + journal meter + báo drift; W1.3 **nguyên nhân gốc truy tận
   gốc**: refresh lookback=0 ⇒ corpus 0 trận FINAL ⇒ mọi đội R0=1500 ⇒ p
   thuần HCA 0.640065 (đúng bằng 1/(1+10^(−100/400))) — engine đúng, lỗi ở
   caller; sửa lookback 14 ngày + chốt chặn vĩnh viễn
   `BLOCKED_CONSTANT_FORECAST`; W1.4 chặn quote trùng 2 decide paths;
   W1.5 cách ly EV >100% + cross-check nguồn 2; W1.6 `laws.py` + JS sinh
   ra + parity; W1.7 storm-collapse, DASHBOARD_REBUILT → metrics,
   pause-watch hết giả RESUMED, fail-fast pin thiếu, root cause 26 lần
   start ngày 10-19 = app relaunch churn (đã ghi handover).
2. **Đã cố hết:** CÓ (battery gồm test cho từng mục).
3. **Dở dang:** Gỡ tạm dừng NBA (QĐ1) là hành động owner: cần 1 mẻ NBA
   forecast variance>0 trên runner production (đã có law
   `league_pauses.NBA` chặn lệnh mới real-plane + `lift_requires` ghi rõ).

### W2 — Tốc độ + một dashboard
1. **Đúng spec:** ĐÚNG. W2.1 đọc ledger tăng dần 2 phía (Python view +
   JS ledger.js) với parity test; W2.2 cadence song song theo giải
   (settle vẫn trước, retry tail-drift idempotent); W2.3 MỘT mặt hiển thị
   (Electron; trang HTML đã xoá, `/api/state` là state API duy nhất);
   W2.4 đủ 4 khối + CLV capture (plane append-only, luật giá đóng = quote
   gần kickoff nhất, NO_CLOSE_PRICE trung thực).
2. **Đã cố hết:** CÓ (kể cả 2 bug thật battery bắt: nhả khoá theo GC,
   `_upcoming_cache` chưa init).
3. **Dở dang:** Không có. CLV lịch sử chỉ tính từ lúc lane chạy (không
   thể hồi phục quá khứ — đã ghi luật).

### W3 — Chuyển nguồn giá PM (tới cổng GO)
1. **Đúng spec:** ĐÚNG. W3.1 luật phí một nguồn (trong laws.py);
   W3.2 battery đầy đủ + live probe read-only ĐẠT (NBA join 2 tên thật →
   event 1191461, CLOB 28 mức; WSL tag scan) → readiness note.
2. **Đã cố hết:** CÓ.
3. **Dở dang:** W3.3 là việc SAU-GO theo thiết kế. Cờ vẫn false.

### W4 — Cổng AI duy nhất
1. **Đúng spec:** ĐÚNG. W4.1 một cổng cả 2 decide paths (WSL vào cổng;
   legacy đánh dấu UNWIRED, battery cấm decide gọi); W4.2 hash-lock;
   W4.3 collector research thật + schema cứng ALLOW|VETO (SWITCH/
   CHALLENGE/ALTERNATIVE cắt khỏi đường có quyền); W4.4 luật im lặng
   PENDING_AI → NO_VERDICT quá hạn + alarm provider >30 phút; W4.5
   scorecard tuần + dashboard + đề xuất giáng cấp (chỉ đề xuất); W4.6
   model qua config + prompt V2 đóng băng sha; W4.7 battery trước —
   ĐẠT. Doc `AI_PIPELINE_DESIGN_V1.md` đã sửa đoạn hàm không tồn tại.
2. **Đã cố hết:** CÓ.
3. **Dở dang:** GO AI authority là câu riêng của owner. Điểm A7 nêu rõ:
   khi bật, cần producer v2 (JS) chạy trong app để sinh opinion.

### W5 — NCAA (NCAA-M / NCAA-W)
1. **Đúng spec:** ĐÚNG. W5.1 đủ điểm chạm; W5.2 adapter ESPN + identity
   norm từ ngày đầu; W5.3 state store ĐÓNG BĂNG (oracle = bản chép độc
   lập walk_forward intake, khớp ≤1e-9; replay bit-identical; GBM refit
   artifact ghim; không sklearn ⇒ rơi Elo đóng băng trung thực); W5.4
   PM-always + anchor batch/tournament; W5.5 nhãn sự thật NGUYÊN VĂN
   (A7 đối chiếu 178/178 ký tự) + log-loss/Brier vs PM; W5.6 mặc định
   TẮT.
2. **Đã cố hết:** CÓ, với 2 hạn chế ĐÃ KHAI BÁO (bootstrap SEASON_ONLY;
   feature conf_game=0 khi feed thiếu conference id).
3. **Dở dang:** Lane sống chờ mùa 2026-27 (bắt đầu 11/11); lần
   `ncaa-refresh-state` đầu chạy khi có trận final đầu mùa.

### W6 — LIVE_READINESS
1–3. ĐÚNG và ĐỦ theo phạm vi "chỉ hồ sơ": `LIVE_READINESS.md` liệt kê đủ
10 mảnh thiếu + điều kiện tiên quyết (trong đó có "A7 audit độc lập
RIÊNG cho tầng thực thi"). Không code, không ví.

## Việc owner cần quyết/làm sau báo cáo này

1. **Áp HEAD `6b7a60f5` vào runner production** (restart từ worktree
   mới) → W0 tự chốt 2 lệnh NBA kẹt, dọn ma settle_last_why; các chốt
   chặn W1 active.
2. **Gỡ tạm dừng NBA (QĐ1):** sau khi thấy 1 mẻ NBA forecast
   variance>0 trên runner thật (journal `CADENCE_FORECAST_OK` + không còn
   BLOCKED_CONSTANT_FORECAST) → sửa config `league_pauses.NBA.active=false`
   (commit có nhật ký).
3. **2 câu GO (đọc note tương ứng, tự gõ riêng):**
   - GO cutover giá PM → `CUTOVER_READINESS_NOTE_2026-10-21.md`.
   - GO quyền AI → `AI_AUTHORITY_READINESS` trong mục W4 (đủ battery;
     bật cờ chỉ sau khi đọc + tự gõ GO).
4. LIVE: chỉ tiến nếu muốn — chu trình riêng, không phải lật cờ của gói
   paper (`LIVE_READINESS.md`).

## Danh sách bằng chứng chính (thư mục chu trình
`research/control/PAPERDESK-FIXALL-NCAA-V1/`)

`A7_FINAL_VERDICT_FIXALL.md` + `A7_FINAL_EVIDENCE.json` (2 vòng audit) ·
`evidence/W0_ACCEPTANCE_REPLAY_2026-10-21.json` (2 lệnh kẹt chốt qua đường
thường trên bản sao) · `evidence/PM_LIVE_PROBE_FIXALL_2026-10-21.json` ·
`CUTOVER_READINESS_NOTE_2026-10-21.md` · `LIVE_READINESS.md` ·
`HANDOVER_W0..W5_2026-10-21.md` · RUNBOOK `apps/paperdesk/RUNBOOK.md`
§8–§12.

## Điều KHÔNG làm (đúng luật gói)

Không tự gõ/tiêu thụ bất kỳ câu GO nào · không bật 2 cờ · không phá seal ·
không sửa tay ledger production (vẫn 82 dòng) · không push/merge · không
đổi ngưỡng EV/stake/cap/hằng số mô hình (chỉ gom nguồn) · không đụng
runner đang chạy.
