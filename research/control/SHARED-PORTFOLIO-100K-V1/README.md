# SHARED-PORTFOLIO-100K-V1 — control dir (PREVIEW, CHƯA ACTIVATE)

Owner directive 2026-09-25: MỘT shadow portfolio dùng chung 100,000
USD-equivalent cho các sleeve còn được quan sát, thay cho mô hình
mỗi-sleeve-100k (PSCTV1 A1 2026-09-24) — áp từ một activation timestamp
MỚI, tuyệt đối không sửa kết quả cũ.

**Trạng thái: EPOCH 2 = PENDING_OWNER_GO. CUTOVER BLOCKED.** Mọi artifact
ở đây là PREVIEW. Chưa có file epoch-1 nào bị ghi/sửa; engine chỉ ĐỌC.

## Nội dung

| File | Vai trò |
|---|---|
| `epoch_config.json` | Config of record: sleeve census, allocation options, capital rule R1–R5, caps đề xuất, open-position law options, GO phrase. `status` → `ACTIVE` chỉ sau owner GO (thao tác operator thủ công, có runbook). |
| `portfolio_lib.py` | Engine thuần: replay FX journal (dedup như daemon), daily series crypto từ valuation marks (identity đã pin), epoch logic, capital rule, exposure/overlap, manifest sha256. |
| `phorec2/` | Dashboard thống nhất (port 8767 scratch): MỘT portfolio $100k, Lịch PnL ngày/tuần/tháng + drill-down, period selector Kỳ mới / Lịch sử cũ, tách realized/unrealized/fee/funding, GROSS/HYPOTHETICAL cho FX, UNAVAILABLE ≠ $0. |
| `crypto_view2.py` | Dashboard crypto v2 (port 8776 scratch): framing epoch-2 chung, không còn cộng 100k×N. |
| `phorec2_app_entry.py` + `build_stage/Phorec2.app` | Bản .app review (PyInstaller + pywebview). KHÔNG thay `~/Applications/Phorec.app` đang chạy. |
| `tests/test_portfolio.py` | 13 test: idempotent replay, force-flat attribution, identity crypto pin trên dữ liệu thật, UNAVAILABLE khi thiếu mark, deterministic rebuild, calendar↔Δequity recon, FX↔journal total, capital rule allow/scale/block, no-order surface. |
| `scripts/sizing_audit.py` → `AUDIT_sizing_fx_shared_100k_v1.md` | Audit sizing 0.5/1.0/1.5 lot, kịch bản pip/spread/gap + crypto đồng lỗ, đề xuất risk budget (số tính tự động từ nguồn có thẩm quyền). |
| `out/screenshots/` | 6 ảnh chụp UI đã xem bằng mắt trước khi bàn giao. |
| `REPORT_HANDOVER.md` | Bảng PASS/FAIL/NOT_RUN + danh sách quyết định/GO cần owner. |

## Chạy bản review

```bash
# dashboard thống nhất (KHÔNG đụng 8766/8765 đang chạy)
.venv/bin/python research/control/SHARED-PORTFOLIO-100K-V1/phorec2/serve_phorec2.py   # → http://127.0.0.1:8767/
.venv/bin/python research/control/SHARED-PORTFOLIO-100K-V1/crypto_view2.py            # → http://127.0.0.1:8776/
# hoặc mở thẳng build: open research/control/SHARED-PORTFOLIO-100K-V1/build_stage/Phorec2.app
.venv/bin/python -m pytest research/control/SHARED-PORTFOLIO-100K-V1/tests/ -q
```

## Runbook activation (chỉ sau owner GO — KHÔNG tự chạy)

1. Owner cung cấp: `T_STAR` (ISO8601 UTC), `OPEN_POSITION_LAW`
   (FLAT_START | REOPEN_AT_MARK), `ALLOCATION` (CONFIRMED3 | WITH_ILLIQ4).
2. Operator ghi `out/epoch1_manifest_<ts>.json` (sha256 toàn bộ nguồn
   epoch-1 — danh sách trùng `source_manifest` của engine).
3. Nếu REOPEN_AT_MARK: ghi boundary rows `out/boundary_<ts>.jsonl` theo
   mark tại T_STAR (closing epoch-1 + opening epoch-2, cùng mark).
4. Sửa `epoch_config.json`: `status: ACTIVE`, `activation_ts_utc`,
   law + allocation + digest; commit kỷ luật do owner chỉ định.
5. Không worker nào được restart/stop trong toàn bộ quy trình.

## Luật bất di bất dịch

- Epoch-1 append-only; không delete/truncate/rewrite/relabel.
- Không chuyển PnL cũ vào epoch-2; không backfill; epoch-2 KHÔNG phải
  continuation của track nào.
- USD và USDT là hai sách riêng, chỉ ghép bằng `usdt_usd_ref` khai báo.
- Thiếu dữ liệu = UNAVAILABLE, không bao giờ $0.
- Allocation KHÔNG được tune trên PnL đã nhìn.
- Engine không có bất kỳ đường lệnh/broker nào (test pin).
