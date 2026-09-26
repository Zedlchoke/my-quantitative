# PLAN — EDGE-SCANNER-TOOLING-V1 — Vendor localhost guard middleware from edge-scanner (platform tooling, 0 scored cells)

> **Status: `GO-1 CONSUMED (phrase verbatim 2026-09-26; worktree
> orca/edge-scanner-tooling-v1-integration @ 938e80e3; 23 tests green on
> .venv 3.12.14; A7 pre-merge D1–D7 PASS, 3 process findings remediated —
> see research/control/EDGE-SCANNER-FEASIBILITY-V1/GO1_RECORDED.json and
> A7_GO1_premerge_REPORT.md) — STOPPED BEFORE GO-2.** GO-2 (wiring vào từng
> consumer) là quyết định riêng từng consumer với phrase riêng; không có gì
> chạy runtime cho tới đó. File này không score, không đụng cycle đang chạy
> (PWS-CX-SOLUSDT-C1, gateway, shadow, dashboard), không ghi strategy
> registry/ledger, không đặt lệnh, không push/merge.
>
> Authored 2026-09-26 bởi Lead từ owner instruction (feasibility song song);
> sản phẩm khảo sát: `research/control/EDGE-SCANNER-FEASIBILITY-V1/FEASIBILITY_REPORT.md`.
> Upstream: github.com/simonro/edge-scanner **@ c927dcb0c5e8122269812d2cdfdc4a3ae71b2ab3**
> (MIT, "Tape to Edge" 2026; NOTICE kèm lightweight-charts Apache-2.0 + schwabdev MIT —
> không áp dụng cho thành phần vendor trong plan này).

## 0. Cycle identity

```text
cycle_id       EDGE-SCANNER-TOOLING-V1 (platform-tooling cycle; scored cells 0/0
               — không bao giờ score; không thuộc PWS-PROGRAM-V1, không tiêu
               identity slot nào của trần 100)
type           additive platform tooling; zero runtime coupling tới bất kỳ
               cycle/service đang chạy cho tới khi một consumer riêng biệt
               được owner duyệt wiring
upstream_pin   c927dcb0c5e8122269812d2cdfdc4a3ae71b2ab3 (main; pin bằng
               VENDOR_PIN.md + digest file đã ghi ở control dir)
scope          vendor đúng 2 file mã nguồn + 1 file test upstream:
               scanner/local_guard.py, tests/test_local_guard.py (port sang
               pytest layout của workspace), LICENSE + NOTICE (bản sao byte)
non_goals      KHÔNG vendor: trigger catalog/setups, stops/size_hint/score,
               gates constants, providers (Alpaca/Schwab/yfinance), dashboard-v2,
               plugin system. KHÔNG nhập semantics chiến lược nào. KHÔNG mạng
               runtime (middleware thuần ASGI, không có đường egress nào).
worktree       .worktrees/edge-scanner-tooling-v1/integration
branch         orca/edge-scanner-tooling-v1-integration
ownership      1 lane implementation (Lead-dispatch), 1 A7 reviewer fresh-context
               (không kế thừa verdict implementer); heavy lock KHÔNG cần
               (light job; nhưng vẫn khai báo locks inspect trước khi chạy pytest)
rollback       revert commit vendor (thuần additive, không consumer nào tham chiếu
               tới đường dẫn mới cho tới wiring GO riêng) ⇒ xóa thư mục vendor +
               tests; không ảnh hưởng bất kỳ runtime nào
```

## 1. Vấn đề được giải

Các sidecar local (gateway/monitor/dashboard app theo mô hình
LIVE-DATA-GATEWAY-V1 / DASHBOARD-AND-SHADOW-RELIABILITY-V1) cần một lớp
hardening đồng nhất chống DNS-rebinding + cross-origin write + non-JSON POST,
phủ cả WebSocket upgrade. `local_guard.py` upstream là 110 dòng pure-ASGI
middleware, có test sẵn, starlette-only, không domain coupling — chi phí vendor
thấp hơn viết lại, và fidelity test đối chiếu được với upstream pin.
(Lane T survey §1 #1; báo cáo khả thi §1, §5, §6.)

## 2. Bối cục vendor (destination layout)

```text
research/platform_tools/thirdparty/edge-scanner/
  VENDOR_PIN.md            # upstream URL + pinned SHA + ngày pin + digest sha256 của từng file vendor
  local_guard.py           # byte-faithful copy từ pinned SHA (chỉ đổi: không đổi gì)
  LICENSE, NOTICE          # bản sao byte từ upstream (nghĩa vụ MIT notice-retention)
  THIRD_PARTY_NOTICES.md   # mục chỉ dẫn: nguồn, license, phạm vi sử dụng nội bộ
tests/platform_tools/thirdparty/
  test_local_guard_fidelity.py   # port cases upstream tests/test_local_guard.py
  test_local_guard_no_egress.py  # deny-list socket: import + full request matrix không được tạo outbound connect nào
```

## 3. Gate chain (gõ đúng chữ tại đúng gate)

| Gate | Hành động sau GO | GO phrase |
|---|---|---|
| Owner duyệt plan này | ghi quyết định vào control dir (không cần registry row — platform cycle) | quyết định ghi, không phrase |
| **GO-1** | register cycle qua researchctl + tạo worktree/branch + vendor bytes + fidelity/no-egress/3.12 tests xanh + A7 pre-merge review PASS — RỒI DỪNG (không wiring vào bất kỳ sidecar nào) | `GO EDGE SCANNER TOOLING V1 VENDOR AND TESTS` |
| **GO-2 (riêng từng consumer)** | wiring middleware vào một sidecar cụ thể (mỗi consumer một quyết định riêng; consumer thuộc cycle khác ⇒ tuân theo amendment law của cycle đó, ví dụ gateway sidecar cần amendment của LIVE-DATA-GATEWAY-V1) | `GO EDGE SCANNER TOOLING V1 WIRE <CONSUMER>` |

A7 review (fresh-context) đứng trước khi đóng GO-1: đối chiếu byte từng file
vendor vs pinned SHA, xác nhận không có file nào ngoài scope, tests là của
chính vendored code (không test-đẻ-ra-pass), và các file KHÔNG vendor (§0
non_goals) không xuất hiện ở bất kỳ đâu trong diff.

## 4. Tests bắt buộc tại GO-1

1. Fidelity matrix (port toàn bộ cases upstream: Host allowlist gồm hostname
   DNS-rebinding, Origin cho unsafe methods + WS upgrade, content-type JSON,
   loopback + `[::1]`, `SCANNER_ALLOWED_HOSTS` semantics) — mọi case phải ra
   kết quả giống upstream pin.
2. No-egress deny-list (socket hook, fail khi bất kỳ outbound connect nào trong
   import + request matrix) — biến tính chất "không mạng" thành property vĩnh viễn.
3. Python 3.12.14 trên `.venv` của workspace.
4. WS-upgrade wrap regression (property upstream; phải giữ).

## 5. Deployment prompt (dùng SAU owner GO-1 — không phải bây giờ)

```text
DISPATCH PACKET — EDGE-SCANNER-TOOLING-V1 lane "vendor-local-guard"

Bạn là lane implementation của cycle EDGE-SCANNER-TOOLING-V1, plan
plans/PLAN_edge_scanner_tooling_v1.md đã được owner phê chuẩn. Worktree:
.worktrees/edge-scanner-tooling-v1/integration, branch
orca/edge-scanner-tooling-v1-integration. Tạo worktree qua researchctl đúng
quy trình; mọi git command nêu tên repo tuyệt đối; stage bằng pathspec.

Nhiệm vụ (đúng thứ tự):
1. Clone/read-only nguồn đã pin c927dcb0c5e8122269812d2cdfdc4a3ae71b2ab3
   (bản sao khảo sát: /tmp/edge-scanner-survey — verify SHA bằng rev-parse
   trước khi dùng; nếu /tmp đã bị dọn, shallow-clone lại và verify cùng SHA).
2. Vendor đúng scope §2: local_guard.py + LICENSE + NOTICE (byte-faithful,
   không sửa dòng nào), ghi VENDOR_PIN.md + THIRD_PARTY_NOTICES.md.
3. Port tests: test_local_guard_fidelity.py (toàn bộ cases upstream) +
   test_local_guard_no_egress.py (socket deny-list). Không thêm code production
   nào ngoài byte-faithful copy.
4. Chạy pytest trên .venv (Python 3.12.14); locks inspect trước — nếu heavy
   lock held, KHÔNG chờ/kill, trả NOT_RUN_RESOURCE_CONFLICT.
5. Commit trong worktree (không push, không merge). Viết handoff
   zcode_orch_v3_handoff@1 tại research/control/EDGE-SCANNER-FEASIBILITY-V1/
   HANDOFF_edge_scanner_tooling_vendor.json (trong ROOT repo, không phải
   worktree — đúng pattern plan_review hiện hành).

CẤM: vendor bất kỳ file nào ngoài scope §2 (đặc biệt: triggers, stops,
size_hint, score, gates constants, providers, dashboard-v2, plugins); chạy
bất kỳ mã nào của upstream ngoài vendored middleware qua pytest; mạng
(theo sau egress-test thì không có); đụng PWS-CX-SOLUSDT-C1, gateway,
shadow, dashboard runtime; ghi IDENTITY_REGISTRY/ledgers; score; push/merge.
DỪNG sau commit + handoff. A7 pre-merge review là lane riêng.
```

## 6. Risks & rollback

- Rủi ro lớn nhất của plan này là scope creep (vendor thêm "vì tiện") — chặn
  bằng A7 diff-audit + non_goals liệt kê đích danh.
- Supply-chain: pinned SHA + digest từng file ghi trong VENDOR_PIN.md; mọi lần
  re-vendor phải là owner decision mới (không silent re-pin).
- Rollback: `git revert` commit vendor (additive, không consumer); wire nào
  đã GO-2 thì revert wiring đó theo amendment của consumer.
