# A7 PRELAUNCH AUDIT — ETHUSDT-OPEN-SEARCH-V2 (fresh context, recompute-from-bytes)

- audited_at_utc: 2026-09-25T03:50:23Z
- auditor: A7 (independent, fresh context; mandate = try to REFUTE the prelaunch claim)
- audited HEAD: `05790ce7bfba8aa6d98e477d4b5a563c80be52ec`, branch
  `orca/ethusdt-open-search-v2-integration`, working tree clean (verified).
- V1 reference: `.worktrees/ethusdt-open-search-v1/integration` @ `8196e3eafd548b747a217f0acf6bf468e272324e` (read-only).
- Authority: `plans/PLAN_ethusdt_open_search_v2.md` (read in full).
- Audit artifacts written ONLY under `research/control/ethusdt_open_search_v2/audits_a7/`.
  Reproduction runs (dry-run, freeze rebuild) were executed in a sandbox copy
  (`/tmp/a7eosv2/sandbox`, `data_local` symlinked read-only); no freeze file in
  the real namespace was modified or re-stamped. `scored` mode was attempted in
  the sandbox (refused, exit 2) and would refuse identically in-place because
  `audits_a7/go_authorization.json` does not exist.

## A. Engine inheritance honesty — PASS

`scripts/eosv2_engine.py` (546 lines) vs V1 `eos1_engine.py` @8196e3ea (480 lines).
Block-by-block byte comparison (22 shared top-level blocks):

- Byte-identical (19): `TIERS`, `BLOCK_SHUFFLE_BARS`, `FOLDS`, `SERIES_ETHUSDT`,
  `SERIES_BTCUSDT`, `SERIES_FUNDING`, `_norm_ts`, `_is_int`, `load_1h`,
  `load_funding`, `to_h4`, `sma_states`, `sign_states`, `pct_rank_states`,
  `InfoSeries`, `shuffle_blocks`, `spearman`, `fold_of`, `PriceAtSettlement`,
  and the `run_book` body including the full cost kernel (fee=tier*5bps/side,
  adverse tick=tier*0.01 both legs, measured-funding settlement at floor-hour
  1h OPEN, force-flat at fold boundary close, one-bar lag).
- Differing (3), all allowed deltas: `run_book` block = ARMS_DESC table swap
  (E1/E2 → EOSV2-A/B, descriptions match plan §1 ladders exactly);
  `build_all_series` = ratio loader removed, 4 alt loaders added;
  `build_targets` = rvol/breadth gate construction, `combine` (A1 AND A3),
  shuffle seed prefix `eos1|` → `eosv2|` (plan §1 seed law), diagnostics keys.
- New-in-V2: `rvol_states`, `breadth_states` (see B). Only-in-V1: none.

No silent change to cost, folds, PIT, funding or force-flat laws.

## B. New constructors — PASS (1 LOW docstring finding)

`rvol_states(closes, vol_win, qual_win=2190, q)`:
- Warmup measured from staged bytes: first defined state exactly at index
  `vol_win + qual_win` — 2370 bars (2021-01-30T00:00Z) for vol_win=180,
  2730 bars (2021-03-31T00:00Z) for vol_win=540, from BTC floor 2020-01-01.
  Fixture golden `st[2369] is None and st[2370] is not None` agrees.
- Strictly-below law: `1 if rvol[i] < thr else 0` (fixture: flat prices → all 0
  after warmup, exactly the degenerate case; vol-halving tail → 1).
- Trailing quantile window is exactly the prior `qual_win` rvol values
  (`rvol[i-qual_win:i]`, current bar excluded — PIT-safe), fixed index
  `k=int(q*(n-1))` on a sorted window → deterministic.
- Determinism: full `build_all_series()+build_targets()` rebuilt twice — all
  target series byte-identical.
- LOW finding: docstring says "std of log returns"; implementation is std of
  simple returns (`c[i]/c[i-1]-1`). Deterministic and population-std (÷vol_win);
  plan §1 says only "rvol(180 H4 closes)". Non-blocking; record as the frozen
  reading.

`breadth_states(per_symbol_states, h4_ts, threshold, min_eligible=3)`:
- Counts only symbols with a DEFINED state at the boundary (`states.get(ts)`
  None → skipped from both cnt and elig); gate = 1 iff cnt>=threshold AND
  elig>=min_eligible; elig==0 → None; 0<elig<min_eligible → 0 (flat). Fixture
  verifies the min_eligible law.
- PIT: per-symbol reads go through `InfoSeries.state_at` (last-observed,
  bisect-right, hold-previous) built from each alt's own H4 SMA states, plus
  the byte-inherited one-bar `shift` before acting. A symbol's state read at
  boundary ts uses only that symbol's bars with open_ts <= ts — the same
  close-at-decision-instant / act-next-open law byte-inherited from V1.
- Independent naive recomputation straight from 1h bytes at B1's first
  decision boundary 2020-04-06T12:00Z: SOL undefined (floor 2020-09),
  BNB/XRP/ADA defined and above own SMA200 → count 3/3, elig 3 ≥ floor →
  gate 1. Matches the plumbing exactly; no lookahead path exists.
- B3 "== 4/4" implemented as threshold=4 over 4 symbols ⇒ exactly 4 (all
  four defined); B4 = SMA600 basis, threshold 3. Matches plan §1 ladders.

## C. Lane-A kill lawfulness — PASS (1 LOW wording finding)

- Plan §3: "floors ≥100 scored bars per fold per arm". feasibility.py
  implements the per-arm reading as decision bars (target != 0) per fold,
  alongside the fold-level floor (fold_bars F1..F4 = 2916/3660/4386/3648, all
  ≥100). The per-arm reading is the conservative one and matches V1's
  feasibility metric (`census_book` structure is V1-inherited).
- RECOMPUTED populations (my own code, staged bytes, engine imported from the
  audited tree) match `freezes/feasibility.json` exactly:
  EOSV2-A1 F1=28, A2 F1=0, A3 F1=0, A4 F1=0 — all < 100 → NOT_RUN_THIN.
  Lane B F1 = 1513/1846/422/1327, per-fold min across lane B = 422 ≥ 100.
  Warmup root cause verified: A1 state defined only from 2021-01-30 (2370-bar
  warmup); Feb–Apr 2021 BTC rvol sat above the trailing-1y median almost
  everywhere (28 quiet H4 bars); stricter A2 (p40) and A3 (540-bar window,
  first defined 2021-03-31) get 0.
- Kill is pre-PnL: feasibility output contains flips/counts/spearman only — no
  price-dependent outcome anywhere; fold population floor was added to the
  committed feasibility.py/runner between bdd1e1a3 and HEAD (pre-outcome,
  plan-law implementation, not an amendment to folds/gates/ladders).
- Zero-denominator exclusion verified in code (`run_all` skips lane-A arms AND
  their G6 controls before any `run_book`), in the reproduced dry-run (zero
  lane-A record IDs; `not_run_thin_arms` lists all four), and in scored mode
  (cells marked NOT_RUN_THIN without computation).
- LOW finding: the freeze's `lane_a_disposition` says "rvol warmup 2370 H4
  bars ~395d exceeds F1 end 2021-04-30" — arithmetically wrong (395d from
  2020-01-01 = ~2021-01-31 < F1 end). True cause = warmup truncation of the
  F1 defined-state window to ~90d, then near-absence of quiet-BTC regime →
  28/0/0/0. The populations (the operative kill evidence) are correct.

## D. Dry-run hygiene — PASS

- Re-ran `run_scored.py dryrun` in the sandbox: 48/48 computations,
  expected = eligible(4)×3 + refs(4)×3 + controls(4×2)×3 = 48, delta 0,
  IDs pairwise distinct, leak scan clean, pass=true. Sandbox output is
  semantically identical to the frozen `dry_run.json` (only built_utc differs).
- Independent leak scan (my own wordlist incl. price/cost/win/loss/cash) over
  the whole file: only contract metadata hits (`"real_pnl": false` key,
  "pre-PnL" prose in the NOT_RUN_THIN status). Books payload contains ZERO
  floats — every value is an integer count or bool.
- Non-vacuity: every lane-B cell (and every control/reference except
  BASE_CASH, which is exempt by law) has fills > 0; lane-B cell `decisions`
  counts equal the recomputed feasibility populations; bars = 14610 everywhere;
  16 book-families × 3 tiers = 48 records.

## E. Freeze chain — PASS (1 MEDIUM custody finding)

- All 8 files hashed in `eosv2_freeze.json` verified against current bytes
  (`shasum -a 256`): eosv2_engine cf1f36d5…, run_scored 974111c5…, stage_all
  5d96cad6…, test_fixtures c4307701…, staged_manifest f02c87e7…, census
  08899a9c…, feasibility 14f328eb…, dry_run 08446a63… — ALL MATCH.
- Freeze reproducibility: re-derived every builder-produced key with the
  committed make_freeze.py logic → byte-equal (arms digests, gates_verbatim,
  code/evidence hashes, budget, verdict_enum, go_phrase, references,
  posthoc_disclosure). MEDIUM finding: the freeze contains two ADDITIVE
  records — `engine_inheritance` and `lane_a_disposition` — that the committed
  builder cannot emit (it was not in dirty_paths at freeze time either), so
  the artifact is not fully byte-reproducible from committed code. Content of
  both records is corroborated by feasibility.json (recomputed) and by this
  audit's A-check; hashes all verify; non-blocking.
- Freeze `tree` records HEAD bdd1e1a3 + dirty paths (feasibility.py,
  run_scored.py, freezes/, data_local) — self-consistent with a freeze built
  pre-commit at 03:32:34Z; the committed files at 05790ce7 hash-match the
  freeze, so the frozen content IS the committed content.
- `lane_a_disposition` + `engine_inheritance` records present as required.

## F. Fixtures — PASS

`tests_py/test_fixtures.py` run in sandbox: exit 0, "ALL FIXTURES PASS",
53 PASS checks (claim said 52 — trivial count discrepancy in prose).
Groups 1–11 are the V1 suite (H4 resample, SMA/sign/pct-rank goldens,
costs-once arithmetic, funding sign, force-flat, truncation invariance,
shuffle determinism, no-lookahead, tier scaling, settlement PIT law E-1,
gates plumbing). Group 12 (NEW) covers rvol degenerate strict-below,
vol-halving positive, zigzag, warmup-None-until-2369, breadth counts >=2 / ==3,
and the min_eligible floor — as required.

## G. Plan conformance — PASS

- `gates()` in run_scored.py is byte-identical to V1's (the full runner diff
  contains only: header, engine import, GO phrase V2, `eligible_arms()` +
  lane-A exclusion + NOT_RUN_THIN cells, schema names, V2 verdict names).
  G6: controls must NOT out-earn @1.0x, ties pass (`not shuf > net`).
  G7: fills@1.5x ≤ 10000 AND 2-adverse-tick execution cost per round trip in
  bps of avg raw fill price (ES1 semantics per A7 F-1 precedent; fees remain
  inside net) — unchanged from V1. G1–G5, G10 identical; G11 disclosure-only
  from feasibility.
- GO phrase exact: "GO ETHUSDT OPEN SEARCH V2 SCORED EXECUTION" (plan §0,
  freeze, runner all equal).
- Scored mode attempted WITHOUT `audits_a7/go_authorization.json`:
  "REFUSED: no audits_a7/go_authorization.json (STOP-1 owner gate not passed)",
  exit 2, nothing computed, no scored/ artifact created.
- Verdict enum: freeze `verdict_enum` = plan §7's five strings exactly; runner
  emits the two outcome verdicts (V2-named) and records NOT_RUN_THIN cells.
- scoreable budget: 4 scored cells ≤ 8 max.

## H. Ancestry / novelty adjudication — NO VETO

Dead map consulted (FAMILY_FAILURES.jsonl, 100+ entries; V1 terminal phase
record; plan §1): EOS1-E1 fences "BTC-price-state transforms (SMA/sign/drawdown
variants) as ETH long/flat gates"; EOS1-E2 fences "relative-strength-ratio
gating … in all pair variants"; ES1-VOLMAN-LONG = inverse-vol SIZING;
XSECT-TSTREND = rank-based cross-sectional portfolios; V17 "breadth" entries
are equities correction-drift breadth and SOL ticket-mix fragmentation —
neither is an alt-price breadth count.

- Lane B tuple = absolute-threshold COUNT of {SOL,BNB,XRP,ADA} above own
  SMA200/600(H4) states gating single-asset ETHUSDT long/flat. No second leg,
  no ranks, no ratios, no price-state-of-BTC, no sizing law. Absent from the
  dead map → genuinely new (observable, vehicle) tuple. Adjudication caveat
  (disclosure, not veto): G11 spearman vs BASE_TREND_LF = 0.63/0.66/0.45/0.46 —
  lane B is substantially ETH-trend-correlated, so its incremental value is
  exactly what G3/G10 must demonstrate at scoring; the gates stand.
- Lane A design, for the record: BTC realized-VOL state as a binary gate on
  ETH is distinct from dead ES1-VOLMAN (which SIZED books by the traded
  asset's own vol via inverse-vol scale) and from dead EOS1-E1 (price-level
  states, not second-moment states). Lawful to have tried; it died by the
  frozen floor pre-PnL, correctly recorded NOT_RUN_THIN. Any future re-entry
  (e.g. longer BTC history) is an owner-level new-tuple decision, not a
  parameter rescue.

## I. Registry — PASS (1 LOW V1-side finding)

- ETHUSDT-OPEN-SEARCH-V2: PLANNED_NOT_STARTED, budget 0/8, head 0000000
  (unconsumed), S1 SEALED_UNTOUCHED, go_phrase_state REGISTERED_NOT_CONSUMED.
  Correct pre-STOP-1 state.
- ETHUSDT-OPEN-SEARCH-V1: TERMINAL, go DEAD (consumed), phase text records
  NO_INCREMENTAL_VALUE with "budget 8/8, 24 observed+published computations".
  LOW finding: the structured registry field `budget.used` = 0 for V1 —
  inconsistent with its own phase narrative (8/8). V1-side bookkeeping
  (outside my namespace); does not gate V2, whose own 0/8 is correct.

## Additional findings (claim-accuracy / hygiene)

- MEDIUM (plan conformance): 552 raw data_local/vision zip files are
  git-COMMITTED at HEAD, contradicting plan §9 "Raw bytes gitignored" and the
  dispatch claim "data_local/vision gitignored". V1 precedent: its worktree
  also tracks 329 raw files. No integrity impact (bytes sha256-pinned in
  staged_manifest.json and cross-checked 80/80/80 vs V1 — independently
  re-verified by me: 80/80/80 match, 0 mismatch); provenance is if anything
  strengthened. Non-blocking; registry note recommended.
- LOW: `census.py` latent dead check — guards against status string
  "UNAVAILABLE_ES1_MANIFEST" but the code emits "UNAVAILABLE_V1_MANIFEST" (had
  the V1 manifest been absent, BUILD_PASS would not have failed closed).
  In this run the manifest existed and I re-verified the cross-check
  independently, so no impact. Also `ethbtc_scored_gap_detail()` is defined
  but never called (harmless — ETHBTC is not a V2 series).
- INFO: feasibility.py docstring says "FAIL-closed … fold population floor
  breach" but arm-floor breaches are recorded as arm_floor_failures
  (cycle stays feasible with eligible arms) — the implemented behavior matches
  plan §3's per-arm NOT_RUN_THIN concept; docstring overstates.
- INFO: stage_all.py/make_freeze.py carry V1 copy artifacts (comment
  "research/control/ethusdt_open_search_v1", manifest schema
  "eos1.staged_manifest@1"). Cosmetic.
- INFO: commit message prose "lane B populations 422-2733" — actual per-fold
  max is 2600 (B2 F3); 2733 appears in no artifact. "fixtures 52 checks" —
  actual 53. Commit-message prose only; artifacts are the authority.

## Verdict

AUTHORIZED_FOR_STOP1 — 0 blocking findings. Engine inheritance is honest
(cost/fold/PIT laws byte-inherited from 8196e3ea with only the declared
additions); the new constructors are correct, deterministic and PIT-safe;
the lane-A kill is lawful, pre-PnL, and reproduces from raw bytes
(28/0/0/0 < 100); the freeze chain verifies and the frozen dry-run is exactly
reproducible with lane A absent; fixtures pass; gates/GO/verdict law matches
the plan; lane B is adjudicated genuinely novel (no veto) with its
trend-correlation disclosed for G3/G10 to adjudicate; the registry is in the
correct pre-GO state. Scored mode refuses without the owner's typed
go_authorization.json.
