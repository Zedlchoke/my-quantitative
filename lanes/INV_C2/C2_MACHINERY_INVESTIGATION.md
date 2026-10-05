# C2_MACHINERY_INVESTIGATION — Lane INV_C2, cycle NFL-WINPROB-NG-SCORED-V1

Written 2026-10-05. Lane: INV_C2 (diagnostic, READ-ONLY on investigated files).
Branch: orca/nfl-winprob-ng-scored-v1-integration · dispatch_sha = actual_start_sha =
`ecf8371abf7839ca49e9245c99f8aa7386d48fdd` · commit_sha: null (uncommitted-by-design).

**Verdict up front: (i) FAULT_ISOLATED_TO_VENUE_CONTROL.** The MACHINERY_SUSPECT is real
but its root cause is a defect in the *negative control's design + adjudication criterion*,
not in the parent C2 machinery, not in the scoring/bootstrap, and not in the time-shuffled
twin code that adjudicated C1/C3/C4. **C3's control verdict is SOUND; C3's ADMIT stands.**
C2 stays OUT of the slate (owner law) — independently re-supported below even with the
control evidence discarded.

---

## 1. What the venue-label-permutation control actually computes (reconstruction)

Pre-registration (binding texts):

- `lanes/DISPATCH/DISPATCH_T_SELECT.md` L41–44: "venue-label permutation for C2 (swap
  home/away on a random half of train games **for deviation updates only**, seed 20261005).
  A control that 'wins' ⇒ machinery suspect flag."
- `MECHANISMS_NFL_NG.md` §2-C2 L187–190 (predecessor cycle
  `.worktrees/nfl-winprob-ng-prep-v1/integration/lanes/B_MECHANISMS/`): "Negative controls:
  **venue-label permutation within train** (swap labels on a random half of train games for
  the deviation updates only) **must destroy the train-internal gain** (else
  implementation/leakage, not signal)".

Implementation (`lanes/T_SELECT/arms.py`, `replay_c2`, L304–351). Signature L304–306:

```python
def replay_c2(records, lam, gamma_d, h, venue_perm_rng=None, return_devs=False):
    """Per-game p_home for C2. R stream is exactly B1* (ratings read, never written)."""
```

Prediction — ALWAYS true roles, h term in true orientation (L333–336):

```python
d_h, d_a = dev[r.home][0], dev[r.away][1]
hterm = 0.0 if r.is_neutral else h
p = sig((r.r_home + d_h - r.r_away - d_a + hterm) / ELO_SCALE)
```

Update branch (L339–348) — one Bernoulli(0.5) draw per non-neutral game; the swap crosses
ONLY the deviation slots; the league scalar `h` and the rating difference keep true
orientation in BOTH branches:

```python
if not r.is_neutral:  # flagged games receive no deviation updates
    if venue_perm_rng is not None and venue_perm_rng.random() < 0.5:
        p_swap = sig((r.r_home + dev[r.home][1] - r.r_away - dev[r.away][0] + hterm) / ELO_SCALE)
        dev[r.home][1] += lam * K_BASE * (r.s_home - p_swap)
        dev[r.away][0] += lam * K_BASE * ((1.0 - r.s_home) - (1.0 - p_swap))
    else:
        dev[r.home][0] += lam * K_BASE * (r.s_home - p)
        dev[r.away][1] += lam * K_BASE * ((1.0 - r.s_home) - (1.0 - p))
```

Call path: `select.py` L230–236 `control_c2_venue_perm` — `rng =
np.random.default_rng(arms.SEED)` (20261005), passed as `venue_perm_rng` (L234–235).
Adjudication: `eval_control` (`select.py` L309–320) — `dll = row_ll[inner] − b1_row_ll[inner]`;
date-cluster bootstrap; **`"wins": bool(hi < 0.0)` — i.e. the control "wins" iff its ΔLL
CI vs B1\* lies entirely below 0 — NOT vs its parent.**

End-to-end, the control arm is therefore: *a C2 arm whose deviation streams receive (i)
correct in-role updates on ~half of each team's in-role games and (ii) crossed
out-of-role updates on ~half of its out-of-role games, while the league h term and all
predictions keep true venue labels* — scored against B1\* (HCA=0, slope 1.605).

## 2. Reproduction (exact) and probe results

All probes rerun from raw `games.csv` through the unmodified `lanes/T_SELECT/{arms,boot}`
(see `probes/probe_c2.py`, `probes/probe_c2_part2.py`, results in `probes/*.json`).
Inner folds 2014–2018, n=1275 rows; seeds identical to the lane run.

| arm (probe) | pooled LL | ΔLL vs B1* [95% CI] | slope |
|---|---|---|---|
| **B1\*** reference | 0.652497 | — | 1.6051 |
| **parent** C2_L075_D1O2_H025 (reproduced) | 0.642470 | −0.010027 [−0.014440, −0.005374] | 1.2533 |
| **control** venue_label_permutation (reproduced) | **0.645624** | **−0.006873 [−0.009950, −0.003733]** | 1.3001 |
| h-only synthetic (λ=0, h=25) | 0.648435 | −0.004062 [−0.005468, −0.002646] | 1.6027 |
| half-speed in-role (λ/2, no perm) | 0.644563 | −0.007934 [−0.010866, −0.004901] | 1.4056 |
| in-role subsample keep=0.5 | 0.644108 | −0.008389 [−0.011910, −0.004709] | 1.3780 |
| in-role subsample keep=0.25 | 0.646025 | −0.006472 [−0.009373, −0.003485] | 1.4655 |
| always-crossed variant (p=1.0) | 0.647495 | −0.005001 [−0.008236, −0.001657] | 1.3148 |
| FULL label swap (predictions+updates+h flipped) | 0.646940 | −0.005557 [−0.008973, −0.002021] | 1.2549 |
| B1\* logits × 1.5 (**no mechanism at all**) | 0.647129 | **−0.005368 [−0.010557, −0.000018]** | 1.0700 |
| B1\* jittered toward 0.5 ((p+0.5)/2) | 0.668148 | **+0.015651 [+0.010082, +0.021101]** | 3.2958 |

Reproduction checks: control rerun bit-identical under the same seed (`True`); row
alignment `len(p)==len(b1_p)==5057` with the same inner mask — `True`. The reproduced
control ΔLL −0.006873 [−0.009950, −0.003733] matches `SELECTION_CONTROLS.csv` to every
printed digit (−0.006872750714132562 [−0.00995017470223513, −0.003732963087756921]).

Deviation-stream forensics (inner rows): parent mean |b^H| = 46.83 Elo, control 34.68
(74%); corr(control b^H, parent b^H) = **0.717**. The corruption does NOT zero the
deviations — they remain a shrunken, partially-correct estimate of the parent's.

Gain destruction accounting (MECHANISMS §2-C2 language): parent gain 0.010027 → control
gain 0.006873 ⇒ **only 31.5% of the train-internal gain destroyed; 68.5% survived.**

## 3. Root cause

**The control was structurally incapable of destroying the gain, and the criterion used to
adjudicate it cannot detect leakage on this baseline.** Three measured components:

1. **The h term is never corrupted** (pre-registered as "deviation updates only"; code
   L343 keeps `+ hterm` in the swapped branch). The league scalar h=25 Elo alone is real
   NFL home-advantage signal absent from B1\* (HCA=0): h-only arm ΔLL = −0.0041, CI < 0.
2. **The deviation share is only partially corrupted**: each slot still receives in-role
   updates on ~50% of its in-role games (half-speed), and crossed out-of-role updates carry
   partially-informative performance data. Measured: control deviations keep corr 0.72 /
   74% magnitude vs parent; net control retains 68.5% of the parent's gain. In-role
   subsampling at keep=0.25–0.5 brackets the control's ΔLL (−0.0065 to −0.0084).
3. **The adjudication criterion is non-diagnostic on an underconfident baseline**: B1\*
   has train slope 1.605 (severely underconfident). ANY arm that adds spread to the
   argument stream beats B1\* — including pure monotone rescaling of B1\*'s own logits by
   ×1.5 with zero mechanism information (ΔLL −0.0054, CI < 0), and even the strictest
   full label-swap corruption (−0.0056, CI < 0). "Control beats B1\* with CI < 0" is
   therefore expected for this control REGARDLESS of whether the parent's gain is real.

Note also the dispatch background's framing ("the control must not beat its parent") is
factually not what happened: **the control LOST to its parent** (0.645624 vs 0.642470,
+0.00315 LL). The `wins` flag fired on the vs-B1\* comparison.

## 4. Candidate-fault adjudication

| hypothesis | verdict | evidence |
|---|---|---|
| (a) updates permuted / predictions true (mismatch) | **CONTRIBUTING (by design)** | §3.1–3.2: h untouched; deviations partially retained (corr 0.72); the "mismatch" is not harmful regularization, it is signal retention |
| (b) E recomputed with permuted roles double-counting signal | **REJECTED** | p_swap is self-consistent with the swapped updates; control deviations carry LESS signal than parent (corr 0.72, mag 0.74), the opposite of double-counting |
| (c) half-speed updates (λ_eff ≈ λ/2) | **CONTRIBUTING** | each slot's in-role updates arrive on ~50% of in-role games; in-role subsample keep=0.5 → −0.0084, keep=0.25 → −0.0065 brackets control −0.0069 |
| (d) row-set/pairing mismatch in ΔLL | **REJECTED** | row alignment verified; ΔLL paired per-row on identical inner mask; bit-exact reproduction from raw data |
| (e) sign/index bug swapping control and parent | **REJECTED** | independent reproduction matches both ledger rows exactly; parent beats control as expected under corruption |
| (f) calibration-jitter toward 0.5 | **REJECTED (direction test)** | 0.5-ward jitter of B1\* is WORSE: ΔLL +0.0157, slope 1.605→3.30. The control's slope moved DOWN toward 1 (1.300): its gain comes from MORE-extreme arguments (h + deviations), the opposite of dithering toward 0.5. (f) would require an overconfident parent; the mirror-image NBA pattern (slope 0.7801, shuffled twins winning) is consistent with (f) THERE — direction-dependent baseline sensitivity, not one shared cross-cycle bug |

## 5. Taint scope (load-bearing)

Code-path audit (grep-verified, file `lanes/T_SELECT/`):

- The faulty branch exists ONLY inside `replay_c2` under `venue_perm_rng is not None`
  (arms.py L340). Sole call site: `control_c2_venue_perm` (select.py L234–235).
  - Parent C2 p-stream (select.py L153) and the C2 time-shuffled twin (select.py L208)
    call `replay_c2` WITHOUT the rng — clean path, bit-verified by the C2_NULL designed
    null and by this investigation's reproduction.
- C1 twin (select.py L172–198): post-hoc permutation of β·(SOS−S̄) slot values on the
  p-stream — independent code.
- C2 twin (select.py L201–227): post-hoc permutation of the prediction bonuses (b^H, b^A)
  — independent of the update-channel fault (its ΔLL was +0.00366, clean).
- **C3 twin** (select.py L239–254): permutes z across lineages at each season boundary,
  then a full `arms.replay_elo` — `replay_elo` contains NO permutation branch and is not
  shared with `replay_c2`'s faulty path. Independent.
- C4 twin (select.py L257–276): permutes short-week flags — independent.
- Shared machinery `eval_control` + `boot.py`: verified correct by bit-exact reproduction
  and row alignment. The criterion weakness ("wins" = ΔLL CI < 0 **vs B1\**") IS shared,
  but it is conservative: it can only fire false alarms (blocking admission), it can never
  fabricate a "clean" — a clean is the raw measurement that the corrupted arm's ΔLL CI
  includes 0, computed on verified machinery.

**C3 control verdict: SOUND.** Its twin (−0.000455 [−0.004890, +0.004169], slope 1.362)
was nowhere near the "wins" threshold, and a clean signal-destroyed twin is the expected
null on C3's parent, whose selected config C3_T050 has slope 1.079 — inside [0.85, 1.15],
i.e. already calibrated enough that a jittered/noise twin has nothing to exploit. The
fault mode that made C2's control win (retained genuine signal: an uncorruptible h term +
half-speed in-role updates) has no analog in C3's twin: permuting z fully destroys the
mechanism's ONLY signal channel (lineage→prior association); nothing real survives.

## 6. Verdict

**(i) FAULT_ISOLATED_TO_VENUE_CONTROL.**

- The C2 MACHINERY_SUSPECT is confirmed as a control-design/criterion defect (pre-registered
  verbatim as "deviation updates only" + adjudicated vs B1\* on an underconfident baseline),
  not parent leakage. The parent's clean-path machinery is bit-verified correct.
- **C2 stays OUT of the slate (owner law) — independently re-supported**: even with the
  venue-control evidence discarded entirely, C2_L075_D1O2_H025 slope 1.2533 is outside the
  pre-registered band [0.85, 1.15] ⇒ G-ENTRY FAIL ⇒ KILL. Additionally, under MECHANISMS
  §2-C2's own falsifier language the control DID formally fail ("must destroy the
  train-internal gain": only 31.5% destroyed). The kill stands for three independent
  reasons. No post-outcome revival is proposed or permitted.
- **C3's ADMIT stands; no ERRATUM and no control re-run is required** — its control
  machinery is code-independent of the fault and correctly implements its pre-registration.

## 7. Remediation PROPOSAL (future cycles only; implement nothing this cycle)

For any successor protocol that reuses negative controls on a possibly-miscalibrated baseline:

1. Venue-permutation controls must corrupt EVERY venue-dependent term (league scalar h
   included), or be adjudicated as **gain destruction vs the PARENT** (pre-registered
   materiality threshold on ΔLL(control, parent)), never as "CI < 0 vs B1\*".
2. Add a spread-matched null arm (e.g., fixed monotone rescaling of the baseline's logits)
   so the "control wins" threshold is calibrated against the baseline's own
   miscalibration direction (slope measured alongside; jitter-toward-0.5 controls only
   bind when baseline slope < 1).
3. Record the baseline's train calibration slope next to every control row in ledgers, so
   criterion weakness is auditable without a re-run.

## 8. Evidence manifest (this lane; all under lanes/INV_C2/)

- `probes/probe_c2.py`, `probes/probe_c2_part2.py` — read-only probe scripts (import
  lanes/T_SELECT unmodified; writes only into lanes/INV_C2/probes/).
- `probes/probe_results.json`, `probes/probe2_results.json` — measured numbers quoted above.
- Investigated (never modified): lanes/T_SELECT/{arms.py, select.py, boot.py,
  SELECTION_REPORT.md, SELECTION_LEDGER.jsonl, SELECTION_CONFIGS.csv,
  SELECTION_CONTROLS.csv, VERDICT_TABLE.md}; lanes/F_FREEZE/FREEZE_PACKET.md;
  lanes/DISPATCH/DISPATCH_T_SELECT.md; MECHANISMS_NFL_NG.md §2 (predecessor worktree,
  read-only); NBA-PLAYERFEAT-SCORED-V1 lanes/T_SELECT/harness.py (cross-cycle context,
  read-only).
- Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python only. No git
  commands. No writes outside lanes/INV_C2/** and the handoff JSON.
