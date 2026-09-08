# STOCKS-FREE-V12 — first report from a fresh A1 (plan §6 template)

Measured 2026-09-08T01:03:29Z..01:06Z (UTC stamps per entry below).

```text
measured UTC / root / branch / HEAD / porcelain
  UTC      2026-09-08T00:53:32Z at first measure (bootstrap commit 01:03Z)
  root     /Users/hoangminhlong/my-quantitative
  branch   main (root checkout)  ->  cycle branch orca/stocks-free-v12-integration
  HEAD     09ccfcc1bb521fbca8a071cb691d2609619a2ea5 (root main at dispatch)
  porcelain  root: only ?? .zcode/ (owner/harness untracked, never staged);
           worktree clean after bootstrap commit 02b4ac2
  NOTE     main advanced 27c1a92 -> 09ccfcc between dispatch drafting and A1
           intake (Lead crypto-V16 closeout sync 0474d9c + PLAN_crypto_v17
           router sync 09ccfcc); owner instruction "branch from main HEAD"
           honored at the MEASURED HEAD. Crypto V16 is CLOSED (terminal
           46db31d, canonical close 9d62d5c) — the dispatch brief's "V16
           running scored cells under the lock" was stale history; re-measured
           before believing. Heavy lock measured FREE at intake (history: 2
           FAILED + 1 FINISHED, all released). Program denominators moved
           227/230 -> 233/236 (ledger authority per P-9); stocks unchanged.

V11 terminal + A7 CONFIRM chain verified; stocks 39/39, budget 0/6, S1 seal
  terminal 9d3a0612f1e35430a300ba02c1b4c28bc748d4b0 == HEAD of worktree
  orca/stocks-free-v11-integration (measured, clean); terminal_report.json
  read FROM COMMIT BYTES: STOCKS_FREE_V11_REJECT_ALL, A7 CONFIRMED 10/10
  recomputed from bytes, 0 unresolved HIGH/CRITICAL, 5 verdict-neutral
  findings; reproduction ALL_MATCH byte-equal BOTH files from twin @aac07d9
  (detached worktree present); budget 3/6 — 3 slots dead forever; stocks
  39/39; S1 SEALED_UNTOUCHED; workers 0. Matches plan §0 exactly.

cohort + panel + V11 census pins re-verified (incl. chain/placebo counts)
  4/4 sha256 pins re-hashed from bytes on this host at V12 intake, MATCH:
    multivintage_panel.jsonl   67591464...af1447
    cohort_v9.json             6a95401f...a2aa62
    v10_timing_observables     b1477ea3...802337
    v10_revision_observables   7110cbf0...5657c2
  V11 census artifact read from terminal commit bytes; counts EQUAL plan §0:
    74,931 filer-events | 1,667,422 chains depth>=2 | 2,112 entities at
    max chain depth >=5 (390 ALIVE + 1,703 DEAD + 19 NOT_DEAD) | 1,038 DEAD
    entities with >=20 strict bars after last event | 8,034,881 clear 5-bar
    placebo windows (96.1% of positions)

governance mechanisms verified on-branch (tests + registry --verify)
  research/governance/ present on main HEAD (diagnostic_persistability.py,
  heavy_lock.py, validate_family_failures.py); targeted governance tests
  54 passed in 1.93s (.venv/bin/python); registry validator:
  55 entries, 0 errors -> PASS (53 at V11 close + 2 crypto-V16 rows at
  Lead closeout). Adoption is MANDATORY this cycle (plan §3): diagnostic
  persistability gate (BLOCKED_PRELAUNCH on any gap, runs BEFORE A7 launch
  authorization), machine-wide heavy lock (stderr tail on FAILED releases),
  failure-registry append at close.

chain-structure + dead-name bookable-window pre-check (fundable clocks)
  Lane 1 (amendment-chain STRUCTURE; no new data dependency): 1,667,422
  depth>=2 chain groups; 2,156 entities with >=1 chain group; 2,112 at
  max depth >=5; deep tail (604,376 groups at depth 5; 68,975 at 6;
  18,867 at 7). FUNDABLE on existing hash-verified artifacts.
  Lane 2 (death/distress-event books): cohort dead class 1,769 (1,752
  priced in the timing layer); 1,038 DEAD entities with >=20
  STRICT_NEXT_BAR bars after last filer-event; DEAD_EVIDENCED events with
  >=1 / >=20 / >=60 bookable bars = 45,141 / 44,288 / 42,772 of 49,411;
  evidenced Form-15 death census on disk (12B/12G taxonomy); EODHD_API_KEY
  name present in gitignored .env (value never read; standing owner item
  keeps the subscription active while stocks cycles run);
  price_last_dates_max 2026-07-17. RAW MATERIAL PRESENT — the plan-mandated
  liquidity/last-quote cheap-kill is a P0/A9-F adjudication, NOT decided
  here; BLOCKED_DATA not triggered at pre-check.

GO/NO_GO for P0
  GO. All §6 prerequisites verified from bytes; both sanctioned axes show
  fundable clocks on owned evidence; no blocker. P0 (A2/A3) dispatches
  coverage-census-only (no proposals, no PnL): chain-depth/shape bookable
  windows per entity (lane 1) and dead-name post-event bookable price
  windows + liquidity/quote feasibility (lane 2), pins re-verified before
  any compute, published BEFORE D1. Heavy jobs only under the machine-wide
  lock (NOT_RUN_RESOURCE_CONFLICT on contention — crypto V17 may claim it).
```

Findings (verdict-neutral, reported not repaired by this A1):
- CONTINUE.md intro line still says "crypto PLAN_crypto_v16.md (RUNNING)"
  while its own body, CLAUDE.md and RULES.md all agree crypto is CLOSED and
  v17 is the next plan — stale derived-checkpoint line, Lead-side fix.
- plans/ACTIVE_CYCLES.json (handbook §3.1 default registry) has never
  existed in this repo; router consensus currently lives in
  CLAUDE/RULES/CONTINUE/GO-registry. Standing gap, recorded.
