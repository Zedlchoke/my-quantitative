# CARRIED_STATUS — GC + SI baseline families, round FUTURES-TEN-HYPO-PREP-20261004 (lane COMM-ME)

- Task: **FUTURES-TEN-HYPO-PREP-20261004**, lane **COMM-ME** (symbols GC, SI).
  Generated 2026-10-04 UTC. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-ten-hypo/prep`
  @ HEAD `a4a882658e09092b5b282b666b30a3cfc5ac3418` (single permitted
  `git rev-parse HEAD`, == dispatch base_sha), branch
  `prep/futures-ten-hypo-20261004`. Root checkout read-only authority:
  `research/control/FUTURES-DATA-10SYMS-V1/**` cited at **root main
  `d8cf8eca300d9eadc703f0d99629bec79102b325`**.
- Class: CARRIED-family status update. **0 PnL, 0 returns, 0 scored runs;
  every scored status is NOT_RUN_DATA_ABSENT (no vendor O1M panel for GC/SI
  — dispatch standing ruling, restated never reopened). Every parameter
  [PROVISIONAL]. Missing evidence is NOT_RUN, never PASS.**
- Baseline ancestry: all four families + SI-F3 construction law carried from
  `research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/comm/COMM_HYPOTHESES.md`
  (984 lines, §3-§4 + §0 + §5-§7). Its 24-artifact hash register
  (`hypo/comm/captures/source_sha256.tsv`) was **re-verified this lane
  BEFORE any fetch: all 24 of 24 rows re-hashed byte-exact** (GC_DOSSIER
  3231d3a0…, SI_DOSSIER a15e5e23…, FEES_CORRECTED 006d6372…, FXCOMM
  0de05fa5…, COMM_CALENDAR adcd3b54…, PLAYBOOKS 7610ed3c…, DATACONTRACT
  df175a2d…, tidy parquets, exemplar raw files incl. GC_GCZ6 c95a6db2…,
  SI_SIZ6 5a594f7d… and the CL/NG exemplars f0b47fef…/9d7755d2…, vendor
  AV1T metadata d431a38d…). Register rows cite paths in the
  **P3-quarantined**
  `futures-behavior/prep` worktree — **that worktree was NOT touched**;
  re-verification hashed the byte-identical committed copies in this
  worktree and the home data dirs.
- New primary-source captures made this lane (7 persisted + route-provenance
  captures; full log `fetch_log.jsonl`, hashes `SHA256SUMS_lane.txt`):
  COT landing (Friday-3:30pm-ET release clock verbatim), legacy CMX report
  (GC Code-088691 / SI Code-084691 as of 2026-09-29), disaggregated
  futures-only current report, disaggregated explanatory notes (money-manager
  definition verbatim), LBMA prices page (auction clocks verbatim + IBA
  licence wall verbatim), Treasury daily real-yield table 2026 YTD (190
  rows, free), WGC research landing (quarterly GDT cadence), Silver
  Institute landing. LBMA transport was OPEN via browser-UA curl this lane
  (prior-lane bot-block not reproduced); the **data tables remain
  sign-in/licence-gated — the wall itself captured verbatim**.

---

## 1. Standing posture (inherited, restated once, unchanged)

1. **No registration path**: GC/SI = NOT_QUALIFIED_V2 (DATACONTRACT
   QUALIFICATION §2, sha256 df175a2d…) + COMMODITIES aggregate **54 minimal
   > 24 ⇒ BLOCKED_TRIAL_BUDGET** on any single-cycle attempt (CENSUS_FINAL
   COMM row; COMM RI §3). No GO_REGISTER/GO_SCORE/GO_ORDER. D1–D12 all open;
   no lane self-ratifies.
2. **Cost law**: MODELED only. Fees 0.85 commission + exchange per-product
   **NOT_FETCHED** (CME BLOCKED_HTTP_403 — root FINAL_REPORT §cme_check +
   costs/IBKR_futures_commissions_2026-10-02.json; only ES carries an
   official exchange example 1.38); corrected all-in GC/SI **2.51 USD/side
   T1** [OBSERVED, FEES_CORRECTED §2, UNDER REVIEW; VERIFIED_VS_ACCOUNT
   NOT_RUN]. Spread proxies = close-proxy full spreads halved (high-biased,
   non-synchronous; BBO NOT_RUN per D5 law). "Measured/complete cost"
   FORBIDDEN.
3. **Era laws**: 14-month program front true-volume (2025-08→2026-10, root
   FINAL_REPORT) with the comm-lane specific chains GC 424 returns
   2025-01-15→2026-10-01 and SI 316 days 2025-07-01→2026-10-01 [OBSERVED,
   COMM_HYPOTHESES §0.3]; **settlement-derived bar law**: per-contract daily
   bars beyond ~1 yr of contract life are close-only v=0 (root FINAL_REPORT
   finding 3) — reference/signal grade, NEVER fills. **SI identity law**:
   tradingClass SI = 5,000 oz (SIL 1,000 oz is a different contract — root
   S1_IDENTITY + FINAL_REPORT finding 7). Roll rule PIT-legal declared (root
   FINAL_REPORT §roll: hold to last session before delivery-month day-1,
   switch at that close; decide at close t, effective t+1). SI cost floor
   honesty: **SI front median spread 4.5 ticks = $112.50 is the largest in
   the 10-symbol program** [OBSERVED, root S6_FRONT_SPREADS.json:SI].
4. **Ancestry re-verification this lane** (all 173 rows of
   `research/wayfinder/FAMILY_FAILURES.jsonl` scanned): the 3 commodities
   rows are COMMNG1-A4-P2-ARM1/2/3 (SCORED_REJECTION,
   CONTROL_OUT_EARNS_RELEASE_CLOCK — an NG release-clock class, not a
   curve/beta/positioning class); beta/vol-class neighbors BAB-LOWBETA
   (COST_DOMINATED), DT100-71-RVREGIME / DT100-73-VOLAUTO /
   DT100-74-VOLTARGET (NEGATIVE_EXPECTANCY), DT100-75-PAIRMR /
   DT100-79-ETHBTC (pair/ratio classes), DT100-78-LEADLAG. None of the four
   carried families is a rename of any dead row (re-adjudicated, verdicts
   unchanged — table in HYPOTHESES_COMM_ME_R3.md §4).

## 2. Updated data posture (a) baseline "no path (NQV2)" vs (b) root IBKR corpus

**(a) vs baseline** (`COMM_HYPOTHESES.md` §0, @72c9bc5b lineage): unchanged
in law. The baseline's "price history = 14–22 months IBKR legacy +
settlement-derived deferred marks" is now the independently verified root
corpus (below); no qualification upgrade is claimed; scored statuses remain
NOT_RUN_DATA_ABSENT because the blocker is **depth + intraday + OI**, none
of which this round added.

**(b) vs root corpus** (`research/control/FUTURES-DATA-10SYMS-V1/`, root
main d8cf8eca…; S9 independent verify PASS 7/7; manifest sha256 5e8e2b77…,
1,160 files, 36,463,541 B):

| item | GC | SI | source (root) |
|---|---|---|---|
| Daily per-contract depth | from **2019-12** (22 contracts, 6 expired) | from **2020-12** (22 contracts, 6 expired) | FINAL_REPORT table; S1_IDENTITY |
| Bar law beyond ~1yr of life | settlement-derived (close-only, v=0) | same | FINAL_REPORT finding 3; S7 v0 shares |
| Front true-volume | ~14 months (root walk-back 2025-08→2026-10); comm chain 424 returns from 2025-01-15 | ~14 months; cycle chain 316 days from 2025-07-01 | FINAL_REPORT; COMM_HYPOTHESES §0.3 |
| Intraday | H1 ~2025-11, M1 ~2025-12 (~10 months) | H1 ~2025-12, M1 ~2025-12 (~10 months) | FINAL_REPORT finding 4; S7_DEPTH_ACTIVE.json (GC M1 probe 2,655 bars first 2025-12-22; SI M1 probe 1,341 bars first 2025-12-22) |
| Front spread (close-proxy median, n=20) | **5.0 ticks = $50** (GCV6; p90 $80) | **4.5 ticks = $112.50** (SIV6; p90 $147.50) — program max | S6_FRONT_SPREADS.json |
| BID/ASK daily 1Y | present | present; **1 crossed day / 251** (all other symbols 0) | FINAL_REPORT cost row |
| Margins (public, 2 sources <2% drift) | ~$22,391 maint / $24,630.10 init (NT 2026-08-31); AMP $24,249 | ~$33,498 maint / $36,847.80 init (NT); AMP $35,641 | costs/SPECS_MARGINS_PUBLIC_2026-10-02.md §3 |
| Contract specs (captured) | 100 troy oz, tick 0.10 = $10, cycle G/J/M/Q/V/Z (AMP) + NT listing-depth text, LTD 13:30 ET (=12:30 CT) 3rd-last BD, physical | 5,000 troy oz (tradingClass SI), tick 0.005 = $25, AMP cycle F/H/K/N/U/Z + NT listing-depth text (measured liquid cycle H/K/N/U/Z; serials dead), LTD 13:25 ET (=12:25 CT) 3rd-last BD, physical | SPECS_MARGINS_PUBLIC §1 (NinjaTrader/AMP mirrors; CME rulebook CME_BLOCKED_TRANSPORT) |
| Fineness | **NOT_IN_ANY_CAPTURED_SPEC** (dispatch premise .995; delivery-grade text CME_BLOCKED_TRANSPORT — archive.org route proven but JS-shell, captures this lane) | same (premise .999, NOT_OBTAINED) | this lane captures cme_gold_markets_page_20260917.html (shell) + fetch_log seq 22/28 |

**Posture deltas vs the baseline's own cost table (declared, both kept):**
baseline SI half-spread proxy was the liquid-era pooled 4-tick $100
(SI_DOSSIER §3) ⇒ S2 $102.51/side; the root front median is 4.5 ticks
$112.50 ⇒ half-spread 56.25 ⇒ updated per-side tiers **S1/S2/S3 =
83.76 / 108.76 / 133.76 USD/side** [DERIVED: fees 2.51 + 56.25 +
slippage {1,2,3}×$25; MODELED, UNDER REVIEW, PROVISIONAL]. GC unchanged:
5-tick $50 reconciles S6 == GC_DOSSIER §3 ⇒ tiers 37.51/47.51/57.51. The
baseline SI numbers remain quoted in the baseline doc; any future packet
must carry BOTH bases and the S6 update, never silently pool them. The
crossed-book day (SI 1/251) is excluded from any spread median
recomputation, flagged, never dropped silently.

**Unchanged spec/calendar pointers (verify against captures, never memory):**
GC official last-trade dates Aug 2013→Dec 2023 (2024–26 NOT_OBTAINED);
SI Mar 2015→Dec 2022 (2023–26 NOT_OBTAINED); GC 12:30 CT vs SI 12:25 CT
cessation (official offset, 2 eras verbatim); holiday grid 2011–15/2017–23
with the binding EXCLUDE law; GC serial-months defect 2025-11→2026-09
(named $0 re-fetch unblock, NOT_RUN this lane); SI liquid cycle
H/K/N/U/Z with serials dead and S1-nearest ≠ liquidity front (SIV6 dead
book vs SIZ6 16.9k lots median).

## 3. Per-family carried status

### GC-F1 CURVE-COMPRESS — CARRIED, DATA-BLOCKED (scored NOT_RUN_DATA_ABSENT)
- Mechanism + anatomy: unchanged (contango 99.8–100% of sessions; median 2m
  spread ≈ −19..−24 USD/oz; 7 roll gaps +27.5..+37.3 ≈ 2m × ~16 USD/oz/mo
  incl. 2026-09-30 +31.1) [OBSERVED, GC_DOSSIER §1/§3, sha256 3231d3a0…].
  Conditional content NOT_RUN (~40 weekly real-volume curve obs; power
  NOT_RUN).
- Updated posture: curve conditioning variable (adjacent-cycle spreads) is
  computable on the verified corpus per-contract dailies (settlement-derived
  era flagged); rate-control leg hardened this lane — the official Treasury
  daily real-yield table is directly fetchable (free; 2026 YTD capture in
  hand) but remains a **measurement/control leg, NOT PIT-strict vintages**
  (FRED/ALFRED year-end law stands) ⇒ D4 stays 1-class. Serial re-fetch
  still the named cheap unblock; still NOT_RUN.
- Spec pointers unchanged (§2 table). Rank (3-axis baseline): tied 6.

### GC-F2 ROLL-MIGRATION — CARRIED, CONSTRUCTION-CLASS (T5; 0 IDs; never scored as alpha)
- Mechanism + anatomy: unchanged (volume crossover 1–2 sessions before the
  declared roll at 5/6 real-era rolls + 6th at roll; offsets −2,−2,−2,−2,−1;
  exemplar 2026-03-27 GCJ6 8,201 vs GCM6 82,091) [OBSERVED, GC_DOSSIER §1].
- Role A precedent: **construction ledger for RMM (FUTURES-SIX-ADOPT R2 §2),
  cite CENSUS_FINAL T5 rows: "GC-F2 ROLL-MIGRATION … construction
  (T5-class) … 0 … never scored as alpha … produces cost inputs" +
  "T5 construction/roll: NQ-F4 (Role B), GC-F2 = 4 + 0 = 4; Role A =
  standing law, 0 IDs"** [OBSERVED, synth/CENSUS_FINAL.md T5 section].
- Updated posture: 2026-09-30 GCV6→GCZ6 roll (+31.1 gap, old leg 245 lots)
  sits inside the verified root corpus (7th gap consistent); OI-based
  deeper rule still NOT_RUN (no OI field anywhere in corpus).

### SI-F1 BETA-CONVEX — CARRIED, DATA-BLOCKED (scored NOT_RUN_DATA_ABSENT)
- Mechanism + anatomy: unchanged (same-day corr 0.828; $-beta median 0.028
  ⇒ elasticity ≈1.9% SI per 1% GC; ratio 44.00→92.79 with one full
  decoupling 2026-01-26; single squeeze regime 60.2% ann-vol) [OBSERVED,
  SI_DOSSIER §3, sha256 a15e5e23…]. Convexity itself NOT_RUN (regime split
  unmeasured).
- Updated posture: both price legs on the verified corpus; vol-normalization
  control still computable stage-1 today; regime breadth NOT_RUN until
  ≥2y two-leg depth lands (owner vendor decision — FINAL_REPORT unlock
  clause). Ancestry re-check vs BAB-LOWBETA / DT100-71/73/74: no veto
  (convexity-conditioning ≠ standalone vol-regime trading; re-adjudicated
  this lane on the actual rows).

### SI-F2 CURVE-FLIP — CARRIED, DATA-BLOCKED (scored NOT_RUN_DATA_ABSENT)
- Mechanism + anatomy: unchanged (6/6 positive roll gaps, median +0.565
  $/oz = 113 ticks = $2,825/contract, mean +0.97%/roll ≈ +5.2%/yr; flip
  never observed in-window; staleness competitor from old-leg 22–376 lots)
  [OBSERVED, SI_DOSSIER §1/§3]. Conditional content NOT_RUN.
- Updated posture: unchanged blockers (lease rates licence-gated — the
  licence wall captured verbatim this lane on the LBMA page; back-adjustment
  mandatory; 2023–26 official dates NOT_OBTAINED). The new R3-F2
  VAULT-FLOW dossier supplies a free scarcity-corroboration observable that
  feeds SI-F2's scarcity-vs-staleness adjudication WITHOUT merging (§dossier
  boundary clause).

### SI-F3 CONSTRUCTION LAW — CARRIED (not a hypothesis; 0 identities)
- Cycle chain H/K/N/U/Z + serial exclusion + S1-front hazard +
  back-adjustment mandate unchanged (SI_DOSSIER H1). Re-verified the serial
  deadness and migration-ramp law against SI_DOSSIER §1 this lane.

## 4. Ancestry table (carried families, re-verified against all 173 rows this lane)

| family | nearest dead rows (id + class) | distinguishability | verdict |
|---|---|---|---|
| GC-F1 | crypto CARRY-1D/3D/7D (SCIENTIFIC_REJECTION/FOLD_CONCENTRATION), DT100-46-CARRY, DT100-95-BASISTERM (NEGATIVE_EXPECTANCY — funding/basis carry in perps); commodities rows COMMNG1 x3 (release-clock) | GC-F1 is curve-COMPRESSION stress conditioning on own per-contract spreads; no funding rate exists on COMEX; no release clock | NO VETO (carried verdict re-affirmed on the rows themselves) |
| GC-F2 | (construction class — no dead row; T5 law binds instead) | never scored as alpha per CENSUS_FINAL T5 | construction-class ceiling stands |
| SI-F1 | BAB-LOWBETA (crypto beta, SCIENTIFIC_REJECTION/COST_DOMINATED); DT100-71-RVREGIME, DT100-73-VOLAUTO, DT100-74-VOLTARGET (NEGATIVE_EXPECTANCY, standalone vol-regime daytrade) | SI-F1 = cross-leg beta-convexity CONDITIONING with vol-normalization NC; not standalone vol-regime trading; cost floor declared (SI program-max spread) rather than hidden | NO VETO (carried) |
| SI-F2 | (none — flip never observed; nearest by name crypto basis/carry rows) | scarcity-flip conditioning on own curve with mandatory staleness control | NO VETO (carried) |

## 5. Provisional 5-dim conversion (0-15 rubric, RANKING_FRAMEWORK anchors; PROVISIONAL — synthesis lane appends finals)

| family | D1 | D2 | D3 | D4 | D5 | total | basis |
|---|---|---|---|---|---|---|---|
| GC-F1 | 2 | 2 | 2 | 1 | 1 | **8** | on-symbol single-era anatomy (A/D1=2 per baseline); kills complete, no delay axis (D3=2); rate control latest-vintage NOT PIT-strict (D4=1); floor computed, MDE NOT_RUN (D5=1) |
| GC-F2 | 2 | 2 | 2 | 3 | 1 | **10** | own observable measured single-era; in-repo strict-past volume state (D4=3); construction ceiling ⇒ never ranked for registration anyway |
| SI-F1 | 2 | 2 | 2 | 3 | 1 | **10** | own observable measured single squeeze regime; in-repo strict-past labels (D4=3); MDE NOT_RUN (D5=1) |
| SI-F2 | 2 | 2 | 2 | 1 | 1 | **8** | 6/6 gaps single-era; SOFR carry floor latest-vintage (D4=1); flip never observed |

Conversion note: the baseline scored the 3-axis 0-9 rubric (all four tied 6).
This conversion re-expresses the same evidence under the 5-dim program
anchors; D4 splits (rates PIT defect vs in-repo features) and the D5
NOT_RUN-MDE anchor are the only deltas. No return statistic enters any cell.

## 6. What would upgrade any carried family (unchanged blockers, restated)

1. ≥2 years continuous true-volume front chain (per-contract daily TRADES +
   BID/ASK from ~2019) — owner vendor decision (Databento / CME DataMine
   purchase or prospective accumulation) — FINAL_REPORT unlock clause.
2. GC serial months 2025-11→2026-09 re-fetch ($0, existing entitlement) —
   unblocks the declared roll rule on that span (NOT_RUN this lane).
3. Daily open interest per contract — unblocks OI-based roll/positioning
   legs (NOT_RUN_DATA_ABSENT everywhere in corpus).
4. Multi-year M1/H1 — enables intraday variants of every family (designs
   exist; measurement NOT_RUN_DATA_ABSENT).
5. Fee A7 re-audit + account verification (D2 open) — cost layer stays
   MODELED/UNDER REVIEW until then.

— End CARRIED_STATUS.md. Outcome-blind; 0 PnL; missing evidence NOT_RUN.
