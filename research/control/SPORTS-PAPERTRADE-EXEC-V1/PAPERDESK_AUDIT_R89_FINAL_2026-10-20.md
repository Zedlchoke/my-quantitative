# ROUND-8/9 AUDIT + READINESS CONCLUSIONS — 2026-10-20 (controller-run,
# compact; a full independent A7 re-dispatch remains available on request —
# delta-7 (independent) covers everything through b42d8e7b)

## 1. Round-8/9 delta verification (controller-run, evidence committed)

- NBA restore: worktree re-added at 82542aa8; loader.py/predict.py pin-shas
  verified OK; probe_engine WIRED_ENGINE_READY; 11 real B1* FORECAST rows
  via pinned core (chain 59 OK). VERIFIED.
- WSL D-1 automation: launchd com.myquant.wslprov.d1 (15:00 ICT daily,
  forecast-only) installed + kickstart verified (D=Oct 21: 0 fixtures);
  M50-56 provenance rows written; IDEMPOTENCE proven (rerun written=0/
  skipped=1). VERIFIED.
- AI default shadow-live on key-present: FIRST REAL OPINION produced —
  model minimax/minimax-m3.1-flash:free, COMPLETED, verdict ABSTAIN
  (lawful: evidence insufficient), 1 system-captured source + 1
  model-claimed source discarded, sidecar only. LIVE_CASE_VERIFIED for
  the OpenRouter provider chain.
- Main ledger: 59 rows (42 + 11 NBA FORECAST + 6 WSL SETTLEMENT), chain OK;
  sha 58edc089… verified unchanged by the sandbox battery (no test writes).

## 2. WSL forecast TIMING law (owner item 3) — basis-of-record lock

The Oct-20 provenance rows for Oct 24-25 were computed from the ONLY
qualified corpus state available (R5-sealed — identical to what a D-1 batch
on Oct 23 would produce, since R6 finals remain unposted upstream
[re-verified live 2026-10-20]). D-1 job simulation TODAY: adapter finds the
existing rows → skips → writes NOTHING (idempotence proven). Therefore the
Oct-20 rows ARE THE BASIS OF RECORD for the Oct 24-25 window.

**LAW (erratum-grade): `wsl_substrate_corpus.jsonl` is FROZEN at the Oct-20
basis (sha-recorded at next touch) until the Oct 24-25 decide windows
close.** If R6 finals enter upstream before then, they feed the NEXT
generation (M50+ windows), NOT this one — refreshing mid-window would
diverge the exec replay from the provenance basis ⇒ BLOCKED_FORECAST_
DISAGREEMENT ⇒ NOT_RUN (the failure the freeze prevents). STALE_CORPUS
posture is displayed; no scores are fabricated from UMA W/D/L.

## 3. NBA e2e status

Pin restored → plan probe: 11 real regular-season fixtures (opening
window), forecast-only run wrote 11 B1* rows through the pinned core.
Quote/decide: NOT_RUN_PENDING_WINDOW — anchors open Oct 20 ~17:20Z for the
Oct-21 tips; the owner's live cadence (quota-guarded) executes quote →
EV/risk → decision at window open. NBA LIVE_CASE_VERIFIED only after the
runner's own rows exist.

## 4. Per-gate conclusions (owner decision points)

- **POLYMARKET_CUTOVER: NOT_READY.** WSL is the only league where PM is
  the decision quote (live, proven 6/6 settlements). NBA/WNBA/soccer
  remain pre-cutover (Odds API/ESPN pinned paths). Cutover requires:
  (a) owner consumes the registered phrase; (b) NEW 2-way moneyline
  joiner/walker for NBA/WNBA (PM NBA markets are 2-outcome — the existing
  3-YES joiner is soccer/WSL law and MUST NOT be applied); (c) live
  book-walk evidence per league. Estimate: a bounded build + A7 after GO
  for soccer; NBA/WNBA joiner is real build work (not a flag flip).
- **AI_AUTHORITY: NOT_READY (machinery READY).** The mandatory gate
  (AI_GATE_MANDATORY_V1, 17/17) + real OpenRouter opinion chain are proven
  end-to-end in SHADOW. Authority requires: owner-registered cycle naming
  the enforcement boundary (which runner code consumes gate.decision),
  A7 prelaunch on that path, owner GO typed at its gate.

## 5. Lifecycle law (owner item 4) — CONSISTENT

The WSL D-1 launcher is FORECAST-ONLY: it writes the provenance ledger
(never the paper ledger, never a bet; runReview/enforcement are app-side).
Paper lifecycle stays: app open → runner runs; app quit → runner stops.
The launcher running with the app closed does not violate this — it only
prepares PIT evidence; decisions happen only while the app (and runner)
run. Documented in RUNBOOK; UI unchanged.

## 6. Final machine state (measured)

HEAD 843fb5a3 == registry (doctor NONE, pre-erratum-commit); tree clean
post-commit; main ledger 59 rows chain OK; owner's PaperDesk + runner
RUNNING (their choice); launchd runner-label disabled+absent;
com.myquant.wslprov.d1 loaded (forecast-only, enabled by owner order);
opslock HELD by the live runner.
