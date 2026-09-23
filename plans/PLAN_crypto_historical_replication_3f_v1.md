# PLAN — CRYPTO-HISTORICAL-REPLICATION-3F-V1

> Owner directive 2026-09-23 (verbatim intent): backtest on OLD data the three
> families ILLIQ-AMIHUD-28D-W, XSECT-FUND-CARRY-7D, BASISLV-PREMFADE-28D to
> test whether the old results replicate on earlier market regimes. This is
> retrospective replication — NOT new-parameter search, NOT prospective
> evidence, and it does NOT change the historical verdicts of the three
> families. Survey target 2020–2024; probe 2019 separately. No scored cell
> before a fresh owner GO at this cycle's own gate.

Status: `PLANNED_NOT_STARTED` → registered `ACTIVE_LIGHT` 2026-09-23 (budget
0/24). **Amendment A1 (owner "xsect provenance", 2026-09-23): XSECT admitted
under the provenance equivalence gate with `EQUIVALENCE_PROVENANCE_ONLY`
labels (§5); fold law refined — primary folds Y2021/Y2022/Y2023 + fold-4
Y2020P-if-census-passes-else-Y2024P (§6); all three bootstrap open items
resolved (§11).**

## 0. Authority order and relationship to older laws

1. This owner directive (2026-09-23) is authority order #1. It explicitly
   orders public Binance data acquisition for 2020–2024 and a 2019
   feasibility probe. V12's "Do not fetch new network data" law
   (`plans/PLAN_crypto.md` §A3.6) was scoped to the V12 cycle and is NOT
   carried into this cycle by the new owner order.
2. The V13 reopening law (`plans/PLAN_crypto_v13.md`) — "The ILLIQ
   replication may re-open ONLY if an authorized window covering the frozen
   replication brief becomes available through such an owner decision; the
   frozen V12 brief is then executed unchanged. Window substitution remains
   forbidden." — is honored as follows: the owner decision is THIS plan; the
   family mechanics/parameters/universe/costs are executed UNCHANGED from the
   frozen authorities in §2; only the evaluation window is new and it is
   preregistered here BEFORE any PnL is seen. The V12 BLOCKED_DATA record
   stays BLOCKED_DATA; this cycle does not retroactively convert it into a
   run result (owner directive, explicit).
3. Forbidden-inventory note (PLAN_crypto_v16 §1 lists PREMFADE variants,
   carry families, owner-gated ILLIQ): this cycle is not a rescue under the
   doctrine because (a) every parameter is recovered byte-exact from the
   frozen authorities — nothing is re-tuned; (b) the historical verdicts
   `V11_FAMILY_REJECT` / `V14_REJECT_ALL` / `CANDIDATE_FAIL` remain the
   labels of record and are reproduced in every artifact; (c) the new trial
   identity is preregistered here; (d) all outcomes (including positive)
   remain outcome-exposed non-promotable candidates (PROSPECTIVE-SHADOW-V1
   §14 disclosure law applies to any future blind discovery).
4. PROSPECTIVE-SHADOW-V1 boundary: the shadow's plan contains no clause
   forbidding a separate retrospective cycle on the same family IDs. This
   cycle writes NOTHING under the shadow worktree, `results/` of the shadow,
   or `research/control/SANDBOX-OVERFIT-3ASSETS/`; it never restarts or
   retunes shadow workers; namespaces here are visibly
   `REPLICATION_NOT_PROSPECTIVE`. Heavy work takes the one machine-wide
   heavy slot; fapi request pacing (≤6 req/min, yielding windows) protects
   the shared egress-IP budget consumed by LIVE-DATA-GATEWAY-V1 and the
   shadow's direct fetches (the 2026-09-21 418 outage precedent).

## 1. Mission and non-mission

- MISSION: for each family, run the byte-exact frozen anchor form on
  preregistered EARLIER windows and report, per family and per fold: return
  %, PnL on the same 100,000-USDT notional baseline, trade count, gross price
  PnL, funding PnL, fees/slippage, net PnL, max drawdown, concentration
  (per fold/symbol/year), and results under frozen stress + a preregistered
  2.0× fee diagnostic.
- NOT the mission: parameter search, year cherry-picking after PnL, symbol
  pruning, cost changes, D2 conditions changes, shadow/paper/live promotion,
  orders, credentials, leverage.
- Positive outcomes are CANDIDATES requiring future validation only. They
  never resurrect the historical rejects.

## 2. Frozen identity authorities (recovered; byte-exact)

| Field | ILLIQ-AMIHUD-28D-W | BASISLV-PREMFADE-28D | XSECT-FUND-CARRY-7D |
|---|---|---|---|
| Historical family | `A8-V11-ILLIQ-AMIHUD` | `A14-V14-A5-BASISLV-PREMFADE` | `H-XSECT-FUNDING-CARRY-v1` |
| Identity authority | terminal commit `c97283e0d1681c24ee9a637a4fb1628d0334b7e1` (branch `orca/v11-integration`): `research/control/v11_run/selection_freeze_specs/A8-V11-ILLIQ-AMIHUD.json`, engine `research/v11/families/illiq_amihud/strategy.py`, digest factory `research/v11/publication_identity.py` | terminal commit `183554add4db82444d3e71beb24fb247c6b420b2` (branch `orca/v14-integration`): `research/control/v14_run/selection_freeze_v14.json`, engine `research/v14/families/basislv_premfade/strategy.py`, `frozen_identity.py`, `restage_basis.py`, staged manifest `d2_a9f/staged_basis_manifest.json` (sha256 `3867bdca…`), force-committed results `results/v14_phase_e` @ `a7a69d2b` | HEAD: `research/hypotheses/H-XSECT-FUNDING-CARRY-v1/candidate.yaml` + engine `research/funding_carry.py`; V6 closure addendum `research/wayfinder/evidence/v6-closure-addendum-20260825.{md,json}` (sha-pinned) |
| Mechanism | 28d mean daily Amihud abs(r)/quote-volume (15m→daily UTC); Mondays 00:00Z; long most-illiquid / short most-liquid quintile; EW, dollar- and BTC-beta-neutral (90d beta); holding 7d; exec lag 1 day | 28d mean perp-vs-index premium (15m buckets); Mondays 00:00Z; long low/discount tercile, short high/premium tercile; EW gross 1.0, per-symbol cap 0.30, MIN_ELIGIBLE 12; holding 7d; fill = close of first completed 15m bar after stamp (00:15Z); stress +1 event delay → 00:30Z | trailing mean of PUBLISHED SETTLED funding 7d; daily 00:00Z; long bottom-2 / short top-2; 24h rebalance; target gross 0.80, hard gross cap 1.00, hard abs-net cap 0.10, max abs symbol weight 0.20; universe ETH,SOL,BNB,XRP,DOGE,LINK,ADA (BTC benchmark only) |
| Universe (frozen staged sets) | 20 symbols: 1000PEPE,AAVE,ACE,ADA,AVAX,BCH,BNB,BOME,BTC,DOGE,ENA,ETH,LINK,NEAR,ONG,SOL,SUI,WLD,XRP,ZEC (BTC excluded as benchmark); PIT eligibility by listing + DV filter; `QUINTILES=5, MIN_ELIGIBLE=10` | 19 symbols (same set minus BTC); PIT eligibility; `MIN_ELIGIBLE=12`, terciles | the 7 fixed symbols; engine fails closed (skips cross-section) on missing data |
| Costs (frozen) | taker fee floor 5.0 bps, 1 adverse tick slip, native funding while held; stress = fee×1.5, +2 ticks, +1 event delay | charged on fills only; real perp-metadata tick sizes; native funding once per settlement; stress = ×1.5 / +2 ticks / +1 delay (V12-inherited law) | fees/slippage per V6 frozen adapter; funding = signal AND cashflow (settled only); stress = ×1.5 / +2 ticks / +1 delay |
| Frozen anchor digests | anchor `76729187a8a94980c08c30ae741a1ae0dd0e4da3d682037012ed7c04016fa8e0`; INV control `d4d32ed62153ae5c9cee69230fc35de92bed64fe560e80f1902cc90f505fc913` (selection_freeze.json) | anchor `8d7704663b923815e0bb2b201c339c9a2c209875c3348752c721d17265247d52`; INV `76f0b0ccba127cef85aa91ebaf4faa4d13fffd5130d2cf6f7e305f53aac46893` (frozen_identity.py) | candidate.yaml frozen caps; digests to be recomputed over the frozen payload at code freeze |
| Historical verdict (UNCHANGED) | `V11_FAMILY_REJECT` — PF 1.354841, net 0.581969, MDD 9.182%, 3/3 folds positive; FAILED single frozen gate `no_positive_fold_gt_50pct_of_positive_pnl` at 0.7055 | `V14_REJECT_ALL` — net +0.700216, PF 1.360047, MDD 11.585%, 3/3 folds; FAILED fold-share 0.5110>0.50; family DSR 0.00224 (N=146) | `CANDIDATE_FAIL` — net +20,580.87 USDT/100k, PF 1.1570, MDD 8.835%, funding +2,277.23; FAILED top-positive-fold 51.66%>50% |
| Historical window | 2025-08-22..2026-08-21 (folds F0/F1/F2) | blind-S0 2025-08-22..2026-08-21 (authorized data window from 2024-08-20) | near-one-year; **exact dates NOT recoverable from committed bytes** (see §5) |

Contradiction disclosures (summary docs vs frozen artifacts): the
FAMILY_FAILURES row for V11 says "symbol-concentration 0.7055" but the A7
terminal audit proves the frozen gate was positive-fold share 0.7055; the V11
`terminal_sha` cited in ledgers (`c97283e0`) predates the scored Phase-E
commits (`369a13fd`/`4160eec4`/`71b8ea3e`). Frozen authority wins: gate =
positive-fold share; baseline metrics are read from the audit commits.

## 3. Windows — preregistered before any PnL

Boundary law: replication windows must NOT overlap `[2024-08-20, 2026-08-21]`
(authorized/staged + scored S0 windows; V12 A3 non-overlap law). No window
substitution, no post-hoc year selection.

| Fold | Window (UTC) | Status |
|---|---|---|
| Y2021 | 2021-01-01T00:00Z .. 2022-01-01T00:00Z | registered, all families |
| Y2022 | 2022-01-01T00:00Z .. 2023-01-01T00:00Z | registered, all families |
| Y2023 | 2023-01-01T00:00Z .. 2024-01-01T00:00Z | registered, all families |
| Y2024P | 2024-01-01T00:00Z .. 2024-08-19T00:00Z | registered, all families |
| Y2020P | family-specific starts: XSECT 2020-10-05, ILLIQ 2020-10-26, BASISLV 2020-11-16 .. 2021-01-01T00:00Z | CONDITIONAL — runs only if the P0 full census proves EVERY scheduled stamp satisfies the frozen eligibility/eligible-count law; otherwise that family's Y2020P is `NOT_RUN_IDENTITY` with failing stamps listed |
| 2019 | — | `NOT_RUN_DATA` + `NOT_RUN_IDENTITY_UNIVERSE` (measured: ≤2 tradeable names; funding floor 2020-07-18; basis endpoint empty 2019-11) |

Warmup is drawn only from pre-window staged data (fold policy inherited from
each family's frozen contract; force-flat at fold boundaries). Y2023+
universe changes (PEPE/SUI/WLD/ONG/ACE listings during 2023) are handled by
the frozen PIT listing eligibility — no manual pruning either direction.

## 4. Data authority (P0 full census + staging, post-registration)

- Primary channels, pinned per family to match each frozen staging class:
  klines 15m via vision monthly zips (V15 stager precedent) with fapi REST
  cross-check per symbol-month sample; basis via `/futures/data/basis`
  PERPETUAL 15m (the V14 frozen signal route) + indexPriceKlines cross-check;
  funding via fapi `/fapi/v1/fundingRate` pagination (V8/V11/V14 precedent)
  with vision fundingRate monthly as cross-check only.
- Conflict policy (frozen now, fail-closed): if any cross-check disagrees with
  the primary channel (e.g., vision shows pre-2020-07-18 settlements fapi
  lacks; klines value mismatch beyond float-exact), the affected
  symbol-month is EXCLUDED from staging and the affected stamps/folds become
  `BLOCKED_DATA`/`NOT_RUN_DATA` with counts. No silent merging, no proxy
  substitution, no current-listing universe substitution, no spot/other-venue
  fills.
- Universe/listing PIT: measured first-archive month per symbol (P0 probe
  census) + 28d listing-age engine law; `onboardDate` used only as
  corroboration, never as authority.
- Storage: raw zips/parquets machine-local under
  `research/control/CRYPTO-HISTORICAL-REPLICATION-3F-V1/staging/`
  (gitignored); every downloaded byte sha256-pinned into a staged manifest
  committed as evidence. No credentials, no paid sources, no order APIs.
- Acquisition pacing: vision CDN requests ≥0.35s apart; fapi ≤6 req/min with
  yielding windows; the bulk basis staging (~6.4k calls, ≈18h) runs under the
  machine-wide heavy lock with etiquette windows so the gateway/shadow IP
  budget is never pressured.
- Delisting/holes: frozen PIT law governs; gaps become NOT_RUN counts, never
  interpolations.

## 5. Equivalence gates (P1 — BEFORE any scored cell)

Rule (owner directive): no scored cell on an engine that has not proven
equivalence on the ORIGINAL window. An equivalence FAIL is a STOP +
investigate, never a tolerance relaxation.

- ILLIQ: restage klines 15m + funding for 2025-08-22..2026-08-21 (vision
  monthly zips + fapi funding); run the frozen engine at `c97283e0` on the
  frozen folds; compare anchor cell against the A7-verified baseline
  (audit commit `71b8ea3e`, `research/audits/v11p/a7_terminal/a7_terminal_wave2.{md,json}`):
  net 0.581969254868, PF 1.354841010840, MDD 0.091821657373, fold PFs
  1.260/1.083/1.781, hit 24/52, 336 positions, fold-share 0.705496856297.
  Registered tolerance: canonical metric surfaces relative diff ≤1e-9 (same
  data values expected — the restage is the same venue data), fold PnL map
  exact. A mismatch beyond tolerance = STOP + investigate (e.g., REST-vs-zip
  bar provenance difference must be root-caused and disclosed before any
  scored cell).
- BASISLV: restage basis + index klines 2025-06-30..2026-08-21 via the frozen
  `restage_basis.py` path; sha256-verify every file against
  `staged_basis_manifest.json` (fail-closed on mismatch — would prove source
  revision drift and STOP the family); run frozen engine at `183554ad`;
  compare against `research/control/v14_run/terminal_report_v14.json`
  (net 0.700216130953, PF 1.360046671971, MDD 0.11585342564,
  price-only 0.011550403641, fold shares) at ≤1e-9 relative, fold map exact.
- XSECT (AMENDED A1, owner decision "xsect provenance" 2026-09-23 — supersedes
  the original NOT_RUN_IDENTITY default): output-equivalence on the original
  window remains IMPOSSIBLE (V6 launch manifests and `results/portfolio_v6/*`
  never committed; backup tarballs `legacy_root_data.tar.gz` sha `f116db23…`
  and `crypto-v14_full.tar.gz` sha `bd5f7528…` deleted from disk — verified
  against `research/control/staging_backups_manifest.md` and
  `~/staging_backups/`); prose reconstruction stays forbidden. XSECT is
  admitted under a **PROVENANCE equivalence gate**, all conditions fail-closed:
  1. `git diff fbd2e9d36b5349489ef29deec4cdeb8bca2b89ad..HEAD --
     research/funding_carry.py research/matrix_runner.py` EMPTY (kernel +
     matrix runner byte-identical since the audited V6 closure — measured
     2026-09-23);
  2. `research/hypotheses/H-XSECT-FUNDING-CARRY-v1/{candidate.yaml,status.yaml}`
     unchanged since the V6 closure era (last change `5b1415e7` lineage —
     measured 2026-09-23);
  3. independent identity recovery by the PROSPECTIVE-SHADOW-V1 P1 lane:
     `research/control/prospective_shadow_v1/identity/identity_recovery.json`
     @ `41f4f227` (branch `orca/prospective-shadow-v1-integration`), sha256
     `845c3e872fcea59d417e83878be79ec8112c197a61663173f24bf58e0cedbcd8`,
     with its recorded A7 identity cross-check PASS (0 HIGH/CRITICAL);
  4. frozen engine tests PASS (`tests/test_funding_carry.py` 5/5 — M0
     measured);
  5. executor disclosure (permanent): `research/portfolio_runner.py` changed
     since V6 closure (+815/−78) — XSECT replication cells run via a
     cycle-local driver importing the frozen kernel; the executor is NOT the
     V6 executor and this is disclosed on every XSECT record.
  LABEL LAW: every XSECT cell record, table row and report line carries
  `EQUIVALENCE_PROVENANCE_ONLY`; XSECT results are always reported as a
  LOWER evidence tier than the output-equivalence families ILLIQ/BASISLV.
  Any condition 1–4 breaking later = STOP for XSECT (fail-closed, no rescue).

## 6. Trial identity, arms, budget

- cycle_id `CRYPTO-HISTORICAL-REPLICATION-3F-V1`; namespace on every record
  `REPLICATION_NOT_PROSPECTIVE`.
- Arms per family: anchor + sign-inverted control (the frozen causal
  falsifier). The 56D neighbour is a mandatory diagnostic namespace in the
  ORIGINAL frozen identity but is NOT scored in this cycle (disclosed
  trial-mass reduction, decided pre-PnL); it may be added only by plan
  amendment before GO.
- Scored cell = (family, arm, fold) with base + frozen stresses (×1.5 fee,
  +2 ticks, +1 delay) + the owner-directed ×2.0-fee diagnostic reported
  inside the cell. Stresses do not consume extra trial identity.
- Cell matrix (AMENDED A1): PRIMARY scored folds per family = Y2021, Y2022,
  Y2023 + fold-4 = **Y2020P if that family's P0 stamp census passes, else
  Y2024P** (deterministic fallback, chosen now). 2 arms × 4 folds × 3
  families = **24 cells = the registered budget cap exactly**. The
  Y2020P-or-Y2024P choice is made per family BEFORE any of that family's
  scored cells run and is recorded with the census evidence. The demoted
  fold (Y2024P when Y2020P wins, or Y2020P when census fails) may be added
  later ONLY through a lawful budget-max increase + plan amendment, never by
  silently exceeding the cap. Stresses (×1.5 fee, +2 ticks, +1 delay) and the
  owner-directed ×2.0-fee diagnostic are reported inside each cell and do not
  consume extra trial identity. Every computed outcome counts in the OBSERVED
  denominator even if publication fails (P-9); dry-run and equivalence runs
  are zero-denominator. Exact-arm dry-run must show pairwise-distinct record
  IDs and zero denominator delta.
- Per-cell trial identity fields: cycle_id, family_id (frozen), arm_id
  (frozen), arm_config_digest (frozen, §2), window fold stamps,
  data_snapshot_digest (staged manifest sha256), code_freeze_sha (per-family
  terminal commit), cost_tier (frozen + stress list). Exact-arm dry-run must
  show pairwise-distinct record IDs and zero denominator delta.

## 7. Gate sequence

1. Registration (researchctl) + integration worktree
   `.worktrees/crypto-historical-replication-3f-v1/integration`, branch
   `orca/crypto-historical-replication-3f-v1-integration` from the wave SHA
   measured at registration.
2. M0: golden/identity/PIT tests of the recovered frozen engines (hand
   fixtures; no-lookahead mutation; cost-once; fold force-flat; fail-closed
   malformed data).
3. P0 full census + staging + per-symbol manifest (sha256 chain), stamp-level
   eligibility proof for the conditional Y2020P folds.
4. P1 equivalence per §5 (STOP on any FAIL).
5. Sanitized exact-arm dry-run: `scored=false`, `real_pnl=false`, no
   PnL/PF/stress fields at ANY record depth, non-vacuous, leak-scan
   recursive, IDs pairwise distinct, denominator delta 0.
6. A7 prelaunch, fresh context, independent (checks hashes, identity, PIT
   authority, accounting, dry-run hygiene, S1 seal, no post-freeze drift,
   denominator seed).
7. STOP — owner gate. Owner types the fresh exact phrase (§9) at this gate
   only.
8. Scored execution under heavy lock; per-cell post-run report (identity,
   exit code, runtime, denominators, gate verdicts, workers, S1 status);
   no early stop for bad results.
9. Independent reproduction (detached twin at the freeze SHA) + A7 terminal
   audit; two-half close (§32 handbook).

## 8. Reporting contract (after GO)

Per family × fold, on the same 100,000-USDT baseline: return %, net PnL,
gross price PnL, funding PnL, fees+slippage, trade count, MDD, concentration
(max symbol weight share / fold-positive share / per-year and per-symbol
concentration), and the stress rows (frozen ×1.5/+2ticks/+1delay and the
preregistered ×2.0 fee diagnostic). Cross-family comparison tables ONLY on
the common registered intersection 2021-01-01..2024-08-19. Negative results,
NOT_RUN rows, incidents, and the trial denominator are all reported. The
2020 partials are reported separately from full years and never merged into
annual aggregates. Conclusion language: which family replicates its historical
near-miss behaviour, which wins only in one era, which lacks data — with the
standing labels (REJECT/CANDIDATE_FAIL) preserved on every family.

## 9. Owner GO gate

After A7 prelaunch passes, the owner must type the exact fresh phrase:

```
GO CRYPTO HISTORICAL REPLICATION 3F V1 SCORED EXECUTION
```

A phrase typed before the A7 prelaunch artifact exists dies unconsumed; a
mis-typed phrase is refused and recorded; the GO does not survive a pause or
transfer to another cycle.

## 10. Terminal outcome vocabulary (decided now, incl. negative)

Per family: `REPLICATED_POSITIVE_EARLIER` / `NOT_REPLICATED_EARLIER` /
`MIXED_BY_ERA` (with the fold table) / `NOT_RUN_DATA` / `NOT_RUN_IDENTITY` /
`BLOCKED_EQUIVALENCE` / `BLOCKED_DATA`. Even `REPLICATED_POSITIVE_EARLIER`
does NOT upgrade a family: historical verdicts stand; the result is only
candidate evidence for a future owner-authorized validation path. No
shadow/paper/live promotion, no orders, no parameter edits after any PnL is
visible.

## 11. Open items carried into bootstrap (AMENDED A1 — owner decisions 2026-09-23)

1. XSECT: RESOLVED by owner decision "xsect provenance" — admitted under the
   provenance equivalence gate with `EQUIVALENCE_PROVENANCE_ONLY` labels
   (§5 amended); restoring `legacy_root_data.tar.gz` would additionally
   ENABLE output-equivalence and is still welcome (upgrade path, amend
   BEFORE PnL).
2. Y2020P conditional folds: REFINED fold law §6 — Y2020P is each family's
   PRIMARY fold-4 if its stamp census passes, else deterministic fallback
   Y2024P; the demoted fold is amendment-gated (budget cap 24 is exact).
3. Neighbour (56D) arms: RESOLVED by owner "mặc định hết" — excluded from
   scoring (diagnostic namespace only).
