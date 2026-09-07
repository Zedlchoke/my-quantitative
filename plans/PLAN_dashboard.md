# LAB DASHBOARD — app macOS tổng quan + theo dõi sống của chương trình research

> Owner plan dated 2026-09-07, phê duyệt qua plan-mode Q&A (loại: tổng
> quan + sống; hình thức: **app riêng build trên Mac**; ngôn ngữ: tiếng
> Việt + thuật ngữ Anh; đồng thời sinh `plans/ACTIVE_CYCLES.json`).
> Đây là plan CÔNG CỤ cho chủ sở hữu — KHÔNG phải research cycle: không
> proposal, không scored cell, không đụng denominator. Luật chống
> overfitting không áp dụng cho công cụ, nhưng luật evidence-first áp
> dụng nguyên vẹn cho HIỂN THỊ: **không có số nào trên dashboard mà
> không truy được artifact**; dữ liệu thiếu hiển thị
> `KHÔNG CÓ DỮ LIỆU`, không bao giờ suy diễn.

## 0. Frozen starting point

```text
main                   6ad4190 (governance merged tại 77e31ff — ba cơ chế
                       đã trên main: failure registry + validator,
                       diagnostic gate, machine-wide heavy lock)
nguồn dữ liệu (đo      FAMILY_FAILURES.jsonl (50 entry đã validate);
2026-09-07)            HYPOTHESIS_LEDGER.md ground-rules denominators;
                       RULES.md §7 GO registry; LESSONS.md P-1..P-11;
                       heavy-lock registry/history (round-2
                       ~/.my-quantitative-governance/heavy_runtime +
                       round-1 .runtime legacy, chỉ-đọc); control dir
                       từng cycle (state/run_contract/event_log/
                       heartbeat); `git worktree list`.
khoảng trống已知       plans/ACTIVE_CYCLES.json CHƯA tồn tại (handbook
                       §3.1 luật-hoá nhưng chưa ai tạo) — dashboard build
                       sẽ sinh nó mỗi lần chạy.
code viz hiện có       KHÔNG CÓ — greenfield, không có gì để tái sử dụng
                       ngoài validator có sẵn của governance.
```

## 1. Mission

Một **app riêng trên Mac** (cửa sổ độc lập, double-click để mở, tự
refresh 30 giây) cho chủ sở hữu nhìn toàn bộ phòng thí nghiệm trên một
màn hình:

- Program: denominators từng asset + tổng (hiện tại 218 published /
  221 observed), 0 survivor, S1 SEALED, GO registry (3 cụm sống).
- Từng asset (crypto / stocks / forex): cycle đang chạy ở phase nào,
  budget, branch/HEAD, heartbeat/sự kiện cuối, worker/lock.
- Bộ nhớ thất bại: 50 family với verdict class + chữ ký, click mở
  evidence (terminal sha, path, ledger row); TECHABORT/NOT_RUN làm mờ
  với nhãn "không mang bằng chứng chất lượng".
- **PnL tổng quan so sánh được** (owner-approved 2026-09-07): bảng
  thống nhất anchor / neighbour / control của các family đã đóng —
  expectancy, PnL, PF, số fold dương, MDD, margin-to-fail — parse từ
  terminal verdict JSON của các cycle đóng (~12 cycle có số máy-đọc-
  được); family nào không có (sprint cũ / không persist) hiện
  `KHÔNG CÓ DỮ LIỆU` + dẫn dòng ledger. KHÔNG có per-trade/per-period
  PnL cho family đã đóng (drivers không persist — bài học P-11); từ
  V16/V7/V11 trở đi gate bắt buộc per-period series nên tương lai có
  đủ.
- Near-miss do Lead tuyển; chữ ký thất bại dạng bar-chart; bài học
  P-1..P-11 dạng accordion.

## 2. Kiến trúc 3 lớp (trong `research/governance/`, branch `orca/lab-dashboard`)

**Lớp 1 — Collector `dashboard_collect.py` (thuần stdlib)**
Đọc mọi nguồn ở §0 thành MỘT snapshot dict; mỗi trường mang
`source_path`. Trạng thái sống đo best-effort, fail-closed. **Sinh
`plans/ACTIVE_CYCLES.json`** mỗi lần chạy (registry §3.1: cycle_id,
plan, status, phase, worktree, branch, head, budget, go_phrase, s1,
measured_at). **Panel PnL**: với mỗi cycle đóng, tìm terminal verdict/
report JSON trong cây git tại terminal SHA đã ghi trong
FAMILY_FAILURES.jsonl (`git show <sha>:<path>`), trích theo bộ key
thống nhất (anchor/neighbour/control × expectancy/pnl/pf/folds/mdd/
margins) — schema khác nhau giữa các cycle thì map tường minh từng
cycle trong một bảng MAPPER có test; không trích được →
`KHÔNG CÓ DỮ LIỆU`, không bao giờ điền số đoán.

**Lớp 2 — Renderer `dashboard_render.py` (stdlib)**
HTML tự chứa: CSS/SVG inline, JS vanilla tối thiểu (filter/expand),
**không CDN, không mạng**. Xuất `dashboard/index.html` (thư mục
`dashboard/` vào .gitignore). Panel theo §1 + footer liệt kê nguồn từng
panel.

**Lớp 3 — App `lab_app.py` + launcher `LabDashboard.command` (root)**
`python -m research.governance.lab_app` mở cửa sổ app riêng bằng
**pywebview** (WebKit hệ thống; dependency duy nhất, cài trong `.venv`,
pin version); nút "Làm mới" + auto-refresh 30 giây; chế độ `--html`
xuất file không cần window (dùng được khi không muốn dependency).

## 3. Panels

1. Header: measured_at, denominators, 0 survivor, S1, GO registry.
2. Ba thẻ asset: phase, budget used/max, branch + HEAD ngắn, heartbeat/
   event cuối, lock hiện tại.
3. "Đang chạy trên máy": heavy-lock registry row hiện hành + 10 dòng
   history cuối (cả hai runtime) + quét `ps` python worker (nhãn
   "đo bằng ps").
4. Bảng failure-memory: filter theo asset / verdict / chữ ký; click mở
   evidence.
5. **Bảng PnL tổng quan**: mỗi family một hàng, cột cố định
   (asset/cycle/family/anchor exp/anchor PF/neighbour/control/PnL/
   folds/MDD/verdict), sort theo cột, số dương âm tô màu, hover hiện
   nguồn; hàng KHÔNG CÓ DỮ LIỆU làm mờ.
6. Bar-chart SVG: đếm primary_failure code.
7. Near-miss tuyển bởi Lead (viện dẫn §E.1 + V6/V10/V15).
8. Accordion P-1..P-11.
9. Footer nguồn.

## 4. Deliverables & commits (pathspec; KHÔNG push/merge main trước chữ của chủ)

- **COMMIT A** (thuần stdlib, đứng độc lập được): collector + renderer
  + `tests/test_dashboard.py` (fixture repo giả trong tmp_path: registry
  giả, ledger giả, lock history giả → assert snapshot đúng key, HTML
  chứa chuỗi then chốt, không rò "None") + `plans/ACTIVE_CYCLES.json`
  bản sinh đầu + `.gitignore dashboard/`.
- **COMMIT B**: `lab_app.py` + `LabDashboard.command` + cài pywebview
  vào `.venv`; chạy app thật một lần cho chủ thấy cửa sổ.

## 5. Hard boundaries

- Không đụng plan/frozen artifact/workers của cycle đang chạy
  (V16/V11/V7); không scored PnL; không S1; không ghi key.
- Không phụ thuộc ngoài trừ pywebview (trong .venv, pin); lớp 1+2 phải
  chạy không cần nó.
- Mọi con số hiển thị phải truy được artifact; thiếu =
  `KHÔNG CÓ DỮ LIỆU`.
- Commit bằng pathspec; push/merge main là OWNER-ONLY.
