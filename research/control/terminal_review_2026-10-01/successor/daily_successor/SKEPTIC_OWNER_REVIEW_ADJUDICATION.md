# SKEPTIC_OWNER_REVIEW_ADJUDICATION — corrected DAILY-successor packet (2026-10-01)

Fresh-context skeptic (no authorship of any adjudicated object). Read-only
except this one file. Objects adjudicated (all uncommitted):

- `…/successor/daily_successor/PLAN_DAILY_SUCCESSOR_DRAFT.md` (incl. §0b
  OWNER REVIEW ADDENDUM) — "the Plan"
- `…/successor/OI_DECISIONS_APPLIED.md` — "OI"
- `…/successor/SUCCESSOR_PLAN_DRAFT.md` (§3.4, §7b) — "SPD"

Corpus quote-verification sources (read this session, verbatim):
`research/control/FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/USDJPY.md`
(S63/S65/S83), `symbols/EURUSD.md` (S6/S61/S85), `symbols/AUDUSD.md`
(S35/S81/S100), `symbols/USDCAD.md` (S90). Arithmetic via
`.venv/bin/python` (date math and row counts only; no engine, no S1, no
network, no ledger).

---

## Q1. Exploratory vs validation labels — RULING: law CORRECT, application INCOMPLETE (BLOCKING residual in §2/§4/§7)

**Is §0b ¶4's labeling law itself correct?** Yes. Its three claims each
check out: (i) the 2020–2026 daily folds are cut from panels whose
underlying higher-clock series (EUR/GBP/JPY M1, AUD/CAD H1) were inside
the PC12A exposed window 2021-01-08→2025-12-26 (Plan §2.1's own
disclosure); (ii) "a new identity does NOT make those folds untouched
OOS" is the conservative and correct reading — the corpus text itself
was written 2026-09-28 with PC12A forensics knowledge (§2.1(ii)), so
even never-scored-at-D1 cells carry selection-side contact; (iii)
"untouched-input series (NZD/CHF/XAU/EIA) do not cure vehicle-side
exposure" is sound because the *traded* instrument's path is what the
PASS bar consumes.

**Sharpest formulation (which folds × which legs × which label):**

- **All folds of the §2 calendar (LEARN 2021-10-01→2022-09-22, embargo,
  folds 1–8 2022-09-30→2026-09-24, unscored tail), for BOTH surviving
  legs, = EXPLORATORY / hypothesis-generating. There is no validation
  surface anywhere in 2020–2026 for any surviving leg.**
  - DS-03: vehicle USDJPY = PC12A-exposed (M1 BID/ASK panel, PC12A-traded
    per §1.1 row 3); input I-JPY is exposure-adjacent by declared
    aggregation; its untouched inputs (RNGWHHD/RBRTE) do not cure the
    vehicle side.
  - DS-05: vehicle EURUSD = PC12A-exposed; 5 of 7 inputs
    (EUR/GBP/JPY/AUD/CAD) exposure-adjacent; NZD/CHF untouched but
    no-cure.
  - Note the asymmetry in §0b ¶4's own parentheticals (it names DS-03's
    *vehicle* exposure, DS-05's *input* exposure); both legs are in fact
    exposed on both channels, so the conclusion is airtight either way.
- **Prospective folds (post-registration accumulated daily bars) are the
  ONLY surface that can ever carry the VALIDATION label and the ONLY
  surface on which PASS bars may read** — for both legs, once ≥6×26w have
  accumulated (see Q2).

**Consistency THROUGHOUT the plan: FAILS.** §0b's supersession clause
makes the 2-leg/EXPLORATORY state legally operative, but the operative
sections were not conformed:

- **§2 residual:** the header still reads "never-scored daily calendar"
  (true as trial accounting, but never-scored ≠ validating) and §2.1
  frames the calendar as "FRESH as a scored-cell space" ending with
  "The NZDUSD/USDCHF/XAUUSD/EIA inputs are untouched by any scored run
  at any date" (line 311) — input-level true, but §2 never restates the
  ¶4 consequence (no cure; EXPLORATORY; no PASS). §2.2 says "≥6×26w
  floor requires ≥156w of **test folds**; the calendar supports 8×26w …
  — proposed below", i.e. it presents folds 1–8 as *the* folds that meet
  the PASS calendar floor. Under ¶4 the ≥6-fold PASS floor can only be
  met by prospective folds.
- **§4 residual (the sharpest one):** the PASS-bars section does NOT
  scope acceptance to the prospective surface. Bar 1: "`netPnL(SLATE) >
  netPnL(B1S)` AND `maxDD(SLATE) < maxDD(B1S)`, **pooled over folds
  1–8**"; the inheritance block: "≥6-fold calendar floor — **met with
  8**". No prospective bar is defined anywhere in §4; a reader executing
  §4 as written would read PASS off the 2020–2026 folds.
- **§7 residual:** the gate list has no item freezing the prospective
  validation calendar, the EXPLORATORY typing of the §2 battery, or the
  post-registration accumulation law; G8 freezes "calendar §2" — i.e.
  the exploratory calendar only — as *the* calendar.

**Findings:** **B1** (BLOCKING) §4 PASS bars not scoped to the
prospective surface; §2/§7 not conformed to ¶4. **M3** (MINOR)
`SUCCESSOR_PLAN_DRAFT.md` §3.4 still says "Daily-cohort track unchanged
(≈10 folds feasible today conditional on data-lane gates + owner
D-1..D-7)" — under ¶4 no DAILY fold cut from 2020–2026 panel data is
validation for the surviving legs (both vehicles PC12A-exposed), so
"feasible today" is old-law language; the §3.4 non-overlap criterion it
cites ("non-overlapping with the 2021-01-08→2025-12-26 EXPOSED window")
is not satisfied at the input level by the §2 folds. **I4** (INFO)
§2.1's "untouched" sentence should carry the ¶4 no-cure clause when
conformed (covered by the B1 edit).

---

## Q2. Truly prospective calendar — RULING: WORKABLE and HONEST only as an accumulation play; earliest honest VALIDATION ≈ 2029-09-27 (R = 2026-10-01); "nothing PASSes before then" is explicit in §0b ONLY, not in the operative sections

**Definition (¶4):** prospective = data accumulated AFTER the
registration date (post-registration daily bars forward). Computed
(`.venv/bin/python`, 2026-10-01):

- ≥6 × 26w folds = **156 weeks = 3.0 years = 1,092 calendar days** of
  accumulation. At ~261 bars/yr that is ~783 bars; 6 × 26w × 5 d/wk =
  780 trading days — the two estimates agree (~3.0 yr).
- With registration R ≈ 2026-10-01 and prospective fold 1 opening at R
  (indicator warmup served from never-scored pre-registration bars —
  lawful: warmup is arithmetic, not selection exposure; the plan should
  SAY so, else a strict reader adds the 60d max corpus lookback):
  - fold 1 2026-10-01→2027-04-01 · fold 2 →2027-09-30 · fold 3
    →2028-03-30 · fold 4 →2028-09-28 · fold 5 →2029-03-29 ·
  - **fold 6 closes 2029-09-27 = earliest honest VALIDATION date**
    (2029-10-04 if a 1-week post-registration seal precedes fold 1).
- Cross-reference: the M1-track's earliest complete 6×26w evaluation is
  2029-12-29 (SPD §3.4) — the DAILY track's honest date is ~3 months
  earlier, same order: **~3 years of disciplined accumulation, no lawful
  shortcut.**

**Is the plan explicit that NOTHING before then can PASS?** §0b ¶4 is
explicit: "PASS bars apply ONLY on the prospective surface; the
2020–2026 battery may run as EXPLORATORY evidence at most." But the
operative sections are not (finding B1): §4 reads PASS over folds 1–8,
and §7/G8 freeze §2 as the calendar. Explicitness lives only in the
addendum; it must be propagated (minimal edits below) or a registration
executed on the unconformed text could read PASS off 2020–2026.

**Workability gaps (beyond arithmetic):**

- **M2a** (MINOR) No ongoing-collection law for the prospective surface.
  G6 backfills AUD/CAD D1 only through 2026-09-30; the surviving legs'
  post-registration inputs need named continuing channels: I-JPY/I-EUR/
  I-GBP via the active live collector; I-AUD/I-CAD/I-NZD/I-CHF via
  scheduled IBKR HMDS D1 pulls (same method as the executed probe); EIA
  via its channel. Without this, DS-05's prospective folds starve silently.
- **I3** (INFO) The prospective-only PASS raises the price of floor
  starvation: campaign 20/3/100 per leg per fold (§3) against two
  selective rules (DS-03's NATGAS +15%/Brent-flat entry is rare) —
  honest typing is `NOT_RUN_THIN`, but a thin prospective fold costs
  calendar that cannot be recovered. Also: with warmup possibly needing
  pre-R bars, state the warmup law explicitly (included in the edit).

---

## Q3. Slate-reduction legality — RULING: all five parkings LEGAL and consistent with the plan's own disclosures; DS-03/DS-05 survival JUSTIFIED with ONE defect (G1 node A, BLOCKING)

Owner law (§0b ¶1): "nếu phải phát minh rule mới thì park chân đó" (if
admission requires inventing a rule, park the leg). Parking is the
conservative direction; the law constrains *admission*, so any parking
is lawful — the checks below verify the *stated reasons* match the
plan's earlier disclosures and the corpus.

**Per-leg verification (corpus quotes re-read this session):**

- **DS-01 — LEGAL.** §1.1's DS-01-a discloses a real corpus tension,
  verified in `AUDUSD.md` S81: hypothesis "AUDNZD **neo về mean dài
  hạn**" (mean-reversion) vs trade line "long AUDUSD + short NZDUSD size
  1:1 **khi z>2**" (pro-z side) — the z sign/fade direction genuinely
  requires an owner pick. DS-01-b verified: coupling "S35 hai policy
  path hội tụ mới vào"; S35 is AUDUSD's own carry rule with "Data: 10y
  yields" — not in this cohort, inputs unevidenced. Two owner choices =
  two potential inventions → park matches the law and §1.1's own
  "(owner may … park at registration)" option.
- **DS-02 — LEGAL.** `USDJPY.md` S63 verified: "short USDJPY
  beta-weighted **với long gold đã có (hedge completion)**" — the corpus
  presumes an existing long-gold book; under OI-3 gold is SIGNAL-ONLY,
  so the executable re-scope changes the trade shape (a one-sided short
  is not the corpus's hedged structure). The Plan itself flagged exactly
  this tension (§8-a(v)); the owner resolved it by parking. Consistent.
- **DS-04 — LEGAL.** `USDJPY.md` S83 verified: "Coupling: **không chạy
  khi US event tuần đó (FOMC/NFP)**" — a mandatory veto needing a named
  events-calendar source not on file; running ungated (the §1.1 default)
  would modify the corpus entry law, and the owner's stricter reading
  (drop = modify → park) is the same logic §0b applies. (DS-04-a's
  four-extra synthetic crosses were a further owner declaration —
  parking subsumes it; the stated reason is a subset of the full
  invention surface, harmlessly so.)
- **DS-06 — LEGAL.** `EURUSD.md` S61 verified: "Coupling: **BTP-Bund
  không nở lớn (fragmentation gate)**" — requires BTP-Bund daily, not on
  file; §1.1's DS-06-a said exactly this and offered park as an option.
- **DS-07 — LEGAL, stated reason UNDERSTATED.** `EURUSD.md` S85
  verified: the Trade line is "fade residual với holding theo half-life
  Kalman implicit" — **no stop exists in the corpus text** (confirmed),
  so §0b's "corpus has NO stop; adding one = invention" is factually
  right. But §1.1 never proposed adding a stop (it ran as-is,
  disclosed), and S85's coupling is "**same fragmentation gate như
  S61**" — DS-07 ALSO carries the unfireable BTP-Bund gate, plus
  Kalman state/obs noise hyperparameters that are owner declarations.
  The parking is legal (conservative direction); the reason line just
  names one of three invention surfaces. **I2** (INFO).
- **S100 / S090 triage parks (§1.2)** — spot-verified against corpus
  (S100 "kill-switch của S31/S32/S63", optional scalp "stop siết"
  unparameterized; S90 "re-weight petro factor trong S88", "Data: 2
  futures D") — park reasons match the corpus text exactly.

**DS-03 survival — JUSTIFIED, one defect.** Quote-verification
(`USDJPY.md` S65, line 241): the Plan's DS-03 block quotes Signal /
Trade / Risk(ellipsed) / Coupling **verbatim** — "Signal: NATGAS 10d
ret > +15% (breaking structure) **khi Brent flat**. · Trade: long USDJPY
5 phiên, stop 1×ATR. … · Coupling: **chỉ khi Brent flat** (để tách
channel — nếu Brent cùng chạy thì là S64)." The Brent-flat condition is
doubly stated — inside the Signal line AND as a "chỉ khi" (= only when)
coupling — so the Plan's reading ("part of the entry law per the
coupling line") is faithful, and the HH-as-JKM-proxy bias is indeed
disclosed in-rule (Risk clause; Hypothesis "NATGAS (proxy JKM lệch)").
Param gaps: ATR window (D1 ATR-14) is a disclosed convention declaration
— lawful under the Plan's param-source law, and G7 marks the DS-03 set
complete. **DEFECT — B3 (BLOCKING):** the LEARN grid G1 includes "A no
filter (off)" as a selectable node. If LEARN selects A, the registered
rule runs *without* the corpus-mandated Brent-flat gate — a rule
modification produced by grid selection, directly contradicting the
owner's own parking logic applied to DS-04 ("dropping the gate =
modifying the rule") and the corpus's own S64/S65 channel separation
("nếu Brent cùng chạy thì là S64" — entering while Brent runs trades
S64's setup under S65's label). Also **M4** (MINOR): §3's
floor-failure law collapses a thin grid "to the frozen default" but G1
names no default node.

**DS-05 survival — JUSTIFIED.** Quote-verification (`EURUSD.md` S6,
line 264-266): Plan quote verbatim — "Signal: rank 20d return của
{EUR,GBP,AUD,NZD,CHF,JPY,CAD} vs USD; vào EURUSD long chỉ khi EUR rank
1–2 · Trade: hold tới khi rơi khỏi top-3, stop 2×ATR · … · Coupling:
rank nhất quán 2 tuần liên tiếp mới vào." The coupling-as-law reading is
verified: "…**mới vào**" = "only then enter" — unambiguous entry-gating
language, and the Plan keeps it mandatory (does not drop it, does not
treat it as advisory). Every other parameter (20d rank window, rank 1–2
entry, top-3 exit, 2×ATR stop) is corpus-quantified; the single
PARAM-GAP (ATR window) is a declared convention. No invented rules. The
FAMILY_HISTORY_NEGATIVE prior label stays carried.

---

## Q4. Gate table completeness — RULING: G1–G9 covers every §7 precondition; THREE registration-phase items missing (one substantive)

Cross-read of §7's six-item list vs the §0b ¶2 table:

| §7 precondition | covered by | check |
|---|---|---|
| §7.1 OI-2 statement exists; measured values frozen into kernel | G1 + G2 | ✓ (G2's "WHERE MEASURED (law in ¶3)" matches §7.1's freeze-into-kernel + §7.3's re-labeling) |
| §7.2 PIT gates: OI-1 labels; σ tripwire; VIX re-verify | G4 + G3 | ✓ (NZD 64.64 / CHF 49.62 carried; XAU σ at freeze — never loosened) |
| §7.3 cost gates: daily-band derivations; U2/U3/U4 re-labeled | G5 (+G2) | ✓ |
| §7.4 vehicle gates: sha-pinned panels; D1 aggregation; DS-04-a synthetics; PARAM-GAP declarations | G7 | ✓ (DS-04-a now moot by parking — G7's generic wording absorbs it) |
| §7.5 D1 input-completion / fold-8 truncation typing | G6 | ✓ |
| §7.6 selection freeze | G8 | ✓ in coverage, **but its §7 text says "this slate (7 legs)"** — stale vs §0b ¶1 (folded into B2) |
| §6 item 4 / SPD §7b quote-CCY implementation + reconciliation | G9 | ✓ (the only §7-external precondition properly captured) |

**Missing from the table:**

- **M2b (MINOR, substantive): no gate freezes the prospective validation
  calendar + EXPLORATORY typing + ongoing-collection law** (Q1/Q2). G8
  freezes only the §2 exploratory calendar. This belongs as a G-row.
- **M2c (MINOR): owner GO-phrase registration** — §7's Then-A1 text says
  "The typed GO phrase is registered at registration"; it is a
  registration-time act and belongs in the table (else a registering
  agent may execute `register` without it).
- **M2d (MINOR): fresh-context A7 prelaunch** — post-registration by
  §7's own sequence ("freeze → A7 → STOP before any scored GO"); it
  should appear as an explicitly phase-labeled row so the table, not
  only prose, carries the stop.

---

## Q5. Statement attribution law soundness — RULING: correct in its refusals; TWO under-specifications in the formulas (MINOR)

¶3's refusals are sound: (i) slippage is NOT measured by statements —
statements record own fills, not contemporaneous quotes, so "stays
DECLARED/PROVISIONAL" is right; (ii) "no after-cost PASS is
self-granted — an after-cost claim needs the governing cost lines
measured or carries the explicit PROVISIONAL label" correctly blocks
self-PASS; (iii) only actually-measured components upgrade — matches the
mission invariant (no inferred PASS).

**Defects in the two formulas as written:**

- **M1a (MINOR) — swap rate application cannot carry Wed×3.** ¶3:
  "attributed to backtest positions by **units × nights × rate**". A
  scalar rate × night-count averages away exactly the weekday structure
  the declared §5 calendar encodes (Sun×1 Mon×1 Tue×1 **Wed×3** Thu×1
  Fri×0 = 7 pip-nights/week; membership `u(E⁻) ≠ 0`). The measured law
  must be per-date: `Σ_nights u(n⁻) × r_ccy(n)` with r_ccy(n) the
  measured per-currency accrual rate of that calendar night — the
  weekday/weekend-roll concentration then comes from the statement
  itself and "replaces [the declared calendar] whole" (§5's own words).
  As written, the formula is not reproducible in the Wed×3 world.
- **M1b (MINOR) — commission matching under-specified + overlap-limited.**
  The window length is deferred ("within a time window (frozen matching
  rule)") without naming window value, multi-match tie-break,
  partial-size aggregation, or symbol normalization (ideal vs conId) —
  reproducible only after freeze unless the freeze-scope is named in the
  law. Deeper: the statement covers ~last 365d (OI-2 export
  instruction), so per-trade matching to backtest fills only binds
  where timestamps overlap (fold 7/8 tail + prospective folds);
  pre-overlap folds must use the frozen commission *schedule* — a
  measured-rate schedule extrapolated per fill, which deserves its own
  label (e.g. SCHEDULE-EXTRAPOLATED) rather than silent "MEASURED per
  trade".
- **I5 (INFO)** — consequence worth one sentence: since slippage stays
  DECLARED forever, every after-cost PASS in this plan permanently
  carries the PROVISIONAL label; and "governing cost lines" should be
  enumerated once (spread MEASURED/MEASURED-DERIVED + commission
  MEASURED + swap MEASURED-rate + slippage DECLARED).

---

## Q6. Consistency sweep — RULING: no residual "only gate" or after-cost-before-G2 claims; ONE stale "folds feasible today" in SPD; §3 does NOT scale — rescope required (BLOCKING)

- **"OI-2 is the only gate":** none found. The Plan's status header
  calls OI-2 "the binding **blocker**" (accurate — blocker ≠ only gate);
  §0b ¶2 explicitly "corrects any 'single-gate' phrasing"; §7 lists six
  conditions. Clean.
- **"Untouched folds":** no sentence in the three objects claims the
  folds are untouched. Residuals of the *class*: Plan §2.1's "inputs are
  untouched by any scored run at any date" (input-level true, needs the
  ¶4 no-cure clause — folded into B1) and **SPD §3.4's "Daily-cohort
  track unchanged (≈10 folds feasible today…)"** (M3) — old-law
  validation feasibility language, unconformed to ¶4. OI's "S1 sealed
  tail untouched" is a different, correct usage.
- **After-cost capability before G2:** none found. §5 gates every
  number on the export landing AND being "frozen into the kernel" (= G1
  + G2); §7.1 binds registration itself to the freeze-into-kernel step;
  SPD §3.5 keeps DECLARED bands with the statement as "the measured
  unlock". Clean.
- **Budget §3 (does it scale?): NO — hard-typed to the 7-leg draft and
  frozen by G8/§7.6 as-is → B2 (BLOCKING).** Stale artifacts: §1.0
  "Result: 7 legs admitted"; §1.1 heading "Admitted legs" with rows
  1–7; §2.3 "All seven legs"; §2.4 "Five legs (DS-01, DS-04, DS-05,
  DS-06, DS-07)" / "counts fully only for DS-02/DS-03"; §3 "SLATE — the
  7-leg daily book", "LORO × {DS-01..DS-07} | 7 | 8 | 56", "15 ≤ 24 ✓;
  118 ≤ 120 ✓", G2 (DS-07 Kalman band) LEARN rows; §4 "B1S is the same
  7 legs", P8L's DS-06/DS-07 cluster note; §5 table "NZDUSD (vehicle,
  DS-01)"; §6.4 "USDJPY legs (DS-02/03/04)"; and sharpest: **§7 item 6
  "Selection freeze: this slate (7 legs)"** — the freeze text itself
  contradicts §0b ¶1 and would be the operative sentence at
  registration.
  **Rescoped budget (computed, DS-03/DS-05 only):** SLATE 1×8 + B0 1×0 +
  B1S 1×8 + B2 1×8 + B3 1×8 + C2 1×8 + LORO×2 = 16 + ×1.5 stress×2 = 16
  → **10 identities / 64 scored rows**; LEARN grid rows = G1 only
  (3 nodes; **G2 moot — DS-07 parked**) → **67 total**; caps 10 ≤ 24 ✓,
  67 ≤ 120 ✓ (headroom 53 rows). Consequence: §3's ×2.0-reporting-tier
  deferral justification ("one more 8-fold identity needs 8 rows and
  only 2 remain") is **obsolete** — restoring ×2.0 on SLATE and B1S
  costs 16 rows → 83 ≤ 120 ✓. Either restore ×2.0 reporting rows or
  re-justify deferral at registration (the §8-c question "does PB2 P6b
  admit deferral at all" re-opens at the smaller size). Also note P8L /
  LORO degenerates to a 2-row table (I3).

---

# Consolidated findings

**BLOCKING (3)**

- **B1** — §4 PASS bars still scoped to pooled folds 1–8; §2/§7 unconformed
  to §0b ¶4 (no EXPLORATORY restatement, no prospective-surface bar, no
  prospective-calendar freeze; §2.2 presents folds 1–8 as meeting the
  PASS calendar floor). Q1/Q2.
- **B2** — §3 budget + §7 item 6 freeze language stale for the 7→2 leg
  reduction (LORO ×7, 15/118 counts, G2 grid rows, "this slate (7
  legs)"); ×2.0-deferral justification obsolete at the rescoped size. Q6.
- **B3** — G1 grid node A ("no filter off") is a selectable rule-modification
  vector: it can drop the corpus-mandated Brent-flat entry gate (S65:
  "khi Brent flat" in Signal + "chỉ khi Brent flat" in Coupling),
  contradicting the owner's own DS-04 parking logic. Q3.

**MINOR (4)**

- **M1** (a, b) — ¶3 swap formula "units × nights × rate" cannot carry the
  Wed×3 weekday structure (needs per-date rate series); commission
  matching window/tie-breaks/symbol-normalization unnamed;
  schedule-extrapolation for non-overlap folds unlabeled. Q5.
- **M2** (a–d) — gate table additions: prospective-calendar + EXPLORATORY
  typing + ongoing-collection law; owner GO-phrase registration;
  A7-prelaunch (phase-labeled); §7 item 6 stale "7 legs" (same edit as
  B2). Q2/Q4.
- **M3** — SPD §3.4 "Daily-cohort … ≈10 folds feasible today" unconformed
  to ¶4 (those folds are EXPLORATORY-only). Q1/Q6.
- **M4** — G1 names no frozen default node for the NOT_RUN_GRID_THIN
  collapse path. Q3.

**INFO (5)**

- **I1** — calendar counting convention: 2020-10-02→2026-09-30 = 2,189
  interval days / 2,190 inclusive bars; the Plan's segments reconcile
  exactly under inclusive-bar counting (364+357+7+8×182 = 2,184; tail 6;
  LEARN 19.55–19.56%). Internally consistent; floor and ≤ checks hold
  either way.
- **I2** — DS-07's stated park reason understates (S85's coupling = "same
  fragmentation gate như S61" also cannot fire; Kalman hyperparameters
  are owner declarations); DS-04's reason could also cite DS-04-a.
  Parking remains legal (conservative direction).
- **I3** — 2-leg degeneracies: P8L/LORO is a 2-row table ("exactly-one-
  break" nearly trivial); campaign floors may starve selective rules —
  honest typing NOT_RUN_THIN, costlier now that PASS is prospective-only.
- **I4** — §2.1's "inputs are untouched…" needs the ¶4 no-cure clause
  (covered by the B1 edit).
- **I5** — slippage is permanently DECLARED ⇒ every after-cost PASS is
  permanently PROVISIONAL-labeled; enumerate "governing cost lines" once.

---

# VERDICT: **FIX_THEN_COMMIT**

The corrected packet is substantively honest — §0b's laws (2-leg slate,
multi-gate registration, attribution law, EXPLORATORY/prospective
split) are correct and the corpus quotes all verify verbatim — but the
operative sections below §0b were not conformed, and G8 would freeze
them as-is. Exact minimal edits (no restructuring; each is an insertion
or one-line replacement):

1. **(B1)** Plan §4, immediately under the heading, insert:
   "**Scope law (§0b ¶4, binding):** every bar in this section reads
   ONLY on the prospective surface (≥6×26w of post-registration
   accumulated daily bars; earliest honest evaluation ≈ 2029-09 for a
   2026-10 registration). The §2 2020–2026 battery (folds 1–8) is
   EXPLORATORY reporting at most — no PASS, no GO, no after-cost claim
   is readable from it; 'pooled over folds 1–8' below means exploratory
   reporting only." Then in bar 1 replace "pooled over folds 1–8" with
   "pooled over the prospective folds"; in the inheritance block replace
   "≥6-fold calendar floor — met with 8" with "≥6-fold calendar floor —
   met only by prospective accumulation (156w)".
2. **(B1)** Plan §2, under the heading, insert: "All folds in this
   section are EXPLORATORY per §0b ¶4 (both surviving legs trade
   PC12A-exposed vehicles; untouched inputs do not cure); no PASS reads
   here." In §2.2, replace "test folds" with "exploratory folds". In
   §2.1's last sentence, append "(input-level only; does not cure
   vehicle-side exposure — §0b ¶4)".
3. **(B2)** Plan §3, after the table insert:
   "**Rescope (§0b ¶1, binding — supersedes the 7-leg table above):**
   operative slate = {DS-03, DS-05}: SLATE 1×8, B0 1×0, B1S 1×8, B2 1×8,
   B3 1×8, C2 1×8, LORO×{DS-03,DS-05} 16, ×1.5 stress SLATE+B1S 16 →
   **10 identities / 64 scored rows**; LEARN rows = G1 only (3 nodes;
   G2 moot, DS-07 parked) → **67 total** (10 ≤ 24 ✓, 67 ≤ 120 ✓). The
   ×2.0-reporting deferral rationale ('only 2 rows remain') is obsolete
   — restore ×2.0 reporting rows for SLATE and B1S (16 rows, 83 ≤ 120 ✓)
   or re-justify deferral at registration. LORO/P8L is a 2-row table;
   report with that degeneracy disclosed."
4. **(B2/M2)** Plan §7 item 6: replace "this slate (7 legs)" with "the
   §0b ¶1 operative slate (DS-03, DS-05; parked legs frozen as parked)".
   Add item 7: "**Prospective validation law frozen:** ≥6×26w folds of
   post-registration accumulation (warmup served from never-scored
   pre-registration bars); EXPLORATORY typing of the §2 battery;
   ongoing-collection law for every consumed input (majors live
   collector; scheduled HMDS D1 pulls for AUD/CAD/NZD/CHF; EIA channel)."
5. **(M2)** Plan §0b ¶2 table, add three rows:
   "| G10 | Prospective validation calendar + EXPLORATORY labels +
   ongoing input-collection law frozen (§7 item 7) | NOT_RUN (freeze-time) |
   | G11 | Owner GO phrase registered at registration; GO reserved to
   the owner at the scored cycle's own gate | NOT_RUN (registration act) |
   | G12 | Fresh-context A7 prelaunch PASS (post-registration, before
   first scored run) | NOT_RUN (prelaunch) |"
6. **(B3/M4)** Plan §1.1 DS-03 grid line: replace "Grid (≤3 nodes, §3):
   A no filter (off) · B |RBRTE 10d ret| < 3% · C < 5%" with
   "Grid (2 selectable nodes — the Brent-flat gate is corpus-mandatory
   (S65 Signal 'khi Brent flat' + Coupling 'chỉ khi Brent flat');
   dropping it = rule modification per the §0b ¶1 owner law, cf.
   DS-04): **B** |RBRTE 10d ret| < 3% (frozen default) · **C** < 5%;
   node A ('no filter') is a REPORTED null-control only, never
   selectable; floor failure collapses to B, typed NOT_RUN_GRID_THIN."
   Mirror the "3 nodes each" wording in §3's LEARN-grid row to
   "G1: 2 selectable nodes (A reported null-control)".
7. **(M1)** Plan §0b ¶3: replace "attributed to backtest positions by
   units × nights × rate (frozen formula, reproducible)" with
   "attributed per held night n as Σ u(n⁻) × r_ccy(n) — r_ccy(n) = the
   measured per-currency accrual rate of that calendar night; the
   weekday/weekend-roll structure (cf. the declared Wed×3 calendar, §5)
   comes from the statement itself and replaces the declared calendar
   whole (frozen formula, reproducible)". Append to the commission
   sentence: "the G2 freeze names window length, multi-match tie-break,
   partial-size aggregation and symbol normalization; where statement
   timestamps do not overlap a backtest fold, the frozen commission
   SCHEDULE applies per fill, labeled SCHEDULE-EXTRAPOLATED."
8. **(M3)** SPD §3.4, after "Daily-cohort track unchanged (≈10 folds
   feasible today conditional on data-lane gates + owner D-1..D-7)."
   insert: "(Per the DAILY plan §0b ¶4 those folds are EXPLORATORY-only
   — daily-track validation is likewise accumulation-based
   post-registration; earliest honest 6×26w evaluation ≈ 2029-09/10 for
   a 2026-10 registration.)"

No edits to OI_DECISIONS_APPLIED.md are required (clean under every
sweep). After edits 1–8 the packet is committable; the committed state
remains DRAFT/NOT REGISTERED with the OI-2 NOT_RUN_STATEMENT blocker
standing, nothing scored, and no PASS inferred anywhere.

---

## Boundary compliance (this task)

Read-only except this one file
(`…/successor/daily_successor/SKEPTIC_OWNER_REVIEW_ADJUDICATION.md`);
`.venv/bin/python` used for date/row arithmetic only; no network, no
engine execution, no scored computation, no registry/eligibility/GO/
ledger/FAMILY_FAILURES write, no S1 touch, no orders, purchases or
keys; objects not edited; nothing committed. No PASS was inferred from
any NOT_RUN cell (mission invariant upheld; B1/B2/B3 exist precisely
because the operative text, if frozen uncorrected, would let a future
reader do so).

— end of adjudication —
