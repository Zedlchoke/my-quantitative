# BÁO CÁO TIẾNG VIỆT — FUTURES-SIX-SCORED-GATE-PREP-20261004 (2026-10-04)

## Tóm tắt một dòng
Theo chỉ thị "thử thêm / thử NQ với lại ES / 4 mã forex nếu có" — diễn giải
đúng luật là **cho phép PREP tới sát gate, KHÔNG phải typed GO** — round
này đã **thực thi xong fee A7 (AUTHORIZED_WITH_FINDINGS, 0 lỗi
HIGH/CRITICAL), lấy được pin D5 (CPI Jan-2026 = 2026-02-13 08:30 ET),
đóng 10/10 advisory NQ 2026, và dựng đủ shortlist + 16 bảng
identity-option cho cả 6 mã**. Follow-up owner-side bắt bất nhất phí
load-bearing (OD-2 đế kế thừa số stale 21.006…/2.24-làm-mặc-định) — đã
erratum + **CYCLE-1 = BLOCKED_COST_FREEZE chờ chữ ký D3 tường minh**
(bảng 2 biến thể corrected; xem `synth/COST_FREEZE_ERRATUM.md`). **Số
trial scored thực tế đã chạy: 0**
(dừng đúng gate theo luật). 0 engine-run, 0 dry-run, 0 PnL, 0 S1/lệnh/mua
data/push/merge/registry write; P3 quarantine không đụng; PB2/PB3 giữ
nguyên.

## Đã làm gì (theo 5 bước owner yêu cầu)
1. **Shortlist 6 mã** (`shortlist/SHORTLIST_6SYM.md`, 38 dòng family × 7
   tiêu chí): ES top = PB1(12, đã đăng ký) → ES-F1(11) → ES-F2(11); NQ =
   NQ-F1/F2/EXPWITCH-NQ; 6E = FX-F3 (MDE 10.1bp, power/cost tốt nhất FX);
   6B = FX-F2-6B; 6J = JF3 → JF1 → RMM; 6A = AF3 → RMM-6A → AF1. Framing-A
   (ít chữ ký nhất): **chỉ ES có slate hợp pháp hôm nay = PB1-only 24 ID**;
   5 mã còn lại rỗng với bộ chữ ký cụ thể được ghi tên.
2. **Budget/identity tables** (`budget/IDENTITY_TABLES.md`, 16 option, mọi
   số trích census): ES-0..4 = 24/35/46/60/67 (mọi option >24 kèm dòng
   sửa trần phải ký, không âm thầm; **phân tích 43-vs-60 giải xong: khác
   base — 43 loại 24 ID PB1 đã đóng băng, 60 = 24+36, 67 = 60+7**); NQ
   22/29/36/43; 6J 29/36/33-40; FX 44/66/96 (CONV-D, kèm bản native
   32/48/72 không trộn); 6A 0 + 26 contingency (PB3). Clock-only shadow
   đếm theo 2 cách đọc (a)/(b) — owner phải chốt 1; placebo ≥100-seed vẫn
   là slot owner.
3. **Giải PREP được phép**:
   - **FEE-A7 EXECUTED** (`fee_a7/A7_FEE_REAUDIT.md` + 9 artifact kèm theo):
     21/21 input re-hash khớp; bóc tách cell RAW-HTML (bẫy Housing-row
     loại trừ); số học 40/40 PASS; validator self-test 6/6 + real-mode
     37/37 trạng thái giống hệt P0-VERIFY; propagation 25 genuine + 1 FP,
     **0 site mới**; batch-1 insertions-only; language scan sạch; SPEC §5
     stale lines nhất quán UNDER-REVIEW; **D3 cả 2 biến thể liệt kê, không
     tự chọn**; e.1-e.4 còn là slot owner.
   - **CAL-CLOSE** (`cal_close/`): D5 OBTAINED (2 artifact độc lập);
     NQ Good-Friday 2026 advisory 10/10; ES 2026 holidays 3 cửa sổ FACT
     (1 capture khôi phục được, khác sha so với claim vòng-1 — đã công
     bố); **14 ô FX residual → CLOSED_PROVEN_ABSENT** (tái xác minh từ
     CDX 709 dòng); lưới FX giữ 256/272; 19/30 lần fetch, 1 vi phạm
     kỷ luật nhỏ (3 lần 1 URL CDX) đã retro-log.
   - NQ cache_v3/D8/D9: bằng chứng đầy đủ từ vòng trước, держ nguyên
     trạng thái "candidate chờ D9" — không tự phê.
4. **Cycle proposal** (`synth/CYCLE_PROPOSAL.md`): khuyến nghị **TÁCH
   CYCLE** — CYCLE-1 `FUTURES-ES-PB1-V1` (PB1-only 24, không cần sửa trần,
   freeze-ready: identity table + chain + cost + PIT/exclude + fold +
   gates theo CYCLE_LAUNCH_DRAFT §6) → CYCLE-2 NQ (sau D9 + trần) →
   CYCLE-3 FX (sau PB2-lift + trần; 6A là contingency annex sau PB3+D8).
   Biến thể gộp all-6 hợp pháp nhưng không khuyến nghị (gắn đường chạy
   scored sớm nhất của ES vào các ruling chậm nhất của FX/6A).
5. **Dừng đúng gate**: không có registration (owner chạy tại ROOT) và
   không có GO đúng form ⇒ **0 scored chạy**. Câu quyết định tối thiểu nằm
   trong `synth/OWNER_DECISION_PACKET.md`: **chữ ký D3 cơ sở phí trước**
   (A hay B — bảng số chính xác trong `synth/COST_FREEZE_ERRATUM.md`
   §2), rồi chọn CYCLE-1 + đăng ký + gõ
   `GO <REGISTERED-CYCLE-ID> SCORED EXECUTION` tại gate.

## Follow-up erratum phí (owner-side review, đóng cùng round)
Phát hiện bất nhất load-bearing giữa A7_FEE_REAUDIT §8 (exchange 1.38
settled ⇒ A = 2.25/21.00/33.50/46.00) với OD-2/CYCLE_PROPOSAL wave-2
(kế thừa số stale 21.006… của SPEC băng + gọi 2.24 là tier-1 mặc định).
Đã xử lý bằng `synth/COST_FREEZE_ERRATUM.md` (append-only, correction of
record): phân định historical-frozen (SPEC §5, dòng Variant-A packet
six-adopt — đứng nguyên như lịch sử, supersede bằng tham chiếu) vs
executable-at-new-freeze (bảng 2 biến thể corrected); exchange 1.38 là
bằng chứng, không phải lựa chọn; **D3/e.4 thành chữ ký BẮT BUỘC tường
minh — CYCLE-1 đổi trạng thái BLOCKED_COST_FREEZE**, rút lại câu "chỉ
còn registration+A7+GO"; silent-default bị rút khỏi vận hành (reading
hợp pháp duy nhất nếu cần: A × 1.38 corrected). MINOR F-1 xử bằng
`cal_close/ERRATUM_F1.md` (append-only, an toàn — không số học nào tiêu
thụ hash stale). Kiểm tra độc lập lại các claims này: mục Verify
follow-up bên dưới.

## Trạng thái từng mã tại giờ đóng round (SAU erratum phí — follow-up owner)
| Mã | Còn chặn gì trước scored |
|---|---|
| ES | **BLOCKED_COST_FREEZE: chữ ký D3 cơ sở phí** (A: 2.25/side, all-in 21.00/33.50/46.00 · B: 2.24/side, 20.99/33.49/45.99; exchange 1.38 evidence-settled; số stale 21.006… và cách nói "2.24 mặc định" đã erratum — `synth/COST_FREEZE_ERRATUM.md`) **rồi mới** registration tại ROOT + prelaunch A7 + typed GO |
| NQ | D9 (cache_v3 canonical) + trần NQ + registration + GO |
| 6E/6B | **PB2 lift** + trần FX + registration + GO |
| 6J | Trần 6J + cổng BBO/cost + registration + GO |
| 6A | **PB3 lift** + D8 (tick-era) — contingency 26 ID |

## Verify độc lập (ĐÃ XONG)
Lane VERIFY (wave 3): **round VERIFIED — 0 CRITICAL / 0 MAJOR / 1 MINOR /
5 NOTE**. Mọi claim then chốt tính lại từ bytes tại HEAD fae2158f: 25/25
input fee re-hash khớp; cell 1.38sup6 đúng 2 lần (L1694/L1706), bẫy
Housing-row loại đúng, footnote-6 "$1.30 per contract"; validator chạy lại
6/6 + 37/37 trạng thái giống hệt; propagation 0 site mới; 19/30 fetch +
đúng 1 vi phạm đã tự khai; 10/10 hash capture; D5 trích nguyên văn từ 2
artifact BLS; 16/16 option budget đối chiếu khớp CENSUS_FINAL; shortlist
6/6 spot-check; slots owner toàn bộ trống; P3 zero usage; GO phrase chỉ
xuất hiện dạng template luật.

**Phân phối findings**: F-1 MINOR — lane CAL-CLOSE trích sha claim của
round-1 cho capture khôi phục `svc_20260401_...0722114222` là `0700f57c`
trong khi verify_report vòng 1 ghi `c8388564` (MISSING_FROM_DISK);
`0700f57c` thuộc capture khác. Kết luận không đổi (bytes phục vụ không
khớp cả hai; hàng round-1 vốn unverified). Erratum của record là chính
VERIFY_REPORT F-1; file lane không sửa (append-only). F-2..F-6 NOTE:
anchor count 686/689 vs 685/688 (lẻ 1-2 hàng do ranh giới liệt kê); báo
cáo này ghi "9 artifact" (đúng: 10) và "40 dòng family" (đúng: 38) — đã
sửa 2 số này tại bản in hiện hành; 1 path tự sửa inline đã khai báo; 1
lệnh git read-only thêm của verifier đã ghi.

## Bằng chứng file (đường dẫn trong round dir)
`dispatch/DISPATCH_MANIFEST.json` · `fee_a7/*` (9 artifact) · `cal_close/*`
· `shortlist/*` · `budget/*` · `synth/CYCLE_PROPOSAL.md` ·
`synth/OWNER_DECISION_PACKET.md` · handoff chuẩn `zcode_orch_v3_handoff@1`
tại `dispatch/handoff_{FEE-A7,CAL-CLOSE,SHORTLIST,BUDGET,VERIFY}.json`.

— Hết REPORT_VI (bản trước verify).

— Hết REPORT_VI (đã verify).
