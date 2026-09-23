# BLIND REVIEW RUBRIC — JRV2-DECISION-AUDIT-V1 (LOCKED 2026-09-23)

Locked and committed BEFORE any case sheet was rendered or read. The
reviewer sees ONLY the named semantic state (9 bins, 14 numerics,
prior_structure, prior_direction, cell, regime clock) — never a JEV label,
a confidence, a margin, a timestamp, or any outcome. Return one verdict per
case plus a confidence and a one-line reason.

## Verdict set

`UPTREND | DOWNTREND | ACCUMULATION | DISTRIBUTION | UNDETERMINED`

`UNDETERMINED` is a first-class answer: use it whenever evidence conflicts
or is too weak. Never force a phase.

## Phase definitions (standard technical / Wyckoff reading)

- **UPTREND — sustained advance.** Medium/long returns positive and
  material (r24/r72 clearly > 0), slow and/or fast EMA slope up, price at
  or above the EMA (dist_ema > 0, often ≥ +0.25), drawdown near highs
  (dd_168 > −0.05±). ADX medium/high supports but does not decide.
- **DOWNTREND — sustained decline.** Mirror: medium/long returns clearly
  negative, slopes down, price at/below the EMA (dist_ema < 0), drawdown
  mild-to-deep.
- **ACCUMULATION — sideways base forming after a decline.** Returns and
  slopes near flat (|r24| small, slopes weak/flat, dist_ema near the EMA),
  price sits in the middle of its recent range (range_pos near 0), AND the
  base sits below prior highs (dd_168 negative — the down-lineage
  context). Prior context DOWN/RANGE-after-down supports it.
- **DISTRIBUTION — sideways top forming after an advance.** Same
  sideways profile but positioned AT or NEAR prior highs (dd_168 >
  −0.05±, range_pos toward the top), consistent with a prior advance.
- **UNDETERMINED —** strong opposing signals (e.g., r72 up but both
  slopes down; extreme volatility chopping an otherwise clear pattern),
  or every field near neutral.

## Reading anchors (locked, from the frozen bin thresholds)

- Returns (regime-bar units): |r24| or |r72| within roughly ±1% ≈ flat;
  |r72| ≥ ±4–5% is a material move (H1/H4: returns compound per bar, so
  lean on the bins `fast_trend`/`slow_trend` and drawdown/extension first).
- `trend_strength` ADX: low < 20 (no trend regime), medium 20–30, high > 30.
- `dist_to_ema`: |value| ≤ 0.25 = at the EMA; beyond ±1.5 = extended.
- `volatility_regime` extreme (> .90 pctile) raises UNDETERMINED pressure.
- `volume_state`/`close_location` are tie-breakers only.
- Prior lineage matters for ACCUMULATION vs DISTRIBUTION: a sideways state
  deep below highs reads ACCUMULATION; at highs reads DISTRIBUTION; with
  `prior_direction = none/NEUTRAL` and no drawdown/extension signal, the
  lineage is unknowable → lean UNDETERMINED.

## Confidence

`low | medium | high` — how clearly the sheet alone identifies the phase.

## What this is NOT

This is a blind plausibility review, not accuracy: no pre-registered
independent ground truth exists for these states. The output measures
blind–JEV agreement and characterizes where JEV's answers are or are not
consistent with readable market structure.
