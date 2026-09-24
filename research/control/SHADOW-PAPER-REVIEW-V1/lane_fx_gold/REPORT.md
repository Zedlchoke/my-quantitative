# REPORT — SHADOW-PAPER-REVIEW-V1 / lane_fx_gold

- Vai trò: lane reviewer READ-ONLY (review-analyst), không ghi ledger/registry/manifest,
  không commit, không heavy job.
- Ngày đo: 2026-09-24 (~12:14 UTC). Root checkout `main` @ `f0a8e800c47de1800011d20bccd9bcb2cc7e8546`
  (khớp dispatch). Mọi số dưới đây ĐO TỪ artifact, có path; phần không đo được ghi NOT_RUN.

## 0. Kết luận nhanh (TL;DR)

| Sleeve | Trạng thái đo được | Bằng chứng kế thừa | Cờ chính |
|---|---|---|---|
| EURUSD RANGEFADE-2M | RUNNING, LONG 1.5 lot từ 12:00 UTC 09-24, equity 99,952.00 (−$48 MTM) | Scored S1 12/12, holdout C3 +274 pips | **Short-beta control CHƯA mount** (bắt buộc theo terminal anchor cycle tổ tiên) |
| GBPUSD RANGEFADE-2M | RUNNING, LONG 1.5 lot từ 12:00 UTC 09-24, −$31.5 MTM | FX-MAJORS holdout +164.2@1x, config digest khớp byte-level | Kế thừa đúng — không cần hành động |
| XAUUSD swing | SHADOW RUNNING (pid 4755), 0 entry từ 09-21, equity 100,000, FLAT | Replay 12,337 bar / 9 entry intents (commit d0e983bd) | **Rarity ~1 entry / ~5.1 năm** → sleeve prospective không bao giờ tự đủ bằng chứng; cần sample-size/opportunity-cost law |

---

## 1. Authority và head đo được

- Plans đọc FULL: `plans/PLAN_fx_rangefade_2m_shadow_v1.md` (đăng ký 2026-09-24,
  cycle FX-RANGEFADE-2M-SHADOW-V1, class PROSPECTIVE SHADOW, 1.5 lot/pair,
  force-flat 20:00 UTC, TrueFX indicative, fail-closed) và
  `plans/PLAN_xauusd_shadow_v1.md` (cycle XAUUSD-SHADOW-V1, spec §2 frozen
  4 điều kiện owner + LEAD-FROZEN instantiations, EODHD fail-closed, overlay
  standalone).
- Worktree heads đo được (`git worktree list`):
  - `.worktrees/fx-rangefade-2m-shadow-v1` @ **f8bb2b73** (branch
    `orca/fx-rangefade-2m-shadow-v1`), tree sạch trừ artifact runtime untracked.
  - `.worktrees/xauusd-shadow-v1/integration` @ **d0e983bd** (branch
    `orca/xauusd-shadow-v1-integration`), tree sạch trừ `a7_impl_r1.json` untracked.
- Registry: entry FX-RANGEFADE-2M-SHADOW-V1 (`plans/CYCLE_REGISTRY.json` ~dòng 1869)
  ghi `head: 4bdfd0e4...`, phase REGISTERED, heartbeat 2026-09-24T02:29:14Z —
  **STALE so với head đo được f8bb2b73** (5 commit sau: 6469019c dashboard v2 →
  41af327f Phorec.app builder → 50c7a465 Phorec real macOS app → f8bb2b73 dtype fix).
  Đây là drift registry↔worktree cần Lead cập nhật registry ở gate kế tiếp.
- Process sống (đo `ps`):
  - FX daemon pid **35609**, uptime ~3h51m, chạy đúng
    `.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/daemon/shadow_daemon.py`.
  - XAUUSD worker pid **4755**, uptime 2d23h15m, argv khớp dispatch
    `research/control/xauusd_shadow_v1/xauusd_shadow.py --runtime-root results/xauusd_shadow_v1 --shadow-start 2026-09-21`;
    cwd = `.worktrees/xauusd-shadow-v1/integration` → **runtime nằm trong worktree
    integration** (`…/integration/results/xauusd_shadow_v1/`), KHÔNG phải root `results/`
    (root `results/xauusd_shadow_v1/` không tồn tại).

---

## 2. FX-RANGEFADE-2M (EURUSD + GBPUSD)

### 2.1 Luật strategy đo từ code (frozen chain)

- Signal: `V.f_rangeexp(plane, 0.3, 0.7, False)` —
  `.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/daemon/shadow_daemon.py:129-132`.
  `v2_lib` resolve về FX-MAJORS-SEARCH-V1 trước (sys.path, shadow_daemon.py:31-32).
- Luật C3 (đọc từ `…/FX-MAJORS-SEARCH-V1/scripts/v2_lib.py:267-321`): prior-day range
  xếp percentile trên trailing 60 ngày (searchsorted, :274-283); ngày "wide"
  (pct > 0.7) → **fade**: close > prior-day high → SHORT, close < prior-day low →
  LONG (:308-312); exit khi |close − mid| < range/4 (:314-316); hour gate 07–18 UTC
  (:304). `use_breakout=False` → nhánh narrow-breakout không dùng.
  Diff function body f_rangeexp giữa copy majors và copy EURUSD-OPEN-SEARCH-V2:
  **IDENTICAL** (đo bằng `diff`).
- Execution: signal trên bar H1 CLOSED → fill tại open bar kế ở quote ngược
  (buy@ask/sell@bid) — shadow_daemon.py:214-216 (open), :204-212 (close), :181-203
  (on_closed_bar → desired_now). Force-flat tại close bar 19:00 = 20:00 UTC
  (shadow_daemon.py:304-308); chặn fill mới từ giờ ≥19 (:194-202, :311).
- Sizing: 1.5 lot/pair cố định, $10/pip/lot, 1 tài khoản $100k chung 2 pair —
  `fx_shadow_core.py:32-34`, PnL :42-44, account block :186-212. Gross notional đo
  1.5 × mid × 100k (shadow_daemon.py:228-231).
- Cost book: **duy nhất opposite-quote TrueFX indicative tại fill**; không có
  model commission/slippage — kế hoạch §2 disclose TCU_RISK_DISCLOSED, vendor seam
  Dukascopy→TrueFX bắt đầu tại launch. Spread fill đo được hôm nay: EURUSD 0.4 pip,
  GBPUSD 0.7 pip (`shadow_journal.jsonl` seq 55/57). Tham chiếu spread corpus
  Dukascopy GBPUSD p50 0.8 pip (`…/FX-MAJORS-SEARCH-V1/data_local/GBPUSD/derived/census.json`)
  → indicative không huyền thoại nhưng vẫn là top-of-book không khả-trade.
- Restart identity: journal replay idempotent (`fx_shadow_core.replay_journal`,
  :83-183) — đo được 11 lần boot (`shadow_start` ×11), boot sau cùng 08:19:13Z
  restore 2 bar; parity_selftest **22/22 PASS, 0 FAIL**.
- Độ bền daemon: `daemon.log` chứa **4 traceback crash**; 3 crash đầu (int(Timestamp),
  thiếu json import) sửa trước, crash #4 06:00Z là dtype bug — sửa tại **f8bb2b73**
  (normalize seed ts → `datetime64[ns, UTC]` tại ingest edge, shadow_daemon.py:113-119;
  3 regression tests pin dtype, 26/26 pass theo commit message). Từ boot 08:19:13Z
  daemon sống ~4h, đã qua nhiều hour-roll.
- Runtime hiện tại (`shadow_state.json` 12:13:58Z): equity **99,952.00**
  (realized 0, unrealized −48.00), 2 sleeve LONG 1.5 lot từ 12:00:12 UTC
  (EURUSD @1.13685, GBPUSD @1.32225), gross **$368,822.25 = 368.82%** seed,
  marks fresh, parity PASS.

### 2.2 Short-beta control — TRẢ LỜI: **CHƯA mount**

- Grep toàn bộ code daemon/worktree (`shadow_daemon.py`, `fx_shadow_core.py`,
  dashboard, tests): không có bất kỳ arm control nào (SHORT_ALWAYS / short-beta /
  baseline journal). Các match duy nhất của "control" là HTTP `Cache-Control` và path.
- Nghĩa vụ đến từ đâu (căn cứ gốc):
  - EURUSD-OPEN-SEARCH-V2 terminal (commit bf4f07f1): holdout 2026-H1 C3 +274.0 pips
    nhưng **SHORT_ALWAYS +314.0** — naive short beating chiến lược trên cùng cửa sổ;
    "T1 preregister short-beta control for any paper-forward successor".
  - EURUSD-RANGEEXP-SCORED-V1 terminal (commit 83264434): "short-beta control
    **mandatory** in paper-forward successor" (baselines holdout: LONG −395 /
    SHORT +314 / RANDOM −267.7).
- FX-RANGEFADE-2M-SHADOW-V1 là paper-forward successor trực tiếp của đúng cuốn sách
  EURUSD đó (cùng family RANGEEXP-C3), nên nghĩa vụ T1 áp dụng. Hiện trạng shadow chỉ
  chạy target C3 thuần → **gap compliance với preregistration của cycle tổ tiên**.
- Hệ quả đo được: nếu thị trường 2026-H2 tiếp tục rơi, PnL shadow EURUSD không thể
  tách edge range-fade khỏi short-beta — đúng cái T1 sinh ra để trả lời.
- GBPUSD ít rủi ro drift hơn: holdout FX-MAJORS baselines đều âm (LONG −132.9,
  SHORT −47.1, RANDOM −1,546.9) trong khi C3 +164.2 — mechanism hai chiều trên cửa sổ
  directionless (`…/FX-MAJORS-SEARCH-V1/CYCLE_VERDICT.md`).

### 2.3 GBPUSD kế thừa FX-MAJORS-SEARCH-V1 — ĐÃ mount đúng

- Conviction tổ tiên: GBPUSD `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION — with
  conviction`, arm `GBPUSD-FX2-RANGEEXP-C3` config `{lo_q 0.3, hi_q 0.7,
  use_breakout false}`, config_digest **020e645dbfec2cdc**, holdout 2026-H1
  **+164.2 pips @1.0 (PF 1.1192, 91 trades)**, +105.3 @1.5
  (`…/FX-MAJORS-SEARCH-V1/outcomes/holdout_check_fx.json`).
- Shadow gọi đúng `f_rangeexp(p, 0.3, 0.7, False)` (shadow_daemon.py:132) — khớp
  từng tham số; digest 020e645d cũng trùng candidate C3 của EURUSD-OPEN-SEARCH-V2
  (commit c5987372: "digests 020e645d/548bb2b60"). Function body byte-identical giữa
  hai copy v2_lib (diff đo được).
- Seed GBPUSD dùng đúng corpus sha-verified của FX-MAJORS
  (`shadow_daemon.py:37-41`, trỏ `.worktrees/fx-majors-search-v1/.../data_local/GBPUSD`),
  census 2021-01-03..2026-09-23 (gồm bridge 07..09), 0 ngày missing
  (`census.json`). Parity boot ghi n_bars GBPUSD 32,188 (journal seq 39).

### 2.4 Hạn chế đo được của parity self-test

`parity_selftest` (shadow_daemon.py:257-267) so `targets_from_df()` với chính
`V.f_rangeexp(...)` — tức gọi **cùng một hàm hai lần** nên về bản chất kiểm tra
plumbing ingestion (seed parquet → df → Plane) chứ không đối chiếu với một book
engine tham chiếu độc lập. Plan §1 nói "shadow's H1 targets must equal the backtest
engine's targets" — về chữ đã đúng (f_rangeexp chính là hàm backtest), nhưng độ mạnh
bằng chứng thấp hơn tên gọi "parity". Xem đề xuất #3.

---

## 3. XAUUSD swing (XAUUSD-SHADOW-V1)

### 3.1 Spec thực chạy (daily re-freeze sau F1)

- Plan §2 frozen trên **1h bars**; thực chạy là **daily bars** — re-freeze 2026-09-21
  sau F1: EODHD `/eod/XAUUSD.FOREX` HTTP 200, intraday **403**
  (docstring `xauusd_shadow.py:8-19`; commit b7186674; audit
  `.worktrees/xauusd-shadow-v1/integration/research/control/xauusd_shadow_v1/a7_impl_r1.json`
  ghi rõ re-freeze "NOT back-ported into the plan text").
- Hằng số đo được (`xauusd_shadow.py`): WARMUP 200 (:35), swing fractal ±5 confirm 5
  (:36, :97-112, strict unique extreme, 3-tuple), tie-break |extreme − close_t|
  (F-MED-1, sửa d0e983bd), EMA9/21 first-value-seed (:60-67), volatility floor
  **ATR14 ≥ 0.15% close VÀ ≥ 1.25× median(ATR14 trailing 100)** (:39, :160-163),
  stop 1×ATR14_entry touch completed-bar (:136-139, F-HIGH-1 sửa 8688f73a),
  time stop **20 bars** (:40), cost 4 bps RT (:41), notional 10% equity (:42),
  poll 3600s (:43), CME holidays 2026 embedded (:44-52), UNFILLED_GAP fail-closed
  (F-MED-2), equity fail-closed None khi outage (F-MED-6).
- Fix tie-break d0e983bd ("semantics-identical"): sửa unpack 3-tuple thành 2 gây
  ValueError ngay bar đầu tiên qua vol floor (proven: replay crash tại bar eligible
  đầu 1980-11-10) → entry path trước fix **không bao giờ** record ENTRY; fix 9 dòng
  engine + 103 dòng tests (`tests/test_xauusd_shadow_v1.py`, 4 test đóng 4 điều kiện
  + full replay không raise). Laws strategy/schedule/cost/ledger byte-untouched.

### 3.2 Runtime đo được (từ 09-21)

- `results/xauusd_shadow_v1/status.json` (12:13Z 09-24 trong worktree): equity
  **100,000.0** (= initial), **FLAT**, `data_gaps: []`, `last_error: null`,
  last_bar **2026-09-23** close 4288.8632, n_bars 12,540, ledger_rows 75,
  last_loop 2026-09-24T11:13:02Z (poll kế ~12:13Z — không stale).
- `ledger.jsonl`: **75/75 dòng MARK_TO_MARKET; 0 TARGET_INTENT; 0 FILL** — sleeve
  chưa có quyết định entry nào kể từ 09-21. Sha-chain liên tục
  571f72cd…→b56a4f84; raw_bars snapshot chain GENESIS→25f1646a.
- Overlay 127.0.0.1:8790 sống (`http_server.log`); request lạ
  `GET /api/snapshot.json` 404 (11:01Z) — dashboard khác probe endpoint không tồn
  tại, harmless.
- NOT_RUN: verify độc lập replay 9-intent — `EODHD_API_KEY` không có trong env của
  lane (worker giữ key trong env riêng, không echo) → không fetch được để chạy lại
  SleeveEngine offline.

### 3.3 Bằng chứng rarity

- Nguồn artifact: commit **d0e983bd** message (git evidence, cùng stat 9 dòng
  engine + 103 dòng test) + registry phase XAUUSD-SHADOW-V1
  (`plans/CYCLE_REGISTRY.json` dòng 1269): "full 12,337-bar real replay now clean:
  9 historical entry intents, latest 2011-09-20 — RARITY IS A PROPERTY OF THE
  FROZEN SPEC, disclosed to the owner who ordered fix-only ('nếu hiếm thì thôi')".
  Không tìm thấy file CSV/JSON liệt kê 9 intent riêng biệt — bằng chứng là commit
  message + regression tests + registry, không phải artifact dữ liệu độc lập.

### 3.4 Toán rarity và ý nghĩa thống kê (tính từ replay đo được)

- Tần suất: λ = 9 intents / 12,337 daily bar = **7.30e-4 intent/bar**.
- Bar/năm của gold daily (EODHD full history): 12,337 bar / 45.87 năm
  (1980-11-10 → 2026-09-20) ≈ **269 bar/năm**.
- Kỳ vọng: **1 entry / ~1,371 bar / ~5.1 năm** prospectively.
- Xác suất (Poisson): P(≥1 entry trong 1 năm) = 1 − e^(−0.196) ≈ **17.8%**;
  P(0 entry sau 2 năm) = e^(−0.392) ≈ **67.6%**; kỳ vọng đạt n trade:
  n=3 → ~15 năm, n=5 → ~26 năm, n=10 → ~51 năm.
- Kết luận thống kê: một sleeve shadow chỉ sinh bằng chứng khi có trade; với λ này,
  **không tồn tại горизон thời gian owner-relevant nào để sleeve tự tích lũy bằng
  chứng keep/kill**. Sau 2–3 năm, trạng thái khả dĩ nhất (0 entry) không phân biệt
  được "spec hiếm có chủ đích" với "spec bug/điều kiện mâu thuẫn". Quyết định
  keep/kill vì thế PHẢI dựa trên luật thời gian + study-side, không dựa trên PnL.
- Tại sao entry hiếm (đọc từ spec): prong 1 của vol floor (ATR ≥ 0.15% close) trên
  **daily** bar gần như luôn đúng với gold (ATR daily ~0.8–1.5% giá) — prong ràng buộc
  là **ATR14 ≥ 1.25× median 100 bar** = trạng thái "vol regime breakout"; cộng thêm
  giá phải nằm trong 0.3×ATR của một fractal swing ±5 đã confirm trễ 5 bar, đúng phía,
  và EMA9/21 đồng hướng. Hội 4 điều kiện đồng thời → xác suất joints ~7e-4/bar.
  Lưu ý: floor 0.15% có ý nghĩa trên 1h bar (spec gốc) nhưng gần-vô-nghĩa trên daily
  re-freeze — rarity có thể khác biệt đáng kể nếu owner từng đoán theo spec 1h.

---

## 4. Phân tích khoa học kinh tế (nhiệm vụ D)

### 4.1 Range-fade tại mép range ngày trước (EURUSD/GBPUSD)

- Cơ chế: fade "wide prior-day range" = **cung cấp thanh khoản ngược hướng stop-flow**:
  khi giá xuyên đỉnh/đáy của một ngày có range thuộc top-30% trailing 60 ngày, bên
  kia lệnh là breakout traders + stop-loss clusters (buy-stops trên prior high,
  sell-stops dưới prior low) — lớp flow dễ cạn nhiên liệu trong phiên vì FX spot
  thiếu trend nội ngày bền (trừ ngày tin). Edge tồn tại khi xác suất sweep-fail
  (failed breakout) cao hơn giá của việc thua ở ngày breakout thật sự; chi phí
  đối xứng: ngày trending thật (news, can thiệp NHTW) là ngày fade mất tiền nhiều
  nhất và signal **không có filter regime/vol** — nó chủ động chọn đúng những ngày
  rộng nhất để fade.
- Bằng chứng S0 ủng hộ: GBPUSD holdout directionless với cả 3 baseline âm mà C3 dương
  (mechanism hai chiều) — sạch nhất; EURUSD holdout dương nhưng SHORT_ALWAYS còn dương
  hơn (+314 vs +274) → một phần không đo được của net là short-beta cửa sổ, đúng lý
  do T1 ra đời.
- Chi phí: fill opposite-quote TrueFX indicative (0.4–0.7 pip đo được) so với giá
  khả-trade ECN thực ~0.6–1.2 pip + commission — mark nghiêng lạc quan có disclosed;
  force-flat 20:00 UTC loại swap/overnight gap — phù hợp mô hình liquidity provision
  nội phiên.
- Rủi ro regime: (i) ngày breakout thật liên tiếp (trend regime) → fade liên tục thua;
  (ii) hệ quả đòn bẩy: gross 368.8% trên $100k là đúng chủ trương 1.5×2 lot nhưng
  nghĩa là một ngày 100 pip xấu = −$1,500/pair (−1.5% equity) — paper-only, nếu ai
  đọc dashboard nhầm là quy mô thật thì nguy cơ nhận thức.

### 4.2 Vàng swing multi-year + volatility floor

- Cơ chế đề bài: continuation tại swing level khi vol đủ lớn = trade momentum breakout
  khỏi vùng tích lũy — bên kia là mean-reversion traders bán into strength/fake
  weakness tại swing cũ; edge tồn tại khi gold đang trong regime trend bền
  (real-rate/FX/safe-haven flow) và vol breakout xác nhận continuation.
- Vì sao entry hiếm: xem §3.4 — vol floor 1.25× median là điều kiện trạng thái hiếm
  (chỉ những giai đoạn vol regime chuyển), cộng proximity hẹp 0.3×ATR quanh fractal
  confirm trễ 5 ngày. Câu hỏi mở (không đo được trong lane): floor được calib
  [LEAD-FROZEN] theo regime vol cũ — liệu phân bố ATR của thập kỷ 2010s (vol thấp)
  có làm mốc 1.25× quá gắt cho regime 2020s; đây là câu hỏi study-side, không được
  tune trên dữ liệu sống.
- Phí cơ hội của $100k đứng yên: virtual — nhưng ngay ở cấp quy hoạch, một sleeve
  10% notional, 0.2 trade/năm kỳ vọng, 4 bps RT, không có ước lượng edge nào đo được
  (0 trade mẫu) đóng góp ~0 evidence và ~0 PnL kỳ vọng; chi phí thật là chú ý (attention)
  + nguy cơ owner đọc "FLAT, equity 100,000" thành "chưa có vấn đề gì".

---

## 5. Ý kiến cải thiện (nhiệm vụ E)

### FX-RANGEFADE-2M

1. **Mount short-beta control arm (EURUSD)** — base paper arm SHORT_ALWAYS cùng
   sizing/cửa sổ chạy song song trong cùng journal, ghi như sleeve contribution
   (không đụng engine/laws của C3).
   - Cơ sở: T1 preregistered (bf4f07f1) + terminal scored "mandatory" (83264434);
     shadow hiện tại không thể trả lời câu hỏi mà tổ tiên yêu cầu.
   - Tác động kỳ vọng: sau 1–2 quý có số prospective C3-vs-SHORT_ALWAYS trực tiếp;
     gần như miễn phí (paper, chung feed).
   - Nhãn: **AMENDMENT_REQUIRED** (plan §0 không có arm; thay đổi scope = new plan +
     re-registration) — hoặc OWNER_DECISION_REQUIRED nếu owner muốn waive T1.
   - Rủi ro: thấp; nhầm lẫn hiển thị 2 sleeve trên Phorec cần label rõ CONTROL.
2. **Registry FX-RANGEFADE stale (4bdfd0e → f8bb2b73)** — cập nhật head/phase ở gate
   kế tiếp. Nhãn: **ENGINEERING_ALLOWABLE** (bắt buộc quy trình registry, không đụng
   runtime). Rủi ro nếu không làm: authority pointer sai cho cycle ACTIVE.
3. **Parity fixture tham chiếu độc lập** — pin hash targets từ một lần chạy scored
   engine trên seed window vào test, để parity không còn tautology (§2.4).
   Nhãn: **ENGINEERING_ALLOWABLE**. Rủi ro thấp.
4. **Slippage proxy TrueFX-vs-Dukascopy** — log mỗi fill: spread indicative tại lúc
   fill vs spread corpus cùng giờ lịch sử, để đo độ lạc quan của mark. Nhãn:
   **ENGINEERING_ALLOWABLE**. Rủi ro: chỉ additive journal field.
5. (Ghi nhận, không cần hành động) GBPUSD inheritance đã đúng byte-level; warm-start
   sau restart chờ 1 giờ cho quyết định đầu (`PairBook.last_target=0` chỉ recompute
   khi có bar fresh) — thiên lệch bảo thủ, không vi phạm luật.

### XAUUSD-SHADOW-V1

6. **BẮT BUỘC — Sample-size law / opportunity-cost law** (đề xuất nguyên văn để
   owner phê):
   - KILL_UNFUNDABLE: nếu sau **24 tháng** prospective liên tục (tính từ 2026-09-21,
     tức review lần đầu **2028-09-21**) ledger vẫn 0 TARGET_INTENT, sleeve bị kill
     với lý do "spec không thể kiếm chứng cứ", không cần PnL;
   - kiểm tra giữa kỳ: mỗi checkpoint tuần chạy lại replay identity-identical trên
     window dữ liệu mới nhất (namespace REPLAY_NOT_PROSPECTIVE, không đổi spec) để
     khẳng định rarity vẫn là tính chất spec chứ không phải bug data/collector
     (floor vẫn tính đúng, bar không missing âm thầm);
   - study-side song song (không đổi identity sleeve): mở cycle study riêng đo phân
     bố điều kiện (tần suất từng điều kiện đơn/đôi trên daily gold 1980–2026) để
     trả lời "điều kiện nào ghép ra độ hiếm" — điều này cần data history có sẵn,
     không đụng worker sống; kết quả là đầu vào để owner quyết có sinh cycle mới với
     spec nới (mọi thay đổi params = new owner instruction + new cycle theo frozen law).
   - Nhãn: **OWNER_DECISION_REQUIRED** (luật keep/kill là quyền owner; spec frozen
     cấm tune ngầm).
   - Rủi ro của việc KHÔNG làm: sleeve chạy vô thời hạn, không bao giờ quyết được,
     attention leak + cảm giác giả "an toàn".
7. **Back-port daily re-freeze vào plan text** (plan §2 vẫn ghi 1h bars / time stop
   48; thực chạy daily / 20 bars — a7_impl_r1 đã flag "NOT back-ported"). Spec phải
   là một truth source. Nhãn: **AMENDMENT_REQUIRED**. Rủi ro thấp (văn bản, không
   đụng engine).
8. **Pin kỳ vọng độ dài history fetch** — `fetch_daily_bars(last_n=300)` gửi
   `last=300` nhưng EODHD trả **full history 12,538–12,540 bar** (đo trong
   `raw_bars.jsonl`); identity replay phụ thuộc behavior upstream không contrato.
   Đề xuất: assert `len(bars) >= 12_000` (hoặc ngưỡng spec-được-freeze), dưới ngưỡng
   → DATA_GAP fail-closed thay vì replay window ngắn âm thầm. Nhãn:
   **ENGINEERING_ALLOWABLE**. Rủi ro nếu không làm: nếu EODHD một ngày honor `last`,
   EMA seed + ATR median đổi ngầm → quyết định có thể đổi không ai biết.
9. (Tùy owner) Nếu owner muốn sleeve tradeable: duy nhất đường new cycle với spec
   mới (vd nới proximity, đổi prong floor) — không tune sleeve hiện có. Nhãn:
   **OWNER_DECISION_REQUIRED** (thông tin; spec hiện tại là của owner, không phải defect).

---

## 6. Coverage / NOT_RUN

- Đo được: heads, processes, runtime state, journal/ledger census, parity 22/22,
  crash count 4, config byte-match GBPUSD, spec constants file:line, rarity math,
  census seeds.
- NOT_RUN: (i) verify độc lập replay 9-intent XAUUSD — thiếu `EODHD_API_KEY` trong
  env lane (worker giữ riêng, không echo); (ii) không có artifact dữ liệu liệt kê 9
  intent — bằng chứng là commit d0e983bd + registry + tests; (iii) không đo được
  slippage real-vs-indicative (chưa đủ fills: 2 fill).
- Lane không ghi ledger/registry/manifest; các đề xuất registry ở §5 là khuyến nghị
  cho Lead, không phải thay đổi do lane thực hiện.
