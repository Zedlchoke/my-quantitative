# A13-V13-A5-EXITCAP — Positioning crowding vs exit capacity (unwind-days)

Lane: a5 | Cycle: CRYPTO-V13 Phase D1 | Outcome-blind proposal (no computation performed)
Status: NEW mechanism, conditioning space = positioning crowding (mission Q2).
Shadow-region posture: voluntarily front-door compliant (section 12 below); confirmatory only if
A1/A7-N classify it into the shadow region.

## 1. Hypothesis ID and mechanism

Hypothesis ID: `A13-V13-A5-EXITCAP`

Binance USD-M perpetuals are continuously margined, leveraged position books.
`sumOpenInterest` measures the GROSS outstanding position stock (longs plus shorts);
it carries no directional OI time-difference in any signal below. The mechanism conditions
on the position STOCK relative to the market's routine risk-transfer CAPACITY: unwind-days
`U_i(T) = OI_notional_i(T) / mean daily dollar turnover_i(trailing 28d)` — the number of
days of average realized turnover required to unwind the open stock.

Economic counterparty: the forced deleverager. Perp positions are levered and auto-liquidated;
when the gross book is heavy relative to routine exit capacity, adverse moves trigger margin
liquidations whose flow exceeds what ordinary counterparties absorb, so liquidation feeds price
against the remaining book and more liquidations fire (cascade dynamic). Evidence base: forced
liquidations on leveraged crypto venues run at 1.9–3.5% of outstanding OI per day even in steady
state (Cheng et al. 2021, BitMEX); cascade-event studies show displayed depth systematically
overstates realizable liquidity exactly when crowded books unwind (SSRN 6891658, Bybit BTCPERP
cascade); practitioner post-mortems of the Oct-2025 deleveraging describe self-reinforcing
threshold dynamics (narrative only, not treated as evidence). Entry liquidity at the crowded
moment is therefore deceptive: the incumbent can enter but cannot rely on exiting at similar cost.

Why the edge exists: the market prices crowding by attention, not by exit capacity. Names whose
book is heavy relative to capacity carry a cascade-vulnerability tail that is systematically
undercompensated in the following week's expected return, because liquidation cascades in
aggregate crypto positioning are historically long-side dominated (Cheng et al.: long
liquidations 3.51% vs short 1.89% of OI per day — margin asymmetry and aggregate net-long bias),
and down-cascades destroy more value than up-squeezes create.

Expected sign: cross-sectionally, LOW unwind-days names outperform HIGH unwind-days names over
the next week. The arm is long the bottom tercile of unwind-days, short the top tercile.
The signal contains NO time-difference of OI, NO return term, NO funding term, NO price-impact
term.

## 2. Falsifiable prediction

Falsifiable prediction: after base costs, the EXITCAP-28D anchor earns positive BTC-beta-adjusted
weekly excess in at least 2 of the 3 frozen chronological folds, its neighbour (56d) supports the
same sign, and the static-scale control does NOT pass the same gate in the anchor's direction.
The hypothesis is FALSIFIED if any of: (a) the anchor's beta-context excess is not positive in
>= 2/3 folds; (b) the static-scale control reproduces the anchor's gate outcome (edge is raw
positioning scale, not capacity normalization); (c) the sign is opposite (high unwind-days
outperforms — cascade-vulnerability story wrong or already priced); (d) the neighbour flips sign
(parameter fragility, mechanism not stable). Any falsification rejects the family; the control is
never promotable to a family in its own right.

## 3. Literature (queries + retrieval UTC + accept/reject; transfer caveats)

Log (all retrieved 2026-09-04, UTC):

| # | Query | Retrieved (UTC) | Source | Verdict + reason |
|---|-------|-----------------|--------|------------------|
| L1 | open interest predict returns cryptocurrency perpetual futures crowding | 11:14 | Giagkiozis et al. 2024, "Reconciling Open Interest with Traded Volume in Perpetual Swaps", Ledger (ledgerjournal.org/ojs/ledger/article/view/325); practitioner crowding/OI pages | ACCEPT (academic) for the OI-vs-volume reconciliation framing: traded volume conflates position-opening and position-closing trades, so volume per unit of open stock is the natural positioning-intensity normalization. Practitioner pages REJECTED as evidence (no methodology), retained as narrative. |
| L2 | Bessembinder hedging pressure risk premium futures markets journal of finance | 11:14 | Bessembinder 1992, Review of Financial Studies 5(4) (correct venue; miscited as JF); De Roon, Nijman & Veld 2000, JF 55(3); Basu & Miffre 2013, JBF | ACCEPT as classic grounding that POSITIONING STRUCTURE carries risk premia in futures. CAVEAT: these use net hedger/speculator dispositions (COT), unavailable in crypto without a data purchase (DATA-GATED); we condition on the gross OI stock normalized by realized turnover — a different, side-agnostic variable; the mechanism (forced-deleveraging vulnerability), not the hedging-pressure premium, carries the sign. |
| L3 | liquidation cascade bitcoin perpetual futures open interest deleveraging empirical study | 11:15 | Cheng et al. 2021, Applied Economics 53(47) (forced liquidations 3.51% long / 1.89% short of outstanding OI per day, BitMEX); SSRN 6891658 (hidden liquidity/displayed depth during a Bybit BTCPERP liquidation cascade); Alexander 2023, EJOR (automatic liquidation mechanics) | ACCEPT (academic) for the cascade-vulnerability mechanism and the long/short liquidation asymmetry supporting the a priori sign. Amberdata "~5% of OI" threshold REJECTED as evidence (practitioner, no methodology). |
| L4 | crypto perpetual futures crowding factor open interest return predictability | 11:14 | ProSP (Physica A 2026, probability-based long-short on perp ranks); extrapolative-demand perpetuals paper (arXiv 2212.06888) | REJECT as direct basis (different conditioning variables; no OI-stock/capacity normalization), retained as context that perp positioning fields are active research inputs. |
| L5 | (follow-up fetch) Ledger 325 full text | 11:17 | ledgerjournal.org PDF | REJECT (retrieval failure — abstract/body not retrievable); cited on title/venue only with that caveat recorded. |

Primary-source claims carried into the design: (i) volume conflates open/close trades, so
turnover per unit of open stock measures position recycling intensity, not direction (L1);
(ii) forced liquidations are a first-order, asymmetric flow on leveraged crypto venues (L3);
(iii) displayed depth is least trustworthy precisely when crowded books unwind (L3).

Transfer caveats (equity/commodity -> Binance USD-M perps):
- Hedging-pressure premia are net-position stories with COT data; our signal is GROSS and
  side-agnostic. If aggregate net positioning flips (short-crowded regimes), the long-side
  cascade asymmetry weakens — this is a declared mechanism risk, not a hidden assumption.
- OI is observed as daily snapshots: intraday crowding spikes are invisible; snapshot stamp
  jitter handled by the frozen hour-snapping loaders; a missing snapshot refuses the stamp.
- Dollar turnover approximated by 15m LAST-price close x base volume; intra-bar price drift and
  taker/maker conflation are accepted noise, identical across arms.
- The cascade premium, if any, is a TAIL phenomenon; a weekly equal-tercile tilt harvests it
  only as a cross-sectional mean shift. A tail event inside one fold can dominate a fold sign —
  that is what the fold-concentration gate (largest fold-positive share <= 50%) is for.

## 4. PIT observable (fusion-record availability semantics)

Decision instant T = Monday 00:00:00Z. A decision at T reads ONLY rows with
`available_time_utc <= T`; retrieval time never substitutes for availability
(research/data_fusion/crypto_compat.py; research/data_fusion/pit.py vintage selection).

- Open interest: dataset `crypto_open_interest`, field `open_interest`; available at the OI
  snapshot stamp. At T use the LATEST snapshot with `available_time_utc <= T` and stamp within
  the trailing 48h; otherwise the symbol is refused at that stamp (fail-closed).
- Mark price: dataset `crypto_mark_price`; available at the mark snapshot stamp (kline close).
  Pairing rule (declared): OI snapshot at stamp s is paired with the LATEST mark record with
  `available_time_utc <= s`; if none within 24h of s, the symbol is refused at that stamp.
  OI_notional_i(T) = OI_i(s) x mark_i(s).
- Turnover: dataset `crypto_bars`, 15m completed bars, available at bar close; daily dollar
  turnover_i(d) = sum over the day's completed bars of (close x volume). Days with any missing
  15m slot inside the formation window are excluded and the exclusion count reported; a
  formation window with more than 10% missing days refuses the stamp (fail-closed).
- Funding: dataset `crypto_funding`, used ONLY as a native cost on held positions. Funding rate
  never enters any signal, ranking or gate.

## 5. Universe, warmup, clock, holding, execution

- Universe: the 20 staged REQUIRED_SYMBOLS minus BTCUSDT (benchmark only) = 19 tradable names.
  Eligibility at T: warmup coverage complete; OI + mark pairing resolvable; formation windows
  clean (fail-closed refusal per symbol per stamp, refusal counts reported).
- Warmup: binding maximum 90 days (BTC-beta context, frozen daily convention); anchor formation
  28d; neighbour formation 56d — all from the frozen warmup table (28/56/90).
- Decision clock: weekly, every Monday 00:00:00Z (52 discretionary decisions/365d <= 60 floor).
- Holding: intended 7 days (median holding 7d >= 3d floor); force-flat at fold boundaries.
- Execution lag (ONE, declared): fills at the close of the first completed 15m bar strictly
  after T (Monday 00:15:00Z bar close), at that bar's close, generic adapter costs applied on
  fills; native funding settlements paid on held legs as cost only.
- Book: long bottom tercile (lowest unwind-days), short top tercile (highest unwind-days),
  6 symbols per side, equal weight 1/12 per held symbol, gross 1.0; max |weight| = 1/12 <= 0.30
  by construction; ties broken by symbol id ascending (declared a priori); middle tercile flat.
- Folds: frozen V12 chronological F0/F1/F2 over the blind-S0 window 2025-08-22..2026-08-21 with
  1-day purge, imported unchanged (not restated here to avoid drift).

## 6. Arms (exactly 3): anchor + neighbour + causal negative control

- ANCHOR — `EXITCAP-28D`: U_i(T) = OI_notional_i(T) / mean daily dollar turnover over trailing
  28d; long bottom tercile / short top tercile as in section 5.
- NEIGHBOUR — `EXITCAP-56D`: same mechanism and book, denominator window 56d. Justification:
  capacity should be measured over a full quarter to smooth regime bursts; 56d is in the frozen
  warmup table and is the pre-declared sibling of the 28d anchor (matches the V12 frozen 28/56
  pairing convention). Supports the mechanism iff same sign and same tercile book.
- CAUSAL NEGATIVE CONTROL — `EXITCAP-STATIC-SCALE`: identical book construction, but the
  denominator is replaced by each symbol's median daily dollar turnover over the 90-day
  pre-window [screen_start - 90d, screen_start), FROZEN for the whole run (a per-symbol
  constant). The control carries zero capacity dynamics after freeze; its cross-sectional
  ranking is driven by raw OI-notional scale up to a static scale factor.
- Preregistered control rule: the control MUST NOT reproduce the anchor — if
  `EXITCAP-STATIC-SCALE` is positive in >= 2/3 folds on the same BTC-beta-context excess gate,
  the anchor's edge is attributed to persistent raw positioning scale rather than to
  capacity-relative crowding, the anchor FAILS the mechanism-attribution gate and the family is
  rejected. The control is never promotable to a family regardless of its own result.
- Beta/funding separation (all arms): identical universe, identical fills and identical native
  funding costs; funding is a cost, never a signal; the incremental gate is BTC-beta-adjusted.
  Any anchor-minus-control difference therefore reflects capacity information, not funding carry
  or beta.

## 7. Incremental test vs buy-and-hold and BTC-beta context

- Benchmark: BTCUSDT buy-and-hold over the same stamps (same clock, same fold boundaries).
- Beta context: weekly arm excess regressed against BTC weekly excess; beta from trailing 90d of
  completed daily bars (frozen convention).
- Binding gate (Stage-A, unrelaxed): BTC-beta-context excess positive in >= 2/3 folds for the
  anchor; raw excess vs buy-and-hold reported alongside and must also be positive in >= 2/3
  folds for the family to advance. Neighbour must show the same sign; control must fail per
  section 6.

## 8. Costs, floors, concentration, drop-one

- Costs: frozen generic adapter fee/slippage schedule (base) and stress = fee x1.5, +2 adverse
  ticks, +1 event delay (fill shifts to the next 15m bar close). Native funding on held legs,
  counted once, cost only. Feasibility (cost drag <= 8%/yr of gross base, <= 12%/yr stressed) is
  evaluated by A9-F from schedule artifacts only — no cost number is computed in this proposal.
- Floors: <= 60 discretionary decisions/365d (52 weekly); median intended holding 7d >= 3d;
  >= 52 weekly decisions per arm in the screen window; >= 15 decisions per fold; zero-position
  arms refused at publication (inherited minimum-activity rule).
- Concentration: no symbol > 25% of turnover (equal tercile book; checked by A9-F); largest
  symbol positive-PnL share <= 0.70 gate inherited; max |weight| <= 0.30 at every stamp by
  construction (1/12).
- Drop-one design (non-vacuous): identify the fold-stamp with the largest held |weight|; drop
  the single symbol attaining that maximum among held positions (by construction it is a held
  max-|weight| symbol); renormalize the remaining side to 5 symbols per side (1/10) and re-run
  the arm. The family survives only if the anchor's fold-sign pattern and the control rule's
  outcome are unchanged; otherwise the edge is symbol-specific and the family is rejected.

## 9. Failure interpretation

- Anchor fails incremental gate in all folds: no after-cost edge; the cascade-vulnerability
  premium is absent or already priced at weekly horizon; family rejected (no parameter search).
- Anchor positive but control also positive: edge is raw positioning scale, not exit-capacity
  normalization; mechanism attribution fails; family rejected.
- Anchor positive, neighbour negative or sign-flipped: formation-window fragility; mechanism not
  stable across the pre-declared sibling parameter; family rejected.
- Anchor fails only under stress: the effect is a microstructure execution artifact (spread/
  slippage-dominated), not positioning structure; family rejected.
- Fold-concentration failure (one fold carries > 50% of positives): regime-dependent cascade
  window, not a persistent mechanism; family rejected.
- Symbol-concentration failure (largest symbol > 0.70 of positive PnL): single-name artifact;
  family rejected.
- Refusal rate (fail-closed) too high (OI/mark pairing unresolved for a majority of stamps):
  BLOCKED_DATA verdict, not a rejection of the mechanism.

## 10. Source-to-test map

| Input field (dataset) | Exact test use |
|---|---|
| OI snapshot `sumOpenInterest` (`crypto_open_interest`, avail = snapshot stamp) | numerator of unwind-days; latest avail <= T, paired at own stamp; refused if stale > 48h |
| Mark price (`crypto_mark_price`, avail = snapshot/kline-close stamp) | convert OI to notional at the OI snapshot stamp (pairing rule, section 4) |
| 15m bar close x volume (`crypto_bars`, avail = bar close) | daily dollar turnover; 28d (anchor) / 56d (neighbour) / frozen-90d-median (control) denominators; turnover-share concentration check |
| Funding settlements (`crypto_funding`, avail = settlement stamp) | native cost on held legs in ALL arms identically; never in signals or gates |
| BTCUSDT 15m bars | weekly buy-and-hold benchmark; 90d beta context |
| Instrument tick size (`crypto_perpetual` metadata) | +2-tick stress slippage unit |
| Completed-bar coverage / gaps | warmup satisfiability (90d binding), formation-window refusal, fold boundaries |

## 11. Ancestry map vs the forbidden inventory

- V12-OILEV-V2 (OI-deleveraging): the forbidden family signals on the TIME-DIFFERENCE of OI
  (deleveraging flow). EXITCAP contains no OI differencing anywhere; the conditioning variable
  is the OI STOCK normalized by realized turnover capacity, and the sign is derived from
  cascade-vulnerability asymmetry, not from inverting or retuning the OILEV-V2 anchor. No sign
  flip, no horizon tweak, no cap raise, no universe carve-out, no renaming of that identity is
  involved. If A1/A7-N nonetheless classify positioning-crowding as shadow-region, section 12
  applies in full, including the binding A7-N |rho| <= 0.20 eligibility check against the frozen
  OILEV-V2 anchor AND its inverted control.
- V6/V1-CARRY-FUNDING: funding appears only as a native cost on held legs, identical across all
  three arms; no funding-derived signal, premium or ranking exists.
- V11-ILLIQ-AMIHUD / V12-ILLIQ-REPLICATION: no |return|/volume price-impact term; turnover here
  is normalized by OPEN STOCK (positioning), not by price impact; no replication of the frozen
  ILLIQ brief is attempted.
- V4-XSECT-MOM, V8R-XSECT-REVERSAL, V9-TS-TREND, WEEKLY-REVERSAL: no return term enters any
  signal; ranking uses OI-notional and turnover only.
- V1-VOLCOMP / V9 dollar-volume shock continuation: no shock level, threshold or breakout; no
  continuation claim; volume enters only as a capacity denominator.
- V11-LOTTERY-MAX-SKEW: no return-distribution moments (no MAX/LOT/skew).
- V10-M01-AGGRESSOR-ABSORPTION: no aggressor/order-flow data; 15m LAST bars only.
- V12-BAB-LOWBETA: no beta-sorted book; beta enters only as the context adjustment, identical
  across arms.

## 12. Shadow-region determination and front-door disclosures (voluntary, pre-staged)

Determination: the mechanism is an EXIT-CAPACITY RISK story (gross leverage crowding vs realized
risk-transfer capacity), not a liquidity-provision premium or a crowding-premium rescue, and its
signal shares no variable with the observed shadow signs. The proposal therefore declares itself
OUTSIDE the shadow region. In the alternative — if A1/A7-N classify any positioning-crowding
conditioning as inside the shadow region — the front door is pre-staged and accepted:
1. Mechanism stated in its own words above (sections 1-2), never as "the inverted anchor".
2. Disclosure: the sign was already observed in V12/V11 control arms — inverted OI-flow +0.758
   raw (V12 OILEV-V2-28D-FLOW-W-INV causal control), V11 LOT inversion (net +0.71, PF 1.34),
   stocks-program vol-level sorting control outperforming its anchor. These are measured
   control-arm observations, not tradable findings and not rescuable descendants. If
   shadow-classified, this family is preregistered CONFIRMATORY and its confirmatory status is
   recorded in the verdict and denominator.
3. Own causal negative control (section 6) separating the mechanism from the rejected ancestor
   (static-scale placebo carries no capacity dynamics and no OI differencing) and from beta/
   funding carry (identical costs/funding across arms; BTC-beta-adjusted gate).
4. The binding A7-N rank-correlation check |rho| <= 0.20 against the frozen OILEV-V2 anchor AND
   its inverted control on the common window is accepted as an eligibility condition;
   failure renders this proposal INELIGIBLE.
5. Stage-A gates apply with no relaxation.

## 13. Outcome-blind attestation

```
OUTCOME-BLIND ATTESTATION
lane: a5  proposal: A13-V13-A5-EXITCAP
I wrote this mechanism and its falsification conditions before computing any
return, metric or ranking, and without access to any scored artifact or
outcome file.
utc: 2026-09-04T11:19:42Z  agent: a5
```
