# PLAN — WEATHER-PM-STATION-MAPPING-PREP-V1 (venue-independent station chain KLGA/KORD/KMIA, $0, 0 scored)

- cycle_id: `WEATHER-PM-STATION-MAPPING-PREP-V1` · asset: shared ·
  **budget 0/0** · no GO phrase registered (PREP only)
- Owner instruction 2026-10-17 (this chat): advance the venue-independent
  model part of the "fast path" round. Use NOAA/NWS, GFS-NODD and IEM **after
  re-checking source terms**. From the existing PM-PAPER-CAPTURE-PREP-V1
  contract pins, prepare a station chain per station:
  **station → coordinates → GFS cell → timezone / observation-day → label
  source** for KLGA, KORD, KMIA. Never reuse Central Park / Midway labels by
  city name. Build/check pipeline, PIT, missingness and QC only. If any chain
  link lacks evidence, record `NOT_RUN_STATION_MAPPING` for that station and
  overall — never fill by speculation.

## 1. Sources and rights (re-checked before any fetch beyond station metadata)

- `api.weather.gov` / `www.weather.gov` (NWS): U.S. federal works — public
  domain (17 USC §105); API docs require a identifying User-Agent and
  request pacing. Allowed: station metadata GETs, hourly observations.
- GFS-NODD (AWS Open Data / registry.opendata.aws `noaa-gfs-bdp-pds`):
  NOAA public-domain model output on AWS Open Data — free retrieval, no
  credential.
- IEM ASOS archive (Iowa Environmental Mesonet, Iowa State):
  per IEM usage statement data are free for use with attribution; usage page
  URL + retrieval date must be quoted in the rights table.
- **No venue API calls at all**: no Polymarket, no Kalshi, no exchange data.
  Settlement/equivalence comparison against any venue's resolution source is
  **deferred and not authorized** — label equivalence therefore stays
  UNVERIFIED by design of this cycle.

## 2. Inputs frozen (read-only citations from PM-PAPER-CAPTURE-PREP-V1)

- `contract_pins/weather_*.json` (12 pins): per-city
  `resolution_rules_verbatim` names the PM station (KLGA / KORD / KMIA),
  `game_start_time` fixes the observation-day timezone
  (measured: CHI 05:00Z = local midnight Central; NYC and MIA to be
  re-measured from their own pins in-cycle), `end_date 12:00Z` is a
  placeholder, not resolution time.
- WEATHER-TEMP-PROB-V1's consumed TEST and all frozen GFS-panel artifacts are
  **untouched evidence**; no labels are reused from Central Park / Midway
  chains.

## 3. Work

1. Station metadata: fetch `api.weather.gov/stations/{KLGA,KORD,KMIA}` —
   official identifier, name, coordinates, elevation. sha256-pin each raw
   response.
2. Deterministic GFS 0.25° cell computation from station coordinates
   (floor to grid); cell corners recorded; no model file download needed at
   PREP stage (cell identity only), GFS retrieval rights quoted.
3. Timezone/observation-day: derive per city from pin `game_start_time`
   evidence + IANA zone; state the local-midnight observation window law.
4. Label source: primary candidate `api.weather.gov` hourly observations for
   the exact station ID; secondary IEM ASOS. **Equivalence of either to the
   PM resolution table (weather.gov/wrh/timeseries hourly "Temp" column) is
   UNVERIFIED** — the wrh timeseries endpoint cannot be compared here
   without touching settlement data, which this cycle forbids. Therefore
   each station's chain is complete only up to link 5 = label source
   (candidate, equivalence-unproven).
5. Pipeline / PIT / missingness / QC design written as spec (no execution
   against outcomes; no fits; no VAL/TEST openings; no metrics/EV/PnL).

## 4. Verdict law

- Any chain with an evidenced missing link → `NOT_RUN_STATION_MAPPING` for
  that station. Given step 4's designed UNVERIFIED label-equivalence link,
  the expected honest overall verdict is **NOT_RUN_STATION_MAPPING** with
  links 1–4 PASS per station and link 5 explicitly OPEN (what evidence would
  close it is stated in the closeout).
- Distinguish throughout: "model/data ready" ≠ "matchable price" ≠
  "profitable". This cycle can at most reach the first.

## 5. Hard fences + stopping rule

- Never: push, merge to main, history rewrite, S1 access, credentials in
  git/log/chat, purchases, signups/credentials, venue (exchange) API calls,
  `git add -A`, writes to ZCode internal DBs.
- No modification of WEATHER-TEMP-PROB-V1 or PM-PAPER-CAPTURE-PREP-V1
  artifacts except read-only citation; no registry writes other than this
  cycle's own registration and phase updates.
- Stop at PREP closeout with exactly ONE executable next-step proposal and
  the PASS/HOLD/NOT_RUN report.
- Independent verifier re-measures: rights quotes vs fetched bytes, station
  coordinates vs response bodies, GFS cell arithmetic, timezone derivation
  vs pin bytes, fence scan (no venue URLs in outputs), verdict honesty.
