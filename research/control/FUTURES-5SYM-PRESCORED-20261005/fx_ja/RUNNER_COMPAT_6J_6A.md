# RUNNER_COMPAT_6J_6A — scored-runner requirements & acceptance checks (DRAFT)

- Lane FXJA, round FUTURES-5SYM-PRESCORED-20261005, PREP-only. Defines what
  the symbol-parameterized scored runner (EXEC lane deliverable) MUST
  support before any 6J/6A identity can route through it. No runner runs
  this round; every check below is a draft acceptance gate. 0 PnL.

## §1 Runner requirements

1. **Contract specs (identity layer)**
   - 6J: multiplier 12,500,000 JPY; tick 5e-07 USD/JPY = $6.25; quote USD
     per JPY. Refuses any 1e-6/1e-4 legacy grid (rejected on data,
     `6j_identity.json`).
   - 6A: multiplier 100,000 AUD; **era-dependent tick** — 1e-04/$10.00
     (sessions ≤ 2020-11-20), 5e-05/$5.00 (≥ 2020-11-23); quote USD per
     AUD. The runner carries the era table, not a scalar tick.
2. **Quote-direction handling (6J-specific, load-bearing)**
   - All sign conventions resolved IN 6J PRICE TERMS (yen-strong = positive
     6J return); any USDJPY-denominated input (e.g. a future MOF zone
     level) enters through an explicit declared sign inversion in the
     identity table. Acceptance: a runner probe on the committed
     orientation slice (2024-07-11, 6JU4 +1.73% vs USDJPY 160.04→157.32)
     must classify the day's direction as POSITIVE 6J return
     (`6j_orientation_recheck.json`).
3. **Era-dependent tick/cost (6A)**
   - Cost binding branches per session era (COST_CONTRACT §2/§3); the
     no-back-cast law is enforced at runtime: an era-2 cost constant
     touching an era-1 session is a hard error. Acceptance probe: compute
     a synthetic era-1 vs era-2 round-trip and require $104.92 vs $54.92
     at T1/S1/×1.0.
4. **Session masks**
   - 6J: 23h CT continuous 17:00→16:00, no maintenance break, 1,380 nominal
     minutes; Tokyo windows bucketed Asia/Tokyo via zoneinfo (DST-correct);
     holiday-shortened sessions excluded by the coverage rule before any
     window statistic.
   - 6A: 17:00 CT Sun → 16:00 CT Fri with the 60-min break; AF1/AF3 windows
     bucketed Australia/Sydney (and Asia/Shanghai for the China window),
     DST-correct in BOTH hemispheres; the opposite-DST natural experiment
     (AF3 C3″) must be computable from the mask layer alone.
5. **BoJ / RBA / MOF date-stamp injection**
   - Injected as date-level PIT calendars: BoJ MPM dates (54, FACT) —
     **never** intraday stamps (NOT_IN_CORPUS; injection of any stamp is a
     runner violation); MOF DISCLOSURE dates with the lag law (labels built
     on disclosure, never op date); RBA decision dates with the 14:30-Sydney
     declared convention and the effective_date − 1 AU-BD rule; FOMC
     statement days (AF1 base-excludes; ES standing-outside shape).
   - Every injected calendar carries its provenance class (FACT / v1-FACT /
     declared-convention / NOT_OBTAINED) in the run manifest.
6. **Cost binding**
   - Consumes the freeze's `cost_binding.json` (COST_CONTRACT ×1.0 gate
     column + ×1.5/×2.0 views); applies the conservative fill law (next-bar
     open, SL-priority, no limit/queue claims); session-of-day slippage
     floor for Tokyo-window / Sydney-morning fills (+1 tick entry-side,
     PROVISIONAL, declared); forbidden-word scan applies to runner output.
7. **Fold routing**
   - Yearly sequential folds with 252-session warmup carve-outs (SPEC_6J §8
     DRAFT shape); folds multiply evaluation, never identities; era seams
     as declared K-views, never resplits; 6A era-1 rows route ONLY to
     descriptive outputs (fold floor law); S1 = SEALED_UNTOUCHED.
8. **Chain consumption**
   - 6J: baseline k=5 chain of record with the flagged 2022-09-20 artifact
     (or cease-guard variant per D9 if ratified); 6A: explicit cease-guard
     variant chain MANDATORY (0 violations); switch-day returns
     spread-adjusted; mode labels (abrupt/gradual) carried from
     `rmm_mode_ledger.json` / `6a_roll_measured.json`.
9. **Ledger law (P-9)**
   - Every registered identity counts into the observed denominator
     regardless of publication failure; readiness measurements never enter
     scored-trial denominators.

## §2 Acceptance checks (draft; all must PASS before any 6J/6A scored cell)

| # | check | expected |
|---|---|---|
| A1 | identity grid probe: 6J tick/multiplier vs `6j_identity.json`; 6A era table vs `6a_tick_adjudication.json` | exact match, both symbols |
| A2 | orientation probe (§1.2) | 2024-07-11 classifies +6J; USDJPY inversion applies |
| A3 | era cost probe (§1.3) | era-1 $104.92 / era-2 $54.92 at T1/S1/×1.0; era-2-into-era-1 raises hard error |
| A4 | chain probe | 6J 27/27 vs `held_volume_k5.parquet` (+2022-09-20 artifact flagged); 6A cease-guard 27/27 with 0 violations |
| A5 | calendar injection probe | BoJ = dates only (any stamp ⇒ FAIL); MOF labels disclosure-dated; RBA −1-BD rule lands 2020-03-19 correctly |
| A6 | session mask probe | Tokyo 09:00 JST found across US DST flips; Sydney 14:30 across AU DST; AF3 C3″ computable |
| A7 | cost binding probe | ×1.0 gate number == freeze digest; ×1.5/×2.0 disclosed views; no "measured cost" string in output |
| A7R | repro twin (G8 shape) | byte/logical match on chain + manifests |
| A8 | fold routing probe | folds multiply evaluation only; 6A era-1 → descriptive-only sink |
| A9 | authority probe | runner refuses to start without the §3 gate tokens |

## §3 Authority coupling (fail-closed)

The runner refuses to start unless the FREEZE_BUILDER_SPEC §5 gate tokens
are present in the selection freeze: 6J — ceiling (P5-D1) + fill law
(P5-D3) + cost A7 (D2); 6A — PB3 lift + D8 (+ D9, + D2 for cost-bearing).
Missing any token ⇒ `BLOCKED_*` at start, never mid-flight. **Today: both
refuse paths armed; the runner is a requirement document, not an executable
path.**

— End RUNNER_COMPAT_6J_6A.
