# FX-MAJORS-BROKER-COST-PROBE-V1 — session report #1 (2026-09-26, BLOCKED_TWS_SESSION_DISCONNECTED)

Status: **probe paused at the owner action boundary** — no data component
measured beyond connectivity. Preregistration: `PROBE_CONTRACT_DIAGNOSIS.md`
(committed `cfd717c8` BEFORE any handshake). This report records everything
measured so far + the blocker + the exact resume path.

## Verdict (split, per contract §5)

1. **V1 API connectivity: PARTIAL_PASS (socket + handshake PROVEN; session-level data channel NOT usable now)**
   - `127.0.0.1:7497` listening; raw-ibapi handshake completed with
     `serverVersion=223` + `managedAccounts` received (multiple sessions:
     clientIds 9033/9041 measurement runs 2026-09-26 ~04:5x–05:0xZ).
   - **TWS server-side Read-Only mode CONFIRMED ACTIVE**: error 321 rejected
     `ReqOpenOrders`/`ReqCompletedOrders` ("The API interface is currently in
     Read-Only mode") — the guard works; no order channel is usable through
     this session even by accident (defense-in-depth held).
2. **V2 market data usable: NOT_RUN — BLOCKED (TWS↔IBKR server link down)**
   - TWS raised 2110 ("Connectivity between Trader Workstation and server is
     broken") and 2157 ("Sec-def data farm connection is broken: secdefil");
     reqContractDetails returned nothing within 20s+; a full 360s stream
     window recorded **0 valid observations** (all grid cells missing, no
     forward-fill — honestly empty, not zero-spread).
   - Screen check (read-only, no click): TWS shows modal **"Login Error —
     Login failed - Server disconnected, please try again"** → the paper
     session is logged OUT server-side. No API data can flow until re-login.
3. **V3 broker cost authority: NOT_RUN** (depends on V2 + statements).

## P3-A comparison

Not computable this session (no spread samples). The frozen law stands
untouched: all-in crossing ≤ 0.41 pips @k=2.0; no threshold/fill-law change.

## Engineering incidents (P-19 disclosure — all mine, none touch data identity)

1. ib_insync auto-sync (`reqOpenOrders`/`reqPositions`/`accountUpdates`)
   blocked by Read-Only mode → connect failed; switched to raw `ibapi`
   (whitelist-literal). ib_insync left installed in `.venv` (operator class).
2. `reqManagedAccounts`→`reqManagedAccts`, `eConnect`→`connect`,
   `eDisconnect`→`disconnect` method-name fixes across ibapi version drift;
   `error()` callback made catch-all (`*a`) after a 6-arg message killed the
   reader thread; handshake wait-loop added after a race; random fresh
   clientId per attempt (stale-session avoidance).
3. One full 360s stream ran with 0 observations (blocked TWS) — its empty
   raw file is honest evidence (kept), no fabrication.
4. Backgrounded shells auto-retried a few times producing several 0-byte raw
   files — all from my own probe process, all killed; no foreign process
   touched; heavy lock never held (light socket reads only).

## Owner action to resume (the ONLY thing missing)

Re-login the TWS **Simulated Trading** session (paper credentials are
owner-only; the Login Error dialog is on screen — I did not click anything).
Keep Enable ActiveX + Read-Only API as configured. If TWS shows the
"incoming API connection" dialog during my rerun, approve it (or tick
auto-accept at your discretion — that is an owner config choice).

Resume path after re-login (no new gates needed — this probe's authority
chain is §1 of the contract; the rerun re-enters at the same whitelist):
`nohup .venv/bin/python -u research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/
broker_cost_probe_FX_majors_2026-09/probe_fx_majors_raw.py > /tmp/fx_probe_run2.log 2>&1 &`
then verdict assembly from `data_local/sanitized_result_*.json`.

## Files

- `probe_fx_majors.py` (ib_insync variant, deprecated for this environment)
  sha256 `4743b164…`; `probe_fx_majors_raw.py` (operative, whitelist-literal)
  sha256 `841d09cf…`; raw evidence under `data_local/` (gitignored, hashed
  at verdict time); screen evidence of the Login Error modal recorded in
  this report (transcript), no screenshot bytes committed.
