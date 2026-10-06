# HYPOTHESES_COMM_EN_R3 — round-3 outcome-blind hypothesis continuation, lane COMM-EN (CL + NG)

- Task: **FUTURES-TEN-HYPO-PREP-20261004**, lane **COMM-EN**. Generated
  2026-10-04 UTC. Worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/futures-ten-hypo/prep` @
  HEAD **`a4a882658e09092b5b282b666b30a3cfc5ac3418`** (the one permitted
  `git rev-parse HEAD`; == dispatch base_sha), branch
  `prep/futures-ten-hypo-20261004`.
- Class: PREP hypothesis dossier. **0 PnL, 0 returns, 0 scored runs, 0
  sweeps, 0 selection by any return statistic.** Every parameter
  **[PROVISIONAL]**. Outcome-blind throughout; missing evidence is
  **NOT_RUN**, never PASS. NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER stands;
  no cycle registration, no trial creation.
- Standing rulings inherited, none reopened: CL/NG have **NO vendor O1M
  panel ⇒ every scored status is NOT_RUN_DATA_ABSENT**; NOT_QUALIFIED_V2
  stands (baseline verdict (a)); root IBKR corpus verdict (b) =
  SIGNAL PASS / DAILY_BT BLOCKED / INTRADAY_BT BLOCKED (root main
  d8cf8eca300d9eadc703f0d99629bec79102b325); fees MODELED /
  VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW; BBO NOT_RUN; 6F out of scope;
  D1–D12 all open; P3 quarantine absolute (`.worktrees/futures-behavior/
  prep` never accessed; baseline hash rows 01–09 re-verified via the
  committed copies in THIS worktree); COMMODITIES 54 > 24 ⇒
  BLOCKED_TRIAL_BUDGET on any single-cycle attempt.
- **Field format**: 11 numbered fields per baseline convention (R2 quality
  bar), **+ field 12 DATA REQUIREMENTS** — mandatory for every family below
  because both are classified **DATA-BLOCKED**.
- Taxonomy: **FACT** (primary source + access date, capture hashed) /
  **OBSERVED** (artifact + file:field) / **MECHANISM_HYPOTHESIS**
  (unmeasured causal story) / **INFERENCE** / **DERIVED** / **NOT_RUN** /
  **NOT_OBTAINED**. Forbidden words: "measured cost", "complete cost",
  any "edge" claim.
- Sources this lane: 20 fetch attempts — 10× HTTP 200 rows (8 capture files
  saved; 2 no-content probes), 6× 404, 4× 403 — all logged
  `fetch_log.jsonl`; captures hashed `SHA256SUMS_lane.txt` (this directory);
  baseline 24-row hash re-verification 24/24 OK before any fetch.

---

## 0. Evidence base consumed before writing (read-only)

1. Baseline families & census:
   `research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/comm/`
   COMM_HYPOTHESES.md (§0 standing context, §1 NG, §2 CL, §5–§7),
   RANKING_INPUT.md (3-axis rubric + 54>24 census), captures/
   source_sha256.tsv (24 rows, all re-verified this lane).
2. Format exemplar: `research/control/FUTURES-SIX-ADOPT-PREP-20261004/hypo/
   HYPOTHESES_R2.md` (11-field convention + veto/ancestry/budget sections).
3. Root READ-ONLY data authority: `research/control/FUTURES-DATA-10SYMS-V1/`
   FINAL_REPORT.md, S6_FRONT_SPREADS.json, S7_DEPTH_ACTIVE.json,
   costs/IBKR_futures_commissions_2026-10-02.json,
   costs/SPECS_MARGINS_PUBLIC_2026-10-02.md (@ root main d8cf8eca).
4. Dead inventory: `research/wayfinder/FAMILY_FAILURES.jsonl` — **all 173
   entries scanned this lane**; the 3 commodities rows (106–108) are
   COMMODITIES-NG1 CoT positioning, plus adjacency rows 58/60/61/62/81/82/91/
   93/172 read in full where load-bearing; ledger row COMMODITIES-NG1 in
   `research/wayfinder/HYPOTHESIS_LEDGER.md` line 233.
5. Ranking rubric: `hypo/cross/RANKING_FRAMEWORK.md` (D1–D5 anchors).
6. Round dispatch: `research/control/FUTURES-TEN-HYPO-PREP-20261004/dispatch/
   DISPATCH_MANIFEST.json`.
7. New primary-source captures this lane (all in `captures/`, sha256 in
   `SHA256SUMS_lane.txt` (comm_energy/)): EIA WPSR + WNGSR release schedules, CFTC COT
   release schedule, EIA STEO main page (release/forecast-completed stamps),
   NOAA CPC 6-10day page (issuance-time law), EIA dnav NG-futures page
   (futures-pricing dead after 2024-04-05), EIA dnav WTI spot page,
   opec.org homepage (dated JMMC items), web.archive.org CME CL page
   (JS-rendered — BLOCKED_CONTENT).

---

## 1. Search result and closure

**2 NEW families are proposed** (target ≤3 honored; quality over quantity),
**4 carried families + 2 construction laws restated** in CARRIED_STATUS.md
(0 new identities), and **6 candidates are VETOED/REJECTED**, each with its
wall cited (§4). Both new families are **DATA-BLOCKED** — they exist as
mechanism + falsification designs + exact data requirements only.

The honest search accounting: the dispatch's five design spaces adjudicated
as — OPEC+ flow ⇒ **NEW (CL-F3)**; CFTC COT extremes ⇒ **VETO (ancestry,
strongest wall in the program for commodities)**; EIA STEO revisions ⇒
**NEW (CLNG-F4)**; NG option-expiry × storage timing ⇒ **REJECT
(construction-adjacent + intraday data-absence)**; Cushing-basis spread ⇒
**REJECT (standing-law + PIT wall)**. Two further space-closures (API prints,
overnight gap) documented in §4.

---

## 2. CL-F3 `OPEC-DEC-FLOW` — scheduled OPEC+ production-decision flow (CL leg only)

**Type: NEW, DATA-BLOCKED (scored status NOT_RUN_DATA_ABSENT).** Event
family; CL leg only (NG has no OPEC analog — Henry Hub is a North-American
regulated-flow market; declared non-leg, not an omission).

1. **Mechanism + microstructure** [MECHANISM_HYPOTHESIS]. **Who is
   forced/slow**: OPEC+ (Declaration-of-Cooperation) ministerial and JMMC
   (and eight-country voluntary-group) meetings publish production-target
   decisions on a pre-announced meeting calendar; physical traders, refiners
   and index/CTA flow must reprice the expected forward supply path at the
   announcement, while discretionary paper positions in CL adjust over
   subsequent sessions. **Why an effect may exist**: a dated supply-policy
   decision changes the market's balance expectation discontinuously; where
   the decision deviates from the prior-meeting trajectory (a real change vs
   a carry-over confirmation), the front CL contract must absorb the
   repricing. **Two competing arms**: arm **A1 DEC-CONT** —
   decision-content continuation (a change-decision moves front CL in the
   supply direction — bullish for cuts/extends, bearish for quota
   increases — with drift persisting days); arm **A2 PRICED-IN** — delegate
   press/leak flow pre-positions the market, so the post-announcement window
   carries nothing conditional on the decision (or reverses the leak move).
   **Measured anatomy being conditioned on**: NONE yet on-symbol — the
   meeting-event series is not built (NOT_RUN); the only adjacent anatomy is
   the corpus weekday/schedule-level material inherited from the baseline
   (CL_DOSSIER §3), which is NOT family-linked. This is the weakest evidence
   posture a NEW family may have — declared, not hidden.
2. **Expected direction, falsifiable** [PROVISIONAL, no PnL claim]:
   A1 — E[CL daily return over the 1–3 sessions after a CHANGE-decision
   meeting] has the sign of the supply-direction convention (cut/extend ⇒
   positive), and exceeds the same clock on CONFIRM/roll-over meetings and
   on the weekday-matched placebo; A2 — the change-vs-confirm contrast is ≈
   zero (decision content adds nothing beyond the meeting clock). The
   change/confirm SPLIT is part of the falsifiable claim, pre-registered
   before any math.
3. **PIT feature availability**: meeting dates + decision text are
   as-published opec.org press items — **the homepage renders and carries
   dated meeting items verbatim** ("67th Meeting of the Joint Ministerial
   Monitoring Committee 2 August 2026") [FACT, captures/opec_home.html,
   sha256 4499580f…, fetched 2026-10-04]; the dedicated calendar path
   `/meetings.html` is **BLOCKED_HTTP_403** [OBSERVED, fetch_log seq 12] and
   **web.archive.org holds no snapshot of it** (404, seq 17/19) ⇒ the event
   series must be harvested from dated press-release items — a collection
   task specified in field 12. Decision classification (change vs
   carry-over; Δ kb/d) comes from the communiqué text as-published.
   **Announcement TIME distribution (Vienna afternoon vs Sunday) is
   NOT_RUN** — until captured, all entries are close-of-next-session
   observations only (daily INFERENCE). Surprise vs consensus:
   consensus is vendor-licensed (no free OPEC consensus measured) ⇒ naive
   arm = decision-vs-prior-target state [PROVISIONAL]; a true-consensus
   variant is NOT_RUN_DATA_ABSENT. Price legs: same corpus walls as all
   comm families (CARRIED_STATUS §2).
4. **Bindings** (universe, clock, roll, expiry — verified against captured
   specs, not memory): **CL (NYMEX): 1,000 barrels; USD & cents/bbl; tick
   0.01 = $10.00** [root main d8cf8eca, costs/SPECS_MARGINS_PUBLIC_2026-10-02.md
   §1 CL row, AMP/NT mirrors fetched 2026-10-02; consistent with baseline
   COMM_HYPOTHESES §0.1]. Physical delivery Cushing; NYMEX/Globex; monthly
   contracts, all 12 listed; last trade = 3rd business day prior to the 25th
   of the month prior to delivery + weekend-shift sub-rule (official dates
   Apr 2010→Feb 2027, COMM_CALENDAR_EVIDENCE sha256 adcd3b54… re-verified
   this lane); **roll rule PIT-legal declared: hold until the last session
   before day-1 of the delivery month; roll ±1 sessions EXCLUDE**;
   negative-price law (simple returns) adopted; RTH bars only in corpus.
   Event universe = OPEC+ meetings 2017-01→present (post
   Declaration-of-Cooperation era) with as-published decisions;
   announcement-day == WPSR-Wednesday coincidences EXCLUDE/split-reported.
5. **Entry / stand-aside / exit [PROVISIONAL]** (daily only; any intraday
   variant is NOT_RUN_DATA_ABSENT): entry = first RTH close after the
   as-published announcement is observable in a daily-bar world (next-close
   convention), direction per arm A1 (A2 is the null arm — fade-state);
   delay-pair {t close, t+1 close} is the only legal delay axis. Exit = t+3
   close or opposite-decision meeting, whichever first [PROVISIONAL].
   Stand-aside: (i) meetings without an as-published decision classification
   EXCLUDE (no inference from memory); (ii) roll ±1 EXCLUDE; (iii) holiday-
   calendar-uncertain days EXCLUDE/NOT_RUN (§0.2 baseline law); (iv)
   WPSR-day coincidences split; (v) venue-closed announcement windows
   (Sunday decisions) flagged — entry remains next-RTH-close, never an
   inferred fill.
6. **Baselines / placebo / negative controls**: C1 seeded **meeting-clock
   placebo** (same meeting calendar, direction shuffled; ≥100 seeds — the
   COMMNG1 release-clock lesson is binding: the bare clock out-earned the
   signal there, so the clock-only arm is mandatory and scored);
   C2 always-in at the meeting clock (does anything survive beyond
   meeting-week exposure?); **NC = the CONFIRM/carry-over-meeting subset**
   (mechanism predicts ≈ nothing on decisions that change no target — if
   confirm-meetings move CL like change-meetings, the state is not the
   mechanism); delay-pair adjudication {t, t+1}.
7. **Refutation conditions**: K1 — C1 clock placebo reproduces the
   change-meeting behavior ⇒ clock artifact, dead (the COMMNG1 law
   transposed); K2 — NC fires (confirm subset ≈ change subset) ⇒
   decision-content dead, family retires to a calendar-construction note;
   K3 — both arms below floor at realistic n; *expected-failure
   interpretation stated a priori*: with only ~12–18 change/confirm events
   inside the 14-month true-volume window, this family is **power-marginal
   by construction today** — a null at this n is the pre-registered K3
   death, NOT evidence of absence (any future legalization requires the
   price-depth purchase of field 12); K4 — delay flip (t vs t+1 sign
   reversal) ⇒ announcement-auction artifact, downgrade to descriptive;
   K5 — era concentration (effect only 2020 COVID-OPEC era or only 2022)
   ⇒ regime proxy, dead. Cost-level: CL MODELED tiers below; a 1–3-day
   event hold pays one round trip ⇒ dies if median conditional |move| ≤
   S2 round trip.
8. **Cost / spread / slippage sensitivity — MODELED COST ONLY**: fees CL
   2.36 USD/side T1 (commission 0.85 + exchange NOT_FETCHED + reg 0.01;
   **UNDER REVIEW until owner A7; VERIFIED_VS_ACCOUNT=NOT_RUN**); spread
   half-turn proxy $15.00 (3-tick $30 front-20d median close-proxy,
   high-biased; root S6_FRONT_SPREADS.json CL.median_usd=30.0); slippage
   tiers {1,2,3}×$10/side research assumption ⇒ S1/S2/S3 = 27.36 / 37.36 /
   47.36 per side; round trip at S2 = 74.72. Weekend-announcement holds
   (field 5-v) carry two overnight gaps priced only by the SI-style
   blind-spot warning (no overnight bars — NOT_RUN_DATA_ABSENT). The words
   "measured/complete cost" are FORBIDDEN.
9. **Regime / era breaks**: feature window 2017→present spans the 2020
   price-collapse+OPEC++ era, the 2022 cut regime, and the 2024–2026
   voluntary-group management era — a 3-regime feature history with
   structurally different decision processes; price window = 14-month
   true-volume era (one regime) + settlement-derived refs only before
   2025-08 ⇒ era-stability kills are unanswerable today (declared
   unanswerable, not skipped). Decision-cadence break (monthly JMMC 2020–21
   vs quarterly/ministerial patterns later) is a declared stratifier,
   [PROVISIONAL] until the event series exists.
10. **Coverage / hole proof**: HAVE (free, hash-pinned): opec.org homepage
    dated meeting items (capture), CFTC-irrelevant walls documented, CL
    14-month front + settlement refs + BID/ASK 1Y + margins/spreads (root).
    HOLE (nothing exists today): the OPEC meeting/decision event series
    itself (collection task, field 12); announcement timestamps; consensus;
    price depth < 2019-09 (settlement-only), < 2025-08 true-volume;
    intraday announcement windows; BBO. **Intraday: nothing below
    2025-11/12 exists for CL.**
11. **Sources per FACT**: (1) opec.org homepage dated items [capture
    4499580f…, 2026-10-04]; /meetings.html 403 + wayback-404 [fetch_log
    seq 12/17/19 — BLOCKED_TRANSPORT/NOT_OBTAINED, no bypass]; (2) CL
    specs/expiry/session: root SPECS_MARGINS_PUBLIC §1 + COMM_CALENDAR_
    EVIDENCE (sha adcd3b54, re-verified); (3) cost law: FEES_CORRECTED
    (sha 006d6372, re-verified) + root S6/IBKR commissions; (4) corpus
    walls: root FINAL_REPORT/S6/S7 @ d8cf8eca; (5) ancestry: FAMILY_FAILURES
    rows 106–108 + HYPOTHESIS_LEDGER COMMODITIES-NG1 row.
12. **DATA REQUIREMENTS (exact purchase/collection spec — nothing ordered,
    owner decision only)**:
    - **Event series (free collection, prep-legal)**: full list of OPEC/OPEC+
      full-ministerial + JMMC + eight-country-voluntary meetings 2017-01→
      present; per meeting: as-published press-release URL, publication
      timestamp, communiqué text, decision class ∈ {target-cut, target-raise,
      extension, carry-over/confirm, exemption/adjustment}, Δ target (kb/d)
      where stated. Source: opec.org press-room items (dated; homepage
      200-verified) — /meetings.html BLOCKED (403) and unarchived; harvest
      = crawl of dated press items. Deliverable format: one JSONL row per
      meeting with sha256 per source page.
    - **Price (vendor purchase OR prospective accumulation — owner
      decision)**: CL per-contract daily TRADES + BID/ASK ≥ 2019-01→present
      (true volume, unadjusted, per-contract with conId/expiry identity);
      M1 (and ideally 1s) TRADES covering announcement windows ≥ 2019 for
      release-time reaction; BBO depth if licensable. Fields: OHLCV,
      per-contract, exchange timestamps, no back-adjustment.
    - **Optional (NOT_RUN if absent)**: vendor OPEC-meeting consensus
      expectations series (would upgrade naive arm); delegate-press
      chronology is NOT purchasable — declared.

---

## 3. CLNG-F4 `STEO-REV` — EIA STEO monthly forecast-revision flow (CL + NG legs, one event set)

**Type: NEW, DATA-BLOCKED (scored status NOT_RUN_DATA_ABSENT).** Monthly
official-model forecast-vintage family; two symbol legs on one shared event
set (the STEO release calendar). Anti-duplication adjudicated against
NG-F2 CPC-REVISION and CL-F1/NG-F1 (§5 table).

1. **Mechanism + microstructure** [MECHANISM_HYPOTHESIS]. **Who is
   forced/slow**: EIA's STEO is the US official monthly energy-balance
   forecast (production, consumption, implied stock path, hub price paths
   for WTI and Henry Hub); systematic money flow and corporate planning
   desks re-anchor to its revision; because the STEO is model-mechanical
   and embargoed ("Forecast Completed" stamp precedes release), the revision
   information reaches the market in one dated packet per month. **Why an
   effect may exist**: a consecutive-vintage revision of the forward
   balance (e.g., next-quarter global/US implied stock change, or US
   production) re-prices the expected path; if the market under-reacts to
   slow official-model information, front futures drift toward the revised
   path over sessions. **Two competing arms**: arm **B1 REV-CONT** —
   revision-direction drift (balance-revision bullish ⇒ positive front
   return); arm **B2 MECHANICAL-NULL** — STEO revisions are extrapolations
   of already-published weekly data (WPSR/WNGSR/EIA-914), so once the
   prior-week inventory state is conditioned, the revision carries nothing.
   The arms are adjudicated on one registered event set with the weekly
   state as the built-in control (cross-family adjudication, mirrors the
   baseline's NG F1-vs-F2 design).
2. **Expected direction, falsifiable** [PROVISIONAL]: B1 — E[front return
   over 1–5 sessions post-release | revision of the named balance item] has
   the revision's sign, per leg (CL, NG), beyond costs, and weakens with
   entry delay; B2 — the same conditional is ≈ 0 after conditioning on the
   prior-week WPSR (CL leg) / WNGSR (NG leg) surprise state. Pre-registered
   revision variable, chosen a priori and frozen before any math
   [PROVISIONAL default: next-quarter implied global stock-change revision;
   secondary robustness variable: STEO WTI / Henry Hub spot-forecast
   revision — both declared, never post-hoc selected].
3. **PIT feature availability**: STEO releases are dated monthly; the
   current page stamps **"Release Date: September 9, 2026 | Forecast
   Completed: September 3, 2026 | Next Release Date: October 6, 2026"**
   [FACT, captures/eia_steo_main.html, sha256 40420203…, fetched
   2026-10-04] — the completed-stamp is direct embargo-law evidence that
   content is frozen before release (PIT by construction IF editions are
   used as-published). **Vintage-archive completeness NOT verified** — the
   archives path 403'd this lane [fetch_log seq 18] ⇒ edition-list
   harvestability is a field-12 data requirement, NOT an assumption.
   Revision series construction (table deltas across editions) NOT_RUN.
   Consensus: not needed (revision-vs-revision family); a
   consensus-vs-STEO variant is NOT_RUN_DATA_ABSENT. Price legs: corpus
   walls as usual.
4. **Bindings**: one event set, two legs: **CL** bindings = §2 field 4
   verbatim; **NG (NYMEX): 10,000 MMBtu; USD/MMBtu; tick 0.001 = $10.00**
   [root SPECS_MARGINS §1 NG row]; physical delivery Henry Hub; monthly
   contracts, all 12 listed (no serial/cycle split — "Monthly contracts
   listed for the current year and the next 12 calendar years", root
   SPECS_MARGINS quote of NT); last trade 3rd-last business day of the
   month before delivery (official dates Jun 2010→Feb 2027, COMM_CALENDAR
   re-verified); same roll rule, negative-price law, RTH-only. Feature
   clock: release day mapped to next-RTH-close (release hour ~10:00 ET
   class [PROVISIONAL] until the per-release timestamp series is captured —
   NOT_RUN).
5. **Entry / stand-aside / exit [PROVISIONAL]** (daily): state R(t) =
   frozen-variable revision between the two most recent as-published STEO
   editions; entry = first RTH close after release (delay-pair {t, t+1});
   direction per B1 (B2 = null arm); exit = 5 sessions or offsetting
   revision [PROVISIONAL]. Stand-aside: (i) STEO release day coinciding
   with WPSR/WNGSR release day (it happens — both are ~10:00–10:30 ET EIA
   products) EXCLUDE/split-reported (event-stacking law); (ii) roll ±1
   EXCLUDE per leg; (iii) holiday-shifted releases flagged from the
   as-published dates themselves; (iv) editions missing the frozen
   variable (schema changes) EXCLUDE, never imputed.
6. **Baselines / placebo / negative controls**: C1 seeded release-clock
   placebo (same monthly calendar, shuffled revision signs, ≥100 seeds);
   C2 always-in at the release clock; **NC = B2's weekly-state conditioning
   set** (if the revision effect is fully absorbed by the prior-week
   WPSR/WNGSR state, the STEO-specific mechanism is dead — the family then
   retires to "weekly families suffice", which is a KILL for B1, not a
   rescue); seasonal placebo (same-calendar-month mean revision of trailing
   years must show nothing); delay-pair adjudication.
7. **Refutation conditions**: K1 — C1 placebo reproduces the effect ⇒
   dead; K2 — B2 wins (weekly state absorbs revision) ⇒ B1 dead, family
   retires (explicitly NOT converted into a fourth weekly family — that
   would duplicate CL-F1/NG-F1); K3 — both arms below floor at realistic n
   (honest power note: ~12–14 releases inside the true-volume window per
   leg ⇒ power-marginal by construction today; a null is the pre-registered
   K3 death, not absence); K4 — revision-variable choice flips the sign of
   the conclusion ⇒ frozen-variable fragility, dead (both declared variables
   must agree in sign for survival — double-variable robustness rule,
   mirrors CL-F1's double-proxy rule); K5 — effect confined to one regime
   (2022 energy crisis or 2020) ⇒ regime proxy, dead; K6 — delay flip ⇒
   same-day absorption artifact, downgrade to descriptive. Cost-level: dies
   if median conditional |move| ≤ S2 round trip per leg.
8. **Cost / spread / slippage sensitivity — MODELED COST ONLY**: CL tiers
   27.36/37.36/47.36 (§2 field 8); **NG fees 2.46/side T1 (UNDER REVIEW)**,
   spread half-turn proxy $10.00 (2-tick $20 front median close-proxy; root
   S6 NG.median_usd=20.0), slippage {1,2,3}×$10 ⇒ NG S1/S2/S3 =
   22.46/32.46/42.46 per side; round trips S2: CL 74.72, NG 64.92. A 5-day
   hold pays one round trip but adds weekend/gap risk with NO overnight
   bars (blind-spot warning, inherited). "Measured/complete cost" FORBIDDEN.
9. **Regime / era breaks**: feature window could span 2017→2026 (~117
   editions) with cadence stability to be verified from the archive (the
   Sep-9-2026 vs Oct-6-2026 stamps bracket the "first/second week" —
   [PROVISIONAL]); price legs one regime (14-month true-volume) +
   settlement-derived refs ⇒ era kills unanswerable today (declared).
   STEO schema changes (table restructures) are era breaks on the feature
   side and must be stratified, never silently pooled.
10. **Coverage / hole proof**: HAVE: release/embargo stamps (capture);
    weekly-state features free (1,205 WNGSR + 790 WPSR vintages,
    re-verified hashes); price/spread/margin posture (root). HOLE: the STEO
    edition archive + release-date series (field 12; archives 403 this
    lane); the revision series itself; price depth (< 2025-08
    settlement-only; < 2019-09 nothing per-contract); intraday; BBO;
    per-release timestamps. **Intraday: nothing for CL before 2025-11/12;
    NG M1 back to ~2023-11 with completeness NOT_RUN.**
11. **Sources per FACT**: (1) STEO stamps [capture 40420203…]; archives 403
    [fetch_log seq 18 — BLOCKED_TRANSPORT]; (2) CL/NG bindings: root
    SPECS_MARGINS §1 + COMM_CALENDAR_EVIDENCE (adcd3b54, re-verified);
    (3) weekly-state vintages: baseline §7 hashes (all re-verified this
    lane); (4) corpus walls: root FINAL_REPORT/S6/S7 @ d8cf8eca; (5) cost
    law: FEES_CORRECTED (006d6372) + root S6/IBKR commissions; (6) ancestry
    anti-duplication: baseline NG-F2/CL-F1/CL-F2 + FAMILY_FAILURES rows
    82/172 (macro-surprise and EIA-energy-signal dead rows, adjudicated §5).
12. **DATA REQUIREMENTS (exact purchase/collection spec)**:
    - **Event/vintage series (free collection, prep-legal)**: complete
      as-published STEO edition archive 2017-01→present (XLSX/CSV as
      published), with per-edition release timestamp + forecast-completed
      stamp; harvestable from EIA STEO pages (current page 200-verified;
      archives path 403 this lane ⇒ confirm harvestability or request
      owner-assisted path). Deliverable: per-edition files + a manifest
      JSONL (edition date, stamps, sha256) + the frozen-variable extraction
      spec (next-quarter implied stock change; WTI/Henry Hub forecast rows)
      pre-registered before first parse.
    - **Price (vendor purchase OR prospective accumulation — owner
      decision)**: per leg (CL, NG) per-contract daily TRADES + BID/ASK
      ≥ 2019-01→present true-volume unadjusted + M1 ≥ 2019 (release-window
      reaction); same field list as CL-F3. NG note: corpus M1 already
      reaches ~2023-11 — a completeness audit of existing NG M1 vs the STEO
      calendar is the cheapest first step (NOT_RUN, prep-legal pass).
    - **Weekly-state controls**: already in hand (re-verified) — no
      purchase.

---

## 4. Veto / rejection section (every rejected candidate, with its wall)

- **V-1 — CFTC COT positioning extremes / crowd-positioning family (CL, NG).
  VOID — ANCESTRY VETO (strongest wall available).** Nearest dead rows:
  FAMILY_FAILURES.jsonl 106/107/108 — COMMNG1-A4-P2 ARM1/ARM2/ARM3,
  "Commodity crowd-carry persistence from CFTC CoT positioning",
  **SCORED_REJECTION**, primary code `CONTROL_OUT_EARNS_RELEASE_CLOCK`,
  terminal `COMMODITIES_NG1_REJECT_ALL`; ledger (line 233): "the bare
  release-clock control out-earned every anchor after costs … the edge
  belonged to the CoT release-calendar geometry, not positioning
  information — crowd-carry positioning frontier measured-closed on this
  substrate". Distinguishability check honestly attempted and failed: the
  dead run's substrate was ETP legs + CoT archives (EODHD), while a CL/NG
  futures CoT family would differ in instrument — but the signal class
  (CoT positioning → commodity returns) and its killing control (the
  Friday-15:30 release clock, now captured verbatim [cftc_cot_release_
  schedule.html, sha256 05c5affe…]: "released at 3:30 p.m. Eastern time …
  usually released on Friday … data from the previous Tuesday") are
  substrate-independent. No rename of dead classes; no third overlap with
  the carried ES-F3 COT-CROWD class either (that family owns the equity-
  index side). **VETO stands; the only legal residue is C1-class clock
  placebos inside other families, which §2/§3 already carry.**
- **V-2 — NG option-expiry × WNGSR-release timing interplay. REJECT —
  construction-adjacent + data-absence.** The mechanism (pinning/gamma
  into option expiry interacting with the Thursday print) is intraday-only
  by nature: BBO NOT_RUN on all symbols (D5 law); NG M1 exists only from
  ~2023-11 with per-release completeness NOT_RUN (root S7; CARRIED_STATUS
  §3.1); expiry/option calendars are construction inputs (DC §1.3 class +
  NG-F3 law: calendars feed stand-aside rules, never standalone alpha).
  Would also duplicate the WNGSR event space already occupied by carried
  NG-F1/F2 (anti-duplication).
- **V-3 — Cushing-basis / WTI-spot relative-value family. REJECT —
  standing-law wall + PIT wall.** DC §1.3 + the CL cost-law declaration
  reserve basis/carry/curve states as conditioning inputs, not standalone
  alpha; CL-F2 already owns the Cushing-information event space. PIT: the
  free WTI–Cushing daily spot (1986-2026, verified live this lane
  [eia_wti_spot_dnav.html, sha256 5f9184d7…]) is a latest-vintage dnav
  page with no as-published archive ⇒ NOT PIT-strict (DATACONTRACT §1.4
  law). Brent leg absent from every owned corpus (vendor-only), so even
  the descriptive cross-market panel cannot be built today
  (NOT_RUN_DATA_ABSENT).
- **V-4 — API Tuesday report family. REJECT — duplicate + data-absence.**
  The API print is already the declared negative-control row of carried
  CL-F1 Field 6(d); API historical prints are vendor-licensed (baseline
  CL-F1 Field 10). Creating it as a family would clone the WPSR event
  space with a data wall.
- **V-5 — CL/NG overnight-session gap family. REJECT — data-absence +
  registered-parent territory.** No overnight bars exist (corpus H1/M1
  begin at RTH opens; FINAL_REPORT "no overnight session"); the
  overnight/tail classes are the REGISTERED PB1 parent pair's territory
  with the baseline §0.5 anti-multi-trial ruling — a comm-leg variant
  would be a disguised re-parameterization.
- **V-6 — "EIA energy signal" gating variants. REJECT — dead-class
  adjacency.** DEV1-DAILY-EXPLORATORY-DS03 (FAMILY_FAILURES row 172):
  "EIA energy signal Brent-flat gate" closed
  `NOT_RUN_THIN_AGGREGATE` + `EXPECTANCY_NONPOSITIVE` + `B0_DOMINANCE` on
  the FX substrate. Any energy-data gating family must clear this ancestry
  row explicitly; this lane proposes none (the weekly inventory families
  NG-F1/CL-F1 already occupy the legitimate form of this space as carried
  families).

## 5. Ancestry-check table (every candidate vs the dead inventory)

Scan basis: all **173** FAMILY_FAILURES.jsonl entries read this lane;
commodities rows 106–108 + adjacency rows (58, 60, 61, 62, 81, 82, 91, 93,
172) read in full; ledger line 233.

| candidate | nearest dead entries (asset, family_id, primary code) | distinguishability statement | verdict |
|---|---|---|---|
| CL-F3 OPEC-DEC-FLOW (NEW) | 106–108 COMMNG1-A4-P2 (CoT positioning; CONTROL_OUT_EARNS_RELEASE_CLOCK); 81 FXNG1-A5-P1 (economy release-order rollout; EXPECTANCY_NONPOSITIVE); 91 FXNG4-A4-P1 (EZ seasonal print-deviation; ANCESTRY_RHO_BLOCK); 172 DEV1-DS03 (EIA-energy FX gate; NOT_RUN_THIN_AGGREGATE) | Mechanism class = SUPPLY-POLICY DECISION flow (production-target changes by a named cartel on a dated meeting calendar). The dead commodities class is POSITIONING-REPORT flow (COT archives) — different information source, different calendar, different actor; the dead FX classes are macroeconomic print events on fiat pairs. No dead row contains a producer-cartel decision event. The COMMNG1 release-clock lesson is imported as K1's mandatory clock placebo rather than ignored. Not a rename of any dead class; distinct from carried CL-F1/F2 (inventory-data resolution vs policy decision). | **NO VETO — pass** (with K1 clock placebo binding) |
| CLNG-F4 STEO-REV (NEW) | 82 FXNG1-A4-P2 ("vintaged surprise vs frozen trend prior" CPI drift; CONTROL_OUTEARNED_ANCHOR); 61/62 FXFV9-A4-P1/P2 (realized-inflation event structure; ANCESTRY_RHO_BLOCK); 172 DEV1-DS03; carried NG-F2 CPC-REVISION (LIVE — duplication check, not ancestry) | Mechanism class = OFFICIAL-MODEL FORECAST-REVISION flow (EIA's own monthly balance forecast). Dead macro-surprise rows are CPI/inflation surprise classes on FX with yield-level shadow controls — different variable, different asset, different revision object. Vs carried NG-F2: different vintage series (NOAA daily weather outlooks vs EIA monthly balance), different cadence (daily vs monthly), different actor (CPC model vs STEO model), different symbol coverage (NG-only vs CL+NG). Vs carried CL-F1/NG-F1: revision-vs-revision (forecast flow) vs actual-vs-consensus (data resolution) — the B2 arm explicitly conditions on the weekly states rather than duplicating them. | **NO VETO — pass** (B2 weekly-state control binding; K4 double-variable rule) |
| COT positioning extremes (REJECTED) | 106–108 (see §4 V-1) | instrument difference (futures vs ETP) does not survive the release-clock falsification law | **VOID — ancestry veto** |
| NG option-expiry × storage timing (REJECTED) | (no dead row; walls are standing-law + data) | DC §1.3 construction class + intraday absence | **REJECT — construction-adjacent + data-absence** |
| Cushing-basis family (REJECTED) | (walls are standing-law + PIT) | DC §1.3 basis/carry class; CL-F2 occupies the space; latest-vintage spot NOT PIT-strict | **REJECT — standing-law + PIT wall** |
| API Tuesday family (REJECTED) | 172-adjacent (energy-data gates) | already CL-F1's declared negative-control row; vendor data wall | **REJECT — duplicate** |
| Overnight-gap family (REJECTED) | PB1 registered parent territory (not a dead row — anti-multi-trial) | no overnight bars; PB1 owns the class | **REJECT — data-absence + anti-multi-trial** |

## 6. Trial-identity census (conventions of RANKING_INPUT §3; CONTINGENCY ONLY)

Convention: every scored cell = one identity; mandatory scored controls =
C1 seeded clock placebo + C2 always-in + the family-specific NC; arms =
{with-state, fade-state}; tails = {positive, negative} state sign; delay =
daily delay-pair {close t, close t+1} (only legal axis); tiers = slippage
S1/S2/S3 on the MODELED table. Descriptive/stage-1 legs = 0 identities.

| family | grid | full-grid IDs | minimal-core (S2) | + scored controls | minimal total | event-set size (feature-side / in-true-volume-window) |
|---|---|---|---|---|---|---|
| CL-F3 OPEC-DEC-FLOW | 2×2×2×3 | 24 | 8 | 3 (C1 clock, C2, NC=confirm-subset) | **11** | meeting list NOT_RUN (~110–135 expected 2017–26 [PROVISIONAL]) / ~12–18 (2025-08→2026-10) |
| CLNG-F4 STEO-REV | 2 legs × (2×2×2×3) | 48 | 16 | 6 (3 per leg; NC=weekly-state per leg) | **22** | ~117 editions 2017–26 [PROVISIONAL] / ~13–14 per leg |
| carried NG-F1 / NG-F2 / CL-F1 / CL-F2(joint) | unchanged | 24 each | 8 | 3 | 11 each | baseline §3 census, unchanged |

**Standing-budget law restated**: hypothetical comm aggregate if ALL
families were ever legalized = 54 (carried) + 11 (CL-F3) + 22 (CLNG-F4) =
**87 > 24 ⇒ BLOCKED_TRIAL_BUDGET on any single-cycle attempt** — enumerated
precisely so a future packet cannot discover this late. **Nothing is
registered, scheduled, or scored; no comm identity enters any cycle's
ceiling arithmetic.** Both new families are additionally DATA-BLOCKED
independently of the budget law.

## 7. Provisional D1–D5 (RANKING_FRAMEWORK anchors, applied mechanically; package-quality only)

| family | D1 | D2 | D3 | D4 | D5 | total | one-line mechanical basis |
|---|---|---|---|---|---|---|---|
| CL-F3 OPEC-DEC-FLOW | 1 | 2 | 2 | 2 | 1 | **8** | no on-symbol family-linked anatomy, event set not built (D1=1); actors+timing named, daily mapping INFERENCE, NC exists (D2=2); kills complete incl. K1 clock placebo, no intraday delay axis, court-MDE NOT_RUN (D3=2); as-published dates+communiqués PIT but /meetings.html BLOCKED_TRANSPORT and announcement timestamps NOT_RUN (D4=2); floor computable, MDE NOT_RUN (D5=1) |
| CLNG-F4 STEO-REV | 1 | 2 | 2 | 2 | 1 | **8** | no on-symbol anatomy, revision series NOT_RUN (D1=1); actors+monthly stamps+embargo captured, INFERENCE daily mapping, B2 weekly-state NC (D2=2); kills complete, no delay axis, MDE NOT_RUN, power-marginal declared (D3=2); as-published-edition PIT + completed-stamp FACT but archive completeness NOT_RUN (D4=2); floor computable, MDE NOT_RUN (D5=1) |

Carried families' 5-dim scores are the synthesis lane's append (baseline
3-axis ranks restated in CARRIED_STATUS; not re-scored here — no
self-ratification of program ranks).

## 8. Data-requirements table (consolidated; nothing ordered — owner decision gate only)

| # | requirement | symbol(s) | depth | fields | event series | unblocks |
|---|---|---|---|---|---|---|
| DR-1 | OPEC meeting/decision collection (FREE) | CL | n/a | press URL, as-published timestamp, communiqué text, decision class, Δ kb/d | 2017-01→present, sha256 per page | CL-F3 feature side (D1 1→2) |
| DR-2 | STEO edition archive (FREE) | CL, NG | n/a | all tables as-published + release/forecast-completed stamps | ~2017→present editions, manifest JSONL | CLNG-F4 feature side |
| DR-3 | Per-contract daily TRADES + BID/ASK history (VENDOR or prospective) | CL, NG | ≥ 2019-01→present, unadjusted, per-contract | OHLCV(true volume), settlement flag, conId/expiry | n/a | every comm family's pre-2025 price leg; 24-month DAILY_BT wall |
| DR-4 | M1 (ideally 1s) TRADES around release/announcement windows (VENDOR or prospective) | CL, NG | ≥ 2019 for CL-F1/F3, NG-F1/F4 reaction windows | OHLCV, exchange ts | WPSR Wed 10:30 / WNGSR Thu 10:30 / OPEC announcements / STEO releases | intraday delay axis; releases NOT_RUN today |
| DR-5 | Completeness audit of EXISTING corpus M1 vs EIA schedules (FREE, prep-legal, NOT_RUN) | NG (2023-11+), CL (2025-11+) | existing files | bar-count vs schedule | ~150 WNGSR / ~47 WPSR / ~13 STEO / OPEC meetings in-window | narrows intraday holes before any spend |
| DR-6 | BBO / depth history (VENDOR, optional) | CL, NG | any | quote book | n/a | fill stories (D5 law) |

## 9. NOT_RUN / NOT_OBTAINED register (this lane)

1. OPEC /meetings.html — BLOCKED_HTTP_403; wayback snapshots — NOT_OBTAINED
   (404 ×2); homepage dated items captured (200). No bypass.
2. STEO archives path — BLOCKED_HTTP_403; vintage-archive completeness
   NOT_RUN (DR-2).
3. CPC URL spelling erratum: baseline `6_10day` 404s; correct `610day`
   captured (issuance-time law verbatim).
4. EIA NG dnav futures extension — NOT_OBTAINABLE post-2024-04-05 (page
   statement, captured); supersedes baseline NG-F1 Field 11(4) candidate.
5. Baseline-hash re-verification — DONE 24/24 (not a NOT_RUN; recorded for
   completeness of the register).
6. Announcement/release timestamp series (OPEC, STEO per-release) — NOT_RUN.
7. Court-method MDE for both new families — NOT_RUN (declared in D3/D5).
8. All cost/account verifications — NOT_RUN (fees UNDER REVIEW; BBO
   NOT_RUN; exchange NOT_FETCHED).

— End HYPOTHESES_COMM_EN_R3.md. Zero PnL/returns entered any cell; missing
evidence is NOT_RUN everywhere; no registration, no trial creation —
proposals on paper only.
