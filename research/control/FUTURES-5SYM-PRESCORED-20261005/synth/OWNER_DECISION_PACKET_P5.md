# OWNER_DECISION_PACKET_P5 — FUTURES-5SYM-PRESCORED-20261005 (controller synthesis)

- Round: FUTURES-5SYM-PRESCORED-20261005, wave-2 SYNTH over 7 wave-1 lanes
  (INTAKE / NQ / FXEB / FXJA / EXEC / HYPO / CALCOST), committed at wave-1
  checkpoints `b051d61e` → `059c0665` → `fe250465` on branch
  `prep/futures-5sym-prescored-20261005` (base `ffed828f`, the k6gate verified chain).
- **NOTHING HERE IS RATIFIED.** The owner's 2026-10-05 instruction authorized
  PREP + hypothesis research on NQ/6E/6B/6J/6A ONLY. It is NOT a typed GO, NOT
  registration, NOT PB2/PB3 lift, NOT D8/D9/D3 ratification, NOT any ceiling.
  **Scored trials run this round: 0. PnL computed: 0.** All gates unchanged:
  NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER; PB2 HOLD; PB3 PARK; ES cap 24
  FROZEN; ES finalize cycle untouched.
- This packet consolidates every decision the lanes surfaced, with the
  classification the owner asked for: **(A) workable now**, **(B) owner must
  decide**, **(C) post-approval registration/gates/GO only**.

## 0. Namespace law (collision fix, supersede-by-reference)

Wave-1 lanes minted P5- IDs independently. Two lanes collided
(FXEB `P5-OD1..OD11` vs HYPO `P5-OD-1..4`). The committed lane files stay
byte-untouched (append-only law); THIS table is the authoritative namespace
map. All later rounds use the right-hand IDs.

| Lane file (as committed) | Authoritative ID | Short question |
|---|---|---|
| nq/ P5-NQ1 | **P5-NQ1** | ADOPT-D9 Option A for NQ (cache_v3 canonical + cease-guard law) |
| nq/ P5-NQ2 | **P5-NQ2** | NQ ceiling NQ-A 22 / NQ-B 29 / NQ-C 36 + clock-shadow reading (a)/(b) |
| nq/ P5-NQ3 | **P5-NQ3** | D3 basis applied to NQ (A 2.25 vs B 2.24; delta $0.02/RT) |
| nq/ P5-NQ4 | **P5-NQ4** | DATA_READINESS_NQ "$2.50" pointer-line erratum adjudication (annotation-only) |
| nq/ P5-NQ5 | **P5-NQ5** | EXPWITCH-NQ leg disposition (dead-at-gate stands vs data-plane fix) |
| nq/ P5-NQ6 | **P5-NQ6** | NQ 2026 calendar residual posture (fail-closed vs bounded extension) |
| fx_eb/ P5-OD1 | **P5-FXEB-OD1** | PB2 lift 6E/6B (owner's alone; not requested here) |
| fx_eb/ P5-OD2 | **P5-FXEB-OD2** | FX ceiling: CONV-D 44/66/96 vs census-native 32/48/72 + clock-shadow reading |
| fx_eb/ P5-OD3 | **P5-FXEB-OD3** | CONV-D core delay-slot pair {D0,D1B} vs {D0,D30M} |
| fx_eb/ P5-OD4 | **P5-FXEB-OD4** | Placebo budget: single-seed default vs ≥100-seed expansion |
| fx_eb/ P5-OD5 | **P5-FXEB-OD5** | RMM Role-B legality (owner DC §1.3 boundary ruling) |
| fx_eb/ P5-OD6 | **P5-FXEB-OD6** | FX reg-basis: Variant-B 2.46 printed vs Variant-A 2.47 DERIVED (not A7-tabulated for FX) |
| fx_eb/ P5-OD7 | **P5-FXEB-OD7** | e.1 FX fee-alias corroboration (accept PARTIAL or fund) |
| fx_eb/ P5-OD8 | **P5-FXEB-OD8** | BBO/fill realism reaffirm (D5 conservative fill binds) |
| fx_eb/ P5-OD9 | **P5-FXEB-OD9** | D12 posture for FX residual cells (6E ECU26/ECZ26; 6B 2023Q1-24Q2 + 0/42; 6E 8 aged-out) |
| fx_eb/ P5-OD10 | **P5-FXEB-OD10** | FX fold/warmup law: 60-held-session family law vs 252-session ES precedent |
| fx_eb/ P5-OD11 | **P5-FXEB-OD11** | Court §b1.1 1m trigger-time anatomy commissioning (pre-F1-registration prerequisite) |
| fx_ja/ P5-D1 | **P5-FXJA-D1** | 6J ceiling J-A 29 / J-B 36 / J-C 33-40 + clock-shadow reading |
| fx_ja/ P5-D2 | **P5-FXJA-D2** | DC §1.3 boundary ruling (only if J-C RMM leg) |
| fx_ja/ P5-D3 | **P5-FXJA-D3** | 6J BBO/fill ruling (conservative law vs fund study) |
| fx_ja/ P5-D4 | **P5-FXJA-D4** | 6J/6A fee-A7 posture (standing D2 vs separate FX A7) |
| fx_ja/ P5-D5 | **P5-FXJA-D5** | 6A activation bundle: PB3 lift → D8 → D9 → fee A7 → ABS/China calendars |
| hypo/ P5-OD-1 | **P5-HYPO-OD1** | EXPWITCH post-gate disposition (= P5-NQ5's program-level twin; sign once, binds both) |
| hypo/ P5-OD-2 | **P5-HYPO-OD2** | BoJ intraday stamp acquisition (minute anchor upgrade; non-blocking per K3) |
| hypo/ P5-OD-3 | **P5-HYPO-OD3** | ABS + China release-calendar acquisition (AU-REL/CN-REL/AF3-K4) |
| hypo/ P5-OD-4 | **P5-HYPO-OD4** | JF2 zone-threshold constant (fix a priori; = FXJA G5 machinery) |
| cal_cost/ P5-CALC-NQ-HOLPROD | **P5-CALC-NQ-HOLPROD** | NQ 2026 holiday product-level: advisory-class operative + documented exclusion, vs open |
| cal_cost/ P5-CALC-6J-IDENT | **P5-CALC-6J-IDENT** | 2 identity-undetermined 6J expiry cells (owner-defined identity source) |
| cal_cost/ P5-CALC-RBA-FWD | **P5-CALC-RBA-FWD** | RBA forward Nov/Dec-2026 (fail-closed exclusion vs acquisition) |
| cal_cost/ P5-CALC-FEE-E14 | **P5-CALC-FEE-E14** | e.1-e.4 fee sub-rulings (= P5-FXEB-OD6/OD7 superset; sign together) |
| fx_eb/ P5-FREEZE-REFUSAL | **P5-FREEZE-REFUSAL** | (draft refusal id, not a decision — builder behavior spec) |

Note: P5-NQ5 and P5-HYPO-OD1 are the same question at different scopes
(NQ-leg vs program). One signature answers both; the packet records them once.

## 1. Shared decisions (bind multiple symbols at once)

| ID (prior authority) | Question | Options with grounds | Impact if signed / if silent |
|---|---|---|---|
| **D3 basis** (ADOPT-D3 + COST_FREEZE_ERRATUM; = P5-NQ3, P5-FXEB-OD6/OD7, P5-CALC-FEE-E14) | Regulatory fee basis | **A** 2.25/side (NFA timeline; FX all-in 2.47 DERIVED) · **B** 2.24/side (IBKR offset; FX 2.46 printed). Exchange cell 1.38 evidence-settled; stale 21.006-prints never consumable; e.1-e.4 ride along | Signed: every per-symbol cost freeze becomes single-variant and freezes. Silent: dual-variant everywhere, no cost-bearing scored cell on ANY symbol (fail-closed) |
| **Placebo slot** (IDENTITY_TABLES §7.3; = P5-FXEB-OD4) | Placebo budget | single-seed/single-delay (ES precedent) vs ≥100-seed expansion (≥1,800 IDs program-wide inference) | Silent: single-seed publication law binds every signed option |
| **BBO/fill** (D5; = P5-FXEB-OD8, P5-FXJA-D3) | Fill model of record | conservative fill law (next-bar open, close-proxy spread high-biased, SL-priority, BBO NOT_RUN) vs fund BBO study | Silent: conservative law binds; no fill-sensitive gate passes |
| **EXPWITCH disposition** (K6GATE gate result; = P5-NQ5 / P5-HYPO-OD1) | Accept both-legs dead-at-gate | accept (default) vs owner data-plane fix for 2013-2021 15-min vendor granularity | Silent: dead stands; no EXPWITCH identity mints anywhere |
| **D9** (ADOPT-D9; = P5-NQ1, 6A leg of P5-FXJA-D5) | cache_v3 canonical + cease-guard standing law | Option A ratify (evidence complete: 66 rolls, cg variant 0 violations, v2 deprecated untouched) | Silent: cache_v3 stays candidate; NQ builder + FX roll chains refuse |
| **D8** (ADOPT-D8; inside P5-FXJA-D5) | 6A era-aware tick/cost law | Option A ratify measured 2020-11-20/23 boundary / Option B demand exchange document | Silent: era-2 models never back-cast into 2020; 6A stays parked regardless |

## 2. Per-symbol decision sets (the minimal signature chain to a first scored cell)

- **NQ (CYCLE-2 path):** P5-NQ1 (D9) → P5-NQ2 (ceiling NQ-A/B/C + shadow reading) → P5-NQ3 (D3) → then C-class. NQ-D 43 has NO lawful path while EXPWITCH-NQ stands dead (P5-NQ5 default). NQ-F3's full-era rebuild precondition is executable-in-principle on cache_v3 (K6GATE), not yet re-run — post-D9 work item, not a signature.
- **6E/6B (CYCLE-3 path):** P5-FXEB-OD1 (PB2 lift — owner's alone) → P5-FXEB-OD2 (ceiling + convention) → P5-FXEB-OD6/OD7 + D3/e.1-e.4 → (if FX-C / J-C-style RMM) P5-FXEB-OD5 → then C-class. P5-FXEB-OD10 (fold/warmup law) must land at freeze. P5-FXEB-OD11 (court §b1.1 anatomy) is an A-class commission any time after PB2 lift decision — it gates F1 registration only.
- **6J:** P5-FXJA-D1 (ceiling J-A/B/C + shadow reading; the single 6J-blocking signature) → P5-FXJA-D3 (BBO) → P5-FXJA-D4 (fee posture; folds into D2/D3) → then C-class. J-C additionally needs P5-FXJA-D2 (DC §1.3). BoJ stamps stay NOT_IN_CORPUS (K3 anchor-insensitivity delivered makes P5-HYPO-OD2 non-blocking).
- **6A:** stays PB3 PARK, 0 budget. Activation bundle = P5-FXJA-D5 (PB3 lift → D8 → D9 → fee A7 → ABS/China per P5-HYPO-OD3). The frozen 26-ID contingency table is carried verbatim; nothing this round expands it.

## 3. What each decision changes (concrete)

| Signature | Data | Identities | Budget arithmetic | Conclusions enabled |
|---|---|---|---|---|
| P5-NQ1 (D9-A) | cache_v3 becomes chain-of-record (6,780,608 rows, 10/10 files re-hashed byte-exact by NQ lane) | 36 draft NQ IDs become freezable (under a ceiling) | NQ-A/B/C = 22/29/36 become signable | NQ prelaunch A7 + dry-run + scored become reachable in principle |
| P5-NQ2 (ceiling) | none | the chosen subset of 36 draft IDs freezes | fixes the NQ observed-denominator plan | same |
| P5-NQ3/D3 | none | none | every NQ/FX cost gate single-variant | cost-bearing gates passable |
| P5-FXEB-OD1 (PB2) | 6E/6B panels already re-hashed zero-drift | 44/66/96 CONV-D options become signable | FX denominators plannable | FX-F1..F4 registration paths open |
| P5-FXJA-D1 (6J ceiling) | none | 29/36/33-40 enumeration freezes | 6J denominator plan fixed | JF1/JF3 (+JF2 host) reachable |
| P5-FXJA-D5 (6A bundle) | era table active at runtime | 26-ID contingency consumable verbatim | 0 → 26 only on full chain | AF1/AF3/AF4 contingency |

## 4. A/B/C classification of ALL remaining work

**A. Workable now (no owner input needed):**
1. Runner contract-number verification (EXEC placeholders) against per-symbol
   lanes' verified identities — wave-2 verifier covers the first pass.
2. NQ-F3 full-era rebuild re-run on cache_v3 (post-D9 by law, but the script
   harness itself can be prepared and dry-checked on synthetic fixtures now).
3. FX-F5/F6/AF2 vintage quantification harnesses (HYPO G3/G4/G9) on committed
   ALFRED captures — descriptive only.
4. NQ dispersion proxy re-derivation on v3 (HYPO G11).
5. FX-F4 M2c-corrected r = RT/MDE re-derivation (HYPO G8).
6. Court §b1.1 anatomy machinery prep (P5-FXEB-OD11's A-half).

**B. Owner decisions:** everything in §0/§1/§2 above. The single minimal
sentence that unlocks the earliest non-ES scored path (NQ):
> "D9 = Option A (cache_v3 canonical + cease-guard law). Trần NQ = [22|29|36]
> (NQ-A/B/C), clock-shadow reading [(a)|(b)]. D3 = [A|B]."
6E/6B/6J each additionally need their own first line (PB2 / ceiling); 6A needs
the full P5-FXJA-D5 bundle.

**C. Post-approval only:** registration at ROOT, prelaunch A7 (fresh-context),
exact-arm dry-run, typed GO `GO <REGISTERED-CYCLE-ID> SCORED EXECUTION`,
scored under heavy lock, reproduction twin, terminal A7. None of these is
delayed by missing PREP work after wave-2 — the only C-inputs are the B
signatures and the runner-verification closure (A.1).

## 5. Standing gates restated (never reopened by this round)

PB2 HOLD · PB3 PARK · ES cap 24 FROZEN + ES BLOCKED_COST_FREEZE (D3, ES side)
· EXPWITCH both legs DEAD-AT-GATE · NQ v2 caches deprecated · BoJ stamps
NOT_IN_CORPUS · no-IMM-derivation · P3 quarantine absolute (futures-behavior
not an ancestor; its captures never read) · databento read-only-research only
(D11) · every cost number MODELED / VERIFIED_VS_ACCOUNT=NOT_RUN.

— End OWNER_DECISION_PACKET_P5. Slots empty; nothing self-ratified; 0 scored
runs exist.
