# KẾ HOẠCH V2 — LỚP Ý KIẾN VÍ PRO CHO TOÀN BỘ GIẢI CÓ DỮ LIỆU

Ngày: 2026-11-05. Người viết: PLANNER Giai đoạn 2, lane PRO-WALLET-V1.
Trạng thái: BẢN KẾ HOẠCH V2 — CHƯA DUYỆT, CHƯA ĐÓNG BĂNG, CHƯA CHẠY. Không được build, không được gọi API, không được chạy bóng khi file này còn chưa được chủ duyệt.

Quy ước nhãn: mọi ngưỡng chưa có lệnh của chủ đều ghi rõ **"SỐ ĐỀ XUẤT — chờ chủ chốt"**. Không ngưỡng nào trong file này là luật đã chốt.

## 0. Căn cứ và ranh giới cứng

Đầu vào (hash đã verify ở Bước 0 và cửa Giai đoạn 1):

| File | sha256 |
|---|---|
| Kế hoạch gốc `ke-hoach-lop-y-kien-vi-pro-nba-wnba-2026-11-05.md` | `6196d282…` |
| Báo cáo Giai đoạn 1 (kèm ERRATA 2026-11-05) `NGHIEN_CUU_GIAI_DOAN1.md` | `61b6f68e6bef008fe11e2687f0235013008e6263900ecb0fffd0909648468f17` |
| Spec copytrade v2 FROZEN (pin theo FILE) `polymarket-copytrade-20-SPEC-V2-FROZEN.md` | `ae504a97feb50204c7028644f78bfd0d1728b8d3f0c7a52d0dfb64cbee55d8` |
| Spec D2 gate invariant (chỉ tham chiếu đường chính, KHÔNG đụng) | `06e204d2…` |

Ranh giới cứng của lớp này (kế thừa kế hoạch gốc + prompt chủ 2026-11-05):

1. **SHADOW-ONLY.** Lớp này chỉ chạy bóng. Không đụng đường chính PaperDesk: không sửa model, không sửa giá, không đụng cổng AI DeepSeek, không sửa sổ D2. Sổ D2 chỉ được ĐỌC khi chấm điểm để đối chiếu quyết định của bàn.
2. Không đặt lệnh thật. Không tài khoản. Không chi tiêu. Giấy 100%, 0 đồng.
3. Áp dụng lớp này vào đường chính = Giai đoạn 7. **GĐ7 CẤM trong prompt này.** Muốn mở phải có: spec riêng + kiểm toán độc lập CONFIRMED + lệnh GO riêng của chủ.
4. File này là bản V2, viết mới. Kế hoạch gốc KHÔNG bị sửa, giữ nguyên làm bằng chứng. Nơi có lệch kế hoạch gốc (phạm vi giải mở rộng theo lệnh chủ) thì ghi rõ lý do bằng chứng.

## 1. Phạm vi giải

Kết luận dữ liệu lấy từ báo cáo Giai đoạn 1 (mục 4 + ERRATA), không đo thêm.

| Giải | Vào/Không | Lý do (bằng chứng GĐ1) |
|---|---|---|
| NBA | **VÀO** | ĐỦ kênh dữ liệu. Mùa đang mở (từ 20/10/2026). Có bằng chứng thị trường trận đơn đo thật (slug `nba-mem-uta-2026-10-26`, mẫu 23 ví/thị trường). |
| Bóng đá nam (SOCCER) | **VÀO** | ĐỦ kênh dữ liệu. Có bằng chứng thị trường đã đóng + đang mở (EPL mở 02/11/2026, Chelsea 10/2026, clob_books 3 cửa HOME/AWAY/DRAW). |
| WSL | **VÀO** | ĐỦ kênh dữ liệu (sau ERRATA). Có sẵn bản đồ Gamma `/events?tag_id=105959&closed=false`, 35 event mở trong snapshot 05/11/2026, snapshot sống liên tục từ 14/10/2026. |
| WNBA | **NGOÀI — THIẾU DỮ LIỆU** | Nghỉ mùa từ ~31/10/2026, về khoảng 05/2027. Không có bằng chứng thị trường WNBA trên đĩa. Không trận mới trong tháng chạy bóng. |
| NCAA nam (bóng rổ) | **NGOÀI — THIẾU DỮ LIỆU** | Mùa mới mở 01/11/2026. Trên đĩa chỉ thấy `ncaa-football` (bóng bầu, môn khác). Chưa có bằng chứng thị trường bóng rổ NCAA trên đĩa. |
| NCAA nữ (bóng rổ) | **NGOÀI — THIẾU DỮ LIỆU** | Như NCAA nam, thanh khoản còn thấp hơn. |

Chỉ tính thị trường THỂ THAO TRẬN ĐƠN: tag `'Sports'` đúng chữ khi `include_tag=true`, `sportsMarketType` khác rỗng, `gameStartTime` khác rỗng, không phải mùa vụ/futures (kế thừa luật Q1 spec v2 đã kiểm toán). Ý kiến tính trên thị trường moneyline chính của trận. Biến thể (exact-score, first-to-score, halftime-result, mùa vụ) chỉ ghi mô tả, không tính ý kiến — SỐ ĐỀ XUẤT — chờ chủ chốt.

Luật bổ sung giải mới:

1. Không tự mở rộng phạm vi giữa tháng chạy bóng. Không có ngoại lệ.
2. Bổ sung giải phải qua đủ 4 bước: (a) bản sửa kế hoạch (v3) viết trước; (b) đo thật có bằng chứng thị trường trận đơn của giải trên đĩa (snapshot + hash); (c) kiểm toán lại độc lập; (d) lệnh của chủ.
3. Mốc kiểm tra lại đề xuất (SỐ ĐỀ XUẤT — chờ chủ chốt): WNBA khi mùa 2027 mở (~05/2027) và có thị trường trận đơn WNBA đo thật; NCAA nam/nữ khi có tối thiểu 5 thị trường trận đơn bóng rổ NCAA đang mở đo thật trên đĩa.

## 2. Định nghĩa "pro" từng giải

Điều kiện chung, áp cho mọi giải trong phạm vi:

1. Ví công khai trên Polymarket, có hoạt động đặt thể thao trong cửa sổ chọn (mục 3).
2. Số lệnh đạt ngưỡng từng giải (bảng dưới) trong cửa sổ chọn.
3. Lãi ròng dương trong cửa sổ chọn. Tính lãi "giữ-tới-chốt" từ `resolutions.payouts` (đơn vị micro-USDC), chỉ tính thị trường đã chốt trước mốc đóng băng; thị trường chưa chốt không tính lúc chọn (kế thừa luật spec v2 mục 2.4 — chống rò rỉ tương lai).
4. Tổng tiền đặt đạt ngưỡng từng giải. Đo từ dữ liệu trade trong cửa sổ chọn. KHÔNG dùng `volumeNum` cuối (chứa tương lai — luật đã chốt của spec v2).
5. Loại ra: ví sàn; ví làm giá (market-maker); ví mới lập (hoạt động đầu tiên cách mốc đóng băng dưới 6 tháng). Dấu hiệu làm giá/bot (kế thừa Q3 spec v2; áp cho lớp này là SỐ ĐỀ XUẤT — chờ chủ chốt): both-sides quá 30% chuỗi TRADE; trên 2.000 lệnh mà lãi/khối lượng dưới 1%.
6. Tối đa 30 ví MỖI GIẢI (SỐ ĐỀ XUẤT — chờ chủ chốt). Xếp hạng theo lãi giữ-tới-chốt trên mỗi đồng đặt, giảm dần. Hòa: số lệnh nhiều hơn trước, rồi số thị trường nhiều hơn trước, rồi địa chỉ ví theo thứ tự chữ cái. Không đủ số đạt chuẩn thì danh sách ngắn hơn 30, ghi rõ; không hạ cửa để đủ.
7. Danh sách ví đóng băng RIÊNG TỪNG GIẢI. Ví pro của giải này không cho ý kiến ở giải khác.

Bảng ngưỡng theo giải — TOÀN BỘ là SỐ ĐỀ XUẤT — chờ chủ chốt. Lý do khác nhau: thanh khoản từng giải khác nhau (NBA mẫu đo 23 ví/thị trường; WSL chưa có số ví trên đĩa, tiền đặt thấp hơn nhiều):

| Giải | Số lệnh tối thiểu / 6 tháng | Tổng tiền đặt tối thiểu | Lãi ròng | Tối đa ví |
|---|---|---|---|---|
| NBA | ≥ 30 | ≥ 5.000 USD | dương | 30 |
| Bóng đá nam | ≥ 30 | ≥ 5.000 USD | dương | 30 |
| WSL | ≥ 15 | ≥ 1.000 USD | dương | 30 |

Ghi chú: 5.000 USD là con số ví dụ trong kế hoạch gốc (chủ chốt số cuối). WSL đề xuất hạ ngưỡng vì thanh khoản thấp. Nếu chủ giữ ngưỡng 5.000/30 lệnh cho WSL mà không đủ ví thì ghi THIẾU DỮ LIỆU, không tự hạ.

## 3. Chọn và đóng băng danh sách ví (chống rò rỉ tương lai)

Nguyên tắc (kế hoạch gốc mục 5): chọn ví TRƯỚC khi thấy kết quả. Đóng băng cả tháng. Không đổi giữa tháng.

Hai cửa sổ tách tuyệt đối:

- **Cửa sổ chọn** (quá khứ): mọi dữ liệu dùng để chọn ví phải có timestamp trước mốc đóng băng T_freeze.
- **Cửa sổ chạy bóng** (tương lai): bắt đầu sau T_freeze. Ý kiến hằng ngày chỉ dùng fill phát sinh trong cửa sổ chạy bóng.

Quy trình:

1. Gắn mốc T_freeze (chính xác tới giây, UTC) TRƯỚC khi thu thập cửa sổ chọn. Ghi T_freeze vào mọi file kết quả.
2. Cửa sổ chọn = [T_freeze − 183 ngày, T_freeze). Thu thập trong cửa sổ chọn: liệt kê thị trường từng giải (mục 7), lấy trade từng thị trường, lấy resolutions thị trường đã chốt, gom theo ví.
3. Áp 7 điều kiện mục 2 cho từng giải. Ra danh sách ví + chỉ số đo được + thứ hạng.
4. Ghi file danh sách ví đóng băng (mỗi giải 1 bảng trong 1 file): địa chỉ ví, số lệnh, tổng tiền đặt, lãi giữ-tới-chốt, dấu hiệu loại. Kèm file .sha256. Ghi rõ T_freeze + cửa sổ chọn.
5. Sau đóng băng: danh sách bất biến trong tháng chạy bóng. Không thêm, không bớt, không thay thứ hạng. Phát hiện lỗi sau đóng băng (ví sàn lọt vào): chỉ ghi ERRATA mô tả; không sửa danh sách; không tính lại ý kiến đã chốt; báo chủ quyết.
6. T_chay (đầu tháng chạy bóng) = 00:00 UTC đầu tiên sau khi danh sách đóng băng VÀ chủ ra lệnh GO chạy bóng. Tháng chạy bóng = [T_chay, T_chay + 1 tháng).

Luật chống rò rỉ tương lai khi chọn (kế thừa luật cấm của spec v2):

- Không dùng leaderboard làm nguồn chọn ví (đã chứng minh không có tháng quá khứ; bảng `all` chứa tương lai).
- Không dùng dữ liệu sau T_freeze, không dùng volumeNum cuối, không dùng kết quả chạy bóng để sửa lựa chọn.
- Sàng thị trường của cửa sổ chọn không dựa trên lãi/PnL/kết quả (luật đã chốt của spec v2 mục 2.2).

## 4. Tính ý kiến hằng ngày và reset 00:00 UTC

- Ngày chạy bóng cắt lúc 00:00 UTC (07:00 giờ Việt Nam). Đây là đầu ngày thi đấu Mỹ.
- Mỗi ngày tính lại từ đầu. Ý kiến hôm qua không mang sang hôm nay. Danh sách ví đóng băng thì cố định cả tháng (kế hoạch gốc mục 4).
- Với mỗi trận trong ngày của từng giải trong phạm vi:
  - Cửa sổ fill = [00:00:00 UTC của ngày đó, gameStartTime của trận). Chỉ fill của ví trong danh sách đóng băng của giải đó, trên thị trường moneyline chính.
  - Đếm: số ví khác nhau đặt mỗi phía; tổng tiền pro mỗi phía. Tiền mỗi fill = price × size (SỐ ĐỀ XUẤT; đối chiếu `usdc_size` của activity khi cần kiểm tra).
  - Phía = token kết cục của moneyline: bóng rổ 2 phía (home/away); bóng đá 3 phía (home/away/draw).
- Ngưỡng ý kiến (SỐ ĐỀ XUẤT — chờ chủ chốt; đúng đề xuất kế hoạch gốc mục 6):
  - Từ 3 ví trở lên cùng đặt 1 phía, VÀ tiền pro phía đó từ 60% trở lên tổng tiền pro của trận → ý kiến "ỦNG HỘ ĐẶT" phía đó.
  - Bàn muốn đặt phía X mà pro ủng hộ phía khác → ghi "CẢNH BÁO BỎ" ở tầng đối chiếu (ý kiến pro vẫn giữ nguyên hướng).
  - Không đạt 2 điều kiện trên → "KHÔNG CÓ Ý KIẾN". Ghi rõ nguyên nhân (thiếu ví / tiền chia đều). Cấm ghi đè thành ủng hộ hay cảnh báo.
- Thời điểm chốt ý kiến: trước gameStartTime của từng trận. Sau khi ghi vào sổ ý kiến thì khóa, không tính lại trong ngày.
- WSL nhiều ngày sẽ không đủ 3 ví → lớp im lặng là ĐÚNG, không phải lỗi (kế hoạch gốc mục 10).
- Một người nhiều ví: đếm theo ví (như kế hoạch gốc). Ghi hạn chế này khi chấm. Nếu có bằng chứng nhóm ví trùng người thì chỉ ghi mô tả, không đổi số đếm — SỐ ĐỀ XUẤT.

## 5. Schema sổ bóng

- Sổ bóng riêng. TUYỆT ĐỐI không đụng sổ D2 của PaperDesk. Không tạo file trong thư mục sổ D2.
- Sổ bóng gồm 2 file CSV append-only: chỉ được thêm dòng; cấm sửa hoặc xóa dòng cũ. Hai file nối nhau bằng khóa (ngay_utc, giai, condition_id). Mỗi file: 1 dòng/trận/ngày.
- Lý do tách 2 file: dòng ý kiến phải viết và khóa TRƯỚC khi trận diễn ra; dòng kết quả chỉ viết SAU khi thị trường chốt. Gộp một file sẽ buộc sửa dòng cũ — phạm append-only.
- Vị trí đề xuất (SỐ ĐỀ XUẤT — chờ chủ chốt): `.my-quantitative-data/PRO-WALLET-V1/shadow/`, ngoài repo. Mỗi ngày sau khi thêm dòng: tính lại .sha256 sidecar cho cả 2 file.

File A — `SO_BONG_Y_KIEN.csv` (viết mỗi ngày, trước gameStartTime từng trận):

| # | Tên cột | Nghĩa |
|---|---|---|
| 1 | ngay_utc | ngày chạy bóng theo UTC (YYYY-MM-DD) |
| 2 | giai | NBA \| SOCCER \| WSL |
| 3 | tran_slug | slug thị trường trận đơn |
| 4 | condition_id | mã conditionId của thị trường moneyline chính |
| 5 | doi_home | tên đội nhà |
| 6 | doi_away | tên đội khách |
| 7 | gio_bat_dau_utc | gameStartTime (ISO 8601 + epoch) |
| 8 | cua_so_fill_utc | cửa sổ fill thực tế lấy được [00:00 UTC, gameStartTime) |
| 9 | so_vi_pro_home | số ví đóng băng đặt home trong cửa sổ fill |
| 10 | so_vi_pro_away | số ví đóng băng đặt away |
| 11 | so_vi_pro_draw | số ví đóng băng đặt draw (bóng rổ để 0) |
| 12 | tien_pro_home_usd | tổng tiền pro phía home |
| 13 | tien_pro_away_usd | tổng tiền pro phía away |
| 14 | tien_pro_draw_usd | tổng tiền pro phía draw (bóng rổ để 0) |
| 15 | y_kien_pro | UNG_HUONG_HOME \| UNG_HUONG_AWAY \| UNG_HUONG_DRAW \| KHONG_CO_Y_KIEN |
| 16 | ly_do | ngắn: đạt hoặc thiếu ngưỡng nào |
| 17 | thoi_diem_chot_utc | thời điểm khóa ý kiến |
| 18 | so_request_dung | số request đã tiêu cho trận này trong ngày |
| 19 | du_lieu_goc | đường dẫn snapshot gốc (truy vết được từng fill) |

File B — `SO_BONG_KET_QUA.csv` (viết sau khi thị trường chốt, mỗi trận đúng 1 lần):

| # | Tên cột | Nghĩa |
|---|---|---|
| 1 | ngay_utc | khóa, giống file A |
| 2 | giai | khóa, giống file A |
| 3 | condition_id | khóa, giống file A |
| 4 | ket_qua_tran | HOME \| AWAY \| DRAW (từ resolutions.payouts) |
| 5 | quyet_dinh_ban | BAN_HOME \| BAN_AWAY \| KHONG_DAT (chỉ đọc từ sổ D2; không có lệnh thì KHONG_DAT) |
| 6 | y_kien_pro_sao_chep | copy từ file A theo khóa; cấm tính lại |
| 7 | nhom_phan_diet | 1_DONG_Y \| 2_NGUOC_Y \| 3_PRO_CO_Y_KIEN \| 4_PRO_KHONG_Y_KIEN (mục 8) |
| 8 | gia_vao_theo_pro | VWAP fill pro trên phía được ủng hộ, trong cửa sổ fill |
| 9 | gia_dong_cua | giá fill cuối cùng trước gameStartTime trên token phía chấm |
| 10 | clv_phan_tram | (gia_dong_cua − gia_vao) / gia_vao × 100 theo phía chấm |
| 11 | paper_pnl_usd | lời/lỗ giấy của dòng này |
| 12 | paper_thang | 1 \| 0 \| 0.5 |
| 13 | thoi_diem_ghi_utc | thời điểm ghi dòng |
| 14 | ghi_chu | rỗng hoặc ghi lỗi/NOT_RUN |

- Trận thiếu dữ liệu (không lấy được fill, chưa chốt, không ánh xạ được sổ D2): ghi NOT_RUN ở trường tương ứng. Không điền suy diễn. Thiếu bằng chứng là NOT_RUN.

## 6. Ngân sách request và luật xếp hàng

Bối cảnh (bằng chứng GĐ1): trần 200 request/ngày là CỘNG DỒN mọi tiến trình. Ngày 05/11 Việc 3 (listing copytrade v2) đã dùng 200/200, còn khoảng 3 ngày (~08–09/11). Worker WSL của lane khác vẫn đang tiêu request Gamma (22 request ngày 05/11).

Luật xếp hàng (phương án mặc định (a) của chủ, REVIEW_PROMPT F2):

1. Lane này KHÔNG gọi API nào cho tới khi listing Việc 3 xong (bằng chứng: interim log của Việc 3 ghi xong), HOẶC chủ ra lệnh chia trần riêng.
2. Trước mỗi phiên chạy: đếm request đã dùng TRONG NGÀY của 3 nguồn: (i) Việc 3 (log của nó); (ii) worker WSL (journal `/Users/hoangminhlong/.my-quantitative-data/sports-polymarket-cutover-prep-v1/journal/`, chỉ đọc); (iii) lane này (request log riêng). Một nguồn không kiểm chứng được → hôm nay KHÔNG ĐƯỢC CHẠY (bằng chứng thiếu = NOT_RUN).
3. Trần lane này: 120 request/ngày (SỐ ĐỀ XUẤT — chờ chủ chốt), chừa tối thiểu 80 cho tiến trình khác. Tổng mọi nguồn phải ≤ 200.
4. Nhịp tối thiểu 10 giây/request. Một tiến trình duy nhất — không song song, không tăng tốc bù.
5. Trước mỗi phiên chạy: kiểm tra sha256 FILE spec copytrade v2 đúng `ae504a97feb50204c7028644f78bfd0d1728b8d3f0c7a52d0dfb64cbee55d8`. Pin theo FILE, không pin HEAD repo (F3). Sai hash hoặc thiếu file → DỪNG, không tự tìm bản khác.
6. Gặp 429, 403, throttle, chậm bất thường → DỪNG toàn bộ phiên. Ghi lỗi + Retry-After vào log. Không tăng tốc, không chạy bù.
7. Mỗi request ghi 1 dòng vào request log của lane: thời điểm, URL, HTTP code, số dòng trả về.

Ước chi phí mỗi ngày chạy bóng (cận dưới — SỐ ĐỀ XUẤT; GĐ4a preflight đo lại và báo trước khi tiêu):

- Liệt kê: WSL 1 request (`/events?tag_id=105959`); NBA 2–4; SOCCER 4–8 (Gamma `/markets` + lọc ngày + phân trang).
- Trade từng trận: NBA 10–15 trận × 1–2 request; SOCCER 10–30 trận × 1–3; WSL 2–6 trận × 1.
- Tổng ước 40–110 request/ngày. Thị trường trên 500 fill/ngày phải chia cửa sổ thời gian → tăng request; preflight phải báo.

Chi phí một lần của GĐ4 (cửa sổ chọn 6 tháng × 3 giải): không chạy đột phát. GĐ4a preflight đếm mô tả trước (số thị trường từng giải, ước request, ước số ngày với trần 120/ngày) → DỪNG, báo chủ duyệt ngân sách. Vượt 14 ngày → báo vượt bao nhiêu + đề xuất giữ/thu hẹp theo luật KHÔNG dựa trên lãi (kế thừa khuôn Việc 3 của spec v2). Chủ quyết.

## 7. Khung thu thập: endpoint, cache, checkpoint, xử lý lỗi

Endpoint (đều đã có bằng chứng đo thật — báo cáo GĐ1 mục 2):

| Việc | Endpoint và luật |
|---|---|
| Liệt kê thị trường WSL | Gamma `GET /events?tag_id=105959&closed=false` (rẻ nhất, bản đồ có sẵn) |
| Liệt kê thị trường NBA/SOCCER | Gamma `GET /markets?include_tag=true` (+ `end_date_min/max`, `order=id`, `ascending=true`, limit ≤ 100 — server kẹp tại 100) → xác minh từng thị trường bằng `gameStartTime`; chỉ giữ tag 'Sports' + `sportsMarketType` ≠ rỗng + `gameStartTime` ≠ rỗng + trận đơn + không mùa vụ |
| Tra lại theo mã | lặp `condition_ids=<mã>` từng mã một + `closed=any` (dạng comma KHÔNG hoạt động; tham số `market=` bị HTTP 400 — cấm dùng) |
| Lấy bet theo trận (ưu tiên) | data-api `GET /v2/trades?condition_id=<cid>&taker_only=false&start&end&limit=500`; trên 500 fill → chia nhỏ cửa sổ start/end (không cursor, không offset); lọc ví đóng băng phía client |
| Lấy bet theo ví (kiểm tra riêng) | data-api `GET /v2/trades?user=<ví>&taker_only=false` |
| Tiền USD từng lệnh | price × size từng fill; `usdc_size` trên `GET /v2/activity?user=&type=TRADE` dùng khi cần đối chiếu |
| Kết quả chốt | data-api `GET /v2/resolutions?condition=` (payouts micro-USDC) + đối chiếu Gamma `umaResolutionStatus`; lệch → DỪNG và báo |
| Giới hạn phân trang Gamma | offset ≥ 2100 bị HTTP 422 → chia lát cửa sổ `end_date` (bisection), mỗi query tối đa ~2.100 dòng |

Cache:

- Mọi response thô lưu snapshot JSON xuống đĩa kèm thời điểm + URL + sha256 (khuôn journal của WSL lane).
- Cùng URL + cùng cửa sổ trong cùng ngày → dùng lại snapshot, không gọi lại.
- Dữ liệu cửa sổ chọn là quá khứ bất biến: cache vĩnh viễn, không bao giờ fetch lại phần đã có.

Checkpoint:

- File tiến độ JSON: đơn vị công việc = (giải, condition_id, bước); trạng thái TODO/DONE/ERROR + số request đã dùng trong ngày.
- Crash hoặc dừng giữa chừng → phiên sau tiếp tục từ checkpoint, không lặp phần DONE.
- Cuối phiên: tổng kết request trong ngày vào request log + checkpoint.

Xử lý lỗi:

- 429/403/throttle → DỪNG toàn bộ (mục 6).
- Lỗi khác (4xx/5xx): thử lại tối đa 2 lần, giữ nhịp 10 giây; vẫn lỗi → đánh dấu ERROR đơn vị đó, tiếp tục phần khác, ghi log ngày.
- Dữ liệu thiếu hoặc không khớp khi tính ý kiến/chấm → NOT_RUN cho trận/trường đó. Không suy diễn, không nội suy.

## 8. Phán xét sau 1 tháng

4 nhóm (kế hoạch gốc mục 8, định nghĩa chặt):

1. NHÓM 1 — ĐỒNG Ý: bàn có lệnh BET_PAPER phía X (đọc từ sổ D2) VÀ ý kiến pro = ủng hộ X.
2. NHÓM 2 — NGƯỢC Ý: bàn đặt X, pro ủng hộ phía khác (kể cả DRAW bóng đá).
3. NHÓM 3 — PRO CÓ Ý KIẾN: mọi trận có ý kiến pro ≠ KHÔNG CÓ Ý KIẾN (chứa nhóm 1, 2 và cả trận bàn không đặt).
4. NHÓM 4 — PRO KHÔNG CÓ Ý KIẾN: mọi trận ý kiến pro = KHÔNG CÓ Ý KIẾN.

Số đo mỗi nhóm: paper PnL (USD), tỉ lệ thắng, CLV (giá vào so giá đóng cửa — mục 5).

- Kịch bản "theo pro" (nhóm 3): mỗi trận có ý kiến, đặt giấy 100 USD phía được ủng hộ; giá vào = VWAP fill pro trong cửa sổ fill (SỐ ĐỀ XUẤT — kế thừa mấu 100 USD cố định của spec v2).
- Kịch bản "bàn đơn thuần": theo lệnh BET_PAPER thật trong sổ D2 (chỉ đọc).

Ngưỡng phán xét: tối thiểu 30 trận có ý kiến pro MỖI GIẢI (SỐ ĐỀ XUẤT — chờ chủ chốt; kế hoạch gốc mục 8). Giải nào thiếu → kết luận giải đó là THIẾU DỮ LIỆU. Không kết luận pro giỏi hay dở ở giải đó. Cấm gộp số giải này bù cho giải khác.

Điều kiện "đạt" của lớp (kế hoạch gốc mục 8): nhóm nghe theo pro lời hơn nhóm không nghe, số trận đủ lớn theo ngưỡng trên, kiểm toán độc lập xác nhận. Thiếu một trong ba thì không đạt.

Mọi ngưỡng đóng băng trước khi chạy. Không đổi sau khi thấy kết quả.

## 9. Những gì KHÔNG được làm

1. Không gọi API Polymarket khi: Việc 3 chưa xong (trừ khi chủ chia trần), tổng ngày đã gần 200, chưa kiểm hash FILE spec, không kiểm chứng được request log của cả 3 nguồn.
2. Không đặt lệnh thật. Không tài khoản. Không chi tiêu. Không ví mới. Không VPN. Không bí mật trong file/log/chat.
3. Không đụng đường chính PaperDesk: không sửa model, giá, cổng AI DeepSeek, sổ D2; không ép lệnh; shadow opinion không bao giờ lọt vào opinion binding của cổng AI (luật spec D2).
4. Không sửa kế hoạch gốc, không sửa báo cáo GĐ1, không sửa file của lane khác, không đụng journal/snapshot của lane WSL (chỉ đọc).
5. Không đổi danh sách ví giữa tháng. Không đổi ngưỡng sau khi thấy kết quả.
6. Không dùng leaderboard làm nguồn chọn ví. Không dùng volumeNum cuối. Không dùng dữ liệu sau T_freeze để chọn ví. Không sàng thị trường theo lãi/PnL/kết quả (luật đã chốt của spec v2).
7. Không tự động đặt lệnh theo ý kiến pro. Lớp này chỉ là ý kiến.
8. Không tự mở rộng giải giữa tháng.
9. GĐ7 (áp dụng vào đường chính) CẤM trong prompt này: cần spec riêng + kiểm toán CONFIRMED + GO riêng của chủ.

## 10. Trình tự các bước còn lại

- Cửa ngay sau file này: CHỦ DUYỆT KE_HOACH_V2 và chốt từng SỐ ĐỀ XUẤT (mục 1 biến thể thị trường, mục 2 ngưỡng pro từng giải, mục 4 ngưỡng 3 ví/60%, mục 5 vị trí sổ bóng, mục 6 trần 120/ngày, mục 8 ngưỡng 30 trận/giải). Không có lệnh duyệt thì không giai đoạn nào chạy.
- GĐ3 — kiểm toán spec: agent khác, dùng mẫu 5 ô của chủ (hash `8eaaaa5e…`), đối chiếu file này với luật đóng băng; verdict CONFIRMED/BUG FOUND/SPEC FLAW/CHƯA ĐỦ BẰNG CHỨNG. DỪNG chờ chủ GO.
- GĐ4 — thu thập + chọn ví + đóng băng:
  1. GĐ4a preflight: đếm mô tả từng giải (số thị trường cửa sổ chọn, ước request, ước số ngày) → DỪNG báo chủ duyệt ngân sách. Chỉ chạy sau khi Việc 3 xong.
  2. GĐ4b: thu thập cửa sổ chọn theo mục 6–7.
  3. GĐ4c: chấm điểm ví theo mục 2, xếp hạng, đóng băng danh sách + T_freeze + hash.
  4. GĐ4d: báo cáo GĐ4 + handoff JSON.
- GĐ5 — kiểm toán độc lập: agent khác, mẫu chủ; đối chiếu danh sách đóng băng với dữ liệu gốc snapshot; tự tính lại ít nhất một phần quan trọng (ví dụ: lãi giữ-tới-chốt của 3 ví); verdict như GĐ3. Có BUG FOUND → sửa + chạy lại sạch phần lỗi.
- GĐ6 — build bóng + chấm: worker chạy 1 tháng. Đăng ký cycle đúng quy trình: qua /worktree-dispatch, worktree/branch `paperdesk-pro-wallet-shadow-v1`, ghi `plans/CYCLE_REGISTRY.json` (ghi trước khỏi quên — REVIEW F5). Mỗi ngày: liệt kê → lấy fill → chốt ý kiến → ghi file A; sau chốt → ghi file B. Hết tháng: chấm theo mục 8, báo cáo + handoff.
- GĐ7 — CẤM (mục 9.9). Không mở trong lane này.

Lưu ý thời gian (kế hoạch gốc mục 9): cửa sổ chấm D2 kết thúc khoảng 09/11. Việc build nên bắt đầu sau khi báo cáo D2 xong cho khỏi rối. Thu thập chỉ đọc của lane này vẫn phải xếp hàng sau Việc 3 theo mục 6.

## 11. Rủi ro đã tính trước

- Pro quá khứ giỏi, tương lai chưa chắc. Quá khứ tốt có thể chỉ là may (kế hoạch gốc mục 10).
- WSL và ngày vắng: nhiều ngày KHÔNG CÓ Ý KIẾN — đúng hành vi, ghi KHÔNG CÓ Ý KIẾN, không ép.
- Dữ liệu Polymarket trễ → ý kiến từ fill trễ yếu đi; ghi cua_so_fill_utc thực tế để đánh giá sau.
- Một người nhiều ví → đếm theo ví, ghi hạn chế khi chấm.
- Pro đặt dẫn dụ → lớp chỉ là ý kiến, không bao giờ tự đặt.
- Trần 200 dùng chung có ngày không đủ chạy → ghi NOT_RUN, không chạy bù tăng tốc.
- Bóng đá nam phạm vi rộng (nhiều giải quốc gia) → GĐ4a preflight phải báo số thị trường; nếu quá lớn, thu hẹp theo luật KHÔNG dựa trên lãi, chủ quyết.

Giai đoạn 2 xong. Làm được: viết KẾ HOẠCH V2 mới (không sửa kế hoạch gốc) cho toàn bộ giải có dữ liệu — NBA, bóng đá nam, WSL vào phạm vi chạy bóng; WNBA (nghỉ mùa từ ~31/10/2026, về ~05/2027) và NCAA nam/nữ bóng rổ (mới mở 01/11/2026, chưa có bằng chứng thị trường trên đĩa) nằm ngoài vì THIẾU DỮ LIỆU, kèm điều kiện bổ sung qua bản sửa kế hoạch + kiểm toán lại + lệnh chủ, cấm mở rộng giữa tháng; định nghĩa pro cho từng giải (số lệnh tối thiểu 6 tháng, lãi ròng dương giữ-tới-chốt, tổng tiền đặt tối thiểu, loại ví sàn/market-maker/ví mới, tối đa 30 ví/giải) — toàn bộ dán nhãn SỐ ĐỀ XUẤT chờ chủ chốt, WSL đề xuất ngưỡng thấp hơn vì thanh khoản thấp; quy trình chọn + đóng băng ví tách tuyệt đối cửa sổ chọn (quá khứ, trước T_freeze) khỏi cửa sổ chạy bóng (tương lai) chống rò rỉ tương lai, chọn TRƯỚC khi thấy kết quả, danh sách đóng băng cả tháng; cách tính ý kiến hằng ngày với reset 00:00 UTC, ngưỡng đề xuất ≥3 ví cùng phía + ≥60% tiền pro, cửa sổ fill [00:00 UTC, gameStartTime), bóng đá 3 phía kể cả hòa; schema sổ bóng 2 file CSV append-only, 1 dòng/trận/ngày mỗi file, liệt kê tên 19 cột file ý kiến + 14 cột file kết quả, không đụng sổ D2; ngân sách request chốt xếp hàng sau Việc 3 (mặc định (a)), đếm chung 3 nguồn (Việc 3, worker WSL, lane này) trước mỗi phiên, trần đề xuất 120/ngày, 10 giây/request, 1 tiến trình, cache, kiểm sha256 FILE spec ae504a97…bee55d8 trước mỗi phiên, 429/403/throttle → DỪNG; khung thu thập dùng đúng endpoint đã có bằng chứng (Gamma /markets include_tag=true, /events tag_id=105959 cho WSL, data-api /v2/trades condition_id hoặc user với taker_only=false, resolutions payouts micro-USDC, offset-cap 2100 → bisection, 500 fill/request → chia cửa sổ, market= bị HTTP 400) kèm cache snapshot + checkpoint + xử lý lỗi NOT_RUN; khung phán xét 1 tháng 4 nhóm (đồng ý/ngược ý/pro có ý kiến/pro không có ý kiến) đo paper PnL + tỉ lệ thắng + CLV, ngưỡng đề xuất ≥30 trận có ý kiến pro MỖI GIẢI, thiếu thì THIẾU DỮ LIỆU từng giải, cấm gộp; danh sách 9 việc cấm (SHADOW-ONLY, không đụng đường chính PaperDesk, GĐ7 CẤM cần spec riêng + kiểm toán CONFIRMED + GO riêng); trình tự còn lại GĐ3 duyệt/kiểm toán → GĐ4 preflight + thu thập + đóng băng ví → GĐ5 kiểm toán độc lập → GĐ6 build bóng 1 tháng + chấm (đăng ký cycle + worktree paperdesk-pro-wallet-shadow-v1); tính sha256 file + ghi sidecar + handoff JSON; 0 request API Polymarket, 0 chi tiêu, 0 lệnh. Chưa làm được: mọi SỐ ĐỀ XUẤT chưa được chủ chốt (ngưỡng pro từng giải, ≥3 ví/≥60%, tối đa 30 ví, trần 120 request/ngày, ≥30 trận/giải, vị trí sổ bóng, xử lý biến thể thị trường); chưa kiểm toán spec GĐ3; chưa preflight GĐ4a nên chưa có số thị trường/ví thật từng giải (trần 200/ngày đang bị Việc 3 tiêu hết, còn ~3 ngày ~08–09/11); chưa có danh sách ví pro cho giải nào; chưa đo thanh khoản WSL/NCAA thực tế để tinh chỉnh ngưỡng. Cửa tiếp theo: chủ duyệt KE_HOACH_V2 + chốt từng SỐ ĐỀ XUẤT, kiểm toán GĐ3 xác nhận không lệch luật, rồi GĐ4a preflight (chỉ chạy sau khi listing Việc 3 xong hoặc chủ chia trần) — áp dụng vào đường chính (GĐ7) vẫn CẤM cho tới khi có spec riêng + kiểm toán CONFIRMED + GO riêng của chủ.
