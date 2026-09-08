# FOREX-FREE-V8 — THE REAL-RATE FRONTIER: MARKET-BASED REAL-YIELD CONDITIONING UNDER THE OWNER KEY

> Owner plan dated 2026-09-08, drafted by the Lead Engineer from V7's
> measured terminal (verified from bytes at `f59ea0c` + closeout `efb9601`).
> Activates on owner dispatch; nothing starts on its own. A correct
> `FOREX_FREE_V8_REJECT_ALL` is a successful research run.
>
> `plans/PLAN_forex_v7.md` and all earlier forex plans/records are closed
> historical authorities.

## 0. Frozen starting point

```text
V7 terminal            f59ea0c490dd8cb2329a3ab39775c76e51577562 + closeout
                       efb9601 (state CLOSED; A7 prelaunch arc R1 REFUSED
                       CRITICAL lookahead -> R3 AUTHORIZED; owner fresh GO;
                       reproduction whole-file byte-identical, ledger sha
                       1a82118b…; budget 6/6)
V7 outcome             both families dead AND control-killed. A4-P1
                       cross-economy spillover: anchor -4.026/trade with
                       the +7d sham REPRODUCING it (cluster #12) — no
                       incremental information on non-reporting pairs.
                       A6-P2 lead-lag: -8.410/trade with own-lag
                       out-earning (negative information). WITH V6
                       (own-economy, sham-NEGATIVE, robustness-killed)
                       THE REACTION-DIRECTION CLASS IS CLOSED on both
                       sides of the economy boundary.
first DSR delivery     V7 computed DSR at terminal from persisted
                       per-period series (N=39, all ~0) — the P-11
                       diagnostic gate delivered on first adoption; V8
                       keeps the contract mandatory.
denominators           forex 39/39; program 227 published / 230 observed
                       (ledger authority, P-9); budget 0/6 for V8; S1
                       SEALED_UNTOUCHED
durable assets         evidenced per-print calendars (GB/CA/AU/NZ),
                       announcement ledger 250 rows (EMU v2, CA v3 pins),
                       V7's 1077 conditioning clocks + staged snapshot
                       (156 files, fe2155c0 chain), dual-book kernel
owner-keyed door       FRED_API_KEY PRESENT in `.env` (owner-placed,
                       measured 2026-09-07 ~18:05 VN + functional probe
                       HTTP 200; root commit 26d0e30) — the door V7
                       carried as DATA_BLOCKED_VALID is now OPEN
governance             V7 ADOPTED gate + lock + registry (first forex
                       adoption, delivered). V8 continues all three
                       MANDATORY (boundary: forex V7+).
```

## 1. What is closed and may not be rescued

The cumulative forbidden inventory through V7, now including the
**cross-economy release-sign spillover continuation form** (A4-P1 — its
sham reproduces it) and the **EURUSD lead-lag diffusion form** (A6-P2 —
own-lag out-earns it). The reaction-direction class is closed as a WHOLE:
own-economy (V6, genuine info, robustness-dead) and cross-economy (V7, no
incremental info) are both measured — re-entering that class at any
k/window/pair/parameter is rescue. All priors stand: release-window
avoidance + sham shadow (V5), carry region (V4 rho 0.997–1.000), session
momentum/fade (V1/V2), vol-gated policy-rate carry (V3R invalidated — its
economic observation stays recorded, not a license). A real-rate proposal
that is nominal carry in new words dies at D2 by measured pooled rho vs
the carry-region exposures; a nominal-yield exposure-form control is
MANDATORY on the real-rate lane for exactly this reason.

## 2. Mission and allowed scope

V8 asks one question:

> Does MARKET-BASED real-rate / inflation-expectation structure — vintaged
> real-yield and breakeven series now reachable under the owner's FRED key,
> read with true point-in-time semantics — carry incremental after-cost
> information on G10 spot, beyond everything the closed classes already
> failed to monetize?

This is the preregistered V4 inflation-axis lineage (real-differential and
PPP-deviation classes, recorded DATA_BLOCKED_VALID in V4 and carried since)
finally getting its funded test. The information set is genuinely new to
the program: market prices of real rates (TIPS-class breakevens / real
yields and their foreign counterparts), not policy rates (V3's axis), not
release calendars (V5/V6/V7's axis), not spot OHLCV.

Three sanctioned axes (wave diversity binding):

1. **real-rate differential conditioning** (mandatory lane): books
   conditioned on vintaged real-yield/breakeven differentials across the
   funded economies vs USD, with (a) ALFRED/FRED vintage availability
   semantics per series, (b) a MANDATORY nominal-yield exposure-form
   control — the convenient explanation is "this is just carry
   relabelled"; if the nominal control reproduces the anchor, the family
   dies as a shadow, (c) measured rho vs the V4 carry-region exposures
   at D2.
2. **inflation-expectation / PPP-deviation class**: the second
   preregistered V4 class — expectation gaps and long-run PPP deviation
   where the series are evidenced and funded (per-print CPI calendars
   already in hand for GB/CA/AU/NZ may supply realized-inflation legs).
3. **open axis**: any literature-backed mechanism on authorized data in
   the non-forbidden space.

Binding rules carried: availability evidence absolute (P-1 — vintages are
the evidence: an ALFRED vintage's release timestamp IS its
`available_time`; asserted lags never authorized); margin-to-fail per gate
(P-2); controls recompute under semantics change (P-3); the three §11.7
verdicts per series (`PASS_PIT_EVIDENCED` / `RETROSPECTIVE_ONLY` /
`BLOCKED_DATA`) — publication lag does NOT prove revision integrity;
stress tier 2.0 primary; dual books; daily-or-slower clocks; break-even
bps mandatory; |rho| <= 0.20 pooled vs ALL forbidden ancestry; exactly
three arms; max six cells; unused slots never reassigned.

Allowed terminal outcomes:

```text
FOREX_FREE_V8_REJECT_ALL
FOREX_FREE_V8_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
FOREX_FREE_V8_BLOCKED_DATA_OR_SELECTION
FOREX_FREE_V8_BLOCKED_PRELAUNCH
FOREX_FREE_V8_INCOMPLETE_NOT_PROMOTABLE
```

`BLOCKED_DATA` is live and cheap: if the FRED/ALFRED real-yield series
cannot fund the S0 window for at least two economies with evidenced
vintage semantics, the axis dies in P0 before any proposal exists. The
V5 ALFRED host failures (CSV hang, license text unreachable) are prior
evidence — P0 must re-measure under the keyed API path and record which
verdict each economy earns.

## 3. Governance adoption (mandatory, continuing)

As V7: diagnostic persistability gate (canonical per-period series
contract — DSR must be computable at terminal; V7 proved the pipeline),
machine-wide heavy lock with stderr-tail on FAILED releases, failure
registry append at close. All three live on main (`research/governance/`,
54 tests + registry --verify).

## 4. Cycle structure (standard, deltas only)

- **P0 (A3)**: FRED/ALFRED data authority under the owner key — API terms
  of use read and recorded (owner keyed-signup already done; agents never
  print/log/transmit the key, environment-only); vintage/release
  semantics per candidate series; revision-integrity verdicts (§11.7)
  per economy; coverage census of real-yield/breakeven depth across
  S0; per-print calendar + ledger pins re-verified. Publish BEFORE D1.
  A funded-economy table with per-series verdicts is the P0 output.
- **P1**: kernel regression (append-only publication per F-A7T-1;
  arm_config_digest in ledger rows).
- **P2**: coverage-first per proposal clock.
- **P3**: invariants freeze INCLUDING the diagnostic_output_contract and
  margin-to-fail scaffolding; no PnL.
- **D1/D2**: three blind lanes from one wave SHA; causal-claim +
  falsification-rule + expected-failure-mode frozen fields; the
  nominal-yield exposure-form control MANDATORY on lane 1; sham-calendar
  placebo mandatory wherever a calendar/expectation-release instant
  conditions the book; novelty vs the full inventory (incl. carry region
  and V7 forms) measured pre-selection; control identifiability measured
  pre-selection.
- **I/Q**: availability-lag mutation per conditioning field (a vintage
  arriving late must move the decision exactly one period); exact-arm
  sanitized dry-run, non-vacuous, recursive leak scan; twins at freeze +
  twin smoke-rerun; heavy phases under the machine-wide lock.
- **E**: max six serial cells after the two-key HARD STOP — A7
  fresh-context first (diagnostic gate in scope), then the owner types,
  fresh and informed:

```text
GO FOREX V8 SCORED EXECUTION
```

- **Terminal**: reproduction from the twin; DSR over the forex program
  history (N = 39 + V8 cells) from persisted series; PBO fail-closed
  below 8 configurations; margins per gate; failure-registry append;
  program totals as-of-intake (P-9).

## 5. Hard boundaries

Unchanged from V7 §5: no signup/key/purchase BY AGENTS (the FRED key is
the owner's own signup, owner-placed in gitignored `.env`; keys
environment-only, redacted from error strings, never in chat/commits/
logs); no S1/paper/live/orders; no raw-data commit; no optimizer/rescue/
threshold weakening; no history rewrite; pushes only on owner
instruction; gates report PASS/FAIL/NOT_RUN/BLOCKED with commands, exit
codes, SHAs and margins; heavy jobs serialized machine-wide UNDER THE
LOCK (crypto V16 scored phase is the expected sibling —
NOT_RUN_RESOURCE_CONFLICT, never contention).

## 6. First report from a fresh A1

```text
measured UTC / root / branch / HEAD / porcelain
V7 terminal + closeout chain verified; forex 39/39, budget 0/6, S1 seal
calendar + announcement-ledger pins re-verified (EMU v2, CA v3)
FRED key presence re-measured (PRESENT expected; assert, never assume)
governance mechanisms verified on-branch (tests + registry --verify)
FRED/ALFRED vintage-availability pre-check (verdict per candidate series)
GO/NO_GO for P0
```
