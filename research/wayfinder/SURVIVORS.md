# Survivor ledger — mechanisms that passed every Stage-A gate

> Maintained by the Lead Engineer. One entry per surviving family, appended
> at terminal close. These are NOT deployable strategies: every survivor is
> locked pending a future owner-approved S1 (out-of-sample) plan. S1 remains
> sealed until that plan exists.

## S-1 — FXFV3-A6-P1 (Forex V3 family2) — vol-gated policy-rate carry

```text
cycle            FOREX-FREE-V3 (closed 2026-09-05T05:02+07:00)
status           FIRST STAGE-A SURVIVOR OF THE PROGRAM (after 172 rejections)
                 LOCKED FOR FUTURE OWNER-APPROVED S1 PLAN ONLY
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

### S1 conditions (binding, from the lock)

- S1 stays SEALED_UNTOUCHED until a new owner-authorized plan opens it.
- No paper/live/orders, no promotion, no parameter re-tuning, no universe
  change between lock and S1.
- Any S1 plan must re-verify W3C and ledger pins before touching sealed data.
- Multiple-testing context for interpretation: this family survived within a
  program of 173 published cells / ~60 families; S1 exists precisely to
  separate real edge from best-of-many.
