# OWNER_DECISIONS — FUTURES-SIX-READINESS-20261004 (controller synth, 2026-10-04)

D1–D7 are CARRIED UNCHANGED from the sibling round FUTURES-P3-QUARANTINE-20261004
(`…/FUTURES-P3-QUARANTINE-20261004/synth/OWNER_DECISIONS.md`) — restated here in one line each so this
packet is self-contained; full context and options live there. D8–D12 are NEW from this round's verified
findings. Nothing here is authorization by itself; every ruling must be written.

## Carried (unchanged)

- **D1** P3 transport adjudication (accept-exception vs permanent quarantine; recommended default B).
- **D2** Authorize the fee A7 (packet READY; 4 sub-rulings e.1–e.4). Until ruled: all fees stay
  MODELED / VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW — re-confirmed by this round (no D2 artifact exists;
  71 grep hits all negations).
- **D3** NFA-basis $0.01/side for ES/NQ all-ins (NFA 0.02 vs offset 0.01). Both files re-hashed unedited.
- **D4** ES denominator: 36 minimal vs 24 frozen (headroom 0; all ES families BLOCKED_TRIAL_BUDGET).
- **D5** CPI Jan-2026 announcement pin (permitted routes only).
- **D6** Remaining calendar cells (sibling list) — this round already closed part of it via FX-EB lane
  (6E +2, 6B +10, holiday tables); the genuinely-absent remainder is unchanged.
- **D7** NG signed-surprise rule + comm data path (not this round's symbols; carried).

## New (from this round, all verified by VERIFY-A7READY)

### D8 — 6A era-aware tick/cost law
Finding: 6A min tick was **1e-04 ($10.00/tick) for sessions 2020-01-02..2020-11-20**, then **5e-05
($5.00/tick) from 2020-11-23** (GCD-verified on 327k+ closes, zero odd prints; vendor definitions match
era 2). The baseline's "$5 throughout" is wrong for the 2020 sub-era.
- **Option A — ratify the era boundary as measured** (2020-11-20/23 weekend): any future 6A cost spec or
  slippage model must be era-aware; fixes the understated 2020 tick-value costs now.
- **Option B — demand a vendor/exchange document before freezing**: keeps the data-derived boundary as
  PROVISIONAL; 2020-era 6A cost work stays blocked on that document.
- Default fail-closed if undecided: era-2-only cost models may not back-cast into 2020-era windows.

### D9 — Explicit cease-guard as the standard chain-builder law (3-symbol evidence)
Finding: the k=5 volume-crossover rule's weak implicit cease-guard is now PROVEN to bite on real data —
6J 2022-09-20 (law), **6A twice** (2024-12-17 dead-held 6AZ4 while 6AH5 traded 55,675 lots; 2026-06-16
dead-held 6AM6 while 6AU6 traded 55,533), and NQ's BEFORE chain once (NQH0_2020 dead-held 49 sessions —
eliminated by this round's v3 rebuild). Explicit-guard variants produce 0 violations with identical roll
dates (except 1 session earlier at the two 6A switches).
- **Option A — adopt "explicit cease-guard mandatory" as a standing data-prep law** and ratify the
  NQ cache_v3 chain (+ guard variants) as the canonical starting point for any future NQ/FX chain build.
- **Option B — leave per-cycle choice**: each future spec decides; the 3 manifestations are recorded as
  precedent.
- Note: ERRATUM-F1 obligation (re-measure 2020 NQ aggregates before any registered cycle consumes them)
  is DISCHARGED by this round's verified rebuild; consumption still requires that cycle's own data freeze.

### D10 — Sibling Q5 coverage over-claim (erratum acknowledgment)
Finding: Q5's coverage JSON lists 23 ES deviation captures; **8 are absent from disk and absent from Q5's
own fetch_log**; zero claimed cells depend on them (this round verified 23/23 claimed cells from the 15
present captures). MINOR.
- **Option A — owner notes the erratum**; the sibling round's artifact keeps working status with this
  round's `es/q5_independent_verify/` as the corrective evidence.
- **Option B — ask the sibling lane (if still live) to append its own erratum.** Either way, no value
  changes.

### D11 — Databento corpus rights posture (beyond read-only research)
Finding (VERIFY lane, from the acquisition ledger): the av1trim corpus is an **owner-authorized paid
purchase** (approved 2026-10-02, ceiling $125, delivered $105.81, ledgered). This round consumed it
read-only under that entitlement. License text is not in the repo → **rights beyond read-only research
reuse are UNRESOLVED (fail-closed)**.
- **Option A — owner records the license class** (e.g. personal/internal research, redistribution
  prohibited) in one line; nothing else changes for PREP rounds.
- **Option B — leave UNRESOLVED**: any future use beyond read-only research (external sharing,
  redistribution, derived-products) requires a fresh ruling first.

### D12 — Residual NOT_OBTAINED calendar cells (post-this-round remainder)
Still open with no legitimate archive source identified: 6E ECU26/ECZ26; 6B 2023Q1–2024Q2 + all holiday
windows (0/42); 6J 2023+2026 quarters + holiday times; 6A 2023Q1/Q2+2026 quarters; NQ 2026 holiday
deviations; (non-mission symbols carried under D6/D7).
- **Option A — bounded permitted-route extension lane next round** (Wayback CDX on the remaining
  product-id endpoints; ≤2 attempts/URL/method): historically yields ~partial recovery (this round:
  +12 FX quarters, +34 holiday windows from 19 fetches).
- **Option B — leave NOT_OBTAINED**: readiness matrices already reflect them accurately; nothing
  downstream misleads.
- No purchase/signup is proposed anywhere in this packet.

— All decisions can be issued in one written ruling; D2 remains the only fee-layer exit from UNDER REVIEW,
D4 the only ES budget exit. This round raises no gate, requests no GO.

— End OWNER_DECISIONS.md.
