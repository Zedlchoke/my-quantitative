# PLAN — WEATHER-LABEL-EQUIP-PREP-V1 (public-observation label law vs PM weather contract rules, $0, 0 scored)

- cycle_id: `WEATHER-LABEL-EQUIP-PREP-V1` · asset: shared · **budget 0/0** ·
  no GO phrase (PREP only)
- Owner instruction 2026-10-17: sole goal — determine whether PUBLIC
  observation data can produce labels correct under the Polymarket weather
  contract rules for KLGA, KORD, KMIA. NOT a scored GO, NOT authorization for
  further Polymarket access of any kind.

## 1. Frozen inputs + source law

- PM contract pins from prior PREP cycles are the ONLY venue input
  (`PM-PAPER-CAPTURE-PREP-V1/contract_pins/weather_*.json`,
  `WEATHER-PM-STATION-MAPPING-PREP-V1/` artifacts) — read-only citations.
  **No Polymarket API/website call, and no alternative settlement source**
  (this includes weather.gov/wrh/timeseries — the venue's resolution table —
  reading it for any day would be reading settlement data; banned).
- NWS `api.weather.gov` observations/station metadata: authorized (open
  data, free to use for any purpose; UA required) — provenance established
  in WEATHER-PM-STATION-MAPPING-PREP-V1 @ c33cc6ca; fetched AGAIN this cycle
  for observation endpoints with raw bytes sha-pinned.
- IEM: if still 404/unreadable → `NOT_RUN_SOURCE`, no silent source swap.

## 2. Work

1. **Station/provenance pins**: per KLGA/KORD/KMIA — station ID, coordinates,
   observation type (METAR), raw timestamps, units, and any QC/QC-history
   fields the API exposes. Raw responses committed + hashed.
2. **Label law per market/era** drafted ONLY from pinned
   `resolution_rules_verbatim`: measured quantity (highest/lowest hourly
   "Temp"), resolution source as written (wrh timeseries), observation-day
   window by IANA zone incl. DST (America/New_York, America/Chicago),
   hourly cadence, peak-extraction rule, unit conversion, whole-°F rounding
   (venue reports whole °F — our rounding rule must be pinned separately and
   marked unverified against venue practice), bucket boundaries from the
   pinned bracket questions. Hourly max vs daily/sub-hourly max are treated
   as DIFFERENT quantities unless evidence proves otherwise (none available
   this cycle ⇒ stated, not assumed).
3. **Requirement map**: rules requirement ↔ observation field ↔ transform ↔
   evidence status per row.
4. **Representative-day raw-byte checks** (no outcomes, no accuracy/metrics):
   one ordinary past day + the two DST 2025-11-02 (fall back) and
   2026-03-08 (spring forward) via
   `api.weather.gov/stations/{id}/observations?start=...&end=...` — verify
   timestamps are UTC monotone, units, midnight-local window behavior across
   DST.
5. **Verdict per city (and era = single current era)**:
   - `LABEL_LAW_EVIDENCED` only if every label-law link is evidenced;
   - `PROXY_ONLY` if public obs only approximate the venue's stated source;
   - `NOT_RUN_LABEL` / `NOT_RUN_SETTLEMENT_EQUIVALENCE` where a source is
     missing or equivalence to the venue's resolution mechanism cannot be
     checked. Never upgrade "NWS labels constructible" to "matches
     Polymarket settlement".

## 3. Expected honest outcome

The venue resolves off wrh hourly table; this cycle may not read it; NWS
api.weather.gov obs are a related but distinct feed (timestamp/unit/rounding
semantics unproven equal) ⇒ per-city verdict expected
**NOT_RUN_SETTLEMENT_EQUIVALENCE** with the NWS label capability recorded as
PROXY_ONLY evidence quality. The label LAW itself (brackets, windows, DST,
cadence, rounding spec) is drafted and evidenced from pins.

## 4. Verifier + fences

Independent verifier re-measures: station identity vs raw bytes; IANA/DST
window derivation (incl. the two DST days from raw obs); units; rounding
spec presence; bucket boundaries vs pinned question text; provenance URLs +
hashes; manifest integrity; fence scan (no wrh fetch, no venue call, no
outcome reading, no metric/EV/PnL numbers, no Central Park/Midway reuse).

Never: push, merge to main, `git add -A`, credentials, purchases, signups,
venue API calls, collector activation, model fits, VAL/TEST reopening,
EV/PnL, orders. Stop at PREP closeout with exactly ONE next-step proposal,
without opening any subsequent gate.
