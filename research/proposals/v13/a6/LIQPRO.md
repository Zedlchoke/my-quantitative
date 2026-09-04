# A13-V13-A6-LIQPRO — Episodic-Depth (Turnover-Burst Concentration) Premium

lane: a6 (outcome-blind proposal, Phase D1) — cycle CRYPTO-V13
schema: v13_proposal_v1 — sibling JSON: `LIQPRO.json` (same content, structured)

---

## 1. Hypothesis ID + mechanism

**Hypothesis ID: `A13-V13-A6-LIQPRO`**

Mechanism (own words): on Binance USD-M perpetuals, the **shape** of turnover
within a week — how concentrated trading is into a few 15-minute bursts versus
spread smoothly across the 2,688 slots — measures the RHYTHM at which liquidity
is provided. When a name's weekly turnover is concentrated into few bursts,
displayed depth exists only episodically: quotes are pulled between bursts,
market-maker inventory risk per unit of standing time spikes, and a position
holder's exit liquidity depends on the next burst arriving on schedule. A
holder of such a name is the residual supplier of continuity between bursts and
bears a recurring episodic-liquidity risk that must be compensated by a higher
expected return — the same channel through which Nagel (2012) prices liquidity
provision and through which the crypto liquidity-provision premium (JBF 2025)
manifests. When turnover is smooth, market makers can rotate inventory against
a steady tape; continuity is cheap and the episodic-depth premium is small.
Economic counterparty: episodic takers (burst-initiated flow) versus liquidity
providers and the between-burst holder who supplies continuity. Why the edge
can exist: liquidity-provision risk is priced (Nagel 2012; JBF 2025 in crypto
specifically; positioning-structure premia in futures, Bessembinder 1992), and
burst concentration is a persistent 28d-scale structural property of a name's
flow, not news. Expected sign: **the 5 symbols with the HIGHEST 28d normalized
turnover-burst concentration outperform the cross-section mean and BTC
buy-and-hold after costs** — holders of episodically-liquid names earn the
continuity premium. Funding never appears in the signal; it is a holding cost
only. The signal contains no return, no price-difference and no OI term: price
enters only as a same-bar deflator of volume (dollar volume), available at the
bar close stamp.

## 2. Falsifiable prediction

The anchor arm (LIQPRO-28D) must, after BASE costs: (a) earn positive
buy-and-hold-BTC-matched excess in >= 2/3 chronological folds; (b) earn
positive BTC-beta-context (beta-adjusted) excess in >= 2/3 folds; (c) pass all
frozen Stage-A gates; (d) be supported by the neighbour (LIQPRO-56D: same sign,
same excess gates); and (e) NOT be reproduced by the causal control
(VOLREG-28D) under the preregistered rule of section 6.

**FALSIFIED if any of:** excess <= 0 in >= 2 folds on either gate; the
vol-level control reproduces the anchor (rule in section 6); the 56d neighbour
fails to show the same-sign positive excess; any Stage-A gate fails; the
drop-one perturbation is vacuous or flips the family verdict. Any single
falsifier rejects the family. No window retune, sign flip, per-symbol cost
exemption or universe carve-out may be attempted afterwards — such a rescue is
itself forbidden (inventory rule).

## 3. Literature (queries + retrieval UTC logged; pass completed BEFORE any candidate return would have been computed — none was)

Same retrieval session as sibling CAPVEL (logged once, cited per use):

| # | Query | Retrieval UTC | Verdict + reason |
|---|-------|---------------|------------------|
| L1 | "open interest to volume ratio cryptocurrency perpetual futures return predictability" | 2026-09-04T11:10:27Z | ACCEPT: Giagkiozis & Said (Ledger / arXiv 2310.14973) — OI misquotation caveat. For LIQPRO this is a SECONDARY caveat: the LIQPRO signal uses bars only, so the caveat applies to the crowding *language*, not the signal. REJECT: practitioner pages. |
| L3 | "trading volume concentration Herfindahl index stock returns informed trading liquidity" | 2026-09-04T11:15:12Z | ACCEPT (primary method provenance): MDPI JRFM 17(8):325 — HHI/Gini are the standard volume-concentration statistics; IJEFR 2021 — Gini volume-concentration events followed by abnormal returns in equities, supporting that concentration structure carries return information. REJECT for direct transfer: equities (auction structure, no 24/7), event-study design, direction-of-effect ambiguity across their specifications. |
| L4 | "market maker inventory risk premium liquidity provision returns asset pricing" | 2026-09-04T11:17:00Z | ACCEPT (primary channel, crypto-specific): "Returns from liquidity provision in cryptocurrency markets" (JBF 2025, S0378426625000317) — the liquidity-provision premium exists in crypto markets. CRITICAL caveat: measured via short-reversal returns; LIQPRO's signal is return-free, so LIQPRO tests whether the premium is harvestable through a STRUCTURAL (turnover-shape) conditioning instead of a return-reversal conditioning. |
| L5 | "hedging pressure risk premium futures markets open interest theory Bessembinder" | 2026-09-04T11:17:21Z | ACCEPT (theory frame): Bessembinder 1992 RFS; De Roon–Nijman–Veld 2000 JF; Basu & Miffre 2013 JBF — futures risk premia carry positioning/structure components beyond beta. REJECT for direct operationalization: no trader classification in the authorized data; LIQPRO uses only the observable turnover shape. |
| L6 | "bitcoin perpetual futures liquidation cascade open interest deleveraging empirical study" | 2026-09-04T11:19:05Z | ACCEPT (context): arXiv 2608.03616; Oct 2025 cascade anatomy — episodic liquidity evaporation is a first-order perp phenomenon, motivating the episodic-depth risk story. REJECT as mechanism template: those designs condition on OI flow; LIQPRO uses no OI at all. |
| L7 | "Nagel evaporating liquidity short-term reversal returns market maker compensation" | 2026-09-04T11:20:10Z | ACCEPT (primary channel, top-tier): Nagel 2012 RFS 25(7) 2005–2039 — returns from liquidity provision are priced and rise when funding liquidity contracts. Caveat: return-based measurement (reversal profits); LIQPRO's conditioning is structural, not return-based. |

**Transfer caveats (binding for interpretation):** (1) equities-to-perp
transfer: 24/7 trading removes session boundaries that generate equity volume
concentration; burst structure here is flow-intrinsic, and concentration
LEVELS are not comparable across settings. (2) The direction-of-effect in the
equity concentration literature is mixed across specifications (L3): the
risk-premium sign predicted here is a hypothesis the folds must decide, not a
replication. (3) The crypto liquidity-provision premium (L4, L7) is
reversal-operationalized: LIQPRO's structural signal could fail even if the
channel exists — that outcome means the premium is not harvestable without
return conditioning, NOT that the channel is absent. (4) Bursty names may carry
wider effective spreads; the frozen generic cost schedule applies uniformly —
no per-symbol fee carve-out is permitted (a carve-out would be a forbidden
cost-exemption rescue). (5) No published cross-sectional study of turnover-burst
concentration on Binance USD-M was found: high prior uncertainty; the
falsification gates decide.

## 4. PIT observable (fusion-record availability semantics)

Decision stamps are Monday 00:00:00Z. A decision at T reads ONLY records with
`available_time_utc <= T` (retrieval time never substitutes for availability;
as-of selection via the frozen fusion `VintageSeries.select` rank
`available_time_utc <= vintage_time_utc <= retrieved_time_utc`):

- `crypto_bars` fields `volume`, `close` (15m): available at the bar close
  boundary (`ts_event`). Per-slot dollar volume `v_i * c_i` uses the SAME
  bar's close as deflator, so each slot's dollar volume is available exactly at
  that bar's close. Signal input (shape of turnover), fill marks, benchmark and
  beta-context series.
- `crypto_mark_price` field `mark_price`: available at the mark snapshot stamp;
  cost marks only, never a signal input.
- `crypto_funding` field `funding_rate`: available at the settlement stamp
  (`fundingTime`); applied to a holding span only when the settlement lies in
  `[ts_opened, ts_closed]`; COST ONLY.
- `crypto_open_interest`: NOT used by any LIQPRO arm (by design — maximal
  structural distance from the forbidden OI families; the positioning/
  liquidity conditioning branch satisfied here is liquidity-provision pressure
  and depth/turnover structure).
- Instrument tick sizes (metadata): slippage floor for the stress schedule.

Signal definition (anchor): over the trailing 28d window of 15m slots,
`p_i = v_i*c_i / Σ_j v_j*c_j`; `HHI_norm = n_slots × Σ_i p_i²` (1 = perfectly
uniform across the window's slots; n_slots = all turnover in one slot).
Scale-free, sign-free, LEVEL-of-shape statistic; no return, no OI, no funding
term enters the ranking.

## 5. Universe, warmup, decision clock, holding, fills

Identical skeleton to sibling CAPVEL, restated in full:

- **Universe**: the 20 frozen required symbols MINUS BTCUSDT (benchmark/context
  only) = 19 tradable USD-M perpetuals. Per-stamp eligibility: complete
  trailing 28d (anchor) / 56d (neighbour) of completed 15m bars; ineligible
  symbols excluded that stamp; book renormalizes across eligible names at equal
  weight 1/N (N = eligible count); N >= 4 satisfies |w| <= 0.30 by construction
  (1/4 = 0.25); N < 4 scales gross down to keep |w| <= 0.30 at every stamp.
- **Warmup**: binding 90d (BTC-beta context) per the frozen warmup table
  (`anchor_28d`, `neighbour_56d`, `beta_90d`); satisfied from authorized
  pre-screen history 2024-08-20..2025-08-22 before the blind-S0 window.
- **Decision clock**: every Monday 00:00:00Z (weekly-or-slower; 52/365d <= the
  frozen 60 discretionary-decisions floor). Book carried between stamps;
  forced-flat only at fold boundaries.
- **Folds**: F0/F1/F2 chronological over the blind-S0 window
  2025-08-22..2026-08-21 with the frozen 1-day purge.
- **One declared execution lag**: fill at the close of the first completed 15m
  bar with close time STRICTLY AFTER the decision stamp = Monday 00:15:00Z.
  Stressed schedule adds +1 event delay -> Monday 00:30:00Z.
- **Holding**: 7d intended; full target-book rebalance at each stamp only.

## 6. Arms — anchor + neighbour + causal negative control (exactly 3)

| Arm | Construction | Role |
|-----|--------------|------|
| **LIQPRO-28D** (anchor) | Rank 19 eligible symbols DESCENDING on `HHI_norm` over the trailing 28d; long the 5 HIGHEST at 0.20 each, gross 1.0. | The mechanism (episodic-depth premium). |
| **LIQPRO-56D** (neighbour) | Same mechanism, formation window 56d. | Justified parameter: episodic-provision regimes persist at quarterly scale; 56d averages over more weekly cycles; stays inside the frozen warmup table (`neighbour_56d`). |
| **VOLREG-28D** (causal negative control) | IDENTICAL pipeline; ranking instead on trailing 28d realized volatility of daily log returns (from authorized 15m bars, PIT stamps) DESCENDING; long the 5 HIGHEST-vol names. | Closest rival explanation: "bursty names outperform simply because they are high-volatility names" (vol-level sorting — a measured shadow-observation-adjacent rival, deliberately placed in the CONTROL seat, never proposed as the mechanism). |

**Preregistered control rule (the control MUST NOT reproduce the anchor):**
control reproduction is defined as: the VOLREG-28D arm passes after-cost
expectancy > 0 AND its per-fold buy-and-hold-excess SIGNS match the anchor's
in >= 2/3 folds. If reproduction occurs, the causal attribution FAILS: any
residual anchor edge belongs to the vol-level rival effect, not to the
episodic-depth structure, and **LIQPRO is INELIGIBLE for selection even if the
anchor itself passes every Stage-A gate.** (The control arm tests a rival; it
is not part of the proposed mechanism and can never be promoted from this
proposal.)

## 7. Incremental test vs buy-and-hold and BTC-beta context

- **Buy-and-hold benchmark**: BTCUSDT buy-and-hold at matched gross from the
  same authorized bars under the same fusion availability stamps, per-fold
  weekly excess.
- **BTC-beta context**: trailing 90d daily beta of the arm vs BTC (frozen
  `beta_90d` warmup, PIT stamps); beta-adjusted excess per fold.
- **Gate (frozen)**: BOTH excess measures positive in >= 2/3 folds. Raw pass
  with beta-context failure = beta in disguise -> REJECT.

## 8. Costs, floors, concentration, drop-one

- **Base costs**: generic adapter fee + slippage on fills only; native funding
  settlements while held enter exactly once as a COST. **Stress**: fee x1.5,
  +2 adverse ticks, +1 event delay.
- **Floors (frozen)**: <= 60 discretionary decisions/365d (52 scheduled);
  median intended holding >= 3d (7d); base cost drag <= 8%/yr of gross;
  stressed <= 12%; no symbol > 25% of one-way turnover; |w| <= 0.30 at every
  stamp by construction; gross <= 1.0.
- **Concentration**: largest-symbol positive-PnL share <= 0.70 enforced as the
  frozen Stage-A gate; equal-weight quintile construction bounds per-swap
  notional at 0.20 of gross. Bursty names may carry wider effective spreads in
  reality; the frozen generic schedule is applied uniformly — any per-symbol
  cost exemption is a forbidden rescue pattern and is not sought.
- **Sample floors**: 52 scheduled stamps/yr; frozen minimum-activity convention
  (zero-position baseline refused at publication); a stamp with fewer than 4
  eligible symbols carries the book unchanged and is still counted.
- **Drop-one design (frozen)**: at each decision stamp the perturbed schedule
  drops the single HELD symbol with MAXIMUM |weight| for that holding span;
  flat book = VACUOUS; gates require non-vacuous drop-one symbol survival AND
  fold survival (dropping any single fold must not flip the family verdict).

## 9. Failure interpretation

| Failure mode | Meaning | Action |
|---|---|---|
| Cost floor breached (base or stress) | Continuity premium not harvestable at frozen costs on bursty names | REJECT cost-infeasible; no fee exemption (exemption = forbidden rescue). |
| Anchor excess <= 0 in >= 2 folds | Episodic-depth sign wrong on this window (consistent with the mixed equity-concentration evidence, L3) | REJECT; sign flip forbidden. |
| VOLREG-28D reproduces the anchor | Attribution failure: edge is vol-level sorting, not episodic depth | REJECT LIQPRO as ineligible. |
| Neighbour fails while anchor passes | Parameter fragility; mechanism unsupported | REJECT family; neighbour never promoted alone. |
| Beta-context fails while raw passes | BTC beta in disguise | REJECT — no incremental information (mission Q2 unmet). |
| Drop-one vacuous or verdict flips | Not robust to held-book composition | REJECT. |
| Persistent bar-coverage gaps force eligibility < 4 | Data problem, not economics | Report as BLOCKED_DATA candidate; no redesign inside this cycle. |

## 10. Source-to-test map (every input field -> exact test use)

| Field (dataset) | Test use |
|---|---|
| `bars.volume` + `bars.close` (`crypto_bars`, 15m) | Per-slot dollar volume for the anchor/neighbour `HHI_norm` ranking; daily log returns ONLY inside the VOLREG control's realized-vol ranking; benchmark and beta-context series; fill marks. |
| `mark_price` (`crypto_mark_price`) | Cost/valuation marks only. |
| `funding_rate` (`crypto_funding`) | Holding cost only, `[ts_opened, ts_closed]`. |
| tick sizes (instrument metadata) | Stress-slippage floor (+2 ticks). |
| `open_interest` (`crypto_open_interest`) | NOT USED by any LIQPRO arm (declared: zero OI dependence, structural distance from OI families). |
| BTCUSDT bars | Buy-and-hold benchmark + 90d beta context only; never tradable in the book. |

## 11. Ancestry map vs the forbidden inventory (why this is NOT a variant, inversion, rescue or renaming)

- **V12-OILEV-V2 / V11-OILEVER-DELEV**: LIQPRO uses NO open-interest data in
  any arm — no OI level, flow, change or ratio; the mechanism cannot be an OI
  sign flip, horizon tweak, carve-out or renaming by construction.
  **Self-preregistered novelty condition (declared outcome-blind): if A7-N
  measures rank correlation |rho| > 0.20 between the LIQPRO weekly signal and
  the frozen OILEV-V2 anchor signal OR its inverted control on the common
  window, LIQPRO is INELIGIBLE.**
- **V6/V1-CARRY-FUNDING**: funding never enters the signal (cost only); no
  carry or crowding-premium-from-funding story.
- **V1-VOLCOMP (incl. V9 dollar-volume shock continuation)**: no
  volatility-compression or breakout-direction premise and no volume-spike
  EVENT conditioning; the signal is a 28d SHAPE statistic (distribution of
  turnover across slots) ranked cross-sectionally, with no continuation claim
  and no price-difference term. Dollar volume uses price only as a same-bar
  level deflator — never differenced, never signed.
- **V9-TS-TREND / V4-XSECT-MOM / V8R-XSECT-REVERSAL / WEEKLY-REVERSAL**: no
  past-return term of any horizon in the anchor or neighbour signal.
- **V11-LOTTERY-MAX-SKEW**: no return-distribution moment in the signal
  (realized vol appears ONLY in the control arm, where it operationalizes the
  rival explanation the mechanism must defeat).
- **V12-BAB-LOWBETA**: no beta-sorted construction; beta appears only in the
  frozen context gate. The vol-sort sits in the CONTROL seat with a
  preregistered must-not-reproduce rule; if it reproduces the anchor the
  proposal is rejected, so LIQPRO cannot profit from a vol/beta effect.
- **V11-ILLIQ-AMIHUD**: Amihud = |return| / dollar-volume; LIQPRO's signal has
  no return term and no ratio of impact to depth — it ranks the time-shape of
  turnover, not price impact.
- **V10-M01-AGGRESSOR-ABSORPTION**: no aggressor/imbalance flow (unavailable
  and unused).
- **V12-ILLIQ-REPLICATION**: not the frozen replication brief; no window
  substitution.
- **DATA-GATED**: only authorized datasets + instrument metadata; no new
  source, key, signup or download.
- **Shadow region: NOT entered.** The predicted sign (long high burst
  concentration) is none of the measured shadow observations (inverted OI-flow
  +0.758, V11 LOT inversion, vol-level sorting control); the mechanism is
  stated in its own words and is preregistered EXPLORATORY (not confirmatory).
  The vol-level rival is deliberately placed in the causal control seat with a
  must-not-reproduce rule — the opposite of promoting the shadow observation.

## 12. Section 1.1 front-door disclosures

Not applicable — this proposal does NOT enter the shadow-effect region. The
section 1.1 disclosure requirement is answered explicitly: no part of LIQPRO's
sign claim derives from, or is justified by, a V12/V11 control-arm observation;
the vol-level sorting observation is instead used ONLY as the causal control's
rival hypothesis, with a preregistered rule under which its reproduction kills
the proposal; the family is preregistered exploratory.

## 13. Outcome-blind attestation

See the signed attestation block at the end of this file.

---

```
OUTCOME-BLIND ATTESTATION
lane: a6  proposal: A13-V13-A6-LIQPRO
I wrote this mechanism and its falsification conditions before computing any
return, metric or ranking, and without access to any scored artifact or
outcome file.
utc: 2026-09-04T11:17:21Z  agent: A6
```
