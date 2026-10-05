# OWNER DECISION PACKET — NFL win-prob: open the successor prediction/scored cycle? (2026-10-05)

Decision required: register (or not) the successor NFL prediction/scored cycle that turns this
PREP into prospective evidence. PREP is complete and verified: D PASS 10/10, D-r2 PASS 6/6,
0 blocking defects; 0 scored; no GO registered or consumed; $0 spent.

Why repo evidence cannot decide it: any scored evaluation consumes trial budget and requires
the two-key launch (independent A7 prelaunch + owner typed GO at that cycle's own gate, P-8).
Opening the cycle also starts a clock: every NFL week that passes without a live prediction
ledger permanently forfeits those games to NOT_RUN prospective.

Option A — register the successor NOW (before 2026-10-06T00:15:00Z):
  Consequence: earliest capturable game = 2026_04_ATL_NO (kickoff 2026-10-06T00:15:00Z),
  then 2026_05_TB_DAL (2026-10-09T00:15:00Z) and the week-5 slate. Requires the full chain
  (plan, registration, freeze packet binding §7 open items, A7, your typed GO) before that
  kickoff — tight but feasible; missing it costs only that one game.
Option B — register soon (this week, after preparation):
  Consequence: week-5 slate (from 2026-10-09) becomes the first prospective window; ~15–16
  games/week accrue thereafter; nothing else changes.
Option C — do not open now:
  Consequence: PREP stays PREP_COMPLETE_PENDING_OWNER_DECISIONS; no predictions recorded; no
  budget consumed; every passing week's games remain NOT_RUN prospective (evidence forfeited,
  integrity unaffected).
Default fail-closed state if no decision: Option C.

Exact action that becomes authorized by your decision: controller registers the successor
cycle via researchctl (fresh cycle_id, e.g. NFL-WINPROB-NG-SCORED-V1 — name is yours),
bootstrap plan inheriting this packet's draft, lanes for train-internal selection, freeze,
A7 prelaunch; you type the GO phrase at that cycle's own gate. The prediction ledger
(nfl_ng_ledger@1) then opens with a real GENESIS and records p_home rows strictly before each
kickoff UTC.

Actions that remain forbidden regardless of choice: retrospective predictions for any played
game (63 games incl. all of weeks 1–4 played to date are NOT_RUN prospective forever); S1;
paper/live; betting; data purchases; push/merge to main; scoring without typed GO.

Measured facts behind this packet: recount 2026-10-05T07:16:19Z (lane A r1), independently
reproduced 07:23:28Z (verifier r2): 272 scheduled / 63 played (all final) / 209 future (0
scored) / earliest future kickoff 2026-10-06T00:15:00Z ATL@NO. Power: 1-season MDD(80%)
0.026–0.056 starves plausible 0.002–0.010 effects — strong conclusions need ≥2 completed
prospective seasons (~540 games); see FREEZE_PACKET_DRAFT.md §6.
