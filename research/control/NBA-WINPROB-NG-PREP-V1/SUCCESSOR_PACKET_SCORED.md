# SUCCESSOR PACKET — NBA-WINPROB-NG-SCORED-V1 (PROPOSAL, NOT A REGISTRATION)

- Proposed cycle_id: **NBA-WINPROB-NG-SCORED-V1** (successor of NBA-WINPROB-NG-PREP-V1)
- Status: DRAFT PROPOSAL ONLY. Nothing here registers anything, consumes any GO, or
  authorizes any scored computation. Registration requires the owner instruction + the
  gates in §8. Written by the controller 2026-10-05 from verified lane bytes (post-fix
  re-verification VERIFICATION_PASS at 4a7ea926).

## 1. Windows (frozen proposal)

- WARM-UP (streams run, never scored): NBA seasons 2016, 2017.
- TRAIN-INTERNAL SELECTION (all free parameters β/λ/θ/w + grids): seasons 2018–2021,
  4 rolling-origin folds; frozen split cutoff **2021-08-01T00:00:00Z** (off-season gap).
- WALK-FORWARD OOS (frozen list, expanding folds): **[2022, 2023, 2024, 2025, 2026]**;
  fold-majority bar = ≥3/5. Single-batch scoring law (no interim OOS peeks).
- PROSPECTIVE ONLY: 2026–27+ games unplayed at the successor freeze; append-only ledger
  rows with `written_at_utc` STRICTLY < tip UTC; no backfill; never pooled into the
  historical OOS headline.
- SPENT WINDOW LAW: 2009–2015 citable, never scoreable; no re-grid of K/HCA/rest/form
  there in any arm or diagnostic.

## 2. Baseline law

- B1* = B1-d own-Elo **K=32, HCA=100** (γ=0.75), LL 0.5987 vs B0 0.6769 (n=8,369, spent
  window) — carried VERBATIM from NBA-WINPROB-SCORED-V1; mandatory arm; never re-tuned.
- Diagnostic ablation arm (outside candidate budget): B1 with HCA=0.

## 3. Arm table (≤9 candidate slots; expected ≤6 used)

| # | Arm | Status | Falsifier (frozen) |
|---|-----|--------|--------------------|
| 1 | B0 constant floor | committed | reference |
| 2 | B1* K=32/HCA=100 verbatim | committed | reference-beater required |
| 3 | NB-H1 SOS-adjusted Elo (β train-only; β=0 null parent) | candidate | REJECT iff pooled 95% paired date-cluster-bootstrap CI of ΔLL vs B1* includes 0 OR ≥ half folds non-negative; shuffled-SOS twin must show nothing |
| 4 | NB-H2 home/away split ratings (λ; λ=0 null parent) | candidate | same CI gate; split-collapse (mean ‖R_h−R_a‖ < 10 Elo) = capacity kill; venue-permutation twin must destroy the gain |
| 5 | NB-H3 fatigue×venue joint block (θ≡0 null parent) | candidate | CI gate on the JOINT block (one ΔLL, never per-term); shuffled travel/rest twins mandatory |
| 6 | NB-H4 pace/efficiency train-only rating-init (w=0 null parent) | candidate-gated | CI gate; gated on data rights at freeze (release-only if gate fails); shuffled-prior twin |
| 7 | availability/injury (H-C3) | **NOT_RUN_PIT** — slot stays empty | only if a rights+timestamp-proven archive appears BEFORE freeze (5-step audit spec in MECHANISMS_NBA_NG.md) |
| 8–9 | reserve | RELEASED (pre-look rule; never reallocated) | — |

- Diagnostic class (outside budget, never candidate wins): shuffled twins per arm;
  B1-HCA0 ablation.
- Kill tests pre-OOS: every arm must survive its train-internal split first; a control
  beating its parent ⇒ machinery audit + arm UN-SCORED.

## 4. Data freeze (hashes to pin at registration)

| Artifact | sha256 |
|---|---|
| hoopR corpus provenance TSV (`~/.my-quantitative-data/nba-hoopr-v1/raw/_download_provenance.tsv`) | 6bf3e729f911ff4215ccd40be199eeb8e07343fdd4fc5b68fc95d8ef2135ec66 |
| pbp corpus 2016–2025 composite (10 parquets, 248,642,536 B; per-file sha256 in `lanes/A_DATA/DOWNLOAD_MANIFEST.md`) | manifest sha256 21fda405af4d819f (full: 21fda405af4d819f…a1d99 — pin the file itself at freeze) |
| GAME_UNIVERSE_SPEC_NBA_2016PLUS.md (post-r1) | b9ee812c7889262cd19e070a1a797a80126c060dd20d74574e426ab53d652194 |
| PIT_AUDIT_NBA.md (post-r1) | 33d18311b8bd083a2c71c7236a871a4712e8c5d133f964baddde6880639e970d |
| MECHANISMS_NBA_NG.md | 9acee28dd0456dc7257b003c05991c4d83c9c84685a402b524ba53462f29bec2 |
| PROTOCOL_DRAFT_NBA_NG.md | a25ccb5e14c9ee0a7f0b97e6a05004e1988604edad0b3b797916cd9ecad986ff |

- Data laws to freeze with them: game-universe filter/dedupe law (14,254 = 14,168 played
  + 19 exhibitions + 67 postponed; tip-UTC Eastern-only canonicalization); **pbp hole =
  14 played games** (ids in ERRATUM_PBP_GAP_R1.md — feature code tolerates, never imputes);
  spread features = UNVERIFIED_PIT ⇒ diagnostic-only; BDL = cross-check spot-source only.

## 5. Metrics + uncertainty (inherited machinery)

- Log loss primary; Brier + reliability + calibration slope [0.85, 1.15] secondary;
  paired date-cluster bootstrap, 10,000 resamples, seed 20261005, per-fold + pooled;
  T1/T2/T3 gate shapes per PROTOCOL_DRAFT_NBA_NG.md (3-of-5 fold bar); playoffs + play-in
  + Cup final reported separately; RS headline only.

## 6. Trial budget (proposed)

- ≤9 scored arms as §3 (one computation per arm on the frozen OOS list = the observed
  denominator unit; diagnostics not counted); replay/repro = +0-trial class (detached
  twin, byte-compare). Exact-arm dry-run before any scored cell (record IDs pairwise
  distinct; empty book = fail).

## 7. Known limitations carried forward

- D2 LOW: `measure_schedule_corpus.json` carries a superseded intermediate dedupe law —
  successor must annotate as superseded (spec law is authority).
- D6/D7 INFO: §2 ET-home subset wording; fold names S1–S4 collide with the sealed S1
  store name — rename folds at freeze (e.g. F1–F5).
- BDL spot-check budget: 5 req/min free tier; re-check sample at freeze (≤25 games).

## 8. Gates still missing before ANY scored run (the registration checklist)

1. Owner instruction naming this successor (this packet is only a proposal).
2. Fresh `researchctl cycle register` (budget from §6; GO phrase registered-not-consumed).
3. Data/code/protocol freeze at the §4 hashes + constants digest; fold renames; annotated
   supersessions (§7).
4. Implementation + synthetic fixtures (no-lookahead mutation, DST boundary, fold
   force-flat, tolerate-14-hole) all PASS.
5. Exact-arm dry-run PASS (non-vacuous; zero denominator delta).
6. Independent A7 prelaunch AUTHORIZED, 0 unresolved HIGH/CRITICAL.
7. Owner typed GO, fresh, verbatim, at THIS cycle's own gate (two-key; nothing survives
   from earlier cycles; P-8).
8. Then scored execution under the machine-wide heavy lock; reproduction twin; A7
   terminal; two-half close.
