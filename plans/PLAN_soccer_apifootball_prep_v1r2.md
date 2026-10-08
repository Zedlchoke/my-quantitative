# PLAN — SOCCER-APIFOOTBALL-PREP-V1R2 (single question: does `/fixtures?id=<id>` work on the API-Football FREE tier to join a live odds row with team names; PREP only, $0, ≤3 API requests)

- cycle_id: `SOCCER-APIFOOTBALL-PREP-V1R2` · asset: shared · budget 0 scored
  cells · no paper rows · registered 2026-10-08 (owner instruction, this chat).
- Owner authority 2026-10-08 (round 3): "Mục tiêu duy nhất: kiểm tra liệu gói
  API-Football Free có cho phép ghép một dòng odds hiện tại với tên hai đội
  bằng endpoint chính thức `/fixtures?id=<fixture_id>` hay không. … Giới hạn
  tối đa 3 API request cho cycle mới, $0 … Không sửa hay 'reset' budget 10/10
  của cycle đã đóng."
- Predecessors: V1 (docs + key rejected, TERMINAL NEED_OWNER_KEY_CHECK,
  f8e729b4) and V1R1 (live probe, TERMINAL DECISION_PACKET_PENDING_OWNER,
  30f2897c): free tier season gate blocks /fixtures by season and `next=` is
  paid-only; odds rows carry no team names; `/fixtures?id=` bypass was the
  recorded residual gap — this round closes exactly that question.

## Work items

1. **SAMPLE SELECTION (no API cost)** — fixture id 1492390 taken from the
   STORED V1R1 raw odds response (`10_odds_date_today.json`, sha256
   8180be47…): Serie A (Brazil) league 71 season 2026, kickoff
   2026-10-08T23:00:00Z, row update 2026-10-07T20:01:16Z, Pinnacle Match
   Winner 2.12/3.20/3.79. No fabricated ids.
2. **ID-JOIN PROBE (request 1/3)** — `/fixtures?id=1492390` with the Free
   key. Record status, response sha256, fetch UTC, ordinal in a NEW journal
   under `~/.my-quantitative-data/soccer-apifootball-prep-v1r2/probe/` with
   its own counter (HARD_CAP=3). The closed cycle's probe_state (10/10)
   is untouched. Check: same fixture id, HOME/AWAY team names present,
   kickoff equals the odds row's kickoff.
3. **BRANCH A (blocked)** — verbatim plan/season error → verdict
   `NOT_RUN_FREE_FIXTURE_ID_BLOCKED`. No paid-tier workarounds attempted.
4. **BRANCH B (pass)** — verdict `ID_JOIN_MECHANISM_PASS` (CLUB sample
   only; NO inference that NT matches have odds). Then ONE attempt at an
   international sample: `/odds?date=2026-11-14` (request 2/3; UEFA NL
   November matchday window) — if real NT odds rows exist pre-match, take
   ONE row → `/fixtures?id=<that id>` (request 3/3) and check the paper
   standard: 1:1 join of both team names to the martj42 corpus entity set,
   `odds_update ≤ fetch < kickoff`, three legs Home/Draw/Away, Pinnacle
   present, 90-minute result definition (league-phase = 90'-clean by
   competition rules; knockout = unproven). Any missing condition →
   sample not paper-grade; no NT odds row → `NOT_RUN_NO_INTL_ODDS_SAMPLE`.
5. **VERIFIER (fresh context)** — re-checks raw-vs-response, join logic,
   budget accounting, key safety, boundaries.
6. **DECISION PACKET** — three separate verdicts as the owner requested:
   (a) does `/fixtures?id=` work on Free; (b) does a real NT sample exist;
   (c) is there enough data + rights to even consider integration.

## Boundaries

$0; ≤3 API requests TOTAL this cycle (own journal + counter); key bytes
never in chat/argv/log/git; no paid-tier workarounds; The Odds API key
never used; no accounts/purchases; no S1; no push/merge/rebase; registry
via researchctl CAS; exec/NBA/WNBA/NFL/discovery + V1/V1R1 worktrees,
ledgers, models, EV thresholds, 1,000 USD wallet UNTOUCHED; no GO typed.
Data under `~/.my-quantitative-data/soccer-apifootball-prep-v1r2/`.
Worktree/branch: `.worktrees/soccer-apifootball-prep-v1r2/integration` on
`orca/soccer-apifootball-prep-v1r2-integration`. Terminal outcomes:
DECISION_PACKET_PENDING_OWNER | NOT_RUN_FREE_FIXTURE_ID_BLOCKED |
NOT_RUN_NO_INTL_ODDS_SAMPLE | TECHABORT_*.
