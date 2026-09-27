# RULE_CANDIDATES — I001 corpus (Lane P2, 2026-09-27)

## STATUS: RANKED — LAWFUL under FREEZE_R1_ADDENDUM_r2_supplementary.md

- Base round (30 fetches) reached 10 admissible / 5 authors → floor failed. Addendum r2 granted
  ≤20 supplementary fetches (total budget 50); round 2 used **7 fetches** and closed the gap.
- **Final corpus: 12 admissible entries (E01–E12) from 6 distinct authors/channels.** Entry floor
  (≥12) and author floor (≥5) both met → frequency ranking per protocol §1.5 is LAWFUL.
- This is a **frequency ranking, not a viability ranking.** The frozen collision table (Bảng 1)
  pre-judges every row below DEAD (rows 1/2/4/7/8/9); the measured per-rule F-0 death ledger that
  follows remains the cycle's product. Per §1.5-5, each RULE enters F-0 individually; if >3
  survive, the council selects ≤3 by maximal distinctness (payer/mechanism, PIT layer, risk shape)
  — criterion declared here, before any outcome exists.
- Outcome-blind: no price panel was ever loaded; every definition below is built from source TEXT
  verbatim (quotes in CORPUS_MANIFEST.jsonl). K-COST notes are declared arithmetic on source-stated
  numbers only.

## Class census (classes aligned to Bảng 1 rows; frequency = distinct authors, K=5 applied)

| rank | class (id) | taxonomy row | distinct authors | setups (entries) | status |
|------|-----------|--------------|------------------|------------------|--------|
| 1 (tie) | RANGE_FADE family (RC-01) | 7 | **4** | 4 (E01, E05, E08, E10) | ranked |
| 1 (tie) | BREAKOUT_CONTINUATION family (RC-02+RC-05) | 1 (E09 adjacent 2) | **4** | 4 (E04, E07, E09, E11) | ranked |
| 3 | TREND_PULLBACK (RC-03+RC-04) | 4 | **1** | 2 (E02, E06) | ranked |
| 4 | PATTERN_REVERSAL_LEVEL (RC-07) | 9 | **1** | 1 (E12) | ranked |
| 5 | NEWS_FADE (RC-06) | 8 | **1** | 1 (E03) | ranked, BLOCKED_DATA |

- Tie at rank 1 (4 authors / 4 setups each) broken by the declared rule: (i) setup count — equal;
  (ii) earliest median publication timestamp — row 7 median (2025-05-21/2025-11-04 pair) precedes
  row 1 median (2025-05-16/2025-11-04 pair is later; row-1 set spans 2023-05-28..2026-06-25).
  Row 7 is therefore listed first. The tie-break is bookkeeping only — both families pass to F-0
  in full.
- Sub-variant note: within row 1, E09 (session-anchor/daily-open continuation) is a clock-anchored
  variant of the same level→break→continuation skeleton (taxonomy rows 1/2 adjacent); it is
  counted in the row-1 class per its row guess and additionally carries its own RC-05 definition
  below because its trigger is operationally distinct.
- N = 5 ranked classes (≤10 permitted). Same-skeleton UNCODIFIABLE corroboration (not counted in
  frequency): U01 Bybit breakout (no target), U09 Phemex breakout idea (no stop), U07 KuCoin blog
  (no stop/exit), U08 KuCoin learn (no stop), U13 Binance patterns (no per-setup stop/target).

## K-COST ceiling note (binding RT ladder 11.92 / 17.88 / 23.84 bps)

Declared RT decomposition per proposal field 8: taker fee 5 bps ×2 + 1 adverse tick ×2 + measured
spread census at fill hour, with declared-band escalation ×1.5 (17.88 bps) / ×2.0 (23.84 bps) for
out-of-census-window fills. The **binding ceiling for any codified class is the worst-case rung it
declares; 23.84 bps is the binding rung unless a RULE's frozen fixture confines fills to the
census window (11.92 bps)**. K-COST notes below compare source-stated geometry (the sources' own
numbers, as declared arithmetic) against the 23.84 bps rung. No class is killed at K-COST on its
stated geometry; every class carries a DEAD collision pre-judgment from Bảng 1 instead. Any RULE
whose frozen construction shrinks stated capture below the binding rung dies at K-COST at freeze.

---

## RANK 1 (tie) — RC-01 RANGE_FADE — taxonomy row 7 — 4 distinct authors

- **Setups/authors:** Phemex Academy (E01, 2025-05-21), Kraken Learn (E05 overextension variant,
  2025-11-04), LiteFinance Blog (E08, 2026-06-25), Binance Academy (E10, 2020-07-01).
- **Closed-bar constructible definition (§4.2).** Range state: boundary low/high = min low / max
  high of the prior W closed intraday bars (**W and frame are source-unstated → frozen
  parameters**; E08's worked example quantifies the band: limit entry $2,250 vs $2,200 floor, TP
  $2,390 vs $2,400 ceiling, stop $2,180; E01 quantifies the exit band: "sell order at $1,590 or
  $1,595 — just below the peak"; E10 leaves "near support" unquantified — recorded unquantified).
  Trigger: a closed bar touches the entry band. **Earliest order at the first tradable quote
  after that bar closes**, filled at opposite-side quote. Stop: outside the range ("always place
  a stop loss just outside the range" E01; "$2,180" E08; "a level that confirms a breakout has
  happened" E10). Exit: limit at the opposite boundary band. No same-bar high/low ordering
  anywhere. Overextension sub-variant (E05): trigger = closed bar with RSI ≤ 25 AND close below
  the lower Bollinger band while a prior closed-bar range exists; entry at first tradable quote
  after signal-bar close; stop below excursion low; **exit = first tradable quote back inside the
  prior range** (source example exits $6.55 vs $6.50–$7.20 range).
- **Flat-by / holding horizon:** hours within a session ("range traders stack multiple trades like
  this throughout sessions" — Kraken); **declared flat-by = end of UTC day** (not source-explicit;
  frozen).
- **Declared payer/premium story FROM THE SOURCE:** E01: "The goal is to exit before the crowd of
  sellers at $1,600 does" — the boundary-crowd is the payer; E08: "ideal for market makers, who
  profit from spreads and commissions" — mid-range entrants pay; E10: "price will continue to
  bounce between the upper and lower edges of the range until a breakout occurs" — momentum
  entrants pay; E05: "trusting the mean reversion thesis" — overextended sellers pay. All lore,
  recorded as claims.
- **K-COST note:** source-stated captures are multi-percent (E08: entry 2,250 → TP 2,390 ≈ 6.2%
  gross vs stop 2,180 ≈ 3.1% risk; E05: 6.30 → 6.55 ≈ 4.0% vs 6.10 ≈ 3.3%) — ≥ 23.84 bps by
  1–2 orders of magnitude as declared. No K-COST kill. Binding wall = F-0 collision (row 7 DEAD:
  FXOS-04, TRACKA1-M1-RANGEFADE-PIT, FXFV1-A3-P2, V16 CLOSE-DISPLACE-FADE).

## RANK 1 (tie) — RC-02/RC-05 BREAKOUT_CONTINUATION — taxonomy row 1 (E09 adjacent row 2) — 4 distinct authors

- **Setups/authors:** Kraken Learn (E04 volume-confirmed breakout, 2025-11-04), LiteFinance
  (E07 breakout checklist, 2026-06-25), CryptoCred (E09 daily-open reclaim continuation,
  2023-05-28), Phemex Academy (E11 TMF volume-flow breakout, 2025-05-16).
- **Closed-bar constructible definitions (§4.2).**
  - *Core breakout (E04 form):* range = session consolidation high/low from closed bars; volume
    state = signal-bar volume ≥ 3× trailing average hourly volume ("three times the average
    hourly volume") — closed-bar computable; signal bar = closed bar whose close is above range
    high meeting the volume state; **order at the first tradable quote after signal-bar close**
    (E04: "enters a long position at $0.91"); stop = "just below the former resistance turned
    support" ($0.88), trail to breakeven then trail; exit = volume taper ("exit around $0.95
    when volume begins to taper off"). No intrabar ordering.
  - *TMF variant (E11):* trigger adds a volume-flow indicator state — TMF crosses positive while
    price closes above consolidation range; entry at first tradable quote after that close;
    stop "below a recent swing low or support" (closed-bar swing); exit "at the next major
    resistance zones" or Fibonacci/previous-high levels (target = next closed-bar resistance
    level; magnitude source-unstated → flagged).
  - *LiteFinance checklist (E07):* "Identify a consolidation range... Wait for a sharp breakout.
    Confirm that open interest is rising. Place a stop-loss beyond the signal candlestick. Take
    profit at the next key level." — **as stated, NOT_CONSTRUCTIBLE on the closed-kline plane**
    (open interest is a futures data layer, not closed klines). Closest legal approximation IS
    stated by the same source ("a genuine wave, one confirmed by strong trading volume and rising
    open interest") → volume-only variant recorded as RC-02-approx-1, fed by E07 alongside E04.
    Stop placement "beyond the signal candlestick" = beyond the signal bar's extreme (closed-bar;
    buffer = frozen parameter).
  - *Session-anchor variant (E09, RC-05):* DO = 00:00 UTC open (known at every bar close); bias
    state = declared subset of the author's enumerated HTF-bias sources (closed-bar; **bias
    operationalization source-unstated → frozen parameter**); trigger = closed bar closes back
    across DO ("Buy reclaim of DO on a bullish trend day"); entry M5/M15/H1 at first tradable
    quote after signal-bar close; stop = running intraday extreme ("Invalidation: LoD... / HoD...");
    exit = hold the trend day.
- **Flat-by / holding horizon:** intraday momentum legs; **declared flat-by = end of UTC day** for
  all four variants (E09's own horizon is the trend day; the others' examples resolve within
  hours). No multi-day carry; force-flat before any 8h funding settlement is structural.
- **Declared payer/premium story FROM THE SOURCE:** E04: "pent-up buying or selling pressure is
  released"; "low-volume breakouts often fizzle out or reverse into false signals" — the payer is
  the late chaser after the fade-traders' level exits; E07: "a breakout can quickly turn into a
  trap... a false breakout caused by a liquidity sweep" — stop-run victims pay (row-9 lore, noted
  for collision); E11: "the breakout might have legs... targeting the next resistance level" —
  breakout doubters pay; E09: payer NOT_STATED_BY_SOURCE (honest flag; constructed story would
  need to pass the fictional-counterparty veto).
- **K-COST note:** E04's own numbers: entry 0.91 → exit ~0.95 ≈ 4.4% gross vs stop 0.88 ≈ 3.3%
  risk — ≥ 23.84 bps as declared. E07/E11/E09 target magnitudes are source-unstated
  (UNMEASURED_FROM_SOURCE flag); any frozen construction must show declared capture > binding
  rung at freeze or die at K-COST. Binding wall = F-0 collision (row 1 DEAD both tracks:
  FXFV2-A4-P1, PSV1-*CONTINUATION, SPRINT H-VOLCOMP-BRKOUT, V17-a5-P1).

## RANK 3 — RC-03/RC-04 TREND_PULLBACK — taxonomy row 4 — 1 distinct author (2 setups)

- **Setups/authors:** Kraken Learn (E02 trend-follow with swing-low trail, E06 VWAP/volume-node
  pullback, both 2025-11-04).
- **Closed-bar constructible definitions (§4.2).**
  - *E02:* trend state = ≥2 higher highs and ≥2 higher lows on closed 1h bars (pivot confirm ≥1
    bar); entry at first tradable quote after the confirmation bar closes (source gives no
    pullback level — at-market entry recorded as stated); stop = "below the most recent swing low"
    (closed-bar swing), moved to breakeven after +1 leg ("adjust their stop-loss to $145"); exit =
    closed bar makes a lower low against trend ("If SOL suddenly breaks below $145 and makes a
    lower low... exits").
  - *E06:* session VWAP (00:00-UTC anchored, closed-bar cumulative typical-price×volume ÷ volume)
    + session volume-node (typical-price volume histogram from closed bars; **binning method
    source-unstated → frozen parameter**); trigger = pullback bar closes within the VWAP/node
    confluence zone; entry = limit at node, earliest fill at first tradable quote after the
    approach bar closes; stop = below node ("stop-loss at $38.10"); exit = "as the price moves
    away from the support zone" (strength resumption; numeric target source-unstated → flagged).
- **Flat-by / holding horizon:** session trend leg; **declared flat-by = end of UTC day.**
- **Declared payer/premium story FROM THE SOURCE:** E02: none named (NOT_STATED_BY_SOURCE —
  honest flag); E06: "capturing the bounce that institutional levels provided"; VWAP as "widely
  used benchmark among institutional traders" — lore only, recorded as claims.
- **K-COST note:** E02 stated numbers: 145 → 148 ≈ 2.07% capture vs 142 stop ≈ 2.07% risk; E06:
  38.45 → 39.50 ≈ 2.7% capture vs 38.10 ≈ 0.91% risk — both ≥ 23.84 bps as declared. No K-COST
  kill. Binding wall = F-0 collision (row 4 DEAD: momentum/continuation every cadence;
  H1TSMOM/H1DONCH ancestry; PSV1-BTC_H4-UPTREND-DONCHIAN).

## RANK 4 — RC-07 PATTERN_REVERSAL_LEVEL — taxonomy row 9 — 1 distinct author

- **Setups/authors:** Bybit Learn (E12 head-and-shoulders, 2021-01-26).
- **Closed-bar constructible definition (§4.2).** Pattern state from closed bars: three pivot
  highs (left shoulder, head, right shoulder; pivots confirm ≥1 bar) with head the highest and
  shoulders at similar levels; neckline = line through the two intervening pivot lows (may be
  tilted; "if the slope is down, it produces a more reliable signal" — recorded); prior-uptrend
  precondition via MA state (source: "defining the prior trend is essential... a simple Moving
  Average (MA)"). Signal bar = **closed bar whose close breaks below the neckline** (volume spike
  ideal, per source). **Entry: "right after the candle's close that breaks below the neckline" —
  first tradable quote after signal-bar close** (source explicitly closed-bar; no intrabar
  ordering). Stop = "slightly above the highest top, which is the pattern's head" (buffer = frozen
  parameter; inverse pattern: "right below the lower low"). **Target = measured move:** "measure
  the distance between the neckline and the top of the head... subtract it from the breakout
  price."
- **Flat-by / holding horizon:** reversal leg to the measured target or stop; **declared flat-by =
  end of UTC day** (intraday instance; not source-explicit — flagged).
- **Declared payer/premium story FROM THE SOURCE:** "the neckline... is responsible for triggering
  the bearish signal. So, if the price breaks below it, we're free to go short"; "Traders consider
  it to be one of the most reliable technical analysis patterns" — payer lore = trapped bulls at
  the neckline retest who pay the breakdown entrant; reliability language is a claim, not
  evidence.
- **K-COST note:** capture = measured-move distance (pattern height), risk = head-to-neckline
  distance — structurally pattern-scale (multi-percent) but numerically UNMEASURED_FROM_SOURCE
  (no bps in article); declared margin over 23.84 bps asserted at pattern scale, to be recomputed
  at freeze on the actual constructed levels. Binding wall = F-0 collision (row 9 DEAD:
  "failed breakout" = relabeled row-1 skeleton, anti-variant §2.3; SRLVCX1-M1 sweep-absorption;
  V17-A6-P2 OICASCADE).

## RANK 5 — RC-06 NEWS_FADE — taxonomy row 8 — 1 distinct author — **BLOCKED_DATA**

- **Setups/authors:** Kraken Learn (E03 XRP news-fade, 2025-11-04).
- **Geometry as stated:** trigger = news spike → stabilization → "signs of exhaustion (declining
  volume, weakening momentum)" (closed-bar states); direction short; entry after stabilization
  ($2.42); stop "above $2.50"; exit ~$2.30 partial gap-fill. Closed-bar portion constructible.
- **Blocker (protocol §1.5-4):** news-touch rules require a PIT-authoritative event calendar with
  true available_at; none staged for SOLUSDT ⇒ **BLOCKED_DATA, no proxy permitted.** The class is
  ranked by frequency but cannot be constructed or trialed this cycle; it passes to the ledger as
  DATA-GATED (Bảng 1 row 8 pre-judgment: "DEAD + DATA-GATED").
- **Flat-by / holding horizon:** hours post-event ("wait 2-4 hours after major news" — source
  guidance); declared flat-by = end of UTC day.
- **Declared payer/premium story FROM THE SOURCE:** "anticipating the gap will partially fill as
  early buyers take profits" — post-news chasers pay the fade; hedgers/panicking retail per
  Bảng 1 lore.
- **K-COST note:** source-stated example: 2.42 → 2.30 ≈ 4.96% capture vs 2.50 stop ≈ 3.3% risk —
  ≥ 23.84 bps as declared; named tail: gap through stop absorbed at taker crossing. Moot until a
  PIT calendar exists.

---

## What the council does next (§1.5-5)

1. Each of the 5 ranked classes yields its setup-level RULEs (12 admissible setups, minus E03
   BLOCKED_DATA = 11 constructible RULE candidates; E07 enters only as its volume-only
   approximation with the OI-as-stated variant marked NOT_CONSTRUCTIBLE).
2. Every RULE runs the F-0 skeleton test first (Bảng 1 collision): rows 1/2/4/7/8/9 are all
   pre-judged DEAD. Pre-registered expectation (proposal §4): ≥80% die here; the per-rule death
   ledger (rule → collision row → kill code) is the cycle product.
3. If >3 RULEs survive, council selects ≤3 by maximal distinctness across (a) payer/mechanism,
   (b) PIT information layer, (c) risk shape; pairs differing by less are merged (anti-variant
   §2.3).
4. Source-unstated parameters to freeze before any trial: W/frame/band (RC-01), bias
   operationalization + entry timeframe (RC-05), volume-node binning (RC-04), stop buffers
   (RC-02/E07, RC-07), MA state for prior trend (RC-07).

**Chưa có PnL nào được xem hoặc tính toán cho identity này.**
