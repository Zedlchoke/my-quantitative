# TASK A4 — Research phân tích (ƯU TIÊN CAO NHẤT của sprint)

> Bạn là agent A4 trong sprint 24h (xem PLAN.md §"Định nghĩa EDGE"). Làm việc CHỈ
> trong worktree này, branch `wt/research-analysis`. TUYỆT ĐỐI không sửa
> `config/*.yaml`, không tune param, không đổi logic strategy.

## Bối cảnh
Scan matrix 2026-08-23 (`results/scan_matrix/20260823T051806Z/report.json`):
0/60 PASS, nhưng 4 combo GẦN ĐỖ chỉ vướng gate folds<5/6 và BH-FDR:

| Combo | Folds+ | Exp sau funding | PF | PnL | BH |
|---|---|---|---|---|---|
| reclaim_mr NEARUSDT | 4/6 | +0.148 | 1.46 | +26.95 | −152.43 |
| trend_pullback BOMEUSDT | 4/6 | +0.128 | 3.35 | +99.72 | −51.84 |
| markdown_breakdown ADAUSDT | 4/6 | +0.039 | 1.14 | +13.64 | +228.03 |
| reclaim_mr SOLUSDT | 3/6 | +0.037 | 1.18 | +6.68 | −36.33 |

## Câu hỏi trung tâm
Fold âm của từng combo có TẬP TRUNG ở regime/quý cụ thể không?
- Nếu CÓ (≤2 regime/quý giải thích hết fold âm) → edge CÓ ĐIỀU KIỆN, đề xuất gate.
- Nếu KHÔNG (lỗ rải rác) → noise, loại khỏi watchlist.

## Các bước
1. Đọc per-combo JSONs trong scan dir (fold-level PnL/exp/trades) +
   NOTES.md §15–§18. Xác định timestamp từng fold, map sang quý 2024Q3→2026Q3.
2. Với combo sống sót: chạy lại backtest fold-level với slippage ×1.5
   (chỉ đọc config hiện tại rồi nhân hệ số khi truyền vào engine — không lưu YAML).
   Dùng python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
3. Cross-check regime: dùng `regime_wyckoff.py` để gắn nhãn phase cho window
   fold âm — fold âm có rơi vào markdown/bear grind không?
4. Viết memo `research/memo_edge_watchlist_W3.md`:
   - Bảng từng combo × fold × quý × regime × PnL (số liệu, không cảm tính).
   - Kết luận per combo: GIỮ (edge có điều kiện, ghi rõ gate) hay LOẠI (noise).
   - Đề xuất watchlist W3 + rule signal-only cho tuần tới.
5. Script phân tích đặt ở `research/analyze_edge_stability.py` — chạy lại được.

## Ràng buộc
- Zero diff vào `config/`, `strategy_*.py`, `backtest/`.
- Kết quả số phải tái lập được từ artifact + script.

## Hoàn thành & bàn giao
- Commit lên branch `wt/research-analysis`, KHÔNG tự merge.
- PR description: "Đã làm / Không kịp / Rủi ro".
- Tiêu chí: memo có bảng fold×quý×regime đầy đủ cho ≥4 combo; script chạy lại OK.
