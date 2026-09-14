# PROSPECTIVE-SHADOW-V1 — P1 Identity Recovery (provenance)

Task: `shv1-p1-identity-recovery` · lane `p1-identity-recovery` · role
`quant-implementer` · branch `orca/shv1-identity` · base
`bd5e3437dd90384f7754cc8e33acb96337500f2d`.

This artifact set recovers and hashes the EXACT historical identities of the
three frozen crypto anchor families so a forward shadow engine can re-express
them without guessing. It is evidence-only: no strategy code, no network
access, no scored computation.

## What was recovered

| Anchor family | Historical family | Identity source | Verdict label (RETAINED) |
|---|---|---|---|
| `ILLIQ-AMIHUD-28D-W` | `A8-V11-ILLIQ-AMIHUD` | commit `c97283e0d1681c24ee9a637a4fb1628d0334b7e1` (V11 selection freeze spec + `research/v11/families/illiq_amihud/*` + 3 test files) + verdict bytes at `df18f53dba30291065f9be157cae04bdcf15bf50` (V11 TERMINAL) | `V11_FAMILY_REJECT` |
| `BASISLV-PREMFADE-28D` | `A14-V14-A5-BASISLV-PREMFADE` | commit `183554add4db82444d3e71beb24fb247c6b420b2` (V14 TERMINAL: selection freeze + `research/v14/families/basislv_premfade/**` incl. `frozen_identity.py`, `strategy.py`, `golden/` + `terminal_report_v14.json`) | `V14_FAMILY_REJECT` |
| `XSECT-FUND-CARRY-7D` | `H-XSECT-FUNDING-CARRY-v1` | tracked working-tree files at base HEAD: `research/hypotheses/H-XSECT-FUNDING-CARRY-v1/{candidate.yaml,status.yaml,hypothesis.md}`, `research/wayfinder/evidence/v6-closure-addendum-20260825.{md,json}`, plus the V6 audit files the addendum names: `research/audits/v6/scientific_audit.json` (sha256 prefix `34859a64`, pinned by the addendum cross-check) and `research/audits/v6/final_transition.json` (immutable lineage record) | `CANDIDATE_FAIL` |

## Provenance caveats (read before consuming)

1. **Lineage.** The V11 identity/terminal commits (`c97283e0`, `df18f53d`) live
   on the `orca/v11-integration` lineage and the V14 terminal commit
   (`183554add4`) on `orca/v14-integration`. None of them is an ancestor of
   this cycle's base `bd5e3437`; they were read READ-ONLY from the shared git
   object store of the same repository (`git show`, `git ls-tree`). No file
   outside this lane's allowed paths was written.
2. **Verdict bytes post-dating the identity commit (family 1).** At
   `c97283e0` the freeze spec + implementation exist but the sprint terminal
   verdict does not; the authoritative verdict bytes (`family_verdict_illiq.json`,
   `terminal_report_v11.json`) were committed at V11 TERMINAL `df18f53d`, of
   which `c97283e0` is a git ancestor. Family 2's identity and verdict share
   one terminal commit.
3. **Concentration digit disclosure (family 1).** The cycle plan prose cites
   symbol concentration `0.705497`; the committed producer verdict bytes say
   `largest positive-fold share=0.7055` (4dp) and the A7 terminal wave-2 audit
   independently recomputed `0.7022573519976983` with an explicit
   `match_4dp: false` disclosure. This manifest pins the producer bytes
   verbatim and arbitrates nothing.
4. **Family 3 ambiguity (bounded, disclosed).** `candidate.yaml` pins universe,
   clocks, feature, lookbacks, side rules, rebalance, folds/purge and risk
   caps verbatim, but several score-affecting fields remain literal
   `TO_FREEZE_AT_AUTHORIZATION` placeholders (`effective_window`,
   `data_hashes`, `folds_clocks_warmup_contract`,
   `funding_publication_convention`, `pipeline_versions`,
   `trial_ledger_and_dsr_estimator`, `gates_scorecard_tiebreak_limits_seeds`)
   and the spec never reached A1 `SPEC_LOCKED` (`draft: FROZEN_FOR_EXECUTION`,
   `locked_by: none`). The V6 execution-time realizations live in
   `results/portfolio_v6/*` artifacts outside this lane's allowed read scope;
   the addendum pins them by sha256 only. Nothing is inferred or substituted
   (see `identity_ambiguity` in the manifest).
5. **Anchor metrics for family 3** are quoted from the hashed addendum bytes:
   net `+20,580.87` USDT on the 100k baseline, PF `1.1570`, MDD `8.84%`
   (`0.08835025043410369`; the `28.85%` MDD claim is REFUTED by A7 finding
   F-1), folds `+10,866.10 / +10,169.00 / −454.21`, top positive fold share
   `0.5165701411874007` on F1 (`51.66% > 50%`).

## How the hashes were computed

- `sha256_of_content` = `hashlib.sha256` over the EXACT bytes: `git show
  <commit>:<path>` for commit-sourced files; direct file read for
  `WORKING_TREE_TRACKED` files.
- `git_blob_sha` = the blob id from `git ls-tree <commit> -- <path>`, or `git
  hash-object <path>` for working-tree files.
- `byte_len` = exact byte count of the same bytes.
- `tests/test_shv1_identity_recovery.py` independently recomputes all of the
  above from git bytes and fails loudly on any drift, missing file, missing
  verdict label, or missing verbatim parameter substring.

## Verdict labels are frozen history

All three historical verdict labels — `V11_FAMILY_REJECT`,
`V14_FAMILY_REJECT`, `CANDIDATE_FAIL` — are RETAINED exactly as recorded by
the historical bytes and are NOT rewritable in cycle
PROSPECTIVE-SHADOW-V1. Nothing in this cycle re-scores, re-judges, or
rehabilitates these families.

## Replay labelling rule (binding on the forward shadow engine)

`REPLAY_NOT_PROSPECTIVE` — any replay by the forward shadow engine over the
historical windows (V11 2025-08-22..2026-08-21, V14 2025-08-22..2026-08-21,
V6 scored trials) MUST be labelled `REPLAY_NOT_PROSPECTIVE`. Only
observations generated strictly forward of an authorization decision may
carry prospective labels.
