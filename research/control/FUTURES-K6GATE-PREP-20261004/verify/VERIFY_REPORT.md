# VERIFY_REPORT — lane VERIFY, round FUTURES-K6GATE-PREP-20261004

- Verifier: fresh-context independent verifier (audit only; repaired nothing; ruled nothing).
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep`, branch
  `prep/futures-k6gate-20261004`.
- HEAD at verifier start (single `git rev-parse HEAD`):
  `3645edd037579313a0c51f9ba165da17a38435db` — the committed wave-1.
- Zero network. Zero PnL. All claims re-measured from bytes; python = root
  `.venv` read-only. Locks inspected before the heaviest reads: `FREE_PROVEN`
  (no registry row, lock not flocked).
- Write boundary: only `verify/` (excl. the read-only PACKET_05e54939_CHECK/)
  + `dispatch/handoff_VERIFY.json`.

## Git evidence log (all read-only; every command disclosed)

| # | Command | Result |
|---|---|---|
| 1 | `git rev-parse HEAD` (start, once) | `3645edd037579313a0c51f9ba165da17a38435db` |
| 2 | `git status --porcelain` (start) | `?? …/synth/SHORTLIST_STALE_COST_ERRATUM.md`, `?? …/verify/` (both are the post-wave-1 controller/verifier artifacts) |
| 3 | `git diff --stat 05e54939 3645edd0` | 35 files, **all** under `research/control/FUTURES-K6GATE-PREP-20261004/**` (+83,134 lines) |
| 4 | `git diff --stat 05e54939 3645edd0 -- research/control/FUTURES-ES-V1-PACKET/ research/control/FUTURES-SIX-ADOPT-PREP-20261004/ research/control/FUTURES-TEN-HYPO-PREP-20261004/ research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/ research/control/FUTURES-SIX-READINESS-20261004/ research/control/FUTURES-OVERNIGHT-PREP-20261003/` | **EMPTY (exit 0)** — SPEC / six-adopt / ten-hypo / six-gate / readiness / overnight dirs zero-diff |
| 5 | `git status --porcelain` (end) | unchanged from start (same 2 untracked entries; nothing staged/committed by this verifier) |
| 6 | `git -C <futures-six-gate>/prep rev-parse HEAD` (E2, read-only) | `05e5493971116eec8db5ea49e30c06930e8cc6bc` — unchanged |
| 7 | `git -C <futures-six-gate>/prep status --porcelain` (E2, read-only) | **EMPTY** — clean; the six-gate round stands byte-identical to its committed state |

Non-git reads: the four lane gate docs + all machine JSONs, the owning family
docs (ESNQ_HYPOTHESES, HYPOTHESES_ESNQ_R3, JPY_AUD_HYPOTHESES, HYPOTHESES_R2,
PB2_ANCESTRY_COURT_DRAFT), the committed inputs (cache_v3 parquets, ES panel,
6E/6J caches, es_expiry_recheck.json, ES_fomc_stats.json, NQ_a4_events.json,
6a_roll_measured.json, 6J_a2_sessions.json, 6E_a1_regimes.json, FEES via the
lane's own tables), the Fed statements archive (147 files, read-only parse),
and the sibling six-gate worktree shortlist/synth files (read-only). Heavy
single-shot parquet reads preceded by `researchctl.py locks inspect` →
FREE_PROVEN.

---

## A. Zero-PnL / anti-cherry-pick law

| Check | Method | Result |
|---|---|---|
| A1 forbidden-statistic terms | grep `expectancy|hit_rate|sharpe|profit_factor|cagr|positive_pnl|total_return|cumulative_return` over all round .md/.json/.py | **PASS** — every hit is a negation/law statement (zero-PnL declarations, dispatch class text). No hit-rate/sharpe/PF/CAGR anywhere. |
| A1 signed-return leakage | key-space scan of all lane JSONs (`*ret*|*sign*|*dir*|*net*|*pnl*`) + compute-script read | **PASS with 1 MINOR finding (V-1)** — NQ m2 (`m2_expwitch_anatomy_v3.json`) and ES m1 (`es_k6_gates_results.json` M1 block) are clean: only `absret*` magnitudes and gap magnitudes (`median_abs_gap_bp`, `p90_abs_gap_bp`). The NQ **M4** a1-recipe mirror carries signed-derived aggregates — see V-1. |
| A2 §0 PREDECLARATION present + quotes | read all 4 lane docs; verbatim grep of cited family docs | **PASS** — NQ §0 (§0.1-§0.6), ES §0 (§0.1-§0.8 incl. the pre-verdict §0.8 amendment), FXEB §0 (0.1-0.7), FXJA §0 (§0.1-§0.7), each quoting owning-family K6 definitions with file+section. **Six** quotes verified verbatim (more than the 3 required): F1-K6 @ `ESNQ_HYPOTHESES.md` L211-214; F2-K6 @ L313-317; F5-K6 @ `HYPOTHESES_ESNQ_R3.md` L313-320; K3 @ `JPY_AUD_HYPOTHESES.md` L190+; D-2 @ `HYPOTHESES_R2.md` L472; court trigger + ≥500 census gate @ `PB2_ANCESTRY_COURT_DRAFT.md` L271/L279. |
| A3 FAILs not re-tuned | read verdict sections; grep re-tune language | **PASS** — ES T3 1.220 < 1.25 reported **FAIL** with margin −0.030 and "NOT re-tuned post-hoc… Re-adjudication of the operationalization is an owner decision" (ES_K6_GATES §1; es_k6_gates.json L123; handoff_ES-K6 L40). NQ 35/66 phantom-gap FAIL reported **FAIL** with the ordinary-Friday 46/80 diagnostic explicitly marked post-hoc/non-adjudicating (NQ §2). Every "re-tun*" hit in the round is a negation. F4-K6 NOT_RUN disposition is written in §0.5 as a pre-compute decision ("Disposition decided BEFORE compute (recorded here, not after)"). |
| A4 no family/parameter change | grep adjust/switch/relax/lower-threshold language | **PASS** — no result changes any family or parameter; synth §2 table keeps every scored-side blocker standing; D8/D9/PB2/PB3/cap-24 all explicitly unlifted. |

**V-1 (MINOR).** NQ M4's a1-rebuild output (`nq/nq_f3_rebuild_a1a2.json`,
mirrored verbatim from the committed `NQ_a1_regimes.py` recipe) contains
signed-return-derived statistics: yearly `ret_pct` (2020 = +38.43%),
`worst_day_pct` (−11.15%), `best_day_pct`, `skew`, `up_days_pct`,
`max_dd_pct`, `acf1_ret_full` (−0.0758 → −0.0857), variance ratios of signed
daily returns, `regime_trend_counts` (trend_up/trend_down labels from rolling
signed mean), and `drawdowns_ge10pct` (18 rows); NQ_K6_GATES.md §4 quotes
several of these. Under the strict A1 whitelist (|ret| dispersion + volume +
bar counts + gap magnitudes) these exceed it. Mitigations (why MINOR, not
worse): (a) they are unconditional series properties — no signal, no
conditioning, no PnL/expectancy; (b) they are **recipe-mandated**: the M4
deliverable is the verbatim rebuild of the family's committed a1 table and the
reconciliation against it (identical values in committed `6E`/NQ a1 class
artifacts); dropping them would break the very comparability M4 exists to
deliver; (c) no gate condition binds on any of them (M4 = descriptive, no
gate); (d) the lane's §6 zero-PnL statement explicitly declares "variance
ratios and autocorrelations of the held daily close series" as part of its
statistic set — disclosed, not smuggled. No CRITICAL/MAJOR signed-return
leakage exists anywhere in the four lane outputs.

**V-2 (NOTE).** FXEB M2 reports signed reopen-gap quantiles (6E p05 −0.034% /
p95 +0.031%, min −0.541% / max +0.241%; 6B analogous; per-era gap stds from
signed gaps). Strictly beyond "gap magnitudes", but the lane pre-declared
exactly this (§0.6(2): "Gap/trigger SIGNS are anatomy; no direction claim is
made or implied") and no verdict binds on sign. Descriptive, disclosed.

## B. Numeric spot-recomputations (independent re-derivations from primary inputs)

| # | Target | Verifier method (independent) | Lane value | Verifier value | Verdict |
|---|---|---|---|---|---|
| B1 | NQ M1 FOMC release-bucket era row | Parsed the cited statements archive (147 files; "For release at 2:00 p.m. E[DS][ST]" proof → 85 unique 2pm dates), rebuilt held-contract windows on cache_v3 with the §0.1 control string (same weekday ±21d, non-FOMC, held, cov ≥ 0.6), median of per-event h0_30 [780,810) volume ratios per era | 2023-26: 1.4559240576 (n=30); 2020-22: 2.2218896165 (n=23); 2016-19: 2.9867751050 (n=32) | **1.4559240576 (n=30) / 2.2218896165 (n=23) / 2.9867751050 (n=32)** — all three bit-exact | **REPRODUCED** |
| B2 | ES F5-K6(i) T3 W-60-full volume ratio | Rebuilt ES trade-date sessions from the 7,825,657-row outright panel (CT mapping, 17:00 rule → 4,204 sessions == lane census), W = committed 68/68 expiry calendar − 5 BLS-stacked, O = 2nd/4th/5th Fridays, cov ≥ 0.6 (390-min RTH-core), complex-summed per-minute volume in [15:00,16:00) CT, mean-over-sessions ratio | T3 1.220 (nW 19 / nO 128); T2 1.269 (20/131); W total 61, O total 432 | **T3 1.2204 (19/128); T2 1.2693 (20/131); W 61, O 432** — class sizes exact, ratios match to rounding | **REPRODUCED** |
| B3 | FXEB M1 6E 2026 census row | Held-contract prefix join on the 6E panel, London-local [08:00,11:00) envelope R_lon, [11:00,15:30) strict-outside trigger, warmup 60 held sessions (end 2020-03-25 ✓), ECB 55 ∪ FOMC 58 exclusions, ≥80% London-morning coverage | 2026: eligible 173, triggered 157 | **eligible 173, triggered 157** — exact | **REPRODUCED** |
| B4a | FXJA M2 6J mode split | Rebuilt the session×contract volume table from `6j_annotated_1m.parquet` over the committed 1,746-session k5 chain and re-ran the cease-guard variant semantics (no-bars ⇒ abrupt; k5 5-session rolling-mean crossover ⇒ gradual) | 19 abrupt / 8 gradual | **19 / 8** — exact | **REPRODUCED** |
| B4b | FXJA M2 6A split (cited) | Counted triggers in committed `6a_roll_measured.json:k5_cease_guard_variant.rolls` | 21 / 6 | **21 cease_guard_no_bars / 6 k5_crossover of 27** — exact | **VERIFIED** |
| B4c | 6J baseline == committed chain | Derived transitions vs `held_volume_k5.parquet` transitions | 27/27 dates and pairs; 2022-09-20 exemplar abrupt | 27/27; my simplified baseline walk reproduces 26/27 identically and differs only at 2022-09-20 vs 09-21 — exactly the no-bars session the lane's own disclosure documents (k5 crossover 09-21; cease-guard law switches at the 09-20 no-bars session). Consistent, not contradicting. | **VERIFIED** |
| B5 | FXJA M3 era cost arithmetic | Decimal recompute from named inputs: RT = 2×(2.46 + spread + slip) | era-1 $104.92 = 15.18 bp @0.6912; era-2 $54.92 = 8.20 bp (8.2019) | **$104.92 exactly = 15.1794 bp → 15.18; $54.92 exactly = 8.2019 bp → 8.20** | **REPRODUCED** |
| B6 | JF1-K3 label vs number | Read `jf1_k3_anchor.json` + the §0.2 pre-declared condition | ANCHOR_INSENSITIVE_AT_45MIN over −9.78 pp | W0 MPM range 34.6636 vs best(±45) 44.4456 (W−45); lead = 34.6636 − 44.4456 = **−9.782 pp < 0.5 pp** under the pre-declared convention ("W0's lead over both ±45 shifts < 0.5 pp ⇒ ANCHOR_INSENSITIVE_AT_45MIN"; leads over both shifts negative). Label, direction convention, and number are **consistent**; all 7 variants reported with identical per-variant statistics matching the md table | **CONSISTENT** |

## C. Reproduction discipline

| # | Target | Method | Result | Verdict |
|---|---|---|---|---|
| C1 | NQ M4 rebuild == `nq_held_daily_v3.parquet` | Independent rebuild: held chain ⟕ session closes → log-diff; seed-20261004 sample of 200 rows vs the readiness parquet, plus full-overlap check | sample max&#124;diff&#124; = **0.0** (ret and close); full overlap n = 4,218, max&#124;diff&#124; = **0.0** — matches the lane's claim exactly | **PASS** |
| C2 | 6J dispersion bar-identical to prior a2 | Per-session matched held-contract bar count from `6j_annotated_1m.parquet` vs `6J_a2_sessions.json` (`full/n_bars`) | **2,309,778 bars / 1,745 sessions** — exact equal on both sides; the "bar-identical, delta zero" claim holds | **PASS** |
| C3 | FXEB M3 6E court-sigma | Independent session close-to-close σ on the held-contract chain (last held bar per session), full era + eras | full-era **0.4682%** vs lane 0.4685% (Δ 0.03 bp ≈ 0.06% rel; last-bar tie-break nuance) vs court input 0.4639% (`6E_a1_regimes.json std_pct = 0.4638867`) — within the lane's "~1%" reproduction criterion (my Δ vs court +0.43 bp ≈ +0.9%) | **PASS** |

## D. Hygiene + laws

| Check | Method | Result |
|---|---|---|
| D1 stale-fee scan | grep `1.386&#124;21.006&#124;33.506&#124;46.006` + silent-default patterns over all round .md/.json/.py | **PASS — zero use-as-value.** Every hit classified: (i) law/erratum labels ("1.386-class glue never consumable", "1.386 forbidden") — FXEB_K6_GATES L19/L240, FXJA_K6_GATES L12, ES_K6_GATES L16/L592, es_k6_gates.json L320, DISPATCH_MANIFEST L21, handoff_FXJA L34; (ii) numeric coincidences in dispersion columns (`abs1m_ret_bp_p90 1.38630…`, `mean_absret_bp_w 1.38679…`, `std_ret_bp/median_absret_bp 1.3864-1.3868`, `nq_f3 1.3867e-06`) — bp-class statistics, not fees; (iii) the packet-check report's own findings quotes (allowed class); (iv) the SHORTLIST_STALE_COST_ERRATUM's verbatim quotes of the superseded lines (the correction itself). **No 21.006/33.506/46.006 value is consumed anywhere in the round.** Silent-default language: only withdrawal/law statements ("silent default withdrawn") and the packet check's historical quotes. |
| D2 handoffs | parsed all 4 | **PASS** — all `schema: zcode_orch_v3_handoff@1`; dispatch_sha == actual_start_sha == `05e5493971116eec8db5ea49e30c06930e8cc6bc` (bare 40-hex) in all four; commit_sha null in all four; NQ handoff carries the locks-inspect record (`locks inspect` → FREE_PROVEN before the M4 heavy job) plus the ret-series crosscheck record. |
| D3 wave diff scope | diff --stat + pathspec diffs (git log items 3-4) | **PASS** — 05e54939..3645edd0 touches only `research/control/FUTURES-K6GATE-PREP-20261004/**`; SPEC/six-adopt/ten-hypo/six-gate/readiness/overnight dirs zero-diff. |
| D4 write bounds + strays | lane dirs vs handoff-declared outputs | **PASS with 1 NOTE (V-3)** — es/ (5/5), fx_eb/ (5/5), fx_ja/ (9/9) contain exactly the declared files. nq/ contains the 10 declared files + `nq/__pycache__/` (2 .pyc compute byproducts, gitignored — V-3). No stray content anywhere; nothing written outside the round dir or the permitted verify/ + handoff paths. |
| D5 P3 quarantine strings | grep `futures-behavior` / `b583c33a` | **PASS** — single hit each, both in DISPATCH_MANIFEST.json L22, which is the quarantine RULE ITSELF ("absolute: no access to .worktrees/futures-behavior/prep (@ b583c33a)"). No access, no read, no path use anywhere else. |

**V-3 (NOTE).** `nq/__pycache__/k6_compute*.cpython-312.pyc` (2 files) sit in
the lane dir on disk. Gitignored (absent from `status --porcelain`), a
byproduct of the compile-check recorded in the NQ handoff. Not a declared
output; harmless; noted for tidiness.

## E. Erratum-chain closure (packet-check FAIL disposition)

| Check | Result |
|---|---|
| E1 verbatim match | **PASS.** Packet check F-4 names `shortlist/shortlist_6sym.json` L56 + `SHORTLIST_6SYM.md` L71; the erratum §1 rows F-4a/F-4b quote exactly those cells (re-read at the clean six-gate worktree: json `"cost": "S1 21.006 / S2 33.506 / S3 46.006 per side FROZEN Variant A (SPEC s5), binds until D3"`; md `**S1 21.006 / S2 33.506 / S3 46.006 per side FROZEN (Variant A)** — binds until D3 (SPEC §5)` — identical modulo the markdown emphasis characters the erratum strips). F-5: md L72 cell contains verbatim `armed n≈91 × tail-split with S2 33.506/side floor` == erratum F-5 quote. F-6: md L71 C7 cell `needs registration + prelaunch A7 (0 HIGH/CRIT) + typed owner GO` == erratum F-6a; json L58 `schedulability` likewise lacks the D3 signature; md L76 ESNQ-F5 `frozen variant default-binding` == erratum F-6b. Every erratum quote traces to the exact line the packet check flagged. |
| E2 append-only in effect | **PASS.** Six-gate worktree: HEAD still `05e5493971116eec8db5ea49e30c06930e8cc6bc`, `status --porcelain` EMPTY — the shortlist files stand byte-identical to their committed state. The k6gate wave diff (35 files) cannot and does not touch them (all paths under `FUTURES-K6GATE-PREP-20261004/`). Nothing was edited in the sibling worktree by anyone in this round. |
| E3 corrected values cell-for-cell | **PASS.** SHORTLIST_STALE_COST_ERRATUM §2.1 == COST_FREEZE_ERRATUM §2 table: A 2.25/side, all-ins **21.00/33.50/46.00** (RT 42.00/67.00/92.00); B 2.24/side, **20.99/33.49/45.99** (RT 41.98/66.98/91.98); stale print 21.006/33.506/46.006 NEVER consumable. §2.2 floor = **33.50 (A) / 33.49 (B)**, not 33.506 — matches the table cells. §4 keeps **CYCLE-1 = BLOCKED_COST_FREEZE** pending the D3 signature, explicitly "exactly as before", and the doc closes "ratifies nothing; keeps every gate closed". |
| E4 closure verdict | **CLOSED.** F-4/F-5/F-6 stand superseded by reference: the correction of record names the exact offending lines, restores the corrected values from the higher authority (COST_FREEZE_ERRATUM §2), preserves the status law, and binds downstream consumers to read the shortlist through the erratum. Nothing remains unclosed. |

**V-4 (NOTE).** The two erratum-chain artifacts — `synth/SHORTLIST_STALE_COST_ERRATUM.md`
and `verify/PACKET_05e54939_CHECK/**` — exist on disk but are **uncommitted**
at verification time (untracked in `status --porcelain`; the wave-1 commit
3645edd0 does not contain them). Their content is fully verified here;
committing them is the controller's per-wave pathspec commit step. Until that
commit lands, the correction of record is on-disk authority only.

## Findings ledger

| id | severity | finding | citations |
|---|---|---|---|
| V-1 | MINOR | NQ M4 a1-recipe mirror carries signed-return-derived statistics (yearly ret_pct +38.43% 2020, worst/best day, skew, up_days, max_dd, acf1_ret, variance ratios, regime_trend labels, drawdowns) — beyond the strict A1 anatomy whitelist; unconditional, recipe-mandated for the committed-a1 reconciliation, disclosed in the lane's §6 statement, gate-free | `nq/nq_f3_rebuild_a1a2.json` (a1.yearly / trend_persistence / regime_trend_counts / drawdowns_ge10pct), `nq/NQ_K6_GATES.md` §4 |
| V-2 | NOTE | FXEB M2 signed reopen-gap quantiles (p05/p95/min/max with signs) — pre-declared as anatomy ("gap SIGNS are anatomy; no direction claim"), no verdict binds on sign | `fx_eb/FXEB_K6_GATES.md` §2, §0.6(2) |
| V-3 | NOTE | `nq/__pycache__/` (2 .pyc) undeclared lane-dir residue, gitignored compile byproduct | `nq/__pycache__/` |
| V-4 | NOTE | Erratum-chain artifacts uncommitted at verification time (untracked; not in 3645edd0) — controller per-wave commit pending | `status --porcelain`, `git diff --stat 05e54939 3645edd0` |

## Round verdict

**VERDICT: VERIFIED — 4/4 lanes (NQ-K6, ES-K6, FXEB-K6, FXJA-K6) + synthesis +
packet-check-chain.** Every load-bearing number sampled reproduces from
primary inputs (three bit-exact recomputes, two exact-count recomputes, one
0.0-diff series match, one exact cost-arithmetic match, one ~1% dispersion
match); both EXPWITCH FAILs and the NQ 35/66 FAIL stand as reported with no
post-hoc tuning; F4-K6 is lawfully NOT_RUN; zero-PnL/zero-fetch/cost laws hold
(1 MINOR whitelist deviation V-1, disclosed and recipe-mandated); handoffs,
write bounds, wave-diff scope and the P3 quarantine are clean; the
packet-check FAIL is provably dispositioned by an append-only erratum whose
quotes and corrected values match their sources exactly, with the six-gate
round untouched at 05e54939. 0 CRITICAL, 0 MAJOR, 1 MINOR, 3 NOTE. Nothing
was repaired, ratified, or consumed by this verification; 0 trials scored.

— End VERIFY_REPORT.md (verifier output; audit only).
