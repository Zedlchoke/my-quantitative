# PLAN FOREX-NG2 — CPI revision-dynamics cycle on the proven vintaged plane

> Status: `PLANNED_NOT_STARTED` (registered 2026-09-11 under owner throughput
> directive P-19: ng1 ended at exactly 6 scored cells / 2 families).
>
> A correct `FOREX_NG2_REJECT_ALL` is a successful research run.

## 0. Owner directive and authority

Owner instruction, verbatim (2026-09-11, P-19):

```text
nếu mà tổng scored cell không quá 6 cells(2 family) thì ghi chú lại lesson,
ledger,... và làm lại thêm 1 cycle lại từ đầu nữa nhé. Quyền GO vẫn thuộc về bạn.
```

Standing GO delegation (carried from the ng1 directive, same structure): at this
cycle's own prelaunch gate, AFTER independent A7 publishes
`FOREX_NG2_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL, the Lead
types the GO decision. Scope excludes S1 opening, push/merge to `main`,
purchases, NEW entitlements beyond those already ruling-authorized in ng1
(Twelve Data spot per the committed authority artifact; S2/S3 CADS pins), keyed
signups, credentials, live/paper/testnet. A7 REFUSED => no GO.

GO phrase (typed only at this cycle's own gate):

```text
GO FOREX NG2 SCORED EXECUTION
```

## 1. Prior verdicts and forbidden ancestry

Everything in ng1 applies (V7/V8/V9 + FXNG1-A5-P1 release-order drift;
FXNG1-A4-P2 CPI acceleration — falsified-by-control #15) plus the full cross-asset
inventory (`research/wayfinder/FAMILY_FAILURES.jsonl`, 83 entries). Pooled
|rho| <= 0.20 vs the 25-shape forex panel (V8 shapes incl. nominal-level shadow,
V4 commodity bloc, V7 spillover/lead-lag, generics) on each proposal's declared
P-12 representation. Re-parameterizing a dead form at another horizon is rescue
(Q-3/P-15) and dies at D2.

## 2. Objective and terminal outcomes (frozen before any proposal)

Objective: test whether CPI REVISION dynamics — the gap between later vintages
and the first print of the same month, a PIT-measurable information source on
the already-pinned vintaged channel that NO prior family has measured — carry
after-cost expectancy on the daily 16:00-NY grid.

Terminal outcomes (preregistered, negative-first):

```text
FOREX_NG2_REJECT_ALL
FOREX_NG2_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
FOREX_NG2_BLOCKED_DATA_OR_SELECTION
FOREX_NG2_BLOCKED_PRELAUNCH
FOREX_NG2_INCOMPLETE_NOT_PROMOTABLE
```

`BLOCKED_DATA is live and cheap`: if the revision-event census (P0) cannot
evidence >= the frozen floor of usable revision events per economy with full
availability windows, the cycle dies in P0 before any proposal is requested.

## 3. Data authority (inherited, already ruled and pinned — no new grants)

- Vintaged CPI GB/CA (MINMEI realtime, 96 vintages each), AU/NZ (quarterly
  vintaged), US (fred_cpiaucsl_rt) — CADS S2/S3 pins re-verified at P0.
- Spot 4 pairs (GBPUSD/USDCAD/AUDUSD/NZDUSD) — spot_pin_manifest from ng1;
  scored consumption AUTHORIZED per the committed authority artifact
  (research/control/forex_ng1_run/p1_spot/spot_authority_proof.json carried by
  this plan's inheritance; the gate reader bytes are law, P-18).
- DGS10 vintaged control bytes — pinned via the V8 manifest chain (ng1 ctl pin).
- 16:00-NY daily grid (1842 days, S0 window 2018-04-04..2025-04-30).
- Machinery inheritance: plane adapters, spot_series, D2 builders, frozen R1-R6
  evaluator, sanitized dry-run scanner — adopted by branch inheritance from the
  FOREX-NG1 terminal (e19c0a4) and re-verified at P0; no code changes to frozen
  ng1 semantics, only new modules under forex_ng2 namespaces.

## 4. New information source (the frontier)

Revision surprise R(m, v2) = I_v2(m) / I_v1(m) − 1 (first-to-second vintage gap,
per economy, PIT at the second vintage's availability instant). The vintaged
channel carries 96 vintages with hundreds of revised months per economy — the
revision stream is a genuine, never-measured observable. Lane constraints:

- Lane A4 — own-economy revision drift: reaction of the revising economy's pair
  to its own revision news. MANDATORY: nominal-exposure control (V8 law,
  DGS10-level), clock-only shadow (Q-7), placebo (non-revision vintage dates),
  neighbour (alternative revision construction, e.g. cumulative multi-vintage).
- Lane A5 — cross-economy revision differential: relative revision news between
  two funded economies conditioning the cross pair. MANDATORY: V7-ancestry
  falsification control (no-differential form) + nominal control + clock shadow
  + order-preserving placebo.

## 5. Phases

```text
P0  revision-event census + inherited pin re-verification (frozen floors:
    >=30 usable own-economy revision events; >=12 cross-economy differential
    events; else BLOCKED_DATA)
D1  2 blind lanes x 2 proposals (outcome-blind, full batteries)
D2  novelty pooled |rho| <= 0.20 vs 25-shape panel + feasibility (Q-6 recent
    window) + identifiability — code+representation committed (P-12)
S   selection freeze (rubric: margin, control runnability, feasibility; max
    2 families x 3 arms; budget 6) BEFORE implementation
I   frozen-spec runners (inherit ng1 evaluator) + arm digests
Z   exact-arm sanitized dry-run (zero outcome leakage)
A7  prelaunch (fresh context; execution-backed) — two-key #1
GO  Lead types GO (delegated) — two-key #2
E   6 cells scored under machine-wide heavy lock; R1-R6 mechanical
R   detached-twin reproduction
T   terminal A7 + two-half close
```

Stage-A rule order R1–R6 and cost contract identical to ng1's frozen set
(1.5bps/side x {1.0,1.5,2.0}, tier 2.0 PRIMARY, conservative vs V8-measured —
Q-8 M2 disclosure carried). Folds identical (2018-04..2020-06 / 2020-07..2022-10
/ 2022-11..2025-04).

## 6. Orchestration and evidence channel

Same law as ng1: committed structured handoffs at
`research/control/FOREX-NG2/orchestration/handoffs/` inside this cycle's
worktree; single-cycle MCP store used with disclosed store-level cycle mislabel;
subagent Flash pin (35ce190) disclosed; guards are law.

## 7. Hard boundaries

S1 SEALED_UNTOUCHED. No push/merge-main/purchases/new entitlements/credentials.
No rescue after scored numbers visible. Missing evidence NOT_RUN. Guard denials
are law. Historical artifacts append-only.
