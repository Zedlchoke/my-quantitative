# SKEPTIC_CHECK_V2 — fresh-context review of DECISION_PACKET.md v2 (2026-10-01)

Reviewer: fresh-context skeptic (read-only; this file is the single write).
Object: working-tree v2 of `research/control/terminal_review_2026-10-01/DECISION_PACKET.md`
(v1 = commit `fc26adf1`). All recomputation done with
`.venv/bin/python` against committed artifacts in
`research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/` (PC12A root evidence
landing), the PC12A lane worktree
(`.worktrees/portfolio-composite-12assets-100k-v1`), the EOSV2 lane worktree
(`.worktrees/ethusdt-open-search-v2`), `plans/CYCLE_REGISTRY.json`, and git.

---

## F-1 — BLOCKING — §2.3(a) "MEASURED MISSED PROFIT" is contradicted by the journals at the cited timestamps

**Claim under review (packet §2.3(a)):** "Cost-guard deferral during a rally —
MEASURED MISSED PROFIT. Week ending 2023-05-19 (fold 2): USDJPY-S026 DEFER ×4 …
B1 executed 4 fills that week. The frozen guard cap … deferred entries exactly
when the leg was earning — one measured contributor to the fold-2 −$208.8k gap."

**What verifies:** the DEFER rows are real and quoted verbatim — POLICY journal
`seq 4135`, `ts_decision_utc 2023-05-16T16:00:00Z`, `leg_id USDJPY-S026`,
`eligibility_state ON`, `blocked_reason_detail "L6 cost guard: trailing 28d
spend 2852.3954 >= cap 2836.97"`, `onoff_features.decision_count_trailing 503`,
`guard.cap_usd 2836.97`; exactly 4 DEFER rows that week (05-16 ×3, 05-17 ×1);
cap provenance verified (`diagnostics/stageb/LADDER.json`:
`p90_trailing28d_usd: 2836.97`; ORCHESTRATOR_LOG `p90: 2836.97`).

**What fails:** the economic attribution.
- B1's only USDJPY fills at the deferred timestamps are the 2023-05-16
  17:00 OPEN (+10,000, cash −1,365,980.35) and 18:00 CLOSE (−10,000, cash
  +1,363,789.65): round-trip cash sum **−$2,190.70** — the "deferred entries"
  **lost** money in B1, they did not earn. The guard avoided a small loss here.
- Of the "4 fills" B1 executed on USDJPY that week, POLICY executed the same
  05-18 14:00 OPEN and 05-19 07:00 CLOSE itself (identical du/cash), so only
  the losing 05-16 round trip is B1-exclusive. (B1 also traded GBPUSD that
  week: 6 fills total.)
- The week's measured divergence (POLICY −9,605.41 vs B1 +40,282.41 weekly
  equity; USDJPY legs −9,572.33 vs +40,367.53; diff −49,887.81) traces to the
  different carried size (POLICY 19,384 vs B1 20,063 units from 05-12) and
  POLICY's 05-18 13:00 close — i.e. mechanism (b) path/size divergence, not
  the cost guard. B1's +$40.4k week comes from mark-to-market on exposure
  POLICY's path did not hold, not from the deferred entries.
- The "missed profit" reading is exactly the counterfactual class the packet
  disclaims two paragraphs later ("NOT established … that any different on/off
  pattern would have improved the result"). As written, a [M] headline asserts
  a mechanism the cited outcome rows contradict.

The fold-2 gap (−208,827.50) and the week's contribution to it are real; the
attribution of that contribution to the deferral is not. This is the flagship
new content of owner-fix (1); a false "MEASURED" label here is commit-blocking.

## F-2 — MINOR — §2.3(b) "no BLOCK/DEFER that week" is false as stated

Week 2024-11-04..08: POLICY journal contains **5 BLOCK rows**
(VC2-LVNFAIL-EURUSD ×2 on 11-04, USDJPY-S003 ×1, USDJPY-S002 ×2), and B1
executed the VC2-EUR round trip POLICY blocked (B1 EURUSD OPEN −10,000
@16:24 → CLOSE @19:54; EURUSD weekly divergence −113.14). The true statement
is scoped to the trading legs: USDJPY-S026 9/9 decisions ON and S014 4/4 ON
with no BLOCK/DEFER (verified), and the week's −114,237.98 divergence is
−114,124.85 USDJPY + −113.14 EURUSD + 0.00 GBPUSD. Sizes verified exactly
(POLICY −19,384/+10,000 vs B1 −4,684/−10,000/+22,591). Mechanism conclusion
survives; the absolute sentence does not.

## F-3 — MINOR — §2.1 "fold 0 is byte-identical" overclaims

Journals are NOT byte-identical in the fold-0 window: POLICY 1,823 rows vs B1
1,956 (SWAP rows 963 vs 1,096; HEADER meta/run_id differ). What IS identical:
every `per_fold[0]` metrics field (net 541,483.955558, DD 64,855.272619,
n_fills 390, full cost bill), all 389 fold-0 NET_ORDER rows, and all
per-symbol fold-0 records. "No gating or size divergence occurred" is
supported (no POLICY BLOCK rows in fold 0; both arms DEFER 15× under the
shared guard), but "byte-identical" should be "fold-0 outcome records
identical (identical fills; no policy-layer gating)".

## F-4 — MINOR — §2.3(c) cites "(per-symbol fold records)" but the printed numbers are the pooled per-fold DDs

+$102.0k (fold 1) = 350,066−248,114 = 101,952 and +$120.2k (fold 6) =
306,777−186,610 = 120,167, and fold-7 63.4k/20.1k = 63,388/20,139 — all from
`per_fold` (pooled), matching §2.1's own table. DDs derived from
`per_symbol_fold_records.friday_equity` give 101,842 / 121,988 instead. Fix
the citation (or the numbers) — do not leave a source pointing at values it
does not produce.

## F-5 — MINOR — §7 corr-3 attributes to v1 a quote v1 does not contain

'v1: "7/12 leave-one-leg removals break"' — `git show
fc26adf1:…DECISION_PACKET.md` contains no "7/12", "removal", "isolation" or
"leave-one" text. The phrase lives in the cycle's own artifacts:
`SESSION_REPORT.md:179` ("7/12 leave-one-leg breaks") and
`TERMINAL_DECISION.md` ("P8: 7/12 removals break the coalition"). The
correction's substance is right and verified — `run_scoredc.py:384-385`
(worktree copy) is exactly the P8 isolation loop (`arms.append(_arm(
f"POLICY_MO_{lid}", legs=[lid]))` and the B1 twin), and TERMINAL_DECISION C-1
confirms both readings FAIL with close code `P8_COALITION` — but §7 must not
present a v1 quote that is not in v1. Re-attribute (e.g. "v1 inherited the
cycle's P8 line ('7/12 removals break the coalition', TERMINAL_DECISION) …").

## F-6 — MINOR — §9 cites `6f9dfd52…` as a precedent "on main"; it is not on main

`git merge-base --is-ancestor 6f9dfd52 main` fails — 6f9dfd52 exists only on
the lane branch `orca/btc-combo6-scored-v1-integration` (it is the lane half
of the BTC-COMBO6 two-half close). The root-main half is `659f76e2`
("BTC-COMBO6-SCORED-V1 two-half close (half-2, root): TERMINAL
COMBO6_NO_INCREMENTAL_VALUE @6f9dfd52"), which IS an ancestor of main. The
conformity argument survives with the correct id; cite `659f76e2` (root half)
and/or describe `6f9dfd52` as the lane half referenced by it.

## F-7 — INFO — two 1-cent display artifacts in the §2.1 harm column

Fold-3 harm shown −3,099.97 (exact −3,099.975339 → −3,099.98) and fold-6 shown
−79,259.30 (exact −79,259.305179 → −79,259.31): consistent with differencing
the displayed 2-dp values. Everything else reconciles exactly: Σ POLICY
603,340.60 = pooled to the cent (diff 0.0000), Σ B1 688,604.03 = pooled, Σ
harm −85,263.43, Σ fills 2,436/2,363 = pooled n_fills_total, Σ-row DDs
418,228/397,157 = pooled max_dd_pooled_usd (note: pooled max DD, not a column
sum), all windows match `test_window`. USDJPY −87,201.39 per-asset harm exact;
"$21.4k more costs" = 21,422.01 exact; "ENTIRE net harm is USDJPY" correct
(EURUSD +1,714.26, GBPUSD +223.70).

## F-8 — INFO — §2.2 per-leg "decisions" list is POLICY-journal decision-row counts; arm unstated

All 11 values (1,891 / 490 / 288 / 238 / 94 / 56 / 30 / 20 / 10 / 4 / 3)
match the POLICY journal DECISION-row counts per leg exactly (total 3,124).
They differ from `metrics.json per_symbol…legs[].decisions` (3,467-style,
all-decision universe incl. B1, where the same legs show 78/74/42/47/83/126).
State the arm and the counting basis ("POLICY-journal decision rows") so the
two countable quantities are not conflated.

## F-9 — INFO — §6 verbatim-row discipline

All quoted fields match `LEG_RESOLUTION_MATRIX.tsv` exactly (gids, tiers
T3_PARK, labels PRIOR_NOT_SCORED ×2 / FAMILY_HISTORY_NEGATIVE ×5, class
NEW-DAILY-CANDIDATE ×7, probe_assets NZDUSD / XAUUSD / XAUUSD / NZDUSD;USDCHF
/ USDCHF;NZDUSD ×3). Two presentational notes: (i) the header sentence lists
9 columns but rows quote a subset (family/horizon omitted on several rows) —
every shown value is verbatim, but "rows quoted verbatim" implies more; (ii)
row 3's note is a light paraphrase ("crisis-alpha switch, VIX(>30) already
evidenced" vs TSV "crisis-alpha tail switch: VIX(>30, already evidenced)…"),
row 2's note quote is a verbatim substring. All status numbers verified:
span 2020-10-02→2026-09-30 with 0 holes >5d (hole_rule quoted in freeze),
spreads p50 0.8822→"0.88bps" and 4.5124→"4.51bps", XAU `abs_basis_p50_bps`
3.2462→"3.25bps", PIT `ASSUMED_NEXT_BUSINESS_DAY (NOT_MEASURED)`, basis
acceptance `NOT_RUN_THRESHOLDS_UNFROZEN`, `M1_H1_panels … NOT_RUN_SIZE_CAP`,
interior gaps NOT_RUN, 131/131 raw hashes DV-verified, exactly 7
NEW-DAILY-CANDIDATE rows (150+128+9+7=294), zero XAGUSD rows, XAGUSD identity
frozen. TB design file (`triple_barrier/INVENTORY_AND_DESIGN.md`, 531 lines):
76 configs (line 24), 18 nodes/family (line 337), 57-row ceiling (lines 350,
478), SL-first law (line 373), A-TREND/VOLPROF exclusions (lines 423, 430),
§2a TB-LABELS firewall (lines 221, 240) — all present as claimed.

## F-10 — INFO — verified clean (no action)

- **§5 calendar law:** `campaign/BACKTEST_CAMPAIGN_DESIGN.md` §3 "≥6 test
  folds or NOT_RUN_INSUFFICIENT_CALENDAR"; 8 test folds × 26w consumed by the
  scored run (metrics.json), sealed 26-week tail = 1 fold-equivalent < 6.
  Rank-2 "labels-only … makes NO claim" honest; ranks 1/3/4/5 all NO. Rank-3
  unambiguous: "on the burned calendar it is unlawful", "fresh panels only",
  "NO — no lawful folds exist today" (fix 5 satisfied; §6/§8 wording
  consistent).
- **§4 seven-deaths:** all 7 enumerated cycles TERMINAL in
  `plans/CYCLE_REGISTRY.json` with the exact close codes quoted
  (JEV_NO_INCREMENTAL_VALUE / NO_REGIME_STRATEGY_INCREMENTAL_VALUE /
  PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE / ROUTER_STATES_THIN /
  COMBO6_NO_INCREMENTAL_VALUE / POLICY_NO_INCREMENTAL_VALUE /
  NO_INCREMENTAL_VALUE); REGIME-GATED-COMBO-V1 is ACTIVE_LIGHT — correctly
  excluded. Narrowed wording matches the enumeration (4 routers + 1 combo +
  1 risk-policy + 1 breadth-gate).
- **§7 corr-1/corr-2 faithful and verified:** v1 really said "the 12
  diagnostic legs' raw carry was real" and "now fully adjudicated"; DSR 0.0002
  (TERMINAL_DECISION), 150→62→12 (TERMINAL_DECISION chain of custody),
  294 = 150 ALREADY-RUNNABLE + 128 STILL-NOT_RUN + 9 FUTURES-BLOCKED + 7
  NEW-DAILY-CANDIDATE (TSV class column), PROVISIONAL_PENDING_COST_AUTHORITY
  (FREEZE.md:48), NET_DEFAULT_COST (campaign design §4).
- **§3 EOSV2 numbers** match `scored/scored_summary.json`: B2 best
  +403,801.90, BASE_ALWAYS_ON_LONG +1,653,470.33, margin −1,249,668.43,
  TREND_LF +472,864.82, G5 fails exactly B1/B2/B4 (B3 True), 8 cells
  (A1–A4 NOT_RUN_THIN + B1–B4).
- **B4:** 128/128 seeded duty-matched arms beat POLICY objective
  (−2,449,821.71; worst seed −1,778,186.11) per B4_BATTERY.json.
- **Root-vs-worktree byte identity** of the four ARMS artifacts confirmed
  (sha256 equal).
- **§9 quotes:** AGENTS.md "Root checkout = bootstrap/owner space" exact;
  CLAUDE.md:30 "A1 is the sole integration, merge, central-ledger and
  publication authority" under "## Repository invariants" (line 25) exact;
  fc26adf1 exists (v1, current main HEAD).
- **No counterfactual on/off improvement is claimed anywhere** (§2.3
  explicitly disclaims and forbids); **LOSS_* taxonomy marked [NR]** and
  absent from both journals (grep 0); **per-leg PnL marked [NR]** with only
  per-leg activity measured. No GO/S1/scored/orders/push language violations;
  packet is preparation-only and says so; §1 registry heads c93123db…/
  857af951… match the registry. Minor §1 phrasing: "Root main @ cbd39395…
  (v1 packet at fc26adf1 on top)" — main now points at fc26adf1 (cbd39395 is
  its parent); harmless but worth re-wording when touching the file.

---

## Verdict

The six owner-demanded fixes are substantively present (harm tables recomputed
true to the cent; citations real; calendar law sourced; corrections faithful
in substance; boundaries held), but v2 introduces one new measured-claim error
(F-1) plus five citation-level defects (F-2..F-6).

**VERDICT: FIX_THEN_COMMIT**

Minimal edits (no renumbering, no restructuring):

1. **F-1 (required), §2.3(a):** replace the heading and last sentence with a
   form such: "**(a) Cost-guard deferral observed — rows verbatim, outcome
   NOT a missed profit at this citation.** … POLICY deferred ×4 (rows quoted);
   B1's corresponding 05-16 17:00→18:00 round trip closed −$2,190.70 gross,
   and POLICY itself took B1's 05-18/05-19 fills — so at this citation the
   guard deferred a round trip that lost in B1; the week's −$49.9k divergence
   (of the fold-2 −$208.8k gap) is dominated by the carried-size/path
   divergence of (b), not by the guard. No counterfactual on the deferral is
   claimed." (Or substitute a week where the deferred entries correspond to
   B1 winners, if one exists in the journal.)
2. **F-2, §2.3(b):** change "ALL policy legs ON (9× S026 ON, 4× S014 ON — no
   BLOCK/DEFER that week)" to "the trading legs were all-ON (9× S026 ON, 4×
   S014 ON, no BLOCK/DEFER on either); 5 BLOCK rows on dormant legs (S002/S003/
   VC2-EUR) contributed −$113.14 of the week's −$114,238".
3. **F-3, §2.1:** "fold 0 is byte-identical" → "fold-0 outcome records are
   identical (net/DD/fills/cost bill; identical 389 NET_ORDER rows; journals
   differ only in SWAP-row bookkeeping and header)".
4. **F-4, §2.3(c):** "(per-symbol fold records)" → "(pooled per-fold DDs,
   §2.1)" or recompute from per-symbol records and cite those values.
5. **F-5, §7 corr-3:** re-attribute the quote to TERMINAL_DECISION.md /
   SESSION_REPORT.md:179 (v1 contains no such phrase).
6. **F-6, §9:** "BTC-COMBO6 two-half close `6f9dfd52…`" → "BTC-COMBO6
   two-half close (root half `659f76e2`, lane half `6f9dfd52`)".
