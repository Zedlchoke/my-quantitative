# PROBE CONTRACT + DIAGNOSIS — FX-MAJORS BROKER COST PROBE V1 (preregistered BEFORE any handshake)

Artifact id: `ERP-FX-MAJORS-BROKER-COST-PROBE-V1` · declared 2026-09-26, by
Lead, under umbrella `ECONOMIC-ROBUSTNESS-PROGRAM-V1` (ACTIVE_LIGHT) — this
file is the NEW PREREGISTERED DIAGNOSIS that lane F's owner-deliverable
Option A requires before any TWS handshake ("the paused TWS handshake itself
is NOT retried without a new preregistered diagnosis per plan §3").

## 1. Authority chain (why no amendment/A7/GO is needed BEFORE the handshake)

1. Owner instruction 2026-09-26 (latest explicit instruction — authority #1):
   TWS Simulated Trading opened, ActiveX+Socket+Read-Only API enabled, port
   7497; "hãy xử lý cửa R1"; probe scope/API-whitelist/verdict-split verbatim.
2. Lane F dossier (DATA-EDGE-UNLOCK-V1, TERMINAL, read-only citation):
   `owner_deliverables[Option A]` preregistered EXACTLY this action — "Start
   TWS or IB Gateway LOGGED IN with Read-Only API enabled... then a
   preregistered FX-majors probe (design templates REUSED verbatim from
   research/control/xauusd_ibkr_probe_2026-09/...)" with the new-diagnosis
   precondition satisfied by THIS file.
3. Umbrella §2.2 permission boundary: read-only intake and re-measurement is
   ALLOWED under the umbrella's light authority; the probe scores nothing,
   creates no cycle, holds no lock (light socket reads), touches no worker.
4. What DOES need gates (none exist yet): any plan amendment reopening the
   frontier, any cohort registration, any scoring — each with A7 + owner GO
   AFTER this probe's evidence exists. This probe itself stops at evidence.

## 2. Distinction from the PAUSED XAUUSD probe (binding)

- The XAUUSD/IBKR handshake of 2026-09-16 stays **PAUSED-probe standing
  NOT_RUN, NO RETRY** (lane-F known_limitations verbatim). The 2026-09-26 TWS
  session is NOT authority to retry it: XAUUSD was owner-removed
  (XAUUSD-SHADOW-V1 terminal); its reopening is a separate owner-registered
  decision. XAUUSD files under `xauusd_ibkr_probe_2026-09/` are READ as
  DESIGN TEMPLATES ONLY (lane-F verbatim rule).
- This probe's instrument set: **EURUSD, GBPUSD, USDCAD, AUDUSD, NZDUSD**
  (secType CASH, exchange IDEALPRO, currency USD — verified via
  contractDetails at session start; no other instrument is queried).

## 3. Scope, API whitelist, prohibitions

- Connect `127.0.0.1:7497` ONLY (TWS Simulated/paper port). **Port 7496
  (live) is FORBIDDEN** — no connection attempt to it, ever, in this probe.
- API calls whitelisted (complete list — anything not listed is not called):
  `connect/isConnected/disconnect`, `reqCurrentTime`, `reqManagedAccts`,
  `reqAccountSummary` (read), `reqContractDetails` (5 FX contracts),
  `reqMarketDataType(1)` with recorded DELAYED(2) fallback (flagged), and
  standing `reqMktData` subscriptions (≤5 concurrent lines) streamed
  event-driven on a 1-second grid (template cadence; no snapshot polling).
- **FORBIDDEN (hard)**: `placeOrder`, `cancelOrder`, `reqMarginChangesForOrder`
  / whatIf, `reqGlobalCancel`, any config/trading-setting change, any order
  of any kind, any position creation (paper or live), any live-gateway
  connection. The probe script contains no order-function calls at all.
  Server-side Read-Only API (owner-enabled) is defense-in-depth, not the
  primary control. If TWS shows an "incoming connection" approval dialog,
  the owner approves it manually; the probe retries connect once.

## 4. Measurements → lane-F ten-component mapping (PASS rule verbatim)

A7 F-C1 binding rule: components 3,4,5,6 (swap LONG/SHORT, triple-swap
convention, rollover clock) must be MEASURED from ACCOUNT-BOUND bytes for
PASS; components 1,2,7,8 (spread, commission, min-size, tick) account-bound
measured unless declared stated-class with frozen stress coverage. Component
9 margin = REPORT-ONLY; 10 = frozen stress multiplier 2.0 (pre-outcome).

| # | Component | This probe's source | Expected class honestly |
|---|---|---|---|
| 1 | executable bid/ask spread | streaming reqMktData distribution (≥6 min, event-driven, no forward-fill, validity bid>0, ask≥bid) | MEASURED (paper-session quotes; LIVE vs DELAYED flagged per marketDataType) |
| 2 | commission | NOT in the TWS socket API; needs Activity/Flex statement Trade+Commission rows | likely NOT_RUN (no trade history on the SIM account) — exact owner document listed |
| 3/4 | swap LONG/SHORT | Flex statement "Interest Accruals" per overnight FX position | NOT_RUN absent a statement with overnight FX positions — **never place an order to create one** |
| 5 | triple-swap/weekend | dated accrual rows around Wednesdays in the statement | NOT_RUN (same evidence class) |
| 6 | rollover clock | broker timestamp convention from statement/rollover rows | NOT_RUN (same) — the Dukascopy 22:00 UTC archive convention is a VENDOR convention, never broker evidence |
| 7 | minimum size | contractDetails (minSize/sizeIncrement where returned) | MEASURED (account-bound channel) |
| 8 | tick | contractDetails minTick | MEASURED |
| 9 | margin | REPORT-ONLY, unmeasured via API (whatIf forbidden) | NOT_RUN by law |
| 10 | stress multiplier | frozen 2.0 pre-outcome (lane-F) | FROZEN |

## 5. Verdict taxonomy (split, per owner instruction)

1. **V1 API connectivity** — PASS/FAIL (+TWS approval-dialog handling noted).
2. **V2 market data usable** — per pair: LIVE / DELAYED / NOT_SUBSCRIBED,
   with n_valid/n_invalid ticks, spread percentiles IN PIPS (pip = 0.0001
   for the five USD-quoted majors) and the sampled UTC hour window honestly
   recorded (the probe cannot choose the hour; no claim about other hours).
3. **V3 broker cost authority** — per-component table + overall verdict:
   `PASS_BROKER_COST_AUTHORITY` only under the A7 F-C1 rule; otherwise
   `BLOCKED_<missing-evidence>` with the exact owner documents needed.

Paper vs live: this session is **TWS SIMULATED (paper)**; every number in
this probe is PAPER-SESSION and labeled so. A paper commission rule realized
by simulated fills proves schedule mechanics, never live execution. No paper
number is ever reported as a live fill.

## 6. P3-A comparison law (frozen BEFORE measurement — no post-hoc change)

Cohort-2 froze P3-A's reopening condition: **measured ALL-IN crossing cost
≤ 0.41 pips at k=2.0** (equivalently base crossing ≤ 0.205 pips; the 0.81
@k=1.0 weaker bound also recorded), where crossing = full spread a−b per
side per the frozen fill law, and ALL-IN includes commission when it exists
as evidence. The comparison in this probe: per pair, measured crossing
percentiles ×{1.0, 2.0} vs the frozen threshold, computed both WITHOUT
commission (spread-only) and WITH stated-class commission if a citable
account-attached schedule exists (otherwise commission stays an explicit
unmeasured add-on that can only worsen the verdict). **No threshold change,
no fill-law reinterpretation after seeing numbers. If measured cost exceeds
the threshold, P3-A stays dead — no rescue.** (Spread samples from this
probe are PAPER-SESSION quotes at the sampled hours only; even a sub-threshold
measurement opens at most an AMENDMENT proposal for owner GO — it does not
rescore anything by itself, and delayed-data samples carry the DELAYED flag
with weakened evidentiary class.)

## 7. Data hygiene

Raw tick JSONL + account bytes → `research/control/ECONOMIC-ROBUSTNESS-
PROGRAM-V1/broker_cost_probe_FX_majors_2026-09/data_local/` (machine-local,
gitignored). Committed evidence: sanitized aggregates (percentiles, counts,
contractDetails fields, hashed account id sha256-12), script sha256, raw-file
sha256. No credentials, no full account numbers, no PII in git. This probe
must never touch candidate returns/PnL/signals (outcome-blindness, template
verbatim).

## 8. Stop conditions

Any unexpected order-channel response, any prompt to accept outgoing
messages, any live-gateway ambiguity ⇒ disconnect immediately + record +
STOP. Statement-dependent components never trigger compensating actions.
