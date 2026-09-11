---
name: structured-handoff
description: "Validate and persist a zcode_orch_v3_handoff@1 artifact returned by a quant subagent: schema fields, git re-measurement, digest binding via the orchestrator MCP, and the refusal rules for invalid handoffs. Use whenever a dispatched subagent returns."
---

# Structured handoff (plan sec 3.3)

Schema `zcode_orch_v3_handoff@1` — required fields:

```text
task_id, cycle_id, role, lane
dispatch_sha, actual_start_sha      (both 40-hex; must be EQUAL or the
                                     handoff is INVALID, full stop)
commit_sha, changed_paths[]
tests[]: {command, exit_code, verdict PASS|FAIL|NOT_RUN, log_digest}
authority_claims[]                  (normally EMPTY for lane agents)
known_limitations[], incidents[]
tree_status, workers
outputs[]: {path, sha256}
recommended_next_action
```

## Validation procedure (Lead runs it, never the lane)

1. `orchestrator_validate_handoff` — store re-reads the artifact from disk;
   digest drift after publish is CONTROL_STATE_DRIFT.
2. Git, independently: commit exists at commit_sha; `git show --stat`
   changed paths all within the task's allowed_paths; tree clean.
3. Tests: re-run at least one targeted command OR verify the log digest.
   Missing evidence = NOT_RUN; it is never promoted to PASS.
4. `orchestrator_mark_integrated` ONLY after the pick lands and targeted
   gates pass; REJECTED/BLOCKED/TECHABORT via `orchestrator_record_blocker`
   with the reason.

## Refusal rules

- dispatch_sha != actual_start_sha -> REFUSED (tree drift mid-task).
- Any authority claim from a lane agent -> REFUSED (lanes have none).
- Missing handoff file after an Agent return -> HANDOFF_INVALID; never infer
  success from chat prose.
- One bad handoff does not fail the lane forever: fix the ROOT cause with a
  new attempt within max_attempts (new attempt record, old one preserved).
