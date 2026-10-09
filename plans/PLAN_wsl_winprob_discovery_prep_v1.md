# PLAN — WSL-WINPROB-DISCOVERY-PREP-V1 (English Women's Super League: data discovery + qualification + baseline design, $0, zero scored)

- cycle_id: WSL-WINPROB-DISCOVERY-PREP-V1 · asset: shared · ACTIVE_LIGHT ·
  **budget 0/0 by law** (DISCOVERY/PREP only; nothing scored this round) ·
  GO phrase registered, NOT typed:
  `GO WSL WINPROB DISCOVERY PREP V1 SCORED RUN`.
- Owner authority 2026-10-09 (this chat): open EXACTLY ONE new
  DISCOVERY/PREP cycle for the English Women's Super League (WSL), not
  scored. Women's football data/baselines are designed FRESH — parameters of
  the men's-international cycle (K=48/ν=0.6/HCA=65) are NEVER copied;
  anything shared must be re-derived and justified from WSL's own data scale
  and calendar. If no qualifying odds source exists, the odds leg records
  **NOT_RUN_ODDS** while the probability-research leg still completes.

## Tasks

1. **EWF DATABASE AUDIT (measured from bytes):** pin a snapshot of
   https://github.com/probjects/ewf-database (clone into
   `~/.my-quantitative-data/wsl-winprob-discovery-prep-v1/ewf-database/`,
   record HEAD sha + per-file sha256 + retrieval timestamps). Measure, never
   assume: license file text (claimed CC BY-SA 4.0 — verify verbatim +
   attribution/share-alike implications for internal research); seasons
   covered; matches per season (WSL specifically); field completeness
   (date, kickoff TIME presence, home/away, scores, venue); team-rename
   lineage (former names, promotion/relegation identity); tie/walkover/
   awarded-match handling; same-day multi-match law (what a day-batch
   prediction rule can and cannot claim); duplicate/contradictory-row
   posture. Verdict per class: EVIDENCED / NOT_RUN_<gap>.
2. **FUTURE FIXTURES + 1X2 ODDS SOURCE SURVEY (documentation only, no API
   calls, no standing-key use, no purchases):** per candidate source (odds
   APIs' women's-football league coverage pages, historical odds archives,
   free CSV sources, exchange archives): seasons covered, 1X2 availability,
   pre-match snapshot timestamp semantics, rights (primary quote), cost,
   machine-downloadability. Classify Class A/B/C per the
   WNBA-ODDS-DISCOVERY qualification law. If no source reaches Class A/B
   with evidenced rights + PIT timestamps ⇒ record **NOT_RUN_ODDS** with the
   specific reason.
3. **BASELINE PROPOSAL (WSL-fresh, PROPOSAL_DRAFT — frozen only in a
   successor round):** B0 three-outcome constant computed on WSL train
   seasons only (value disclosed as train-internal descriptive statistic);
   Elo/Davidson baseline with parameter grids sized to WSL's data volume
   (~10–12 teams, ~22 rounds/season; order-of-magnitude fewer matches than
   the men's corpus) and documented rationale for each grid bound; day-batch
   law; HCA and ν tie-model treatment with designed nulls (θ=0-style
   equivalence arms) per house doctrine. No OOS numbers, no selection on
   future outcomes.
4. **DESIGN: walk-forward by season** (train on complete prior seasons,
   evaluate next season; season-boundary law; promotion/relegation identity
   law), freeze-packet TEMPLATE (what a scored successor must pin: universe,
   ties, splits, metrics MIN_VALID floors, margins-to-fail, trial budget,
   seed, claim caps), synthetic PIT test battery LIST + implementation for
   the proposed pipeline shape (same-day exclusion, season boundary,
   renames, 3-way normalization, as-of timestamp strict inequality,
   missing-data fail-closed, ledger tamper detection) — synthetic corpora
   only, zero real scored rows, and **conditions to register a scored
   successor** (which gates must PASS first).
5. Controller artifacts; independent verifier re-derives season counts,
   license quote, and the B0 descriptive value from the pinned bytes.

## Boundaries

$0 (public repo clone + documentation only); no purchases; no accounts; no
paid API calls; no S1; no push/merge/rebase; registry via researchctl CAS;
other cycles untouched; calibration vocabulary only — no betting/edge
language; missing evidence = NOT_RUN_*; worktree
`.worktrees/wsl-winprob-discovery-prep-v1/integration` on
`orca/wsl-winprob-discovery-prep-v1-integration`; artifacts under
`research/control/WSL-WINPROB-DISCOVERY-PREP-V1/`.

## Terminal outcomes (negative-first)

**DISCOVERY_QUALIFICATION_COMPLETE_<ODDS_VERDICT>** (odds verdict ∈
{CLASS_A_PRESENT, NOT_RUN_ODDS, NOT_RUN_INSUFFICIENT_COVERAGE}; baselines +
design + conditions delivered; nothing scored) | BLOCKED_LICENSE |
BLOCKED_DATA (repo unreachable/unverifiable) | NOT_RUN_* | TECHABORT_*. The
GO phrase stays unconsumed; an early/paraphrased GO dies unconsumed.
