# W1.4 adoption rounds 1–3 — 2026-10-24

## Authority and gate

Owner round2 and round3 instructions expressly authorize merge main, rebuild/restart and push only after fresh independent A7 PASS/PASS_WITH_FINDINGS with zero open HIGH/MEDIUM. A7_ROUND3_REPORT.md verdict PASS, 0 HIGH, 0 MEDIUM, independently bound to target 7dbcb6cb004d93547e379100d13f3fb615651ca2. Artifact commit beb542694c53dc44c8afdd995596a950a3f2c238; final audited lane HEAD 16b9169aca5ddc80e3e6a789299524d343f9067c. Lead independently checked handoff schema, git scope and output digests (ADOPTION_HANDOFF_VALIDATION.json). Orchestrator store unavailable; no store validation claimed.

## Repair history and limits

- Round1 8d790592: replace price-only blocking with source identity; price twins nonblocking with public notes. A7 BUG_REFUSE: explicit tokens ignored and missing-ID diagnostic priority wrong.
- Round2 300297d6: actual token/outcome principal identity, semantic fallback disclosed; both-side identity validation before collision classification; owner two-tier legacy rule. A7 confirmed these repairs but BUG_REFUSE for one WSL caller KeyError before guard.
- Round3 81ba710f0480bade3fde145569f3b8944c9e46dd: exact move of existing W1.4 block before WSL downstream source indexing/stake/recheck. Actual caller regressions persist exactly one terminal zero-stake QUOTE_IDENTITY_MISSING with missing fields. Standard caller scan and regressions found no corresponding source bug; execute.py byte-identical to round2.

Candidate missing required identity always fails closed. Incomplete historical peer sharing any available strong payload/event/market ID also fails closed as QUOTE_IDENTITY_MISSING. Otherwise incomplete peer is excluded with public INCOMPLETE_PEERS_SKIPPED count and per-row disclosure; no historical data or identity fabricated. Complete quotes sharing payload, bookmaker+market or event+token identity across fixtures remain blocking. Equal prices alone yield PRICE_TWIN_OBSERVED.

## Frozen full-ledger replay (descriptive)

46 MARKET_QUOTE records, 10 incomplete legacy rows. Each candidate compared against the entire frozen ledger. Historical decisions were not changed and these replays were never appended as production decisions.

| Candidate match_id | W1.4 status | INCOMPLETE_PEERS_SKIPPED | Price twin match_id |
|---|---|---:|---|
| 401909853 | CLEAR | 10 | 401909845 |
| 401909095 | CLEAR | 10 | 401909093 |
| 401909849 | CLEAR | 10 | 401909850 |
| 401909850 | CLEAR | 10 | 401909849 |

CLEAR is only W1.4 status, not EV/AI permission or proof of strategy edge. Per-row evidence remains ROUND2_FULL_LEDGER_REPLAY.json and A7_ROUND3_TEST_LOG.txt.

## Verification

Round1 347/347; round2 364/364 twice; round3 full PaperDesk battery 372 passed/0 failed/0 skipped twice (65.06s and 62.20s, equal counts). A7 independently reran 63 tests, exact original WSL caller probes, 31 missing-field subsets, 6 blank cases, complete control, baseline sensitivity, prior F1/F2 and two-tier cases plus all four full-ledger candidates. Postmerge targeted caller+identity+W1 suite 63/63 in1.55s.

V3 registered SHA c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890. Frozen56 FORECAST SHA f12710e2d5f89b5d232d5b49358d791d7fa0b49d77152dc9c61baf8ac02cf0f4; first48 f6dd607c6ebb6e6173047a06208b9c6ea733e67599a43e99068cfa36dadc5240. All unchanged after restart. Configuration unchanged; root W1.4 source byte-equal audited lane. W1.5/EV/AI/stake/selection laws unchanged. No scientific trial, denominator delta +0/+0, S1 untouched; no family kill or survivor.

## Adoption and runtime

Main merge 5720612e1f8cdfd961aeb3cbc267aa1d33ce46dd (normal merge, no history rewrite). Old exact root ops PID15385 stopped cleanly with SIGTERM after audit gate; old app PID44911 quit. Electron arm64 build/codesign PASS. Launch explicitly selects merged root: `open -a /Users/hoangminhlong/my-quantitative/apps/paperdesk/build/PaperDesk-darwin-arm64/PaperDesk.app --args --worktree /Users/hoangminhlong/my-quantitative`.

App PID5797; production paper ops PID5814, cwd merged root, started03:46:58Z. Native app observation: RUNNER LIVE pid5814 child, ledger chain OK169rows, live trading sealed. Heartbeat tick261 at06:59:17Z; API localhost8791/api/state HTTP200. See ADOPTION_RUNTIME.json. Build-time ledger check168rows chain OK; normal runner subsequently appended settlement, app chain169rows OK. Initial40s startup heartbeat check timed out; later live heartbeat/UI confirmed without another restart.

Existing AI provider problem persists: latest pass reviewed7, provider_failed1, rate_limited6, written0; fail-closed AI gate unchanged. Runner liveness and audited source adoption are confirmed; fresh production W1.4 candidate acceptance is not claimed. Shadow ensemble service not changed by this adoption.

## Closeout

Cycle closes with audited lane preserved, workers0, budget0/0 and owner acceptance gate met. Registry CAS plus append-only events and projection, engineering-only hypothesis ledger/MAP entry are control-plane landing. Final evidence commit/push follows this dossier; exact final remote HEAD is reported to owner after verifying remote equality. Global doctor has legacy unrelated findings; per-cycle findings and projection consistency are checked separately, never relabeled global PASS.
