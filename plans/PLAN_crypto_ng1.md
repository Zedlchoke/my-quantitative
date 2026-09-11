# PLAN CRYPTO-NG1 — next-generation crypto cycle on platform v3

> Status: `PLANNED_NOT_STARTED` (registered 2026-09-11).
>
> Generation note: this is the first crypto cycle on the research platform v3
> data plane and the first cycle of the `ng1` generation opened by the owner's
> standing directive of 2026-09-11. A correct `CRYPTO_NG1_REJECT_ALL` is a
> successful research run.

## 0. Owner directive and authority

Owner instruction, verbatim (2026-09-11):

```text
bắt đầu các plan cho các assets mới. Gọi là crypto_ng1, forex_ng1, stocks_ng1.
sử dụng hệ thống mới cập nhật và các bài học cũ. Từ đó đưa ra được hướng đi và
gọi agent. Bạn có toàn quyền tự quyết GO SCORED. Tôi muốn bạn là người quyết
định mọi thứ và prompt này chạy 1 lần không hỏi lại. output tôi muốn là
terminal cuối cùng của các plan.
```

Standing GO delegation (P-8 adaptation, recorded here and in the registry):
at this cycle's own prelaunch gate, AFTER independent A7 publishes
`CRYPTO_NG1_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL, the
Lead (A1) types the GO decision under the owner's standing delegation above.
The delegation substitutes the owner's key in the two-key launch with an
explicit, quoted, scoped standing instruction; it does NOT extend to S1
opening, push/merge to `main`, purchases, keyed signups, credentials, or any
live/paper/testnet action. If A7 REFUSES, no GO is typed; the remediation
loop or an honest negative terminal follows.

GO phrase (typed only at this cycle's own gate):

```text
GO CRYPTO NG1 SCORED EXECUTION
```

## 1. Prior verdicts and forbidden ancestry

- CRYPTO-V16 `SCIENTIFIC_REJECTION`: A6-V16-F1 CLOSE-DISPLACE-FADE, A6-V16-F2
  RUNPERSIST (dead at ANY clock).
- CRYPTO-V17 `V17_BLOCKED_DATA_OR_SELECTION` (0/6 cells; six families
  measured-dead by their own frozen rules): SILRES, WKNDLIQ, TICKET-BREADTH,
  FUNDJUMP, ATTN-PHASE, OICASCADE. SOL-composition and OI-cascade event
  families are measured-dead ancestry.
- Standing priors from V14/V15 and earlier (OI term-structure, liquidity
  episodicity, OILEV-V2 + inverted shadow, PREMFADE, BAB, carry,
  elite-size-asymmetry, taker-saturation, elite-level shadow).
- Canonical inventory: `research/wayfinder/FAMILY_FAILURES.jsonl` +
  `research/wayfinder/HYPOTHESIS_LEDGER.md` (P-9/P-10). The D2 novelty gate
  pools against the FULL inventory INCLUDING the H0 hygiene rows appended at
  bootstrap of this cycle generation.
- Re-entry law (V17 terminal): intraday lane 1 re-opens only via a plan that
  preregisters MATERIALLY NEW mechanisms (new mechanism + new information
  source + new causal control) with measured decorrelation
  (pooled |rho| <= 0.20). Dead forms re-clocked die at D2.

## 2. Objective and terminal outcomes (frozen before any proposal)

Objective: test whether EXOGENOUS-CLOCK reaction structure on the frozen
BTC/ETH/SOL H1 panels carries after-cost expectancy that no endogenous
microstructure family (all now measured-dead) can explain.

Terminal outcomes (preregistered, negative-first):

```text
CRYPTO_NG1_REJECT_ALL
CRYPTO_NG1_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
CRYPTO_NG1_BLOCKED_DATA_OR_SELECTION
CRYPTO_NG1_BLOCKED_PRELAUNCH
CRYPTO_NG1_INCOMPLETE_NOT_PROMOTABLE
```

`BLOCKED_DATA is live and cheap`: if the S4 CADS re-pin or plane adoption
fails verification, or the announcement-calendar instants cannot be
PIT-evidenced, the cycle dies in P0 before any proposal is requested.

## 3. Data authority and platform v3 adoption (P0)

Frozen consumption set (exactly the GRANTED S4 series, nothing else):

- `binance-daily-h1-panels`: panel_BTCUSDT_h1.csv `111c1a2d…`,
  panel_ETHUSDT_h1.csv `ebd487a6…`, panel_SOLUSDT_h1.csv `c4ca0b6e…`,
  panel_manifest.json `761190a5…` (CADS S4, GA4 GRANTED).
- `binance-open-interest`: oi_series_reduced.json `f26a61e4…` (CADS S4).
- Funding-rate settlements: keyless fapi pull, 1,158 settlements/symbol
  (V17-measured authority class; re-proved per series at P0).
- Announcement instants: deterministic public schedules of scheduled US
  macro prints (FOMC decisions, CPI, NFP) retrieved from official
  BLS/Federal Reserve publication calendars with per-release publication
  timestamps. Static schedules are PIT-trivially-evidenced; NO consensus,
  NO forecast, NO revised-narrative data. Fail-closed: any instant without
  a publication timestamp is dropped, never inferred.

Adoption law (handbook §33, platform plan §7A): one per-asset adoption
commit; consumption ONLY via the platform path
(`pa4_pa5_authority.consume_via_plane` shape: AuthorityRegistry verdict ->
CADS resolve verify-on-read -> manifest-verified frozen query); never open
data files directly in scored code; a bounded shadow-parity pilot
(plane-read vs V17-direct-read, digest equality on a sample window) must
PASS before any downstream lane consumes the plane. Every series outside
the frozen set stays BLOCKED_DATA. Keyless Binance public data only; no
key, no signup, no purchase by agents.

## 4. Phases and gates

```text
P0  data authority + platform adoption (S4 re-pin verify, calendar
    instants census, shadow parity pilot)           -> P0_GATE
P1  kernel/accounting inheritance (V17 scored driver adapted; dual-book,
    cost-once per fill L-V14-0)                     -> P1_GATE
P2  PIT/feasibility: recent-window decision ceilings (Q-6), warmup
    coverage, per-lane kill tests                   -> P2_GATE
D1  blind proposal lanes (A4, A5) dispatched from one wave SHA
D2  novelty + feasibility MEASURED; measurement code AND representation
    committed before the number is cited (P-12)
S   selection freeze (rubric §6 frozen BEFORE D1 dispatch)
I   implementation lanes (only if selection non-empty)
Z   exact-arm sanitized dry-run (non-vacuous, recursive leak scan)
A7  independent prelaunch audit (fresh context)
GO  Lead types GO under owner standing delegation
E   scored cells under machine-wide heavy lock (budget 6)
R   detached-twin reproduction
T   terminal A7 + two-half close
```

## 5. Cost, kernel and clock identity

- Clock: UTC H1 on the frozen panels; decision instants on bar close;
  sub-hour cadence battery = delay-pair + clairvoyant controls + no-lookahead
  mutation fixtures (Q-4).
- Costs: measured taker + spread at stress tier 2.0 as PRIMARY (Q-2/Q-8);
  cost exactly once per fill; measured beats stated everywhere.
- Kernel: V17 `run_v17_cell.py` family-agnostic driver semantics inherited
  via the adoption commit with compatibility tests; frozen-rule fail-closed
  enforcement unchanged.
- Diagnostics: per-period series prospective DSR (P-11 mandatory);
  PBO fail-closed NOT_RUN when cells < 8 (V17 contract).

## 6. Proposal lanes (blind) and frozen selection rubric

Lane A4 — scheduled-announcement reaction structure: mechanism must name
who is forced/late (e.g., liquidity provision drained at print instants),
an observable from the frozen set, one supporting neighbour, one
causal/placebo control (announcement shifted +/-k sessions), a clock-only
shadow (Q-7), and a falsification rule. Forbidden: any form whose signal
reduces to endogenous price/OI/funding structure already in the inventory.

Lane A5 — deterministic derivatives-calendar structure: quarterly futures
settlement dates and last-Friday options-expiry clocks as conditioning
events; same control battery + clock-only shadow; novelty must survive
pooled |rho| <= 0.20 vs WKNDLIQ (both are calendar-conditioned) AND the
rest of the inventory.

Frozen rubric (exists before D1 returns; no threshold may move after any
scored number is seen):

1. Mechanism statement with forced-participant identity — pass/fail.
2. Ancestry: pooled |rho| <= 0.20 vs full inventory (H0-hygiene-augmented);
   violation = D2 VETO, recorded with margin (P-2).
3. Feasibility (no PnL): recent-window decision count >= frozen floor;
   warmup coverage; turnover/cost ceiling kill BEFORE selection (A9-F).
4. Control battery runnable on frozen representation; control that cannot
   move the signal = INVALID NULL, not a pass (Q-11).
5. Max 2 families x 3 arms = 6 cells; budget 6; arms pairwise distinct by
   arm_config_digest.
6. Selection ranks by pre-registered evidence strength (mechanism +
   decorrelation margin + feasibility), never by any scored/smoke number
   (P-15: smoke may kill + disclose only).

## 7. Dry-run, prelaunch, GO, scored execution, reproduction

- Exact-arm dry-run: scored=false, real_pnl=false, published=false;
  recursive scan for PnL/PF/stress leakage at every nesting depth;
  empty-book/zero-decision = FAIL (non-vacuous); record IDs pairwise
  distinct; replay delta zero.
- A7 prelaunch (fresh context): hash chain, exact-arm identity, data/PIT
  authority, accounting, dry-run hygiene, S1 seal, no post-freeze drift,
  denominator seed, twin integrity; verdict
  `CRYPTO_NG1_S0_LAUNCH_AUTHORIZED` requires zero unresolved HIGH/CRITICAL.
- Scored execution: machine-wide heavy lock; cells run one at a time with
  after-cell identity/denominator reporting; TECHABORT taxonomy per §20.
- Reproduction: detached twin at code-freeze SHA, frozen inputs
  sha-verified, byte/record comparison; `ALL_MATCH` proves
  self-consistency only (P-4).

## 8. Orchestration and evidence channel

- Lanes dispatched with plugin-role packets (quant-explorer/implementer/
  reproducer/auditor) with structured handoffs schema
  `zcode_orch_v3_handoff@1` written to
  `research/control/CRYPTO-NG1/orchestration/handoffs/` INSIDE this
  cycle's worktree (committed with the lane's single commit).
- The single-cycle orchestrator MCP store (ZCODE-ORCHESTRATION-V3) is NOT
  used for foreign-cycle tasks (foreign-task isolation by design,
  `orchestrator_store._check_cycle`); controller validation of every
  handoff is A1's duty at integration time.
- Subagents run pinned to `builtin:zai-coding-plan/GLM-5.3-Flash` per
  owner instruction 2026-09-11 (agent definitions commit 35ce190);
  sessions that snapshotted pre-pin run GLM-5.3 — disclosed, never silent.

## 9. Hard boundaries

S1 stays SEALED_UNTOUCHED. No key, no signup, no purchase, no credentials
in prompts/logs/git. No push, no merge to `main` by lanes. No parameter
rescue after scored PnL is visible. Missing evidence is NOT_RUN, never
inferred PASS. Guard denials are law (§2.6). Historical worktrees/ledgers
are append-only evidence.
