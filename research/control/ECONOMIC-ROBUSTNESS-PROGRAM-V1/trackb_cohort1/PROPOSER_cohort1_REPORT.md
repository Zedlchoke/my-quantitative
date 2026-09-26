# PROPOSER REPORT — ERP-TRACKB-PROGRAM-V1 cohort-1 (blind lane P1)

- Lane: trackb-cohort1-proposer, outcome-blind. Date: 2026-09-26. Base: main @ e4e3b9159685b9da0bafeed6814f0a73c872cbcb.
- Read (only): PLAN_erp_trackb_program_v1.md; PLAN_economic_robustness_program_v1.md §§5.3–5.7, 5.13, 5.14; LESSONS Q-1, Q-2, Q-6, P-27. No ledger/MAP/terminal/dashboard/outcome file opened; no PnL/PF/winner appears below.
- Book law: one shared 100,000 USDT book, long spot + short perp 1:1, unlevered; taker cost book; maker-only assumptions forbidden; entry only when expected carry over the intended hold >= full RT stress cost (law b).

## Anchors and breakeven arithmetic (declared facts only)

- Mean settled BTC funding 11.798%/yr => 3.23 bps/day => ~113 bps per 35-day hold. Downtrend mean ~1.11 bps/day => ~38.9 bps/35d. 24.7% of in-downtrend settlements negative; worst -0.30%/8h ~ 2.5 fee round-trips (frozen anchor).
- Two-leg taker RT 20–25 bps (mid 22.5); x1.5 = 30–37.5; x2.0 = 40–50 (mid 45).
- Breakeven days (bill / daily carry): mean-carry 6.2–7.7 base, 9.3–11.6 x1.5, 12.4–15.5 x2.0. Downtrend-carry 18–23 base, 27–34 x1.5, 36–45 x2.0 — matches the frozen §4.5 anchor. Consequence: in downtrend states a 3–5 week hold does NOT clear the x2.0 bill; the law-(b) gate binds exactly there.
- Q-6 binding: 11.798%/yr is a full-archive average (2020–2026); crypto ceilings decay. Entry-gate expected carry must be computed on the recent-window settled distribution, never the archive mean; recent-ceiling re-measurement is a freeze prerequisite (feasibility on the nearest window, §5.5).

## Candidate 1 — TB1-DN-CARRY-CTG (cost-gated fixed-horizon cash-and-carry)

Mechanism: enter only when expected carry over the intended 35-day hold >= RT stress bill (45 bps at x2.0), computed from the recent-window settled-funding distribution; hold exactly 35 days (105 settlements); weekly decision clock (Friday 00:00 UTC bar close); no intraweek rebalance; force-flat at fold boundaries. No funding-rate window, no prediction, no basis-level signal — the gate is a feasibility inequality, not a forecast.

1. Payer: leveraged USDⓈ-M perpetual longs (retail leverage demand + perp-native speculators). Their demand is leverage, not delta; arbing funding away means surrendering the leverage they came for, or holding spot inventory + margin they do not want (capital, custody, venue ops).
2. Premium: ~113 bps gross per 35-day hold at archive mean (3.23 bps/day); ~+68 bps/decision net of x2.0 RT stress; to be re-anchored on the recent window (Q-6).
3. Persistence: structural — funding is the price of persistent leverage demand; eroded by institutional carry-capture capacity (basis desks/ETF arb), funding compression as the tape matures, and deleveraging episodes (downtrend mean 1.11 bps/day, 24.7% negative settlements).
4. Risk transferred: funding-path tail (24.7% negative settlements in downtrends; worst tick -0.30% ~ 2.5 RT fees); short-leg uPnL margin path on pumps; hedge drift between legs; venue/outage risk (missed settlements, adverse gap reopen — DECLARED band); liquidation model DECLARED (tape BLOCKED).
5. Observable: settled funding available only at `fundingTime` (next-interval rate = PREDICTED, excluded); basis = perp − spot on synchronized 1h bars; entry decided at weekly bar close from then-available settlements only.
6. Horizon/clock: 35-day holds; weekly decision clock; exit only at horizon or force-flat.
7. Capacity (order-of-magnitude, DECLARED): top-of-book BTCUSDT perp/spot supports ~$1–5M clips at single-digit bps impact; edge halves around ~$20–100M per-clip taker flow where book-walk cost ~ daily carry; the 100k shared book is far inside capacity — the binding constraint is the low-turnover law, not depth. Must be census'd (Q-8) before scoring.
8. Costs: entry spot taker + perp taker ~10–12.5 bps; exit same => RT 20–25 bps (anchor, DECLARED until fill-hour census); spread/slippage conditional on the gate's own fill states (Q-2: premium-rich states are volatile states — the gate selecting rich states does not make the bar-close fill cheap); x1.5/x2.0 on every component + funding settled along the path.
9. Falsifier: entry-timing permutation control (same holding distribution, entry ticks shuffled within matched funding-state marginals) must NOT reproduce the net-of-stress carry; if it does, the gate carries no information and the identity dies. Kill also if: recent-window cost-survivability ceiling < 45 bps/35d for the majority of weekly ticks (pre-PnL, §5.5/Q-1); top fold > 50% of positive PnL (§5.14) — carry concentrated in the 2020–21 mania.
10. Controls/baselines: causal = entry-timing permutation (removes gate-timing info, keeps exposure shape; must be constructible and move the result, Q-11). Inverted = hold the same book exactly during gate-excluded states (expected carry < bill); must not out-earn the anchor. Baselines: cash 0%; long BTC spot same cost book; perp-only unlevered where scoreable.
- Nearest dead ancestor: CARRY-1D/3D/7D (CRYPTO-V6). Different in mechanism (feasibility-gated fixed-hold book vs funding-window prediction), information source (none vs trailing funding windows), causal control (timing-permutation vs fold-concentration kill). Disclosed adjacency: exposure SHAPE (long carry) is shared; the F-0 court must rule the gate is feasibility arithmetic, not re-clocked window selection.

## Candidate 2 — TB1-DN-CARRY-DTX (negative-run exit gate; regime-conditional holding)

Mechanism: same book and entry gate as CTG; the hypothesis is that the settled-funding STATE (sign/run of settlements, not a level window) carries exit information. Exit now iff E[remaining funding] < −exit RT (~-11 bps base / -25 bps stress), estimated from a 21-settled-day realized run-rate; ordinary downtrends (mean +1.11 bps/day) never trigger — only severe sustained negative runs do. Exit checks weekly only; exits rare by construction.

1. Payer: same leveraged longs; the incremental premium comes from deleveraging episodes in which payers unwind at a loss and funding runs deeply negative faster than a hedged book would exit.
2. Premium: tail-state insurance — avoided negative funding beyond the exit fee in severe runs (worst measured stretches at -0.30%/8h sustained imply tens of bps of remaining-hold loss); expected fire frequency is low; on unaffected holds the premium is ~0. Honest magnitude: small, and it must be shown net of its own exit bills and whipsaws.
3. Persistence: same structural base as CTG; the state info persists because deleveraging episodes are recurrent and measurable; eroded if funding turns state-independent or if the run-state is priced instantly by basis-arb capacity.
4. Risk transferred: CTG's tails plus whipsaw risk (exit followed by immediate recovery wastes the exit RT and re-entry bill); margin path during the exit itself.
5. Observable: settlement sign/run-length at `fundingTime` (PIT at settlement); same synchronized-basis and clock discipline; no predicted funding.
6. Horizon/clock: 35-day holds; weekly clock for entry and the weekly exit check; re-entry counts as a new decision.
7. Capacity: same as CTG (exits are partial-book two-leg RTs, same depth class).
8. Costs: CTG's cost book + early-exit two-leg RT ~10–12.5 bps base / 20–25 bps x2 stress, charged on the actual gated book at its fill hours (P-27/Q-2); re-entry pays a fresh entry half-RT and must re-pass the CTG gate.
9. Falsifier: funding SIGN-SCRAMBLE control (permute settlement signs within the level-matched distribution, preserving mean and magnitude marginals) must NOT reproduce the exit gate's improvement; if scrambled-state exits match real-state exits, sign/run carries no information and the identity collapses into the vetoed funding-level class. Kill also if DTX underperforms fixed-hold CTG net of exit costs across folds; inversion (exit when gate says hold) must not out-earn.
10. Controls/baselines: causal = sign-scramble (removes run-state info, keeps level and exposure shape). Inverted = anti-gate exits. Baselines: CTG fixed-hold book (primary, nested), cash, long spot, perp-only.
- Nearest dead ancestor: CARRY-1D/3D/7D and FUNDCROWD-MR (both consume the same settlement series). Different in: exit-only risk gate (no entry signal, no crowding mean-reversion), sign-state information (not level windows), causal control type (sign-scramble). Disclosed adjacency: if the F-0 court rules the sign-run exit a variant of the funding-window class, this slot empties.

## Slot 3 — EMPTY (SLOT_LEFT_EMPTY)

The natural third mechanism — basis-prepaid entry (enter only when the synchronized perp premium >= RT cost so convergence alone pays the round trip; funding as surplus) — is REJECTED pre-proposal under the P-27 F-0 court: same skeleton (delta-neutral carry), same information source as BASISLV-PREMFADE-28D (premium level), and umbrella §4.2 already records V14's price-only edge as funding-credit harvesting — a cost-thresholded premium gate is a re-tune, not a mechanism. Q-2 also binds: premium-spike states are the high-volatility fill states, so the entry coupon is offset by the conditional execution bill on the actual gated book; at x2.0 the coupon must cover ~45 bps before any funding, concentrating entries in the same mania folds that killed V6/V14 on concentration.

## Six economic questions (joint answers; per-candidate deltas above)

1. Who pays: leveraged BTCUSDⓈ-M perpetual longs whose demand is leverage itself; they cannot arb the funding away without giving up the leverage or holding spot inventory they do not want.
2. Premium: ~113 bps gross per 35-day hold at archive mean; ~+68 bps/decision net of x2.0 RT. Track-B law (c) disclosure: this premium is funding credit — carry harvest, not information alpha; every verdict must say so.
3. How long / erosion: persists while leveraged-long demand persists; eroded by institutional carry capacity, funding compression as the tape matures (Q-6), and deleveraging episodes.
4. Risk taken: funding-path tail, short-leg margin path, hedge drift, venue/outage (declared bands), declared liquidation model.
5. When the bill exceeds the premium: the x2.0 bill (45 bps) needs 12.4–15.5 days at mean carry but 36–45 days at downtrend carry — a 3–5 week hold clears stress only in non-downtrend states. CTG's entry gate and DTX's exit gate are the same inequality applied forward vs backward.
6. Refutation: CTG dies if the timing-permutation control reproduces the edge or the recent-window ceiling is sub-bill; DTX dies if the sign-scramble control reproduces it or fixed-hold CTG beats it net of exit costs; no inverted book may out-earn its anchor.

## Program-compliance notes

- Both candidates: `ANCESTRY_EXPOSED_DEV` (all of 2020-07-18..2026-08-21 is outcome-exposed; dev evidence kills and engineers only, never promotes); 2026-08-22..freeze = `SEAM_CONSISTENCY_ONLY`; the only real OOS is post-freeze prospective accrual, one look, decision-count gates.
- Power: weekly clock x 35-day holds => ~318 weekly ticks, ~64 non-overlapping holds over the archive; below the §5.14 252-decision daily adjudication floor — the child must run its power analysis at freeze and either justify fewer decisions with the thicker per-decision edge or declare `NOT_RUN_THIN`; sub-power positives are INCONCLUSIVE, never PASS. DTX additionally risks firing below any adjudicable count (time-stop law applies).
- Freeze shape per §5.7: one anchor + <=2 neighbours each (CTG: hold 28d / 42d at the same 2.0x gate; DTX: confirm window 14d / 28d); no grid, no blend, no sign-flip rename. F-0 court ruling precedes rho; rho precedes PnL.

## Honest count

Two (2) genuinely distinct mechanisms: CTG (a feasibility-gated fixed-horizon carry book with no predictive information source) and DTX (a regime-state holding-policy hypothesis tested by a sign-scramble null, nested on CTG's book). Slot 3 intentionally empty under SLOT_LEFT_EMPTY. Both carry disclosed adjacency to the CARRY/BASISLV ancestry and are submitted to the F-0 court for the skeleton/payer/information ruling before any rho test.
