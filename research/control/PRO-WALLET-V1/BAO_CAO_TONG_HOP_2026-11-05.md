# BÁO CÁO TỔNG HỢP CHẠY PROMPT V2 — PRO-WALLET-V1 (dừng đúng cửa, 2026-11-05)

Người viết: agent chính (Mac). Phạm vi: Bước 0 + Giai đoạn 1 + 2 + 3. Giai đoạn 4 CHƯA giao — lý do ở mục 4. Giai đoạn 7 CẤM, không đụng.

## 1. Đã làm (mỗi giai đoạn 1 subagent riêng, agent chính chỉ giao + kiểm cửa)

| Bước | Subagent | Output | sha256 | Cửa |
|---|---|---|---|---|
| Bước 0 | agent chính | BUOC0_DOC_TRUOC.md | 1c9db6a7…790bb | PASS (57/57 manifest, 4 hash khớp pin) |
| GĐ1 | RESEARCHER | NGHIEN_CUU_GIAI_DOAN1.md (+ERRATA) | 61b6f68e…468f17 | PASS |
| GĐ2 | PLANNER (agent khác) | KE_HOACH_V2.md | 61188913…0c5d59 | PASS |
| GĐ3 | AUDITOR-1 (agent khác nữa) | AUDIT_KE_HOACH_V2.md | 5bc89e44…c853a2f6 | PASS — verdict **CONFIRMED** |

- Repo input clone `Zedlchoke/edge-hunt-ai-desk` @ `10d3eb7f…`, `shasum -c MANIFEST.sha256` 57/57 OK. Pin FILE spec copytrade v2 `ae504a97…bee55d8` khớp. Cả 4 đầu vào hash khớp pin của chủ.
- 0 request API Polymarket tiêu tốn trong cả chuỗi. 0 chi tiêu. 0 file nguồn/sổ cũ bị sửa (chỉ file mới trong `research/control/PRO-WALLET-V1/`).
- Lỗi vận hành đã lộ và xử lý: agent chính giao sai đường dẫn cutover-prep → RESEARCHER xuất ERRATA, WSL đổi THIẾU → ĐỦ kênh dữ liệu.

## 2. Kết quả chính

- **Phạm vi giải có dữ liệu:** NBA, bóng đá nam, WSL (WSL có sẵn bản đồ `tag_id=105959`, 35 event mở). WNBA nghỉ mùa (~05/2027 mới về), NCAA nam/nữ bóng rổ chưa có bằng chứng thị trường trên đĩa → nằm ngoài, THIẾU DỮ LIỆU; bổ sung sau phải qua bản sửa kế hoạch + kiểm toán.
- **Endpoint có bằng chứng:** Gamma `/markets?include_tag=true` (hoặc `/events?tag_id=` cho WSL) → data-api `/v2/trades` (condition_id hoặc user, taker_only=false), `/v2/activity` (usdc_size), `/v2/resolutions`. Offset-cap 2100 (HTTP 422) → bisection; 500 fill/request; `market=` HTTP 400.
- **Kế hoạch v2 (273 dòng, 11 mục):** định nghĩa pro từng giải, chọn + đóng băng ví TRƯỚC khi thấy kết quả (tách cửa sổ chọn [T_freeze−183d, T_freeze) khỏi cửa sổ chạy bóng), ý kiến reset 00:00 UTC, ngưỡng ≥3 ví + ≥60% tiền pro, sổ bóng append-only 2 file (19 + 14 cột) tách絶 sổ D2, phán xét 4 nhóm + ≥30 trận có ý kiến pro MỖI giải. Mọi ngưỡng dán nhãn **SỐ ĐỀ XUẤT — chờ chủ chốt**.
- **Kiểm toán CONFIRMED:** 22/22 luật khớp, không rò rỉ tương lai, hash toàn bộ 15 đầu vào tự tính lại khớp. 5 phát hiện phụ N1–N5 KHÔNG chặn (chi tiết trong AUDIT_KE_HOACH_V2.md).

## 3. Phát hiện vận hành chủ cần biết

- Trần 200 request/ngày cộng dồn: hôm nay Việc 3 đã dùng 200/200; worker WSL lane còn sống và cũng tiêu Gamma (22 request hôm nay). Mọi thu thập của lane này phải XẾP HÀNG và ĐẾM CHUNG cả hai nguồn trên.

## 4. Vì sao dừng trước Giai đoạn 4 (3 luật cùng hội tụ)

1. Mẫu kiểm toán đóng băng: sau CONFIRMED, chờ CHỦ đọc file audit rồi mới có lệnh GO cho bước tiếp theo.
2. F2 mặc định (a): trần cộng dồn đã hết hôm nay; listing Việc 3 còn ~3 ngày (~08–09/11).
3. KE_HOACH_V2 còn bộ SỐ ĐỀ XUẤT chưa chốt + N1–N5 cần xử lý bằng chữ — thu thập sớm theo ngưỡng chưa chốt dễ tốn ngân sách rồi thu lại.

## 5. Chủ cần quyết để mở Giai đoạn 4

1. Đọc `AUDIT_KE_HOACH_V2.md` + `KE_HOACH_V2.md`; chốt từng SỐ ĐỀ XUẤT (≥3 ví/≥60%, tối đa 30 ví, tổng tiền đặt tối thiểu từng giải, trần 120 request/ngày của lane) và xử lý N1–N5 bằng chữ (sửa chữ → hash mới → nếu đổi luật thì kiểm toán lại).
2. Chọn F2: giữ (a) xếp hàng (mặc định) hay (b) chia trần (ghi số request/ngày cho lane này).
3. Gõ lệnh GO riêng cho GĐ4 (ví dụ: "GO GĐ4 PRO-WALLET-V1 xếp hàng theo (a)").

## 6. Cửa sau đó

GĐ4 (COLLECTOR, xếp hàng) → GĐ5 (AUDITOR-2) → GĐ6 (BUILDER — cần worktree/branch mới `paperdesk-pro-wallet-shadow-v1` + ghi cycle registry, chạy bóng 1 tháng) → GĐ7 CẤM trừ khi có spec áp dụng đóng băng + kiểm toán CONFIRMED + GO riêng của chủ.

---

"Giai đoạn 3 xong (chuỗi hôm nay: Bước 0 + GĐ1 + GĐ2 + GĐ3). Làm được: verify toàn bộ input theo hash, nghiên cứu 6 giải, viết kế hoạch v2, kiểm toán độc lập CONFIRMED, ghi đủ gate log + handoff. Chưa làm được: chưa thu thập dữ liệu (chưa có GO riêng của chủ + trần 200/ngày đã hết vì Việc 3), chưa chốt SỐ ĐỀ XUẤT của kế hoạch v2. Cửa tiếp theo: chủ đọc audit + chốt ngưỡng + chọn (a)/(b) + GO GĐ4."
