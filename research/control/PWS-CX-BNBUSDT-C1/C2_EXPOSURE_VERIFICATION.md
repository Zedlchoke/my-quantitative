# Phase C2 — Exposure verification — BNBUSDT × plane × window (sha-pinned)

- Cycle: `PWS-CX-BNBUSDT-C1` · Lane: PIT/DATA AUDITOR (`c1c2-data-pit`) ·
  Date: 2026-09-26.
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-bnbusdt-c1/integration`,
  branch `orca/pws-cx-bnbusdt-c1-integration`, start HEAD
  `363cf282d6f3b08b9c8d2f449debdb0e056cf49b`.
- Evidence sources: **registry-level only** — `plans/CYCLE_REGISTRY.json`
  (75 cycles, updated 2026-09-26T14:12:44Z), `research/wayfinder/MAP.md`,
  `research/wayfinder/HYPOTHESIS_LEDGER.md`,
  `research/wayfinder/FAMILY_FAILURES.jsonl`, per-pair authority
  `research/control/SRLV-PROGRAM-V1/OUTCOME_EXPOSURE_MAP.md` (§2 crypto table,
  registry-derived), and the plans named below. **No scored outcome / PnL file
  was opened for any cycle.** The `ETHUSDT-OPEN-SEARCH-V2` worktree was NOT
  touched; its facts are taken from its registry row + plan text only.

## 1. Classification table (BNBUSDT)

| Plane / source | Window (this corpus) | Classification | Scope of prior exposure (registry-level) | Permitted role |
|---|---|---|---|---|
| Vision um klines **1h** | 2020-02-10T08:00Z .. 2026-08-31T23:00Z (57,472 bars) | **ELIGIBLE_DEV_BASELINE_EXPOSED** (`OUTCOME_EXPOSED_baseline`) | xsect baselines only (V11/V14-era cross-sectional crypto families incl. BNB in universe + funding-carry/panel inputs); **no dedicated BNB directional search ever scored** (EXPOSURE_MAP §2 line 71: `OUTCOME_EXPOSED_baseline` "như SOL") | dev for new identity, every dev row labelled `ANCESTRY_EXPOSED_DEV`; fixture; never new-evidence/OOS |
| Vision klines **15m / 1m** (not staged) | 2020..2026-08 | **ANCESTRY_EXPOSED_RECLK** | same price history already outcome-exposed at 1h; re-clock veto Q-3 — changing plane creates no outcome-free surface (EXPOSURE_MAP §2 row "(4 cặp) Vision klines 15m/1m") | `ANCESTRY_EXPOSED_DEV` (kill/engineering only); never OOS |
| Funding series (fapi, this cycle's scan) | 2020-02-10T08:00Z .. 2026-09-26T08:00Z (7,261 settlements) | **Cost-authority measured observable** (baseline-exposed via funding-carry ancestor scope) | ancestor crypto cycles consumed funding as carry/panel input; BNB funding itself never a scored family (zero FAMILY_FAILURES rows keyed BNBUSDT) | cost book mandatory input; per-settlement path accounting |
| bookTicker spread census | **NOT_RUN_DISK_CONSTRAINT** (7 GB free < 25 GB required) | — | newly-attempted observable, not run | any cost gate consuming spread stays fail-closed (BLOCKED for scoring) |
| liquidationSnapshot / OI history / L2 order book | 404 / ~41.6h lookback / not multi-year | **BLOCKED_UNCONSTRUCTIBLE / BLOCKED** (EXPOSURE_MAP §2) | — | not usable as observables; proxies need falsifiers |

## 2. Registry rows verified (bytes read this lane)

- `plans/CYCLE_REGISTRY.json` has **no per-symbol scope fields**; per-pair
  exposure authority is OUTCOME_EXPOSURE_MAP §2. Registry-level cross-checks:
  - `PWS-CX-BNBUSDT-C1` (this cycle): ACTIVE_LIGHT, GO-1 execution, budget
    **0/18**, `s1: SEALED_UNTOUCHED`, GO-2 phrase REGISTERED_NOT_CONSUMED.
    First registry row to carry a BNB-scoped cycle.
  - **`ETHUSDT-OPEN-SEARCH-V2`** (ACTIVE_LIGHT, STOP-1 awaiting owner GO,
    budget 0/8): registry phase field states "7-series corpus BUILD_PASS
    (V1 cross-check 80/80 byte-identical x3 shared; alt floors ADA
    2020-01-31/**BNB 2020-02-10**/XRP 2020-01-06/SOL 2020-09-14) … budget 0/8;
    S1 SEALED; **zero scored PnL**". Its plan
    (`plans/PLAN_ethusdt_open_search_v2.md` lines 21/60/75/95-96) confirms the
    staged corpus includes `klines:BNBUSDT:1h` and that the staged lane-B
    alt-breadth arms consume BNB only inside a 4-asset breadth count
    (`breadth_200(SOL,BNB,XRP,ADA) >= 3/4`). **Read-only knowledge recorded
    here; that worktree was not opened, not re-staged, not touched.** Its BNB
    staging is corpus-build exposure, not scored outcome exposure (0/8).
  - `CRYPTO-HISTORICAL-REPLICATION-3F-V1` (ACTIVE_LIGHT, heavy lock): 8
    BASISLV cells = 4 folds × (28D anchor, 28D-INV) on BTC (per EXPOSURE_MAP
    §2: "CHR3F staged + scored" is the BTC 15m row). No BNB scored cell.
  - `ETHUSDT-OPEN-SEARCH-V1` (TERMINAL): ETH-only scored search (8 cells,
    G3 wall); family kills EOS1-E1/E2 are ETH-keyed. No BNB.
  - `SRLV-CX-C1` (TERMINAL REJECT_ALL): universe BTC/ETH/SOL/BNB
    (`plans/PLAN_srlv_cx_cohort_1.md` line 26), 6/18 observed, 0 OOS looks.
    Its plan line 61 already records "SOL/BNB 1h" as baseline-exposed. This is
    part of the baseline-exposure class, consistent with the map.
  - CRYPTO V14 (TERMINAL `V14_REJECT_ALL`, wayfinder MAP.md 2026-09-05:
    cross-sectional crypto families, PREMFADE-28D fold-concentration kill,
    crypto 143/146 cells) — the V11/V14-era cross-sectional touch that makes
    1h BNBUSDT `OUTCOME_EXPOSED_baseline` (same-by-law as the SOLUSDT row of
    OUTCOME_EXPOSURE_MAP §2 line 70).
- `research/wayfinder/FAMILY_FAILURES.jsonl` (137 rows): **zero rows keyed
  BNBUSDT**.
- `research/wayfinder/HYPOTHESIS_LEDGER.md` (273 lines): **zero BNB mentions**.

## 3. Exposure finding

**No scored/searched BNBUSDT price-history outcome exists anywhere in the
registry, wayfinder ledgers, or the exposure map beyond the baseline class.**
The precise inventory of prior BNB price-history exposure:

1. Cross-sectional universes that included BNB among N assets (V11/V14-era
   crypto families; SRLV-CX-C1 6 observed cells in a 4-pair universe) —
   baseline-exposure class per the map.
2. Funding-carry / panel inputs consumed BNB funding as a cost/carry
   observable, never as a scored family.
3. `ETHUSDT-OPEN-SEARCH-V2` staged (build-verified, 0 scored cells) a corpus
   containing BNB 1h — corpus staging + breadth-count definition only.

**Classification CONFIRMED: `ELIGIBLE_DEV_BASELINE_EXPOSED`; every dev row of
this cycle carries `ANCESTRY_EXPOSED_DEV`.** There is NO provably outcome-free
BNBUSDT history window: 1h is outcome-exposed (baseline scope), 15m/1m are
ancestry-exposed by re-clock, funding is a cost authority baseline-exposed via
funding-carry, and the spread census did not run. Per the frozen child plan
(`plans/PLAN_pws_cx_bnbusdt_c1.md` §2.2): OOS = prospective accumulation after
freeze; maximal in-history conclusion =
`CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`.

## 4. Dev folds (pinned pre-outcome)

Pinned now, before any council proposal or scored cell, per child plan §C2;
power may narrow usage but the windows are frozen:

| Fold | Window | Corpus anchor |
|---|---|---|
| F1 | 2020-02-10 → 2021-12-31 | 16,576 bars measured in window (partial first month: 472 bars from 2020-02-10T08:00Z + 7,344 bars 2020-03..12 + 8,760 bars 2021) |
| F2 | 2022-01-01 → 2023-06-30 | full months, 0 gaps |
| F3 | 2023-07-01 → 2024-12-31 | full months, 0 gaps |
| F4 | 2025-01-01 → 2026-08-31 | full months, ends at corpus end |

(Bar counts F2-F4 recomputable from `C1_machine_KLINE_CENSUS_BNBUSDT.json`
`monthly_bars`; F1 = 472 + sum(2020-03..2020-12) + sum(2021).)

## 5. Collision fences honored (evidence)

| Fence | State at audit | Action by this lane |
|---|---|---|
| `ETHUSDT-OPEN-SEARCH-V2` S1/surface | SEALED_UNTOUCHED, STOP-1 pending owner GO | Registry row + plan text read only; no worktree path accessed; no corpus re-staged; no GO phrase consumed |
| `CRYPTO-HISTORICAL-REPLICATION-3F-V1` heavy lock | not dispatched by this lane | No heavy job launched; census compute is single-core streaming of 2.7 MB of zips + one funding JSON |
| SOLUSDT terminal worktree (append-only evidence) | read-only precedent reads | C1 report structure mirrored from its committed report; its `data_local/` bytes not copied into this cycle |
| Shadow workers | untouched | Not inspected beyond registry rows |

## 6. Machine-file sha256 table (this cycle)

| Artifact | sha256 |
|---|---|
| `C1_machine_KLINE_CENSUS_BNBUSDT.json` | see §6 of `C1_data_gate_REPORT.md` (pinned after final write) |
| `C1_machine_FUNDING_STATS_BNBUSDT.json` | see §6 of `C1_data_gate_REPORT.md` |
| `data_local/vision/klines_um_BNBUSDT_1h_MANIFEST.json` | pinned in `data_local/INVENTORY.md` build |
| `data_local/funding/fapi_scan_BNBUSDT_2026-09-26.json` | `464da8832d53bf0454f286d8ef3566a357a69d93336de5aa5d2835876c0dc893` |
| licenses | Binance Vision ToU pdf **cited, not copied**: sha `94d6f61a39b5f821ef1d38f968aea1f2aa136e374f2061a2131db9a6af96bc3b` at the SOLUSDT child path (same keyless endpoints) |

Phase C2 verdict: **CONFIRMED** — expected classification
`ELIGIBLE_DEV_BASELINE_EXPOSED` + `ANCESTRY_EXPOSED_DEV` labels matches the
measured registry/ledger state exactly; no outcome-free window; OOS is
prospective-only; dev folds F1-F4 pinned above.
