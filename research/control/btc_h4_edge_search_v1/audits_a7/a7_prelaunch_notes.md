# A7 prelaunch audit notes — BTC-H4-EDGE-SEARCH-V1 (measured 2026-09-23T15:10Z, HEAD 9128821)

Independent fresh-context auditor. Mission: refute the prelaunch claim. I wrote
only this directory + the handoff; I repaired nothing.

## What I re-ran with my own hands (not taken on faith)

1. **C2 identity gate** — `es1_reconcile_comparator.py` under the workspace venv:
   verdict RECONCILED, exit 0, net rel-err 9.0e-10, every fold rel-err <= 9.4e-8,
   86 trades (79 DONCHIAN_STOP + 7 GATE_INACTIVE), ledger to the cent
   (177,691.82; +140,843.28 / −46,959.99 / +133,820.83 / −50,012.30). The rewrite
   of `comparator_reconciliation.json` was **byte-identical** to the committed
   artifact (diff clean), so the tree stayed clean. 1.2 s — light census, no lock.
2. **C3 fixtures** — pytest: 8/8 pass. Then I READ the tests and graded what they
   actually pin (see JSON): the no-lookahead mutation test is strong; funding
   sign/boundary is exact; the scale-cap test cheats by capping inside the test
   body (MEDIUM, F-A7-2); the band golden never exercises exit-from-long
   stickiness (LOW, F-A7-3); next-bar fill is only partially distinguishable from
   same-bar-close fill on that fixture, but the fold-level reconcile vs PSV1
   backstops fill timing hard.
3. **C6 ancestry** — re-ran `ancestry_rho.py` with the output path redirected to
   /tmp so the committed artifact stayed untouched: **byte-identical** result.
   Lane A worst |rho| = 0.090376 (PASS), lane B = 0.20509 → VETOED. The razor
   number is real. Lane C's same-family declaration is verbatim what plan §4 G11
   preregistered — honest, no novelty claim made.
4. **C5 data authority** — re-downloaded 3 sample zips straight from
   data.binance.vision (ETH 1h 2020-01, BTC funding 2023-06, SOL 1h 2026-08):
   all three SHA-256 + byte-length MATCH the manifest. Manifest has zero coverage
   holes; SOL's gate FAIL numbers (0.23% gaps, 72h run) match the freeze text
   exactly; funding spans 2020-01..2026-08 with 7,305 BTC settlements ≈ a
   complete 8h cadence.
5. **C4 dry run** — programmatic recursive walk of every key and leaf in
   `dry_run_counts.json`: zero PnL/equity/gross/fees/cash keys anywhere, 14
   non-vacuous decision paths, COMPARATOR exactly 86 entries, scale bounds ≤ 1.
6. **C7/C8** — greps: `fold_net` exists only in accounting + the identity gate;
   no year-conditioned logic; only network host in all of `scripts/` is
   data.binance.vision (keyless); no broker/order surface ("order" hits are an
   rng permutation variable). All 14 files changed since base af52f358 sit inside
   the cycle directory. PSV1/V2/TRV1 integration worktrees clean; no remote
   contains this branch's HEAD (never pushed); `data_local/` is gitignored and
   untracked. S1: nothing on this branch touches it; the sandbox is untracked in
   the root repo and I never opened it.

## What I refused to take on faith — and what broke

The one claim I refused to trust was that the frozen engine is *runnable* for
P4. I executed every public code path of `es1_engine.py`. **The lane D
measured-funding loader crashes**: `load_funding_measured()` (es1_engine.py:71)
uses `Path(...)` but never imports `pathlib.Path` — `NameError` on first call
(reproduced). P4 must price every cell AND every baseline under BOTH funding
laws (plan §3 lane D, §7 denominator); as frozen, the scored run dies at the
first measured-law pricing, or someone edits the engine post-freeze — both
unacceptable at a STOP-1 gate. I verified the blast radius: feeding an
externally built 7,305-row funding frame into `simulate(funding_law="measured")`
runs fine, so the defect is the loader plus the missing fixture, not the
simulator. It fails LOUD (crash), not silently — good — but loud-and-blocking is
still blocking. That is finding F-A7-1 (HIGH), and it alone forces
**REMEDIATION_REQUIRED**.

## Strongest-alternative check (C9)

Best self-dealing hypotheses I could construct, checked: (a) post-hoc G6
shuffle seed — the seed is hard-coded and disclosed but not plan-preregistered
(LOW, F-A7-6); (b) razor ancestry veto of lane B — independently reproduced,
and vetoing *reduces* the trial count 12→8, the anti-selection direction;
(c) measured-funding law quietly favoring a lane — it is exposure-proportional,
applied to arms and re-run baselines alike, with a rank change pre-declared a
first-class finding; no artifact contradicts that.

## Bottom line

Verdict **REMEDIATION_REQUIRED**, 1 blocking (F-A7-1: loader NameError + zero
measured-law fixture coverage). Fix is small and belongs to A1/owner: add the
import, add a measured-law funding fixture, re-run fixtures + dry run, refresh
the freeze's engine SHA — then this cycle is, on every other axis I measured,
the cleanest prelaunch package this program has produced.
