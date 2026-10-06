# OWNER_DECISION_PACKET — FUTURES-DATACONTRACT-QUAL-V1

- Phiên bản 2 + cập nhật r6 (2026-10-03, sau vòng qualification D2-D6; xem
  SUMMARY_QUAL_ACTIONS.md cho verdict PASS/NOT_RUN từng mục). Phiên bản 1 (đề xuất
  D1–D7) nằm trong git history — mọi quyết định dưới đây THAY THÊ menu/đề xuất
  cũ, không chạy song song.
- **PHÁN QUYẾT CO-OWNER (nguyên tắc, chốt):**
  `NO_GO_REGISTER · NO_GO_SCORE · NO_GO_ORDER` — không đăng ký cycle, không
  scored, không S1/paper/live/order, không mua data, không đụng root main,
  không push/merge. Phạm vi còn lại của task: qualification/read-only.

## Quyết định D1–D7 (Co-Owner)

| # | chủ đề | QUYẾT ĐỊNH | hệ quả ghi vào surface |
|---|---|---|---|
| D1 | Slippage | **Giả định nghiên cứu 1 / 2 / 3 tick mỗi chiều** — KHÔNG phải measured cost. Thay thế menu cũ (0.25/0.5/1.0 × tick — đã gỡ). **Không nhân stress trùng lặp**: bộ {1,2,3 tick}/chiều CHÍNH là chiều sensitivity của chi phí; cấm xếp chồng hệ số ×1.5/×2.0 lên thành phần slippage (stress nhân chỉ còn giá trị nếu owner tái lập sau này trên thành phần ĐÃ ĐO) | PLAYBOOKS_DRAFT §1/§4 đã sửa |
| D2 | Exchange fee | **ES-only trước**; xác minh phí **đúng account** của owner (broker LIVE dự kiến = IBKR; đối chiếu theo pricing plan/tier của account + exchange/clearing/regulatory hiệu lực). **Ràng buộc r3: xác minh xong vẫn chỉ cho MODELED COST** — spread close-proxy + slippage {1,2,3 tick} là giả định, **cấm gọi complete/measured cost**; **phân biệt phí lịch sử theo năm với biểu phí hiện tại**. **r6 (D2-FEESRC): bảng public-reference theo plan/tier đã có** — IBKR Fixed 0.85; Tiered 0.85/0.65/0.45/0.25; +exchange 1.386 +regulatory 0.011; all-in tính 2.247 @≤1k; mọi dòng VERIFIED_VS_ACCOUNT=NOT_RUN; NFA đổi 2014/2018; đa số năm lịch sử = CURRENT_SCHEDULE_AS_APPROXIMATION. **Account verification vẫn NOT_RUN — cập nhật r6b: 2 artifact account owner do Co-Owner kiểm (kỳ 2026-10-01..02) chỉ có cổ phiếu, KHÔNG có futures/fee/plan line ⇒ VERIFIED_VS_ACCOUNT giữ NOT_RUN; artifact nhạy cảm KHÔNG vào repo/log**; D6 re-fetch không thay thế account fee evidence | PB1 ưu tiên ES; NQ sibling chỉ sau cost gate; ngôn ngữ modeled-cost áp toàn spec |
| D3 | Holiday | **Lịch CME official historical theo product/year** là authority; ngày không chắc chắn → **EXCLUDE/NOT_RUN** (không inferred-pass). **r6 (D3-CMECAL): ES holidays + early-closes 17/17 năm (2010-2026) authority-backed** — 2026 LIVE_OFFICIAL (fetch sống 2026-10-03; **403 cũ không tái lập — re-measurement có ngày, không phải circumvent**: ≤2 lần/URL, không spoof UA/proxy); 2010 PDF chính thức; 2011-2025 ARCHIVED_OFFICIAL. **Còn thiếu: expirations 2019-2023 + 2026 (36/68 quý có), ES 2026 giờ cụ thể (widget), trích 5 mã CME khác** — không suy diễn lấp gap | Session-filter của mọi playbook buộc theo authority này; tín hiệu PB1 đã đổi sang close era-correct + cờ prev_short |
| D4 | ECB PIT | **Verify 45/55 ngày ECB còn lại** — **XONG r6 (D4-ECBVERIFY): 55/55 machine-verified** (HTTP 200 + title + date-string; 19/19 MRO khớp tuyến phụ; 2020-03-18 = PEPP title variant disclosed) — nhưng **PB2 vẫn HOLD** bất kể kết quả verify | PB2 HOLD không phụ thuộc D4 |
| D5 | Fill/BBO | **Chưa mua BBO.** Đánh giá schema/quote **ES** trước. Ghi nhận luật: **bbo-1m KHÔNG đủ chứng minh intrabar fill/queue** — fill law của mọi playbook giữ conservative (fill = open bar kế, same-bar ambiguity xử lý kín, không claim queue/limit-fill) | PLAYBOOKS_DRAFT §4 điều 8 mới |
| D6 | IBKR re-fetch | **Được phép chạy read-only, tuần tự** — **ĐÃ CHẠY r6 (PASS)**: canary + 24 request tuần tự readonly qua gateway local (không credential); 6 file vào `staging_refetch_20261003/` + sha256 manifest; **0 ghi vào raw/** (ranh giới staging-only được giữ); fronts không đổi; tường expired chưa lùi ở chu kỳ 1 ngày (walls ES/NQ=202509, FX=202512) ⇒ **việc ĐỊNH KỲ hàng tuần**; staging chờ owner/phiên sau promote theo luật | A1 lặp hàng tuần; owner quyết promote staging |
| D7 | 6F | **NOT_RUN_DATA_ABSENT giữ nguyên, chưa mua** — không suy diễn, không thay bằng 6J | Ma trận hypothesis không đổi |

## Trạng thái playbook sau phán quyết (cập nhật vào PLAYBOOKS_DRAFT.md)

- **PB1 (OVN→RTH)**: **ES ưu tiên để hoàn thiện spec** (ES có all-in doc +
  spread 1 tick mỏng nhất + 16.4y); **CONT và REV đăng ký CÙNG lúc** (không
  chọn tail/chiều hậu nghiệm); **NQ sibling chỉ sau cost gate** (D2). Thêm
  ràng buộc spec: **session theo era** (close 16:30/16:15/16:00 CT đúng từng
  giai đoạn — đã đo trong contract §1.2); **luật same-bar TP/SL** (một bar
  chạm cả hai → xử lý deterministic thận trọng, ghi ở spec); **trần 24 scored
  results TỔNG kể cả baseline** — cấu hình phải cắt gọn cho vừa trần, chốt
  chính xác lúc freeze spec.
- **PB2 (London-range→US): HOLD.** Lý do ancestry: **FOREX-FREE-V1/V2 London
  failures** (chuỗi chết của họ London-session trên FX spot). Điều kiện mở
  lại: **mechanism/placebo court** — phân biệt cơ chế so với họ chết (§14.3
  ancestry veto: mechanism + information source + causal control phải khác)
  + placebo court (clock/placebo phải có power phân định) TRƯỚC khi được đề
  nghị đăng ký lại. Verify ECB (D4) không tự mở HOLD.
- **PB3 (RBA-window): PARK.** Lý do: n=67 events trên 6.8y + hai lỗi mở của
  6A chưa giải (tick-size legacy conflict 5e-5 vs 1e-4 chưa adjudicated;
  roll k=5 chưa đo — A7-DC-F3). Không burn budget vào K0 kill đã đoán trước.

## Điểm GO mới (thay mục cũ)

1. Owner hoàn thành D2 (xác minh phí ES đúng account — chỉ cho modeled cost;
   bảng public-reference plan/tier r6 đã sẵn làm tham chiếu) + D3 phần còn thiếu
   (expirations 2019-2023 + 2026; ES 2026 giờ cụ thể; trích 5 mã khác —
   holidays/early-closes ES 17/17 năm đã có r6).
2. **Co-Owner ĐÃ CHỌN A-r4 làm PHẠM VI DỰ KIẾN cho PB1-ES (r5; chưa freeze,
   không phải GO)**: tối đa 24 identity = primary 16 + FOMC sensitivity 4 +
   C1/C2/C3/C4 (placebo đơn seed 20261002 đơn delay — giới hạn đã công bố,
   KHÔNG claim permutation robustness; ±21d giữ descriptive). Thiết kế đầy đủ
   được tách rõ: **D1 = 52** (placebo đơn-delay, nhất quán với dòng C1) và
   **D2 = 53** (placebo cặp delay) — cả hai > 24 ⇒ BLOCKED_TRIAL_BUDGET. Việc
   freeze spec còn cần: D2 (phí ES đúng account, modeled cost) + D3 (lịch CME
   official) + same-bar TP/SL luật kín + era-session/C_prev era-correct + A7
   review.
3. Khi đó mới đề nghị `NO_GO_REGISTER` được xem lại — GO phrase gõ tại gate
   của cycle tương lai, không sớm hơn. Hiện tại: **NO_GO_REGISTER giữ nguyên**.

## Trạng thái repo

- Branch `prep/futures-behavior-10syms-20261002`; các bản cập nhật phiên bản
  2 này commit riêng trên cùng control dir; root main không đụng; không
  push/merge; heavy lock FREE_PROVEN (đo lại trước khi ghi).
