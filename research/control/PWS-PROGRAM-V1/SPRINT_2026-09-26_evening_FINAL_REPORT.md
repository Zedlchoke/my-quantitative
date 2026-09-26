# FINAL REPORT — PWS discovery sprint tối 2026-09-26 (giới hạn 23:59 +07)

- Bound: `SPRINT_2026-09-26_evening.md` (363cf282). Owner instruction verbatim
  intent 13:41Z: tìm tối đa 2 identity khác cơ chế có walk-forward dương sau
  phí — **mục tiêu tìm kiếm, không phải chỉ tiêu; 0/1/2 đều hợp lệ**.
- Kết luận một dòng: **0 ứng viên backtest — và đó là kết quả đo được, đúng
  gate, không phải thiếu thử.** Không có con số PnL dương nào tối nay vì
  không identity nào vượt được F-0 trên lớp thông tin được cấp quyền; chạy
  backtest cho biến thể family đã chết là đúng lỗi multiple-testing mà
  chương trình chống (Harvey–Liu–Zhu; Bailey) và owner chỉ thị cấm rõ.

## Bảng đếm yêu cầu (trial accounting trung thực)

| Đại lượng | Số | Ghi chú |
|---|---|---|
| Proposed (vào registry) | **1** | PWS-CX-SOLUSDT-I001 (phiên chiều, TAILPAYER-RUN-REGIME) |
| F0-killed | **1** | I001 VETOED_SAME_FAMILY (skeptic + 2×A7 độc lập xác nhận) |
| Frozen | **0** | không identity nào qua F-0 trên cả hai pair |
| Scored | **0** | 0 scored cells mọi cycle (SOL 0/18, BNB 0/18) |
| Dev-pass | **0** | slate rỗng ⇒ không có gì để score |
| OOS-pass | **0** | 0 holdout look, 0 outcome view, S1 SEALED_UNTOUCHED |
| PnL sau phí | **KHÔNG TÍNH** | không scored run nào được chạy — đây là thiết kế của gate, không phải thiếu nỗ lực |
| N_registry | 1/100 | BNB tiêu 0 slot (proposals tự rút sau F-0, precedent P1) |

## Việc đã làm (chuỗi gate)

1. **Đóng SOLUSDT đúng thủ tục** — hai A7 terminal ĐỘC LẬP cùng CONFIRM
   (033c2bef của session song song; da217e72 của sprint này, mọi số tái tính
   exact); two-half close c0ddf816; append-only repair 4ceee776 sau khi
   phát hiện report lane đầu bị ghi đè. **Đúng như owner sửa: 1 identity
   F0-kill trước PnL, slate trống, 0/18 scored — không nói "100 strategy đã
   bác bỏ".**
2. **Kiểm tra pair kế theo luật PWS** — GO-1 BNBUSDT tiêu 14:10Z dưới ủy
   quyền chuỗi GO (GO RECORD ghi cả hai cách đọc ủy quyền + chỉ thị sprint
   13:41Z làm tiebreaker; A7 plan-review 9caac6ba AUTHORIZED_FOR_GO1_GATE
   xác nhận độc lập cách đọc đó). C0 PASS; C1 đo data plane BNB riêng; C2
   CONFIRMED; P1 blind 0/11 hướng sống (5 autopsies; event-layer BNB =
   BLOCKED_NEW_DATA_OWNER_GATE — revival condition R5 cho owner); skeptic
   verify SLATE_EMPTY_VERIFIED bằng số đo trên chuỗi BNB; C3 + verdict;
   A7 terminal CONFIRM_WITH_FINDINGS (3 LOW đã errata); two-half close đầy
   đủ.
3. **Không score, không GO-2, không GO-3** — GO-2 chết UNCONSUMED ở cả hai
   child (SOL vì slate rỗng; BNB vì slate rỗng VÀ cost gate fail-closed:
   spread census NOT_RUN_DISK_CONSTRAINT với df 7GB < 25GB — không thay
   census pair khác).

## Số đo pair-contrast ghi nhận (tài sản)

BNB ≠ SOL về phân phối (klines gapless 57,472 bars; funding median 0,
49.6% zero prints, không deep-print, 0 anomalous spacings; ceiling×power
fee-only 80 episode — không rỗng như SOL nhưng < sàn 100) — nhưng luật
identity (same-family + K-ANC: rho 1.12–2.97× bar 0.20 trên chính chuỗi
BNB) giết class trước khi khác biệt phân phối có ý nghĩa. Asymmetry được
disclosed: leg vs-unconditional không vượt bar trên BNB; K-CONC không
chuyển sang BNB — kill không dựa vào hai thành phần đó.

## GO / S1 / dừng

- GO tiêu: GO-1 SOLUSDT (11:14Z, session chính), GO-1 BNBUSDT (14:10Z,
  sprint này). GO-2/GO-3: chưa từng tiêu. EDGE-SCANNER GO-1 (session song
  song, ngoài phạm vi sprint này, đã dừng trước GO-2).
- S1 SEALED_UNTOUCHED mọi nơi; sealed AUDUSD/USDCAD 2026-H1 không đọc;
  surface ETHUSDT-OPEN-SEARCH-V2 không tiêu.
- **Lý do dừng: hết thông tin mới trên lớp observable được cấp quyền** —
  stop-rule track CX §9(a) kích hoạt (2 pair-child liên tiếp slate rỗng);
  viability council bắt buộc trước pair mới. Giới hạn thời gian respected
  (xong 22:4x+07, trước hard-stop 23:30).

## Cửa tái mở (owner decision — xem OWNER_PACKET §7)

O1 (khuyến nghị): duyệt MỘT information layer mới có authority — ứng viên
đo sẵn **BNB event calendar** (burn quý / SEC-DOJ 2023 / Launchpool) ⇒
DATACOST row + child plan + A7 + council. O2: mở BTCUSDT trên lớp cũ
(không khuyến nghị). O3: disk ≥25GB cho spread census (chỉ sau O1). FX:
chờ reopener R1/R2/R3 bằng chứng bytes.

## Nhãn kết quả

Không có gì hôm nay được gọi là "strategy kiếm lời". Kết quả sprint =
`NO_ELIGIBLE_PROPOSAL` × 2 pair-child, đúng luật, tái lập độc lập 2 lần,
0 contamination OOS. Khi một identity thật sự vượt F-0 + dev gates + GO-2
hợp lệ, nhãn tối đa trong history vẫn là
`CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` (paper-tier) — "có lời trong
giao dịch thật" cần prospective shadow mà không buổi tối nào chứng minh
được.
