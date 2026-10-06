# 6B — British Pound Futures Research Framework

**Core exposure:** GBP/USD exposure driven by BoE-Fed differentials, UK growth/inflation, fiscal credibility, and risk sentiment.

**Key participant groups:** banks, corporates, asset managers, macro funds, CTAs, market makers.


## 1. Foundation questions
- What exactly does this contract represent economically?
- Who must trade it for hedging reasons, and who trades it for speculation/arbitrage?
- What determines fair value versus the related cash/spot market?
- Which expiries are normally liquid, and when does liquidity migrate?
- What settlement/delivery mechanics can distort the front contract?
- Which session contains the most information and liquidity?
- What is the minimum data needed to reconstruct a tradeable PIT series?

## 2. Market structure questions
- How does volume distribute by session and expiry?
- How quickly does volume/OI shift during roll?
- Does spread widen materially overnight, near releases, or near expiry?
- Are there recurring opening/settlement/roll effects?
- Which contract-selection rule is most stable: calendar, volume, OI, or hybrid?
- How much does back-adjustment methodology alter apparent trend signals?

## 3. Causal-driver research
For every driver below, build a table with: source → mechanism → expected sign → horizon → regime → PIT source → confounder → falsification test.

## 4. Regime map
At minimum classify:
- volatility: low / medium / high
- trend: trending / range / crisis
- monetary regime: easing / neutral / tightening
- USD regime: weak / neutral / strong where relevant
- liquidity: normal / stressed
- contract-specific fundamental regime

Questions:
- Which relationships are invariant across regimes?
- Which only exist during stress?
- Does signal sign flip across regimes?
- Is the apparent edge merely a volatility-scaling artifact?

## 5. Event-study framework
For every scheduled event:
1. Define event timestamp in exchange time and UTC.
2. Store consensus, actual, prior, revision, and surprise if available.
3. Measure returns at 1m, 5m, 15m, 1h, session-close, 1d, 3d.
4. Measure spread and volume response.
5. Condition on regime and positioning.
6. Separate first reaction from subsequent drift/reversal.
7. Test whether entering 1–5 minutes later destroys the edge.

## 6. Term-structure / roll research
- Build raw individual-contract panel.
- Build front, second, third, and farther expiries using PIT contract selection.
- Compute calendar spreads, slope, curvature, roll yield, and days-to-expiry.
- Compare calendar roll vs volume roll vs OI roll.
- Test signals on unadjusted and back-adjusted continuous series.
- Explicitly verify no price jump created by vendor stitching is treated as alpha.

## 7. Cross-asset research
For every related market:
- contemporaneous correlation
- rolling beta
- lead/lag
- response conditional on volatility
- response conditional on macro surprise
- relative-value spread / ratio
- whether the relation survives transaction costs and entry delay

## 8. Candidate-signal design
For each candidate signal specify:
- economic mechanism
- exact formula
- PIT availability
- normalization
- entry/exit
- holding horizon
- expected turnover
- execution assumption
- regime filter
- invalidation condition

## 9. Backtest protocol
Required:
- individual expiry contracts, not vendor continuous only
- walk-forward OOS
- year-by-year attribution
- regime attribution
- long vs short split
- costs at baseline / 1.5× / 2×
- delayed-entry test
- alternate roll rule
- parameter perturbation
- bootstrap / block-resampling where appropriate
- exposure and correlation with other portfolio legs

## 10. Data checklist
Databento phase-1:
- `ohlcv-1m`
- `definition`
- `statistics`
- individual expiries from 2010-06-06 onward where available

Selective later data:
- `bbo-1m` or `bbo-1s`
- `mbp-1` only for execution/microstructure validation

External PIT data should include release timestamp, timezone, and vintages/revisions where relevant.

## 11. Failure-mode checklist
Reject or flag if:
- edge disappears under realistic costs
- one crisis year explains most PnL
- revised data are used as if known historically
- roll convention creates the signal
- performance requires same-bar execution at event timestamps
- relationship is unstable without a defensible regime explanation
- contract liquidity is insufficient at the assumed size

## 12. Research deliverables
Produce:
1. market-mechanics memo
2. causal-driver table
3. event calendar
4. term-structure diagnostics
5. cross-asset matrix
6. candidate hypotheses ranked by testability, not by backtest return
7. data-gap table
8. PIT audit
9. backtest report
10. rejection log for failed hypotheses


## 13. Contract-specific driver map
### Primary drivers
- BoE-Fed policy differential
- UK wage/inflation data
- UK growth/PMIs
- fiscal policy and gilt stress
- risk sentiment
- USD cycle
- energy/import terms of trade

### Related markets / confirmation variables
- 6E
- gilts vs Treasuries if sourced
- FTSE
- DXY
- ES/VIX

### Scheduled / recurring events
- BoE
- UK CPI/wages
- UK GDP/PMIs
- UK fiscal statements
- FOMC
- US CPI/NFP

## 14. Contract-specific foundation questions
- When do UK-specific fiscal risks dominate global USD factors?
- How persistent are BoE repricing shocks?
- Does GBP behave more like a European currency or risk-sensitive asset in each regime?
- Which UK data releases have persistent versus mean-reverting effects?

## 15. High-value hypotheses to test first
- GBP reacts more to UK rate repricing when inflation persistence is high
- GBP underperforms EUR during UK-specific fiscal credibility shocks
- London-session breakouts differ by macro regime
- Relative surprise UK-vs-US predicts multi-day direction

For each hypothesis, explicitly write the causal mechanism and a falsification condition before running the backtest.

## 16. Contract-specific failure modes
- Brexit-era structural breaks
- fiscal-event jumps
- thin Asian-session liquidity
- cash/futures basis and roll

## 17. First research sprint
1. Build PIT contract panel from Databento definitions.
2. Create liquidity and roll diagnostics by year.
3. Build baseline 1-minute return/volatility/session statistics.
4. Add the top 3 causal drivers using PIT-safe sources.
5. Run event studies before building full trading rules.
6. Test 3–5 hypotheses with walk-forward validation.
7. Reject aggressively if edge depends on one regime or unrealistic execution.