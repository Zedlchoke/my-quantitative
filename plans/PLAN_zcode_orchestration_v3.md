# ZCODE-ORCHESTRATION-V3 — one Lead session, automatic subagents, durable handoffs

> Status: `PLANNED_NOT_STARTED`.
>
> This plan automates coordination, not scientific judgment. It uses supported
> ZCode mechanisms only: primary Agent, custom/plugin subagents, background
> returns, commands, skills, hooks, MCP and optional Automations. Direct writes
> to ZCode session databases, task SQLite files or undocumented internal state
> are forbidden.

## 0. Owner problem and desired outcome

Current manual flow:

```text
Lead thread + Crypto thread + Stocks thread + Forex thread
worker finishes -> owner notices -> owner copies report -> owner pastes to Lead
Lead reads report -> Lead writes next prompt -> owner pastes prompt to worker
```

Desired flow:

```text
owner starts one Lead session once
Lead dispatches ZCode subagents in foreground/background
subagents return automatically to the Lead conversation
Lead validates handoff artifacts, integrates and dispatches the next ready work
owner is notified only at a true authority blocker or terminal verdict
```

Strongest positive verdict:

```text
ZCODE_ORCHESTRATION_V3_PASS_AUTONOMOUS_HANDOFF_CANARY
```

It means the owner no longer copies ordinary agent outputs between threads. It
does not authorize unattended scoring, S1, provider decisions, push/merge or
live trading.

## 1. Verified ZCode capability boundary

Official documentation measured during planning:

- Subagents run in isolated context and summarize back to the primary Agent.
- Background subagent outcomes return to the main conversation automatically,
  and the primary Agent can continue from them.
- Custom subagents are user-level Beta, stored under
  `~/.zcode/agents/<name>.md`; plugins can bundle subagents for distribution.
- A subagent cannot spawn another subagent.
- ZCode v3.7.1+ injects user/workspace `AGENTS.md` into subagents by default;
  built-in Explore is an exception.
- `CLAUDE.md` is not continuously loaded by ZCode Agent; workspace rules must
  be available through `AGENTS.md` or explicit plan instructions.
- Hooks are local subprocesses for SessionStart, prompt/tool/stop events; hooks
  cannot call the model themselves.
- Project `.zcode` hook configuration is currently ignored; distributable
  project hooks must live in an installed plugin or user-level config.
- Stop hooks can request continuation only a bounded number of times, so they
  are a safety gate, not a durable scheduler.
- Automations can run scheduled/idle work only while the computer and ZCode app
  are awake; they are not a substitute for the controller state machine.

Sources to reverify at implementation:

```text
https://zcode.z.ai/en/docs/subagents
https://zcode.z.ai/en/docs/hooks
https://zcode.z.ai/en/docs/plugin
https://zcode.z.ai/en/docs/automations
https://zcode.z.ai/en/docs/agents
https://zcode.z.ai/en/docs/mcp-services
```

## 2. Core architecture decision

### 2.1 One primary Lead session

Use one ZCode primary conversation as the only reasoning controller for a
logical program run. The existing Crypto/Stocks/Forex top-level threads may
remain as historical/read-only views, but they are no longer message buses or
authorities.

Because subagents cannot create children, hierarchy is deliberately one level:

```text
ZCode primary Lead/A1
├── read-only explorer
├── crypto lane agents
├── stocks lane agents
├── forex lane agents
├── implementation/reproduction agents
└── independent A7 agents
```

The primary Lead alone dispatches every subagent, even when a task conceptually
belongs to an asset controller. This preserves one authority and avoids an
unsupported nested-agent design.

### 2.2 Two channels of communication

1. **ZCode return channel** — foreground/background subagent result returns
   automatically to the primary conversation.
2. **Durable artifact channel** — every task and handoff is represented by a
   machine-readable file so a compacted/restarted session can recover without
   copying chat text.

Chat summaries are convenient; artifacts are authority.

### 2.3 Official plugin, not internal database manipulation

Build a repository-owned ZCode plugin:

```text
plugins/quant-research-orchestrator/
├── .zcode-plugin/plugin.json
├── agents/
│   ├── quant-explorer.md
│   ├── quant-implementer.md
│   ├── quant-reproducer.md
│   └── quant-auditor.md
├── commands/
│   ├── lead-start.md
│   ├── lead-status.md
│   ├── lead-resume.md
│   └── lead-close.md
├── skills/
│   ├── controller-loop/SKILL.md
│   ├── dispatch-packet/SKILL.md
│   └── structured-handoff/SKILL.md
├── hooks/hooks.json
├── scripts/
│   ├── hook_session_start.py
│   ├── hook_pre_tool.py
│   ├── hook_post_agent.py
│   └── hook_stop.py
└── .mcp.json
```

The plugin is installed through ZCode's local personal marketplace and fully
reviewed before enablement. Enabled hooks execute local code and therefore
receive the same security scrutiny as repository code.

## 3. Repository control plane

### 3.1 Runtime versus committed evidence

```text
gitignored runtime:
  .runtime/orchestrator_v3/tasks.json
  .runtime/orchestrator_v3/events.jsonl
  .runtime/orchestrator_v3/heartbeats/
  .runtime/orchestrator_v3/inbox/

committed cycle evidence:
  research/control/<cycle>/orchestration/
    dispatch_manifest.json
    handoffs/*.json
    integration_events.jsonl
    terminal_reconciliation.json
```

Runtime files coordinate live work; committed files support claims. Scientific
ledgers and frozen cycle artifacts remain under their existing authorities.

### 3.2 Task schema

Every task has:

```text
task_id / cycle_id / role / objective
created_utc / updated_utc
parent_controller_id (always the primary Lead; no nested parent)
status / dependencies / priority / workload_class
base_sha / branch / absolute_worktree
allowed_paths / forbidden_paths
required_inputs with hashes
required_outputs
test_commands / stop_conditions
background_allowed
zcode_invocation_id when exposed
heartbeat / attempts / max_attempts
handoff_path / blocker / terminal_reason
```

Allowed state machine:

```text
REGISTERED
-> READY
-> DISPATCHED
-> RUNNING
-> HANDOFF_READY
-> VALIDATING
-> INTEGRATED | REJECTED | BLOCKED | TECHABORT
-> TERMINAL
```

No backward transition. Retry creates a new attempt record; it does not erase
the failed attempt.

### 3.3 Structured handoff schema

```text
task/cycle/role/lane
dispatch SHA and actual starting SHA
commit SHA and changed paths
tests: command/exit/PASS|FAIL|NOT_RUN/log digest
authority claims (normally empty for lane agents)
known limitations/incidents
tree status/workers/processes
outputs and hashes
recommended next action
```

The Lead treats free-form chat output as advisory until the handoff schema,
Git state and evidence validate.

## 4. ZCode subagent definitions

### 4.1 quant-explorer

- Read/Grep/Glob/WebSearch/WebFetch only.
- No edits, Bash mutation, Git changes or authority decisions.
- Returns evidence paths and uncertainties.
- Built-in Explore does not inject AGENTS.md, so the dispatch packet must carry
  its specific boundary.

### 4.2 quant-implementer

- Read/Grep/Glob/Bash/Edit/Write as required.
- One worktree, one ownership manifest, one focused commit.
- Cannot merge, rebase, push, update ledger/registry or touch another lane.
- Must publish structured handoff before return.

### 4.3 quant-reproducer

- Detached tree and frozen inputs only.
- Cannot repair implementation or reinterpret tolerances.
- Emits comparison artifacts and `ALL_MATCH|MISMATCH|NOT_RUN`.

### 4.4 quant-auditor

- Fresh-context A7 behavior.
- Reads frozen claim/evidence; writes audit namespace only.
- Cannot fix code, weaken gates or select a convenient verdict.
- Prefer separate model/context from implementer.

Descriptions must be narrow enough that the primary Agent chooses the right
role automatically. Tool allowlists are exhaustive. Path-level protection is
enforced by hooks because ZCode tool permissions are tool-level, not an
ownership system.

## 5. MCP controller service

Create a small local stdio MCP server backed by existing governance modules,
not a second scheduler authority. Proposed tools:

```text
orchestrator_intake
orchestrator_register_task
orchestrator_list_ready
orchestrator_mark_dispatched
orchestrator_heartbeat
orchestrator_publish_handoff
orchestrator_validate_handoff
orchestrator_mark_integrated
orchestrator_record_blocker
orchestrator_waiting_summary
orchestrator_terminal_check
```

Rules:

- MCP never calls a model or spawns ZCode agents by itself.
- The primary Lead invokes ZCode's Agent tool after registering a task.
- MCP uses atomic write, fsync/rename, schema validation and append-only events.
- Repeated tool calls are idempotent by task/attempt/digest.
- It wraps/reuses `researchctl` registry, scheduler and heavy-lock state rather
  than cloning them.
- Missing/malformed runtime state is `CONTROL_STATE_DRIFT`, not empty queue.

## 6. Hooks

### 6.1 SessionStart

Inject a compact, generated snapshot:

- cwd/branch/HEAD/dirty;
- canonical active cycles;
- heavy lock and reconciled jobs;
- pending handoffs/blockers;
- current plan and next ready task;
- S1/GO boundary.

The hook is read-only and has a strict timeout. Failure is visible but must not
silently invent a clean state.

### 6.2 PreToolUse

For Agent/Task/Bash/Edit/Write operations:

- confirm current task/worktree/branch/base;
- enforce allowed/forbidden paths;
- block ledger/registry writes by lane agents;
- block push, main merge, destructive reset, credential echo and S1 paths;
- inspect heavy lock before heavy commands;
- require an ownership manifest before writable subagent dispatch.

The hook does not grant authority that the plan/owner did not grant.

### 6.3 PostToolUse / PostToolUseFailure

- record dispatch/invocation result when available;
- validate handoff path after an Agent/Task returns;
- classify tool failure and inject bounded recovery guidance;
- mark missing handoff as `HANDOFF_INVALID`, never infer success from prose.

### 6.4 Stop

Before the primary Agent finishes, check:

- active owned tasks;
- returned but unvalidated handoffs;
- integration gates not run;
- unreconciled state/heartbeat/registry;
- real owner-authority blocker;
- terminal report status.

If useful work remains, request continuation with a compact next action. Since
ZCode bounds repeated Stop blocking, durable recovery remains the MCP/task
state plus `/lead-resume`, not an infinite hook loop.

Project-level hooks are not used because the current ZCode version ignores
them. Hooks ship inside the installed plugin.

## 7. Workspace instructions and context economy

Create a workspace `AGENTS.md` because ZCode does not continuously load
`CLAUDE.md`. It should be a compact router, not a duplicate 1,500-line manual:

```text
repo mission and invariant summary
read applicable plan in full
CLAUDE.md + handbook authority pointers
worktree/branch/lock/S1/push boundaries
required structured handoff
commands to remeasure state
```

Context policy:

- primary Lead reads full plan and handbook;
- subagents receive a generated 2-8 KB role packet with exact hashes/paths;
- subagents do not receive unrelated terminal histories or scored outcomes;
- A7 receives the claim and evidence set, not implementer persuasion;
- compaction checkpoint is written to artifacts before `/compact`;
- project memory is not assumed available to subagents.

## 8. Controller loop

The reusable `$controller-loop` skill instructs the Lead:

```text
1. reconcile repository/runtime truth
2. validate current plan and owner authority
3. register dependency graph
4. dispatch all READY disjoint light tasks, within slot cap
5. keep integration/control work moving
6. accept returned handoff automatically
7. validate Git/evidence independently
8. integrate one commit at a time and run targeted gates
9. unlock dependent tasks
10. queue/wait for heavy work under global lock
11. dispatch reproduction then A7
12. terminal-reconcile and notify owner
```

Owner notification occurs only for:

- credential/account/license/purchase decision;
- S1/scored GO required by plan;
- push/main merge/deployment authority;
- irreconcilable ownership/semantic choice;
- repeated blocker after safe alternatives are exhausted;
- terminal verdict.

Ordinary PASS/FAIL handoffs do not require copy/paste or owner acknowledgment.

## 9. Automations usage

Automations are optional recovery/watchdog aids:

- one same-session hourly read-only health task may inspect stale tasks,
  heartbeats, lock and pending handoffs;
- it may prompt the Lead session to resume from durable state;
- it cannot mutate code, grant GO, run scoring or delete tasks;
- Keep Awake is an owner UI choice;
- a sleeping/closed computer means skipped execution and must remain visible;
- do not create one scheduled task per lane or exhaust ZCode's task limit.

Normal background subagent return is the primary continuation mechanism.

## 10. Implementation phases

### P0 — capability and version probe

Remeasure ZCode version, subagent availability, Agent tool, foreground/background
return, AGENTS.md injection, plugin loading, hooks, MCP and Automations. Use a
disposable fixture project. Any unsupported capability changes the design;
never simulate it by editing internal databases.

### P1 — contract freeze

Freeze plugin layout, task/handoff/event schemas, state transitions, role tool
permissions, hook I/O, MCP methods, ownership enforcement, retry policy,
notification boundaries and canary cases.

### P2 — state/MCP lane

Implement atomic task store and stdio MCP wrapper with unit tests for:

- state transitions and idempotency;
- concurrent claims;
- controller restart;
- duplicate return;
- stale heartbeat/dead PID;
- malformed state;
- dependency cycle;
- foreign task/worker isolation;
- reconciliation with researchctl.

### P3 — plugin agents/commands/skills lane

Implement definitions and commands. Validate manifest/frontmatter, exact tool
names, `thoughtLevel` spelling, maxTurns and AGENTS.md injection behavior.

### P4 — hooks lane

Implement hook subprocesses and fixture-test every event JSON/exit behavior:
allow, deny, inject context, failure, timeout and Stop continuation. Prove path
ownership and destructive/credential/S1 guards.

### P5 — integration and local installation

A1 integrates state -> plugin -> hooks sequentially, runs tests, creates a
local marketplace entry and asks the owner only for the explicit trust/install
action if ZCode UI requires it. Start a new session after install because
subagent/hook configuration is snapshotted at session start.

### P6 — canary 1: read-only

Lead dispatches two Explore-style tasks in parallel. They automatically return;
Lead validates artifacts and produces a combined report without owner relay.

### P7 — canary 2: isolated implementation

Lead creates two disjoint fixture worktrees, dispatches implementers, receives
handoffs, validates and integrates sequentially, then runs targeted tests.
No real asset cycle is touched.

### P8 — canary 3: reproduction and A7

Lead dispatches reproducer and then independent auditor. Deliberately inject
one bad handoff/path mismatch and prove hooks/controller refuse it. Repeat with
a valid handoff and close.

### P9 — interruption recovery

Close/restart the ZCode session after durable checkpoint. `/lead-resume` must
reconstruct ready/running/returned tasks from files and real Git/process state,
without pasted chat history and without double integration.

### P10 — full tests and independent audit

Run plugin/schema/hook/MCP/governance tests, compileall, security scan, clean
fixture canaries and A7 fresh-context audit. Inspect ZCode hook logs for hidden
failures. Zero HIGH/CRITICAL required.

### P11 — terminal closeout

Publish exact version/pins, plugin install instructions, test evidence, canary
transcripts/digests, recovery proof, limitations, workers/trees and terminal
verdict. No push/main merge without owner authority.

## 11. Gate matrix

| Gate | Requirement |
|---|---|
| Z3-G0 | supported ZCode capabilities remeasured |
| Z3-G1 | task/handoff/hook/MCP contract frozen |
| Z3-G2 | atomic state and recovery tests PASS |
| Z3-G3 | plugin agents/commands/skills load correctly |
| Z3-G4 | hooks enforce ownership/security/stop boundaries |
| Z3-G5 | read-only automatic return canary PASS |
| Z3-G6 | isolated implementation/integration canary PASS |
| Z3-G7 | reproduction/A7 and bad-handoff refusal PASS |
| Z3-G8 | restart recovery, zero duplicate integration |
| Z3-G9 | full battery and A7 zero HIGH/CRITICAL |
| Z3-G10 | terminal artifacts/workers/trees reconcile |

## 12. Terminal verdicts

- `ZCODE_ORCHESTRATION_V3_PASS_AUTONOMOUS_HANDOFF_CANARY`
- `ZCODE_ORCHESTRATION_V3_PASS_READONLY_ONLY`
- `ZCODE_ORCHESTRATION_V3_BLOCKED_ZCODE_CAPABILITY`
- `ZCODE_ORCHESTRATION_V3_BLOCKED_PLUGIN_TRUST_INSTALL`
- `ZCODE_ORCHESTRATION_V3_BLOCKED_RESOURCE_CONFLICT`
- `ZCODE_ORCHESTRATION_V3_FAIL_HANDOFF_INTEGRITY`
- `ZCODE_ORCHESTRATION_V3_FAIL_OWNERSHIP_ISOLATION`
- `ZCODE_ORCHESTRATION_V3_FAIL_RESTART_RECOVERY`
- `ZCODE_ORCHESTRATION_V3_INCOMPLETE_NOT_PROMOTABLE`

## 13. Hard boundaries

- No direct SQLite/session database writes or reverse-engineered task injection.
- No assumption that separate top-level ZCode threads can message each other.
- No nested subagent design; current ZCode subagents cannot spawn children.
- No chat prose treated as authoritative handoff.
- No plugin hook may call a model or grant authority.
- No full-access/yolo default for scheduled tasks.
- No unattended S1/scoring/GO/push/merge/live action.
- No secret in prompt, telemetry, task, handoff, hook log or Git.
- No cross-worktree edit or automatic conflict resolution.
- No infinite retry, polling or Stop-hook loop.
- No killing or stealing a foreign heavy worker.

## 14. Definition of done and expected benefit

Positive completion means:

- owner starts one Lead thread instead of relaying four threads;
- Lead directly dispatches all subagents;
- results return automatically to Lead;
- handoffs survive compaction/restart;
- dependency-ready tasks are dispatched without owner copy/paste;
- integration, reproduction and audit remain separated;
- only real authority blockers and terminal reports reach the owner.

Measured targets, not guaranteed claims:

```text
owner copy/paste handoffs             100% -> near 0%
manual agent-status checking          reduce 70-90%
orchestration/context tokens          reduce 20-40% after warmup
time between lane finish/next dispatch minutes-hours -> seconds/minutes
scientific safeguards                 unchanged or stronger
```

## 15. Fresh-session dispatch

```text
You are A1 Controller for ZCODE-ORCHESTRATION-V3. Read
plans/PLAN_zcode_orchestration_v3.md IN FULL, then CLAUDE.md,
HOW_TO_BE_A_LEAD_ENGINEER.md and current governance code. First remeasure the
installed ZCode version and every capability in plan section 1 using official
interfaces only. Produce P0 first report before implementation.

Build and test the official repository-owned plugin, atomic task/handoff MCP
service, AGENTS.md router, hooks, commands, skills and flat custom subagents.
Use fixture projects/worktrees for canaries. Prove background results return to
the primary Lead, invalid handoffs are refused, and a restarted session resumes
without pasted chat or duplicate integration. Do not touch active asset cycles,
internal ZCode databases, S1, scoring, credentials, providers, push/main merge
or live systems. Stop only for a true ZCode capability/plugin trust blocker or
terminal verdict.
```
