# 6J Quote-Orientation Re-proof + BBO Impossibility + Corrected Cost Layers

Task FUTURES-P3-QUARANTINE-20261004, lane **Q4-DATA-CHECKS**. Generated 2026-10-04 UTC.
Machine companion: `6j_orientation_check.json`. Read-only; one light 3-day slice
read of the existing `6J_cache/6j_outright_1m.parquet` (predicate-filtered,
~4.7k rows) — no heavy scans, no lock.

---

## (a) Quote-orientation law — RE-PROVEN from artifact AND from disk slice

**The law.** 6J is quoted **USD per JPY** (JPY/USD convention), NOT USDJPY.
Contract size ¥12,500,000; 2020–2026 absolute 1m band
**0.0061095 – 0.0099205** (implied USDJPY 163.68 – 100.80). **6J UP = yen
appreciation (yen strong); long 6J = long JPY / short USD; a "USDJPY-long" spot
idea is a 6J SHORT.** [FACT: 6J_DEEP_v2.md header "Quote-orientation trap"
(lines 56–62), restated §7; v1 6J_DOSSIER.md §1 "Mechanics" (¥12.5M, quoted USD
per JPY, CME product-page JPY/USD framing, S1_IDENTITY multiplier 12500000 /
minTick 5e-07); OBSERVED corroboration v1 §1 quote_convention_check — every close
on the 5e-7 grid, max deviation 0.0; 6J_DEEP_v2.md §8: tick-grid violations 0
across 2,843,938 bars]

**Disk re-proof (this lane)** [OBSERVED: script window = 2024-07-10T00:00Z →
2024-07-12T23:59Z slice of `6J_cache/6j_outright_1m.parquet`, front contract
6JU4 by volume (415,392 lots on 07-11)]:

- Date chosen is the **dossier-cited** 2024-07-11 MOF JPY-buying intervention
  (US-morning burst "2024-07-11 12:42 UTC london_pm/ny_am", 6J_DEEP_v2.md §0-6;
  drawdown leg 2024-07-10→08-05 "+11.1% … Jul-11/12 ops", §2).
- Result: 6JU4 close path 0.006249 → 0.0063775 on 2024-07-11 (**+2.056%**), day
  range 0.0062420–0.0064110, volume 415,392 vs 87,771 the prior day (4.73×
  prior-day ratio; the dossier's own metric — vs strict-past 21-session median —
  sits in its documented 1.75–4.79× op-day range).
- **The burst minute is exact**: 12:41→12:42 UTC close jumps 0.0062800 →
  0.0063325 (+5.25e-5 = **105 ticks in one minute**), the minute the dossier
  timestamps for the intervention burst (12:42 UTC).
- **Direction consistency**: implied USDJPY 1/0.006249 = 160.03 → 1/0.0063775 =
  156.80 — USDJPY DOWN ~2.0% (yen STRONG) while 6J quoted price rose +2.056%.
  This is exactly the law: yen strength = 6J price UP (USD per JPY). The session
  return is inside the dossier's documented op-day band +0.78…+2.35%
  (8/10 JPY-buying ops; 6J_DEEP_v2.md §0-6). The dispatch draft's tentative
  "price DOWN while yen strengthens" is the USDJPY-spot reflex; in 6J quote
  terms the correct signature is price UP — and that is what the data shows.
- Scale note: panel closes are price × 1e9 (same convention as the NQ caches);
  6,248,000 → 0.0062480 USD/JPY, on the 5e-7 grid.

**Verdict (a)**: PASS — orientation law re-proven from the dossier evidence chain
AND from a fresh 3-day disk slice on a dossier-cited intervention date; the
burst-minute match (12:42 UTC, 105 ticks) independently corroborates both the
orientation and the dossier's event anatomy.

## (b) BBO/execution — D5 law restated + measured thinness facts; NO fill/queue claims possible

**D5 law** (RANKING_FRAMEWORK.md §D5, FUTURES-OVERNIGHT-PREP-20261003):
floor ratio r = RT(S2-mid) ÷ MDE(n), where RT(S2-mid) is the **modeled**
round-trip at the middle tier built ONLY from corrected fees + close-proxy
spread + 1-tick-pair slippage (FEES_CORRECTED @72c9bc5b; all MODELED COST,
account verification NOT_RUN, UNDER REVIEW). The floor is arithmetic on
fees/spread/slippage tiers — NOT an expectancy, NOT a breakeven-win-rate claim,
NOT a PnL estimate; the words "measured/complete cost" are FORBIDDEN.

**Measured 6J book facts** [OBSERVED]:
- **MPM decision window (12:00–15:30 JST) book ~35.8% thinner than full day**:
  `6J_a2_sessions.json` → `boj_decision_window`: median 1m volume **34 vs 53**
  full-day → (53−34)/53 = **35.85%**; volume share 9.50% of session; 349,656
  bars (6J_DEEP_v2.md §3, §6-H4).
- Tokyo-morning execution: tokyo_am median 1m volume 59 vs ny_am 120 — Asia-hours
  execution pays ~2× thinner books (§6-H6).
- **Volume-definition gap**: summed 1m outright volume = **0.455×** (median;
  p10–p90 0.29–0.48; n=752 days, 2023-10+) the GLBX cleared-volume statistic
  (`6J_qa_ledger.json volume_scale_check_2023plus.median_ratio = 0.45543`) →
  volume SHARES/RATIOS only, never absolute levels.

**Conclusion**: the panel has **no BBO/quote data** — true spread, queue
position, fill probability and slippage are all **NOT_RUN** (BBO NOT_RUN is a
standing register item, 6J_DEEP_v2.md §9 / JPY_AUD_HYPOTHESES.md §8). Therefore
no fill/queue claim of any kind is possible on this evidence; the conservative
fill law binds: spread = high-biased close-proxy, slippage = assumed tick tiers,
stress law ×1.0/1.5/2.0 on (spread + declared slippage).

## (c) Cost layers with CORRECTED fees — MODELED, UNDER REVIEW, VERIFIED_VS_ACCOUNT=NOT_RUN

**Inputs (all cited)**:
- Fee layer: FEES_CORRECTED.md §2 (`FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/source/`),
  glued-superscript erratum P0-VERIFY-upheld: 6J all-in **T1 = 2.46 USD/side**
  (commission 0.85 + exchange 1.60 + reg 0.01); T2 2.26 / T3 2.06 / T4 1.86.
  FX row caveat: 1.60 is the generic CME "Forex Futures" group row — 6J not
  printed verbatim (mapping PARTIAL). All MODELED_COST, SOURCE=PUBLIC_REFERENCE,
  **VERIFIED_VS_ACCOUNT=NOT_RUN**, UNDER REVIEW.
- Tick arithmetic (VERIFIED from contract spec, not assumed): minTick
  **5e-7 USD/JPY quote units** × multiplier **12,500,000 JPY** = **$6.25/tick**
  (S1_IDENTITY.json 6J multiplier 12500000 / minTick 5e-07, v1 §1; corroborated
  by the measured grid: 0 tick-grid violations in 2.84M bars, §8; and by
  dossier §4 arithmetic −138 ticks ≈ −$863 → $6.254/tick). The legacy
  1e-4/$12.50 "JY" conflict remains unadjudicated for the CME rulebook source
  (transport-blocked) — broker secdef + raw grid agree on 5e-7/$6.25.
- Spread close-proxy: **$25/side = 4 ticks** (DC §1.7 6J column, 20d median
  close-proxy; high-biased; BBO NOT_RUN).
- Slippage: assumed tiers {1, 2, 3} ticks/side (DC §1.7 stress law ×1.0/1.5/2.0).
- Notional: **representative price 0.006383** (2026-10-01 panel close,
  6J_DEEP_v2.md §2) × ¥12,500,000 = **$79,787.50**; band extremes
  0.0061095 → $76,368.75 and 0.0099205 → $124,006.25.

**Arithmetic** (per side = fee + spread + slippage; RT = 2 × per side;
bp = RT / notional × 10^4):

| Tier (fee/side) | slip 1 tick ($6.25): per-side / RT / bp | slip 2 ticks ($12.50) | slip 3 ticks ($18.75) |
|---|---|---|---|
| T1 $2.46 | $33.71 / **$67.42** / **8.45 bp** | $39.96 / $79.92 / 10.02 bp | $46.21 / $92.42 / 11.58 bp |
| T2 $2.26 | $33.51 / $67.02 / 8.40 bp | $39.76 / $79.52 / 9.97 bp | $46.01 / $92.02 / 11.53 bp |
| T3 $2.06 | $33.31 / $66.62 / 8.35 bp | $39.56 / $79.12 / 9.92 bp | $45.81 / $91.62 / 11.48 bp |
| T4 $1.86 | $33.11 / $66.22 / 8.30 bp | $39.36 / $78.72 / 9.87 bp | $45.61 / $91.22 / 11.43 bp |

Headline (T1, 1-tick slip): **RT $67.42 = 8.45 bp** of the $79,787.50 notional —
reconciles exactly with the prior artifact's "$67.42 RT ≈ 8.5 bp"
(JPY_AUD_HYPOTHESES.md §JF1 cost level).

Band sensitivity (T1): at band-low notional $76,368.75 → 8.83 / 10.47 / 12.10 bp;
at band-high $124,006.25 → 5.44 / 6.44 / 7.45 bp. Same price move therefore costs
~1.6× more bp in the weak-yen regime than at the 2020 high.

**Labels (binding on every number above)**: MODELED COST / UNDER REVIEW /
VERIFIED_VS_ACCOUNT=NOT_RUN. Fee layer corrected (P0-VERIFY upheld) but the A7
re-verification packet is pending (Q3-FEE-A7-READY this round, PREPARE ONLY);
spread is a high-biased close proxy; slippage is an assumption; FX fee-group
mapping PARTIAL; no fill/queue claim is possible (see (b)).

## Verdicts

| Check | Verdict | Taxonomy |
|---|---|---|
| (a) orientation law | PROVEN (artifact + fresh disk slice, burst-minute exact) | FACT(artifact) + OBSERVED(script+window) |
| (b) BBO impossibility | CONFIRMED — no fill/queue claims; conservative fill law binds | OBSERVED(34 vs 53, 0.455×) + NOT_RUN(BBO) |
| (c) cost layers | COMPUTED — headline RT $67.42 = 8.45 bp (T1/1-tick); range 8.30–12.10 bp across tiers on 2026 notional | MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN |
