# SKEPTIC_NOREVIEW — SLEEVE-FX5-100K-V1 (Lane SK: independent skeptic/reproducer)

- Court: Lane SK, pre-GO sleeve program SLEEVE-FX5-100K-V1, cycle_id
  `SLEEVE-FX5-100K-V1-PREGO`.
- Measured-at (UTC, `date -u`): 2026-09-29T01:52:06Z. Read-only audit: no git
  commands, no backtests, no signals, no PnL, no scoring, 0 workers. Owner
  dirty tree preserved untouched.
- Claim under audit: Lane F0 (f0/F0_VERDICTS.md + SLATE_PROPOSAL.md) overturned
  all 15 census DISTINCT_TESTABLE rows and returned NO_ELIGIBLE_PROPOSAL
  (empty slate, no cycle). Lane PC (pitcost/COST_AUTHORITY_TABLE.md +
  PIT_COST_FREEZE_DRAFT.md) holds all 5 pairs PROVISIONAL_PENDING_COST_AUTHORITY
  with commission/swap/slippage DECLARED and swap-profit sleeves BLOCKED_COST.
- Mandate: attempt to WRONGFULLY-KILL the empty slate (the expensive error is a
  false NO_ELIGIBLE), reproduce PC's measurements, and audit the F0 process.
- Python for recomputes: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.

## 1. Method

1. Every one of the 15 rows was re-adjudicated against (a) the F0 verdict
   text, (b) the FULL cited ancestor record in `research/wayfinder/
   FAMILY_FAILURES.jsonl` (all 21 distinct cited ids located by line and read
   in full; for TRACKA2-P3B-DINV-1D including its nested FX2-* references,
   cross-checked against `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/
   tracka_cohort2/SKEPTIC_F1_cohort2_REPORT.md`), and (c) the row's own source
   idea text in `research/control/FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/
   symbols/<SYM>.md` at the cited source_ref lines (all 15 read verbatim).
2. Doctrine read in full: HOW_TO_BE_A_LEAD_ENGINEER.md §14.3; LESSONS.md
   P-27/P-28/P-29 (incl. P-29's ceiling-x-power pre-scoring veto and
   pair-swap law), Q-3/Q-7/Q-11 via LESSONS.md and the carrying records.
3. Data claims re-measured by me, not taken from either lane: ANC parquet
   schema, M1 .bi5 volume field, PC spread statistics (2 spot recomputes from
   the raw panels), calendar arithmetic, and the on-disk status of the ERP1
   raw M1 corpus.

## 2. Per-row re-adjudication (15/15)

Agreement column = my independent conclusion vs F0's verdict.

| # | gid | F0 verdict | Ancestor coverage independent check | SK |
|---|-----|-----------|--------------------------------------|----|
| 1 | GBPUSD-S079 | REJECT_VARIANT_SAME_FAMILY (TRACKA2-P3B + COMMNG1) | Source (GBPUSD.md S79) confirms positioning is ESTIMATED from a 20d/60d vol-scaled trend factor rebuilt from spot daily ("Data: spot daily (rebuild factor) + public CTA notes nếu có") — the operative information source IS own-price momentum at day clock; entry = direction of the fresh factor sign, hold 2-3 days = the continuation leg TRACKA2-P3B measured (rho 0.30-0.31 vs dead H1 TSMOM/donchian, reopening NONE). Payer story (forced unwind) is asserted, not observed; COMMNG1-A4-P2-ARM1-NEUTRAL shows even OBSERVED CoT positioning lost to its bare release-clock control — an own-price proxy is strictly weaker. A positioning-driven NARRATIVE does not change the information CLASS, which is own price. | AGREE |
| 2 | USDJPY-S012 | REJECT_VARIANT_SAME_FAMILY (FXFV2-A4-P1/P2, FXFV1-A3-P1/P2, DT100-09) | FXFV2-A4-P1 (line 34) = "Tokyo-range compression → London-morning expansion", anchor −3.804/trade PF 0.593, 1,541 trades, gross edge already negative. S12 = the SAME session observable (Tokyo range vs ATR), opposite tail (extension vs compression) and opposite sign (fade vs join) — both axes are named non-novelty axes in §14.3; FXFV1-A3-P2 (fade side, late-NY) and DT100-09-ASIANRANGE (Asian-range class, PF_BELOW_THRESHOLD) close the class around it. Caveat recorded (L-3): the exact extension→fade cell was not itself a measured FXFV2 anchor, and FXFV2's per-pair coverage is not independently verifiable from retained artifacts (program level: "7 free-data pairs" per HYPOTHESIS_LEDGER §D; FXFV3 names USDJPY in the same program) — but pair membership is immaterial under P-29/§14.3 pair-swap law, and the census's own proposed clock-shadow control is the same control shape that killed FXFV2-A4-P2. | AGREE |
| 3 | EURUSD-S027 | REJECT_VARIANT_SAME_FAMILY (DT100-71-RVREGIME + H-VOLCOMP + standing veto) | DT100-71 record verified (exp −11.37 bps PF 0.703, 4581 trades, 0/4 folds — quoted exactly). Entry leg = direction of the expansion candle = own-price breakout continuation at H4 clock = the vetoed class re-clocked (Q-3 forbids the cadance change); the ATR-ratio gate is a vol-state level on an autocorrelated chain (P-29). | AGREE |
| 4 | AUDUSD-S001 | REJECT_VARIANT_SAME_FAMILY (standing veto + ES1) | EMA stack = smoothed momentum state on own price at H4/D1 clock, on a pair the veto was measured ON (AUDUSD rho 0.3103). The "China credit impulse" coupling is a gate on a dead law (P-27, owner law 2026-09-26: adding an observable/gate to a dead law is a variant); the census's own required_pit_data is OHLC only, so the declared information set is own price anyway. | AGREE |
| 5 | AUDUSD-S003 | REJECT_VARIANT_SAME_FAMILY (standing veto; P-27/P-29) | ADX/MACD gate = gate-on-dead-law; ADX trend-strength state is itself a momentum state (P-29 representation argument applies verbatim). Intra-slate distinctness (vs S1) is not ancestry novelty — F0's point is correct. | AGREE |
| 6 | AUDUSD-S017 | REJECT_VARIANT_SAME_FAMILY (FXOS-04 + MR-transfer + FX2-STOCH-C4 shadow) | FXOS-04 (line 120) verified: Bollinger MR fade on 15m EURUSD, holdout net negative, dev edge attributed to selection — the oscillator-exhaustion-fade class is measured dead on an FX major with measured costs; TD count is a deterministic own-price transform (rename, §14.3). FX2-STOCH-C4 appears only as a nested reference (see L-2) but the standalone FXOS-04 + mean-reversion-transfer records already carry the class. | AGREE |
| 7 | AUDUSD-S087 | REJECT_DATA_OR_COST (volume absent; M5 below ceiling) | VERIFIED MYSELF: bars1h_ANC_AUDUSD.parquet columns = `ts, b_o, b_h, b_l, b_c, a_o, a_c, s_open, s_close` — NO volume column (30,420 rows, 2021-01-03 23:00 → 2026-06-30 20:00); same for USDCAD (30,386 rows). The S87 signal conditions on "volume ngày thấp/cao" (verbatim in AUDUSD.md) — literally uncomputable on the declared panel. M5 decision clock is below the R6 H1 ceiling. F0's honest note that NO dead volume-profile ancestor exists is imprecise (M-3: DT100-13-VWAPMR) but the kill is data, not ancestry — unaffected. | AGREE |
| 8 | AUDUSD-S088 | REJECT_DATA_OR_COST (same + range fence secondary) | "tick volume tăng" is a load-bearing conditional (verbatim in S88 signal); 8-12 pip approach band + 6 pip stop are sub-H1 geometry — a single H1 bar spans the whole approach. Option-expiry calendar is optional in source ("nếu có") — but its absence only de-funds the claimed barrier-gamma payer; the data kill stands on tick-volume + M5 regardless. | AGREE |
| 9 | AUDUSD-S002 | REJECT_VARIANT_SAME_FAMILY (FX2-H1DONCH-C1 via standing veto + PSV1 pair) | Standing veto measured ON AUDUSD (worst |rho| 0.3103 vs FX2-H1DONCH-C1, reopening NONE, "re-clocking is ancestry violation"); D1 Donchian 20/55 two-sided SAR = channel-breakout continuation at day clock. PSV1 twins verified (CONTROL_OUTEARNED_ANCHOR +190,392 vs +177,692; no incremental value over ALWAYS_ON_LONG). Census N-2 mislabel ("ungated" vs source "Coupling: gate ADX14>20") confirmed by me — immaterial, gate-difference is a variant per P-27. | AGREE |
| 10 | USDCAD-S002 | REJECT_VARIANT_SAME_FAMILY (same, measured pair) | Veto measured ON USDCAD (FX2-H1TSMOM-C1 0.3032, FX2-H1DONCH-C1 0.3001). "Deliberately unfiltered baseline" framing does not move a §14.3 axis. | AGREE |
| 11 | AUDUSD-S046 | REJECT_NOT_STANDALONE | Source text (AUDUSD.md S46) says verbatim: "chỉ dùng như prior, không standalone" — the idea's own source declares it cannot form a book. Payer difference vs SFV3-A6-TOM-SETTLE correctly acknowledged by F0 and correctly ruled insufficient (cannot rescue a non-book). NOTE (M-2): F0 missed the strongest citation — FXNG4-A4-P1, a dead FOREX calendar/seasonal book (ANCESTRY_RHO_BLOCK 0.8883 vs generic weekday geometry, "books stack on weekday geometry") — which would make the kill stronger, not weaker. | AGREE |
| 12 | USDCAD-S047 | REJECT_DATA_OR_COST (WTI panel + power) | Source text (USDCAD.md S47) puts the hedge IN the trade prescription: "Trade: short USDCAD nửa size + oil-hedge ngược"; census required_pit_data: "...plus WTI hedge leg" — as proposed the mechanism REQUIRES an instrument the sleeve does not carry (5 FX pairs; other 7 assets FLAT, no substitute data). Independent of WTI: I count exactly 5 winter entry episodes (mid-Nov 2021/2022/2023/2024/2025) in the 2021-01..2026-06 panels — the P-29/P-31 ceiling-x-power pre-scoring veto applies (arithmetically underpowered across 8 folds). F0's payer analysis (winter-energy payer genuinely differs from TOM-SETTLE) is correct and the kill does not rest on it. | AGREE |
| 13 | EURUSD-S009 | REJECT_NOT_STANDALONE (BRV1 + dead entry leg) | Census payer column "UNCLEAR"; entry leg = EMA alignment = vetoed momentum class; without the entry there is no position, so the claimed mechanism (exit rule) cannot form its own book. BRV1-RISK-OVERLAY verified (exit-side overlays cut winners and losers proportionally — measured, BTC). Structural argument is asset-agnostic and sufficient. | AGREE |
| 14 | USDCAD-S025 | REJECT_VARIANT_SAME_FAMILY (FXFV2-A4-P2 + range fence + FAILBRK) | FXFV2-A4-P2 verified: break+retest-hold skeleton, placebo ≈ anchor (−3.093/trade) — the retest skeleton is measured-dead on FX; TRACKA2-C1C2C3 fence permanently closes range-adjacent triggers absent NEW payer + NEW information layer; S25's payer IS stop-flow ("institutional reallocation stop-flow") — the payer family the fence names as dead; info layer = own-price levels + rejection candle. Both signs dead (fade: TRACKA1/TRACKA2; continuation: FXFV2-A4-P2; DT100-83-FAILBRK opposite sign, 32,586 trades). The census listed FAILBRK itself and still passed the row — overturn was correct. | AGREE |
| 15 | USDCAD-S004 | REJECT_VARIANT_SAME_FAMILY (standing veto on measured pair + TSMOM twins) | Veto measured ON USDCAD (0.3032 vs FX2-H1TSMOM-C1, reopening NONE); the 200DMA-dislocation gate is a normalized distance-from-slow-MA state = slow momentum level-window (P-29: the gate IS the ancestor). XSECT-TSTREND-L14/L28 (5/5 rejected, denominator 117) and DT100-80-TSMOMH (−10.59 bps PF 0.83, 0/4) verified verbatim. | AGREE |

**15/15 rows: I AGREE with every F0 verdict. No wrongful kill found.** The two
most attackable links (rows 2 and 12) were probed hardest and both hold: row 2
rests on §14.3 sign/threshold non-novelty which is exactly the written law
(plus the same observable and the same session), and row 12's kill survives
even under the most charitable reading of the WTI leg (optional) because the
5-episode power arithmetic alone is a P-29-class pre-scoring veto.

## 3. Citation authenticity (F0 process audit)

- All 21 distinct ancestor family_ids cited across F0_VERDICTS.md resolve to
  real FAMILY_FAILURES.jsonl records (line numbers held by this audit), with
  three exceptions that are nested-only references — FX2-H1TSMOM-C1,
  FX2-H1DONCH-C1, FX2-STOCH-C4 — which exist inside TRACKA2-P3B-DINV-1D's
  primary_failure detail (line 131) and the cohort-2 skeptic report (rho
  values 0.3032/0.3103/0.3001/0.295x verified at SKEPTIC_F1_cohort2_REPORT.md
  lines 62-96). F0 disclosed this limitation itself in its handoff
  known_limitations. **No invented citation found.** All quoted statistics
  match the records verbatim (spot-checked: DT100-71 −11.37/0.703/4581;
  DT100-80 −10.59/0.83; DT100-83 −10.56/0.569/32586; FXFV2-A4-P1
  −3.804/0.593/1541; FXFV2-A4-P2 −3.093 placebo≈anchor; FXOS-04 +1203.6→
  −134.4; PSV1 +190,392 vs +177,692; COMMNG1 release-clock control
  out-earning all anchors).
- N-1 root cause CONFIRMED from the input TSV itself: of the 8 rows carrying
  ancestry hits, EVERY hit family is crypto/stocks/sprint (PSV1, DT100, SFV3,
  BRV1, XSECT) — zero of the 38 forex-asset records in FAMILY_FAILURES.jsonl
  (lines 31-65, 82-95, 120, 127-134, 140) was ever surfaced, including
  FXFV2-A4-P1 whose title shares the literal word "Tokyo-range" with row 2's
  mechanism. The miss pattern is exactly family-name-keyed matching (the
  families named in the 12 non-distinct rows), as F0 hypothesized. I could
  not locate the census lane's own artifacts beyond the 15-row extract (the
  digest the census lanes held is not committed in the cycle dir — see I-6),
  so the mechanism is confirmed by pattern, not by reading the census code.
- N-2 confirmed: census verdict_reason says "ungated two-sided Turtle" while
  AUDUSD.md S2 carries "Coupling: gate ADX14>20". Immaterial (P-27).

## 4. Reproducer duty on Lane PC

### 4.1 Spread spot-recomputations (my own code, from the raw panels)

Method per PIT_COST_FREEZE_DRAFT Appendix B; sleeve window Fridays
2021-01-08 → 2026-06-26 enumerated by me (286 Fridays, matching PC §2.1).

1. **EURUSD Friday-20:00Z fill spread_open** (spread of the [20:00,20:01)
   minute, sec==72000, volume>0 both sides, scale 1e5, pip 1e-4),
   fx-rangefade M1 .bi5: **p50 = 0.300 / p90 = 0.500 pips, n = 286/286** —
   EXACT match to PC C1 (0.3 / 0.5, 286/286).
2. **GBPUSD Sunday-reopen spread_open** (first minute of the following Sunday
   with volume>0 both sides and ask>bid), fx-majors-search M1 .bi5:
   **p50 = 13.45 / p90 = 23.74 pips, n = 284** vs PC C3 (13.4 / 23.8, n=283)
   — p50 delta +0.4%, p90 delta −0.3%, both far inside the ±15% tolerance.
   The one-count difference is explained: my filter admits 2023-01-01 (New
   Year Sunday, first tradable minute 23:04 UTC, spread 16.8 pips) which PC's
   stricter validity rule evidently excludes; the other two missing Sundays
   (2023-12-24, 2023-12-31) are not-tradable in both pipelines. INFO: PC
   should state the validity rule that drops the 23:04-reopen week (L-1).

Both spot checks PASS. PC's C1/C3 measured-spread claims are reproducible
from the panels to within 0.4% — materially stronger agreement than required.

### 4.2 Calendar arithmetic (verified by enumeration)

- 286 sleeve Fridays 2021-01-08 → 2026-06-26 (enumerated). ✓
- F1..F8 test-window Friday stamps reproduced exactly (F1 2022-01-07 →
  2022-07-01 … F8 2025-07-04 → 2025-12-26). ✓
- Weeks 53..260 = 208 = 8 × 26; 52 warmup + 208 fold-test + 26 sealed = 286. ✓
- Option A: OOS weeks 261-286 = Friday stamps 2026-01-02 → 2026-06-26;
  Mon-aligned week 261 starts Mon 2025-12-29 and 26 weeks (182 days) ends
  Sun 2026-06-28. Consistent — a full 26-week OOS ending at the last common
  Friday stamp, and nothing after 2025-12-29 is computed pre-terminal. ✓
  The dispatch's "2026-01-05 → 2026-06-26" alternative is indeed mutually
  exclusive with 26 Mon-aligned weeks (it yields 25); PC's §2.4 correction
  and Option A recommendation are arithmetically right. ✓
- OOS end respects the ANC 2026-06-30 end cap (R7) with one week of margin. ✓

### 4.3 PC verdict table spot-audit

The C1-C8 component structure, the MEASURED-vs-DECLARED law, the
swap-profit BLOCKED_COST rule (pessimistic symmetry, COST_ACCOUNTING_SPEC
§2.7) and the n=1-day paper-window classification (owner directive quoted
verbatim) are internally consistent with the cited inputs; nothing optimistic
is inferred anywhere I checked. No finding above LOW against PC.

## 5. Data-claim verification results (rows 7-8 and the N-3 contradiction)

1. **ANC volume absence: CONFIRMED** (direct parquet read; §2 rows 7-8).
2. **M1 .bi5 volume presence: CONFIRMED** — I decoded one file myself
   (GBPUSD 2026-09-22 BID, lzma + `struct '>5if'`): 1,440 records of
   (sec, o, c, l, h, volume_f32); 1,429 records volume>0. The field exists
   and is populated on tradable minutes (Dukascopy tick-count volume — a
   proxy, as F0's handoff itself flags).
3. **F0 N-3 vs PC R6 contradiction: RESOLVED IN PC'S FAVOR.** F0's N-3 and
   SLATE_PROPOSAL salvage note 3 claim the ERP1 raw M1 corpus for
   AUDUSD/USDCAD "physically exists" (2,007 BID+ASK day-files/pair). I
   searched: the ERP1-TRACKA-COHORT-1 worktree's `data_local/duka/` holds
   ONLY the sha-pinned manifests (`m1_manifest_AUDUSD.json`,
   `m1_manifest_USDCAD.json`, 4,014 entries each, window 2021-01-01 →
   2026-06-30, days_missing=[]); ZERO .bi5 files exist anywhere reachable
   (worktrees + machine-local data root). The DATACOST cohort-1 report says
   the raw bytes were "machine-local, gitignored" — they are no longer
   present. PC's R6 ("raw M1 … not on disk, duka manifests only") is
   correct. F0's wording is wrong-TODAY. Verdict-neutral (rows 7-8 died on
   the declared ceiling, which is unchanged), but the reopening condition
   must be amended (M-1).
4. **PITDATA schema citation: CONFIRMED** — PITDATA_cohort2_REPORT.md line 23
   states the 15m/1h schema exactly as F0 quoted.

## 6. Findings register

- **CRITICAL: none.**
- **HIGH: none.** (No wrongful kill; both spread recomputes inside 0.4%;
  calendar arithmetic exact; no invented citations.)
- **M-1 (MEDIUM, F0 N-3 / salvage note 3):** "ERP1 raw M1 corpus physically
  exists" is false as of this audit — only the sha-pinned manifests exist.
  The reopening condition "data authority extension to ERP1 raws" actually
  requires a RE-DOWNLOAD verified against the manifests, plus the authority
  extension, plus respect for the sealed 2026-H1 holdout segment. Correct
  salvage note 3 before any owner decision relies on it.
- **M-2 (MEDIUM, F0 citations):** FXNG4-A4-P1 (FOREX-NG4, forex, CLOSED,
  ANCESTRY_RHO_BLOCK — "EZ seasonal-naive print-deviation on EURUSD", veto
  0.8883 vs generic weekday geometry, "books stack on weekday geometry") is
  a dead FOREX calendar/seasonal ancestor directly applicable to rows 11-12
  that F0 did not cite. Direction of error: STRENGTHENS both kills (no
  wrongful-kill implication), but it shows F0's positive citation scan was
  not exhaustive for the calendar rows, and F0 let the census's "no dead FX
  weekday class" wording stand uncorrected when a measured dead FX
  calendar-conditioning book existed. Future calendar-book proposals must
  scan FXNG4-A4-P1 (and FXNG3-A5-P2) alongside DT100-34/V17-A4-P1.
- **M-3 (MEDIUM/LOW, F0 salvage note 1):** "NO dead volume-profile ancestor
  was found in the 169 records" is imprecise: DT100-13-VWAPMR (crypto, VWAP
  mean-reversion rescore anchor, exp −2.18 bps PF 0.835, 0/4 folds, recorded
  2026-09-28) is a dead volume-weighted-price-anchor acceptance/reversion
  neighbor. Does not affect row 7's data kill, but the M1-pair
  volume-profile salvage claim ("the one genuinely unclaimed observable
  surface") must be qualified: a future row there must clear DT100-13-VWAPMR
  first and must state the tick-count-volume proxy limitation.
- **L-1 (LOW, PC):** Sunday-reopen n=283 vs my 284 (2023-01-01 New-Year
  reopen at 23:04 UTC); percentiles unaffected. State the validity rule.
- **L-2 (LOW, F0, disclosed):** FX2-H1TSMOM-C1 / FX2-H1DONCH-C1 / FX2-STOCH-
  C4 are nested references, not standalone records; values trace cleanly to
  the cohort-2 skeptic report. F0 disclosed this itself.
- **L-3 (LOW, F0 row 2):** the exact (Tokyo-extension → London-fade) cell
  was not a measured FXFV2 anchor; kill rests on class-level extension per
  §14.3/P-27. Doctrine-consistent; the weakest of the 15 links, still not
  wrongful. FXFV2 per-pair coverage not independently verifiable from
  retained artifacts (immaterial under the pair-swap law).
- **I-1 (INFO):** EURUSD Fri-20Z spot-check exact match; GBPUSD reopen
  within 0.4%.
- **I-2 (INFO):** All calendar arithmetic verified (§4.2).
- **I-3 (INFO):** N-1 root cause confirmed by pattern (§3).
- **I-4 (INFO):** ANC schema and M1 volume verified by direct measurement
  (§5); my own struct/LZMA decode cited.
- **I-5 (INFO):** N-2 confirmed against source text.
- **I-6 (INFO, process):** the census lane's full digest/artifacts are not
  committed anywhere in the cycle directory (only the 15-row extract);
  auditability of the census step depends on F0's re-search, which is
  exactly the failure mode N-1 describes.
- **I-7 (INFO):** cycle plan/ directory exists but is empty at audit time.

## 7. Reopening conditions — endorsement

Endorsed as proposed by F0/PC, with amendments:

1. **Volume-profile on the M1 pairs** — ENDORSE WITH AMENDMENT: the new row
   must (a) scan/clear DT100-13-VWAPMR (M-3), (b) declare Dukascopy
   volume_f32 as tick-count proxy, (c) carry the lagged-twin + inverted-arm
   controls per P-28 as F0 already specified.
2. **ERP1 raw M1 corpus for AUDUSD/USDCAD** — ENDORSE THE CONCEPT, AMEND THE
   PATH: bytes are gone; condition = owner data-authority extension +
   re-download verified against the sha-pinned m1_manifest files + the
   2026-H1 sealed holdout stays sealed (DTPFX1 precedent). Only rows 7-8
   would be re-adjudicated; the ancestry fences on 9/10/14/15 stand.
3. **Observed-flow calendar book** — ENDORSE WITH ADDITION: scan set must
   include FXNG4-A4-P1 and FXNG3-A5-P2 (M-2) beside DT100-34/V17-A4-P1; bar
   remains beat-a-clock-only-shadow (Q-7) with the flow observable doing
   measurable work (Q-11).
4. **IBKR statement for cost authority** — ENDORSE unamended (C4/C5/C6
   upgrade paths and machine-local path in COST_AUTHORITY_TABLE §3 are
   correct; swap-profit sleeves stay BLOCKED_COST until then).

Conditions I would ADD:

5. **Class-based ancestry index for the census step** — the N-1 root cause is
   a tooling gap: build a keyword/family-class index over FAMILY_FAILURES
   keyed on (mechanism skeleton, payer class, information class) so the next
   census cannot miss 38 forex records again; every "none-found" must be
   machine-verified against it before a row may be called DISTINCT_TESTABLE.
6. **Commit census artifacts** — the census digest and its search parameters
   belong in the cycle directory (I-6), else every downstream audit inherits
   the F0-only re-search dependency.
7. **Timestamp-rule disclosure for edge-case fills** — PC should publish the
   validity rules that exclude marginal reopen weeks (L-1) so n counts are
   reproducible to the unit, not just to the percentile.

## 8. Bottom line

The empty slate survives an adversarial read. Every one of the 15 kills is
supported by (i) an ancestor whose skeleton/information-source genuinely
covers the row after reading the full record and the source idea text, or
(ii) a data/power deficiency I re-measured myself. The expensive error —
wrongfully killing a legitimate program — did NOT occur. Lane PC's measured
spread authority reproduces from raw panels to within 0.4% and its calendar
arithmetic is exact; its DECLARED/blocked cost posture is law-consistent and
infer nothing optimistic. The findings above (M-1..M-3) correct the record on
three points of fact/wording without changing any verdict.

EMPTY_SLATE_HONEST
