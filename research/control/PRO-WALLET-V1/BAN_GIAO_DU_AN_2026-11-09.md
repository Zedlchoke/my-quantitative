# BẢN GIAO DỰ ÁN PRO-WALLET-V1 — LỚP Ý KIẾN VÍ PRO CHO PAPERDESK — 2026-11-09

Tài liệu bàn giao toàn diện cho agent mới nhận phụ trách. Mọi con số/đường dẫn/hash dưới đây là thực đo tại thời điểm bàn giao.

---

## 1. MỤC TIÊU (điều agent mới phải thuộc lòng)

**Câu hỏi duy nhất của dự án:** *"Nếu nhìn theo các ví pro trên Polymarket đặt gì mà đặt theo, có lời hơn không?"*

Cách trả lời: thêm **"mắt thứ 4"** cho bàn PaperDesk (bàn hiện có 3 mắt: model dự báo + giá Polymarket + cổng AI DeepSeek). Mắt này xem các ví pro thật đặt cược gì mỗi ngày → cho ý kiến **"ủng hộ đặt" / "cảnh báo bỏ" / "không có ý kiến"** → chạy **CHỈ GIẤY (shadow)** đúng 1 tháng → chấm so sánh 4 nhóm (bàn&pro đồng ý / ngược ý / pro có ý kiến / pro im lặng) bằng paper PnL + win rate + CLV → kết luận có đáng đưa vào đường chính hay không.

**Ranh giới tuyệt đối:**
- $0 chi tiêu, không tài khoản mới, không lệnh thật, chỉ đặt giấy.
- KHÔNG đụng đường production của PaperDesk: không sửa model dự báo, cổng AI, sổ D2, luật quyết định, không ép lệnh.
- Giai đoạn 7 (áp dụng vào production) **CẤM** cho tới khi có đủ 3 thứ: spec áp dụng đóng băng + hash, kiểm toán độc lập CONFIRMED, lệnh GO riêng của chủ.
- Evidence-first: thiếu bằng chứng = NOT_RUN, không bao giờ suy ra PASS. Không bịa số — thiếu thì ghi "chưa có số".

## 2. VỊ TRÍ HIỆN TẠI (một câu)

Kế hoạch đã duyệt + kiểm toán CONFIRMED; việc nền (thống kê thị trường Polymarket) đã XONG; preflight đo ban đầu **VƯỢT khung 14 ngày** → toàn bộ thu thập đang **DỪNG**, automation tạm dừng, **chờ chủ chọn phương án A/B/C** (mục 6.3). Chưa tiêu requests của tháng chạy bóng; chưa có danh sách ví; chưa chạy bóng ngày nào.

## 3. BỐI CẢNH HỆ THỐNG (3 dự án dùng chung 1 máy, 1 ngân sách)

| Hệ thống | Vai trò với dự án này | Đường dẫn then chốt |
|---|---|---|
| **PaperDesk** (production paper) | Nền tảng được quan sát/so sánh; KHÔNG được đụng | repo `/Users/hoangminhlong/my-quantitative` (checkout chính, branch main); runner `research.papertrade_exec.ops_service` hiện pid 17524, cwd root; app GUI `apps/paperdesk` (PaperDesk.app) sở hữu vòng đời runner — launchd job đã bị bootout từ 19/10 (takeover.json), **không dùng launchctl kickstart**; restart đúng cách = `kill -TERM <pid>` (nhả khóa ~2s) rồi `nohup .venv/bin/python -m research.papertrade_exec.ops_service` cwd root checkout, log `/tmp/paperdesk_service_main_<ngày>.log` |
| **Copytrade-20** (dự án riêng của chủ, Việc 1–5) | Đã xong Việc 3 (thống kê thị trường) — dùng chung trần request; từ nay 0 lượt/ngày | repo `~/Downloads/Polymarket`; spec v2 FROZEN tại `docs/polymarket-copytrade-20-SPEC-V2-FROZEN.md` — **pin theo FILE, sha256 `ae504a97feb50204c7028644f78bfd0d1728b8d3f0c9b7a52d0dfb64cbee55d8`** (KHÔNG pin HEAD repo); dữ liệu listing tại `viec3/data/listing/listing_slim.jsonl.valid` (19.350 thị trường hợp lệ 2025-09-13→12-12) — neo số liệu hữu ích; dự án đó đang chờ kiểm toán riêng của nó, KHÔNG phải việc của lane này |
| **PRO-WALLET-V1** (dự án này) | Lane nghiên cứu shadow | Báo cáo/log: `research/control/PRO-WALLET-V1/` (trong repo). Data plane: `.my-quantitative-data/PRO-WALLET-V1/` **cấp repo** (`collect/request_log.jsonl`, `collect/snapshots/`, tương lai `shadow/`, `collect/checkpoint.json`). Repo input đã verify: `…/input-edge-hunt-ai-desk` @ commit `10d3eb7f…`, manifest 57/57 |

**Worker WSL** (thuộc PaperDesk, chỉ ĐỌC): fetch gamma `/events?tag_id=105959` nhịp 30 phút (đã giảm từ 15,5 phút — commit `73351c97`); journal tại `~/.my-quantitative-data/sports-polymarket-cutover-prep-v1/journal/` (mỗi file = 1 request). Cơ chế bật/tắt bằng config `research/papertrade_exec/config.json`: `sport_keys.WSL` (đăng ký lane) + `league_pauses.WSL.active` (chặn decide). LƯU Ý: cổng pause chỉ chặn `cmd_decide`; muốn chặn cả fetch phải xóa `sport_keys.WSL`.

## 4. LUẬT NGÂN SÁCH REQUEST (quan trọng nhất về vận hành)

1. Trần **200 request/ngày CỘNG DỒN mọi tiến trình**, theo **NGÀY SAIGON** (ngày mới bắt đầu 17:00Z). Cách đếm từng nguồn:
   - Việc 3: đếm `viec3/data/ledger.jsonl` — dòng có `status`+`latency_ms`, quy đổi ts UTC→Saigon (mẫu code trong `v3_preflight_day6.sh`).
   - WSL: đếm file `journal_wsl_lane_*.jsonl` trong cửa sổ ngày Saigon (từ 17:00Z hôm trước).
   - Lane này: đếm `collect/request_log.jsonl`.
   - **Một nguồn không kiểm chứng được → hôm đó KHÔNG CHẠY (NOT_RUN).**
2. Phân bổ HIỆN TẠI (quyết định bổ sung của chủ, sha `b11e2172…`, file `QUYET_DINH_BO_SUNG_CAP_2026-11-06.md` trong lane): **Việc 3 = 0 (đã xong), WSL ≤50/ngày, lane ví pro ≤120/ngày.**
3. Trước mỗi phiên: kiểm sha256 FILE spec copytrade v2 (mục 3) — sai hash → DỪNG.
4. Nhịp ≥10 giây/request, 1 tiến trình duy nhất, không tăng tốc bù. **429/403/throttle → DỪNG toàn phiên**, ghi Retry-After.
5. Mỗi request ghi 1 dòng log: thời điểm UTC, URL, HTTP code, số dòng trả về.
6. Lịch sử vượt trần đã xử lý xong: 05/11 = 222, 06/11 = 217/200 (ghi nhận, không truy cứu). Từ 07/11 đổ đi chưa vượt.

## 5. LUẬT CHỌN VÍ PRO + Ý KIẾN (ĐÃ CHỐT BỞI CHỦ — KHÔNG ĐƯỢC ĐỔI)

Nguồn khóa: `QUYET_DINH_COORDINATOR_2026-11-06.md` (sha `914838c1…`) + quyết định bổ sung (`b11e2172…`) + `KE_HOACH_V2.md` (sha `61188913…` — **file giữ nguyên từng byte**; các chỉnh chữ N1–N5 sống trong các quyết định, KHÔNG sửa file).

- **Định nghĩa pro từng giải** (trong 6 tháng trước mốc đóng băng): NBA ≥30 lệnh + ≥5.000 USD tiền đặt; bóng đá nam ≥30 + ≥5.000 USD; WSL ≥15 + ≥1.000 USD; lãi ròng dương giữ-tới-chốt; loại ví sàn/market-maker/ví mới; tối đa 30 ví/giải.
- **Chọn ví TRƯỚC khi thấy kết quả**: cửa sổ chọn = [T_freeze − 183 ngày, T_freeze); T_freeze gắn chính xác tới giây (UTC) TRƯỚC lần chạy thu thập đầu tiên, ghi vào mọi file kết quả. Danh sách đóng băng cả tháng chạy bóng, không thêm bớt giữa tháng. **Cấm**: leaderboard làm nguồn chọn, `volumeNum` cuối, sàng theo lãi/PnL/kết quả.
- **Ý kiến hằng ngày** (reset 00:00 UTC): ≥3 ví cùng phía + ≥60% tiền pro phía đó → "ủng hộ đặt"; pro ngược hướng bàn → "cảnh báo bỏ"; còn lại "không có ý kiến".
- **Phán xét 1 tháng**: 4 nhóm; đo paper PnL + win rate + CLV; kịch bản "theo pro" 100 USD/trận @ VWAP fill pro, tiền fill = price × size; cần **≥30 trận có ý kiến pro MỖI GIẢI**, thiếu → THIẾU DỮ LIỆU (không kết luận). Enum có `BAN_DRAW` (N3). `paper_pnl_usd` thuộc kịch bản "theo pro" (N5).
- Sổ bóng riêng (append-only) tại `.my-quantitative-data/PRO-WALLET-V1/shadow/`, 2 file schema 19+14 cột (chi tiết trong KE_HOACH_V2 mục 5) — **tuyệt đối không đụng sổ D2**.

## 6. TIẾN TRÌNH 7 GIAI ĐOẠN — TRẠNG THÁI & BẰNG CHỨNG

| GĐ | Trạng thái | Artifact chính (đều kèm .sha256) |
|---|---|---|
| Bước 0 đọc input | ✅ | `BUOC0_DOC_TRUOC.md` (`1c9db6a7…`); clone input verified |
| 1 nghiên cứu giải | ✅ (có ERRATA) | `NGHIEN_CUU_GIAI_DOAN1.md` (`61b6f68e…`): NBA, bóng đá nam, WSL = ĐỦ kênh; WNBA (nghỉ ~05/2027), NCAA nam/nữ = THIẾU DỮ LIỆU |
| 2 kế hoạch v2 | ✅ | `KE_HOACH_V2.md` (`61188913…`) |
| 3 kiểm toán kế hoạch | ✅ CONFIRMED | `AUDIT_KE_HOACH_V2.md` (`5bc89e44…`) — 22/22 luật, không rò rỉ tương lai |
| 4 thu thập | ⏸ **DỪNG sau preflight** | `BAO_CAO_XEP_HANG_GD4_2026-11-06.md` + phụ lục WSL (`03501a5c…`); `BIEN_BAN_TAM_DUNG_WSL_2026-11-06.md` (`27e627b8…`); `BAO_CAO_GD4A_PREFLIGHT_2026-11-09.md` (`cb9a191a…`) verdict VƯỢT |
| 5 kiểm toán dữ liệu | chưa | làm bởi agent KHÁC (mẫu `PROMPT_AGENT_KIEM_TOAN_DOC_LAP_MOI_LAN.md` sha `8eaaaa5e…` trong repo input; điền 5 ô từ file gốc, không từ chat) |
| 6 chạy bóng 1 tháng + chấm | chưa | cần worktree/branch mới `paperdesk-pro-wallet-shadow-v1` + ghi cycle registry + GO riêng của chủ |
| 7 áp dụng production | 🔒 CẤM | cần spec riêng + kiểm toán CONFIRMED + GO riêng |

Log cửa tổng: `GATE_LOG.md` (đọc đầu tiên mỗi ngày). Báo cáo ngày: `BAO_CAO_NGAY_*.md`.

### 6.1 Vì sao đang dừng (tóm tắt preflight 09/11)

Neo số đo listing Việc 3: NBA ~49 thị trường/ngày mùa / 0 nghỉ hè; bóng đá ~31/ngày mùa cao điểm; WSL = 0 qua `/markets` (chỉ thấy qua tag 105959). Chiếu lên cửa sổ 183 ngày: NBA ~1.100–1.400 thị trường, bóng đá ~3.800–5.400, WSL ~85. Lấy trades (data-api `/v2/trades?condition_id=`, 500 fill/request, quá thì chia cửa sổ thời gian): tổng 3 giải ~9.000–14.600 request = **75–122 ngày @120/ngày**; NBA+WSL tốt nhất **17–33 ngày**; WSL-only <1 ngày nhưng mẫu vô dụng. Khung đã duyệt là ≤120/ngày VÀ ≤14 ngày → **VƯỢT → DỪNG đúng luật, KHÔNG tự thu hẹp.**

### 6.2 Đề xuất đang chờ chủ chọn (đã trình 09/11)

- **A (được khuyên)**: NBA + WSL, nới khung ngày 14 → ~35 ngày, giữ nguyên mọi luật khác. Kết luận cuối ~giữa tháng 1.
- **B**: như A + nâng trần lane 120 → ~145/ngày (tổng vẫn ≤200). Nhanh thêm ~20%.
- **C**: chỉ WSL chạy thử quy trình (thiếu dữ liệu gần như chắc chắn).
- KHÔNG đề xuất thu hẹp cửa sổ 183 ngày (đổi luật chọn ví đã chốt).

### 6.3 Automation hiện trạng

`automation-297a8146` (backstop hằng ngày 06:00) — **ĐANG TẠM DỪNG** đúng điều kiện dừng (preflight VƯỢT). Khi chủ chọn A/B → chủResume nó (nút resume trên giao diện automation) HOẶC agent mới lập lại lịch; nội dung prompt đầy đủ của nó nằm trong máy (nó là phiên bản của các trình tự ở mục 4+5). Phiên chính Việc 3 cũng có automation 00:10 riêng — Việc 3 đã xong nên nó sẽ tự không còn việc.

## 7. QUY TRÌNH CHẠY PHIÊN GĐ4b KHI ĐƯỢC DUYỆT (theo đúng kế hoạch)

1. Đếm 3 nguồn (mục 4.1) → cap phiên = min(120 hoặc trần mới, 200 − WSL_hôm_nay − 2 dự phòng).
2. Kiểm hash FILE spec → gắn **T_freeze** (lần đầu) ghi vào checkpoint + mọi file.
3. Phiên đầu tiên của GĐ4b: ưu tiên tìm tag_id NBA/bóng đá (qua event tags của 1 event NBA sống — `/events?closed=false` rồi đọc trường `tags`; WSL = 105959 đã biết) để liệt kê rẻ; nếu không thấy tag trong ~10 lượt → dùng đường quét `/markets?include_tag=true` + lọc `gameStartTime` phía client (phương pháp Việc 3, ~8 request/ngày-lịch).
4. Thu thập: mỗi thị trường hợp lệ (tag 'Sports' + sportsMarketType + gameStartTime trong cửa sổ + trận đơn + không mùa vụ) → `/v2/trades?condition_id=&taker_only=false` giữ ts trong cửa sổ; snapshot JSON kèm URL+thời điểm+sha256 vào `collect/snapshots/`; cache vĩnh viễn (quá khứ bất biến — không fetch lại); checkpoint `(giải, condition_id, bước)` vào `collect/checkpoint.json`, phiên sau tiếp tục từ checkpoint.
5. Đủ dữ liệu → GĐ4c chấm điểm + đóng băng danh sách (xếp hạng lãi giữ-tới-chốt/đồng đặt giảm dần; hòa: lệnh → thị trường → địa chỉ alphabet; không đủ 30 thì danh sách ngắn hơn, không hạ cửa) → file danh sách + .sha256 vào lane.
6. GĐ5: spawn SUBAGENT MỚI làm kiểm toán (mẫu 5 ô) → verdict CONFIRMED mới tính.
7. Mỗi giai đoạn xong kết báo cáo bằng câu bắt buộc: "Giai đoạn X xong. Làm được: … Chưa làm được: … Cửa tiếp theo: …" — và mọi file tính sha256 ghi vào báo cáo.

## 8. CẠM BẪY ĐÃ BIẾT (danh sách lỗi đã trả giá)

1. **Quy ước ngày**: luôn dùng ngày Saigon cho trần 200 (code Việc 3 cũng vậy). Trộn UTC/Saigon từng gây ra kết luận sai (vụ "WSL 10" ngày 06/11).
2. **WSL tàng hình** với quét `/markets` — chỉ dùng tag 105959.
3. **Pause WSL đủ 2 lớp** nếu cần dừng hẳn: `league_pauses` chỉ chặn decide, fetch nằm ở wiring quote (`maybe_wsl` → `_wire_wsl_real_quote`) — phải xóa `sport_keys.WSL`. Config được service đọc live mỗi lần gọi (không cần restart).
4. **Không giết tiến trình người khác** (runner ops_service, Việc 3, worker WSL). Không chạy trùng Việc 3 (khóa + pgrep + ledger triple-check).
5. **Pin hash theo FILE** spec, không theo HEAD repo polymarket (repo còn di chuyển).
6. `market=` trên data-api trả HTTP 400 (cấm); dạng comma cho condition_ids không hoạt động; offset ≥2100 → HTTP 422 (chia lát end_date).
7. Git: chỉ `git add` theo pathspec (cấm `git add -A`), không push, không merge main, không rewrite; commit bằng identity máy tự cấu hình (đã khai báo với chủ).
8. Mọi báo cáo tiếng Việt, câu ngắn; con số luôn kèm nguồn file.

## 9. DÒNG THỜI GIAN DỰ KIẾN (nếu chủ duyệt A)

- Ngay khi duyệt: resume automation / chạy phiên GĐ4b đầu (gắn T_freeze) — tìm tag NBA.
- ~17–33 ngày thu thập (cận dưới nếu có tag NBA) → đóng băng danh sách ví → GĐ5 kiểm toán.
- ~giữa 12 → giữa tháng 1: chạy bóng 30 ngày (GĐ6, cần GO riêng cho worktree mới).
- Sau bóng: chấm 4 nhóm → báo cáo tổng → **chủ quyết GĐ7**.

## 10. DANH SÁCH FILE CHÍNH TRONG LANE (research/control/PRO-WALLET-V1/)

REVIEW_PROMPT_CHU_2026-11-05 · BUOC0_DOC_TRUOC · NGHIEN_CUU_GIAI_DOAN1 · KE_HOACH_V2 · AUDIT_KE_HOACH_V2 · BAO_CAO_TONG_HOP_2026-11-05 · BAO_CAO_XEP_HANG_GD4_2026-11-06 (+ PHU_LUC_WSL) · BIEN_BAN_TAM_DUNG_WSL · QUYET_DINH_COORDINATOR_2026-11-06 · QUYET_DINH_BO_SUNG_CAP_2026-11-06 · BAO_CAO_GD4A_PREFLIGHT_2026-11-09 · BAO_CAO_NGAY_* · GATE_LOG (đọc ĐẦU TIÊN mỗi ngày) · handoffs/*.json.

---

Câu kết bàn giao: "Dự án đang dừng đúng luật tại cửa GĐ4 sau preflight VƯỢT; mọi thứ khác đã sẵn sàng; việc tiếp theo thuộc về CHỦ (chọn A/B/C), sau đó agent mới chạy GĐ4b theo mục 7 với các luật mục 4–5."
