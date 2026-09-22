# A7 PROBE AUDIT — EURUSD-DATA-QUALIFICATION-V1 P1 bounded probe

- Auditor: A7 (independent, fresh context)
- Audited HEAD: `e49c23cff682ab15507651078f399dd485e9260d`
  (branch `orca/eurusd-data-qualification-v1-integration`)
- Claim under audit: **PROBE_FAIL — gate LICENSE_RESOLVED (Dukascopy UNCLEAR;
  Twelve Data CLEAR_FOR_INTERNAL_RESEARCH but lacks bid/ask on the current
  plan)**, cycle consequence **BLOCKED_SOURCE_LICENSE**, all technical gates PASS.
- Written: 2026-09-22T08:27:57Z
- Machine-readable twin: `audits/a7_probe_audit.json` (schema `edq1_a7_probe_audit@1`)

## VERDICT: AUTHORIZED_BLOCKED_SOURCE_LICENSE

The claim survives every attempt to break it. All technical numbers re-verified
from raw bytes with independently written code; the license reading is faithful
and conservative; the cycle-verdict mapping is forced by plan §3.

## A. License evidence (re-fetched live 2026-09-22)

| Check | Result | Evidence |
|---|---|---|
| Dukascopy TCU verbatim quotes (6 clauses) | PASS | All appear verbatim on the live Terms-of-Use page, incl. the scraper clause ("...without the prior express written consent of DUKASCOPY"), the "construct a database of any kind" clause, the "personal, non-commercial use" License clause. The page's own sic wording "automate device" is preserved by the lane's quote. |
| Historical Data page quotes (3) | PASS | All verbatim; page is descriptive only — no license grant, no mention of `datafeed.dukascopy.com`, exactly as the lane stated. |
| Dedicated datafeed terms 404 | PASS | `.../marketwatch/historical/datafeed/` returns 404 (reproduced by curl); control URL returns 200 from the same network. |
| Twelve Data terms quotes (8 clauses) | PASS | §2.1, §1 Internal Use, §2.2(a), §2.3(b)/(g)/(l), §16.2, §6.1 all verbatim. |
| Status fidelity, no fabrication, no terms acceptance | PASS | **UNCLEAR is a faithful conservative reading**: if the TCU applies, automated acquisition requires prior express written consent and database construction is forbidden; if it does not apply, no license governs the bytes at all — either branch leaves clearance unresolved. No status fabricated. No terms accepted: both fetchers are unauthenticated GETs with a self-identifying UA; the license record explicitly disclaims acceptance on anyone's behalf. |

## B. Technical claims (recomputed from bytes, independent code)

| Check | Result | Evidence |
|---|---|---|
| sha256 manifest vs bytes | PASS | Recomputed for **all 242** files (exceeds required 3): 0 mismatches, 0 byte-count mismatches. |
| Independent bi5 decode (LZMA + `'>5i'`) | PASS | 5 files decoded (3 window + 2 boundary): tick counts 2660/1161/2350/3629/5092 and price-int ranges match the manifest exactly; prices 1.08414–1.09345 (window), 1.08244–1.08375 (2023), 1.15253–1.15475 (2025) — plausible EURUSD. Scale int/1e5 confirmed. |
| Full 240-file tick walk | PASS | 578,916 ticks; 11,527 distinct minutes; 0 duplicate ticks; 0 monotonicity violations — all reproduce exactly. |
| Coverage day math (2024-03-04) | PASS | 1427 minutes / 57,947 ticks reproduce; expected = 1440 − 13 enumerated gap-minutes = 1427, exact. Saturday 2024-03-09: zero minutes, zero ticks. |
| Weekend + DST | PASS | Fri 21:59Z → Sun 21:00Z = 2820 min = exactly 47 h; 47 zero-byte HTTP-200 files; 0 HTTP 404s; DST one-hour shift visible (22:00Z Fri close EST vs 21:00Z Sun open EDT). |
| Span coverage | PASS | 11,527/11,580 = 99.542% reproduces; 44 micro-gaps, 53 minutes, max 3 (the census array's 45th entry is the weekend gap itself — reconciles). |
| Indicative reconciliation | PASS | Full recompute: A (open-labeled) n=11459, median 0.35 pips / p95 1.15 / max 42.65; B median 0.60 — exact match; A wins ⇒ open-time labeling confirmed. 20-minute sample below. TD inventory: 11,509 unique bars, fields exactly {datetime, open, high, low, close} — no bid/ask, no volume on this plan. |
| Timestamp convention | PASS | London-0700 first tick: offset 89 ms → 2024-03-05T07:00:00.089Z, bid 1.08468 / ask 1.08470 — reproduces; all offsets in [0, 3600000). TD pacing ≤8 req/min honored; recorded URLs redacted of apikey. |
| Tests | PASS | Re-run independently: 4/4 PASS. |

### 20-minute reconciliation sample (recomputed by A7)

| TD bar (UTC) | TD close | Duka mid close | abs diff (pips) |
|---|---|---|---|
| 2024-03-04 10:18 | 1.08510 | 1.08514 | 0.45 |
| 2024-03-04 13:15 | 1.08460 | 1.08458 | 0.25 |
| 2024-03-04 15:54 | 1.08620 | 1.08624 | 0.40 |
| 2024-03-04 19:08 | 1.08560 | 1.08570 | 0.95 |
| 2024-03-04 19:50 | 1.08570 | 1.08575 | 0.50 |
| 2024-03-04 23:32 | 1.08575 | 1.08576 | 0.10 |
| 2024-03-05 00:50 | 1.08540 | 1.08540 | 0.05 |
| 2024-03-05 01:46 | 1.08490 | 1.08496 | 0.65 |
| 2024-03-05 17:16 | 1.08630 | 1.08621 | 0.95 |
| 2024-03-06 10:44 | 1.08740 | 1.08742 | 0.15 |
| 2024-03-06 17:50 | 1.09020 | 1.09020 | 0.00 |
| 2024-03-07 16:32 | 1.09350 | 1.09340 | 0.95 |
| 2024-03-08 03:59 | 1.09480 | 1.09474 | 0.65 |
| 2024-03-08 11:56 | 1.09315 | 1.09316 | 0.10 |
| 2024-03-08 18:19 | 1.09355 | 1.09352 | 0.30 |
| 2024-03-10 22:32 | 1.09390 | 1.09388 | 0.25 |
| 2024-03-11 18:42 | 1.09215 | 1.09217 | 0.20 |
| 2024-03-12 02:29 | 1.09340 | 1.09335 | 0.45 |
| 2024-03-12 15:18 | 1.09130 | 1.09129 | 0.10 |
| 2024-03-13 09:56 | 1.09250 | 1.09239 | 1.15 |

## C. Verdict logic

- Plan §1: license must be recorded and resolvable; bytes attributable to
  Dukascopy but no applicable terms found ⇒ `CANDIDATE_NOT_AUTHORIZED` ⇒ the
  verdict cannot be QUALIFIED.
- Plan §3 P1: "fail = any of: license unresolved, ..." and "PROBE_FAIL stops
  the cycle at the matching BLOCKED_* verdict." The failed gate is
  LICENSE_RESOLVED ⇒ the matching enum is **BLOCKED_SOURCE_LICENSE**. Correct.
- No reading justifies stage 2: plan §0a forbids full-history while the license
  is unclear, and skipping Dukascopy is fatal anyway — Twelve Data has no
  bid/ask on this plan, so the cost-authority gate could never pass
  (§4 ⇒ BLOCKED_COST_AUTHORITY). Continuing would spend the heavy-lock budget
  on an unauthorized bulk download — exactly what the owner forbade.
- NOT_RUN items (correctly scoped, must not be inferred as PASS): the formal
  §2 preregistered tolerance test (P2) and 3–5y retrieval scale/throughput
  (P2, heavy lock). `MULTI_YEAR_AVAILABLE` PASS is supportable only as "same
  schema decodes plausible 2023 and 2025 hours" (verified by A7), not as
  multi-year retrieval feasibility — the lane discloses this.

## D. Scope audit

- Lane branch = exactly **1 commit** (`e49c23c`) touching exactly **14 files**,
  all under `research/control/eurusd_data_qualification_v1/`. No strategy, PnL,
  broker, or JEV surface; no imports from backtest/strategy/risk.
- Credentials: `TWELVE_DATA_API_KEY` value read in-memory from root `.env`
  (never printed) — absent from all 1,174 tracked files and from the lane diff;
  no `apikey=<value>` strings; recorded URLs redacted.
- Raw vendor bytes: `data_local/.gitignore` (`*` rule) keeps everything
  untracked; `git ls-files` cycle dir = 14 files, none under `data_local/`
  except `.gitignore` itself.
- `SANDBOX-OVERFIT-3ASSETS/` and `d2_curiosity_v1_sources/`: untouched by every
  commit in this worktree's history.

## E. Handoff validity

`handoffs/lane_source_probe_handoff.json` — schema `zcode_orch_v3_handoff@1`;
dispatch_sha == actual_start_sha (40-hex, resolves, ancestor of HEAD);
commit_sha resolves to the lane commit; tree_status honest. Field-shape
deviations: see findings F1/F2.

## Findings

| # | Severity | Detail |
|---|---|---|
| F1 | MEDIUM | Lane handoff deviates from strict `zcode_orch_v3_handoff@1` shapes: `tests[]` entries {name, verdict} lack command/exit_code/log_digest; `outputs[]` are bare paths without {path, sha256}; `recommended_next_action` absent. Substance independently verified (tests 4/4 PASS; outputs digested in the manifest) — verdict unaffected; fix shape at integration, do not re-dispatch the lane. |
| F2 | LOW | `authority_claims[]` non-empty in a lane handoff (schema: "normally EMPTY for lane agents"); entries are compliance statements, not authorization claims — refusal rule not triggered in substance. |
| F3 | LOW | A7 dispatch packet names audited HEAD as a 39-hex string (`...f399dd48e9260d` missing the `5` at char 34 vs real `e49c23cff682ab15507651078f399dd485e9260d`); prefix unique on the branch; lane's own handoff sha is correct. Dispatch typo for the owner to correct. |
| F4 | LOW | Counting phrasing: "195/195 non-empty" includes the 2 boundary files (window non-empty = 193; 193+2+47=242 reconciles); census gap count 45 includes the weekend entry while prose says "44 micro-gaps" (44+1=45). Arithmetic exact in both cases. |
| F5 | LOW | Dukascopy license search breadth: 2 pages + 1 probed 404 recorded; no other candidate terms locations probed. UNCLEAR errs conservative; a missed blanket clearance is unlikely (TCU written-consent clause); resolution is owner action regardless. |

## Owner decision required

1. **Unblock path (the only one)**: record either (a) Dukascopy's prior express
   written consent for automated retrieval of the public datafeed for internal
   research, or (b) an explicit owner legal determination on the
   TCU-vs-datafeed question. Technical evidence is already probe-grade; P2 can
   start immediately upon either.
2. Correct the malformed dispatch sha (F3).
3. Decide whether Twelve Data's revocable license + §16 retention constraints
   are acceptable for the reconciliation role at P2 scale.

Artifacts are left **uncommitted** (untracked) for A1 integration, per
instructions. My handoff: `handoffs/a7_probe_handoff.json`.
