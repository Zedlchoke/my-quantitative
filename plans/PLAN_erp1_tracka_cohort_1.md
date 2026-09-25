# PLAN (DRAFT) — ERP1-TRACKA-COHORT-1 — FX range-edge liquidity absorption: RANGEFADE replication + same-family mechanism cohort

> **Status: `DRAFT_FOR_OWNER_GO — NOT REGISTERED, NOT EXECUTED.** This file
> registers nothing, starts no worker, downloads no data, opens no S1,
> places no order, consumes no GO, and touches no running shadow worker
> (FX-RANGEFADE-2M-SHADOW-V1 daemon stays untouched). Parent law:
> `plans/PLAN_economic_robustness_program_v1.md` (ECONOMIC-ROBUSTNESS-
> PROGRAM-V1, ACTIVE_LIGHT in registry) §5.4 Track A, §§5.1–5.15, §6–9.
> Registration only via `researchctl cycle register` after owner GO on this
> plan (proposed command in the owner decision packet).
>
> Authored 2026-09-25 by A1 from explicit owner instruction (verbatim
> intent: open child cycle ERP1-TRACKA-COHORT-1 to find and replicate FX
> strategies sharing RANGEFADE-2M's economic mechanism — absorbing
> short-term trading-pressure then harvesting price recovery — targeting
> explainable, reproducible edge, NOT nice-PnL parameter sets).

## 0. Cycle identity

```text
cycle_id     ERP1-TRACKA-COHORT-1
class        MECHANISM COHORT (outcome-blind council -> pre-PnL
             falsification -> frozen scored trials under a paper-tier
             cost book; verdict class bounded to paper tier, §6)
parent       ECONOMIC-ROBUSTNESS-PROGRAM-V1 (umbrella, Track A)
asset        forex (majors; universe frozen in §5)
budget       24 scored cells MAX; EFFECTIVE 18 after D2 veto (12 Task-1
             replication on 2 new pairs + 6 for the one surviving Task-2
             mechanism); observed/published denominators per umbrella §5.8
ledger       research/control/ERP1-TRACKA-COHORT-1/trial_ledger.jsonl
             (append-only, one row per scored cell + holdout look)
S1           SEALED_UNTOUCHED (no S1 surface in this cycle; S1 request law
             = umbrella §5.10)
orders       NONE — no broker surface, no live/paper order placement; any
             prospective continuation is a separate owner-GO shadow surface
shadow       DOES NOT touch FX-RANGEFADE-2M-SHADOW-V1 workers, journal,
             daemon, dashboard or worktree (read-only citation only)
GO-1 phrase  GO ERP1 TRACKA COHORT 1 REGISTER AND COUNCIL
             (typed fresh at registration gate; authorizes: registration,
             council already run under umbrella light authority is FROZEN
             as appendix A, data-gate probe downloads, PIT/cost audits,
             falsification battery, trial freeze — and STOPS)
GO-2 phrase  GO ERP1 TRACKA COHORT 1 SCORED
             (typed fresh at the scored gate only after A7 prelaunch
             PASS; authorizes the 24-cell cap only)
forbidden    parameter grids; indicator blending; sign-flip renames;
             lo_q/hi_q re-tunes presented as new mechanisms; reading
             ancestry/shadow PnL into proposer packets; S1; orders;
             shadow-worker touch; registry edits outside researchctl;
             merging/pushing; editing TERMINAL verdicts
```

## 1. Objective and non-objectives

### 1.1 Two tasks, never conflated

- **Task 1 — Replication of the frozen RANGEFADE law on outcome-free
  surfaces.** The byte-exact ancestor law plus a preregistered PIT-clean
  re-specification (§4.2), run on **new pairs** (outcome-free: never
  searched in any program cycle) and, if the owner unblocks an independent
  historical source, on an independent-source panel (§5.3). Replication
  answers: does the *law* reproduce outside the surfaces it was found on?
- **Task 2 — New FX mechanisms in the same economic family** (range-edge /
  pressure-absorption liquidity provision), each with its own payer,
  transferred risk, observable and falsifier. A renamed copy, a lo_q/hi_q
  re-tune, a session-window shift of RANGEFADE, or an inverted old family
  is **not** a new mechanism (§7.4 novelty law).

### 1.2 Non-objectives

- No promotion beyond `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` (paper
  tier — broker cost authority is BLOCKED program-wide, §6.2).
- No rescue of the EURUSD/GBPUSD/USDJPP scored histories: those windows are
  outcome-exposed ancestry (§3) and are never re-scored as fresh evidence.
- No live-readiness claim of any kind (umbrella §1.3).
- `REJECT_ALL` is an expected, valid terminal verdict.

## 2. Authority, Phase-0 and boundaries

- Authority order: owner instruction > this child plan (once registered) >
  umbrella plan > CLAUDE.md + handbook v2. This child may be stricter than
  the umbrella, never weaker.
- Phase-0 gate re-measured at this child's own intake before any dispatch
  (umbrella §3). Snapshot at drafting (2026-09-25, root checkout): registry
  reconciled; root `main` @ `69ddc604…`; heavy lock `FREE_PROVEN`; FX
  shadow daemon PID 79157 + dashboard alive and UNTOUCHED; orchestrator v3
  events idle (last 2026-09-19); pre-existing doctor HIGH findings are the
  accepted-historical TERMINAL-cycle class (umbrella P0-3).
- One live Lead session; machine-wide heavy lock for the bounded M1 probe
  downloads only (yielding pattern if long); light council work under the
  umbrella's light authority.
- Worktrees: implementation lanes only in this cycle's own worktree
  (`.worktrees/erp1-tracka-cohort-1/...` created at registration by A1);
  council/audit artifacts land in the control namespace read-only-writes
  (report files only, no engine edits).

## 3. Ancestry disclosure (binding, outcome-exposed)

All council lanes and every future artifact of this cycle MUST carry this
disclosure block. **The RANGEFADE ancestry is OUTCOME-EXPOSED**: its dev
campaigns, holdout results and the running shadow journal have been seen by
humans and agents. Therefore:

1. Proposer packets contain **no** PnL, PF, win-rate, trade-count outcome,
   shadow journal content, or any ranked/selected/winner information from
   any scored or shadow surface (handbook §12.5, umbrella §5.1).
2. Ancestry chain (labels pinned, identities disclosed, numbers NOT cited
   in proposer packets):
   - `EURUSD-OPEN-SEARCH-V1` — TERMINAL, 48-trial EURUSD campaign, the one
     gate-eligible family failed its single frozen holdout look.
   - `EURUSD-OPEN-SEARCH-V2` — TERMINAL, second EURUSD census; FX2-RANGEEXP
     config C3 `{lo_q 0.3, hi_q 0.7, fade}` selected and consumed its
     one-look holdout; SHORT_ALWAYS short-beta control recorded.
   - `EURUSD-RANGEEXP-SCORED-V1` — TERMINAL, scored confirmation cycle of
     the C3 law (engine/audit lineage; commit `83264434`).
   - `FX-MAJORS-SEARCH-V1` — TERMINAL, GBPUSD + USDJPY transfer; both
     pairs' dev + holdout windows consumed (one-look law).
   - `FX-RANGEFADE-2M-SHADOW-V1` — ACTIVE_LIGHT prospective shadow,
     EURUSD+GBPUSD, 1.5 lots/pair; journal books gross price movement only
     (fee/slippage fields arrive via amendment A1-controls, whose GO is
     recorded and whose activation is in progress per the registry write
     token 2026-09-25T05:35Z — A7 F5; re-measure the amendment's live
     state at this child's intake and never cite pre-amendment journal
     fields as cost evidence).
3. Consequence: **EURUSD, GBPUSD, USDJPY full scored windows (2021-01 ..
   2026-06 holdout inclusive) are outcome-exposed surfaces.** No cell in
   this cycle scores them as evidence. They may appear ONLY as (a) disclosed
   ancestry in reports, (b) engine-parity fixtures, (c) reference panels for
   spread-curve construction (cost authority, not outcome authority).
4. Ancestry gate: every Task-2 proposal runs pooled |rho| ≤ 0.20 vs
   `research/wayfinder/FAMILY_FAILURES.jsonl` dead families + class vetoes
   (re-clock, calendar geometry, displaced-fade, nominal-level, vol-level,
   premium-fade ancestry) — umbrella §6, immovable.
5. The 12-family V1/V2 census exposure: all 12 FX families (GAP, PDHLOC,
   DOW, ASIAFADE, SESSMA, H1TSMOM, H1DONCH, DAYMOM, RANGEEXP, STOCH,
   ROUNDNUM, HOURREV) have dev-window outcome exposure on EURUSD (and
   GBPUSD/USDJPY for FX-MAJORS). Any Task-2 mechanism built from a census
   family must disclose that exposure and pass the ancestry veto; selection
   on remembered dev PnL is prohibited and structurally impossible in
   blind packets.

## 4. The frozen law to replicate (Task 1)

### 4.1 Byte-exact ancestor law (RANGEFADE-2M identity)

- Signal: `v2_lib.f_rangeexp(p, 0.3, 0.7, use_breakout=False)` over H1
  bars, exactly as scored in FX-MAJORS-SEARCH-V1 and running in the shadow
  (code authority:
  `.../EURUSD-RANGEEXP-SCORED-V1/scripts/v2_lib.py:265`, imported by the
  shadow daemon; engine SHA pinned at freeze). Mechanics (non-authoritative
  prose): per traded day, rank yesterday's high−low range in a trailing
  ≤60-day window; in the not-extremely-wide regime, fade breaks of the
  previous day's high/low during 07:00–18:00 UTC (break above prev-high →
  short; below prev-low → long), exit when price returns to the middle
  quarter of the prev-day range; flat at day boundary.
- Execution law: signal on CLOSED H1 bar → fill at NEXT H1 open at the
  OPPOSITE quote (buy@ask, sell@bid); no fills on/after the 19:00 H1 bar;
  force-flat before 20:00 UTC daily; weekend flat; no overnight, no swap
  (structural-zero financing — enforced by executor FIXTURE, not comment:
  datacost condition 2).

### 4.2 Preregistered PIT-clean re-specification (the replication anchor)

**Council code verdict (skeptic lane, static read at the dispatch SHA —
binding for this freeze): SUSPECT CONFIRMED, with two refinements.**
(a) The leak is real: `_prev_day_stats` (`v2_lib.py:66-79`) accumulates
day-d full-day highs/lows; `pct[d]` (`:274-281`) ranks day d's OWN
full-day range and is consumed at day-d's first bar (`:291-301`) — the
fade/follow mode is decided up to ~20 hours before the information exists;
100% of day-d fills inherit it. (b) A second, quieter leak: the
`pct[d] > 0` guard (`:293`) flat-days exactly the days whose full-day range
ties/undercuts the trailing 60-day minimum — a hindsight range filter.
(c) The deployed mapping in the frozen config (0.3, 0.7, False) is, by
code authority (`:293-297, 305-320`): **pct==0 → flat; 0 < pct ≤ 0.7 →
FADE; pct > 0.7 → FOLLOW/breakout** (line `:296` is dead code — recorded
in the semantic diff table, no behavior impact). Any prose elsewhere that
inverts this mapping is void; the code is authority. (d) The running
shadow daemon replays the same function on a growing panel
(`shadow_daemon.py:225-228, 277-288`), so its day-d mode is a RUNNING
partial-range percentile — a THIRD law, PIT-legal in itself but not
numerically identical to either backtest law; the daemon's parity
self-test (`:515-525`) compares the same function on the same panel and is
structurally blind to this divergence (and `:284` hard-codes a cosmetic
PASS). Consequently: **no artifact of this cycle may cite "shadow parity
PASS" as evidence about R-ORIG semantics**, and scored-ancestor outcomes
are not evidence about the live law or vice versa.

- **R-ANCHOR (primary, frozen now):** the ancestor law with exactly ONE
  delta — the mode percentile input index shifts `pct[d] → pct[d−1]`
  (yesterday's range percentile, fully known at day start), and the
  `pct > 0` guard shifts with the index (flat days FOLLOW minimum-range
  days, no lookahead). Everything else byte-identical to §4.1/§4.2 code
  authority, mapping included. This is the honest replication target; it
  has never produced any ancestry result. **Skeptic precision notes
  (D2-confirmed, verbatim):** (i) `pct==0` arises under searchsorted-left
  when the own range is ≤ the trailing-window minimum *ties included* —
  the flat-day exclusion migrates to the day AFTER a minimum-range day,
  and days lacking `pct[d−1]` → flat; (ii) the guard evaluates
  `pct[d−1] > 0`, and M-1's shift-equivalence proof stays a freeze
  fixture.
- **R-ORIG (diagnostic neighbour, frozen now):** the byte-exact ancestor
  law. Its role is the leak probe: the preregistered comparison R-ANCHOR
  vs R-ORIG on identical folds is falsifier F-PIT-1's outcome surface.
  R-ORIG can never be selected as the surviving anchor of this cycle; if
  R-ORIG out-performs R-ANCHOR beyond the preregistered seam law (§9.4),
  the mechanism is falsified on that pair (edge was the seam, not the
  economics).
- One quantile-support neighbour (R-NEIGH): `lo_q 0.25 / hi_q 0.75` on the
  R-ANCHOR semantics — support check only, can never support or flip any
  verdict (its success is not evidence), never a grid.
- R-DAEMON (emulated, no scored cell): the running-partial-range law,
  emulated on the full panel for seam measurement only (F-PIT-1 / M-3).

## 5. Data authority and sources (measured; independent-source posture explicit)

### 5.1 Primary corpora (existing, sha-pinned)

| Source | Pairs | Window | State |
|---|---|---|---|
| Dukascopy M1 BID/ASK day files (`datafeed.dukascopy.com`, bi5) | EURUSD | 2021-01..2026-06 (+bridge to 2026-09-23 in shadow worktree) | sha-pinned, censused: spread p50 ≈ 0.3 pips, session/rollover curve BUILD_PASS |
| same | GBPUSD, USDJPY | 2021-01..2026-06 (4,014 files/pair, 0 missing) | spread p50 0.8 / 0.5 pips; USDJPY 1e-3 scale probe-proven |

License posture (binding, disclosed): `OWNER_DIRECTIVE_SOURCE_AUTHORIZATION`
with `TCU_RISK_DISCLOSED` — the standing program posture inherited from the
ancestry cycles. The formal tension is on record:
`EURUSD-DATA-QUALIFICATION-V1` (BLOCKED) holds `BLOCKED_SOURCE_LICENSE`
with the verbatim TCU quotes; Track A children inherit the umbrella §5.4
ruling (paper-tier use under owner directive, risk disclosed) and do NOT
re-litigate it inside this cycle. The three owner unblock paths (TrueFX
registration / Dukascopy written consent / OANDA v20 practice) remain open
owner actions and would upgrade this table.

### 5.2 New-pair corpora (Task-1 outcome-free surfaces; ≤2 pairs)

- Council proposes the pair slate (appendix A); frozen at GO-1. **LOCKED
  by owner D-B (2026-09-25): AUDUSD + USDCAD — the two new pairs are the
  ONLY replication surface this cycle** (spare USDCHF needs an owner
  amendment; EURUSD/GBPUSD/USDJPY are outcome-exposed ancestry, never
  re-scored). Criteria:
  top liquidity, full Dukascopy M1 bid/ask coverage 2021-01..2026-06,
  distinct economic bloc vs EURUSD/GBPUSD (diversifies the USD-beta
  confound), pip-scale probed per pair (never assumed — USDJPY precedent).
- Data gate per pair BEFORE any outcome (critic-hardened checklist):
  pre-gate registry check that the pair was never searched in any program
  cycle; bi5 probe vs tick ground truth (~7–14 days straddling a DST
  transition + a rollover; 24-byte M1 layout invariant asserted);
  **pip-scale + level-band probe derived from probe ticks — BLOCKING PORT
  DEFECT: `build_bars.py` hard-codes `PIP=1e-4`, `PRICE_SCALE=1e5` and the
  EURUSD band `0.80 < bid < 1.35`, `engine.py` hard-codes `PIP=1e4`;
  copying verbatim fail-closes every non-EURUSD pair — the cohort engine
  MUST parametrize scale/pip/band per pair with per-pair fixtures**; census
  BUILD_PASS (tradable-minute share > 0.90; non-positive-spread minutes
  < 1% gate, ≈ 0 expectation; valid 15m bars > 100k; duplicates = 0
  fail-closed; `days_short_records` enumerated); gap census (micro-gaps
  enumerated; weekend/DST boundaries measured); session spread curve build
  (§6.3 hardened schema); DST/rollover calendar fixtures (rollover bucket
  count > 0 asserted; Sunday-open cell present); engine parity + per-pair
  scale fixtures; gate verdict + sha chain recorded. Raw bytes
  machine-local, sha manifests committed.
- Bounded download sizing (critic estimate): ~4,014 M1 day files/pair ≈
  ~44 MB compressed/pair + tick probe ~10–30 MB/pair ⇒ two pairs ≈
  110–150 MB total, ≈ 35–70 min/pair at the existing keep-alive pacing —
  a bounded heavy job under the machine-wide lock (yield if over window).

### 5.3 Independent-source replication (Task-1b; BLOCKED-bounded)

**Owner decision D-C (2026-09-25, LOCKED): no independent-source unblock
this cycle.** Task-1b remains reconciliation-only; every result of this
cohort carries `SINGLE_SOURCE_PANEL` and is bounded to paper tier — these
are properties of the evidence, not placeholders awaiting an upgrade.

- Status today: **no authorized independent historical bid/ask source
  exists** (EDQ1 verdict above; Twelve Data = internal-research-clear but
  NO bid/ask, reconciliation-only; TrueFX historical needs owner login;
  OANDA practice needs owner registration).
- Therefore Task-1b is `BLOCKED_SOURCE_LICENSE`-bounded at freeze: what MAY
  run without new owner action is a **mid-price reconciliation panel**
  (Twelve Data or second-vendor closes): H1 close cross-vendor tolerance
  check (pre-registered tolerance, no forcing two vendors to agree) whose
  only verdict is level-consistency of the primary panel — it is NOT a
  cost authority and NOT an execution panel.
- ~~If the owner completes an unblock path before GO-2, Task-1b upgrades to
  a full independent-source replication arm under a plan amendment (new
  GO).~~ **SUPERSEDED by owner D-C LOCK (2026-09-25): no unblock this
  cycle.** The upgrade sentence is retained only as the law a FUTURE
  owner-GO amendment would follow; it grants nothing now. Conclusion tiers
  are labelled accordingly in every artifact.

## 6. Cost authority (paper-tier book; five binding conditions verbatim)

1. **Verdict class bounded:** every output of this cycle can only ever be
   `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` (paper tier). No paper PASS
   promotes toward real-money inference without Lane F
   `PASS_BROKER_COST_AUTHORITY` (FOREX-NG8 stays closed).
2. **Structural-zero financing enforced, not assumed:** flat-by-20:00 UTC
   and weekend-flat are executor FIXTURES (unit-tested), not comments.
3. **Per-session spread, not global p50:** the executor charges the measured
   session/rollover spread curve at event time (sha-pinned census per
   pair); the frozen ×2.0 stress applies to per-regime medians.
4. **Adverse selection declared unmeasurable:** fill quality (queue
   position, pick-off) is not observable in M1 bid/ask corpora — declared
   class in every verdict, stress-covered, never assumed into a measured
   number. **In particular: taker fills at the opposite quote are NEVER
   described as "earning the market maker's spread"; the strategy PAYS the
   spread. Any maker-capture claim requires queue-position evidence this
   cycle cannot produce.**
5. **Marks-vs-fills seam disclosed:** any live-mark comparison discloses
   the TrueFX-indicative vs Dukascopy-bar seam.
- Primary book = measured components only (per-session spread curves,
  venue-free fee buffer as DECLARED component listed verbatim with stress
   coverage — commission remains unmeasured program-wide). Stress = ×2.0
  per-regime medians (frozen pre-outcome) with ×1.5 and ×2.0 both reported
  (umbrella §5.14).
- **Charging semantics (critic-hardened, binding spec):** the executor
  charges the FILL BAR'S OWN measured spread × k ∈ {1.0, 1.5, 2.0}
  (`s_open` at entry/reversal bar open, `s_close` at exit bar close;
  day-close force-flat exits use the day-close bar's close spread; one
  spread crossing per side, round trip = entry + exit crossing). The
  per-session census curve is the PERSISTED AUTHORITY for stress floors,
  the F-5 ceiling, the §9.4 seam-band constant and the F-4 decomposition
  tables — never a substitute for the bar. Census schema hardening
  (mandatory for new pairs): per-bucket counts persisted (no silent
  low-sample drops — a dropped bucket becomes explicit `null` +
  `LOW_SAMPLE_BUCKET` flag); close-spread quantiles persisted alongside
  open-spread; a census-vs-executor reconcile test (per-bar spread medians
  bucketed per session == census p50 within rounding).
- **Force-flat semantic pinned to ONE law:** this cycle's H1 law (no fills
  on/after the 19:00 bar, flat before 20:00 UTC) — the older 15m fixture's
  21:00-rollover constant is NOT inherited. Enforcement = build-failing
  fixtures: no-position-after-flat assertion at every hour ≥ 20 UTC and
  across Friday→Sunday boundaries (incl. synthetic DST calendars);
  financing code path absent-or-raises (structural zero, not a numeric
  zero); a 20:05-UTC mutation bar produces no fill and no carried
  position; avoided rollover spread documented as a property of the law,
  never claimed as saved cost.
- Taker-fill cost model: entry/exit at opposite quote + the fill bar's
  measured spread × k; slippage beyond spread = declared-unmeasured,
  covered by stress. No assumed-fee substitution may appear in any
  headline number (owner instruction 2026-09-25, binding). **Wording bans
  (every artifact):** never "earning/capturing the market maker's spread"
  for taker fills (the strategy PAYS the spread); no maker-capture/rebate/
  queue-rent claims (queue-position evidence does not exist here); never
  "fill at mid" / "zero slippage"; never "no transaction costs" (the
  honest statement is "no financing by structural fixture + no measured
  commission + measured spread × k"); non-positive-spread minutes are a
  data red flag, never an opportunity; no live-readiness wording of any
  kind. Mandatory class label in every verdict:
  `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK; cost = taker at opposite quote
  + measured per-bar spread × k; adverse selection stress-covered, never
  measured` — plus `SINGLE_SOURCE_PANEL` on every verdict label (all
  historical evidence is Dukascopy-derived bars; the TrueFX-indicative
  marks seam stays disclosed, never resolved by the reconciliation panel).
- **Incident cross-reference (binding):** the ancestor-law PIT seam, the
  hindsight flat-day filter and the three-laws finding are recorded as
  `tracka_cohort1/INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25.md`; its citation
  law (ancestor numbers = R-ORIG-semantics facts; never evidence for the
  daemon law or for R-ANCHOR; "parity PASS" never citable as semantics
  evidence) governs every artifact of this program.
- **Unfundable-arm veto (critic):** any Task-2 mechanism whose
  entry/exit geometry needs sub-M1 event timing, queue/depth conditions,
  maker fills or tick-level fill sequencing is NOT honestly costable on M1
  bid/ask and is vetoed at proposal review (pre-PnL falsifier class).

## 7. Mechanism council (outcome-blind) and cohort freeze

### 7.1 Composition and blindness

Explorer (evidence), skeptic (falsification), data/cost critic
(measurability) — dispatched with packets that contain the §3 disclosure,
the §4 law text, the §5 source table and NOTHING from the outcome-exposed
surfaces (no PnL/PF/win-rate/trade outcomes, no journal bytes, no MAP
outcome rows, no dashboard). **Composition completed per owner decision
D-E (2026-09-25, resolves A7 F1/C1): two additional BLIND PROPOSER lanes
(P1, P2) ran under the same blindness law, independent of each other and
of the other lanes. Their mechanism outputs are recorded as FUTURE-COHORT
CANDIDATES ONLY — by the same owner instruction this cohort opens NO
additional mechanism slots and M2 stays dead (§7.2); their design-review
findings ARE integrated into this plan (§8 F-3 mode-sham, §9.1 holdout
companions, M3 control decomposition).** Council artifacts:
`research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/`
(handoff JSONs `zcode_orch_v3_handoff@1` at the dispatch paths). This
session's council ran under umbrella light authority; its slate is frozen
as appendix A and re-verified (hashes) at GO-1.

### 7.2 Cohort law (umbrella §5.2/§5.7, restated as this cycle's freeze)

- **At most 3 mechanisms**: M1 = RANGEFADE range-edge absorption (Task 1,
  mandatory slot), M2/M3 = at most two NEW same-family mechanisms (Task 2).
  Fewer allowed; a fourth requires a new cohort.
- Per mechanism the frozen trial names exactly: **one anchor**, **at most
  two neighbours**, **one causal control**, **one inverted control**,
  **one simple baseline set** (Task-1 baseline set = FLAT + day-session
  SHORT_ALWAYS + day-session LONG_ALWAYS; the SHORT/LONG arms ARE the
  short-USD-beta controls — their comparison to the anchor is reported in
  every artifact; for JPY-quoted and bloc-diverse pairs the council names
  the correct beta direction per pair).
- No grids, no blending, no sign-flip renames. Every arm gets
  `arm_config_digest`; exact-arm dry-run non-vacuous + leak-scanned before
  any scored cell.

### 7.3 Proposal format (umbrella §5.3 — all 10 fields) and the six economic questions

Every Task-2 proposal answers the 10 mandatory fields (payer, premium,
persistence, risk transferred, observable + availability evidence, holding
horizon, capacity, costs base+stress, falsifier, controls/baseline). The
handoff summary frame per mechanism is the **six economic questions**:

1. Ai trả premium — ai bị ép/nóng lòng/ghét rủi ro trả, và vì sao họ không
   thể hoặc không sẽ arbitrage nó đi? (payer + non-arbitrage reason)
2. Premium kỳ vọng bao nhiêu bps mỗi quyết định/chu kỳ, và rủi ro nào
   strategy gánh để đổi lấy nó — tên đuôi cụ thể? (premium + risk + tail)
3. Vì sao premium còn tồn tại (cấu trúc/quy định/hành vi/bảng cân đối) và
   điều gì sẽ xói mòn nó? (persistence + erosion)
4. Observable PIT nào mã hóa cơ chế — event/effective/available tách biệt,
   đo được trên nguồn nào ĐÃ cấp quyền? (observable + data authority)
5. Kết quả quan sát được nào sẽ BÁC BỎ cơ chế, và control nào phải KHÔNG
   tái tạo được edge? (falsifier + control prediction)
6. Chi phí toàn chuyến ở base và stress ×2.0 theo phiên còn để dư bao nhiêu
   giả thuyết — cost-survivability ceiling? (cost ceiling + capacity)

### 7.4 Novelty law (restated, binding)

A Task-2 mechanism is NEW only if mechanism + information source + causal
control are new. Veto classes: renamed/re-tuned/re-clocked/re-sessioned
RANGEFADE; inverted dead families; indicator blends; cross-horizon rescue
(Q-3); anything failing the ancestry rho gate.

## 8. Pre-PnL falsification battery (gate BEFORE any scored cell)

Each frozen mechanism passes, in order, on the NEW pairs only:

- **F-1 Ancestry:** rho gate + class vetoes (§3.4), with the skeptic's
  **representation law (A7 F2, binding): pooled |rho| ≤ 0.20 vs dead
  families is computed on the EXACT scored target-array representation
  with the frozen variant set, BY THE SKEPTIC LANE, not the proposer — a
  rho computed on a friendlier representation is void.**
- **F-2 PIT audit of the exact signal code** at day/H1 granularity =
  **F-PIT-1**, executed as the skeptic lane's M-1..M-5 (all signal-level,
  on the NEW pairs' dev window, before any PnL anywhere in the cycle):
  - **M-1 shift-equivalence proof**: R-ANCHOR implemented as a pure
    usage-index shift must equal an independent from-scratch implementation
    (percentile of `ranges[d−1][0]` vs history strictly before d−1);
    unequal ⇒ `NOT_RUN_ARMS_REDERIVED`.
  - **M-2 non-vacuity of the one-day shift**: share of in-session dev bars
    where `tgt(R-ANCHOR) != tgt(R-ORIG)`; **< 2% ⇒ KILL_VACUOUS_MUTATION**
    (arm set re-derived ONCE, as a registered pre-PnL amendment inheriting
    the consumed look count).
  - **M-3 partial-range emulation**: R-DAEMON vs R-ORIG bar-level
    disagreement, day-level mode-flip rate, early-silenced days (logged;
    defines what the shadow can testify about — `DISCLOSED_SEAM`, not a
    kill).
  - **M-4 self-test blindness fixture**: synthetic panel where daemon-law
    and R-ORIG diverge while the shipped same-panel self-test construction
    still returns PASS — committed as a code fixture.
  - **M-5 panel-truncation PIT proof**: R-ORIG replayed on panels
    truncated at each day start MUST differ from full-panel output (leak
    proven end-to-end); R-ANCHOR replayed the same way MUST be identical
    (PIT-clean as executed, not just as specified).
  - F-PIT-1 completes and freezes (verdict + seam-band constants logged)
    BEFORE the first PnL-bearing cell of ANY arm.
- **F-3 Clock/session geometry — CLOCK-PLACEBO control (must MOVE, Q-11):**
  identical execution law and cost book; entries at the anchor's average
  entries-per-day and average entry hours, exits at average holding
  duration, direction alternating day-by-day. Non-vacuity predicates (all
  must hold or the control is REBUILT before scoring): occupancy 10–40% of
  in-session bars; both directions present; ≥90% of its round trips differ
  from the anchor's; non-constant signal series. Release-calendar/rollover
  geometry checks; per-hour PnL tables + pre/post-DST-transition splits
  mandatory; S6 no-drift-flag law for fades binding. **Mode-sham
  signal-level test (proposer P1 finding, integrated):** a day-level
  mode-label permutation (fade/follow labels shuffled at a frozen seed,
  marginal frequency preserved, everything else identical) must be
  non-vacuous (≥2% of day labels change) and is adjudicated through the
  §9.4 seam law — the mode-selection channel is exactly what the PIT
  repair changed, so it gets its own null; signal-level, no scored arm,
  no new slot.
- **F-4 Short/bloc-beta:** per pair, the USD sign of the anchor's average
  net exposure is DECLARED at freeze; `anchor_minus_beta_control` is
  reported against the beta-MATCHED baseline (the always-on book whose USD
  sign matches the anchor), with both books' tables in every artifact;
  per-fold beta tables mandatory (time-varying beta); same-window
  USD-basket correlation of the anchor's daily PnL = disclosed diagnostic
  only. Per-pair frozen directions: AUDUSD → SHORT_ALWAYS; USDCAD →
  LONG_ALWAYS (USD-base pair); spare USDCHF → full-window drift sign rule
  with mid-window inversion disclosed. **Disclosed limitation (proposer
  P2): the beta books match the anchor's USD SIGN, not its regime-day
  composition — the per-fold beta tables mandated above are the carrier
  of that residual and no composition-matching retrofit is allowed
  post-PnL.**
- **F-5 Cost-survivability ceiling (A7 F4 clarification, binding):** the
  ceiling is DECLARED-BAND ARITHMETIC — the proposal's preregistered
  premium band (from its §7.3 ten-field format, field 2) vs the
  ×2.0-stressed per-session
  book MEASURED from the census on the F-6 recent window (last 6 months),
  using the CONDITIONAL spread at break-style bars (the census's
  break-hour bucket — the family fills exactly when spreads widen; session
  p50 understates the fills taken). NO backtest, no measured gross return
  — the premium side stays the proposal's declared hypothesis until the
  scored phase. Negative ceiling = veto BEFORE scoring (VOL-NG1
  precedent).
- **F-6 Feasibility on the nearest window** (Q-6): per-fold (not just
  total) trade-population disclosure vs the §9.2 floors, on the last 6
  months, not archive average.
- **F-7 Concentration pre-check:** declared concentration statistic +
  exclusion-zone of every threshold at fold, trade AND session-hour level
  (Q-12).

Ordering law (owner instruction, binding): **data/PIT/cost audit and
falsification run to completion BEFORE any PnL-bearing computation
anywhere in the cycle.** Failing F-1..F-7 for a mechanism removes it
pre-PnL (recorded in the ledger as NOT_SCORED_FALSIFIED with the falsifier
ID); it does not open a tuning loop.

## 9. Fold/holdout contract, thresholds, kill laws

### 9.1 Folds and holdout

- Dev window 2021-01-01..2025-12-31; **holdout 2026-01-01..2026-06-30** —
  untouched by ANY program search on the NEW pairs (verified against the
  registry before freeze). Chronological non-overlapping folds F1..F6 as in
  the ancestry convention; force-flat at fold boundaries; no fold-window
  substitution after any PnL is seen.
- **One-look holdout law (A7 F3 pin, binding; P2-finding extension):** each
  pair's holdout is consumed by EXACTLY ONE preregistered evaluation PASS,
  whose membership is frozen before the pass: the promotable ANCHOR arms
  that passed ALL dev gates (R-ANCHOR per pair; the M3 anchor), plus —
  computed in the same single pass, as companions, never as independent
  consumers — their preregistered **causal control, inverted control and
  baseline books** (the §9.3 holdout control clause REQUIRES the inverted
  companion: "inverted strictly below anchor" must be evaluable on the
  holdout too, else a holdout-only inversion passes unchecked — proposer
  P2 finding, integrated). **Never-selectable arms (R-ORIG, R-NEIGH) and
  dev-killed mechanisms (including KILL_PIT_SEAM and control kills) take
  NO holdout look — a dead arm cannot be allowed to burn the pair's one
  irreversible outcome-free window.** Preregistered per-arm criteria;
  failure is final, no rescue. Holdout looks count in the observed
  denominator.

### 9.2 Dev-gate thresholds (frozen; per arm per pair)

- G1 net > 0 @ cost ×1.0; G2 PF ≥ 1.20; G3 ≥ 4/6 folds net > 0; G4 net >
  0 @ ×1.5; G5 adjudication floor ≥ 100 closed round trips AND ≥ 6 months
  (smoke floor 30 = eligibility only — umbrella §5.14); G6 top-fold share
  ≤ 50% of positive net; G7 top-5-trades share ≤ 50% of positive net;
  **G8 top single session-hour share of positive net ≤ 50%** (this family's
  profits can concentrate in 1–2 hours while fold/trade splits look clean —
  the clock-geometry residue F-3 hunts); exclusion zones logged at fold,
  trade AND hour level (Q-12).

### 9.3 PROMOTE / KILL / TIME-STOP (preregistered, umbrella §5.13)

- **PROMOTE (= paper-tier candidate, nothing more):** all G1–G8 PASS at
  dev AND holdout net > 0 @ ×1.0 and @ ×1.5, one look; the causal control
  must ALSO fail to reproduce on the holdout window (control computed on
  holdout too — a dev-only control pass would make PROMOTE a dev-fit);
  baselines beaten by `anchor_minus_beta_control`; inverted control
  strictly below anchor; DSR reported across the cohort's full trial
  history; reproduction exact. **Power gate (skeptic, binding): PROMOTE
  additionally requires ≥ 236 closed round trips on the union of dev folds
  OR a preregistered bootstrap CI on PF excluding 1.0 at the frozen seed;
  below that the best available label is `NOT_POWERED_CANDIDATE`**
  (eligible for prospective continuation, never PROMOTE). Output label is
  exactly `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` — this grants
  eligibility to REQUEST a prospective-shadow amendment (owner GO
  elsewhere), never S1, never live.
- **KILL:** any G-gate FAIL at dev (terminal for that arm); inverted
  control ≥ anchor, or inverted control passes G1@×1.0 on folds where the
  anchor fails a gate (the sign carried the information — chasing the
  inversion is rescue, immutable house law); causal control reproduces
  (§9.4); short/long-beta control explains the edge (§9.4); holdout net ≤
  0; concentration law breach. Kill is terminal for the identity on that
  pair; the failure registry is appended. **No replacement proposal enters
  mid-cohort** (a vetoed or killed Task-2 mechanism is
  `NOT_SCORED_FALSIFIED`, not a slot reopening).
- **TIME-STOP:** if by freeze+60 days the data gates of a pair have not
  passed, or a mechanism's falsifier battery has not completed, that
  mechanism/pair closes `BLOCKED_*` honestly — no assumed data, no pair
  substitution after any signal exists on the slate, no rushed gates. If
  the whole cohort's cells cannot reach G5 populations, the cohort closes
  `REJECT_ALL`/`BLOCKED_*` — both valid.

### 9.4 Control-prediction bands and the seam law (frozen)

- **Causal (clock-placebo) control:** net ≥ 0.5 × anchor net @ ×1.0 ⇒
  `KILL_CONTROL_REPRODUCED`; ALSO kills if the control is net-positive on
  ≥ 4/6 dev folds while the anchor's overall net is < 2× the control's
  (a clock that pays most folds is geometry, not mechanism).
- **Seam law (skeptic-refined, all pinned to the ×1.0 book; A7 F8 units +
  pairing pin):** let `S = net_dev(R-ORIG) − net_dev(R-ANCHOR)` on
  identical folds; `c_rt` = median full round-trip cost (per-session
  spread curve, base book, logged at freeze with the actual number);
  `N_diff` = count of round trips whose (entry_ts, direction) differ
  between arms (computable pre-PnL). **All quantities in the pair's own
  pip unit** (ledgered pips; USD conversion only at reporting). **`KILL_PIT_SEAM`
  fires if ANY of:** (i) `S > 10 × c_rt`; (ii) `S > 3 × c_rt` AND `S > 0`
  on ≥ 4/6 dev folds; (iii) per-trip mean of R-ORIG on its `N_diff`-only
  trips exceeds R-ANCHOR's mean on the nearest-in-time unmatched
  R-ANCHOR-only trip within the same UTC day (unmatched trips excluded
  and counted; equidistant candidate matches resolve to the EARLIER
  entry_ts — rule frozen; and if the matched-pair count is below the
  minimum-N floor pinned in §10, limb (iii) is `NOT_RUN` fail-closed and
  the limb-(i)/(ii) verdict stands) by > 1 × c_rt. `PASS_PIT` = none fire
  and M-2 non-vacuity holds. R-ORIG is never selectable regardless of
  outcome.
- **Inverted control:** ≥ anchor ⇒ `KILL_INVERSION` (plus the §9.3
  shadow-wins clause).
- **Beta law:** `anchor_minus_beta_control` ≤ 0 at ×1.0 ⇒
  `KILL_BETA_EXPLAINED`; ALSO fires at
  `anchor_minus_beta_control < 0.5 × anchor net` (a beta-matched baseline
  that explains half the edge leaves no mechanism worth a cohort slot).

## 10. Trial budget, ledger, denominators

- Cap: **24 scored cells** = Task 1: 2 pairs × 6 arms (R-ANCHOR, R-ORIG,
  R-NEIGH, causal control, inverted control, baseline-set counted as one
  composite arm) = 12; Task 2: ≤2 mechanisms × 6 arms × 1 anchor pair each
  (anchor pair = the mechanism's declared home pair, one per mechanism) =
  12. Holdout looks are NOT extra cells but are ledgered. Any re-run after
  a TECHABORT consumes budget (observed counter always).
- Ledger row per cell/look (contract, frozen): `cycle_id, mechanism_id,
  arm_id, arm_config_digest, pair, fold_or_holdout_tag, cost_tier, net_pnl,
  gross_pnl, gates_with_margins_to_fail, verdict, exclusion_zones,
  labels[], sha_chain{code_freeze, data_manifest, selection_digest}` —
  APPEND-ONLY (`trial_ledger.jsonl`; no row is ever edited; a bad row is
  corrected by a later row referencing it). **Mandatory labels on every
  row: `SINGLE_SOURCE_PANEL`, `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`,
  `PAPER_TIER` (owner D-C); control rows additionally persist
  `gross_pnl`/`net_pnl` decomposition (M3 condition; §A.2).** Observed vs
  published split per umbrella §5.8; DSR computed across ALL cohort trials
  (per-period series persisted); PBO = NOT_RUN (6-arm classes < 8 configs,
  fail-closed).
- Engine semantics: reuse the ancestry engine (pip-size parametrized,
  fixture suites byte-compatible) + new pair-scale fixtures; parity
  self-test vs the frozen law on the outcome-exposed pairs is FIXTURE-only
  (never reported as evidence).
- **GO-1 freeze-artifact mandatory pins (A7 round-2 D1, binding content of
  the freeze artifact; A7 prelaunch verifies all five before GO-2):**
  (i) the numeric bootstrap seed (§9.3 power gate) AND the mode-sham
  shuffle seed (§8 F-3), with their storage path (freeze JSON committed
  before any scored computation);
  (ii) the §9.1 holdout-pass membership artifact — the frozen list of
  anchor arms + companions per pair, sha256'd before the pass;
  (iii) the mode-sham outcome vocabulary, pinned as: non-vacuity failure
  (<2% labels change) ⇒ `KILL_VACUOUS_MUTATION` class (arm set re-derived
  once, pre-PnL, registered amendment inheriting the consumed look);
  seam-law firing attributable to the mode channel ⇒ `KILL_PIT_SEAM`;
  otherwise a diagnostic-only record — never a positive input;
  (iv) two-pair close semantics: identical UTC close law for both pairs
  (no fills on/after the 19:00 H1 bar, force-flat before 20:00 UTC,
  weekend flat) — no per-pair local-close variant exists in this cohort;
  (v) seam limb (iii) minimum-N evaluability floor: matched-pair count
  < 20 ⇒ limb (iii) `NOT_RUN` fail-closed (limbs (i)/(ii) decide).

## 11. A7 arc, decisions, close

- A7 fresh-context prelaunch before GO-2 (hashes chain, exact-arm identity,
  PIT/cost audits, dry-run hygiene, S1 sealed, denominator seed, zero
  unresolved HIGH/CRITICAL); A7 terminal at close. Positive claims get the
  stricter audit (handbook §22.2). A7 REFUSED = normal remediation arc.
  **Plan-audit arc (done, 2026-09-25): A7 verdict `PASS_WITH_CONDITIONS`
  — 0 CRITICAL / 0 HIGH; findings F1–F11 all dispositioned into this text
  (F1 sole-proposer disclosure §7.1; F2 representation law F-1; F3
  holdout one-look scope §9.1; F4 F-5 arithmetic clarification; F5 A1
  amendment status §3.2; F8 seam-law units/pairing §9.4; F10 D-B
  ratification item; F6/F7 recorded in appendix A.3; F9 fail-safe as
  written; F11 recorded). Report:
  `tracka_cohort1/A7_tracka1_plan_audit_REPORT.md`.**
- Terminal verdict vocabulary: umbrella §9 (paper-tier bound).
- Owner decisions: **LOCKED 2026-09-25 (second session):**
  **(D-B)** pair slate = AUDUSD + USDCAD, and Track A replication targets
  are the two NEW pairs ONLY — EURUSD/GBPUSD/USDJPY stay outcome-exposed
  ancestry, never re-scored here (A7 F10 ratified); **(D-C)** no
  independent-source unblock this cycle — Task-1b reconciliation-only,
  every result `SINGLE_SOURCE_PANEL` + paper tier; **(D-E)** blind
  proposer lanes ADDED (P1+P2 ran; composition literal-compliant), no
  additional mechanism slots, M2 not rescued.
  **REMAINING:** **(D-A)** the GO itself — the owner types GO-1 at this
  gate; **(D-F)** the proposed evidence classification of
  FX-RANGEFADE-2M-SHADOW-V1 as `DIAGNOSTIC_PENDING_PIT_REBASE`
  (`PROPOSAL_SHADOW_CLASSIFICATION_FX-RANGEFADE-2M_2026-09-25.md` —
  proposal only; daemon/journal/ledger untouched; no promotion, no
  $100k-account change; fail-closed default = no change).
  Related record: `INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25.md` — the
  ancestor-law PIT seam is a recorded incident; ancestor backtests are
  R-ORIG-semantics facts and are NOT evidence for the daemon's running
  law nor for R-ANCHOR (citation law inside the incident file). This
  drafting session executed NOTHING beyond read-only re-measure + council
  dispatch under umbrella light authority + this document.

## Appendix A — Council slate (FROZEN from the 2026-09-25 outcome-blind council)

Artifacts (authorities): `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/
tracka_cohort1/` — `EXPLORER_cohort1_REPORT.md`,
`SKEPTIC_cohort1_REPORT.md` (incl. the appended `D2 VETO ADJUDICATION`
section), `DATACOST_cohort1_REPORT.md`, and
`HANDOFF_tracka1_{explorer,skeptic,datacost}.json`
(`zcode_orch_v3_handoff@1`). All lanes measured the same base: root
`main` @ `69ddc60447d223249319f82b71b21e26ab941203` (a sha typo in one
dispatch packet's prose was caught and recorded as explorer incident I1;
the measured value governs everywhere). Slate hash-pinned at GO-1.

### A.1 Pair slate (Task 1) — LOCKED by owner D-B (2026-09-25): AUDUSD + USDCAD; spare USDCHF owner-amendment only

1. **AUDUSD** — Pacific commodity bloc (China/terms-of-trade beta),
   USD-quote so the beta control keeps EURUSD/GBPUSD semantics:
   **SHORT_ALWAYS** day-session beta control. Coverage/spread/scale =
   expectations pending the §5.2 gate (probe mandatory).
2. **USDCAD** — North-American oil bloc, USD-BASE pair: mirrored
   base/quote geometry (spread asymmetry, rollover side, pip geometry
   flip) makes replication a structural generalization, not a cosmetic
   swap: **LONG_ALWAYS** day-session beta control (USD sign flips with the
   convention).
3. Spare (owner amendment only): **USDCHF** — distinct bloc but its beta
   sign is window-dependent; if promoted, beta direction frozen
   pre-outcome by full-window drift-sign rule with the mid-window
   inversion disclosed.
   Excluded on record: NZDUSD (bloc-redundant with AUDUSD), EURJPY/
   GBPJPY/EURGBP (both legs consumed; no USD anchor for the beta
   framework), AUD-crosses/Scandies (liquidity/coverage depth).

### A.2 Mechanism slate (max 3; IDs stable)

- **M1 — RANGEFADE-PIT replication (Task 1; mandatory slot).** Arms per
  §4.2: R-ANCHOR (pct[d−1]) ×2 pairs, R-ORIG diagnostic ×2, R-NEIGH
  (0.25/0.75) ×2, clock-placebo causal control ×2, inverted control ×2,
  baseline set (FLAT + SHORT/LONG_ALWAYS, beta-matched reporting) ×2.
  = 12 cells. Structural expectation ≈125–300 decisions/pair/yr
  (clock arithmetic, no backtest); warmup ≈61 traded days.
- **M2 — XCONF-ABSORB (cross-leg attribution-gated absorption).**
  **VETOED at D2 by the skeptic under V-4_BLEND as written (corroborated
  by V-1): gating a PDHLOC-class home trigger with a PDHLOC-class
  reference-leg state is a gating combination of two ancestry
  observables; the "one composite observable" framing is the re-labeling
  V-4 exists to catch.** Disposition `NOT_SCORED_FALSIFIED`, slot CLOSED,
  no reassignment/repair loop this cohort (a cross-pair gate on a
  NON-ancestry observable may be a future-cohort proposal). The proposal
  text and its pre-declared kill candidate (`FXFV7-A6-P2` shadow) remain
  in the explorer report as failure memory.
- **M3 — QSTATE-ABSORB (provider-quote-state–gated edge absorption).**
  Home **USDCAD**. **ADMITTED at D2** (V-2 does not fire: the enumerated
  objects are price ranges; a spread-quantile is a different data layer
  and re-parameterizes nothing in the range-regime selection; no family
  function consumes the spread path — `v2_lib.py:27-28` is cost plumbing
  only; V-4 does not fire: single ancestry leg). Mechanism: absorb
  prev-day-band breaks ONLY when the just-closed break hour's median
  bid/ask spread ≤ its trailing 20-trading-day same-hour p60 — a break
  against calm quotes is a non-informed cascade (absorbable); a break
  with quote-widening is informed/rollover flow (stand down). Payer:
  forced stop/liquidation flow in calm hours (mandatory, anonymous,
  dispersed; makers quote, they do not initiate). Risk: short
  informed-break; named tail = slow informed accumulation deliberately
  executed in calm hours; secondary = London-fix-hour misclassification
  (handled by the per-session curve). Arms: anchor (p60 gate) + N1
  (60-day state window) + N2 (3-bar median state) + causal control
  (**spread-WIDE complement book** — same trigger, fade only where break
  spread > p60; must NOT reach ≥0.5× anchor) + inverted + baseline set
  (beta-matched = LONG_ALWAYS) = 6 cells. ≈125–450 decisions/yr
  expectation; warmup ≈1 month; no new downloads. **D2 pre-registered
  conditions (binding):** armed V-1 fixture (Spearman |rho| vs R-ANCHOR
  target array on USDCAD dev panel > 0.60 ⇒ `VETO_NOVELTY_RENAME`
  pre-score); T-1 session-collapse tripwire (≥80% of gate-open bars in
  one ≤6h UTC window ⇒ V-3 re-session kill); T-2 just-closed-bar PIT
  fixture; T-3 ≥2% mutation non-vacuity (state shifted one day must move
  the book); F-5 arithmetic kill pre-declared (measured stress round trip
  ≥ 2.0 pips vs hypothesis ≤ 1.5 pips ⇒ forced pre-PnL kill — M3 is the
  cohort's most cost-fragile cell, disclosed as design); G8 applies;
  **control-decomposition condition (proposers P1+P2 finding, integrated):
  the spread-WIDE complement is cost-handicapped by construction under the
  fill-bar-spread cost book (it trades exactly the wide-spread bars), so
  EVERY control arm persists its GROSS and NET decomposition; kill bands
  stay NET (the honest economic test — no band loosened) and the
  decomposition makes the reason (information vs cost) a matter of
  record;**
  occupancy-matched F-3 control.
  The six economic questions per mechanism (M1 included) are answered in
  full in the explorer report §2.1–2.2 and summarized in the owner packet.

### A.3 Council lane verdicts

**Session-2 additions (owner D-E, 2026-09-25):** blind proposers P1 + P2
ran under the same blindness law (independent lanes; artifacts
`PROPOSER1_cohort1_REPORT.md`, `PROPOSER2_cohort1_REPORT.md` + handoffs).
**No mechanism slot was opened and M2 was not rescued (owner instruction,
binding):** their proposals are recorded as FUTURE-COHORT CANDIDATES —
P1: PROV-ABSORB (provenance-gated band-break absorption — fade only when
the breached extreme formed in a liquid-session window); P2-A:
RECLAIM-ABSORB (fade band sweeps that close back inside — **cross-lane
tension on record: the explorer self-vetoed the retest/second-probe class
on `FXFV2-A4-P2` + displaced-fade class; a future cohort's D2 must
adjudicate the class question BEFORE any rho fixture**); P2-B:
PROBE-DEPLETION GATE (fade gated by within-day same-edge M1-probe count
≥2). None consumed a slot, a cell, or a look. Their design-review
findings ARE binding plan law now: F-3 mode-sham test (P1), §9.1
inverted-control holdout companion (P2), M3/controls gross+net
decomposition (P1+P2), F-4 beta-composition disclosure (P2).

- Explorer: slate as above; kill-first headline = the PIT seam ("the
  honest R-ANCHOR never produced any ancestry result; if F-PIT-1 fires,
  falsification with zero PnL is the correct outcome").
- Skeptic: **SURVIVES_AS_HYPOTHESIS — conditional** on the GO-1
  pre-conditions, ALL now integrated into this plan: §4.2 erratum
  (D2-confirmed with precision notes), F-PIT-1 = M-1..M-5 + seam law
  (i)(ii)(iii) before any PnL, power gate ≥236 RT / bootstrap CI,
  G8 hour-concentration, causal-control non-vacuity predicates,
  beta-kill margin 0.5×, holdout control clause, no-mid-cohort
  replacement law. Kill-first: the mandatory slot's object "does not
  honestly exist yet" (confirmed whole-day mode leak + third-law daemon +
  blind parity self-test).
- Data/cost critic: paper tier is the STRUCTURAL ceiling (license
  posture + unmeasured commission + single-vendor + fill-quality class);
  cost book hardenings integrated in §5.2/§6; blocking engine port defect
  (hard-coded PIP/PRICE_SCALE/band) integrated in §5.2.
- **A7 plan-audit errata recorded against lane reports (append-only — lane
  files unchanged, corrections govern here): the family-failure registry
  measures 126 entries (explorer said 127, A7 F6); the engine's signal
  shift is `engine.py:108` (skeptic cited :97-100) and the price scale is
  the literal `o / 1e5` at `build_bars.py:47` (A7 F7).**

### A.4 Cohort summary for the owner

2 mechanisms frozen (M1 replication ×2 pairs; M3 quote-state gate ×1
pair), 1 proposal vetoed pre-PnL (M2), 18 effective cells of the 24 cap,
two GO gates, and the honest expectation — stated by all three lanes —
that F-PIT-1 (the PIT seam) and F-5 (cost ceiling) are the modal killers;
`REJECT_ALL` is a fully valid outcome.
