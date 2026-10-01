# OWNER_PACKET_SUCCESSOR — on/off research program preparation (2026-10-01)

From DECISION_PACKET v2.1 (`615f43f4`) under your open-research steering.
Everything here is PREPARATION: no registration, no GO, no scored cell,
no S1, no orders, no reuse of PC12A headroom. Data lane (7-asset
unblock, branch `orca/pc12a-7asset-unblock-20261001 @8b8c24a5`) read
read-only, untouched.

## (1) Completed this session

- **Gating-vs-sizing decomposition** (GATING_VS_SIZING.md): the PC12A
  harm is a PARTICIPATION effect — skipped trades −$385.5k vs
  same-trade rescaling −$7.3k (2%) (convention-dependent split, DECOMP §8.3); **L6 cost guard alone = −$352,959
  (91.4% of USDJPY gate harm)**; E1 floor net +$17.3k; degradation/W
  gates never fired. Slate design budget therefore goes to the
  participation layer, not caps.
- **Rule slate** (RULE_SLATE.md): 12 docket hypotheses ranked by
  mechanism/coverage/overfit-risk (NOT exposed PnL); 3 flagged
  HIGH-RISK as visibly shaped on exposed folds (named). Selected 6-rule
  per-symbol slate with frozen decision-time triggers, anti-hypotheses,
  controls (always-on, leave-one-rule, ≥100-seed dwell battery,
  clock-shadow, cost stress, missed-winners + false-admission tables);
  budget ≤24 identities / ≤120 rows.
- **Successor plan draft** (SUCCESSOR_PLAN_DRAFT.md): full protocol —
  hypothesis IDs, frozen grids, LEARN-window law, PASS bars incl. the
  two governing additions (P-MW missed-winners, P-FA false-admissions),
  freeze→A7→GO chain, 12-asset expansion path.

## (2) Per-symbol status

| symbol | inference today | validation calendar | note |
|---|---|---|---|
| USDJPY | YES (703 trades) | M1-track **2029-09-26** (recommended) / 2028-12-23 max-credit | slate J1/J2/J3 |
| EURUSD, GBPUSD | YES | same M1-track | slate E1/E2/G1 |
| USDCAD, AUDUSD | TRAIN-only | **NOT_RUN** — no lawful H1/M1 calendar on file | needs collector decision |
| NZDUSD, USDCHF, XAUUSD, XAGUSD | NO | daily-track feasible TODAY (≈10 folds) **conditional on data-lane gates + your D-1..D-7** | 7 NEW-DAILY candidates |
| BRENT, WTI, NATGAS | NO | same daily-track condition (EIA dailies joined by the data lane) | roll/chain gates still open |

## (3) Owner decisions needed (each ONE action)

1. **Calendar track election**: M1-track (EUR/GBP/JPY slate, validation
   earliest **2029-09** — the honest cost of the burned folds) vs
   DAILY-track (7 new candidates, can start once data gates pass) vs
   BOTH in parallel. This is the pivotal scope decision.
2. **Data lane decisions D-1..D-7** (their owner packet, at their
   gate) — unblocks the daily track.
3. **USDCAD/AUDUSD collector decision** or accept permanent NOT_RUN.
4. **IBKR Activity/Flex statement** (optional, any time): measured
   commission/swap/slippage — upgrades every PROVISIONAL label.
5. Register the successor cycle (its own GO phrase lives in the draft
   plan §3.7; not consumable from this packet).

## (4) Standing boundaries

PC12A/EOSV2 TERMINAL with GOs DEAD — untouched. S1 SEALED. Exposed
folds permanently hypothesis-only. Heavy lock FREE (no contention with
the data lane). No eligibility/registry writes to beautify anything.
