# PLAN — SOCCER-INTL-90MIN-PREP-V1 (ET-effect study + 90-minute prospective validation protocol; $0; zero scored cells)

- cycle_id: SOCCER-INTL-90MIN-PREP-V1 · asset: shared ·
  **budget 0/0 by law** (descriptive study of an ALREADY-EXPOSED window +
  source documentation + protocol drafting; nothing scored, nothing
  purchased, no model change) · GO phrase registered, NOT typed:
  `GO SOCCER INTL 90MIN PREP V1 QUALIFIED PROTOCOL`.
- Owner authority 2026-10-09 (this chat): open ONE PREP to study the
  men's-international model **under correct 90-minute results**: how extra
  time affects labels, the rating stream and draw probabilities; and prepare
  the prospective validation protocol. STOP before any GO or scored run.
  Every number on the 441 matches and the [2001,2023) window carries the
  label **RETROSPECTIVE_DIAGNOSTIC_POSTHOC**; 2023+ is partially revealed
  (ERRATUM) — never a clean holdout, never called a new OOS, never edge or
  PnL. Closed TERMINAL verdicts, the paper ledger and every automation are
  read-only.

## Inheritance (cite, never duplicate or modify)

- `SOCCER-INTL-WINPROB-SCORED-V1` (TERMINAL 6d3e659): frozen arms of record
  (B1 K=48 ν=0.6 HCA=65; V1 HCA=80; B0 0.495584/0.231516/0.272900),
  engine bytes, recorded `SCORED_postgo-1.json`. READ-ONLY.
- `SOCCER-1X2-POSTHOC-ANALYSIS-V1` (591d5a54, this session's lanes): the
  36/36-EXACT reproduction recipe, corpus-target vs 90-min audit (4,838 +
  14,445 + 1,425), and lane L_DIAG441 (the 441-match
  RETROSPECTIVE_DIAGNOSTIC_POSTHOC_SUBSET with per-match vectors, verifier
  VERIFY_PASS_WITH_FINDINGS 137/0). READ-ONLY.
- `SOCCER-1X2-SOURCE-PREP-V1` (15fa917b): openfootball CC0 clones pinned
  (worldcup `19155966c…`, euro `88d150a6c…`), ET paren convention +
  ERRATUM_R2 (Greece–Czech 2004-07-01 ⇒ flips class = 20), JOIN artifact
  443 rows (421+20+2), 984 NOT_RUN (982 non-covered + 2 euro-2016
  date-error). READ-ONLY.

## Tasks

1. **RATING STREAM ET AUDIT (reproduce first or BLOCKED):** re-run the
   frozen replay and require the reproduction gate 36/36 float-exact vs
   `SCORED_postgo-1.json` AND byte-identical engine extract sha
   `6ba7709d…`; mismatch ⇒ **BLOCKED_REPRODUCTION, halt**. Then identify
   exactly which matches fed a post-ET result into the Elo update: the 20
   proven OOS flips (openfootball bytes) + a full WC/Euro census of
   ET-decided corpus-H/A rows across ALL editions 1930–2024 (the stream
   predates 2001; disclose the train-era pollution without rerunning it).
   For each OOS flip: update timestamp (end-of-day Phase 2), and downstream
   forecast impact.
2. **SOURCES FOR THE 984 (documentation only, $0, no API calls, no key
   reads, no accounts, no scraping of forbidden sources):** per source:
   rights (primary quote + URL + retrieval time), REAL measured coverage
   for the 7 uncovered competitions (AFCON 272, Gold Cup 225, Copa América
   157, AFC Asian Cup 144, Confed Cup 79, Viva WC 57, Arab Cup 48) + the 2
   euro-2016 rows, 1:1 join law (date + two teams + crosswalk), the 90-min
   score field, ET/pens encoding, ambiguous-row accounting.
   football-data.org `score.regularTime` is a named candidate: record what
   the docs literally say the field is; **coverage and rights are NOT
   inferrable from docs — NOT_RUN_PENDING_PROBE**. Upstream openfootball
   may have moved (repos are live): `git ls-remote` re-pin check allowed
   (read-only); a fresh re-parse could resolve the 2 euro-2016 rows.
3. **RETROSPECTIVE SENSITIVITY (same-universe counterfactual):** original
   stream vs stream whose update targets use the 90-minute labels WHERE
   PROVEN (the 20 flips); K/ν/HCA and the PIT day-batch law unchanged;
   nothing tuned. Disclose exactly which games change rating state, per
   flip update timestamps, and the impact on p_home/p_draw/p_away, LL, RPS,
   Brier — same 20,708-row universe both sides (no row dropped, so no
   universe confound); splits 421 keep / 20 flip / missing NOT_RUN. The
   counterfactual is a LOWER BOUND on ET pollution (984 OOS + train-era
   ET-decided rows keep their original updates); no improvement language.
4. **DRAW CALIBRATION (no tuning, no winner selection):** predicted-draw
   deciles for B0/B1/V1 on the same rows: full OOS 20,708 + friendly /
   competitive + WC/Euro group vs knockout (phase derived deterministically
   per edition and validated against openfootball round headers;
   editions that fail validation ⇒ NOT_RUN_PHASE) + eras + the 441/20
   subsets. Observed-vs-predicted with 95% Wilson intervals; bins under the
   engine's 50-row floor are INVALID, never interpreted. The 20-flip bin
   counts are disclosed but carry no inference.
5. **FREEZE PACKET for the prospective 90-minute 1X2 validation** (draft,
   no run): target = 90-minute 1X2; fixture+result source with proven
   rights; forecast timestamp strictly pre-kickoff; as-of rating law
   (end-of-D-1 snapshot); postponement/cancellation/ET handling; baseline
   arms; metrics; minimum sample; fail conditions. Odds must carry the SAME
   90-minute market definition and a pre-decision timestamp; any missing
   evidence ⇒ NOT_RUN line. Knockout stays **BLOCKED for paper trade**
   until target and odds settlement rules are proven aligned.
6. Independent verifier re-derives joins, labels and metrics from bytes.

## Boundaries

$0; documentation-only web access; NO API calls of any kind, NO key reads,
NO accounts, NO purchases, NO scraping of rights-restricted sources; no S1;
no push/merge/rebase; registry via researchctl CAS; closed verdicts, paper
ledger, automations and every other cycle read-only; heavy lock for the
replays (short, bounded); missing evidence = NOT_RUN_*; worktree
`.worktrees/soccer-intl-90min-prep-v1/integration` on
`orca/soccer-intl-90min-prep-v1-integration`; artifacts under
`research/control/SOCCER-INTL-90MIN-PREP-V1/`. Labels:
RETROSPECTIVE_DIAGNOSTIC_POSTHOC on all 441/window numbers; no model,
paper-adapter or ledger change in this cycle.

## Terminal outcomes (negative-first)

**90MIN_PREP_STUDY_COMPLETE** (audit + source matrix + sensitivity +
calibration + freeze packet + decision packet delivered; NOT_RUN count may
be large — a documented zero-coverage answer is valid) | BLOCKED_REPRODUCTION
(engine bytes/floats drift vs the recorded artifacts) | NOT_RUN_* |
BLOCKED_* | TECHABORT_*. GO phrase stays unconsumed; no scored run is
authorized by this plan.
