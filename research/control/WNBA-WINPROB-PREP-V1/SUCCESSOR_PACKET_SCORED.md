# SUCCESSOR PACKET — WNBA-WINPROB-SCORED-V1 (PROPOSAL, NOT A REGISTRATION)

- Proposed cycle_id: **WNBA-WINPROB-SCORED-V1** (successor of WNBA-WINPROB-PREP-V1)
- Status: DRAFT PROPOSAL ONLY. Nothing here registers anything, consumes any GO, or
  authorizes any scored computation. Registration requires the owner instruction + the
  gates in §8. Written by the controller 2026-10-05 from verified lane bytes (post-fix
  re-verification VERIFICATION_PASS at fcae4931; W-H2 roster PIT = PIT_PASS_BY_CONSTRUCTION
  independently confirmed).
- INDEPENDENCE LAW: no NBA data, parameter, or verdict is WNBA evidence. NBA machinery
  (fold/bootstrap/gate SHAPES) is inherited as machinery only.

## 1. Windows (frozen proposal)

- ERA LAW: 1997–2001 stats-side schedules = rating-stream WARM-UP ONLY (never
  train/score/feature rows; warm-up-vs-cold-start rerun is a reported diagnostic, never
  an arm).
- TRAIN: 2002 → (first OOS season − 1) — placeholder 2002–2018; train-internal selection
  via 4 expanding-origin 2-season validation blocks (~440 games each), grids
  pre-registered (see §3).
- WALK-FORWARD OOS: final 7 complete seasons at the successor's data freeze — placeholder
  2019–2025 if 2026 incomplete at freeze, else 2020–2026; expanding folds; frozen
  constants; B0 refit per fold.
- PROSPECTIVE ONLY: future seasons via append-only ledger rows (`written_at_utc`
  STRICTLY < tip UTC); ≥2 accrued seasons before any prospective report; 2026
  if-necessary TBD rows are placeholders, never games.

## 2. Baseline law

- B0 constant floor + **fresh WNBA B1 own-Elo** with train-only selected constants from
  the pre-registered grid K∈{8,16,32} × HCA∈{0,50,100} × γ∈{0.65,0.75,0.85} (1997–2001
  warm-up feeding the streams). HCA prior expectation: positive but UNMEASURED — the grid
  must include 0 and bracket [0,150]; NBA's K=32/HCA=100 is citable context, never a
  WNBA value.

## 3. Arm table (ceiling 9; 5 allocated, 4 released to V1)

| # | Arm | Status | Falsifier (frozen) |
|---|-----|--------|--------------------|
| 1 | B0 constant floor | committed | reference |
| 2 | B1 fresh WNBA own-Elo (grid above; degenerate-grid K→0 kill) | committed | REJECT-vs-B0 iff pooled 95% paired date-cluster-bootstrap CI of ΔLL includes 0 OR ≥ half of ~24 season folds non-negative |
| 3 | W-H2 continuity-modulated carryover (ρ; global-ρ0 null parent) | candidate — **PIT cleared** (see §4) | REJECT iff pooled 95% CI of ΔLL vs the global-ρ0 parent includes 0 OR ≥ half folds non-negative; near-constant cross-team continuity ⇒ automatic drop |
| 4 | W-H3 SOS decomposition (β; β=0 null parent) | candidate | same CI gate vs W-H1/B1; SOS term = 0 at each team's game 1; shuffled-SOS twin |
| 5 | reserve slot | fully pre-specifiable at freeze or RELEASED | — |
| 6–9 | released | — | — |

- Diagnostic class (outside budget): time-shuffled twins per arm; warm-up-vs-cold-start
  rerun; twin-beats-parent ⇒ machinery audit + arm UN-SCORED.
- DROPPED per owner rule (NOT_RUN_PIT / mechanism-first rejects): availability/injury
  (no feed+timestamps), b2b/travel fatigue arms, expansion-init prior, overseas
  availability, matchup familiarity, MOV-Elo, additive logistic-over-Elo.

## 4. W-H2 PIT law (the load-bearing new freeze item)

- Verdict: **PIT_PASS_BY_CONSTRUCTION** (game-linked prior-season derivation), measured:
  roster coverage 5,983/5,988 universe games (5 missing listed; none a team's game 1);
  0 duplicate (game,team,athlete); all roster game_ids schedule-resolvable; minutes-side
  computable-continuity 0% (2003) / 38.5% (2004) / 92.3% (2005) / **100% T≥2006**;
  retro-addition scan 0 from 2006; 2025 starter cross-check 622/622 exact.
- FROZEN as-of law: continuity inputs = strictly-prior-SEASON game-linked roster/box
  facts only; season-T rows never used for T's own predictions; game-day
  active/DNP/starter/reason are post-game facts — legal for T−1 derivation, FORBIDDEN as
  same-season pre-game features; eligibility windows: **minutes-weighted T≥2006,
  roster-share T≥2003** (variant choice train-internal at freeze); 5 truncated game-1
  rosters + 5 box-missing games 2010–2016 carried as structural missingness.
- 4 MINOR text-vs-machine corrections (D-6..D-9 of DELTA_REVERIFY_R2) to be applied to
  the audit text AT FREEZE (machine outputs measurements_r2.json are authoritative):
  game-1 roster min is 8–9 rows for 5/318 team-seasons; box completeness exceptions
  2010/2012/2016; 2025 roster file = 312 keys incl. ASG; covered = 5,983 (5,963 =
  exactly-10-starter count).

## 5. Data freeze (hashes to pin at registration)

| Artifact | sha256 |
|---|---|
| wnba-v1 corpus manifest (winprob-ng-prep lane B DATA_MANIFEST.md) | fc0d6456ae1aee43455578a376e745f162656d157a7ecaf186fedd773704e2b9 |
| wnba-v1 corpus ATTRIBUTION.md | 1068e5c7aae614347550266da94d067f38c7c2cc9b569e685cfed3aced301f5a |
| team_key_table.csv (20-key lineage, post-r1) | 2020104263a25f6439ee995490683e6a60e0fda7df59ee709e6a94b3758f3cd9 |
| roster_audit download manifest (50 files, 86,572,091 B) | 4632fb22c4724ad385ed8a10605dfeeb3f7f445a3a8710a60b71e649f59556a7 |
| GAME_UNIVERSE_SPEC_WNBA_1997PLUS.md (post-r1) | 989230ef2ca217ceffb52f0faf1acbd5d3cda34cf861634ec4327374df1a2556 |
| ROSTER_PIT_AUDIT_WNBA.md | a68122da820cea475c4c4cec83e0c5eade1e7172b3b1a86ea9f36d262e83861a |
| MECHANISMS_WNBA.md | aad08f93cb31465ed3e4b377fb2b32bb50b3a46fe249776116f167cad425dcfb |
| PROTOCOL_DRAFT_WNBA.md (post-counts-r1) | e030af105f33098c74b9c4639dd909c78aac6715bde065b03f188c4069bbcb05 |

- Data laws frozen with them: filter law (status 'post' only; drop Forfeit/Postponed;
  21 alias rows / 13 tokens; 7 TBD; NEVER filter on score presence — 0–0 prefill);
  20-key lineage (LVA := UTA→SAN→LVA; DAL := DET→TUL→DAL; LAS continuous; join on
  display_name/crosswalk, never raw ESPN abbreviations — DET rows mislabeled TUL
  2002–2009); tip_utc := parse(ESPN schedule date, UTC); box −0400 suffix is cosmetic;
  stats game_date == ET date; 2020 Wubble 147 games REAL; 6 Cup finals flagged; 16
  neutral rows → HCA=0 default with separate report.

## 6. Metrics + uncertainty (inherited machinery)

- Log loss primary; Brier + reliability + calibration slope [0.85, 1.15] secondary;
  paired date-cluster bootstrap; T1/T2/T3 gate shapes inherited; capacity honesty:
  ~230 RS games/season; fold/block/pooled minimums per PROTOCOL_DRAFT_WNBA.md; effects
  < ~0.003 ΔLL expected INCONCLUSIVE (state, don't stretch).

## 7. Trial budget (proposed)

- ≤9 scored arms as §3 (5 allocated); observed denominator = one computation per arm on
  the frozen OOS seasons; diagnostics +0; repro twin +0-trial class; exact-arm dry-run
  before any scored cell.

## 8. Gates still missing before ANY scored run (the registration checklist)

1. Owner instruction naming this successor (this packet is only a proposal).
2. Fresh `researchctl cycle register` (budget from §7; GO phrase registered-not-consumed).
3. Data/code/protocol freeze at the §5 hashes + constants digest; apply the §4 MINOR
   text corrections; fold renames (no S1-named folds).
4. Implementation + synthetic fixtures (no-lookahead mutation incl. the strictly-prior-
   season roster gate, DST/UTC boundaries, filter-law assertions) all PASS.
5. Exact-arm dry-run PASS (non-vacuous; zero denominator delta).
6. Independent A7 prelaunch AUTHORIZED, 0 unresolved HIGH/CRITICAL.
7. Owner typed GO, fresh, verbatim, at THIS cycle's own gate (two-key; P-8).
8. Then scored execution under the heavy lock; reproduction twin; A7 terminal; two-half
   close.
