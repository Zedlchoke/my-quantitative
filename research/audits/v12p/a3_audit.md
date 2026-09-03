# V12P A3 — PIT data inventory, ILLIQ replication window authority, equal-twin staging manifests

Worktree: `orca/v12p-a3-data` @ `8bfbae5073d0d2079a18863d060084cc929ba7a4` (verified clean).
Producer: A3. No network fetches. No raw data committed.

## 1. Required symbol set — declared BEFORE coverage was computed

The 20 required symbols are the union of (a) the ILLIQ family universe — "20 staged
binance_bar symbols; PIT eligibility by listing + DV filter"
(`research/control/v11_run/selection_freeze_specs/A8-V11-ILLIQ-AMIHUD.json`, V11 selection
freeze) with BTCUSDT as the frozen benchmark leg — and (b) the OILEV-V2 / blind S0 snapshot
universe — the 20 consolidated OI symbols
(`research/control/v11_run/oi_staging_manifest.json`). Both universes are the same 20 names:

1000PEPEUSDT, AAVEUSDT, ACEUSDT, ADAUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BOMEUSDT, BTCUSDT,
DOGEUSDT, ENAUSDT, ETHUSDT, LINKUSDT, NEARUSDT, ONGUSDT, SOLUSDT, SUIUSDT, WLDUSDT,
XRPUSDT, ZECUSDT.

## 2. Declared coverage requirements (ILLIQ replication, S0R window)

Window W = `2024-08-22T00:00:00Z .. 2025-08-21T00:00:00Z` (half-open vs V11 scored window
`2025-08-22T00:00:00Z .. 2026-08-21T00:00:00Z`; non-overlap verified programmatically —
S0R ends a full day before the scored window opens).

- **bars** — every 15-minute slot in W has exactly one completed bar (`ts_event <= t`
  completion rule, same as the V11 loader); no internal gaps; no synthesized tail; plus
  warmup: 28d anchor formation, 56d neighbour formation, 90d BTC beta hedge, all from
  pre-window completed bars only. Binding requirement at the first decision stamp
  (first Monday strictly after W start = `2024-08-26T00:00Z`): 90 days = 8640 completed
  15m slots before the stamp (anchor floor 2688, neighbour floor 5376).
- **funding** — native settlements over W at the symbol's own cadence; PIT rule: a
  settlement applies to a holding span only when its ts lies in `[ts_opened, ts_closed]`.
- **instrument metadata** — tick size (price_increment), precisions, fees present and sane.
- OI is **not** a required field for the ILLIQ identity (bars + funding only); it is
  required for OILEV-V2 / blind in the S0 snapshot window only.

## 3. ILLIQ replication window verdict: `V12_ILLIQ_REPLICATION_BLOCKED_DATA`

The preferred preregistered S0R window is **NOT frozen**; its three slots stay unused.
No substitute window was applied (forbidden by PLAN §7 A3). Non-overlap with the V11
scored window was verified first and holds; the failure is purely data coverage.

Exact missing list (full detail in `a3_illiq_window_verdict.json` / `a3_inventory_raw.json`):

1. **bars_window_coverage** — completed-bar coverage does not start at the window head:
   - 13 symbols (1000PEPE, AAVE, ACE, AVAX, BCH, BOME, BTC, ENA, NEAR, ONG, SUI, WLD,
     ZEC): first local bar `2024-08-23T05:15:00Z` → **116 missing slots** each
     (`2024-08-22T00:15Z .. 2024-08-23T05:00Z`, 29h).
   - ETHUSDT: first local bar `2024-08-23T00:15:00Z` → **96 missing slots** (24h head).
     (ETH also has 3 internal gap runs elsewhere in its history — 57 + 4 + 2 slots — all
     outside both the S0R and S0 windows.)
   - 6 symbols (ADA, BNB, DOGE, LINK, SOL, XRP) fully cover W in-window (0 missing).
   - The benchmark leg BTCUSDT itself fails at the window head.
2. **bars_warmup** — all 20 symbols fail. Pre-window (close <= `2024-08-22T00:00Z`) local
   history is 40 bars (10h) for 6 symbols and zero for the other 14, vs 2688 / 5376 / 8640
   completed slots required for anchor / neighbour / beta at the first stamp. The earliest
   locally-servable 28d stamp is `2024-09-23T00:00Z`, so the first four weekly stamps
   cannot form the anchor book and the window head cannot be formed at all.
3. **funding_head** — 13 symbols have no local settlements before `2024-08-23T08:00:00Z`
   (first 32h of W unfunded-in-data). The 7 symbols covered by the
   `funding_data/20240820_20260821` bundle are complete from `2024-08-22T08:00Z` with
   zero coverage holes. Funding alone would not have blocked (holding spans begin after
   the first stamp + 1-day execution lag), but bars/warmup already block decisively.

Funding internal coverage inside W is otherwise clean: zero coverage holes for every
homogeneous-cadence symbol (max internal gap = native 8h cadence); ACE/ONG carry genuine
1h/4h/8h cadence mixes (recorded as cadence clusters, not data loss).

## 4. OILEV-V2 / blind family S0 snapshot — VERIFIED, authorized

Window `2025-08-22T00:00:00Z .. 2026-08-21T00:00:00Z`, per PLAN §7 A3 deliverable 4
(authorized only because no OILEV PnL was computed and the blind proposal does not exist).

- bars: 20/20 symbols at **34944/34944 completed slots, 0 missing**.
- funding: 20/20 symbols with head/tail slack <= 8h and no internal spacing > 8h; the
  last in-window settlement lands exactly at the window end
  (`2026-08-21T00:00:00Z`) after hour-grid jitter snapping.
- OI: **20/20 parquet sha256 match** `oi_data/staging_report.json`
  (== `research/control/v11_run/oi_staging_manifest.json`, hashes agree 20/20); 417/417
  days present per symbol (`2025-07-01 .. 2026-08-21`), 0 internal gap days.
- instrument metadata present for all 20 (tick sizes 1e-7 .. 1e-2, taker 5e-4).

Evidence: `a3_s0_snapshot_authorization.json`.

## 5. Equal-twin staging manifest

`research/v12/data_contract.py::emit_file_manifest` generates deterministic per-file
sha256 manifests (`v12_staged_manifest_v1`) over the staged roots; `manifest_sha256`
hashes only the canonical sorted `files` section, so identical bytes on two hosts produce
identical manifests, and `verify_against_manifest` re-hashes to prove an equal twin.

Committed artifact: `a3_staging_manifest.json` — **90 files**
(20 bar parquets, 20 metadata parquets, 27 funding JSONs, 20 OI parquets + label paths),
`manifest_sha256 = 76c0c4eb3e4a0ee8820b2a6698302f7ce396e6a634d215391450548a2ba1ee23`.
Hashes only; the raw data stays in the gitignored workspace roots.

## 6. Loader conventions discovered (recorded in data_manifest.json)

- Bar `ts_event` = close boundary **minus ~1ms** (Binance close-time convention, with a
  sub-ms artifact); consecutive closes differ by exactly 900s. Inventory snaps closes
  forward to the UTC slot boundary (`snap_bar_closes_to_slots`); the loader completion
  rule (`ts_event <= t`) is unchanged.
- `fundingTime` carries a few-ms jitter around exact hour boundaries
  (`snap_funding_times_to_hour`); without snapping, boundary settlements are silently
  dropped by exact-equality PIT checks.
- Some symbols settle funding at 4h (and briefly 1h) cadences — funding inventory reports
  cadence clusters instead of assuming 8h.

## 7. Code, tests

- `research/v12/data_contract.py` — frozen windows, required set, declared requirements,
  PIT inventory (bars/funding/OI/metadata), warmup satisfiability, staging manifest
  generator.
- `research/v12/load_validation.py` — fail-closed `DataLoadError` validators: window
  bounds, completed-bar integrity (gaps, duplicates, partial tail, late bars), funding
  PIT applicability + span coverage, manifest-hash match, window non-overlap.
- `tests/test_v12p_a3_data.py` — 28 tests, tiny synthetic fixtures in `tmp_path`; the
  real data stores are never touched by tests.

## 8. Assumptions

- ACE/ONG/BOME/ENA mixed funding cadences are genuine exchange phase changes; the single
  >8h spacing inside the 4h phases of BOME/ENA cannot be separated from a lost settlement
  without the exchange funding-info history, which is not locally available and must not
  be fetched per A3 rules.
- The 7-symbol `20240820_20260821` funding bundle is treated as an alternate PIT source
  for those symbols only; bundles are never mixed within a span (de-dup by snapped ts).
- OI is not required for ILLIQ; the ILLIQ blockers above do not touch the OILEV/blind
  S0 snapshot, which is complete.
