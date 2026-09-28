# REPORT_HANDOVER — PORTFOLIO ONE / SHARED-PORTFOLIO-100K-V1 (gate A · PREVIEW · STOPPED FOR OWNER)

Owner directive 2026-09-25 (v2) · compile 2026-09-25 · **KHÔNG claim live-ready;
preview KHÔNG phải tài khoản đã chạy.**

## 0. Gate A bàn giao — DỪNG Ở ĐÂY chờ owner duyệt

Deliverables:
- **Plan**: `plans/DRAFT_amendment_PSCTV1_A4_shared_portfolio_100k_epoch2.md` (v2)
- **Preview app**: `research/control/SHARED-PORTFOLIO-100K-V1/build_stage/PhorecOne.app`
  (đang chạy ở http://127.0.0.1:8768/ — cửa sổ WKWebView mở; đóng app không
  ảnh hưởng worker nào)
- **Independent review**: `REVIEW_LOG.md` (Review 2: NEEDS_FIXES → đã fix hết
  2 MAJOR + 5 MINOR; 36/36 tests)
- **Evidence giữ nguyên từ v1**: `portfolio_lib.py` (lớp đọc dữ liệu đã kiểm
  chứng — không đổi logic), 13 ảnh chụp 2 đời UI, journal/marks/ledgers
  epoch-1 nguyên vẹn append-only.

## 1. Re-measure đầu phiên (snapshot 2026-09-25 ~10:30–11:30 +07)

| Item | State |
|---|---|
| Lock heavy | FREE_PROVEN |
| FX daemon (worker) | pid 35609 chạy — KHÔNG đụng |
| Phorec cũ (dashboard) | serve.py pid 8093, port 8766 — KHÔNG đụng |
| Shadow Monitor cũ | shadow_view_server.py pid 22766, port 8765 — KHÔNG đụng |
| Quant Shadow Dashboard | port 8791 — KHÔNG còn listener (pidfile 57257 stale, tự tắt bởi lane của nó) |
| PSV1 | **A2 Phase A ĐÃ ACTIVATE** T_act=2026-09-25T03:57:05Z (lane khác, HEAD 2ab6314); e-worker mới |
| CHR3F BASISLV scored | pid chạy tiếp, 16/16 cell FAIL do bug plugin `_benchmark` — không đụng, đã báo cáo |
| ETH V2 | ACTIVE_LIGHT tại STOP-1 AWAITING OWNER GO (lane khác đăng ký) |
| Root HEAD | d37caa81; registry files đang modified (của lane khác) — không đụng |

## 2. Thay đổi chủ trương đã cài vào A4-v2

- Epoch-2 = **chỉ FX-RANGEFADE-2M + BTC4H-BANDRIDGE** dùng chung $100.000
  USD-eq, sleeve-fenced $50k+$50k (giữ nguyên ngữ nghĩa sizing pin).
- **BASISLV** OBSERVATION_ONLY, **ILLIQ** DIAGNOSTIC_ONLY (D5 — không đủ điều
  kiện theo cấu tạo), **XSECT** retire theo A3: tiếp tục luật hiện hành trong
  sổ riêng — không vốn, không góp PnL headline.
- **USDT=USD 1:1 = GIẢ ĐỊNH BÁO CÁO** — nhãn hiện trên banner, chip BANDRIDGE,
  config, và được áp qua `usdt_usd_ref` trong mọi tổng.
- Read model **adapter-based** (`one/read_model.py`): registry mặc định 2
  sleeve, `auto_mount: false`, sleeve lạ trong registry → fail-closed raise.
- App **chỉ đọc, GET-only, không endpoint lệnh** (test pin); đóng app không
  đụng worker.
- Xung đột luật: PSCTV1 A1 (2026-09-24) "no shared capital anywhere" bị
  supersede CHỈ cho epoch-2 bởi directive của owner, có ghi rõ trong draft §2;
  không tự sửa registry/worker.

## 3. Accounting freeze (trước activation; reviewer đã soát)

| Luật | Nội dung |
|---|---|
| Epoch | Mở kỳ $100k tại T*, PnL mới từ 0; ledger cũ bất biến + sha256 manifest; "reset" chỉ là mốc trong sách MỚI |
| Vị thế mở | FLAT_START (kéo sang về sách cũ trọn vẹn) hoặc REOPEN_AT_MARK (boundary row do operator ghi, epoch-2 chỉ tính close − boundary mark; thiếu manifest → UNAVAILABLE, không bao giờ tự tính) |
| Chi phí | FX = GROSS/HYPOTHETICAL (journal không có fee/slippage/funding; spread ngầm trong fill đối diện) — không bao giờ hiện/sum như net; khoảng trống cost/USD-exposure chờ A1-controls GO. BANDRIDGE: 6 bps/side + digest boundary T_act |
| Capital/risk | R1–R5 + caps 250/150/150/15 — **chỉ decision-support/display, CHƯA enforce** ở đâu cả (owner phải chọn enforcement point bằng amendment riêng); xung đột 1.5-lot vs cap 150% trên fence $50k được disclose |
| Sizing | Không tự chọn lại từ PnL đã thấy: caps giữ nguyên con số đề xuất trước epoch-2; allocation EQUAL_2WAY duy nhất |
| BANDRIDGE | A2 Phase A đã activate (lane khác) — mount dùng sleeve-fence giữ nguyên semantics sizing B/fill law A/cost law; không sửa luật A2 |

## 4. Bảng PASS/FAIL/NOT_RUN (gate A)

| Hạng mục | Kết quả | Evidence |
|---|---|---|
| Re-measure registry/lock/workers/HEAD | PASS | §1 bảng trên + `REVIEW_LOG.md` |
| Đọc plan/authority hiện hành | PASS | PLAN_fx_rangefade (đầy đủ 74 dòng), PSV1 §5/§9+A1, A2/A3 drafts, PORTFOLIO_MIGRATION_COMPAT.md |
| A4-v2 draft nhất quán config↔code | PASS | Review 2: GO phrase byte-identical, gate fields khớp `_validate_activation` |
| Adapter law: 2 sleeve, no auto-mount, lạ→fail-closed | PASS | `test_exactly_two_sleeves_mounted`, `test_no_auto_mount_unknown_sleeve_fails_closed`, `test_adapter_registry_has_no_discovery` |
| Account accounting: 100k mở kỳ, PnL từ 0, không cộng sách cũ | PASS | `test_epoch2_inert_in_preview_and_baseline_is_100k`, banner NOT_ACTIVATED |
| Vị thế mở tại T* theo luật đã duyệt | PASS | `test_epoch2_fx_attribution_respects_open_position_law`, `test_reopen_without_boundary_manifest_is_unavailable` |
| Reconciliation equity↔calendar↔trades | PASS | `test_fx_calendar_matches_journal_total`, `test_bandridge_calendar_matches_equity_delta` |
| Restart/idempotence | PASS | `test_fx_replay_survives_duplication`, `test_build_one_state_deterministic` |
| Thiếu dữ liệu → UNAVAILABLE không $0 | PASS | `test_missing_bandridge_mark_day_is_not_zero`, dot PARTIAL trên lịch |
| USD/USDT ref áp vào accounting + nhãn | PASS | `test_usdt_ref_is_declared_and_labeled`, calendar ×ref |
| Activation fail-closed | PASS | `test_activation_fail_closed_and_epoch2_from_tstar`, `test_epoch2_gated_on_valid_activation` |
| App chỉ đọc, không đường lệnh | PASS | `test_no_order_surface_in_one_app`; không write path (review xác nhận) |
| Đóng app không ảnh hưởng worker | PASS | cold-launch 04:29:09 owner đóng cửa sổ → daemon 35609 + workers chạy nguyên (log + ps) |
| Cold-launch .app | PASS (manual) | binary start → GET 200 →窗口; ghi rõ là manual check trong draft §7 |
| Logo | PASS | dùng logo Phorec sẵn có (`dashboard/assets/logo.jpg`) + `phorec.icns` sẵn có cho icon — không tạo artwork mới; `/logo.jpg` 200 |
| UI 2 sleeve Forex/Crypto + chart + lịch + lệnh + trạng thái dữ liệu | PASS | `out/screenshots/10–13` (đã xem bằng mắt) |
| Independent review gate A | PASS (sau fix) | Review 2: 2 MAJOR + 5 MINOR đã fix; 36/36 tests |
| Activation epoch-2 | NOT_RUN (BLOCKED) | chờ GO — `epoch_config.status = PENDING_OWNER_GO` |
| Cutover/decommission dashboard cũ | NOT_RUN (BLOCKED) | gate B — GO riêng + inventory §8 draft |
| Caps enforcement | NOT_RUN | không tồn tại điểm enforce — cần quyết định owner (xem §3) |
| MAE per-trade FX / hard stop | FAIL/NOT_RUN | không có trong thiết kế; "maximum loss chưa được giới hạn bởi thiết kế" |
| Worker restart / S1 / scored / order / push-merge | NOT_RUN (cấm) | không có trong phạm vi gate A |

## 5. Gate B — sẽ làm SAU GO riêng (chưa làm gì)

1. Owner GO activation (`GO PORTFOLIO ONE EPOCH2 ACTIVATE T_STAR=… OPEN_POSITION_LAW=…`).
2. Operator: epoch-1 sha256 manifest + boundary rows (nếu REOPEN_AT_MARK) + config → ACTIVE + rule_digest + review_log_sha256.
3. Decommission dashboards cũ (danh mục đích danh trong draft §8, re-measure lúc đó; lưu bản phục hồi kiểu Phorec-prev-<ts>.app trước, stop sau) — KHÔNG đụng daemon/workers/ledger/S1/scored.
4. Quyết định enforcement point cho caps + sizing FX trong epoch-2 (1.5 lot frozen hiện NẰM NGOÀI cap 150% trên fence $50k — cần owner chọn: giữ grandfathered hoặc amendment sizing mới).

## 6. Quyết định còn cần owner

1. **Duyệt gate A** (plan A4-v2 + preview app + review) — hoặc yêu cầu sửa.
2. **T_STAR + OPEN_POSITION_LAW** (FLAT_START | REOPEN_AT_MARK) cho activation GO.
3. **Sizing FX trong epoch-2**: 1.5-lot frozen vs cap — giữ grandfathered hiển thị hay amendment sizing mới (0.5–0.6 lot theo audit)?
4. **Enforcement point** cho caps (hiện chỉ display).
5. **GO gate B** (decommission dashboard cũ) — sau khi activation ổn.
6. (Ngoài phạm vi, đã báo cáo) CHR3F BASISLV scored run đang fail 16/16 cell do bug plugin — lane CHR3F phải tự xử.

---

## 7. ACTIVATION — ĐÃ THỰC HIỆN (owner GO 2026-09-25)

- Owner GO verbatim: **"activate đi tiếp tục"** (sau khi duyệt gate A).
- **T\* = 2026-09-25T05:07:30Z** · equity mở kỳ **$100,000.00** · PnL epoch-2 **$0.00**.
- **OPEN_POSITION_LAW = FLAT_START** — tại T* cả hai sách FLAT (EURUSD/GBPUSD FLAT; BANDRIDGE position 0, pending null → hai luật tương đương; snapshot lưu trong activation record).
- Preconditions đã đầy đủ: epoch-1 manifest sha256 (`out/epoch1_manifest_20260925T050730Z.json`), rule_digest `8615aaed…`, review_log_sha256 `796e7db7…` (Review 2 + dispositions), allocation EQUAL_2WAY.
- Activation record: `out/activation_record_20260925T050730Z.json`.
- App phục vụ trạng thái ACTIVE ở http://127.0.0.1:8768/ (ảnh `out/screenshots/14_one_active_epoch2.png`). Lưu ý: đóng cửa sổ app = dừng server preview (worker không bị ảnh hưởng); mở lại bằng double-click `build_stage/PhorecOne.app`.
- Bug sửa trong lúc kích hoạt: app frozen cache key không track config thật → activation không được nhận diện cho tới khi sửa `_mtime_key` (dùng CONFIG_FALLBACK) + rebuild.
- Vẫn chờ owner: gate B decommission; enforcement point cho caps; sizing FX trong epoch-2 (1.5-lot vs cap).
