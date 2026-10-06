# SHARED_MECHANISM_MAP — which 5SYM families share one mechanism, and what must be re-proven per symbol

- Round: **FUTURES-5SYM-PRESCORED-20261005**, lane **HYPO**. Outcome-blind:
  no return statistic, no PnL, no scored claim enters any cell. This map
  organizes the census (`CENSUS_5SYM.md`) by mechanism class; it creates
  no families and merges none that are lawfully separate.
- **The governing law stated once, up front**: efficacy (or anatomy, or
  package quality) on one symbol is NOT evidence for another symbol.
  Shared mechanism class means shared *vocabulary of hypothesis and
  kill-set* — never shared *evidence*. Every scored registration treats
  each symbol leg as its own trial with its own null.

## M1 — US-data-open 08:30-ET release (the 07:30-CT clock)

| leg | family | role |
|---|---|---|
| NQ | NQ-F2 MACRO-0730-NQ | equity-index leg (era-confined 2023-26) |
| 6E | FX-F3 US-8:30 Spillover | spillover into the still-open London book |
| 6B | FX-F3 US-8:30 Spillover | same |

- **Shared core**: the BLS schedule calendar + vintage law is ONE
  program asset (`events_bbo_coverage/bls_dates.json` PASS_EVIDENCED
  204/204 rows each CPI/EMPSIT, all 08:30 ET; BLSV §5 2025-vintage law:
  11 CPI / 10 EMPSIT actuals; canceled-but-expected days enumerated);
  the 07:30-CT anchor minute; the two-arm continuation/reversal
  structure; the canceled-day falsifier design.
- **MUST be re-proven per symbol** (never assumed transferable):
  (a) the release-minute anatomy itself — measured separately on each
  symbol and each is a different shape (NQ 4.51× scoring-era spike;
  6E ×1.95 volume; 6B thin-book response window); (b) the response
  window's local-clock bucketing (NQ: RTH; 6E/6B: Europe/London);
  (c) the cost floor (NQ S1/S2/S3 23.49/28.49/33.49 USD/side vs 6E RT
  3.6–6.3 bp vs 6B 6.3–11.2 bp — different denominators entirely);
  (d) event vintages as known at each decision date (shared table, per-
  symbol application); (e) exclusion sets (NQ era gate; FX double-event
  central-bank overlaps).
- **Transfer law**: a PASS/FAIL of the NQ leg says nothing about the
  6E/6B legs and vice versa; the FX legs additionally carry the
  mandatory sham-calendar control (house standard since FXFV5,
  FAMILY_FAILURES row 40) and the near-miss disclosure of the dead
  cross-economy spillover row 51.

## M2 — Scheduled policy-decision resolution (central-bank decision minutes/windows)

| leg | family | decision authority |
|---|---|---|
| NQ | NQ-F1 FOMC-ERA | FOMC statement (13:00 CT) |
| 6E | FX-F2 Policy-Decision (FOMC anchor) | FOMC statement + ECB stratum |
| 6B | FX-F2 Policy-Decision (MPC anchor) | MPC (12:00 London) + FOMC stratum |
| 6J | JF1 BoJ MPM window | BoJ day-2 statements (12:00–15:30 JST window convention) |
| 6A | AF1 RBA Decision-Minute | RBA (14:30 Sydney anchor convention) |

- **Shared core**: mechanism class (uncertainty resolution; R-C drift
  vs R-D reversal arms, both tails registered); the intensity-ordering
  falsifiable claim (reaction scales with spike intensity — 6E FOMC
  ×17.24 vs ECB ×1.73 is the measured template); the clock-only shadow
  law; the delay-pair artifact detector; event-stacking exclusion law.
- **MUST be re-proven per symbol**: (a) the decision calendar and its
  PIT authority — each is a different source with different evidence
  grade (FOMC archived-HTML minute-proof; MPC assembly-method
  disclosed; ECB machine-verified; BoJ date-only archive — minute
  stamps NOT evidenced, window convention lawful; RBA date-granularity
  only, anchor a declared convention); (b) the anchor minute/window and
  its DST-stability (6B minute-720 stable across 8 DST-mismatch dates;
  JF1 K3 anchor-insensitivity DELIVERED; NQ 13:00 CT); (c) the holding
  window length and exit clock (6E 3h; 6B ≈9h; JF1 to session close;
  AF1 to 17:00 Sydney); (d) the cost floor per symbol (NQ / 6E / 6B /
  6J / 6A bands all differ; 6A era-aware); (e) the thin-book execution
  floor (JF1 34-vs-53 1m volume; AF1 home-session modest depth);
  (f) each leg's own K6-class anatomy gate — NQ-F1/F2 PASSED this
  round; the others are committed descriptive anatomy, none of it
  transferable.
- **Transfer law**: this is the map's most important instance — five
  central banks, five books, five calendars. NQ's FOMC anatomy PASS is
  NOT evidence for 6E's FOMC leg or 6B's MPC leg; the ES sibling
  families (registered program-side) are not evidence for any 5SYM leg.
  The ECB/FOMC strata are family-internal negative controls, not
  cross-symbol evidence.

## M3 — Contract roll-migration mode (RMM)

| leg | family | role |
|---|---|---|
| 6E | RMM Role-B (6E) | gated alpha leg, +4 IDs |
| 6B | RMM Role-B (6B) | gated alpha leg, +4 IDs |
| 6J | RMM Role-B (6J) | gated alpha leg, +4 IDs |
| 6A | RMM Role-B (6A) | contingency-only (PB3 PARK), +4 IDs |
| NQ | — | **EXCLUDED by anti-duplication**: NQ-F4 ROLLWK is the NQ roll-microstructure class owner; RMM proposes no NQ leg (HYPOTHESES_R2 §2 field 4) |

- **Shared core**: the mechanism (compressed-vs-gradual forced position
  transfer; M-COMPRESS-REV vs M-COMPRESS-CONT arms with the
  mode-monotone gradient as part of the claim); the strict-past mode
  classifier (decide at close t, effective t+1); the C1 block-shuffle
  placebo design (iid forbidden); the K1–K7 kill set including the DC
  §1.3 boundary clause (roll-GAP level / rate differential ⇒ out-of-law)
  and the K3 residual law (generic roll-week exposure belongs to NQ-F4
  on NQ; no new FX family may be spun from the residual); Role-A =
  construction ledger, 0 IDs, on every leg.
- **MUST be re-proven per symbol**: (a) the 27-roll switch tables and
  leads (6E 13–19d, 6B 17d, 6J OI-lead 1–3d, 6A crossover 9–15d after
  declared); (b) the mode split — measured/derived per symbol and NOT
  pooled (6E 22/5, 6B 23/4, 6J 19/8, 6A 21/6 — different gradual
  fractions are themselves part of each leg's falsifiable base);
  (c) the cost law including 6A's era boundary (era-1 15.18 bp vs
  era-2 8.20 bp MODELED — never back-cast); (d) event-exclusion
  calendars per leg; (e) the DC §1.3 boundary ruling is ONE owner
  decision in form but binds each Role-B leg separately at
  registration.
- **Transfer law**: the CEASE-SYNC descriptive (18/24 abrupt weeks
  all-4-symbol ±1 week) is cross-symbol *synchronization* anatomy — it
  is explicitly NOT evidence that any leg carries a post-switch
  signature, and MUST NOT be cited as cross-leg efficacy support. The
  mode × post-switch-drift interaction is NOT_RUN on every leg; until
  measured per leg, no leg has any family evidence at all.

## M4 — Tick-grid / venue-microstructure event conditioning

| leg | family | role |
|---|---|---|
| 6A | AF4 Tick-Regime Conditioning | overlay on AF1/AF3 (the grid event is 6A's) |
| 6J | (constant-tick negative instrument) | 6J grid measured CONSTANT across eras (GCD 500 int-nano sampled eras) |
| 6E/6B | (constant-tick negative instruments) | tick-constancy at 2020-11-23 CONSTANT (GCD 50,000 / 100,000 int-nano; `tick_constancy_6e6b.json`) |

- **Shared core**: the same-date placebo law — a genuine grid law must
  NOT appear on unchanged-grid symbols at the same dates (the 2020
  COVID confound is the declared dominant alternative explanation).
- **Per-symbol**: the grid event itself is 6A-only; era-1 (231
  sessions) is pre-declared descriptive-only (fold floor fails); the
  overlay holds 0 standalone identities and its null is identity with
  the host.
- **Transfer law**: none — this is a single-symbol event class whose
  other symbols exist only as negative instruments. The 6E/6B
  constancy result (delivered this round) closes AF4's secondary
  control and nothing else.

## M5 — Session-structure discovery/fade (home or third-session range breaks)

| leg | family | window |
|---|---|---|
| 6E | FX-F1 London-Range | London 08:00–11:00 range, trigger 11:00–15:30 London |
| 6B | FX-F1 London-Range | same |
| 6J | JF3 Tokyo-Morning | Tokyo 09:00–11:30 JST range |
| 6A | AF3 Bimodal US+Sydney | Sydney 09:30–11:30 morning range |

- **Shared core**: the arms structure (discovery-continuation vs
  thin-book fade), the DST-mismatch clock-law falsifier design (sign
  flip under CT bucketing = clock bug), the coverage-≥80% exclusion
  rule, the delay-pair thin-book detector.
- **MUST be re-proven per symbol — and the dead corpus binds this
  class hardest**: (a) the anatomy is per-symbol and different in kind
  (6E London 21.59% of volume; 6B London-share drift 28.7→23.7%; 6J
  tokyo_am 18.1% of session highs; 6A bimodal U-curve); (b) the cost
  floor including session-of-day dependent fills (6J 59-vs-120
  thin-book floor; 6A Sydney-morning +1 tick floor); (c) **the ancestry
  exposure is NOT uniform**: 6E/6B legs sit inside the PB2 ancestry
  court (dead FX-spot session corpus 12/12 EXPECTANCY_NONPOSITIVE —
  HOLD); JF3's nearest dead row is the same-window-pair spot family
  (FOREX-FREE-V2-A4-P1, row 34 — disclosed near-miss); AF3 is 6A
  PARK with no dead ancestor. The shared class label must never be
  used to average these exposure levels.
- **Transfer law**: FX-F1's census PASS (1,362/1,342 triggers) is NOT
  evidence for JF3 or AF3; the PB2 HOLD binds only the 6E/6B legs but
  the *reasoning* (dead spot corpus) is cited in JF3's dossier as its
  standing risk. Cross-leg claims are barred.

## M6 — Rate-differential / CIP regime conditioning (overlays)

| leg | family |
|---|---|
| 6E / 6B | FX-F5 Rate-Differential Regime Conditioning |
| 6A | AF2 RBA-vs-Fed Differential Regime Conditioning |

- **Shared core**: H-G overlay law (conditioning, never standalone;
  0 standalone identities); the vintage-fragility precedent is ONE
  program law (6E r=+0.9097 latest-vintage vs −0.107 PIT-as-of — the
  measured flip; AF2's K2 bar: ≥3-of-16 material-roll flips ⇒ dead);
  block-shuffle label placebo (iid forbidden); the √2 MDE inflation
  cost of conditioning.
- **Per-symbol**: the differential definition (SOFR/DFEDTARU − Bank
  Rate vs US−AUD), the roll-gap basis (27 rolls per symbol), and the
  zero-differential negative windows (6B 2025-26 at 0.00pp; 6A 2021
  ZIRP noise band).
- **Transfer law**: the standalone differential/carry classes are
  measured-dead program-wide (rows 56/64/65/83 — nominal-yield-level
  exposure forms, PPP deviations); that death binds BOTH overlays as
  their standing out-of-law boundary (DC §1.3) — it is ancestry
  evidence against the standalone FORM, never evidence for or against
  either overlay's conditioning value.

## M7 — Multi-day reversion (horizon T4)

| leg | family |
|---|---|
| NQ | NQ-F3 RUN-REV-NQ |
| (ES) | ES-F4 RUN-REV — registered program-side sibling, out of 5SYM scope, cited only as the class owner |

- **Shared core**: the run-length/VR/acf1 descriptive vocabulary and
  the K3 concentration-kill design.
- **Per-symbol**: the NQ run census (NOT_RUN), the intraday-placement
  gate (NOT_RUN), and the 2020-crash concentration stratum are NQ-only;
  the rebuild precondition (delivered descriptively on v3) is NQ's
  own.
- **Transfer law**: ES-F4's statistics are ES evidence; NQ-F3 stands
  or falls on NQ's own census and gates.

## Summary table — shared vs per-symbol obligations

| mechanism | symbols | shared (one proof suffices) | per-symbol (never shared) |
|---|---|---|---|
| M1 08:30 US data | NQ, 6E, 6B | BLS calendar + vintage law; anchor minute; arm structure; canceled-day falsifier design | anatomy, response-window clock, cost floor, era gates, exclusions |
| M2 policy decision | NQ, 6E, 6B, 6J, 6A | mechanism class + intensity-ordering claim; shadow law; delay-pair detector | calendar PIT authority, anchor/window, holding window, cost floor, anatomy gate |
| M3 roll migration | 6E, 6B, 6J, 6A (NQ excluded) | classifier, placebo design, kill set K1–K7, DC §1.3 clause, Role-A law | switch tables, mode split, cost era law, exclusions, per-leg boundary application |
| M4 grid event | 6A (+negative instruments 6J/6E/6B) | same-date placebo law | the grid event itself, era thinness law |
| M5 session structure | 6E, 6B, 6J, 6A | arm structure, DST falsifier design, coverage rule | anatomy, cost/session floors, ancestry exposure (PB2 vs row-34 vs none) |
| M6 differential overlay | 6E/6B, 6A | overlay law, vintage-flip precedent, block-shuffle law | differential definition, roll basis, negative windows |
| M7 multi-day reversion | NQ | descriptive vocabulary, concentration-kill design | run census, placement gate, rebuild, 2020 stratum |

— End SHARED_MECHANISM_MAP.md. Outcome-blind; organizational only; the
transfer law above binds every downstream consumer of this census.
