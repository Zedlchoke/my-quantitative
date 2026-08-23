# H-FUNDCROWD-MR-v1 — Funding-crowding gate on reclaim mean-reversion

**Family:** `funding_oi_crowding` · **State:** `SPEC_DRAFT` · **Owner:** A4 ·
**Candidate version:** 1 · **Split policy:** `S0_chrono3fold`

## Motivation (new mechanism, not a resurrection)

NOTES §13.5/§15.2 established the crowding axis: funding-positive share 67.8–
88.9% across the cohort in a bullish window, LINK an outlier at 5.93 bps/
settlement, and the rule "do not fade blindly when carry is crowded; subtract
carry". The scan matrix shows reclaim-MR shapes are the strongest near-winners
(`NEAR`, `SOL`) but only EXPLORATORY and fold-unstable. This hypothesis changes
the *entry condition* with a pre-registered funding gate as a NEW candidate
version (`H-FUNDCROWD-MR-v1`), locked before any scored run — it is NOT a
post-hoc regime patch on an old candidate (PLAN §2 rules 5–6).

## Economic mechanism

A reclaim long entered while funding percentile is high buys carry from crowded
longs who must pay every 8h and are prone to forced unwinds that extend the
dip. The same reclaim taken when funding is NOT crowded has symmetric payoff to
the reversion without adverse carry/unwind tails. Short side mirrored.

## Rules summary (frozen; exact text in candidate.yaml)

1. Base entry/exit = frozen `strategy_reclaim_mr` logic (unchanged module).
2. NEW gate: funding-rate percentile of last settled rate vs trailing 30d of
   settlements; point-in-time safe (8h settlement lag; only published rates).
3. Skip longs when percentile > `threshold_p`; skip shorts when < 100 − p.
4. Grid: `threshold_p ∈ {70, 75, 80}` × HTF filter fixed ON → **4 combos MAX**
   (p70/p75/p80 × on/off HTF filter fixed ⇒ declared budget 4).

## Invalidating evidence

- Standard G3 failures (exp ≤ 0, PF < 1.10, folds < 2/3, concentration).
- Gate does not improve vs ungated baseline on identical folds → reject both.
- Edge present only where funding data is thin (coverage artifact).

## Data / feasibility

- Funding bundles exist: `funding_data/scan_2026`, 20 symbols × 730 days,
  8h settlements → percentile feature is computable point-in-time. FEASIBLE.
- OI overlay is ~30 days only → **no OI-based signal in this candidate**;
  OI-conditioned variants remain DATA_INCOMPLETE for 2y windows.
- Implementation deferred within iteration 1 (wrapper module + new version;
  frozen `strategy_reclaim_mr.py` untouched). Budget line respected: max 2 new
  strategy implementations per sprint.
