# A7 FINAL VERDICT — PAPERDESK FIXALL + NCAA (gói việc 2026-10-21)

> Auditor độc lập, fresh-context, chỉ đọc code (chạy test được, không sửa
> source). Ngày audit: 2026-10-21. HEAD: `e071c0da` trên branch
> `orca/paperdesk-fixall-ncaa-v1-integration`, base `11da8071`, working tree
> sạch. Vi phạm = dừng việc: audit này KHÔNG tự gõ/tiêu thụ GO nào.

---

# DELTA RE-AUDIT (2026-10-21) — remediation commit `af40456f`

## FINAL VERDICT (delta, áp dụng cho HEAD `af40456f`): **PASS_WITH_FINDINGS — 0 CRITICAL · 0 HIGH · 0 MED · 6 LOW**

Cả 3 MED của vòng A7 gốc (tại `e071c0da`) đã được sửa và verify lại trên
code; 4 LOW gốc vẫn còn nguyên giá trị; remediation thêm 2 LOW mới
(A7-R1, A7-R2). Điều kiện nghiệm thu của gói ("PASS_WITH_FINDINGS không
còn CRITICAL/HIGH/MED") **ĐÃ ĐẠT**.

## Delta battery (2 lượt liên tiếp tại `af40456f`)

| Battery | Kết quả |
|---|---|
| Python run 1: `pytest tests/papertrade_exec/ -q` | **206 passed** in 51.19s, exit 0 |
| Python run 2 (chạy liền) | **206 passed** in 50.11s, exit 0 |

(204 cũ + 2 test remediation mới: `test_a7_m2_league_pause_law`,
`test_a7_m3_weekly_scorecard_job` — test_fixall_w4.py:407-449.)

## Hard laws re-verified tại `af40456f`

Cả hai cờ vẫn `false` (config.json:139,141) · seal vẫn ném
(`apps/paperdesk/main/seal.js:38`) · sổ production vẫn đúng **82 dòng** ·
không có remote branch `paperdesk` (grep -c = 0), 86 commit local-only.

## Remediation verification per MED

**A7-M1 (NCAA artifacts sandbox-plane) — FIXED.**
`_ncaa_plane_dir(args)` (`execute.py:2804-2812`): sandbox ⇒
`<data-root>/sandbox/ncaa`, real ⇒ `<data-root>/ncaa`. Được dùng ở cả 4
điểm ghi/đọc: state load `execute.py:916`, artifacts load `execute.py:924`
(compute_forecasts NCAA), state save `execute.py:2850`, GBM refit
`execute.py:2869` (cmd_ncaa_refresh_state). Grep còn lại: không còn đường
`data_root/"ncaa"` trực tiếp nào ngoài helper. Adversarial (a): sandbox
invocation không thể ghi real plane (helper tách theo `args.sandbox`);
ngược lại real job không thể nhiễm sandbox; seam `ncaa_scoreboard` vẫn bị
chặn `BLOCKED_TEST_HOOK_IN_REAL_MODE` ở real mode. Test W5 refresh đã cập
nhưng đọc đúng `sandbox/ncaa/NCAA-M/state.json`.

**A7-M2 (QĐ1 NBA pause) — FIXED.**
Config `league_pauses.NBA.active=true` kèm `lift_requires` + reason
(`config.json:143-149` — lift chỉ bằng config commit có journal sau khi 1
mẻ NBA production forecast variance > 0). `league_paused(league)`
(`execute.py:115-125`); `cmd_decide` TỪ CHỐI NEW decisions trên REAL plane
TRƯỚC `open_ledger` — `BLOCKED_LEAGUE_PAUSED` (`execute.py:2264-2273`);
sandbox không bị ảnh hưởng. Adversarial (b): pause league-scoped (WNBA/
SOCCER không dính — test khẳng định `league_paused("WNBA") is None`);
settle KHÔNG có pause check (cmd_settle không đụng) — settle tiếp tục đúng
spec; cadence journal `CADENCE_DECIDE_BLOCKED` và các league khác chạy
tiếp (`ops_service.py:1184-1192` — chỉ `BLOCKED_ANCHOR_PASSED` mới break,
`BLOCKED_LEAGUE_PAUSED` không hard-break). Test chứng minh refuse xảy ra
trước khi `open_ledger` được gọi (mock cấm + assert untouched).

**A7-M3 (scorecard) — FIXED.**
`_maybe_weekly_scorecard` (`ops_service.py:1274-1300`): pacing 7 ngày qua
`<state_dir>/ai_scorecard.json`, tính từ verified ledger + opinions_v2,
incident `AI_SCORECARD_COMPUTED` / `AI_SCORECARD_ERROR`, honest 0 khi
chưa có opinion; nối vào tick tại `ops_service.py:1327` (sau
`_ai_pending_watch`, trước heartbeat). Dashboard:
`desk.ai_scorecard` (`ops_service.py:1454-1455`), surface qua
`live_dashboard.py:206`, renderer card có net value + downgrade proposal
(`apps/paperdesk/renderer/app.js:280-303`, guard `|| {}` khi thiếu
payload). `compute_scorecard` read-only (grep: 0 write). Adversarial (c):
không bao giờ chặn tick (try/except toàn hàm; pacing early-return),
ghi ĐÚNG 1 file trong state_dir qua `_atomic_write`.

## Adversarial (d) — slip-up scan trên các hàm bị đụng

Không tìm thấy lỗi kiểu UnboundLocalError: `_ledger_state` trả 3-tuple và
cả 3 caller unpack 3 (`ops_service.py` return + :628/:646/:1286 —
docstring "(core, led)" stale, cosmetic); kwargs khớp chữ ký
`compute_scorecard(*, ledger_rows, opinions_dir)` (`ai_scorecard.py:39`);
renderer guard payload thiếu. **2 residual LOW mới:**

- **A7-R1 (LOW)** — `league_paused` fail-OPEN khi config
  `league_pauses` lỗi shape (`except Exception: return None`,
  `execute.py:124-125`): config hỏng cục bộ → NBA pause tự nhấc im lặng
  trong khi phần còn lại của config vẫn hợp lệ. Nên fail-closed (lỗi đọc
  config ⇒ coi như paused, hoặc raise).
- **A7-R2 (LOW)** — `maybe_wsl` trả về TRƯỚC pause check
  (`cmd_decide`, `execute.py:2258-2261`): nếu ngày nào config pause WSL,
  lane WSL sẽ không tôn trọng (hiện chỉ có NBA trong `league_pauses`,
  không ảnh hưởng hiện tại).

## Tồn tại từ vòng trước (không đổi)

4 LOW gốc A7-L1..A7-L4 giữ nguyên (latent anchor-missing window, quarantine
row churn, constant-block ≥2 rows, pinned-core truncation dependency).
Các mục pending cấu trúc cũng không đổi: production-runner adoption
(2 lệnh NBA kẹt vẫn OPEN trên sổ thật, 82 dòng), W3.3 hậu-GO, NCAA chờ
mùa 11/11 (SEASON_ONLY bootstrap + conf_game gap đã khai), báo cáo tổng
kết `PAPERDESK_FIXALL_NCAA_FINAL_2026-10-21.md` giờ có thể viết trên nền
verdict này.

---

# BASE A7 (tại `e071c0da` — giữ nguyên làm lịch sử)

## VERDICT: **PASS_WITH_FINDINGS**

Counts: **0 CRITICAL · 0 HIGH · 3 MED · 4 LOW.**
Chỉ tiêu nghiệm thu của gói ("PASS_WITH_FINDINGS không còn
CRITICAL/HIGH/MED") chưa đạt tuyệt đối — 3 MED dưới đây cần owner/executor
xử lý trong báo cáo tổng kết, không có mục nào là lỗi tiền/sổ sách.

---

## 1. Battery (chạy lại 2 lượt liên tiếp tại HEAD từ worktree)

| Battery | Kết quả |
|---|---|
| Python run 1: `pytest tests/papertrade_exec/ -q` | **204 passed** in 42.88s, exit 0 |
| Python run 2 (chạy liền) | **204 passed** in 43.16s, exit 0 |
| `node test_ai_gate.js` | **17/17 pass** |
| `node test_ai_seam.js` | **43/43 pass** |
| `node test_paper_policy.js` | **27/27 pass** |

Khớp đúng con số handover W5 (204/204 × 2).

## 2. Bốn luật cứng (hard laws)

1. **Cả 2 cờ false** — VERIFIED. `research/papertrade_exec/config.json:138-142`
   `feature_gates: {ai_authority_active: false, pm_cutover_active: false}`
   kèm law comment "production gates stay OFF until typed GO".
2. **Seal còn ném** — VERIFIED. `apps/paperdesk/main/seal.js:38`
   `throw new Error('SEALED: LiveExecution has no implementation in ...')`;
   không có ví/ký/endpoint đặt lệnh nào được thêm (W6 chỉ là hồ sơ,
   LIVE_READINESS.md, không code).
3. **Sổ production nguyên vẹn 82 dòng** — VERIFIED. `wc -l` và parse JSONL
   cùng cho **82**; 13 BET_PAPER tổng, **3 còn mở** (401909088, 401909090,
   401909836) — gói fix KHÔNG hề ghi vào sổ thật. Replay nghiệm thu W0 chạy
   trên bản sao byte-copy (evidence/W0_ACCEPTANCE_REPLAY_2026-10-21.json:
   settled 2, kept_open 0, chain ok, production untouched).
4. **Không push** — VERIFIED. Branch không có upstream
   (`git branch -vv` — chỉ 2 branch khác có upstream); không tồn tại
   `origin/...paperdesk-fixall...` (grep exit 1); `origin/main..HEAD` = 84
   commit chỉ nằm local.

## 3. Spot-verify các claim rủi ro nhất (file:line)

| Claim | Kết quả | Bằng chứng |
|---|---|---|
| W0.1 settle identity qua crosswalk ghim | VERIFIED | `team_names.py` (norm duy nhất + crosswalk sha-pinned + `same_team` fail-closed); `pins.json:23-27` sha256 khớp shasum thực tế của CSV; CSV = 30 NBA + 15 WNBA team distinct; `results_fetch.py:172-177` so identity qua `same_team` (tên giàu nhất nguồn: displayName hoặc abbr) |
| W1.3 block forecast hằng + fix lookback | VERIFIED | `execute.py:1848-1872` `BLOCKED_CONSTANT_FORECAST`, nối ở **cả hai** decide path (`execute.py:2275`, `wsl_lane.py:872`); fix gốc `execute.py:966-981` refresh lùi `nba_refresh_lookback_days` (config:144, mặc định 14) |
| W1.4 block giá trùng, 2 path | VERIFIED | `execute.py:1877-1906` hai arm (sha bytes / float vector PM); `execute.py:2343-2359` + `wsl_lane.py:909-918` → `NOT_RUN_QUOTE_COLLISION` terminal |
| W1.5 cách ly EV > 100% | VERIFIED | `laws.EV_OUTLIER_THRESHOLD`; `execute.py:2374-2390`, `wsl_lane.py:929-945`; `ev_outlier_disposition` `execute.py:1981-2058` (nguồn 2 cùng >100% → terminal; lệch → cách ly + luật quote tươi + 3 lần → terminal) |
| W4 cổng hash-locked ALLOW\|VETO cả 2 path + luật im lặng | VERIFIED | `apply_ai_gate_v2` `execute.py:2186-2245`; path chuẩn `execute.py:2395-2410`, WSL `wsl_lane.py:950-972` (đường né cổng đã xoá; legacy evaluator có test cấm decide gọi vào); hash qua `build_candidate_hash`; schema cứng `ai_gate_v2.py:77-110` (ALLOW 0 nguồn = INVALID); PENDING tới anchor−30m rồi `NOT_PLACED_AI_NO_VERDICT`; pending >30m → alarm `AI_PROVIDER_DOWN` |
| W5.5 nhãn sự thật khớp nguyên văn owner | VERIFIED | `ops_service.py:88-92` `NCAA_TRUTH_LABEL`; so từng ký tự với text trong `plans/PLAN_paperdesk_fixall_ncaa_v1.md` W5.5: **khớp tuyệt đối 178/178 ký tự** (khác biệt duy nhất là cặp ngoặc kép markdown bao ngoài trong plan; dấu gạch ngang giống hệt) |

## 4. Adversarial checks (6/6 đã làm)

- **(a) Né cổng AI khi bật cờ?** KHÔNG. Đã liệt kê mọi `append_decision`:
  hàng BET_PAPER duy nhất được append ở `execute.py:2412` và
  `wsl_lane.py:978` — cả hai ĐỨNG SAU khối gate; mọi nhánh khác đều
  terminal/cách ly.
- **(b) Guard W1.4 bắt oan giá coarse?** KHÔNG. Arm float chỉ áp hàng
  PM-family (`_pm_family`); arm sha cần payload bytes giống hệt.
  `test_quote_collision_unit` (test_fixall_w1.py:230) phủ đúng ca
  1.85/2.05 lặp hợp lệ → None.
- **(c) Ledger incremental chịu dòng cuối cụt?** Path incremental CÓ
  (`JSONDecodeError → full re-verify`, `ops_service.py:186-188`; JS
  `ledger.js:86-88`); đường full lại dựa vào pinned `load()` ngoài tầm nhìn
  repo → LOW A7-L4.
- **(d) JS ledger không cache chain FAILED?** CÓ — cache chỉ ghi trong
  `if (chain.ok)` (`ledger.js:124-128`), failure withhold toàn bộ tài chính.
- **(e) `settle_last_why` bị cắt lúc settle?** CÓ — `_prune_settle_why`
  `ops_service.py:494-514`, gọi tại :616 và :740 (cả stuck_state).
- **(f) Sandbox NCAA ghi sang plane thật?** Sandbox DAY thì không (ledger
  về `data_root/sandbox/`, forecast chỉ đọc state) — nhưng JOB
  `ncaa-refresh-state` ghi state/artifact KHÔNG có hậu tố sandbox →
  **A7-M1**.

## 5. Findings

### A7-M1 — MED — Ghi state NCAA không tách plane sandbox
`execute.py:2818` ghi `data_root/ncaa/<league>/state.json` và
`execute.py:2836-2837` refit GBM vào `data_root/ncaa/<league>/artifacts` —
không có hậu tố sandbox, trong khi luật sandbox của repo chỉ tách LEDGER
(`execute.py:572-575`). Một lần chạy rehearsal `--sandbox` với seam game giả
nhưng giữ data_root production sẽ ghi đè state thật. Hiện vô hại (real plane
chưa có thư mục `ncaa/`, forecast chỉ đọc, state có digest + artifact sha
để phát hiện drift) nhưng là hazard thật trước mùa 11/11. Sửa: hậu tố
`sandbox/` cho cả state + artifacts, hoặc chặn refresh-state khi
`args.sandbox` trừ khi data_root nằm ngoài plane thật.

### A7-M2 — MED — QĐ1 (tạm dừng NBA) không có law code nào giữ
Không tồn tại pause theo giải trong code — chỉ có cờ pause TOÀN CỤC ngoài
(`pause_decisions.flag`, `ops_service.py:399-413`) và chốt chặn
`BLOCKED_CONSTANT_FORECAST` (đúng failure mode đã biết). QĐ1 đòi "gỡ bằng
thao tác có journal, không im lặng" — thao tác đó chưa tồn tại: sau khi
owner áp HEAD lên runner, NBA tự quay lại vào lệnh ngay khi mẻ forecast có
variance > 0 mà không có dòng journal un-pause nào. Handover W1 đã khai;
cần một law/journal rõ ràng trước khi áp production.

### A7-M3 — MED — W4.5 bảng điểm AI: chỉ có thư viện, chưa có job, chưa có dashboard
`ai_scorecard.compute_scorecard` không được gọi bởi job tuần nào
(grep ops_service/live_dashboard: 0 call site) và không có khối hiển thị;
plan W4 nghiệm thu đòi "dashboard thấy hàng chờ AI + bảng điểm AI" — hàng
chờ CÓ (`ops_service.py:1422`, `live_dashboard.py:204`), bảng điểm
KHÔNG. Đang ngủ vì cờ AI OFF, nhưng trở thành điều kiện chặn trước mọi
GO AI authority.

### A7-L1 — LOW — Cửa sau "anchor thiếu" thu hẹp cửa sổ AI về 0
`execute.py:2217` `if anchor and not ...` — forecast row thiếu
`anchor_utc` → bỏ qua PENDING, đi thẳng `NOT_PLACED_AI_NO_VERDICT` (giết
lệnh ở lần im lặng đầu). Cả 2 lane hiện đều ghi trường này
(`execute.py:1041`, `wsl_lane.py:754`) nên latent; hướng fail-closed.

### A7-L2 — LOW — Cách ly EV append row mới mỗi pass
`execute.py:2313-2341`: khi chưa có quote tươi, mỗi pass decide lại append
một hàng `QUARANTINED_EV_OUTLIER` mới — sổ phình theo nhịp cadence, không
dedup; các hàng này cũng tính vào terminal 3-lần (gộp hai nguồn gốc khác
nhau).

### A7-L3 — LOW — Block forecast hằng cần ≥2 hàng
`execute.py:1862` `len(rows) >= 2` — ngày có đúng 1 trận với p cold-start
hằng sẽ lọt qua block (WNBA/SOCCER/NCAA có ngày 1 trận).

### A7-L4 — LOW — Độ bền dòng-cụt của đường full phụ thuộc pinned core
`ops_service.py:199-205` full re-verify gọi `PaperLedger.load()` ngoài
repo (giới hạn tầm nhìn như audit trước A1); phần trong repo xử lý đúng
(JSONDecodeError → full). Nếu load() raise trên dòng cụt vĩnh viễn → tick
lỗi có journal (TICK_ERROR), không mất dữ liệu.

## 6. Những việc trong gói CHƯA xong hẳn / chỉ xong một phần

1. **Production-runner adoption pending** (cấu trúc, đã khai): 2 lệnh NBA
   kẹt thật vẫn OPEN trên sổ production (đo: 82 dòng, 3 mở). Nghiệm thu W0
   "tự chốt qua đường thường" mới chứng minh trên bản sao; chốt thật chỉ
   xảy ra khi owner áp HEAD này lên runner.
2. **QĐ1 NBA pause** — vận hành, không phải law có journal (A7-M2).
3. **W4.5 bảng điểm AI** — chưa có job tuần, chưa có khối dashboard
   (A7-M3); readiness note AI authority nằm trong báo cáo tổng kết (chưa
   viết).
4. **W5 — các giới hạn đã khai thẳng**: bootstrap SEASON_ONLY (corpus
   2016–2025 là nâng cấp có khai báo, `config.json` ncaa_lanes_note);
   feature `conf_game` = 0.0 + `conference_unknown` khi feed thiếu
   conference ids; mùa 2026-27 chưa bắt đầu (11/11) nên 2 lane chưa từng
   chạy ngày trận thật — chỉ sandbox.
5. **W3.3 theo dõi 48h sau GO** — là việc hậu-GO, đúng thiết kế chưa chạy.
6. **Báo cáo tổng kết `PAPERDESK_FIXALL_NCAA_FINAL_2026-10-21.md`** chưa
   tồn tại — plan §THỰC THI xếp nó cùng bước A7 này; viết sau verdict.

## 7. Tóm tắt per-W

| W | Trạng thái |
|---|---|
| W0 | **XONG** (W0.1–W0.6 đều verify được trong code + replay nghiệm thu trên bản sao; chốt thật chờ adoption) |
| W1 | **XONG** (W1.1–W1.7 verify; 404 WC-group ≤1/ngày, quota theo đơn vị provider, gốc forecast hằng đã sửa + chặn, collision/outlier 2 path, laws một nguồn, storm/metrics/pause-attribution) |
| W2 | **XONG** (incremental 2 tầng parity, cadence song song ≤4 worker + tail-drift retry, một mặt hiển thị, 4 khối dashboard có CLV trung thực NO_CLOSE_PRICE) |
| W3 | **XONG** (một luật phí, readiness note, live probe NBA+WSL có evidence; cờ vẫn false; W3.3 là hậu-GO) |
| W4 | **XONG GẦN HẾT** — W4.1–W4.4, W4.6, W4.7 verify; **W4.5 một phần** (A7-M3) |
| W5 | **XONG với giới hạn đã khai** (label nguyên văn, PM-only quote, state store parity oracle, GBM pin; SEASON_ONLY + conf_game gap + chưa có ngày trận thật) |
| W6 | **XONG** (LIVE_READINESS.md đủ: ví/custody, EIP-712, CLOB order/fill, redeem, allowance/gas, geoblock/KYC, pháp lý; không code, không ví) |

---
*Audit này không tự gõ/tiêu thụ bất kỳ câu GO nào; hai cờ production vẫn
false; sổ production 82 dòng nguyên vẹn; không push.*
