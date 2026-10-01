# G6_ADJUDICATION — spread-envelope FAIL of the AUD/CA HMDS D1 pull (2026-10-01)

Fresh-context skeptic ruling (no authorship of any adjudicated object). **Read-only
except this one file**; `.venv/bin/python` used read-only on frozen raw files;
no objects edited, nothing committed, nothing scored, no S1. Adjudicated
question (owner directive): the G6 pull's pre-registered spread-envelope check
FAILED — rule between (a) typed `NOT_RUN_INPUT_END` + force-flat for
2026-07-01→09-30, (b) prospective amendment (accept data under a corrected,
owner-frozen envelope law), or (c) another lawful option. The owner FORBIDS
relabeling FAIL→PASS because older panels also fail.

---

## 1. WHAT failed, precisely (requirement 1)

**The check:** pre-registered band `p50 ∈ [0.25×,4×]·C1_p50 AND p90 < 8 pips`,
applied to the **close-side spread** `(ASK_close − BID_close)/pip` of the G6
HMDS D1 pull (AUDUSD/USDCAD, all 66 weekdays of 2026-07-01→09-30, quantile
convention 'lower', crossed-book filter). Source of the band: the lane's own
pre-pull constants (`g6_pull/verify_g6_pull.py` L112, `g6_pull.py` L52-54,
"sanity anchors only") — a PREPARATION-stage screen, not a registered gate.

**Decomposed result (re-derived independently from raw, this session):**

| leg | AUDUSD | USDCAD | verdict |
|---|---|---|---|
| p50 ∈ [0.25×,4×]·C1 p50 | 2.5 ∈ [0.25, 4.0] | 2.5 ∈ [0.30, 4.8] | **PASS both** |
| p90 < 8 pips (absolute) | 8.5 | 14.0 | **FAIL both** |

The reported "FAIL on both pairs" is therefore **entirely the absolute
`p90 < 8 pips` leg**. That cap has no anchor in either observable (see §2) —
C1 p90s are 1.3/1.6 pips; where did 8 come from? It is an ad-hoc absolute
number, and it is the sole failing leg.

**The anchor — what C1 actually measured** (`SLEEVE-FX5-100K-V1/pitcost/
COST_AUTHORITY_TABLE.md` §C1): AUDUSD 1.0/1.3 (n=199/286 Fridays), USDCAD
1.2/1.6 (n=247/286) = **H1 ANC panel-venue (Dukascopy-feed) `s_open` of the
Friday 20:00-open bar**, sleeve window 2021-01-08→2026-06-26. (The pull
script's comment "close-side H1 C1 cells" is a mislabel: the table says
`s_open`; open-side. Immaterial to the outcome — both differ from the G6
statistic — but recorded for accuracy.)

**The measured observable:** IBKR IDEALPRO HMDS **daily per-side close
prints** — each side's own last quote of the session — over **all weekdays**
of Q3-2026. These are not the same observable on four axes:

| axis | C1 anchor | G6 statistic |
|---|---|---|
| venue | panel venue (Dukascopy-feed ANC) | IBKR IDEALPRO HMDS |
| instant | H1 bar open, Friday 20:00 UTC | per-side session last print (~17:00 ET) |
| day-set | Fridays only (199/247 of 286) | all 66 weekdays (13 Fridays ≈ 20%) |
| window | 2021-01-08→2026-06-26 | 2026-07-01→09-30 (entirely after) |

**Was the band ever lawful for this observable? No — as a calibrated
admission band it was never lawful.** Four independent proofs:

1. **Unsatisfiable by the accepted corpus.** The same `p90 < 8 pips` leg,
   applied to the frozen, accepted 7-asset HMDS corpus (same source, same
   statistic), fails **in the same quarter** (NZDUSD Q3-2026 p90 = 8.0 —
   fails strict `<`; USDCHF 12.5) **and over its full 6-year window**
   (NZD 11.5, CHF 14.0 pips; n=1553 each; recomputed independently this
   session). A band no acceptable HMDS daily close-side panel can ever pass
   cannot discriminate good data from bad — it is miscalibrated for the
   observable, exactly as the pull agent noted (and the owner's no-relabel
   law is why this is adjudicated rather than waved through).
2. **The anchor's own authority table forbids the transfer.** COST_AUTHORITY
   _TABLE C1 caveat (ii): the panel↔IBKR transfer is **UNMEASURED** and must
   be labeled. Using C1 (panel venue) as a magnitude anchor for an IBKR
   statistic silently transfers venues the table itself declares
   unmeasured.
3. **The Friday effect is a property of the source, not of this pull.**
   Friday close = the weekend-stale last print. Frozen corpus, same quarter:
   NZD Friday median 8.0 vs midweek 0.5 pips (16×); CHF 13.5 vs 3.0 (4.5×);
   full-window Friday medians 10.5 / 9.5. G6: AUD 8.5 vs 1.5; CAD 16.0 vs
   2.0. With Fridays ≈ 20% of the day-set, the p90 index (58 of 65) sits
   inside the Friday cluster — **10 of the top 13 spreads are Fridays on
   both G6 pairs** — so the p90 measures the Friday regime, i.e. the
   day-set composition of the observable, not data quality.
4. **The owner has already classified this observable class.** Gate-table
   row G5 (co-owner decision 2026-10-01, PLAN §0b ¶2): the async two-sided
   daily difference "is a **BAR-SIDE DIFFERENCE, NOT a simultaneously-
   measured executable spread**"; execution cost is MEASURED only where
   simultaneous quotes exist — everything else DECLARED. The G6 close-side
   statistic is exactly this class; a tight executable-spread cap on it
   contradicts the owner's own recorded classification.

**What the check is lawfully FOR** (and where it works): a **gross-error
screen** — wrong instrument, side swap, unit error, day misalignment. On
every leg that detects those, the pull PASSES (re-measured): 0 crossed
books; exact BID/ASK date alignment; all spreads ≥ 0 and exact minTick
(0.5 pip) multiples; close-mid domains plausible (AUD 0.689–0.722, CAD
1.376–1.423); coverage 66/66 weekdays, 0 interior gaps; integrity re-hash
16/16 match (re-done this session); midweek medians 1.5/2.0 pips inside the
C1 anchor p50 range 1.0–1.6; quarter p50s bracketed by the same-source
same-quarter accepted instruments [NZD 0.5, CHF 4.5].

---

## 2. RULING (requirement 2): **(b) — prospective amendment, owner-frozen corrected envelope law; the pre-registered FAIL stands as recorded; data admitted for input completion**

### 2.1 Why the FAIL does not condemn the data — the mechanism under EXPLORATORY-ONLY

Does the envelope FAIL even matter for an exploratory battery under declared
costs? **It matters through exactly one channel — input admissibility — and
the correct remedy on that channel is fixing the screen's law, not
discarding the data:**

- **No PASS is at stake.** §0b ¶4 + the exploratory-only amendment: the
  2020–2026 battery is EXPLORATORY; PASS bars read only on the prospective
  surface. Nothing in this battery can be promoted regardless of this check.
- **No cost line is at stake.** OI-2: commission/swap/slippage are
  DECLARED-pessimistic; and the daily kernel prices fills off the **fill
  bar's own open-side quoted prices** (`spread_once` = half the D1 fill
  bar's own quoted spread, plan §5; G5 §1.1/§1.5). The close-side statistic
  the failing check measured is **not a cost-consumed quantity**; per the
  G5 owner decision it is a bar-side difference, not an executable spread.
- **What IS at stake: admissibility of the AUD/CA D1 extension** (G6/§7.5)
  — is the extension panel correctly identified, paired, aligned? That is
  the gross-error class, and every such leg passes (§1).

Consequently the FAIL is load-bearing only as a screen result, and the
screen's magnitude leg is proven miscalibrated (§1). Leaving it standing
unsatisfied is not an option either: plan §7 item 7 freezes an
**ongoing-collection law of scheduled HMDS D1 pulls** (AUD/CAD/NZD/CHF,
forward) — an unsatisfiable band would manufacture a false FAIL on every
future pull. The amendment is therefore **required, not optional**.

### 2.2 Why not (a) typed `NOT_RUN_INPUT_END` + force-flat

`NOT_RUN_INPUT_END` has fixed semantics in this workspace: **the consumed
input bar does not exist** → `UNAVAILABLE` → fail-closed (G5 §2.3(b):
"from 2026-07-02 … the consumed bar does not exist → UNAVAILABLE →
fail-closed abort"). The G6 bars **exist** — 66/66 weekdays, sha-verified,
PIT-clean (end-bounded, closed bars, forming bar excluded and disclosed).
Typing `NOT_RUN_INPUT_END` over existing, verified data would write a
**false trial-accounting record**: it misstates WHY rows did not run, and a
future auditor reconciling input coverage would either hunt for missing
bars that are not missing or conclude the panel ends 2026-06-30 when it
does not. The mission invariant ("missing evidence is `NOT_RUN`, never
inferred `PASS`") protects against inferring PASS from absence; it does not
authorize asserting absence where evidence exists. Option (a) would also
destroy **61/130 fold-8 sessions (46.9%) for DS-05** — the only operative
leg consuming AUD/CA — to remedy a defect the data does not have. If the
owner ever did want to exclude existing data, the honest typing would be an
admission-rejection label (e.g. `NOT_RUN_ADMITTED_DATA_EXCLUDED` with the
band citation), never `NOT_RUN_INPUT_END`.

### 2.3 Why not silent acceptance — and the lane's self-verdict

The owner forbids relabeling FAIL→PASS. Accordingly: **the pre-registered
band result stays FAIL, verbatim, in `VERIFICATION.json`** (and the
lane's report already reports it honestly). The lane's own
"PASS-with-disclosure / overall PASS" verdicts are **not endorsed as they
stand** — a PASS granted over a failed pre-registered screen is lawful only
after the owner freezes the corrected law (the amendment changes the
screen's calibration prospectively; the same measurements then pass **by
measurement under the new law**, not by relabeling the old result). The
pull remains labeled PREPARATION feeding an unregistered cycle; nothing
scores; OI-2 stands; panel assembly/aggregation/serving under OI-1 remains
an A1/registration act, as the pull report itself states.

### 2.4 Fresh-skeptic checks performed against the data-defect hypothesis (all negative)

- Integrity: all 16 raw files re-hashed against `MANIFEST.json` — 16/16
  match (this session, independent).
- A side-swap/pairing artifact would produce crossed books — 0 on both
  pairs; a unit error would break minTick multiplicity — 0 violations.
- A chunk-boundary pairing artifact (main vs addendum chunks overlapping
  07-01/07-02) would cluster wide spreads on boundary dates — instead the
  wide tail is uniformly the 13 Fridays across the whole quarter.
- The same Friday pattern exists in the frozen accepted corpus (§1.3).
- **Venue seam, measured (new this session):** on the June-2026 overlap
  (n=20 days, verbatim June rows in the addendum chunks vs the sha-pinned
  H1 ANC parquets — both re-hashed, pins match), |HMDS daily close-mid −
  H1 20:00Z-bar close-mid| = **p50 0.35 / p90 ≤ 1.0 / max 3.15 pips** on
  both pairs (vs last-bar-of-date: p50 1.15/2.10, max 9.6/23.3 — the ANC
  panel's last bar is not a fixed hour, which is exactly why the declared
  aggregation law exists). The HMDS daily close is the ~17:00 ET session
  close; the stitch at 2026-06-30→07-01 is coherent at the signal (close
  mid) level, with the seam two orders below typical daily moves. This is
  a MEASURED-ON-OVERLAP disclosure, not cost authority.

---

## 3. The corrected envelope law — draft for owner freeze (requirement 3)

**No-loosening justification first.** The correction is derived from WHAT
the observable is, and from anchors that **pre-date the pull** (the frozen
corpus was sha-frozen 2026-09-30; the G6 pull landed 2026-10-01):
(i) the gated magnitude legs move from a Friday-contaminated all-weekday
p90 (which measures day-set composition) to the **midweek subset** where
the close print is an ordinary-liquidity print commensurable with the
anchor class — and on that subset the law keeps the original C1-multiple
leg **and adds two legs the old band lacked** (same-source midweek p50
bracket; midweek p90 cap); (ii) Friday behavior is disclosed, never gated
and never trimmed (owner G5 no-trim law), because Friday width is a
construction property of the observable, not a defect signature; (iii)
structural gross-error legs are unchanged and fail-closed. The law is
stricter on everything except the specific quantity proven miscalibrated.

**Draft law sentence (freeze verbatim):**

> **HMDS-D1-CLOSE-ENVELOPE@1** (prospective; binds every IBKR HMDS D1
> BID/ASK pull of the DAILY successor, beginning with
> `G6-INPUT-COMPLETION-IBKR-D1-2026-10-01`): the pull's close-side spread
> `(ASK_close − BID_close)/pip` on date-aligned, uncrossed days is a
> per-side **asynchronous session-last-print difference** on IDEALPRO — a
> bar-side difference, not a simultaneously-quoted executable spread and
> not a cost line — and its admission screen is therefore: **(i)
> STRUCTURAL (fail-closed):** zero crossed books; exact BID/ASK date
> alignment; every spread ≥ 0 and an exact integer multiple of minTick;
> close-mid domain plausible for the instrument; coverage complete per the
> source calendar law (all weekdays for this source). **(ii) MIDWEEK
> MAGNITUDE (Mon–Thu only; Friday's close is by construction the
> weekend-stale last print and is disclosed, never gated, never trimmed):**
> midweek p50 ∈ [0.25×, 4×] of the pair's C1 panel-venue anchor p50, AND
> midweek p50/p90 inside the frozen same-source 7-asset corpus's midweek
> bracket for the matching window class (frozen 2026-09-30, pre-dating
> this law's first application: midweek p50 ∈ [0.5, 3.0] pips; midweek
> p90 ≤ 11.0 pips, the corpus FULL-window midweek p90 maximum). **(iii)
> DISCLOSURE (not a gate):** Friday median/p90/max and the weekday
> composition of the top tail reported verbatim; any overlap with a
> panel-venue series gets a venue-seam measurement
> (|HMDS close-mid − declared-aggregation close-mid|) reported as
> MEASURED-ON-OVERLAP (2026-06: p50 0.35 / p90 ≤ 1.0 / max 3.15 pips) —
> which transfers **no cost authority**: execution cost remains MEASURED
> only where simultaneous quotes exist (C1–C3 panel-venue cells) and
> DECLARED elsewhere. The superseded band (`p50 ∈ [0.25×,4×]·C1 p50 AND
> p90 < 8 pips`, all weekdays) remains recorded as FAIL for AUDUSD/USDCAD
> in `VERIFICATION.json` and is never relabeled; this law takes effect
> only at owner freeze and applies prospectively.

**Application to the G6 pull under this law (passes by measurement, with
margin — not a boundary fit):** structural legs all pass (§2.4); midweek
p50 1.5 / 2.0 vs [0.5, 3.0] and vs C1 multiples (1.5×, 1.67×); midweek
p90 4.0 / 3.5 vs cap 11.0. **Defect-catching check (the law still bites):**
side swap → crossed books (i); unit error → minTick/mid-domain (i); wrong
conId → mid-domain (i); day misalignment → side alignment (i); a genuine
midweek liquidity regime change → (ii); the Friday tail is carried as
disclosure because it cannot distinguish defect from property — and it
prices nothing.

**Residual honest disclosures to carry at registration:** USDCAD's Friday
median/p90 (16.0 / 33.5) sits at/just above the frozen corpus's own
Friday envelope (CHF 13.5 / 28.0 same quarter; 32.5 full-window) —
same-source-comparable, disclosed, cost-irrelevant; the seam measurement
is n=20 days, one month, close-mid only; the pull script's "close-side H1
C1 cells" comment is a mislabel (C1 is `s_open`); the verify script's
control `passes_pre_registered_band` applies only the p90 leg to controls
(NZD fails by equality, 8.0 < 8.0 false; CHF 12.5) — the JSON's
"band also fails the corpus" claim is true for that leg, stated here with
its precise reading.

---

## 4. What would have to be true for the opposite ruling — (a) rejection + typed truncation (requirement 4)

1. **Actual data defect:** any structural-leg failure — crossed books,
   side misalignment, non-minTick spreads, implausible mid domain, or
   coverage gaps in the pulled window. (All measured clean.)
2. **Genuine same-source anomaly:** G6 midweek statistics outside the
   frozen corpus's midweek bracket — i.e., the data unlike the accepted
   same-source data on the commensurable subset. (Midweek p50/p90 sit
   comfortably inside.)
3. **A corrupting venue seam:** seam error at a scale that materially
   distorts the consuming signal (DS-05's 20d cross-sectional return
   ranks, tens of pips). (Measured seam ≤ ~1 pip p90 on the overlap.)
4. **A registered gate, not a preparation screen:** if the band had been
   frozen as a gate of an already-registered scored cycle, acceptance
   would require the registered amendment procedure (amend + independent
   review BEFORE admitting, per the OI-1 divergence-note law) — and even
   then the rejection typing for existing data would be an admission
   FAIL label, not `NOT_RUN_INPUT_END`, which would still be false.
5. **Evidence of a source change on 2026-07-01** (e.g., an IDEALPRO
   quote-feed regime change) making the Friday width new behavior rather
   than the day-set effect. (Against: the frozen corpus shows the same
   Friday regime in the same quarter and full-window; AUD/CA midweek
   medians match the C1 anchors, so no level shift.)

Absent all five, rejection would record a false cause and burn 46.9% of
fold 8 for DS-05 to remedy a defect in a screen, not in the data.

---

## 5. Evidence index

- `g6_pull/G6_PULL_REPORT.md` §6 (both checks), §7 (verdicts, PASS-with-disclosure), §7 consequence paragraph
- `g6_pull/VERIFICATION.json` (`pre_registered_band: FAIL` both; `same_source_control`; `gross_error_screen: PASS`; `source_bracket_check: PASS`; forming-bar disclosure)
- `g6_pull/MANIFEST.json` (16 files, identities conId 14433401 / 15016062, request parameters)
- `g6_pull/verify_g6_pull.py` L26/L112/L126 (band constants; anchor comment) · `g6_pull.py` L52-54 ("sanity anchors only")
- `G5_G6_SPREADS_INPUTEND.md` §1.5 (async first/last prints; open-side vs close-side), §1.8 (frozen band tables), §2.3(b) (`NOT_RUN_INPUT_END` semantics), §2.2 (channel audit)
- `SLEEVE-FX5-100K-V1/pitcost/COST_AUTHORITY_TABLE.md` §C1 (anchor definition: Friday 20:00 UTC, H1 ANC `s_open`, panel venue, sleeve window, n=199/247 of 286) + caveat (ii) (panel↔IBKR transfer UNMEASURED)
- `OI_DECISIONS_APPLIED.md` (OI-1 panel-of-record; OI-2 blocker + option (c) exploratory-only)
- `DRAFT_AMENDMENT_EXPLORATORY_ONLY.md` (no PASS reads; no after-cost PASS) · `PLAN_DAILY_SUCCESSOR_DRAFT.md` §0b ¶2 G5/G6 rows, ¶4, §5, §7 items 5/7 · `ACTION_PACKET_GATES.md` (owner decision 3)
- Fresh re-measurements (this session, read-only, reproducible): 16/16 sha re-hash; G6 stats re-derived (p50/p90, midweek/Friday medians, top-13 weekday composition); frozen-corpus NZD/CHF close-side pips stats Q3-2026 and FULL (n=1553); midweek brackets; H1 ANC parquet sha re-verification (both match pins `4e0ca174…` / `335a6e2a…`); June-2026 venue-seam overlap (n=20).

## Ruling in one line

**(b): the pre-registered `p90 < 8 pips` band FAIL stands, recorded, never
relabeled — it was never a lawful calibration for an async HMDS daily
close-side statistic (it is unsatisfiable even by the frozen accepted
corpus, and the C1 anchor is a different venue/clock/day-set whose transfer
the cost table itself labels UNMEASURED); the data is admitted for input
completion only upon owner freeze of HMDS-D1-CLOSE-ENVELOPE@1 (§3), which
is stricter on every defect mode that is real and refuses to gate on the
Friday construction property it cannot discriminate; `NOT_RUN_INPUT_END`
is false for bars that exist and would burn 46.9% of fold 8's DS-05
sessions to remedy a screen defect.**

Nothing herein scores, registers, freezes or amends anything: the freeze
act is the owner's; OI-2 stands; no PASS inferred from any cell.

— end G6_ADJUDICATION —
