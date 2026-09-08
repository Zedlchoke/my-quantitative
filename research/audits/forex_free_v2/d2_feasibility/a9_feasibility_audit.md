# A9-F Feasibility Audit — FOREX-FREE-V2, six proposals (F2-D2)

- Auditor: A9-F (independent feasibility auditor; no PnL computed, no repairs)
- Cycle: FOREX-FREE-V2, phase F2-D2
- Branch: `orca/forex-free-v2-a9-feasibility`, base `24c7230`
- Measured UTC: start `2026-09-04T03:00:11Z`, simulations `2026-09-04T03:18:33Z`
- Attestation: **no PnL computed; schedule/descriptive analysis only; read-only snapshot; S1 untouched**
- Machine-readable twin: `a9_feasibility_audit.json` (same directory)

## Method

For each of the six proposals in `research/proposals/forex_free_v2/{a4,a5,a6}_lane/proposal_{1,2}.json`
I ran a **schedule-only simulation on the real snapshot** (counts of decisions / entries /
round-trips / cap events; zero PnL, zero traded returns), using the read-only V1 snapshot
`/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v1/integration/data_raw/forex_free_v1`
via `research/assets/forex_free_v1/td_loader.load_pair_h1` and the
`research/assets/forex_free_v2/data_authority.py` conventions. Descriptive statistics
(median bar ranges, |close-to-close| moves in bps, cross-sectional demeaned extreme spreads)
are direction-agnostic data statistics, never conditioned into a strategy return.

All six proposals were **schedule-simulated on real data**. Observed max frequency:
every proposal respects **<= 1 entry/pair/UTC-day** (single exception: A6-P1's decision-day
dedup produced 2 entries on 79 pair-days — its own cap-key defect, see below) and
**<= 3 RT/pair/week** after the frozen governor/substitution (binding counts below).

## Data-level facts (all 7 pairs, snapshot 2020-01-29/30 .. 2026-09-02)

- Bars per pair: 42,646–42,775. Inside-open missing bars: 283–349/pair (~0.8%).
- **~3,400–3,535 out-of-session bars per pair (~8%)**: the provider emits Sunday bars from
  ~19:00Z and Monday 00:00Z bars (present on 98.3% of Mondays) although the frozen weekly
  convention (Sun 21:00 NY open) classifies them out-of-session.
- **16:00 America/New_York flat bar is ABSENT on 410/2408 pair-Fridays (17%)** — provider
  short-days (e.g. EUR/USD Fridays 2021-07-09/16 end at 13:00Z; 2020-12-25 ends 17:00Z) —
  and on 54 other weekday pair-days.
- Descriptive magnitudes: median H1 true range 9.9–15.8 bps; median |4h| move 7.9–14.5 bps;
  |8h| 13.0–22.0 bps; |12h| 17.3–26.9 bps. A5-P1 decision spread (demeaned extreme-vs-extreme,
  day-to-date): median 57.8 bps (p25 41.5). A5-P2 prior-session bottom2−top2 demeaned spread:
  median 114.3 bps (p25 78.4; proposal claimed 50–120).

## Verdicts

| Proposal | Verdict | Blocking finding |
|---|---|---|
| FXFV2-A4-P1 | **FEASIBILITY_PASS** | — (MEDIUM findings below) |
| FXFV2-A4-P2 | **FEASIBILITY_PASS** | — (MEDIUM findings below) |
| FXFV2-A5-P1 | **FEASIBILITY_FAIL** | HIGH: Friday missing-flat fallback unsatisfiable (36 legs) |
| FXFV2-A5-P2 | **FEASIBILITY_FAIL** | HIGH: same, 4-leg amplified (140 legs unresolvable) |
| FXFV2-A6-P1 | **FEASIBILITY_FAIL** | HIGH x2: no missing-flat fallback (110 entries) + missing-bar semantics ambiguity (11x) |
| FXFV2-A6-P2 | **FEASIBILITY_FAIL** | HIGH: no missing-flat fallback (157 entries) |

All four failures share **one blocking class**: on provider-short Fridays the 16:00 NY bar
does not exist; A6 has no fallback at all, and A5's frozen fallback ("first available later
H1 bar open **the same UTC day**") has no bar to fill at — the only outcomes are forbidden
weekend carry or an undefined schedule. A4's `early_forced_flat` fallback ("open of the
immediately preceding existing bar") is sound and was exercised 70 (P1) / 89 (P2) times.
The four failures are otherwise schedule-feasible (caps hold, cell floors clear) and are
repairable **only by an owner-side frozen amendment**; this audit does not repair.

## Per-proposal detail

### FXFV2-A4-P1 — Tokyo compression → London-morning break — PASS
Simulated: **1,708 entries; 0.72 RT/pair/week; max 1 entry/pair/UTC-day; max 3 RT/pair/week**
(85 pair-weeks at cap, 9 signals dropped). Folds 499/574/635 (≥400 each); full 1,708 (≥1,200);
compressed decisions 2,768 (min/pair/fold 93 vs floor 80). First state evaluable 2020-03-04/05.
- **MEDIUM**: realized frequency 0.72 is **below** the frozen band 1.0–1.6 — compression
  incidence 23.8% (assumed 25–35%), break-given-compression 61.7% (assumed 85–95%). Decision
  floor margin thin (1.16x).
- **MEDIUM**: Tokyo range [00:00,09:00) UTC overlaps the London-morning window by 1–2 bars
  (BST 07/08Z; GMT 08Z). A decision bar inside its own T_H/T_L can never strictly breach —
  self-referential dead bars; effective trigger window 2–3 bars, DST-asymmetric, not "4 bars".
  Not lookahead (bar completed before next-open entry), but a spec defect to resolve.
- **MEDIUM** (cross-cutting): Monday Tokyo ranges are complete only via convention-out-of-session
  Monday 00:00Z bars and then span the weekend gap; bar-universe rule unpinned.
- LOW: fold-1 start 2020-03-01 vs first evaluable 2020-03-04/05. LOW: cap "not expected to
  bind" is false (85 pair-weeks).
- Cost hurdle: 3 bps RT vs median 8–11h move 13–22 bps → ~15–25% capture (tier-2 6 bps → 30–45%).

### FXFV2-A4-P2 — London-AM break → retest-hold — PASS
Simulated: **4,029 entries; 1.70 RT/pair/week; max 1/pair/day; max 3/week** (571 pair-weeks at
cap, 166 dropped). Folds 1,297/1,319/1,413 (≥400); states: retest 4,202 / void 5,995 /
no-resolution 1,417; decisions 10,197 (min/pair/fold 434 ≥ 150). Entry deadline (<20:00 London)
verified safe in all four offset combinations incl. EU/US desync weeks (≥1h to flat); entries
13–19Z only; 89 early-forced-flat events handled.
- **MEDIUM**: realized frequency 1.70 is ~2x the frozen band 0.7–1.3; the weekly cap binds in
  ~15% of pair-weeks — the governor materially truncates the scored sample (drop-not-defer),
  contradicting "expected slack ~3x".
- LOW: whether the break bar itself can be the void bar is unspecified.
- Cost hurdle: 3 bps vs 1–7h holds (median 4h move 8–14 bps) → ~20–35% capture — the most
  cost-demanding of the six.

### FXFV2-A5-P1 — USD-neutral 2-leg same-day dislocation RV — FAIL
Simulated: 1,734 gated decision days; gate met 38.9% (claimed 50–70%); **673 RT
(1.99 construction-RT/week; 0.29/pair/week)**; folds (legs) 408/436/502 (≥100); decisions ≥ 250;
max 3 RT/pair/week via frozen substitution (41 pair-weeks at cap).
- **HIGH (blocking)**: `forced_flat_fallback` ("first available later H1 bar open the same UTC
  day") is unsatisfiable when the 16:00 NY bar is missing on a Friday: **all 36 flat-bar-missing
  leg events (2.7% of 1,346 legs) were provider-short Fridays with no later bar**. No defined
  exit ⇒ forbidden weekend carry or undefined schedule. Mid-week the same fallback would fill
  AT the 17:00 NY rollover instant, not strictly before.
- MEDIUM: frequency claims optimistic (gate 39% vs 50–70%; 2.0 vs 3.0 RT/wk; 0.29 vs 0.86/pair/wk).
- MEDIUM: Monday day-to-date increments start at the convention-out-of-session 00:00Z stamp
  (weekend-gap contaminated) when all bars are loaded, or Mondays die when filtered.
- PASS-side: USD-neutral algebra verified exact (m·(+1−1)=0); symmetric selection with frozen
  tie-break; drop-one well-defined; cost 6 bps RT vs median 57.8 bps spread (~10% hurdle) —
  structurally plausible; single-timestamp 2-leg fills; 8 GB trivial.

### FXFV2-A5-P2 — USD-neutral 4-leg prior-session outlier reversal — FAIL
Simulated: 1,735 gated days; gate met 70.9%; **1,192 RT (3.52 construction-RT/week; 2.01
leg-visits/pair/week — matches the claimed 2.0)**; folds (legs) 1,488/1,616/1,664; max 3/pair/week
via substitution (904 pair-weeks at cap ≈ 47%).
- **HIGH (blocking)**: same unsatisfiable fallback, 4x amplified: **160 flat-bar-missing leg
  events (2.9% of 4,768 legs), 140 on provider-short Fridays**. One stranded leg breaks the
  2-vs-2 neutral pair-off for the other three; no frozen rule covers divergent exits.
- MEDIUM: the weekly cap binds on ~47% of pair-weeks — realized composition is
  governor-shaped, not signal-shaped, on nearly half the pair-weeks.
- PASS-side: algebra exact; drop-one (k=2 of 6) well-posed; cost 12 bps vs median 114.3 bps
  spread (~10.5% hurdle) — plausible; cells clear.

### FXFV2-A6-P1 — 24-bar TR compression + 48-bar channel breach (any-hour) — FAIL
Simulated both readings of the fail-closed clause:
- Bar-index reading (primary): **4,009 entries; 1.69 RT/pair/week** (claimed 1.8 — accurate);
  folds 1,194/1,356/1,459 (≥100); compression-state evaluations 111,718 (their analytic ~121k);
  caps hold (208 dropped). BUT **max entries/pair/UTC-day = 2 on 79 pair-days**: the first-of-day
  dedup keys on the decision bar's UTC date while the cap counts entries per UTC date — around
  00:00Z the keys diverge (MEDIUM). 147 entries (66 on Sundays, e.g. Sunday 18–19Z, Monday
  00:00Z) sit on convention-out-of-session stamps (MEDIUM).
- Grid-contiguity reading: **357 entries, ALL in fold 3** — the snapshot contains **no 241
  consecutive hourly bars before 2026-01**, so a 240h lookback always spans a weekend. F1/F2
  unpopulated ⇒ per-populated-fold floor (100) and the 2/3-populated-folds gate unevaluable;
  minimum_decisions 20,000 vs 14,518 fails.
- **HIGH (blocking) #1**: no missing-flat fallback — 110 entries (2.7%) have no 16:00 NY bar on
  the entry date; the forced flat is the ONLY exit; `MissingBarNoTradeError` semantics are
  entry-time and cannot close an open position ⇒ forbidden carry or crash.
- **HIGH (blocking) #2**: the missing-bar clause is ambiguous between index and grid-contiguity
  semantics with 11x frequency divergence and opposite feasibility outcomes; spec text
  (index-based windows) and fail-closed sentence (grid-flavored) point different ways.

### FXFV2-A6-P2 — Thin-Asian state + turnover-burst reversion — FAIL
Simulated: **4,557 entries; 1.92 RT/pair/week** (claimed 1.7, +13%); thin-state days 6,229
(≥3,000); folds 1,401/1,541/1,615 (≥100); entries 07–10Z only (≥10h before flat, DST-safe);
caps hold (376 dropped; 860 pair-weeks at cap).
- **HIGH (blocking)**: hold-to-flat at the 16:00 NY bar is the ONLY exit and **157 entries
  (3.4%) have no such bar on the entry date** (provider-short Fridays); no fallback defined.
- MEDIUM: weekly cap binds on ~45% of pair-weeks.
- LOW: Monday Asian windows are complete only via convention-out-of-session Monday 00:00Z bars;
  filtering makes every Monday NO_TRADE. Bar-universe rule unpinned.

## Cross-cutting findings

1. **MEDIUM — Friday flat bar (X1)**: 17% of pair-Fridays lack the 16:00 NY bar; only A4
   defines a sound fallback. This single fact decides the pass/fail split above.
2. **MEDIUM — week-boundary input hygiene (X2)**: load-all vs inside-open-only bar universes
   produce materially different schedules (Monday observables weekend-gap-contaminated vs
   Mondays fail-closed dead; Sunday stamps tradable in any-hour designs). No proposal pins it.
3. **LOW — frequency estimates (X3)**: off in both directions (A4-P1 −45% vs its full-sample
   claim; A4-P2 +68%; A5-P1 gate −11pp; A5-P2/A6 accurate). Caps and cell floors, not estimates,
   decided feasibility.
4. **LOW — determinism pins (X4)**: sigma ddof (A5), median implementation, zoneinfo/tzdata
   version (EU/US desync weeks), residual recentring in z must be pinned.

## Resource + implementation summary

7 pairs × ~42.7k H1 bars; full audit suite (7 simulations) ran in ~3 minutes on one core —
8 GB host suitability is a non-issue for every proposal. Single-leg proposals (A4, A6) have
simple deterministic state machines; A5's 2/4-leg constructions fill at single timestamps
(no divergence while bars exist) but diverge on missing flat bars (see HIGHs). No proposal
requires intrabar, bid/ask, H4 or D1 inputs; all warmups fit the 2020-01-30 start
(largest need: A4-P1, state evaluable from 2020-03-04).
