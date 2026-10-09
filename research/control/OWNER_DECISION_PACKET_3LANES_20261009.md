# OWNER DECISION PACKET — THREE LANES 2026-10-09 (NFL P2 / Soccer 1X2 post-hoc / WSL discovery)

Owner instruction 2026-10-09 executed: three separate lanes, independent
verifiers, STOP before every scored OOS and before every owner GO. All three
cycles: $0 spent, 0 scored cells consumed, GO phrases REGISTERED_NOT_
CONSUMED, no push/merge, no purchases/accounts, no S1 access. Registered
cycles (plans committed at main `ba117cef`):

| lane | cycle_id | branch @ head (measured 2026-10-09) | verdict |
|---|---|---|---|
| NFL P2 | NFL-WINPROB-P2-RESELECT-PREP-V1 | orca/nfl-winprob-p2-reselect-prep-v1-integration @ dccecb12 | **SELECTION_NEGATIVE_NO_THETA_BEATS_B1STAR_BASE10** (valid negative; nothing scored) |
| Soccer | SOCCER-1X2-POSTHOC-ANALYSIS-V1 | orca/soccer-1x2-posthoc-v1-integration @ d8e11d98 | **POSTHOC_DESCRIPTIVE_COMPLETE** (reproduction gate 36/36 EXACT) |
| WSL | WSL-WINPROB-DISCOVERY-PREP-V1 | orca/wsl-winprob-discovery-prep-v1-integration @ 4c4c39bc | **DISCOVERY_QUALIFICATION_COMPLETE_NOT_RUN_ODDS** |

## Comparison table

| dimension | NFL (P2 successor) | Soccer nam (1X2 post-hoc) | WSL (new discovery) |
|---|---|---|---|
| Data & rights | games.csv f1e8fe78 (nflverse, read-only, prior pins); pbp 2000–2017 read-only; no new downloads | corpus results.csv df35268f (martj42, CC0-1.0) + shootouts/former_names; engine bytes read-only from TERMINAL branch (6ba7709d) | ewf-database clone HEAD ffd15562 pinned; **CC BY-SA 4.0 verified verbatim** — internal non-shared research unencumbered; public derivatives owe attribution+share-alike (textual reading, not legal advice) |
| Match counts in scope | TRAIN 5,057 rows 2000–2018 (inner-eval 1,275; ties 9; neutral 51) | OOS 20,708 rows 2001–2022 (friendly 7,145 / competitive 13,563) | WSL tier-1 1,335 matches / 15 seasons 2011–2024/25 (modern 12-team era 660 across 5 seasons; train proposal 2020-21..2023-24 = 528) |
| Proven (PASS with evidence) | E1 machine reproduction EXACT (0.6407092590929282; 7/7 folds ≤1e-9); one-delta base-10 port proven; null θ=0 bit-for-bit ≡ B1*; B0/folds identity; deterministic re-runs byte-identical; independent verifier recompute **VERIFY_PASS zero-drift** (re-ran both scripts under lock) | Frozen engine reproduces recorded scored run **exactly** (36/36 field equality incl. stop_at=2023-01-01 → OOS independent of 2023+); argmax accuracy measured per slice/year; game-by-game 90-min audit counts; verifier independent corpus-side recompute (pending verdict line) | License + coverage measured from bytes (15/15 seasons standings cross-check); renames/awarded/same-day laws mapped; B0 3-way train proposal computed (0.429924/0.170455/0.399621); WSL-fresh Elo/Davidson grids with rationale; synthetic PIT battery 7/7 (verifier recompute pending) |
| NOT_RUN (recorded, never inferred) | C3 θ under base-10: **no selectable point** (θ=25 +0.001830 slope 0.832 FAIL band; monotone worse to θ=100); finer θ∈(0,25) NOT measured; 2019–2025 scored pass NOT_RUN (this round); 2026+ belongs to live NG cycle | **1,425 rows NOT_RUN_TARGET_NO_ET_FLAG** (90-min outcome unresolvable from corpus); **NOT_RUN_ODDS_MEN_INTL** (no Class-A pre-match-timestamped 1X2 source at $0); 2023+ not used (partially revealed per ERRATUM) | **NOT_RUN_ODDS** (no WSL key at The Odds API; Betfair 403 w/o account; OddsPortal bars scraping; zero women's coverage in free CSVs); NOT_RUN_NO_KICKOFF_TIME / NOT_RUN_NO_VENUE (source lacks fields); NOT_RUN_NO_2025_26; 1 anomalous row (M-2024-2025-1-001-M) needs a successor law |
| Cost | $0 | $0 | $0 |
| Risks | (i) e→b10 equivalence intuition fails across machineries (trajectories differ) — that's WHY the re-run was required; (ii) any future 2019–2025 number is replication-only, never fresh evidence; (iii) tempting "finer grid" is a NEW experiment — silent extension forbidden | (i) accuracy ≈ mean max-prob must NOT be read as edge; (ii) 69.7% "structure-compatible" rows are compatible only under tournament-structure assumptions; (iii) 2023+ is not a clean holdout — permanent caveat | (i) kickoff times absent forever → day-batch law only, T0−Xh anchor impossible from this source; (ii) share-alike triggers on public derivatives; (iii) tiny data (528 train) → high variance, small grids only; (iv) 2 awarded matches poison goal-informed models unless dropped |
| Independent verifier | **VERIFY_PASS** (dccecb12) | **VERIFY_PASS** (8d4cfbec/d8e11d98; 2 informational findings, zero measured impact: heuristic hint-list looseness selects the identical 1,425 ambiguous rows; shootout file 683 rows vs 682 joined — both statements accurate as written) | **VERIFY_PASS** (407ff0a4/3131e939; 3 non-blocking prose-level findings in the proposal: odds-ratio arithmetic 1.413–2.371× vs quoted 1.5–3.5×, implied-q figures, one cosmetic label — all recorded in the verify report; census/license/B0/battery all reproduced exactly) |

## Owner decisions required (nothing self-executes)

**NFL (D-P2, pick ONE):**
- **D-P2-1 (recommended):** accept the negative. C3 slot released
  (`NOT_RUN_SELECTION_NEGATIVE`). If any scored pass is wanted, authorize
  the reduced B0+B1_STAR replication pass (2/3 cells) — its GO phrase is
  `GO NFL WINPROB P2 RESELECT PREP V1 SCORED PASS`, typed ONLY by the owner,
  verbatim, fresh, at this cycle's own gate after A7 prelaunch of that pass.
- **D-P2-2:** authorize a NEW preregistered finer low-θ grid (e.g.
  {5,10,15,20}) under the identical folds law, still TRAIN-only.
- **D-P2-3:** halt the P2 line (machinery question already answered).

**Soccer (D-S1X2, pick any subset):**
- **D-S1X2-1:** accept POSTHOC_DESCRIPTIVE_COMPLETE as the answer to "can
  the model serve 1X2 odds": probabilities YES (calibrated, recorded),
  odds-serving **blocked on evidence** (no $0 Class-A odds source; 1,425
  targets unresolvable). No edge claim exists or is made.
- **D-S1X2-2 (optional, paid):** authorize a budgeted census of The Odds API
  historical h2h for internationals (day×credit cost model first, WNBA
  precedent) — requires explicit spend authorization.
- **D-S1X2-3 (optional, $0):** authorize a successor to hunt a 90-minute
  results source with ET flags (resolves the 1,425 rows + future targets).

**WSL (D-WSL, pick any subset):**
- **D-WSL-1 (recommended):** accept DISCOVERY_QUALIFICATION_COMPLETE with
  NOT_RUN_ODDS; the probability-research leg is ready to register a scored
  successor PREP under the written gates (`wsl_winprob_freeze@1` template +
  scored-successor conditions in the design doc).
- **D-WSL-2 (optional):** name additional odds sources/leads to survey
  (sales inquiries, licensed archives) before the successor round.
- **D-WSL-3:** pin the successor's as-of law: day-batch (date-granular,
  source has no kickoff times) — or fund a kickoff-time source search.

## Stopping state (all three lanes)

budget 0 used everywhere · GO phrases unconsumed · heavy lock released ·
worktrees clean · no push/merge · S1 untouched · every other cycle's
ledgers/models byte-untouched (NG prospective ledger 129 rows verified
untouched by the NFL verifier) · no betting-edge claim anywhere (accuracy
and log loss are calibration descriptors only).
