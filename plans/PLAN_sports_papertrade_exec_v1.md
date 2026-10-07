# PLAN — SPORTS-PAPERTRADE-EXEC-V1 (ONE-GO execution umbrella for NBA + WNBA-2026 + SOCCER paper, $0)

- cycle_id: `SPORTS-PAPERTRADE-EXEC-V1` · asset: shared · budget 0 scored cells ·
  registered 2026-10-07 (owner round-3 instruction, this chat).
- Owner authority 2026-10-07: "chuẩn bị NBA, WNBA và bóng đá nam quốc tế để Owner
  chỉ cần gõ MỘT GO duy nhất, sau đó hệ thống paper trade tự vận hành cho cả ba
  giải khi từng trận đủ điều kiện"; "Không lách hoặc giả vờ đã tiêu các GO riêng
  đang đăng ký"; "Nếu luật hiện hành không cho gộp, hãy lập successor cycle hoặc
  amendment hợp lệ, đăng ký/freeze một phrase GO duy nhất". Explicitly **NOT a
  typed GO**; no real paper row in this prep round.
- THE ONE GO (REGISTERED_NOT_CONSUMED; typed ONLY by the owner, verbatim, fresh,
  at this cycle's own gate):
  **`GO SPORTS PAPERTRADE EXEC V1 RUN ALL`**

## 1. What the one GO authorizes (declared here, BEFORE typing)

Typing the phrase above authorizes the controller to:
1. Create the REAL paper ledger GENESIS (one wallet 1,000.00 USD) under
   SPORTS-PAPERTRADE-V1 laws (5.00 fixed stake; 100.00 open cap in-lock; EV≥5%
   on listed odds with c=0.02 frozen assumption; 10% drawdown pause; one
   selection per match; T-6h/anchor PIT laws; refund settlement law).
2. Execute prospective forecasting for the three absorbed lanes, using ONLY the
   frozen artifacts of: `WNBA-WINPROB-2026-REMAINDER-V1` (B1-WNBA verbatim,
   pins 82263eab…/b9446f76…, head d6ed119e), `NBA-WINPROB-PROSPECTIVE-PREP-V1`
   (B1* K=32/HCA=100/γ=0.75 + slope-0.8107 disclosure, head e23f0fa8),
   `SOCCER-INTL-WINPROB-PROSPECTIVE-PREP-V1` (B1 K=48/ν=0.6/HCA=65, head
   78ae172f).
3. Record the three cycles' registry phases as
   `EXEC_GO_CONSUMED_VIA_SPORTS-PAPERTRADE-EXEC-V1 <verbatim phrase> <ts>` —
   an explicit cross-reference journal entry. **Their own GO phrases are
   SUPERSEDED and die UNCONSUMED** (never marked consumed); the owner typed ONE
   fresh phrase at THIS gate, whose §1 mapping the owner read before typing.
4. Operate the cadence: per-league day batches at each league's anchor law
   (NBA/WNBA tip-relative T0−6h10m; SOCCER kickoff−6h strict), odds capture
   quota-guarded (pinnacle; 4 credits/day + 120/month caps), decision + ledger
   append + dashboard refresh; settlements after results.
5. Schedule automation (cron) for the runner — only AFTER the GO.

## 2. What the one GO does NOT open (fail-closed, journaled NOT_RUN)

- WNBA season ≥2027: governed by the untouched `WNBA-WINPROB-PROSPECTIVE-PREP-V1`
  (9ed717c4, phrase `GO WNBA WINPROB PROSPECTIVE V1 PREDICTIONS` still
  REGISTERED_NOT_CONSUMED). The runner structurally supports 2027 fixtures but
  journals every such match NOT_RUN_FORECAST_GATE_2027 until that separate GO.
- Any match without: valid fixture (true UTC), pre-anchor forecast capacity,
  qualifying pre-anchor quote (soccer: three 1X2 legs from ONE bookmaker and ONE
  snapshot), 1:1 crosswalk, risk-gate headroom. A match whose anchor passed
  before all gates closed is NOT_RUN forever (no backfill).
- Real money, purchases, quota-cap changes, S1, push/merge.

## 3. Production runner (built + verified BEFORE the GO)

`research/papertrade/execute.py` in this cycle's worktree, subcommands:
`plan` (upcoming fixtures + per-match eligibility/deadlines), `forecast`
(engine wiring per league, frozen pins re-hashed at each run start; refuses at/
after anchor; idempotent), `quote` (quota-guarded capture; freshness row law),
`decide` (crosswalk 1:1 → EV → risk gates → in-lock ledger append, statuses
BET_PAPER/NO_EDGE/NO_QUOTE/…/BLOCKED_*), `run-day --date` (full chain),
`dashboard` (rebuild; SANDBOX banner when sandbox genesis), `settle`.
GO gate: `GO_TOKEN.json` (verbatim phrase) AND this cycle's registry phase
containing GO_CONSUMED — single phrase by construction; the retired phrases are
accepted nowhere.

## 4. Pre-GO proof obligations (this round, all must PASS before the packet)

1. End-to-end SUCCESS path on pristine copies: real registry copy + real
   fixture/schedule data, OUTCOME-MASKED, with SYNTHETIC probabilities and
   synthetic odds — full chain forecast→quote→decision→ledger→dashboard into a
   SANDBOX ledger; byte-level repro. No real p, no real odds stored pre-GO.
2. Adversarial battery (extend existing 29-test battery): wrong/missing GO,
   HEAD drift, pin drift, forecast after anchor, odds updated after capture,
   missing odds/draw leg, duplicate match, 21st-bet cap in-lock, quota exhausted,
   key file error, ledger tamper, postpone/cancel refund, idempotent re-run.
3. Independent verifier (fresh context) at the final SHA: confirms the
   executable production runner exists and wires the three leagues, registry
   HEADs match, lock clean, no real paper row pre-GO, single-phrase GO gate.
4. `OWNER_GO_PACKET.md`: the exact ONE phrase, the ONE controller command after
   GO, cadence, per-league NOT_RUN lists + eligibility auto-transition
   conditions, and the explicit statement that GO cannot create rows for matches
   lacking schedule/forecast/odds.

## 5. Boundaries

$0; no purchases; no S1; no push/merge; registry via researchctl CAS; heavy lock
machine-wide; data under `~/.my-quantitative-data/sports-papertrade-exec-v1/`;
all four prior worktrees read-only; key bytes never in chat/log/git. Worktree/
branch: `orca/spt-exec-v1-integration`. Terminal outcomes:
READY_PENDING_ONE_OWNER_GO | BLOCKED_<gate> | NOT_RUN_WNBA2026_ANCHOR_MISSED
(report FAIL/NOT_RUN honestly rather than loosening gates) | TECHABORT_*.
