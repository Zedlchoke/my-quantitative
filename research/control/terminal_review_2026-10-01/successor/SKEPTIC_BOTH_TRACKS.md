# SKEPTIC_BOTH_TRACKS — fresh-context audit of the session-3 successor package (2026-10-01)

**Scope.** Uncommitted objects under
`research/control/terminal_review_2026-10-01/`:
`successor/{DAILY_ADMISSION_MATRIX, M1_OPERATIVE_UPDATE,
OWNER_DECISION_TABLE, SUCCESSOR_PLAN_DRAFT, RULE_SLATE, GATING_VS_SIZING}.md`
(+ the REV-3 DELTA appended to the matrix at 11:17, after the first
sessions) and `DECISION_PACKET.md` §13 erratum. Read-only except this one
file; every finding below carries its evidence. Verification tool: repo
`.venv/bin/python`; lane evidence via `git show cbae7556:…` / `d722f5d5:…`;
probe evidence via `git show 87e65f00:…`; journals read in place under
`…/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/ARMS/`.

**Overall: the package is overwhelmingly faithful to its cited evidence —
two dozen spot-checked cells reproduce exactly; the calendar arithmetic,
the at-par currency identity, the par anchors and the pooled-flip
arithmetic all re-verify. Three defects rise above cosmetic: (A) the
converted-DD claim that carries the erratum's "verdict survives under
every convention" sentence is not recomputable from committed evidence and
my two rough replays invert its ordering; (B) the attribution-not-ablation
fixes are half-applied while the audit note still says "files NOT edited";
(C) the owner decision table calls the M1 collection protocol "live" under
"no owner input needed" although the protocol's own section says it is a
draft for owner registration with an owner-named source. Verdict at end.**

---

## 1. DAILY_ADMISSION_MATRIX — cells vs artifacts (24 cells checked)

### 1.1 Verified exact (citation real, value matches)

| # | cell | artifact | result |
|---|---|---|---|
| 1 | NZDUSD panel 1553 d/side 2020-10-02→2026-09-30, 0 holes >5d, max gap 4d, sha `c681402b…` | `IDENTITY_FREEZE…json@87e65f00` `assets.NZDUSD` (`aggregate.sha256` = c681402b03e5…, per-side n_days 1553, hole_count 0, max_calendar_gap 4) | MATCH |
| 2 | NZDUSD spread p50 0.88 / p90 18.65 / max 239.07 bps (n=1553) | same `spread_daily` (0.8822/18.6544/239.0719, n 1553) | MATCH |
| 3 | USDCHF sha `7fbd3a80…`; spread 4.51/16.02/216.10; conId 12087820 | same (`7fbd3a80e641…`, 4.5124/16.0242/216.096; conId 12087820) | MATCH |
| 4 | XAUUSD 1544 d/side; sha `02445884…`; spread 5.52/18.61/74.17 n=1543 + 2025-05-23 crossed-book exclusion; conId 69067924 | same (`02445884c9b2…`, 5.5163/18.6133/74.1656 n=1543; caveat "1 day excluded by the a>=b rule: 2025-05-23 crossed book (BID 3361.0 > ASK 3359.78)") | MATCH |
| 5 | XAGUSD sha `492dfbc0…`; spread 10.35/40.83/162.81 (widest p50); conId 77124483 | same (`492dfbc0803…`, 10.3526/40.8256/162.8053) | MATCH |
| 6 | XAU TD overlap n=1531 (2020-10-02→2026-09-16), abs p50 3.2462 bps, signed mean +0.3359 USD, `pit_lag=ASSUMED_NEXT_BUSINESS_DAY`, `basis_acceptance=NOT_RUN_THRESHOLDS_UNFROZEN`, archive sha `49c2684e…`, F-2 finding | `IDENTITY_FREEZE…xau_overlap_vs_td_archive` (n_aligned 1531, first/last, 3.2462, 0.3359, statuses, archive_sha256 49c2684e…, F-2 text) | MATCH |
| 7 | Basis p50s: NZDUSD FRED 9.38 / ECB 21.52; USDCHF 9.32 / 18.43; σ 64.64 / 49.62 bps | `XCHECK_REPORT.json@cbae7556` (`overlaps` abs_p50_bps 9.3832/21.5229/9.3214/18.4347; `panel_volatility` 64.6388/49.615) | MATCH |
| 8 | Coverage: NZD/CHF FRED 96.01% / ECB 98.71%, isolation 1 d (2022-12-26), streak 1552; XAU TD 99.22%, 12 isolation days (2025-04-15/16 + 2026-09-17→09-30), streak 1531; XAG "n/a — no archive exists" | `COVERAGE_REPORT.json@cbae7556` `assets.*` (all values incl. the exact 12 XAU isolation dates; XAU tail post-archive-end since TD ends 2026-09-16) | MATCH |
| 9 | EIA spans/covers: RBRTE 1512d / 97.55%; RWTC 1494d / 97.9%; RNGWHHD 1496d / 98.03%; mirror equality 1511/1511, 1492/1492, 1496/1496 max diff 0.0 | `COVERAGE_REPORT` `archives.EIA_spot` + `XCHECK` `mirror_value_equality` | MATCH |
| 10 | Flat-by-year: BRENT 100/100/100/95.3/57.9/0; WTI …98.1 2023, 42.5 2024, 0 2025+; NG 100/97.2/87.4/39.3/0.4/0 | `COVERAGE_REPORT` `flat_ohlc_share_pct_by_year` | MATCH |
| 11 | Front spreads COIL 12.60/32.95/58.62 n=29; CL 3.23/4.43/5.02 n=30; NG 6.54/7.02/10.05 n=30; "last-30-D1-bars window to 2026-09-30", "front-month quotes only" | `COVERAGE_REPORT` `measurable_cost_addendum` (12.598/32.954/58.623 n29; 3.225/4.429/5.019 n30; 6.536/7.022/10.045 n30; `sample_window` "last 30 D1 bars to 2026-09-30") | MATCH |
| 12 | Expired months 16/16 unresolved, includeExpired empty details, prior err-200 shape | `d2_expired_month_resolution.json` sha `03e689cf…` in `MANIFEST_IBKR_RO.json@cbae7556` (12/12 files listed); commit cbae7556 message | MATCH |
| 13 | ADJUSTED_LAST divergences $1.73 (BRENT) / $1.11 first 2024-11-29 (WTI) / $0.057 first 2021-11-22 (NG), "tens of dollars" rejection | `ENERGY_ADJUSTED_ANALYSIS.json@cbae7556` `assets.*.adj_vs_trades` (1.73; 1.11/2024-11-29; 0.0567/2021-11-22) | MATCH |
| 14 | Entitlement: BRENT live 354; WTI 10168/no delayed; NG 354/10167; D4 re-probe technical NOT_RUN (hung, thread-guard) | `GATE_TABLE_7ASSETS.md@87e65f00` §BRENT/§WTI/§NATGAS + `AVAILABILITY_EVIDENCE.json@cbae7556` `channel_notes` | MATCH |
| 15 | CONTFUT conId echoes CLX6 304037511 / NGX26 269460170 | `ERRATUM_LABELS_2026-09-30.md@87e65f00` CONTFUT table | MATCH |
| 16 | Availability obs 1: same-evening closed + forming bar at 2026-09-30 22:52 ET, source `d1b_spot_metals_bid_channel.json` sha `5cde7f15…`; obs 7 ADJUSTED_LAST forming 10-01 at 02:51Z | `AVAILABILITY_EVIDENCE.json@cbae7556` observations 1–7 + `MANIFEST_IBKR_RO` (d1b sha 5cde7f15447…) | MATCH |
| 17 | FRED FX ≥3bd stale (ends 2026-09-25, 2 manifested obs), energy mirror 1bd (ends 09-29), EIA direct 1 obs through 09-29 | `AVAILABILITY_EVIDENCE` obs 3/4/5 + `FRED_STALENESS_POINT2.json` + `XCHECK` `retrieval_staleness` | MATCH |
| 18 | XAG browser paths: stooq "Access denied" 13-byte body to real browser; LBMA Cloudflare; TRANSCRIPT_DERIVED_RECORD class; SLV r 0.9827 proxy-class | `XAG_BROWSER_ATTEMPTS_2026-10-01.json@cbae7556` (verbatim) + `XCHECK` `proxies.XAGUSD_SLV` (r 0.982733) | MATCH |
| 19 | 7 candidate rows = LEG_RESOLUTION lines 34/63/83/99/149/163/167, all `BLOCKED pending plan amendment`; family/horizon labels; rows 3–7 FAMILY_HISTORY_NEGATIVE, 2–7 PRIOR_NOT_SCORED | `LEG_RESOLUTION_MATRIX.tsv@87e65f00` | MATCH |
| 20 | §3 leg census: S065/S090/S063(EUR)/S062/S081/S089/S005/S098/S084/S065(USDCAD)/S068/S058/S031 all exist; NZD-S068/EUR-S058/USDCAD-S031 carry `NEEDS_MACRO_PIT_UNEVIDENCED` (pit_class col); S084 INTRADAY; S063 JKM-proxy bias disclosed in-rule | `PORTFOLIO_ELIGIBILITY_1200.tsv@87e65f00` + corpus `symbols/USDJPY.md` S65 ("NATGAS (HH) là proxy lệch cho JKM") | MATCH |
| 21 | Signal-only WTI consumers USDCAD-S001/S008/S013/S017/S063 on G-PIT-V3; short-WTI execution legs S062/S081/S089; curve rows S005 (CL1–CL6)/S098; AECO/TTF non-IBKR | `GATE_TABLE_7ASSETS.md@87e65f00` §WTI/§NATGAS | MATCH |
| 22 | Futures footer quote "no honest amendment scope exists until the chain source is named" | `GATE_TABLE_7ASSETS.md@87e65f00` §BRENT footer (verbatim) | MATCH |
| 23 | CONTFUT boundary discrepancy: DRAFT §5 "not admitted before 2023 (BRENT/WTI) / late-2022 (NATGAS)" vs skeptic-corrected 2025-01-01 / 2024-01-01 | `DRAFT_AMENDMENT_SUCCESSOR.md@cbae7556` §5 line 76 (2023/late-2022) vs `SESSION_REPORT.md@cbae7556` rev-2 item 4 ("corrected to 2025-01-01 … / 2024-01-01") — and the flat-by-year table supports the correction | ACCURATE (discrepancy real; correctly carried to D-DAILY-9) |
| 24 | Corpus rule text S81 / S100 / S63 / S83 / S6 / S61 / S85 quotes (mechanisms, thresholds, exits) | `FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/{AUDUSD,USDJPY,EURUSD}.md` | MATCH |

### 1.2 Signal-vs-vehicle discipline

Held throughout. Matrix A separates signal price from execution vehicle
per asset (energy rows explicitly `signal PASS / execution FAIL`); Matrix B
verdicts are a conditional class (`ADMITTABLE-AS` = measured inputs +
executable-class vehicle, admission still requiring the named owner action
+ registration), every candidate row names its single missing item, the
status header repeats "every candidate below remains BLOCKED until a
registered successor amendment carries it", and §2 states the XAU
signal-side-only reading for S063/S100 in plain words. No candidate is
admitted on inference; joint verdicts of all 7 are consistent with their
signal + vehicle rows (checked individually). The futures-block statement
(§4) matches the lane's measurements: 16/16 expired months, ADJUSTED_LAST
divergence ≤$1.73/6y = not a chain, entitlement FAIL, costs only a 29–30d
front sample — plus the flat-OHLC disqualifier and the frozen-position
footer quote. The energy §3 verdicts correctly separate EIA-clearable
signal legs, TTF/AECO/macro-blocked legs, and short-WTI execution legs.

### 1.3 Findings — DAILY matrix

- **[MINOR] F-D1 — wrong sha digit for the roll-check artifact.** The
  matrix cites `d5_contfut_details_rollcheck.json` sha `ee853636…` in two
  places (§1 BRENT vehicle cell; §4 item 2). `MANIFEST_IBKR_RO.json@cbae7556`
  gives `ee85363b52a018f1…`. Wrong 8th hex char; the file name is right.
  Fix: `ee853636` → `ee85363b` (2 occurrences).
- **[MINOR] F-D2 — REV-3 DELTA item 3 misattributes the corrected
  boundary's source.** The delta states the law "CONTFUT not admissible
  … before 2025-01-01 (BRENT/WTI) / 2024-01-01 (NATGAS)" citing
  `(DRAFT_AMENDMENT_SUCCESSOR.md)` — but the draft **@d722f5d5 still says
  "before 2023 / late-2022"** (§5, unchanged by lane rev 3; not in its
  changed-file list). The corrected law text lives in
  `HANDOFF_TO_PORTFOLIO_CHAT.md@d722f5d5` (lines 41–42) and the
  proxies/CONTFUT/EIA-never-executable law in `OWNER_INPUT_CHECKLIST.md`
  header. Fix the parenthetical to cite those two.
- **[MINOR] F-D3 — superseded body cells after the REV-3 append.** §1's
  "next-day persistence PREPARED_NOT_RUN" cells and D-DAILY-1 ("Execute
  the prepared availability point-2 re-run") are now superseded by REV-3
  item 1 (point-2 EXECUTED 2026-10-01T04:00:32Z, class
  `PERSISTENCE_PRESENCE_MEASURED_2pts` — verified in
  `AVAILABILITY_EVIDENCE.json@d722f5d5`). A reader of §6 alone would act
  on a completed item. Fix: annotate D-DAILY-1
  "[EXECUTED by lane rev-3 — see REV-3 DELTA 1]".
- **[INFO] F-D4 — XAU TD p95 differs across artifacts.** Matrix quotes
  p95 26.5142 (IDENTITY_FREEZE value) while session-2 `XCHECK` shows
  26.5549 (p50 3.2462 matches both exactly). Immaterial; cite the freeze
  explicitly for p95.
- **[INFO] F-D5 — S63 gold-leg nuance.** Corpus S63's trade line is
  "short USDJPY beta-weighted với long gold đã có (hedge completion)" —
  i.e. hedge-completion against an *already-held* gold long. The matrix's
  "gold is NOT the traded vehicle" reading matches the lane's row note and
  is defensible, but the corpus→config translation should state that the
  rule books no gold leg of its own.

---

## 2. M1_OPERATIVE_UPDATE — no-unseal arithmetic

### 2.1 Verified

- **Sealed tail**: `stagec/VERIFY.json` in the worktree
  (`.worktrees/portfolio-composite-12assets-100k-v1/integration/…/stagec/`)
  says `sealed_tail: ["2026-01-02","2026-06-26"]` — exact match to §1.1.
- **Anchor dates (recomputed with .venv python)**: never-scored segment
  2025-12-27→2026-09-23 = 270 d = 38.57 w ✓; seal = 175 d = 25.0 w exactly ✓
  (the file's artifact-correction flag — RULE_SLATE §4.1/CAM §3 say
  "26-week sealed tail" — is right: CAM §3 verbatim says "remaining
  26-week sealed tail"); unsealed stock 2026-06-27→2026-09-23 = 88 d =
  12.57 w ✓; sliver 5 d ✓ (date-difference convention; see INFO F-M4).
  poolB `audit_summary.json`: M1 panels last tradable 2026-09-23T23:59Z,
  span 2092 d, 1,440 rec/day ✓. CAM §3 window 2021-01-08→2026-06-26 ✓;
  H1_PANELS.json 2021-01-03→2026-06-30, `read_only: true` ✓.
- **N1 (recommended)**: LEARN 2026-06-27+182 = **2026-12-26** ✓; fold 1 =
  +7 = **2027-01-02** ✓; readable = +182 = **2027-07-03** ✓; battery =
  +1092 = **2029-12-29** ✓; strict variant 88+94 fresh ⇒ LEARN end
  **2027-01-02**, fold 1 2027-01-09, readable 2027-07-10, battery
  **2030-01-05** ✓; completeness 175/182 = 96.2% ✓ (88 stock + 87 fresh
  from 2026-10-01, 7-day hole typed).
- **N2**: as-written LEARN 2026-09-24+182 = 2027-03-25 ✓ (slate's 03-24 =
  181 d, one day short — the correction is right); fold 1 2027-04-01,
  readable 2027-09-30, battery 2030-03-28 ✓; concrete from 2026-10-01:
  LEARN 2026-10-01→2027-04-01, fold 1 2027-04-08, readable 2027-10-07,
  battery 2030-04-04 ✓.
- **Reference unseal variant**: fold 1 2026-09-30, readable 2027-03-31,
  battery 2029-09-26 ✓ (reproduces RULE_SLATE §6 exactly, as claimed).
  "Mid-2027 unattainable": 2026-06-27→2027-06-30 = 368 d = 52.6 w = 2.02
  folds < 6 ✓.
- **§3.4 replacement**: the text now in SUCCESSOR_PLAN_DRAFT §3 item 4
  matches M1_OPERATIVE §1.4 verbatim-in-substance — every operative date,
  the seal statement, the 88 d / 7-day-hole disclosures, the strict
  alternative, the supersession clause, USDCAD/AUDUSD NOT_RUN, the
  daily-track caveat and the mid-2027 sentence all agree; it supersedes
  cleanly (the plan drops only the superseded variants' parenthetical
  detail, which M1 §1.3/§1.4 retain).

### 2.2 Findings — M1 calendar

- **[MINOR] F-M1 — no-LEARN corner battery date is 7 days wrong.** §1.3:
  "folds start immediately 2026-06-27 … battery complete 2029-06-30".
  2026-06-27 + 1,092 d = **2029-06-23** (recomputed; the file's own
  formula). The corner is explicitly NOT recommended, but the date as
  printed is not any variant's arithmetic. Fix: `2029-06-30` → `2029-06-23`.
- **[INFO] F-M4 — boundary-day accounting.** The §1.1 decomposition
  5 + 175 + 88 = 268 ≠ 270: two transition days (2026-01-01 and the
  06-26/06-27 seam) fall outside the three quoted date-difference spans.
  Each number is individually correct under the file's convention and the
  sliver is explicitly called non-contiguous/immaterial — no fix required,
  noted for completeness.

---

## 3. Currency finding (M1_OPERATIVE §3 + DECISION_PACKET §13)

### 3.1 Verified exact (independent recomputation from the journals)

- **At-par identity — re-verified on 100% of USDJPY fills, not just 50**:
  `cash_delta_usd = −(delta_units × fill_price) − commission_usd` holds
  with worst residual **0.0000000000** on all **1,526 POLICY + 1,309 B1 =
  2,835 rows** (both arms, parsed in full). The §3.1 example reproduces
  verbatim (POLICY seq 2412, 2022-01-07T16:00Z, −10,000 @ 115.63 →
  +1,156,299.65 = 10,000×115.63 − 0.35).
- **Swap convention**: implied-rate/last-mid ratio p50 **1.0005** / p95
  **1.006** (POLICY; B1 1.0003/1.0055); Wednesday swap/unit p50
  0.000204 vs non-Wed 0.000068 = **exactly ×3**. Commission = 3.5e-05
  per unit (0.35 per 10k) on every fill. Fill mids span
  113.6775–161.814 ✓.
- **Par anchors**: window nets **600,082.92 / 687,284.31** recomputed from
  journals (Σfills − Σswaps) ✓; all 8 per-fold USDJPY nets match metrics
  to the cent (540,319.38 / −150,957.64 / 21,369.13 / −78,342.41 /
  209,981.98 / 74,220.88 / −231,317.85 / 214,809.45) ✓; harm
  −87,201.39 ✓; per-fold harm signs 0,−,−,−,+,+,−,+ ✓ incl. fold-7
  +3,677.13 par ✓. **Pooled par DDs reproduced to the cent by my own
  weekly-chain replay** (418,227.97 / 397,156.85 — identical to
  metrics.json), which also validates the mark-chain construction.
- **Pooled-flip arithmetic — internally exact**: POLICY converted
  5,670.63 / 5,817.59 = (EUR 2,315.24 + GBP 942.44 = 3,257.68) +
  2,412.95 / 2,559.91 ✓; B1 4,502.47 / 4,931.09 = (600.97 + 718.75 =
  1,319.72) + 3,182.75 / 3,611.36 ✓; converted pooled harm +1,168.16 /
  +886.50 POLICY-favorable ✓; EUR+GBP true-USD edge 1,937.96 =
  1,714.26 + 223.70 ✓. Per-unit illustrations (NY bucket, L6, 29 defers,
  c=239.54, median winner, friction) all recompute exactly under
  ÷161.81/÷113.68 ✓. Per-fold converted column sums to the stated window
  figure (2,561 ≈ 2,559.91 at quoted rounding) ✓.
- **Erratum does not edit frozen artifacts** ✓: the working-tree diff
  touches only DECISION_PACKET.md (two attribution rewordings + the §13
  append) and the three successor files; no cycle/terminal/registry/ledger
  file modified.

### 3.2 Findings — currency

- **[MAJOR — the one load-bearing gap] F-C1 — the converted weekly DD
  (6,439.67 vs 5,270.49) is not recomputable from committed evidence, and
  my rough replays invert its ordering.** DECISION_PACKET §13 item 2 and
  M1 §3.3 assert "the P1 DD leg fails under every convention (6,440 vs
  5,270 converted)". The chain/routine that produced these numbers is not
  on file (the session's only artifact is the .md itself; M1's own §3.3
  applies "[NR] not recomputable from committed aggregates" to the B4
  ranking but not to this). I built two independent mark-time replays from
  the committed journals/metrics — both reproduce the par pooled DD to the
  cent — and got converted pooled DDs of **POLICY 3,275 / B1 4,658** and
  (different fold-edge convention) **POLICY 34,387 / B1 60,543**: in both,
  POLICY < B1, i.e. the opposite ordering, under which the DD leg would
  NOT fail and the erratum's verdict-preservation argument would not go
  through as stated. My replays are admittedly cruder than the described
  routine (weekend force-flat assignment, fallback marks), so this is not
  proof the claim is wrong — but under workspace law a universal claim
  ("every convention") resting on an unpublished routine fails the
  evidence bar, and the ordering is exactly the sensitive part (a path
  statistic over a mixed-convention sum). Rough magnitude check: par DD
  ÷161.81–÷113.68 gives 2,585–3,678 USD; the claimed 6,440 is ~1.7–2.5×
  above the naive band — possible with rate-move MTM on the JPY liability,
  but only the chain can show it. **Minimal fix (choose one):**
  (i) publish the converted weekly chain (dates, both arms, both
  conventions) as an appendix to M1 §3.2 or a sibling artifact — the
  par-side validation already exists; or (ii) reword DP §13 item 2 and
  M1 §3.3 to scope the claim: "under the described mark-time conversion
  routine the DD leg fails (6,439.67 > 5,270.49; routine validated by
  cent-exact par reproduction, chain not independently recomputable from
  committed aggregates); the par-convention DD leg fails exactly" —
  deleting "under every convention". The same applies to the P7 converted
  fold-0 share "84%" (the par 89.7% = 541,483.96/603,340.60 verifies; the
  84% needs the unpublished chain).
- **[MINOR] F-C2 — effective-ratio band mis-stated in M1 §3.2.**
  "effective window ratios 216–249×": the four ratios are 248.7 / 234.4
  (POLICY) and 216.0 / **190.3** (B1 single-end-rate). Actual band
  190–249×. (DECISION_PACKET §13's "~190–250×" already has it right.)
  Fix: `216–249` → `190–249` in M1 §3.2.
- Everything else in §3/§13 — the identity, both coexisting conventions,
  the within-symbol invariance claim (7/8 fold-sign matches, fold-7 flip
  sub-noise — recomputed), the pooled flip, the AND-semantics reasoning,
  the successor-engine REQUIRED item — verifies.

---

## 4. Attribution fixes (RULE_SLATE / GATING / DECISION_PACKET)

Diff vs `87e65f00` shows exactly four applied edits, all faithful to
M1_OPERATIVE §2.1's proposals:

- DP §2.3(a): "deferrals were net HARMFUL" → "deferrals' B1-path
  attribution was net-negative … (attribution, not ablation)" ✓
- DP §11.1: "guard HARMFUL window-wide" → "carried a negative B1-path
  attribution window-wide (attribution, not ablation)" ✓
- GATING §9.2: "is the single largest identified harm mechanism" →
  "carries the single largest attributed harm block (attribution, not
  ablation)" ✓
- RULE_SLATE SU-RS-J3 measured prior: leave-29-out DD numbers now tagged
  "[leave-29-out on B1's realized path = attribution; not evidence that
  relaxing the guard causes these outcomes on any other path]" ✓

**[MAJOR] F-A1 — half-applied fix set + stale audit note.** The other four
fixes M1_OPERATIVE §2.1 itself lists were NOT applied, and the named
causal-sounding lines remain:

1. `RULE_SLATE.md:53` (§1 row 5): "Large measured **leakage** (+274.6k
   journal units)" — untagged.
2. `RULE_SLATE.md:146–148` (SU-RS-J3 disclosure): "the **leakage** is the
   largest single measured block of the USDJPY harm" — untagged.
3. `RULE_SLATE.md:102–105` (SU-RS-J1 measured prior): "blocking removes 50
   losers … maxDD −412,208.31 → −359,621.76" — realized-path arithmetic
   with no path-attribution tag (the exact class §2.1 flagged).
4. `GATING_VS_SIZING.md:249–251`: the proposed append after "…skips
   winners in trends." ("all guard numbers are attributions on the
   realized exposed paths; §8.4's no-counterfactual ban applies") — not
   appended.

Grep confirms: 'leakage' → RULE_SLATE 53/147 only; 'causes' → only inside
the correct tag (RULE_SLATE 151) and DP's unrelated "root-caused";
'removing them worsens' → now tagged; remaining 'worsens' hits are
prospective anti-hypothesis clauses (legitimate). Meanwhile M1 §2.1 still
reads "(fixes listed; files **NOT edited**)" — stale: four were applied
after M1 was written (mtimes 11:05 vs M1 11:02). **Minimal fix**: apply
the four remaining fixes verbatim from M1 §2.1 and update the §2.1
parenthetical to "fixes applied in session 3" (preferred — the owner
demanded this discipline and the slate table is what consumers quote); or,
if the intent was analyst-proposes-only, revert the four applied edits —
but do not leave half a fix set with a note claiming none.

**[INFO] F-A2.** DP §11.1 "blocking NY longs is the ONLY PnL- and
DD-consistent off-rule (+281k avoided, DD −412k→−360k)" is the same
attribution shape as RULE_SLATE J1; if J1 gets the tag, this line merits
the same one.

---

## 5. OWNER_DECISION_TABLE (11:17 version, OI-1..OI-6)

Verified: the OI rows faithfully compress the lane's
`OWNER_INPUT_CHECKLIST.md@d722f5d5` (OI-1 (a)/(b) + σ-law; OI-2 statement
as the only unmeasured cost; OI-3 XAU pin sha `49c2684e…`; OI-4 XAG
(a)–(d); OI-5 chain + subscriptions + AECO/TTF; OI-6 registration) — all
match the checklist's substance; OI-1 correctly folds in the now-measured
point-2. N1 dates and M1-CAL match M1_OPERATIVE exactly. "verbatim" is a
slight stretch (rows are compressed) but nothing is distorted. No
GO-consumable language ("GOs DEAD"; GO typed at the future cycle's own
gate). One-action discipline holds per row except as noted.

Findings:

- **[MAJOR] F-O1 — "collection protocol live" under "no owner input
  needed".** Section "What can be done NOW" item 2 states the M1
  collection protocol is live. M1 §5 says the opposite: "Protocol spec
  (draft for owner registration; nothing runs from this file)"; the
  primary channel needs an **owner-named** M1 source (Dukascopy-precedent
  weekly refresh); the secondary "extended continuous 7497 session" is a
  change to the SIXSOURCE collector lane's bounded-window design. As
  printed, the owner is told lawful accumulation toward the 2026-12-26
  LEARN end can proceed without them. Fix (one line): "M1-track: activate
  the collection protocol per M1_OPERATIVE_UPDATE §5 once you name the M1
  source (and authorize the 7497 extension) — protocol staged, NOT live;
  seal boundary hard-enforced."
- **[MINOR] F-O2 — N2 row mixes the two N2 sub-variants.** "LEARN
  2026-09-24→2027-03-25 | 2027-04-08 | 2030-04-04": the LEARN dates are
  the as-written corrected variant, whose fold 1 / battery are
  **2027-04-01 / 2030-03-28**; 2027-04-08 / 2030-04-04 belong to the
  concrete from-2026-10-01 variant, whose LEARN is **2026-10-01→
  2027-04-01**. Fix to one consistent row, e.g. "2026-10-01→2027-04-01 |
  2027-04-08 | 2030-04-04" (concrete) or "2026-09-24→2027-03-25 |
  2027-04-01 | 2030-03-28" (as-written).
- **[MINOR] F-O3 — dangling id: "NOT_RUN (per D-4 recommendation)".** The
  table renamed the collector item to M1-D; the validation row still cites
  the old D-4 (which in the lane packet means the energy chain). Fix:
  "per M1-D recommendation".
- **[MINOR] F-O4 — "all 4 legs measured FAIL" (Futures execution row).**
  The four chain-law items are: per-month history FAIL, roll FAIL,
  entitlement FAIL, costs **NOT_RUN** (matrix §4 item 4) — and there are
  three energy assets, not four legs. Fix: "chain law unmet on every leg
  (3× measured FAIL + costs NOT_RUN)".
- **[MINOR] F-O5 — "feasible TODAY" caveat not present inline.** The DAILY
  validation row says "on registration + 8 test folds (feasible TODAY)"
  without the condition; OWNER_PACKET_SUCCESSOR (2) bolds the correct
  form ("conditional on data-lane gates + your D-1..D-7"), and the OI
  table implies it, but the row an owner will quote should carry it. Fix:
  append "— conditional on OI-1 (PIT law) + registration; costs fail-closed
  until OI-2".
- **[INFO] F-O6.** OI-1 bundles two declarations (availability semantics +
  σ-law threshold freeze) that the matrix carried as two separate
  one-action items (D-DAILY-2/D-DAILY-3); inherited from the lane's
  checklist, noted for the one-action ledger.

---

## 6. Cross-file consistency + boundaries

- **Data lane**: branch `orca/pc12a-7asset-unblock-20261001` advanced to
  `d722f5d5` at 11:09:25 — by the lane's own session 3 (its own worktree,
  clean; commit message lane-voiced). The review objects were all written
  before 11:09 except the two 11:17 updates (matrix REV-3 DELTA + decision
  table OI rewrite), which correctly integrate @d722f5d5 read-only. No
  review object wrote to the lane; the matrix's pinned @cbae7556
  citations remain valid as evidence pins. D-DAILY-1 staleness handled as
  F-D3.
- **TERMINAL cycles / registry**: PC12A worktree clean at `c93123db`
  (TERMINAL commit; matches registry per DP §1); `plans/CYCLE_REGISTRY.json`
  has no working-tree diff; no writes to either cycle's control plane in
  git status.
- **Owner dirty tree**: exactly the documented set (SIXSOURCE ibkr_fx ×3,
  SANDBOX ×2, SLEEVE-FX5) — untouched.
- **Session writes**: confined to `terminal_review_2026-10-01/`
  (4 modified + 3 new successor files) plus this skeptic file. No network,
  no S1, no scored computation, no lock contention in any object's claims.
- Internal consistency: M1 ↔ PLAN §3.4 ↔ decision-table N1/M1-CAL dates
  agree; matrix ↔ decision table ↔ lane checklist OI items agree; the
  energy/futures-block statements agree across matrix §4, decision table
  footer row and the lane footer. The EXPOSED-window start 2021-01-08
  (M1/PLAN) matches CAM §3 ✓.

---

## Verdict

**VERDICT: FIX_THEN_COMMIT.**

The evidence base is strong — of ~30 spot checks across both tracks, all
but one citation-digit reproduce exactly, the no-unseal calendar
recomputes date-for-date, and the currency identity/par-anchor/pooled-flip
work re-verifies to the cent on the full fill population. The package is
committable once these are discharged:

**Must fix before commit (3 MAJOR):**

1. **F-C1** (erratum evidence bar): publish the converted weekly DD chain
   or scope DP §13 item 2 + M1 §3.3 to remove "under every convention"
   (exact replacement wording provided in §3.2 above). The ordering
   POLICY>B1 is the load-bearing, non-reproducible part; my two
   cent-validated par replays both suggest the opposite ordering.
2. **F-A1** (attribution consistency): apply the four remaining fixes
   verbatim from M1_OPERATIVE §2.1 (RULE_SLATE 53, 146–148, 102–105;
   GATING 249–251) and update M1 §2.1's "files NOT edited" parenthetical.
3. **F-O1** (owner-facing authority): reword decision-table "NOW" item 2 —
   the collection protocol is staged/draft, not live, and needs the
   owner-named source.

**Fix in the same pass (7 MINOR):** F-D1 (sha ee853636→ee85363b ×2),
F-D2 (REV-3 item 3 source → HANDOFF/checklist), F-D3 (mark D-DAILY-1
executed), F-M1 (2029-06-30→2029-06-23), F-C2 (216–249→190–249), F-O2 (N2
row unmix), F-O3/F-O4/F-O5 (D-4→M1-D; "4 legs FAIL" reword; feasible-TODAY
caveat).

**No action (INFO):** F-D4, F-D5, F-M4, F-A2, F-O6.

— end of skeptic file —
