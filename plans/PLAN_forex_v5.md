# FOREX-FREE-V5 — THE INFLATION / REAL-RATE AXIS ON EVIDENCED VINTAGES

> Owner plan dated 2026-09-05, drafted by the Lead Engineer from V4's
> measured terminal. Activates on owner dispatch; nothing starts on its own.
> A correct `FOREX_FREE_V5_REJECT_ALL` — or a fast honest
> `FOREX_FREE_V5_BLOCKED_DATA_AUTHORITY` if the axis cannot be evidenced —
> is a successful research run.
>
> `PLAN_forex_v4.md` and all earlier forex plans/records are closed
> historical authorities.

## 0. Frozen starting point

```text
V4 terminal            edba9bf (branch orca/forex-free-v4-integration;
                       A7 terminal CONFIRM_FOREX_FREE_V4_REJECT_ALL,
                       8/8 check groups from bytes, 0 blocking)
V4 outcome             commodity-bloc risk-off REJECT (whisper-positive,
                       zero robustness); family2 REJECT; carry front door
                       CLOSED at D2 by measured rho 0.997-1.000 vs both
                       invalidated-ancestor variants
carried forward        two DATA_BLOCKED_VALID proposal classes —
                       real-differential and PPP-deviation — pre-registered
                       selectable the moment their availability evidence is
                       wired (this cycle's P0 exists for exactly that)
denominators           forex 24/24; budget 0/6 for V5; S1 SEALED_UNTOUCHED
announcement ledger    pin ae5e1f2e (220 rows; 108/151 rate-change events
                       evidenced; CA 22 + EMU 19 rows remain unevidenced)
inherited machinery    dual books, stress tiers on booked PnL, break-even
                       bps, margin-to-fail per gate (P-2), DST 16:00-NY
                       calendar, USD-drift gate, twins/reproduction harness,
                       two-key launch protocol proven in production (P-8)
data cost              $0 — keyless official sources only
```

## 1. What is closed and may not be rescued

The cumulative forbidden inventory plus V4's additions: commodity-bloc
risk-off event conditioning (and every threshold/window variant). **The
carry front door stays CLOSED**: V4 measured the re-entry proposals at rho
0.997–1.000 against both variants of the invalidated ancestor — the region
is the same trade; any future re-entry needs a materially new mechanism
through a new owner plan and will face the same measured rho bar. The
DATA_BLOCKED_VALID classes are NOT forbidden — they are unfunded, and V5
exists to fund them honestly or close the axis honestly.

## 2. Mission and allowed scope

V5 asks one question:

> Do inflation- and real-rate-conditioned mechanisms — per-print CPI
> structure and vintaged market-based real-rate structure — produce
> incremental after-cost information on the authorized 7-pair universe at
> daily-or-slower clocks, under fully evidenced availability (P-1)?

Two macro information axes, funded or killed in P0 before any proposal:

1. **per-print official inflation** — CPI/HICP release-calendar evidence per
   economy of the pair universe (US BLS, EMU ECB/Eurostat, UK ONS, JP
   Statistics Bureau, CH BFS/Federal Statistical Office, CA StatCan, AU
   ABS, NZ Stats NZ): official keyless static schedule pages + archival
   release dates, each series carrying its own EVIDENCED availability row.
   The real-differential and PPP-deviation classes pre-register here.
2. **vintaged market-based real-rate structure** — ALFRED (archival FRED)
   as the PIT authority: vintage-archived breakeven/forward inflation and
   real-yield series with TRUE point-in-time semantics; probe keyless CSV
   access, vintage availability stamps, coverage vs the S0 window, license.

Scope rules frozen: availability evidence absolute (asserted bounds never
authorized); controls runnable under evidenced semantics (P-3); decision
clocks daily or slower; dual books with price-only sign never inverted;
stress tier 2.0 primary; margin-to-fail per gate; placebo-style controls
standard; |rho| <= 0.20 novelty vs ALL forbidden ancestry (now including
V4 family1 and the carry region); wave diversity binding; exactly three
arms per family; max six scored cells; unused slots never reassigned.

Allowed terminal outcomes:

```text
FOREX_FREE_V5_REJECT_ALL
FOREX_FREE_V5_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
FOREX_FREE_V5_BLOCKED_DATA_OR_SELECTION
FOREX_FREE_V5_BLOCKED_PRELAUNCH
FOREX_FREE_V5_INCOMPLETE_NOT_PROMOTABLE
```

`BLOCKED_DATA` is a first-class honest close: if P0 cannot evidence EITHER
axis for enough of the universe to fund a conditioning clock, V5 closes
cheap, exactly as V8's plan contemplated for its own leg.

## 3. Phase V5-P — evidence wiring (the make-or-break, before any proposal)

- **P0a CPI release calendars (A3)**: per economy, archive official
  schedule pages (bytes + sha256), map historical release dates to prints,
  build per-series availability tables in the EVIDENCED/ASSERTED/UNEVIDENCED
  taxonomy; a bloc without evidence is OUT (recorded, not inferred).
- **P0b ALFRED vintages (A3)**: probe the archival CSV endpoints keyless —
  vintage semantics (a true as-of date per row), series coverage vs
  2018-04-04..2025-07-24, revision behavior (the ONLY provable PIT test),
  license scope for internal research storage (FRED/ALFRED terms; no
  signup — if any key is ever required, that is an owner decision, never
  an agent signup).
- **P0c announcement-ledger extension (A2)**: continue the append-only
  extension (CA, EMU rows; any other officially evidenced events found);
  base pin re-verified, extension re-pinned; only-availability-differs
  invariant re-run.
- **P1/P2/P3**: inherited kernel regression; coverage-first publication of
  every funded conditioning clock BEFORE D1; baseline invariants freeze
  with margin-to-fail scaffolding. No PnL in Phase P.

## 4. Phases D1–E (standard, with structural mandates)

D1: three blind lanes from one wave SHA (two proposals each) — one lane on
the per-print axis (the pre-registered classes re-proposed blind plus new
mechanisms), one on the vintaged market axis if funded, one open axis; full
packet discipline with outcome-blind attestations. D2: independent
novelty/feasibility with the FULL forbidden inventory; control
identifiability measured pre-selection. I/Q: availability-lag mutation
tests per conditioning series; dry-run with binding non-vacuity gates;
recursive leak scan; twins. E: serial cells after the two-key HARD STOP —
A7 fresh-context independent (Lead- or owner-dispatched, never self-audit)
publishes `FOREX_FREE_V5_S0_LAUNCH_AUTHORIZED`; then the owner types,
fresh and informed:

```text
GO FOREX V5 SCORED EXECUTION
```

(the frozen phrase gate adjudicates form, as it did in V4 — P-8).

## 5. Hard boundaries

No signup, key or purchase by agents (keyless official sources only; any
key-requiring route is an owner decision); no S1 access, paper, live,
orders; no raw-data commit (snapshots gitignored, hash manifests);
no optimizer/rescue/threshold weakening; no rewriting prior ledgers or
terminals; pushes only on owner instruction; gates report
PASS/FAIL/NOT_RUN/BLOCKED with commands, exit codes, SHAs, margins.

## 6. First report from a fresh A1

```text
measured UTC / root / branch / HEAD / porcelain
V4 terminal + A7 CONFIRM chain verified; denominators 24/24, budget 0/6, S1 seal
announcement-ledger pin re-hash; ALFRED + CPI-calendar probe plan per economy
inherited kernel/panel/calendar hashes re-verified
GO/NO_GO for P0 evidence wiring
```
