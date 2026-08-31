# Worktree manifest contract

Each lane record must contain:

```text
role, path, branch, bootstrap_sha, allowed_globs, forbidden_globs,
expected_deliverables, commit_sha, targeted_test_command, test_result,
status, merge_order, delegation_allowed
```

Use absolute paths and full 40-character SHAs. All unspecified files are
read-only. Record `commit_sha` only after the lane returns a clean commit.

Dispatch packet:

```text
ROLE: <role>
WORKTREE: <absolute path>
BRANCH: <branch or DETACHED>
BOOTSTRAP_SHA: <40-character SHA>
READ_FIRST: <plan and authority files>
ALLOWED_GLOBS: <exact list>
FORBIDDEN_GLOBS: <exact list>
DELIVERABLES: <exact list>
TARGETED_TEST: <exact command>
MERGE_ORDER: <integer>
FORBIDDEN_ACTIONS: merge, rebase, push, reset, delete, S1, unassigned files
FIRST_ACTION: print pwd, HEAD, branch, porcelain; stop on mismatch
```
