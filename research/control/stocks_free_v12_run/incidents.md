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

## INC-V12-2 — cosmetic placeholder timestamp in A4 hashes file (2026-09-08)
`d1_a4_proposal_hashes.json` carried `built_at_utc: 00:00:00Z` (predating its
own wave commit — impossible). A1 corrected to the real time with an in-file
note; proposal hashes unchanged (re-verified byte-equal). Found by A1 at
integration; also raised by A7 terminal as F-6-adjacent LOW.

## INC-V12-3 — D2 lane agent infra death, module survived (2026-09-08)
Second API-infra death of the cycle (connect timeout ~52 min). The lane had
written the complete module (100,251 bytes, V11-skeleton disclosure) and its
lock wrapper, but never acquired the lock (registry has no D2 entry from it)
and never ran the measurement. A1 completed the run (see INC-V12-4).

## INC-V12-4 — D2 module one-line defect, fixed by A1 pre-run (2026-09-08)
`feasibility_block` crashed at first real run: `grid_dates_flat` returns
`date` objects, line 1584 wrapped them in `dd()/fromisoformat` → TypeError.
One-line fix (drop the wrapper; downstream uses the date as a dict key
consistently). Disclosed in the D2 commit message; after the fix the module
ran 2 passes BYTE_IDENTICAL (digest c3e27a88…) and A7's independent re-run
reproduced the measurement content-exact.

## A7 terminal verdict + findings disposition (2026-09-08)
A7 fresh-context `STOCKS_FREE_V12_TERMINAL_CONFIRMED_BLOCKED_DATA_OR_SELECTION`
(audit commit cc85fc5bd24aaacbc868563912cf3125fd18e195; 19/19 chain SHAs, P0
pins re-hashed MATCH, 121/121 kernel byte-exact + 41/41 kernel tests, D2
re-run under lock content-exact vs recorded bytes, A6 grep reproduced 6/11/0/0
vs 337,241, kill logic confirmed under frozen bars, counters/law/label PASS).
Findings disposition by A1:
- F-1 HIGH (process-only): staged registry rows A4-H1/H2 carried invalid code
  `D2_NOVELTY_BLOCK` → corrected to validator-known `ANCESTRY_RHO_BLOCK`
  (content unchanged, marked in-detail); appended-copy validation in the
  worktree: 61 entries, 0 errors → PASS. Lead's root append can proceed
  verbatim.
- F-2 MEDIUM: terminal prose said "one FAILED release"; registry shows 18
  FAILED D2 releases, all with stderr tails — evidence STRONGER than claimed;
  terminal_report.json left byte-untouched post-audit (audited artifact), this
  errata is the record.
- F-3 MEDIUM: module shadows `identifiability_weights` (dead first def) —
  A7-adjudicated verdict-invariant for all six kills.
- F-4/F-5/F-6 LOW: A6 sub-label cosmetics; INC-V12-2/3/4 now mirrored here
  per F-5; cross-run digest difference is by-construction (embedded timestamp).
