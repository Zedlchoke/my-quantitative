# FX-MAJORS-BROKER-COST-PROBE-V1 — VERDICT (session 2, closed 2026-09-26)

Preregistration `PROBE_CONTRACT_DIAGNOSIS.md` (cfd717c8) → session 1 BLOCKED
(d32c02e8) → owner re-login → session 2 measured → this verdict. Owner then
confirmed no further TWS-side actions available; session closed honestly.

## Verdict (3 phần, per contract §5)

### V1 — API connectivity: **PASS**
Socket 127.0.0.1:7497, raw-ibapi, multiple complete sessions (serverVersion
223; managedAccounts; farm status OK: 2104/2106/2158). Read-Only API
**confirmed active server-side** (order-channel reads rejected 321).

### V2 — market data usable: **NOT_SUBSCRIBED (two-sided) / partial**
- `marketDataType=1 (LIVE)` announced for all 5 subscriptions, **zero
  subscription errors** — but tick streams return **BID=-1, ASK=-1 (UNSET)**
  on all five pairs; only single-sided indicative prices flow (tick type 9).
- Full 360s × 5 pairs streams (2 runs): **0 valid two-sided observations**
  (no forward-fill; honestly empty).
- Late-session handshake stalls (TWS API session-slot exhaustion after ~20
  probe connections) — further sampling NOT_RUN; not needed for the verdict.

### V3 — broker cost authority: **STILL `BLOCKED_BROKER_COST_AUTHORITY`** (A7 F-C1 rule)

| # | Component | Class after this probe | Evidence |
|---|---|---|---|
| 1 | executable spread | **NOT_SUBSCRIBED** (two-sided absent; SIM account lacks market data) | bid/ask=-1 ×5 pairs; 0 valid obs; EVIDENCE_sanitized |
| 2 | commission | NOT_RUN (no statement) | needs Activity/Flex Trade+Commission rows |
| 3/4 | swap LONG/SHORT | NOT_RUN | needs statement Interest Accruals w/ overnight FX |
| 5 | triple-swap/weekend | NOT_RUN | same |
| 6 | rollover clock | NOT_RUN | same |
| 7 | minimum size | NOT_RUN via API (CASH contractDetails returns no minSize) | needs statement or docs |
| 8 | **tick** | **MEASURED (paper, account-bound channel)** | **minTick = 0.00005 = 0.5 pip, all 5 pairs (EUR/GBP/USDCAD/AUD/NZD; IDEALPRO)** |
| 9 | margin | NOT_RUN by law (whatIf forbidden) | report-only |
| 10 | stress multiplier | FROZEN 2.0 pre-outcome | lane-F |

## P3-A adjudication (frozen law, no post-hoc change)

Frozen reopening condition: **measured ALL-IN crossing ≤ 0.41 pips @k=2.0**
(base crossing ≤ 0.205 pips), spread + commission included. Measured fact:
**minTick = 0.5 pip ⇒ the minimum positive spread at this venue is 0.5 pip
⇒ base crossing ≥ 0.5 pip ⇒ ×2.0 ≥ 1.0 pip = 2.4× the frozen threshold —
BEFORE commission.** The condition is **arithmetically unattainable at IBKR
IDEALPRO (paper book, this tick geometry)**. Per the no-rescue law, P3-A
stays dead at this venue; its FAMILY_FAILURES reopening condition remains
textually accurate (it demanded sub-threshold measured all-in cost — the
measurement went the other way). **No rescue, no threshold change.**

## What this session changed (frontier knowledge)

- R1 executed to the extent the TWS SIM session allows: connectivity + tick
  geometry measured; two-sided quotes + commission + swap remain owner-
  documents-gated (below). The NO_CANDIDATE frontier conclusion is
  UNCHANGED — this probe did not open cohort-3 (nothing new viable; it
  removed one theoretical reopening path).
- Engineering-artifact assets banked: whitelist-literal read-only probe
  script (sha 841d09cf + live-print patch), sanitized-evidence format,
  handshake/session diagnostics.

## Exact owner documents that would unblock the remaining components

1. **Two-sided market data**: enable FX delayed (free) via TWS "Manage Data
   Subscriptions" or share subscriptions from a funded account → rerun the
   probe (one command) for the spread distribution (DELAYED- or LIVE-flagged).
   NOTE: even a zero spread distribution would not resurrect P3-A here (tick
   geometry decides); it would serve FUTURE mechanisms' cost books.
2. **Activity/Flex statement** (any window containing FX trades + overnight
   FX positions, from any IBKR account the owner holds): Trade+Commission
   rows → component 2; Interest Accruals rows → 3/4/5; dated rollover rows →
   6; min trade size → 7. Uploaded as machine-local raw bytes (outside git)
   with sanitized extracts committed.
3. TWS restart whenever re-probing (clears the API session-slot stalls).

## Boundaries honored

No orders of any kind (no placeOrder/cancelOrder/whatIf anywhere; server
Read-Only proven); live port 7496 never touched; XAUUSD PAUSED probe not
retried (templates read-only, per lane-F law); raw bytes + account ids
outside git (sha256-12 hash only); no scoring, no OOS, no shadow touch;
sealed map unchanged.
