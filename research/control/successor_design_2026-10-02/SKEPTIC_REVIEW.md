# SKEPTIC_REVIEW — independent verification of successor_design_2026-10-02

Independent fresh-context reviewer (general-purpose subagent, read-only,
own scripts in /tmp only), dispatched before the packet's commit. Full
verdict relayed verbatim in the session record; this file summarizes the
disposition. Reviewer recomputed every headline number from the raw
journals/metrics.

## Verified exactly (no discrepancy)

1. 24 `*_MO_*` arms are SOLO single-leg books (header + every row one leg);
   docket B §9's "minus-one/plus-one arms" label is wrong — packet
   correction #1 upheld.
2. Fill matching: 2,436 / 2,363 / shared 2,001 (1,517 same-size, 484
   sized) / 435 P-only / 362 B1-only / union 2,798 — exact.
3. Decision dedup: POLICY 3,124 ⊂ B1 3,467 (union 3,467) — exact.
4. Solo-arm nets: S014 +109,448.16 vs trig −222,300.73/−319,603.73;
   S026 +9,203.41 vs trig +825,243.84/+822,232.99; S002 −248,990.41 (B1
   solo) vs +137,883.41 (floored POLICY) — exact; the three-attribution
   conflict is real.
5. Control arms: B8 +388,900.79 · B1 +688,604.03 · B5 +54,024.18 ·
   B6 −256,347.66 · B7 +591,219.62 · B2 +356,100.53 · B3 +1,731.42 — exact.
6. `paper_fold_net_by_leg` B1: S026 +1,637,143.15; S003 +225,631.11;
   S023 +230,099.40; S014 +34,984.20; S002 −24,268.70 — exact.
7. Co-loss 27/208 weeks (all EURUSD×USDJPY; GBPUSD never); weekly
   correlations −0.1217 / +0.1607 / −0.0263 — signs/magnitudes hold under
   an alternative zero-fill convention too.
8. POLICY heat events marginals 36.92/4.49/57.84% — exact.
9. Blocked inventory totals (343/331/35; 296/101; SUPERMAJORITY 659 vs
   1,021 metrics-only; per-leg supermajority 706/186/55/22/20) — exact.
11. DAILY battery numbers (−1,088.08 / −1,400.54 / −1,713.01; 61 fires;
   1,128+73+24=1,225) — exact; TF-1 C2→REPORT20_PAIR substitution
   correctly NOT described as clock-shadow anywhere in the packet.

## Defects found → ALL FIXED before commit (file-by-file)

| # | defect | fix applied |
|---|---|---|
| a | COMPLEMENTARITY §1 claimed USDJPY+EURUSD hold "simultaneously a majority of the time"; true joint = 22.92% of window | sentence replaced with the joint numbers; joint metric added to `complementarity.json` (`exposure_joint_POLICY`) |
| b | SYMBOL_DOSSIERS S003 row carried S002's trig (+68,820 n=7 belongs to S002; S003 n=2 → −5,464.87); "49 blocks" matched nothing (S003 = 37) | table fixed; blocked line fixed (S002 79 · S003 37 · S023 16 · VC2-JPY 22) |
| c | JOURNAL_CENSUS §3.1 per-leg BLOCKED_FLOOR breakdown wrong (49/14/14 → 79/37/16/22) | fixed; now cites the machine recount |
| d | `census.json` `per_leg_inventory` contained only B1 (script indentation bug) — cited evidence did not exist | script fixed, re-run; both arms present; numbers re-verified against reviewer's independent recount |
| e | COMPOSITE_POLICY_DESIGN §2 Layer 0 "validated core" overclaim | reworded: "structurally unchanged ≠ validated"; DSR REJECT disclosure added |
| f | JOURNAL_CENSUS §5 mixed a cross-arm sum (1,692) with deduped union figures | restated per-arm (848/844) with the dedup framing explicit |
| g | "empty dict" wording for B1 heat events (key is ABSENT, not empty) | corrected in header + script note |
| 10 | Tier-arm row claimed "decision counts verified identical" — false for the POLICY family (3,124/3,126/3,114/3,110; cost-guard defer variation) | corrected in §1 table, §4 reconciliation table, and `census.json` dedup_law |

## Reviewer bottom line (relay)

"the packet's headline machinery (dedup law, fill/decision matching,
three-attribution conflict, control-arm table, DAILY accounting) survives
adversarial recomputation exactly. The real defects are concentrated in
the per-leg blocked/trig details … one factually false exposure sentence …
the 'validated core' phrase, and the overstated tier-arm identity" — all
repaired above before the packet was committed.

— end record —
