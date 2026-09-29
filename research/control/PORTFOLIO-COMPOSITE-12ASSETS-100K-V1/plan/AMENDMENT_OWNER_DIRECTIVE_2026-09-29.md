# AMENDMENT — OWNER DIRECTIVE 2026-09-29 (2nd): portfolio-complementarity research law

Program PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 · recorded by A1 at receipt,
2026-09-29 · status: PRE-REGISTRATION AMENDMENT to the draft plan (the
cycle remains UNREGISTERED; this document governs the draft's next
revision and will be frozen into the plan at registration).

## 1. Owner directive (key sentences, verbatim Vietnamese)

> owner KHÔNG yêu cầu novelty của từng strategy con. Đừng dùng "trùng
> family cũ" làm lý do tự động loại một ý tưởng khỏi vòng khám phá danh
> mục. Hãy ưu tiên strategy có quy tắc rõ, dữ liệu và chi phí đủ kiểm tra,
> số lệnh đủ lớn, cùng hành vi lời/lỗ có thể bổ sung cho các strategy
> khác.
>
> Xét cả strategy đã từng bị bác ở cấp riêng lẻ như ứng viên DIAGNOSTIC
> cho bài toán danh mục. Giữ nguyên kết quả thất bại và lịch sử thử nghiệm
> của chúng; không đổi tên thành edge mới. Kiểm tra liệu một policy dùng
> thông tin có sẵn trước lệnh có thể chọn đúng thời điểm bật/tắt, sau khi
> tính lệnh lời bị bỏ lỡ và mọi chi phí chuyển trạng thái hay không.
>
> Không giới hạn ở cặp strategy hoặc nhóm volume-profile. Khảo sát toàn bộ
> 1.200 ý tưởng theo khả năng triển khai hiện tại, rồi đề xuất các nhóm có
> thể dùng cùng nhau […]. Các tài sản thiếu dữ liệu vẫn giữ BLOCKED cho tới
> khi được mở khóa.
>
> Quy định novelty/F-0 trong các plan cũ đang chặn cách nghiên cứu này.
> Hãy soạn amendment/cycle mới nêu rõ owner muốn cho phép nghiên cứu
> portfolio-complementarity với các family cũ ở mức exploratory/diagnostic,
> có trial ledger và nhãn outcome-exposed. Trình đúng cổng đăng ký/duyệt
> theo repo; không tự vượt qua gate, không chạy scored cell trước GO.
> Tiêu chuẩn để công nhận strategy lớn vẫn phải là kết quả sau phí và
> drawdown trên fold chưa dùng để chọn policy, so với các baseline.

## 2. What changes in the research law (and what does NOT)

### Changed — admission law for sub-strategies

1. **Ancestry/novelty is a LABEL, not a gate.** A corpus idea enters
   portfolio exploration if and only if it is IMPLEMENTABLE today: clear
   mechanical rule (compilable), data panel exists, PIT chain provable,
   costs testable (spreads measured + DECLARED pessimistic comm/swap/slip),
   enough expected decisions, no swap-profit dependence. Its family-level
   failure history is carried as `outcome_exposed_label`
   (FAMILY_HISTORY_NEGATIVE | F0_INDIVIDUAL_REJECT | PRIOR_NOT_SCORED) into
   every ledger row — never renamed, never presented as a new edge.
2. **Previously-rejected strategies are DIAGNOSTIC candidates.** The
   question they answer is not "does this leg have edge?" (already answered
   NO at the individual level for labeled rows) but "can a policy using
   only pre-trade-available information time this leg ON/OFF such that,
   AFTER counting missed profitable trades and ALL state-switching costs,
   the portfolio beats its baselines?"
3. **Selection criterion for exploration prioritization** (owner's words):
   clear rules · testable data and costs · enough trades · loss/win
   behavior that can complement other strategies.

### Unchanged — the protection architecture

- **Acceptance bar:** the large strategy is accepted ONLY on after-cost
  net PnL AND drawdown, measured on folds NOT used to select the policy,
  versus the preregistered baseline battery (PASS_BARS_V2). No diagnostic
  result on a selection fold may serve as evidence of the final claim.
- **Trial ledger + denominators (P-9):** every exploratory computation is
  a ledger row with fold scope and label; observed/published counted
  separately. The wider search makes DSR/PBO MORE binding, not less.
- **Fold discipline:** grouping/policy/caps/gates learned on TRAIN only;
  later folds are checks; sealed tail untouched; no looking at the
  confirmation fold to choose rules (fold-lock law).
- **Cost/PIT/mechanization gates:** unchanged (see §3 blockers).
- **Registry/gates:** registration still needs the owner's typed GO at the
  plan's §9 phrase; scored execution still needs A7 prelaunch + fresh GO.
  This amendment is submitted AT the registration gate, not past it.

## 3. Effect on the eligibility table (executed, reproducible)

Ladder v2 (builder `eligibility/build_portfolio_eligibility.py` v2,
regenerated + validated: 1,200 rows, 1,200 unique gids, provenance ==
census verdicts):

| exploratory_status | rows |
|---|---|
| EXPLORATORY_CANDIDATE | **292** (EURUSD 55 · GBPUSD 83 · USDJPY 49 · USDCAD 50 · AUDUSD 55; all 10 families represented) |
| BLOCKED_NO_PRICE_DATA | 565 (NZDUSD USDCHF XAGUSD BRENT WTI NATGAS — stay BLOCKED until owner unlocks, per directive) |
| BLOCKED_PIT_UNEVIDENCED | 115 |
| BLOCKED_VENUE_UNEVIDENCED | 90 (XAUUSD) |
| BLOCKED_NOT_MECHANIZABLE | 68 |
| BLOCKED_DATA_CEILING | 39 (intraday features on H1-only pairs) |
| BLOCKED_DATA_FEATURE | 22 |
| BLOCKED_COST_SWAP | 9 |

Labels among candidates: FAMILY_HISTORY_NEGATIVE 222 · PRIOR_NOT_SCORED
59 · F0_INDIVIDUAL_REJECT 11.

## 4. Honest disclosure — the tension this amendment authorizes

- **The direct ancestors of this question shape died:** REGIME-GATED-
  COMBO-V1 (gating dead legs — exposed reading pending owner a/b) and
  BTC-COMBO6-SCORED-V1 (fixed combo, COMBO6_NO_INCREMENTAL_VALUE). Prior
  plans' verdict laws called "gating individually-dead legs" an
  anti-pattern. **The owner has now explicitly authorized reopening this
  pattern as a DIAGNOSTIC question**, with (a) outcome-exposed labels,
  (b) missed-profit accounting, (c) full switching-cost accounting,
  (d) acceptance still reserved to untouched folds vs baselines. The
  honest prior remains NEGATIVE; the changed axis is authorization +
  accounting discipline, not new information. A7 will test exactly this
  framing.
- **Wider search ⇒ larger multiple-testing surface:** 292 candidates ×
  controls enlarge the discovery ledger; the deflated-Sharpe/PBO
  machinery prices the whole ledger, and the PASS bars (PASS_BARS_V2 P5)
  bind on it. Budget caps grow for DISCOVERY rows but NOT for SCORED
  cells (see plan v2 §4).
- **Outcome-exposure containment:** family-history knowledge (published
  terminal verdicts of other cycles) MAY inform grouping and framing — it
  is owner-authorized and labeled. It is FORBIDDEN for any current-panel
  fold outcome to inform grouping/policy selection: the grouping lane
  works from mechanism class, implementability, and PUBLISHED prior-cycle
  verdicts only, never from a computation on the current panels' test
  folds (which do not exist yet and will not exist before GO).

## 5. Downstream artifact updates driven by this amendment

- `eligibility/*` — ladder v2 (done, this session).
- `plan/PLAN_..._DRAFT.md` — v2 admission law + discovery budget (next).
- `policy/PORTFOLIO_POLICY_ARCHITECTURE.md` — §0 changed-axis statement
  and L2 gating feature set restated under the diagnostic framing (next).
- `campaign/BACKTEST_CAMPAIGN_DESIGN.md` — Stage-A becomes an
  IMPLEMENTABILITY battery (mechanization + feasibility bill), not a
  novelty court; DSR/PBO over the larger ledger (next).
- Lanes D (panel audit) and P (PASS bars / accounting / fixtures) are
  UNAFFECTED and remain load-bearing. Lane M's class spec remains the
  mechanization spec for the VOLPROF arms — now one family among 292
  candidates, its ancestry-rho section demoted from kill-gate to
  measured-and-disclosed.
