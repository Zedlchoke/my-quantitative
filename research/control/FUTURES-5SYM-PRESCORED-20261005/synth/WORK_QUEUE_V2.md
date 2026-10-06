# WORK_QUEUE_V2 — FUTURES-5SYM-PRESCORED-20261005 sau wave-3 (mỗi mục có bằng chứng)

Thay thế WORK_QUEUE.md bằng supersede-by-reference (file cũ giữ nguyên làm bằng chứng).
Trạng thái: CLOSED-A (đóng hết phần được phép) / PARTIAL-A (đóng phần A, phần còn lại
phụ thuộc owner) / [B] owner quyết / [C] sau phê duyệt.

| # | Mục | Trạng thái wave-3 | Bằng chứng (command/exit/artifact) |
|---|---|---|---|
| 1 | Đối chứng symbol_contracts từng mã | **CLOSED-A** | exec/contract_verification.{md,json} — 72 đơn vị: 67 MATCH / 1 MISMATCH / 4 PENDING; mọi trường số runner tiêu thụ MATCH đủ 6 mã; MISMATCH NQ rth đã sửa evidence-backed trong exec/symbol_contracts.json (FREEZE-WIRING, diff 4+/3-); 4 FX rth PENDING giữ fail-closed (không bằng chứng trong tree); handoff_CONTRACTS PASS |
| 2 | Verify round tại committed SHA | **[A] wave-3 verify** | dispatch/handoff_VERIFY.json (sau commit synth này) |
| 3 | NQ-F3 full-era rebuild | **PARTIAL-A**: harness + synthetic 39/39 PASS exit 0; refusal --real exit 20 REFUSED_D9_UNSIGNED; chạy thật NOT_RUN chờ P5-NQ1 | meas_nq/m2_f3_rebuild_harness/ (rebuild_harness.py, HARNESS_SPEC.md, kết quả 39/39) |
| 4-7 | Freeze-builder NQ / 6E/6B / 6J / 6A | **PARTIAL-A**: khung builder đầy đủ + GATE-0 refusal từng mã (exit 21/22/23/24→25→21/26/27/29/30/31) + bundle deterministic byte-identical; chạy thật NOT_RUN đúng luật (authority chưa ký) | freeze_wiring/freeze_builder.py + FREEZE_BUILDER_SPEC_IMPL.md + tests 21/21 PASS |
| 8 | FX-F5 CIP-vintage sensitivity | **CLOSED-A** (trong phạm vi dữ liệu có sẵn): rho +0.9097 latest-vintage vs **−0.1068 vintage-as-of**; 1/27 flip (2022-12-01); ngưỡng 0.20 ĐẠT latest / THẤT BẠI as-of → **việc passes là vintage-dependent**; fresh vintage CSVs NOT_IN_TREE | meas_fx/m1_fx_f5_cip_vintage.{md,json}; handoff_MEAS-FX PASS |
| 9 | FX-F6 transfer measurement | **PARTIAL-A**: harness T = sign-agreement diff + block bootstrap, 4/4 synthetic PASS (null −0.029; injected +0.10 recovered [0.016,0.101]; no-lookahead byte-identical; obs+3 lag); chạy dữ liệu thật NOT_RUN (owner-gated, conditional-on-signal) | meas_fx/m2_fx_f6_transfer.{md,json} + harness |
| 10 | AF2 K2 vintage-flip | **PARTIAL-A**: machinery ≥3/16 flip-counter fixture-proven (2/6 injected recovered exact; null 0); **0/16 vintage coverage** — không có DFF vintage set nào tồn tại; cần owner data-plane acquisition | meas_fx/m3_af2_vintage_flip.{md,json} |
| 11 | NQ session-σ dispersion proxy trên v3 | **CLOSED-A**: 285/285 so sánh k6gate tái hiện bit-identical; **defect-INVARIANT ở median** (112.2984→112.2984bp, delta 0.0); năm-2020 duy nhất được hiệu chỉnh +1.2719pp; mới: phân rã theo lớp phiên RTH 2.75 / Globex 1.26 / break 1.16 bp | meas_nq/m1_session_sigma_v3.{md,json} |
| 12 | FX-F4 RT/MDE theo erratum M2c | **CLOSED-A**: corrected weekday gap-std 3.038/3.999bp; Reading B r = 15.2–26.5 (6E) / 20.2–35.8 (6B); p95 gap 3.10/4.40bp **dưới RT floors** → F4 chết tại n khả thi theo thang đã chỉnh (số học mô tả, không PnL) | meas_fx/m4_fx_f4_rt_mde.{md,json} |
| 13 | Trigger-time anatomy (court §b1.1) | **PARTIAL-A**: machinery (FX-F1 adapter census-law + trigger windows + fixtures) sẵn; phép đo 1m commissioned REFUSES chờ P5-FXEB-OD11 | adapt_fx_eb/fx_f1/ + handoff (OD11 always-refuses by test) |
| 14 | Adapter từng family | **MỚI — CLOSED-A**: 19 adapter nối vào đường chạy thật qua spec_compiler; pytest: NQ 65/65, FXEB 86/86, FXJA 90/90, wiring 21/21 (exit 0 cả bốn); PIT/boundary/era/direction/refusal đều có test | adapt_nq/ adapt_fx_eb/ adapt_fx_ja/ freeze_wiring/ |
| 15 | Registration packets / A7 / dry-run / GO / scored / twin / terminal A7 | **[C]** bất biến — chỉ sau chuỗi chữ ký §2 OWNER_DECISION_PACKET_P5 | — |

Còn mở dạng [B] (owner): toàn bộ mục trong OWNER_DECISION_PACKET_P5_V2 §2–§4 + 2 phát
hiện mới cần định đo thái (FX-F5 vintage-law reading; FX-F4 power-death ghi nhận) +
AF2 DFF-vintage acquisition + PENDING 4 ô FX rth session-mask (không bằng chứng trong
tree — hoặc owner chấp nhận Globex-template làm luật phiên FX, hoặc cấp nguồn bằng
chứng). Không còn mục [A] nào chưa làm trong phạm vi authority hiện hành.

— Hết WORK_QUEUE_V2.

## WAVE-4 cập nhật (sau fix defect wiring + canonical code)
| # | Mục | Trạng thái | Bằng chứng |
|---|---|---|---|
| W4-1 | Sửa semantic wiring (mixed-direction + timeline/folds) | **CLOSED-A**: intent-mode runner extension (intent_packet@1 INTENT_TIMELINE_VERBATIM), repro FAIL→FIXED (2 trades dirs [1,-1]); positional compiler relabeled + refuses >1-intent | freeze_wiring/repro_mixed_direction/{REPRO_FAIL,REPRO_FIXED}.json; INTENT_SEAM_SPEC.md; suites 42+33+12 exit 0 |
| W4-2 | 10 bài test有意义 theo yêu cầu owner | **CLOSED-A**: T-MD1..T-MD10 (+2 unit) PASS — parity vs reference độc lập 7 case, PIT prefix byte-identical, retry idempotent, mọi failure path | freeze_wiring/tests/test_intent_seam.py |
| W4-3 | Canonical integration = code đã test | **CLOSED-A (wrapper)**: production_exec.py qua governance.heavy_lock + CAS registry, 14/14 sandbox tests cùng code path; real lock/registry/GO = NOT_RUN sau 2 authorization (PREP_BUILD flip + typed GO) | canonical/ + CANONICAL_INTEGRATION_V2.md |
| W4-4 | Readiness matrix / PACKET cập nhật | **CLOSED-A** (mục này + file synth) | synth/*_v2/v3 sections |

Phần [B]/[C] giữ nguyên như PACKET_V2 §2–§4; không có mục implementation [A] nào còn mở.
