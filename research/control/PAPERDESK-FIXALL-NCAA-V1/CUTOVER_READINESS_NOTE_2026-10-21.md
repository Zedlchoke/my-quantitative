# CUTOVER READINESS NOTE — Polymarket quote source (PAPERDESK-FIXALL-NCAA-V1)

> Ngày: 2026-10-21 · Lane: `.worktrees/paperdesk-fixall-ncaa-v1/integration`
> @ `orca/paperdesk-fixall-ncaa-v1-integration` (W0–W2 + W3 đã commit).
> **Cờ `pm_cutover_active` trên production vẫn `false`. NOTE NÀY KHÔNG BẬT
> CỜ — chỉ owner gõ GO riêng mới bật.**

## 1. Trạng thái sẵn sàng (đo tại HEAD này)

| Khoán kiểm | Kết quả | Bằng chứng |
|---|---|---|
| Battery sandbox toàn bộ (gồm PM wiring: 2-way NBA/WNBA, 3-YES soccer/WSL, join-fail → NOT_RUN, quote rows ghi ledger ở cả 2 nhánh, adversarial mapping) | **183/183 × 2 lần chạy liên tiếp** | `tests/papertrade_exec/` (battery 147 gốc + 36 test W0/W1/W2) |
| JS batteries (ai-gate 17/17, seam 43/43, policy 27/27, chart-lifecycle) | Xanh | `apps/paperdesk/test_*.js` |
| Join luật 2-đã-ghim live (NBA) | **PASS** — trận thật hôm nay: ESPN `401909834` Orlando Magic vs Atlanta Hawks → PM event `1191461` "Hawks vs. Magic" (tiêu đề dạng ngắn AWAY-first, join bằng CẢ HAI tên, market `5716400`, outcomes `["Hawks","Magic"]`) | `evidence/PM_LIVE_PROBE_FIXALL_2026-10-21.json` |
| CLOB book-walk live (read-only) | **PASS** — 28 mức giá, best_ask có, book hash ghi evidence | như trên |
| WSL tag scan live (tag ghim `105959`) | **PASS** — thấy sự kiện 1X2 3-market mở (Tottenham vs Arsenal WFC) | như trên |
| Luật phí MỘT NGUỒN (W3.1) | `laws.py` = nguồn duy nhất: pre-cutover `FLAT_FEE_PRE_CUTOVER=0.02`, PM `PM_TAKER_FEE_RATE=0.05·p·(1−p)`; parity JS↔Python test | `laws.py`, `build_laws_js.py`, `test_fixall_w1.py` |
| Chống hỏng dữ liệu trước cutover (W1.4/W1.5) | quote trùng snapshot ⇒ `NOT_RUN_QUOTE_COLLISION`; EV > 100% ⇒ cách ly + cross-check nguồn 2 | `execute.py`, `wsl_lane.py` |

## 2. Nghĩa của câu GO (để owner đọc trước khi gõ)

`GO` cutover **chỉ đổi NGUỒN GIÁ PAPER**: sau GO, quote quyết định của
NBA/WNBA/SOCCER/WSL lấy từ sổ Polymarket (book-walk theo stake thật, phí
taker thật), thất bại join/walk ⇒ `NOT_RUN_PM_QUOTE` fail-closed, KHÔNG
fallback về Odds API. Vẫn là `BET_PAPER` trên sổ giấy — **không có tiền
thật nào di chuyển** (live là hồ sơ riêng, xem LIVE_READINESS.md).

Hai cờ được bật sau GO: `feature_gates.pm_cutover_active: true` trong
`research/papertrade_exec/config.json` (commit riêng, có nhật ký GO phrase
của owner).

## 3. Kế hoạch theo dõi 48h đầu sau GO (W3.3 — chỉ chạy SAU khi owner gõ GO)

1. Tỉ lệ quote PM thành công % + số `NOT_RUN_PM_QUOTE` theo giải (nhìn được
   ở khối League Health — W2.4).
2. So EV hai nguồn trên CÙNG trận (Pinnacle snapshot vs PM walk) — nhật ký
   quote 2 nhánh đã ghi đủ evidence.
3. CLV đo tiếp tục với PM làm giá đóng (luật CLV W2.4 tự chuyển nguồn theo
   quote gần kickoff nhất); Pinnacle giữ vai trò tham chiếu CLV.
4. Chốt chặn W1.4/W1.5 hoạt động cả hai nhánh.

## 4. Rủi ro đã biết (nêu thẳng)

- PM chưa niêm yết mọi trận (soccer nam quốc tế đã đo NOT_RUN_PM_MARKET_NOT_YET_LISTED) → những trận đó KHÔNG vào lệnh sau cutover — đây là hành
  vi đúng (không bịa giá) nhưng làm giảm số lệnh so với nguồn Pinnacle.
- Thanh khoản mỏng ở chân xa ⇒ walk fail-closed ⇒ NOT_RUN (đúng luật).
- Mọi rủi ro snap-shot cũ đã có chặn: PIT law T-6h, hash-lock candidate
  (W4), collision guard (W1.4).

## 5. Việc còn thiếu TRƯỚC khi GO (không chặn GO, nhưng phải biết)

- W4 (cổng AI) chưa nối WSL vào boundary — SAU GO giá PM, WSL vẫn vào lệnh
  như hiện tại (WSL đã chạy PM quote từ trước); khi owner gõ GO thứ hai
  (AI authority) thì W4 phải đã xong.
- NBA đang tạm dừng theo QĐ1 — gỡ sau khi forecast NBA có variance > 0
  trên runner production (W1.3 đã sửa gốc + chặn).
