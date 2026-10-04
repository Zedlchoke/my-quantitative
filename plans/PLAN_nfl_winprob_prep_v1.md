# PLAN — NFL-WINPROB-PREP-V1 (data-authority + protocol PREP, $0 budget)

- cycle_id: NFL-WINPROB-PREP-V1 · asset: shared · lifecycle: ACTIVE_LIGHT, budget 0 scored cells, NO GO phrase (PREP-only by law)
- registered per owner chat directive 2026-10-04 (NFL authorization round): owner authorizes
  downloading CLEARLY-RIGHTED free NFL data, data audit, hypothesis research, and win-probability
  model PREP "giống NBA". The message is explicitly NOT a typed GO for scoring/backtest on real
  outcomes. No S1, no push/merge, no accounts/keys/purchases, no orders/betting. No mixing of
  NBA budget/trials/data. If root carries others' changes: preserve, wait for valid registration
  path, never reset/overwrite.

## 1. Data authority law ($0, no signup)

- PRIMARY: nflverse/nflverse-data RELEASES only — data license CC BY 4.0 (verbatim-verified
  2026-10-04 in the NBA-PREP annex NFL_DATA_RIGHTS_MATRIX.md E1: "reproduce and Share ... in
  whole or in part" + database-rights clause "extract, reuse, reproduce, and Share all or a
  substantial portion of the contents of the database"). Re-verified live by lane A this cycle.
- Scope of download (lane B): `schedules` release games.csv (full history) + release
  timestamp.json + GitHub release metadata (tag, asset updated_at, size) + `pbp` release subset
  (5 most-recent complete seasons) for audit only. Raw bytes OUTSIDE git under
  ~/.my-quantitative-data/nfl-nflverse-v1/raw/ with ATTRIBUTION.md (CC BY 4.0, nflverse
  attribution string, release tag, pull time UTC, sha256, bytes, no-endorsement note).
- BANNED: nflverse/nfldata repo files (repo has NO license — annex R5), NFL.com scraping (R9
  FAIL), Pro Football Reference scraping (R8 FAIL 5(10)/5(11)), ESPN endpoints (R10 UNVERIFIED),
  any keyed/paid API (balldontlie/Tank01/The Odds API — BLOCKED_NO_KEY / NOT_RUN).
- Features v1: game-level results ONLY. Play-by-play is downloaded for audit but NOT a v1
  feature source (post-game compilation + mid-week retro corrections — annex E5; WP/EP columns
  are model outputs). Betting/odds columns (spread_line, moneylines) are closing-line-contaminated
  → quarantined at build, never features. Injuries: PIT at publication time NOT provable
  (date_modified ≠ announcement time — annex R4) → NOT_RUN_PIT, excluded from v1.

## 2. As-of law (v1, kickoff grain)

For game G: admissible information = games with kickoff (gametime, UTC-parsed) strictly before
kickoff(G) + static identity mappings. games.csv carries `gametime`; if parse/coverage proves
inadequate in lane B's census, degrade to DAY grain (kickoff date strictly before) with the
degradation measured and recorded; week grain only as last resort. Same-day doubleheaders do not
exist in the NFL; byes are handled naturally via rest-day features.

## 3. Identity / era laws

- Team renames relocations map to one lineage stream each (abbrev changes e.g. SD→LAC, OAK→LV,
  STL→LA; WAS continuity) — frozen mapping table audited by lane B, fixture at build.
- Neutral-site games (Super Bowl, international series) — games.csv `site`/neutral indicators
  audited by lane B; if not flaggable → declared limitation + sensitivity (mirror NBA precedent).
- Playoffs: game_type filter; regular season primary, playoffs separate report.
- Postponements/re-schedules: features derive from completed games only (PIT-clean by construction).

## 4. Lanes and separation of duties

| Lane | Role | Write scope (worktree) |
|---|---|---|
| A | rights + provenance/PIT re-verification (web read-only) | lanes/NFL_A_rights/ |
| B | download, coverage/identity/quality census, hash manifest | lanes/NFL_B_dataset/ |
| C | 2-3 mechanism hypotheses + B0/B1/B2 + evaluation protocol | lanes/NFL_C_protocol/ |
| D | independent verifier AFTER controller synthesis | lanes/NFL_D_verify/ |
Handoff JSON `zcode_orch_v3_handoff@1` per lane; controller lands commits by pathspec; lanes
never touch registry/other cycles/NBA artifacts.

## 5. Gates

- G0 bootstrap (this plan + registry + worktree) · G1 lane A rights PASS · G2 lane B census +
  hashes PASS · G3 protocol frozen · G4 builder/features + synthetic tests PASS + mechanics-only
  real-data transform (NO metric on real outcomes) · G5 lane D verification 0 HIGH/CRITICAL.
Terminal: PREP_COMPLETE_PENDING_OWNER_SUCCESSOR | BLOCKED_DATA_RIGHTS | TECHABORT_*.
Scoring lives in a successor cycle (NFL-WINPROB-SCORED-V1) requiring fresh registration + A7 +
owner GO at its own gate. This cycle registers NO GO phrase.

## 6. Boundaries

Raw + derived outside git; in-tree: code, docs, manifests, hashes. No metric computation on
real outcomes anywhere in this cycle. No NBA asset reuse (separate package `nfl_winprob/`,
separate data dir, separate ledger). NFL matrix annex remains untouched (append-only history).
