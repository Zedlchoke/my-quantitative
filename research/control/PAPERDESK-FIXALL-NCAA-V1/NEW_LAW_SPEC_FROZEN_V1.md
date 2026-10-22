# NEW-LAW ERA SPEC — FROZEN V1 (PAPERDESK UPGRADE V2, U7)

- Lane: `.worktrees/paperdesk-fixall-ncaa-v1/integration`
  (`orca/paperdesk-fixall-ncaa-v1-integration`). Frozen: 2026-10-21.
- Status: **FROZEN — SHADOW ONLY.** Nothing in this spec changes any
  production decision today. The evaluator runs as a SHADOW
  (`research/papertrade_exec/new_law_shadow.py`, journal
  `<data>/ops/shadow_new_law.jsonl`, sandbox-aware) and the era OPENS only
  on a separate, explicit owner GO. Until that GO: paper 100%, current
  law unchanged, seal untouched.
- Registration: `sha256 (measured over this file with this line's digest
  value replaced by empty): 7a402a534100828d2a85807ab9d988e34940899b1e3c05df96be8a540c7aa986`
  (formula identical to AI_PROMPT_V2.md — the digest VALUE on this line is
  blanked before hashing, so the registration is self-consistent and
  re-measurable by anyone).

This spec freezes the DECISION LAW of the new era. Parameter values are
law, not tuning knobs; changing any frozen constant after the era GO is a
new spec with a new registration and a fresh future-only evaluation.

## 1. Scope and identity

The new law prices 2-way moneyline candidates (HOME/AWAY; a 3-way soccer
variant may be added only as a V2 spec). Inputs, per candidate:

- `p` — the model probability vector (the SAME frozen model the current
  law uses; the model itself is not changed by this spec);
- PM quote — the Polymarket decimal price for the leg being taken (the
  executable CLOB price; `p_pm = 1/decimal`);
- Pinnacle reference — Pinnacle h2h decimal odds for the match at decision
  time, vig-stripped by the U6 no-vig law
  (`p_pin_leg = (1/odds_leg) / Σ(1/odds)`, `clv_plane.no_vig_probabilities`);
- `chosen_leg` — the leg frozen by the decision pipeline.

Missing or degenerate inputs are NO_RUN — never guessed, never substituted.

## 2. Sharp-price gate (FROZEN)

The PM price is taken ONLY when it beats the Pinnacle no-vig reference at
decision time by the frozen margin, PM-fee-adjusted:

```
p_pm_eff  = p_pm + 0.05 · p_pm · (1 − p_pm)      [PM taker fee, applied ONCE — the pinned FEE_ONCE law]
TAKE-gate: p_pm_eff ≤ p_pin_leg · (1 − 0.03)     [SHARP_PRICE_MARGIN = 3%, frozen]
```

If the gate fails the candidate is SKIP (reason `SHARP_PRICE_GATE`).
The 3% margin is a transaction-cost-of-truth allowance: it demands the
exchange price be cheaper than the sharp book by more than the round-trip
noise floor before the new era will pay for the position.

## 3. Blended probability law (FROZEN)

EV is computed from a frozen log-odds blend of the MODEL probability and
the PINNACLE no-vig probability — NEVER with the PM price being taken
(the price is an input to cost, never to belief):

```
logit(p_blend) = w · logit(p_model) + (1 − w) · logit(p_pin_leg)
EV_blend       = p_blend − p_pm_eff
```

**Blend weight `w` — fitting protocol (recorded, NOT a fitted number):**

1. Corpus: every FORECAST match in the ledger + U6 CLV sidecar records
   with a Pinnacle close, STRICTLY BEFORE the era-open date `E` (the owner
   GO date). No data at or after `E` is ever touched (future-only scoring,
   §6).
2. Grid search `w ∈ {0.00, 0.05, …, 1.00}` maximizing out-of-sample
   log-score (log loss) of `p_blend` against realized outcomes, using
   rolling-origin folds (train on all data before fold cut, score the
   next month; folds walk forward; the reported `w` is the log-loss-
   weighted average of per-fold optima rounded to 0.05).
3. Guard rail: if `w = 1.00` (model only) wins, the blend collapses to
   the model and the spec is re-registered as V2 before the era opens —
   the owner is told the market added nothing.
4. The resulting `w` is written into THIS file as a registered amendment
   (new sha) BEFORE the first live new-law decision, and is then LOCKED.
   The SHADOW journal carries `p_model` and `p_pin_leg` in every record so
   any `w` can be re-applied offline; the shadow's own `w` is the
   PROVISIONAL identity weight 0.5 and is labeled as such — it is not a
   fit and confers no authority.

## 4. Disagreement-scaled edge threshold + kill gate (FROZEN)

```
threshold = 0.05 + 0.5 · |p_model − p_pin_leg|     [EDGE_BASE = 5%, EDGE_DISAGREEMENT_K = 0.5, frozen]
TAKE  ⇔  sharp-price gate PASS  AND  EV_blend ≥ threshold
```

When model and sharp book disagree, the candidate must clear a HIGHER bar
(disagreement is model risk, priced as such). Constants are frozen; the
sensitivity band below is the only sanctioned perturbation.

**Kill gate (era-level, evaluated by the owner on FUTURE scored data):**

- Real cost accounting: PM taker fee ONCE per fill (§2 formula), plus a
  0.5%-per-side slippage allowance on entry; no other cost is invented.
- Minimum evidence: **n ≥ 200 scored decisions** (TAKE decisions that
  reached settlement) before any GO/NO-GO verdict is even computed.
- Untouched holdout: the final verdict is computed on decisions AFTER the
  era-open date `E` only; the fitting corpus of §3 is never reused for
  the verdict.
- Sensitivity: every frozen parameter (margin 3%, base 5%, k 0.5, the
  locked `w`) is perturbed ±10% and ±20%; the verdict (positive vs
  non-positive expectancy, and the kill-line of the next bullet) must not
  flip sign across the band. A verdict that flips is NO-GO.
- Kill line: if realized CLV_pin mean < 0 OR realized ROI ≤ 0 over the
  first 200 scored decisions, the era is KILLED (config league_pauses
  entry, owner countersigns); no re-fitting on the killed window.

## 5. Per-league auto-cutoff keyed on the U6 CLV plane (FROZEN)

The U6 CLV plane (`clv_plane.py`, sidecar under `<data>/ops/clv/`) is the
era's tripwire. Per league, computed on scored bets only (placed bets with
both entry and Pinnacle close in the sidecar records):

```
rolling CLV_pin = mean of the last 30 scored bets' (entry_decimal /
                  pin_close_decimal − 1) on the chosen leg
AUTO-CUTOFF:    rolling CLV_pin < −5%  ⇒  the league pauses ITSELF
                (config league_pauses[league].active = true, reason
                NEW_LAW_CLV_CUTOFF, evidence = the sidecar record ids)
```

Implementation law: the cutoff check reads ONLY the U6 sidecar (measure
plane), never edits history; a pause is lifted only by an explicit owner
act recorded like the QD1 lift. The shadow annotates each record with the
league's CLV state when the report is available; the runner-side check
activates with the era GO, not before.

## 6. Scoring only on future data (FROZEN)

No new-law performance claim may ever be computed on data at or before
the era-open date `E`. The shadow journal accumulates from now (it is
forward-looking bookkeeping), but era verdicts, kill-gate arithmetic and
any published number use ONLY decisions taken after `E`. Backtests over
old ledger data may inform the §3 fit — nothing else.

## 7. What this spec does NOT change

- The current production decision law (EV ≥ 5%, PIT, stake, capital cap,
  AI authority gate) runs UNCHANGED until the owner GO for this era.
- The U6 CLV plane stays MEASURE-ONLY.
- The SHADOW evaluator writes only its own journal; it reads the ledger,
  never the gates.
- seal.js stays SEALED; feature gates stay exactly as the owner set them;
  paper 100%.
