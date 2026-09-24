# PLAN FX-RANGEFADE-2M-SHADOW-V1 — prospective paper shadow for the combined majors book ("Phorec")

> Registered 2026-09-24 by A1 under the owner instruction "cộng EURUSD và
> GBPUSD lại thành 1 strategy và làm dashboard quant shadow giống như bên
> crypto ... đánh 1,5 lot". Paper/shadow ONLY (same class as
> PROSPECTIVE-SHADOW-V1): marks and hypothetical fills, ZERO broker/order/
> live surface. Dashboard name: **Phorec** (owner-chosen, owner-supplied logo).

## 0. Cycle identity

```text
cycle_id     FX-RANGEFADE-2M-SHADOW-V1
class        PROSPECTIVE SHADOW (paper tracking of a frozen strategy on
             live prices; produces prospective evidence, not S0 backtests)
asset        forex (EURUSD + GBPUSD)
budget       0 scored cells at open; shadow journal entries accrue weekly
strategy     RANGEFADE-2M = FX2-RANGEEXP-C3 config {lo_q 0.3, hi_q 0.7,
             fade} applied per pair, EURUSD + GBPUSD
size         1.5 lots per pair per signal (fixed, non-compounding) = max
             3 lots gross; pip value $10/lot/pair
S1           n/a (no S1 surface)
orders       NONE — never connects to any broker; quote feed is read-only
go_phrase    none registered (no scored surface at open; scored cells from
             the shadow journal follow the program's later governance)
```

## 1. Frozen strategy law (inherited, sha-verified)

- Signals: `v2_lib.f_rangeexp(p, 0.3, 0.7, use_breakout=False)` — the exact
  function scored in FX-MAJORS-SEARCH-V1 and audited byte-exact twice.
- Execution: signal on CLOSED H1 bar → fill at NEXT H1 open at the
  OPPOSITE quote (buy@ask, sell@bid; live TrueFX quotes in shadow);
  force-flat before 20:00 UTC daily; weekend flat; no swap (never
  overnight).
- Reconciliation duty: the shadow's H1 targets must equal the backtest
  engine's targets when fed identical bars (parity self-test runs at
  launch and weekly).

## 2. Price sources (disclosed, fail-closed)

- History seed: existing Dukascopy M1 bid/ask corpora 2021-01..2026-06 +
  a bridge download 2026-07-01..2026-09-23 (same source/scale probes).
- Live marks: TrueFX free streaming rates (webrates.truefx.com, indicative
  top-of-book, no account). Posture: OWNER_DIRECTIVE_SOURCE_AUTHORIZATION
  with TCU_RISK_DISCLOSED (same as all FX data in this program); read-only
  poll every ~15s; the vendor seam (Dukascopy bars → TrueFX marks) is
  disclosed and starts at shadow launch (2026-09-24): marks before/after
  the seam come from different vendors — spreads/levels may differ slightly
  and this is part of what prospective tracking measures.
- Fail-closed: quote staleness > 15 min → DATA_STALE (dashboard shows it,
  no decisions computed from stale bars); missing H1 bar → position stays,
  decision deferred; daemon death → heartbeat file goes stale and the
  dashboard shows OFFLINE. Weekend: feed poll continues, trading law keeps
  the book flat.

## 3. Shadow contract (dashboard + journal)

- State: `shadow_state.json` (equity on $100,000 seed, per-pair sleeve:
  position, entry, unrealized, fills, next decision time; marks with
  timestamps; DATA_STALE/OFFLINE indicators) written atomically every poll.
- Journal: `shadow_journal.jsonl` — append-only record of every fill,
  every daily flat, every H1 decision (with bar timestamps and quote
  provenance). This journal is the raw material of future weekly scored
  cells.
- Dashboard **Phorec**: local HTML (owner logo asset) served from the
  state file — equity, PnL total/day, per-pair sleeves, freshness,
  next-decision countdown; auto-refresh. Local-only bind (127.0.0.1).

## 4. Boundaries

No broker connectivity, no credentials, no orders (paper marks only);
no secrets; engine/strategy code frozen (parity-tested); any parameter
change = new plan + re-registration; heavy-lock law respected (light
poller; bridge download is probe-sized).
