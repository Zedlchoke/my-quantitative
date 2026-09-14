# quant-research-orchestrator — install instructions (P5)

Repository-owned ZCode plugin for ZCODE-ORCHESTRATION-V3
(plans/PLAN_zcode_orchestration_v3.md). It bundles four flat subagents, four
Lead commands, three skills, four hooks and one local stdio MCP server that
wraps the repository governance modules. It coordinates; it never scores,
never calls a model, never pushes.

Version 0.1.2 explicitly pins all four subagent roles to
`builtin:zai-coding-plan/GLM-5.3-Flash` with `thoughtLevel: high`. ZCode
snapshots agent configuration at session start, so reinstall/update the plugin
and start a new Lead session before expecting the pin to take effect.

## Sequencing (constraint C1 — measure, don't skip)

The plugin's `mcpServers` command and every hook command use CANONICAL
absolute paths into the main checkout
(`/Users/hoangminhlong/my-quantitative/plugins/...`). Therefore:

1. The integration branch
   `orca/zcode-orchestration-v3-integration` must first be merged to `main`
   (owner authority — merge to main is never self-authorized).
2. Only after the merge do the referenced paths exist at their canonical
   locations.

## Install (the plan's single P5 owner action)

1. Open ZCode Settings > Plugins.
2. Create > Add marketplace > point it at
   `/Users/hoangminhlong/my-quantitative/plugins` (local directory; ZCode
   validates `marketplace.json` before adding).
3. Install `quant-research-orchestrator` from the Personal tab. Newly
   installed plugins are enabled by default — enabling IS the code-execution
   trust decision. Review `hooks/hooks.json` and `scripts/` first; all code
   is repository code and auditable in Git.
4. START A NEW SESSION afterwards (hook/plugin/MCP config is snapshotted at
   session start; a running session never hot-reloads).
5. In the new Lead session run `/lead-start` (command) and follow the
   controller-loop skill. The `orchestrator` MCP tools become available to
   that session.

There is no headless install path (no `zcode` CLI binary on this machine);
hand-editing `~/.zcode/cli/plugins/installed_plugins.json` or config.json is
undocumented internal-state manipulation and is forbidden by the plan.

## What enabling grants (read before enabling)

- Hooks execute local Python subprocesses on SessionStart / PreToolUse /
  PostToolUse / Stop with strict timeouts. They are read-only guards except
  that they can DENY tool calls and request bounded Stop continuation (max 3,
  self-capped).
- The MCP server (`scripts/mcp_server.py`) reads/writes ONLY
  `.runtime/orchestrator_v3/` (gitignored) and reads the canonical registry.
- Nothing here scores, trades, pushes, merges or opens S1.
