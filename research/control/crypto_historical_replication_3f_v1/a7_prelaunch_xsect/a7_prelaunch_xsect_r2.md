# A7 prelaunch audit — round 2 (delta) — XSECT-FUND-CARRY-7D

Cycle CRYPTO-HISTORICAL-REPLICATION-3F-V1 · audit_utc 2026-09-23T21:14:56Z
Root head `232b4733` · worktree head `98fad8b4` (the A7-r1 remediation commit)
Artifact: `a7_prelaunch_xsect_r2.json` (schema `chr3f_a7_prelaunch@1`, round 2)

## Verdict: AUTHORIZED

R1's single blocking finding (B1: funding data plane could not feed the frozen
loader) is remediated and verified on the real data path. Everything r1
reproduced clean still reproduces clean at the moved head. Denominators and
boundaries intact: budget 0/24, no scored records anywhere, S1 sealed, GO
unconsumed.

## Blocking remediation — recomputed from bytes

1. **Bundles (PASS).** All 8 XSECT bundles
   `funding_data_scan/scan_2026/<SYM>/funding.json` now carry
   `requested_start_ms=1593561600000` / `requested_end_ms=1724112000000`,
   exactly equal to the staging `window` fields, and their `rows` are
   byte-equal to `staging/funding/<SYM>_funding.json` (structure equality AND
   identical canonical-serialization sha256; counts 4534/4385/4534/4534/4506/
   4534/4534/4534). Every row `fundingTime` inside the window. Extended
   sweep: all 20 regenerated bundles pass — the record's "all 20" claim is
   true.
2. **Frozen loader (PASS).** Ran `research.funding_pit.load_funding_bundle`
   from `recovered/v6_root` myself on all 8: zero exceptions, rows > 0,
   first/last settlement within `[requested_start_ms, requested_end_ms]`.
   The r1 `ValueError: missing audit metadata` failure mode is gone.
3. **Real-data-path shape driver (PASS, reproduced).** The driver calls the
   frozen `compute_target_weights_funding_carry` with exactly its true
   keyword-only signature. I re-executed its computation independently
   (stdout only, controller artifact untouched): every fold statistic
   reproduced exactly — Y2021 362 stamps/0 skips/124 digests, Y2022
   363/0/96, Y2023 364/0/128, Y2020P 88/0/38 — verdict PASS. 0 skips means
   the frozen kernel returned status OK, never SKIP_INCOMPLETE, from the
   regenerated bundles; >1 distinct weight digests per fold proves
   non-constant weights. Shape-only confirmed by code inspection (no
   PnL/orders/equity). The 7-symbol traded set matches plan §2 ("BTC
   benchmark only").
4. **Remediation record (PASS).** All three claims match recomputed bytes.

## No regression since r1

- Root: only commit since r1's head is `232b4733` — registry-only, another
  cycle's row (EURUSD), disclosed control-plane. Worktree remediation commit
  `98fad8b4` touches exactly the 3 remediation artifacts.
- Identity spot-checks at current HEAD all reproduce r1: frozen surfaces
  (`funding_carry`, `matrix_runner`, `funding_pit`) diff-empty
  closure..HEAD and sha-identical root↔recovered; candidate.yaml untouched
  since closure; status.yaml pinned at `5b1415e7`; identity pin `845c3e87`
  matches; `portfolio_runner.py` sha `4711257f…` matches the r1 pin.
- Denominators: registry 0/24; only the DR2 dry-run row (REJECTED, not
  scored) exists; no `chr3f_scored` anywhere; staging and root `results/`
  clean; events ledger has no scored entries.
- Locks: history is exclusively 3 CHR3F `data-staging` rows (FINISHED);
  one stale RUNNING row (dead pid) → `CONTROL_STATE_DRIFT`, flock free —
  hygiene, reclaim-only per discipline.

## Scored invocation conformance (plan §3/§6)

`chr3f_xsect_scored.py` windows match §3 exactly (Y2021/Y2022/Y2023 full
years, Y2020P from 2020-10-05 per the pre-launch census PASS); 2 arms
ANCHOR + INV `--reverse`; `--folds 3`; lookback 7; 8 cells = 4×2 inside the
A2 XSECT share; cycle-local registry/outputs; heavy lock per cell. The
launcher refuses to run unless this r2 artifact reads AUTHORIZED, then
self-stages the `funding_data` and `catalog_live_crypto` symlinks and exits
hard if the funding link is broken. Cells will run against the regenerated,
loader-compatible bundles. Invocation otherwise unchanged from the r1 packet.

## Non-blocking notes

N1 launch symlinks now self-staged by the launcher (carried from r1 N1,
weakened) · N2 registry row head/phase lags the remediation commit
(hygiene) · N3 stale heavy-lock RUNNING row (dead pid, flock free) · N4
shape driver starts at each fold's first Monday, leaving the first 1–3
daily stamps per fold unproven by the driver (covered by warmup + fold
census) · N5 controller delivered shape-only driver per the r2 dispatch
instead of r1's sketched PnL dry-run — intent met within scope · N6 dead
`BENCH` variable in the driver (cosmetic).

Audit-only: no files outside `a7_prelaunch_xsect/a7_prelaunch_xsect_r2.{json,md}`
were written.
