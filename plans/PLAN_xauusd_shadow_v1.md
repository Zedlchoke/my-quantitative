# PLAN XAUUSD-SHADOW-V1 — forward internal shadow observation of one owner-specified XAUUSD technical strategy

> Status: `DRAFT_NOT_REGISTERED / PENDING A7 PLAN AUDIT`. Owner
> instruction 2026-09-21 (verbatim intent): "xây cho tôi strategy XAUUSD
> và đưa vào paper trading theo sau: Price within 0.3x ATR of a swing
> level / Price holding the right side of that level / EMA 9 and EMA 21
> aligned with the direction / Enough volatility to be worth trading"
> + clarification: "paper ý tôi là chạy trong app quant shadow này cho
> tôi coi. Hiện có hạ tầng shadow paper trading mà" — i.e. the INTERNAL
> shadow dashboard (PROSPECTIVE-SHADOW-V1 class), NOT external
> paper/testnet/live orders. Frozen reading: an internal virtual-ledger
> shadow sleeve exactly in the sense of PLAN_prospective_shadow_v1.md
> §2 (no order to any external venue, no broker account, no new
> credential, TARGET_INTENT records only).

## 0. Cycle identity

```text
cycle_id          XAUUSD-SHADOW-V1
asset             gold-fx (XAUUSD spot)
plan              plans/PLAN_xauusd_shadow_v1.md
budget            0/0 scored cells (shadow observation — NO bookable
                  claim, NO profitability language, ever)
S1                SEALED_UNTOUCHED
orders            NONE — internal virtual ledger only (shadow class)
go_phrase         GO XAUUSD SHADOW V1 START
dashboard         internal Quant Shadow Dashboard (integration constrained per §7)
```

## 1. What this cycle is NOT

- NOT a scored/research cycle: no acceptance battery, no Stage-A, no
  survivor language; shadow output is OBSERVATION ONLY.
- NOT external trading: no paper/testnet/live order, no broker, no
  account creation, no new credential (the ONLY key allowed is the
  pre-existing `EODHD_API_KEY` entitlement, never echoed).
- NOT a backtest: forward-only from SHADOW_START; historical bars are
  replayed ONLY for deterministic identity/warmup tests under the
  namespace `REPLAY_NOT_PROSPECTIVE` and are never reported as
  prospective performance.

## 2. Frozen strategy specification (frozen BEFORE any observation)

Owner's four conditions verbatim + frozen instantiations of every
underdetermined parameter (each marked [LEAD-FROZEN], chosen
outcome-blind, never tuned after any result is seen; a change = new
owner instruction + new cycle):

```text
instrument        XAUUSD spot, USD per troy ounce
bars              1h bars; decision at completed-bar close; fills at
                  the NEXT bar's open (F5-class clock) [LEAD-FROZEN]
warmup            200 completed 1h bars before the first eligible
                  decision (covers EMA21, ATR14, swing window, and the
                  volatility filter's 100-bar ATR median) [LEAD-FROZEN]

swing level L     fractal definition [LEAD-FROZEN]: a swing HIGH is a
                  bar whose high is the strict maximum of the window
                  [t-5, t+5]; swing LOW symmetric. A level is CONFIRMED
                  5 bars after its extreme bar (no lookahead). L = the
                  most recently confirmed swing level at decision time;
                  if both a high and a low confirm on the same bar, the
                  one with the larger |extreme − close| wins
                  [LEAD-FROZEN tie-break].

condition 1       |close_t − L| <= 0.3 × ATR14_t   (owner verbatim)
                  ATR14 = Wilder ATR, period 14, on 1h bars
condition 2       right side of the level (owner verbatim):
                  if L is a swing LOW  → long side: close_t >= L
                  if L is a swing HIGH → short side: close_t <= L
condition 3       EMA alignment (owner verbatim): long requires
                  EMA9_t > EMA21_t; short requires EMA9_t < EMA21_t
                  (EMA on close, standard alpha = 2/(N+1))
condition 4       enough volatility [LEAD-FROZEN instantiation]:
                  ATR14_t >= 0.15% of close_t AND ATR14_t >= 1.25 ×
                  median(ATR14 over trailing 100 completed bars)
direction         LONG only at swing LOWs, SHORT only at swing HIGHs
                  (condition 2 fixes the side; no双向 at one level)

entry             all four conditions true at bar close t → order
                  TARGET_INTENT at t+1 open [shadow fill model below]
exit [LEAD-FROZEN, owner gave none]: first of
                  (a) EMA9/EMA21 cross against the position at a
                      completed bar close → exit next bar open;
                  (b) hard stop: entry ± 1.0 × ATR14_entry (adverse);
                  (c) time stop: 48 completed bars after entry;
                  (d) shadow-session end (cycle stop) → flat at last
                      observed price.
sizing            fixed notional = 10% of sleeve equity per position,
                  one position at a time [LEAD-FROZEN]
fills             virtual: next-bar open ± half-spread; if the intended
                  entry/exit bar is missing from the feed, the intent
                  is NOT filled and is recorded UNFILLED_GAP (never
                  imputed) [fail-closed]
costs             virtual round-trip cost 4.0 bps of notional
                  [LEAD-FROZEN conservative constant; NO broker cost
                  authority exists for XAUUSD in this program —
                  FOREX-NG6-F4 class: components UNMEASURED, labeled]
sleeve equity     100,000 USD virtual at SHADOW_START
```

## 3. Data source (fail-closed, before any socket/request pattern freezes)

Primary candidate: EODHD intraday XAUUSD under the EXISTING
`EODHD_API_KEY` entitlement (no new credential). F1 three-layer
P-25-style gate for THIS cycle (reachable / permitted / served),
re-measured — the stocks-cycle entitlement does NOT automatically
extend to FX intraday; if any layer fails, the cycle is
`BLOCKED_SOURCE` and NO fallback source is improvised (owner decides).
Keyless fallbacks are listed for the owner only, not auto-used.

Collector requirements: light worker (NEVER the machine-wide heavy
lock), polling cadence ≤ 15 min for 1h bars, exchange timestamp +
local receive timestamp recorded, gap detection (missing bar hours
recorded, never filled), append-only raw layer + normalized layer,
hash-chained manifests, crash-safe resume, health heartbeat. The
XAUUSD weekend closure is a MARKET property: Sat/Sun gaps are recorded
as market-closed, not data gaps.

## 4. Ledger and labels

Append-only virtual ledger per PROSPECTIVE-SHADOW-V1 §2 class:
TARGET_INTENT → VIRTUAL_FILL → MARK_TO_MARKET rows; equity/drawdown
series; every row sha-chained. Every rendered number carries
`SHADOW_OBSERVATION_ONLY / NOT A PROFITABILITY CLAIM / COST MODEL
UNMEASURED-CONSERVATIVE`. No Sharpe/PF publication gating is claimed.

## 5. Dashboard integration (constrained)

The Quant Shadow Dashboard belongs to PROSPECTIVE-SHADOW-V1's runtime.
This cycle MUST NOT modify that cycle's engine or ledger. Integration
law: XAUUSD-SHADOW-V1 writes its OWN runtime tree
(`results/xauusd_shadow_v1/`); the dashboard gains an XAUUSD panel via
a minimal renderer-level addition audited in isolation (reads the new
tree only), OR a standalone overlay window — implementation choice
frozen at dispatch after A7 reviews which is least invasive. Either
way: zero writes into PROSPECTIVE-SHADOW-V1's runtime.

## 6. Gates / phases

```text
F1  source terms gate (EODHD FX intraday entitlement; fail-closed)
F2  canaries + double-pull byte-identity + never-existed-symbol canary
S   THIS plan §2 IS the frozen spec (nothing to freeze separately)
I   implementation lane (collector + sleeve engine + ledger + panel)
Z   sanitized dry-run on REPLAY_NOT_PROSPECTIVE historical bars
    (determinism, no-lookahead: every fill's information set <= t)
A7  fresh-context audit: plan (pre-registration), source terms,
    no-lookahead, ledger integrity, dashboard non-invasiveness
GO  owner types `GO XAUUSD SHADOW V1 START`
E   forward shadow (indefinite; weekly health checkpoints; WAITING_DATA
    if feed down — never FAIL for missing coverage)
```

## 7. Boundaries

No scored cells; no acceptance battery; no S1; no orders/credentials/
accounts; no purchases; light worker only (heavy lock reserved — the
co-tenant scored run owns it); no parameter change after any shadow
result is visible (frozen spec above is final); PROSPECTIVE-SHADOW-V1
untouched (its current dashboard DATA BLOCKED marks on 2 sleeves are
THAT cycle's scope — reported to the owner separately, not fixed
here).
