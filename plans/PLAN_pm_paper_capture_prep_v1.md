# PLAN — PM-PAPER-CAPTURE-PREP-V1 (Polymarket prospective paper-capture prep: NBA first, Weather gated; budget 0/0)

- cycle_id: `PM-PAPER-CAPTURE-PREP-V1` · asset: shared · **budget 0 scored
  cells by law (0/0)** · **NO go_phrase by design**. This cycle is **price
  evidence collection prep** — it is NOT a scored GO, not paper PnL, not
  trading, not EV computation, not selection from outcomes.
- Owner instruction 2026-10-17 (round 2, this chat): open the successor PREP
  from `OPPORTUNITY-CENSUS-V1` (TERMINAL-quality closeout
  READY_FOR_OWNER_REVIEW at e15e0c68, registry 8331a5e6): build the
  prospective paper-capture flow for **NBA moneyline @ Polymarket first**,
  **Weather @ Polymarket only if it passes its own separate gate**.
- Owner decisions LOCKED this round (bind, do not relitigate):
  1. Kalshi stays **HOLD entitlement** (unchanged).
  2. No WNBA odds purchase (The Odds API historical stays unfunded).
  3. WSL is the shortlist alternate — **not** added to any collector.
  4. Weather GFS B1/B2 did NOT beat B0 in WEATHER-TEMP-PROB-V1 — weather is
     never presented as existing edge; the weather lane's value here is
     market-infrastructure evidence only.
  5. This instruction is **not** a scored GO.

## 0. Hard fences

- No new model fits, no signal trials, no scored cells, no S1, no
  credentials/signup, no purchases, no orders (real or paper), no push/merge,
  no history rewrite, no `git add -A`, no writes to other cycles' surfaces
  (`WEATHER-TEMP-PROB-V1` 6/6 stays consumed and read-only).
- Closing prices are never a decision-time price. No EV/PnL/selection is
  computed from captured quotes. No outcome data is joined during this PREP
  (anchors are frozen BEFORE any outcome data exists on disk; in practice:
  this PREP reads no outcome rows at all).
- Bounded network: all live reads are journaled public no-auth GETs with a
  per-run cap (≤40 GETs per probe run; collector runs have their own caps in
  `COLLECTOR_SPEC.md`). One retry max on transport errors; 429/403 ⇒ stop
  that source for the run and record.

## 1. Gate R — data rights (FIRST; failure stops dependents)

Byte-read the official Terms the owner identified:
`https://polymarket.com/tos` → the page embeds the authoritative Google Doc
(`docs.google.com/document/d/1N4aYlRcqaWCeKMID7vUSWJ1UPMvw_v6SP4cOFN8ZxR4`),
"POLYMARKET.COM TERMS OF USE, Effective as of August 11, 2026" (59,187 bytes
text export retrieved 2026-10-17, sha256 pinned in `RIGHTS_LEDGER.md`).
Load-bearing verbatim clauses (full quotes in RIGHTS_LEDGER.md):

- §5.1: license is "personal, limited, revocable, non-exclusive,
  non-sublicensable, non-transferable license to use, copy, and distribute in
  connection with such use … solely intended to allow you to access, use or
  otherwise interact with the Site, any other Interface, and Features."
- §4.2 prohibits "data mining tools, robots, crawlers, or similar data
  gathering and extraction tools to scrape or otherwise remove data from the
  Site, any other Interface, or Features"; "manual process to monitor or copy
  … without our prior written consent"; harvesting "for any unauthorized
  purpose"; and access/use of the "Data … directly or through an API …
  whether in raw, derived, aggregated, or anonymized form" by **Capital
  Market Clients** (professional capital-markets entities incl. proprietary
  trading) "unless otherwise agreed to in writing by us".
- API docs state "Public market data is available without credentials" but
  carry **no** data-use/license terms — API docs do not self-prove warehouse
  rights (owner's rule).

**Ruling (mechanical from the clauses):** small journaled read-only probes
(pin contracts, book spot-checks) are licensed *access/use/interaction* under
§5.1. **A standing/periodic snapshot collector cannot be concluded authorized
within scope**: the §5.1 license does not reach a data-collection program,
the §4.2 robots/crawlers clause plausibly covers scheduled extraction, and
the Capital-Market-Client Data restriction makes professional-use storage a
written-agreement matter that only the owner can resolve.
⇒ `rights_verdict(collector) = HOLD_PENDING_ENTITLEMENT`; the collector is
BUILT and synthetic-tested but **NOT live-activated** by this cycle. The
entitlement path is owner-level: written agreement from Polymarket, an
official data license, or the owner's documented legal determination that the
user is outside the restricted categories AND accepts the scraping-clause
risk. Probe-level work proceeds (steps 2–3) as ordered.

## 2. Step P — pin contracts (journaled probes)

Per market, byte-pinned into `CONTRACT_PIN_LEDGER.md` + `contract_pins/`:
NBA game events (≥6 upcoming + all currently-open game events visible within
probe cap): Gamma event id/slug, market ids, `clobTokenIds` (outcome tokens),
outcome names, verbatim resolution/description text (win rules), open/close
times, fee reference (sports taker 0.05·p·(1−p) carried; pin the per-market
`feeRateBps` fields verbatim if present). Weather daily high/low events for
NYC/Chicago/Miami: pin per-event resolution text verbatim — station/observable,
resolution source, timezone/day boundary, bucket structure, fee fields —
from Polymarket's OWN bytes. **Kalshi labels are NEVER mapped onto
Polymarket by city name**; the Kalshi comparison (station CLINYC/MDW/MIA,
civil-day law, settlement era split) is cited only from the already-pinned
weather-prep artifacts as a *difference checklist*.

## 3. Step M — matchability measurement (S4 recompute)

For a sample of pinned markets: one CLOB book snapshot each (bid/ask levels
with sizes + venue timestamp) at expected decision anchors. Anchors are
FROZEN in `ANCHORS_FREEZE.md` before any outcome data could exist: NBA =
T0−6h10m (inherited league law), Weather = D−0 00:00Z contract-day boundary.
Recompute rubric S4 (spread+fee drag band) for CAND-NBA-PM and
CAND-WEATHER-PM from measured spread at anchor + carried fee law. Empty
book, stale timestamp, or spread beyond the frozen band ⇒
`NOT_RUN_EXECUTABLE_QUOTE` for that market and the S4 verdict is lowered per
the census rubric — never guessed.

## 4. Step C — collector (built, NOT activated)

`tools/pm_capture_collector.py` per `COLLECTOR_SPEC.md`: read-only, no-auth,
idempotent (event-scoped state; a re-run never duplicates a snapshot), emits
`opportunity_census@1` rows (SCHEMA inherited verbatim from the census:
one event = one independent opportunity), stores raw append-only snapshot +
received_at + venue quote timestamp + bid/ask/size + fee/rules_version +
sha256 + QC codes; rate limit ≤1 req/s and per-run GET caps; bounded retries;
`gap_ledger.csv` for missed windows; stop-file mechanism
(`STOP` file present ⇒ collector refuses to run); **no closing-price
substitution** — a window without a live pre-anchor quote is
`MISSING_NO_PRE_ANCHOR_QUOTE`, never backfilled with close.

## 5. Step V — synthetic dry-run + independent verifier

Synthetic-mode dry-run (zero network) proves idempotency, dedup, gap ledger,
stop-file, and schema emission on injected fixtures. Independent
fresh-context verifier re-derives: pins match pinned bytes; probe journal
monotonic + capped; anchor freeze precedes probe artifacts; S4 bands
recomputed; collector idempotency + QC codes on synthetic replay; manifest
hashes. Exit codes 0/2/3/4 as in the census.

## 6. Activation status law (deliverable)

Per market, exactly one of: `ACTIVATED_READ_ONLY` (requires gates R+P+M+V
ALL PASS) · `HOLD_PENDING_ENTITLEMENT` (gate R unmet — collector suppressed)
· `NOT_RUN_<reason>`. Given the Gate R ruling, NBA and Weather both land
`HOLD_PENDING_ENTITLEMENT` with everything else proven as far as probes
allow. Overall verdict must be one of `CAPTURE_ACTIVE_READ_ONLY` /
`READY_FOR_OWNER_REVIEW` / `HOLD:<reason>` — expected: `HOLD` on gate R,
with the written-agreement path documented for the owner.

## 7. Deliverables

`RIGHTS_LEDGER.md` (verbatim clause quotes + sha256 of the ToS text + API
docs quote) · `CONTRACT_PIN_LEDGER.md` + `contract_pins/` · `ANCHORS_FREEZE.md`
· `SPREAD_DEPTH_PROBES.md` + probe journal · recompute of S4 ·
`COLLECTOR_SPEC.md` + `tools/pm_capture_collector.py` + synthetic fixtures ·
`verify_capture_prep.py` + `VERIFY_RECORD.json` · `MANIFEST.json` ·
`CAPTURE_PREP_CLOSEOUT.md` · `handoff.json` (`zcode_orch_v3_handoff@1`).
Registry updated via researchctl only. HARD STOP before any activation,
purchase, credential, order, or push.
