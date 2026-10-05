# PREP_SUMMARY — WINPROB-PLAYERFEAT-PREP-V1 (2026-10-05)

Verdict: **PREP_COMPLETE_PENDING_OWNER_DECISIONS** — all four lanes landed, independent
verifier D VERIFIED_WITH_MINOR (0 BLOCKER / 0 MAJOR / 1 MINOR doc-only / 2 INFO); 0 scored
by law (budget 0/0, no GO phrase registered); $0 spent (public URLs only).

## What is now on disk (frozen, sha-pinned)

- **NBA player-feature table** (lane A): 28,374 rows = 2 × 14,187 played games 2016–2026, one
  row per (game_id, team side); groups A (top5_share/load k=5 — raw minutes-mass measured
  degenerate ≈240+25·OT and substituted per the measured-degeneracy law), B (top-3 form vs
  own baseline), C (absence indicators with same-team-10-games trade guard); strict as-of
  `asof_v1_strict_tip_utc`; 1,688 neutral rows flagged; 19 exhibition games flagged; zero
  outcome columns; 42/42 selftest; downloads 8 new seasons provenance-pinned (join 1.0000 in
  8/11 seasons, 0.9992 in 2017–19 with 3 named box-less FINAL games).
- **WNBA player-feature table** (lane B): 11,976 rows = 2 × 5,988 universe games 2002–2026;
  groups A continuity (v2 as-of law, 2014–2026), B load k∈{3,5}, C form+absence; 20-key
  lineage joins; deterministic rebuild sha-identical; 46/46 selftest; corpus spot re-hash 8/8.
- **NFL crosswalk UNBLOCKED** (lane C + D adjudication): players.parquet sha-pinned
  (485b1980…, build 2026-10-04); GSIS join to weekly stats 100.00% (2024/2025/2026); PFR
  join to snap_counts 99.73%/99.82%; round-trip stats↔snaps via crosswalk 97.55% (2026);
  32/32 teams; ACT∧2026 roster 1,731. **Predecessor HOLD: LIFTED — confirmed by independent
  verifier D** (owner's condition "chỉ gỡ HOLD nếu verifier xác nhận" met). Residual
  blockers carried by name: snap_counts ≤1-week in-season lag; release-cadence (not
  row-level) availability — frozen sha256s are the anchor; **target-game injury/active/DNP/
  starter status remains NOT_RUN_PIT** (no pre-game publish timestamps; law unchanged).

## Falsifiable hypotheses pre-registered (design-only; never run this cycle)

- NBA (vs frozen B1* K=32 HCA=100, evaluation window NBA 2016+ train-internal): H-PF-A
  rotation concentration (top5_share deviation, prior-5) carries calibration information
  beyond Elo; H-PF-B top-3 player form-vs-self improves mid-season calibration; H-PF-C
  lagged observed absence (prior-games DNP) predicts weakened rotation beyond Elo.
  Time-shuffled negative controls per group; T1-ancestry veto enforced (no rest-days or
  win/loss-form re-entry). Falsifier: shuffled-twin parity ⇒ group discarded.
- WNBA (vs frozen WNBA baseline law, W-H1/W-H2 machinery reference): H-W-A continuity-
  modulated season-start carryover beats scalar-ρ0 parent on season-boundary slices; H-W-B
  rotation concentration/load prior-k; H-W-C top-player form/absence. Same shuffle
  falsifiers; era guards 2004+/2013+.
- NFL: no hypotheses run (crosswalk-verification round only); feature proposals for a
  successor inherit the predecessor lane-C groups (QB form/availability, skill-player usage
  mass, absence proxy) now unblocked at the join layer.

## Boundary compliance

0 scored computations (verifier grep clean); no win-prob metrics on real outcomes; no S1;
no purchases/accounts/keys; no push/merge (branches local); lanes never touched frozen
artifacts; language law held.

## Chain

bootstrap 00323ba → A_NBA_FEAT d5c40e8 → B_WNBA_FEAT 261c645 → C_NFL_CROSSWALK 6e014f4 →
wave-1 event 8ad8785 → D_VERIFY (+CONFIRM LIFT) → head a4838291 → PREP_SUMMARY (this commit).

## Next authorized path (owner decisions required)

1. Scored player-feature successors (NBA / WNBA / NFL): fresh registration per league,
   freeze, A7 prelaunch, owner typed GO at each cycle's own gate. NBA/WNBA successors may
   reuse these frozen tables (extend-only); NFL feature-prep successor may now be proposed
   with the crosswalk unblocked (target-game status stays NOT_RUN_PIT).
2. Nothing in this cycle authorizes scoring, GO consumption, publication, or commercial use
   (underlying ESPN/league data rights remain unverified — internal research only).
