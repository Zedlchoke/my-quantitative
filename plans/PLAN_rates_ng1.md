# PLAN RATES-NG1 — US Treasury curve cycle on platform v3 (new asset family)

> Status: `PLANNED_NOT_STARTED` (registered 2026-09-12).
>
> Generation note: first cycle of the new-assets generation (owner directive
> 2026-09-12, third generation); first `rates` asset family in program
> history — the same-asset ancestry inventory is EMPTY by construction.
> A correct `RATES_NG1_REJECT_ALL` is a successful research run.

## 0. Owner directive and authority

Owner instruction, verbatim (2026-09-12): "mở cycle 3 assets mới suwt dụng
những nguồn dữ liệu mới và hướng mới bạn đề xuất. Nguồn dữ liệu phải là
miễn phí hoặc có trong gói EODO gì đó tôi mua." (typos preserved; gloss:
open a 3-new-assets generation on new data sources and new directions of
the Lead's proposal; every source must be free or inside the owner's EODHD
package — no purchases, no new keyed signups.)

Standing GO delegation continues (structure of ng1/ng2, owner directive
2026-09-11 carried forward): at this cycle's own prelaunch gate, AFTER
independent A7 publishes `RATES_NG1_S0_LAUNCH_AUTHORIZED` with zero
unresolved HIGH/CRITICAL, the Lead (A1) types the GO decision under the
owner's standing delegation. A7 REFUSED => no GO. Scope excludes S1
opening, push/merge to `main`, purchases, new keyed signups, credentials
in logs, live/paper/testnet.

GO phrase (typed only at this cycle's own gate):

```text
GO RATES NG1 SCORED EXECUTION
```

## 1. Prior verdicts and forbidden ancestry

- No rates family exists in the inventory. Named cross-asset kill-candidates
  (pooled into the D2 veto set):
  1. **DGS10-level nominal-exposure forms** — falsification-by-control #14
     (FX-V8: level control out-earned 4.01x) and #15 (FOREX-NG1:
     CTL-DGS10LEVEL +4.13/trade out-earned its anchor). Any proposal whose
     declared representation reduces to yield-LEVEL beta on any grid dies.
  2. FX 16:00-NY reaction-direction and release-order forms (V7/V8/V9/NG1).
  3. Generic shadows: `momentum_63s`, `generic_dow_tue` clock forms.
- Mandatory control (V8 law adapted): a **level-vs-shape decomposition
  control** on every lane — the signal must survive orthogonalization
  against the level factor, or the family is a re-clocked level and dies.
- Canonical inventory: `research/wayfinder/FAMILY_FAILURES.jsonl` +
  `research/wayfinder/HYPOTHESIS_LEDGER.md` (pooled, P-9/P-12).

## 2. Objective and terminal outcomes (frozen before any proposal)

Objective: test whether Treasury curve-SHAPE dynamics (level-slope-
curvature decomposition) and official auction-supply clocks carry
after-cost expectancy on tradeable US Treasury ETP legs that no dead
yield-level / reaction-direction family can explain.

Terminal outcomes (preregistered, negative-first):

```text
RATES_NG1_REJECT_ALL
RATES_NG1_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
RATES_NG1_BLOCKED_DATA_OR_SELECTION
RATES_NG1_BLOCKED_PRELAUNCH
RATES_NG1_INCOMPLETE_NOT_PROMOTABLE
```

`BLOCKED_DATA is live and cheap`: if the Treasury.gov pull/re-pin, the
FRED granted-set re-pin, the ETP census, or the auction-calendar PIT
census fails in P0, the cycle dies before proposals.

## 3. Data authority and platform v3 adoption (P0)

Measured liveness 2026-09-12 (Lead probe, recorded): Treasury.gov daily
par-yield CSV served (2025 verified: 1M..30Y daily); EODHD family-1 EOD
serves US ETPs fresh to 2026-09-11 (TLT 2002→, 6071 rows) but serves
NO indices (.IND 404) and NO futures (.COMEX 404); Stooq futures CSV is
JavaScript-challenge-blocked for curl (browser-class CANDIDATE only,
never a primary authority).

Frozen consumption set (nothing else; everything else stays BLOCKED_DATA):

- **S5 Treasury.gov daily par yield curve** (official, free, keyless):
  per-year CSVs, full tenor set; deterministic retrieval; sha-pinned
  substrate manifest; depth census from 1990.
- **S2 FRED keyed granted set re-pinned** (V8/V9 series already granted:
  DGS10, DGS2, DFII10, DFII5, T10YIE, T5YIE, CPIAUCSL): CADS re-pin,
  0-drift verify; FRED_API_KEY presence is not authority (V9 law).
- **EODHD family-1 US Treasury ETP EOD** (existing owner key, programmatic
  .env load, never echoed — V13 precedent): candidate legs TLT/IEF/IEI/SHY
  + delisted-channel probe (US delisted=1, V8-proven) for dead Treasury
  ETPs; RAW primary + corp-actions cross-check (V8 convention).
- **Treasury auction calendar** (official, free, keyless): tentative +
  announcement dates as PIT conditioning clock.
- P-7 canaries mandatory: fabricated dates, fabricated tenor columns, a
  never-existed series — each must FAIL.

Adoption law: one per-asset adoption commit; consumption ONLY via
`consume_via_plane`; bounded shadow-parity pilot (plane-read vs raw file
bytes, digest equality on overlap) must PASS before downstream lanes.

## 4. Phases and gates

Same law as `plans/PLAN_crypto_ng1.md` §4-§7 structure:

```text
P0  data authority + platform adoption (S5 pin, S2 re-pin, ETP census,
    auction-calendar PIT census, shadow parity)          -> P0 gate
P1  kernel/accounting inheritance; ETP cost constants re-measured (Q-8)
P2  feasibility floors (Q-6 recent window; lane dies cheap if under floor)
D1  blind proposal lanes (A4, A5) from one wave SHA
D2  novelty pooled |rho| <= 0.20 vs inventory incl. named shadows;
    code AND representation committed before any number is cited (P-12)
S   selection freeze (rubric §6 frozen BEFORE D1 dispatch)
I   implementation (only if selection non-empty)
Z   exact-arm sanitized dry-run
A7  independent prelaunch audit -> RATES_NG1_S0_LAUNCH_AUTHORIZED
GO  Lead types GO under owner standing delegation
E   scored cells under machine-wide heavy lock (budget 6)
R   detached-twin reproduction
T   terminal A7 + two-half close
```

## 5. Cost, kernel and clock identity

- Clock: daily NY-close decision grid on EODHD EOD ETP bars; curve facts
  same-day official CSV; availability convention bar-readable close+1
  session (V7 law); UTC/NY DST fixtures mandatory.
- Costs: measured ETP spreads at stress tier (Q-8; never vendor-stated);
  expense-ratio drag carried in the cost ladder (tier 2.0); cost once per
  fill.
- Kernel: inherited dual-book accounting kernel with compatibility tests;
  diagnostics 14-canon + prospective DSR (P-11); PBO fail-closed < 8 cells.

## 6. Proposal lanes (blind) and frozen selection rubric

Lane A4 — auction-supply clock: official auction announcement/tentative
dates as conditioning clock around ETP decisions; PIT evidence per event;
mechanism must declare why issuance-supply timing differs from the dead
policy-clock forms (crypto-ng1 FOMC kills). Battery: delay-pair,
clairvoyant (Q-4), clock-only shadow, shifted-calendar placebo.

Lane A5 — curve-shape structure: level-slope-curvature decomposition
dynamics on the official curve (steepener/carry forms), executed on ETP
legs. Battery: MANDATORY level-vs-shape decomposition control (§1),
clock shadow, placebo, one falsification rule.

Frozen rubric (before D1 returns; no threshold moves after any scored
number): identical 6 points to `plans/PLAN_forex_ng1.md` §6 (mechanism;
pooled |rho| <= 0.20 with margin recorded P-2; Q-6 feasibility no-PnL;
control battery runnable with invalid-null distinction Q-11; max 2
families x 3 arms = 6 cells, budget 6, distinct arm_config_digest;
preregistered ranking, smoke kills-never-selects P-15).

## 7-9. Dry-run/prelaunch/GO/E/R/T, orchestration, boundaries

Identical law to `plans/PLAN_crypto_ng1.md` §7-§9 with A7 verdict key
`RATES_NG1_S0_LAUNCH_AUTHORIZED`; heavy lock serialized machine-wide with
sibling cycles (yield pattern if long idles); reproduction detached twin
(ALL_MATCH proves self-consistency only, P-4); handoffs committed at
`research/control/RATES-NG1/orchestration/handoffs/` inside this cycle's
worktree; single-cycle MCP store: task rows carry store-level cycle_id
`ZCODE-ORCHESTRATION-V3` with the real cycle disclosed in the objective
(ng precedent). Hard boundaries: no S1, no push/merge-main, no purchases,
no new keyed signups, no credentials in logs, no consensus/forecast data,
no current-vintage substitution for pinned official series.
