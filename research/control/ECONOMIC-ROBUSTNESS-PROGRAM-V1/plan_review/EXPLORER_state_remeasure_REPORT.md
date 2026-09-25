# EXPLORER — STATE RE-MEASURE REPORT (ECONOMIC-ROBUSTNESS-PROGRAM-V1)

- Role: quant-explorer, READ-ONLY evidence lane. Task `erp1-explorer-remeasure`.
- Measured: 2026-09-25 (~08:45–09:05 local, ≈01:45–02:05 UTC). Root checkout
  `main` @ `7343dde57fe86b38d205b0bec5e8af92a4c4404d` (= dispatch sha; verified
  `git rev-parse HEAD`). Tree clean except 5 pre-existing untracked paths
  (`.zcode/`, `plan_at.md`, `research/control/DASHBOARD-AND-SHADOW-RELIABILITY-V1/`,
  `research/control/SANDBOX-OVERFIT-3ASSETS/`, `research/control/d2_curiosity_v1_sources/`).
- Method: light local python over jsonl/state/heartbeat bytes; `ps aux`; no
  network, no S1, no scored cells, no writes outside the two artifacts of this lane.
- All numbers below re-measured from bytes TODAY unless explicitly labeled
  `[2026-09-24 snapshot]` (quoted from the SHADOW-PAPER-REVIEW-V1 lane reports).

---

## 1. Per-sleeve current state (bytes, cited)

### 1.1 XSECT-FUND-CARRY-7D
File: `.worktrees/prospective-shadow-v1/integration/results/prospective_shadow_v1/ledgers/XSECT-FUND-CARRY-7D.jsonl` (30,161 bytes; mtime 2026-09-25 07:17 local)

- Rows: **11** (schema `shv1_event_v1`).
- First observed_at `2026-09-15T00:15:15Z`; last observed_at `2026-09-25T00:17:35Z`.
  Scheduled decisions 2026-09-15T00:00Z → 2026-09-25T00:00Z, daily, no gap.
- Decisions/fills: 11/11 accounting OK + data OK + risk OK; **0 DATA_BLOCKED,
  0 UNAVAILABLE_FAIL_CLOSED**; **52 virtual fills** total (per-day counts
  4,4,6,6,4,5,5,4,4,6,4). `no_order_proof.emitted_action_types = ["TARGET_INTENT"]` every row.
- Cumulative booked (sum over 11 rows, USDT):
  - `price_pnl` **−354.4501**, `fee` **+286.4265**, `slippage` **+68.0236**,
    `funding_cashflow` **+4.6039**, `total_pnl` **−349.8462**.
  - Daily `total_pnl` series (USDT): −45.83, −2.06, −37.76, −50.33, −52.74,
    −30.63, −24.15, −2.84, +0.35, −52.23, −51.62 → mean −31.80, stdev 21.54 (n=11).
  - Ledger `equity` last = 99,948.3772 (row-local basis; see §2).
- Live mark (valuation heartbeat `.../runtime/valuation_heartbeat.json`,
  `mark_timestamp_utc 2026-09-25T01:55:00Z`): **equity 99,094.9223, status RUNNING**
  (cash 98,833.7952 → unrealized ≈ +261.13 held in marks; mark-level fields
  `fees 286.4265`, `funding 4.6039`, `realized_pnl 0.0`, `net 0.002635`).
- Digests (constant across all 11 rows): `config_digest b13f1a2578921632…`,
  `cost_regime_digest 130d2e7ee97478c0…`, `code_freeze_sha af4df157690ae9b0…`;
  `data_snapshot_digest` unique per day (11 distinct).
- vs `[2026-09-24 snapshot]` (lane_crypto_sleeves REPORT §3): 10 decisions /
  48 fills / Σfee 246.43 / Σslip 56.40 / Σfunding +4.60 / booked net −298.22.
  **Delta today: +1 decision, +4 fills, +40.00 fee, +11.62 slippage, booked net
  −51.62 worse; funding unchanged** (09-25 row had funding 0.00). Mark equity
  basis moved 99,662.87 (12:10Z 09-24) → 99,094.92 (01:55Z 09-25).

### 1.2 ILLIQ-AMIHUD-28D-W
File: same dir, `ILLIQ-AMIHUD-28D-W.jsonl` (3,922 bytes; mtime 2026-09-21 07:17 local — **byte-unchanged since 09-21**)

- Rows: **1**. observed_at `2026-09-21T00:16:22Z`; scheduled decision `2026-09-21T00:00:00Z`.
- 1/1 OK/OK/OK; **8 fills** (long APT/ATOM/ETC/OP ±0.125 vs short BTC/ETH/SOL/XRP).
- Booked: `price_pnl` −63.2139, `fee` +50.00, `slippage` +13.2139,
  `funding_cashflow` 0.0, `total_pnl` −63.2139; ledger equity 99,936.7861.
- Live mark 01:55Z 09-25: **equity 100,348.4675, RUNNING** (cash 99,936.7861 →
  unrealized ≈ +411.68; `fees 50.0`, `funding 0.0`).
- Digests: `config_digest dec528c13815d472…`, `cost_regime_digest 71ea4bd61bdf6f65…`
  (own 20-symbol tick book — differs from the other three), `code_freeze af4df157…`.
- Next decision per heartbeat: `2026-09-28T00:00:00Z`.
- vs `[2026-09-24 snapshot]`: ledger rows identical (1 decision, 8 fills, −63.21).
  Mark equity then 100,083.70 → now 100,348.47 (MTM only). Still 1/52 yearly events used.

### 1.3 BASISLV-PREMFADE-28D
File: same dir, `BASISLV-PREMFADE-28D.jsonl` (1,292 bytes; mtime 2026-09-21 07:11 local — **byte-unchanged since 09-21**)

- Rows: **1**. observed_at `2026-09-21T00:10:37Z`; scheduled `2026-09-21T00:00:00Z`.
- Status: `data_status DATA_BLOCKED`, `accounting_status UNAVAILABLE_FAIL_CLOSED`,
  risk OK; **0 fills**; all PnL fields 0.0; equity 100,000 (FLAT_OK at latest mark).
  `data_snapshot_digest` literally begins `DATA_BLOCKED:mis…` (vendor gap record).
- Digests: `config_digest 47839e9ca55a247a…`, `cost_regime_digest 130d2e7ee97478c0…`.
- Next decision: `2026-09-28T00:00:00Z` (source healed per
  `research/control/DASHBOARD-AND-SHADOW-RELIABILITY-V1/GATES.md` G2 [2026-09-24]:
  13/13 candidates × 30 days, 0 gaps).
- vs `[2026-09-24 snapshot]`: unchanged. Still 0 effective observations.

### 1.4 BTC4H-BANDRIDGE
Live ledger: same dir, `BTC4H-BANDRIDGE.jsonl` (75,098 bytes; mtime 2026-09-25 07:17 local).
Secondary (computation-home) dir: `.worktrees/btc-h4-band-risk-v1/integration/research/control/btc_h4_band_risk_v1/shadow_bandridge/` — `ledger.jsonl` **0 bytes**, `state.json` (mtime 09-24 07:33: equity 100,000, position 0, filled false, last_bucket_ms 1790193600000 ≈ 2026-09-23T20:00Z), `SPEC.md` (MOUNT NOTE explains the production ledger lives in the prospective worktree).

- Rows: **61**. First observed_at `2026-09-24T00:58:11Z` (backfill), last
  `2026-09-25T00:17:35Z`; scheduled decisions 09-15T00:00Z → 09-25T00:00Z H4 cadence.
- Split: **56 UNAVAILABLE_FAIL_CLOSED** (09-15T00Z → 09-24T04Z; carry
  `target_weights {BTCUSDT: 1.0}`, 0 fills, cash guard) + **5 OK** (09-24T08Z →
  09-25T00Z; `data_status OK` on all 61 rows).
- **0 fills ever; all PnL fields 0; equity 100,000 flat** at every row and at the
  01:55Z mark (FLAT_OK). OK rows emit `TARGET_INTENT` with empty `target_weights`
  — no-trade is signal-legal: `band_gate_on=1.0`, `band_r` 0.0543–0.0662
  (> 0.03 gate), `donch_state=0.0` (no breakout yet) on every OK row.
- Digests: `config_digest d7f1ae50b96b1b4e…` (own), `cost_regime_digest
  130d2e7ee97478c0…` (**same shared book as CARRY/BASISLV — no 6bps override
  present in any record**), `code_freeze af4df157…`.
- vs `[2026-09-24 snapshot]`: 57 → 61 rows (+4 OK rows). **Still 0 fills**; the
  sizing A/B/C packet and the 6bps-vs-5bps+tick cost-law question remain open
  (see §4a/§4b). Gate has been continuously ON since the first OK row.

### 1.5 FX-RANGEFADE-2M (EURUSD + GBPUSD, "Phorec")
Files: `.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/{shadow_state.json, shadow_journal.jsonl, daemon_heartbeat.json, equity_curve.json}`

- `shadow_state.json` (schema `phorec.shadow_state@2`, `updated_utc
  2026-09-25T01:56:47+00:00`): one shared $100,000 paper account, **equity
  100,087.0, realized +87.0, unrealized 0.0, both pairs FLAT**, gross exposure 0.
  Sleeves: EURUSD realized **+120.0** (1 fill), GBPUSD realized **−33.0**
  (1 fill). `parity_selftest PASS`. `data_stale false, marks_fresh true`.
  1.5 lots/pair; force-flat law 20:00 UTC noted per pair.
- `shadow_journal.jsonl`: **86 rows** (event_seq 86), first ts
  `2026-09-24T03:25:43Z`, last `2026-09-25T01:00:07Z`. Event census:
  parity_selftest ×22 (all PASS), shadow_start ×11 (restart/replay,
  idempotent boot_replay ×12), bar_closed ×36, **fill_open ×2**,
  **force_flat ×2**, day_roll ×1.
- The 2 round-trips both closed `force_flat` at `2026-09-24T20:00:09Z`:
  - EURUSD long 1.5 lots: entry 1.13685 → exit 1.13765 = +8.0 pips → **+120 USD**
  - GBPUSD long 1.5 lots: entry 1.32225 → exit 1.32203 = −2.2 pips → **−33 USD**
  - FX accounting fields actually present: `pnl_usd`, `entry_px`, `exit_px`,
    `lots`, `realized_total`. **No fee / slippage / funding fields exist** —
    pnl is pure price-move at $10/pip/lot on the opposite TrueFX quote.
- `daemon_heartbeat.json`: `pid_heartbeat_utc 2026-09-25T01:56:47+00:00` (fresh).
- vs `[2026-09-24 snapshot]` (lane_fx_gold, measured ~12:14Z 09-24): then both
  pairs LONG 1.5 lots from 12:00Z, equity 99,952.00 (−48 MTM), 0 closes. Since
  then: both positions force-flattened at 20:00Z, realized +87 net, account
  back to FLAT at +87 vs seed.

### 1.6 XAUUSD-SHADOW-V1 (context only — TERMINAL)
Closeout artifact exists: `research/control/XAUUSD-SHADOW-V1/CLOSEOUT_OWNER_REMOVAL_2026-09-24.md` (2,936 bytes, mtime 2026-09-24 19:55 local). One-line claim: TERMINAL owner-removal per owner instruction ("bỏ XAUUSD swing ra khỏi hệ thống"); measured pre-stop state 76 ledger + 76 raw_bars rows, **0 entries / 0 fills / 0 orders ever**; nothing deleted; shadow program continues as 6 sleeves on $600k paper (FX pair shares one account).

---

## 2. PnL accounting definitions actually present per ledger (for A1 reconciliation)

Facts only — measured identities from bytes, no verdicts.

### 2.1 Crypto decision ledgers (schema `shv1_event_v1`, 4 files)
Field names present per row: `gross`, `price_pnl`, `fee`, `slippage`,
`funding_cashflow`, `net`, `total_pnl`, `equity`, `cash`; per-fill objects in
`virtual_fill_events` carry `fee` and `slippage_amount` (and `ref_price`,
`fill_price = ref ± 1 tick`, `qty`, `tick_size`).

Measured identities (exact across every populated row of CARRY + ILLIQ):
1. **`total_pnl = price_pnl + funding_cashflow`** (exact, all rows).
2. **`price_pnl ≈ −(fee + slippage)`** with residual |·| ≤ ~0.005 USDT — i.e.
   the field named `price_pnl` is booked NET of fee+slippage at the decision
   bar (gross market move ≈ 0 at the entry bar; it is not a gross price-PnL field).
3. **`net` = 0.0 constant** in every decision event (it is not booked net PnL).
4. **`gross` = sum of |target_weights|** (exposure fraction: 0.8004 CARRY,
   1.0006 ILLIQ, 0.0 BANDRIDGE OK-rows) — NOT gross PnL in dollars.
5. **`equity`/`cash` at decision rows are mark-to-market snapshots including
   unrealized**, not compounding from booked `total_pnl` (CARRY equity path
   99,954 → 98,645 → 98,918 → 98,457 → 99,947 → … → 99,948 while cumulative
   booked total_pnl drifts only −349.85). The unrealized component lives in
   `valuation_marks/*.jsonl` (fields there: `realized_pnl`, `fees`, `funding`,
   `net`, `equity`, `cash`, `positions[]` with `avg_price`/`mark_price`/`notional`;
   latest marks 2026-09-25T01:55:00Z: XSECT equity 99,094.92 / ILLIQ 100,348.47 /
   BASISLV + BANDRIDGE 100,000 FLAT).
   Consequently: booked Σtotal_pnl (−349.85 CARRY) and mark equity (99,094.92)
   are **two different bases** and must not be summed or compared as one number
   (the 09-24 OWNER_REPORT already showed the same split: "realized +3,936.27"
   vs equity MTM +428.15 [2026-09-24 snapshot]).
6. Digest fields present in every record: `config_digest`, `cost_regime_digest`,
   `code_freeze_sha`, `data_snapshot_digest` (per-sleeve values in §1).
   CARRY/BASISLV/BANDRIDGE share `cost_regime_digest 130d2e7e…`; ILLIQ has its
   own `71ea4bd6…`; no record carries a 6bps-specific digest.

### 2.2 FX journal (schema `phorec.*`)
Fields present: `pnl_usd`, `realized_total`, `entry_px`, `exit_px`, `lots`,
`dir`. **No fee, slippage, or funding field exists**; PnL is gross price-move
($10/pip/lot, opposite TrueFX indicative quote at fill). Equity basis is the
single shared $100k account (state file `account.equity`), not per-pair.

### 2.3 XAUUSD (terminal)
Never triggered; declared cost law was constant 4 bps round-trip
("UNMEASURED-CONSERVATIVE" label), so no booked PnL definition ever materialized.

### 2.4 Cross-ledger definition conflicts visible from bytes (facts)
- Crypto `price_pnl` is net-of-costs-at-bar; FX `pnl_usd` is gross with no cost
  fields at all. Same word "PnL", different definitions.
- Crypto `equity` (decision rows) is MTM-inclusive and non-compounding;
  `valuation_marks` equity is the live MTM series; FX equity is one shared
  account including realized only when flat. Three equity bases coexist.
- Funding: booked per 8h settlement in CARRY only (Σ +4.60); ILLIQ shows 0.0
  (open since 09-21; whether a settlement has simply not been booked is not
  determinable from the ledger bytes alone — same NOT_RUN note as the 09-24 lane).

---

## 3. Worker / heartbeat liveness (read-only `ps` + heartbeat files, 2026-09-25)

| Process | pid | Evidence | Freshness |
|---|---|---|---|
| crypto `shadow_worker.py` (prospective worktree) | 35779 | `ps aux` + `.../runtime/heartbeat.json` (`pid 35779`, `last_loop_utc 2026-09-25T01:52:52Z`, loop_count 211, `shutdown_signal null`, inode-vs-path check match true) | fresh |
| crypto `valuation_worker.py` | 35871 | `ps aux` + `.../runtime/valuation_heartbeat.json` (`pid 35871`, `last_loop_utc 2026-09-25T01:55:00Z`, loop 212, marks_written 724, `heavy_lock_verdict FREE_PROVEN`) | fresh |
| FX `shadow_daemon.py` | 35609 | `ps aux` + `daemon_heartbeat.json` (`pid_heartbeat_utc 2026-09-25T01:56:47+00:00`) | fresh |
| FX dashboard `serve.py` | 8093 | `ps aux` | running |
| Quant Shadow Dashboard.app | 46011 | `ps aux` | running |
| `shadow_view_server.py` | 22766 | `ps aux` | running (since Sun) |

Heartbeat `last_completed` matches ledger last rows for all 4 crypto sleeves;
`next_decision_per_family`: CARRY 09-26T00:00Z, BANDRIDGE 09-25T04:00Z, ILLIQ +
BASISLV 09-28T00:00Z. No stale heartbeat found at measure time.

---

## 4. Extracted measured claims — SHADOW-PAPER-REVIEW-V1 lane reports (2026-09-24)

Source files: `research/control/SHADOW-PAPER-REVIEW-V1/lane_crypto_sleeves/REPORT.md`,
`.../lane_fx_gold/REPORT.md`, `.../lane_portfolio_program/REPORT.md` (plus the
packet under DASHBOARD-AND-SHADOW-RELIABILITY-V1). Verbatim-short, cite kept.

### (a) BANDRIDGE sizing A/B/C + fill-law A/B (packet `OWNER_DECISION_PACKET_bandridge_sizing_and_fill_law.md`)
Mechanism measured: sizing `qty = w*equity/ref` + buy-side cash guard
`qty*fill_price + fee ≤ cash` with `fill_price = ref + 1 tick`, fee 0.05% →
w=1.0 needs ≈ **100,050.02** USDT on 100,000 cash → `InsufficientCashError` →
whole rebalance cancelled pre-mutation, 0 fills, event fail-closed.
- **Q1 Sizing**: A = keep fail-closed (sleeve stays $100k idle forever);
  B = **cost-aware sizing** `qty = min(w*equity/ref, cash/(fill_price*(1+fee)))`
  → realized weight ≈ 0.99946, `realized_weights` logged per event, needs
  identity-manifest amendment; C = tolerance on cash guard (`needed ≤ cash*(1+tol)`,
  e.g. tol 1e-3 → fill 1.0 with cash −$50 temporarily) = changes accounting
  semantics (micro-overdraft), stronger amendment. Lane recommendation was B.
- **Q2 Fill law**: docstring/SPEC promise "fill at NEXT H4 OPEN" vs executor
  filling at the **first completed 15m bar** after the boundary (+1 tick adverse).
  A = fix the doc to match the executor (15m-bar is canonical; doc-only, re-pin
  SPEC hash); B = re-derive executor to H4-open (forward-only amendment +
  preregister + parity tests). Lane recommendation was A. Finding recorded-not-fixed
  at commit a8062b1a (`.../findings/FINDING-2026-09-24-fill-timing-h4-open-vs-15m-bar.md`).
- Owner decision field in the packet: still blank as of today's read.

### (b) Cost-identity finding: SPEC 6 bps/side vs executor 5 bps + 1 tick
- Identity manifest pins `fee_bps_per_side: 6.0` for BANDRIDGE
  (`.worktrees/prospective-shadow-v1/integration/research/control/prospective_shadow_v1/identity/identity_recovery.json`
  families[3]; SPEC.md sha `3a7591fb…`; amendment A1 of
  `plans/PLAN_prospective_shadow_v1.md` says "6 bps/side").
- Production executor books `FEE_RATE_CURRENT = 0.0005` (5 bps) + 1 tick
  adverse for every family (`e/shadow_worker.py` L180, L508–524 `cost_books_for()`;
  `accounting.py:354-356` fee = qty·ref·fee_rate; fill at ref ± 1 tick).
- Every BANDRIDGE ledger row carries `cost_regime_digest 130d2e7e…` — the same
  shared book as CARRY/BASISLV, i.e. **no 6bps override exists in any record**
  (re-confirmed today, §1.4). Gap ≈ 2 bps per round-trip on notional.
  Still unmaterialized (0 fills), but both lane reports require it be settled
  before the first fill.

### (c) FX short-beta control — MANDATORY law source
- `EURUSD-OPEN-SEARCH-V2` terminal, commit **bf4f07f1**: "T1 preregister
  short-beta control for any paper-forward successor" (holdout 2026-H1:
  C3 +274.0 pips vs SHORT_ALWAYS +314.0 — naive short beat the strategy).
- `EURUSD-RANGEEXP-SCORED-V1` terminal, commit **83264434**: "short-beta control
  **mandatory** in paper-forward successor" (holdout baselines: LONG −395 /
  SHORT +314 / RANDOM −267.7 pips).
- FX-RANGEFADE-2M-SHADOW-V1 is the paper-forward successor of that same book
  (family RANGEEXP-C3). At review: control NOT mounted (code grep: no control arm).
  Today's re-check of the 86-row journal: still no control-arm events of any kind.

### (d) XSECT turnover / cost-drag numbers [2026-09-24 snapshot, 10 days]
- Turnover ≈ **0.62x/day** (Σ traded notional 492,853 USDT / 10 days / ~80k book);
  4 direction flips / 40 (symbol,day); books XRP long 9/10 days, DOGE short 9/10.
- Costs booked first 10 days **302.83 USDT ≈ 30.3 bps of equity ≈ ~11%/yr
  run-rate**; funding collected only **+4.60 USDT (~1.7%/yr)** with negative
  days (−1.73, −1.68). Historical edge +20.6%/yr (plan §3.3) → cost book eats
  ~half of the historical edge. Today's remeasure extends the same series to 11
  days: Σfee 286.43 + Σslip 68.02 = 354.45 USDT gross costs booked, funding +4.60.

### (e) Power analysis (52-week window vs Sharpe thresholds) [lane_portfolio_program §3]
Law used: min detectable per-decision Sharpe after n obs = z/√n; z=1 (~1σ),
z=2 (~95% two-sided). General conclusion: **a 1-year window only separates
edges with annualized Sharpe ≥ ~2.0 at 2σ (≈1.0 at 1σ)**.

| Sleeve | n/year | 1σ threshold | 2σ threshold |
|---|---|---|---|
| XSECT daily | 365 | 0.052 | 0.105 |
| FX 2-pair | ~350 RT (from holdout 87 RT/6mo ×2) | 0.053 | 0.107 |
| ILLIQ/BASISLV weekly | 52 | 0.139 | **0.277 (≈ annualized Sharpe 2.0)** |
| BANDRIDGE (if filled) | ~18 RT | 0.236 | 0.471 |
| XAUUSD | ~6.4 RT | 0.395 | **0.791** |

Years to t=2 for true per-decision Sharpe s: s=0.05 → 4.4y (XSECT) / 30.8y
(weekly) / 250y (XAUUSD); s=0.10 → 1.1y / 7.7y / 62.5y; s=0.30 → 0.1y / 0.9y / 6.9y.
Corollaries measured in the lane: historical PF 1.354841 (ILLIQ) / 1.360047
(BASISLV) sits below the weekly 2σ threshold → 52-week window under-powered for
both; BANDRIDGE information rate was 0 by construction (57 decisions, 0 fills);
XAUUSD near-infinite (rarity ≈ 1 entry / ~5.1 years); FX and XSECT are the only
sleeves with discriminating power inside a year. Structural finding: PSV1
checkpoints (13/26/52 weeks) are calendar-based and no promote/kill/time-stop
statistical law is preregistered anywhere in the 3 plans (PSV1 §7/§12/§13
verbatim-quoted in the lane report; FX and XAUUSD plans have none at all).

---

## 5. DASHBOARD-AND-SHADOW-RELIABILITY-V1 (untracked owner evidence dir)

Files: `A7-RELIABILITY-AUDIT-2026-09-24.md` (14,033 B), `GATES.md` (18,219 B),
`OWNER_DECISION_PACKET_bandridge_sizing_and_fill_law.md` (3,898 B),
`OWNER_REPORT_2026-09-24.md` (8,811 B).

Measured reliability verdict line (A7 audit, dated 2026-09-24):
> "A7 VERDICT: CONFIRM"

— fresh-context re-audit: 56 fills (CARRY 48 + ILLIQ 8) exact against the frozen
cost law, 0 duplicate event_ids, append-only intact, no signal/executor/accounting
law touched by the 6-commit crypto batch, BANDRIDGE fail-closed root cause real
and owner-open, dashboard 2,033-point combined history + mount-day PnL identity
reproduce bit-exact from mark bytes (1,983/2,033 exact-match points cited in the
lane report), honest fail-closed display. GATES.md total gate: PARTIAL (market/
owner items pending). OWNER_REPORT overall status: e-worker + valuation worker +
FX daemon all running correct HEAD after controlled restart, ledger byte-counts
identical before/after restart (no event duplication).

Note: BANDRIDGE byte counts cited in the 09-24 lane (70,298) vs today (75,098)
differ only by the 4 appended OK rows — consistent with append-only.

---

## 6. NOT_RUN / limitations of this remeasure

- Win-rate and per-round-trip realized PnL: **not recomputable** — the
  `shv1_event_v1` schema has no per-fill realized_pnl (aggregate fee/slip/funding
  + MTM equity only). Same NOT_RUN as the 09-24 lane.
- The CARRY "realized +3,936.27" OWNER_REPORT component: different accounting
  basis; cannot be re-derived from decision-event bytes (no per-fill attribution).
- Per-decision σ for ILLIQ/BASISLV/FX: still NOT_RUN (0–1 fill events each);
  power table quoted from the lane, not re-estimated.
- FX prospective signal frequency (~350 RT/yr) is a holdout-derived estimate,
  not re-measurable from 2 fills.
- Registry heads (`plans/CYCLE_REGISTRY.json`) not re-read in this lane;
  worktree HEAD statuses quoted from the 09-24 artifacts (drift notes there:
  PSV1 registry vs 236bf2f7, FX registry 4bdfd0e vs f8bb2b73 — not re-verified).
- ILLIQ funding = 0.0 booked: whether an 8h settlement has occurred since the
  09-21 open is not determinable from ledger bytes (flagged, not resolved).
- XAUUSD 9-intent replay evidence remains commit-message + registry + tests
  (no independent data artifact exists) — inherited NOT_RUN from the fx_gold lane.

— quant-explorer lane `state-remeasure`, ECONOMIC-ROBUSTNESS-PROGRAM-V1, 2026-09-25.
