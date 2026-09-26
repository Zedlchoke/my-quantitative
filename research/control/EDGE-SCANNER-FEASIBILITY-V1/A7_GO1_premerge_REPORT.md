# A7 PRE-MERGE REVIEW — EDGE-SCANNER-TOOLING-V1 GO-1 (fresh context)

Filed by Lead verbatim from the independent A7 reviewer lane's verdict
(2026-09-26; the reviewer did not implement the change and wrote no files —
this file is the Lead's transcription of its review artifact).

Object: worktree `.worktrees/edge-scanner-tooling-v1/integration`, branch
`orca/edge-scanner-tooling-v1-integration`, commit `938e80e3c3e16f47d00d559ef0c6ed46d4cd0c9b`
(parent `c9956ac7` = main HEAD). Upstream pin verified `c927dcb0c5e8122269812d2cdfdc4a3ae71b2ab3`.

## D1 BYTE-FIDELITY — PASS
`shasum -a 256` upstream @ pin vs vendored, all three identical:
- `local_guard.py` = `4418a2e1c50e2b7be642bf5c2d2f3745bee81f34378d637332bdeef91f88b762` (both sides)
- `LICENSE` = `5d44f49c87f1a8e86d5e423293fba1b077d611e055e63a5ddf1e7666f56e28e3` (both sides)
- `NOTICE` = `d84c264d4623e6c2d27ac14a0007470786ecb2b964b7c4813863731fd1a0d133` (both sides)
- `diff upstream/scanner/local_guard.py <vendored>` → empty. VENDOR_PIN.md's recorded digests match all three computed values exactly.

## D2 SCOPE CONTAINMENT — PASS
`git diff --name-status` = exactly 10 files, all status `A` (pure additive):
3 vendored + 2 manifests + 5 test-package files. `git ls-tree -r HEAD
research/platform_tools/thirdparty/edge-scanner` = exactly 5 tracked files;
on-disk `__pycache__/` untracked and gitignored. Non-goals keyword grep over
the full diff: all hits are (a) verbatim upstream NOTICE attribution text,
(b) manifest sentences stating "NOT vendored here", (c) the upstream test-case
name `test_dashboard_and_scripts_still_write` (a guard case, not dashboard
code). No trigger catalog, stops, size_hint, score, gates constants,
providers, dashboard-v2, or plugin code anywhere.

## D3 TESTS-TEST-THE-VENDORED-CODE — PASS
(a) conftest.py inserts the vendored dir at `sys.path[0]`. (b) Counterfactual
session: `local_guard.__file__` resolves into the worktree vendored dir;
`find` over worktree and `.venv/lib` found no other `local_guard.py` — no
shadow copy, so pytest necessarily exercised the vendored bytes. (c)
Non-vacuousness probe (in-process, no files edited): unpatched guard gives
evil-Origin POST → 403, rebind Host → 400, text/plain POST → 415, loopback →
passthrough; with `origin_allowed` monkeypatched to always-True in memory the
evil-Origin JSON POST flips to 200/app-called — the fidelity asserts would
FAIL. The tests discriminate.

## D4 FIDELITY COVERAGE vs UPSTREAM — PASS
Upstream `tests/test_local_guard.py` has 8 cases exercising local_guard; all
8 ported name-for-name with identical header matrices and outcomes: (1)
foreign-origin POST 403 ×3 sub-cases; (2) post-must-be-json 415 ×4 params;
(3) dashboard/scripts write 4 origins; (4) vite preflight OPTIONS pass;
(5) rebound hostname 400 ×4 method/path params; (6) loopback names ×4;
(7) LAN allow_hosts + wildcard + SCANNER_ALLOWED_HOSTS comma list; (8)
foreign websocket close 1008 ×2 params. Excluded per plan §0 and honestly
documented in the port docstring: upstream static-route UNC tests
(`_safe_static_path`/`mount_v2_static`) — no local_guard-relevant upstream
case dropped. Port is strictly stronger (adds app-not-called and error-body
asserts); no false-pass path (passthrough cases require `called=True`).

## D5 TEST RUN — PASS
`.venv/bin/python -m pytest <worktree>/tests/platform_tools/thirdparty -q` →
**23 passed in 0.23s** (matches commit message). No-egress non-vacuity:
`pytest.raises(AssertionError)` sanity on `socket.create_connection` — if the
denial silently failed to arm, a `ConnectionRefusedError` (not AssertionError)
would fail the test. Vacuous pass structurally impossible. Locks FREE_PROVEN.

## D6 ENVIRONMENT CHANGE DISCLOSURE — PASS
`pip list`: starlette 1.7.0, anyio 4.15.1 — exactly the disclosed versions;
no other venv package depends on either (grep over dist-info METADATA: zero
dependents) — consistent with additive-only. Vendored module's external
imports via AST: only `starlette.responses`. Disclosure present in both the
commit message and THIRD_PARTY_NOTICES.md.

## D7 NO-EGRESS PERMANENCE — PASS
`no_sockets` fixture denies `socket.socket.connect`, `connect_ex`,
`socket.create_connection`; import test pops `sys.modules` and fresh-imports
under denial; matrix test drives 8 cases covering every guard branch under
denial (403/415/400 + POST/GET/OPTIONS passes + WS close + WS pass); plus a
static import-scan test. Two informational nits (non-blocking): static scan's
banned-substring list would miss `from http import client` (runtime denial
still catches any connect); lifespan branch exercised only in the fidelity
battery, not under denial.

## FINDINGS (none in the commit; all process/documentation)
1. **MEDIUM** — Plan §5 step 5 implementer handoff JSON absent from
   `research/control/EDGE-SCANNER-FEASIBILITY-V1/`.
2. **MEDIUM** — Plan §3 GO-1 begins with "register cycle qua researchctl";
   no EDGE-SCANNER-TOOLING-V1 row existed at review time.
3. **LOW** — `VENDOR_PIN.md:8` cites `plans/PLAN_edge_scanner_tooling_v1.md`,
   which did not exist at review time (actual then:
   `plans/DRAFT_EDGE-SCANNER-TOOLING-V1.md`); manifest doc-reference only,
   does not touch vendored bytes, re-pin law not triggered.

## VERDICT (as issued): REMEDIATION_REQUIRED —
"The vendored code, scope containment, test fidelity, no-egress enforcement,
and byte fidelity are all clean — D1 through D7 PASS with zero defects in the
commit itself. GO-1 cannot be recorded as complete yet solely because two
plan-mandated authority artifacts are absent from the evidence trail" (the
handoff JSON and the registration; plus the optional filename fix).

## LEAD REMEDIATION RECORD (same session, after the review)
- Finding 1 → `HANDOFF_edge_scanner_tooling_vendor.json` filed.
- Finding 2 → cycle registered via `researchctl cycle register` (see
  `plans/CYCLE_REGISTRY.json` row EDGE-SCANNER-TOOLING-V1 and `GO1_RECORDED.json`).
- Finding 3 → plan renamed to `plans/PLAN_edge_scanner_tooling_v1.md`
  (workspace PLAN_ convention), making `VENDOR_PIN.md:8`'s reference correct
  with zero change to the worktree commit.
- No code or test changes were made post-review; worktree commit remains
  `938e80e3`.

Post-remediation state: **GO-1 recorded COMPLETE; cycle STOPPED before GO-2.**
