# COST_CONTRACT_6E_6B — modeled cost ladder S1/S2/S3 × ×1.0/×1.5/×2.0, per symbol, + the dead-spot 3.0 bp ancestry fence

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **FXEB**, 2026-10-05. PREP-only;
  no cost number is recomputed against any account; nothing here is executable.
- **CONDITIONAL-ON-PB2-LIFT DRAFT — PB2 HOLD (6E/6B) stands.**
- Binding labels on EVERY number below: **MODELED COST · UNDER REVIEW ·
  `VERIFIED_VS_ACCOUNT=NOT_RUN`** (until a clean fee A7 against the account + the
  reg-basis owner ruling). The words "measured cost"/"complete cost" are FORBIDDEN on
  any output (A7 §7 language law). The stale glued-value class (e.g. ES 21.006) is
  NEVER consumable on FX either — the dual-variant erratum law
  (`COST_FREEZE_ERRATUM.md`, sha256 `cf83bc2d…09ae8`) supersedes by reference.
- Per-symbol law: 6E and 6B carry separate ladders; no cell shared silently.

## 1. Fee law (fee-only layer, per side, USD)

Source: `FEES_CORRECTED.md` (sha256 `006d6372…5d1bef`) + `A7_FEE_REAUDIT.md` §2 cell 4 /
§3 step-3 (sha256 `2c1095d6…211ad`) — the only lawful fee numbers:

| component | value/side | class |
|---|---|---|
| Commission (IBKR Fixed / tier-1) | 0.85 | LITERAL (ladder 0.85/0.65/0.45/0.25, deltas −0.20) |
| Exchange, CME **Forex Futures** group | 1.60 | LITERAL cell (archive_CME.php.html L1668, RAW); label aliases incl. EUR/GBP/JPY/AUD/6H — **6E/6B never printed verbatim ⇒ mapping PARTIAL** (owner slot e.1) |
| Regulatory — Variant B (IBKR-offset epoch) | 0.01 | composition actually printed in the corrected FX tier |
| Regulatory — Variant A (NFA basis) | 0.02 | **DERIVED for FX: not in any A7 dual-variant table (A7 §8 tabulates ES/NQ only) ⇒ FX Variant-A all-ins below are DERIVED and require the owner reg-basis ruling (P5-OD7)** |

**FX tier table (corrected, A7-verified arithmetic)**: T1 **2.46** / T2 **2.26** /
T3 **2.06** / T4 **1.86** USD/side (B-composition 0.85+1.60+0.01). Variant-A composition
= 0.85+1.60+0.02 = **2.47 / 2.27 / 2.07 / 1.87** [DERIVED]. Delta A−B = +$0.01/side =
+$0.02/RT — same shape as the ES/NQ dual variant.

## 2. Spread proxy + slippage assumptions and their evidence

- **Spread proxy: $18.75/side = 3 ticks × $6.25 close-proxy, HIGH-BIASED** (DC §1.7;
  court §b4 table: 6E 1.21–1.57 bp/side, 6B 2.11–2.89 bp/side across measured price
  ranges). **BBO NOT_RUN (D5 law — not purchased; single-level BBOMsg could not prove
  fill/queue anyway).** Hazard declared: the proxy is measured on full-session closes —
  it is *most* biased-low exactly where FX-F4 trades (17:00 CT reopen thin window,
  p05 session volume 7,904 contracts; `FX_HYPOTHESES.md` §4.8) and on spike minutes
  (F2/F3 fills inside decaying volume spikes; tier-3 plausibly understates reality).
- **Slippage tiers S1/S2/S3 = {1, 2, 3} ticks/side × $6.25** = 6.25 / 12.50 / 18.75
  USD/side — research assumption (D1-class), never a measurement.
- Fill law (conservative): entry = open of next 1m bar; no limit/queue claims;
  same-bar TP/SL ⇒ SL-priority; event-window law ≥1 minute post-release.

## 3. Modeled cost ladder (per symbol; USD; RT = 2 sides)

Formula [DERIVED, worked example]: `RT(tier) = 2 × (fee_all_in + 18.75 + slippage_tier)`.
6E S2 example: 2 × (2.46 + 18.75 + 12.50) = **67.42 USD RT**.

### 3.1 6E — Euro FX (EUR 125,000; px range 0.9552–1.2429 ⇒ notional $119,400–155,363 [MEASURED range, FX_HYPOTHESES §7])

| tier | all-in/side (USD) | RT ×1.0 (USD) | RT ×1.5 | RT ×2.0 | RT bp @ notional 119,400 | RT bp @ notional 155,363 |
|---|---|---|---|---|---|---|
| S1 | 27.46 | 54.92 | 82.38 | 109.84 | 4.60 | 3.53 |
| S2 | 33.71 | 67.42 | 101.13 | 134.84 | 5.65 | 4.34 |
| S3 | 39.96 | 79.92 | 119.88 | 159.84 | 6.69 | 5.14 |

Headline band (recorded law, `FX_HYPOTHESES.md` §7): **6E modeled RT 3.6–6.3 bp**
(spread 2.41–3.14 + fees 0.32–0.41 + slippage 0.91/1.82/2.73 bp). Variant-A fee shift:
+$0.02 RT ≈ +0.013–0.017 bp — disclosed, immaterial vs tier spread but owner-ruled.

### 3.2 6B — British Pound FX (GBP 62,500; px range 1.0392–1.4205 ⇒ notional $64,950–88,781; slippage bp quoted at reference px 1.30 ⇒ notional 81,250, per the family cost table)

| tier | all-in/side (USD) | RT ×1.0 (USD) | RT ×1.5 | RT ×2.0 | RT bp @ notional 64,950 | RT bp @ notional 88,781 | slippage share bp @ 81,250 |
|---|---|---|---|---|---|---|---|
| S1 | 27.46 | 54.92 | 82.38 | 109.84 | 8.45 | 6.19 | 1.54 |
| S2 | 33.71 | 67.42 | 101.13 | 134.84 | 10.38 | 7.59 | 3.08 |
| S3 | 39.96 | 79.92 | 119.88 | 159.84 | 12.30 | 9.00 | 4.62 |

Headline band (recorded law): **6B modeled RT 6.3–11.2 bp** (spread 4.22–5.77 + fees
0.55–0.76 + slippage 1.54/3.08/4.62 bp). 6B USD RT equals 6E's only because both tick
values are $6.25 — in bp-of-notional 6B is ~1.8× more expensive per RT.

Stress-ladder law (six-adopt CYCLE_LAUNCH_DRAFT §3, binding post-lift): ×1.0 is the
GATE number; ×1.5/×2.0 are disclosed robustness views; a survivor that dies at ×1.5 is
disclosed as such, never hidden.

## 4. The dead-FX-spot 3.0 bp ancestry fence (PB2)

[FACT, PB2_ANCESTRY_COURT_DRAFT §a/§b4 (sha256 `e358e2ce…de57f`): the dead spot families
(FOREX-FREE-V1/V2, 12 cells, 0 survivors, all EXPECTANCY_NONPOSITIVE) ran on a frozen
proxy of **1.5 bp/side → 3.0 bp RT base**, stress {4.5, 6.0} bp; no bid/ask, forced flat
pre-rollover.]

| vehicle | modeled RT | multiple of the dead 3.0 bp floor |
|---|---|---|
| 6E futures (S1–S3 ×1.0) | 3.5–6.7 bp (band 3.6–6.3) | **1.2–2.1×** |
| 6B futures (S1–S3 ×1.0) | 6.2–12.3 bp (band 6.3–11.2) | **2.1–3.7×** |

**Fence statement (court §b4, unchanged by the corrected fee layer): the futures vehicle
is NOT cheaper per notional than the dead spot proxy; any PB2 reopening argument of the
form "futures costs are lower" is CURRENTLY UNSUPPORTED.** The honest cost-distinction
claim is structural only (observable tick grid — constancy PROVEN both symbols;
decomposable fee components; no dealer-spread opacity) and even that requires the fee
layer to complete (A7 run; account verification NOT_RUN). This fence is the reason PB2
is HOLD and stays HOLD until the Co-Owner rules otherwise.

## 5. Power-vs-cost coupling (carried)

Court §c3 finding (restated in IDENTITY_BUDGET §7): at program-feasible n≈300–900 the
MDE floor (4–9 bp/trade class) coincides with these cost floors; 6B's F1 MDE-at-n
(4.2 bp) sits below 6B's own S1 cost floor (6.2–8.5 bp). A null at that n is the
pre-registered death of a family, NOT evidence of absence. No profitability inference
is drawn anywhere in this packet.

— End COST_CONTRACT_6E_6B.md. MODELED COST everywhere; UNDER REVIEW; NOT_RUN account
verification; conditional-on-PB2-lift.
