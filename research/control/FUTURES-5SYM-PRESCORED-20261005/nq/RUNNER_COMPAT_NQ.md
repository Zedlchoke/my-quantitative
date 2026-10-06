# RUNNER_COMPAT_NQ — requirements the shared runner (exec/ lane output) must PROVE for NQ (acceptance checks for the wave-2 verifier)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **NQ**, 2026-10-05. DRAFT-PENDING-OWNER.
- Scope: the shared scored runner (the exec/ lane's deliverable — see the round's
  `exec/_upstream_scored_runner_spec.md`) must satisfy EVERY check below for any NQ identity to be
  runnable at a future registered cycle. **These are acceptance checks for the wave-2 verifier,
  not a claim that the runner satisfies them today (runner-side verification: NOT_RUN).** No NQ
  identity exists lawfully until SPEC_NQ's conditional-binding state clears (D9 + ceiling +
  clock-shadow reading + D3).

## RC-1 Contract-spec binding (identity arithmetic)

| # | check | must prove | evidence anchor to re-verify against |
|---|---|---|---|
| RC-1.1 | tick | NQ price step = 0.25 index pt; tick value **$5.00** used in every $ conversion (SL/TP distances, slippage, spread) | `SPEC_NQ.md` §1; `HYPOTHESES_ESNQ_R3.md` field 4 (sha256 `9dfe7b12…d288`); runner must REFUSE a $2.50/tick configuration (**P5-NQ4 defect guard**) |
| RC-1.2 | multiplier | **20 USD/pt** in all notional/P&L conversions; quote unit = index points | same cites |
| RC-1.3 | USD quote / point space | prices handled as index points; fixed-point 1e-9 ingestion per the D5 schema (`ts_event` = bar START) | `SPEC_PB1_ES.md` §1 schema law carried; cache_v3 panel schema |
| RC-1.4 | tick-constant regime | no era-branched tick table for NQ (contrast 6A D8 law — NQ has none and must NOT inherit one) | `esnq_hypotheses.json::cost_law` flat slippage (sha256 `68e21c56…6605`) |

## RC-2 Session masks (era-correct)

| # | check | must prove |
|---|---|---|
| RC-2.1 | era switch | session close = 16:15 CT through **2015-09-18**; **16:00 CT from 2015-09-21**; day boundary 17:00 CT; a mis-dated session mask ⇒ runner refuses the fold |
| RC-2.2 | era-A Friday class | era-A Fridays measured per-session by their own last minute (15:15 CT class), never asserted |
| RC-2.3 | DST law | fall-back Sundays keep the SUNDAY session_date for post-17:00 bars (absolute-24h quirk, 35 rows) — a DST-corrected "fix" in the runner is a **contract violation** |
| RC-2.4 | coverage law | RTH-core coverage = minutes-with-bar share 08:30 CT→era close; < 0.60 ⇒ session EXCLUDED from scoring, count disclosed |
| RC-2.5 | held-contract-only | every fill/anatomy consumes the held chain only (`held_volume_k5_v3`); cross-contract same-timestamp rows never enter a fill |

## RC-3 FOMC / BLS stamp injection (event PIT)

| # | check | must prove |
|---|---|---|
| RC-3.1 | FOMC standing-outside | every base-FOMC statement day (132 statements 2011–2026 incl. 40 untimed 2011–2015) EXCLUDED at day level; FOMCIN arms = inverse include set; stamps injected from the committed statement archive pointers, never from a live source |
| RC-3.2 | timed-event set | the 14:00-ET timed events resolve to **85** on cache_v3 (incl. 2020-04-29); a runner computing 84 is consuming a stale (pre-v3) event table ⇒ refuse |
| RC-3.3 | BLS vintage law | CPI/EMPSIT stamps keyed to the decision-date vintage (204+204 rows, 08:30 ET); canceled-but-expected days routed to their separate strata; current-calendar inference path must not exist in the runner |
| RC-3.4 | D5 pin | the 2026-02-13 CPI 08:30-ET embargo stamp present in any 2026-window evaluation configuration |

## RC-4 Cost-table binding at freeze

| # | check | must prove |
|---|---|---|
| RC-4.1 | frozen table only | the runner binds ONE cost table carried in the selection freeze manifest (per-side B 23.49/28.49/33.49 or A 23.50/28.50/33.50 per the D3 ruling); no re-derivation at run time |
| RC-4.2 | stale-print refusal | any appearance of 1.386 or the 21.006-class ladder in a config ⇒ hard refuse (`COST_FREEZE_ERRATUM.md` §1/§6, sha256 `cf83bc2d…9ae8`) |
| RC-4.3 | stress ladder | every identity evaluated at ×1.0 (gate number) and ×1.5/×2.0 (disclosed views); RT = 2 × per-side; A-window 2014-10-01→2017-12-31 reg handling correct |
| RC-4.4 | language law | outputs contain no "measured cost"/"complete cost" strings; VERIFIED_VS_ACCOUNT=NOT_RUN carried on every cost surface |
| RC-4.5 | fill law | fill = next 1m bar open after trigger; no limit/queue/BBO claims; same-bar TP/SL ⇒ SL priority; mandatory flat at era-correct close |

## RC-5 Fold routing

| # | check | must prove |
|---|---|---|
| RC-5.1 | fold map | F1 2010-06..2012-12 · F2 2013-01..2017-12 · F3 2018-01..2021-12 · F4 2022-01..2026-09, mapped onto cache_v3 span (first held session 2010-06-07); boundaries byte-frozen |
| RC-5.2 | warmup | 252 held sessions excluded at each fold head; warmup sessions never contribute scored statistics |
| RC-5.3 | fold×identity law | folds multiply evaluation views only — identity count is invariant across folds (per-identity fold vectors, never per-fold identities) |
| RC-5.4 | K-views | the six declared K-views (SPEC_NQ §6) are evaluation labels, never fold cuts, never identity splits |
| RC-5.5 | S1 seal | no fold, view, or identity touches the sealed post-freeze window; S1 path exists but is gated OFF at the runner level |

## RC-6 Identity-ID routing

| # | check | must prove |
|---|---|---|
| RC-6.1 | ID grammar | every run resolves IDs matching the frozen grammar `FBNQ1-*`/registered-token (`IDENTITY_BUDGET_NQ.md` §3); unknown IDs refuse; the enumeration in the frozen identity table is byte-exact at dry-run (probe R1/R2 precedent) |
| RC-6.2 | family routing | F1→FOMC stamps; F2→BLS stamps @07:30 CT anchor; F3→held daily series runs; F4→roll-week calendar + NEW-4 audit; shadow/ALW/FLAT controls route with their own machinery |
| RC-6.3 | dead-leg guard | the runner MUST refuse to instantiate any EXPWITCH-NQ identity (leg DEAD-AT-GATE) until a recorded owner data-plane ruling says otherwise (P5-NQ5) |
| RC-6.4 | budget counters | every instantiated identity increments the observed scored denominator (P-9 law); dry-runs touch zero counters |
| RC-6.5 | cache discipline | v2/pre-v3 cache paths (incl. `FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache/`) are refused as inputs — cache_v3 only (`DEPRECATION_NQ_V2_CACHES.md`, sha256 `29790cd1…16b0`) |
| RC-6.6 | gate wiring | G1–G9 + clock-shadow gate + K2 family-kill + NEW-4 construction audit computed per identity; gate arithmetic reproducible from the run ledger alone |

## RC-7 Verifier protocol (wave-2)

1. Static checks RC-1..RC-6 against the runner source + freeze manifest (no run needed).
2. One exact-arm dry-run rehearsal under ×1.0 (launch-draft §6.3): byte-exact identity
   enumeration vs the frozen table AND cost recomputation == frozen table; output quarantined
   descriptive-only; budget counters untouched.
3. Any check failure ⇒ NQ identities UNRUNNABLE (`BLOCKED_RUNNER_COMPAT_<check>`); never a
   mid-flight patch.

— End RUNNER_COMPAT_NQ. Acceptance law for the verifier; runner-side status NOT_RUN.
