# FINDING: fill-timing mismatch — plan/adapter "next H4 open" vs executor "first completed 15m bar"

- date: 2026-09-24
- raised_by: Lead/A1 session (owner order 2026-09-24: "Chênh lệch 'fill ở H4 open'
  trong plan với 'nến 15 phút sau quyết định' trong executor: ghi thành finding
  riêng để audit sau, KHÔNG tự đổi cơ chế khớp lệnh trong nhiệm vụ UI này")
- status: OPEN — recorded only; NO code, config, ledger or frozen-law change made
- scope: PROSPECTIVE-SHADOW-V1, family BTC4H-BANDRIDGE (executor semantics are
  shared by all families via the same executor)

## The discrepancy

1. Adapter contract (research/shadow_v1/families/btc4h_bandridge.py, docstring
   lines 12-13):
   `exec = decision at each H4 bucket close; the engine fills at the next H4 open`

2. Executor rule (research/shadow_v1/executor.py):
   - line 340: `self.fill_bar_interval = str(config.get("fill_bar_interval", "15m"))`
   - module docstring lines 10-12: virtual fills execute at the
     `first completed bar strictly after the decision; buy at ref + ticks*tick,
     sell at ref - ticks*tick`

So the priced fill bar is the first COMPLETED **15-minute** bar after the H4
decision boundary — i.e. the fill references a price observed up to ~15 minutes
AFTER the H4 open — while the adapter/plan language promises a fill AT the H4
open. These are two different fill models (opening price of the H4 bar vs first
completed 15m bar after the boundary; with a `ticks` offset on top).

## Observed state (measured 2026-09-24)

- BTC4H-BANDRIDGE: 55 decision/intent records in
  `results/prospective_shadow_v1/ledgers/BTC4H-BANDRIDGE.jsonl`, `executed=0`,
  0 fills (first fillable decision = first post-mount H4 boundary) — the
  mismatch has NOT yet materialized in a BANDRIDGE fill.
- XSECT-FUND-CARRY-7D (daily clock, same executor default): 48 fills, e.g.
  decisions at 00:00 UTC filled with `actual_virtual_fill_time` on the 07:00
  (UTC+7) grid — consistent with the 15m-fill-bar rule, not with any
  "fill at decision-bar open" reading.

## Impact (not measured — for the audit to quantify)

- Every fill may embed up to one fill-bar-interval (~15m) of adverse/favorable
  selection vs the promised H4-open price, plus the tick offset.
- Prospective sleeve PnL and the future weekly scored cells derived from this
  journal inherit whichever fill model is canonical — this must be settled
  BEFORE any scored use.

## Requested audit decision (one of)

- (a) declare the executor's first-completed-15m-bar rule the canonical frozen
  law and correct the adapter/plan wording (documentation-only amendment), or
- (b) re-derive fills at the true H4 open for this family under a new
  preregistered amendment (accounting change, must be forward-only).

## Boundaries respected

No change to executor.py, btc4h_bandridge.py, scheduler, ledger bytes or any
frozen config was made for this finding.
