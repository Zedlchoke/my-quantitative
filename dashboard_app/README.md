# Quant Shadow Dashboard (.app)

Ứng dụng macOS read-only hiển thị trạng thái paper/shadow của cycle
**PROSPECTIVE-SHADOW-V1** (3 family × 100,000 USDT, tổng 300,000 USDT).

- **Artifact**: `dist/Quant Shadow Dashboard.app` (build từ lane
  `orca/shv1-dashboard`; xem "Build lại" bên dưới).
- **Mở**: double-click trong Finder (hoặc `open "dist/Quant Shadow Dashboard.app"`).
- **Dữ liệu**: đọc trực tiếp (chỉ đọc) từ runtime của cycle —
  `results/prospective_shadow_v1/{ledgers,valuation_marks,runtime}` —
  đường dẫn tự suy ra từ `plans/CYCLE_REGISTRY.json` (không hard-code).
- **Engine**: import lúc chạy từ integration worktree
  (`research.shadow_v1.dashboard.snapshot`) — đúng code sinh ra dữ liệu,
  không fork. App bundle không chứa engine và không chứa credential.
- **Refresh**: 30 giây; fingerprint theo (size, mtime_ns) — không đổi
  bytes là không đọc lại lịch sử; partial-line đang ghi → giữ snapshot
  cũ + DATA ERROR, vòng sau tự thử lại.
- **Chỉ đọc**: server GET/HEAD-only trên 127.0.0.1 (mặc định port 8791,
  bận thì tự nhảy port); không có route ghi, không đặt lệnh, không đụng
  heavy lock, không ảnh hưởng decision/valuation workers khi đóng.

## Trạng thái trên trang

- `LIVE` — heartbeat + valuation marks còn mới theo contract (≤ 900 s).
- `STALE` — quá ngưỡng nhưng vẫn đọc được dữ liệu cũ (giữ mark hợp lệ
  cuối; lỗi mạng valuation không bao giờ thành khoản lỗ).
- `DATA ERROR` — file/schema lỗi hoặc không đọc được (hiển thị snapshot
  tốt cuối cùng kèm lý do).

Gross exposure = Σ|notional| các vị thế đang mở (canonical `gross`
trong mark cũ bị lỗi pre-remediation 0.0071 → không dùng, đã ghi rõ
trong `store.family_gross`). SL/TP hiển thị `N/A` vì family đóng băng
không có stop/take cố định (plan §9.6) — không bao giờ bịa số.

## Log

`~/Library/Logs/QuantShadowDashboard/app.log` (tự xoay 1 MB). Marker
runtime + pidfile: `~/Library/Application Support/QuantShadowDashboard/`.

## Diagnostics (không mở cửa sổ)

```bash
.venv/bin/python -m dashboard_app.app_main --check
```

In ra runtime đã resolve, trạng thái, equity tổng, số lệnh.

## Build lại `.app`

```bash
cd /Users/hoangminhlong/my-quantitative/.worktrees/prospective-shadow-v1/dashboard
/Users/hoangminhlong/my-quantitative/.venv/bin/pyinstaller \
  --name "Quant Shadow Dashboard" --windowed --noconfirm --clean \
  --hidden-import webview.platforms.cocoa \
  --hidden-import zoneinfo --collect-all tzdata \
  --hidden-import csv --hidden-import hashlib --hidden-import io \
  --hidden-import re --hidden-import html --hidden-import argparse \
  --hidden-import urllib.request \
  --distpath dist --workpath build app_entry.py
rm -rf "dist/Quant Shadow Dashboard"   # bỏ thư mục onedir thừa
```

Build-deps cài vào `.venv` của repo: `pyinstaller`, `tzdata`.

## Signing / Gatekeeper

Đây là **local unsigned/ad-hoc-signed build** (`codesign -dv` →
`Signature=adhoc`), KHÔNG notarized, không Gatekeeper-ready cho máy
khác. Trên chính máy build này `open` chạy thẳng (không quarantine).
Nếu copy sang máy khác: chuột phải → Open, hoặc
System Settings → Privacy & Security → "Open Anyway".

## Tests

```bash
cd /Users/hoangminhlong/my-quantitative/.worktrees/prospective-shadow-v1/dashboard
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/test_quant_shadow_app.py -q
```

18 test: partial/corrupt JSONL, dedup fill ID, per-family equity/PnL,
combined 300K strict-sum, daily PnL boundary (00:00 Asia/Ho_Chi_Minh),
realized/unrealized, gross USD+%, SL/TP N/A, stale heartbeat,
valuation network error (giữ mark, không thành lỗ), incremental
refresh, restart không double-count + ledger bytes không đổi,
server GET/HEAD-only, resolve runtime từ registry.
