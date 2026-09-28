# ERRATUM — VERDICT_session2.md (2026-09-26), issued 2026-09-28T02:15Z

Session: DATA-FOUNDATION-SIXSOURCE-V1 lane L-FX (owner directive
2026-09-28). This erratum CORRECTS the factual record per the owner's
instruction ("nếu bằng chứng đổi kết luận, lập erratum có timestamp thay
vì sửa lịch sử"). `VERDICT_session2.md` is NOT edited; it remains the
verdict of its time. No family verdict is reopened by this document.

## E1 — V2 classification "NOT_SUBSCRIBED (SIM account lacks market data)" is CORRECTED to "subscribed-and-live; Saturday window was market closure"

- The 2026-09-26 measurement window was 05:47–05:53 UTC = **01:47–01:53 ET
  Saturday** — deep inside the FX weekend closure (Fri 17:00 ET
  2026-09-25 → Sun 17:00 ET 2026-09-27). BID/ASK = −1 (UNSET) with only
  single-sided indicative tick-type-9 values is the expected signature of
  a CLOSED IDEALPRO book, not of a missing entitlement.
- The same verdict already recorded "marketDataType=1 (LIVE) announced
  for all 5 subscriptions, zero subscription errors" — i.e. the
  subscription machinery never rejected anything.
- Independent re-measurement 2026-09-28T02:03:35–02:08:38Z (52 min–5 h
  after the Sunday 17:00 ET reopen), raw-ibapi read-only whitelist probe
  (no placeOrder/cancelOrder/whatIf in file by construction):
  - `marketDataType=1` served on all 5 pairs (EURUSD/GBPUSD/AUDUSD/
    USDCAD/USDJPY), zero subscription errors (354/10089/10090/4200 all
    absent).
  - **Two-sided tickByTickBidAsk streams valid on all 5 pairs**:
    1,665 / 1,982 / 1,688 / 1,373 / 1,776 valid observations
    (ask≥bid>0) in ~5 minutes, with server-side timestamps and sizes.
  - Spread (pips, paper session, thin Sunday-evening ET book):
    EURUSD p50 0.1 / p90 0.2; GBPUSD 0.4 / 0.5; AUDUSD 0.1 / 0.2;
    USDCAD 0.6 / 0.6; USDJPY 0.4 / 0.6. Max 0.3–0.8.
  - Evidence: `research/control/DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/
    sanitized_s0_verify_20260928T020329Z.json`; raw ndjson sha256
    `789e7e45318a86a2…` (1,990,131 bytes) at
    `~/.my-quantitative-data/sixsource-foundation-v1/ibkr_fx/`.
- Consequence for the verdict's owner-action list: item 1 ("enable FX
  delayed via Manage Data Subscriptions … then rerun") is **already
  satisfied by the current session state** — two-sided LIVE-flagged data
  flows without any TWS-side change. The exact subscription line-item
  is not readable through the read-only whitelist; what is measured is
  that data flows, flagged LIVE (mdt=1), with no error.

## E2 — the P3-A premise "minTick = 0.5 pip ⇒ minimum positive spread ≥ 0.5 pip" is contradicted by the observable stream

- `contractDetails` STILL declares minTick = 5e-05 (0.5 pip) on the four
  4-decimal pairs and 0.005 on USDJPY — the Saturday reading was not a
  data error; secdef declares 0.5 pip.
- The live quote stream, however, steps in 1e-05 increments: e.g.
  EURUSD bid 1.13888 / ask 1.13889 (0.1 pip), and the measured
  distribution contains 0.1-pip spreads on all five pairs with
  1,373–1,982 valid observations each.
- Therefore "the minimum positive spread at this venue is 0.5 pip ⇒
  base crossing ≥ 0.5 pip ⇒ ×2.0 ≥ 1.0 pip = 2.4× threshold" is FALSE as
  a statement about the observable spread distribution. The declared
  minTick may still govern ORDER PRICE increments (untestable here —
  placing orders is forbidden), but the cost-band arithmetic in V3/P3-A
  can no longer rest on the 0.5-pip floor premise.
- **Standing law honored**: P3-A's F0/dead-at-this-venue verdict is NOT
  reopened by this erratum (no-rescue law; reopening conditions are an
  owner gate decision per FAMILY_FAILURES). This document only corrects
  the factual record so any future reopener decision is made on measured
  truth.

## What this erratum does NOT change

- V1 (connectivity PASS) — unchanged, re-confirmed.
- V3 cost components 2–7 (commission, swap L/S, triple-swap, rollover
  clock, min size): still NOT_RUN — they need an Activity/Flex statement
  containing FX trades + overnight FX positions. No statement has been
  provided; **no trades were created to sample** (explicitly forbidden).
- Component 8 (tick): the Saturday VALUE (minTick 0.5 pip from secdef)
  stands as a secdef declaration; the new measured fact (stream
  granularity 0.1 pip) is added alongside it.
- Component 9 (margin, whatIf-forbidden) and 10 (stress 2.0 frozen) —
  unchanged.
- All sealed/holdout surfaces, ledger rows, registry states — untouched.

## Owner document still required (unchanged from the verdict's list)

Activity Statement or Flex Query (any window containing FX trades +
overnight FX positions) placed at `~/.my-quantitative-data/ibkr_statement/`
— never into chat/git. That unblocks components 2–7. Spread two-sided
(component 1) is now MEASURED-streaming; its distribution continues in
the SIXSOURCE bounded sessions (fix window 2026-09-28 15:00 UTC,
rollover window 21:00 UTC, both scheduled read-only).
