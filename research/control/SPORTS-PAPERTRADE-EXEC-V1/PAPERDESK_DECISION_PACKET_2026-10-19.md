# PAPERDESK DECISION PACKET — 2026-10-19
# Cycle SPORTS-PAPERTRADE-EXEC-V1 · AMENDMENT_MACOS_APP_UI_V1

## 1. Điều đã giao trong vòng này (không cần GO mới)

Ứng dụng macOS **PaperDesk.app** = UI + lifecycle controller cho paper trading
đang chạy, theo chỉ thị Owner trong chat 2026-10-19:
- Mở app = kết nối/khởi động đúng MỘT paper runner; Quit = graceful stop việc
  tìm & quyết định lệnh mới; đóng cửa sổ có hành vi tường minh (pause/keep/ask).
- Không tự chạy khi đăng nhập (takeover bootout launchd agent có journal).
- Dashboard đọc ledger thật (chain-verify byte-exact trong app), Polymarket là
  nguồn market data hiển thị chính (read-only GET + raw + sha256 journal).
- Tách seam `MarketDataProvider` / `PaperExecution` / `LiveExecution`;
  `LiveExecution` NIÊM PHONG (không endpoint, không key, không đường gửi lệnh).
- AI review GLM-5.3-Flash ở SHADOW, sidecar store, fail-closed; mock demo có
  nhãn MOCK; `NOT_RUN_AI_RUNTIME_ENTITLEMENT` (không có key General API).
- Battery seam 6/6 PASS + e2e + UI evidence + A7 độc lập.

Không có lệnh nào bị sửa/backfill; ledger chỉ có đúng một writer (pinned core)
như trước. app không tiêu bất kỳ GO phrase nào.

## 2. Các GO phrase — trạng thái CHÍNH XÁC

| Phrase | Trạng thái | Ý nghĩa |
|---|---|---|
| `GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER` | **REGISTERED_NOT_CONSUMED** (đã đăng ký 2026-10-10, scope cutover nguồn quote của pipeline) | App vòng này KHÔNG tiêu. PM data mà app hiển thị là data đọc công khai cho UI/AI-input; quote dùng cho quyết định vẫn theo pipeline đã pin cho đến khi Owner gõ phrase này tại gate của cycle. |
| `GO SPORTS PAPERTRADE EXEC V1 RUN ALL` | DEAD — consumed 2026-10-07 (ledger genesis) | — |
| AI authority (candidate `GO SPORTS PAPERTRADE EXEC V1 AI AUTHORITY`) | **NOT_REGISTERED** | Chỉ Owner mới được đăng ký + gõ. Cần nếu muốn AI có quyền VETO/CHALLENGE/ALTERNATIVE tác động lên paper. Trước đó bắt buộc: policy freeze + A7 prelaunch của cơ chế AI-authority + đăng ký phrase tại gate. |
| Live trading Polymarket | **KHÔNG đăng ký bất kỳ phrase nào** | Thuộc chu kỳ riêng tương lai, qua cổng ủy quyền riêng (key custody ngoài app, allow-list endpoint, per-order human confirm, A7). `LiveExecution` trong app chỉ là seam niêm phong. |

## 3. Điều kiện bắt buộc TRƯỚC khi kết nối live trading (danh sách kiểm định)

1. Chu kỳ mới do Owner phát lệnh, plan riêng, budget riêng, GO phrase riêng.
2. Cổng ủy quyền (delegation gateway) tách biệt: giữ credential, ký request,
   giới hạn endpoint, rate/limit, ghi nhật ký bất biến; app chỉ gọi gateway.
3. A7 prelaunch độc lập trên gateway + sự cho phép pháp lý/ToS của venue.
4. Owner gõ GO verbatim tại gate của chu kỳ đó (P-8). PaperDesk hiện tại
   không chứa code gửi lệnh và sẽ KHÔNG tự mở rộng thành đường live.

## 4. Trạng thái đã đo 2026-10-19 (không lấy từ prompt)

- Runner thật: pid 86445 `ops_service` (launchd), ledger 42+ rows chain OK,
  equity 102,215c. Heavy lock machine-wide: HELD bởi FUTURES-SRBOUNCE-RUN-V1
  (pid 82155) — app vòng này không chạy heavy job nào, không đụng worker đó.
- Entitlement AI: kho secret chỉ có databento/football_data/fred; không có key
  Z.ai General API ⇒ mock/shadow demo + `NOT_RUN_AI_RUNTIME_ENTITLEMENT`.

## 5. DỪNG ĐÚNG TRƯỚC ACTIVATION — các phrase sẽ dùng khi Owner muốn

- Chuyển PM thành nguồn quote quyết định cho toàn giải:
  gõ **`GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER`** tại gate
  SPORTS-PAPERTRADE-EXEC-V1 (đã đăng ký sẵn, chưa tiêu). Tác dụng: pipeline
  quote/decision chuyển sang nguồn PM đã prep; app hiển thị không đổi.
- Cho AI quyền tác động paper: yêu cầu đăng ký phrase AI AUTHORITY trước
  (hiện CHƯA đăng ký), sau đó Owner gõ tại gate.
- Live trading: không có phrase để gõ trong vòng này — phải mở chu kỳ mới.
