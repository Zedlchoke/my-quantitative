# EDGE-SCANNER FEASIBILITY REPORT — integration survey (read-only)

```text
survey_id       EDGE-SCANNER-FEASIBILITY-V1
date_utc        2026-09-26
requested_by    owner instruction 2026-09-26 (parallel feasibility study)
upstream        github.com/simonro/edge-scanner
pinned_sha      c927dcb0c5e8122269812d2cdfdc4a3ae71b2ab3   (refs/heads/main, verified by git ls-remote AND shallow clone rev-parse)
upstream_license MIT (c) 2026 "Tape to Edge"; NOTICE covers lightweight-charts (Apache-2.0, attribution-logo required) and schwabdev (MIT)
survey_mode     READ-ONLY. Zero code executed from upstream, zero pip/npm installs,
                zero network calls by survey tooling, zero API keys. Static reading only.
lanes           Lane T (technical) + Lane S (scientific), independent, parallel.
repo_state      root @ c9956ac7 (main). Running cycles untouched: PWS-CX-SOLUSDT-C1
                ACTIVE_LIGHT (HEAD drift 9f1a8c4 vs registry ef3418d = that lane's own
                in-flight work, not ours), heavy lock FREE_PROVEN at survey start.
writes          this control dir + plans/DRAFT_EDGE-SCANNER-TOOLING-V1.md ONLY.
                No registry/ledger writes, no IDENTITY_REGISTRY rows, no scoring,
                no OOS looks, no shadow/dashboard touching, no orders, no push.
```

## 0. Headline

1. **edge-scanner is a well-engineered US-equity intraday ALERT SCANNER, not a
   strategy and not research infrastructure.** 46 native triggers
   (`scanner/trigger_catalog.py:171-402`; the "~45" belief is verified — README
   itself says "about 45"), 18 library setups, 16 seeded presets; live-only,
   stateful, no PIT replay discipline. Its own README says the setups are
   "starting points, not a strategy".
2. **Lane S verdict: 0 of 46 triggers survive paper screening.** Every cluster
   dies on ≥1 (usually 2–3) independent axes: no portable payer (no opening
   auction / no consolidated VWAP benchmark / no float-short-interest / no
   halts on FX or 24/7 perps), dead-family collision (range-edge fade +
   gated variants permanently closed; SRLVCX1 sweep-reclaim; breakout/
   compression classes; funding-level gates rho≈1.0), fatal cost arithmetic
   (P3-A: novel PIT-clean mechanism still measured 0.9–1.0 pip crossings vs
   ≤0.41 required; FX stressed RT floor 3.6/4.4 pips), or BLOCKED data class
   (depth/OI/liquidations). **REJECT for all strategy semantics. No
   RESEARCH_IDEA_ONLY survivors — so nothing is proposed into the
   IDENTITY_REGISTRY and the ≤100 ceiling is untouched.**
3. **Lane T verdict: a small tooling surface is genuinely reusable.** Best
   candidate: `scanner/local_guard.py` (110-line pure-ASGI localhost +
   DNS-rebinding + content-type guard) for hardening the workspace's local
   sidecar surfaces (LIVE-DATA-GATEWAY-V1 class). Five further components are
   worth adopting **as patterns/design rules, not code**. The trigger engine,
   providers, dashboard code, and anything sizing/score-shaped must NOT enter
   the workspace.
4. **Security/license posture is good for a local tool**: MIT with a clean
   NOTICE; one anonymous GitHub egress at startup (kill switch
   `UPDATE_CHECK=0`); localhost-only by default with no auth BY DESIGN (an
   accepted risk documented in its own `.env.example`); no eval/exec/pickle;
   deps floored AND capped with CVE reasons. Residual risks listed in §3.

## 1. What is reusable (Lane T) — triage

| # | Component (upstream cite) | What it gives | Coupling cost | Decision (this survey's recommendation) |
|---|---|---|---|---|
| 1 | `scanner/local_guard.py` (+ `tests/test_local_guard.py`) | Localhost/DNS-rebinding/content-type guard middleware for any local FastAPI/uvicorn sidecar; covers WebSockets; pure ASGI | starlette import only; env var semantics; zero domain coupling | **ADOPT_TOOLING** (the only vendoring recommended) |
| 2 | `scanner/data/quote_bars.py` `QuoteBarBuilder` | quote→1-min-bar reconstruction: odd-lot SEC tiers, counter-reset vs revision, volume scale calibration, injectable clock | pandas only; encodes US-equity tape microstructure — irrelevant to FX/CX venues | **ADOPT_TOOLING (DEFERRED)** — vendor only if a US-equity data-plane cycle ever opens |
| 3 | parquet cache discipline (`data/alpaca.py:39-108`, `cache/parquet.py`) | adjustment-named cache dirs, per-timeframe dirs, spacing heal, provider-isolated trees | pattern ports in an afternoon; code is Alpaca-flavored | **ADOPT_TOOLING (pattern only)** for gateway cache law |
| 4 | `alert_sink.py` cooldown/dedupe (89 lines) | keyed cooldown window + capacity trim, accept/reject returned so callers can record WHY | trivial re-implementation | **ADOPT_TOOLING (pattern only)** for any alert/notification surface |
| 5 | `feed_hub.py` one-publisher/many-subscriber WS hub | server-side subscription filters, replay+seq dedupe, bounded outboxes, slow-subscriber disconnect | asyncio + wire format; re-substitute own payload schema | **ADOPT_TOOLING (pattern only)** as design reference for live-monitor WS |
| 6 | `recent_activity.py` record-not-recompute explainability | "why did nothing happen" surface backed by outcomes recorded at event time (`sent/blocked/repeat/waiting/suppressed/quiet`) | framework-free design rule | **ADOPT_TOOLING (pattern only)** for "why is this strategy FLAT/BLOCKED" panels |
| 7 | Condition DSL invariants (`conditions.py`) | edge-vs-level separation (conditions physically cannot mutate trigger latches), fail-closed `availability` policy, `warming_up` vs missing distinction | adopting the DSL itself means adopting `SymbolState` substrate (high) | **ADOPT_TOOLING (invariants only; re-implement evaluator)** |

### Why alerts get blocked (owner's explicit question — the full chain)

The scanner can always answer "why no alert" because every rejection is an
enrolled outcome, visible per setup per symbol via `/api/v2/check/{symbol}`
(`recent_activity.py:159-227`). The 15 blocking mechanisms, in causal order:

1. Late/replayed bar admission drop (`live_scanner.py:344-369`); 2. session-phase
routing — premarket bars never touch VWAP/HOD/RVOL state (`state.py:261-280`);
3. SPY (regime-only) and unknown symbols never alert (`live_scanner.py:401-413`);
4. trigger EDGE latches advance in ALL sessions so a premarket cross does not
re-fire at the open (`custom_setups.py:522-527`, measured 200→52 spurious
alerts); 5. setup session filter (`:550-551`); 6. direction filter (`:559-560`);
7. per-trigger `repeat_sec` don't-repeat → outcome `repeat` (`:562-569`); 8.
`and|atleast` window not yet satisfied → `waiting` (`:573-590`); 9. per-setup
`repeat_sec` → `repeat` (`:592-599`); 10. one alert per setup/symbol/bar
(`:604-606`); 11. universe/parameter profile gate — the choke point, fail-closed
on missing values, per-condition "what it has vs what it needs" reasons →
`blocked` (`live_scanner.py:211-273`, `conditions.py:33-44`); 12. gate library
`GateResult(None)=no_data` semantics, e.g. `gate_rvol` blocks, `gate_rrs_d1`
passes during warmup only (`gates.py:50-84`); 13. sink cooldown dedupe (key
`(symbol, direction, trigger)`, default 5 min) → `repeat` (`alert_sink.py:16,46-53`);
14. sink capacity trim to max-score at 5000 (`alert_sink.py:17,58-89`); 15. WS
slow-subscriber disconnect + seq-dedupe replay (`feed_hub.py:42-56`).

`suppressed` exists in the taxonomy but has no emitter in the public build
(private-plugin only). This chain — record every rejection as a first-class
outcome instead of silently dropping — is upstream's most valuable design idea
for this workspace (#6 above).

## 2. What does NOT fit (REJECT / NOT_A_FIT)

| Part | Why rejected |
|---|---|
| **All 46 triggers + 18 setups + 16 presets** (as strategy ideas) | Lane S: 0/46 survive. Cluster-level detail in §4; each collides with dead families or lacks a payer that exists on FX/CX venues. A composition of dead skeletons is not a new identity (skeleton test). |
| Trigger engine code (`trigger_catalog.py`, `triggers.py`, `custom_setups.py` state substrate) | Welded to `SymbolState`/`SymbolSeries` (US-equity session semantics: RTH/premarket, RVOL time-of-day profiles, SPY regime). Wrong asset class entirely. |
| `stops.py`, `size_hint`, alert `score` heuristic | Sizing/PnL-adjacent semantics and an un-derived ranking number (`custom_setups.py:672-677`) — importing any of these would put un-evidenced numbers on workspace surfaces, violating the dashboard artifact law. Must never enter. |
| `gates.py` threshold constants | Explicitly "code defaults, editable in the dashboard" (`gates.py:30-37`) — not evidence. The `GateResult(None)=no_data` convention is the only transferable part. |
| Data providers (Alpaca SIP/IEX, Schwab/schwabdev, yfinance, Nasdaq RSS) | Wrong asset class; SIP is a paid plan and IEX measurably breaks volume triggers; Schwab needs weekly interactive re-auth; yfinance is an unofficial scraping API with Chrome-UA spoofing (`news.py:46-47`, ToS-gray). Workspace already has its own gateway. |
| `dashboard-v2` code | React+Vite app with WS transport; workspace governance dashboard law is "no CDN, no network" (`plans/PLAN_dashboard.md:74-77`) — wholesale adoption would violate it. Three patterns stolen instead (§1 #5/#6, capability-flag degradation). |
| Plugin system (`plugins.py`, `scanner/private/`) | Private-code dependency; arbitrary import surface. |
| News/fundamentals as inputs | No trigger/condition consumes news upstream (display-only); fundamentals are current-cached for 7 days (not PIT); FX/CX analogues either don't exist or are BLOCKED data classes. |

## 3. Risks

**License/data**
- MIT: copying substantial portions requires retaining the copyright + permission
  notice — satisfied by a vendored LICENSE/NOTICE copy + THIRD_PARTY_NOTICES
  entry. No source-file headers upstream.
- If anything chart-related were ever vendored: lightweight-charts Apache-2.0
  **attribution logo must stay enabled** (upstream NOTICE). Not triggered by the
  recommended adoption (middleware only).
- Market-data terms are runtime/user-account concerns (Alpaca plan, Schwab
  token, RSS) and are NOT inherited by vendoring python middleware. No
  obligation created by this survey.

**Security** (egress inventory verified complete by Lane T)
- One anonymous startup egress (GitHub release check; `UPDATE_CHECK=0` kills
  it; 6 s timeout, 256 KB cap). Alpaca/Schwab/yfinance/RSS egress only when
  configured+run — we never run it.
- Localhost-only bind with **no authentication by design**; guard middleware
  defends via Host-header allowlist (DNS-rebinding), same-machine Origin for
  unsafe methods/WS, JSON content-type for POST. Gaps: any local process can
  GET; missing Host header passes for non-browser clients (documented upstream).
- `SCANNER_ALLOWED_HOSTS` opens an **unauthenticated LAN-writable API** — must
  never be set on a shared network; any adoption inherits this rule.
- schwabdev stores OAuth tokens in `~/.schwabdev/tokens.db` (not used by us).
  Alpaca keys in gitignored `.env`.
- No eval/exec/pickle anywhere; subprocess only read-only port diagnostics after
  bind failure; `importlib` confined to the absent private plugin namespace.
- Dependency hygiene: floors AND caps on every runtime dep with named CVE
  reasons; weekly dependabot; CI Python 3.11 with least-priv permissions.
  Workspace `.venv` = 3.12.14 → compatible.

**Data-science (Lane S)**
- Upstream is live-only: no PIT revision discipline, fundamentals cached
  current-for-7-days, session rings reset daily, no historical decision
  replay. Treating its alerts as PnL evidence would be category error —
  forbidden by this survey and by workspace law.
- Volume/RS/RVOL observables — the only ones constructible on klines — belong
  to measured-dead families here (`XSECT-VOLSHK-S15`, `SFV4`, sprint volume;
  P-27 "adding an observable is not adding a mechanism").

## 4. Science screening (Lane S) — 46 triggers → 0 survivors

Dead-class index built from all 136 `research/wayfinder/FAMILY_FAILURES.jsonl`
rows (22 classes indexed). Screening table condensed to clusters:

| Cluster (n triggers) | Portable payer? | Family collision (family_id) | Verdict |
|---|---|---|---|
| Session-extreme breakout/chase (11) | No (no session extremes on 24/7) | FXFV1/FXFV2 session families; CX breakout classes; Q-3 re-clock | REJECT |
| Level rejection / fade (5) | No (absorption payer measured dead) | R-ANCHOR/RANGEFADE + ALL gated variants (permanently closed); SRLVCX1 (K-CTRL inverted out-earns) | REJECT |
| VWAP family (6+3) | Payer REAL on equities, NOT portable (no consolidated benchmark flow on FX; no session on CX) | mean-reversion-to-anchor dead; re-clock; fictional-counterparty veto | REJECT |
| EMA/micro-trend (4+2) | No (momentum continuation) | XSECT-TSTREND, H1TSMOM/DONCH ancestry, PSV1, EOS1-E1 | REJECT |
| Candle patterns (9) | No payer (self-referential shape) | H-VOLCOMP-BRKOUT (inside bar verbatim), sprint 98/98 negative | REJECT |
| Momentum impulse (3) | No | A6-V16-F2-RUNPERSIST; Q-4 delay-1; cost floor (M3-QSTATE 4.8 vs 2.0 pips) | REJECT |
| Gap at open (1+1) | Observable does not exist on FX/CX | V17-A4-P1-WKNDLIQ (weekend-gap analogue dead) | REJECT (venue-structural) |
| Volume/attention RVOL (2+2) | kline volume exists but no distinct payer; P-27 variant | XSECT-VOLSHK-S15, SFV4 | REJECT |
| Relative strength vs SPY / market-align (1+4) | Lead-lag dead | FXFV7-A6-P2 (own-lag out-earns), EOS1-E2, CNG1-A4-P1 | REJECT |
| N-day/52w levels (2) | No (Donchian dead; multi-day FX BLOCKED NG6/NG7) | PSV1, ES1-BAND-TREND, TRACKB1 | REJECT |
| Opening-range breakout (2) | No opening auction on FX/CX | FXFV1-A3-P1 (London-open analogue dead) | REJECT (venue-structural) |
| V-off-VWAP dwell-filtered reclaim (1) | Strip VWAP → exactly the F-0-killed sweep-reclaim skeleton | SRLVCX1-M1 + TRACKA2-C2-RECLAIM-ABSORB; P-27 | REJECT |
| Fundamentals-conditioned float/short%/cap (3) | No FX analogue; CX = funding rho-1.0 identity; liquidation tape BLOCKED | TRACKB1-CLASSA, V17-FUNDJUMP, BTC-BEAR fictional-counterparty veto | REJECT |

Honest expectation check: with measured base rates (ERP1-TRACKA-COHORT-2 7/7
pre-PnL deaths; SRLV 3/4 skeptic vetoes; EURUSD 1/48 then holdout fail; ≥76/100
PWS identities designed to die pre-PnL), zero survivors from a generic retail
scanner is the modal outcome, not a surprise. Confirmatory finding: upstream's
best refinements (dwell-filtered VWAP reclaim, clear-air void gate, time-of-day
RVOL) are all observable-refinements of skeletons this workspace already killed
— P-27 demonstrated from the outside.

**Consequence for PWS**: nothing from this survey enters
`IDENTITY_REGISTRY.jsonl`; the ≤100 ceiling and the running
PWS-CX-SOLUSDT-C1 cycle are untouched. Any future re-screening of a
US-equity-derived idea would still start at F-0 court with a registry slot at
the right gate.

## 5. Minimal integration diagram (recommended adoption only)

```text
┌────────────────────────────────────────────────────────────────────┐
│ upstream simonro/edge-scanner @ c927dcb0 (MIT)  — READ-ONLY SOURCE │
│  scanner/local_guard.py  +  tests/test_local_guard.py  +  LICENSE/ │
│  NOTICE                                                              │
└───────────────┬────────────────────────────────────────────────────┘
                │  vendor once, pinned SHA (cycle EDGE-SCANNER-TOOLING-V1)
                ▼
┌────────────────────────────────────────────────────────────────────┐
│ my-quantitative  research/platform_tools/thirdparty/edge-scanner/  │
│  local_guard.py  (byte-faithful)  THIRD_PARTY_NOTICES + PIN.md     │
│  tests/test_local_guard_fidelity.py  tests/test_no_egress.py       │
└───────────────┬────────────────────────────────────────────────────┘
                │  opt-in wiring ONLY after separate owner GO per consumer
                ▼
┌────────────────────────────────────────────────────────────────────┐
│ local sidecar surfaces (LIVE-DATA-GATEWAY-V1 class; dashboard      │
│ sidecars) wrap their FastAPI apps with the middleware              │
└────────────────────────────────────────────────────────────────────┘

NEVER CROSSES THIS LINE (rejected): trigger catalog, setups, stops/size/
score, gates thresholds, Alpaca/Schwab/yfinance providers, dashboard-v2
code, plugin system, any strategy semantics, any PnL claim.
```

## 6. Required tests if the tooling adoption is approved

1. **Port-fidelity matrix**: port upstream `tests/test_local_guard.py` cases
   verbatim (Host allowlist incl. DNS-rebinding hostnames, Origin rules for
   unsafe methods + WS upgrade, JSON content-type enforcement, loopback +
   `[::1]`, `SCANNER_ALLOWED_HOSTS` semantics) — vendored code must behave
   identically on every recorded case.
2. **No-egress deny-list test**: socket-connection hook asserting zero
   outbound connects across import + request handling of every vendored
   module (the middleware has no network path; the test makes it a permanent
   property).
3. **Python 3.12 compat run** of the ported tests on workspace `.venv`.
4. **WS coverage**: middleware must wrap WebSocket upgrades (upstream
   property; regression-test it).
5. If pattern-level items are later implemented natively (sink dedupe,
   explainability outcomes): state-machine tests for cooldown windows /
   outcome taxonomy, per workspace fixture law.

## 7. Decision table (survey recommendation — all stop at owner GO)

| Part | Decision |
|---|---|
| `local_guard.py` + tests (vendored, pinned, MIT-noticed) | **ADOPT_TOOLING** — draft plan `plans/DRAFT_EDGE-SCANNER-TOOLING-V1.md` attached |
| `quote_bars.py` | **ADOPT_TOOLING (DEFERRED)** — precondition: a future US-equity data-plane cycle |
| Cache discipline / sink dedupe / feed_hub / explainability / DSL invariants | **ADOPT_TOOLING (pattern only)** — documented here as design rules; no vendoring |
| All 46 trigger ideas + 18 setups + 16 presets | **REJECT** (0/46 survive; §4) |
| Trigger engine code, stops/size/score, gates constants, providers, dashboard-v2 code, plugin system, news/fundamentals inputs | **REJECT** (never enter workspace surfaces) |

No RESEARCH_IDEA_ONLY items exist. Nothing here consumes or requests any PWS
GO phrase; the draft plan has its own gate vocabulary and stops before
registration until the owner approves.
