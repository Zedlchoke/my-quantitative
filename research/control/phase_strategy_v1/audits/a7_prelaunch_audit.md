# A7 PRELAUNCH AUDIT — PHASE-STRATEGY-V1

- Schema: `psv1_a7_prelaunch_audit@1` (machine-readable twin: `a7_prelaunch_audit.json`)
- Audited head: `4b7eae34f679e96857299142c1221ec39bc542f5` on `orca/phase-strategy-v1-integration`
- Audit worktree: `.worktrees/phase-strategy-v1/a7-prelaunch` @ `orca/psv1-a7-prelaunch`
- Measured: 2026-09-23T09:06:06Z, fresh context, independent
- Method: recompute from bytes and source. Raw data re-hashed from lane-worktree
  `data_staging/`; census arithmetic independently re-derived with auditor-owned
  run-length logic from raw bytes; test suites re-executed; no predecessor
  PnL-bearing artifact opened (SPY.json.gz touched by sha256 over bytes only).

## VERDICT: `REMEDIATION_REQUIRED`

Blocking: **A7-H1** (1 HIGH). Non-blocking: 2 MEDIUM, 2 LOW, 4 INFO.
Everything else the prelaunch checklist covers passed on independent
recomputation — the freeze is one cheap, pre-PnL measurement away from
re-audit. That measurement must not be waived: missing evidence is NOT_RUN,
never inferred PASS.

---

## The blocking finding (A7-H1, HIGH)

**E3 ancestry is not discharged for all three BTC_H1 arms.**

L1's census (`lane_btc_h1/census/census.json`, `ancestry.per_candidate.*`)
records `run_imbalance` as `NOT_MEASURED_WITH_REASON` — "requires
trade-direction/run-level data; not reconstructible from 1h OHLCV" — for
`PSV1-BTC_H1-UPTREND-BREAKOUT_CONT`, `PSV1-BTC_H1-ACC-FLOOR_PROVISION`, and
`PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT`.

That reason is factually wrong inside this cycle's own frozen tree:

- L2's `lane_btc_h4/pipeline/ancestry.py::shadow_series` reconstructs
  `run_imbalance` **from closes alone**: `sign(ret1).rolling(win).sum()/win`,
  daily-sampled. The identical construction is trivially expressible on L1's
  H1 closes.
- `run_imbalance` is in the plan §7.2 **BTC-applicable** dead-shadow list, and
  §7.2 obligates each lane to measure the applicable frozen shadows.
- L2's measured worst (+0.168) attaches to L2's signal series; it is evidence
  about L2's book, not L1's. It cannot be inherited.
- L1's other three NOT_MEASURED reasons (OI, OI-share/stoch, DVOL, pair) ARE
  legitimate — those observables are genuinely absent from the cell data
  contract.

Consequence: the P4 freeze declares 3 of 4 arms ELIGIBLE with E3 only
partially measured. Remediation is pre-outcome and cheap — measure the three
rhos (close-based reconstruction per L2's frozen method or an explicitly
frozen equivalent), apply the 0.20 bar, record in census + freeze, re-commit
at a new head; `|rho| > 0.20` ⇒ that arm is `ANCESTRY_VETOED`. Then a fresh
A7 pass on the delta.

## Non-blocking findings

| ID | Sev | Finding (one line) |
|---|---|---|
| A7-M2 | MEDIUM | BTC_H4 arm `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION@freeze1` has **no `arm_config_digest`** anywhere frozen — §6 identity field missing on 1 of 4 arms; L2's proposal deferred it to "A1 at integration" and A1 never added it. Deterministically derivable from frozen bytes; fold into the remediation commit. |
| A7-M3 | MEDIUM | Skip texts + integration commit messages claim BTC manifest digest verification "remains binding at scored-run/A7 time", but **evaluation_freeze schedules no such step for BTC** (only the SPY gate re-run is scheduled). BTC verification is ingest-time only; SPY is code-enforced at load. A7 has now re-hashed 6 BTC raw files byte-exact, satisfying the "A7 time" half. |
| A7-L4 | LOW | P4 freeze `not_scored` omits the BTC_H4 TRANSITION_UNKNOWN row (14/15 slots enumerated; the disposition exists in the lane's proposals as GATE_STATE_NOT_TRADABLE/FLAT). |
| A7-L5 | LOW | OWNERSHIP_MANIFEST `a7.status` stale ("NOT_SPAWNED" while this audit runs). |
| A7-I6 | INFO | SPY floor-margins use fold-truncated episode sums (23 UP / 11 DOWN); global-run counts (22/10) also disclosed; both conventions below floor on thin phases — no effect on any thin call. |
| A7-I7 | INFO | Lane test suites must run per lane (duplicate test basenames collide if combined in one pytest process). Scored-run harness should preserve per-lane invocation. |
| A7-I8 | INFO | A1 exists as `eaef65d6` (main) and byte-identical cherry-pick `b75f35f7` on the integration chain; plan bytes identical; chain intact. |
| A7-I9 | INFO | §7.1 breadth: event-conditional Donchian/breakout/floor books are distinguished from the forbidden continuous specialists by recorded pre-outcome class arguments; G6 controls test gate-informativeness. A7 terminal to re-examine. |

## What passed (independently verified — summary)

1. **Freeze/commit chain** — all 13 named digests resolve; lane subtrees
   byte-identical between lane tips and integration picks (tree hashes
   `5a6531b6`/`7f190729`/`fb5c0f32`); registry head `4b7eae34` == audited
   head; handoffs schema `zcode_orch_v3_handoff@1` with all core-16 fields;
   predecessors TERMINAL and NOT reopened.
2. **Data authority & PIT** — re-hashed 3 L1 zips + 3 L2 zips from raw staging
   bytes: all match pinned digests; SPY snapshot `3fd229f9…3803` re-verified
   byte-exact. PIT convention (knowable at close, fill next open) present in
   all three cells. The A1 catalog reclassification is **honest and
   evidence-backed**: quantitative forensics (alignment optimum +0h, close
   corr 0.9999688, diffs to -6798, volume ~12x with both decodes VWAP-sane),
   two-lane independence, native-4h shadow 14,607/14,610 at 1e-9, FAIL
   verdict preserved, no smoothing, escalated + disclosed everywhere.
3. **Phase rules** — all three causal, parameters round/domain-standard,
   TRANSITION_UNKNOWN code-owned, five outputs, warmup excluded. The
   no-lookahead tests genuinely mutate FUTURE bars (L1 replaces the entire
   future after t0; L2 sets close[200:]=1e9; L3 sweeps 4 paths × 4 cuts) and
   assert past labels unchanged.
4. **Census arithmetic** — reproduced EXACTLY from raw bytes: L1 all five
   phases (ACC 69 / UP 172 / DIST 75 / DOWN 190 / UNK 3, decisions
   6458/20411/6295/24913/171); L2 all 20 fold cells including thin calls
   (ACC F4 71<100; DIST F1 66, F4 53); SPY thin calls fail-closed with
   negative margins (ACC 15, DIST 5, DOWN ≤11, UNKNOWN by-construction FLAT);
   UPTREND floors met (margin +3 episodes; per-fold decisions
   581/314/280/762 ≥ 100). No cross-cell pooling anywhere.
5. **Ancestry (rho bar application)** — amended VETO-iff-|rho|>0.20 applied
   consistently (L1 worst 0.082, L2 worst 0.168, L3 self-killed 0.559);
   §7.1 class arguments recorded pre-outcome. FAIL is only on the unmeasured
   shadow above.
6. **Outcome-blindness** — zero PnL-path code (all PnL-shaped identifiers
   confined to hygiene-test banned lists/docstrings); `pct_change` only in
   pre-PnL ancestry shadows; no MAP/SURVIVORS/ledger/V2/RSMV1 reads (strings
   exist only in guard forbidden-path lists); ceiling arithmetic counts-only
   (L1 margins 9.5–35.6x; L2 20.4 bps vs 100 bps bound).
7. **Tuesday gate** — auditor re-ran L3: 55/55 pass. Tests are falsifiable:
   the defect-shape fixture must produce Tuesday-onset forced flats, and the
   lane pipeline must produce zero clock-attributable force-flats on the same
   dates; rotation replay invariant +1..+4 on synthetic and real snapshot;
   re-run scheduled inside the scored run with BLOCKED halt law.
8. **Evaluation freeze** — 4 baselines sane/frozen (SMA200 cell-clock;
   30/20→10 DD, min-hold 5); costs exact (BTC 6 bps/side + funding
   1.377e-5/8h; SPY 10 bps/fill; full-stack tiers 1.0/1.5/2.0); G1–G9 equal
   to §16.3 (no weakening); floors 20/3/100 unrelaxed; relaxed-floor
   precedent absent.
9. **Boundaries** — budget 4≤15, 0 used; S1 sealed and unreferenced; only
   keyless `data.binance.vision` GETs (no auth surface, no broker/order
   code); worktrees/branches match the ownership manifest; 0 cycle merges,
   0 remote refs (no push).
10. **Suites re-run in the audit worktree** — L3 55 pass; L1 32 pass + 3
    honest disclosed staging-skips; L2 44 pass + 1 skip; hygiene/guard suites
    pass.

## What the owner must know before any GO

- **Do not type the GO phrase yet.** The verdict is `REMEDIATION_REQUIRED`.
  After the H1 measurement + re-freeze (plus the two cheap M-fixes in the
  same commit), a fresh A7 pass on the delta is required before STOP-1.
- If any of the three measured run_imbalance rhos exceeds 0.20, that arm is
  `ANCESTRY_VETOED` — the freeze shrinks and the budget drops with it. That
  is a normal, valid outcome, not a failure of the cycle.
- The BTC 2020–2024 history extension and the SPY 2015–2026 window remain
  `DISCOVERY` (never OOS); the catalog (sha 81d4f147…) is dead as a reference
  and correctly demoted; the Vision series is the scored source with its own
  independent anchors.
- Nothing in this audit consumes the GO phrase; no scored run exists; no
  predecessor artifact was opened; S1 untouched.

— A7, independent prelaunch auditor
