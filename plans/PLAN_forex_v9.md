# FOREX-FREE-V9 — THE PPP-DEVIATION FRONTIER: REALIZED-INFLATION REAL-RATE MISALIGNMENT

> Owner plan dated 2026-09-09, drafted by the Lead Engineer from V8's
> measured scored outcome (verified from bytes at `07e1b95`; terminal
> chain completing at plan-freeze — see §0 precondition). Activates on
> owner dispatch AFTER the V8 close chain lands; nothing starts on its
> own. A correct `FOREX_FREE_V9_REJECT_ALL` is a successful research run.
>
> `plans/PLAN_forex_v8.md` and all earlier forex plans/records are closed
> historical authorities.

## 0. Frozen starting point

```text
V8 scored outcome      E COMPLETE at 07e1b95 (3/3 cells published
                       exactly-once, budget 3/6, 3 slots dead forever):
                       FXFV8-A5-P1 REJECT_ALL. Anchor (breakeven-slope
                       dispersion z252) whisper-positive PF 1.0531 /
                       +4.928 per trade but fails G2 (margin -0.0469),
                       G5 (BE 6.35bps vs 1.5 floor), LOPO 1.0; the
                       owner-mandated DGS10 nominal-yield-LEVEL control
                       OUT-EARNS the anchor 4.01x same sign (+19.77/trade,
                       PF 1.2268) -> R1 nominal-shadow + R2
                       parameterization kills fire on all arms
                       (falsification-by-control cluster #14). DSR N=42
                       0.341/0.406/0.540 — nothing survives deflation;
                       PBO NOT_RUN fail-closed (3<8). F2 boundary bound in
                       practice (anchor died at exactly 2/3 folds under
                       owner-ratified strict semantics) and was
                       verdict-neutral.
V8 close-chain          PRECONDITION OF V9 BOOTSTRAP (all four, in order):
precondition            (1) twin reproduction ALL_MATCH from r-reproduce-1
                       @720decb; (2) A1 closeout commit of the terminal
                       artifacts (verdict + DSR + registry row with
                       terminal_sha filled and unknown_fields back to []);
                       (3) A7 fresh-context terminal audit (Lead/owner
                       dispatched — the A1 thread never audits itself);
                       (4) Lead close-sync: root failure registry 55->56
                       validated + committed by pathspec, ledger forex
                       42/42 + program 236 published / 239 observed,
                       researchctl registry flip FOREX-FREE-V8 ->
                       TERMINAL. Bootstrap is BLOCKED until all four land.
V8 new veto entries     (a) inflation-compensation term-structure
                       dispersion (breakeven-slope conditioning in any
                       window/z); (b) the nominal-yield-LEVEL exposure
                       form — now a MEASURED shadow (PF 1.2268) and a
                       named ancestor; (c) real-rate-differential lane
                       measured BLOCKED on FRED (US-only, 5 independent
                       channels) — re-entry only via a NEW evidenced
                       non-FRED authority, preregistered in a future plan.
durable assets          evidenced per-print calendars GB/CA/AU/NZ +
                       announcement ledger (EMU v2, CA v3 pins); V8's
                       pinned FRED bytes (DFII10/T10YIE/DGS10, 5ca0bcea
                       class); dual-book kernel; 14-canon diagnostic set
                       incl. per-period series (P-11 contract proven V7,
                       delivered V8); DSR-at-terminal machinery.
denominators            forex 42/42; program 236 published / 239 observed
                       (ledger authority, P-9; both land at V8 close-sync
                       — the precondition above); budget 0/6 for V9; S1
                       SEALED_UNTOUCHED everywhere.
owner-keyed door        FRED_API_KEY PRESENT in gitignored `.env`
                       (owner-placed 2026-09-07; probes HTTP 200). Key
                       presence is not data authority; P0 re-proves per
                       series. Agents never print/log/transmit it.
governance              V9 bootstraps THROUGH the SHV1 hardened control
                       plane: researchctl/canonical registry writes,
                       retry taxonomy, diagnostic gate + machine lock +
                       failure registry all MANDATORY (forex adoption
                       boundary long passed).
```

## 1. What is closed and may not be rescued

The cumulative forbidden inventory through V8. All priors stand and are
measured at D2 by pooled |rho| <= 0.20 vs EVERY entry:

- session/open momentum & fade structures (V1/V2 era);
- release-window avoidance conditioning + its sham-calendar shadow (V5);
- the vol-gated policy-rate-differential carry region (V3R invalidated;
  V4 measured re-entry rho 0.997–1.000 — the carry front door is CLOSED);
  the V3R economic observation (PF 1.2825 under honest availability)
  stays recorded — it is not a license;
- commodity-bloc risk-off event baskets (V4);
- the reaction-direction class as a WHOLE (V6 own-economy + V7
  cross-economy — any k/window/pair re-entry is rescue);
- EURUSD lead-lag diffusion / cross-pair continuation (V7 — own-lag
  out-earns);
- inflation-compensation term-structure dispersion (V8 — killed by its
  own mandatory control);
- the nominal-yield-LEVEL exposure form (V8's measured shadow — any
  proposal whose conditioning reduces to nominal yield level in new
  words dies at D2);
- real-rate differentials on FRED (V8 P0 — the series do not exist for
  non-US economies there; this is a data verdict, not a family verdict,
  and re-entry needs a new evidenced authority).

A PPP/misalignment proposal that is nominal-price-trend exposure in new
words dies at D2 by measured pooled rho vs the V8 nominal-level shadow —
for exactly this reason the nominal-exposure control on lane 1 is
MANDATORY, not optional.

## 2. Mission and allowed scope

V9 asks one question:

> Does REALIZED-inflation-constructed real-exchange-rate misalignment —
> the second preregistered V4 inflation-axis class, unblocked by V5's
> evidenced per-print calendars and the owner's FRED key — carry
> incremental after-cost information on funded G10 spot, beyond
> everything the closed classes already failed to monetize?

This is the last untested branch of the V4 inflation-axis lineage
(`DATA_BLOCKED_VALID`, carried since V4 §terminal; V8 spent its budget on
the market-based branch, which the control falsified). The information
set is new to the program: PIT-constructed price-level differentials from
REALIZED inflation prints (never a market price of expectations, never a
policy rate, never spot OHLCV conditioning).

Two sanctioned axes (wave diversity binding):

1. **realized-inflation PPP-deviation misalignment** (mandatory lane):
   real-rate deviation constructed from evidenced CPI index levels per
   economy (GB/CA/AU/NZ official sources keyless; US leg via FRED under
   the owner key), conditioned books on the funded pairs, with
   (a) §11.7 vintaged availability per CPI series — a print's
   announcement-ledger instant IS its `available_time`; revision history
   per series recorded; (b) a MANDATORY nominal-exposure control — same
   rule computed on the NOMINAL price-level differential with the
   misalignment removed; if the nominal control reproduces the anchor
   (>= 0.5x, same sign), the family dies exactly as V8's did;
   (c) +7d sham-calendar placebo wherever a print instant conditions
   anything; (d) measured rho vs the V8 dispersion + nominal-level
   shadow + carry region at D2.
2. **open axis**: any literature-backed mechanism on authorized data in
   the non-forbidden space.

`BLOCKED_DATA` is live and cheap: if CPI index levels cannot be
PIT-evidenced (announcement instant + unrevised-as-of or vintaged) for at
least TWO funded non-US economies AND a US leg, the mandatory lane dies
in P0 before any proposal exists — the V8 precedent (real-rate lane
measured US-only and killed for exactly this reason) is the template.

Allowed terminal outcomes:

```text
FOREX_FREE_V9_REJECT_ALL
FOREX_FREE_V9_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
FOREX_FREE_V9_BLOCKED_DATA_OR_SELECTION
FOREX_FREE_V9_BLOCKED_PRELAUNCH
FOREX_FREE_V9_INCOMPLETE_NOT_PROMOTABLE
```

Binding rules carried: availability evidence absolute (P-1);
margin-to-fail per gate (P-2); controls recompute under any semantics
change (P-3); daily-or-slower clocks; dual books (price-only must not
invert sign); stress tier 2.0 PRIMARY; break-even bps mandatory;
USD-drift gate; exactly three arms per family; max six cells; unused
slots never reassigned; multiple testing priced at terminal (DSR over
the forex program history, N = 42 + V9 cells).

## 3. Governance adoption (mandatory, continuing)

As V8 plus the SHV1 plane: diagnostic persistability gate (canonical
per-period series contract — DSR must be computable at terminal),
machine-wide heavy lock (V13's SEC silence-window yielding pattern is
the standing example of not starving siblings), failure-registry append
at close with `unknown_fields: []`, bootstrap through
`researchctl`/canonical `cycle_registry@1` writes (never hand-edited),
retry taxonomy binding (CODE_OR_SCHEMA_ERROR is never auto-retried),
dashboard/doctor reads leave the tree clean.

## 4. Cycle structure (standard, deltas only)

- **P0 (A3)**: CPI index-level data authority — per-series (ONS,
  StatCan, ABS, Stats NZ, BLS-via-FRED) license/entitlement read and
  recorded (keyless official pages: no account, no click-through that
  agents accept); announcement-instant availability per the V5
  ledger class; revision-integrity verdicts (§11.7) per series;
  coverage census of index depth across S0; calendar + ledger pins
  re-verified (EMU v2, CA v3). Publish BEFORE D1. A funded-economy
  table with per-series verdicts is the P0 output; the mandatory lane's
  kill test runs HERE.
- **P1**: kernel regression (append-only publication per F-A7T-1;
  arm_config_digest in ledger rows).
- **P2**: coverage-first per proposal clock.
- **P3**: invariants freeze INCLUDING the diagnostic_output_contract
  and margin-to-fail scaffolding; no PnL.
- **D1/D2**: three blind lanes from one wave SHA; causal-claim +
  falsification-rule + expected-failure-mode frozen fields; the
  nominal-exposure control MANDATORY on lane 1; sham-calendar placebo
  mandatory wherever a calendar/print instant conditions the book;
  novelty vs the full inventory (incl. the V8 shadow pair) measured
  pre-selection; control identifiability measured pre-selection.
- **I/Q**: availability-lag mutation per conditioning field (a print
  arriving late must move the decision exactly one period); exact-arm
  sanitized dry-run, non-vacuous, recursive leak scan; twins at freeze
  + twin smoke-rerun; heavy phases under the machine-wide lock.
- **E**: max six serial cells after the two-key HARD STOP — A7
  fresh-context first (diagnostic gate in scope; 0 unresolved
  HIGH/CRITICAL), then the owner types, fresh and informed:

```text
GO FOREX V9 SCORED EXECUTION
```

- **Terminal**: reproduction from the twin; DSR over the forex program
  history (N = 42 + V9 cells) from persisted series; PBO fail-closed
  below 8 configurations; margins per gate; failure-registry append;
  program totals as-of-intake (P-9).

## 5. Hard boundaries

Unchanged from V8 §5: no signup/key/purchase BY AGENTS (the FRED key is
the owner's own signup, owner-placed in gitignored `.env`; keys
environment-only, redacted from error strings, never in chat/commits/
logs); no S1/paper/live/orders; no raw-data commit; no optimizer/rescue/
threshold weakening; no history rewrite; pushes only on owner
instruction; gates report PASS/FAIL/NOT_RUN/BLOCKED with commands, exit
codes, SHAs and margins; heavy jobs serialized machine-wide UNDER THE
LOCK (V13's crawl and V17's post-remediation phases are the expected
siblings — NOT_RUN_RESOURCE_CONFLICT, never contention).

## 6. First report from a fresh A1

```text
measured UTC / root / branch / HEAD / porcelain
V8 close-chain precondition verified: TERMINAL in registry, ledger
forex 42/42, program 236/239, root failure registry 56 --verify PASS
calendar + announcement-ledger pins re-verified (EMU v2, CA v3)
FRED key presence re-measured (PRESENT expected; assert, never assume)
governance mechanisms verified on-branch (tests + registry --verify)
CPI index-level availability pre-check (verdict per candidate series)
GO/NO_GO for P0
```
