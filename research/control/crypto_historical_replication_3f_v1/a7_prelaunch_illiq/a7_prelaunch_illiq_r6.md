# A7 prelaunch ILLIQ — round 6 delta audit (r5 B2 remediation)

- Schema: `chr3f_a7_prelaunch@1`, round **6**
- Audit UTC: 2026-09-24T03:43:20Z
- Lane HEAD: `4fc94350152f29f8f9ad2c4a75e96e3fbded8a65` (`orca/crypto-historical-replication-3f-v1-integration`)
- Root HEAD: `8ec3965d2e0c4342e798c6d8ffee425085885d44` (main — bootstrap/owner space)
- Supersedes: r5 REFUSED at the same path (r5 finding **B2**: the S0R fold got ZERO funding — the cell
  runner hardcoded funding root `scan_2026` whose coverage ends 2024-08-20T00:00Z; the covering
  A-window root `scan_2026_a` was never read, so the disclosed S0R DIAG −0.589 was funding-free).
- Delta scope: B2 remediation only. Everything recomputed from bytes; nothing trusted.

## Verdict: **AUTHORIZED**

B2 remediation verified in full; wiring correct for both folds; no regressions. Zero blocking findings.

## What was verified (9 checks, all PASS)

1. **Per-fold funding wiring (C1).** `illiq_scored.py` FOLDS rows are 5-tuples carrying a funding root:
   Y2024P→`funding_data_scan/scan_2026`, S0R→`funding_data_scan/scan_2026_a`; the launcher passes
   `--funding-scan` per cell (line 54). `illiq_cell_runner.py` declares `--funding-scan` required and
   binds `SCAN = a.funding_scan` **after** `a = ap.parse_args()` (lines 24-25). The earlier scrambled
   binding order is proven and fixed in commit `b94e9d5b` (diff moves `parse_args()` above the SCAN
   assignment). Wiring commit `2404f5d4` touches only the two wiring files + the r5 verdict JSON.
2. **Funded S0R DIAG is funded (C2).** `illiq_diag/S0R-ANCHOR-A5-funded/results/artifact.json`
   (sha256 `22fc7e48…`): `funding_sum = +0.026254351928` — **nonzero**. `net_return_sum −0.563057513256`,
   `position_pf 0.782120763557`, `max_drawdown 0.601152076924`, `n_positions 336` — all match the
   disclosed numbers exactly. Internal identity reconciles to the last digit:
   price_pnl −0.580743409342 + funding 0.026254351928 − costs 0.008568455842 = net −0.563057513256.
3. **Run completeness + position identity (C3).** Log tail shows the completed rc path with result
   sha `8c8e1242…`. Positions are identical between funded and funding-free runs (price_pnl, costs,
   n_positions 336, n_days 52, hit_rate 0.25 all equal); the net delta is exactly the funding layer:
   −0.589311865184 + 0.026254351928 = −0.563057513256. Since `scan_2026` has zero rows in
   2024-08-22..2025-08-21 and `scan_2026_a` is the only root covering that span, a positive funding_sum
   on identical positions proves the run read `scan_2026_a` over the S0R window.
4. **Funding coverage (C4).** Measured min/max fundingTime over all 20 symbols: `scan_2026`
   2020-07-01..2024-08-20T00:00Z (covers Y2024P end 2024-08-19); `scan_2026_a`
   2024-08-20..2026-08-21T23:00Z (fully covers S0R 2024-08-22..2025-08-21 +3d). Contiguous join at
   2024-08-20. Early starts for BOME/ENA/ACE/ONG are listing dates, not gaps.
5. **Both DIAG versions preserved (C5).** Funding-free `S0R-ANCHOR-A5` intact (funding_sum 0.0,
   net −0.589311865184, sha `8f823d11…`) alongside `-funded`. Funded small-json shard committed under
   `illiq_diag_summary/shards/S0R-ANCHOR-A5-funded/` (commit `4fc94350`); byte-identical copy of the
   funded artifact at `illiq_diag_summary/results/artifact.json`; bulk stays machine-local per layout law.
6. **Root disclosure (C6).** Root
   `research/control/CRYPTO-HISTORICAL-REPLICATION-3F-V1/bootstrap/amendment_a4_illiq_outcome_exposed.md`
   §"A5-funded DIAG (post A7-r5 B2 remediation, disclosed to owner 2026-09-24)" carries the exact funded
   numbers; committed at root main `8ec3965d`. The same file documents owner decisions A4/A4b/A5 —
   outcome-exposure accepted and S0R authorized by the owner before this audit.
7. **Engine byte-identity to `c97283e0` (C7).** `recovered/` is gitignored, so the comparison was done
   blob-by-blob against the `c97283e0` tree (`research/`, 484 blobs): **123/123 present on-disk files
   byte-identical, 0 diffs**; extras are `__pycache__/*.pyc` only; the 361 absent tree files are bulk
   records/scratch with no runtime `.py` missing; all 10 runtime-critical ILLIQ-path modules
   (`hyp_a8_m01`, `adapter_v10/{runner,protocol,stress,converters,base}`, `v11 illiq_amihud plugin`,
   `protocol/{registry,metrics,manifest}`) present and matched.
8. **Y2024P unaffected (C8).** The launcher passes `scan_2026` for Y2024P — the same root the runner
   hardcoded pre-fix. Coverage math holds (window end 2024-08-19 < 2024-08-20). Prior
   `Y2024P-ANCHOR-A4` DIAG (funding_sum 0.0204, nonzero) preserved and valid.
9. **State gates (C9).** 0 ILLIQ scored cells (13 status rows all rc=1/null; no cell dirs under
   `illiq_scored_out/`); XSECT 8 rc=0 rows; budget 8 used + 4 ILLIQ pending = **12 ≤ 24** (amendment
   A4b/A5); launcher self-gate intact (reads this verdict path, exits 5 unless AUTHORIZED); boundaries
   clean (remediation commits touch only cycle control files; root commit only the bootstrap amendment).

## Non-blocking findings (5)

- **N1** (carried r5): dead duplicate `"rc": 0` key in the status-row literal (`illiq_scored.py` line 65,
  overwritten by line 72). r5 asked for removal with B2; still present. Behavior correct.
- **N2** (carried r5): heavy-lock registry stale RUNNING row pid 71445 (dead, heartbeat
  2026-09-24T01:42:23Z, flock free) — `locks inspect` = CONTROL_STATE_DRIFT. Reclaim per round-2
  discipline **before** the scored sweep or the acquire may refuse. Never killed by inspection.
- **N3**: `a7_prelaunch_illiq_r5.md` is untracked in the lane (r3/r4 mds are tracked). Commit with r6 files.
- **N4**: tracked funded-DIAG evidence is a 4-line shard descriptor only; the full artifact digest
  (sha256 `22fc7e48…`) should be recorded in a tracked file as optional hardening.
- **N5**: root `plans/CYCLE_REGISTRY.json` CHR3F row is stale (predates A4b/A5 and r5; budget.used 0);
  the 12/24 law lives in the bootstrap amendment. Refresh at the next registry write.

## Owner path

The ILLIQ scored sweep (4 cells = {Y2024P, S0R} × {ANCHOR, INV}) may now be launched via
`illiq_scored.py`; the self-gate is satisfied by this AUTHORIZED verdict. Resolve N2 first.
S0R outcome is outcome-exposed AND funding-complete: funded net −0.5631 (funding +0.026), loss story
unchanged from the disclosed funding-free −0.5893; these results remain non-preregistered evidence forever.
