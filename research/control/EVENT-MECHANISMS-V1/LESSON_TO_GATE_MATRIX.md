# LESSON-TO-GATE MATRIX — EVENT-MECHANISMS-V1

Owner-directed (2026-09-27). Every error class the program has already paid
for is mapped to the machine-enforced gate that must fire BEFORE any scored
PnL this cycle. A gate not listed here does not exist; a listed gate not
run is `NOT_RUN`, never inferred PASS.

## The six owner-named error classes → gates

| # | Error already paid for | Evidence (source) | Gate that must catch it (this cycle) | Gate ID |
|---|---|---|---|---|
| E1 | **RANGEFADE lookahead / unfinished-day state**: prior-day range/mode computed on a day that had not finished; leaky twin passed all 8 gates (+3,207/+5,030 pips), PIT-clean law PF 1.03–1.05 and dies at 1.5× cost | ERP1-TRACKA-COHORT-1 `INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25.md`; LESSONS P-18 (holdout cannot clear a lookahead); HYPOTHESIS_LEDGER TRACKA2 row | Every event/state feature must be computed on a panel **truncated at each decision instant** and replay byte-identical (panel-truncation replay, 100% of decision points); unfinished-window guard asserts window completeness from window-boundary timestamps, not from row presence; delay twin shifts signal one index with preregistered seam band | G4a PIT battery; G4b future-mutation; G4c panel-truncation replay |
| E2 | **Same implementation reproduces the same bug**: exact reproduction recreates lookahead bug and result | LESSONS P-4; Q-14 equivalence baselines drift silently | A **second, independent implementation from the frozen spec** (different author context, no shared feature code) must agree within preregistered tolerance on decisions/fills/costs before scored run; disagreement = blocker, not a tolerance negotiation | G5 independent implementation |
| E3 | **Many variants of one family** (multiple testing → beautiful curve by luck) | plan_at.md §5; Harvey/Liu/Zhu; F-0 court kills (DTP 11/11, ERP1-TRACKB 9 classes → 1 admitted); anti-variant law ≥2/3 axes | Skeleton-merge at screening (substantially-identical ideas collapse to one); max **3 identities** total; per identity **1 anchor + ≤2 neighbours + 1 same-direction control + 1 sign-flip control + 1 preregistered baseline**; every scored computation enters the append-only trial ledger (observed counter) — no post-hoc "that one doesn't count" | G1 screening court + skeleton merge; G3 identity freeze; L1 trial ledger |
| E4 | **Costs eat the edge** | ERP1-TRACKA2 P3-A killed by the bill (measured 0.9–1.0 pips vs frozen ≤0.41 @k=2.0); VOL-NG1 cost-ceiling family kill; ERP1 floor 3.6/4.4 pips RT; 38 forex failures never reached it | Preregistered **cost ceilings frozen before any PnL**: stocks = Q-2 conditional-cost law (open-vs-midday 3.33×/3.35×) + L-SAMV1-3 X1/X2 fill-feasibility (volume-0 bars unfillable, notional ≤ participation fraction, unfillable skipped AND counted); gross expectancy must clear the ceiling at ×1.0 and survive ×1.5/×2.0 stress — ceiling arithmetic done on paper BEFORE implementation | G6 cost ceiling (pre-implementation) |
| E5 | **Data/timestamp without authority**: retrieved_time used as available_time; vendor-stated constants; adjusted series as-of-pull (lookahead by construction); posting-bound ignored | §13 PIT doctrine; P-26 (cadence-text bound re-derived per file class); Q-8; L-SAMV1-1 (EODHD adjusted_close lookahead by construction); FTD ≥17d posting bound | Authority row per dataset (source/terms/period/resolution/event-available-ingested/revision/tz/missingness/manifest) with measured-not-stated availability; `available_at` only from release evidence (EDGAR acceptance datetime of the correct vintage; amendments create new vintages); no substituted backfilled timestamps/prices for convenience — missing = `BLOCKED_DATA` with owner-action list | G2 data authority (fail-closed) |
| E6 | **Prospective/OOS results not derivable from backtest** | Standing law (S0 ≠ untouched OOS; shadow floors; paper ≠ live); Q-9 half-seal protects nothing; owner 2026-09-25 §6.9–6.10 | S0 walk-forward is screening-only (labeled seen); **sealed OOS is a separate owner gate** (G9) after G8 scored run; no hypothesis/parameter/cost-law change after scored PnL visible — any change = new identity + new ancestry accounting; prospective claims only from prospective shadow under its own cycle | G8 scored walk-forward → G9 sealed-OOS gate (two separate owner gates) |

## Additional standing lessons wired into gates

| Lesson | Gate wiring |
|---|---|
| P-2 thin margins: margin-to-fail recorded on every gate verdict | all gates |
| P-7 bundle ≠ endpoint: coverage verdict binds to exact channel | G2 (channel-scoped authority rows; canary names) |
| P-15 smoke numbers kill, never select | L1 ledger labels; selection only from frozen arms |
| P-19/P-30 measured stamps: numbers in artifacts are measured, SHA/data from `git rev-parse`/hashes, timestamps from clock at recording | every artifact |
| Q-11 a permutation is a null only if it moves the signal; clock-only shadow for event conditioning (Q-7) | G4d control validity; G6 controls |
| Q-12 exclusion zone of the bar disclosed ("nothing passed" + bar height) | every gate verdict |
| P-24 falsification-by-control compounding: release-calendar owns the money (macro clock class dead) | G1 screening collision table |
| P-27/P-29 representation-rho: smooth input of a dead observable = same family | G3 F-0 court |
| §39 ERP1 three-law seam (scored law vs PIT-clean re-spec vs runtime law) — measure divergence before trusting any number | G4c |
| P-10 root checkout shared stage: stage by pathspec, no `git add -A`, no dirty index across long ops | all commits |
