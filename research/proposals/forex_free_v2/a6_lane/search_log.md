# A6 lane search log — FOREX-FREE-V2, phase F2-D1

- lane: `.worktrees/forex-free-v2/d1-a6-proposals` (branch `orca/forex-free-v2-a6-proposals`)
- base wave SHA: `9e7e89c253caee2d7ec2681bbfe9e375da84c0d5` (verified equal to HEAD at start of work)
- date: 2026-09-04
- assigned mechanism class: **volatility/liquidity state transitions visible in H1 OHLCV**
- deliverables: exactly two outcome-blind proposals (`proposal_1.json`, `proposal_2.json`), this log, `lane_report_a6.json`

## 1. Information firewall

Files actually read (allowlist only):

- `PLAN_forex_v2.md`
- `research/control/forex_free_v2_run/run_contract.json`
- `research/control/forex_free_v2_run/frequency_contract.json`
- `research/control/forex_free_v2_run/data_manifest.json`
- `research/control/forex_free_v2_run/forbidden_family_inventory.json`
- `research/assets/forex/sessions.py`
- `research/assets/forex/calendar.py`
- `research/assets/forex_free_v1/td_loader.py` (bar JSON schema only: `datetime/open/high/low/close`; loader hygiene noted: ascending unique bars, OHLC-consistency quarantine, fail-closed on missing files)

Not read, per firewall: `research/control/forex_free_v1_run/`, `research/assets/forex_free_v1/family1.py|family2.py|scored_runner.py|exec_driver.py|probe_td.py|completion_pass.py|repair_pass.py`, anything under `research/proposals/` (any cycle; this lane only WROTE its own files there), `tests/assets/forex_free_v1/`, `PLAN_forex.md`. No `git log` / `git show` / `git diff`; only `git rev-parse HEAD` / `git merge-base` / `git branch --show-current` / `git status` for lane bookkeeping. No `data_raw/**` read; no backtest or PnL computation of any kind.

V1 knowledge actually held at design time: only the forbidden-inventory mechanism names and their frozen summary stats (London-open continuation anchor; late-NY standardized-extension fade anchor; both rejected, expectancy negative; plus the enumerated forbidden rescue operations and the near-duplicate London-to-NY momentum item).

## 2. Hard constraints that shaped the search

1. Bar schema has **no volume** — every state variable must be OHLC-derived (range/true-range family). "OHLCV" in the class name resolves to OHLC in this snapshot.
2. Bid/ask, H4, rollover/swap: `UNAVAILABLE_FAIL_CLOSED` — no spread-state, carry, or financing-state mechanisms.
3. Frequency contract: ≤1 entry/pair/UTC-day, ≤3 RT/pair/week, every position flat at the 16:00 America/New_York bar **open** on the entry UTC day. Intraday-only, low turnover by design.
4. Entry at the next allowed H1 bar open after the decision bar completes (one-event lag); completed bars only; missing bar ⇒ NO_TRADE, never fill-forward.
5. Forbidden families: London-open continuation, NY-open nearby-clock continuation, late-NY standardized-extension fade, and sign/clock/session-relabel/threshold-lookback variants; plus the near-duplicate London-to-NY momentum. Consequence: mechanisms must be **conditional on the vol/liquidity STATE**, and each control arm must delete exactly the state-conditioning so that any unconditional continuation/fade edge lands in the control, not the anchor.

## 3. Candidate mechanisms considered and disposition

| # | Candidate | Disposition | Reason |
|---|-----------|-------------|--------|
| 1 | Session-clock-keyed continuation (any session open, any nearby clock) | REJECTED at design | Direct forbidden-family proximity; a clock-keyed direction bet is a relabeled variant regardless of packaging. |
| 2 | Late-session extension fade variants | REJECTED at design | Forbidden family2 and its threshold/horizon neighborhood. |
| 3 | Spread-liquidity state transitions (bid-ask proxy from quoted data) | INELIGIBLE | Historical bid/ask `UNAVAILABLE_FAIL_CLOSED`; no honest proxy exists in OHLC-only data. |
| 4 | Volume/turnover-state transitions | INELIGIBLE | Bar schema carries no volume field. |
| 5 | Weekend-gap / Sunday-open state transitions | REJECTED at design | ≤ ~340 weekly events across 6.6y (below the sample floors), single-event exposure right at the weekly open where the schedule is thinnest; also hard to keep clear of open-continuation framing. |
| 6 | Cross-sectional vol-state dispersion (relative vol state across the 7 pairs) | SET ASIDE | Drifts toward the cross-pair lead/lag / dispersion class owned by other lanes and the plan's separate search domains; kept out to preserve clean lane separation. |
| 7 | **Compression→expansion transition (time-series realized-vol state) + channel-breach continuation** | **SELECTED → proposal_1** | State-conditional by construction; trigger and direction come from the breach of a compressed range, in any hour; control deletes the compression gate. |
| 8 | **Thin-Asian-session → liquid-European-session turnover transition + state-conditional reversion of the Asian drift** | **SELECTED → proposal_2** | Session-liquidity state transition detected from data (range-burst), not a wall clock; direction opposes the thin-session move; control deletes the thin-state gate. |

## 4. Why the two selected proposals are genuinely different from each other

| Dimension | proposal_1 (FXFV2-A6-P1) | proposal_2 (FXFV2-A6-P2) |
|---|---|---|
| State variable | Trailing 24-bar true-range sum vs its 10 prior non-overlapping block medians (realized-vol compression) | Same-day Asian-window (UTC 00–06) range vs trailing 15-day median (session-liquidity thinness) + same-day turnover burst detector |
| Transition direction traded | compressed → expanded | thin → liquid |
| Trigger | H1 close beyond the 48-bar high/low channel | First bar in UTC 06–10 with TR > 1.5 × same-day Asian median TR |
| Direction source | Continuation of the breach side (state-conditional) | Opposite the Asian-drift sign (state-conditional reversion) |
| Dominant trade window | Any hour of the week | Entries only in/just after the 06–10 UTC handoff window |
| Mechanism family | Volatility clustering + order-level cascade at range extremes | Intraday liquidity seasonality + inventory-driven thin-session displacement reverting at turnover arrival |
| Literature anchor | Osler 2003 (JF); Engle 1982 (Econometrica) | Andersen & Bollerslev 1998 (JF); Bollerslev & Domowitz 1993 (JF) |

## 5. Differentiation from the forbidden families (both proposals)

- Neither proposal measures any session-open move, and neither keys a **direction** to any wall clock. The only clock terms are the frozen decision/entry/forced-flat mechanics shared by all V2 schedules (16:00 NY bar-open flat is universal, not a signal).
- proposal_1: no session term anywhere; the trigger is a 48-bar channel breach evaluable any hour, gated by a measured vol state; it continues (never fades) and only in compression.
- proposal_2: full disclosure — its burst window brackets the London handoff, as any turnover-transition design must. It differs structurally from London-open continuation: state variable = measured thin-Asian range state; trigger = data-detected TR burst; direction = AGAINST the Asian drift (00–06 UTC measurement), whereas the forbidden family trades WITH the London-session move. It differs from late-NY standardized-extension fade: different clock (06–10 UTC vs late NY), different measured quantity (Asian drift vs standardized daily extension), and a state gate the forbidden family never had. A7-N is explicitly invited to re-audit this differentiation.
- No arm inverts a rejected family's sign; no arm assumes lower fees; no arm cherry-picks pairs; the controls REMOVE the state-conditioning rather than invert anything.

## 6. Control-arm discipline (per the hard caution)

- P1 anchor = compression state AND channel breach. P1 control = channel breach alone. The placebo keeps every unconditional-breakout property and deletes only the state gate; if the placebo reproduces the anchor, the mechanism is generic breakout continuation and the family is rejected by preregistered rule.
- P2 anchor = thin state AND turnover burst (reversion of Asian drift). P2 control = burst reversion alone. If the placebo reproduces the anchor, Asian-drift reversion is unconditional and the family is rejected by preregistered rule.
- Neighbours change exactly one measurement presumption each (P1: intraday TR blocks → prior-trading-day range; P2: high-low range → true-range sum) and are preregistered to move TOGETHER with their anchors; divergence ⇒ unstable mechanism ⇒ not promotable.

## 7. Frequency feasibility arithmetic (analytic, schedule-level)

- P1: compression ≈ 50% of hours (median split); 48-bar channel close-breach ≈ 4–6% of hours per side, collapsing further via the first-per-day dedup → ≈ 1.8 RT/pair/week (cap 3 as backstop; 1/day enforced by construction).
- P2: thin state ≈ 50% of days; first burst in the 4-bar window ≈ 60–75% of days → ≈ 1.7 RT/pair/week (cap 3 as backstop; 1/day by construction).
- Both obey ≤1 entry/pair/UTC-day and ≤3 RT/pair/week with the caps frozen as schedule rules; realized-frequency audit remains an implementation/scoring gate.

## 8. Literature integrity note

All four cited sources are standard, high-confidence references the author knows to exist with the stated authors/venue/year: Osler (JF 2003, 58(5)); Engle (Econometrica 1982, 50(4)); Andersen & Bollerslev (JF 1998, 53(1)); Bollerslev & Domowitz (JF 1993, 48(4)). Each claim line in the proposals is a one-sentence paraphrase of the paper's core documented finding. No source was fabricated and no claim depends on an unverified citation.

## 9. Attestation

Outcome-blind: no V1 outcome, per-cell PnL, scored digest, or prior proposal artifact was read; no backtest or PnL was computed; no real market data was loaded. One frozen parameter set per arm; no grids, menus, or ranges anywhere in either proposal.
