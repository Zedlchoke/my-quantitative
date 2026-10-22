# ERRATUM_EXEC_5 — LIVE PAPER-EXEC SERVICE (supervisor + auto-settle + live dashboard)

- Cycle: `SPORTS-PAPERTRADE-EXEC-V1` · branch `orca/spt-exec-v1-integration`
- Written: 2026-10-08 (owner instruction, this chat, 09:00Z window)
- Authority: owner instruction 2026-10-08 ("Ưu tiên vận hành
  SPORTS-PAPERTRADE-EXEC-V1: dashboard LIVE … tự nhận tín hiệu … tự settle …
  tự cập nhật dashboard liên tục") — the latest explicit owner instruction
  (authority pointer 1). The ONE GO (`GO SPORTS PAPERTRADE EXEC V1 RUN ALL`)
  was already typed by the owner verbatim at 2026-10-07T11:08:47Z and consumed
  (root + mirror per ERRATUM_EXEC_1 D-1; journal events 2026-10-07T11:19:08Z
  and REGISTRY_SAVED at 11:11/11:19Z; `GO_TOKEN.json` in this control dir).
  Plan §1(5) authorizes scheduling automation for the runner ONLY AFTER the
  GO — that condition is met, so **no new GO is needed and none is typed**.

## D-1 · Scope of what this erratum registers

A durable local service (`research/papertrade_exec/ops_service.py` +
`live_dashboard.py`, launchd `com.myquant.sptexec.ops`) that, on a tick loop:

1. **CADENCE** — per league/date, inside each match's pre-anchor window only,
   invokes the EXISTING frozen runner chain `plan → forecast → quote → decide`
   (the runner keeps every refusal law: GO gate, pins, anchors, PIT, quota,
   one-selection-per-match, in-lock cap recheck). The supervisor adds only a
   POLICY layer: a match enters the capture window
   `anchor − LOOKAHEAD_LEAGUE ≤ now < anchor` with
   LOOKAHEAD WNBA/NBA = 24 h, SOCCER = 48 h (limits early price lock-in
   without ever crossing the anchor). Fixture discovery for SOCCER uses the
   0-credit `/events` endpoint, cached ≥ 30 min per sport key. Odds credits
   are spent only for in-window matches that still lack a quote (the runner's
   own write-plan filters decided matches), under the frozen 4/day + 120/month
   quota law.
2. **SETTLE** — for each decided BET_PAPER row with `kickoff + 3 h` passed and
   no SETTLEMENT row: fetch the result from the D-2 source; only a
   `completed=true` FINAL with 1:1 identity produces a settle attempt via the
   existing `settle` subcommand (append-only, duplicate-refusing). Anything
   less (non-FINAL, missing event, ambiguous identity) keeps the bet OPEN and
   journals the reason; retries back off (ESPN 30 min; The Odds API scores
   ≥ 6 h — it costs a credit). Postponed/cancelled is recognized ONLY from an
   explicit source status → `VOID` refund per frozen settlement law.
   **No backfill**: results are fetched AFTER kickoff+grace; forecasts/quotes
   are never written after an anchor (runner-refused).
3. **DASHBOARD** — rebuilds the pinned static dashboard after every ledger
   change AND serves a LIVE local web page (`live_dashboard.py`, binds
   127.0.0.1:8791 only) that re-reads + `verify_chain()`s the ledger on every
   request and exposes: service status/heartbeat/latency, quota, wallet
   (equity/peak/drawdown/exposure), per-match forecast/odds/EV/decision/
   result, NOT_RUN causes, incidents. Auto-refresh ≤ 10 s client-side.
   SANDBOX and REAL ledgers are never rendered as each other (mode badge from
   the GENESIS row's `sandbox` flag). Key bytes never enter the page, the
   state JSON, or logs (only the 12-hex fingerprint may appear).

$0 spend beyond existing free/credit-capped endpoints; no purchases; no
push/merge; no new typed GO; no gate loosened; heavy machine-wide lock not
required (this service does no heavy compute; it holds its own
`ops/service.lock` single-instance flock).

## D-2 · Settlement result sources (identity + timestamp law)

| League | Source | Identity | FINAL test | Cost |
|---|---|---|---|---|
| NBA / WNBA | ESPN public scoreboard `site.api.espn.com/apis/site/v2/sports/basketball/{wnba|nba}/scoreboard?dates=YYYYMMDD` | event `id` equals the ledger `match_id` BY CONSTRUCTION (the pinned schedules' ids ARE ESPN event ids, e.g. 401918297/401918298) + home/away display-name cross-check vs the ledger row | `status.type.completed == true` (+ score fields present) | free |
| SOCCER | The Odds API `/v4/sports/{key}/scores` (same key/quota/pin law as capture) | event `id` equals the ledger `match_id` (same source that produced the fixture) | `completed == true` with both scores | 1 credit, quota-guarded, ≥ 6 h between attempts |

Soccer settle is restricted to stage-law-ELIGIBLE matches (UNL league phase =
90-minute full-time, where the FT score IS the bookmaker 1X2 settlement
basis); knockout-phase matches remain fail-closed per the competition law
(config v2). Raw response bytes + fetch meta are persisted under
`ops/results/evidence/` before any settle attempt (append-only evidence).

## D-3 · Settlement audit performed under this erratum (2026-10-08)

Both open BET_PAPER rows were audited against ESPN (probe 2026-10-08T08:57Z,
free, no key):

- `401918297` ATL 101 – NY 98 (`Final/OT`, completed) — chosen HOME → WIN
  (+395 c). Identity: ESPN id 401918297 = ledger match_id; ESPN "Atlanta
  Dream" home = ledger home ATL.
- `401918298` GS 83 – LV 81 (`Final`, completed) — chosen HOME → WIN
  (+405 c). Identity likewise (Golden State Valkyries home = ledger GS).

Settlements are executed through the frozen `settle` subcommand with the
fetched results file + evidence snapshot; the ledger will carry two SETTLEMENT
rows with `source_ref` = espn_scoreboard identity strings and the fetch
timestamp. No forecast/quote was created or altered by this audit.

## D-4 · Registry drift noted (no manual edit)

The registry row's `phase` field truthfully reads `GO_CONSUMED CAPTURE_ACTIVE`
(evidence above) while the `go_phrase_state` field still reads
`REGISTERED_NOT_CONSUMED`. The consumption events in
`plans/CYCLE_REGISTRY.events.jsonl` (2026-10-07T11:19:08Z "GO_CONSUMED 2026-10-07
— owner typed verbatim …") plus the mirrored `GO_TOKEN.json` are authoritative;
`go_phrase_state` is a stale bookkeeping field the researchctl `cycle update`
surface does not expose. Resolution: recorded here (CAS-only policy — no hand
edits to `plans/CYCLE_REGISTRY.json`), and the refreshed `--phase` label via
`researchctl cycle update` carries the drift note. If a future researchctl
version exposes the field, it may be CAS-normalized with this erratum as the
reason reference.

## D-5 · Boundaries re-affirmed

PAPER ONLY (virtual cents), wallet 1,000.00 USD genesis, fixed 5.00 USD stake,
100.00 USD open cap, EV ≥ 5% at c = 0.02, 10% drawdown pause, one selection
per match, PIT/no-backfill anchors. Real money: never. Purchases: never.
Push/merge: never. Public web exposure: never (bind 127.0.0.1 only). WNBA
season ≥ 2027 stays NOT_RUN behind the untouched prospective-prep GO. Any
gate this service cannot satisfy is fail-closed and journaled as NOT_RUN /
BLOCKED_* with the specific reason — never worked around.
