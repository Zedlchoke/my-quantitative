# REVIEW_LOG — SHARED-PORTFOLIO-100K-V1

## Review 2 — independent reviewer (fresh context), 2026-09-25 — A4-v2 / PhorecOne (gate A)

- Scope: `plans/DRAFT_amendment_PSCTV1_A4_shared_portfolio_100k_epoch2.md` (v2),
  `epoch_config.json` @2, `one/read_model.py`, `one/serve_one.py`,
  `one_app_entry.py`, `tests/test_one_app.py`; cross-checked against
  `ECONOMIC-ROBUSTNESS-PROGRAM-V1/PORTFOLIO_MIGRATION_COMPAT.md`,
  PSCTV1 A1 (2026-09-24) verbatim, A2 activation artifact
  (`cost_regime_boundaries/BANDRIDGE_A2_ACTIVATION.json`: GO 03:41Z → T_act
  03:57:05Z, digest b84ae93e…, 61 ledger rows), daemon dedup core.
- Verified clean: 33/33 tests at review time; GO phrase byte-identical
  draft↔config; gate fields ↔ `_validate_activation` exact match; FX dedup
  byte-equivalent to daemon; no write path in the app; activation flip →
  PREVIEW_FORCED; A2 framing modifies no A2 law.
- Verdict at review time: **NEEDS_FIXES** (0 BLOCKER, 2 MAJOR, 5 MINOR, 3 NOTE).

### Disposition

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | Post-activation FX epoch-2 booked full PnL of pre-T* opens; boundary manifest unconsumed | MAJOR | `_epoch2_two_sleeves`: trades paired with open-ts; FLAT_START → carried closes stay entirely in epoch-1; REOPEN_AT_MARK → (close − boundary mark) from operator manifest, missing manifest → UNAVAILABLE (ACTIVE_PARTIAL), never silently booked; tests added |
| 2 | R1–R5/caps presented as binding but enforced nowhere | MAJOR | Draft §3.4 rewritten: caps are DECISION-SUPPORT/DISPLAY ONLY until owner defines an enforcement point; frozen 1.5-lot vs 150% cap = disclosed conflict requiring explicit owner sizing decision — never silent scaling |
| 3 | BR missing marks ≥ T* silently contributed 0 to total | MINOR | BR part UNAVAILABLE, epoch-2 status ACTIVE_PARTIAL; test pins it |
| 4 | Calendar totals ignored usdt_usd_ref | MINOR | `calendar()` multiplies BR day-PnL by declared ref, label "USDT×ref" |
| 5 | Cold launch listed as test but only manual | MINOR | Draft §7 states manual check (performed 2026-09-25) honestly |
| 6 | v1 test fixture used CONFIRMED3 (stale after @2) | MINOR | Fixture updated to EQUAL_2WAY; also fixed PREVIEW_FORCED still computing epoch-2 numbers (epoch-2 gated on valid ACTIVE in both engines) |
| 7 | CAPS box hardcoded; day_detail limited trades | MINOR | CAPS box renders from config values; day-detail limitation accepted (drill-down covers journal history via closed-trades table) |
| 8 | Gate B inventory: Quant dashboard not currently running (stale pidfile 57257, no listener) | NOTE | Draft §8 updated with snapshot pids + re-measure-at-gate-B instruction |
| 9 | FX plan §3 non-supersession absent from config | NOTE | `supersedes_note` extended: FX dashboard contract keeps serving until gate-B decommission |
| 10 | This review not yet recorded | NOTE | This entry |

Post-fix state: **36/36 tests pass** (19 engine + 17 app). PhorecOne rebuilt,
cold-launched, `/`+`/logo.jpg`+`/one.json` 200, mode PREVIEW, caps from config.

Residual known limitations: USDTUSD monitoring procedural; caps not enforced
anywhere (owner decision pending); cold-launch manual; Quant dashboard
pidfile stale (verify at gate B).

## Review 1 — independent reviewer (fresh context), 2026-09-25 — v1 artifacts

- Scope: `plans/DRAFT_amendment_PSCTV1_A4_shared_portfolio_100k_epoch2.md`,
  `epoch_config.json`, `portfolio_lib.py`, `AUDIT_sizing_fx_shared_100k_v1.md`,
  `tests/test_portfolio.py`, `phorec2/serve_phorec2.py` (+ cross-check against
  the FX daemon core and real PSV1 marks).
- Verdict at review time: **NEEDS_FIXES** (1 BLOCKER, 3 MAJOR, 5 MINOR, 2 NOTE).
- Verified clean by reviewer: zero write paths to epoch-1 sources; GET-only
  servers; FX replay dedup keys byte-identical to the daemon's; crypto equity
  identity spot-verified exact on real marks; dashboard epoch separation and
  UNAVAILABLE/GROSS labeling.

### Disposition

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | Audit pip value ×10 overstated ($100 vs $10/pip/lot) | BLOCKER | `scripts/sizing_audit.py` corrected (lots×10), audit regenerated; amendment §3.4 rewritten on corrected math. Corrected: 1.5 lot 200-pip both = $6,000 (6%); binding constraint is the LEVERAGE caps (FX 369% > 150% cap). |
| 2 | R3 total cap never binding (class-only headroom) | MAJOR | `apply_capital_rule` now takes min(class headroom, total headroom); cross-class test added (`test_capital_rule_cross_class_total_cap_binds`). |
| 3 | Activation = bare JSON flip (no validation) | MAJOR | `_validate_activation`: ACTIVE honored only with T_STAR + open_position_law + allocation.mode + rule_digest + review_log_sha256, else `PREVIEW_FORCED` with reason; tests `test_activation_is_fail_closed_until_all_go_fields_present`. |
| 4 | Post-GO epoch-2 computation missing (dead `None if not active else None`) | MAJOR | `_epoch2_block` implemented: FX closes at/after T_STAR, crypto baseline = first mark ≥ T_STAR, opening equity 100k; inert while PREVIEW; test `test_epoch2_only_counts_post_activation_data`. |
| 5 | Missing law tests (activation refusal, R4 min-unit, cross-class, USDT ref ≠ 1, synthetic RECON_FAIL) | MAJOR | All five added; suite now 19 tests, all passing 2026-09-25. |
| 6 | Config rationale falsely claimed alphabetical order | MINOR | Rationale rewritten: USD sleeve first, then PSCTV1 mounting order; declared fixed. |
| 7 | FX min-unit $11.5k underestimate (1.15 price hint) | MINOR | Conservative constant: 0.10 lot × 100,000 × 1.35 ≈ $13,500. |
| 8 | USDTUSD monitoring promised but not automated | MINOR | Config now states MANUAL/PROCEDURAL honestly; no code fetch. |
| 9 | REVIEW_LOG missing | MINOR | This file. |
| 10 | Audit gross drift / docstring overstated "out/ cache" | NOTE | Audit regenerated at close of fixes; serve docstring accurate (in-memory cache only). |
| 11 | (clean checks) | NOTE | No action. |

Residual known limitations (disclosed, GO-gated work remains):
- Epoch-2 day-boundary attribution for carried positions relies on the
  operator's boundary rows at activation (engine baseline = first mark ≥
  T_STAR as proxy; boundary rows are authority).
- USDTUSD monitoring is procedural, not automated.
- `Quant Shadow Dashboard` (PSV1 worktree `dashboard/dashboard_app/page.py`,
  port 8791) still renders the old 400k framing — replacing it is a cutover
  item under the owner's GO, not done in this preview.
- `realized_today` field in the FX daemon state appears to carry the previous
  UTC day's realized across midnight (journal replay is authoritative;
  display-level daemon quirk observed 2026-09-25, reported, NOT fixed — worker
  untouched).
