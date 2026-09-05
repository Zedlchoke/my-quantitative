# STOCKS-FREE-V8 — STANDING-READY: OWNER-SOURCE PRICE AUTHORITY + FUNDAMENTALS-CONDITIONED DISCOVERY

> Owner plan dated 2026-09-05, held DORMANT under the V7 ACCEPT_CLOSE
> decision (option C). This plan activates the day the owner provides or
> authorizes a single-name price source with delisted coverage. Until then
> no agent starts this cycle; nothing in this file overrides the dormancy.
>
> `PLAN_stocks_v7.md` and all earlier stocks plans/records are closed
> historical authorities. A correct `STOCKS_FREE_V8_REJECT_ALL` — or a fast
> honest `STOCKS_FREE_V8_BLOCKED_DATA_AUTHORITY` if the provided source
> fails the probe — is a successful research run.

## 0. Activation condition (the only thing that starts V8)

The owner, by explicit instruction, provides ONE of:

```text
(A) an entitled source with delisted US single-name daily history
    (e.g. a survivorship-bias-free vendor subscription, a broker export
    covering delisted names) — license evidence supplied by the owner;
(B) authorization to purchase/upgrade a named provider (agent purchases
    remain forbidden; the owner executes the transaction).
```

On activation, A1 remeasures everything below; drift is recorded, never
normalized.

## 1. Frozen starting point

```text
V7 terminal            5ccc587c39f0b794b61e70d3185ba114a8ddb887
                       (STOCKS_FREE_V7_BLOCKED_DATA_AUTHORITY)
V7 owner decision      ACCEPT_CLOSE + standing re-open (event log 31b705f)
denominators           stocks 21/21; budget 0/6 for V8; S1 SEALED_UNTOUCHED
inherited assets       multi-vintage SEC PIT panel, sha256 pinned
                       1cb115d3dbb563cbc6ec4b1ce78ef2347b4538b23fc9e3232e
                       38b1f9d16cdd40 (staged gitignored; source lane
                       worktree must survive until V8 copies + verifies);
                       154-clock fundable freeze (p0a_clock_freeze.json);
                       V7 probe evidence (five gates with measured PASS
                       baselines); pit_conditioning.py; fusion core
                       c6a0576e...; lessons L1–L9 + program P-1..P-6
GO discipline          no GO carries across cycles; V8 requires its own
                       owner GO at its own prelaunch (V6 ruling stands)
```

## 2. Mission

> Does the owner-provided price source pass the six-gate authority suite —
> and if it does, do PIT-fundamentals-conditioned mechanisms from the frozen
> 154-clock set produce incremental after-cost information beyond SPY/
> sector beta on a survivorship-aware single-name panel?

## 3. The six gates (from V7; five already carry measured baselines)

1. license/entitlement scope for equities + snapshot permissions;
2. history depth >= the S0 window (V7 baseline: Twelve Data served ~20y);
3. **delisted coverage — the make-or-break** (V7 failure mode: dead tickers
   404 everywhere; a never-existed control symbol established the 404
   semantics — the same canary method applies: SEC-corroborated dead names
   TWTR/SIVB/TWX/FRC plus the control symbol);
4. raw/adjusted clarity + L7 corporate-action reconciliation vs SEC-recorded
   distributions (V7 baselines: CMG 50:1, TJX 2:1 split ratios; KO
   dividend window +6.24% vs SEC-implied +6.00%);
5. availability evidence per bar publication (close + one session read-lag;
   asserted bounds never authorized);
6. data integrity (OHLC consistency; deterministic double-pull).

Any gate failure closes V8 `BLOCKED_DATA_AUTHORITY` with evidence — the
probe is cheap and terminal by design. A source failing gate 3 does not
stop the program from asking the owner for a different one.

## 4. Cycle structure on a passing source

Identical to V7 §3–§13, summarized: worktree `orca/stocks-free-v8-
integration` from the V7 terminal (or a newer owner-authorized descendant);
P0a panel re-hash + cohort construction (SEC submissions survivorship
census — the leg never yet run); P1–P3 inherited factory/coverage-first/
invariants (liquidity-band equity costs, stress multipliers applied to
booked PnL); D1 three blind lanes on assigned axes (>=3 of 6 proposals
fundamentals-conditioned from the 154 clocks; wave diversity binding);
D2 audits (novelty with the full forbidden inventory incl. both V6/V7
blocked entries; feasibility with break-even headroom); I implementation
(cost linear in fills; placebo controls runnable by construction; margin-
to-fail per gate frozen at implementation); Q freeze + twins + recursive
dry-run leak scan; independent A7 prelaunch; HARD STOP until the owner
types `GO STOCKS V8 SCORED EXECUTION`; E max six serial cells with per-cell
reporting; reproduction from the twin; terminal A7 with positive-stricter
audit; DSR/PBO in the terminal statement.

## 5. Hard boundaries

Unchanged from V7 §15: no signup/purchase by agents; keys in environment
only; no S1 access/paper/live/orders; no raw-data commit; no optimizer or
rescue in any form; no rewriting history; pushes only on owner instruction;
gates report PASS/FAIL/NOT_RUN/BLOCKED.

## 6. First report from a fresh A1 (on activation)

```text
measured UTC / root / branch / HEAD / porcelain
V7 terminal + ACCEPT_CLOSE decision verified
the owner-provided source: identity, entitlement evidence, fetch plan
denominators 21/21, budget 0/6, S1 seal, workers
inherited panel + clock-freeze hashes re-verified
probe plan for gates 1–6 (canary set from V7 evidence)
GO/NO_GO for the probe
```
