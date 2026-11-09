# BIÊN BẢN TẠM DỪNG WORKER WSL — 2026-11-06 03:29Z

Căn cứ: QUYET_DINH_BO_SUNG_CAP_2026-11-06.md (sha256 b11e2172d065e9fec85a9d9f1f0c8f7a00afdce711c700f821099b6f7f9d9e0) mục "TẠM DỪNG worker WSL ngay tới 00:00 ICT 07/11".

## Cơ chế đã dùng (không giết tiến trình, không sửa code)

- Thêm mục `league_pauses.WSL = {active: true, ...}` vào `research/papertrade_exec/config.json` (checkout chính — đúng cây mà runner pid 35523 đang chạy, cwd root).
- Đây là cơ chế PAUSE THIẾT KẾ SẴN của chính lane (luật QD1/A7-M2, `execute.py::league_paused`, kiểm tra đứng TRƯỚC mọi lane dispatch trên đường REAL — "no lane is above an owner pause"). `load_config()` đọc file mỗi lần gọi → hiệu lực từ lần dispatch kế tiếp, KHÔNG restart service.
- Hiệu ứng: lane WSL từ chối dispatch mới (kèm cả fetch gamma `tag_id=105959` — nguồn ~93 request/ngày); settle + dashboard vẫn chạy theo luật QD1. Các giải khác (NBA, SOCCER…) không bị đụng (đã verify `league_paused('NBA')` = None).
- File `config.json` trước sửa: sha256 `8617d43ee11acc453b90d6bb21ad3d6554cccc704ef2799280733c6cd6e3b125`, git-clean. Sau sửa: JSON validate OK + `league_paused('WSL')` trả đúng pause record (chạy bằng `.venv/bin/python` import code thật).

## Bằng chứng xác nhận (cập nhật sau khi qua mốc nhịp cũ)

- Fetch WSL cuối trước pause: 03:23:03Z (journal_wsl_lane_2026-11-06T032303Z). Theo nhịp cũ ~15,5 phút, fetch kế dự kiến ~03:38:33Z. Nếu pause hoạt động: KHÔNG có file journal mới sau mốc này.
- [Cập nhật 03:41Z — xem mục "Kết quả xác nhận" dưới.]

## Kết quả xác nhận (đo thực nghiệm, 03:57:23Z)

**Lớp 1 — `league_pauses.WSL.active=true` (đặt 03:29:32Z): KHÔNG ĐỦ.** Fetch 03:38:04Z vẫn xảy ra. Nguyên nhân đo được: cổng `league_paused()` chỉ đứng trong `cmd_decide`; còn fetch gamma nằm trong **wiring quote** (`maybe_wsl()` → `_wire_wsl_real_quote()`) chạy trên đường `cmd_quote` — TRƯỚC cổng pause. Đúng 1 request lọt (ghi nhận trung thực; tổng WSL ngày Saigon 06/11 dừng ở 42).

**Lớp 2 — xóa `sport_keys.WSL` khỏi config (03:42:20Z): CHẶN ĐƯỢC, xác nhận thực nghiệm:**
- Verify qua code production (`.venv/bin/python`, import thật): `wsl_configured()` = False; `_cadence_leagues()` = ('NBA','WNBA','SOCCER','NCAA-M','NCAA-W') — WSL bị loại khỏi cadence (đúng thiết kế CAPITAL-V3 §4: "WSL joins the cadence ONLY when the committed config registers sport_keys.WSL"); `maybe_wsl()` giờ BLOCKED_LEAGUE ngay đầu — không còn đường wiring/fetch.
- Heartbeat service: tick 03:51:58Z và 03:57:21Z (sau lớp 2) — cadence KHÔNG còn WSL, cùng pid 35523 (KHÔNG restart service, config đọc live).
- Journal: fetch WSL cuối = **03:38:04Z**; qua đúng mốc lần thử kế theo throttle 900s (~03:53:04Z) → KHÔNG có file journal mới. WSL dừng hẳn từ 03:42:20Z.

**Tổng kết ngày Saigon 06/11 (chốt):** Việc 3 = 172, WSL = 42 (27 tối 05/11 + 15 sáng 06/11), lane ví pro = 0 → tổng 214/200 (vượt 14; fetch 03:23:03Z và 03:38:04Z xảy ra trước khi quyết định bổ sung tới tay tôi; mọi dòng sau 03:42:20Z = 0).

**Khôi phục (reversible) — làm ĐÚNG THỨ TỰ:**
1. Đưa nhịp 30 phút lên trước (mục "Việc còn treo").
2. Thêm lại `"WSL": "wsl_polymarket_gamma"` vào `sport_keys` (giá trị gốc ghi ở đây + git diff).
3. Đặt `league_pauses.WSL.active` = false hoặc xóa mục.
4. Verify: fetch đầu theo nhịp mới + đếm ≤50/ngày.

## CẬP NHẬT 04:57Z 06/11 — NHỊP 30 PHÚT ĐÃ LÊN, VERIFY ĐẠT, COMMIT XONG, RE-PAUSE TỚI 00:00 ICT

Chủ duyệt (qua coordinator): tôi được sửa `ops_service.py` thêm throttle riêng WSL 1800s (giải khác giữ 900s), restart, verify, commit chung.

**Đã làm:**
1. Code: thêm `WSL_CADENCE_THROTTLE_S = 1800` + nhánh điều kiện tại chỗ dùng duy nhất (dòng 1047), theo đúng khuôn điều kiện per-league sẵn có của settle SOCCER. Diff: +7/−1, không đụng gì khác.
2. Khởi động lại runner: phát hiện launchd job `com.myquant.sptexec.ops` bị bootout từ takeover 19/10 (takeover.json: "runner lifecycle now follows the app") — runner 35523 là external-spawn (Nov 4, cwd root checkout), app chỉ ATTACH không respawn → kickstart vô hiệu. Đã làm đúng dạng: `kill -TERM 35523` (thoát sạch, nhả khóa sau 2s) → start lại `nohup .venv/bin/python -m research.papertrade_exec.ops_service` cwd root checkout (pid **17524**, lstart 04:23:00Z, khóa HELD, heartbeat pid 17524 tick 04:23:19Z). Log: `/tmp/paperdesk_service_main_2026-11-06.log`.
3. **Verify 3 kiểm của chủ — ĐẠT, bằng chứng thực nghiệm:**
   - WSL ~30 phút: fetch 04:23:16Z → **04:53:44Z** (gap 30m28s = 1800s + tick); mốc phân biệt **04:38:16Z đã qua mà KHÔNG có fetch** (code cũ 900s lẽ ra fetch tại đó); tick 04:55:28Z lại THROTTLED.
   - Giải khác không đổi: NBA plan refresh 04:23:09Z → 04:38:25Z (giữ 900s); diff chỉ thêm nhánh WSL.
   - Journal có file mới: `journal_wsl_lane_2026-11-06T045344Z.jsonl`.
4. Commit `73351c97` trên main (config.json + ops_service.py, +14/−1), KHÔNG push. Lưu ý nhỏ: git dùng identity tự cấu hình theo máy (`Hoang Minh Long <hoangminhlong@192.168.0.9>`).
5. **Re-pause tới 00:00 ICT 07/11** (quyết định bổ sung còn hiệu lực; câu deadline của chủ "để automation gỡ pause đúng giờ"): xóa tạm `sport_keys.WSL` khỏi config LIVE (delta chưa commit — đúng mô hình pause sáng nay; automation 17:00Z sẽ re-add → trở lại đúng trạng thái đã commit). WSL fetch cuối: 04:53:44Z.

**Khai báo request trong quá trình verify (3 fetch WSL, theo lệnh kiểm tra của chủ):**
- 04:21:35Z — tiến trình CŨ, nhịp 900s (cửa sổ đua giữa config-restore 04:21:23 và TERM — đã lường trước, 1 request).
- 04:23:16Z — tiến trình mới, tick đầu.
- 04:53:44Z — fetch theo biên 1800s (chính là bằng chứng "journal có file mới").
Tổng WSL ngày Saigon 06/11 chốt: **45** (27 + 18). Tổng cả ngày: 172 + 45 + 0 = **217/200**. Không còn request nào của WSL sau 04:53:44Z.

## Việc còn treo cho 07/11 (00:00 ICT = 17:00Z 06/11)

1. Đổi nhịp WSL ~15,5 phút → ~30 phút: nhịp nằm ở hằng số code `CADENCE_THROTTLE_S = 900` trong `research/papertrade_exec/ops_service.py` — DÙNG CHUNG mọi giải. Đổi riêng WSL = sửa code (throttle per-league, ví dụ WSL 1800 / mặc định 900) + restart ops service (KeepAlive, `launchctl kickstart -k gui/$UID/com.myquant.sptexec.ops`). Sửa code production lane khác → cần chủ chỉ định người làm (coordinator hay tôi).
2. Gỡ pause (`active: false` hoặc xóa mục WSL) CHỈ SAU khi nhịp 30 phút có hiệu lực — nếu không, gỡ pause sẽ trả WSL về ~93 request/ngày, phá bổ trần 50/ngày của quyết định.
3. Lưu ý rủi ro đã cân nhắc trong quyết định: giữ pause lâu hơn 00:00 ICT sẽ chặn lane WSL vào đúng đầu tuần trận (07–08/11) — cần nhịp mới lên kịp TRƯỚC khung anchor trận.

## RESUME 00:00 ICT 07/11 (17:00Z 06/11) — automation thi hành, XONG

1. Kiểm điều kiện: `WSL_CADENCE_THROTTLE_S = 1800` có mặt (commit 73351c97), runner pid 17524 (khởi động 04:23Z 06/11, cwd root checkout) đang chạy code mới → điều kiện nhịp 30 phút ĐÃ có hiệu lực.
2. Gỡ pause: re-add `"WSL": "wsl_polymarket_gamma"` vào sport_keys lúc **17:01:02Z**; `league_pauses.WSL.active` đã false từ commit. Verify code path: `wsl_configured()`=True, `_cadence_leagues()` có WSL. Config live khớp lại byte-đối-byte commit 73351c97 (git sạch).
3. **Bằng chứng nhịp ~30 phút sau resume (ngày Saigon 07/11):**
   - Fetch #1: **17:01:20Z** (= 00:01:20 ICT 07/11, tick đầu sau gỡ pause).
   - Mốc code-cũ 17:16:20 (T+900s) qua sạch — kiểm lúc 17:14:00 và 17:23:28: THROTTLED, không fetch.
   - Fetch #2: **17:31:42Z** (biên eligible 17:31:20 + tick đầu). Gap = **30 phút 22 giây**.
   - Đếm WSL ngày Saigon 07/11: 2/50 trở đi (nhịp 30 phút ≈ tối đa ~48/ngày).
4. Việc 3 (kiểm song song): commit cuối 02d8f3f + interim FINAL 06/11 — listing CHƯA XONG, "chờ GO 07/11" (GO 150/ngày đã có trong quyết định bổ sung; phiên Việc 3 chưa chạy đêm 07/11 tại thời điểm kiểm 00:33 ICT).
5. Cửa GĐ4 lane ví pro: VẪN ĐÓNG (điều kiện "interim Việc 3 ghi XONG" chưa đạt). Khi mở: pro ≤120/ngày, WSL ≤50/ngày, tổng ≤200, ngày Saigon, đếm 3 nguồn trước mỗi phiên.
