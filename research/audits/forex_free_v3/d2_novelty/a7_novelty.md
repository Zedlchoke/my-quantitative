# A7-N Novelty / Anti-Rescue Audit — FOREX-FREE-V3, Phase V3-D2

Auditor: A7-N (independent; audit artifacts only — no code or proposal repaired).
Audited at 2026-09-04 on branch `orca/forex-free-v3-d2-a7-novelty`,
HEAD `ac83dc80dce6664e92e09f30ec4b4be100cc7608`, porcelain clean at start.
Machine-readable verdicts: `a7_novelty.json` (same directory).

## Verdicts

| hypothesis_id | title (abbrev) | verdict |
|---|---|---|
| FXFV3-A4-P1 | Post-availability drift in the direction of a policy-rate change | **NOVELTY_PASS** |
| FXFV3-A4-P2 | Policy-rate differential divergence trend, weekly clock | **NOVELTY_PASS** |
| FXFV3-A5-P1 | Policy-divergence-gated daily trend | **NOVELTY_PASS** |
| FXFV3-A5-P2 | Daily panel-outlier reversal in high dispersion | **NOVELTY_PASS** |
| FXFV3-A6-P1 | Realized-vol-gated policy-rate-differential carry | **NOVELTY_PASS** |
| FXFV3-A6-P2 | Cross-pair leave-one-out lead-lag, daily | **NOVELTY_PASS** |

Blockers: none. 0 CRITICAL, 0 HIGH, 2 MEDIUM (both non-binding selection-time
remarks), 5 LOW, 4 INFO.

## Feature table (source / clock / conditioning / holding / direction)

All four forbidden rows share one genus: **intraday price session structure**
(session-open move, late-session standardized extension, Tokyo-range
compression→London expansion, London-AM break + retest-hold), conditioned on
session geometry at intraday clocks. Full table in `a7_novelty.json`.

Distinct-feature counts (out of 5) against the four forbidden rows:

| proposal | vs F1 | vs F2 | vs F3 | vs F4 | shared feature |
|---|---|---|---|---|---|
| A4-P1 | 5 | 5 | 5 | 5 | none |
| A4-P2 | 5 | 5 | 5 | 5 | none |
| A5-P1 | 4 | 5 | 5 | 5 | "continuation" class only (21-day own trend vs session-open move) |
| A5-P2 | 5 | 4 | 5 | 5 | "fade" class only (5-day panel z vs intraday session extension) |
| A6-P1 | 5 | 5 | 5 | 5 | none |
| A6-P2 | 4 | 5 | 4 | 4 | "continuation" class only (LOO cross-pair daily mean vs session moves) |

Minimum across all 24 pairs: 4/5 distinct; the single shared feature is always
only the abstract direction class, never the operative observable. Rename /
invert / re-clock test: no forbidden row's operative observable (intraday
session geometry) appears in any proposal; the only sign flip in the set is
A4-P1's internal preregistered control, which adds falsification and cannot
rescue. Re-clocking to the frozen daily-or-slower rule with a different
observable is not a re-clock of an intraday signal.

## Checks per proposal (all six PASS on all five)

1. **Feature comparison vs every forbidden row** — PASS (table above).
2. **Rescue-clause scan** — PASS: all clocks daily-or-slower per the frozen
   invariant; costs at the frozen 1.5 bps × {1.0,1.5,2.0} authority with
   F1-fixed booked stress and separate delay stress; full 7-pair universe
   everywhere (no subsets); no session relabeling; no threshold relaxation of
   any forbidden-row parameter; no result-aware reuse (fresh blind packets).
3. **Control structure** — every control is a preregistered single-ingredient
   ablation on an identical schedule: sign-flipped conditioning (A4-P1),
   +182d availability shift (A4-P2), macro-direction-only (A5-P1), own
   time-series z (A5-P2), sham-pair derangement with disclosed leakage and a
   0.5x rule (A6-P1), own lag-1 self-signal with a 0.5x rule (A6-P2). None is
   a strawman; each has a distinct preregistered non-reproduction rule, and
   the incremental benchmarks separately isolate the conditioning claim.
4. **Outcome-blind attestation** — present and specific in all six; A5/A6 add
   explicit `written_before_scoring_utc` stamps (A4 lacks the field — LOW,
   cosmetic). A6's broader disclosed read-scope (V2 predecessor packets for
   novelty differentiation) is mechanism knowledge, permitted, no outcomes.
5. **Macro-flag consistency** — consistent in all six; 4 of 6 macro-conditioned
   (quorum ≥ 3 met).

## Cross-proposal duplicates

None. No two proposals are the same mechanism in different clothes. Two genus
overlaps recorded as **MEDIUM, non-binding** remarks to A1:

- {A4-P2, A5-P1, A6-P1} share the BIS WS_CBPOL differential ingredient with
  three different mechanisms (drift direction / drift gate / level direction).
  If more than one is selected, record a V2-style merge caveat; note the shared
  single-series dependency at the P3/Q live-coverage gate.
- {A5-P2, A6-P2} are both daily cross-sectional price books with opposite
  exploitation signs; if both selected they partially offset and share the
  16:00-NY Friday flat-bar dependency — A9-F should verify Friday handling
  (the defect that killed four V2 proposals; structurally addressed in all six
  V3 packets by next-existing-bar fail-closed semantics — INFO).

Selection is A1's under the frozen rubric; these remarks do not bind it.

## Scope note

This audit ran the novelty/anti-rescue checks only (PLAN §8, A7-N). Feasibility,
PIT coverage, turnover arithmetic and break-even headroom belong to A9-F and
were not run here. No PnL exists or was computed.
