# FOREX-FREE-V3R — DATA-AUTHORITY REMEDIATION FOR THE PROVISIONAL SURVIVOR

> Owner remediation plan dated 2026-09-05, drafted from the owner audit that
> downgraded FXFV3-A6-P1 to `PROVISIONAL_STAGE_A_SURVIVOR_PENDING_PIT_AUTHORITY`.
>
> This is an audit-remediation cycle, not a research cycle: the strategy is
> FROZEN byte-identical and is never adjusted. The only question V3R answers
> is whether the Stage-A result survives once BIS availability timestamps are
> replaced by evidenced announcement timestamps. S1 stays sealed throughout.

## 0. Frozen starting point

```text
cycle being remediated   FOREX-FREE-V3 (closed 2026-09-05)
survivor (provisional)   FXFV3-A6-P1 family2 — vol-gated policy-rate carry
W3C                      331a3893184b10782f735be1248d9fa792fe5783
ledger sha256            6329cabcf80f6cc67009dec7f042fba3832607dd...
downgrade                PROVISIONAL_STAGE_A_SURVIVOR_PENDING_PIT_AUTHORITY
                         (SURVIVORS.md S-1 audit findings 1–4)
forbidden from V3R       any change to parameters, universe, cost schedule,
                         volatility gate, decision clock, arms, gates or
                         thresholds — rescue by any name is vetoed
```

## 1. Mission

> Replace the INFERRED BIS availability bound (`available_time = end of
> effective_date`, asserted in code prose) with PER-EVENT EVIDENCED
> announcement timestamps from official central-bank sources, then recompute
> the exact frozen W3C strategy and let the result decide the survivor's
> fate. No outcome is privileged: if the corrected availability kills the
> result, the honest verdict is `FOREX_FREE_V3_DATA_AUTHORITY_INVALIDATED`.

## 2. Phase V3R-R1 — announcement ledger (the missing evidence)

Build `research/control/forex_free_v3r_run/announcement_ledger.jsonl`, one row
per policy-rate change event per currency area, covering every event the
scored window reads:

- currency areas: USD (Federal Reserve), EUR (ECB), GBP (Bank of England),
  JPY (Bank of Japan), CHF (SNB), CAD (Bank of Canada), AUD (RBA), NZD (RBNZ)
  — the USD leg is included because the differential direction needs both
  sides;
- per event: official source citation (URL/press-release identifier), raw
  bytes archived under hash, announcement timestamp (UTC, as precise as the
  source provides), effective date, old/new rate, and the decision-clock
  mapping (first 16:00-NY decision at which the change is readable under the
  evidence);
- unscheduled/emergency moves must be flagged explicitly — they are the
  events most likely to violate the "announced on or before effective date"
  assumption;
- events where the announcement timestamp cannot be evidenced from an
  official source are recorded `AVAILABILITY_UNEVIDENCED` and the conservative
  bound used for them is the LATER of (end of effective day, first BIS
  publication stamp) — never the earlier;
- the ledger is append-only and hash-pinned before any recompute.

## 3. Phase V3R-R2 — corrected-availability recompute

Recompute the EXACT W3C strategy (code hashes verified against the W3C
freeze before running; zero edits permitted) with one and only one change:
`available_time_utc` for macro rows now comes from the announcement ledger.
Report BOTH books per cell (price-only and financing-adjusted under the
frozen formula), plus:

- a per-event diff table: every decision whose readable rate differs between
  the old (inferred) and new (evidenced) availability;
- the expectancy-to-PnL reconciliation (audit finding 3): per arm, show
  n_trades, expectancy basis definition from the frozen scoring contract,
  and the arithmetic bridging expectancy x count to booked PnL for both
  books — including why price-only expectancy (+5.53) coexisted with
  price_only_pnl_usd −692.29;
- the multiple-testing statement (audit finding 4): Deflated Sharpe Ratio and
  Probability of Backtest Overfitting computed over the published program
  history, reported for the record (S1 remains the arbiter).

## 4. Phase V3R-R3 — independent A7 data-authority audit

A7 audits, without repairing anything:

- announcement-ledger completeness vs the union of rate-change dates the
  scored books actually read;
- evidence quality per event (official source, timestamp provenance);
- recompute determinism from the W3C twin;
- the reconciliation table above;
- gates re-evaluated UNCHANGED against the corrected books.

## 5. Phase V3R-R4 — verdict (binary, no middle path)

```text
IF anchor AND neighbour still PASS every frozen Stage-A gate
   (financing-adjusted book governs, price-only reported, all other gates
   unchanged) under corrected availability:
     survivor RESTORED to full Stage-A standing; SURVIVORS.md updated;
     PLAN S1 may be drafted (separate owner decision).

OTHERWISE:
     verdict FOREX_FREE_V3_DATA_AUTHORITY_INVALIDATED recorded in the V3
     lineage; the family joins the forbidden inventory as a
     data-authority-invalidated row; no parameter, universe, cost, gate or
     threshold may be adjusted to save it; S1 is not opened for it.
```

The placebo control is expected to remain non-reproducing in both outcomes;
its behaviour is reported, not gated on.

## 6. Boundaries

- S1 SEALED_UNTOUCHED; no paper/live/orders/credentials.
- No strategy edits of any kind; the W3C code is executed, never modified.
- No new data sources beyond the official CB announcements (public, keyless).
- No rewriting of V3 artifacts: the recompute writes to new V3R artifacts;
  the original six cells and their ledger stay byte-immutable historical
  evidence, with the V3R outcome recorded as an append-only adjudication.
- Report gates only as PASS/FAIL/NOT_RUN/BLOCKED. A correct invalidation is
  preferable to a preserved survivor built on inferred timestamps.

## 7. First report from a fresh A1

```text
measured UTC / root / branch / HEAD / porcelain
V3 W3C + ledger pins re-verified
S-1 provisional status + the four audit findings restated
announcement-ledger coverage plan (events per area, sources)
V3R worktree path / branch / base SHA
GO/NO_GO for R1
```
