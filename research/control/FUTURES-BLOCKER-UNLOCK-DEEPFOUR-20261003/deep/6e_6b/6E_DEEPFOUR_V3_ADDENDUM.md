# 6E DEEP-FOUR V3 ADDENDUM — Euro FX Futures (EUR/USD), research v3 layer on dossier v2

- Task: `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003`, lane **B2-DEEP-6E6B**,
  generated 2026-10-03 (UTC).
- Class: PREP desk research on existing evidence + official public sources.
  **0 PnL, 0 scored runs, 0 signal selection, 0 ranking by any return
  statistic.** Every parameter carries **[PROVISIONAL]**. PB2 remains **HOLD**
  by Co-Owner ruling; nothing here reopens anything.
- Base evidence (read in full, errata applied):
  `research/control/FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/6E_DEEP_v2.md`
  (hereafter 6E_v2 §n, incl. ERRATA MAJOR-1/MAJOR-2 ledger §11);
  `research/control/FUTURES-DATACONTRACT-QUAL-V1/DATACONTRACT_QUALIFICATION.md`
  (DC §n); `PLAYBOOKS_DRAFT.md` r5 (PB §n);
  `SUMMARY_QUAL_ACTIONS.md` r6 (SQA §n). Analysis JSONs under
  `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/` cited as
  `script:field`.
- Taxonomy: **FACT** (primary source + date, URL where official) /
  **OBSERVED** (script + window) / **POSTULATED** (mechanism, unmeasured) /
  **NOT_RUN** (missing evidence never PASS). Arithmetic derived from measured
  inputs is tagged **DERIVED** with the inputs named.

---

## 1. Identity & registry

- 6E = CME Globex Euro FX futures; EUR 125,000 per contract; quoted USD per
  EUR; minTick 5e-05 = $6.25/tick [OBSERVED, DC §1.1 identity table; carried
  from 6E_v2 §1 header, origin v1 S1 identity]. Tick grid on outright closes:
  0 violations at 1e-9 fixed point vs 5e-05, full 2020-2026 window
  [OBSERVED, 6E_v2 §1 quality ledger].
- Registry: 90 contracts = 33 quarterly (HMUZ) + 57 serial; serials are dead
  books across the full 6.8y — 0.34% of outright volume (1.06M vs 309.8M
  contracts), median daily serial volume 140 contracts, zero serials with
  median ≥1k [OBSERVED, `6E_a3_term.json:serial_vs_quarterly`; 6E_v2 §2].
  Universe law: HMUZ-only.
- Symbol-plane contamination already filtered and disclosed: stray outright
  rows `6JZ7` (4,831 bars, AV1B file) and `SIJ5` (1,869 bars, AV1R file)
  removed by filter `^6E[A-Z]\d$`; calendar-spread instruments excluded from
  price panels (row share rising 6.4%→14.5% across eras is itself a
  microstructure fact, roll migration into spread books POSTULATED)
  [OBSERVED, `6E_a3_term.json:stray_symbol_rows`; 6E_v2 §1; DC §1.6].
- Statistics dataset (settlement/cleared-volume/OI) is 2023-10+ only; venue-OI
  joins require publication dedupe (the "2.000× CFTC convention" claim is
  RETRACTED as a publication-duplication artifact; deduped ratio 1.0000,
  150/156 weeks within ±0.2%) [OBSERVED, 6E_v2 §1 ERRATUM MAJOR-1].

## 2. PIT inventory (events + rates)

| source | available_at | status |
|---|---|---|
| ECB GC decisions (55 dates 2020-2026) | decision press release 14:15 CET/CEST, presser 14:45 (= 07:15 CT in 49/55; 08:15 CT in 6 spring DST-mismatch meetings) | **PASS_EVIDENCED — 55/55 machine-verified** (HTTP 200 + title + date-string each date; 19/19 MRO effective-date cross-check via ECB SDW; 2020-03-18 PEPP title variant disclosed) [FACT; lane D4-ECBVERIFY 2026-10-03, SQA §D4; DC §1.4]. URL scheme: ecb.europa.eu press releases (`ecb.mpYYMMDD~hash`) |
| FOMC statements (58 in panel 2020-2026) | "For release at …" in-document; 53 at 13:00 CT, remainder 2020 emergency timings | PASS_EVIDENCED, 58/58 with primary-source time proof from archived federalreserve.gov HTML on disk [FACT/OBSERVED, `6E_a4_events.json:fomc`; 6E_v2 §6] |
| Rates (FRED SOFR, ECB SDW €STR) | latest-vintage daily; ALFRED year-end vintages on disk (no 2025-12-31 vintage) | **NOT PIT-strict** — descriptive/CIP use only with mandatory vintage sensitivity (§7) [FACT; 6E_v2 §5 ERRATUM MAJOR-2; DC §1.4] |
| US 8:30 ET release-type decomposition (CPI/NFP/other) | — | NOT_RUN (no PIT US release calendar on disk; lane A5 is filling BLS, results not consumed here) |

## 3. Session structure by era / DST (LOCAL-CLOCK LAW)

- Session template: 17:00 CT (D-1) → 16:00 CT (D), 23h with 16:00–17:00 CT
  maintenance break; Sunday-evening open on 348/1,746 sessions (1.9% of front
  volume); median 1,600+ printed 1m bars/session ≈ full tradable day
  [OBSERVED, 6E_v2 §1/§2; DC §1.2].
- **London-local bucketing is proven, not assumed**: in US/EU DST-mismatch
  weeks (~March, late Oct–early Nov; 159,982 front bars) the CT-hour volume
  profile shifts by exactly one CT hour — h+02 share 6.79%→4.71%, h+03
  5.64%→6.80%, h+04 4.70%→5.71%, h+05 4.33%→5.03%; London-local
  08:00–12:00 carries 21.6% of volume vs 17.1% for fixed CT 02:00–05:00
  [OBSERVED, `6E_a2_sessions.json:dst_mismatch_effect`, `london_views`;
  6E_v2 §4]. **Binding law (DC §1.2): every session-bucketed feature must
  bucket by Europe/London local time, never fixed CT.**
- Information/volume split: ECB/US-data block 06:30–08:00 CT carries **15.6%
  of full-session realized variance on 12.5% of volume** (highest
  information-per-contract segment); London morning 16.6% RV; per-session
  median RV share London morning 17.6% (top) [OBSERVED,
  `6E_a2_sessions.json:rv_share_by_segment`, `median_session_rv_share_by_segment`;
  6E_v2 §4].
- Quietest hours (ex-break): 17:00–18:00 CT (1.004%) and 23:00–24:00 CT
  (1.015%) [OBSERVED, 6E_v2 §4, ERRATUM MINOR-3d].

## 4. Roll & calendar

- **Construction rule (frozen, DC §1.3): hold nearest HMUZ; roll at the close
  of the Friday of expiry week** — the session 1 trading day before the Monday
  last-trade. Volume crossover lands on exactly that Friday in **27/27 rolls**
  (2020-03→2026-09) [OBSERVED, `6E_a3_term.json:migration_median_new_volume_share`
  (d−3 Friday 87.1% → d−0 Monday 98.8%); 6E_v2 §5; DC §1.3].
- Expiry rule 80/80: last trade = 2nd exchange business day before 3rd
  Wednesday of delivery month, holiday set {MLK, Presidents, Juneteenth
  (2022+), Columbus Day, Good Friday, Veterans Day, weekend-observed shifts}
  — 80/80 expired contracts match last observed session, quarterlies AND
  serials [OBSERVED, `6E_cache/expiry_rule_check.json`; 6E_v2 §2].
- Declared-rule thin windows DISSOLVED: 0 sessions <10k and 0 <25k contracts
  in the final 14 sessions before delivery-month day-1, all 27 rolls
  [OBSERVED, `6E_a3_term.json:declared_rule_thin_windows`].
- Unadjusted-chain contamination: +0.80%…+2.18%/yr artificial upward drift
  (2020 +1.09, 2021 +0.80, 2022 +2.18, 2023 +1.93, 2024 +1.60, 2025 +2.10,
  2026 +1.16 through Sep) — back-adjustment mandatory; drift largest exactly
  in high-differential years [OBSERVED, `6E_a3_term.json:unadjusted_chain_embedding_per_year`;
  6E_v2 §5].
- **Calendar authority status: FX holidays official = NOT_RUN at write time**
  (DC §1.2/§2: 6E row "NOT_RUN official"; SQA §D3 covered ES only). Lane
  **A2-CMECAL-FX** is extracting the CME calendar for 6E/6B/6J/6A in this
  same task; its outputs are NOT consumed here. **REQUIREMENTS this addendum
  places on that lane** (requirements, not results): (i) holidays +
  early-closes per product-year from official CME sources (live or archived
  official; verbatim tables, no inference gap-fill); (ii) quarterly
  expiration-rule confirmation incl. the holiday set above (already 80/80
  bar-validated — the official layer must agree or the disagreement is
  itself evidence); (iii) each date labeled with source URL + capture date;
  (iv) uncertain dates ⇒ EXCLUDE/NOT_RUN (DC §1.2 law) — no inferred-pass.
  Until then: any calendar-dependent conditioning stays EXCLUDE/NOT_RUN.

## 5. Event anatomy (release-anchored, descriptive only)

- ECB decision minute (07:15/08:15 CT): median volume ×1.73 vs control
  Thursdays same minute; presser minute +30m ×1.46; pre-release minutes
  QUIETER than control (×0.88–0.94) [OBSERVED, `6E_a4_events.json:ecb`;
  6E_v2 §6]. ECB is a ×1.7 blip, NOT a ×17 FOMC-class event in the 6E book.
- FOMC statement minute 13:00 CT: median volume **×17.2** vs control
  Wednesdays; +5m ×9.96; +10m ×5.61; re-amplifies 13:40 CT ×8.8 — the single
  largest scheduled 1m-volume event of the 6E day [OBSERVED,
  `6E_a4_events.json:fomc`; 6E_v2 §6]. Control-Wednesday peak-minute mode
  13:59 CT (162 of ~340), secondary cluster 12:00–12:02 CT [OBSERVED,
  ERRATUM MINOR-4].
- 8:30 ET block: 07:30 CT median volume ×1.95 (277 vs 142 the minute
  before), range ×1.5, on 1,732/1,746 sessions — every weekday [OBSERVED,
  `6E_a2_sessions.json:us_830et_block`; 6E_v2 §4/§6]. This spike falls
  INSIDE the H-C/H-D trigger window (see §9) — hence the mandatory delay
  variants.

## 6. Coverage & data quality (2020-01 → 2026-09, 6.75y)

- 1,746 held-chain sessions; 3,054,311 outright 1m bars; three delivery eras
  (AV1B backfill2 / AV1R backfill / AV1T original) butt cleanly at
  2021-12-31→2022-01-03 and 2025-12-31→2026-01-02; 0 stale/zero-volume bars,
  0 duplicates, 0 negative prices, 0 tick-multiple violations, 1
  maintenance-break bar removed [OBSERVED, `6E_a6_dq.json:eras`; 6E_v2 §1].
- v1-window percentile placement: the v1 247-day window sits at the **6.8th
  percentile** of all same-length rolling vol windows 2020-2026 (v1 ann vol
  5.42%; rolling p05 5.66 / p50 7.19 / p95 9.94; drift 25.8th pct)
  [OBSERVED, `6E_a1_regimes.json:v1_window_placement`; 6E_v2 §3]. Any
  v1-calibrated cost/vol parameter is quiet-regime-calibrated.
- Contamination cleanups ALREADY APPLIED to this evidence base (do not
  re-apply): stray 6JZ7/SIJ5 rows filtered; spread instruments excluded;
  venue-OI dedupe law established (ERRATUM MAJOR-1); DST session-date
  mislabeling fixed in the v2 build (2,712 bars pre-fix); errata MAJOR-2,
  MINOR-3a..d, MINOR-4, MINOR-5, NOTE-6/7 applied in the dossier text
  [OBSERVED, 6E_v2 §11].

## 7. Spread / cost / margin — MODELED COST ONLY

- Spread: close-proxy **$18.75 half-turn** (= 3 ticks × $6.25), **high-biased**
  (close-proxy, not BBO; BBO NOT_RUN everywhere per DC §1.7) [OBSERVED, DC
  §1.7 cost table]. In bp of notional [DERIVED]: 0.00015/px × 1e4 →
  **1.21–1.57 bp/side** across the window price range 0.9552–1.2429 (1.36 bp
  at px 1.10; notional $137,500 at 1.10).
- Exchange fee 6E: **NOT_FETCHED** (DC §1.7; CME 403 at v2 time; lane A4-FEES
  is fetching public schedules in this same task — not consumed here).
  Commission IBKR $0.85/side known from v1 [FACT, DC §1.7]. Slippage =
  research assumption {1,2,3} ticks/side [PROVISIONAL, D1 via PB §4.4].
  ⇒ **any cost statement is MODELED COST, BLOCKED one more layer on the
  exchange fee; the words "measured cost"/"complete cost" are FORBIDDEN**
  (PB §4.4 law).
- Modeled round-trip arithmetic [DERIVED from above inputs]: spread 2.4–3.1 bp
  + slippage 0.9–2.7 bp + fees (commission ~0.012 bp/side at $137.5k notional
  + exchange NOT_FETCHED) ≈ **3.3–5.8 bp + exchange fee** round trip.
- Margin: ~$2.4–2.6k/contract initial (two public sources, <2% disagreement;
  account verification NOT_RUN) [FACT public-reference, DC §1.7].
- **CIP facts are INPUTS, not alpha** (owner law, DC §1.3): roll gaps 27/27
  positive (+36..+138 ticks, median +91 ticks ≈ +0.455% ≈ +$568.75/contract);
  sign agreement with SOFR−€STR differential **27/27 latest-vintage, 26/27
  PIT-as-of** — but the correlation is vintage-fragile: r = 0.91
  latest-vintage vs **r = −0.107 PIT-as-of** (ALFRED year-end vintages;
  no 2025 vintage exists) [OBSERVED, `6E_a3_term.json:gap_summary`
  (corr_gap_vs_cip 0.9097, median_gap_minus_cip_ticks 6.18); ERRATUM MAJOR-2].
  **Only the sign is robust. CIP-vintage sensitivity must be quantified
  (real-time SOFR source decision by owner) before ANY H2-family
  registration.**

## 8. Economic mechanism — POSTULATED, both directions

- **H-C (continuation)**: London-morning flow (London-local 08:00–12:00 =
  21.6% of volume; top per-session RV share 17.6%) discovers information
  while US liquidity is absent; a 1m close outside the London-morning range
  during 11:00–15:30 London encodes that discovery; arriving US liquidity
  (US-morning block 40.5% of volume at 08:00–11:00 CT) absorbs the same
  information and continues the move to the 16:00 CT close.
- **H-D (fade)**: the London range extension is an over-extension made in
  thin US-absent liquidity; arriving US liquidity absorbs and fades it
  (consistent with the mild multi-week mean-reversion VR(10)=0.927,
  VR(21)=0.887 measured on daily returns [OBSERVED, 6E_v2 §3]).
- Both mechanisms are POSTULATED; neither is tested here (conditional
  mean-return = NOT_RUN by law). The two cannot both survive — registering
  them as a pair is falsification-by-competitor (PB §0 row H-C/H-D).

## 9. Hypothesis pair — H-C vs H-D [PROVISIONAL, PB2 remains HOLD]

Mirrors PLAYBOOKS_DRAFT §2 (PB2) field table; nothing is registered; every
parameter [PROVISIONAL].

| field | specification [PROVISIONAL] |
|---|---|
| Universe | 6E held chain per DC §1.3 (Friday-of-expiry-week roll, 27/27 measured); 2020-01→2026-09 |
| Signal | R_lon = high−low of 08:00–11:00 Europe/London local (LOCAL-CLOCK LAW §3); trigger = first 1m close strictly outside R_lon during 11:00–15:30 London local |
| Entry | fill = open of next 1m bar after trigger; **mandatory delay variants +1 bar and +30m** (the 07:30 CT US-macro spike ×1.95 falls inside the trigger window — §5) |
| Stand-aside | (i) ECB GC days base-EXCLUDE (55/55 machine-verified D4; the verification blocker for the INCLUDE-sensitivity leg is dissolved, but INCLUDE remains a sensitivity leg only, runnable solely if the future registered cycle's spec says so — decision is Co-Owner's at reopen, not this lane's); (ii) FOMC days EXCLUDE (13:00 CT ×17.2 inside holding window); (iii) London-morning coverage <80% of expected bars EXCLUDE; (iv) warmup 60d; (v) calendar-uncertain dates EXCLUDE/NOT_RUN until A2-CMECAL-FX lands (§4) |
| TP | 2.0 × SL distance [PROVISIONAL R=2] |
| SL | 1.0 × ATR(20d, session range, median) [PROVISIONAL; ATR value NOT_RUN here] |
| Same-bar TP/SL | deterministic conservative: **SL priority** (no OHLC-order favoritism) [PROVISIONAL law, PB §4] |
| Time exit | 16:00 CT (flat before close — daytrade, no roll-carry) |
| Roll | DC §1.3 (§4 above); position flat before roll-session close |
| Sizing | risk 0.5% equity/trade [PROVISIONAL]; cap 5 contracts [PROVISIONAL capacity] |
| Cost | MODELED COST with exchange NOT_FETCHED disclosed (§7); slippage {1,2,3} ticks/side assumptions; spread close-proxy high-biased |
| Counter-hypothesis controls | clock/placebo (same-time unconditional random-sign entry, seeded, multi-seed before any claim); always-in-London-window baseline; see PB2_ANCESTRY_COURT_DRAFT.md §c for the power requirements |
| Kill rules | K1: effect survives ONLY with event-days INCLUDED ⇒ event-effect reclassification (belongs to a different family; needs surprise data NOT_RUN); K2: both H-C and H-D below Stage-A floor ⇒ family dead, no re-tparam; K3: 6E vs 6B opposite sign ⇒ no common-mechanism claim (symbol-specific at most); K4: sign flips in DST-mismatch weeks under CT bucketing ⇒ clock-law bug, not alpha; K5: rolling-window sign instability across 2020-22 vs 2023-26 ⇒ regime artifact |

## NOT_RUN register (explicit, this addendum)

- Trigger census (count of 1m closes outside R_lon per session), conditional
  returns, any PnL, any selection — NOT_RUN by law; trigger census is the
  court's first required descriptive input (see court draft §c).
- BBO true spread, execution realism — NOT_RUN (not purchased; DC §1.7).
- Exchange fee — NOT_FETCHED (A4 in flight).
- FX official holiday calendar — NOT_RUN (A2 in flight; requirements §4).
- ATR(20d) numeric level for SL — NOT_RUN in this lane.
- Per-era (delivery-era) session recomposition beyond v2's era table — NOT_RUN
  (v2 era table used as-is).

— End 6E addendum. Every number above traces to file:section or script:field;
missing evidence is NOT_RUN, never PASS.
