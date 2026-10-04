# A7 PRELAUNCH AUDIT — ROUND 3 (DELTA) — NBA-WINPROB-SCORED-V1

Auditor: A7 (independent, adversarial, never repair). Date: 2026-10-04.
Scope: delta re-audit after freeze v3; verifies every round-2 blocker (C1, M1, M2, L1-L3)
is actually fixed in the shipped code and the as-frozen package. All measurements below
were re-executed by this audit on the live worktree; nothing is taken from prior reports.

## VERDICT (one line)

**A7_PRELAUNCH_AUTHORIZED** — conditional on exactly ONE controller action before launch:
update `a7_report_path` in `FREEZE_MANIFEST.json` from `AUDIT_PRELAUNCH_ROUND2.md` to
`AUDIT_PRELAUNCH_ROUND3.md` in a manifest-only, allowlisted commit (Finding F1, LOW-severity
pin, self-enforcing — see §1.4). 0 unresolved HIGH/CRITICAL. All round-2 blockers C1, M1,
M2, L1, L2, L3 verified FIXED with live measurements. No scored outcome exists; both launch
keys remain: this authorization (key 1, now satisfied modulo the pin) + owner typed GO
(key 2, must not exist yet — verified absent).

Launch state measured at HEAD `3c2731f1aee41f7711a301baa177ec9f307d3d4b`
(branch `orca/nba-winprob-scored-v1-integration`, clean tree at audit start).

---

## 1. C1 FIX — freeze v3 pin coverage — PASS (verified)

Round-2 C1 (CRITICAL): freeze v2 commit 227e3faa modified `nba_winprob/make_freeze_manifest.py`
relative to its own pinned sha — the generator sat outside its own snapshot, making the
package permanently unlaunchable. Freeze v3 claims to fix this by pinning 685f10ef, a commit
made BEFORE manifest generation. Re-measured:

### 1.1 The pinned sha contains both code files

`git ls-tree -r 685f10ef --name-only -- nba_winprob/` → 16 files including
`nba_winprob/run_evaluation.py` and `nba_winprob/make_freeze_manifest.py`.

### 1.2 Pinned blobs are byte-identical to HEAD (the code that will run)

```
nba_winprob/run_evaluation.py      pinned=b899c34b...  HEAD=b899c34b...  same=YES
nba_winprob/make_freeze_manifest.py pinned=754fb2a1...  HEAD=754fb2a1...  same=YES
```
The tree is clean (`git status --porcelain` empty at audit start), so working-tree code =
HEAD blobs = pinned blobs. The gate that will run at launch is the pinned gate.

### 1.3 Post-freeze drift is manifest-only and allowlisted

`git diff --name-only 685f10ef..HEAD` → exactly one path:
`research/control/NBA-WINPROB-SCORED-V1/FREEZE_MANIFEST.json` (+5/−4 lines). This is inside
the manifest's `post_freeze_allowlist` entry `research/control/NBA-WINPROB-SCORED-V1/**`
and outside `nba_winprob/`. No other file changed. The commit that created the manifest
(3c2731f1) changed nothing else (`--stat`: 1 file changed).

### 1.4 The manifest-only pin question (this round's key structural check)

The manifest's `a7_report_path` still names `.../audits/AUDIT_PRELAUNCH_ROUND2.md`
(FREEZE_MANIFEST.json line 16). ROUND2 exists but is a REFUSAL document
(`AUDIT_PRELAUNCH_ROUND2.md` line 3: "VERDICT: A7_PRELAUNCH_BLOCKED — REFUSED") and
deliberately carries zero occurrences of the authorization token (r2 L6 grep-verified;
re-verified this round). The shipped gate therefore refuses at launch with exactly one
reason — **this is CORRECT fail-safe behavior** (a refusal document must never satisfy the
A7 gate), and requires the controller to update the pin. Evaluated:

- The required update edits ONLY `FREEZE_MANIFEST.json` — a path covered by the
  `post_freeze_allowlist` (`research/control/NBA-WINPROB-SCORED-V1/**`), with zero
  `nba_winprob/` change. Live measurement already demonstrates this shape passes the drift
  gates: the end-to-end gate run in §4 executed against the current
  manifest-only-delta state (685f10ef..HEAD) and produced **zero** drift reasons.
- **Conclusion: the manifest update alone keeps C1 fixed.** The condition is
  self-enforcing by the shipped gate itself: pin at ROUND2 → gate refuses (refusal token
  absent, correct); pin at ROUND3 (this file carries the authorization token, §4/§6) →
  gate passes. No code change is involved or permitted in the same action.

### 1.5 Supersedes chain integrity

- Manifest `supersedes.code_freeze_sha` = `2c64b6f3...` (freeze v2) and
  `older_freeze` = `39b11156` (v1, `FREEZE_MANIFEST.SUPERSEDED_BLOCKED.json`, whose own
  `code_freeze_sha` = 39b11156...).
- Ancestry measured: `2c64b6f3` IS an ancestor of `685f10ef`; `39b11156` IS an ancestor of
  `2c64b6f3`. Chain v1 → v2 → v3 is linear and honest; the v3 `supersedes.reason` names the
  v2 generator defect (C1) + M1/M2 + L1-L3 accurately.
- Manifest schema `nba_winprob_scored_freeze@2` (runner requires exactly this: line 286).

---

## 2. M1/M2 FIX — verdict semantics — PASS (verbatim quotes)

Round-2 M1/M2 (MEDIUM): H1 REJECT carried an extra OR term; INCONCLUSIVE was broader than
protocol sec6. Both re-read in the shipped `nba_winprob/run_evaluation.py` (blob b899c34b,
identical at 685f10ef and HEAD).

### 2.1 M1 — H1 REJECT is now exactly the registered rule

Code, lines 229-234:

```python
    verdicts["hypotheses"] = {
        "H1_dynamic_strength": {
            "rule": "REJECT iff all four 95% CIs of pooled DL(B1-arm, B0) include 0 or lie entirely > 0",
            "REJECT": all(not arm_favors(f"{a}_vs_B0") for a in B1_ARMS),
```

Required: `all(not favors(a_vs_B0) for a in B1_ARMS)` — **exact match**. `B1_ARMS` is
line 42: `[a.arm_id for a in ARMS if a.kind == "B1"]` (4 arms: B1-a/b/c/d, identity
verified against protocol.py and the manifest in §5.2). `arm_favors` (line 188-189) is
`ci(key)["ci95_hi"] < 0`, so `not arm_favors` = CI includes 0 or lies entirely > 0 —
precisely protocol sec1 line 20: "Falsification rule: H1 REJECT iff all four 95% CIs of
pooled ΔLL(B1-arm, B0) include 0 or lie entirely > 0". The pre-fix defect is gone; delta
diff (227e3faa..HEAD) shows the deleted line was:

```
-            "REJECT": all(not arm_favors(f"{a}_vs_B0") for a in B1_ARMS if a == b1star) or
-                      all(not arm_favors(f"{a}_vs_B0") for a in B1_ARMS),
```

### 2.2 M2 — INCONCLUSIVE is now exactly sec6

Code, lines 223-228:

```python
    decisive = [k for k in comparisons["pooled"] if arm_favors(k) or ref_favors(k)]
    decision_keys = list(comparisons["pooled"].keys())
    all_cis_include_zero = all(not (arm_favors(k) or ref_favors(k)) for k in decision_keys)
    verdicts["INCONCLUSIVE"] = (all_cis_include_zero
                                and 0.85 <= slope_b2a <= 1.15
                                and not verdicts["PROGRAM_PASS"])
```

Required: (all decision CIs include 0) AND T2 holds AND not PASS.
- "all decision CIs include 0": iterated over ALL 11 pooled registered comparisons;
  `not (arm_favors or ref_favors)` = CI includes 0 (neither side's 95% CI excludes 0).
- "T2 holds": `0.85 <= slope_b2a <= 1.15` — character-for-character the same predicate as
  T2's PASS at line 209 (`"PASS": 0.85 <= slope_b2a <= 1.15`). Written as the literal band
  expression rather than a dict reference — semantically identical (Finding F3,
  informational only).
- "not PASS": `not verdicts["PROGRAM_PASS"]`.
Matches protocol sec6 line 114 verbatim: "INCONCLUSIVE: all decision CIs include 0 while
T2 holds → no PASS". Delta diff confirms the old defect
(`INCONCLUSIVE = not PROGRAM_PASS and not REJECT.ANY`) was removed.

---

## 3. L1/L2/L3 FIX — gate hardening — PASS (quoted + measured)

Round-2 L1/L2/L3 (LOW group, elevated to launch-relevant): ledger override bypass, silent
skip of missing data files, truthiness-only `typed_at`. All three re-read AND re-executed
against the shipped gate.

### 3.1 L1 — `--ledger` divergence refused before any effect

Code, `main()` lines 439-442 (executed BEFORE `check_launch_gates` and before any write):

```python
    ledger = m.get("ledger_path")
    if args.ledger and os.path.abspath(args.ledger) != os.path.abspath(ledger):
        print(f"REFUSED — --ledger {args.ledger} != pinned {ledger}", file=sys.stderr)
        return 3
```

Measured: `--ledger /tmp/a7r3_rogue_ledger.jsonl` → stderr
`REFUSED — --ledger /tmp/a7r3_rogue_ledger.jsonl != pinned .../TRIAL_LEDGER.jsonl`,
exit code **3**, nothing written (rogue file never created).

### 3.2 L2 — missing pinned/data files are refusal reasons, never silent skips

Code, `check_launch_gates` lines 297-304:

```python
        for name, p in (("games", pin_g), ("features", pin_f)):
            if not os.path.exists(p):
                reasons.append(f"pinned {name} missing: {p}")
    for name, meta in m.get("data", {}).items():
        if not os.path.exists(meta["path"]):
            reasons.append(f"data missing: {name} {meta['path']}")
        elif _sha256_file(meta["path"]) != meta["sha256"]:
            reasons.append(f"data hash mismatch: {name}")
```

Measured (synthetic /tmp manifests, schema-valid):
- `data.games.path` → nonexistent → reason `data missing: games /tmp/a7r3_nonexistent_games.csv`.
- `pinned_games` → nonexistent → reason `pinned games missing: /tmp/a7r3_nonexistent_games.csv`.

### 3.3 L3 — `typed_at` ISO-8601 parsed, not just truthy

Code, lines 349-355:

```python
            if not rec.get("typed_at"):
                reasons.append("GO record missing typed_at")
            else:
                try:
                    dt.datetime.fromisoformat(str(rec["typed_at"]).replace("Z", "+00:00"))
                except ValueError:
                    reasons.append("GO record typed_at not ISO-8601")
```

Measured:
- `typed_at: "October 4th 2026"` → reason `GO record typed_at not ISO-8601`.
- `typed_at` absent → reason `GO record missing typed_at`.
- `typed_at: "2026-10-04T21:00:00+00:00"` (valid) → no reason.

Bonus re-verification (wrong phrase): `phrase: "GO NOW"` → reason
`GO record phrase mismatch` (exit-3 refusal path confirmed).

---

## 4. Launch gate, end-to-end, with a syntactically valid GO record — measured

A valid structured GO record was written to `/tmp/a7r3_go_valid.json`
(`phrase` = exact registered phrase, `cycle_id`, `typed_by: "owner"`, `typed_at` ISO) and the
real manifest + real worktree + shipped `check_launch_gates` were executed live
(lock state `FREE_PROVEN` confirmed immediately prior via `researchctl.py locks inspect`):

```
ok: False
REASON: A7 report does not carry A7_PRELAUNCH_AUTHORIZED
```

**The ONLY remaining reason is the by-design A7-artifact reason** — and it fires because the
manifest pin names the ROUND2 REFUSAL document (§1.4). Every other gate dimension passed
live: manifest schema/cycle, pinned path equality, existence + sha256 of all 5 pinned data
files, no code drift, no allowlist breach, clean tree, FREE lock, and full GO-record
validation (phrase / cycle / owner / ISO typed_at). This is the single required controller
action of Finding F1; once the pin names this file (which carries the token, §6), the gate
is expected to pass with an owner GO present at launch.

---

## 5. Regression suite — PASS (all measured)

### 5.1 Tests and selftest
- `pytest nba_winprob/tests/ -q` → **33 passed** in 55.91s (0 failed, 0 skipped).
- `run_evaluation --synthetic-selftest` → `SELFTEST PASS v2: 9 arms, 7 comparisons
  (pooled+per-fold), verdicts emitted, fold reliability/slope present, bootstrap
  deterministic; no real data touched.` (banner wording carried over — Finding F2, cosmetic).

### 5.2 Identity — manifest ↔ protocol.py ↔ runner
Programmatic comparison: manifest 9-arm table == `protocol.ARMS` (arm_id/kind/K/HCA/features
tuples exact) → True; manifest `registered_comparisons` == runner `REGISTERED_COMPARISONS`
(11 pairs, incl. the 4× B1-vs-B0 demanded by H1) → True; manifest `go_phrase` == runner
`GO_PHRASE` → True.

### 5.3 Pinned data recompute (independent shasum, not via the gate)
```
c86f104d9c30a67f4735592d31308dab3c95d55998d80d51822d2679e50fc86b  features.csv  == manifest
e24d9a3b1feb5f9e5b0408c1e0c93d34c2137f174788667dd082754ec636f098  games.csv     == manifest
d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc  nbaallelo.csv == manifest
```
Protocol digest recomputed: `c058760d...a451f7` == manifest `protocol_digest` (path
`lanes/C_protocol/PROTOCOL_EVAL.md`, exists). Amendment digest recomputed:
`e7531c7e...3e53bc` == manifest `amendment_digest`.

### 5.4 Ledger discipline
`TRIAL_LEDGER.jsonl`: exactly 9 rows, all `status: PREREGISTERED`, `observed: false`,
class PRIMARY, 9 distinct arm_ids (B0, B1-a..d, B2-a..d), zero `COMPUTED`, zero metric
fields. First row verbatim:
`{"schema": "nba_winprob_trial_ledger@1", "cycle_id": "NBA-WINPROB-SCORED-V1", "arm_id": "B0", "status": "PREREGISTERED", "observed": false, "class": "PRIMARY", "registered_at_utc": "2026-10-04T12:09:43Z", "spec": {"K": null, "HCA": null, "features": []}}`

### 5.5 No real-outcome metric anywhere
- `results/` dir exists and is EMPTY (0 files).
- Repo-wide `find -name scored_summary.json` (excluding .git) → 0 hits.
- No GO record exists for this cycle: zero files under
  `research/control/NBA-WINPROB-SCORED-V1/` matching GO-record patterns; the phrase appears
  only inside the two manifests and audit prose (REGISTERED_NOT_CONSUMED).
- Registry (`researchctl.py cycle list`): `NBA-WINPROB-SCORED-V1 ACTIVE_LIGHT 0/9` on
  `orca/nba-winprob-scored-v1-integration` — budget consumed 0 of 9.

### 5.6 Round-2 artifact flow
E2 round-2 (DELTA PASS, C1 launch-blocking finding) and A7 round-2 (REFUSED) reports are
landed at `lanes/E2_data_freeze/E2_REPORT_ROUND2.md` + `audits/AUDIT_PRELAUNCH_ROUND2.md`
(commit a70980c7), as the freeze v3 reason line claims.

---

## 6. Findings

| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| F1 | LOW (pin) / launch-relevant | `a7_report_path` (manifest line 16) pins `AUDIT_PRELAUNCH_ROUND2.md` — a REFUSAL document with zero occurrences of the authorization token. The shipped gate refuses at launch with exactly `A7 report does not carry A7_PRELAUNCH_AUTHORIZED`. This is CORRECT fail-safe behavior, not a gate defect; the round-3 file cannot retroactively become the pinned token without a controller manifest action. | **Required action (the verdict's single condition):** controller updates `a7_report_path` → `.../audits/AUDIT_PRELAUNCH_ROUND3.md` in a manifest-only commit (allowlist-covered; no `nba_winprob/` change → C1 remains fixed, per live measurement §1.4). Self-enforcing: until the pin moves, the gate refuses; once it moves, this file's token satisfies the gate. Controller must re-run the gate after the pin commit. |
| F2 | LOW (cosmetic, carried from r2-L4) | Selftest banner still reads "7 comparisons" while 11 pooled comparisons are computed (line 431). Banner text only; assertions in the same function check 11 (`assert ... == 11` semantics via pooled count == 11 at line 384). | No action required for launch; fix at leisure post-launch. |
| F3 | LOW (informational) | INCONCLUSIVE expresses "T2 holds" as the literal band `0.85 <= slope_b2a <= 1.15` (line 227) instead of referencing `verdicts["T2_calibration"]["PASS"]`. Byte-identical predicate to line 209; zero semantic divergence. | No action; noted so future T2 edits remember to change both sites. |
| F4 | LOW (informational, carried) | A7-artifact gate is a substring match for the token (r2-L6); owner identity rests on `typed_by` + mission law (no crypto auth). Accepted two-key design; this file deliberately carries the token only in combination with the F1 condition. | No action. |

No HIGH or CRITICAL findings. No new MEDIUM findings.

## 7. Required actions (exhaustive, in order)

1. **Controller (allowlisted, manifest-only):** edit `research/control/NBA-WINPROB-SCORED-V1/FREEZE_MANIFEST.json` line 16: `a7_report_path` → `.../audits/AUDIT_PRELAUNCH_ROUND3.md`. Commit touches NO other file (this audit's 2 files may land in the same or a preceding control-path commit; nothing outside `research/control/NBA-WINPROB-SCORED-V1/**`). Re-run the launch gate post-commit.
2. **Owner (key 2):** type `GO NBA WINPROB SCORED V1 EVALUATION` as a structured record at this cycle's own gate, only after action 1.
3. Launch may then proceed; every other gate dimension is measured PASS at HEAD 3c2731f1.

## 8. Verdict

**A7_PRELAUNCH_AUTHORIZED** — 0 unresolved HIGH/CRITICAL, conditional solely on the F1
manifest-pin action above (mechanically enforced by the shipped gate itself). All round-2
blockers (C1 CRITICAL; M1, M2 MEDIUM; L1, L2, L3) verified fixed in shipped code by direct
quote + live adversarial execution; regression suite 33/33 + selftest PASS; ledger 9
PREREGISTERED / 0 COMPUTED; budget 0/9; no scored outcome exists anywhere; no GO record
exists. Authorization is key one of two: scored execution remains impossible until the
owner types the registered phrase at this cycle's own gate.
