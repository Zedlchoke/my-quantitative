# PROPOSAL DTP-CX-SOLUSDT-I001 — OUTCOME-BLIND ANNOTATED PLAYBOOK CORPUS

- Lane: `p1` · Role: `blind-proposer` (playbook collector/definer) · Date: 2026-09-27 (UTC)
- Cycle: `DTP-CX-SOLUSDT-C1` · Parent program: `DAYTRADE-PLAYBOOKS-PROGRAM-V1`
- Measured worktree HEAD at proposal time: `9ba72e6cd2b28a039791cc6a6f75e8ac10ef1cb2`
  (branch `orca/dtp-cx-solusdt-c1-integration`). No commit made (lane writes only;
  commit_sha null by dispatch).
- Outcome-blind lane. Diet: master plan §2.2/§4/§6.1, child plan §3, frozen
  `PLAYBOOK_TAXONOMY.md`, ERP umbrella §5.3, `FAMILY_FAILURES.jsonl` dead-class labels,
  taxonomy collision table. No outcome surface, no PnL, no sealed/holdout file was
  sought or read. WebSearch was used ONLY to establish that dated public playbook
  sources EXIST (existence check; no outcome statistics collected).
- Taxonomy route: **row 13 — METHOD (discretionary annotated playbooks)**, authorized
  by master §4.3. This proposal operationalizes row 13 for pair SOLUSDT.

> **Chưa có PnL nào được xem hoặc tính toán cho identity này.**

## 0. What this identity IS and IS NOT (read first)

**I001 is a GENERATOR of candidate rules, not itself a scored identity.** The scored
surface of this program is, at most, individual RULEs codified from the annotation
corpus that individually survive F-0 — and they enter trial freeze only within the
≤3-identity-per-pair cap (master §6.2). If zero rules survive F-0, the cycle closes
with a **measured** collision verdict (`NO_ELIGIBLE_PROPOSAL` / per-rule
`F0_KILLED`), which is a first-class product (master §1.1, Q-16). Honest prior:
the taxonomy collision table (Bảng 1, rows 1–11) pre-judges essentially every
well-known retail intraday skeleton as DEAD or BLOCKED; **we expect the large
majority of codified rules to die at F-0 by collision, and measuring that death
rate — replacing rumor with measurement — is the primary deliverable of I001.**

The corpus build itself is **post-freeze, pre-GO-2**, executed only under the frozen
protocol below. Nothing in this proposal collects the corpus now.

## 1. Annotation PROTOCOL spec (frozen before any corpus byte exists)

### 1.1 Source-selection criteria (all must hold; checked per entry)

1. **Public** — openly accessible without membership: no paid signal groups, no
   private Discords/Telegram channels, no DMs.
2. **Dated** — the platform records a publication timestamp (video upload date,
   post publish/edit date, article publish/updated date). An entry whose publication
   date cannot be established from platform metadata is **inadmissible**.
3. **Geometry-stated** — the source names a setup with at least: trigger condition,
   direction, entry location, invalidation/stop, and target or exit condition.
   Entries missing any element are retained in the manifest as `UNCODIFIABLE` and
   excluded from codification.
4. **Instrument-scoped** — setup is intraday on SOL, or on BTC/ETH/alt-crypto with
   an explicit transfer note recorded (transfer to SOL is then itself part of the
   codified rule and is disclosed in every artifact referencing it). Stocks-only
   playbooks are out of scope for CX.
5. **Author-independence cap** — at most K entries per author/channel (K frozen at
   protocol freeze; default K=5) so no single voice dominates the frequency ranking.
6. **Pre-decision-point rule** — the entry's annotation decision point is the
   platform-recorded publication timestamp; only sources published BEFORE any
   in-window setup's decision point are admissible for that window (see 1.4).

### 1.2 Entry record (manifest schema, per entry; corpus manifest is a §11 master artifact)

`{entry_id, source_name, source_class, url, publication_timestamp (platform-recorded),
retrieved_timestamp, author/channel, instruments_referenced, setup_verbatim_quote,
annotator_id, codified_rule_id | UNCODIFIABLE(reason), taxonomy_row_guess,
blind_checklist_signed}` — `publication_timestamp` is the `available_at` of the
hypothesis (handbook §13 event/effective/available/retrieved separated);
`retrieved_timestamp` = corpus-build date.

### 1.3 Annotator data-window rule — outcome-blind by construction

The annotator works on data **truncated at the entry's decision point**: the panel
loaded into the annotator workspace ends at the publication timestamp; no bar after
it exists in the workspace (byte-level panel truncation, sha of the truncated panel
recorded in the manifest). The annotator codifies the setup's trigger/entry/stop/
exit geometry against truncated bars only.

### 1.4 Prohibition list (explicit; violation = entry invalid + incident record)

- **No outcome-known chart redraws.** Never open a chart that displays
  post-publication data for the annotated setup; never "improve" an entry to look
  better with knowledge of what followed (master §1.2 hard law).
- **No hindsight entries.** Ex-post trade recaps ("how I caught this trade", P&L
  screenshots, result narrations) are outcome-contaminated and are NEVER admissible
  as setup entries. Only pre-entry setup descriptions are.
- **No sources published after the annotation window for in-window setups.** A 2024
  video describing "the SOL setup that worked in 2021" cannot annotate a 2021
  window.
- **No paraphrase-sharpening.** The annotation records the source's stated geometry
  verbatim; the annotator may not add levels, filters, or confirmations the source
  did not state.
- **No outcome statistics as evidence.** Author-claimed win rates / R multiples are
  recorded as claims in a dedicated claim field, never used as premium evidence.
- **No peeking at reserved OOS.** The annotation window excludes any window whose
  membership is (or will be) sha-frozen as sealed/prospective OOS (master §8).

### 1.5 Codification pipeline

1. Corpus assembly under this frozen protocol (post-freeze, pre-GO-2).
2. Setups classified against frozen taxonomy rows (Bảng 1) by the collector;
   **frequency = count of independent documented setups per class across distinct
   authors** (author cap 1.1-5 applies).
3. **Top-N setup classes by documented frequency become RULEs** (N frozen at
   protocol freeze; default N ≤ 10, subordinated to the freeze cap in step 5).
4. Each RULE gets a **closed-bar constructible definition per master §4.2**: level/
   state from closed bars only; pivot/level confirm ≥1 bar; earliest order at the
   first tradable quote after the signal bar closes, filled at the opposite-side
   quote; same-bar high/low ordering prohibited (`NOT_CONSTRUCTIBLE_INTRABAR` if
   impossible); flat-by rule frozen; PIT joins with real `available_at`; news-touch
   rules additionally require a PIT-authoritative event calendar (missing ⇒
   `BLOCKED_DATA`, no proxy).
5. **Each RULE individually enters F-0** (skeptic VETO, SRLV §2.3 three tests). A
   RULE becomes an identity candidate only after passing F-0; if more than 3 RULEs
   survive, the council selects ≤3 by a criterion declared before any outcome
   exists: maximal distinctness across (a) payer/mechanism, (b) PIT information
   layer, (c) risk shape (anti-variant law §2.3 two-of-three rule applies between
   any pair of selected RULEs — RULEs differing by less are merged, not scored
   twice).

## 2. Source existence — evidence from 2026-09-27 WebSearch existence checks

Existence-only searches (no outcome statistics collected) establish at least five
concrete source classes with platform-recorded dates:

1. **CryptoCred — Technical Analysis lesson series (YouTube).** Dated video lessons
   on candlestick structure, risk management, order flow, horizontal S/R, and a
   "Daily Open Trade Strategy"; series published 2019–2021 (upload dates carried by
   channel metadata). https://www.youtube.com/@CryptoCred (lesson list mirrored in a
   dated study guide on scribd.com).
2. **Binance Academy / Binance Blog trading guides (dated articles).** E.g.
   "A Beginner's Guide to Day Trading Cryptocurrency" (academy.binance.com; carries
   publish/updated timestamps); Binance Blog "A Beginner's Guide to Swing Trading
   Cryptocurrency" (Nov 20, 2023) and "Inside the Mind of a Professional Crypto
   Trader — Nik Patel" (Jun 7, 2023). https://academy.binance.com
3. **TradingView published ideas on SOL (per-post platform timestamps).** Public,
   individually timestamped setup write-ups referencing SOL levels/patterns
   (e.g., SOL head-and-shoulders / level setups surfaced in search).
   https://www.tradingview.com/ideas/
4. **Reddit r/algotrading / r/Daytrading community threads (dated posts).** Dated
   public threads describing intraday crypto scalping/day-trading mechanics (e.g.,
   r/algotrading thread "Finally having good results with my scalping alog",
   https://www.reddit.com/r/algotrading/comments/1r5al3o/; post timestamps
   platform-recorded; exact dates captured per-entry at corpus build).
5. **Published prop-desk-style strategy guides/PDFs (hosting-platform upload
   dates).** E.g. "6-Step Shark Trader Strategy Guide" (ORB with partial profits at
   S/R and VWAP), https://www.scribd.com (upload date recorded per document).

Caveat recorded honestly: search snippets did not always expose exact per-item
dates; the protocol (1.1-2) makes an unverifiable date inadmissible, and per-entry
platform timestamps are captured at corpus build. This existence check is
sufficient for the identity's *observability* field; it is not corpus content.

## 3. The ten §5.3 fields (identity-level, best-evidenced; per-rule override at codification)

1. **Payer.** Declared per RULE at codification, from the source's own story, and
   tested at F-0. Honest identity-level prior: most retail playbook payer lore is
   exactly the taxonomy Bảng 1 lore — stop-run victims, breakout chasers, FOMO
   retest buyers, late fade-sellers, funding-dodgers — whose families are already
   measured-dead (rows 1–11). A RULE that cannot name a payer who is
   forced/impatient/risk-averse and cannot self-arbitrage the premium away fails
   the F-0 payer test individually.
2. **Premium.** Per-RULE, declared pre-F-0 from the source's stated stop/target
   geometry in bps-per-decision at SOL price levels — never from outcomes.
   Ceiling honesty: the declared intraday RT cost book (~11–13 bps; child plan §3,
   shared with I002) means any RULE whose stated geometry implies gross capture
   below the RT ceiling on the frozen exit horizon is pre-dead at K-COST.
3. **Persistence.** Behavioral (playbook popularity) for most RULEs; erodes via
   crowding/mechanization. Skeptic tests the persistence claim at F-0; a RULE
   whose only persistence story is "the source says it works" is dead on
   information test (Q-7).
4. **Risk transferred.** Per-RULE intraday directional risk over the codified
   holding window; hard flat-by frozen at protocol/trial freeze; no multi-day
   carry (funding-adjacent class = dead row 10; force-flat before 8h settlement if
   a RULE's window would cross one). Named tail: gap through stop on thin book /
   event spike absorbed at taker crossing.
5. **Observable.** (a) The corpus + codified RULE definitions, constructible from
   closed bars on the SOLUSDT plane (1m/15m staged at data gate ≤0.5 GB per §3.4;
   bookTicker/aggTrades/mark/index coverage-verified per contract, missing ⇒
   BLOCKED). (b) Availability evidence: dated public sources exist (§2 above);
   plane assets PWS-CX-SOLUSDT durable (1h klines 2020-09..2026-08 gapless
   floor-exact; funding 6,580 settlements bit-exact; spread census p50 0.469 bps,
   6-month bookTicker) re-verified by bytes at the data gate; per-entry
   `available_at` = platform publication timestamp, `retrieved` = build date.
   (c) Any RULE needing an event calendar with true `available_at` names it or is
   `BLOCKED_DATA`.
6. **Holding horizon.** Per-RULE intraday (minutes–hours) set by the codified exit;
   hard flat-by cap; event-driven decision clock on closed bars (UTC).
7. **Capacity.** Order-of-magnitude from top-of-book at event time (bookTicker
   census at data gate): retail-scale notional; the pick-off/fade premia these
   playbooks imply decay with own order size, so capacity is small by mechanism.
   Per-RULE capacity declared at freeze from measured top-of-book depth, labeled
   `UNMEASURED_BEYOND_TOP_OF_BOOK` where depth history is absent.
8. **Costs.** Full RT decomposition per RULE: taker fee DECLARED 5 bps ×2 legs +
   1 adverse tick ×2 + spread census at the fill hour (measured; out-of-census-
   window fills costed at declared band ×1.5/×2.0 with
   `FILL_QUALITY_CLASS_declared` label) + funding only if the frozen window
   crosses a settlement (default: force-flat fixture makes this structural-zero,
   declared not assumed; `FUNDING_PATH_STRESSED` label if ever crossed). Fee layer
   promoted to measured only when validated vs fills (Q-8).
9. **Falsifier.** Per-RULE battery: (a) F-0 skeleton test — strip the
   RULE-specific observable, keep trigger/direction/exit shape; any same-shape
   match to dead family rows 1–11 ⇒ `F0_KILLED` with the collision row cited;
   (b) representation rho > 0.20 vs the dead class on a frozen, committed,
   reproducible representation ⇒ K-ANC; (c) the RULE must beat its clock-shifted
   placebo, inverted control, and beta-matched baseline at measured spread +
   declared fee + measured funding, two-sided, ≥100 closed RT over ≥2 vol regimes
   (master §6.5 floors); positive-but-sub-power = INCONCLUSIVE, never PASS. The
   control that must NOT reproduce the anchor: placebo (below).
10. **Control and baseline.** Per frozen RULE: causal control = clock-shifted
    placebo (same RULE re-timed +24h on the same clock; constructible null that
    MOVES the signal — Q-11), must not reproduce ≥0.5× anchor (K-CTRL); inverted
    control runnable, must not out-earn anchor, never read backwards as signal
    (P-28); baseline = beta-matched per-pair baseline set per master §6.2 (anchor
    must beat baseline with ≥2× margin).

## 4. Expectation stated honestly (pre-registered, testable)

Given the frozen collision table, we pre-register: **we expect ≥80% of codified
RULEs to match a dead skeleton (rows 1–11) at F-0**, and the survivors to be few
and to face the same K-ANC/K-COST/controls walls as I002. The measured per-rule
death ledger (rule → collision row → kill code) is itself a program artifact: it
either justifies `NO_ELIGIBLE_PROPOSAL` with evidence, or surfaces a genuinely
distinct surviving mechanism eligible for the freeze cap. Either outcome is a
product; neither is tuned toward.

## 5. BLOCKED_INCOMPLETE items declared

- Per-RULE premium figures: unfilled until corpus build + codification (post-freeze,
  pre-GO-2). Identity-level ceiling only (field 2). This is by design of the
  generator route, disclosed rather than papered over.
- K per author, N top-rules, and the exact annotation windows: frozen at protocol
  freeze (council), not here.
- Exact per-entry publication timestamps: captured at corpus build (§2 caveat).

---
*Blindness attestation: no backtest outcome, PnL, or sealed/holdout content was
sought, read, or used; no corpus byte was collected; the WebSearches were
existence checks only.*
