# V11 Literature evidence packet — FROZEN 2026-09-02T14:42:11Z

Producer: A1 (L0, PLAN.md §8.1). Frozen BEFORE any V11 scored result exists
(V11 budget 0/12; no scored artifact in any V11 tree). Retrieval method:
web search + publisher/DOI identity verification on 2026-09-02T14:42:11Z. No commentary,
social posts or vendor backtests were used to establish any mechanism.

## Source identity (verified)

- **S1. Revisiting the low-volatility anomaly in cryptocurrency markets** — Sujin Pyo, Huisu Jang (2026), Finance Research Letters (Elsevier), vol. 97, art. 109851. DOI 10.1016/j.frl.2026.109851 · https://www.sciencedirect.com/science/article/abs/pii/S1544612326003818 · retrieved 2026-09-02T14:42:11Z
- **S2. Speculation and lottery-like demand in cryptocurrency markets** — Klaus Grobys (2021), Journal of International Financial Markets, Institutions and Money (Elsevier), vol. 71, art. 101289. DOI 10.1016/j.intfin.2021.101289 · https://www.sciencedirect.com/science/article/pii/S1042443121000081 · retrieved 2026-09-02T14:42:11Z
- **S3. Lottery-like preferences and the MAX effect in the cryptocurrency market** — M. Ozdamar et al. (2021), Financial Innovation (SpringerOpen), vol. 7, art. 79. DOI 10.1186/s40854-021-00291-9 · https://d-nb.info/1246248476/34 · retrieved 2026-09-02T14:42:11Z
- **S4. Binance USD-M Futures market data endpoints (klines, funding rate history, open interest, mark price)** — Binance (official venue documentation) (2026), developers.binance.com — derivatives USDⓈ-M market data. DOI n/a · https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api · retrieved 2026-09-02T14:42:11Z

## Claim → test mapping (frozen)

| Element | Frozen value |
|---|---|
| source claim | falsifiable crypto-perpetual hypothesis |
| required PIT fields and transformation | completed 15m bars -> daily UTC close aggregates; features from COMPLETED bars only; one declared execution lag after availability |
| formation/holding/rebalance clock | weekly-or-slower per owner brief |
| expected sign and economic counterparty | predeclared per family |
| causal negative control | sign-destroying inverted book |
| external-validity risks | spot-to-perp transfer, funding drag, shorting/borrow, survivorship/listing bias, liquidity filters, BTC beta, costs, publication-sample overlap, universe/history availability in frozen snapshot |
| repo test that could reject the claim | schedule-only cost gate (A3), causal control sign test, PIT/no-leak fixtures, orthogonality rho vs rejected ancestors (A7-N), Stage-A gates (PLAN 15) |

## Family 1 — V11-SEED-DEFENSIVE-RESIDUAL-RISK (from S1)

- **Hypothesis (falsifiable):** coins with LOWER trailing BTC-residualised
  total/downside risk outperform HIGHER-risk coins on a beta-aware long/short
  perpetual book held weekly-or-slower, after adapter costs and native funding.
- **PIT fields:** completed 15m bars → daily UTC closes (both symbol and BTC);
  rolling 90d daily beta vs BTC frozen rule; residual return r_i − β_i·r_BTC.
- **Clock:** 28d formation; weekly (7d) rebalance; ≥3d effective holding.
- **Expected sign / counterparty:** long low-residual-risk / short
  high-residual-risk; counterparty = lottery-seeking leverage demand that
  over-trades high-vol coins and pays funding.
- **Causal negative control:** sign-INVERTED same book (high-risk minus
  low-risk). If it also earns positive net spread, the mechanism claim is dead.
- **External validity:** spot→perp transfer re-earned; funding charged while
  held; perp shorting native; PIT listing/survivorship via repo snapshot;
  liquidity filter; BTC beta residualised by construction; taker+slippage via
  adapter; papers' spot sample predates the repo window (disclosed).

## Family 2 — V11-SEED-LOTTERY-MAX-SKEW (from S2, S3)

- **Hypothesis (falsifiable):** coins with LOWER trailing BTC-residualised MAX
  outperform HIGHER-MAX coins on a low-lottery vs high-lottery book,
  weekly-or-slower, after costs and funding.
- **PIT fields:** daily residual series (90d beta rule) → MAX = max daily
  residual return over trailing 7d; alternative idiosyncratic skew = 30d
  rolling skew of residual dailies.
- **Clock:** 7d feature window; weekly (7d) rebalance; ≥3d effective holding.
- **Expected sign / counterparty:** long low-lottery / short high-lottery;
  counterparty = preference-driven overpaying for jackpot payoffs.
- **Causal negative control:** sign-INVERTED MAX book (high-MAX minus
  low-MAX); positive net spread on the inverted book falsifies the mechanism.
- **External validity:** as Family 1, plus tail-sensitivity: no single fold or
  symbol may dominate (Stage-A concentration gates).

## Rules binding all consumers

1. Published returns are PRIORS. They never waive novelty, orthogonality,
   data, cost, stress, negative-control or A7 gates.
2. L0 inspected schema/coverage/prewindow diagnostics only; no candidate
   returns, PnL, PF, Sharpe or ranking on the scored window were computed.
3. Literature search by outcome-blind lanes must finish before any lane
   computes candidate returns (PLAN §8.2).
4. Any threshold change requires an owner amendment BEFORE proposal scoring.

## Hashes (frozen)

See literature_evidence_packet.json `artifact_hashes` — computed at freeze by
A1 over these exact bytes.
