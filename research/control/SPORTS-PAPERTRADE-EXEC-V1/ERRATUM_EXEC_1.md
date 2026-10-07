# ERRATUM EXEC-1 — GO consumption mechanics + NBA status refresh (pre-GO, 2026-10-07)

Status: PRE-GO (zero real rows; the ONE GO untyped). Supersedes two items by
reference; no code changed — the two-key gate's fail-closed behavior is byte-identical.

## D-1 (closes A7-F1 MEDIUM) — where GO_CONSUMED must be recorded

`execute.py`'s `exec_go_state` reads THIS worktree's registry mirror
(`plans/CYCLE_REGISTRY.json` on branch `orca/spt-exec-v1-integration`, frozen at
branch point), while root `researchctl cycle update` writes the ROOT registry
copy. Both are lawful registry surfaces; they diverge only until synced.
**Controller post-GO procedure (mechanical, pre-authorized by the packet, no
Owner decision needed):**
1. Transcribe the verbatim phrase to
   `research/control/SPORTS-PAPERTRADE-EXEC-V1/GO_TOKEN.json` (this worktree).
2. Consume in the ROOT registry:
   `researchctl cycle update --cycle SPORTS-PAPERTRADE-EXEC-V1 --phase "GO_CONSUMED <phrase> <ts>"`.
3. Mirror the consumption into THIS worktree's registry mirror with the same
   phase text (pathspec edit of `plans/CYCLE_REGISTRY.json` on this branch +
   commit), so the file the gate reads contains GO_CONSUMED.
4. Only then run the first `run-day`. Until step 3 lands, every mutation refuses
   BLOCKED_NO_GO (verified by A7-F1 rehearsal) — fail-closed by construction.

## D-2 (closes A7-F4 LOW) — NBA status in the NOT_RUN table

The OWNER_GO_PACKET row "NBA = BLOCKED_NBA_CORPUS_BIND, NOT fixable by this GO"
is SUPERSEDED by `ERRATUM_NBA_REWIRE.md` + registry phase: NBA is wired to the
lawful ESPN-PIT path (frozen payloads only; bind path DEAD; disclosure carried
verbatim; warm-up 2016–17 carried pre-registration). Post-GO, NBA forecasts run
in the normal cadence; the first eligible batch is the 2026-10-20/21 opening
window (anchor 2026-10-20T12:50:00Z). `OWNER_GO_PACKET.md`'s table is corrected
by this reference (the packet file is not edited — this erratum supersedes by
section, house convention).

Unchanged: the ONE phrase `GO SPORTS PAPERTRADE EXEC V1 RUN ALL`; WNBA-2027
outside scope; soccer per-match NOT_RUN on missing 1X2; missed WNBA anchors
NOT_RUN forever; zero real rows; $0.
