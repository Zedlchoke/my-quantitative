# A7 TERMINAL AUDIT — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (2026-09-28)

Independent terminal auditor (fresh context; built nothing audited). Claim
under audit: A1's `TERMINAL_DECISION.md` typed close `ROUTER_STATES_THIN` at
0 scored cells — (a) preregistered floors killed every state, (b) P-29
representation-rho killed the V2 layer, PIT gates PASSED first, standing
scored-GO delegation dies unconsumed, no relaxation/substitution.

- Worktree audited: `.worktrees/portfolio-router-12assets-100k-v1/integration`,
  branch `orca/portfolio-router-12assets-100k-v1-integration`,
  `git rev-parse HEAD` = `59578b6c08bad787b5a6f074d974aa334b97edd0` (equals
  the dispatch SHA; verified). Worktree porcelain: CLEAN.
- Audit mode: read-only; recomputes from raw files with the auditor's own
  implementation (`state_engine.py`/`battery_state.py` reporting layers NOT
  imported; only the loaders data plane was used for EURUSD M1). Python:
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python` (3.12.14,
  numpy 2.5.2, pandas 3.0.5).

## 1. Independent recompute — all headline numbers reproduce

Rebuilt from raw bytes (EFFR NY-Fed JSON, CBOE VIX csv, FRED Brent/WTI csv,
EURUSD M1 via loaders): panel epoch, full 534-Friday chain from epoch,
per-Friday V1/V2/V3 evaluation, ladder, dwell, merge, census, rho battery.

| quantity | battery (committed) | A7 recompute | delta |
|---|---|---|---|
| epoch first computable Friday | 2016-04-08T17:00-04:00 | 2016-04-08T17:00-04:00 | 0 |
| calendar Fridays | 286 (2021-01-08..2026-06-26) | 286 | 0 |
| WAR_ENERGY merged eps / occupancy / candidate w | 10 / 55 / 68 | 10 / 55 / 68 | 0 |
| RISK_STRESS | 7 / 24 / 34 | 7 / 24 / 34 | 0 |
| TIGHTENING | 2 / 59 / 61 | 2 / 59 / 61 | 0 |
| EASING | 3 / 30 / 26 | 3 / 30 / 26 | 0 |
| ABSTAIN | 5 / 118 / 97 | 5 / 118 / 97 | 0 |
| raw runs (sequence of 38, dates+lengths) | JSON `raw_runs` | identical, entry-for-entry | 0 |
| merged episodes EP024–EP050 (27, spans + state_true_weeks) | JSON `merged_episodes` | identical, entry-for-entry | 0 |
| per-fold F2 (5 states x 9 folds) | JSON | identical, all 45 values | 0 |
| per-fold F3 (5 states x 9 folds) | JSON | identical, all 45 values | 0 |
| rho(v2_pct, eurusd_rv30_pct), n=271 | 0.4828124267259972 | 0.4828124263454978 | 3.8e-10 |
| rho(v2_STRESS, eurusd_rv_p80), n=271 | 0.30335437324521436 | 0.30335437324521436 | 0 |
| rho(state_RISK_STRESS, eurusd_rv_p80), n=271 | 0.21793013546206105 | 0.21793013546206105 | 0 |
| Fridays with RV undefined (short history) | 15 | 15 | 0 |
| payload_sha256 | 4a5f0fc581995d2b… | recomputed over provenance-free payload | MATCH |

All within the mandated tolerances (rho ±0.005, episodes ±1); the two exact
indicator rhos match to the last digit and the continuous rho differs only in
floating-point association order. The census is byte-level faithful, not just
numerically close.

## 2. Kill-code correctness audit (both directions)

- **RV30 series PIT-clean**: EURUSD D1 bars are close-stamped with the
  right-edge label at next-day 00:00 UTC (loaders convention); a Friday
  17:00 ET decision (21:00/22:00 UTC) samples the last D1 label ≤ decision =
  **Thursday's completed bar** (`sample_at_fridays`, battery_state.py:232-244).
  My recompute's sampled labels confirm (bar labeled 2021-01-08 contains Jan 7
  minutes). No same-day lookahead anywhere.
- **Percentile windows trailing-only**: V2 window = `v[pos-251:pos+1]`
  (state_engine.py:470), V3 same over common spreads (:490), RV30 window
  `rv[lo:i+1]` with `lo = i-251` (battery_state.py:165-169). All include the
  current value, use only strictly-older history otherwise. Weak/inclusive
  rank documented; deterministic.
- **V3 10-calendar-day rule**: cutoff `dec_date − 10d` on the Brent/WTI
  COMMON-date series (state_engine.py:482) = PIT_DOSSIER G-PIT-V3 frozen rule
  verbatim ("latest observation with date ≤ (F − 10 calendar days)").
- **V1 63-business-day delta**: positional row `now_pos − 63` over the usable
  EFFR series (state_engine.py:449), availability `d+1 15:00 ET` per
  G-PIT-V1; the positional-over-own-series reading of "business days" is
  documented in the module contract and is the natural one for a
  business-day-published series. My independent implementation agrees.
- **Dwell/merge match frozen §3.3**: min-dwell effective at the 2nd
  consecutive weekly observation; ABSTAIN bypasses dwell (effective
  immediately — no carry-forward, the fail-closed law); merge = same-state
  runs with < 4 intervening weekly observations sharing an episode_id,
  transitive closure via union-find (state_engine.py:571-611) — a faithful
  generalization of "adjacent". Merge never rewrites weekly effective states
  (episode-accounting only) — verified by the identical effective sequence in
  my recompute.
- **No computation defect found that could flip any verdict.** The one
  interpretive choice with any latitude (V2 T−1 buffer excluding the Friday
  VIX print that the bare d-16:15 formula would nominally admit) is documented
  in-code, reproduces the PIT_DOSSIER G-PIT-V2 application sentence verbatim,
  and is strictly conservative (costs staleness, never lookahead).

## 3. Tests (fresh run)

`research/pr12a100k/tests`: **33 passed** in 18.65s (14 state_engine + 19
loaders). The no-lookahead test genuinely truncates: 32 real decision Fridays
2021-2026, `compute_state(ts, panel)` vs `compute_state(ts, panel.truncate(ts))`
byte-identical JSON, plus a synthetic twin with a post-decision VIX spike
(test_state_engine.py:98-130). V3 10-day boundary, per-variable staleness,
dwell/merge hand fixtures, ladder priority, determinism all present.

## 4. Frozen laws followed, not bent

- Floors F1≥10 / F2≥2 / F3≥26 and the 0.20 rho bar are preregistered in the
  committed pre-GO docs (policy §3.5/§3.6, protocol §4/§8, plan §4 — commit
  `a51dc758`, before any census existed) and are exactly what
  `battery_state.py` enforces (constants at :76-79).
- **Zero commits after the census commit (59578b6c) touch `plans/`,
  `router/`, or `plan/`**; `git diff a51dc758 59578b6c` on the control dir is
  pure additions (pit/, battery/, MANIFEST.md). Root log shows the same.
  No floor relaxation, no variable substitution; the TIPS rho row is
  NOT_RUN-disclosed, not substituted.
- Close label: protocol §4.1 — "If ≥ 2 of 4 states fail ⇒ close
  `ROUTER_STATES_THIN`" — and §8 lists it among the preregistered close
  codes. All four tradeable states fail floors (three of them on F1 alone),
  so the close fires at 0 scored cells: with every state FLAT the router
  degenerates to the always-eligible book (B3) and any scored spend would
  price a tautology. `ROUTER_STATES_THIN` is the correct and strongest
  allowed typed close; reopening condition stated once (Q-10), as required.

## 5. F2/F3 mis-specification disclosure is sound

F1 alone (≥10 merged episodes, full set) kills RISK_STRESS (7), TIGHTENING
(2), EASING (3) — 3 of 4 tradeable states ≥ the 2 needed for the close; the
close therefore does NOT depend on the (admittedly near-impossible: F3≥26
weeks per 26-week fold = 100% occupancy) F2/F3 per-fold floors. The V2 rho
kill (0.4828 > 0.20) is entirely floor-independent. Even the sole F1 survivor
WAR_ENERGY (margin 0) could not form a router alone. Confirmed by recompute.

## 6. Boundaries

- **S1**: registry `s1 = SEALED_UNTOUCHED`; code greps for S1 access return
  only `DGS10` substring false-positives and prose stating the seal. Clean.
- **No PnL anywhere**: no PnL/equity/Sharpe computation in the engine or
  battery; no `*SCORED*`/`*PNL*` artifacts in the worktree; `measured_panels`
  is a data-plane measurement (vol/liquidity), not outcomes.
- **Budget**: registry row `used 0 / max 64`, `go_phrase_state =
  REGISTERED_NOT_CONSUMED`, workers 0 — consistent with "0 scored cells".
- **Owner directive**: recorded verbatim (Vietnamese, 2026-09-28); the
  standing scored-GO delegation was conditioned on A7 AUTHORIZED *for a
  scored execution* — with no scored subject remaining, the key dies
  unconsumed. This matches handbook §19.3/P-8 ("GO gõ sớm = intent, chết
  unconsumed"; terminal is absorbing: a GO phrase dies consumed or
  extinguished-unconsumed) and the directive's own no-substitution clause.
  Registry confirms the phrase was never consumed.
- **I1c/I1d never dispatched**: no handoffs or artifacts exist for them.
- **PIT evidence spot-checks**: evidence pages exist and carry the quoted
  text — NY Fed "approximately 9:00 a.m.", CBOE "4:15 p.m. ET (Cboe RTH
  session)", EIA "Release Date: 9/23/2026 / Next Release Date: 9/30/2026"
  (Wednesdays → weekly cadence). I independently reproduced the VIX
  dual-channel cross-check: 9,278 common dates 1990-01-02..2026-09-22,
  0 value diffs. Raw MANIFEST n_files = 50.

## Findings

- **F-1 MEDIUM — staleness constants not traceable to a committed frozen
  doc.** Engine staleness (V1 >10 calendar days, V2 >5 business days,
  V3 >25 calendar days; state_engine.py:128-130) cites dispatch packet I1b,
  which is not itself archived in the repo. The committed design draft §3.4
  (ROUTER_POLICY_DESIGN_DRAFT.md:262-266) instead says V1 >5 business days,
  V2/V3 >2 business days — arithmetically incompatible with the frozen V3
  10-calendar-day PIT rule (latest usable common obs is ALWAYS ≥10 days old,
  so §3.4-as-written forces permanent ABSTAIN — an even harder kill, 0
  episodes for every state). The engine's thresholds are the pass-favorable
  reading, the census ran with 0 stale weeks, and the states still failed.
  Verdict-safe in both directions (stricter reading only kills harder);
  flagged for provenance hygiene, not as a defect.
- **F-2 LOW — F1 window reading.** The census counts merged episodes over the
  full 286-week calendar including the 52-week warmup (policy §3.5 wording
  "full fold set (total)" supports this; protocol §4.1 says "training fold
  set"). Under the stricter test-folds-only reading WAR_ENERGY would drop
  10→6 and ALL four tradeable states would fail F1 outright. The chosen
  reading is the pass-favorable one; the close is unchanged or strengthened
  either way.
- **F-3 LOW — no trial-ledger row for the primary-config census.** Protocol
  §3 counts "the preregistered primary config (trial 1)" as a ledger row; no
  trial ledger exists yet (the evaluation lane never ran). The pending
  two-half close should add the accounting row (or record why the pre-PnL
  battery is ledger-exempt) so P-9 denominators stay reconciled.
- **F-4 LOW — rhetorical overcount.** TERMINAL_DECISION's "Five router-class
  attempts … same verdict five different ways" counts REGIME-GATED-COMBO-V1,
  whose reading is exposed-pending-owner (registry ACTIVE_LIGHT, awaiting
  owner a/b), not a terminal verdict. Not load-bearing for this close.
- **F-5 INFO — V3 cadence caveat compressed.** PIT_DOSSIER marks the
  historical constancy of EIA's weekly cadence (pre-2025-12) as
  ASSERTED-conservative; TERMINAL_DECISION says "EIA weekly-release cadence
  measured" without repeating the caveat. Direction conservative (staler
  data cannot leak); dossier-level disclosure exists.
- **F-6 INFO — drawdown-hysteresis rows degenerate.** PSV1 −30%/−10%
  constants never trigger on 2021-2026 FX majors (0 risk-off weeks, all 5
  symbols) → rho undefined, reported `degenerate_constant_series`, not PASS.
  Honest handling; the V2 kill rests on the three measured rho rows.
- **F-7 INFO — registry head lags worktree.** Registry row head `a63d053d`
  vs worktree HEAD `59578b6c` (two commits: D1+I1a, I1b). The
  TERMINAL_DECISION's in-flight next steps already include the registry
  head/TERMINAL flip in the pending two-half close; not a drift incident at
  audit time, but it must land with the close.

## Conclusion

The negative close is real, not a false kill: every census number and every
rho reproduces from raw bytes under an independent implementation; the floors
and the rho bar are preregistered, committed before the census, and untouched
after it; the engine's interpretive choices all run in the anti-kill
(conservative) direction and the kill survives them; the tests genuinely
enforce the no-lookahead law; S1/budget/PnL/two-key boundaries are clean.
`ROUTER_STATES_THIN` at 0 scored cells is the strongest allowed typed close
under the frozen protocol.

A7_TERMINAL_VERDICT: CONFIRM
