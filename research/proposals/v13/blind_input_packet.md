# V13 blind input packet (frozen) — read this FIRST

You are a V13 blind proposal lane. Propose **exactly two** genuinely new
outcome-blind mechanisms **conditioned on positioning/liquidity information**
for Binance USD-M perpetuals (plan mission Q2). Write JSON+MD under your own
prefix `research/proposals/v13/<your-lane>/` (a5, a6, or a8).

## Isolation contract

You MAY read: this packet; `research/control/v13_run/run_contract.json`;
`research/control/v13_run/forbidden_family_inventory.json`;
`research/control/v13_run/v13_p_freeze.json`; `research/v12/data_contract.py`
and `research/v12/load_validation.py` (schema/windows only);
`research/data_fusion/models.py`, `research/data_fusion/pit.py` and
`research/data_fusion/crypto_compat.py` (record schema + availability
semantics); `research/v11/cost_feasibility.py` (schedule-only feasibility);
public literature and official venue/API documentation (log every query,
retrieval UTC, and accept/reject reason).

You MUST NOT read: any family metrics or scored artifacts, terminal reports,
`research/control/v12_run/*` (the V12 forbidden inventory is carried into the
V13 inventory file; read only that), other lanes' proposals, anything under
S1, `research/audits/*`.

You MUST NOT compute returns, PnL, PF, Sharpe, rankings or run backtests.
Literature search must finish before you would compute any candidate return.
You MUST NOT read any per-arm outcome file — none will be given.

## Data you may design against (schema only)

Universe: 20 Binance USD-M perpetuals (BTCUSDT = context benchmark only).
Authorized window: 2024-08-20T00:00:00Z..2026-08-21T00:00:00Z; blind-S0
screen window 2025-08-22..2026-08-21; folds F0/F1/F2 chronological with 1-day
purge. Fields: completed 15m bars (available at bar CLOSE); funding
settlements (mixed 8h/4h/1h cadences; available at settlement stamp); daily
open interest (available at OI snapshot stamp); mark price snapshots;
instrument tick sizes. PIT AUTHORITY (new in V13): fusion-record availability
semantics — a decision at T can never read a row whose `available_time_utc >
T`; retrieval time never substitutes for availability.

## Conditioning space (mission Q2)

Mechanisms must be conditioned on positioning/liquidity information: open
interest and its dynamics, positioning crowding, liquidity provision,
market-making pressure, depth/turnover structure. Boundaries:

- V12 OILEV-V2 (OI-deleveraging) is FORBIDDEN including any sign flip,
  horizon tweak, cap raise, universe carve-out or renaming — see inventory
  entry V12-OILEV-V2;
- funding-carry / crowding-premium rescues (V6 family) remain FORBIDDEN;
  funding may appear only as a COST, never as the signal;
- ordinary momentum, reversal, volume-shock, LOT/MAX/skew, Amihud variants:
  all FORBIDDEN per the inventory.

## Shadow-effect region (plan section 1.1) — the only sanctioned re-entry

A proposal may state a NEW economic mechanism in the shadow region (e.g. a
liquidity-provision / crowding-premium story) ONLY through the front door:
(1) the mechanism is stated in its own words, never as "the inverted anchor";
(2) the packet DISCLOSES that the sign was already observed in a V12/V11
control arm (inverted OI-flow +0.758; V11 LOT inversion; stocks vol-level
sorting) and the family is preregistered as CONFIRMATORY;
(3) it carries its OWN causal negative control separating the new mechanism
from the rejected ancestor AND from beta/funding carry;
(4) A7-N will enforce rank correlation |rho| <= 0.20 against the frozen
OILEV-V2 anchor AND its inverted control on the common window, else the
proposal is INELIGIBLE;
(5) Stage-A gates apply with no relaxation; confirmatory status is recorded
in the verdict and denominator.

## Costs, floors, constraints (frozen, inherited from V12)

Generic adapter fees/slippage, native funding while held (cost only), stress =
fee x1.5 / +2 ticks / +1 event delay. Floors: <=60 discretionary
decisions/365d; median holding >=3d; base cost drag <=8%/yr of gross;
stressed <=12%; no symbol >25% of turnover; max |weight| <= 0.30 at every
stamp by construction. Every proposal = anchor + justified neighbour + causal
negative control (exactly 3 arms). Sprint ceiling: 6 scored cells across at
most 2 selected families (budget 9, unused slots never reassigned).

## Required proposal content (per proposal)

1. Hypothesis ID `A13-V13-<NAME>` + one-paragraph mechanism (economic
   counterparty, why the edge exists, expected sign);
2. falsifiable prediction (what outcome would falsify it);
3. literature: primary-source claim + crypto-perpetual transfer caveats
   (queries + retrieval UTC logged);
4. PIT observable with fusion-record availability semantics (fields + clock);
5. universe, warmup, decision clock (weekly-or-slower, Monday 00:00:00Z),
   holding, rebalance/fill schedule (one declared execution lag);
6. anchor + one neighbour (same mechanism, different justified parameter) +
   one causal negative control (preregistered rule under which the control
   MUST NOT reproduce the anchor);
7. incremental test vs buy-and-hold AND BTC-beta context (gate: excess
   positive in >= 2/3 folds);
8. base and stress costs; turnover and sample floor; concentration and
   drop-one design (drop must select a held maximum-|weight| symbol);
9. failure interpretation (what each failure mode means);
10. source-to-test map (every input field -> exact test use);
11. ancestry map vs the forbidden inventory: why this is NOT a variant,
    inversion, rescue or renaming of any listed family;
12. if in the shadow region: the section 1.1 front-door disclosures;
13. signed outcome-blind attestation (you computed no returns/PnL and saw no
    outcome files).

## Attestation block (end of each MD)

```
OUTCOME-BLIND ATTESTATION
lane: <a5|a6|a8>  proposal: <A13-V13-NAME>
I wrote this mechanism and its falsification conditions before computing any
return, metric or ranking, and without access to any scored artifact or
outcome file.
utc: <retrieval-completion UTC>  agent: <lane id>
```
