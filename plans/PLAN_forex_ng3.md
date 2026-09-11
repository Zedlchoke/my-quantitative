# PLAN FOREX-NG3 — CA-anchored CPI revision-dynamics cycle (census-informed floors)

> Status: `PLANNED_NOT_STARTED` (registered 2026-09-11 under the P-19 standing
> directive, recursive application: FOREX-NG2 closed BLOCKED_DATA at P0 with 0
> scored cells — total generation cells still <= 6).
>
> A correct `FOREX_NG3_REJECT_ALL` is a successful research run.

## 0. Owner directive and authority

Owner instruction, verbatim (2026-09-11, P-19, carried by recursion):

```text
nếu mà tổng scored cell không quá 6 cells(2 family) thì ghi chú lại lesson,
ledger,... và làm lại thêm 1 cycle lại từ đầu nữa nhé. Quyền GO vẫn thuộc về bạn.
```

Standing GO delegation (same structure as ng1/ng2): at this cycle's own prelaunch
gate, AFTER independent A7 publishes `FOREX_NG3_S0_LAUNCH_AUTHORIZED` with zero
unresolved HIGH/CRITICAL, the Lead types the GO decision. Scope excludes S1,
push/merge-main, purchases, new entitlements, keyed signups, live/paper.
A7 REFUSED => no GO.

GO phrase (typed only at this cycle's own gate):

```text
GO FOREX NG3 SCORED EXECUTION
```

## 1. Prior verdicts and forbidden ancestry

Full inventory (`research/wayfinder/FAMILY_FAILURES.jsonl`) including all ng1
kills (release-order drift; CPI acceleration falsified-by-control #15) and the
ng2 P0 census findings. Pooled |rho| <= 0.20 vs the 25-shape forex panel on each
proposal's declared P-12 representation; rescue at another horizon dies at D2.

## 2. Objective and terminal outcomes (frozen before any proposal)

Objective: test whether CA-anchored CPI revision dynamics (the genuinely-alive
first-print revision stream measured by the ng2 census: CA 72 first-print
revision events, 30 in the recent 24 months) carry after-cost expectancy on the
daily 16:00-NY grid.

Terminal outcomes (preregistered, negative-first):

```text
FOREX_NG3_REJECT_ALL
FOREX_NG3_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
FOREX_NG3_BLOCKED_DATA_OR_SELECTION
FOREX_NG3_BLOCKED_PRELAUNCH
FOREX_NG3_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Census-informed frozen floors (design source disclosed)

The ng2 P0 census (committed at the FOREX-NG2 close; A7-audited) measured, per
economy, usable revision events AND the first-print ("real") sub-stream that
excludes bulk re-referencing artifacts:

- CA: 72 first-print events (30 recent) — ALIVE; the anchor economy.
- GB: 8 first-print events (60/68 are one bulk 2018 re-referencing coefficient)
  — EXCLUDED as anchor, disclosed; usable only as a non-anchor differential leg.
- AU: 26 usable events (< 30) — EXCLUDED as anchor (ng2's kill), disclosed.
- NZ: 24 first-print events — EXCLUDED as anchor, disclosed.
- US: 84 usable (quote leg; not an anchor by design).

Frozen floors for THIS cycle (set BEFORE any new measurement, from the already
measured ng2 census — this is design-from-census, not floor-shopping-after-fail:
no threshold in this cycle may change after any measurement):

- A4 (own-economy CA revision drift): >= 30 CA first-print revision events with
  full availability windows (measured 72; Q-6 recent >= 15 of the 30 measured).
- A5 (revision differential CA-vs-others): >= 12 differential months (measured
  102 in ng2's wider definition; this cycle re-measures under the first-print
  restricted definition and fails closed if < 12).
- Anchor universe: CA only; GB/AU/NZ excluded-as-anchor with the disclosed
  reasons above. Re-including any excluded economy as anchor is forbidden in
  this cycle.

## 4. Data authority (inherited, no new grants) and machinery

Identical to ng2 §3: S2/S3 CADS pins, spot 4 pairs with the committed
AUTHORIZED gate (P-18 law), DGS10 vintaged control, 1842-day grid, inherited
evaluators/adapters; new modules only under forex_ng3 namespaces.

## 5. Phases and lanes

```text
P0  pin re-verification + CA-first-print revision census under the restricted
    definition (floors above; BLOCKED_DATA if any fails)
D1  2 blind lanes x 2 proposals:
    A4 own-economy CA revision drift (USDCAD), mandatory nominal-exposure
    control (DGS10-level) + clock shadow + placebo (non-revision vintage dates)
    + neighbour (alternative revision construction);
    A5 revision differential CA-vs-(GB/AU/NZ/US legs), mandatory V7-style
    no-differential falsification control + nominal control + clock shadow +
    order-preserving placebo + neighbour.
D2  novelty (pooled |rho| <= 0.20, 25-shape panel) + feasibility (Q-6) +
    identifiability — code+representation committed (P-12)
S   selection freeze (rubric: margin, control runnability, feasibility; max
    2 families x 3 arms; budget 6) BEFORE implementation
I   frozen-spec runners (inherit ng1 evaluator) + arm digests
Z   exact-arm sanitized dry-run
A7  prelaunch (execution-backed, fresh context) — two-key #1
GO  Lead types GO (delegated) — two-key #2
E   6 cells scored under machine-wide heavy lock; R1-R6 mechanical
R   detached-twin reproduction
T   terminal A7 + two-half close
```

Stage-A rules R1-R6, cost contract (1.5bps/side ladder, tier 2.0 PRIMARY, Q-8
M2 disclosure), folds: identical to ng1's frozen set.

## 6. Orchestration, evidence channel, hard boundaries

Same law as ng1/ng2: committed structured handoffs at
`research/control/FOREX-NG3/orchestration/handoffs/`; store-cycle mislabel
disclosed; Flash pin disclosed; S1 SEALED; no push/merge/purchases; no rescue;
missing evidence NOT_RUN.
