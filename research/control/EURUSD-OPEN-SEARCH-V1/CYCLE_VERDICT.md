# CYCLE VERDICT — EURUSD-OPEN-SEARCH-V1 (registration state, 2026-09-23)

- Date (UTC): 2026-09-23
- Branch: `orca/eurusd-open-search-v1-integration` (worktree
  `.worktrees/eurusd-open-search-v1/integration`), base = plan commit
  `bf5e8191ebf0cd1fa3d2e0b6e044cdaedf8f29d0` on `main`
- Plan: `plans/PLAN_eurusd_open_search_v1.md`
- Owner directive: 2026-09-23 (open search under D2 owner waiver; this
  instruction is NOT a GO)
- P1 evidence: `P1_SOURCE_RESURVEY_2026-09-23.md`, `P1_VERDICT.json`

## VERDICT: `BLOCKED_SOURCE_LICENSE` (registration state; P1 phase)

Exactly one enum per plan §6. The blocker is DATA LICENSE — the campaign
never reached any signal, backtest, or PnL computation.

## Why (one paragraph)

The owner-ordered re-survey of TrueFX from its original terms found the
historical tick downloads login/registration-gated with the license text
visible only after login and no public terms document at all; every legacy
anonymous archive URL pattern returns 404. The OANDA v20 Practice path is
owner-conditional and no owner-issued credential exists (`.env` name
census, values unread). Dukascopy remains blocked absent written consent
(EURUSD-DATA-QUALIFICATION-V1 `BLOCKED_SOURCE_LICENSE` @ 2026-09-22 stands;
nothing new landed since — no commits, no credentials, no license files).
Additional sweep (HistData, TickData, OlsenData, Polygon, Dukascopy-derived
"free" resellers) surfaces no source that clears the six-criteria
checklist. Free is not authorized; fail-closed applies. Zero PnL was
computed; 0 of 96 trials executed; D2 was never evaluated and is recorded
`OWNER_WAIVED_EXPLORATORY` (not PASS); all historical forex verdicts are
untouched.

## Census

| Item | State |
|---|---|
| PnL computed | 0 (forbidden by plan §1) |
| Trials executed | 0 / 96 cap |
| Denominators | unchanged (forex 48/48, program 283/286 per ledger) |
| S1 | SEALED_UNTOUCHED (no strategy surface exists yet) |
| Heavy lock | NOT contended (held by CRYPTO-HISTORICAL-REPLICATION-3F-V1) |
| Secrets | none printed or committed |

## Owner actions (pick ONE to unblock)

1. **TrueFX (recommended first)** — register the free account personally
   (agent signup prohibited), capture the verbatim license at the
   historical-downloads page and paste it into this cycle. License
   permitting internal-research storage + programmatic monthly-zip
   retrieval → source becomes PRIMARY; P1-bis bounded probe (7–14 days)
   starts.
2. **OANDA v20 Practice** — register the free practice account and accept
   its terms personally; provide the token as a new env name (never
   printed/committed). Then API-terms storage review + empirical bid/ask
   probe.
3. **Dukascopy written consent** — email Dukascopy Bank SA for express
   written consent (automated bi5 retrieval, internal non-commercial
   research, derived-dataset retention). A consent letter in this cycle is
   license authority.
4. **Paid vendors** (TickData.com, OlsenData, Polygon $49+/mo) — explicit
   owner purchase authorization if free paths fail.

After any path clears: P1-bis bounded probe → data manifest freeze with
dev/holdout split dates → A7 prelaunch → owner GO (fresh, verbatim:
`GO EURUSD OPEN SEARCH V1 EXPLORATORY SCORED`) → ≤96-trial exploratory
campaign → candidate freeze or NO_CANDIDATE → single sealed-holdout check.

## What was NOT done

No strategy, hypothesis scoring, backtest, candidate freeze, holdout
open, or A7 prelaunch (nothing to audit yet beyond this verdict artifact —
an independent fresh-context audit of THIS close runs at registration per
governance; see `audits/` when present). No account creation, no terms
acceptance, no purchases, no downloads beyond HEAD/GET availability
probes of HTML endpoints, no secrets read (names only).
