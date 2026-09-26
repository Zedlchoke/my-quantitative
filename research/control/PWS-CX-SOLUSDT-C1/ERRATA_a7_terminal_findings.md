# ERRATA — PWS-CX-SOLUSDT-C1 — theo A7 terminal findings (P-19 hygiene)

- Nguồn: `audits_a7/A7_TERMINAL_REPORT.md` (commit 033c2bef; verdict
  `CONFIRM_NO_ELIGIBLE_PROPOSAL`, 0 HIGH / 1 MED / 4 LOW). Các file gốc giữ
  nguyên (append-only); bản ghi đúng nằm ở đây.

1. **[MED — skeptic arithmetic one-sided]** Sweep/episode/ceiling trong
   `council/SKEPTIC_F0_REPORT.md` tính trênruns MỘT CHIỀU (positive-rate);
   P2-1 là hai chiều. Đọc hai chiều: "θ≥4 ⇒ 0 runs" thành 12 runs;
   "(K=3, θ=5.23 bps) ⇒ 0 episodes" thành 8 episodes phía âm. A7 đã tự
   re-verify nửa thiếu: rho hai chiều 0.316–0.703 (vẫn toàn bộ trên bar
   0.20), 8 episodes ≪ sàn 100, deep runs tập trung 2022/FTX (run dài 51
   settlement FTX ≈ 39% negative mass) ⇒ `VETOED_SAME_FAMILY` sống ở CẢ
   HAI cách đọc. Verdict không đổi.
2. **[LOW — deep prints]** Skeptic ghi "4 print −200 bps = 13.8% negative
   mass"; đo lại: **7 print −200 bps = 19.3%** — mạnh hơn nữa cho kill.
3. **[LOW — FTX spacing]** Recovery lane ghi "99×1-4h + 2×5-7h"; đo lại:
   **101×1-4h** (không có spacing 5-7h).
4. **[LOW — handoff bookkeeping]** 4 handoff trong `handoffs/` (bản thứ 5
   nhầm lẫn là handoff plan-review của root); c1c2 dùng khóa
   `changed_files`; P2 `tests: []`. Không ảnh hưởng evidence.
5. **[LOW — rho prose]** Khoảng rho trong văn bản skeptic hơi lỏng: ô
   θ=1.0/W90 nằm 0.199–0.207 (vượt bar trong nhiễu); mọi cửa đủ power vẫn
   ≥0.31. Nearest-ancestor windows ≥0.31 tại mọi gate khả thi.
