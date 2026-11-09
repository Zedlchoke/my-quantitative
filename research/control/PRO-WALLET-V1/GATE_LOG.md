# GATE LOG — PRO-WALLET-V1 (agent chính ghi sau mỗi cửa)

Quy ước: mỗi cửa ghi điều kiện kiểm (file tồn tại / hash khớp / câu bắt buộc có) + kết luận MỞ/ĐÓNG cửa tiếp theo.

## Cửa Bước 0 — PASS (2026-11-05)

- Clone `Zedlchoke/edge-hunt-ai-desk` về `.my-quantitative-data/PRO-WALLET-V1/input-edge-hunt-ai-desk`, checkout detach `10d3eb7ff9495b2c5b309e9a05ff889f79ca3d80` — HEAD đúng.
- `shasum -a 256 -c MANIFEST.sha256`: 57/57 OK, 0 lệch.
- Hash pack: ke-hoach `6196d282…` ✓, spec D2 `06e204d2…` ✓, mẫu kiểm toán `8eaaaa5e…` ✓. Spec copytrade v2 FILE: `ae504a97…bee55d8` ✓ (pin theo FILE).
- Ghi chú đọc: `BUOC0_DOC_TRUOC.md`, sha256 `1c9db6a7bfd37821b1616dbb473122b491c7f5f884f0cdcbc885192a15d790bb`, sidecar OK.
- Kết luận: MỞ Giai đoạn 1.

## Cửa Giai đoạn 1 (RESEARCHER) — PASS (2026-11-05, sau errata)

- File `NGHIEN_CUU_GIAI_DOAN1.md` tồn tại; sha256 sau errata `61b6f68e6bef008fe11e2687f0235013008e6263900ecb0fffd0909648468f17`, sidecar `shasum -c` OK.
- Câu bắt buộc cuối file: CÓ, đúng hình thức.
- Handoff `handoffs/HANDOFF_GD1_RESEARCHER.json`: schema `zcode_orch_v3_handoff@1`, JSON hợp lệ, có trường errata.
- Lỗi dispatcher đã xử lý: agent chính giao sai đường dẫn cutover-prep (trong repo thay vì cấp HOME) → RESEARCHER xuất errata, WSL đổi kết luận THIẾU → ĐỦ kênh dữ liệu. Các mục cũ giữ nguyên làm bằng chứng.
- Kết luận nội dung: NBA, bóng đá nam, WSL = ĐỦ kênh dữ liệu; WNBA (nghỉ mùa), NCAA nam, NCAA nữ = THIẾU DỮ LIỆU thị trường trên đĩa. 0 request API Polymarket tiêu tốn.
- Phát hiện vận hành gửi tiếp GĐ2: trần 200/ngày cộng dồn đang bị tiêu bởi Việc 3 (200/200 mỗi ngày, còn ~3 ngày) VÀ worker WSL lane (22 request Gamma hôm nay, còn sống).
- Kết luận: MỞ Giai đoạn 2.

## Cửa Giai đoạn 2 (PLANNER) — PASS (2026-11-05)

- File `KE_HOACH_V2.md` tồn tại (273 dòng, 11 mục + mục 0); sha256 `61188913b9e0bb8b9a176807a65b35a07ce12c5c0c413c781e4db7d1710c5d59`, sidecar `shasum -c` OK.
- Câu bắt buộc cuối file: CÓ, đúng hình thức.
- Handoff `handoffs/HANDOFF_GD2_PLANNER.json`: schema `zcode_orch_v3_handoff@1`, JSON hợp lệ, status DONE.
- Kế hoạch gốc không bị sửa (file input giữ nguyên sha 6196d282…).
- Điểm nội dung chính: NBA/bóng đá nam/WSL vào phạm vi; WNBA + NCAA nam/nữ ngoài vì THIẾU DỮ LIỆU (điều kiện bổ sung phải qua bản sửa + kiểm toán); mọi ngưỡng dán nhãn "SỐ ĐỀ XUẤT — chờ chủ chốt"; sổ bóng append-only tách sổ D2; xếp hàng request sau Việc 3 + đếm chung worker WSL.
- Kết luận: MỞ Giai đoạn 3 (AUDITOR-1 độc lập).

## Cửa Giai đoạn 3 (AUDITOR-1) — PASS, verdict CONFIRMED (2026-11-05)

- File `AUDIT_KE_HOACH_V2.md` tồn tại (33.130 byte); sha256 `5bc89e44f04f391670d9df41ec482f024843824acbd7cd459b9946b8c853a2f6`, sidecar `shasum -c` OK.
- Verdict 1 dòng đầu file: **CONFIRMED** (đối tượng là bản kế hoạch chưa chạy; 22/22 luật khớp; không rò rỉ tương lai; tính lại độc lập khớp 2/3 phần chính, 1 lệch nhỏ dòng mô tả ngân sách — không đổi verdict).
- Câu bắt buộc cuối file: CÓ. Handoff `handoffs/HANDOFF_GD3_AUDITOR1.json`: verdict CONFIRMED, JSON hợp lệ.
- 5 phát hiện phụ KHÔNG chặn (N1 sửa dòng ước ngân sách 29–139; N2 tách 2 nguồn bằng chứng NBA; N3 enum thiếu BAN_DRAW đã có lối fail-closed; N4 GĐ1 ghi 395 vs đếm lại 394 file journal; N5 định nghĩa cột paper_pnl_usd) — để chủ xử lý bằng chữ ở vòng duyệt.
- AUDITOR-1 là agent mới, khác PLANNER/RESEARCHER — đúng luật độc lập.

## Quyết định của agent chính sau GĐ3 — KHÔNG giao COLLECTOR hôm nay (DỪNG)

Ba luật cùng hội tụ về DỪNG:
1. Mẫu kiểm toán đóng băng (8eaaaa5e…): sau audit CONFIRMED, chờ CHỦ đọc file kiểm toán rồi mới có lệnh GO cho bước tiếp theo — auditor không có quyền GO, agent chính cũng không tự sáng quyền đó.
2. Phương án F2 mặc định (a): trần 200 request/ngày cộng dồn đã hết hôm nay (Việc 3 dùng 200/200) và worker WSL còn tiêu tiếp — dù có GO, thu thập cũng phải xếp hàng tới ~08–09/11.
3. KE_HOACH_V2 còn nguyên bộ "SỐ ĐỀ XUẤT — chờ chủ chốt" (ngưỡng 3 ví/60%, 30 ví, tiền đặt tối thiểu từng giải, trần 120 request/ngày) + N1–N5 cần chủ xử lý bằng chữ. Thu thập theo ngưỡng chưa chốt = nguy cơ thu lại, tốn ngân sách giới hạn.

GĐ7 (áp dụng PaperDesk): CẤM, không đổi.

## Cửa GĐ4 — kiểm xếp hàng ngày 2026-11-06: NOT_RUN (hàng chưa mở)

- Prompt GĐ4 nhận 06/11, GO ban hành theo văn bản lệnh chủ. Kiểm mục 1 trước phiên đầu:
  - KE_HOACH_V2.md nguyên byte (61188913…), spec V2 FILE khớp (ae504a97…bee55d8) — PASS.
  - Việc 3 CHƯA XONG: interim 06/11 (commit 040802a) "CHƯA XONG", 32/105 ngày phủ, còn ~300–400 request → điều kiện tiên quyết SAI → NOT_RUN, 0 request của lane hôm nay.
  - 3 nguồn kiểm chứng đủ: Việc 3 = 111/200 (ngày Saigon), WSL = 10 (00:04–02:22Z, UTC), lane này = 0.
- Flag: QUYET_DINH_COORDINATOR_2026-11-06.md KHÔNG tìm thấy trên đĩa (find rộng) — cần ghi/ chỉ đường dẫn trước phiên thu thập đầu.
- Ước sơ bộ 0-request (trong báo cáo): liệt kê 183 ngày ≈ ~1.500 request theo mốc 8,3 req/ngày-liịch của Việc 3; trade 3 giải thêm hàng nghìn → nguy cơ vượt khung 14 ngày × 120. GĐ4a đo thật sẽ chốt.
- Báo cáo: BAO_CAO_XEP_HANG_GD4_2026-11-06.md, sha256 64d13607a06553f248c6462080a4f394b63665da30add11654687a26b6803435. Handoff: handoffs/HANDOFF_GD4_QUEUECHECK_2026-11-06.json (NOT_RUN_QUEUE_CLOSED).
- Kết luận: giữ cửa GĐ4 ĐÓNG. Mở lại khi: interim Việc 3 ghi XONG + file quyết định GO có trên đĩa + kiểm 3 nguồn ngày đó PASS.

## Cập nhật sau khi chủ chuyển file quyết định — 2026-11-06

- `QUYET_DINH_COORDINATOR_2026-11-06.md` chủ chuyển qua link muse.ai: đã tải về thư mục đón `incoming/QUYET_DINH_2026-11-06/`, copy byte-exact vào lane `research/control/PRO-WALLET-V1/`, sha256 `914838c116a0c7473ba8d3f3b3ef153113393ec01c5581acf0036e15ef2848e4`, sidecar OK.
- Đối chiếu nội dung với prompt GĐ4: KHỚP đầy đủ (thẩm quyền ủy quyền chủ 09:22 ICT; ngưỡng chốt NBA/bóng đá/WSL; ≥3 ví/≥60%; trần lane 120, tổng ≤200; N1–N5 bằng chữ + file KE_HOACH_V2 giữ nguyên 61188913…; F2 (a); GO GĐ4 BAN HÀNH; "Thu thập chỉ sau khi Việc 3 xong"; GĐ7 CẤM; GĐ5 agent khác). Phán quyết trần: ngày 05/11 tổng 222 ghi nhận 1 lần, từ nay đếm đủ 3 nguồn.
- Flag "thiếu file quyết định" trong BAO_CAO_XEP_HANG_GD4_2026-11-06.md: ĐÃ ĐÓNG.
- Cửa GĐ4 vẫn ĐÓNG chờ duy nhất điều kiện còn lại: interim/log Việc 3 ghi XONG (+ kiểm 3 nguồn + hash spec tại ngày chạy).

## Cập nhật 03:12Z 06/11 — lệnh duyệt "Việc 3 +79": NOT_RUN, trần gộp đã vượt

- Chủ duyệt continuation Việc 3 tối đa 79 (số học lệnh: 111+79+WSL10=200). Đo lại: **Việc 3 = 172** (lệnh 09:27 cho phiên khác đã thi hành +61 lúc 09:54–09:59 VN, commit 02d8f3f "BẢN CUỐI chờ GO 07/11"), **WSL = 40** trong cửa sổ ngày Saigon 06/11 (27+13 file journal, nhịp ~15,5 phút) → tổng **212 > 200**. Không chạy.
- Phát hiện cấu trúc: WSL ~93 request/ngày ≈ 47% trần → Việc 3 cần 3–4 ngày nữa; GĐ4 không bao giờ mở được nếu giữ nguyên → chủ cần quyết (giảm WSL / chia trần / chấp nhận lùi) + chốt quy ước ngày (Saigon vs UTC cho kết luận trái ngược).
- Phụ lục: BAO_CAO_XEP_HANG_GD4_2026-11-06_PHU_LUC_WSL.md (kèm sha256 sidecar).

## Cập nhật 03:57Z 06/11 — QUYET_DINH_BO_SUNG_CAP thi hành: WSL ĐÃ DỪNG THẬT

- File quyết định bổ sung vào lane: QUYET_DINH_BO_SUNG_CAP_2026-11-06.md, sha256 `b11e2172…f9d9e0`, copy byte-exact từ link chủ chuyển, sidecar OK.
- Thi hành "TẠM DỪNG worker WSL": 2 lớp config (không giết tiến trình, không restart service, không sửa code):
  1. `league_pauses.WSL.active=true` (03:29:32Z) — chặn decide. PHÁT HIỆN LỖ HỎNG: fetch gamma nằm ở wiring quote (`maybe_wsl` → `_wire_wsl_real_quote`, đường `cmd_quote`) TRƯỚC cổng pause → 1 request lọt lúc 03:38:04Z.
  2. Xóa `sport_keys.WSL` (03:42:20Z) — WSL ra khỏi `_cadence_leagues()` + `maybe_wsl` BLOCKED_LEAGUE đầu đường. XÁC NHẬN THỰC NGHIỆM: tick cadence 03:51:58Z & 03:57:21Z không còn WSL, không file journal mới sau 03:38:04Z (đã qua mốc thử kế ~03:53:04Z theo throttle 900s). Runner pid 35523 giữ nguyên.
- Chốt ngày Saigon 06/11: Việc 3 = 172, WSL = 42, lane này = 0 → 214/200 (vượt 14, mọi dòng chảy dừng từ 03:42:20Z).
- Biên bản: BIEN_BAN_TAM_DUNG_WSL_2026-11-06.md, sha256 `1ab2b276…69af842`. config.json đang M (7+/2−) — chưa commit, có thể revert sạch bằng git.
- Treo cho 07/11: nhịp WSL 30 phút = `CADENCE_THROTTLE_S=900` là hằng số code dùng chung mọi giải → cần per-league throttle + restart service (người làm do chủ chỉ định). Đã lập automation 00:00 ICT 07/11 (id automation-297a8146): chỉ gỡ pause NẾU nhịp 30 phút đã có; nếu chưa → giữ pause + báo cáo (fail-closed, có rủi ro anchor trận WSL 07–08/11).
- GĐ4 lane: vẫn 0 request, xếp hàng sau Việc 3 (GO 07/11: Việc 3 ≤150/ngày).

## Cập nhật 04:57Z 06/11 — chủ duyệt sửa code nhịp WSL: ĐÃ LÀM, VERIFY ĐẠT, COMMIT 73351c97

- `ops_service.py`: +`WSL_CADENCE_THROTTLE_S=1800`, nhánh điều kiện tại dòng 1047 (khuôn per-league như settle SOCCER), diff +7/−1 không đổi gì khác.
- Restart: launchd job bị bootout từ takeover 19/10 → runner là external-spawn; đã TERM 35523 (thoát sạch, khóa nhả 2s) → start lại pid **17524** cwd root checkout, khóa HELD, heartbeat mới.
- Verify thực nghiệm ĐẠT: fetch gap 04:23:16→04:53:44 (1800s+tick); mốc 04:38:16 (code cũ sẽ fetch) qua sạch; NBA giữ 900s (04:23:09→04:38:25); journal có file mới; tick 04:55:28 THROTTLED.
- Commit `73351c97` main (config + code, +14/−1, không push; identity máy tự cấu hình — khai báo).
- Re-pause tới 00:00 ICT 07/11 theo quyết định bổ sung: xóa tạm sport_keys.WSL khỏi config LIVE (delta chưa commit; automation 17:00Z re-add → khớp lại commit). WSL fetch cuối 04:53:44Z.
- 3 fetch WSL trong verify (04:21:35 cũ/nhịp 900s cửa sổ đua — khai báo; 04:23:16; 04:53:44) — theo lệnh kiểm tra của chủ. WSL ngày 06/11 chốt **45**; tổng ngày **217/200**; không request WSL nào sau 04:53:44Z.
- Biên bản cập nhật: BIEN_BAN_TAM_DUNG_WSL_2026-11-06.md (sha mới trong sidecar).

## Automation 00:00 ICT 07/11 (17:00Z 06/11) — RESUME WSL: XONG, verify đạt

- Điều kiện nhịp 30 phút: CÓ (commit 73351c97, runner 17524 chạy code mới) → gỡ pause đúng trình tự.
- Re-add sport_keys.WSL lúc 17:01:02Z; config live khớp lại commit 73351c97 (git sạch).
- Bằng chứng: fetch #1 17:01:20Z; mốc code-cũ 17:16:20 qua sạch (THROTTLED tại 17:14:00 & 17:23:28); fetch #2 17:31:42Z — gap 30m22s. WSL ngày Saigon 07/11: 2/50.
- Việc 3 tại 00:33 ICT 07/11: CHƯA XONG (commit cuối 02d8f3f, interim FINAL 06/11, chờ GO 07/11 chạy đêm) → **cửa GĐ4 VẪN ĐÓNG**. Khi mở: pro ≤120, WSL ≤50, tổng ≤200, ngày Saigon, đếm 3 nguồn trước mỗi phiên.
- Biên bản (kèm mục RESUME): BIEN_BAN_TAM_DUNG_WSL_2026-11-06.md, sha256 `27e627b8…0cbc872`.

## 2026-11-08 ~13:15 VN — chủ ủy quyền chạy hằng ngày; Việc 3 đã tự chạy (phiên khác) — tôi không chạy trùng

- **Quyền hạn mới của chủ (chat 2026-11-08 ~13:14 VN):** "vậy bạn chạy đi. Tôi cho phép bạn chạy mỗi ngày mà không cần xin ý kiến tôi." — áp dụng cho chuỗi Việc 3 (tới khi listing XONG) và sau đó là các phiên GĐ4 của lane này, trong mọi trần/luật đang đứng.
- **Thực tế đo lúc 13:15 VN:** phiên Việc 3 KHÁC (session ZCode khác, pid 66049, zsh spawn 13:11:43 VN) đang chạy ngày 08/11 theo GO "ngày 7 ngày 8", **cap 200** (không phải 150 như quyết định bổ sung b11e2172), nhịp 10s, watchdog cooldown 17 phút + 1 retry 15s. Tiến độ lúc đo: 9 request, checkpoint slice 2025-10-23→24. WSL hôm nay: 0; lane này: 0.
- **Quyết định của tôi:** KHÔNG can thiệp (luật không giết tiến trình người khác, không chạy trùng 1 tiến trình). KHÔNG khởi động phiên riêng. Ghi nhận LỆCH: quyết định bổ sung ghi Việc 3 ≤150/ngày từ 07/11, phiên kia chạy 200 theo GO mới hơn của chủ — nếu phiên đó tiêu gần 200 HÔM NAY, tổng với WSL (trận WSL 08/11 cần quote chiều tối) có nguy cơ vượt 200 gộp. Tôi theo dõi, ghi số thực, không tự cắt ai.
- Automation backstop hằng ngày 00:05 VN đã lập (xem cron): chỉ chạy Việc 3 khi phiên khác KHÔNG chạy trong ngày; khi listing XONG → mở cửa GĐ4 + phiên thu thập bounded ≤120/ngày theo kế hoạch đã duyệt; dừng an toàn khi vượt khung / lỗi / GĐ5 verdict.

## 2026-11-09 06:00 VN — automation backstop: Việc 3 HOÀN TẤT → MỞ CỬA GĐ4 → preflight VƯỢT → DỪNG, chờ chủ

- **Việc 3 HOÀN TẤT** (commit `9c3698f` đêm 09/11 của phiên chính: 105/105 ngày phủ, hàng đợi rỗng, 71.351 id / 19.230 hợp lệ, 1.305 request thật/6 ngày). Điều kiện "interim ghi XONG" ĐẠT → **CỬA GĐ4 MỞ**: từ giờ lane ví pro ≤120/ngày, WSL ≤50, Việc 3 = 0 (phân bổ theo quyết định b11e2172).
- Ngày Saigon 09/11: Việc 3 tiêu 175 (phiên cuối của nó), WSL 0, lane này 3 (probe) = 178/200 ✓.
- **GĐ4a preflight ĐÃ CHẠY** (3 request probe: WSL tag 105959 hoạt động — 6 event mở; /events sống; /tags tồn tại nhưng không hiệu quả săn id). Ước tính neo trên số đo listing: NBA ~1.100–1.400 thị trường, bóng đá ~3.800–5.400, WSL ~85 (tag-only). Tổng 3 giải ~9.000–14.600 request = **75–122 ngày @120** — VƯỢT khung 14 ngày 5–8,7×; NBA+WSL (tốt nhất) 17–33 ngày — vẫn VƯỢT; WSL-only ĐẠT nhưng mẫu vô dụng (4–6 trận/tháng bóng).
- **Verdict: VƯỢT → GĐ4b DỪNG HẲN đúng luật** (lệnh GĐ4: "Vượt 1 trong 2 → DỪNG, báo cáo số vượt + đề xuất giữ/thu hẹp theo luật KHÔNG dựa trên lãi. Không tự thu hẹp"). Đề xuất A (NBA+WSL nới khung ngày, giữ nguyên luật — khuyên) / B (A + trần 145) / C (WSL-only chạy thử) — chi tiết BAO_CAO_GD4A_PREFLIGHT_2026-11-09.md sha `cb9a191a…`.
- Automation backstop: TẠM DỪNG theo đúng điều kiện dừng ghi trong lệnh lập nó.
- Request log lane: `.my-quantitative-data/PRO-WALLET-V1/collect/request_log.jsonl` (3 dòng, mỗi dòng đủ trường theo luật).
