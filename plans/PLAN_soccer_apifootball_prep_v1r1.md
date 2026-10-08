# PLAN — SOCCER-APIFOOTBALL-PREP-V1R1 (successor probe: API-Football fixture + $0 1X2 odds for men's NT soccer; PREP only, $0, ≤5 remaining API requests)

- cycle_id: `SOCCER-APIFOOTBALL-PREP-V1R1` · asset: shared · budget 0 scored
  cells · no paper rows · registered 2026-10-08 (owner instruction, this chat).
- Owner authority 2026-10-08 (round 2): "Key đã được thay tại
  ~/.config/soccer-api-football/api_key. Chạy probe kế nhiệm theo
  plan_successor.json, tối đa 5 request còn lại. Kiểm tra xác thực trước,
  rồi mới kiểm tra fixture và odds; không in key hoặc sửa chương trình
  paper đang chạy."
- Predecessor `SOCCER-APIFOOTBALL-PREP-V1` closed TERMINAL
  NEED_OWNER_KEY_CHECK at f8e729b4 (verifier PASS_WITH_NOTES); governance
  forbids TERMINAL→ACTIVE_LIGHT, so this is a NEW registered round on a
  branch parented at the predecessor's terminal head — same law, same
  harness, same shared request budget (probe_state.json: 5/10 used, 5 left,
  HARD_CAP=10 enforced pre-send by the harness).

## Work items

1. **AUTH FIRST** — `/status` (request 6/10). If token error again → stop,
   verdict NOT_RUN_KEY_REJECTED_AGAIN, re-escalate to owner. If valid:
   journal account/plan/requests.current+limit_day.
2. **CATALOGUE** — `/leagues?country=World` (request 7/10): league ids +
   current seasons + per-league coverage flags (odds true/false) for every
   in-scope men's-NT family. Catalogue ≠ odds — flag only gates.
3. **FIXTURES** — `/fixtures?league=<id>&next=25&timezone=UTC` (request 8/10)
   for ONE in-scope league chosen at runtime (prefer odds:true and nearest
   upcoming matches; friendlies or WCQ or NL as availability dictates):
   fixture id, UTC kickoff, round/stage, status.
4. **ODDS** — `/odds?fixture=<id>` (requests 9-10/10) for TWO real fixtures
   from step 3: bets "Match Winner" 3 values Home/Draw/Away, bookmaker
   names/ids, per-bookmaker update timestamp vs fetch time.
5. **JOIN SAMPLE** — on the probed fixtures: API-Football team names →
   crosswalk (predecessor's EXTENDED_CROSSWALK pattern, fail-closed) →
   martj42 corpus entity → odds leg. Missing leg → NOT_RUN with exact
   reason. B1 probabilities re-use the predecessor's proven plumbing;
   no synthetic data.
6. **VERIFIER (fresh context)** + **DECISION_PACKET** update: per-league
   PASS/CONDITIONAL/NOT_RUN, coverage catalogue-vs-real, rights/PIT (90'
   definition still undocumented → knockout gate stands), free-tier season
   reality, bookmaker observation, Pinnacle question (if applicable) for the
   owner. Terminal outcomes: DECISION_PACKET_PENDING_OWNER |
   NOT_RUN_KEY_REJECTED_AGAIN | NOT_RUN_SOURCE | TECHABORT_*.

## Boundaries

$0; ≤5 API requests THIS round (10 lifetime cap shared with V1 via
probe_state.json); key bytes never in chat/log/git; The Odds API key never
used for this service; no accounts/purchases; no S1; no push/merge/rebase;
registry via researchctl CAS; exec/NBA/WNBA/NFL/discovery worktrees +
ledgers + models + EV thresholds + 1,000 USD wallet UNTOUCHED; no GO typed;
politeness (sequential, 1.5 s spacing, backoff on 429/5xx). Data continues
under `~/.my-quantitative-data/soccer-apifootball-prep-v1/` (shared with V1
by design — the request journal is the budget authority).
Worktree/branch: `.worktrees/soccer-apifootball-prep-v1r1/integration` on
`orca/soccer-apifootball-prep-v1r1-integration`.
