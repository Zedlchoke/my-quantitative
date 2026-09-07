# FOREX-FREE-V7 — THE SPILLOVER FRONTIER: CROSS-ECONOMY REACTION CONDITIONING

> Owner plan dated 2026-09-07, drafted by the Lead Engineer from V6's
> measured terminal (A7-terminal CONFIRM chain verified). Activates on
> owner dispatch; nothing starts on its own. A correct
> `FOREX_FREE_V7_REJECT_ALL` is a successful research run.
>
> `plans/PLAN_forex_v6.md` and all earlier forex plans/records are closed
> historical authorities.

## 0. Frozen starting point

```text
V6 terminal            4d81dcd + A7 terminal CONFIRM 0dead47 (recomputed
                       from bytes; 4 findings, 0 blocking) + closeout
                       e645aca (kernel debt F-A7-T-1, gate-equality quirk,
                       verdict-neutral, carried as owner item)
V6 outcome             FXFV6-A4-P1 own-economy reaction-direction drift is
                       the forex season's near-miss: anchor fin-adj
                       +824.37 @tier2.0 (+0.963/trade, 208 trades) dying
                       on FOUR robustness gates — PF 1.0979 vs 1.10
                       (margin −0.0021, razor per P-2), GBPUSD pair
                       concentration 0.4257 vs 0.40, break-even 3.475bps
                       vs 1.5 floor, LOPO 3/4; k=10 neighbour out-earned
                       (+1922.02, PF 1.1142) failing its own gates.
                       SHAM CONTROL NEGATIVE (−910.40, PF 0.899): the
                       release-DIRECTION conditioning carries GENUINE
                       calendar information (V5's sham-shadow
                       counter-evidenced) — the family dies on robustness,
                       not mechanism absence. FXFV6-A6-P2 USD PC1-gated
                       reversal mechanically dead (−3.299/trade).
denominators           forex 33/33; program 218/221 (ledger authority,
                       P-9); budget 0/6 for V7; S1 SEALED_UNTOUCHED
durable assets         evidenced per-print calendars (GB 88 / CA 105 /
                       AU 23 / NZ 30 in-S0 clocks), announcement ledger
                       250 rows (base + cf1f01a7 + EMU v2 repair + CA v3
                       timezone fix — intraday-grade stamps available)
owner-keyed door       FRED_API_KEY ABSENT in .env (measured 2026-09-07)
                       — the market-based real-rate axis stays
                       DATA_BLOCKED_VALID until the owner signs up and
                       places the key (free signup, like EODHD)
governance adoption    V7 is the FIRST FOREX cycle past the adoption
                       boundary (FAMILY_PIPELINE §11) and ADOPTS the
                       three mechanisms now merged on main@77e31ff —
                       see §3 (mandatory)
```

## 1. What is closed and may not be rescued

The cumulative forbidden inventory through V6, now including: the
**own-economy reaction-direction drift form** (V6's A4-P1 — robustness-
killed; re-entering the same conditioning on the same own-economy pairs
at any k/window/parameter is rescue; the near-miss is recorded, not a
license) and the **USD PC1-concentration-gated reversal form** (A6-P2).
All priors stand: release-window position-avoidance + the sham-calendar
shadow (V5), the carry region (V4 measured rho), session momentum/fade
(V1/V2), vol-gated carry (V3R invalidated). The V3R economic observation
(PF 1.2825 under honest availability) stays recorded — not a license.
A cross-economy proposal that turns out to be the own-economy anchor in
new words dies at D2 by measured pooled rho vs the V6 exposures.

## 2. Mission and allowed scope

V7 asks one question:

> Does CROSS-ECONOMY spillover conditioning — reactions measured on
> NON-reporting currencies around the evidenced GB/CA/AU/NZ release
> calendars — carry incremental after-cost information, beyond what the
> dead own-economy form already failed to monetize?

The mechanism class is genuinely different from V6's: the forced
traders are cross-border (importers/exporters invoicing in dominant
currencies, hedgers and liquidity providers rebalancing when a FOREIGN
bloc's print moves global risk), not the reporting economy's own
rate-expectation market. Literature lineage: exchange-rate news
spillover, dominant-currency pricing (Gopinath), common-factor reaction
to scheduled macro news. The falsification control class is mandatory
and mirrors the house standard: a **sham-calendar placebo** (shifted
release dates, matched windows) MUST run under evidenced semantics —
V6's sham-NEGATIVE is the proof that this control discriminates.

Three sanctioned axes (wave diversity binding):

1. **cross-economy spillover** (mandatory lane): direction/volatility
   conditioning on non-reporting pairs around the evidenced prints
   (e.g. EUR/JPY-cross reactions to GB prints; commodity-bloc crosses
   to AU/NZ prints) — coverage-first: bookable non-reporting decision
   windows per calendar measured in P0 BEFORE proposals.
2. **market-based real-rate structure — IF AND ONLY IF the owner
   unlocks FRED** (key in `.env`): vintaged breakeven/real-yield series
   with true PIT semantics; the preregistered V4/V5 inflation classes
   (real-differential, PPP-deviation) test here. Without the unlock
   this lane is DATA_BLOCKED_VALID, carried again.
3. **open axis**: any literature-backed mechanism on authorized data in
   the non-forbidden space.

Binding rules carried: availability evidence absolute (P-1); margin-to-
fail per gate (P-2); controls recompute under semantics change (P-3);
stress tier 2.0 primary; dual books (price-only must not invert sign);
daily-or-slower clocks (intraday only where stamps prove it); break-even
bps mandatory; |rho| <= 0.20 pooled vs ALL forbidden ancestry INCLUDING
V6's two forms and the V5 shadows; exactly three arms; max six cells;
unused slots never reassigned.

Allowed terminal outcomes:

```text
FOREX_FREE_V7_REJECT_ALL
FOREX_FREE_V7_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
FOREX_FREE_V7_BLOCKED_DATA_OR_SELECTION
FOREX_FREE_V7_BLOCKED_PRELAUNCH
FOREX_FREE_V7_INCOMPLETE_NOT_PROMOTABLE
```

`BLOCKED_DATA` is live and cheap: if spillover coverage (bookable
non-reporting windows per evidenced calendar) cannot fund conditioning
clocks, the axis dies in P0 before any proposal exists.

## 3. Governance adoption (mandatory in V7 — first forex cycle past the boundary)

The three mechanisms are merged on main (`77e31ff`; modules in
`research/governance/`). V7's plan preregisters and ADOPTS:

1. **Diagnostic persistability gate** — the run contract carries a
   `diagnostic_output_contract` using the CANONICAL
   `CATEGORY_REQUIRED_FIELDS` (per-period series with arm_id/period/
   returns MANDATORY — DSR/PBO must never be NOT_RUN for missing bytes
   again: V3R + V15 + P-11); schema ids resolve to the registered
   `diag/<category>@1`; the twin smoke-rerun proves fresh emission in an
   empty sandbox. Gate runs BEFORE A7 launch authorization; any gap is
   BLOCKED_PRELAUNCH.
2. **Global heavy lock** — every heavy phase acquires the machine-wide
   lock (`~/.my-quantitative-governance/heavy_runtime`); FAILED
   releases carry the stderr tail in the release note.
3. **Failure memory** — at close, families append to
   `research/wayfinder/FAMILY_FAILURES.jsonl` under the five-class
   taxonomy; the V6 rows exist and are the near-miss memory this plan
   builds on.

## 4. Cycle structure (standard, deltas only)

- **P0 (A3)**: spillover coverage census on the evidenced calendars
  (non-reporting pairs × release events; bookable windows; dead/no-data
  pairs excluded fail-closed); calendar + ledger pins re-verified
  (incl. EMU v2, CA v3); FRED unlock re-measured (key presence, one
  probe call class only if present). Publish BEFORE D1.
- **P1**: kernel regression (append-only publication per F-A7T-1 debt
  note; arm_config_digest in ledger rows per F-TERM-4).
- **P2**: coverage-first per proposal clock.
- **P3**: invariants freeze INCLUDING the diagnostic_output_contract
  (§3.1) and margin-to-fail scaffolding; no PnL.
- **D1/D2**: three blind lanes from one wave SHA; proposal packets
  carry causal_claim_one_sentence + falsification_rule +
  expected_failure_mode; sham-calendar control MANDATORY on lane 1;
  novelty vs the full inventory (incl. V6 forms) measured pre-selection;
  control identifiability measured pre-selection.
- **I/Q**: availability-lag mutation per conditioning field; exact-arm
  sanitized dry-run, non-vacuous, recursive leak scan; twins at freeze
  + twin smoke-rerun under the diagnostic gate; heavy phases under the
  machine-wide lock.
- **E**: max six serial cells after the two-key HARD STOP — A7
  fresh-context independent first (diagnostic gate in its scope), then
  the owner types, fresh and informed:

```text
GO FOREX V7 SCORED EXECUTION
```

- **Terminal**: reproduction from the twin (per-period series exist);
  DSR over the forex program history (N = 33 + V7 cells); margins per
  gate; failure-registry append; program totals as-of-intake (P-9).

## 5. Hard boundaries

Unchanged from V6 §5: no signup/key/purchase BY AGENTS (the FRED key,
if any, is the owner's own free signup placed by the owner in gitignored
`.env`); no S1/paper/live/orders; no raw-data commit; no
optimizer/rescue/threshold weakening; no history rewrite; pushes only on
owner instruction; gates report PASS/FAIL/NOT_RUN/BLOCKED with commands,
exit codes, SHAs and margins; heavy jobs serialized machine-wide UNDER
THE LOCK (sibling cycles — stocks V11, crypto V16 — respected with
NOT_RUN_RESOURCE_CONFLICT).

## 6. First report from a fresh A1

```text
measured UTC / root / branch / HEAD / porcelain
V6 terminal + A7T CONFIRM chain verified; forex 33/33, budget 0/6, S1 seal
calendar + announcement-ledger pins re-verified (EMU v2, CA v3)
governance mechanisms verified on-branch (54 tests, registry --verify)
spillover coverage pre-check (bookable non-reporting windows per calendar)
FRED unlock status (key presence measured, not assumed)
GO/NO_GO for P0
```
