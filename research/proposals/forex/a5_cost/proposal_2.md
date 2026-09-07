# FX2-A5-P2 — Fixing-and-rollover window risk premium on DST-correct clocks

Lane: A5 (cost / rollover / accounting perspective) — F2 outcome-blind proposal.
Status: scientific hypothesis. No returns, no PnL, no backtest were computed for
this proposal and no other lane's output or scored ledger was read.

## Mechanism in one paragraph

Currency benchmarks (Tokyo 09:55 JST, ECB 14:15 CET, WM/Reuters 16:00 London)
and the New York 17:00 ET rollover concentrate inelastic, mandate-driven order
flow: passive hedgers must trade at fixings, and dealer rolls plus financing
charges concentrate at the roll. Krohn, Mueller & Whelan (2024, Journal of
Finance) document sharp, predictable return and volume spikes around the
fixings, consistent with benchmark-flow price pressure that partially reverses
afterward; Andersen & Bollerslev (1997) document the structural intraday
volatility periodicity; Cornett et al. (1995) show the FX day splits into
distinct overnight vs intraday return components. From this lane's perspective
the mechanism is a liquidity-provision premium: whoever absorbs inelastic
fixing/rollover flow, or holds exposure through the financing hour when spreads
widen, is compensated for that service. The signal is deterministic calendar
membership known infinitely in advance — no estimation, no fitted hour, no
session filter chosen after seeing returns.

## Contract fields (narrative mirror of proposal_2.json — JSON is authoritative)

- **Economic mechanism**: benchmark price pressure + financing-hour inventory
  risk, paid to the patient liquidity-providing side; direction (USD side)
  preregistered from the documented pressure sign, not from observed profits.
- **Expected counterparty**: passive benchmark-hedgers and corporate treasury
  flows trading at the fix regardless of price; dealers long inventory risk
  through the roll; leveraged investors paying the financing wedge.
- **Signal fields and publication clock**: window membership predicates in
  named zoneinfo zones (America/New_York 17:00 roll, Europe/London 16:00 fix,
  Asia/Tokyo 09:55 fix); PIT fixing-convention history (currently UNAVAILABLE);
  executable bid/ask at window open/close (currently UNAVAILABLE). The
  publication clock is the calendar itself — zero look-ahead by construction.
- **Formation / holding / rebalance**: enter USD-long basket at window open on
  the executable ask; hold exactly the 1h bar containing the fixing/roll
  timestamp; exit at executable bid. No portfolio rebalancing — an event
  schedule. Variant A closes before the roll (spread-net test); variant B holds
  through the roll so the charged swap is inside the test; A−B measures the
  rollover wedge directly.
- **Pair universe and neutralization**: the seven frozen USD pairs; one
  USD-long basket per window, equal-risk weights; no cross exposure; exposure
  reported by underlying currency.
- **Expected spread / rollover / turnover**: high turnover (~1 window/day);
  spread is the first-order economic variable and spreads are typically widest
  exactly at the rollover — the mechanism survives only if the window premium
  exceeds measured executable round-trip cost, per pair and session, never a
  global pip and never midpoint labeled executable. Variant A charges no swap;
  variant B requires an authorized swap schedule (UNAVAILABLE — blocked).
- **Anchor / neighbour / negative control**:
  - *Anchor*: USD basket over the WM/R 16:00 London fix window, no-roll,
    net of executable spread — the best-documented fixing-flow concentration.
  - *Neighbour*: same construction at the Tokyo 09:55 JST fix — same
    mechanism, independent institution and session; validates if same-signed
    with the sharp-around-fix/reverse-after shape; a London-only result must be
    argued, not assumed.
  - *Causal negative control*: preregistered +6h shifted placebo window with
    identical length, pairs, turnover and DST behavior, landing on event-free
    local time. It preserves everything mechanical and removes only the
    hypothesized cause (event timing); a placebo premium ≥ anchor premium
    destroys the family.
- **Expected regimes and falsification**: premium structurally stable and
  scaling with benchmark-hedging volume; absent before fixing conventions
  existed (a "premium" in pre-convention sub-periods is a clock/PIT bug);
  independent of the rate cycle. Falsified if anchor ≤ 0 net of costs, placebo
  ≥ anchor, neighbour opposite-signed without explanation, premium shifts with
  DST transitions, or premium survives only on midpoint/constant-spread
  scoring.
- **Macro/session external-validity risks**: anachronistic fixing conventions
  without PIT history; hardcoded UTC offsets breaking twice a year at DST;
  holiday-thinned weeks (tables SYNTHETIC_TEST_ONLY); macro-release days
  (exclusions must be preregistered, never tuned); one dealer's quotes are not
  the global decentralized market; 1h base clock is coarse for 30-minute
  windows — finer execution claims need finer PIT data and new trials.
- **Exact trial count**: 4 (anchor A no-roll; anchor B roll-through, blocked on
  swap authority; Tokyo neighbour; +6h placebo). No post-score replacement,
  shifting or re-windowing.
- **Required PIT fields and availability** (graded against measured repo facts):
  bid/ask 1h history — UNAVAILABLE (0 of 7 pairs, fail-closed); PIT
  fixing-convention history — UNAVAILABLE (no repo source); rollover/swap
  schedule — UNAVAILABLE (variant B only); holiday tables — SYNTHETIC_TEST_ONLY;
  session/DST clocks — implemented (zoneinfo DST real; wall-time session labels
  SYNTHETIC_TEST_ONLY defaults, so predicates must use named zones); finer-than-
  1h data — UNAVAILABLE and out of initial scope, declared honestly.
- **Prohibited shortcut check**: none apply (no indicator grids; no volume
  used; no rates used, so the carry-from-today shortcut is inapplicable;
  windows and placebo fixed from documented fixing times before any PnL —
  no post-hoc session filter; executable sides required, midpoint is
  DIAGNOSTIC_ONLY).
- **Ancestry statement**: first-cycle proposal; not a rescue of any previously
  rejected family; no other lane read. Clock-based exposure is generic, but the
  mechanism (benchmark-fixing price pressure, financing-hour liquidity
  provision, DST-real named-zone clocks, 24/5 structure, fixing-window spread
  and charged-roll cost objects) is FX-native and new to this repo.

## Feasibility statement

Feasibility-blocked at selection as things stand: real bid/ask history and the
PIT fixing-convention history are UNAVAILABLE, and the swap-schedule authority
needed for the roll-through variant is UNAVAILABLE. Proceeds only if the owner
explicitly authorizes those sources. This proposal never claims or implies the
data exists.
