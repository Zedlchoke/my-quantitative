# PLAN — SPORTS-PAPERTRADE-V1 (virtual paper trading, NBA + WNBA + intl soccer, $0)

- cycle_id: `SPORTS-PAPERTRADE-V1` · asset: shared · budget **0 scored cells by law**
  (paper rows are market-data + journal rows, never scored trials) · registered
  2026-10-07.
- Owner authority 2026-10-07 (this chat, original + AMENDMENT "PAPER TRADE NBA +
  WNBA + SOCCER"): prepare and enter VIRTUAL paper trading — one wallet 1,000.00 USD,
  per-match dashboard, odds-based risk. **No real money. No real bets.** This is
  explicitly NOT a typed GO for capture; paper rows require this cycle's own owner GO
  (below) plus each league's own forecast-gate validity.
- GO phrase (REGISTERED_NOT_CONSUMED, typed ONLY by the owner, verbatim, fresh, at
  this cycle's own gate after reading the A7 verdict):
  **`GO SPORTS PAPERTRADE V1 CAPTURE`**
- Hard boundaries: $0 service cost; no purchases; no S1; no push/merge/rebase; no
  real-money or real-betting action of any kind; no odds proxy (listed decimal odds
  from an authorized snapshot only); API key bytes never in chat/prompt/argv/log/git
  (runtime read of `~/.config/wnba-money-capture/odds_api_key`, mode 0600; only
  `KEY_FINGERPRINT = sha256(key)[:12]` journaled; GEN-1 per
  OWNER_DECISION_CAPTURE_2); **no backfill** — a forecast/quote/decision is valid
  only if recorded strictly before kickoff/tip; played-before-record = NOT_RUN
  forever; missing evidence = NOT_RUN_<reason>, never inferred PASS.

## 1. Per-league forecast authorities (each gate is the owner's alone)

| League | Model (frozen, verbatim, never re-tuned) | Forecast gate (precondition for its paper rows) |
|---|---|---|
| NBA | B1* own-Elo **K=32, HCA=100, γ=0.75**, binary updates; boundary `R←1500+0.75·(R−1500)` — verified from `SELECTION/frozen_specs.json` + `FREEZE_ADDENDUM_20261006` at `.worktrees/nba-winprob-ng-scored-v1/integration/.../NBA-WINPROB-NG-SCORED-V1/` | successor cycle `NBA-WINPROB-PROSPECTIVE-PREP-V1` (registered PLANNED_NOT_STARTED) prepared + its owner GO; until then **NBA paper rows = NOT_RUN_FORECAST_GATE** |
| WNBA | B1-WNBA own-Elo **K=32, HCA=50, γ=0.65** (engine pins 82263eab…/b9446f76…) | `WNBA-WINPROB-PROSPECTIVE-PREP-V1` PRELAUNCH_READY at 9ed717c4, GO `GO WNBA WINPROB PROSPECTIVE V1 PREDICTIONS` unconsumed; 2027 schedule **TBD_PREP NOT PUBLISHED** ⇒ until both, **WNBA rows = NOT_RUN_FORECAST_GATE / NOT_RUN_NO_SCHEDULE** |
| SOCCER | B1 Elo/Davidson **K=48, ν=0.6, HCA=65** (V1 HCA=80 shadow reported, never selectable) — verified from `FREEZE_SCORED.md` at `.worktrees/soccer-intl-winprob-scored-v1/integration/.../SOCCER-INTL-WINPROB-SCORED-V1/` | successor cycle `SOCCER-INTL-WINPROB-PROSPECTIVE-PREP-V1` (registered PLANNED_NOT_STARTED) prepared + its owner GO; fixtures source with true UTC kickoff pinned; until then **SOCCER rows = NOT_RUN_FORECAST_GATE / NOT_RUN_SOURCE** |

- Old OOS verdicts are RESEARCH EVIDENCE, never pre-recorded forecasts. The NBA
  disclosure travels verbatim everywhere NBA numbers appear: **pooled OOS
  F1–F5 2022–2026 LL 0.639953 (n=6,605) and calibration slope 0.8107 (below the
  [0.85, 1.15] secondary band — overconfidence sign); NO recalibration may be fit
  on that viewed OOS.** Soccer held-out 2023+ is PARTIALLY REVEALED (erratum) —
  never called a clean holdout, never used to tune.
- Retro corpora/scored ledgers of all closed cycles stay untouched.

## 2. CAPITAL + STAKE LAW V2 (frozen; ERRATUM_CAPITAL_LAW_V2 supersedes all
earlier capital text)

1. **ONE virtual wallet**: GENESIS equity **1,000.00 USD** across NBA + WNBA +
   SOCCER. No sleeves, no splits, no second wallet. Dashboard reports per-sport
   PnL/risk columns but a single total equity.
2. **Fixed stake exactly 5.00 USD** per valid paper bet. No Kelly sizing, no
   odds/balance/feeling adjustment. Odds and p_model decide BET/NO_BET only.
3. **Open-exposure cap 100.00 USD** = sum of stakes of all unsettled bets across
   the three sports. Checked **immediately before append under the ledger flock**;
   the bet that would exceed cap (the 21st concurrent) is journaled
   **BLOCKED_OPEN_EXPOSURE** — never silently skipped. Postponed/cancelled bets
   stay unsettled (stake still counted) until settled by the frozen settlement law.
4. **Drawdown pause**: total equity drawdown from peak ≥ 10% ⇒ PAUSE_NEW_PAPER_BETS
   (BET attempts journaled BLOCKED_DRAWDOWN_PAUSE; NO_BET journaling continues).
   No wallet reset, no threshold/stake change after any PnL is visible.
5. **One selection max per match**; duplicates refused (BLOCKED_DUPLICATE_SELECTION).
   Only h2h two-way (WNBA/NBA) and 1X2 three-way (SOCCER) on the pinned bookmaker
   snapshot; no parlay/in-play/hedge/other markets.
6. **Settlement law (frozen)**: leg wins ⇒ pnl = +stake×(d−1); loses ⇒ −stake;
   void/push/cancel/postpone-no-reschedule ⇒ refund, pnl 0, stake released.
   equity_after = prev equity + pnl. Integer cents internally; USD 2dp out.
7. **¼-Kelly is a CONTROL INDEX only**: f*=max(0,(p·d−1)/(d−1)), displayed on the
   dashboard; never used to size the ledger stake; no second wallet.

## 3. EV law (frozen signal; disclosed assumptions)

- EV_net per 1 USD stake on the **listed** decimal odds d:
  `EV_net = p_model × d − 1 − c`, with **c = 0.02 frozen friction assumption**
  (slippage/fee buffer; an ASSUMPTION, not a measured cost — labeled as such in
  every disclosure). Market no-vig p is diagnostic only; EV and PnL never use it.
- Proposed signal: **BET iff EV_net ≥ 0.05** (p·d ≥ 1.07) on the chosen leg
  (argmax EV among eligible legs), AND all §2 risk checks pass, AND both the
  forecast and the quote are PIT-valid (forecast recorded at/after its batch time
  and strictly before the league cutoff; quote `fetch_ts < tip − 6h` and
  `source_last_update ≤ fetch_ts`, ERRATUM_CAPTURE_1 E-2 law; league cutoffs bind
  per their own freeze). Every sub-threshold match is still journaled (NO_EDGE,
  with all legs' EV). The 5% buffer is an operational pre-freeze, not an optimum.

## 4. Ledger `sports_papertrade_ledger@1` + dashboard

- Append-only JSONL, hash-chain (`prev_row_sha256`), flock+fsync, GENESIS row
  pinning wallet 1,000.00 USD + plan sha + corpus/snapshot pins + GEN-1
  fingerprint. Row families: GENESIS, MARKET_QUOTE, FORECAST, DECISION
  (statuses: BET_PAPER, NO_EDGE, NO_QUOTE, NO_FORECAST, STALE_PRICE,
  CROSSWALK_MISS, RESOURCE_CONFLICT, QUOTA_SKIP, CANCELLED, BLOCKED_*,
  PIT_VIOLATION_REFUSED), SETTLEMENT. No edits, no deletes, no re-prediction.
- Every universe match gets ≥1 journaled decision row (zero implicit drops).
- Dashboard: internal static HTML + CSV export built from the ledger only —
  per-match rows (league, competition, teams, local + UTC kickoff, status,
  per-outcome p, listed odds per outcome, fair value, no-vig market p, EV,
  stake 5.00/0, decision reason, open/settled, result, PnL, equity after, total
  open exposure), NOT_RUN counters by cause (forecast/odds/source/PIT/GO),
  equity + per-sport PnL + ROI-on-staked + max drawdown, calibration/log
  loss/RPS per league once ≥100 settled (always labeled descriptive; positive
  PnL on few matches is NEVER called edge), ¼-Kelly control index, PAPER-vs-real
  separation is explicit and permanent.

## 5. Gate sequence (this round stops at D)

A. Survey data/rights/coverage/quota (soccer fixtures census on the authorized
   provider incl. which international competitions actually carry 1X2; NBA/WNBA
   sport-key census 0-credit; quota ledger honoring 4 credits/day + 120/month
   standing caps shared across the key) + risk spec + ledger schema + dashboard
   prototype. B. Synthetic + adversarial battery (look-ahead, odds-updated-after-
   capture, missing draw leg, duplicate, postpone, quota guard, 21st-bet cap,
   drawdown pause, missing GO refusal, tamper detection, byte-level repro of the
   decision pipeline) — all green pre-GO on synthetic fixtures only. C.
   Independent verifier (fresh context) at final HEAD: re-measure registry/
   branch/lock, re-run dry-run PASS-path and refusal-path, boundary compliance.
   D. **STOP before owner GO.** E. Missing sources ⇒ per-league NOT_RUN_* stated,
   never fabricated rows.

## 6. Artifacts + lanes

Control: `research/control/SPORTS-PAPERTRADE-V1/` (ERRATUM_CAPITAL_LAW_V2.md,
RISK_SPEC, LEDGER_SCHEMA, census artifacts, handoffs/). Code:
`research/papertrade/` (ledger, risk, odds_client, engine adapters, dashboard)
+ `tests/papertrade/` in the integration worktree. Lanes: controller builds core
in the integration worktree; survey lanes (soccer census, NBA bind) and the
independent verifier run as separate fresh-context agents writing
`zcode_orch_v3_handoff@1` JSONs at their handoff_paths. Data outside git under
`~/.my-quantitative-data/sports-papertrade-v1/`. Terminal outcomes
(negative-first): PRELAUNCH_READY_PENDING_OWNER_GO | PRELAUNCH_BLOCKED_<gate> |
NOT_RUN_ODDS_SOURCE | NOT_RUN_NETWORK | NOT_RUN_RESOURCE_CONFLICT | TECHABORT_*.
The GO phrase is the owner's alone; an early or paraphrased GO dies unconsumed.
