# AUTHORITY_MATRIX — LANE-INTAKE, round FUTURES-5SYM-PRESCORED-20261005

- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`,
  branch `prep/futures-5sym-prescored-20261005`, HEAD measured at lane start
  `ffed828f73fa19fa0ff4aee3ac1b441909a43940` (== dispatch_sha). Machine twin:
  `authority_matrix.json` (same entries, same IDs).
- Scope: every decision / gate / ruling relevant to **NQ, 6E, 6B, 6J, 6A**,
  enumerated exhaustively from the committed rounds. Three buckets only:
  **(A) OWNER-APPROVED** (approving instruction/registration cited),
  **(B) PENDING-OWNER** (open slot + fail-closed default named),
  **(C) PROPOSAL-ONLY** (never signed; mere draft).
- Namespace law (dispatch `decision_namespace_law`): original IDs are cited
  unchanged; new IDs must be prefixed `P5-`. **This lane minted zero P5- IDs**:
  every open slot found in intake is already carried under an existing original
  ID (D1–D12, OD-1..OD-7, TEN-HYPO OD-1..OD-4, plus the recorded 6J BoJ-stamps
  slot); minting a P5- alias would duplicate, not add.
- Nothing here is authorization. This matrix is intake bookkeeping.

## 0. Round-level authorization frame (the only owner instruction in force for THIS round)

Owner instruction 2026-10-05 (recorded verbatim-quoted in
`../dispatch/DISPATCH_MANIFEST.json` `interpretation_law`, sha256
`f9e7b400dfec5c064494a16c7bec0494b08545caa4a95b4e84736174d999ca7a`):
authorizes **PREP + outcome-blind hypothesis research on the 5 symbols ONLY**.
Explicitly **NOT** a typed GO, NOT registration, NOT PB2/PB3 lift, NOT D8/D9
ratification, NOT any ceiling/cap signature, NOT fee-policy approval. Every
prior open decision stays open; fail-closed defaults bind. Absolute
prohibitions include: 0 scored runs / 0 strategy PnL, no outcome-computing
dry-runs, no S1, no P3-quarantined-capture reads, permitted calendar routes
only, one heavy job machine-wide.

Standing gates restated unchanged by every source round and still in force at
this HEAD (NOT reopened by anyone): `NO_GO_REGISTER / NO_GO_SCORE /
NO_GO_ORDER`; **PB2 HOLD** (6E/6B); **PB3 PARK** (6A); **ES cap 24 FROZEN**
(ES out of this round's scored scope; carried as context); fees MODELED COST /
`VERIFIED_VS_ACCOUNT=NOT_RUN` / UNDER REVIEW; BBO NOT_RUN everywhere (D5 law);
PIT vintage law (current-calendar inference forbidden); conservative fill law
(fill = next-bar open, close proxies only); `data-ready ≠ scored-authorized`;
P3-obtained captures quarantined, never read.

---

## 1. Bucket (A) — OWNER-APPROVED (in force; approving instrument cited)

| id | ruling / gate | who signed + approving instrument | what it binds (per symbol) | evidence path |
|---|---|---|---|---|
| A-1 | **NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER** standing gates | Owner standing rulings; restated unchanged in every committed round header (CYCLE_LAUNCH_DRAFT status line; SYNTHESIS_K6; IDENTITY_TABLES §0; TEN-HYPO packet header; SIX-READINESS census law line) | All 5 symbols: nothing may be registered, scored, or ordered; a GO exists only as the exact typed phrase `GO <REGISTERED-CYCLE-ID> SCORED EXECUTION` at the registered cycle's own gate (two-key law; GO_RECORDED precedent `DAILY-EXPLORATORY-V1/auth/GO_RECORDED.json` sha `ef88fd80…07df`) | `research/control/FUTURES-SIX-ADOPT-PREP-20261004/packet/CYCLE_LAUNCH_DRAFT.md` §7 (sha `bc2b6488…bcb03`); `research/control/DAILY-EXPLORATORY-V1/auth/GO_RECORDED.json` |
| A-2 | **PB2 HOLD** — 6E/6B program court | Owner standing ruling (program court); restated as absolute in dispatch `pb2_pb3` and by IDENTITY_TABLES §0.4, SYNTHESIS_K6, SIX-READINESS census | 6E, 6B: zero scheduled identities; FX options exist only as PB2-lift-conditional drafts (bucket C); K6GATE gates never schedule | `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/budget/IDENTITY_TABLES.md` §0.4 (sha `750858ab…f6e6`); `research/control/FUTURES-5SYM-PRESCORED-20261005/dispatch/DISPATCH_MANIFEST.json` |
| A-3 | **PB3 PARK** — 6A contingency-only | Owner standing ruling; restated by DATA_READINESS_6A header ("restated here, never reopened"), IDENTITY_TABLES §0.3 (0 budget, contingency lines only), FXJA_K6_GATES header | 6A: 0 registered budget; 26-identity contingency table (IDENTITY_TABLES) enters no cycle until owner unparks; readiness work is contingency-only | `research/control/FUTURES-SIX-READINESS-20261004/fx_ja/DATA_READINESS_6A.md` header (sha `28ea9093…9a8e`); IDENTITY_TABLES §0.3 |
| A-4 | **ES cap 24 FROZEN** + no-silent-raise absolute | Owner registration of PB1 parent family (SPEC_PB1_ES §6 table, 24 identities); dispatch absolute `no_silent_cap_raise` ("never silently to 43"); every ES count >24 = owner amendment only | ES only (context for this round): PB1-only slate lawful today, headroom 0; 43/60/67 are option arithmetic, never defaults; EXPWITCH-ES leg born-blocked and additionally DEAD at its F5-K6 gate | `research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` (sha `445f7499…b7073`, re-verified this lane); IDENTITY_TABLES §0.1/§3.3 |
| A-5 | **PREP-scope authorization 2026-10-05** (this round) | Owner instruction 2026-10-05, recorded as `interpretation_law` in the dispatch manifest | All 5 symbols: PREP + hypothesis research only; no scored run, no outcome-computing dry-run, no registration, no ledger/registry writes | `research/control/FUTURES-5SYM-PRESCORED-20261005/dispatch/DISPATCH_MANIFEST.json` (sha `f9e7b400…9ca7a`) |
| A-6 | **Fee A7 EXECUTION authorization** (2026-10-04) — execution half of D2 only | Owner 2026-10-04 instruction ("Giải các việc PREP được phép: dữ liệu, calendar, NQ cache_v3, cost/fee A7, PIT…"), recorded as written authorization to EXECUTE the audit (A7_FEE_REAUDIT §0; SIX-GATE packet interpretation ruling the owner may override) | All 5 symbols: the audit ran AUTHORIZED_WITH_FINDINGS, 0 HIGH / 0 CRITICAL unresolved (25/25 inputs byte-verified, 40/40 arithmetic, 37/37 validator grid). This authorizes the AUDIT ONLY — it is NOT a D2/D3/e.1–e.4 ruling; if the owner overrides the reading, artifacts stand as audit evidence and D2 stays open. No scored cell consumed anything (0 trials) | `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/fee_a7/A7_FEE_REAUDIT.md` (sha `2c1095d6…11ad`); `synth/OWNER_DECISION_PACKET.md` interpretation ruling |
| A-7 | **Databento av1trim purchase entitlement** — paid purchase approved by owner 2026-10-02 (ceiling $125, delivered $105.81, ledgered); consumed READ-ONLY by the readiness/adopt/k6gate rounds under that entitlement | Owner purchase approval 2026-10-02 (acquisition ledger, found by the VERIFY lane); D11 finding text | All 5 FX+NQ symbols: corpus `~/my-quantitative-data/futures-databento-av1trim` usable read-only for research. **Rights beyond read-only research (sharing, redistribution, derived products) = UNRESOLVED, fail-closed per D11** — any such use needs a fresh owner ruling first | `research/control/FUTURES-SIX-READINESS-20261004/dispatch/handoff_VERIFY-A7READY.json` (source-inventory verdict line); `synth/OWNER_DECISIONS.md` D11 (sha `d14e436f…ad93`) |
| A-8 | **Standing PIT / vintage law** — event calendars keyed to vintage as-of decision date; current-calendar inference FORBIDDEN everywhere | Owner standing ruling; restated in CYCLE_LAUNCH_DRAFT §2, all DATA_READINESS dossiers, P3-round Q4 normalization rule | All 5 symbols: every event-PIT cell; NOT_OBTAINED stamps are never inferred PASS | CYCLE_LAUNCH_DRAFT §2; `DATA_READINESS_6J.md` Dim 5 |
| A-9 | **Standing conservative fill law + BBO NOT_RUN (D5 law)** — single-level BBOMsg cannot prove fill/queue; fill = next-bar open, no limit/queue claims, close proxies only, SL-priority same-bar | Owner standing ruling (D5); restated in every cost dimension | All 5 symbols: cost dim 8 — BBO/fill/queue stays NOT_RUN on every symbol | CYCLE_LAUNCH_DRAFT §3; `DATA_READINESS_6J.md` Dim 6 |
| A-10 | **Standing language law** — MODELED COST everywhere; the words "measured cost"/"complete cost" forbidden on outputs; `VERIFIED_VS_ACCOUNT=NOT_RUN` labels | Owner standing ruling (D2 sphere); A7 step-7 scan: 0 positive uses, labels present in 12/12 fee-bearing files | All 5 symbols: every cost citation | `A7_FEE_REAUDIT.md` §7; CYCLE_LAUNCH_DRAFT §3 |
| A-11 | **P3-quarantine absolute** — P3-obtained captures (futures-behavior 0225b3c2 content / P3 lane artifacts) quarantined, never read; valid-result counts exclude P3 | Owner directive via FUTURES-P3-QUARANTINE-20261004 QUARANTINE_NOTICE (tip `b583c33a`, NOT in this branch's ancestry) + this round's dispatch absolute prohibition | All 5 symbols: any calendar cell that could only come from P3 captures stays NOT_OBTAINED/per D1 default | `../dispatch/DISPATCH_MANIFEST.json` absolute_prohibitions; `FUTURES-P3-QUARANTINE-20261004` commit message at `b583c33a` (not an ancestor — verified `git merge-base --is-ancestor` exit 1) |
| A-12 | **NQ v2-cache deprecation (in force, independent of D9)** — `FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache/` SUPERSEDED for all future consumption | Lane data ruling (ADOPT), standing via the D8/D9 sheet's fail-closed default: "no future cycle may consume the v2 NQ caches (deprecation stands independent of ratification)"; measured defects: 92,075-bar panel hole, dead-held 49 sessions | NQ: chain of record for any future build is cache_v3-or-successor only; v2 is append-only historical evidence | `research/control/FUTURES-SIX-ADOPT-PREP-20261004/adopt/DEPRECATION_NQ_V2_CACHES.md` (sha `29790cd1…16b0`); `D8_D9_DECISION_SHEET.md` fail-closed default |

Notes on bucket A: A-1..A-4, A-8..A-11 are owner-set standing rulings; A-5
is this round's owner instruction; A-6 is an owner-execution authorization
explicitly NOT covering the D2/D3 policy rulings; A-7 covers the paid purchase
and read-only research consumption ONLY (see D11); A-12 is a lane data ruling
whose binding force is codified as D9's fail-closed default (owner ratification
of the *positive* act — cache_v3 canonicalization — remains pending).

---

## 2. Bucket (B) — PENDING-OWNER (open decision slots; fail-closed default binds)

Original IDs preserved; source of record for D1–D12 is
`research/control/FUTURES-SIX-READINESS-20261004/synth/OWNER_DECISIONS.md`
(sha `d14e436f9110dd1a9f425ed1c0303d4acd77064344d1902cff26019fa1daad93`,
pinned identically by six-adopt packet §9); dependency mirror
`FUTURES-SIX-ADOPT-PREP-20261004/packet/open_decisions_dependency.json`
(sha `7229fd31…7327`).

| id | question | who must sign | fail-closed default (in force) | what it blocks (per symbol) | evidence path |
|---|---|---|---|---|---|
| D1 | P3 transport adjudication: accept-exception vs permanent quarantine (recommended default B) | Owner | P3-obtained cells stay quarantined; Q5 data usable only after per-use independent re-verify; P3 SNI-swap evidence forbidden | All 5 symbols: any cell whose only source is a P3 capture; Q5-derived cells carry the re-verify condition (this round's per-use re-verifies are recorded where used) | OWNER_DECISIONS.md (carried); FUTURES-P3-QUARANTINE-20261004 (out-of-ancestry tip `b583c33a`) |
| D2 | Ratify the fee A7 outcome + corrected-fee consumption downstream (4 sub-rulings e.1–e.4); execution half discharged by the clean A7 | Owner | All fees stay MODELED / `VERIFIED_VS_ACCOUNT=NOT_RUN` / UNDER REVIEW; no scored cell passes any cost gate; fee A7 remains audit-only | All 5 symbols: entire cost dimension (dim 8); prelaunch-A7 cost precondition | OWNER_DECISIONS.md D2; A7_FEE_REAUDIT §10 pending-slot table |
| D3 (= e.4) | NFA regulatory basis: Variant A (NFA 0.02 default; 0.01 only 2014-10-01→2017-12-31; fee 2.25/side; ES all-ins 21.00/33.50/46.00) vs Variant B (IBKR offset 0.01 throughout; 2.24/side; 20.99/33.49/45.99) | Owner — EXPLICIT signature REQUIRED, no silent default (old "silence ⇒ SPEC §5 binds" operating rule WITHDRAWN by COST_FREEZE_ERRATUM §3.4) | While undecided: both bases coexist and **no cost gate may consume either number**; CYCLE-1 `FUTURES-ES-PB1-V1` is **BLOCKED_COST_FREEZE**; **the stale SPEC print 21.006/33.506/46.006 (glued 1.386) is NEVER consumable** | NQ: NQ all-in table A 23.50/28.50/33.50 vs B 23.49/28.49/33.49 (spread/slippage per NQ cell) unusable for gating; 6E/6B/6J/6A: rides D2 (FX alias e.1 partial) | `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/synth/COST_FREEZE_ERRATUM.md` (sha `cf83bc2d…9ae8`) §2/§4; `K6GATE …/synth/SHORTLIST_STALE_COST_ERRATUM.md` (sha `7fe438c2…72a0`) |
| e.1 | FX fee-group alias mapping PARTIAL (generic CME "Forex Futures" row 1.60; 6E/6B/6J/6A never verbatim) — accept as tabulated? | Owner (may sign "accept as tabulated"; documented by A7, does not block an ES cycle) | PARTIAL mapping stands; FX fees stay MODELED/UNDER REVIEW | 6E, 6B, 6J, 6A: fee alias provenance | A7_FEE_REAUDIT §2 cell 4 + §10 |
| e.2 | Account-geography basis for the IB-JP paren (0.011 = 0.01×1.1 tax artifact; US-entity pages operative) | Owner | US-entity basis as tabulated by the A7 | Indirect (fee epoch interpretation), all symbols | A7_FEE_REAUDIT §10 |
| e.3 | NYMEX reg epoch rule (0.02→0.01 temporal window; historical-year modeling binding) | Owner | As tabulated by the A7 (epoch-binding question open) | Not this round's symbols (carried); fee-epoch hygiene | A7_FEE_REAUDIT §10 |
| D4 | ES trial denominator: 36 minimal vs 24 frozen (headroom 0) | Owner (any raise = signed amendment with exact arithmetic) | 24 frozen stands; all ES families BLOCKED_TRIAL_BUDGET; no permutation-robustness claims | ES only (context). 43-vs-60-vs-67 reconciled: different BASE, same increments; neither is a ceiling | IDENTITY_TABLES §0.1/§3.3; OWNER_DECISIONS D4 |
| D5 | CPI Jan-2026 announcement pin (permitted routes only) — **RESOLVED BY EVIDENCE 2026-10-04**: OBTAINED = Friday 2026-02-13, embargo 08:30 a.m. ET (USDL-26-0186; two independent official BLS artifacts) | (was owner slot; cell obtained — vintage law itself unchanged and stays in force) | n/a — pin in hand; remaining BLS vintage completeness still governed by the vintage law | Macro-conditioned arms on all symbols: the Jan-2026 CPI pin is consumable as FACT; vintage law unchanged | `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/cal_close/CAL_CLOSE_REPORT.md` (sha `338cf4e8…a56f`) §1 Obtained table |
| D6 | Remaining calendar cells (sibling list; non-mission symbols) | Owner (whether to fund/permit further extension) | NOT_OBTAINED stands; derivation forbidden | None of the 5 mission symbols beyond what D12 covers (carried siblings only) | OWNER_DECISIONS D6 |
| D7 | NG signed-surprise rule + comm data path | Owner | No NG/commodity arm exists in this cycle | None of the 5 (carried) | OWNER_DECISIONS D7 |
| D8 | 6A era-aware tick/cost law: Option A ratify measured boundary (era-1 2020-01-02..2020-11-20 = 1e-04 = $10.00/tick, 231 sessions; era-2 from 2020-11-23 = 5e-05 = $5.00/tick) vs Option B demand vendor/exchange document first (boundary stays PROVISIONAL; official rulebook BLOCKED_TRANSPORT) | Owner | **Era-2-only cost models may not back-cast into 2020-era windows**; any 6A cost spec lacking the era table is invalid for windows overlapping 2020-01-02..2020-11-20; era-1 RT 1-tick $104.92 = 15.18bp vs era-2 $54.92 = 8.20bp (MODELED) | 6A: every cost/spread/slippage model (REQUIRED spec element); any 2020-window 6A evaluation; PB3-lift contingency annex still also needs the lift itself | `research/control/FUTURES-SIX-ADOPT-PREP-20261004/adopt/6A_TICK_ERA_LAW.md` (sha `bd9c2011…7635`, PROPOSED label); `6a_tick_adjudication.json` (sha `06367e67…282d`); K6GATE `aud_d2_tickera.json` (sha `14426cfb…3729`) |
| D9 | Explicit cease-guard as standing chain-builder law + ratify NQ cache_v3 as canonical (3-symbol / 4-manifestation evidence: 6J 2022-09-20; 6A 2024-12-17 + 2026-06-16; NQ-v2-before NQH0_2020 49 dead sessions; explicit-guard variants 0 violations, roll dates identical except the two 6A switches 1 session earlier) | Owner | Per-cycle choice of guard; **cache_v3 stays canonical-CANDIDATE** (consumable only with explicit per-cycle citation of this packet, never as ratified canonical); any chain consumption must measure and disclose cease-guard violations first; v2 deprecation stands regardless (A-12) | NQ: scored path entirely (OD-3/SIX-GATE: "blocks every NQ scored path"); 6J/6A: RMM Role-B legs; chain-of-record status for NQ (6,780,608 rows / 66 rolls / 0 violations / PIT_CLEAN_BY_CONSTRUCTION) | `D8_D9_DECISION_SHEET.md` (sha `b1d6079f…f8ae`); `CEASE_GUARD_STANDARD.md` (sha `6c58a3f8…1b44`); `CACHE_V3_PIT_STATEMENT.md` (sha `602ed0d6…9595`); `cache_v3_hashes.json` (sha `6cad549d…894d3`); `cease_guard_audit.json` (sha `4432293a…750b`) |
| D10 | Sibling Q5 coverage over-claim erratum (8/23 ES deviation captures absent from disk and fetch_log; 0 claimed cells depend on them) — note the erratum? | Owner (one-line acknowledgment; Option A) or sibling-lane self-erratum (Option B) | Sibling artifact keeps working status with `es/q5_independent_verify/` as corrective evidence; no new cell may cite the 8 absent captures | ES (context); provenance hygiene precedent for all FX/NQ calendar cells | OWNER_DECISIONS D10; `FUTURES-SIX-READINESS-20261004/es/q5_independent_verify/` |
| D11 | Databento corpus rights BEYOND read-only research (license text not in repo) — record the license class? | Owner | **Read-only research only; anything else (external sharing, redistribution, derived products, publication-subset branch) requires a fresh ruling first** | All 5 symbols: any non-read-only use of the av1trim corpus | OWNER_DECISIONS D11; `dispatch/handoff_VERIFY-A7READY.json` source-inventory verdict |
| D12 | Residual NOT_OBTAINED calendar cells — bounded permitted-route extension lane vs leave NOT_OBTAINED. Inventory: 6E ECU26/ECZ26; 6B 2023Q1–2024Q2 + all 42 holiday windows; 6J 2023+2026 quarters (+2 identity-undeterminable cells) + holiday times; 6A 2023Q1/Q2 + 2026 quarters + holiday times; NQ 2026 holiday deviations (product level) | Owner | Cells stay NOT_OBTAINED; never rule-derived; affected windows/quarters excluded fail-closed at any freeze; no purchase/signup proposed anywhere | 6E: late-2026 roll-integrity cells; 6B: 6 expiry cells + entire holiday grid; 6J: 6 expiry cells + holiday times; 6A: 6 expiry cells + holiday times; NQ: 2026 holiday session times (advisory-class 10/10 obtained, product 0/10) | `RESIDUAL_INVENTORY.md` (sha `29fea296…f81dc`); `CAL_CLOSE_REPORT.md` §5 fail-closed register; OWNER_DECISIONS D12 |
| SIXGATE-OD-1 | Scope of the FIRST scored cycle: CYCLE-1 `FUTURES-ES-PB1-V1` (ES PB1-only 24; recommended) vs CYCLE-1b ES+NQ (46/53/60/67) vs CYCLE-0 all-6 | Owner | Nothing runs; the recommended path is a recommendation, not a decision | All 5 symbols: which cycle any of them could ever enter; ES/NQ/FX/6A pairing choices | `research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/synth/OWNER_DECISION_PACKET.md` (sha `3366776e…423b`) OD-1; `CYCLE_PROPOSAL.md` (sha `e8e45492…6550`) §1 |
| SIXGATE-OD-2 | D3 basis + e.1–e.4 at/before CYCLE-1 freeze (REQUIRED EXPLICIT) | Owner | BLOCKED_COST_FREEZE (see D3) | ES first, NQ next (dual-variant NQ table frozen at freeze) | OWNER_DECISION_PACKET OD-2 |
| SIXGATE-OD-3 | D9 canonicalization signature (evidence complete: 66 rolls, cg variant byte-identical, crash roll exact, deprecated v2 untouched) | Owner | cache_v3 CANDIDATE (see D9) | NQ scored path; RMM Role-B 6J/6A legs | OWNER_DECISION_PACKET OD-3 |
| SIXGATE-OD-4 | D4 ES cap amendment (only if scope > 24): ES-1 35 / ES-2 46 / ES-3 60 / ES-4 67 | Owner (each >24 line is a signed amendment, never silent) | 24 stands; CYCLE-1 needs none | ES (context) | OWNER_DECISION_PACKET OD-4; IDENTITY_TABLES §3.2 |
| SIXGATE-OD-5 | **PB2 lift (6E/6B)** — lift instruments: FX options FX-A/B/C (44/66/96 CONV-D) | Owner | 6E/6B stay HOLD | 6E, 6B: everything scored | OWNER_DECISION_PACKET OD-5; IDENTITY_TABLES §6 |
| SIXGATE-OD-6 | **PB3 lift (6A)** + D8 signature; 6A contingency 26 identities | Owner | 6A stays PARK | 6A: everything scored | OWNER_DECISION_PACKET OD-5/OD-6; IDENTITY_TABLES §7.2 |
| SIXGATE-OD-7 | Ceilings + two counting rulings, needed at ANY FX/NQ/6J freeze: (i) NQ ceiling NQ-A/B/C/D = 22/29/36/43; (ii) 6J ceiling J-A/B/C = 29/36/33–40; (iii) FX ceiling FX-A/B/C = 44/66/96 **CONV-D** or census-native 32/48/72 — the option must name which convention; (iv) clock-only shadow counting reading (a) inside-family (default used in tables) vs (b) additive; (v) placebo ≥100-seed expansion = EMPTY owner ruling (single-seed/single-delay ES precedent binds otherwise; multi-seed-as-identities ⇒ ≥1,800 placebo identities for the 18 returned legs) | Owner | No ceiling exists anywhere for NQ/6J/6E/6B ⇒ no registration possible on those symbols until a signed ceiling exists; reading (a) is the tables' declared default, signature must name (a) or (b); placebo stays single-seed/single-delay | NQ: no cap exists — ceiling REQUIRED; 6J: no cap — REQUIRED; 6E/6B: behind PB2 + ceiling; all: placebo budget | IDENTITY_TABLES §2.1, §4, §5, §6, §7.3; OWNER_DECISION_PACKET OD-7 |
| TEN-HYPO-OD-1 | Accept EXPWITCH (ESNQ-F5) into the pre-registration pipeline as a PROPOSAL? | Owner | Stays a paper dossier; 0 identities. Post-hoc state: BOTH legs DEAD at their pre-declared F5-K6 gates (ES T3 1.220 < 1.25, margin −0.030; NQ part-ii 35/66 expiry Fridays carry 15-min RTH vendor gaps); threshold miss NOT re-tuned; owner may re-adjudicate threshold only as an explicit disclosed amendment; NQ vendor-gap resolution = owner data-plane decision | ES (born-blocked anyway), NQ (dead at gate + D9/ceiling still required) | `research/control/FUTURES-TEN-HYPO-PREP-20261004/synth/OWNER_DECISION_PACKET.md` (sha `4fb20a63…7cf9`) OD-1; `K6GATE …/synth/SYNTHESIS_K6.md` (sha `03a8e77e…8237`) §1/§3.3; `m2_expwitch_anatomy_v3.json` (sha `2d2068f1…f98d`) |
| TEN-HYPO-OD-2 | Commodity data path (vendor purchase / IBKR collection / accept 14-month volume limit) | Owner (only the owner can spend or commit collection) | All commodity lines stay DATA-BLOCKED | None of the 5 (carried) | TEN-HYPO OWNER_DECISION_PACKET OD-2 |
| TEN-HYPO-OD-3 | 6J ceiling + RMM Role-B DC §1.3 boundary ruling | Owner | 6J families stay CTG; RMM Role B stays proposal-only | 6J: RMM Role-B leg (+4 IDs/leg) and ceiling | TEN-HYPO OWNER_DECISION_PACKET OD-3; IDENTITY_TABLES §5 J-C |
| TEN-HYPO-OD-4 | D1–D12 unchanged (pointer; adds/resolves nothing) | Owner | All six-adopt defaults apply verbatim | All | TEN-HYPO OWNER_DECISION_PACKET OD-4 |
| 6J-BOJ-STAMPS | BoJ intraday decision stamps: corpus carries dates only (156 statement files, 0 intraday timestamps) — owner decides whether any intraday BoJ-timed arm may exist; JF1 12:00–15:30 JST anchor stays a declared convention (anchor-robustness K3 delivered: ANCHOR_INSENSITIVE_AT_45MIN over 54 MPM days) | Owner | Dates-only posture stands; JF1 anchor conventional; no intraday-timed BoJ arm | 6J: JF1-family timing law | `DATA_READINESS_6J.md` Dim 5 (sha `2e322ef2…3ef7`); K6GATE `jf1_k3_anchor.json` (sha `235e0472…545dc`) |
| 6J-JF2-THRESHOLD | JF2 threshold constant is owner-gated (declared, not self-settable) | Owner | Unset ⇒ JF2 stays contingency spec, no constant frozen | 6J: JF2 block | IDENTITY_TABLES §5 secondary gates |

---

## 3. Bucket (C) — PROPOSAL-ONLY (never signed; drafts, options, proposed laws)

| artifact | what it is | status word (verbatim) | evidence path |
|---|---|---|---|
| C-1 | Six-symbol cycle launch packet `FUTURES-SIX-V1` (working title) | "LAUNCH DRAFT — PACKED FOR OWNER REVIEW. **NOT REGISTERED. NOT AUTHORIZED. NOT GO.**" | `FUTURES-SIX-ADOPT-PREP-20261004/packet/CYCLE_LAUNCH_DRAFT.md` (sha `bc2b6488…bcb03`) |
| C-2 | Split-cycle path CYCLE-1 (ES) / CYCLE-2 (NQ) / CYCLE-3 (FX) / CYCLE-0 (all-6, not recommended) | "Preparation, not authorization"; a PROPOSAL for owner choice (OD-1) | `FUTURES-SIX-SCORED-GATE-PREP-20261004/synth/CYCLE_PROPOSAL.md` (sha `e8e45492…6550`) |
| C-3 | Cease-guard standard (normative algorithm + audit) | "PROPOSED STANDARD — pending owner decision D9… no standard here is in force until the owner writes one" | `adopt/CEASE_GUARD_STANDARD.md` (sha `6c58a3f8…1b44`) |
| C-4 | 6A era-aware tick/cost law (era table + cost implications) | "PROPOSED — pending owner decision D8. Nothing here freezes a cost spec" | `adopt/6A_TICK_ERA_LAW.md` (sha `bd9c2011…7635`) |
| C-5 | NQ cache_v3 canonical status + PIT classification (PIT_CLEAN_BY_CONSTRUCTION) | "canonical-CANDIDATE — consumption as canonical requires owner ratification (D9). Nothing here ratifies anything" | `adopt/CACHE_V3_PIT_STATEMENT.md` (sha `602ed0d6…9595`) |
| C-6 | Budget/ceiling OPTIONS: ES-0..ES-4 (24/35/46/60/67), NQ-A..D (22/29/36/43), J-A..C (29/36/33–40), FX-A..C (44/66/96 CONV-D vs census-native 32/48/72), 6A contingency 26; CONV-D conversion convention; clock-shadow reading (a)/(b) | "the exact option set… the owner may sign at a future registration… no option in this document is recommended"; "This document registers nothing and executes nothing" | `budget/IDENTITY_TABLES.md` (sha `750858ab…f6e6`) |
| C-7 | SIXGATE OD-1..OD-7 decision packet itself | "NOTHING HERE IS RATIFIED BY THIS THREAD… Slots empty; nothing self-ratified" | `synth/OWNER_DECISION_PACKET.md` (sha `3366776e…423b`) |
| C-8 | TEN-HYPO decision packet + EXPWITCH dossier + outcome-blind ranking | "PREP OUTPUT FOR OWNER REVIEW. NOT A RULING. NOT AUTHORIZATION."; EXPWITCH = paper dossier (OD-1 default) | `FUTURES-TEN-HYPO-PREP-20261004/synth/OWNER_DECISION_PACKET.md` (sha `4fb20a63…7cf9`); `CANDIDATE_CENSUS_10SYM.md` (sha `47dc0e82…0006`); `OUTCOME_BLIND_RANKING_R3.md` (sha `ae29254a…9ea2`) |
| C-9 | D8/D9 decision sheet (concrete option text + quantitative consequences) | "NOT ratified by owner as of 2026-10-04; this sheet is input to a ruling, not a ruling" | `adopt/D8_D9_DECISION_SHEET.md` (sha `b1d6079f…f8ae`) |
| C-10 | RMM Role-B (NQ-F4/6J/6A legs, +4 IDs/leg) | Proposal-only (TEN-HYPO OD-3 default: "RMM Role B stays proposal-only"); DC §1.3 boundary ruling required | TEN-HYPO OWNER_DECISION_PACKET OD-3; IDENTITY_TABLES §5/§6 |
| C-11 | SPEC_PB1_ES as a *specification* for any non-ES cycle | For the 5 mission symbols SPEC_PB1_ES is PRECEDENT ONLY (structure/format/fold/control precedent; the ES cycle itself is a separate registered ES-cycle track, read-only for this round per dispatch) | `FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` (sha `445f7499…b7073`) |

---

## 4. What each of the 5 symbols still needs before ANY scored consumption (intake summary)

| symbol | owner signatures still required (in dependency order) |
|---|---|
| NQ | D9 (cache_v3 canonicalization + cease-guard law) → NQ ceiling (OD-7-i, reading (a)/(b) named) → registration → prelaunch A7 → typed GO. Fee layer D2/D3 must also be ruled before any cost-bearing freeze. EXPWITCH-NQ additionally dead at gate (owner data-plane decision to revive or not). |
| 6E | PB2 lift (OD-5) → FX ceiling with convention named (OD-7-iii) → registration → prelaunch A7 → typed GO (+ D2/D3 for the fee layer; D12 late-2026 expiry cells excluded fail-closed at freeze). |
| 6B | Same chain as 6E, plus: the entire holiday-deviation grid is NOT_OBTAINED (0/42) ⇒ holiday-shortened-session handling must be bar-count exclusion by declared rule at freeze; 6 expiry cells 2023Q1–2024Q2 excluded fail-closed. |
| 6J | 6J ceiling (OD-7-ii / TEN-HYPO-OD-3) → BoJ-stamps ruling (6J-BOJ-STAMPS) if any intraday-timed arm is wanted → BBO/cost gates (D2) → registration → GO. JF2 threshold constant owner-gated. 6 expiry cells + holiday times NOT_OBTAINED. |
| 6A | PB3 lift (OD-6) AND D8 (era-aware tick law) both required — the 26-identity contingency annex enters no cycle until both land; then registration → A7 → GO. Era-2-only cost models may not back-cast into 2020 windows (fail-closed, in force). |

Every row above ends at the same place absent further rulings: **0 scored
trials exist on all five symbols** (P-9 ledger law statement, IDENTITY_TABLES
§7.1); the only observed denominators are data/readiness measurements.

## 5. Coverage statement

Enumerated sources: FUTURES-SIX-READINESS-20261004 (OWNER_DECISIONS D1–D12 +
census + 5 mission dossiers + verify), FUTURES-SIX-ADOPT-PREP-20261004
(D8/D9 sheet, CEASE_GUARD_STANDARD, 6A_TICK_ERA_LAW, CACHE_V3_PIT_STATEMENT,
DEPRECATION_NQ_V2_CACHES, CYCLE_LAUNCH_DRAFT, open_decisions_dependency.json,
cal_eb/cal_janq/fee_es/hypo), FUTURES-SIX-SCORED-GATE-PREP-20261004
(OWNER_DECISION_PACKET OD-1..OD-7, CYCLE_PROPOSAL, COST_FREEZE_ERRATUM,
IDENTITY_TABLES, A7_FEE_REAUDIT, cal_close/CAL_CLOSE + RESIDUAL_INVENTORY),
FUTURES-TEN-HYPO-PREP-20261004 (OWNER_DECISION_PACKET OD-1..OD-4,
CANDIDATE_CENSUS, OUTCOME_BLIND_RANKING), FUTURES-K6GATE-PREP-20261004
(SYNTHESIS_K6, SHORTLIST_STALE_COST_ERRATUM, 3 per-symbol gate reports),
FUTURES-P3-QUARANTINE-20261004 (D1–D7 origin; out-of-ancestry tip `b583c33a`,
quoted via this branch's carried restatements only), FUTURES-ES-V1-PACKET
(SPEC precedent), DAILY-EXPLORATORY-V1 (two-key GO precedent). The six-gate
shortlist lane deliverables are consumed only through
SHORTLIST_STALE_COST_ERRATUM (F-4/F-5/F-6 superseded lines).

No NEW decision slots were discovered that are not already carried under an
existing original ID; accordingly **no P5- IDs were minted** (namespace law).
This matrix raises no gate and requests no GO.

— End AUTHORITY_MATRIX.md.
