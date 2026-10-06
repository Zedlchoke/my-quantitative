# D6-IBKRREFETCH — IBKR conditional re-fetch lane report

Cycle: FUTURES-DATACONTRACT-QUAL-V1 | Lane: D6-IBKRREFETCH | Date: 2026-10-03
Verdict: **PASS** (canary passed; minimal serial re-fetch completed, staging-only)

## 0. Boundary compliance (Co-Owner update received mid-run, BEFORE any fetch writes)

- The boundary update ("staging-only output; never write into `raw/`") arrived after
  inspect/canary-script authoring but **before the canary request and before any data
  write**. Nothing was ever written into
  `/Users/hoangminhlong/.my-quantitative-data/futures-10syms-v1/raw/` — verified
  post-run: `find raw -newermt "2026-10-03 00:00"` returns zero files.
- The root repo's `raw_manifest.jsonl` (1470 lines, last entry 2026-10-02T04:11:54Z,
  NGV26 bulk) was **not appended** — read-only.
- All fetched payloads were written only to:
  `/Users/hoangminhlong/.my-quantitative-data/futures-10syms-v1/staging_refetch_20261003/`
  (6 new files, created 2026-10-03 14:55–14:56 local / 07:55–07:56 UTC).
- No overwrites or deletions anywhere. No credentials involved (TWS API socket has no
  auth headers; log redaction filter from the probe module was active).

## 1. Inspect findings — how fut10_probe.py talks to IBKR

Source (read-only): `/Users/hoangminhlong/my-quantitative/research/control/FUTURES-DATA-10SYMS-V1/fut10_probe.py`

- Transport: **IBKR TWS API socket** at `127.0.0.1:7497` via `ib_insync` 0.9.86
  (venv). NOT an HTTP endpoint; no URLs, no headers, no cookies.
- Auth model: none at the protocol level from the script's side — it relies on a
  locally running, logged-in TWS/IB Gateway holding the session. The script passes
  `readonly=True` + unique `clientId`; it never sends credentials. A local gateway
  was confirmed listening (JavaApplication pid 913, `*:7497 LISTEN`) before the canary.
- Pacing in root script: `PACING_S = 3.0` between historical requests; walk-back probes
  0.4s. Byte cap 2.0 GiB on new raw bytes. Manifest: append-only JSONL per file.
- Stage functions (`stage_sample`, `stage_bulk`) write into `raw/` and append to the
  root manifest — **NOT invoked by D6**. D6 imports the module read-only and reuses
  only the pure request helpers (`connect`, `fut_contract`, `details_row`,
  `hist_request`, `by_conid`, `ErrCollector`, `redact`), which perform no file I/O.
- D6 request profile: serial only, 2.5s sleep between ALL requests, clientIds 9261
  (canary) / 9262 (fetch), readonly, timeout 15s. 25 requests total incl. canary
  (budget ~30). Server version reported by gateway: 176.

## 2. Canary — PASS

One request through the same code path (ES current front per 2026-10-02 baseline:
ESZ6 conId 515416632, CME):

| item | value |
|---|---|
| request | TRADES, 1 day, 3 D, useRTH=True, formatDate=1, keepUpToDate=False |
| connection | ok, serverVersion 176, clientId 9261, readonly |
| result | ok=true, n_rows=3, bars 2026-09-30 .. **2026-10-02** (fresh through last session) |
| errors | none (no 2xxx codes, no exception) |

Artifact: `analysis/d6_ibkr/canary.json` (runner: `canary_run.py`).

## 3. Fetch log (24 requests, 2026-10-03T07:55:52Z .. 07:57:06Z, budget_exhausted=false)

Per symbol: 1 active-chain `reqContractDetails` + 1 front daily-3D TRADES fetch
(staged) + 2 expired-wall probes just beyond the 2026-10-02 wall. Wall probe targets:
ES/NQ beyond 202509 → 202506, 202503; FX beyond 202512 → 202509, 202506.

### Staged files (all in staging_refetch_20261003/, sha256 manifest: d6_staging_manifest.json)

| file | request params | ok | n_rows | last bar | bytes | sha256 | fetched (UTC) |
|---|---|---|---|---|---|---|---|
| ES_ESZ6_515416632_front-d6-20261003_TRADES_1day_3D.json | conId 515416632 CME, TRADES 1day 3D | true | 3 | 2026-10-02 | 698 | 7a6f4537bd79ab9ed81c85d4b06047747023012e8532e8a4fda50ac5a39a19be | 07:55:57Z |
| NQ_NQZ6_563947726_front-d6-20261003_TRADES_1day_3D.json | conId 563947726 CME, TRADES 1day 3D | true | 3 | 2026-10-02 | 705 | f70b63d496447b949af9d3b71c2708db850c0b1e756281a9b91958ceae391143 | 07:56:09Z |
| 6E_6EV6_881167137_front-d6-20261003_TRADES_1day_3D.json | conId 881167137 CME, TRADES 1day 3D | true | 3 | 2026-10-02 | 675 | 894832c92c1688dc9d47aede7d8aef070ceebed99bfebbd605d47403c6910158 | 07:56:21Z |
| 6B_6BV6_881167030_front-d6-20261003_TRADES_1day_3D.json | conId 881167030 CME, TRADES 1day 3D | true | 3 | 2026-10-02 | 661 | 328ac00bfc9da5beb81dbdc1440a1739e4cd47ed48a8502631ba2807038e612a | 07:56:33Z |
| 6A_6AV6_881166970_front-d6-20261003_TRADES_1day_3D.json | conId 881166970 CME, TRADES 1day 3D | true | 3 | 2026-10-02 | 664 | bb927f1666535ebcf7afe1dbcdd5769b16b9717060eedf5818b5012ef5a0caf0 | 07:56:46Z |
| 6J_6JV6_881167175_front-d6-20261003_TRADES_1day_3D.json | conId 881167175 CME, TRADES 1day 3D | true | 3 | 2026-10-02 | 694 | db3d5c4a25fa4f205d89b608656c6670c1a0574a88547391cd4e90307abff1c1 | 07:56:58Z |

Payload schema mirrors the root S4 sample payload (fetched_utc, conId, localSymbol,
role, expiry_month, exchange, whatUse, barSize, durationStr, endDateTime, useRTH,
endpoint, ok, errors, n_rows, bars). Naming follows the S4 role-tag convention
(`{sym}_{localSymbol}_{conId}_{role}_{whatUse}_{bs}_{dur}.json`) with role
`front-d6-20261003` — distinct names, zero collision with existing raw files.

## 4. Findings

1. **Fronts unchanged** since 2026-10-02 baseline: ESZ6 / NQZ6 (2026-12-18),
   6EV6 / 6BV6 / 6AV6 / 6JV6 (2026-10-19). No roll between sessions.
2. **Newly listable: 0** for all 6 symbols — active-chain conId sets are identical to
   the 2026-10-02 S1_IDENTITY sets (ES 21, NQ 12, FX 36 each); nothing dropped either.
3. **Expired wall did NOT recede in 1 day**: all boundary probes returned TWS error
   200 "No security definition has been found" — ES/NQ at 202506 and 202503, FX at
   202509 and 202506. Walls therefore remain at ES/NQ=202509, FX=202512. This is
   negative evidence for the "recedes weekly" hypothesis at a 1-day horizon; the
   wall cross-section is unchanged and the existing raw coverage of the resolvable
   expired space remains complete.
4. **Just-expired (202609) contracts need no re-fetch**: ESU6/NQU6/6EU6/6BU6/6AU6/6JU6
   each already have 10 files in raw/ from the 2026-10-02 bulk (verified read-only).
5. Data availability is current: every staged front file ends at bar 2026-10-02, the
   last completed trading session before this fetch.

## 5. Write accounting (this lane)

- `research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d6_ibkr/canary_run.py`,
  `canary.json`, `d6_fetch_run.py`, `d6_fetch_log.json`, `d6_staging_manifest.json`,
  `d6_report.md` (this file) — worktree, allowed area.
- `research/control/FUTURES-DATACONTRACT-QUAL-V1/dispatch/handoff_D6-IBKRREFETCH.json`
  — worktree, allowed area.
- `~/.my-quantitative-data/futures-10syms-v1/staging_refetch_20261003/` — 6 new files
  (staging, per boundary update).
- Nothing else. No commits; no ledger/registry/lock touches; root repo untouched.

## 6. Limitations

- Staged payloads are tiny probes (3 rows each) — they evidence freshness and code-path
  equivalence, not bulk history.
- Wall non-recession at a 1-day horizon does not falsify weekly recession; a re-probe
  after the next weekly boundary would be the discriminating test.
- Active-chain comparison relies on conId sets from the 2026-10-02 S1_IDENTITY.json
  snapshot (read-only); listing lag on IB's side could delay new listings by hours.
