# OWNER GATE BRIEF — NFL-WINPROB-NG-SCORED-V1 (2026-10-05)

A7 verdict: **A7_PRELAUNCH_PASS** (10/10 checks, 0 blockers; notes in A7_PRELAUNCH_VERDICT.md).
State: PRELAUNCH_READY_PENDING_OWNER_GO. **The decision is yours only**: type
`GO NFL WINPROB NG SCORED V1 PROSPECTIVE` verbatim at this cycle's own gate — or decline
(no GO = nothing runs; a valid terminal). No agent may type it for you.

**On GO — week-capture mechanics (mechanical, no discretion).** The controller (single recorder)
substitutes only the two GENESIS placeholders, writes the real ledger, then appends one weekly
batch of prediction rows for all games of the upcoming week, completed >= 6h before that week's
first kickoff UTC. A week is capturable iff its batch lands on time AFTER your GO; no backfill, ever.

**Clock (UTC).** Week-5 slate opens `2026_05_TB_DAL` 2026-10-09T00:15:00Z; with the >=6h margin,
GO + first batch must land by **2026-10-08 ~18:15Z** to capture week 5. Week-4 MNF `2026_04_ATL_NO`
2026-10-06T00:15Z is **forfeit-by-design** under your Option B (week 5 is the first target); it
becomes NOT_RUN prospective forever like the 63 already-played games.

**Forbidden after GO, unchanged.** Retrospective predictions for any played game; 2019-2025 stays
SPENT cite-only; no S1; no paper/live; no publication/commercial use (CC BY 4.0 covers the data;
league/ESPN publication-commercial rights UNVERIFIED - internal research only, fail-closed); no
push/merge to main; no arm/config/threshold change after the first prospective row; no
outcome-based early stopping (decision reads once per completed prospective season; strong
conclusions need >=2 completed seasons). Budget stays 0/9 until rows accrue under frozen gates.
Evidence: `lanes/A7_PRELAUNCH/{A7_PRELAUNCH_VERDICT.md, AUDIT_EVIDENCE.md}`;
`lanes/F_FREEZE/FREEZE_PACKET.md` (§4 capture law, §6 GENESIS, §10 boundaries).
