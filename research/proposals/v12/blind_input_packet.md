# V12 blind input packet (frozen) — read this FIRST

You are a V12 blind proposal lane. Propose **exactly two** genuinely new
low-turnover mechanisms for Binance USD-M perpetuals. Write JSON+MD under
your own prefix `research/proposals/v12/<your-lane>/`.

## Isolation contract

You MAY read: this packet; `research/v12/data_contract.py` and
`research/v12/load_validation.py` (schema/windows); `research/adapter_v10/`
`protocol.py`, `base.py`, `facade.py`, `benchmarks.py`, `stress.py`
(interfaces); `research/v11/cost_feasibility.py` (schedule-only feasibility
interfaces); `research/control/v12_run/forbidden_family_inventory.json`;
public literature and official venue/API documentation (log every query,
retrieval UTC, and accept/reject reason).

You MUST NOT read: any V11 family metrics or scored artifacts, terminal
reports, `research/control/v11_run/*` (except the forbidden inventory),
other lanes' proposals, anything under S1, `research/audits/*`.

You MUST NOT compute returns, PnL, PF, Sharpe, rankings or run backtests.
Literature search must finish before you would compute any candidate return.

## Data you may design against (schema only)

Universe: 20 Binance USD-M perpetuals (BTCUSDT = context benchmark only).
Window: 2025-08-22T00:00:00Z..2026-08-21T00:00:00Z. Fields: completed 15m
bars; funding settlements (mixed 8h/4h/1h cadences on some symbols); daily
open interest (2025-07-01..2026-08-21); instrument tick sizes 1e-7..1e-2.
PIT: completed bars + last completed OI row strictly before the stamp; one
declared execution lag. Decision clock: weekly-or-slower, Monday 00:00:00Z.

## Costs, floors, constraints (frozen)

Generic adapter fees/slippage, native funding while held, stress = fee x1.5 /
+2 ticks / +1 event delay. Floors: <=60 discretionary decisions/365d; median
holding >=3d; base cost drag <=8%/yr of gross; stressed <=12%; no symbol >25%
of turnover; max |weight| <= 0.30 at every stamp by construction. Every
family = anchor + justified neighbour + causal negative control. Max 3 scored
cells/family; sprint ceiling 9; observed denominator 128.

## Ineligible

Everything in `forbidden_family_inventory.json`: LOT/MAX/skew inversion or
variants; Amihud/illiquidity variants (reserved); OI-deleveraging variants
(reserved); aggressor absorption; funding-carry rescues; ordinary momentum;
ordinary reversal; volume-shock continuation; renamed rejected baselines;
anything needing unavailable or purchased data.

## Required proposal content

Primary-source claim + crypto-perpetual transfer caveats; economic
counterparty + expected sign; PIT fields + availability clock; universe,
formation, holding, rebalance schedule; target book + beta/risk
neutralisation + expected turnover; anchor + neighbour + causal negative
control; fees/slippage/funding/stress treatment; falsification condition;
ancestry map vs V1-V11; why it is neither LOT inversion nor an ILLIQ/OILEV
parameter rescue.
