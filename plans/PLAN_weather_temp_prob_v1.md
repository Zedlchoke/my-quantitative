# PLAN — WEATHER-TEMP-PROB-V1 / Phase M-1 (APPROVED, owner GO 2026-10-15)

> **OWNER GO M-1 recorded 2026-10-15** (verbatim, excerpt): "OWNER GO M-1 —
> WEATHER-TEMP-PROB-V1. Tôi duyệt plan M-1, MODEL_SPEC v1.1 và amendments
> v3.2/v3.3 cho phạm vi: xây panel nhãn CLI/ACIS + dự báo GFS-NODD, kiểm tra
> PIT/QC và đóng băng artifact. Ngân sách $0, scored budget 0/0. Lệnh này
> KHÔNG cho phép fit/đánh giá model trên dữ liệu thật."
> Scope fences in force: no S1, no exchange data (Kalshi/Polymarket/Open-
> Meteo), no standing collector, no purchases, no orders, no push/merge;
> fitting/evaluation on real data = M-2 behind its own gate + owner GO.

Incorporates MODEL_SPEC v1.1 (§8 phase
split), AMENDMENTS v3.2 (two views + DOCUMENTED_GUARD) and v3.3 (GFS-NODD
source), and the D3 adjudication (SOURCES LAYER 0).

## 1. Identity

| field | value |
|---|---|
| cycle_id | `WEATHER-TEMP-PROB-V1` |
| asset | `weather-prediction-markets` |
| phase | **M-1 — label + GFS panel harvest/QC ONLY (0 scored, $0)** |
| budget | 0/0 (no scored cells in M-1; M-2 scored = separate gate + owner GO) |
| worktree / branch | `.worktrees/weather-temp-prob-v1/integration` / `orca/weather-temp-prob-v1-integration` (controller-created) |

## 2. M-1 scope (MODEL_SPEC v1.1 §8)

IN: (a) NWS CLI labels for CLINYC/CLIMDW/CLIMIA via IEM AFOS — post-day-end
CLIMATE REPORT per the CLI version law (§1); (b) ACIS TMAX cross-checks
(MDW/NYC/MIA sids); (c) GFS-NODD 00Z D-1 panel per the B1.1 valid_time
matrix incl. DST days (byte-range reads only, per-run measured
Last-Modified availability); (d) PIT/QC battery + exclusion ledgers; (e)
sha256 freeze manifests per run; (f) independent verifier run.
OUT (not in M-1): model fitting on real data (M-2 = SCORED evaluation of the
model on real data — own gate + owner GO), any exchange-data harvest
(Kalshi/Polymarket — gated by the exchange-data D3 adjudication), platform
mapping/economics (M-3), S1, standing collectors, orders, purchases,
push/merge.

## 3. Data sources & rights (D3 status, frozen)

| source | use in M-1 | rights status | evidence |
|---|---|---|---|
| NOAA GFS 0.25° via NODD S3 | forecast panel (primary) | **GRANTED_WITH_EVIDENCE** — US Gov public domain (17 USC §105; NODD policy byte-read at harvest formality) | probes `d3_v4` + `station_chain_v5` |
| Kalshi market data | **NOT TOUCHED in M-1** | HOLD_PENDING_ENTITLEMENT (API Developer Agreement + ToS identified; byte-read blocked by 429) | probe evidence saved |
| Open-Meteo | **NOT TOUCHED (HOLD)** | CANDIDATE_NOT_AUTHORIZED — free-tier terms classify undisclosed research at commercial entities as commercial | terms quoted in SOURCES LAYER 0 |
| IEM AFOS (CLI/ZFP) | labels + cross-check | GRANTED_WITH_EVIDENCE — public domain + attribution | disclaimer quoted |
| ACIS | cross-check | GRANTED_WITH_EVIDENCE — NOAA RCC public domain + attribution | StnMeta probes |
| ECMWF Open Data | n/a | UNAVAILABLE_FAIL_CLOSED (no historical retention without an account) | probe saved |

## 4. Station mapping (chain audited 2026-10-15, fail-closed)

| series | CLI token | CLI product (IEM, probe) | ACIS sid / GHCN | coords (ACIS) | GFS 0.25° cells (lat × lon) |
|---|---|---|---|---|---|
| KXHIGHNY | CLINYC | NWS NYC "CLIMATE REPORT" | NYC / USW00094728 | 40.77898, −73.96925 | [40.75,41.00] × [−74.00,−73.75] |
| KXHIGHCHI | CLIMDW | NWS MDW "MIDWAY CLIMATE SUMMARY" (NOT O'Hare) | MDW / USW00014819 | 41.78412, −87.75514 | [41.75,42.00] × [−88.00,−87.75] |
| KXHIGHMIA | CLIMIA | NWS MIA "MIAMI CLIMATE SUMMARY" | MIA / USW00012839 | 25.78805, −80.31694 | [25.75,26.00] × [−80.50,−80.25] |

Evidence: `sources/probe_evidence/station_chain_v5/` (ACIS StnMeta ×3 + IEM
CLI pages + retrieval log + SHA256SUMS). Any chain link mismatch at harvest ⇒
fail-closed for that station (`NOT_RUN_STATION_CHAIN`).

## 5. Deliverables (M-1 exit criteria)

1. Label ledger per station-day: post-day-end CLI value + issue timestamp +
   ACIS cross-check ±2°F flag (`NOT_RUN_LABEL` when absent).
2. GFS panel per station-day: needed file set (B1.1 matrix incl. DST days),
   per-file HTTP status + Last-Modified, per-day `AVAIL(day)` and PIT gate
   verdicts (`NOT_RUN_PIT` / `NOT_RUN_AVAILABILITY`).
3. Censuses IN M-1: label far-end per series; GFS version census; measured
   availability distribution (S3 Last-Modified). Censuses NOT in M-1
   (exchange-data phases): Kalshi candle-gap census, trade-tape depth, fee
   bytes.
4. Freeze manifests (per-run sha256) + independent verifier report.
5. M-1 closeout report READY_FOR_OWNER (feeds the M-2 gate).

## 6. Stop conditions & NOT_RUN codes

Halt + owner packet on: any D3 fence hit (Open-Meteo calls, exchange data),
any license ambiguity, `QC_STATION_TOKEN`/chain mismatch, freeze-manifest
drift, or any need for credentials/purchases. Codes: `NOT_RUN_LABEL`,
`NOT_RUN_PIT`, `NOT_RUN_AVAILABILITY`, `NOT_RUN_STATION_CHAIN`,
`NOT_RUN_RESOURCE_CONFLICT` (lock held), `HOLD_CONTROL_STATE_DRIFT`
(plans/ dirty).

## 7. Preconditions for controller registration (B→A, current)

plans/ clean ✓ (measured) · heavy lock FREE at execution time (last measured
HELD by the SRML-DEV lane — re-measure immediately before; held ⇒
NOT_RUN_RESOURCE_CONFLICT) · owner approves THIS plan + MODEL_SPEC v1.1 +
AMENDMENTS v3.2/v3.3 (D4/D5/D8 per DECISION_REVIEW) · deploy commands per
DEPLOY_COMMANDS_DRAFT (safe-teardown law included).
