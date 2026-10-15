# SPORTS PREP ROUND — 2026-10-15 (owner instruction round; PREP ONLY; freeze/decision packet)

Round authority: owner instruction 2026-10-15 (this chat). Scope: one PREP
round covering (a) a new NWSL lane and (b) forecast-quality improvement
investigation for NBA, WNBA, WSL, men's internationals, NFL. Hard stop:
**this packet** — no new scored OOS, no model or paper-decision changes to
anything running, no paper-ledger writes, no GO, no purchases, no real bets,
no push/merge. Successors open only after owner review of this packet.

State at round open (measured 2026-10-15, root checkout main
`60c19649f43416c89065426fda295e89ae8128fe`): heavy lock FREE_PROVEN; registry
coherent (doctor: only LOW/MEDIUM legacy-worktree findings); paper ledger
`~/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl`
= 24 rows chain OK, equity 102,215c ($1,022.15), BET_PAPER rows: WNBA ×2
(v2 stake 500c), WSL ×3 incl. FD-2026-M37 at 1,022c (v3 1% law live); NBA has
no decision rows (forecast gate unmet). New cycle registered this round:
**NWSL-WINPROB-PREP-V1** (ACTIVE_LIGHT, budget 0/0, no GO phrase — see
`plans/PLAN_nwsl_winprob_prep_v1.md` + `research/control/NWSL-WINPROB-PREP-V1/`).

## 0. Global exposure law for this round (binding on every league)

The 2026-10-14 four-league odds diagnostic
(`~/.my-quantitative-data/four-league-odds-diagnostic-20261014/`, 100 fixed
games × NBA/WNBA/WSL/soccer-men; seed 20261014) is **POST-HOC EXPOSED
DESCRIPTOR** for all four leagues: 293/400 rows carry archived prices, all
`B_ARCHIVE_NO_QUOTE_TIMESTAMP`; the full paper gate admits **0/400**; the
"206 matches EV≥5%" figure (WNBA 67 + NBA 61 + soccer 78) is arithmetic on
untradable archive prices — **never OOS evidence, never a money backtest, never
a tuning surface**. WSL row: 0/100 matched odds (`NOT_RUN_ODDS`). Soccer rows
needed Home/Away orientation repair on a secondary archive with no price
timestamps. No EV, calibration or selection claim in this packet reads those
bytes except as labeled burned context.

Metrics law (all leagues, all future cycles): report log loss (primary),
Brier/RPS, per-bin calibration + slope (band [0.85, 1.15]), sharpness
(mean max-probability), match counts and per-season uncertainty
(date-cluster bootstrap); **never rank a two-way league's LL against a
three-way league's LL** — formats differ, numbers are not comparable.

Forecast-vs-profit separation law: "better forecast" (LL/RPS/calibration vs
the immutable baseline and, where PIT odds exist, vs de-vig market) is
evaluated on TRAIN/selection-legal windows; "bettable edge" additionally
requires timestamped pre-anchor quotes, correct payout law, executable price,
depth walk, fees, quota — i.e. the full capital-v3 paper gate. Absent any
element ⇒ `NOT_RUN_*`, never arithmetic substitutes.

---

## 1. NBA

| Item | State (measured) |
|---|---|
| Baseline running | **B1\*** own-Elo K=32/HCA=100/γ=0.75, constants FROZEN forever (NBA-WINPROB-NG-SCORED-V1 TERMINAL). **H-CAL1** p′=σ(0.71·logit p) dual-recording prospectively (NBA-WINPROB-HCAL1-PROSPECTIVE-PREP-V1, OPERATIONAL_GO_CONSUMED_RECORDING_R3_HARDENED). Paper rows: blocked (`NOT_RUN_FORECAST_GATE`) until `GO NBA WINPROB PROSPECTIVE V1 PREDICTIONS` (REGISTERED_NOT_CONSUMED) |
| Exposed data | warm-up 2016–17; SEL 2018–2021 consumed (c=0.71 selected there); **2022–2026 RETROSPECTIVE_DIAGNOSTIC_EXPOSED** (B1* pooled F1–F5 LL 0.639953 n=6,605, slope 0.8107; H-CAL1 LL 0.630650); player-feature arms selection-negative (NBA-PLAYERFEAT-SCORED-V1: all 3 PF arms fail train-internal G-ENTRY); 100 fixed 2023-24 games with archive prices (burned, §0) |
| Clean window | **2026–27 season onward only** (fresh = prospective pre-tip forecasts) |
| Timestamped odds | None qualified at $0: archive prices Class C (no timestamps); PM watcher scanned NBA 1,214 events 2026-10-10 → all `NOT_RUN_NO_MARKET`; The Odds API = paid history ⇒ market-comparison and EV lanes `NOT_RUN_ODDS` |
| Data rights | hoopR CC BY 4.0 + MIT attribution; ESPN schedules $0 no-auth (ng-prep pins) |
| Blockers | c re-selection on 2022–26 is BANNED (exposed); H-CAL1 must not enter paper decisions without its own owner gate; calibration-slope shortfall (0.8107) is a recorded sign, not a retuning invitation |

**Hypotheses (for the next registered round, not run here).**
- *H-NBA-IMP (improvement, mechanism-first)*: schedule-context mechanism
  (rest days / back-to-back / travel) as an additive argument layer to the
  frozen B1* engine, selected ONLY on TRAIN 2018–2021 under a second-use
  disclosure (that window is c-consumed; everything computed there is
  `TRAIN_INTERNAL_DIAGNOSTIC_SECOND_USE`, never OOS). Dead-arm veto carried:
  additive-feature layers failed as player features; the schedule mechanism
  is a different information source but inherits the veto list's
  no-regrid-on-2009-2015 and no-market-features laws.
- *H-NBA-NULL (null)*: designed placebo — the same schedule features
  date-shuffled within game-day batches must produce ΔLL CI including 0
  against B1*; and c=1 identity ≡ B1* bit-for-bit (standing control).
- *Lineup/injury family*: opens only behind a PIT gate (archived pre-tip
  timestamps from bytes); default expectation `NOT_RUN_PIT` — no timestamped
  historical lineup archive identified at $0.
- Arbiter: any surviving spec goes to a 2026–27 prospective dual-recording
  arm (H-CAL1 pattern: own cycle, own GO, KEEP_B1STAR default), never into
  the running paper chain by injection.

**Verdict: KEEP** B1* + H-CAL1 recording (frozen controls). **TUNE_CANDIDATE**
(schedule-context spec, second-use labeled; lineup family PIT-gated).
**NOT_RUN**: odds/market comparison at $0; c re-selection on exposed windows.

---

## 2. WNBA

| Item | State (measured) |
|---|---|
| Baseline running | **B1-WNBA** own-Elo K=32/HCA=50/γ=0.65 — pooled OOS 2020–2026 LL 0.611603, n=1,773 (TERMINAL WNBA-PLAYERFEAT-SCORED-V1; B0 floor 0.603755). IMPROVE-PREP closed **LOCKED_KEEP_B1** (H-EFF points variant ΔLL +0.001240 CI incl 0 → worse; H-SCHED +0.000515 CI incl 0; H-STATUS `NOT_RUN_PIT`). Paper: 16 ledger rows, 2 BET_PAPER (v2 stake) |
| Exposed data | seasons 2020–2026 + every prior trial (AMD1 23/24 + IMPROVE 10/24 diagnostics — all CIs incl 0); **odds sets burned: 200 fixed retro (2026-10-09) + 150 manual-odds (2026-10-09) + 100 four-league 2024 games (2026-10-14)** — per owner law: never a tuning input |
| Clean window | **2027 season**, prospective, after (i) 2027 schedule publication (currently `NOT_RUN_NO_SCHEDULE`) and (ii) the successor's own GO (`GO WNBA WINPROB PROSPECTIVE V1 PREDICTIONS` REGISTERED_NOT_CONSUMED; 2026-remainder GO packet also pending owner) |
| Timestamped odds | `NOT_RUN_ODDS` at $0 (0 valid game-quotes; no Class-A source). Only rights-clean PIT candidate: The Odds API `basketball_wnba` h2h **paid** (history starts 2022-05; 2020–21 unpurchasable there; est. $8.05 one-pass inside a $30/20K month). PM: 11 events scanned, `NOT_RUN_NO_MARKET` (2026-10-10) |
| Data rights | ESPN schedules/boxscores $0 no-auth (ESPN channel class); release store 2025–2026 present, 2002–2024 pulled in IMPROVE-PREP with provenance |
| Blockers | odds funding decision (D1 fund / D2 Betfair probe / D3 sales) pending since WNBA-ODDS-DISCOVERY; 2027 schedule unpublished |

**Hypotheses.**
- *H-WNBA-SLICE (improvement, diagnostic-first)*: season-start block (first
  k games per team-season) and playoff rounds as separate calibration strata
  vs the frozen B1 — mechanism: offseason roster churn + playoff intensity
  shift Elo levels. Honest selection window: evaluation seasons **≤ 2019
  only** (lock rule carried verbatim from IMPROVE-PREP; 2020–2026 never an
  input). If ≤2019 MIN_VALID cannot be met ⇒ `NOT_RUN_INSUFFICIENT_DATA`
  (honest stop, nothing scored).
- *H-WNBA-NULL*: within-season epoch-relabeled placebo (same feature rows,
  shuffled stratum labels) must give ΔLL CI incl 0; B1-verbatim replay parity
  1,773/1,773 bit-exact as standing control.
- *Model–market divergence*: reported ONLY as a `CLASS_C_ARCHIVE_DESCRIPTOR`
  on the burned sets (disagreement rates, no EV, no tuning); a real
  model-vs-market arm requires the owner odds-funding decision first.
- Arbiter: any locked spec reaches WNBA-WINPROB-PROSPECTIVE-PREP-V1 released
  slots 3–9 ONLY via owner-authorized amendment to that cycle; confirmation =
  prospective 2027+ forecasts paired vs B1 under the successor's own GO.

**Verdict: KEEP** B1. **TUNE_CANDIDATE** (H-WNBA-SLICE on ≤2019 window).
**HOLD**: 2026-remainder + 2027 prospective GO packets (owner timing).
**NOT_RUN**: any tuning on the 350 burned odds games; odds lanes at $0.

---

## 3. WSL (women's England)

| Item | State (measured) |
|---|---|
| Baseline running | **B1 = B2** Elo/Davidson K=24/ν=0.55/HCA=40 — chrono scored OOS 2023-24+2024-25 n=263: LL 0.848764126, RPS 0.170647469, Brier 0.163670509, argmax 0.6084 (WSL-WINPROB-SCORED-PREP-V1, budget 3/3, repro twin ALL_MATCH, A7 from-scratch byte-exact). Paper: **BET_PAPER live** (v3 stake; first landed row FD-2026-M37 1,022c; 0 open PM pairings at 2026-10-10 scan → most fixtures journal `NOT_RUN_NO_MARKET`) |
| Exposed data (owner-required disclosure) | **OOS 2023-24 + 2024-25 is PARTIALLY EXPOSED, never "clean"**: standings/match-counts read on every season 2011–2024/25; B0-fit level on 2020-21..2023-24 train seasons; 2024-25 was DISCOVERY's descriptive "held-out". 100 fixed 2023-25 games found NO qualified odds (0/100) |
| Clean window | **2025-26 onward** fixtures via the live BET_PAPER forecast stream (pre-kick, shared ledger) — the only fresh-evidence surface |
| Timestamped odds | PM three-YES per event with **90-minute verbatim resolution rules** (the qualified WSL lane source; snapshot law: fetched strictly pre-anchor, append-only); historical PM depth + The Odds API WSL history = unpaid ⇒ `NOT_RUN_ODDS` historical stands |
| Data rights | ewf-database git HEAD ffd15562 (CC BY-SA 4.0 verified verbatim; internal research unencumbered); kickoff/venue absent ⇒ date-granular laws |
| Blockers | PM per-fixture market availability is fail-closed (`NOT_RUN_NO_MARKET`); OOS window spent (one scored pass consumed) |

**Hypotheses.**
- *H-WSL-DRAWCAL (improvement)* — **B1R-WSL**: a WSL-specific frozen draw
  recalibration map (PAV isotonic on p_D, H/A renormalized — the exact B1R
  transform law) **fit on warmup seasons 2011–2018/19 ONLY** (by scored-prep
  law those seasons are ratings-only, never scored, never grid-consumed),
  holdout = train-internal 2019-20..2022-23 reported with a second-use label
  (that window selected K/ν/HCA, not a draw map — still labeled, still not
  OOS), final arbiter = pre-registered prospective decision on the 2025-26+
  BET_PAPER forecast stream (mirroring DRAW_CAL_HYPOTHESIS n=1,000 logic;
  thresholds frozen before the first prospective draw row). Men's parameters
  and the men's B1R map are EXCLUDED by law — WSL draws ≈17% share; the map
  must be WSL-fitted with MIN_VALID laws.
- *H-WSL-NULL*: identity map (p_D′=p_D) ≡ B1 bit-for-bit; placebo map fit on
  within-season score-shuffled draws must NOT beat identity on the holdout
  (CI discipline).
- *Three-way calibration audit* (owner ask): decile reliability for H/D/A
  separately, draw slope emphasized, on the partially-exposed 263-row OOS —
  reported as `PARTIALLY_EXPOSED_DESCRIPTOR`, never as tuning evidence.

**Verdict: KEEP** B1=B2 scored control. **TUNE_CANDIDATE** (B1R-WSL map, warmup
fit + prospective arbiter). **NOT_RUN**: historical odds; any use of 2023-25
as a fresh holdout (owner language: old OOS partially exposed — restated).

---

## 4. Soccer men's internationals

| Item | State (measured) |
|---|---|
| Baseline running | **B1** Elo/Davidson K=48/ν=0.6/HCA=65 — chrono OOS [2001,2023) n=20,708: B0 1.049906 / **B1 0.912037** / V1 0.909325 (TERMINAL, closed history). **B1R** (frozen draw map: PAV isotonic 18 pools, fit [1971,1991) n=9,289, zero post-2001 contact) is the LIVE paper decision model since 2026-10-10 (`B1R_SWITCH_LIVE`, first row dadbec71); WC/Euro groups integrated config-only |
| Exposed data | OOS [2001,2023) fully scored; heldout 2023+ PARTIALLY REVEALED (n=3,737/arm mechanically recorded — erratum; never a clean holdout); **DIAG441** retrospective subset consumed (441 WC/Euro 90-min-resolvable rows; 20 label flips; ALL_441 B1 ΔLL +0.025455 — closed verdicts untouched); 100 fixed WC/Euro 2002-22 archive-odds games (burned, §0) |
| Clean window | fixtures **not yet played** (post-2026-10-15: Nations League 2026-27 etc.), forecasted pre-kick by the live paper cadence; pre-registered draw arbiter = prospective n=1,000 decision (DRAW_CAL_HYPOTHESIS, running) |
| Timestamped odds | `$0-qualified sources today: ZERO` (documented zero, SOCCER-1X2-SOURCE-PREP). PM UNL scan: 2 events, `NOT_RUN_NO_MARKET` (2026-10-10). The Odds API = B-potential but NT 1X2 presence `NOT_RUN_ODDS_UNVERIFIED` + paid history |
| 90-minute target law | corpus target = recorded 90/120 score with shootout winners never modifying target; corpus H/A rows are 90-min UNDERDETERMINED (`NOT_RUN_TARGET_NO_ET_FLAG`); OPENFOOTBALL (CC0) is the only Class-A resolver — 441/1,425 ambiguous rows resolved (421 confirm / 20 flip / 2 blocked); **knockout stays BLOCKED/NOT_RUN for paper until BOTH target and market settlement are proven 90-minute** |
| Data rights | martj42 corpus CC0-1.0 (sha df35268f unchanged since DISCOVERY) |
| Blockers | 90-min ET resolution for future knockouts unresolved (SOCCER-INTL-90MIN: token ladder 0/984, no blind purchase recommended); no $0 odds source |

**Hypotheses.**
- *H-SOCCER-IMP (improvement, candidate for a future registered cycle)*:
  confederation-structure mechanism (e.g., inter-confederation strength
  differential as a 3-way intercept), selected train-internal on [1951,2001)
  with MIN_VALID + second-use disclosure (that region selected B1's grid and
  V1's HCA; B1R's map sits at [1971,1991) — an H-SOCCER-IMP spec must not
  re-select ν or the draw map). Forbidden selection surfaces: OOS [2001,2023),
  DIAG441, B1R holdout [1991,2001), heldout 2023+.
- *H-SOCCER-NULL*: all-confederation-coefficients-equal ≡ B1 bit-for-bit;
  B1R-vs-identity on the prospective stream is the standing null/arbiter pair
  (already pre-registered — this round changes nothing about it).
- *Draw calibration per owner ask*: audit B1's draw calibration on TRAIN-legal
  windows ([1951,2001), labeled) + restate B1R map law; no new draw parameter
  selection anywhere.

**Verdict: KEEP** B1/B1R live + prospective n=1,000 arbiter. **TUNE_CANDIDATE**
(H-SOCCER-IMP, own future cycle, second-use labeled). **NOT_RUN**: knockout
paper without 90-min law on both sides; parameter selection on any exposed
window; odds lanes at $0.

---

## 5. NFL

| Item | State (measured) |
|---|---|
| Baseline running | **NG prospective 2026 LIVE** (NFL-WINPROB-NG-SCORED-V1): weeks 5+6+7 landed immutable (129 rows, chain 67e89b2e; no re-forecast ever); cadence gate-first 6–72h window, automation DAILY 17:00Z; **next eligible fire 2026-10-27T17:00Z** (week 8 opener 2026-10-30T00:15Z); budget 0/9. Arms of record: B0 constant 0.571399049390; **B1_STAR** K=40/HCA=0/γ=2/3 (anchor 0.6407092590929282, predecessor E1 base-10); E2 NG-machine diagnostic 0.6505203624255933 (base-e link — a DIFFERENT measurement) |
| Selection-negative + machinery record (owner ask #10) | **P2-RESELECT round-2 2026-10-09: owner accepted the negative** — `OWNER_ACCEPTED_NEGATIVE_C3_FINAL_NOT_RUN_SELECTION_NEGATIVE` (no finer grid on old data; scored B0+B1* pass of that round NOT run; GO stays REGISTERED_NOT_CONSUMED). Machinery divergence documented and audited (MACHREM chain): base-10 predecessor link `1/(1+10^(−(R_home+HCA−R_away)/400))` vs base-e NG link `sig((R_own−R_opp)/400)` (effective divisor ≈173.72) — estimand separation E1/E2/E3, never compared as one measurement; WALKFWD halted at REPLAY_CONSISTENCY by design (spec-level divergence, nothing published); **MACHREM sits at `OWNER_DECISION_PENDING_C3_TRANSFER_CONFOUND`** |
| Exposed data | 2000–2018 TRAIN_INTERNAL (both programs' selection territory); 2019–2025 RETROSPECTIVE_WALK_FORWARD (spent; outcomes observed; C3 virgin only w.r.t. NG selection — still never fresh evidence) |
| Clean window | **2026+ prospective, owned exclusively by the live NG cycle** (read-only to everything else) |
| Timestamped odds | none anywhere in the NFL program (odds columns quarantined at load by law); no NFL odds source surveyed/authorized to date |
| Blockers | any new C3 proposal is BLOCKED until the owner resolves the MACHREM decision packet; θ rescue from 2019–25 is banned |

**Hypotheses.**
- *H-NFL-IMP*: **none proposed this round** — per owner law, a new C3 (or any
  successor arm) is prepared only after the MACHREM decision lands, as a new
  registered round with its own gates; if approved later, it re-runs the
  IDENTICAL θ grid under the base-10 machinery of record, freeze-before-read
  (the P2 protocol stands ready), and its arbiter is the live 2026+ ledger,
  never 2019–25.
- *H-NFL-NULL*: designed null θ=0 ≡ B1* bit-for-bit (twice-proven; re-asserted
  in any successor); C3_TWIN shuffled-z remains the machinery-suspect canary.

**Verdict: HOLD** all NFL tuning (owner decision pending). **KEEP** NG
prospective 2026 untouched — cadence, ledger, executor byte-unchanged; next
fire 2026-10-27. **NOT_RUN**: θ rescue on exposed seasons; NFL odds lane
(not opened this round; opening one = owner decision).

---

## 6. NWSL (new lane)

Registered this round: **NWSL-WINPROB-PREP-V1** (ACTIVE_LIGHT, 0/0, no GO
phrase). Full source survey with byte pins:
`research/control/NWSL-WINPROB-PREP-V1/SURVEY_20261015.md`. Summary:

| Item | State |
|---|---|
| Fixtures/results/venue/kickoff-UTC | ESPN `usa.nwsl` scoreboard — LIVE 2026 (season 14024), 2016 depth byte-proven (fresh fetch = DISCOVERY pin sha 726dde33…, cross-cycle reproduction); est ≈530 dated requests to harvest; rendered ToU pin owed before bulk |
| Results depth + playoff ET flag | nwslR/nwsldata `matches.csv`: 1,170 matches 2016–2024 with stadium/city + **penalty scores + won_on_penalties** — but STALE after 2024-06 (2025–26 gap). SoccerStatsUS/nwsl_data (CC BY 4.0, fresh 2026-10-02) = backfill candidate, parser owed |
| Odds 1X2 | PM Gamma: three YES/NO markets per match event, **draw = 90 min + stoppage verbatim (pinned)**; 2026 events observed; pre-2026 census + CLOB price-history PIT grade = lane work. ESPN odds null. The Odds API page 404 at guessed slug; keyed enumeration + paid history ⇒ `CANDIDATE_NOT_AUTHORIZED` |
| Lineups/injuries | `NOT_RUN_PIT` default (no timestamped archive identified at $0) |
| Exposure | **No NWSL window is exposed** — nothing has ever been computed on NWSL outcomes; selection must stay on declared train seasons frozen before any OOS choice |
| Baselines (next round) | B0-NWSL constant 3-way; B1-NWSL Elo/Davidson (NWSL-fitted only; men's/other-league parameters EXCLUDED by law); MKT-NWSL de-vig market arm where pre-anchor PM snapshots exist; designed nulls as controls |
| Join law | date + team-pair crosswalk with kickoff-UTC consistency bound; expansion/relocation crosswalk audit (FC Kansas City → Utah Royals → Current; WNY Flash → NC Courage; 2026 Boston Legacy FC) with measured join rates; playoff-row marker law audited (nwslR penalty fields × ESPN season-type), never asserted |
| Costs/blockers | $0 everywhere; ESPN ToU pin; PM census; paid sources out of scope absent owner decision; NWSL paper hookup = separate owner decision + separate gate |

**Verdict: TUNE_CANDIDATE-by-construction** (greenfield: baselines first,
improvement hypotheses only after B0/B1 exist). **NOT_RUN** today: odds
history pre-2026, lineups PIT, official-site bulk, paper hookup.

---

## 7. Independent verifier plan (for every successor this packet proposes)

Fresh-context verifier (A7 pattern; writes audit namespace only, never
repairs), must re-derive from bytes:
1. **Data**: re-fetch ≥ the pinned samples (ESPN 2016 expected byte-stable —
   cross-cycle reproduction demonstrated 2026-10-15), re-hash corpora, re-run
   join-rate and coverage censuses, re-verify licenses at the pinned SHAs.
2. **Samples/arms**: parity anchors (B1-verbatim replays bit-exact per league:
   WNBA 1,773/1,773; NBA 6,605/6,605 precedent; WSL from-scratch
   reimplementation; soccer 36/36 EXACT reproduction-gate precedent), designed
   nulls bit-for-bit, twins deterministic.
3. **Metrics**: recompute LL/Brier/RPS/bins/slope/CI from prediction ledgers;
   verify denominators and per-season counts; verify NO two-way-vs-three-way
   LL comparison exists anywhere in artifacts.
4. **Trial budget**: selection ledgers arithmetic + caps; every refused case
   recorded (no silent retries).
5. **Lookahead/PIT refusal battery** (must all refuse): quote/snapshot
   `fetch_ts ≥ anchor` → refuse; `line_update > snapshot_time` → refuse;
   stale snapshot → refuse; missing draw leg on a 3-way market → refuse;
   played-before-record forecast → refuse; `B_ARCHIVE_NO_QUOTE_TIMESTAMP`
   rows entering any EV claim → refuse; late-arriving stats touching earlier
   forecasts (mutation probe) → refuse; knockout without proven 90-minute law
   on both target and market sides → refuse.
6. **Boundary compliance**: $0 unless an owner decision says otherwise; no GO
   typed by agents; other cycles' bytes untouched (NFL NG cadence, WSL/soccer
   BET_PAPER lanes, NBA H-CAL1 recorder); registry coherent.

## 8. Verdict table (this round)

| League | Baseline of record | KEEP | TUNE_CANDIDATE | HOLD | NOT_RUN |
|---|---|---|---|---|---|
| NBA | B1* (frozen) + H-CAL1 recording | B1*, H-CAL1 c=0.71 | schedule-context spec (second-use, TRAIN-labeled; 2026–27 dual-recording arbiter) | paper gate (owner GO) | odds/market at $0; c re-selection on 2022–26 |
| WNBA | B1-WNBA 0.611603 | B1 | H-WNBA-SLICE (≤2019 window only) | 2026-remainder + 2027 GO packets | tuning on the 350 burned odds games; odds at $0 |
| WSL | B1=B2 0.848764 (n=263, partially-exposed OOS) | B1=B2 | B1R-WSL draw map (warmup fit; BET_PAPER stream arbiter) | — | historical odds; reusing 2023-25 as fresh holdout |
| Soccer men | B1 0.912037 + B1R live | B1, B1R, prospective n=1,000 arbiter | H-SOCCER-IMP (own future cycle; [1951,2001) second-use) | — | knockout without 90-min law; selection on OOS/DIAG441/[1991,2001)/2023+ |
| NFL | B1_STAR anchor 0.6407 (E1) + NG 2026 live | NG prospective 2026 (untouched; next fire 2026-10-27) | — (blocked) | ALL C3 successors → MACHREM owner decision | θ rescue on 2019–25; NFL odds lane |
| NWSL | none yet (greenfield) | — | everything-by-construction (baselines first) | lanes pending owner review of this packet | odds history pre-2026; lineups PIT; official bulk; paper hookup |

## 9. Owner decision requests (fail-closed defaults if unanswered)

1. **NWSL**: authorize dispatch of NWSL-WINPROB-PREP-V1 lanes (ESPN ToU pin +
   ≈530-request harvest; nwslR/SoccerStatsUS cross-check; PM NWSL census +
   snapshot pilot — all $0). Default if unanswered: lanes stay undispatched.
2. **NFL**: resolve the pending MACHREM `OWNER_DECISION_PENDING_C3_TRANSFER_
   CONFOUND` decision packet (C3 transfer confound) — this gates ALL new NFL
   arms. Default: HOLD stands; NG 2026 cadence continues.
3. **WNBA**: (a) odds funding D1 (~$8 one-pass / $30 month) vs D2 Betfair
   probe vs D3 sales inquiries; (b) timing for the 2026-remainder GO and the
   2027 prospective TBD_PREP. Default: `NOT_RUN_ODDS` + packets stay pending.
4. **NBA**: optional authorization of the schedule-context diagnostic cycle
   (TRAIN-second-use labels only). Default: not opened. NBA paper GO remains
   at its own gate.
5. **WSL / Soccer**: optional authorization of B1R-WSL candidate cycle and
   H-SOCCER-IMP candidate cycle as next registered rounds. Default: not
   opened; live BET_PAPER lanes continue under current law.
6. **Global**: confirm the four-league odds diagnostic (400 games / 206 EV5
   arithmetic rows) stays a burned descriptor — no successor may read it as
   evidence, tuning input, or money backtest. Default: burned, as written.

— End of packet. Nothing scored, nothing prospective, no ledger writes, no GO,
no push/merge. Registry delta: +NWSL-WINPROB-PREP-V1 (ACTIVE_LIGHT 0/0, no GO
phrase); plan `plans/PLAN_nwsl_winprob_prep_v1.md`; survey artifacts under
`research/control/NWSL-WINPROB-PREP-V1/`.
