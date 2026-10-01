# M1_OPERATIVE_UPDATE — PC12A successor, M1 track (owner no-unseal directive)

**STATUS HEADER — READ FIRST.** Preparation-only analyst output for the
PC12A successor program, M1-TRACK (EURUSD/GBPUSD/USDJPY), 2026-10-01.
Read-only except this one file. No scored runs, no engine execution, no S1
access, no network, no ledger/registry writes. **The S1 sealed tail stays
SEALED — the owner has NOT authorized unsealing; every variant below
assumes it is never read.** All computation in this file is offline
arithmetic on committed journals/metrics/audit artifacts (the same evidence
class as the symbol dockets and GATING_VS_SIZING), date arithmetic with the
repo `.venv` python, and reading of committed files. Hypothesis-generating
throughout; missing evidence is `NOT_RUN`, never inferred PASS.

Inputs consumed (read-only): `terminal_review_2026-10-01/successor/{RULE_SLATE,
GATING_VS_SIZING,SUCCESSOR_PLAN_DRAFT,OWNER_PACKET_SUCCESSOR,SKEPTIC_SUCCESSOR}.md`,
`terminal_review_2026-10-01/{DECISION_PACKET.md,symbol_docket/*.md}`,
`PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/{diagnostics/stagec/ARMS/{POLICY,
B1_ALWAYS_ON}/,campaign/BACKTEST_CAMPAIGN_DESIGN.md,journal/FILL_ACCOUNTING_SPEC.md,
policy/PASS_BARS_V2.md,poolB/data_audit/audit_summary.json}`,
worktree `…/diagnostics/stageb/LADDER.json`,
`SLEEVE-FX5-100K-V1/pitcost/COST_AUTHORITY_TABLE.md`,
`DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/*`, `plans/CYCLE_REGISTRY.json`.

---

## 1. NO-UNSEAL FALLBACK MADE OPERATIVE — recomputed LEARN and validation calendar

**Owner directive:** the unseal variant is OFF. RULE_SLATE §4's primary
learning window (LEARN = never-scored M1 2025-12-27→2026-09-23, incl. the
sealed tail) is DEAD in its unsealed form; §4 item 5's fallback semantics
apply: *defaults stand now; grids learn on the first 26 weeks of live
accumulation instead.* This section recomputes both no-unseal variants from
the artifacts and replaces SUCCESSOR_PLAN_DRAFT §3.4.

### 1.1 Anchor facts (all from committed artifacts, re-measured today)

| fact | value | source |
|---|---|---|
| Scored TEST window (exposed, burned) | 2022-01-07→2025-12-26 (8 folds) | metrics `per_fold`, CAM §3 |
| Never-scored M1 segment on file | 2025-12-27→2026-09-23 = **270 d = 38.57 w** | poolB `audit_summary.json` (M1 panels 2021-01-01→2026-09-23, 2,092 files/side, 1,440 rec/day) |
| **S1 sealed tail** | **2026-01-02→2026-06-26** = 175 d = 25.0 w | `stagec/VERIFY.json` `sealed_tail: ["2026-01-02","2026-06-26"]` |
| Unsealed never-scored M1 **after** the seal | **2026-06-27→2026-09-23** = 88 d = 12.57 w | panel end − seal end |
| Unsealed never-scored sliver **before** the seal | 2025-12-27→2026-01-01 = 5 d | non-contiguous with the above; immaterial (0.7 w) |
| Campaign common-calendar end | 2026-06-26 (M1 tail beyond it unused; H1 panels end 2026-06-30) | CAM §3, H1_PANELS.json |

**Two artifacts corrections (flag, do not silently inherit):**
(i) RULE_SLATE §4.1 calls the sealed tail "the 26-week sealed tail"; the
operative artifact says 175 d = **25.0 weeks**. (ii) RULE_SLATE §4.5's
fallback LEARN "2026-09-24→2027-03-24" is 181 d (25.86 w) — one day short
of 26 w; SUCCESSOR_PLAN_DRAFT §3.2's "2027-03-25" is the exact 26-week end.
This file canonicalizes 182 d = 26 w.

**Accumulation assumption (explicit).** The M1 panels are frozen at
2026-09-23. The only live FX channel on file (SIXSOURCE `ibkr_fx`) is a
*bounded-window* read-only quote collector (3 sessions on 2026-09-28,
~5–30 min each, cost-band windows) — **it is not an M1 bar accumulator, and
HMDS M1 history is NOT_RUN (size-cap, probe)**. Therefore no M1 bars exist
for 2026-09-24 onward today. All concrete dates below assume **the next
lawful fresh M1 data day is 2026-10-01** ("accumulation continues from
2026-10-01"), leaving a typed **7-day coverage hole 2026-09-24→2026-09-30**
unless an owner-named lawful channel backfills it (backfill there is legal:
the hole lies OUTSIDE the seal, which ended 2026-06-26). If a lawful
backfill lands (§5), the hole disappears and the "hole-tolerant" dates are
exact rather than approximate.

### 1.2 Calendar law and formulas (frozen)

- LEARN length = 26 w = 182 d (fallback semantics, RULE_SLATE §4.5).
- Embargo E = 7 d between LEARN end and fold-1 start (RULE_SLATE §4.3).
- Validation = ≥6 × 26 w non-overlapping folds (PB2 E-Law 5; CAM §3):
  6×182 = 1,092 d.
- Formulas: `fold1_start = LEARN_end + 7`; `fold1_readable = fold1_start +
  182`; `battery_complete = fold1_start + 1092`; LEARN must not overlap any
  fold; folds must not overlap the exposed window (→2025-12-26), the seal
  (2026-01-02→2026-06-26), or LEARN.

### 1.3 The two no-unseal variants

**Variant N1 (RECOMMENDED OPERATIVE) — LEARN headed by the unsealed
never-scored segment.** The seal only covers 2026-01-02→2026-06-26; the
88 unsealed never-scored days 2026-06-27→2026-09-23 are lawful TRAIN
material the slate's fallback silently ignored.

- `LEARN = 2026-06-27 → 2026-06-27 + 182 d = 2026-12-26` (26 calendar
  weeks; contains 175 data days = 96.2% completeness under the no-backfill
  assumption; 182/182 if the 7-day hole is lawfully backfilled).
  Strict alternative (law demands 182 *data* days, no hole tolerance):
  LEARN completes 2027-01-02 (88 on file + 94 fresh from 2026-10-01).
- **fold 1 start = 2027-01-02** (2026-12-26 + 7 d); strict-data reading:
  2027-01-09.
- **fold 1 readable (start+26 w) = 2027-07-03** (strict: 2027-07-10).
- **Earliest complete 6×26 w evaluation = 2029-12-29** (strict: 2030-01-05).
- No-LEARN corner (folds start immediately 2026-06-27, grids collapse to
  frozen defaults via §4.4 `NOT_RUN_GRID_THIN` by construction): battery
  complete **2029-06-23** — the absolute earliest no-unseal date, at the
  cost of zero grid learning; NOT recommended (the three gridded rules
  exist precisely because their defaults are fold-shaped).

**Variant N2 (slate's named fallback, corrected) — pure live-accumulation
LEARN.**

- As written (assumes accumulation existed from 2026-09-24): LEARN
  2026-09-24→2027-03-25 (182 d; the slate's 03-24 end corrected +1 d);
  **fold 1 start 2027-04-01, readable 2027-09-30, battery complete
  2030-03-28** (slate's own "fold 1 starts 2027-03-31 / ≈2030-03" follows
  from its 181-d reading).
- Concrete under "accumulation continues from 2026-10-01" (no backfill):
  LEARN **2026-10-01→2027-04-01**; **fold 1 start 2027-04-08, readable
  2027-10-07, battery complete 2030-04-04.**

**Reference (dead by directive):** unseal variant — LEARN 2025-12-27→
2026-09-23; fold 1 2026-09-30, readable 2027-03-31, battery 2029-09-26
(reproduces RULE_SLATE §6 exactly). **Cost of no-unseal: ~3 months under N1
(2029-12-29 vs 2029-09-26), ~6 months under N2.** The dispatch's
"mid-2027" remains unattainable on every variant: fresh stock at
2027-06-30 from 2026-06-27 = 368 d = 52.6 w = 2.02 folds < 6 ⇒
`NOT_RUN_INSUFFICIENT_CALENDAR`.

### 1.4 OPERATIVE REPLACEMENT TEXT for SUCCESSOR_PLAN_DRAFT §3 item 4 (verbatim draft)

> **4. Validation calendar (NO-UNSEAL OPERATIVE).** ≥6×26w folds + 1-week
> embargo, non-overlapping with the 2021-01-08→2025-12-26 EXPOSED window,
> the S1 sealed tail (2026-01-02→2026-06-26 — stays SEALED; no unseal is
> authorized), and the LEARN window. LEARN (no-unseal) = the unsealed
> never-scored M1 segment **2026-06-27→2026-09-23** (88 d on file) extended
> by lawful live accumulation to 26 weeks: **LEARN 2026-06-27→2026-12-26**
> (the 7-day accumulation hole 2026-09-24→2026-09-30 is typed and disclosed
> unless lawfully backfilled; any backfill channel must not touch
> 2026-01-02→2026-06-26). **Fold 1 starts 2027-01-02** (LEARN end + 7 d),
> readable **2027-07-03**; earliest complete 6×26w evaluation
> **2029-12-29** (2030-01-05 if 182 full data days are required without
> backfill). This supersedes RULE_SLATE §4.5's fallback dates (LEARN
> 2026-09-24→2027-03-25 — its 03-24 end was one day short; fold 1
> 2027-03-31/04-01, battery ≈2030-03-27/28 under that variant) and the
> unseal variants (fold 1 2026-09-30, battery 2029-09-26 — DEAD by owner
> directive). USDCAD/AUDUSD: **NOT_RUN** (no lawful H1/M1 calendar on file;
> §6 decision packet). Daily-cohort track unchanged (≈10 folds feasible
> today conditional on data-lane gates + owner D-1..D-7). "Mid-2027"
> remains unattainable on every lawful variant (fresh stock at 2027-06-30 =
> 2.02 folds < 6 ⇒ NOT_RUN_INSUFFICIENT_CALENDAR).

---

## 2. ATTRIBUTION vs ABLATION — the canonical paragraph (owner's demand)

**Canonical paragraph (every consumer of the docket/gating numbers must
cite this verbatim or by file+section):**

> **Attribution is not ablation.** Every retrospective number produced by
> the symbol dockets, GATING_VS_SIZING and the RULE_SLATE "measured
> priors" — including the L6 −$352,959 figure and the +274,572.47 of the
> 29 matched defers — is **historical attribution on the realized exposed
> paths**: arithmetic that decomposes the POLICY−B1 divergence (or a
> book-with-trades-removed) on the paths that were actually scored
> (2022-01-07→2025-12-26, folds already burned). It answers *what the
> guard's skips cost in B1's realized path* — where B1 admitted the trades
> POLICY deferred, those trades made +274.6k journal units and were
> drawdown-reducing **on that path**. It does **not** answer *what removing
> the guard causes*: an interventional re-run (guard relaxed/removed under
> RULE_SLATE SU-RS-J3) produces different trailing-spend trajectories and
> therefore different later guard states, different netting inventory,
> different sizing paths and different trades — none of which exist in any
> journal on file. The causal quantity is **new scored work and is NOT_RUN
> today**; it can only be measured on a lawful fresh calendar under the
> preregistered grid + anti-hypothesis. The same paragraph applies to every
> suppression test in docket A §6 / docket B §6 (entry-side recomputation,
> exits unchanged — path-approximate attribution) and to every component of
> the GATING_VS_SIZING decomposition (§8.4's no-counterfactual ban).
> Nothing in the successor prep changed any gate in any run.

### 2.1 Audit of RULE_SLATE / GATING_VS_SIZING for blurring (fixes listed; APPLIED by A1 this session — see the tagged lines)

- **RULE_SLATE.md:53** (§1 row 5): "Large measured **leakage** (+274.6k
  journal units)" — causal-sounding. Fix: "Large measured **B1-path
  attribution** (+274.6k journal units on the 29 matched defers; not an
  ablation — the causal effect of relaxing the guard is unmeasured)".
- **RULE_SLATE.md:102–105** (SU-RS-J1 measured prior): presents
  suppression bookkeeping incl. "maxDD −412,208.31 → −359,621.76" without a
  path-approximation tag. Fix: append "[path arithmetic on the realized
  exposed path, exits unchanged; an interventional re-run would produce
  different re-entry/netting/sizing paths — attribution only]".
- **RULE_SLATE.md:146–148** (SU-RS-J3 overfit disclosure): "the
  **leakage** is the largest single measured block of the USDJPY harm".
  Fix: "the deferred set's B1-path **attribution** is the largest single
  attributed block of the USDJPY gate harm".
- **RULE_SLATE.md:149–151** (SU-RS-J3 measured prior): "removing them
  worsens B1 USDJPY maxDD −378,482.09 → −501,493.31" — a leave-29-out on
  B1's realized path stated without the tag. Fix: append "[leave-29-out on
  B1's realized path = attribution; not evidence that relaxing the guard
  causes these outcomes on any other path]".
- **GATING_VS_SIZING.md:247**: "**The L6 cost guard is the single largest
  identified harm mechanism:**". Fix: "**The L6 cost guard carries the
  single largest attributed harm block (attribution, not ablation):**".
- **GATING_VS_SIZING.md:249–251**: "The guard fires … and skips winners in
  trends." Fix: append "(all guard numbers are attributions on the realized
  exposed paths; §8.4's no-counterfactual ban applies — no run changed the
  gate)". GATING §8.4 already carries the correct disclaimer; the fixes
  extend it to the §9 conclusions where consumers actually quote from.
- Advisory (outside the two named files): DECISION_PACKET.md:272 "guard
  HARMFUL window-wide" and :298 "window-wise harmful, +$274.6k foregone"
  read causally; USDJPY_DOCKET §8 already tags the same number correctly
  ("[derived attribution — B1 path, n=29, one trade 46%]").

---

## 3. CURRENCY-CONVERSION CHECK — USDJPY fill cash at par (docket A §0/§9)

**Question (docket A flag):** USDJPY NET_ORDER `cash_delta_usd` appears
carried at par from the JPY notional while SWAP rows are rate-converted.
Verified, quantified, and the effect on the PC12A terminal verdict bounded.

### 3.1 The convention, verified literally on every fill

Identity `cash_delta_usd = −(delta_units × fill_price) − commission_usd`
holds with **max residual 0.00000000 on 100% of USDJPY fills (POLICY
1,526 + B1 1,309 = 2,835 rows)**. Example (POLICY seq 2412,
2022-01-07T16:00Z): sell 10,000 units @ 115.63 → cash +1,156,299.65 =
10,000×115.63 − 0.35 — the **JPY notional booked 1:1 as "USD"** (par).
Swap rows ARE rate-converted: implied rate = units_abs×0.01/swap_usd
matches the last-seen mid at ratio p50 1.0005 / p95 1.006 (Wednesday rows
exactly ×3). Two conventions coexist in one ledger — FILL_ACCOUNTING_SPEC
§4 frozen quote-currency book convention, applied identically in both arms
and all folds. USDJPY fill mids span **113.68–161.81** (fold-end marks
131.88–160.85).

### 3.2 Distortion magnitude (converted via a mark-time quote-CCY debt model)

Method (offline, committed artifacts only): fold membership by exact
cumulative-cash checkpoint scan against `per_symbol_fold_records` cash_end
(8/8 checkpoints matched in both arms; flat-week replay residual $0.00 vs
the official friday_equity chain; the par DD routine reproduces metrics
`max_dd_pooled_usd` 418,227.97 / 397,156.85 **to the cent**). Converted
equity = USD cash − commissions/P − swap + base units − JPY net liability/P
at the implied official Friday marks.

| quantity (USDJPY) | par (journal units) | explicit quote→USD |
|---|---:|---:|
| POLICY window net | +600,082.92 | **+2,412.95** (single end-rate 156.52) / **+2,559.91** (fold-edge conversion) |
| B1 window net | +687,284.31 | +3,182.75 / +3,611.36 |
| POLICY per-fold net (f0..f7) | 540,319 / −150,958 / 21,369 / −78,342 / 209,982 / 74,221 / −231,318 / 214,809 | 3,724 / −1,289 / 0 / −736 / +1,071 / +348 / −1,740 / +1,183 |
| window harm (P−B1) | −87,201.39 | **−1,051** / −770 (sign stable) |
| per-fold harm signs | 0, −, −, −, +, +, −, + | identical except **fold 7: +3,677 par → −57 conv** (both sub-noise) |

Per-unit band: every USDJPY absolute magnitude scales into **[÷161.81,
÷113.68]**; effective window ratios 216–249×. Illustrations: NY-long bucket
−281,460 par ≈ −$1.74k–2.48k; L6 attribution −352,959 par ≈ −$2.18k–3.10k;
29 matched defers +274,572 par ≈ +$1.70k–2.41k; W/L threshold c = 239.54
par ≈ $1.48–2.11; median winner +9,027.60 par ≈ $56–79. Cost bills scale
likewise (friction 128,073 par ≈ $0.8–1.1k) — note commission was computed
on the USD base notional (0.35 per 10k units), which is the *correct* USD
figure by accident of the par convention.

### 3.3 What is invariant, what is not — and the verdict

- **Within-symbol, same-convention comparisons: INVARIANT (proved).** Both
  arms share the convention; USDJPY harm keeps its sign and the fold
  structure under conversion (7/8 fold-sign matches, the one flip is
  noise-scale). The GATING_VS_SIZING decomposition is within-symbol
  arithmetic; its ordering (GATE −386k ≫ SIZE −7.6k par) survives
  component-wise scaling (~÷130–160); EURUSD/GBPUSD rows are true USD and
  unchanged.
- **Cross-symbol POOLED comparisons are NOT convention-invariant (measured,
  not assumed).** The pooled books mix true-USD (EUR/GBP) with par-"USD"
  (JPY): POLICY pooled net 603,340.60 vs B1 688,604.03 fails the P1 net
  leg at par, but under explicit conversion **POLICY 5,670.63–5,817.59 >
  B1 4,502.47–4,931.09 — the pooled net-harm sign flips** (−85,263.43 par
  → **+886.50 / +1,168.16 POLICY-favorable**), because the true-USD
  EUR+GBP edge (+1,937.96) outweighs the converted USDJPY harm
  (−770…−1,051).
- **The terminal verdict SURVIVES.** P1 is AND-semantics
  (PASS_BARS_V2 §2): the **DD leg still fails under conversion** (POLICY
  6,439.67 > B1 5,270.49 converted weekly DD, mark-consistent chain; the
  par legs 418,227.97 > 397,156.85 also fail), and P1-B0 passes either
  way. `POLICY_NO_INCREMENTAL_VALUE` therefore stands — **but its sub-tag
  structure is convention-dependent**: under explicit conversion only
  `P1_B1_DD` fires; `P1_B1_PNL` would not. Consequences for citation law:
  the "−$85,263 pooled harm" headline must always be quoted as
  "USDJPY-journal-units harm −$87,201 (sign-stable); pooled sign
  convention-dependent (−85,263 par vs +887…+1,168 converted)". P7 fold
  concentration still fails under conversion (fold-0 share 84% vs 89.7%
  par). The B4-battery 128/128 objective-ranking under conversion is
  **[NR]** (not recomputable from committed aggregates; same mixing hazard
  named).
- **Successor-engine fix (REQUIRED item, prerequisite to any dollar bar):**
  implement explicit quote-CCY accounting per FILL_ACCOUNTING_SPEC §4 —
  per-fill quote→USD conversion at the fill's own price, a per-symbol
  quote-currency ledger (JPY liability/asset marked at the bar mid), USD
  book equity = USD cash + Σ base units ± quote-CCY positions/rate, plus
  the already-required MAE/MFE and per-leg exposure journaling (A §9, B
  §9). **Freeze ONE conversion convention at registration**: fold nets
  differ by ~6% between realization-time and end-rate conversion
  (2,559.91 vs 2,412.95) — a preregistration choice, not a presentation
  choice. Every PC12A journal-unit threshold carried into the successor
  (c_pair medians, P-MW/P-FA dollar terms, cost-stress tiers on USDJPY)
  must be restated in converted USD.

---

## 4. COST AUTHORITY CHECK — scored stack vs COST_AUTHORITY_TABLE

Confirmed from the journals/metrics (no new measurement):

- **C1/C2/C3 spreads: MEASURED, panel venue** — journals carry
  `spread_pips_charged` cells (C1 on all 910 EUR/GBP fills; C1 + declared
  C2/C3 bands on USDJPY); authority values match (EURUSD 0.3/0.5, GBPUSD
  0.8/1.3, USDJPY 0.5/0.9 p50/p90; C3 reopen cells 11.0/22.0 USDJPY).
- **C4 commission U2 0.35 bps/side DECLARED** — journal commission =
  0.000035 × notional, verified per fill (EURUSD 11,347 USD → 0.397145).
- **C5 swap U4/U5 1 pip/night against, Wed ×3, 22:00 UTC, never income —
  DECLARED** — verified in rows (§3.1), rate-converted.
- **C6 slip U3 0.2/1.0 pip DECLARED** — `U3_NON_EVENT` 0.20/fill par on
  non-event fills.
- **Stress tiers** ×1.0/×1.5/×2.0 present as scored identities
  (`POLICY_X15/X20`, `B1_X15/X20`) on all variable components; C7 n/a
  (spot OTC); C8 margin declared, PnL-inert.
- **Per-pair verdict: PROVISIONAL_PENDING_COST_AUTHORITY on all pairs;
  every survivor carries NET_DEFAULT_COST** — matches the authority table
  §2 exactly. LADDER.json confirms the L6 cap $2,836.97 = **p90 of the
  TRAIN switching-cost ladder** (3,394 events, p50 $1,770.51) — the
  guard-cap provenance is TRAIN-derived, pre-test, and unchanged.

**Successor conclusions provisional on the owner statement** (IBKR
Activity/Flex: FX trades + Interest Accruals →
`~/.my-quantitative-data/ibkr_statement/`): every net-PnL PASS claim
(incl. P-MW/P-FA dollar terms), the P2 governing ×1.5 tier, EURUSD
swap-dominance findings (65% of its cost bill), C-H-C2 swap-drag, and any
absolute-dollar statement. Also unmeasured: panel↔IBKR spread venue
transfer (C1 caveat ii) — the SIXSOURCE bounded sessions are the named
upgrade path (≥200 valid two-sided obs per pair×hour-bucket; 3 sessions on
file = first n-small cells only). Nothing new measured in this file. ✔

---

## 5. Collection / forward-validation protocol — EURUSD/GBPUSD/USDJPY (preparation-level spec)

**What actually exists (measured):** (i) frozen Dukascopy .bi5 M1 BID/ASK
panels 2021-01-01→2026-09-23 (2,092 files/side/symbol, sha'd + audited in
poolB `audit_summary.json`); (ii) SIXSOURCE `ibkr_fx` = read-only
bounded-session tbt BidAsk collector on port 7497
(`collect_fx_ticks.py`, no order functions by construction, sanitized
JSON windows + raw bytes outside git under sha256, append-only
`sessions_index.jsonl`; 3 sessions on 2026-09-28, 2–3/week planned) — a
**cost-band accumulator, not an M1 panel channel**; (iii) HMDS M1 history
NOT_RUN (size-capped, probe); (iv) LIVE-DATA-GATEWAY-V1 is a **crypto**
lane (Binance REST/WS) — no FX M1 relevance. Conclusion: **no continuous
M1 accumulation exists today; the calendar in §1 is contingent on creating
one lawfully.**

**Protocol spec (draft for owner registration; nothing runs from this
file):**

1. **Primary panel channel — scheduled bounded refresh via an owner-named
   free/keyless M1 source (Dukascopy precedent).** Weekly bounded fetches
   extend `data_local/<SYM>/M1/{BID,ASK}/YYYY-MM-DD.bi5` (identical schema:
   1,440 records/day, t/o/c/l/h per side) under a NEW lane directory —
   never inside frozen panel paths. **Hard boundary: no fetch range may
   touch 2026-01-02→2026-06-26 (S1 seal).** The 2026-09-24→2026-09-30 hole
   is outside the seal and may be backfilled here (closes §1's hole and
   restores the N1 dates to full data days).
2. **Secondary channel — extended continuous read-only 7497 session**
   (same whitelist, order functions absent) writing rolling sanitized quote
   windows → same-day incremental M1 bar builds + a **measured** PIT-lag
   band (recv−server skew measured ≤2.08 s; second-resolution server
   stamps declared `approx`; no forward-fill).
3. **Writes & manifests.** Every bar file gets an append-only JSONL
   manifest row (mirror `sessions_index.jsonl` conventions): date, side,
   sha256, n_records, first/last tradable ts, acquisition session/fetch id,
   source venue. Repairs are new manifest rows, never in-place edits.
4. **PIT stamping.** Bars carry acquisition UTC; pit_lag declared from
   measured stream skew or fetch latency as applicable; venue-transfer
   caveat (C1 caveat ii) on any IBKR-sourced bar — the panel of record
   stays single-venue per symbol.
5. **Weekly integrity checks** (extend the poolB audit script): file
   continuity (holes typed with reason codes, never silently filled),
   nrec=1440 histogram, zero-byte/name conformance, negative-spread census
   (=0), tradable-minute census, cross-side date-set identity, digest
   re-hash vs manifest, cross-venue spot-checks vs the IBKR sanitized
   windows.
6. **When the calendar becomes lawful.** Under §1's N1: when accumulation
   delivers through **2026-12-26** (LEARN complete) → fold 1 lawful from
   **2027-01-02** (readable 2027-07-03; battery 2029-12-29). Fold windows
   must never overlap the exposed window, the seal, or LEARN.

Explicitly NOT in this protocol: HMDS M1 history (size-cap NOT_RUN), any
S1 read, unowned network sources, any scored run, any eligibility change.

---

## 6. USDCAD/AUDUSD collector feasibility — DECISION PACKET

Context (docket C): 9 H1 legs diagnosed, **all 9 killed COST_DOMINATED at
×2.0** (only USDCAD-S011 +$111.72 and S091 +$313.61 were net-positive at
×1.0, both flipping at ×2.0); C2 21:00-bar structural absence (431/320 of
30,043 weekday rows); Friday 20:00-bar deferral 13.6% USDCAD / **30.4%
AUDUSD** into 4–6× wider C3; H1 panels frozen 2021-01-03→2026-06-30
(`read_only`); reopening requires the TERMINAL_DECISION Q-10
changed-mechanism-axis condition; R6 PIT freeze keeps M1 features on these
pairs BLOCKED_DATA.

| option | what | cost/effort | risk | lawfulness | earliest 6×26w validation |
|---|---|---|---|---|---|
| **(a) do nothing** | permanent `NOT_RUN` for this successor; H-C1/H-C2/H-C3 stay parked as named re-entry triggers | zero | none | fully lawful (no action) | **never** |
| **(b) IBKR 7497 continuous H1 accumulation** | extend the read-only collector to 24/5 for USDCAD/AUDUSD + H1 bar builder + own cost authority | high: collector hardening, new panel-of-record, new cost cells | single-venue paper quotes; venue transfer unmeasured; C1–C3 panel cells do not carry over | read-only channel proven (both pairs streamed in s0: 1,373/1,688 obs), but panel-of-record + cost gates unproven; Q-10 check needed | from 2026-10-01: folds-from-day-1 (frozen defaults) **2029-09-27**; with 26w LEARN + embargo **2030-04-04** |
| **(c) owner-named free/keyless H1 refresh (Dukascopy precedent)** | bounded weekly H1 refresh extending the existing ANC panels contiguously (2026-07-01→today is unsealed-for-H1: no H1 fold was ever scored; conservative fresh boundary = campaign end 2026-06-26/panel end 2026-06-30) + forward accumulation | low: precedent machinery exists (same venue, cost cells carry over) | discovery exposure of TRAIN folds 2021→2025-06 must be priced (same as any successor); needs owner naming + plan amendment + Q-10 | highest of the collector options (identical venue to frozen panels; keyless precedent = the original fetches) | folds from 2026-07-01 → **2029-06-27** (defaults-first); with 26w fresh LEARN (2026-07-01→2026-12-30) folds 2027-01-06 → **2030-01-02** |
| **(d) drop the pairs** | programmatic removal from the successor scope | zero | none | fully lawful | never |

**Recommendation: (a) — do nothing this cycle (accept permanent NOT_RUN
for USDCAD/AUDUSD in ONOFF-SUCCESSOR-V1), with (d) as its formal wording
at registration.** Reasons: (i) the H1 economics are the worst in the
program (9/9 cost kills; the two ×1.0 survivors flip at the governing
×2.0; H-C2 — the only broadly-sweeping hypothesis — is gated on the owner
cost statement, not a collector); (ii) the collector options' earliest
dates (2029-06/2030-04) are not materially earlier than the already-funded
M1 track (2029-12-29) and would validate only benched hypotheses ranked
9–11; (iii) the successor's ≤24-identity budget is committed to the
6-rule M1 slate; (iv) option (b) buys a single-venue panel with no
measured cost authority. If the owner nevertheless wants the H1 track,
**(c) dominates (b)** on every axis — name the source, and the H-C1/H-C3
re-entry triggers (per-fill hour-stamped pricing; amended Friday fill law)
become testable on the 2029-06-23 calendar at the earliest.

---

## Traceability (claim → evidence)

- Sealed-tail dates: `stagec/VERIFY.json` (`sealed_tail`), CAM §3; panel
  spans: poolB `audit_summary.json`; collector facts: SIXSOURCE
  `ibkr_fx/{L-FX_REPORT.md,sessions_index.jsonl,sanitized_*}`,
  CYCLE_REGISTRY LIVE-DATA-GATEWAY-V1 (crypto); HMDS M1: probe per DP §11.0.
- Calendar arithmetic: `.venv` python date math from the anchors above
  (this session; formulas in §1.2 so every date is re-derivable).
- Currency identity/conversion: committed stagec journals + metrics
  (2,835 USDJPY fills; checkpoint scan 8/8 arms; DD routine reproduces
  metrics to the cent; converted chains use implied official Friday marks).
- Cost stack: journals' cost fields vs `COST_AUTHORITY_TABLE.md`;
  L6 cap: stageb `LADDER.json` (`guard.cap_usd` 2,836.97 = TRAIN p90).
- Attribution/ablation: GATING_VS_SIZING §8.4, USDJPY_DOCKET §6/§8, RULE_SLATE
  §1/§2 (lines cited in §2.1).

— end of file. The only artifact written this session is this file.
