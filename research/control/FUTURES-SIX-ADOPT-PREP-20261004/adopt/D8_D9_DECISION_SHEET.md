# D8_D9_DECISION_SHEET — concrete decision items for the owner

Round: FUTURES-SIX-ADOPT-PREP-20261004 · Lane ADOPT · 2026-10-04

> **NOT ratified by owner as of 2026-10-04; this sheet is input to a ruling, not a ruling.**
> Both items originate in the verified findings of round FUTURES-SIX-READINESS-20261004
> (`synth/OWNER_DECISIONS.md` D8/D9) and are made CONCRETE here with quantitative consequences and
> fail-closed defaults. Every number below is re-measured or file-pointered by this lane
> (`adopt/cache_v3_hashes.json`, `CACHE_V3_PIT_STATEMENT.md`, `CEASE_GUARD_STANDARD.md`,
> `6A_TICK_ERA_LAW.md`).

---

## D8 — 6A era-aware tick/cost law

**Context.** The v2 dossier's tick conflict (0.00005 vs 0.0001) is RESOLVED_PER_ERA from data:
tick 1e-04 = **$10.00/tick** for sessions **2020-01-02..2020-11-20** (231 sessions; zero odd prints
in 327k+ closes), tick 5e-05 = **$5.00/tick** from **2020-11-23** to corpus end (GCD-verified across
4 era chunks, 2.4M+ rows, 1.97M increments; vendor definitions 2023-10+ match era 2). Independent
verification reproduced the break exactly at the 2020-11-20→23 weekend. Full text:
`adopt/6A_TICK_ERA_LAW.md`.

**Option A — ratify the era boundary as measured.**
Consequence: the era table in `6A_TICK_ERA_LAW.md` §1 becomes the standing law; any future 6A cost
spec must be era-aware (§4 checklist); the 2020 sub-era slip understatement is fixed at
**+$10.00/RT per contract (+100% of the slip component; $20 vs $10 for a 1-tick-per-side model)**.
Residual risk: the official rulebook page stays BLOCKED_TRANSPORT — a ratified data-derived boundary
could shift if an official document ever contradicts it (no such document identified; measured
evidence is unanimous).

**Option B — demand a vendor/exchange document before freezing.**
Consequence: the boundary stays PROVISIONAL; the measurement stands as descriptive-only; 2020-era 6A
cost work remains blocked on obtaining an official page (permitted routes only; no purchase is
proposed anywhere). Era 2 ($5.00 from 2020-11-23) is uncontroversial and could be frozen separately.

**If undecided (fail-closed default):** **era-2-only cost models may not back-cast into 2020-era
windows.** Any 6A cost spec lacking the era table is invalid for windows overlapping
2020-01-02..2020-11-20.

---

## D9 — explicit cease-guard as the standard chain-builder law + NQ cache_v3 ratification

**Context.** The k=5 volume-crossover rule's weak implicit guard is PROVEN to bite on real data in
**3 symbols / 4 manifestations**: 6J 2022-09-20 (held ceased `6JU2` while `6JZ2` traded 125,303
lots; session vanished from the chain), 6A 2024-12-17 (dead-held `6AZ4` while `6AH5` traded 55,675)
and 2026-06-16 (dead-held `6AM6` while `6AU6` traded 55,533), and NQ's v2 chain 2020-03-23..05-29
(`NQH0_2020` dead-held **49 sessions**; wrong roll 2020-06-01 at dte −73). Explicit-guard variants
produce **0 violations** with identical roll dates — the only deltas are the two 6A switches moving
1 session earlier (restoring exactly the vanished sessions). Evidence table + normative text +
pseudocode: `adopt/CEASE_GUARD_STANDARD.md`.

**Option A — adopt "explicit cease-guard mandatory" as a standing data-prep law AND ratify the NQ
cache_v3 chain (+ guard variants) as the canonical starting point for any future NQ/FX chain build.**
Consequence: `CEASE_GUARD_STANDARD.md` moves PROPOSED → standing law (future builders must implement
§2 and pass the §2.5 audit); `FUTURES-SIX-READINESS-20261004/nq/cache_v3/` becomes canonical for
consumption (with hashes `adopt/cache_v3_hashes.json` and PIT classification
`CACHE_V3_PIT_STATEMENT.md`: PIT_CLEAN_BY_CONSTRUCTION); the v2 caches' deprecation
(`DEPRECATION_NQ_V2_CACHES.md`) is confirmed; ERRATUM-F1's re-measure obligation stays discharged.
Quantified state being ratified: panel 6,780,608 rows; held chain 4,219 sessions / 66 rolls with the
NQH0_2020→NQM0_2020 roll at the true 2020-03-19 crossover; 0 cease-guard violations; reproduction
digests re-confirmed by this lane with 0 deltas.

**Option B — leave per-cycle choice.**
Consequence: each future spec decides its own guard; the 3-symbol table stands as precedent only;
NQ cache_v3 remains **canonical-CANDIDATE** (usable, cited, not ratified); the cease-guard text
serves as the reference implementation each spec must explicitly adopt or deviate from.

**If undecided (fail-closed default):** **per-cycle choice of guard** — and no future cycle may
consume the v2 NQ caches (deprecation stands independent of ratification), while cache_v3 stays
candidate-status until a cycle's own data freeze + owner ruling.

---

## What remains blocked while D8/D9 are open

* **D8 open**: any 2020-era 6A cost/slippage number (blocked by the fail-closed default); any frozen
  6A cost spec (era-blind specs are defects by definition).
* **D9 open**: NQ cache_v3 stays CANDIDATE (consumption allowed only with explicit per-cycle
  citation of this packet, not as ratified canonical); cease-guard variants stay diagnostic-labeled;
  no chain builder may claim compliance with a "standard" that does not yet exist in force.
* Independent of both: fees stay MODELED / VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW (D2/D3
  territory, unchanged); no scored cells; no PnL claims arise from this packet.

*This sheet raises no gate and requests no GO. It is input to a written owner ruling.*
