# DATA-FOUNDATION-SIXSOURCE-V1 — intake (controller A1, 2026-09-28)

Read-only data-foundation session over six source groups per owner
instruction 2026-09-28 (verbatim anchor preserved in
`dispatch/OWNER_DIRECTIVE_2026-09-28.md`): (1) FX cost-band IBKR,
(2) crypto orderbook/L2, (3) on-chain, (4) options, (5) rates intraday,
(6) CME.

## Hard non-goals (owner's)

No scored cells, no S1/OOS opening, no orders (no placeOrder/cancelOrder/
whatIf anywhere), no shadow/dashboard touch, no credential in prompt/log/
git, no paid package enablement, no account signup, no bulk purchase, no
candle substitution for missing L2/proxy bytes, TWS Read-Only config not
modified.

## Re-measured intake (2026-09-28T01:55Z)

- Root `/Users/hoangminhlong/my-quantitative`, branch `main`,
  HEAD `f98087f632552f11d68c5b6b66708d46545f750e`.
- Dirty tree: owner's modified `plans/ACTIVE_CYCLES.json`,
  `plans/CYCLE_REGISTRY.events.jsonl`, `plans/CYCLE_REGISTRY.json` +
  untracked dirs of other sessions — **preserved untouched, not staged,
  not committed** (P-8/P-9).
- Heavy lock: FREE_PROVEN (no holder, no flock).
- Disk: 26 GiB free of 228 GiB (root volume) — above the 5 GiB floor used
  by prior data cycles.
- Active light neighbors at intake: PROSPECTIVE-SHADOW-V1,
  LIVE-DATA-GATEWAY-V1, FX-RANGEFADE-2M-SHADOW-V1, ILLIQ-LOSS-MECH-V1,
  ETHUSDT-OPEN-SEARCH-V2, SHADOW-PAPER-REVIEW-V1,
  ECONOMIC-ROBUSTNESS-PROGRAM-V1, EVENT-MECHANISMS-V1, DAYTRADER-100-V1.
  None of their surfaces are touched in write mode.
- Clock: 2026-09-28T01:55:02Z = Sun 21:55 ET (FX week reopened 55 min
  ago at Sun 17:00 ET). EDT (US) / BST (UK) both still in force
  (transitions 2026-11-01 / 2026-10-25 — after this session).

## Registration status (disclosure)

**No cycle registered in `plans/CYCLE_REGISTRY.json` for this session** —
it is a bounded read-only reconnaissance under the owner's direct
instruction (authority order #1), the registry files are owner-dirty from
other live sessions, and this session has no scored surface, no GO phrase
and no budget to account. Precedent: standalone probe control dirs
(`xauusd_ibkr_probe_2026-09`, `broker_cost_probe_FX_majors_2026-09`).
Nothing here flips any lifecycle or ledger row.

## Lane structure (owner's split, scaled to workload)

| Lane | Who | Scope | Evidence root |
|---|---|---|---|
| L-FX (P1) | controller inline | IBKR TWS paper read-only probes + bounded sampling sessions + Saturday-verdict cross-check/erratum | `ibkr_fx/` |
| L-CX (P2) | subagent, packet `dispatch/PACKET_lane_cx.md` | Binance L2 collector (≤2 symbols), Deribit options sample, one bounded on-chain query | `cx/` |
| L-RATES (P3) | controller inline | CME reachability re-measure (SNI discrimination per L-FXFF-1), NY-Fed daily-official vs intraday distinction | `cme_rates/` |

Each lane ends with a `zcode_orch_v3_handoff@1` JSON at its declared
handoff path. `commit_sha` is null for all lanes this session (no-commit
session; changed paths disclosed per lane; owner reviews and commits).

## Inherited rulings this session does not re-litigate

- L-FXFF-1 / L-FIBV1-1: `*.cmegroup.com`, `*.dukascopy.com`,
  `www.sec.gov` estate SNI-filtered on the measured network path; never
  bypassed; a fresh canary re-measure is in scope (P3) with the SNI vs
  no-SNI discrimination recorded.
- Saturday verdict 2026-09-26 (`broker_cost_probe_FX_majors_2026-09/
  VERDICT_session2.md`): V1 PASS / V2 NOT_SUBSCRIBED / V3 cost components
  table. **Cross-check against market calendar + entitlements is an
  explicit P1 deliverable** — 2026-09-26 was a Saturday (FX closed Fri
  17:00 ET → Sun 17:00 ET); the owner's 2026-09-28T01:52Z observation
  (marketDataType 1 + valid two-sided quotes on 5 pairs incl USDJPY)
  contradicts the NOT_SUBSCRIBED classification. Erratum path (timestamped,
  history never edited): `ibkr_fx/ERRATUM_verdict_session2_*.md`.
- P3-A / FIXCERT no-rescue laws: evidence recorded here never reopens a
  killed family by itself; any reopener is an owner gate decision.
- Crypto: "Không suy ra order book hay forced flow từ nến" — L2 sampled
  from 2026-09-28 is PROSPECTIVE, never labeled historical.
