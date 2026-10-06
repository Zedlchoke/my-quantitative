# A7_FEE_READINESS_PACKET — self-contained briefing for a fresh independent A7 auditor

- Round: FUTURES-P3-QUARANTINE-20261004, lane Q3-FEE-A7-READY. Written 2026-10-04 UTC.
- Worktree: `prep/futures-behavior-10syms-20261002` @
  `0225b3c25bf1cf269dae5a835853b5b3904125a0` (== dispatch sha; re-measured, no drift).
- Companion: `PROPAGATION_COUNT_RECONCILIATION.md` / `.json` (same dir) — the
  propagation-count half of the A7's scope, already reconciled by this lane.
- **THIS PACKET IS PREPARATION ONLY. It is not authorization and the A7 has NOT
  been run by this lane.** See §4 (preconditions/authority).

## (a) Scope of the A7 audit

1. **Fee erratum, end-to-end re-validation.** The parent rounds (A4-FEES in
   `FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003`, D2-FEESRC in
   `FUTURES-DATACONTRACT-QUAL-V1`) transcribed IBKR "fees charged to offset"
   pages with a suspected glued-superscript defect: rendered `1.38⁶` → `1.386`,
   `0.01¹` → `0.011`. The overnight round (P0A-FEESOURCE / P0B-FEEIMPACT /
   P0-VERIFY) re-sourced the pages, confirmed the defect at byte level, and
   published corrected values (ES/NQ 2.24, FX 2.46, CL 2.36, NG 2.46, GC/SI
   2.51 USD/side tier-1; verdict `UPHELD_IN_FULL`). The A7 independently
   re-derives every load-bearing cell from the raw captures — it does NOT
   inherit P0A/P0B/P0-VERIFY conclusions.
2. **Propagation impact re-validation.** 25 genuine stale-parent-value sites
   (22 frozen-historical + 3 living-doc; grep universe 26 files − 1 false
   positive; the "27" in the overnight dispatch mission text is a clerical
   off-by-one). Full classification: companion reconciliation doc.
3. **UNDER-REVIEW status of SPEC_PB1_ES §5 cost lines — adjudicate the
   governance state, do not "fix" it.** `FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md`
   (freeze-ready r3, frozen) still prints, at HEAD:
   - L100 `| Exchange (CME) | 1.386 | public LIVE_OFFICIAL (IBKR CME.php offset table); current-as-approximation mọi năm lịch |`
   - L101 `... IBKR offset 0.011 KHÔNG dùng, KHÔNG cộng kèm ...` (NFA timeline row)
   - L104 `| All-in/side (mặc định NFA 0.02) | S1 21.006 · S2 33.506 · S3 46.006 | ...`
   The erratum (`GATE_REVIEW_NOTE.md` §1) records these §5 lines and every
   cost gate derived from them as **UNDER REVIEW** until a new A7 re-audits.
   The A7's job: **adjudicate that this state is properly documented** — spec
   byte-identical (not silently edited), under-review record discoverable and
   consistent, and the erratum-governance chain (append-only, corrections
   supersede by reference, never in-place edits of frozen artifacts) intact.
   Under the corrected values the stale lines would read 1.38 / offset note
   0.01 / 21.00 · 33.50 · 46.00 (exchange delta −0.006; see GATE_REVIEW_NOTE §1)
   — but only the owner/owning lane applies that after the A7, by committed round.

## (b) Inputs inventory (sha256 recomputed by this lane 2026-10-04 at HEAD 0225b3c2)

All under `research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/`.
All 16-hex prefixes cross-check against `source/MANIFEST.md` (11/11 match).

Source captures (`source/`):
| File | Kind / epoch | sha256 |
|---|---|---|
| `archive_CME.php.html` | RAW HTML, web.archive.org, CME.php 2026-06-08T11:46:25Z — superscript byte-authority | `0f726c52ce90a2e159b376ef40e11e78afd8d279bceb263719038d4c3a3b9e85` |
| `archive_COMEX.php.html` | RAW HTML, COMEX.php 2026-03-10T00:15:01Z | `8809dec04e5c9c15c7f15dda38f38f4417f96d249a284fbffeacffa6c02d13a4` |
| `archive_NYMEX.php.html` | RAW HTML, NYMEX.php 2026-09-25T17:36:26Z (decompressed) | `9031e0d9a274488d5aba14d256c97b0c4460bce5636c2bb25e5f351b214806ff` |
| `archive_NYMEX.php.html.gz_raw` | gzip bytes as received | `64ecfd220713c2fe765192727d6607500c3fa8998f135601050e1d37916a32a9` |
| `archive_commissions-futures.php.html` | RAW HTML, 2026-09-25T17:33:27Z (decompressed) | `6df03fd5645b67d46ca0d6db8c9689ed92d298571ceb99d59c92e9365040964f` |
| `archive_commissions-futures.php.html.gz_raw` | gzip bytes as received | `50a950c9d2843b331d6b4df122b0bdfc56bc82ece9c3b4f75a9fa191c6e8b0eb` |
| `CME.php.txt` | LIVE 2026-10-03T15:20:30Z tag-stripped render (glue demonstrated; NOT byte authority) | `75a8647065d1590e06db7b1244f72a759b09ec672f8eb2072fd09343a5978565` |
| `COMEX.php.txt` | LIVE 2026-10-03T15:21:30Z render | `4317c15a187162aef9a80c76e63af372b7034a4157e0317b9b634237e798997a` |
| `NYMEX.php.txt` | LIVE 2026-10-03T15:22:00Z render | `dbcc25b3cf519925eebfd9388312c6eca940a27287319a329767b4e58129ed1a` |
| `commissions-futures-amer.php.txt` | LIVE 2026-10-03T15:22:40Z render (?re=amer) | `14d79331c4255addefd7a573c83730f08832508b1ceb3b3b64f9cc4fb0348cda` |
| `CME.php.md` | QUARANTINED transcription-incident record — NOT evidence | `469d8220a061384a0ec80a8d5c1091c06c617a688d1cbb46fc7bb5f4c8de545c` |
| `fees_corrected.json` | machine table, per-cell capture refs — the intended downstream source | `7cd65f253f51ed0bc8fad25dc939797fb4e874ce1d975269f98affa128a2aca8` |
| `FEES_CORRECTED.md` | corrected table + provenance verdict | `006d6372fb5a6f09595d24297174a3a0c1390d27ac869b027adf12bd1b5d1bef` |
| `superscript_adjudication.md` | cell-by-cell glue adjudication narrative | `e36a01239329a869ae64ab5867c50087f23c6977fcdc7f801d18dbaab7d37356` |
| `fetch_log.jsonl` | every fetch attempt incl. blocked transports | `f370f305e53ad6706574bf975f2e935dfc8a2137ac8721016e2b4d0fe1544bf6` |
| `MANIFEST.md` | source-dir evidence manifest | `c8c8ff5a06d5091689d028666633cecba27cb55b9c9ac64d0e3a543958ffed4f` |

Impact layer (`impact/`):
| File | sha256 |
|---|---|
| `FEE_ERRATUM_DRAFT.md` | `3796579d51027d951f527d6989b3da9fcdd3f1395ed4925085782303ce39e5d1` |
| `validate_fee_sources.py` | `fdead766f84521337ff4b7af3a861437a24317831bda9874494fc2c8fe780050` |
| `GATE_REVIEW_NOTE.md` | `5d50ac79c9bca82c696caa7315cbc9c81bcdd4e9a2c09745c6a713efd11161d0` |

Verify layer (`verify/`):
| File | sha256 |
|---|---|
| `P0_ERRATUM_VERDICT.md` | `6967a804468f9a095a45297f1200f49d537d47c3d1442c9a5548af01b0c03575` |
| `p0_verdict.json` | `f1e5b6363af9271be931477d3b6e9197ba57b779c469a0c0dadbc6138c60d347` |

Supporting (context, not hashed here): `verify/p0_verify_expected.json`,
`p0_verify_validator_report.json`, `p0_verify_validator_stdout.log`; frozen spec
`FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md` (§5 L100/101/104); parent transcription
sites listed in the companion reconciliation §2.

## (c) Check list the A7 must run (all read-only at the authorized HEAD)

1. **Input integrity.** Recompute sha256 of every file in §b; diff against
   this packet, `source/MANIFEST.md`, and `p0_verdict.json.outputs_recomputed`.
   Any drift ⇒ stop and report before proceeding.
2. **Source-text re-extraction, per cell** — including **footnote-marker
   disambiguation**. For each load-bearing cell (ES/NQ exchange, CME reg,
   FX-group 1.60, CL/NG exchange + NYMEX reg, GC/SI exchange + COMEX reg,
   commission ladder 0.85/0.65/0.45/0.25 + Fixed 0.85, clearing 0.00, give-up
   0.05): locate the value in the marker-preserving RAW HTML (`archive_*.html`),
   with row-label scoping (e.g. `1.38<sup>2</sup>` on the Housing row must NOT
   be attributed to ES/NQ; `1.38<sup>6</sup>` appears exactly twice — NQ L1691-1695,
   ES L1703-1707). Distinguish: LITERAL clean / LITERAL marker-adjacent /
   FOOTNOTE_GLUED (base + marker = parent value ⇒ parent reading fails) /
   NOT_LOCATED. Tag-stripped live renders (`*.php.txt`) are glue-demonstration
   exhibits, never value authority.
3. **Arithmetic re-check, independent.** Commission ladder deltas
   (−0.20/−0.40/−0.60), tier-2/3/4 all-ins per code, IBKR worked examples
   (`0.85+1.38+0.00+0.01=2.24` Fixed; the Tiered example's known IBKR-side
   stale cell prints reg 0.00 summing to 2.24 — characterize, don't inherit),
   and the IB-JP paren tax arithmetic (`0.011 = 0.01×1.1`; June `0.022 = 0.02×1.1`).
4. **Validator real-mode reproduction.** Run `impact/validate_fee_sources.py`:
   self-test (expect 6/6, exit 0) then real mode against P0-VERIFY's 37-check
   grid `verify/p0_verify_expected.json` (expect exit 1 = ≥1 NOT_LOCATED, from
   the deliberate adverse parent-value checks; corrected values LITERAL;
   `1.386` FOOTNOTE_GLUED ×2). Known validator warts to account for (P0-VERIFY
   §5, raw HTML is authority regardless): argv `--expected/--report` value
   parsing; glue classifier misses span-wrapped markers
   (`0.95</span><sup>4</sup>` → NOT_LOCATED not FOOTNOTE_GLUED); annotation
   header inside `CME.php.txt` makes its MARKERS_PRESENT flag spurious.
5. **Propagation grep reproduction.** Re-run the canonical grep (companion doc
   §1) at the authorized HEAD; reproduce the classification: 25 genuine
   (22 frozen + 3 living) + ERRATUM-SELFREF set + false positives, and confirm
   zero new genuine sites in non-erratum round files. Spot-verify the frozen-vs-
   living labels (living sites: DATACONTRACT_QUALIFICATION §3 L206-207,
   SUMMARY_QUAL_ACTIONS L15, OWNER_DECISION_PACKET L17; supplementary rounded:
   PLAYBOOKS_DRAFT L75/185/210).
6. **Classification audit frozen-vs-living.** Verify no frozen-historical file
   was modified by the erratum rounds (batch-1 commit `72c9bc5b` = 359 files,
   100% additions inside the round dir; re-measure `git status`/`git log` at
   the authorized HEAD rather than trusting this packet).
7. **"No-measured-cost" language scan.** Confirm no artifact claims measured
   account-verified cost: every fee value carries VERIFIED_VS_ACCOUNT=NOT_RUN /
   MODELED_COST; "measured cost"/"complete cost" wording forbidden in family
   docs (e.g. `hypo/es_nq/esnq_hypotheses.json` forbidden_words).
8. **SPEC_PB1_ES under-review consistency adjudication.** Confirm: spec still
   prints the L100/L101/L104 parent-derived lines byte-identically (frozen,
   not silently edited); `GATE_REVIEW_NOTE.md` §1 + `FEE_ERRATUM_DRAFT.md` §4
   record them UNDER REVIEW with the corrected-value consequences stated;
   downstream family docs label the fee layer UNDER REVIEW; and the overnight
   P1 families consume `fees_corrected.json` values, not parent values. Also
   adjudicate the reg-basis divergence recorded in the companion doc §4
   (hypo/es_nq modeled 20.99/33.49/45.99 & 23.49/28.49/33.49 from fee all-in
   2.24 = offset-reg 0.01, vs SPEC §5 NFA-timeline 0.02 ⇒ 21.00/33.50/46.00 &
   23.50/28.50/33.50): rule which basis is canonical for modeled all-ins.
9. **Verdict discipline.** Every A7 claim FACT (capture byte citation) /
   INFERENCE (labeled) / NOT_RUN; missing evidence never PASS; the A7's R2
   must not repeat the parent A7's blind spot ("recomputed exact" =
   arithmetic-vs-transcribed-table, not source re-read — `a7_spec_checks.json`
   L47, `CROSSCHECK_REPORT.md` L21).

## (d) Preconditions and authority statement

- **The A7 runs ONLY on owner/plan authorization. This packet's existence is
  preparation, not authorization.** No scoring, no GO, no ledger/registry
  writes, no order of any kind rides on the A7's result without the standing
  gates (NO_GO_REGISTER/SCORE/ORDER; PB2 HOLD; PB3 PARK; ES 24 frozen
  identities BLOCKED_TRIAL_BUDGET) being lifted by the owner in writing.
- A7 is read-only over the evidence universe; its writable surface is its own
  round dir + handoff, per dispatch law. Append-only: no edits to committed or
  frozen files; corrections supersede by reference.
- Standing context to carry: P3-BROWSER-CAL is QUARANTINED_POLICY_BREACH (does
  not touch this fee evidence chain — different lane, calendar domain); safe
  baseline `d7fc6231`; heavy lock must be respected if the A7 runs anything
  heavy (it should not need to — all evidence is committed captures; zero
  network fetches required or recommended, per P0-VERIFY §6).
- Recommended A7 anchor HEAD: the dispatch-approved HEAD of the round in which
  the owner authorizes it (re-measure and record drift at start; this packet's
  measurements were taken at `0225b3c2`).

## (e) Open items the A7 will need ruled on (owner/plan rulings, not A7-derivable)

1. **FX-group fee mapping corroboration — PARTIAL.** The CME "Forex Futures"
   row (alias EUR/GBP/JPY/AUD + 6H, value `1.60`, sup 9 on the LABEL,
   archive_CME.php.html L1666-1673) never prints `6E/6B/6J/6A` verbatim. The
   1.60 value is CONFIRMED; the alias→symbol binding is inference from IBKR's
   own row naming. One dated binding page corroborating the aliases is still
   missing (recorded PARTIAL in `fees_corrected.json` and family docs, e.g.
   `JPY_AUD_HYPOTHESES.md` L218 "FX fee-group mapping PARTIAL (1 dated binding
   page pending)"). Ruling: accept PARTIAL, or name the binding page to fetch.
2. **Geography footnote interpretation.** CME reg cell marker-1 points to the
   NFA-assessment note; the same cell carries an INLINE IB-JP parenthetical
   "(For IB-JP customers: 0.011 incl. tax)". Adjudicated base = 0.01 for
   non-IB-JP accounts, corroborated by the US-pages worked example
   (`Regulatory Fee USD 0.01`, 2026-09-25 RAW). Ruling needed: confirm the
   owner's account geography (US-entity pages are the operative basis) so the
   paren (a 0.01×1.1 tax artifact) cannot be re-read as a 3-decimal base.
3. **NYMEX reg 0.02→0.01 temporal window.** Parent recorded 0.02; live render
   AND 2026-09-25 RAW both show 0.01 with parent 0.02 NOT_LOCATED in either.
   "Extraction error" for this cell is INFERENCE: a 0.01→0.02→0.01 flip inside
   2026-09-25..10-03 is not physically excludable from this machine (live raw
   transport BLOCKED_TRANSPORT). Related genuine temporal changes already
   byte-captured: GC/SI group 1.60→1.65 (2026-03-10 → live), CME reg
   `0.02<sup>1</sup>` (June-08 RAW) → 0.01 (Sep-25/Oct-03). Ruling: which
   epochs bind historical-year modeling (current-schedule-as-approximation rule
   vs per-year schedule sourcing — family docs already declare pre-2018
   schedules NOT sourced).
4. **(Carried from companion doc §4) Reg-component basis for modeled
   all-ins**: IBKR offset 0.01 (hypo/es_nq 2.24-based, 20.99 family) vs NFA
   timeline 0.02 (SPEC §5 law, 21.00 family). $0.01/side; nothing scored
   today; standardize before any cost-gate adjudication.
