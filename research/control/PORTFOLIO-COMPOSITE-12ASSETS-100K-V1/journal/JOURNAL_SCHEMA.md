# JOURNAL_SCHEMA + LOSS-ANALYSIS PROTOCOL — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (pre-GO draft)

Append-only journal for EVERY order intent in every backtest — including
signals that were blocked, deferred, netted-to-zero or fail-closed. One
JSONL row per order-lifecycle event; hash-chained per run
(`prev_row_sha256`), written under the trial's freeze SHA. Nothing is ever
edited after write; corrections are new rows with `corrects_row_id`.

## 1. Row schema (journal_row@1)

Decision-time block (known BEFORE the order exists):
- `ts_decision_utc`, `fold_id`, `cycle_id`, `sleeve_id`, `corpus_gid`/
  `class_candidate_id`, `symbol`, `family_id`, `mech_key`
- `feature_pit_snapshot`: {`input_id`, `available_time_utc`, `value_digest`,
  `max_age_ok`: bool} — one entry per PIT input; any staleness ⇒ row still
  written with `outcome=BLOCKED_STALE`
- `direction_vote` (−1/0/+1), `desired_risk_units`
- `entry_reason_code` (frozen enum from leg spec), `eligibility_state`
  (ON/PROBATION/OFF + which E-rule), `risk_rule_state` (L5 caps active,
  headroom before/after), `portfolio_state` (n_eligible, portfolio_heat,
  cluster_exposures at decision)

Order/fill block:
- `order_id`, `order_kind` (OPEN/CLOSE/ROLL/ADJUST/DEFER), `ts_fill_utc`,
  `fill_price`, `fill_side_quote` (bid/ask), `spread_pips_charged`
  (C1/C2/C3 cell id), `slippage_beyond_spread` (U3 band id), `venue_model`
  (PANEL_DUKA | IBKR_TRANSFERRED)
- `commission` (U2 declared id or measured ref), `swap_financing`
  (per-night accrual rows with Wed×3 flag), `roll_cost` (futures/CFD legs
  only — none at registration), `fx_conversion` (quote→USD, rate + source ts)

Outcome block (written at close; never back-filled silently):
- `gross_pnl_usd`, `cost_total_usd`, `net_pnl_usd`, `mae_pips`, `mfe_pips`
  (from M1/H1 path between fill and close), `hold_bars`, `exit_reason_code`
- `size_at_open` (units + notional), `exposure_after` (per asset/cluster/
  portfolio), `turnover_usd`
- `outcome` enum: `FILLED` | `BLOCKED_STALE` | `BLOCKED_FLOOR` |
  `BLOCKED_COST_BUDGET` | `BLOCKED_RISK_CAP` | `NETTED_TO_ZERO` (tie) |
  `DEFERRED_COST_GUARD` | `KILLSWITCH_FLAT`
- `blocked_reason_detail` (free text, frozen enums preferred)

## 2. Reconciliation (per-bar, per-run; a scored run that fails it is void)

1. Σ position deltas from FILLED rows == positions ledger at every bar.
2. Cash: equity(t) == equity(t−1) + Σ net_pnl(closed) + Σ mtv(open) − Σ
   costs(accrued); residual must be 0 to 1e-9.
3. Every BLOCKED row's stated rule must be re-derivable from the frozen
   policy inputs at `ts_decision_utc` (recompute check on a 1% sample, full
   recompute on STOP-3 integrity trips).
4. `UNAVAILABLE` inputs abort the affected leg (fail-closed), never 0-fill.

## 3. Loss taxonomy and investigation loop

Every closed trade with net_pnl < 0 is tagged with exactly one primary
cause (+ optional secondary), assigned by mechanical rules first:

| code | mechanical test | then investigated by |
|---|---|---|
| `LOSS_COST` | gross_pnl > 0 ≥ net_pnl | cost-bill decomposition vs entry estimate |
| `LOSS_SIGNAL` | adverse excursion begins <2 bars after fill, no regime move | leg-rule forensics (was the entry inside its declared edge conditions?) |
| `LOSS_REGIME` | asset realized vol / cross-asset correlation outside TRAIN envelope at entry | regime-envelope audit (descriptive, NOT a new gate source) |
| `LOSS_FILL` | fill beyond modeled spread+slip p99 | venue/fill-model audit |
| `LOSS_SIZING` | loss > 2× per-decision risk budget | sizing-path audit (vol estimate error?) |
| `LOSS_CONCENTRATION` | trade closed during cluster co-drawdown episode (≥2 assets in cluster simultaneously −1σ) | cluster-map audit |
| `LOSS_UNKNOWN` | none of the above provable | recorded as UNKNOWN — never guessed |

Outputs required per fold (TRAIN folds only for learning; test folds only
for reporting):

- avoidable-loss ledger: losses a candidate pre-computable condition would
  have skipped, AND the profits the same condition would have skipped —
  both must be reported (no cherry side).
- condition promotion law: a loss-derived on/off condition may enter L2
  eligibility ONLY if (a) fitted on folds strictly EARLIER than the fold
  where it is evaluated, (b) it survives the same condition on ≥2 disjoint
  earlier folds, (c) it is frozen before evaluation, (d) it is not itself a
  regime-prediction variable in disguise (§POLICY-ARCH L2 forbidden list).
  If data insufficient to test (a)-(b): `INCONCLUSIVE` — recorded, not
  promoted. **Looking at the losses of the fold you are about to confirm
  with is forbidden** (owner law; enforced by fold-lock in the engine).

## 4. Co-loss and complementarity reporting (feeds Stage-B)

Per fold: joint-loss episode census (hours/days where ≥2 legs simultaneously
in drawdown), pairwise leg-PnL correlation, order-overlap rate (same asset
same bar), common-exposure integral, turnover and state-switch cost, and
portfolio DD vs max single-leg DD. These are the quantities the policy's
increment claim is measured against (POLICY-ARCH §8).
