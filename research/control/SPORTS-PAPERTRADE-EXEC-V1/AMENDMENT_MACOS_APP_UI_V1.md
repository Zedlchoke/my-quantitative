# AMENDMENT_MACOS_APP_UI_V1 — PaperDesk.app (macOS UI + lifecycle controller)
# cho SPORTS-PAPERTRADE-EXEC-V1

- Registered: 2026-10-19, theo chỉ thị trực tiếp của Owner trong chat cùng ngày.
- Cycle: `SPORTS-PAPERTRADE-EXEC-V1` (ACTIVE_LIGHT, GO_CONSUMED CAPTURE_ACTIVE
  LIVE_SERVICE_ACTIVE) — amendment này KHÔNG đổi lifecycle, KHÔNG đăng ký cycle
  mới, KHÔNG tiêu bất kỳ GO phrase nào. `plans/CYCLE_REGISTRY.json` không bị
  sửa bởi amendment này.
- Data plane: `~/.my-quantitative-data/sports-papertrade-exec-v1/` (thêm hai
  thư mục con: `ops/control/`, `ai_review/`). $0, không mua gì, không push/merge.

## 1. Scope được phép (UI + vận hành, không đụng luật quyết định)

1. **PaperDesk.app** — ứng dụng macOS SwiftUI, double-click được, build lại bằng
   một lệnh (`apps/paperdesk/build_app.sh`).
2. **Lifecycle controller**: mở app = kết nối vào đúng một paper runner đang
   chạy (heartbeat `ops/state/heartbeat.json` + flock `ops/service.lock`) hoặc
   khởi động đúng một runner khi chưa có; Quit app = dừng graceful (SIGTERM →
   journals `SERVICE_STOP`, ledger giữ nguyên, lệnh OPEN ở lại OPEN). Đóng cửa
   sổ = đặt `ops/control/pause_decisions.flag` (chỉ dừng tìm kiếm + quyết định
   lệnh MỚI; settle + dashboard vẫn chạy) hoặc giữ chạy, theo lựa chọn trong UI.
   Không tự chạy khi đăng nhập máy: app thực hiện takeover bằng
   `launchctl bootout` của agent `com.myquant.sptexec.ops` (KeepAlive/RunAtLoad
   mâu thuẫn với luật lifecycle Owner vừa đặt) và tự quản runner như child
   process; takeover được journal và ghi `ops/control/takeover.json`.
3. **Dashboard đọc-thật**: UI đọc ledger append-only TRỰC TIẾP (parse +
   chain-verify byte-exact trong app: canonical JSON
   `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=True)` →
   sha256) và `/api/state` trên 127.0.0.1:8791 (GET-only, có sẵn). Lịch sử chỉ
   từ ledger; không cache UI làm nguồn sự thật. Chain FAIL ⇒ treo banner đỏ +
   ẩn toàn bộ số tài chính (fail-closed như `build_state`).
4. **Polymarket = nguồn market data hiển thị chính**: `MarketDataProvider`
   read-only (Gamma events + CLOB books), ghi raw response + URL + retrieval
   UTC + token/market IDs + sha256 vào `pm_ui_snapshots/`. KHÔNG thay đổi nguồn
   quote của pipeline quyết định (pipeline đã pin; cutover PM cho pipeline vẫn
   do phrase đã đăng ký kiểm soát — app không tiêu nó).
5. **AI review GLM-5.3-FLASH — SHADOW ONLY**: opinion (APPROVE/VETO/CHALLENGE/
   ALTERNATIVE/ABSTAIN) theo JSON schema cố định, lưu sidecar
   `ai_review/opinions/`, KHÔNG được đọc bởi bất kỳ đường quyết định nào
   (guard-test cấm import). Entitlement General API chưa có ⇒ chạy MOCK demo có
   nhãn `MOCK` + ghi `NOT_RUN_AI_RUNTIME_ENTITLEMENT`. Secret (khi có) chỉ nằm
   trong macOS Keychain. Web connector chỉ đọc, có budget; nội dung web là dữ
   liệu không đáng tin, không phải chỉ thị.
6. **Kiểm thử + bằng chứng**: battery mới `test_ui_control_seam.py` (6 test),
   e2e sandbox (open/quit/reopen, 2 instance, crash, offline, AI late/malformed,
   ledger tamper), ảnh chụp thật của .app, A7 verifier độc lập.

## 2. Cấm (fail-closed, không có đường code)

- Bất kỳ đường gửi order thật nào: `LiveExecution` trong app là protocol bị
  niêm phong — thân rỗng `fatalError("SEALED")`, không chứa HTTP/endpoint đặt
  lệnh, không credential path, không build-flag mở nó. Polymarket live trading
  là chu kỳ riêng tương lai qua cổng ủy quyền riêng; amendment này không đăng
  ký GO phrase nào cho nó.
- AI ảnh hưởng quyết định: không VETO/CHALLENGE/ALTERNATIVE tác động lên
  pipeline paper. Muốn có quyền đó: đăng ký policy + freeze + A7 + Owner GO
  RIÊNG (phrase candidate `GO SPORTS PAPERTRADE EXEC V1 AI AUTHORITY` được ghi
  trong decision packet như NOT_REGISTERED — chỉ owner mới được đăng ký + gõ).
- Sửa/backfill ledger; tự đổi stake/cap/EV/drawdown/quota/anchor; kill worker
  không thuộc app (heavy lock FUTURES-SRBOUNCE-RUN-V1 không bị đụng); dùng
  Coding Plan API làm backend opinion; key vào log/git/frontend.

## 3. Non-interference

Toàn bộ quyết định paper vẫn do runner đã pin thực hiện (GO gate + pins +
chain verify từng lệnh). App chỉ: (a) chọn KHI NÀO runner được tìm/quyết định
(flag + SIGTERM), (b) hiển thị, (c) ghi sidecar AI. Ledger chỉ được ghi bởi
pinned core như trước — app không có code append ledger.

## 4. Nhãn trạng thái giao hàng này

- AI runtime: `NOT_RUN_AI_RUNTIME_ENTITLEMENT` (không có key Z.ai General API
  trong kho secret; env ZAI_* là OAuth Coding Plan — bị cấm làm backend
  opinion). Mock/shadow demo có nhãn `MOCK` rõ ràng trên UI.
- PM UI snapshots: có thể chạy thật khi mở app (read-only GET công khai); mọi
  refusal (offline, 4xx/5xx, stale) hiển thị đúng trạng thái.

## 5. Tech note (2026-10-19): stack = Electron (không phải SwiftUI)

SwiftUI attempt bị chặn bởi bug toolchain CLT (modulemap `SwiftBridging`
trùng lặp — chi tiết: `TOOLCHAIN_BLOCKER_NOTE.md`). Theo tiêu chí Owner
"chọn dựa trên môi trường thực tế": node v24 + npm khoẻ, binary prebuilt →
**Electron**. Kiến trúc seam/laws không đổi:
- main process: `main/ledger.js` (typed JSON parse + canonical sha256
  byte-exact với pinned Python — đã đối chiếu 42/42 row trên ledger thật),
  `main/runner.js` (attach/spawn/SIGTERM/pause-flag/launchd bootout),
  `main/market.js` (GET-only /api/state + Polymarket read-only snapshots),
  `main/ai.js` (SHADOW, fail-closed, Keychain qua /usr/bin/security),
  `main/seal.js` (LiveExecution niêm phong).
- renderer: contextIsolation + preload bridge, CSP không cho remote content.
- battery: `tests/papertrade_exec/test_ui_control_seam.py` (6),
  `apps/paperdesk/test_ai_seam.js` (14),
  `apps/paperdesk/e2e_evidence.sh` (17 check chính),
  `apps/paperdesk/e2e_lifecycle.sh` (12 check takeover trên runner thật).
