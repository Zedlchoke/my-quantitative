# PLAN — SPORTS-PAPERTRADE-CAPITAL-V3 (capital law v3: 1%-equity stake, $500 open
# cap, WSL into the shared wallet/ledger/dashboard; PAPER ONLY; STOP before GO)

- cycle_id: `SPORTS-PAPERTRADE-CAPITAL-V3` · asset: shared · ACTIVE_LIGHT ·
  budget 0/0 scored by law (process amendment, no scored arms) · registered
  2026-10-10 (owner round-13 instruction, this chat).
- GO phrase (REGISTERED_NOT_CONSUMED, typed ONLY by the owner, verbatim,
  fresh, at this cycle's own gate):
  **`GO SPORTS PAPERTRADE CAPITAL V3 ACTIVATE`**
- Companion gate (WSL cycle, own phrase): **`GO WSL WINPROB PROSPECTIVE
  PAPER V1 BET_PAPER`** — registered by this round per AMENDMENT_R5
  (resolving ERRATUM_3's DECLARED_NOT_REGISTERED disposition); it may be
  typed only AFTER the phrase above is consumed (ordering law, §7).

## §0 Authority and supersession

Owner instruction 2026-10-10 round-13. This amendment supersedes, from its
effective instant, ONLY the capital parameters of ERRATUM_CAPITAL_LAW_V2
(fixed $5 stake; $100 open cap) and the WSL standalone-ledger scope of
AMENDMENT_R4_NEW_SCOPE_FREEZE §5. Everything else stands verbatim: EV gate
(p·d_eff − 1 − c ≥ 0.05, c = 0.02), drawdown pause (10% from peak), PIT
laws (T-6h anchors, quote freshness), quota caps, duplicate/one-decision
law, crosswalk fail-closed identity, settlement/refund taxonomy, append-only
ledger, one-flock in-lock rechecks, and every data-source rights law.

## §1 Stake law (v3)

1. `equity_cents(D)` at a decision = `WALLET_GENESIS_CENTS (100_000)` +
   Σ `SETTLEMENT.pnl_cents` over ledger rows — identical to the existing
   `PaperLedger.equity_cents()`; open (unsettled) bets contribute 0.
2. `stake_cents(D) = (equity_cents(D) + 50) // 100` — 1% of equity rounded
   HALF-UP to the cent at exactly .5 sub-cent. Example (owner's):
   equity 102,215c → stake (102,265)//100 = **1,022c = $10.22**.
3. Degenerate guard: `equity_cents < 100` ⇒ stake undefined ⇒ the decision
   is journaled `BLOCKED_INSUFFICIENT_EQUITY` stake 0 (fail-closed; the
   drawdown pause will normally have fired long before).
4. Applies at decision time to EVERY league (NBA/WNBA/men's-soccer/WSL)
   once activated; recorded stakes and decisions are NEVER edited
   (append-only; no backfill, no re-decision).

## §2 Open-cap law (v3)

1. `OPEN_EXPOSURE_CAP_CENTS` 10,000 → **50,000** ($500) — total unsettled
   stake across ALL leagues, one wallet.
2. Availability bound (new): an append is lawful only if
   `open_exposure_after ≤ 50_000` **and** `open_exposure_after ≤
   equity_cents` (never commit paper money the wallet does not have).
3. Both bounds are checked (a) in `evaluate_match` (pre-draft) and (b) in
   `in_lock_recheck` INSIDE the ledger flock against the reloaded on-disk
   tail immediately before bytes are written (S3 law of ERRATUM_CAPITAL_
   LAW_V2 carried verbatim). At the boundary: a decision that lands exactly
   AT $500 open is ACCEPTED; the next one is `BLOCKED_OPEN_EXPOSURE`.
4. Stake actually locked per bet = the full stake_cents incl. the PM taker
   fee inside the walked cost (fee-once-in-denominator law, R4 §3): the
   book-walk consumes exactly `stake_cents/100` USDC across asks+fees;
   `budget_short_usdc == 0` or the leg is `NO_QUOTE_DEPTH`. The stake is
   NEVER shrunk to fit depth.

## §3 Computation order per decision (normative; battery-pinned)

1. In-lock tail reload → `equity_cents` (settled PnL only).
2. `stake_cents = (equity + 50) // 100` (§1.2); degenerate guard §1.3.
3. For each of the three YES legs of the ONE Polymarket event:
   `walk_the_book(asks, budget_usdc = stake_cents/100)` — multi-level VWAP,
   `filled_shares`, `fee_total` (fee_i = 0.05·p_i·(1−p_i) per share,
   Sports taker law), `budget_short_usdc` MUST be 0 per leg.
4. Effective decimal per leg: `d_eff = 1/(avg_cost_per_share_incl_fee) =
   filled_shares / stake` — the R4 §3 per-share form
   `d_eff = 1/(ask + fee_per_share)` generalized to the multi-level walk
   (fee counted exactly once; c continues to cover residual slippage —
   R4 §3 verbatim). DATED NOTE 2026-10-10 (post-implementation, before A7):
   an earlier draft of this line also showed `stake/(stake−fee_total)` —
   that form is NOT identical and is DROPPED; the walk consumes the budget
   INCLUSIVE of fees (Σ p_i·sh_i + fee_i·sh_i = stake), which is the only
   form that reconciles R4 §3, §2.4 and §3.6 simultaneously. Enters the
   UNCHANGED EV gate `p·d_eff − 1 − 0.02 ≥ 0.05`.
5. argmax-EV leg; all existing gates in the existing order; cap/availability
   bounds per §2 with `stake_cents` (not a constant).
6. Row records: `stake_cents`, `equity_at_decision_cents`, `stake_law:
   "v3-1pct"`, walked fills + fee + depth shares, and for WSL the snapshot
   ids. Payout law: WIN ⇒ `pnl_cents = round(filled_shares × 100) −
   stake_cents`; LOSE ⇒ `−stake_cents`; VOID/PUSH/CANCELLED/
   POSTPONED_NO_RESCHEDULE ⇒ 0 (refund) — settled on the decision's OWN
   frozen stake.

## §4 WSL into the shared wallet/ledger/dashboard

1. ONE wallet, ONE shared ledger
   (`sports-papertrade-exec-v1/ledger/paper_ledger.jsonl`). The WSL
   forecast-only ledger (sha `dd8a501f…`, 3 rows) is PROVENANCE ONLY:
   forecasts may be cross-referenced, never imported as bets, never
   double-counted in equity or exposure. Its `guard_not_shared_ledger`
   stands for the standalone adapter; the SHARED-ledger WSL BET_PAPER path
   is owned by the exec runner (single wiring point) under this amendment.
2. Exec runner WSL lane (new, gated): fixtures from the program's own
   substrate; FORECAST rows written to the SHARED ledger via the byte-pinned
   frozen WSL engine (`109c3ec1…`, fidelity-proven port) and CROSS-CHECKED
   against the provenance ledger's row for the same fixture — any p mismatch
   ⇒ `BLOCKED_FORECAST_DISAGREEMENT` (fail-closed, never averaged).
3. Quote: Polymarket ONLY for WSL — three YES markets (Home/Draw/Away) of
   the SAME event, verbatim 90-minute resolution rules captured, NO(Home)
   never used as AWAY, mid/last/site-% never execution prices, snapshot
   fetched strictly before the anchor (append-only snapshots, cutover-prep
   data plane), `walk_the_book` at the §3 stake. The cutover prep's
   `polymarket_source.py` (sha `4b27ab17…`) is reused byte-pinned,
   stake-parameterized.
4. BET_PAPER for a WSL fixture requires ALL of: real open PM market of the
   exact fixture (1:1 join + kickoff consistency ≤3600s); three YES legs of
   one event; settlement law = 90-minute result verbatim; ask fills the
   FULL §3 stake (`budget_short_usdc == 0`); fee + depth recorded; valid
   pre-anchor snapshot; valid pre-anchor forecast (§4.2); every risk gate
   PASS incl. the §2 bounds in-lock; and the WSL cycle's BET_PAPER phrase
   recorded OWNER_GO_TYPED_LIVE in the registry (checked in-lock, the
   `b1r_switch_ts_verified` pattern). ANY miss ⇒ precise NOT_RUN_<reason>
   (NOT_RUN_NO_MARKET, NOT_RUN_MARKET_MISMATCH, NO_QUOTE_DEPTH,
   NOT_RUN_SNAPSHOT_STALE, NOT_RUN_RULES, BLOCKED_*…), never a synthetic
   bet, never a narrowed condition.
5. Dashboard: the live dashboard renders every WSL fixture from the shared
   ledger (forecast p×3, market/price/fee/depth/asks, decision + precise
   NOT_RUN reason, stake, PnL) and the SHARED equity/exposure — same
   per-request chain-verify law; the WSL standalone section artifact
   remains the provenance view until then.

## §5 Activation (two-key, inert-by-default)

The entire v3 path is DEAD CODE until BOTH:
(a) `config.json` carries `capital_law: {"version": 3, "effective_utc": …}`
    (absent ⇒ v2 behavior byte-for-byte — a pre-GO crash/restart cannot
    activate anything), AND
(b) the registry row of THIS cycle records `OWNER_GO_TYPED_LIVE` for the
    phrase in §GO (checked by the runner at start + per decision,
    `b1r_switch_ts_verified` pattern; missing ⇒ v2 law + loud journal).
Application post-GO (controller, journaled): apply the frozen patchset to
the core + exec branches, RE-SEAL `pins.json` (core sha advances; the WSL
adapter verifies via the same shared pins), add the config block, restart
under launchd, run the first-rows audit. `walk_the_book` gains the explicit
`budget_usdc` argument at every call site (it is already parameterized).

## §6 What does NOT change

EV gate + c; drawdown pause; PIT/anchor/cutoff laws; quota caps + HALT_KEY;
duplicate/one-decision law; crosswalk fail-closed; settlement taxonomy;
append-only chain + per-request dashboard verification; all data rights
laws; the PM watcher (read-only); the WC/Euro intake (config-only, its own
gate consumed); the PM-primary cutover for NBA/WNBA/UNL (still gated by
`GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER` — untouched); historical
rows/ledgers (byte-frozen); completed evidence of other cycles (historical;
post-activation re-runs disclose the delta).

## §7 Gate structure and ordering

- `GO SPORTS PAPERTRADE CAPITAL V3 ACTIVATE` — this cycle. Activates §1–§5
  program-wide from the consumption instant (prospective; no backfill).
- `GO WSL WINPROB PROSPECTIVE PAPER V1 BET_PAPER` — WSL cycle (registered
  by this round per AMENDMENT_R5). Lawful to type only AFTER the phrase
  above is consumed; until then a typed WSL BET_PAPER phrase dies
  unconsumed and the runner's in-lock WSL gate refuses.
- Neither phrase authorizes real money, order placement, purchases, or any
  source switch for NBA/WNBA/UNL.

## §8 Verification (before the gate)

Battery (sandbox ledgers; ×2 byte-identical runs) — ALL required:
T1 stake 1% as equity changes (settled PnL moves the next stake);
T2 cent rounding (½-sub-cent boundary pinned; owner example 102,215→1,022);
T3 multi-league shared cap counting (WNBA+NBA+soccer+WSL in one ledger);
T4 decision landing exactly AT $500 ACCEPTED;
T5 next decision beyond $500 BLOCKED_OPEN_EXPOSURE (in-lock, tail-reload);
T6 two concurrent decisions (flock serializes; exactly one proceeds);
T7 settlement WIN/LOSE/REFUND on a v3 stake (payout §3.6 rounding);
T8 postpone ⇒ stake released from open exposure;
T9 drawdown pause still fires (unchanged threshold);
T10 WSL missing market ⇒ NOT_RUN_NO_MARKET (no synthetic bet);
T11 WSL wrong/missing 90-min rules ⇒ NOT_RUN_RULES;
T12 WSL missing draw leg ⇒ NOT_RUN (never two-leg);
T13 WSL stale snapshot (fetch ≥ anchor) ⇒ NOT_RUN_SNAPSHOT_STALE;
T14 WSL depth < stake ⇒ NO_QUOTE_DEPTH (stake never shrunk);
T15 fee math exactness at a NON-$5 stake (vwap + 0.05·p·(1−p), d_eff);
T16 duplicate across leagues ⇒ BLOCKED_DUPLICATE_SELECTION;
T17 restart/idempotence (re-run writes nothing new);
T18 pre-activation ledger byte-unchanged (v2 path untouched while config
    block absent, incl. across a simulated restart);
T19 availability bound (equity − open) blocks before the cap would;
T20 WSL forecast disagreement (provenance vs shared) ⇒ BLOCKED_… (no avg).
Independent fresh-context A7 at the final head: verifies EVERY PASS path
and EVERY fail-closed path above, the two-key inertness (pre-GO restart
safety), pins re-seal correctness, ledger/dashboard invariants, and the
§3 computation-order conformance from code + traces.

## §9 Worktrees / boundaries

Integration `.worktrees/sports-capital-v3/integration` on
`orca/sports-capital-v3-integration`; the frozen patchset + battery live
THERE (candidate; the live exec/core worktrees stay byte-identical until
the GO — application is a post-GO controller act). Data plane
`~/.my-quantitative-data/sports-capital-v3/`. No push/merge; no edits to
other lanes' worktrees; heavy lock per law; $0; key bytes never in
chat/log/git.

## §10 Terminal outcomes (negative-first)

CAPITAL_V3_READY_PENDING_OWNER_GO (patchset + battery + A7 PASS; GO not
typed) | PRELAUNCH_BLOCKED_<gate> | NOT_RUN_* | TECHABORT_*. An
early/paraphrased GO dies unconsumed; the GO phrase is never typed by a
lane.
