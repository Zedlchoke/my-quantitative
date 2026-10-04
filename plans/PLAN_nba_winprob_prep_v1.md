# PLAN — NBA-WINPROB-PREP-V1 (data-authority + protocol PREP, $0 budget)

- cycle_id: NBA-WINPROB-PREP-V1
- asset: shared (new research program: NBA pre-game win-probability, v1)
- lifecycle target: ACTIVE_LIGHT, budget max = 0 scored cells (PREP-only by law)
- registered per owner chat directive 2026-10-04 (verbatim intent preserved below)

## 0. Owner authority boundary (verbatim intent, not a typed GO)

Owner directive 2026-10-04 authorizes PREP and implementation for an NBA
win-probability program at $0 data/service budget, and states explicitly:

- "Câu này là ủy quyền làm PREP và triển khai, KHÔNG phải typed GO cho một
  cycle chưa đăng ký."
- Forbidden: S1 access, orders, paid services, auto-converting trials,
  account/API-key creation (keyed signup is owner-only per handbook §29),
  push/merge. Root checkout is owner space; lane work in the cycle worktree.
- If all repo gates allowed scoring, execute per plan/registry/gate; if a
  fresh typed GO after A7 or data rights are missing, stop at a complete PREP
  package and report the exact blockage.

Consequence: this cycle registers NO GO phrase and budget max = 0, so no
scored/evaluated outcome can be produced under it. Evaluation lives in a
successor cycle that must be separately registered after this PREP closes.

## 1. Objective

Prepare a fully reproducible historical backtest design for NBA pre-game
win-probability (regular season primary, playoffs separate; log loss primary
metric; forecast skill only — no betting, no PnL, no edge claims), with every
data source rights-verified at $0 and no signup.

## 2. Lanes and separation of duties

| Lane | Role | Write scope | Forbidden |
|---|---|---|---|
| A | independent $0 sources + data-rights audit (web, read-only) | `lanes/A_rights_audit/` | git, accounts/keys, purchases, anything outside lane dir |
| B | coverage/identity/PIT audit of downloaded bytes + dataset design | `lanes/B_dataset/` | same as A |
| C | hypotheses + baselines + evaluation protocol | `lanes/C_protocol/` | same as A |
| NFL | NFL $0 data/rights/PIT/coverage audit, audit-only annex (owner addendum 2026-10-04; NO NFL cycle, NO NFL model/backtest) | `lanes/NFL_AUDIT/` | same as A |
| D | independent verifier AFTER controller synthesis | `lanes/D_verify/` | same as A + never repairs |

Controller (this Lead session) cross-checks lane conclusions against
artifacts, never against chat prose; lands lane commits by pathspec; owns the
registry via `researchctl` only. Lanes return handoff JSON
`zcode_orch_v3_handoff@1` (controller-landed; lanes do not commit, deviation
from §11 one-worktree-per-agent documented as scaled-down single-integration
mode with disjoint directories + sequential controller commits).

## 3. Data authority law ($0, no signup)

Candidates and prior verified facts (to be re-verified independently by A):

- FiveThirtyEight `data` repo, file `nba-elo/nbaallelo.csv`: repo states data
  licensed CC BY 4.0 unless otherwise noted; sports forecasts frozen
  2023-06-13. nba-elo README states game information sourced from
  Basketball-Reference.com → upstream-rights analysis REQUIRED before any
  modeling use (owner directive). Until lane A's memo lands and the
  controller records a decision, modeling use is UNVERIFIED.
- balldontlie: API key required (owner-only signup → BLOCKED_NO_KEY for this
  program); free-tier endpoint scope to be re-verified at docs.balldontlie.io.
- NBA.com/Stats: FAQ states stats not available for download; ToU restricts
  downloads to personal/noncommercial single-machine and stats to news
  reporting/private non-commercial use → NOT_AUTHORIZED for storage.
- Sports Reference (Basketball-Reference): ToU clause 5(11) prohibits
  ML/prediction use of site content including statistics without permission;
  5(9)-(10) restrict automated access and substitute databases → FAIL for
  modeling use; view/cross-check only.
- Raw bytes stay OUTSIDE git under `~/.my-quantitative-data/nba-538-v1/`;
  in-tree artifacts are manifests, hashes, attribution, normalized compact
  derivatives only if size is reasonable, code and documents.

## 4. As-of law (v1, date-grain) — replaces the retired wall-clock rule

Owner defect fix: "T−24h sau 17:00 local ngày trước" is RETIRED (does not fit
all tip-offs and is not reconstructible from date-only data).

v1 law: for game G, the admissible information set is
`S(G) = {all games with date_game strictly before date_game(G)} + static
franchise/identity mappings`. Consequences:

- Same-day games are never inputs to each other (kills same-day ordering
  leakage by construction).
- PIT-safety argument (to be re-proven by lane C with assumptions listed):
  games are dated by start date; earliest realistic tip 11:00 ET; latest
  prior-date completion ~01:30 PT (= 04:30 ET next day) → every prior-date
  game ends ≥ ~6.5h before the earliest next-date tip. Any forecast moment
  in (end of last prior-date game, tip of G) is PIT-valid for S(G).
- Time-grain observables (injury reports with intraday updates, odds
  snapshots, lineup confirmation) are NOT_RUN_PIT in v1: no $0 source with
  historical publish timestamps exists in the verified set. Injury and odds
  features are therefore excluded from v1 entirely.

## 5. Leakage laws (v1)

1. Precomputed Elo (538 `elo_i`/`elo_n`) is a cross-check/golden fixture
   ONLY, never a model input; the model Elo is rebuilt by our own update
   rule under the date-grain as-of law.
2. Team identity: franchise continuity via `fran_id`-style mapping; rename
   census (SEA/OKC, VAN/MEM, NJN/BKN, CHH/CHO/CHA, NOH/NOK/NOP, KC/…) must
   be audited by lane B; one lineage = one rating stream.
3. Neutral-site games (international games, 2020 bubble): cannot be flagged
   from results data alone → documented limitation + sensitivity segment
   (Aug–Oct 2020 restart) in the successor scored protocol; never silently
   dropped.
4. Postponed games: features derive from COMPLETED games only (dates of
   games actually played), so postponements cannot leak; schedule-based
   (future-game) features are NOT_RUN (no as-of schedule snapshots).

## 6. Trial budget, freeze, metrics (binding on the successor scored cycle)

- Arms ≤ 9 total: B0 constant (train-only) = 1; B1 own-Elo grid ≤ 4
  (K × HCA preregistered); B2 logistic PIT variants ≤ 4 (incl. one ablation
  without rest features = H3 kill test).
- Freeze before scoring: grid, features, folds, metrics, PASS thresholds all
  preregistered (lane C artifact) before any evaluation on real outcomes.
- Walk-forward by season, expanding train; regular season primary, playoffs
  reported separately.
- Metrics: mean log loss (primary), Brier, 10-bin reliability +
  calibration slope; paired per-game Δlog-loss vs baselines with block
  bootstrap clustered by game date (95% CI).
- Accuracy is never reported as edge; no PnL anywhere in v1.
- Every scientifically evaluated configuration counts into the observed
  denominator, published or not (P-9).

## 7. Gates of this PREP cycle

- G0 bootstrap: this plan + registry row + worktree/branch committed.
- G1 data authority: lane A memo + controller decision recorded (incl. the
  538↔BRef upstream analysis and the download-or-not decision).
- G2 dataset audit: lane B byte-level audit PASS with hashes.
- G3 protocol frozen: lane C artifact landed.
- G4 implementation: dataset builder + Elo + features code with synthetic
  fixtures PASS (golden hand-computed, no-lookahead mutation test, same-day
  exclusion, rename continuity, B2B computation); NO evaluation on real
  outcomes anywhere in this cycle.
- G5 verification: lane D report with 0 unresolved HIGH/CRITICAL.

Terminal outcomes (negative-first): PREP_COMPLETE_PENDING_OWNER_SUCCESSOR |
BLOCKED_DATA_RIGHTS | BLOCKED_NO_TYPED_GO (expected terminal state: PREP
package complete; evaluation NOT_RUN by construction) | TECHABORT_*.

## 8. GO phrase

This cycle registers NO GO phrase (budget 0, no scored gate). Proposed phrase
for the successor scored cycle (NBA-WINPROB-SCORED-V1, to be registered after
this PREP closes; owner types it ONLY at that cycle's own gate after A7):

    GO NBA WINPROB SCORED V1 EVALUATION

## 9. Limitations

- $0/no-signup constraint excludes balldontlie (key), The Odds API beyond
  its free tier (key), and any paid feed; injury/odds/lineup features are
  NOT_RUN_PIT in v1.
- Date-grain as-of means no intraday information; this is a deliberate
  conservative information set, not a claim it is the live information set.
- The 538 dataset is frozen at 2023-06-13; successor seasons need a later
  rights-cleared source (balldontlie if owner signs up, or other).

## 10. Incidents / deviations

- Deviation from one-worktree-per-lane: single integration worktree with
  disjoint lane directories; controller commits per lane. Recorded here.
- Prior-turn facts used (already verified live on 2026-10-04): NBA Stats FAQ
  download refusal; NBA ToU personal/noncommercial limits; SR ToU 5(9)(10)(11);
  balldontlie ToS §6; The Odds API ToS storage/ML grant; NBA injury-report
  policy timings; 538 CC BY 4.0 + freeze. Lane A re-verifies the load-bearing
  subset independently.
