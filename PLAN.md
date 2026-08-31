# V11 — LOW-TURNOVER CRYPTO DISCOVERY ON THE V10 RESEARCH FACTORY

> **Owner authority for a fresh coding-agent context. Read this file in full
> before creating agents, worktrees, commits or scored artifacts.**
>
> This is a new sprint. The V10/V10R clock expired and MUST NOT be extended or
> reused. V11 starts only when A1 records a new go-live timestamp, deadline and
> frozen contract as described below.

## 0. Measured entry state and source of truth

Measured on 2026-08-29 after fetching all GitHub refs:

- root `main` and `origin/main`: `394e2d7`;
- V10 terminal authority: `origin/orca/v10-integration@e6fa2b1`;
- the local linked worktree branch `orca/v10-integration` was fast-forwarded to
  the same `e6fa2b1` and measured clean;
- `main` and `orca/v10-integration` are divergent from merge-base `e5b0bab`;
  do not claim that V10 terminal evidence is on `main` until it has actually
  been merged;
- untracked `.DS_Store` files belong to the owner and are out of scope;
- V10 terminal verdict is `M01_FAMILY_REJECT`;
- M01 scored computations: 3; published cells: 2; one computed neighbour is
  unpublished because of a trial-key collision;
- ledger/published denominator: 119; scientifically observed scored
  denominator: at least 120 pending V11P reconciliation;
- no V10/V11 strategy is promoted to S1, paper, testnet or live.

Primary evidence:

- `research/control/v10r_run/family_terminal_m01.json` at `e6fa2b1`;
- `research/control/v10r_run/r4_reproduction_report.json` at `e6fa2b1`;
- `research/control/v10r_run/a7_prelaunch_v10r_host3/verdict_v2.json`;
- `research/control/v10r_run/event_log.jsonl`;
- terminal `CONTINUE.md` on `orca/v10-integration@e6fa2b1`.

Before acting, A1 MUST re-measure every SHA, branch, dirty file, active worker,
clock and denominator. If reality differs, preserve this snapshot as history,
write a delta report and use measured reality. Never silently rewrite history.

## 1. V10 conclusion — closed, do not rescue

Family `A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL` is closed REJECT:

| Arm | Status | Net result | Scientific reading |
|---|---|---:|---|
| anchor | published | -578745.6738 | gross price PnL approximately zero; loss is almost entirely costs |
| neighbour | computed, unpublished | -515951.9347 | same losing profile; trial identity collision prevented publication |
| C2 placebo | published | -607353.9182 | placebo approximately equals mechanism; no incremental flow information |

Further facts:

- anchor PF `2.42e-08`, 0/3 positive folds, 6916 positions;
- all Stage-A performance and stress gates failed except non-performance
  bookkeeping gates;
- reproduction was `ALL_MATCH` for 3/3 arms and 54/54 canonical artifact
  contents after normalising worktree-local absolute paths;
- A7 authorized the scored launch after data remediation;
- the failure is therefore useful scientific evidence, not a reason to lower
  fees, tune thresholds or rename the mechanism.

Forbidden M01 rescue actions:

- no fee/slippage reduction to make M01 profitable;
- no threshold/lookback/grid search on M01;
- no reduced-universe rescue after seeing symbol results;
- no maker-fill assumption without real order-placement and fill evidence;
- no M01-adjacent aggressor-flow proposal unless the novelty audit proves a
  different observable, counterparty, holding clock and causal control.

## 2. V11 mission

V11 has three equally important objectives:

1. Repair the last scientific-accounting defects exposed by V10 without
   changing any historical scored result.
2. Audit and, only if eligible, test two owner-seeded, literature-backed,
   low-turnover crypto-perpetual families: defensive residual/downside risk and
   lottery-demand/MAX/idiosyncratic skew.
3. Independently discover and select exactly **two additional genuinely new,
   low-turnover families** through outcome-blind agent research. Every eligible
   family has three preregistered cells: anchor, theoretically justified
   neighbour and causal negative control.

The factory path is fixed:

```text
frozen literature evidence packet + two owner-seeded family briefs
  -> outcome-blind mechanism proposals for two additional families
  -> novelty/rescue audit
  -> data and schedule-only cost feasibility
  -> selection freeze
  -> generic V10 adapter implementation
  -> exact-arm dry-run with temporary ledger
  -> code/data/spec freeze
  -> independent A7 prelaunch audit
  -> 3 chronological scored cells per family
  -> stress matrix
  -> independent reproduction
  -> family verdict and lessons register
```

V11 is successful if it produces honest, reproducible evidence. A terminal
`V11_REJECT_ALL`, `V11_BLOCKED_PRELAUNCH` or `V11_INCOMPLETE_NOT_PROMOTABLE`
is valid. Profit without clean provenance, controls and reproduction is not a
success.

## 3. Hard scientific boundaries

- V11 remains crypto-perpetual S0 screening only.
- Do not mix crypto with stocks, TradFi perpetuals or forex data/contracts.
- Do not open, inspect or score an untouched/future S1 window.
- No paper, testnet, live, credentials, orders or leverage deployment.
- No scored parameter grids, Bayesian optimisation, genetic search or manual
  tuning after any scored PnL is visible.
- No replacement family or replacement cell after a frozen cell is scored.
- Every computed scored result counts scientifically, even if publication
  fails. A ledger bug cannot make an observed trial disappear.
- Old worktrees, artifacts and ledgers are append-only historical evidence;
  never delete, overwrite or reset them.
- Missing evidence is `UNAVAILABLE_FAIL_CLOSED`, never inferred PASS.
- Push to remote only after A1 announces the exact commits and the owner has
  authorized that push. Local commits and local merges are allowed.

## 4. V11 clock, budget and starting denominator

### 4.1 Clock

- Operational clock: **12 hours** from V11 go-live.
- Go-live occurs only after P0 intake completes and A1 writes the absolute UTC
  deadline to `research/control/v11_run/run_contract.json` and
  `heartbeat.json`.
- No automatic extension.
- With less than 120 minutes remaining: start no new scored cell.
- With less than 45 minutes remaining: stop owned process groups safely,
  reconcile artifacts and close honestly.
- The discovery/engineering lanes may close early; the deadline is a ceiling,
  not a reason to wait.

### 4.2 Budget

- Target four selected families: two owner-seeded families plus exactly two
  agent-discovered families.
- Exactly three frozen cells per eligible selected family.
- Maximum V11 scored budget: **12 computed cells**.
- An owner-seeded family that fails novelty, data, cost, identity or prelaunch
  eligibility is recorded `BLOCKED_PRE_SCORE`; its three slots stay unused and
  may not be reassigned to a fifth family.
- No score before selection freeze and A7 authorization.
- Technical abort before any scored metric consumes zero budget only when a
  forensic `TECHABORT` artifact proves this.
- Once metrics are computed, the scientific-observation counter increments
  exactly once even if ledger publication fails.

### 4.3 Denominator

V11 intake starts with two counters:

```text
published_ledger_denominator = 119
observed_scored_denominator  = 120
```

The difference is the V10 M01 neighbour. P1 must reconcile it append-only.
Until A7 approves the reconciliation, V11 scored launch is blocked. DSR/PBO
and any multiple-testing statement use the conservative observed denominator,
never the smaller number.

## 5. Worktree topology and agent governance

### 5.1 Why worktrees live inside the project

All new worktrees MUST default to:

```text
/Users/hoangminhlong/my-quantitative/.worktrees/v11/
```

This path is inside the OpenCode project permission boundary and avoids the
repeated external-directory approval prompt caused by sibling paths such as
`~/my-quantitative-v11-wt/`. A1 adds `/.worktrees/` to `.gitignore` in the
bootstrap commit if it is not already ignored.

Do not use `$HOME`, `~`, unresolved globs or destructive cleanup commands in
worktree lifecycle commands. Do not remove worktrees without owner approval.

### 5.2 Concurrency policy

- A1 is the only integration/merge authority.
- At most **A1 + 3 light subagents** are active simultaneously.
- No subagent may create a child agent unless A1 records a bounded delegation
  in `worktree_manifest.json`.
- Heavy workers are separate from coding agents.
- Within one family, scored cells are serial.
- Up to three family chains may run concurrently, at most one cell per family,
  only when a fresh measured resource probe authorizes that many heavy workers.
  The fourth chain waits; the inherited heavy-worker ceiling remains three.
- Reproduction may use up to `min(3, measured_safe_cap)` isolated workers.
- Full pytest runs alone with zero heavy worker.

### 5.3 Worktree manifest contract

Before dispatch, A1 creates
`research/control/v11_run/worktree_manifest.json` with one record per lane:

```text
role
path
branch
bootstrap_sha
allowed_globs
forbidden_globs
expected_deliverables
commit_sha
targeted_test_command
test_result
status
merge_order
delegation_allowed
```

Rules:

- every lane begins at the exact same wave bootstrap SHA;
- each lane has non-overlapping write ownership;
- all unspecified files are read-only;
- PLAN.md, CONTINUE.md, global ledgers and central manifests are A1-only;
- each subagent returns one clean commit plus a small handoff JSON;
- subagents never merge, rebase, push or amend another lane's commit;
- A1 cherry-picks one commit at a time and tests after every pick;
- conflicts are resolved by returning work to the owning lane, not by broad
  unreviewed edits in integration.

### 5.4 Bootstrap topology

The current owner PLAN lives on divergent `main`, while V10 terminal evidence
lives on `orca/v10-integration@e6fa2b1`. A1 MUST preserve both histories:

1. Verify the only owner-approved tracked root change is this `PLAN.md`.
2. Add `/.worktrees/` to `.gitignore` if it is not already ignored; this is
   the only additional bootstrap edit A1 may make.
3. Commit exactly `PLAN.md` and, if changed, `.gitignore` on `main`; never add
   `.DS_Store` or any other file.
4. Create branch/worktree `orca/v11-integration` from that owner-plan commit:

   ```text
   branch: orca/v11-integration
   path:   /Users/hoangminhlong/my-quantitative/.worktrees/v11/integration
   ```

5. In `orca/v11-integration`, merge `orca/v10-integration@e6fa2b1` with a
   merge commit. Resolve:
   - `PLAN.md` to this V11 owner plan;
   - `CONTINUE.md` to the V10 terminal truth, then append the V11 intake delta.
6. Run targeted adapter tests and validate terminal JSON before declaring the
   resulting merge commit `V11_BOOTSTRAP_SHA`.
7. All subsequent lanes branch from a recorded wave SHA descended from this
   bootstrap.

Never merge V11 into `main` or push during bootstrap. Final integration is a
separate owner checkpoint.

### 5.5 Exact worktree and subagent launch procedure

A1 creates a worktree before spawning the agent that owns it. Never spawn two
agents into the root checkout or tell an agent to create its own unspecified
worktree.

For each wave, A1 applies this exact pattern with explicit values:

```bash
git -C /Users/hoangminhlong/my-quantitative worktree add \
  -b orca/v11p-a2-publication \
  /Users/hoangminhlong/my-quantitative/.worktrees/v11/p1-a2-publication \
  V11_BOOTSTRAP_SHA
```

`V11_BOOTSTRAP_SHA` is a placeholder in this document. A1 replaces it with the
measured full 40-character SHA; it must not pass the literal placeholder to
Git. Repeat with the exact path/branch listed for A3 and A4. Later waves use
their own frozen wave SHA, not the original bootstrap automatically.

After creation, A1 verifies every lane before dispatch:

```bash
git -C <exact-worktree-path> rev-parse HEAD
git -C <exact-worktree-path> branch --show-current
git -C <exact-worktree-path> status --porcelain
```

Required result: expected SHA, expected branch and empty status. A1 writes
these values into `worktree_manifest.json`, commits the manifest on integration
and only then spawns/delegates the subagents.

Every subagent prompt must contain this compact contract:

```text
ROLE: <A2/A3/... and one-sentence mission>
WORKTREE: <absolute path>
BRANCH: <exact branch>
BOOTSTRAP_SHA: <full SHA>
READ FIRST: <maximum 3-6 relevant authority files>
ALLOWED WRITES: <exact globs>
FORBIDDEN WRITES: PLAN.md, CONTINUE.md, central manifests, ledgers and all
                  unspecified paths
REQUIRED TESTS: <targeted commands>
REQUIRED ARTIFACTS: <exact paths>
COMMIT: one clean commit; no merge/rebase/push/amend
NO CHILD AGENTS unless worktree_manifest explicitly delegates them
RETURN ONLY: commit SHA, changed files, test counts, artifact paths, blockers,
             assumptions; detailed logs stay on disk
```

Operational rules for OpenCode/Orca:

- the subagent task must be launched with the absolute worktree path in its
  prompt and title;
- the subagent's first command verifies `pwd`, branch, SHA and clean state;
- if any identity differs, it stops before writing and reports
  `WORKTREE_IDENTITY_MISMATCH`;
- A1 monitors agents from the controller thread but does not duplicate their
  edits;
- when one agent finishes, A1 reviews/merges its commit while the other lanes
  may continue if they do not depend on that commit;
- a lane marked complete is not reused for an unrelated task; create a fresh
  branch/worktree from the next wave SHA instead;
- because all paths remain inside the project root, no broad external-directory
  permission should be necessary. Never solve a prompt by granting full-machine
  access; scope any unavoidable approval to `.worktrees/v11/*` only.

## 6. Phase P0 — measured intake and control plane

A1 owns this phase and must not delegate authority files.

Required measurements:

- UTC time and 12-hour deadline;
- root, V10 terminal and V11 bootstrap SHAs;
- dirty/untracked files in every owned worktree;
- active PIDs and process ownership;
- published and observed denominators;
- V11 budget `0/12`;
- available/total RAM and a preliminary heavy-worker cap;
- hashes of V10 terminal evidence;
- proof that no V11 scored artifact exists.

Required artifacts under `research/control/v11_run/`:

- `run_contract.json`;
- `state.json`;
- `heartbeat.json`;
- `event_log.jsonl`;
- `worktree_manifest.json`;
- `v10_terminal_intake.json`;
- `denominator_reconciliation.json` initially `PENDING`;
- `lessons_register.json`.

All JSON artifacts include schema, generated UTC, producer role, bootstrap SHA,
input hashes, command/measurement source, verdict and reasons.

## 7. Phase P1 — three parallel factory-repair lanes

A1 creates and dispatches exactly these three worktrees from
`V11_BOOTSTRAP_SHA`.

### A2 — publication identity and denominator reconciliation

```text
path:   .worktrees/v11/p1-a2-publication
branch: orca/v11p-a2-publication
```

Allowed production ownership:

- `research/adapter_v10/publish.py`;
- the minimum necessary identity definition in
  `research/adapter_v10/protocol.py`;
- new V11-specific publication/accounting helpers;
- dedicated tests and `research/audits/v11p/a2_*` evidence.

Deliverables:

1. Trial identity contains explicit `arm_id` and canonical
   `arm_config_digest`; every score-affecting arm field must influence the
   digest.
2. Anchor, neighbour and control produce distinct keys; exact replay of each
   produces the same key and zero additional publication.
3. Historical V10 keys remain readable; do not rewrite old ledger bytes.
4. Reconcile M01 neighbour append-only. Preferred outcomes:
   - append an explicit provenance-linked historical observation/amendment
     accepted by the ledger schema; or
   - retain ledger=119 but freeze a first-class observed denominator=120 used
     by all statistical consumers.
5. Tests prove compute-once increments observed count even when publication is
   refused, while a true idempotent replay increments neither counter.
6. Migration/fault tests cover collision, missing arm id, digest drift,
   duplicate replay and concurrent append.

Forbidden:

- changing M01 metrics or historical verdict;
- deleting/reordering historical ledger rows;
- weakening exactly-once or fail-closed behaviour.

### A3 — schedule-only cost feasibility gate

```text
path:   .worktrees/v11/p1-a3-costgate
branch: orca/v11p-a3-costgate
```

Allowed ownership:

- new `research/v11/cost_feasibility.py` and closely related V11 modules;
- dedicated tests;
- `research/audits/v11p/a3_*` evidence.

The gate may inspect schedules, target books, fills, funding cadence and cost
parameters but MUST NOT compute or expose scored return/PnL.

Frozen feasibility metrics:

- decision count per 365-day equivalent;
- one-way turnover from actual target deltas;
- base and stressed cost drag from adapter cost functions;
- median/maximum holding duration;
- per-symbol turnover contribution;
- expected funding-event count while held;
- proposed signal availability and missingness.

V11 default pre-score floors:

- no more than 60 scheduled discretionary rebalance decisions per 365 days;
- median intended holding period at least 3 calendar days;
- annualised base cost drag no greater than 8% of average gross capital;
- annualised fee×1.5/+2-tick stressed cost drag no greater than 12%;
- no symbol contributes more than 25% of total turnover;
- every value reproducible from schedule artifacts alone.

Risk/terminal forced-flat actions are reported separately from discretionary
decisions. Any threshold change must occur before proposal scoring and requires
an owner amendment; it may never be changed because a candidate failed.

### A4 — exact-arm dry-run and platform-safe QA

```text
path:   .worktrees/v11/p1-a4-preflight
branch: orca/v11p-a4-preflight
```

Allowed ownership:

- new `research/v11/exact_arm_dryrun.py` and preflight helpers;
- dedicated tests/fixtures;
- minimal platform-test corrections with explicit allowlist;
- `research/audits/v11p/a4_*` evidence.

Deliverables:

1. A no-real-PnL exact-arm dry-run traverses load -> signal shape -> schedule ->
   fills -> costs/funding shape -> dummy finite metrics -> temporary-ledger
   publication.
2. It proves all three arm identities are distinct before freeze.
3. It detects missing tick sizes, benchmark declaration, terminal valuation
   bar, funding bundle, stale manifest and non-finite payload.
4. Tests never rewrite tracked golden reports.
5. Platform-specific process/path tests are either made portable or explicitly
   scoped; no blanket skip and no weakening of scored-path assertions.
6. Running the relevant test suite leaves `git status --porcelain` unchanged.

### P1 integration order

After all three lanes ACK:

1. A1 reviews A2 and cherry-picks it first.
2. Run publication/ledger targeted tests.
3. Cherry-pick A3; run cost-gate tests.
4. Cherry-pick A4; run dry-run/platform tests.
5. Run the combined V11P acceptance matrix.
6. Run full pytest alone once, not once per subagent.
7. Diff the tree before/after tests; tracked mutation is a FAIL.
8. Create `V11P_REPAIR_SHA` only if all required gates pass.

No scored backtest is allowed during P1.

## 8. Phase L0/D1 — literature seeds and outcome-blind proposal wave

### 8.1 L0 — frozen literature evidence packet

Before proposal agents are dispatched, A1 creates and hashes:

- `research/proposals/v11/literature_evidence_packet.md`;
- `research/proposals/v11/literature_evidence_packet.json`;
- `research/proposals/v11/seed_defensive_residual_risk.json`;
- `research/proposals/v11/seed_lottery_max_skew.json`.

The packet is written before any V11 scored result exists. It may use published
papers, preprints from identifiable authors/institutions and official venue/API
documentation. Prefer primary sources; record title, authors, year, DOI or
stable URL, retrieval UTC and which exact claim is being used. Commentary,
social posts and vendor backtests may be listed as leads but cannot establish a
mechanism or set a parameter.

For every source, the packet maps:

```text
source claim
-> falsifiable crypto-perpetual hypothesis
-> required PIT fields and transformation
-> formation/holding/rebalance clock
-> expected sign and economic counterparty
-> causal negative control
-> external-validity risks
-> repo test that could reject the claim
```

Minimum external-validity checks include spot-to-perpetual transfer, funding,
shorting and borrow differences, survivorship/listing bias, liquidity filters,
BTC beta, transaction costs, publication-sample overlap and whether the paper's
universe/history is available in the frozen repo snapshot. Published returns
are priors, never evidence that the repo implementation is profitable.

Initial seed references, to be verified and frozen by L0 rather than copied
uncritically, include:

- *Revisiting the low-volatility anomaly in cryptocurrency markets*, Finance
  Research Letters (2026), DOI `10.1016/j.frl.2026.109851`;
- *Speculation and lottery-like demand in cryptocurrency markets*, Journal of
  International Financial Markets, Institutions and Money (2021), DOI
  `10.1016/j.intfin.2021.101289`;
- *Lottery-like preferences and the MAX effect in the cryptocurrency market*,
  Financial Innovation (2021), DOI `10.1186/s40854-021-00291-9`;
- official Binance USD-M Futures market-data documentation for supported bar,
  funding, OI and mark-price semantics.

The two owner-seeded family briefs are mandatory audit inputs:

1. **V11-SEED-DEFENSIVE-RESIDUAL-RISK** — build slow daily features only from
   completed base bars; residualise against frozen BTC context; test whether
   lower residual/downside-risk coins outperform higher-risk coins using a
   beta-aware long/short book and weekly-or-slower rebalance. L0 must freeze one
   literature-justified anchor, one adjacent formation/holding neighbour and a
   sign-destroying or mechanism-destroying causal control without reading V11
   PnL.
2. **V11-SEED-LOTTERY-MAX-SKEW** — build daily BTC-residualised MAX and/or
   idiosyncratic-skew features; test whether lottery-like speculative demand is
   overpriced using a low-lottery versus high-lottery book and weekly-or-slower
   rebalance. L0 freezes one paper-traceable anchor, one justified MAX/skew
   neighbour and a causal control before scored implementation.

These are fixed research families, not automatic winners. They receive no
waiver from novelty, orthogonality, data, cost, stress, negative-control or A7
gates. L0 may inspect schema, coverage and prewindow-only diagnostics but may
not compute candidate returns, PnL, PF, Sharpe or ranking on the scored window.

### 8.2 D1 — three independent proposal lanes for two additional families

From `V11P_REPAIR_SHA`, A1 creates three independent proposal worktrees and
dispatches A5, A6 and A8 concurrently. These agents receive only:

- data schema/availability;
- generic adapter contract;
- cost-feasibility thresholds;
- the frozen L0 literature packet and its source-quality/external-validity
  rules;
- mechanism-level lessons and forbidden-family inventory;
- no V10 candidate PnL table beyond the statement that high-turnover M01 had
  zero gross edge and was rejected;
- no V11 scored-window candidate returns, PnL, ranking or tuned diagnostics;
- no other proposal agent's output.

Outcome-blind agents MAY search academic literature and official data/venue
documentation before proposal freeze. Each lane logs queries, retrieval UTC,
accepted/rejected sources and the reason for every parameter mapping. Literature
search must finish before that lane computes any candidate return; later papers
cannot be used to redesign a proposal after scored evidence is visible.

Worktrees:

```text
.worktrees/v11/d1-a5-proposals  orca/v11d-a5-proposals
.worktrees/v11/d1-a6-proposals  orca/v11d-a6-proposals
.worktrees/v11/d1-a8-proposals  orca/v11d-a8-proposals
```

Each agent proposes exactly two mechanisms in JSON+Markdown under its own
non-overlapping file prefix in `research/proposals/v11/`.

Every proposal must specify before any scored implementation:

- primary-source citations and a source-claim-to-test mapping;
- economic mechanism and expected counterparty;
- required observable fields and PIT clock;
- universe and benchmark role;
- schedule, holding period and turnover rationale;
- target construction and risk neutralisation;
- anchor, neighbour and causal negative control;
- expected sign and falsification condition;
- funding/cost treatment;
- known ancestry/proximity to all V1–V10 families;
- data readiness and implementation estimate;
- why it is not a rescue of a previously rejected family.

The two owner-seeded families are already reserved and do not count among the
six blinded proposal documents. Proposal agents must seek other genuinely
orthogonal low-turnover mechanisms supported by current bars/funding data.
They may use research literature to generate priors, but copying a paper title
without a PIT implementation path, counterparty, falsification rule and
perpetual-specific caveat is ineligible.

Proposals are ineligible if they are merely new lookbacks/thresholds for:

- trend or momentum;
- reversal/residual mean reversion;
- funding carry/crowding rescue;
- volume-shock continuation;
- weekly reversal;
- M01 aggressor-flow absorption.

## 9. Phase D2 — novelty and feasibility audits

A1 merges the frozen L0 packet, two seed briefs and six outcome-blind proposal
documents only, creating `V11_PROPOSAL_POOL_SHA`. Then two independent agents
run in parallel:

### A7-N — novelty and anti-rescue auditor

```text
path:   .worktrees/v11/d2-a7-novelty
branch: orca/v11d-a7-novelty
```

Responsibilities:

- verify the literature packet's source identity, claim mapping and
  spot-to-perpetual caveats without treating publication as profitability proof;
- map both seed families and all six proposals against V1–V10 inventory;
- reject hidden parameter rescues;
- measure prewindow signal-rank similarity where implementable;
- require `abs(rho) < 0.50` versus rejected ancestors;
- require every pair among the four frozen families to have `abs(rho) < 0.35`
  on common eligible prewindow stamps;
- challenge the proposed negative control and falsification logic;
- publish objections without editing proposals.

### A9-F — data, turnover and implementation feasibility auditor

```text
path:   .worktrees/v11/d2-a9-feasibility
branch: orca/v11d-a9-feasibility
```

Responsibilities:

- verify every required field exists PIT-correctly for the frozen window;
- run schedule-only feasibility without PnL;
- apply all P1 cost/turnover floors;
- check minimum eligible symbols per decision;
- estimate compute/RAM/runtime using representative feature generation;
- flag any need for new external data; do not download it without owner scope;
- produce PASS/FAIL/UNAVAILABLE for both seed families and every proposal.

No candidate score or return may be produced in D1/D2.

## 10. Phase D3 — four-family selection freeze

A1 evaluates the two owner-seeded families and selects exactly two additional
eligible families from the six outcome-blind proposals using only frozen rubric
scores and audit outputs. The target freeze is four families total. No
discretionary replacement is allowed after opening scored results.

Required eligibility:

- genuinely novel mechanism and no rescue veto;
- data readiness PASS;
- cost feasibility PASS;
- implementable through the existing generic adapter;
- explicit anchor, neighbour and causal negative control;
- pairwise orthogonality threshold PASS;
- expected holding and turnover within V11 floors;
- no unresolved HIGH/CRITICAL objection.

Tie-break for the two discovered slots is lexicographic hypothesis id. If fewer
than two discovered families are eligible, close
`V11_BLOCKED_SELECTION_INSUFFICIENT`; do not lower thresholds. If an
owner-seeded family is ineligible, record it `BLOCKED_PRE_SCORE`, leave its
three scored slots unused and do not replace it with a third discovered family.

Freeze artifacts:

- `research/control/v11_run/selection_freeze.json`;
- one immutable spec per selected family;
- exact `arm_id` and `arm_config_digest` for up to twelve cells;
- feature/window/fold/universe/cost/funding/stress hashes;
- budget `0/12` and observed denominator start;
- implementation ownership and file allowlists.

After freeze there are no grids, no parameter changes and no substitute slots.

## 11. Phase I — four family implementations in resource-gated waves

A1 creates one worktree per eligible frozen family from the exact
selection-freeze SHA:

```text
.worktrees/v11/i-family-1  orca/v11i-family-1
.worktrees/v11/i-family-2  orca/v11i-family-2
.worktrees/v11/i-family-3  orca/v11i-family-3
.worktrees/v11/i-family-4  orca/v11i-family-4
```

Families 1 and 2 are the owner-seeded families in the fixed order above;
families 3 and 4 are the selected outcome-blind discoveries. A1 dispatches at
most three light implementation lanes at once and starts the fourth only after
a slot is free. An ineligible seed family has no implementation worktree.

At selection freeze, replace generic names with the frozen hypothesis ids and
record exact non-overlapping file allowlists. Each implementer owns only:

- one strategy module;
- one adapter plugin;
- its tests/golden feature vectors;
- its C1-style field verification artifact;
- no central registry/factory/publication files.

Implementation requirements per family:

- completed-bar and PIT-correct features;
- no future universe selection;
- deterministic targets and schedule;
- explicit BTC benchmark/hedge semantics;
- native funding while held;
- generic adapter costs/fills/stress only;
- distinct frozen identities for anchor/neighbor/control;
- dummy/synthetic causal tests for expected sign and negative control;
- double-generation determinism;
- schedule-only cost feasibility PASS;
- exact-arm dry-run PASS with temporary ledger;
- targeted suite and clean-tree handoff commit.

A1 cherry-picks family implementations one at a time. A1 or one short-lived
wiring agent may make one centralized registry/factory commit after all
eligible plugins exist. Wiring may not duplicate/fork the adapter.

## 12. Phase Q — integrated QA and fresh freeze W11

Before scored execution:

1. Run targeted suites for every eligible family and shared adapter.
2. Run a combined up-to-twelve-arm exact dry-run into an empty temporary ledger:
   - one distinct trial key per frozen arm;
   - one first publication per frozen arm;
   - one replay per arm with zero denominator delta;
   - no real scored metric or result artifact.
3. Run full pytest alone; tree must remain clean.
4. Re-run data coverage against loader-selected values, not merely files that
   exist somewhere in staging.
5. Verify funding settlements, instruments, tick sizes and terminal valuation
   coverage for every selected symbol.
6. Run a fresh resource probe and freeze `measured_safe_cap` plus operative
   heavy cap.
7. Freeze final code-bearing `W11`.
8. Create fresh detached execution/reproduction trees inside
   `.worktrees/v11/exec-*` at exactly W11; stage data read-only and require
   byte-identical manifests.

Old V10 R1c/R2c may be read as evidence but never reused to score V11.

## 13. Phase A7 — independent prelaunch audit

A new A7 audit worktree is created only after W11:

```text
.worktrees/v11/a7-prelaunch  orca/v11-a7-prelaunch
```

A7 writes only under `research/audits/v11p/` and may not edit production code,
contracts, specs, data or score artifacts.

A7 independently recomputes:

- code/data/spec/manifest/execution-tree pin chain;
- publication identity and denominator reconciliation;
- up-to-twelve-arm dry-run uniqueness/idempotence;
- PIT/no-leakage, window/folds/warmup/purge;
- data/funding/instrument/tick/terminal coverage;
- schedule-only cost feasibility;
- novelty/rescue and selected-family orthogonality;
- negative-control definitions;
- stress matrix completeness;
- resource cap and process ownership;
- budget 0/12 and absence of scored artifacts;
- full/targeted test evidence and clean trees;
- deadline remaining at least 120 minutes.

Launch requires explicit `V11_LAUNCH_AUTHORIZED`, zero unresolved
HIGH/CRITICAL, measured heavy cap at least 1 and all hashes pinned. Otherwise
close/remediate within frozen scope and re-audit; no scored launch.

## 14. Phase E — up to twelve scored cells

Each family executes in frozen order:

1. anchor;
2. neighbour;
3. negative control.

Concurrency:

- cells within a family are serial;
- up to `min(3, measured_safe_cap)` families may each run one cell concurrently
  when their worktrees/output/registry shards are isolated; the remaining
  family chains wait;
- A1 remains the sole publisher/ledger reconciler;
- no pytest while a scored worker is active.

Per-cell mandatory path:

```text
preflight pins
-> schedule/targets
-> chronological folds with warmup/purge
-> next-allowed-event fills
-> costs + native funding
-> base result
-> fee x1.5, +2 ticks, +1 event delay
-> drop-one-symbol and drop-one-fold
-> benchmark/context and concentration
-> canonical artifacts
-> observed counter +1
-> append-only publication exactly once
```

A computed metric can never be hidden because publication fails. A1 records
both counters after every cell. No cell result may alter later frozen cells.

## 15. Phase R — reproduction and terminal science

- Reproduce every computed cell, up to twelve, in clean fresh processes from the reproduction
  trees.
- Require exact/all-match on signals, schedule, trades, positions, costs,
  funding, folds, metrics, stress outputs, hashes and verdict inputs.
- Worktree-local absolute paths may be normalised only when the normalisation
  rule was frozen before reproduction.
- Run independent A7 terminal audit after reproduction.

Stage-A gates per family remain:

- after-cost expectancy > 0;
- PF >= 1.10;
- at least 2/3 folds positive;
- no populated fold PF < 0.80;
- no positive fold contributes > 50% of positive PnL;
- MDD <= 10%;
- symbol contribution <= 40%;
- minimum trade/decision evidence adequate for the family clock;
- drop-one-symbol and drop-one-fold survival;
- stressed PnL > 0 and stressed PF >= 1.00;
- neighbour supports the anchor;
- causal negative control shows incremental mechanism information;
- schedule-only cost gate remained valid on realised schedules;
- reproduction all-match;
- zero unresolved HIGH/CRITICAL;
- multiple-testing statistics use observed denominator >=120 plus every V11
  computed scored cell, or are `UNAVAILABLE_FAIL_CLOSED` with zero credit.

Allowed family outcomes:

- `V11_FAMILY_REJECT`;
- `V11_STAGE_A_SURVIVOR_LOCKED_FOR_FUTURE_S1`;
- `V11_FAMILY_BLOCKED`;
- `V11_FAMILY_INCOMPLETE_NOT_PROMOTABLE`.

Allowed sprint outcomes:

- `V11_REJECT_ALL`;
- `V11_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1`;
- `V11_BLOCKED_PRELAUNCH`;
- `V11_INCOMPLETE_NOT_PROMOTABLE`.

Even a survivor is only locked for a future non-overlapping S1 plan. V11 may
not inspect S1, paper trade or place orders.

## 16. Token, context and runtime efficiency

The prior workflow consumed excessive tokens. V11 applies these limits:

- A1 reads this PLAN, terminal V10 evidence and current authority files once;
  it does not replay the full V1–V10 conversation.
- Subagent prompts contain only their scope, interfaces, allowed files,
  acceptance tests and the minimum referenced evidence.
- Agents use `rg`/`rg --files`; no broad dumps of results or all Git history.
- Tool output and detailed logs go to artifacts, not conversation.
- Every subagent handoff is at most approximately 2,000 tokens and contains:
  commit SHA, files changed, tests, artifact paths, blockers and assumptions.
- Proposal agents do not run the full suite.
- Implementation agents run targeted tests only.
- A1 runs the combined/full suite once per integration wave.
- A7 audits by recomputation but does not reread irrelevant historical prose.
- No foreground `sleep` polling. Use background workers, PID/event logs and
  heartbeat/status commands.
- Do not repeatedly ask the owner for GO. Stop only at an explicit boundary:
  credentials/network-data expansion, push, deletion, S1/live, expired clock
  or an unresolved gate requiring a scientific choice.

## 17. Mandatory checkpoints and reports

A1 publishes concise checkpoints to the owner and full artifacts to disk:

1. intake/merge: SHAs, dirty state, deadline, denominator and topology;
2. P1: three repair commits, tests and reconciliation verdict;
3. L0/D1: frozen literature packet, two seed briefs and six outcome-blind
   proposals received;
4. D2/D3: novelty/feasibility results, seed dispositions and exact two
   discovered-family selections; target four-family freeze;
5. I/Q: implementation commits, up-to-twelve-arm dry-run, full suite, W11 pins;
6. A7: prelaunch verdict and resource cap;
7. after each scored cell: cell id, publication status, counters, no tuning;
8. reproduction: exact computed-cell count, up to 12/12 status;
9. terminal: family verdicts, denominator/budget, workers=0, clean state,
   commit graph and next safe action.

## 18. Definition of Done

V11 is complete only when all applicable items are true:

- V10 terminal history and this owner PLAN coexist in `orca/v11-integration`;
- worktree manifest proves isolated ownership and clean merges;
- trial identity collision is fixed and historical compatibility tested;
- published/observed denominator difference is explicitly reconciled;
- schedule-only cost gate and exact-arm dry-run are operational;
- a frozen, source-audited literature packet and two owner-seeded briefs exist;
- exactly six outcome-blind proposals were evaluated, exactly two additional
  eligible families were selected, and each seed has an explicit eligible or
  `BLOCKED_PRE_SCORE` disposition, or selection closed honestly;
- selected families use the generic adapter, not forks;
- fresh W11/execution/reproduction pins are exact;
- A7 prelaunch is explicit;
- at most twelve computed scored cells exist and every one is counted;
- reproduction and terminal A7 audit are complete, or the sprint closes with
  a truthful BLOCKED/INCOMPLETE state;
- `PLAN.md`, `CONTINUE.md`, Wayfinder map, master JSON+Markdown report,
  lessons register, state and heartbeat agree;
- owned workers are zero and integration is clean;
- no S1/live boundary was crossed;
- no remote push or main merge occurred without owner authorization.

## 19. A1 first response and autonomous continuation

The first response from a fresh A1 thread must report, before dispatch:

```text
measured UTC
main SHA
V10 terminal SHA
dirty/untracked files
owner PLAN commit SHA
V11 integration path/branch/bootstrap SHA
new 12-hour deadline
published denominator / observed denominator
budget 0/12
active workers
P1 worktree paths, branches and allowlists
preliminary heavy cap
GO/NO_GO for light coding lanes
```

After that report A1 continues automatically through safe local,
non-destructive phases. It does not wait for repeated owner approval between
light-agent waves. It must stop before push/main merge, new external data,
deletion, S1/live activity, deadline extension or any scientific threshold
change.
