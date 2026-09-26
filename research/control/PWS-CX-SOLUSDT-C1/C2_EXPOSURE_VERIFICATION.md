# Phase C2 — Exposure verification — SOLUSDT × plane × window (sha-pinned)

- Cycle: `PWS-CX-SOLUSDT-C1` · Lane: PIT/DATA AUDITOR COMPLETION
  (`c1c2-data-pit-recovery`) · Date: 2026-09-26.
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-solusdt-c1/integration`,
  branch `orca/pws-cx-solusdt-c1-integration`, dispatch/start HEAD
  `5aadae7a515962feb85f523e73410d30ae907296`.
- Evidence sources: **registry-level only** — `plans/CYCLE_REGISTRY.json`,
  `research/wayfinder/MAP.md`, `research/wayfinder/FAMILY_FAILURES.jsonl`, and the
  per-pair authority derived from them,
  `research/control/SRLV-PROGRAM-V1/OUTCOME_EXPOSURE_MAP.md` (§2 crypto table,
  authored from registry+wayfinder). **No scored outcome / PnL file was opened**
  (none exists for this cycle; none was consulted for any cycle).

## 1. Classification table (SOLUSDT)

| Plane / source | Window (this corpus) | Classification | Scope of prior exposure (registry-level) | Permitted role |
|---|---|---|---|---|
| Vision um klines **1h** | 2020-09-14T07:00Z .. 2026-08-31T23:00Z (52,145 bars) | **OUTCOME_EXPOSED_baseline** | xsect baselines only (V11/V14-era cross-sectional families + funding-carry); **no dedicated SOL directional search ever scored** (EXPOSURE_MAP §2 row; MAP.md V14 `V14_REJECT_ALL`, CRYPTO-NG4 SOL-RV24 panel re-pin) | dev for new identity with ancestry disclosure; fixture; never new-evidence/OOS |
| Vision klines **15m / 1m** (not staged) | 2020..2026-08 | **ANCESTRY_EXPOSED_RECLK** | same price history already outcome-exposed at 1h; re-clock veto Q-3 — changing plane creates no outcome-free surface | `ANCESTRY_EXPOSED_DEV` (kill/engineering only); never OOS |
| Funding series (fapi, merged H1+H2) | 2020-09-13T16:00Z .. 2026-08-21T16:00Z (6,580 settlements) | **Cost-authority measured observable** (also baseline-exposed via funding-carry ancestor scope) | staged/scored surfaces of ancestor crypto cycles used funding as carry/panel input (CHR3F staging campaign is the direct source of this corpus) | cost book mandatory input; per-settlement path accounting |
| bookTicker spread census | archive exists 2023-05..2024-04 only; 6 months sampled (see C1 report) | **Cost authority — current evidence class** | newly measured this cycle (prior cycles: coverage unverified ⇒ BLOCKED per EXPOSURE_MAP) | conditional per-hour fill-cost input; any freeze must disclose the sampling |
| liquidationSnapshot / OI history / L2 order book | 404 / ~41.6h lookback / not multi-year | **BLOCKED_UNCONSTRUCTIBLE / BLOCKED** | — | not usable as observables; proxies need falsifiers |

## 2. Registry rows verified

- `plans/CYCLE_REGISTRY.json` (73 cycles) contains **no per-symbol scope fields**;
  the per-pair exposure authority is OUTCOME_EXPOSURE_MAP §2 (registry-derived).
  Registry-level cross-checks performed:
  - `PWS-CX-SOLUSDT-C1` (this cycle): ACTIVE_LIGHT, GO-1 execution, budget 0/18,
    `s1: SEALED_UNTOUCHED`, go phrase REGISTERED_NOT_CONSUMED. The only registry
    row naming SOLUSDT.
  - `CRYPTO-HISTORICAL-REPLICATION-3F-V1`: ACTIVE_LIGHT, BASISLV scored execution
    under **machine-wide heavy lock**. Its CHR3F staging campaign (2026-09-23/24)
    produced the fapi funding scans this corpus merges (sha-pinned in
    `C1_machine_FUNDING_STATS_SOLUSDT.json` → `sources.*.sha256`).
  - `ETHUSDT-OPEN-SEARCH-V2`: ACTIVE_LIGHT, STOP-1 awaiting owner GO, S1 SEALED —
    untouched (see §4).
  - Terminal ancestors per wayfinder: CRYPTO-V14 `V14_REJECT_ALL` (cross-sectional
    families, PREMFADE-28D fold-concentration kill), CRYPTO-NG4
    `CRYPTO_NG4_BLOCKED_DATA_OR_SELECTION` (SOL-RV24 panel re-pinned; 11/11
    crypto-NG proposals dead at rho bar 0.20) — these are the V11/V14-era xsect
    baseline touches that make 1h SOLUSDT `OUTCOME_EXPOSED_baseline`.
- `research/wayfinder/FAMILY_FAILURES.jsonl` (136 rows): **zero rows keyed
  SOLUSDT** — consistent with the map: SOL was touched only inside
  cross-sectional universes/panels, never as a dedicated scored family.

## 3. Conclusion — OOS posture

**There is NO provably outcome-free SOLUSDT history window.** The 1h corpus is
outcome-exposed (baseline scope), 15m/1m are ancestry-exposed by re-clock, the
funding series is a cost authority that is itself baseline-exposed via
funding-carry, and the spread census is new but covers only a 6-month stratum of
an exposed corpus. Therefore, per the frozen plan
(`plans/PLAN_pws_cx_solusdt_c1.md` lines 78-79 and 168):

> OOS = **prospective accumulation after freeze** — D13 / D26 / D52, with D104
> final per umbrella §5.12.

No dev/OOS look at any SOLUSDT history window may be claimed as out-of-sample.
All in-history evaluation is dev with mandatory ancestry disclosure.

## 4. Collision fences honored (evidence)

| Fence | State at audit | Action by this lane |
|---|---|---|
| `ETHUSDT-OPEN-SEARCH-V2` S1/surface | SEALED_UNTOUCHED, STOP-1 pending owner GO | No GO phrase consumed, no surface touched, no corpus re-staged. The prior C1 lane performed one **read-only** byte-identity check (72/72 sha256) of our SOLUSDT klines copy against that worktree's copy — a provenance comparison, not a write; disclosed in `data_local/INVENTORY.md`. |
| `CRYPTO-HISTORICAL-REPLICATION-3F-V1` heavy lock | `researchctl locks inspect` at 2026-09-26 audit time: **`FREE_PROVEN`** (no registry holder, flock free) | No heavy job launched by this lane; all recomputation single-core streaming. |
| Shadow workers (`FX-RANGEFADE-2M-SHADOW-V1`, `PROSPECTIVE-SHADOW-V1`) | untouched | Not inspected beyond registry row, not restarted, not modified. |

## 5. Machine-file sha256 table (verified corpus anchors)

| Artifact | sha256 |
|---|---|
| `C1_machine_KLINE_CENSUS_SOLUSDT.json` | `cf567ff5249732b175590f03de6b0089b186700c4148ddb5e5005c386e76776d` |
| `C1_machine_FUNDING_STATS_SOLUSDT.json` | `688619e4eab5c12d0dff630f16ca8be09c48712403e88e0036b85e049b71dfbe` |
| `C1_machine_SPREAD_CENSUS_SOLUSDT.json` | `a6d0d58c1dfb30d810a10b0e95d5ba67df7a2870f4342a52fa87956ae0bb42ab` |
| `data_local/vision/klines_um_SOLUSDT_1h_MANIFEST.json` | `64286fdffc350f6595d5b19b363ca056d5d2d66d28db8e15abf6a716554d69cb` |
| `data_local/funding/MANIFEST_fapi_merged_SOLUSDT.json` | `698a6275a89bbe834f7b04fb3fafcc343d4735b2d0e5db4bb8731ddd446c7285` |
| `data_local/funding/SOLUSDT_funding.json` (4,385 rows, H1-era merged copy) | `9e850cb4e24cd309a3123fe9b3b3c543aef6f7e510ca36a7e241f5df4d5a1036` |
| `data_local/funding/fapi_scan2026_H1_SOLUSDT.json` | `3dcac8d8f9064a433747fe5da84990f4c91cb5f0af05ccb602572368d87332c0` |
| `data_local/funding/fapi_scan2026a_H2_SOLUSDT.json` | `3c5366492cce9e59110019c8b11309d8df4b30c8436796be15d0687383c1cb1c` |
| `licenses/Binance_Vision-Terms_of_Use.pdf` | `94d6f61a39b5f821ef1d38f968aea1f2aa136e374f2061a2131db9a6af96bc3b` |
| `data_local/INVENTORY.md` (sha256 of all 84 data files incl. untracked zips) | see file; the 72 klines zips and 6 bookTicker zips remain **untracked** (12 GB > 50 MB ceiling) |

Phase C2 verdict: **CONFIRMED** — classification matches the expected map exactly;
no outcome-free window exists; OOS is prospective-only (D13/D26/D52, D104 final).
