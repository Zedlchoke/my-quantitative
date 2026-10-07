# ERRATUM EXEC-3 — SOCCER real path wired; crosswalk extension; two incidents found and handled (post-GO, 2026-10-07)

Scope: owner instruction 2026-10-07 — complete the REAL SOCCER path into
SPORTS-PAPERTRADE-EXEC-V1 for the registered sport key
`soccer_uefa_nations_league` ONLY (no new competitions; config law unchanged).

## 1. What changed

- `fixtures_for(..., "SOCCER", ...)` no longer returns BLOCKED_FIXTURES_SOURCE
  in real mode. Real fixtures now flow from The Odds API
  `/v4/sports/{key}/events` (0-credit, journaled like every call) through the
  pinned core quota-guarded client: response bytes + a .meta record (endpoint,
  fetched_at, sha256, remaining) are persisted under
  `<data-root>/data/events_<key>.json` as the rows' snapshot source; every
  FORECAST row cites `the_odds_api/events/<key>@<sha12>#<event_id>`.
- Schema law verified against the LIVE payload (first fetch 12:31Z, 0 credit,
  remaining unchanged 493): every event must carry non-empty string
  id/home_team/away_team + parseable UTC commence_time. Schema drift is
  BLOCKED_FIXTURES_SCHEMA; duplicate identity (same id conflicting fields, or
  two ids in one (commence_time, team-set) slot) is BLOCKED_FIXTURES_DUPLICATE
  — 1:1 downstream matching must never be ambiguous. Exact duplicates collapse.
- Crosswalk growth landed per the freeze: SOCCER-INTL-WINPROB-PROSPECTIVE-PREP-V1
  FREEZE_SKELETON §5 lists "extend the 8-pair seed empirically from real
  payloads; fail-closed until then" as an open obligation. The pinned engine
  resolves provider names ONLY through the seed file in the READ-ONLY prep
  worktree, so growth lives in THIS cycle's own
  `research/papertrade_exec/PROVIDER_NAME_CROSSWALK_EXTENSION.csv`:
  the pinned seed's bytes are a strict, enforced byte prefix (the seed can
  never be rewritten or shrunk), the extension sha256 is a required pin in
  this cycle's pins.json (`soccer_crosswalk_extension_csv`), and the pinned
  engine's own crosswalk laws (header, ambiguity, 8-pair floor) re-run on the
  extension at every real run BEFORE the engine is invoked. The engine module's
  crosswalk path is pointed at the verified extension for the process, so the
  engine itself resolves through the same mapping. Rows appended: England→
  England, Croatia→Croatia — identity pairs observed on REAL event
  8a1174de9079b530bd6612e3fde6e2fa (snapshot bbea03c7ec05…), corpus evidence
  results.csv 1098/400 rows. Builder committed:
  `build_soccer_crosswalk_extension.py` (idempotent; refuses any non-prefix
  base). Re-pinning is deliberate and disclosed here. Names still unresolved
  are split per-fixture and journaled CROSSWALK_MISS (dashboard cause
  identity_crosswalk) — never fuzzy, never batch-killing.
- Rerun safety (same-day reruns, append-only): NO_QUOTE/QUOTA_SKIP journals and
  quote rows are never re-written for already-decided matches
  (`_quote_write_plan`, `journal_quota_skip(..., decided=)`); forecast skips
  decided matches; QUOTA_SKIP mid-loop refuses the whole mapping (no partial
  capture). Ledger stays append-only; nothing is overwritten or backfilled.

## 2. Incident A — latent crash on the quote journal path (found by the real run)

The first real soccer `quote` (12:38:09Z, HTTP 200, 1 credit, remaining 492)
mapped its payload to a NO_QUOTE journal row, and the journal append crashed:
`in_lock_recheck_for` imported `research.papertrade.risk` — a module name that
does not exist in this worktree (the core is pinned as `spt_core`). The bug is
pre-existing (the path never executed: earlier WNBA captures matched 1:1 and
wrote rows, never journals). Fixed: the recheck resolves the pinned core
through the package loader; regression test
`test_in_lock_recheck_for_uses_pinned_core` exercises the exact call site.
Cost: the mapped payload and its specific NO_QUOTE reason were lost (the crash
preceded the write; only the quota-journal row evidences the fetch). Per the
no-fabrication law no reason text was reconstructed, and per the no-backfill
law the payload was not re-fetched.

## 3. Incident B — the credit's outcome and why the match is deliberately left undecided today

The ledger gained no quote row from the 12:38:09Z payload (rows list confirms:
the write loop ran before the crash and wrote nothing), so the provider said
no-qualifying-quote for the match; the specific reason is the lost text of
Incident A. Today's quota is exhausted (4/4: three WNBA captures + this one),
and re-running `quote` now would journal QUOTA_SKIP rows — which are terminal
decisions under the one-selection law — killing the match's November capture.
The match is therefore left with its REAL FORECAST row (B1 ENGINE p recorded
12:37:58Z, anchor 2026-11-12T13:45:00Z, kickoff 19:45:00Z — PIT window open
for 36 more days) and NOTHING decided. The lawful continuation is the standard
cadence: capture `quote --league SOCCER --date 2026-11-12` at the next quota
window (00:00Z reset), then `decide`; if the provider still lacks the three
1X2 legs, the fixed code journals NO_QUOTE with the specific reason — the
correct NOT_RUN-with-evidence outcome under the frozen rules. A one-shot
scheduled automation (07:10 ICT = 00:10Z, after the reset) runs exactly that
chain; no GO is typed (the consumed-GO gate stands), no new credits beyond the
standing caps.

## 4. Known pre-existing condition (not introduced here)

The NBA-PREP sibling suite (81 tests) has 1 failure
(`test_f_real_smoke_opening_slate`): it re-verifies the payload corpus against
the frozen composite 3d527b3c…, but the corpus was lawfully extended post-GO
this morning (11:10–11:16Z refresh, REFRESH_MANIFEST chain → e4d3cbe7…). This
cycle's manifest-aware verification (`nba_payload_verdict` via verify-pins)
accepts the chained corpus; the sibling's own strict test predates the chain.
Sibling tree is clean at its pinned head 82542aa8. Recorded, not normalized.

## 5. State after this erratum

- Battery 46/46 (36 prior + 10 new); siblings: WNBA 79/79, soccer 94/94,
  NBA-prep 80/81 (see §4).
- Real ledger (append-only, 8 rows): GENESIS + 2 WNBA FORECAST + 2 WNBA
  MARKET_QUOTE + 2 WNBA BET_PAPER (open, 500c each) + 1 SOCCER FORECAST
  (ENGINE). Equity 1000.00 USD; open exposure 10.00/100.00 USD; no
  settlements today; WNBA/NBA rows untouched.
- Quota: day 4/4, month 4/120, provider remaining 492; every call journaled.
- Credits spent by this work session: 1 (Incident A). Events fetches: 0 credit.
