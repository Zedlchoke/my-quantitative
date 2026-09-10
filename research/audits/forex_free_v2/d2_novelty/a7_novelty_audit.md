# A7-N Novelty Audit — FOREX-FREE-V2, phase F2-D2

- Auditor: A7-N (independent novelty auditor; **audit-only, no repairs, no PnL computed**)
- Measured (UTC): 2026-09-04T03:17:36Z
- Base SHA: `24c7230` (full: `24c72306cb3724328061e398372c0cf88898b600`)
- Branch: `orca/forex-free-v2-a7-novelty`
- Structured twin: `research/audits/forex_free_v2/d2_novelty/a7_novelty_audit.json`
- Auditor access: unlike proposal agents, A7-N read the full V1 evidence — `forbidden_family_inventory.json`, `PLAN_forex_v2.md` §1, V1 control plane (`state.json`, `scored_ledger_published.jsonl`, `selection_freeze.json`, `w1_freeze.json`), `family1.py`, `family2.py`, all six V1 proposals, and the V1 novelty audit (source of the near-duplicate ruling).

## Verdicts

| Proposal | Mechanism (one line) | Verdict |
|---|---|---|
| FXFV2-A4-P1 | Tokyo-range compression → first London-morning breach of the overnight extremes, continuation, flat 16:00 NY | **NOVELTY_PASS** |
| FXFV2-A4-P2 | London-AM range break confirmed by retest-hold, London-afternoon continuation, flat 16:00 NY | **NOVELTY_PASS** |
| FXFV2-A5-P1 | Same-day extreme-vs-extreme demeaned-residual dislocation convergence (USD-neutral, 2 legs, 12:00Z decision) | **NOVELTY_PASS** |
| FXFV2-A5-P2 | Prior-session outlier basket reversal (USD-neutral, bottom-2 vs top-2, 07:00Z decision) | **NOVELTY_PASS** |
| FXFV2-A6-P1 | 24-bar TR compression state + first-of-day 48-bar channel close-breach continuation, any hour | **NOVELTY_PASS** |
| FXFV2-A6-P2 | Thin-Asian state + turnover-burst detector → reversion opposite the Asian drift, 06–10 UTC | **NOVELTY_PASS** |

**0 NOVELTY_FAIL, 0 HIGH findings, 8 MEDIUM, 8 LOW, 0 overlap FAILs, 0 fabricated citations, 0 control failures.**

## Forbidden-set check (what A7-N verified against)

- **Family1 (FXFV1-A3-P1)**: unconditional sign of 3-bar post-open momentum at 08:00 London (NY-open neighbour), entry fill 12:00 London, flat 16:00 NY. V1: expectancy −2.3527, PF 0.8489, 11,459 trades.
- **Family2 (FXFV1-A3-P2)**: fade of the vol-standardized 4-bar NY extension (|z| ≥ 1.0), entered 13:00 NY; Tokyo-open neighbour was the session-relocated arm (also scored and rejected: −2.7196, PF 0.8874, 142 trades). Anchor: −2.8957, PF 0.6376, 1,020 trades.
- **Known near-duplicate**: V1 FXFV1-A4-P2 — London-morning momentum carry into the NY overlap (V1 novelty audit HIGH cell vs A3-P1; one-bar window difference, same 12:00-London fill).
- Ledger numbers in `scored_ledger_published.jsonl` match the inventory exactly.

## Per-proposal reasoning (condensed; full detail in the JSON)

### FXFV2-A4-P1 — PASS
Not a family1 variant: the signal object changed (prior-session extreme breach vs open-relative momentum), cadence is conditional (~25–35% of days), and an invalidation exit exists. But it **is** a London-morning continuation trade in the family1 neighborhood — on compressed days the breach side often equals the open-momentum sign.
- **MEDIUM (A4P1-1)**: family1 neighborhood; differentiation rests on the compression state + level-breach trigger, with the midpoint placebo structurally able to catch (and self-reject) a generic compression+momentum edge.
- **MEDIUM (A4P1-2)**: **undisclosed lineage to V1's unselected, never-scored FXFV1-A4-P1** (Tokyo compression → London expansion; 6-bar range, close-beyond trigger, 15:00 NY flat). V2 is materially re-specified (quantified 0.75×median gate, intrabar-touch trigger, 9-bar range, invalidation exit, midpoint control). Eligible — V1 A4-P1 has no observed outcome, and this audit is the independent novelty decision over a fresh blind packet — but the lineage must travel with the proposal into selection. Not a fault of A4 (firewall forbade reading V1 proposals).
- **MEDIUM (A4P1-3)**: no frozen USD-drift falsification diagnostic (descriptive only); the direction_check counts quoted long/short, not USD-leg. See USD section.
- LOW: cap-truncated control day-mix (disclosed); Osler 2000 claim hedged appropriately ("consistent with" — verified against newyorkfed.org EPR 6(2)).

### FXFV2-A4-P2 — PASS
Not the V1 near-duplicate: requires London-AM range break **plus** a retest-hold reaction state, entering later (13:00–19:00 London) on a conditional subset; the duplicate was the unconditional sign of the morning move at a fixed 12:00-London fill. Not family1: afternoon resolution, conditional, level-break + state machine. Not family2: no fade anywhere.
- **MEDIUM (A4P2-1)**: on trend days it holds the same direction as family1/the duplicate, hours later — the retest-hold state and the complement-state control are the operative differentiators.
- **MEDIUM (A4P2-2)**: same USD-diagnostic gap as A4-P1.
- LOW: control invalidation asymmetry (opposite-extreme stop) — defensible fairness choice, disclosed.
- Control adequacy: ADEQUATE — the void-day complement control removes exactly the retest-hold ingredient; reproduction would self-reject. Sources verified (Osler 2003 JF 58(5) 1791–1819; Brock–Lakonishok–LeBaron 1992 JF 47(5) 1731–1764).

### FXFV2-A5-P1 — PASS
No session clock, no directional single-pair bet; algebra of USD neutrality checked by A7-N and exact to first order (equal +1/−1 units ⇒ m cancels). Hash-placebo control is a clean de-link and self-voids on reproduction. Lustig–Roussanov–Verdelhan 2011 JF 66(4) verified.
- LOW: "first bar of trading day" boundary not explicitly frozen (P2 freezes NY-rollover; P1 does not).
- LOW: gate-frequency estimate 0.5–0.7 for z-range ≥ 3.0 is generous (~0.4 for 7 iid normals); schedule estimate only.

### FXFV2-A5-P2 — PASS
Cross-sectional inter-day reversal, not a family2-style single-pair fade; 2v2 basket algebra cancels m exactly; preregistered usd_drift failure mode. Lehmann 1990 QJE 105(1) and Nagel 2012 RFS 25(7) verified; equity-to-FX port properly labeled.
- **MEDIUM (A5P2-1)**: the stale-ranking (T-2) control is a **graded** de-link — cross-sectional demeaned-return ranks are autocorrelated day-over-day, so T-2 correlates with T-1; partial control reproduction has no frozen interpretation (full reproduction voids, which is safe/conservative). No independent hash placebo in this proposal.

### FXFV2-A6-P1 — PASS
No session clock anywhere in state/trigger/direction (verified in spec). Unconditional 48-bar channel breakout is generic Donchian, not a forbidden family — and it **is the control arm**, with a frozen self-reject rule (control expectancy ≥ 0.5× anchor or PF ≥ 1.10). D1–D3 USD-leg diagnostics frozen and meaningful. Engle 1982 verified; Osler 2003 verified with a page-range typo.
- **MEDIUM (A6P1-1)**: overlap warning with A4-P1 — same compression→breach-continuation genus, overlapping trigger hours, correlated direction on compressed trend days. Schedules not identical ⇒ no FAIL. **Merge candidate (MUST)**.
- LOW: Osler page typo; arbitrary-but-frozen control thresholds.

### FXFV2-A6-P2 — PASS
Direction opposes the measured Asian drift; trigger is a data-detected TR burst, not a clock; the London-handoff bracketing is fully disclosed. Versus family2: clock 06–10 UTC vs late-NY, raw ungated drift vs z-standardized extension, new thin-state gate — not a nearby variant.
- **MEDIUM (A6P2-1)**: adjacency to rejected family2's **Tokyo-open neighbour cell** (both fade an Asian-session displacement to the same 16:00 NY flat). The structural safeguard is that the control arm **is** the unconditional Asian-drift fade (the forbidden-genus rival); control reproduction self-rejects. The scorer must treat the control verdict as load-bearing for this proposal's eligibility.
- **LOW (A6P2-2)**: overlap warning with A4-P1 — shared thin-Asian state genus and overlapping 07–11Z entry windows; direction agreement non-systematic (anti-Asian-drift vs London-breach-side). Not a mirror (a mirror of A4-P1 would fade the London breach).
- Sources verified by web check: Andersen–Bollerslev 1998 JF 53(1) 219–265; Bollerslev–Domowitz 1993 JF 48(4) 1421–1443 (exact).

## Overlap adjudication (rule: FAIL only if same trade schedule in direction AND session)

No pair FAILS. Key cells:

| Pair | Rating | Note |
|---|---|---|
| A4-P1 ↔ A6-P1 | WARNING-STRONG | Same genus; same-bar co-fire possible on compressed days; **merge candidate (MUST)** |
| A4-P1 ↔ A4-P2 | WARNING | Same class, same London day, correlated direction on trend days (double exposure); **merge candidate (SHOULD)** |
| A4-P2 ↔ A6-P1 | WARNING | Same London-afternoon continuation direction possible; different state/trigger |
| A5-P1 ↔ A5-P2 | WARNING | State-variable reuse only; complementary horizons (13:00Z convergence vs 08:00Z reversal) |
| A4-P1 ↔ A6-P2 | WARNING | Shared thin-Asian genus, overlapping entry hours, non-systematic direction agreement |
| A6-P1 ↔ A6-P2 | WARNING | Same-lane state concept; opposite direction logic (continuation vs reversion) |
| A5-\* ↔ A4/A6-\* | LOW | Market-neutral RV vs directional single-pair books |

## Merge candidates and recommended family groupings

1. **MUST — {FXFV2-A4-P1, FXFV2-A6-P1}**: if both are selected, treat as ONE family (state-conditional breach continuation) for family counting/selection budget — pick one representative or run a trade-overlap audit (same pair, same day, same direction) and budget the union as one family.
2. **SHOULD — {FXFV2-A4-P1, FXFV2-A4-P2}**: if both are selected, treat as one super-family ("conditional London-day range expansion") or demonstrate schedule disjointness and cap joint exposure.
3. Note: A4-P1 appears in both groupings. If A4-P1, A4-P2 and A6-P1 all survived Stage-A, the honest reading is **one super-family of state-conditional London-day continuation instantiated three ways**; they must not consume three independent family slots.
4. Independent: FXFV2-A5-P1, FXFV2-A5-P2, FXFV2-A6-P2.

## USD / common-factor explainability

- **A5-P1 / A5-P2**: neutrality algebra verified exact to first order (equal units, Σx=0 ⇒ the equal-weighted USD index cancels); honesty notes and preregistered USD-drift failure modes present. ADEQUATE.
- **A6-P1 / A6-P2**: null construction with frozen D1 (USD-leg imbalance), D2 (cross-sectional coherence), D3 (conditional expectancy split) diagnostics — meaningful and preregistered. ADEQUATE.
- **A4-P1 / A4-P2**: GAP (**MEDIUM A4P1-3 / A4P2-2**). Null construction is permitted (PLAN §12 gates neutrality only where claimed), but the only USD diagnostic is explicitly non-gated and descriptive, and the concentration plan counts quoted long/short, not USD-leg sign — a coherent broad-USD-drift explanation of the anchor would be caught by **no** frozen gate. PLAN §"novelty/feasibility" assigns the by-construction check to A7; A7 records the exposure and **recommends** (audit recommendation, not a repair) that the Stage-A scorer apply the A6-style D1–D3 diagnostics to both A4 anchors before any survivor is locked.

## Outcome-blind process verification

- Full read + targeted grep sweep of all six proposals for V1 outcome numbers (−2.35/−2.89/11459/11512/1020/0.849/0.638) and ledger digests: **zero hits**; the only matches are forward-looking falsification language. No proposal requires knowledge of results; all failure interpretations are frozen ex ante.
- **PROC-1 (LOW)**: A4 ran one post-commit `git log -1` on its own lane tip, disclosed and recorded in the V2 event log. A7-N independently confirms non-contamination: (a) executed **after** the lane commit froze the proposals — no causal path into proposal text; (b) the only visible content was A4's own commit message (`5900b03`), which A7-N read — pure V2-cycle text, no V1 outcomes; (c) the lane report's "git log never run" statement is accurate for the pre-commit design phase it attests. Letter-level deviation, zero outcome content.

## Attestation

audit-only, no repairs, no PnL computed. A7-N loaded no market data and computed no schedule, backtest, or PnL; every judgment above is from committed proposal/control/evidence files plus the auditor's own literature verification (Bollerslev–Domowitz 1993 and Osler 2000 web-verified; all other citations checked against auditor knowledge of the primary literature).
