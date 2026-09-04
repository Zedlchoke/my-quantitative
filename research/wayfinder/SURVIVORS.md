# Survivor ledger — mechanisms that passed every Stage-A gate

> Maintained by the Lead Engineer. One entry per surviving family, appended
> at terminal close. These are NOT deployable strategies: every survivor is
> locked pending a future owner-approved S1 (out-of-sample) plan. S1 remains
> sealed until that plan exists.
>
> 2026-09-05 owner audit: S-1 is downgraded to
> `PROVISIONAL_STAGE_A_SURVIVOR_PENDING_PIT_AUTHORITY`. The BIS availability
> timestamps were INFERRED (date-only upper bound asserted in code prose),
> not evidenced per event. See remediation conditions below and
> `PLAN_forex_v3r.md`.

## S-1 — FXFV3-A6-P1 (Forex V3 family2) — vol-gated policy-rate carry

```text
status           PROVISIONAL_STAGE_A_SURVIVOR_PENDING_PIT_AUTHORITY
                 (downgraded from PIT-audited by owner audit 2026-09-05;
                 engineering chain PASS, data-authority claim UNPROVEN)
remediation      PLAN_forex_v3r.md — announcement ledger + recompute under
                 corrected availability; survivor restored only if anchor
                 and neighbour still PASS every frozen gate unchanged
producer         proposal lane A6, blind, outcome-blind attested
certified by     A7 terminal 2a3e9f6 — C1..C8 all PASS, 0 HIGH/CRITICAL
freeze pins      W3C 331a3893184b10782f735be1248d9fa792fe5783
                 ledger sha256 6329cabcf80f6cc67009dec7f042fba3832607dd...
                 reproduction ALL_MATCH, byte-identical in both twins
denominators     forex 18/18 (V1 6 + V2 6 + V3 6); program 173 published
```

### Mechanism (plain words)

Uncovered interest parity fails in a signed, exploitable direction: the
currency of the higher-policy-rate area tends to *appreciate* rather than
depreciate by the differential (Fama 1984 forward-premium puzzle) — the
economic basis of carry. But naive carry has crash risk concentrated in
HIGH-volatility states (Brunnermeier–Nagel–Pedersen 2009 carry crashes;
Menkhoff et al. 2012: carry loads negatively on FX-vol innovations).

The family therefore **holds the per-pair policy-rate-differential direction
only while the pair's own trailing realized volatility is in the LOW tail of
its own trailing distribution, and unwinds to flat in the HIGH state**. The
tradeable object is the state-gated differential direction — not any price
pattern: direction comes exclusively from as-of BIS WS_CBPOL policy-rate
vintages read point-in-time; the volatility state is a conditioning gate on
holding, never an entry trigger.

### Frozen rule (single parameter set)

```text
decision clock    daily 16:00-NY, 7 authorized pairs (free-data contract)
direction_i       sign of as-of BIS WS_CBPOL differential, availability-gated
vol state         trailing realized vol of the pair: sum of H1 true ranges
                 per NY-day / 16:00-NY close; state_block 20 NY-days,
                 baseline 10 blocks; LOW tail = hold-eligible, HIGH = unwind
entry             next 16:00-NY bar open after state/direction agree
exit              HIGH unwind / differential sign flip reverse / force-flat
books             price-only AND financing-adjusted PnL, frozen formula
```

### Scored evidence (anchor / neighbour / control)

| arm | expectancy (fin-adj) | price-only | PF | trades | note |
|---|---|---|---|---|---|
| anchor | **+23.92** | **+5.53** | 1.331 | 113 | incremental alpha +12.32; MDD $1,830; break-even 4.26 bps |
| neighbour | +18.61 | +11.77 | 1.385 | 289 | different state parameters, same mechanism — supports |
| placebo control | −7.22 | — | — | — | **fails as designed** — the behaviour does not reproduce without the mechanism |

Robustness: drop-one-pair 8/8 and drop-one-fold survive; all three stress
tiers positive; USD-drift correlation −0.116 (clean); 2/3+ folds positive;
reproduction ALL_MATCH in both twins.

### Why it survived where 172 cells failed

1. **New information, not new arithmetic** — direction from policy-rate
   vintages (a non-price source, PIT-audited), not another transform of
   OHLCV.
2. **Low frequency** — 113 trades; costs cannot eat a 4.26 bps break-even
   (V1 forex died at 11k+ trades, cost-dominated).
3. **Honest books** — price-only expectancy is positive (+5.53): the
   financing formula does not manufacture the edge.
4. **Literature-grounded, with the documented failure mode gated** — the
   HIGH-vol unwind is exactly the Brunnermeier–Nagel–Pedersen crash state.
5. **Specificity proven by its own placebo** — the control arm loses, so the
   returns belong to the mechanism, not the book shape.

### S-1 owner-audit findings (2026-09-05) — why provisional

1. **Availability UNPROVEN**: `macro_fetch.py` stamps
   `available_time = end of effective_date` on the asserted basis that every
   CBPOL change is announced on or before its effective date. BIS payloads
   carry no historical availability stamps and the repo holds no per-event
   announcement records. `HISTORICAL_MARKET_AVAILABILITY = UNPROVEN`. This
   does not prove look-ahead — it means the evidence was never stored.
2. **Stage-A pass depends on the financing model**: price-only PF is
   **1.0687 < 1.10**; only the financing-adjusted book (PF 1.331) clears the
   PF gate. Price-only expectancy is positive (+5.53) but the financing
   approximation (policy-rate differentials, not broker swap/forward
   points/OIS) is not proven tradeable.
3. **Expectancy-to-PnL reconciliation required** (Lead Engineer addition):
   financing-adj expectancy 23.92 x 113 trades ≈ +2,703 vs booked
   financing_adjusted_pnl_usd +1,354.86; price-only expectancy +5.53 implies
   ≈ +625 vs booked price_only_pnl_usd **−692.29** (opposite sign). Units or
   book-basis mismatch — must be reconciled explicitly in V3R.
4. **Multiple testing unaddressed**: no DSR / PBO / White's Reality Check /
   FDR adjustment computed; with ~60 families and 173 published cells the
   Stage-A pass must be treated as best-of-many until S1.

### S1 conditions (binding, from the lock — unchanged)

- S1 stays SEALED_UNTOUCHED until a new owner-authorized plan opens it.
- No paper/live/orders, no promotion, no parameter re-tuning, no universe
  change between lock and S1.
- Any S1 plan must re-verify W3C and ledger pins before touching sealed data,
  and must carry the V3R remediation verdict plus the multiple-testing
  statistics above.
