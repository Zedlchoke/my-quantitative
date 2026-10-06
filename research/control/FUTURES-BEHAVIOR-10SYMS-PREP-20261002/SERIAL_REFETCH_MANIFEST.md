# SERIAL_REFETCH_MANIFEST — FUTURES-BEHAVIOR-10SYMS-PREP-20261002

- Written: 2026-10-02, round **co-owner-review-fix-1**, lane **HANDOFF-RESEARCH**.
- **THIS MANIFEST IS PREPARATION ONLY. No downloads, no resolves, no API
  calls of any kind happen from this lane.** It is a bounded, $0, same-
  entitlement work order for the OWNER (or a future data lane) to execute or
  decline. Nothing here self-grants data acquisition beyond the existing
  IBKR entitlement, and nothing here touches vendor purchases (those stay
  owner-gated per DATA_ACQUISITION_SPEC.md).
- Evidence base: per-symbol dossiers §1/§6 (GC, 6J, 6B, 6A),
  research/control/FUTURES-DATA-10SYMS-V1/S1_IDENTITY.json (read-only; its
  measured `deepest_resolved` per symbol is the empirical resolve-wall
  frontier as of 2026-10-02), and the raw corpus file-size census
  (~/.my-quantitative-data/futures-10syms-v1/raw/, 1160 files, read-only).

## 0. Why (measured defects this would close)

The data lane's declared roll rule ("roll to the next listed contract at the
last session before day-1 of the expiry month") requires SERIAL (non-cycle)
months that were never fetched. Dossiers measured the literal rule
**NOT executable** on this snapshot for: GC 2025-11…2026-09 (6 serials), 6J
2025-09…2026-08 (8 serials), 6B 2026-01…2026-08 (all expired serials), 6A
2026-01…2026-08 (6 serials). All chain statistics for those spans use
disclosed quarterly/cycle-skip adaptations. The re-fetch would make the
literal-rule chain reconstructable AND would measure whether those serial
books were ever liquid (the FX/serial dead-book thesis is currently inferred
from the two near serials 6EV6/6AX6 + 2027-28 active serials only).

## 1. Per-contract work order (26 contracts, 5 job types each)

Job types per contract (identical to the existing corpus pattern):
`TRADES_1day_6Y`, `TRADES_1hour_30D`, `TRADES_1min_2D`, `BID_1day_1Y`,
`ASK_1day_1Y`. **Proposed window for every contract = its FULL LISTED LIFE
up to its own roll boundary** (endDateTime = last session before day-1 of
its LAST-TRADE month, canonical basis per audit M2 — the same cut convention
the corpus already uses). The critical span for chain reconstruction is each
serial's turn as "next listed" target: from the prior quarterly's roll date
to its own boundary; requesting full life is simpler, smaller, and also
captures listing-to-boundary for liquidity verification.

`conId`: **NOT_IN_SNAPSHOT for all 26** — verified against S1_IDENTITY.json
(active_chain + expired_walk: none of these localSymbols were ever
resolved). Resolution must re-derive conId from (tradingClass, localSymbol)
via reqContractDetails at execution time. localSymbols below are the
sufficient IBKR keys.

| # | Symbol | localSymbol | Delivery month | Est. LTD (rule) | Est. LTD month | Resolve status est. (2026-10-02) | Est. IBKR age-out |
|---|--------|-------------|----------------|-----------------|----------------|-----------------------------------|-------------------|
| 1 | GC | GCX5 | Nov-2025 | 3rd-last bday of month prior (GC rule) | 2025-10 | AT EDGE — equals GC deepest_resolved=202510 | ~now (weeks at best) |
| 2 | GC | GCF6 | Jan-2026 | " | 2025-12 | inside wall (>202510) | ~Dec-2026/Jan-2027 |
| 3 | GC | GCH6 | Mar-2026 | " | 2026-02 | inside | ~Feb/Mar-2027 |
| 4 | GC | GCK6 | May-2026 | " | 2026-04 | inside | ~Apr/May-2027 |
| 5 | GC | GCN6 | Jul-2026 | " | 2026-06 | inside | ~Jun/Jul-2027 |
| 6 | GC | GCU6 | Sep-2026 | " | 2026-08 | inside | ~Aug/Sep-2027 |
| 7 | 6J | 6JV5 | Oct-2025 | 2nd exch. bday before 3rd Wed of month prior (IMM) | 2025-09 | **BELOW the FX frontier (deepest_resolved=202512) — likely already unresolvable** | likely past |
| 8 | 6J | 6JX5 | Nov-2025 | " | 2025-10 | **BELOW frontier — likely unresolvable** | likely past/weeks |
| 9 | 6J | 6JF6 | Jan-2026 | " | 2025-12 | AT frontier (=202512) | ~Dec-2026 — attempt FIRST |
| 10 | 6J | 6JG6 | Feb-2026 | " | 2026-01 | inside | ~Jan-2027 |
| 11 | 6J | 6JJ6 | Apr-2026 | " | 2026-03 | inside | ~Mar-2027 |
| 12 | 6J | 6JK6 | May-2026 | " | 2026-04 | inside | ~Apr-2027 |
| 13 | 6J | 6JN6 | Jul-2026 | " | 2026-06 | inside | ~Jun-2027 |
| 14 | 6J | 6JQ6 | Aug-2026 | " | 2026-07 | inside | ~Jul-2027 |
| 15 | 6B | 6BF6 | Jan-2026 | " | 2025-12 | AT frontier (=202512) | ~Dec-2026 — attempt FIRST |
| 16 | 6B | 6BG6 | Feb-2026 | " | 2026-01 | inside | ~Jan-2027 |
| 17 | 6B | 6BJ6 | Apr-2026 | " | 2026-03 | inside | ~Mar-2027 |
| 18 | 6B | 6BK6 | May-2026 | " | 2026-04 | inside | ~Apr-2027 |
| 19 | 6B | 6BN6 | Jul-2026 | " | 2026-06 | inside | ~Jun-2027 |
| 20 | 6B | 6BQ6 | Aug-2026 | " | 2026-07 | inside | ~Jul-2027 |
| 21 | 6A | 6AF6 | Jan-2026 | " | 2025-12 | AT frontier (=202512) | ~Dec-2026/Jan-2027 |
| 22 | 6A | 6AG6 | Feb-2026 | " | 2026-01 | inside | ~Jan-2027 (6A dossier: "Jan–Mar 2027") |
| 23 | 6A | 6AJ6 | Apr-2026 | " | 2026-03 | inside | ~Mar-2027 |
| 24 | 6A | 6AK6 | May-2026 | " | 2026-04 | inside | ~Apr-2027 |
| 25 | 6A | 6AN6 | Jul-2026 | " | 2026-06 | inside | ~Jun-2027 |
| 26 | 6A | 6AQ6 | Aug-2026 | " | 2026-07 | inside | ~Jul-2027 |

LTD estimates are computed from the exchange rules measured in the dossiers
(GC: 3rd-last business day of the prior month; FX IMM: 2nd exchange business
day before the 3rd Wednesday, holiday-shifted 20/20 in 6E/6B/6A checks);
exact dates come free from the resolve itself — do not act on the estimates.

### Age-out deadline reasoning (measured, not assumed)

IBKR's expired-contract resolve/venue window is ~1 year ("expired-secdef
wall"). Empirical frontier TODAY (S1 deepest_resolved): GC = 202510,
6J/6B/6A = 202512 (last-trade months successfully resolved in the data
lane's expired walk). Consequences:

1. **6JV5 and 6JX5 sit below the FX frontier** (LTD months 2025-09/2025-10)
   — they are most likely ALREADY unresolvable via IBKR. The 6J dossier
   itself judged the 8 serials "unrecoverable via IB"; the 6A dossier judged
   its 6 "still inside" — both were directionally right for their own sets;
   the frontier measurement reconciles them: 6J's two oldest are (probably)
   gone, everything from 6JF6/F6-class onward is recoverable NOW.
2. **GCX5 and the F6-class (6JF6/6BF6/6AF6, LTD month 2025-12) are the
   time-critical set**: GCX5 is at the measured GC frontier this month;
   the F6-class hits the FX frontier around Dec-2026. The
   INTEGRATION_SUMMARY §3.1 phrase "~Q1-2027 for the oldest" is correct for
   the G6/H6 bulk but OPTIMISTIC for these — flagging here rather than
   editing another lane's text.
3. Recommended probe order (all $0): resolve #1, #7, #8 first (edge/likely-
   lost — establishes the true frontier), then the F6-class, then the rest.
   A failed resolve is itself recorded evidence (NOT_RESOLVABLE + date).

## 2. Pace, storage, expected coverage (estimates from the measured corpus)

- **Requests**: 26 secdef resolves + 26 × 5 data jobs = 156 requests.
  IBKR pacing guideline ≈ 60 hist-data requests / 10 min → ≈ 3 pacing
  windows ≈ **20–40 minutes** for one bounded session. Resolve-first, then
  fetch only the resolvable set.
- **Storage** (corpus means per job: 1day ~57KB, 1hour ~15KB, 1min ~52KB,
  BID ~14.5KB, ASK ~14.5KB → ~153KB/contract): **≤ ~4.0 MB** for all 26
  (serials' short listed lives make this an upper bound; daily-jobs-only
  fallback ≈ 0.9 MB). Total corpus would grow 36.5 → ~40 MB.
- **Expected coverage**: literal declared-rule chain reconstruction for GC
  2025-09→2026-09, 6J 2025-12→2026-08 (2025-09..11 if #7/#8 resolve),
  6B/6A 2025-12→2026-08; per-serial liquidity verification (dead-book
  thesis); roll-boundary gap measurement on the serial legs. It does NOT
  add pre-2025 true volume, OI, or any session the entitlement never
  recorded.
- **Expected failure modes**: error-162 empty files for jobs outside the
  entitlement's recorded window (tolerated class in the adapter); resolve
  failures for the below-frontier set (record as NOT_RESOLVABLE).

## 3. Separate bounded option — useRTH=false overnight re-pull ($0)

The entire corpus is useRTH=true (RTH 08:30–16:00 CT only): overnight/
Globex, Asia and London sessions are NOT_RUN for every symbol, and BoJ/ECB/
RBA/AU/China event windows are invisible (dossier tz maps). A bounded
overnight re-pull on the SAME entitlement (flagged cheapest-fix by the NQ
dossier and INTEGRATION_SUMMARY §3.2):

- **Scope v1 (bounded)**: 10 symbols × current front + next contracts
  (20 contracts) × {`TRADES_1day_6Y` useRTH=false, `TRADES_1hour_30D`
  useRTH=false} = **40 requests ≈ 1 pacing window**. Optional +10 ×
  `TRADES_1min_2D` useRTH=false for the fronts.
- **Expected depth (honest)**: overnight bars will be real only where/when
  the entitlement actually recorded them — expect ~10–14 months of usable
  overnight on fronts (NG ~2.2y), NOT deep history. This unlocks
  session-share statistics, hidden-session decomposition and event-window
  feasibility checks; it does NOT unblock DAILY_BT (still ~14-month
  true-volume) and is NOT a substitute for vendor history.
- **Not included (owner-gated)**: any vendor purchase, any new account.

## 4. Vendor-path statement (why IBKR wall ≠ dead end)

**Losing IBKR resolve on a contract does NOT mean losing the data class.**
The Databento GLBX.MDP3 path in DATA_ACQUISITION_SPEC.md is unaffected:
catalog availability from 2010-06-06 (verbatim caveat "Historical data
availability could vary between schemas" — Phase-0 FREE per-symbol/schema
probes are mandatory before any spend), definition schema carries the
contract universe with activation/expiration, and historical data requires
no license. The 26 serials above exist in vendor history regardless of
IBKR's resolve wall; NOT_SOLVED_BY_VENDOR items (consensus archives, broker
slippage, weather vintages) are unchanged by this manifest. Sequence
recommendation: run the $0 IBKR probe first; whatever fails the wall goes
onto the vendor Phase-0/Phase-1 request list as a tiny add-on (26 contracts
× daily ohlcv-1s/1m is negligible next to the 10-root bulk ask).

## 5. Execution guardrails for whoever runs it

1. No purchases, no new accounts, no credentials in logs.
2. Raw data dir is read-only for research lanes; a re-fetch writes NEW files
   under the existing naming convention into a NEW dated snapshot dir (or
   the owner's designated collector path) — never in-place edits.
3. Record per contract: resolve result, conId, exact LTD, per-job bar counts,
   error classes; declare failures NOT_RESOLVABLE/NOT_FETCHED — never
   inferred.
4. One heavy-job machine-wide lock only if the fetch job qualifies as heavy
   (it does not — bounded 156 requests).
5. Update the coverage manifest + affected dossiers' §1 executability
   statements after the fetch (out of scope here).
