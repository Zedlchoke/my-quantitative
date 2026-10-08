# PLAN — SOCCER-APIFOOTBALL-PREP-V1R3 (micro-round: 1X2 odds of ONE real men's-NT match near kickoff; PREP only, $0, ≤3 API requests, one scheduled in-window run)

- cycle_id: `SOCCER-APIFOOTBALL-PREP-V1R3` · asset: shared · budget 0 scored
  cells · no paper rows · registered 2026-10-08 (owner instruction, this chat).
- Owner authority 2026-10-08 (round 4): open the successor micro-round to
  V1R2. Sole target: 1X2 odds of a REAL men's-NT match close to kickoff.
  Priority sample: **England–Croatia, kickoff 2026-11-12T19:45:00Z**, which
  already has a FORECAST in the paper ledger. Free tier only serves
  odds-by-date near the current day → **NO API calls today asking about
  November**. Not integrated into SPORTS-PAPERTRADE-EXEC-V1 this round.
- Inheritance: V1 (docs) → V1R1 (live gates) → V1R2 (`/fixtures?id=` PASS,
  odds date-window gate verbatim). Proven reusable facts: id-join works on
  Free for current seasons; odds rows carry 3-leg Match Winner + row-level
  `update`; the odds window is ±1 day; the anchor (kickoff−6h = 2026-11-12
  T13:45Z) always falls inside the T-1..T+1 window.

## PINNED PROBE SPECIFICATION (prepared now, executed only in-window)

- **Run moment (pinned)**: 2026-11-12T13:00Z (= 20:00 +07 local) — 45 min
  before the anchor 13:45Z, i.e. "gần mốc kickoff−6h nhưng vẫn trước mốc
  đó". One run; in-run transport retries do not consume the API budget
  unless the server answered (HTTP errors are journaled ordinals).
- **Budget (pinned)**: HARD_CAP = 3 API requests, own journal + counter at
  `~/.my-quantitative-data/soccer-apifootball-prep-v1r3/probe/`. Predecessor
  budgets (V1 10/10, V1R2 2/3) are NEVER read/written/reset.
- **Request ladder (pinned order + stop conditions)**:
  - R1 `GET /odds?date=2026-11-12` (known-good param form, page 1).
    Scan every row for the England–Croatia fixture by (teams OR
    fixture_id→later) — rows do NOT carry team names (V1R1 finding), so
    match candidates by kickoff timestamp 1794512700 (2026-11-12T19:45Z)
    and league id 5 (UEFA Nations League). Record paging.total.
    - If exactly one candidate row → go to R3 with its fixture id.
    - If ambiguous (multiple rows share kickoff+league — not expected for
      one fixture) or not found and paging.total == 1 → STOP →
      `NOT_RUN_NO_ODDS_ROW_FOUND` (no guessing, no other-match odds).
    - If not found and paging.total > 1 → R2.
  - R2 `GET /odds?date=2026-11-12&league=5` (server-side league filter —
    untested combo; if it errors with a plan/parameter gate, journal the
    verbatim error and FALL BACK ONCE to `page=2` of R1). Scan as above.
    - Found → R3. Not found after this → STOP → `NOT_RUN_NO_ODDS_ROW_FOUND`
      (with honest sub-reason: budget exhausted before deeper pagination).
  - R3 `GET /fixtures?id=<fixture_id from R1/R2>` → identity join check:
    same id, team names England/Croatia (either order home/away recorded
    as-is), kickoff == 2026-11-12T19:45:00Z, then the paper-standard gates:
    three legs Home/Draw/Away, Pinnacle presence in the odds row,
    `odds_update ≤ fetch < kickoff`, 1:1 join compatibility with the
    ledger FORECAST (team-name level; ledger read-only).
- **No-assumption law**: the API's possession of this fixture is NOT
  assumed; absence → journaled NOT_RUN with the exact reason. Never use
  another match's odds; never fabricate prices; never raise quota; no
  paid-tier workarounds; The Odds API key never used for this service.
- **Key**: read only from `~/.config/soccer-api-football/api_key`; never in
  chat/argv/log/git.
- **PIT note (fixed)**: league-phase UEFA NL = 90'-clean by competition
  rules (running-lane law); the provider's own 90' settlement definition
  remains undocumented → verdict (C) in the packet can be at best
  "competition-rules-90', provider-definition UNDOCUMENTED".

## Execution path (control plane)

The scheduling path exists (workspace cron via ZCode). One ONE-SHOT
automation is created at registration, firing **2026-11-12 20:00 +07**
(13:00Z), carrying the full self-contained runbook (this spec) as its
prompt. The scheduled run: executes the ladder, journals everything
(including errors/empty pages), writes `EVIDENCE_PROBE_R3.json` +
`JOIN_SAMPLE_R3.json`, dispatches the independent verifier (raw bytes,
join, PIT), writes `DECISION_PACKET.md` with the THREE verdicts — (A) NT
odds + Pinnacle real? (B) snapshot/research rights clear enough? (C) Match
Winner proven as 90-minute result? — proposes a dedicated integration
cycle ONLY if all three PASS, sets registry TERMINAL, commits locally.
No GO, no paper bet, no ledger/cadence/model/EV-threshold/wallet change,
no purchase, no push/merge at any point.

## Boundaries

$0; ≤3 API requests this cycle; no API call before the pinned window; no
accounts/purchases; no S1; no push/merge/rebase; registry via researchctl
CAS; exec/paper program (The Odds API lane) UNTOUCHED; ledger read-only
for the FORECAST cross-check. Data under
`~/.my-quantitative-data/soccer-apifootball-prep-v1r3/`.
Worktree/branch: `.worktrees/soccer-apifootball-prep-v1r3/integration` on
`orca/soccer-apifootball-prep-v1r3-integration`. Terminal outcomes:
DECISION_PACKET_PENDING_OWNER | NOT_RUN_NO_ODDS_ROW_FOUND |
NOT_RUN_* (specific) | TECHABORT_*.
