# STOP-1 — OWNER GATE PACKET (ETHUSDT-OPEN-SEARCH-V1)

Status: **AWAITING OWNER GO.** A7 prelaunch delta r1 =
`AUTHORIZED_FOR_STOP1` (0 findings). Budget 0/8 consumed. S1
SEALED_UNTOUCHED. Zero scored PnL computed. This packet is the campaign
charter the owner accepts by typing the GO phrase.

## What will run on GO

8 scored cells (2 lanes × 4 round-ladder configs, all frozen in
`freezes/eos1_freeze.json`), each on the staged corpus
2020-01-01..2026-08-31 (ETHUSDT USDT-M perp H4, measured funding, fee
5 bps/side + 1 adverse tick, tiers ×1.0/×1.5/×2.0), against frozen
references (BASE_CASH / BASE_ALWAYS_ON_LONG / BASE_TREND_LF /
REF_SHORT_ALWAYS) and preregistered controls (block-shuffle 30-bar of the
info series; sign-inversion), under gates G1–G11 (plan §6):

- **Lane E1** — BTC-information execution: A1 BTC SMA200(H4)→ETH long/flat;
  A2 BTC SMA100(H4); A3 BTC 30d momentum sign; A4 A1 ∧ ETH-SMA200 (combo).
- **Lane E2** — ETHBTC rotation: B1 ratio > SMA600(H4) (~100d); B2 ratio >
  SMA1200 (~200d); B3 ratio 90d pct-rank > 0.50; B4 B1 ∧ BTC-SMA200.

## Evidence state at this gate

- Data: 4 series staged (manifest sha-pinned); ETHUSDT/BTCUSDT 1h zero
  gaps; funding 7,305 settlements from exactly 2020-01-01T00:00Z; ES1
  cross-check 80/80 months byte-identical; census BUILD_PASS.
- Engine: hand-computed fixtures 10/10 groups ALL PASS (incl. PIT
  no-lookahead mutation, cost-exactly-once, funding sign, fold
  force-flat, tier scaling, settlement PIT law).
- Dry-run: 84/84 computations, pairwise-distinct record IDs, leak-scan
  clean, all books non-vacuous, denominator delta 0.
- A7 (fresh context, adversarial): freeze chain byte-exact; census
  reproduced from raw bytes; ancestry adjudicated — both lanes are
  genuinely new (info-source, vehicle) tuples vs all 40 crypto dead
  families, no veto; 2 blocking findings remediated + delta-verified.

## Overfit risk (preregistered honesty)

Everything is POSTHOC (outcome-observed windows; plan §1). The G5 fold
concentration bar (≤0.50) is expected to be the structural killer —
ETH's F1 2020-21 rally dominates every long book's fold profile. A NO
result is a valid terminal; the campaign then opens tranche V2 under the
standing directive. A survivor earns ONLY
`POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION` — deployable
evidence still requires a prospective sleeve decision.

## The exact phrase the owner must type at this gate

```
GO ETHUSDT OPEN SEARCH V1 SCORED EXECUTION
```

Any other phrasing is refused and recorded; a GO typed before this packet
existed dies unconsumed; the GO does not survive pauses or transfer.
