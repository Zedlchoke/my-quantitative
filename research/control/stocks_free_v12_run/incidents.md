# STOCKS-FREE-V12 incidents (append-only)

## INC-V12-1 — P0 lane agent died post-compute (infra); A1 completed the artifact (2026-09-08)

- What: the background P0 A2/A3 lane agent (dispatched 01:10Z from e0dcb0f)
  died at ~01:32Z with an infrastructure error ("Cannot connect to API:
  write EPIPE", duration ~20.3 min) AFTER its census compute had completed
  cleanly. It never wrote the final artifact nor its commit.
- Evidence the compute itself finished: round-2 heavy-lock registry entry
  `STOCKS-FREE-V12 / P0_CENSUS_LANE / FINISHED`, acquired 01:24:03Z,
  released 01:27:08Z, release_note "2 independent full passes; digest
  e1f98aa49d837426..; determinism=BYTE_IDENTICAL"; `.staging_sec_v12/
  lock_run.log` shows EXIT=0, both passes digest-identical, lock released
  FINISHED; no orphan census process remained.
- A1 completion path (V11 INC-V11-2 precedent: lane interrupted, A1
  completed, disclosed): artifact
  `research/control/stocks_free_v12_run/p0_v12_structure_death_census.json`
  assembled by A1 from the lane's staging bytes VERBATIM (summary embedded
  unmodified; sha256 re-verified against both pass digests); the Step-0 pin
  re-verification the lane asserted but never recorded was re-executed and
  evidenced by A1 post-compute (4/4 MATCH, digests identical to A1's
  pre-compute verification at 00:58Z; input mtimes unchanged Sep 5/6).
- Verdict-neutral by construction: no numbers were produced by A1; A1 only
  embedded lane bytes and added verification/lock/incident/verdict-wording
  sections. Lane-2 fundability deliberately NOT promoted to PASS
  (liquidity/cost-ceiling cheap-kill belongs to A9-F per owner reminder).
- Commit: 1bc3df814b700fe9b33154b4fa1b6534952c1360 (artifact + the lane's
  .gitignore staging line only).
