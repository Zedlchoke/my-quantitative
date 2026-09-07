# A7 Forex F2 — Novelty / Feasibility Audit of the Six-Proposal Pool

- Schema: `forex_f2_a7_novelty_audit_v1` (authoritative JSON: `a7_f2_novelty_audit.json`, same directory)
- Auditor: A7 (independent; audit artifacts only — no repairs, no production-code edits, no selection, no ranking, no scoring)
- Measured (UTC): 2026-09-03T00:25:38Z
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/forex/f3-a7-audit`
- Branch: `orca/forex-f3-a7-audit`
- Bootstrap SHA: `4b9ee91ef6c38af1cce6b0a6c68d52a27bb38c7e` — HEAD verified equal, status clean

## 1. Scope and inputs

Audited: the six F2 proposals under `research/proposals/forex/{a3_data,a4_calendar,a5_cost}/`
(JSON authoritative; .md narratives checked for consistency), against
`PLAN_forex.md` sections 1–2 and 9, `research/control/forex_run/f2_proposal_pool.json`,
`research/control/forex_run/data_manifest.json` (plus session/rollover/conversion
manifests), and the historical crypto-family evidence (NOTES.md §19–21,
`research/wayfinder/MAP.md`).

Input integrity: all six proposal SHA-256 digests recomputed and matched
`f2_proposal_pool.json` exactly; the pool wave SHA `aba863eb…` is an ancestor of
this audit HEAD. No digest mismatches.

Input limitation: `results/registry/experiments.jsonl` does not exist at the
bootstrap SHA; ancestry mapping used NOTES.md and MAP.md (both present at
bootstrap). Only family names/mechanisms were taken from that evidence.

## 2. Verdict table

| Proposal | Mechanism (short) | Verdict | Worst objection |
|---|---|---|---|
| FX2-A3-P1 | Rollover-boundary (17:00 ET) window premium, DST-correct | CONDITIONAL_ON_OWNER_DATA | LOW |
| FX2-A3-P2 | Cross-sectional relative-spread scarcity, dollar-neutral | CONDITIONAL_ON_OWNER_DATA | LOW |
| FX2-A4-P1 | DST-desync London–NY overlap premium | CONDITIONAL_ON_OWNER_DATA | MEDIUM |
| FX2-A4-P2 | Pre-release liquidity-withdrawal premium (NFP/CPI/FOMC) | CONDITIONAL_ON_OWNER_DATA | LOW |
| FX2-A5-P1 | PIT rate-differential carry, dollar-neutral, net-of-financing | CONDITIONAL_ON_OWNER_DATA | LOW |
| FX2-A5-P2 | Fixing/rollover window USD exposure (WM/R, Tokyo) | **INELIGIBLE** | **HIGH** |

Counts: **0 ELIGIBLE · 5 CONDITIONAL_ON_OWNER_DATA · 1 INELIGIBLE.**
Objection totals: 9 LOW, 3 MEDIUM, 1 HIGH, 0 CRITICAL.

Note on grading: every proposal honestly declares its missing real-FX data; that
alone is CONDITIONAL, never INELIGIBLE. The single INELIGIBLE rests on a
specification defect, not on missing data.

## 3. Checks that passed for all six

1. **Contract completeness (PLAN §9):** 6/6 — all declaration fields present and
   non-empty, including exact trial counts (2/2/3/3/4/4) with no-post-score-
   replacement statements.
2. **Prohibited-shortcut scan:** 0 violations across all five categories. A5-P1
   handles the carry shortcut explicitly (PIT vintages required, absence declared
   blocking, non-PIT sensitivity is a falsification trigger). A5-P2's direction is
   preregistered from the documented pressure sign, not observed profits.
3. **Data-availability honesty:** 6/6 — every grading matches measured fact
   (bid/ask 0/7 UNAVAILABLE fail-closed; rollover `BLOCKED_NO_BROKER_SCHEDULE`;
   holidays `SYNTHETIC_TEST_ONLY`; PIT macro UNAVAILABLE; zoneinfo DST real and
   tested — `research/assets/forex/sessions.py`, `tests/assets/forex/test_sessions_dst.py`
   verified on disk). No proposal implies unavailable data exists. A4-P1's
   "rollover not required" claim verified true by construction (08:00–12:00 NY
   never contains 17:00 NY).
4. **Source authority:** 0 fabricated citations detected. Three load-bearing,
   least-canonical sources independently verified by search — Ranaldo 2009
   (JBF 33, 2199–2206), Antolin-Diaz/Cenedese/Han/Sarno 2023 (SSRN 4565111,
   R&R RFS), Krohn/Mueller/Whelan 2024 (JF 79(1) 541–578, DOI 10.1111/jofi.13306;
   its documented USD-appreciates-into-fixings fact supports A5-P2's preregistered
   USD-long direction). Remaining entries canonical and bibliographically
   consistent; both proposals that could not fully verify a DOI string say so
   explicitly. No load-bearing claim rests on an unverified source.
5. **Outcome-blindness:** PASS 6/6 — no computed returns/PnL/backtests anywhere
   (all numbers are literature facts or preregistration arithmetic).

## 4. Per-proposal findings and objections

### FX2-A3-P1 — CONDITIONAL_ON_OWNER_DATA (worst LOW)
Sound clock-anchored design; the +6h control window was verified to land in the
deep Asia pre-open lull (18:45–19:45 UTC / 03:45 JST) and is genuinely event-free;
the DST-naive C2 control is a proper destruction test.
- OBJ-A3P1-01 (LOW): "stands as liquidity provider" framing contradicts marketable
  bar-close fills that pay the widened window spread; the net-of-cost window-
  premium claim itself remains coherent.
- OBJ-A3P1-02 (LOW): needs tick/≤1-minute quotes — finer than the 1h repo floor;
  must be named in the owner authorization.

### FX2-A3-P2 — CONDITIONAL_ON_OWNER_DATA (worst LOW)
Quote-state-only thesis is clean and well-scoped (one dealer panel, never
"global").
- OBJ-A3P2-01 (LOW): the +180-day shift placebo preserves persistent cross-
  sectional spread ordering, so it errs toward false destruction of a genuine
  slow-moving scarcity signal; conservative direction, no false-acceptance risk.
- OBJ-A3P2-02 (LOW): 1-minute aligned 7-pair panel required — above the 1h floor.

### FX2-A4-P1 — CONDITIONAL_ON_OWNER_DATA (worst MEDIUM)
Elegant pure-tzdb signal; only tzdb is available today, correctly identified.
- OBJ-A4P1-01 (MEDIUM): the preregistered gloss "autumn gap gives D=+6h" is
  arithmetically impossible: zoneinfo over 2025–26 shows D = tz(London)−tz(NY) is
  +4h on 28 days/year (both gaps) and +5h otherwise; D=+6h occurs 0 days. The
  detector (D≠+5h) and day-sets remain valid, but the wrong factual claim inside
  the signal definition must be restated from tzdb at freeze.
- OBJ-A4P1-02 (MEDIUM): the ±1-week label-shift placebo is contaminated in the
  March gap (~2–3 weeks long): shifted day-sets still contain a majority of truly
  desynchronized days, so the placebo is partially active exactly where the effect
  is predicted strongest; the autumn placebo is cleaner.

### FX2-A4-P2 — CONDITIONAL_ON_OWNER_DATA (worst LOW)
Timestamps-only design honestly avoids the PIT-vintage dependency; T+65min
placebo and matched non-release neighbour are genuine destruction controls; the
hard blockers (release calendar, rollover schedule) are correctly self-declared.
- OBJ-A4P2-01 (LOW): FOMC windows touch exactly ONE 17:00 boundary (the entry),
  not two as stated — verified by boundary walk (Tue 17:00 → Wed 13:55 = 20.9h,
  one boundary). Error overstates FOMC cost (conservative).
- OBJ-A4P2-02 (LOW): "14:00 with the 2011 presser-cycle conventions" conflates
  the 2011 presser introduction with the 2013 statement-time move; the per-event
  agency-calendar mitigation covers it.

### FX2-A5-P1 — CONDITIONAL_ON_OWNER_DATA (worst LOW)
The pool's canonical-carry proposal; sign-flip and rank-scramble controls are
genuinely destructive; the 1M-tenor neighbour is a justified cousin. Declared
feels-blocked status is accurate.
- OBJ-A5P1-01 (LOW): the PIT 3M/1M authorization must explicitly name LIBOR→RFR
  transition handling (declared vintages or sample splits); a single tenor-
  continuous authoritative vintage series may not exist.
- OBJ-A5P1-02 (LOW): EWMA halflife is "declared" but not numerically pinned; must
  be a fixed number in the freeze.
- Ancestry attention (MEDIUM visibility, not a rescue flag): mechanism shape
  (financing-premium accrual + sign-flip control + crash skew) is adjacent to the
  REJECTED crypto V6 CARRY family; openly declared, FX-native, and inside the
  PLAN §9 priority space. The freeze should record the distinction.

### FX2-A5-P2 — INELIGIBLE (worst HIGH)
- OBJ-A5P2-01 (HIGH, unresolvable → INELIGIBLE): the preregistered +6h placebo is
  broken. The anchor is the 1h bar containing 16:00 London; +6h is the bar
  containing 22:00 London, which zoneinfo shows equals 17:00 New York on 241 of
  261 weekdays in 2025 (~92%) — i.e. the placebo IS the New York 17:00 rollover
  bar, the largest documented daily spread-widening/financing event and the very
  object of the proposal's own variant B (18:00 NY, the hour after the roll, on
  the remaining DST-gap days). The stated premise "no benchmark fixing and no
  rollover event" is false (the proposal's own parenthetical arithmetic is
  internally inconsistent). The control therefore does not destroy the mechanism;
  it swaps the fixing event for the rollover event, making the stated placebo
  interpretation invalid and falsification criterion (b) able to fire on a genuine
  fixing premium. A required PLAN §9 element (causal negative control) is invalid
  as specified. A7 does not repair: within this frozen pool the objection cannot
  be resolved, hence INELIGIBLE. Everything else in the proposal is sound (the
  literature sign for USD-long-into-fixings verified; availability honesty clean),
  so a corrected fixing-window design must arrive as a new cycle proposal.
- OBJ-A5P2-02 (LOW): name says "financing-hour" but the primary scored anchor is
  the fixing window (variant B is swap-blocked).
- OBJ-A5P2-03 (LOW): 1h clock is coarse vs ~30-minute fixing microstructure;
  honestly declared, no intrabar claims.

## 5. Cross-proposal orthogonality (6×6, 15 pairs)

0 HIGH; 4 MEDIUM; 11 LOW. No two proposals are effectively the same mechanism.

| Pair | Grade | One-line justification |
|---|---|---|
| A3P1–A3P2 | MEDIUM | Same quote panel and 17:00-ET clock neighborhood; different information set (window drift vs relative-spread cross-section) and holding. |
| A3P1–A4P1 | MEDIUM | Both session-clock window premia in the same PLAN priority space; different windows, day-sets, causal variables (roll event vs tzdb desync). |
| A3P1–A4P2 | LOW | Roll-boundary cycle vs scheduled-event risk transfer; disjoint windows/day-sets. |
| A3P1–A5P1 | LOW | Clock-window premium vs rate carry; disjoint. |
| A3P1–A5P2 | MEDIUM | Both daily dealer-event families; primary anchors distinct, but A5-P2's blocked variant B would hold the same 17:00-ET roll bar — latent overlap if ever activated. |
| A3P2–A4P1 | LOW | Spread cross-section vs pure tzdb label; disjoint. |
| A3P2–A4P2 | LOW | Quote-state vs release calendar; disjoint. |
| A3P2–A5P1 | MEDIUM | Both dollar-neutral cross-sectional sorts over the same 7 pairs; information sets disjoint (spread vs rates). |
| A3P2–A5P2 | LOW | Cross-sectional state vs single-factor deterministic schedule; disjoint. |
| A4P1–A4P2 | MEDIUM | Same family shape (calendar-window basket, 3-trial structure); distinct exogenous drivers (tzdb vs agency calendars), barely overlapping windows. |
| A4P1–A5P1 | LOW | Calendar premium vs carry; disjoint. |
| A4P1–A5P2 | LOW | DST-gap day-set vs daily fixing schedule; distinct. |
| A4P2–A5P2 | LOW | Both deterministic calendar windows but different clocks and direction sources. |
| A4P2–A5P1 | LOW | Event timing (explicitly not rate-based) vs carry; disjoint. |
| A5P1–A5P2 | LOW | Carry vs fixing window; A5-P2 uses no rates by design. |

## 6. Ancestry vs prior crypto families

Basis: NOTES.md §19–21 and MAP.md (experiments.jsonl absent at bootstrap).
Rejected: V6 CARRY-1D/3D/7D (crypto funding carry), H-XSECT-MOM-v1,
H-VOLCOMP-BRKOUT-v1, H-FUNDCROWD-MR-v2, V9 multi-family (5/5). Pending, never
rejected: V7 XSECT-FUND-PRICE-DIV. Blocked: V10 aggressor-absorption panel.

| Proposal | Adjacent families | Hidden rescue? |
|---|---|---|
| A3-P1 | none (no 24/7 analog to a dealer day-end) | No |
| A3-P2 | H-XSECT-MOM (rej.), V7 fund-price-div (pending) — shape only (dollar-neutral cross-sectional sort) | No |
| A4-P1 | none (no DST in crypto) | No |
| A4-P2 | none (no scheduled-release clock in crypto) | No |
| A5-P1 | V6 CARRY (REJECTED) — closest shape adjacency: financing-premium accrual, sign-flip control, crash skew; openly declared, FX-native signal/financing, PLAN-sanctioned priority space | No (MEDIUM-visibility note for freeze) |
| A5-P2 | none material (generic "clock exposure" idea only) | No |

Hidden rescues found: 0.

## 7. Lane isolation

PASS. Each of `orca/forex-f2-a3-proposals` (`331af4a`), `orca/forex-f2-a4-proposals`
(`44cbefe`), `orca/forex-f2-a5-proposals` (`7a1d6f1`) has exactly one lane commit
on the shared base `aba863eb`, touches only its own four files under
`research/proposals/forex/<lane>/`, and each tip matches
`f2_proposal_pool.json.lane_commits`. No lane read/write evidence crosses lanes;
no production code touched.

## 8. Blockers (evidence for the selection freeze)

1. **Zero ELIGIBLE proposals.** All five surviving proposals are blocked on owner
   data authorization (real bid/ask 0/7; rollover/swap schedule authority; PIT
   rate vintages incl. LIBOR-transition handling for A5-P1; official release-
   timestamp ingest for A4-P2; authoritative holiday tables; provider session
   convention). Per PLAN §9, fewer than two eligible families closes
   `FOREX_BLOCKED_SELECTION_INSUFFICIENT` unless the owner authorizes the named
   data before the freeze.
2. **FX2-A5-P2 INELIGIBLE as specified** (OBJ-A5P2-01 HIGH): the negative-control
   defect is a specification error, not a data gap, and cannot be resolved inside
   this frozen pool. A corrected fixing-window proposal is a future-cycle input.
3. **experiments.jsonl absent** at the bootstrap SHA; ancestry relied on
   NOTES.md/MAP.md.

## 9. Assumptions

- Proposal JSON is authoritative; .md narratives consistent with their JSON.
- WebSearch used sparingly: exactly three spot-checks (one per proposal for
  A4-P1, A4-P2, A5-P2, on each one's most load-bearing, least-canonical source);
  other sources graded on bibliographic consistency.
- Clock-arithmetic objections use zoneinfo tzdb 2025–2026 rules; policy changes
  (e.g. DST abolition) are declared risks inside the affected proposals.
- This artifact is evidence only: no selection, no ranking, no scored values,
  no repairs. Audit computation was limited to input digests, git history, and
  tzdb calendar arithmetic on preregistered window definitions.
