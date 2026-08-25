# A7 Adversarial Challenge Protocol — V6P (frozen before execution)

- **Author:** A7 independent scientific auditor (read-only outside `research/audits/v6p/`)
- **Repo:** `/Users/hoangminhlong/my-quantitative`
- **Frozen:** 2026-08-24, before any V6P validation worker launch
- **Scope:** PLAN.md §1.2 findings N01–N15, §5, §6.5, §7 gates V6P-C01..C20, §15 controller contract
- **Rule:** A7 never repairs implementation or touches results. Missing evidence is
  FAIL/BLOCKED/NOT_TESTED, never PASS (PLAN §2 rule 10). All commands use
  `.venv/bin/python`. Every check below was designed against the actual current
  evidence: `research/audits/v5r/new_lineage_baseline.json` still contains
  `"verified_by": "PENDING_A6"`; all four `results/diagnostic_v5r/*/launch_manifest.yaml`
  record `dirty_worktree_at_launch: true`; the v5r reconciliation artifact records
  `registry_append_only_verified: false` and its report declares
  `stage_a_root: results/portfolio_v4`; v5r reproduction compares only orders/positions
  digests + pnl/mdd/beta/turnover. These are historical facts preserved as-is; V6P must
  prove the repaired behavior in fresh namespaces.

**Total protocol items: 40** (A:5 pre-launch, B:15 per-finding, C:10 post-freeze,
D:6 verdict/independence, E:4 sampling policy).

---

## A. Pre-launch verification (run before ANY V6P validation worker)

All five items must individually PASS before any worker command is issued. Any
single failure aborts launch (fail-closed), mirroring
`validate_launch_provenance` in `research/provenance_v6p.py:140` and the runner
preflight at `research/portfolio_runner.py:1763`.

### P-A-1 Clean tree
Command:
```bash
git -C /Users/hoangminhlong/my-quantitative status --porcelain=v1
```
Pass criterion: output is empty at audit time AND each V6P
`launch_manifest.yaml` records `dirty_worktree_at_launch: false`. Contrast
(N02): all four v5r manifests record `true`; those are immutable history.

### P-A-2 HEAD equals frozen baseline head
Commands:
```bash
git rev-parse HEAD
.venv/bin/python -c "import json;print(json.load(open('research/audits/v6p/baseline_root.json'))['launch_head'])"
```
Pass criterion: both SHA strings identical; additionally
`baseline_root.json.worktree_clean == true` and every V6P manifest's
`git_commit_at_launch == baseline_root.json.launch_head`.
Gate substantiated: **V6P-C04** (also C02).

### P-A-3 External root has NO self-referential hash key (N03)
Command:
```bash
.venv/bin/python - <<'EOF'
import json, re
from pathlib import Path
from research.provenance_v6p import baseline_self_hash_violations
p = Path("research/audits/v6p/baseline_root.json")
b = json.loads(p.read_bytes())
print("validator:", baseline_self_hash_violations(b, p.read_bytes()))
bad = [k for k in json.dumps(b).split('"') if re.fullmatch(r"(?i)(self_?hash.*|.*self.*hash.*|baseline_sha256|manifest_sha256|own_sha256)", k)]
print("regex_hits:", sorted(set(bad)))
EOF
```
Pass criterion: validator returns `[]` and regex hits are empty — no key inside
the baseline declares itself as the hash of this document (external-root design;
`created_at_utc` is the single freeze timestamp; attestation stamps live in the
separate attestation file). Historical contrast recorded: the v5r baseline lists
its own path+hash inside `source_spec_data_contract_hashes`, which can never
match its own bytes.
Gate: **V6P-C02**.

### P-A-4 Attestation PASS with matching hashes
Command:
```bash
.venv/bin/python - <<'EOF'
import json, hashlib
from pathlib import Path
base = Path("research/audits/v6p/baseline_root.json").read_bytes()
att = json.loads(Path("research/audits/v6p/a7_prelaunch_attestation.json").read_text())
d = hashlib.sha256(base).hexdigest()
print(att["verdict"], att["baseline_sha256"] == d)
EOF
```
Pass criterion: `verdict == "PASS"`; every `checks` value true;
`attestation.baseline_sha256 == sha256(baseline_root.json bytes)` recomputed
here independently; `baseline_root.attestation.sha256_at_freeze` is null or
equal to that digest; the attestation references the baseline by hash only.
Gate: **V6P-C03**.

### P-A-5 Attestation strictly precedes EVERY launch start
Command (A7-independent; stricter than the shipped validator, which compares
only baseline creation to one timestamp):
```bash
.venv/bin/python - <<'EOF'
import json, glob
from datetime import datetime
att = datetime.fromisoformat(json.load(open("research/audits/v6p/a7_prelaunch_attestation.json"))["audited_at_utc"])
cre = datetime.fromisoformat(json.load(open("research/audits/v6p/baseline_root.json"))["created_at_utc"])
starts = []
for m in sorted(glob.glob("results/validation_v6p/*/launch_manifest.yaml")):
    for line in open(m):
        if line.startswith(("run_started_utc", "backtest_run_started_utc", "started_at_utc")):
            starts.append((m, datetime.fromisoformat(line.split(":",1)[1].strip().strip("'\""))))
            break
print(min(s[1] for s in starts) if starts else "NO_STARTS_FOUND",
      "att_ok:", all(att < s[1] for s in starts),
      "created_ok:", all(cre < s[1] for s in starts))
EOF
```
Pass criterion: `att_ok == True` and `created_ok == True` — both baseline freeze
timestamp and attestation `audited_at_utc` are strictly BEFORE every validation
launch start (no post-launch baseline creation, no retroactive attestation).
Gate: **V6P-C03** (+C04).

---

## B. Per-finding challenge N01–N15 → exact check → pass criterion → gate

Each row: finding, exact command/script check, pass criterion, gate(s) it
substantiates. All 15 findings are tested explicitly (N13 forbids sample-only
audit).

### P-B-1 — N01 (CRITICAL): baseline attestation pending / R04 overclaim
Check:
```bash
.venv/bin/python - <<'EOF'
import json, hashlib
old = json.load(open("research/audits/v5r/new_lineage_baseline.json"))
print("v5r_slot_untouched:", old["a6_pre_launch_verification"]["verified_by"] == "PENDING_A6")
new = json.load(open("research/audits/v6p/baseline_root.json"))
att = json.load(open("research/audits/v6p/a7_prelaunch_attestation.json"))
print("no_pending_in_new:", all(v != "PENDING" for v in
      [str(new.get("attestation")), att["verdict"]]))
add = open("research/audits/v6p/v5r_reaudit_addendum.md").read()
print("n01_recorded:", "N01" in add)
EOF
```
Pass criterion: v5r baseline slot remains untouched (`PENDING_A6` preserved as
immutable history); NEW v6p baseline carries no pending verifier slot; committed
A7 attestation exists with verdict PASS (per P-A-4); addendum records N01.
Gates: **C03** primary, **C01** (addendum completeness).

### P-B-2 — N02 (CRITICAL): dirty worktree at launch
Check:
```bash
.venv/bin/python - <<'EOF'
import glob
for m in sorted(glob.glob("results/validation_v6p/*/launch_manifest.yaml")):
    dirty = head = None
    for line in open(m):
        if line.startswith("dirty_worktree_at_launch:"): dirty = line.split(":")[1].strip()
        if line.startswith("git_commit_at_launch:"): head = line.split(":")[1].strip()
    print(m, dirty, head)
EOF
```
Pass criterion: `dirty == "false"` for ALL V6P manifests and
`git_commit_at_launch == baseline.launch_head` for all; zero exceptions.
Historical v5r manifests keep `true` (unchanged).
Gate: **C04**.

### P-B-3 — N03 (HIGH→verified): self-referential baseline hash
Check: exactly P-A-3 (validator + regex on `baseline_root.json`).
Pass criterion: no self-referential hash key; external-root design holds;
negative test exists proving detection (tests covering
`baseline_self_hash_violations` return non-empty on a planted self-hash key).
Gate: **C02**.

### P-B-4 — N04 (CRITICAL): reset-fold outer curve
Check (semantic identity from reconciler AND ledger; field names adapted to the
actual `schema_version` present, semantics mandatory):
```bash
.venv/bin/python - <<'EOF'
import json, glob
for e in sorted(glob.glob("results/validation_v6p/*/")):
    r = json.load(open(e + "accounting_reconciliation.json"))
    f = r["folds"]
    chain = all(abs(f[i]["ending_equity"] - f[i+1]["starting_equity"]) <= 1e-6
                for i in range(len(f)-1))
    print(e, "fold_chain:", chain, "reset_folds:", r.get("reset_folds", "MISSING"))
EOF
```
Plus ledger cross-check per experiment: first equity observation of fold k ==
last equity observation of fold k−1 in `portfolio_ledger.jsonl`.
Pass criterion: `reset_folds=false`; F2 start == F1 end, F3 start == F2 end
(within $1e-6); engine invoked once per experiment (single chronological
timeline evidenced in run.log); MDD recomputed from the continuous equity path
matches `canonical_metrics.json` within 1e-9 relative.
Gates: **C09**, **C10**.

### P-B-5 — N05 (CRITICAL): risk mode inactive / gross >1.00
Check (full census, see P-E-1):
```bash
.venv/bin/python - <<'EOF'
import json, glob
for e in sorted(glob.glob("results/validation_v6p/*/")):
    rows = [json.loads(l) for l in open(e+"exposure_control.jsonl")]
    modes = {r.get("risk_mode") for r in rows}
    viol = [r for r in rows if r.get("gross_exposure", 0) > 1.00 + 1e-9
            or abs(r.get("net_exposure", 0)) > 0.10 + 1e-9]
    print(e, "rows:", len(rows), "modes:", modes, "violations_after_action:", len(viol))
EOF
```
Pass criterion: every row shows `risk_mode == "RISK_MODE_V1"` active; zero rows
with gross >1.00, |net| >0.10, or |symbol weight| > declared cap after
reduce-only action; max gross recomputed from `portfolio_ledger.jsonl` ≤1.00
(the 39%-of-bars / 1.2746 pattern of N05 must be absent).
Gate: **C12**.

### P-B-6 — N06 (CRITICAL): missing settlement/accounting artifacts
Check:
```bash
for d in results/validation_v6p/*/; do
  for f in funding_cashflows.jsonl accounting_reconciliation.json \
           commission_slippage.json terminal_positions.jsonl exposure_control.jsonl; do
    test -s "$d$f" || echo "MISSING_OR_EMPTY: $d$f";
  done;
done; echo "artifact presence scan done"
```
Pass criterion: no `MISSING_OR_EMPTY` lines across all three validation roots
(each file exists, size >0, parses). Terminal rows reconcile to closed legs and
leave a flat final book.
Gate: **C11**.

### P-B-7 — N07 (CRITICAL): hand-built XG1 booleans
Check:
```bash
grep -n "execution_ledger_rows\|evaluate_xg1_measured" research/portfolio_runner.py research/protocol/gates.py | head -20
.venv/bin/python - <<'EOF'
import json, glob
for g in sorted(glob.glob("results/validation_v6p/*/gate_result.json")):
    d = json.load(open(g))
    xg1 = next(x for x in d["gates"] if str(x.get("gate","")).startswith("XG1"))
    print(g, xg1.get("verdict"),
          {k: xg1.get(k) for k in ("missing_signal_ts_count","signal_ts_ge_fill_ts_count",
                                   "measured_from_rows") if k in xg1})
EOF
```
Pass criterion: scored path supplies real `execution_ledger_rows` (code
inspection shows no hand-built boolean fallback on the scored path);
gate_result exposes measured counters derived from rows with
`missing_signal_ts_count == 0` and `signal_ts >= fill_ts violation count == 0`;
a negative fixture proves the fallback path cannot produce PASS.
Gate: **C08**.

### P-B-8 — N08 (HIGH): coverage adapter returns None / XG0 sees zero days
Check:
```bash
.venv/bin/python - <<'EOF'
import json, glob
for g in sorted(glob.glob("results/validation_v6p/*/gate_result.json")):
    d = json.load(open(g))
    xg0 = next(x for x in d["gates"] if str(x.get("gate","")).startswith("XG0"))
    cov = xg0.get("coverage") or {}
    print(g, xg0.get("verdict"), xg0.get("reasons"),
          "traded_days:", cov.get("traded_bar_coverage"), 
          "funding:", type(cov.get("funding_coverage")).__name__)
EOF
```
Pass criterion: XG0 payload contains measured blocks (see P-C-7) with numeric,
non-null coverage counts >0 for all seven traded symbols; `coverage=None`
semantics absent; verdict not driven by an unimplemented adapter.
Gate: **C06**.

### P-B-9 — N09 (HIGH): benchmark/funding reason conflation
Check:
```bash
grep -rn "benchmark_coverage_incomplete\|funding_coverage_insufficient\|funding_settlement_missing" research/protocol/gates.py tests/ | head -15
.venv/bin/python -c "
import json,glob
for g in sorted(glob.glob('results/validation_v6p/*/gate_result.json')):
    d=json.load(open(g))
    xg0=[x for x in d['gates'] if str(x.get('gate','')).startswith('XG0')][0]
    rs=xg0.get('reasons',[])
    print(g, rs, 'distinct:', ('benchmark_coverage_incomplete' in rs) <= any('benchmark' in str(x.get('coverage',{})) for x in [xg0]))
"
.venv/bin/python -m pytest tests/ -k "reason or coverage" -q --no-header 2>&1 | tail -3
```
Pass criterion: BTC benchmark absence/failure maps ONLY to
`benchmark_coverage_incomplete`; funding failure requires measured
missing/late settlement counts from the same runtime bundle (never a bare
`funding_coverage_insufficient` without measured counts); reason-semantics
negative fixtures pass.
Gates: **C06**, **C07**.

### P-B-10 — N10 (HIGH): conditional stress + expectancy_r
Check:
```bash
.venv/bin/python - <<'EOF'
import json, glob
for s in sorted(glob.glob("results/validation_v6p/*/stress_report.json")):
    d = json.load(open(s))
    txt = open(s).read()
    print(s, "uncond:", d.get("executed_unconditionally"),
          "variants:", len(d.get("variants", [])),
          "expectancy_r_present:", "expectancy_r" in txt)
EOF
```
Pass criterion: `executed_unconditionally == true` for ALL experiments including
`V6P-MOM-7D-BASEFAIL-SENTINEL` whose base edge intentionally FAILS; all variant
families present (P-C-5 census); metric set uses canonical PnL/PF/funding
PnL/fold returns/MDD/exposure and `expectancy_r` appears NOWHERE in the report.
Gates: **C13**, **C14**.

### P-B-11 — N11 (HIGH): shallow reproduction surface
Check:
```bash
.venv/bin/python - <<'EOF'
import json, glob
FULL = {"signals","orders","positions","portfolio_ledger","funding_cashflows",
        "terminal_positions","exposure_control","accounting_reconciliation",
        "commission_slippage","canonical_metrics","stress_report","gate_result",
        "scorecard","artifact_hashes"}
for c in sorted(glob.glob("results/reproduction_v6p/*/comparison.json")):
    d = json.load(open(c))
    have = set(d.get("values", {}).get("source", {}).keys()) | set(
        k[:-6] for k in d.get("checks", {}) if k.endswith("_match"))
    print(c, "all_match:", d.get("all_match"),
          "separate_proc:", d.get("rerun_process_separate"),
          "missing_components:", sorted(FULL - have))
EOF
```
Pass criterion: `all_match == true`, `rerun_process_separate == true`, and
`missing_components == []` against the FULL 14-component surface of PLAN §6.4(9)
— orders/positions-only comparison (the N11 defect) is insufficient.
Gate: **C18**.

### P-B-12 — N12 (HIGH): append_only false / stale stage_a_root
Check:
```bash
.venv/bin/python - <<'EOF'
import json
r = json.load(open("results/matrix/v6p_validation/reconciliation.json"))
rep = json.load(open("results/matrix/v6p_validation/report.json"))
print("append_only:", r.get("registry_append_only_verified"))
roots = json.dumps(rep)
print("stale_portfolio_v4_root:", "portfolio_v4" in roots)
print("mismatches:", len(r.get("mismatches", [])))
EOF
```
Pass criterion: FINAL v6p reconciliation records
`registry_append_only_verified == true`; no root field points to
`results/portfolio_v4` or any legacy stage-a root; matrix mismatches empty.
Historical contrast preserved: v5r reconciliation recorded `false`.
Gates: **C17** primary, **C16**.

### P-B-13 — N13 (HIGH): audit incompleteness (A6 blind spots)
Check: this protocol itself + post-freeze memo must show machine-checked
evidence for every item P-A-1..P-E-4, with per-finding resolution entries:
```bash
.venv/bin/python -c "
import json
d=json.load(open('research/audits/v6p/scientific_audit_v6p.json'))
findings=d.get('findings',{})
missing=[f'n{i:02d}' for i in range(1,16) if f'n{i:02d}' not in {k.lower() for k in findings}]
print('findings_covered:', len(findings)>=15, 'missing:', missing)
print('unresolved_high_critical:',
      [k for k,v in findings.items() if str(v.get('severity','')).upper() in ('HIGH','CRITICAL') and v.get('status')!='RESOLVED'])
"
```
Pass criterion: all 15 findings have explicit verdicts with evidence paths;
every V6P gate C01–C20 carries an independent A7 status; zero sampled-only
claims (sampling discipline per Section E).
Gate: **C19**.

### P-B-14 — N14 (MEDIUM): purge/embargo not frozen in contract
Check:
```bash
grep -rn "purge\|embargo" results/validation_v6p/*/frozen/*.yaml \
      results/validation_v6p/*/launch_manifest.yaml contracts/ 2>/dev/null | head -8
```
Pass criterion: explicit `purge_embargo` fields frozen (value consistent with
PLAN §8.2 `24h`) inside hashed contract/spec files BEFORE launch (files listed
in `baseline_root.source_files_sha256`); absence ⇒ FAIL for this item.
Enforcement evidence itself surfaces at fold boundaries (feeds V6 FG1; V6P
criterion is the frozen declaration).
Gate: **C02** (freeze completeness), feeds FG1 downstream.

### P-B-15 — N15 (MEDIUM): stale transition timestamps/heads
Check:
```bash
.venv/bin/python - <<'EOF'
import json, subprocess
from datetime import datetime
d = json.load(open("research/audits/v6p/v6p_transition.json"))
keys = ["created_at_utc","audited_at_utc","integrated_at_utc","audited_head","final_head"]
present = [k for k in keys if d.get(k)]
ts = [datetime.fromisoformat(d[k]) for k in present if k.endswith("_utc")]
head = subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True).stdout.strip()
print("all_keys_present:", len(present)==len(keys),
      "monotonic:", ts==sorted(ts),
      "final_head_fresh:", d.get("final_head")==head)
EOF
```
Pass criterion: distinct `created_at_utc` / `audited_at_utc` /
`integrated_at_utc`, `audited_head`, `final_head` all populated;
timestamps monotonically ordered; `final_head` equals actual HEAD after
integration (refreshed via `refresh_transition_heads`, not rewritten content).
Gate: **C16**.

---

## C. Post-freeze full-population audit plan — `results/validation_v6p/*`

Executed only after the whole population is frozen (A1 hands the complete set,
never a subset — PLAN §9.2(8)). Items P-C-1..P-C-10.

### P-C-1 Population completeness and freeze integrity
Enumerate ALL directories under `results/validation_v6p/`,
`results/reproduction_v6p/`, `results/matrix/v6p_validation/`.
Pass criterion: exactly the pre-registered roots exist —
`V6P-MOM-7D-BASEFAIL-SENTINEL`, `V6P-REVERSE-7D-FUNDING-SIGN`,
`V6P-GOLDEN-SYNTHETIC` (plus reproduction `<verify_id>` dirs and the matrix
root); matrix index references exactly these; no orphan/unregistered
experiment dir; no root overwritten or reused from V5R namespaces.

### P-C-2 Accounting identity — dual independent recomputation
For EACH experiment: (i) from `accounting_reconciliation.json` verify
`ending_equity − starting_equity == closed_price_pnl + terminal_pnl +
funding_cashflows − commissions − slippage − rejection_costs` (fold level AND
experiment level); (ii) INDEPENDENTLY recompute the same identity by summing
`portfolio_ledger.jsonl` row components directly (not trusting the
reconciler's numbers). Pass criterion: both computations agree with each other
and with reported equity delta within max($0.01, 1e-6·|equity|); the GOLDEN
SYNTHETIC run additionally matches hand-computed expected orders, funding,
costs, risk trims, terminal PnL, and continuous equity constants exactly
within declared tolerance. Gate: **C11** (+C09).

### P-C-3 Continuous-capital proof
Per experiment: fold k starting equity == fold k−1 ending equity from BOTH
reconciler folds and raw ledger bar series (first/last equity observations per
declared fold interval); `reset_folds=false`; MDD recomputed by A7 from the
continuous equity path equals `canonical_metrics.mdd` (≤1e-9 rel); fold
returns computed from continuous endpoints equal reported fold returns.
Gate: **C09**, **C10**.

### P-C-4 Risk caps census (100% of rows)
Every row of `exposure_control.jsonl`: `risk_mode` enabled, gross ≤1.00+ε,
|net| ≤0.10+ε, |weight per symbol| ≤ declared cap (0.20)+ε AFTER deterministic
reduce-only action; count violations == 0. Cross-check: max gross/net
recomputed from `portfolio_ledger.jsonl` ≤ caps. Gate: **C12**.

### P-C-5 Unconditional stress presence — full variant census
Per experiment (SENTINEL included): `stress_report.executed_unconditionally ==
true`; expected variant families enumerated and ALL executed:
fee×1.5, adverse two ticks, extra one-event delay,
drop-one-symbol × each of the 7 traded symbols, drop-one-fold × 3 folds
(= 13 variants minimum); each variant reports family-aware metrics (PnL, PF,
funding PnL, fold returns, MDD, exposure) and NO `expectancy_r` anywhere.
Negative base edge (sentinel) did NOT skip any stress. Gate: **C13**, **C14**.

### P-C-6 Measured XG1 counters — zero-violation proof
Per experiment: XG1 gate measured from real execution/order rows; counters for
missing signal timestamps and `signal_ts ≥ fill_ts` violations are present,
row-derived, and exactly zero; no boolean fallback on the scored path (P-B-7
code check re-affirmed on final HEAD). Gate: **C08**.

### P-C-7 XG0 blocks present with distinct reasons
Per experiment: payload blocks exist and are populated —
`traded_bar_coverage` (7 traded symbols only), `benchmark_coverage`
(BTCUSDT context only), `funding_coverage` (settlement count/first/last/
completeness per traded symbol), `metadata_coverage` (tick/step/min-notional
per symbol), `requested_window`, `effective_common_window`. Any benchmark
issue uses `benchmark_coverage_incomplete`; funding issues carry measured
settlement counts; codes never conflated. Gate: **C06**, **C07**.

### P-C-8 Hash manifests verified by EXTERNAL reader
A7 runs a separate-process verifier (own `.venv/bin/python` invocation, not
the runner's code path) recomputing sha256 of every entry in each
experiment's `artifact_hashes.json` and of the reproduction rerun artifacts.
Pass criterion: zero mismatches across the full population; hashes-last
ordering evidenced (manifest written after all other files, mtimes/log order).
Gate: **C15**.

### P-C-9 Reproduction — all_match with FULL component list
Each `results/reproduction_v6p/<verify_id>/comparison.json`:
`all_match == true`, `rerun_process_separate == true`, separate output root,
frozen inputs, and the checks dict covers the COMPLETE component list —
signals, orders, positions, portfolio_ledger, funding_cashflows,
terminal_positions, exposure_control, accounting_reconciliation,
commission_slippage/costs, canonical_metrics, stress_report, gate_result,
scorecard, final artifact hashes/digest. ANY absent component ⇒ FAIL (N11
regression guard). Reproduction may not use the source artifact's verdict as
expected truth. Gate: **C18**.

### P-C-10 Registry append-only TRUE in FINAL reconciliation + empty mismatches
FINAL artifact `results/matrix/v6p_validation/reconciliation.json`:
`registry_append_only_verified == true`, `mismatches == []`,
`final_verdict == COMPLETE`; report/index/experiment counts agree with the
directory population and merged registry shard row counts; index roots resolve
on disk; transition counts agree; NO legacy `stage_a_root=results/portfolio_v4`.
Gate: **C16**, **C17**.

---

## D. Independence attestations and verdict rules

### P-D-1 Independence declaration
A7 writes only files under `research/audits/v6p/`; owns no implementation,
spec, gate-repair, or result artifact; performs all checks in separate reader
processes; takes no code ownership overlap with A2–A6 (PLAN §3). This protocol
is frozen before V6P workers run (this document's own commit precedes launches,
provable via git history — same standard as P-A-5).

### P-D-2 Evidence authority
Raw machine artifacts recomputed by A7 outrank any reported verdict string
(PLAN §2 authority order). A7 never trusts: gate ledgers, scorecards, or
reproduction `all_match` flags without recomputation per Sections B/C.

### P-D-3 Verdict rule — PASS
`scientific_audit_v6p.json` overall verdict is PASS iff: every applicable item
P-A-1..P-C-10 passes; all V6P gates C01–C20 independently corroborated PASS;
zero unresolved HIGH/CRITICAL findings (C20); no S1 access, no live-money
surface touched at any point.

### P-D-4 Verdict rule — FAIL
Any failed protocol item, any unresolved HIGH/CRITICAL, any gate A7 cannot
corroborate from raw evidence, or any contradiction between claimed and
recomputed values ⇒ overall FAIL with per-item severity and evidence paths.

### P-D-5 BLOCKED conditions
Verdict is BLOCKED (never silently FAIL/PASS) when: baseline/attestation
missing or unreadable at audit time; provenance validators fail-closed
(P-A-* unexecutable); population incomplete, inaccessible, or partially
frozen; hash-manifest tampering indicators; registry mutation detected;
any S1/live touch discovered; or the census cannot complete inside the
controller deadline (§15.4) — time exhaustion yields BLOCKED/INCOMPLETE,
never PASS.

### P-D-6 Attestation artifacts and sign-off
A7 produces `challenge_memo_v6p.md` and `scientific_audit_v6p.json` containing:
per-gate C01–C20 independent status, per-finding N01–N15 resolution
(resolved_evidence_path each), full-vs-sampled disclosure per Section E, seed
record, HEAD, UTC timestamps, and the explicit verdict PASS/FAIL/BLOCKED.
Missing evidence classifies as FAIL/BLOCKED/NOT_TESTED, never PASS.

---

## E. Sampling vs census policy

### P-E-1 Mandatory 100% census populations (no sampling permitted)
(a) all validation experiments 3/3 and their full artifact sets (P-C-1);
(b) ALL `portfolio_ledger.jsonl` rows for the accounting identity (P-C-2);
(c) ALL fold boundaries for continuity (P-C-3);
(d) ALL `exposure_control.jsonl` rows for caps (P-C-4);
(e) ALL stress variants incl. every drop-one-symbol ×7 and drop-one-fold ×3
(P-C-5);
(f) ALL XG1 counters and XG0 payload blocks (P-C-6/7);
(g) ALL `artifact_hashes.json` entries (P-C-8);
(h) ALL reproduction comparisons against the FULL component list (P-C-9);
(i) ALL 20 gate rows and ALL 15 findings (Sections B/D).

### P-E-2 Permitted seeded samples
Sampling is allowed ONLY for supplementary robustness scans beyond the mandated
census — e.g., re-deriving order↔ledger linkage for large `orders.jsonl`, or
spot-verifying individual funding settlements against the canonical bundle —
and only when a census population exceeds 100,000 rows. Parameters (fixed):
`seed = 20260824`, generator `random.Random(20260824)` (Mersenne Twister),
sample size `n = min(1000, ceil(0.001 * N))`, drawn WITHOUT replacement from
the sorted, post-freeze row-ID space. Sampled IDs and per-row results are
recorded verbatim in `scientific_audit_v6p.json`.

### P-E-3 Escalation rule
Any single failed sampled item escalates that specific check to a full 100%
census of that artifact; the escalated census result (not the sample)
determines pass/fail. No re-draw, no seed change, no substitution.

### P-E-4 Seed discipline
The seed 20260824, generator, sizes, and draw timing (always AFTER population
freeze, BEFORE result inspection) are recorded in the final audit artifact.
Re-rolling or post-hoc seed selection invalidates the affected check ⇒ FAIL.

---

## Execution sequence

1. Freeze this protocol (commit) — H00:00–H00:30 window per PLAN §4.
2. Run P-A-1..P-A-5 immediately before issuing any V6P validation worker
   command; any failure stops the launch.
3. After population freeze, execute P-C-1..P-C-10 plus re-run P-A-* on the
   final HEAD; compile P-B verdicts; emit P-D-6 artifacts.
4. Report gate-count style progress: `V6P x/20 corroborated; findings y/15
   resolved; census items z/40 PASS`.
