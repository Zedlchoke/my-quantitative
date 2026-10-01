# G3+G4 — VIX re-verification + σ tripwire computation (DAILY successor prep)

Analyst: G3+G4 lane (read-only prep), 2026-10-01. Repo
`/Users/hoangminhlong/my-quantitative`, interpreter `.venv/bin/python`.
Preparation only — no registration, no scored runs, no network fetches, no
S1. Nothing here is a GO; nothing is frozen by this file alone.

> **FREEZE-TIME STATUS — READ FIRST.** These are freeze-TIME computations
> done EARLY (before registration). They are the template + the measured
> numbers the registration re-run must reproduce. At registration G3/G4 are
> **re-run and frozen — and never loosened to pass** (OI-1 law;
> `OI_DECISIONS_APPLIED.md`). Any value that changed by then is re-measured
> and re-frozen as it falls; a FAIL at freeze is a FAIL, not a re-derivation
> invitation. Baseline σ values below that exactly reproduce the lane's
> committed numbers carry VERIFIED; everything else carries the early/
> freeze-time label.

Gate slots: `PLAN_DAILY_SUCCESSOR_DRAFT.md` §1 gate table — G3 "VIX
span/availability re-verified at freeze", G4 "σ tripwire 1σ/5σ/0.5σ computed
vs each archive (NZD 64.64 / CHF 49.62 measured; XAU at freeze)". Both are
listed NOT_RUN there (freeze-time checks); this document executes them early
and re-flags them for the registration re-run.

---

## 1. G3 — VIX span/availability re-verification

DS-02 (USDJPY-S063, `xasset_safehaven_goldjpy`, PARKED in the DAILY draft)
consumes **I-VIX** ("VIX Δ5 ngày > +4 … exit khi VIX<20"). Other on-file VIX
consumers (PC12A trial ledger, `PARKED_IMPL`): **USDJPY-S066** (VIX>25 two
consecutive closes → short 0.5× vol-target, exit VIX<20; `AMECH-W1-084`,
"core input VIX daily close not staged on this checkout") and **AUDUSD-S091**
(VIX 20d-median; `AMECH-W1-081`). The G-PIT-V2 law binds all three the same
way; DS-02 is the named freeze-check consumer per the dispatch.

### 1.1 Store identity (sha re-verification)

Store: `~/.my-quantitative-data/pr12a100k/raw/` — committed raw store of the
PORTFOLIO-ROUTER-12ASSETS-100K-V1 D1_macro_pit lane.
`MANIFEST.json` (`pr12a100k_raw_manifest@1`, generated 2026-09-28T13:51:50Z,
`n_files: 50`). The manifest lives at the `raw/` root (one manifest covers
all 50 sha-pinned files across vix/effr/brent/wti/alfred/evidence_pages).

Identity check recomputed 2026-10-01 with `hashlib.sha256`, **all 50
manifest files** (superset of the required ≥3-file sample):

- **MATCH: 50/50. MISMATCH: 0. MISSING: 0.**
- VIX-channel files (the two that matter for this gate), manifest sha vs
  recomputed sha:
  - `raw/vix/VIX_History_cboe.csv` — `4bca3f49062d5196f00cf6e62d04f77304608884ca4d791d2e7210e274d52796` — **MATCH** (473,074 bytes; fetched 2026-09-28T13:13:48Z from `cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv`).
  - `raw/vix/VIXCLS_fredgraph.csv` — `675f9bcb86ee88799f8f7a8b7ee9c30f7a0be26a26df8f9549bddf9e84c4a598` — **MATCH** (161,323 bytes; fetched 2026-09-28T13:13:16Z from `fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS`).
  - Supporting vintages also re-verified: `alfred/vintage_VIXCLS_20241120.csv` (`68f3e493…`) MATCH; `alfred/vintage_VIXCLS_20260303.csv` (`855003fe…`) MATCH.

### 1.2 Span, rows, gap census (recomputed from the pinned bytes)

CBOE channel `vix/VIX_History_cboe.csv` (DATE,OPEN,HIGH,LOW,CLOSE; CLOSE used):

| metric | value |
|---|---|
| rows | **9,281** (0 duplicate dates) |
| span | **1990-01-02 → 2026-09-25** |
| weekend rows | **0 Saturday, 0 Sunday** (weekday census Mon–Fri = 1764/1900/1896/1869/1852) |
| full-history gap census | 1d:7284 · 2d:79 · 3d:1700 (weekends) · 4d:214 (holiday weekends) · 5d:2 (2006-12-29→2007-01-03, 2012-10-26→2012-10-31) · 7d:1 (2001-09-10→2001-09-17, post-9/11 exchange close) |
| gaps >5d | 1 in 36 years (the 2001 week), none in-window |
| **window 2020-10-01→2026-09-30** | **n=1,536**, first 2020-10-01, last 2026-09-25; gaps 1d:1217 · 2d:6 · 3d:292 · 4d:20; **max gap 4 days** |
| missing weekdays in-window | **26, all US exchange holidays** (Thanksgiving/Christmas/NewYear/MLK/Presidents/GoodFriday/Memorial/Jul4-observed/Labor; by year 2020:2, 2021:9, 2022:4, 2023:3, 2024:3, 2025:3, 2026:2 — full list in the analyst transcript) |

FRED mirror `vix/VIXCLS_fredgraph.csv`: 9,279 rows, span 1990-01-02 →
2026-09-22, 0 weekend rows, same window census (n=1,533, max gap 4d, the
same 26 holidays). FRED-only date vs CBOE: 1999-12-31 (known mirror quirk,
outside the window).

### 1.3 G-PIT-V2 law re-verified against the pinned bytes

Source of law: `pit/PIT_DOSSIER.md` (PORTFOLIO-ROUTER-12ASSETS-100K-V1
worktree), G-PIT-V2 — VERDICT PASS_EVIDENCED. Re-measured today:

1. **Dual-channel value cross-check REPRODUCED EXACTLY.** CBOE vs FRED:
   **9,278 common dates 1990-01-02 → 2026-09-22, zero value mismatches,
   max |diff| = 0.000000** — identical to the dossier's frozen
   "9,278/9,278" sentence. Only divergence is recency: CBOE-only 3 dates
   (2026-09-23/24/25); FRED-only 1 date (1999-12-31). FRED mirror lag vs
   CBOE-direct measured 3 trading days at the 2026-09-28 fetch — consistent
   with the dossier's "measured 1 bd (2024-11), 1 bd (2026-03), 3 bd
   (2026-09)".
2. **Dissemination time (unchanged, archived evidence):** CBOE RTH VIX
   calculation ends 16:15 ET → the closing VIX value of day d exists by
   **d 16:15 ET** (`evidence_pages/cboe_vix_faqs.html`, sha `7cc05c13f9cc`,
   re-verified MATCH in §1.1's 50/50). File freshness measured ≤1 trading
   day (Monday 2026-09-28 file contains Friday 2026-09-25 — confirmed by the
   span above).
3. **Vintage/no-retro-revision evidence (sha-pinned, re-verified):**
   Wayback captures 2024-11-20 (`68f3e493…`, last obs 2024-11-19, 8,805
   rows) and 2026-03-03 (`855003fe…`, last obs 2026-02-27, 9,133 rows)
   agree value-for-value with the current bytes on every overlapping date
   (dossier's 3-vintage proof; vintages re-hashed MATCH today).

### 1.4 G3 verdicts

**(a) Span covers the 2020-10 → 2026-09 daily calendar need — PASS
(EVIDENCED, freeze-time, committed store).** The CBOE channel covers
2020-10-01 → 2026-09-25 with n=1,536 sessions, max calendar gap 4 days, and
0 missing weekdays beyond the 26 US exchange holidays. Disclosure: the last
3 trading days of the window (2026-09-28/29/30) post-date the frozen fetch
(2026-09-28T13:13Z) and are legitimately absent from the committed store;
the **registration re-run must re-extend and re-verify the tail** (expected:
same channel, ≤1 trading-day freshness). FRED mirror alone would FAIL a
freshness need at the window tail (ends 2026-09-22) but is the citation/
archive channel, not the live channel.

**(b) Availability law restated for the DAILY clock — PASS (law restated,
clock-arithmetic proven, no new measurement needed).**

> **DAILY-clock VIX availability law:** the VIX close of date **t** is
> published by **t 16:15 ET** (CBOE-direct channel, archived evidence) and
> is **usable at the t+1 close decision** per the OI-1 next-business-day
> rule. Margin: t 16:15 ET → t+1 17:00 ET = **24 h 45 m ≥ 24 h** — the same
> clock arithmetic as the frozen G-PIT-V2 proof ("Thursday 16:15 → Friday
> 17:00"), so the successor consumes VIX exactly one decision-day behind
> publication, strictly conservative (costs staleness, never lookahead).

Mechanical form (plan §engine, "PIT snapshot fields"): every VIX input row
carries `available_time_utc` = **the next business day after the consumed
D1 bar's close** — the plan explicitly floors VIX to the OI-1
next-business-day class. Note this floor is MORE conservative than raw
G-PIT-V2 (which would nominally admit the same-day 16:15 value into a 17:00
decision); the successor does not use that same-day margin. The FRED mirror
channel keeps its frozen conservative rule (value of d usable from d+3
business days) — archive/citation only, never the live channel. G3 at
registration = re-run §1.1–1.4 on the then-current store.

---

## 2. G4 — σ tripwire 1σ/5σ/0.5σ computation

### 2.1 The σ-law (frozen text this computation implements)

From OI_DECISIONS_APPLIED.md (2026-10-01, post-b00f934e): "σ tripwire
FROZEN: 1σ/5σ/0.5σ per the lane's σ-law (tripwire in panel-volatility
units; tight bars demote ECB; NEVER loosened to pass)". The lane law is
OWNER_PACKET.md **D-1b "Threshold law"** (withdrawn fixed-number bars
replaced):

> **abs p50 ≤ 1σ AND abs p95 ≤ 5σ AND |signed mean| ≤ 0.5σ**, with σ =
> full-window daily close-to-close return σ of the IBKR mid panel
> (`panel_volatility` in XCHECK_REPORT.json) — an **instrument property
> measured from the IBKR panel, independent of the basis table**.

Per D-1b ¶1, the freeze must log the measured distribution beside the bar
(exclusion-zone logging) and name the corruption modes the bar catches:
**level/scale errors, stale-frozen panels, systematic offset**. Multiplier
semantics (owner's own usage): **1σ = the default abs-p50 tripwire leg; 5σ
= the abs-p95 tail leg (reject outlier / basis-break); 0.5σ = the
|signed-mean| tight leg — tight-bar application demotes a failing archive
(e.g. ECB → disclosed-secondary), never moves the bar.**

### 2.2 Estimator definition — recovered EXACTLY from the lane's committed script

The estimator is NOT mine; it is reproduced line-for-line from
`validate_xcheck.py` (committed at `cbae7556`, current at `d722f5d5` on the
`pc12a-7asset-unblock-20261001` worktree), functions `ibkr_mid()` and
`ret_sigma_bps()` (lines 63–73, 322–330):

1. **Panel**: for each of the 6 yearly chunks
   (`{ASSET}_1d_BID_{20210930..20260930}.json` + `_ASK_` twins,
   `~/.my-quantitative-data/portfolio-composite-12assets-100k-v1/ibkr_acq_20260930/`),
   take `close` per date from BID and ASK; keep dates present in BOTH with
   `bid>0 and ask>=bid`; **mid = (BID close + ASK close)/2**; chunk-merge
   by dict assignment (later chunk wins on overlap).
2. **Returns**: sort dates; **simple (not log) close-to-close returns**,
   `r = (mid[b]/mid[a] − 1) × 10⁴` bps, over consecutive panel dates.
3. **σ**: **population standard deviation** (`statistics.pstdev`) of all
   such returns over the full panel (no window filter, no ddof=1), rounded
   to 4 decimals; `n_returns` = count of consecutive pairs.

So: "σ = pstdev of daily simple mid returns in bps, full panel". The
dispatch's guess ("log-returns × 10,000") is CLOSE but NOT the lane's
definition — the lane froze simple returns. I used the lane's definition;
the baselines reproduce bit-exactly (§2.3), so no lane confirmation is
needed.

### 2.3 Recomputation results (IBKR chunks, DV-verified 2026-09-30, 131 files)

| instrument | panel span | n obs | n returns | σ (bps) | baseline | verdict |
|---|---|---|---|---|---|---|
| NZDUSD | 2020-10-02 → 2026-09-30 | 1,553 | 1,552 | **64.6388** | 64.6388 (XCHECK@cbae7556; "64.64") | **VERIFIED — exact (Δ 0.0000)** |
| USDCHF | 2020-10-02 → 2026-09-30 | 1,553 | 1,552 | **49.6150** | 49.6150 (XCHECK@cbae7556; "49.62") | **VERIFIED — exact (Δ 0.0000)** |
| XAUUSD (IBKR panel — **freeze basis**) | 2020-10-02 → 2026-09-30 | 1,543 | 1,542 | **112.1838** | — (plan: "XAU σ computed at freeze") | **COMPUTED (freeze-time, early)** |
| XAUUSD (pinned TD archive, window 2020-10-01→2026-09-30 — **cross-check**) | 2020-10-01 → 2026-09-16* | 1,705 | 1,704 | **104.5190** | — | COMPUTED (cross-check) |
| XAUUSD (pinned TD archive, full series 1979-12-26→2026-09-16) | 1979-12-26 → 2026-09-16 | 12,268 | 12,267 | 115.1141 | — | COMPUTED (context only) |

\* archive window filter is 2020-10-01..2026-09-30; the archive's own last
obs is 2026-09-16. XCHECK spans agree: `TD_XAUUSD` n_window=1705,
`IBKR_XAUUSD_mid` n_window=1543.

Pinned archive re-verified (OI-3):
`/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng6/integration/research/control/forex_ng6_run/p0/staging/XAUUSD_1day_full.json`
— sha256 recomputed = `49c2684ebb045302acf0c452b5aa9a3b96dff73eb3bc6f5add1801d6817fb33d`,
1,347,055 bytes — **exact match to the pin**.

**Which basis the tripwire freezes on:** the **IBKR panel** (OI-1:
panel-of-record for XAUUSD; D-1b: σ measured "from the IBKR panel"). The
pinned TD archive is the **cross-check** (OI-3; XAU-as-SIGNAL basis
MEASURED vs pinned archive). The two σ's differ — 112.18 (IBKR) vs 104.52
(archive, same window, ≈7.3% apart) — because venue calendars differ
(1,543 vs 1,705 sessions in-window) and fixing times differ (IBKR ET
session close vs TD close series); this is disclosed, not harmonized. The
IBKR basis is also the higher (more conservative) σ for the p50/p95 legs.
For the archive's own |signed-mean| tight leg the D-1b ¶3 substitute-panel
rule applies as it falls — never re-derived from the overlap table.

### 2.4 FREEZE-READY TRIPWIRE TABLE (1σ/5σ/0.5σ, bps)

| instrument | σ basis (units: bps of daily mid return) | σ | **0.5σ** = \|signed mean\| ≤ (tight leg → demote failing archive) | **1σ** = abs p50 ≤ (default tripwire) | **5σ** = abs p95 ≤ (outlier / basis-break reject) |
|---|---|---|---|---|---|
| **NZDUSD** | IBKR mid panel 2020-10-02→2026-09-30, n_ret 1,552 (**VERIFIED** vs baseline) | 64.6388 | **32.32** | **64.64** | **323.19** |
| **USDCHF** | IBKR mid panel 2020-10-02→2026-09-30, n_ret 1,552 (**VERIFIED** vs baseline) | 49.6150 | **24.81** | **49.62** | **248.08** |
| **XAUUSD** | IBKR mid panel 2020-10-02→2026-09-30, n_ret 1,542 (**freeze basis per OI-1**) | 112.1838 | **56.09** | **112.18** | **560.92** |
| XAUUSD (cross-check row, NOT the freeze basis) | pinned TD archive, window n_ret 1,704 | 104.5190 | 52.26 | 104.52 | 522.60 |

Instantiation cross-check: D-1b's own frozen reading — "NZDUSD p50 ≤ 64.6 /
p95 ≤ 323.2 / |mean| ≤ 32.3; USDCHF p50 ≤ 49.6 / p95 ≤ 248.1 / |mean| ≤
24.8" — **agrees with the recomputed table on every leg**.

Exclusion-zone logging (D-1b ¶1 duty — measured distributions beside the
bar, from `XCHECK_REPORT.json` `overlaps`, committed at `cbae7556`):

| archive vs IBKR | abs p50 (≤1σ leg) | abs p95 (≤5σ leg) | \|signed mean\| (≤0.5σ leg) | outcome |
|---|---|---|---|---|
| NZDUSD / FRED H.10 DEXUSNZ | 9.3832 ≤ 64.64 | 36.1566 ≤ 323.19 | 2.2944 ≤ 32.32 | PASS (margin) |
| NZDUSD / ECB eurofxref cross | 21.5229 ≤ 64.64 | 82.8968 ≤ 323.19 | 0.3657 ≤ 32.32 | PASS (margin) |
| USDCHF / FRED H.10 DEXSZUS | 9.3214 ≤ 49.62 | 35.4055 ≤ 248.08 | 1.5372 ≤ 24.81 | PASS (margin) |
| USDCHF / ECB eurofxref cross | 18.4347 ≤ 49.62 | 72.4287 ≤ 248.08 | 0.3334 ≤ 24.81 | PASS (margin) |
| XAUUSD / pinned TD archive | 3.2462 ≤ 112.18 | 26.5549 ≤ 560.92 | 1.6392 ≤ 56.09 | PASS (margin) |

Observed outcome note (observation, not an input, per D-1b ¶2): under the
1σ/5σ/0.5σ bar both FRED and ECB pass all three legs for both FX pairs, and
the pinned TD archive passes for XAUUSD. Under any TIGHT bar near the
10–15 bps p50 scale (D-1b ¶3 substitute-panel rule) FRED passes and **ECB
fails (21.52/18.43) → ECB is demoted to disclosed-secondary, the bar is
not raised**.

### 2.5 G4 verdicts

- **NZDUSD σ baseline 64.64 bps — PASS / VERIFIED (exact reproduction,
  Δ 0.0000, lane estimator + lane bytes).**
- **USDCHF σ baseline 49.62 bps — PASS / VERIFIED (exact reproduction,
  Δ 0.0000).**
- **XAUUSD σ — PASS as an early freeze-time computation** (IBKR 112.1838
  bps = freeze basis per OI-1; pinned-archive cross-check 104.5190 bps,
  sha re-verified). The plan said "XAU σ computed at freeze" — this IS that
  computation, done early; it must be re-run on the registration-day panel
  bytes and frozen there (never loosened).
- G4 at registration = re-run §2.3 on the then-current IBKR chunks,
  re-verify the pinned archive sha, re-instantiate §2.4, re-log §2.4's
  exclusion zone.

---

## 3. Sources (every number re-derivable from these paths)

- VIX store + manifest: `~/.my-quantitative-data/pr12a100k/raw/MANIFEST.json`,
  `raw/vix/VIX_History_cboe.csv`, `raw/vix/VIXCLS_fredgraph.csv`,
  `raw/alfred/vintage_VIXCLS_{20241120,20260303}.csv`,
  `raw/evidence_pages/cboe_vix_faqs.html`.
- G-PIT-V2 law: `.worktrees/portfolio-router-12assets-100k-v1/integration/
  research/control/PORTFOLIO-ROUTER-12ASSETS-100K-V1/pit/PIT_DOSSIER.md`
  (§G-PIT-V2; frozen available_at rules; 9,278/9,278 dual-channel sentence).
- σ-law + baselines: `.worktrees/pc12a-7asset-unblock-20261001/research/
  control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01/{OWNER_PACKET.md §D-1b,
  XCHECK_REPORT.json (panel_volatility, overlaps), validate_xcheck.py
  (estimator, lines 63–73/322–330)}` — baseline confirmed at commit
  `cbae7556` via `git show`.
- IBKR panels: `~/.my-quantitative-data/portfolio-composite-12assets-100k-v1/
  ibkr_acq_20260930/{NZDUSD,USDCHF,XAUUSD}_1d_{BID,ASK}_{20210930..20260930}.json`.
- XAU pinned archive: `.worktrees/forex-ng6/integration/research/control/
  forex_ng6_run/p0/staging/XAUUSD_1day_full.json` (sha
  `49c2684ebb045302acf0c452b5aa9a3b96dff73eb3bc6f5add1801d6817fb33d`).
- OI decisions: `research/control/terminal_review_2026-10-01/successor/
  OI_DECISIONS_APPLIED.md` (OI-1, OI-3); lane checklist
  `OWNER_INPUT_CHECKLIST.md@d722f5d5`.
- VIX consumers: `PLAN_DAILY_SUCCESSOR_DRAFT.md` (row 2 DS-02, §I-VIX,
  engine PIT-snapshot law "VIX floored to the same next-business-day
  class"); PC12A `TRIAL_LEDGER.jsonl` rows `AMECH-W1-081/084` (PARKED_IMPL).

## 4. Bottom line

| gate | verdict now | at registration |
|---|---|---|
| G3 (a) VIX span covers 2020-10→2026-09 daily need | **PASS (committed store; 26 holiday-only missing weekdays, max gap 4d; tail 09-28..09-30 post-dates the fetch — re-extend)** | re-run on then-current store |
| G3 (b) availability law for DAILY clock | **PASS (restated: VIX of t usable at t+1 close decision; 24h45m ≥ 24h margin, same clock arithmetic as frozen G-PIT-V2; OI-1 next-business-day floor)** | unchanged law, re-applied |
| G3 sha identity | **PASS 50/50 manifest files (incl. both VIX channel files)** | re-run |
| G4 NZDUSD σ 64.64 | **PASS — VERIFIED exact (64.6388)** | re-run, freeze |
| G4 USDCHF σ 49.62 | **PASS — VERIFIED exact (49.6150)** | re-run, freeze |
| G4 XAUUSD σ | **PASS (computed early: IBKR 112.1838 freeze-basis; TD archive cross-check 104.5190, sha MATCH)** | re-run on registration-day bytes, freeze |
| G4 tripwire 1σ/5σ/0.5σ | **freeze-ready table §2.4; matches D-1b's instantiated values; observed distributions logged §2.4** | re-instantiate, freeze, never loosen |
