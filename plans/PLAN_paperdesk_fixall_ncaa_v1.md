# PAPERDESK FIX-ALL + NCAA — GÓI VIỆC CHO AGENT THỰC THI (Zcode)

> **Người giao việc:** chủ sở hữu (owner), qua Muse coordinator, 2026-10-21.
> **Lệnh của owner, nguyên văn ý:** "cho agent trong Zcode sửa toàn bộ và thêm NCAA vào. Tôi muốn app hoàn thiện chỉn chu chuẩn chỉ."
> **Repo:** `~/my-quantitative` · **Lane làm việc:** worktree `.worktrees/sports-papertrade-exec-v1/integration`, branch `orca/spt-exec-v1-integration` (tạo worktree/branch vòng mới theo đúng kỷ luật repo nếu luật chu trình yêu cầu — KHÔNG làm việc thẳng trên lane đang chạy production paper).
> **Bằng chứng gốc:** 2 bản audit độc lập ngày 2026-10-21 (audit code theo file:dòng + audit dữ liệu vận hành thật). Các phát hiện quyết định được nhúng thẳng trong gói này; bản audit đầy đủ nằm cùng thư mục chu trình (`PAPERDESK_AUDIT_CODE_2026-10-21.md`, `PAPERDESK_AUDIT_RUNTIME_2026-10-21.md`) và hồ sơ NCAA ở `ncaa_intake/` cùng thư mục.
> **Trạng thái production tại thời điểm giao việc (đo thật):** ledger 82 dòng, chain OK, equity 113.495c, PnL +13.495c (WNBA +2.215 / WSL +11.280 / NBA 0 / SOCCER 0); 13 BET_PAPER tích lũy, 10 đã settle, **3 lệnh NBA đang mở, trong đó 2 lệnh ĐÃ ĐÁ XONG NHƯNG KẸT CHƯA CHỐT ĐƯỢC**. Runner đang sống.

---

## 0. LUẬT CỨNG CỦA GÓI VIỆC NÀY (đọc trước, vi phạm = dừng việc)

1. **KHÔNG tự gõ/tiêu thụ bất kỳ câu GO nào.** Cả 2 cờ `feature_gates.pm_cutover_active` và `feature_gates.ai_authority_active` phải giữ `false` trên production cho tới khi owner tự gõ GO riêng cho từng cờ. Việc của agent: xây + kiểm chứng trong sandbox tới trạng thái "chỉ còn thiếu câu GO của owner".
2. **KHÔNG phá niêm phong live.** `LiveExecution` giữ nguyên SEALED. Không viết code ví, ký lệnh, đặt lệnh thật, redeem trong gói này (xem W6).
3. **KHÔNG chỉnh lặng các con số đã đóng băng:** ngưỡng EV 5%, stake 1% vốn, trần mở 50.000c, anchor law từng giải, hằng số mô hình. Việc được phép và bắt buộc: gom mỗi hằng số về MỘT nguồn duy nhất (W1.6) — giữ nguyên giá trị.
4. **Giữ nguyên kỷ luật đang có:** ledger hash-chain append-only, pin sha256 mọi engine/nguồn ngoài, journal raw response, fail-closed. Không đánh đổi các thứ này để lấy tốc độ.
5. **Mỗi vòng việc kết thúc bằng:** test suite xanh 2 lượt chạy liên tiếp (byte-repro như kỷ luật hiện tại), cập nhật RUNBOOK, và một handover note trong thư mục chu trình. **Toàn bộ gói kết thúc bằng A7 audit độc lập ở HEAD cuối cùng** — không có A7 PASS (hoặc PASS_WITH_FINDINGS không còn CRITICAL/HIGH/MED) thì không được báo "hoàn thành".
6. **Hai lệnh NBA đang kẹt (401909088, 401909090) là dữ liệu production.** Sau khi sửa W0, chúng phải tự chốt được qua đường settle bình thường. CẤM sửa tay ledger, CẤM ghi SETTLEMENT thủ công.

## QUYẾT ĐỊNH CỦA OWNER ĐÃ CHỐT TRONG GÓI NÀY (không hỏi lại)

- **QĐ1 — NBA:** tạm dừng vào lệnh NBA mới ngay từ đầu gói việc (qua cơ chế pause/law hiện có của hệ, journal rõ ràng) cho tới khi W1.3 xong (biết rõ nguyên nhân dự đoán hằng số + có chốt chặn). WNBA/WSL/SOCCER chạy tiếp.
- **QĐ2 — AI im lặng = không vào lệnh** (mặc định CẤM), nhưng qua cơ chế hàng chờ ở W4.4 — không chết lệnh ngay ở lần im lặng đầu tiên.
- **QĐ3 — NCAA vào ở chế độ paper-dự-đoán, gắn nhãn rõ** (W5.5). Không một dòng chữ nào trong app/tài liệu được khẳng định NCAA có lợi thế tiền: bản nam đã THUA thị trường trong bài kiểm tra tiền (t = −7,00, kiểm toán CONFIRMED), bản nữ CHƯA có dữ liệu giá để kết luận.
- **QĐ4 — Model cho cổng AI:** kiến trúc phải hỗ trợ cắm model trả phí qua config (W4.6); việc chọn model + bật quyền AI vẫn chờ GO riêng của owner.

---

## W0 — SỬA ĐƯỜNG CHỐT SỔ (ưu tiên 1, làm trước mọi thứ)

**W0.1 — Bảng nối tên đội cho nguồn kết quả (gốc của lỗi kẹt).** `research/papertrade_exec/results_fetch.py:129-137` đang so abbreviation ESPN (`DET`, `BOS`, `SA`, `OKC`…) với tên đầy đủ trong ledger (`Detroit Pistons`…) bằng `!=` trực tiếp → mọi lệnh NBA không bao giờ khớp kết quả.
- Xây MỘT module chuẩn hoá tên dùng chung cho toàn hệ (thay cả 3 hàm `_norm`/`norm_team` đang rời nhau ở `pm_moneyline.py:37-39`, `wsl_results.py:47-54`, `execute.py:1637`): đầu vào nhận cả tên đầy đủ, tên viết tắt ESPN, tên Polymarket; đầu ra là một team-id chuẩn duy nhất. Bảng nối đặt trong crosswalk đã ghim (mở rộng `PROVIDER_NAME_CROSSWALK_EXTENSION.csv` hoặc cơ chế tương đương có pin), KHÔNG hard-code rải rác.
- `results_fetch` phải map qua module này trước khi so. WNBA hiện "thoát" chỉ vì ledger của nó tình cờ ghi sẵn dạng viết tắt — sau W0.1 cả hai giải phải đi cùng một đường chuẩn hoá.
- Test bắt buộc: cặp (DET↔Detroit Pistons, BOS↔Boston Celtics, SA↔San Antonio Spurs, OKC↔Oklahoma City Thunder) + toàn bộ 30 đội NBA + 13 đội WNBA, lấy từ payload ESPN thật đã journal; test fail-closed khi tên lạ không có trong bảng nối (giữ OPEN + incident, không đoán).

**W0.2 — Nhịp thử chốt đều đặn.** Hiện một lệnh kẹt ~9 giờ chỉ được thử chốt 1 lần (incidents chỉ có 1 `SETTLE_KEEP_OPEN` cho 401909088). Đổi luật thử lại: mọi lệnh OPEN đã qua giờ kết thúc ước tính đều được xét lại MỖI vòng settle (throttle theo nguồn thì giữ, nhưng lệnh phải nằm trong hàng xét mỗi tick, không rơi khỏi hàng sau 1 lần fail). Mục tiêu đo được: **lệnh chốt xong ≤ 3 tiếng sau khi trận kết thúc** với NBA/WNBA (grace 3h hiện tại ở `results_fetch.py:25` được phép xem lại trong thiết kế, ghi rõ lý do nếu đổi).

**W0.3 — Báo động lệnh kẹt + hàng dead-letter.**
- Lệnh OPEN quá (giờ kết thúc + 6h) chưa chốt → incident mức cao riêng (`SETTLE_STUCK_ALARM`) + hiện ở dashboard (W2.4).
- Quá 48h → trạng thái dead-letter (vẫn OPEN trong ledger, nhưng có nhãn + lý do + tuổi kẹt hiển thị rõ); chỉ owner mới xử được, và mọi thao tác xử phải qua một đường ghi sổ có kiểm toán (không sửa ledger tay).
- Xoá mục trong `settle_last_why.json` ngay khi lệnh tương ứng chốt thành công (hiện 6/8 mục là bóng ma của lệnh WSL đã chốt từ 2026-10-20).

**W0.4 — WSL: nới điều kiện chân DRAW đúng bản chất.** `wsl_results.py:125-250` bắt cả 3 chân (HOME/DRAW/AWAY) cùng closed + UMA resolved + identity (tên hoặc ngày trong question). Polymarket hay ghi market DRAW không kèm ngày → chân DRAW `date_ok=False` → cả trận không chốt (bằng chứng runtime: FD-2026-M36…M42). Sửa luật identity cho chân DRAW: khớp bằng (cặp tên đội của event + market type DRAW) là đủ, ngày chỉ là tín hiệu phụ. Vẫn fail-closed khi mâu thuẫn thật (2 chân cùng nhận thắng, UMA chưa resolved). Thêm test bằng đúng payload của M36–M42 đã journal.

**W0.5 — Soccer: đường void cho trận đã đá nhưng ngoài luật giải.** `ops_service.py:352-375` chạy stage-law TRƯỚC khi lấy kết quả → trận `bet_eligible=False` bị inconclusive vĩnh viễn. Thêm nhánh: trận đã qua giờ đá + grace mà không đủ điều kiện stage-law → ghi nhận kết quả thực tế (nếu có lệnh mở) và VOID/refund theo `settlement_refund_results` đã có trong config, kèm lý do. Không để lệnh mở vô hạn.

**W0.6 — ESPN cửa sổ ngày + hoãn/huỷ.** `fetch_espn_results` chỉ tra ngày trận + ngày liền trước; mở rộng cửa sổ tra cứu hợp lý (ghi rõ luật mới), nhận diện hoãn/huỷ không chỉ dựa chuỗi mô tả — có test cho trận dời ngày.

**Nghiệm thu W0:** 2 lệnh NBA kẹt tự chốt qua đường thường; bộ test settle xanh 2 lượt; một lệnh giả lập bị chặn kết quả sẽ sinh alarm ở +6h và dead-letter ở +48h trong sandbox; `settle_last_why.json` sạch bóng ma.

---

## W1 — NGỪNG ĐỐT CÔNG + CHỐT CHẶN DỮ LIỆU SAI

**W1.1 — Tắt poll giải không tồn tại.** 1.972/4.423 lần gọi Odds API (44,6%) là 404 vào `soccer_fifa_world_cup_group` — sport key chính config đã ghi là không tồn tại — gọi 232–282 lần/ngày trái với note "max 1/day". Xoá key khỏi danh sách poll chủ động (hoặc cổng 1 lần/ngày đúng như note, có test đếm).

**W1.2 — Đếm quota phải khớp nhà cung cấp.** Journal ghi 1 credit/lần gọi WNBA odds nhưng bộ đếm provider tăng +2/lần (ngày 2026-10-07 thực tiêu 8 credit trong khi cap nội bộ 4/ngày tưởng là đủ). Sửa bộ đếm nội bộ theo đúng cách provider trừ (theo endpoint + sport), có test đối chiếu journal ↔ provider counters.

**W1.3 — NBA forecast hằng số: tìm nguyên nhân + chốt chặn.** Bằng chứng: 14/14 FORECAST NBA trong ledger có p = 0,640065/0,359935 GIỐNG HỆT nhau tới 6 chữ số. Việc 1: truy nguyên nhân tận gốc (engine entry, state đầu vào, hay đường fallback trả hằng số) và sửa đúng gốc, ghi rõ nguyên nhân trong handover — KHÔNG chấp nhận "đổi hằng số khác". Việc 2: chốt chặn vĩnh viễn trong decide path: nếu toàn bộ forecast của một giải trong một mẻ giống hệt nhau (hoặc phương sai = 0) → chặn toàn bộ mẻ, incident mức cao, không vào lệnh nào. Test: mẻ giả lập toàn hằng số phải bị chặn; mẻ bình thường qua. Chỉ khi cả 2 việc xong mới gỡ tạm dừng NBA của QĐ1 (gỡ bằng thao tác có journal, không im lặng).

**W1.4 — Chốt chặn giá trùng giữa các trận (WSL).** Odds chân DRAW của M39 = M42 (5,647962497524461) và M38 = M41 (5,9980806141780825), trùng tới 15 chữ số — nghi một snapshot PM bị dùng lại cho nhiều trận. Truy vết đường join quote → fixture; sửa gốc nếu có; thêm chốt chặn: cùng một quote snapshot/hash không được phục vụ 2 fixture khác nhau; phát hiện trùng → chặn lệnh + incident.

**W1.5 — EV ngoại lai phải cách ly.** Lệnh M39 vào với EV_net +196,68% (và thua). Luật mới trong decide path: EV_net > 100% → trạng thái cách ly (`QUARANTINED_EV_OUTLIER`): bắt buộc lấy giá lại độc lập + kiểm tra chéo nguồn thứ hai; vẫn bất thường → không vào lệnh, journal đầy đủ. Ngưỡng 100% là luật vận hành mới của gói này (ghi vào config + Laws screen), không phải chỉnh ngưỡng EV 5%.

**W1.6 — Một nguồn hằng số duy nhất.** EV_THRESHOLD 0,05 hiện chép tay ở ≥4 nơi (`decision_pipeline.py:32`, `ai_gate.js:23`, `paper_policy.js:28`, pinned core); stake law chép 3 nơi; anchor law chép cả ở JS (`ai.js:6-11`). Gom về một module hằng số Python + một file sinh cho JS, có test parity JS↔Python cho: ngưỡng EV, stake law, anchor law, phí (xem W3.1). Giá trị giữ nguyên, chỉ gom nguồn.

**W1.7 — Dọn nhật ký + cờ pause.**
- `incidents.jsonl`: DASHBOARD_REBUILT chiếm 61,4% — chuyển thành metric/heartbeat riêng, không ghi incident. Lỗi lặp giống hệt nhau (bão 446 FileNotFoundError pins.json ngày 2026-10-09) phải gộp: 1 incident + bộ đếm + lần đầu/cuối.
- Cờ pause: PAUSED 4 lần nhưng RESUMED 30 lần trong nhật ký — truy nguyên nhân cờ bị gỡ (UI ghi đè? restart?) và sửa; mọi thay đổi cờ phải journal kèm nguồn (ai/cái gì đổi).
- Điều tra riêng: ngày 2026-10-19 service start 26 lần — tìm vòng crash/restart, sửa gốc, ghi nguyên nhân vào handover.

**Nghiệm thu W1:** journal 1 ngày chạy thật không còn 404 WC-group; test các chốt chặn xanh; báo cáo nguyên nhân forecast hằng số + crash-loop viết rõ.

---

## W2 — TỐC ĐỘ + MỘT DASHBOARD + NHÌN THẤY ĐƯỢC SỰ THẬT

**W2.1 — Ledger đọc tăng dần.** Hiện mọi tick/request đều `load()` + verify toàn bộ JSONL (`ops_service.py:240`, `live_dashboard.py:321+`, JS `ledger.js:46`) — chi phí lớn dần theo lịch sử. Đổi: verify toàn bộ 1 lần lúc khởi động; sau đó đọc tăng dần theo offset đã verify, verify lại toàn bộ theo lịch thưa (ví dụ mỗi giờ + khi nghi ngờ). Hash-chain semantics giữ nguyên; có test parity kết quả state giữa đường cũ và đường mới trên ledger thật.

**W2.2 — Các giải chạy song song.** Service hiện đơn luồng tuần tự (settle → cadence → dashboard, tick 30s, cadence throttle 900s/league). Tách worker theo giải (hoặc hàng đợi việc có ưu tiên: settle trước decide) để một nguồn chậm không chặn các giải khác. Anchor law và throttle quota giữ đúng luật hiện hành cho tới W3.

**W2.3 — Một mặt hiển thị duy nhất.** Hiện có Electron app + trang `live_dashboard.py` (127.0.0.1:8791) dựng số bằng 2 đường khác nhau. Chọn Electron là mặt duy nhất; trang web hoặc tắt hẳn, hoặc chỉ còn là bản đọc cùng một state API với Electron. Không để 2 nguồn số liệu song song.

**W2.4 — Dashboard thêm 4 khối (dữ liệu đã có sẵn trong hệ, chỉ thiếu hiển thị):**
1. **Hàng lệnh kẹt:** mọi lệnh OPEN quá hạn chốt: trận, tuổi kẹt, lý do giữ mở (từ settle-why đã dọn ở W0.3), trạng thái dead-letter.
2. **CLV — giá đóng cửa:** với mỗi lệnh, ghi thêm giá thị trường tại thời điểm trận bắt đầu (PM sau cutover; trước cutover dùng giá Pinnacle/PM snapshot gần giờ đá nhất) và hiệu số với giá vào lệnh. Đây là trường dữ liệu MỚI — đi qua đường amendment của chu trình (append-only, không sửa dòng cũ), kèm luật lấy giá ghi rõ. Dashboard hiện PnL kèm CLV trung bình theo giải.
3. **Bảng theo giải:** số lệnh, BET/NO_EDGE/NO_QUOTE/NOT_RUN theo nguyên nhân, PnL, CLV — một chỗ nhìn ra giải nào sống, giải nào chết vì lý do gì.
4. **Thẻ sức khoẻ từng giải:** lần forecast/quote/decide thành công gần nhất, quota còn lại hôm nay/tháng (theo bộ đếm đã sửa W1.2), số trận sắp vào cửa sổ anchor, lỗi đặc thù đang mở của lane (stage-law, STALE_CORPUS…).

**Nghiệm thu W2:** mở app thấy ngay (a) có lệnh kẹt hay không và vì sao, (b) PnL + CLV từng giải, (c) lane nào đang chết lặng; state Electron và API khớp nhau trên cùng ledger.

---

## W3 — CHUYỂN NGUỒN GIÁ POLYMARKET (xây tới cổng GO, không tự bật)

**W3.1 — Thống nhất MỘT luật phí trước khi cutover.** Hiện có 3 định nghĩa: trừ phẳng 0,02 (`decision_pipeline.py:90` = `ai_gate.js:46-49` = `paper_policy.js:132-139`) vs phí PM thật `0,05·p·(1−p)` theo sổ lệnh (`pm_moneyline.py:215-216,237-238`, `wsl_lane.py:362-370`). Luật đích: phí = phí thật của nguồn giá đang dùng, khai trong module hằng số của W1.6, cả hai tầng Python/JS dùng chung, có test parity. Mục tiêu: EV 5% trước và sau cutover có CÙNG một nghĩa.

**W3.2 — Hoàn thiện đường PM tới mức sẵn sàng bật.** Đường PM đã có từ vòng 17 (join theo tên đã ghim, book-walk theo stake thật, fail-closed NOT_RUN_PM_QUOTE, không fallback Odds API). Việc còn lại: chạy lại toàn bộ battery sandbox ở HEAD mới sau W0–W2 (đặc biệt: 2-way NBA/WNBA, 3-YES soccer/WSL, join fail → NOT_RUN, quote rows ghi ledger ở cả 2 nhánh), cộng live read-only probe cho ít nhất NBA + WSL ở cửa sổ có trận thật. Kết quả gói thành một **cutover readiness note**: owner chỉ việc đọc và tự gõ GO.

**W3.3 — Sau khi owner gõ GO (việc tương lai, KHÔNG làm trong gói này):** lật cờ, theo dõi 48h đầu (quote thành công %, NOT_RUN_PM_QUOTE, so EV hai nguồn trên cùng trận), Pinnacle giữ vai trò nguồn CLV tham chiếu (W2.4).

**Nghiệm thu W3:** readiness note + battery xanh; cờ production vẫn `false`.

---

## W4 — CỔNG AI DUY NHẤT: CHỈ CẤM HOẶC CHO PHÉP

Hiện trạng phải thay: 5 mảnh AI rời (JS `ai.js` SHADOW, `ai_gate.js`, `paper_policy.js`; Python `decision_pipeline.py` + boundary trong `execute.py:1866-1890`), cờ tắt, AI **không có tìm kiếm web** (evidence chỉ là Gamma khớp tên + CLOB + fetch allow-list mà không nơi nào cấp URL → bằng chứng web ≈ rỗng), opinion nạp kiểu "file mới nhất" không khoá theo lệnh, có hành động SWITCH đổi chân vượt spec của owner, lane WSL chưa nối, và ABSTAIN hiện là DECISION terminal (bật cờ là AI sập = chết cả ngày lệnh). Tài liệu `AI_PIPELINE_DESIGN_V1.md` còn mô tả hàm `decision_pipeline.run()` không tồn tại — sửa tài liệu cho khớp code thật.

**W4.1 — Một cổng duy nhất trong đường decide của Python**, mọi giải đi qua (kể cả WSL — xoá đường trả-sớm `execute.py:1796-1798` né cổng). Các mảnh JS chỉ còn nhiệm vụ hiển thị + thu thập, không tự chấm cổng riêng; `paper_policy` hoặc xoá, hoặc thành bản hiển thị của cùng một luật (không luật riêng).

**W4.2 — Kích hoạt đúng spec:** candidate đã qua cổng EV ≥ 5% (và qua hết cổng xác định: depth, cap, drawdown) → BẮT BUỘC có một AI review cho đúng candidate đó trước khi append BET_PAPER. Opinion khoá bằng candidate hash (đã có `build_candidate_hash` ở `decision_pipeline.py:120-130` — dùng nó): hash gồm fixture + chân + giá + EV + snapshot mô hình. Giá/EV đổi → hash đổi → review cũ vô hiệu, phải review lại.

**W4.3 — AI có công cụ nghiên cứu thật.** Trước khi phán, AI phải tự thu: tin chấn thương/nghi ngờ ra sân, đội hình dự kiến/xác nhận, tin mới 48h về hai đội (nguồn báo thể thao + trang chủ giải/đội), cộng đối chiếu lại các số cơ bản (form 5 trận, đối đầu, nghỉ ngơi). Mọi nguồn phải lưu trích dẫn (URL + thời gian lấy + đoạn trích) vào hồ sơ lệnh. Không có nguồn nào lấy được → đó là một lý do CẤM hợp lệ (không đủ bằng chứng), ghi rõ. Đầu ra ép schema cứng: `{verdict: ALLOW | VETO, reason_codes: [...], summary: "...", sources: [...]}` — ngoài 2 verdict này, mọi output đều coi là không hợp lệ. **Xoá hẳn SWITCH/CHALLENGE/ALTERNATIVE khỏi đường có quyền** (code sandbox cũ có thể giữ nhưng không được nối vào đường decide).

**W4.4 — Luật im lặng (theo QĐ2):** chưa có verdict hợp lệ → candidate ở trạng thái `PENDING_AI`, được gọi lại theo nhịp (ví dụ mỗi 5 phút) cho tới (anchor − 30 phút). Tới hạn vẫn không có verdict → `NOT_PLACED_AI_NO_VERDICT` (không vào lệnh) + incident. Toàn bộ provider sập quá 30 phút → alarm mức cao cho owner (không giết lệnh trong im lặng — mọi lệnh chờ đều nhìn thấy được ở dashboard, khối "chờ AI").

**W4.5 — Bảng điểm AI (điều kiện để được tin):** job hằng tuần tự chấm: lệnh ALLOW đã vào → kết quả + CLV; lệnh VETO → kết quả giả định nếu đã vào (theo giá tại anchor + kết quả trận). Dashboard khối AI hiện: số review, tỉ lệ VETO, giá trị ròng của lớp AI (PnL giữ lại được − PnL bị bỏ lỡ). Luật giáng cấp: sau ≥ 100 review có kết quả, nếu nhóm VETO không tệ hơn nhóm ALLOW một cách có ý nghĩa → tự đề xuất hạ AI về SHADOW (chỉ owner mới quyết, hệ chỉ đề xuất kèm số).

**W4.6 — Cắm model:** provider khai qua config (model id, endpoint, key trong Keychain như hiện tại). Free chain OpenRouter hiện tại được giữ làm mặc định sandbox; kiến trúc không được khoá cứng vào nó. Prompt đóng băng theo phiên bản (version + hash ghi vào từng opinion).

**W4.7 — Thứ tự bật:** battery sandbox đầy đủ trước (ALLOW qua, VETO chặn, output rác → không hợp lệ, provider sập → PENDING rồi NO_VERDICT đúng hạn, WSL qua cổng, hash đổi → review lại). Xong battery + A7 phần AI → viết **AI authority readiness note** xin owner GO riêng. Cờ production giữ `false` cho tới lúc đó.

**Nghiệm thu W4:** 0 đường decide nào né được cổng; mọi BET_PAPER (khi cờ bật trong sandbox) đều có opinion khoá-hash đi kèm; dashboard thấy hàng chờ AI + bảng điểm AI.

---

## W5 — NCAA: HAI LÀN MỚI (NCAA-M, NCAA-W) — PAPER DỰ ĐOÁN

Spec mô hình đầy đủ nằm ở `ncaa_intake/` (dossier + `frozen_test.py` + `pilot_elo.py` + kết quả + 2 bản kiểm toán). Tóm tắt bắt buộc phải tôn trọng: Elo K=20, HFA +65 (0 nếu sân trung lập), đội mới 1500, cuối mùa kéo 25% về 1500; lớp hiệu suất ghi điểm đã chỉnh (trung bình giải khởi tạo 70, H_PTS 3,2, bước cập nhật 0,06, kéo 25% cuối mùa); GBM `HistGradientBoostingClassifier` mặc định, `random_state=0`, train trên các mùa < mùa đánh giá; 8 features đóng băng: `elo_diff, eff_margin, net_diff, rest_h, rest_a, rest_diff, conf_game, neutral`. **CẤM chỉnh lặng bất kỳ hằng số nào** — đây là mô hình đã kiểm toán CONFIRMED cho bài dự đoán.

**W5.1 — Chỗ chạm kiến trúc (làm đồng bộ, tránh vết xe WSL):** `LEAGUES` trong `backend/__init__.py:29`, `LEAGUE_CHOICES`/`DEFAULT_SPORT_KEYS`/`fixtures_for` trong `execute.py`, `DEFAULT_LOOKAHEAD_H`/`_cadence_leagues` trong `ops_service.py`, config (`sport_keys`, `anchor_law`), JS (`candidates.js`, `deadlineFor` trong `ai.js`, bộ lọc giải ở renderer), pins. NCAA-M và NCAA-W là 2 lane riêng (model/lịch/kết quả khác nhau).

**W5.2 — Adapter lịch + kết quả** từ ESPN bóng rổ đại học (men's/women's college basketball) hoặc sportsdataverse: team-id ổn định, tên chuẩn hoá qua module của W0.1 NGAY từ đầu (đây là bài học của lỗi NBA), cờ sân trung lập + trận trong conference lấy từ nguồn, múi giờ Mỹ xử lý theo dossier §6.3. Nguồn kết quả thêm vào `ESPN_LEAGUE_PATH` (`results_fetch.py:23-24`) và đi qua cùng đường chuẩn hoá tên.

**W5.3 — Kho trạng thái mô hình (phần nặng nhất, thiết kế trước khi code):** state store theo đội, có phiên bản + hash: sau mỗi trận final, cập nhật Elo/efficiency theo đúng luật đóng băng; đầu ngày dự đoán từ state hiện tại; job refit GBM theo mùa (train seasons < Y). State phải dựng lại được từ lịch sử tỉ số thô (replay test: dựng lại từ đầu cho ra state giống hệt — đây là bài kiểm tra chống rò rỉ của bản kiểm toán gốc, giữ nguyên). Pin artifact GBM theo mùa như mọi engine khác.

**W5.4 — Giá paper + vòng đời:** quote Polymarket bằng joiner 2-way sẵn có (`pm_moneyline.py`) — PM có niêm yết NCAA; nếu PM chưa list trận → NOT_RUN như các giải khác, không bịa giá. Anchor law đề xuất: mẻ ngày T0−6h10m như NBA cho mùa thường; tournament: anchor theo trận + `neutral` bắt buộc đúng (ghi luật vào config + amendment). Settle qua W5.2. NCAA đi qua cổng AI của W4 như mọi giải (khi cờ AI bật).

**W5.5 — Nhãn sự thật trên dashboard (bắt buộc, không gỡ):** lane NCAA hiện kèm dòng nhãn cố định: *"Dự đoán — mô hình thắng bài kiểm tra dự đoán (đã kiểm toán), CHƯA có bằng chứng thắng thị trường: bản nam đã thua giá đóng cửa trong bài kiểm tra tiền; bản nữ chưa kiểm tra được."* Số liệu NCAA tách riêng, không gộp vào PnL "có lợi thế" của các giải khác; dashboard hiện thêm độ chính xác dự đoán (log-loss/Brier chạy) của lane NCAA so với giá PM — đó là thước đo đúng cho lane này ở giai đoạn này.

**W5.6 — (Tuỳ chọn, spec riêng, mặc định TẮT):** sổ theo dõi forward cho giả thuyết "chỉ các trận mô hình lệch giá thị trường > 10%" — tín hiệu hậu kiểm duy nhất từng dương ở bản nam (n=2.227, +4,5%/lệnh tại giá đóng, có 3 lưu ý kèm theo trong dossier §3.5). Nếu làm: đăng ký thành spec con riêng, ghi trước luật, chỉ ghi sổ theo dõi (không stake, không gộp PnL chính).

**Nghiệm thu W5:** replay test bit-for-bit trên 1 mùa quá khứ cho cả 2 giới; 1 ngày sandbox đầy đủ forecast→quote(PM)→decide→settle cho cả NCAA-M và NCAA-W; dashboard có nhãn W5.5; battery tổng vẫn xanh.

---

## W6 — LIVE POLYMARKET: CHỈ CHUẨN BỊ HỒ SƠ, KHÔNG XÂY

Viết/cập nhật **LIVE_READINESS.md** trong thư mục chu trình: liệt kê đúng những gì còn thiếu để đặt lệnh thật (ví + custody, ký EIP-712, CLOB order/fill/huỷ, redeem sau UMA, kiểm tra số dư/allowance, geoblock/KYC, pháp lý Việt Nam cho giao dịch Polymarket) + điều kiện tiên quyết (W0–W4 xong, CLV đo được > 0 trên mẫu đủ lớn, owner GO riêng, kiểm toán độc lập riêng). **Không code, không tạo ví, không nạp tiền trong gói này.**

---

## THỨ TỰ THỰC THI + BÁO CÁO

W0 → W1 → W2 → W3 (readiness) → W4 (sandbox + readiness) → W5 → W6 (hồ sơ). W3/W4 chỉ chờ owner GO để bật — agent không tự bật. Mỗi W: commit riêng theo kỷ luật repo, test 2 lượt, handover note. Cuối gói: **A7 audit độc lập toàn bộ HEAD cuối** + một báo cáo tổng kết duy nhất (`PAPERDESK_FIXALL_NCAA_FINAL_2026-10-21.md` trong thư mục chu trình) trả lời 3 câu cho từng W: làm đúng spec chưa / đã cố hết chưa / còn đường nào dở dang và vì sao. Owner đọc báo cáo đó để quyết 2 câu GO (cutover giá PM, quyền AI) và việc gỡ tạm dừng NBA.

## KHÔNG LÀM TRONG GÓI NÀY
- Không live trading dưới mọi hình thức. Không tạo tài khoản/ví ở bất kỳ đâu.
- Không đổi ngưỡng EV, stake, cap, hằng số mô hình (chỉ gom nguồn — W1.6).
- Không merge/push nếu kỷ luật chu trình không cho phép ở vòng này.
- Không xoá/sửa bất kỳ dòng ledger production nào.

