# DRAFT AMENDMENT — PWS-PROGRAM-V1 — caps & charter của chương trình ≤100 identity (2026-09-26)

> **Status: `DRAFT_FOR_OWNER_DECISION — KHÔNG HIỆU LỰC tới khi owner phê
> chuẩn.** Owner instruction 2026-09-26 nói rõ: prompt đó KHÔNG âm thầm là
> quyền vượt cap; amendment này phải qua A7 review + owner duyệt (ghi vào
> `research/control/PWS-PROGRAM-V1/OWNER_PACKET_program_open_2026-09-26.md`)
> TRƯỚC khi bất kỳ cycle nào của PWS được đăng ký hoặc chạy (P-8).

## 1. Luật hiện hành bị chạm tới (trích nguyên văn)

| Nguồn luật | Điều khoản | Giới hạn |
|---|---|---|
| `plans/PLAN_srlv_program_v1.md` §9 | program budget cap | ≤ 96 scored cells; ≤ 3 cohort/track; ≤ 3 cơ chế/cohort; ≤ 18 cells/cohort |
| `plans/PLAN_economic_robustness_program_v1.md` §5.2 | max mechanisms per cohort | ≤ 3 mechanisms/cohort (umbrella-level, mọi child kế thừa) |
| `plans/PLAN_erp_forex_program_v1.md` §8 | program-level cap do owner đặt từng cohort | child tự chốt, program-level owner đặt |

## 2. PWS-PROGRAM-V1 cần gì mà luật hiện hành không đủ

1. **Số cohort/track**: PWS có 6 pair-child FX + 4 pair-child CX (từng pair
   một là yêu cầu owner) — vượt "≤3 cohort/track" của SRLV §9.
2. **Trần 100 identity**: chưa có cấu trúc nào đăng ký "identity survey
   ceiling" như đầu vào kiểm soát multiple-testing (DSR hiện chỉ tính trên
   trial ledger đã score).
3. Giữ nguyên được (không cần sửa): ≤3 cơ chế/cohort (umbrella §5.2) — mỗi
   pair-child là một cohort, tối đa 3 identity frozen/pair; ≤18 cells/cohort.

## 3. Amendment đề xuất (Option A — khuyến nghị)

```text
A1  Scored-cell cap PWS:  ≤ 96 scored cells toàn chương trình
                          (FX ≤ 48, CX ≤ 48; trần khảo sát identity 100
                          KHÔNG cộng thành cells — chỉ identity được freeze
                          mới tiêu cells).
A2  Per-pair-child:       ≤ 18 scored cells; ≤ 3 identity frozen/pair
                          (umbrella §5.2 giữ nguyên cho từng pair-child).
A3  Pair-child count:     ≤ 6 FX + ≤ 4 CX (từng pair một, tuần tự §3.2 của
                          master plan; thay thế "≤3 cohort/track" CHỈ trong
                          phạm vi PWS — SRLV và các program khác không đổi).
A4  Identity ceiling:     ≤ 100 identity ID toàn chương trình (IDENTITY_
                          REGISTRY.jsonl, append-only; §2 master plan).
    Multiple-testing:     DSR tại mọi terminal với N_eff = max(scored
                          trials, identity đã score, frozen identity đã xem
                          outcome) VÀ công khai N_registry ≤ 100; PBO khi
                          ≥8 configs else NOT_RUN (P-9/P-11 mở rộng).
A5  Identity structure:   4–6 cells/identity (anchor + ≤2 neighbour + 1
                          causal control + 1 inverted control + 1 baseline;
                          neighbour tối thiểu hóa khi ngân sách căng).
```

Hệ quả số học (minh bạch): ≤96 cells ÷ 6 cells/identity = **≤16 identity
được score tối đa** (≤24 nếu mọi identity chạy dạng 4 cells); ≥76/100
identity theo thiết kế không bao giờ được score — sống và chết ở registry.
Đây là chủ đích: trần khảo sát rộng để không bỏ sót cơ chế mới, trần score
hẹp để multiple-testing không nuốt toàn bộ ý nghĩa thống kê.

**Thứ tự ràng buộc khi các trần xung đột (binding order — luật):** các trần
KHÔNG cộng dồn. Bao danh nghĩa per-pair là 10×18 = 180 cells (CX 4×18 = 72 >
CX ≤ 48; FX 6×18 = 108 > FX ≤ 48) và bao danh nghĩa frozen là ≤30 identity ×
4 cells = 120 > 96 — các con số đó KHÔNG BAO GIỜ khả dụng đồng thời. Program
cap ≤96 (FX≤48/CX≤48) LUÔN thắng; trần per-pair (≤18) và ≤3 identity/pair
chỉ PHÂN BỔ trong program cap, không mở rộng nó; stop conditions (master
plan §9) thường chặn sớm hơn nữa. (Cấu trúc bậc thang này kế thừa nguyên vẹn
lattice của SRLV §9: 3 cohort × 18 = 54 > 48.)

## 4. Option B (nếu owner muốn room score lớn hơn)

Như A nhưng A1 = ≤ 144 cells (FX ≤ 72 / CX ≤ 72) hoặc ≤ 192 (FX ≤ 96 /
CX ≤ 96). Cảnh báo trung thực theo base rate đo được của chính chương trình:
EURUSD open-search 1/48 gate-eligible rồi fail holdout; DSR V14 0.00224 trên
N=146; ERP cohort-2 7/7 chết pre-PnL — cells thêm sau điểm này chủ yếu mua
thêm xác nhận cái chết với chi phí OOS-tiện-ích và quyền lực thống kê giảm
(theo đúng lý thuyết multiple-testing mà owner dẫn: Harvey–Liu–Zhu; Bailey
và cộng sự). **Lead khuyến nghị Option A.**

## 5. Điều không đổi (ràng buộc tự khai)

- Umbrella §§1–11, forex charter R0–R6 + roster, SRLV F-0 court/PIT §3/
  kill rules §10/stop §11: kế thừa toàn bộ, PWS chỉ chặt hơn không lỏng hơn.
- Sealed one-look (S1, AUDUSD/USDCAD 2026-H1 program-level), re-clock veto,
  no-rescue laws, PAPER_TIER vocabulary: nguyên văn.
- Ngân sách scored của PWS là RIÊNG (không trừ vào cap 96 của SRLV — SRLV
  đóng cohort-1 CX rồi; hai program dùng chung ancestors nhưng tách budget/
  ledger/verdict). Trial accounting P-9 vẫn ghi cross-program totals trung
  thực qua ledger.

## 6. Hiệu lực

Amendment có hiệu lực duy nhất qua quyết định owner ghi tại OWNER_PACKET
(bảng Q2). Chưa duyệt ⇒ PWS không đăng ký cycle nào, không freeze, không
score; toàn bộ artifact ở dạng DRAFT.
