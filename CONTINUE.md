# CONTINUE.md — V8R context handoff (2026-08-26)

Đọc `PLAN.md` toàn bộ trước khi làm. Trạng thái đúng: **7 worktree đã bàn giao code, chưa integration chính thức, chưa có scored V8/V8X**.

## Root và lineage

- Root dự kiến: `291a158`; phải đo lại khi nhận việc.
- Parent V7 closure: `72eada1`.
- Root có untracked historical artifact `research/control/v8_run/worktree_manifest.json`; bảo tồn, không clean/overwrite.
- Old sprint: `2026-08-25T14:45:53Z → 2026-08-26T02:45:53Z`. Không kéo dài deadline.
- Tạo `research/control/v8_resume_run/` với start/deadline mới và parent manifest hash.
- Old terminal label: `V8_PREP_CONTEXT_HANDOFF_NO_SCORED_ARTIFACT`.

## Existing worktrees

| Role | Tip | State | Next |
|---|---:|---|---|
| A2 | `300391d` | clean, T12 provisional | prove funding coverage over possible held exposure; follow-up commit |
| A3 | `b6743aa` | dirty golden | remove absolute temp path; two byte-identical generations; clean follow-up commit |
| A4 | `846ecd5` | clean | integrate after remediations |
| A5 | `1b388ab` | clean | integrate after remediations |
| A6 | `0857c7b` | clean | resolve contract later at final code SHA; audit equity spec blocker |
| A7 | `291a158` | no audit yet | audit only after integration/preflight |
| A8 | `4f1d704` | clean but nonconforming | pre-window rank, exclude BTC, 15m gaps/full funding; follow-up commit |
| A9 | `d053f0c` | clean | preserve equity provider blocker; no equity run |

Paths: `../my-quantitative-v8-wt/a2-core-data`, `a3-weekly-engine`, `a4-finalizer`, `a5-reproduction`, `a6-contract-golden`, `a7-independent-audit`, `a8-crypto-breadth`, `a9-equity-breadth`.

## Verified rehearsal

- Cherry-pick seven original tips in a temp clone: no conflict.
- Targeted: `146 passed`.
- Full: `835 passed, 16 warnings`.
- Must rerun on corrected final integration SHA; this rehearsal is not T14 authorization.

## Immediate next action

1. Read-only inventory, no scored artifact census, close old prep lineage.
2. Freeze new V8R control lineage.
3. Dispatch only R-A2, R-A3, R-A8 in parallel on existing worktrees.
4. Integrate corrected tips in PLAN §5 order; targeted + full tests.
5. Resolve contract/baseline; remeasure T01–T15; A7 T14.
6. Only `15/15 PASS` + A7 authorization permits four frozen V8 trials.
7. V8X-Crypto only if PLAN §8 passes and >=300 minutes remain.
8. Equity remains `NOT_STARTED_PROVIDER_AND_SPEC_BLOCKED`.

## Hard prohibitions

No S1/paper/live/orders · no tuning from PnL · no equity scored run · no `git add -A` · no reset/clean · no rewrite frozen artifacts · no push without owner request.
