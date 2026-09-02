# A7 audit — A3 Family 1 `EQ_S2_A3_F1_PIT_RECON_FLOW` (PIT index-reconstitution forced-flow drift)

Sources audited: `research/proposals/stocks/a3_family1.{md,json}` (twin, consistent).

## 1. Dimension findings (PLAN §9)

### Novelty — PASS (strong)
Index-reconstitution price pressure is a classical space (Shleifer 1986;
Harris & Gurel 1986), but the proposal's lens is genuinely additive: the anchor
"is expressible **only** on such effective-dated membership plus PIT announcement
timestamps" and the falsification rule includes "(d) the edge exists only with
backfilled current membership rather than `members_as_of` effective rows (pure
data artifact)". Making the naive-backtest fake itself a falsification condition
is a novelty contribution, not a re-run. Not a PLAN-simple indicator grid: one
event type, one declared window constant, one neutralization.

### Source quality — PASS (strong)
Eight citations, all real to the best of A7 internal knowledge (Shleifer 1986
JF; Harris & Gurel 1986 JF; Beneish & Whaley 1996 JF; Wurgler & Zhuravskaya
2002 JEP; Greenwood 2005 JFE; Barberis-Shleifer-Wurgler 2005 JFE;
Chang-Hong-Liskovich 2015 JFE; Baker-Bradley-Wurgler 2011 FAJ), each marked
`MODEL_INTERNAL_UNVERIFIED` with "No DOIs and no direct quotes are asserted".
Attributions are used correctly (CHL 2015 as the rule-based-recon RDD basis for
the neighbour; B&W 1996 as anticipation evidence and decay caveat).

### Correlation (structural only) — PASS
Observable: index announcement/effective membership events. Clock: multi-week
announcement→effective→+20-session schedule. Counterparty: "index-tracking funds
and benchmark-constrained active managers" with tracking-error mandates.
Numeric prewindow rho: NOT_IMPLEMENTABLE_NO_REAL_DATA (no real data in sprint).

### Data readiness vs as-built factory — PASS with findings
Verified expressible: `MembershipTable.members_as_of` (structural no-backfill
ban exists as claimed), `SecurityMaster.ticker_as_of`,
`build_rebalance_snapshot` ACCEPTED/REJECTED rows, `evaluate_delisting_retention`,
`US_EQUITY_REGULAR_V1` close events, one-event entry delay helpers. Real data:
correctly declared UNAVAILABLE_PENDING_ENTITLEMENT incl. announcement records,
membership history for anchor and control indices, tracking-AUM, PIT GICS,
PIT borrow. Provider authority policy quoted matches `provider.py` as-built.
**Objection O1 (MEDIUM):** the JSON claims the announcement stream rides
"`BarLoader` event rows (ts_exchange, ts_ingest, allow_duplicate_timestamps=True)"
but as-built `BarLoader._validate_schema` requires numeric
`open/high/low/close/volume` on every row of `REQUIRED_BAR_COLUMNS`, and
`_assert_gaps` applies bar-gap discipline unless `enforce_gaps=False` with a
session predicate. Index announcements are not bars. Expressible instead as a
dedicated synthetic input record (precedent: `DividendEvent`, `BorrowLocate`),
but the stated binding is inaccurate and must be specified at freeze.
**Objection O2 (MEDIUM):** the "primary benchmark" is never named; the control
index is described only as "a matched index ... with economically negligible
tracking assets"; window constants are deferred ("window constants must be
declared per announcement-era"). All three are legitimate freeze-time
declarations, but the match rule for the control must be declared ex ante to
prevent control-shopping. Not disqualifying: the family fixes the mechanism,
clocks and falsification before any outcome.

### Cost/borrow feasibility — PASS
"Capacity is bounded by the A5 impact model (square-root law, hard order-size
caps...)" and "deletions (wide-spread, deteriorating names) bind first"; shorts
borrow-gated, "unavailable borrow => the short is rejected with a reason and the
book re-normalizes"; close-auction concentration acknowledged with per-name size
limits. Turnover 4–10x/yr is coherent with the declared cost models; x1.5 cost
and borrow x2/unavailable stresses are inside the falsification rule. No
free-borrow, no free-fill, no halt-fill anywhere.

### Hidden crypto-family rescue — NO RESCUE (E6 = 1)
Rescue-veto check vs inventory:
- vs M01 aggressor-flow absorption (rejected, PLAN.md §1): different observable
  (PIT membership announcements vs order-book aggressor imbalance), different
  counterparty (mandate-forced index funds vs momentum aggressors), different
  clock (multi-week schedule vs intraday), different control (no-tracking-AUM
  index vs crypto placebo). The causal control severs the mechanism: it keeps
  the "index change" observable while removing the tracking money, so a
  momentum/size confound that moved the anchor would also move the control and
  falsify.
- vs funding-carry (V6 CARRY-1D/3D/7D rejected): "No funding-rate observable or
  carry term anywhere" — confirmed; no perp, no funding term.
- vs weekly reversal (REVERSE-3D lineage): event-driven book around scheduled
  reconstitutions, not a periodic reversal clock; not conditioned on past
  returns.

## 2. Rubric scoring

- E1 fields_complete = 1 (all nine PLAN §9 fields present and specific in both twins)
- E2 literature = 1 (real published basis, honest MODEL_INTERNAL_UNVERIFIED, nothing fabricated)
- E3 arms = 1 (anchor + CHL-justified rule-based neighbour + no-flow control that plausibly destroys the mechanism while keeping the observable)
- E4 implementable = 1 (synthetic-fixture expressible against verified factory APIs; O1 binding correction is a freeze specification, not new scored machinery)
- E5 cost_borrow = 1 (coherent with declared cost models; borrow-gated; no free-borrow/free-fill)
- E6 not_rescue = 1 (all four axes differ from every rejected family)
- E7 a7_clean = 1 (0 HIGH/CRITICAL; 2 MEDIUM, 1 LOW — advisory only)

**Sum 7/7 — ELIGIBLE.**

## 3. Quality score: 8.5 / 10

Justification: the strongest causal design of the six (the control holds the
observable constant and removes only the forced-flow channel); literature basis
deep and correctly deployed (mechanism, anticipation, RDD neighbour, decay
caveats all cited to purpose); the backfilled-membership falsifier directly
weaponizes the lane's PIT machinery. Deductions: freeze-time specification debt
(O1 loader binding, O2 index/control/window identities), and the honest caveat
that the documented effect has decayed for decades — a real null risk the
proposal itself declares.

## 4. Objections

| id | severity | objection | resolution required |
|---|---|---|---|
| O1 | MEDIUM | Announcement stream cannot ride `BarLoader` as claimed (numeric OHLCV schema; gap discipline); stated factory binding inaccurate | Freeze must declare a dedicated event-record schema with `ts_exchange`/`ts_ingest` and PIT discipline, or an explicit loader extension |
| O2 | MEDIUM | Benchmark index, control index and per-era window constants unnamed/unfixed | Freeze must pin index identities, the control "matched/negligible-tracking" rule, and era-conditional constants ex ante |
| O3 | LOW | Exit at effective+20 can precede/overlap entry when an era has short announcement→effective gaps | Freeze must define degenerate-window handling |

## 5. Verdict

**ELIGIBLE** (7/7). No failed rubric items. Expected rank 1 under the frozen
rubric (quality 8.5, no tie).
