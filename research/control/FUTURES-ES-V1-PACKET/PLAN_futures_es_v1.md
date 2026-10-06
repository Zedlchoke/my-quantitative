# PLAN_futures_es_v1 — FUTURES-ES-V1 (cycle packet, chờ owner duyệt + GO)

- Ngày soạn: 2026-10-03 (phiên chuẩn bị theo chỉ thị owner "chuẩn bị tối đa
  để bắt đầu cycle ES tối nay"). Trạng thái: **PACKET_READY — CHƯA ĐĂNG KÝ,
  CHƯA GO**. `NO_GO_REGISTER/SCORE/ORDER` vẫn hiệu lực cho tới khi owner gõ
  GO phrase tại gate của cycle này.
- Authority: chỉ thị owner 2026-10-03 (D2 account NOT_RUN — Access Denied;
  chấp nhận MODELED COST công khai); DATACONTRACT_QUALIFICATION (Bước 1
  CLOSED_WITH_ERRATA; r6 D2-D6); PLAYBOOKS_DRAFT r5 (A-r4 Co-Owner chọn);
  SPEC_PB1_ES (executable spec, outcome-blind).

## 0. Mission

Kiểm chứng giả thuyết OVN→RTH continuation vs reversion trên ES (2010-2026)
dưới MODELED COST đầy đủ khai báo, trong cycle đăng ký-budget-frozen, ≤24
scored identities, falsification-first. Không edge nào được claim nếu gates
không qua.

## 1. Phạm vi

ES-only. EXCLUDE theo SPEC §2 (D3 authority: E1 ngày / E2 roll không authority
/ E3 2026 bounds / E4 prev uncertain / E5 strays). NQ/FX/6F/commodities ngoài
phạm vi. Construction rules ≠ alpha (roll T-5, session era, exclude-list là
điều kiện chạy).

## 2. Data & identity binding

- Vendor parquet root vật lý (PATH LAW); T-5 roll + Juneteenth; era-correct
  sessions; ts_event=interval-start; dash-filter; D5 conventions.
- Danh tính trial: 24 IDs theo SPEC §6 (A-r4). Budget **max 24** — không thêm
  cell nào không có trong bảng trừ khi owner amendment.

## 3. Chi phí — MODELED COST (D2 account NOT_RUN, chấp nhận owner)

SPEC §5: commission Fixed 0.85 + exchange 1.386 (current-as-approx) + NFA theo
timeline chính thức + spread proxy 6.25 + slippage giả định {12.50, 25.00,
37.50}/chiều. Cấm ngôn ngữ measured/complete. Historical disclosure: chỉ NFA
per-year; commission/exchange current-as-approximation (biểu per-year
NOT_OBTAINABLE — D2 r6).

## 4. Gates (theo SPEC §8) + reproduction + audit

G1-G9; kill K1-K4; reproduction detached-twin byte-match; **A7 prelaunch
độc lập bắt buộc trước GO** (two-key thứ nhất).

## 5. Denominators & trial accounting

observed/published tách biei; mọi identity đã tính vào observed kể cả
publication fail; ledger theo P-9. Intake snapshot ≠ current total.

## 6. GO phrase (exact, gõ tại gate của cycle này)

```
GO FUTURES ES V1 SCORED EXECUTION
```

Two-key: (1) A7 prelaunch AUTHORIZED (0 HIGH/CRITICAL unresolved); (2) owner
gõ phrase trên nguyên văn, MỚI, tại gate. GO sớm = intent, chết unconsumed.

## 7. Trình tự đăng ký (runbook — bước nào writes root thì cần phiên được owner ủy quyền)

1. Owner duyệt packet này (SPEC + PLAN + exclude-rule generation).
2. **Đăng ký cycle**: `.venv/bin/python research/researchctl.py cycle register
   FUTURES-ES-V1 …` chạy tại ROOT checkout — **ghi `plans/CYCLE_REGISTRY.json`
   trên main ⇒ vượt phạm vi phiên prep hiện tại (không đụng root main)**. Đây
   là BLOCKER TỐI THIỂU số 1: cần owner tự chạy, hoặc cấp phiên A1 root được
   ủy quyền rõ ràng để register + commit control-plane (registry-only,
   pathspec, không đụng dirty files của owner).
3. Sau đăng ký: sinh exclude-list deterministic (SPEC §2) + freeze spec/IDs
   sha; A7 prelaunch; GO; scored ≤24 cells dưới heavy lock; repro twin;
   terminal A7; two-half close theo §32 handbook.

## 8. Terminal outcomes

SPEC §9. Mọi kết thúc đều hợp lệ; REJECT_ALL là kết quả tốt nếu bằng chứng sạch.

## 9. Non-goals

Không S1/paper/live/order/push/merge/mua data; không promotion; không chỉnh
tham số sau khi thấy PnL; không mở NO_GO nào ngoài GO phrase tại gate.

## 10. Blockers tối thiểu (báo owner)

1. **Root-registry write**: đăng ký cycle cần ghi registry trên root main —
   phiên prep bị cấm đụng root main ⇒ owner chạy hoặc ủy quyền riêng.
2. **A7-SPEC verdict** (đang chạy trong packet này) phải sạch HIGH/CRITICAL.
3. D2 account verification: **NOT_RUN vĩnh viễn cho cycle này** theo chấp
   nhận owner (MODELED COST) — ghi nhận, không phải blocker.
4. D3 phần dư (expirations 2019-2023+2026; ES 2026 times) — xử lý bằng
   EXCLUDE rules, không chặn.
