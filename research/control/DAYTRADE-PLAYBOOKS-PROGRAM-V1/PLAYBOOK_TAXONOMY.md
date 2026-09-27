# PLAYBOOK_TAXONOMY — DAYTRADE-PLAYBOOKS-PROGRAM-V1 (draft, freeze tại GO-1)

- Authored 2026-09-27 bởi Lead (survey-only; chưa đăng ký cycle, chưa score,
  chưa mở sealed window nào; không đọc nội dung data của bất kỳ worktree nào).
- Nguồn đối chiếu: `research/wayfinder/FAMILY_FAILURES.jsonl` (137 entries),
  `research/wayfinder/MAP.md`, `research/control/SRLV-PROGRAM-V1/
  OUTCOME_EXPOSURE_MAP.md` §4 (hàng rào ancestry), `research/control/
  ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/VIABILITY_cohort3_REPORT.md`
  (12 dead classes FX), `research/control/SRLV-PROGRAM-V1/
  DATACOST_FEASIBILITY_MATRIX.md`.
- Quy ước: mọi định nghĩa phải **constructible từ bar đã đóng** (mức từ close
  của bar đã đóng; pivot confirm ≥1 bar; fill ở quote giao dịch được sau khi
  tín hiệu đã biết; không same-bar high/low ordering — §4.2 master plan).
  "Payer (lore)" = câu chuyện payer mà dân day-trader ngụ ý, KHÔNG phải bằng
  chứng. "Phán quyết tiền-council" = kết luận collision của Lead; council F-0
  vẫn là nơi phán cuối.
- Ký hiệu va chạm: **DEAD** = skeleton trùng family đã chết có bằng chứng đo
  (tên family dẫn chứng); **DEAD-FX** / **DEAD-CX** = chết theo track;
  **BLOCKED** = thiếu dữ liệu bắt buộc; **OPEN-KILLRISK** = chưa có kill trục
  tiếp, nhưng có kill-risk phải đo; **METHOD** = dòng phương pháp, không phải
  identity.

## Bảng 1 — Taxonomy playbook day-trading → đối chiếu family đã chết

| # | Playbook | Định nghĩa constructible (bar đóng) | Payer (lore) | Va chạm FX | Va chạm CX | Phán quyết tiền-council |
|---|---|---|---|---|---|---|
| 1 | **Opening-range breakout (ORB)** — phá đỉnh/đáy khoảng N phút đầu phiên | Range = high/low của N bar đầu phiên (bar đóng); entry khi close bar vượt range + confirm; stop đối diện; flat cuối phiên | Stop-run của trader đứng ngoài phiên; "breakout chaser" trả cho người vào sớm | `FXFV2-A4-P1` Tokyo-compression→London-expansion DEAD (EXPECTANCY_NONPOSITIVE); VIABILITY: "momentum/continuation mọi cadence" dead; "fix-window/clock/calendar" dead | `PSV1-*CONTINUATION` DEAD (CONTROL_OUTEARNED); SPRINT `H-VOLCOMP-BRKOUT` DEAD; `V17-a5-P1-ATTN-PHASE` (US-session continuation) DEAD | **DEAD cả hai track** — mọi biến thể N/bar-confirm là re-clock/re-gate của skeleton range→break→continuation |
| 2 | **Session-compression → expansion** (Asia hẹp → London nổ) | Range phiên A (bar đóng) < ngưỡng; phiên B: entry như #1 | Thanh khoản dồn sau im lặng; hedger vào lúc mở London | `FXFV2-A4-P1` DEAD (đúng family này); `FXFV1-A3-P1` London-open continuation DEAD | như #1 qua skeleton | **DEAD** (FX đo trực tiếp; CX = skeleton #1) |
| 3 | **Break-and-retest** (phá mức rồi quay lại test, vào theo hướng phá) | Mức phá được confirm bởi bar đóng; entry khi bar đóng retest giữ phía phá; stop dưới mức | Người mua/bán trễ tại mức; "FOMO retest" | `FXFV2-A4-P2` London-AM range break + retest-hold DEAD (CONTROL_REPRODUCED); `TRACKA2-C1 RECLAIM-ABSORB` VETO same-family | SRLV class sweep/absorption tại level (`SRLVCX1-M1`) DEAD | **DEAD** (retest = gate cosmetic trên skeleton #1 — P-27 "adding an observable is not a new mechanism") |
| 4 | **Trend pullback** (nhập theo trend intraday: EMA/VWAP pullback) | Trend-state từ bar đóng (vd slope/EMA của khung intraday); entry khi pullback chạm EMA + bar đóng xác nhận theo trend; stop dưới swing | Trader chốt lời sớm trong trend; counter-trend bị stop | VIABILITY: momentum/continuation mọi cadence dead; `H1TSMOM/H1DONCH` ancestry (DINV-1D ANCESTRY_RHO 0.30) | `PSV1-BTC_H4-UPTREND-DONCHIAN` DEAD; BTC-H4-CONTINUATION: KHÔNG có at-entry PIT state tách regime (forensic đo) | **DEAD** — pullback-gate = re-gate của continuation class |
| 5 | **Phản ứng quanh mức giá tròn / psychological (00/50)** | Mức = bội số 50/100 pips (crypto: bội 100/1000); đợi bar đóng chạm + từ chối (rejection bar); entry theo chiều từ chối | Stop-cluster quanh mức tròn bị hunt; LP thu spread | `ROUNDNUM` — **census-family** (census 12 họ EURUSD-OPEN-SEARCH-V1: 12 families × 48 trials, không họ nào sống sót qua gates; không phải row FAMILY_FAILURES — provenance: OUTCOME_EXPOSURE_MAP §1) + VIABILITY range-edge class | SRLV pivot-level absorption DEAD (M1 SETTLE-RESOLVE, cả 2 chiều, inverted out-earns) | **DEAD** — level-reaction skeleton = SRLV/range-edge đã đo chết; crypto thêm PROXY_NOT_ORDERBOOK cho mọi câu chuyện "stop hunt/L2" |
| 6 | **Pivot-point hệ thống** (daily/weekly pivots từ H/L/C ngày trước) | Pivot = công thức từ bar ngày/ tuần ĐÃ ĐÓNG; chờ confirm ≥1 bar tại pivot; entry phản ứng tại pivot | Như #5 | `PDHLOC-C2` — **census-family** (FX-MAJORS-SEARCH-V1: USDJPY thin, drift-confounded, carry-beta control mandatory; provenance: MAP/FX-MAJORS artifacts) + range-fade PIT-seam KILL (TRACKA1-M1: "edge" là lookahead, PIT-clean PF 1.03–1.05 chết ở 1.5×) | như #5 | **DEAD** (và chú ý: bản "sống" GBPUSD/EURUSD cũ đã bị TRACKA1 chứng minh là PIT-seam artifact) |
| 7 | **Range/VWAP-deviation fade (mean reversion intraday)** | Deviation từ anchor (prior range/VWAP proxy từ bar đóng) > ngưỡng; fade về anchor; flat cuối phiên | Người breakout trả cho mean-reverter trong range | `FXOS-04` Bollinger fade 15m — HOLDOUT_FAILURE_NO_RESCUE; `TRACKA1-M1-RANGEFADE-PIT` DEAD (PIT-clean chết 1.5×); `FXFV1-A3-P2` late-NY fade DEAD; VIABILITY mean-reversion oscillators dead | `EOS1` không phải; nhưng SRLV absorption = fade-at-level DEAD; `V16 CLOSE-DISPLACE-FADE` DEAD (PF razor) | **DEAD** — đây là family bị đo kỹ nhất chương trình (3 lần chết độc lập) |
| 8 | **Biến động sau tin (news straddle / fade-after-spike)** | Event window từ lịch có `available_at` THẬT; entry sau khi bar đóng đầu tiên post-event xác nhận direction/reversal | Hedger/retail panicking tại release; dealer widen spread | VIABILITY event/macro dead; `FXNG1/3/4`, `FXFV5/6/7` CPI/revision DEAD mọi dạng; RATES/COMM: release-clock control out-earns — edge thuộc calendar geometry | `CNG1-A4` FOMC-instant DEAD; `CNG2-A4` CPI/NFP-instant DEAD; `V17-A6-P1 FUNDJUMP` DEAD | **DEAD + DATA-GATED** — lịch PIT đủ điều kiện hầu như không có (available_at + revision); mọi re-run là re-clock của dead event class |
| 9 | **Exhaustion / reversal tại level (failed breakout, bull trap, climax volume)** | Failed break: bar đóng quay lại trong range sau khi phá; entry ngược; volume climax = proxy từ klines | Người bắt đuôi breakout trả cho reversal trader | = #5/#7 kết hợp — range-edge fade mọi gate DEAD (TRACKA2-C1C2C3 vetoed same-family) | `SRLVCX1-M1` sweep-then-absorption DEAD (inverted out-earns: settlement adjacency nghiêng continuation); `V17-A6-P2 OICASCADE` DEAD (control out-earns) | **DEAD** — "failed breakout" là đảo nhãn của #1, không phải cơ chế mới (anti-variant §2.3) |
| 10 | **Settlement/funding-adjacent intraday** (funding dodge, settle-hour drift) | Cửa sổ quanh mốc 8h funding; direction từ vị thế funding | Người tránh phí funding | n/a (không có funding FX) | `CNG2-A5-P1/P2` funding-dodge/post-settle DEAD; `SRLVCX1-M1` settle-adjacent DEAD (đo cả 2 chiều); `PWSCXSOL1-I001` funding-run DEAD (representation rho vs CARRY) | **DEAD** — funding-plane fences pair-agnostic (P-29); BNB event-layer (burn/SEC-DOJ) = BLOCKED_NEW_DATA_OWNER_GATE |
| 11 | **Liquidation-cascade / OI-flush continuation** | Cascade proxy từ nến volume/OI khi có | Forced liquidation flow | n/a | Liquidation tape 404; multi-year OI none — `BLOCKED_UNCONSTRUCTIBLE` (bear-recon); `V17-A6-P2 OICASCADE` DEAD; cơ chế "cascade từ nến" = CẤM gọi là forced flow (DATA-FOUNDATION prohibition) | **BLOCKED + DEAD** (cả dữ liệu lẫn family) |
| 12 | **Cross-asset lead-lag intraday (BTC → alt)** | BTC move confirm (bar đóng khung 1m–15m) → vào SOL cùng chiều khi SOL chưa adjust (quote confirm) | Maker/stale quote trên alt book bị adversely select bởi thông tin BTC | `FXFV7-A6-P2` EURUSD lead-lag diffusion DEAD (FOREX, khác asset — base rate context) | **Không có kill trực tiếp trên record** (xsect momentum/reversal dead là cross-sectional daily; `EOS1-E2` ratio-gates dead — khác cấu trúc) | **OPEN-KILLRISK** — kill-risks phải đo: K-ANC representation vs EOS1-E2/xsect-momentum; K-COST ceiling×power grid (RT declared ~11–13 bps vs diffusion capture 1m); payer phải qua fictional-counterparty veto. Ứng viên hợp lệ duy nhất ở dạng "chưa đo" |
| 13 | *(METHOD)* **Discretionary annotated playbooks** | Bộ annotation mù outcome từ nguồn dated (journal/video); rule codify từng setup; mỗi rule chịu F-0 riêng | Theo từng rule codify | n/a (method) | n/a (method) | **METHOD** — route hợp lệ §4.3; kỳ vọng trung thực: đa số rule codify = skeleton #1–#11 ⇒ collision kill; giá trị của route này là ĐO được điều đó thay vì đồn đại |

## Bảng 2 — Tổng quan đủ/thiếu dữ liệu theo pair (kế thừa DATACOST matrix 2026-09-26, re-verify tại GO-1 của child)

| Track | Pair | Dữ liệu giá | Chi phí đo được | Thiếu (chặn) | Trạng thái mở cửa |
|---|---|---|---|---|---|
| CX | SOLUSDT | 1h 2020-09..2026-08 gapless floor-exact; funding 6,580 settlements bit-exact; 1m/15m chưa stage (staging ≤0.5GB OK) | spread census p50 0.469 bps (6-tháng bookTicker); funding MEASURED; fee DECLARED 5bps+1tick | license text chưa capture (gate ghi posture); spread census chỉ 6 tháng — re-verify | `ELIGIBLE_DEV_BASELINE_EXPOSED` — mở đầu |
| CX | BTCUSDT | 1h 2020-01..2026-08; 15m catalog 2024-08+ staged; 1m chưa stage | funding MEASURED 11.798%/yr; fee DECLARED; **spread census NOT_RUN** | spread census; G5 fold-conc unpassable long-biased | `ELIGIBLE_DEV_ANCESTRY_EXPOSED` — thứ 2 |
| CX | ETHUSDT | 1h + funding 2020-01..2026-08 (7,305 settlements) | như BTC | spread census; VA CHẠM ETHUSDT-OPEN-SEARCH-V2 (ACTIVE) | `ELIGIBLE_DEV_ANCESTRY_EXPOSED` — thứ 3 |
| CX | BNBUSDT | 1h 2020-02..2026-08 gapless floor-exact; funding 7,261 | **spread census NOT_RUN_DISK_CONSTRAINT (cần 25GB, disk 6.1GiB)** | spread census | `BLOCKED_COST_CENSUS` — cuối |
| FX | AUDUSD/USDCAD | Dukascopy M1 bid/ask 2021-01..2025-12 (dev) + 2026-H1 SEALED-UNREAD | spread curve sha-pinned (crossing 0.9–1.2 pips; stressed RT 3.6/4.4) | reopener R1/R2/R3/R5 (owner action); commission/financing UNMEASURED | `DORMANT — BLOCKED_FRONTIER_NOT_REOPENED` (score bị chặn; council pre-PnL chỉ chạy nếu owner mở) |
| FX | EURUSD/GBPUSD/USDJPY | Dukascopy M1 bid/ask 2021..2026 outcome-exposed trọn window | spread p50 0.3/0.8/0.5 pip | — (không bao giờ dev/OOS) | `ELIGIBLE_RESTRICTED` — ancestry/fixture/cost authority |
| FX | USDCHF | 0 bytes | — | data + license | `BLOCKED_DATA_LICENSE` (R4-only) |

## Bảng 3 — Hàng rào ancestry trực tiếp lên không gian playbook (đọc trước council)

1. VIABILITY 12 dead classes FX (2026-09-26): range-edge fade mọi gate;
   momentum/continuation mọi cadence; quote/spread-state gates; quote-layer
   observables; fix-window/clock/calendar; cross-pair lead-lag; event/macro;
   carry/multi-day (BLOCKED no financing band); vol-state làm NGUỒN hướng;
   microstructure tape (UNCONSTRUCTIBLE trên M1); mean-reversion oscillators;
   new-pair transfer.
2. Crypto dead-set: 11/11 crypto-ng proposals chết ở rho 0.20; carry
   identity-killed rho 1.0; settlement-adjacent chết cả 2 chiều; funding-run
   gates chết bằng representation math (P-27/P-28/P-29); PSV1 continuation
   CONTROL_OUTEARNED; EOS1-E1/E2; BTC-BEAR double veto (fictional
   counterparty + ancestry); G5 fold-conc 0.50 structurally unpassable cho
   BTC-long 2020-2026.
3. Luật F-0 (owner 2026-09-26): "adding an observable is not a new
   mechanism" — skeleton/payer/information tests chạy TRƯỚC rho, TRƯỚC PnL.
4. Luật owner 2026-09-27: đổi pair/timeframe/session/filter KHÔNG PHẢI
   strategy mới; crypto cấm nến→order-flow/L2; FX cần reopener để score.
