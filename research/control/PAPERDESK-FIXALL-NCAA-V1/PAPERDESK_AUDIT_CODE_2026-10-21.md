# AUDIT CODE — PaperDesk (Paper Trading Thể Thao / Polymarket)

> Auditor độc lập, chỉ đọc, không sửa code. Ngày audit: 2026-10-21.
> Phạm vi: bản sao byte-exact tại `~/workspace/paperdesk-audit/` từ repo `my-quantitative`,
> worktree `.worktrees/sports-papertrade-exec-v1/integration` (HEAD `c4422f8d` theo `docs/HANDOVER_ROUND17_2026-10-21.md`).
> Mức độ: **Nghiêm trọng** = tiền/sổ sách sai hoặc lệnh kẹt vĩnh viễn / app đích không thể đạt · **Cao** = chức năng đích thiếu hoặc sai trong điều kiện thường gặp · **Trung bình** = chậm, dễ vỡ, hoặc thiếu quan sát · **Thấp** = vệ sinh code.

## Giới hạn phạm vi (đọc trước — quan trọng)

1. **Lõi được ghim (pinned core) KHÔNG có trong bản sao.** `execute.py` gọi `core.risk.evaluate_match`, `core.risk.settle`, `core.ledger.PaperLedger`, `core.dashboard.build`, `core.odds_client` từ một worktree khác, chỉ được xác thực bằng sha256 trong `config/pins.json`. Vì vậy công thức EV/stake/settle **đang chạy thật** nằm ngoài tầm nhìn của audit này — mọi nhận định về EV ở mục A đều ghi rõ phần nào kiểm chứng được, phần nào không.
2. **Thư mục tests Python không có trong bản sao** (chỉ có `app_root/test_ai_gate.js`). Con số “147 passed” trong HANDOVER là lời kể của vòng 17, không kiểm chứng lại được tại đây.
3. Một số file phụ (build script, `package.json` đầy đủ của app, launchd plist, CYCLE_REGISTRY) không có trong bản sao. “Không tìm thấy” trong báo cáo này nghĩa là *không tìm thấy trong code đã kéo*, không phải khẳng định tuyệt đối trên máy của chủ sở hữu.

---

## 0. Tổng quan kiến trúc hiện tại

```
┌──────────────────────────── Electron app (macOS) ────────────────────────────┐
│ app_main/main.js ── poll 2s (runner) · 4s (state) · 30s (AI scheduler)       │
│   ├─ runner.js      quản lý ĐÚNG 1 tiến trình Python: attach / spawn /       │
│   │                 SIGTERM có kiểm tra danh tính PID; pause flag (chỉ       │
│   │                 chặn quyết định mới, không chặn settle)                  │
│   ├─ ledger.js      đọc paper_ledger.jsonl + verify chuỗi sha (bản JS)       │
│   ├─ market.js      đọc Gamma/CLOB Polymarket (chỉ hiển thị + bằng chứng AI) │
│   ├─ ai.js          AI SHADOW: OpenRouter free models → opinions/ (sidecar)  │
│   ├─ ai_gate.js     chấm KEEP/VETO/SWITCH/ABSTAIN (bản JS, sandbox/display)  │
│   ├─ paper_policy.js chấm lại cùng bộ cổng (bản JS thứ hai, advisory)        │
│   └─ seal.js        LiveExecution = SEALED (gọi là ném lỗi)                  │
│ app_renderer/       6 màn: Dashboard · Matches · Opportunities · Health ·    │
│                     AI · Laws — nhận state qua IPC, không tự fetch           │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │ spawn / heartbeat.json / /api/state
┌──────────────────────────────────▼── Python service ─────────────────────────┐
│ backend/ops_service.py  vòng tick 30s, TUẦN TỰ: settle → cadence → dashboard │
│ backend/execute.py (2262 dòng)  plan → forecast → quote → decide → settle    │
│   ├─ adapters.py        fixture + engine NBA/WNBA/SOCCER (byte-pinned)       │
│   ├─ wsl_lane.py (948)  lane WSL riêng: forecast PM-only, decide riêng,      │
│   │                     KHÔNG qua cổng AI của execute.py                     │
│   ├─ results_fetch.py   kết quả NBA/WNBA = ESPN · SOCCER = Odds API /scores  │
│   ├─ wsl_results.py     kết quả WSL = Gamma + UMA resolution                 │
│   ├─ pm_moneyline.py / pm_quote_source.py  quote Polymarket (SAU cutover)    │
│   └─ decision_pipeline.py  cổng xác định + cổng AI (bản Python)              │
│ PINNED CORE (ngoài bản sao): ledger hash-chain · risk/EV/stake · dashboard   │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
   Nguồn giá HIỆN TẠI: NBA/WNBA/SOCCER = Pinnacle qua The Odds API (quota)     │
                     WSL = Polymarket Gamma/CLOB (đã live trong paper)       │
   Nguồn giá ĐÍCH:     Polymarket cho mọi giải — code đã viết, cờ đang TẮT     │
```

Luồng dữ liệu một lệnh: `ops_service.tick()` → `cmd_plan` (miễn phí) → `cmd_forecast` (engine ghim, trước anchor) → `cmd_quote` (Pinnacle hoặc PM) → `cmd_decide` (`risk.evaluate_match` của core + cổng AI Python nếu cờ bật) → ghi `DECISION/BET_PAPER` vào `paper_ledger.jsonl` → sau trận `settle_pass` lấy kết quả → `cmd_settle` ghi `SETTLEMENT` (PnL) → dashboard dựng lại từ ledger.

Hai sự thật nền của toàn bộ báo cáo:

- `config/config.json:144-147` — `"feature_gates": {"pm_cutover_active": false, "ai_authority_active": false}`. Cả hai bước nhảy của app đích (giá Polymarket, AI có quyền chặn lệnh) **đều chưa bật**.
- `docs/RUNBOOK.md:3` — *“Scope: paper money ONLY. Live trading is SEALED (no path, no phrase, no key).”* Live thật hiện **không tồn tại dưới bất kỳ dạng nào** (mục E).

---

## A. Vòng đời lệnh: forecast → quote → EV gate → decide → settle → dashboard

**A1 — Nghiêm trọng — Công thức EV đang chạy thật không kiểm chứng được từ repo này.**
`backend/execute.py:1849-1853`: `dec = risk.evaluate_match(led, …, forecast=fc_row, quote=qt.get(f.match_id), …)` — `risk` là pinned core ngoài bản sao. Mọi bản sao của công thức EV tìm thấy trong code đã kéo đều là bản *phụ* (dùng cho AI gate / pipeline sandbox), không phải bản quyết định tiền thật. Hệ quả: câu hỏi “EV 5% đã trừ phí chưa, có đúng không” **không trả lời dứt khoát được** nếu chỉ đọc repo này; phải audit cả worktree `sports-papertrade-v1` (paper core).

**A2 — Cao — Ba định nghĩa “phí” khác nhau cùng tồn tại, EV giữa các nguồn giá không so sánh được.**
- Bản pipeline: `backend/decision_pipeline.py:90` — `ev = (p_leg * d - 1.0 - 0.02)` : trừ phẳng `c = 0.02`. Cùng hằng số này lặp lại ở `app_main/ai_gate.js:46-49` và `app_main/paper_policy.js:132-139` (*“c = 0.02 baked in”*).
- Bản Polymarket: `backend/pm_moneyline.py:215-216,237-238` — phí taker thật của sàn: `fee += 0.05 * price * (1 - price) * take` theo từng mức giá trong sổ lệnh.
- Bản WSL: `backend/wsl_lane.py:362-370` — `d_eff = 1/(vwap_ask + fee_per_share)`, phí `0.05·p·(1−p)` đúng một lần.
Hệ quả: cùng một trận, EV tính theo giá Pinnacle (trừ 2% phẳng — là *ước lượng*, không phải phí Pinnacle thật) và EV tính theo giá PM (phí sàn thật, phụ thuộc giá) sẽ lệch nhau một cách hệ thống. Khi bật cutover, ngưỡng 5% sẽ “đổi nghĩa” mà không có dòng code nào cảnh báo.

**A3 — Trung bình — Ngưỡng EV ≥ 5% nhất quán ở mọi bản sao tìm thấy (điểm tốt), nhưng nằm rải ở ít nhất 4 nơi.**
`backend/decision_pipeline.py:32` `EV_THRESHOLD = 0.05` · `app_main/ai_gate.js:23` · `app_main/paper_policy.js:28` · và bản trong pinned core (không thấy). Không có một nguồn hằng số duy nhất cho cả JS lẫn Python. Đổi ngưỡng trong tương lai rất dễ sót một nơi → hai tầng chấm nhau bằng hai luật khác nhau.

**A4 — Cao — Quote không đồng nhất giữa các giải, và 3/4 giải vẫn phụ thuộc Pinnacle.**
`backend/execute.py:1326,1389,1407+` (`cmd_quote`): cờ tắt → nhánh thật là *“core quota-guarded client”* lấy Pinnacle qua The Odds API cho NBA/WNBA/SOCCER; cờ bật → nhánh PM (`pm_quote_rows_for_fixtures`), fail-closed, *“never an Odds API fallback”*. WSL đi đường riêng hoàn toàn: `backend/wsl_lane.py:18-25` — *“Quote: Polymarket ONLY — three YES binaries … via the byte-pinned polymarket_source”*. Hệ quả thực tế: app đang chạy là một app **lai hai nguồn giá**, và chất lượng/độ trễ quote của 3 giải chính bị trần bởi quota Odds API (mục C4).

**A5 — Trung bình — Anchor (hạn chót ra quyết định) mỗi giải một luật, và AI dùng bản sao của luật này.**
`backend/__init__.py:35-36`: NBA/WNBA `BATCH_LEAD_SECONDS = 6*3600+600` (T0 = trận sớm nhất của cả mẻ ngày, trừ 6h10m) · SOCCER/WSL = kickoff − 6h từng trận (`config/config.json` `anchor_law`). `app_main/ai.js:6-11` tự chép lại hai luật này chỉ để hẹn giờ review. Hệ quả: một trận NBA tip muộn trong ngày bị khoá quyết định theo giờ của trận sớm nhất — đúng luật đã đóng băng, nhưng người vận hành nhìn dashboard sẽ thấy “trận tối nay đã hết hạn quyết định từ trưa” mà không có giải thích tại chỗ.

**A6 — Cao — SOCCER có hai lớp cổng riêng mà giải khác không có: stage law + B1R.**
`backend/execute.py:1817-1847` (trong `cmd_decide`): trận soccer ngoài cửa sổ `competition_law` trong `config/config.json` → `NOT_RUN_STAGE_LAW`; không có forecast B1R hợp lệ → `NOT_RUN_NO_B1R_FORECAST`, terminal. Cộng thêm `soccer_stage_law()` tại `execute.py:282+` và kiểm tra chéo tên đội tại `crosswalk_ok()` `execute.py:1641-1655`. Đây là luật đúng ý đồ, nhưng nó làm vòng đời soccer dài và dễ “chết im lặng” hơn hẳn NBA/WNBA: forecast có, quote có, nhưng decide vẫn NOT_RUN vì thiếu twin B1R.

**A7 — Trung bình — Stake law nhất quán (điểm tốt) nhưng cũng bị nhân bản.**
`config/config.json` `capital_law`: *“stake_cents = (equity_cents + 50) // 100 (1% of equity…)”*, trần mở `open_cap_cents = 50000`. Bản JS chép lại y hệt ở `app_main/pm_stake_law.js:1-10` (10 dòng, chỉ dùng cho book-walk phía app). WSL kiểm tra lại lần thứ ba trong lock: `backend/wsl_lane.py:342-355`. Ba bản cùng một luật, không bản nào import bản nào.

**A8 — Thấp — Idempotence của vòng đời vào lệnh là chắc (điểm tốt).**
`cmd_decide` bỏ qua `f.match_id in decided` (`execute.py:1813-1816`); forecast/quote đều kiểm tra index đã có trước khi ghi; append quyết định có `in_lock_recheck` dưới flock. Chạy lại một tick không sinh lệnh trùng — phần này không có lỗi tìm thấy.

---

## B. Settlement — chốt lệnh đã xong (điểm chủ sở hữu phàn nàn — và phàn nàn là đúng)

Cơ chế hiện tại: `backend/ops_service.py:249-330` (`settle_pass`) chạy đầu mỗi tick: gom `DECISION/BET_PAPER` chưa có `SETTLEMENT`, chỉ lấy trận đã qua `kickoff + grace`, gom theo (giải, ngày), qua cổng throttle mới gọi nguồn kết quả, rồi ghi file kết quả tạm và gọi `execute.cmd_settle`. Nguyên tắc xuyên suốt: **chỉ FINAL + khớp danh tính 1:1 mới chốt; mọi thứ khác giữ OPEN.** Nguyên tắc an toàn — nhưng có một lỗi làm nó gãy ở giải quan trọng nhất, và nhiều đường kẹt không có lối ra.

**B1 — Nghiêm trọng — NBA/WNBA: so sánh tên viết tắt với tên đầy đủ bằng phép bằng chuỗi trực tiếp → lệnh NBA/WNBA kẹt OPEN vĩnh viễn. ĐÃ CÓ BẰNG CHỨNG THẬT.**
`backend/results_fetch.py:129-137`:
```python
abbr = {c["homeAway"]: c.get("team", {}).get("abbreviation") for c in comp["competitors"]}
if abbr.get("home") != row["home"] or abbr.get("away") != row["away"]:
    … "identity mismatch: source {abbr} != ledger {row['home']}/{row['away']} (kept OPEN)"
```
ESPN trả abbreviation (`DET`, `BOS`, `SA`, `OKC`…), ledger ghi tên đầy đủ (`Detroit Pistons`, `Boston Celtics`…). Trong code đã kéo **không có** bảng ánh xạ abbreviation ↔ tên đầy đủ, **không có** hàm chuẩn hoá nào cho đường này (hàm `norm_team` ở `execute.py:1637` chỉ dùng cho crosswalk forecast/quote, không được gọi ở đây). Bằng chứng runtime đi kèm bản sao, `runtime/settle_last_why.json`:
- `"401909088": "identity mismatch: source {'home': 'DET', 'away': 'BOS'} != ledger Detroit Pistons/Boston Celtics (kept OPEN)"`
- `"401909090": "identity mismatch: source {'home': 'SA', 'away': 'OKC'} != ledger San Antonio Spurs/Oklahoma City Thunder (kept OPEN)"`

Hệ quả: **mọi** lệnh NBA (và WNBA khi tên ledger là tên đầy đủ — lưu ý các hàng WNBA cũ trong ledger mẫu ghi sẵn dạng viết tắt `ATL`/`NY`/`LV`/`GS` nên tình cờ khớp; NBA thì không) sẽ không bao giờ tự chốt được. Vốn bị khoá trong “open exposure”, PnL không cập nhật, equity trên dashboard đứng yên — đúng triệu chứng chủ sở hữu mô tả. Đây là lỗi số 1 của toàn hệ thống hiện tại.

**B2 — Cao — Không có đường thoát cho lệnh kẹt: không hạn tuổi, không leo thang, không chốt tay có kiểm toán.**
Tìm khắp `ops_service.py` / `results_fetch.py` / `wsl_results.py`: một lệnh inconclusive chỉ được journal lý do (`SETTLE_KEEP_OPEN`, deduplicate theo chuỗi `why` trong `settle_last_why.json` — lý do không đổi thì **không bao giờ journal lại nữa**). Không tìm thấy: ngưỡng “kẹt > N giờ → báo động riêng”, trạng thái dead-letter, cơ chế void/refund theo tuổi, hay nút thao tác tay trong app. Một lệnh kẹt vì B1 sẽ kẹt *im lặng mãi mãi*.

**B3 — Cao — Độ trễ chốt sổ theo thiết kế đã là hàng giờ, kể cả khi mọi thứ đúng.**
- `backend/results_fetch.py:25` — `SETTLE_GRACE_HOURS = 3`: không xét chốt trước kickoff+3h.
- `backend/ops_service.py:50` — `ESPN_SETTLE_THROTTLE_S = 1800`: mỗi (giải, ngày) tối đa 1 lần fetch / 30 phút.
- `backend/results_fetch.py:26` — `SOCCER_RETRY_MIN_SECONDS = 6*3600`: soccer tối đa 1 lần / 6 giờ (vì `/scores` tốn 1 credit).
Cộng dồn: NBA/WNBA chốt trễ nhất ~3,5 giờ sau trận (nếu B1 được sửa); soccer có thể ~9 giờ. Với yêu cầu “liên tục cập nhật nhanh” của chủ sở hữu, đây là chậm theo luật, không phải lỗi — nhưng phải nói rõ để chủ biết trần hiện tại nằm ở đâu.

**B4 — Cao — SOCCER: trận không đủ điều kiện stage law thì không bao giờ có kết quả, kể cả khi trận đã đá xong.**
`backend/ops_service.py:352-375` (`_fetch_results` nhánh SOCCER): stage law chạy **trước** khi fetch; trận `bet_eligible=False` bị đưa vào `ineligible` (inconclusive) ở mọi lần xét, vĩnh viễn. Không có nhánh “trận đã đá → refund/void”. Tương tự, `/scores` trả `completed != true` hoặc thiếu event id → giữ OPEN vô hạn (`results_fetch.py:233-235`).

**B5 — Cao — WSL: điều kiện chốt UMA quá cứng ở khâu “date_ok / id_ok” từng chân — bằng chứng runtime cho thấy cả loạt trận kẹt vì 1 trong 3 chân lệch ngày.**
`backend/wsl_results.py:125-250` (`fetch_wsl_settleable`): đòi **cả 3** market (HOME/DRAW/AWAY) cùng `closed=True`, `umaResolutionStatus == "resolved"`, giá YES hợp lệ, và identity từng chân (tên đội trong question **hoặc** ngày kickoff trong question). `runtime/settle_last_why.json` ghi hàng loạt `FD-2026-M36…M42`: *“not a finished 90-minute resolution (… DRAW:… date_ok=False …)”* — tức 2/3 chân đã resolved sạch, chỉ chân DRAW thiếu ngày trong câu hỏi PM thì **cả trận không chốt**. Mã nguồn tự ghi nhận PM hay viết market DRAW không kèm ngày (`wsl_results.py` phần identity: *“Polymarket phrases DRAW markets without a date…”*) nhưng điều kiện `leg_ok` cho chân đó vẫn có thể rơi vào `date_ok=False` khi question không chứa cả tên đội lẫn ngày. Hệ quả: WSL — giải được coi là “live tốt nhất” (6/6 đã chốt theo HANDOVER) — vẫn có một họ lệnh kẹt cấu trúc.

**B6 — Trung bình — WSL: `STALE_CORPUS` chỉ là nhãn sức khoẻ, không phải cơ chế hồi phục.**
`backend/wsl_results.py:252-295` (`classify_open_bets`): quá kickoff+2h mà chưa có UMA sạch → `STALE_CORPUS`; `ops_service.py` ghi `state/wsl_settle_health.json` + incident. Nhưng corpus/substrate làm mới là việc *“refreshed by the controller”* (ghi trong `config/config.json` `wsl_lane_note`) — tức phụ thuộc thao tác ngoài vòng tick. Không có tự fetch lại, không có nguồn kết quả dự phòng (ví dụ tỉ số chính thức) trong code đã kéo.

**B7 — Trung bình — ESPN: cửa sổ ngày tìm event hẹp và nhận diện hoãn/huỷ dựa vào chuỗi mô tả.**
`results_fetch.py` `fetch_espn_results`: chỉ tra scoreboard của ngày UTC của trận và **ngày liền trước** (vòng `for offset in (0, 1)`); không thấy event → inconclusive. Hoãn/huỷ chỉ nhận từ `description`/`detail` chứa `POSTPON`/`CANCEL` hoặc `state` đúng chuỗi. Trận dời ngày xa, hoặc ESPN đổi wording, đều thành kẹt OPEN im lặng (kết hợp B2 = không ai biết).

**B8 — Trung bình — NBA/WNBA hoà điểm “completed” bị giữ OPEN vô hạn.**
`backend/results_fetch.py:51-62` `map_completed_to_result`: 2-way mà `home == away` → `None` → inconclusive. Ngoài đời NBA/WNBA luôn có hiệp phụ nên gần như không xảy ra — nhưng nếu nguồn trả tỉ số trước hiệp phụ hoặc lỗi dữ liệu, lệnh kẹt không lối ra (lại B2).

**B9 — Thấp — Phần chốt lõi làm đúng nhiều việc (điểm tốt).**
`execute.py:1959-1997` (`cmd_settle` / `_cmd_settle_standard`): bỏ qua lệnh đã có `SETTLEMENT` (`settled_decision_refs`), kết quả thiếu → giữ OPEN thay vì đoán, refund cho `VOID/PUSH/CANCELLED/POSTPONED_NO_RESCHEDULE` theo `config.json settlement_refund_results`, và WSL còn khoá nguồn kết quả: `wsl_lane.py:921-948` từ chối mọi file kết quả không có `source_ref` bắt đầu bằng `polymarket_uma event=`. Thiết kế chống-chốt-bừa là chắc; vấn đề nằm ở khâu *lấy được kết quả khớp danh tính*, không nằm ở khâu ghi sổ.

---

## C. Tốc độ / tính liên tục

**C1 — Cao — Toàn bộ service là một luồng tuần tự; một khâu chậm chặn mọi khâu sau.**
`backend/ops_service.py:48` `TICK_SECONDS_DEFAULT = 30`; `tick()` tại `ops_service.py:576+` chạy lần lượt `settle_pass()` → `cadence_pass()` → `maybe_rebuild_dashboard()` → heartbeat, rồi ngủ đủ 30s. Không thread, không async, không hàng đợi trong code đã kéo. Một lần fetch ESPN/PM/Odds API treo (timeout 20s ở ESPN, 15s ở AI web connector) cộng dồn thẳng vào độ trễ của mọi giải còn lại.

**C2 — Cao — Nhịp quyết định thực tế là 15 phút, không phải 30 giây.**
`backend/ops_service.py:49` `CADENCE_THROTTLE_S = 900`: mỗi (giải, ngày) tối đa 1 lần chạy plan→forecast→quote→decide mỗi 15 phút; plan cho 4 giải × 3 ngày (hôm nay..+2) cũng bị throttle tương tự và cache trong `plan_cache.json`. Tick 30s chỉ là nhịp *kiểm tra*, không phải nhịp *ra quyết định*. Trận vừa vào cửa sổ anchor hoặc giá vừa nhảy EV sẽ đợi tối đa ~15 phút mới được xét.

**C3 — Cao — Ledger JSONL được đọc lại từ đầu + verify chuỗi sha nhiều lần trong một tick — chi phí O(n) lặp lại, lớn dần theo tuổi sổ.**
- `ops_service.py:240` (`_ledger_state`): `PaperLedger(…).load()` + `verify_chain()` — gọi ở đầu `settle_pass`, và lại ở các đường khác.
- `ops_service.py` `state_fn()` (cuối file): lại `load_pinned_core` + dựng state cho `/api/state`.
- `backend/live_dashboard.py:321+` (`build_state`): *“Every /api/state request re-reads the ledger from disk, verifies the hash chain”* — mỗi request là một lần đọc+verify toàn sổ.
- Phía Electron: `app_main/ledger.js:46` `fs.readFileSync(path)` đọc toàn file rồi verify lại bằng bản JS, theo nhịp poll của `main.js`.
Ở quy mô hiện tại (ledger mẫu 82 hàng) điều này vô hình. Ở quy mô app đích (4–5 giải, chạy liên tục nhiều tháng, hàng nghìn hàng) nó trở thành nút thắt chính: **mọi nhịp đều trả giá theo tổng lịch sử**, không theo phần thay đổi. Không tìm thấy index, offset đọc tăng dần, hay cache theo mtime cho đường Python (chỉ dashboard tĩnh có marker mtime — C5).

**C4 — Nghiêm trọng (cho app đích) — Quota The Odds API là trần cứng của nhịp quote 3 giải chính.**
`config/config.json` `soccer_sport_keys_note`: *“quota caps 4 credits/day + 120/month, journal every call, HALT_KEY on 401/403”*. `execute.py:1407-1440+`: mỗi lần quote là một call tính credit qua `QuotaLedger` của pinned core; hết quota → `QUOTA_SKIP`. Đáng ngại hơn: `execute.py:1614-1632` (`journal_quota_skip`) ghi `QUOTA_SKIP` thành một **hàng DECISION terminal** — mà `cmd_decide`/`cadence` lại bỏ qua mọi match đã có quyết định. Tức một ngày hết quota có thể **đốt vĩnh viễn cơ hội của các trận hôm đó** (không có re-queue sau khi quota hồi). Đây là lý do kiến trúc đích bắt buộc phải qua PM quote (miễn phí, không quota) — và cờ đó đang tắt (A4).

**C5 — Trung bình — Dashboard tĩnh chỉ dựng lại khi ledger đổi hoặc quá 5 phút; hai hệ dashboard cùng tồn tại.**
`backend/ops_service.py:52` `DASHBOARD_MAX_AGE_S = 300` + `maybe_rebuild_dashboard()` kiểm tra mtime. Song song đó `live_dashboard.py` phục vụ trang riêng ở `127.0.0.1:8791` tự refresh 8s (`live_dashboard.py:18`). Electron lại là hệ thứ ba (mục H). Ba đường hiển thị, ba lần verify chuỗi, không đường nào chia sẻ kết quả với đường nào.

**C6 — Trung bình — `plan_cache.json` chỉ cache báo cáo plan, và luật dọn cache mong manh.**
`ops_service.py:390-430` (`cadence_pass`): cache key `cadence:{league}:{date}`, ghi lại mỗi lần fresh, dọn bằng điều kiện so ngày lấy từ `report.date` *hoặc* biến ngày của vòng lặp hiện tại — logic dọn phụ thuộc dữ liệu trong report, dễ giữ rác hoặc xoá nhầm khi report rỗng. Cache này không giúp gì cho quote/forecast (phần tốn credit/thời gian thật).

**C7 — Thấp — Thứ tự tick ưu tiên settle trước cadence (điểm tốt).** Lệnh cũ được xét chốt trước khi sinh lệnh mới trong cùng tick; pause flag của UI cũng chỉ chặn cadence, settle vẫn chạy (`ops_service.py` `tick()`). Thiết kế đúng; chỉ thua ở B1/B3.

---

## D. AI gate — phần lệch xa yêu cầu của chủ sở hữu nhất

Yêu cầu của chủ: *mỗi lệnh mới qua EV ≥ 5% phải luôn có AI đánh giá (search tin/chấn thương/đội hình hoặc tính lại), AI chỉ có 2 lựa chọn: CẤM hoặc CHO PHÉP.*

**D1 — Nghiêm trọng — Hiện tại AI không chặn được bất kỳ lệnh nào. Cả hai tầng đều đang ở chế độ “nói cho vui”.**
- Cờ: `config/config.json:146` `"ai_authority_active": false`; `execute.py:1867` — cổng Python chỉ chạy `if flags["ai_authority_active"] and dec.get("status") == "BET_PAPER"`.
- Phía app: `docs/RUNBOOK.md` §3 — *“let AI affect decisions (SHADOW sidecar only)”* bị liệt vào việc app **không thể** làm; `app_main/ai.js:2` tự ghi *“free-model SHADOW reviewer”*.
Hệ quả: hôm nay, một lệnh EV 30% với tin chấn thương chấn động vẫn vào sổ bình thường; AI có viết gì cũng chỉ nằm ở sidecar.

**D2 — Nghiêm trọng — AI không hề “lên mạng search”. Không có search engine, không có truy vấn tin tức/chấn thương/đội hình trong code đã kéo.**
`app_main/ai.js:262-330` (`captureEvidence`) — toàn bộ “nghiên cứu” của AI gồm đúng 3 thứ, đều đóng gói sẵn trước khi gọi model:
1. trang Gamma Polymarket khớp tên hai đội trong tiêu đề (`ai.js:269-294`, tự ghi *“MATCHED BY TEAM-NAME-IN-TITLE ONLY — NOT fixture-authenticated”*);
2. sổ lệnh CLOB của tối đa 3 market khớp tên đó (`ai.js:296-315`);
3. fetch các URL trong danh sách cho phép qua `AIWebConnector` (`ai.js:113-161`): allow-list cứng 8 domain (`www.bbc.com`, `www.thefa.com`, `wsl-full.com`, `www.espn.com`, `en.wikipedia.org`, `www.fifa.com`, `www.uefa.com`…), trần 5 request/60s.
Và khâu (3) gần như chết: tìm khắp code đã kéo **không có nơi nào cấp URL cho candidate** (không tìm thấy field kiểu `webUrls`/`evidenceUrls` được gán ở `candidates.js`, `main.js` hay backend). Tức bằng chứng web thực tế ≈ rỗng; prompt còn dặn model *“Any URL or source you invent … will be discarded”* (`ai.js:85-89`) và cấm model tự recompute số (`ai.js:92-93`). Đây là thiết kế “AI đọc biên bản hệ thống đưa”, ngược hẳn yêu cầu “AI tự search rồi phán”.

**D3 — Cao — Có tới 5 mảnh AI chồng nhau, không mảnh nào là “cổng” hoàn chỉnh nối đầu-cuối.**
| # | Mảnh | Nơi | Trạng thái thật |
|---|---|---|---|
| 1 | Model caller (OpenRouter free chain) | `app_main/ai.js` (733 dòng) | SHADOW, ghi opinions |
| 2 | Gate enforcer JS | `app_main/ai_gate.js` (`enforceAIGate`, 165 dòng) | Chỉ sandbox/test + display |
| 3 | Policy evaluator JS | `app_main/paper_policy.js` (231 dòng) | Advisory, *“never imported by any ledger path”* (tự ghi trong `POLICY_FREEZE…md` §6) |
| 4 | Gate evaluator Python | `backend/decision_pipeline.py` (`evaluate_ai_gate`) | Chỉ được gọi khi cờ bật |
| 5 | Boundary Python | `backend/execute.py:1661-1890` (`ai_boundary_review`, `_map_ai_opinion`, `load_ai_opinion`) | Cờ tắt = `DISABLED` |
Thêm nữa: `docs/AI_PIPELINE_DESIGN_V1.md` mô tả *“the cadence calls decision_pipeline.run()”* — nhưng trong `decision_pipeline.py` đã kéo **không có hàm `run()` nào**; file chỉ có gate evaluator + candidate hash. Tài liệu đang mô tả một pipeline không tồn tại trong code.

**D4 — Cao — Cầu nối JS → Python là “file mới nhất trong thư mục”, không khoá theo candidate.**
`backend/execute.py:1728-1759` (`load_ai_opinion`): đọc opinion mới nhất cho `match_id` từ `<data_root>/ai_review/opinions/`. Ý kiến được sinh bởi scheduler JS theo nhịp riêng (mục D6), không sinh *trong* luồng decide. Rủi ro cấu trúc: decide chạy trước khi opinion kịp ghi → `ABSTAIN` (khi cờ bật = mất lệnh, xem D5); opinion cũ của một vòng trước được dùng lại nếu vòng mới chưa xong — `_map_ai_opinion` (`execute.py:1690-1726`) chỉ kiểm tra `status == COMPLETED` và hạn chót, không kiểm tra opinion đó thuộc đúng snapshot giá/EV của candidate hiện tại.

**D5 — Cao — Hành vi ABSTAIN/timeout/toàn bộ provider fail: hai tầng, hai hậu quả trái ngược.**
- Tầng JS (hiện hành): `ai.js:549-560,592,638` — mọi model fail → opinion `ALL_PROVIDERS_FAILED` / verdict `ABSTAIN`; hết hạn → `TIMEOUT_LATE_INVALID`. Vì là SHADOW nên **không ảnh hưởng gì** tới lệnh.
- Tầng Python (khi bật cờ): `decision_pipeline.py:167-174` — `ABSTAIN` → `NOT_PLACED`; `execute.py:1886-1890` — mọi kết quả khác `PLACE` đều bị giáng thành `NOT_PLACED_AI_GATE`, `stake_cents = 0`, và đó là **hàng DECISION terminal** (không retry trong ngày). Tức chỉ cần OpenRouter free chain sập một buổi là **toàn bộ lệnh hôm đó chết**, kể cả lệnh EV rất cao — fail-closed đến mức thành fail-deadly. Không có hàng đợi chờ AI, không có hạn “chờ tối đa X phút rồi xét lại trong cửa sổ anchor”.

**D6 — Cao — Ngưỡng kích hoạt AI không phải “EV ≥ 5%”.**
- Scheduler JS: `app_main/main.js:398-430` — cứ 30s lại `buildCandidates` từ ledger+plan rồi `ai.maybeAutoReview(candidates, pm)`; `app_main/candidates.js` dựng candidate theo fixture, **không lọc theo EV**. Đồng thời `main.js:113-115` ghi scheduler *“IDLE while mode is disabled-no-entitlement”* — tức ngay cả việc sinh opinion tự động cũng đang ngủ, chỉ chạy khi có entitlement/mode cho phép.
- Boundary Python: kích hoạt theo `status == BET_PAPER` (tức *sau* khi core đã cho qua EV — gần với ý chủ, nhưng là hệ quả gián tiếp, không phải điều kiện “EV ≥ 5% → gọi AI” được viết ở đâu cả).
Kết luận: không tồn tại trong code một quy tắc *“candidate qua EV 5% ⇒ bắt buộc có một AI review mới, đúng candidate đó, trước khi append”*.

**D7 — Trung bình — Bộ hành động hiện tại (5 verdict × 4 action) phức tạp hơn nhiều so với “Cấm / Cho phép” của chủ, và có một hành động chủ không hề yêu cầu: SWITCH.**
`app_main/ai.js:57` — `VERDICTS = ['APPROVE','VETO','CHALLENGE','ALTERNATIVE','ABSTAIN']`; action: `KEEP|SKIP|SWITCH` (+ `VETO` ở tầng gate). `decision_pipeline.py:188-217`: `SWITCH` cho phép AI **đổi chân cược** sang chân khác nếu chân đó qua lại toàn bộ cổng EV/depth/cap. Đây là quyền lực lớn hơn “Cấm/Cho phép” rất nhiều (AI đổi ý chí của model định lượng), và cũng là bề mặt lỗi lớn nhất của cả hệ AI. Nếu làm đúng spec của chủ, toàn bộ nhánh SWITCH/CHALLENGE/ALTERNATIVE phải bị cắt, chỉ còn `ALLOW` (tương đương KEEP) và `VETO`.

**D8 — Trung bình — Lane WSL không có cổng AI nào cả.**
`docs/HANDOVER_ROUND17_2026-10-21.md` tự ghi: *“WSL AI boundary: the WSL lane's decider is its own module (wsl_lane); the AI boundary wired this round covers the NBA/WNBA/SOCCER decide path… wiring WSL decide into the same gate is a follow-up BEFORE any AI-authority GO.”* Kiểm chứng trong code: `execute.py:1796-1798` — `maybe_wsl(args, "decide")` trả về sớm từ `wsl_lane.cmd_decide`, không đi qua khối AI ở `execute.py:1866+`. Vậy kể cả khi chủ bật cờ AI ngày mai, giải đang chạy tốt nhất (WSL) vẫn vào lệnh không qua AI.

**D9 — Trung bình — Chất lượng model AI hiện tại là free-tier, và prompt cấm AI làm đúng việc chủ muốn.**
`app_main/ai.js:34-57`: chain 5 model `:free` của OpenRouter (minimax-m3.1-flash, gemma-4-31b-it, nemotron-3-ultra, inkling, openrouter/free), key trong macOS Keychain, fallback khi 429/5xx/timeout. Prompt (`ai.js:75-103`): *“You NEVER execute, never modify any number… judge only plausibility and evidence quality”* và cấm bịa nguồn. Với yêu cầu “search chấn thương/đội hình rồi Cấm/Cho phép”, hệ hiện tại thiếu cả ba: công cụ search (D2), quyền phán theo tin (prompt hiện tại chỉ cho phán theo *chất lượng bằng chứng đóng gói*), và model đủ tin cậy cho quyết định tiền (free chain, không SLA, hết quota là ABSTAIN → D5).

**D10 — Thấp — Muốn bật AI thành cổng thật cần gì (liệt kê đúng thứ tự phụ thuộc):**
1. Một câu GO riêng cho AI authority (chưa đăng ký — `POLICY_FREEZE_AI_ACTIONS_V1.md`: *“AI AUTHORITY STATUS: NOT REGISTERED”*) rồi mới được lật `ai_authority_active` (`config.json:146`) — lật cờ chay mà không có GO là trái luật vận hành của chính hệ thống.
2. Nối WSL vào cùng boundary (D8).
3. Thay cơ chế opinion-file-mới-nhất bằng opinion **khoá theo candidate hash** (đã có sẵn hàm `build_candidate_hash` ở `decision_pipeline.py:120-130` nhưng không thấy được dùng để khoá opinion ở đường Python).
4. Thêm tầng search thật (D2) + đổi prompt + bỏ SWITCH (D7).
5. Thêm chính sách chờ/retry trong cửa sổ anchor để ABSTAIN vì hạ tầng không giết lệnh oan (D5).
Thiếu bất kỳ mục nào trong 2–5, “bật cờ” chỉ tạo ra một cổng AI hình thức.

---

## E. Live Polymarket — khoảng cách tới lệnh thật

**E1 — Nghiêm trọng — Live không phải “chưa bật”, mà là “chưa hề được xây”.**
`app_main/seal.js:22-43`: `LIVE_EXECUTION_SEAL` là một object đóng băng mà method duy nhất `submit()` **ném lỗi** *“SEALED: LiveExecution has no implementation in PaperDesk”*. `docs/RUNBOOK.md` §3: app *“CANNOT: … place orders (no endpoint, no credentials — LiveExecution is a sealed type)”*. Tìm khắp code đã kéo: **không tìm thấy** bất kỳ thứ nào sau đây —
- ví / khoá riêng / lưu trữ credential cho giao dịch (chỉ có key Odds API dạng fingerprint và key OpenRouter trong Keychain, cả hai đều không ký được lệnh);
- ký EIP-712 cho CLOB order (không thư viện ký, không typed-data struct);
- endpoint đặt lệnh CLOB (mọi URL PM trong code đều là GET: Gamma events, CLOB book — `pm_moneyline.py:28-30`, `market.js`);
- vòng đời order thật: gửi → chờ fill một phần/toàn phần → huỷ → đối soát fill với ledger;
- redeem/claim sau khi market resolved, cộng hưởng USDC về ví;
- kiểm tra số dư/allowance USDC, gas, địa chỉ proxy wallet;
- kiểm tra pháp lý/khu vực (geoblock) hay KYC cho tài khoản sẽ giao dịch.
`backend/pm_moneyline.py:16` tự ghi: *“Read-only: this module NEVER places orders.”*

**E2 — Cao — Kể cả “GO cutover” cũng không phải live.**
Câu GO được mô tả trong HANDOVER (*“GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER → flips pm_cutover_active: production quotes switch to PM book-walks”*) chỉ đổi **nguồn giá cho paper**. Đừng để tên “cutover” gây hiểu nhầm ở tầng quản trị: sau cutover, hệ vẫn ghi `BET_PAPER` vào ledger giấy, không có đồng tiền thật nào di chuyển.

**E3 — Trung bình — Những gì paper hiện tại *dùng được* cho live (điểm tốt, để khỏi xây lại từ 0):**
- Book-walk theo đúng stake + phí taker thật (E/D ở `pm_moneyline.py`, `wsl_lane.py`) — đây chính là logic định giá/thanh khoản cần cho đặt lệnh thật.
- Joiner khớp event/market/token theo tên đã pin + crosswalk journal (`execute.py` nhánh PM) — là nền của khâu “đặt đúng market”.
- UMA settlement law cho WSL (`wsl_results.py`) — cùng cơ chế resolution mà live redeem sẽ phải chờ.
Thiếu toàn bộ tầng *thực thi và tiền* ở E1; ước lượng trung thực: live là một **dự án riêng** (ví/ký/gateway/xác nhận người/xử lý fill/redeem/audit tiền), không phải một lần lật cờ.

**E4 — Trung bình — Seal có điều kiện mở đã được viết sẵn (điểm tốt về quản trị).**
`seal.js:26-34` liệt kê 4 điều kiện mở live: cycle riêng + GO phrase riêng, delegation gateway với custody ngoài + allow-list + xác nhận từng lệnh, audit độc lập trước launch, chủ tự gõ GO tại cổng của cycle đó. Đây là khung đúng; vấn đề chỉ là chưa điều kiện nào trong 4 điều kiện được thực hiện.

---

## F. NCAA — muốn gắn thêm một lane cần chạm đúng những điểm nào

Đọc đối chiếu `~/workspace/your_files/ncaa-model-full-dossier.md` + `ncaa-model-handoff/` (frozen_test.py, pilot_elo.py, README/AUDIT): mô hình NCAA là GBM trên Elo + hiệu suất ghi điểm, **có trạng thái cập nhật sau từng trận** (Elo K=20, sân nhà +65, kéo 25% về 1500 giữa mùa; efficiency cập nhật bước 0,06), cần lịch + tỉ số D1 nam & nữ từ ESPN/sportsdataverse, và phán quyết tiền: **nam đã CHẾT trước closing line (kiểm toán xác nhận), nữ THIẾU DỮ LIỆU odds**. Tức về mặt sản phẩm, NCAA chỉ nên vào ở chế độ paper/dự đoán — nhưng ngay cả việc đó cũng chưa có lane nào chứa được:

**F1 — Nghiêm trọng — Danh sách giải bị khoá cứng ở nhiều nơi; “thêm vào config” là không đủ.**
- `backend/__init__.py:29` — `LEAGUES = ("NBA", "WNBA", "SOCCER")` (WSL đã phải chui vào bằng ngoại lệ có điều kiện ở khắp nơi — tiền lệ xấu nên tránh lặp lại).
- `backend/execute.py` `LEAGUE_CHOICES` (sau `load_config`), `DEFAULT_SPORT_KEYS` (`execute.py:68-69`), và `fixtures_for()` (`execute.py` nhánh theo từng giải) — mỗi giải là một nhánh `if` riêng.
- `backend/ops_service.py` `DEFAULT_LOOKAHEAD_H` + `_cadence_leagues()` — lookahead và danh sách cadence khai riêng.
Muốn thêm NCAA M/W phải sửa đồng bộ cả 4–5 điểm này (và coi NCAA-Men / NCAA-Women là **hai** lane riêng, vì model, lịch và phán quyết tiền của chúng khác nhau).

**F2 — Cao — Chưa có adapter fixture cho NCAA.**
`adapters.py` có loader cho NBA (ESPN payload theo ngày) và WNBA (CSV lịch tĩnh), soccer (Odds API events). NCAA cần loader mới: lịch D1 (hàng nghìn đội, nhiều trận/ngày, giải đấu cuối mùa + sân trung lập) từ ESPN/sportsdataverse, kèm ánh xạ team-id ổn định. Đây cũng là bài học từ B1: nếu id/tên không chuẩn hoá ngay ở adapter, settlement sẽ gãy hệt như NBA.

**F3 — Cao — Interface engine hiện tại không chứa nổi mô hình có trạng thái của NCAA.**
`compute_forecasts`/`probe_engine` trong `execute.py` giả định engine là một entry `predict.py` byte-pinned, nhận fixture + state digest đóng băng và trả `p_home/p_away` (mẫu WNBA/NBA). Mô hình NCAA cần **state store sống**: sau mỗi trận phải cập nhật Elo/efficiency rồi mới dự đoán trận sau, cộng GBM train lại theo mùa (walk-forward). Không tìm thấy trong code đã kéo: kho state theo đội có version, job cập nhật sau trận, hay cơ chế pin GBM artifact theo mùa. Đây là điểm chạm code lớn nhất của lane NCAA — lớn hơn hẳn khâu fixture.

**F4 — Cao — Chưa có luật anchor, luật giải đấu, và nguồn settlement cho NCAA.**
- Anchor: `anchor_law` trong `config.json` chỉ có NBA/WNBA/SOCCER; NCAA cần luật riêng (mùa thường theo mẻ ngày giống NBA? tournament: nhiều trận cùng ngày, sân trung lập, HCA = 0 — dossier ghi rõ `neutral` là một feature của model, trong khi adapter hiện tại của soccer ép `neutral=False`).
- Settlement: `backend/results_fetch.py:23-24` — `ESPN_LEAGUE_PATH = {"WNBA": "wnba", "NBA": "nba"}`; ESPN college basketball là path khác (men's/women's college basketball) và **vẫn sẽ dính lỗi abbreviation của B1** nếu không sửa trước. Không có nguồn CBBD nào trong code đã kéo.
- Quote: nếu paper theo giá PM thì dùng lại joiner 2-way của `pm_moneyline.py` (điểm tốt — PM có market NCAA); nếu theo closing odds nhà cái thì quay lại bài toán quota Odds API (C4) và phán quyết “nam đã chết” của dossier.

**F5 — Trung bình — Các điểm chạm phụ (dễ quên, quên là gãy lặng):**
`live_dashboard.enrich_matches` (generic theo `league` — điểm tốt, ít phải sửa) · `app_main/candidates.js` + `deadlineFor` trong `ai.js` (bản sao anchor law — phải thêm luật NCAA ở cả JS) · bộ lọc giải trong `app_renderer/app.js` · `dashboard_summary` theo giải ở pinned core (ngoài bản sao — phải kiểm tra core có nhận league lạ không, hay rơi vào “unknown”) · pins.json (thêm package NCAA) · GO/registry riêng nếu muốn NCAA có phrase gate như WSL.

**F6 — Thấp — Điều kiện tiên quyết theo chính dossier:** NCAA nam vào paper phải gắn nhãn rõ “dự đoán, không có edge tiền đã kiểm chứng”; NCAA nữ chưa có benchmark odds. Nếu app hiển thị NCAA cạnh các giải khác mà không gắn nhãn này, dashboard sẽ nói dối bằng cách im lặng.

---

## G. Sức khoẻ code

**G1 — Cao — Monolith `execute.py` 2.262 dòng ôm mọi luật của 3 giải + PM cutover + AI boundary + B1R.**
Forecast, quote hai nguồn, decide, settle, dashboard, plan, pins, capital-law — tất cả trong một file, với trạng thái toàn cục kiểu `_B1R_SWITCH_VERIFIED`, `_B1R_ADAPTER` cache module-level. Hệ quả: mọi thay đổi (ví dụ thêm NCAA — mục F) đều phải phẫu thuật cùng một file với mọi giải đang chạy; review và test chọn lọc rất khó.

**G2 — Cao — Trùng lặp luật JS ↔ Python ở ít nhất 5 cặp, không có cơ chế đồng bộ tự động:**
1. Verify chuỗi ledger: `app_main/ledger.js` + `canonical.js` (JS) ↔ pinned core (Python).
2. EV gate cho AI: `app_main/ai_gate.js` ↔ `app_main/paper_policy.js` ↔ `backend/decision_pipeline.py` (ba bản của cùng một bộ cổng — xem A3/D3).
3. Stake law: `app_main/pm_stake_law.js` ↔ capital law Python (A7).
4. Anchor law: `app_main/ai.js` (bản sao hẹn giờ) ↔ `backend/__init__.py` (A5).
5. Chuẩn hoá tên: `pm_moneyline.py:37-39` `_norm` ↔ `wsl_results.py:47-54` `_norm` ↔ `execute.py:1637` `norm_team` (ba hàm, hai thuật toán khác nhau: một hàm bỏ mọi ký tự không phải `[a-z0-9]`, một hàm chỉ casefold+gộp khoảng trắng — **khác nhau này chính là họ lỗi của B1**).
Điểm cộng: có test parity JS↔Python cho ledger (theo RUNBOOK §6), nhưng không tìm thấy test parity cho 4 cặp còn lại trong bản sao.

**G3 — Trung bình — Đường dẫn cứng theo máy của chủ sở hữu rải khắp nơi.**
`execute.py:54-64` (`PINNED_ROOTS`: 5 đường `/Users/hoangminhlong/my-quantitative/.worktrees/…`) · `wsl_lane.py:61,73` · `config/pins.json` (mọi `worktree`/`path`) · `config/config.json:140-142` (3 đường data WSL) · `app_main/main.js:26-29` (`DEFAULT_DATA_ROOT`, `DEFAULT_WORKTREE`) · `app_main/runner.js:13` (`PYTHON = '/Users/hoangminhlong/my-quantitative/.venv/bin/python'`). Đổi máy, đổi username, hoặc dọn worktree là app chết ở nhiều điểm cùng lúc — và chết theo kiểu `BLOCKED_PIN_DRIFT`/thiếu file khó truy nguyên nhân.

**G4 — Trung bình — Nuốt exception ở các điểm quyết định, một số nuốt thành “hành vi mặc định nguy hiểm”.**
- `backend/execute.py` `capital_law_for`: `except Exception: row = {}` → registry hỏng đọc thành luật vốn v2 (có ghi là chủ ý fail-closed về v2, nhưng v2/v3 khác stake law — một lỗi đọc file có thể âm thầm đổi cỡ stake).
- `ops_service.py:66` `_cadence_leagues`: `except Exception: pass` → lỗi config làm WSL biến mất khỏi cadence không tiếng động.
- `ops_service.py` `reconcile_missed_windows`: `except Exception: continue` theo từng plan — cửa sổ bị bỏ lỡ có thể không bao giờ được journal.
- `app_main/ai.js:318` — `catch (e) { /* evidence capture is best-effort, never fatal */ }`: mất bằng chứng PM lặng lẽ, opinion vẫn chạy tiếp với ít bằng chứng hơn (chỉ được cứu bởi luật “0 evidence → ABSTAIN” khi rỗng hẳn).
- Ngược lại, `tick()` nuốt exception toàn cục rồi journal `TICK_ERROR` (`ops_service.py:636`) — service không chết (tốt) nhưng một lỗi lặp lại mỗi tick sẽ chỉ tồn tại dưới dạng incident, không có bộ đếm/ngưỡng báo động.

**G5 — Trung bình — Test coverage: phần nguy hiểm nhất lại nằm ngoài bản sao.**
Trong bản sao chỉ có `app_root/test_ai_gate.js` (battery JS cho ai_gate). Toàn bộ tests Python (settle identity, crosswalk, quota, WSL UMA, PM join/walk) được HANDOVER kể là 147 test xanh nhưng **không có trong code đã kéo** nên auditor không đối chiếu được test ↔ code. Riêng lỗi B1 cho thấy: hoặc không có test nào cho cặp (abbreviation ESPN, tên đầy đủ ledger) ở NBA, hoặc test đã dùng dữ liệu WNBA dạng viết tắt nên xanh giả. Đây là lỗ hổng coverage nguy hiểm nhất vì nó nằm đúng trên đường tiền về.

**G6 — Thấp — TODO/FIXME/HACK: sạch.** Grep toàn bộ bản sao: không tìm thấy `TODO`/`FIXME`/`HACK`/`XXX` trong code (chỉ có một comment về escape ký tự trong `canonical.js` chứa chuỗi gần giống). Nợ kỹ thuật của hệ này không nằm ở comment dang dở mà ở kiến trúc (G1/G2) và các cờ chưa bật.

**G7 — Trung bình — Heartbeat/stale alarm: có, nhưng ngưỡng lỏng và chỉ ở tầng hiển thị.**
`live_dashboard.py:19` `HEARTBEAT_STALE_S = 180`; renderer báo `STALE (>180s)` ở màn Health. Với tick 30s + cadence throttle 15 phút, một service “còn heartbeat nhưng đứng yên không ra quyết định” vẫn xanh. Không tìm thấy alarm theo *tiến độ công việc* (ví dụ: có trận trong cửa sổ anchor mà 30 phút không có decision nào, hoặc có lệnh quá grace+6h chưa chốt — chính là alarm sẽ bắt được B1/B5 ngoài đời).

**G8 — Thấp — Kỷ luật ghi sổ/audit là điểm mạnh thật của codebase (ghi nhận để giữ khi sửa).**
Hash-chain ledger + verify fail-closed ở cả hai tầng, pin sha256 cho mọi engine/nguồn ngoài, journal raw response cho mọi lần fetch PM/Odds API, incident journal cho mọi lần giữ OPEN/chặn. Khi sửa B1 hay thêm NCAA, đừng đánh đổi những thứ này để lấy tốc độ.

---

## H. Dashboard renderer (Electron)

Hiện có: `app_renderer/app.js` 6 màn — Dashboard (equity, exposure, equity curve qua `chart.js`, KPI), Matches (từng trận: forecast p, quote, EV theo chân, quyết định, PnL, khối AI shadow), Opportunities, Health (runner, heartbeat, stale alarm, incidents, quota/PM probe), AI (opinions shadow), Laws (luật đóng băng). Cơ chế refresh: renderer **không tự fetch** — `preload.js` chỉ nhận broadcast `state` qua IPC; `app_main/main.js:391-439`: poll runner mỗi **2s**, dựng state + broadcast mỗi **4s**, probe Polymarket theo ticker riêng; state mỗi lần dựng lại đọc lại toàn ledger (C3).

**H1 — Cao — Thiếu “hàng đợi lệnh kẹt” — đúng thông tin chủ sở hữu cần nhất lại không có màn nào.**
Không có view nào liệt kê: lệnh OPEN quá hạn chốt (kèm tuổi kẹt + lý do giữ OPEN từ `settle_last_why.json`), lệnh `STALE_CORPUS`/`IDENTITY_UNRESOLVED` của WSL (dữ liệu đã có ở `state/wsl_settle_health.json` phía Python nhưng không thấy được renderer tiêu thụ), hay số lệnh đang chờ UMA. Người vận hành chỉ biết “equity chưa nhảy”, không biết *vì lệnh nào, kẹt ở đâu, từ bao giờ* — B1/B5 vì thế mà sống sót lâu trong thực tế.

**H2 — Cao — Không có CLV ở bất cứ đâu.**
Grep `CLV|closing` trên toàn bộ code đã kéo: **0 kết quả**. Không lưu giá đóng cửa, không so giá vào lệnh với giá chốt của thị trường. Với một hệ đánh giá edge, thiếu CLV nghĩa là thiếu thước đo sớm nhất cho câu hỏi “model có thật sự hơn thị trường không” — PnL thô (đang có) cần rất nhiều lệnh mới nói được điều đó.

**H3 — Trung bình — PnL theo giải có ở tầng dữ liệu Python nhưng mỏng ở tầng Electron.**
`runtime/dashboard_summary.json` (đầu ra của pinned dashboard) có `sport_pnl_cents` theo giải (NBA 0 / WNBA 2215 / WSL 11280…) và `not_run_by_cause`. Renderer Electron chủ yếu hiển thị equity tổng + PnL từng trận; không thấy bảng tổng hợp theo giải × trạng thái (BET/NO_EDGE/NOT_RUN theo nguyên nhân) tương đương bản Python trong 6 màn đã kéo. Hệ quả: không nhìn được “giải nào đang kiếm tiền, giải nào đang chết vì hết quota/stage law” trong một chỗ.

**H4 — Trung bình — Ý kiến AI hiển thị như một bảo tàng, không nối với kết quả lệnh.**
Màn AI và khối AI trong Matches cho thấy opinion/verdict shadow; nhưng vì D1/D6, không có cột “AI nói gì → lệnh có vào không → kết quả ra sao”, không có thống kê AI đúng/sai theo thời gian. Khi AI được trao quyền thật, dashboard hiện tại không có chỗ để *kiểm chứng* AI — điều kiện tiên quyết để tin một cổng tự động.

**H5 — Trung bình — Sức khoẻ từng lane chưa tách.**
Màn Health gộp runner/heartbeat/incidents thành một khối chung. Không có thẻ riêng từng giải kiểu: lần forecast/quote/decide thành công gần nhất, quota Odds API còn lại hôm nay/tháng (dữ liệu có ở `live_dashboard` phía Python — `state["quota"]` — nhưng không thấy ở renderer Electron đã kéo), số trận sắp tới trong cửa sổ, lỗi đặc thù của lane (B1R, stage law, STALE_CORPUS). Một lane chết lặng (ví dụ WSL biến mất khỏi cadence vì G4) sẽ không lộ diện.

**H6 — Thấp — Hai dashboard song song dễ gây hiểu nhầm số liệu.**
Trang `live_dashboard.py` (127.0.0.1:8791, refresh 8s) và app Electron (broadcast 4s) dựng state bằng hai đường code khác nhau từ cùng một ledger. Khi hai nơi lệch nhau (thời điểm verify, cách tính wallet), không có dấu hiệu nào cho người dùng biết nên tin nơi nào. App đích nên còn đúng một mặt hiển thị.

**H7 — Thấp — Điểm tốt:** chain-tamper thì app giấu toàn bộ số liệu tài chính và hiện banner (fail-closed, `ledger.js` + RUNBOOK §6), phân biệt SANDBOX/REAL theo GENESIS row, và màn Laws liệt kê rõ các việc bị cấm (kể cả “AI ảnh hưởng quyết định” đang bị cấm) — tính trung thực hiển thị của app hiện tại cao hơn mặt bằng chung; các mục H1–H5 là *thiếu tính năng quản trị*, không phải hiển thị sai.

---

## Bảng đối chiếu 5 điểm app đích

| # | Điểm app đích của chủ sở hữu | Trạng thái | Căn cứ chính |
|---|---|---|---|
| 1 | Mở app là tự chạy (paper), đang paper NBA/WNBA/WSL/soccer nam | **Có một nửa** | Runner 1-tiến-trình, attach/spawn/takeover chắc (`runner.js`, RUNBOOK §2); nhưng app *không* tự chạy ở login sau takeover (chủ ý), 3/4 giải vẫn quote Pinnacle chứ không phải PM (A4), và vòng đời từng giải lệch nhau (A6, D8) |
| 1b | Gắn thêm NCAA M/W | **Chưa có** | Không lane, không adapter, không engine-state, không anchor/settlement law (F1–F4); model đã có sẵn ở handoff nhưng chưa tích hợp; phán quyết tiền: nam CHẾT, nữ THIẾU DỮ LIỆU → chỉ nên vào dạng paper-dự đoán có gắn nhãn (F6) |
| 2 | Liên tục cập nhật + tính toán nhanh mọi thứ | **Có một nửa** | Tick 30s nhưng quyết định throttle 15 phút (C2), service đơn luồng tuần tự (C1), ledger đọc+verify toàn bộ ở mọi nhịp (C3), quota Odds API 4 credit/ngày là trần cứng (C4) |
| 3 | Lệnh đã xong tự kiểm tra kết quả → chốt sổ → cập nhật vốn | **Có một nửa — và đang gãy ở NBA** | Khung settle đúng và an toàn (B9) nhưng lỗi abbreviation làm NBA kẹt vĩnh viễn, đã có bằng chứng runtime (B1); WSL kẹt theo họ vì điều kiện date/id từng chân (B5); soccer stage-law không có đường refund (B4); không cơ chế thoát kẹt/báo động theo tuổi lệnh (B2, G7) |
| 4 | Mỗi lệnh qua EV ≥ 5% luôn có AI đánh giá (search/tính lại), AI chỉ Cấm hoặc Cho phép | **Chưa có** | AI đang SHADOW + cờ tắt (D1); không có search thật, bằng chứng web gần như rỗng (D2); 5 mảnh AI chồng nhau, tài liệu mô tả hàm không tồn tại (D3); kích hoạt không theo EV 5% (D6); bộ hành động có SWITCH/CHALLENGE vượt spec (D7); WSL ngoài cổng (D8); ABSTAIN khi bật cờ sẽ giết toàn bộ lệnh ngày (D5) |
| 5 | Đích cuối: live Polymarket thật | **Chưa có** | `LiveExecution` là seal ném lỗi (E1); thiếu toàn bộ tầng ví/ký EIP-712/CLOB order/fill/redeem; GO cutover kể cả khi gõ cũng chỉ đổi nguồn giá paper (E2). Có sẵn: book-walk+phí thật, joiner theo tên, UMA law (E3) và khung điều kiện mở seal (E4) |

### Ba việc phải làm trước mọi việc khác (theo thứ tự của auditor)

1. **Sửa B1 + thêm alarm lệnh kẹt (B2/G7/H1).** Không sửa đường tiền về thì mọi con số PnL/equity từ nay về sau đều không đáng tin, và app đích điểm 3 coi như chưa đạt.
2. **Quyết định GO cutover PM quote hoặc chấp nhận trần quota.** Chừng nào 3 giải chính còn ăn giá Pinnacle qua 4 credit/ngày, “nhanh + liên tục” (điểm 2) là không thể về mặt vật lý.
3. **Thiết kế lại cổng AI theo đúng spec 2 lựa chọn trước khi xin GO AI authority:** bỏ SWITCH, khoá opinion theo candidate, thêm search thật, thêm chính sách chờ thay vì ABSTAIN-chết-ngay, và nối WSL. Bật cờ trên kiến trúc hiện tại (D10) sẽ cho một cổng vừa yếu vừa nguy hiểm.

