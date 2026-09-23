# PLAN EURUSD-OPEN-SEARCH-V1 — after-cost EURUSD strategy open search (D2 owner-waived exploratory)

> Registered 2026-09-23 by A1 under explicit owner instruction of the same
> date. S0 exploration ONLY. The owner instruction of 2026-09-23 is the sole
> authorization for opening this cycle; it is NOT a scoring GO.

## 0. Cycle identity

```text
cycle_id     EURUSD-OPEN-SEARCH-V1
class        STRATEGY SEARCH (exploratory S0, after-cost PnL permitted ONLY
             after the §1 data precondition passes)
asset        forex (EURUSD only)
budget       24 families × 4 configs/family = 96 exploratory trials MAX
             (observed denominator counts every scientifically computed
             trial, winners and losers alike)
S1           SEALED_UNTOUCHED (the §3 historical holdout is program-S0; it is
             NEVER called S1 and never grounds a real-money claim)
orders       NONE (no paper/live/order placement of any kind)
go_phrase    GO EURUSD OPEN SEARCH V1 EXPLORATORY SCORED
             (typed only at this cycle's own gate, after A7 prelaunch, by
             the owner; the 2026-09-23 instruction is NOT a GO)
forbidden    JEV-REGIME-ROUTER-V1/V2 surfaces; research/control/
             SANDBOX-OVERFIT-3ASSETS/; research/control/d2_curiosity_v1_sources/;
             research/control/bear_opportunity_recon_2026-09/; editing any
             historical forex cycle verdict (FOREX V1–V9, NG1–NG7,
             FX-FUTURES-FRONTIER-V1, FOREX-INTRA-BIDASK-V1,
             EURUSD-DATA-QUALIFICATION-V1 — all read-only evidence)
```

## 0a. Owner directive anchors (2026-09-23, binding)

- D2 novelty/mechanism screening is WAIVED before backtest IN THE
  EXPLORATORY PHASE ONLY. Every record states `D2 = OWNER_WAIVED_EXPLORATORY`.
  Writing "D2 PASS" is FORBIDDEN (the gate was not evaluated).
- NOT waived, ever: data/license/PIT authority, measured costs, trial
  accounting, reproduction, A7 independence, owner GO, S1 seal, machine-wide
  heavy lock.
- Data unlock precedes ANY PnL computation. No PnL may ever be derived from
  a source lacking demonstrated research rights. No account creation, no
  terms acceptance, no purchases on the owner's behalf; no secret ever
  printed or committed.
- Spread and swap are measured, never assumed zero. Mid-only data may drive
  signal research but can NEVER ground an after-cost PASS verdict.
- Stop at the owner gate with: source status, the ACTUAL trial denominator,
  frozen candidates, costs, overfit risk, and this cycle's GO phrase.

## 1. Data precondition (blocking, before any PnL)

A source qualifies ONLY with per-source artifacts proving ALL of:
access+storage rights for internal research; instrument identity; true
bid/ask; timestamp semantics + data availability time; 3–5 year coverage;
gap/DST/weekend census; raw-byte SHA-256 manifest; deterministic re-download;
cost. Candidate order per owner 2026-09-23: TrueFX (from its original
terms — re-surveyed 2026-09-23, still login-gated with no public license;
status `CANDIDATE_NOT_AUTHORIZED`), OANDA v20 Practice ONLY if an
owner-issued account/token already exists (env census 2026-09-23: none
exists), Dukascopy ONLY with written consent text in evidence (none exists;
site TCU forbids automated acquisition + database construction).

Rules:

- Price-mid-only research is allowed for SIGNAL exploration; any after-cost
  PASS verdict requires two-sided bid/ask fills on licensed data.
- Spread measured per session (Asia/London/NY-overlap/NY-late) and at the
  21:00–22:00 UTC rollover; overnight/weekend holding requires PROVEN
  swap/financing data, else every strategy must close before rollover.
- No qualifying source ⇒ close exactly one of `BLOCKED_SOURCE_LICENSE` or
  `BLOCKED_COST_AUTHORITY` with the precise owner actions; ZERO PnL exists.

## 2. Search design (no D2)

Lanes: A2 data/PIT + costs; A3 hypothesis authoring (outcome-blind until
its own batch); A4 critique + trial control (denominator, identity, cost
sanity); A7 audit-only, never repairs.

Family census (each gets at most 4 configs at selection freeze):

```text
FXOS-01 trend MA-cross          FXOS-13 Asia-session range
FXOS-02 trend Donchian          FXOS-14 rollover-liquidity effects
FXOS-03 trend slope/regression  FXOS-15 intraday carry-drift (pre-rollover close)
FXOS-04 MR Bollinger fade       FXOS-16 CPI print (PIT calendar)
FXOS-05 MR RSI extreme fade     FXOS-17 NFP print (PIT calendar)
FXOS-06 MR rolling z-score      FXOS-18 central-bank decision (PIT calendar)
FXOS-07 failed-breakout fade    FXOS-19 pre/post-event drift avoidance
FXOS-08 ATR range breakout      FXOS-20 cross-asset momentum spillover
FXOS-09 volatility-contraction  FXOS-21 tick imbalance / order-flow proxy
FXOS-10 London-open momentum    FXOS-22 candle pattern + filters
FXOS-11 NY-open momentum        FXOS-23 EURUSD vs correlated pair spread
FXOS-12 London/NY overlap       FXOS-24 time-of-day seasonality
```

D2 novelty/mechanism veto is NOT applied (owner-waived exploratory). Old
failure memory is read for understanding, never as a pre-backtest veto.
Every executed trial records: trial ID, family, exact rules, parameters,
data snapshot SHA, cost tier, rationale — including every loser. The
denominator is bounded: no infinite reuse of the same data window.

## 3. Development / holdout protocol

- Split rule (preregistered NOW, dates frozen at data-manifest freeze,
  before any PnL): development = full coverage minus the FINAL ~30% of the
  timeline (min 18 months); historical holdout = that final block. The
  holdout is SEALED for the entire exploratory phase — no code, no eyes, no
  summaries.
- Inside development: walk-forward with warmup and purge/embargo; rule and
  config selection use development after-cost results ONLY.
- No early stop on a positive number. The close reports the FULL
  distribution of the 96-trial campaign: negative/positive counts, fees,
  turnover, parameter sensitivity.
- At most 1–2 candidates frozen (`NO_CANDIDATE` otherwise). No candidate
  becomes a strategy claim: verdicts are limited to "candidate pending
  prospective verification" or "no value".

## 4. Costs and fills

Two-sided marketable fills at the OPPOSITE quote (buy@ask, sell@bid) at
next-bar-open; measured per-session spread medians as base cost; stress
tiers 1.5× and 2.0× mandatory; latency charged at one bar minimum;
rollover handling per §1. Baselines at freeze, run identically: CASH;
naive long-only and short-only over the same hours; random-matched entries
(matching trade count and holding-time distribution); plus any suitable
existing forex baseline artifact if one exists at execution time.

## 5. Candidate check (P3)

Code/data/strategy/benchmark/gates freeze BEFORE the first holdout
opening; A7 prelaunch audits the freeze; owner GO (two-key, fresh, verbatim)
launches the single holdout run. ONE look at the holdout. A failed holdout
is final for this campaign: no re-tuning against the same holdout; any
next round requires NEW future data or an owner-opened successor campaign
with the contaminated holdout declared. The holdout result is program-S0
evidence, never S1, never a profitability confirmation.

## 6. Governance

Mandatory implementation tests: PIT/no-lookahead mutation, bid/ask fill
correctness, calendar/DST/weekend, cost-once accounting, trial counter
integrity, fail-closed on malformed data. Heavy lock per law. A7
fresh-context prelaunch audit before any scored computation. Terminal
verdict enum (exactly one): `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` |
`NO_CANDIDATE_NO_VALUE` | `BLOCKED_SOURCE_LICENSE` |
`BLOCKED_COST_AUTHORITY` | `TECHABORT`. No paper/live/order surfaces.

## 7. Current state at registration (2026-09-23)

P1 re-survey artifact:
`research/control/EURUSD-OPEN-SEARCH-V1/P1_SOURCE_RESURVEY_2026-09-23.md`.
No qualifying bid/ask source exists today (TrueFX gated + no public
license; no OANDA credentials; no Dukascopy consent; no new rights since
the 2026-09-22 verdict). Cycle registers `BLOCKED_SOURCE_LICENSE` with
zero PnL and zero trials executed; the owner actions listed in the verdict
are the unblock paths. Trials (≤96) run only after a source clears §1.
