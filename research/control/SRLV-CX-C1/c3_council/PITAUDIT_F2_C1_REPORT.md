# PITAUDIT_F2_C1 — PIT / constructibility audit of council proposals, SRLV-CX-C1

- Lane: PIT/DATA AUDITOR (F2). FAIL power on any lookahead / constructibility defect. No PnL exists; nothing scored was consulted.
- Date: 2026-09-26. Worktree verified: `/Users/hoangminhlong/my-quantitative/.worktrees/srlv-cx-c1/integration`, branch `orca/srlv-cx-c1-integration`, HEAD `d3f063a05338e498912a16d4678d4451fd0cb838`.
- Audited against the frozen ban list: `plans/PLAN_srlv_program_v1.md` §3 (PIT/intrabar law, items 1–8) and §2.4 (vol-state contract); data reality: `research/control/SRLV-CX-C1/c1_datagate/C1_DATAGATE_VERDICT.md`, `research/control/SRLV-CX-C1/c2_exposure/EXPOSURE_VERIFICATION_C1.md`.
- Objects audited (literal check, bar-index level): `research/control/SRLV-CX-C1/c3_council/PROPOSAL_P1.md` (P1-A, P1-B), `PROPOSAL_P2.md` (P2-M1, P2-M2).
- touched paths: this file + `HANDOFF_pit.json` only. No commit.

---

## 0. Global convention that every window below depends on (pin P0)

All bar arithmetic in both proposals requires the **bar labeling convention** to be pinned:
bars are labeled by UTC **open time**; close-time = open + 1h. All four proposals mix
"close-time" (P1 windows) and open-time hours (P2-M2 mask) without stating the convention.
Every result below assumes open-time labeling. Pin it verbatim at freeze; a flip of the
convention shifts every P1 window by one bar and invalidates the flat-by-settlement math in §1/§2.

---

## 1. P1-A — SETTLE-SWEEP-ABSORB

### 1.1 Same-day / same-window statistics
- ATR24: "mean true range of the last 24 CLOSED bars at decision time (trailing only)". Legal under §2.4. **Pin P1-3**: ATR24(x) at any evaluation at close of bar x must be mean TR over exactly one pinned window — either x−24..x−1 or x−23..x (both fully closed at close of x; recommending x−23..x, warmup 25 bars incl. the prior close needed by the first TR). The text does not say which, and ATR24 is consumed at *multiple* instants (sweep evaluation, per-bar breakdown-expiry check in (s,c], disaster stop, P1-B buffer): each consumption must recompute ATR24 at *its own* evaluation close, never reuse an event-time ATR. No same-day percentile, no unclosed-bar input — verified absent.
- Prior-window statistics: none used. No same-day regime statistic anywhere. PASS.

### 1.2 Pivot confirmation lag / off-by-one (audit item 2)
- t_known = close of bar j+6; inputs = lows/highs of j−6..j+6, all closed at that instant. Lag = 6 closed bars ≥ 1-bar law floor. PASS.
- **Same-bar confirm-and-trigger is impossible by construction** — verified proof: the pivot definition requires `low[j]` strictly below the lows of j+1..j+6, hence `low[j+6] > L`, so bar j+6 cannot sweep its own level (`low[s] < L` false), and since `close[j+6] ≤ high[j+6] < H` (mirror) it cannot break it either. The first bar that *can* trigger is j+7, strictly after t_known. No off-by-one exists — **provided** the strict inequalities of the pivot definition are frozen verbatim (pin P1-8: all pivot neighbor comparisons strict; equality ⇒ not a pivot).
- Whether s ≥ j+6 or s ≥ j+7 is moot for triggering (see proof) but the freeze must still pin the candidate range (pin P1-9).

### 1.3 Fill law (audit item 3)
- Decision at close of c ⇒ fill at open of c+1, opposite-quote, 1 adverse tick. Exactly the engine law (§3.3). Sweep bar s and reclaim bar c are enforced distinct (c > s) — no same-bar confirm-then-backward-fill. Exit rules all close-based with next-open execution. PASS.

### 1.4 Intrabar ordering (audit item 4)
- Sweep = `low[s] < L` on one bar; reclaim = `close[c] > L` on a **later** bar. Cross-bar; "no intrabar ordering assumed" stated. No wick-then-body or high-before-low assumption anywhere. PASS.

### 1.5 Settlement windows & flat-by-settlement (audit item 5)
- S_k known in advance (clock / announced funding schedule) — PIT-legal. Window reads TIMES only, never rate magnitudes (fence 4 respected). PASS.
- **Finding F-1 (highest severity for P1, constructibility not lookahead): the literal entry rule and the literal flat-exit rule collide.** With open-time bars, W_k = bars open ∈ [S−2h, S+2h]. Latest chain: s open S+2h, c = s+3 ⇒ decision at close-time ≤ S+6h ⇒ entry open ≤ S+6h. But the pre-registered flat exit ("open of the last bar whose close precedes S_{k+1} − 2h" = S+6h) is the bar opening at **S+4h** (closes S+5h < S+6h). Entries with fill open ≥ S+4h would occur at or after the mandated exit. **Pin P1-1 (mandatory, unique fail-closed resolution)**: at entry evaluation, precompute the clock-determined exit open T_exit; if T_exit ≤ entry open-time ⇒ skip the event, log SKIP_FLAT_WINDOW. Under P1-1 the numbers reconcile exactly with the stated "worst-case hold ≤ 4 bars" (entry open ≤ S+3h, forced exit at open S+4h, 4 held bars, flat 4h before S_{k+1}). Without P1-1 the spec is non-constructible; any implementation without it = K-PIT at fixture time (fixture F-P1A-FLAT).
- Pin P1-2 (event partition, fail-closed): the text covers bars in (s, c] for the breakdown clause but not the sweep bar's own close. Freeze the partition table: `close[s] > L` ⇒ sweep state opens (P1-A path); `close[s] ≤ L − 0.25×ATR24` ⇒ breakdown, belongs to P1-B only; `close[s] ∈ (L − 0.25×ATR24, L]` ⇒ dead zone ⇒ expires flat on BOTH mechanisms, logged. Equality cases resolved by strictness pins.
- Pin P1-4: intactness is closes-only, evaluated as "no bar k with t_known < k < s closed on the far side" at the sweep bar (the sweep bar's own close is handled by P1-2, not by intactness).
- Pin P1-5: precedence — one position per pair; events arising while a position is held are ignored; a consumed sweep bar never re-triggers; a *new* sweep bar may re-trigger the same level after full flat. Simultaneous long-side and short-side events in the same bar ⇒ skip (fail-closed). Not stated in the proposal; must be frozen.
- Exit (i) "opposite-side reclaim close" is ambiguous for the long arm (reclaim of the mirror swing high, vs. back through the swept low). Pin P1-6: define the opposite-side object exactly (recommend: mirror swing level, i.e., close > H exits a long entered off the low sweep).
- Ordering of the forced time exit vs close-based exits at the same instant: T_exit open wins (forced flat), pin P1-7.

### 1.6 Calendar / clock (audit item 6)
- Settlement clock UTC 00/08/16; no DST in UTC; crypto 24/7. PASS. **Pin P1-10 (funding-grid reality)**: BTC/ETH use the measured per-pair `fundingTime` grid (floors 2019-09-10 / 2020-01-01 — both precede the kline window, PASS). SOL/BNB flat arms assume the 8h grid, but SOL/BNB funding is NOT staged and venues have historically changed funding intervals on some symbols. Before any SOL/BNB flat arm scores: enumerate the ACTUAL historical settlement grid (staged or venue-archived schedule); if any interval ≠ 8h in-panel, re-derive the window/flat geometry against the actual grid or `BLOCK` the arm. Fail-closed.

### 1.7 Funding PIT (audit item 7)
- Mechanism conditions on settlement TIMES only — no conditioning on the current-interval (not-yet-settled) rate anywhere. Stress book applies the measured rate per settlement actually held across; a settlement's rate is used only at/after its `fundingTime`. PASS. Base book funding ≡ 0 holds under P1-1 (verified: no held interval contains S_{k+1}).

### 1.8 SOL 2 gaps (audit item 8)
- The per-pair data gate is cited but the no-fill rule is not restated. **Pin P1-11 (binding, from C1 verdict)**: any missing bar inside ANY required window (pivot j−6..j+6, ATR24 window, sweep/reclaim candidate bars, fill open, exit open) ⇒ no evaluation / no fill / force-flat, no interpolation, no forward-fill of prices; log SKIP_GAP. Fail-closed. Applies to SOL's 2 disclosed gaps and to any pair.

### 1.9 Warmup (audit item 9)
- ATR24 (pin P1-3) needs 25 completed bars (24 TR values, first TR needs the prior close). First fully-formed pivot at j ≥ 6; first triggerable bar ≥ j+7. Pin: no decision before `panel_start + 25 bars`, and level usable only from its own t_known. State in freeze.

### 1.10 P1-A verdict
**PIT_CONSTRUCTIBLE** — conditional on pins P0, P1-1..P1-11 being frozen verbatim. F-1 (flat-exit/entry collision) is the one defect class in this proposal; it has a unique fail-closed resolution, so it is a mandatory freeze pin, not a PIT_FAIL. Unpinned implementation ⇒ K-PIT at fixture stage (fixtures §5).

---

## 2. P1-B — SETTLE-BREAK-CASCADE

Shares P1-A's level machinery, so pins P0, P1-3..P1-11 carry over. Differences audited:

### 2.1 Break event
- `close[b] > H + 0.25×ATR24` — close-based; wicks never trigger; no intrabar ordering. PASS. ATR24 evaluated at close of b per pin P1-3 (buffer neighbors 0.15/0.40 frozen).
- **Pin P1-B-1**: "intact swing high H" must be evaluated closes-only at b's open (bars t_known < k < b); the break bar's own close is the event, not an intactness violation.
- Same-bar confirm-and-trigger: impossible by the pivot strict inequality (`high[j+6] < H` ⇒ `close[j+6] < H + buffer`), same proof as §1.2. PASS.

### 2.2 Fill law / exits
- Decision close of b ⇒ fill open of b+1. PASS (engine law).
- Exits: (i) opposite acceptance close-based; (ii) disaster stop close beyond entry-side extreme by > 1.0×ATR24 beyond the level — pin the ATR24 evaluation instant at each held bar's close (P1-3 applies); (iii) flat-by-settlement — **F-1 applies identically** (b can sit late in W_k; entry open can reach S+6h vs T_exit S+4h). Pin P1-1 (skip when T_exit ≤ entry open) is mandatory here too.
- Worst-case hold ≤ 4 bars reconciles only under P1-1, as in §1.5.

### 2.3 Funding / gaps / warmup
- Identical to P1-A: funding PIT PASS (times-only in the anchor; measured rate only at/after fundingTime in the stress book); SOL/BNB flat arms subject to pin P1-10 grid verification and P1-11 gap rule; warmup 25 bars + pivot context.

### 2.4 P1-B verdict
**PIT_CONSTRUCTIBLE** — conditional on P0, P1-1..P1-11, P1-B-1 frozen.

---

## 3. P2-M1 — Prior-Day-Extreme Sweep-then-Reclaim (PDSR)

### 3.1 Same-day / same-window statistics (the critical check)
- Level = max/min over the 24 completed bars of **day d−1** — the PREVIOUS completed UTC day, never the current one. `t_known` = 00:00 UTC of day d. This is exactly the §3.5 requirement ("day-d full range tại day start" forbidden; d−1 used). PASS.
- Absorption proxy: `range_{t+1} > median(range, t−23..t)` — decision at close of t+1; bars t−23..t all closed by then; the deciding bar's own range is closed at decision. Trailing-only. PASS. Pin P2M1-2: median window is exactly t−23..t (24 bars, excluding the deciding bar), frozen.
- Vol state (optional arm): trailing 24 completed-bar log-return std, walk-forward terciles — §2.4-conformant; incrementality test with drop-vol-not-identity rule pre-registered. PASS.

### 3.2 Pivot lag / off-by-one
- Level confirmed at close of the last bar of d−1 (lag = 1 closed bar = law floor). First trigger bar of day d closes at 01:00 ≥ t_known — strictly after confirmation. No off-by-one. PASS.
- Pin P2M1-3 (day-roll): level set frozen at entry even if UTC day rolls mid-trade — stated in the proposal; freeze verbatim. A new day's level never retroactively applies to an open trade.

### 3.3 Fill law (audit item 3) — the t/t+1/t+2 sequence
- Sweep decided at close of bar t; reclaim confirmed at close of bar t+1; **decision bar = t+1, fill = open of t+2**. This is exactly the engine law (decision on the closed bar whose close informs the decision ⇒ fill next open). One full bar elapses between the deciding close and nothing — the fill is at the first instant after the deciding close. **Legal; not a tighter variant.** Any variant that fills at close of t+1, or at open of t+1 (using t's close only), would be *different*, not tighter; any variant deciding on t+1 and filling at t+1's open is impossible/impossible-to-construct and would be illegal — none is proposed. PASS.
- Exits: all close-based, executed next open. PASS.

### 3.4 Intrabar ordering
- Close-through only; "wicks never trigger"; reclaim is a close condition. No intrabar ordering anywhere. PASS.

### 3.5 Funding
- BTC/ETH only; holds may span ≤1 settlement; "a settlement is known only AT its fundingTime" stated verbatim; per-settlement accounting, price/funding columns separated (Q-14), dual book. No conditioning on predicted rates. PASS. SOL/BNB excluded from the anchor (funding NOT staged) — funding gate honored; the optional flat-by-settlement SOL/BNB neighbour inherits pins P1-10/P1-11 and must pass fixture F-FLAT.

### 3.6 Gaps / warmup / calendar
- No SOL anchor ⇒ gap rule N/A for the anchor; neighbour must inherit the C1 no-fill rule.
- Warmup: **pin P2M1-4**: first valid decision requires (a) day d−1 fully inside the panel (earliest decision day = panel day 2) and (b) absorption median bars t−23..t present ⇒ trigger bar index ≥ 23. Freeze: `first_decision = max(first bar of panel-day 2, bar_index ≥ 23)`.
- Calendar: UTC day boundary, no DST (UTC), 24/7. PASS — verified as the dispatch asked.
- **Pin P2M1-1 (spec gap, fail-closed)**: upside sweep at H followed by `close_{t+1} < L` (continuation through the whole prior-day range) is neither reclaim (`L ≤ close ≤ H`) nor acceptance (`> H`). Pin: expires flat, logged SKIP_CONTINUATION. Boundary `close_{t+1} == H`: reclaim test is inclusive (`≤ H`), acceptance strict (`> H`) — consistent, no gap; freeze the inclusive/strict bounds verbatim.
- Pin P2M1-5: multiple sweep events of the same day's level set — chronological first-come, one position per pair, events during hold ignored, re-arm only from a new sweep bar after full flat.

### 3.7 P2-M1 verdict
**PIT_CONSTRUCTIBLE** — conditional on pins P0, P2M1-1..P2M1-5 frozen.

---

## 4. P2-M2 — Weekly-Shelf Break-Acceptance Impulse (WSA)

### 4.1 Same-window statistics
- Shelf at close of t = extremes over completed bars t−168..t−1, **window excludes bar t** ⇒ no self-inclusion, pivot lag ≥ 1 by construction. PASS. Expansion proxy median over t−23..t — trailing, closed. PASS (same pin semantics as P2M1-2).
- Fixture-relevant proof: a "broken" implementation including bar t in its own shelf would let the event bar's close exceed a range it itself extends — the F-SHELF fixture below detects exactly this.

### 4.2 Pivot lag / off-by-one
- `close_t > W_high(t)` with W(t) built from ≤ t−1: all inputs closed at the deciding close. Acceptance compares `close_{t+1}` against the **frozen** W values (computed at t, known one bar earlier). No off-by-one. PASS.

### 4.3 Fill law
- Decision close of t+1 ⇒ fill open of t+2 — engine law, same reasoning as §3.3. Legal, not tighter. Exits close-based, next open. PASS.
- **Pin P2M2-3 (time-stop bar arithmetic)**: "time stop M2 = 4 bars after entry" is ambiguous. Freeze: entry fill bar E = bar t+2; exit decision at close of E+3, execution at open of E+4 = entry open + 4h (exactly 4 held bars).

### 4.4 Intrabar ordering
- Close-through break, close-based acceptance, close-based invalidation. No intrabar ordering anywhere. PASS.

### 4.5 Flat-by-settlement — **the sharpest finding of this audit (F-2)**
The proposal claims: with M2=4 and entry opens restricted to {01,02,03,09,10,11,17,18,19}, "the position always closes ≥1 bar before the next 00/08/16 UTC boundary". This claim is **true only under pin P2M2-3** (exit at entry open + 4h). Verified hour-by-hour under that reading:

| entry open | exit open (+4h) | next boundary | margin |
|---|---|---|---|
| 01 | 05 | 08 | 3h ✓ |
| 02 | 06 | 08 | 2h ✓ |
| 03 | 07 | 08 | 1h ✓ |
| 09 | 13 | 16 | 3h ✓ |
| 10 | 14 | 16 | 2h ✓ |
| 11 | 15 | 16 | 1h ✓ |
| 17 | 21 | 00 | 3h ✓ |
| 18 | 22 | 00 | 2h ✓ |
| 19 | 23 | 00 | 1h ✓ |

Under the alternative reading (exit decision at close of E+4, execution at open +5h), entries at 03/11/19 UTC exit **exactly at** the 08/16/00 boundary ⇒ position open at a settlement ⇒ the SOL/BNB zero-funding claim is FALSE and the funding gate is violated. The proposal's own "≥1 bar before" phrasing matches the +4h reading, so the intent is recoverable — but the guarantee is reading-dependent. **Mandatory pin P2M2-1: freeze the +4h semantics (4 held bars, exit at the 5th open) and require fixture F-M2-FLAT (the 9-row table above, re-derived against the ACTUAL per-pair settlement grid per pin P1-10) to pass before any SOL/BNB flat arm scores. If the +4h semantics cannot be pinned, this flips to `PIT_FAIL_FLAT_BY_SETTLEMENT_NOT_GUARANTEED`.** BTC/ETH arms: hold (E_open, E_open+4h] across an 8h grid contains at most 1 boundary — funding measured there, PASS.
- Invalidations fire earlier than the time stop only — earlier is flatter; no path holds longer. PASS under P2M2-1.
- Mask applies to FILL opens (t+2 open); deciding bars may be any hour; identical mask on every control — constructible, pin P2M2-4 (events whose t+2 open falls outside the mask are skipped and logged).

### 4.6 Funding PIT
- BTC/ETH: measured per-settlement, known at fundingTime, ≤1 crossed, dual book. No predicted-rate conditioning. PASS. SOL/BNB: structural zero under P2M2-1 + P1-10.

### 4.7 Gaps
- Text covers only "entry/hold spans a gap bar". **Pin P2M2-2 (extend, fail-closed)**: any missing bar in ANY required window — the 168-bar shelf, the 24-bar median window, event bar, acceptance bar, fill open, exit open ⇒ shelf/decision invalid ⇒ no decision, no interpolation, logged SKIP_GAP. With only 2 disclosed SOL gaps this is cheap and must be total, not partial (a partial-window extreme is a silent lookahead-shaped hazard: a shorter window produces different "extremes").

### 4.8 Warmup (audit item 9)
- **Pin P2M2-5**: shelf complete ⇒ event bar index ≥ 168; median window ⇒ ≥ 23 (dominated); first possible fill open ≥ bar index 170. No decision before `panel_start + 168 bars`. Freeze and enforce (fixture F-WARMUP).

### 4.9 P2-M2 verdict
**PIT_CONSTRUCTIBLE** — conditional on pins P0, P2M2-1 (gate severity), P2M2-2..P2M2-5 frozen. The explicit flip condition on P2M2-1 is recorded in §4.5.

---

## 5. Cross-cutting checks (all four)

| Audit item | P1-A | P1-B | P2-M1 | P2-M2 |
|---|---|---|---|---|
| 1 same-window stats | PASS (pin P1-3) | PASS (pin P1-3) | PASS (d−1 level; pin P2M1-2) | PASS (t-excluded shelf; pin P2M1-2 semantics) |
| 2 pivot lag / off-by-one | PASS (proof §1.2) | PASS (proof §2.1) | PASS (1-bar lag, §3.2) | PASS (t-exclusion, §4.2) |
| 3 fill law | PASS | PASS | PASS (t+1 close → t+2 open = engine law) | PASS (same) |
| 4 intrabar ordering | PASS (cross-bar) | PASS (closes only) | PASS (closes only) | PASS (closes only) |
| 5 flat-by-settlement | PIN P1-1 (F-1) | PIN P1-1 (F-1) | n/a (funding-exposed by design, BTC/ETH measured) | PIN P2M2-1 (F-2, gate severity) |
| 6 calendar/DST | PASS (UTC; pin P1-10 grid) | PASS | PASS (UTC day) | PASS (rolling 168h, calendar-free) |
| 7 funding PIT | PASS (times only) | PASS (times only) | PASS (rate at fundingTime) | PASS |
| 8 SOL gaps fail-closed | PIN P1-11 | PIN P1-11 | n/a anchor / neighbour inherits | PIN P2M2-2 |
| 9 warmup | PIN 25 bars | PIN 25 bars | PIN P2M1-4 | PIN P2M2-5 |

No lookahead defect found in any proposal. The two constructibility defects (F-1, F-2) both live in the exit/flat laws, both have unique fail-closed resolutions, and both are gated by fixtures below. **No proposal earns a PIT_FAIL.** Every verdict is conditional: an implementation that ships without the pins is K-PIT at fixture time, regardless of the CONSTRUCTIBLE label here.

---

## 6. EXACT fixture list (mandatory before ANY scored run)

Serialization precondition for all byte-identity fixtures: event records written with a pinned fixed-decimal float format and a pinned field order; sha256 of the sorted record stream is the comparison key. Bar convention per pin P0 everywhere.

### 6.1 Common M-class core (every mechanism, every pair, dev folds F1–F4)

- **F1 PANEL-TRUNCATION BYTE-IDENTITY** (plan §3.6-i, M-5): ≥ 512 decision timestamps per mechanism, stratified across pairs × folds × event states (no-event / sweep-or-break open / event expired / entry / each exit rule). For each, truncate the panel at the decision close and re-run the full pipeline from panel start. The emitted decision record must be byte-identical. PASS = 512/512 identical, zero tolerance.
- **F2 FUTURE-MUTATION INVARIANCE** (§3.6-ii): same timestamps; mutate every bar strictly after the decision close (set OHLC = (c, 2c, 0.5c, c) plus +5% drift) and re-run. Decision records (including any frozen level/ATR/median values they carry) must be unchanged. PASS = 100% invariance. Per mechanism, additionally assert the frozen object is stable: P1 level value recorded at t_known; P2-M1 day-d−1 extremes frozen at entry; P2-M2 shelf frozen at the event bar.
- **F3 DELAY-PAIR delay-0 / delay-1** (§3.7, Q-4): delay-0 = spec fills; delay-1 shifts ONLY the fill one bar later (P1-A: open c+2; P1-B: open b+2; P2-M1: open t+3; P2-M2: open t+3), all rules otherwise frozen, full engine re-run. Note: occupancy (one position per pair) can legitimately diverge the event sets downstream — the fixture requires both arms complete and finite on the same panel with the expectancy-ratio table emitted for the pre-registered kill adjudication; it does NOT require identical trade sets.
- **F4 NON-VACUITY (≥2% decision rate)**: per pair × fold, decision-capable bars = post-warmup bars inside the pair's data-gate window. (a) defined-decision coverage: share of decision-capable bars where the engine emits a defined decision record (any of no-event / state-open / expired / entry / hold / exit — including logged skips) ≥ 2% (a correct engine is near 100%; this catches silent-empty engines); (b) full-census row: candidate events found, expired, traded, per direction per fold, against the proposal's own predicted event-rate band (0.1×–10×); (c) trade counts vs the ≥100-RT floor reported per direction per pair — below-floor rows are labeled `NOT_RUN_THIN` (pre-registered legitimate death), never silently dropped.
- **F5 DRY-RUN LEAK SCAN** (§3.8): (a) static: AST/grep scan of the signal module for `shift(-`, `.iloc[i+k]`, `bfill`, `fillna(method="bfill")`, `rolling(center=True)`, and any use of a candidate bar's own high/low inside functions declared trailing (ATR24, median-range, shelf); (b) runtime taint probe: every observable call logs (decision_ts, max_input_bar_ts); assert `max_input_bar_ts ≤ decision_ts` for 100% of calls; (c) funding sentinel probe (funding-exposed arms): set each settlement's rate to a sentinel visible only at/after fundingTime; assert it is applied only to holds spanning that settlement and never read by any decision before it; assert the next interval's rate is never read.
- **F6 INDEPENDENT IMPLEMENTATION** (§3.6-iii, pre-scored-run): reproducer re-implements from the PROPOSAL text + raw klines only (no impl code reuse); record-level diff on dev folds over (pair, event bar ts, level value, ATR24/median inputs, decision ts, fill ts, side, exit ts, exit rule): discrete fields exact, floats equal at the pinned decimals. Any diff ⇒ K-PIT.
- **F7 FOLD FORCE-FLAT** (C2 binding): assert zero held positions cross any F1/F2/F3/F4 boundary timestamp, all four mechanisms.

### 6.2 Per-mechanism fixtures

- **F-P1A-FLAT / F-P1B-FLAT** (enforces pin P1-1, finding F-1): synthetic panel with a sweep/break at the window's end (s open = S+2h, c = s+3) ⇒ assert the engine SKIPS (T_exit ≤ entry open) and that over the full dev panel zero held intervals contain any actual settlement instant from the per-pair grid; emit the entry-open vs T_exit histogram.
- **F-P1-OFFBYONE** (pins P1-8/P1-9): synthetic panel whose only candidate is bar j+6 itself ⇒ assert no trigger (pivot strict-inequality proof) and that the first possible trigger bar is j+7.
- **F-P1-PARTITION** (pin P1-2): sweep bar closing in each of the three zones (`> L`, `≤ L−0.25ATR24`, dead zone) ⇒ assert trade / P1-B-only / flat-both respectively, logged.
- **F-ATR-INSTANT** (pin P1-3): event where ATR24 differs across the sweep, expiry-check, and stop evaluation instants ⇒ assert per-instant recomputation (no event-time ATR reuse).
- **F-M1-DAY** (P2-M1): (a) sweep bar = first bar of day d ⇒ level = day d−1 extremes; (b) contaminate day d with synthetic partial-day extremes ⇒ day-d−1 level unchanged (same-day exclusion proof); (c) `close_{t+1} < L` continuation case ⇒ SKIP_CONTINUATION, flat (pin P2M1-1); (d) boundary `close_{t+1} == H` ⇒ reclaim, inclusive bounds (pin P2M1-1).
- **F-M2-SHELF** (P2-M2): event bar sets a new 168h extreme ⇒ shelf must exclude bar t (detects the self-inclusion bug); frozen-shelf stability under future mutation.
- **F-M2-FLAT** (P2-M2, pin P2M2-1 — GATE for all SOL/BNB flat arms): re-derive the 9-row entry-hour→exit-hour table (§4.5) from the implementation and from the ACTUAL per-pair settlement grid; assert every exit open is ≥1 bar before the next actual boundary; assert zero held interval contains a settlement instant over the full dev panel. Fail ⇒ the SOL/BNB arms are `PIT_FAIL_FLAT_BY_SETTLEMENT_NOT_GUARANTEED` and blocked.
- **F-GRID** (pin P1-10, gate for any SOL/BNB flat arm): enumerate the actual per-pair historical settlement grid; if any interval ≠ 8h in-panel ⇒ re-derive geometry against the actual grid or `BLOCK` the arm. Fail-closed.
- **F-GAP** (pins P1-11 / P2M2-2): inject the 2 SOL gaps (and synthetic gaps at fill/exit opens and inside ATR/shelf/median windows) ⇒ no evaluation/fill, force-flat, no interpolation, SKIP_GAP logged; assert a partial-window shelf is never computed.
- **F-WARMUP** (pins P2M1-4 / P2M2-5 / §1.9): assert zero decisions before panel_start + warmup (P1: 25 bars; P2-M1: max(day-2 start, index ≥ 23); P2-M2: 168 bars, first fill ≥ 170).
- **F-PRECEDENCE** (pins P1-5 / P2M1-5 / P2M2-4): simultaneous both-side events, events during hold, out-of-mask fill opens ⇒ deterministic pinned behavior, logged.

### 6.3 Acceptance

A mechanism may enter any scored run only after F1–F7 (its pair scope) plus all of its per-mechanism fixtures PASS on the exact frozen code digest. F-M2-FLAT and F-GRID additionally gate the SOL/BNB flat arms specifically. Fixture failure on any pin ⇒ K-PIT for that mechanism as implemented.

---

## 7. Verdict summary

| Proposal | Verdict | Blocking pins | Flip condition |
|---|---|---|---|
| P1-A SETTLE-SWEEP-ABSORB | PIT_CONSTRUCTIBLE | P0, P1-1..P1-11 | — (P1-1 unpinned ⇒ K-PIT at fixtures) |
| P1-B SETTLE-BREAK-CASCADE | PIT_CONSTRUCTIBLE | P0, P1-1..P1-11, P1-B-1 | — |
| P2-M1 PDSR | PIT_CONSTRUCTIBLE | P0, P2M1-1..P2M1-5 | — |
| P2-M2 WSA | PIT_CONSTRUCTIBLE | P0, P2M2-1..P2M2-5 | P2M2-1 unpinnable ⇒ `PIT_FAIL_FLAT_BY_SETTLEMENT_NOT_GUARANTEED` |

All four observables are geometric from completed 1h bars, use ≥1-closed-bar confirmation lags, next-bar-open fills, no intrabar ordering, no unsettled-rate conditioning, and no same-day regime statistics. The exit/flat laws carry the only two defects (F-1, F-2); both are resolved fail-closed by the pins and gated by fixtures. This lane will re-audit the frozen code digest against these pins at F3 if dispatched.
