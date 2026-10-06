# SYMBOL_READINESS — FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (per-symbol ×10)

Lane REQUEST-PACKET · 2026-10-02. Status vocabulary:

- **READY_PREP** — prep-side work for this symbol is complete; the next
  concrete step for its vendor-gated hypotheses is Databento delivery
  (owner-gated purchase), and no OTHER known blocker precedes that step.
- **WAIT_DATA** — waiting on Databento delivery (or pilot), AND at least one
  additional gate follows before any backtest use.
- **OTHER_BLOCKER** — a non-Databento blocker sits FIRST in the chain (or is
  permanently outside the vendor's reach); data delivery alone cannot move
  the symbol to testable.

Discipline: rows do NOT attribute everything to the vendor. Every chain ends
at its TRUE blocker (usually an owner decision or an input class Databento
does not sell). "Databento does not provide": consensus archives, forecast
vintages, macro vintages, exchange fees for our account, our own slippage,
holiday calendars as a typed product, our broker fills (full list:
DATA_ACQUISITION_SPEC.md §8).

Common blockers AFTER data delivery (apply to ALL 10 rows; not repeated in
each): (1) declared slippage — NO declared value exists
(NOT_RUN_NO_DECLARED_VALUE; owner must declare explicit nonzero
USD/contract/side; BACKTEST_LAUNCH_DRAFT §4 — any Arm B pass/fail statement
is blocked until then); (2) exchange fees NOT_FETCHED 9/10 (only ES has a
documented all-in example 2.24; CME fee pages transport-blocked in prep);
(3) real exchange holiday calendar (engine `require_real_calendar`
hard-stop; holiday-vs-fetch-gap typing NOT_RUN); (4) registration — every
scored/backtest arm needs a future REGISTERED cycle with frozen trial
budget + owner GO; (5) IBKR-side serial re-fetch deadlines
(SERIAL_REFETCH_MANIFEST.md: 26 serials; time-critical set GCX5 now,
6JF6/6BF6/6AF6 ~Dec-2026; 6JV5/6JX5 likely already unresolvable) — $0, same
entitlement, independent of the vendor path; (6) IBKR corpus is RTH-only —
vendor closes overnight for vendor-covered windows, but IBKR-side
session-share history stays RTH until the useRTH=false re-pull.

| Symbol | Status | Databento lines | Vendor data solves | Non-vendor blockers that STILL gate (true end of chain) |
|---|---|---|---|---|
| **NQ** | WAIT_DATA (pilot first) | PILOT-01..06, EXP-01..05, EXP-06/07 | true-volume daily ≥5y (H1/H5), full-Globex M1 2019→ (H4), CoT-positioning depth via OI (H2 with free CFTC) | H3 consensus archive (NOT sold by vendor; commercial/scrape owner decision); H1 ALFRED vintages (free, unfetched); entry-delay realism needs M1 delivery first → chain ends at OWNER: pilot approval → spend → acceptance, then slippage + registration |
| **ES** | WAIT_DATA | EXP-01..05, EXP-06/07 (no pilot) | roll-timing micro depth (H1/H2), macro-release M1 2019→ (H3), gap/regime depth (H5) | H3 consensus archive (vendor-n/a); H2 dividend-yield series (index-provider/paid, PARAM-GAP until sourced); ES is the ONLY symbol with a documented all-in fee example ($2.24) — fee blocker partially cleared; slippage + registration remain |
| **CL** | WAIT_DATA (pilot first) | PILOT-01..06, EXP-01..05, EXP-06/07 | backwardation-regime breadth ≥5y (H1 contango regime unseen in 14m), 10:30 ET M1 event floors (H2/H3) | H2/H3 consensus archive (PARAM-GAP — surprise undefined without it; vendor-n/a); H3 needs RB/HO product data (not requested, not owned); EIA schedule verify-at-collection; chain ends at OWNER: pilot → spend → consensus decision → slippage + registration |
| **NG** | WAIT_DATA | EXP-01..05, EXP-06/07 | ~2.2y→≥5y intraday (H1 ≥100 EIA events), seasonal curve depth (H3/H4), storage-percentile regimes | weather FORECAST vintages (NOAA NDFD AWS from 2020-04-16 → only; pre-2020 effectively unreachable; H2/H4 bounded to that era); consensus archive (H1 X-Bcf threshold has no measured basis); EIA release-time verify-at-collection; chain ends at INPUT AVAILABILITY (vintages) + OWNER (consensus, spend, slippage, registration) |
| **GC** | OTHER_BLOCKER (serial deadline) + WAIT_DATA | EXP-01..05, EXP-07 | volume-crossover roll detail (H1), curve depth ≥2y real-volume (H3), ratio regimes (H4) | H2 consensus archive (vendor-n/a); time-critical $0 serial re-fetch: GCX5 AT the resolve edge now, GCF6..GCU6 age out ~Dec-2026→Sep-2027 (chain-baseline proof + serial-liquidity thesis); vendor definitions/daily can reconstruct serials later, but the $0 window closes first — chain ends at OWNER: serial re-fetch NOW (or explicit waiver), then spend, consensus, slippage, registration |
| **SI** | WAIT_DATA | EXP-01..05, EXP-07 | ≥10y two-leg daily for ratio reversion floors (H2, needs ~100 episodes), overnight/tail regimes with full session (H5), cycle-chain verification incl. serial books (H1) | identity trap SI vs SIL re-verify rides vendor definitions (pilot-equivalent check before SI bulk); single-regime squeeze sample (2026) — depth is the fix, but year-by-year stability gates remain; chain ends at OWNER: spend → acceptance → slippage + registration |
| **6E** | WAIT_DATA | EXP-01..05, EXP-06/07 | CIP-carry depth ≥8 quarters (H2 floor), FOMC in-window M1 2019→ (H3), serial-book verification (H1) | USD/EUR rate series (FRED, free, unfetched); H4+ event families 8:30 ET/ECB pre-window need Globex M1 (vendor solves) but consensus stays vendor-n/a; chain ends at OWNER: spend → rates pull → slippage + registration |
| **6J** | OTHER_BLOCKER (serial deadline + intervention lag) + WAIT_DATA | EXP-01..05, EXP-06/07 | overnight BoJ-session M1 2021→ (H2 entry timing), HMUZ chain depth (H1/H3), serial-book verification | MOF intervention amounts publish ~1 month late (H2 PIT condition; price-proxy variant testable without it); serials 6JV5/6JX5 LIKELY ALREADY unresolvable via IBKR (below measured FX frontier 202512) — vendor path is the only recovery for those two; chain ends at INPUT LAG (MOF) + OWNER (spend, slippage, registration) |
| **6B** | OTHER_BLOCKER (serial deadline) + WAIT_DATA | EXP-01..05, EXP-06/07 | volume-crossover roll depth ≥12 quarterly rolls (H1 floor; only 4 measured), BoE/UK event M1 (H2/H3) | ALL expired 6B serials never fetched (6BF6 frontier ~Dec-2026, then G6..Q6 through Jul-2027) — same $0 deadline logic as GC; H2 needs UK+US PIT consensus with timestamps (vendor-n/a) AND London-session coverage (vendor M1 solves); ONS vintages for UK data; chain ends at OWNER: serial re-fetch timing, consensus decision, spend, slippage, registration |
| **6A** | OTHER_BLOCKER (serial deadline + proxy input) + WAIT_DATA | EXP-01..05, EXP-06/07 | hidden-session RBA reaction M1 2021→ (H1 entry realism), quarterly-chain depth (H2) | serials 6AF6/6AG6 age out ~Dec-2026/Jan-2027 (dossier: Jan–Mar 2027) — $0 window; H1 surprise classification needs 5-min AUD/USD spot or Globex M1 at 22:30 CT (PARAM-GAP — not owned; vendor M1 partially covers, classification basis must be declared); H2 needs HG copper + iron-ore proxy (HG NOT in this vendor request — separate free/vendor input, owner decision); chain ends at INPUT (proxies) + OWNER (serial re-fetch, spend, slippage, registration) |

## Row-by-row gating chains (first blocking item → true blocker)

- **NQ / CL**: pilot acceptance → per-line spend → EXP depth → (H3-class)
  consensus archive decision → declared slippage → registration → owner GO.
  True blocker today: OWNER pilot/spend decision; later: consensus +
  slippage + registration (never "vendor lacks data").
- **ES**: spend → depth → H2 dividend-yield source → slippage →
  registration. (ES is the only symbol whose all-in fee example exists.)
- **NG**: spend → depth + ≥100 events → weather vintages (bounded
  2020-04-16→) + consensus → slippage → registration. Even perfect vendor
  data leaves H2/H4 vintage-bounded and H1 consensus-gated.
- **GC / 6B / 6A / 6J**: $0 serial re-fetch deadline FIRST (evidence window
  closing Dec-2026→2027; 6J already lost 2 serials probably) → then the same
  vendor chain. Choosing vendor-only is legitimate (vendor history has the
  serials) but must be an explicit owner decision, not drift.
- **SI**: identity re-verification (SI 5000oz class via vendor definitions)
  before SI bulk; then depth; single-episode regime risk remains a validity
  gate no data purchase removes.
- **6E / 6J / 6B / 6A (FX class)**: rate/vintage series (free, unfetched) +
  intervention/consensus inputs (vendor-n/a) sit BESIDE the vendor path,
  not behind it.

## What is NOT a Databento matter (never was)

Declared slippage; exchange fees for our account (9/10 NOT_FETCHED);
holiday calendar source; consensus/expectations archives; NG weather
vintages; macro vintages (ALFRED); CFTC CoT release discipline (public,
free); MOF intervention lag; HG copper / iron-ore proxies; broker paper/live
fill audit trail (the only true slippage measurement); registration + owner
GO for anything scored. Full list with URLs: DATA_ACQUISITION_SPEC.md §8.

Evidence: dossiers §5/§6 per symbol; BACKTEST_LAUNCH_DRAFT §4/§6/§9;
INTEGRATION_SUMMARY §1–§3; SERIAL_REFETCH_MANIFEST.md §1 (age-out
frontier); COVERAGE_MANIFEST.json (measured walls). Status date 2026-10-02;
re-measure before relying on any row.
