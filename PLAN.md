# PLAN.md — Kế hoạch 24 giờ · 5 agent OpenCode song song

> **Dự án:** my-quantitative (NautilusTrader — Binance USD-M perp, Testnet only)
> **Bắt đầu:** 2026-08-23 ~14:00 (+07) · **Kết thúc:** 2026-08-24 ~14:00 (+07)
> **Nguyên tắc bất di bất dịch (từ NOTES.md §12):**
> - ĐÓNG BĂNG params chiến lược — KHÔNG grid, KHÔNG đổi stop/TP/vhf/adx/vol
> - KHÔNG live tiền thật — chỉ Testnet/Demo, guard `LIVE` không được gỡ
> - Mỗi agent làm việc trong **git worktree riêng** (Orca quản lý), merge qua PR
> - Ghi nhận mọi kết quả vào NOTES.md, artifact vào `results/`

---

## Tổng quan đội hình — 5 × OpenCode (ox-alpha)

| # | Agent | Vai trò | Worktree (branch) | Ưu tiên |
|---|-------|---------|-------------------|---------|
| A1 | **OpenCode #1** | Điều phối trưởng + Reviewer cuối | main (không edit code trực tiếp) | — |
| A2 | **OpenCode #2** | Data & Forward-test pipeline | `../my-quantitative-wt/data-pipeline` (`wt/data-pipeline`) | CAO — chạy W2 sớm vì tốn wall-clock |
| A3 | **OpenCode #3** | Safety guards (thu hẹp: chỉ test guard LIVE) | `../my-quantitative-wt/quality-safety` (`wt/quality-safety`) | THẤP |
| A4 | **OpenCode #4** | Research phân tích (không tune) | `../my-quantitative-wt/research-analysis` (`wt/research-analysis`) | **CAO NHẤT — nơi ra edge** |
| A5 | **OpenCode #5** | Ops tối thiểu (`status_report.py`) | `../my-quantitative-wt/ops-reporting` (`wt/ops-reporting`) | THẤP |

## Định nghĩa EDGE (v2 — A1 bổ sung, ràng buộc mọi agent)

Một combo chỉ được gọi là **edge candidate** khi ĐỒNG THỜI thỏa:

1. Expectancy sau funding > 0 và PF > 1.2 trên window 2 năm.
2. ≥ 4/6 fold dương, VÀ các fold âm tập trung ở ≤ 2 regime/quý xác định được
   (→ edge có điều kiện, ghi rõ điều kiện gate), hoặc dương đều mọi fold.
3. PnL > buy-and-hold cùng kỳ, HOẶC có lý do market-neutral rõ ràng
   (ví dụ: short-only trong markdown phase).
4. Edge còn tồn tại khi nhân slippage ×1.5 so với config hiện tại
   (stress test chi phí giao dịch).
5. Kết quả được A4 ghi trong memo kèm số liệu, KHÔNG cảm tính.

> Deliverable 24h = **watchlist W3**: mã + combo đạt chuẩn trên, kèm rule vào
> lệnh để forward-test signal-only tuần tới. KHÔNG đụng YAML, KHÔNG live.

### Hạ tầng chung cho worktree (A1 setup sẵn)

- Data dirs lớn bị gitignore → mỗi worktree có **symlink**:
  `catalog`, `catalog_live_crypto`, `funding_data`, `derivatives_data`, `.env`.
- Python gọi bằng đường dẫn tuyệt đối:
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
- `results/` trong worktree là local; artifact cuối copy về main repo.

---

## A1 — Điều phối & Review

**Goal:** Giữ cả 4 agent đi đúng hướng, không ai vi phạm nguyên tắc đóng băng params,
mọi PR được review và merge an toàn trước mốc 24h.

| Giờ | Việc |
|-----|------|
| H0–H1 | Tạo worktree cho A2–A5, giao brief từng agent, kiểm tra baseline tests xanh |
| H1–H8 | Theo dõi tiến độ mỗi 2h (terminal read / orchestration send trong Orca), chặn mọi thay đổi param YAML |
| H8 | **Checkpoint giữa ca:** review PR của A2+A3, merge nếu đạt, điều phối lại nếu trễ |
| H8–H20 | Tiếp tục giám sát; xử lý xung đột merge giữa các worktree |
| H20–H23 | Review tổng: chạy full test suite, duyệt merge cuối, tổng hợp báo cáo |
| H24 | Viết tổng kết 24h vào NOTES.md §19, đề xuất kế hoạch tuần W2 |

**Tiêu chí hoàn thành:** 4/4 PR được review; ≥3 merged; không có thay đổi trái phép
vào config params; báo cáo tổng kết tồn tại.

---

## A2 — OpenCode #1: Data & Forward-test pipeline

**Goal:** Forward-test W2 chạy sạch, tự động, không dính bẫy skip-im-lặng đã gặp ở W1.

| Giờ | Việc |
|-----|------|
| H0–H2 | Đọc `scripts/weekly_forward_test.sh` + bug tail-overlap W1; viết test tái hiện bẫy overlap |
| H2–H6 | Cứng hoá pipeline download: fetch chỉ sau bar cuối (+buffer), log rõ số bar mới fetched, fail-loud nếu 0 bar mới khi thị trường có data |
| H6–H10 | Chạy W2 forward test: download → OOS validate 60d → artifact JSON vào `results/forward_test/` |
| H10–H12 | Cập nhật bảng log W2 trong NOTES.md (Trades/Exp/PF/PnL + ghi chú thị trường), **KHÔNG rút ra kết luận tune** |
| H12–H20 | Kiểm tra định kỳ cửa sổ data; nếu phát hiện gap data thì vá và rerun; hỗ trợ A4 cần data nào |
| H20–H22 | PR: pipeline cứng hoá + artifacts W2 |

**Tiêu chí hoàn thành:** `weekly_forward_test.sh` chạy 1 lệnh không lỗi; W2 có
artifact JSON; bảng W2 được điền; test overlap pass.

---

## A3 — OpenCode #3: Safety guards (scope thu hẹp v2)

**Goal (v2):** Chỉ 1 việc bắt buộc: hard-guard LIVE tiền thật. Bỏ mục tiêu
coverage >90% và smoke-test toàn bộ factory — test không tạo edge, làm tối thiểu.

| Giờ | Việc |
|-----|------|
| H0–H2 | Audit `pytest tests/` hiện tại — liệt kê module chưa có test (ưu tiên `risk/limits.py`, `strategy_factory.py`) |
| H2–H8 | Viết unit test cho `risk/limits.py`: daily loss cap, cooldown sau lỗ, position sizing min(...); test biên (ATR=0, notional cap) |
| H8–H14 | Audit hard-guard LIVE: xác nhận mọi entry point live đều bị chặn khi `enable_trading: false`; thêm test phủ các đường vòng (config override, env var) |
| H14–H18 | Smoke test toàn bộ strategy factory với từng `strategy_type` trên fixture data nhỏ |
| H18–H22 | PR: tests + báo cáo audit guard |

**Tiêu chí hoàn thành:** coverage `risk/limits.py` > 90%; ≥1 test chứng minh LIVE
bị chặn; full suite xanh; không sửa logic production (chỉ thêm test).

---

## A4 — OpenCode #4: Research phân tích (read-only params) — **ƯU TIÊN CAO NHẤT**

**Goal (v2):** Đây là agent duy nhất trực tiếp tạo ra edge candidate trong 24h.
Trọng tâm: 4 combo gần đỗ ở §18.1 (NEAR reclaim_mr, BOME trend_pullback, ADA
markdown_breakdown, SOL reclaim_mr) — câu trả lời phải có là: fold âm có tập
trung theo regime/quý không? Nếu có → edge có điều kiện; nếu không → noise, bỏ.
Bổ sung v2: stress test slippage ×1.5 cho combo sống sót.

| Giờ | Việc |
|-----|------|
| H0–H3 | Đọc lại §15–§17 NOTES.md + artifacts `results/scan_matrix/20260823T051806Z/`; đặt 3 câu hỏi nghiên cứu cụ thể |
| H3–H9 | Phân tích fold composition: MR ETH lỗ khi nào (bear grind F1/F2?), tương quan Wyckoff phase × PnL trên window 2 năm |
| H9–H14 | So sánh top combos scan (NEAR reclaim, BOME pullback): edge có ổn định theo thời gian hay tập trung 1 regime? Vẽ bảng theo quý |
| H14–H18 | Viết memo `research/memo_regime_dependency.md`: edge nào đáng đưa vào watchlist W3+, cái nào bỏ |
| H18–H22 | PR: memo + notebook/script phân tích tái lập được |

**Tiêu chí hoàn thành:** Memo có bằng chứng số (không cảm tính); script phân tích
chạy lại được; **zero thay đổi** vào config/*.yaml.

---

## A5 — OpenCode #5: Ops tối thiểu (v2)

**Goal (v2):** Thu hẹp còn đúng 2 thứ: `scripts/status_report.py` +
`python main.py status`. Bỏ weekly digest, dọn artifact, cron automation —
không tạo edge, chỉ làm khi dư thời gian.

| Giờ | H0–H4: viết `scripts/status_report.py` gom tất cả JSON trong results/ → 1 bảng markdown |
|-----|------|
| H4–H8 | Thêm command `python main.py status` gọi report trên |
| H8–H12 | Weekly digest tự động: script tạo mục NOTES sẵn format cho W2/W3 (như bảng §12) |
| H12–H16 | Dọn dẹp: chuẩn hoá tên artifacts, thêm `.gitignore` cho file tạm lớn |
| H16–H20 | Tạo Orca automation mẫu: nhắc weekly forward test (cron-style) |
| H20–H22 | PR: scripts + docs cập nhật README phần "Cách chạy nhanh" |

**Tiêu chí hoàn thành:** `python main.py status` chạy < 5s, xuất bảng đúng;
automation mẫu tồn tại trong Orca; README có mục quick-run.

---

## Mốc chung (milestones)

| Mốc | Giờ | Nội dung |
|-----|-----|----------|
| M1 | H2 | Cả 4 agent có worktree + brief + baseline tests xanh |
| M2 | H8 | Checkpoint: A2 pipeline hardened, A3 nửa tests — A1 merge đợt 1 |
| M3 | H14 | A2 chạy xong W2 forward test; A4 có bản phân tích sơ bộ |
| M4 | H20 | Feature freeze — mọi người chuyển sang viết PR + docs |
| M5 | H24 | Merge cuối, tổng kết vào NOTES.md §19, kế hoạch W2 |

## Quy tắc phối hợp

1. **Merge chỉ qua A1 (OpenCode #1)** — agent khác không tự merge.
2. **Xung đột:** ai chạm file chung (`NOTES.md`, `README.md`) rebase trước khi PR.
3. **Kẹt > 45 phút:** báo A1 qua orchestration message, không tự xoay hướng.
4. **Cấm:** đổi param YAML chiến lược, gỡ guard LIVE, chạy grid optimizer, live tiền thật.
5. Cuối ca, mỗi agent append 1 đoạn "Đã làm / Không kịp / Rủi ro" vào PR description.
