# 6B DEEP-FOUR V3 ADDENDUM — British Pound Futures (GBP/USD), research v3 layer on dossier v2

- Task: `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003`, lane **B2-DEEP-6E6B**,
  generated 2026-10-03 (UTC).
- Class: PREP desk research on existing evidence + official public sources.
  **0 PnL, 0 scored runs, 0 signal selection, 0 ranking by any return
  statistic.** Every parameter carries **[PROVISIONAL]**. PB2 remains **HOLD**
  by Co-Owner ruling; nothing here reopens anything.
- Base evidence (read in full, errata M1–M7 applied):
  `research/control/FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/6B_DEEP_v2.md`
  (hereafter 6B_v2 §n, incl. ERRATA ledger §11);
  `research/control/FUTURES-DATACONTRACT-QUAL-V1/DATACONTRACT_QUALIFICATION.md`
  (DC §n); `PLAYBOOKS_DRAFT.md` r5 (PB §n); `SUMMARY_QUAL_ACTIONS.md` r6
  (SQA §n). Analysis JSONs under
  `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/` cited as
  `script:field`.
- Taxonomy: **FACT** (primary source + date, URL where official) /
  **OBSERVED** (script + window) / **POSTULATED** / **NOT_RUN** / **DERIVED**
  (arithmetic from named measured inputs).

---

## 1. Identity & registry

- 6B = CME Globex British Pound futures; GBP 62,500 per contract; quoted USD
  per GBP; **minTick 0.0001 = $6.25/tick, primary-source adjudicated** from
  19,183 GLBX definition rows 2023-10→2026-10 (uniformly 0.0001; resolves the
  v1 AMP(0.0001)/TK(0.0002) conflict) [FACT: vendor definition records; 6B_v2
  §7; DC §1.1].
- Registry: 48 registry rows resolve to **32 distinct quarterly (HMUZ)**
  contract keys; 28 front-scale quarterlies 2020→2026 carry the real market
  (>1M contracts lifetime each); **59 stray clusters quarantined** — 57 dead
  serial-month clusters (0.256% of outright volume), 1 non-6B symbol `GCQ4`
  (gold leak, 2,139 bars 2020-07→2020-11), 1 `6BM5` early cluster (1,392 bars
  ~5y before plausible listing; unresolved vendor-side) [OBSERVED,
  `6B_deep_lib.build_contract_registry`; `6B_a7_quality.py:stray_clusters`;
  6B_v2 §0.1/§7; DC §1.6].
- LTD rule: 2 business days before 3rd Wednesday (Mon–Fri approximation;
  Monday-holiday shifts tolerated, e.g. 6BM3 last bar 2023-06-16 Juneteenth
  week) [OBSERVED, 6B_v2 §0.1].

## 2. PIT inventory

| source | available_at | status |
|---|---|---|
| BoE MPC calendars (2020→2027) | announcements 12:00 London (measured spike minute 720: 3,451 vs 1,392 contracts/min at 12:01) | **PASS_EVIDENCED (assembly-method disclosed)** — assembled from bankofengland.co.uk "MPC dates for YYYY" + upcoming-mpc-dates pages, fetched 2026-10-02; 2020-03-11 moved meeting + 2020-03-19 emergency from the Bank-Rate table; rate-change subset == local parquet exactly [FACT/OBSERVED, 6B_v2 §0; DC §1.4] |
| BoE Official Bank Rate (2000→2025-12-18) | official_history_latest, revision-free levels | FACT; vintage caveat benign for same-day-known policy targets [6B_v2 §0/§3] |
| FOMC statements (59 in window, 58 dates in panel) | 59/59 in-document release-time proof; 53 at 14:00 ET = 13:00 CT anchor | PASS_EVIDENCED [FACT/OBSERVED, `6B_a4_events.json:fomc`; 6B_v2 §0 ERRATUM M4] |
| Gilt nominal curve (local copy) | declared publication lag; coverage **ends 2024** | **PARTIAL** — PIT use requires ≥1 business-day lag (DECLARED_LAG law); 2025-2026 gilt coupling NOT_RUN [FACT; 6B_v2 §0/§6] |
| Fed DFEDTARU (FRED latest) | latest-vintage, not vintage-true | **rates NOT PIT-strict** — descriptive/CIP use with sensitivity only [FACT; 6B_v2 §0; DC §1.4] |
| ONS UK-data calendar / consensus surprise | — | NOT_RUN (unfetched; no licensed surprise source) |

## 3. Session structure by era / DST (LOCAL-CLOCK LAW)

- Session template: 17:00 CT (D-1) → 16:00 CT (D); 2,549,633 outright 1m rows
  2020-01→2026-09; 0 weekend bars; exactly 1 bar inside the maintenance break
  in 6.8y [OBSERVED, `6B_build_cache.py`; `6B_a7_quality.py`; 6B_v2 §0.1/§7].
- **BoE 12:00 London anchor is minute-stable across UK/US DST-mismatch
  weeks**: 2022-10-06 12:00 London = 06:00 CT (minute 360); 2022-03-17 /
  2022-11-03 / 2023-03-23 / 2023-11-02 / 2024-03-21 / 2024-10-31 = 07:00 CT
  (minute 420) [OBSERVED, `6B_a2_sessions.py:boe_1200_london_in_ct_clock`;
  6B_v2 §0.1]. MPC-day mean volume by London minute peaks at exactly minute
  720 (3,450.8 vs 1,392.2 at 721, 1,073.7 at 722) [OBSERVED,
  `6B_a2_sessions.json:mpc_day_top5_minutes`].
- London-morning volume share 07:00–12:00 London: **28.7% (2020-21) → 27.5%
  (2022) → 27.5% (2023-24) → 23.7% (2025-26)** — ~5pp drift toward US hours
  (12:00–17:00 block 44.6%→45.5–46.5%; 17:00–24:00 17.9%→21.8%); the 08:00
  London hour falls hardest (7.7%→5.7%); modal hour 15:00 London
  (12.1–12.8% every era) [OBSERVED,
  `6B_a2_sessions.json:volume_share_by_london_hour`, `london_morning_share_07_12`;
  6B_v2 §2]. Mechanism POSTULATED (US-macro dominance of the
  rate-differential regime). **Consequence: any session-structure hypothesis
  must be rolling-window, not full-sample.**
- Per-minute vol: London morning (08:00–12:00) vs US RTH near-parity — above
  in 2020-22, slightly below every year 2023-26 [OBSERVED,
  `6B_a2_sessions.json:per_minute_vol_by_segment_pct_ann_by_year`; 6B_v2 §2].

## 4. Roll & calendar

- **Construction rule (frozen, DC §1.3): PIT k=5 volume-crossover** — switch
  at first close where next quarterly's trailing-5-session mean volume >
  held's (decision at close t, effective t+1), **+ mandatory cease-guard**
  (force-switch if held contract ceases trading: <25% bars or volume≈0 while
  rule has not switched — 6J lesson, binding FX-wide; DC §1.3).
- Crossover timing: **median 11 sessions AFTER the declared calendar roll**
  (min 9, q25 10, q75 11, max 13; 27/27 crossovers INSIDE the old contract's
  delivery month) [OBSERVED, `6B_a3_term.json:migration`
  (median_sessions_declared_to_crossover 11.0)]. Old contract still trades
  66k–172k contracts at every declared roll (median old:new = 129:1; old keeps
  median 824,460 contracts inside its delivery month) [OBSERVED, same block].
- Thin-window exposure measured: the calendar rule holds the thin new
  contract ~11 sessions post-roll — held-contract volume
  **1,069..13,222 contracts/day (median ~3.1k)** in 2024-03-01..12 vs 100k+
  on the old; 114/1,746 held-chain sessions have <600 printed 1m bars, almost
  all inside those windows [OBSERVED, 6B_v2 §3 ERRATUM M7; `6B_a7_quality.py:
  sessions_below_600_bars`]. The k=5 rule removes this window by construction;
  cease-guard is the safety net.
- OI-informed alternative (2023-12→2026-09, 11 rolls): OI crossover LEADS
  volume crossover by 5–7 days (median −6); OI statistic has next-morning
  publication lag (adapter law) [OBSERVED, `6B_a3_term.json:oi_vs_volume_crossover`;
  6B_v2 §3].
- Roll-gap distribution: n=27, mean +6.5 ticks, median +5.0, q05..q95
  −3.7..+22.7, 20 positive / 7 negative [OBSERVED,
  `6B_a3_term.json:roll_gap_dist_ticks`].
- **Calendar authority status: FX holidays official = NOT_RUN at write time**
  (DC §1.2 6B row "NOT_RUN official"; missing-weekday sessions currently
  inferred from data only, 6B_v2 §7). Lane **A2-CMECAL-FX** is extracting the
  official CME calendar in this same task — NOT consumed here.
  **REQUIREMENTS on A2 (requirements, not results)**: (i) holidays +
  early-closes per product-year, official sources (live/archived official),
  verbatim tables, no gap-fill inference; (ii) expiration-rule confirmation
  (2-business-days-before-3rd-Wednesday with UK/US holiday interplay — the
  Monday-holiday LTD shifts already observed in bars must reconcile);
  (iii) source URL + capture date per date; (iv) uncertain ⇒ EXCLUDE/NOT_RUN.
  Must reconcile the v2-observed missing weekday sessions (2020-04-10,
  2020-12-25, 2021-01-01, 2021-12-24, 2022-04-15, 2022-12-26, 2023-01-02,
  2023-12-25, 2024-01-01, 2024-03-29, …) against the official list.

## 5. Event anatomy (release-anchored, descriptive only)

- BoE MPC days (n=56 in panel: 22 rate-change / 34 hold): ±30m around 12:00
  London median volume 17,454 vs 3,371 (non-MPC Thursday) = **5.2×**;
  |1m ret| sum 2.5×; window range 4.1×. **First 5 minutes: 7,091 vs 380 =
  18.7×**, |ret| 7.6×. Whole day 1.51× volume, 1.51× range. Change-vs-hold:
  day volume ~equal (calendar drives attendance); first-5m volume and |move|
  larger on change days [OBSERVED, `6B_a4_events.json:boe`; 6B_v2 §4].
- FOMC days (58 in panel): first 5m after 13:00 CT 2,266 vs 239 = **9.5×**
  (USD-leg event, ~half BoE intensity); ±30m 2.6×; whole day 1.12× only
  [OBSERVED, `6B_a4_events.json:fomc`; 6B_v2 §4].
- Event-window execution law (6B_v2 H2'): entry must assume ≥1 minute
  post-12:00:00 London on MPC days — same-minute fills optimistic against the
  18.7× spike [OBSERVED basis; law statement in 6B_v2 §8-H2'].
- Crisis bar sanity: 2022-09-26 = all-data volume record 374,255 contracts
  (4.5× median day), low 1.0392 [OBSERVED, 6B_v2 §1].

## 6. Coverage & data quality (2020-01 → 2026-09, 6.8y)

- Panel: 2,549,633 outright 1m rows; held calendar chain 1,746 sessions;
  era table (backfill 518/522 weekday-days, main 1,096/1,107, recent 132/132);
  0 OHLC violations, 0 zero-volume bars, 0 duplicate keys; butt joints
  2022-01-01 / 2026-04-01 zero-duplicate, closes continuous [OBSERVED,
  `6B_a7_quality.py` era table, `butt_joints`; 6B_v2 §7].
- Contamination cleanups ALREADY APPLIED (do not re-apply): 59 stray clusters
  quarantined incl. GCQ4 leak and 6BM5 early cluster; spread-instrument rows
  excluded (37,943/135,537/15,559 per era); truncated final session
  2026-10-01 excluded from full-session statistics; CoT tidy fix (M6,
  whitespace-only, numbers unchanged) [OBSERVED, 6B_v2 §7/§11].
- Chain-law agreement: calendar rule vs k=5 rule agree 1,458/1,746 sessions
  (83.5%); daily-return corr 0.9998; roll-boundary returns excluded from all
  statistics on both chains [OBSERVED, `6B_build_cache.py`; 6B_v2 §0.1].
- Regime context for any future windowing: rolling-63d ann vol 4.72%→20.08%
  (max window ends 2022-12-15, LDI/fiscal crisis = THE vol regime of record;
  all top-8 stress windows end 2022-11-28→12-20); VR(21)=0.73, VR(63)=0.60
  multi-week mean-reversion, suspended in 2022 (VR21 0.98) [OBSERVED,
  `6B_a1_regimes.py`; 6B_v2 §1].

## 7. Spread / cost / margin — MODELED COST ONLY

- Spread: close-proxy **$18.75 half-turn** (= 3 ticks × $6.25), **high-biased**
  (close-proxy; BBO NOT_RUN, DC §1.7) [OBSERVED, DC §1.7]. In bp of notional
  [DERIVED]: 0.0003/px × 1e4 → **2.11–2.89 bp/side** across window closes
  1.0392–1.4205 (2.31 bp at px 1.30; notional $81,250 at 1.30). **6B's
  per-notional spread proxy is materially ABOVE 6E's (1.21–1.57 bp) and above
  the dead FX-spot families' frozen 1.5 bp/side proxy** — cost structure does
  NOT trivially favor the futures vehicle; see court draft §b.
- Exchange fee 6B: **NOT_FETCHED** (DC §1.7; IBKR $0.85/side known from v1;
  lane A4-FEES in flight, not consumed here). Slippage {1,2,3} ticks/side
  research assumptions [PROVISIONAL, D1]. ⇒ MODELED COST only, BLOCKED one
  more layer; "measured/complete cost" FORBIDDEN.
- Modeled round-trip arithmetic [DERIVED]: spread 4.2–5.8 bp + slippage
  1.5–4.6 bp + fees (commission ~0.021 bp/side at $81.25k + exchange
  NOT_FETCHED) ≈ **5.7–10.4 bp + exchange fee** round trip.
- Margin: ~$2.2–2.4k/contract initial (two public sources <2% disagreement;
  account verification NOT_RUN) [FACT public-reference, DC §1.7].
- **CIP facts are INPUTS, not alpha** (owner law, DC §1.3): corr(roll-gap
  ticks, Fed-target-upper − Bank Rate) = **Pearson +0.84** (Spearman +0.744,
  ERRATUM M1) across 27 rolls; mean gap +9.4 ticks when diff>0 (n=19) vs −3.0
  when diff<0 (n=1); regression slope 0.186%/pp vs theory 0.253%/pp (91-day
  ACT/360) = realized carry ≈ 73% of textbook CIP; calendar-spread medians
  walk with the differential through the whole cycle (+19.5 ticks 2022 →
  −1.0 2026) [OBSERVED, `6B_a3_term.json:gap_vs_policy_diff`, `cip_check`,
  `calendar_spread_median_ticks_by_year`; 6B_v2 §3]. **v1's mixed-sign
  verdict is OVERTURNED**: v1's four rolls (2025-11→2026-08) all sat at a
  roll-date differential of exactly 0.00pp (synchronized-policy window;
  zero-diff rolls show small mixed-sign gaps −5..+13 ticks — exactly what v1
  measured) [OBSERVED, 6B_v2 §3 ERRATUM M2; A7-6B CONFIRMED]. Vintage
  caveat stands: BoE revision-free; DFEDTARU latest-not-vintage (benign for
  same-day-known targets, disclosed).

## 8. Economic mechanism — POSTULATED, both directions

- **H-C (continuation)**: London-morning GBP flow (08:00–12:00 London,
  23.7–28.7% of volume with drift) discovers UK-specific and global-dollar
  information while US liquidity is absent; a 1m close outside the
  London-morning range during 11:00–15:30 London encodes it; arriving US
  liquidity continues the move into the 16:00 CT close.
- **H-D (fade)**: London range extension is thin-liquidity over-extension;
  arriving US liquidity (modal hour 15:00 London = 09:00–10:00 CT) absorbs
  and fades it — consistent with 6B's multi-week mean-reversion (VR21 0.73)
  though that daily-frequency evidence does not transfer directly to the
  intraday horizon [POSTULATED; VR facts OBSERVED §6].
- 6B-specific confounder the court must carry: **London-share drift
  (28.7%→23.7%)** — a full-sample London effect would smear two different
  liquidity regimes; rolling-window mandatory (§3).

## 9. Hypothesis pair — H-C vs H-D [PROVISIONAL, PB2 remains HOLD]

Mirrors PLAYBOOKS_DRAFT §2 (PB2) field table; nothing registered; every
parameter [PROVISIONAL].

| field | specification [PROVISIONAL] |
|---|---|
| Universe | 6B held chain per DC §1.3 (k=5 volume-crossover + cease-guard); 2020-01→2026-09 |
| Signal | R_lon = high−low of 08:00–11:00 Europe/London local (LOCAL-CLOCK LAW §3); trigger = first 1m close strictly outside R_lon during 11:00–15:30 London local |
| Entry | fill = open of next 1m bar after trigger; **mandatory delay variants +1 bar and +30m** (07:30 CT US-macro spike class falls in window; BoE 12:00 London anchor minute-720 is base-EXCLUDED via stand-aside) |
| Stand-aside | (i) BoE MPC days base-EXCLUDE (calendar PASS_EVIDENCED §2; INCLUDE = sensitivity leg only, Co-Owner decision at any reopen); (ii) FOMC days EXCLUDE (13:00 CT 9.5× inside holding window); (iii) London-morning coverage <80% of expected bars EXCLUDE (thin k=5 post-roll windows measured §4 make this load-bearing on 6B); (iv) warmup 60d; (v) calendar-uncertain dates EXCLUDE/NOT_RUN until A2 lands (§4) |
| TP | 2.0 × SL distance [PROVISIONAL R=2] |
| SL | 1.0 × ATR(20d, session range, median) [PROVISIONAL; ATR value NOT_RUN here] |
| Same-bar TP/SL | deterministic conservative: **SL priority** [PROVISIONAL law, PB §4] |
| Time exit | 16:00 CT (flat before close) |
| Roll | DC §1.3 k=5 + cease-guard (§4); flat before roll-session close |
| Sizing | risk 0.5% equity/trade [PROVISIONAL]; cap 5 contracts [PROVISIONAL capacity] |
| Cost | MODELED COST with exchange NOT_FETCHED disclosed (§7); 6B per-notional proxy above both 6E and the dead spot families — cost-overcome bar is higher |
| Counter-hypothesis controls | clock/placebo (same-time random-sign, seeded, multi-seed); always-in-London-window baseline; **London-share drift split (2020-22 vs 2023-26)** as a 6B-specific control (PB §2 counter row) |
| Kill rules | K1: effect survives ONLY with event-days INCLUDED ⇒ event-effect reclassification (needs surprise data NOT_RUN); K2: both arms below Stage-A floor ⇒ family dead, no re-tparam; K3: 6B vs 6E opposite sign ⇒ no common-mechanism claim; K4: sign flips in DST-mismatch weeks under CT bucketing ⇒ clock-law bug not alpha; K5: rolling-window sign instability across 2020-22 vs 2023-26 ⇒ regime artifact (aggravated on 6B by the measured London-share drift) |

## NOT_RUN register (explicit, this addendum)

- Trigger census, conditional returns, PnL, selection — NOT_RUN by law;
  census is a court-required descriptive input (court draft §c).
- BBO true spread / execution realism; exchange fee; FX official holiday
  calendar (A2 in flight; requirements §4); ATR(20d) numeric level.
- Gilt coupling 2025-2026 (local data ends 2024); consensus surprise
  vintages; ONS calendar; 6B↔6E relative value (cross-symbol, deferred).
- 6BM5 early-cluster + GCQ4 vendor-side adjudication (quarantined, §1).

— End 6B addendum. Every number traces to file:section or script:field;
missing evidence is NOT_RUN, never PASS.
