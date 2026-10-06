# REGISTRATION_READINESS — FUTURES-ES-PB1-V1 (CYCLE-1: ES, PB1-only, 24 identities)

Lane FREEZE-AUDIT, round FUTURES-ES-PB1-REGPREP-20261004, 2026-10-04.
Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep`
@ `ffed828f73fa19fa0ff4aee3ac1b441909a43940` (branch `prep/futures-es-reg-20261004`).

**This lane registers NOTHING and runs NOTHING.** Audit/extraction only; zero
network; zero PnL; zero scoring; zero registration; no registry/ledger writes.
Every claim below is checked against the pinned artifacts in
`freeze/freeze_pins.json` (34 pins, all in-git at this HEAD).

## (a) Is the freeze set COMPLETE?

**YES — at the freeze-input level: every input is pinned and every number is
source-traced.** Evidence:

1. **Spec byte-frozen.** `SPEC_PB1_ES.md` sha256
   `445f749906481f33080185cab1628e6365ef2f6db3b9c4f9f0847646eb6b7073` —
   **MATCH** with the expected pin (byte-frozen proof), independently
   corroborated by A7_FEE_REAUDIT §1 (same digest recorded MATCH at 893db28c).
2. **Identity table reconciled exactly.** Independent transcription of SPEC §6
   yields 24 identities: P-A 8 + P-B 8 + FOMC 4 + C1-C4 4 = 24 — count and
   composition both match the census claims (IDENTITY_TABLES.md §0 ruling 1 and
   §3.1 "8+8+4+4=24"; Option ES-0 = "SPEC_PB1_ES r3 §6, unchanged, as the
   identity-table annex", convention CONV-A). Zero discrepancies
   (`freeze/identity_table_24.json`).
3. **Cost freeze closes cell-by-cell.** Independent re-derivation from raw
   components (0.85 + 1.38 + 0.02) matches ALL of: D3_RECORDED
   `interpretation.effective_cost_table_es`, COST_FREEZE_ERRATUM §2 (Variant A
   column), and A7_FEE_REAUDIT §8 (Variant A column) — 18/18 cells, 3/3 labels,
   0 mismatches, 0 use-as-value hits for the retired glued values
   (`freeze/cost_freeze_check.json`). Fees/side **2.25**; all-ins
   **21.00 / 33.50 / 46.00** per side; RT **42.00 / 67.00 / 92.00**; window
   2014-10-01→2017-12-31 **20.99 / 33.49 / 45.99**. Labels binding:
   **MODELED COST**; **VERIFIED_VS_ACCOUNT = NOT_RUN** (never inferred PASS);
   documentation-A7 clean (**AUTHORIZED_WITH_FINDINGS, 0 HIGH / 0 CRITICAL**).
4. **Data panel pinned.** ES 1m outright panel (7,825,657 bars) sha
   `7ae6de2d…27b95`, present in THIS worktree checkout (tracked ⇒ in-git), and
   byte-identical at the sibling readiness worktree's recorded source path. All
   11 ES_cache files (panel, segments, 4 held-chain variants, contract-daily,
   contracts manifest, roll table, + 2 companions) pinned.
5. **PIT/exclude law side inventoried with pins** (`freeze/pit_exclude_set.json`):
   FOMC 132-statement day-exclude (dated artifact + inventory audit), BLS
   vintage law + the D5 pin (calendar_close_delta.json), holiday fail-closed
   exclusions incl. ES 2026 CAL-CLOSE results, RTH-core <60% floor, roll/expiry
   quarter-exclude law, E3-E5, fold structure (4 folds, warmup 252). All NOT_RUN
   items stay NOT_RUN — listed explicitly, never inferred PASS.

### Completeness caveats (surface, do not resolve)

- **C-1 (GO-phrase text).** PLAN_futures_es_v1 §6 (pinned 06140882…) fixes the
  GO phrase as `GO FUTURES ES V1 SCORED EXECUTION`, while this round's dispatch
  packet text writes `GO FUTURES-ES-PB1-V1 SCORED EXECUTION`. Under the
  exact-match law (typed GO dies unconsumed if paraphrased), the canonical
  string is whatever is entered in the cycle's registered gate — the owner must
  see both renderings at registration and one must be the registered text.
  Reported, not resolved.
- **C-2 (stale committed prints are history, not cost).** SPEC §5 L100/L104 and
  PLAN §3 still print the retired glued values as committed history; the
  COST_FREEZE_ERRATUM (and SHORTLIST_STALE_COST_ERRATUM for the shortlist
  lines) supersede them BY REFERENCE for every future freeze. They are not
  consumed by this freeze set; they stand byte-frozen as evidence (append-only
  law, nothing edited).
- **C-3 (fee dim was BLOCKED at readiness time).** DATA_READINESS_ES dim 6
  recorded BLOCKED at the pre-D3 state (2.24 basis, reg divergence open, fee A7
  READY-NOT-RUN). The subsequent chain — fee A7 executed clean
  (AUTHORIZED_WITH_FINDINGS, 0 HIGH/CRIT) + COST_FREEZE_ERRATUM §2 + owner D3=A
  — resolves the reg-basis question at **2.25/side** for ES. VERIFIED_VS_ACCOUNT
  remains NOT_RUN exactly as labeled everywhere; nothing inferred.
- **C-4 (the generated exclude-list does not exist yet).** The deterministic
  exclude-list is generated at freeze, post-registration (SPEC §2); its sha is
  recorded into the selection freeze at that point. This lane pins the laws and
  evidence, not the generated list.

## (b) Authority sufficiency

**D3 = Variant A is recorded and SUFFICIENT for the ES cost freeze.**
`auth/D3_RECORDED.json` (decision_id `D3-VARIANT-A-20261004`, owner quote
verbatim "tôi chọn 2.25$"): `authority_scope.closes = ["D3", "e.4"]` — e.4 is
CLOSED. The three remaining open rulings are FX/NYMEX-scoped and **non-blocking
for ES**; A7_EXECUTION_PACKET §4 defines them verbatim:

> - **e.1** FX-group fee mapping corroboration — accept PARTIAL (CME "Forex
>   Futures" row aliases, 1.60 confirmed; 6E/6B/6J/6A never printed verbatim) or
>   name the binding page.
> - **e.2** Account geography basis for the IB-JP paren (`0.011 = 0.01×1.1` tax
>   artifact) — confirm US-entity pages are the operative basis.
> - **e.3** NYMEX reg 0.02→0.01 temporal window / epoch-binding rule for
>   historical-year modeling.
> - **e.4** (= **D3**) Reg-component basis for modeled all-ins: NFA 0.02 vs IBKR
>   offset 0.01 — quantified in `D3_QUANT_SHEET.md` (same dir).

D3=A also does NOT: type a GO, register the cycle, authorize S1/order/purchase/
push, lift D9/PB2/PB3/D8 or any cap, or make fees VERIFIED_VS_ACCOUNT
(D3_RECORDED `does_NOT_do`, verbatim record). ES cap 24 FROZEN stands; PB2
HOLD; PB3 PARK; NO_GO_SCORE / NO_GO_ORDER stand until the registered gate.

## (c) Remaining gates, in exact order

1. **Registration at ROOT.** `research/researchctl.py cycle register` writes
   `plans/CYCLE_REGISTRY.json` on root main — outside any prep session's write
   scope. Owner-run, or an explicitly owner-delegated root session (registry
   only, pathspec-staged). **The current authority text does NOT include
   registration** — no artifact authorizes this lane or any prep lane to
   register; PLAN §7 step 2 names it BLOCKER TỐI THIỂU số 1. At registration:
   spec sha + identity-table sha + exclude-list sha enter the selection freeze;
   the canonical GO phrase is fixed (see C-1).
2. **Prelaunch A7** — independent prelaunch audit of the registered cycle
   (spec-ready; PLAN §4 "A7 prelaunch độc lập bắt buộc trước GO", two-key
   first key: A7 AUTHORIZED with 0 HIGH/CRITICAL unresolved).
3. **Exact-arm dry-run** — post-registration by law; runs the registered arms
   end-to-end under the frozen inputs before any scored cell.
4. **Typed owner GO at the registered cycle's gate** — exact-match law: the
   owner types the registered phrase verbatim, fresh, at the gate; a
   paraphrase dies unconsumed. Two-key: A7 prelaunch AUTHORIZED + owner phrase.

## Standing statement

Freeze-set status: **COMPLETE at the freeze-input level; registration-ready as
an INPUT SET** — the act of registration belongs to the owner/root session and
has not occurred (`NO_GO_REGISTER`-class law holds; D3_RECORDED
`registry_state_at_record`: root main c7611803, NO futures cycle registered).
0 PnL exists anywhere in this program; 0 scored trials on these symbols; this
lane computed hashes, transcribed tables, and compared numbers — nothing else.

— End REGISTRATION_READINESS.md. Lane FREEZE-AUDIT registers nothing, runs
nothing, decides nothing.

## CORRECTION 2026-10-04 (post-77a763ac audit, F-AF1 — append-only)

- Supersedes the §(b) sentence "The three remaining open rulings are
  FX/NYMEX-scoped…" at L80: the precise scoping is **e.1 FX-scoped;
  e.2 geography-scoped (account-geography basis; not consumed under
  Variant A — the 0.011 offset is unused); e.3 NYMEX-scoped** — per
  auth/D3_RECORDED.json sufficiency_conclusion (as completed) and
  A7_EXECUTION_PACKET §4 definitions.
- Supersedes this file's pin-basis references to `freeze_pins.json`:
  the AUTHORITATIVE pin manifest is **`freeze/freeze_pins_v2.json`**
  (34 pins re-hashed at the corrected final state; supersession record:
  `freeze/PIN_SUPERSESSION.md`). v1 stands as the lane-time historical
  measurement.
- No other content of this file is affected; the original text above
  stands as history, superseded by this section.
