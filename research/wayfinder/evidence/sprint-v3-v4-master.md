# Master Sprint V3→V4 — Final Report (2026-08-24)

```text
V3_PIPELINE_VERDICT : PIPELINE_PASS_CANDIDATE_FAIL
V3_TRANSITION       : V4_AUTHORIZED (19/19 criteria PASS — v3_transition.json)
V4_PIPELINE_VERDICT : PIPELINE_PASS_CANDIDATE_FAIL
V4_FAMILY_VERDICT   : REJECTED
S1_STATUS           : candidate_locked=no · capture_started=no · inspected_or_scored=no

MASTER OUTCOME: V3_PASS_V4_CANDIDATE_FAIL
```

## SPRINT V3 — Execution Truth & Provenance Closure

- Execution: `NEXT_BAR_EVENT_BASELINE` ×98 cells; **17,320 scored entries,
  signal_ts < fill_ts trên 100%**, 0 violations; micro-fixture chứng minh
  fill tại close bar kế tiếp (semantic ghi đúng "next-bar-close", không gọi next-open).
- Position R: initial_risk freeze tại entry; expectancy-R tính được 98/98.
- Provenance launch-time: manifest schema v3 ghi TRƯỚC engine.run; lock-before-run
  fail-closed; argv/commit/dirty thật; fundcrowd lock sửa qua status.yaml có nguồn
  git commit `0bc1a4c` (spec bytes không đổi).
- Gates: G0 98 PASS · G1 98 PASS (evidence-backed, hết hard-code) · G2A 98 PASS ·
  G2b ban đầu NOT_YET_TESTED → **independent reruns: 9/9 families + 2/2 survivors
  = 10/10 PASS** (trades/PnL/fold-digest khớp tuyệt đối).
- Matrix reconciliation: COMPLETE — declared=indexed=files=completed=98, 0 mismatch.
- G3: 96 FAIL · **2 survivors** (funding_crowding ETHUSDT v0/v2: PF 1.45/1.38,
  R +0.47/+0.37, folds 3/3, conc ≤48.8%). Không lock được: G4 stress suite
  NOT_IMPLEMENTED + status.yaml V2 REJECTED stands (không post-hoc rescue).
- V2 hashes: 1281 files snapshot → recheck chỉ registry.jsonl tăng trưởng append-only.

## SPRINT V4 — H-XSECT-MOM-v1 (bounded cross-sectional)

Spec locked trước scored runs (budget 3+1, universe 7 mã, daily 00:00 UTC rank,
long top2 / short bottom2, gross 1.0, |w|≤0.25, skip-if-incomplete).

| Experiment | PnL (USDT) | PF vị thế | Folds F1/F2/F3 | gross_max | beta | MDD |
|---|---:|---:|---|---:|---:|---:|
| XSECT-MOM-3D | −8,056 | 0.976 | −15.1k / −20.9k / +27.9k | **1.275** | −0.027 | 23.7% |
| XSECT-MOM-7D | +9,735 | 1.028 | +4.1k / −19.0k / +24.6k | **1.203** | −0.018 | 30.7% |
| XSECT-MOM-14D | −7,967 | 1.002 | −2.2k / −15.0k / +9.3k | **1.207** | −0.037 | 24.1% |
| REVERSE-7D (control) | −27,171 | 0.931 | — | 1.235 | +0.024 | 36.6% |

Verdicts: 3× REJECTED + 1× CONTROL_ONLY. **Không candidate nào đủ điều kiện lock.**

Đọc kết quả:
1. **Beta-neutral hoạt động**: |beta| 0.02–0.04 ≪ 0.25 — dollar-neutral construction
   đã loại common-beta (nguyên nhân chết của các family V2).
2. **Momentum direction có tín hiệu**: MOM-7D (+9.7k) thắng xa REVERSE-7D (−27.2k)
   → cơ chế ranking có thông tin; NHƯNG risk side thất bại thảm: gross drift
   vượt trần 1.0 tới 1.275 giữa các rebalance (chỉ enforce tại rebalance),
   MDD 24–37% ≫ 10%, fold concentration cực cao (một fold mang toàn bộ PnL).
3. XG0 FAIL do payload mapping coverage/funding chưa khớp schema evaluator
   (đã biết từ V3); XG3 INCONCLUSIVE vì MISSING_R_NORMALIZATION khai báo;
   XG4 INCONCLUSIVE (stress suite chưa build).

## SAFETY

Không live-money change; LIVE guards 11 tests xanh; không đụng enable_trading paths.

## TESTS

`.venv/bin/python -m pytest tests/ -q` → **474 passed / 0 failed / 0 xfailed**
(hành trình: 277 → V3 +88 → V4 +109).

## LIMITATIONS (ghi nhận trung thực)

1. Portfolio closed-leg PnL đang ghi 0.0 (bug hạch toán leg) — PF vị thế portfolio
   chưa đáng tin; total PnL/folds lấy từ equity/cash identity (đúng).
2. Gross exposure chỉ enforce tại rebalance → drift vượt 1.0 giữa kỳ; cần
   intraday de-risking rule hoặc rebalance trigger theo exposure.
3. Commission decomposition null ở ledger V3 (fee nằm trong realized pnl).
4. Stress suite (fee×1.5 / two-tick / delay) chưa build → XG4 INCONCLUSIVE.
5. Expectancy-R ở portfolio level = MISSING_R_NORMALIZATION (legs không có stop
   concept); cần định nghĩa R cho portfolio legs.

## NEXT ACTIONS

P0: fix portfolio closed-leg PnL accounting · intraday gross-exposure clamp ·
build execution-stress harness (fee50/two-tick/delay).
P1: commission decomposition vào ledger · R-normalization cho portfolio legs.
P2: DSR/PBO cho cross-sectional family; mở rộng universe khi có S1 protocol.
