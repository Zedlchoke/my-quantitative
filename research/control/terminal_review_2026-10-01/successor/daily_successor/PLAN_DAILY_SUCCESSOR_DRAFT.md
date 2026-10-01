# PLAN_DAILY_SUCCESSOR_DRAFT — PC12A successor DAILY track (OI-6 preparation draft)

**STATUS HEADER — READ FIRST.** Preregistration preparation for a FUTURE
registered daily-track successor cycle. **DRAFT, NOT REGISTERED.** Nothing
in this file admits, raises, registers, freezes or scores anything. No
engine run, no S1 touch, no network, no ledger write, no orders, no keys.
**The binding blocker is OI-2: the IBKR Activity/Flex statement is ABSENT
(`~/.my-quantitative-data/ibkr_statement/` does not exist — measured
2026-10-01), so commission/swap/slippage = NOT_RUN_STATEMENT and NOTHING
scores, no after-cost PASS is readable, and no scored run may execute
until the statement lands** (owner law, `OI_DECISIONS_APPLIED.md` §OI-2).
Missing evidence is `NOT_RUN`, never inferred `PASS` (mission invariant).
This document is the ONE file written by this task (read-only elsewhere).

Binding admission state: `../OI_DECISIONS_APPLIED.md` (OI-1..OI-5,
M1-CAL=N1, M1-D). Inputs: `../DAILY_ADMISSION_MATRIX.md` (incl REV-3
DELTA), `../SUCCESSOR_PLAN_DRAFT.md` (§3 protocol skeleton, §7b quote-CCY
law), `../RULE_SLATE.md` (M1-track hypotheses — **deliberately NOT
imported here**; the two tracks stay separate per the dispatch),
`…/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/eligibility/PORTFOLIO_ELIGIBILITY_1200.tsv`
(+ `ibkr_capability_probe_2026-09-30/LEG_RESOLUTION_MATRIX.tsv`), corpus
`…/FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/*.md`, engine/journal law
`…/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/journal/JOURNAL_SCHEMA.md` +
`FILL_ACCOUNTING_SPEC.md`, policy `…/policy/PASS_BARS_V2.md`.

---

## 0. Binding admission state (executed owner decisions — restated as law for this plan)

| id | executed decision | consequence for the daily slate |
|---|---|---|
| **OI-1** | IBKR HMDS D1 BID/ASK = panel-of-record for NZDUSD/USDCHF/XAUUSD/XAGUSD; **only closed bars from the NEXT business day**; label `LAG_DECLARED_BY_OWNER (DECLARED, NOT MEASURED — historical lag not measured; point-1/point-2 presence evidence on file)`; σ tripwire FROZEN 1σ/5σ/0.5σ (never loosened) | Feature `available_time` = next business day for every OI-1 panel input; point-2 presence class `PERSISTENCE_PRESENCE_MEASURED_2pts` (REV-3), value-stability still NOT_MEASURED |
| **OI-2** | Statement ABSENT (measured) | Costs NOT_RUN_STATEMENT ⇒ **NO after-cost PASS, NO scored run, registration of the scored cycle GATED** |
| **OI-3** | XAU archive pinned + sha256 verified (`49c2684e…`, full hash in OI-3) | XAU-as-SIGNAL admissible (basis MEASURED vs pinned archive); XAU-as-VEHICLE still cost-gated by OI-2 |
| **OI-4** | XAG NOT_RUN (skeptic-required independent archive absent; no SLV proxy, no purchase) | Anything XAG-dependent stays out (§1.3) |
| **OI-5** | RBRTE/RWTC/RNGWHHD = DAILY SIGNAL-ONLY inputs, 1bd declared serving, SINGLE-SOURCE label, never fill prices; energy execution FLAT/NOT_RUN; AECO/TTF rows NOT_RUN | EIA legs admissible as FX-signal inputs only; no energy vehicle anywhere |
| **M1-CAL/M1-D** | S1 sealed tail untouched; USDCAD/AUDUSD intraday NOT_RUN this cycle, **daily-clock candidates judged separately (here)** | AUDUSD/USDCAD inputs enter only as D1 closes aggregated from their frozen H1 panels (declared law, §1.1-I) |

Signal-side admissible today: NZDUSD, USDCHF (OI-1 panels), XAU (OI-3),
EIA dailies (OI-5) + the pre-evidenced PC12A-lineage panels
(EURUSD/GBPUSD/USDJPY M1; AUDUSD/USDCAD H1-staged) and VIX (evidenced
G-PIT-V2 per Matrix B). Executable vehicles: **FX-spot pairs only**.

---

## 1. LEG SLATE — scoped to ACTUALLY admitted legs

Candidate pool per dispatch: Matrix B's 7 NEW-DAILY-CANDIDATE rows
(`LEG_RESOLUTION_MATRIX.tsv` lines 34/63/83/99/149/163/167) + the 2
EIA-signal legs (USDJPY-S065 line 65, USDCAD-S090 line 257). Corpus rule
texts were READ for all nine (`symbols/*.md`, quoted verbatim below;
Vietnamese corpus text quoted as written — glosses are mine and marked).
**Result: 7 legs admitted to the draft slate; 2 legs PARKED by triage
discipline because their corpus rule text is not rule-ready on reading**
(§1.2). Data-addressability (Matrix B "ADMITTABLE-AS") is a data verdict,
not a rule-readiness verdict — no inference upgrades anywhere.

### 1.1 Admitted legs (the daily slate book)

| # | sleeve_id | corpus_gid | family / mech_key | traded vehicle (clock=Daily) | required signal inputs (admission basis each) | outcome_exposed_label (eligibility TSV) | cluster_id draft |
|---|---|---|---|---|---|---|---|
| 1 | **DS-01** | AUDUSD-S081 | I-STATARB / pairs_zscore_band | **AUDUSD FX-spot + NZDUSD FX-spot, 1:1 two-leg** (AUDUSD: evidenced FX-spot, H1-docket ALREADY-RUNNABLE class; NZDUSD: OI-1 panel, conId 39453441, five-major entitlement caveat carried) | AUDUSD D1 closes (I-AUD) + NZDUSD D1 closes (I-NZD) | PRIOR_NOT_SCORED (known_negative_prior NO) | statarb_pairs_audnzd |
| 2 | **DS-02** | USDJPY-S063 | G-XASSET / safehaven_convergence | **USDJPY FX-spot** (PC12A-traded, M1 BID/ASK panel) — gold is NOT the traded vehicle | USDJPY D1 (I-JPY) + XAUUSD D1 close (I-XAU: OI-1 panel + OI-3 pinned archive) + VIX (I-VIX: evidenced G-PIT-V2) | PRIOR_NOT_SCORED (NO) | xasset_safehaven_goldjpy |
| 3 | **DS-03** | USDJPY-S065 | G-XASSET / lng_import_exposure | **USDJPY FX-spot** | RNGWHHD D1 (I-EIA-NG: OI-5 signal-only, 1bd serving) + RBRTE D1 (I-EIA-BR: OI-5) + USDJPY D1 (I-JPY) | PRIOR_NOT_SCORED (NO) | xasset_energy_lng |
| 4 | **DS-04** | USDJPY-S083 | I-STATARB / cross_basket_residual | **USDJPY FX-spot** | USDJPY D1 + 6 JPY-cross D1 closes: NZDJPY/CHFJPY synthetic = NZDUSD/USDCHF × USDJPY (I-NZD/I-CHF OI-1; declared in Matrix B) ; EURJPY/AUDJPY/CADJPY/GBPJPY synthetic from majors (I-EUR/I-AUD/I-CAD/I-GBP — declared construction, §1.1 notes) | PRIOR_NOT_SCORED (NO) | statarb_jpy_basket |
| 5 | **DS-05** | EURUSD-S006 | A-TREND / xsect_antiusd_rank | **EURUSD FX-spot** (PC12A-traded) | 7 USD-pair D1 closes: EURUSD/GBPUSD/USDJPY (I-EUR/I-GBP/I-JPY) + AUDUSD/USDCAD (I-AUD/I-CAD) + NZDUSD/USDCHF (I-NZD/I-CHF OI-1) | FAMILY_HISTORY_NEGATIVE (YES) | trend_xsect_antiusd |
| 6 | **DS-06** | EURUSD-S061 | G-XASSET / basket_residual_fade | **EURUSD FX-spot** | 7 USD-pair D1 closes (same basis as DS-05) | FAMILY_HISTORY_NEGATIVE (YES) | statarb_usdbasket_residual (shared with DS-07) |
| 7 | **DS-07** | EURUSD-S085 | I-STATARB / basket_residual_fade | **EURUSD FX-spot** | 7 USD-pair D1 closes (same basis as DS-05) | FAMILY_HISTORY_NEGATIVE (YES) | statarb_usdbasket_residual (shared with DS-06) |

**Input basis classes (cited once, referenced by tag):**

- **I-NZD** — NZDUSD IBKR HMDS D1 BID/ASK panel-of-record, 1553 days/side
  2020-10-02→2026-09-30, aggregate sha `c681402b…`, DV-verified, 0 holes
  >5d; spread_daily MEASURED p50 0.88 / p90 18.65 / max 239.07 bps;
  panel σ 64.64 bps (**OI-1**; `IDENTITY_FREEZE_2026-09-30.json@87e65f00`).
- **I-CHF** — USDCHF same class, sha `7fbd3a80…`, spread 4.51/16.02/216.10
  bps, σ 49.62 bps; ERRATUM-1 (FRED DEXSZUS no inversion) carried (**OI-1**).
- **I-XAU** — XAUUSD D1 close, SIGNAL-ONLY: IBKR panel sha `02445884…`
  (1544 d/side) cross-checked against the **OI-3 pinned** TD archive
  (`…/forex-ng6/…/staging/XAUUSD_1day_full.json`, sha256 verified
  `49c2684ebb045302acf0c452b5aa9a3b96dff73eb3bc6f5add1801d6817fb33c`):
  overlap n=1531, abs p50 3.2462 / p95 26.5142 bps, signed mean +0.3359
  USD; tripwire 1σ/5σ/0.5σ FROZEN, XAU σ computed at registration freeze.
- **I-EIA-NG / I-EIA-BR / I-EIA-WT** — RNGWHHD (1496d) / RBRTE (1512d) /
  RWTC (1494d), span-complete 2020-10-01→2026-09-29, sha-pinned
  (`MANIFEST_RAW.json@cbae7556`), 1bd serving measured; label
  `SINGLE-SOURCE-COMPILATION, DUAL-CHANNEL-RETRIEVAL-CONFIRMED`;
  **never fill prices** (**OI-5**).
- **I-EUR / I-GBP / I-JPY** — EURUSD/GBPUSD/USDJPY evidenced M1 BID/ASK
  panels (PC12A poolB lineage, spans from 2021-01-01, live collector
  active) consumed at Daily clock via a **declared D1-close aggregation**
  (17:00 ET close; the aggregation law is a registration declaration, not
  a measurement). Not OI-covered — labeled EVIDENCED-PANEL/DECLARED-AGG.
- **I-AUD / I-CAD** — AUDUSD/USDCAD frozen read-only H1 panels
  (2021-01-03→2026-06-30, H1 docket C §1.1) consumed via the same declared
  D1-close aggregation (M1-D: intraday NOT_RUN; daily use lawful).
  **Calendar consequence:** these inputs end 2026-06-30 (§2.4).
- **I-VIX** — VIX, "evidenced G-PIT-V2" per Matrix B row 2; span/availability
  re-verification against the daily calendar is a registration-gate item
  (not re-measured here — no inference).

**Per-leg corpus rule (verbatim) + param-source + registration decisions.**
Entry/exit parameters are quoted verbatim from the symbol files;
`PARAM-GAP` items are parameters the corpus text does not quantify — each
carries its param-source (owner-frozen declaration or LEARN grid, §3) and
none is silently defaulted.

**DS-01 — AUDUSD-S081** (`symbols/AUDUSD.md` §Family I, S81):
> "Signal: AUDNZD z-score(60d) > ±2 & half-life OU <20 ngày · Trade: long
> AUDUSD + short NZDUSD size 1:1 khi z>2 (đóng khi z=0.3), stop z>3 · …
> giới hạn hold bằng thời gian 2×half-life"

- Params present verbatim: z window 60d; entry |z|>±2 with OU half-life
  <20d filter (mandatory — the family's own 2026 RBA/RBNZ divergence
  break risk); exit z=0.3; stop z>3; hold cap 2×half-life; legs 1:1.
- **Direction disclosure (registration decision DS-01-a):** the corpus
  hypothesis is mean-reversion ("AUDNZD neo về mean dài hạn") while the
  trade line literally reads long-AUD/short-NZD "khi z>2" — the pro-z
  side. The sign convention of z and the fade direction must be resolved
  BY THE OWNER at registration (frozen, either reading); this draft does
  not pick one. PARAM-GAP: OU estimation window (declared at
  registration).
- PARAM-GAP: ATR none needed (z-based stops). Coupling disclosure (registration decision DS-01-b): the corpus entry condition `Coupling: S35 hai policy path hội tụ mới vào` (AUDUSD.md S81) cannot fire — S35 is not in this cohort and its inputs are unevidenced here; default = run ungated with the omission disclosed (owner may name a source or park at registration).
Rule-ready otherwise modulo DS-01-a/DS-01-b.

**DS-02 — USDJPY-S063** (`symbols/USDJPY.md` S63):
> "Signal: VIX Δ5 ngày > +4 và z(USDJPY ret + β×gold ret)>1.5σ. · Trade:
> short USDJPY beta-weighted với long gold đã có (hedge completion), stop
> 1×ATR, exit khi VIX<20."

- Params verbatim: VIX 5d change > +4; residual z > 1.5σ; stop 1×ATR;
  exit VIX<20.
- **Re-scope declaration (registration decision DS-02-a):** "với long
  gold đã có (hedge completion)" presumes an existing long-gold position;
  under the admission law gold is SIGNAL-ONLY here, so the executable leg
  is short USDJPY beta-weighted — the re-scope is frozen at registration.
- PARAM-GAP (declared, no grid): β estimation window and z standardization
  window (family convention: rolling 60d — `symbols/USDJPY.md` S61 uses
  "rolling 60 ngày"; DECLARED, labeled as convention not corpus); ATR
  window (D1 ATR-14 convention DECLARED). Coupling "gold trend phải đang
  dương" is advisory context — inclusion/exclusion frozen at registration.

**DS-03 — USDJPY-S065** (`symbols/USDJPY.md` S65):
> "Signal: NATGAS 10d ret > +15% (breaking structure) khi Brent flat. ·
> Trade: long USDJPY 5 phiên, stop 1×ATR. · Risk: NATGAS HH–JKM decouple
> (US export capacity)… · Coupling: chỉ khi Brent flat (để tách channel —
> nếu Brent cùng chạy thì là S64)."

- Params verbatim: NATGAS 10d return > +15%; Brent-flat channel filter
  (part of the entry law per the coupling line); hold 5 sessions; stop
  1×ATR. The HH-as-JKM-proxy bias is disclosed **in-rule** (Risk clause).
- PARAM-GAP → **LEARN GRID (G1)**: "Brent flat" is unquantified in the
  corpus. Grid (≤3 nodes, §3): A no filter (off) · B |RBRTE 10d ret| <
  3% · C < 5%. PARAM-GAP declared: ATR window (D1 ATR-14 convention).
- EIA inputs under OI-5: 1bd declared serving ⇒ T+1-open decisions only
  (a 10d return on bars through T decides at T+1 open) — never fills.

**DS-04 — USDJPY-S083** (`symbols/USDJPY.md` S83):
> "Signal: |z|>2 của USDJPY residual vs basket PCA fit. · Trade: fade
> residual 1 tuần, stop z>3. · … · Data: 7 cặp OHLC. · Coupling: không
> chạy khi US event tuần đó (FOMC/NFP)."

- Params verbatim: |z|>2 entry; fade 1 week; stop z>3; inputs 7 pairs.
- Synthetic-cross declaration (registration decision DS-04-a):
  NZDJPY = NZDUSD×USDJPY and CHFJPY = USDJPY/USDCHF are declared by
  Matrix B; **this plan extends the same declared construction** to
  EURJPY = EURUSD×USDJPY, AUDJPY = AUDUSD×USDJPY, CADJPY = USDJPY/USDCAD,
  GBPJPY = GBPUSD×USDJPY (triangle arithmetic on D1 closes of evidenced /
  OI-1 panels) — a declaration to freeze at registration (skeptic item
  §8-a). PARAM-GAP declared: PCA fit window + z window.
- Coupling veto "không chạy khi US event (FOMC/NFP)" needs a named
  events-calendar source not on file — registration decision DS-04-b:
  include with an owner-named calendar, or run ungated with the omission
  disclosed (default in this draft: run ungated + disclosed).

**DS-05 — EURUSD-S006** (`symbols/EURUSD.md` S6):
> "Signal: rank 20d return của {EUR,GBP,AUD,NZD,CHF,JPY,CAD} vs USD; vào
> EURUSD long chỉ khi EUR rank 1–2 · Trade: hold tới khi rơi khỏi top-3,
> stop 2×ATR · … · Coupling: rank nhất quán 2 tuần liên tiếp mới vào."

- Params verbatim: 20d cross-sectional return rank over the 7 currencies;
  long-only entry at EUR rank 1–2; the 2-consecutive-week rank
  consistency IS part of the entry law (corpus coupling line); exit on
  dropping out of top-3; stop 2×ATR.
- PARAM-GAP declared: ATR window (D1 ATR-14 convention).

**DS-06 — EURUSD-S061** (`symbols/EURUSD.md` S61):
> "Signal: regress daily returns lên basket {GBPUSD, AUDUSD, NZDUSD,
> −USDJPY, −USDCAD, −USDCHF}; residual z(20d)>2 · Trade: fade residual,
> target z=0.3, stop z=3, holding ≤10 phiên."

- Params verbatim: basket regression with stated signs; residual z(20d)>2
  entry; target z=0.3; stop z=3; hold ≤10 sessions.
- PARAM-GAP declared: regression estimation window (rolling convention).
- Coupling "BTP-Bund không nở mạnh (fragmentation gate)" requires BTP-Bund
  daily — NOT on file. Registration decision DS-06-a: the gate cannot
  fire; default = run ungated with the omission disclosed and
  fragmentation-break carried as a named anti-hypothesis failure mode
  (owner may instead park the leg or name a source at registration).

**DS-07 — EURUSD-S085** (`symbols/EURUSD.md` S85):
> "Signal: Kalman residual vượt adaptive ±2.5σ · Trade: fade residual với
> holding theo half-life Kalman implicit · … · Data: 7 pairs, Kalman
> engine."

- Params verbatim: adaptive ±2.5σ band on the Kalman residual; holding by
  the filter's implicit half-life. **No stop-loss exists in the corpus
  text — disclosed as-is** (exit = half-life holding + band re-entry);
  docket risk clause names filter-lag-at-break as the failure mode.
- PARAM-GAP → **LEARN GRID (G2)**: band multiplier nodes {2.0σ · 2.5σ
  (corpus default) · 3.0σ}; Kalman hyperparameters (state/obs noise)
  DECLARED at registration. Same fragmentation-gate decision as DS-06
  (DS-06-a applies mutatis mutandis).

**Cluster note (draft):** DS-06 and DS-07 share the identical 7-pair
anti-USD basket input and the same fade mechanism — one shared
cluster_id, cluster-exposure caps apply, and P8L (§4) must show the slate
does not hinge on this single cluster (skeptic item §8-d).

### 1.2 PARKED by triage discipline (corpus text not rule-ready; no inference upgrades)

| leg | corpus text read | exact park reason | re-entry path |
|---|---|---|---|
| **AUDUSD-S100** (`symbols/AUDUSD.md` S100) | "Signal: ba điều kiện trên thoả trong 2 ngày · Trade: thoát longs theo rule cứng; optional short AUDUSD scalp với stop siết, không average · … đây là capital-preservation module · Coupling: là kill-switch của S31/S32/S63" | **NOT_RULE_READY_STANDALONE**: the mandatory action is exiting the longs of host rules (S31/S32/S63) that are NOT in this cohort; the short-AUD scalp branch is optional and unparameterized ("stop siết" — no distance, no size). A standalone daily leg cannot be scored without inventing parameters. | Registered OVERLAY amendment once a host AUD-long book exists (e.g. over DS-01's AUD leg), with quantified scalp params owner-frozen |
| **USDCAD-S090** (`symbols/USDCAD.md` S90) | "Signal: CUSUM break test trên ratio. · Trade: re-weight petro factor trong S88. … · Data: 2 futures D." | **NOT_RULE_READY_STANDALONE**: (i) the action is a meta re-weight of another sleeve's factor (S88 multi-factor fair-value model — not in this cohort), not a position with entry/exit; (ii) the corpus specifies **futures** daily data ("2 futures D") — substituting EIA spot dailies for futures in the CUSUM ratio is a channel swap requiring an owner declaration that re-freezes the rule (no inference). | Owner-registered re-specification: define the standalone position law (direction/size/exit off the CUSUM break) + declare EIA-spot-for-futures signal substitution, or wait for a certified chain (energy execution stays FLAT per OI-5) |

### 1.3 EXCLUDED by binding admission state (exact NOT_RUN reason each)

| leg | excluded because (exact reason) |
|---|---|
| **EURUSD-S063** (TTF−Henry Hub EA shock) | TTF leg is NOT EIA and not IBKR — needs an owner-named TTF source; OI-5 executed state: **AECO/TTF corpus rows NOT_RUN** |
| **USDCAD-S062 / S081 / S089** (USDCAD–WTI pairs trades) | traded vehicle includes a **short-WTI execution leg** — WTI signal measured (RWTC) but energy execution **FLAT/NOT_RUN under OI-5** (no certified chain) ⇒ SIGNAL-ONLY / EXECUTION-BLOCKED |
| **USDCAD-S005 / S098** (CL1–CL6 curve, 6M curve slope) | require the **futures curve**, which a spot daily is not — BLOCKED on the chain (OI-5 energy execution FLAT) |
| **USDCAD-S084** (Brent lead-lag minute scale) | needs **intraday** energy — daily archive structurally insufficient; USDCAD intraday also NOT_RUN (M1-D) |
| **USDCAD-S065** (NATGAS AECO spill) | **AECO** is a non-IBKR, non-EIA hub — owner-named source absent; OI-5: AECO rows NOT_RUN |
| **XAUUSD-S063 / XAGUSD-S081** (gold-silver ratio bands / GSR z reversion) | **XAG-dependent** — OI-4 executed fallback: XAGUSD remains NOT_RUN (PIT-FAIL stands; no independent spot archive; no SLV proxy) |
| **NZDUSD-S068 / EURUSD-S058 / USDCAD-S031** (dairy-oil ToT, OPEC+ event, carry+oil hedge) | macro-PIT inputs unevidenced (`NEEDS_MACRO_PIT_UNEVIDENCED` in the frozen eligibility row) — the oil leg alone is not the rule |

No XAG or energy-execution dependency exists anywhere in §1.1 (verified
per leg above; Matrix A: "zero triage rows need only XAGUSD").

---

## 2. Fold calendar (never-scored daily calendar; exact dates)

### 2.1 Freshness statement (and its limit, stated honestly)

The daily calendar is FRESH as a scored-cell space: **no scored identity
in any prior cycle ever consumed these D1 panels at a Daily clock** — the
PC12A scored folds were M1-clock corpus legs on EURUSD/GBPUSD/USDJPY
(2021-01-08→2025-12-26 EXPOSED), a different identity set. Declared
limitation carried, not hidden: (i) the underlying higher-clock panels of
EURUSD/GBPUSD/USDJPY/AUDUSD/USDCAD WERE part of the PC12A exposed window,
so legs consuming majors-derived D1 closes (DS-01/02/03/04/05/06/07 — all
of them) are labeled **EXPOSURE-ADJACENT** at the input level; (ii) the
corpus text itself was written 2026-09-28 with PC12A forensics knowledge —
mitigated by frozen verbatim rule text, frozen anti-hypotheses, negative-
close-first law and the PRIOR_NOT_SCORED / FAMILY_HISTORY_NEGATIVE labels
already in the frozen eligibility rows. The NZDUSD/USDCHF/XAUUSD/EIA
inputs are untouched by any scored run at any date.

### 2.2 Arithmetic (venv python, 2026-10-01)

- Master daily calendar: **2020-10-02 → 2026-09-30** = 2,190 days =
  312.857 weeks (≈313w; NZDUSD/USDCHF panels 1,553 d/side; XAU 1,544;
  EIA 2020-10-01→2026-09-29).
- ≥6×26w floor requires ≥156w of test folds; the calendar supports 8×26w
  (208w) after warmup + LEARN + embargo — proposed below.
- **WARMUP 52w = 364d: 2020-10-02 → 2021-09-30.** No decisions scored or
  learned; indicator burn-in (max corpus lookback 60d — margin huge);
  majors-derived inputs become available 2021-01-04, inside warmup, so no
  fold is affected.
- **LEARN = 51w = 357d: 2021-10-01 → 2022-09-22** (= 19.55% of the
  post-warmup 260.857w). Exactly 20% would be 52.17w; **52 whole weeks
  overshoot the calendar by 1 day** (fold 8 would end 2026-10-01 >
  2026-09-30) — the rounding-DOWN-to-whole-weeks law is stated here and
  frozen at registration. *Deviation disclosure:* `SUCCESSOR_PLAN_DRAFT`
  §3.2 words the DAILY-track LEARN as "the first 20% of the … calendar
  (2020-10-02→)"; this plan instead places the 52w warmup BEFORE LEARN
  (the dispatch's own ordering) so that LEARN data is post-warmup and
  input-complete throughout — the alternative (warmup inside LEARN)
  leaves only ~10.4w of usable learning data. Owner freezes the choice at
  registration; the skeptic must attack it (§8-b).
- **EMBARGO 1w: 2022-09-23 → 2022-09-29** (LEARN end + 7d; no selection
  contact with post-LEARN data before freeze — inherited law).
- **8 × 26w test folds (182d each), fold-edge force-flat inherited:**

| fold | start | end |
|---|---|---|
| 1 | 2022-09-30 | 2023-03-30 |
| 2 | 2023-03-31 | 2023-09-28 |
| 3 | 2023-09-29 | 2024-03-28 |
| 4 | 2024-03-29 | 2024-09-26 |
| 5 | 2024-09-27 | 2025-03-27 |
| 6 | 2025-03-28 | 2025-09-25 |
| 7 | 2025-09-26 | 2026-03-26 |
| 8 | 2026-03-27 | 2026-09-24 |

- Unscored tail: 2026-09-25 → 2026-09-30 (6d) stays UNSCORED reserve.
  8 folds ≥ 6-fold calendar floor (E-Law 5). CHECK: 364 + 357 + 7 + 8×182
  = 2,184 ≤ 2,190. ✓

### 2.3 Per-leg calendar notes

All seven legs' inputs exist from 2021-01-04 (≤ warmup end) — no fold is
input-starved at the start. VIX span re-verification is a registration
gate item (§7).

### 2.4 The AUD/CA end-of-panel boundary (registration prerequisite)

AUDUSD/USDCAD H1 panels end **2026-06-30**; fold 8 runs to 2026-09-24.
Five legs (DS-01, DS-04, DS-05, DS-06, DS-07) consume AUD/CA-derived
inputs. **D1 INPUT-COMPLETION ACTION (proposed registration
prerequisite, lawful and reversible):** extend AUDUSD/USDCAD with an IBKR
HMDS D1 BID/ASK pull 2026-07-01→2026-09-30 (same method as the executed
7-asset probe; sha-frozen like the others) + extend the majors' D1
aggregation through ≥2026-09-24 via the active live collector. Fallback
if declined: fold 8 is typed `NOT_RUN_INPUT_END` per affected leg from
2026-07-01 (fold 8 then counts fully only for DS-02/DS-03) — typed, never
silently truncated.

---

# 2.1-addendum (skeptic-recommended)
AUDUSD/USDCAD H1 panels were staged/TRAIN-only in PC12A (never scored); their derived daily inputs are labeled EXPOSURE-ADJACENT conservatively.
The ×2.0 reporting-tier deferral is a registered deviation from PB2 P6b (non-governing), recorded at registration.

## 3. Trial budget (draft; zero rows exist today — OI-2 blocker)

Counting law inherited (PB2 E-Law 8 / CAM §6): baseline IDENTITIES on the
scored line; the random battery is ONE identity executed as ≤128 seeded
sub-runs on its own disclosed line; stress-tier and LORO re-runs are
identity-classified. B0 FLAT is one identity with **zero journal rows**
(flat by construction — PB2 §1 B0 law).

| identity | count | folds | rows |
|---|---|---|---|
| **SLATE** — the 7-leg daily book (DS-01..07) | 1 | 8 | 8 |
| **B0 FLAT** | 1 | 0 | 0 |
| **B1S ALWAYS-ON WALL** (same legs, eligibility pinned ON; **designated primary baseline**, §4) | 1 | 8 | 8 |
| **B2 EQUAL_WEIGHT** (PB2 §1 B2 corrected semantics) | 1 | 8 | 8 |
| **B3 BEST_SINGLE** (PB2 §1 B3; obj_B3 = DSR on LEARN decision-cycle NET returns at ×2.0 kernel, LEARN-side selection, tie-break chain frozen) | 1 | 8 | 8 |
| **C2 random dwell battery** — ≥100 seeds (≤128), duty+flip matched to the slate's realized LEARN per-leg entry path; ONE identity, seeds on their own line | 1 | 8 | 8 (+ seed sub-run line) |
| **LORO leave-one-leg-out** × {DS-01..DS-07} | 7 | 8 | 56 |
| **×1.5 stress SLATE** (governing) | 1 | 8 | 8 |
| **×1.5 stress B1S** (governing) | 1 | 8 | 8 |
| **subtotal (scored)** | **15** | | **112** |
| LEARN-side grid rows: G1 (DS-03 Brent-flat) + G2 (DS-07 Kalman band), 3 nodes each, ONE LEARN pass (LEARN is a single window; RULE_SLATE §4's split/fallback variants are M1-track constructs and do not apply at this calendar) | | | 6 |
| **total** | **15 identities** | | **118 rows** |

- **Caps:** 15 ≤ 24 identities ✓; 118 ≤ 120 rows ✓ (headroom: 9
  identities, 2 rows).
- **×2.0 REPORTING TIER DEFERRED — justification:** PB2 P6b semantics are
  inherited, but one more 8-fold identity needs 8 rows and only 2 remain;
  the ×1.5 GOVERNING tier runs on BOTH arms (the bar that gates PASS),
  every number carries `NET_DEFAULT_COST`/PROVISIONAL labels until OI-2,
  and the cost-dominated sign-flip disclosure is still evaluated at ×1.5
  (net sign flip on either arm ⇒ `POLICY_COST_DOMINATED` disclosure). A
  registered amendment before fold-1 execution may swap budget
  composition — never mid-cycle.
- LEARN grids: selection objective frozen (maximize net improvement vs
  B1S on LEARN subject to maxDD not worse; tie-break fewer deferred
  decisions, then lexicographic sleeve_id); floor failure ⇒ grid
  collapses to the frozen default, typed `NOT_RUN_GRID_THIN` — never
  silently widened. DS-02/04/05/06 param gaps are owner DECLARATIONS, not
  grids (§1.1).
- Inherited floors stay binding: campaign 20/3/100 per leg per fold (CAM
  §3) + battery ≥100 seeds; floor failure ⇒ typed `NOT_RUN_THIN`.
- Ledger rows estimate today: **0** (nothing run; OI-2 blocker).

---

## 4. Controls & PASS bars (all NOT_RUN until OI-2 + registration)

**Inheritance (wholesale).** PASS_BARS_V2 law: AND-only semantics (net
PnL strictly higher AND maxDD strictly lower vs the named baseline, ties
fail — E-Law 4), pooled test folds, E-Laws 1–8 (quantities; fold-edge
force-flat disclosure; comparability; strictness; ≥6-fold calendar floor
— met with 8; book-integrity precondition; ordering; budget counting).

1. **PRIMARY BAR — the always-on wall (seven-deaths lesson).**
   `netPnL(SLATE) > netPnL(B1S)` AND `maxDD(SLATE) < maxDD(B1S)`,
   pooled over folds 1–8, strict both legs. B1S is the same 7 legs with
   eligibility pinned ON — the baseline class that killed PC12A is the
   designated primary, not a secondary control.
2. **P1-B0 sub-bar:** netPnL(SLATE) > 0 pooled (absolute net edge after
   all costs).
3. **Stress:** the AND-pair must also hold at cost tier ×1.5 (governing,
   both arms re-priced; FILL_ACCOUNTING_SPEC §5); ×2.0 reporting tier
   deferred with justification (§3).
4. **Battery bar:** SLATE beats the C2 random dwell-matched battery per
   PB2 §4 clause semantics (cadence-as-value guard).
5. **P-MW (missed-winners bar, per leg via LORO).** For each DS-r:
   `Δ(r) = netPnL(SLATE) − netPnL(SLATE ∖ r) > 0` pooled, strict, with
   the mandatory two-sided per-fold table (n added; Σ added-winner net;
   Σ added-loser net; largest single winner as share of the loser side).
   Reporting one side only ⇒ `NOT_RUN_INTEGRITY` (STOP-3 class).
6. **P-FA (false-admission mirror).** Any leg whose own realized book
   nets ≤ 0 pooled while the slate passes ⇒ false-carriage disclosure;
   single-trade concentration ≥ 50% of any leg's (or the admitted set's)
   gain carries a mandatory concentration disclosure.
7. **P7 fold concentration:** ≤ 50% pooled PnL share per fold / ≤ 2×
   pro-rata DD share.
8. **P8L leave-one-leg:** exactly-one-break ⇒ `POLICY_ONE_LEG_CARRIER`;
   the shared DS-06/DS-07 cluster makes this load-bearing (§1.1 cluster
   note).
9. Floors (§3) unmet ⇒ typed `NOT_RUN_THIN`; negative close is
   first-class (seventh-death prior stands).

---

## 5. Cost law (NOTHING SCORES until OI-2 lands)

**Owner law (OI-2, binding):** the statement is ABSENT ⇒ commission /
swap / slippage are NOT_RUN_STATEMENT ⇒ no after-cost PASS, no scored
run, no GO. Everything in this section is kernel DESIGN; every number it
would produce is `PROVISIONAL_PENDING_COST_AUTHORITY` /
`NET_DEFAULT_COST` until the export lands in
`~/.my-quantitative-data/ibkr_statement/` (machine-local, never in
chat/git) and is frozen into the kernel.

**Measured cells that exist for the daily pairs:**

| pair (role here) | measured basis | values |
|---|---|---|
| NZDUSD (vehicle, DS-01) | IBKR D1 daily-band spread, 1553d, identity-frozen | p50 0.88 / p90 18.65 / max 239.07 bps |
| USDCHF (signal input only) | same class | p50 4.51 / p90 16.02 / max 216.10 bps |
| XAUUSD (signal input only) | same class (n=1543; one crossed-book day excluded by a≥b rule, disclosed) | p50 5.52 / p90 18.61 / max 74.17 bps |
| EURUSD / USDJPY / GBPUSD (vehicle/inputs) | PC12A M1 window cells C1/C2/C3 (COST_AUTHORITY_TABLE + Lane-D corrected cells) — **roll/reopen window cells are N/A at the Daily clock** (no 21:00–22:00Z window fills, no Sunday-reopen modeling: D1 decisions fill at the next D1 bar open) | e.g. C1 Fri-20:00 p50/p90 pips: EURUSD 0.3/0.5 · GBPUSD 0.8/1.3 · USDJPY 0.5/0.9 |
| AUDUSD / USDCAD (inputs; AUD vehicle in DS-01) | H1-clock cells per H1 docket C §1.4 | e.g. AUDUSD C1 1.0/1.3 pips |

**Daily-band spread stats for EURUSD/USDJPY/GBPUSD/AUDUSD/USDCAD are NOT
YET COMPUTED** — they are a deterministic derivation from the frozen
measured M1/H1 BID/ASK panels, executed and logged at registration
freeze (label `MEASURED-DERIVED`); until then those cells are
NOT_COMPUTED, never guessed.

**What the Daily-clock cost kernel uses (design):**
- Fill at the NEXT D1 bar open on the quoted side (next-bar-open law,
  FILL_ACCOUNTING_SPEC §1.3 adapted to D1; `UNAVAILABLE ≠ 0` fail-closed
  with forward bar search and `UNAVAILABLE_FILL_BAR` journaling).
- `spread_once = half of the D1 fill bar's own quoted spread` (the daily
  band); `slip_beyond_halfspread` = U3 DECLARED daily variant (event
  calendar = declared CB-blackout and top-tier-release DAY lists);
  spread-once identity `spread_once + slip == |fill − mid_at_fill|`
  exact per fill — no third crossing line (spec §2).
- **Commission U2 = 0.35 bps per side** of traded notional — DECLARED.
- **Swap U4/U5 accrual law for multi-day holds (every daily leg holds
  nights: 5–10 sessions typical, hold caps ≤2×half-life / ≤10 phiên):**
  1 pip per night **against the position in BOTH directions, never
  income** (pessimistic symmetry); accrual boundary 22:00 UTC; frozen
  DECLARED calendar — Sun ×1, Mon ×1, Tue ×1, **Wed ×3** (spot T+2 rolls
  the weekend), Thu ×1, **Fri ×0**, Sat no event ⇒ exactly 7 pip-nights
  per 7-night week for a continuously held position; membership rule:
  an event at E charges iff `u(E⁻) ≠ 0`. This calendar is a DECLARED
  modeling convention, NOT a venue-measured fact — the OI-2 statement
  replaces it whole.
- **Stress ×1.5 GOVERNING** on ALL variable components (crossing
  distance, commission rate, swap rate, cell p90s; Wed×3 preserved;
  non-variable fences unscaled) — spec §5. ×2.0 deferred (§3).
- GROSS/NET dual books; PASS bars consume NET only.

---

## 6. Journal law (PC12A engine lineage; journal_row@1)

Append-only, hash-chained (`prev_row_sha256`) under the trial freeze SHA;
**every order intent journaled — filled, blocked, deferred, netted,
fail-closed** (JOURNAL_SCHEMA header law + §1). Daily-clock specifics this plan adds:

1. **PIT snapshot fields (the OI-1 law made mechanical):** every decision
   row carries `feature_pit_snapshot` with one entry per input:
   `{input_id, available_time_utc, value_digest, max_age_ok}` where
   **`available_time_utc` = the NEXT BUSINESS DAY after the consumed D1
   bar's close** (OI-1 `LAG_DECLARED_BY_OWNER`; EIA inputs the same T+1
   class via their measured 1bd serving — OI-5; VIX floored to the same
   next-business-day class). Decision timestamp = T+1 open; any staleness
   ⇒ the row is still written with `outcome=BLOCKED_STALE` (no cash
   effect). UNAVAILABLE inputs abort the affected leg fail-closed, never
   0-fill.
2. **Full trade rows:** decision block (fold/cycle/sleeve/corpus ids,
   family, mech_key, direction_vote, desired_risk_units,
   entry_reason_code from the frozen leg spec, eligibility/risk/portfolio
   state) + fill block (fill_price, quoted side, `spread_pips_charged` =
   daily-band cell id, `slippage_beyond_spread` = U3 band id,
   commission, per-night swap rows with **Wed×3 flag**, venue model) +
   outcome block (gross/cost/net USD, MAE/MFE, hold_bars,
   exit_reason_code).
3. **Blocked-signal rows:** decision-time block + outcome enum +
   `blocked_reason_detail`; rule re-derivable from frozen policy inputs
   at `ts_decision_utc` (1% sample, full recompute on STOP-3 trips).
4. **Quote-CCY conversion rows (§7b of the protocol skeleton — REQUIRED,
   implemented before freeze):** all PnL/DD computed in quote-CCY then
   converted at ONE frozen convention — per-fill realization rate for
   cash events, equity marks at the same bar's conversion rate.
   **USDJPY legs (DS-02/03/04) carry an explicit JPY→USD conversion row
   per fill** (rate = the fill bar's own USDJPY mid, source ts logged);
   EURUSD/AUDUSD/NZDUSD quote USD (conversion identity 1.0, still
   logged). Reconciliation: per-symbol quote-CCY books must satisfy the
   FILL_ACCOUNTING_SPEC §6 equity-decomposition invariant to 1e-9 AND
   cross-check against a par-convention replay with the disclosed
   divergence bound (closes the PC12A at-par defect, DECISION_PACKET
   §13).
5. **MAE/MFE at the daily clock:** computed on the finest LAWFUL clock
   per symbol — majors via H1/M1 sub-path; NZDUSD D1-path only (intraday
   interior scans NOT_RUN per ERRATUM_LABELS_2026-09-30) — labeled
   coarser, never extrapolated.
6. Fold-edge force-flat: positions force-closed at each fold's last bar,
   costs charged, disclosed (E-Law 2).

---

## 7. Registration gate (exact condition; what A1 does then)

**GATE — registration of the scored DAILY successor executes ONLY when
ALL hold:**

1. **OI-2 LANDS:** the IBKR Activity/Flex statement exists in
   `~/.my-quantitative-data/ibkr_statement/` (Trades-with-Commission +
   Interest Accruals sections; covering FX trades + overnights) and its
   measured commission/swap values are frozen into the cost kernel,
   converting the DECLARED bands to measured. Until then the
   **NOT_RUN_STATEMENT blocker stands** — no scored run, no after-cost
   PASS, nothing in this plan scores.
2. **PIT gates PASS:** OI-1 labels applied to every consumed series; the
   1σ/5σ/0.5σ tripwire computed at freeze against each archive (NZDUSD σ
   64.64 / USDCHF σ 49.62 bps measured; **XAU σ computed at freeze** vs
   the pinned TD archive); VIX span/availability re-verified.
3. **Cost gates PASS:** daily-band spread derivations computed and frozen
   (MEASURED-DERIVED, logged); U2/U3/U4 bands re-labeled measured where
   the statement converts them.
4. **Vehicle gates PASS:** sha-pinned panels of record; the declared
   D1-close aggregation law, the synthetic-cross constructions (DS-04-a)
   and all per-leg PARAM-GAP declarations frozen.
5. **D1 input-completion action resolved** (§2.4): AUDUSD/USDCAD D1
   extension pull landed, or fold-8 truncation typed
   `NOT_RUN_INPUT_END`.
6. **Selection freeze:** this slate (7 legs), the parked/excluded tables,
   param declarations, grids G1/G2, calendar §2 and budget §3 frozen.

**Then A1 (and ONLY then):** `researchctl register` the successor
daily-track amendment naming this plan + OWNER_PACKET v2 + GATE_UPDATE v2
+ GATE_TABLE_V2 + frozen manifests + DAILY_ADMISSION_MATRIX + OI_DECISIONS_APPLIED
as preregistration inputs → freeze code/data/selection/cost → fresh-context
**A7 prelaunch** → **STOP before any scored GO**. The typed GO phrase is
registered at registration and belongs to the owner at that cycle's own
gate — it is not consumable from this draft. (Registration also carries
D-DAILY-9's boundary-sentence correction duty; no CONTFUT boundary exists
in this slate — energy execution FLAT — so that correction is moot here
but not for any future energy amendment.)

---

## 8. Fresh-skeptic attack list (mandatory pre-registration review)

The fresh skeptic (fresh context, no authorship of this file) must attack
at minimum:

- **a. Admission inferences.** (i) The synthetic-cross extension beyond
  Matrix B's declared NZDJPY/CHFJPY pair — EURJPY/AUDJPY/CADJPY/GBPJPY by
  triangle arithmetic on D1 closes of USD-majors (DS-04-a): is
  close-multiplication a faithful cross at the 17:00 ET close, and is the
  declaration lawful rather than an evidence upgrade? (ii) The declared
  D1-close aggregation from M1/H1 panels (which close time; holiday
  alignment; gap handling). (iii) VIX "evidenced G-PIT-V2" carried on
  Matrix B's citation alone — span vs 2021-10-01→2022-09-22 LEARN +
  folds must be re-measured. (iv) The EXPOSURE-ADJACENT labeling (§2.1) —
  does any PASS bar quietly lean on folds whose underlying majors panels
  are PC12A-exposed? (v) The parked-vs-admitted boundary: is DS-02's
  "hedge completion" re-scope (gold signal-only) any less of a rule
  rewrite than the park reasons given DS-04-a/S-090?
- **b. Calendar arithmetic.** Recompute 2,190d / 312.857w; 364+357+7+
  8×182 = 2,184 ≤ 2,190; the 51w-vs-20% rounding law and the deviation
  from SUCCESSOR_PLAN_DRAFT §3.2's "first 20%" wording; warmup-before-
  LEARN vs warmup-inside-LEARN; per-fold date boundaries (weekend/
  holiday placement of 2022-09-30 … 2026-09-24); the AUD/CA 2026-06-30
  boundary arithmetic; whether fold-edge force-flat interacts with
  multi-week holds (S083 fades 1 week — can a fold edge strand a
  half-life hold?).
- **c. Budget sums.** 15 identities / 112 scored rows / 6 LEARN rows /
  118 total; B0 zero-row counting law; the battery's own seed line; the
  ×2.0 deferral justification (does PB2 P6b admit deferral at all, or is
  this plan non-compliant and obliged to restructure?); whether 6 LEARN
  grid rows suffice for G1/G2 honesty.
- **d. Corpus-rule fidelity.** Verbatim quotes vs this file's paraphrases
  (any drift = integrity trip): the DS-01 z-direction ambiguity
  (registration decision DS-01-a — is admitting the leg at all lawful
  while the corpus text is internally tensioned?); dropped/ungated
  couplings (FOMC/NFP veto DS-04-b; BTP-Bund gates DS-06-a); DS-07's
  absent stop; DS-02's declared 60d windows; whether S100/S090 park
  reasons are complete and whether any other leg's coupling line was
  quietly promoted or demoted; the shared DS-06/DS-07 cluster (is the
  slate secretly a 6-hypothesis book?).
- **e. Admission-state scoping.** Confirm no XAG/energy-execution/AECO/
  TTF dependency leaked into §1.1; confirm OI-2 blocker language appears
  at every gate where a score could be implied.

---

## Boundary compliance (this task)

Read-only except this one file
(`…/successor/daily_successor/PLAN_DAILY_SUCCESSOR_DRAFT.md`); `.venv/
bin/python` used for date/row arithmetic only; no network, no engine
execution, no scored computation, no registry/eligibility/GO/ledger/
FAMILY_FAILURES write, no S1 touch, no orders, purchases or keys; lane
branches not written. No PASS was inferred from any NOT_RUN cell; costs
are NOT_RUN (OI-2) and nothing herein scores.

— end of draft —
